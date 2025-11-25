"""
Patient Portal Platform - SQLAlchemy Models
EPIC-014: Comprehensive patient self-service portal

Database tables for:
- Portal user accounts and authentication
- Session management
- Proxy/family access
- Secure messaging
- User preferences
- Audit logging
"""
from datetime import datetime, time, date
from typing import Optional, List
from uuid import uuid4
import enum

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Float, DateTime, Date, Time,
    ForeignKey, Enum, BigInteger, Numeric, UniqueConstraint, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from shared.database.connection import Base


def generate_uuid():
    return uuid4()


# ==================== Enums ====================

class PortalUserStatus(str, enum.Enum):
    """Portal user account status"""
    PENDING_VERIFICATION = "pending_verification"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    LOCKED = "locked"
    DEACTIVATED = "deactivated"


class VerificationType(str, enum.Enum):
    """Verification method types"""
    EMAIL = "email"
    SMS = "sms"
    IDENTITY = "identity"
    MFA = "mfa"


class MFAMethod(str, enum.Enum):
    """Multi-factor authentication methods"""
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    BIOMETRIC = "biometric"
    BACKUP_CODE = "backup_code"


class SessionStatus(str, enum.Enum):
    """Session status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    LOGGED_OUT = "logged_out"


class ProxyRelationship(str, enum.Enum):
    """Proxy relationship types"""
    PARENT = "parent"
    GUARDIAN = "guardian"
    SPOUSE = "spouse"
    CHILD = "child"
    CAREGIVER = "caregiver"
    POWER_OF_ATTORNEY = "power_of_attorney"
    HEALTHCARE_PROXY = "healthcare_proxy"
    OTHER = "other"


class ProxyAccessLevel(str, enum.Enum):
    """Proxy access levels"""
    FULL = "full"
    READ_ONLY = "read_only"
    APPOINTMENTS_ONLY = "appointments_only"
    MESSAGES_ONLY = "messages_only"
    BILLING_ONLY = "billing_only"
    CUSTOM = "custom"


class MessageFolder(str, enum.Enum):
    """Message folder types"""
    INBOX = "inbox"
    SENT = "sent"
    DRAFTS = "drafts"
    ARCHIVED = "archived"
    TRASH = "trash"


class MessagePriority(str, enum.Enum):
    """Message priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class MessageStatus(str, enum.Enum):
    """Message status"""
    DRAFT = "draft"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    REPLIED = "replied"
    ARCHIVED = "archived"
    DELETED = "deleted"


class AuditAction(str, enum.Enum):
    """Audit action types"""
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    PROFILE_UPDATE = "profile_update"
    RECORDS_ACCESSED = "records_accessed"
    RECORDS_DOWNLOADED = "records_downloaded"
    RECORDS_SHARED = "records_shared"
    MESSAGE_SENT = "message_sent"
    MESSAGE_READ = "message_read"
    APPOINTMENT_BOOKED = "appointment_booked"
    APPOINTMENT_CANCELLED = "appointment_cancelled"
    PAYMENT_MADE = "payment_made"
    PRESCRIPTION_REFILL = "prescription_refill"
    PROXY_ACCESS_GRANTED = "proxy_access_granted"
    PROXY_ACCESS_REVOKED = "proxy_access_revoked"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"


class PaymentMethod(str, enum.Enum):
    """Payment method types"""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    ACH = "ach"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"
    HSA = "hsa"
    FSA = "fsa"


