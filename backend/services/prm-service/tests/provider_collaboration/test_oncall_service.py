"""
On-Call Service Tests
EPIC-015: Unit tests for on-call schedule and request service
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, date, time, timezone, timedelta

from modules.provider_collaboration.services.on_call_service import OnCallService
from modules.provider_collaboration.schemas import (
    OnCallScheduleCreate, OnCallScheduleUpdate, OnCallRequestCreate,
    OnCallStatusSchema, RequestUrgencySchema
)
from modules.provider_collaboration.models import (
    OnCallStatus, OnCallRequestStatus, RequestUrgency
)


class TestOnCallService:
    """Tests for OnCallService"""

    @pytest.fixture
    def service(self):
        return OnCallService()

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

    # ==================== Schedule Creation Tests ====================

    @pytest.mark.asyncio
    async def test_create_schedule(self, service, mock_db, provider_id, tenant_id):
        """Test creating an on-call schedule"""
        scheduled_provider_id = uuid4()

        data = OnCallScheduleCreate(
            provider_id=scheduled_provider_id,
            specialty="Cardiology",
            service="Internal Medicine",
            start_time=datetime.now(timezone.utc) + timedelta(hours=8),
            end_time=datetime.now(timezone.utc) + timedelta(hours=20),
            is_primary=True
        )

        # Mock no overlapping schedule
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.create_schedule(
            mock_db, provider_id, tenant_id, data, "127.0.0.1"
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_create_schedule_with_backup(self, service, mock_db, provider_id, tenant_id):
        """Test creating schedule with backup provider"""
        scheduled_provider_id = uuid4()
        backup_provider_id = uuid4()

        data = OnCallScheduleCreate(
            provider_id=scheduled_provider_id,
            specialty="Neurology",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(hours=12),
            is_primary=True,
            backup_provider_id=backup_provider_id
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.create_schedule(
            mock_db, provider_id, tenant_id, data, "127.0.0.1"
        )

        assert mock_db.add.called

    @pytest.mark.asyncio
    async def test_create_schedule_overlapping(self, service, mock_db, provider_id, tenant_id):
        """Test that overlapping schedules are rejected"""
        scheduled_provider_id = uuid4()

        existing_schedule = MagicMock()
        existing_schedule.id = uuid4()

        data = OnCallScheduleCreate(
            provider_id=scheduled_provider_id,
            specialty="Cardiology",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(hours=12),
            is_primary=True
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_schedule
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Overlapping schedule"):
            await service.create_schedule(mock_db, provider_id, tenant_id, data, "127.0.0.1")

    # ==================== Schedule Update Tests ====================

    @pytest.mark.asyncio
    async def test_update_schedule(self, service, mock_db, provider_id, tenant_id):
        """Test updating an on-call schedule"""
        schedule_id = uuid4()

        schedule = MagicMock()
        schedule.id = schedule_id
        schedule.tenant_id = tenant_id
        schedule.status = OnCallStatus.SCHEDULED
        schedule.start_time = datetime.now(timezone.utc)
        schedule.end_time = datetime.now(timezone.utc) + timedelta(hours=12)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = schedule
        mock_db.execute.return_value = mock_result

        data = OnCallScheduleUpdate(
            notes="Updated contact preferences",
            contact_preferences={"phone": "555-1234"}
        )

        result = await service.update_schedule(
            mock_db, provider_id, tenant_id, schedule_id, data
        )

        assert schedule.notes == "Updated contact preferences"
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_update_cancelled_schedule(self, service, mock_db, provider_id, tenant_id):
        """Test that cancelled schedules cannot be updated"""
        schedule_id = uuid4()

        schedule = MagicMock()
        schedule.id = schedule_id
        schedule.tenant_id = tenant_id
        schedule.status = OnCallStatus.CANCELLED

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = schedule
        mock_db.execute.return_value = mock_result

        data = OnCallScheduleUpdate(notes="Test update")

        with pytest.raises(ValueError, match="Cannot update cancelled"):
            await service.update_schedule(mock_db, provider_id, tenant_id, schedule_id, data)

    # ==================== Schedule Status Tests ====================

    @pytest.mark.asyncio
    async def test_activate_schedule(self, service, mock_db, provider_id):
        """Test activating an on-call schedule"""
        schedule_id = uuid4()

        schedule = MagicMock()
        schedule.id = schedule_id
        schedule.provider_id = provider_id
        schedule.status = OnCallStatus.SCHEDULED

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = schedule
        mock_db.execute.return_value = mock_result

        result = await service.activate_schedule(mock_db, provider_id, schedule_id)

        assert schedule.status == OnCallStatus.ACTIVE
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_activate_schedule_wrong_provider(self, service, mock_db, provider_id):
        """Test that only scheduled provider can activate"""
        schedule_id = uuid4()
        other_provider = uuid4()

        schedule = MagicMock()
        schedule.id = schedule_id
        schedule.provider_id = other_provider
        schedule.status = OnCallStatus.SCHEDULED

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = schedule
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Only scheduled provider"):
            await service.activate_schedule(mock_db, provider_id, schedule_id)

    @pytest.mark.asyncio
    async def test_complete_schedule(self, service, mock_db, provider_id):
        """Test completing an on-call schedule"""
        schedule_id = uuid4()

        schedule = MagicMock()
        schedule.id = schedule_id
        schedule.provider_id = provider_id
        schedule.status = OnCallStatus.ACTIVE

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = schedule
        mock_db.execute.return_value = mock_result

        result = await service.complete_schedule(mock_db, provider_id, schedule_id)

        assert schedule.status == OnCallStatus.COMPLETED
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_cancel_schedule(self, service, mock_db, provider_id, tenant_id):
        """Test cancelling an on-call schedule"""
        schedule_id = uuid4()

        schedule = MagicMock()
        schedule.id = schedule_id
        schedule.tenant_id = tenant_id
        schedule.status = OnCallStatus.SCHEDULED
        schedule.notes = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = schedule
        mock_db.execute.return_value = mock_result

        result = await service.cancel_schedule(
            mock_db, provider_id, tenant_id, schedule_id, "Provider unavailable"
        )

        assert schedule.status == OnCallStatus.CANCELLED
        assert mock_db.commit.called

    # ==================== On-Call Request Tests ====================

    @pytest.mark.asyncio
    async def test_create_request(self, service, mock_db, provider_id, tenant_id):
        """Test creating an on-call request"""
        patient_id = uuid4()
        schedule_id = uuid4()

        schedule_response = MagicMock()
        schedule_response.id = schedule_id

        data = OnCallRequestCreate(
            specialty="Cardiology",
            urgency=RequestUrgencySchema.URGENT,
            reason="Chest pain in ED patient",
            clinical_summary="56yo male with substernal chest pain, elevated troponin",
            patient_id=patient_id,
            callback_number="555-1234"
        )

        # Mock get_current_oncall
        with patch.object(service, 'get_current_oncall', return_value=schedule_response):
            result = await service.create_request(
                mock_db, provider_id, tenant_id, data, "127.0.0.1"
            )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_create_request_no_oncall(self, service, mock_db, provider_id, tenant_id):
        """Test request fails when no on-call provider available"""
        data = OnCallRequestCreate(
            specialty="Dermatology",
            urgency=RequestUrgencySchema.ROUTINE,
            reason="Rash consultation"
        )

        # Mock no current on-call
        with patch.object(service, 'get_current_oncall', return_value=None):
            with pytest.raises(ValueError, match="No on-call provider found"):
                await service.create_request(mock_db, provider_id, tenant_id, data, "127.0.0.1")

    @pytest.mark.asyncio
    async def test_acknowledge_request(self, service, mock_db, provider_id):
        """Test acknowledging an on-call request"""
        request_id = uuid4()

        schedule = MagicMock()
        schedule.provider_id = provider_id

        request = MagicMock()
        request.id = request_id
        request.schedule = schedule
        request.status = OnCallRequestStatus.PENDING
        request.created_at = datetime.now(timezone.utc) - timedelta(minutes=5)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = request
        mock_db.execute.return_value = mock_result

        result = await service.acknowledge_request(mock_db, provider_id, request_id)

        assert request.status == OnCallRequestStatus.ACKNOWLEDGED
        assert request.acknowledged_at is not None
        assert request.response_time_minutes is not None
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_respond_to_request_accept(self, service, mock_db, provider_id):
        """Test accepting an on-call request"""
        request_id = uuid4()

        schedule = MagicMock()
        schedule.provider_id = provider_id

        request = MagicMock()
        request.id = request_id
        request.schedule = schedule
        request.status = OnCallRequestStatus.ACKNOWLEDGED
        request.acknowledged_at = datetime.now(timezone.utc)
        request.created_at = datetime.now(timezone.utc) - timedelta(minutes=10)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = request
        mock_db.execute.return_value = mock_result

        result = await service.respond_to_request(
            mock_db, provider_id, request_id, "On my way", accept=True
        )

        assert request.status == OnCallRequestStatus.IN_PROGRESS
        assert request.responded_at is not None
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_respond_to_request_decline(self, service, mock_db, provider_id):
        """Test declining an on-call request"""
        request_id = uuid4()

        schedule = MagicMock()
        schedule.provider_id = provider_id

        request = MagicMock()
        request.id = request_id
        request.schedule = schedule
        request.status = OnCallRequestStatus.PENDING
        request.escalation_level = 1
        request.urgency = RequestUrgency.URGENT
        request.created_at = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = request
        mock_db.execute.return_value = mock_result

        result = await service.respond_to_request(
            mock_db, provider_id, request_id, "In surgery, please escalate", accept=False
        )

        assert request.status == OnCallRequestStatus.ESCALATED
        assert request.escalation_level == 2
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_complete_request(self, service, mock_db, provider_id):
        """Test completing an on-call request"""
        request_id = uuid4()

        schedule = MagicMock()
        schedule.provider_id = provider_id

        request = MagicMock()
        request.id = request_id
        request.schedule = schedule
        request.status = OnCallRequestStatus.IN_PROGRESS

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = request
        mock_db.execute.return_value = mock_result

        result = await service.complete_request(
            mock_db, provider_id, request_id, "Patient stabilized, admitted to telemetry"
        )

        assert request.status == OnCallRequestStatus.COMPLETED
        assert request.completed_at is not None
        assert request.resolution == "Patient stabilized, admitted to telemetry"
        assert mock_db.commit.called


class TestOnCallServiceEscalation:
    """Escalation-specific tests for OnCallService"""

    @pytest.fixture
    def service(self):
        return OnCallService()

    def test_escalation_timeouts_configured(self, service):
        """Test escalation timeouts are correctly configured"""
        assert service.escalation_timeouts[RequestUrgency.ROUTINE] == 60
        assert service.escalation_timeouts[RequestUrgency.URGENT] == 15
        assert service.escalation_timeouts[RequestUrgency.EMERGENT] == 5
        assert service.escalation_timeouts[RequestUrgency.STAT] == 2

    @pytest.mark.asyncio
    async def test_escalate_request_with_backup(self, service):
        """Test escalating to backup provider"""
        mock_db = AsyncMock()
        request_id = uuid4()
        backup_provider = uuid4()
        backup_schedule_id = uuid4()

        schedule = MagicMock()
        schedule.backup_provider_id = backup_provider
        schedule.specialty = "Cardiology"

        request = MagicMock()
        request.id = request_id
        request.schedule = schedule
        request.status = OnCallRequestStatus.PENDING
        request.urgency = RequestUrgency.URGENT
        request.escalation_level = 1

        # Mock finding backup schedule
        backup_schedule = MagicMock()
        backup_schedule.id = backup_schedule_id

        mock_results = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=request)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=backup_schedule))
        ]
        mock_db.execute = AsyncMock(side_effect=mock_results)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        result = await service.escalate_request(mock_db, request_id)

        assert request.schedule_id == backup_schedule_id
        assert request.escalation_level == 2

    @pytest.mark.asyncio
    async def test_escalate_request_no_backup(self, service):
        """Test escalation when no backup available"""
        mock_db = AsyncMock()
        request_id = uuid4()

        schedule = MagicMock()
        schedule.backup_provider_id = None
        schedule.specialty = "Cardiology"

        request = MagicMock()
        request.id = request_id
        request.schedule = schedule
        request.status = OnCallRequestStatus.PENDING
        request.urgency = RequestUrgency.URGENT
        request.escalation_level = 1

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = request
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        result = await service.escalate_request(mock_db, request_id)

        assert request.status == OnCallRequestStatus.ESCALATED
        assert request.escalation_level == 2
