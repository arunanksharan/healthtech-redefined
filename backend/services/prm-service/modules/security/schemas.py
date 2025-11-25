"""
Security Schemas

Pydantic schemas for EPIC-021: Security Hardening
Request/Response validation for MFA, Session, RBAC, Encryption, Monitoring, and Vulnerability Management.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum as PyEnum
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Enums (mirror models.py)
# ============================================================================

class MFAMethodEnum(str, PyEnum):
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    WEBAUTHN = "webauthn"
    BACKUP_CODE = "backup_code"


class MFAStatusEnum(str, PyEnum):
    DISABLED = "disabled"
    PENDING = "pending"
    ENABLED = "enabled"
    SUSPENDED = "suspended"


class SessionStatusEnum(str, PyEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    LOCKED = "locked"


class PermissionActionEnum(str, PyEnum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"
    EXPORT = "export"
    IMPORT = "import"


class ResourceTypeEnum(str, PyEnum):
    PATIENT = "patient"
    PRACTITIONER = "practitioner"
    ENCOUNTER = "encounter"
    OBSERVATION = "observation"
    CONDITION = "condition"
    MEDICATION = "medication"
    PROCEDURE = "procedure"
    APPOINTMENT = "appointment"
    ORGANIZATION = "organization"
    REPORT = "report"
    BILLING = "billing"
    AUDIT_LOG = "audit_log"
    CONFIGURATION = "configuration"
    USER = "user"
    ROLE = "role"


class RoleTypeEnum(str, PyEnum):
    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    PHYSICIAN = "physician"
    NURSE = "nurse"
    MEDICAL_ASSISTANT = "medical_assistant"
    FRONT_DESK = "front_desk"
    BILLING_SPECIALIST = "billing_specialist"
    LAB_TECHNICIAN = "lab_technician"
    PHARMACIST = "pharmacist"
    CARE_COORDINATOR = "care_coordinator"
    PATIENT_PORTAL = "patient_portal"
    READ_ONLY = "read_only"
    CUSTOM = "custom"


class KeyTypeEnum(str, PyEnum):
    MASTER = "master"
    DATA = "data"
    TENANT = "tenant"
    FIELD = "field"
    SIGNING = "signing"
    TLS = "tls"


class KeyStatusEnum(str, PyEnum):
    ACTIVE = "active"
    PENDING_ROTATION = "pending_rotation"
    ROTATED = "rotated"
    COMPROMISED = "compromised"
    DESTROYED = "destroyed"


class EncryptionAlgorithmEnum(str, PyEnum):
    AES_256_GCM = "aes_256_gcm"
    AES_256_CBC = "aes_256_cbc"
    RSA_2048 = "rsa_2048"
    RSA_4096 = "rsa_4096"
    CHACHA20_POLY1305 = "chacha20_poly1305"


class ThreatTypeEnum(str, PyEnum):
    BRUTE_FORCE = "brute_force"
    CREDENTIAL_STUFFING = "credential_stuffing"
    SESSION_HIJACKING = "session_hijacking"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CSRF = "csrf"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    MALWARE = "malware"
    DDOS = "ddos"


class ThreatSeverityEnum(str, PyEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IncidentStatusEnum(str, PyEnum):
    NEW = "new"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    ERADICATED = "eradicated"
    RECOVERED = "recovered"
    CLOSED = "closed"


class VulnerabilitySeverityEnum(str, PyEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class VulnerabilityStatusEnum(str, PyEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    REMEDIATED = "remediated"
    ACCEPTED = "accepted"
    FALSE_POSITIVE = "false_positive"


class ScanTypeEnum(str, PyEnum):
    DEPENDENCY = "dependency"
    CONTAINER = "container"
    SAST = "sast"
    DAST = "dast"
    PENTEST = "pentest"
    INFRASTRUCTURE = "infrastructure"


# ============================================================================
# MFA Schemas
# ============================================================================

class MFATOTPEnrollRequest(BaseModel):
    """Request to start TOTP enrollment"""
    device_name: Optional[str] = Field(None, max_length=255)


class MFATOTPEnrollResponse(BaseModel):
    """TOTP enrollment response"""
    enrollment_id: str
    secret: str
    provisioning_uri: str
    instructions: str


class MFATOTPVerifyRequest(BaseModel):
    """Request to verify TOTP enrollment"""
    code: str = Field(..., min_length=6, max_length=6)


class MFATOTPVerifyResponse(BaseModel):
    """TOTP verification response"""
    enrollment_id: str
    status: str
    is_primary: bool
    backup_codes: List[str]
    message: str


class MFASMSEnrollRequest(BaseModel):
    """Request to start SMS enrollment"""
    phone_number: str = Field(..., min_length=10, max_length=20)


class MFASMSEnrollResponse(BaseModel):
    """SMS enrollment response"""
    enrollment_id: str
    phone_masked: str
    message: str


class MFAVerifyCodeRequest(BaseModel):
    """Generic verification code request"""
    code: str = Field(..., min_length=6, max_length=8)


class WebAuthnRegistrationOptionsResponse(BaseModel):
    """WebAuthn registration options"""
    challenge: str
    rp: Dict[str, str]
    user: Dict[str, str]
    pubKeyCredParams: List[Dict[str, Any]]
    timeout: int
    excludeCredentials: List[Dict[str, str]]
    authenticatorSelection: Dict[str, Any]
    attestation: str


class WebAuthnRegistrationRequest(BaseModel):
    """WebAuthn registration completion"""
    credential: Dict[str, Any]
    device_name: Optional[str] = None


class WebAuthnAuthenticationRequest(BaseModel):
    """WebAuthn authentication assertion"""
    assertion: Dict[str, Any]


class MFAEnrollmentResponse(BaseModel):
    """MFA enrollment details"""
    id: str
    method: MFAMethodEnum
    status: MFAStatusEnum
    is_primary: bool
    device_name: Optional[str] = None
    last_used_at: Optional[datetime] = None
    use_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class MFAPolicyCreate(BaseModel):
    """Create MFA policy"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    required_for_all: bool = False
    required_roles: Optional[List[str]] = None
    allowed_methods: Optional[List[MFAMethodEnum]] = None
    grace_period_hours: int = Field(default=72, ge=0)
    remember_device_days: int = Field(default=30, ge=0)
    require_for_phi_access: bool = True
    require_for_admin_actions: bool = True
    require_on_new_device: bool = True
    require_on_new_location: bool = True


