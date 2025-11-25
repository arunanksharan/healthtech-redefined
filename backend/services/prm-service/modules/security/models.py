"""
Security Hardening Models

SQLAlchemy ORM models for EPIC-021: Security Hardening
Includes MFA, Session Management, RBAC, Encryption, and Security Monitoring.
"""

import enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime,
    ForeignKey, JSON, Enum, Index, UniqueConstraint, CheckConstraint,
    BigInteger, LargeBinary
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET, ARRAY
import uuid

from shared.database import Base


# ============================================================================
# Enums
# ============================================================================

class MFAMethod(str, enum.Enum):
    """MFA authentication methods"""
    TOTP = "totp"                    # Time-based One-Time Password
    SMS = "sms"                      # SMS OTP
    EMAIL = "email"                  # Email OTP
    WEBAUTHN = "webauthn"           # Hardware security keys (FIDO2)
    BACKUP_CODE = "backup_code"     # Backup recovery codes


class MFAStatus(str, enum.Enum):
    """MFA enrollment status"""
    DISABLED = "disabled"
    PENDING = "pending"             # Started but not verified
    ENABLED = "enabled"
    SUSPENDED = "suspended"         # Temporarily disabled


class SessionStatus(str, enum.Enum):
    """Session status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    LOCKED = "locked"


class TokenType(str, enum.Enum):
    """Token types"""
    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"
    MFA_SETUP = "mfa_setup"


class PermissionAction(str, enum.Enum):
    """Permission actions"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"
    EXPORT = "export"
    IMPORT = "import"


class ResourceType(str, enum.Enum):
    """Resource types for RBAC"""
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


class RoleType(str, enum.Enum):
    """Predefined healthcare roles"""
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


class EncryptionAlgorithm(str, enum.Enum):
    """Encryption algorithms"""
    AES_256_GCM = "aes_256_gcm"
    AES_256_CBC = "aes_256_cbc"
    RSA_2048 = "rsa_2048"
    RSA_4096 = "rsa_4096"
    CHACHA20_POLY1305 = "chacha20_poly1305"


class KeyType(str, enum.Enum):
    """Encryption key types"""
    MASTER = "master"               # Master encryption key
    DATA = "data"                   # Data encryption key
    TENANT = "tenant"               # Tenant-specific key
    FIELD = "field"                 # Field-level encryption key
    SIGNING = "signing"             # JWT/Token signing key
    TLS = "tls"                     # TLS certificate key


class KeyStatus(str, enum.Enum):
    """Key lifecycle status"""
    ACTIVE = "active"
    PENDING_ROTATION = "pending_rotation"
    ROTATED = "rotated"
    COMPROMISED = "compromised"
    DESTROYED = "destroyed"


class ThreatType(str, enum.Enum):
    """Security threat types"""
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


class ThreatSeverity(str, enum.Enum):
    """Threat severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IncidentStatus(str, enum.Enum):
    """Security incident status"""
    NEW = "new"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    ERADICATED = "eradicated"
    RECOVERED = "recovered"
    CLOSED = "closed"


class VulnerabilitySeverity(str, enum.Enum):
    """Vulnerability severity (CVSS-based)"""
    CRITICAL = "critical"   # 9.0-10.0
    HIGH = "high"           # 7.0-8.9
    MEDIUM = "medium"       # 4.0-6.9
    LOW = "low"             # 0.1-3.9
    NONE = "none"           # 0.0


class VulnerabilityStatus(str, enum.Enum):
    """Vulnerability remediation status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    REMEDIATED = "remediated"
    ACCEPTED = "accepted"           # Risk accepted
    FALSE_POSITIVE = "false_positive"


class ScanType(str, enum.Enum):
    """Security scan types"""
    DEPENDENCY = "dependency"       # Dependency scanning
    CONTAINER = "container"         # Container image scanning
    SAST = "sast"                   # Static analysis
    DAST = "dast"                   # Dynamic analysis
    PENTEST = "pentest"             # Penetration test
    INFRASTRUCTURE = "infrastructure"


# ============================================================================
# MFA Models
# ============================================================================

