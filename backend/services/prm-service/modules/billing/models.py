"""
Insurance & Billing Database Models

SQLAlchemy models for persistent storage of billing data:
- Insurance policies and coverage
- Eligibility verification records
- Prior authorizations
- Claims and claim lines
- Payments and adjustments
- Patient statements
- Fee schedules and contracts
- Revenue cycle analytics

EPIC-008: Insurance & Billing Integration
"""

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Float, DateTime, Date,
    ForeignKey, Index, UniqueConstraint, Numeric
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import uuid
import enum

Base = declarative_base()


# ============================================================================
# ENUMS
# ============================================================================

class EligibilityStatus(str, enum.Enum):
    """Eligibility verification status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    TERMINATED = "terminated"
    UNKNOWN = "unknown"


class CoverageType(str, enum.Enum):
    """Types of insurance coverage."""
    MEDICAL = "medical"
    DENTAL = "dental"
    VISION = "vision"
    PHARMACY = "pharmacy"
    MENTAL_HEALTH = "mental_health"
    SUBSTANCE_ABUSE = "substance_abuse"


class PlanType(str, enum.Enum):
    """Insurance plan types."""
    HMO = "hmo"
    PPO = "ppo"
    EPO = "epo"
    POS = "pos"
    HDHP = "hdhp"
    MEDICARE = "medicare"
    MEDICAID = "medicaid"
    TRICARE = "tricare"
    WORKERS_COMP = "workers_comp"
    AUTO = "auto"


class NetworkStatus(str, enum.Enum):
    """Provider network status."""
    IN_NETWORK = "in_network"
    OUT_OF_NETWORK = "out_of_network"
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"


class PriorAuthStatus(str, enum.Enum):
    """Prior authorization status."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PENDING_INFO = "pending_info"
    APPROVED = "approved"
    DENIED = "denied"
    PARTIALLY_APPROVED = "partially_approved"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    APPEALED = "appealed"


class ClaimType(str, enum.Enum):
    """Claim types."""
    PROFESSIONAL = "professional"  # CMS-1500
    INSTITUTIONAL = "institutional"  # UB-04
    DENTAL = "dental"


class ClaimStatus(str, enum.Enum):
    """Claim processing status."""
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


class SubmissionMethod(str, enum.Enum):
    """Claim submission methods."""
    ELECTRONIC_837 = "electronic_837"
    PAPER = "paper"
    PORTAL = "portal"
    DIRECT_ENTRY = "direct_entry"


class PaymentType(str, enum.Enum):
    """Payment types."""
    COPAY = "copay"
    COINSURANCE = "coinsurance"
    DEDUCTIBLE = "deductible"
    SELF_PAY = "self_pay"
    BALANCE = "balance"
    PREPAYMENT = "prepayment"
    REFUND = "refund"


class PaymentMethod(str, enum.Enum):
    """Payment methods."""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    ACH = "ach"
    CHECK = "check"
    CASH = "cash"
    HSA = "hsa"
    FSA = "fsa"
    PAYMENT_PLAN = "payment_plan"
    INSURANCE = "insurance"


class PaymentStatus(str, enum.Enum):
    """Payment status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIAL_REFUND = "partial_refund"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"


class StatementStatus(str, enum.Enum):
    """Statement status."""
    DRAFT = "draft"
    GENERATED = "generated"
    SENT = "sent"
    DELIVERED = "delivered"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    OVERDUE = "overdue"
    COLLECTIONS = "collections"


class AdjustmentGroupCode(str, enum.Enum):
    """CARC Group Codes."""
    CO = "CO"  # Contractual Obligation
    PR = "PR"  # Patient Responsibility
    OA = "OA"  # Other Adjustment
    PI = "PI"  # Payer Initiated


class DenialCategory(str, enum.Enum):
    """Denial categories."""
    ELIGIBILITY = "eligibility"
    AUTHORIZATION = "authorization"
    CODING = "coding"
    DUPLICATE = "duplicate"
    TIMELY_FILING = "timely_filing"
    MEDICAL_NECESSITY = "medical_necessity"
    BUNDLING = "bundling"
    OTHER = "other"


# ============================================================================
# INSURANCE & COVERAGE MODELS
# ============================================================================

class InsurancePolicy(Base):
    """Patient's insurance policy."""
    __tablename__ = "insurance_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Payer information
    payer_id = Column(String(50), nullable=False, index=True)
    payer_name = Column(String(200), nullable=False)
    payer_address = Column(Text)
    payer_phone = Column(String(20))
    payer_portal_url = Column(String(500))

    # Plan details
    plan_name = Column(String(200))
    plan_type = Column(String(50))  # HMO, PPO, etc.
    group_number = Column(String(50))
    group_name = Column(String(200))

    # Member info
    member_id = Column(String(50), nullable=False)
    subscriber_id = Column(String(50))
    subscriber_name = Column(String(200))
    relationship_to_subscriber = Column(String(20), default="self")

    # Coverage period
    effective_date = Column(Date, nullable=False)
    termination_date = Column(Date)

    # Coverage details
    coverage_types = Column(ARRAY(String), default=list)  # medical, dental, vision
    is_primary = Column(Boolean, default=True)
    coordination_order = Column(Integer, default=1)

    # Status
    status = Column(String(20), default="active")
    verified_at = Column(DateTime(timezone=True))
    verification_source = Column(String(50))

    # Benefits summary (cached from eligibility check)
    benefits_summary = Column(JSONB, default=dict)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_insurance_policies_patient", "tenant_id", "patient_id"),
        Index("idx_insurance_policies_payer", "payer_id"),
    )


