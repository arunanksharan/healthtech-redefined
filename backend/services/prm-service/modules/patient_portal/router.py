"""
Patient Portal API Router
EPIC-014: FastAPI routes for patient portal operations
"""
from typing import List, Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database.connection import get_db
from modules.patient_portal.services import (
    AuthService,
    PatientPortalService,
    BillingService,
    PrescriptionService,
)
from modules.patient_portal.schemas import (
    # Auth
    RegisterRequest, RegisterResponse,
    LoginRequest, LoginResponse,
    RefreshTokenRequest, TokenResponse,
    PasswordChangeRequest, PasswordResetRequest, PasswordResetConfirm,
    MFASetupRequest, MFASetupResponse, MFAVerifyRequest,
    VerifyEmailRequest, VerifyPhoneRequest, SendVerificationRequest,
    # Profile
    PortalUserResponse, ProfileUpdateRequest,
    PatientProfileResponse, PatientProfileUpdateRequest,
    # Preferences
    PortalPreferencesResponse, PortalPreferencesUpdate,
    # Health Records
    HealthRecordResponse, LabResultResponse, HealthSummaryResponse,
    RecordFilter, RecordDownloadRequest, RecordShareRequest, RecordShareResponse,
    # Appointments
    AppointmentSearchRequest, AppointmentSearchResponse,
    AppointmentBookRequest, AppointmentResponse,
    AppointmentRescheduleRequest, AppointmentCancelRequest, AppointmentCheckInRequest,
    # Messaging
    MessageThreadCreate, MessageThreadResponse, MessageCreate, MessageResponse,
    MessageListResponse, MessageSearchRequest, MarkNotificationsRead,
    # Billing
    BillingSummaryResponse,
    PaymentMethodCreate, PaymentMethodResponse,
    PaymentRequest, PaymentResponse,
    PaymentPlanRequest, PaymentPlanResponse,
    PaymentHistoryResponse,
    # Prescriptions
    PrescriptionResponse, RefillRequest as RefillRequestSchema, RefillResponse,
    # Proxy Access
    ProxyAccessRequest, ProxyAccessResponse, ProxyAccessUpdate, ProxyAccessRevoke,
    ProxyPatientSummary,
    # Notifications
    NotificationResponse, NotificationListResponse,
    # Sessions
    SessionResponse, SessionListResponse, RevokeSessionRequest,
    # Dashboard
    DashboardResponse,
    # Common
    PaginationParams, MessageFolderEnum, MFAMethodEnum, RefillStatusEnum,
)
from modules.patient_portal.models import MFAMethod, MessageFolder, RefillStatus

router = APIRouter(prefix="/portal", tags=["Patient Portal"])
security = HTTPBearer()

# Service instances
auth_service = AuthService()
portal_service = PatientPortalService()
billing_service = BillingService()
prescription_service = PrescriptionService()


# ==================== Dependency Functions ====================