class MFAEnrollment(Base):
    """MFA enrollment for users"""
    __tablename__ = "security_mfa_enrollments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # MFA Configuration
    method = Column(Enum(MFAMethod), nullable=False)
    status = Column(Enum(MFAStatus), default=MFAStatus.DISABLED, nullable=False)
    is_primary = Column(Boolean, default=False)

    # Method-specific data (encrypted)
    secret_encrypted = Column(LargeBinary)          # TOTP secret
    phone_number_hash = Column(String(64))          # SMS phone (hashed)
    email_hash = Column(String(64))                 # Email (hashed)
    webauthn_credential_id = Column(String(512))    # WebAuthn credential
    webauthn_public_key = Column(Text)              # WebAuthn public key

    # Verification
    verified_at = Column(DateTime)
    last_used_at = Column(DateTime)
    use_count = Column(Integer, default=0)

    # Metadata
    device_name = Column(String(255))
    enrolled_ip = Column(INET)
    enrolled_user_agent = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_mfa_user_method", "user_id", "method"),
        UniqueConstraint("user_id", "method", "webauthn_credential_id", name="uq_mfa_user_method_credential"),
    )


class MFABackupCode(Base):
    """Backup codes for MFA recovery"""
    __tablename__ = "security_mfa_backup_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    code_hash = Column(String(64), nullable=False)  # SHA-256 hash
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime)
    used_ip = Column(INET)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime)

    __table_args__ = (
        Index("idx_backup_codes_user", "user_id", "is_used"),
    )


class MFAPolicy(Base):
    """MFA enforcement policies"""
    __tablename__ = "security_mfa_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)

    # Policy Configuration
    required_for_all = Column(Boolean, default=False)
    required_roles = Column(ARRAY(String))          # Roles requiring MFA
    allowed_methods = Column(ARRAY(String))         # Allowed MFA methods
    grace_period_hours = Column(Integer, default=72)  # Time to enroll
    remember_device_days = Column(Integer, default=30)

    # PHI Access Requirements
    require_for_phi_access = Column(Boolean, default=True)
    require_for_admin_actions = Column(Boolean, default=True)

    # Risk-based MFA
    require_on_new_device = Column(Boolean, default=True)
    require_on_new_location = Column(Boolean, default=True)
    require_on_suspicious_activity = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True))


# ============================================================================
# Session Management Models
# ============================================================================

class UserSession(Base):
    """Active user sessions"""
    __tablename__ = "security_user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Session Identification
    session_token_hash = Column(String(64), nullable=False, unique=True)
    refresh_token_hash = Column(String(64), unique=True)

    # Session State
    status = Column(Enum(SessionStatus), default=SessionStatus.ACTIVE, nullable=False)

    # Session Metadata
    ip_address = Column(INET)
    user_agent = Column(Text)
    device_fingerprint = Column(String(64))
    device_type = Column(String(50))                # desktop, mobile, tablet
    browser = Column(String(100))
    os = Column(String(100))

    # Location (if available)
    location_country = Column(String(2))
    location_city = Column(String(255))
    location_lat = Column(Float)
    location_lon = Column(Float)

    # Timing
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_activity_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime)
    revoked_reason = Column(String(255))

    # MFA Verification
    mfa_verified = Column(Boolean, default=False)
    mfa_verified_at = Column(DateTime)
    mfa_method_used = Column(Enum(MFAMethod))

    # Risk Score
    risk_score = Column(Float, default=0.0)
    is_trusted_device = Column(Boolean, default=False)

    __table_args__ = (
        Index("idx_sessions_user_status", "user_id", "status"),
        Index("idx_sessions_expires", "expires_at"),
        Index("idx_sessions_activity", "last_activity_at"),
    )


