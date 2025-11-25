"""
Drug-Allergy Service

Provides drug-allergy checking with cross-reactivity detection
and alternative medication suggestions.

EPIC-020: Clinical Decision Support
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from modules.cds.models import (
    DrugDatabase,
    DrugAllergyMapping,
    CDSAlert,
    InteractionSeverity,
    InteractionType,
    AlertTier,
    AlertStatus,
)
from modules.cds.schemas import (
    MedicationInput,
    DrugAllergyResult,
)


class AllergyService:
    """Service for drug-allergy checking."""

    # Cross-reactivity risk levels
    CROSS_REACTIVITY_THRESHOLDS = {
        "high": 0.5,      # >50% cross-reactivity
        "moderate": 0.1,  # 10-50% cross-reactivity
        "low": 0.01,      # 1-10% cross-reactivity
    }

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def check_allergies(
        self,
        medications: List[MedicationInput],
        patient_allergies: List[Dict[str, Any]],
    ) -> List[DrugAllergyResult]:
        """
        Check medications against patient allergies.

        Args:
            medications: Medications to check
            patient_allergies: Patient's documented allergies
                Each allergy should have: code, name, reaction_type, severity
        """
        alerts = []

        for medication in medications:
            for allergy in patient_allergies:
                result = await self._check_allergy_conflict(medication, allergy)
                if result:
                    alerts.append(result)

        return alerts

    async def _check_allergy_conflict(
        self,
        medication: MedicationInput,
        allergy: Dict[str, Any],
    ) -> Optional[DrugAllergyResult]:
        """Check if a medication conflicts with a specific allergy."""
        allergy_code = allergy.get("code", "")
        allergy_name = allergy.get("name", "")
        reaction_type = allergy.get("reaction_type", "allergy")
        reaction_severity = allergy.get("severity", "unknown")

        # Direct match - medication is the allergen
        if await self._is_direct_match(medication.rxnorm_code, allergy_code):
            return DrugAllergyResult(
                severity=InteractionSeverity.CONTRAINDICATED,
                medication=medication,
                allergy_code=allergy_code,
                allergy_name=allergy_name,
                reaction_type=reaction_type,
                is_cross_reactive=False,
                recommendation=f"Patient has documented {reaction_type} to this medication. Consider alternative therapy.",
                alternative_medications=await self._get_alternatives(medication.rxnorm_code),
            )

        # Check cross-reactivity
        cross_reactivity = await self._check_cross_reactivity(
            medication.rxnorm_code, allergy_code
        )

        if cross_reactivity:
            severity = self._get_cross_reactivity_severity(
                cross_reactivity["risk"], reaction_severity
            )

            return DrugAllergyResult(
                severity=severity,
                medication=medication,
                allergy_code=allergy_code,
                allergy_name=allergy_name,
                reaction_type=reaction_type,
                is_cross_reactive=True,
                cross_reactivity_info=cross_reactivity["info"],
                recommendation=cross_reactivity["recommendation"],
                alternative_medications=await self._get_alternatives(medication.rxnorm_code),
            )

        return None

    async def _is_direct_match(
        self,
        medication_rxnorm: str,
        allergy_code: str,
    ) -> bool:
        """Check if medication directly matches the allergen."""
        # Check if allergy code matches medication RxNorm
        if medication_rxnorm == allergy_code:
            return True

        # Check if allergy is to a drug class that includes this medication
        drug_info = await self._get_drug_info(medication_rxnorm)
        if drug_info and drug_info.allergy_class_codes:
            if allergy_code in drug_info.allergy_class_codes:
                return True

        return False

    async def _check_cross_reactivity(
        self,
        medication_rxnorm: str,
        allergy_code: str,
    ) -> Optional[Dict[str, Any]]:
        """Check for cross-reactivity between medication and allergen."""
        # Get allergy mapping for the medication
        query = select(DrugAllergyMapping).where(
            and_(
                DrugAllergyMapping.tenant_id == self.tenant_id,
                DrugAllergyMapping.is_active == True,
                DrugAllergyMapping.drug_rxnorm == medication_rxnorm,
            )
        )

        result = await self.db.execute(query)
        mapping = result.scalar_one_or_none()

        if not mapping:
            return None

        # Check if allergen is in cross-reactive drugs
        if allergy_code in (mapping.cross_reactive_drugs or []):
            return {
                "risk": mapping.cross_reactivity_risk,
                "info": f"Cross-reactivity with {mapping.allergy_class_name} class. "
                        f"Risk level: {mapping.cross_reactivity_risk}",
                "recommendation": self._get_cross_reactivity_recommendation(
                    mapping.cross_reactivity_risk
                ),
            }

        # Check class-level cross-reactivity
        if mapping.allergy_class_code == allergy_code:
            return {
                "risk": mapping.cross_reactivity_risk,
                "info": f"Medication belongs to {mapping.allergy_class_name} class",
                "recommendation": self._get_cross_reactivity_recommendation(
                    mapping.cross_reactivity_risk
                ),
            }

        return None

    def _get_cross_reactivity_severity(
        self,
        risk_level: str,
        reaction_severity: str,
    ) -> InteractionSeverity:
        """Determine alert severity based on cross-reactivity and reaction history."""
        # High risk + severe reaction = contraindicated
        if risk_level == "high" and reaction_severity in ["severe", "anaphylaxis"]:
            return InteractionSeverity.CONTRAINDICATED

        # High risk or severe reaction = major
        if risk_level == "high" or reaction_severity in ["severe", "anaphylaxis"]:
            return InteractionSeverity.MAJOR

        # Moderate risk = moderate
        if risk_level == "moderate":
            return InteractionSeverity.MODERATE

        # Low risk = minor
        return InteractionSeverity.MINOR

    def _get_cross_reactivity_recommendation(self, risk_level: str) -> str:
        """Get recommendation based on cross-reactivity risk."""
        recommendations = {
            "high": "High cross-reactivity risk. Consider alternative medication. "
                   "If no alternative available, use with caution and monitor closely.",
            "moderate": "Moderate cross-reactivity risk. Use with caution. "
                       "Consider skin testing or graded challenge if benefit outweighs risk.",
            "low": "Low cross-reactivity risk. May use with appropriate monitoring. "
                  "Ensure patient is informed and watch for reaction signs.",
        }
        return recommendations.get(risk_level, "Cross-reactivity possible. Use clinical judgment.")

    async def _get_drug_info(self, rxnorm_code: str) -> Optional[DrugDatabase]:
        """Get drug information from database."""
        query = select(DrugDatabase).where(
            and_(
                DrugDatabase.tenant_id == self.tenant_id,
                DrugDatabase.rxnorm_code == rxnorm_code,
                DrugDatabase.is_active == True,
            )
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_alternatives(
        self,
        medication_rxnorm: str,
        max_alternatives: int = 5,
    ) -> List[MedicationInput]:
        """Get alternative medications in the same therapeutic class."""
        drug_info = await self._get_drug_info(medication_rxnorm)
        if not drug_info or not drug_info.therapeutic_class:
            return []

        # Find other drugs in the same therapeutic class
        query = select(DrugDatabase).where(
            and_(
                DrugDatabase.tenant_id == self.tenant_id,
                DrugDatabase.therapeutic_class == drug_info.therapeutic_class,
                DrugDatabase.rxnorm_code != medication_rxnorm,
                DrugDatabase.is_active == True,
            )
        ).limit(max_alternatives)

        result = await self.db.execute(query)
        alternatives = result.scalars().all()

        return [
            MedicationInput(
                rxnorm_code=alt.rxnorm_code,
                name=alt.name,
            )
            for alt in alternatives
        ]

    async def add_allergy_mapping(
        self,
        drug_rxnorm: str,
        allergy_class_code: str,
        allergy_class_name: str,
        cross_reactive_drugs: List[str] = None,
        cross_reactivity_risk: str = "unknown",
        **kwargs,
    ) -> DrugAllergyMapping:
        """Add a new drug-allergy mapping."""
        mapping = DrugAllergyMapping(
            tenant_id=self.tenant_id,
            drug_rxnorm=drug_rxnorm,
            allergy_class_code=allergy_class_code,
            allergy_class_name=allergy_class_name,
            cross_reactive_drugs=cross_reactive_drugs or [],
            cross_reactivity_risk=cross_reactivity_risk,
            **kwargs,
        )
        self.db.add(mapping)
        await self.db.flush()
        return mapping

    async def get_allergy_mappings(
        self,
        drug_rxnorm: Optional[str] = None,
        allergy_class_code: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[DrugAllergyMapping]:
        """Get allergy mappings with optional filters."""
        query = select(DrugAllergyMapping).where(
            and_(
                DrugAllergyMapping.tenant_id == self.tenant_id,
                DrugAllergyMapping.is_active == True,
            )
        )

        if drug_rxnorm:
            query = query.where(DrugAllergyMapping.drug_rxnorm == drug_rxnorm)

        if allergy_class_code:
            query = query.where(DrugAllergyMapping.allergy_class_code == allergy_class_code)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_allergy_alerts(
        self,
        allergy_results: List[DrugAllergyResult],
        patient_id: UUID,
        provider_id: UUID,
        encounter_id: Optional[UUID] = None,
        order_id: Optional[UUID] = None,
    ) -> List[CDSAlert]:
        """Create CDS alerts from allergy check results."""
        alerts = []

        severity_to_tier = {
            InteractionSeverity.CONTRAINDICATED: AlertTier.HARD_STOP,
            InteractionSeverity.MAJOR: AlertTier.HARD_STOP,
            InteractionSeverity.MODERATE: AlertTier.SOFT_STOP,
            InteractionSeverity.MINOR: AlertTier.INFORMATIONAL,
        }

        for result in allergy_results:
            cross_info = " (cross-reactivity)" if result.is_cross_reactive else ""

            alert = CDSAlert(
                tenant_id=self.tenant_id,
                patient_id=patient_id,
                encounter_id=encounter_id,
                provider_id=provider_id,
                order_id=order_id,
                alert_type=InteractionType.DRUG_ALLERGY,
                severity=result.severity,
                tier=severity_to_tier.get(result.severity, AlertTier.SOFT_STOP),
                status=AlertStatus.ACTIVE,
                title=f"Drug-Allergy Alert{cross_info}: {result.medication.name or result.medication.rxnorm_code}",
                message=f"Patient has documented allergy to {result.allergy_name}. {result.cross_reactivity_info or ''}",
                details={
                    "reaction_type": result.reaction_type,
                    "is_cross_reactive": result.is_cross_reactive,
                    "alternatives": [alt.dict() for alt in result.alternative_medications],
                },
                recommendation=result.recommendation,
                drug1_rxnorm=result.medication.rxnorm_code,
                drug1_name=result.medication.name,
                allergy_code=result.allergy_code,
            )
            self.db.add(alert)
            alerts.append(alert)

        await self.db.flush()
        return alerts

    async def check_previously_tolerated(
        self,
        medication_rxnorm: str,
        patient_id: UUID,
        allergy_code: str,
    ) -> bool:
        """Check if patient has previously tolerated the medication despite allergy."""
        # This would query medication administration records
        # to see if patient received and tolerated the medication
        # Implementation depends on integration with medication records
        return False

    async def get_desensitization_protocols(
        self,
        medication_rxnorm: str,
        allergy_code: str,
    ) -> Optional[Dict[str, Any]]:
        """Get desensitization protocol if available for the drug/allergy combination."""
        # Would return standardized desensitization protocols
        # Common for medications like aspirin, chemotherapy agents, etc.
        return None
