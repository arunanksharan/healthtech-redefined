"""
Clinical Decision Support (CDS) Pydantic Schemas

Request/response schemas for CDS API endpoints:
- Drug interaction checking
- Drug-allergy alerts
- Clinical guidelines
- Quality measures and care gaps
- CDS Hooks
- Alert management
- AI diagnostic support

EPIC-020: Clinical Decision Support
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from uuid import UUID
from enum import Enum


# ============================================================================
# ENUMS (Mirror models.py)
# ============================================================================

class InteractionSeverity(str, Enum):
    CONTRAINDICATED = "contraindicated"
    MAJOR = "major"
    MODERATE = "moderate"
    MINOR = "minor"
    UNKNOWN = "unknown"


class InteractionType(str, Enum):
    DRUG_DRUG = "drug_drug"
    DRUG_ALLERGY = "drug_allergy"
    DRUG_DISEASE = "drug_disease"
    DRUG_FOOD = "drug_food"
    DRUG_LAB = "drug_lab"
    DUPLICATE_THERAPY = "duplicate_therapy"


class AlertTier(str, Enum):
    HARD_STOP = "hard_stop"
    SOFT_STOP = "soft_stop"
    INFORMATIONAL = "informational"


class AlertStatus(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    OVERRIDDEN = "overridden"
    DISMISSED = "dismissed"
    EXPIRED = "expired"


class OverrideReason(str, Enum):
    BENEFIT_OUTWEIGHS_RISK = "benefit_outweighs_risk"
    PATIENT_TOLERATED_PREVIOUSLY = "patient_tolerated_previously"
    WILL_MONITOR = "will_monitor"
    DOSE_ADJUSTED = "dose_adjusted"
    NO_ALTERNATIVE = "no_alternative"
    PATIENT_REQUESTED = "patient_requested"
    EMERGENCY_SITUATION = "emergency_situation"
    CLINICAL_JUDGMENT = "clinical_judgment"
    OTHER = "other"


class GuidelineCategory(str, Enum):
    TREATMENT = "treatment"
    DIAGNOSTIC = "diagnostic"
    PREVENTIVE = "preventive"
    SCREENING = "screening"
    MEDICATION = "medication"
    PROCEDURE = "procedure"
    LIFESTYLE = "lifestyle"


class GuidelineSource(str, Enum):
    USPSTF = "uspstf"
    AHA = "aha"
    ADA = "ada"
    AAFP = "aafp"
    ACS = "acs"
    CDC = "cdc"
    UPTODATE = "uptodate"
    DYNAMED = "dynamed"
    CUSTOM = "custom"


class MeasureType(str, Enum):
    HEDIS = "hedis"
    CMS = "cms"
    MIPS = "mips"
    STATE = "state"
    PAYER = "payer"
    CUSTOM = "custom"


class MeasureStatus(str, Enum):
    MET = "met"
    NOT_MET = "not_met"
    EXCLUDED = "excluded"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"


class CareGapPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CareGapStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"
    SNOOZED = "snoozed"
    NOT_APPLICABLE = "not_applicable"


class CDSHookType(str, Enum):
    PATIENT_VIEW = "patient-view"
    ORDER_SELECT = "order-select"
    ORDER_SIGN = "order-sign"
    MEDICATION_PRESCRIBE = "medication-prescribe"
    ENCOUNTER_START = "encounter-start"
    ENCOUNTER_DISCHARGE = "encounter-discharge"
    APPOINTMENT_BOOK = "appointment-book"


class CDSCardType(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    SUCCESS = "success"


class DiagnosisSuggestionSource(str, Enum):
    AI_MODEL = "ai_model"
    CLINICAL_CRITERIA = "clinical_criteria"
    DIFFERENTIAL_ENGINE = "differential_engine"
    KNOWLEDGE_BASE = "knowledge_base"


# ============================================================================
# MEDICATION SCHEMAS
# ============================================================================

class MedicationInput(BaseModel):
    """Input medication for interaction checking."""
    rxnorm_code: str
    name: Optional[str] = None
    dose: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    ndc_code: Optional[str] = None


class MedicationListInput(BaseModel):
    """List of medications to check."""
    medications: List[MedicationInput]
    patient_id: UUID
    include_current_meds: bool = True
    include_allergies: bool = True
    include_conditions: bool = True


# ============================================================================
# DRUG INTERACTION SCHEMAS
# ============================================================================

class DrugInteractionBase(BaseModel):
    """Base drug interaction schema."""
    drug1_rxnorm: str
    drug1_name: Optional[str] = None
    drug2_rxnorm: str
    drug2_name: Optional[str] = None
    interaction_type: InteractionType
    severity: InteractionSeverity
    description: str
    clinical_effect: Optional[str] = None
    mechanism: Optional[str] = None
    recommendation: Optional[str] = None


class DrugInteractionRuleCreate(DrugInteractionBase):
    """Create drug interaction rule."""
    drug_class1: Optional[str] = None
    drug_class2: Optional[str] = None
    is_class_interaction: bool = False
    management: Optional[str] = None
    evidence_level: Optional[str] = None
    references: List[Dict[str, Any]] = Field(default_factory=list)


class DrugInteractionRuleUpdate(BaseModel):
    """Update drug interaction rule."""
    severity: Optional[InteractionSeverity] = None
    description: Optional[str] = None
    clinical_effect: Optional[str] = None
    recommendation: Optional[str] = None
    management: Optional[str] = None
    is_active: Optional[bool] = None


class DrugInteractionRuleResponse(DrugInteractionBase):
    """Drug interaction rule response."""
    id: UUID
    drug_class1: Optional[str] = None
    drug_class2: Optional[str] = None
    is_class_interaction: bool
    management: Optional[str] = None
    evidence_level: Optional[str] = None
    references: List[Dict[str, Any]] = Field(default_factory=list)
    source: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DrugInteractionResult(BaseModel):
    """Result of interaction check."""
    interaction_type: InteractionType
    severity: InteractionSeverity
    drug1: MedicationInput
    drug2: MedicationInput
    description: str
    clinical_effect: Optional[str] = None
    recommendation: Optional[str] = None
    management: Optional[str] = None
    evidence_level: Optional[str] = None
    references: List[Dict[str, Any]] = Field(default_factory=list)
    rule_id: Optional[UUID] = None


class DrugAllergyResult(BaseModel):
    """Result of drug-allergy check."""
    severity: InteractionSeverity
    medication: MedicationInput
    allergy_code: str
    allergy_name: str
    reaction_type: Optional[str] = None
    is_cross_reactive: bool = False
    cross_reactivity_info: Optional[str] = None
    recommendation: Optional[str] = None
    alternative_medications: List[MedicationInput] = Field(default_factory=list)


class DrugDiseaseResult(BaseModel):
    """Result of drug-disease contraindication check."""
    severity: InteractionSeverity
    medication: MedicationInput
    condition_code: str
    condition_name: str
    description: str
    recommendation: Optional[str] = None


class InteractionCheckResponse(BaseModel):
    """Complete interaction check response."""
    patient_id: UUID
    checked_at: datetime
    drug_drug_interactions: List[DrugInteractionResult] = Field(default_factory=list)
    drug_allergy_alerts: List[DrugAllergyResult] = Field(default_factory=list)
    drug_disease_alerts: List[DrugDiseaseResult] = Field(default_factory=list)
    duplicate_therapies: List[DrugInteractionResult] = Field(default_factory=list)
    total_alerts: int
    has_critical: bool
    has_major: bool


# ============================================================================
# CDS ALERT SCHEMAS
# ============================================================================

class CDSAlertCreate(BaseModel):
    """Create CDS alert."""
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    provider_id: Optional[UUID] = None
    order_id: Optional[UUID] = None
    alert_type: InteractionType
    severity: InteractionSeverity
    tier: AlertTier
    title: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    recommendation: Optional[str] = None
    drug1_rxnorm: Optional[str] = None
    drug1_name: Optional[str] = None
    drug2_rxnorm: Optional[str] = None
    drug2_name: Optional[str] = None
    allergy_code: Optional[str] = None
    condition_code: Optional[str] = None
    rule_id: Optional[UUID] = None
    expires_at: Optional[datetime] = None


class CDSAlertResponse(BaseModel):
    """CDS alert response."""
    id: UUID
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    provider_id: Optional[UUID] = None
    order_id: Optional[UUID] = None
    alert_type: InteractionType
    severity: InteractionSeverity
    tier: AlertTier
    status: AlertStatus
    title: str
    message: str
    details: Dict[str, Any]
    recommendation: Optional[str] = None
    drug1_rxnorm: Optional[str] = None
    drug1_name: Optional[str] = None
    drug2_rxnorm: Optional[str] = None
    drug2_name: Optional[str] = None
    triggered_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class AlertAcknowledge(BaseModel):
    """Acknowledge an alert."""
    acknowledged_by: UUID
    was_helpful: Optional[bool] = None


class AlertOverrideCreate(BaseModel):
    """Override an alert."""
    provider_id: UUID
    reason: OverrideReason
    reason_other: Optional[str] = None
    clinical_justification: str
    will_monitor: bool = False
    monitoring_plan: Optional[str] = None
    supervising_provider_id: Optional[UUID] = None
    was_emergency: bool = False
    patient_consented: Optional[bool] = None


class AlertOverrideResponse(BaseModel):
    """Alert override response."""
    id: UUID
    alert_id: UUID
    provider_id: UUID
    reason: OverrideReason
    reason_other: Optional[str] = None
    clinical_justification: str
    will_monitor: bool
    monitoring_plan: Optional[str] = None
    was_emergency: bool
    override_at: datetime

    class Config:
        from_attributes = True


class AlertDismiss(BaseModel):
    """Dismiss an alert."""
    dismissed_by: UUID
    reason: Optional[str] = None


# ============================================================================
# ALERT CONFIGURATION SCHEMAS
# ============================================================================

class AlertConfigurationCreate(BaseModel):
    """Create alert configuration."""
    alert_type: Optional[InteractionType] = None
    severity: Optional[InteractionSeverity] = None
    drug_class: Optional[str] = None
    tier: AlertTier = AlertTier.SOFT_STOP
    is_enabled: bool = True
    is_suppressible: bool = True
    requires_override_reason: bool = True
    min_severity: InteractionSeverity = InteractionSeverity.MINOR
    exclude_conditions: List[str] = Field(default_factory=list)
    provider_roles: List[str] = Field(default_factory=list)
    care_settings: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class AlertConfigurationUpdate(BaseModel):
    """Update alert configuration."""
    tier: Optional[AlertTier] = None
    is_enabled: Optional[bool] = None
    is_suppressible: Optional[bool] = None
    requires_override_reason: Optional[bool] = None
    min_severity: Optional[InteractionSeverity] = None
    notes: Optional[str] = None


class AlertConfigurationResponse(BaseModel):
    """Alert configuration response."""
    id: UUID
    alert_type: Optional[InteractionType] = None
    severity: Optional[InteractionSeverity] = None
    drug_class: Optional[str] = None
    tier: AlertTier
    is_enabled: bool
    is_suppressible: bool
    requires_override_reason: bool
    min_severity: InteractionSeverity
    created_at: datetime

    class Config:
        from_attributes = True


class AlertAnalyticsResponse(BaseModel):
    """Alert analytics response."""
    period_date: date
    period_type: str
    alert_type: Optional[InteractionType] = None
    severity: Optional[InteractionSeverity] = None
    total_alerts: int
    acknowledged_count: int
    overridden_count: int
    dismissed_count: int
    override_rate: Optional[float] = None
    avg_response_time_ms: Optional[int] = None
    override_reasons: Dict[str, int] = Field(default_factory=dict)

    class Config:
        from_attributes = True


# ============================================================================
# CLINICAL GUIDELINE SCHEMAS
# ============================================================================

class GuidelineCreate(BaseModel):
    """Create clinical guideline."""
    external_id: Optional[str] = None
    title: str
    short_title: Optional[str] = None
    category: GuidelineCategory
    source: GuidelineSource
    publisher: Optional[str] = None
    conditions: List[str] = Field(default_factory=list)
    condition_names: List[str] = Field(default_factory=list)
    summary: Optional[str] = None
    key_recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    full_content: Optional[str] = None
    content_url: Optional[str] = None
    evidence_grade: Optional[str] = None
    recommendation_strength: Optional[str] = None
    references: List[Dict[str, Any]] = Field(default_factory=list)
    patient_population: Optional[str] = None
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    gender: Optional[str] = None
    version: Optional[str] = None
    published_date: Optional[date] = None


class GuidelineUpdate(BaseModel):
    """Update clinical guideline."""
    title: Optional[str] = None
    summary: Optional[str] = None
    key_recommendations: Optional[List[Dict[str, Any]]] = None
    full_content: Optional[str] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None


class GuidelineResponse(BaseModel):
    """Clinical guideline response."""
    id: UUID
    external_id: Optional[str] = None
    title: str
    short_title: Optional[str] = None
    category: GuidelineCategory
    source: GuidelineSource
    publisher: Optional[str] = None
    conditions: List[str]
    condition_names: List[str]
    summary: Optional[str] = None
    key_recommendations: List[Dict[str, Any]]
    evidence_grade: Optional[str] = None
    recommendation_strength: Optional[str] = None
    patient_population: Optional[str] = None
    version: Optional[str] = None
    published_date: Optional[date] = None
    is_active: bool
    view_count: int
    usefulness_rating: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class GuidelineSearchRequest(BaseModel):
    """Search for guidelines."""
    query: Optional[str] = None
    conditions: Optional[List[str]] = None
    categories: Optional[List[GuidelineCategory]] = None
    sources: Optional[List[GuidelineSource]] = None
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    limit: int = 10


class GuidelineRecommendation(BaseModel):
    """Guideline recommendation for context."""
    guideline: GuidelineResponse
    relevance_score: float
    matched_conditions: List[str]
    reason: str


class GuidelineAccessLog(BaseModel):
    """Log guideline access."""
    guideline_id: UUID
    provider_id: UUID
    patient_id: Optional[UUID] = None
    encounter_id: Optional[UUID] = None
    access_context: Optional[str] = None
    was_helpful: Optional[bool] = None
    feedback: Optional[str] = None


# ============================================================================
# QUALITY MEASURE SCHEMAS
# ============================================================================

class QualityMeasureCreate(BaseModel):
    """Create quality measure."""
    measure_id: str
    title: str
    short_name: Optional[str] = None
    version: Optional[str] = None
    measure_type: MeasureType
    category: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None
    rationale: Optional[str] = None
    clinical_recommendation: Optional[str] = None
    initial_population_cql: Optional[str] = None
    denominator_cql: Optional[str] = None
    numerator_cql: Optional[str] = None
    exclusion_cql: Optional[str] = None
    exception_cql: Optional[str] = None
    target_rate: Optional[float] = None
    reporting_period_start: Optional[date] = None
    reporting_period_end: Optional[date] = None
    specification_url: Optional[str] = None


class QualityMeasureUpdate(BaseModel):
    """Update quality measure."""
    title: Optional[str] = None
    description: Optional[str] = None
    target_rate: Optional[float] = None
    is_active: Optional[bool] = None
    is_required: Optional[bool] = None


class QualityMeasureResponse(BaseModel):
    """Quality measure response."""
    id: UUID
    measure_id: str
    title: str
    short_name: Optional[str] = None
    version: Optional[str] = None
    measure_type: MeasureType
    category: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None
    rationale: Optional[str] = None
    target_rate: Optional[float] = None
    benchmark_rate: Optional[float] = None
    reporting_period_start: Optional[date] = None
    reporting_period_end: Optional[date] = None
    is_active: bool
    is_required: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PatientMeasureResponse(BaseModel):
    """Patient measure evaluation response."""
    id: UUID
    patient_id: UUID
    measure: QualityMeasureResponse
    period_start: date
    period_end: date
    in_initial_population: bool
    in_denominator: bool
    in_numerator: bool
    is_excluded: bool
    has_exception: bool
    status: MeasureStatus
    evaluation_date: Optional[datetime] = None
    gap_actions: List[Dict[str, Any]]

    class Config:
        from_attributes = True


class MeasureEvaluationRequest(BaseModel):
    """Request to evaluate measures for a patient."""
    patient_id: UUID
    measure_ids: Optional[List[UUID]] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None


class MeasureEvaluationResponse(BaseModel):
    """Measure evaluation response."""
    patient_id: UUID
    evaluated_at: datetime
    measures: List[PatientMeasureResponse]
    total_measures: int
    met_count: int
    not_met_count: int
    excluded_count: int


# ============================================================================
# CARE GAP SCHEMAS
# ============================================================================

class CareGapCreate(BaseModel):
    """Create care gap."""
    patient_id: UUID
    measure_id: Optional[UUID] = None
    gap_type: str
    title: str
    description: Optional[str] = None
    priority: CareGapPriority = CareGapPriority.MEDIUM
    recommended_action: Optional[str] = None
    action_type: Optional[str] = None
    order_code: Optional[str] = None
    due_date: Optional[date] = None
    attributed_provider_id: Optional[UUID] = None


class CareGapUpdate(BaseModel):
    """Update care gap."""
    status: Optional[CareGapStatus] = None
    priority: Optional[CareGapPriority] = None
    snoozed_until: Optional[date] = None
    snooze_reason: Optional[str] = None
    closure_evidence: Optional[Dict[str, Any]] = None


class CareGapResponse(BaseModel):
    """Care gap response."""
    id: UUID
    patient_id: UUID
    measure_id: Optional[UUID] = None
    gap_type: str
    title: str
    description: Optional[str] = None
    priority: CareGapPriority
    status: CareGapStatus
    recommended_action: Optional[str] = None
    action_type: Optional[str] = None
    order_code: Optional[str] = None
    due_date: Optional[date] = None
    last_performed: Optional[date] = None
    attributed_provider_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CareGapClose(BaseModel):
    """Close a care gap."""
    closed_by_provider_id: UUID
    closure_evidence: Dict[str, Any]


class PatientCareGapSummary(BaseModel):
    """Summary of patient's care gaps."""
    patient_id: UUID
    total_gaps: int
    critical_gaps: int
    high_priority_gaps: int
    overdue_gaps: int
    gaps: List[CareGapResponse]