class SessionPolicy(Base):
    """Session management policies"""
    __tablename__ = "security_session_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)

    # Timeout Configuration (in minutes)
    idle_timeout_minutes = Column(Integer, default=15)
    absolute_timeout_minutes = Column(Integer, default=480)  # 8 hours
    refresh_token_lifetime_minutes = Column(Integer, default=10080)  # 7 days

    # Concurrent Sessions
    max_concurrent_sessions = Column(Integer, default=5)
    on_exceed_action = Column(String(50), default="revoke_oldest")  # revoke_oldest, deny_new, notify

    # Security Settings
    bind_to_ip = Column(Boolean, default=False)
    bind_to_device = Column(Boolean, default=True)
    require_mfa_on_new_device = Column(Boolean, default=True)

    # Inactivity handling
    warn_before_timeout_minutes = Column(Integer, default=2)
    extend_on_activity = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LoginAttempt(Base):
    """Track login attempts for security analysis"""
    __tablename__ = "security_login_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True)

    # Attempt Details
    username = Column(String(255), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), index=True)  # If known

    # Status
    success = Column(Boolean, nullable=False)
    failure_reason = Column(String(255))

    # Client Information
    ip_address = Column(INET, nullable=False, index=True)
    user_agent = Column(Text)
    device_fingerprint = Column(String(64))

    # Location
    location_country = Column(String(2))
    location_city = Column(String(255))

    # MFA
    mfa_required = Column(Boolean, default=False)
    mfa_method = Column(Enum(MFAMethod))
    mfa_success = Column(Boolean)

    # Timing
    attempted_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    response_time_ms = Column(Integer)

    __table_args__ = (
        Index("idx_login_attempts_ip_time", "ip_address", "attempted_at"),
        Index("idx_login_attempts_user_time", "username", "attempted_at"),
    )


# ============================================================================
# RBAC Models
# ============================================================================

class Role(Base):
    """Role definitions"""
    __tablename__ = "security_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True)  # NULL for system roles

    name = Column(String(100), nullable=False)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)

    role_type = Column(Enum(RoleType), default=RoleType.CUSTOM, nullable=False)
    is_system_role = Column(Boolean, default=False)  # Cannot be deleted
    is_active = Column(Boolean, default=True)

    # Hierarchy
    parent_role_id = Column(UUID(as_uuid=True), ForeignKey("security_roles.id"))
    hierarchy_level = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True))

    # Relationships
    parent_role = relationship("Role", remote_side=[id], backref="child_roles")
    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_role_tenant_name"),
        Index("idx_roles_tenant_type", "tenant_id", "role_type"),
    )


class Permission(Base):
    """Permission definitions"""
    __tablename__ = "security_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)

    resource_type = Column(Enum(ResourceType), nullable=False)
    action = Column(Enum(PermissionAction), nullable=False)

    # Additional constraints
    scope = Column(String(50))  # all, owned, team, department
    conditions = Column(JSONB)  # Additional conditions as JSON

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("resource_type", "action", "scope", name="uq_permission_resource_action"),
        Index("idx_permissions_resource", "resource_type"),
    )


class RolePermission(Base):
    """Role-Permission assignments"""
    __tablename__ = "security_role_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id = Column(UUID(as_uuid=True), ForeignKey("security_roles.id", ondelete="CASCADE"), nullable=False)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("security_permissions.id", ondelete="CASCADE"), nullable=False)

    # Override settings
    is_granted = Column(Boolean, default=True)  # Can be denied explicitly
    conditions_override = Column(JSONB)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    granted_by = Column(UUID(as_uuid=True))

    # Relationships
    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission")

    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )


class UserRole(Base):
    """User-Role assignments"""
    __tablename__ = "security_user_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("security_roles.id", ondelete="CASCADE"), nullable=False)

    # Scope limitations
    scope_type = Column(String(50))  # organization, department, team, location
    scope_id = Column(UUID(as_uuid=True))

    # Validity period
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    assigned_by = Column(UUID(as_uuid=True))

    # Relationships
    role = relationship("Role")

    __table_args__ = (
        UniqueConstraint("user_id", "role_id", "scope_type", "scope_id", name="uq_user_role_scope"),
        Index("idx_user_roles_user", "user_id", "is_active"),
    )


class BreakTheGlassAccess(Base):
    """Emergency break-the-glass access records"""
    __tablename__ = "security_break_glass_access"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Justification
    reason = Column(Text, nullable=False)
    emergency_type = Column(String(100))  # medical_emergency, quality_review, etc.

    # Access Details
    resources_accessed = Column(JSONB)  # List of resource types and IDs accessed
    access_started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    access_ended_at = Column(DateTime)

    # Review
    reviewed_by = Column(UUID(as_uuid=True))
    reviewed_at = Column(DateTime)
    review_outcome = Column(String(50))  # approved, violation, pending
    review_notes = Column(Text)

    # Client Info
    ip_address = Column(INET)
    user_agent = Column(Text)

    __table_args__ = (
        Index("idx_break_glass_patient", "patient_id", "access_started_at"),
        Index("idx_break_glass_user", "user_id", "access_started_at"),
    )


