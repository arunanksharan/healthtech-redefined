"""
Omnichannel Communications Platform - SQLAlchemy Models
EPIC-013: Unified patient communication across all channels
"""
from datetime import datetime, time
from typing import Optional, List
from uuid import uuid4
import enum

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Float, DateTime, Date, Time,
    ForeignKey, Enum, BigInteger, Numeric, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from shared.database.connection import Base


def generate_uuid():
    return uuid4()


# ==================== Enums ====================

class OmniChannelType(str, enum.Enum):
    """Communication channel types"""
    WHATSAPP = "whatsapp"
    SMS = "sms"
    EMAIL = "email"
    VOICE = "voice"
    IN_APP = "in_app"
    PUSH_NOTIFICATION = "push_notification"
    WEBCHAT = "webchat"


class MessageDirection(str, enum.Enum):
    """Message direction"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class DeliveryStatus(str, enum.Enum):
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


class ConversationStatus(str, enum.Enum):
    """Conversation status"""
    NEW = "new"
    OPEN = "open"
    PENDING = "pending"
    RESOLVED = "resolved"
    CLOSED = "closed"
    SPAM = "spam"


class ConversationPriority(str, enum.Enum):
    """Conversation priority"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TemplateStatus(str, enum.Enum):
    """Template approval status"""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"


class TemplateCategory(str, enum.Enum):
    """Template categories (WhatsApp)"""
    AUTHENTICATION = "authentication"
    MARKETING = "marketing"
    UTILITY = "utility"
    APPOINTMENT_UPDATE = "appointment_update"
    ALERT_UPDATE = "alert_update"
    PAYMENT_UPDATE = "payment_update"
    SHIPPING_UPDATE = "shipping_update"
    TICKET_UPDATE = "ticket_update"
    ACCOUNT_UPDATE = "account_update"


class ProviderType(str, enum.Enum):
    """Communication provider types"""
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


