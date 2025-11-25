"""
Security Router

FastAPI router for EPIC-021: Security Hardening
Provides endpoints for MFA, Session, RBAC, Encryption, Monitoring, and Vulnerability Management.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from shared.database import get_db

from modules.security.models import (
    MFAMethod,
    ThreatSeverity,
    ThreatType,
    IncidentStatus,
    VulnerabilitySeverity,
    VulnerabilityStatus,
    ScanType,
    KeyType,
    ResourceType,
    PermissionAction,
)
from modules.security.schemas import (
    # MFA
    MFATOTPEnrollRequest,
    MFATOTPEnrollResponse,
    MFATOTPVerifyRequest,
    MFATOTPVerifyResponse,
    MFASMSEnrollRequest,
    MFASMSEnrollResponse,
    MFAVerifyCodeRequest,
    WebAuthnRegistrationOptionsResponse,
    WebAuthnRegistrationRequest,
    WebAuthnAuthenticationRequest,
    MFAEnrollmentResponse,
    MFAPolicyCreate,
    MFAPolicyResponse,
    MFARequirementCheck,
    # Session
    SessionCreateResponse,
    SessionRefreshRequest,
    SessionResponse,
    SessionRevokeRequest,
    SessionPolicyCreate,
    SessionPolicyResponse,
    SessionAnalyticsResponse,
    # RBAC
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    PermissionCreate,
    PermissionResponse,
    RolePermissionAssign,
    UserRoleAssign,
    UserRoleResponse,
    PermissionCheckRequest,
    PermissionCheckResponse,
    BreakGlassRequest,
    BreakGlassResponse,
    BreakGlassReview,
    # Encryption
    EncryptionKeyCreate,
    EncryptionKeyResponse,
    FieldEncryptionConfigCreate,
    FieldEncryptionConfigResponse,
    CertificateCreate,
    CertificateResponse,
    EncryptionStatusResponse,
    # Monitoring
    SecurityEventCreate,
    SecurityEventResponse,
    ThreatDetectionRuleCreate,
    ThreatDetectionRuleResponse,
    SecurityIncidentCreate,
    SecurityIncidentResponse,
    IncidentStatusUpdate,
    IncidentResponseCreate,
    IncidentClose,
    SecurityDashboardResponse,
    AuditLogResponse,
    # Vulnerability
    VulnerabilityCreate,
    VulnerabilityResponse,
    VulnerabilityStatusUpdate,
    SecurityScanCreate,
    SecurityScanResponse,
    SecurityScanComplete,
    VulnerabilityDashboardResponse,
    SLAComplianceResponse,
    TopVulnerableComponent,
    # Common
    SuccessResponse,
    ErrorResponse,
)
from modules.security.services import (
    MFAService,
    SessionService,
    RBACService,
    EncryptionService,
    SecurityMonitoringService,
    VulnerabilityService,
)


router = APIRouter(prefix="/security", tags=["Security"])


# =============================================================================
# Helper Functions
# =============================================================================

def get_tenant_id(request: Request) -> UUID:
    """Extract tenant_id from request context"""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        # Default for development
        return UUID("00000000-0000-0000-0000-000000000001")
    return tenant_id


def get_user_id(request: Request) -> UUID:
    """Extract user_id from request context"""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        # Default for development
        return UUID("00000000-0000-0000-0000-000000000001")
    return user_id


def get_client_ip(request: Request) -> str:
    """Get client IP address"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# =============================================================================
# MFA Endpoints
# =============================================================================