# ============================================================================
# Encryption & Key Management Models
# ============================================================================

class EncryptionKey(Base):
    """Encryption key metadata"""
    __tablename__ = "security_encryption_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True)  # NULL for system keys

    key_id = Column(String(255), nullable=False, unique=True)  # External key ID (KMS)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    key_type = Column(Enum(KeyType), nullable=False)
    algorithm = Column(Enum(EncryptionAlgorithm), nullable=False)
    key_size_bits = Column(Integer)

    status = Column(Enum(KeyStatus), default=KeyStatus.ACTIVE, nullable=False)

    # Key Hierarchy
    parent_key_id = Column(UUID(as_uuid=True), ForeignKey("security_encryption_keys.id"))

    # Rotation
    version = Column(Integer, default=1)
    rotation_schedule_days = Column(Integer)
    last_rotated_at = Column(DateTime)
    next_rotation_at = Column(DateTime)

    # Usage tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime)
    destroyed_at = Column(DateTime)

    # Provider info
    kms_provider = Column(String(50))  # aws_kms, hashicorp_vault, local
    kms_key_arn = Column(String(512))

    created_by = Column(UUID(as_uuid=True))

    __table_args__ = (
        Index("idx_keys_tenant_type", "tenant_id", "key_type", "status"),
    )


class FieldEncryptionConfig(Base):
    """Field-level encryption configuration"""
    __tablename__ = "security_field_encryption_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True)

    table_name = Column(String(255), nullable=False)
    column_name = Column(String(255), nullable=False)

    encryption_key_id = Column(UUID(as_uuid=True), ForeignKey("security_encryption_keys.id"))
    algorithm = Column(Enum(EncryptionAlgorithm), default=EncryptionAlgorithm.AES_256_GCM)

    # Searchable encryption
    is_searchable = Column(Boolean, default=False)
    search_algorithm = Column(String(100))  # deterministic, randomized

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_id", "table_name", "column_name", name="uq_field_encryption"),
    )


class CertificateRecord(Base):
    """TLS certificate management"""
    __tablename__ = "security_certificates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    domain = Column(String(255), nullable=False)
    common_name = Column(String(255))
    san_domains = Column(ARRAY(String))  # Subject Alternative Names

    # Certificate Info
    serial_number = Column(String(255))
    fingerprint_sha256 = Column(String(64))
    issuer = Column(String(512))

    # Validity
    issued_at = Column(DateTime)
    expires_at = Column(DateTime, nullable=False)

    # Status
    is_active = Column(Boolean, default=True)
    auto_renew = Column(Boolean, default=True)
    last_renewed_at = Column(DateTime)
    renewal_attempts = Column(Integer, default=0)

    # Provider
    provider = Column(String(100))  # letsencrypt, acm, manual
    provider_certificate_id = Column(String(512))

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_certificates_domain", "domain"),
        Index("idx_certificates_expires", "expires_at"),
    )


# ============================================================================
# Security Monitoring Models
# ============================================================================

class SecurityEvent(Base):
    """Security events and alerts"""
    __tablename__ = "security_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True)

    event_type = Column(String(100), nullable=False, index=True)
    threat_type = Column(Enum(ThreatType))
    severity = Column(Enum(ThreatSeverity), nullable=False)

    # Event Details
    title = Column(String(500), nullable=False)
    description = Column(Text)
    details = Column(JSONB)

    # Source
    source_ip = Column(INET)
    source_user_id = Column(UUID(as_uuid=True))
    source_service = Column(String(255))

    # Target
    target_resource_type = Column(String(100))
    target_resource_id = Column(String(255))
    target_user_id = Column(UUID(as_uuid=True))

    # Detection
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    detection_rule_id = Column(String(255))
    confidence_score = Column(Float)

    # Response
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(UUID(as_uuid=True))
    acknowledged_at = Column(DateTime)

    # Correlation
    correlation_id = Column(String(255), index=True)
    related_event_ids = Column(ARRAY(UUID(as_uuid=True)))

    __table_args__ = (
        Index("idx_security_events_tenant_time", "tenant_id", "detected_at"),
        Index("idx_security_events_severity", "severity", "detected_at"),
    )


