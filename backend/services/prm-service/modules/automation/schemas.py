"""
Intelligent Automation Module Schemas
EPIC-012: Intelligent Automation Platform API Schemas
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field


# ==================== Workflow Enums ====================

class WorkflowStatusEnum(str, Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TriggerTypeEnum(str, Enum):
    """Workflow trigger types"""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    EVENT = "event"
    WEBHOOK = "webhook"
    CONDITION = "condition"


class ActionTypeEnum(str, Enum):
    """Workflow action types"""
    HTTP_REQUEST = "http_request"
    DATABASE_QUERY = "database_query"
    SEND_EMAIL = "send_email"
    SEND_SMS = "send_sms"
    SEND_NOTIFICATION = "send_notification"
    UPDATE_RECORD = "update_record"
    CREATE_TASK = "create_task"
    WAIT = "wait"
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"
    HUMAN_TASK = "human_task"
    CALL_WORKFLOW = "call_workflow"
    TRANSFORM_DATA = "transform_data"
    VALIDATE_DATA = "validate_data"
    ML_PREDICTION = "ml_prediction"


class StepTypeEnum(str, Enum):
    """Workflow step types"""
    ACTION = "action"
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"
    HUMAN_TASK = "human_task"
    SUB_WORKFLOW = "sub_workflow"


# ==================== Appointment Enums ====================

class AppointmentTypeEnum(str, Enum):
    """Appointment types"""
    NEW_PATIENT = "new_patient"
    FOLLOW_UP = "follow_up"
    ANNUAL_WELLNESS = "annual_wellness"
    SICK_VISIT = "sick_visit"
    PROCEDURE = "procedure"
    TELEHEALTH = "telehealth"
    LAB_ONLY = "lab_only"
    CONSULTATION = "consultation"


class NoShowRiskLevelEnum(str, Enum):
    """No-show risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


# ==================== Care Gap Enums ====================

class CareGapTypeEnum(str, Enum):
    """Types of care gaps"""
    PREVENTIVE = "preventive"
    CHRONIC_CARE = "chronic_care"
    MEDICATION = "medication"
    SCREENING = "screening"
    IMMUNIZATION = "immunization"
    FOLLOW_UP = "follow_up"


class CareGapPriorityEnum(str, Enum):
    """Care gap priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CareGapStatusEnum(str, Enum):
    """Care gap status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    SCHEDULED = "scheduled"
    CLOSED = "closed"
    EXCLUDED = "excluded"


# ==================== Document Processing Enums ====================

class DocumentTypeEnum(str, Enum):
    """Document types"""
    MEDICAL_RECORD = "medical_record"
    LAB_REPORT = "lab_report"
    PRESCRIPTION = "prescription"
    INSURANCE_CARD = "insurance_card"
    REFERRAL_LETTER = "referral_letter"
    DISCHARGE_SUMMARY = "discharge_summary"
    CONSENT_FORM = "consent_form"
    INTAKE_FORM = "intake_form"
    ID_DOCUMENT = "id_document"
    UNKNOWN = "unknown"


class ProcessingStatusEnum(str, Enum):
    """Document processing status"""
    PENDING = "pending"
    PREPROCESSING = "preprocessing"
    OCR_PROCESSING = "ocr_processing"
    CLASSIFYING = "classifying"
    EXTRACTING = "extracting"
    VALIDATING = "validating"
    REVIEW_REQUIRED = "review_required"
    COMPLETED = "completed"
    FAILED = "failed"


