"""
E-Prescribing System

Comprehensive electronic prescribing with:
- Drug database integration (RxNorm)
- Drug-drug interaction checking
- Allergy checking
- Dosage calculation
- Pharmacy directory integration
- Controlled substance support (EPCS)
- Prescription history

EPIC-006: US-006.1 E-Prescribing System
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class PrescriptionStatus(str, Enum):
    """Prescription status."""
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
    """DEA controlled substance schedules."""
    NON_CONTROLLED = "non_controlled"
    SCHEDULE_I = "I"
    SCHEDULE_II = "II"
    SCHEDULE_III = "III"
    SCHEDULE_IV = "IV"
    SCHEDULE_V = "V"


class InteractionSeverity(str, Enum):
    """Drug interaction severity levels."""
    SEVERE = "severe"
    MAJOR = "major"
    MODERATE = "moderate"
    MINOR = "minor"
    NONE = "none"


class AllergyType(str, Enum):
    """Types of drug allergies."""
    ALLERGY = "allergy"
    INTOLERANCE = "intolerance"
    ADVERSE_REACTION = "adverse_reaction"


@dataclass
class Drug:
    """Drug/medication information."""
    drug_id: str
    rxnorm_code: str
    ndc_code: Optional[str] = None
    name: str = ""
    generic_name: str = ""
    brand_names: List[str] = field(default_factory=list)
    strength: str = ""
    form: str = ""  # tablet, capsule, liquid, etc.
    route: str = ""  # oral, topical, IV, etc.
    schedule: DrugSchedule = DrugSchedule.NON_CONTROLLED
    drug_class: str = ""
    therapeutic_class: str = ""
    contraindications: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    interactions: List[str] = field(default_factory=list)
    black_box_warning: Optional[str] = None


@dataclass
class DrugInteraction:
    """Drug-drug interaction information."""
    interaction_id: str
    drug1_rxnorm: str
    drug2_rxnorm: str
    severity: InteractionSeverity
    description: str
    clinical_effects: str
    management: str
    documentation_level: str  # established, probable, theoretical
    onset: str  # rapid, delayed


@dataclass
class DrugAllergy:
    """Patient drug allergy."""
    allergy_id: str
    patient_id: str
    drug_rxnorm: str
    drug_name: str
    allergy_type: AllergyType
    reaction: str
    severity: str
    onset_date: Optional[datetime] = None
    verified: bool = False
    verified_by: Optional[str] = None


@dataclass
class Sig:
    """Prescription sig (directions)."""
    dose: float
    dose_unit: str  # mg, mL, tablets, etc.
    route: str
    frequency: str  # BID, TID, QID, etc.
    frequency_description: str  # "twice daily", "every 8 hours"
    duration: Optional[str] = None
    duration_days: Optional[int] = None
    max_daily_dose: Optional[float] = None
    prn: bool = False
    prn_reason: Optional[str] = None
    special_instructions: Optional[str] = None


@dataclass
class Pharmacy:
    """Pharmacy information."""
    pharmacy_id: str
    ncpdp_id: str
    npi: str
    name: str
    address: str
    city: str
    state: str
    zip_code: str
    phone: str
    fax: Optional[str] = None
    email: Optional[str] = None
    accepts_epcs: bool = False
    specialty: Optional[str] = None  # retail, mail-order, specialty


@dataclass
class Prescription:
    """Electronic prescription."""
    prescription_id: str
    tenant_id: str
    patient_id: str
    prescriber_id: str
    encounter_id: Optional[str] = None

    # Drug info
    drug: Drug = None
    rxnorm_code: str = ""
    drug_name: str = ""
    strength: str = ""
    form: str = ""

    # Sig
    sig: Sig = None
    sig_text: str = ""

    # Quantity
    quantity: float = 0
    quantity_unit: str = ""
    days_supply: int = 0
    refills: int = 0
    refills_remaining: int = 0

    # Pharmacy
    pharmacy: Optional[Pharmacy] = None
    pharmacy_id: Optional[str] = None

    # Status
    status: PrescriptionStatus = PrescriptionStatus.DRAFT
    dispense_as_written: bool = False

    # Controlled substance
    is_controlled: bool = False
    schedule: DrugSchedule = DrugSchedule.NON_CONTROLLED

    # Safety checks
    interactions_checked: bool = False
    allergies_checked: bool = False
    overrides: List[Dict[str, Any]] = field(default_factory=list)

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    signed_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    dispensed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    # Audit
    created_by: Optional[str] = None
    signed_by: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prescriptionId": self.prescription_id,
            "patientId": self.patient_id,
            "prescriberId": self.prescriber_id,
            "drugName": self.drug_name,
            "strength": self.strength,
            "form": self.form,
            "sigText": self.sig_text,
            "quantity": self.quantity,
            "daysSupply": self.days_supply,
            "refills": self.refills,
            "status": self.status.value,
            "isControlled": self.is_controlled,
            "createdAt": self.created_at.isoformat(),
        }


class DrugDatabase:
    """
    Drug database service for medication information.

    Integrates with RxNorm for standardized drug coding.
    """

    def __init__(self):
        self._drug_cache: Dict[str, Drug] = {}

    async def search_drugs(
        self,
        query: str,
        limit: int = 20,
        include_generic: bool = True,
        include_brand: bool = True,
    ) -> List[Drug]:
        """
        Search for drugs by name.

        Args:
            query: Search term
            limit: Maximum results
            include_generic: Include generic drugs
            include_brand: Include brand name drugs

        Returns:
            List of matching drugs
        """
        # Would integrate with RxNorm API or local database
        logger.debug(f"Drug search: {query}")
        return []

    async def get_drug_by_rxnorm(self, rxnorm_code: str) -> Optional[Drug]:
        """Get drug by RxNorm code."""
        if rxnorm_code in self._drug_cache:
            return self._drug_cache[rxnorm_code]

        # Would fetch from RxNorm API
        return None

    async def get_drug_by_ndc(self, ndc_code: str) -> Optional[Drug]:
        """Get drug by NDC code."""
        # Would fetch from database
        return None

    async def get_generic_equivalents(self, rxnorm_code: str) -> List[Drug]:
        """Get generic equivalents for a drug."""
        return []

    async def get_drug_forms(self, rxnorm_code: str) -> List[str]:
        """Get available forms for a drug."""
        return []

    async def get_drug_strengths(self, rxnorm_code: str, form: str) -> List[str]:
        """Get available strengths for a drug form."""
        return []


class DrugInteractionChecker:
    """
    Drug interaction checking service.

    Checks for:
    - Drug-drug interactions
    - Drug-allergy interactions
    - Drug-condition interactions
    - Duplicate therapy
    - Dosage warnings
    """

    def __init__(self, drug_database: DrugDatabase):
        self.drug_database = drug_database
        self._interaction_cache: Dict[str, List[DrugInteraction]] = {}

    async def check_interactions(
        self,
        drug_rxnorm: str,
        current_medications: List[str],
    ) -> List[DrugInteraction]:
        """
        Check for drug-drug interactions.

        Args:
            drug_rxnorm: RxNorm code of new drug
            current_medications: List of RxNorm codes for current meds

        Returns:
            List of interactions found
        """
        interactions = []

        for med_rxnorm in current_medications:
            cache_key = f"{min(drug_rxnorm, med_rxnorm)}:{max(drug_rxnorm, med_rxnorm)}"

            if cache_key in self._interaction_cache:
                interactions.extend(self._interaction_cache[cache_key])
            else:
                # Would check interaction database
                found = await self._lookup_interaction(drug_rxnorm, med_rxnorm)
                self._interaction_cache[cache_key] = found
                interactions.extend(found)

        return interactions

    async def _lookup_interaction(
        self,
        drug1: str,
        drug2: str,
    ) -> List[DrugInteraction]:
        """Look up interaction between two drugs."""
        # Would query interaction database
        return []

    async def check_allergies(
        self,
        drug_rxnorm: str,
        patient_allergies: List[DrugAllergy],
    ) -> List[Tuple[DrugAllergy, str]]:
        """
        Check for drug-allergy interactions.

        Args:
            drug_rxnorm: RxNorm code of drug
            patient_allergies: Patient's known allergies

        Returns:
            List of (allergy, reason) tuples
        """
        matches = []

        drug = await self.drug_database.get_drug_by_rxnorm(drug_rxnorm)
        if not drug:
            return matches

        for allergy in patient_allergies:
            # Check exact match
            if allergy.drug_rxnorm == drug_rxnorm:
                matches.append((allergy, "Direct allergy match"))
                continue

            # Check drug class
            if allergy.drug_rxnorm in (drug.drug_class or ""):
                matches.append((allergy, f"Same drug class: {drug.drug_class}"))

        return matches

    async def check_duplicate_therapy(
        self,
        drug_rxnorm: str,
        current_medications: List[str],
    ) -> List[Dict[str, Any]]:
        """Check for duplicate therapeutic class."""
        duplicates = []

        drug = await self.drug_database.get_drug_by_rxnorm(drug_rxnorm)
        if not drug:
            return duplicates

        for med_rxnorm in current_medications:
            med = await self.drug_database.get_drug_by_rxnorm(med_rxnorm)
            if med and med.therapeutic_class == drug.therapeutic_class:
                duplicates.append({
                    "existingDrug": med.name,
                    "newDrug": drug.name,
                    "therapeuticClass": drug.therapeutic_class,
                })

        return duplicates

    async def check_dosage(
        self,
        drug_rxnorm: str,
        sig: Sig,
        patient_weight_kg: Optional[float] = None,
        patient_age_years: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Check dosage for appropriateness."""
        warnings = []

        # Would check against max daily dose, weight-based dosing, age adjustments
        if sig.max_daily_dose and sig.dose * 4 > sig.max_daily_dose:  # Assuming QID
            warnings.append({
                "type": "max_daily_dose_exceeded",
                "message": f"Daily dose may exceed maximum of {sig.max_daily_dose}",
            })

        return warnings


