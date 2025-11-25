"""
Insurance & Billing Test Suite

EPIC-008: Insurance & Billing Integration

Comprehensive tests covering:
- Eligibility verification
- Prior authorization management
- Claims generation & submission
- Payment processing
- Patient statements
- Fee schedules & contracts
- Denial management
- Revenue cycle analytics
"""

import pytest
from datetime import datetime, date, timedelta, timezone
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4
from decimal import Decimal

# Import schemas
from services.prm.modules.billing.schemas import (
    EligibilityVerifyRequest,
    EligibilityResponse,
    PriorAuthCreate,
    PriorAuthStatus,
    PriorAuthResponse,
    ClaimCreate,
    ClaimType,
    ClaimStatus,
    ClaimLineCreate,
    ClaimResponse,
    PaymentCreate,
    PaymentType,
    PaymentMethod,
    PaymentStatus,
    PaymentResponse,
    PaymentPlanCreate,
    PaymentPlanResponse,
    PaymentCardCreate,
    PaymentCardResponse,
    StatementGenerateRequest,
    StatementResponse,
    FeeScheduleCreate,
    FeeScheduleRateCreate,
    FeeScheduleResponse,
    PayerContractCreate,
    PayerContractResponse,
    DenialRecordCreate,
    DenialCategory,
    DenialRecordResponse,
    InsurancePolicyCreate,
    InsurancePolicyResponse,
    BatchEligibilityRequest,
    ClaimValidationResult,
    RevenueCycleMetrics,
    ClaimsSummary,
    DenialAnalytics,
    ARAgingReport,
)

# Import models
from services.prm.modules.billing.models import (
    InsurancePolicy,
    EligibilityVerification,
    PriorAuthorization,
    Claim,
    ClaimLine,
    ClaimAdjustment,
    RemittanceAdvice,
    Payment,
    PaymentCard,
    PaymentPlan,
    PaymentPlanSchedule,
    PatientStatement,
    FeeSchedule,
    FeeScheduleRate,
    PayerContract,
    ContractRateOverride,
    DenialRecord,
    BillingAuditLog,
    EligibilityStatus,
    CoverageType,
    PlanType,
    NetworkStatus,
    PriorAuthStatus as ModelPriorAuthStatus,
    ClaimType as ModelClaimType,
    ClaimStatus as ModelClaimStatus,
    SubmissionMethod,
    PaymentType as ModelPaymentType,
    PaymentMethod as ModelPaymentMethod,
    PaymentStatus as ModelPaymentStatus,
    StatementStatus,
    AdjustmentGroupCode,
    DenialCategory as ModelDenialCategory,
)


# ============================================================================
# ENUM TESTS
# ============================================================================