class ExtractionConfidenceEnum(str, Enum):
    """Extraction confidence levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


# ==================== Campaign Enums ====================

class CampaignTypeEnum(str, Enum):
    """Campaign types"""
    APPOINTMENT_REMINDER = "appointment_reminder"
    PREVENTIVE_CARE = "preventive_care"
    CHRONIC_CARE = "chronic_care"
    WELLNESS = "wellness"
    REACTIVATION = "reactivation"
    POST_VISIT = "post_visit"
    SATISFACTION = "satisfaction"
    EDUCATIONAL = "educational"
    BILLING = "billing"


class CampaignStatusEnum(str, Enum):
    """Campaign status"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OutreachChannelEnum(str, Enum):
    """Outreach channels"""
    SMS = "sms"
    EMAIL = "email"
    VOICE = "voice"
    WHATSAPP = "whatsapp"
    PUSH_NOTIFICATION = "push_notification"
    PATIENT_PORTAL = "patient_portal"


class MessageStatusEnum(str, Enum):
    """Message status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    RESPONDED = "responded"
    BOUNCED = "bounced"
    FAILED = "failed"


# ==================== Clinical Task Enums ====================

class ClinicalTaskTypeEnum(str, Enum):
    """Clinical task types"""
    LAB_REVIEW = "lab_review"
    LAB_CRITICAL = "lab_critical"
    MEDICATION_REFILL = "medication_refill"
    PRIOR_AUTH = "prior_auth"
    REFERRAL_PROCESSING = "referral_processing"
    DOCUMENT_REVIEW = "document_review"
    PATIENT_MESSAGE = "patient_message"
    CARE_COORDINATION = "care_coordination"


class TaskPriorityEnum(str, Enum):
    """Task priority levels"""
    STAT = "stat"
    URGENT = "urgent"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class TaskStatusEnum(str, Enum):
    """Task status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_REVIEW = "awaiting_review"
    COMPLETED = "completed"
    ESCALATED = "escalated"
    CANCELLED = "cancelled"


# ==================== Revenue Cycle Enums ====================

class ClaimStatusEnum(str, Enum):
    """Claim status"""
    DRAFT = "draft"
    VALIDATED = "validated"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    APPROVED = "approved"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    DENIED = "denied"
    APPEALED = "appealed"


class PriorAuthStatusEnum(str, Enum):
    """Prior authorization status"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    PARTIALLY_APPROVED = "partially_approved"
    DENIED = "denied"
    EXPIRED = "expired"


class CollectionStatusEnum(str, Enum):
    """Collection status"""
    CURRENT = "current"
    REMINDER_SENT = "reminder_sent"
    PAST_DUE_30 = "past_due_30"
    PAST_DUE_60 = "past_due_60"
    PAST_DUE_90 = "past_due_90"
    PAYMENT_PLAN = "payment_plan"
    COLLECTIONS = "collections"


# ==================== Human Task Enums ====================

class HumanTaskTypeEnum(str, Enum):
    """Human task types"""
    APPROVAL = "approval"
    REVIEW = "review"
    DATA_ENTRY = "data_entry"
    VERIFICATION = "verification"
    DECISION = "decision"
    EXCEPTION = "exception"
    ESCALATION = "escalation"


class TaskStateEnum(str, Enum):
    """Task state"""
    CREATED = "created"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    CANCELLED = "cancelled"


class AssignmentStrategyEnum(str, Enum):
    """Task assignment strategies"""
    ROUND_ROBIN = "round_robin"
    LOAD_BALANCED = "load_balanced"
    SKILL_BASED = "skill_based"
    MANUAL = "manual"


# ==================== Workflow Schemas ====================

class WorkflowTriggerSchema(BaseModel):
    """Workflow trigger configuration"""
    trigger_type: TriggerTypeEnum
    config: Dict[str, Any] = Field(default_factory=dict)
    schedule: Optional[str] = None  # Cron expression
    event_type: Optional[str] = None
    webhook_secret: Optional[str] = None


class WorkflowConditionSchema(BaseModel):
    """Workflow condition configuration"""
    field: str
    operator: str  # eq, ne, gt, lt, contains, etc.
    value: Any


class WorkflowActionSchema(BaseModel):
    """Workflow action configuration"""
    action_type: ActionTypeEnum
    config: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = 30
    retry_count: int = 0


class WorkflowStepSchema(BaseModel):
    """Workflow step definition"""
    step_id: str
    name: str
    step_type: StepTypeEnum
    action: Optional[WorkflowActionSchema] = None
    conditions: List[WorkflowConditionSchema] = Field(default_factory=list)
    on_success: Optional[str] = None
    on_failure: Optional[str] = None
    timeout_seconds: int = 60


class CreateWorkflowRequest(BaseModel):
    """Request to create a workflow"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    trigger: WorkflowTriggerSchema
    steps: List[WorkflowStepSchema] = Field(..., min_length=1)
    is_active: bool = True
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowResponse(BaseModel):
    """Workflow definition response"""
    workflow_id: UUID
    name: str
    description: Optional[str]
    trigger: WorkflowTriggerSchema
    steps: List[WorkflowStepSchema]
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime
    last_run_at: Optional[datetime]
    run_count: int
    success_count: int
    failure_count: int

    class Config:
        from_attributes = True


