"""
App Marketplace Service
FastAPI service for third-party app management, API keys, and granular permissions
Port: 8023
"""
import logging
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID
import json

from fastapi import FastAPI, HTTPException, Depends, Query, Header
from sqlalchemy import create_engine, and_, or_, func
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import IntegrityError

from shared.database.models import (
    App,
    AppKey,
    AppScope,
    AppUsageLog,
    NetworkOrganization,
    Tenant
)
from shared.events.types import EventType
from shared.events.publisher import publish_event
from schemas import (
    AppCreate,
    AppUpdate,
    AppResponse,
    AppListResponse,
    AppKeyCreate,
    AppKeyResponse,
    AppKeyListResponse,
    AppScopeCreate,
    AppScopeResponse,
    AppScopeListResponse,
    AppUsageLogResponse,
    AppUsageLogListResponse,
    AppUsageStats,
    PermissionCheckRequest,
    PermissionCheckResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# FastAPI app
app = FastAPI(
    title="App Marketplace Service",
    description="Third-party app management with granular permissions and usage tracking",
    version="0.1.0"
)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== App Endpoints ====================

@app.post(
    "/api/v1/apps/apps",
    response_model=AppResponse,
    status_code=201,
    tags=["Apps"]
)
async def register_app(
    app_data: AppCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Register a new app in the marketplace.

    - **app_type**: web_app, agent, mobile, integration
    - **is_platform_app**: True for first-party platform apps
    """
    # Check if code already exists
    existing = db.query(App).filter(
        and_(
            App.tenant_id == app_data.tenant_id,
            App.code == app_data.code
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"App with code '{app_data.code}' already exists"
        )

    # Validate owner org if provided
    if app_data.owner_org_id:
        owner_org = db.query(NetworkOrganization).filter(
            NetworkOrganization.id == app_data.owner_org_id
        ).first()
        if not owner_org:
            raise HTTPException(status_code=404, detail="Owner organization not found")

    # Create app
    new_app = App(
        tenant_id=app_data.tenant_id,
        code=app_data.code,
        name=app_data.name,
        description=app_data.description,
        app_type=app_data.app_type,
        owner_org_id=app_data.owner_org_id,
        homepage_url=app_data.homepage_url,
        callback_url=app_data.callback_url,
        webhook_url=app_data.webhook_url,
        is_platform_app=app_data.is_platform_app,
        is_active=app_data.is_active,
        metadata=app_data.metadata
    )

    db.add(new_app)

    try:
        db.commit()
        db.refresh(new_app)

        # Publish event
        await publish_event(
            EventType.APP_REGISTERED,
            {
                "app_id": str(new_app.id),
                "code": new_app.code,
                "app_type": new_app.app_type,
                "is_platform_app": new_app.is_platform_app
            }
        )

        logger.info(f"App registered: {new_app.code}")
        return new_app

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")


@app.get(
    "/api/v1/apps/apps",
    response_model=AppListResponse,
    tags=["Apps"]
)
async def list_apps(
    tenant_id: Optional[UUID] = Query(None),
    app_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_platform_app: Optional[bool] = Query(None),
    search: Optional[str] = Query(None, description="Search by name or code"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List apps with filtering."""
    query = db.query(App)

    if tenant_id:
        query = query.filter(App.tenant_id == tenant_id)

    if app_type:
        query = query.filter(App.app_type == app_type.lower())

    if is_active is not None:
        query = query.filter(App.is_active == is_active)

    if is_platform_app is not None:
        query = query.filter(App.is_platform_app == is_platform_app)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                App.name.ilike(search_pattern),
                App.code.ilike(search_pattern)
            )
        )

    total = query.count()
    offset = (page - 1) * page_size
    apps = query.order_by(App.created_at.desc()).offset(offset).limit(page_size).all()

    return AppListResponse(
        total=total,
        apps=apps,
        page=page,
        page_size=page_size,
        has_next=offset + page_size < total,
        has_previous=page > 1
    )


@app.get(
    "/api/v1/apps/apps/{app_id}",
    response_model=AppResponse,
    tags=["Apps"]
)
async def get_app(
    app_id: UUID,
    db: Session = Depends(get_db)
):
    """Get an app by ID."""
    app_obj = db.query(App).filter(App.id == app_id).first()

    if not app_obj:
        raise HTTPException(status_code=404, detail="App not found")

    return app_obj


