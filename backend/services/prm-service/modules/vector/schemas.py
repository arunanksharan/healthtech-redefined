"""
Vector Module Schemas
Schemas for semantic search and text ingestion
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, validator


# ==================== Ingest Schemas ====================

class IngestTranscriptsByConversation(BaseModel):
    """Ingest all transcripts for a conversation"""
    conversation_id: UUID
    chunk_chars: int = Field(default=800, ge=200, le=4000, description="Characters per chunk")
    overlap: int = Field(default=120, ge=0, le=1000, description="Overlap between chunks")


class IngestMessageTranscript(BaseModel):
    """Ingest transcript for a single message"""
    message_id: UUID
    chunk_chars: int = Field(default=800, ge=200, le=4000)
    overlap: int = Field(default=120, ge=0, le=1000)


class IngestTicketNotes(BaseModel):
    """Ingest all notes for a ticket"""
    ticket_id: UUID
    chunk_chars: int = Field(default=800, ge=200, le=1000)
    overlap: int = Field(default=120, ge=0, le=500)


class IngestKnowledge(BaseModel):
    """Ingest free-text knowledge document"""
    title: Optional[str] = Field(None, max_length=200, description="Document title")
    text: str = Field(..., min_length=1, description="Document text")
    patient_id: Optional[UUID] = Field(None, description="Link to patient if applicable")
    chunk_chars: int = Field(default=1000, ge=200, le=4000)
    overlap: int = Field(default=150, ge=0, le=1000)

    @validator('text')
    def validate_text_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Text cannot be empty or whitespace only')
        return v.strip()


# ==================== Search Schemas ====================

class SearchQuery(BaseModel):
    """Semantic search query"""
    q: str = Field(..., min_length=1, max_length=1000, description="Search query")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of results")
    patient_id: Optional[UUID] = Field(None, description="Filter by patient")
    source_type: Optional[str] = Field(
        None,
        description="Filter by source type",
        pattern="^(transcript|ticket_note|knowledge)$"
    )

    @validator('q')
    def validate_query_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Search query cannot be empty')
        return v.strip()


class ChunkOut(BaseModel):
    """Search result chunk"""
    id: UUID
    org_id: UUID
    source_type: str
    source_id: str
    patient_id: Optional[UUID]
    locator: Optional[Dict[str, Any]]
    text: str
    chunk_index: int
    score: float = Field(..., description="Relevance score (higher is better)")

    class Config:
        from_attributes = True


# ==================== Management Schemas ====================

class IngestResult(BaseModel):
    """Result of ingestion operation"""
    indexed: int = Field(..., description="Number of chunks indexed")
    source_id: Optional[str] = Field(None, description="Generated source ID (for knowledge)")
    skipped: Optional[str] = Field(None, description="Reason for skipping (e.g., consent_required)")


class TextChunkResponse(BaseModel):
    """Text chunk response"""
    id: UUID
    org_id: UUID
    source_type: str
    source_id: str
    patient_id: Optional[UUID]
    locator: Optional[Dict[str, Any]]
    text: str
    chunk_index: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VectorStatistics(BaseModel):
    """Vector search statistics"""
    total_chunks: int
    total_sources: int
    by_source_type: Dict[str, int]
    by_patient: Dict[str, int] = Field(default_factory=dict, description="Top 10 patients by chunk count")
    avg_chunk_length: float