class ExecuteWorkflowRequest(BaseModel):
    """Request to execute a workflow"""
    workflow_id: UUID
    input_data: Dict[str, Any] = Field(default_factory=dict)
    async_execution: bool = True


class WorkflowExecutionResponse(BaseModel):
    """Workflow execution response"""
    execution_id: UUID
    workflow_id: UUID
    status: WorkflowStatusEnum
    started_at: datetime
    completed_at: Optional[datetime]
    current_step: Optional[str]
    output_data: Dict[str, Any]
    error_message: Optional[str]
    steps_completed: int
    total_steps: int

    class Config:
        from_attributes = True


# ==================== Appointment Optimization Schemas ====================

class NoShowPredictionRequest(BaseModel):
    """Request for no-show prediction"""
    patient_id: UUID
    appointment_date: datetime
    appointment_type: AppointmentTypeEnum
    provider_id: Optional[UUID] = None
    lead_time_days: Optional[int] = None


class NoShowPredictionResponse(BaseModel):
    """No-show prediction response"""
    prediction_id: UUID
    patient_id: UUID
    risk_level: NoShowRiskLevelEnum
    probability: float = Field(..., ge=0.0, le=1.0)
    risk_factors: List[Dict[str, Any]]
    recommended_interventions: List[str]
    reminder_schedule: List[Dict[str, Any]]

    class Config:
        from_attributes = True


class ScheduleOptimizationRequest(BaseModel):
    """Request for schedule optimization"""
    provider_id: UUID
    date_from: datetime
    date_to: datetime
    appointment_type: Optional[AppointmentTypeEnum] = None
    include_overbooking: bool = True


class TimeSlotResponse(BaseModel):
    """Available time slot"""
    start_time: datetime
    end_time: datetime
    provider_id: UUID
    room_id: Optional[str] = None
    appointment_type: AppointmentTypeEnum
    is_available: bool
    overbooking_allowed: bool
    overbooking_count: int


class ScheduleOptimizationResponse(BaseModel):
    """Schedule optimization response"""
    optimization_id: UUID
    provider_id: UUID
    available_slots: List[TimeSlotResponse]
    utilization_rate: float
    recommended_overbooking: Dict[str, int]
    predicted_no_shows: int


class WaitlistRequest(BaseModel):
    """Request to add to waitlist"""
    patient_id: UUID
    appointment_type: AppointmentTypeEnum
    provider_id: Optional[UUID] = None
    preferred_dates: List[datetime] = Field(default_factory=list)
    preferred_times: List[str] = Field(default_factory=list)
    urgency: TaskPriorityEnum = TaskPriorityEnum.NORMAL


class WaitlistResponse(BaseModel):
    """Waitlist entry response"""
    waitlist_id: UUID
    patient_id: UUID
    position: int
    estimated_wait_days: Optional[int]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Care Gap Schemas ====================

