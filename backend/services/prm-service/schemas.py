"""
PRM Service Pydantic Schemas
Request/Response models for journey orchestration, communications, and tickets
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator
from enum import Enum


# ==================== Enums ====================

class JourneyType(str, Enum):
    """Journey type enumeration"""
    OPD = "opd"
    IPD = "ipd"
    PROCEDURE = "procedure"
    CHRONIC_CARE = "chronic_care"
    WELLNESS = "wellness"


class JourneyStatus(str, Enum):
    """Journey status enumeration"""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class StageStatus(str, Enum):
    """Stage status enumeration"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


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


class TicketPriority(str, Enum):
    """Ticket priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketStatus(str, Enum):
    """Ticket status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


# ==================== Journey Schemas ====================

class JourneyStageCreate(BaseModel):
    """Schema for creating a journey stage"""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    order_index: int = Field(..., ge=0)
    trigger_event: Optional[str] = Field(
        None,
        description="Event that triggers advancement to this stage"
    )
    actions: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Actions to perform when stage is entered (e.g., send communication)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Pre-visit Prep",
                "description": "Send pre-visit instructions and forms",
                "order_index": 0,
                "trigger_event": "Appointment.Created",
                "actions": {
                    "send_communication": {
                        "channel": "whatsapp",
                        "template": "pre_visit_instructions"
                    }
                }
            }
        }


class JourneyStageUpdate(BaseModel):
    """Schema for updating a journey stage"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    order_index: Optional[int] = Field(None, ge=0)
    trigger_event: Optional[str] = None
    actions: Optional[Dict[str, Any]] = None


class JourneyStageResponse(BaseModel):
    """Response schema for journey stage"""

    id: UUID
    journey_id: UUID
    name: str
    description: Optional[str] = None
    code: str
    order_index: int
    trigger_event: Optional[str] = None
    actions: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JourneyCreate(BaseModel):
    """Schema for creating a journey definition"""

    tenant_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    journey_type: JourneyType
    is_default: bool = Field(
        default=False,
        description="Auto-apply this journey when trigger conditions are met"
    )
    trigger_conditions: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Conditions for auto-journey creation"
    )
    stages: Optional[List[JourneyStageCreate]] = Field(
        default_factory=list,
        description="Journey stages (can be added after journey creation)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "name": "OPD Visit Journey",
                "description": "Standard outpatient visit journey",
                "journey_type": "opd",
                "is_default": True,
                "trigger_conditions": {
                    "appointment_type": "new"
                },
                "stages": [
                    {
                        "name": "Pre-visit",
                        "order_index": 0,
                        "trigger_event": "Appointment.Created"
                    },
                    {
                        "name": "Day of Visit",
                        "order_index": 1,
                        "trigger_event": "Appointment.CheckedIn"
                    },
                    {
                        "name": "Post-visit",
                        "order_index": 2,
                        "trigger_event": "Encounter.Completed"
                    }
                ]
            }
        }


class JourneyUpdate(BaseModel):
    """Schema for updating a journey definition"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_default: Optional[bool] = None
    trigger_conditions: Optional[Dict[str, Any]] = None


class JourneyResponse(BaseModel):
    """Response schema for journey definition"""

    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str] = None
    code: str
    journey_type: Optional[str] = "wellness"
    is_default: bool = False
    trigger_conditions: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    stages: List[JourneyStageResponse] = []

    class Config:
        from_attributes = True


class JourneyListResponse(BaseModel):
    """Response for list of journeys"""

    total: int
    journeys: List[JourneyResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== Journey Instance Schemas ====================

class JourneyInstanceCreate(BaseModel):
    """Schema for creating a journey instance"""

    tenant_id: UUID
    journey_id: UUID
    patient_id: UUID
    appointment_id: Optional[UUID] = Field(
        None,
        description="Link to appointment that triggered this journey"
    )
    encounter_id: Optional[UUID] = Field(
        None,
        description="Link to encounter"
    )
    context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional context data (e.g., patient preferences, special instructions)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "journey_id": "journey-uuid",
                "patient_id": "patient-uuid",
                "appointment_id": "appointment-uuid",
                "context": {
                    "preferred_communication": "whatsapp",
                    "language": "en",
                    "special_needs": "wheelchair_access"
                }
            }
        }


class JourneyInstanceUpdate(BaseModel):
    """Schema for updating a journey instance"""

    status: Optional[JourneyStatus] = None
    current_stage_id: Optional[UUID] = None
    context: Optional[Dict[str, Any]] = None
    completed_at: Optional[datetime] = None


class JourneyInstanceStageUpdate(BaseModel):
    """Schema for updating stage status in journey instance"""

    status: StageStatus
    entered_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=2000)


class JourneyInstanceResponse(BaseModel):
    """Response schema for journey instance"""

    id: UUID
    tenant_id: UUID
    journey_id: UUID
    patient_id: UUID
    status: str
    current_stage_id: Optional[UUID] = None
    meta_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JourneyInstanceWithStages(BaseModel):
    """Journey instance with stage statuses"""

    id: UUID
    tenant_id: UUID
    journey_id: UUID
    journey_name: str
    patient_id: UUID
    status: str
    current_stage_id: Optional[UUID] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    stages: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of stages with their current status"
    )

    class Config:
        from_attributes = True


