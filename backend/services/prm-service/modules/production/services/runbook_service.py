"""
Runbook Service

Service for managing operational runbooks and incident playbooks.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    Runbook, IncidentPlaybook, RunbookType, AlertSeverity
)
from ..schemas import (
    RunbookCreate, RunbookUpdate, IncidentPlaybookCreate,
    OperationalReadinessSummary
)


class RunbookService:
    """Service for runbook management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Runbooks
    # =========================================================================

    async def create_runbook(
        self,
        tenant_id: UUID,
        data: RunbookCreate,
        created_by: Optional[UUID] = None
    ) -> Runbook:
        """Create a new runbook."""
        runbook = Runbook(
            tenant_id=tenant_id,
            title=data.title,
            description=data.description,
            runbook_type=data.runbook_type,
            steps=data.steps,
            prerequisites=data.prerequisites or [],
            required_access=data.required_access or [],
            associated_alerts=data.associated_alerts or [],
            affected_services=data.affected_services or [],
            automated_steps=data.automated_steps or [],
            automation_script_url=data.automation_script_url,
            estimated_duration_minutes=data.estimated_duration_minutes,
            difficulty_level=data.difficulty_level,
            owner_team=data.owner_team,
            tags=data.tags or [],
            created_by=created_by
        )
        self.db.add(runbook)
        await self.db.commit()
        await self.db.refresh(runbook)
        return runbook

    async def get_runbook(
        self,
        tenant_id: UUID,
        runbook_id: UUID
    ) -> Optional[Runbook]:
        """Get runbook by ID."""
        result = await self.db.execute(
            select(Runbook).where(
                and_(
                    Runbook.tenant_id == tenant_id,
                    Runbook.id == runbook_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_runbooks(
        self,
        tenant_id: UUID,
        runbook_type: Optional[RunbookType] = None,
        affected_service: Optional[str] = None,
        active_only: bool = False
    ) -> List[Runbook]:
        """List runbooks."""
        query = select(Runbook).where(Runbook.tenant_id == tenant_id)

        if runbook_type:
            query = query.where(Runbook.runbook_type == runbook_type)
        if active_only:
            query = query.where(Runbook.is_active == True)
        if affected_service:
            query = query.where(Runbook.affected_services.contains([affected_service]))

        query = query.order_by(Runbook.title)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_runbook(
        self,
        tenant_id: UUID,
        runbook_id: UUID,
        data: RunbookUpdate
    ) -> Optional[Runbook]:
        """Update a runbook."""
        runbook = await self.get_runbook(tenant_id, runbook_id)
        if runbook:
            if data.title is not None:
                runbook.title = data.title
            if data.description is not None:
                runbook.description = data.description
            if data.steps is not None:
                runbook.steps = data.steps
            if data.prerequisites is not None:
                runbook.prerequisites = data.prerequisites
            if data.required_access is not None:
                runbook.required_access = data.required_access
            if data.affected_services is not None:
                runbook.affected_services = data.affected_services
            if data.estimated_duration_minutes is not None:
                runbook.estimated_duration_minutes = data.estimated_duration_minutes
            if data.is_active is not None:
                runbook.is_active = data.is_active

            runbook.version += 1
            runbook.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(runbook)
        return runbook

    async def record_runbook_usage(
        self,
        tenant_id: UUID,
        runbook_id: UUID
    ) -> Optional[Runbook]:
        """Record that a runbook was used."""
        runbook = await self.get_runbook(tenant_id, runbook_id)
        if runbook:
            runbook.times_used += 1
            runbook.last_used_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(runbook)
        return runbook

    async def mark_runbook_reviewed(
        self,
        tenant_id: UUID,
        runbook_id: UUID,
        next_review_days: int = 90
    ) -> Optional[Runbook]:
        """Mark a runbook as reviewed."""
        runbook = await self.get_runbook(tenant_id, runbook_id)
        if runbook:
            runbook.last_reviewed_at = datetime.utcnow()
            runbook.next_review_date = datetime.utcnow() + timedelta(days=next_review_days)
            runbook.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(runbook)
        return runbook

    async def get_runbooks_needing_review(
        self,
        tenant_id: UUID
    ) -> List[Runbook]:
        """Get runbooks that need review."""
        result = await self.db.execute(
            select(Runbook).where(
                and_(
                    Runbook.tenant_id == tenant_id,
                    Runbook.is_active == True,
                    Runbook.next_review_date <= datetime.utcnow()
                )
            )
        )
        return list(result.scalars().all())

    async def search_runbooks(
        self,
        tenant_id: UUID,
        query: str
    ) -> List[Runbook]:
        """Search runbooks by title or description."""
        result = await self.db.execute(
            select(Runbook).where(
                and_(
                    Runbook.tenant_id == tenant_id,
                    Runbook.is_active == True,
                    (
                        Runbook.title.ilike(f"%{query}%") |
                        Runbook.description.ilike(f"%{query}%")
                    )
                )
            )
        )
        return list(result.scalars().all())

    async def get_runbooks_for_alert(
        self,
        tenant_id: UUID,
        alert_id: UUID
    ) -> List[Runbook]:
        """Get runbooks associated with an alert."""
        result = await self.db.execute(
            select(Runbook).where(
                and_(
                    Runbook.tenant_id == tenant_id,
                    Runbook.is_active == True,
                    Runbook.associated_alerts.contains([alert_id])
                )
            )
        )
        return list(result.scalars().all())

    # =========================================================================
    # Incident Playbooks
    # =========================================================================

    async def create_playbook(
        self,
        tenant_id: UUID,
        data: IncidentPlaybookCreate,
        created_by: Optional[UUID] = None
    ) -> IncidentPlaybook:
        """Create a new incident playbook."""
        playbook = IncidentPlaybook(
            tenant_id=tenant_id,
            title=data.title,
            description=data.description,
            severity=data.severity,
            symptoms=data.symptoms,
            diagnosis_steps=data.diagnosis_steps,
            immediate_actions=data.immediate_actions,
            long_term_fixes=data.long_term_fixes or [],
            communication_template=data.communication_template,
            stakeholders_to_notify=data.stakeholders_to_notify or [],
            related_runbooks=data.related_runbooks or [],
            related_alerts=data.related_alerts or [],
            created_by=created_by
        )
        self.db.add(playbook)
        await self.db.commit()
        await self.db.refresh(playbook)
        return playbook

    async def get_playbook(
        self,
        tenant_id: UUID,
        playbook_id: UUID
    ) -> Optional[IncidentPlaybook]:
        """Get playbook by ID."""
        result = await self.db.execute(
            select(IncidentPlaybook).where(
                and_(
                    IncidentPlaybook.tenant_id == tenant_id,
                    IncidentPlaybook.id == playbook_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_playbooks(
        self,
        tenant_id: UUID,
        severity: Optional[AlertSeverity] = None,
        active_only: bool = False
    ) -> List[IncidentPlaybook]:
        """List incident playbooks."""
        query = select(IncidentPlaybook).where(
            IncidentPlaybook.tenant_id == tenant_id
        )
        if severity:
            query = query.where(IncidentPlaybook.severity == severity)
        if active_only:
            query = query.where(IncidentPlaybook.is_active == True)
        query = query.order_by(IncidentPlaybook.severity, IncidentPlaybook.title)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def record_playbook_usage(
        self,
        tenant_id: UUID,
        playbook_id: UUID,
        resolution_minutes: Optional[float] = None
    ) -> Optional[IncidentPlaybook]:
        """Record that a playbook was used."""
        playbook = await self.get_playbook(tenant_id, playbook_id)
        if playbook:
            playbook.times_used += 1

            if resolution_minutes is not None:
                # Update average resolution time
                if playbook.avg_resolution_minutes:
                    total = playbook.avg_resolution_minutes * (playbook.times_used - 1)
                    playbook.avg_resolution_minutes = (total + resolution_minutes) / playbook.times_used
                else:
                    playbook.avg_resolution_minutes = resolution_minutes

            playbook.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(playbook)
        return playbook

    async def get_playbooks_for_symptoms(
        self,
        tenant_id: UUID,
        symptoms_keywords: List[str]
    ) -> List[IncidentPlaybook]:
        """Find playbooks matching symptoms."""
        # This is a simplified version - in production, use full-text search
        playbooks = await self.list_playbooks(tenant_id, active_only=True)
        matching = []

        for playbook in playbooks:
            for symptom in playbook.symptoms or []:
                symptom_text = str(symptom).lower()
                for keyword in symptoms_keywords:
                    if keyword.lower() in symptom_text:
                        matching.append(playbook)
                        break
                else:
                    continue
                break

        return matching

    async def get_playbooks_for_alert(
        self,
        tenant_id: UUID,
        alert_id: UUID
    ) -> List[IncidentPlaybook]:
        """Get playbooks associated with an alert."""
        result = await self.db.execute(
            select(IncidentPlaybook).where(
                and_(
                    IncidentPlaybook.tenant_id == tenant_id,
                    IncidentPlaybook.is_active == True,
                    IncidentPlaybook.related_alerts.contains([alert_id])
                )
            )
        )
        return list(result.scalars().all())

    # =========================================================================
    # Summary
    # =========================================================================

    async def get_operational_readiness_summary(
        self,
        tenant_id: UUID
    ) -> OperationalReadinessSummary:
        """Get operational readiness summary."""
        # Total runbooks
        runbooks_result = await self.db.execute(
            select(func.count(Runbook.id)).where(
                and_(
                    Runbook.tenant_id == tenant_id,
                    Runbook.is_active == True
                )
            )
        )
        total_runbooks = runbooks_result.scalar() or 0

        # Total playbooks
        playbooks_result = await self.db.execute(
            select(func.count(IncidentPlaybook.id)).where(
                and_(
                    IncidentPlaybook.tenant_id == tenant_id,
                    IncidentPlaybook.is_active == True
                )
            )
        )
        total_playbooks = playbooks_result.scalar() or 0

        # Runbooks by type
        type_result = await self.db.execute(
            select(
                Runbook.runbook_type,
                func.count(Runbook.id)
            ).where(
                and_(
                    Runbook.tenant_id == tenant_id,
                    Runbook.is_active == True
                )
            ).group_by(Runbook.runbook_type)
        )
        runbooks_by_type = {str(row[0].value): row[1] for row in type_result.all()}

        # Recently used runbooks (last 30 days)
        recent_date = datetime.utcnow() - timedelta(days=30)
        recent_result = await self.db.execute(
            select(func.count(Runbook.id)).where(
                and_(
                    Runbook.tenant_id == tenant_id,
                    Runbook.is_active == True,
                    Runbook.last_used_at >= recent_date
                )
            )
        )
        runbooks_recently_used = recent_result.scalar() or 0

        return OperationalReadinessSummary(
            total_runbooks=total_runbooks,
            total_playbooks=total_playbooks,
            runbooks_by_type=runbooks_by_type,
            runbooks_recently_used=runbooks_recently_used
        )
