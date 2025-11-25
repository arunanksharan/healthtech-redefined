"""
API Marketplace Models
EPIC-018: Database models for Developer Platform & API Marketplace

Includes:
- Developer organizations and team members
- OAuth applications and credentials
- API keys and rate limits
- Marketplace applications and installations
- App reviews and ratings
- Sandbox environments
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import uuid4
import enum

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, DateTime, ForeignKey,
    Numeric, Index, UniqueConstraint, CheckConstraint, Table
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SQLEnum

from shared.database import Base


# ============================================================================
# Enums
# ============================================================================

class DeveloperRole(str, enum.Enum):
    """Roles within a developer organization"""
    OWNER = "owner"
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class DeveloperStatus(str, enum.Enum):
    """Developer organization status"""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


class AppType(str, enum.Enum):
    """Type of OAuth application"""
    WEB = "web"
    NATIVE = "native"
    SPA = "spa"
    BACKEND = "backend"
    SMART_ON_FHIR = "smart_on_fhir"


class AppStatus(str, enum.Enum):
    """Application status"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    SUSPENDED = "suspended"
    DEPRECATED = "deprecated"


class InstallationStatus(str, enum.Enum):
    """App installation status"""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    UNINSTALLED = "uninstalled"


class SandboxStatus(str, enum.Enum):
    """Sandbox environment status"""
    PROVISIONING = "provisioning"
    ACTIVE = "active"
    RESETTING = "resetting"
    EXPIRED = "expired"
    DELETED = "deleted"


class TokenType(str, enum.Enum):
    """OAuth token type"""
    ACCESS = "access"
    REFRESH = "refresh"
    AUTHORIZATION_CODE = "authorization_code"


class GrantType(str, enum.Enum):
    """OAuth grant types"""
    AUTHORIZATION_CODE = "authorization_code"
    CLIENT_CREDENTIALS = "client_credentials"
    REFRESH_TOKEN = "refresh_token"


class WebhookEventType(str, enum.Enum):
    """Webhook event types"""
    APP_INSTALLED = "app.installed"
    APP_UNINSTALLED = "app.uninstalled"
    APP_AUTHORIZED = "app.authorized"
    APP_REVOKED = "app.revoked"
    SUBSCRIPTION_CREATED = "subscription.created"
    SUBSCRIPTION_UPDATED = "subscription.updated"
    PATIENT_UPDATED = "patient.updated"
    APPOINTMENT_CREATED = "appointment.created"
    APPOINTMENT_UPDATED = "appointment.updated"


class APIKeyStatus(str, enum.Enum):
    """API key status"""
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class AppCategory(str, enum.Enum):
    """Marketplace app categories"""
    CLINICAL = "clinical"
    BILLING = "billing"
    ANALYTICS = "analytics"
    COMMUNICATION = "communication"
    INTEGRATION = "integration"
    AI_ML = "ai_ml"
    TELEHEALTH = "telehealth"
    PATIENT_ENGAGEMENT = "patient_engagement"
    WORKFLOW = "workflow"
    OTHER = "other"


# ============================================================================
# Developer Organization Models
# ============================================================================

class DeveloperOrganization(Base):
    """Developer organization/company"""
    __tablename__ = "developer_organizations"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(200), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False)
    website = Column(String(500))
    description = Column(Text)
    logo_url = Column(String(500))

    # Contact information
    contact_name = Column(String(200))
    contact_email = Column(String(255))
    contact_phone = Column(String(50))

    # Address
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(2), default="US")

    # Verification
    status = Column(SQLEnum(DeveloperStatus), default=DeveloperStatus.PENDING)
    verified_at = Column(DateTime)
    verification_data = Column(JSONB, default={})

    # Agreement
    agreed_to_terms = Column(Boolean, default=False)
    terms_accepted_at = Column(DateTime)
    terms_version = Column(String(20))

    # Settings
    settings = Column(JSONB, default={})
    metadata = Column(JSONB, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    members = relationship("DeveloperMember", back_populates="organization", cascade="all, delete-orphan")
    applications = relationship("OAuthApplication", back_populates="organization", cascade="all, delete-orphan")
    sandboxes = relationship("SandboxEnvironment", back_populates="organization", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_dev_org_status", "status"),
        Index("ix_dev_org_email", "email"),
    )


class DeveloperMember(Base):
    """Team member in a developer organization"""
    __tablename__ = "developer_members"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("developer_organizations.id"), nullable=False)
    user_id = Column(PGUUID(as_uuid=True), nullable=False)  # Links to auth system

    # Member info
    email = Column(String(255), nullable=False)
    name = Column(String(200))
    role = Column(SQLEnum(DeveloperRole), default=DeveloperRole.DEVELOPER)
    is_active = Column(Boolean, default=True)

    # Invitation
    invited_by = Column(PGUUID(as_uuid=True))
    invited_at = Column(DateTime)
    accepted_at = Column(DateTime)
    invitation_token = Column(String(64), unique=True)

    # 2FA
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(64))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime)

    # Relationships
    organization = relationship("DeveloperOrganization", back_populates="members")

    __table_args__ = (
        UniqueConstraint("organization_id", "email", name="uq_dev_member_org_email"),
        Index("ix_dev_member_user", "user_id"),
    )


