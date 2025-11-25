"""
Quality Measure Service

Provides quality measure evaluation, care gap detection,
and CQL-based measure calculation.

EPIC-020: Clinical Decision Support
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from modules.cds.models import (
    QualityMeasure,
    PatientMeasure,
    CareGap,
    MeasureType,
    MeasureStatus,
    CareGapPriority,
    CareGapStatus,
)
from modules.cds.schemas import (
    QualityMeasureCreate,
    QualityMeasureUpdate,
    MeasureEvaluationRequest,
    MeasureEvaluationResponse,
    PatientMeasureResponse,
    CareGapCreate,
    CareGapUpdate,
    PatientCareGapSummary,
)


class QualityMeasureService:
    """Service for quality measure evaluation and care gap detection."""

    # Common care gap definitions
    CARE_GAP_DEFINITIONS = {
        "A1C_TEST": {
            "title": "HbA1c Test Due",
            "gap_type": "lab",
            "action_type": "order",
            "order_code": "4548-4",  # LOINC for HbA1c
            "priority": CareGapPriority.HIGH,
        },
        "MAMMOGRAM": {
            "title": "Mammogram Screening Due",
            "gap_type": "screening",
            "action_type": "referral",
            "order_code": "77067",  # CPT for mammogram
            "priority": CareGapPriority.MEDIUM,
        },
        "COLONOSCOPY": {
            "title": "Colorectal Cancer Screening Due",
            "gap_type": "screening",
            "action_type": "referral",
            "order_code": "45378",  # CPT for colonoscopy
            "priority": CareGapPriority.MEDIUM,
        },
        "FLU_VACCINE": {
            "title": "Influenza Vaccination Due",
            "gap_type": "vaccination",
            "action_type": "order",
            "order_code": "90686",  # CPT for flu vaccine
            "priority": CareGapPriority.MEDIUM,
        },
        "BP_CHECK": {
            "title": "Blood Pressure Check Due",
            "gap_type": "vital",
            "action_type": "procedure",
            "priority": CareGapPriority.HIGH,
        },
    }

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def create_measure(
        self,
        data: QualityMeasureCreate,
    ) -> QualityMeasure:
        """Create a new quality measure definition."""
        measure = QualityMeasure(
            tenant_id=self.tenant_id,
            measure_id=data.measure_id,
            title=data.title,
            short_name=data.short_name,
            version=data.version,
            measure_type=data.measure_type,
            category=data.category,
            domain=data.domain,
            description=data.description,
            rationale=data.rationale,
            clinical_recommendation=data.clinical_recommendation,
            initial_population_cql=data.initial_population_cql,
            denominator_cql=data.denominator_cql,
            numerator_cql=data.numerator_cql,
            exclusion_cql=data.exclusion_cql,
            exception_cql=data.exception_cql,
            target_rate=data.target_rate,
            reporting_period_start=data.reporting_period_start,
            reporting_period_end=data.reporting_period_end,
            specification_url=data.specification_url,
        )
        self.db.add(measure)
        await self.db.flush()
        return measure

    async def get_measure(self, measure_id: UUID) -> Optional[QualityMeasure]:
        """Get measure by ID."""
        query = select(QualityMeasure).where(
            and_(
                QualityMeasure.id == measure_id,
                QualityMeasure.tenant_id == self.tenant_id,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_measure_by_code(
        self,
        measure_code: str,
        version: Optional[str] = None,
    ) -> Optional[QualityMeasure]:
        """Get measure by measure code."""
        query = select(QualityMeasure).where(
            and_(
                QualityMeasure.tenant_id == self.tenant_id,
                QualityMeasure.measure_id == measure_code,
                QualityMeasure.is_active == True,
            )
        )

        if version:
            query = query.where(QualityMeasure.version == version)
        else:
            query = query.order_by(QualityMeasure.created_at.desc())

        result = await self.db.execute(query)
        return result.scalars().first()

    async def list_measures(
        self,
        measure_type: Optional[MeasureType] = None,
        category: Optional[str] = None,
        domain: Optional[str] = None,
        is_active: bool = True,
        is_required: bool = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[QualityMeasure]:
        """List quality measures."""
        query = select(QualityMeasure).where(
            and_(
                QualityMeasure.tenant_id == self.tenant_id,
                QualityMeasure.is_active == is_active,
            )
        )

        if measure_type:
            query = query.where(QualityMeasure.measure_type == measure_type)
        if category:
            query = query.where(QualityMeasure.category == category)
        if domain:
            query = query.where(QualityMeasure.domain == domain)
        if is_required is not None:
            query = query.where(QualityMeasure.is_required == is_required)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def evaluate_patient_measures(
        self,
        request: MeasureEvaluationRequest,
        patient_data: Dict[str, Any],
    ) -> MeasureEvaluationResponse:
        """
        Evaluate quality measures for a patient.

        Args:
            request: Evaluation request with patient and measure IDs
            patient_data: Patient clinical data for CQL evaluation
        """
        # Get measures to evaluate
        if request.measure_ids:
            measures = []
            for mid in request.measure_ids:
                measure = await self.get_measure(mid)
                if measure:
                    measures.append(measure)
        else:
            measures = await self.list_measures(is_active=True)

        # Determine evaluation period
        period_start = request.period_start or date(date.today().year, 1, 1)
        period_end = request.period_end or date.today()

        # Evaluate each measure
        patient_measures = []
        for measure in measures:
            patient_measure = await self._evaluate_single_measure(
                measure=measure,
                patient_id=request.patient_id,
                patient_data=patient_data,
                period_start=period_start,
                period_end=period_end,
            )
            patient_measures.append(patient_measure)

        # Calculate summary
        met_count = sum(1 for pm in patient_measures if pm.status == MeasureStatus.MET)
        not_met_count = sum(1 for pm in patient_measures if pm.status == MeasureStatus.NOT_MET)
        excluded_count = sum(1 for pm in patient_measures if pm.status == MeasureStatus.EXCLUDED)

        return MeasureEvaluationResponse(
            patient_id=request.patient_id,
            evaluated_at=datetime.utcnow(),
            measures=[PatientMeasureResponse.from_orm(pm) for pm in patient_measures],
            total_measures=len(patient_measures),
            met_count=met_count,
            not_met_count=not_met_count,
            excluded_count=excluded_count,
        )

    async def _evaluate_single_measure(
        self,
        measure: QualityMeasure,
        patient_id: UUID,
        patient_data: Dict[str, Any],
        period_start: date,
        period_end: date,
    ) -> PatientMeasure:
        """Evaluate a single measure for a patient."""
        # Check for existing evaluation in this period
        query = select(PatientMeasure).where(
            and_(
                PatientMeasure.patient_id == patient_id,
                PatientMeasure.measure_id == measure.id,
                PatientMeasure.period_start == period_start,
                PatientMeasure.period_end == period_end,
            )
        )
        result = await self.db.execute(query)
        patient_measure = result.scalar_one_or_none()

        if not patient_measure:
            patient_measure = PatientMeasure(
                tenant_id=self.tenant_id,
                patient_id=patient_id,
                measure_id=measure.id,
                period_start=period_start,
                period_end=period_end,
            )
            self.db.add(patient_measure)

        # Evaluate CQL criteria
        # Note: In production, this would use a CQL engine
        evaluation_result = await self._execute_cql_evaluation(
            measure=measure,
            patient_data=patient_data,
            period_start=period_start,
            period_end=period_end,
        )

        # Update patient measure with results
        patient_measure.in_initial_population = evaluation_result.get("in_initial_population", False)
        patient_measure.in_denominator = evaluation_result.get("in_denominator", False)
        patient_measure.in_numerator = evaluation_result.get("in_numerator", False)
        patient_measure.is_excluded = evaluation_result.get("is_excluded", False)
        patient_measure.has_exception = evaluation_result.get("has_exception", False)
        patient_measure.supporting_data = evaluation_result.get("supporting_data", {})
        patient_measure.exclusion_reason = evaluation_result.get("exclusion_reason")
        patient_measure.exception_reason = evaluation_result.get("exception_reason")
        patient_measure.evaluation_date = datetime.utcnow()

        # Determine status
        if patient_measure.is_excluded:
            patient_measure.status = MeasureStatus.EXCLUDED
        elif not patient_measure.in_initial_population or not patient_measure.in_denominator:
            patient_measure.status = MeasureStatus.EXCLUDED
        elif patient_measure.in_numerator:
            patient_measure.status = MeasureStatus.MET
        else:
            patient_measure.status = MeasureStatus.NOT_MET
            # Generate gap actions
            patient_measure.gap_actions = await self._generate_gap_actions(
                measure, patient_data
            )

        await self.db.flush()
        return patient_measure

    async def _execute_cql_evaluation(
        self,
        measure: QualityMeasure,
        patient_data: Dict[str, Any],
        period_start: date,
        period_end: date,
    ) -> Dict[str, Any]:
        """
        Execute CQL evaluation for a measure.

        Note: This is a simplified implementation. In production,
        this would integrate with a CQL engine like cql-exec-fhir.
        """
        # Simplified evaluation based on patient data
        result = {
            "in_initial_population": False,
            "in_denominator": False,
            "in_numerator": False,
            "is_excluded": False,
            "has_exception": False,
            "supporting_data": {},
        }

        # Basic evaluation logic (would be replaced by actual CQL execution)
        patient_age = patient_data.get("age", 0)
        conditions = patient_data.get("conditions", [])
        procedures = patient_data.get("procedures", [])
        observations = patient_data.get("observations", [])

        # Example: Diabetes A1C measure evaluation
        if measure.domain == "diabetes":
            has_diabetes = any("E11" in c.get("code", "") for c in conditions)
            if has_diabetes and 18 <= patient_age <= 75:
                result["in_initial_population"] = True
                result["in_denominator"] = True

                # Check for A1C in period
                has_a1c = any(
                    obs.get("code") == "4548-4" and
                    period_start <= date.fromisoformat(obs.get("date", "1900-01-01")) <= period_end
                    for obs in observations
                )
                result["in_numerator"] = has_a1c

        return result

    async def _generate_gap_actions(
        self,
        measure: QualityMeasure,
        patient_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Generate recommended actions to close the care gap."""
        actions = []

        # Map measure to gap definition
        gap_key = None
        if "A1C" in measure.measure_id.upper() or measure.domain == "diabetes":
            gap_key = "A1C_TEST"
        elif "MAMMOGRAM" in measure.measure_id.upper() or "BCS" in measure.measure_id.upper():
            gap_key = "MAMMOGRAM"
        elif "COLONOSCOPY" in measure.measure_id.upper() or "COL" in measure.measure_id.upper():
            gap_key = "COLONOSCOPY"

        if gap_key and gap_key in self.CARE_GAP_DEFINITIONS:
            gap_def = self.CARE_GAP_DEFINITIONS[gap_key]
            actions.append({
                "action": gap_def["title"],
                "type": gap_def["action_type"],
                "order_code": gap_def.get("order_code"),
                "priority": gap_def["priority"].value,
            })

        return actions

    # Care Gap Methods

    async def create_care_gap(
        self,
        data: CareGapCreate,
    ) -> CareGap:
        """Create a new care gap."""
        care_gap = CareGap(
            tenant_id=self.tenant_id,
            patient_id=data.patient_id,
            measure_id=data.measure_id,
            gap_type=data.gap_type,
            title=data.title,
            description=data.description,
            priority=data.priority,
            recommended_action=data.recommended_action,
            action_type=data.action_type,
            order_code=data.order_code,
            due_date=data.due_date,
            attributed_provider_id=data.attributed_provider_id,
        )
        self.db.add(care_gap)
        await self.db.flush()
        return care_gap

    async def get_care_gap(self, gap_id: UUID) -> Optional[CareGap]:
        """Get care gap by ID."""
        query = select(CareGap).where(
            and_(
                CareGap.id == gap_id,
                CareGap.tenant_id == self.tenant_id,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_patient_care_gaps(
        self,
        patient_id: UUID,
        status: Optional[CareGapStatus] = None,
        priority: Optional[CareGapPriority] = None,
        include_closed: bool = False,
    ) -> PatientCareGapSummary:
        """Get all care gaps for a patient."""
        query = select(CareGap).where(
            and_(
                CareGap.tenant_id == self.tenant_id,
                CareGap.patient_id == patient_id,
            )
        )

        if status:
            query = query.where(CareGap.status == status)
        elif not include_closed:
            query = query.where(CareGap.status != CareGapStatus.CLOSED)

        if priority:
            query = query.where(CareGap.priority == priority)

        query = query.order_by(CareGap.priority, CareGap.due_date)
        result = await self.db.execute(query)
        gaps = list(result.scalars().all())

        # Calculate summary
        critical_gaps = sum(1 for g in gaps if g.priority == CareGapPriority.CRITICAL)
        high_priority_gaps = sum(1 for g in gaps if g.priority == CareGapPriority.HIGH)
        overdue_gaps = sum(1 for g in gaps if g.due_date and g.due_date < date.today())

        return PatientCareGapSummary(
            patient_id=patient_id,
            total_gaps=len(gaps),
            critical_gaps=critical_gaps,
            high_priority_gaps=high_priority_gaps,
            overdue_gaps=overdue_gaps,
            gaps=[CareGapResponse.from_orm(g) for g in gaps],
        )

    async def update_care_gap(
        self,
        gap_id: UUID,
        data: CareGapUpdate,
    ) -> Optional[CareGap]:
        """Update a care gap."""
        care_gap = await self.get_care_gap(gap_id)
        if not care_gap:
            return None

        update_data = data.dict(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(care_gap, key):
                setattr(care_gap, key, value)

        await self.db.flush()
        return care_gap

    async def close_care_gap(
        self,
        gap_id: UUID,
        closed_by_provider_id: UUID,
        closure_evidence: Dict[str, Any],
    ) -> Optional[CareGap]:
        """Close a care gap with evidence."""
        care_gap = await self.get_care_gap(gap_id)
        if not care_gap:
            return None

        care_gap.status = CareGapStatus.CLOSED
        care_gap.closed_date = date.today()
        care_gap.closed_by_provider_id = closed_by_provider_id
        care_gap.closure_evidence = closure_evidence

        await self.db.flush()
        return care_gap

    async def snooze_care_gap(
        self,
        gap_id: UUID,
        snoozed_until: date,
        snooze_reason: str,
    ) -> Optional[CareGap]:
        """Snooze a care gap until a future date."""
        care_gap = await self.get_care_gap(gap_id)
        if not care_gap:
            return None

        care_gap.status = CareGapStatus.SNOOZED
        care_gap.snoozed_until = snoozed_until
        care_gap.snooze_reason = snooze_reason

        await self.db.flush()
        return care_gap

    async def auto_detect_care_gaps(
        self,
        patient_id: UUID,
        patient_data: Dict[str, Any],
    ) -> List[CareGap]:
        """Automatically detect care gaps based on patient data."""
        detected_gaps = []

        # Evaluate all active measures
        evaluation = await self.evaluate_patient_measures(
            request=MeasureEvaluationRequest(patient_id=patient_id),
            patient_data=patient_data,
        )

        # Create care gaps for measures not met
        for pm in evaluation.measures:
            if pm.status == MeasureStatus.NOT_MET and pm.gap_actions:
                for action in pm.gap_actions:
                    # Check if gap already exists
                    existing_query = select(CareGap).where(
                        and_(
                            CareGap.patient_id == patient_id,
                            CareGap.measure_id == pm.measure.id,
                            CareGap.status.in_([CareGapStatus.OPEN, CareGapStatus.IN_PROGRESS]),
                        )
                    )
                    result = await self.db.execute(existing_query)
                    existing = result.scalar_one_or_none()

                    if not existing:
                        gap = CareGap(
                            tenant_id=self.tenant_id,
                            patient_id=patient_id,
                            measure_id=pm.measure.id,
                            patient_measure_id=pm.id,
                            gap_type=action.get("type", "other"),
                            title=action.get("action"),
                            priority=CareGapPriority(action.get("priority", "medium")),
                            recommended_action=action.get("action"),
                            action_type=action.get("type"),
                            order_code=action.get("order_code"),
                        )
                        self.db.add(gap)
                        detected_gaps.append(gap)

        await self.db.flush()
        return detected_gaps

    async def get_measure_performance(
        self,
        measure_id: UUID,
        period_start: date,
        period_end: date,
    ) -> Dict[str, Any]:
        """Get measure performance metrics."""
        query = select(PatientMeasure).where(
            and_(
                PatientMeasure.measure_id == measure_id,
                PatientMeasure.tenant_id == self.tenant_id,
                PatientMeasure.period_start >= period_start,
                PatientMeasure.period_end <= period_end,
            )
        )

        result = await self.db.execute(query)
        patient_measures = list(result.scalars().all())

        total_denominator = sum(1 for pm in patient_measures if pm.in_denominator)
        total_numerator = sum(1 for pm in patient_measures if pm.in_numerator)
        total_excluded = sum(1 for pm in patient_measures if pm.is_excluded)

        performance_rate = (total_numerator / total_denominator * 100) if total_denominator > 0 else 0

        measure = await self.get_measure(measure_id)

        return {
            "measure_id": measure_id,
            "measure_title": measure.title if measure else None,
            "period_start": period_start,
            "period_end": period_end,
            "total_patients": len(patient_measures),
            "denominator_count": total_denominator,
            "numerator_count": total_numerator,
            "excluded_count": total_excluded,
            "performance_rate": round(performance_rate, 2),
            "target_rate": measure.target_rate if measure else None,
            "meets_target": performance_rate >= (measure.target_rate or 0) if measure else None,
        }
