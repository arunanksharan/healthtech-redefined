"""
Claims Management Service

Healthcare claims processing:
- Claim creation and submission
- Status tracking
- Adjudication handling
- Denial management
- ERA/EOB processing

EPIC-008: US-008.2 Claims Management
"""

from datetime import datetime, timezone, date
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class ClaimStatus(str, Enum):
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
    APPEALED = "appealed"
    VOID = "void"


class ClaimType(str, Enum):
    """Type of claim."""
    PROFESSIONAL = "professional"  # CMS-1500
    INSTITUTIONAL = "institutional"  # UB-04
    DENTAL = "dental"


class SubmissionMethod(str, Enum):
    """Claim submission method."""
    ELECTRONIC = "electronic"
    PAPER = "paper"
    PORTAL = "portal"


@dataclass
class Diagnosis:
    """Diagnosis on a claim."""
    code: str
    code_type: str = "ICD-10"  # ICD-10, ICD-9
    sequence: int = 1
    pointer: str = ""  # A, B, C, D for claim line linking


@dataclass
class ClaimLine:
    """A line item on a claim (service)."""
    line_id: str
    sequence: int

    # Service details
    procedure_code: str  # CPT/HCPCS code
    modifiers: List[str] = field(default_factory=list)
    description: str = ""

    # Date and place
    service_date: date = field(default_factory=date.today)
    service_end_date: Optional[date] = None
    place_of_service: str = "11"  # 11 = Office

    # Diagnosis pointers
    diagnosis_pointers: List[str] = field(default_factory=list)

    # Units and charges
    units: int = 1
    charge_amount: float = 0

    # Adjudication (filled after payer response)
    allowed_amount: float = 0
    paid_amount: float = 0
    adjustment_amount: float = 0
    patient_responsibility: float = 0
    denial_reason: Optional[str] = None

    # Revenue code (for institutional)
    revenue_code: Optional[str] = None

    # NDC for drugs
    ndc_code: Optional[str] = None


@dataclass
class ClaimAdjustment:
    """Adjustment to a claim or line."""
    adjustment_id: str
    claim_id: str
    line_id: Optional[str] = None

    group_code: str = ""  # CO, PR, OA, PI
    reason_code: str = ""  # CARC code
    amount: float = 0
    description: str = ""


@dataclass
class PayerRemittance:
    """Payer remittance advice (ERA/835)."""
    remittance_id: str
    claim_id: str
    payer_id: str

    check_number: Optional[str] = None
    check_date: Optional[date] = None
    payment_amount: float = 0
    payment_method: str = "EFT"

    received_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    adjustments: List[ClaimAdjustment] = field(default_factory=list)
    remark_codes: List[str] = field(default_factory=list)


@dataclass
class Claim:
    """Healthcare insurance claim."""
    claim_id: str
    tenant_id: str

    # Type
    claim_type: ClaimType = ClaimType.PROFESSIONAL

    # Patient
    patient_id: str = ""
    patient_name: str = ""
    patient_dob: Optional[date] = None
    patient_address: str = ""

    # Subscriber (if different from patient)
    subscriber_id: Optional[str] = None
    subscriber_name: Optional[str] = None
    relationship_to_subscriber: str = "self"

    # Insurance
    payer_id: str = ""
    payer_name: str = ""
    member_id: str = ""
    group_number: Optional[str] = None

    # Secondary insurance
    secondary_payer_id: Optional[str] = None
    secondary_member_id: Optional[str] = None

    # Provider
    billing_provider_npi: str = ""
    billing_provider_name: str = ""
    billing_provider_tax_id: str = ""
    rendering_provider_npi: Optional[str] = None
    referring_provider_npi: Optional[str] = None

    # Facility
    facility_npi: Optional[str] = None
    facility_name: Optional[str] = None

    # Encounter
    encounter_id: Optional[str] = None
    admission_date: Optional[date] = None
    discharge_date: Optional[date] = None

    # Diagnoses
    diagnoses: List[Diagnosis] = field(default_factory=list)

    # Service lines
    lines: List[ClaimLine] = field(default_factory=list)

    # Prior authorization
    prior_auth_number: Optional[str] = None

    # Totals
    total_charge: float = 0
    total_allowed: float = 0
    total_paid: float = 0
    total_adjustment: float = 0
    patient_responsibility: float = 0

    # Status
    status: ClaimStatus = ClaimStatus.DRAFT
    submission_method: SubmissionMethod = SubmissionMethod.ELECTRONIC

    # Submission tracking
    submitted_at: Optional[datetime] = None
    payer_claim_number: Optional[str] = None
    clearinghouse_claim_id: Optional[str] = None

    # Remittance
    remittances: List[PayerRemittance] = field(default_factory=list)

    # Denial
    denial_reason: Optional[str] = None
    denial_date: Optional[date] = None

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Notes
    internal_notes: str = ""
    submission_notes: str = ""


