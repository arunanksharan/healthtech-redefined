"""
Scheduling Service Pydantic Schemas
Request/Response models for scheduling operations
"""
from datetime import datetime, date, time
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, validator


# ==================== Provider Schedule Schemas ====================

class ProviderScheduleCreate(BaseModel):
    """Schema for creating provider schedule"""

    tenant_id: UUID
    practitioner_id: UUID
    location_id: UUID
    specialty_code: Optional[str] = None
    valid_from: date
    valid_to: Optional[date] = None
    day_of_week: int = Field(..., ge=1, le=7, description="1=Monday, 7=Sunday")
    start_time: time
    end_time: time
    slot_duration_minutes: int = Field(..., ge=5, le=120)
    max_patients_per_slot: int = Field(default=1, ge=1, le=10)

    @validator("end_time")
    def validate_end_time(cls, v, values):
        if "start_time" in values and v <= values["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v

    @validator("valid_to")
    def validate_valid_to(cls, v, values):
        if v and "valid_from" in values and v <= values["valid_from"]:
            raise ValueError("valid_to must be after valid_from")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "practitioner_id": "practitioner-uuid",
                "location_id": "location-uuid",
                "specialty_code": "CARDIOLOGY",
                "valid_from": "2025-01-15",
                "valid_to": "2025-12-31",
                "day_of_week": 1,
                "start_time": "09:00:00",
                "end_time": "17:00:00",
                "slot_duration_minutes": 15,
                "max_patients_per_slot": 1
            }
        }


class ProviderScheduleUpdate(BaseModel):
    """Schema for updating provider schedule"""

    valid_to: Optional[date] = None
    slot_duration_minutes: Optional[int] = Field(None, ge=5, le=120)
    max_patients_per_slot: Optional[int] = Field(None, ge=1, le=10)
    is_active: Optional[bool] = None


class ProviderScheduleResponse(BaseModel):
    """Response schema for provider schedule"""

    id: UUID
    tenant_id: UUID
    practitioner_id: UUID
    location_id: UUID
    specialty_code: Optional[str] = None
    valid_from: date
    valid_to: Optional[date] = None
    day_of_week: int
    start_time: time
    end_time: time
    slot_duration_minutes: int
    max_patients_per_slot: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Time Slot Schemas ====================

class SlotMaterializeRequest(BaseModel):
    """Request to materialize slots for a schedule"""

    from_date: date = Field(..., description="Start date for slot generation")
    to_date: date = Field(..., description="End date for slot generation")

    @validator("to_date")
    def validate_to_date(cls, v, values):
        if "from_date" in values and v < values["from_date"]:
            raise ValueError("to_date must be on or after from_date")

        # Limit to 90 days at a time
        if "from_date" in values:
            delta = (v - values["from_date"]).days
            if delta > 90:
                raise ValueError("Cannot materialize more than 90 days at once")

        return v

    class Config:
        json_schema_extra = {
            "example": {
                "from_date": "2025-01-15",
                "to_date": "2025-02-15"
            }
        }


class TimeSlotResponse(BaseModel):
    """Response schema for time slot"""

    id: UUID
    tenant_id: UUID
    practitioner_id: UUID
    location_id: UUID
    schedule_id: UUID
    start_datetime: datetime
    end_datetime: datetime
    capacity: int
    booked_count: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TimeSlotListResponse(BaseModel):
    """Response for list of time slots"""

    total: int
    slots: List[TimeSlotResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== Appointment Schemas ====================

class AppointmentCreate(BaseModel):
    """Schema for creating appointment"""

    tenant_id: UUID
    patient_id: UUID
    practitioner_id: UUID
    location_id: UUID
    time_slot_id: UUID
    appointment_type: str = Field(..., description="new, followup, procedure")
    reason_text: Optional[str] = Field(None, max_length=1000)
    source_channel: str = Field(..., description="web, whatsapp, callcenter")
    metadata: Optional[dict] = None

    @validator("appointment_type")
    def validate_appointment_type(cls, v):
        valid_types = ["new", "followup", "procedure"]
        if v.lower() not in valid_types:
            raise ValueError(f"appointment_type must be one of: {', '.join(valid_types)}")
        return v.lower()

    @validator("source_channel")
    def validate_source_channel(cls, v):
        valid_channels = ["web", "whatsapp", "callcenter", "mobile", "phone"]
        if v.lower() not in valid_channels:
            raise ValueError(f"source_channel must be one of: {', '.join(valid_channels)}")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "patient_id": "patient-uuid",
                "practitioner_id": "practitioner-uuid",
                "location_id": "location-uuid",
                "time_slot_id": "slot-uuid",
                "appointment_type": "new",
                "reason_text": "Chest pain for 2 days",
                "source_channel": "web"
            }
        }


class AppointmentUpdate(BaseModel):
    """Schema for updating appointment"""

    time_slot_id: Optional[UUID] = None
    status: Optional[str] = None
    reason_text: Optional[str] = Field(None, max_length=1000)
    metadata: Optional[dict] = None

    @validator("status")
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = ["booked", "checked_in", "cancelled", "no_show", "completed"]
            if v.lower() not in valid_statuses:
                raise ValueError(f"status must be one of: {', '.join(valid_statuses)}")
            return v.lower()
        return v


class AppointmentResponse(BaseModel):
    """Response schema for appointment"""

    id: UUID
    tenant_id: UUID
    patient_id: UUID
    practitioner_id: UUID
    location_id: UUID
    time_slot_id: UUID
    appointment_type: str
    status: str
    reason_text: Optional[str] = None
    source_channel: str
    encounter_id: Optional[UUID] = None
    metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    # Nested data from relationships
    time_slot: Optional[TimeSlotResponse] = None

    class Config:
        from_attributes = True


class AppointmentListResponse(BaseModel):
    """Response for list of appointments"""

    total: int
    appointments: List[AppointmentResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


class AppointmentWithDetails(BaseModel):
    """Appointment with full details including patient and practitioner"""

    id: UUID
    tenant_id: UUID
    patient_id: UUID
    patient_name: Optional[str] = None
    practitioner_id: UUID
    practitioner_name: Optional[str] = None
    location_id: UUID
    location_name: Optional[str] = None
    appointment_type: str
    status: str
    reason_text: Optional[str] = None
    source_channel: str
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# ==================== Search & Filter Schemas ====================

class SlotSearchParams(BaseModel):
    """Parameters for searching available slots"""

    practitioner_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    specialty_code: Optional[str] = None
    from_datetime: Optional[datetime] = None
    to_datetime: Optional[datetime] = None
    status: str = Field(default="available", description="available, full, blocked")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class AppointmentSearchParams(BaseModel):
    """Parameters for searching appointments"""

    patient_id: Optional[UUID] = None
    practitioner_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    status: Optional[str] = None
    appointment_type: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


# ==================== Bulk Operations ====================

class SlotMaterializeResponse(BaseModel):
    """Response for slot materialization"""

    schedule_id: UUID
    slots_created: int
    from_date: date
    to_date: date
    message: str


class AppointmentCheckInRequest(BaseModel):
    """Request to check in an appointment"""

    checked_in_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "checked_in_at": "2025-01-15T09:00:00Z"
            }
        }


class AppointmentStatusUpdate(BaseModel):
    """Generic status update for appointments"""

    status: str
    notes: Optional[str] = None

    @validator("status")
    def validate_status(cls, v):
        valid_statuses = ["booked", "checked_in", "cancelled", "no_show", "completed"]
        if v.lower() not in valid_statuses:
            raise ValueError(f"status must be one of: {', '.join(valid_statuses)}")
        return v.lower()
