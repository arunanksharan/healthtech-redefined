"""
Conversation Schemas
Request/Response models for conversation management
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator
from enum import Enum


# ==================== Enums ====================

class ConversationStatus(str, Enum):
    """Conversation lifecycle status"""
    OPEN = "open"
    PENDING = "pending"
    SNOOZED = "snoozed"
    CLOSED = "closed"


class ConversationPriority(str, Enum):
    """Conversation priority levels"""
    P0 = "p0"  # Critical
    P1 = "p1"  # High
    P2 = "p2"  # Medium (default)
    P3 = "p3"  # Low


class MessageDirection(str, Enum):
    """Message direction"""
    INBOUND = "inbound"   # From patient
    OUTBOUND = "outbound"  # To patient


class MessageActorType(str, Enum):
    """Who sent/received the message"""
    PATIENT = "patient"
    RELATED_PERSON = "related_person"
    AGENT = "agent"      # Human agent
    BOT = "bot"          # AI/automated
    SYSTEM = "system"    # System-generated


class MessageContentType(str, Enum):
    """Message content type"""
    TEXT = "text"
    MEDIA = "media"
    VOICE = "voice"
    FILE = "file"


class ChannelType(str, Enum):
    """Communication channel"""
    WHATSAPP = "whatsapp"
    SMS = "sms"
    EMAIL = "email"
    PHONE = "phone"
    WEBCHAT = "webchat"
    IN_PERSON = "in_person"


# ==================== Request Schemas ====================

class ConversationCreate(BaseModel):
    """Create new conversation"""
    patient_id: Optional[UUID] = None
    subject: Optional[str] = Field(None, max_length=200)
    status: ConversationStatus = ConversationStatus.OPEN
    priority: ConversationPriority = ConversationPriority.P2
    channel_type: ChannelType = ChannelType.WHATSAPP
    initial_message: Optional[str] = None  # First message to start conversation


class MessageCreate(BaseModel):
    """Create message in conversation"""
    conversation_id: UUID
    direction: MessageDirection
    actor_type: MessageActorType = MessageActorType.PATIENT
    content_type: MessageContentType = MessageContentType.TEXT
    text_body: Optional[str] = None
    media_url: Optional[str] = None
    locale: Optional[str] = "en-US"


class ConversationUpdate(BaseModel):
    """Update conversation"""
    subject: Optional[str] = Field(None, max_length=200)
    status: Optional[ConversationStatus] = None
    priority: Optional[ConversationPriority] = None
    current_owner_id: Optional[UUID] = None


class ConversationStateUpdate(BaseModel):
    """Update conversation state (from n8n/AI)"""
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    completed_fields: List[str] = Field(default_factory=list)
    next_field: Optional[str] = None
    ai_response: Optional[str] = None


# ==================== Response Schemas ====================

class MessageResponse(BaseModel):
    """Message response"""
    id: UUID
    conversation_id: UUID
    direction: MessageDirection
    actor_type: MessageActorType
    content_type: MessageContentType
    text_body: Optional[str]
    media_url: Optional[str]
    created_at: datetime
    sentiment: Optional[str] = None

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Conversation response"""
    id: UUID
    patient_id: Optional[UUID]
    subject: Optional[str]
    status: ConversationStatus
    priority: ConversationPriority
    current_owner_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0

    class Config:
        from_attributes = True


class ConversationDetailResponse(ConversationResponse):
    """Conversation with messages"""
    messages: List[MessageResponse] = Field(default_factory=list)


class ConversationStateResponse(BaseModel):
    """Current conversation state (from Redis)"""
    conversation_id: UUID
    patient_phone: Optional[str] = None
    required_fields: List[str] = Field(default_factory=list)
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    is_complete: bool = False
    message_count: int = 0
    created_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None


# ==================== State Management Schemas ====================

class IntakeField(str, Enum):
    """Standard intake fields"""
    PATIENT_NAME = "patient.name"
    PATIENT_DOB = "patient.dob"
    PATIENT_PHONE = "patient.phone"
    CHIEF_COMPLAINT = "intake.chief_complaint.text"
    SYMPTOMS = "intake.symptoms"
    CONDITION_HISTORY = "intake.condition_history"
    ALLERGIES = "intake.allergies"
    MEDICATIONS = "intake.medications"
    FAMILY_HISTORY = "intake.family_history"
    PREFERRED_LOCATION = "appointment_request.preferred_location"
    PREFERRED_DAY = "appointment_request.preferred_day"
    PREFERRED_TIME = "appointment_request.preferred_time"
    PRACTITIONER_NAME = "appointment_request.practitioner_name"
    SPECIALTY = "appointment_request.specialty"


class ConversationStateInit(BaseModel):
    """Initialize conversation state"""
    conversation_id: UUID
    patient_phone: str
    required_fields: List[str] = Field(
        default_factory=lambda: [
            IntakeField.PATIENT_NAME.value,
            IntakeField.PATIENT_DOB.value,
            IntakeField.CHIEF_COMPLAINT.value,
            IntakeField.SYMPTOMS.value,
            IntakeField.ALLERGIES.value,
            IntakeField.MEDICATIONS.value,
            IntakeField.PREFERRED_LOCATION.value,
            IntakeField.PREFERRED_DAY.value,
            IntakeField.PREFERRED_TIME.value,
        ]
    )
    initial_data: Dict[str, Any] = Field(default_factory=dict)


# ==================== List/Filter Schemas ====================

class ConversationListFilters(BaseModel):
    """Filters for listing conversations"""
    patient_id: Optional[UUID] = None
    status: Optional[ConversationStatus] = None
    priority: Optional[ConversationPriority] = None
    owner_id: Optional[UUID] = None
    search_query: Optional[str] = None  # Search in subject or messages
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)