@router.post("/mfa/totp/enroll", response_model=MFATOTPEnrollResponse)
async def enroll_totp(
    request: Request,
    body: MFATOTPEnrollRequest,
    db: Session = Depends(get_db),
):
    """Start TOTP enrollment"""
    service = MFAService(db)
    try:
        result = service.enroll_totp(
            tenant_id=get_tenant_id(request),
            user_id=get_user_id(request),
            device_name=body.device_name,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/mfa/totp/verify", response_model=MFATOTPVerifyResponse)
async def verify_totp_enrollment(
    request: Request,
    body: MFATOTPVerifyRequest,
    db: Session = Depends(get_db),
):
    """Verify TOTP enrollment with code"""
    service = MFAService(db)
    try:
        result = service.verify_totp_enrollment(
            tenant_id=get_tenant_id(request),
            user_id=get_user_id(request),
            code=body.code,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/mfa/totp/authenticate", response_model=SuccessResponse)
async def authenticate_totp(
    request: Request,
    body: MFAVerifyCodeRequest,
    db: Session = Depends(get_db),
):
    """Verify TOTP code for authentication"""
    service = MFAService(db)
    if service.verify_totp(
        tenant_id=get_tenant_id(request),
        user_id=get_user_id(request),
        code=body.code,
    ):
        return SuccessResponse(message="TOTP verification successful")
    raise HTTPException(status_code=401, detail="Invalid TOTP code")


@router.post("/mfa/sms/enroll", response_model=MFASMSEnrollResponse)
async def enroll_sms(
    request: Request,
    body: MFASMSEnrollRequest,
    db: Session = Depends(get_db),
):
    """Start SMS MFA enrollment"""
    service = MFAService(db)
    try:
        result = service.enroll_sms(
            tenant_id=get_tenant_id(request),
            user_id=get_user_id(request),
            phone_number=body.phone_number,
            ip_address=get_client_ip(request),
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/mfa/sms/verify", response_model=SuccessResponse)
async def verify_sms_enrollment(
    request: Request,
    body: MFAVerifyCodeRequest,
    db: Session = Depends(get_db),
):
    """Verify SMS enrollment code"""
    service = MFAService(db)
    try:
        service.verify_sms_enrollment(
            tenant_id=get_tenant_id(request),
            user_id=get_user_id(request),
            code=body.code,
        )
        return SuccessResponse(message="SMS MFA enabled successfully")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/mfa/sms/send", response_model=SuccessResponse)
async def send_sms_code(
    request: Request,
    db: Session = Depends(get_db),
):
    """Send SMS code for authentication"""
    service = MFAService(db)
    try:
        result = service.send_sms_code(
            tenant_id=get_tenant_id(request),
            user_id=get_user_id(request),
        )
        return SuccessResponse(message=result["message"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/mfa/sms/authenticate", response_model=SuccessResponse)
async def authenticate_sms(
    request: Request,
    body: MFAVerifyCodeRequest,
    db: Session = Depends(get_db),
):
    """Verify SMS code for authentication"""
    service = MFAService(db)
    if service.verify_sms(
        tenant_id=get_tenant_id(request),
        user_id=get_user_id(request),
        code=body.code,
    ):
        return SuccessResponse(message="SMS verification successful")
    raise HTTPException(status_code=401, detail="Invalid SMS code")


@router.post("/mfa/webauthn/register/options", response_model=WebAuthnRegistrationOptionsResponse)
async def webauthn_register_options(
    request: Request,
    db: Session = Depends(get_db),
):
    """Get WebAuthn registration options"""
    service = MFAService(db)
    # In production, get username from authenticated user
    result = service.start_webauthn_registration(
        tenant_id=get_tenant_id(request),
        user_id=get_user_id(request),
        username="user@example.com",
    )
    return result


@router.post("/mfa/webauthn/register", response_model=SuccessResponse)
async def webauthn_register(
    request: Request,
    body: WebAuthnRegistrationRequest,
    db: Session = Depends(get_db),
):
    """Complete WebAuthn registration"""
    service = MFAService(db)
    try:
        result = service.complete_webauthn_registration(
            tenant_id=get_tenant_id(request),
            user_id=get_user_id(request),
            credential=body.credential,
            device_name=body.device_name,
            ip_address=get_client_ip(request),
        )
        return SuccessResponse(message=result["message"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/mfa/webauthn/authenticate", response_model=SuccessResponse)
async def webauthn_authenticate(
    request: Request,
    body: WebAuthnAuthenticationRequest,
    db: Session = Depends(get_db),
):
    """Verify WebAuthn authentication"""
    service = MFAService(db)
    if service.verify_webauthn(
        tenant_id=get_tenant_id(request),
        user_id=get_user_id(request),
        assertion=body.assertion,
    ):
        return SuccessResponse(message="WebAuthn verification successful")
    raise HTTPException(status_code=401, detail="WebAuthn verification failed")


@router.post("/mfa/backup-code/verify", response_model=SuccessResponse)
async def verify_backup_code(
    request: Request,
    body: MFAVerifyCodeRequest,
    db: Session = Depends(get_db),
):
    """Verify backup code"""
    service = MFAService(db)
    if service.verify_backup_code(
        tenant_id=get_tenant_id(request),
        user_id=get_user_id(request),
        code=body.code,
    ):
        return SuccessResponse(message="Backup code verified")
    raise HTTPException(status_code=401, detail="Invalid backup code")


@router.post("/mfa/backup-codes/regenerate")
async def regenerate_backup_codes(
    request: Request,
    db: Session = Depends(get_db),
):
    """Regenerate backup codes"""
    service = MFAService(db)
    codes = service.regenerate_backup_codes(
        tenant_id=get_tenant_id(request),
        user_id=get_user_id(request),
    )
    return {"backup_codes": codes}


@router.get("/mfa/enrollments", response_model=List[MFAEnrollmentResponse])
async def list_mfa_enrollments(
    request: Request,
    db: Session = Depends(get_db),
):
    """Get all MFA enrollments for current user"""
    service = MFAService(db)
    enrollments = service.get_enrollments(
        tenant_id=get_tenant_id(request),
        user_id=get_user_id(request),
    )
    return enrollments


@router.delete("/mfa/enrollments/{enrollment_id}")
async def disable_mfa_enrollment(
    request: Request,
    enrollment_id: UUID,
    db: Session = Depends(get_db),
):
    """Disable an MFA enrollment"""
    service = MFAService(db)
    try:
        result = service.disable_enrollment(
            tenant_id=get_tenant_id(request),
            user_id=get_user_id(request),
            enrollment_id=enrollment_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/mfa/policies", response_model=MFAPolicyResponse)
async def create_mfa_policy(
    request: Request,
    body: MFAPolicyCreate,
    db: Session = Depends(get_db),
):
    """Create MFA policy"""
    service = MFAService(db)
    policy = service.create_policy(
        tenant_id=get_tenant_id(request),
        created_by=get_user_id(request),
        **body.model_dump(),
    )
    return policy


@router.get("/mfa/policies/active", response_model=Optional[MFAPolicyResponse])
async def get_active_mfa_policy(
    request: Request,
    db: Session = Depends(get_db),
):
    """Get active MFA policy"""
    service = MFAService(db)
    return service.get_active_policy(get_tenant_id(request))


@router.post("/mfa/check-required", response_model=MFARequirementCheck)
async def check_mfa_required(
    request: Request,
    roles: List[str] = Query(default=[]),
    accessing_phi: bool = False,
    is_admin_action: bool = False,
    is_new_device: bool = False,
    db: Session = Depends(get_db),
):
    """Check if MFA is required for context"""
    service = MFAService(db)
    return service.check_mfa_required(
        tenant_id=get_tenant_id(request),
        user_id=get_user_id(request),
        roles=roles,
        accessing_phi=accessing_phi,
        is_admin_action=is_admin_action,
        is_new_device=is_new_device,
    )


# =============================================================================
# Session Endpoints
# =============================================================================

@router.post("/sessions/refresh", response_model=SessionCreateResponse)
async def refresh_session(
    request: Request,
    body: SessionRefreshRequest,
    db: Session = Depends(get_db),
):
    """Refresh session with refresh token"""
    service = SessionService(db)
    try:
        result = service.refresh_session(
            refresh_token=body.refresh_token,
            ip_address=get_client_ip(request),
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/sessions", response_model=List[SessionResponse])
async def list_active_sessions(
    request: Request,
    db: Session = Depends(get_db),
):
    """Get all active sessions for current user"""
    service = SessionService(db)
    return service.get_active_sessions(
        tenant_id=get_tenant_id(request),
        user_id=get_user_id(request),
    )


@router.get("/sessions/history", response_model=List[SessionResponse])
async def get_session_history(
    request: Request,
    limit: int = Query(default=50, le=100),
    db: Session = Depends(get_db),
):
    """Get session history for current user"""
    service = SessionService(db)
    return service.get_session_history(
        tenant_id=get_tenant_id(request),
        user_id=get_user_id(request),
        limit=limit,
    )


@router.post("/sessions/revoke", response_model=SuccessResponse)
async def revoke_session(
    request: Request,
    body: SessionRevokeRequest,
    db: Session = Depends(get_db),
):
    """Revoke a specific session"""
    service = SessionService(db)
    if service.revoke_session(body.session_id, body.reason):
        return SuccessResponse(message="Session revoked")
    raise HTTPException(status_code=404, detail="Session not found")


@router.post("/sessions/revoke-all", response_model=SuccessResponse)
async def revoke_all_sessions(
    request: Request,
    except_current: bool = True,
    db: Session = Depends(get_db),
):
    """Revoke all sessions (logout everywhere)"""
    service = SessionService(db)
    current_session = getattr(request.state, "session_id", None)
    count = service.revoke_all_sessions(
        tenant_id=get_tenant_id(request),
        user_id=get_user_id(request),
        except_session_id=current_session if except_current else None,
        reason="User-initiated logout all",
    )
    return SuccessResponse(message=f"{count} sessions revoked")


@router.post("/sessions/policies", response_model=SessionPolicyResponse)
async def create_session_policy(
    request: Request,
    body: SessionPolicyCreate,
    db: Session = Depends(get_db),
):
    """Create session policy"""
    service = SessionService(db)
    return service.create_policy(
        tenant_id=get_tenant_id(request),
        **body.model_dump(),
    )


@router.get("/sessions/analytics", response_model=SessionAnalyticsResponse)
async def get_session_analytics(
    request: Request,
    days: int = Query(default=30, le=90),
    db: Session = Depends(get_db),
):
    """Get session analytics"""
    service = SessionService(db)
    return service.get_session_analytics(
        tenant_id=get_tenant_id(request),
        days=days,
    )


# =============================================================================
# RBAC Endpoints
# =============================================================================

@router.post("/roles", response_model=RoleResponse)
async def create_role(
    request: Request,
    body: RoleCreate,
    db: Session = Depends(get_db),
):
    """Create a new role"""
    service = RBACService(db)
    try:
        return service.create_role(
            tenant_id=get_tenant_id(request),
            created_by=get_user_id(request),
            **body.model_dump(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/roles", response_model=List[RoleResponse])
async def list_roles(
    request: Request,
    include_system: bool = True,
    db: Session = Depends(get_db),
):
    """List all roles"""
    service = RBACService(db)
    return service.list_roles(
        tenant_id=get_tenant_id(request),
        include_system=include_system,
    )


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: UUID,
    db: Session = Depends(get_db),
):
    """Get role by ID"""
    service = RBACService(db)
    role = service.get_role(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.patch("/roles/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: UUID,
    body: RoleUpdate,
    db: Session = Depends(get_db),
):
    """Update role"""
    service = RBACService(db)
    try:
        role = service.update_role(role_id, **body.model_dump(exclude_unset=True))
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        return role
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/roles/{role_id}", response_model=SuccessResponse)
async def delete_role(
    role_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete role"""
    service = RBACService(db)
    try:
        if service.delete_role(role_id):
            return SuccessResponse(message="Role deleted")
        raise HTTPException(status_code=404, detail="Role not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/roles/{role_id}/permissions", response_model=SuccessResponse)
async def assign_permission_to_role(
    request: Request,
    role_id: UUID,
    body: RolePermissionAssign,
    db: Session = Depends(get_db),
):
    """Assign permission to role"""
    service = RBACService(db)
    try:
        service.assign_permission_to_role(
            role_id=role_id,
            permission_id=body.permission_id,
            granted_by=get_user_id(request),
            conditions_override=body.conditions_override,
        )
        return SuccessResponse(message="Permission assigned")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/roles/{role_id}/permissions/{permission_id}", response_model=SuccessResponse)
async def revoke_permission_from_role(
    role_id: UUID,
    permission_id: UUID,
    db: Session = Depends(get_db),
):
    """Revoke permission from role"""
    service = RBACService(db)
    if service.revoke_permission_from_role(role_id, permission_id):
        return SuccessResponse(message="Permission revoked")
    raise HTTPException(status_code=404, detail="Assignment not found")


@router.get("/permissions", response_model=List[PermissionResponse])
async def list_permissions(
    resource_type: Optional[ResourceType] = None,
    db: Session = Depends(get_db),
):
    """List all permissions"""
    service = RBACService(db)
    return service.list_permissions(resource_type=resource_type)


@router.post("/permissions", response_model=PermissionResponse)
async def create_permission(
    body: PermissionCreate,
    db: Session = Depends(get_db),
):
    """Create a new permission"""
    service = RBACService(db)
    return service.create_permission(**body.model_dump())


@router.post("/users/{user_id}/roles", response_model=SuccessResponse)
async def assign_role_to_user(
    request: Request,
    user_id: UUID,
    body: UserRoleAssign,
    db: Session = Depends(get_db),
):
    """Assign role to user"""
    service = RBACService(db)
    try:
        service.assign_role_to_user(
            tenant_id=get_tenant_id(request),
            user_id=user_id,
            assigned_by=get_user_id(request),
            **body.model_dump(),
        )
        return SuccessResponse(message="Role assigned")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users/{user_id}/roles", response_model=List[UserRoleResponse])
async def get_user_roles(
    request: Request,
    user_id: UUID,
    db: Session = Depends(get_db),
):
    """Get user roles"""
    service = RBACService(db)
    return service.get_user_roles(
        tenant_id=get_tenant_id(request),
        user_id=user_id,
    )


@router.delete("/users/{user_id}/roles/{user_role_id}", response_model=SuccessResponse)
async def revoke_role_from_user(
    user_role_id: UUID,
    db: Session = Depends(get_db),
):
    """Revoke role from user"""
    service = RBACService(db)
    if service.revoke_role_from_user(user_role_id):
        return SuccessResponse(message="Role revoked")
    raise HTTPException(status_code=404, detail="Assignment not found")


@router.post("/check-permission", response_model=PermissionCheckResponse)
async def check_permission(
    request: Request,
    body: PermissionCheckRequest,
    db: Session = Depends(get_db),
):
    """Check if current user has permission"""
    service = RBACService(db)
    return service.check_permission(
        tenant_id=get_tenant_id(request),
        user_id=get_user_id(request),
        resource_type=body.resource_type,
        action=body.action,
        resource_id=body.resource_id,
        scope_context=body.scope_context,
    )


@router.get("/users/{user_id}/permissions")
async def get_user_permissions(
    request: Request,
    user_id: UUID,
    db: Session = Depends(get_db),
):
    """Get all permissions for user"""
    service = RBACService(db)
    return service.get_user_permissions(
        tenant_id=get_tenant_id(request),
        user_id=user_id,
    )


@router.post("/break-glass", response_model=BreakGlassResponse)
async def create_break_glass_access(
    request: Request,
    body: BreakGlassRequest,
    db: Session = Depends(get_db),
):
    """Create emergency break-the-glass access"""
    service = RBACService(db)
    return service.create_break_glass_access(
        tenant_id=get_tenant_id(request),
        user_id=get_user_id(request),
        patient_id=body.patient_id,
        reason=body.reason,
        emergency_type=body.emergency_type,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )


@router.post("/break-glass/{access_id}/end", response_model=SuccessResponse)
async def end_break_glass_access(
    access_id: UUID,
    db: Session = Depends(get_db),
):
    """End break-the-glass access session"""
    service = RBACService(db)
    if service.end_break_glass_access(access_id):
        return SuccessResponse(message="Break-the-glass access ended")
    raise HTTPException(status_code=404, detail="Access not found")


@router.post("/break-glass/{access_id}/review", response_model=SuccessResponse)
async def review_break_glass_access(
    request: Request,
    access_id: UUID,
    body: BreakGlassReview,
    db: Session = Depends(get_db),
):
    """Review break-the-glass access"""
    service = RBACService(db)
    if service.review_break_glass_access(
        access_id=access_id,
        reviewed_by=get_user_id(request),
        outcome=body.outcome,
        notes=body.notes,
    ):
        return SuccessResponse(message="Review recorded")
    raise HTTPException(status_code=404, detail="Access not found")


@router.get("/break-glass/pending")
async def get_pending_break_glass_reviews(
    request: Request,
    db: Session = Depends(get_db),
):
    """Get pending break-the-glass reviews"""
    service = RBACService(db)
    return service.get_pending_break_glass_reviews(get_tenant_id(request))


@router.post("/roles/initialize-system", response_model=SuccessResponse)
async def initialize_system_roles(
    db: Session = Depends(get_db),
):
    """Initialize predefined healthcare roles"""
    service = RBACService(db)
    count = service.initialize_system_roles()
    return SuccessResponse(message=f"Initialized {count} system roles")


# =============================================================================
# Encryption Endpoints
# =============================================================================

@router.post("/encryption/keys", response_model=EncryptionKeyResponse)
async def create_encryption_key(
    request: Request,
    body: EncryptionKeyCreate,
    db: Session = Depends(get_db),
):
    """Create encryption key"""
    service = EncryptionService(db)
    return service.create_key(
        tenant_id=get_tenant_id(request),
        created_by=get_user_id(request),
        **body.model_dump(),
    )


@router.get("/encryption/keys", response_model=List[EncryptionKeyResponse])
async def list_encryption_keys(
    request: Request,
    key_type: Optional[KeyType] = None,
    db: Session = Depends(get_db),
):
    """List encryption keys"""
    service = EncryptionService(db)
    return service.list_keys(
        tenant_id=get_tenant_id(request),
        key_type=key_type,
    )


@router.get("/encryption/keys/{key_id}", response_model=EncryptionKeyResponse)
async def get_encryption_key(
    key_id: UUID,
    db: Session = Depends(get_db),
):
    """Get encryption key"""
    service = EncryptionService(db)
    key = service.get_key(key_id)
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    return key


@router.post("/encryption/keys/{key_id}/rotate", response_model=EncryptionKeyResponse)
async def rotate_encryption_key(
    request: Request,
    key_id: UUID,
    db: Session = Depends(get_db),
):
    """Rotate encryption key"""
    service = EncryptionService(db)
    try:
        return service.rotate_key(
            key_id=key_id,
            rotated_by=get_user_id(request),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/encryption/keys/{key_id}", response_model=SuccessResponse)
async def destroy_encryption_key(
    key_id: UUID,
    db: Session = Depends(get_db),
):
    """Destroy encryption key"""
    service = EncryptionService(db)
    try:
        if service.destroy_key(key_id):
            return SuccessResponse(message="Key destroyed")
        raise HTTPException(status_code=404, detail="Key not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/encryption/fields", response_model=FieldEncryptionConfigResponse)
async def configure_field_encryption(
    request: Request,
    body: FieldEncryptionConfigCreate,
    db: Session = Depends(get_db),
):
    """Configure field-level encryption"""
    service = EncryptionService(db)
    return service.configure_field_encryption(
        tenant_id=get_tenant_id(request),
        **body.model_dump(),
    )


@router.get("/encryption/fields", response_model=List[FieldEncryptionConfigResponse])
async def list_field_encryption_configs(
    request: Request,
    db: Session = Depends(get_db),
):
    """List field encryption configurations"""
    service = EncryptionService(db)
    return service.get_field_encryption_configs(get_tenant_id(request))


@router.post("/encryption/certificates", response_model=CertificateResponse)
async def create_certificate(
    body: CertificateCreate,
    db: Session = Depends(get_db),
):
    """Record TLS certificate"""
    service = EncryptionService(db)
    return service.create_certificate_record(**body.model_dump())


@router.get("/encryption/certificates", response_model=List[CertificateResponse])
async def list_certificates(
    include_expired: bool = False,
    db: Session = Depends(get_db),
):
    """List certificates"""
    service = EncryptionService(db)
    return service.list_certificates(include_expired=include_expired)


@router.get("/encryption/certificates/expiring", response_model=List[CertificateResponse])
async def get_expiring_certificates(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get certificates expiring soon"""
    service = EncryptionService(db)
    return service.get_expiring_certificates(days=days)


@router.get("/encryption/status", response_model=EncryptionStatusResponse)
async def get_encryption_status(
    request: Request,
    db: Session = Depends(get_db),
):
    """Get encryption status overview"""
    service = EncryptionService(db)
    return service.get_encryption_status(get_tenant_id(request))


# =============================================================================
# Security Monitoring Endpoints
# =============================================================================

@router.post("/events", response_model=SecurityEventResponse)
async def create_security_event(
    request: Request,
    body: SecurityEventCreate,
    db: Session = Depends(get_db),
):
    """Create security event"""
    service = SecurityMonitoringService(db)
    return service.create_event(
        tenant_id=get_tenant_id(request),
        **body.model_dump(),
    )


@router.get("/events", response_model=List[SecurityEventResponse])
async def list_security_events(
    request: Request,
    severity: Optional[ThreatSeverity] = None,
    threat_type: Optional[ThreatType] = None,
    acknowledged: Optional[bool] = None,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
):
    """List security events"""
    service = SecurityMonitoringService(db)
    return service.list_events(
        tenant_id=get_tenant_id(request),
        severity=severity,
        threat_type=threat_type,
        acknowledged=acknowledged,
        limit=limit,
    )


@router.post("/events/{event_id}/acknowledge", response_model=SuccessResponse)
async def acknowledge_security_event(
    request: Request,
    event_id: UUID,
    db: Session = Depends(get_db),
):
    """Acknowledge security event"""
    service = SecurityMonitoringService(db)
    if service.acknowledge_event(event_id, get_user_id(request)):
        return SuccessResponse(message="Event acknowledged")
    raise HTTPException(status_code=404, detail="Event not found")


@router.post("/detection-rules", response_model=ThreatDetectionRuleResponse)
async def create_detection_rule(
    request: Request,
    body: ThreatDetectionRuleCreate,
    db: Session = Depends(get_db),
):
    """Create threat detection rule"""
    service = SecurityMonitoringService(db)
    return service.create_detection_rule(
        tenant_id=get_tenant_id(request),
        **body.model_dump(),
    )


@router.get("/detection-rules", response_model=List[ThreatDetectionRuleResponse])
async def list_detection_rules(
    request: Request,
    threat_type: Optional[ThreatType] = None,
    is_active: bool = True,
    db: Session = Depends(get_db),
):
    """List detection rules"""
    service = SecurityMonitoringService(db)
    return service.list_detection_rules(
        tenant_id=get_tenant_id(request),
        threat_type=threat_type,
        is_active=is_active,
    )


@router.post("/incidents", response_model=SecurityIncidentResponse)
async def create_incident(
    request: Request,
    body: SecurityIncidentCreate,
    db: Session = Depends(get_db),
):
    """Create security incident"""
    service = SecurityMonitoringService(db)
    return service.create_incident(
        tenant_id=get_tenant_id(request),
        **body.model_dump(),
    )


@router.get("/incidents", response_model=List[SecurityIncidentResponse])
async def list_incidents(
    request: Request,
    status: Optional[IncidentStatus] = None,
    severity: Optional[ThreatSeverity] = None,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
):
    """List security incidents"""
    service = SecurityMonitoringService(db)
    return service.list_incidents(
        tenant_id=get_tenant_id(request),
        status=status,
        severity=severity,
        limit=limit,
    )


@router.get("/incidents/{incident_id}", response_model=SecurityIncidentResponse)
async def get_incident(
    incident_id: UUID,
    db: Session = Depends(get_db),
):
    """Get incident by ID"""
    service = SecurityMonitoringService(db)
    incident = service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.patch("/incidents/{incident_id}/status", response_model=SecurityIncidentResponse)
async def update_incident_status(
    incident_id: UUID,
    body: IncidentStatusUpdate,
    db: Session = Depends(get_db),
):
    """Update incident status"""
    service = SecurityMonitoringService(db)
    incident = service.update_incident_status(
        incident_id=incident_id,
        status=body.status,
        assigned_to=body.assigned_to,
    )
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("/incidents/{incident_id}/responses", response_model=SuccessResponse)
async def add_incident_response(
    request: Request,
    incident_id: UUID,
    body: IncidentResponseCreate,
    db: Session = Depends(get_db),
):
    """Add incident response action"""
    service = SecurityMonitoringService(db)
    service.add_incident_response(
        incident_id=incident_id,
        performed_by=get_user_id(request),
        **body.model_dump(),
    )
    return SuccessResponse(message="Response added")


@router.post("/incidents/{incident_id}/close", response_model=SecurityIncidentResponse)
async def close_incident(
    incident_id: UUID,
    body: IncidentClose,
    db: Session = Depends(get_db),
):
    """Close incident with post-mortem"""
    service = SecurityMonitoringService(db)
    incident = service.close_incident(
        incident_id=incident_id,
        **body.model_dump(),
    )
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.get("/dashboard", response_model=SecurityDashboardResponse)
async def get_security_dashboard(
    request: Request,
    days: int = Query(default=30, le=90),
    db: Session = Depends(get_db),
):
    """Get security dashboard metrics"""
    service = SecurityMonitoringService(db)
    return service.get_security_dashboard(
        tenant_id=get_tenant_id(request),
        days=days,
    )


@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def list_audit_logs(
    request: Request,
    actor_id: Optional[UUID] = None,
    event_category: Optional[str] = None,
    hipaa_only: bool = False,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
):
    """List security audit logs"""
    service = SecurityMonitoringService(db)
    return service.list_audit_logs(
        tenant_id=get_tenant_id(request),
        actor_id=actor_id,
        event_category=event_category,
        hipaa_only=hipaa_only,
        limit=limit,
    )


@router.post("/detection-rules/initialize", response_model=SuccessResponse)
async def initialize_default_rules(
    db: Session = Depends(get_db),
):
    """Initialize default threat detection rules"""
    service = SecurityMonitoringService(db)
    count = service.initialize_default_rules()
    return SuccessResponse(message=f"Initialized {count} default rules")


# =============================================================================
# Vulnerability Management Endpoints
# =============================================================================

@router.post("/vulnerabilities", response_model=VulnerabilityResponse)
async def create_vulnerability(
    request: Request,
    body: VulnerabilityCreate,
    db: Session = Depends(get_db),
):
    """Create vulnerability record"""
    service = VulnerabilityService(db)
    return service.create_vulnerability(
        tenant_id=get_tenant_id(request),
        **body.model_dump(),
    )


@router.get("/vulnerabilities", response_model=List[VulnerabilityResponse])
async def list_vulnerabilities(
    request: Request,
    severity: Optional[VulnerabilitySeverity] = None,
    status: Optional[VulnerabilityStatus] = None,
    scan_type: Optional[ScanType] = None,
    sla_breached_only: bool = False,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
):
    """List vulnerabilities"""
    service = VulnerabilityService(db)
    return service.list_vulnerabilities(
        tenant_id=get_tenant_id(request),
        severity=severity,
        status=status,
        scan_type=scan_type,
        sla_breached_only=sla_breached_only,
        limit=limit,
    )


@router.get("/vulnerabilities/{vuln_id}", response_model=VulnerabilityResponse)
async def get_vulnerability(
    vuln_id: UUID,
    db: Session = Depends(get_db),
):
    """Get vulnerability by ID"""
    service = VulnerabilityService(db)
    vuln = service.get_vulnerability(vuln_id)
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    return vuln


@router.patch("/vulnerabilities/{vuln_id}/status", response_model=VulnerabilityResponse)
async def update_vulnerability_status(
    vuln_id: UUID,
    body: VulnerabilityStatusUpdate,
    db: Session = Depends(get_db),
):
    """Update vulnerability status"""
    service = VulnerabilityService(db)
    vuln = service.update_vulnerability_status(
        vuln_id=vuln_id,
        status=body.status,
        assigned_to=body.assigned_to,
    )
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    return vuln


@router.post("/vulnerabilities/{vuln_id}/verify", response_model=VulnerabilityResponse)
async def verify_vulnerability_remediation(
    vuln_id: UUID,
    db: Session = Depends(get_db),
):
    """Verify vulnerability remediation"""
    service = VulnerabilityService(db)
    vuln = service.verify_remediation(vuln_id)
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    return vuln


@router.post("/vulnerabilities/{vuln_id}/false-positive", response_model=VulnerabilityResponse)
async def mark_vulnerability_false_positive(
    vuln_id: UUID,
    reason: str = Query(default=None),
    db: Session = Depends(get_db),
):
    """Mark vulnerability as false positive"""
    service = VulnerabilityService(db)
    vuln = service.mark_false_positive(vuln_id, reason)
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    return vuln


@router.post("/scans", response_model=SecurityScanResponse)
async def start_security_scan(
    request: Request,
    body: SecurityScanCreate,
    db: Session = Depends(get_db),
):
    """Start a security scan"""
    service = VulnerabilityService(db)
    return service.start_scan(
        tenant_id=get_tenant_id(request),
        triggered_by_user=get_user_id(request),
        **body.model_dump(),
    )


@router.get("/scans", response_model=List[SecurityScanResponse])
async def list_security_scans(
    request: Request,
    scan_type: Optional[ScanType] = None,
    status: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    db: Session = Depends(get_db),
):
    """List security scans"""
    service = VulnerabilityService(db)
    return service.list_scans(
        tenant_id=get_tenant_id(request),
        scan_type=scan_type,
        status=status,
        limit=limit,
    )


@router.post("/scans/{scan_id}/complete", response_model=SecurityScanResponse)
async def complete_security_scan(
    scan_id: UUID,
    body: SecurityScanComplete,
    db: Session = Depends(get_db),
):
    """Complete a security scan"""
    service = VulnerabilityService(db)
    scan = service.complete_scan(
        scan_id=scan_id,
        **body.model_dump(),
    )
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@router.get("/vulnerabilities/dashboard", response_model=VulnerabilityDashboardResponse)
async def get_vulnerability_dashboard(
    request: Request,
    db: Session = Depends(get_db),
):
    """Get vulnerability dashboard"""
    service = VulnerabilityService(db)
    return service.get_vulnerability_dashboard(get_tenant_id(request))


@router.get("/vulnerabilities/sla-compliance", response_model=SLAComplianceResponse)
async def get_sla_compliance(
    request: Request,
    days: int = Query(default=30, le=90),
    db: Session = Depends(get_db),
):
    """Get SLA compliance report"""
    service = VulnerabilityService(db)
    return service.get_sla_compliance_report(
        tenant_id=get_tenant_id(request),
        days=days,
    )


@router.get("/vulnerabilities/top-components", response_model=List[TopVulnerableComponent])
async def get_top_vulnerable_components(
    request: Request,
    limit: int = Query(default=10, le=50),
    db: Session = Depends(get_db),
):
    """Get top vulnerable components"""
    service = VulnerabilityService(db)
    return service.get_top_vulnerable_components(
        tenant_id=get_tenant_id(request),
        limit=limit,
    )