# ============================================================================
# CDS HOOKS SCHEMAS
# ============================================================================

class CDSServiceCreate(BaseModel):
    """Register CDS service."""
    service_id: str
    name: str
    description: Optional[str] = None
    hook: CDSHookType
    endpoint_url: str
    is_internal: bool = True
    auth_type: Optional[str] = None
    prefetch_templates: Dict[str, str] = Field(default_factory=dict)
    timeout_ms: int = 5000
    priority: int = 100


class CDSServiceUpdate(BaseModel):
    """Update CDS service."""
    name: Optional[str] = None
    description: Optional[str] = None
    endpoint_url: Optional[str] = None
    is_enabled: Optional[bool] = None
    timeout_ms: Optional[int] = None
    priority: Optional[int] = None


class CDSServiceResponse(BaseModel):
    """CDS service response."""
    id: UUID
    service_id: str
    name: str
    description: Optional[str] = None
    hook: CDSHookType
    endpoint_url: str
    is_internal: bool
    is_enabled: bool
    timeout_ms: int
    priority: int
    is_healthy: bool
    total_invocations: int
    avg_response_time_ms: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CDSHookRequest(BaseModel):
    """CDS Hooks request (per spec)."""
    hook: str
    hookInstance: str
    context: Dict[str, Any]
    prefetch: Optional[Dict[str, Any]] = None
    fhirServer: Optional[str] = None
    fhirAuthorization: Optional[Dict[str, str]] = None


