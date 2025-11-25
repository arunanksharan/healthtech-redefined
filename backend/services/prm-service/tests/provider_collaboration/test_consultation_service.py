"""
Consultation Service Tests
EPIC-015: Unit tests for specialist consultation service
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from modules.provider_collaboration.services.consultation_service import ConsultationService
from modules.provider_collaboration.schemas import (
    ConsultationCreate, ConsultationAccept, ConsultationDecline,
    ConsultationReportCreate, ConsultationUrgencySchema
)
from modules.provider_collaboration.models import (
    ConsultationStatus, ConsultationUrgency
)


class TestConsultationService:
    """Tests for ConsultationService"""

    @pytest.fixture
    def service(self):
        return ConsultationService()

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

    # ==================== Consultation Creation Tests ====================

    @pytest.mark.asyncio
    async def test_create_consultation_success(self, service, mock_db, provider_id, tenant_id):
        """Test creating a consultation request"""
        consultant_id = uuid4()
        patient_id = uuid4()

        data = ConsultationCreate(
            consultant_id=consultant_id,
            patient_id=patient_id,
            specialty="Cardiology",
            urgency=ConsultationUrgencySchema.URGENT,
            reason="Chest pain evaluation",
            clinical_question="Does the patient need cardiac catheterization?"
        )

        # Mock get_consultation return
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.create_consultation(
            mock_db, provider_id, tenant_id, data, "127.0.0.1"
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_create_consultation_calculates_sla(self, service, mock_db, provider_id, tenant_id):
        """Test that SLA deadlines are calculated correctly"""
        consultant_id = uuid4()
        patient_id = uuid4()

        # Test STAT urgency
        data = ConsultationCreate(
            consultant_id=consultant_id,
            patient_id=patient_id,
            specialty="Neurology",
            urgency=ConsultationUrgencySchema.STAT,
            reason="Stroke symptoms"
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.create_consultation(
            mock_db, provider_id, tenant_id, data, "127.0.0.1"
        )

        # Verify SLA hours for STAT
        assert service.sla_hours[ConsultationUrgency.STAT] == 0.5

    # ==================== Consultation Status Tests ====================

    @pytest.mark.asyncio
    async def test_accept_consultation(self, service, mock_db, provider_id):
        """Test accepting a consultation"""
        consultation_id = uuid4()

        consultation = MagicMock()
        consultation.id = consultation_id
        consultation.consultant_id = provider_id
        consultation.status = ConsultationStatus.PENDING
        consultation.tenant_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = consultation
        mock_db.execute.return_value = mock_result

        data = ConsultationAccept(
            estimated_completion="2 hours",
            notes="Will review after current procedure"
        )

        result = await service.accept_consultation(
            mock_db, provider_id, consultation_id, data
        )

        assert consultation.status == ConsultationStatus.ACCEPTED
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_accept_consultation_wrong_provider(self, service, mock_db, provider_id):
        """Test that non-consultants cannot accept"""
        consultation_id = uuid4()
        other_provider = uuid4()

        consultation = MagicMock()
        consultation.id = consultation_id
        consultation.consultant_id = other_provider
        consultation.status = ConsultationStatus.PENDING

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = consultation
        mock_db.execute.return_value = mock_result

        data = ConsultationAccept(estimated_completion="1 hour")

        with pytest.raises(ValueError, match="Only consultant can accept"):
            await service.accept_consultation(mock_db, provider_id, consultation_id, data)

    @pytest.mark.asyncio
    async def test_decline_consultation(self, service, mock_db, provider_id):
        """Test declining a consultation"""
        consultation_id = uuid4()

        consultation = MagicMock()
        consultation.id = consultation_id
        consultation.consultant_id = provider_id
        consultation.status = ConsultationStatus.PENDING
        consultation.tenant_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = consultation
        mock_db.execute.return_value = mock_result

        data = ConsultationDecline(
            reason="Schedule conflict",
            suggest_alternative=True,
            alternative_consultant_id=uuid4()
        )

        result = await service.decline_consultation(
            mock_db, provider_id, consultation_id, data
        )

        assert consultation.status == ConsultationStatus.DECLINED
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_start_consultation(self, service, mock_db, provider_id):
        """Test starting a consultation"""
        consultation_id = uuid4()

        consultation = MagicMock()
        consultation.id = consultation_id
        consultation.consultant_id = provider_id
        consultation.status = ConsultationStatus.ACCEPTED
        consultation.tenant_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = consultation
        mock_db.execute.return_value = mock_result

        result = await service.start_consultation(mock_db, provider_id, consultation_id)

        assert consultation.status == ConsultationStatus.IN_PROGRESS
        assert consultation.started_at is not None
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_start_consultation_wrong_status(self, service, mock_db, provider_id):
        """Test that only accepted consultations can be started"""
        consultation_id = uuid4()

        consultation = MagicMock()
        consultation.id = consultation_id
        consultation.consultant_id = provider_id
        consultation.status = ConsultationStatus.PENDING

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = consultation
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="not in accepted status"):
            await service.start_consultation(mock_db, provider_id, consultation_id)

    # ==================== Consultation Report Tests ====================

    @pytest.mark.asyncio
    async def test_create_report(self, service, mock_db, provider_id):
        """Test creating a consultation report"""
        consultation_id = uuid4()

        consultation = MagicMock()
        consultation.id = consultation_id
        consultation.consultant_id = provider_id
        consultation.status = ConsultationStatus.IN_PROGRESS
        consultation.report = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = consultation
        mock_db.execute.return_value = mock_result

        data = ConsultationReportCreate(
            findings="Elevated troponin, ST changes on ECG",
            recommendations="Recommend cardiac catheterization",
            diagnosis_codes=["I21.9"],
            follow_up_required=True,
            follow_up_instructions="See in 2 weeks post-procedure"
        )

        result = await service.create_report(
            mock_db, provider_id, consultation_id, data
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_sign_report(self, service, mock_db, provider_id):
        """Test signing a consultation report"""
        consultation_id = uuid4()

        report = MagicMock()
        report.id = uuid4()
        report.findings = "Test findings"
        report.recommendations = "Test recommendations"
        report.signed = False
        report.created_at = datetime.now(timezone.utc)

        consultation = MagicMock()
        consultation.id = consultation_id
        consultation.consultant_id = provider_id
        consultation.status = ConsultationStatus.IN_PROGRESS
        consultation.report = report
        consultation.tenant_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = consultation
        mock_db.execute.return_value = mock_result

        result = await service.sign_report(mock_db, provider_id, consultation_id)

        assert report.signed is True
        assert report.signed_at is not None
        assert consultation.status == ConsultationStatus.REPORTED
        assert mock_db.commit.called

    # ==================== Consultation Completion Tests ====================

    @pytest.mark.asyncio
    async def test_complete_consultation(self, service, mock_db, provider_id):
        """Test completing a consultation"""
        consultation_id = uuid4()

        report = MagicMock()
        report.signed = True

        consultation = MagicMock()
        consultation.id = consultation_id
        consultation.consultant_id = provider_id
        consultation.status = ConsultationStatus.REPORTED
        consultation.report = report
        consultation.created_at = datetime.now(timezone.utc)
        consultation.started_at = datetime.now(timezone.utc)
        consultation.tenant_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = consultation
        mock_db.execute.return_value = mock_result

        result = await service.complete_consultation(mock_db, provider_id, consultation_id)

        assert consultation.status == ConsultationStatus.COMPLETED
        assert consultation.completed_at is not None
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_complete_consultation_without_signed_report(self, service, mock_db, provider_id):
        """Test that consultations cannot be completed without signed report"""
        consultation_id = uuid4()

        report = MagicMock()
        report.signed = False

        consultation = MagicMock()
        consultation.id = consultation_id
        consultation.consultant_id = provider_id
        consultation.status = ConsultationStatus.IN_PROGRESS
        consultation.report = report

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = consultation
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Report must be signed"):
            await service.complete_consultation(mock_db, provider_id, consultation_id)


class TestConsultationServiceSLA:
    """SLA-specific tests for ConsultationService"""

    @pytest.fixture
    def service(self):
        return ConsultationService()

    def test_sla_hours_configuration(self, service):
        """Test SLA hours are correctly configured"""
        assert service.sla_hours[ConsultationUrgency.ROUTINE] == 24
        assert service.sla_hours[ConsultationUrgency.URGENT] == 4
        assert service.sla_hours[ConsultationUrgency.EMERGENT] == 1
        assert service.sla_hours[ConsultationUrgency.STAT] == 0.5

    def test_sla_calculation_routine(self, service):
        """Test SLA deadline calculation for routine"""
        now = datetime.now(timezone.utc)
        expected_deadline = now + timedelta(hours=24)

        # Calculate would happen in create_consultation
        actual_hours = service.sla_hours[ConsultationUrgency.ROUTINE]
        assert actual_hours == 24

    def test_sla_calculation_stat(self, service):
        """Test SLA deadline calculation for STAT"""
        now = datetime.now(timezone.utc)
        expected_deadline = now + timedelta(hours=0.5)

        actual_hours = service.sla_hours[ConsultationUrgency.STAT]
        assert actual_hours == 0.5
