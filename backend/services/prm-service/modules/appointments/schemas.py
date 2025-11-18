"""
Appointment Schemas
Request/Response models for appointment booking and management
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator
from enum import Enum


# ==================== Enums ====================

class AppointmentStatus(str, Enum):
    """Appointment lifecycle status"""
    REQUESTED = "requested"
    PENDING_CONFIRM = "pending_confirm"
    CONFIRMED = "confirmed"
    RESCHEDULED = "rescheduled"
    CANCELED = "canceled"
    NO_SHOW = "no_show"
    COMPLETED = "completed"


class AppointmentChannel(str, Enum):
    """How appointment was booked"""
    WHATSAPP = "whatsapp"
    PHONE = "phone"
    WEB = "web"
    IN_PERSON = "in_person"
    VOICE_AGENT = "voice_agent"


class SlotSelectionAction(str, Enum):
    """User action during slot selection"""
    CONFIRM = "confirm_slot"
    REJECT = "reject_slots"
    CANCEL = "cancel_booking"
    AMBIGUOUS = "ambiguous"


# ==================== Slot Models ====================

class AppointmentSlot(BaseModel):
    """Available appointment slot"""
    slot_datetime: datetime = Field(..., description="Slot start time")
    practitioner_name: str = Field(..., description="Practitioner name")
    practitioner_id: Optional[UUID] = None
    location_name: str = Field(..., description="Location/clinic name")
    location_id: Optional[UUID] = None
    duration_minutes: int = Field(30, description="Appointment duration")
    specialty: Optional[str] = None

    @property
    def formatted_datetime(self) -> str:
        """Human-readable date/time"""
        return self.slot_datetime.strftime("%A, %B %d at %I:%M %p")

    @property
    def formatted_date(self) -> str:
        """Human-readable date"""
        return self.slot_datetime.strftime("%A, %B %d")

    @property
    def formatted_time(self) -> str:
        """Human-readable time"""
        return self.slot_datetime.strftime("%I:%M %p")


class SlotsAvailable(BaseModel):
    """List of available slots for presentation"""
    conversation_id: UUID
    slots: List[AppointmentSlot]
    message_to_user: str = Field(
        ...,
        description="Formatted message with slot options"
    )
    total_slots: int = Field(..., ge=0)

    @validator("total_slots", always=True)
    def validate_total_slots(cls, v, values):
        if "slots" in values:
            return len(values["slots"])
        return v


# ==================== Request Schemas ====================

class AppointmentBookingRequest(BaseModel):
    """Request to book appointment"""
    conversation_id: UUID
    patient_id: Optional[UUID] = None
    patient_phone: str = Field(..., description="Patient phone number")

    # Booking preferences
    preferred_practitioner: Optional[str] = None
    preferred_specialty: Optional[str] = None
    preferred_location: Optional[str] = None
    preferred_date: Optional[str] = None  # Free-form: "tomorrow", "next Monday"
    preferred_time: Optional[str] = None  # Free-form: "morning", "10:00 AM"

    # Appointment details
    reason: Optional[str] = None
    chief_complaint: Optional[str] = None

    # Channel
    channel: AppointmentChannel = AppointmentChannel.WHATSAPP


class SlotSelectionReply(BaseModel):
    """Patient's reply to slot options"""
    conversation_id: UUID
    user_text: str = Field(..., description="User's message text")
    available_slots: List[AppointmentSlot] = Field(
        ...,
        description="Slots that were presented to user"
    )


class AppointmentConfirmation(BaseModel):
    """Confirm specific appointment slot"""
    conversation_id: UUID
    selected_slot: AppointmentSlot
    patient_id: UUID
    patient_phone: str


class AppointmentUpdate(BaseModel):
    """Update existing appointment"""
    status: Optional[AppointmentStatus] = None
    confirmed_start: Optional[datetime] = None
    confirmed_end: Optional[datetime] = None
    notes: Optional[str] = None


# ==================== Response Schemas ====================

class AppointmentResponse(BaseModel):
    """Appointment response"""
    id: UUID
    patient_id: UUID
    practitioner_id: Optional[UUID]
    practitioner_name: Optional[str]
    location_id: Optional[UUID]
    location_name: Optional[str]
    status: AppointmentStatus
    confirmed_start: Optional[datetime]
    confirmed_end: Optional[datetime]
    channel_origin: str
    reason: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookingResult(BaseModel):
    """Result of booking operation"""
    success: bool
    message: str
    appointment_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    action_taken: str  # "slots_sent", "appointment_confirmed", "booking_failed"
    errors: List[str] = Field(default_factory=list)


class SlotSelectionResult(BaseModel):
    """Result of slot selection processing"""
    success: bool
    message: str
    action: SlotSelectionAction
    appointment_id: Optional[UUID] = None
    needs_clarification: bool = False
    follow_up_message: Optional[str] = None


# ==================== n8n Integration Schemas ====================

class BookingIntentData(BaseModel):
    """Booking intent extracted from conversation"""
    patient_name: Optional[str] = None
    patient_dob: Optional[str] = None
    chief_complaint: Optional[str] = None
    symptoms: Optional[str] = None
    preferred_practitioner: Optional[str] = None
    preferred_specialty: Optional[str] = None
    preferred_location: Optional[str] = None
    preferred_day: Optional[str] = None
    preferred_time: Optional[str] = None
    department: Optional[str] = None  # AI-determined department


class SlotPreferences(BaseModel):
    """Preferences for slot filtering"""
    preferred_day: Optional[int] = Field(
        None,
        description="Day of week (0=Monday, 6=Sunday)"
    )
    preferred_time_minutes: Optional[int] = Field(
        None,
        description="Preferred time as minutes from midnight (e.g., 600 = 10:00 AM)"
    )
    preferred_location: Optional[str] = None
    preferred_practitioner: Optional[str] = None
    department: Optional[str] = None  # Specialty/department


# ==================== List/Filter Schemas ====================

class AppointmentListFilters(BaseModel):
    """Filters for listing appointments"""
    patient_id: Optional[UUID] = None
    practitioner_id: Optional[UUID] = None
    status: Optional[AppointmentStatus] = None
    channel: Optional[AppointmentChannel] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)