class CareGapRuleRequest(BaseModel):
    """Request to create a care gap rule"""
    name: str = Field(..., min_length=1)
    description: str
    gap_type: CareGapTypeEnum
    condition_codes: List[str] = Field(default_factory=list)
    procedure_codes: List[str] = Field(default_factory=list)
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    gender: Optional[str] = None
    frequency_days: int = 365
    measure_id: Optional[str] = None


class CareGapRuleResponse(BaseModel):
    """Care gap rule response"""
    rule_id: UUID
    name: str
    description: str
    gap_type: CareGapTypeEnum
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DetectCareGapsRequest(BaseModel):
    """Request to detect care gaps"""
    patient_id: Optional[UUID] = None
    gap_types: Optional[List[CareGapTypeEnum]] = None
    include_closed: bool = False


class DetectedCareGapResponse(BaseModel):
    """Detected care gap response"""
    gap_id: UUID
    patient_id: UUID
    rule_id: UUID
    gap_type: CareGapTypeEnum
    gap_name: str
    priority: CareGapPriorityEnum
    status: CareGapStatusEnum
    due_date: Optional[datetime]
    last_completed: Optional[datetime]
    days_overdue: int
    impact_score: float
    recommended_actions: List[str]
    detected_at: datetime

    class Config:
        from_attributes = True


class CareGapInterventionRequest(BaseModel):
    """Request to create care gap intervention"""
    gap_id: UUID
    channel: OutreachChannelEnum
    message: str
    scheduled_date: Optional[datetime] = None


class CareGapInterventionResponse(BaseModel):
    """Care gap intervention response"""
    intervention_id: UUID
    gap_id: UUID
    channel: OutreachChannelEnum
    status: str
    scheduled_at: datetime
    sent_at: Optional[datetime]
    response_received: bool

    class Config:
        from_attributes = True


# ==================== Document Processing Schemas ====================

class ProcessDocumentRequest(BaseModel):
    """Request to process a document"""
    file_path: str
    file_name: str
    file_type: str
    file_size: int
    expected_type: Optional[DocumentTypeEnum] = None
    auto_classify: bool = True
    extract_data: bool = True


class ExtractedFieldResponse(BaseModel):
    """Extracted field response"""
    field_name: str
    value: Any
    confidence: float
    confidence_level: ExtractionConfidenceEnum
    validation_status: str
    source_text: Optional[str] = None


class DocumentProcessingResponse(BaseModel):
    """Document processing response"""
    job_id: UUID
    document_id: UUID
    status: ProcessingStatusEnum
    document_type: Optional[DocumentTypeEnum]
    extracted_fields: List[ExtractedFieldResponse]
    validation_errors: List[str]
    requires_human_review: bool
    processing_time_ms: int
    created_at: datetime

    class Config:
        from_attributes = True


class ApproveDocumentExtractionRequest(BaseModel):
    """Request to approve document extraction"""
    job_id: UUID
    approved_fields: Dict[str, Any]
    notes: Optional[str] = None


# ==================== Campaign Schemas ====================

class SegmentCriteriaSchema(BaseModel):
    """Segment criteria"""
    field: str
    operator: str
    value: Any
    logical_operator: str = "AND"


class CreateSegmentRequest(BaseModel):
    """Request to create a patient segment"""
    name: str = Field(..., min_length=1)
    description: str
    criteria: List[SegmentCriteriaSchema]
    is_dynamic: bool = True


class SegmentResponse(BaseModel):
    """Patient segment response"""
    segment_id: UUID
    name: str
    description: str
    estimated_size: int
    is_dynamic: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CreateTemplateRequest(BaseModel):
    """Request to create a message template"""
    name: str = Field(..., min_length=1)
    channel: OutreachChannelEnum
    subject: Optional[str] = None
    body: str = Field(..., min_length=10)
    language: str = "en"


