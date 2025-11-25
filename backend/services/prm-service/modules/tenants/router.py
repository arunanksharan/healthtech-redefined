"""
Tenant Management API Router

EPIC-004: Multi-Tenancy Implementation

Provides comprehensive tenant management endpoints:
- Tenant CRUD operations
- Provisioning and onboarding
- Configuration management
- Usage tracking
- API key management
- Data export
- Audit logs
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text

from shared.database.connection import get_db
from shared.database.tenant_service import TenantServiceImpl, TenantCreate, TenantUpdate, ApiKeyCreate, DataExportRequest as DataExportServiceRequest
from shared.database.tenant_context import TenantTier, TenantStatus
from shared.database.cache import cache_manager
from shared.auth.dependencies import get_current_user, get_principal, Principal, require_scopes
from shared.auth.tenant_middleware import get_tenant_id, get_tenant_context, require_feature
from shared.auth.passwords import hash_password

from .schemas import (
    TenantSignupRequest,
    TenantSignupResponse,
    TenantCreateRequest,
    TenantUpdateRequest,
    TenantSettingsUpdate,
    TenantBrandingUpdate,
    TenantFeaturesUpdate,
    TenantResponse,
    TenantDetailResponse,
    TenantListResponse,
    TenantLimitsResponse,
    TenantBrandingResponse,
    TenantSettingsResponse,
    TenantSuspendRequest,
    UsageStatsResponse,
    QuotaCheckResponse,
    ApiKeyCreateRequest,
    ApiKeyResponse,
    ApiKeyCreatedResponse,
    InviteUserRequest,
    InvitationResponse,
    DataExportRequest,
    DataExportResponse,
    AuditLogEntry,
    AuditLogListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tenants", tags=["Tenants"])


# =============================================================================
# PUBLIC ENDPOINTS (No Auth Required)
# =============================================================================


@router.post(
    "/signup",
    response_model=TenantSignupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Sign up for a new tenant account",
)
async def signup_tenant(
    data: TenantSignupRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Create a new tenant account with an admin user.

    This is a public endpoint for self-service signup.
    """
    service = TenantServiceImpl(db, cache_manager)

    # Check if slug is available
    existing = await service.get_tenant_by_slug(data.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Organization slug '{data.slug}' is already taken"
        )

    # Create tenant
    try:
        create_data = TenantCreate(
            name=data.organization_name,
            slug=data.slug,
            tier=TenantTier(data.tier.value),
            owner_email=data.admin_email,
            owner_name=data.admin_name,
            phone=data.phone,
            country=data.country,
            timezone=data.timezone,
        )

        tenant_response, temp_password = await service.create_tenant(create_data)

        # Override with user's password
        db.execute(
            text("""
                UPDATE users
                SET password_hash = :password_hash
                WHERE tenant_id = :tenant_id AND email = :email
            """),
            {
                "password_hash": hash_password(data.admin_password),
                "tenant_id": tenant_response.id,
                "email": data.admin_email,
            }
        )
        db.commit()

        login_url = f"https://{data.slug}.healthtech.app/login"

        return TenantSignupResponse(
            tenant=TenantResponse(
                id=tenant_response.id,
                name=tenant_response.name,
                slug=tenant_response.slug,
                code=tenant_response.code,
                domain=tenant_response.domain,
                tier=TenantTier(tenant_response.tier),
                status=TenantStatus(tenant_response.status),
                owner_email=tenant_response.owner_email,
                owner_name=tenant_response.owner_name,
                timezone=tenant_response.timezone,
                is_active=tenant_response.is_active,
                created_at=tenant_response.created_at,
                updated_at=tenant_response.updated_at,
            ),
            admin_user={
                "email": data.admin_email,
                "name": data.admin_name,
                "role": "tenant_admin",
            },
            login_url=login_url,
            message="Your account has been created. Please log in to continue.",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/check-slug/{slug}",
    summary="Check if a slug is available",
)
async def check_slug_availability(
    slug: str,
    db: Session = Depends(get_db),
):
    """Check if a tenant slug is available for registration."""
    service = TenantServiceImpl(db, cache_manager)
    existing = await service.get_tenant_by_slug(slug)

    return {
        "slug": slug,
        "available": existing is None,
    }


# =============================================================================
# TENANT ADMIN ENDPOINTS
# =============================================================================


