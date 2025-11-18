"""
Voice Agent Webhook Schemas
Request/Response models for Zucol/Zoice webhook integration
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator
from enum import Enum


# ==================== Enums ====================

class VoiceCallIntent(str, Enum):
    """Detected intent from voice call"""
    BOOK_APPOINTMENT = "book_appointment"
    CANCEL_APPOINTMENT = "cancel_appointment"
    RESCHEDULE_APPOINTMENT = "reschedule_appointment"
    INQUIRY = "inquiry"
    EMERGENCY = "emergency"
    COMPLAINT = "complaint"
    FOLLOWUP = "followup"
    OTHER = "other"


class VoiceCallOutcome(str, Enum):
    """Call outcome"""
    APPOINTMENT_BOOKED = "appointment_booked"
    APPOINTMENT_CANCELLED = "appointment_cancelled"
    QUERY_ANSWERED = "query_answered"
    TRANSFERRED_TO_HUMAN = "transferred_to_human"
    VOICEMAIL = "voicemail"
    NO_ANSWER = "no_answer"
    CALL_FAILED = "call_failed"
    OTHER = "other"


# ==================== Voice Agent Webhook Request ====================

class VoiceAgentWebhookRequest(BaseModel):
    """
    Webhook payload from Zucol/Zoice voice agent
    Sent after call completion with full call data
    """

    # Call identifiers
    call_id: UUID = Field(..., description="Unique call ID from Zoice")
    plivo_call_id: Optional[str] = Field(None, description="Telephony provider call ID")

    # Call participants
    patient_phone: str = Field(..., description="Patient phone number (E.164 format)")
    agent_phone: Optional[str] = Field(None, description="Voice agent phone number")

    # Call metadata
    call_type: str = Field(..., description="inbound or outbound")
    pipeline_id: Optional[UUID] = Field(None, description="Zoice pipeline ID")
    agent_name: Optional[str] = Field(None, description="Name of voice agent")

    # Call timing
    started_at: datetime = Field(..., description="When call started")
    ended_at: datetime = Field(..., description="When call ended")
    duration_seconds: int = Field(..., ge=0, description="Total call duration")

    # Call audio & transcript
    recording_url: str = Field(..., description="URL to call recording")
    transcript: str = Field(..., description="Full call transcript")
    turns: Optional[List[Dict[str, Any]]] = Field(None, description="Turn-by-turn conversation")

    # AI/NLP analysis
    detected_intent: Optional[VoiceCallIntent] = Field(None, description="Detected intent")
    call_outcome: Optional[VoiceCallOutcome] = Field(None, description="Call outcome")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence")

    # Extracted structured data
    extracted_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured data extracted (patient info, appointment details, etc.)"
    )

    # Quality metrics
    audio_quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    transcription_quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Language and sentiment
    language: Optional[str] = Field(None, description="Language code (en, hi, es, etc.)")
    sentiment: Optional[str] = Field(None, description="Overall call sentiment")

    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator("patient_phone")
    def validate_phone_format(cls, v):
        """Ensure E.164 format"""
        cleaned = "".join(c for c in v if c.isdigit() or c == "+")
        if not cleaned.startswith("+"):
            cleaned = "+" + cleaned
        if len(cleaned) < 10:
            raise ValueError("Phone number too short")
        return cleaned


# ==================== Extracted Data Schemas ====================

class AppointmentBookingExtraction(BaseModel):
    """Appointment booking data extracted from call"""
    patient_name: Optional[str] = None
    patient_dob: Optional[str] = None
    practitioner_name: Optional[str] = None
    practitioner_specialty: Optional[str] = None
    preferred_date: Optional[str] = None  # Free-form: "tomorrow", "next Monday"
    preferred_time: Optional[str] = None  # Free-form: "10:00 AM", "morning"
    location: Optional[str] = None
    reason: Optional[str] = None
    symptoms: Optional[List[str]] = None
    chief_complaint: Optional[str] = None
    urgency: Optional[str] = None  # routine, urgent, emergency


class PatientInfoExtraction(BaseModel):
    """Patient information extracted from call"""
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None


# ==================== Response Schemas ====================

class VoiceCallWebhookResponse(BaseModel):
    """Response to voice agent webhook"""
    success: bool
    message: str
    call_record_id: Optional[UUID] = None  # ID of created VoiceCall record
    patient_id: Optional[UUID] = None  # Patient ID if identified
    appointment_id: Optional[UUID] = None  # Appointment ID if booked
    conversation_id: Optional[UUID] = None  # Conversation thread ID
    actions_taken: List[str] = Field(default_factory=list)  # ["patient_created", "appointment_booked"]
    errors: List[str] = Field(default_factory=list)


# ==================== Tool Call Requests (from Voice Agent during call) ====================

class VoiceAgentToolRequest(BaseModel):
    """Base request for tool calls from voice agent"""
    call_id: UUID = Field(..., description="Current call ID")
    tenant_id: UUID = Field(..., description="Tenant ID")


class PatientLookupRequest(VoiceAgentToolRequest):
    """Request to lookup patient by phone"""
    phone: str = Field(..., description="Patient phone number")


class AvailableSlotsRequest(VoiceAgentToolRequest):
    """Request to get available appointment slots"""
    practitioner_name: Optional[str] = None
    specialty: Optional[str] = None
    location: Optional[str] = None
    preferred_date: Optional[str] = None  # YYYY-MM-DD or relative like "tomorrow"
    preferred_time: Optional[str] = None  # HH:MM or relative like "morning"


class BookAppointmentRequest(VoiceAgentToolRequest):
    """Request to book an appointment during call"""
    patient_phone: str
    patient_name: Optional[str] = None
    slot_datetime: datetime
    practitioner_id: Optional[UUID] = None
    practitioner_name: Optional[str] = None
    location_id: Optional[UUID] = None
    location_name: Optional[str] = None
    reason: Optional[str] = None
    chief_complaint: Optional[str] = None


# ==================== Tool Call Responses ====================

class PatientLookupResponse(BaseModel):
    """Response for patient lookup"""
    found: bool
    patient_id: Optional[UUID] = None
    patient_name: Optional[str] = None
    patient_data: Optional[Dict[str, Any]] = None


class AppointmentSlot(BaseModel):
    """Available appointment slot"""
    datetime: datetime
    practitioner_name: str
    practitioner_id: UUID
    location_name: str
    location_id: UUID
    duration_minutes: int = 30
    formatted_time: str  # "Monday, Nov 20 at 10:00 AM"


class AvailableSlotsResponse(BaseModel):
    """Response for available slots query"""
    slots: List[AppointmentSlot]
    total_found: int


class BookAppointmentResponse(BaseModel):
    """Response for appointment booking"""
    success: bool
    appointment_id: Optional[UUID] = None
    message: str
    confirmation_details: Optional[Dict[str, Any]] = None
