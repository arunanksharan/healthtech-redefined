"""
Vector Router
API endpoints for semantic search and text ingestion
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from loguru import logger

from shared.database.connection import get_db

from modules.vector.schemas import (
    IngestTranscriptsByConversation,
    IngestMessageTranscript,
    IngestTicketNotes,
    IngestKnowledge,
    SearchQuery,
    ChunkOut,
    IngestResult,
    VectorStatistics
)
from modules.vector.service import VectorService


router = APIRouter(prefix="/vector", tags=["Vector Search"])


# ==================== Ingest Endpoints ====================

@router.post("/ingest/conversation", response_model=IngestResult, status_code=201)
async def ingest_conversation(
    payload: IngestTranscriptsByConversation,
    db: Session = Depends(get_db)
):
    """
    Ingest all message transcripts for a conversation

    Process:
      1. Loads all messages with transcripts for the conversation
      2. Chunks each transcript into manageable sizes
      3. Generates embeddings for each chunk
      4. Deletes old chunks for this conversation
      5. Inserts new chunks

    Use case:
      - After conversation ends, index for future search
      - Re-index after conversation is updated

    Chunking parameters:
      - chunk_chars: 800 (recommended 200-4000)
      - overlap: 120 (recommended 0-1000)

    Consent:
      - If conversation is linked to patient, requires data_processing consent
      - If no consent, returns indexed=0 with skipped="consent_required"
    """
    service = VectorService(db)

    try:
        # TODO: Get org_id from auth context
        # For now, using hardcoded value
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")

        result = await service.ingest_conversation(org_id, payload)
        return result

    except Exception as e:
        logger.error(f"Error ingesting conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/ingest/message", response_model=IngestResult, status_code=201)
async def ingest_message(
    payload: IngestMessageTranscript,
    db: Session = Depends(get_db)
):
    """
    Ingest transcript for a single message

    Similar to ingest_conversation but for a single message.
    Useful for real-time indexing as messages arrive.

    NOTE: Currently not implemented - returns indexed=0
    """
    service = VectorService(db)

    try:
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")
        result = await service.ingest_message(org_id, payload)
        return result

    except Exception as e:
        logger.error(f"Error ingesting message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/ingest/ticket", response_model=IngestResult, status_code=201)
async def ingest_ticket_notes(
    payload: IngestTicketNotes,
    db: Session = Depends(get_db)
):
    """
    Ingest all notes for a support ticket

    Process:
      1. Loads all notes for the ticket
      2. Chunks combined notes or individual notes
      3. Generates embeddings
      4. Deletes old chunks for this ticket
      5. Inserts new chunks

    Use case:
      - Index ticket notes for similarity search
      - Find related tickets by content
      - Auto-suggest solutions based on similar tickets
    """
    service = VectorService(db)

    try:
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")
        result = await service.ingest_ticket(org_id, payload)
        return result

    except Exception as e:
        logger.error(f"Error ingesting ticket: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/ingest/knowledge", response_model=IngestResult, status_code=201)
async def ingest_knowledge(
    payload: IngestKnowledge,
    db: Session = Depends(get_db)
):
    """
    Ingest free-text knowledge document

    Process:
      1. Chunks the provided text
      2. Generates embeddings
      3. Creates unique source_id for the document
      4. Inserts chunks

    Use case:
      - Index policy documents
      - Index FAQs
      - Index treatment protocols
      - Index medical guidelines

    Returns source_id that can be used to:
      - Reference the document
      - Delete it later if needed

    Example:
    ```json
    {
      "title": "HIPAA Privacy Policy",
      "text": "The Health Insurance Portability...",
      "chunk_chars": 1000,
      "overlap": 150
    }
    ```
    """
    service = VectorService(db)

    try:
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")
        result = await service.ingest_knowledge(org_id, payload)
        return result

    except Exception as e:
        logger.error(f"Error ingesting knowledge: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


# ==================== Search Endpoints ====================

@router.post("/search", response_model=List[ChunkOut])
async def search(
    payload: SearchQuery,
    db: Session = Depends(get_db)
):
    """
    Semantic search across indexed content

    Algorithm:
      1. Generates embedding for query text
      2. Executes hybrid search:
         - Vector similarity (L2 distance)
         - Full-text search (PostgreSQL ts_rank)
         - Combined score: similarity + (0.3 * fts_rank)
      3. Checks patient consent for results
      4. Returns top_k results sorted by score

    Parameters:
      - q: Search query (1-1000 chars)
      - top_k: Number of results (1-50, default 10)
      - patient_id: Optional filter by patient
      - source_type: Optional filter (transcript, ticket_note, knowledge)

    Returns:
      List of chunks with relevance scores (higher = more relevant)

    Example:
    ```json
    {
      "q": "patient reported headache",
      "top_k": 10,
      "source_type": "transcript"
    }
    ```

    Response:
    ```json
    [
      {
        "id": "uuid",
        "text": "Patient mentioned severe headache...",
        "score": 0.92,
        "source_type": "transcript",
        "source_id": "conversation-uuid",
        "locator": {"conversation_id": "...", "message_id": "..."}
      }
    ]
    ```
    """
    service = VectorService(db)

    try:
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")
        results = await service.search(org_id, payload)
        return results

    except Exception as e:
        logger.error(f"Error executing search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# ==================== Management Endpoints ====================

@router.get("/stats", response_model=VectorStatistics)
async def get_statistics(
    db: Session = Depends(get_db)
):
    """
    Get vector search statistics

    Returns:
      - total_chunks: Total indexed chunks
      - total_sources: Number of unique sources
      - by_source_type: Count by type (transcript, ticket_note, knowledge)
      - by_patient: Top 10 patients by chunk count
      - avg_chunk_length: Average characters per chunk
    """
    service = VectorService(db)

    try:
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")
        stats = await service.get_statistics(org_id)
        return stats

    except Exception as e:
        logger.error(f"Error getting statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.delete("/source/{source_type}/{source_id}")
async def delete_source(
    source_type: str,
    source_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete all chunks for a given source

    Use cases:
      - Remove indexed conversation when deleted
      - Remove indexed ticket when deleted
      - Remove knowledge document

    Parameters:
      - source_type: transcript, ticket_note, or knowledge
      - source_id: UUID of the source

    Returns:
      Number of chunks deleted
    """
    service = VectorService(db)

    try:
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")
        count = await service.delete_source(org_id, source_type, source_id)

        return {
            "deleted": count,
            "source_type": source_type,
            "source_id": source_id
        }

    except Exception as e:
        logger.error(f"Error deleting source: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")


# ==================== Health Check ====================

@router.get("/health/check")
async def vector_health_check():
    """Health check for vector search module"""
    from core.embeddings import embeddings_service

    embeddings_status = "configured" if embeddings_service.client else "not_configured"

    return {
        "status": "healthy",
        "module": "vector",
        "features": [
            "semantic_search",
            "hybrid_search",
            "text_chunking",
            "multi_source_ingestion"
        ],
        "embeddings": embeddings_status,
        "embedding_model": "text-embedding-3-small",
        "embedding_dimensions": 384,
        "note": "Using JSON storage for embeddings. For production, migrate to pgvector extension."
    }