class EligibilityVerification(Base):
    """Eligibility verification record."""
    __tablename__ = "eligibility_verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("insurance_policies.id"))

    # Request details
    payer_id = Column(String(50), nullable=False)
    member_id = Column(String(50), nullable=False)
    provider_id = Column(UUID(as_uuid=True))
    provider_npi = Column(String(10))
    service_type = Column(String(50))
    service_date = Column(Date)

    # Timing
    requested_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    responded_at = Column(DateTime(timezone=True))
    response_time_ms = Column(Integer)

    # Response
    status = Column(String(20), default="pending")  # pending, success, error
    error_code = Column(String(50))
    error_message = Column(Text)

    # Coverage results
    eligibility_status = Column(String(20))  # active, inactive, pending, terminated
    coverage_active = Column(Boolean, default=False)
    coverage_details = Column(JSONB, default=dict)  # Full coverage info

    # Service-specific results
    service_eligible = Column(Boolean, default=True)
    copay_amount = Column(Numeric(10, 2), default=0)
    coinsurance_percent = Column(Float, default=0)
    deductible_remaining = Column(Numeric(10, 2))
    out_of_pocket_remaining = Column(Numeric(10, 2))
    prior_auth_required = Column(Boolean, default=False)
    estimated_patient_responsibility = Column(Numeric(10, 2))

    # Source tracking
    source = Column(String(50), default="api")  # api, batch, manual
    clearinghouse_id = Column(String(100))
    trace_number = Column(String(50))

    # Raw data
    raw_request = Column(JSONB)
    raw_response = Column(JSONB)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("idx_eligibility_verifications_patient", "tenant_id", "patient_id"),
        Index("idx_eligibility_verifications_date", "requested_at"),
    )


# ============================================================================
# PRIOR AUTHORIZATION MODELS
# ============================================================================

class PriorAuthorization(Base):
    """Prior authorization request."""
    __tablename__ = "prior_authorizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("insurance_policies.id"))

    # Authorization details
    auth_number = Column(String(50), index=True)
    payer_id = Column(String(50), nullable=False)
    payer_name = Column(String(200))

    # Service details
    service_type = Column(String(100))  # imaging, surgery, DME, etc.
    procedure_codes = Column(ARRAY(String), default=list)  # CPT codes
    diagnosis_codes = Column(ARRAY(String), default=list)  # ICD-10 codes
    quantity_requested = Column(Integer, default=1)
    quantity_approved = Column(Integer)

    # Provider info
    requesting_provider_id = Column(UUID(as_uuid=True))
    requesting_provider_npi = Column(String(10))
    performing_provider_id = Column(UUID(as_uuid=True))
    performing_provider_npi = Column(String(10))
    facility_id = Column(UUID(as_uuid=True))
    facility_npi = Column(String(10))

    # Clinical information
    clinical_summary = Column(Text)
    medical_necessity = Column(Text)

    # Dates
    requested_date = Column(Date, default=date.today)
    service_date_start = Column(Date)
    service_date_end = Column(Date)
    effective_date = Column(Date)
    expiration_date = Column(Date)

    # Status tracking
    status = Column(String(30), default="draft", index=True)
    status_reason = Column(Text)

    # Submission
    submission_method = Column(String(30))  # electronic, fax, phone, portal
    submitted_at = Column(DateTime(timezone=True))
    submitted_by = Column(UUID(as_uuid=True))
    reference_number = Column(String(50))

    # Response
    decision_date = Column(Date)
    decision_reason = Column(Text)
    payer_notes = Column(Text)

    # Appeal tracking
    appeal_deadline = Column(Date)
    appealed_at = Column(DateTime(timezone=True))
    appeal_status = Column(String(30))
    appeal_notes = Column(Text)

    # Documents
    documents = Column(JSONB, default=list)  # [{id, name, type, uploaded_at}]

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_prior_auths_patient", "tenant_id", "patient_id"),
        Index("idx_prior_auths_status", "status"),
        Index("idx_prior_auths_auth_number", "auth_number"),
    )


