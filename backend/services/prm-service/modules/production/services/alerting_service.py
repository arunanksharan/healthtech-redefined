"""
Alerting Service

Service for managing alert rules, incidents, on-call schedules, and escalation policies.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    AlertRule, AlertIncident, OnCallSchedule, EscalationPolicy,
    AlertSeverity, AlertStatus, IncidentStatus
)
from ..schemas import (
    AlertRuleCreate, AlertIncidentCreate, AlertIncidentUpdate,
    OnCallScheduleCreate, EscalationPolicyCreate, AlertingSummary
)


class AlertingService:
    """Service for alerting and incident management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._incident_counter = 0

    # =========================================================================
    # Alert Rules
    # =========================================================================

    async def create_alert_rule(
        self,
        tenant_id: UUID,
        data: AlertRuleCreate,
        created_by: Optional[UUID] = None
    ) -> AlertRule:
        """Create a new alert rule."""
        rule = AlertRule(
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            severity=data.severity,
            prometheus_query=data.prometheus_query,
            threshold_operator=data.threshold_operator,
            threshold_value=data.threshold_value,
            for_duration=data.for_duration,
            evaluation_interval=data.evaluation_interval,
            notification_channels=data.notification_channels or [],
            runbook_url=data.runbook_url,
            runbook_id=data.runbook_id,
            labels=data.labels or {},
            annotations=data.annotations or {},
            group_by=data.group_by or [],
            inhibit_rules=data.inhibit_rules or [],
            enabled=data.enabled,
            created_by=created_by
        )
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def get_alert_rule(
        self,
        tenant_id: UUID,
        rule_id: UUID
    ) -> Optional[AlertRule]:
        """Get alert rule by ID."""
        result = await self.db.execute(
            select(AlertRule).where(
                and_(
                    AlertRule.tenant_id == tenant_id,
                    AlertRule.id == rule_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_alert_rules(
        self,
        tenant_id: UUID,
        severity: Optional[AlertSeverity] = None,
        enabled_only: bool = False
    ) -> List[AlertRule]:
        """List alert rules."""
        query = select(AlertRule).where(AlertRule.tenant_id == tenant_id)
        if severity:
            query = query.where(AlertRule.severity == severity)
        if enabled_only:
            query = query.where(AlertRule.enabled == True)
        query = query.order_by(AlertRule.severity, AlertRule.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_alert_rule(
        self,
        tenant_id: UUID,
        rule_id: UUID,
        enabled: Optional[bool] = None,
        prometheus_query: Optional[str] = None,
        threshold_value: Optional[float] = None
    ) -> Optional[AlertRule]:
        """Update an alert rule."""
        rule = await self.get_alert_rule(tenant_id, rule_id)
        if rule:
            if enabled is not None:
                rule.enabled = enabled
            if prometheus_query:
                rule.prometheus_query = prometheus_query
            if threshold_value is not None:
                rule.threshold_value = threshold_value
            rule.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(rule)
        return rule

    async def silence_alert_rule(
        self,
        tenant_id: UUID,
        rule_id: UUID,
        duration_hours: int = 1
    ) -> Optional[AlertRule]:
        """Silence an alert rule for a duration."""
        rule = await self.get_alert_rule(tenant_id, rule_id)
        if rule:
            rule.silenced_until = datetime.utcnow() + timedelta(hours=duration_hours)
            rule.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(rule)
        return rule

    async def trigger_alert(
        self,
        tenant_id: UUID,
        rule_id: UUID
    ) -> Optional[AlertRule]:
        """Record that an alert was triggered."""
        rule = await self.get_alert_rule(tenant_id, rule_id)
        if rule:
            rule.last_triggered_at = datetime.utcnow()
            rule.trigger_count += 1
            await self.db.commit()
            await self.db.refresh(rule)
        return rule

    # =========================================================================
    # Incidents
    # =========================================================================

    async def _generate_incident_number(self, tenant_id: UUID) -> str:
        """Generate unique incident number."""
        result = await self.db.execute(
            select(func.count(AlertIncident.id)).where(
                AlertIncident.tenant_id == tenant_id
            )
        )
        count = result.scalar() or 0
        return f"INC-{count + 1:04d}"

    async def create_incident(
        self,
        tenant_id: UUID,
        data: AlertIncidentCreate
    ) -> AlertIncident:
        """Create a new incident."""
        incident_number = await self._generate_incident_number(tenant_id)

        incident = AlertIncident(
            tenant_id=tenant_id,
            alert_rule_id=data.alert_rule_id,
            incident_number=incident_number,
            title=data.title,
            description=data.description,
            severity=data.severity,
            status=IncidentStatus.TRIGGERED,
            affected_services=data.affected_services or [],
            affected_users=data.affected_users,
            customer_impact=data.customer_impact
        )
        self.db.add(incident)
        await self.db.commit()
        await self.db.refresh(incident)
        return incident

    async def get_incident(
        self,
        tenant_id: UUID,
        incident_id: UUID
    ) -> Optional[AlertIncident]:
        """Get incident by ID."""
        result = await self.db.execute(
            select(AlertIncident).where(
                and_(
                    AlertIncident.tenant_id == tenant_id,
                    AlertIncident.id == incident_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_incident_by_number(
        self,
        tenant_id: UUID,
        incident_number: str
    ) -> Optional[AlertIncident]:
        """Get incident by incident number."""
        result = await self.db.execute(
            select(AlertIncident).where(
                and_(
                    AlertIncident.tenant_id == tenant_id,
                    AlertIncident.incident_number == incident_number
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_incidents(
        self,
        tenant_id: UUID,
        status: Optional[IncidentStatus] = None,
        severity: Optional[AlertSeverity] = None,
        active_only: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[AlertIncident]:
        """List incidents."""
        query = select(AlertIncident).where(AlertIncident.tenant_id == tenant_id)

        if status:
            query = query.where(AlertIncident.status == status)
        if severity:
            query = query.where(AlertIncident.severity == severity)
        if active_only:
            query = query.where(
                AlertIncident.status.in_([
                    IncidentStatus.TRIGGERED,
                    IncidentStatus.ACKNOWLEDGED,
                    IncidentStatus.IN_PROGRESS
                ])
            )

        query = query.order_by(
            AlertIncident.severity,
            AlertIncident.triggered_at.desc()
        )
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def acknowledge_incident(
        self,
        tenant_id: UUID,
        incident_id: UUID,
        assigned_to: UUID
    ) -> Optional[AlertIncident]:
        """Acknowledge an incident."""
        incident = await self.get_incident(tenant_id, incident_id)
        if incident:
            incident.status = IncidentStatus.ACKNOWLEDGED
            incident.acknowledged_at = datetime.utcnow()
            incident.assigned_to = assigned_to

            # Calculate time to acknowledge
            if incident.triggered_at:
                delta = datetime.utcnow() - incident.triggered_at
                incident.time_to_acknowledge_seconds = int(delta.total_seconds())

            incident.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(incident)
        return incident

    async def update_incident(
        self,
        tenant_id: UUID,
        incident_id: UUID,
        data: AlertIncidentUpdate
    ) -> Optional[AlertIncident]:
        """Update an incident."""
        incident = await self.get_incident(tenant_id, incident_id)
        if incident:
            if data.status:
                incident.status = data.status
                if data.status == IncidentStatus.RESOLVED:
                    incident.resolved_at = datetime.utcnow()
                    if incident.triggered_at:
                        delta = datetime.utcnow() - incident.triggered_at
                        incident.time_to_resolve_seconds = int(delta.total_seconds())
                elif data.status == IncidentStatus.CLOSED:
                    incident.closed_at = datetime.utcnow()
            if data.assigned_to:
                incident.assigned_to = data.assigned_to
            if data.root_cause:
                incident.root_cause = data.root_cause
            if data.resolution_summary:
                incident.resolution_summary = data.resolution_summary
            if data.postmortem_url:
                incident.postmortem_url = data.postmortem_url

            incident.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(incident)
        return incident

    async def resolve_incident(
        self,
        tenant_id: UUID,
        incident_id: UUID,
        resolution_summary: str,
        root_cause: Optional[str] = None
    ) -> Optional[AlertIncident]:
        """Resolve an incident."""
        incident = await self.get_incident(tenant_id, incident_id)
        if incident:
            incident.status = IncidentStatus.RESOLVED
            incident.resolved_at = datetime.utcnow()
            incident.resolution_summary = resolution_summary
            incident.root_cause = root_cause

            if incident.triggered_at:
                delta = datetime.utcnow() - incident.triggered_at
                incident.time_to_resolve_seconds = int(delta.total_seconds())

            incident.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(incident)
        return incident

    async def escalate_incident(
        self,
        tenant_id: UUID,
        incident_id: UUID
    ) -> Optional[AlertIncident]:
        """Escalate an incident to the next level."""
        incident = await self.get_incident(tenant_id, incident_id)
        if incident:
            incident.escalation_level += 1
            incident.status = IncidentStatus.ESCALATED
            incident.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(incident)
        return incident

    # =========================================================================
    # On-Call Schedules
    # =========================================================================

    async def create_on_call_schedule(
        self,
        tenant_id: UUID,
        data: OnCallScheduleCreate
    ) -> OnCallSchedule:
        """Create a new on-call schedule."""
        schedule = OnCallSchedule(
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            team_name=data.team_name,
            members=data.members or [],
            rotation_type=data.rotation_type,
            rotation_start_day=data.rotation_start_day,
            rotation_start_hour=data.rotation_start_hour,
            handoff_time=data.handoff_time,
            timezone=data.timezone,
            pagerduty_schedule_id=data.pagerduty_schedule_id,
            opsgenie_schedule_id=data.opsgenie_schedule_id,
            enabled=data.enabled
        )

        # Set initial on-call if members exist
        if data.members and len(data.members) > 0:
            schedule.current_primary = data.members[0]
            if len(data.members) > 1:
                schedule.current_secondary = data.members[1]

        self.db.add(schedule)
        await self.db.commit()
        await self.db.refresh(schedule)
        return schedule

    async def get_on_call_schedule(
        self,
        tenant_id: UUID,
        schedule_id: UUID
    ) -> Optional[OnCallSchedule]:
        """Get on-call schedule by ID."""
        result = await self.db.execute(
            select(OnCallSchedule).where(
                and_(
                    OnCallSchedule.tenant_id == tenant_id,
                    OnCallSchedule.id == schedule_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_on_call_schedules(
        self,
        tenant_id: UUID,
        enabled_only: bool = False
    ) -> List[OnCallSchedule]:
        """List on-call schedules."""
        query = select(OnCallSchedule).where(OnCallSchedule.tenant_id == tenant_id)
        if enabled_only:
            query = query.where(OnCallSchedule.enabled == True)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_current_on_call(
        self,
        tenant_id: UUID,
        schedule_id: UUID
    ) -> Dict[str, Optional[UUID]]:
        """Get current on-call engineers."""
        schedule = await self.get_on_call_schedule(tenant_id, schedule_id)
        if schedule:
            return {
                "primary": schedule.current_primary,
                "secondary": schedule.current_secondary
            }
        return {"primary": None, "secondary": None}

    async def rotate_on_call(
        self,
        tenant_id: UUID,
        schedule_id: UUID
    ) -> Optional[OnCallSchedule]:
        """Rotate to next on-call member."""
        schedule = await self.get_on_call_schedule(tenant_id, schedule_id)
        if schedule and schedule.members:
            members = schedule.members
            if schedule.current_primary:
                try:
                    current_idx = members.index(schedule.current_primary)
                    next_primary_idx = (current_idx + 1) % len(members)
                    schedule.current_primary = members[next_primary_idx]
                    if len(members) > 1:
                        next_secondary_idx = (next_primary_idx + 1) % len(members)
                        schedule.current_secondary = members[next_secondary_idx]
                except ValueError:
                    schedule.current_primary = members[0]
                    if len(members) > 1:
                        schedule.current_secondary = members[1]

            schedule.next_rotation_at = datetime.utcnow() + timedelta(days=7)
            schedule.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(schedule)
        return schedule

    # =========================================================================
    # Escalation Policies
    # =========================================================================

    async def create_escalation_policy(
        self,
        tenant_id: UUID,
        data: EscalationPolicyCreate
    ) -> EscalationPolicy:
        """Create a new escalation policy."""
        policy = EscalationPolicy(
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            escalation_levels=data.escalation_levels,
            repeat_enabled=data.repeat_enabled,
            repeat_limit=data.repeat_limit,
            require_acknowledgment=data.require_acknowledgment,
            acknowledgment_timeout_minutes=data.acknowledgment_timeout_minutes,
            pagerduty_policy_id=data.pagerduty_policy_id,
            opsgenie_policy_id=data.opsgenie_policy_id,
            enabled=data.enabled
        )
        self.db.add(policy)
        await self.db.commit()
        await self.db.refresh(policy)
        return policy

    async def get_escalation_policy(
        self,
        tenant_id: UUID,
        policy_id: UUID
    ) -> Optional[EscalationPolicy]:
        """Get escalation policy by ID."""
        result = await self.db.execute(
            select(EscalationPolicy).where(
                and_(
                    EscalationPolicy.tenant_id == tenant_id,
                    EscalationPolicy.id == policy_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_escalation_policies(
        self,
        tenant_id: UUID,
        enabled_only: bool = False
    ) -> List[EscalationPolicy]:
        """List escalation policies."""
        query = select(EscalationPolicy).where(EscalationPolicy.tenant_id == tenant_id)
        if enabled_only:
            query = query.where(EscalationPolicy.enabled == True)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # =========================================================================
    # Statistics and Summary
    # =========================================================================

    async def calculate_mttr(
        self,
        tenant_id: UUID,
        days: int = 30
    ) -> Optional[float]:
        """Calculate Mean Time to Resolve."""
        since = datetime.utcnow() - timedelta(days=days)
        result = await self.db.execute(
            select(func.avg(AlertIncident.time_to_resolve_seconds)).where(
                and_(
                    AlertIncident.tenant_id == tenant_id,
                    AlertIncident.resolved_at >= since,
                    AlertIncident.time_to_resolve_seconds.isnot(None)
                )
            )
        )
        avg_seconds = result.scalar()
        if avg_seconds:
            return avg_seconds / 60  # Return in minutes
        return None

    async def calculate_mttd(
        self,
        tenant_id: UUID,
        days: int = 30
    ) -> Optional[float]:
        """Calculate Mean Time to Detect (acknowledge)."""
        since = datetime.utcnow() - timedelta(days=days)
        result = await self.db.execute(
            select(func.avg(AlertIncident.time_to_acknowledge_seconds)).where(
                and_(
                    AlertIncident.tenant_id == tenant_id,
                    AlertIncident.acknowledged_at >= since,
                    AlertIncident.time_to_acknowledge_seconds.isnot(None)
                )
            )
        )
        avg_seconds = result.scalar()
        if avg_seconds:
            return avg_seconds / 60  # Return in minutes
        return None

    async def get_alerting_summary(
        self,
        tenant_id: UUID
    ) -> AlertingSummary:
        """Get alerting summary."""
        # Alert rules
        total_rules_result = await self.db.execute(
            select(func.count(AlertRule.id)).where(AlertRule.tenant_id == tenant_id)
        )
        total_alert_rules = total_rules_result.scalar() or 0

        enabled_rules_result = await self.db.execute(
            select(func.count(AlertRule.id)).where(
                and_(
                    AlertRule.tenant_id == tenant_id,
                    AlertRule.enabled == True
                )
            )
        )
        enabled_alert_rules = enabled_rules_result.scalar() or 0

        # Active incidents
        active_result = await self.db.execute(
            select(func.count(AlertIncident.id)).where(
                and_(
                    AlertIncident.tenant_id == tenant_id,
                    AlertIncident.status.in_([
                        IncidentStatus.TRIGGERED,
                        IncidentStatus.ACKNOWLEDGED,
                        IncidentStatus.IN_PROGRESS
                    ])
                )
            )
        )
        active_incidents = active_result.scalar() or 0

        # Incidents by severity
        severity_result = await self.db.execute(
            select(
                AlertIncident.severity,
                func.count(AlertIncident.id)
            ).where(
                and_(
                    AlertIncident.tenant_id == tenant_id,
                    AlertIncident.status.in_([
                        IncidentStatus.TRIGGERED,
                        IncidentStatus.ACKNOWLEDGED,
                        IncidentStatus.IN_PROGRESS
                    ])
                )
            ).group_by(AlertIncident.severity)
        )
        incidents_by_severity = {str(row[0].value): row[1] for row in severity_result.all()}

        # Incidents by status
        status_result = await self.db.execute(
            select(
                AlertIncident.status,
                func.count(AlertIncident.id)
            ).where(
                AlertIncident.tenant_id == tenant_id
            ).group_by(AlertIncident.status)
        )
        incidents_by_status = {str(row[0].value): row[1] for row in status_result.all()}

        # MTTR and MTTD
        mttr = await self.calculate_mttr(tenant_id)
        mttd = await self.calculate_mttd(tenant_id)

        # On-call schedules
        schedules_result = await self.db.execute(
            select(func.count(OnCallSchedule.id)).where(
                and_(
                    OnCallSchedule.tenant_id == tenant_id,
                    OnCallSchedule.enabled == True
                )
            )
        )
        on_call_schedules = schedules_result.scalar() or 0

        return AlertingSummary(
            total_alert_rules=total_alert_rules,
            enabled_alert_rules=enabled_alert_rules,
            active_incidents=active_incidents,
            incidents_by_severity=incidents_by_severity,
            incidents_by_status=incidents_by_status,
            mttr_minutes=mttr,
            mttd_minutes=mttd,
            on_call_schedules=on_call_schedules
        )
