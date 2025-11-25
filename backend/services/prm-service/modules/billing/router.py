"""
Insurance & Billing API Router

FastAPI endpoints for billing operations:
- Eligibility verification (US-008.1)
- Prior authorization (US-008.2)
- Claims management (US-008.3)
- Payment processing (US-008.4)
- Patient billing (US-008.5)
- Fee schedules (US-008.6)
- Contracts (US-008.7)
- Analytics (US-008.8)
- Compliance (US-008.9)

EPIC-008: Insurance & Billing Integration
"""

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session

from .schemas import (
    # Insurance Policy
    InsurancePolicyCreate, InsurancePolicyResponse,
    # Eligibility
    EligibilityVerifyRequest, EligibilityResponse, BatchEligibilityRequest,
    # Prior Authorization
    PriorAuthCreate, PriorAuthUpdate, PriorAuthResponse,
    PriorAuthSubmit, PriorAuthDecision,
    # Claims
    ClaimCreate, ClaimResponse, ClaimLineCreate, DiagnosisCreate,
    ClaimValidationResult, ClaimSubmitRequest, ClaimAdjustmentCreate,
    # Remittance
    RemittanceCreate, RemittanceResponse,
    # Payments
    PaymentCreate, PaymentResponse, PaymentRefundRequest,
    PaymentCardCreate, PaymentCardResponse,
    PaymentPlanCreate, PaymentPlanResponse, PaymentPlanSignRequest,
    # Statements
    StatementGenerateRequest, StatementResponse, StatementSendRequest,
    # Fee Schedules
    FeeScheduleCreate, FeeScheduleResponse, FeeScheduleBulkUpdateRequest,
    # Contracts
    PayerContractCreate, PayerContractResponse,
    # Denials
    DenialRecordCreate, DenialRecordResponse, DenialAppealRequest, DenialResolveRequest,
    # Analytics
    RevenueCycleMetrics, ClaimsSummary, DenialAnalytics, ARAgingReport,
    # Common
    PaginatedResponse,
)
from .service import (
    EligibilityServiceDB,
    PriorAuthorizationServiceDB,
    ClaimsServiceDB,
    PaymentServiceDB,
    StatementServiceDB,
    BillingAnalyticsService,
)
from .models import (
    InsurancePolicy, FeeSchedule, FeeScheduleRate,
    PayerContract, ContractRateOverride, DenialRecord,
)

router = APIRouter(prefix="/billing", tags=["Billing & Insurance"])


# Dependency to get database session (placeholder)
def get_db():
    """Get database session - to be implemented with actual DB."""
    # In production, this would yield a real database session
    pass


def get_tenant_id(x_tenant_id: str = Header(...)) -> UUID:
    """Extract tenant ID from header."""
    return UUID(x_tenant_id)


# ============================================================================
# INSURANCE POLICY ENDPOINTS
# ============================================================================

