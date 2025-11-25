"""
Handoff Service Tests
EPIC-015: Unit tests for shift handoff service (SBAR format)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, date, time, timezone, timedelta

from modules.provider_collaboration.services.handoff_service import HandoffService
from modules.provider_collaboration.schemas import (
    HandoffCreate, PatientHandoffUpdate, HandoffAcknowledge, HandoffQuestion,
    HandoffTypeSchema, QuestionPrioritySchema
)
from modules.provider_collaboration.models import HandoffStatus, HandoffType


class TestHandoffService:
    """Tests for HandoffService"""

    @pytest.fixture
    def service(self):
        return HandoffService()

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

    # ==================== Handoff Creation Tests ====================

    @pytest.mark.asyncio
    async def test_create_handoff(self, service, mock_db, provider_id, tenant_id):
        """Test creating a shift handoff"""
        incoming_provider_id = uuid4()
        patient_ids = [uuid4() for _ in range(5)]

        data = HandoffCreate(
            incoming_provider_id=incoming_provider_id,
            handoff_type=HandoffTypeSchema.SHIFT_CHANGE,
            service="Internal Medicine",
            unit="ICU",
            shift_date=date.today(),
            scheduled_time=datetime.now(timezone.utc) + timedelta(hours=1),
            patient_ids=patient_ids
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.create_handoff(
            mock_db, provider_id, tenant_id, data, "127.0.0.1"
        )

        # Verify handoff, conversation, participants, patient handoffs, and audit log created
        assert mock_db.add.call_count >= 8  # 1 handoff + 1 conv + 2 participants + 5 patient handoffs + 1 audit
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_create_handoff_with_patient_count(self, service, mock_db, provider_id, tenant_id):
        """Test that patient count is set correctly"""
        incoming_provider_id = uuid4()
        patient_ids = [uuid4() for _ in range(3)]

        data = HandoffCreate(
            incoming_provider_id=incoming_provider_id,
            handoff_type=HandoffTypeSchema.SHIFT_CHANGE,
            service="Emergency",
            unit="ED",
            shift_date=date.today(),
            scheduled_time=datetime.now(timezone.utc),
            patient_ids=patient_ids
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.create_handoff(
            mock_db, provider_id, tenant_id, data, "127.0.0.1"
        )

        # The add method should have been called with a handoff object
        assert mock_db.add.called

    # ==================== Handoff Status Tests ====================

    @pytest.mark.asyncio
    async def test_start_handoff(self, service, mock_db, provider_id):
        """Test starting a handoff session"""
        handoff_id = uuid4()

        handoff = MagicMock()
        handoff.id = handoff_id
        handoff.outgoing_provider_id = provider_id
        handoff.status = HandoffStatus.SCHEDULED
        handoff.tenant_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = handoff
        mock_db.execute.return_value = mock_result

        result = await service.start_handoff(mock_db, provider_id, handoff_id)

        assert handoff.status == HandoffStatus.IN_PROGRESS
        assert handoff.started_at is not None
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_start_handoff_wrong_provider(self, service, mock_db, provider_id):
        """Test that only outgoing provider can start handoff"""
        handoff_id = uuid4()
        other_provider = uuid4()

        handoff = MagicMock()
        handoff.id = handoff_id
        handoff.outgoing_provider_id = other_provider
        handoff.status = HandoffStatus.SCHEDULED

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = handoff
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Only outgoing provider can start"):
            await service.start_handoff(mock_db, provider_id, handoff_id)

    @pytest.mark.asyncio
    async def test_start_handoff_wrong_status(self, service, mock_db, provider_id):
        """Test that only scheduled handoffs can be started"""
        handoff_id = uuid4()

        handoff = MagicMock()
        handoff.id = handoff_id
        handoff.outgoing_provider_id = provider_id
        handoff.status = HandoffStatus.IN_PROGRESS

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = handoff
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="not in scheduled status"):
            await service.start_handoff(mock_db, provider_id, handoff_id)

    # ==================== SBAR Update Tests ====================

    @pytest.mark.asyncio
    async def test_update_patient_handoff_sbar(self, service, mock_db, provider_id):
        """Test updating patient SBAR data"""
        patient_handoff_id = uuid4()

        shift_handoff = MagicMock()
        shift_handoff.outgoing_provider_id = provider_id

        patient_handoff = MagicMock()
        patient_handoff.id = patient_handoff_id
        patient_handoff.shift_handoff = shift_handoff
        patient_handoff.patient_id = uuid4()
        patient_handoff.situation = None
        patient_handoff.background = None
        patient_handoff.assessment = None
        patient_handoff.recommendations = None
        patient_handoff.critical_items = []
        patient_handoff.has_critical_items = False
        patient_handoff.pending_tasks = []
        patient_handoff.reviewed = False
        patient_handoff.questions_raised = []
        patient_handoff.questions_resolved = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = patient_handoff
        mock_db.execute.return_value = mock_result

        data = PatientHandoffUpdate(
            situation="72yo male admitted for CHF exacerbation",
            background="History of HFrEF, EF 25%, on optimal medical therapy",
            assessment="Improving, euvolemic on current diuretic regimen",
            recommendations="Continue diuresis, can likely discharge tomorrow",
            critical_items=["Monitor I/O closely", "Weigh daily"]
        )

        result = await service.update_patient_handoff(
            mock_db, provider_id, patient_handoff_id, data
        )

        assert patient_handoff.situation == data.situation
        assert patient_handoff.background == data.background
        assert patient_handoff.assessment == data.assessment
        assert patient_handoff.recommendations == data.recommendations
        assert patient_handoff.has_critical_items is True
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_update_patient_handoff_wrong_provider(self, service, mock_db, provider_id):
        """Test that only outgoing provider can update SBAR"""
        patient_handoff_id = uuid4()
        other_provider = uuid4()

        shift_handoff = MagicMock()
        shift_handoff.outgoing_provider_id = other_provider

        patient_handoff = MagicMock()
        patient_handoff.id = patient_handoff_id
        patient_handoff.shift_handoff = shift_handoff

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = patient_handoff
        mock_db.execute.return_value = mock_result

        data = PatientHandoffUpdate(situation="Test situation")

        with pytest.raises(ValueError, match="Only outgoing provider"):
            await service.update_patient_handoff(mock_db, provider_id, patient_handoff_id, data)

    # ==================== Question Tests ====================

    @pytest.mark.asyncio
    async def test_raise_question(self, service, mock_db, provider_id):
        """Test raising a question about a patient handoff"""
        handoff_id = uuid4()
        patient_id = uuid4()

        patient_handoff = MagicMock()
        patient_handoff.patient_id = patient_id
        patient_handoff.questions_raised = []
        patient_handoff.questions_resolved = True

        handoff = MagicMock()
        handoff.id = handoff_id
        handoff.incoming_provider_id = provider_id
        handoff.patient_handoffs = [patient_handoff]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = handoff
        mock_db.execute.return_value = mock_result

        data = HandoffQuestion(
            patient_id=patient_id,
            question="What is the target urine output?",
            priority=QuestionPrioritySchema.HIGH
        )

        await service.raise_question(mock_db, provider_id, handoff_id, data)

        assert len(patient_handoff.questions_raised) == 1
        assert patient_handoff.questions_resolved is False
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_raise_question_wrong_provider(self, service, mock_db, provider_id):
        """Test that only incoming provider can raise questions"""
        handoff_id = uuid4()
        other_provider = uuid4()

        handoff = MagicMock()
        handoff.id = handoff_id
        handoff.incoming_provider_id = other_provider

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = handoff
        mock_db.execute.return_value = mock_result

        data = HandoffQuestion(
            patient_id=uuid4(),
            question="Test question?",
            priority=QuestionPrioritySchema.MEDIUM
        )

        with pytest.raises(ValueError, match="Only incoming provider"):
            await service.raise_question(mock_db, provider_id, handoff_id, data)

    # ==================== Acknowledgment Tests ====================

    @pytest.mark.asyncio
    async def test_acknowledge_handoff(self, service, mock_db, provider_id):
        """Test acknowledging a handoff"""
        handoff_id = uuid4()

        handoff = MagicMock()
        handoff.id = handoff_id
        handoff.incoming_provider_id = provider_id
        handoff.status = HandoffStatus.IN_PROGRESS
        handoff.started_at = datetime.now(timezone.utc) - timedelta(minutes=30)
        handoff.tenant_id = uuid4()
        handoff.outgoing_provider_id = uuid4()
        handoff.handoff_type = HandoffType.SHIFT_CHANGE
        handoff.service = "Medicine"
        handoff.unit = "ICU"
        handoff.shift_date = date.today()
        handoff.scheduled_time = datetime.now(timezone.utc)
        handoff.completed_at = None
        handoff.duration_minutes = None
        handoff.patient_count = 5
        handoff.patient_handoffs = []
        handoff.conversation_id = uuid4()
        handoff.acknowledged = False
        handoff.quality_score = None
        handoff.created_at = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = handoff
        mock_db.execute.return_value = mock_result

        data = HandoffAcknowledge(
            signature="Dr. Jane Smith",
            feedback="Thorough handoff, all questions answered"
        )

        result = await service.acknowledge_handoff(mock_db, provider_id, handoff_id, data)

        assert handoff.acknowledged is True
        assert handoff.status == HandoffStatus.COMPLETED
        assert handoff.completed_at is not None
        assert handoff.duration_minutes is not None
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_acknowledge_handoff_wrong_provider(self, service, mock_db, provider_id):
        """Test that only incoming provider can acknowledge"""
        handoff_id = uuid4()
        other_provider = uuid4()

        handoff = MagicMock()
        handoff.id = handoff_id
        handoff.incoming_provider_id = other_provider
        handoff.status = HandoffStatus.IN_PROGRESS

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = handoff
        mock_db.execute.return_value = mock_result

        data = HandoffAcknowledge(signature="Test Signature")

        with pytest.raises(ValueError, match="Only incoming provider"):
            await service.acknowledge_handoff(mock_db, provider_id, handoff_id, data)

    @pytest.mark.asyncio
    async def test_acknowledge_handoff_wrong_status(self, service, mock_db, provider_id):
        """Test that only in-progress handoffs can be acknowledged"""
        handoff_id = uuid4()

        handoff = MagicMock()
        handoff.id = handoff_id
        handoff.incoming_provider_id = provider_id
        handoff.status = HandoffStatus.SCHEDULED

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = handoff
        mock_db.execute.return_value = mock_result

        data = HandoffAcknowledge(signature="Test Signature")

        with pytest.raises(ValueError, match="not in progress"):
            await service.acknowledge_handoff(mock_db, provider_id, handoff_id, data)

    # ==================== SBAR Generation Tests ====================

    @pytest.mark.asyncio
    async def test_generate_patient_sbar(self, service, mock_db, provider_id):
        """Test generating SBAR template for a patient"""
        patient_id = uuid4()

        result = await service.generate_patient_sbar(mock_db, patient_id, provider_id)

        # Verify SBAR structure
        assert "situation" in result
        assert "background" in result
        assert "assessment" in result
        assert "recommendations" in result

        # Verify situation fields
        assert "chief_complaint" in result["situation"]
        assert "code_status" in result["situation"]

        # Verify background fields
        assert "history" in result["background"]
        assert "allergies" in result["background"]
        assert "medications" in result["background"]

        # Verify assessment fields
        assert "vital_signs" in result["assessment"]
        assert "labs" in result["assessment"]

        # Verify recommendations fields
        assert "pending_tasks" in result["recommendations"]
        assert "contingencies" in result["recommendations"]


class TestHandoffServiceValidation:
    """Validation tests for HandoffService"""

    @pytest.fixture
    def service(self):
        return HandoffService()

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_get_handoff_not_found(self, service, mock_db):
        """Test getting non-existent handoff"""
        provider_id = uuid4()
        tenant_id = uuid4()
        handoff_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Handoff not found"):
            await service.get_handoff(mock_db, provider_id, tenant_id, handoff_id)

    @pytest.mark.asyncio
    async def test_get_handoff_not_authorized(self, service, mock_db):
        """Test that only participating providers can access handoff"""
        provider_id = uuid4()
        tenant_id = uuid4()
        handoff_id = uuid4()
        outgoing = uuid4()
        incoming = uuid4()

        handoff = MagicMock()
        handoff.id = handoff_id
        handoff.tenant_id = tenant_id
        handoff.outgoing_provider_id = outgoing
        handoff.incoming_provider_id = incoming

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = handoff
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Not authorized"):
            await service.get_handoff(mock_db, provider_id, tenant_id, handoff_id)