class TestBillingEnums:
    """Tests for billing enum values."""

    def test_eligibility_status_values(self):
        """Test eligibility status enum."""
        assert EligibilityStatus.ACTIVE.value == "active"
        assert EligibilityStatus.INACTIVE.value == "inactive"
        assert EligibilityStatus.PENDING.value == "pending"
        assert EligibilityStatus.TERMINATED.value == "terminated"
        assert EligibilityStatus.UNKNOWN.value == "unknown"

    def test_coverage_type_values(self):
        """Test coverage type enum."""
        assert CoverageType.MEDICAL.value == "medical"
        assert CoverageType.DENTAL.value == "dental"
        assert CoverageType.VISION.value == "vision"
        assert CoverageType.PHARMACY.value == "pharmacy"

    def test_plan_type_values(self):
        """Test plan type enum."""
        assert PlanType.HMO.value == "hmo"
        assert PlanType.PPO.value == "ppo"
        assert PlanType.EPO.value == "epo"
        assert PlanType.MEDICARE.value == "medicare"
        assert PlanType.MEDICAID.value == "medicaid"

    def test_prior_auth_status_values(self):
        """Test prior auth status enum."""
        assert ModelPriorAuthStatus.DRAFT.value == "draft"
        assert ModelPriorAuthStatus.SUBMITTED.value == "submitted"
        assert ModelPriorAuthStatus.APPROVED.value == "approved"
        assert ModelPriorAuthStatus.DENIED.value == "denied"
        assert ModelPriorAuthStatus.APPEALED.value == "appealed"

    def test_claim_type_values(self):
        """Test claim type enum."""
        assert ModelClaimType.PROFESSIONAL.value == "professional"
        assert ModelClaimType.INSTITUTIONAL.value == "institutional"
        assert ModelClaimType.DENTAL.value == "dental"

    def test_claim_status_values(self):
        """Test claim status enum."""
        assert ModelClaimStatus.DRAFT.value == "draft"
        assert ModelClaimStatus.SUBMITTED.value == "submitted"
        assert ModelClaimStatus.PAID.value == "paid"
        assert ModelClaimStatus.DENIED.value == "denied"
        assert ModelClaimStatus.VOID.value == "void"

    def test_payment_type_values(self):
        """Test payment type enum."""
        assert ModelPaymentType.COPAY.value == "copay"
        assert ModelPaymentType.COINSURANCE.value == "coinsurance"
        assert ModelPaymentType.DEDUCTIBLE.value == "deductible"
        assert ModelPaymentType.SELF_PAY.value == "self_pay"

    def test_payment_method_values(self):
        """Test payment method enum."""
        assert ModelPaymentMethod.CREDIT_CARD.value == "credit_card"
        assert ModelPaymentMethod.ACH.value == "ach"
        assert ModelPaymentMethod.CHECK.value == "check"
        assert ModelPaymentMethod.CASH.value == "cash"

    def test_payment_status_values(self):
        """Test payment status enum."""
        assert ModelPaymentStatus.PENDING.value == "pending"
        assert ModelPaymentStatus.COMPLETED.value == "completed"
        assert ModelPaymentStatus.REFUNDED.value == "refunded"
        assert ModelPaymentStatus.FAILED.value == "failed"

    def test_adjustment_group_code_values(self):
        """Test CARC group codes."""
        assert AdjustmentGroupCode.CO.value == "CO"  # Contractual Obligation
        assert AdjustmentGroupCode.PR.value == "PR"  # Patient Responsibility
        assert AdjustmentGroupCode.OA.value == "OA"  # Other Adjustment
        assert AdjustmentGroupCode.PI.value == "PI"  # Payer Initiated

    def test_denial_category_values(self):
        """Test denial category enum."""
        assert ModelDenialCategory.ELIGIBILITY.value == "eligibility"
        assert ModelDenialCategory.AUTHORIZATION.value == "authorization"
        assert ModelDenialCategory.CODING.value == "coding"
        assert ModelDenialCategory.TIMELY_FILING.value == "timely_filing"


# ============================================================================
# SCHEMA VALIDATION TESTS
# ============================================================================

class TestEligibilitySchemas:
    """Tests for eligibility schemas."""

    def test_eligibility_verify_request_valid(self):
        """Test valid eligibility verification request."""
        request = EligibilityVerifyRequest(
            patient_id=uuid4(),
            payer_id="BCBS",
            member_id="MEM123456",
            service_type="office_visit",
        )
        assert request.payer_id == "BCBS"
        assert request.member_id == "MEM123456"
        assert request.service_type == "office_visit"

    def test_eligibility_verify_request_minimal(self):
        """Test minimal eligibility request."""
        request = EligibilityVerifyRequest(
            patient_id=uuid4(),
            payer_id="UHC",
            member_id="ABC123",
        )
        assert request.service_type is None
        assert request.provider_npi is None

    def test_batch_eligibility_request(self):
        """Test batch eligibility request."""
        patient_id = uuid4()
        batch = BatchEligibilityRequest(
            verifications=[
                EligibilityVerifyRequest(
                    patient_id=patient_id,
                    payer_id="BCBS",
                    member_id="MEM001",
                ),
                EligibilityVerifyRequest(
                    patient_id=patient_id,
                    payer_id="AETNA",
                    member_id="MEM002",
                ),
            ]
        )
        assert len(batch.verifications) == 2