@router.post("/policies", response_model=InsurancePolicyResponse, status_code=201)
async def create_insurance_policy(
    data: InsurancePolicyCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Create a new insurance policy for a patient."""
    from uuid import uuid4

    policy = InsurancePolicy(
        id=uuid4(),
        tenant_id=tenant_id,
        patient_id=data.patient_id,
        payer_id=data.payer_id,
        payer_name=data.payer_name,
        member_id=data.member_id,
        plan_name=data.plan_name,
        plan_type=data.plan_type,
        group_number=data.group_number,
        group_name=data.group_name,
        subscriber_id=data.subscriber_id,
        subscriber_name=data.subscriber_name,
        relationship_to_subscriber=data.relationship_to_subscriber,
        effective_date=data.effective_date,
        termination_date=data.termination_date,
        coverage_types=data.coverage_types,
        is_primary=data.is_primary,
        coordination_order=data.coordination_order,
        status="active",
    )

    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


@router.get("/policies/{policy_id}", response_model=InsurancePolicyResponse)
async def get_insurance_policy(
    policy_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get insurance policy by ID."""
    policy = db.query(InsurancePolicy).filter(
        InsurancePolicy.id == policy_id,
        InsurancePolicy.tenant_id == tenant_id,
    ).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.get("/patients/{patient_id}/policies", response_model=List[InsurancePolicyResponse])
async def get_patient_policies(
    patient_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get all insurance policies for a patient."""
    policies = db.query(InsurancePolicy).filter(
        InsurancePolicy.tenant_id == tenant_id,
        InsurancePolicy.patient_id == patient_id,
    ).order_by(InsurancePolicy.coordination_order).all()
    return policies


# ============================================================================
# ELIGIBILITY VERIFICATION ENDPOINTS
# ============================================================================

@router.post("/eligibility/verify", response_model=EligibilityResponse)
async def verify_eligibility(
    data: EligibilityVerifyRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Verify patient insurance eligibility in real-time."""
    service = EligibilityServiceDB(db, tenant_id)
    verification = await service.verify_eligibility(
        patient_id=data.patient_id,
        payer_id=data.payer_id,
        member_id=data.member_id,
        service_type=data.service_type,
        service_date=data.service_date,
        provider_id=data.provider_id,
        provider_npi=data.provider_npi,
    )
    return verification


@router.post("/eligibility/batch", response_model=List[EligibilityResponse])
async def batch_verify_eligibility(
    data: BatchEligibilityRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Batch eligibility verification for multiple patients."""
    service = EligibilityServiceDB(db, tenant_id)
    results = await service.batch_verify([v.dict() for v in data.verifications])
    return results


@router.get("/eligibility/{verification_id}", response_model=EligibilityResponse)
async def get_eligibility_verification(
    verification_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get eligibility verification by ID."""
    service = EligibilityServiceDB(db, tenant_id)
    verification = await service.get_verification(verification_id)
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    return verification


@router.get("/patients/{patient_id}/eligibility", response_model=List[EligibilityResponse])
async def get_patient_eligibility_history(
    patient_id: UUID,
    limit: int = Query(10, le=100),
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get eligibility verification history for a patient."""
    service = EligibilityServiceDB(db, tenant_id)
    verifications = await service.get_patient_verifications(patient_id, limit)
    return verifications


# ============================================================================
# PRIOR AUTHORIZATION ENDPOINTS
# ============================================================================

@router.post("/prior-auth", response_model=PriorAuthResponse, status_code=201)
async def create_prior_authorization(
    data: PriorAuthCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Create a new prior authorization request."""
    service = PriorAuthorizationServiceDB(db, tenant_id)
    prior_auth = await service.create_prior_auth(
        patient_id=data.patient_id,
        payer_id=data.payer_id,
        service_type=data.service_type,
        procedure_codes=data.procedure_codes,
        diagnosis_codes=data.diagnosis_codes,
        quantity_requested=data.quantity_requested,
        **data.dict(exclude={"patient_id", "payer_id", "service_type", "procedure_codes", "diagnosis_codes", "quantity_requested"}),
    )
    return prior_auth


@router.get("/prior-auth/{auth_id}", response_model=PriorAuthResponse)
async def get_prior_authorization(
    auth_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get prior authorization by ID."""
    service = PriorAuthorizationServiceDB(db, tenant_id)
    prior_auth = await service.get_prior_auth(auth_id)
    if not prior_auth:
        raise HTTPException(status_code=404, detail="Prior authorization not found")
    return prior_auth


@router.put("/prior-auth/{auth_id}", response_model=PriorAuthResponse)
async def update_prior_authorization(
    auth_id: UUID,
    data: PriorAuthUpdate,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Update prior authorization."""
    service = PriorAuthorizationServiceDB(db, tenant_id)
    prior_auth = await service.update_prior_auth(
        auth_id,
        **data.dict(exclude_unset=True),
    )
    if not prior_auth:
        raise HTTPException(status_code=404, detail="Prior authorization not found")
    return prior_auth


@router.post("/prior-auth/{auth_id}/submit", response_model=PriorAuthResponse)
async def submit_prior_authorization(
    auth_id: UUID,
    data: PriorAuthSubmit,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Submit prior authorization to payer."""
    service = PriorAuthorizationServiceDB(db, tenant_id)
    prior_auth = await service.submit_prior_auth(
        auth_id,
        submission_method=data.submission_method,
    )
    if not prior_auth:
        raise HTTPException(status_code=404, detail="Prior authorization not found")
    return prior_auth


@router.post("/prior-auth/{auth_id}/decision", response_model=PriorAuthResponse)
async def record_prior_auth_decision(
    auth_id: UUID,
    data: PriorAuthDecision,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Record prior authorization decision from payer."""
    service = PriorAuthorizationServiceDB(db, tenant_id)
    prior_auth = await service.record_decision(
        auth_id,
        status=data.status.value,
        auth_number=data.auth_number,
        quantity_approved=data.quantity_approved,
        effective_date=data.effective_date,
        expiration_date=data.expiration_date,
        decision_reason=data.decision_reason,
        payer_notes=data.payer_notes,
    )
    if not prior_auth:
        raise HTTPException(status_code=404, detail="Prior authorization not found")
    return prior_auth


@router.post("/prior-auth/{auth_id}/appeal", response_model=PriorAuthResponse)
async def appeal_prior_authorization(
    auth_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Appeal a denied prior authorization."""
    service = PriorAuthorizationServiceDB(db, tenant_id)
    prior_auth = await service.appeal_prior_auth(auth_id)
    if not prior_auth:
        raise HTTPException(status_code=400, detail="Cannot appeal this authorization")
    return prior_auth


@router.get("/patients/{patient_id}/prior-auth", response_model=List[PriorAuthResponse])
async def get_patient_prior_authorizations(
    patient_id: UUID,
    status: Optional[str] = None,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get prior authorizations for a patient."""
    service = PriorAuthorizationServiceDB(db, tenant_id)
    auths = await service.get_patient_prior_auths(patient_id, status)
    return auths


@router.get("/prior-auth/expiring", response_model=List[PriorAuthResponse])
async def get_expiring_authorizations(
    days_ahead: int = Query(30, le=90),
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get prior authorizations expiring within specified days."""
    service = PriorAuthorizationServiceDB(db, tenant_id)
    auths = await service.get_expiring_auths(days_ahead)
    return auths


# ============================================================================
# CLAIMS ENDPOINTS
# ============================================================================

@router.post("/claims", response_model=ClaimResponse, status_code=201)
async def create_claim(
    data: ClaimCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Create a new insurance claim."""
    service = ClaimsServiceDB(db, tenant_id)
    claim = await service.create_claim(
        patient_id=data.patient_id,
        payer_id=data.payer_id,
        member_id=data.member_id,
        billing_provider_npi=data.billing_provider_npi,
        service_date_start=data.service_date_start,
        claim_type=data.claim_type.value,
        policy_id=data.policy_id,
        group_number=data.group_number,
        prior_auth_number=data.prior_auth_number,
        prior_auth_id=data.prior_auth_id,
        billing_provider_tax_id=data.billing_provider_tax_id,
        rendering_provider_npi=data.rendering_provider_npi,
        referring_provider_npi=data.referring_provider_npi,
        facility_npi=data.facility_npi,
        encounter_id=data.encounter_id,
        service_date_end=data.service_date_end,
        place_of_service=data.place_of_service,
        diagnoses=[d.dict() for d in data.diagnoses],
        lines=[l.dict() for l in data.lines],
    )
    return claim


@router.get("/claims/{claim_id}", response_model=ClaimResponse)
async def get_claim(
    claim_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get claim by ID."""
    service = ClaimsServiceDB(db, tenant_id)
    claim = await service.get_claim(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim


@router.post("/claims/{claim_id}/diagnoses", response_model=ClaimResponse)
async def add_diagnosis_to_claim(
    claim_id: UUID,
    data: DiagnosisCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Add diagnosis to claim."""
    service = ClaimsServiceDB(db, tenant_id)
    claim = await service.add_diagnosis(
        claim_id,
        code=data.code,
        code_type=data.code_type,
        sequence=data.sequence,
    )
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim


@router.post("/claims/{claim_id}/lines", response_model=ClaimResponse)
async def add_line_to_claim(
    claim_id: UUID,
    data: ClaimLineCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Add service line to claim."""
    service = ClaimsServiceDB(db, tenant_id)
    await service.add_claim_line(
        claim_id,
        procedure_code=data.procedure_code,
        charge_amount=data.charge_amount,
        service_date=data.service_date,
        modifiers=data.modifiers,
        description=data.description,
        diagnosis_pointers=data.diagnosis_pointers,
        place_of_service=data.place_of_service,
        units=data.units,
        rendering_provider_npi=data.rendering_provider_npi,
    )
    claim = await service.get_claim(claim_id)
    return claim


@router.post("/claims/{claim_id}/validate", response_model=ClaimValidationResult)
async def validate_claim(
    claim_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Validate claim for submission."""
    service = ClaimsServiceDB(db, tenant_id)
    result = await service.validate_claim(claim_id)
    return result


@router.post("/claims/{claim_id}/submit", response_model=ClaimResponse)
async def submit_claim(
    claim_id: UUID,
    data: ClaimSubmitRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Submit claim to payer."""
    service = ClaimsServiceDB(db, tenant_id)
    try:
        claim = await service.submit_claim(
            claim_id,
            submission_method=data.submission_method,
        )
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        return claim
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/claims/{claim_id}/void", response_model=ClaimResponse)
async def void_claim(
    claim_id: UUID,
    reason: str = Query(...),
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Void a claim."""
    service = ClaimsServiceDB(db, tenant_id)
    claim = await service.void_claim(claim_id, reason)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim


@router.get("/patients/{patient_id}/claims", response_model=List[ClaimResponse])
async def get_patient_claims(
    patient_id: UUID,
    status: Optional[str] = None,
    limit: int = Query(50, le=100),
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get claims for a patient."""
    service = ClaimsServiceDB(db, tenant_id)
    claims = await service.get_patient_claims(patient_id, status, limit)
    return claims


@router.get("/claims/pending", response_model=List[ClaimResponse])
async def get_pending_claims(
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get claims pending submission."""
    service = ClaimsServiceDB(db, tenant_id)
    claims = await service.get_pending_claims()
    return claims


# ============================================================================
# PAYMENT ENDPOINTS
# ============================================================================

@router.post("/payments", response_model=PaymentResponse, status_code=201)
async def process_payment(
    data: PaymentCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Process a patient payment."""
    service = PaymentServiceDB(db, tenant_id)
    payment = await service.process_payment(
        patient_id=data.patient_id,
        amount=data.amount,
        payment_type=data.payment_type.value,
        payment_method=data.payment_method.value,
        card_id=data.card_id,
        check_number=data.check_number,
        encounter_id=data.encounter_id,
        claim_id=data.claim_id,
        appointment_id=data.appointment_id,
        payment_plan_id=data.payment_plan_id,
        notes=data.notes,
    )
    return payment


@router.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get payment by ID."""
    service = PaymentServiceDB(db, tenant_id)
    payment = await service.get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.post("/payments/{payment_id}/refund", response_model=PaymentResponse)
async def refund_payment(
    payment_id: UUID,
    data: PaymentRefundRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Refund a payment."""
    service = PaymentServiceDB(db, tenant_id)
    try:
        payment = await service.refund_payment(
            payment_id,
            amount=data.amount,
            reason=data.reason,
        )
        if not payment:
            raise HTTPException(status_code=400, detail="Cannot refund this payment")
        return payment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/patients/{patient_id}/payments", response_model=List[PaymentResponse])
async def get_patient_payments(
    patient_id: UUID,
    limit: int = Query(50, le=100),
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get payments for a patient."""
    service = PaymentServiceDB(db, tenant_id)
    payments = await service.get_patient_payments(patient_id, limit)
    return payments


# ============================================================================
# PAYMENT CARD ENDPOINTS
# ============================================================================

@router.post("/cards", response_model=PaymentCardResponse, status_code=201)
async def store_payment_card(
    data: PaymentCardCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Store a payment card (tokenized)."""
    service = PaymentServiceDB(db, tenant_id)
    card = await service.store_card(
        patient_id=data.patient_id,
        token=data.token,
        last_four=data.last_four,
        card_type=data.card_type,
        expiry_month=data.expiry_month,
        expiry_year=data.expiry_year,
        cardholder_name=data.cardholder_name,
        billing_address=data.billing_address,
        is_default=data.is_default,
    )
    return card


@router.get("/patients/{patient_id}/cards", response_model=List[PaymentCardResponse])
async def get_patient_cards(
    patient_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get stored payment cards for a patient."""
    service = PaymentServiceDB(db, tenant_id)
    cards = await service.get_patient_cards(patient_id)
    return cards


@router.delete("/cards/{card_id}")
async def delete_payment_card(
    card_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Delete a stored payment card."""
    service = PaymentServiceDB(db, tenant_id)
    if not await service.delete_card(card_id):
        raise HTTPException(status_code=404, detail="Card not found")
    return {"status": "deleted"}


# ============================================================================
# PAYMENT PLAN ENDPOINTS
# ============================================================================

@router.post("/payment-plans", response_model=PaymentPlanResponse, status_code=201)
async def create_payment_plan(
    data: PaymentPlanCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Create a payment plan."""
    service = PaymentServiceDB(db, tenant_id)
    plan = await service.create_payment_plan(
        patient_id=data.patient_id,
        total_amount=data.total_amount,
        payment_amount=data.payment_amount,
        total_payments=data.total_payments,
        start_date=data.start_date,
        frequency=data.frequency,
        down_payment=data.down_payment,
        plan_name=data.plan_name,
        auto_pay=data.auto_pay,
        card_id=data.card_id,
        claim_ids=data.claim_ids,
        encounter_ids=data.encounter_ids,
    )
    return plan


@router.get("/patients/{patient_id}/payment-plans", response_model=List[PaymentPlanResponse])
async def get_patient_payment_plans(
    patient_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get payment plans for a patient."""
    service = PaymentServiceDB(db, tenant_id)
    plans = await service.get_patient_plans(patient_id)
    return plans


# ============================================================================
# PATIENT STATEMENT ENDPOINTS
# ============================================================================

@router.post("/statements/generate", response_model=StatementResponse)
async def generate_statement(
    data: StatementGenerateRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Generate a patient statement."""
    service = StatementServiceDB(db, tenant_id)
    statement = await service.generate_statement(
        patient_id=data.patient_id,
        period_start=data.period_start,
        period_end=data.period_end,
    )
    return statement


@router.post("/statements/{statement_id}/send", response_model=StatementResponse)
async def send_statement(
    statement_id: UUID,
    data: StatementSendRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Send statement to patient."""
    service = StatementServiceDB(db, tenant_id)
    statement = await service.send_statement(
        statement_id,
        delivery_method=data.delivery_method,
    )
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found")
    return statement


@router.get("/patients/{patient_id}/statements", response_model=List[StatementResponse])
async def get_patient_statements(
    patient_id: UUID,
    limit: int = Query(12, le=24),
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get statements for a patient."""
    service = StatementServiceDB(db, tenant_id)
    statements = await service.get_patient_statements(patient_id, limit)
    return statements


# ============================================================================
# FEE SCHEDULE ENDPOINTS
# ============================================================================

@router.post("/fee-schedules", response_model=FeeScheduleResponse, status_code=201)
async def create_fee_schedule(
    data: FeeScheduleCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Create a fee schedule."""
    from uuid import uuid4

    schedule = FeeSchedule(
        id=uuid4(),
        tenant_id=tenant_id,
        name=data.name,
        description=data.description,
        schedule_type=data.schedule_type,
        effective_date=data.effective_date,
        termination_date=data.termination_date,
        is_default=data.is_default,
        payer_id=data.payer_id,
        locality=data.locality,
    )

    db.add(schedule)

    # Add rates
    for rate_data in data.rates:
        rate = FeeScheduleRate(
            id=uuid4(),
            schedule_id=schedule.id,
            tenant_id=tenant_id,
            procedure_code=rate_data.procedure_code,
            modifier=rate_data.modifier,
            charge_amount=rate_data.charge_amount,
            expected_reimbursement=rate_data.expected_reimbursement,
            rvu_work=rate_data.rvu_work,
            rvu_pe=rate_data.rvu_pe,
            rvu_mp=rate_data.rvu_mp,
        )
        db.add(rate)

    db.commit()
    db.refresh(schedule)
    return schedule


@router.get("/fee-schedules", response_model=List[FeeScheduleResponse])
async def list_fee_schedules(
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """List all fee schedules."""
    schedules = db.query(FeeSchedule).filter(
        FeeSchedule.tenant_id == tenant_id,
        FeeSchedule.is_active == True,
    ).all()
    return schedules


@router.get("/fee-schedules/{schedule_id}", response_model=FeeScheduleResponse)
async def get_fee_schedule(
    schedule_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get fee schedule by ID."""
    schedule = db.query(FeeSchedule).filter(
        FeeSchedule.id == schedule_id,
        FeeSchedule.tenant_id == tenant_id,
    ).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Fee schedule not found")
    return schedule


@router.get("/fee-schedules/{schedule_id}/rates/{procedure_code}")
async def get_fee_schedule_rate(
    schedule_id: UUID,
    procedure_code: str,
    modifier: Optional[str] = None,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get rate for a specific procedure code."""
    query = db.query(FeeScheduleRate).filter(
        FeeScheduleRate.schedule_id == schedule_id,
        FeeScheduleRate.procedure_code == procedure_code,
    )
    if modifier:
        query = query.filter(FeeScheduleRate.modifier == modifier)

    rate = query.first()
    if not rate:
        raise HTTPException(status_code=404, detail="Rate not found")
    return rate


# ============================================================================
# CONTRACT ENDPOINTS
# ============================================================================

@router.post("/contracts", response_model=PayerContractResponse, status_code=201)
async def create_payer_contract(
    data: PayerContractCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Create a payer contract."""
    from uuid import uuid4

    contract = PayerContract(
        id=uuid4(),
        tenant_id=tenant_id,
        payer_id=data.payer_id,
        payer_name=data.payer_name,
        contract_name=data.contract_name,
        contract_number=data.contract_number,
        effective_date=data.effective_date,
        termination_date=data.termination_date,
        auto_renew=data.auto_renew,
        renewal_notice_days=data.renewal_notice_days,
        rate_type=data.rate_type,
        base_rate_percent=data.base_rate_percent,
        fee_schedule_id=data.fee_schedule_id,
        timely_filing_days=data.timely_filing_days,
        appeal_filing_days=data.appeal_filing_days,
        terms_notes=data.terms_notes,
        status="active",
    )

    db.add(contract)

    # Add rate overrides
    for override_data in data.rate_overrides:
        override = ContractRateOverride(
            id=uuid4(),
            contract_id=contract.id,
            tenant_id=tenant_id,
            procedure_code=override_data.procedure_code,
            modifier=override_data.modifier,
            rate_type=override_data.rate_type,
            rate_amount=override_data.rate_amount,
            rate_percent=override_data.rate_percent,
            effective_date=override_data.effective_date,
        )
        db.add(override)

    db.commit()
    db.refresh(contract)
    return contract


@router.get("/contracts", response_model=List[PayerContractResponse])
async def list_payer_contracts(
    payer_id: Optional[str] = None,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """List payer contracts."""
    query = db.query(PayerContract).filter(
        PayerContract.tenant_id == tenant_id,
    )
    if payer_id:
        query = query.filter(PayerContract.payer_id == payer_id)
    contracts = query.all()
    return contracts


@router.get("/contracts/{contract_id}", response_model=PayerContractResponse)
async def get_payer_contract(
    contract_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get payer contract by ID."""
    contract = db.query(PayerContract).filter(
        PayerContract.id == contract_id,
        PayerContract.tenant_id == tenant_id,
    ).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract


# ============================================================================
# DENIAL MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/denials", response_model=DenialRecordResponse, status_code=201)
async def record_denial(
    data: DenialRecordCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Record a claim denial."""
    from uuid import uuid4

    denial = DenialRecord(
        id=uuid4(),
        tenant_id=tenant_id,
        claim_id=data.claim_id,
        claim_line_id=data.claim_line_id,
        denial_date=data.denial_date,
        denial_reason_code=data.denial_reason_code,
        denial_reason_description=data.denial_reason_description,
        denial_category=data.denial_category.value if data.denial_category else None,
        denied_amount=data.denied_amount,
        is_appealable=data.is_appealable,
        appeal_deadline=data.appeal_deadline,
        resolution_status="open",
    )

    db.add(denial)
    db.commit()
    db.refresh(denial)
    return denial


@router.get("/denials/{denial_id}", response_model=DenialRecordResponse)
async def get_denial(
    denial_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get denial record by ID."""
    denial = db.query(DenialRecord).filter(
        DenialRecord.id == denial_id,
        DenialRecord.tenant_id == tenant_id,
    ).first()
    if not denial:
        raise HTTPException(status_code=404, detail="Denial record not found")
    return denial


@router.post("/denials/{denial_id}/appeal", response_model=DenialRecordResponse)
async def submit_denial_appeal(
    denial_id: UUID,
    data: DenialAppealRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Submit appeal for denial."""
    denial = db.query(DenialRecord).filter(
        DenialRecord.id == denial_id,
        DenialRecord.tenant_id == tenant_id,
    ).first()

    if not denial:
        raise HTTPException(status_code=404, detail="Denial record not found")
    if not denial.is_appealable:
        raise HTTPException(status_code=400, detail="Denial is not appealable")

    denial.appeal_submitted = True
    denial.appeal_submitted_at = datetime.now()
    denial.appeal_status = "submitted"
    denial.resolution_status = "in_progress"

    db.commit()
    db.refresh(denial)
    return denial


@router.post("/denials/{denial_id}/resolve", response_model=DenialRecordResponse)
async def resolve_denial(
    denial_id: UUID,
    data: DenialResolveRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Resolve a denial."""
    denial = db.query(DenialRecord).filter(
        DenialRecord.id == denial_id,
        DenialRecord.tenant_id == tenant_id,
    ).first()

    if not denial:
        raise HTTPException(status_code=404, detail="Denial record not found")

    denial.resolution_status = data.resolution_status
    denial.resolution_date = date.today()
    denial.resolution_notes = data.resolution_notes
    denial.recovered_amount = data.recovered_amount
    denial.root_cause = data.root_cause
    denial.preventable = data.preventable

    db.commit()
    db.refresh(denial)
    return denial


@router.get("/denials", response_model=List[DenialRecordResponse])
async def list_denials(
    status: Optional[str] = None,
    category: Optional[str] = None,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """List denial records."""
    query = db.query(DenialRecord).filter(
        DenialRecord.tenant_id == tenant_id,
    )
    if status:
        query = query.filter(DenialRecord.resolution_status == status)
    if category:
        query = query.filter(DenialRecord.denial_category == category)

    denials = query.order_by(DenialRecord.denial_date.desc()).all()
    return denials


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/analytics/revenue-cycle", response_model=RevenueCycleMetrics)
async def get_revenue_cycle_metrics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get revenue cycle KPIs."""
    service = BillingAnalyticsService(db, tenant_id)
    metrics = await service.get_revenue_cycle_metrics(start_date, end_date)
    return RevenueCycleMetrics(**metrics)


@router.get("/analytics/claims-summary", response_model=ClaimsSummary)
async def get_claims_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get claims summary statistics."""
    service = BillingAnalyticsService(db, tenant_id)
    summary = await service.get_claims_summary(start_date, end_date)
    return ClaimsSummary(**summary)


@router.get("/analytics/denials", response_model=DenialAnalytics)
async def get_denial_analytics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get denial analytics."""
    service = BillingAnalyticsService(db, tenant_id)
    analytics = await service.get_denial_analytics(start_date, end_date)
    return DenialAnalytics(**analytics)


@router.get("/analytics/ar-aging", response_model=ARAgingReport)
async def get_ar_aging_report(
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get accounts receivable aging report."""
    service = BillingAnalyticsService(db, tenant_id)
    report = await service.get_ar_aging_report()
    return ARAgingReport(**report)