# ============================================================================
# CLAIMS MODELS
# ============================================================================

class Claim(Base):
    """Insurance claim."""
    __tablename__ = "claims"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    claim_number = Column(String(50), unique=True, nullable=False)

    # Claim type
    claim_type = Column(String(20), nullable=False, default="professional")  # professional, institutional

    # Patient info
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    patient_account_number = Column(String(50))

    # Subscriber info (may differ from patient)
    subscriber_id = Column(UUID(as_uuid=True))
    subscriber_name = Column(String(200))
    relationship_to_subscriber = Column(String(20))

    # Insurance info
    policy_id = Column(UUID(as_uuid=True), ForeignKey("insurance_policies.id"))
    payer_id = Column(String(50), nullable=False, index=True)
    payer_name = Column(String(200))
    member_id = Column(String(50), nullable=False)
    group_number = Column(String(50))
    prior_auth_number = Column(String(50))
    prior_auth_id = Column(UUID(as_uuid=True), ForeignKey("prior_authorizations.id"))

    # Secondary insurance
    secondary_payer_id = Column(String(50))
    secondary_member_id = Column(String(50))
    secondary_policy_id = Column(UUID(as_uuid=True))

    # Provider info
    billing_provider_id = Column(UUID(as_uuid=True))
    billing_provider_npi = Column(String(10), nullable=False)
    billing_provider_tax_id = Column(String(20))
    rendering_provider_id = Column(UUID(as_uuid=True))
    rendering_provider_npi = Column(String(10))
    referring_provider_id = Column(UUID(as_uuid=True))
    referring_provider_npi = Column(String(10))
    facility_id = Column(UUID(as_uuid=True))
    facility_npi = Column(String(10))

    # Encounter reference
    encounter_id = Column(UUID(as_uuid=True))

    # Dates
    statement_date = Column(Date, default=date.today)
    service_date_start = Column(Date, nullable=False)
    service_date_end = Column(Date)
    admission_date = Column(Date)  # Institutional
    discharge_date = Column(Date)  # Institutional

    # Place of service
    place_of_service = Column(String(5), default="11")  # Office
    facility_type_code = Column(String(10))  # Institutional

    # Diagnoses
    diagnoses = Column(JSONB, default=list)  # [{code, type, sequence, pointer}]
    principal_diagnosis = Column(String(20))
    admitting_diagnosis = Column(String(20))

    # Totals
    total_charge = Column(Numeric(12, 2), default=0)
    total_allowed = Column(Numeric(12, 2))
    total_paid = Column(Numeric(12, 2), default=0)
    total_adjustment = Column(Numeric(12, 2), default=0)
    patient_responsibility = Column(Numeric(12, 2), default=0)
    balance = Column(Numeric(12, 2))

    # Status
    status = Column(String(30), default="draft", index=True)
    status_date = Column(DateTime(timezone=True))
    status_reason = Column(Text)

    # Submission
    submission_method = Column(String(30))
    submitted_at = Column(DateTime(timezone=True))
    submitted_by = Column(UUID(as_uuid=True))
    payer_claim_number = Column(String(50))
    clearinghouse_id = Column(String(100))
    clearinghouse_claim_id = Column(String(100))

    # Acknowledgment
    acknowledged_at = Column(DateTime(timezone=True))
    acknowledgment_code = Column(String(10))  # A, R (Accepted, Rejected)
    acknowledgment_errors = Column(JSONB, default=list)

    # Adjudication
    adjudicated_at = Column(DateTime(timezone=True))
    paid_at = Column(DateTime(timezone=True))
    check_number = Column(String(50))
    eft_trace_number = Column(String(50))

    # Denial
    denied_at = Column(DateTime(timezone=True))
    denial_reason_codes = Column(ARRAY(String), default=list)
    denial_category = Column(String(30))

    # Appeal
    appeal_deadline = Column(Date)
    appealed_at = Column(DateTime(timezone=True))
    appeal_status = Column(String(30))

    # Notes
    internal_notes = Column(Text)
    submission_notes = Column(Text)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lines = relationship("ClaimLine", back_populates="claim", cascade="all, delete-orphan")
    adjustments = relationship("ClaimAdjustment", back_populates="claim", cascade="all, delete-orphan")
    remittances = relationship("RemittanceAdvice", back_populates="claim")

    __table_args__ = (
        Index("idx_claims_patient", "tenant_id", "patient_id"),
        Index("idx_claims_payer", "payer_id"),
        Index("idx_claims_status", "status"),
        Index("idx_claims_service_date", "service_date_start"),
    )


