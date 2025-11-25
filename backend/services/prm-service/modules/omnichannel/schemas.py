"""
Omnichannel Communications Platform - Pydantic Schemas
Request/Response models for API validation
"""
from datetime import datetime, time, date
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field, validator, EmailStr
import re


# ==================== Enums ====================

class ChannelType(str, Enum):
    """Communication channels"""
    WHATSAPP = "whatsapp"
    SMS = "sms"
    EMAIL = "email"
    VOICE = "voice"
    IN_APP = "in_app"
    PUSH_NOTIFICATION = "push_notification"
    WEBCHAT = "webchat"


class MessageDirection(str, Enum):
    """Message direction"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class DeliveryStatus(str, Enum):
    """Message delivery status"""
    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    BOUNCED = "bounced"
    BLOCKED = "blocked"
    EXPIRED = "expired"


class ConversationStatus(str, Enum):
    """Conversation status"""
    NEW = "new"
    OPEN = "open"
    PENDING = "pending"
    RESOLVED = "resolved"
    CLOSED = "closed"
    SPAM = "spam"


class ConversationPriority(str, Enum):
    """Conversation priority"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TemplateStatus(str, Enum):
    """Template status"""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"


class TemplateCategory(str, Enum):
    """Template categories"""
    AUTHENTICATION = "authentication"
    MARKETING = "marketing"
    UTILITY = "utility"
    APPOINTMENT_UPDATE = "appointment_update"
    ALERT_UPDATE = "alert_update"
    PAYMENT_UPDATE = "payment_update"
    SHIPPING_UPDATE = "shipping_update"
    TICKET_UPDATE = "ticket_update"
    ACCOUNT_UPDATE = "account_update"


class ProviderType(str, Enum):
    """Provider types"""
    TWILIO_SMS = "twilio_sms"
    TWILIO_VOICE = "twilio_voice"
    TWILIO_WHATSAPP = "twilio_whatsapp"
    AWS_SNS = "aws_sns"
    AWS_SES = "aws_ses"
    AWS_CONNECT = "aws_connect"
    SENDGRID = "sendgrid"
    MESSAGEBIRD = "messagebird"
    VONAGE = "vonage"
    META_WHATSAPP = "meta_whatsapp"
    FIREBASE_PUSH = "firebase_push"


class CampaignStatus(str, Enum):
    """Campaign status"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class CampaignType(str, Enum):
    """Campaign type"""
    ONE_TIME = "one_time"
    RECURRING = "recurring"
    TRIGGERED = "triggered"
    DRIP = "drip"
    AB_TEST = "ab_test"


class ConsentType(str, Enum):
    """Consent types"""
    MARKETING = "marketing"
    TRANSACTIONAL = "transactional"
    APPOINTMENT_REMINDERS = "appointment_reminders"
    HEALTH_TIPS = "health_tips"
    SURVEYS = "surveys"
    EMERGENCY = "emergency"
    ALL_COMMUNICATIONS = "all_communications"


class ConsentStatus(str, Enum):
    """Consent status"""
    GRANTED = "granted"
    DENIED = "denied"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"
    PENDING = "pending"


# ==================== Base Schemas ====================

class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    class Config:
        from_attributes = True
        use_enum_values = True


class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    total: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== Provider Schemas ====================

class ProviderCredentials(BaseModel):
    """Provider credentials (varies by provider)"""
    account_sid: Optional[str] = None
    auth_token: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    access_token: Optional[str] = None
    webhook_verify_token: Optional[str] = None


class ProviderCreate(BaseModel):
    """Create a new provider"""
    tenant_id: UUID
    name: str = Field(..., min_length=1, max_length=100)
    provider_type: ProviderType
    channel: ChannelType
    is_primary: bool = False
    is_fallback: bool = False
    priority: int = 0
    credentials: Dict[str, Any]
    config: Optional[Dict[str, Any]] = {}
    rate_limit_per_second: int = 10
    rate_limit_per_day: Optional[int] = None
    from_phone_number: Optional[str] = None
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    reply_to_email: Optional[str] = None
    whatsapp_business_account_id: Optional[str] = None
    whatsapp_phone_number_id: Optional[str] = None


class ProviderUpdate(BaseModel):
    """Update provider"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_primary: Optional[bool] = None
    is_fallback: Optional[bool] = None
    priority: Optional[int] = None
    credentials: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None
    rate_limit_per_second: Optional[int] = None
    rate_limit_per_day: Optional[int] = None
    from_phone_number: Optional[str] = None
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    is_active: Optional[bool] = None