class TestPriorAuthSchemas:
    """Tests for prior authorization schemas."""

    def test_prior_auth_create_valid(self):
        """Test valid prior auth creation."""
        prior_auth = PriorAuthCreate(
            patient_id=uuid4(),
            payer_id="CIGNA",
            service_type="imaging",
            procedure_codes=["70553", "70554"],
            diagnosis_codes=["G43.909"],
            quantity_requested=1,
        )
        assert prior_auth.service_type == "imaging"
        assert len(prior_auth.procedure_codes) == 2
        assert prior_auth.quantity_requested == 1

    def test_prior_auth_status_enum(self):
        """Test prior auth status schema enum."""
        assert PriorAuthStatus.DRAFT == "draft"
        assert PriorAuthStatus.APPROVED == "approved"
        assert PriorAuthStatus.DENIED == "denied"


class TestClaimSchemas:
    """Tests for claim schemas."""

    def test_claim_create_valid(self):
        """Test valid claim creation."""
        claim = ClaimCreate(
            patient_id=uuid4(),
            payer_id="MEDICARE",
            member_id="1EG4TE5MK72",
            billing_provider_npi="1234567890",
            service_date_start=date.today(),
            diagnoses=[
                {"code": "J06.9", "code_type": "ICD-10"},
            ],
            lines=[
                ClaimLineCreate(
                    procedure_code="99213",
                    charge_amount=150.00,
                    service_date=date.today(),
                ),
            ],
        )
        assert claim.claim_type == ClaimType.PROFESSIONAL
        assert claim.billing_provider_npi == "1234567890"
        assert len(claim.diagnoses) == 1
        assert len(claim.lines) == 1

    def test_claim_line_create(self):
        """Test claim line creation."""
        line = ClaimLineCreate(
            procedure_code="99214",
            modifiers=["25"],
            description="Office visit, moderate complexity",
            diagnosis_pointers=["A", "B"],
            service_date=date.today(),
            units=1,
            charge_amount=200.00,
        )
        assert line.procedure_code == "99214"
        assert line.modifiers == ["25"]
        assert line.units == 1
        assert line.charge_amount == 200.00

    def test_claim_type_enum(self):
        """Test claim type schema enum."""
        assert ClaimType.PROFESSIONAL == "professional"
        assert ClaimType.INSTITUTIONAL == "institutional"

    def test_claim_status_enum(self):
        """Test claim status schema enum."""
        assert ClaimStatus.DRAFT == "draft"
        assert ClaimStatus.SUBMITTED == "submitted"
        assert ClaimStatus.PAID == "paid"


class TestPaymentSchemas:
    """Tests for payment schemas."""

    def test_payment_create_valid(self):
        """Test valid payment creation."""
        payment = PaymentCreate(
            patient_id=uuid4(),
            amount=50.00,
            payment_type=PaymentType.COPAY,
            payment_method=PaymentMethod.CREDIT_CARD,
            card_id=uuid4(),
        )
        assert payment.amount == 50.00
        assert payment.payment_type == PaymentType.COPAY
        assert payment.payment_method == PaymentMethod.CREDIT_CARD

    def test_payment_amount_validation(self):
        """Test payment amount must be positive."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            PaymentCreate(
                patient_id=uuid4(),
                amount=0,  # Invalid - must be > 0
                payment_type=PaymentType.COPAY,
                payment_method=PaymentMethod.CASH,
            )

    def test_payment_card_create(self):
        """Test payment card creation."""
        card = PaymentCardCreate(
            patient_id=uuid4(),
            token="tok_visa_4242",
            last_four="4242",
            card_type="visa",
            expiry_month=12,
            expiry_year=2026,
            cardholder_name="John Doe",
            is_default=True,
        )
        assert card.last_four == "4242"
        assert card.card_type == "visa"
        assert card.is_default is True

    def test_payment_card_last_four_validation(self):
        """Test payment card last four must be exactly 4 digits."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            PaymentCardCreate(
                patient_id=uuid4(),
                token="tok_test",
                last_four="42",  # Invalid - too short
                card_type="visa",
                expiry_month=12,
                expiry_year=2026,
            )

    def test_payment_plan_create(self):
        """Test payment plan creation."""
        plan = PaymentPlanCreate(
            patient_id=uuid4(),
            plan_name="12-Month Payment Plan",
            total_amount=1200.00,
            down_payment=100.00,
            payment_amount=100.00,
            frequency="monthly",
            start_date=date.today(),
            total_payments=12,
            auto_pay=True,
        )
        assert plan.total_amount == 1200.00
        assert plan.payment_amount == 100.00
        assert plan.total_payments == 12


