"""
Go-Live Service

Service for managing go-live checklists, status pages, and launch preparation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    GoLiveChecklist, GoLiveChecklistItem, StatusPageComponent, StatusPageIncident,
    ChecklistCategory, ChecklistItemStatus, HealthStatus, EnvironmentType
)
from ..schemas import (
    GoLiveChecklistCreate, GoLiveChecklistItemCreate, GoLiveChecklistItemUpdate,
    StatusPageComponentCreate, StatusPageIncidentCreate, StatusPageIncidentUpdate,
    GoLiveReadinessSummary
)


class GoLiveService:
    """Service for go-live preparation management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Go-Live Checklists
    # =========================================================================

    async def create_checklist(
        self,
        tenant_id: UUID,
        data: GoLiveChecklistCreate,
        created_by: Optional[UUID] = None
    ) -> GoLiveChecklist:
        """Create a new go-live checklist."""
        checklist = GoLiveChecklist(
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            target_go_live_date=data.target_go_live_date,
            environment=data.environment,
            required_approvers=data.required_approvers or [],
            release_notes_url=data.release_notes_url,
            rollback_plan_url=data.rollback_plan_url,
            created_by=created_by
        )
        self.db.add(checklist)
        await self.db.commit()
        await self.db.refresh(checklist)
        return checklist

    async def get_checklist(
        self,
        tenant_id: UUID,
        checklist_id: UUID
    ) -> Optional[GoLiveChecklist]:
        """Get checklist by ID."""
        result = await self.db.execute(
            select(GoLiveChecklist).where(
                and_(
                    GoLiveChecklist.tenant_id == tenant_id,
                    GoLiveChecklist.id == checklist_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_checklists(
        self,
        tenant_id: UUID,
        environment: Optional[EnvironmentType] = None
    ) -> List[GoLiveChecklist]:
        """List go-live checklists."""
        query = select(GoLiveChecklist).where(
            GoLiveChecklist.tenant_id == tenant_id
        )
        if environment:
            query = query.where(GoLiveChecklist.environment == environment)
        query = query.order_by(GoLiveChecklist.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def start_checklist(
        self,
        tenant_id: UUID,
        checklist_id: UUID
    ) -> Optional[GoLiveChecklist]:
        """Start a go-live checklist."""
        checklist = await self.get_checklist(tenant_id, checklist_id)
        if checklist:
            checklist.started_at = datetime.utcnow()
            checklist.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(checklist)
        return checklist

    async def _update_checklist_progress(
        self,
        checklist_id: UUID
    ) -> None:
        """Update checklist progress based on items."""
        # Get all items
        items_result = await self.db.execute(
            select(GoLiveChecklistItem).where(
                GoLiveChecklistItem.checklist_id == checklist_id
            )
        )
        items = list(items_result.scalars().all())

        checklist_result = await self.db.execute(
            select(GoLiveChecklist).where(GoLiveChecklist.id == checklist_id)
        )
        checklist = checklist_result.scalar_one_or_none()

        if checklist and items:
            total = len(items)
            completed = sum(1 for i in items if i.status == ChecklistItemStatus.COMPLETED)
            blocked = sum(1 for i in items if i.status == ChecklistItemStatus.BLOCKED)

            checklist.total_items = total
            checklist.completed_items = completed
            checklist.blocked_items = blocked
            checklist.completion_percentage = (completed / total * 100) if total > 0 else 0.0

            # Update blockers list
            blockers = []
            for item in items:
                if item.status == ChecklistItemStatus.BLOCKED:
                    blockers.append({
                        "item_id": str(item.id),
                        "title": item.title,
                        "reason": item.blocker_reason
                    })
            checklist.blockers = blockers

            # Check if ready (all critical items completed, no blockers)
            critical_pending = sum(
                1 for i in items
                if i.is_critical and i.status not in [
                    ChecklistItemStatus.COMPLETED,
                    ChecklistItemStatus.NOT_APPLICABLE
                ]
            )
            checklist.is_ready = critical_pending == 0 and blocked == 0

            if checklist.is_ready and checklist.completed_at is None and completed == total:
                checklist.completed_at = datetime.utcnow()

            checklist.updated_at = datetime.utcnow()
            await self.db.commit()

    async def approve_checklist(
        self,
        tenant_id: UUID,
        checklist_id: UUID,
        approver_id: UUID
    ) -> Optional[GoLiveChecklist]:
        """Add approval to checklist."""
        checklist = await self.get_checklist(tenant_id, checklist_id)
        if checklist:
            approvals = checklist.approvals_received or []
            approvals.append({
                "approver_id": str(approver_id),
                "approved_at": datetime.utcnow().isoformat()
            })
            checklist.approvals_received = approvals
            checklist.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(checklist)
        return checklist

    async def mark_go_live(
        self,
        tenant_id: UUID,
        checklist_id: UUID
    ) -> Optional[GoLiveChecklist]:
        """Mark checklist as gone live."""
        checklist = await self.get_checklist(tenant_id, checklist_id)
        if checklist and checklist.is_ready:
            checklist.actual_go_live_at = datetime.utcnow()
            checklist.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(checklist)
        return checklist

    # =========================================================================
    # Checklist Items
    # =========================================================================

    async def create_checklist_item(
        self,
        tenant_id: UUID,
        data: GoLiveChecklistItemCreate
    ) -> GoLiveChecklistItem:
        """Create a new checklist item."""
        item = GoLiveChecklistItem(
            checklist_id=data.checklist_id,
            title=data.title,
            description=data.description,
            category=data.category,
            is_critical=data.is_critical,
            is_blocker=data.is_blocker,
            assigned_to=data.assigned_to,
            owner_team=data.owner_team,
            verification_method=data.verification_method,
            depends_on=data.depends_on or [],
            due_date=data.due_date,
            display_order=data.display_order
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)

        # Update checklist progress
        await self._update_checklist_progress(data.checklist_id)

        return item

    async def get_checklist_item(
        self,
        tenant_id: UUID,
        item_id: UUID
    ) -> Optional[GoLiveChecklistItem]:
        """Get checklist item by ID."""
        result = await self.db.execute(
            select(GoLiveChecklistItem).where(
                GoLiveChecklistItem.id == item_id
            )
        )
        return result.scalar_one_or_none()

    async def list_checklist_items(
        self,
        tenant_id: UUID,
        checklist_id: UUID,
        category: Optional[ChecklistCategory] = None,
        status: Optional[ChecklistItemStatus] = None
    ) -> List[GoLiveChecklistItem]:
        """List checklist items."""
        query = select(GoLiveChecklistItem).where(
            GoLiveChecklistItem.checklist_id == checklist_id
        )
        if category:
            query = query.where(GoLiveChecklistItem.category == category)
        if status:
            query = query.where(GoLiveChecklistItem.status == status)
        query = query.order_by(
            GoLiveChecklistItem.category,
            GoLiveChecklistItem.display_order
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_checklist_item(
        self,
        tenant_id: UUID,
        item_id: UUID,
        data: GoLiveChecklistItemUpdate
    ) -> Optional[GoLiveChecklistItem]:
        """Update a checklist item."""
        item = await self.get_checklist_item(tenant_id, item_id)
        if item:
            if data.status is not None:
                item.status = data.status
                if data.status == ChecklistItemStatus.IN_PROGRESS and item.started_at is None:
                    item.started_at = datetime.utcnow()
                elif data.status == ChecklistItemStatus.COMPLETED:
                    item.completed_at = datetime.utcnow()
                elif data.status == ChecklistItemStatus.BLOCKED:
                    item.is_blocker = True
            if data.assigned_to is not None:
                item.assigned_to = data.assigned_to
            if data.evidence_url is not None:
                item.evidence_url = data.evidence_url
            if data.notes is not None:
                item.notes = data.notes
            if data.blocker_reason is not None:
                item.blocker_reason = data.blocker_reason

            item.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(item)

            # Update checklist progress
            await self._update_checklist_progress(item.checklist_id)

        return item

    async def complete_checklist_item(
        self,
        tenant_id: UUID,
        item_id: UUID,
        evidence_url: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Optional[GoLiveChecklistItem]:
        """Complete a checklist item."""
        item = await self.get_checklist_item(tenant_id, item_id)
        if item:
            item.status = ChecklistItemStatus.COMPLETED
            item.completed_at = datetime.utcnow()
            item.evidence_url = evidence_url
            item.notes = notes
            item.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(item)

            await self._update_checklist_progress(item.checklist_id)

        return item

    async def block_checklist_item(
        self,
        tenant_id: UUID,
        item_id: UUID,
        reason: str
    ) -> Optional[GoLiveChecklistItem]:
        """Mark a checklist item as blocked."""
        item = await self.get_checklist_item(tenant_id, item_id)
        if item:
            item.status = ChecklistItemStatus.BLOCKED
            item.is_blocker = True
            item.blocker_reason = reason
            item.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(item)

            await self._update_checklist_progress(item.checklist_id)

        return item

    async def get_pending_critical_items(
        self,
        tenant_id: UUID,
        checklist_id: UUID
    ) -> List[GoLiveChecklistItem]:
        """Get pending critical items."""
        result = await self.db.execute(
            select(GoLiveChecklistItem).where(
                and_(
                    GoLiveChecklistItem.checklist_id == checklist_id,
                    GoLiveChecklistItem.is_critical == True,
                    GoLiveChecklistItem.status.in_([
                        ChecklistItemStatus.PENDING,
                        ChecklistItemStatus.IN_PROGRESS,
                        ChecklistItemStatus.BLOCKED
                    ])
                )
            )
        )
        return list(result.scalars().all())

    # =========================================================================
    # Status Page Components
    # =========================================================================

    async def create_status_component(
        self,
        tenant_id: UUID,
        data: StatusPageComponentCreate
    ) -> StatusPageComponent:
        """Create a status page component."""
        component = StatusPageComponent(
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            group_name=data.group_name,
            display_order=data.display_order,
            health_check_id=data.health_check_id,
            show_on_public_page=data.show_on_public_page,
            show_uptime=data.show_uptime,
            statuspage_component_id=data.statuspage_component_id
        )
        self.db.add(component)
        await self.db.commit()
        await self.db.refresh(component)
        return component

    async def get_status_component(
        self,
        tenant_id: UUID,
        component_id: UUID
    ) -> Optional[StatusPageComponent]:
        """Get status component by ID."""
        result = await self.db.execute(
            select(StatusPageComponent).where(
                and_(
                    StatusPageComponent.tenant_id == tenant_id,
                    StatusPageComponent.id == component_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_status_components(
        self,
        tenant_id: UUID,
        public_only: bool = False
    ) -> List[StatusPageComponent]:
        """List status components."""
        query = select(StatusPageComponent).where(
            StatusPageComponent.tenant_id == tenant_id
        )
        if public_only:
            query = query.where(StatusPageComponent.show_on_public_page == True)
        query = query.order_by(
            StatusPageComponent.group_name,
            StatusPageComponent.display_order
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_component_status(
        self,
        tenant_id: UUID,
        component_id: UUID,
        status: HealthStatus
    ) -> Optional[StatusPageComponent]:
        """Update component status."""
        component = await self.get_status_component(tenant_id, component_id)
        if component:
            component.status = status
            component.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(component)
        return component

    # =========================================================================
    # Status Page Incidents
    # =========================================================================

    async def create_status_incident(
        self,
        tenant_id: UUID,
        data: StatusPageIncidentCreate
    ) -> StatusPageIncident:
        """Create a status page incident."""
        incident = StatusPageIncident(
            tenant_id=tenant_id,
            alert_incident_id=data.alert_incident_id,
            title=data.title,
            status=data.status,
            impact=data.impact,
            affected_components=data.affected_components or [],
            is_public=data.is_public,
            scheduled_maintenance=data.scheduled_maintenance,
            scheduled_start=data.scheduled_start,
            scheduled_end=data.scheduled_end,
            updates=[{
                "timestamp": datetime.utcnow().isoformat(),
                "status": data.status,
                "message": f"Incident created: {data.title}"
            }]
        )
        self.db.add(incident)
        await self.db.commit()
        await self.db.refresh(incident)
        return incident

    async def get_status_incident(
        self,
        tenant_id: UUID,
        incident_id: UUID
    ) -> Optional[StatusPageIncident]:
        """Get status incident by ID."""
        result = await self.db.execute(
            select(StatusPageIncident).where(
                and_(
                    StatusPageIncident.tenant_id == tenant_id,
                    StatusPageIncident.id == incident_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_status_incidents(
        self,
        tenant_id: UUID,
        public_only: bool = False,
        active_only: bool = False
    ) -> List[StatusPageIncident]:
        """List status incidents."""
        query = select(StatusPageIncident).where(
            StatusPageIncident.tenant_id == tenant_id
        )
        if public_only:
            query = query.where(StatusPageIncident.is_public == True)
        if active_only:
            query = query.where(StatusPageIncident.resolved_at.is_(None))
        query = query.order_by(StatusPageIncident.started_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_status_incident(
        self,
        tenant_id: UUID,
        incident_id: UUID,
        data: StatusPageIncidentUpdate
    ) -> Optional[StatusPageIncident]:
        """Update a status incident."""
        incident = await self.get_status_incident(tenant_id, incident_id)
        if incident:
            if data.status is not None:
                incident.status = data.status
                if data.status == "resolved":
                    incident.resolved_at = datetime.utcnow()
            if data.impact is not None:
                incident.impact = data.impact

            # Add update message
            if data.message:
                updates = incident.updates or []
                updates.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": data.status or incident.status,
                    "message": data.message
                })
                incident.updates = updates

            incident.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(incident)
        return incident

    async def resolve_status_incident(
        self,
        tenant_id: UUID,
        incident_id: UUID,
        message: str
    ) -> Optional[StatusPageIncident]:
        """Resolve a status incident."""
        incident = await self.get_status_incident(tenant_id, incident_id)
        if incident:
            incident.status = "resolved"
            incident.resolved_at = datetime.utcnow()

            updates = incident.updates or []
            updates.append({
                "timestamp": datetime.utcnow().isoformat(),
                "status": "resolved",
                "message": message
            })
            incident.updates = updates

            incident.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(incident)
        return incident

    # =========================================================================
    # Summary
    # =========================================================================

    async def get_go_live_readiness_summary(
        self,
        tenant_id: UUID
    ) -> GoLiveReadinessSummary:
        """Get go-live readiness summary."""
        # Total checklists
        checklists_result = await self.db.execute(
            select(func.count(GoLiveChecklist.id)).where(
                GoLiveChecklist.tenant_id == tenant_id
            )
        )
        total_checklists = checklists_result.scalar() or 0

        # Ready checklists
        ready_result = await self.db.execute(
            select(func.count(GoLiveChecklist.id)).where(
                and_(
                    GoLiveChecklist.tenant_id == tenant_id,
                    GoLiveChecklist.is_ready == True
                )
            )
        )
        ready_checklists = ready_result.scalar() or 0

        # Items summary
        items_result = await self.db.execute(
            select(
                GoLiveChecklistItem.status,
                func.count(GoLiveChecklistItem.id)
            ).join(
                GoLiveChecklist,
                GoLiveChecklistItem.checklist_id == GoLiveChecklist.id
            ).where(
                GoLiveChecklist.tenant_id == tenant_id
            ).group_by(GoLiveChecklistItem.status)
        )
        items_by_status = {str(row[0].value): row[1] for row in items_result.all()}

        checklist_items_completed = items_by_status.get(ChecklistItemStatus.COMPLETED.value, 0)
        checklist_items_pending = items_by_status.get(ChecklistItemStatus.PENDING.value, 0)
        checklist_items_blocked = items_by_status.get(ChecklistItemStatus.BLOCKED.value, 0)

        # Critical items pending
        critical_result = await self.db.execute(
            select(func.count(GoLiveChecklistItem.id)).join(
                GoLiveChecklist,
                GoLiveChecklistItem.checklist_id == GoLiveChecklist.id
            ).where(
                and_(
                    GoLiveChecklist.tenant_id == tenant_id,
                    GoLiveChecklistItem.is_critical == True,
                    GoLiveChecklistItem.status.in_([
                        ChecklistItemStatus.PENDING,
                        ChecklistItemStatus.IN_PROGRESS
                    ])
                )
            )
        )
        critical_items_pending = critical_result.scalar() or 0

        # Blockers
        blockers_result = await self.db.execute(
            select(GoLiveChecklistItem.title).join(
                GoLiveChecklist,
                GoLiveChecklistItem.checklist_id == GoLiveChecklist.id
            ).where(
                and_(
                    GoLiveChecklist.tenant_id == tenant_id,
                    GoLiveChecklistItem.status == ChecklistItemStatus.BLOCKED
                )
            ).limit(10)
        )
        blockers = [row[0] for row in blockers_result.all()]

        return GoLiveReadinessSummary(
            total_checklists=total_checklists,
            ready_checklists=ready_checklists,
            checklist_items_completed=checklist_items_completed,
            checklist_items_pending=checklist_items_pending,
            checklist_items_blocked=checklist_items_blocked,
            critical_items_pending=critical_items_pending,
            blockers=blockers
        )
