"""
Webhook Schemas
Request/Response models for Twilio and Voice Agent webhooks
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator
from enum import Enum


# ==================== Twilio Schemas ====================

class TwilioMessageType(str, Enum):
    """Twilio message type"""
    TEXT = "text"
    MEDIA = "media"


class TwilioWebhookPayload(BaseModel):
    """
    Twilio incoming message webhook payload

    This follows Twilio's WhatsApp API format:
    https://www.twilio.com/docs/whatsapp/api#incoming-message-webhooks
    """

    # Message identifiers
    MessageSid: str = Field(..., description="Unique message identifier")
    SmsSid: str = Field(..., description="Same as MessageSid for compatibility")

    # Participant phone numbers (E.164 format with whatsapp: prefix)
    From: str = Field(..., description="Sender phone (whatsapp:+1234567890)")
    To: str = Field(..., description="Recipient phone (whatsapp:+1234567890)")

    # Message content
    Body: str = Field(default="", description="Message text content")

    # Media attachments
    NumMedia: str = Field(default="0", description="Number of media files")

    # Additional fields (optional, populated if media present)
    MediaUrl0: Optional[str] = Field(None, description="URL of first media file")
    MediaContentType0: Optional[str] = Field(None, description="MIME type of first media")

    # Account information
    AccountSid: str = Field(..., description="Twilio account SID")
    MessagingServiceSid: Optional[str] = None

    # Status (for status callbacks)
    MessageStatus: Optional[str] = None

    @validator("From", "To")
    def normalize_phone_number(cls, v):
        """Extract phone number from whatsapp: prefix"""
        if v.startswith("whatsapp:"):
            return v.replace("whatsapp:", "")
        return v

    @validator("NumMedia")
    def convert_num_media(cls, v):
        """Convert NumMedia to integer"""
        try:
            return str(int(v))  # Keep as string but validate it's a number
        except (ValueError, TypeError):
            return "0"

    @property
    def has_media(self) -> bool:
        """Check if message has media attachments"""
        return int(self.NumMedia) > 0

    @property
    def message_type(self) -> TwilioMessageType:
        """Determine message type"""
        return TwilioMessageType.MEDIA if self.has_media else TwilioMessageType.TEXT

    @property
    def is_voice_message(self) -> bool:
        """Check if media is a voice message"""
        if not self.has_media or not self.MediaContentType0:
            return False
        return self.MediaContentType0.startswith("audio/")


class TwilioStatusCallback(BaseModel):
    """Twilio message status callback payload"""

    MessageSid: str
    MessageStatus: str  # queued, sending, sent, delivered, undelivered, failed
    ErrorCode: Optional[str] = None
    ErrorMessage: Optional[str] = None
    To: str
    From: str

    @validator("From", "To")
    def normalize_phone(cls, v):
        if v.startswith("whatsapp:"):
            return v.replace("whatsapp:", "")
        return v


# ==================== Voice Agent Schemas ====================

class VoiceAgentIntent(str, Enum):
    """Extracted intent from voice call"""
    BOOK_APPOINTMENT = "book_appointment"
    CANCEL_APPOINTMENT = "cancel_appointment"
    RESCHEDULE_APPOINTMENT = "reschedule_appointment"
    INQUIRY = "inquiry"
    EMERGENCY = "emergency"
    OTHER = "other"


class VoiceAgentWebhookPayload(BaseModel):
    """
    Voice agent (zoice) webhook payload
    Standardized format for call transcript processing
    """

    # Call identifiers
    call_id: UUID = Field(..., description="Unique call identifier")
    patient_phone: str = Field(..., description="Patient phone number (E.164)")

    # Call audio & transcript
    recording_url: str = Field(..., description="URL to call recording")
    transcript: str = Field(..., description="Full call transcript")

    # Extracted structured data
    extracted_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured data extracted from transcript"
    )

    # Call metadata
    duration_seconds: int = Field(..., ge=0, description="Call duration in seconds")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Transcription confidence")

    # Timestamps
    call_started_at: datetime = Field(..., description="When call started")
    call_ended_at: datetime = Field(..., description="When call ended")

    # Intent (if detected)
    detected_intent: Optional[VoiceAgentIntent] = None

    @validator("patient_phone")
    def validate_phone_format(cls, v):
        """Ensure E.164 format"""
        # Remove any non-digit characters except +
        cleaned = "".join(c for c in v if c.isdigit() or c == "+")

        # Add + if not present
        if not cleaned.startswith("+"):
            cleaned = "+" + cleaned

        # Basic validation
        if len(cleaned) < 10:
            raise ValueError("Phone number too short")

        return cleaned

    @property
    def is_booking_intent(self) -> bool:
        """Check if intent is appointment booking"""
        return self.detected_intent == VoiceAgentIntent.BOOK_APPOINTMENT

    @property
    def has_extracted_data(self) -> bool:
        """Check if structured data was extracted"""
        return bool(self.extracted_data)


class VoiceAgentExtractedData(BaseModel):
    """Structured data extracted from voice transcript"""

    # Patient information
    patient_name: Optional[str] = None

    # Appointment details
    practitioner_name: Optional[str] = None
    speciality: Optional[str] = None
    preferred_date: Optional[str] = None  # Free-form: "tomorrow", "next Monday", etc.
    preferred_time: Optional[str] = None  # Free-form: "10AM", "morning", etc.
    reason: Optional[str] = None

    # Confidence scores (per field)
    confidence_scores: Dict[str, float] = Field(default_factory=dict)


# ==================== Response Schemas ====================

class WebhookProcessingResult(BaseModel):
    """Result of webhook processing"""

    success: bool
    message: str
    conversation_id: Optional[UUID] = None
    action_taken: Optional[str] = None  # "message_stored", "booking_initiated", etc.
    errors: List[str] = Field(default_factory=list)


class WebhookHealthResponse(BaseModel):
    """Webhook health check response"""

    status: str  # "healthy", "degraded", "unhealthy"
    webhook_type: str  # "twilio", "voice_agent"
    last_received: Optional[datetime] = None
    total_processed: int = 0
    error_rate: float = 0.0
