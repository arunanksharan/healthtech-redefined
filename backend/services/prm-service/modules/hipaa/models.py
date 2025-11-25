"""
HIPAA Compliance Models

SQLAlchemy ORM models for EPIC-022: HIPAA Compliance
Includes Audit Logging, Access Controls, Data Retention, Breach Management,
BAA Management, Training Tracking, and Risk Assessment.
"""

import enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime,
    ForeignKey, JSON, Enum, Index, UniqueConstraint, CheckConstraint,
    BigInteger, Date, LargeBinary
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET, ARRAY
import uuid

from shared.database import Base


# ============================================================================
# Enums
# ============================================================================

class AuditAction(str, enum.Enum):
    """PHI audit actions"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    PRINT = "print"
    EXPORT = "export"
    IMPORT = "import"
    TRANSMIT = "transmit"
    QUERY = "query"
    LOGIN = "login"
    LOGOUT = "logout"
    FAILED_LOGIN = "failed_login"
    ACCESS_DENIED = "access_denied"


class AuditOutcome(str, enum.Enum):
    """Audit event outcome"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class PHICategory(str, enum.Enum):
    """Categories of Protected Health Information"""
    DEMOGRAPHICS = "demographics"           # Name, DOB, address, etc.
    MEDICAL_RECORDS = "medical_records"     # Diagnoses, treatments
    PRESCRIPTION = "prescription"           # Medication history
    LAB_RESULTS = "lab_results"            # Lab and test results
    IMAGING = "imaging"                    # Radiology, images
    BILLING = "billing"                    # Financial information
    INSURANCE = "insurance"                # Insurance details
    MENTAL_HEALTH = "mental_health"        # Sensitive mental health
    SUBSTANCE_ABUSE = "substance_abuse"    # Highly sensitive
    HIV_AIDS = "hiv_aids"                  # Highly sensitive
    GENETIC = "genetic"                    # Genetic information
    PSYCHOTHERAPY = "psychotherapy"        # Psychotherapy notes
    FULL_RECORD = "full_record"            # Complete patient record


class AccessJustification(str, enum.Enum):
    """Justification for PHI access"""
    TREATMENT = "treatment"
    PAYMENT = "payment"
    OPERATIONS = "operations"
    EMERGENCY = "emergency"
    RESEARCH = "research"
    PUBLIC_HEALTH = "public_health"
    LAW_ENFORCEMENT = "law_enforcement"
    PATIENT_REQUEST = "patient_request"
    BREAK_THE_GLASS = "break_the_glass"


class RelationshipType(str, enum.Enum):
    """Treatment relationship types"""
    PRIMARY_CARE = "primary_care"
    SPECIALIST_REFERRAL = "specialist_referral"
    CARE_TEAM = "care_team"
    CONSULTING = "consulting"
    EMERGENCY = "emergency"
    FACILITY_BASED = "facility_based"
    HISTORICAL = "historical"


class RelationshipStatus(str, enum.Enum):
    """Treatment relationship status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    TERMINATED = "terminated"


class AccessRequestStatus(str, enum.Enum):
    """Access request workflow status"""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    REVOKED = "revoked"


class CertificationStatus(str, enum.Enum):
    """Access certification status"""
    PENDING = "pending"
    CERTIFIED = "certified"
    DECERTIFIED = "decertified"
    ESCALATED = "escalated"


class AnomalyType(str, enum.Enum):
    """Access anomaly types"""
    AFTER_HOURS = "after_hours"
    BULK_ACCESS = "bulk_access"
    VIP_ACCESS = "vip_access"
    EMPLOYEE_ACCESS = "employee_access"
    UNUSUAL_PATTERN = "unusual_pattern"
    GEOGRAPHIC_ANOMALY = "geographic_anomaly"
    HIGH_VOLUME = "high_volume"
    UNAUTHORIZED_RESOURCE = "unauthorized_resource"


class AnomalySeverity(str, enum.Enum):
    """Anomaly severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RetentionCategory(str, enum.Enum):
    """Data retention categories"""
    MEDICAL_RECORD = "medical_record"       # Typically 7-10 years after last encounter
    MINOR_RECORD = "minor_record"           # Age of majority + retention period
    BILLING_RECORD = "billing_record"       # 7 years
    AUDIT_LOG = "audit_log"                 # 7 years (HIPAA requirement)
    CORRESPONDENCE = "correspondence"        # 3-7 years
    CONSENT_FORM = "consent_form"           # 10 years
    RESEARCH_DATA = "research_data"         # Per study protocol
    IMAGING = "imaging"                     # 5-7 years
    LAB_RESULT = "lab_result"               # 7 years
    PRESCRIPTION = "prescription"           # 7 years