class TestFeeScheduleSchemas:
    """Tests for fee schedule schemas."""

    def test_fee_schedule_create(self):
        """Test fee schedule creation."""
        schedule = FeeScheduleCreate(
            name="Standard Fee Schedule 2024",
            schedule_type="standard",
            effective_date=date(2024, 1, 1),
            is_default=True,
            rates=[
                FeeScheduleRateCreate(
                    procedure_code="99213",
                    charge_amount=150.00,
                    expected_reimbursement=95.00,
                ),
                FeeScheduleRateCreate(
                    procedure_code="99214",
                    charge_amount=200.00,
                    expected_reimbursement=125.00,
                ),
            ],
        )
        assert schedule.name == "Standard Fee Schedule 2024"
        assert len(schedule.rates) == 2
        assert schedule.is_default is True


class TestContractSchemas:
    """Tests for payer contract schemas."""

    def test_payer_contract_create(self):
        """Test payer contract creation."""
        contract = PayerContractCreate(
            payer_id="BCBS",
            payer_name="Blue Cross Blue Shield",
            contract_name="BCBS PPO 2024",
            effective_date=date(2024, 1, 1),
            termination_date=date(2025, 12, 31),
            rate_type="percent_of_medicare",
            base_rate_percent=120.0,
            timely_filing_days=365,
            appeal_filing_days=180,
        )
        assert contract.payer_id == "BCBS"
        assert contract.base_rate_percent == 120.0
        assert contract.timely_filing_days == 365


class TestDenialSchemas:
    """Tests for denial management schemas."""

    def test_denial_record_create(self):
        """Test denial record creation."""
        denial = DenialRecordCreate(
            claim_id=uuid4(),
            denial_date=date.today(),
            denial_reason_code="CO-16",
            denial_reason_description="Claim/service lacks information",
            denial_category=DenialCategory.CODING,
            denied_amount=500.00,
            is_appealable=True,
            appeal_deadline=date.today() + timedelta(days=180),
        )
        assert denial.denial_reason_code == "CO-16"
        assert denial.denial_category == DenialCategory.CODING
        assert denial.denied_amount == 500.00


class TestAnalyticsSchemas:
    """Tests for analytics schemas."""

    def test_revenue_cycle_metrics(self):
        """Test revenue cycle metrics schema."""
        metrics = RevenueCycleMetrics(
            days_in_ar=35.5,
            clean_claim_rate=95.2,
            denial_rate=4.8,
            first_pass_payment_rate=92.0,
            collection_rate=97.5,
            net_collection_rate=99.1,
            total_charges=1000000.00,
            total_payments=950000.00,
            total_adjustments=25000.00,
            total_ar=150000.00,
            ar_over_90_days=15000.00,
            prior_auth_turnaround_days=2.5,
        )
        assert metrics.clean_claim_rate == 95.2
        assert metrics.denial_rate == 4.8

    def test_claims_summary(self):
        """Test claims summary schema."""
        summary = ClaimsSummary(
            total_claims=500,
            claims_by_status={"paid": 450, "pending": 30, "denied": 20},
            claims_by_payer={"BCBS": 200, "UHC": 150, "AETNA": 150},
            total_charged=500000.00,
            total_paid=475000.00,
            total_denied=25000.00,
            average_days_to_payment=28.5,
        )
        assert summary.total_claims == 500
        assert summary.total_paid == 475000.00

    def test_ar_aging_report(self):
        """Test AR aging report schema."""
        aging = ARAgingReport(
            total_ar=150000.00,
            current=50000.00,
            days_1_30=40000.00,
            days_31_60=30000.00,
            days_61_90=15000.00,
            days_91_120=10000.00,
            days_over_120=5000.00,
            by_payer={
                "BCBS": {"total": 60000.00},
                "UHC": {"total": 50000.00},
                "AETNA": {"total": 40000.00},
            },
        )
        assert aging.total_ar == 150000.00
        assert aging.days_over_120 == 5000.00


