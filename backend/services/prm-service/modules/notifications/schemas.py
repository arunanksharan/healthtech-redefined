"""
Notification Schemas
Message templates and multi-channel notifications
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, validator
from enum import Enum


# ==================== Enums ====================

class NotificationChannel(str, Enum):
    """Notification delivery channel"""
    WHATSAPP = "whatsapp"
    SMS = "sms"
    EMAIL = "email"
    VOICE = "voice"
    PUSH = "push"


class NotificationStatus(str, Enum):
    """Notification delivery status"""
    QUEUED = "queued"        # Waiting to be sent
    SENDING = "sending"      # Currently being sent
    SENT = "sent"            # Successfully sent
    DELIVERED = "delivered"  # Confirmed delivery
    FAILED = "failed"        # Failed to send
    BOUNCED = "bounced"      # Email bounced
    UNSUBSCRIBED = "unsubscribed"  # Recipient unsubscribed


class NotificationPriority(str, Enum):
    """Notification priority for queue processing"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TemplateCategory(str, Enum):
    """Template categories for organization"""
    APPOINTMENT = "appointment"
    REMINDER = "reminder"
    CONFIRMATION = "confirmation"
    CANCELLATION = "cancellation"
    ALERT = "alert"
    MARKETING = "marketing"
    TRANSACTIONAL = "transactional"
    SYSTEM = "system"


# ==================== Template Schemas ====================

class MessageTemplateCreate(BaseModel):
    """Create message template"""
    name: str = Field(..., min_length=1, max_length=100, description="Unique template name")
    channel: NotificationChannel
    category: TemplateCategory = TemplateCategory.TRANSACTIONAL

    # Content
    subject: Optional[str] = Field(None, max_length=200, description="Email subject or SMS preview")
    body: str = Field(..., min_length=1, description="Template body with {variables}")

    # Metadata
    description: Optional[str] = Field(None, max_length=500)
    variables: List[str] = Field(
        default_factory=list,
        description="List of variables used in template (e.g., ['patient_name', 'appointment_date'])"
    )
    is_active: bool = True

    @validator('body')
    def validate_template_syntax(cls, v):
        """Basic validation of template syntax"""
        # Check for balanced braces
        if v.count('{') != v.count('}'):
            raise ValueError('Template has unbalanced braces')

        return v

    @validator('name')
    def validate_name_format(cls, v):
        """Validate template name format"""
        # Only allow alphanumeric, underscore, hyphen
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Template name can only contain letters, numbers, underscore, and hyphen')

        return v


class MessageTemplateUpdate(BaseModel):
    """Update message template"""
    subject: Optional[str] = Field(None, max_length=200)
    body: Optional[str] = None
    description: Optional[str] = Field(None, max_length=500)
    variables: Optional[List[str]] = None
    is_active: Optional[bool] = None
    category: Optional[TemplateCategory] = None


class MessageTemplateResponse(BaseModel):
    """Message template response"""
    id: UUID
    org_id: Optional[UUID] = None

    name: str
    channel: NotificationChannel
    category: TemplateCategory

    subject: Optional[str]
    body: str
    description: Optional[str]
    variables: List[str]
    is_active: bool

    # Usage statistics
    total_sent: int = 0
    last_used_at: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Notification Schemas ====================

class NotificationSend(BaseModel):
    """Send notification directly (without template)"""
    channel: NotificationChannel
    to: str = Field(..., description="Recipient (phone number or email)")
    subject: Optional[str] = Field(None, max_length=200, description="For email")
    body: str = Field(..., min_length=1, description="Message body")

    # Optional
    priority: NotificationPriority = NotificationPriority.NORMAL
    scheduled_for: Optional[datetime] = Field(None, description="Schedule for future delivery")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context")

    @validator('to')
    def validate_recipient(cls, v, values):
        """Validate recipient format based on channel"""
        channel = values.get('channel')

        if channel in [NotificationChannel.WHATSAPP, NotificationChannel.SMS, NotificationChannel.VOICE]:
            # Phone number validation
            import re
            cleaned = re.sub(r'[^\d+]', '', v)
            if len(cleaned) < 10:
                raise ValueError('Phone number too short')

            # Add + if not present
            if not cleaned.startswith('+'):
                if cleaned.startswith('1') and len(cleaned) == 11:
                    cleaned = '+' + cleaned
                elif len(cleaned) == 10:
                    cleaned = '+1' + cleaned
                else:
                    cleaned = '+' + cleaned

            return cleaned

        elif channel == NotificationChannel.EMAIL:
            # Email validation (basic)
            if '@' not in v or '.' not in v:
                raise ValueError('Invalid email format')

        return v


