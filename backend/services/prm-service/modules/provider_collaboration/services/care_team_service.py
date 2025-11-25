"""
Provider Collaboration Care Team Service
EPIC-015: Care team coordination and management
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from modules.provider_collaboration.models import (
    CareTeam, CareTeamMember, CareTeamTask, ProviderConversation, ConversationParticipant,
    CollaborationAuditLog, CareTeamStatus, CareTeamRole, ConversationType, MessagePriority
)
from modules.provider_collaboration.schemas import (
    CareTeamCreate, CareTeamUpdate, CareTeamMemberCreate, CareTeamMemberUpdate,
    CareTeamGoalUpdate, CareTeamTaskCreate, CareTeamTaskUpdate,
    CareTeamResponse, CareTeamMemberResponse, CareTeamTaskResponse,
    CareTeamListResponse, CareTeamGoal
)


class CareTeamService:
    """
    Handles care team management including:
    - Team creation and management
    - Member roles and responsibilities
    - Task assignment and tracking
    - Care plans and goals
    """

    def __init__(self):
        pass

    async def create_care_team(
        self,
        db: AsyncSession,
        provider_id: UUID,
        tenant_id: UUID,
        data: CareTeamCreate,
        ip_address: str = None
    ) -> CareTeamResponse:
        """Create a new care team"""

        # Create care team
        care_team = CareTeam(
            id=uuid4(),
            tenant_id=tenant_id,
            patient_id=data.patient_id,
            encounter_id=data.encounter_id,
            name=data.name,
            description=data.description,
            team_type=data.team_type,
            lead_provider_id=data.lead_provider_id or provider_id,
            status=CareTeamStatus.ACTIVE,
            status_updated_at=datetime.now(timezone.utc)
        )
        db.add(care_team)

        # Create conversation for care team
        conversation = ProviderConversation(
            id=uuid4(),
            tenant_id=tenant_id,
            type=ConversationType.CARE_TEAM,
            name=data.name,
            description=f"Care team conversation for {data.name}",
            patient_id=data.patient_id,
            care_team_id=care_team.id,
            created_by=provider_id,
            is_encrypted=True
        )
        db.add(conversation)

        care_team.conversation_id = conversation.id

        # Add creator as lead/owner
        creator_member = CareTeamMember(
            id=uuid4(),
            care_team_id=care_team.id,
            provider_id=provider_id,
            role=CareTeamRole.ATTENDING_PHYSICIAN,
            is_primary=True,
            is_active=True
        )
        db.add(creator_member)

        creator_participant = ConversationParticipant(
            id=uuid4(),
            conversation_id=conversation.id,
            provider_id=provider_id,
            role="owner",
            care_team_role=CareTeamRole.ATTENDING_PHYSICIAN,
            can_add_members=True,
            can_remove_members=True,
            can_edit_settings=True
        )
        db.add(creator_participant)

        # Add other members
        for member_data in data.members:
            if member_data.provider_id != provider_id:
                member = CareTeamMember(
                    id=uuid4(),
                    care_team_id=care_team.id,
                    provider_id=member_data.provider_id,
                    role=CareTeamRole(member_data.role.value),
                    custom_role=member_data.custom_role,
                    responsibilities=member_data.responsibilities,
                    is_primary=member_data.is_primary,
                    is_active=True
                )
                db.add(member)

                participant = ConversationParticipant(
                    id=uuid4(),
                    conversation_id=conversation.id,
                    provider_id=member_data.provider_id,
                    role="member",
                    care_team_role=CareTeamRole(member_data.role.value)
                )
                db.add(participant)

        # Log action
        audit_log = CollaborationAuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            provider_id=provider_id,
            action="care_team_created",
            action_category="care_team",
            action_description=f"Created care team: {data.name}",
            entity_type="care_team",
            entity_id=care_team.id,
            patient_id=data.patient_id,
            ip_address=ip_address
        )
        db.add(audit_log)

        await db.commit()

        return await self.get_care_team(db, provider_id, tenant_id, care_team.id)

    async def get_care_team(
        self,
        db: AsyncSession,
        provider_id: UUID,
        tenant_id: UUID,
        care_team_id: UUID
    ) -> CareTeamResponse:
        """Get care team details"""

        result = await db.execute(
            select(CareTeam)
            .options(
                selectinload(CareTeam.members),
                selectinload(CareTeam.tasks)
            )
            .where(
                and_(
                    CareTeam.id == care_team_id,
                    CareTeam.tenant_id == tenant_id
                )
            )
        )
        care_team = result.scalar_one_or_none()

        if not care_team:
            raise ValueError("Care team not found")

        # Check access - must be a member
        is_member = any(m.provider_id == provider_id and m.is_active for m in care_team.members)
        if not is_member:
            raise ValueError("Not authorized to view this care team")

        members = [
            CareTeamMemberResponse(
                id=m.id,
                provider_id=m.provider_id,
                role=m.role.value,
                custom_role=m.custom_role,
                responsibilities=m.responsibilities,
                is_active=m.is_active,
                is_primary=m.is_primary,
                joined_at=m.joined_at
            )
            for m in care_team.members if m.is_active
        ]

        pending_tasks_count = sum(1 for t in care_team.tasks if t.status == "pending")

        goals = []
        if care_team.goals:
            goals = [CareTeamGoal(**g) for g in care_team.goals]

        return CareTeamResponse(
            id=care_team.id,
            patient_id=care_team.patient_id,
            name=care_team.name,
            description=care_team.description,
            team_type=care_team.team_type,
            lead_provider_id=care_team.lead_provider_id,
            status=care_team.status.value,
            conversation_id=care_team.conversation_id,
            care_plan=care_team.care_plan,
            goals=goals,
            members=members,
            pending_tasks_count=pending_tasks_count,
            created_at=care_team.created_at,
            updated_at=care_team.updated_at
        )

    async def list_care_teams(
        self,
        db: AsyncSession,
        provider_id: UUID,
        tenant_id: UUID,
        patient_id: Optional[UUID] = None,
        status: Optional[CareTeamStatus] = None,
        page: int = 1,
        page_size: int = 20
    ) -> CareTeamListResponse:
        """List care teams for a provider"""

        # Get care team IDs where provider is a member
        member_subquery = (
            select(CareTeamMember.care_team_id)
            .where(
                and_(
                    CareTeamMember.provider_id == provider_id,
                    CareTeamMember.is_active == True
                )
            )
        )

        query = (
            select(CareTeam)
            .options(selectinload(CareTeam.members))
            .where(
                and_(
                    CareTeam.tenant_id == tenant_id,
                    CareTeam.id.in_(member_subquery)
                )
            )
        )

        if patient_id:
            query = query.where(CareTeam.patient_id == patient_id)

        if status:
            query = query.where(CareTeam.status == status)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Get paginated results
        query = query.order_by(desc(CareTeam.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        care_teams = result.scalars().all()

        return CareTeamListResponse(
            care_teams=[
                CareTeamResponse(
                    id=ct.id,
                    patient_id=ct.patient_id,
                    name=ct.name,
                    description=ct.description,
                    team_type=ct.team_type,
                    lead_provider_id=ct.lead_provider_id,
                    status=ct.status.value,
                    conversation_id=ct.conversation_id,
                    care_plan=ct.care_plan,
                    goals=[CareTeamGoal(**g) for g in ct.goals] if ct.goals else [],
                    members=[
                        CareTeamMemberResponse(
                            id=m.id,
                            provider_id=m.provider_id,
                            role=m.role.value,
                            custom_role=m.custom_role,
                            is_active=m.is_active,
                            is_primary=m.is_primary,
                            joined_at=m.joined_at
                        )
                        for m in ct.members if m.is_active
                    ],
                    pending_tasks_count=0,
                    created_at=ct.created_at,
                    updated_at=ct.updated_at
                )
                for ct in care_teams
            ],
            total=total,
            page=page,
            page_size=page_size
        )

    async def add_member(
        self,
        db: AsyncSession,
        provider_id: UUID,
        care_team_id: UUID,
        data: CareTeamMemberCreate
    ) -> CareTeamMemberResponse:
        """Add member to care team"""

        result = await db.execute(
            select(CareTeam)
            .options(selectinload(CareTeam.members))
            .where(CareTeam.id == care_team_id)
        )
        care_team = result.scalar_one_or_none()

        if not care_team:
            raise ValueError("Care team not found")

        # Check if requester is lead or attending
        requester_is_lead = care_team.lead_provider_id == provider_id
        requester_is_attending = any(
            m.provider_id == provider_id and m.role == CareTeamRole.ATTENDING_PHYSICIAN
            for m in care_team.members
        )

        if not (requester_is_lead or requester_is_attending):
            raise ValueError("Not authorized to add members")

        # Check if already a member
        existing = next(
            (m for m in care_team.members if m.provider_id == data.provider_id),
            None
        )

        if existing:
            if existing.is_active:
                raise ValueError("Provider is already a member")
            # Reactivate
            existing.is_active = True
            existing.left_at = None
            existing.role = CareTeamRole(data.role.value)
            await db.commit()
            await db.refresh(existing)
            return CareTeamMemberResponse(
                id=existing.id,
                provider_id=existing.provider_id,
                role=existing.role.value,
                custom_role=existing.custom_role,
                is_active=existing.is_active,
                is_primary=existing.is_primary,
                joined_at=existing.joined_at
            )

        member = CareTeamMember(
            id=uuid4(),
            care_team_id=care_team_id,
            provider_id=data.provider_id,
            role=CareTeamRole(data.role.value),
            custom_role=data.custom_role,
            responsibilities=data.responsibilities,
            is_primary=data.is_primary,
            is_active=True
        )
        db.add(member)

        # Add to conversation
        if care_team.conversation_id:
            participant = ConversationParticipant(
                id=uuid4(),
                conversation_id=care_team.conversation_id,
                provider_id=data.provider_id,
                role="member",
                care_team_role=CareTeamRole(data.role.value)
            )
            db.add(participant)

        await db.commit()
        await db.refresh(member)

        return CareTeamMemberResponse(
            id=member.id,
            provider_id=member.provider_id,
            role=member.role.value,
            custom_role=member.custom_role,
            responsibilities=member.responsibilities,
            is_active=member.is_active,
            is_primary=member.is_primary,
            joined_at=member.joined_at
        )

    async def remove_member(
        self,
        db: AsyncSession,
        provider_id: UUID,
        care_team_id: UUID,
        member_provider_id: UUID
    ):
        """Remove member from care team"""

        result = await db.execute(
            select(CareTeam).where(CareTeam.id == care_team_id)
        )
        care_team = result.scalar_one_or_none()

        if not care_team:
            raise ValueError("Care team not found")

        if care_team.lead_provider_id != provider_id:
            raise ValueError("Only team lead can remove members")

        await db.execute(
            update(CareTeamMember).where(
                and_(
                    CareTeamMember.care_team_id == care_team_id,
                    CareTeamMember.provider_id == member_provider_id
                )
            ).values(
                is_active=False,
                left_at=datetime.now(timezone.utc)
            )
        )

        # Remove from conversation
        if care_team.conversation_id:
            await db.execute(
                update(ConversationParticipant).where(
                    and_(
                        ConversationParticipant.conversation_id == care_team.conversation_id,
                        ConversationParticipant.provider_id == member_provider_id
                    )
                ).values(
                    is_active=False,
                    left_at=datetime.now(timezone.utc)
                )
            )

        await db.commit()

    async def update_goals(
        self,
        db: AsyncSession,
        provider_id: UUID,
        care_team_id: UUID,
        data: CareTeamGoalUpdate
    ) -> CareTeamResponse:
        """Update care team goals"""

        result = await db.execute(
            select(CareTeam).where(CareTeam.id == care_team_id)
        )
        care_team = result.scalar_one_or_none()

        if not care_team:
            raise ValueError("Care team not found")

        goals_data = [g.dict() for g in data.goals]
        for g in goals_data:
            if not g.get('id'):
                g['id'] = str(uuid4())

        care_team.goals = goals_data

        await db.commit()

        return await self.get_care_team(db, provider_id, care_team.tenant_id, care_team_id)

    # ==================== Task Management ====================

    async def create_task(
        self,
        db: AsyncSession,
        provider_id: UUID,
        tenant_id: UUID,
        care_team_id: UUID,
        data: CareTeamTaskCreate
    ) -> CareTeamTaskResponse:
        """Create a task for the care team"""

        task = CareTeamTask(
            id=uuid4(),
            care_team_id=care_team_id,
            tenant_id=tenant_id,
            title=data.title,
            description=data.description,
            category=data.category,
            assigned_to=data.assigned_to,
            assigned_by=provider_id,
            assigned_role=data.assigned_role,
            priority=MessagePriority(data.priority.value) if data.priority else MessagePriority.NORMAL,
            due_date=data.due_date,
            reminder_at=data.reminder_at,
            status="pending"
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)

        return CareTeamTaskResponse(
            id=task.id,
            care_team_id=task.care_team_id,
            title=task.title,
            description=task.description,
            category=task.category,
            assigned_to=task.assigned_to,
            assigned_by=task.assigned_by,
            priority=task.priority.value,
            due_date=task.due_date,
            status=task.status,
            completed_at=task.completed_at,
            created_at=task.created_at
        )

    async def update_task(
        self,
        db: AsyncSession,
        provider_id: UUID,
        task_id: UUID,
        data: CareTeamTaskUpdate
    ) -> CareTeamTaskResponse:
        """Update a care team task"""

        result = await db.execute(
            select(CareTeamTask).where(CareTeamTask.id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            raise ValueError("Task not found")

        if data.title is not None:
            task.title = data.title
        if data.description is not None:
            task.description = data.description
        if data.assigned_to is not None:
            task.assigned_to = data.assigned_to
        if data.priority is not None:
            task.priority = MessagePriority(data.priority.value)
        if data.due_date is not None:
            task.due_date = data.due_date
        if data.status is not None:
            task.status = data.status
            if data.status == "completed":
                task.completed_at = datetime.now(timezone.utc)
                task.completed_by = provider_id
        if data.completion_notes is not None:
            task.completion_notes = data.completion_notes

        await db.commit()
        await db.refresh(task)

        return CareTeamTaskResponse(
            id=task.id,
            care_team_id=task.care_team_id,
            title=task.title,
            description=task.description,
            category=task.category,
            assigned_to=task.assigned_to,
            assigned_by=task.assigned_by,
            priority=task.priority.value,
            due_date=task.due_date,
            status=task.status,
            completed_at=task.completed_at,
            created_at=task.created_at
        )

    async def list_tasks(
        self,
        db: AsyncSession,
        provider_id: UUID,
        tenant_id: UUID,
        care_team_id: Optional[UUID] = None,
        assigned_to_me: bool = False,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[CareTeamTaskResponse]:
        """List care team tasks"""

        query = select(CareTeamTask).where(
            CareTeamTask.tenant_id == tenant_id
        )

        if care_team_id:
            query = query.where(CareTeamTask.care_team_id == care_team_id)

        if assigned_to_me:
            query = query.where(CareTeamTask.assigned_to == provider_id)

        if status:
            query = query.where(CareTeamTask.status == status)

        query = query.order_by(desc(CareTeamTask.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        tasks = result.scalars().all()

        return [
            CareTeamTaskResponse(
                id=t.id,
                care_team_id=t.care_team_id,
                title=t.title,
                description=t.description,
                category=t.category,
                assigned_to=t.assigned_to,
                assigned_by=t.assigned_by,
                priority=t.priority.value if t.priority else "normal",
                due_date=t.due_date,
                status=t.status,
                completed_at=t.completed_at,
                created_at=t.created_at
            )
            for t in tasks
        ]
