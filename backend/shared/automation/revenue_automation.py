"""
Revenue Cycle Automation Service

Automates claims processing, prior authorization, denials management,
payment posting, and patient collections workflows.

Part of EPIC-012: Intelligent Automation Platform
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


class ClaimStatus(str, Enum):
    """Claim lifecycle status"""
    DRAFT = "draft"
    VALIDATED = "validated"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    IN_REVIEW = "in_review"
    PENDING_INFO = "pending_info"
    APPROVED = "approved"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    DENIED = "denied"
    APPEALED = "appealed"
    ADJUSTED = "adjusted"
    VOIDED = "voided"


class DenialReasonCategory(str, Enum):
    """Categories of claim denials"""
    ELIGIBILITY = "eligibility"
    AUTHORIZATION = "authorization"
    CODING = "coding"
    DUPLICATE = "duplicate"
    TIMELY_FILING = "timely_filing"
    MEDICAL_NECESSITY = "medical_necessity"
    BUNDLING = "bundling"
    NON_COVERED = "non_covered"
    COORDINATION_OF_BENEFITS = "cob"
    PATIENT_RESPONSIBILITY = "patient_responsibility"
    OTHER = "other"


class PriorAuthStatus(str, Enum):
    """Prior authorization status"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    PARTIALLY_APPROVED = "partially_approved"
    DENIED = "denied"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    """Payment status"""
    PENDING = "pending"
    POSTED = "posted"
    RECONCILED = "reconciled"
    ADJUSTED = "adjusted"
    REFUNDED = "refunded"


class CollectionStatus(str, Enum):
    """Patient collection status"""
    CURRENT = "current"
    REMINDER_SENT = "reminder_sent"
    PAST_DUE_30 = "past_due_30"
    PAST_DUE_60 = "past_due_60"
    PAST_DUE_90 = "past_due_90"
    PAYMENT_PLAN = "payment_plan"
    COLLECTIONS = "collections"
    BAD_DEBT = "bad_debt"
    WRITE_OFF = "write_off"


class PaymentPlanStatus(str, Enum):
    """Payment plan status"""
    ACTIVE = "active"
    CURRENT = "current"
    DELINQUENT = "delinquent"
    COMPLETED = "completed"
    DEFAULTED = "defaulted"
    CANCELLED = "cancelled"


@dataclass
class ClaimLine:
    """Individual line on a claim"""
    line_number: int
    procedure_code: str
    procedure_description: str
    diagnosis_codes: list[str]
    units: int
    charge_amount: Decimal
    modifier_codes: list[str] = field(default_factory=list)
    service_date: Optional[datetime] = None
    place_of_service: str = "11"  # Office
    allowed_amount: Optional[Decimal] = None
    paid_amount: Optional[Decimal] = None
    adjustment_amount: Optional[Decimal] = None
    patient_responsibility: Optional[Decimal] = None
    denial_reason: Optional[str] = None


@dataclass
class Claim:
    """Healthcare claim"""
    claim_id: str
    tenant_id: str
    patient_id: str
    encounter_id: str
    payer_id: str
    payer_name: str
    provider_id: str
    provider_npi: str
    status: ClaimStatus
    claim_type: str  # professional, institutional
    lines: list[ClaimLine]
    total_charges: Decimal
    service_date_from: datetime
    service_date_to: datetime
    created_at: datetime
    submitted_at: Optional[datetime] = None
    adjudicated_at: Optional[datetime] = None
    total_allowed: Decimal = Decimal("0")
    total_paid: Decimal = Decimal("0")
    total_adjustments: Decimal = Decimal("0")
    patient_responsibility: Decimal = Decimal("0")
    check_number: Optional[str] = None
    era_id: Optional[str] = None
    prior_auth_number: Optional[str] = None
    referring_provider_npi: Optional[str] = None
    rendering_provider_npi: Optional[str] = None
    validation_errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ClaimValidationRule:
    """Rule for claim validation"""
    rule_id: str
    name: str
    description: str
    error_code: str
    severity: str  # error, warning
    check_function: str
    active: bool = True