class TemplateResponse(BaseModel):
    """Message template response"""
    template_id: UUID
    name: str
    channel: OutreachChannelEnum
    subject: Optional[str]
    body: str
    variables: List[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CampaignStepSchema(BaseModel):
    """Campaign step configuration"""
    name: str
    channel: OutreachChannelEnum
    template_id: UUID
    delay_days: int = 0
    delay_hours: int = 0
    condition: Optional[Dict[str, Any]] = None
    fallback_channel: Optional[OutreachChannelEnum] = None


class CampaignScheduleSchema(BaseModel):
    """Campaign schedule configuration"""
    start_date: datetime
    end_date: Optional[datetime] = None
    send_times: List[str] = Field(default=["09:00"])
    send_days: List[int] = Field(default=[0, 1, 2, 3, 4])
    timezone: str = "UTC"
    max_per_day: Optional[int] = None
    cooldown_days: int = 7


class CreateCampaignRequest(BaseModel):
    """Request to create a campaign"""
    name: str = Field(..., min_length=1)
    description: str
    campaign_type: CampaignTypeEnum
    segment_id: UUID
    steps: List[CampaignStepSchema] = Field(..., min_length=1)
    schedule: CampaignScheduleSchema
    priority: TaskPriorityEnum = TaskPriorityEnum.NORMAL


class CampaignResponse(BaseModel):
    """Campaign response"""
    campaign_id: UUID
    name: str
    description: str
    campaign_type: CampaignTypeEnum
    status: CampaignStatusEnum
    segment_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CampaignAnalyticsResponse(BaseModel):
    """Campaign analytics response"""
    campaign_id: UUID
    total_targeted: int
    total_sent: int
    total_delivered: int
    total_opened: int
    total_clicked: int
    total_responded: int
    delivery_rate: float
    open_rate: float
    click_rate: float
    response_rate: float
    by_channel: Dict[str, Dict[str, int]]


class QuickCampaignRequest(BaseModel):
    """Request for quick one-off campaign"""
    campaign_type: CampaignTypeEnum
    patient_ids: List[UUID] = Field(..., min_length=1)
    message: str = Field(..., min_length=10)
    channel: OutreachChannelEnum = OutreachChannelEnum.SMS
    send_immediately: bool = True


# ==================== Clinical Task Schemas ====================

class CreateClinicalTaskRequest(BaseModel):
    """Request to create a clinical task"""
    task_type: ClinicalTaskTypeEnum
    patient_id: UUID
    provider_id: Optional[UUID] = None
    title: str = Field(..., min_length=1)
    description: str
    priority: TaskPriorityEnum = TaskPriorityEnum.NORMAL
    due_hours: Optional[int] = None
    assigned_to: Optional[UUID] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[UUID] = None


class ClinicalTaskResponse(BaseModel):
    """Clinical task response"""
    task_id: UUID
    task_type: ClinicalTaskTypeEnum
    patient_id: UUID
    provider_id: Optional[UUID]
    title: str
    description: str
    priority: TaskPriorityEnum
    status: TaskStatusEnum
    assigned_to: Optional[UUID]
    due_date: Optional[datetime]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class LabTriageRequest(BaseModel):
    """Request for lab result triage"""
    patient_id: UUID
    test_code: str
    test_name: str
    value: float
    unit: str
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None
    ordering_provider_id: UUID
    collected_date: datetime


class LabTriageResponse(BaseModel):
    """Lab triage response"""
    result_id: UUID
    patient_id: UUID
    test_name: str
    value: float
    status: str
    is_critical: bool
    task_created: bool
    task_id: Optional[UUID]

    class Config:
        from_attributes = True


class RefillRequest(BaseModel):
    """Medication refill request"""
    patient_id: UUID
    medication_name: str
    strength: str
    quantity: int
    days_supply: int
    refills_remaining: int
    prescriber_id: UUID
    pharmacy_id: Optional[UUID] = None
    is_controlled: bool = False


class RefillResponse(BaseModel):
    """Refill request response"""
    request_id: UUID
    patient_id: UUID
    medication_name: str
    status: str
    auto_approved: bool
    requires_review: bool
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ReferralRequest(BaseModel):
    """Patient referral request"""
    patient_id: UUID
    referring_provider_id: UUID
    specialty: str
    reason: str
    diagnosis_codes: List[str]
    urgency: TaskPriorityEnum = TaskPriorityEnum.NORMAL
    referred_to_provider_id: Optional[UUID] = None
    clinical_notes: Optional[str] = None


class ReferralResponse(BaseModel):
    """Referral response"""
    referral_id: UUID
    patient_id: UUID
    specialty: str
    status: str
    auth_required: bool
    auth_number: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Revenue Cycle Schemas ====================

class ClaimLineSchema(BaseModel):
    """Claim line item"""
    line_number: int
    procedure_code: str
    procedure_description: str
    diagnosis_codes: List[str]
    units: int
    charge_amount: Decimal
    modifier_codes: List[str] = Field(default_factory=list)
    service_date: Optional[datetime] = None


class CreateClaimRequest(BaseModel):
    """Request to create a claim"""
    patient_id: UUID
    encounter_id: UUID
    payer_id: UUID
    provider_id: UUID
    provider_npi: str
    claim_type: str = "professional"
    lines: List[ClaimLineSchema] = Field(..., min_length=1)
    service_date_from: datetime
    service_date_to: datetime
    prior_auth_number: Optional[str] = None


class ClaimResponse(BaseModel):
    """Claim response"""
    claim_id: UUID
    patient_id: UUID
    payer_id: UUID
    status: ClaimStatusEnum
    total_charges: Decimal
    total_paid: Decimal
    patient_responsibility: Decimal
    validation_errors: List[str]
    created_at: datetime
    submitted_at: Optional[datetime]

    class Config:
        from_attributes = True


class SubmitClaimRequest(BaseModel):
    """Request to submit a claim"""
    claim_id: UUID
    clearinghouse: str = "default"


class CreatePriorAuthRequest(BaseModel):
    """Request to create prior authorization"""
    patient_id: UUID
    payer_id: UUID
    provider_id: UUID
    procedure_codes: List[str]
    diagnosis_codes: List[str]
    service_type: str
    units_requested: int
    clinical_notes: Optional[str] = None


class PriorAuthResponse(BaseModel):
    """Prior authorization response"""
    auth_id: UUID
    patient_id: UUID
    payer_id: UUID
    status: PriorAuthStatusEnum
    auth_number: Optional[str]
    units_approved: Optional[int]
    effective_date: Optional[datetime]
    expiry_date: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class PostPaymentRequest(BaseModel):
    """Request to post a patient payment"""
    patient_id: UUID
    amount: Decimal = Field(..., gt=0)
    payment_method: str
    claim_id: Optional[UUID] = None
    notes: Optional[str] = None


class PaymentResponse(BaseModel):
    """Payment response"""
    payment_id: UUID
    patient_id: UUID
    amount: Decimal
    payment_type: str
    status: str
    payment_date: datetime

    class Config:
        from_attributes = True


class CreatePaymentPlanRequest(BaseModel):
    """Request to create a payment plan"""
    patient_id: UUID
    total_amount: Decimal = Field(..., gt=0)
    num_payments: int = Field(..., ge=2, le=60)
    payment_day: int = Field(1, ge=1, le=28)
    auto_pay: bool = False


class PaymentPlanResponse(BaseModel):
    """Payment plan response"""
    plan_id: UUID
    patient_id: UUID
    total_amount: Decimal
    monthly_payment: Decimal
    remaining_balance: Decimal
    status: str
    next_payment_date: datetime
    payments_made: int
    num_payments: int

    class Config:
        from_attributes = True


class ARAgingResponse(BaseModel):
    """Accounts receivable aging response"""
    total_ar: float
    aging_0_30: float
    aging_31_60: float
    aging_61_90: float
    aging_over_90: float
    accounts_count: int
    with_payment_plans: int
    in_collections: int


class DenialAnalyticsResponse(BaseModel):
    """Denial analytics response"""
    total_denials: int
    total_denied_amount: float
    total_appealed: int
    appeal_rate: float
    by_category: Dict[str, Dict[str, Any]]


# ==================== Human Task Schemas ====================

class CreateHumanTaskRequest(BaseModel):
    """Request to create a human task"""
    task_type: HumanTaskTypeEnum
    title: str = Field(..., min_length=1)
    description: str
    priority: TaskPriorityEnum = TaskPriorityEnum.NORMAL
    due_hours: Optional[int] = None
    form_data: Dict[str, Any] = Field(default_factory=dict)
    patient_id: Optional[UUID] = None
    provider_id: Optional[UUID] = None
    queue_id: Optional[UUID] = None
    assigned_to: Optional[UUID] = None
    tags: List[str] = Field(default_factory=list)


class HumanTaskResponse(BaseModel):
    """Human task response"""
    task_id: UUID
    task_type: HumanTaskTypeEnum
    title: str
    description: str
    priority: TaskPriorityEnum
    state: TaskStateEnum
    assigned_to: Optional[UUID]
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    outcome: Optional[str]

    class Config:
        from_attributes = True


class ClaimTaskRequest(BaseModel):
    """Request to claim a task"""
    task_id: UUID


class CompleteTaskRequest(BaseModel):
    """Request to complete a task"""
    task_id: UUID
    outcome: str
    outcome_data: Dict[str, Any] = Field(default_factory=dict)


class ApproveTaskRequest(BaseModel):
    """Request to approve a task"""
    task_id: UUID
    comments: Optional[str] = None


class RejectTaskRequest(BaseModel):
    """Request to reject a task"""
    task_id: UUID
    reason: str


class EscalateTaskRequest(BaseModel):
    """Request to escalate a task"""
    task_id: UUID
    reason: str
    escalate_to: Optional[UUID] = None


class AddTaskCommentRequest(BaseModel):
    """Request to add a task comment"""
    task_id: UUID
    content: str = Field(..., min_length=1)
    is_internal: bool = False


class TaskCommentResponse(BaseModel):
    """Task comment response"""
    comment_id: UUID
    task_id: UUID
    user_id: UUID
    content: str
    is_internal: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CreateTaskQueueRequest(BaseModel):
    """Request to create a task queue"""
    name: str = Field(..., min_length=1)
    description: str
    task_types: List[HumanTaskTypeEnum]
    assignment_strategy: AssignmentStrategyEnum = AssignmentStrategyEnum.LOAD_BALANCED
    eligible_roles: List[str] = Field(default_factory=list)
    auto_assign: bool = True


class TaskQueueResponse(BaseModel):
    """Task queue response"""
    queue_id: UUID
    name: str
    description: str
    task_types: List[HumanTaskTypeEnum]
    assignment_strategy: AssignmentStrategyEnum
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class WorkerStatsResponse(BaseModel):
    """Worker statistics response"""
    user_id: UUID
    current_tasks: int
    completed_total: int
    completed_today: int
    overdue_tasks: int
    average_completion_time: float
    performance_score: float


# ==================== Module Statistics ====================

class AutomationStatistics(BaseModel):
    """Automation module statistics"""
    total_workflows: int
    active_workflows: int
    workflow_executions_today: int
    workflow_success_rate: float
    total_care_gaps_detected: int
    care_gaps_closed_rate: float
    total_documents_processed: int
    document_accuracy_rate: float
    active_campaigns: int
    campaign_response_rate: float
    pending_clinical_tasks: int
    average_task_completion_time: float
    claims_submitted_today: int
    denial_rate: float


class AutomationHealthCheck(BaseModel):
    """Automation module health check"""
    status: str
    module: str
    features: List[str]
    workflow_engine_status: str
    document_processor_status: str
    outreach_engine_status: str
    task_manager_status: str