def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def get_user_agent(request: Request) -> str:
    """Extract user agent from request"""
    return request.headers.get("User-Agent", "")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Validate JWT token and return user info"""
    try:
        payload = auth_service.decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        return {
            "user_id": UUID(payload["sub"]),
            "tenant_id": UUID(payload["tenant_id"]),
            "token": credentials.credentials
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


# ==================== Authentication Routes ====================

@router.post("/auth/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    req: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """Register new patient portal account"""
    try:
        return await auth_service.register(
            db, tenant_id, request,
            ip_address=get_client_ip(req),
            user_agent=get_user_agent(req)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/auth/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    req: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """Login to patient portal"""
    try:
        return await auth_service.login(
            db, tenant_id, request,
            ip_address=get_client_ip(req),
            user_agent=get_user_agent(req)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    req: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token"""
    try:
        return await auth_service.refresh_tokens(
            db, request.refresh_token,
            ip_address=get_client_ip(req)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    req: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Logout from patient portal"""
    await auth_service.logout(
        db,
        current_user["user_id"],
        current_user["tenant_id"],
        current_user["token"],
        ip_address=get_client_ip(req),
        user_agent=get_user_agent(req)
    )


@router.post("/auth/password/change", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    request: PasswordChangeRequest,
    req: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change password"""
    # Implementation would be added to auth_service
    pass


@router.post("/auth/password/reset", status_code=status.HTTP_204_NO_CONTENT)
async def request_password_reset(
    request: PasswordResetRequest,
    tenant_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Request password reset"""
    await auth_service.initiate_password_reset(db, tenant_id, request.email)


@router.post("/auth/password/reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_password_reset(
    request: PasswordResetConfirm,
    req: Request,
    db: AsyncSession = Depends(get_db)
):
    """Confirm password reset"""
    try:
        await auth_service.reset_password(
            db, request.token, request.new_password,
            ip_address=get_client_ip(req),
            user_agent=get_user_agent(req)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/auth/verify/email", status_code=status.HTTP_204_NO_CONTENT)
async def verify_email(
    request: VerifyEmailRequest,
    req: Request,
    db: AsyncSession = Depends(get_db)
):
    """Verify email address"""
    try:
        await auth_service.verify_email(db, request.token, ip_address=get_client_ip(req))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================== MFA Routes ====================

@router.post("/auth/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(
    request: MFASetupRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Setup multi-factor authentication"""
    try:
        return await auth_service.setup_mfa(
            db,
            current_user["user_id"],
            current_user["tenant_id"],
            MFAMethod(request.method.value)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/auth/mfa/verify", status_code=status.HTTP_204_NO_CONTENT)
async def verify_mfa(
    request: MFAVerifyRequest,
    req: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Verify and enable MFA"""
    try:
        await auth_service.verify_and_enable_mfa(
            db,
            current_user["user_id"],
            current_user["tenant_id"],
            request.code,
            ip_address=get_client_ip(req),
            user_agent=get_user_agent(req)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/auth/mfa", status_code=status.HTTP_204_NO_CONTENT)
async def disable_mfa(
    password: str = Query(..., description="Current password for verification"),
    req: Request = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Disable MFA"""
    try:
        await auth_service.disable_mfa(
            db,
            current_user["user_id"],
            current_user["tenant_id"],
            password,
            ip_address=get_client_ip(req),
            user_agent=get_user_agent(req)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================== Profile Routes ====================

@router.get("/profile", response_model=PatientProfileResponse)
async def get_profile(
    patient_id: Optional[UUID] = Query(None, description="Patient ID for proxy access"),
    req: Request = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get patient profile"""
    try:
        return await portal_service.get_patient_profile(
            db,
            current_user["user_id"],
            current_user["tenant_id"],
            patient_id,
            ip_address=get_client_ip(req)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/profile", response_model=PatientProfileResponse)
async def update_profile(
    request: PatientProfileUpdateRequest,
    req: Request = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update patient profile"""
    try:
        return await portal_service.update_patient_profile(
            db,
            current_user["user_id"],
            current_user["tenant_id"],
            request,
            ip_address=get_client_ip(req)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================== Preferences Routes ====================

@router.get("/preferences", response_model=PortalPreferencesResponse)
async def get_preferences(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user preferences"""
    try:
        return await portal_service.get_preferences(db, current_user["user_id"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/preferences", response_model=PortalPreferencesResponse)
async def update_preferences(
    request: PortalPreferencesUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user preferences"""
    return await portal_service.update_preferences(db, current_user["user_id"], request)


# ==================== Health Records Routes ====================

@router.get("/health-records", response_model=List[HealthRecordResponse])
async def get_health_records(
    record_type: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    patient_id: Optional[UUID] = Query(None, description="Patient ID for proxy access"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    req: Request = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get patient health records"""
    filters = RecordFilter(
        record_type=record_type,
        date_from=date_from,
        date_to=date_to
    )
    records, _ = await portal_service.get_health_records(
        db,
        current_user["user_id"],
        current_user["tenant_id"],
        patient_id,
        filters,
        page,
        page_size,
        ip_address=get_client_ip(req)
    )
    return records


@router.get("/health-records/lab-results", response_model=List[LabResultResponse])
async def get_lab_results(
    test_type: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    patient_id: Optional[UUID] = Query(None),
    req: Request = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get lab results with trending"""
    return await portal_service.get_lab_results(
        db,
        current_user["user_id"],
        current_user["tenant_id"],
        patient_id,
        test_type,
        date_from,
        date_to,
        ip_address=get_client_ip(req)
    )


@router.get("/health-records/summary", response_model=HealthSummaryResponse)
async def get_health_summary(
    patient_id: Optional[UUID] = Query(None),
    req: Request = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get health summary"""
    return await portal_service.get_health_summary(
        db,
        current_user["user_id"],
        current_user["tenant_id"],
        patient_id,
        ip_address=get_client_ip(req)
    )


@router.post("/health-records/share", response_model=RecordShareResponse)
async def share_records(
    request: RecordShareRequest,
    req: Request = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create shareable link for health records"""
    return await portal_service.share_records(
        db,
        current_user["user_id"],
        current_user["tenant_id"],
        request,
        ip_address=get_client_ip(req)
    )


# ==================== Messaging Routes ====================

@router.get("/messages", response_model=MessageListResponse)
async def get_messages(
    folder: Optional[MessageFolderEnum] = Query(None),
    is_unread: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get message threads"""
    return await portal_service.get_message_threads(
        db,
        current_user["user_id"],
        current_user["tenant_id"],
        MessageFolder(folder.value) if folder else None,
        is_unread,
        page,
        page_size
    )


@router.post("/messages", response_model=MessageThreadResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    request: MessageThreadCreate,
    req: Request = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new message thread"""
    return await portal_service.create_message_thread(
        db,
        current_user["user_id"],
        current_user["tenant_id"],
        request,
        ip_address=get_client_ip(req)
    )


@router.get("/messages/{thread_id}", response_model=List[MessageResponse])
async def get_thread_messages(
    thread_id: UUID,
    req: Request = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get messages in thread"""
    try:
        return await portal_service.get_thread_messages(
            db,
            current_user["user_id"],
            current_user["tenant_id"],
            thread_id,
            ip_address=get_client_ip(req)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/messages/{thread_id}/reply", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def reply_to_message(
    thread_id: UUID,
    request: MessageCreate,
    req: Request = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reply to message thread"""
    try:
        return await portal_service.reply_to_thread(
            db,
            current_user["user_id"],
            current_user["tenant_id"],
            thread_id,
            request,
            ip_address=get_client_ip(req)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================== Notifications Routes ====================

@router.get("/notifications", response_model=NotificationListResponse)
async def get_notifications(
    is_read: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get notifications"""
    return await portal_service.get_notifications(
        db,
        current_user["user_id"],
        is_read,
        page,
        page_size
    )


@router.post("/notifications/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_notifications_read(
    request: MarkNotificationsRead,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark notifications as read"""
    await portal_service.mark_notifications_read(
        db,
        current_user["user_id"],
        request.notification_ids,
        request.mark_all
    )


# ==================== Billing Routes ====================

@router.get("/billing/summary", response_model=BillingSummaryResponse)
async def get_billing_summary(
    patient_id: Optional[UUID] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get billing summary"""
    return await billing_service.get_billing_summary(
        db,
        current_user["user_id"],
        current_user["tenant_id"],
        patient_id
    )


@router.get("/billing/payment-methods", response_model=List[PaymentMethodResponse])
async def get_payment_methods(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get saved payment methods"""
    return await billing_service.get_payment_methods(db, current_user["user_id"])


@router.post("/billing/payment-methods", response_model=PaymentMethodResponse, status_code=status.HTTP_201_CREATED)
async def add_payment_method(
    request: PaymentMethodCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add payment method"""
    return await billing_service.add_payment_method(
        db,
        current_user["user_id"],
        current_user["tenant_id"],
        request
    )


@router.delete("/billing/payment-methods/{method_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment_method(
    method_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete payment method"""
    try:
        await billing_service.delete_payment_method(db, current_user["user_id"], method_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/billing/payment-methods/{method_id}/default", status_code=status.HTTP_204_NO_CONTENT)
async def set_default_payment_method(
    method_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Set default payment method"""
    await billing_service.set_default_payment_method(db, current_user["user_id"], method_id)


@router.post("/billing/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def make_payment(
    request: PaymentRequest,
    req: Request = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Make a payment"""
    try:
        return await billing_service.process_payment(
            db,
            current_user["user_id"],
            current_user["tenant_id"],
            request,
            ip_address=get_client_ip(req)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/billing/payments/history", response_model=PaymentHistoryResponse)
async def get_payment_history(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get payment history"""
    return await billing_service.get_payment_history(
        db,
        current_user["user_id"],
        page,
        page_size,
        date_from,
        date_to
    )


@router.get("/billing/payment-plans", response_model=List[PaymentPlanResponse])
async def get_payment_plans(
    active_only: bool = Query(True),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get payment plans"""
    return await billing_service.get_payment_plans(db, current_user["user_id"], active_only)


@router.post("/billing/payment-plans", response_model=PaymentPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_payment_plan(
    request: PaymentPlanRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create payment plan"""
    return await billing_service.create_payment_plan(
        db,
        current_user["user_id"],
        current_user["tenant_id"],
        request
    )


@router.delete("/billing/payment-plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_payment_plan(
    plan_id: UUID,
    reason: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel payment plan"""
    try:
        await billing_service.cancel_payment_plan(db, current_user["user_id"], plan_id, reason)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================== Prescription Routes ====================

@router.get("/prescriptions", response_model=List[PrescriptionResponse])
async def get_prescriptions(
    active_only: bool = Query(True),
    patient_id: Optional[UUID] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get prescriptions"""
    return await prescription_service.get_prescriptions(
        db,
        current_user["user_id"],
        current_user["tenant_id"],
        patient_id,
        active_only
    )


@router.post("/prescriptions/refill", response_model=RefillResponse, status_code=status.HTTP_201_CREATED)
async def request_refill(
    request: RefillRequestSchema,
    req: Request = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Request prescription refill"""
    return await prescription_service.request_refill(
        db,
        current_user["user_id"],
        current_user["tenant_id"],
        request,
        ip_address=get_client_ip(req)
    )


@router.get("/prescriptions/refills", response_model=List[RefillResponse])
async def get_refill_requests(
    status: Optional[RefillStatusEnum] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get refill requests"""
    return await prescription_service.get_refill_requests(
        db,
        current_user["user_id"],
        current_user["tenant_id"],
        RefillStatus(status.value) if status else None,
        page,
        page_size
    )


@router.get("/prescriptions/refills/{refill_id}", response_model=RefillResponse)
async def get_refill_status(
    refill_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get refill request status"""
    try:
        return await prescription_service.get_refill_status(
            db,
            current_user["user_id"],
            refill_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/prescriptions/refills/{refill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_refill(
    refill_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel refill request"""
    try:
        await prescription_service.cancel_refill_request(
            db,
            current_user["user_id"],
            refill_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================== Proxy Access Routes ====================

@router.get("/proxy-accounts", response_model=List[ProxyPatientSummary])
async def get_proxy_accounts(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get accounts user has proxy access to"""
    return await portal_service.get_proxy_accounts(
        db,
        current_user["user_id"],
        current_user["tenant_id"]
    )


@router.post("/proxy-access", response_model=ProxyAccessResponse, status_code=status.HTTP_201_CREATED)
async def grant_proxy_access(
    request: ProxyAccessRequest,
    req: Request = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Grant proxy access to another user"""
    try:
        return await portal_service.grant_proxy_access(
            db,
            current_user["user_id"],
            current_user["tenant_id"],
            request,
            ip_address=get_client_ip(req)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/proxy-access/{proxy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_proxy_access(
    proxy_id: UUID,
    reason: Optional[str] = Query(None),
    req: Request = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Revoke proxy access"""
    try:
        await portal_service.revoke_proxy_access(
            db,
            current_user["user_id"],
            current_user["tenant_id"],
            proxy_id,
            reason,
            ip_address=get_client_ip(req)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ==================== Session Management Routes ====================

@router.get("/sessions", response_model=SessionListResponse)
async def get_active_sessions(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get active sessions"""
    sessions = await auth_service.get_active_sessions(
        db,
        current_user["user_id"],
        current_user["token"]
    )
    return SessionListResponse(
        sessions=[
            SessionResponse(
                id=s["id"],
                device_type=s.get("device_type"),
                device_name=s.get("device_name"),
                browser=s.get("browser"),
                os=s.get("os"),
                ip_address=str(s.get("ip_address")) if s.get("ip_address") else None,
                location=s.get("location"),
                is_current=s.get("is_current", False),
                created_at=s["created_at"],
                last_activity_at=s["last_activity_at"]
            )
            for s in sessions
        ],
        total_count=len(sessions)
    )


@router.post("/sessions/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_sessions(
    request: RevokeSessionRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Revoke sessions"""
    if request.revoke_all_except_current:
        await auth_service.revoke_all_sessions_except_current(
            db,
            current_user["user_id"],
            current_user["token"]
        )
    elif request.session_id:
        await auth_service.revoke_session(
            db,
            current_user["user_id"],
            request.session_id
        )