class ProviderResponse(BaseSchema):
    """Provider response"""
    id: UUID
    tenant_id: UUID
    name: str
    provider_type: ProviderType
    channel: ChannelType
    is_primary: bool
    is_fallback: bool
    priority: int
    config: Dict[str, Any]
    rate_limit_per_second: int
    rate_limit_per_day: Optional[int]
    from_phone_number: Optional[str]
    from_email: Optional[str]
    from_name: Optional[str]
    whatsapp_verified: bool
    is_active: bool
    health_status: str
    failure_count: int
    created_at: datetime
    updated_at: datetime


class ProviderListResponse(PaginatedResponse):
    """List of providers"""
    providers: List[ProviderResponse]


# ==================== Template Schemas ====================

class TemplateButton(BaseModel):
    """Template button configuration"""
    type: str  # reply, url, phone
    text: str
    url: Optional[str] = None
    phone_number: Optional[str] = None


class TemplateCreate(BaseModel):
    """Create a new template"""
    tenant_id: UUID
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=50, pattern=r'^[a-z0-9_]+$')
    description: Optional[str] = None
    channel: ChannelType
    category: Optional[TemplateCategory] = None
    subject: Optional[str] = Field(None, max_length=255)
    body: str = Field(..., min_length=1)
    body_html: Optional[str] = None
    header_text: Optional[str] = Field(None, max_length=255)
    footer_text: Optional[str] = Field(None, max_length=255)
    variables: Optional[List[str]] = []
    default_values: Optional[Dict[str, str]] = {}
    buttons: Optional[List[TemplateButton]] = []
    quick_replies: Optional[List[str]] = []
    media_type: Optional[str] = None
    media_url: Optional[str] = None
    language: str = "en"


