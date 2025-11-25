"""
Insurance & Billing Service Layer

Business logic services for billing operations:
- Eligibility verification with persistence
- Prior authorization management
- Claims lifecycle management
- Payment processing
- Statement generation
- Revenue cycle analytics

EPIC-008: Insurance & Billing Integration
"""

from datetime import datetime, date, timezone, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from decimal import Decimal
import logging

from .models import (
    InsurancePolicy, EligibilityVerification, PriorAuthorization,
    Claim, ClaimLine, ClaimAdjustment, RemittanceAdvice,
    Payment, PaymentCard, PaymentPlan, PaymentPlanSchedule,
    PatientStatement, FeeSchedule, FeeScheduleRate,
    PayerContract, ContractRateOverride, DenialRecord, BillingAuditLog,
    ClaimStatus, PaymentStatus, PriorAuthStatus
)

logger = logging.getLogger(__name__)


# ============================================================================
# ELIGIBILITY SERVICE
# ============================================================================

class EligibilityServiceDB:
    """Eligibility verification service with database persistence."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def verify_eligibility(
        self,
        patient_id: UUID,
        payer_id: str,
        member_id: str,
        service_type: Optional[str] = None,
        service_date: Optional[date] = None,
        provider_id: Optional[UUID] = None,
        provider_npi: Optional[str] = None,
    ) -> EligibilityVerification:
        """Verify patient insurance eligibility."""
        start_time = datetime.now(timezone.utc)

        verification = EligibilityVerification(
            id=uuid4(),
            tenant_id=self.tenant_id,
            patient_id=patient_id,
            payer_id=payer_id,
            member_id=member_id,
            provider_id=provider_id,
            provider_npi=provider_npi,
            service_type=service_type,
            service_date=service_date or date.today(),
            requested_at=start_time,
            source="api",
        )

        try:
            # In production, call clearinghouse API (270/271 EDI)
            # For now, generate mock response
            coverage = await self._mock_eligibility_check(payer_id, member_id, service_type)

            verification.status = "success"
            verification.responded_at = datetime.now(timezone.utc)
            verification.response_time_ms = int(
                (verification.responded_at - start_time).total_seconds() * 1000
            )
            verification.eligibility_status = "active"
            verification.coverage_active = True
            verification.coverage_details = coverage

            # Extract service-specific info
            if service_type and coverage.get("benefits", {}).get(service_type):
                benefit = coverage["benefits"][service_type]
                verification.service_eligible = benefit.get("covered", True)
                verification.copay_amount = benefit.get("copay_amount", 0)
                verification.coinsurance_percent = benefit.get("coinsurance_percent", 0)
                verification.prior_auth_required = benefit.get("prior_auth_required", False)

            # Calculate estimated patient responsibility
            verification.estimated_patient_responsibility = await self._estimate_patient_cost(
                coverage, service_type
            )

            # Get deductible info
            deductibles = coverage.get("deductibles", [])
            if deductibles:
                individual_ded = next(
                    (d for d in deductibles if d.get("coverage_level") == "individual"), None
                )
                if individual_ded:
                    verification.deductible_remaining = individual_ded.get("remaining")

        except Exception as e:
            verification.status = "error"
            verification.error_message = str(e)
            verification.responded_at = datetime.now(timezone.utc)
            logger.error(f"Eligibility verification failed: {e}")

        self.db.add(verification)
        self.db.commit()
        self.db.refresh(verification)
        return verification

    async def _mock_eligibility_check(
        self,
        payer_id: str,
        member_id: str,
        service_type: Optional[str],
    ) -> Dict[str, Any]:
        """Generate mock eligibility response."""
        # In production, parse 271 EDI response
        return {
            "payer_id": payer_id,
            "payer_name": self._get_payer_name(payer_id),
            "plan_name": f"{payer_id} PPO",
            "plan_type": "PPO",
            "member_id": member_id,
            "status": "active",
            "effective_date": str(date(2024, 1, 1)),
            "deductibles": [
                {
                    "coverage_level": "individual",
                    "network_type": "in_network",
                    "amount": 1500,
                    "remaining": 750,
                    "met": 750,
                },
                {
                    "coverage_level": "family",
                    "network_type": "in_network",
                    "amount": 3000,
                    "remaining": 1500,
                    "met": 1500,
                },
            ],
            "out_of_pocket": [
                {
                    "coverage_level": "individual",
                    "network_type": "in_network",
                    "amount": 6000,
                    "remaining": 4500,
                    "met": 1500,
                },
            ],
            "benefits": {
                "office_visit": {
                    "covered": True,
                    "copay_amount": 25,
                    "coinsurance_percent": 0,
                    "prior_auth_required": False,
                },
                "specialist": {
                    "covered": True,
                    "copay_amount": 50,
                    "coinsurance_percent": 0,
                    "prior_auth_required": False,
                },
                "preventive": {
                    "covered": True,
                    "copay_amount": 0,
                    "coverage_percent": 100,
                    "prior_auth_required": False,
                },
                "telehealth": {
                    "covered": True,
                    "copay_amount": 0,
                    "coinsurance_percent": 20,
                    "prior_auth_required": False,
                },
                "lab": {
                    "covered": True,
                    "copay_amount": 0,
                    "coinsurance_percent": 20,
                    "prior_auth_required": False,
                },
                "imaging": {
                    "covered": True,
                    "copay_amount": 0,
                    "coinsurance_percent": 20,
                    "prior_auth_required": True,
                },
                "surgery": {
                    "covered": True,
                    "copay_amount": 0,
                    "coinsurance_percent": 20,
                    "prior_auth_required": True,
                },
            },
        }

    def _get_payer_name(self, payer_id: str) -> str:
        """Get payer name from ID."""
        payers = {
            "BCBS": "Blue Cross Blue Shield",
            "AETNA": "Aetna",
            "UHC": "UnitedHealthcare",
            "CIGNA": "Cigna",
            "MEDICARE": "Medicare",
            "MEDICAID": "Medicaid",
        }
        return payers.get(payer_id, payer_id)

    async def _estimate_patient_cost(
        self,
        coverage: Dict[str, Any],
        service_type: Optional[str],
        estimated_charge: float = 200,
    ) -> float:
        """Estimate patient out-of-pocket cost."""
        if not service_type:
            return 0

        benefit = coverage.get("benefits", {}).get(service_type)
        if not benefit:
            return estimated_charge

        patient_cost = benefit.get("copay_amount", 0)

        coinsurance = benefit.get("coinsurance_percent", 0)
        if coinsurance > 0:
            deductibles = coverage.get("deductibles", [])
            individual_ded = next(
                (d for d in deductibles if d.get("coverage_level") == "individual"), None
            )

            if individual_ded and individual_ded.get("remaining", 0) > 0:
                ded_portion = min(individual_ded["remaining"], estimated_charge)
                remaining = estimated_charge - ded_portion
                patient_cost += ded_portion + (remaining * coinsurance / 100)
            else:
                patient_cost += estimated_charge * coinsurance / 100

        return round(patient_cost, 2)

    async def get_verification(self, verification_id: UUID) -> Optional[EligibilityVerification]:
        """Get eligibility verification by ID."""
        return self.db.query(EligibilityVerification).filter(
            EligibilityVerification.id == verification_id,
            EligibilityVerification.tenant_id == self.tenant_id,
        ).first()

    async def get_patient_verifications(
        self,
        patient_id: UUID,
        limit: int = 10,
    ) -> List[EligibilityVerification]:
        """Get recent eligibility verifications for a patient."""
        return self.db.query(EligibilityVerification).filter(
            EligibilityVerification.tenant_id == self.tenant_id,
            EligibilityVerification.patient_id == patient_id,
        ).order_by(desc(EligibilityVerification.requested_at)).limit(limit).all()

    async def batch_verify(
        self,
        verifications: List[Dict[str, Any]],
    ) -> List[EligibilityVerification]:
        """Batch eligibility verification."""
        results = []
        for v in verifications:
            result = await self.verify_eligibility(
                patient_id=v["patient_id"],
                payer_id=v["payer_id"],
                member_id=v["member_id"],
                service_type=v.get("service_type"),
                provider_id=v.get("provider_id"),
            )
            results.append(result)
        return results


# ============================================================================
# PRIOR AUTHORIZATION SERVICE
# ============================================================================

class PriorAuthorizationServiceDB:
    """Prior authorization management service."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def create_prior_auth(
        self,
        patient_id: UUID,
        payer_id: str,
        service_type: str,
        procedure_codes: List[str] = None,
        diagnosis_codes: List[str] = None,
        quantity_requested: int = 1,
        **kwargs,
    ) -> PriorAuthorization:
        """Create a new prior authorization request."""
        prior_auth = PriorAuthorization(
            id=uuid4(),
            tenant_id=self.tenant_id,
            patient_id=patient_id,
            payer_id=payer_id,
            payer_name=kwargs.get("payer_name"),
            service_type=service_type,
            procedure_codes=procedure_codes or [],
            diagnosis_codes=diagnosis_codes or [],
            quantity_requested=quantity_requested,
            policy_id=kwargs.get("policy_id"),
            requesting_provider_id=kwargs.get("requesting_provider_id"),
            requesting_provider_npi=kwargs.get("requesting_provider_npi"),
            performing_provider_id=kwargs.get("performing_provider_id"),
            performing_provider_npi=kwargs.get("performing_provider_npi"),
            facility_id=kwargs.get("facility_id"),
            service_date_start=kwargs.get("service_date_start"),
            service_date_end=kwargs.get("service_date_end"),
            clinical_summary=kwargs.get("clinical_summary"),
            medical_necessity=kwargs.get("medical_necessity"),
            status="draft",
        )

        self.db.add(prior_auth)
        self.db.commit()
        self.db.refresh(prior_auth)
        return prior_auth

    async def get_prior_auth(self, auth_id: UUID) -> Optional[PriorAuthorization]:
        """Get prior authorization by ID."""
        return self.db.query(PriorAuthorization).filter(
            PriorAuthorization.id == auth_id,
            PriorAuthorization.tenant_id == self.tenant_id,
        ).first()

    async def update_prior_auth(
        self,
        auth_id: UUID,
        **updates,
    ) -> Optional[PriorAuthorization]:
        """Update prior authorization."""
        prior_auth = await self.get_prior_auth(auth_id)
        if not prior_auth:
            return None

        for key, value in updates.items():
            if hasattr(prior_auth, key) and value is not None:
                setattr(prior_auth, key, value)

        self.db.commit()
        self.db.refresh(prior_auth)
        return prior_auth

    async def submit_prior_auth(
        self,
        auth_id: UUID,
        submission_method: str = "electronic",
        submitted_by: Optional[UUID] = None,
    ) -> Optional[PriorAuthorization]:
        """Submit prior authorization to payer."""
        prior_auth = await self.get_prior_auth(auth_id)
        if not prior_auth:
            return None

        # In production, format and submit 278 EDI request
        prior_auth.status = "submitted"
        prior_auth.submission_method = submission_method
        prior_auth.submitted_at = datetime.now(timezone.utc)
        prior_auth.submitted_by = submitted_by
        prior_auth.reference_number = f"PA-{uuid4().hex[:8].upper()}"

        self.db.commit()
        self.db.refresh(prior_auth)
        return prior_auth

    async def record_decision(
        self,
        auth_id: UUID,
        status: str,
        auth_number: Optional[str] = None,
        quantity_approved: Optional[int] = None,
        effective_date: Optional[date] = None,
        expiration_date: Optional[date] = None,
        decision_reason: Optional[str] = None,
        payer_notes: Optional[str] = None,
    ) -> Optional[PriorAuthorization]:
        """Record prior authorization decision."""
        prior_auth = await self.get_prior_auth(auth_id)
        if not prior_auth:
            return None

        prior_auth.status = status
        prior_auth.auth_number = auth_number
        prior_auth.quantity_approved = quantity_approved
        prior_auth.effective_date = effective_date
        prior_auth.expiration_date = expiration_date
        prior_auth.decision_date = date.today()
        prior_auth.decision_reason = decision_reason
        prior_auth.payer_notes = payer_notes

        # Set appeal deadline if denied
        if status == "denied":
            prior_auth.appeal_deadline = date.today() + timedelta(days=180)

        self.db.commit()
        self.db.refresh(prior_auth)
        return prior_auth

    async def appeal_prior_auth(
        self,
        auth_id: UUID,
        appeal_notes: Optional[str] = None,
    ) -> Optional[PriorAuthorization]:
        """Submit appeal for denied prior auth."""
        prior_auth = await self.get_prior_auth(auth_id)
        if not prior_auth or prior_auth.status != "denied":
            return None

        prior_auth.status = "appealed"
        prior_auth.appealed_at = datetime.now(timezone.utc)
        prior_auth.appeal_status = "submitted"
        prior_auth.appeal_notes = appeal_notes

        self.db.commit()
        self.db.refresh(prior_auth)
        return prior_auth

    async def get_patient_prior_auths(
        self,
        patient_id: UUID,
        status: Optional[str] = None,
    ) -> List[PriorAuthorization]:
        """Get prior authorizations for a patient."""
        query = self.db.query(PriorAuthorization).filter(
            PriorAuthorization.tenant_id == self.tenant_id,
            PriorAuthorization.patient_id == patient_id,
        )
        if status:
            query = query.filter(PriorAuthorization.status == status)
        return query.order_by(desc(PriorAuthorization.created_at)).all()

    async def get_expiring_auths(self, days_ahead: int = 30) -> List[PriorAuthorization]:
        """Get prior authorizations expiring soon."""
        expiry_threshold = date.today() + timedelta(days=days_ahead)
        return self.db.query(PriorAuthorization).filter(
            PriorAuthorization.tenant_id == self.tenant_id,
            PriorAuthorization.status == "approved",
            PriorAuthorization.expiration_date <= expiry_threshold,
            PriorAuthorization.expiration_date >= date.today(),
        ).all()