# ============================================================================
# OAuth Application Models
# ============================================================================

class OAuthApplication(Base):
    """OAuth application registered by developers"""
    __tablename__ = "oauth_applications"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("developer_organizations.id"), nullable=False)

    # Basic info
    name = Column(String(200), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    app_type = Column(SQLEnum(AppType), default=AppType.WEB)
    status = Column(SQLEnum(AppStatus), default=AppStatus.DRAFT)

    # OAuth credentials
    client_id = Column(String(64), unique=True, nullable=False, index=True)
    client_secret_hash = Column(String(128))  # Hashed secret
    client_secret_prefix = Column(String(8))  # First 8 chars for identification

    # OAuth configuration
    redirect_uris = Column(ARRAY(String), default=[])
    allowed_grant_types = Column(ARRAY(String), default=["authorization_code"])
    allowed_scopes = Column(ARRAY(String), default=[])
    default_scopes = Column(ARRAY(String), default=[])

    # SMART on FHIR
    is_smart_on_fhir = Column(Boolean, default=False)
    launch_uri = Column(String(500))
    smart_capabilities = Column(JSONB, default={})

    # URLs
    homepage_url = Column(String(500))
    privacy_policy_url = Column(String(500))
    terms_of_service_url = Column(String(500))
    support_url = Column(String(500))

    # Branding
    logo_url = Column(String(500))
    icon_url = Column(String(500))
    primary_color = Column(String(7))

    # Token settings
    access_token_ttl = Column(Integer, default=3600)  # 1 hour
    refresh_token_ttl = Column(Integer, default=2592000)  # 30 days
    require_pkce = Column(Boolean, default=True)

    # Security
    allowed_origins = Column(ARRAY(String), default=[])
    ip_allowlist = Column(ARRAY(String), default=[])

    # Settings
    settings = Column(JSONB, default={})
    metadata = Column(JSONB, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = relationship("DeveloperOrganization", back_populates="applications")
    api_keys = relationship("APIKey", back_populates="application", cascade="all, delete-orphan")
    tokens = relationship("OAuthToken", back_populates="application", cascade="all, delete-orphan")
    webhooks = relationship("WebhookEndpoint", back_populates="application", cascade="all, delete-orphan")
    installations = relationship("AppInstallation", back_populates="application")

    __table_args__ = (
        Index("ix_oauth_app_org", "organization_id"),
        Index("ix_oauth_app_status", "status"),
    )


class APIKey(Base):
    """API keys for application authentication"""
    __tablename__ = "api_keys"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    application_id = Column(PGUUID(as_uuid=True), ForeignKey("oauth_applications.id"), nullable=False)

    # Key details
    name = Column(String(100), nullable=False)
    key_prefix = Column(String(8), nullable=False)  # prm_live_
    key_hash = Column(String(128), nullable=False, unique=True)
    status = Column(SQLEnum(APIKeyStatus), default=APIKeyStatus.ACTIVE)

    # Permissions
    scopes = Column(ARRAY(String), default=[])
    is_test_key = Column(Boolean, default=False)

    # Usage limits
    rate_limit_per_minute = Column(Integer, default=60)
    rate_limit_per_day = Column(Integer, default=10000)
    monthly_quota = Column(Integer)

    # Security
    ip_allowlist = Column(ARRAY(String), default=[])
    allowed_referrers = Column(ARRAY(String), default=[])

    # Expiration
    expires_at = Column(DateTime)

    # Usage tracking
    last_used_at = Column(DateTime)
    last_used_ip = Column(String(45))
    total_requests = Column(Integer, default=0)

    # Created by
    created_by = Column(PGUUID(as_uuid=True))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime)

    # Relationships
    application = relationship("OAuthApplication", back_populates="api_keys")

    __table_args__ = (
        Index("ix_api_key_app", "application_id"),
        Index("ix_api_key_prefix", "key_prefix"),
    )


class OAuthToken(Base):
    """OAuth tokens (access, refresh, authorization codes)"""
    __tablename__ = "oauth_tokens"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    application_id = Column(PGUUID(as_uuid=True), ForeignKey("oauth_applications.id"), nullable=False)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    # Token details
    token_type = Column(SQLEnum(TokenType), nullable=False)
    token_hash = Column(String(128), nullable=False, unique=True)
    token_prefix = Column(String(8))

    # User context
    user_id = Column(PGUUID(as_uuid=True))  # For user-based tokens
    patient_id = Column(PGUUID(as_uuid=True))  # For SMART patient context

    # Grant info
    grant_type = Column(SQLEnum(GrantType))
    scopes = Column(ARRAY(String), default=[])

    # SMART context
    launch_context = Column(JSONB, default={})  # patient, encounter, user

    # Token chain
    parent_token_id = Column(PGUUID(as_uuid=True))  # For refresh token chain

    # Expiration
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime)

    # PKCE
    code_challenge = Column(String(128))
    code_challenge_method = Column(String(10))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime)

    # Relationships
    application = relationship("OAuthApplication", back_populates="tokens")

    __table_args__ = (
        Index("ix_oauth_token_app", "application_id"),
        Index("ix_oauth_token_user", "user_id"),
        Index("ix_oauth_token_expires", "expires_at"),
    )