class NotificationSendWithTemplate(BaseModel):
    """Send notification using template"""
    template_name: str = Field(..., description="Template name to use")
    channel: NotificationChannel
    to: str = Field(..., description="Recipient")
    variables: Dict[str, Any] = Field(
        default_factory=dict,
        description="Variables to substitute in template"
    )

    # Optional
    priority: NotificationPriority = NotificationPriority.NORMAL
    scheduled_for: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NotificationSchedule(BaseModel):
    """Schedule recurring notification"""
    template_name: str
    channel: NotificationChannel
    recipients: List[str] = Field(..., min_items=1)
    variables: Dict[str, Any] = Field(default_factory=dict)

    # Scheduling
    send_at: datetime = Field(..., description="When to send")
    recurrence: Optional[str] = Field(
        None,
        description="Recurrence pattern (daily, weekly, monthly)"
    )


class NotificationResponse(BaseModel):
    """Notification response"""
    id: UUID
    org_id: Optional[UUID] = None

    # Channel and recipient
    channel: NotificationChannel
    to: str

    # Content
    subject: Optional[str]
    body: str

    # Status
    status: NotificationStatus
    priority: NotificationPriority

    # Scheduling
    scheduled_for: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

    # Template reference
    template_id: Optional[UUID] = None
    template_name: Optional[str] = None

    # Error tracking
    error_message: Optional[str] = None
    retry_count: int = 0

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    created_at: datetime
    updated_at: datetime

    @property
    def is_sent(self) -> bool:
        """Check if notification was sent"""
        return self.status in [
            NotificationStatus.SENT,
            NotificationStatus.DELIVERED
        ]

    @property
    def is_failed(self) -> bool:
        """Check if notification failed"""
        return self.status in [
            NotificationStatus.FAILED,
            NotificationStatus.BOUNCED
        ]

    class Config:
        from_attributes = True


# ==================== List/Filter Schemas ====================

class TemplateListFilters(BaseModel):
    """Filters for listing templates"""
    channel: Optional[NotificationChannel] = None
    category: Optional[TemplateCategory] = None
    is_active: Optional[bool] = None
    search_query: Optional[str] = None  # Search in name, description
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)


class NotificationListFilters(BaseModel):
    """Filters for listing notifications"""
    channel: Optional[NotificationChannel] = None
    status: Optional[NotificationStatus] = None
    to: Optional[str] = None  # Filter by recipient
    template_id: Optional[UUID] = None
    sent_after: Optional[datetime] = None
    sent_before: Optional[datetime] = None
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)


# ==================== Bulk Operations ====================

class BulkNotificationSend(BaseModel):
    """Send notifications to multiple recipients"""
    template_name: str
    channel: NotificationChannel
    recipients: List[str] = Field(..., min_items=1, max_items=1000)
    variables: Dict[str, Any] = Field(
        default_factory=dict,
        description="Variables applied to all recipients"
    )
    per_recipient_variables: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="Variables specific to each recipient (keyed by recipient)"
    )


class BulkNotificationResult(BaseModel):
    """Result of bulk notification send"""
    total_recipients: int
    successful: int
    failed: int
    queued_notification_ids: List[UUID]
    errors: List[str] = Field(default_factory=list)


# ==================== Statistics ====================

class NotificationStatistics(BaseModel):
    """Notification delivery statistics"""
    total_sent: int
    total_delivered: int
    total_failed: int

    # By channel
    by_channel: Dict[str, int]

    # By status
    by_status: Dict[str, int]

    # Success rate
    delivery_rate: float = Field(..., ge=0.0, le=1.0, description="Successful delivery rate")

    # Templates
    most_used_templates: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Top 10 most used templates"
    )

    # Time period
    period_start: datetime
    period_end: datetime


# ==================== Template Rendering ====================

class TemplateRenderRequest(BaseModel):
    """Request to preview template rendering"""
    template_name: str
    variables: Dict[str, Any] = Field(default_factory=dict)


class TemplateRenderResponse(BaseModel):
    """Rendered template preview"""
    subject: Optional[str]
    body: str
    variables_used: List[str]
    missing_variables: List[str] = Field(
        default_factory=list,
        description="Variables in template but not provided"
    )
