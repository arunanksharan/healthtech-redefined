"""
API Marketplace Schemas
EPIC-018: Pydantic schemas for Developer Platform & API Marketplace
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, field_validator, HttpUrl, EmailStr


# ============================================================================
# Enum Schemas
# ============================================================================

class DeveloperRoleSchema(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class DeveloperStatusSchema(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


class AppTypeSchema(str, Enum):
    WEB = "web"
    NATIVE = "native"
    SPA = "spa"
    BACKEND = "backend"
    SMART_ON_FHIR = "smart_on_fhir"


class AppStatusSchema(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    SUSPENDED = "suspended"
    DEPRECATED = "deprecated"


class InstallationStatusSchema(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    UNINSTALLED = "uninstalled"


class AppCategorySchema(str, Enum):
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


class GrantTypeSchema(str, Enum):
    AUTHORIZATION_CODE = "authorization_code"
    CLIENT_CREDENTIALS = "client_credentials"
    REFRESH_TOKEN = "refresh_token"


class TokenTypeSchema(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


# ============================================================================
# Developer Organization Schemas
# ============================================================================

class DeveloperOrgCreate(BaseModel):
    """Create developer organization"""
    name: str = Field(..., min_length=2, max_length=200)
    email: EmailStr
    website: Optional[str] = None
    description: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "US"


class DeveloperOrgUpdate(BaseModel):
    """Update developer organization"""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    website: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class DeveloperOrgResponse(BaseModel):
    """Developer organization response"""
    id: UUID
    name: str
    slug: str
    email: str
    website: Optional[str]
    description: Optional[str]
    logo_url: Optional[str]
    contact_name: Optional[str]
    status: str
    verified_at: Optional[datetime]
    agreed_to_terms: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DeveloperOrgListResponse(BaseModel):
    """List of developer organizations"""
    items: List[DeveloperOrgResponse]
    total: int


# ============================================================================
# Team Member Schemas
# ============================================================================

class TeamMemberInvite(BaseModel):
    """Invite team member"""
    email: EmailStr
    name: Optional[str] = None
    role: DeveloperRoleSchema = DeveloperRoleSchema.DEVELOPER


class TeamMemberUpdate(BaseModel):
    """Update team member"""
    name: Optional[str] = None
    role: Optional[DeveloperRoleSchema] = None
    is_active: Optional[bool] = None


class TeamMemberResponse(BaseModel):
    """Team member response"""
    id: UUID
    organization_id: UUID
    user_id: Optional[UUID]
    email: str
    name: Optional[str]
    role: str
    is_active: bool
    invited_at: Optional[datetime]
    accepted_at: Optional[datetime]
    last_login_at: Optional[datetime]
    two_factor_enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TeamMemberListResponse(BaseModel):
    """List of team members"""
    members: List[TeamMemberResponse]
    total: int


# ============================================================================
# OAuth Application Schemas
# ============================================================================

class OAuthAppCreate(BaseModel):
    """Create OAuth application"""
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    app_type: AppTypeSchema = AppTypeSchema.WEB
    redirect_uris: List[str] = Field(default=[])
    homepage_url: Optional[str] = None
    privacy_policy_url: Optional[str] = None
    terms_of_service_url: Optional[str] = None
    support_url: Optional[str] = None
    logo_url: Optional[str] = None
    is_smart_on_fhir: bool = False
    launch_uri: Optional[str] = None
    allowed_scopes: List[str] = Field(default=[])


class OAuthAppUpdate(BaseModel):
    """Update OAuth application"""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    redirect_uris: Optional[List[str]] = None
    homepage_url: Optional[str] = None
    privacy_policy_url: Optional[str] = None
    terms_of_service_url: Optional[str] = None
    support_url: Optional[str] = None
    logo_url: Optional[str] = None
    icon_url: Optional[str] = None
    primary_color: Optional[str] = None
    access_token_ttl: Optional[int] = None
    refresh_token_ttl: Optional[int] = None
    require_pkce: Optional[bool] = None
    allowed_origins: Optional[List[str]] = None
    ip_allowlist: Optional[List[str]] = None
    settings: Optional[Dict[str, Any]] = None


class OAuthAppResponse(BaseModel):
    """OAuth application response"""
    id: UUID
    organization_id: UUID
    name: str
    slug: str
    description: Optional[str]
    app_type: str
    status: str
    client_id: str
    redirect_uris: List[str]
    allowed_grant_types: List[str]
    allowed_scopes: List[str]
    default_scopes: List[str]
    is_smart_on_fhir: bool
    launch_uri: Optional[str]
    homepage_url: Optional[str]
    logo_url: Optional[str]
    icon_url: Optional[str]
    access_token_ttl: int
    refresh_token_ttl: int
    require_pkce: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class OAuthAppWithSecret(OAuthAppResponse):
    """OAuth app response including client secret (only shown once)"""
    client_secret: str


class OAuthAppListResponse(BaseModel):
    """List of OAuth applications"""
    items: List[OAuthAppResponse]
    total: int


class ClientSecretRotateResponse(BaseModel):
    """Response after rotating client secret"""
    client_id: str
    client_secret: str
    client_secret_prefix: str
    rotated_at: datetime


# ============================================================================
# API Key Schemas
# ============================================================================

class APIKeyCreate(BaseModel):
    """Create API key"""
    name: str = Field(..., max_length=100)
    scopes: List[str] = Field(default=[])
    is_test_key: bool = False
    rate_limit_per_minute: int = 60
    rate_limit_per_day: int = 10000
    monthly_quota: Optional[int] = None
    ip_allowlist: List[str] = Field(default=[])
    expires_at: Optional[datetime] = None


class APIKeyResponse(BaseModel):
    """API key response"""
    id: UUID
    application_id: UUID
    name: str
    key_prefix: str
    status: str
    scopes: List[str]
    is_test_key: bool
    rate_limit_per_minute: int
    rate_limit_per_day: int
    monthly_quota: Optional[int]
    last_used_at: Optional[datetime]
    total_requests: int
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class APIKeyWithSecret(APIKeyResponse):
    """API key response with secret (only shown once)"""
    key: str


class APIKeyListResponse(BaseModel):
    """List of API keys"""
    items: List[APIKeyResponse]
    total: int


# ============================================================================
# OAuth Authorization Schemas
# ============================================================================

class AuthorizationRequest(BaseModel):
    """OAuth authorization request"""
    response_type: str = "code"
    client_id: str
    redirect_uri: str
    scope: Optional[str] = None
    state: Optional[str] = None
    code_challenge: Optional[str] = None
    code_challenge_method: Optional[str] = None
    # SMART on FHIR
    aud: Optional[str] = None  # FHIR server URL
    launch: Optional[str] = None  # EHR launch token


class AuthorizationResponse(BaseModel):
    """OAuth authorization response"""
    code: str
    state: Optional[str]
    redirect_uri: str


class TokenRequest(BaseModel):
    """OAuth token request"""
    grant_type: GrantTypeSchema
    client_id: str
    client_secret: Optional[str] = None
    code: Optional[str] = None
    redirect_uri: Optional[str] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    code_verifier: Optional[str] = None


class TokenResponse(BaseModel):
    """OAuth token response"""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    scope: str
    # SMART on FHIR context
    patient: Optional[str] = None
    encounter: Optional[str] = None
    id_token: Optional[str] = None


class TokenIntrospectionRequest(BaseModel):
    """Token introspection request"""
    token: str
    token_type_hint: Optional[str] = None


class TokenIntrospectionResponse(BaseModel):
    """Token introspection response"""
    active: bool
    scope: Optional[str] = None
    client_id: Optional[str] = None
    username: Optional[str] = None
    exp: Optional[int] = None
    iat: Optional[int] = None
    sub: Optional[str] = None
    aud: Optional[str] = None
    iss: Optional[str] = None
    # Custom claims
    tenant_id: Optional[str] = None
    patient_id: Optional[str] = None


class TokenRevocationRequest(BaseModel):
    """Token revocation request"""
    token: str
    token_type_hint: Optional[str] = None


# ============================================================================
# Consent Schemas
# ============================================================================

class ConsentGrant(BaseModel):
    """Grant consent to application"""
    scopes: List[str]
    patient_id: Optional[UUID] = None


class ConsentResponse(BaseModel):
    """Consent response"""
    id: UUID
    application_id: UUID
    application_name: str
    tenant_id: UUID
    user_id: UUID
    patient_id: Optional[UUID]
    granted_scopes: List[str]
    is_active: bool
    granted_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class ConsentListResponse(BaseModel):
    """List of consents"""
    items: List[ConsentResponse]
    total: int


# ============================================================================
# Webhook Schemas
# ============================================================================

class WebhookCreate(BaseModel):
    """Create webhook endpoint"""
    url: str
    description: Optional[str] = None
    subscribed_events: List[str] = Field(default=[])
    timeout_seconds: int = 30
    max_retries: int = 3


class WebhookUpdate(BaseModel):
    """Update webhook endpoint"""
    url: Optional[str] = None
    description: Optional[str] = None
    subscribed_events: Optional[List[str]] = None
    is_active: Optional[bool] = None
    timeout_seconds: Optional[int] = None
    max_retries: Optional[int] = None


class WebhookResponse(BaseModel):
    """Webhook endpoint response"""
    id: UUID
    application_id: UUID
    url: str
    description: Optional[str]
    is_active: bool
    subscribed_events: List[str]
    timeout_seconds: int
    max_retries: int
    total_deliveries: int
    successful_deliveries: int
    failed_deliveries: int
    last_delivery_at: Optional[datetime]
    last_status_code: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class WebhookSecretResponse(BaseModel):
    """Webhook with secret (only shown once)"""
    id: UUID
    secret: str


class WebhookDeliveryResponse(BaseModel):
    """Webhook delivery response"""
    id: UUID
    endpoint_id: UUID
    event_type: str
    event_id: str
    attempt_number: int
    status_code: Optional[int]
    response_time_ms: Optional[int]
    is_successful: Optional[bool]
    error_message: Optional[str]
    delivered_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Marketplace App Schemas
# ============================================================================

class MarketplaceAppCreate(BaseModel):
    """Create marketplace app listing"""
    application_id: UUID
    display_name: str = Field(..., max_length=200)
    short_description: str = Field(..., max_length=300)
    long_description: Optional[str] = None
    tagline: Optional[str] = Field(None, max_length=100)
    category: AppCategorySchema = AppCategorySchema.OTHER
    subcategory: Optional[str] = None
    tags: List[str] = Field(default=[])
    icon_url: Optional[str] = None
    banner_url: Optional[str] = None
    screenshots: List[Dict[str, str]] = Field(default=[])
    video_url: Optional[str] = None
    documentation_url: Optional[str] = None
    changelog_url: Optional[str] = None
    support_email: Optional[EmailStr] = None
    is_free: bool = True
    pricing_model: Optional[str] = None
    price_monthly: Optional[Decimal] = None
    price_annual: Optional[Decimal] = None
    pricing_details: Optional[Dict[str, Any]] = None
    required_scopes: List[str] = Field(default=[])
    optional_scopes: List[str] = Field(default=[])


class MarketplaceAppUpdate(BaseModel):
    """Update marketplace app listing"""
    display_name: Optional[str] = Field(None, max_length=200)
    short_description: Optional[str] = Field(None, max_length=300)
    long_description: Optional[str] = None
    tagline: Optional[str] = None
    category: Optional[AppCategorySchema] = None
    subcategory: Optional[str] = None
    tags: Optional[List[str]] = None
    icon_url: Optional[str] = None
    banner_url: Optional[str] = None
    screenshots: Optional[List[Dict[str, str]]] = None
    video_url: Optional[str] = None
    documentation_url: Optional[str] = None
    support_email: Optional[EmailStr] = None
    pricing_model: Optional[str] = None
    price_monthly: Optional[Decimal] = None
    price_annual: Optional[Decimal] = None
    pricing_details: Optional[Dict[str, Any]] = None
    required_scopes: Optional[List[str]] = None
    optional_scopes: Optional[List[str]] = None


class MarketplaceAppResponse(BaseModel):
    """Marketplace app response"""
    id: UUID
    application_id: UUID
    organization_id: UUID
    display_name: str
    short_description: str
    long_description: Optional[str]
    tagline: Optional[str]
    category: str
    subcategory: Optional[str]
    tags: List[str]
    icon_url: Optional[str]
    banner_url: Optional[str]
    screenshots: List[Dict[str, Any]]
    video_url: Optional[str]
    documentation_url: Optional[str]
    support_email: Optional[str]
    is_free: bool
    pricing_model: Optional[str]
    price_monthly: Optional[float]
    price_annual: Optional[float]
    install_count: int
    average_rating: float
    review_count: int
    is_featured: bool
    is_verified: bool
    current_version: Optional[str]
    required_scopes: List[str]
    optional_scopes: List[str]
    published_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class MarketplaceAppListResponse(BaseModel):
    """List of marketplace apps"""
    items: List[MarketplaceAppResponse]
    total: int
    categories: Dict[str, int]


class MarketplaceSearchParams(BaseModel):
    """Marketplace search parameters"""
    query: Optional[str] = None
    category: Optional[AppCategorySchema] = None
    is_free: Optional[bool] = None
    is_featured: Optional[bool] = None
    min_rating: Optional[float] = None
    sort_by: str = "popularity"  # popularity, rating, newest, name
    skip: int = 0
    limit: int = 20


# ============================================================================
# App Version Schemas
# ============================================================================

class AppVersionCreate(BaseModel):
    """Create app version"""
    version: str = Field(..., max_length=20)
    version_name: Optional[str] = None
    release_notes: Optional[str] = None
    scope_changes: Optional[Dict[str, List[str]]] = None
    breaking_changes: bool = False


class AppVersionResponse(BaseModel):
    """App version response"""
    id: UUID
    marketplace_app_id: UUID
    version: str
    version_name: Optional[str]
    release_notes: Optional[str]
    status: str
    scope_changes: Dict[str, Any]
    breaking_changes: bool
    rollout_percentage: int
    is_current: bool
    submitted_at: Optional[datetime]
    reviewed_at: Optional[datetime]
    published_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# App Installation Schemas
# ============================================================================

class AppInstallRequest(BaseModel):
    """Request to install an app"""
    application_id: UUID
    scopes: List[str] = Field(default=[])
    configuration: Optional[Dict[str, Any]] = None


class AppInstallResponse(BaseModel):
    """App installation response"""
    id: UUID
    application_id: UUID
    tenant_id: UUID
    status: str
    granted_scopes: List[str]
    configured_scopes: List[str]
    installed_by: Optional[UUID]
    installed_version: Optional[str]
    configuration: Dict[str, Any]
    last_used_at: Optional[datetime]
    api_calls_count: int
    installed_at: datetime

    class Config:
        from_attributes = True


class AppInstallListResponse(BaseModel):
    """List of app installations"""
    items: List[AppInstallResponse]
    total: int


# ============================================================================
# App Review Schemas
# ============================================================================

class AppReviewCreate(BaseModel):
    """Create app review"""
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = Field(None, max_length=200)
    body: Optional[str] = None


class AppReviewUpdate(BaseModel):
    """Update app review"""
    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = None
    body: Optional[str] = None


class AppReviewResponse(BaseModel):
    """App review response"""
    id: UUID
    marketplace_app_id: UUID
    tenant_id: UUID
    user_id: UUID
    rating: int
    title: Optional[str]
    body: Optional[str]
    is_verified_purchase: bool
    publisher_response: Optional[str]
    publisher_responded_at: Optional[datetime]
    helpful_count: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class AppReviewListResponse(BaseModel):
    """List of app reviews"""
    items: List[AppReviewResponse]
    total: int
    average_rating: float
    rating_distribution: Dict[int, int]


class PublisherReviewResponse(BaseModel):
    """Publisher response to review"""
    response: str


# ============================================================================
# Sandbox Schemas
# ============================================================================

class SandboxCreate(BaseModel):
    """Create sandbox environment"""
    name: str = Field(default="Default Sandbox", max_length=100)
    has_sample_data: bool = True
    sample_data_config: Optional[Dict[str, Any]] = None


class SandboxResponse(BaseModel):
    """Sandbox environment response"""
    id: UUID
    organization_id: UUID
    name: str
    status: str
    sandbox_tenant_id: Optional[UUID]
    has_sample_data: bool
    max_api_calls_per_day: int
    max_records: int
    api_calls_today: int
    total_api_calls: int
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]

    class Config:
        from_attributes = True


class SandboxWithCredentials(SandboxResponse):
    """Sandbox with test credentials (only shown once)"""
    test_api_key: str


class SandboxResetResponse(BaseModel):
    """Sandbox reset response"""
    id: UUID
    status: str
    reset_at: datetime
    new_test_api_key: Optional[str]


# ============================================================================
# API Usage Schemas
# ============================================================================

class APIUsageStats(BaseModel):
    """API usage statistics"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    requests_by_endpoint: Dict[str, int]
    requests_by_status: Dict[int, int]
    requests_by_hour: List[Dict[str, Any]]


