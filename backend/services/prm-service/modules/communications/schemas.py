"""
Communications Schemas
Request/Response models for multi-channel communications
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator
from enum import Enum


class CommunicationType(str, Enum):
    """Communication channel type"""
    WHATSAPP = "whatsapp"
    SMS = "sms"
    EMAIL = "email"
    VOICE = "voice"
    IN_APP = "in_app"


class CommunicationStatus(str, Enum):
    """Communication delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class CommunicationCreate(BaseModel):
    """Schema for creating a communication"""

    tenant_id: UUID
    patient_id: UUID
    journey_instance_id: Optional[UUID] = None
    channel: CommunicationType
    recipient: str = Field(..., description="Phone number, email, or WhatsApp number")
    subject: Optional[str] = Field(None, max_length=255)
    message: str = Field(..., min_length=1, max_length=5000)
    template_name: Optional[str] = None
    template_vars: Optional[Dict[str, Any]] = Field(default_factory=dict)
    scheduled_for: Optional[datetime] = None

    @validator("recipient")
    def validate_recipient(cls, v, values):
        channel = values.get("channel")
        if channel == CommunicationType.EMAIL:
            if "@" not in v:
                raise ValueError("Invalid email format")
        elif channel in [CommunicationType.SMS, CommunicationType.WHATSAPP]:
            # Basic phone validation
            cleaned = v.replace("+", "").replace("-", "").replace(" ", "")
            if not cleaned.isdigit() or len(cleaned) < 10:
                raise ValueError("Invalid phone number format")
        return v


class CommunicationUpdate(BaseModel):
    """Schema for updating a communication"""

    status: Optional[CommunicationStatus] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    error_message: Optional[str] = Field(None, max_length=500)


class CommunicationResponse(BaseModel):
    """Response schema for communication"""

    id: UUID
    tenant_id: UUID
    patient_id: UUID
    journey_instance_id: Optional[UUID] = None
    channel: str
    recipient: str
    subject: Optional[str] = None
    message: str
    template_name: Optional[str] = None
    status: str
    scheduled_for: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CommunicationListResponse(BaseModel):
    """Response for list of communications"""

    total: int
    communications: List[CommunicationResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


class SendCommunicationRequest(BaseModel):
    """Request to send a communication immediately"""

    force_send: bool = Field(default=False)
