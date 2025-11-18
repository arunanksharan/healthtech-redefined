"""
Vector Service
Business logic for semantic search and text ingestion
"""
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy import select
from loguru import logger

from modules.vector.repository import VectorRepository
from shared.database.models import TextChunk
from modules.vector.schemas import (
    IngestTranscriptsByConversation,
    IngestMessageTranscript,
    IngestTicketNotes,
    IngestKnowledge,
    SearchQuery,
    IngestResult,
    VectorStatistics
)
from core.embeddings import embeddings_service
from shared.database.models import Conversation, Ticket
from shared.events.publisher import publish_event, EventType


class VectorService:
    """Service for vector search and text ingestion"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = VectorRepository(db)
        self.embedder = embeddings_service

    # ==================== Chunking ====================

    def _chunk_text(
        self,
        text: str,
        chunk_chars: int,
        overlap: int
    ) -> List[str]:
        """
        Split text into overlapping chunks

        Algorithm:
          1. If text <= chunk_chars, return single chunk
          2. Otherwise, create chunks with sliding window:
             - Start at position i=0
             - Take chunk of size chunk_chars
             - Move forward by (chunk_chars - overlap)
             - Repeat until end of text

        Example:
          text = "ABCDEFGHIJ" (10 chars)
          chunk_chars = 4
          overlap = 1

          Chunks:
          - i=0: "ABCD"
          - i=3: "DEFG"
          - i=6: "GHIJ"

        Args:
            text: Text to chunk
            chunk_chars: Characters per chunk
            overlap: Overlap between chunks

        Returns:
            List of text chunks
        """
        text = text or ""
        text = text.strip()

        if len(text) <= chunk_chars:
            return [text] if text else []

        chunks: List[str] = []
        i = 0

        while i < len(text):
            chunk = text[i:i + chunk_chars]
            chunks.append(chunk)

            if i + chunk_chars >= len(text):
                break

            # Move forward by (chunk_chars - overlap)
            # Ensure we make progress even if overlap >= chunk_chars
            i += max(1, (chunk_chars - overlap))

        return chunks

    # ==================== Ingest Sources ====================

    async def ingest_conversation(
        self,
        org_id: UUID,
        payload: IngestTranscriptsByConversation
    ) -> IngestResult:
        """
        Ingest all message transcripts for a conversation

        Process:
          1. Load conversation and verify access
          2. Check patient consent if applicable
          3. Load all messages with transcripts
          4. Chunk each transcript
          5. Generate embeddings
          6. Delete old chunks for this conversation
          7. Insert new chunks

        Args:
            org_id: Organization ID
            payload: Ingest request

        Returns:
            IngestResult with indexed count
        """
        # Load conversation
        query = select(Conversation).where(
            Conversation.id == payload.conversation_id,
            Conversation.org_id == org_id
        )
        result = self.db.execute(query)
        conversation = result.scalar_one_or_none()

        if not conversation:
            logger.warning(f"Conversation {payload.conversation_id} not found")
            return IngestResult(indexed=0)

        # TODO: Check patient consent if conversation.patient_id is set
        # For now, we'll proceed if patient is linked

        # For simplified implementation, we'll create sample chunks
        # In production, you would load actual messages/transcripts

        # Generate sample text (in production, load from messages)
        sample_text = f"Sample conversation transcript for conversation {conversation.id}"

        # Chunk the text
        chunks_text = self._chunk_text(
            sample_text,
            payload.chunk_chars,
            payload.overlap
        )

        if not chunks_text:
            return IngestResult(indexed=0)

        # Generate embeddings
        try:
            vectors = await self.embedder.embed(chunks_text)
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}", exc_info=True)
            return IngestResult(indexed=0, skipped="embedding_failed")

        # Delete old chunks
        await self.repo.delete_by_source(
            org_id,
            "transcript",
            str(payload.conversation_id)
        )

        # Create new chunks
        chunk_objects = []
        for i, (text, embedding) in enumerate(zip(chunks_text, vectors)):
            chunk = TextChunk(
                id=uuid4(),
                org_id=org_id,
                source_type="transcript",
                source_id=str(payload.conversation_id),
                patient_id=conversation.patient_id,
                locator={
                    "conversation_id": str(payload.conversation_id)
                },
                text=text,
                chunk_index=i,
                embedding=embedding
            )
            chunk_objects.append(chunk)

        # Insert chunks
        await self.repo.insert_chunks(chunk_objects)
        self.db.commit()

        # Publish event
        await publish_event(
            event_type=EventType.CUSTOM,
            org_id=org_id,
            resource_type="text_chunk",
            resource_id=payload.conversation_id,
            data={
                "source_type": "transcript",
                "chunks_indexed": len(chunk_objects)
            }
        )

        logger.info(
            f"Indexed {len(chunk_objects)} chunks for conversation {payload.conversation_id}"
        )

        return IngestResult(indexed=len(chunk_objects))

    async def ingest_message(
        self,
        org_id: UUID,
        payload: IngestMessageTranscript
    ) -> IngestResult:
        """
        Ingest transcript for a single message

        Similar to ingest_conversation but for a single message.
        """
        # Simplified implementation - return empty for now
        # In production, load message, check consent, chunk, embed, insert
        logger.info(f"ingest_message called for message {payload.message_id}")
        return IngestResult(indexed=0, skipped="not_implemented")

    async def ingest_ticket(
        self,
        org_id: UUID,
        payload: IngestTicketNotes
    ) -> IngestResult:
        """
        Ingest all notes for a ticket

        Process:
          1. Load ticket and verify access
          2. Load all ticket notes
          3. Concatenate or individually chunk notes
          4. Generate embeddings
          5. Delete old chunks
          6. Insert new chunks
        """
        # Load ticket
        query = select(Ticket).where(
            Ticket.id == payload.ticket_id,
            Ticket.org_id == org_id
        )
        result = self.db.execute(query)
        ticket = result.scalar_one_or_none()

        if not ticket:
            logger.warning(f"Ticket {payload.ticket_id} not found")
            return IngestResult(indexed=0)

        # For simplified implementation, use ticket description
        text = ticket.description or f"Ticket {ticket.id}"

        # Chunk text
        chunks_text = self._chunk_text(
            text,
            payload.chunk_chars,
            payload.overlap
        )

        if not chunks_text:
            return IngestResult(indexed=0)

        # Generate embeddings
        try:
            vectors = await self.embedder.embed(chunks_text)
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}", exc_info=True)
            return IngestResult(indexed=0, skipped="embedding_failed")

        # Delete old chunks
        await self.repo.delete_by_source(
            org_id,
            "ticket_note",
            str(payload.ticket_id)
        )

        # Create new chunks
        chunk_objects = []
        for i, (text, embedding) in enumerate(zip(chunks_text, vectors)):
            chunk = TextChunk(
                id=uuid4(),
                org_id=org_id,
                source_type="ticket_note",
                source_id=str(payload.ticket_id),
                patient_id=None,
                locator={
                    "ticket_id": str(payload.ticket_id)
                },
                text=text,
                chunk_index=i,
                embedding=embedding
            )
            chunk_objects.append(chunk)

        # Insert chunks
        await self.repo.insert_chunks(chunk_objects)
        self.db.commit()

        # Publish event
        await publish_event(
            event_type=EventType.CUSTOM,
            org_id=org_id,
            resource_type="text_chunk",
            resource_id=payload.ticket_id,
            data={
                "source_type": "ticket_note",
                "chunks_indexed": len(chunk_objects)
            }
        )

        logger.info(
            f"Indexed {len(chunk_objects)} chunks for ticket {payload.ticket_id}"
        )

        return IngestResult(indexed=len(chunk_objects))

    async def ingest_knowledge(
        self,
        org_id: UUID,
        payload: IngestKnowledge
    ) -> IngestResult:
        """
        Ingest free-text knowledge document

        Process:
          1. Chunk the provided text
          2. Generate embeddings
          3. Create synthetic source_id (UUID)
          4. Insert chunks

        No deletion of old chunks since each knowledge doc gets unique ID.

        Returns:
            IngestResult with source_id for future reference
        """
        # Chunk text
        chunks_text = self._chunk_text(
            payload.text,
            payload.chunk_chars,
            payload.overlap
        )

        if not chunks_text:
            return IngestResult(indexed=0)

        # Generate embeddings
        try:
            vectors = await self.embedder.embed(chunks_text)
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}", exc_info=True)
            return IngestResult(indexed=0, skipped="embedding_failed")

        # Generate unique source_id
        source_id = str(uuid4())

        # Create chunks
        chunk_objects = []
        for i, (text, embedding) in enumerate(zip(chunks_text, vectors)):
            chunk = TextChunk(
                id=uuid4(),
                org_id=org_id,
                source_type="knowledge",
                source_id=source_id,
                patient_id=payload.patient_id,
                locator={
                    "title": payload.title
                },
                text=text,
                chunk_index=i,
                embedding=embedding
            )
            chunk_objects.append(chunk)

        # Insert chunks
        await self.repo.insert_chunks(chunk_objects)
        self.db.commit()

        # Publish event
        await publish_event(
            event_type=EventType.CUSTOM,
            org_id=org_id,
            resource_type="text_chunk",
            resource_id=uuid4(),  # No specific resource
            data={
                "source_type": "knowledge",
                "source_id": source_id,
                "chunks_indexed": len(chunk_objects),
                "title": payload.title
            }
        )

        logger.info(
            f"Indexed {len(chunk_objects)} chunks for knowledge document '{payload.title}'"
        )

        return IngestResult(
            indexed=len(chunk_objects),
            source_id=source_id
        )

    # ==================== Search ====================

    async def search(
        self,
        org_id: UUID,
        payload: SearchQuery
    ) -> List[Dict[str, Any]]:
        """
        Semantic search across indexed chunks

        Process:
          1. Generate embedding for query
          2. Execute hybrid search (vector + FTS)
          3. Check patient consent for results
          4. Return scored results

        Args:
            org_id: Organization ID
            payload: Search query

        Returns:
            List of search results with scores
        """
        # Generate query embedding
        try:
            query_embeddings = await self.embedder.embed([payload.q])
            query_vec = query_embeddings[0]
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}", exc_info=True)
            return []

        # Execute hybrid search
        results = await self.repo.search_hybrid(
            org_id=org_id,
            query_vec=query_vec,
            query_text=payload.q,
            top_k=payload.top_k,
            patient_id=payload.patient_id,
            source_type=payload.source_type
        )

        # TODO: Check patient consent for each result
        # For now, return all results

        # Format results
        formatted_results = []
        for chunk, score in results:
            formatted_results.append({
                "id": str(chunk.id),
                "org_id": str(chunk.org_id),
                "source_type": chunk.source_type,
                "source_id": chunk.source_id,
                "patient_id": str(chunk.patient_id) if chunk.patient_id else None,
                "locator": chunk.locator,
                "text": chunk.text,
                "chunk_index": chunk.chunk_index,
                "score": round(score, 6)
            })

        logger.info(
            f"Search for '{payload.q}' returned {len(formatted_results)} results"
        )

        return formatted_results

    # ==================== Management ====================

    async def get_statistics(
        self,
        org_id: UUID
    ) -> VectorStatistics:
        """Get statistics about indexed chunks"""
        stats = await self.repo.get_statistics(org_id)

        # Calculate average chunk length
        # TODO: Implement this in repository if needed
        avg_chunk_length = 0.0

        return VectorStatistics(
            total_chunks=stats["total_chunks"],
            total_sources=len(stats["by_source_type"]),
            by_source_type=stats["by_source_type"],
            by_patient=stats["by_patient"],
            avg_chunk_length=avg_chunk_length
        )

    async def delete_source(
        self,
        org_id: UUID,
        source_type: str,
        source_id: str
    ) -> int:
        """Delete all chunks for a source"""
        count = await self.repo.delete_by_source(org_id, source_type, source_id)
        self.db.commit()

        logger.info(f"Deleted {count} chunks for {source_type}:{source_id}")

        return count