class TemplateUpdate(BaseModel):
    """Update template"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    subject: Optional[str] = Field(None, max_length=255)
    body: Optional[str] = Field(None, min_length=1)
    body_html: Optional[str] = None
    header_text: Optional[str] = Field(None, max_length=255)
    footer_text: Optional[str] = Field(None, max_length=255)
    variables: Optional[List[str]] = None
    default_values: Optional[Dict[str, str]] = None
    buttons: Optional[List[TemplateButton]] = None
    quick_replies: Optional[List[str]] = None
    is_active: Optional[bool] = None


class TemplateResponse(BaseSchema):
    """Template response"""
    id: UUID
    tenant_id: UUID
    name: str
    code: str
    description: Optional[str]
    channel: ChannelType
    category: Optional[TemplateCategory]
    subject: Optional[str]
    body: str
    body_html: Optional[str]
    header_text: Optional[str]
    footer_text: Optional[str]
    variables: List[str]
    default_values: Dict[str, str]
    buttons: List[Dict[str, Any]]
    quick_replies: List[str]
    media_type: Optional[str]
    media_url: Optional[str]
    status: TemplateStatus
    version: int
    language: str
    usage_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TemplateListResponse(PaginatedResponse):
    """List of templates"""
    templates: List[TemplateResponse]


class TemplateRenderRequest(BaseModel):
    """Render a template with variables"""
    template_id: UUID
    variables: Dict[str, Any]
    language: Optional[str] = "en"


class TemplateRenderResponse(BaseModel):
    """Rendered template"""
    subject: Optional[str]
    body: str
    body_html: Optional[str]


# ==================== Message Schemas ====================

class SendMessageRequest(BaseModel):
    """Send a message request"""
    tenant_id: UUID
    patient_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    channel: Optional[ChannelType] = None  # None = auto-select
    recipient: str = Field(..., description="Phone number, email, or contact ID")
    message_type: str = "text"
    content: Optional[str] = None
    subject: Optional[str] = None  # For email
    template_id: Optional[UUID] = None
    template_variables: Optional[Dict[str, Any]] = {}
    attachments: Optional[List[Dict[str, Any]]] = []
    buttons: Optional[List[TemplateButton]] = []
    reply_to_message_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = {}
    scheduled_at: Optional[datetime] = None
    priority: ConversationPriority = ConversationPriority.NORMAL

    @validator('recipient')
    def validate_recipient(cls, v, values):
        # Basic validation - more specific validation in service
        if not v or len(v) < 3:
            raise ValueError("Recipient is required")
        return v.strip()


class BulkSendRequest(BaseModel):
    """Bulk send messages"""
    tenant_id: UUID
    recipients: List[str]
    channel: Optional[ChannelType] = None
    content: Optional[str] = None
    template_id: Optional[UUID] = None
    template_variables: Optional[Dict[str, Any]] = {}
    personalization: Optional[Dict[str, Dict[str, Any]]] = {}  # recipient -> variables
    campaign_id: Optional[UUID] = None
    scheduled_at: Optional[datetime] = None


class MessageResponse(BaseSchema):
    """Message response"""
    id: UUID
    tenant_id: UUID
    conversation_id: UUID
    patient_id: Optional[UUID]
    external_id: Optional[str]
    channel: ChannelType
    direction: MessageDirection
    sender_type: Optional[str]
    sender_name: Optional[str]
    sender_contact: Optional[str]
    recipient_contact: Optional[str]
    message_type: str
    content: Optional[str]
    subject: Optional[str]
    template_id: Optional[UUID]
    template_variables: Optional[Dict[str, Any]]
    attachments: List[Dict[str, Any]] = []
    buttons: Optional[List[Dict[str, Any]]]
    status: DeliveryStatus
    error_message: Optional[str]
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]
    intent: Optional[str]
    sentiment: Optional[str]
    created_at: datetime


class MessageListResponse(PaginatedResponse):
    """List of messages"""
    messages: List[MessageResponse]


class MessageStatusUpdate(BaseModel):
    """Update message status (from webhook)"""
    external_id: str
    status: DeliveryStatus
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: Optional[datetime] = None
    provider_response: Optional[Dict[str, Any]] = None


# ==================== Conversation Schemas ====================

class ConversationCreate(BaseModel):
    """Create a conversation"""
    tenant_id: UUID
    patient_id: Optional[UUID] = None
    external_contact_id: str
    external_contact_name: Optional[str] = None
    primary_channel: ChannelType
    topic: Optional[str] = None
    related_resource_type: Optional[str] = None
    related_resource_id: Optional[UUID] = None
    priority: ConversationPriority = ConversationPriority.NORMAL
    context: Optional[Dict[str, Any]] = {}


class ConversationUpdate(BaseModel):
    """Update conversation"""
    status: Optional[ConversationStatus] = None
    priority: Optional[ConversationPriority] = None
    assigned_agent_id: Optional[UUID] = None
    assigned_team_id: Optional[UUID] = None
    topic: Optional[str] = None
    sub_topic: Optional[str] = None
    tags: Optional[List[str]] = None
    context: Optional[Dict[str, Any]] = None


class ConversationResponse(BaseSchema):
    """Conversation response"""
    id: UUID
    tenant_id: UUID
    patient_id: Optional[UUID]
    external_contact_id: str
    external_contact_name: Optional[str]
    conversation_key: str
    primary_channel: ChannelType
    channels_used: List[str]
    status: ConversationStatus
    priority: ConversationPriority
    sentiment: Optional[str]
    assigned_agent_id: Optional[UUID]
    assigned_team_id: Optional[UUID]
    message_count: int
    unread_count: int
    topic: Optional[str]
    tags: List[str]
    first_message_at: Optional[datetime]
    last_message_at: Optional[datetime]
    first_response_at: Optional[datetime]
    first_response_sla_met: Optional[bool]
    created_at: datetime
    updated_at: datetime


class ConversationDetailResponse(ConversationResponse):
    """Detailed conversation with messages"""
    messages: List[MessageResponse]
    patient_info: Optional[Dict[str, Any]] = None
    context: Dict[str, Any] = {}


class ConversationListResponse(PaginatedResponse):
    """List of conversations"""
    conversations: List[ConversationResponse]


class ConversationAssign(BaseModel):
    """Assign conversation to agent"""
    agent_id: UUID
    notes: Optional[str] = None


class ConversationTransfer(BaseModel):
    """Transfer conversation"""
    to_agent_id: Optional[UUID] = None
    to_team_id: Optional[UUID] = None
    notes: Optional[str] = None


# ==================== Preference Schemas ====================

class PreferenceChannelConfig(BaseModel):
    """Channel preference configuration"""
    enabled: bool = True
    priority: int = 0


class PreferenceCreate(BaseModel):
    """Create communication preference"""
    tenant_id: UUID
    patient_id: UUID
    preferred_channel: Optional[ChannelType] = None
    fallback_channel: Optional[ChannelType] = None
    channel_preferences: Optional[Dict[str, PreferenceChannelConfig]] = {}
    phone_primary: Optional[str] = None
    phone_secondary: Optional[str] = None
    email_primary: Optional[str] = None
    email_secondary: Optional[str] = None
    whatsapp_number: Optional[str] = None
    preferred_language: str = "en"
    timezone: str = "UTC"
    preferred_time_start: Optional[str] = None  # HH:MM format
    preferred_time_end: Optional[str] = None
    do_not_disturb_start: Optional[str] = None
    do_not_disturb_end: Optional[str] = None
    allow_weekend_contact: bool = True
    max_messages_per_day: Optional[int] = None
    max_messages_per_week: Optional[int] = None
    appointment_reminders: bool = True
    appointment_reminder_hours: List[int] = [24, 2]
    health_tips: bool = False
    marketing_messages: bool = False
    survey_invitations: bool = True
    lab_results: bool = True
    prescription_reminders: bool = True
    billing_notifications: bool = True
    emergency_alerts: bool = True
    auto_channel_selection: bool = True


class PreferenceUpdate(BaseModel):
    """Update preference"""
    preferred_channel: Optional[ChannelType] = None
    fallback_channel: Optional[ChannelType] = None
    channel_preferences: Optional[Dict[str, PreferenceChannelConfig]] = None
    phone_primary: Optional[str] = None
    phone_secondary: Optional[str] = None
    email_primary: Optional[str] = None
    email_secondary: Optional[str] = None
    whatsapp_number: Optional[str] = None
    preferred_language: Optional[str] = None
    timezone: Optional[str] = None
    preferred_time_start: Optional[str] = None
    preferred_time_end: Optional[str] = None
    do_not_disturb_start: Optional[str] = None
    do_not_disturb_end: Optional[str] = None
    allow_weekend_contact: Optional[bool] = None
    max_messages_per_day: Optional[int] = None
    max_messages_per_week: Optional[int] = None
    appointment_reminders: Optional[bool] = None
    appointment_reminder_hours: Optional[List[int]] = None
    health_tips: Optional[bool] = None
    marketing_messages: Optional[bool] = None
    survey_invitations: Optional[bool] = None
    lab_results: Optional[bool] = None
    prescription_reminders: Optional[bool] = None
    billing_notifications: Optional[bool] = None
    emergency_alerts: Optional[bool] = None
    auto_channel_selection: Optional[bool] = None


class PreferenceResponse(BaseSchema):
    """Preference response"""
    id: UUID
    tenant_id: UUID
    patient_id: UUID
    preferred_channel: Optional[ChannelType]
    fallback_channel: Optional[ChannelType]
    channel_preferences: Dict[str, Any]
    phone_primary: Optional[str]
    phone_secondary: Optional[str]
    email_primary: Optional[str]
    email_secondary: Optional[str]
    whatsapp_number: Optional[str]
    preferred_language: str
    timezone: str
    allow_weekend_contact: bool
    appointment_reminders: bool
    health_tips: bool
    marketing_messages: bool
    lab_results: bool
    emergency_alerts: bool
    auto_channel_selection: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ==================== Consent Schemas ====================

class ConsentCreate(BaseModel):
    """Create consent record"""
    tenant_id: UUID
    patient_id: UUID
    consent_type: ConsentType
    channel: Optional[ChannelType] = None
    status: ConsentStatus = ConsentStatus.GRANTED
    capture_method: Optional[str] = None
    capture_source: Optional[str] = None
    consent_text: Optional[str] = None
    consent_version: Optional[str] = None
    legal_basis: Optional[str] = None
    purposes: Optional[List[str]] = []
    valid_until: Optional[datetime] = None


class ConsentResponse(BaseSchema):
    """Consent response"""
    id: UUID
    tenant_id: UUID
    patient_id: UUID
    consent_type: ConsentType
    channel: Optional[ChannelType]
    status: ConsentStatus
    capture_method: Optional[str]
    capture_source: Optional[str]
    consent_version: Optional[str]
    legal_basis: Optional[str]
    valid_from: datetime
    valid_until: Optional[datetime]
    withdrawn_at: Optional[datetime]
    created_at: datetime


class ConsentListResponse(PaginatedResponse):
    """List of consents"""
    consents: List[ConsentResponse]


class OptOutRequest(BaseModel):
    """Opt-out request"""
    tenant_id: UUID
    contact_type: str  # phone, email, whatsapp
    contact_value: str
    channel: Optional[ChannelType] = None
    opt_out_type: str = "all"  # all, marketing, transactional
    reason: Optional[str] = None
    method: str = "api"
    source_message_id: Optional[UUID] = None


class OptOutResponse(BaseSchema):
    """Opt-out response"""
    id: UUID
    tenant_id: UUID
    patient_id: Optional[UUID]
    contact_type: str
    contact_value: str
    channel: Optional[ChannelType]
    opt_out_type: str
    is_active: bool
    opted_out_at: datetime


# ==================== Campaign Schemas ====================

class CampaignCreate(BaseModel):
    """Create campaign"""
    tenant_id: UUID
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    campaign_type: CampaignType
    channels: List[ChannelType]
    primary_channel: Optional[ChannelType] = None
    template_id: Optional[UUID] = None
    subject: Optional[str] = None
    content: Optional[str] = None
    content_html: Optional[str] = None
    segment_id: Optional[UUID] = None
    segment_query: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None
    timezone: str = "UTC"
    send_window_start: Optional[str] = None  # HH:MM
    send_window_end: Optional[str] = None
    respect_dnd: bool = True
    recurrence_rule: Optional[str] = None
    recurrence_end_date: Optional[datetime] = None
    trigger_event: Optional[str] = None
    trigger_conditions: Optional[Dict[str, Any]] = None
    trigger_delay_minutes: int = 0
    is_ab_test: bool = False
    ab_test_percentage: int = 20
    ab_winner_criteria: Optional[str] = None
    ab_test_duration_hours: int = 24
    budget_limit: Optional[float] = None
    tags: Optional[List[str]] = []


class CampaignUpdate(BaseModel):
    """Update campaign"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    template_id: Optional[UUID] = None
    subject: Optional[str] = None
    content: Optional[str] = None
    content_html: Optional[str] = None
    segment_id: Optional[UUID] = None
    segment_query: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None
    send_window_start: Optional[str] = None
    send_window_end: Optional[str] = None
    respect_dnd: Optional[bool] = None
    budget_limit: Optional[float] = None
    tags: Optional[List[str]] = None


