"""
Care Team Service Tests
EPIC-015: Unit tests for care team coordination service
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from modules.provider_collaboration.services.care_team_service import CareTeamService
from modules.provider_collaboration.schemas import (
    CareTeamCreate, CareTeamUpdate, CareTeamMemberAdd, CareTeamMemberUpdate,
    CareTeamTaskCreate, CareTeamTaskUpdate, CareTeamGoalsUpdate,
    CareTeamStatusSchema, CareTeamRoleSchema, TaskStatusSchema, TaskPrioritySchema
)
from modules.provider_collaboration.models import (
    CareTeamStatus, CareTeamRole, TaskStatus, TaskPriority
)


class TestCareTeamService:
    """Tests for CareTeamService"""

    @pytest.fixture
    def service(self):
        return CareTeamService()

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def provider_id(self):
        return uuid4()

    @pytest.fixture
    def tenant_id(self):
        return uuid4()

    # ==================== Care Team Creation Tests ====================

    @pytest.mark.asyncio
    async def test_create_care_team(self, service, mock_db, provider_id, tenant_id):
        """Test creating a care team"""
        patient_id = uuid4()

        data = CareTeamCreate(
            name="Cardiac Care Team",
            patient_id=patient_id,
            description="Team for post-MI patient care",
            care_goals=["Optimize cardiac function", "Prevent readmission"]
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.create_care_team(
            mock_db, provider_id, tenant_id, data, "127.0.0.1"
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_create_care_team_adds_creator_as_lead(self, service, mock_db, provider_id, tenant_id):
        """Test that creator is added as team lead"""
        patient_id = uuid4()

        data = CareTeamCreate(
            name="Oncology Team",
            patient_id=patient_id
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.create_care_team(
            mock_db, provider_id, tenant_id, data, "127.0.0.1"
        )

        # Verify multiple adds (care team, member, conversation, participant, audit)
        assert mock_db.add.call_count >= 4

    # ==================== Care Team Update Tests ====================

    @pytest.mark.asyncio
    async def test_update_care_team(self, service, mock_db, provider_id, tenant_id):
        """Test updating care team details"""
        care_team_id = uuid4()

        care_team = MagicMock()
        care_team.id = care_team_id
        care_team.tenant_id = tenant_id
        care_team.status = CareTeamStatus.ACTIVE
        care_team.members = [MagicMock(provider_id=provider_id)]
        care_team.name = "Old Name"
        care_team.description = None
        care_team.care_goals = []
        care_team.patient_id = uuid4()
        care_team.conversation_id = uuid4()
        care_team.created_by = provider_id
        care_team.created_at = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = care_team
        mock_db.execute.return_value = mock_result

        data = CareTeamUpdate(
            name="Updated Care Team",
            description="New description"
        )

        result = await service.update_care_team(
            mock_db, provider_id, tenant_id, care_team_id, data
        )

        assert care_team.name == "Updated Care Team"
        assert care_team.description == "New description"
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_update_care_goals(self, service, mock_db, provider_id, tenant_id):
        """Test updating care team goals"""
        care_team_id = uuid4()

        care_team = MagicMock()
        care_team.id = care_team_id
        care_team.tenant_id = tenant_id
        care_team.members = [MagicMock(provider_id=provider_id)]
        care_team.care_goals = []
        care_team.status = CareTeamStatus.ACTIVE
        care_team.name = "Test Team"
        care_team.patient_id = uuid4()
        care_team.conversation_id = uuid4()
        care_team.created_by = provider_id
        care_team.created_at = datetime.now(timezone.utc)
        care_team.description = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = care_team
        mock_db.execute.return_value = mock_result

        data = CareTeamGoalsUpdate(
            care_goals=["Goal 1", "Goal 2", "Goal 3"]
        )

        result = await service.update_goals(
            mock_db, provider_id, tenant_id, care_team_id, data
        )

        assert care_team.care_goals == ["Goal 1", "Goal 2", "Goal 3"]
        assert mock_db.commit.called

    # ==================== Member Management Tests ====================

    @pytest.mark.asyncio
    async def test_add_member(self, service, mock_db, provider_id, tenant_id):
        """Test adding a member to care team"""
        care_team_id = uuid4()
        new_member_id = uuid4()

        care_team = MagicMock()
        care_team.id = care_team_id
        care_team.tenant_id = tenant_id
        care_team.members = [MagicMock(provider_id=provider_id)]
        care_team.conversation_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = care_team
        mock_db.execute.return_value = mock_result

        data = CareTeamMemberAdd(
            provider_id=new_member_id,
            role=CareTeamRoleSchema.SPECIALIST,
            specialty="Cardiology"
        )

        result = await service.add_member(
            mock_db, provider_id, tenant_id, care_team_id, data
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_add_existing_member(self, service, mock_db, provider_id, tenant_id):
        """Test that adding existing member fails"""
        care_team_id = uuid4()
        existing_member_id = uuid4()

        existing_member = MagicMock()
        existing_member.provider_id = existing_member_id

        care_team = MagicMock()
        care_team.id = care_team_id
        care_team.tenant_id = tenant_id
        care_team.members = [MagicMock(provider_id=provider_id), existing_member]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = care_team
        mock_db.execute.return_value = mock_result

        data = CareTeamMemberAdd(
            provider_id=existing_member_id,
            role=CareTeamRoleSchema.SPECIALIST
        )

        with pytest.raises(ValueError, match="already a member"):
            await service.add_member(mock_db, provider_id, tenant_id, care_team_id, data)

    @pytest.mark.asyncio
    async def test_remove_member(self, service, mock_db, provider_id, tenant_id):
        """Test removing a member from care team"""
        member_id = uuid4()
        care_team_id = uuid4()

        member = MagicMock()
        member.id = member_id
        member.care_team_id = care_team_id
        member.care_team = MagicMock()
        member.care_team.members = [
            MagicMock(provider_id=provider_id),
            member
        ]
        member.care_team.conversation_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = member
        mock_db.execute.return_value = mock_result

        await service.remove_member(mock_db, provider_id, tenant_id, member_id)

        assert mock_db.delete.called
        assert mock_db.commit.called

    # ==================== Task Management Tests ====================

    @pytest.mark.asyncio
    async def test_create_task(self, service, mock_db, provider_id, tenant_id):
        """Test creating a care team task"""
        care_team_id = uuid4()
        assignee_id = uuid4()

        care_team = MagicMock()
        care_team.id = care_team_id
        care_team.tenant_id = tenant_id
        care_team.members = [
            MagicMock(provider_id=provider_id),
            MagicMock(provider_id=assignee_id)
        ]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = care_team
        mock_db.execute.return_value = mock_result

        data = CareTeamTaskCreate(
            title="Schedule follow-up",
            description="Schedule 2-week follow-up appointment",
            assignee_id=assignee_id,
            priority=TaskPrioritySchema.HIGH,
            due_date=datetime.now(timezone.utc) + timedelta(days=7)
        )

        result = await service.create_task(
            mock_db, provider_id, tenant_id, care_team_id, data
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_create_task_non_member_assignee(self, service, mock_db, provider_id, tenant_id):
        """Test that tasks cannot be assigned to non-members"""
        care_team_id = uuid4()
        non_member_id = uuid4()

        care_team = MagicMock()
        care_team.id = care_team_id
        care_team.tenant_id = tenant_id
        care_team.members = [MagicMock(provider_id=provider_id)]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = care_team
        mock_db.execute.return_value = mock_result

        data = CareTeamTaskCreate(
            title="Test task",
            assignee_id=non_member_id,
            priority=TaskPrioritySchema.MEDIUM
        )

        with pytest.raises(ValueError, match="Assignee is not a team member"):
            await service.create_task(mock_db, provider_id, tenant_id, care_team_id, data)

    @pytest.mark.asyncio
    async def test_update_task(self, service, mock_db, provider_id):
        """Test updating a task"""
        task_id = uuid4()

        task = MagicMock()
        task.id = task_id
        task.care_team = MagicMock()
        task.care_team.members = [MagicMock(provider_id=provider_id)]
        task.status = TaskStatus.PENDING
        task.title = "Original title"
        task.description = None
        task.priority = TaskPriority.MEDIUM
        task.due_date = None
        task.assignee_id = provider_id
        task.care_team_id = uuid4()
        task.created_by = provider_id
        task.created_at = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = task
        mock_db.execute.return_value = mock_result

        data = CareTeamTaskUpdate(
            status=TaskStatusSchema.IN_PROGRESS,
            notes="Started working on this"
        )

        result = await service.update_task(mock_db, provider_id, task_id, data)

        assert task.status == TaskStatus.IN_PROGRESS
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_complete_task(self, service, mock_db, provider_id):
        """Test completing a task"""
        task_id = uuid4()

        task = MagicMock()
        task.id = task_id
        task.care_team = MagicMock()
        task.care_team.members = [MagicMock(provider_id=provider_id)]
        task.status = TaskStatus.IN_PROGRESS
        task.title = "Test task"
        task.description = None
        task.priority = TaskPriority.HIGH
        task.due_date = None
        task.assignee_id = provider_id
        task.care_team_id = uuid4()
        task.created_by = provider_id
        task.created_at = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = task
        mock_db.execute.return_value = mock_result

        result = await service.complete_task(mock_db, provider_id, task_id, "Task completed successfully")

        assert task.status == TaskStatus.COMPLETED
        assert task.completed_at is not None
        assert task.completed_by == provider_id
        assert mock_db.commit.called


class TestCareTeamServiceValidation:
    """Validation tests for CareTeamService"""

    @pytest.fixture
    def service(self):
        return CareTeamService()

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_get_care_team_not_found(self, service, mock_db):
        """Test getting non-existent care team"""
        provider_id = uuid4()
        tenant_id = uuid4()
        care_team_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Care team not found"):
            await service.get_care_team(mock_db, provider_id, tenant_id, care_team_id)

    @pytest.mark.asyncio
    async def test_get_care_team_not_member(self, service, mock_db):
        """Test that non-members cannot access care team"""
        provider_id = uuid4()
        tenant_id = uuid4()
        care_team_id = uuid4()
        other_provider = uuid4()

        care_team = MagicMock()
        care_team.id = care_team_id
        care_team.tenant_id = tenant_id
        care_team.members = [MagicMock(provider_id=other_provider)]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = care_team
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Not a member"):
            await service.get_care_team(mock_db, provider_id, tenant_id, care_team_id)