class ClaimLine(Base):
    """Individual service line on a claim."""
    __tablename__ = "claim_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)

    # Line details
    line_number = Column(Integer, nullable=False)

    # Service
    procedure_code = Column(String(10), nullable=False)  # CPT/HCPCS
    modifiers = Column(ARRAY(String), default=list)  # Up to 4
    description = Column(String(500))

    # Revenue code (institutional)
    revenue_code = Column(String(10))

    # Diagnosis pointers
    diagnosis_pointers = Column(ARRAY(String), default=list)  # A, B, C, D

    # Service dates
    service_date = Column(Date, nullable=False)
    service_date_end = Column(Date)

    # Place of service
    place_of_service = Column(String(5))

    # Units and charges
    units = Column(Numeric(10, 2), default=1)
    unit_type = Column(String(10), default="UN")  # UN=Units, MJ=Minutes
    charge_amount = Column(Numeric(12, 2), nullable=False)

    # NDC for drugs
    ndc_code = Column(String(15))
    ndc_quantity = Column(Numeric(10, 3))
    ndc_unit = Column(String(5))

    # Rendering provider (if different from claim level)
    rendering_provider_npi = Column(String(10))

    # Adjudication
    allowed_amount = Column(Numeric(12, 2))
    paid_amount = Column(Numeric(12, 2))
    adjustment_amount = Column(Numeric(12, 2), default=0)
    patient_responsibility = Column(Numeric(12, 2))
    denial_reason = Column(String(10))
    remark_codes = Column(ARRAY(String), default=list)

    # Status
    status = Column(String(20), default="pending")

    # Relationship
    claim = relationship("Claim", back_populates="lines")

    __table_args__ = (
        Index("idx_claim_lines_claim", "claim_id"),
        Index("idx_claim_lines_procedure", "procedure_code"),
    )


class ClaimAdjustment(Base):
    """Adjustment to a claim."""
    __tablename__ = "claim_adjustments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    claim_line_id = Column(UUID(as_uuid=True), ForeignKey("claim_lines.id"))
    tenant_id = Column(UUID(as_uuid=True), nullable=False)

    # Adjustment details
    group_code = Column(String(5), nullable=False)  # CO, PR, OA, PI
    reason_code = Column(String(10), nullable=False)  # CARC code
    amount = Column(Numeric(12, 2), nullable=False)
    quantity = Column(Numeric(10, 2))

    description = Column(Text)

    # Source
    source = Column(String(30))  # remittance, manual, auto_post
    remittance_id = Column(UUID(as_uuid=True))

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True))

    claim = relationship("Claim", back_populates="adjustments")


# ============================================================================
# REMITTANCE & ERA MODELS
# ============================================================================