@dataclass
class DenialRecord:
    """Claim denial record"""
    denial_id: str
    claim_id: str
    line_number: Optional[int]
    denial_code: str
    denial_reason: str
    category: DenialReasonCategory
    payer_message: str
    amount_denied: Decimal
    received_date: datetime
    appeal_deadline: Optional[datetime] = None
    is_appealable: bool = True
    appeal_id: Optional[str] = None
    resolution: Optional[str] = None
    resolved_at: Optional[datetime] = None


@dataclass
class PriorAuthorization:
    """Prior authorization request"""
    auth_id: str
    tenant_id: str
    patient_id: str
    payer_id: str
    provider_id: str
    procedure_codes: list[str]
    diagnosis_codes: list[str]
    service_type: str
    units_requested: int
    status: PriorAuthStatus
    requested_date: datetime
    submitted_date: Optional[datetime] = None
    decision_date: Optional[datetime] = None
    auth_number: Optional[str] = None
    units_approved: Optional[int] = None
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    clinical_notes: Optional[str] = None
    denial_reason: Optional[str] = None
    supporting_docs: list[str] = field(default_factory=list)


@dataclass
class PaymentRecord:
    """Payment posting record"""
    payment_id: str
    tenant_id: str
    claim_id: Optional[str]
    patient_id: str
    payer_id: Optional[str]
    payment_type: str  # insurance, patient, adjustment
    amount: Decimal
    payment_date: datetime
    posted_date: Optional[datetime] = None
    status: PaymentStatus = PaymentStatus.PENDING
    check_number: Optional[str] = None
    era_id: Optional[str] = None
    payment_method: str = "EFT"  # EFT, check, credit_card, cash
    notes: Optional[str] = None


@dataclass
class PatientBalance:
    """Patient balance information"""
    patient_id: str
    tenant_id: str
    current_balance: Decimal
    balance_0_30: Decimal
    balance_31_60: Decimal
    balance_61_90: Decimal
    balance_over_90: Decimal
    collection_status: CollectionStatus
    last_statement_date: Optional[datetime] = None
    last_payment_date: Optional[datetime] = None
    last_payment_amount: Decimal = Decimal("0")
    payment_plan_id: Optional[str] = None
    has_active_payment_plan: bool = False


@dataclass
class PaymentPlan:
    """Patient payment plan"""
    plan_id: str
    tenant_id: str
    patient_id: str
    total_amount: Decimal
    monthly_payment: Decimal
    remaining_balance: Decimal
    start_date: datetime
    next_payment_date: datetime
    status: PaymentPlanStatus
    payment_day: int  # Day of month
    num_payments: int
    payments_made: int
    auto_pay_enabled: bool = False
    payment_method_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CollectionAction:
    """Collection action record"""
    action_id: str
    patient_id: str
    action_type: str  # statement, reminder, call, letter, collections_agency
    action_date: datetime
    amount: Decimal
    notes: Optional[str] = None
    result: Optional[str] = None
    next_action_date: Optional[datetime] = None


