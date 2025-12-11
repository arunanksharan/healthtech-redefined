"""
Insurance Eligibility Verification

Real-time eligibility checking:
- Coverage verification
- Benefit details
- Copay/deductible information
- Prior authorization requirements
- Network status

EPIC-008: US-008.1 Eligibility Verification
"""

from datetime import datetime, timezone, date
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class EligibilityStatus(str, Enum):
    """Overall eligibility status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    TERMINATED = "terminated"
    UNKNOWN = "unknown"


class CoverageType(str, Enum):
    """Types of insurance coverage."""
    MEDICAL = "medical"
    DENTAL = "dental"
    VISION = "vision"
    PHARMACY = "pharmacy"
    MENTAL_HEALTH = "mental_health"
    SUBSTANCE_ABUSE = "substance_abuse"


class NetworkStatus(str, Enum):
    """Provider network status."""
    IN_NETWORK = "in_network"
    OUT_OF_NETWORK = "out_of_network"
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"


@dataclass
class BenefitInfo:
    """Information about a specific benefit."""
    benefit_type: str  # e.g., "office_visit", "preventive", "specialist"
    coverage_level: str  # individual, family

    # Coverage details
    covered: bool = True
    coverage_percent: float = 80.0  # Insurance covers 80%
    copay_amount: float = 0
    coinsurance_percent: float = 20.0  # Patient pays 20%

    # Limits
    visits_used: int = 0
    visits_remaining: Optional[int] = None
    visits_limit: Optional[int] = None
    dollar_limit: Optional[float] = None
    dollar_used: float = 0

    # Prior authorization
    prior_auth_required: bool = False
    prior_auth_phone: Optional[str] = None

    # Notes
    notes: str = ""


@dataclass
class DeductibleInfo:
    """Deductible information."""
    coverage_level: str  # individual, family
    network_type: NetworkStatus

    # Amounts
    amount: float = 0
    remaining: float = 0
    met: float = 0

    # Period
    period_start: Optional[date] = None
    period_end: Optional[date] = None


@dataclass
class OutOfPocketInfo:
    """Out-of-pocket maximum information."""
    coverage_level: str
    network_type: NetworkStatus

    amount: float = 0
    remaining: float = 0
    met: float = 0


@dataclass
class CoverageInfo:
    """Insurance coverage information."""
    coverage_id: str
    payer_id: str
    payer_name: str

    # Plan details
    plan_name: str = ""
    plan_type: str = ""  # HMO, PPO, EPO, POS
    group_number: Optional[str] = None
    group_name: Optional[str] = None

    # Member info
    member_id: str = ""
    subscriber_id: Optional[str] = None
    relationship_to_subscriber: str = "self"

    # Coverage period
    effective_date: Optional[date] = None
    termination_date: Optional[date] = None

    # Status
    status: EligibilityStatus = EligibilityStatus.ACTIVE
    coverage_types: List[CoverageType] = field(default_factory=list)

    # Network
    network_status: NetworkStatus = NetworkStatus.IN_NETWORK

    # Deductibles
    deductibles: List[DeductibleInfo] = field(default_factory=list)

    # Out of pocket
    out_of_pocket: List[OutOfPocketInfo] = field(default_factory=list)

    # Benefits
    benefits: Dict[str, BenefitInfo] = field(default_factory=dict)

    # Primary care
    pcp_required: bool = False
    pcp_name: Optional[str] = None
    pcp_npi: Optional[str] = None

    # Contact
    payer_phone: Optional[str] = None
    claims_address: Optional[str] = None


@dataclass
class EligibilityCheck:
    """Result of an eligibility verification check."""
    check_id: str
    tenant_id: str

    # Request info
    patient_id: str
    provider_id: Optional[str] = None
    service_type: Optional[str] = None
    service_date: date = field(default_factory=date.today)

    # Timing
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    responded_at: Optional[datetime] = None

    # Response
    status: str = "pending"  # pending, success, error
    error_message: Optional[str] = None

    # Coverage results
    primary_coverage: Optional[CoverageInfo] = None
    secondary_coverage: Optional[CoverageInfo] = None

    # Specific service eligibility
    service_eligible: bool = True
    copay_amount: float = 0
    coinsurance_percent: float = 0
    prior_auth_required: bool = False
    prior_auth_number: Optional[str] = None

    # Estimated patient responsibility
    estimated_patient_responsibility: float = 0

    # Raw response
    raw_response: Optional[Dict[str, Any]] = None


class EligibilityService:
    """
    Insurance eligibility verification service.

    Provides:
    - Real-time eligibility checks
    - Benefit verification
    - Cost estimation
    - Prior auth requirements
    """

    def __init__(self):
        self._checks: Dict[str, EligibilityCheck] = {}

        # Mock payer data (would connect to clearinghouse in production)
        self._payer_data: Dict[str, Dict[str, Any]] = {
            "BCBS": {
                "name": "Blue Cross Blue Shield",
                "plans": ["PPO", "HMO", "EPO"],
            },
            "AETNA": {
                "name": "Aetna",
                "plans": ["PPO", "HMO"],
            },
            "UHC": {
                "name": "UnitedHealthcare",
                "plans": ["PPO", "HMO", "POS"],
            },
            "CIGNA": {
                "name": "Cigna",
                "plans": ["PPO", "HMO"],
            },
            "MEDICARE": {
                "name": "Medicare",
                "plans": ["Original", "Advantage"],
            },
            "MEDICAID": {
                "name": "Medicaid",
                "plans": ["Standard"],
            },
        }

    async def verify_eligibility(
        self,
        tenant_id: str,
        patient_id: str,
        payer_id: str,
        member_id: str,
        service_type: Optional[str] = None,
        service_date: Optional[date] = None,
        provider_id: Optional[str] = None,
        provider_npi: Optional[str] = None,
    ) -> EligibilityCheck:
        """
        Verify patient insurance eligibility.

        Performs real-time eligibility check with payer.
        """
        check = EligibilityCheck(
            check_id=str(uuid4()),
            tenant_id=tenant_id,
            patient_id=patient_id,
            provider_id=provider_id,
            service_type=service_type,
            service_date=service_date or date.today(),
        )

        try:
            # In production, this would call a clearinghouse API
            # For now, generate mock response
            coverage = await self._mock_eligibility_check(
                payer_id, member_id, service_type, provider_npi
            )

            check.status = "success"
            check.responded_at = datetime.now(timezone.utc)
            check.primary_coverage = coverage

            # Calculate estimates
            if service_type and service_type in coverage.benefits:
                benefit = coverage.benefits[service_type]
                check.service_eligible = benefit.covered
                check.copay_amount = benefit.copay_amount
                check.coinsurance_percent = benefit.coinsurance_percent
                check.prior_auth_required = benefit.prior_auth_required

                # Estimate patient responsibility
                check.estimated_patient_responsibility = await self._estimate_patient_cost(
                    coverage, service_type
                )

        except Exception as e:
            check.status = "error"
            check.error_message = str(e)
            check.responded_at = datetime.now(timezone.utc)
            logger.error(f"Eligibility check failed: {e}")

        self._checks[check.check_id] = check
        return check

    async def _mock_eligibility_check(
        self,
        payer_id: str,
        member_id: str,
        service_type: Optional[str],
        provider_npi: Optional[str],
    ) -> CoverageInfo:
        """Generate mock eligibility response."""
        payer = self._payer_data.get(payer_id, {})

        coverage = CoverageInfo(
            coverage_id=str(uuid4()),
            payer_id=payer_id,
            payer_name=payer.get("name", payer_id),
            plan_name=f"{payer.get('name', payer_id)} PPO",
            plan_type="PPO",
            member_id=member_id,
            status=EligibilityStatus.ACTIVE,
            effective_date=date(2024, 1, 1),
            network_status=NetworkStatus.IN_NETWORK,
            coverage_types=[CoverageType.MEDICAL, CoverageType.PHARMACY],
        )

        # Add deductibles
        coverage.deductibles = [
            DeductibleInfo(
                coverage_level="individual",
                network_type=NetworkStatus.IN_NETWORK,
                amount=1500,
                remaining=750,
                met=750,
            ),
            DeductibleInfo(
                coverage_level="family",
                network_type=NetworkStatus.IN_NETWORK,
                amount=3000,
                remaining=1500,
                met=1500,
            ),
        ]

        # Add out of pocket
        coverage.out_of_pocket = [
            OutOfPocketInfo(
                coverage_level="individual",
                network_type=NetworkStatus.IN_NETWORK,
                amount=6000,
                remaining=4500,
                met=1500,
            ),
        ]

        # Add benefits
        coverage.benefits = {
            "office_visit": BenefitInfo(
                benefit_type="office_visit",
                coverage_level="individual",
                covered=True,
                copay_amount=25,
                coinsurance_percent=0,
            ),
            "specialist": BenefitInfo(
                benefit_type="specialist",
                coverage_level="individual",
                covered=True,
                copay_amount=50,
                coinsurance_percent=0,
            ),
            "preventive": BenefitInfo(
                benefit_type="preventive",
                coverage_level="individual",
                covered=True,
                copay_amount=0,
                coverage_percent=100,
            ),
            "telehealth": BenefitInfo(
                benefit_type="telehealth",
                coverage_level="individual",
                covered=True,
                copay_amount=0,
                coinsurance_percent=20,
            ),
            "lab": BenefitInfo(
                benefit_type="lab",
                coverage_level="individual",
                covered=True,
                copay_amount=0,
                coinsurance_percent=20,
            ),
            "imaging": BenefitInfo(
                benefit_type="imaging",
                coverage_level="individual",
                covered=True,
                copay_amount=0,
                coinsurance_percent=20,
                prior_auth_required=True,
            ),
            "surgery": BenefitInfo(
                benefit_type="surgery",
                coverage_level="individual",
                covered=True,
                copay_amount=0,
                coinsurance_percent=20,
                prior_auth_required=True,
            ),
        }

        return coverage

    async def _estimate_patient_cost(
        self,
        coverage: CoverageInfo,
        service_type: str,
        estimated_charge: float = 200,
    ) -> float:
        """Estimate patient out-of-pocket cost."""
        benefit = coverage.benefits.get(service_type)
        if not benefit:
            return estimated_charge

        # Start with copay
        patient_cost = benefit.copay_amount

        # Add coinsurance if applicable
        if benefit.coinsurance_percent > 0:
            # Check if deductible is met
            deductible = next(
                (d for d in coverage.deductibles
                 if d.coverage_level == "individual"
                 and d.network_type == coverage.network_status),
                None
            )

            if deductible and deductible.remaining > 0:
                # Patient pays toward deductible first
                deductible_portion = min(deductible.remaining, estimated_charge)
                remaining_charge = estimated_charge - deductible_portion
                patient_cost += deductible_portion + (remaining_charge * benefit.coinsurance_percent / 100)
            else:
                # Deductible met, only coinsurance
                patient_cost += estimated_charge * benefit.coinsurance_percent / 100

        return round(patient_cost, 2)

    async def check_prior_auth_required(
        self,
        payer_id: str,
        service_type: str,
        procedure_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Check if prior authorization is required for a service."""
        # In production, check payer rules
        requires_auth = service_type in ("imaging", "surgery", "dme", "specialty_drugs")

        return {
            "prior_auth_required": requires_auth,
            "payer_id": payer_id,
            "service_type": service_type,
            "procedure_code": procedure_code,
            "auth_phone": "1-800-555-0100" if requires_auth else None,
            "estimated_turnaround_days": 3 if requires_auth else 0,
        }

    async def get_eligibility_check(
        self,
        check_id: str,
    ) -> Optional[EligibilityCheck]:
        """Get an eligibility check by ID."""
        return self._checks.get(check_id)

    async def get_patient_checks(
        self,
        tenant_id: str,
        patient_id: str,
        limit: int = 10,
    ) -> List[EligibilityCheck]:
        """Get recent eligibility checks for a patient."""
        checks = [
            c for c in self._checks.values()
            if c.tenant_id == tenant_id and c.patient_id == patient_id
        ]
        checks.sort(key=lambda c: c.requested_at, reverse=True)
        return checks[:limit]

    async def batch_verify(
        self,
        tenant_id: str,
        verifications: List[Dict[str, Any]],
    ) -> List[EligibilityCheck]:
        """Verify eligibility for multiple patients."""
        results = []
        for v in verifications:
            check = await self.verify_eligibility(
                tenant_id=tenant_id,
                patient_id=v["patient_id"],
                payer_id=v["payer_id"],
                member_id=v["member_id"],
                service_type=v.get("service_type"),
                provider_id=v.get("provider_id"),
            )
            results.append(check)
        return results


# Global eligibility service instance
eligibility_service = EligibilityService()