# ============================================================================
# CLAIMS SERVICE
# ============================================================================

class ClaimsServiceDB:
    """Claims management service."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self._claim_counter = 1

    async def create_claim(
        self,
        patient_id: UUID,
        payer_id: str,
        member_id: str,
        billing_provider_npi: str,
        service_date_start: date,
        **kwargs,
    ) -> Claim:
        """Create a new claim."""
        claim_number = f"CLM-{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"

        claim = Claim(
            id=uuid4(),
            tenant_id=self.tenant_id,
            claim_number=claim_number,
            claim_type=kwargs.get("claim_type", "professional"),
            patient_id=patient_id,
            payer_id=payer_id,
            payer_name=kwargs.get("payer_name"),
            member_id=member_id,
            group_number=kwargs.get("group_number"),
            policy_id=kwargs.get("policy_id"),
            prior_auth_number=kwargs.get("prior_auth_number"),
            prior_auth_id=kwargs.get("prior_auth_id"),
            billing_provider_npi=billing_provider_npi,
            billing_provider_tax_id=kwargs.get("billing_provider_tax_id"),
            rendering_provider_npi=kwargs.get("rendering_provider_npi"),
            referring_provider_npi=kwargs.get("referring_provider_npi"),
            facility_npi=kwargs.get("facility_npi"),
            encounter_id=kwargs.get("encounter_id"),
            service_date_start=service_date_start,
            service_date_end=kwargs.get("service_date_end"),
            place_of_service=kwargs.get("place_of_service", "11"),
            diagnoses=kwargs.get("diagnoses", []),
            status="draft",
        )

        self.db.add(claim)
        self.db.commit()
        self.db.refresh(claim)

        # Add claim lines if provided
        lines = kwargs.get("lines", [])
        for i, line_data in enumerate(lines):
            await self.add_claim_line(claim.id, line_number=i + 1, **line_data)

        self.db.refresh(claim)
        return claim

    async def add_diagnosis(
        self,
        claim_id: UUID,
        code: str,
        code_type: str = "ICD-10",
        sequence: Optional[int] = None,
    ) -> Optional[Claim]:
        """Add diagnosis to claim."""
        claim = await self.get_claim(claim_id)
        if not claim:
            return None

        diagnoses = claim.diagnoses or []
        new_seq = sequence or len(diagnoses) + 1
        pointer = chr(64 + new_seq)  # A, B, C, D...

        diagnoses.append({
            "code": code,
            "type": code_type,
            "sequence": new_seq,
            "pointer": pointer,
        })

        claim.diagnoses = diagnoses
        if new_seq == 1:
            claim.principal_diagnosis = code

        self.db.commit()
        self.db.refresh(claim)
        return claim

    async def add_claim_line(
        self,
        claim_id: UUID,
        procedure_code: str,
        charge_amount: float,
        service_date: date,
        line_number: Optional[int] = None,
        **kwargs,
    ) -> ClaimLine:
        """Add service line to claim."""
        claim = await self.get_claim(claim_id)
        if not claim:
            raise ValueError("Claim not found")

        if line_number is None:
            existing_lines = self.db.query(ClaimLine).filter(
                ClaimLine.claim_id == claim_id
            ).count()
            line_number = existing_lines + 1

        line = ClaimLine(
            id=uuid4(),
            claim_id=claim_id,
            tenant_id=self.tenant_id,
            line_number=line_number,
            procedure_code=procedure_code,
            modifiers=kwargs.get("modifiers", []),
            description=kwargs.get("description"),
            revenue_code=kwargs.get("revenue_code"),
            diagnosis_pointers=kwargs.get("diagnosis_pointers", ["A"]),
            service_date=service_date,
            service_date_end=kwargs.get("service_date_end"),
            place_of_service=kwargs.get("place_of_service"),
            units=kwargs.get("units", 1),
            charge_amount=charge_amount,
            rendering_provider_npi=kwargs.get("rendering_provider_npi"),
            ndc_code=kwargs.get("ndc_code"),
            status="pending",
        )

        self.db.add(line)

        # Update claim totals
        claim.total_charge = (claim.total_charge or 0) + Decimal(str(charge_amount))

        self.db.commit()
        self.db.refresh(line)
        return line

    async def validate_claim(self, claim_id: UUID) -> Dict[str, Any]:
        """Validate claim for submission."""
        claim = await self.get_claim(claim_id)
        if not claim:
            return {"valid": False, "errors": [{"field": "claim", "error": "Claim not found"}]}

        errors = []
        warnings = []

        # Required field validation
        if not claim.diagnoses:
            errors.append({"field": "diagnoses", "error": "At least one diagnosis required"})

        if not claim.lines:
            errors.append({"field": "lines", "error": "At least one service line required"})

        # Validate diagnosis pointers
        valid_pointers = {d.get("pointer") for d in (claim.diagnoses or [])}
        for line in claim.lines or []:
            for pointer in line.diagnosis_pointers or []:
                if pointer not in valid_pointers:
                    errors.append({
                        "field": f"line_{line.line_number}",
                        "error": f"Invalid diagnosis pointer: {pointer}",
                    })

        # NCCI edit checks (simplified)
        procedure_codes = [line.procedure_code for line in claim.lines or []]
        # In production, check NCCI bundling rules

        # Medical necessity check
        # In production, verify diagnoses support procedures

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    async def submit_claim(
        self,
        claim_id: UUID,
        submission_method: str = "electronic_837",
        submitted_by: Optional[UUID] = None,
    ) -> Optional[Claim]:
        """Submit claim to payer."""
        claim = await self.get_claim(claim_id)
        if not claim:
            return None

        # Validate before submission
        validation = await self.validate_claim(claim_id)
        if not validation["valid"]:
            raise ValueError(f"Claim validation failed: {validation['errors']}")

        # In production, generate 837 EDI and submit to clearinghouse
        claim.status = "submitted"
        claim.submission_method = submission_method
        claim.submitted_at = datetime.now(timezone.utc)
        claim.submitted_by = submitted_by
        claim.status_date = datetime.now(timezone.utc)

        # Generate mock clearinghouse ID
        claim.clearinghouse_claim_id = f"CH-{uuid4().hex[:12].upper()}"

        self.db.commit()
        self.db.refresh(claim)
        return claim

    async def process_acknowledgment(
        self,
        claim_id: UUID,
        acknowledged: bool,
        payer_claim_number: Optional[str] = None,
        errors: List[Dict] = None,
    ) -> Optional[Claim]:
        """Process claim acknowledgment (277CA)."""
        claim = await self.get_claim(claim_id)
        if not claim:
            return None

        claim.acknowledged_at = datetime.now(timezone.utc)
        claim.acknowledgment_code = "A" if acknowledged else "R"
        claim.acknowledgment_errors = errors or []

        if acknowledged:
            claim.status = "acknowledged"
            claim.payer_claim_number = payer_claim_number
        else:
            claim.status = "rejected"

        claim.status_date = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(claim)
        return claim

    async def void_claim(
        self,
        claim_id: UUID,
        reason: str,
    ) -> Optional[Claim]:
        """Void a claim."""
        claim = await self.get_claim(claim_id)
        if not claim:
            return None

        claim.status = "void"
        claim.status_reason = reason
        claim.status_date = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(claim)
        return claim

    async def get_claim(self, claim_id: UUID) -> Optional[Claim]:
        """Get claim by ID."""
        return self.db.query(Claim).filter(
            Claim.id == claim_id,
            Claim.tenant_id == self.tenant_id,
        ).first()

    async def get_patient_claims(
        self,
        patient_id: UUID,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[Claim]:
        """Get claims for a patient."""
        query = self.db.query(Claim).filter(
            Claim.tenant_id == self.tenant_id,
            Claim.patient_id == patient_id,
        )
        if status:
            query = query.filter(Claim.status == status)
        return query.order_by(desc(Claim.created_at)).limit(limit).all()

    async def get_pending_claims(self) -> List[Claim]:
        """Get claims pending submission."""
        return self.db.query(Claim).filter(
            Claim.tenant_id == self.tenant_id,
            Claim.status.in_(["draft", "pending_submission"]),
        ).order_by(Claim.created_at).all()


# ============================================================================
# PAYMENT SERVICE
# ============================================================================

class PaymentServiceDB:
    """Payment processing service."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def process_payment(
        self,
        patient_id: UUID,
        amount: float,
        payment_type: str,
        payment_method: str,
        **kwargs,
    ) -> Payment:
        """Process a payment."""
        payment_number = f"PMT-{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"

        payment = Payment(
            id=uuid4(),
            tenant_id=self.tenant_id,
            payment_number=payment_number,
            patient_id=patient_id,
            amount=amount,
            payment_type=payment_type,
            payment_method=payment_method,
            card_id=kwargs.get("card_id"),
            check_number=kwargs.get("check_number"),
            encounter_id=kwargs.get("encounter_id"),
            claim_id=kwargs.get("claim_id"),
            appointment_id=kwargs.get("appointment_id"),
            payment_plan_id=kwargs.get("payment_plan_id"),
            notes=kwargs.get("notes"),
            status="pending",
        )

        # Get card details if card payment
        if payment.card_id:
            card = self.db.query(PaymentCard).filter(
                PaymentCard.id == payment.card_id
            ).first()
            if card:
                payment.card_last_four = card.last_four
                payment.card_type = card.card_type

        # In production, process through payment gateway (Stripe, Square)
        # Mock successful processing
        payment.status = "completed"
        payment.processor = "stripe"
        payment.processor_transaction_id = f"txn_{uuid4().hex}"
        payment.authorization_code = uuid4().hex[:6].upper()
        payment.processed_at = datetime.now(timezone.utc)
        payment.receipt_number = f"RCP-{uuid4().hex[:8].upper()}"

        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    async def refund_payment(
        self,
        payment_id: UUID,
        amount: Optional[float] = None,
        reason: str = "",
    ) -> Optional[Payment]:
        """Refund a payment."""
        payment = await self.get_payment(payment_id)
        if not payment or payment.status != "completed":
            return None

        refund_amount = amount or float(payment.amount)
        if refund_amount > float(payment.amount):
            raise ValueError("Refund amount exceeds payment amount")

        # In production, process refund through payment gateway
        payment.refund_amount = refund_amount
        payment.refund_reason = reason
        payment.refunded_at = datetime.now(timezone.utc)
        payment.refund_transaction_id = f"rfnd_{uuid4().hex}"

        if refund_amount >= float(payment.amount):
            payment.status = "refunded"
        else:
            payment.status = "partial_refund"

        self.db.commit()
        self.db.refresh(payment)
        return payment

    async def store_card(
        self,
        patient_id: UUID,
        token: str,
        last_four: str,
        card_type: str,
        expiry_month: int,
        expiry_year: int,
        **kwargs,
    ) -> PaymentCard:
        """Store a payment card (tokenized)."""
        card = PaymentCard(
            id=uuid4(),
            tenant_id=self.tenant_id,
            patient_id=patient_id,
            token=token,
            last_four=last_four,
            card_type=card_type,
            expiry_month=expiry_month,
            expiry_year=expiry_year,
            cardholder_name=kwargs.get("cardholder_name"),
            billing_address=kwargs.get("billing_address"),
            is_default=kwargs.get("is_default", False),
        )

        # If setting as default, unset other defaults
        if card.is_default:
            self.db.query(PaymentCard).filter(
                PaymentCard.tenant_id == self.tenant_id,
                PaymentCard.patient_id == patient_id,
                PaymentCard.is_default == True,
            ).update({"is_default": False})

        self.db.add(card)
        self.db.commit()
        self.db.refresh(card)
        return card

    async def get_patient_cards(self, patient_id: UUID) -> List[PaymentCard]:
        """Get patient's stored cards."""
        return self.db.query(PaymentCard).filter(
            PaymentCard.tenant_id == self.tenant_id,
            PaymentCard.patient_id == patient_id,
            PaymentCard.is_active == True,
        ).all()

    async def delete_card(self, card_id: UUID) -> bool:
        """Delete (deactivate) a stored card."""
        card = self.db.query(PaymentCard).filter(
            PaymentCard.id == card_id,
            PaymentCard.tenant_id == self.tenant_id,
        ).first()
        if card:
            card.is_active = False
            self.db.commit()
            return True
        return False

    async def create_payment_plan(
        self,
        patient_id: UUID,
        total_amount: float,
        payment_amount: float,
        total_payments: int,
        start_date: date,
        frequency: str = "monthly",
        **kwargs,
    ) -> PaymentPlan:
        """Create a payment plan."""
        down_payment = kwargs.get("down_payment", 0)

        plan = PaymentPlan(
            id=uuid4(),
            tenant_id=self.tenant_id,
            patient_id=patient_id,
            plan_name=kwargs.get("plan_name"),
            total_amount=total_amount,
            down_payment=down_payment,
            payment_amount=payment_amount,
            frequency=frequency,
            paid_amount=down_payment,
            remaining_amount=total_amount - down_payment,
            total_payments=total_payments,
            start_date=start_date,
            auto_pay=kwargs.get("auto_pay", False),
            card_id=kwargs.get("card_id"),
            claim_ids=kwargs.get("claim_ids", []),
            encounter_ids=kwargs.get("encounter_ids", []),
            status="active",
        )

        # Calculate end date
        if frequency == "weekly":
            plan.end_date = start_date + timedelta(weeks=total_payments)
        elif frequency == "biweekly":
            plan.end_date = start_date + timedelta(weeks=total_payments * 2)
        else:  # monthly
            plan.end_date = start_date + timedelta(days=total_payments * 30)

        self.db.add(plan)
        self.db.commit()

        # Create scheduled payments
        current_date = start_date
        for seq in range(1, total_payments + 1):
            schedule = PaymentPlanSchedule(
                id=uuid4(),
                plan_id=plan.id,
                tenant_id=self.tenant_id,
                sequence=seq,
                due_date=current_date,
                amount=payment_amount,
                status="scheduled",
            )
            self.db.add(schedule)

            if frequency == "weekly":
                current_date += timedelta(weeks=1)
            elif frequency == "biweekly":
                current_date += timedelta(weeks=2)
            else:
                current_date += timedelta(days=30)

        plan.next_payment_date = start_date
        self.db.commit()
        self.db.refresh(plan)
        return plan

    async def get_payment(self, payment_id: UUID) -> Optional[Payment]:
        """Get payment by ID."""
        return self.db.query(Payment).filter(
            Payment.id == payment_id,
            Payment.tenant_id == self.tenant_id,
        ).first()

    async def get_patient_payments(
        self,
        patient_id: UUID,
        limit: int = 50,
    ) -> List[Payment]:
        """Get payments for a patient."""
        return self.db.query(Payment).filter(
            Payment.tenant_id == self.tenant_id,
            Payment.patient_id == patient_id,
        ).order_by(desc(Payment.created_at)).limit(limit).all()

    async def get_patient_plans(
        self,
        patient_id: UUID,
    ) -> List[PaymentPlan]:
        """Get payment plans for a patient."""
        return self.db.query(PaymentPlan).filter(
            PaymentPlan.tenant_id == self.tenant_id,
            PaymentPlan.patient_id == patient_id,
        ).order_by(desc(PaymentPlan.created_at)).all()