class OAuthConsent(Base):
    """User consent records for OAuth applications"""
    __tablename__ = "oauth_consents"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    application_id = Column(PGUUID(as_uuid=True), ForeignKey("oauth_applications.id"), nullable=False)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(PGUUID(as_uuid=True), nullable=False)
    patient_id = Column(PGUUID(as_uuid=True))  # If patient-specific consent

    # Consent details
    granted_scopes = Column(ARRAY(String), default=[])
    is_active = Column(Boolean, default=True)

    # Timestamps
    granted_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    revoked_at = Column(DateTime)

    __table_args__ = (
        UniqueConstraint("application_id", "tenant_id", "user_id", "patient_id",
                         name="uq_oauth_consent_app_user"),
        Index("ix_oauth_consent_app", "application_id"),
        Index("ix_oauth_consent_user", "user_id"),
    )


# ============================================================================
# Webhook Models
# ============================================================================

class WebhookEndpoint(Base):
    """Webhook endpoints for applications"""
    __tablename__ = "webhook_endpoints"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    application_id = Column(PGUUID(as_uuid=True), ForeignKey("oauth_applications.id"), nullable=False)

    # Endpoint config
    url = Column(String(500), nullable=False)
    description = Column(String(200))
    is_active = Column(Boolean, default=True)

    # Events
    subscribed_events = Column(ARRAY(String), default=[])

    # Security
    secret = Column(String(64))  # For signature verification
    secret_hash = Column(String(128))

    # Delivery settings
    timeout_seconds = Column(Integer, default=30)
    max_retries = Column(Integer, default=3)

    # Stats
    total_deliveries = Column(Integer, default=0)
    successful_deliveries = Column(Integer, default=0)
    failed_deliveries = Column(Integer, default=0)
    last_delivery_at = Column(DateTime)
    last_status_code = Column(Integer)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    application = relationship("OAuthApplication", back_populates="webhooks")

    __table_args__ = (
        Index("ix_webhook_app", "application_id"),
    )


class WebhookDelivery(Base):
    """Webhook delivery attempts"""
    __tablename__ = "webhook_deliveries"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    endpoint_id = Column(PGUUID(as_uuid=True), ForeignKey("webhook_endpoints.id"), nullable=False)

    # Event details
    event_type = Column(String(50), nullable=False)
    event_id = Column(String(64), nullable=False)
    payload = Column(JSONB, nullable=False)

    # Delivery attempt
    attempt_number = Column(Integer, default=1)
    status_code = Column(Integer)
    response_body = Column(Text)
    response_time_ms = Column(Integer)

    # Result
    is_successful = Column(Boolean)
    error_message = Column(Text)

    # Timestamps
    scheduled_at = Column(DateTime)
    delivered_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_webhook_delivery_endpoint", "endpoint_id"),
        Index("ix_webhook_delivery_event", "event_id"),
    )


