"""
Mobile Applications Router
EPIC-016: FastAPI endpoints for mobile platform
"""
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from modules.mobile.services import (
    DeviceService,
    PushNotificationService,
    MobileSyncService,
    WearableService,
    MobileAuthService
)
from modules.mobile.schemas import (
    # Device schemas
    DeviceRegister, DeviceUpdate, DeviceSecurityUpdate,
    DeviceResponse, DeviceListResponse,
    # Session schemas
    SessionCreate, SessionResponse, SessionRefresh,
    BiometricAuthRequest, BiometricAuthResponse,
    # Notification schemas
    NotificationSend, NotificationBulkSend, NotificationResponse,
    NotificationListResponse, NotificationPreferenceUpdate, NotificationPreferenceResponse,
    # Sync schemas
    SyncRequest, SyncResponse, SyncPush, SyncPushResult,
    SyncConflictResolve, SyncStatusResponse,
    # Wearable schemas
    WearableConnect, WearableUpdate, WearableResponse, WearableListResponse,
    # Health metric schemas
    HealthMetricRecord, HealthMetricBulkRecord, HealthMetricResponse,
    HealthMetricListResponse, HealthMetricSummary, HealthMetricGoalCreate, HealthMetricGoalResponse,
    # Other schemas
    AppUsageEventRecord, AppUsageEventBatch, AppCrashReportCreate,
    AppVersionCheck, AppVersionResponse,
    DeepLinkCreate, DeepLinkResponse, DeepLinkResolve, DeepLinkResolveResponse,
    StorageInfoResponse, CacheClearRequest,
    # Enums
    DeviceStatusSchema, NotificationTypeSchema, HealthMetricTypeSchema
)
from modules.mobile.models import DeviceStatus, NotificationType, HealthMetricType


router = APIRouter(prefix="/mobile", tags=["Mobile Applications"])

# Service instances
device_service = DeviceService()
notification_service = PushNotificationService()
sync_service = MobileSyncService()
wearable_service = WearableService()
auth_service = MobileAuthService()


def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


# ============================================================================
# Device Management Endpoints
# ============================================================================