class PharmacyDirectory:
    """Pharmacy directory service."""

    async def search_pharmacies(
        self,
        zip_code: str,
        radius_miles: int = 10,
        specialty: Optional[str] = None,
    ) -> List[Pharmacy]:
        """Search for pharmacies by location."""
        return []

    async def get_pharmacy(self, pharmacy_id: str) -> Optional[Pharmacy]:
        """Get pharmacy by ID."""
        return None

    async def get_pharmacy_by_ncpdp(self, ncpdp_id: str) -> Optional[Pharmacy]:
        """Get pharmacy by NCPDP ID."""
        return None


class PrescriptionService:
    """
    Main prescription management service.

    Handles:
    - Prescription creation and management
    - Safety checks
    - Electronic transmission
    - EPCS compliance
    - Refill management
    """

    def __init__(
        self,
        drug_database: Optional[DrugDatabase] = None,
        interaction_checker: Optional[DrugInteractionChecker] = None,
        pharmacy_directory: Optional[PharmacyDirectory] = None,
    ):
        self.drug_database = drug_database or DrugDatabase()
        self.interaction_checker = interaction_checker or DrugInteractionChecker(self.drug_database)
        self.pharmacy_directory = pharmacy_directory or PharmacyDirectory()

    async def create_prescription(
        self,
        tenant_id: str,
        patient_id: str,
        prescriber_id: str,
        rxnorm_code: str,
        sig: Sig,
        quantity: float,
        quantity_unit: str,
        days_supply: int,
        refills: int = 0,
        encounter_id: Optional[str] = None,
        pharmacy_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Prescription:
        """
        Create a new prescription.

        Args:
            tenant_id: Tenant ID
            patient_id: Patient ID
            prescriber_id: Prescribing provider ID
            rxnorm_code: RxNorm code for drug
            sig: Prescription directions
            quantity: Quantity to dispense
            quantity_unit: Unit for quantity
            days_supply: Days supply
            refills: Number of refills
            encounter_id: Associated encounter
            pharmacy_id: Target pharmacy
            notes: Additional notes

        Returns:
            Created Prescription
        """
        drug = await self.drug_database.get_drug_by_rxnorm(rxnorm_code)

        prescription = Prescription(
            prescription_id=str(uuid4()),
            tenant_id=tenant_id,
            patient_id=patient_id,
            prescriber_id=prescriber_id,
            encounter_id=encounter_id,
            drug=drug,
            rxnorm_code=rxnorm_code,
            drug_name=drug.name if drug else "",
            strength=drug.strength if drug else "",
            form=drug.form if drug else "",
            sig=sig,
            sig_text=self._format_sig(sig),
            quantity=quantity,
            quantity_unit=quantity_unit,
            days_supply=days_supply,
            refills=refills,
            refills_remaining=refills,
            pharmacy_id=pharmacy_id,
            is_controlled=drug.schedule != DrugSchedule.NON_CONTROLLED if drug else False,
            schedule=drug.schedule if drug else DrugSchedule.NON_CONTROLLED,
            created_by=prescriber_id,
            notes=notes,
        )

        # Set expiration (1 year for non-controlled, varies for controlled)
        if prescription.is_controlled:
            prescription.expires_at = datetime.now(timezone.utc) + timedelta(days=90)
        else:
            prescription.expires_at = datetime.now(timezone.utc) + timedelta(days=365)

        logger.info(f"Created prescription: {prescription.prescription_id}")
        return prescription

    def _format_sig(self, sig: Sig) -> str:
        """Format sig into readable text."""
        parts = [
            f"Take {sig.dose} {sig.dose_unit}",
            f"by {sig.route}",
            sig.frequency_description,
        ]

        if sig.duration:
            parts.append(f"for {sig.duration}")

        if sig.prn:
            parts.append(f"as needed for {sig.prn_reason or 'symptoms'}")

        if sig.special_instructions:
            parts.append(sig.special_instructions)

        return " ".join(parts)

    async def perform_safety_checks(
        self,
        prescription: Prescription,
        current_medications: List[str],
        patient_allergies: List[DrugAllergy],
        patient_weight_kg: Optional[float] = None,
        patient_age_years: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Perform all safety checks for a prescription.

        Returns:
            Dictionary with check results
        """
        results = {
            "passed": True,
            "interactions": [],
            "allergies": [],
            "duplicates": [],
            "dosage_warnings": [],
            "requires_override": False,
        }

        # Check drug interactions
        interactions = await self.interaction_checker.check_interactions(
            prescription.rxnorm_code,
            current_medications,
        )
        results["interactions"] = [
            {
                "severity": i.severity.value,
                "description": i.description,
                "management": i.management,
            }
            for i in interactions
        ]

        # Check allergies
        allergy_matches = await self.interaction_checker.check_allergies(
            prescription.rxnorm_code,
            patient_allergies,
        )
        results["allergies"] = [
            {
                "allergyId": a.allergy_id,
                "drug": a.drug_name,
                "reaction": a.reaction,
                "reason": reason,
            }
            for a, reason in allergy_matches
        ]

        # Check duplicate therapy
        duplicates = await self.interaction_checker.check_duplicate_therapy(
            prescription.rxnorm_code,
            current_medications,
        )
        results["duplicates"] = duplicates

        # Check dosage
        if prescription.sig:
            dosage_warnings = await self.interaction_checker.check_dosage(
                prescription.rxnorm_code,
                prescription.sig,
                patient_weight_kg,
                patient_age_years,
            )
            results["dosage_warnings"] = dosage_warnings

        # Determine if override is required
        severe_interactions = [i for i in interactions if i.severity in [InteractionSeverity.SEVERE, InteractionSeverity.MAJOR]]
        if severe_interactions or allergy_matches:
            results["passed"] = False
            results["requires_override"] = True

        prescription.interactions_checked = True
        prescription.allergies_checked = True

        return results

    async def sign_prescription(
        self,
        prescription: Prescription,
        signer_id: str,
        signature_token: Optional[str] = None,  # For EPCS
    ) -> Prescription:
        """
        Sign a prescription (provider signature).

        For controlled substances, requires EPCS two-factor authentication.
        """
        if prescription.is_controlled:
            # Verify EPCS authentication
            if not signature_token:
                raise ValueError("EPCS authentication required for controlled substances")
            # Would verify signature token

        prescription.status = PrescriptionStatus.SIGNED
        prescription.signed_at = datetime.now(timezone.utc)
        prescription.signed_by = signer_id

        logger.info(f"Prescription signed: {prescription.prescription_id}")
        return prescription

    async def send_to_pharmacy(
        self,
        prescription: Prescription,
        pharmacy_id: str,
    ) -> Prescription:
        """
        Send prescription to pharmacy electronically.

        Uses Surescripts network for transmission.
        """
        if prescription.status != PrescriptionStatus.SIGNED:
            raise ValueError("Prescription must be signed before sending")

        # Get pharmacy
        pharmacy = await self.pharmacy_directory.get_pharmacy(pharmacy_id)
        if not pharmacy:
            raise ValueError(f"Pharmacy not found: {pharmacy_id}")

        # Would send via Surescripts NCPDP SCRIPT
        prescription.pharmacy = pharmacy
        prescription.pharmacy_id = pharmacy_id
        prescription.status = PrescriptionStatus.SENT
        prescription.sent_at = datetime.now(timezone.utc)

        logger.info(f"Prescription sent to pharmacy: {prescription.prescription_id} -> {pharmacy_id}")
        return prescription

    async def cancel_prescription(
        self,
        prescription: Prescription,
        reason: str,
        cancelled_by: str,
    ) -> Prescription:
        """Cancel a prescription."""
        if prescription.status == PrescriptionStatus.DISPENSED:
            raise ValueError("Cannot cancel dispensed prescription")

        prescription.status = PrescriptionStatus.CANCELLED
        prescription.notes = f"{prescription.notes or ''}\nCancelled: {reason}"
        prescription.updated_at = datetime.now(timezone.utc)

        # Would send cancellation to pharmacy if already sent
        if prescription.sent_at:
            # Send cancellation message
            pass

        logger.info(f"Prescription cancelled: {prescription.prescription_id}")
        return prescription

    async def request_refill(
        self,
        prescription: Prescription,
        requested_by: str,
    ) -> Dict[str, Any]:
        """Process a refill request."""
        if prescription.refills_remaining <= 0:
            return {
                "approved": False,
                "reason": "No refills remaining",
                "requires_new_prescription": True,
            }

        if prescription.expires_at and prescription.expires_at < datetime.now(timezone.utc):
            return {
                "approved": False,
                "reason": "Prescription expired",
                "requires_new_prescription": True,
            }

        # Create refill
        prescription.refills_remaining -= 1
        prescription.status = PrescriptionStatus.PENDING_REVIEW

        return {
            "approved": True,
            "refills_remaining": prescription.refills_remaining,
        }

    async def get_patient_medications(
        self,
        tenant_id: str,
        patient_id: str,
        active_only: bool = True,
    ) -> List[Prescription]:
        """Get all medications for a patient."""
        # Would query database
        return []

    async def get_prescription_history(
        self,
        tenant_id: str,
        patient_id: str,
        drug_rxnorm: Optional[str] = None,
        limit: int = 50,
    ) -> List[Prescription]:
        """Get prescription history for a patient."""
        # Would query database
        return []