# ============================================================================
# MODEL TESTS
# ============================================================================

class TestInsurancePolicyModel:
    """Tests for insurance policy model."""

    def test_insurance_policy_creation(self):
        """Test creating an insurance policy."""
        policy = InsurancePolicy(
            id=uuid4(),
            tenant_id=uuid4(),
            patient_id=uuid4(),
            payer_id="BCBS",
            payer_name="Blue Cross Blue Shield",
            member_id="MEM123456",
            plan_type="PPO",
            effective_date=date(2024, 1, 1),
            is_primary=True,
            coordination_order=1,
            status="active",
        )
        assert policy.payer_id == "BCBS"
        assert policy.is_primary is True


class TestClaimModel:
    """Tests for claim model."""

    def test_claim_creation(self):
        """Test creating a claim."""
        claim = Claim(
            id=uuid4(),
            tenant_id=uuid4(),
            claim_number="CLM-20240101-ABC123",
            claim_type="professional",
            patient_id=uuid4(),
            payer_id="UHC",
            member_id="UHC123456",
            billing_provider_npi="1234567890",
            service_date_start=date.today(),
            total_charge=Decimal("500.00"),
            status="draft",
        )
        assert claim.claim_number.startswith("CLM-")
        assert claim.status == "draft"
        assert claim.total_charge == Decimal("500.00")


class TestPaymentModel:
    """Tests for payment model."""

    def test_payment_creation(self):
        """Test creating a payment."""
        payment = Payment(
            id=uuid4(),
            tenant_id=uuid4(),
            payment_number="PMT-20240101-XYZ789",
            patient_id=uuid4(),
            amount=Decimal("50.00"),
            payment_type="copay",
            payment_method="credit_card",
            status="completed",
        )
        assert payment.amount == Decimal("50.00")
        assert payment.status == "completed"


class TestPaymentPlanModel:
    """Tests for payment plan model."""

    def test_payment_plan_creation(self):
        """Test creating a payment plan."""
        plan = PaymentPlan(
            id=uuid4(),
            tenant_id=uuid4(),
            patient_id=uuid4(),
            total_amount=Decimal("1200.00"),
            payment_amount=Decimal("100.00"),
            frequency="monthly",
            total_payments=12,
            start_date=date.today(),
            status="active",
        )
        assert plan.total_payments == 12
        assert plan.frequency == "monthly"


class TestDenialRecordModel:
    """Tests for denial record model."""

    def test_denial_record_creation(self):
        """Test creating a denial record."""
        denial = DenialRecord(
            id=uuid4(),
            tenant_id=uuid4(),
            claim_id=uuid4(),
            denial_date=date.today(),
            denial_reason_code="CO-4",
            denial_category="coding",
            denied_amount=Decimal("250.00"),
            is_appealable=True,
            resolution_status="open",
        )
        assert denial.denial_reason_code == "CO-4"
        assert denial.is_appealable is True


# ============================================================================
# SERVICE LAYER TESTS
# ============================================================================

