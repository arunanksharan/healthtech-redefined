"""
Insurance & Billing API Schemas

Pydantic schemas for request/response validation:
- Eligibility verification
- Prior authorization
- Claims management
- Payment processing
- Patient statements
- Fee schedules & contracts

EPIC-008: Insurance & Billing Integration
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from uuid import UUID
from enum import Enum
from decimal import Decimal


# ============================================================================
# ENUMS (matching models.py)
# ============================================================================

class EligibilityStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    TERMINATED = "terminated"
    UNKNOWN = "unknown"


class CoverageType(str, Enum):
    MEDICAL = "medical"
    DENTAL = "dental"
    VISION = "vision"
    PHARMACY = "pharmacy"
    MENTAL_HEALTH = "mental_health"
    SUBSTANCE_ABUSE = "substance_abuse"


class PlanType(str, Enum):
    HMO = "hmo"
    PPO = "ppo"
    EPO = "epo"
    POS = "pos"
    HDHP = "hdhp"
    MEDICARE = "medicare"
    MEDICAID = "medicaid"


class PriorAuthStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PENDING_INFO = "pending_info"
    APPROVED = "approved"
    DENIED = "denied"
    PARTIALLY_APPROVED = "partially_approved"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    APPEALED = "appealed"


class ClaimType(str, Enum):
    PROFESSIONAL = "professional"
    INSTITUTIONAL = "institutional"
    DENTAL = "dental"


class ClaimStatus(str, Enum):
    DRAFT = "draft"
    PENDING_SUBMISSION = "pending_submission"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    IN_PROCESS = "in_process"
    ADJUDICATED = "adjudicated"
    PAID = "paid"
    PARTIAL_PAID = "partial_paid"
    DENIED = "denied"
    REJECTED = "rejected"
    APPEALED = "appealed"
    VOID = "void"


class PaymentType(str, Enum):
    COPAY = "copay"
    COINSURANCE = "coinsurance"
    DEDUCTIBLE = "deductible"
    SELF_PAY = "self_pay"
    BALANCE = "balance"
    PREPAYMENT = "prepayment"
    REFUND = "refund"


class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    ACH = "ach"
    CHECK = "check"
    CASH = "cash"
    HSA = "hsa"
    FSA = "fsa"
    PAYMENT_PLAN = "payment_plan"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIAL_REFUND = "partial_refund"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"


class DenialCategory(str, Enum):
    ELIGIBILITY = "eligibility"
    AUTHORIZATION = "authorization"
    CODING = "coding"
    DUPLICATE = "duplicate"
    TIMELY_FILING = "timely_filing"
    MEDICAL_NECESSITY = "medical_necessity"
    BUNDLING = "bundling"
    OTHER = "other"


# ============================================================================
# INSURANCE POLICY SCHEMAS
# ============================================================================

class InsurancePolicyCreate(BaseModel):
    """Create insurance policy."""
    patient_id: UUID
    payer_id: str = Field(..., max_length=50)
    payer_name: str = Field(..., max_length=200)
    member_id: str = Field(..., max_length=50)
    plan_name: Optional[str] = None
    plan_type: Optional[str] = None
    group_number: Optional[str] = None
    group_name: Optional[str] = None
    subscriber_id: Optional[str] = None
    subscriber_name: Optional[str] = None
    relationship_to_subscriber: str = "self"
    effective_date: date
    termination_date: Optional[date] = None
    coverage_types: List[str] = ["medical"]
    is_primary: bool = True
    coordination_order: int = 1


class InsurancePolicyResponse(BaseModel):
    """Insurance policy response."""
    id: UUID
    patient_id: UUID
    payer_id: str
    payer_name: str
    plan_name: Optional[str]
    plan_type: Optional[str]
    member_id: str
    group_number: Optional[str]
    effective_date: date
    termination_date: Optional[date]
    status: str
    is_primary: bool
    coordination_order: int
    verified_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# ELIGIBILITY SCHEMAS
# ============================================================================

class EligibilityVerifyRequest(BaseModel):
    """Request eligibility verification."""
    patient_id: UUID
    payer_id: str
    member_id: str
    service_type: Optional[str] = None
    service_date: Optional[date] = None
    provider_id: Optional[UUID] = None
    provider_npi: Optional[str] = None


class BenefitInfoResponse(BaseModel):
    """Benefit information."""
    benefit_type: str
    covered: bool = True
    copay_amount: float = 0
    coinsurance_percent: float = 0
    prior_auth_required: bool = False
    visits_remaining: Optional[int] = None
    dollar_limit: Optional[float] = None
    notes: Optional[str] = None


class DeductibleInfoResponse(BaseModel):
    """Deductible information."""
    coverage_level: str
    network_type: str
    amount: float
    remaining: float
    met: float


class CoverageInfoResponse(BaseModel):
    """Coverage information."""
    payer_id: str
    payer_name: str
    plan_name: str
    plan_type: str
    member_id: str
    status: EligibilityStatus
    effective_date: Optional[date]
    termination_date: Optional[date]
    deductibles: List[DeductibleInfoResponse] = []
    benefits: Dict[str, BenefitInfoResponse] = {}


class EligibilityResponse(BaseModel):
    """Eligibility verification response."""
    id: UUID
    patient_id: UUID
    payer_id: str
    member_id: str
    status: str
    eligibility_status: Optional[str]
    coverage_active: bool
    service_eligible: bool = True
    copay_amount: float = 0
    coinsurance_percent: float = 0
    deductible_remaining: Optional[float]
    prior_auth_required: bool = False
    estimated_patient_responsibility: Optional[float]
    coverage_details: Optional[CoverageInfoResponse]
    requested_at: datetime
    responded_at: Optional[datetime]
    response_time_ms: Optional[int]

    class Config:
        from_attributes = True


class BatchEligibilityRequest(BaseModel):
    """Batch eligibility verification request."""
    verifications: List[EligibilityVerifyRequest]


# ============================================================================
# PRIOR AUTHORIZATION SCHEMAS
# ============================================================================

class PriorAuthCreate(BaseModel):
    """Create prior authorization request."""
    patient_id: UUID
    policy_id: Optional[UUID] = None
    payer_id: str
    payer_name: Optional[str] = None
    service_type: str
    procedure_codes: List[str] = []
    diagnosis_codes: List[str] = []
    quantity_requested: int = 1
    requesting_provider_id: Optional[UUID] = None
    requesting_provider_npi: Optional[str] = None
    performing_provider_id: Optional[UUID] = None
    performing_provider_npi: Optional[str] = None
    facility_id: Optional[UUID] = None
    service_date_start: Optional[date] = None
    service_date_end: Optional[date] = None
    clinical_summary: Optional[str] = None
    medical_necessity: Optional[str] = None


class PriorAuthUpdate(BaseModel):
    """Update prior authorization."""
    service_type: Optional[str] = None
    procedure_codes: Optional[List[str]] = None
    diagnosis_codes: Optional[List[str]] = None
    quantity_requested: Optional[int] = None
    clinical_summary: Optional[str] = None
    medical_necessity: Optional[str] = None
    service_date_start: Optional[date] = None
    service_date_end: Optional[date] = None


class PriorAuthResponse(BaseModel):
    """Prior authorization response."""
    id: UUID
    patient_id: UUID
    auth_number: Optional[str]
    payer_id: str
    payer_name: Optional[str]
    service_type: str
    procedure_codes: List[str]
    diagnosis_codes: List[str]
    quantity_requested: int
    quantity_approved: Optional[int]
    status: PriorAuthStatus
    status_reason: Optional[str]
    requested_date: date
    effective_date: Optional[date]
    expiration_date: Optional[date]
    decision_date: Optional[date]
    decision_reason: Optional[str]
    submitted_at: Optional[datetime]
    appeal_deadline: Optional[date]
    created_at: datetime

    class Config:
        from_attributes = True


class PriorAuthSubmit(BaseModel):
    """Submit prior authorization."""
    submission_method: str = "electronic"  # electronic, fax, phone, portal


class PriorAuthDecision(BaseModel):
    """Record prior auth decision."""
    status: PriorAuthStatus
    auth_number: Optional[str] = None
    quantity_approved: Optional[int] = None
    effective_date: Optional[date] = None
    expiration_date: Optional[date] = None
    decision_reason: Optional[str] = None
    payer_notes: Optional[str] = None


# ============================================================================
# CLAIMS SCHEMAS
# ============================================================================

class DiagnosisCreate(BaseModel):
    """Add diagnosis to claim."""
    code: str = Field(..., max_length=20)
    code_type: str = "ICD-10"
    sequence: Optional[int] = None


class ClaimLineCreate(BaseModel):
    """Add service line to claim."""
    procedure_code: str = Field(..., max_length=10)
    modifiers: List[str] = []
    description: Optional[str] = None
    revenue_code: Optional[str] = None
    diagnosis_pointers: List[str] = ["A"]
    service_date: date
    service_date_end: Optional[date] = None
    place_of_service: str = "11"
    units: float = 1
    charge_amount: float
    rendering_provider_npi: Optional[str] = None
    ndc_code: Optional[str] = None


class ClaimCreate(BaseModel):
    """Create a new claim."""
    claim_type: ClaimType = ClaimType.PROFESSIONAL
    patient_id: UUID
    policy_id: Optional[UUID] = None
    payer_id: str
    member_id: str
    group_number: Optional[str] = None
    prior_auth_number: Optional[str] = None
    prior_auth_id: Optional[UUID] = None
    billing_provider_npi: str
    billing_provider_tax_id: Optional[str] = None
    rendering_provider_npi: Optional[str] = None
    referring_provider_npi: Optional[str] = None
    facility_npi: Optional[str] = None
    encounter_id: Optional[UUID] = None
    service_date_start: date
    service_date_end: Optional[date] = None
    place_of_service: str = "11"
    diagnoses: List[DiagnosisCreate] = []
    lines: List[ClaimLineCreate] = []


class ClaimLineResponse(BaseModel):
    """Claim line response."""
    id: UUID
    line_number: int
    procedure_code: str
    modifiers: List[str]
    description: Optional[str]
    diagnosis_pointers: List[str]
    service_date: date
    units: float
    charge_amount: float
    allowed_amount: Optional[float]
    paid_amount: Optional[float]
    adjustment_amount: float
    patient_responsibility: Optional[float]
    status: str

    class Config:
        from_attributes = True


class ClaimResponse(BaseModel):
    """Claim response."""
    id: UUID
    claim_number: str
    claim_type: str
    patient_id: UUID
    payer_id: str
    payer_name: Optional[str]
    member_id: str
    service_date_start: date
    service_date_end: Optional[date]
    diagnoses: List[Dict[str, Any]]
    total_charge: float
    total_allowed: Optional[float]
    total_paid: float
    total_adjustment: float
    patient_responsibility: float
    balance: Optional[float]
    status: ClaimStatus
    status_date: Optional[datetime]
    submitted_at: Optional[datetime]
    payer_claim_number: Optional[str]
    denied_at: Optional[datetime]
    denial_reason_codes: List[str]
    lines: List[ClaimLineResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


class ClaimValidationResult(BaseModel):
    """Claim validation result."""
    valid: bool
    errors: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []


class ClaimSubmitRequest(BaseModel):
    """Submit claim."""
    submission_method: str = "electronic_837"


class ClaimAdjustmentCreate(BaseModel):
    """Add adjustment to claim."""
    claim_line_id: Optional[UUID] = None
    group_code: str  # CO, PR, OA, PI
    reason_code: str  # CARC code
    amount: float
    description: Optional[str] = None


# ============================================================================
# REMITTANCE/ERA SCHEMAS
# ============================================================================

class RemittanceCreate(BaseModel):
    """Record remittance/payment posting."""
    claim_id: UUID
    payer_id: str
    check_number: Optional[str] = None
    eft_trace_number: Optional[str] = None
    payment_method: str = "ACH"
    payment_date: date
    payment_amount: float
    charged_amount: float
    allowed_amount: float
    paid_amount: float
    patient_responsibility: float
    adjustments: List[ClaimAdjustmentCreate] = []
    remark_codes: List[str] = []


class RemittanceResponse(BaseModel):
    """Remittance response."""
    id: UUID
    claim_id: Optional[UUID]
    payer_id: str
    check_number: Optional[str]
    eft_trace_number: Optional[str]
    payment_date: Optional[date]
    payment_amount: Optional[float]
    charged_amount: Optional[float]
    allowed_amount: Optional[float]
    paid_amount: Optional[float]
    patient_responsibility: Optional[float]
    adjustments: List[Dict[str, Any]]
    processed_at: Optional[datetime]
    posted_at: Optional[datetime]
    auto_posted: bool

    class Config:
        from_attributes = True


# ============================================================================
# PAYMENT SCHEMAS
# ============================================================================

class PaymentCardCreate(BaseModel):
    """Store payment card."""
    patient_id: UUID
    token: str  # From payment processor
    last_four: str = Field(..., min_length=4, max_length=4)
    card_type: str
    expiry_month: int = Field(..., ge=1, le=12)
    expiry_year: int
    cardholder_name: Optional[str] = None
    billing_address: Optional[Dict[str, str]] = None
    is_default: bool = False


class PaymentCardResponse(BaseModel):
    """Payment card response."""
    id: UUID
    patient_id: UUID
    last_four: str
    card_type: str
    expiry_month: int
    expiry_year: int
    cardholder_name: Optional[str]
    is_default: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentCreate(BaseModel):
    """Create payment."""
    patient_id: UUID
    amount: float = Field(..., gt=0)
    payment_type: PaymentType
    payment_method: PaymentMethod
    card_id: Optional[UUID] = None
    check_number: Optional[str] = None
    encounter_id: Optional[UUID] = None
    claim_id: Optional[UUID] = None
    appointment_id: Optional[UUID] = None
    payment_plan_id: Optional[UUID] = None
    notes: Optional[str] = None


class PaymentResponse(BaseModel):
    """Payment response."""
    id: UUID
    payment_number: Optional[str]
    patient_id: UUID
    amount: float
    currency: str
    payment_type: PaymentType
    payment_method: PaymentMethod
    status: PaymentStatus
    card_last_four: Optional[str]
    card_type: Optional[str]
    check_number: Optional[str]
    processor_transaction_id: Optional[str]
    authorization_code: Optional[str]
    receipt_number: Optional[str]
    processed_at: Optional[datetime]
    refund_amount: Optional[float]
    refunded_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentRefundRequest(BaseModel):
    """Refund payment."""
    amount: Optional[float] = None  # Full refund if not specified
    reason: str


# ============================================================================
# PAYMENT PLAN SCHEMAS
# ============================================================================

class PaymentPlanCreate(BaseModel):
    """Create payment plan."""
    patient_id: UUID
    plan_name: Optional[str] = None
    total_amount: float = Field(..., gt=0)
    down_payment: float = 0
    payment_amount: float = Field(..., gt=0)
    frequency: str = "monthly"  # weekly, biweekly, monthly
    start_date: date
    total_payments: int = Field(..., ge=1)
    auto_pay: bool = False
    card_id: Optional[UUID] = None
    claim_ids: List[UUID] = []
    encounter_ids: List[UUID] = []


class PaymentPlanScheduleResponse(BaseModel):
    """Payment plan schedule item."""
    id: UUID
    sequence: int
    due_date: date
    amount: float
    status: str
    paid_at: Optional[datetime]

    class Config:
        from_attributes = True


class PaymentPlanResponse(BaseModel):
    """Payment plan response."""
    id: UUID
    patient_id: UUID
    plan_name: Optional[str]
    total_amount: float
    down_payment: float
    payment_amount: float
    frequency: str
    paid_amount: float
    remaining_amount: Optional[float]
    payments_made: int
    total_payments: int
    start_date: date
    end_date: Optional[date]
    next_payment_date: Optional[date]
    status: str
    auto_pay: bool
    agreement_signed: bool
    scheduled_payments: List[PaymentPlanScheduleResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentPlanSignRequest(BaseModel):
    """Sign payment plan agreement."""
    ip_address: Optional[str] = None


# ============================================================================
# PATIENT STATEMENT SCHEMAS
# ============================================================================

class StatementGenerateRequest(BaseModel):
    """Generate patient statement."""
    patient_id: UUID
    period_start: Optional[date] = None
    period_end: Optional[date] = None


class StatementResponse(BaseModel):
    """Patient statement response."""
    id: UUID
    patient_id: UUID
    statement_number: Optional[str]
    statement_date: date
    period_start: Optional[date]
    period_end: Optional[date]
    due_date: Optional[date]
    previous_balance: float
    new_charges: float
    payments_received: float
    adjustments: float
    current_balance: float
    amount_due: float
    current: float
    days_30: float
    days_60: float
    days_90: float
    days_120_plus: float
    status: str
    dunning_level: int
    delivery_method: str
    sent_at: Optional[datetime]
    pdf_url: Optional[str]
    line_items: List[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class StatementSendRequest(BaseModel):
    """Send statement to patient."""
    delivery_method: str = "email"  # email, mail, portal


# ============================================================================
# FEE SCHEDULE SCHEMAS
# ============================================================================

class FeeScheduleRateCreate(BaseModel):
    """Add rate to fee schedule."""
    procedure_code: str
    modifier: Optional[str] = None
    charge_amount: float
    expected_reimbursement: Optional[float] = None
    rvu_work: Optional[float] = None
    rvu_pe: Optional[float] = None
    rvu_mp: Optional[float] = None


class FeeScheduleCreate(BaseModel):
    """Create fee schedule."""
    name: str
    description: Optional[str] = None
    schedule_type: Optional[str] = None
    effective_date: date
    termination_date: Optional[date] = None
    is_default: bool = False
    payer_id: Optional[str] = None
    locality: Optional[str] = None
    rates: List[FeeScheduleRateCreate] = []


class FeeScheduleRateResponse(BaseModel):
    """Fee schedule rate response."""
    id: UUID
    procedure_code: str
    modifier: Optional[str]
    charge_amount: float
    expected_reimbursement: Optional[float]
    rvu_total: Optional[float]
    is_active: bool

    class Config:
        from_attributes = True


class FeeScheduleResponse(BaseModel):
    """Fee schedule response."""
    id: UUID
    name: str
    description: Optional[str]
    schedule_type: Optional[str]
    effective_date: date
    termination_date: Optional[date]
    is_default: bool
    payer_id: Optional[str]
    is_active: bool
    rates: List[FeeScheduleRateResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


class FeeScheduleBulkUpdateRequest(BaseModel):
    """Bulk update fee schedule rates."""
    rates: List[FeeScheduleRateCreate]


# ============================================================================
# CONTRACT SCHEMAS
# ============================================================================

class ContractRateOverrideCreate(BaseModel):
    """Add rate override to contract."""
    procedure_code: str
    modifier: Optional[str] = None
    rate_type: str = "fixed"  # fixed, percent_of_charge, percent_of_medicare
    rate_amount: Optional[float] = None
    rate_percent: Optional[float] = None
    effective_date: Optional[date] = None


class PayerContractCreate(BaseModel):
    """Create payer contract."""
    payer_id: str
    payer_name: str
    contract_name: Optional[str] = None
    contract_number: Optional[str] = None
    effective_date: date
    termination_date: Optional[date] = None
    auto_renew: bool = True
    renewal_notice_days: int = 90
    rate_type: Optional[str] = None
    base_rate_percent: Optional[float] = None
    fee_schedule_id: Optional[UUID] = None
    timely_filing_days: int = 365
    appeal_filing_days: int = 180
    terms_notes: Optional[str] = None
    rate_overrides: List[ContractRateOverrideCreate] = []


class ContractRateOverrideResponse(BaseModel):
    """Contract rate override response."""
    id: UUID
    procedure_code: str
    modifier: Optional[str]
    rate_type: str
    rate_amount: Optional[float]
    rate_percent: Optional[float]
    is_active: bool

    class Config:
        from_attributes = True


class PayerContractResponse(BaseModel):
    """Payer contract response."""
    id: UUID
    payer_id: str
    payer_name: str
    contract_name: Optional[str]
    contract_number: Optional[str]
    effective_date: date
    termination_date: Optional[date]
    auto_renew: bool
    rate_type: Optional[str]
    base_rate_percent: Optional[float]
    timely_filing_days: int
    appeal_filing_days: int
    status: str
    rate_overrides: List[ContractRateOverrideResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# DENIAL MANAGEMENT SCHEMAS
# ============================================================================

class DenialRecordCreate(BaseModel):
    """Record denial."""
    claim_id: UUID
    claim_line_id: Optional[UUID] = None
    denial_date: date
    denial_reason_code: str
    denial_reason_description: Optional[str] = None
    denial_category: Optional[DenialCategory] = None
    denied_amount: float
    is_appealable: bool = True
    appeal_deadline: Optional[date] = None


class DenialRecordResponse(BaseModel):
    """Denial record response."""
    id: UUID
    claim_id: UUID
    denial_date: date
    denial_reason_code: str
    denial_reason_description: Optional[str]
    denial_category: Optional[str]
    denied_amount: float
    potential_recovery: Optional[float]
    appeal_deadline: Optional[date]
    is_appealable: bool
    appeal_submitted: bool
    appeal_status: Optional[str]
    appeal_outcome: Optional[str]
    recovered_amount: Optional[float]
    resolution_status: str
    resolution_date: Optional[date]
    root_cause: Optional[str]
    preventable: Optional[bool]
    created_at: datetime

    class Config:
        from_attributes = True


class DenialAppealRequest(BaseModel):
    """Submit denial appeal."""
    appeal_notes: Optional[str] = None


class DenialResolveRequest(BaseModel):
    """Resolve denial."""
    resolution_status: str  # resolved, written_off
    resolution_notes: Optional[str] = None
    recovered_amount: Optional[float] = None
    root_cause: Optional[str] = None
    preventable: Optional[bool] = None


# ============================================================================
# ANALYTICS SCHEMAS
# ============================================================================

class RevenueCycleMetrics(BaseModel):
    """Revenue cycle KPIs."""
    days_in_ar: float
    clean_claim_rate: float
    denial_rate: float
    first_pass_payment_rate: float
    collection_rate: float
    net_collection_rate: float
    total_charges: float
    total_payments: float
    total_adjustments: float
    total_ar: float
    ar_over_90_days: float
    prior_auth_turnaround_days: float


class ClaimsSummary(BaseModel):
    """Claims summary statistics."""
    total_claims: int
    claims_by_status: Dict[str, int]
    claims_by_payer: Dict[str, int]
    total_charged: float
    total_paid: float
    total_denied: float
    average_days_to_payment: float


class DenialAnalytics(BaseModel):
    """Denial analytics."""
    total_denials: int
    total_denied_amount: float
    denials_by_category: Dict[str, int]
    denials_by_payer: Dict[str, int]
    denials_by_reason: Dict[str, int]
    appeal_success_rate: float
    total_recovered: float
    average_recovery_time_days: float


class PaymentAnalytics(BaseModel):
    """Payment analytics."""
    total_payments: int
    total_collected: float
    payments_by_type: Dict[str, float]
    payments_by_method: Dict[str, float]
    average_payment_amount: float
    refund_total: float


class ARAgingReport(BaseModel):
    """Accounts receivable aging report."""
    total_ar: float
    current: float
    days_1_30: float
    days_31_60: float
    days_61_90: float
    days_91_120: float
    days_over_120: float
    by_payer: Dict[str, Dict[str, float]]


# ============================================================================
# PAGINATION
# ============================================================================

class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