class MFAPolicyResponse(BaseModel):
    """MFA policy details"""
    id: UUID
    name: str
    is_active: bool
    required_for_all: bool
    required_roles: Optional[List[str]] = None
    allowed_methods: Optional[List[str]] = None
    grace_period_hours: int
    remember_device_days: int
    created_at: datetime

    class Config:
        from_attributes = True


class MFARequirementCheck(BaseModel):
    """MFA requirement check response"""
    required: bool
    reasons: List[str]
    allowed_methods: List[str]


# ============================================================================
# Session Schemas
# ============================================================================

class SessionCreateRequest(BaseModel):
    """Create session request (internal)"""
    user_id: UUID
    ip_address: str
    user_agent: Optional[str] = None
    device_fingerprint: Optional[str] = None
    mfa_verified: bool = False
    mfa_method: Optional[MFAMethodEnum] = None


class SessionCreateResponse(BaseModel):
    """Session creation response"""
    session_id: str
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int


class SessionRefreshRequest(BaseModel):
    """Refresh session request"""
    refresh_token: str


class SessionResponse(BaseModel):
    """Session details"""
    id: str
    device_type: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    ip_address: Optional[str] = None
    location_country: Optional[str] = None
    location_city: Optional[str] = None
    created_at: datetime
    last_activity_at: Optional[datetime] = None
    mfa_verified: bool
    is_current: bool = False


class SessionRevokeRequest(BaseModel):
    """Revoke session request"""
    session_id: UUID
    reason: Optional[str] = None


class SessionPolicyCreate(BaseModel):
    """Create session policy"""
    name: str = Field(..., min_length=1, max_length=255)
    idle_timeout_minutes: int = Field(default=15, ge=1, le=1440)
    absolute_timeout_minutes: int = Field(default=480, ge=1, le=10080)
    refresh_token_lifetime_minutes: int = Field(default=10080, ge=1)
    max_concurrent_sessions: int = Field(default=5, ge=1, le=100)
    on_exceed_action: str = Field(default="revoke_oldest")
    bind_to_ip: bool = False
    bind_to_device: bool = True
    require_mfa_on_new_device: bool = True


class SessionPolicyResponse(BaseModel):
    """Session policy details"""
    id: UUID
    name: str
    is_active: bool
    is_default: bool
    idle_timeout_minutes: int
    absolute_timeout_minutes: int
    max_concurrent_sessions: int
    created_at: datetime

    class Config:
        from_attributes = True


