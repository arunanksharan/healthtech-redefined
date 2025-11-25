"""
HIPAA Compliance Module

Comprehensive HIPAA compliance features for EPIC-022: HIPAA Compliance
Including Audit Logging, Access Controls, Data Retention, Breach Management,
BAA Tracking, Training Management, and Risk Assessment.
"""

from modules.hipaa.models import (
    # Enums
    AuditAction,
    AuditOutcome,
    PHICategory,
    AccessJustification,
    RelationshipType,
    RelationshipStatus,
    AccessRequestStatus,
    CertificationStatus,
    AnomalyType,
    AnomalySeverity,
    RetentionCategory,
    RetentionStatus,
    LegalHoldType,
    LegalHoldStatus,
    DestructionMethod,
    RightOfAccessStatus,
    BreachStatus,
    BreachType,
    NotificationType,
    NotificationStatus,
    BAAType,
    BAAStatus,
    TrainingType,
    TrainingStatus,
    RiskLevel,
    RiskCategory,
    RemediationStatus,
    # Audit Models
    PHIAuditLog,
    AuditRetentionPolicy,
    # Access Control Models
    TreatmentRelationship,
    AccessRequest,
    AccessCertification,
    CertificationCampaign,
    AccessAnomaly,
    VIPPatient,
    # Retention Models
    RetentionPolicy,
    RetentionSchedule,
    LegalHold,
    DestructionCertificate,
    RightOfAccessRequest,
    # Breach Models
    BreachIncident,
    BreachAssessment,
    BreachNotification,
    # BAA Models
    BusinessAssociateAgreement,
    BAAAmendment,
    BAATemplate,
    # Training Models
    TrainingModule,
    TrainingAssignment,
    PolicyDocument,
    PolicyAcknowledgment,
    # Risk Models
    RiskAssessment,
    RiskItem,
    RemediationPlan,
    RiskRegister,
)

from modules.hipaa.router import router

from modules.hipaa.services import (
    AuditService,
    AccessControlService,
    NORMAL_WORKING_HOURS,
    RetentionService,
    DEFAULT_RETENTION_PERIODS,
    BreachService,
    BAAService,
    TrainingService,
    RiskService,
    RISK_MATRIX,
)

__all__ = [
    # Router
    "router",
    # Enums
    "AuditAction",
    "AuditOutcome",
    "PHICategory",
    "AccessJustification",
    "RelationshipType",
    "RelationshipStatus",
    "AccessRequestStatus",
    "CertificationStatus",
    "AnomalyType",
    "AnomalySeverity",
    "RetentionCategory",
    "RetentionStatus",
    "LegalHoldType",
    "LegalHoldStatus",
    "DestructionMethod",
    "RightOfAccessStatus",
    "BreachStatus",
    "BreachType",
    "NotificationType",
    "NotificationStatus",
    "BAAType",
    "BAAStatus",
    "TrainingType",
    "TrainingStatus",
    "RiskLevel",
    "RiskCategory",
    "RemediationStatus",
    # Audit Models
    "PHIAuditLog",
    "AuditRetentionPolicy",
    # Access Control Models
    "TreatmentRelationship",
    "AccessRequest",
    "AccessCertification",
    "CertificationCampaign",
    "AccessAnomaly",
    "VIPPatient",
    # Retention Models
    "RetentionPolicy",
    "RetentionSchedule",
    "LegalHold",
    "DestructionCertificate",
    "RightOfAccessRequest",
    # Breach Models
    "BreachIncident",
    "BreachAssessment",
    "BreachNotification",
    # BAA Models
    "BusinessAssociateAgreement",
    "BAAAmendment",
    "BAATemplate",
    # Training Models
    "TrainingModule",
    "TrainingAssignment",
    "PolicyDocument",
    "PolicyAcknowledgment",
    # Risk Models
    "RiskAssessment",
    "RiskItem",
    "RemediationPlan",
    "RiskRegister",
    # Services
    "AuditService",
    "AccessControlService",
    "NORMAL_WORKING_HOURS",
    "RetentionService",
    "DEFAULT_RETENTION_PERIODS",
    "BreachService",
    "BAAService",
    "TrainingService",
    "RiskService",
    "RISK_MATRIX",
]