class CDSLink(BaseModel):
    """CDS card link."""
    label: str
    url: str
    type: str = "absolute"  # absolute, smart


class CDSSuggestion(BaseModel):
    """CDS card suggestion."""
    label: str
    uuid: Optional[str] = None
    isRecommended: bool = False
    actions: List[Dict[str, Any]] = Field(default_factory=list)


class CDSCardResponse(BaseModel):
    """CDS card (per spec)."""
    uuid: Optional[str] = None
    summary: str
    detail: Optional[str] = None
    indicator: str = "info"
    source: Dict[str, str]
    suggestions: List[CDSSuggestion] = Field(default_factory=list)
    links: List[CDSLink] = Field(default_factory=list)
    selectionBehavior: Optional[str] = None


class CDSHookResponse(BaseModel):
    """CDS Hooks response (per spec)."""
    cards: List[CDSCardResponse] = Field(default_factory=list)


class CDSCardInteraction(BaseModel):
    """Log card interaction."""
    card_id: UUID
    was_accepted: Optional[bool] = None
    suggestion_selected: Optional[str] = None
    link_clicked: Optional[str] = None


# ============================================================================
# DIAGNOSTIC SUPPORT SCHEMAS
# ============================================================================

class SymptomInput(BaseModel):
    """Input symptom for diagnostic support."""
    code: Optional[str] = None  # SNOMED
    name: str
    onset: Optional[str] = None
    duration: Optional[str] = None
    severity: Optional[str] = None
    location: Optional[str] = None
    characteristics: Optional[List[str]] = None


