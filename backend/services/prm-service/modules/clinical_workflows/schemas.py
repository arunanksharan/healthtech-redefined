"""
Clinical Workflows Pydantic Schemas

Request and response models for clinical workflow APIs.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field, validator


# ==================== Enums ====================

class PrescriptionStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    PENDING_SIGNATURE = "pending_signature"
    SIGNED = "signed"
    SENT = "sent"
    RECEIVED = "received"
    DISPENSED = "dispensed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    ON_HOLD = "on_hold"


class DrugSchedule(str, Enum):
    NON_CONTROLLED = "non_controlled"
    SCHEDULE_I = "I"
    SCHEDULE_II = "II"
    SCHEDULE_III = "III"
    SCHEDULE_IV = "IV"
    SCHEDULE_V = "V"


class InteractionSeverity(str, Enum):
    SEVERE = "severe"
    MAJOR = "major"
    MODERATE = "moderate"
    MINOR = "minor"
    NONE = "none"


class LabOrderStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    ORDERED = "ordered"
    SPECIMEN_COLLECTED = "specimen_collected"
    RECEIVED_BY_LAB = "received_by_lab"
    IN_PROGRESS = "in_progress"
    RESULTED = "resulted"
    FINAL = "final"
    CANCELLED = "cancelled"


class OrderPriority(str, Enum):
    ROUTINE = "routine"
    URGENT = "urgent"
    STAT = "stat"
    ASAP = "asap"
    TIMED = "timed"


class InterpretationFlag(str, Enum):
    NORMAL = "N"
    LOW = "L"
    HIGH = "H"
    CRITICAL_LOW = "LL"
    CRITICAL_HIGH = "HH"
    ABNORMAL = "A"


class ImagingModality(str, Enum):
    XRAY = "XR"
    CT = "CT"
    MRI = "MR"
    ULTRASOUND = "US"
    MAMMOGRAPHY = "MG"
    NUCLEAR_MEDICINE = "NM"
    PET = "PT"
    FLUOROSCOPY = "FL"


class ImagingOrderStatus(str, Enum):
    DRAFT = "draft"
    ORDERED = "ordered"
    SCHEDULED = "scheduled"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REPORTED = "reported"
    FINAL = "final"
    CANCELLED = "cancelled"


class ReferralStatus(str, Enum):
    DRAFT = "draft"
    PENDING_AUTH = "pending_authorization"
    AUTHORIZED = "authorized"
    SENT = "sent"
    RECEIVED = "received"
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DENIED = "denied"


class ReferralPriority(str, Enum):
    ROUTINE = "routine"
    URGENT = "urgent"
    EMERGENT = "emergent"
    STAT = "stat"


class ReferralType(str, Enum):
    CONSULTATION = "consultation"
    PROCEDURE = "procedure"
    DIAGNOSTIC = "diagnostic"
    THERAPY = "therapy"
    SECOND_OPINION = "second_opinion"
    TRANSFER = "transfer"


class NoteStatus(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    PENDING_SIGNATURE = "pending_signature"
    SIGNED = "signed"
    COSIGNED = "cosigned"
    AMENDED = "amended"


class NoteType(str, Enum):
    PROGRESS_NOTE = "progress_note"
    HISTORY_PHYSICAL = "history_physical"
    CONSULTATION = "consultation"
    PROCEDURE_NOTE = "procedure_note"
    OPERATIVE_NOTE = "operative_note"
    DISCHARGE_SUMMARY = "discharge_summary"
    NURSING_NOTE = "nursing_note"
    TELEPHONE_ENCOUNTER = "telephone_encounter"
    TELEMEDICINE = "telemedicine"


class CarePlanStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    REVOKED = "revoked"
    COMPLETED = "completed"


class CarePlanCategory(str, Enum):
    CHRONIC_DISEASE = "chronic_disease"
    PREVENTIVE = "preventive"
    POST_SURGICAL = "post_surgical"
    REHABILITATION = "rehabilitation"
    MENTAL_HEALTH = "mental_health"


class GoalStatus(str, Enum):
    PROPOSED = "proposed"
    PLANNED = "planned"
    ACCEPTED = "accepted"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class GoalPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    CONTRAINDICATION = "contraindication"


class AlertCategory(str, Enum):
    DRUG_INTERACTION = "drug_interaction"
    DRUG_ALLERGY = "drug_allergy"
    DUPLICATE_THERAPY = "duplicate_therapy"
    DOSE_CHECK = "dose_check"
    LAB_ALERT = "lab_alert"
    PREVENTIVE_CARE = "preventive_care"
    QUALITY_MEASURE = "quality_measure"


class VitalType(str, Enum):
    BLOOD_PRESSURE = "blood_pressure"
    HEART_RATE = "heart_rate"
    RESPIRATORY_RATE = "respiratory_rate"
    TEMPERATURE = "temperature"
    OXYGEN_SATURATION = "oxygen_saturation"
    WEIGHT = "weight"
    HEIGHT = "height"
    BMI = "bmi"
    PAIN_LEVEL = "pain_level"


# ==================== Prescription Schemas ====================

class SigCreate(BaseModel):
    """Prescription directions."""
    dose: float
    dose_unit: str
    route: str
    frequency: str
    frequency_description: Optional[str] = None
    duration: Optional[str] = None
    duration_days: Optional[int] = None
    as_needed: bool = False
    as_needed_reason: Optional[str] = None
    special_instructions: Optional[str] = None


class PrescriptionCreate(BaseModel):
    """Create prescription request."""
    tenant_id: UUID
    patient_id: UUID
    prescriber_id: UUID
    encounter_id: Optional[UUID] = None
    rxnorm_code: str
    drug_name: str
    strength: Optional[str] = None
    form: Optional[str] = None
    sig: SigCreate
    quantity: float
    quantity_unit: str
    days_supply: int
    refills: int = 0
    pharmacy_id: Optional[str] = None
    dispense_as_written: bool = False
    notes: Optional[str] = None


class PrescriptionUpdate(BaseModel):
    """Update prescription request."""
    sig: Optional[SigCreate] = None
    quantity: Optional[float] = None
    refills: Optional[int] = None
    pharmacy_id: Optional[str] = None
    notes: Optional[str] = None


class PrescriptionResponse(BaseModel):
    """Prescription response."""
    id: UUID
    tenant_id: UUID
    patient_id: UUID
    prescriber_id: UUID
    rxnorm_code: str
    drug_name: str
    strength: Optional[str]
    form: Optional[str]
    sig_text: Optional[str]
    quantity: float
    quantity_unit: Optional[str]
    days_supply: Optional[int]
    refills: int
    refills_remaining: int
    status: PrescriptionStatus
    is_controlled: bool
    dea_schedule: Optional[str]
    interactions_checked: bool
    allergies_checked: bool
    created_at: datetime
    signed_at: Optional[datetime]
    sent_at: Optional[datetime]
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class DrugSearchRequest(BaseModel):
    """Drug search request."""
    query: str
    limit: int = 20
    include_generic: bool = True
    include_brand: bool = True


class DrugInfo(BaseModel):
    """Drug information response."""
    rxnorm_code: str
    name: str
    generic_name: Optional[str]
    brand_names: List[str] = []
    strength: Optional[str]
    form: Optional[str]
    route: Optional[str]
    schedule: DrugSchedule = DrugSchedule.NON_CONTROLLED
    drug_class: Optional[str]
    black_box_warning: Optional[str]


class InteractionCheckRequest(BaseModel):
    """Drug interaction check request."""
    rxnorm_code: str
    current_medications: List[str]
    patient_id: UUID


class InteractionCheckResponse(BaseModel):
    """Drug interaction check response."""
    has_interactions: bool
    interactions: List[Dict[str, Any]]
    has_allergies: bool
    allergy_matches: List[Dict[str, Any]]
    has_duplicates: bool
    duplicates: List[Dict[str, Any]]
    requires_override: bool


class SignPrescriptionRequest(BaseModel):
    """Sign prescription request."""
    signer_id: UUID
    signature_token: Optional[str] = None  # Required for EPCS


class SendToPharmacyRequest(BaseModel):
    """Send to pharmacy request."""
    pharmacy_id: str
    pharmacy_ncpdp: Optional[str] = None


# ==================== Lab Order Schemas ====================

class LabTestCreate(BaseModel):
    """Lab test in order."""
    loinc_code: str
    test_name: str
    cpt_code: Optional[str] = None


class LabOrderCreate(BaseModel):
    """Create lab order request."""
    tenant_id: UUID
    patient_id: UUID
    ordering_provider_id: UUID
    encounter_id: Optional[UUID] = None
    tests: List[LabTestCreate]
    priority: OrderPriority = OrderPriority.ROUTINE
    diagnosis_codes: List[str] = []
    clinical_indication: Optional[str] = None
    fasting_required: bool = False
    scheduled_date: Optional[datetime] = None
    notes: Optional[str] = None


class LabOrderResponse(BaseModel):
    """Lab order response."""
    id: UUID
    tenant_id: UUID
    patient_id: UUID
    ordering_provider_id: UUID
    tests: List[Dict[str, Any]]
    priority: str
    status: LabOrderStatus
    has_critical_results: bool
    created_at: datetime
    ordered_at: Optional[datetime]
    resulted_at: Optional[datetime]

    class Config:
        from_attributes = True


class LabResultResponse(BaseModel):
    """Lab result response."""
    id: UUID
    order_id: UUID
    loinc_code: str
    test_name: str
    value: Optional[str]
    value_numeric: Optional[float]
    units: Optional[str]
    reference_low: Optional[float]
    reference_high: Optional[float]
    interpretation: Optional[str]
    is_critical: bool
    is_abnormal: bool
    status: str
    resulted_at: datetime

    class Config:
        from_attributes = True


class RecordSpecimenRequest(BaseModel):
    """Record specimen collection request."""
    collected_by: UUID
    collection_time: Optional[datetime] = None
    container_id: Optional[str] = None
    notes: Optional[str] = None


class LabResultTrendResponse(BaseModel):
    """Lab result trend response."""
    loinc_code: str
    test_name: str
    unit: str
    values: List[Dict[str, Any]]  # [{"date": ..., "value": ...}, ...]


# ==================== Imaging Schemas ====================

class ImagingOrderCreate(BaseModel):
    """Create imaging order request."""
    tenant_id: UUID
    patient_id: UUID
    ordering_provider_id: UUID
    encounter_id: Optional[UUID] = None
    procedure_code: str
    procedure_name: str
    modality: ImagingModality
    body_part: Optional[str] = None
    laterality: Optional[str] = None
    priority: OrderPriority = OrderPriority.ROUTINE
    clinical_indication: str
    diagnosis_codes: List[str] = []
    contrast_required: bool = False
    notes: Optional[str] = None


class ImagingOrderResponse(BaseModel):
    """Imaging order response."""
    id: UUID
    tenant_id: UUID
    patient_id: UUID
    procedure_code: str
    procedure_name: str
    modality: str
    priority: str
    status: ImagingOrderStatus
    scheduled_datetime: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ImagingStudyResponse(BaseModel):
    """Imaging study response."""
    id: UUID
    order_id: Optional[UUID]
    accession_number: Optional[str]
    study_instance_uid: str
    modality: str
    study_description: Optional[str]
    num_series: int
    num_images: int
    radiation_dose_msv: Optional[float]
    study_datetime: datetime
    pacs_url: Optional[str]

    class Config:
        from_attributes = True


class RadiologyReportResponse(BaseModel):
    """Radiology report response."""
    id: UUID
    study_id: UUID
    impression: Optional[str]
    findings: Optional[str]
    comparison: Optional[str]
    technique: Optional[str]
    radiologist_name: Optional[str]
    status: str
    finalized_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== Referral Schemas ====================

class ReferralCreate(BaseModel):
    """Create referral request."""
    tenant_id: UUID
    patient_id: UUID
    referring_provider_id: UUID
    encounter_id: Optional[UUID] = None
    target_specialty: str
    receiving_provider_id: Optional[UUID] = None
    referral_type: ReferralType = ReferralType.CONSULTATION
    priority: ReferralPriority = ReferralPriority.ROUTINE
    reason: str
    clinical_question: Optional[str] = None
    diagnosis_codes: List[str] = []
    preferred_date_start: Optional[datetime] = None
    preferred_date_end: Optional[datetime] = None


class ReferralResponse(BaseModel):
    """Referral response."""
    id: UUID
    tenant_id: UUID
    patient_id: UUID
    referring_provider_id: UUID
    receiving_provider_id: Optional[UUID]
    target_specialty: Optional[str]
    referral_type: str
    priority: str
    reason: str
    status: ReferralStatus
    requires_authorization: bool
    authorization_status: Optional[str]
    scheduled_datetime: Optional[datetime]
    created_at: datetime
    sent_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class ReferralMessageCreate(BaseModel):
    """Create referral message."""
    sender_id: UUID
    sender_type: str
    content: str


class ReferralDocumentResponse(BaseModel):
    """Referral document response."""
    id: UUID
    document_type: str
    file_name: str
    mime_type: Optional[str]
    storage_url: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


class ProviderSearchRequest(BaseModel):
    """Provider search request."""
    specialty_code: Optional[str] = None
    in_network_only: bool = True
    accepting_new_patients: bool = True
    telehealth: Optional[bool] = None
    language: Optional[str] = None
    max_wait_days: Optional[int] = None


class ProviderResponse(BaseModel):
    """Provider response."""
    provider_id: str
    npi: str
    name: str
    organization: Optional[str]
    specialties: List[Dict[str, Any]]
    accepting_new_patients: bool
    in_network: bool
    average_wait_days: Optional[int]
    telehealth_available: bool


# ==================== Clinical Documentation Schemas ====================

class SOAPContentCreate(BaseModel):
    """SOAP note content."""
    chief_complaint: Optional[str] = None
    subjective: Optional[str] = None
    hpi: Optional[str] = None
    ros: Optional[Dict[str, str]] = None
    objective: Optional[str] = None
    vitals: Optional[Dict[str, Any]] = None
    physical_exam: Optional[Dict[str, str]] = None
    assessment: Optional[str] = None
    diagnoses: Optional[List[Dict[str, str]]] = None
    plan: Optional[str] = None
    plan_items: Optional[List[Dict[str, Any]]] = None


class ClinicalNoteCreate(BaseModel):
    """Create clinical note request."""
    tenant_id: UUID
    patient_id: UUID
    encounter_id: UUID
    author_id: UUID
    note_type: NoteType = NoteType.PROGRESS_NOTE
    template_id: Optional[UUID] = None
    title: Optional[str] = None
    content: Optional[str] = None
    structured_content: Optional[SOAPContentCreate] = None


class ClinicalNoteUpdate(BaseModel):
    """Update clinical note request."""
    title: Optional[str] = None
    content: Optional[str] = None
    structured_content: Optional[SOAPContentCreate] = None
    diagnosis_codes: Optional[List[Dict[str, str]]] = None
    procedure_codes: Optional[List[Dict[str, str]]] = None


class ClinicalNoteResponse(BaseModel):
    """Clinical note response."""
    id: UUID
    tenant_id: UUID
    patient_id: UUID
    encounter_id: Optional[UUID]
    author_id: UUID
    note_type: str
    title: Optional[str]
    content: Optional[str]
    structured_content: Optional[Dict[str, Any]]
    diagnosis_codes: List[Dict[str, Any]]
    procedure_codes: List[Dict[str, Any]]
    status: NoteStatus
    signed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SignNoteRequest(BaseModel):
    """Sign note request."""
    signer_id: UUID


class AddAddendumRequest(BaseModel):
    """Add addendum request."""
    author_id: UUID
    content: str


class NoteTemplateCreate(BaseModel):
    """Create note template request."""
    tenant_id: UUID
    name: str
    note_type: NoteType
    specialty: Optional[str] = None
    sections: List[Dict[str, Any]] = []
    default_content: Dict[str, str] = {}


class NoteTemplateResponse(BaseModel):
    """Note template response."""
    id: UUID
    tenant_id: UUID
    name: str
    note_type: str
    specialty: Optional[str]
    sections: List[Dict[str, Any]]
    default_content: Dict[str, Any]
    is_default: bool
    is_active: bool

    class Config:
        from_attributes = True


class SmartPhraseCreate(BaseModel):
    """Create smart phrase request."""
    tenant_id: UUID
    owner_id: Optional[UUID] = None
    abbreviation: str
    name: str
    content: str
    category: Optional[str] = None
    variables: List[str] = []


class SmartPhraseResponse(BaseModel):
    """Smart phrase response."""
    id: UUID
    abbreviation: str
    name: str
    content: str
    category: Optional[str]
    variables: List[str]
    usage_count: int

    class Config:
        from_attributes = True


class CodeSuggestionResponse(BaseModel):
    """Auto-coding suggestion response."""
    code: str
    code_system: str
    description: str
    confidence: float
    source_text: str


# ==================== Care Plan Schemas ====================

class CareGoalTargetCreate(BaseModel):
    """Care goal target."""
    measure: str
    detail_value: Any
    unit: Optional[str] = None
    due_date: Optional[datetime] = None


class CareGoalCreate(BaseModel):
    """Create care goal request."""
    category: Optional[str] = None
    description: str
    priority: GoalPriority = GoalPriority.MEDIUM
    targets: List[CareGoalTargetCreate] = []
    start_date: Optional[datetime] = None
    target_date: Optional[datetime] = None
    owner_id: Optional[UUID] = None


class CareInterventionCreate(BaseModel):
    """Create care intervention request."""
    category: Optional[str] = None
    description: str
    reason: Optional[str] = None
    goal_ids: List[UUID] = []
    scheduled_timing: Optional[str] = None
    scheduled_datetime: Optional[datetime] = None
    assigned_to_id: Optional[UUID] = None
    instructions: Optional[str] = None


class CarePlanCreate(BaseModel):
    """Create care plan request."""
    tenant_id: UUID
    patient_id: UUID
    title: str
    description: Optional[str] = None
    category: CarePlanCategory = CarePlanCategory.CHRONIC_DISEASE
    author_id: Optional[UUID] = None
    condition_ids: List[UUID] = []
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    goals: List[CareGoalCreate] = []
    interventions: List[CareInterventionCreate] = []


class CarePlanResponse(BaseModel):
    """Care plan response."""
    id: UUID
    tenant_id: UUID
    patient_id: UUID
    title: str
    description: Optional[str]
    category: str
    status: CarePlanStatus
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CareGoalResponse(BaseModel):
    """Care goal response."""
    id: UUID
    care_plan_id: UUID
    category: Optional[str]
    description: str
    priority: str
    targets: List[Dict[str, Any]]
    status: str
    achievement_status: str
    start_date: Optional[datetime]
    target_date: Optional[datetime]

    class Config:
        from_attributes = True


class GoalProgressCreate(BaseModel):
    """Record goal progress request."""
    measure: str
    value: Any
    unit: Optional[str] = None
    recorded_by: UUID
    notes: Optional[str] = None


class CareInterventionResponse(BaseModel):
    """Care intervention response."""
    id: UUID
    care_plan_id: UUID
    category: Optional[str]
    description: str
    status: str
    scheduled_timing: Optional[str]
    scheduled_datetime: Optional[datetime]
    assigned_to_id: Optional[UUID]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class CareTeamMemberCreate(BaseModel):
    """Add care team member request."""
    provider_id: Optional[UUID] = None
    role: str
    name: str
    specialty: Optional[str] = None


# ==================== Clinical Decision Support Schemas ====================

class EvaluateAlertsRequest(BaseModel):
    """Evaluate CDS alerts request."""
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    context: Optional[Dict[str, Any]] = None


class ClinicalAlertResponse(BaseModel):
    """Clinical alert response."""
    id: UUID
    tenant_id: UUID
    patient_id: UUID
    category: str
    severity: str
    title: str
    message: str
    suggested_actions: List[Dict[str, Any]]
    status: str
    created_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class AcknowledgeAlertRequest(BaseModel):
    """Acknowledge alert request."""
    user_id: UUID


class OverrideAlertRequest(BaseModel):
    """Override alert request."""
    user_id: UUID
    reason: str


class CDSRuleCreate(BaseModel):
    """Create CDS rule request."""
    tenant_id: UUID
    name: str
    description: Optional[str] = None
    category: AlertCategory
    conditions: List[Dict[str, Any]]
    alert_severity: AlertSeverity = AlertSeverity.WARNING
    alert_title_template: Optional[str] = None
    alert_message_template: Optional[str] = None
    suggested_actions: List[Dict[str, Any]] = []


class CDSRuleResponse(BaseModel):
    """CDS rule response."""
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    category: str
    alert_severity: str
    is_active: bool
    priority: int

    class Config:
        from_attributes = True


class PreventiveCareRecommendationResponse(BaseModel):
    """Preventive care recommendation response."""
    name: str
    description: str
    service_type: str
    is_due: bool
    last_performed: Optional[datetime]
    next_due: Optional[datetime]
    uspstf_grade: Optional[str]


# ==================== Vital Signs Schemas ====================

class VitalSignCreate(BaseModel):
    """Record vital sign request."""
    tenant_id: UUID
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    vital_type: VitalType
    value: Optional[float] = None
    value_string: Optional[str] = None  # For BP like "120/80"
    unit: str
    systolic: Optional[float] = None
    diastolic: Optional[float] = None
    recorded_by: UUID
    device_id: Optional[str] = None
    method: Optional[str] = None  # manual, device, patient_reported
    position: Optional[str] = None  # sitting, standing, supine
    notes: Optional[str] = None

    @validator('value', 'value_string', pre=True, always=True)
    def check_value_present(cls, v, values):
        # At least one value must be present
        return v


class VitalSignResponse(BaseModel):
    """Vital sign response."""
    id: UUID
    tenant_id: UUID
    patient_id: UUID
    vital_type: str
    value: Optional[float]
    value_string: Optional[str]
    unit: Optional[str]
    systolic: Optional[float]
    diastolic: Optional[float]
    is_abnormal: bool
    interpretation: Optional[str]
    recorded_at: datetime
    recorded_by: Optional[UUID]

    class Config:
        from_attributes = True


class VitalSignsBatchCreate(BaseModel):
    """Batch record vital signs request."""
    tenant_id: UUID
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    recorded_by: UUID
    vitals: List[Dict[str, Any]]


class EarlyWarningScoreResponse(BaseModel):
    """Early warning score response."""
    id: UUID
    patient_id: UUID
    score_type: str
    total_score: int
    risk_level: str
    component_scores: Dict[str, Any]
    calculated_at: datetime
    alert_triggered: bool

    class Config:
        from_attributes = True


class VitalTrendResponse(BaseModel):
    """Vital sign trend response."""
    vital_type: str
    unit: str
    values: List[Dict[str, Any]]  # [{"timestamp": ..., "value": ...}, ...]


# ==================== Discharge Schemas ====================

class DischargeChecklistItem(BaseModel):
    """Discharge checklist item."""
    item_id: str
    description: str
    is_required: bool = True
    is_completed: bool = False
    completed_by: Optional[UUID] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None


class DischargeMedication(BaseModel):
    """Discharge medication."""
    rxnorm_code: str
    drug_name: str
    sig_text: str
    quantity: int
    refills: int
    is_new: bool = False
    is_changed: bool = False
    is_discontinued: bool = False
    change_reason: Optional[str] = None


class DischargeRecordCreate(BaseModel):
    """Create discharge record request."""
    tenant_id: UUID
    patient_id: UUID
    encounter_id: UUID
    discharge_disposition: str
    discharge_destination: Optional[str] = None
    discharge_medications: List[DischargeMedication] = []
    discharge_instructions: Optional[str] = None
    activity_restrictions: Optional[str] = None
    diet_instructions: Optional[str] = None
    follow_up_appointments: List[Dict[str, Any]] = []
    follow_up_provider_id: Optional[UUID] = None
    follow_up_date: Optional[datetime] = None


class DischargeRecordResponse(BaseModel):
    """Discharge record response."""
    id: UUID
    tenant_id: UUID
    patient_id: UUID
    encounter_id: UUID
    discharge_disposition: str
    discharge_destination: Optional[str]
    checklist_items: List[Dict[str, Any]]
    all_items_completed: bool
    med_reconciliation_completed: bool
    discharge_instructions: Optional[str]
    follow_up_date: Optional[datetime]
    readmission_risk_score: Optional[float]
    readmission_risk_level: Optional[str]
    status: str
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class UpdateChecklistRequest(BaseModel):
    """Update checklist item request."""
    item_id: str
    is_completed: bool
    completed_by: UUID
    notes: Optional[str] = None


# ==================== List Response Schemas ====================

class PaginatedResponse(BaseModel):
    """Base paginated response."""
    total: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


class PrescriptionListResponse(PaginatedResponse):
    """Prescription list response."""
    prescriptions: List[PrescriptionResponse]


class LabOrderListResponse(PaginatedResponse):
    """Lab order list response."""
    orders: List[LabOrderResponse]


class ImagingOrderListResponse(PaginatedResponse):
    """Imaging order list response."""
    orders: List[ImagingOrderResponse]


class ReferralListResponse(PaginatedResponse):
    """Referral list response."""
    referrals: List[ReferralResponse]


class ClinicalNoteListResponse(PaginatedResponse):
    """Clinical note list response."""
    notes: List[ClinicalNoteResponse]


class CarePlanListResponse(PaginatedResponse):
    """Care plan list response."""
    care_plans: List[CarePlanResponse]


class ClinicalAlertListResponse(PaginatedResponse):
    """Clinical alert list response."""
    alerts: List[ClinicalAlertResponse]


class VitalSignListResponse(PaginatedResponse):
    """Vital sign list response."""
    vital_signs: List[VitalSignResponse]