# ============================================================================
# Marketplace Models
# ============================================================================

class MarketplaceApp(Base):
    """Published application in marketplace"""
    __tablename__ = "marketplace_apps"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    application_id = Column(PGUUID(as_uuid=True), ForeignKey("oauth_applications.id"), nullable=False, unique=True)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("developer_organizations.id"), nullable=False)

    # Display info
    display_name = Column(String(200), nullable=False)
    short_description = Column(String(300), nullable=False)
    long_description = Column(Text)
    tagline = Column(String(100))

    # Categorization
    category = Column(SQLEnum(AppCategory), default=AppCategory.OTHER)
    subcategory = Column(String(50))
    tags = Column(ARRAY(String), default=[])

    # Media
    icon_url = Column(String(500))
    banner_url = Column(String(500))
    screenshots = Column(JSONB, default=[])  # [{url, caption}]
    video_url = Column(String(500))

    # Documentation
    documentation_url = Column(String(500))
    changelog_url = Column(String(500))
    support_email = Column(String(255))

    # Pricing
    is_free = Column(Boolean, default=True)
    pricing_model = Column(String(50))  # free, flat, per_user, usage_based
    price_monthly = Column(Numeric(10, 2))
    price_annual = Column(Numeric(10, 2))
    pricing_details = Column(JSONB, default={})

    # Stats
    install_count = Column(Integer, default=0)
    average_rating = Column(Numeric(2, 1), default=0)
    review_count = Column(Integer, default=0)

    # Visibility
    is_featured = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    is_visible = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    # Requirements
    required_scopes = Column(ARRAY(String), default=[])
    optional_scopes = Column(ARRAY(String), default=[])
    min_platform_version = Column(String(20))

    # Version
    current_version = Column(String(20))
    latest_release_at = Column(DateTime)

    # Timestamps
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    application = relationship("OAuthApplication")
    organization = relationship("DeveloperOrganization")
    versions = relationship("AppVersion", back_populates="marketplace_app", cascade="all, delete-orphan")
    reviews = relationship("AppReview", back_populates="marketplace_app", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_marketplace_app_category", "category"),
        Index("ix_marketplace_app_featured", "is_featured"),
        Index("ix_marketplace_app_rating", "average_rating"),
    )


class AppVersion(Base):
    """Version history for marketplace apps"""
    __tablename__ = "app_versions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    marketplace_app_id = Column(PGUUID(as_uuid=True), ForeignKey("marketplace_apps.id"), nullable=False)

    # Version info
    version = Column(String(20), nullable=False)
    version_name = Column(String(100))
    release_notes = Column(Text)

    # Status
    status = Column(SQLEnum(AppStatus), default=AppStatus.DRAFT)

    # Changes
    scope_changes = Column(JSONB, default={})  # added, removed scopes
    breaking_changes = Column(Boolean, default=False)

    # Review
    submitted_at = Column(DateTime)
    reviewed_at = Column(DateTime)
    reviewed_by = Column(PGUUID(as_uuid=True))
    review_notes = Column(Text)

    # Rollout
    rollout_percentage = Column(Integer, default=100)
    is_current = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime)

    # Relationships
    marketplace_app = relationship("MarketplaceApp", back_populates="versions")

    __table_args__ = (
        UniqueConstraint("marketplace_app_id", "version", name="uq_app_version"),
        Index("ix_app_version_app", "marketplace_app_id"),
    )


class AppInstallation(Base):
    """App installations by tenants"""
    __tablename__ = "app_installations"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    application_id = Column(PGUUID(as_uuid=True), ForeignKey("oauth_applications.id"), nullable=False)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    # Status
    status = Column(SQLEnum(InstallationStatus), default=InstallationStatus.PENDING)

    # Permissions
    granted_scopes = Column(ARRAY(String), default=[])
    configured_scopes = Column(ARRAY(String), default=[])

    # Installation context
    installed_by = Column(PGUUID(as_uuid=True))
    installed_version = Column(String(20))

    # Configuration
    configuration = Column(JSONB, default={})

    # Usage stats
    last_used_at = Column(DateTime)
    api_calls_count = Column(Integer, default=0)

    # Timestamps
    installed_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    uninstalled_at = Column(DateTime)

    # Relationships
    application = relationship("OAuthApplication", back_populates="installations")

    __table_args__ = (
        UniqueConstraint("application_id", "tenant_id", name="uq_app_installation_tenant"),
        Index("ix_installation_status", "status"),
    )