class RevenueCycleAutomation:
    """
    Revenue cycle automation engine.
    Handles claims, prior auth, denials, payments, and collections.
    """

    def __init__(self):
        self.claims: dict[str, Claim] = {}
        self.denials: dict[str, DenialRecord] = {}
        self.prior_auths: dict[str, PriorAuthorization] = {}
        self.payments: dict[str, PaymentRecord] = {}
        self.patient_balances: dict[str, PatientBalance] = {}
        self.payment_plans: dict[str, PaymentPlan] = {}
        self.collection_actions: dict[str, CollectionAction] = {}
        self.validation_rules: list[ClaimValidationRule] = []
        self._initialize_validation_rules()

    def _initialize_validation_rules(self):
        """Initialize claim validation rules"""
        self.validation_rules = [
            ClaimValidationRule(
                rule_id="req-patient-info",
                name="Patient Information Required",
                description="Patient demographics must be complete",
                error_code="PAT001",
                severity="error",
                check_function="_validate_patient_info"
            ),
            ClaimValidationRule(
                rule_id="req-diagnosis",
                name="Diagnosis Code Required",
                description="At least one diagnosis code required",
                error_code="DX001",
                severity="error",
                check_function="_validate_diagnosis"
            ),
            ClaimValidationRule(
                rule_id="req-npi",
                name="Provider NPI Required",
                description="Valid provider NPI required",
                error_code="NPI001",
                severity="error",
                check_function="_validate_npi"
            ),
            ClaimValidationRule(
                rule_id="valid-dates",
                name="Valid Service Dates",
                description="Service dates must be valid and not in future",
                error_code="DATE001",
                severity="error",
                check_function="_validate_dates"
            ),
            ClaimValidationRule(
                rule_id="modifier-check",
                name="Modifier Validation",
                description="Procedure-modifier combinations must be valid",
                error_code="MOD001",
                severity="warning",
                check_function="_validate_modifiers"
            ),
            ClaimValidationRule(
                rule_id="prior-auth-check",
                name="Prior Authorization Check",
                description="Check if prior auth is required and present",
                error_code="AUTH001",
                severity="error",
                check_function="_validate_prior_auth"
            ),
            ClaimValidationRule(
                rule_id="timely-filing",
                name="Timely Filing Check",
                description="Claim must be within filing deadline",
                error_code="TIME001",
                severity="error",
                check_function="_validate_timely_filing"
            )
        ]

    async def validate_claim(
        self,
        claim: Claim,
        patient_data: dict[str, Any],
        payer_rules: Optional[dict[str, Any]] = None
    ) -> tuple[bool, list[str], list[str]]:
        """Validate a claim before submission"""
        errors = []
        warnings = []

        for rule in self.validation_rules:
            if not rule.active:
                continue

            is_valid, message = await self._run_validation(rule, claim, patient_data, payer_rules)
            if not is_valid:
                if rule.severity == "error":
                    errors.append(f"[{rule.error_code}] {message}")
                else:
                    warnings.append(f"[{rule.error_code}] {message}")

        claim.validation_errors = errors
        claim.status = ClaimStatus.VALIDATED if not errors else ClaimStatus.DRAFT

        return len(errors) == 0, errors, warnings

    async def _run_validation(
        self,
        rule: ClaimValidationRule,
        claim: Claim,
        patient_data: dict[str, Any],
        payer_rules: Optional[dict[str, Any]]
    ) -> tuple[bool, str]:
        """Run a single validation rule"""
        validation_methods = {
            "_validate_patient_info": self._validate_patient_info,
            "_validate_diagnosis": self._validate_diagnosis,
            "_validate_npi": self._validate_npi,
            "_validate_dates": self._validate_dates,
            "_validate_modifiers": self._validate_modifiers,
            "_validate_prior_auth": self._validate_prior_auth,
            "_validate_timely_filing": self._validate_timely_filing
        }

        method = validation_methods.get(rule.check_function)
        if method:
            return await method(claim, patient_data, payer_rules)

        return True, ""

    async def _validate_patient_info(
        self,
        claim: Claim,
        patient_data: dict[str, Any],
        _
    ) -> tuple[bool, str]:
        """Validate patient information"""
        required_fields = ["name", "date_of_birth", "gender", "address"]
        missing = [f for f in required_fields if not patient_data.get(f)]
        if missing:
            return False, f"Missing patient info: {', '.join(missing)}"
        return True, ""

    async def _validate_diagnosis(
        self,
        claim: Claim,
        _patient: dict[str, Any],
        _payer: Optional[dict[str, Any]]
    ) -> tuple[bool, str]:
        """Validate diagnosis codes"""
        all_dx = set()
        for line in claim.lines:
            all_dx.update(line.diagnosis_codes)
        if not all_dx:
            return False, "At least one diagnosis code required"
        return True, ""

    async def _validate_npi(
        self,
        claim: Claim,
        _patient: dict[str, Any],
        _payer: Optional[dict[str, Any]]
    ) -> tuple[bool, str]:
        """Validate provider NPI"""
        if not claim.provider_npi or len(claim.provider_npi) != 10:
            return False, "Invalid provider NPI"
        return True, ""

    async def _validate_dates(
        self,
        claim: Claim,
        _patient: dict[str, Any],
        _payer: Optional[dict[str, Any]]
    ) -> tuple[bool, str]:
        """Validate service dates"""
        now = datetime.utcnow()
        if claim.service_date_from > now:
            return False, "Service date cannot be in the future"
        if claim.service_date_to < claim.service_date_from:
            return False, "Service end date cannot be before start date"
        return True, ""

    async def _validate_modifiers(
        self,
        claim: Claim,
        _patient: dict[str, Any],
        _payer: Optional[dict[str, Any]]
    ) -> tuple[bool, str]:
        """Validate procedure-modifier combinations"""
        # Simplified validation - in production would check against CMS rules
        invalid_combinations = []
        for line in claim.lines:
            if "TC" in line.modifier_codes and "26" in line.modifier_codes:
                invalid_combinations.append(f"Line {line.line_number}: TC and 26 cannot be used together")

        if invalid_combinations:
            return False, "; ".join(invalid_combinations)
        return True, ""

    async def _validate_prior_auth(
        self,
        claim: Claim,
        _patient: dict[str, Any],
        payer_rules: Optional[dict[str, Any]]
    ) -> tuple[bool, str]:
        """Validate prior authorization"""
        if not payer_rules:
            return True, ""

        auth_required_codes = payer_rules.get("auth_required_codes", [])
        for line in claim.lines:
            if line.procedure_code in auth_required_codes and not claim.prior_auth_number:
                return False, f"Prior auth required for procedure {line.procedure_code}"

        return True, ""

    async def _validate_timely_filing(
        self,
        claim: Claim,
        _patient: dict[str, Any],
        payer_rules: Optional[dict[str, Any]]
    ) -> tuple[bool, str]:
        """Validate timely filing"""
        filing_limit_days = 365  # Default 1 year
        if payer_rules:
            filing_limit_days = payer_rules.get("filing_limit_days", 365)

        days_since_service = (datetime.utcnow() - claim.service_date_to).days
        if days_since_service > filing_limit_days:
            return False, f"Claim exceeds timely filing limit of {filing_limit_days} days"

        return True, ""

    async def submit_claim(
        self,
        claim_id: str,
        clearinghouse: str = "default"
    ) -> Claim:
        """Submit claim to clearinghouse"""
        claim = self.claims.get(claim_id)
        if not claim:
            raise ValueError(f"Claim not found: {claim_id}")

        if claim.status != ClaimStatus.VALIDATED:
            raise ValueError("Claim must be validated before submission")

        # Simulate submission
        await asyncio.sleep(0.1)

        claim.status = ClaimStatus.SUBMITTED
        claim.submitted_at = datetime.utcnow()
        claim.metadata["clearinghouse"] = clearinghouse
        claim.metadata["submission_id"] = str(uuid4())

        return claim

    async def process_era(
        self,
        tenant_id: str,
        era_data: dict[str, Any]
    ) -> list[PaymentRecord]:
        """Process Electronic Remittance Advice (ERA/835)"""
        payments = []
        era_id = era_data.get("era_id", str(uuid4()))

        for claim_payment in era_data.get("claim_payments", []):
            claim_id = claim_payment.get("claim_id")
            claim = self.claims.get(claim_id)

            if claim:
                # Update claim with payment info
                claim.total_paid = Decimal(str(claim_payment.get("paid_amount", 0)))
                claim.total_allowed = Decimal(str(claim_payment.get("allowed_amount", 0)))
                claim.total_adjustments = Decimal(str(claim_payment.get("adjustment_amount", 0)))
                claim.patient_responsibility = Decimal(str(claim_payment.get("patient_responsibility", 0)))
                claim.check_number = era_data.get("check_number")
                claim.era_id = era_id
                claim.adjudicated_at = datetime.utcnow()

                # Update status
                if claim.total_paid >= claim.total_charges:
                    claim.status = ClaimStatus.PAID
                elif claim.total_paid > 0:
                    claim.status = ClaimStatus.PARTIALLY_PAID
                else:
                    claim.status = ClaimStatus.DENIED

                # Process denials
                for denial in claim_payment.get("denials", []):
                    await self._process_denial(claim, denial)

                # Create payment record
                payment = PaymentRecord(
                    payment_id=str(uuid4()),
                    tenant_id=tenant_id,
                    claim_id=claim_id,
                    patient_id=claim.patient_id,
                    payer_id=claim.payer_id,
                    payment_type="insurance",
                    amount=claim.total_paid,
                    payment_date=datetime.utcnow(),
                    status=PaymentStatus.PENDING,
                    check_number=era_data.get("check_number"),
                    era_id=era_id
                )
                self.payments[payment.payment_id] = payment
                payments.append(payment)

                # Update patient balance
                await self._update_patient_balance(tenant_id, claim.patient_id, claim)

        return payments

    async def _process_denial(
        self,
        claim: Claim,
        denial_data: dict[str, Any]
    ) -> DenialRecord:
        """Process a claim denial"""
        denial = DenialRecord(
            denial_id=str(uuid4()),
            claim_id=claim.claim_id,
            line_number=denial_data.get("line_number"),
            denial_code=denial_data.get("code", ""),
            denial_reason=denial_data.get("reason", ""),
            category=self._categorize_denial(denial_data.get("code", "")),
            payer_message=denial_data.get("message", ""),
            amount_denied=Decimal(str(denial_data.get("amount", 0))),
            received_date=datetime.utcnow(),
            appeal_deadline=datetime.utcnow() + timedelta(days=60)  # Default 60 days
        )

        self.denials[denial.denial_id] = denial
        return denial

    def _categorize_denial(self, code: str) -> DenialReasonCategory:
        """Categorize denial based on code"""
        # Map common denial codes to categories
        code_mapping = {
            "1": DenialReasonCategory.PATIENT_RESPONSIBILITY,
            "2": DenialReasonCategory.PATIENT_RESPONSIBILITY,
            "3": DenialReasonCategory.PATIENT_RESPONSIBILITY,
            "4": DenialReasonCategory.CODING,
            "5": DenialReasonCategory.CODING,
            "18": DenialReasonCategory.DUPLICATE,
            "27": DenialReasonCategory.ELIGIBILITY,
            "29": DenialReasonCategory.TIMELY_FILING,
            "50": DenialReasonCategory.MEDICAL_NECESSITY,
            "96": DenialReasonCategory.NON_COVERED,
            "97": DenialReasonCategory.AUTHORIZATION
        }
        return code_mapping.get(code, DenialReasonCategory.OTHER)

    async def _update_patient_balance(
        self,
        tenant_id: str,
        patient_id: str,
        claim: Claim
    ):
        """Update patient balance after claim adjudication"""
        balance = self.patient_balances.get(patient_id)
        if not balance:
            balance = PatientBalance(
                patient_id=patient_id,
                tenant_id=tenant_id,
                current_balance=Decimal("0"),
                balance_0_30=Decimal("0"),
                balance_31_60=Decimal("0"),
                balance_61_90=Decimal("0"),
                balance_over_90=Decimal("0"),
                collection_status=CollectionStatus.CURRENT
            )
            self.patient_balances[patient_id] = balance

        balance.current_balance += claim.patient_responsibility

    async def create_appeal(
        self,
        denial_id: str,
        appeal_reason: str,
        supporting_docs: list[str],
        submitted_by: str
    ) -> DenialRecord:
        """Create an appeal for a denied claim"""
        denial = self.denials.get(denial_id)
        if not denial:
            raise ValueError(f"Denial not found: {denial_id}")

        if not denial.is_appealable:
            raise ValueError("This denial is not appealable")

        if denial.appeal_deadline and datetime.utcnow() > denial.appeal_deadline:
            raise ValueError("Appeal deadline has passed")

        appeal_id = str(uuid4())
        denial.appeal_id = appeal_id

        # Update original claim status
        claim = self.claims.get(denial.claim_id)
        if claim:
            claim.status = ClaimStatus.APPEALED
            claim.metadata["appeal_id"] = appeal_id
            claim.metadata["appeal_reason"] = appeal_reason
            claim.metadata["appeal_docs"] = supporting_docs
            claim.metadata["appealed_by"] = submitted_by
            claim.metadata["appeal_date"] = datetime.utcnow().isoformat()

        return denial

    async def submit_prior_auth(
        self,
        tenant_id: str,
        patient_id: str,
        payer_id: str,
        provider_id: str,
        procedure_codes: list[str],
        diagnosis_codes: list[str],
        service_type: str,
        units: int,
        clinical_notes: Optional[str] = None
    ) -> PriorAuthorization:
        """Submit a prior authorization request"""
        auth = PriorAuthorization(
            auth_id=str(uuid4()),
            tenant_id=tenant_id,
            patient_id=patient_id,
            payer_id=payer_id,
            provider_id=provider_id,
            procedure_codes=procedure_codes,
            diagnosis_codes=diagnosis_codes,
            service_type=service_type,
            units_requested=units,
            status=PriorAuthStatus.PENDING,
            requested_date=datetime.utcnow(),
            clinical_notes=clinical_notes
        )

        self.prior_auths[auth.auth_id] = auth

        # Simulate submission
        await asyncio.sleep(0.1)
        auth.status = PriorAuthStatus.SUBMITTED
        auth.submitted_date = datetime.utcnow()

        return auth

    async def update_prior_auth_decision(
        self,
        auth_id: str,
        decision: str,
        auth_number: Optional[str] = None,
        units_approved: Optional[int] = None,
        effective_date: Optional[datetime] = None,
        expiry_date: Optional[datetime] = None,
        denial_reason: Optional[str] = None
    ) -> PriorAuthorization:
        """Update prior auth with payer decision"""
        auth = self.prior_auths.get(auth_id)
        if not auth:
            raise ValueError(f"Prior auth not found: {auth_id}")

        auth.decision_date = datetime.utcnow()

        if decision == "approved":
            auth.status = PriorAuthStatus.APPROVED
            auth.auth_number = auth_number
            auth.units_approved = units_approved or auth.units_requested
            auth.effective_date = effective_date or datetime.utcnow()
            auth.expiry_date = expiry_date
        elif decision == "partially_approved":
            auth.status = PriorAuthStatus.PARTIALLY_APPROVED
            auth.auth_number = auth_number
            auth.units_approved = units_approved
            auth.effective_date = effective_date
            auth.expiry_date = expiry_date
        elif decision == "denied":
            auth.status = PriorAuthStatus.DENIED
            auth.denial_reason = denial_reason

        return auth

    async def post_patient_payment(
        self,
        tenant_id: str,
        patient_id: str,
        amount: Decimal,
        payment_method: str,
        claim_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> PaymentRecord:
        """Post a patient payment"""
        payment = PaymentRecord(
            payment_id=str(uuid4()),
            tenant_id=tenant_id,
            claim_id=claim_id,
            patient_id=patient_id,
            payer_id=None,
            payment_type="patient",
            amount=amount,
            payment_date=datetime.utcnow(),
            status=PaymentStatus.POSTED,
            posted_date=datetime.utcnow(),
            payment_method=payment_method,
            notes=notes
        )

        self.payments[payment.payment_id] = payment

        # Update patient balance
        balance = self.patient_balances.get(patient_id)
        if balance:
            balance.current_balance -= amount
            balance.last_payment_date = datetime.utcnow()
            balance.last_payment_amount = amount

            # Update collection status if balance cleared
            if balance.current_balance <= 0:
                balance.collection_status = CollectionStatus.CURRENT

        return payment

    async def create_payment_plan(
        self,
        tenant_id: str,
        patient_id: str,
        total_amount: Decimal,
        num_payments: int,
        payment_day: int = 1,
        auto_pay: bool = False
    ) -> PaymentPlan:
        """Create a patient payment plan"""
        monthly_payment = total_amount / num_payments

        plan = PaymentPlan(
            plan_id=str(uuid4()),
            tenant_id=tenant_id,
            patient_id=patient_id,
            total_amount=total_amount,
            monthly_payment=monthly_payment.quantize(Decimal("0.01")),
            remaining_balance=total_amount,
            start_date=datetime.utcnow(),
            next_payment_date=self._calculate_next_payment_date(payment_day),
            status=PaymentPlanStatus.ACTIVE,
            payment_day=payment_day,
            num_payments=num_payments,
            payments_made=0,
            auto_pay_enabled=auto_pay
        )

        self.payment_plans[plan.plan_id] = plan

        # Update patient balance
        balance = self.patient_balances.get(patient_id)
        if balance:
            balance.has_active_payment_plan = True
            balance.payment_plan_id = plan.plan_id
            balance.collection_status = CollectionStatus.PAYMENT_PLAN

        return plan

    def _calculate_next_payment_date(self, day: int) -> datetime:
        """Calculate next payment date"""
        today = datetime.utcnow()
        if today.day < day:
            return today.replace(day=day)
        else:
            # Next month
            if today.month == 12:
                return today.replace(year=today.year + 1, month=1, day=day)
            else:
                return today.replace(month=today.month + 1, day=day)

    async def process_payment_plan_payment(
        self,
        plan_id: str,
        amount: Decimal,
        payment_method: str
    ) -> tuple[PaymentPlan, PaymentRecord]:
        """Process a payment plan payment"""
        plan = self.payment_plans.get(plan_id)
        if not plan:
            raise ValueError(f"Payment plan not found: {plan_id}")

        # Create payment
        payment = await self.post_patient_payment(
            tenant_id=plan.tenant_id,
            patient_id=plan.patient_id,
            amount=amount,
            payment_method=payment_method,
            notes=f"Payment plan: {plan_id}"
        )

        # Update plan
        plan.remaining_balance -= amount
        plan.payments_made += 1
        plan.next_payment_date = self._calculate_next_payment_date(plan.payment_day)
        plan.status = PaymentPlanStatus.CURRENT

        if plan.remaining_balance <= 0:
            plan.status = PaymentPlanStatus.COMPLETED

        return plan, payment

    async def run_collection_workflow(
        self,
        tenant_id: str
    ) -> list[CollectionAction]:
        """Run automated collection workflow"""
        actions = []
        today = datetime.utcnow()

        for patient_id, balance in self.patient_balances.items():
            if balance.tenant_id != tenant_id:
                continue
            if balance.current_balance <= 0:
                continue
            if balance.has_active_payment_plan:
                continue

            action = None

            # Determine collection action based on aging
            if balance.balance_over_90 > 0:
                if balance.collection_status != CollectionStatus.COLLECTIONS:
                    action = CollectionAction(
                        action_id=str(uuid4()),
                        patient_id=patient_id,
                        action_type="collections_referral",
                        action_date=today,
                        amount=balance.balance_over_90,
                        notes="Referred to collections agency"
                    )
                    balance.collection_status = CollectionStatus.COLLECTIONS
            elif balance.balance_61_90 > 0:
                if balance.collection_status not in [CollectionStatus.PAST_DUE_90, CollectionStatus.COLLECTIONS]:
                    action = CollectionAction(
                        action_id=str(uuid4()),
                        patient_id=patient_id,
                        action_type="final_notice",
                        action_date=today,
                        amount=balance.balance_61_90,
                        notes="Final notice before collections"
                    )
                    balance.collection_status = CollectionStatus.PAST_DUE_90
            elif balance.balance_31_60 > 0:
                if balance.collection_status not in [CollectionStatus.PAST_DUE_60, CollectionStatus.PAST_DUE_90, CollectionStatus.COLLECTIONS]:
                    action = CollectionAction(
                        action_id=str(uuid4()),
                        patient_id=patient_id,
                        action_type="reminder_letter",
                        action_date=today,
                        amount=balance.balance_31_60,
                        notes="Second reminder notice"
                    )
                    balance.collection_status = CollectionStatus.PAST_DUE_60
            elif balance.balance_0_30 > 0:
                # Check if statement needed
                days_since_statement = 30
                if balance.last_statement_date:
                    days_since_statement = (today - balance.last_statement_date).days

                if days_since_statement >= 30:
                    action = CollectionAction(
                        action_id=str(uuid4()),
                        patient_id=patient_id,
                        action_type="statement",
                        action_date=today,
                        amount=balance.current_balance,
                        notes="Monthly statement"
                    )
                    balance.last_statement_date = today
                    balance.collection_status = CollectionStatus.REMINDER_SENT

            if action:
                self.collection_actions[action.action_id] = action
                actions.append(action)

        return actions

    async def get_denial_analytics(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> dict[str, Any]:
        """Get denial analytics for a period"""
        denials = [
            d for d in self.denials.values()
            if start_date <= d.received_date <= end_date
        ]

        by_category = {}
        for d in denials:
            cat = d.category.value
            if cat not in by_category:
                by_category[cat] = {"count": 0, "amount": Decimal("0")}
            by_category[cat]["count"] += 1
            by_category[cat]["amount"] += d.amount_denied

        total_denied = sum(d.amount_denied for d in denials)
        total_appealed = sum(1 for d in denials if d.appeal_id)

        return {
            "total_denials": len(denials),
            "total_denied_amount": float(total_denied),
            "total_appealed": total_appealed,
            "appeal_rate": total_appealed / len(denials) if denials else 0,
            "by_category": {
                k: {"count": v["count"], "amount": float(v["amount"])}
                for k, v in by_category.items()
            }
        }

    async def get_ar_aging(
        self,
        tenant_id: str
    ) -> dict[str, Any]:
        """Get accounts receivable aging summary"""
        balances = [b for b in self.patient_balances.values() if b.tenant_id == tenant_id]

        return {
            "total_ar": float(sum(b.current_balance for b in balances)),
            "aging_0_30": float(sum(b.balance_0_30 for b in balances)),
            "aging_31_60": float(sum(b.balance_31_60 for b in balances)),
            "aging_61_90": float(sum(b.balance_61_90 for b in balances)),
            "aging_over_90": float(sum(b.balance_over_90 for b in balances)),
            "accounts_count": len(balances),
            "with_payment_plans": sum(1 for b in balances if b.has_active_payment_plan),
            "in_collections": sum(1 for b in balances if b.collection_status == CollectionStatus.COLLECTIONS)
        }


# Singleton instance
_revenue_automation: Optional[RevenueCycleAutomation] = None


def get_revenue_automation() -> RevenueCycleAutomation:
    """Get singleton revenue automation instance"""
    global _revenue_automation
    if _revenue_automation is None:
        _revenue_automation = RevenueCycleAutomation()
    return _revenue_automation