class RemittanceAdvice(Base):
    """835 Electronic Remittance Advice."""
    __tablename__ = "remittance_advices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"))

    # Payer info
    payer_id = Column(String(50), nullable=False)
    payer_name = Column(String(200))

    # Payment info
    check_number = Column(String(50))
    eft_trace_number = Column(String(50))
    payment_method = Column(String(20))  # CHK, ACH, NON
    payment_date = Column(Date)
    payment_amount = Column(Numeric(12, 2))

    # Claim details from ERA
    payer_claim_number = Column(String(50))
    patient_account_number = Column(String(50))
    claim_status_code = Column(String(5))

    # Amounts
    charged_amount = Column(Numeric(12, 2))
    allowed_amount = Column(Numeric(12, 2))
    paid_amount = Column(Numeric(12, 2))
    patient_responsibility = Column(Numeric(12, 2))

    # Adjustments summary
    adjustments = Column(JSONB, default=list)  # [{group, reason, amount}]
    remark_codes = Column(ARRAY(String), default=list)

    # Processing
    received_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    processed_at = Column(DateTime(timezone=True))
    posted_at = Column(DateTime(timezone=True))
    posted_by = Column(UUID(as_uuid=True))
    auto_posted = Column(Boolean, default=False)

    # Raw data
    raw_835 = Column(Text)

    claim = relationship("Claim", back_populates="remittances")


# ============================================================================
# PAYMENT MODELS
# ============================================================================

class Payment(Base):
    """Payment transaction."""
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    payment_number = Column(String(50), unique=True)

    # Patient
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Amount
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="USD")

    # Payment details
    payment_type = Column(String(30), nullable=False)  # copay, coinsurance, deductible, self_pay
    payment_method = Column(String(30), nullable=False)  # credit_card, ach, check, cash
    payment_source = Column(String(30))  # patient, guarantor, insurance

    # Card details (if applicable)
    card_id = Column(UUID(as_uuid=True), ForeignKey("payment_cards.id"))
    card_last_four = Column(String(4))
    card_type = Column(String(20))

    # Check details (if applicable)
    check_number = Column(String(50))
    bank_name = Column(String(200))

    # Status
    status = Column(String(30), default="pending", index=True)
    status_reason = Column(Text)

    # Processing
    processor = Column(String(50))  # stripe, square, etc.
    processor_transaction_id = Column(String(100))
    authorization_code = Column(String(50))
    processed_at = Column(DateTime(timezone=True))

    # Allocation
    encounter_id = Column(UUID(as_uuid=True))
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"))
    appointment_id = Column(UUID(as_uuid=True))
    payment_plan_id = Column(UUID(as_uuid=True), ForeignKey("payment_plans.id"))

    # Receipt
    receipt_number = Column(String(50))
    receipt_sent = Column(Boolean, default=False)
    receipt_sent_at = Column(DateTime(timezone=True))

    # Refund
    refund_amount = Column(Numeric(12, 2))
    refund_reason = Column(Text)
    refunded_at = Column(DateTime(timezone=True))
    refund_transaction_id = Column(String(100))

    # Metadata
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True))
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_payments_patient", "tenant_id", "patient_id"),
        Index("idx_payments_status", "status"),
        Index("idx_payments_date", "created_at"),
    )


class PaymentCard(Base):
    """Stored payment card (tokenized)."""
    __tablename__ = "payment_cards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Tokenized card info
    token = Column(String(200), nullable=False)  # Payment processor token
    last_four = Column(String(4), nullable=False)
    card_type = Column(String(20))  # visa, mastercard, amex
    expiry_month = Column(Integer)
    expiry_year = Column(Integer)

    # Card holder
    cardholder_name = Column(String(200))
    billing_address = Column(JSONB)

    # Status
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class PaymentPlan(Base):
    """Patient payment plan."""
    __tablename__ = "payment_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Plan details
    plan_name = Column(String(200))
    total_amount = Column(Numeric(12, 2), nullable=False)
    down_payment = Column(Numeric(12, 2), default=0)
    payment_amount = Column(Numeric(12, 2), nullable=False)
    frequency = Column(String(20), default="monthly")  # weekly, biweekly, monthly

    # Progress
    paid_amount = Column(Numeric(12, 2), default=0)
    remaining_amount = Column(Numeric(12, 2))
    payments_made = Column(Integer, default=0)
    total_payments = Column(Integer, nullable=False)

    # Dates
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    next_payment_date = Column(Date)

    # Status
    status = Column(String(20), default="active")  # active, completed, defaulted, cancelled

    # Auto-pay
    auto_pay = Column(Boolean, default=False)
    card_id = Column(UUID(as_uuid=True), ForeignKey("payment_cards.id"))

    # Related
    claim_ids = Column(ARRAY(UUID), default=list)
    encounter_ids = Column(ARRAY(UUID), default=list)

    # Signed agreement
    agreement_signed = Column(Boolean, default=False)
    agreement_signed_at = Column(DateTime(timezone=True))
    agreement_ip_address = Column(String(50))

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    scheduled_payments = relationship("PaymentPlanSchedule", back_populates="plan", cascade="all, delete-orphan")