class ThreatDetectionRule(Base):
    """Threat detection rules configuration"""
    __tablename__ = "security_threat_detection_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text)

    threat_type = Column(Enum(ThreatType), nullable=False)
    severity = Column(Enum(ThreatSeverity), nullable=False)

    # Rule Configuration
    rule_type = Column(String(50))  # threshold, anomaly, pattern, ml
    conditions = Column(JSONB, nullable=False)  # Rule conditions as JSON

    # Thresholds
    threshold_count = Column(Integer)
    threshold_window_minutes = Column(Integer)

    # Actions
    actions = Column(JSONB)  # Alert, block, lock_account, etc.

    is_active = Column(Boolean, default=True)
    is_system_rule = Column(Boolean, default=False)

    # Stats
    trigger_count = Column(Integer, default=0)
    last_triggered_at = Column(DateTime)
    false_positive_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SecurityIncident(Base):
    """Security incident tracking"""
    __tablename__ = "security_incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True)

    incident_number = Column(String(50), nullable=False, unique=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)

    severity = Column(Enum(ThreatSeverity), nullable=False)
    status = Column(Enum(IncidentStatus), default=IncidentStatus.NEW, nullable=False)

    # Classification
    threat_type = Column(Enum(ThreatType))
    attack_vector = Column(String(255))
    affected_systems = Column(ARRAY(String))

    # Impact
    data_breach = Column(Boolean, default=False)
    phi_involved = Column(Boolean, default=False)
    affected_user_count = Column(Integer)
    affected_patient_count = Column(Integer)

    # Timeline
    detected_at = Column(DateTime, nullable=False)
    contained_at = Column(DateTime)
    eradicated_at = Column(DateTime)
    recovered_at = Column(DateTime)
    closed_at = Column(DateTime)

    # Ownership
    assigned_to = Column(UUID(as_uuid=True))
    escalated_to = Column(UUID(as_uuid=True))

    # Related Events
    related_event_ids = Column(ARRAY(UUID(as_uuid=True)))

    # Post-Incident
    root_cause = Column(Text)
    remediation_steps = Column(JSONB)
    lessons_learned = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_incidents_status", "status", "severity"),
        Index("idx_incidents_detected", "detected_at"),
    )


class IncidentResponse(Base):
    """Incident response actions and notes"""
    __tablename__ = "security_incident_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("security_incidents.id", ondelete="CASCADE"), nullable=False)

    action_type = Column(String(100), nullable=False)  # note, containment, evidence, escalation, resolution
    description = Column(Text, nullable=False)

    # Evidence
    evidence_collected = Column(JSONB)
    attachments = Column(ARRAY(String))

    performed_by = Column(UUID(as_uuid=True), nullable=False)
    performed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_incident_responses_incident", "incident_id", "performed_at"),
    )


# ============================================================================
# Vulnerability Management Models
# ============================================================================

class Vulnerability(Base):
    """Vulnerability tracking"""
    __tablename__ = "security_vulnerabilities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True)  # NULL for platform-wide

    # Identification
    cve_id = Column(String(50), index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)

    # Classification
    severity = Column(Enum(VulnerabilitySeverity), nullable=False)
    cvss_score = Column(Float)
    cvss_vector = Column(String(255))

    # Source
    scan_type = Column(Enum(ScanType), nullable=False)
    scanner = Column(String(100))
    scan_id = Column(String(255))

    # Affected Component
    component_type = Column(String(100))  # dependency, container, code, infrastructure
    component_name = Column(String(255))
    component_version = Column(String(100))
    affected_file = Column(String(512))
    affected_line = Column(Integer)

    # Status
    status = Column(Enum(VulnerabilityStatus), default=VulnerabilityStatus.OPEN, nullable=False)

    # Fix Information
    fix_available = Column(Boolean)
    fixed_version = Column(String(100))
    remediation_guidance = Column(Text)

    # SLA
    sla_due_date = Column(DateTime)

    # Tracking
    discovered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    remediated_at = Column(DateTime)
    verified_at = Column(DateTime)

    assigned_to = Column(UUID(as_uuid=True))

    __table_args__ = (
        Index("idx_vulns_status_severity", "status", "severity"),
        Index("idx_vulns_sla", "sla_due_date", "status"),
    )