@router.post("/devices/register", response_model=DeviceResponse)
async def register_device(
    request: Request,
    data: DeviceRegister,
    user_id: UUID = Query(..., description="User ID"),
    user_type: str = Query(..., description="User type (patient/practitioner)"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Register a new mobile device or update existing"""
    try:
        return await device_service.register_device(
            db, user_id, user_type, tenant_id, data, get_client_ip(request)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/devices/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: UUID,
    data: DeviceUpdate,
    user_id: UUID = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """Update device information"""
    try:
        return await device_service.update_device(db, device_id, user_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/devices/{device_id}/security", response_model=DeviceResponse)
async def update_device_security(
    request: Request,
    device_id: UUID,
    data: DeviceSecurityUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update device security flags (jailbreak/root detection)"""
    try:
        return await device_service.update_device_security(
            db, device_id, data, get_client_ip(request)
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/devices/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: UUID,
    user_id: UUID = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get device by ID"""
    try:
        return await device_service.get_device(db, device_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/devices", response_model=DeviceListResponse)
async def list_devices(
    user_id: UUID = Query(..., description="User ID"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    status: Optional[DeviceStatusSchema] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db)
):
    """List all devices for a user"""
    status_enum = DeviceStatus(status.value) if status else None
    return await device_service.list_user_devices(db, user_id, tenant_id, status_enum)


@router.put("/devices/{device_id}/token")
async def update_device_token(
    device_id: UUID,
    device_token: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db)
):
    """Update device push notification token"""
    await device_service.update_device_token(db, device_id, device_token)
    return {"status": "success"}


@router.post("/devices/{device_id}/deactivate")
async def deactivate_device(
    request: Request,
    device_id: UUID,
    user_id: UUID = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate a device"""
    try:
        await device_service.deactivate_device(
            db, device_id, user_id, get_client_ip(request)
        )
        return {"status": "deactivated"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/devices/{device_id}/revoke")
async def revoke_device(
    request: Request,
    device_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    reason: Optional[str] = Body(None, embed=True),
    db: AsyncSession = Depends(get_db)
):
    """Revoke device access (admin action)"""
    try:
        await device_service.revoke_device(
            db, device_id, tenant_id, reason, get_client_ip(request)
        )
        return {"status": "revoked"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# Authentication Endpoints
# ============================================================================

@router.post("/auth/session", response_model=SessionResponse)
async def create_session(
    request: Request,
    data: SessionCreate,
    device_id: UUID = Query(..., description="Device ID"),
    user_id: UUID = Query(..., description="User ID"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Create a new mobile session"""
    try:
        return await auth_service.create_session(
            db, device_id, user_id, tenant_id, data,
            get_client_ip(request),
            request.headers.get("User-Agent")
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auth/refresh", response_model=SessionResponse)
async def refresh_session(
    request: Request,
    data: SessionRefresh,
    db: AsyncSession = Depends(get_db)
):
    """Refresh an existing session"""
    try:
        return await auth_service.refresh_session(db, data, get_client_ip(request))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/auth/biometric", response_model=BiometricAuthResponse)
async def authenticate_biometric(
    request: Request,
    data: BiometricAuthRequest,
    device_id: UUID = Query(..., description="Device ID"),
    user_id: UUID = Query(..., description="User ID"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Authenticate using biometric"""
    try:
        return await auth_service.authenticate_biometric(
            db, device_id, user_id, tenant_id, data, get_client_ip(request)
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/auth/biometric/challenge")
async def get_biometric_challenge(
    device_id: UUID = Query(..., description="Device ID"),
    db: AsyncSession = Depends(get_db)
):
    """Generate a challenge for biometric authentication"""
    return await auth_service.generate_biometric_challenge(db, device_id)


@router.post("/auth/biometric/enable")
async def enable_biometric(
    device_id: UUID = Query(..., description="Device ID"),
    user_id: UUID = Query(..., description="User ID"),
    biometric_type: str = Body(..., embed=True),
    public_key: Optional[str] = Body(None, embed=True),
    db: AsyncSession = Depends(get_db)
):
    """Enable biometric authentication on device"""
    from modules.mobile.models import BiometricType
    try:
        await auth_service.enable_biometric(
            db, device_id, user_id, BiometricType(biometric_type), public_key
        )
        return {"status": "enabled"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auth/biometric/disable")
async def disable_biometric(
    device_id: UUID = Query(..., description="Device ID"),
    user_id: UUID = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """Disable biometric authentication on device"""
    try:
        await auth_service.disable_biometric(db, device_id, user_id)
        return {"status": "disabled"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auth/logout")
async def logout(
    request: Request,
    session_id: UUID = Query(..., description="Session ID"),
    user_id: UUID = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """End a mobile session (logout)"""
    try:
        await auth_service.end_session(db, session_id, user_id, get_client_ip(request))
        return {"status": "logged_out"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/auth/logout-all")
async def logout_all(
    user_id: UUID = Query(..., description="User ID"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    except_session_id: Optional[UUID] = Query(None, description="Keep this session"),
    db: AsyncSession = Depends(get_db)
):
    """End all sessions for a user"""
    count = await auth_service.end_all_sessions(db, user_id, tenant_id, except_session_id)
    return {"status": "success", "sessions_ended": count}


@router.get("/auth/sessions")
async def get_active_sessions(
    user_id: UUID = Query(..., description="User ID"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get all active sessions for a user"""
    return await auth_service.get_active_sessions(db, user_id, tenant_id)


@router.get("/auth/audit-log")
async def get_audit_log(
    user_id: UUID = Query(..., description="User ID"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    action_category: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db)
):
    """Get authentication audit log"""
    return await auth_service.get_audit_log(
        db, user_id, tenant_id, action_category, limit, offset
    )


# ============================================================================
# Push Notification Endpoints
# ============================================================================

@router.post("/notifications/send", response_model=NotificationResponse)
async def send_notification(
    data: NotificationSend,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    user_id: UUID = Query(..., description="Target user ID"),
    sender_id: Optional[UUID] = Query(None, description="Sender ID"),
    db: AsyncSession = Depends(get_db)
):
    """Send a push notification to a user"""
    try:
        return await notification_service.send_notification(
            db, tenant_id, user_id, data, sender_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/notifications/send-bulk", response_model=List[NotificationResponse])
async def send_bulk_notification(
    data: NotificationBulkSend,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    sender_id: Optional[UUID] = Query(None, description="Sender ID"),
    db: AsyncSession = Depends(get_db)
):
    """Send notification to multiple users"""
    return await notification_service.send_bulk_notification(
        db, tenant_id, data, sender_id
    )


@router.post("/notifications/schedule", response_model=NotificationResponse)
async def schedule_notification(
    data: NotificationSend,
    scheduled_time: datetime = Query(..., description="When to send"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    user_id: UUID = Query(..., description="Target user ID"),
    sender_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Schedule a notification for later delivery"""
    return await notification_service.schedule_notification(
        db, tenant_id, user_id, data, scheduled_time, sender_id
    )


@router.get("/notifications", response_model=NotificationListResponse)
async def get_notifications(
    user_id: UUID = Query(..., description="User ID"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    unread_only: bool = Query(False),
    notification_type: Optional[NotificationTypeSchema] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db)
):
    """Get notifications for a user"""
    type_enum = NotificationType(notification_type.value) if notification_type else None
    return await notification_service.get_user_notifications(
        db, user_id, tenant_id, unread_only, type_enum, limit, offset
    )


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: UUID,
    user_id: UUID = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """Mark a notification as read"""
    await notification_service.mark_notification_read(db, notification_id, user_id)
    return {"status": "read"}


@router.post("/notifications/{notification_id}/click")
async def mark_notification_clicked(
    notification_id: UUID,
    user_id: UUID = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """Mark a notification as clicked"""
    await notification_service.mark_notification_clicked(db, notification_id, user_id)
    return {"status": "clicked"}


@router.post("/notifications/read-all")
async def mark_all_notifications_read(
    user_id: UUID = Query(..., description="User ID"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Mark all notifications as read"""
    count = await notification_service.mark_all_read(db, user_id, tenant_id)
    return {"status": "success", "marked_read": count}


@router.delete("/notifications/{notification_id}")
async def cancel_notification(
    notification_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Cancel a scheduled notification"""
    try:
        await notification_service.cancel_notification(db, notification_id, tenant_id)
        return {"status": "cancelled"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/notifications/preferences", response_model=NotificationPreferenceResponse)
async def get_notification_preferences(
    user_id: UUID = Query(..., description="User ID"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    device_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get notification preferences"""
    return await notification_service.get_preferences(db, user_id, tenant_id, device_id)


@router.put("/notifications/preferences", response_model=NotificationPreferenceResponse)
async def update_notification_preferences(
    data: NotificationPreferenceUpdate,
    user_id: UUID = Query(..., description="User ID"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    device_id: UUID = Query(..., description="Device ID"),
    db: AsyncSession = Depends(get_db)
):
    """Update notification preferences"""
    return await notification_service.update_preferences(
        db, user_id, tenant_id, device_id, data
    )


@router.get("/notifications/stats")
async def get_notification_stats(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Get notification delivery statistics"""
    return await notification_service.get_notification_stats(
        db, tenant_id, start_date, end_date
    )


# ============================================================================
# Sync Endpoints
# ============================================================================

@router.post("/sync/pull", response_model=SyncResponse)
async def sync_pull(
    data: SyncRequest,
    device_id: UUID = Query(..., description="Device ID"),
    user_id: UUID = Query(..., description="User ID"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Pull changes from server (delta sync)"""
    return await sync_service.pull_changes(db, device_id, user_id, tenant_id, data)


@router.post("/sync/push", response_model=SyncPushResult)
async def sync_push(
    data: SyncPush,
    device_id: UUID = Query(..., description="Device ID"),
    user_id: UUID = Query(..., description="User ID"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Push local changes to server"""
    return await sync_service.push_changes(db, device_id, user_id, tenant_id, data)


@router.post("/sync/conflicts/{conflict_id}/resolve")
async def resolve_sync_conflict(
    conflict_id: UUID,
    data: SyncConflictResolve,
    device_id: UUID = Query(..., description="Device ID"),
    db: AsyncSession = Depends(get_db)
):
    """Resolve a sync conflict"""
    try:
        return await sync_service.resolve_conflict(db, conflict_id, device_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sync/status", response_model=SyncStatusResponse)
async def get_sync_status(
    device_id: UUID = Query(..., description="Device ID"),
    user_id: UUID = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get current sync status"""
    return await sync_service.get_sync_status(db, device_id, user_id)


@router.post("/sync/reset")
async def reset_sync(
    device_id: UUID = Query(..., description="Device ID"),
    entity_types: Optional[List[str]] = Body(None, embed=True),
    db: AsyncSession = Depends(get_db)
):
    """Reset sync state (requires full re-sync)"""
    from modules.mobile.models import SyncEntityType
    types = [SyncEntityType(t) for t in entity_types] if entity_types else None
    await sync_service.reset_sync(db, device_id, types)
    return {"status": "reset"}


@router.get("/sync/full")
async def get_full_sync_data(
    user_id: UUID = Query(..., description="User ID"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    entity_types: List[str] = Query(...),
    page: int = Query(1),
    page_size: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db)
):
    """Get full data for initial sync"""
    from modules.mobile.models import SyncEntityType
    types = [SyncEntityType(t) for t in entity_types]
    return await sync_service.get_full_sync_data(
        db, user_id, tenant_id, types, page, page_size
    )


# ============================================================================
# Wearable Device Endpoints
# ============================================================================

@router.post("/wearables/connect", response_model=WearableResponse)
async def connect_wearable(
    data: WearableConnect,
    user_id: UUID = Query(..., description="User ID"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Connect a new wearable device"""
    return await wearable_service.connect_wearable(db, user_id, tenant_id, data)


@router.put("/wearables/{wearable_id}", response_model=WearableResponse)
async def update_wearable(
    wearable_id: UUID,
    data: WearableUpdate,
    user_id: UUID = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """Update wearable device information"""
    try:
        return await wearable_service.update_wearable(db, wearable_id, user_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/wearables/{wearable_id}/disconnect")
async def disconnect_wearable(
    wearable_id: UUID,
    user_id: UUID = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """Disconnect a wearable device"""
    try:
        await wearable_service.disconnect_wearable(db, wearable_id, user_id)
        return {"status": "disconnected"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/wearables/{wearable_id}", response_model=WearableResponse)
async def get_wearable(
    wearable_id: UUID,
    user_id: UUID = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get wearable device by ID"""
    try:
        return await wearable_service.get_wearable(db, wearable_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/wearables", response_model=WearableListResponse)
async def list_wearables(
    user_id: UUID = Query(..., description="User ID"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    """List all wearable devices for a user"""
    return await wearable_service.list_user_wearables(db, user_id, tenant_id, active_only)


@router.post("/wearables/{wearable_id}/sync")
async def sync_wearable(
    wearable_id: UUID,
    user_id: UUID = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """Sync data from wearable device"""
    try:
        return await wearable_service.sync_wearable_data(db, wearable_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Health Metrics Endpoints
# ============================================================================

@router.post("/health-metrics", response_model=HealthMetricResponse)
async def record_health_metric(
    data: HealthMetricRecord,
    user_id: UUID = Query(..., description="User ID"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Record a single health metric"""
    return await wearable_service.record_health_metric(db, user_id, tenant_id, data)


@router.post("/health-metrics/bulk", response_model=List[HealthMetricResponse])
async def record_bulk_metrics(
    data: HealthMetricBulkRecord,
    user_id: UUID = Query(..., description="User ID"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Record multiple health metrics at once"""
    return await wearable_service.record_bulk_metrics(db, user_id, tenant_id, data)


@router.get("/health-metrics", response_model=HealthMetricListResponse)
async def get_health_metrics(
    user_id: UUID = Query(..., description="User ID"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    metric_type: Optional[HealthMetricTypeSchema] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    wearable_id: Optional[UUID] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db)
):
    """Get health metrics for a user"""
    type_enum = HealthMetricType(metric_type.value) if metric_type else None
    return await wearable_service.get_health_metrics(
        db, user_id, tenant_id, type_enum, start_date, end_date, wearable_id, limit, offset
    )


@router.get("/health-metrics/summary", response_model=HealthMetricSummary)
async def get_metric_summary(
    user_id: UUID = Query(..., description="User ID"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    metric_type: HealthMetricTypeSchema = Query(...),
    period: str = Query("day", regex="^(day|week|month)$"),
    date_ref: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get summary statistics for a metric type"""
    return await wearable_service.get_metric_summary(
        db, user_id, tenant_id, HealthMetricType(metric_type.value), period, date_ref
    )


@router.get("/health-metrics/trends")
async def get_metric_trends(
    user_id: UUID = Query(..., description="User ID"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    metric_type: HealthMetricTypeSchema = Query(...),
    days: int = Query(7, le=90),
    db: AsyncSession = Depends(get_db)
):
    """Get daily trend data for a metric"""
    return await wearable_service.get_daily_trends(
        db, user_id, tenant_id, HealthMetricType(metric_type.value), days
    )


# ============================================================================
# Health Goals Endpoints
# ============================================================================

@router.post("/health-goals", response_model=HealthMetricGoalResponse)
async def create_health_goal(
    data: HealthMetricGoalCreate,
    user_id: UUID = Query(..., description="User ID"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Create a health metric goal"""
    return await wearable_service.create_health_goal(db, user_id, tenant_id, data)


@router.put("/health-goals/{goal_id}", response_model=HealthMetricGoalResponse)
async def update_health_goal(
    goal_id: UUID,
    data: dict = Body(...),
    user_id: UUID = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """Update a health goal"""
    try:
        return await wearable_service.update_health_goal(db, goal_id, user_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/health-goals/{goal_id}")
async def delete_health_goal(
    goal_id: UUID,
    user_id: UUID = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """Delete a health goal"""
    await wearable_service.delete_health_goal(db, goal_id, user_id)
    return {"status": "deleted"}


@router.get("/health-goals", response_model=List[HealthMetricGoalResponse])
async def get_health_goals(
    user_id: UUID = Query(..., description="User ID"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    """Get all health goals for a user"""
    return await wearable_service.get_user_goals(db, user_id, tenant_id, active_only)


@router.get("/health-goals/{goal_id}/progress")
async def get_goal_progress(
    goal_id: UUID,
    user_id: UUID = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get progress for a specific goal"""
    try:
        return await wearable_service.get_goal_progress(db, goal_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# App Analytics Endpoints
# ============================================================================

@router.post("/analytics/usage")
async def record_usage_event(
    data: AppUsageEventRecord,
    user_id: UUID = Query(..., description="User ID"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Record a single app usage event"""
    # Placeholder - would store usage event
    return {"status": "recorded"}


@router.post("/analytics/usage/batch")
async def record_usage_events_batch(
    data: AppUsageEventBatch,
    user_id: UUID = Query(..., description="User ID"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Record multiple app usage events"""
    # Placeholder - would store batch of events
    return {"status": "recorded", "count": len(data.events)}


@router.post("/analytics/crash")
async def report_crash(
    data: AppCrashReportCreate,
    user_id: UUID = Query(..., description="User ID"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Report an app crash"""
    # Placeholder - would store crash report
    return {"status": "reported"}


# ============================================================================
# App Version Endpoints
# ============================================================================

@router.post("/app/version-check", response_model=AppVersionResponse)
async def check_app_version(
    data: AppVersionCheck,
    db: AsyncSession = Depends(get_db)
):
    """Check if app needs update"""
    # Placeholder - would check against version config
    return AppVersionResponse(
        current_version=data.current_version,
        latest_version="2.0.0",
        min_required_version="1.5.0",
        update_available=True,
        update_required=False,
        update_url=f"https://{'apps.apple.com' if data.platform.value == 'ios' else 'play.google.com'}/app/healthcare",
        release_notes="Bug fixes and performance improvements"
    )


# ============================================================================
# Deep Link Endpoints
# ============================================================================

@router.post("/deeplinks/create", response_model=DeepLinkResponse)
async def create_deep_link(
    data: DeepLinkCreate,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Create a deep link"""
    # Generate deep link URL
    from urllib.parse import urlencode
    params = urlencode(data.params) if data.params else ""
    link_url = f"healthcare://{data.path}?{params}"

    return DeepLinkResponse(
        link_url=link_url,
        web_url=f"https://app.healthcare.com/{data.path}?{params}",
        expires_at=data.expires_at
    )


@router.post("/deeplinks/resolve", response_model=DeepLinkResolveResponse)
async def resolve_deep_link(
    data: DeepLinkResolve,
    db: AsyncSession = Depends(get_db)
):
    """Resolve a deep link"""
    # Parse and resolve deep link
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(data.link_url)

    return DeepLinkResolveResponse(
        path=parsed.path.lstrip("/"),
        params=dict(parse_qs(parsed.query)),
        is_valid=True
    )


# ============================================================================
# Storage Management Endpoints
# ============================================================================

@router.get("/storage/info", response_model=StorageInfoResponse)
async def get_storage_info(
    device_id: UUID = Query(..., description="Device ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get storage information for a device"""
    # Placeholder - would calculate actual storage
    return StorageInfoResponse(
        total_size_bytes=104857600,  # 100MB
        cache_size_bytes=20971520,   # 20MB
        offline_data_size_bytes=52428800,  # 50MB
        documents_size_bytes=31457280,  # 30MB
        last_cleanup_at=datetime.now()
    )


@router.post("/storage/clear-cache")
async def clear_cache(
    data: CacheClearRequest,
    device_id: UUID = Query(..., description="Device ID"),
    db: AsyncSession = Depends(get_db)
):
    """Clear device cache"""
    # Placeholder - would send command to clear cache
    return {"status": "cleared", "types": data.cache_types}
