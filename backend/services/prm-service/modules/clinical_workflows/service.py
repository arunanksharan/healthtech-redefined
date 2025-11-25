"""
Clinical Workflows Service

Business logic layer for clinical workflow operations.
Integrates with shared clinical modules and FHIR services.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID, uuid4
import logging

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

# Import models
from .models import (
    Prescription, DrugInteractionCheck,
    LabOrder, LabResult,
    ImagingOrder, ImagingStudy, RadiologyReport,
    Referral, ReferralDocument, ReferralMessage,
    ClinicalNote, NoteTemplate, SmartPhrase,
    CarePlan, CareGoal, GoalProgress, CareIntervention, CareTeamMember,
    ClinicalAlert, CDSRule,
    VitalSign, EarlyWarningScore,
    DischargeRecord,
)

# Import schemas
from .schemas import (
    PrescriptionCreate, LabOrderCreate, ImagingOrderCreate,
    ReferralCreate, ClinicalNoteCreate, CarePlanCreate,
    VitalSignCreate, DischargeRecordCreate,
    InteractionSeverity, OrderPriority, AlertSeverity, AlertCategory,
)

logger = logging.getLogger(__name__)


class PrescriptionService:
    """E-Prescribing service with drug interaction checking."""

    # Mock RxNorm drug database (in production, integrate with actual database)
    DRUG_DATABASE = {
        "198440": {"name": "Lisinopril 10mg tablet", "generic": "lisinopril", "class": "ACE inhibitor", "schedule": None},
        "197884": {"name": "Metformin 500mg tablet", "generic": "metformin", "class": "Biguanide", "schedule": None},
        "312961": {"name": "Oxycodone 5mg tablet", "generic": "oxycodone", "class": "Opioid", "schedule": "II"},
        "197517": {"name": "Atorvastatin 20mg tablet", "generic": "atorvastatin", "class": "Statin", "schedule": None},
        "311026": {"name": "Amoxicillin 500mg capsule", "generic": "amoxicillin", "class": "Antibiotic", "schedule": None},
        "853538": {"name": "Alprazolam 0.5mg tablet", "generic": "alprazolam", "class": "Benzodiazepine", "schedule": "IV"},
    }

    # Drug interaction matrix (simplified)
    INTERACTIONS = {
        ("198440", "312961"): {"severity": "major", "description": "ACE inhibitors may increase opioid effects"},
        ("197884", "312961"): {"severity": "moderate", "description": "Possible enhanced hypoglycemic effect"},
        ("853538", "312961"): {"severity": "severe", "description": "CNS depression risk - avoid combination"},
    }

    async def create_prescription(
        self,
        db: Session,
        data: PrescriptionCreate,
    ) -> Prescription:
        """Create a new prescription."""
        # Build sig text from components
        sig_text = f"Take {data.sig.dose} {data.sig.dose_unit} by {data.sig.route} {data.sig.frequency}"
        if data.sig.duration:
            sig_text += f" for {data.sig.duration}"
        if data.sig.as_needed:
            sig_text += f" as needed for {data.sig.as_needed_reason or 'symptoms'}"

        # Look up drug info
        drug_info = self.DRUG_DATABASE.get(data.rxnorm_code, {})
        is_controlled = drug_info.get("schedule") is not None
        dea_schedule = drug_info.get("schedule")

        prescription = Prescription(
            id=uuid4(),
            tenant_id=data.tenant_id,
            patient_id=data.patient_id,
            prescriber_id=data.prescriber_id,
            encounter_id=data.encounter_id,
            rxnorm_code=data.rxnorm_code,
            drug_name=data.drug_name,
            strength=data.strength,
            form=data.form,
            sig_text=sig_text,
            dose=data.sig.dose,
            dose_unit=data.sig.dose_unit,
            route=data.sig.route,
            frequency=data.sig.frequency,
            duration=data.sig.duration,
            duration_days=data.sig.duration_days,
            as_needed=data.sig.as_needed,
            as_needed_reason=data.sig.as_needed_reason,
            special_instructions=data.sig.special_instructions,
            quantity=data.quantity,
            quantity_unit=data.quantity_unit,
            days_supply=data.days_supply,
            refills=data.refills,
            refills_remaining=data.refills,
            pharmacy_id=data.pharmacy_id,
            dispense_as_written=data.dispense_as_written,
            is_controlled=is_controlled,
            dea_schedule=dea_schedule,
            notes=data.notes,
            expires_at=datetime.now(timezone.utc) + timedelta(days=365 if not is_controlled else 90),
        )

        db.add(prescription)
        db.commit()
        db.refresh(prescription)

        logger.info(f"Created prescription {prescription.id} for patient {data.patient_id}")
        return prescription

    async def check_interactions(
        self,
        db: Session,
        tenant_id: UUID,
        patient_id: UUID,
        rxnorm_code: str,
        current_medications: List[str],
    ) -> Dict[str, Any]:
        """Check drug interactions against current medications."""
        interactions = []
        has_severe = False

        for med_code in current_medications:
            # Check both directions
            key1 = (rxnorm_code, med_code)
            key2 = (med_code, rxnorm_code)

            interaction = self.INTERACTIONS.get(key1) or self.INTERACTIONS.get(key2)
            if interaction:
                interactions.append({
                    "drug1": rxnorm_code,
                    "drug2": med_code,
                    "severity": interaction["severity"],
                    "description": interaction["description"],
                })
                if interaction["severity"] == "severe":
                    has_severe = True

        # Check for duplicate therapy
        duplicates = []
        new_drug_class = self.DRUG_DATABASE.get(rxnorm_code, {}).get("class")
        for med_code in current_medications:
            existing_class = self.DRUG_DATABASE.get(med_code, {}).get("class")
            if new_drug_class and existing_class and new_drug_class == existing_class:
                duplicates.append({
                    "drug1": rxnorm_code,
                    "drug2": med_code,
                    "class": new_drug_class,
                })

        # TODO: Check allergies against patient's allergy list

        return {
            "has_interactions": len(interactions) > 0,
            "interactions": interactions,
            "has_allergies": False,  # Would check patient allergies
            "allergy_matches": [],
            "has_duplicates": len(duplicates) > 0,
            "duplicates": duplicates,
            "requires_override": has_severe,
        }

    async def sign_prescription(
        self,
        db: Session,
        prescription_id: UUID,
        signer_id: UUID,
    ) -> Prescription:
        """Sign and finalize a prescription."""
        prescription = db.query(Prescription).filter(
            Prescription.id == prescription_id
        ).first()

        if not prescription:
            raise ValueError("Prescription not found")

        prescription.status = "signed"
        prescription.signed_at = datetime.now(timezone.utc)
        prescription.signed_by = signer_id

        db.commit()
        db.refresh(prescription)

        logger.info(f"Prescription {prescription_id} signed by {signer_id}")
        return prescription

    async def send_to_pharmacy(
        self,
        db: Session,
        prescription_id: UUID,
        pharmacy_id: str,
        pharmacy_ncpdp: Optional[str] = None,
    ) -> Prescription:
        """Send prescription to pharmacy via e-prescribing network."""
        prescription = db.query(Prescription).filter(
            Prescription.id == prescription_id
        ).first()

        if not prescription:
            raise ValueError("Prescription not found")
        if prescription.status != "signed":
            raise ValueError("Prescription must be signed before sending")

        # In production, integrate with Surescripts or similar
        prescription.pharmacy_id = pharmacy_id
        prescription.pharmacy_ncpdp = pharmacy_ncpdp
        prescription.status = "sent"
        prescription.sent_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(prescription)

        logger.info(f"Prescription {prescription_id} sent to pharmacy {pharmacy_id}")
        return prescription

    async def get_patient_prescriptions(
        self,
        db: Session,
        tenant_id: UUID,
        patient_id: UUID,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Prescription], int]:
        """Get prescriptions for a patient."""
        query = db.query(Prescription).filter(
            Prescription.tenant_id == tenant_id,
            Prescription.patient_id == patient_id,
        )

        if status:
            query = query.filter(Prescription.status == status)

        total = query.count()
        prescriptions = query.order_by(
            desc(Prescription.created_at)
        ).offset((page - 1) * page_size).limit(page_size).all()

        return prescriptions, total


class LabOrderService:
    """Laboratory order management service."""

    async def create_order(
        self,
        db: Session,
        data: LabOrderCreate,
    ) -> LabOrder:
        """Create a new lab order."""
        tests_data = [
            {"loinc_code": t.loinc_code, "test_name": t.test_name, "cpt_code": t.cpt_code}
            for t in data.tests
        ]

        order = LabOrder(
            id=uuid4(),
            tenant_id=data.tenant_id,
            patient_id=data.patient_id,
            ordering_provider_id=data.ordering_provider_id,
            encounter_id=data.encounter_id,
            tests=tests_data,
            priority=data.priority.value,
            diagnosis_codes=data.diagnosis_codes,
            clinical_indication=data.clinical_indication,
            fasting_required=data.fasting_required,
            scheduled_date=data.scheduled_date,
            notes=data.notes,
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        logger.info(f"Created lab order {order.id} for patient {data.patient_id}")
        return order

    async def submit_order(
        self,
        db: Session,
        order_id: UUID,
    ) -> LabOrder:
        """Submit order to performing lab."""
        order = db.query(LabOrder).filter(LabOrder.id == order_id).first()
        if not order:
            raise ValueError("Lab order not found")

        # In production, would send HL7 ORM message to lab
        order.status = "ordered"
        order.ordered_at = datetime.now(timezone.utc)
        order.lab_order_number = f"LAB-{uuid4().hex[:8].upper()}"

        db.commit()
        db.refresh(order)

        logger.info(f"Lab order {order_id} submitted")
        return order

    async def record_specimen_collection(
        self,
        db: Session,
        order_id: UUID,
        collected_by: UUID,
        collection_time: Optional[datetime] = None,
    ) -> LabOrder:
        """Record specimen collection."""
        order = db.query(LabOrder).filter(LabOrder.id == order_id).first()
        if not order:
            raise ValueError("Lab order not found")

        order.status = "specimen_collected"
        order.collected_at = collection_time or datetime.now(timezone.utc)

        db.commit()
        db.refresh(order)

        return order

    async def record_results(
        self,
        db: Session,
        order_id: UUID,
        results: List[Dict[str, Any]],
    ) -> List[LabResult]:
        """Record lab results for an order."""
        order = db.query(LabOrder).filter(LabOrder.id == order_id).first()
        if not order:
            raise ValueError("Lab order not found")

        result_records = []
        has_critical = False

        for result_data in results:
            # Determine if abnormal/critical
            value_numeric = result_data.get("value_numeric")
            ref_low = result_data.get("reference_low")
            ref_high = result_data.get("reference_high")

            is_abnormal = False
            is_critical = result_data.get("is_critical", False)
            interpretation = "N"

            if value_numeric is not None:
                if ref_low is not None and value_numeric < ref_low:
                    is_abnormal = True
                    interpretation = "LL" if is_critical else "L"
                elif ref_high is not None and value_numeric > ref_high:
                    is_abnormal = True
                    interpretation = "HH" if is_critical else "H"

            if is_critical:
                has_critical = True

            result = LabResult(
                id=uuid4(),
                order_id=order_id,
                tenant_id=order.tenant_id,
                patient_id=order.patient_id,
                loinc_code=result_data["loinc_code"],
                test_name=result_data["test_name"],
                value=result_data.get("value"),
                value_numeric=value_numeric,
                units=result_data.get("units"),
                reference_low=ref_low,
                reference_high=ref_high,
                reference_text=result_data.get("reference_text"),
                interpretation=interpretation,
                is_abnormal=is_abnormal,
                is_critical=is_critical,
                status=result_data.get("status", "final"),
                resulted_by=result_data.get("resulted_by"),
                notes=result_data.get("notes"),
            )
            db.add(result)
            result_records.append(result)

        order.status = "resulted"
        order.resulted_at = datetime.now(timezone.utc)
        order.has_critical_results = has_critical

        db.commit()

        for r in result_records:
            db.refresh(r)

        logger.info(f"Recorded {len(result_records)} results for order {order_id}")
        return result_records

    async def get_result_trends(
        self,
        db: Session,
        tenant_id: UUID,
        patient_id: UUID,
        loinc_code: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get historical trend for a lab test."""
        results = db.query(LabResult).filter(
            LabResult.tenant_id == tenant_id,
            LabResult.patient_id == patient_id,
            LabResult.loinc_code == loinc_code,
        ).order_by(desc(LabResult.resulted_at)).limit(limit).all()

        return [
            {
                "date": r.resulted_at.isoformat(),
                "value": r.value_numeric or r.value,
                "unit": r.units,
                "interpretation": r.interpretation,
            }
            for r in reversed(results)
        ]