@app.patch(
    "/api/v1/apps/apps/{app_id}",
    response_model=AppResponse,
    tags=["Apps"]
)
async def update_app(
    app_id: UUID,
    update_data: AppUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Update app details."""
    app_obj = db.query(App).filter(App.id == app_id).first()

    if not app_obj:
        raise HTTPException(status_code=404, detail="App not found")

    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(app_obj, field, value)

    app_obj.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(app_obj)

    logger.info(f"App updated: {app_obj.code}")
    return app_obj


# ==================== App Key Endpoints ====================

@app.post(
    "/api/v1/apps/apps/{app_id}/keys",
    response_model=AppKeyResponse,
    status_code=201,
    tags=["App Keys"]
)
async def create_app_key(
    app_id: UUID,
    key_data: AppKeyCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Create a new API key for an app.

    The API key is only shown once at creation. Store it securely!
    """
    # Validate app exists
    app_obj = db.query(App).filter(App.id == app_id).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="App not found")

    # Generate API key
    raw_key = f"htk_{secrets.token_urlsafe(32)}"

    # Hash the key for storage
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    # Create app key
    app_key = AppKey(
        app_id=app_id,
        key_name=key_data.key_name,
        key_hash=key_hash,
        key_prefix=raw_key[:12],  # Store prefix for identification
        expires_at=key_data.expires_at,
        ip_whitelist=key_data.ip_whitelist,
        is_active=True
    )

    db.add(app_key)
    db.commit()
    db.refresh(app_key)

    # Publish event
    await publish_event(
        EventType.APP_KEY_CREATED,
        {
            "app_id": str(app_id),
            "key_id": str(app_key.id),
            "key_name": key_data.key_name
        }
    )

    logger.info(f"API key created for app {app_obj.code}: {key_data.key_name}")

    # Return response with actual key (only shown once!)
    response = AppKeyResponse(
        id=app_key.id,
        app_id=app_key.app_id,
        key_name=app_key.key_name,
        api_key=raw_key,  # Only shown at creation
        expires_at=app_key.expires_at,
        ip_whitelist=app_key.ip_whitelist,
        is_active=app_key.is_active,
        last_used_at=app_key.last_used_at,
        created_at=app_key.created_at
    )

    return response


@app.get(
    "/api/v1/apps/apps/{app_id}/keys",
    response_model=List[AppKeyListResponse],
    tags=["App Keys"]
)
async def list_app_keys(
    app_id: UUID,
    db: Session = Depends(get_db)
):
    """
    List API keys for an app.

    Note: Actual keys are not returned, only metadata.
    """
    # Validate app exists
    app_obj = db.query(App).filter(App.id == app_id).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="App not found")

    keys = db.query(AppKey).filter(AppKey.app_id == app_id).order_by(
        AppKey.created_at.desc()
    ).all()

    return [
        AppKeyListResponse(
            id=key.id,
            app_id=key.app_id,
            key_name=key.key_name,
            key_prefix=key.key_prefix,
            expires_at=key.expires_at,
            is_active=key.is_active,
            last_used_at=key.last_used_at,
            created_at=key.created_at
        )
        for key in keys
    ]