class AppReview(Base):
    """User reviews for marketplace apps"""
    __tablename__ = "app_reviews"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    marketplace_app_id = Column(PGUUID(as_uuid=True), ForeignKey("marketplace_apps.id"), nullable=False)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(PGUUID(as_uuid=True), nullable=False)

    # Review content
    rating = Column(Integer, nullable=False)  # 1-5
    title = Column(String(200))
    body = Column(Text)

    # Verification
    is_verified_purchase = Column(Boolean, default=False)
    installation_id = Column(PGUUID(as_uuid=True))

    # Moderation
    is_visible = Column(Boolean, default=True)
    is_flagged = Column(Boolean, default=False)
    moderation_notes = Column(Text)

    # Response from publisher
    publisher_response = Column(Text)
    publisher_responded_at = Column(DateTime)

    # Stats
    helpful_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    marketplace_app = relationship("MarketplaceApp", back_populates="reviews")

    __table_args__ = (
        UniqueConstraint("marketplace_app_id", "tenant_id", "user_id", name="uq_app_review_user"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_rating_range"),
        Index("ix_app_review_app", "marketplace_app_id"),
    )


# ============================================================================
# Sandbox Models
# ============================================================================

class SandboxEnvironment(Base):
    """Sandbox environment for developers"""
    __tablename__ = "sandbox_environments"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("developer_organizations.id"), nullable=False)

    # Sandbox details
    name = Column(String(100), default="Default Sandbox")
    status = Column(SQLEnum(SandboxStatus), default=SandboxStatus.PROVISIONING)

    # Virtual tenant
    sandbox_tenant_id = Column(PGUUID(as_uuid=True), unique=True)

    # Test data
    has_sample_data = Column(Boolean, default=True)
    sample_data_config = Column(JSONB, default={})

    # Credentials
    test_api_key_prefix = Column(String(8))
    test_api_key_hash = Column(String(128))

    # Limits
    max_api_calls_per_day = Column(Integer, default=1000)
    max_records = Column(Integer, default=100)

    # Usage
    api_calls_today = Column(Integer, default=0)
    total_api_calls = Column(Integer, default=0)
    last_reset_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    last_used_at = Column(DateTime)

    # Relationships
    organization = relationship("DeveloperOrganization", back_populates="sandboxes")

    __table_args__ = (
        Index("ix_sandbox_org", "organization_id"),
        Index("ix_sandbox_status", "status"),
    )


# ============================================================================
# API Usage Models
# ============================================================================

class APIUsageLog(Base):
    """API usage tracking for rate limiting and analytics"""
    __tablename__ = "api_usage_logs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    application_id = Column(PGUUID(as_uuid=True), index=True)
    api_key_id = Column(PGUUID(as_uuid=True), index=True)
    tenant_id = Column(PGUUID(as_uuid=True), index=True)

    # Request details
    endpoint = Column(String(200), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer)

    # Performance
    response_time_ms = Column(Integer)

    # Client info
    client_ip = Column(String(45))
    user_agent = Column(String(500))

    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_api_usage_app_time", "application_id", "timestamp"),
    )


class RateLimitBucket(Base):
    """Rate limit tracking buckets"""
    __tablename__ = "rate_limit_buckets"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Identifier
    bucket_key = Column(String(200), nullable=False, unique=True, index=True)

    # Limits
    request_count = Column(Integer, default=0)
    limit_per_window = Column(Integer, nullable=False)
    window_size_seconds = Column(Integer, nullable=False)

    # Window
    window_start = Column(DateTime, nullable=False)
    window_end = Column(DateTime, nullable=False)

    # Updated
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# Audit Models
# ============================================================================

class DeveloperAuditLog(Base):
    """Audit log for developer platform activities"""
    __tablename__ = "developer_audit_logs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), index=True)
    user_id = Column(PGUUID(as_uuid=True), index=True)
    application_id = Column(PGUUID(as_uuid=True), index=True)

    # Action
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(PGUUID(as_uuid=True))

    # Details
    details = Column(JSONB, default={})
    ip_address = Column(String(45))
    user_agent = Column(String(500))

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_dev_audit_org_time", "organization_id", "created_at"),
    )