class SessionAnalyticsResponse(BaseModel):
    """Session analytics"""
    period_days: int
    total_sessions: int
    active_sessions: int
    device_breakdown: Dict[str, int]
    login_attempts: Dict[str, Any]


# ============================================================================
# RBAC Schemas
# ============================================================================

class RoleCreate(BaseModel):
    """Create role"""
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    role_type: RoleTypeEnum = RoleTypeEnum.CUSTOM
    parent_role_id: Optional[UUID] = None


class RoleUpdate(BaseModel):
    """Update role"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class RoleResponse(BaseModel):
    """Role details"""
    id: UUID
    name: str
    display_name: str
    description: Optional[str] = None
    role_type: RoleTypeEnum
    is_system_role: bool
    is_active: bool
    hierarchy_level: int
    created_at: datetime

    class Config:
        from_attributes = True


class PermissionCreate(BaseModel):
    """Create permission"""
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=255)
    resource_type: ResourceTypeEnum
    action: PermissionActionEnum
    scope: str = "all"
    description: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None


class PermissionResponse(BaseModel):
    """Permission details"""
    id: UUID
    name: str
    display_name: str
    resource_type: ResourceTypeEnum
    action: PermissionActionEnum
    scope: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class RolePermissionAssign(BaseModel):
    """Assign permission to role"""
    permission_id: UUID
    conditions_override: Optional[Dict[str, Any]] = None


class UserRoleAssign(BaseModel):
    """Assign role to user"""
    role_id: UUID
    scope_type: Optional[str] = None
    scope_id: Optional[UUID] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class UserRoleResponse(BaseModel):
    """User role assignment"""
    id: str
    role_id: str
    role_name: str
    role_display_name: str
    role_type: str
    scope_type: Optional[str] = None
    scope_id: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class PermissionCheckRequest(BaseModel):
    """Permission check request"""
    resource_type: ResourceTypeEnum
    action: PermissionActionEnum
    resource_id: Optional[UUID] = None
    scope_context: Optional[Dict[str, Any]] = None


class PermissionCheckResponse(BaseModel):
    """Permission check result"""
    allowed: bool
    reason: str
    permission: Optional[str] = None
    required: Optional[str] = None


class BreakGlassRequest(BaseModel):
    """Break the glass access request"""
    patient_id: UUID
    reason: str = Field(..., min_length=10, max_length=1000)
    emergency_type: Optional[str] = None


class BreakGlassResponse(BaseModel):
    """Break the glass access response"""
    id: UUID
    patient_id: UUID
    access_started_at: datetime
    reason: str

    class Config:
        from_attributes = True


class BreakGlassReview(BaseModel):
    """Break the glass review"""
    outcome: str = Field(..., pattern="^(approved|violation|pending)$")
    notes: Optional[str] = None


# ============================================================================
# Encryption Schemas
# ============================================================================

class EncryptionKeyCreate(BaseModel):
    """Create encryption key"""
    name: str = Field(..., min_length=1, max_length=255)
    key_type: KeyTypeEnum
    algorithm: EncryptionAlgorithmEnum = EncryptionAlgorithmEnum.AES_256_GCM
    rotation_days: Optional[int] = Field(default=90, ge=0)
    parent_key_id: Optional[UUID] = None
    kms_provider: str = "local"


class EncryptionKeyResponse(BaseModel):
    """Encryption key details"""
    id: UUID
    key_id: str
    name: str
    key_type: KeyTypeEnum
    algorithm: EncryptionAlgorithmEnum
    key_size_bits: Optional[int] = None
    status: KeyStatusEnum
    version: int
    rotation_schedule_days: Optional[int] = None
    next_rotation_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FieldEncryptionConfigCreate(BaseModel):
    """Configure field encryption"""
    table_name: str = Field(..., min_length=1, max_length=255)
    column_name: str = Field(..., min_length=1, max_length=255)
    encryption_key_id: UUID
    algorithm: EncryptionAlgorithmEnum = EncryptionAlgorithmEnum.AES_256_GCM
    is_searchable: bool = False


class FieldEncryptionConfigResponse(BaseModel):
    """Field encryption config"""
    id: UUID
    table_name: str
    column_name: str
    encryption_key_id: Optional[UUID] = None
    algorithm: EncryptionAlgorithmEnum
    is_searchable: bool
    is_active: bool

    class Config:
        from_attributes = True


class CertificateCreate(BaseModel):
    """Create certificate record"""
    domain: str = Field(..., min_length=1, max_length=255)
    serial_number: str
    fingerprint_sha256: str
    issuer: str
    issued_at: datetime
    expires_at: datetime
    provider: str = "letsencrypt"
    san_domains: Optional[List[str]] = None
    auto_renew: bool = True


class CertificateResponse(BaseModel):
    """Certificate details"""
    id: UUID
    domain: str
    san_domains: Optional[List[str]] = None
    serial_number: Optional[str] = None
    fingerprint_sha256: Optional[str] = None
    issuer: Optional[str] = None
    issued_at: Optional[datetime] = None
    expires_at: datetime
    is_active: bool
    auto_renew: bool
    provider: Optional[str] = None

    class Config:
        from_attributes = True


class EncryptionStatusResponse(BaseModel):
    """Encryption status overview"""
    keys: Dict[str, int]
    field_encryption: Dict[str, int]
    certificates: Dict[str, int]
    compliance: Dict[str, bool]


# ============================================================================
# Security Monitoring Schemas
# ============================================================================

class SecurityEventCreate(BaseModel):
    """Create security event"""
    event_type: str = Field(..., min_length=1, max_length=100)
    severity: ThreatSeverityEnum
    title: str = Field(..., min_length=1, max_length=500)
    threat_type: Optional[ThreatTypeEnum] = None
    description: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    source_ip: Optional[str] = None
    source_user_id: Optional[UUID] = None
    source_service: Optional[str] = None
    target_resource_type: Optional[str] = None
    target_resource_id: Optional[str] = None
    target_user_id: Optional[UUID] = None


class SecurityEventResponse(BaseModel):
    """Security event details"""
    id: UUID
    event_type: str
    threat_type: Optional[ThreatTypeEnum] = None
    severity: ThreatSeverityEnum
    title: str
    description: Optional[str] = None
    source_ip: Optional[str] = None
    source_user_id: Optional[UUID] = None
    detected_at: datetime
    is_acknowledged: bool
    correlation_id: Optional[str] = None

    class Config:
        from_attributes = True


class ThreatDetectionRuleCreate(BaseModel):
    """Create threat detection rule"""
    name: str = Field(..., min_length=1, max_length=255)
    threat_type: ThreatTypeEnum
    severity: ThreatSeverityEnum
    conditions: Dict[str, Any]
    description: Optional[str] = None
    rule_type: str = "threshold"
    threshold_count: Optional[int] = None
    threshold_window_minutes: Optional[int] = None
    actions: Optional[Dict[str, Any]] = None


class ThreatDetectionRuleResponse(BaseModel):
    """Threat detection rule details"""
    id: UUID
    name: str
    threat_type: ThreatTypeEnum
    severity: ThreatSeverityEnum
    rule_type: Optional[str] = None
    is_active: bool
    is_system_rule: bool
    trigger_count: int
    last_triggered_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SecurityIncidentCreate(BaseModel):
    """Create security incident"""
    title: str = Field(..., min_length=1, max_length=500)
    severity: ThreatSeverityEnum
    description: Optional[str] = None
    threat_type: Optional[ThreatTypeEnum] = None
    attack_vector: Optional[str] = None
    affected_systems: Optional[List[str]] = None
    data_breach: bool = False
    phi_involved: bool = False


class SecurityIncidentResponse(BaseModel):
    """Security incident details"""
    id: UUID
    incident_number: str
    title: str
    severity: ThreatSeverityEnum
    status: IncidentStatusEnum
    threat_type: Optional[ThreatTypeEnum] = None
    data_breach: bool
    phi_involved: bool
    detected_at: datetime
    assigned_to: Optional[UUID] = None
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class IncidentStatusUpdate(BaseModel):
    """Update incident status"""
    status: IncidentStatusEnum
    assigned_to: Optional[UUID] = None


class IncidentResponseCreate(BaseModel):
    """Add incident response action"""
    action_type: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    evidence_collected: Optional[Dict[str, Any]] = None
    attachments: Optional[List[str]] = None


class IncidentClose(BaseModel):
    """Close incident with post-mortem"""
    root_cause: Optional[str] = None
    remediation_steps: Optional[Dict[str, Any]] = None
    lessons_learned: Optional[str] = None


class SecurityDashboardResponse(BaseModel):
    """Security dashboard metrics"""
    period_days: int
    events: Dict[str, Any]
    incidents: Dict[str, Any]
    top_threats: List[Dict[str, Any]]
    compliance: Dict[str, int]


class AuditLogResponse(BaseModel):
    """Security audit log entry"""
    id: UUID
    event_category: str
    event_type: str
    event_action: str
    actor_id: Optional[UUID] = None
    actor_type: Optional[str] = None
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    outcome: str
    hipaa_relevant: bool
    phi_accessed: bool
    occurred_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Vulnerability Management Schemas
# ============================================================================

class VulnerabilityCreate(BaseModel):
    """Create vulnerability"""
    title: str = Field(..., min_length=1, max_length=500)
    severity: VulnerabilitySeverityEnum
    scan_type: ScanTypeEnum
    scanner: str = Field(..., min_length=1, max_length=100)
    component_type: str = Field(..., min_length=1, max_length=100)
    component_name: str = Field(..., min_length=1, max_length=255)
    cve_id: Optional[str] = None
    description: Optional[str] = None
    cvss_score: Optional[float] = Field(default=None, ge=0, le=10)
    cvss_vector: Optional[str] = None
    component_version: Optional[str] = None
    affected_file: Optional[str] = None
    affected_line: Optional[int] = None
    fix_available: bool = False
    fixed_version: Optional[str] = None
    remediation_guidance: Optional[str] = None


class VulnerabilityResponse(BaseModel):
    """Vulnerability details"""
    id: UUID
    cve_id: Optional[str] = None
    title: str
    severity: VulnerabilitySeverityEnum
    cvss_score: Optional[float] = None
    scan_type: ScanTypeEnum
    component_type: Optional[str] = None
    component_name: Optional[str] = None
    component_version: Optional[str] = None
    status: VulnerabilityStatusEnum
    fix_available: Optional[bool] = None
    fixed_version: Optional[str] = None
    sla_due_date: Optional[datetime] = None
    discovered_at: datetime
    remediated_at: Optional[datetime] = None
    assigned_to: Optional[UUID] = None

    class Config:
        from_attributes = True


class VulnerabilityStatusUpdate(BaseModel):
    """Update vulnerability status"""
    status: VulnerabilityStatusEnum
    assigned_to: Optional[UUID] = None


class SecurityScanCreate(BaseModel):
    """Start security scan"""
    scan_type: ScanTypeEnum
    scanner: str = Field(..., min_length=1, max_length=100)
    target: str = Field(..., min_length=1, max_length=512)
    target_version: Optional[str] = None
    scan_config: Optional[Dict[str, Any]] = None
    triggered_by: str = "manual"


class SecurityScanResponse(BaseModel):
    """Security scan details"""
    id: UUID
    scan_type: ScanTypeEnum
    scanner: str
    target: str
    target_version: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    status: Optional[str] = None
    total_findings: Optional[int] = None
    critical_count: Optional[int] = None
    high_count: Optional[int] = None
    medium_count: Optional[int] = None
    low_count: Optional[int] = None

    class Config:
        from_attributes = True


class SecurityScanComplete(BaseModel):
    """Complete security scan"""
    total_findings: int = Field(..., ge=0)
    critical_count: int = Field(default=0, ge=0)
    high_count: int = Field(default=0, ge=0)
    medium_count: int = Field(default=0, ge=0)
    low_count: int = Field(default=0, ge=0)
    error_message: Optional[str] = None


class VulnerabilityDashboardResponse(BaseModel):
    """Vulnerability dashboard metrics"""
    summary: Dict[str, int]
    by_severity: Dict[str, int]
    by_component: Dict[str, int]
    trends_30_days: Dict[str, Any]
    recent_scans: List[Dict[str, Any]]


class SLAComplianceResponse(BaseModel):
    """SLA compliance report"""
    period_days: int
    overall: Dict[str, Any]
    by_severity: Dict[str, Dict[str, Any]]
    sla_definitions: Dict[str, str]


class TopVulnerableComponent(BaseModel):
    """Top vulnerable component"""
    component_name: str
    component_type: str
    total_vulnerabilities: int
    critical_count: int
    high_count: int


# ============================================================================
# Common Response Schemas
# ============================================================================

class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool = True
    message: str


class ErrorResponse(BaseModel):
    """Generic error response"""
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None


class PaginatedResponse(BaseModel):
    """Paginated list response"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    has_more: bool
