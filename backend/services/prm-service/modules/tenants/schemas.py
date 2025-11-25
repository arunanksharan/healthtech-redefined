"""
Tenant Management Schemas

EPIC-004: Multi-Tenancy Implementation
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, EmailStr, Field, validator


class TenantTier(str, Enum):
    """Tenant subscription tiers."""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class TenantStatus(str, Enum):
    """Tenant status."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    CANCELLED = "cancelled"
    PENDING = "pending"


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================


class TenantSignupRequest(BaseModel):
    """Schema for new tenant signup."""
    organization_name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100, regex="^[a-z0-9-]+$")
    admin_email: EmailStr
    admin_name: str = Field(..., min_length=2, max_length=255)
    admin_password: str = Field(..., min_length=8, max_length=128)
    phone: Optional[str] = None
    country: str = "US"
    timezone: str = "UTC"
    tier: TenantTier = TenantTier.FREE
    accept_terms: bool = Field(..., description="Must accept terms of service")

    @validator("accept_terms")
    def must_accept_terms(cls, v):
        if not v:
            raise ValueError("You must accept the terms of service")
        return v


class TenantCreateRequest(BaseModel):
    """Schema for creating a tenant (admin use)."""
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100, regex="^[a-z0-9-]+$")
    owner_email: EmailStr
    owner_name: str = Field(..., min_length=2, max_length=255)
    phone: Optional[str] = None
    address: Optional[str] = None
    country: str = "US"
    timezone: str = "UTC"
    tier: TenantTier = TenantTier.FREE


class TenantUpdateRequest(BaseModel):
    """Schema for updating a tenant."""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    owner_email: Optional[EmailStr] = None
    owner_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None


class TenantSettingsUpdate(BaseModel):
    """Schema for updating tenant settings."""
    timezone: Optional[str] = None
    date_format: Optional[str] = None
    time_format: Optional[str] = None
    language: Optional[str] = None
    currency: Optional[str] = None
    appointment_duration_minutes: Optional[int] = Field(None, ge=5, le=480)
    enable_reminders: Optional[bool] = None
    reminder_hours_before: Optional[int] = Field(None, ge=1, le=168)
    enable_waitlist: Optional[bool] = None
    enable_online_booking: Optional[bool] = None
    require_payment_upfront: Optional[bool] = None
    hipaa_mode: Optional[bool] = None
    audit_logging: Optional[bool] = None
    two_factor_required: Optional[bool] = None
    session_timeout_minutes: Optional[int] = Field(None, ge=5, le=1440)


class TenantBrandingUpdate(BaseModel):
    """Schema for updating tenant branding."""
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: Optional[str] = Field(None, regex="^#[0-9A-Fa-f]{6}$")
    secondary_color: Optional[str] = Field(None, regex="^#[0-9A-Fa-f]{6}$")
    accent_color: Optional[str] = Field(None, regex="^#[0-9A-Fa-f]{6}$")
    font_family: Optional[str] = None
    custom_css: Optional[str] = None


class TenantFeaturesUpdate(BaseModel):
    """Schema for updating tenant features."""
    telehealth: Optional[bool] = None
    ai_features: Optional[bool] = None
    custom_reports: Optional[bool] = None
    white_label: Optional[bool] = None
    api_access: Optional[bool] = None
    sso: Optional[bool] = None
    audit_trail: Optional[bool] = None


class ApiKeyCreateRequest(BaseModel):
    """Schema for creating an API key."""
    name: str = Field(..., min_length=2, max_length=255)
    scopes: List[str] = Field(default_factory=list)
    rate_limit: int = Field(default=1000, ge=1, le=100000)
    expires_in_days: Optional[int] = Field(default=None, ge=1, le=365)


class InviteUserRequest(BaseModel):
    """Schema for inviting a user to tenant."""
    email: EmailStr
    role: str = Field(default="user")
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class DataExportRequest(BaseModel):
    """Schema for requesting a data export."""
    export_type: str = Field(default="full")  # full, partial, gdpr_request
    format: str = Field(default="json")  # json, csv, fhir_bundle
    include_tables: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class TenantSuspendRequest(BaseModel):
    """Schema for suspending a tenant."""
    reason: str = Field(..., min_length=10, max_length=1000)


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================