class CampaignResponse(BaseSchema):
    """Campaign response"""
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    campaign_type: CampaignType
    channels: List[str]
    primary_channel: Optional[ChannelType]
    template_id: Optional[UUID]
    subject: Optional[str]
    status: CampaignStatus
    scheduled_at: Optional[datetime]
    is_ab_test: bool
    total_recipients: int
    messages_sent: int
    messages_delivered: int
    messages_failed: int
    messages_opened: int
    messages_clicked: int
    opt_outs: int
    budget_limit: Optional[float]
    budget_spent: Optional[float]
    tags: List[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class CampaignListResponse(PaginatedResponse):
    """List of campaigns"""
    campaigns: List[CampaignResponse]


class CampaignAction(BaseModel):
    """Campaign action (start, pause, cancel)"""
    action: str  # start, pause, resume, cancel


# ==================== Segment Schemas ====================

class SegmentCondition(BaseModel):
    """Segment condition"""
    field: str
    operator: str  # equals, not_equals, greater_than, less_than, contains, in
    value: Any


class SegmentCreate(BaseModel):
    """Create segment"""
    tenant_id: UUID
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    conditions: List[SegmentCondition]
    condition_logic: str = "AND"
    is_static: bool = False
    static_members: Optional[List[UUID]] = None
    auto_refresh: bool = True
    refresh_interval_hours: int = 24


class SegmentUpdate(BaseModel):
    """Update segment"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    conditions: Optional[List[SegmentCondition]] = None
    condition_logic: Optional[str] = None
    is_static: Optional[bool] = None
    static_members: Optional[List[UUID]] = None
    auto_refresh: Optional[bool] = None
    refresh_interval_hours: Optional[int] = None


class SegmentResponse(BaseSchema):
    """Segment response"""
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    conditions: List[Dict[str, Any]]
    condition_logic: str
    is_static: bool
    estimated_size: Optional[int]
    last_calculated_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SegmentListResponse(PaginatedResponse):
    """List of segments"""
    segments: List[SegmentResponse]


class SegmentEstimateResponse(BaseModel):
    """Segment size estimate"""
    estimated_size: int
    sample_members: List[Dict[str, Any]] = []


# ==================== Unified Inbox Schemas ====================

class InboxFilter(BaseModel):
    """Inbox filter options"""
    status: Optional[List[ConversationStatus]] = None
    priority: Optional[List[ConversationPriority]] = None
    channels: Optional[List[ChannelType]] = None
    assigned_agent_id: Optional[UUID] = None
    unassigned_only: bool = False
    tags: Optional[List[str]] = None
    search: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class InboxConversation(ConversationResponse):
    """Inbox conversation with extra info"""
    patient_name: Optional[str] = None
    patient_mrn: Optional[str] = None
    last_message_preview: Optional[str] = None
    agent_name: Optional[str] = None


class InboxListResponse(PaginatedResponse):
    """Inbox list"""
    conversations: List[InboxConversation]
    unread_total: int = 0
    counts_by_status: Dict[str, int] = {}


class CannedResponseCreate(BaseModel):
    """Create canned response"""
    tenant_id: UUID
    name: str = Field(..., min_length=1, max_length=100)
    shortcut: Optional[str] = Field(None, max_length=50)
    content: str = Field(..., min_length=1)
    category: Optional[str] = None
    tags: Optional[List[str]] = []
    is_global: bool = True
    variables: Optional[List[str]] = []


class CannedResponseResponse(BaseSchema):
    """Canned response"""
    id: UUID
    tenant_id: UUID
    name: str
    shortcut: Optional[str]
    content: str
    category: Optional[str]
    tags: List[str]
    is_global: bool
    variables: List[str]
    usage_count: int
    is_active: bool
    created_at: datetime


class CannedResponseListResponse(PaginatedResponse):
    """List of canned responses"""
    responses: List[CannedResponseResponse]


# ==================== Analytics Schemas ====================

class ChannelMetrics(BaseModel):
    """Channel metrics"""
    channel: ChannelType
    messages_sent: int = 0
    messages_delivered: int = 0
    messages_failed: int = 0
    messages_received: int = 0
    delivery_rate: Optional[float] = None
    open_rate: Optional[float] = None
    click_rate: Optional[float] = None
    avg_response_time_seconds: Optional[float] = None
    total_cost: float = 0


class AnalyticsSummary(BaseModel):
    """Analytics summary"""
    period_start: datetime
    period_end: datetime
    total_messages_sent: int = 0
    total_messages_delivered: int = 0
    total_conversations: int = 0
    total_conversations_resolved: int = 0
    overall_delivery_rate: Optional[float] = None
    overall_response_rate: Optional[float] = None
    avg_first_response_seconds: Optional[float] = None
    avg_resolution_seconds: Optional[float] = None
    sla_compliance_rate: Optional[float] = None
    total_cost: float = 0
    channel_breakdown: List[ChannelMetrics] = []


class CampaignMetrics(BaseModel):
    """Campaign metrics"""
    campaign_id: UUID
    campaign_name: str
    total_recipients: int = 0
    sent: int = 0
    delivered: int = 0
    opened: int = 0
    clicked: int = 0
    converted: int = 0
    delivery_rate: Optional[float] = None
    open_rate: Optional[float] = None
    click_rate: Optional[float] = None
    conversion_rate: Optional[float] = None
    total_cost: float = 0


class EngagementScoreResponse(BaseModel):
    """Patient engagement score"""
    patient_id: UUID
    overall_score: float
    score_tier: str
    response_score: Optional[float]
    open_score: Optional[float]
    recency_score: Optional[float]
    preferred_channel: Optional[str]
    last_interaction_at: Optional[datetime]
    calculated_at: datetime


# ==================== Webhook Schemas ====================

class WhatsAppWebhookPayload(BaseModel):
    """WhatsApp webhook payload"""
    object: str
    entry: List[Dict[str, Any]]


class TwilioWebhookPayload(BaseModel):
    """Twilio webhook payload"""
    MessageSid: Optional[str] = None
    SmsSid: Optional[str] = None
    AccountSid: Optional[str] = None
    From: Optional[str] = None
    To: Optional[str] = None
    Body: Optional[str] = None
    MessageStatus: Optional[str] = None
    ErrorCode: Optional[str] = None
    ErrorMessage: Optional[str] = None


class SendGridWebhookPayload(BaseModel):
    """SendGrid webhook event"""
    email: str
    event: str
    sg_message_id: Optional[str] = None
    timestamp: int
    reason: Optional[str] = None
    url: Optional[str] = None


# ==================== SLA Schemas ====================

class SLAConfigCreate(BaseModel):
    """Create SLA configuration"""
    tenant_id: UUID
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    first_response_time_low: int = 60
    first_response_time_normal: int = 30
    first_response_time_high: int = 15
    first_response_time_urgent: int = 5
    resolution_time_low: int = 1440
    resolution_time_normal: int = 480
    resolution_time_high: int = 240
    resolution_time_urgent: int = 60
    business_hours_only: bool = True
    business_hours_start: str = "09:00"
    business_hours_end: str = "17:00"
    business_days: List[int] = [1, 2, 3, 4, 5]
    escalation_enabled: bool = True
    escalation_threshold_percentage: int = 80
    escalation_notify_emails: Optional[List[str]] = []
    is_default: bool = False


class SLAConfigResponse(BaseSchema):
    """SLA configuration response"""
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    first_response_time_low: int
    first_response_time_normal: int
    first_response_time_high: int
    first_response_time_urgent: int
    resolution_time_low: int
    resolution_time_normal: int
    resolution_time_high: int
    resolution_time_urgent: int
    business_hours_only: bool
    escalation_enabled: bool
    escalation_threshold_percentage: int
    is_default: bool
    is_active: bool
    created_at: datetime


class SLATrackingResponse(BaseModel):
    """SLA tracking status"""
    conversation_id: UUID
    first_response_due_at: Optional[datetime]
    first_response_at: Optional[datetime]
    first_response_breached: bool
    first_response_time_seconds: Optional[int]
    resolution_due_at: Optional[datetime]
    resolved_at: Optional[datetime]
    resolution_breached: bool
    resolution_time_seconds: Optional[int]
    escalated: bool
    escalation_level: int