class PaymentPlanSchedule(Base):
    """Scheduled payment in a payment plan."""
    __tablename__ = "payment_plan_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("payment_plans.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)

    sequence = Column(Integer, nullable=False)
    due_date = Column(Date, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(20), default="scheduled")  # scheduled, paid, overdue, cancelled

    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"))
    paid_at = Column(DateTime(timezone=True))

    plan = relationship("PaymentPlan", back_populates="scheduled_payments")


# ============================================================================
# PATIENT STATEMENT MODELS
# ============================================================================

class PatientStatement(Base):
    """Patient billing statement."""
    __tablename__ = "patient_statements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    statement_number = Column(String(50), unique=True)

    # Statement period
    statement_date = Column(Date, nullable=False)
    period_start = Column(Date)
    period_end = Column(Date)
    due_date = Column(Date)

    # Amounts
    previous_balance = Column(Numeric(12, 2), default=0)
    new_charges = Column(Numeric(12, 2), default=0)
    payments_received = Column(Numeric(12, 2), default=0)
    adjustments = Column(Numeric(12, 2), default=0)
    current_balance = Column(Numeric(12, 2), nullable=False)
    amount_due = Column(Numeric(12, 2), nullable=False)
    minimum_payment = Column(Numeric(12, 2))

    # Aging
    current = Column(Numeric(12, 2), default=0)
    days_30 = Column(Numeric(12, 2), default=0)
    days_60 = Column(Numeric(12, 2), default=0)
    days_90 = Column(Numeric(12, 2), default=0)
    days_120_plus = Column(Numeric(12, 2), default=0)

    # Line items
    line_items = Column(JSONB, default=list)  # [{date, description, amount, insurance_paid, patient_owes}]

    # Status
    status = Column(String(20), default="generated")
    dunning_level = Column(Integer, default=0)  # 0-4 collection stages

    # Delivery
    delivery_method = Column(String(20), default="email")  # email, mail, portal
    sent_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    viewed_at = Column(DateTime(timezone=True))

    # PDF
    pdf_url = Column(String(500))
    pdf_generated_at = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_patient_statements_patient", "tenant_id", "patient_id"),
        Index("idx_patient_statements_date", "statement_date"),
    )


# ============================================================================
# FEE SCHEDULE MODELS
# ============================================================================

class FeeSchedule(Base):
    """Fee schedule for pricing."""
    __tablename__ = "fee_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    description = Column(Text)
    schedule_type = Column(String(30))  # standard, medicare, medicaid, commercial

    # Effective dates
    effective_date = Column(Date, nullable=False)
    termination_date = Column(Date)

    # Default for
    is_default = Column(Boolean, default=False)
    payer_id = Column(String(50))  # If specific to payer

    # Geographic adjustment
    locality = Column(String(10))  # Medicare locality
    gpci_work = Column(Float, default=1.0)
    gpci_pe = Column(Float, default=1.0)
    gpci_mp = Column(Float, default=1.0)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    rates = relationship("FeeScheduleRate", back_populates="schedule", cascade="all, delete-orphan")


class FeeScheduleRate(Base):
    """Individual rate in a fee schedule."""
    __tablename__ = "fee_schedule_rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    schedule_id = Column(UUID(as_uuid=True), ForeignKey("fee_schedules.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)

    # Code
    procedure_code = Column(String(10), nullable=False)
    modifier = Column(String(5))

    # Amounts
    charge_amount = Column(Numeric(12, 2), nullable=False)  # What we bill
    expected_reimbursement = Column(Numeric(12, 2))  # Expected payment

    # RVUs (for Medicare)
    rvu_work = Column(Float)
    rvu_pe = Column(Float)
    rvu_mp = Column(Float)
    rvu_total = Column(Float)

    # Status
    is_active = Column(Boolean, default=True)

    schedule = relationship("FeeSchedule", back_populates="rates")

    __table_args__ = (
        Index("idx_fee_schedule_rates_code", "procedure_code"),
        UniqueConstraint("schedule_id", "procedure_code", "modifier", name="uq_fee_schedule_rate"),
    )