class TenantLimitsResponse(BaseModel):
    """Tenant resource limits."""
    max_users: int
    max_patients: int
    max_storage_gb: int
    max_api_calls_per_day: int
    max_concurrent_connections: int
    max_file_upload_mb: int
    data_retention_days: int


class TenantBrandingResponse(BaseModel):
    """Tenant branding configuration."""
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: str = "#0066CC"
    secondary_color: str = "#F0F0F0"
    accent_color: str = "#00CC66"
    font_family: str = "Inter, sans-serif"
    custom_css: Optional[str] = None


class TenantSettingsResponse(BaseModel):
    """Tenant settings."""
    timezone: str = "UTC"
    date_format: str = "YYYY-MM-DD"
    time_format: str = "HH:mm"
    language: str = "en"
    currency: str = "USD"
    appointment_duration_minutes: int = 30
    enable_reminders: bool = True
    reminder_hours_before: int = 24
    enable_waitlist: bool = True
    enable_online_booking: bool = True
    require_payment_upfront: bool = False
    hipaa_mode: bool = True
    audit_logging: bool = True
    two_factor_required: bool = False
    session_timeout_minutes: int = 30


class TenantResponse(BaseModel):
    """Full tenant response."""
    id: str
    name: str
    slug: str
    code: str
    domain: Optional[str] = None
    tier: TenantTier
    status: TenantStatus
    owner_email: Optional[str] = None
    owner_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    timezone: str = "UTC"
    is_active: bool
    trial_ends_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TenantDetailResponse(TenantResponse):
    """Detailed tenant response including settings and limits."""
    limits: TenantLimitsResponse
    settings: TenantSettingsResponse
    branding: TenantBrandingResponse
    features: Dict[str, bool] = {}


class TenantListResponse(BaseModel):
    """Paginated list of tenants."""
    tenants: List[TenantResponse]
    total: int
    page: int
    page_size: int
    pages: int


class UsageStatsResponse(BaseModel):
    """Tenant usage statistics."""
    user_count: int = 0
    patient_count: int = 0
    appointment_count: int = 0
    encounter_count: int = 0
    storage_bytes: int = 0
    storage_used_percent: float = 0
    api_calls_today: int = 0
    api_calls_this_month: int = 0
    api_calls_limit_today: int = 0
    api_calls_remaining_today: int = 0


class QuotaCheckResponse(BaseModel):
    """Quota check result."""
    allowed: bool
    resource: str
    current: int
    limit: int
    remaining: int
    message: str


class ApiKeyResponse(BaseModel):
    """API key response (without secret)."""
    id: str
    name: str
    key_prefix: str
    scopes: List[str]
    rate_limit: int
    is_active: bool
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime


class ApiKeyCreatedResponse(BaseModel):
    """API key creation response (includes secret once)."""
    id: str
    name: str
    key: str  # Full key - only shown once
    key_prefix: str
    scopes: List[str]
    rate_limit: int
    expires_at: Optional[datetime] = None
    created_at: datetime
    warning: str = "Store this key securely. It will not be shown again."


class InvitationResponse(BaseModel):
    """User invitation response."""
    id: str
    email: str
    role: str
    status: str
    invited_by: Optional[str] = None
    expires_at: datetime
    created_at: datetime


class DataExportResponse(BaseModel):
    """Data export status response."""
    export_id: str
    export_type: str
    status: str
    format: str
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    records_exported: Optional[int] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime


class AuditLogEntry(BaseModel):
    """Audit log entry."""
    id: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    ip_address: Optional[str] = None
    changes: Optional[Dict[str, Any]] = None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    """Paginated audit log list."""
    entries: List[AuditLogEntry]
    total: int
    page: int
    page_size: int


class TenantSignupResponse(BaseModel):
    """Tenant signup response."""
    tenant: TenantResponse
    admin_user: Dict[str, Any]
    login_url: str
    message: str
