"""
Vector Repository
Database operations for text chunks and semantic search
"""
from typing import List, Tuple, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func, desc, delete as sql_delete
from datetime import datetime
from loguru import logger
import numpy as np

from shared.database.models import TextChunk


class VectorRepository:
    """Repository for vector search operations"""

    def __init__(self, db: Session):
        self.db = db

    async def delete_by_source(
        self,
        org_id: UUID,
        source_type: str,
        source_id: str
    ) -> int:
        """
        Soft delete all chunks for a given source

        Used before re-indexing to remove stale chunks.
        """
        query = select(TextChunk).where(
            and_(
                TextChunk.org_id == org_id,
                TextChunk.source_type == source_type,
                TextChunk.source_id == source_id,
                TextChunk.deleted_at.is_(None)
            )
        )

        result = self.db.execute(query)
        chunks = result.scalars().all()

        count = 0
        for chunk in chunks:
            chunk.deleted_at = datetime.utcnow()
            count += 1

        if count > 0:
            self.db.flush()
            logger.debug(f"Soft deleted {count} chunks for {source_type}:{source_id}")

        return count

    async def insert_chunks(self, chunks: List[TextChunk]) -> None:
        """
        Bulk insert text chunks

        Args:
            chunks: List of TextChunk objects to insert
        """
        if not chunks:
            return

        self.db.add_all(chunks)
        self.db.flush()

        logger.debug(f"Inserted {len(chunks)} text chunks")

    async def search_hybrid(
        self,
        org_id: UUID,
        query_vec: List[float],
        query_text: str,
        *,
        top_k: int = 10,
        patient_id: Optional[UUID] = None,
        source_type: Optional[str] = None
    ) -> List[Tuple[TextChunk, float]]:
        """
        Hybrid search: Vector similarity + Full-text search

        Algorithm:
          1. Calculate L2 distance between query_vec and chunk embeddings
          2. Calculate full-text search rank using PostgreSQL ts_rank
          3. Combine scores: similarity + (0.3 * fts_rank)
          4. Return top_k results sorted by combined score

        NOTE: This is a simplified implementation using Python-based similarity.
        For production with pgvector:
          - Use database-side vector operations (much faster)
          - Use ivfflat or hnsw indexes
          - Use pgvector's distance operators (<->, <#>, <=>)

        Args:
            org_id: Organization ID
            query_vec: Query embedding vector
            query_text: Query text for full-text search
            top_k: Number of results to return
            patient_id: Optional patient filter
            source_type: Optional source type filter

        Returns:
            List of (TextChunk, score) tuples, sorted by score descending
        """
        # Build base query
        conditions = [
            TextChunk.org_id == org_id,
            TextChunk.deleted_at.is_(None)
        ]

        if patient_id:
            conditions.append(TextChunk.patient_id == patient_id)

        if source_type:
            conditions.append(TextChunk.source_type == source_type)

        # Full-text search rank
        # Uses PostgreSQL's tsvector and ts_rank functions
        tsvec = func.to_tsvector('simple', TextChunk.text)
        tsq = func.plainto_tsquery('simple', query_text)
        fts_rank = func.ts_rank_cd(tsvec, tsq).label("fts_rank")

        # Execute query
        query = (
            select(TextChunk, fts_rank)
            .where(and_(*conditions))
        )

        result = self.db.execute(query)
        rows = result.all()

        if not rows:
            return []

        # Calculate vector similarity scores in Python
        # NOTE: In production with pgvector, this would be done in the database
        scored_results = []

        query_vec_np = np.array(query_vec)

        for chunk, fts_rank_value in rows:
            # Get chunk embedding
            chunk_vec_np = np.array(chunk.embedding)

            # Calculate L2 distance
            distance = np.linalg.norm(query_vec_np - chunk_vec_np)

            # Convert distance to similarity (inverse)
            vector_sim = 1.0 / (1.0 + distance)

            # Combine vector similarity with FTS rank (weighted 70/30)
            combined_score = vector_sim + (0.3 * float(fts_rank_value if fts_rank_value else 0))

            scored_results.append((chunk, combined_score))

        # Sort by score descending and take top_k
        scored_results.sort(key=lambda x: x[1], reverse=True)

        return scored_results[:top_k]

    async def get_statistics(
        self,
        org_id: UUID
    ) -> dict:
        """
        Get statistics about indexed chunks

        Returns:
            Dict with statistics:
            - total_chunks
            - by_source_type
            - by_patient
        """
        # Total chunks
        total_query = select(func.count(TextChunk.id)).where(
            and_(
                TextChunk.org_id == org_id,
                TextChunk.deleted_at.is_(None)
            )
        )
        total_result = self.db.execute(total_query)
        total_chunks = total_result.scalar() or 0

        # By source type
        by_type_query = (
            select(
                TextChunk.source_type,
                func.count(TextChunk.id).label('count')
            )
            .where(
                and_(
                    TextChunk.org_id == org_id,
                    TextChunk.deleted_at.is_(None)
                )
            )
            .group_by(TextChunk.source_type)
        )
        by_type_result = self.db.execute(by_type_query)
        by_source_type = {row[0]: row[1] for row in by_type_result.all()}

        # By patient (top 10)
        by_patient_query = (
            select(
                TextChunk.patient_id,
                func.count(TextChunk.id).label('count')
            )
            .where(
                and_(
                    TextChunk.org_id == org_id,
                    TextChunk.deleted_at.is_(None),
                    TextChunk.patient_id.isnot(None)
                )
            )
            .group_by(TextChunk.patient_id)
            .order_by(desc('count'))
            .limit(10)
        )
        by_patient_result = self.db.execute(by_patient_query)
        by_patient = {str(row[0]): row[1] for row in by_patient_result.all()}

        return {
            "total_chunks": total_chunks,
            "by_source_type": by_source_type,
            "by_patient": by_patient
        }

    async def get_chunk(
        self,
        chunk_id: UUID,
        org_id: UUID
    ) -> Optional[TextChunk]:
        """Get a single chunk by ID"""
        query = select(TextChunk).where(
            and_(
                TextChunk.id == chunk_id,
                TextChunk.org_id == org_id,
                TextChunk.deleted_at.is_(None)
            )
        )

        result = self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_chunks_by_source(
        self,
        org_id: UUID,
        source_type: str,
        source_id: str
    ) -> List[TextChunk]:
        """List all chunks for a given source"""
        query = (
            select(TextChunk)
            .where(
                and_(
                    TextChunk.org_id == org_id,
                    TextChunk.source_type == source_type,
                    TextChunk.source_id == source_id,
                    TextChunk.deleted_at.is_(None)
                )
            )
            .order_by(TextChunk.chunk_index)
        )

        result = self.db.execute(query)
        return result.scalars().all()