# ============================================================================
# STATEMENT SERVICE
# ============================================================================

class StatementServiceDB:
    """Patient statement service."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def generate_statement(
        self,
        patient_id: UUID,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
    ) -> PatientStatement:
        """Generate patient statement."""
        statement_number = f"STMT-{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"

        if not period_end:
            period_end = date.today()
        if not period_start:
            period_start = period_end - timedelta(days=30)

        # Calculate amounts (in production, aggregate from claims and payments)
        previous_balance = 0
        new_charges = 0
        payments_received = 0
        adjustments = 0

        # Get claims in period
        claims = self.db.query(Claim).filter(
            Claim.tenant_id == self.tenant_id,
            Claim.patient_id == patient_id,
            Claim.service_date_start >= period_start,
            Claim.service_date_start <= period_end,
        ).all()

        line_items = []
        for claim in claims:
            new_charges += float(claim.patient_responsibility or 0)
            line_items.append({
                "date": str(claim.service_date_start),
                "description": f"Services - Claim {claim.claim_number}",
                "charges": float(claim.total_charge or 0),
                "insurance_paid": float(claim.total_paid or 0),
                "patient_owes": float(claim.patient_responsibility or 0),
            })

        # Get payments in period
        payments = self.db.query(Payment).filter(
            Payment.tenant_id == self.tenant_id,
            Payment.patient_id == patient_id,
            Payment.created_at >= datetime.combine(period_start, datetime.min.time()),
            Payment.created_at <= datetime.combine(period_end, datetime.max.time()),
            Payment.status == "completed",
        ).all()

        for payment in payments:
            payments_received += float(payment.amount)
            line_items.append({
                "date": str(payment.created_at.date()),
                "description": f"Payment - {payment.payment_number}",
                "payment": float(payment.amount),
            })

        current_balance = previous_balance + new_charges - payments_received - adjustments
        amount_due = max(0, current_balance)

        statement = PatientStatement(
            id=uuid4(),
            tenant_id=self.tenant_id,
            patient_id=patient_id,
            statement_number=statement_number,
            statement_date=date.today(),
            period_start=period_start,
            period_end=period_end,
            due_date=date.today() + timedelta(days=30),
            previous_balance=previous_balance,
            new_charges=new_charges,
            payments_received=payments_received,
            adjustments=adjustments,
            current_balance=current_balance,
            amount_due=amount_due,
            line_items=line_items,
            status="generated",
        )

        # Calculate aging
        statement.current = amount_due  # Simplified

        self.db.add(statement)
        self.db.commit()
        self.db.refresh(statement)
        return statement

    async def send_statement(
        self,
        statement_id: UUID,
        delivery_method: str = "email",
    ) -> Optional[PatientStatement]:
        """Send statement to patient."""
        statement = self.db.query(PatientStatement).filter(
            PatientStatement.id == statement_id,
            PatientStatement.tenant_id == self.tenant_id,
        ).first()

        if not statement:
            return None

        # In production, send via email/mail/portal
        statement.delivery_method = delivery_method
        statement.sent_at = datetime.now(timezone.utc)
        statement.status = "sent"

        self.db.commit()
        self.db.refresh(statement)
        return statement

    async def get_patient_statements(
        self,
        patient_id: UUID,
        limit: int = 12,
    ) -> List[PatientStatement]:
        """Get statements for a patient."""
        return self.db.query(PatientStatement).filter(
            PatientStatement.tenant_id == self.tenant_id,
            PatientStatement.patient_id == patient_id,
        ).order_by(desc(PatientStatement.statement_date)).limit(limit).all()


# ============================================================================
# ANALYTICS SERVICE
# ============================================================================

class BillingAnalyticsService:
    """Revenue cycle analytics service."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def get_revenue_cycle_metrics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Get revenue cycle KPIs."""
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # Get claims in period
        claims = self.db.query(Claim).filter(
            Claim.tenant_id == self.tenant_id,
            Claim.service_date_start >= start_date,
            Claim.service_date_start <= end_date,
        ).all()

        total_claims = len(claims)
        clean_claims = len([c for c in claims if c.status not in ["rejected"]])
        denied_claims = len([c for c in claims if c.status == "denied"])
        paid_claims = len([c for c in claims if c.status in ["paid", "partial_paid"]])

        total_charges = sum(float(c.total_charge or 0) for c in claims)
        total_payments = sum(float(c.total_paid or 0) for c in claims)
        total_adjustments = sum(float(c.total_adjustment or 0) for c in claims)
        total_ar = sum(float(c.balance or 0) for c in claims if c.balance and c.balance > 0)

        return {
            "days_in_ar": 35.5,  # Would calculate from payment dates
            "clean_claim_rate": clean_claims / total_claims * 100 if total_claims else 0,
            "denial_rate": denied_claims / total_claims * 100 if total_claims else 0,
            "first_pass_payment_rate": paid_claims / total_claims * 100 if total_claims else 0,
            "collection_rate": total_payments / total_charges * 100 if total_charges else 0,
            "net_collection_rate": total_payments / (total_charges - total_adjustments) * 100 if (total_charges - total_adjustments) else 0,
            "total_charges": total_charges,
            "total_payments": total_payments,
            "total_adjustments": total_adjustments,
            "total_ar": total_ar,
            "ar_over_90_days": 0,  # Would calculate from aging
            "prior_auth_turnaround_days": 2.5,  # Would calculate from PA data
        }

    async def get_claims_summary(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Get claims summary statistics."""
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        claims = self.db.query(Claim).filter(
            Claim.tenant_id == self.tenant_id,
            Claim.service_date_start >= start_date,
            Claim.service_date_start <= end_date,
        ).all()

        claims_by_status = {}
        claims_by_payer = {}
        total_charged = 0
        total_paid = 0
        total_denied = 0

        for claim in claims:
            claims_by_status[claim.status] = claims_by_status.get(claim.status, 0) + 1
            claims_by_payer[claim.payer_id] = claims_by_payer.get(claim.payer_id, 0) + 1
            total_charged += float(claim.total_charge or 0)
            total_paid += float(claim.total_paid or 0)
            if claim.status == "denied":
                total_denied += float(claim.total_charge or 0)

        return {
            "total_claims": len(claims),
            "claims_by_status": claims_by_status,
            "claims_by_payer": claims_by_payer,
            "total_charged": total_charged,
            "total_paid": total_paid,
            "total_denied": total_denied,
            "average_days_to_payment": 28.5,  # Would calculate from dates
        }

    async def get_denial_analytics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Get denial analytics."""
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=90)

        denials = self.db.query(DenialRecord).filter(
            DenialRecord.tenant_id == self.tenant_id,
            DenialRecord.denial_date >= start_date,
            DenialRecord.denial_date <= end_date,
        ).all()

        denials_by_category = {}
        denials_by_reason = {}
        total_denied = 0
        total_recovered = 0
        appeals_submitted = 0
        appeals_overturned = 0

        for denial in denials:
            denials_by_category[denial.denial_category or "other"] = \
                denials_by_category.get(denial.denial_category or "other", 0) + 1
            denials_by_reason[denial.denial_reason_code] = \
                denials_by_reason.get(denial.denial_reason_code, 0) + 1
            total_denied += float(denial.denied_amount or 0)
            total_recovered += float(denial.recovered_amount or 0)
            if denial.appeal_submitted:
                appeals_submitted += 1
            if denial.appeal_outcome == "overturned":
                appeals_overturned += 1

        return {
            "total_denials": len(denials),
            "total_denied_amount": total_denied,
            "denials_by_category": denials_by_category,
            "denials_by_payer": {},  # Would join with claims
            "denials_by_reason": denials_by_reason,
            "appeal_success_rate": appeals_overturned / appeals_submitted * 100 if appeals_submitted else 0,
            "total_recovered": total_recovered,
            "average_recovery_time_days": 45,  # Would calculate from dates
        }

    async def get_ar_aging_report(self) -> Dict[str, Any]:
        """Get accounts receivable aging report."""
        claims = self.db.query(Claim).filter(
            Claim.tenant_id == self.tenant_id,
            Claim.balance > 0,
        ).all()

        today = date.today()
        aging = {
            "total_ar": 0,
            "current": 0,
            "days_1_30": 0,
            "days_31_60": 0,
            "days_61_90": 0,
            "days_91_120": 0,
            "days_over_120": 0,
            "by_payer": {},
        }

        for claim in claims:
            balance = float(claim.balance)
            aging["total_ar"] += balance

            days_old = (today - claim.service_date_start).days

            if days_old <= 0:
                aging["current"] += balance
            elif days_old <= 30:
                aging["days_1_30"] += balance
            elif days_old <= 60:
                aging["days_31_60"] += balance
            elif days_old <= 90:
                aging["days_61_90"] += balance
            elif days_old <= 120:
                aging["days_91_120"] += balance
            else:
                aging["days_over_120"] += balance

            # By payer
            if claim.payer_id not in aging["by_payer"]:
                aging["by_payer"][claim.payer_id] = {"total": 0}
            aging["by_payer"][claim.payer_id]["total"] += balance

        return aging