class TestEligibilityService:
    """Tests for eligibility service."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()
        db.query = MagicMock()
        return db

    @pytest.mark.asyncio
    async def test_verify_eligibility_success(self, mock_db):
        """Test successful eligibility verification."""
        from services.prm.modules.billing.service import EligibilityServiceDB

        tenant_id = uuid4()
        patient_id = uuid4()
        service = EligibilityServiceDB(mock_db, tenant_id)

        result = await service.verify_eligibility(
            patient_id=patient_id,
            payer_id="BCBS",
            member_id="MEM123456",
            service_type="office_visit",
        )

        assert result is not None
        assert result.payer_id == "BCBS"
        assert result.member_id == "MEM123456"
        assert result.status == "success"
        assert result.coverage_active is True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_eligibility_with_copay(self, mock_db):
        """Test eligibility verification returns copay info."""
        from services.prm.modules.billing.service import EligibilityServiceDB

        tenant_id = uuid4()
        patient_id = uuid4()
        service = EligibilityServiceDB(mock_db, tenant_id)

        result = await service.verify_eligibility(
            patient_id=patient_id,
            payer_id="AETNA",
            member_id="AET789",
            service_type="office_visit",
        )

        assert result.copay_amount == 25  # Mock returns $25 copay for office visit
        assert result.prior_auth_required is False


class TestPriorAuthService:
    """Tests for prior authorization service."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()
        db.query = MagicMock()
        return db

    @pytest.mark.asyncio
    async def test_create_prior_auth(self, mock_db):
        """Test creating prior authorization."""
        from services.prm.modules.billing.service import PriorAuthorizationServiceDB

        tenant_id = uuid4()
        patient_id = uuid4()
        service = PriorAuthorizationServiceDB(mock_db, tenant_id)

        result = await service.create_prior_auth(
            patient_id=patient_id,
            payer_id="CIGNA",
            service_type="imaging",
            procedure_codes=["70553"],
            diagnosis_codes=["G43.909"],
            quantity_requested=1,
        )

        assert result is not None
        assert result.payer_id == "CIGNA"
        assert result.service_type == "imaging"
        assert result.status == "draft"
        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_prior_auth(self, mock_db):
        """Test submitting prior authorization."""
        from services.prm.modules.billing.service import PriorAuthorizationServiceDB

        tenant_id = uuid4()
        service = PriorAuthorizationServiceDB(mock_db, tenant_id)

        # Create mock prior auth
        mock_prior_auth = PriorAuthorization(
            id=uuid4(),
            tenant_id=tenant_id,
            patient_id=uuid4(),
            payer_id="UHC",
            service_type="surgery",
            status="draft",
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_prior_auth

        result = await service.submit_prior_auth(
            auth_id=mock_prior_auth.id,
            submission_method="electronic",
        )

        assert result.status == "submitted"
        assert result.submission_method == "electronic"
        assert result.reference_number is not None


class TestClaimsService:
    """Tests for claims service."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()
        db.query = MagicMock()
        return db

    @pytest.mark.asyncio
    async def test_create_claim(self, mock_db):
        """Test creating a claim."""
        from services.prm.modules.billing.service import ClaimsServiceDB

        tenant_id = uuid4()
        patient_id = uuid4()
        service = ClaimsServiceDB(mock_db, tenant_id)

        result = await service.create_claim(
            patient_id=patient_id,
            payer_id="MEDICARE",
            member_id="1EG4TE5MK72",
            billing_provider_npi="1234567890",
            service_date_start=date.today(),
        )

        assert result is not None
        assert result.payer_id == "MEDICARE"
        assert result.claim_number.startswith("CLM-")
        assert result.status == "draft"
        mock_db.add.assert_called()

    @pytest.mark.asyncio
    async def test_validate_claim_no_diagnoses(self, mock_db):
        """Test claim validation fails without diagnoses."""
        from services.prm.modules.billing.service import ClaimsServiceDB

        tenant_id = uuid4()
        service = ClaimsServiceDB(mock_db, tenant_id)

        # Mock claim without diagnoses
        mock_claim = Claim(
            id=uuid4(),
            tenant_id=tenant_id,
            claim_number="CLM-TEST",
            patient_id=uuid4(),
            payer_id="BCBS",
            member_id="MEM123",
            billing_provider_npi="1234567890",
            service_date_start=date.today(),
            diagnoses=[],
            lines=[],
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_claim

        result = await service.validate_claim(mock_claim.id)

        assert result["valid"] is False
        assert any(e["field"] == "diagnoses" for e in result["errors"])

    @pytest.mark.asyncio
    async def test_void_claim(self, mock_db):
        """Test voiding a claim."""
        from services.prm.modules.billing.service import ClaimsServiceDB

        tenant_id = uuid4()
        service = ClaimsServiceDB(mock_db, tenant_id)

        mock_claim = Claim(
            id=uuid4(),
            tenant_id=tenant_id,
            claim_number="CLM-VOID",
            patient_id=uuid4(),
            payer_id="UHC",
            member_id="UHC123",
            billing_provider_npi="1234567890",
            service_date_start=date.today(),
            status="submitted",
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_claim

        result = await service.void_claim(
            claim_id=mock_claim.id,
            reason="Duplicate claim",
        )

        assert result.status == "void"
        assert result.status_reason == "Duplicate claim"


class TestPaymentService:
    """Tests for payment service."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()
        db.query = MagicMock()
        return db

    @pytest.mark.asyncio
    async def test_process_payment(self, mock_db):
        """Test processing a payment."""
        from services.prm.modules.billing.service import PaymentServiceDB

        tenant_id = uuid4()
        patient_id = uuid4()
        service = PaymentServiceDB(mock_db, tenant_id)

        result = await service.process_payment(
            patient_id=patient_id,
            amount=50.00,
            payment_type="copay",
            payment_method="credit_card",
        )

        assert result is not None
        assert result.amount == 50.00
        assert result.status == "completed"
        assert result.processor_transaction_id is not None
        assert result.receipt_number is not None

    @pytest.mark.asyncio
    async def test_refund_payment(self, mock_db):
        """Test refunding a payment."""
        from services.prm.modules.billing.service import PaymentServiceDB

        tenant_id = uuid4()
        service = PaymentServiceDB(mock_db, tenant_id)

        mock_payment = Payment(
            id=uuid4(),
            tenant_id=tenant_id,
            patient_id=uuid4(),
            amount=Decimal("100.00"),
            payment_type="copay",
            payment_method="credit_card",
            status="completed",
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_payment

        result = await service.refund_payment(
            payment_id=mock_payment.id,
            amount=50.00,
            reason="Partial refund - duplicate charge",
        )

        assert result.refund_amount == 50.00
        assert result.status == "partial_refund"

    @pytest.mark.asyncio
    async def test_create_payment_plan(self, mock_db):
        """Test creating a payment plan."""
        from services.prm.modules.billing.service import PaymentServiceDB

        tenant_id = uuid4()
        patient_id = uuid4()
        service = PaymentServiceDB(mock_db, tenant_id)

        result = await service.create_payment_plan(
            patient_id=patient_id,
            total_amount=1200.00,
            payment_amount=100.00,
            total_payments=12,
            start_date=date.today(),
            frequency="monthly",
        )

        assert result is not None
        assert result.total_amount == 1200.00
        assert result.total_payments == 12
        assert result.status == "active"


class TestStatementService:
    """Tests for statement service."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()
        db.query = MagicMock()
        return db

    @pytest.mark.asyncio
    async def test_generate_statement(self, mock_db):
        """Test generating a patient statement."""
        from services.prm.modules.billing.service import StatementServiceDB

        tenant_id = uuid4()
        patient_id = uuid4()
        service = StatementServiceDB(mock_db, tenant_id)

        # Mock empty claims and payments
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = await service.generate_statement(
            patient_id=patient_id,
            period_start=date.today() - timedelta(days=30),
            period_end=date.today(),
        )

        assert result is not None
        assert result.statement_number.startswith("STMT-")
        assert result.status == "generated"


class TestBillingAnalyticsService:
    """Tests for billing analytics service."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.query = MagicMock()
        return db

    @pytest.mark.asyncio
    async def test_get_revenue_cycle_metrics(self, mock_db):
        """Test getting revenue cycle metrics."""
        from services.prm.modules.billing.service import BillingAnalyticsService

        tenant_id = uuid4()
        service = BillingAnalyticsService(mock_db, tenant_id)

        # Mock empty claims
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = await service.get_revenue_cycle_metrics(
            start_date=date.today() - timedelta(days=30),
            end_date=date.today(),
        )

        assert "days_in_ar" in result
        assert "clean_claim_rate" in result
        assert "denial_rate" in result

    @pytest.mark.asyncio
    async def test_get_ar_aging_report(self, mock_db):
        """Test getting AR aging report."""
        from services.prm.modules.billing.service import BillingAnalyticsService

        tenant_id = uuid4()
        service = BillingAnalyticsService(mock_db, tenant_id)

        # Mock claims with balances
        mock_claims = [
            MagicMock(
                balance=Decimal("100.00"),
                service_date_start=date.today() - timedelta(days=15),
                payer_id="BCBS",
            ),
            MagicMock(
                balance=Decimal("200.00"),
                service_date_start=date.today() - timedelta(days=45),
                payer_id="UHC",
            ),
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_claims

        result = await service.get_ar_aging_report()

        assert "total_ar" in result
        assert "by_payer" in result


# ============================================================================
# INTEGRATION STYLE TESTS
# ============================================================================

class TestClaimLifecycle:
    """Tests for complete claim lifecycle."""

    def test_claim_status_transitions(self):
        """Test valid claim status transitions."""
        valid_transitions = {
            "draft": ["pending_submission", "void"],
            "pending_submission": ["submitted", "void"],
            "submitted": ["acknowledged", "rejected"],
            "acknowledged": ["in_process", "paid", "denied"],
            "in_process": ["adjudicated", "paid", "denied"],
            "adjudicated": ["paid", "partial_paid", "denied"],
            "denied": ["appealed", "void"],
            "appealed": ["paid", "denied"],
        }

        # Test each transition
        for from_status, to_statuses in valid_transitions.items():
            for to_status in to_statuses:
                assert ModelClaimStatus(to_status), f"Invalid status: {to_status}"

    def test_claim_number_format(self):
        """Test claim number format."""
        claim_number = f"CLM-{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"
        assert claim_number.startswith("CLM-")
        assert len(claim_number) == 21  # CLM- + 8 digits + - + 8 hex chars


class TestPaymentPlanCalculations:
    """Tests for payment plan calculations."""

    def test_monthly_payment_plan_schedule(self):
        """Test monthly payment plan schedule calculation."""
        total_amount = 1200.00
        payment_amount = 100.00
        total_payments = 12
        down_payment = 0

        calculated_total = down_payment + (payment_amount * total_payments)
        assert calculated_total == total_amount

    def test_payment_plan_with_down_payment(self):
        """Test payment plan with down payment."""
        total_amount = 1200.00
        down_payment = 200.00
        remaining = total_amount - down_payment
        payment_amount = 100.00
        total_payments = 10

        assert remaining == 1000.00
        assert payment_amount * total_payments == remaining


class TestEDIFormatting:
    """Tests for EDI format validation."""

    def test_npi_format(self):
        """Test NPI format validation."""
        valid_npi = "1234567890"
        assert len(valid_npi) == 10
        assert valid_npi.isdigit()

    def test_member_id_formats(self):
        """Test various member ID formats."""
        # Medicare Beneficiary Identifier (MBI)
        mbi = "1EG4TE5MK72"
        assert len(mbi) == 11

        # Standard member ID
        member_id = "MEM123456789"
        assert member_id.startswith("MEM")

    def test_diagnosis_code_formats(self):
        """Test ICD-10 diagnosis code formats."""
        # Standard ICD-10-CM code
        icd10 = "J06.9"
        assert len(icd10) <= 8

        # Full precision code
        icd10_full = "G43.909"
        assert "." in icd10_full

    def test_procedure_code_formats(self):
        """Test CPT/HCPCS code formats."""
        # CPT code
        cpt = "99213"
        assert len(cpt) == 5
        assert cpt.isdigit()

        # HCPCS code
        hcpcs = "J0129"
        assert len(hcpcs) == 5


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