@router.get(
    "/current",
    response_model=TenantDetailResponse,
    summary="Get current tenant details",
)
async def get_current_tenant_details(
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get details of the current tenant."""
    service = TenantServiceImpl(db, cache_manager)
    tenant = await service.get_tenant(tenant_id)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    return TenantDetailResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        code=tenant.code,
        domain=tenant.domain,
        tier=TenantTier(tenant.tier),
        status=TenantStatus(tenant.status),
        owner_email=tenant.owner_email,
        owner_name=tenant.owner_name,
        timezone=tenant.timezone,
        is_active=tenant.is_active,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
        limits=TenantLimitsResponse(**tenant.limits) if tenant.limits else TenantLimitsResponse(
            max_users=5, max_patients=1000, max_storage_gb=5,
            max_api_calls_per_day=10000, max_concurrent_connections=10,
            max_file_upload_mb=10, data_retention_days=365
        ),
        settings=TenantSettingsResponse(**tenant.settings) if tenant.settings else TenantSettingsResponse(),
        branding=TenantBrandingResponse(**tenant.branding) if tenant.branding else TenantBrandingResponse(),
        features=tenant.features or {},
    )


@router.patch(
    "/current",
    response_model=TenantResponse,
    summary="Update current tenant",
    dependencies=[Depends(require_scopes("tenant:write"))],
)
async def update_current_tenant(
    data: TenantUpdateRequest,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Update current tenant details."""
    service = TenantServiceImpl(db, cache_manager)

    update_data = TenantUpdate(
        name=data.name,
        owner_email=data.owner_email,
        owner_name=data.owner_name,
        phone=data.phone,
        address=data.address,
        country=data.country,
        timezone=data.timezone,
    )

    tenant = await service.update_tenant(tenant_id, **update_data.dict(exclude_none=True))

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        code=tenant.code,
        domain=tenant.domain,
        tier=TenantTier(tenant.tier),
        status=TenantStatus(tenant.status),
        owner_email=tenant.owner_email,
        owner_name=tenant.owner_name,
        timezone=tenant.timezone,
        is_active=tenant.is_active,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
    )