class JourneyInstanceListResponse(BaseModel):
    """Response for list of journey instances"""

    total: int
    instances: List[JourneyInstanceResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


class AdvanceStageRequest(BaseModel):
    """Request to advance journey to next stage"""

    force: bool = Field(
        default=False,
        description="Force advancement even if current stage is not completed"
    )
    notes: Optional[str] = Field(None, max_length=2000)


# ==================== Communication Schemas ====================

class CommunicationCreate(BaseModel):
    """Schema for creating a communication"""

    tenant_id: UUID
    patient_id: UUID
    journey_instance_id: Optional[UUID] = Field(
        None,
        description="Link to journey instance if part of journey automation"
    )
    channel: CommunicationType
    recipient: str = Field(
        ...,
        description="Phone number, email, or WhatsApp number"
    )
    subject: Optional[str] = Field(None, max_length=255)
    message: str = Field(..., min_length=1, max_length=5000)
    template_name: Optional[str] = Field(
        None,
        description="Template used for this communication"
    )
    template_vars: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Variables used in template"
    )
    scheduled_for: Optional[datetime] = Field(
        None,
        description="Schedule for future delivery"
    )

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

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "patient_id": "patient-uuid",
                "journey_instance_id": "journey-instance-uuid",
                "channel": "whatsapp",
                "recipient": "+1234567890",
                "subject": "Appointment Reminder",
                "message": "Your appointment is tomorrow at 10 AM",
                "template_name": "appointment_reminder",
                "template_vars": {
                    "patient_name": "John Doe",
                    "appointment_time": "10:00 AM",
                    "doctor_name": "Dr. Smith"
                }
            }
        }


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
    patient_id: Optional[UUID] = None
    journey_instance_id: Optional[UUID] = None
    channel: str
    direction: str
    template_code: Optional[str] = None
    content: Optional[str] = None
    content_structured: Optional[Dict[str, Any]] = None
    status: str
    created_by_user_id: Optional[UUID] = None
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

    force_send: bool = Field(
        default=False,
        description="Send immediately even if scheduled for later"
    )


# ==================== Ticket Schemas ====================

class TicketCreate(BaseModel):
    """Schema for creating a support ticket"""

    tenant_id: UUID
    patient_id: UUID
    journey_instance_id: Optional[UUID] = Field(
        None,
        description="Link to journey instance if ticket is journey-related"
    )
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1, max_length=5000)
    priority: TicketPriority = Field(default=TicketPriority.MEDIUM)
    category: Optional[str] = Field(
        None,
        max_length=100,
        description="Ticket category (e.g., billing, clinical, administrative)"
    )
    assigned_to: Optional[UUID] = Field(
        None,
        description="Staff member UUID"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "patient_id": "patient-uuid",
                "journey_instance_id": "journey-instance-uuid",
                "title": "Need wheelchair assistance",
                "description": "Patient requires wheelchair for appointment tomorrow",
                "priority": "high",
                "category": "administrative"
            }
        }


class TicketUpdate(BaseModel):
    """Schema for updating a ticket"""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    assigned_to: Optional[UUID] = None
    resolution_notes: Optional[str] = Field(None, max_length=2000)


class TicketCommentCreate(BaseModel):
    """Schema for adding a comment to a ticket"""

    author_id: UUID = Field(..., description="User ID of comment author")
    comment: str = Field(..., min_length=1, max_length=2000)
    is_internal: bool = Field(
        default=False,
        description="Internal comment not visible to patient"
    )


class TicketCommentResponse(BaseModel):
    """Response schema for ticket comment"""

    id: UUID
    ticket_id: UUID
    author_id: UUID
    comment: str
    is_internal: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TicketResponse(BaseModel):
    """Response schema for ticket"""

    id: UUID
    tenant_id: UUID
    patient_id: Optional[UUID] = None
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    created_by_user_id: Optional[UUID] = None
    assigned_to_user_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TicketWithComments(BaseModel):
    """Ticket with comments"""

    id: UUID
    tenant_id: UUID
    patient_id: UUID
    journey_instance_id: Optional[UUID] = None
    title: str
    description: str
    status: str
    priority: str
    category: Optional[str] = None
    assigned_to: Optional[UUID] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    comments: List[TicketCommentResponse] = []

    class Config:
        from_attributes = True


class TicketListResponse(BaseModel):
    """Response for list of tickets"""

    total: int
    tickets: List[TicketResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== Template Schemas ====================

class CommunicationTemplate(BaseModel):
    """Communication template for rendering messages"""

    name: str
    channel: CommunicationType
    subject_template: Optional[str] = None
    message_template: str
    variables: List[str] = Field(
        default_factory=list,
        description="List of variable names used in template"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "appointment_reminder",
                "channel": "whatsapp",
                "subject_template": None,
                "message_template": "Hi {{patient_name}}, this is a reminder for your appointment with {{doctor_name}} on {{appointment_date}} at {{appointment_time}}.",
                "variables": ["patient_name", "doctor_name", "appointment_date", "appointment_time"]
            }
        }


class TemplateRenderRequest(BaseModel):
    """Request to render a template with variables"""

    template_name: str
    variables: Dict[str, Any]

    class Config:
        json_schema_extra = {
            "example": {
                "template_name": "appointment_reminder",
                "variables": {
                    "patient_name": "John Doe",
                    "doctor_name": "Dr. Smith",
                    "appointment_date": "2025-01-16",
                    "appointment_time": "10:00 AM"
                }
            }
        }


class TemplateRenderResponse(BaseModel):
    """Rendered template response"""

    subject: Optional[str] = None
    message: str
