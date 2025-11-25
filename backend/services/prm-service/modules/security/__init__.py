"""
Security Hardening Module

Comprehensive security features for EPIC-021: Security Hardening
Including MFA, Session Management, RBAC, Encryption, Monitoring, and Vulnerability Management.
"""

from modules.security.models import (
    # Enums
    MFAMethod,
    MFAStatus,
    SessionStatus,
    TokenType,
    PermissionAction,
    ResourceType,
    RoleType,
    EncryptionAlgorithm,
    KeyType,
    KeyStatus,
    ThreatType,
    ThreatSeverity,
    IncidentStatus,
    VulnerabilitySeverity,
    VulnerabilityStatus,
    ScanType,
    # MFA Models
    MFAEnrollment,
    MFABackupCode,
    MFAPolicy,
    # Session Models
    UserSession,
    SessionPolicy,
    LoginAttempt,
    # RBAC Models
    Role,
    Permission,
    RolePermission,
    UserRole,
    BreakTheGlassAccess,
    # Encryption Models
    EncryptionKey,
    FieldEncryptionConfig,
    CertificateRecord,
    # Monitoring Models
    SecurityEvent,
    ThreatDetectionRule,
    SecurityIncident,
    IncidentResponse,
    SecurityAuditLog,
    # Vulnerability Models
    Vulnerability,
    SecurityScan,
    # API Security Models
    APISecurityPolicy,
    APIRequestLog,
)

from modules.security.router import router

from modules.security.services import (
    MFAService,
    TOTPGenerator,
    SessionService,
    RBACService,
    HEALTHCARE_ROLES,
    EncryptionService,
    SecurityMonitoringService,
    VulnerabilityService,
    SLA_BY_SEVERITY,
)

__all__ = [
    # Router
    "router",
    # Enums
    "MFAMethod",
    "MFAStatus",
    "SessionStatus",
    "TokenType",
    "PermissionAction",
    "ResourceType",
    "RoleType",
    "EncryptionAlgorithm",
    "KeyType",
    "KeyStatus",
    "ThreatType",
    "ThreatSeverity",
    "IncidentStatus",
    "VulnerabilitySeverity",
    "VulnerabilityStatus",
    "ScanType",
    # MFA Models
    "MFAEnrollment",
    "MFABackupCode",
    "MFAPolicy",
    # Session Models
    "UserSession",
    "SessionPolicy",
    "LoginAttempt",
    # RBAC Models
    "Role",
    "Permission",
    "RolePermission",
    "UserRole",
    "BreakTheGlassAccess",
    # Encryption Models
    "EncryptionKey",
    "FieldEncryptionConfig",
    "CertificateRecord",
    # Monitoring Models
    "SecurityEvent",
    "ThreatDetectionRule",
    "SecurityIncident",
    "IncidentResponse",
    "SecurityAuditLog",
    # Vulnerability Models
    "Vulnerability",
    "SecurityScan",
    # API Security Models
    "APISecurityPolicy",
    "APIRequestLog",
    # Services
    "MFAService",
    "TOTPGenerator",
    "SessionService",
    "RBACService",
    "HEALTHCARE_ROLES",
    "EncryptionService",
    "SecurityMonitoringService",
    "VulnerabilityService",
    "SLA_BY_SEVERITY",
]