class RetentionStatus(str, enum.Enum):
    """Retention policy status"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    PENDING_DESTRUCTION = "pending_destruction"
    DESTROYED = "destroyed"
    LEGAL_HOLD = "legal_hold"


class LegalHoldType(str, enum.Enum):
    """Types of legal holds"""
    LITIGATION = "litigation"
    REGULATORY = "regulatory"
    INTERNAL_INVESTIGATION = "internal_investigation"
    PRESERVATION_NOTICE = "preservation_notice"
    HIPAA_INVESTIGATION = "hipaa_investigation"


class LegalHoldStatus(str, enum.Enum):
    """Legal hold status"""
    ACTIVE = "active"
    PENDING_RELEASE = "pending_release"
    RELEASED = "released"


class DestructionMethod(str, enum.Enum):
    """Data destruction methods"""
    DELETION = "deletion"                   # Logical deletion
    SHREDDING = "shredding"                # Secure file overwrite
    CRYPTOGRAPHIC_ERASURE = "cryptographic_erasure"  # Key destruction
    PHYSICAL_DESTRUCTION = "physical_destruction"    # Hardware destruction
    DEGAUSSING = "degaussing"              # Magnetic media


class RightOfAccessStatus(str, enum.Enum):
    """Right of Access request status"""
    RECEIVED = "received"
    IDENTITY_VERIFICATION = "identity_verification"
    PROCESSING = "processing"
    READY = "ready"
    DELIVERED = "delivered"
    DENIED = "denied"
    EXTENDED = "extended"                   # 30-day extension


class BreachStatus(str, enum.Enum):
    """Breach investigation status"""
    SUSPECTED = "suspected"
    CONFIRMED = "confirmed"
    NOT_A_BREACH = "not_a_breach"
    INVESTIGATING = "investigating"
    NOTIFYING = "notifying"
    CLOSED = "closed"


class BreachType(str, enum.Enum):
    """Types of breaches"""
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    THEFT = "theft"
    LOSS = "loss"
    IMPROPER_DISPOSAL = "improper_disposal"
    HACKING = "hacking"
    UNAUTHORIZED_DISCLOSURE = "unauthorized_disclosure"
    VENDOR_INCIDENT = "vendor_incident"
    EMPLOYEE_ERROR = "employee_error"


class NotificationType(str, enum.Enum):
    """Breach notification types"""
    HHS_NOTIFICATION = "hhs_notification"
    PATIENT_NOTIFICATION = "patient_notification"
    MEDIA_NOTIFICATION = "media_notification"
    STATE_NOTIFICATION = "state_notification"


class NotificationStatus(str, enum.Enum):
    """Notification delivery status"""
    DRAFT = "draft"
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    BOUNCED = "bounced"
    FAILED = "failed"


class BAAType(str, enum.Enum):
    """BAA agreement types"""
    CUSTOMER = "customer"                   # We are the BA
    VENDOR = "vendor"                       # They are our BA
    SUBCONTRACTOR = "subcontractor"        # BA subcontractor chain


class BAAStatus(str, enum.Enum):
    """BAA status"""
    DRAFT = "draft"
    NEGOTIATING = "negotiating"
    PENDING_SIGNATURE = "pending_signature"
    EXECUTED = "executed"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class TrainingType(str, enum.Enum):
    """Training module types"""
    HIPAA_BASICS = "hipaa_basics"
    PRIVACY_RULE = "privacy_rule"
    SECURITY_RULE = "security_rule"
    BREACH_RESPONSE = "breach_response"
    ROLE_SPECIFIC = "role_specific"
    SECURITY_AWARENESS = "security_awareness"
    ANNUAL_REFRESHER = "annual_refresher"


class TrainingStatus(str, enum.Enum):
    """Training assignment status"""
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    WAIVED = "waived"


class RiskLevel(str, enum.Enum):
    """Risk level classification"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class RiskCategory(str, enum.Enum):
    """Risk assessment categories"""
    ADMINISTRATIVE = "administrative"
    PHYSICAL = "physical"
    TECHNICAL = "technical"
    ORGANIZATIONAL = "organizational"
    COMPLIANCE = "compliance"