class CampaignStatus(str, enum.Enum):
    """Campaign status"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class CampaignType(str, enum.Enum):
    """Campaign types"""
    ONE_TIME = "one_time"
    RECURRING = "recurring"
    TRIGGERED = "triggered"
    DRIP = "drip"
    AB_TEST = "ab_test"


class ConsentType(str, enum.Enum):
    """Communication consent types"""
    MARKETING = "marketing"
    TRANSACTIONAL = "transactional"
    APPOINTMENT_REMINDERS = "appointment_reminders"
    HEALTH_TIPS = "health_tips"
    SURVEYS = "surveys"
    EMERGENCY = "emergency"
    ALL_COMMUNICATIONS = "all_communications"


class ConsentStatus(str, enum.Enum):
    """Consent status"""
    GRANTED = "granted"
    DENIED = "denied"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"
    PENDING = "pending"


# ==================== Provider Configuration ====================

class OmnichannelProvider(Base):
    """Communication provider configurations"""
    __tablename__ = "omnichannel_providers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    provider_type = Column(Enum(ProviderType), nullable=False)
    channel = Column(Enum(OmniChannelType), nullable=False)
    is_primary = Column(Boolean, default=False)
    is_fallback = Column(Boolean, default=False)
    priority = Column(Integer, default=0)

    # Encrypted credentials
    credentials = Column(JSONB, nullable=False)
    credentials_encrypted = Column(Boolean, default=True)

    # Configuration
    config = Column(JSONB, default={})
    rate_limit_per_second = Column(Integer, default=10)
    rate_limit_per_day = Column(Integer)
    daily_usage_count = Column(Integer, default=0)
    daily_usage_reset_at = Column(DateTime(timezone=True))

    # Sender identities
    from_phone_number = Column(String(20))
    from_email = Column(String(255))
    from_name = Column(String(100))
    reply_to_email = Column(String(255))

    # WhatsApp specific
    whatsapp_business_account_id = Column(String(100))
    whatsapp_phone_number_id = Column(String(100))
    whatsapp_verified = Column(Boolean, default=False)

    # Status
    is_active = Column(Boolean, default=True)
    last_health_check = Column(DateTime(timezone=True))
    health_status = Column(String(20), default="healthy")
    failure_count = Column(Integer, default=0)
    last_failure_at = Column(DateTime(timezone=True))

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Relationships
    messages = relationship("OmnichannelMessage", back_populates="provider")


# ==================== Templates ====================

class OmnichannelTemplate(Base):
    """Message templates for all channels"""
    __tablename__ = "omnichannel_templates"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_template_tenant_code'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text)

    # Channel configuration
    channel = Column(Enum(OmniChannelType), nullable=False)
    category = Column(Enum(TemplateCategory))

    # Content
    subject = Column(String(255))
    body = Column(Text, nullable=False)
    body_html = Column(Text)
    header_text = Column(String(255))
    footer_text = Column(String(255))

    # Dynamic content
    variables = Column(JSONB, default=[])
    default_values = Column(JSONB, default={})

    # WhatsApp specific
    whatsapp_template_id = Column(String(100))
    whatsapp_template_name = Column(String(100))
    buttons = Column(JSONB, default=[])
    quick_replies = Column(JSONB, default=[])

    # Media
    media_type = Column(String(20))
    media_url = Column(String(500))
    media_filename = Column(String(255))

    # Status
    status = Column(Enum(TemplateStatus), default=TemplateStatus.DRAFT)
    approved_at = Column(DateTime(timezone=True))
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    rejection_reason = Column(Text)

    # Versioning
    version = Column(Integer, default=1)
    previous_version_id = Column(UUID(as_uuid=True))

    # Localization
    language = Column(String(10), default="en")
    translations = Column(JSONB, default={})

    # Usage
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True))

    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Relationships
    messages = relationship("OmnichannelMessage", back_populates="template")
    approvals = relationship("TemplateApproval", back_populates="template")


class TemplateApproval(Base):
    """Template approval workflow"""
    __tablename__ = "template_approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    template_id = Column(UUID(as_uuid=True), ForeignKey("omnichannel_templates.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    reviewed_at = Column(DateTime(timezone=True))
    status = Column(String(20), default="pending")
    comments = Column(Text)
    external_approval_id = Column(String(100))
    external_status = Column(String(50))

    # Relationships
    template = relationship("OmnichannelTemplate", back_populates="approvals")


# ==================== Conversations & Messages ====================

class OmnichannelConversation(Base):
    """Unified conversation threads across channels"""
    __tablename__ = "omnichannel_conversations"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'conversation_key', name='uq_conversation_key'),
        Index('ix_conversation_status_agent', 'tenant_id', 'status', 'assigned_agent_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), index=True)
    external_contact_id = Column(String(255))
    external_contact_name = Column(String(255))

    # Identification
    conversation_key = Column(String(255), nullable=False)
    session_id = Column(String(100))

    # Channel
    primary_channel = Column(Enum(OmniChannelType), nullable=False)
    channels_used = Column(ARRAY(String), default=[])

    # Status
    status = Column(Enum(ConversationStatus), default=ConversationStatus.NEW)
    priority = Column(Enum(ConversationPriority), default=ConversationPriority.NORMAL)
    sentiment = Column(String(20))
    sentiment_score = Column(Float)

    # Assignment
    assigned_agent_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    assigned_team_id = Column(UUID(as_uuid=True))
    assigned_at = Column(DateTime(timezone=True))
    last_agent_reply_at = Column(DateTime(timezone=True))

    # Message counts
    message_count = Column(Integer, default=0)
    inbound_count = Column(Integer, default=0)
    outbound_count = Column(Integer, default=0)
    unread_count = Column(Integer, default=0)

    # Context
    topic = Column(String(100))
    sub_topic = Column(String(100))
    tags = Column(ARRAY(String), default=[])
    context = Column(JSONB, default={})

    # Related resources
    related_resource_type = Column(String(50))
    related_resource_id = Column(UUID(as_uuid=True))

    # SLA
    sla_config_id = Column(UUID(as_uuid=True))
    first_response_at = Column(DateTime(timezone=True))
    first_response_sla_met = Column(Boolean)
    resolution_sla_met = Column(Boolean)

    # Timestamps
    first_message_at = Column(DateTime(timezone=True))
    last_message_at = Column(DateTime(timezone=True))
    last_patient_message_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    closed_at = Column(DateTime(timezone=True))
    closed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    messages = relationship("OmnichannelMessage", back_populates="conversation", order_by="OmnichannelMessage.created_at")
    assignments = relationship("InboxAssignment", back_populates="conversation")
    sla_tracking = relationship("SLATracking", back_populates="conversation", uselist=False)


class OmnichannelMessage(Base):
    """Messages across all channels"""
    __tablename__ = "omnichannel_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("omnichannel_conversations.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), index=True)

    # Identification
    external_id = Column(String(255), index=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("omnichannel_providers.id"))

    # Channel
    channel = Column(Enum(OmniChannelType), nullable=False)
    direction = Column(Enum(MessageDirection), nullable=False)

    # Sender/Recipient
    sender_type = Column(String(20))
    sender_id = Column(UUID(as_uuid=True))
    sender_name = Column(String(255))
    sender_contact = Column(String(255))
    recipient_contact = Column(String(255))

    # Content
    message_type = Column(String(50), default="text")
    content = Column(Text)
    content_encrypted = Column(Boolean, default=False)
    content_structured = Column(JSONB)

    # Template
    template_id = Column(UUID(as_uuid=True), ForeignKey("omnichannel_templates.id"))
    template_variables = Column(JSONB)

    # Email specific
    subject = Column(String(255))
    cc = Column(ARRAY(String))
    bcc = Column(ARRAY(String))

    # Interactive elements
    buttons = Column(JSONB)
    list_sections = Column(JSONB)
    selected_button_id = Column(String(100))
    selected_list_item_id = Column(String(100))

    # Reply context
    reply_to_message_id = Column(UUID(as_uuid=True), ForeignKey("omnichannel_messages.id"))
    reply_to_external_id = Column(String(255))

    # Delivery status
    status = Column(Enum(DeliveryStatus), default=DeliveryStatus.PENDING)
    error_code = Column(String(50))
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    next_retry_at = Column(DateTime(timezone=True))

    # Timestamps
    queued_at = Column(DateTime(timezone=True))
    sent_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    read_at = Column(DateTime(timezone=True))
    failed_at = Column(DateTime(timezone=True))

    # Cost
    cost = Column(Numeric(10, 4))
    cost_currency = Column(String(3), default="USD")
    segments = Column(Integer, default=1)

    # AI analysis
    intent = Column(String(100))
    entities = Column(JSONB)
    sentiment = Column(String(20))
    sentiment_score = Column(Float)
    language_detected = Column(String(10))
    auto_translated = Column(Boolean, default=False)
    original_content = Column(Text)

    # Metadata
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Relationships
    conversation = relationship("OmnichannelConversation", back_populates="messages")
    provider = relationship("OmnichannelProvider", back_populates="messages")
    template = relationship("OmnichannelTemplate", back_populates="messages")
    attachments = relationship("MessageAttachment", back_populates="message")
    delivery_statuses = relationship("MessageDeliveryStatus", back_populates="message")


class MessageAttachment(Base):
    """Message attachments"""
    __tablename__ = "message_attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    message_id = Column(UUID(as_uuid=True), ForeignKey("omnichannel_messages.id"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # File info
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50))
    mime_type = Column(String(100))
    file_size = Column(BigInteger)

    # Storage
    storage_provider = Column(String(20), default="s3")
    storage_key = Column(String(500))
    storage_url = Column(String(1000))
    signed_url = Column(String(2000))
    signed_url_expires_at = Column(DateTime(timezone=True))

    # Provider specific
    external_media_id = Column(String(255))
    external_url = Column(String(1000))

    # Security
    is_encrypted = Column(Boolean, default=True)
    encryption_key_id = Column(String(100))
    checksum = Column(String(64))

    # Media info
    thumbnail_url = Column(String(1000))
    width = Column(Integer)
    height = Column(Integer)
    duration_seconds = Column(Integer)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    message = relationship("OmnichannelMessage", back_populates="attachments")


class MessageDeliveryStatus(Base):
    """Detailed delivery status tracking"""
    __tablename__ = "message_delivery_status"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    message_id = Column(UUID(as_uuid=True), ForeignKey("omnichannel_messages.id"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Status
    status = Column(Enum(DeliveryStatus), nullable=False)
    status_at = Column(DateTime(timezone=True), server_default=func.now())

    # Provider info
    provider_id = Column(UUID(as_uuid=True), ForeignKey("omnichannel_providers.id"))
    provider_status = Column(String(50))
    provider_response = Column(JSONB)

    # Error details
    error_code = Column(String(50))
    error_message = Column(Text)
    is_permanent_failure = Column(Boolean, default=False)

    # Webhook
    webhook_payload = Column(JSONB)
    webhook_received_at = Column(DateTime(timezone=True))

    # Relationships
    message = relationship("OmnichannelMessage", back_populates="delivery_statuses")


# ==================== Preferences & Consent ====================

class CommunicationPreference(Base):
    """Patient communication preferences"""
    __tablename__ = "communication_preferences"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'patient_id', name='uq_preference_patient'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)

    # Channel preferences
    preferred_channel = Column(Enum(OmniChannelType))
    fallback_channel = Column(Enum(OmniChannelType))
    channel_preferences = Column(JSONB, default={})

    # Contact info
    phone_primary = Column(String(20))
    phone_secondary = Column(String(20))
    email_primary = Column(String(255))
    email_secondary = Column(String(255))
    whatsapp_number = Column(String(20))

    # Time preferences
    preferred_language = Column(String(10), default="en")
    timezone = Column(String(50), default="UTC")
    preferred_time_start = Column(Time)
    preferred_time_end = Column(Time)
    do_not_disturb_start = Column(Time)
    do_not_disturb_end = Column(Time)
    allow_weekend_contact = Column(Boolean, default=True)

    # Frequency
    max_messages_per_day = Column(Integer)
    max_messages_per_week = Column(Integer)
    min_hours_between_messages = Column(Integer, default=1)

    # Category preferences
    appointment_reminders = Column(Boolean, default=True)
    appointment_reminder_hours = Column(ARRAY(Integer), default=[24, 2])
    health_tips = Column(Boolean, default=False)
    marketing_messages = Column(Boolean, default=False)
    survey_invitations = Column(Boolean, default=True)
    lab_results = Column(Boolean, default=True)
    prescription_reminders = Column(Boolean, default=True)
    billing_notifications = Column(Boolean, default=True)
    emergency_alerts = Column(Boolean, default=True)

    # Smart routing
    auto_channel_selection = Column(Boolean, default=True)
    cost_optimization = Column(Boolean, default=False)

    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))


class ConsentRecord(Base):
    """HIPAA-compliant consent tracking"""
    __tablename__ = "consent_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)

    # Consent details
    consent_type = Column(Enum(ConsentType), nullable=False)
    channel = Column(Enum(OmniChannelType))
    status = Column(Enum(ConsentStatus), nullable=False)

    # Capture details
    capture_method = Column(String(50))
    capture_source = Column(String(100))
    ip_address = Column(String(45))
    user_agent = Column(String(500))

    # Legal
    consent_text = Column(Text)
    consent_version = Column(String(20))
    legal_basis = Column(String(50))
    purposes = Column(ARRAY(String))

    # Validity
    valid_from = Column(DateTime(timezone=True), server_default=func.now())
    valid_until = Column(DateTime(timezone=True))

    # Withdrawal
    withdrawn_at = Column(DateTime(timezone=True))
    withdrawal_method = Column(String(50))
    withdrawal_reason = Column(Text)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class OptOutRecord(Base):
    """Opt-out management"""
    __tablename__ = "opt_out_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))

    # Contact
    contact_type = Column(String(20), nullable=False)
    contact_value = Column(String(255), nullable=False)

    # Opt-out details
    channel = Column(Enum(OmniChannelType))
    opt_out_type = Column(String(50))
    reason = Column(Text)

    # Capture
    method = Column(String(50))
    source_message_id = Column(UUID(as_uuid=True))
    source_campaign_id = Column(UUID(as_uuid=True))

    # Status
    is_active = Column(Boolean, default=True)
    opted_out_at = Column(DateTime(timezone=True), server_default=func.now())
    opted_back_in_at = Column(DateTime(timezone=True))

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ==================== Campaigns ====================

class Campaign(Base):
    """Multi-channel campaigns"""
    __tablename__ = "campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Configuration
    campaign_type = Column(Enum(CampaignType), nullable=False)
    channels = Column(ARRAY(String), nullable=False)
    primary_channel = Column(Enum(OmniChannelType))

    # Content
    template_id = Column(UUID(as_uuid=True), ForeignKey("omnichannel_templates.id"))
    subject = Column(String(255))
    content = Column(Text)
    content_html = Column(Text)

    # Audience
    segment_id = Column(UUID(as_uuid=True))
    segment_query = Column(JSONB)
    estimated_audience_size = Column(Integer)
    exclusion_lists = Column(ARRAY(UUID(as_uuid=True)))

    # Scheduling
    scheduled_at = Column(DateTime(timezone=True))
    timezone = Column(String(50), default="UTC")
    send_window_start = Column(Time)
    send_window_end = Column(Time)
    respect_dnd = Column(Boolean, default=True)

    # Recurring
    recurrence_rule = Column(String(255))
    recurrence_end_date = Column(DateTime(timezone=True))
    next_execution_at = Column(DateTime(timezone=True))

    # Trigger
    trigger_event = Column(String(100))
    trigger_conditions = Column(JSONB)
    trigger_delay_minutes = Column(Integer, default=0)

    # A/B Testing
    is_ab_test = Column(Boolean, default=False)
    ab_test_percentage = Column(Integer, default=20)
    ab_winner_criteria = Column(String(50))
    ab_test_duration_hours = Column(Integer, default=24)
    ab_winner_variant_id = Column(UUID(as_uuid=True))

    # Status
    status = Column(Enum(CampaignStatus), default=CampaignStatus.DRAFT)

    # Budget
    budget_limit = Column(Numeric(10, 2))
    budget_spent = Column(Numeric(10, 2), default=0)
    cost_per_message = Column(Numeric(10, 4))

    # Metrics
    total_recipients = Column(Integer, default=0)
    messages_sent = Column(Integer, default=0)
    messages_delivered = Column(Integer, default=0)
    messages_failed = Column(Integer, default=0)
    messages_opened = Column(Integer, default=0)
    messages_clicked = Column(Integer, default=0)
    opt_outs = Column(Integer, default=0)

    # Timestamps
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    paused_at = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))

    # Metadata
    tags = Column(ARRAY(String))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Relationships
    template = relationship("OmnichannelTemplate")
    executions = relationship("CampaignExecution", back_populates="campaign")
    variants = relationship("ABTestVariant", back_populates="campaign")
    analytics = relationship("CampaignAnalytics", back_populates="campaign")


class CampaignSegment(Base):
    """Audience segmentation"""
    __tablename__ = "campaign_segments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)

    # Definition
    conditions = Column(JSONB, nullable=False)
    condition_logic = Column(String(10), default="AND")

    # Size
    estimated_size = Column(Integer)
    last_calculated_at = Column(DateTime(timezone=True))
    auto_refresh = Column(Boolean, default=True)
    refresh_interval_hours = Column(Integer, default=24)

    # Membership
    is_static = Column(Boolean, default=False)
    static_members = Column(ARRAY(UUID(as_uuid=True)))

    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))


class ABTestVariant(Base):
    """A/B test variants"""
    __tablename__ = "ab_test_variants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Variant
    name = Column(String(50), nullable=False)
    weight = Column(Integer, default=50)

    # Content
    subject = Column(String(255))
    content = Column(Text)
    template_id = Column(UUID(as_uuid=True), ForeignKey("omnichannel_templates.id"))

    # Metrics
    recipients = Column(Integer, default=0)
    sent = Column(Integer, default=0)
    delivered = Column(Integer, default=0)
    opened = Column(Integer, default=0)
    clicked = Column(Integer, default=0)
    converted = Column(Integer, default=0)

    # Rates
    delivery_rate = Column(Float)
    open_rate = Column(Float)
    click_rate = Column(Float)
    conversion_rate = Column(Float)

    # Winner
    is_winner = Column(Boolean, default=False)
    winner_declared_at = Column(DateTime(timezone=True))

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    campaign = relationship("Campaign", back_populates="variants")


class CampaignExecution(Base):
    """Campaign execution tracking"""
    __tablename__ = "campaign_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Tracking
    execution_number = Column(Integer, default=1)
    status = Column(String(20), default="pending")
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # Metrics
    total_recipients = Column(Integer, default=0)
    processed = Column(Integer, default=0)
    sent = Column(Integer, default=0)
    delivered = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    skipped = Column(Integer, default=0)

    # Cost
    total_cost = Column(Numeric(10, 2), default=0)

    # Errors
    error_message = Column(Text)
    error_details = Column(JSONB)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    campaign = relationship("Campaign", back_populates="executions")


# ==================== Unified Inbox ====================

class InboxAssignment(Base):
    """Agent conversation assignments"""
    __tablename__ = "inbox_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("omnichannel_conversations.id"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Assignment
    agent_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    assignment_type = Column(String(20), default="manual")

    # Status
    is_active = Column(Boolean, default=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    unassigned_at = Column(DateTime(timezone=True))
    unassignment_reason = Column(String(50))

    # Transfer
    transferred_from = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    transfer_notes = Column(Text)

    # Relationships
    conversation = relationship("OmnichannelConversation", back_populates="assignments")


class CannedResponse(Base):
    """Pre-defined response templates"""
    __tablename__ = "canned_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Content
    name = Column(String(100), nullable=False)
    shortcut = Column(String(50))
    content = Column(Text, nullable=False)

    # Categorization
    category = Column(String(50))
    tags = Column(ARRAY(String))

    # Scope
    is_global = Column(Boolean, default=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Variables
    variables = Column(ARRAY(String))

    # Usage
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True))

    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))


class ConversationTag(Base):
    """Conversation categorization tags"""
    __tablename__ = "conversation_tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(50), nullable=False)
    color = Column(String(7))
    description = Column(Text)
    is_system = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SLAConfiguration(Base):
    """SLA definitions"""
    __tablename__ = "sla_configurations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)

    # First response (minutes)
    first_response_time_low = Column(Integer, default=60)
    first_response_time_normal = Column(Integer, default=30)
    first_response_time_high = Column(Integer, default=15)
    first_response_time_urgent = Column(Integer, default=5)

    # Resolution (minutes)
    resolution_time_low = Column(Integer, default=1440)
    resolution_time_normal = Column(Integer, default=480)
    resolution_time_high = Column(Integer, default=240)
    resolution_time_urgent = Column(Integer, default=60)

    # Business hours
    business_hours_only = Column(Boolean, default=True)
    business_hours_start = Column(Time, default=time(9, 0))
    business_hours_end = Column(Time, default=time(17, 0))
    business_days = Column(ARRAY(Integer), default=[1, 2, 3, 4, 5])

    # Escalation
    escalation_enabled = Column(Boolean, default=True)
    escalation_threshold_percentage = Column(Integer, default=80)
    escalation_notify_emails = Column(ARRAY(String))

    # Metadata
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    tracking = relationship("SLATracking", back_populates="sla_config")


class SLATracking(Base):
    """SLA compliance tracking"""
    __tablename__ = "sla_tracking"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("omnichannel_conversations.id"), nullable=False, index=True)
    sla_config_id = Column(UUID(as_uuid=True), ForeignKey("sla_configurations.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # First response
    first_response_due_at = Column(DateTime(timezone=True))
    first_response_at = Column(DateTime(timezone=True))
    first_response_breached = Column(Boolean, default=False)
    first_response_time_seconds = Column(Integer)

    # Resolution
    resolution_due_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    resolution_breached = Column(Boolean, default=False)
    resolution_time_seconds = Column(Integer)

    # Escalation
    escalated = Column(Boolean, default=False)
    escalated_at = Column(DateTime(timezone=True))
    escalation_level = Column(Integer, default=0)

    # Pause
    paused_at = Column(DateTime(timezone=True))
    total_paused_seconds = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    conversation = relationship("OmnichannelConversation", back_populates="sla_tracking")
    sla_config = relationship("SLAConfiguration", back_populates="tracking")


# ==================== Analytics ====================

class ChannelAnalyticsDaily(Base):
    """Daily channel metrics"""
    __tablename__ = "channel_analytics_daily"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'date', 'channel', name='uq_channel_analytics_date'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    channel = Column(Enum(OmniChannelType), nullable=False)

    # Volume
    messages_sent = Column(Integer, default=0)
    messages_delivered = Column(Integer, default=0)
    messages_failed = Column(Integer, default=0)
    messages_received = Column(Integer, default=0)
    conversations_started = Column(Integer, default=0)
    conversations_resolved = Column(Integer, default=0)

    # Rates
    delivery_rate = Column(Float)
    open_rate = Column(Float)
    click_rate = Column(Float)
    response_rate = Column(Float)

    # Response time
    avg_first_response_seconds = Column(Float)
    avg_resolution_seconds = Column(Float)
    median_first_response_seconds = Column(Float)
    median_resolution_seconds = Column(Float)

    # Cost
    total_cost = Column(Numeric(10, 2), default=0)
    cost_per_message = Column(Numeric(10, 4))

    # SLA
    sla_first_response_met = Column(Integer, default=0)
    sla_first_response_breached = Column(Integer, default=0)
    sla_resolution_met = Column(Integer, default=0)
    sla_resolution_breached = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CampaignAnalytics(Base):
    """Campaign performance metrics"""
    __tablename__ = "campaign_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    date = Column(Date, nullable=False)

    # Delivery
    sent = Column(Integer, default=0)
    delivered = Column(Integer, default=0)
    bounced = Column(Integer, default=0)
    failed = Column(Integer, default=0)

    # Engagement
    opened = Column(Integer, default=0)
    unique_opens = Column(Integer, default=0)
    clicked = Column(Integer, default=0)
    unique_clicks = Column(Integer, default=0)
    replied = Column(Integer, default=0)
    unsubscribed = Column(Integer, default=0)
    spam_reports = Column(Integer, default=0)

    # Conversion
    conversions = Column(Integer, default=0)
    conversion_value = Column(Numeric(10, 2), default=0)

    # Rates
    delivery_rate = Column(Float)
    open_rate = Column(Float)
    click_rate = Column(Float)
    conversion_rate = Column(Float)

    # Cost
    total_cost = Column(Numeric(10, 2), default=0)
    cost_per_conversion = Column(Numeric(10, 2))

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    campaign = relationship("Campaign", back_populates="analytics")


class EngagementScore(Base):
    """Patient engagement scoring"""
    __tablename__ = "engagement_scores"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'patient_id', name='uq_engagement_patient'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)

    # Score
    overall_score = Column(Float, nullable=False)
    score_tier = Column(String(20))

    # Components
    response_score = Column(Float)
    open_score = Column(Float)
    click_score = Column(Float)
    recency_score = Column(Float)
    frequency_score = Column(Float)

    # Activity
    messages_received_30d = Column(Integer, default=0)
    messages_opened_30d = Column(Integer, default=0)
    messages_clicked_30d = Column(Integer, default=0)
    responses_30d = Column(Integer, default=0)
    last_interaction_at = Column(DateTime(timezone=True))

    # Channel engagement
    preferred_channel = Column(String(20))
    best_engagement_time = Column(Time)
    best_engagement_day = Column(Integer)

    # Metadata
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ==================== Audit & Compliance ====================

class CommunicationAuditLog(Base):
    """HIPAA audit trail"""
    __tablename__ = "communication_audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Resource
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(UUID(as_uuid=True), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), index=True)

    # Action
    action = Column(String(50), nullable=False)
    action_details = Column(JSONB)

    # Actor
    actor_type = Column(String(20), nullable=False)
    actor_id = Column(UUID(as_uuid=True))
    actor_name = Column(String(255))
    actor_ip = Column(String(45))
    actor_user_agent = Column(String(500))

    # PHI
    contains_phi = Column(Boolean, default=False)
    phi_accessed = Column(ARRAY(String))

    # Channel
    channel = Column(String(20))
    external_id = Column(String(255))

    # Request
    request_id = Column(String(100))
    request_method = Column(String(10))
    request_path = Column(String(500))

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class EncryptionKey(Base):
    """Encryption key management"""
    __tablename__ = "encryption_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Key
    key_id = Column(String(100), nullable=False)
    key_type = Column(String(20), nullable=False)
    algorithm = Column(String(20), default="AES-256-GCM")

    # Version
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)

    # Rotation
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    rotated_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    rotated_from_id = Column(UUID(as_uuid=True))