class SecurityScan(Base):
    """Security scan execution records"""
    __tablename__ = "security_scans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True)

    scan_type = Column(Enum(ScanType), nullable=False)
    scanner = Column(String(100), nullable=False)

    # Target
    target = Column(String(512))  # URL, repo, container image
    target_version = Column(String(100))

    # Execution
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)

    status = Column(String(50))  # running, completed, failed
    error_message = Column(Text)

    # Results Summary
    total_findings = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)

    # Configuration
    scan_config = Column(JSONB)

    triggered_by = Column(String(100))  # scheduled, ci_cd, manual
    triggered_by_user = Column(UUID(as_uuid=True))

    __table_args__ = (
        Index("idx_scans_type_time", "scan_type", "started_at"),
    )


# ============================================================================
# API Security Models
# ============================================================================

class APISecurityPolicy(Base):
    """API security policies"""
    __tablename__ = "security_api_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)

    # Rate Limiting
    rate_limit_requests = Column(Integer)
    rate_limit_window_seconds = Column(Integer)
    burst_limit = Column(Integer)

    # IP Restrictions
    allowed_ips = Column(ARRAY(INET))
    blocked_ips = Column(ARRAY(INET))
    geo_restrictions = Column(ARRAY(String))  # Country codes

    # Request Validation
    max_request_size_bytes = Column(Integer, default=10485760)  # 10MB
    allowed_content_types = Column(ARRAY(String))
    require_https = Column(Boolean, default=True)

    # CORS
    cors_allowed_origins = Column(ARRAY(String))
    cors_allowed_methods = Column(ARRAY(String))
    cors_allowed_headers = Column(ARRAY(String))
    cors_max_age_seconds = Column(Integer, default=86400)

    # Security Headers
    security_headers = Column(JSONB)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class APIRequestLog(Base):
    """API request logging with PII masking"""
    __tablename__ = "security_api_request_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True)

    # Request Identification
    request_id = Column(String(64), nullable=False, index=True)
    trace_id = Column(String(64), index=True)

    # User Context
    user_id = Column(UUID(as_uuid=True), index=True)
    api_key_id = Column(UUID(as_uuid=True))

    # Request Details (sanitized)
    method = Column(String(10), nullable=False)
    path = Column(String(512), nullable=False)
    query_params_hash = Column(String(64))  # Hashed for privacy

    # Client Info
    ip_address = Column(INET, nullable=False)
    user_agent = Column(String(512))

    # Response
    status_code = Column(Integer)
    response_time_ms = Column(Integer)
    response_size_bytes = Column(Integer)

    # Security Context
    authenticated = Column(Boolean)
    authorized = Column(Boolean)
    mfa_verified = Column(Boolean)

    # Timestamps
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("idx_api_logs_tenant_time", "tenant_id", "requested_at"),
        Index("idx_api_logs_user_time", "user_id", "requested_at"),
    )


class SecurityAuditLog(Base):
    """Comprehensive security audit log"""
    __tablename__ = "security_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True)

    # Event Classification
    event_category = Column(String(100), nullable=False)  # authentication, authorization, data_access, config_change
    event_type = Column(String(100), nullable=False)
    event_action = Column(String(100), nullable=False)

    # Actor
    actor_id = Column(UUID(as_uuid=True), index=True)
    actor_type = Column(String(50))  # user, system, api_key
    actor_ip = Column(INET)

    # Target
    target_type = Column(String(100))
    target_id = Column(String(255))

    # Details
    description = Column(Text)
    details = Column(JSONB)

    # Outcome
    outcome = Column(String(50))  # success, failure, denied
    failure_reason = Column(String(255))

    # Compliance
    hipaa_relevant = Column(Boolean, default=False)
    phi_accessed = Column(Boolean, default=False)

    occurred_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("idx_audit_tenant_time", "tenant_id", "occurred_at"),
        Index("idx_audit_actor_time", "actor_id", "occurred_at"),
        Index("idx_audit_category", "event_category", "occurred_at"),
    )