class ImagingService:
    """Imaging workflow management service."""

    async def create_order(
        self,
        db: Session,
        data: ImagingOrderCreate,
    ) -> ImagingOrder:
        """Create an imaging order."""
        order = ImagingOrder(
            id=uuid4(),
            tenant_id=data.tenant_id,
            patient_id=data.patient_id,
            ordering_provider_id=data.ordering_provider_id,
            encounter_id=data.encounter_id,
            procedure_code=data.procedure_code,
            procedure_name=data.procedure_name,
            modality=data.modality.value,
            body_part=data.body_part,
            laterality=data.laterality,
            priority=data.priority.value,
            clinical_indication=data.clinical_indication,
            diagnosis_codes=data.diagnosis_codes,
            contrast_required=data.contrast_required,
            notes=data.notes,
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        logger.info(f"Created imaging order {order.id}")
        return order

    async def schedule_order(
        self,
        db: Session,
        order_id: UUID,
        scheduled_datetime: datetime,
        location: str,
    ) -> ImagingOrder:
        """Schedule imaging appointment."""
        order = db.query(ImagingOrder).filter(ImagingOrder.id == order_id).first()
        if not order:
            raise ValueError("Imaging order not found")

        order.scheduled_datetime = scheduled_datetime
        order.performing_location = location
        order.status = "scheduled"

        db.commit()
        db.refresh(order)

        return order

    async def record_study(
        self,
        db: Session,
        order_id: UUID,
        accession_number: str,
        study_instance_uid: str,
        study_data: Dict[str, Any],
    ) -> ImagingStudy:
        """Record completed imaging study."""
        order = db.query(ImagingOrder).filter(ImagingOrder.id == order_id).first()
        if not order:
            raise ValueError("Imaging order not found")

        study = ImagingStudy(
            id=uuid4(),
            order_id=order_id,
            tenant_id=order.tenant_id,
            patient_id=order.patient_id,
            accession_number=accession_number,
            study_instance_uid=study_instance_uid,
            modality=order.modality,
            study_description=study_data.get("description"),
            body_part=order.body_part,
            num_series=study_data.get("num_series", 0),
            num_images=study_data.get("num_images", 0),
            radiation_dose_msv=study_data.get("radiation_dose_msv"),
            pacs_url=study_data.get("pacs_url"),
        )

        order.status = "completed"

        db.add(study)
        db.commit()
        db.refresh(study)

        return study

    async def get_cumulative_dose(
        self,
        db: Session,
        tenant_id: UUID,
        patient_id: UUID,
        months: int = 12,
    ) -> Dict[str, Any]:
        """Get cumulative radiation dose for patient."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=months * 30)

        studies = db.query(ImagingStudy).filter(
            ImagingStudy.tenant_id == tenant_id,
            ImagingStudy.patient_id == patient_id,
            ImagingStudy.study_datetime >= cutoff,
            ImagingStudy.radiation_dose_msv.isnot(None),
        ).all()

        total_dose = sum(s.radiation_dose_msv or 0 for s in studies)

        return {
            "total_dose_msv": round(total_dose, 2),
            "studies_count": len(studies),
            "period_months": months,
        }


class ReferralService:
    """Referral management service."""

    async def create_referral(
        self,
        db: Session,
        data: ReferralCreate,
    ) -> Referral:
        """Create a new referral."""
        referral = Referral(
            id=uuid4(),
            tenant_id=data.tenant_id,
            patient_id=data.patient_id,
            referring_provider_id=data.referring_provider_id,
            encounter_id=data.encounter_id,
            target_specialty=data.target_specialty,
            receiving_provider_id=data.receiving_provider_id,
            referral_type=data.referral_type.value,
            priority=data.priority.value,
            reason=data.reason,
            clinical_question=data.clinical_question,
            diagnosis_codes=data.diagnosis_codes,
            preferred_date_start=data.preferred_date_start,
            preferred_date_end=data.preferred_date_end,
        )

        db.add(referral)
        db.commit()
        db.refresh(referral)

        logger.info(f"Created referral {referral.id}")
        return referral

    async def submit_referral(
        self,
        db: Session,
        referral_id: UUID,
    ) -> Referral:
        """Submit referral to receiving provider."""
        referral = db.query(Referral).filter(Referral.id == referral_id).first()
        if not referral:
            raise ValueError("Referral not found")

        # Check authorization if required
        if referral.requires_authorization and referral.authorization_status != "approved":
            raise ValueError("Referral requires approved authorization")

        referral.status = "sent"
        referral.sent_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(referral)

        return referral

    async def complete_referral(
        self,
        db: Session,
        referral_id: UUID,
        consultation_notes: str,
        recommendations: Optional[str] = None,
        follow_up_needed: bool = False,
    ) -> Referral:
        """Complete referral with consultation response."""
        referral = db.query(Referral).filter(Referral.id == referral_id).first()
        if not referral:
            raise ValueError("Referral not found")

        referral.consultation_notes = consultation_notes
        referral.recommendations = recommendations
        referral.follow_up_needed = follow_up_needed
        referral.status = "completed"
        referral.completed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(referral)

        return referral


class DocumentationService:
    """Clinical documentation service."""

    async def create_note(
        self,
        db: Session,
        data: ClinicalNoteCreate,
    ) -> ClinicalNote:
        """Create a clinical note."""
        # Process structured content if provided
        structured = None
        if data.structured_content:
            structured = data.structured_content.dict()

        note = ClinicalNote(
            id=uuid4(),
            tenant_id=data.tenant_id,
            patient_id=data.patient_id,
            encounter_id=data.encounter_id,
            author_id=data.author_id,
            note_type=data.note_type.value,
            template_id=data.template_id,
            title=data.title,
            content=data.content,
            structured_content=structured,
        )

        db.add(note)
        db.commit()
        db.refresh(note)

        logger.info(f"Created clinical note {note.id}")
        return note

    async def sign_note(
        self,
        db: Session,
        note_id: UUID,
        signer_id: UUID,
    ) -> ClinicalNote:
        """Sign a clinical note."""
        note = db.query(ClinicalNote).filter(ClinicalNote.id == note_id).first()
        if not note:
            raise ValueError("Note not found")

        note.status = "signed"
        note.signed_by = signer_id
        note.signed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(note)

        return note

    async def add_addendum(
        self,
        db: Session,
        note_id: UUID,
        author_id: UUID,
        content: str,
    ) -> ClinicalNote:
        """Add addendum to a note."""
        note = db.query(ClinicalNote).filter(ClinicalNote.id == note_id).first()
        if not note:
            raise ValueError("Note not found")

        addendum = {
            "id": str(uuid4()),
            "author_id": str(author_id),
            "content": content,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        amendments = note.amendments or []
        amendments.append(addendum)
        note.amendments = amendments
        note.status = "amended"

        db.commit()
        db.refresh(note)

        return note

    async def suggest_codes(
        self,
        db: Session,
        note_content: str,
    ) -> List[Dict[str, Any]]:
        """AI-powered code suggestion from note content."""
        # Simplified mock implementation
        # In production, would use NLP/AI for code extraction
        suggestions = []

        # Simple keyword matching for demo
        if "hypertension" in note_content.lower():
            suggestions.append({
                "code": "I10",
                "code_system": "ICD-10-CM",
                "description": "Essential (primary) hypertension",
                "confidence": 0.85,
                "source_text": "hypertension",
            })
        if "diabetes" in note_content.lower():
            suggestions.append({
                "code": "E11.9",
                "code_system": "ICD-10-CM",
                "description": "Type 2 diabetes mellitus without complications",
                "confidence": 0.75,
                "source_text": "diabetes",
            })

        return suggestions


class CarePlanService:
    """Care plan management service."""

    async def create_care_plan(
        self,
        db: Session,
        data: CarePlanCreate,
    ) -> CarePlan:
        """Create a care plan with goals and interventions."""
        plan = CarePlan(
            id=uuid4(),
            tenant_id=data.tenant_id,
            patient_id=data.patient_id,
            title=data.title,
            description=data.description,
            category=data.category.value,
            author_id=data.author_id,
            condition_ids=[str(c) for c in data.condition_ids] if data.condition_ids else [],
            period_start=data.period_start or datetime.now(timezone.utc),
            period_end=data.period_end,
        )

        db.add(plan)
        db.flush()

        # Add goals
        for goal_data in data.goals:
            goal = CareGoal(
                id=uuid4(),
                care_plan_id=plan.id,
                patient_id=data.patient_id,
                category=goal_data.category,
                description=goal_data.description,
                priority=goal_data.priority.value,
                targets=[t.dict() for t in goal_data.targets],
                start_date=goal_data.start_date,
                target_date=goal_data.target_date,
                owner_id=goal_data.owner_id,
            )
            db.add(goal)

        # Add interventions
        for int_data in data.interventions:
            intervention = CareIntervention(
                id=uuid4(),
                care_plan_id=plan.id,
                category=int_data.category,
                description=int_data.description,
                reason=int_data.reason,
                goal_ids=[str(g) for g in int_data.goal_ids] if int_data.goal_ids else [],
                scheduled_timing=int_data.scheduled_timing,
                scheduled_datetime=int_data.scheduled_datetime,
                assigned_to_id=int_data.assigned_to_id,
                instructions=int_data.instructions,
            )
            db.add(intervention)

        db.commit()
        db.refresh(plan)

        logger.info(f"Created care plan {plan.id}")
        return plan

    async def activate_care_plan(
        self,
        db: Session,
        plan_id: UUID,
    ) -> CarePlan:
        """Activate a care plan."""
        plan = db.query(CarePlan).filter(CarePlan.id == plan_id).first()
        if not plan:
            raise ValueError("Care plan not found")

        plan.status = "active"

        # Activate goals
        for goal in db.query(CareGoal).filter(CareGoal.care_plan_id == plan_id).all():
            if goal.status == "proposed":
                goal.status = "active"

        # Activate interventions
        for intervention in db.query(CareIntervention).filter(
            CareIntervention.care_plan_id == plan_id
        ).all():
            if intervention.status == "planned":
                intervention.status = "in_progress"

        db.commit()
        db.refresh(plan)

        return plan

    async def record_goal_progress(
        self,
        db: Session,
        goal_id: UUID,
        measure: str,
        value: Any,
        recorded_by: UUID,
        unit: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> GoalProgress:
        """Record progress toward a goal."""
        goal = db.query(CareGoal).filter(CareGoal.id == goal_id).first()
        if not goal:
            raise ValueError("Goal not found")

        # Determine achievement status
        value_numeric = float(value) if isinstance(value, (int, float)) else None
        achievement_status = "in_progress"

        for target in goal.targets or []:
            if target.get("measure") == measure:
                target_value = target.get("detail_value")
                if value_numeric is not None and isinstance(target_value, (int, float)):
                    if value_numeric >= target_value * 0.95:
                        achievement_status = "achieved"
                        goal.status = "completed"
                break

        progress = GoalProgress(
            id=uuid4(),
            goal_id=goal_id,
            recorded_by=recorded_by,
            measure=measure,
            value=str(value),
            value_numeric=value_numeric,
            unit=unit,
            achievement_status=achievement_status,
            notes=notes,
        )

        goal.achievement_status = achievement_status

        db.add(progress)
        db.commit()
        db.refresh(progress)

        return progress


class DecisionSupportService:
    """Clinical decision support service."""

    async def evaluate_alerts(
        self,
        db: Session,
        tenant_id: UUID,
        patient_id: UUID,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[ClinicalAlert]:
        """Evaluate CDS rules and generate alerts."""
        # Get active rules for tenant
        rules = db.query(CDSRule).filter(
            CDSRule.tenant_id == tenant_id,
            CDSRule.is_active == True,
        ).order_by(CDSRule.priority).all()

        # Build patient context (in production, fetch from patient record)
        patient_context = context or {}

        alerts = []
        for rule in rules:
            if self._evaluate_rule(rule, patient_context):
                alert = ClinicalAlert(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    patient_id=patient_id,
                    category=rule.category,
                    severity=rule.alert_severity,
                    title=rule.alert_title_template or rule.name,
                    message=rule.alert_message_template or rule.description,
                    rule_id=rule.id,
                    suggested_actions=rule.suggested_actions or [],
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
                )
                db.add(alert)
                alerts.append(alert)

        if alerts:
            db.commit()

        return alerts

    def _evaluate_rule(
        self,
        rule: CDSRule,
        context: Dict[str, Any],
    ) -> bool:
        """Evaluate a single rule against context."""
        # Simple condition evaluation
        for condition in rule.conditions or []:
            field = condition.get("field")
            operator = condition.get("operator")
            value = condition.get("value")

            field_value = context.get(field)

            if operator == "eq" and field_value != value:
                return False
            elif operator == "ne" and field_value == value:
                return False
            elif operator == "gt" and (field_value is None or field_value <= value):
                return False
            elif operator == "lt" and (field_value is None or field_value >= value):
                return False
            elif operator == "exists" and field_value is None:
                return False

        return True

    async def acknowledge_alert(
        self,
        db: Session,
        alert_id: UUID,
        user_id: UUID,
    ) -> ClinicalAlert:
        """Acknowledge an alert."""
        alert = db.query(ClinicalAlert).filter(ClinicalAlert.id == alert_id).first()
        if not alert:
            raise ValueError("Alert not found")

        alert.status = "acknowledged"
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(alert)

        return alert

    async def override_alert(
        self,
        db: Session,
        alert_id: UUID,
        user_id: UUID,
        reason: str,
    ) -> ClinicalAlert:
        """Override an alert with reason."""
        alert = db.query(ClinicalAlert).filter(ClinicalAlert.id == alert_id).first()
        if not alert:
            raise ValueError("Alert not found")

        alert.status = "overridden"
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.now(timezone.utc)
        alert.override_reason = reason

        db.commit()
        db.refresh(alert)

        logger.warning(f"Alert {alert_id} overridden by {user_id}: {reason}")
        return alert


class VitalSignsService:
    """Vital signs management service."""

    # Normal ranges
    NORMAL_RANGES = {
        "blood_pressure_systolic": (90, 120),
        "blood_pressure_diastolic": (60, 80),
        "heart_rate": (60, 100),
        "respiratory_rate": (12, 20),
        "temperature": (36.1, 37.2),
        "oxygen_saturation": (95, 100),
    }

    async def record_vital_sign(
        self,
        db: Session,
        data: VitalSignCreate,
    ) -> VitalSign:
        """Record a vital sign measurement."""
        # Process value
        value = data.value
        value_string = data.value_string

        # For blood pressure, parse string
        systolic = data.systolic
        diastolic = data.diastolic
        if data.vital_type.value == "blood_pressure" and value_string and "/" in value_string:
            parts = value_string.split("/")
            systolic = float(parts[0])
            diastolic = float(parts[1])

        # Check for abnormal
        is_abnormal = False
        interpretation = None

        if data.vital_type.value == "blood_pressure":
            if systolic and (systolic < 90 or systolic > 140):
                is_abnormal = True
            if diastolic and (diastolic < 60 or diastolic > 90):
                is_abnormal = True
        elif value is not None:
            ranges = self.NORMAL_RANGES.get(data.vital_type.value)
            if ranges:
                if value < ranges[0]:
                    is_abnormal = True
                    interpretation = "L"
                elif value > ranges[1]:
                    is_abnormal = True
                    interpretation = "H"

        vital = VitalSign(
            id=uuid4(),
            tenant_id=data.tenant_id,
            patient_id=data.patient_id,
            encounter_id=data.encounter_id,
            vital_type=data.vital_type.value,
            value=value,
            value_string=value_string,
            unit=data.unit,
            systolic=systolic,
            diastolic=diastolic,
            is_abnormal=is_abnormal,
            interpretation=interpretation,
            recorded_by=data.recorded_by,
            device_id=data.device_id,
            method=data.method,
            position=data.position,
            notes=data.notes,
        )

        db.add(vital)
        db.commit()
        db.refresh(vital)

        return vital

    async def calculate_early_warning_score(
        self,
        db: Session,
        tenant_id: UUID,
        patient_id: UUID,
        encounter_id: Optional[UUID] = None,
    ) -> EarlyWarningScore:
        """Calculate NEWS (National Early Warning Score)."""
        # Get latest vitals
        query = db.query(VitalSign).filter(
            VitalSign.tenant_id == tenant_id,
            VitalSign.patient_id == patient_id,
        )
        if encounter_id:
            query = query.filter(VitalSign.encounter_id == encounter_id)

        # Get most recent of each vital type
        vitals = {}
        for vital_type in ["heart_rate", "respiratory_rate", "oxygen_saturation", "temperature", "blood_pressure"]:
            latest = query.filter(
                VitalSign.vital_type == vital_type
            ).order_by(desc(VitalSign.recorded_at)).first()
            if latest:
                vitals[vital_type] = latest

        # Calculate component scores (simplified NEWS)
        scores = {}
        total = 0

        # Respiratory rate
        if "respiratory_rate" in vitals:
            rr = vitals["respiratory_rate"].value
            if rr <= 8:
                scores["respiratory_rate"] = 3
            elif rr <= 11:
                scores["respiratory_rate"] = 1
            elif rr <= 20:
                scores["respiratory_rate"] = 0
            elif rr <= 24:
                scores["respiratory_rate"] = 2
            else:
                scores["respiratory_rate"] = 3
            total += scores["respiratory_rate"]

        # Oxygen saturation
        if "oxygen_saturation" in vitals:
            spo2 = vitals["oxygen_saturation"].value
            if spo2 <= 91:
                scores["oxygen_saturation"] = 3
            elif spo2 <= 93:
                scores["oxygen_saturation"] = 2
            elif spo2 <= 95:
                scores["oxygen_saturation"] = 1
            else:
                scores["oxygen_saturation"] = 0
            total += scores["oxygen_saturation"]

        # Heart rate
        if "heart_rate" in vitals:
            hr = vitals["heart_rate"].value
            if hr <= 40:
                scores["heart_rate"] = 3
            elif hr <= 50:
                scores["heart_rate"] = 1
            elif hr <= 90:
                scores["heart_rate"] = 0
            elif hr <= 110:
                scores["heart_rate"] = 1
            elif hr <= 130:
                scores["heart_rate"] = 2
            else:
                scores["heart_rate"] = 3
            total += scores["heart_rate"]

        # Temperature
        if "temperature" in vitals:
            temp = vitals["temperature"].value
            if temp <= 35.0:
                scores["temperature"] = 3
            elif temp <= 36.0:
                scores["temperature"] = 1
            elif temp <= 38.0:
                scores["temperature"] = 0
            elif temp <= 39.0:
                scores["temperature"] = 1
            else:
                scores["temperature"] = 2
            total += scores["temperature"]

        # Systolic BP
        if "blood_pressure" in vitals:
            sbp = vitals["blood_pressure"].systolic
            if sbp and sbp <= 90:
                scores["blood_pressure"] = 3
            elif sbp and sbp <= 100:
                scores["blood_pressure"] = 2
            elif sbp and sbp <= 110:
                scores["blood_pressure"] = 1
            elif sbp and sbp <= 219:
                scores["blood_pressure"] = 0
            else:
                scores["blood_pressure"] = 3
            total += scores.get("blood_pressure", 0)

        # Determine risk level
        if total >= 7:
            risk_level = "high"
        elif total >= 5:
            risk_level = "medium"
        else:
            risk_level = "low"

        ews = EarlyWarningScore(
            id=uuid4(),
            tenant_id=tenant_id,
            patient_id=patient_id,
            encounter_id=encounter_id,
            score_type="NEWS",
            total_score=total,
            risk_level=risk_level,
            component_scores=scores,
            vital_sign_ids=[v.id for v in vitals.values()],
            alert_triggered=total >= 5,
        )

        db.add(ews)
        db.commit()
        db.refresh(ews)

        return ews

    async def get_vital_trends(
        self,
        db: Session,
        tenant_id: UUID,
        patient_id: UUID,
        vital_type: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get vital sign trends."""
        vitals = db.query(VitalSign).filter(
            VitalSign.tenant_id == tenant_id,
            VitalSign.patient_id == patient_id,
            VitalSign.vital_type == vital_type,
        ).order_by(desc(VitalSign.recorded_at)).limit(limit).all()

        return [
            {
                "timestamp": v.recorded_at.isoformat(),
                "value": v.value if v.value else v.value_string,
                "systolic": v.systolic,
                "diastolic": v.diastolic,
            }
            for v in reversed(vitals)
        ]


class DischargeService:
    """Discharge management service."""

    DEFAULT_CHECKLIST = [
        {"item_id": "med_rec", "description": "Medication reconciliation completed", "is_required": True},
        {"item_id": "discharge_rx", "description": "Discharge prescriptions provided", "is_required": True},
        {"item_id": "instructions", "description": "Discharge instructions reviewed with patient", "is_required": True},
        {"item_id": "followup", "description": "Follow-up appointment scheduled", "is_required": True},
        {"item_id": "transport", "description": "Transportation arranged", "is_required": False},
        {"item_id": "equipment", "description": "DME ordered if needed", "is_required": False},
        {"item_id": "summary_sent", "description": "Discharge summary sent to PCP", "is_required": True},
    ]

    async def create_discharge_record(
        self,
        db: Session,
        data: DischargeRecordCreate,
    ) -> DischargeRecord:
        """Create a discharge record."""
        # Initialize checklist
        checklist = [
            {**item, "is_completed": False}
            for item in self.DEFAULT_CHECKLIST
        ]

        # Convert medication data
        discharge_meds = [m.dict() for m in data.discharge_medications]

        record = DischargeRecord(
            id=uuid4(),
            tenant_id=data.tenant_id,
            patient_id=data.patient_id,
            encounter_id=data.encounter_id,
            discharge_disposition=data.discharge_disposition,
            discharge_destination=data.discharge_destination,
            checklist_items=checklist,
            discharge_medications=discharge_meds,
            discharge_instructions=data.discharge_instructions,
            activity_restrictions=data.activity_restrictions,
            diet_instructions=data.diet_instructions,
            follow_up_appointments=data.follow_up_appointments,
            follow_up_provider_id=data.follow_up_provider_id,
            follow_up_date=data.follow_up_date,
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        return record

    async def update_checklist_item(
        self,
        db: Session,
        record_id: UUID,
        item_id: str,
        is_completed: bool,
        completed_by: UUID,
        notes: Optional[str] = None,
    ) -> DischargeRecord:
        """Update a checklist item."""
        record = db.query(DischargeRecord).filter(DischargeRecord.id == record_id).first()
        if not record:
            raise ValueError("Discharge record not found")

        checklist = record.checklist_items or []
        for item in checklist:
            if item.get("item_id") == item_id:
                item["is_completed"] = is_completed
                if is_completed:
                    item["completed_by"] = str(completed_by)
                    item["completed_at"] = datetime.now(timezone.utc).isoformat()
                if notes:
                    item["notes"] = notes
                break

        record.checklist_items = checklist

        # Check if all required items are completed
        required_items = [i for i in checklist if i.get("is_required")]
        record.all_items_completed = all(i.get("is_completed") for i in required_items)

        db.commit()
        db.refresh(record)

        return record

    async def complete_discharge(
        self,
        db: Session,
        record_id: UUID,
        completed_by: UUID,
    ) -> DischargeRecord:
        """Finalize discharge."""
        record = db.query(DischargeRecord).filter(DischargeRecord.id == record_id).first()
        if not record:
            raise ValueError("Discharge record not found")

        if not record.all_items_completed:
            raise ValueError("All required checklist items must be completed")

        record.status = "completed"
        record.completed_at = datetime.now(timezone.utc)
        record.completed_by = completed_by

        db.commit()
        db.refresh(record)

        return record


# Service instances
prescription_service = PrescriptionService()
lab_order_service = LabOrderService()
imaging_service = ImagingService()
referral_service = ReferralService()
documentation_service = DocumentationService()
care_plan_service = CarePlanService()
decision_support_service = DecisionSupportService()
vital_signs_service = VitalSignsService()
discharge_service = DischargeService()
