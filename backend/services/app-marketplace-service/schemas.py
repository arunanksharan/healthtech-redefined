"""
App Marketplace Service Pydantic Schemas
Request/Response models for apps, API keys, scopes, and usage logs
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator


# ==================== App Schemas ====================

class AppCreate(BaseModel):
    """Schema for registering an app"""

    tenant_id: UUID
    code: str = Field(..., description="Unique app code (e.g., ZOOM_INTEGRATION, NLP_TRIAGE_AGENT)")
    name: str
    description: Optional[str] = None
    app_type: str = Field(..., description="web_app, agent, mobile, integration")
    owner_org_id: Optional[UUID] = Field(None, description="Network organization that owns the app")
    homepage_url: Optional[str] = None
    callback_url: Optional[str] = Field(None, description="OAuth callback URL")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for events")
    is_platform_app: bool = Field(default=False, description="True for first-party platform apps")
    is_active: bool = Field(default=True)
    metadata: Optional[Dict[str, Any]] = None

    @validator("app_type")
    def validate_app_type(cls, v):
        valid_types = ["web_app", "agent", "mobile", "integration", "analytics", "workflow"]
        if v.lower() not in valid_types:
            raise ValueError(f"app_type must be one of: {', '.join(valid_types)}")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "code": "ZOOM_TELEHEALTH",
                "name": "Zoom Telehealth Integration",
                "description": "Video consultation integration with Zoom",
                "app_type": "integration",
                "homepage_url": "https://zoom.us/healthcare",
                "callback_url": "https://zoom.us/oauth/callback",
                "webhook_url": "https://zoom.us/webhooks/healthtech",
                "is_platform_app": False,
                "metadata": {
                    "vendor": "Zoom Video Communications",
                    "version": "1.0.0"
                }
            }
        }


class AppUpdate(BaseModel):
    """Schema for updating an app"""

    name: Optional[str] = None
    description: Optional[str] = None
    homepage_url: Optional[str] = None
    callback_url: Optional[str] = None
    webhook_url: Optional[str] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class AppResponse(BaseModel):
    """Response schema for app"""

    id: UUID
    tenant_id: UUID
    code: str
    name: str
    description: Optional[str] = None
    app_type: str
    owner_org_id: Optional[UUID] = None
    homepage_url: Optional[str] = None
    callback_url: Optional[str] = None
    webhook_url: Optional[str] = None
    is_platform_app: bool
    is_active: bool
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AppListResponse(BaseModel):
    """Response for list of apps"""

    total: int
    apps: List[AppResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== App Key Schemas ====================

class AppKeyCreate(BaseModel):
    """Schema for creating an API key for an app"""

    app_id: UUID
    key_name: str = Field(..., description="Friendly name for the key (e.g., 'Production', 'Staging')")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration date")
    ip_whitelist: Optional[List[str]] = Field(None, description="IP addresses allowed to use this key")

    class Config:
        json_schema_extra = {
            "example": {
                "app_id": "app-uuid-123",
                "key_name": "Production Key",
                "expires_at": "2026-12-31T23:59:59Z",
                "ip_whitelist": ["203.0.113.0/24", "198.51.100.42"]
            }
        }


class AppKeyResponse(BaseModel):
    """Response schema for app key"""

    id: UUID
    app_id: UUID
    key_name: str
    api_key: str = Field(..., description="The actual API key (only shown once at creation)")
    expires_at: Optional[datetime] = None
    ip_whitelist: Optional[List[str]] = None
    is_active: bool
    last_used_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AppKeyListResponse(BaseModel):
    """Response for list of app keys (without showing actual keys)"""

    id: UUID
    app_id: UUID
    key_name: str
    key_prefix: str = Field(..., description="First 8 chars of key for identification")
    expires_at: Optional[datetime] = None
    is_active: bool
    last_used_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== App Scope Schemas ====================

class AppScopeCreate(BaseModel):
    """Schema for granting a scope to an app"""

    app_id: UUID
    scope_type: str = Field(..., description="FHIR, TOOL, EVENT, ADMIN")
    scope_code: str = Field(..., description="Specific permission code")
    restrictions: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional restrictions (e.g., patient_id, read_only)"
    )

    @validator("scope_type")
    def validate_scope_type(cls, v):
        valid_types = ["FHIR", "TOOL", "EVENT", "ADMIN"]
        if v.upper() not in valid_types:
            raise ValueError(f"scope_type must be one of: {', '.join(valid_types)}")
        return v.upper()

    class Config:
        json_schema_extra = {
            "example": {
                "app_id": "app-uuid-123",
                "scope_type": "FHIR",
                "scope_code": "fhir.Patient.read",
                "restrictions": {
                    "read_only": True,
                    "tenant_ids": ["tenant-uuid-1", "tenant-uuid-2"]
                }
            }
        }


class AppScopeResponse(BaseModel):
    """Response schema for app scope"""

    id: UUID
    app_id: UUID
    scope_type: str
    scope_code: str
    restrictions: Optional[Dict[str, Any]] = None
    granted_at: datetime

    class Config:
        from_attributes = True


class AppScopeListResponse(BaseModel):
    """Response for list of app scopes"""

    total: int
    scopes: List[AppScopeResponse]


# ==================== App Usage Log Schemas ====================

class AppUsageLogResponse(BaseModel):
    """Response schema for app usage log"""

    id: UUID
    app_id: UUID
    app_key_id: UUID
    usage_type: str
    scope_code: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    http_method: Optional[str] = None
    endpoint: Optional[str] = None
    status_code: Optional[int] = None
    response_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    occurred_at: datetime

    class Config:
        from_attributes = True


class AppUsageLogListResponse(BaseModel):
    """Response for list of app usage logs"""

    total: int
    logs: List[AppUsageLogResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== App Analytics Schemas ====================

class AppUsageStats(BaseModel):
    """Usage statistics for an app"""

    app_id: UUID
    app_name: str
    total_api_calls: int
    total_events_delivered: int
    avg_response_time_ms: float
    error_rate: float
    last_used_at: Optional[datetime] = None
    top_endpoints: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Most frequently used endpoints"
    )
    daily_usage: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Usage breakdown by day"
    )


# ==================== Permission Check Schemas ====================

class PermissionCheckRequest(BaseModel):
    """Request to check if an app has a specific permission"""

    app_id: UUID
    scope_type: str
    scope_code: str
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional context for permission evaluation"
    )


class PermissionCheckResponse(BaseModel):
    """Response for permission check"""

    has_permission: bool
    scope: Optional[AppScopeResponse] = None
    restrictions: Optional[Dict[str, Any]] = None
    reason: Optional[str] = Field(None, description="Reason if permission denied")