class RemediationStatus(str, enum.Enum):
    """Remediation item status"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VERIFIED = "verified"
    DEFERRED = "deferred"
    ACCEPTED = "accepted"                   # Risk accepted


# ============================================================================
# Audit Logging Models
# ============================================================================

class PHIAuditLog(Base):
    """
    Comprehensive PHI access audit log.
    Implements tamper-proof logging with cryptographic verification.
    Maps to FHIR AuditEvent resource.
    """
    __tablename__ = "hipaa_phi_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Event identification
    event_id = Column(String(100), unique=True, nullable=False)
    event_type = Column(String(50), nullable=False)
    action = Column(Enum(AuditAction), nullable=False)
    outcome = Column(Enum(AuditOutcome), nullable=False, default=AuditOutcome.SUCCESS)

    # Timestamp with precision
    recorded_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    event_start = Column(DateTime, nullable=True)
    event_end = Column(DateTime, nullable=True)

    # Actor (who performed the action)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    user_type = Column(String(50), nullable=True)  # practitioner, patient, system
    user_name = Column(String(200), nullable=True)
    user_role = Column(String(100), nullable=True)

    # Network information
    source_ip = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    geo_location = Column(String(200), nullable=True)

    # Session context
    session_id = Column(UUID(as_uuid=True), nullable=True)
    request_id = Column(String(100), nullable=True)

    # PHI Entity (what was accessed)
    phi_category = Column(Enum(PHICategory), nullable=False)
    resource_type = Column(String(100), nullable=False)  # FHIR resource type
    resource_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Patient context
    patient_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    patient_mrn = Column(String(50), nullable=True)

    # Encounter/clinical context
    encounter_id = Column(UUID(as_uuid=True), nullable=True)
    justification = Column(Enum(AccessJustification), nullable=True)
    justification_details = Column(Text, nullable=True)

    # Data access details
    fields_accessed = Column(JSONB, nullable=True)  # List of field names
    query_parameters = Column(JSONB, nullable=True)  # Search/filter params
    data_before = Column(JSONB, nullable=True)       # For updates
    data_after = Column(JSONB, nullable=True)        # For updates

    # FHIR AuditEvent mapping
    fhir_audit_event_id = Column(String(100), nullable=True)
    fhir_event_coding = Column(JSONB, nullable=True)

    # Tamper-proof chain
    previous_hash = Column(String(64), nullable=True)
    record_hash = Column(String(64), nullable=False)
    hash_algorithm = Column(String(20), default="sha256")

    # Additional metadata
    service_name = Column(String(100), nullable=True)
    api_endpoint = Column(String(500), nullable=True)
    http_method = Column(String(10), nullable=True)
    response_code = Column(Integer, nullable=True)

    # Archival tracking
    archived = Column(Boolean, default=False)
    archived_at = Column(DateTime, nullable=True)
    archive_location = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_phi_audit_tenant_recorded", "tenant_id", "recorded_at"),
        Index("ix_phi_audit_user_recorded", "user_id", "recorded_at"),
        Index("ix_phi_audit_patient_recorded", "patient_id", "recorded_at"),
        Index("ix_phi_audit_action_category", "action", "phi_category"),
    )


class AuditRetentionPolicy(Base):
    """
    Audit log retention policy configuration.
    Ensures 7-year retention for HIPAA compliance.
    """
    __tablename__ = "hipaa_audit_retention_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Retention settings
    retention_days = Column(Integer, nullable=False, default=2555)  # 7 years
    archive_after_days = Column(Integer, nullable=False, default=365)
    archive_storage_class = Column(String(50), default="GLACIER")

    # Policy application
    applies_to_actions = Column(ARRAY(String), nullable=True)
    applies_to_categories = Column(ARRAY(String), nullable=True)

    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)


# ============================================================================
# Access Control Models
# ============================================================================

class TreatmentRelationship(Base):
    """
    Treatment relationship between patient and provider.
    Used for minimum necessary access control verification.
    """
    __tablename__ = "hipaa_treatment_relationships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Parties
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    provider_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    provider_type = Column(String(50), nullable=False)  # practitioner, organization

    # Relationship details
    relationship_type = Column(Enum(RelationshipType), nullable=False)
    status = Column(Enum(RelationshipStatus), default=RelationshipStatus.ACTIVE)

    # Validity period
    effective_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=True)

    # Referral/authorization tracking
    referral_id = Column(UUID(as_uuid=True), nullable=True)
    authorization_number = Column(String(100), nullable=True)

    # Care team context
    care_team_id = Column(UUID(as_uuid=True), nullable=True)
    care_team_role = Column(String(100), nullable=True)

    # Facility context
    facility_id = Column(UUID(as_uuid=True), nullable=True)
    department = Column(String(200), nullable=True)

    # Access scope
    allowed_phi_categories = Column(ARRAY(String), nullable=True)
    restricted_phi_categories = Column(ARRAY(String), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)

    __table_args__ = (
        Index("ix_treatment_rel_patient_provider", "patient_id", "provider_id"),
        UniqueConstraint("tenant_id", "patient_id", "provider_id", "relationship_type",
                        name="uq_treatment_relationship"),
    )


class AccessRequest(Base):
    """
    PHI access request workflow.
    For cases where direct treatment relationship doesn't exist.
    """
    __tablename__ = "hipaa_access_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Request details
    request_number = Column(String(50), unique=True, nullable=False)
    requester_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    requester_name = Column(String(200), nullable=True)
    requester_role = Column(String(100), nullable=True)

    # Target patient/data
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    requested_phi_categories = Column(ARRAY(String), nullable=False)
    requested_resources = Column(JSONB, nullable=True)

    # Justification
    justification = Column(Enum(AccessJustification), nullable=False)
    justification_details = Column(Text, nullable=False)
    clinical_context = Column(Text, nullable=True)

    # Workflow
    status = Column(Enum(AccessRequestStatus), default=AccessRequestStatus.PENDING)

    # Approval details
    approver_id = Column(UUID(as_uuid=True), nullable=True)
    approver_name = Column(String(200), nullable=True)
    approval_date = Column(DateTime, nullable=True)
    denial_reason = Column(Text, nullable=True)

    # Time-limited access
    access_start = Column(DateTime, nullable=True)
    access_end = Column(DateTime, nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_access_request_status", "status", "created_at"),
    )


class AccessCertification(Base):
    """
    Periodic access certification review.
    Ensures continued appropriate access to PHI.
    """
    __tablename__ = "hipaa_access_certifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Certification campaign
    campaign_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    campaign_name = Column(String(200), nullable=True)

    # Access being certified
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_name = Column(String(200), nullable=True)
    role_id = Column(UUID(as_uuid=True), nullable=True)
    role_name = Column(String(200), nullable=True)

    # Scope
    access_type = Column(String(50), nullable=False)  # role, permission, resource
    access_details = Column(JSONB, nullable=False)

    # Reviewer
    reviewer_id = Column(UUID(as_uuid=True), nullable=False)
    reviewer_name = Column(String(200), nullable=True)

    # Certification status
    status = Column(Enum(CertificationStatus), default=CertificationStatus.PENDING)
    certification_date = Column(DateTime, nullable=True)
    comments = Column(Text, nullable=True)

    # Deadlines
    due_date = Column(DateTime, nullable=False)
    reminder_sent = Column(Boolean, default=False)
    escalated = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CertificationCampaign(Base):
    """
    Access certification campaign for periodic reviews.
    """
    __tablename__ = "hipaa_certification_campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Campaign period
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    # Scope
    scope_type = Column(String(50), nullable=False)  # all, department, role
    scope_criteria = Column(JSONB, nullable=True)

    # Progress
    total_certifications = Column(Integer, default=0)
    completed_certifications = Column(Integer, default=0)
    certified_count = Column(Integer, default=0)
    decertified_count = Column(Integer, default=0)

    # Status
    is_active = Column(Boolean, default=True)
    completed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)


class AccessAnomaly(Base):
    """
    Detected access anomalies for investigation.
    """
    __tablename__ = "hipaa_access_anomalies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Detection details
    anomaly_type = Column(Enum(AnomalyType), nullable=False)
    severity = Column(Enum(AnomalySeverity), nullable=False)

    # Actor
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_name = Column(String(200), nullable=True)
    user_role = Column(String(100), nullable=True)

    # Context
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    source_ip = Column(INET, nullable=True)

    # Anomaly details
    description = Column(Text, nullable=False)
    evidence = Column(JSONB, nullable=False)  # Access patterns, volumes, etc.
    baseline_comparison = Column(JSONB, nullable=True)  # Comparison to normal

    # Related patient(s) if applicable
    affected_patient_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=True)

    # Related audit logs
    audit_log_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=True)

    # Investigation
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(UUID(as_uuid=True), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    investigation_notes = Column(Text, nullable=True)

    # Resolution
    resolved = Column(Boolean, default=False)
    resolution = Column(Text, nullable=True)
    false_positive = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_access_anomaly_severity", "severity", "detected_at"),
        Index("ix_access_anomaly_type_user", "anomaly_type", "user_id"),
    )


class VIPPatient(Base):
    """
    VIP patient designation for enhanced access monitoring.
    """
    __tablename__ = "hipaa_vip_patients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    patient_id = Column(UUID(as_uuid=True), nullable=False, unique=True)

    # VIP designation
    vip_reason = Column(String(200), nullable=False)  # celebrity, employee, executive
    enhanced_monitoring = Column(Boolean, default=True)
    access_alerts_enabled = Column(Boolean, default=True)

    # Approved accessors
    allowed_user_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=True)
    allowed_roles = Column(ARRAY(String), nullable=True)

    # Alert configuration
    alert_recipients = Column(ARRAY(String), nullable=True)  # Email addresses

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)


# ============================================================================
# Data Retention Models
# ============================================================================

class RetentionPolicy(Base):
    """
    Data retention policy configuration.
    Supports different retention periods by data category and jurisdiction.
    """
    __tablename__ = "hipaa_retention_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Category and scope
    category = Column(Enum(RetentionCategory), nullable=False)
    resource_types = Column(ARRAY(String), nullable=True)  # FHIR resource types

    # Retention period
    retention_years = Column(Integer, nullable=False)
    retention_months = Column(Integer, default=0)

    # For minor records
    applies_to_minors = Column(Boolean, default=False)
    minor_retention_from_age = Column(Integer, default=18)  # Age of majority
    minor_additional_years = Column(Integer, default=0)

    # Jurisdiction
    jurisdiction = Column(String(50), nullable=True)  # State or federal
    regulation_reference = Column(String(200), nullable=True)

    # Destruction settings
    destruction_method = Column(Enum(DestructionMethod), default=DestructionMethod.CRYPTOGRAPHIC_ERASURE)
    require_destruction_certificate = Column(Boolean, default=True)

    # Archive settings
    archive_before_destruction = Column(Boolean, default=True)
    archive_storage_class = Column(String(50), default="GLACIER")

    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)

    __table_args__ = (
        Index("ix_retention_policy_category", "category", "is_active"),
    )


class RetentionSchedule(Base):
    """
    Tracks retention schedule for individual records.
    """
    __tablename__ = "hipaa_retention_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Record identification
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(UUID(as_uuid=True), nullable=False)
    patient_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Policy reference
    policy_id = Column(UUID(as_uuid=True), ForeignKey("hipaa_retention_policies.id"), nullable=False)

    # Retention calculation
    record_date = Column(Date, nullable=False)  # Date record was created/last active
    retention_start_date = Column(Date, nullable=False)
    scheduled_destruction_date = Column(Date, nullable=False, index=True)

    # Status
    status = Column(Enum(RetentionStatus), default=RetentionStatus.ACTIVE)

    # Archive tracking
    archived_at = Column(DateTime, nullable=True)
    archive_location = Column(String(500), nullable=True)

    # Destruction tracking
    destruction_approved = Column(Boolean, default=False)
    destruction_approved_by = Column(UUID(as_uuid=True), nullable=True)
    destruction_approved_at = Column(DateTime, nullable=True)
    destroyed_at = Column(DateTime, nullable=True)
    destruction_certificate_id = Column(UUID(as_uuid=True), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_retention_schedule_status_date", "status", "scheduled_destruction_date"),
        UniqueConstraint("resource_type", "resource_id", name="uq_retention_schedule_resource"),
    )


class LegalHold(Base):
    """
    Legal hold to suspend data destruction.
    """
    __tablename__ = "hipaa_legal_holds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Hold identification
    hold_number = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Hold type and reason
    hold_type = Column(Enum(LegalHoldType), nullable=False)
    matter_reference = Column(String(200), nullable=True)  # Case number, etc.

    # Scope
    scope_type = Column(String(50), nullable=False)  # patient, date_range, custodian
    scope_criteria = Column(JSONB, nullable=False)  # Criteria for affected records

    # Affected records tracking
    affected_patient_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=True)
    affected_record_count = Column(Integer, default=0)

    # Legal counsel
    legal_contact_name = Column(String(200), nullable=True)
    legal_contact_email = Column(String(200), nullable=True)

    # Hold period
    status = Column(Enum(LegalHoldStatus), default=LegalHoldStatus.ACTIVE)
    effective_date = Column(Date, nullable=False)
    release_date = Column(Date, nullable=True)

    # Workflow
    created_by = Column(UUID(as_uuid=True), nullable=False)
    released_by = Column(UUID(as_uuid=True), nullable=True)
    release_approved_by = Column(UUID(as_uuid=True), nullable=True)
    release_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    released_at = Column(DateTime, nullable=True)


class DestructionCertificate(Base):
    """
    Certificate documenting data destruction.
    """
    __tablename__ = "hipaa_destruction_certificates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Certificate identification
    certificate_number = Column(String(50), unique=True, nullable=False)

    # Destruction details
    destruction_date = Column(DateTime, nullable=False)
    destruction_method = Column(Enum(DestructionMethod), nullable=False)

    # Records destroyed
    record_count = Column(Integer, nullable=False)
    record_summary = Column(JSONB, nullable=False)  # Summary of what was destroyed
    resource_types = Column(ARRAY(String), nullable=False)

    # Patient context
    affected_patient_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=True)

    # Verification
    verified = Column(Boolean, default=False)
    verified_by = Column(UUID(as_uuid=True), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verification_method = Column(String(200), nullable=True)

    # Authorization
    authorized_by = Column(UUID(as_uuid=True), nullable=False)
    authorization_date = Column(DateTime, nullable=False)

    # Certificate hash for integrity
    certificate_hash = Column(String(64), nullable=False)

    # Retention of certificate itself (kept longer than data)
    certificate_retention_date = Column(Date, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=False)


class RightOfAccessRequest(Base):
    """
    Patient Right of Access request tracking.
    45-day fulfillment requirement (or 30-day extension).
    """
    __tablename__ = "hipaa_right_of_access_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Request identification
    request_number = Column(String(50), unique=True, nullable=False)

    # Requestor
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    requestor_type = Column(String(50), nullable=False)  # patient, representative
    representative_name = Column(String(200), nullable=True)
    representative_relationship = Column(String(100), nullable=True)

    # Contact information
    delivery_email = Column(String(200), nullable=True)
    delivery_address = Column(Text, nullable=True)
    delivery_method = Column(String(50), nullable=False)  # electronic, mail, pickup

    # Request scope
    requested_records = Column(JSONB, nullable=False)  # What was requested
    date_range_start = Column(Date, nullable=True)
    date_range_end = Column(Date, nullable=True)

    # Identity verification
    identity_verified = Column(Boolean, default=False)
    verification_method = Column(String(200), nullable=True)
    verification_date = Column(DateTime, nullable=True)
    verified_by = Column(UUID(as_uuid=True), nullable=True)

    # Status and timeline
    status = Column(Enum(RightOfAccessStatus), default=RightOfAccessStatus.RECEIVED)
    received_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=False)  # 30 days default
    extension_granted = Column(Boolean, default=False)
    extension_reason = Column(Text, nullable=True)
    extended_due_date = Column(DateTime, nullable=True)

    # Processing
    assigned_to = Column(UUID(as_uuid=True), nullable=True)
    processing_started_at = Column(DateTime, nullable=True)

    # Export details
    export_format = Column(String(50), nullable=True)  # PDF, FHIR JSON, etc.
    export_size_bytes = Column(BigInteger, nullable=True)
    export_location = Column(String(500), nullable=True)
    export_password_protected = Column(Boolean, default=True)

    # Delivery
    delivered_at = Column(DateTime, nullable=True)
    delivery_confirmation = Column(String(200), nullable=True)

    # Denial (if applicable)
    denied = Column(Boolean, default=False)
    denial_reason = Column(Text, nullable=True)
    denial_code = Column(String(50), nullable=True)

    # Fee tracking (reasonable cost-based fee allowed)
    fee_amount = Column(Float, nullable=True)
    fee_paid = Column(Boolean, default=False)
    fee_waived = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_roa_status_due_date", "status", "due_date"),
    )


# ============================================================================
# Breach Management Models
# ============================================================================

class BreachIncident(Base):
    """
    HIPAA breach incident tracking.
    """
    __tablename__ = "hipaa_breach_incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Incident identification
    incident_number = Column(String(50), unique=True, nullable=False)

    # Discovery
    discovered_date = Column(DateTime, nullable=False)
    discovered_by = Column(UUID(as_uuid=True), nullable=True)
    discovery_method = Column(String(200), nullable=True)

    # Incident details
    breach_type = Column(Enum(BreachType), nullable=False)
    description = Column(Text, nullable=False)

    # Dates (for notification calculations)
    breach_date = Column(Date, nullable=True)  # When breach occurred
    breach_start = Column(DateTime, nullable=True)
    breach_end = Column(DateTime, nullable=True)

    # Status
    status = Column(Enum(BreachStatus), default=BreachStatus.SUSPECTED)

    # Affected individuals
    affected_individuals_count = Column(Integer, default=0)
    affected_patient_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=True)

    # PHI involved
    phi_categories_involved = Column(ARRAY(String), nullable=False)
    phi_description = Column(Text, nullable=True)

    # Source/cause
    breach_source = Column(String(200), nullable=True)  # Employee, vendor, hacker
    root_cause = Column(Text, nullable=True)

    # Investigation
    lead_investigator = Column(UUID(as_uuid=True), nullable=True)
    investigation_notes = Column(Text, nullable=True)

    # Notification deadlines
    hhs_notification_deadline = Column(DateTime, nullable=True)  # 60 days from discovery
    patient_notification_deadline = Column(DateTime, nullable=True)

    # Resolution
    containment_actions = Column(Text, nullable=True)
    remediation_actions = Column(Text, nullable=True)
    lessons_learned = Column(Text, nullable=True)

    closed_at = Column(DateTime, nullable=True)
    closed_by = Column(UUID(as_uuid=True), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_breach_incident_status", "status", "discovered_date"),
    )


class BreachAssessment(Base):
    """
    Breach risk assessment (4-factor test).
    Determines if notification is required.
    """
    __tablename__ = "hipaa_breach_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    incident_id = Column(UUID(as_uuid=True), ForeignKey("hipaa_breach_incidents.id"), nullable=False)

    # Assessment date and assessor
    assessed_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    assessed_by = Column(UUID(as_uuid=True), nullable=False)
    assessor_name = Column(String(200), nullable=True)

    # 4-Factor Risk Assessment

    # Factor 1: Nature and extent of PHI involved
    factor1_phi_nature = Column(Text, nullable=False)
    factor1_phi_types = Column(ARRAY(String), nullable=False)
    factor1_identifiability = Column(String(50), nullable=False)  # low, medium, high
    factor1_score = Column(Integer, nullable=False)  # 1-10

    # Factor 2: Unauthorized person who used/received PHI
    factor2_recipient_description = Column(Text, nullable=False)
    factor2_recipient_type = Column(String(100), nullable=True)
    factor2_obligation_to_protect = Column(Boolean, nullable=True)
    factor2_score = Column(Integer, nullable=False)  # 1-10

    # Factor 3: Whether PHI was actually viewed/acquired
    factor3_phi_accessed = Column(String(50), nullable=False)  # yes, no, unknown
    factor3_access_evidence = Column(Text, nullable=True)
    factor3_score = Column(Integer, nullable=False)  # 1-10

    # Factor 4: Extent to which risk has been mitigated
    factor4_mitigation_actions = Column(Text, nullable=False)
    factor4_assurances_obtained = Column(Boolean, default=False)
    factor4_phi_returned_destroyed = Column(Boolean, default=False)
    factor4_score = Column(Integer, nullable=False)  # 1-10

    # Overall assessment
    overall_risk_score = Column(Integer, nullable=False)  # Sum or weighted average
    risk_level = Column(Enum(RiskLevel), nullable=False)

    # Determination
    notification_required = Column(Boolean, nullable=False)
    notification_determination_reason = Column(Text, nullable=False)

    # Low probability exception
    low_probability_exception = Column(Boolean, default=False)
    exception_justification = Column(Text, nullable=True)

    # Review/approval
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_comments = Column(Text, nullable=True)
    approved = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BreachNotification(Base):
    """
    Breach notification tracking (HHS, patients, media).
    """
    __tablename__ = "hipaa_breach_notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    incident_id = Column(UUID(as_uuid=True), ForeignKey("hipaa_breach_incidents.id"), nullable=False)

    # Notification type
    notification_type = Column(Enum(NotificationType), nullable=False)

    # Recipient
    recipient_type = Column(String(50), nullable=False)  # hhs, patient, media, state
    recipient_name = Column(String(200), nullable=True)
    recipient_email = Column(String(200), nullable=True)
    recipient_address = Column(Text, nullable=True)
    patient_id = Column(UUID(as_uuid=True), nullable=True)  # For patient notifications

    # Content
    notification_content = Column(Text, nullable=False)
    letter_template_used = Column(String(100), nullable=True)

    # Status
    status = Column(Enum(NotificationStatus), default=NotificationStatus.DRAFT)

    # Timing
    scheduled_date = Column(DateTime, nullable=True)
    sent_date = Column(DateTime, nullable=True)
    delivered_date = Column(DateTime, nullable=True)

    # Delivery tracking
    delivery_method = Column(String(50), nullable=True)  # email, mail, both
    tracking_number = Column(String(100), nullable=True)
    delivery_confirmation = Column(String(200), nullable=True)

    # Failed delivery handling
    failed_reason = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    alternative_notification_used = Column(Boolean, default=False)

    # For HHS submissions
    hhs_submission_id = Column(String(100), nullable=True)
    hhs_acknowledgment = Column(String(200), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)

    __table_args__ = (
        Index("ix_breach_notification_incident", "incident_id", "notification_type"),
    )


# ============================================================================
# BAA Management Models
# ============================================================================

class BusinessAssociateAgreement(Base):
    """
    Business Associate Agreement tracking.
    """
    __tablename__ = "hipaa_business_associate_agreements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # BAA identification
    baa_number = Column(String(50), unique=True, nullable=False)

    # Agreement type and parties
    baa_type = Column(Enum(BAAType), nullable=False)

    # Counterparty (vendor or customer)
    counterparty_name = Column(String(300), nullable=False)
    counterparty_type = Column(String(50), nullable=False)  # vendor, customer
    counterparty_address = Column(Text, nullable=True)
    counterparty_contact_name = Column(String(200), nullable=True)
    counterparty_contact_email = Column(String(200), nullable=True)
    counterparty_contact_phone = Column(String(50), nullable=True)

    # Services covered
    services_description = Column(Text, nullable=False)
    phi_categories_covered = Column(ARRAY(String), nullable=False)

    # Status
    status = Column(Enum(BAAStatus), default=BAAStatus.DRAFT)

    # Document
    template_used = Column(String(100), nullable=True)
    document_url = Column(String(500), nullable=True)
    document_hash = Column(String(64), nullable=True)

    # Execution
    execution_date = Column(Date, nullable=True)
    effective_date = Column(Date, nullable=True)
    expiration_date = Column(Date, nullable=True)
    auto_renew = Column(Boolean, default=False)
    renewal_term_months = Column(Integer, nullable=True)

    # Signatories
    our_signatory_name = Column(String(200), nullable=True)
    our_signatory_title = Column(String(200), nullable=True)
    our_signature_date = Column(Date, nullable=True)
    counterparty_signatory_name = Column(String(200), nullable=True)
    counterparty_signatory_title = Column(String(200), nullable=True)
    counterparty_signature_date = Column(Date, nullable=True)

    # E-signature tracking
    esignature_envelope_id = Column(String(100), nullable=True)
    esignature_status = Column(String(50), nullable=True)

    # Termination
    terminated = Column(Boolean, default=False)
    termination_date = Column(Date, nullable=True)
    termination_reason = Column(Text, nullable=True)

    # Compliance tracking
    last_compliance_review = Column(Date, nullable=True)
    compliance_notes = Column(Text, nullable=True)

    # Parent BAA (for subcontractors)
    parent_baa_id = Column(UUID(as_uuid=True), ForeignKey("hipaa_business_associate_agreements.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)

    __table_args__ = (
        Index("ix_baa_status_expiration", "status", "expiration_date"),
        Index("ix_baa_counterparty", "counterparty_name"),
    )


class BAAAmendment(Base):
    """
    BAA amendment tracking.
    """
    __tablename__ = "hipaa_baa_amendments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    baa_id = Column(UUID(as_uuid=True), ForeignKey("hipaa_business_associate_agreements.id"), nullable=False)

    amendment_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    changes_summary = Column(Text, nullable=False)

    effective_date = Column(Date, nullable=False)
    document_url = Column(String(500), nullable=True)

    # Execution
    executed = Column(Boolean, default=False)
    execution_date = Column(Date, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)


class BAATemplate(Base):
    """
    BAA template library.
    """
    __tablename__ = "hipaa_baa_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    template_type = Column(Enum(BAAType), nullable=False)

    # Content
    template_content = Column(Text, nullable=False)
    variable_fields = Column(JSONB, nullable=True)  # Placeholders in template

    # Version control
    version = Column(String(20), nullable=False)
    previous_version_id = Column(UUID(as_uuid=True), nullable=True)

    # Approval
    approved = Column(Boolean, default=False)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    legal_review_date = Column(Date, nullable=True)

    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)


# ============================================================================
# Training Management Models
# ============================================================================

class TrainingModule(Base):
    """
    HIPAA training module definition.
    """
    __tablename__ = "hipaa_training_modules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    training_type = Column(Enum(TrainingType), nullable=False)

    # Content
    content_url = Column(String(500), nullable=True)  # LMS link or content location
    duration_minutes = Column(Integer, nullable=False)
    passing_score = Column(Integer, default=80)

    # Requirements
    required_for_roles = Column(ARRAY(String), nullable=True)
    required_for_all = Column(Boolean, default=False)
    required_for_phi_access = Column(Boolean, default=False)

    # Recurrence
    recurrence_months = Column(Integer, nullable=True)  # null = one-time

    # Version
    version = Column(String(20), nullable=False)
    effective_date = Column(Date, nullable=False)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)


class TrainingAssignment(Base):
    """
    Training assignment for workforce members.
    """
    __tablename__ = "hipaa_training_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    module_id = Column(UUID(as_uuid=True), ForeignKey("hipaa_training_modules.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_name = Column(String(200), nullable=True)
    user_email = Column(String(200), nullable=True)
    user_role = Column(String(100), nullable=True)

    # Assignment
    assigned_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=False)
    assigned_by = Column(UUID(as_uuid=True), nullable=True)

    # Status
    status = Column(Enum(TrainingStatus), default=TrainingStatus.ASSIGNED)

    # Completion
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    score = Column(Integer, nullable=True)
    passed = Column(Boolean, nullable=True)
    attempts = Column(Integer, default=0)

    # Certificate
    certificate_id = Column(String(100), nullable=True)
    certificate_url = Column(String(500), nullable=True)

    # Reminders
    reminder_sent_count = Column(Integer, default=0)
    last_reminder_sent = Column(DateTime, nullable=True)

    # Next recurrence (for annual refreshers)
    next_due_date = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_training_assignment_status", "status", "due_date"),
        Index("ix_training_assignment_user", "user_id", "module_id"),
    )


class PolicyDocument(Base):
    """
    HIPAA policy document management.
    """
    __tablename__ = "hipaa_policy_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    title = Column(String(300), nullable=False)
    policy_number = Column(String(50), unique=True, nullable=False)
    category = Column(String(100), nullable=False)

    # Content
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)

    # Version control
    version = Column(String(20), nullable=False)
    previous_version_id = Column(UUID(as_uuid=True), nullable=True)
    effective_date = Column(Date, nullable=False)
    review_date = Column(Date, nullable=True)

    # Approval
    approved = Column(Boolean, default=False)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    # Acknowledgment requirements
    requires_acknowledgment = Column(Boolean, default=True)
    required_for_roles = Column(ARRAY(String), nullable=True)
    required_for_all = Column(Boolean, default=False)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)


class PolicyAcknowledgment(Base):
    """
    Policy acknowledgment tracking.
    """
    __tablename__ = "hipaa_policy_acknowledgments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    policy_id = Column(UUID(as_uuid=True), ForeignKey("hipaa_policy_documents.id"), nullable=False)
    policy_version = Column(String(20), nullable=False)

    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_name = Column(String(200), nullable=True)
    user_role = Column(String(100), nullable=True)

    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime, nullable=True)

    # Electronic signature
    signature_ip = Column(INET, nullable=True)
    signature_user_agent = Column(Text, nullable=True)
    signature_hash = Column(String(64), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("policy_id", "policy_version", "user_id",
                        name="uq_policy_acknowledgment"),
    )


# ============================================================================
# Risk Assessment Models
# ============================================================================

class RiskAssessment(Base):
    """
    HIPAA risk assessment.
    """
    __tablename__ = "hipaa_risk_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Assessment identification
    assessment_number = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    assessment_type = Column(String(50), nullable=False)  # annual, targeted, post-incident

    # Scope
    scope_description = Column(Text, nullable=False)
    systems_in_scope = Column(ARRAY(String), nullable=True)
    departments_in_scope = Column(ARRAY(String), nullable=True)

    # Timeline
    start_date = Column(Date, nullable=False)
    target_completion_date = Column(Date, nullable=False)
    actual_completion_date = Column(Date, nullable=True)

    # Lead assessor
    lead_assessor_id = Column(UUID(as_uuid=True), nullable=False)
    lead_assessor_name = Column(String(200), nullable=True)
    assessment_team = Column(JSONB, nullable=True)  # List of team members

    # Methodology
    methodology = Column(String(100), nullable=True)  # NIST, HITRUST, etc.
    methodology_version = Column(String(20), nullable=True)

    # Summary scores
    total_risks_identified = Column(Integer, default=0)
    critical_risks = Column(Integer, default=0)
    high_risks = Column(Integer, default=0)
    medium_risks = Column(Integer, default=0)
    low_risks = Column(Integer, default=0)

    # Overall rating
    overall_risk_level = Column(Enum(RiskLevel), nullable=True)

    # Approval
    status = Column(String(50), default="in_progress")
    approved = Column(Boolean, default=False)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    # Documentation
    executive_summary = Column(Text, nullable=True)
    report_url = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)


class RiskItem(Base):
    """
    Individual risk item identified in assessment.
    """
    __tablename__ = "hipaa_risk_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    assessment_id = Column(UUID(as_uuid=True), ForeignKey("hipaa_risk_assessments.id"), nullable=False)

    # Risk identification
    risk_number = Column(String(50), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=False)

    # Categorization
    category = Column(Enum(RiskCategory), nullable=False)
    safeguard_type = Column(String(100), nullable=True)  # Administrative, Physical, Technical
    hipaa_reference = Column(String(100), nullable=True)  # §164.xxx

    # Threat/vulnerability
    threat_source = Column(String(200), nullable=True)
    vulnerability = Column(Text, nullable=True)
    existing_controls = Column(Text, nullable=True)

    # Risk scoring
    likelihood = Column(Integer, nullable=False)  # 1-5
    impact = Column(Integer, nullable=False)      # 1-5
    inherent_risk_score = Column(Integer, nullable=False)  # likelihood * impact
    risk_level = Column(Enum(RiskLevel), nullable=False)

    # With controls
    control_effectiveness = Column(Integer, nullable=True)  # 1-5
    residual_risk_score = Column(Integer, nullable=True)
    residual_risk_level = Column(Enum(RiskLevel), nullable=True)

    # Evidence
    evidence = Column(Text, nullable=True)
    affected_assets = Column(ARRAY(String), nullable=True)

    # Status
    status = Column(Enum(RemediationStatus), default=RemediationStatus.PLANNED)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("assessment_id", "risk_number", name="uq_risk_item_number"),
        Index("ix_risk_item_level", "risk_level", "status"),
    )


class RemediationPlan(Base):
    """
    Risk remediation plan and tracking.
    """
    __tablename__ = "hipaa_remediation_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    risk_id = Column(UUID(as_uuid=True), ForeignKey("hipaa_risk_items.id"), nullable=False)

    # Remediation details
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=False)

    # Assignment
    owner_id = Column(UUID(as_uuid=True), nullable=False)
    owner_name = Column(String(200), nullable=True)

    # Timeline
    planned_start_date = Column(Date, nullable=False)
    target_completion_date = Column(Date, nullable=False)
    actual_start_date = Column(Date, nullable=True)
    actual_completion_date = Column(Date, nullable=True)

    # Status
    status = Column(Enum(RemediationStatus), default=RemediationStatus.PLANNED)
    percent_complete = Column(Integer, default=0)

    # For accepted risks
    risk_acceptance_approved = Column(Boolean, default=False)
    risk_acceptance_approved_by = Column(UUID(as_uuid=True), nullable=True)
    risk_acceptance_reason = Column(Text, nullable=True)
    risk_acceptance_expiration = Column(Date, nullable=True)

    # Verification
    verification_required = Column(Boolean, default=True)
    verified_by = Column(UUID(as_uuid=True), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verification_evidence = Column(Text, nullable=True)

    # Cost tracking
    estimated_cost = Column(Float, nullable=True)
    actual_cost = Column(Float, nullable=True)

    # Notes and updates
    implementation_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)

    __table_args__ = (
        Index("ix_remediation_status_date", "status", "target_completion_date"),
    )


class RiskRegister(Base):
    """
    Consolidated risk register for ongoing monitoring.
    """
    __tablename__ = "hipaa_risk_register"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Risk identification (can link to assessment or be standalone)
    risk_id = Column(String(50), unique=True, nullable=False)
    source_assessment_id = Column(UUID(as_uuid=True), ForeignKey("hipaa_risk_assessments.id"), nullable=True)
    source_risk_item_id = Column(UUID(as_uuid=True), ForeignKey("hipaa_risk_items.id"), nullable=True)

    # Risk details
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(Enum(RiskCategory), nullable=False)

    # Current risk level
    current_risk_level = Column(Enum(RiskLevel), nullable=False)
    current_likelihood = Column(Integer, nullable=False)
    current_impact = Column(Integer, nullable=False)

    # Target risk level
    target_risk_level = Column(Enum(RiskLevel), nullable=True)

    # Risk treatment
    treatment_strategy = Column(String(50), nullable=False)  # mitigate, accept, transfer, avoid
    treatment_status = Column(Enum(RemediationStatus), default=RemediationStatus.PLANNED)

    # Owner
    risk_owner_id = Column(UUID(as_uuid=True), nullable=False)
    risk_owner_name = Column(String(200), nullable=True)

    # Timeline
    identified_date = Column(Date, nullable=False)
    target_resolution_date = Column(Date, nullable=True)
    last_review_date = Column(Date, nullable=True)
    next_review_date = Column(Date, nullable=True)

    # History
    risk_trend = Column(String(20), nullable=True)  # increasing, stable, decreasing
    historical_scores = Column(JSONB, nullable=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_risk_register_level", "current_risk_level", "is_active"),
    )