class APIUsageSummary(BaseModel):
    """API usage summary for billing"""
    period_start: datetime
    period_end: datetime
    total_api_calls: int
    included_calls: int
    overage_calls: int
    estimated_cost: float


class RateLimitStatus(BaseModel):
    """Rate limit status"""
    limit: int
    remaining: int
    reset_at: datetime
    retry_after_seconds: Optional[int]


# ============================================================================
# SMART on FHIR Schemas
# ============================================================================

class SMARTConfiguration(BaseModel):
    """SMART on FHIR well-known configuration"""
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    token_endpoint_auth_methods_supported: List[str]
    registration_endpoint: Optional[str]
    scopes_supported: List[str]
    response_types_supported: List[str]
    capabilities: List[str]
    code_challenge_methods_supported: List[str]


class SMARTLaunchContext(BaseModel):
    """SMART launch context"""
    patient: Optional[str] = None
    encounter: Optional[str] = None
    user: Optional[str] = None
    fhirContext: Optional[List[Dict[str, str]]] = None


# ============================================================================
# Developer Dashboard Schemas
# ============================================================================

class DeveloperDashboard(BaseModel):
    """Developer dashboard data"""
    organization: DeveloperOrgResponse
    applications: List[OAuthAppResponse]
    total_api_calls_today: int
    total_api_calls_month: int
    active_installations: int
    sandbox_status: Optional[str]
    recent_activity: List[Dict[str, Any]]


class DeveloperStats(BaseModel):
    """Developer statistics"""
    total_applications: int
    total_api_keys: int
    total_installations: int
    total_api_calls: int
    api_calls_trend: List[Dict[str, Any]]
    top_endpoints: List[Dict[str, Any]]
    error_rate: float


# ============================================================================
# Audit Log Schemas
# ============================================================================

class AuditLogResponse(BaseModel):
    """Audit log entry response"""
    id: UUID
    organization_id: Optional[UUID]
    user_id: Optional[UUID]
    application_id: Optional[UUID]
    action: str
    entity_type: Optional[str]
    entity_id: Optional[UUID]
    details: Dict[str, Any]
    ip_address: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """List of audit logs"""
    items: List[AuditLogResponse]
    total: int