# ============================================================================
# CONTRACT MODELS
# ============================================================================

class PayerContract(Base):
    """Payer contract."""
    __tablename__ = "payer_contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Payer info
    payer_id = Column(String(50), nullable=False, index=True)
    payer_name = Column(String(200), nullable=False)
    contract_name = Column(String(200))

    # Contract terms
    contract_number = Column(String(50))
    effective_date = Column(Date, nullable=False)
    termination_date = Column(Date)
    auto_renew = Column(Boolean, default=True)
    renewal_notice_days = Column(Integer, default=90)

    # Rates
    rate_type = Column(String(30))  # percent_of_medicare, fee_schedule, per_diem, case_rate
    base_rate_percent = Column(Float)  # e.g., 120% of Medicare
    fee_schedule_id = Column(UUID(as_uuid=True), ForeignKey("fee_schedules.id"))

    # Timely filing
    timely_filing_days = Column(Integer, default=365)
    appeal_filing_days = Column(Integer, default=180)

    # Terms
    terms_notes = Column(Text)
    special_provisions = Column(JSONB, default=dict)

    # Documents
    contract_document_url = Column(String(500))

    # Status
    status = Column(String(20), default="active")  # draft, active, expired, terminated

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    rate_overrides = relationship("ContractRateOverride", back_populates="contract", cascade="all, delete-orphan")


class ContractRateOverride(Base):
    """Contract-specific rate override."""
    __tablename__ = "contract_rate_overrides"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("payer_contracts.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)

    procedure_code = Column(String(10), nullable=False)
    modifier = Column(String(5))

    # Override
    rate_type = Column(String(30))  # fixed, percent_of_charge, percent_of_medicare
    rate_amount = Column(Numeric(12, 2))
    rate_percent = Column(Float)

    # Effective dates
    effective_date = Column(Date)
    termination_date = Column(Date)

    is_active = Column(Boolean, default=True)

    contract = relationship("PayerContract", back_populates="rate_overrides")


# ============================================================================
# DENIAL MANAGEMENT MODELS
# ============================================================================

class DenialRecord(Base):
    """Denial tracking for denial management."""
    __tablename__ = "denial_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    claim_line_id = Column(UUID(as_uuid=True), ForeignKey("claim_lines.id"))

    # Denial info
    denial_date = Column(Date, nullable=False)
    denial_reason_code = Column(String(10), nullable=False)
    denial_reason_description = Column(Text)
    denial_category = Column(String(30))  # eligibility, auth, coding, etc.

    # Amounts
    denied_amount = Column(Numeric(12, 2), nullable=False)
    potential_recovery = Column(Numeric(12, 2))

    # Appeal
    appeal_deadline = Column(Date)
    is_appealable = Column(Boolean, default=True)
    appeal_submitted = Column(Boolean, default=False)
    appeal_submitted_at = Column(DateTime(timezone=True))
    appeal_status = Column(String(30))
    appeal_outcome = Column(String(30))  # overturned, upheld, partial
    recovered_amount = Column(Numeric(12, 2))

    # Assignment
    assigned_to = Column(UUID(as_uuid=True))
    assigned_at = Column(DateTime(timezone=True))

    # Resolution
    resolution_status = Column(String(30), default="open")  # open, in_progress, resolved, written_off
    resolution_date = Column(Date)
    resolution_notes = Column(Text)

    # Root cause
    root_cause = Column(String(100))
    preventable = Column(Boolean)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_denial_records_claim", "claim_id"),
        Index("idx_denial_records_status", "resolution_status"),
        Index("idx_denial_records_category", "denial_category"),
    )


# ============================================================================
# AUDIT & COMPLIANCE MODELS
# ============================================================================

class BillingAuditLog(Base):
    """Audit log for billing activities."""
    __tablename__ = "billing_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # What
    entity_type = Column(String(50), nullable=False)  # claim, payment, adjustment
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    action = Column(String(50), nullable=False)  # created, updated, submitted, voided

    # Who
    user_id = Column(UUID(as_uuid=True))
    user_name = Column(String(200))
    user_role = Column(String(50))

    # Details
    old_values = Column(JSONB)
    new_values = Column(JSONB)
    change_summary = Column(Text)

    # Context
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    session_id = Column(String(100))

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("idx_billing_audit_entity", "entity_type", "entity_id"),
        Index("idx_billing_audit_date", "created_at"),
    )
