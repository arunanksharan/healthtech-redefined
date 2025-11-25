"""
Care Plan Management System

Comprehensive care plan management including:
- Goal-oriented care planning
- Intervention tracking
- Progress monitoring
- Care team coordination
- Patient engagement
- Chronic disease management

EPIC-006: US-006.7 Care Plan Management
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class GoalStatus(str, Enum):
    """Status of a care goal."""
    PROPOSED = "proposed"
    PLANNED = "planned"
    ACCEPTED = "accepted"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NOT_ACHIEVED = "not_achieved"


class GoalPriority(str, Enum):
    """Priority level for goals."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class InterventionStatus(str, Enum):
    """Status of a care intervention."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class CarePlanStatus(str, Enum):
    """Status of a care plan."""
    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    REVOKED = "revoked"
    COMPLETED = "completed"


class CarePlanCategory(str, Enum):
    """Category of care plan."""
    CHRONIC_DISEASE = "chronic_disease"
    PREVENTIVE = "preventive"
    POST_SURGICAL = "post_surgical"
    REHABILITATION = "rehabilitation"
    MENTAL_HEALTH = "mental_health"
    MATERNITY = "maternity"
    PEDIATRIC = "pediatric"
    PALLIATIVE = "palliative"
    WELLNESS = "wellness"


@dataclass
class CareGoalTarget:
    """Measurable target for a care goal."""
    target_id: str
    measure: str  # What is being measured (e.g., "HbA1c", "weight", "steps_per_day")
    detail_type: str  # quantity, range, codeable_concept
    detail_value: Any  # Target value
    unit: Optional[str] = None
    due_date: Optional[datetime] = None


@dataclass
class GoalProgress:
    """Progress entry for a care goal."""
    progress_id: str
    goal_id: str
    recorded_at: datetime
    recorded_by: str

    # Measurement
    measure: str
    value: Any
    unit: Optional[str] = None

    # Status at this point
    achievement_status: str = "in_progress"  # in_progress, improving, worsening, no_change, achieved
    notes: Optional[str] = None


@dataclass
class CareGoal:
    """
    Care goal for a patient.

    Based on FHIR Goal resource.
    """
    goal_id: str
    care_plan_id: str
    patient_id: str

    # Goal definition
    category: str = ""  # behavioral, dietary, physiological, safety
    description: str = ""
    priority: GoalPriority = GoalPriority.MEDIUM

    # Addresses (conditions this goal is addressing)
    addresses_conditions: List[str] = field(default_factory=list)

    # Targets
    targets: List[CareGoalTarget] = field(default_factory=list)

    # Timeline
    start_date: Optional[datetime] = None
    target_date: Optional[datetime] = None

    # Status
    status: GoalStatus = GoalStatus.PROPOSED
    achievement_status: str = "in_progress"

    # Progress tracking
    progress_entries: List[GoalProgress] = field(default_factory=list)

    # Responsibility
    expressed_by: Optional[str] = None  # patient, practitioner, related_person
    owner_id: Optional[str] = None  # Who is responsible

    notes: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class CareIntervention:
    """
    Care intervention/activity in a care plan.

    An action to achieve a goal.
    """
    intervention_id: str
    care_plan_id: str
    goal_ids: List[str] = field(default_factory=list)  # Goals this addresses

    # Intervention definition
    category: str = ""  # medication, procedure, education, counseling, monitoring
    description: str = ""
    reason: str = ""

    # Timing
    scheduled_timing: Optional[str] = None  # e.g., "daily", "weekly", "as_needed"
    scheduled_datetime: Optional[datetime] = None
    duration: Optional[str] = None

    # Assignment
    assigned_to_id: Optional[str] = None
    assigned_to_type: str = "practitioner"  # practitioner, patient, caregiver

    # Instructions
    instructions: str = ""
    reference_documents: List[str] = field(default_factory=list)

    # Status tracking
    status: InterventionStatus = InterventionStatus.PLANNED
    completed_at: Optional[datetime] = None
    outcome: Optional[str] = None
    outcome_notes: Optional[str] = None

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class CareTeamMember:
    """Member of a care team."""
    member_id: str
    care_plan_id: str

    provider_id: Optional[str] = None
    patient_id: Optional[str] = None  # For patient as team member
    caregiver_id: Optional[str] = None

    role: str = ""  # primary_care, specialist, nurse, social_worker, caregiver
    name: str = ""
    specialty: Optional[str] = None
    contact_info: Optional[str] = None

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: bool = True


@dataclass
class CarePlan:
    """
    Patient care plan.

    Based on FHIR CarePlan resource.
    """
    care_plan_id: str
    tenant_id: str
    patient_id: str

    # Plan details
    title: str = ""
    description: str = ""
    category: CarePlanCategory = CarePlanCategory.CHRONIC_DISEASE

    # Addresses conditions
    condition_ids: List[str] = field(default_factory=list)

    # Goals and interventions
    goals: List[CareGoal] = field(default_factory=list)
    interventions: List[CareIntervention] = field(default_factory=list)

    # Care team
    care_team: List[CareTeamMember] = field(default_factory=list)
    author_id: Optional[str] = None

    # Timeline
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    # Status
    status: CarePlanStatus = CarePlanStatus.DRAFT
    intent: str = "plan"  # proposal, plan, order, option

    # Related plans
    based_on: List[str] = field(default_factory=list)  # Protocol IDs
    replaces: Optional[str] = None  # Previous plan ID
    part_of: Optional[str] = None  # Parent plan ID

    # Documentation
    supporting_info: List[str] = field(default_factory=list)
    notes: List[Dict[str, Any]] = field(default_factory=list)

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class CareProtocol:
    """
    Reusable care protocol/pathway template.

    Defines standard goals and interventions for a condition.
    """
    protocol_id: str
    tenant_id: str

    name: str = ""
    description: str = ""
    category: CarePlanCategory = CarePlanCategory.CHRONIC_DISEASE

    # Target conditions
    applicable_conditions: List[str] = field(default_factory=list)

    # Template goals and interventions
    goal_templates: List[Dict[str, Any]] = field(default_factory=list)
    intervention_templates: List[Dict[str, Any]] = field(default_factory=list)

    # Evidence base
    evidence_level: str = ""  # A, B, C, D, Expert
    references: List[str] = field(default_factory=list)

    # Metadata
    version: str = "1.0"
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class CarePlanService:
    """
    Care plan management service.

    Handles:
    - Care plan creation from protocols
    - Goal tracking and progress
    - Intervention management
    - Care team coordination
    - Patient engagement
    """

    def __init__(self):
        self._protocols: Dict[str, CareProtocol] = {}

    async def create_care_plan(
        self,
        tenant_id: str,
        patient_id: str,
        title: str,
        category: CarePlanCategory = CarePlanCategory.CHRONIC_DISEASE,
        author_id: Optional[str] = None,
        condition_ids: Optional[List[str]] = None,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
        description: str = "",
    ) -> CarePlan:
        """Create a new care plan."""
        care_plan = CarePlan(
            care_plan_id=str(uuid4()),
            tenant_id=tenant_id,
            patient_id=patient_id,
            title=title,
            description=description,
            category=category,
            author_id=author_id,
            condition_ids=condition_ids or [],
            period_start=period_start or datetime.now(timezone.utc),
            period_end=period_end,
        )

        logger.info(f"Created care plan: {care_plan.care_plan_id}")
        return care_plan

    async def create_from_protocol(
        self,
        tenant_id: str,
        patient_id: str,
        protocol_id: str,
        author_id: Optional[str] = None,
        customizations: Optional[Dict[str, Any]] = None,
    ) -> CarePlan:
        """Create a care plan from a protocol template."""
        protocol = self._protocols.get(protocol_id)
        if not protocol:
            raise ValueError(f"Protocol not found: {protocol_id}")

        # Create care plan
        care_plan = await self.create_care_plan(
            tenant_id=tenant_id,
            patient_id=patient_id,
            title=protocol.name,
            category=protocol.category,
            author_id=author_id,
            description=protocol.description,
        )

        care_plan.based_on = [protocol_id]

        # Create goals from templates
        customizations = customizations or {}
        for goal_template in protocol.goal_templates:
            goal = await self.add_goal(
                care_plan=care_plan,
                description=goal_template.get("description", ""),
                category=goal_template.get("category", ""),
                priority=GoalPriority(goal_template.get("priority", "medium")),
                target_date_days=goal_template.get("target_date_days"),
            )

            # Add targets
            for target_template in goal_template.get("targets", []):
                await self.add_goal_target(
                    goal=goal,
                    measure=target_template["measure"],
                    detail_value=target_template["value"],
                    unit=target_template.get("unit"),
                )

        # Create interventions from templates
        for int_template in protocol.intervention_templates:
            await self.add_intervention(
                care_plan=care_plan,
                description=int_template.get("description", ""),
                category=int_template.get("category", ""),
                scheduled_timing=int_template.get("timing"),
                instructions=int_template.get("instructions", ""),
            )

        return care_plan

    async def add_goal(
        self,
        care_plan: CarePlan,
        description: str,
        category: str = "",
        priority: GoalPriority = GoalPriority.MEDIUM,
        start_date: Optional[datetime] = None,
        target_date: Optional[datetime] = None,
        target_date_days: Optional[int] = None,
        addresses_conditions: Optional[List[str]] = None,
        owner_id: Optional[str] = None,
    ) -> CareGoal:
        """Add a goal to the care plan."""
        if target_date_days and not target_date:
            target_date = datetime.now(timezone.utc) + timedelta(days=target_date_days)

        goal = CareGoal(
            goal_id=str(uuid4()),
            care_plan_id=care_plan.care_plan_id,
            patient_id=care_plan.patient_id,
            description=description,
            category=category,
            priority=priority,
            start_date=start_date or datetime.now(timezone.utc),
            target_date=target_date,
            addresses_conditions=addresses_conditions or care_plan.condition_ids,
            owner_id=owner_id,
            status=GoalStatus.PLANNED,
        )

        care_plan.goals.append(goal)
        care_plan.updated_at = datetime.now(timezone.utc)

        return goal

    async def add_goal_target(
        self,
        goal: CareGoal,
        measure: str,
        detail_value: Any,
        unit: Optional[str] = None,
        due_date: Optional[datetime] = None,
    ) -> CareGoalTarget:
        """Add a measurable target to a goal."""
        target = CareGoalTarget(
            target_id=str(uuid4()),
            measure=measure,
            detail_type="quantity" if isinstance(detail_value, (int, float)) else "string",
            detail_value=detail_value,
            unit=unit,
            due_date=due_date or goal.target_date,
        )

        goal.targets.append(target)
        return target

    async def record_goal_progress(
        self,
        goal: CareGoal,
        measure: str,
        value: Any,
        recorded_by: str,
        unit: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> GoalProgress:
        """Record progress toward a goal."""
        # Determine achievement status based on targets
        achievement = "in_progress"
        for target in goal.targets:
            if target.measure == measure:
                if isinstance(value, (int, float)) and isinstance(target.detail_value, (int, float)):
                    # Check if target is reached
                    if value >= target.detail_value * 0.95:  # Within 5%
                        achievement = "achieved"
                    elif len(goal.progress_entries) > 0:
                        prev = goal.progress_entries[-1]
                        if hasattr(prev, 'value') and isinstance(prev.value, (int, float)):
                            if value > prev.value:
                                achievement = "improving"
                            elif value < prev.value:
                                achievement = "worsening"
                            else:
                                achievement = "no_change"
                break

        progress = GoalProgress(
            progress_id=str(uuid4()),
            goal_id=goal.goal_id,
            recorded_at=datetime.now(timezone.utc),
            recorded_by=recorded_by,
            measure=measure,
            value=value,
            unit=unit,
            achievement_status=achievement,
            notes=notes,
        )

        goal.progress_entries.append(progress)
        goal.achievement_status = achievement

        # Update goal status if achieved
        if achievement == "achieved":
            goal.status = GoalStatus.COMPLETED

        return progress

    async def add_intervention(
        self,
        care_plan: CarePlan,
        description: str,
        category: str = "",
        goal_ids: Optional[List[str]] = None,
        scheduled_timing: Optional[str] = None,
        scheduled_datetime: Optional[datetime] = None,
        assigned_to_id: Optional[str] = None,
        instructions: str = "",
    ) -> CareIntervention:
        """Add an intervention to the care plan."""
        intervention = CareIntervention(
            intervention_id=str(uuid4()),
            care_plan_id=care_plan.care_plan_id,
            goal_ids=goal_ids or [],
            description=description,
            category=category,
            scheduled_timing=scheduled_timing,
            scheduled_datetime=scheduled_datetime,
            assigned_to_id=assigned_to_id,
            instructions=instructions,
        )

        care_plan.interventions.append(intervention)
        care_plan.updated_at = datetime.now(timezone.utc)

        return intervention

    async def complete_intervention(
        self,
        intervention: CareIntervention,
        outcome: str = "completed",
        outcome_notes: Optional[str] = None,
    ) -> CareIntervention:
        """Mark an intervention as completed."""
        intervention.status = InterventionStatus.COMPLETED
        intervention.completed_at = datetime.now(timezone.utc)
        intervention.outcome = outcome
        intervention.outcome_notes = outcome_notes

        return intervention

    async def add_care_team_member(
        self,
        care_plan: CarePlan,
        provider_id: Optional[str] = None,
        role: str = "",
        name: str = "",
        specialty: Optional[str] = None,
    ) -> CareTeamMember:
        """Add a care team member."""
        member = CareTeamMember(
            member_id=str(uuid4()),
            care_plan_id=care_plan.care_plan_id,
            provider_id=provider_id,
            role=role,
            name=name,
            specialty=specialty,
            start_date=datetime.now(timezone.utc),
        )

        care_plan.care_team.append(member)
        return member

    async def activate_care_plan(
        self,
        care_plan: CarePlan,
    ) -> CarePlan:
        """Activate a care plan."""
        care_plan.status = CarePlanStatus.ACTIVE

        # Activate all goals
        for goal in care_plan.goals:
            if goal.status == GoalStatus.PLANNED:
                goal.status = GoalStatus.ACTIVE

        # Activate all interventions
        for intervention in care_plan.interventions:
            if intervention.status == InterventionStatus.PLANNED:
                intervention.status = InterventionStatus.IN_PROGRESS

        care_plan.updated_at = datetime.now(timezone.utc)
        logger.info(f"Activated care plan: {care_plan.care_plan_id}")

        return care_plan

    async def complete_care_plan(
        self,
        care_plan: CarePlan,
    ) -> CarePlan:
        """Complete a care plan."""
        care_plan.status = CarePlanStatus.COMPLETED
        care_plan.period_end = datetime.now(timezone.utc)
        care_plan.updated_at = datetime.now(timezone.utc)

        logger.info(f"Completed care plan: {care_plan.care_plan_id}")
        return care_plan

    async def get_patient_care_plans(
        self,
        tenant_id: str,
        patient_id: str,
        status: Optional[CarePlanStatus] = None,
        category: Optional[CarePlanCategory] = None,
    ) -> List[CarePlan]:
        """Get care plans for a patient."""
        # Would query database
        return []

    async def get_pending_interventions(
        self,
        tenant_id: str,
        patient_id: Optional[str] = None,
        assigned_to_id: Optional[str] = None,
        due_before: Optional[datetime] = None,
    ) -> List[CareIntervention]:
        """Get pending interventions."""
        # Would query database
        return []

    async def create_protocol(
        self,
        tenant_id: str,
        name: str,
        category: CarePlanCategory,
        goal_templates: List[Dict[str, Any]],
        intervention_templates: List[Dict[str, Any]],
        description: str = "",
        applicable_conditions: Optional[List[str]] = None,
    ) -> CareProtocol:
        """Create a care protocol template."""
        protocol = CareProtocol(
            protocol_id=str(uuid4()),
            tenant_id=tenant_id,
            name=name,
            description=description,
            category=category,
            applicable_conditions=applicable_conditions or [],
            goal_templates=goal_templates,
            intervention_templates=intervention_templates,
        )

        self._protocols[protocol.protocol_id] = protocol
        return protocol

    async def get_protocols(
        self,
        tenant_id: str,
        category: Optional[CarePlanCategory] = None,
        condition: Optional[str] = None,
    ) -> List[CareProtocol]:
        """Get available protocols."""
        results = []
        for protocol in self._protocols.values():
            if protocol.tenant_id != tenant_id or not protocol.is_active:
                continue
            if category and protocol.category != category:
                continue
            if condition and condition not in protocol.applicable_conditions:
                continue
            results.append(protocol)
        return results
