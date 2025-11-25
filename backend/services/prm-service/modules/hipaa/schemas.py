"""
HIPAA Compliance Schemas

Pydantic schemas for EPIC-022: HIPAA Compliance
Request/Response validation for all HIPAA compliance operations.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, EmailStr
from uuid import UUID


# ============================================================================
# Enums (mirrored from models for Pydantic)
# ============================================================================

class AuditAction(str, Enum):
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


class AuditOutcome(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class PHICategory(str, Enum):
    DEMOGRAPHICS = "demographics"
    MEDICAL_RECORDS = "medical_records"
    PRESCRIPTION = "prescription"
    LAB_RESULTS = "lab_results"
    IMAGING = "imaging"
    BILLING = "billing"
    INSURANCE = "insurance"
    MENTAL_HEALTH = "mental_health"
    SUBSTANCE_ABUSE = "substance_abuse"
    HIV_AIDS = "hiv_aids"
    GENETIC = "genetic"
    PSYCHOTHERAPY = "psychotherapy"
    FULL_RECORD = "full_record"


class AccessJustification(str, Enum):
    TREATMENT = "treatment"
    PAYMENT = "payment"
    OPERATIONS = "operations"
    EMERGENCY = "emergency"
    RESEARCH = "research"
    PUBLIC_HEALTH = "public_health"
    LAW_ENFORCEMENT = "law_enforcement"
    PATIENT_REQUEST = "patient_request"
    BREAK_THE_GLASS = "break_the_glass"


class RelationshipType(str, Enum):
    PRIMARY_CARE = "primary_care"
    SPECIALIST_REFERRAL = "specialist_referral"
    CARE_TEAM = "care_team"
    CONSULTING = "consulting"
    EMERGENCY = "emergency"
    FACILITY_BASED = "facility_based"
    HISTORICAL = "historical"


class RelationshipStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    TERMINATED = "terminated"


class AccessRequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    REVOKED = "revoked"


class CertificationStatus(str, Enum):
    PENDING = "pending"
    CERTIFIED = "certified"
    DECERTIFIED = "decertified"
    ESCALATED = "escalated"


class AnomalyType(str, Enum):
    AFTER_HOURS = "after_hours"
    BULK_ACCESS = "bulk_access"
    VIP_ACCESS = "vip_access"
    EMPLOYEE_ACCESS = "employee_access"
    UNUSUAL_PATTERN = "unusual_pattern"
    GEOGRAPHIC_ANOMALY = "geographic_anomaly"
    HIGH_VOLUME = "high_volume"
    UNAUTHORIZED_RESOURCE = "unauthorized_resource"


class AnomalySeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RetentionCategory(str, Enum):
    MEDICAL_RECORD = "medical_record"
    MINOR_RECORD = "minor_record"
    BILLING_RECORD = "billing_record"
    AUDIT_LOG = "audit_log"
    CORRESPONDENCE = "correspondence"
    CONSENT_FORM = "consent_form"
    RESEARCH_DATA = "research_data"
    IMAGING = "imaging"
    LAB_RESULT = "lab_result"
    PRESCRIPTION = "prescription"


class RetentionStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    PENDING_DESTRUCTION = "pending_destruction"
    DESTROYED = "destroyed"
    LEGAL_HOLD = "legal_hold"


class LegalHoldType(str, Enum):
    LITIGATION = "litigation"
    REGULATORY = "regulatory"
    INTERNAL_INVESTIGATION = "internal_investigation"
    PRESERVATION_NOTICE = "preservation_notice"
    HIPAA_INVESTIGATION = "hipaa_investigation"


class LegalHoldStatus(str, Enum):
    ACTIVE = "active"
    PENDING_RELEASE = "pending_release"
    RELEASED = "released"


class DestructionMethod(str, Enum):
    DELETION = "deletion"
    SHREDDING = "shredding"
    CRYPTOGRAPHIC_ERASURE = "cryptographic_erasure"
    PHYSICAL_DESTRUCTION = "physical_destruction"
    DEGAUSSING = "degaussing"


class RightOfAccessStatus(str, Enum):
    RECEIVED = "received"
    IDENTITY_VERIFICATION = "identity_verification"
    PROCESSING = "processing"
    READY = "ready"
    DELIVERED = "delivered"
    DENIED = "denied"
    EXTENDED = "extended"


class BreachStatus(str, Enum):
    SUSPECTED = "suspected"
    CONFIRMED = "confirmed"
    NOT_A_BREACH = "not_a_breach"
    INVESTIGATING = "investigating"
    NOTIFYING = "notifying"
    CLOSED = "closed"


class BreachType(str, Enum):
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    THEFT = "theft"
    LOSS = "loss"
    IMPROPER_DISPOSAL = "improper_disposal"
    HACKING = "hacking"
    UNAUTHORIZED_DISCLOSURE = "unauthorized_disclosure"
    VENDOR_INCIDENT = "vendor_incident"
    EMPLOYEE_ERROR = "employee_error"


class NotificationType(str, Enum):
    HHS_NOTIFICATION = "hhs_notification"
    PATIENT_NOTIFICATION = "patient_notification"
    MEDIA_NOTIFICATION = "media_notification"
    STATE_NOTIFICATION = "state_notification"


class NotificationStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    BOUNCED = "bounced"
    FAILED = "failed"


class BAAType(str, Enum):
    CUSTOMER = "customer"
    VENDOR = "vendor"
    SUBCONTRACTOR = "subcontractor"


class BAAStatus(str, Enum):
    DRAFT = "draft"
    NEGOTIATING = "negotiating"
    PENDING_SIGNATURE = "pending_signature"
    EXECUTED = "executed"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class TrainingType(str, Enum):
    HIPAA_BASICS = "hipaa_basics"
    PRIVACY_RULE = "privacy_rule"
    SECURITY_RULE = "security_rule"
    BREACH_RESPONSE = "breach_response"
    ROLE_SPECIFIC = "role_specific"
    SECURITY_AWARENESS = "security_awareness"
    ANNUAL_REFRESHER = "annual_refresher"


class TrainingStatus(str, Enum):
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    WAIVED = "waived"


class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class RiskCategory(str, Enum):
    ADMINISTRATIVE = "administrative"
    PHYSICAL = "physical"
    TECHNICAL = "technical"
    ORGANIZATIONAL = "organizational"
    COMPLIANCE = "compliance"


class RemediationStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VERIFIED = "verified"
    DEFERRED = "deferred"
    ACCEPTED = "accepted"


# ============================================================================
# Audit Logging Schemas
# ============================================================================

class PHIAuditLogCreate(BaseModel):
    """Create a new PHI audit log entry"""
    event_type: str
    action: AuditAction
    outcome: AuditOutcome = AuditOutcome.SUCCESS
    user_id: Optional[UUID] = None
    user_type: Optional[str] = None
    user_name: Optional[str] = None
    user_role: Optional[str] = None
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[UUID] = None
    request_id: Optional[str] = None
    phi_category: PHICategory
    resource_type: str
    resource_id: Optional[UUID] = None
    patient_id: Optional[UUID] = None
    patient_mrn: Optional[str] = None
    encounter_id: Optional[UUID] = None
    justification: Optional[AccessJustification] = None
    justification_details: Optional[str] = None
    fields_accessed: Optional[List[str]] = None
    query_parameters: Optional[Dict[str, Any]] = None
    data_before: Optional[Dict[str, Any]] = None
    data_after: Optional[Dict[str, Any]] = None
    service_name: Optional[str] = None
    api_endpoint: Optional[str] = None
    http_method: Optional[str] = None
    response_code: Optional[int] = None


class PHIAuditLogResponse(BaseModel):
    """PHI audit log response"""
    id: UUID
    tenant_id: UUID
    event_id: str
    event_type: str
    action: AuditAction
    outcome: AuditOutcome
    recorded_at: datetime
    user_id: Optional[UUID]
    user_name: Optional[str]
    user_role: Optional[str]
    source_ip: Optional[str]
    phi_category: PHICategory
    resource_type: str
    resource_id: Optional[UUID]
    patient_id: Optional[UUID]
    justification: Optional[AccessJustification]
    record_hash: str

    class Config:
        from_attributes = True


class AuditLogSearchRequest(BaseModel):
    """Search parameters for audit logs"""
    user_id: Optional[UUID] = None
    patient_id: Optional[UUID] = None
    action: Optional[AuditAction] = None
    phi_category: Optional[PHICategory] = None
    resource_type: Optional[str] = None
    outcome: Optional[AuditOutcome] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    source_ip: Optional[str] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)


class AuditLogSearchResponse(BaseModel):
    """Audit log search results"""
    logs: List[PHIAuditLogResponse]
    total: int
    has_more: bool


class AuditRetentionPolicyCreate(BaseModel):
    """Create audit retention policy"""
    name: str
    description: Optional[str] = None
    retention_days: int = Field(default=2555, ge=365)  # Minimum 1 year
    archive_after_days: int = Field(default=365, ge=30)
    archive_storage_class: str = "GLACIER"
    applies_to_actions: Optional[List[str]] = None
    applies_to_categories: Optional[List[str]] = None
    is_default: bool = False


class AuditRetentionPolicyResponse(BaseModel):
    """Audit retention policy response"""
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    retention_days: int
    archive_after_days: int
    is_active: bool
    is_default: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Access Control Schemas
# ============================================================================

class TreatmentRelationshipCreate(BaseModel):
    """Create treatment relationship"""
    patient_id: UUID
    provider_id: UUID
    provider_type: str
    relationship_type: RelationshipType
    effective_date: date
    expiration_date: Optional[date] = None
    referral_id: Optional[UUID] = None
    authorization_number: Optional[str] = None
    care_team_id: Optional[UUID] = None
    care_team_role: Optional[str] = None
    facility_id: Optional[UUID] = None
    department: Optional[str] = None
    allowed_phi_categories: Optional[List[str]] = None
    restricted_phi_categories: Optional[List[str]] = None


class TreatmentRelationshipResponse(BaseModel):
    """Treatment relationship response"""
    id: UUID
    tenant_id: UUID
    patient_id: UUID
    provider_id: UUID
    provider_type: str
    relationship_type: RelationshipType
    status: RelationshipStatus
    effective_date: date
    expiration_date: Optional[date]
    care_team_role: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AccessRequestCreate(BaseModel):
    """Create PHI access request"""
    patient_id: UUID
    requested_phi_categories: List[str]
    requested_resources: Optional[Dict[str, Any]] = None
    justification: AccessJustification
    justification_details: str
    clinical_context: Optional[str] = None
    access_duration_hours: Optional[int] = Field(default=24, le=720)


class AccessRequestResponse(BaseModel):
    """Access request response"""
    id: UUID
    tenant_id: UUID
    request_number: str
    requester_id: UUID
    requester_name: Optional[str]
    patient_id: UUID
    requested_phi_categories: List[str]
    justification: AccessJustification
    status: AccessRequestStatus
    approver_name: Optional[str]
    approval_date: Optional[datetime]
    access_start: Optional[datetime]
    access_end: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class AccessRequestApproval(BaseModel):
    """Approve or deny access request"""
    approved: bool
    denial_reason: Optional[str] = None
    access_duration_hours: Optional[int] = None


class AccessCertificationResponse(BaseModel):
    """Access certification response"""
    id: UUID
    campaign_id: UUID
    campaign_name: Optional[str]
    user_id: UUID
    user_name: Optional[str]
    role_name: Optional[str]
    access_type: str
    access_details: Dict[str, Any]
    reviewer_name: Optional[str]
    status: CertificationStatus
    due_date: datetime
    certification_date: Optional[datetime]

    class Config:
        from_attributes = True


class CertificationCampaignCreate(BaseModel):
    """Create certification campaign"""
    name: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    scope_type: str
    scope_criteria: Optional[Dict[str, Any]] = None


class CertificationCampaignResponse(BaseModel):
    """Certification campaign response"""
    id: UUID
    tenant_id: UUID
    name: str
    start_date: datetime
    end_date: datetime
    scope_type: str
    total_certifications: int
    completed_certifications: int
    certified_count: int
    decertified_count: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AccessAnomalyResponse(BaseModel):
    """Access anomaly response"""
    id: UUID
    tenant_id: UUID
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    user_id: UUID
    user_name: Optional[str]
    detected_at: datetime
    description: str
    evidence: Dict[str, Any]
    acknowledged: bool
    resolved: bool
    false_positive: bool

    class Config:
        from_attributes = True


class AnomalyAcknowledge(BaseModel):
    """Acknowledge anomaly"""
    investigation_notes: Optional[str] = None


class AnomalyResolve(BaseModel):
    """Resolve anomaly"""
    resolution: str
    false_positive: bool = False


class VIPPatientCreate(BaseModel):
    """Designate VIP patient"""
    patient_id: UUID
    vip_reason: str
    enhanced_monitoring: bool = True
    access_alerts_enabled: bool = True
    allowed_user_ids: Optional[List[UUID]] = None
    allowed_roles: Optional[List[str]] = None
    alert_recipients: Optional[List[str]] = None


class VIPPatientResponse(BaseModel):
    """VIP patient response"""
    id: UUID
    tenant_id: UUID
    patient_id: UUID
    vip_reason: str
    enhanced_monitoring: bool
    access_alerts_enabled: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Data Retention Schemas
# ============================================================================

class RetentionPolicyCreate(BaseModel):
    """Create retention policy"""
    name: str
    description: Optional[str] = None
    category: RetentionCategory
    resource_types: Optional[List[str]] = None
    retention_years: int = Field(ge=1, le=50)
    retention_months: int = Field(default=0, ge=0, le=11)
    applies_to_minors: bool = False
    minor_retention_from_age: int = 18
    minor_additional_years: int = 0
    jurisdiction: Optional[str] = None
    regulation_reference: Optional[str] = None
    destruction_method: DestructionMethod = DestructionMethod.CRYPTOGRAPHIC_ERASURE
    require_destruction_certificate: bool = True
    archive_before_destruction: bool = True
    is_default: bool = False


class RetentionPolicyResponse(BaseModel):
    """Retention policy response"""
    id: UUID
    tenant_id: UUID
    name: str
    category: RetentionCategory
    retention_years: int
    retention_months: int
    jurisdiction: Optional[str]
    destruction_method: DestructionMethod
    is_active: bool
    is_default: bool
    created_at: datetime

    class Config:
        from_attributes = True


class RetentionScheduleResponse(BaseModel):
    """Retention schedule response"""
    id: UUID
    resource_type: str
    resource_id: UUID
    patient_id: Optional[UUID]
    record_date: date
    scheduled_destruction_date: date
    status: RetentionStatus
    archived_at: Optional[datetime]

    class Config:
        from_attributes = True


class LegalHoldCreate(BaseModel):
    """Create legal hold"""
    name: str
    description: Optional[str] = None
    hold_type: LegalHoldType
    matter_reference: Optional[str] = None
    scope_type: str
    scope_criteria: Dict[str, Any]
    affected_patient_ids: Optional[List[UUID]] = None
    legal_contact_name: Optional[str] = None
    legal_contact_email: Optional[EmailStr] = None
    effective_date: date


class LegalHoldResponse(BaseModel):
    """Legal hold response"""
    id: UUID
    tenant_id: UUID
    hold_number: str
    name: str
    hold_type: LegalHoldType
    matter_reference: Optional[str]
    status: LegalHoldStatus
    effective_date: date
    release_date: Optional[date]
    affected_record_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class LegalHoldRelease(BaseModel):
    """Release legal hold"""
    release_reason: str


class DestructionCertificateResponse(BaseModel):
    """Destruction certificate response"""
    id: UUID
    tenant_id: UUID
    certificate_number: str
    destruction_date: datetime
    destruction_method: DestructionMethod
    record_count: int
    resource_types: List[str]
    verified: bool
    certificate_hash: str
    created_at: datetime

    class Config:
        from_attributes = True


class RightOfAccessRequestCreate(BaseModel):
    """Create Right of Access request"""
    patient_id: UUID
    requestor_type: str
    representative_name: Optional[str] = None
    representative_relationship: Optional[str] = None
    delivery_email: Optional[EmailStr] = None
    delivery_address: Optional[str] = None
    delivery_method: str
    requested_records: Dict[str, Any]
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None


class RightOfAccessRequestResponse(BaseModel):
    """Right of Access request response"""
    id: UUID
    tenant_id: UUID
    request_number: str
    patient_id: UUID
    requestor_type: str
    delivery_method: str
    status: RightOfAccessStatus
    received_date: datetime
    due_date: datetime
    extension_granted: bool
    extended_due_date: Optional[datetime]
    delivered_at: Optional[datetime]
    denied: bool
    created_at: datetime

    class Config:
        from_attributes = True


class RightOfAccessVerifyIdentity(BaseModel):
    """Verify identity for Right of Access request"""
    verification_method: str


class RightOfAccessExtend(BaseModel):
    """Extend Right of Access deadline"""
    extension_reason: str


class RightOfAccessDeliver(BaseModel):
    """Mark Right of Access as delivered"""
    export_format: str
    export_location: str
    delivery_confirmation: Optional[str] = None


class RightOfAccessDeny(BaseModel):
    """Deny Right of Access request"""
    denial_reason: str
    denial_code: str


# ============================================================================
# Breach Management Schemas
# ============================================================================

class BreachIncidentCreate(BaseModel):
    """Create breach incident"""
    discovered_date: datetime
    discovery_method: Optional[str] = None
    breach_type: BreachType
    description: str
    breach_date: Optional[date] = None
    phi_categories_involved: List[str]
    phi_description: Optional[str] = None
    breach_source: Optional[str] = None


class BreachIncidentResponse(BaseModel):
    """Breach incident response"""
    id: UUID
    tenant_id: UUID
    incident_number: str
    discovered_date: datetime
    breach_type: BreachType
    status: BreachStatus
    affected_individuals_count: int
    phi_categories_involved: List[str]
    hhs_notification_deadline: Optional[datetime]
    patient_notification_deadline: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class BreachIncidentUpdate(BaseModel):
    """Update breach incident"""
    status: Optional[BreachStatus] = None
    affected_individuals_count: Optional[int] = None
    affected_patient_ids: Optional[List[UUID]] = None
    root_cause: Optional[str] = None
    containment_actions: Optional[str] = None
    remediation_actions: Optional[str] = None
    lessons_learned: Optional[str] = None


class BreachAssessmentCreate(BaseModel):
    """Create breach risk assessment"""
    incident_id: UUID
    factor1_phi_nature: str
    factor1_phi_types: List[str]
    factor1_identifiability: str
    factor1_score: int = Field(ge=1, le=10)
    factor2_recipient_description: str
    factor2_recipient_type: Optional[str] = None
    factor2_obligation_to_protect: Optional[bool] = None
    factor2_score: int = Field(ge=1, le=10)
    factor3_phi_accessed: str
    factor3_access_evidence: Optional[str] = None
    factor3_score: int = Field(ge=1, le=10)
    factor4_mitigation_actions: str
    factor4_assurances_obtained: bool = False
    factor4_phi_returned_destroyed: bool = False
    factor4_score: int = Field(ge=1, le=10)
    low_probability_exception: bool = False
    exception_justification: Optional[str] = None


class BreachAssessmentResponse(BaseModel):
    """Breach assessment response"""
    id: UUID
    incident_id: UUID
    assessed_date: datetime
    assessor_name: Optional[str]
    factor1_score: int
    factor2_score: int
    factor3_score: int
    factor4_score: int
    overall_risk_score: int
    risk_level: RiskLevel
    notification_required: bool
    notification_determination_reason: str
    approved: bool

    class Config:
        from_attributes = True


class BreachNotificationCreate(BaseModel):
    """Create breach notification"""
    incident_id: UUID
    notification_type: NotificationType
    recipient_type: str
    recipient_name: Optional[str] = None
    recipient_email: Optional[EmailStr] = None
    recipient_address: Optional[str] = None
    patient_id: Optional[UUID] = None
    notification_content: str
    letter_template_used: Optional[str] = None
    delivery_method: Optional[str] = None
    scheduled_date: Optional[datetime] = None


class BreachNotificationResponse(BaseModel):
    """Breach notification response"""
    id: UUID
    incident_id: UUID
    notification_type: NotificationType
    recipient_type: str
    recipient_name: Optional[str]
    status: NotificationStatus
    scheduled_date: Optional[datetime]
    sent_date: Optional[datetime]
    delivered_date: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class BreachNotificationSend(BaseModel):
    """Send breach notification"""
    delivery_method: str


# ============================================================================
# BAA Management Schemas
# ============================================================================

class BusinessAssociateAgreementCreate(BaseModel):
    """Create BAA"""
    baa_type: BAAType
    counterparty_name: str
    counterparty_type: str
    counterparty_address: Optional[str] = None
    counterparty_contact_name: Optional[str] = None
    counterparty_contact_email: Optional[EmailStr] = None
    counterparty_contact_phone: Optional[str] = None
    services_description: str
    phi_categories_covered: List[str]
    template_used: Optional[str] = None
    effective_date: Optional[date] = None
    expiration_date: Optional[date] = None
    auto_renew: bool = False
    renewal_term_months: Optional[int] = None
    parent_baa_id: Optional[UUID] = None


class BusinessAssociateAgreementResponse(BaseModel):
    """BAA response"""
    id: UUID
    tenant_id: UUID
    baa_number: str
    baa_type: BAAType
    counterparty_name: str
    counterparty_type: str
    services_description: str
    status: BAAStatus
    execution_date: Optional[date]
    effective_date: Optional[date]
    expiration_date: Optional[date]
    auto_renew: bool
    terminated: bool
    created_at: datetime

    class Config:
        from_attributes = True


class BAAExecute(BaseModel):
    """Execute BAA"""
    our_signatory_name: str
    our_signatory_title: str
    counterparty_signatory_name: str
    counterparty_signatory_title: str
    execution_date: date
    effective_date: date
    document_url: Optional[str] = None


class BAATerminate(BaseModel):
    """Terminate BAA"""
    termination_reason: str
    termination_date: date


class BAAAmendmentCreate(BaseModel):
    """Create BAA amendment"""
    baa_id: UUID
    description: str
    changes_summary: str
    effective_date: date
    document_url: Optional[str] = None


class BAAAmendmentResponse(BaseModel):
    """BAA amendment response"""
    id: UUID
    baa_id: UUID
    amendment_number: int
    description: str
    effective_date: date
    executed: bool
    execution_date: Optional[date]
    created_at: datetime

    class Config:
        from_attributes = True


class BAATemplateCreate(BaseModel):
    """Create BAA template"""
    name: str
    description: Optional[str] = None
    template_type: BAAType
    template_content: str
    variable_fields: Optional[Dict[str, Any]] = None
    version: str
    is_default: bool = False


class BAATemplateResponse(BaseModel):
    """BAA template response"""
    id: UUID
    tenant_id: UUID
    name: str
    template_type: BAAType
    version: str
    approved: bool
    is_active: bool
    is_default: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Training Management Schemas
# ============================================================================

class TrainingModuleCreate(BaseModel):
    """Create training module"""
    name: str
    description: Optional[str] = None
    training_type: TrainingType
    content_url: Optional[str] = None
    duration_minutes: int = Field(ge=1)
    passing_score: int = Field(default=80, ge=0, le=100)
    required_for_roles: Optional[List[str]] = None
    required_for_all: bool = False
    required_for_phi_access: bool = False
    recurrence_months: Optional[int] = None
    version: str
    effective_date: date


class TrainingModuleResponse(BaseModel):
    """Training module response"""
    id: UUID
    tenant_id: UUID
    name: str
    training_type: TrainingType
    duration_minutes: int
    passing_score: int
    required_for_all: bool
    required_for_phi_access: bool
    recurrence_months: Optional[int]
    version: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TrainingAssignmentCreate(BaseModel):
    """Create training assignment"""
    module_id: UUID
    user_id: UUID
    user_name: Optional[str] = None
    user_email: Optional[EmailStr] = None
    user_role: Optional[str] = None
    due_date: datetime


class TrainingAssignmentResponse(BaseModel):
    """Training assignment response"""
    id: UUID
    tenant_id: UUID
    module_id: UUID
    user_id: UUID
    user_name: Optional[str]
    assigned_date: datetime
    due_date: datetime
    status: TrainingStatus
    completed_at: Optional[datetime]
    score: Optional[int]
    passed: Optional[bool]
    certificate_id: Optional[str]

    class Config:
        from_attributes = True


class TrainingComplete(BaseModel):
    """Complete training"""
    score: int = Field(ge=0, le=100)


class PolicyDocumentCreate(BaseModel):
    """Create policy document"""
    title: str
    policy_number: str
    category: str
    content: str
    summary: Optional[str] = None
    version: str
    effective_date: date
    review_date: Optional[date] = None
    requires_acknowledgment: bool = True
    required_for_roles: Optional[List[str]] = None
    required_for_all: bool = False


class PolicyDocumentResponse(BaseModel):
    """Policy document response"""
    id: UUID
    tenant_id: UUID
    title: str
    policy_number: str
    category: str
    version: str
    effective_date: date
    requires_acknowledgment: bool
    approved: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PolicyAcknowledgmentResponse(BaseModel):
    """Policy acknowledgment response"""
    id: UUID
    policy_id: UUID
    policy_version: str
    user_id: UUID
    user_name: Optional[str]
    acknowledged: bool
    acknowledged_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================================================
# Risk Assessment Schemas
# ============================================================================

class RiskAssessmentCreate(BaseModel):
    """Create risk assessment"""
    name: str
    description: Optional[str] = None
    assessment_type: str
    scope_description: str
    systems_in_scope: Optional[List[str]] = None
    departments_in_scope: Optional[List[str]] = None
    start_date: date
    target_completion_date: date
    methodology: Optional[str] = None
    methodology_version: Optional[str] = None
    assessment_team: Optional[List[Dict[str, Any]]] = None


class RiskAssessmentResponse(BaseModel):
    """Risk assessment response"""
    id: UUID
    tenant_id: UUID
    assessment_number: str
    name: str
    assessment_type: str
    start_date: date
    target_completion_date: date
    actual_completion_date: Optional[date]
    lead_assessor_name: Optional[str]
    total_risks_identified: int
    critical_risks: int
    high_risks: int
    medium_risks: int
    low_risks: int
    overall_risk_level: Optional[RiskLevel]
    status: str
    approved: bool
    created_at: datetime

    class Config:
        from_attributes = True


class RiskAssessmentComplete(BaseModel):
    """Complete risk assessment"""
    executive_summary: str
    overall_risk_level: RiskLevel
    report_url: Optional[str] = None


class RiskItemCreate(BaseModel):
    """Create risk item"""
    assessment_id: UUID
    risk_number: str
    title: str
    description: str
    category: RiskCategory
    safeguard_type: Optional[str] = None
    hipaa_reference: Optional[str] = None
    threat_source: Optional[str] = None
    vulnerability: Optional[str] = None
    existing_controls: Optional[str] = None
    likelihood: int = Field(ge=1, le=5)
    impact: int = Field(ge=1, le=5)
    control_effectiveness: Optional[int] = Field(default=None, ge=1, le=5)
    evidence: Optional[str] = None
    affected_assets: Optional[List[str]] = None


class RiskItemResponse(BaseModel):
    """Risk item response"""
    id: UUID
    assessment_id: UUID
    risk_number: str
    title: str
    category: RiskCategory
    hipaa_reference: Optional[str]
    likelihood: int
    impact: int
    inherent_risk_score: int
    risk_level: RiskLevel
    residual_risk_score: Optional[int]
    residual_risk_level: Optional[RiskLevel]
    status: RemediationStatus
    created_at: datetime

    class Config:
        from_attributes = True


class RemediationPlanCreate(BaseModel):
    """Create remediation plan"""
    risk_id: UUID
    title: str
    description: str
    owner_id: UUID
    owner_name: Optional[str] = None
    planned_start_date: date
    target_completion_date: date
    estimated_cost: Optional[float] = None
    verification_required: bool = True


class RemediationPlanResponse(BaseModel):
    """Remediation plan response"""
    id: UUID
    risk_id: UUID
    title: str
    owner_name: Optional[str]
    planned_start_date: date
    target_completion_date: date
    actual_completion_date: Optional[date]
    status: RemediationStatus
    percent_complete: int
    estimated_cost: Optional[float]
    actual_cost: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class RemediationUpdate(BaseModel):
    """Update remediation plan"""
    status: Optional[RemediationStatus] = None
    percent_complete: Optional[int] = Field(default=None, ge=0, le=100)
    actual_start_date: Optional[date] = None
    actual_cost: Optional[float] = None
    implementation_notes: Optional[str] = None


class RemediationVerify(BaseModel):
    """Verify remediation"""
    verification_evidence: str


class RiskAcceptance(BaseModel):
    """Accept risk"""
    risk_acceptance_reason: str
    risk_acceptance_expiration: Optional[date] = None


class RiskRegisterResponse(BaseModel):
    """Risk register entry response"""
    id: UUID
    tenant_id: UUID
    risk_id: str
    title: str
    category: RiskCategory
    current_risk_level: RiskLevel
    current_likelihood: int
    current_impact: int
    target_risk_level: Optional[RiskLevel]
    treatment_strategy: str
    treatment_status: RemediationStatus
    risk_owner_name: Optional[str]
    identified_date: date
    target_resolution_date: Optional[date]
    risk_trend: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


# ============================================================================
# Dashboard and Reporting Schemas
# ============================================================================

class ComplianceDashboard(BaseModel):
    """HIPAA compliance dashboard"""
    # Audit metrics
    total_audit_logs_today: int
    audit_logs_by_action: Dict[str, int]
    audit_logs_by_outcome: Dict[str, int]

    # Access metrics
    active_treatment_relationships: int
    pending_access_requests: int
    open_anomalies: int
    anomalies_by_severity: Dict[str, int]

    # Retention metrics
    records_pending_destruction: int
    active_legal_holds: int
    pending_roa_requests: int

    # Breach metrics
    active_breach_investigations: int
    breaches_by_status: Dict[str, int]

    # BAA metrics
    active_baas: int
    baas_expiring_soon: int
    pending_baa_signatures: int

    # Training metrics
    overdue_trainings: int
    training_completion_rate: float
    pending_policy_acknowledgments: int

    # Risk metrics
    open_risk_items: int
    risks_by_level: Dict[str, int]
    overdue_remediations: int


class AuditReport(BaseModel):
    """Audit log report"""
    report_period_start: datetime
    report_period_end: datetime
    total_events: int
    events_by_action: Dict[str, int]
    events_by_category: Dict[str, int]
    events_by_outcome: Dict[str, int]
    top_users: List[Dict[str, Any]]
    top_patients: List[Dict[str, Any]]
    anomalies_detected: int


class BAAComplianceReport(BaseModel):
    """BAA compliance report"""
    total_baas: int
    executed_baas: int
    pending_baas: int
    expiring_within_90_days: int
    missing_baa_vendors: List[str]
    subcontractor_chain: List[Dict[str, Any]]


class TrainingComplianceReport(BaseModel):
    """Training compliance report"""
    total_workforce: int
    fully_compliant: int
    partially_compliant: int
    non_compliant: int
    compliance_rate: float
    overdue_by_module: Dict[str, int]
    upcoming_due: List[Dict[str, Any]]


class RiskSummaryReport(BaseModel):
    """Risk assessment summary"""
    assessment_id: UUID
    assessment_name: str
    assessment_date: date
    total_risks: int
    risks_by_level: Dict[str, int]
    risks_by_category: Dict[str, int]
    remediation_progress: Dict[str, int]
    overall_risk_rating: str
