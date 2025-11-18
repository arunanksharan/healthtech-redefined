"""
Voice & Collaboration Service Pydantic Schemas
Request/Response models for voice sessions, collaboration threads, and note revisions
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator


# ==================== Voice Session Schemas ====================

class VoiceSessionCreate(BaseModel):
    """Schema for creating a voice session"""

    tenant_id: UUID
    user_id: UUID
    encounter_id: Optional[UUID] = None
    session_type: str = Field(..., description="opd_consult, ward_round, handoff, procedure_note, discharge_summary")
    asr_model: str = Field(default="whisper-large-v3", description="ASR model to use")
    enable_diarization: bool = Field(default=True, description="Enable speaker diarization")
    language: str = Field(default="en", description="Primary language code")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for session")

    @validator("session_type")
    def validate_session_type(cls, v):
        valid_types = ["opd_consult", "ward_round", "handoff", "procedure_note", "discharge_summary", "team_discussion"]
        if v.lower() not in valid_types:
            raise ValueError(f"session_type must be one of: {', '.join(valid_types)}")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "user_id": "user-uuid-doctor-sharma",
                "encounter_id": "encounter-uuid-abc123",
                "session_type": "opd_consult",
                "asr_model": "whisper-large-v3",
                "enable_diarization": True,
                "language": "en",
                "context": {
                    "specialty": "CARDIOLOGY",
                    "patient_name": "John Doe"
                }
            }
        }


class VoiceSessionResponse(BaseModel):
    """Response schema for voice session"""

    id: UUID
    tenant_id: UUID
    user_id: UUID
    encounter_id: Optional[UUID] = None
    session_type: str
    asr_model: str
    enable_diarization: bool
    language: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    transcript: Optional[str] = None
    transcript_structured: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class VoiceSegmentCreate(BaseModel):
    """Schema for ingesting a transcript segment"""

    segment_index: int = Field(..., description="Sequential segment number")
    start_time: float = Field(..., description="Segment start time in seconds")
    end_time: float = Field(..., description="Segment end time in seconds")
    text: str = Field(..., description="Transcribed text")
    speaker_id: Optional[str] = Field(None, description="Speaker identifier (if diarization enabled)")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Transcription confidence")
    words: Optional[List[Dict[str, Any]]] = Field(None, description="Word-level timestamps")

    class Config:
        json_schema_extra = {
            "example": {
                "segment_index": 0,
                "start_time": 0.0,
                "end_time": 5.2,
                "text": "Patient presents with chest pain radiating to left arm",
                "speaker_id": "SPEAKER_00",
                "confidence": 0.95,
                "words": [
                    {"word": "Patient", "start": 0.0, "end": 0.4, "confidence": 0.98},
                    {"word": "presents", "start": 0.5, "end": 0.9, "confidence": 0.96}
                ]
            }
        }


class VoiceSegmentResponse(BaseModel):
    """Response schema for voice segment"""

    id: UUID
    voice_session_id: UUID
    segment_index: int
    start_time: float
    end_time: float
    text: str
    speaker_id: Optional[str] = None
    confidence: Optional[float] = None
    words: Optional[List[Dict[str, Any]]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FinalizeSessionRequest(BaseModel):
    """Request to finalize a voice session"""

    generate_note: bool = Field(default=True, description="Generate structured note from transcript")
    note_template: Optional[str] = Field(None, description="Template to use for note generation")


# ==================== Collaboration Thread Schemas ====================

class CollabThreadCreate(BaseModel):
    """Schema for creating a collaboration thread"""

    tenant_id: UUID
    patient_id: Optional[UUID] = None
    encounter_id: Optional[UUID] = None
    episode_id: Optional[UUID] = None
    title: str = Field(..., description="Thread title")
    thread_type: str = Field(..., description="case_discussion, mdr, tumor_board, discharge_planning, complex_care")
    description: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags for categorization")
    participants: List[UUID] = Field(..., description="List of user IDs")
    created_by: UUID

    @validator("thread_type")
    def validate_thread_type(cls, v):
        valid_types = ["case_discussion", "mdr", "tumor_board", "discharge_planning", "complex_care", "quality_review"]
        if v.lower() not in valid_types:
            raise ValueError(f"thread_type must be one of: {', '.join(valid_types)}")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "patient_id": "patient-uuid-abc123",
                "encounter_id": "encounter-uuid-xyz789",
                "title": "Complex DM case - insulin adjustment",
                "thread_type": "case_discussion",
                "description": "Patient with poorly controlled DM, need endocrine consult input",
                "tags": ["diabetes", "endocrine", "consult"],
                "participants": ["user-uuid-doctor-sharma", "user-uuid-doctor-patel"],
                "created_by": "user-uuid-doctor-sharma"
            }
        }


class CollabThreadUpdate(BaseModel):
    """Schema for updating a thread"""

    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = Field(None, description="active, resolved, archived")
    participants: Optional[List[UUID]] = None

    @validator("status")
    def validate_status(cls, v):
        if v:
            valid_statuses = ["active", "resolved", "archived"]
            if v.lower() not in valid_statuses:
                raise ValueError(f"status must be one of: {', '.join(valid_statuses)}")
            return v.lower()
        return v


class CollabThreadResponse(BaseModel):
    """Response schema for collaboration thread"""

    id: UUID
    tenant_id: UUID
    patient_id: Optional[UUID] = None
    encounter_id: Optional[UUID] = None
    episode_id: Optional[UUID] = None
    title: str
    thread_type: str
    description: Optional[str] = None
    tags: List[str]
    participants: List[UUID]
    created_by: UUID
    status: str
    message_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CollabThreadListResponse(BaseModel):
    """Response for list of threads"""

    total: int
    threads: List[CollabThreadResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== Collaboration Message Schemas ====================

class CollabMessageCreate(BaseModel):
    """Schema for creating a message in a thread"""

    content: str = Field(..., description="Message content (supports Markdown)")
    message_type: str = Field(default="user", description="user, ai_agent, system")
    author_id: Optional[UUID] = Field(None, description="User ID (for user messages)")
    agent_name: Optional[str] = Field(None, description="Agent name (for AI messages)")
    mentions: Optional[List[UUID]] = Field(default_factory=list, description="Mentioned user IDs")
    attachments: Optional[List[Dict[str, str]]] = Field(default_factory=list, description="Attached files/links")

    @validator("message_type")
    def validate_message_type(cls, v):
        valid_types = ["user", "ai_agent", "system"]
        if v.lower() not in valid_types:
            raise ValueError(f"message_type must be one of: {', '.join(valid_types)}")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "content": "Based on latest HbA1c of 9.2%, I recommend increasing insulin dose. @DrPatel what do you think?",
                "message_type": "user",
                "author_id": "user-uuid-doctor-sharma",
                "mentions": ["user-uuid-doctor-patel"],
                "attachments": [
                    {"type": "lab_result", "id": "lab-uuid-hba1c"}
                ]
            }
        }


class CollabMessageResponse(BaseModel):
    """Response schema for collaboration message"""

    id: UUID
    collab_thread_id: UUID
    content: str
    message_type: str
    author_id: Optional[UUID] = None
    agent_name: Optional[str] = None
    mentions: List[UUID]
    attachments: List[Dict[str, str]]
    created_at: datetime

    class Config:
        from_attributes = True


class CollabMessageListResponse(BaseModel):
    """Response for list of messages"""

    total: int
    messages: List[CollabMessageResponse]
    thread: CollabThreadResponse
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== Note Revision Schemas ====================

class NoteRevisionCreate(BaseModel):
    """Schema for creating a note revision"""

    tenant_id: UUID
    encounter_id: UUID
    note_type: str = Field(..., description="progress_note, discharge_summary, procedure_note, consult_note")
    content: str = Field(..., description="Note content (structured or free text)")
    format: str = Field(default="markdown", description="markdown, html, fhir_composition")
    author_id: UUID
    voice_session_id: Optional[UUID] = Field(None, description="Source voice session if generated from voice")
    ai_generated: bool = Field(default=False, description="Was this note AI-generated?")
    ai_model: Optional[str] = Field(None, description="AI model used (if ai_generated=true)")
    parent_revision_id: Optional[UUID] = Field(None, description="Previous revision ID (for versioning)")
    change_summary: Optional[str] = Field(None, description="Summary of changes from previous version")

    @validator("note_type")
    def validate_note_type(cls, v):
        valid_types = ["progress_note", "discharge_summary", "procedure_note", "consult_note", "admission_note", "op_note"]
        if v.lower() not in valid_types:
            raise ValueError(f"note_type must be one of: {', '.join(valid_types)}")
        return v.lower()

    @validator("format")
    def validate_format(cls, v):
        valid_formats = ["markdown", "html", "fhir_composition", "plain_text"]
        if v.lower() not in valid_formats:
            raise ValueError(f"format must be one of: {', '.join(valid_formats)}")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "encounter_id": "encounter-uuid-abc123",
                "note_type": "progress_note",
                "content": "# Progress Note\\n\\n**Chief Complaint:** Chest pain\\n\\n**Assessment:** Stable angina...",
                "format": "markdown",
                "author_id": "user-uuid-doctor-sharma",
                "voice_session_id": "voice-session-uuid",
                "ai_generated": True,
                "ai_model": "gpt-4",
                "change_summary": "AI-generated from voice session"
            }
        }


class NoteRevisionResponse(BaseModel):
    """Response schema for note revision"""

    id: UUID
    tenant_id: UUID
    encounter_id: UUID
    note_type: str
    content: str
    format: str
    author_id: UUID
    voice_session_id: Optional[UUID] = None
    ai_generated: bool
    ai_model: Optional[str] = None
    parent_revision_id: Optional[UUID] = None
    change_summary: Optional[str] = None
    revision_number: int
    is_final: bool
    finalized_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NoteRevisionListResponse(BaseModel):
    """Response for list of note revisions"""

    total: int
    revisions: List[NoteRevisionResponse]
    encounter_id: UUID
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


class MarkFinalRequest(BaseModel):
    """Request to mark a note revision as final"""

    finalized_by: UUID = Field(..., description="User ID marking the note as final")
    attestation: Optional[str] = Field(None, description="Attestation statement")