class PaymentStatus(str, enum.Enum):
    """Payment status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    DISPUTED = "disputed"


class RefillStatus(str, enum.Enum):
    """Prescription refill status"""
    REQUESTED = "requested"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    DENIED = "denied"
    PROCESSING = "processing"
    READY_FOR_PICKUP = "ready_for_pickup"
    SHIPPED = "shipped"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ==================== Portal Users ====================

class PortalUser(Base):
    """Patient portal user accounts"""
    __tablename__ = "portal_users"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'email', name='uq_portal_user_email'),
        Index('ix_portal_user_patient', 'tenant_id', 'patient_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)

    # Authentication
    email = Column(String(255), nullable=False)
    password_hash = Column(String(255))
    password_salt = Column(String(64))
    password_changed_at = Column(DateTime(timezone=True))
    password_expires_at = Column(DateTime(timezone=True))
    require_password_change = Column(Boolean, default=False)

    # Account Status
    status = Column(Enum(PortalUserStatus), default=PortalUserStatus.PENDING_VERIFICATION)
    activation_code = Column(String(100))
    activation_code_expires_at = Column(DateTime(timezone=True))

    # Email Verification
    email_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime(timezone=True))
    email_verification_token = Column(String(255))
    email_verification_expires_at = Column(DateTime(timezone=True))

    # Phone Verification
    phone_number = Column(String(20))
    phone_verified = Column(Boolean, default=False)
    phone_verified_at = Column(DateTime(timezone=True))
    phone_verification_code = Column(String(10))
    phone_verification_expires_at = Column(DateTime(timezone=True))

    # Multi-Factor Authentication
    mfa_enabled = Column(Boolean, default=False)
    mfa_method = Column(Enum(MFAMethod))
    mfa_secret = Column(String(255))
    mfa_backup_codes = Column(JSONB, default=[])
    mfa_enabled_at = Column(DateTime(timezone=True))

    # Security
    login_attempts = Column(Integer, default=0)
    last_failed_login_at = Column(DateTime(timezone=True))
    locked_until = Column(DateTime(timezone=True))
    security_questions = Column(JSONB, default=[])

    # Session tracking
    last_login_at = Column(DateTime(timezone=True))
    last_login_ip = Column(INET)
    last_login_user_agent = Column(String(500))
    last_activity_at = Column(DateTime(timezone=True))
    total_logins = Column(Integer, default=0)

    # Profile
    display_name = Column(String(100))
    avatar_url = Column(String(500))
    preferred_language = Column(String(10), default="en")
    timezone = Column(String(50), default="UTC")

    # Terms
    terms_accepted = Column(Boolean, default=False)
    terms_accepted_at = Column(DateTime(timezone=True))
    terms_version = Column(String(20))
    privacy_accepted = Column(Boolean, default=False)
    privacy_accepted_at = Column(DateTime(timezone=True))

    # SSO
    sso_provider = Column(String(50))
    sso_provider_id = Column(String(255))
    sso_linked_at = Column(DateTime(timezone=True))

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deactivated_at = Column(DateTime(timezone=True))
    deactivation_reason = Column(Text)

    # Relationships
    sessions = relationship("PortalSession", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("PortalPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    messages_sent = relationship("SecureMessage", foreign_keys="[SecureMessage.sender_id]", back_populates="sender")
    messages_received = relationship("SecureMessage", foreign_keys="[SecureMessage.recipient_id]", back_populates="recipient")
    proxy_grants = relationship("ProxyAccess", foreign_keys="[ProxyAccess.grantor_id]", back_populates="grantor")
    proxy_received = relationship("ProxyAccess", foreign_keys="[ProxyAccess.grantee_id]", back_populates="grantee")
    saved_payments = relationship("SavedPaymentMethod", back_populates="user", cascade="all, delete-orphan")
    refill_requests = relationship("RefillRequest", back_populates="user")
    audit_logs = relationship("PortalAuditLog", back_populates="user")
    notifications = relationship("PortalNotification", back_populates="user", cascade="all, delete-orphan")


class PortalSession(Base):
    """User session management"""
    __tablename__ = "portal_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("portal_users.id"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Token
    token_hash = Column(String(255), unique=True, nullable=False)
    refresh_token_hash = Column(String(255), unique=True)

    # Session info
    status = Column(Enum(SessionStatus), default=SessionStatus.ACTIVE)
    device_type = Column(String(50))
    device_name = Column(String(100))
    browser = Column(String(100))
    os = Column(String(100))
    ip_address = Column(INET)
    user_agent = Column(Text)
    location = Column(JSONB)

    # Expiration
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    refresh_expires_at = Column(DateTime(timezone=True))
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())

    # Termination
    ended_at = Column(DateTime(timezone=True))
    end_reason = Column(String(50))

    # Proxy context
    is_proxy_session = Column(Boolean, default=False)
    proxy_patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))

    # Relationships
    user = relationship("PortalUser", back_populates="sessions")


# ==================== Proxy Access ====================

class ProxyAccess(Base):
    """Proxy/family access management"""
    __tablename__ = "proxy_access"
    __table_args__ = (
        UniqueConstraint('grantor_id', 'grantee_id', name='uq_proxy_grantor_grantee'),
        Index('ix_proxy_grantee', 'grantee_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Parties
    grantor_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    grantee_id = Column(UUID(as_uuid=True), ForeignKey("portal_users.id"), nullable=False)

    # Relationship
    relationship_type = Column(Enum(ProxyRelationship), nullable=False)
    relationship_description = Column(String(255))

    # Access
    access_level = Column(Enum(ProxyAccessLevel), nullable=False)
    custom_permissions = Column(JSONB, default={})

    # Permissions flags
    can_view_records = Column(Boolean, default=True)
    can_download_records = Column(Boolean, default=False)
    can_share_records = Column(Boolean, default=False)
    can_book_appointments = Column(Boolean, default=True)
    can_cancel_appointments = Column(Boolean, default=True)
    can_send_messages = Column(Boolean, default=True)
    can_view_billing = Column(Boolean, default=True)
    can_make_payments = Column(Boolean, default=False)
    can_request_refills = Column(Boolean, default=True)
    can_view_sensitive_records = Column(Boolean, default=False)

    # Validity
    valid_from = Column(DateTime(timezone=True), server_default=func.now())
    valid_until = Column(DateTime(timezone=True))
    is_permanent = Column(Boolean, default=False)

    # Status
    is_active = Column(Boolean, default=True)
    revoked_at = Column(DateTime(timezone=True))
    revoked_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    revocation_reason = Column(Text)

    # Verification
    verification_required = Column(Boolean, default=True)
    verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True))
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    verification_document_id = Column(UUID(as_uuid=True))

    # Legal
    legal_document_id = Column(UUID(as_uuid=True))
    legal_document_type = Column(String(50))
    consent_obtained = Column(Boolean, default=False)
    consent_obtained_at = Column(DateTime(timezone=True))

    # For minors
    is_minor_access = Column(Boolean, default=False)
    minor_date_of_birth = Column(Date)
    minor_age_out_date = Column(Date)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Relationships
    grantor = relationship("PortalUser", foreign_keys=[grantee_id], back_populates="proxy_received")
    grantee = relationship("PortalUser", foreign_keys=[grantee_id], back_populates="proxy_received")


# ==================== Secure Messaging ====================

class MessageThread(Base):
    """Message thread/conversation"""
    __tablename__ = "message_threads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)

    # Thread info
    subject = Column(String(255), nullable=False)
    category = Column(String(50))
    tags = Column(ARRAY(String), default=[])

    # Participants
    provider_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    provider_name = Column(String(255))
    department = Column(String(100))
    care_team_id = Column(UUID(as_uuid=True))

    # Status
    is_open = Column(Boolean, default=True)
    is_urgent = Column(Boolean, default=False)
    requires_response = Column(Boolean, default=True)
    auto_response_sent = Column(Boolean, default=False)

    # Message counts
    message_count = Column(Integer, default=0)
    unread_patient_count = Column(Integer, default=0)
    unread_provider_count = Column(Integer, default=0)

    # Timestamps
    last_message_at = Column(DateTime(timezone=True))
    last_patient_message_at = Column(DateTime(timezone=True))
    last_provider_message_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Related resources
    related_appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id"))
    related_encounter_id = Column(UUID(as_uuid=True))

    # SLA
    response_due_at = Column(DateTime(timezone=True))
    response_sla_met = Column(Boolean)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    archived_at = Column(DateTime(timezone=True))

    # Relationships
    messages = relationship("SecureMessage", back_populates="thread", order_by="SecureMessage.created_at")


class SecureMessage(Base):
    """Secure messages between patients and providers"""
    __tablename__ = "secure_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    thread_id = Column(UUID(as_uuid=True), ForeignKey("message_threads.id"), nullable=False, index=True)

    # Parties
    sender_id = Column(UUID(as_uuid=True), ForeignKey("portal_users.id"), index=True)
    sender_type = Column(String(20), nullable=False)  # patient, provider, system
    sender_name = Column(String(255))
    recipient_id = Column(UUID(as_uuid=True), ForeignKey("portal_users.id"))
    recipient_type = Column(String(20))
    recipient_name = Column(String(255))

    # Content
    content = Column(Text, nullable=False)
    content_html = Column(Text)
    is_encrypted = Column(Boolean, default=True)
    encryption_key_id = Column(String(100))

    # Attachments
    has_attachments = Column(Boolean, default=False)
    attachment_count = Column(Integer, default=0)

    # Status
    status = Column(Enum(MessageStatus), default=MessageStatus.SENT)
    priority = Column(Enum(MessagePriority), default=MessagePriority.NORMAL)
    folder = Column(Enum(MessageFolder), default=MessageFolder.INBOX)

    # Delivery
    sent_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    read_at = Column(DateTime(timezone=True))
    replied_at = Column(DateTime(timezone=True))

    # Reply context
    reply_to_id = Column(UUID(as_uuid=True), ForeignKey("secure_messages.id"))
    is_auto_response = Column(Boolean, default=False)
    auto_response_type = Column(String(50))

    # Forwarding
    forwarded_from_id = Column(UUID(as_uuid=True))
    forwarded_to = Column(ARRAY(UUID(as_uuid=True)))
    forwarded_at = Column(DateTime(timezone=True))

    # Proxy context
    sent_via_proxy = Column(Boolean, default=False)
    proxy_user_id = Column(UUID(as_uuid=True), ForeignKey("portal_users.id"))

    # Metadata
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(UUID(as_uuid=True))

    # Relationships
    thread = relationship("MessageThread", back_populates="messages")
    sender = relationship("PortalUser", foreign_keys=[sender_id], back_populates="messages_sent")
    recipient = relationship("PortalUser", foreign_keys=[recipient_id], back_populates="messages_received")
    attachments = relationship("MessageAttachmentPortal", back_populates="message", cascade="all, delete-orphan")


class MessageAttachmentPortal(Base):
    """Secure message attachments"""
    __tablename__ = "portal_message_attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    message_id = Column(UUID(as_uuid=True), ForeignKey("secure_messages.id"), nullable=False, index=True)
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

    # Security
    is_encrypted = Column(Boolean, default=True)
    encryption_key_id = Column(String(100))
    checksum = Column(String(64))

    # Scanning
    virus_scanned = Column(Boolean, default=False)
    virus_scan_result = Column(String(50))
    scanned_at = Column(DateTime(timezone=True))

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    message = relationship("SecureMessage", back_populates="attachments")


# ==================== User Preferences ====================

class PortalPreference(Base):
    """User portal preferences and settings"""
    __tablename__ = "portal_preferences"

    user_id = Column(UUID(as_uuid=True), ForeignKey("portal_users.id"), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Display
    language = Column(String(10), default="en")
    timezone = Column(String(50), default="UTC")
    date_format = Column(String(20), default="MM/DD/YYYY")
    time_format = Column(String(10), default="12h")
    theme = Column(String(20), default="light")

    # Accessibility
    accessibility_settings = Column(JSONB, default={
        "font_size": "medium",
        "high_contrast": False,
        "screen_reader_optimized": False,
        "reduce_motion": False,
        "color_blind_mode": None
    })

    # Notifications
    notification_settings = Column(JSONB, default={
        "email_enabled": True,
        "sms_enabled": True,
        "push_enabled": True,
        "appointment_reminders": True,
        "appointment_reminder_hours": [24, 2],
        "lab_results_available": True,
        "new_messages": True,
        "billing_notifications": True,
        "prescription_ready": True,
        "health_tips": False,
        "marketing": False
    })

    # Dashboard
    dashboard_layout = Column(JSONB, default={
        "widgets": [
            {"id": "appointments", "position": 1, "visible": True},
            {"id": "medications", "position": 2, "visible": True},
            {"id": "messages", "position": 3, "visible": True},
            {"id": "health_summary", "position": 4, "visible": True},
            {"id": "billing", "position": 5, "visible": True}
        ]
    })

    # Privacy
    privacy_settings = Column(JSONB, default={
        "show_photo": True,
        "share_health_data_research": False,
        "allow_care_team_access": True
    })

    # Communication
    communication_preferences = Column(JSONB, default={
        "preferred_contact_method": "email",
        "appointment_confirmation": "email",
        "lab_results_notification": "email",
        "billing_statements": "email",
        "do_not_disturb_start": None,
        "do_not_disturb_end": None
    })

    # Quick actions
    favorite_actions = Column(ARRAY(String), default=[
        "book_appointment",
        "send_message",
        "request_refill"
    ])

    # Onboarding
    onboarding_completed = Column(Boolean, default=False)
    onboarding_completed_at = Column(DateTime(timezone=True))
    tour_completed = Column(Boolean, default=False)
    feature_tips_shown = Column(JSONB, default={})

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("PortalUser", back_populates="preferences")


# ==================== Billing & Payments ====================

class SavedPaymentMethod(Base):
    """Saved payment methods for portal users"""
    __tablename__ = "saved_payment_methods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("portal_users.id"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Payment method
    payment_type = Column(Enum(PaymentMethod), nullable=False)
    is_default = Column(Boolean, default=False)
    nickname = Column(String(50))

    # Card details (tokenized)
    card_brand = Column(String(20))
    card_last_four = Column(String(4))
    card_exp_month = Column(Integer)
    card_exp_year = Column(Integer)
    card_holder_name = Column(String(255))

    # Bank details (tokenized)
    bank_name = Column(String(100))
    account_type = Column(String(20))
    account_last_four = Column(String(4))
    routing_number_last_four = Column(String(4))

    # Payment processor
    processor = Column(String(50), default="stripe")
    processor_token = Column(String(255))
    processor_customer_id = Column(String(255))

    # Billing address
    billing_address = Column(JSONB)

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True))

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("PortalUser", back_populates="saved_payments")


class PortalPayment(Base):
    """Payments made through the portal"""
    __tablename__ = "portal_payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("portal_users.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)

    # Payment details
    payment_method_id = Column(UUID(as_uuid=True), ForeignKey("saved_payment_methods.id"))
    payment_type = Column(Enum(PaymentMethod), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")

    # Allocation
    statement_ids = Column(ARRAY(UUID(as_uuid=True)))
    encounter_ids = Column(ARRAY(UUID(as_uuid=True)))
    payment_plan_id = Column(UUID(as_uuid=True))

    # Processing
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    processor = Column(String(50))
    processor_transaction_id = Column(String(255))
    processor_response = Column(JSONB)

    # Confirmation
    confirmation_number = Column(String(50))
    receipt_url = Column(String(500))
    receipt_sent = Column(Boolean, default=False)
    receipt_sent_at = Column(DateTime(timezone=True))

    # Timestamps
    initiated_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    failed_at = Column(DateTime(timezone=True))

    # Error handling
    error_code = Column(String(50))
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    # Refund
    refunded = Column(Boolean, default=False)
    refund_amount = Column(Numeric(10, 2))
    refunded_at = Column(DateTime(timezone=True))
    refund_reason = Column(Text)

    # Metadata
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PaymentPlan(Base):
    """Patient payment plans"""
    __tablename__ = "payment_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("portal_users.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)

    # Plan details
    name = Column(String(100))
    total_amount = Column(Numeric(10, 2), nullable=False)
    remaining_amount = Column(Numeric(10, 2), nullable=False)
    monthly_payment = Column(Numeric(10, 2), nullable=False)
    number_of_payments = Column(Integer, nullable=False)
    payments_made = Column(Integer, default=0)

    # Schedule
    start_date = Column(Date, nullable=False)
    next_payment_date = Column(Date)
    payment_day_of_month = Column(Integer)

    # Auto-pay
    auto_pay_enabled = Column(Boolean, default=False)
    payment_method_id = Column(UUID(as_uuid=True), ForeignKey("saved_payment_methods.id"))

    # Interest
    interest_rate = Column(Numeric(5, 2), default=0)
    total_interest = Column(Numeric(10, 2), default=0)

    # Status
    is_active = Column(Boolean, default=True)
    status = Column(String(20), default="active")
    completed_at = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))
    cancellation_reason = Column(Text)

    # Delinquency
    missed_payments = Column(Integer, default=0)
    is_delinquent = Column(Boolean, default=False)
    delinquent_since = Column(Date)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))


# ==================== Prescription Refills ====================

class RefillRequest(Base):
    """Prescription refill requests"""
    __tablename__ = "refill_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("portal_users.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)

    # Prescription reference
    prescription_id = Column(UUID(as_uuid=True), nullable=False)
    medication_name = Column(String(255), nullable=False)
    medication_dosage = Column(String(100))
    medication_instructions = Column(Text)

    # Request details
    quantity_requested = Column(Integer)
    days_supply_requested = Column(Integer)
    notes = Column(Text)
    urgent = Column(Boolean, default=False)

    # Pharmacy
    pharmacy_id = Column(UUID(as_uuid=True))
    pharmacy_name = Column(String(255))
    pharmacy_phone = Column(String(20))
    pharmacy_address = Column(JSONB)
    delivery_requested = Column(Boolean, default=False)
    delivery_address = Column(JSONB)

    # Status
    status = Column(Enum(RefillStatus), default=RefillStatus.REQUESTED)
    status_updated_at = Column(DateTime(timezone=True))
    status_updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Approval
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    denial_reason = Column(Text)
    requires_appointment = Column(Boolean, default=False)

    # Prior authorization
    prior_auth_required = Column(Boolean, default=False)
    prior_auth_status = Column(String(50))
    prior_auth_number = Column(String(100))

    # Processing
    processed_at = Column(DateTime(timezone=True))
    ready_at = Column(DateTime(timezone=True))
    picked_up_at = Column(DateTime(timezone=True))
    shipped_at = Column(DateTime(timezone=True))
    tracking_number = Column(String(100))

    # Cost
    estimated_cost = Column(Numeric(10, 2))
    copay_amount = Column(Numeric(10, 2))
    insurance_coverage = Column(Numeric(10, 2))

    # Proxy context
    requested_via_proxy = Column(Boolean, default=False)
    proxy_user_id = Column(UUID(as_uuid=True), ForeignKey("portal_users.id"))

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("PortalUser", foreign_keys=[user_id], back_populates="refill_requests")


# ==================== Notifications ====================

class PortalNotification(Base):
    """Portal notifications for users"""
    __tablename__ = "portal_notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("portal_users.id"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Notification
    notification_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    icon = Column(String(50))
    action_url = Column(String(500))
    action_text = Column(String(100))

    # Priority
    priority = Column(String(20), default="normal")
    is_urgent = Column(Boolean, default=False)

    # Status
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True))
    is_dismissed = Column(Boolean, default=False)
    dismissed_at = Column(DateTime(timezone=True))

    # Delivery
    channels_sent = Column(ARRAY(String), default=[])
    email_sent = Column(Boolean, default=False)
    email_sent_at = Column(DateTime(timezone=True))
    sms_sent = Column(Boolean, default=False)
    sms_sent_at = Column(DateTime(timezone=True))
    push_sent = Column(Boolean, default=False)
    push_sent_at = Column(DateTime(timezone=True))

    # Reference
    reference_type = Column(String(50))
    reference_id = Column(UUID(as_uuid=True))

    # Expiration
    expires_at = Column(DateTime(timezone=True))

    # Metadata
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("PortalUser", back_populates="notifications")


# ==================== Health Records Access ====================

class RecordAccessLog(Base):
    """Patient health record access tracking"""
    __tablename__ = "record_access_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("portal_users.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)

    # Record info
    record_type = Column(String(50), nullable=False)
    record_id = Column(UUID(as_uuid=True))
    record_ids = Column(ARRAY(UUID(as_uuid=True)))
    record_date_from = Column(Date)
    record_date_to = Column(Date)

    # Access type
    action = Column(String(50), nullable=False)  # view, download, share, print
    access_method = Column(String(50))  # portal, api, export

    # Download/Share details
    download_format = Column(String(20))
    share_recipient = Column(String(255))
    share_method = Column(String(50))
    share_expiry = Column(DateTime(timezone=True))
    share_access_count = Column(Integer, default=0)

    # Proxy context
    accessed_via_proxy = Column(Boolean, default=False)
    proxy_user_id = Column(UUID(as_uuid=True), ForeignKey("portal_users.id"))

    # Context
    ip_address = Column(INET)
    user_agent = Column(String(500))
    session_id = Column(UUID(as_uuid=True), ForeignKey("portal_sessions.id"))

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RecordShareLink(Base):
    """Shareable links for health records"""
    __tablename__ = "record_share_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("portal_users.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)

    # Link
    token = Column(String(255), unique=True, nullable=False)
    share_url = Column(String(500))

    # Content
    record_type = Column(String(50))
    record_ids = Column(ARRAY(UUID(as_uuid=True)))
    include_attachments = Column(Boolean, default=False)

    # Recipient
    recipient_name = Column(String(255))
    recipient_email = Column(String(255))
    recipient_organization = Column(String(255))
    purpose = Column(String(255))

    # Security
    password_protected = Column(Boolean, default=False)
    password_hash = Column(String(255))
    max_access_count = Column(Integer)
    access_count = Column(Integer, default=0)

    # Validity
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)
    revoked_at = Column(DateTime(timezone=True))

    # Notification
    notification_sent = Column(Boolean, default=False)
    notification_sent_at = Column(DateTime(timezone=True))

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_accessed_at = Column(DateTime(timezone=True))


# ==================== Audit & Compliance ====================

class PortalAuditLog(Base):
    """HIPAA-compliant audit log for all portal activities"""
    __tablename__ = "portal_audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("portal_users.id"), index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), index=True)

    # Action
    action = Column(Enum(AuditAction), nullable=False)
    action_category = Column(String(50))
    action_description = Column(Text)

    # Resource
    resource_type = Column(String(50))
    resource_id = Column(UUID(as_uuid=True))
    resource_name = Column(String(255))

    # Details
    details = Column(JSONB, default={})
    changes = Column(JSONB)  # Before/after for updates
    request_body = Column(JSONB)  # Sanitized request

    # Context
    session_id = Column(UUID(as_uuid=True), ForeignKey("portal_sessions.id"))
    ip_address = Column(INET)
    user_agent = Column(String(500))
    device_type = Column(String(50))
    location = Column(JSONB)

    # Proxy context
    is_proxy_action = Column(Boolean, default=False)
    proxy_user_id = Column(UUID(as_uuid=True), ForeignKey("portal_users.id"))
    on_behalf_of_patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))

    # PHI
    contains_phi = Column(Boolean, default=False)
    phi_fields_accessed = Column(ARRAY(String))

    # Result
    success = Column(Boolean, default=True)
    error_code = Column(String(50))
    error_message = Column(Text)

    # Request info
    request_id = Column(String(100))
    request_method = Column(String(10))
    request_path = Column(String(500))
    response_status = Column(Integer)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("PortalUser", foreign_keys=[user_id], back_populates="audit_logs")


# ==================== Identity Verification ====================

class IdentityVerification(Base):
    """Identity verification records"""
    __tablename__ = "identity_verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("portal_users.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)

    # Verification method
    verification_type = Column(Enum(VerificationType), nullable=False)
    verification_method = Column(String(50))

    # Identity matching
    match_fields = Column(JSONB)  # Fields used for matching
    match_score = Column(Float)
    match_threshold = Column(Float, default=0.8)

    # Document verification
    document_type = Column(String(50))  # driver_license, passport, etc.
    document_number_last_four = Column(String(4))
    document_expiry = Column(Date)
    document_verified = Column(Boolean, default=False)

    # Third-party verification
    provider = Column(String(50))
    provider_reference_id = Column(String(255))
    provider_response = Column(JSONB)

    # Status
    status = Column(String(20), default="pending")
    verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True))
    failed_reason = Column(Text)
    attempts = Column(Integer, default=1)

    # Metadata
    ip_address = Column(INET)
    user_agent = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True))


# Alias for compatibility
ChannelAnalyticsModel = None  # Will be imported from omnichannel if needed