@app.delete(
    "/api/v1/apps/keys/{key_id}",
    status_code=204,
    tags=["App Keys"]
)
async def revoke_app_key(
    key_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Revoke an API key."""
    app_key = db.query(AppKey).filter(AppKey.id == key_id).first()

    if not app_key:
        raise HTTPException(status_code=404, detail="API key not found")

    app_key.is_active = False
    db.commit()

    # Publish event
    await publish_event(
        EventType.APP_KEY_REVOKED,
        {
            "app_id": str(app_key.app_id),
            "key_id": str(app_key.id)
        }
    )

    logger.info(f"API key revoked: {key_id}")
    return None


# ==================== App Scope Endpoints ====================

@app.post(
    "/api/v1/apps/scopes",
    response_model=AppScopeResponse,
    status_code=201,
    tags=["App Scopes"]
)
async def grant_scope(
    scope_data: AppScopeCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Grant a permission scope to an app.

    - **scope_type**: FHIR, TOOL, EVENT, ADMIN
    - **scope_code**: Specific permission (e.g., fhir.Patient.read, tool.prescribe)
    """
    # Validate app exists
    app_obj = db.query(App).filter(App.id == scope_data.app_id).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="App not found")

    # Check if scope already granted
    existing = db.query(AppScope).filter(
        and_(
            AppScope.app_id == scope_data.app_id,
            AppScope.scope_type == scope_data.scope_type,
            AppScope.scope_code == scope_data.scope_code
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Scope '{scope_data.scope_code}' already granted to app"
        )

    # Create scope
    scope = AppScope(
        app_id=scope_data.app_id,
        scope_type=scope_data.scope_type,
        scope_code=scope_data.scope_code,
        restrictions=scope_data.restrictions,
        granted_at=datetime.utcnow()
    )

    db.add(scope)
    db.commit()
    db.refresh(scope)

    # Publish event
    await publish_event(
        EventType.APP_SCOPE_GRANTED,
        {
            "app_id": str(scope_data.app_id),
            "scope_id": str(scope.id),
            "scope_type": scope.scope_type,
            "scope_code": scope.scope_code
        }
    )

    logger.info(f"Scope granted to app {app_obj.code}: {scope.scope_code}")
    return scope


@app.get(
    "/api/v1/apps/apps/{app_id}/scopes",
    response_model=AppScopeListResponse,
    tags=["App Scopes"]
)
async def list_app_scopes(
    app_id: UUID,
    scope_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List permission scopes granted to an app."""
    # Validate app exists
    app_obj = db.query(App).filter(App.id == app_id).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="App not found")

    query = db.query(AppScope).filter(AppScope.app_id == app_id)

    if scope_type:
        query = query.filter(AppScope.scope_type == scope_type.upper())

    scopes = query.order_by(AppScope.granted_at.desc()).all()

    return AppScopeListResponse(
        total=len(scopes),
        scopes=scopes
    )


@app.delete(
    "/api/v1/apps/scopes/{scope_id}",
    status_code=204,
    tags=["App Scopes"]
)
async def revoke_scope(
    scope_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Revoke a permission scope from an app."""
    scope = db.query(AppScope).filter(AppScope.id == scope_id).first()

    if not scope:
        raise HTTPException(status_code=404, detail="Scope not found")

    app_id = scope.app_id
    scope_code = scope.scope_code

    db.delete(scope)
    db.commit()

    # Publish event
    await publish_event(
        EventType.APP_SCOPE_REVOKED,
        {
            "app_id": str(app_id),
            "scope_id": str(scope_id),
            "scope_code": scope_code
        }
    )

    logger.info(f"Scope revoked: {scope_code} from app {app_id}")
    return None


# ==================== Usage Log Endpoints ====================

@app.get(
    "/api/v1/apps/apps/{app_id}/usage",
    response_model=AppUsageLogListResponse,
    tags=["Usage Logs"]
)
async def get_app_usage_logs(
    app_id: UUID,
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    usage_type: Optional[str] = Query(None, description="api_call, event_delivery"),
    status_code: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Get usage logs for an app."""
    # Validate app exists
    app_obj = db.query(App).filter(App.id == app_id).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="App not found")

    query = db.query(AppUsageLog).filter(AppUsageLog.app_id == app_id)

    if from_date:
        query = query.filter(AppUsageLog.occurred_at >= from_date)

    if to_date:
        query = query.filter(AppUsageLog.occurred_at <= to_date)

    if usage_type:
        query = query.filter(AppUsageLog.usage_type == usage_type)

    if status_code:
        query = query.filter(AppUsageLog.status_code == status_code)

    total = query.count()
    offset = (page - 1) * page_size
    logs = query.order_by(AppUsageLog.occurred_at.desc()).offset(offset).limit(page_size).all()

    return AppUsageLogListResponse(
        total=total,
        logs=logs,
        page=page,
        page_size=page_size,
        has_next=offset + page_size < total,
        has_previous=page > 1
    )


@app.get(
    "/api/v1/apps/apps/{app_id}/stats",
    response_model=AppUsageStats,
    tags=["Usage Logs"]
)
async def get_app_usage_stats(
    app_id: UUID,
    from_date: Optional[datetime] = Query(None, description="Defaults to 30 days ago"),
    to_date: Optional[datetime] = Query(None, description="Defaults to now"),
    db: Session = Depends(get_db)
):
    """Get usage statistics for an app."""
    # Validate app exists
    app_obj = db.query(App).filter(App.id == app_id).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="App not found")

    # Set default date range
    if not to_date:
        to_date = datetime.utcnow()
    if not from_date:
        from_date = to_date - timedelta(days=30)

    # Get usage logs
    logs = db.query(AppUsageLog).filter(
        and_(
            AppUsageLog.app_id == app_id,
            AppUsageLog.occurred_at >= from_date,
            AppUsageLog.occurred_at <= to_date
        )
    ).all()

    # Calculate stats
    total_api_calls = sum(1 for log in logs if log.usage_type == "api_call")
    total_events = sum(1 for log in logs if log.usage_type == "event_delivery")

    response_times = [log.response_time_ms for log in logs if log.response_time_ms]
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0

    error_count = sum(1 for log in logs if log.status_code and log.status_code >= 400)
    error_rate = (error_count / len(logs) * 100) if logs else 0

    last_used = max([log.occurred_at for log in logs]) if logs else None

    # Top endpoints
    endpoint_counts = {}
    for log in logs:
        if log.endpoint:
            endpoint_counts[log.endpoint] = endpoint_counts.get(log.endpoint, 0) + 1

    top_endpoints = [
        {"endpoint": endpoint, "count": count}
        for endpoint, count in sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    ]

    # Daily usage
    daily_usage = {}
    for log in logs:
        day = log.occurred_at.date().isoformat()
        if day not in daily_usage:
            daily_usage[day] = {"api_calls": 0, "events": 0}

        if log.usage_type == "api_call":
            daily_usage[day]["api_calls"] += 1
        elif log.usage_type == "event_delivery":
            daily_usage[day]["events"] += 1

    daily_usage_list = [
        {"date": date, **stats}
        for date, stats in sorted(daily_usage.items())
    ]

    return AppUsageStats(
        app_id=app_id,
        app_name=app_obj.name,
        total_api_calls=total_api_calls,
        total_events_delivered=total_events,
        avg_response_time_ms=avg_response_time,
        error_rate=error_rate,
        last_used_at=last_used,
        top_endpoints=top_endpoints,
        daily_usage=daily_usage_list
    )


# ==================== Permission Check Endpoint ====================

@app.post(
    "/api/v1/apps/permissions/check",
    response_model=PermissionCheckResponse,
    tags=["Permissions"]
)
async def check_permission(
    permission_check: PermissionCheckRequest,
    db: Session = Depends(get_db)
):
    """
    Check if an app has a specific permission.

    Used by other services to validate app permissions before allowing operations.
    """
    # Validate app exists and is active
    app_obj = db.query(App).filter(App.id == permission_check.app_id).first()

    if not app_obj:
        return PermissionCheckResponse(
            has_permission=False,
            reason="App not found"
        )

    if not app_obj.is_active:
        return PermissionCheckResponse(
            has_permission=False,
            reason="App is not active"
        )

    # Check for scope
    scope = db.query(AppScope).filter(
        and_(
            AppScope.app_id == permission_check.app_id,
            AppScope.scope_type == permission_check.scope_type.upper(),
            AppScope.scope_code == permission_check.scope_code
        )
    ).first()

    if not scope:
        return PermissionCheckResponse(
            has_permission=False,
            reason=f"App does not have scope '{permission_check.scope_code}'"
        )

    # Check restrictions if provided
    if scope.restrictions and permission_check.context:
        # Example: Check tenant_ids restriction
        if "tenant_ids" in scope.restrictions:
            allowed_tenant_ids = scope.restrictions["tenant_ids"]
            context_tenant_id = permission_check.context.get("tenant_id")

            if context_tenant_id and context_tenant_id not in allowed_tenant_ids:
                return PermissionCheckResponse(
                    has_permission=False,
                    scope=scope,
                    restrictions=scope.restrictions,
                    reason="Tenant not in allowed list"
                )

    # Permission granted
    return PermissionCheckResponse(
        has_permission=True,
        scope=scope,
        restrictions=scope.restrictions
    )


# ==================== Helper Functions ====================

async def log_app_usage(
    app_id: UUID,
    app_key_id: UUID,
    usage_type: str,
    endpoint: str,
    http_method: str,
    status_code: int,
    response_time_ms: int,
    ip_address: str,
    db: Session
):
    """Log app API usage."""
    usage_log = AppUsageLog(
        app_id=app_id,
        app_key_id=app_key_id,
        usage_type=usage_type,
        endpoint=endpoint,
        http_method=http_method,
        status_code=status_code,
        response_time_ms=response_time_ms,
        ip_address=ip_address,
        occurred_at=datetime.utcnow()
    )

    db.add(usage_log)
    db.commit()

    # Update key last_used_at
    app_key = db.query(AppKey).filter(AppKey.id == app_key_id).first()
    if app_key:
        app_key.last_used_at = datetime.utcnow()
        db.commit()


# Health check
@app.get("/health", tags=["System"])
async def health_check():
    """Service health check endpoint."""
    return {
        "service": "app-marketplace-service",
        "status": "healthy",
        "version": "0.1.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8023)