class FindingInput(BaseModel):
    """Input finding (exam, vital)."""
    type: str  # vital_sign, physical_exam, lab_result
    code: Optional[str] = None
    name: str
    value: Optional[str] = None
    unit: Optional[str] = None
    interpretation: Optional[str] = None


class DiagnosticSessionCreate(BaseModel):
    """Create diagnostic session."""
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    chief_complaint: Optional[str] = None
    symptoms: List[SymptomInput] = Field(default_factory=list)
    findings: List[FindingInput] = Field(default_factory=list)
    history: Dict[str, Any] = Field(default_factory=dict)
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    relevant_conditions: List[str] = Field(default_factory=list)
    relevant_medications: List[str] = Field(default_factory=list)


class DiagnosticSessionUpdate(BaseModel):
    """Update diagnostic session."""
    chief_complaint: Optional[str] = None
    symptoms: Optional[List[SymptomInput]] = None
    findings: Optional[List[FindingInput]] = None
    status: Optional[str] = None


class DiagnosisSuggestionResponse(BaseModel):
    """Diagnosis suggestion response."""
    id: UUID
    diagnosis_code: str
    diagnosis_code_system: str
    diagnosis_name: str
    probability: Optional[float] = None
    confidence: Optional[float] = None
    rank: Optional[int] = None
    source: DiagnosisSuggestionSource
    is_cant_miss: bool
    urgency: Optional[str] = None
    reasoning: Optional[str] = None
    supporting_evidence: List[Dict[str, Any]]
    against_evidence: List[Dict[str, Any]]
    recommended_tests: List[Dict[str, Any]]
    recommended_imaging: List[Dict[str, Any]]
    recommended_referrals: List[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class DiagnosticSessionResponse(BaseModel):
    """Diagnostic session response."""
    id: UUID
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    provider_id: UUID
    chief_complaint: Optional[str] = None
    symptoms: List[Dict[str, Any]]
    findings: List[Dict[str, Any]]
    status: str
    suggestions: List[DiagnosisSuggestionResponse]
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DiagnosisFeedback(BaseModel):
    """Feedback on diagnosis suggestion."""
    suggestion_id: UUID
    was_accepted: Optional[bool] = None
    feedback_rating: Optional[int] = Field(None, ge=1, le=5)
    feedback_comment: Optional[str] = None
    final_diagnosis: Optional[str] = None


class DifferentialDiagnosisRequest(BaseModel):
    """Request for differential diagnosis."""
    patient_id: UUID
    chief_complaint: str
    symptoms: List[SymptomInput]
    findings: List[FindingInput] = Field(default_factory=list)
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    max_suggestions: int = 10
    include_cant_miss: bool = True


class DifferentialDiagnosisResponse(BaseModel):
    """Differential diagnosis response."""
    session_id: UUID
    patient_id: UUID
    differential: List[DiagnosisSuggestionResponse]
    cant_miss_diagnoses: List[DiagnosisSuggestionResponse]
    recommended_workup: Dict[str, List[Dict[str, Any]]]
    generated_at: datetime


# ============================================================================
# DASHBOARD & REPORTING SCHEMAS
# ============================================================================

class CDSDashboard(BaseModel):
    """CDS dashboard for providers."""
    provider_id: UUID
    period_start: date
    period_end: date
    total_alerts: int
    alerts_by_type: Dict[str, int]
    alerts_by_severity: Dict[str, int]
    override_rate: float
    top_override_reasons: List[Dict[str, Any]]
    avg_response_time_ms: int
    patients_with_care_gaps: int
    critical_care_gaps: int


class OrganizationCDSMetrics(BaseModel):
    """Organization-level CDS metrics."""
    tenant_id: UUID
    period_start: date
    period_end: date
    total_alerts: int
    unique_patients_alerted: int
    override_rate: float
    potential_adverse_events_prevented: int
    quality_measure_performance: Dict[str, float]
    care_gap_closure_rate: float
    top_interacting_drug_pairs: List[Dict[str, Any]]


class DrugDatabaseStats(BaseModel):
    """Drug database statistics."""
    total_drugs: int
    total_interaction_rules: int
    total_allergy_mappings: int
    total_contraindications: int
    last_updated: datetime
    sources: List[str]