@router.put(
    "/current/settings",
    response_model=TenantSettingsResponse,
    summary="Update tenant settings",
    dependencies=[Depends(require_scopes("tenant:write"))],
)
async def update_tenant_settings(
    data: TenantSettingsUpdate,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Update tenant settings."""
    service = TenantServiceImpl(db, cache_manager)

    settings = data.dict(exclude_none=True)
    if settings:
        await service.update_tenant(tenant_id, settings=settings)

    tenant = await service.get_tenant(tenant_id)
    return TenantSettingsResponse(**(tenant.settings or {}))


@router.put(
    "/current/branding",
    response_model=TenantBrandingResponse,
    summary="Update tenant branding",
    dependencies=[Depends(require_scopes("tenant:write"))],
)
async def update_tenant_branding(
    data: TenantBrandingUpdate,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Update tenant branding configuration."""
    service = TenantServiceImpl(db, cache_manager)

    branding = data.dict(exclude_none=True)
    if branding:
        await service.update_tenant(tenant_id, branding=branding)

    tenant = await service.get_tenant(tenant_id)
    return TenantBrandingResponse(**(tenant.branding or {}))


# =============================================================================
# USAGE & QUOTA ENDPOINTS
# =============================================================================


@router.get(
    "/current/usage",
    response_model=UsageStatsResponse,
    summary="Get tenant usage statistics",
)
async def get_tenant_usage(
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get current usage statistics for the tenant."""
    service = TenantServiceImpl(db, cache_manager)
    stats = await service.get_usage_stats(tenant_id)
    tenant = await service.get_tenant(tenant_id)

    limits = tenant.limits or {}
    api_limit = limits.get("max_api_calls_per_day", 10000)
    storage_limit = limits.get("max_storage_gb", 5) * 1024 * 1024 * 1024

    return UsageStatsResponse(
        user_count=stats.user_count,
        patient_count=stats.patient_count,
        appointment_count=stats.appointment_count,
        encounter_count=stats.encounter_count,
        storage_bytes=stats.storage_bytes,
        storage_used_percent=(stats.storage_bytes / storage_limit * 100) if storage_limit > 0 else 0,
        api_calls_today=stats.api_calls_today,
        api_calls_this_month=stats.api_calls_this_month,
        api_calls_limit_today=api_limit,
        api_calls_remaining_today=max(0, api_limit - stats.api_calls_today),
    )


@router.get(
    "/current/quota/{resource}",
    response_model=QuotaCheckResponse,
    summary="Check resource quota",
)
async def check_resource_quota(
    resource: str,
    amount: int = Query(default=1, ge=1),
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Check if a resource quota would be exceeded."""
    service = TenantServiceImpl(db, cache_manager)
    allowed, message = await service.check_quota(tenant_id, resource, amount)
    stats = await service.get_usage_stats(tenant_id)
    tenant = await service.get_tenant(tenant_id)

    limits = tenant.limits or {}

    # Get current and limit values
    resource_map = {
        "users": (stats.user_count, limits.get("max_users", 5)),
        "patients": (stats.patient_count, limits.get("max_patients", 1000)),
        "api_calls": (stats.api_calls_today, limits.get("max_api_calls_per_day", 10000)),
        "storage": (stats.storage_bytes, limits.get("max_storage_gb", 5) * 1024 * 1024 * 1024),
    }

    current, limit = resource_map.get(resource, (0, 0))

    return QuotaCheckResponse(
        allowed=allowed,
        resource=resource,
        current=current,
        limit=limit,
        remaining=max(0, limit - current),
        message=message,
    )


# =============================================================================
# API KEY MANAGEMENT
# =============================================================================


@router.get(
    "/current/api-keys",
    response_model=List[ApiKeyResponse],
    summary="List API keys",
    dependencies=[Depends(require_scopes("api_key:read"))],
)
async def list_api_keys(
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """List all API keys for the tenant."""
    service = TenantServiceImpl(db, cache_manager)
    keys = await service.list_api_keys(tenant_id)

    return [
        ApiKeyResponse(
            id=k["id"],
            name=k["name"],
            key_prefix=k["key_prefix"],
            scopes=k["scopes"],
            rate_limit=k["rate_limit"],
            is_active=k["is_active"],
            last_used_at=k["last_used_at"],
            expires_at=k["expires_at"],
            created_at=k["created_at"],
        )
        for k in keys
    ]


@router.post(
    "/current/api-keys",
    response_model=ApiKeyCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create API key",
    dependencies=[Depends(require_scopes("api_key:write"))],
)
async def create_api_key(
    data: ApiKeyCreateRequest,
    tenant_id: str = Depends(get_tenant_id),
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
):
    """Create a new API key for the tenant."""
    service = TenantServiceImpl(db, cache_manager)

    create_data = ApiKeyCreate(
        name=data.name,
        scopes=data.scopes,
        rate_limit=data.rate_limit,
        expires_in_days=data.expires_in_days,
    )

    raw_key, key_info = await service.create_api_key(
        tenant_id, create_data, str(principal.user_id)
    )

    return ApiKeyCreatedResponse(
        id=key_info["id"],
        name=key_info["name"],
        key=raw_key,
        key_prefix=key_info["key_prefix"],
        scopes=key_info["scopes"],
        rate_limit=key_info["rate_limit"],
        expires_at=key_info["expires_at"],
        created_at=key_info["created_at"],
    )


@router.delete(
    "/current/api-keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke API key",
    dependencies=[Depends(require_scopes("api_key:write"))],
)
async def revoke_api_key(
    key_id: str,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Revoke an API key."""
    service = TenantServiceImpl(db, cache_manager)
    await service.revoke_api_key(tenant_id, key_id)


# =============================================================================
# DATA EXPORT
# =============================================================================


@router.post(
    "/current/exports",
    response_model=DataExportResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request data export",
    dependencies=[Depends(require_scopes("export:write"))],
)
async def request_data_export(
    data: DataExportRequest,
    background_tasks: BackgroundTasks,
    tenant_id: str = Depends(get_tenant_id),
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
):
    """Request a data export for the tenant."""
    service = TenantServiceImpl(db, cache_manager)

    export_data = DataExportServiceRequest(
        export_type=data.export_type,
        format=data.format,
        include_tables=data.include_tables,
        date_from=data.date_from,
        date_to=data.date_to,
    )

    result = await service.request_data_export(
        tenant_id, export_data, str(principal.user_id)
    )

    return DataExportResponse(
        export_id=result["export_id"],
        export_type=data.export_type,
        status=result["status"],
        format=data.format,
        expires_at=result["expires_at"],
        created_at=datetime.now(timezone.utc),
    )


@router.get(
    "/current/exports/{export_id}",
    response_model=DataExportResponse,
    summary="Get export status",
)
async def get_export_status(
    export_id: str,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get the status of a data export."""
    service = TenantServiceImpl(db, cache_manager)
    result = await service.get_export_status(tenant_id, export_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found"
        )

    return DataExportResponse(**result)


# =============================================================================
# AUDIT LOGS
# =============================================================================


@router.get(
    "/current/audit-logs",
    response_model=AuditLogListResponse,
    summary="Get audit logs",
    dependencies=[Depends(require_scopes("audit:read"))],
)
async def get_audit_logs(
    resource_type: Optional[str] = None,
    action: Optional[str] = None,
    user_id: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get audit logs for the tenant."""
    offset = (page - 1) * page_size

    # Build query
    conditions = ["tenant_id = :tenant_id"]
    params = {"tenant_id": tenant_id, "limit": page_size, "offset": offset}

    if resource_type:
        conditions.append("resource_type = :resource_type")
        params["resource_type"] = resource_type

    if action:
        conditions.append("action = :action")
        params["action"] = action

    if user_id:
        conditions.append("user_id = :user_id")
        params["user_id"] = user_id

    if date_from:
        conditions.append("created_at >= :date_from")
        params["date_from"] = date_from

    if date_to:
        conditions.append("created_at <= :date_to")
        params["date_to"] = date_to

    where_clause = " AND ".join(conditions)

    # Get count
    count = db.execute(
        text(f"SELECT COUNT(*) FROM tenant_audit_logs WHERE {where_clause}"),
        params
    ).scalar()

    # Get logs
    results = db.execute(
        text(f"""
            SELECT
                l.id, l.action, l.resource_type, l.resource_id, l.user_id,
                u.email as user_email, l.ip_address, l.changes, l.created_at
            FROM tenant_audit_logs l
            LEFT JOIN users u ON l.user_id = u.id
            WHERE {where_clause}
            ORDER BY l.created_at DESC
            LIMIT :limit OFFSET :offset
        """),
        params
    ).fetchall()

    entries = [
        AuditLogEntry(
            id=str(r.id),
            action=r.action,
            resource_type=r.resource_type,
            resource_id=str(r.resource_id) if r.resource_id else None,
            user_id=str(r.user_id) if r.user_id else None,
            user_email=r.user_email,
            ip_address=r.ip_address,
            changes=r.changes,
            created_at=r.created_at,
        )
        for r in results
    ]

    return AuditLogListResponse(
        entries=entries,
        total=count,
        page=page,
        page_size=page_size,
    )


# =============================================================================
# SUPER ADMIN ENDPOINTS
# =============================================================================


@router.get(
    "",
    response_model=TenantListResponse,
    summary="List all tenants (admin only)",
    dependencies=[Depends(require_scopes("admin:tenants:read"))],
)
async def list_all_tenants(
    status_filter: Optional[TenantStatus] = Query(None, alias="status"),
    tier_filter: Optional[TenantTier] = Query(None, alias="tier"),
    search: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List all tenants (super admin only)."""
    service = TenantServiceImpl(db, cache_manager)

    tenants, total = await service.list_tenants(
        status=status_filter,
        tier=tier_filter,
        search=search,
        skip=(page - 1) * page_size,
        limit=page_size,
    )

    return TenantListResponse(
        tenants=[
            TenantResponse(
                id=t.id,
                name=t.name,
                slug=t.slug,
                code=t.code,
                domain=t.domain,
                tier=TenantTier(t.tier),
                status=TenantStatus(t.status),
                owner_email=t.owner_email,
                owner_name=t.owner_name,
                timezone=t.timezone,
                is_active=t.is_active,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in tenants
        ],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post(
    "",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create tenant (admin only)",
    dependencies=[Depends(require_scopes("admin:tenants:write"))],
)
async def create_tenant_admin(
    data: TenantCreateRequest,
    db: Session = Depends(get_db),
):
    """Create a new tenant (super admin only)."""
    service = TenantServiceImpl(db, cache_manager)

    create_data = TenantCreate(
        name=data.name,
        slug=data.slug,
        tier=TenantTier(data.tier.value),
        owner_email=data.owner_email,
        owner_name=data.owner_name,
        phone=data.phone,
        address=data.address,
        country=data.country,
        timezone=data.timezone,
    )

    try:
        tenant, _ = await service.create_tenant(create_data)
        return TenantResponse(
            id=tenant.id,
            name=tenant.name,
            slug=tenant.slug,
            code=tenant.code,
            domain=tenant.domain,
            tier=TenantTier(tenant.tier),
            status=TenantStatus(tenant.status),
            owner_email=tenant.owner_email,
            owner_name=tenant.owner_name,
            timezone=tenant.timezone,
            is_active=tenant.is_active,
            created_at=tenant.created_at,
            updated_at=tenant.updated_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{tenant_id}",
    response_model=TenantDetailResponse,
    summary="Get tenant details (admin only)",
    dependencies=[Depends(require_scopes("admin:tenants:read"))],
)
async def get_tenant_admin(
    tenant_id: str,
    db: Session = Depends(get_db),
):
    """Get tenant details (super admin only)."""
    service = TenantServiceImpl(db, cache_manager)
    tenant = await service.get_tenant(tenant_id)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    return TenantDetailResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        code=tenant.code,
        domain=tenant.domain,
        tier=TenantTier(tenant.tier),
        status=TenantStatus(tenant.status),
        owner_email=tenant.owner_email,
        owner_name=tenant.owner_name,
        timezone=tenant.timezone,
        is_active=tenant.is_active,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
        limits=TenantLimitsResponse(**tenant.limits) if tenant.limits else TenantLimitsResponse(
            max_users=5, max_patients=1000, max_storage_gb=5,
            max_api_calls_per_day=10000, max_concurrent_connections=10,
            max_file_upload_mb=10, data_retention_days=365
        ),
        settings=TenantSettingsResponse(**tenant.settings) if tenant.settings else TenantSettingsResponse(),
        branding=TenantBrandingResponse(**tenant.branding) if tenant.branding else TenantBrandingResponse(),
        features=tenant.features or {},
    )


@router.post(
    "/{tenant_id}/suspend",
    status_code=status.HTTP_200_OK,
    summary="Suspend tenant (admin only)",
    dependencies=[Depends(require_scopes("admin:tenants:write"))],
)
async def suspend_tenant(
    tenant_id: str,
    data: TenantSuspendRequest,
    db: Session = Depends(get_db),
):
    """Suspend a tenant (super admin only)."""
    service = TenantServiceImpl(db, cache_manager)
    await service.suspend_tenant(tenant_id, data.reason)

    return {"message": "Tenant suspended", "tenant_id": tenant_id}


@router.post(
    "/{tenant_id}/activate",
    status_code=status.HTTP_200_OK,
    summary="Activate tenant (admin only)",
    dependencies=[Depends(require_scopes("admin:tenants:write"))],
)
async def activate_tenant(
    tenant_id: str,
    db: Session = Depends(get_db),
):
    """Activate a suspended tenant (super admin only)."""
    service = TenantServiceImpl(db, cache_manager)
    await service.activate_tenant(tenant_id)

    return {"message": "Tenant activated", "tenant_id": tenant_id}


@router.delete(
    "/{tenant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete tenant (admin only)",
    dependencies=[Depends(require_scopes("admin:tenants:delete"))],
)
async def delete_tenant(
    tenant_id: str,
    hard_delete: bool = Query(default=False),
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
):
    """Delete a tenant (super admin only)."""
    service = TenantServiceImpl(db, cache_manager)
    await service.delete_tenant(
        tenant_id,
        hard_delete=hard_delete,
        deleted_by=str(principal.user_id)
    )


@router.patch(
    "/{tenant_id}/tier",
    response_model=TenantResponse,
    summary="Change tenant tier (admin only)",
    dependencies=[Depends(require_scopes("admin:tenants:write"))],
)
async def change_tenant_tier(
    tenant_id: str,
    tier: TenantTier,
    db: Session = Depends(get_db),
):
    """Change a tenant's subscription tier (super admin only)."""
    service = TenantServiceImpl(db, cache_manager)

    tenant = await service.update_tenant(tenant_id, tier=tier)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        code=tenant.code,
        domain=tenant.domain,
        tier=TenantTier(tenant.tier),
        status=TenantStatus(tenant.status),
        owner_email=tenant.owner_email,
        owner_name=tenant.owner_name,
        timezone=tenant.timezone,
        is_active=tenant.is_active,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
    )


@router.put(
    "/{tenant_id}/features",
    summary="Update tenant features (admin only)",
    dependencies=[Depends(require_scopes("admin:tenants:write"))],
)
async def update_tenant_features_admin(
    tenant_id: str,
    data: TenantFeaturesUpdate,
    db: Session = Depends(get_db),
):
    """Update tenant feature flags (super admin only)."""
    service = TenantServiceImpl(db, cache_manager)

    features = data.dict(exclude_none=True)
    if features:
        await service.update_tenant(tenant_id, features=features)

    tenant = await service.get_tenant(tenant_id)

    return {"features": tenant.features}
