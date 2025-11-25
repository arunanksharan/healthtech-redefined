"""
Risk Assessment Service

HIPAA risk assessment, remediation tracking, and risk register management.
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from modules.hipaa.models import (
    RiskAssessment,
    RiskItem,
    RemediationPlan,
    RiskRegister,
    RiskLevel,
    RiskCategory,
    RemediationStatus,
)


# Risk calculation matrix (likelihood x impact)
RISK_MATRIX = {
    (1, 1): RiskLevel.MINIMAL,
    (1, 2): RiskLevel.LOW,
    (1, 3): RiskLevel.LOW,
    (1, 4): RiskLevel.MEDIUM,
    (1, 5): RiskLevel.MEDIUM,
    (2, 1): RiskLevel.LOW,
    (2, 2): RiskLevel.LOW,
    (2, 3): RiskLevel.MEDIUM,
    (2, 4): RiskLevel.MEDIUM,
    (2, 5): RiskLevel.HIGH,
    (3, 1): RiskLevel.LOW,
    (3, 2): RiskLevel.MEDIUM,
    (3, 3): RiskLevel.MEDIUM,
    (3, 4): RiskLevel.HIGH,
    (3, 5): RiskLevel.HIGH,
    (4, 1): RiskLevel.MEDIUM,
    (4, 2): RiskLevel.MEDIUM,
    (4, 3): RiskLevel.HIGH,
    (4, 4): RiskLevel.HIGH,
    (4, 5): RiskLevel.CRITICAL,
    (5, 1): RiskLevel.MEDIUM,
    (5, 2): RiskLevel.HIGH,
    (5, 3): RiskLevel.HIGH,
    (5, 4): RiskLevel.CRITICAL,
    (5, 5): RiskLevel.CRITICAL,
}


class RiskService:
    """
    Service for HIPAA risk assessment and management.

    Features:
    - Risk assessment creation and management
    - Risk item identification and scoring
    - Remediation plan tracking
    - Risk register maintenance
    - Risk trend analysis
    - Compliance reporting
    """

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    # =========================================================================
    # Risk Assessment Management
    # =========================================================================

    async def create_assessment(
        self,
        name: str,
        assessment_type: str,
        scope_description: str,
        start_date: date,
        target_completion_date: date,
        lead_assessor_id: UUID,
        description: Optional[str] = None,
        systems_in_scope: Optional[List[str]] = None,
        departments_in_scope: Optional[List[str]] = None,
        lead_assessor_name: Optional[str] = None,
        assessment_team: Optional[List[Dict[str, Any]]] = None,
        methodology: Optional[str] = None,
        methodology_version: Optional[str] = None,
        created_by: Optional[UUID] = None,
    ) -> RiskAssessment:
        """Create a new risk assessment."""
        assessment_number = f"RA-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"

        assessment = RiskAssessment(
            tenant_id=self.tenant_id,
            assessment_number=assessment_number,
            name=name,
            description=description,
            assessment_type=assessment_type,
            scope_description=scope_description,
            systems_in_scope=systems_in_scope,
            departments_in_scope=departments_in_scope,
            start_date=start_date,
            target_completion_date=target_completion_date,
            lead_assessor_id=lead_assessor_id,
            lead_assessor_name=lead_assessor_name,
            assessment_team=assessment_team,
            methodology=methodology,
            methodology_version=methodology_version,
            status="in_progress",
            created_by=created_by,
        )

        self.db.add(assessment)
        await self.db.commit()
        await self.db.refresh(assessment)

        return assessment

    async def get_assessment(self, assessment_id: UUID) -> Optional[RiskAssessment]:
        """Get risk assessment by ID."""
        query = select(RiskAssessment).where(
            and_(
                RiskAssessment.id == assessment_id,
                RiskAssessment.tenant_id == self.tenant_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def complete_assessment(
        self,
        assessment_id: UUID,
        executive_summary: str,
        overall_risk_level: RiskLevel,
        report_url: Optional[str] = None,
    ) -> Optional[RiskAssessment]:
        """Complete a risk assessment."""
        assessment = await self.get_assessment(assessment_id)
        if not assessment:
            return None

        assessment.status = "completed"
        assessment.actual_completion_date = date.today()
        assessment.executive_summary = executive_summary
        assessment.overall_risk_level = overall_risk_level
        assessment.report_url = report_url
        assessment.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(assessment)

        return assessment

    async def approve_assessment(
        self,
        assessment_id: UUID,
        approved_by: UUID,
    ) -> Optional[RiskAssessment]:
        """Approve a completed risk assessment."""
        assessment = await self.get_assessment(assessment_id)
        if not assessment:
            return None

        assessment.approved = True
        assessment.approved_by = approved_by
        assessment.approved_at = datetime.utcnow()
        assessment.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(assessment)

        return assessment

    async def list_assessments(
        self,
        status: Optional[str] = None,
        assessment_type: Optional[str] = None,
    ) -> List[RiskAssessment]:
        """List risk assessments."""
        query = select(RiskAssessment).where(
            RiskAssessment.tenant_id == self.tenant_id
        )

        if status:
            query = query.where(RiskAssessment.status == status)
        if assessment_type:
            query = query.where(RiskAssessment.assessment_type == assessment_type)

        query = query.order_by(desc(RiskAssessment.start_date))

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # =========================================================================
    # Risk Item Management
    # =========================================================================

    async def create_risk_item(
        self,
        assessment_id: UUID,
        risk_number: str,
        title: str,
        description: str,
        category: RiskCategory,
        likelihood: int,
        impact: int,
        safeguard_type: Optional[str] = None,
        hipaa_reference: Optional[str] = None,
        threat_source: Optional[str] = None,
        vulnerability: Optional[str] = None,
        existing_controls: Optional[str] = None,
        control_effectiveness: Optional[int] = None,
        evidence: Optional[str] = None,
        affected_assets: Optional[List[str]] = None,
    ) -> RiskItem:
        """Create a risk item."""
        # Calculate risk scores
        inherent_risk_score = likelihood * impact
        risk_level = self._calculate_risk_level(likelihood, impact)

        # Calculate residual risk if control effectiveness provided
        residual_risk_score = None
        residual_risk_level = None
        if control_effectiveness:
            effective_likelihood = max(1, likelihood - (control_effectiveness - 3))
            residual_risk_score = effective_likelihood * impact
            residual_risk_level = self._calculate_risk_level(effective_likelihood, impact)

        risk_item = RiskItem(
            tenant_id=self.tenant_id,
            assessment_id=assessment_id,
            risk_number=risk_number,
            title=title,
            description=description,
            category=category,
            safeguard_type=safeguard_type,
            hipaa_reference=hipaa_reference,
            threat_source=threat_source,
            vulnerability=vulnerability,
            existing_controls=existing_controls,
            likelihood=likelihood,
            impact=impact,
            inherent_risk_score=inherent_risk_score,
            risk_level=risk_level,
            control_effectiveness=control_effectiveness,
            residual_risk_score=residual_risk_score,
            residual_risk_level=residual_risk_level,
            evidence=evidence,
            affected_assets=affected_assets,
            status=RemediationStatus.PLANNED,
        )

        self.db.add(risk_item)

        # Update assessment risk counts
        assessment = await self.get_assessment(assessment_id)
        if assessment:
            assessment.total_risks_identified += 1
            if risk_level == RiskLevel.CRITICAL:
                assessment.critical_risks += 1
            elif risk_level == RiskLevel.HIGH:
                assessment.high_risks += 1
            elif risk_level == RiskLevel.MEDIUM:
                assessment.medium_risks += 1
            elif risk_level == RiskLevel.LOW:
                assessment.low_risks += 1

        await self.db.commit()
        await self.db.refresh(risk_item)

        return risk_item

    def _calculate_risk_level(self, likelihood: int, impact: int) -> RiskLevel:
        """Calculate risk level from likelihood and impact."""
        return RISK_MATRIX.get((likelihood, impact), RiskLevel.MEDIUM)

    async def get_risk_item(self, risk_id: UUID) -> Optional[RiskItem]:
        """Get risk item by ID."""
        query = select(RiskItem).where(
            and_(
                RiskItem.id == risk_id,
                RiskItem.tenant_id == self.tenant_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_risk_status(
        self,
        risk_id: UUID,
        status: RemediationStatus,
    ) -> Optional[RiskItem]:
        """Update risk item status."""
        risk_item = await self.get_risk_item(risk_id)
        if risk_item:
            risk_item.status = status
            risk_item.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(risk_item)
        return risk_item

    async def list_risk_items(
        self,
        assessment_id: Optional[UUID] = None,
        risk_level: Optional[RiskLevel] = None,
        category: Optional[RiskCategory] = None,
        status: Optional[RemediationStatus] = None,
    ) -> List[RiskItem]:
        """List risk items with filtering."""
        query = select(RiskItem).where(
            RiskItem.tenant_id == self.tenant_id
        )

        if assessment_id:
            query = query.where(RiskItem.assessment_id == assessment_id)
        if risk_level:
            query = query.where(RiskItem.risk_level == risk_level)
        if category:
            query = query.where(RiskItem.category == category)
        if status:
            query = query.where(RiskItem.status == status)

        query = query.order_by(
            desc(RiskItem.risk_level),
            desc(RiskItem.inherent_risk_score)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # =========================================================================
    # Remediation Planning
    # =========================================================================

    async def create_remediation_plan(
        self,
        risk_id: UUID,
        title: str,
        description: str,
        owner_id: UUID,
        planned_start_date: date,
        target_completion_date: date,
        owner_name: Optional[str] = None,
        estimated_cost: Optional[float] = None,
        verification_required: bool = True,
        created_by: Optional[UUID] = None,
    ) -> RemediationPlan:
        """Create a remediation plan for a risk."""
        plan = RemediationPlan(
            tenant_id=self.tenant_id,
            risk_id=risk_id,
            title=title,
            description=description,
            owner_id=owner_id,
            owner_name=owner_name,
            planned_start_date=planned_start_date,
            target_completion_date=target_completion_date,
            estimated_cost=estimated_cost,
            verification_required=verification_required,
            status=RemediationStatus.PLANNED,
            created_by=created_by,
        )

        self.db.add(plan)
        await self.db.commit()
        await self.db.refresh(plan)

        return plan

    async def get_remediation_plan(self, plan_id: UUID) -> Optional[RemediationPlan]:
        """Get remediation plan by ID."""
        query = select(RemediationPlan).where(
            and_(
                RemediationPlan.id == plan_id,
                RemediationPlan.tenant_id == self.tenant_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_remediation_progress(
        self,
        plan_id: UUID,
        status: Optional[RemediationStatus] = None,
        percent_complete: Optional[int] = None,
        actual_start_date: Optional[date] = None,
        actual_cost: Optional[float] = None,
        implementation_notes: Optional[str] = None,
    ) -> Optional[RemediationPlan]:
        """Update remediation plan progress."""
        plan = await self.get_remediation_plan(plan_id)
        if not plan:
            return None

        if status:
            plan.status = status
        if percent_complete is not None:
            plan.percent_complete = percent_complete
        if actual_start_date:
            plan.actual_start_date = actual_start_date
        if actual_cost is not None:
            plan.actual_cost = actual_cost
        if implementation_notes:
            plan.implementation_notes = implementation_notes

        # Auto-complete if 100%
        if percent_complete == 100 and plan.status != RemediationStatus.COMPLETED:
            plan.status = RemediationStatus.COMPLETED
            plan.actual_completion_date = date.today()

        plan.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(plan)

        # Update associated risk status
        if plan.status == RemediationStatus.COMPLETED:
            await self.update_risk_status(plan.risk_id, RemediationStatus.COMPLETED)

        return plan

    async def verify_remediation(
        self,
        plan_id: UUID,
        verified_by: UUID,
        verification_evidence: str,
    ) -> Optional[RemediationPlan]:
        """Verify that remediation was completed successfully."""
        plan = await self.get_remediation_plan(plan_id)
        if not plan:
            return None

        plan.status = RemediationStatus.VERIFIED
        plan.verified_by = verified_by
        plan.verified_at = datetime.utcnow()
        plan.verification_evidence = verification_evidence
        plan.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(plan)

        # Update associated risk status
        await self.update_risk_status(plan.risk_id, RemediationStatus.VERIFIED)

        return plan

    async def accept_risk(
        self,
        plan_id: UUID,
        approved_by: UUID,
        acceptance_reason: str,
        expiration_date: Optional[date] = None,
    ) -> Optional[RemediationPlan]:
        """Accept risk instead of remediating."""
        plan = await self.get_remediation_plan(plan_id)
        if not plan:
            return None

        plan.status = RemediationStatus.ACCEPTED
        plan.risk_acceptance_approved = True
        plan.risk_acceptance_approved_by = approved_by
        plan.risk_acceptance_reason = acceptance_reason
        plan.risk_acceptance_expiration = expiration_date
        plan.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(plan)

        # Update associated risk status
        await self.update_risk_status(plan.risk_id, RemediationStatus.ACCEPTED)

        return plan

    async def list_remediation_plans(
        self,
        status: Optional[RemediationStatus] = None,
        owner_id: Optional[UUID] = None,
        overdue_only: bool = False,
    ) -> List[RemediationPlan]:
        """List remediation plans."""
        query = select(RemediationPlan).where(
            RemediationPlan.tenant_id == self.tenant_id
        )

        if status:
            query = query.where(RemediationPlan.status == status)
        if owner_id:
            query = query.where(RemediationPlan.owner_id == owner_id)
        if overdue_only:
            query = query.where(
                and_(
                    RemediationPlan.target_completion_date < date.today(),
                    RemediationPlan.status.in_([
                        RemediationStatus.PLANNED,
                        RemediationStatus.IN_PROGRESS,
                    ])
                )
            )

        query = query.order_by(RemediationPlan.target_completion_date)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_overdue_remediations(self) -> List[RemediationPlan]:
        """Get overdue remediation plans."""
        return await self.list_remediation_plans(overdue_only=True)

    # =========================================================================
    # Risk Register
    # =========================================================================

    async def add_to_risk_register(
        self,
        risk_item: RiskItem,
        risk_owner_id: UUID,
        treatment_strategy: str,
        risk_owner_name: Optional[str] = None,
        target_risk_level: Optional[RiskLevel] = None,
        target_resolution_date: Optional[date] = None,
    ) -> RiskRegister:
        """Add a risk to the risk register."""
        risk_id = f"RR-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"

        register_entry = RiskRegister(
            tenant_id=self.tenant_id,
            risk_id=risk_id,
            source_assessment_id=risk_item.assessment_id,
            source_risk_item_id=risk_item.id,
            title=risk_item.title,
            description=risk_item.description,
            category=risk_item.category,
            current_risk_level=risk_item.risk_level,
            current_likelihood=risk_item.likelihood,
            current_impact=risk_item.impact,
            target_risk_level=target_risk_level,
            treatment_strategy=treatment_strategy,
            treatment_status=risk_item.status,
            risk_owner_id=risk_owner_id,
            risk_owner_name=risk_owner_name,
            identified_date=date.today(),
            target_resolution_date=target_resolution_date,
            next_review_date=date.today() + timedelta(days=90),  # Quarterly review
            historical_scores=[{
                "date": date.today().isoformat(),
                "likelihood": risk_item.likelihood,
                "impact": risk_item.impact,
                "level": risk_item.risk_level.value,
            }],
        )

        self.db.add(register_entry)
        await self.db.commit()
        await self.db.refresh(register_entry)

        return register_entry

    async def update_risk_register(
        self,
        register_id: UUID,
        current_risk_level: Optional[RiskLevel] = None,
        current_likelihood: Optional[int] = None,
        current_impact: Optional[int] = None,
        treatment_status: Optional[RemediationStatus] = None,
        risk_trend: Optional[str] = None,
    ) -> Optional[RiskRegister]:
        """Update a risk register entry."""
        query = select(RiskRegister).where(
            and_(
                RiskRegister.id == register_id,
                RiskRegister.tenant_id == self.tenant_id
            )
        )
        result = await self.db.execute(query)
        entry = result.scalar_one_or_none()

        if not entry:
            return None

        if current_risk_level:
            entry.current_risk_level = current_risk_level
        if current_likelihood is not None:
            entry.current_likelihood = current_likelihood
        if current_impact is not None:
            entry.current_impact = current_impact
        if treatment_status:
            entry.treatment_status = treatment_status
        if risk_trend:
            entry.risk_trend = risk_trend

        # Add to historical scores
        if current_likelihood is not None and current_impact is not None:
            new_score = {
                "date": date.today().isoformat(),
                "likelihood": current_likelihood,
                "impact": current_impact,
                "level": entry.current_risk_level.value if entry.current_risk_level else None,
            }
            if entry.historical_scores:
                entry.historical_scores.append(new_score)
            else:
                entry.historical_scores = [new_score]

        entry.last_review_date = date.today()
        entry.next_review_date = date.today() + timedelta(days=90)
        entry.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(entry)

        return entry

    async def list_risk_register(
        self,
        risk_level: Optional[RiskLevel] = None,
        category: Optional[RiskCategory] = None,
        treatment_status: Optional[RemediationStatus] = None,
        active_only: bool = True,
    ) -> List[RiskRegister]:
        """List risk register entries."""
        query = select(RiskRegister).where(
            RiskRegister.tenant_id == self.tenant_id
        )

        if risk_level:
            query = query.where(RiskRegister.current_risk_level == risk_level)
        if category:
            query = query.where(RiskRegister.category == category)
        if treatment_status:
            query = query.where(RiskRegister.treatment_status == treatment_status)
        if active_only:
            query = query.where(RiskRegister.is_active == True)

        query = query.order_by(
            desc(RiskRegister.current_risk_level),
            RiskRegister.next_review_date
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_risks_due_for_review(self) -> List[RiskRegister]:
        """Get risks due for review."""
        query = select(RiskRegister).where(
            and_(
                RiskRegister.tenant_id == self.tenant_id,
                RiskRegister.is_active == True,
                RiskRegister.next_review_date <= date.today()
            )
        ).order_by(RiskRegister.next_review_date)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # =========================================================================
    # Risk Reporting
    # =========================================================================

    async def get_risk_dashboard(self) -> Dict[str, Any]:
        """Get risk dashboard statistics."""
        # Open risks by level
        level_query = (
            select(RiskRegister.current_risk_level, func.count(RiskRegister.id))
            .where(
                and_(
                    RiskRegister.tenant_id == self.tenant_id,
                    RiskRegister.is_active == True,
                    RiskRegister.treatment_status.notin_([
                        RemediationStatus.COMPLETED,
                        RemediationStatus.VERIFIED,
                    ])
                )
            )
            .group_by(RiskRegister.current_risk_level)
        )
        level_result = await self.db.execute(level_query)
        by_level = {row[0].value: row[1] for row in level_result.all()}

        # Open risks by category
        category_query = (
            select(RiskRegister.category, func.count(RiskRegister.id))
            .where(
                and_(
                    RiskRegister.tenant_id == self.tenant_id,
                    RiskRegister.is_active == True,
                    RiskRegister.treatment_status.notin_([
                        RemediationStatus.COMPLETED,
                        RemediationStatus.VERIFIED,
                    ])
                )
            )
            .group_by(RiskRegister.category)
        )
        category_result = await self.db.execute(category_query)
        by_category = {row[0].value: row[1] for row in category_result.all()}

        # Total open risks
        total_open_query = select(func.count()).select_from(RiskRegister).where(
            and_(
                RiskRegister.tenant_id == self.tenant_id,
                RiskRegister.is_active == True,
                RiskRegister.treatment_status.notin_([
                    RemediationStatus.COMPLETED,
                    RemediationStatus.VERIFIED,
                ])
            )
        )
        total_open_result = await self.db.execute(total_open_query)
        total_open = total_open_result.scalar()

        # Overdue remediations
        overdue_remediations = await self.get_overdue_remediations()

        # Risks due for review
        due_for_review = await self.get_risks_due_for_review()

        return {
            "total_open_risks": total_open,
            "risks_by_level": by_level,
            "risks_by_category": by_category,
            "overdue_remediations": len(overdue_remediations),
            "risks_due_for_review": len(due_for_review),
        }

    async def generate_risk_report(
        self,
        assessment_id: UUID,
    ) -> Dict[str, Any]:
        """Generate detailed risk report for an assessment."""
        assessment = await self.get_assessment(assessment_id)
        if not assessment:
            return {}

        risk_items = await self.list_risk_items(assessment_id=assessment_id)

        # Calculate statistics
        by_level = {}
        by_category = {}
        for item in risk_items:
            level = item.risk_level.value
            by_level[level] = by_level.get(level, 0) + 1

            cat = item.category.value
            by_category[cat] = by_category.get(cat, 0) + 1

        # Get remediation status
        remediation_status = {}
        for item in risk_items:
            status = item.status.value
            remediation_status[status] = remediation_status.get(status, 0) + 1

        return {
            "assessment_number": assessment.assessment_number,
            "assessment_name": assessment.name,
            "assessment_type": assessment.assessment_type,
            "start_date": assessment.start_date.isoformat(),
            "completion_date": assessment.actual_completion_date.isoformat() if assessment.actual_completion_date else None,
            "lead_assessor": assessment.lead_assessor_name,
            "methodology": assessment.methodology,
            "overall_risk_level": assessment.overall_risk_level.value if assessment.overall_risk_level else None,
            "total_risks": len(risk_items),
            "risks_by_level": by_level,
            "risks_by_category": by_category,
            "remediation_status": remediation_status,
            "executive_summary": assessment.executive_summary,
            "risk_items": [
                {
                    "risk_number": item.risk_number,
                    "title": item.title,
                    "category": item.category.value,
                    "risk_level": item.risk_level.value,
                    "likelihood": item.likelihood,
                    "impact": item.impact,
                    "inherent_score": item.inherent_risk_score,
                    "residual_score": item.residual_risk_score,
                    "status": item.status.value,
                    "hipaa_reference": item.hipaa_reference,
                }
                for item in risk_items
            ],
        }