@dataclass
class ClaimValidationError:
    """Validation error for a claim."""
    field: str
    message: str
    severity: str = "error"  # error, warning


class ClaimsService:
    """
    Claims management service.

    Handles:
    - Claim creation
    - Validation
    - Submission to payers
    - Status tracking
    - Remittance processing
    """

    def __init__(self):
        self._claims: Dict[str, Claim] = {}

        # CPT codes for validation (subset)
        self._valid_cpt_codes = {
            "99201", "99202", "99203", "99204", "99205",  # New patient
            "99211", "99212", "99213", "99214", "99215",  # Established
            "99441", "99442", "99443",  # Telehealth
            "99381", "99382", "99383", "99384", "99385", "99386", "99387",  # Preventive new
            "99391", "99392", "99393", "99394", "99395", "99396", "99397",  # Preventive est
        }

    async def create_claim(
        self,
        tenant_id: str,
        patient_id: str,
        payer_id: str,
        member_id: str,
        encounter_id: Optional[str] = None,
        claim_type: ClaimType = ClaimType.PROFESSIONAL,
    ) -> Claim:
        """Create a new claim."""
        claim = Claim(
            claim_id=str(uuid4()),
            tenant_id=tenant_id,
            patient_id=patient_id,
            payer_id=payer_id,
            member_id=member_id,
            encounter_id=encounter_id,
            claim_type=claim_type,
        )

        self._claims[claim.claim_id] = claim
        logger.info(f"Created claim: {claim.claim_id}")

        return claim

    async def add_diagnosis(
        self,
        claim_id: str,
        code: str,
        code_type: str = "ICD-10",
    ) -> Claim:
        """Add a diagnosis to a claim."""
        claim = self._claims.get(claim_id)
        if not claim:
            raise ValueError(f"Claim not found: {claim_id}")

        sequence = len(claim.diagnoses) + 1
        pointer = chr(64 + sequence)  # A, B, C, D...

        diagnosis = Diagnosis(
            code=code,
            code_type=code_type,
            sequence=sequence,
            pointer=pointer,
        )

        claim.diagnoses.append(diagnosis)
        claim.updated_at = datetime.now(timezone.utc)

        return claim

    async def add_service_line(
        self,
        claim_id: str,
        procedure_code: str,
        charge_amount: float,
        service_date: date,
        units: int = 1,
        modifiers: Optional[List[str]] = None,
        diagnosis_pointers: Optional[List[str]] = None,
        place_of_service: str = "11",
        description: str = "",
    ) -> ClaimLine:
        """Add a service line to a claim."""
        claim = self._claims.get(claim_id)
        if not claim:
            raise ValueError(f"Claim not found: {claim_id}")

        sequence = len(claim.lines) + 1

        line = ClaimLine(
            line_id=str(uuid4()),
            sequence=sequence,
            procedure_code=procedure_code,
            modifiers=modifiers or [],
            description=description,
            service_date=service_date,
            place_of_service=place_of_service,
            diagnosis_pointers=diagnosis_pointers or ["A"],
            units=units,
            charge_amount=charge_amount,
        )

        claim.lines.append(line)
        claim.total_charge = sum(l.charge_amount for l in claim.lines)
        claim.updated_at = datetime.now(timezone.utc)

        return line

    async def validate_claim(
        self,
        claim_id: str,
    ) -> List[ClaimValidationError]:
        """Validate a claim before submission."""
        claim = self._claims.get(claim_id)
        if not claim:
            raise ValueError(f"Claim not found: {claim_id}")

        errors = []

        # Required fields
        if not claim.patient_id:
            errors.append(ClaimValidationError("patient_id", "Patient is required"))
        if not claim.payer_id:
            errors.append(ClaimValidationError("payer_id", "Payer is required"))
        if not claim.member_id:
            errors.append(ClaimValidationError("member_id", "Member ID is required"))
        if not claim.billing_provider_npi:
            errors.append(ClaimValidationError("billing_provider_npi", "Billing provider NPI is required"))

        # At least one diagnosis
        if not claim.diagnoses:
            errors.append(ClaimValidationError("diagnoses", "At least one diagnosis is required"))

        # At least one service line
        if not claim.lines:
            errors.append(ClaimValidationError("lines", "At least one service line is required"))

        # Validate service lines
        for line in claim.lines:
            # Check diagnosis pointers
            for pointer in line.diagnosis_pointers:
                if not any(d.pointer == pointer for d in claim.diagnoses):
                    errors.append(ClaimValidationError(
                        f"line_{line.sequence}",
                        f"Diagnosis pointer {pointer} does not exist"
                    ))

            # Check charge amount
            if line.charge_amount <= 0:
                errors.append(ClaimValidationError(
                    f"line_{line.sequence}",
                    "Charge amount must be greater than zero"
                ))

        return errors

    async def submit_claim(
        self,
        claim_id: str,
    ) -> Claim:
        """Submit a claim to the payer."""
        claim = self._claims.get(claim_id)
        if not claim:
            raise ValueError(f"Claim not found: {claim_id}")

        # Validate first
        errors = await self.validate_claim(claim_id)
        if any(e.severity == "error" for e in errors):
            raise ValueError(f"Claim has validation errors: {errors}")

        # In production, this would send to clearinghouse
        claim.status = ClaimStatus.SUBMITTED
        claim.submitted_at = datetime.now(timezone.utc)
        claim.clearinghouse_claim_id = f"CH-{claim.claim_id[:8]}"

        logger.info(f"Submitted claim: {claim.claim_id}")
        return claim

    async def process_acknowledgment(
        self,
        claim_id: str,
        payer_claim_number: str,
        accepted: bool = True,
        rejection_reason: Optional[str] = None,
    ) -> Claim:
        """Process payer acknowledgment (277CA)."""
        claim = self._claims.get(claim_id)
        if not claim:
            raise ValueError(f"Claim not found: {claim_id}")

        claim.payer_claim_number = payer_claim_number

        if accepted:
            claim.status = ClaimStatus.ACKNOWLEDGED
        else:
            claim.status = ClaimStatus.DENIED
            claim.denial_reason = rejection_reason
            claim.denial_date = date.today()

        claim.updated_at = datetime.now(timezone.utc)
        return claim

    async def process_remittance(
        self,
        claim_id: str,
        payer_id: str,
        payment_amount: float,
        check_number: Optional[str] = None,
        line_adjudications: Optional[List[Dict[str, Any]]] = None,
    ) -> PayerRemittance:
        """Process payer remittance (835/ERA)."""
        claim = self._claims.get(claim_id)
        if not claim:
            raise ValueError(f"Claim not found: {claim_id}")

        remittance = PayerRemittance(
            remittance_id=str(uuid4()),
            claim_id=claim_id,
            payer_id=payer_id,
            check_number=check_number,
            check_date=date.today(),
            payment_amount=payment_amount,
        )

        # Process line level adjudications
        if line_adjudications:
            for adj in line_adjudications:
                line = next(
                    (l for l in claim.lines if l.sequence == adj.get("sequence")),
                    None
                )
                if line:
                    line.allowed_amount = adj.get("allowed_amount", 0)
                    line.paid_amount = adj.get("paid_amount", 0)
                    line.adjustment_amount = adj.get("adjustment_amount", 0)
                    line.patient_responsibility = adj.get("patient_responsibility", 0)
                    line.denial_reason = adj.get("denial_reason")

        # Update claim totals
        claim.total_allowed = sum(l.allowed_amount for l in claim.lines)
        claim.total_paid += payment_amount
        claim.total_adjustment = sum(l.adjustment_amount for l in claim.lines)
        claim.patient_responsibility = sum(l.patient_responsibility for l in claim.lines)

        # Update status
        if claim.total_paid >= claim.total_allowed:
            claim.status = ClaimStatus.PAID
        elif claim.total_paid > 0:
            claim.status = ClaimStatus.PARTIAL_PAID
        else:
            claim.status = ClaimStatus.DENIED

        claim.remittances.append(remittance)
        claim.updated_at = datetime.now(timezone.utc)

        logger.info(f"Processed remittance for claim: {claim_id}, paid: {payment_amount}")
        return remittance

    async def create_secondary_claim(
        self,
        claim_id: str,
    ) -> Claim:
        """Create a secondary claim after primary adjudication."""
        primary = self._claims.get(claim_id)
        if not primary:
            raise ValueError(f"Primary claim not found: {claim_id}")

        if not primary.secondary_payer_id:
            raise ValueError("No secondary payer on primary claim")

        secondary = Claim(
            claim_id=str(uuid4()),
            tenant_id=primary.tenant_id,
            patient_id=primary.patient_id,
            payer_id=primary.secondary_payer_id,
            member_id=primary.secondary_member_id or "",
            claim_type=primary.claim_type,
            encounter_id=primary.encounter_id,
            diagnoses=primary.diagnoses.copy(),
        )

        # Copy lines with patient responsibility as new charge
        for line in primary.lines:
            new_line = ClaimLine(
                line_id=str(uuid4()),
                sequence=line.sequence,
                procedure_code=line.procedure_code,
                modifiers=line.modifiers.copy(),
                description=line.description,
                service_date=line.service_date,
                place_of_service=line.place_of_service,
                diagnosis_pointers=line.diagnosis_pointers.copy(),
                units=line.units,
                charge_amount=line.patient_responsibility,
            )
            secondary.lines.append(new_line)

        secondary.total_charge = sum(l.charge_amount for l in secondary.lines)

        self._claims[secondary.claim_id] = secondary
        return secondary

    async def appeal_claim(
        self,
        claim_id: str,
        reason: str,
        supporting_documents: Optional[List[str]] = None,
    ) -> Claim:
        """Appeal a denied claim."""
        claim = self._claims.get(claim_id)
        if not claim:
            raise ValueError(f"Claim not found: {claim_id}")

        if claim.status != ClaimStatus.DENIED:
            raise ValueError("Can only appeal denied claims")

        claim.status = ClaimStatus.APPEALED
        claim.internal_notes += f"\nAppeal: {reason}"
        claim.updated_at = datetime.now(timezone.utc)

        logger.info(f"Appealed claim: {claim_id}")
        return claim

    async def void_claim(
        self,
        claim_id: str,
        reason: str,
    ) -> Claim:
        """Void a claim."""
        claim = self._claims.get(claim_id)
        if not claim:
            raise ValueError(f"Claim not found: {claim_id}")

        claim.status = ClaimStatus.VOID
        claim.internal_notes += f"\nVoided: {reason}"
        claim.updated_at = datetime.now(timezone.utc)

        logger.info(f"Voided claim: {claim_id}")
        return claim

    async def get_claim(
        self,
        claim_id: str,
    ) -> Optional[Claim]:
        """Get a claim by ID."""
        return self._claims.get(claim_id)

    async def get_patient_claims(
        self,
        tenant_id: str,
        patient_id: str,
        status: Optional[ClaimStatus] = None,
        limit: int = 50,
    ) -> List[Claim]:
        """Get claims for a patient."""
        claims = [
            c for c in self._claims.values()
            if c.tenant_id == tenant_id and c.patient_id == patient_id
        ]

        if status:
            claims = [c for c in claims if c.status == status]

        claims.sort(key=lambda c: c.created_at, reverse=True)
        return claims[:limit]

    async def get_pending_claims(
        self,
        tenant_id: str,
    ) -> List[Claim]:
        """Get claims pending submission or adjudication."""
        pending_statuses = {
            ClaimStatus.DRAFT,
            ClaimStatus.PENDING_SUBMISSION,
            ClaimStatus.SUBMITTED,
            ClaimStatus.ACKNOWLEDGED,
            ClaimStatus.IN_PROCESS,
        }

        return [
            c for c in self._claims.values()
            if c.tenant_id == tenant_id and c.status in pending_statuses
        ]

    async def get_claims_summary(
        self,
        tenant_id: str,
        date_from: date,
        date_to: date,
    ) -> Dict[str, Any]:
        """Get claims summary for a date range."""
        claims = [
            c for c in self._claims.values()
            if c.tenant_id == tenant_id
            and c.created_at.date() >= date_from
            and c.created_at.date() <= date_to
        ]

        return {
            "total_claims": len(claims),
            "total_charges": sum(c.total_charge for c in claims),
            "total_paid": sum(c.total_paid for c in claims),
            "total_pending": sum(
                c.total_charge for c in claims
                if c.status in (ClaimStatus.SUBMITTED, ClaimStatus.ACKNOWLEDGED, ClaimStatus.IN_PROCESS)
            ),
            "by_status": {
                status.value: len([c for c in claims if c.status == status])
                for status in ClaimStatus
            },
        }


# Global claims service instance
claims_service = ClaimsService()
