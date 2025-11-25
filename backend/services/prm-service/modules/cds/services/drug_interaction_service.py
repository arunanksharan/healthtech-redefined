"""
Drug Interaction Service

Provides drug-drug interaction checking, duplicate therapy detection,
and drug-disease contraindication checking.

EPIC-020: Clinical Decision Support
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from modules.cds.models import (
    DrugDatabase,
    DrugInteractionRule,
    DrugDiseaseContraindication,
    CDSAlert,
    InteractionSeverity,
    InteractionType,
    AlertTier,
    AlertStatus,
)
from modules.cds.schemas import (
    MedicationInput,
    DrugInteractionResult,
    DrugDiseaseResult,
    InteractionCheckResponse,
)


class DrugInteractionService:
    """Service for drug interaction checking."""

    # Severity to tier mapping
    SEVERITY_TO_TIER = {
        InteractionSeverity.CONTRAINDICATED: AlertTier.HARD_STOP,
        InteractionSeverity.MAJOR: AlertTier.HARD_STOP,
        InteractionSeverity.MODERATE: AlertTier.SOFT_STOP,
        InteractionSeverity.MINOR: AlertTier.INFORMATIONAL,
        InteractionSeverity.UNKNOWN: AlertTier.INFORMATIONAL,
    }

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def check_interactions(
        self,
        medications: List[MedicationInput],
        patient_id: UUID,
        current_medications: Optional[List[MedicationInput]] = None,
        patient_conditions: Optional[List[Dict[str, str]]] = None,
    ) -> InteractionCheckResponse:
        """
        Check for drug-drug interactions among medications.

        Args:
            medications: New medications being prescribed
            patient_id: Patient ID
            current_medications: Patient's current medication list
            patient_conditions: Patient's active conditions
        """
        all_medications = medications.copy()
        if current_medications:
            all_medications.extend(current_medications)

        drug_drug_interactions = []
        drug_disease_alerts = []
        duplicate_therapies = []

        # Check drug-drug interactions
        for i, med1 in enumerate(all_medications):
            for med2 in all_medications[i + 1:]:
                interaction = await self._check_drug_pair(med1, med2)
                if interaction:
                    drug_drug_interactions.append(interaction)

        # Check for duplicate therapies
        duplicates = await self._check_duplicate_therapy(all_medications)
        duplicate_therapies.extend(duplicates)

        # Check drug-disease contraindications
        if patient_conditions:
            for med in medications:
                for condition in patient_conditions:
                    contra = await self._check_drug_disease(med, condition)
                    if contra:
                        drug_disease_alerts.append(contra)

        # Calculate summary
        total_alerts = (
            len(drug_drug_interactions) +
            len(drug_disease_alerts) +
            len(duplicate_therapies)
        )

        has_critical = any(
            i.severity == InteractionSeverity.CONTRAINDICATED
            for i in drug_drug_interactions + drug_disease_alerts
        )
        has_major = any(
            i.severity == InteractionSeverity.MAJOR
            for i in drug_drug_interactions + drug_disease_alerts
        )

        return InteractionCheckResponse(
            patient_id=patient_id,
            checked_at=datetime.utcnow(),
            drug_drug_interactions=drug_drug_interactions,
            drug_allergy_alerts=[],  # Handled by AllergyService
            drug_disease_alerts=drug_disease_alerts,
            duplicate_therapies=duplicate_therapies,
            total_alerts=total_alerts,
            has_critical=has_critical,
            has_major=has_major,
        )

    async def _check_drug_pair(
        self,
        med1: MedicationInput,
        med2: MedicationInput,
    ) -> Optional[DrugInteractionResult]:
        """Check interaction between two drugs."""
        # Query for direct drug-drug interaction
        query = select(DrugInteractionRule).where(
            and_(
                DrugInteractionRule.tenant_id == self.tenant_id,
                DrugInteractionRule.is_active == True,
                or_(
                    and_(
                        DrugInteractionRule.drug1_rxnorm == med1.rxnorm_code,
                        DrugInteractionRule.drug2_rxnorm == med2.rxnorm_code,
                    ),
                    and_(
                        DrugInteractionRule.drug1_rxnorm == med2.rxnorm_code,
                        DrugInteractionRule.drug2_rxnorm == med1.rxnorm_code,
                    ),
                ),
            )
        )

        result = await self.db.execute(query)
        rule = result.scalar_one_or_none()

        if rule:
            return DrugInteractionResult(
                interaction_type=rule.interaction_type,
                severity=rule.severity,
                drug1=med1,
                drug2=med2,
                description=rule.description,
                clinical_effect=rule.clinical_effect,
                recommendation=rule.recommendation,
                management=rule.management,
                evidence_level=rule.evidence_level,
                references=rule.references or [],
                rule_id=rule.id,
            )

        # Check class-level interactions if no direct match
        return await self._check_class_interaction(med1, med2)

    async def _check_class_interaction(
        self,
        med1: MedicationInput,
        med2: MedicationInput,
    ) -> Optional[DrugInteractionResult]:
        """Check for class-level drug interactions."""
        # Get drug classes for both medications
        drug1_info = await self._get_drug_info(med1.rxnorm_code)
        drug2_info = await self._get_drug_info(med2.rxnorm_code)

        if not drug1_info or not drug2_info:
            return None

        # Check for class-level interaction rules
        query = select(DrugInteractionRule).where(
            and_(
                DrugInteractionRule.tenant_id == self.tenant_id,
                DrugInteractionRule.is_active == True,
                DrugInteractionRule.is_class_interaction == True,
                or_(
                    and_(
                        DrugInteractionRule.drug_class1 == drug1_info.drug_class,
                        DrugInteractionRule.drug_class2 == drug2_info.drug_class,
                    ),
                    and_(
                        DrugInteractionRule.drug_class1 == drug2_info.drug_class,
                        DrugInteractionRule.drug_class2 == drug1_info.drug_class,
                    ),
                ),
            )
        )

        result = await self.db.execute(query)
        rule = result.scalar_one_or_none()

        if rule:
            return DrugInteractionResult(
                interaction_type=rule.interaction_type,
                severity=rule.severity,
                drug1=med1,
                drug2=med2,
                description=rule.description,
                clinical_effect=rule.clinical_effect,
                recommendation=rule.recommendation,
                management=rule.management,
                evidence_level=rule.evidence_level,
                references=rule.references or [],
                rule_id=rule.id,
            )

        return None

    async def _check_duplicate_therapy(
        self,
        medications: List[MedicationInput],
    ) -> List[DrugInteractionResult]:
        """Check for duplicate therapeutic classes."""
        duplicates = []
        drug_classes: Dict[str, List[MedicationInput]] = {}

        # Group medications by therapeutic class
        for med in medications:
            drug_info = await self._get_drug_info(med.rxnorm_code)
            if drug_info and drug_info.therapeutic_class:
                if drug_info.therapeutic_class not in drug_classes:
                    drug_classes[drug_info.therapeutic_class] = []
                drug_classes[drug_info.therapeutic_class].append(med)

        # Find duplicates
        for therapeutic_class, meds in drug_classes.items():
            if len(meds) > 1:
                for i, med1 in enumerate(meds):
                    for med2 in meds[i + 1:]:
                        duplicates.append(DrugInteractionResult(
                            interaction_type=InteractionType.DUPLICATE_THERAPY,
                            severity=InteractionSeverity.MODERATE,
                            drug1=med1,
                            drug2=med2,
                            description=f"Duplicate therapy: Both medications are in the {therapeutic_class} class",
                            clinical_effect="Increased risk of adverse effects and toxicity",
                            recommendation="Review necessity of both medications",
                            management="Consider discontinuing one of the duplicate therapies",
                            evidence_level="established",
                            references=[],
                            rule_id=None,
                        ))

        return duplicates

    async def _check_drug_disease(
        self,
        medication: MedicationInput,
        condition: Dict[str, str],
    ) -> Optional[DrugDiseaseResult]:
        """Check for drug-disease contraindication."""
        query = select(DrugDiseaseContraindication).where(
            and_(
                DrugDiseaseContraindication.tenant_id == self.tenant_id,
                DrugDiseaseContraindication.is_active == True,
                DrugDiseaseContraindication.drug_rxnorm == medication.rxnorm_code,
                DrugDiseaseContraindication.condition_code == condition.get("code"),
            )
        )

        result = await self.db.execute(query)
        contra = result.scalar_one_or_none()

        if contra:
            return DrugDiseaseResult(
                severity=contra.severity,
                medication=medication,
                condition_code=contra.condition_code,
                condition_name=contra.condition_name,
                description=contra.description,
                recommendation=contra.recommendation,
            )

        # Check class-level contraindication
        drug_info = await self._get_drug_info(medication.rxnorm_code)
        if drug_info and drug_info.drug_class:
            query = select(DrugDiseaseContraindication).where(
                and_(
                    DrugDiseaseContraindication.tenant_id == self.tenant_id,
                    DrugDiseaseContraindication.is_active == True,
                    DrugDiseaseContraindication.is_class_contraindication == True,
                    DrugDiseaseContraindication.drug_class == drug_info.drug_class,
                    DrugDiseaseContraindication.condition_code == condition.get("code"),
                )
            )

            result = await self.db.execute(query)
            contra = result.scalar_one_or_none()

            if contra:
                return DrugDiseaseResult(
                    severity=contra.severity,
                    medication=medication,
                    condition_code=contra.condition_code,
                    condition_name=contra.condition_name,
                    description=contra.description,
                    recommendation=contra.recommendation,
                )

        return None

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

    async def create_alerts_from_results(
        self,
        check_response: InteractionCheckResponse,
        provider_id: UUID,
        encounter_id: Optional[UUID] = None,
        order_id: Optional[UUID] = None,
    ) -> List[CDSAlert]:
        """Create CDS alerts from interaction check results."""
        alerts = []

        # Create alerts for drug-drug interactions
        for interaction in check_response.drug_drug_interactions:
            alert = CDSAlert(
                tenant_id=self.tenant_id,
                patient_id=check_response.patient_id,
                encounter_id=encounter_id,
                provider_id=provider_id,
                order_id=order_id,
                alert_type=interaction.interaction_type,
                severity=interaction.severity,
                tier=self.SEVERITY_TO_TIER.get(interaction.severity, AlertTier.SOFT_STOP),
                status=AlertStatus.ACTIVE,
                title=f"Drug Interaction: {interaction.drug1.name or interaction.drug1.rxnorm_code} + {interaction.drug2.name or interaction.drug2.rxnorm_code}",
                message=interaction.description,
                details={
                    "clinical_effect": interaction.clinical_effect,
                    "evidence_level": interaction.evidence_level,
                },
                recommendation=interaction.recommendation,
                drug1_rxnorm=interaction.drug1.rxnorm_code,
                drug1_name=interaction.drug1.name,
                drug2_rxnorm=interaction.drug2.rxnorm_code,
                drug2_name=interaction.drug2.name,
                rule_id=interaction.rule_id,
            )
            self.db.add(alert)
            alerts.append(alert)

        # Create alerts for drug-disease contraindications
        for contra in check_response.drug_disease_alerts:
            alert = CDSAlert(
                tenant_id=self.tenant_id,
                patient_id=check_response.patient_id,
                encounter_id=encounter_id,
                provider_id=provider_id,
                order_id=order_id,
                alert_type=InteractionType.DRUG_DISEASE,
                severity=contra.severity,
                tier=self.SEVERITY_TO_TIER.get(contra.severity, AlertTier.SOFT_STOP),
                status=AlertStatus.ACTIVE,
                title=f"Drug-Disease Contraindication: {contra.medication.name or contra.medication.rxnorm_code}",
                message=contra.description,
                recommendation=contra.recommendation,
                drug1_rxnorm=contra.medication.rxnorm_code,
                drug1_name=contra.medication.name,
                condition_code=contra.condition_code,
            )
            self.db.add(alert)
            alerts.append(alert)

        await self.db.flush()
        return alerts

    async def add_interaction_rule(
        self,
        drug1_rxnorm: str,
        drug2_rxnorm: str,
        severity: InteractionSeverity,
        description: str,
        **kwargs,
    ) -> DrugInteractionRule:
        """Add a new drug interaction rule."""
        rule = DrugInteractionRule(
            tenant_id=self.tenant_id,
            drug1_rxnorm=drug1_rxnorm,
            drug2_rxnorm=drug2_rxnorm,
            interaction_type=InteractionType.DRUG_DRUG,
            severity=severity,
            description=description,
            **kwargs,
        )
        self.db.add(rule)
        await self.db.flush()
        return rule

    async def list_interaction_rules(
        self,
        severity: Optional[InteractionSeverity] = None,
        drug_rxnorm: Optional[str] = None,
        is_active: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> List[DrugInteractionRule]:
        """List drug interaction rules."""
        query = select(DrugInteractionRule).where(
            and_(
                DrugInteractionRule.tenant_id == self.tenant_id,
                DrugInteractionRule.is_active == is_active,
            )
        )

        if severity:
            query = query.where(DrugInteractionRule.severity == severity)

        if drug_rxnorm:
            query = query.where(
                or_(
                    DrugInteractionRule.drug1_rxnorm == drug_rxnorm,
                    DrugInteractionRule.drug2_rxnorm == drug_rxnorm,
                )
            )

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_interaction_rule(
        self,
        rule_id: UUID,
        **updates,
    ) -> Optional[DrugInteractionRule]:
        """Update a drug interaction rule."""
        query = select(DrugInteractionRule).where(
            and_(
                DrugInteractionRule.id == rule_id,
                DrugInteractionRule.tenant_id == self.tenant_id,
            )
        )
        result = await self.db.execute(query)
        rule = result.scalar_one_or_none()

        if rule:
            for key, value in updates.items():
                if hasattr(rule, key) and value is not None:
                    setattr(rule, key, value)
            await self.db.flush()

        return rule
