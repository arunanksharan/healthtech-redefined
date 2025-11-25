"""
Test Telehealth Service Layer
Unit tests for EPIC-007 telehealth service classes
"""
import pytest
from uuid import uuid4, UUID
from datetime import datetime, date, time, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.orm import Session

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../..")))

from services.prm_service.modules.telehealth.service import (
    TelehealthSessionService,
    TelehealthAppointmentService,
    WaitingRoomServiceDB,
    TelehealthPaymentService,
    TelehealthAnalyticsService
)
from services.prm_service.modules.telehealth.models import (
    SessionStatus, ParticipantRole, ParticipantStatus,
    AppointmentType, AppointmentStatus, WaitingStatus,
    DeviceCheckStatus, RecordingStatus, PaymentStatus
)


@pytest.fixture
def mock_db():
    """Create a mock database session"""
    return MagicMock(spec=Session)


@pytest.fixture
def tenant_id():
    """Test tenant ID"""
    return uuid4()


@pytest.fixture
def patient_id():
    """Test patient ID"""
    return uuid4()


@pytest.fixture
def provider_id():
    """Test provider ID"""
    return uuid4()


@pytest.fixture
def user_id():
    """Test user ID"""
    return uuid4()


# ============================================================================
# SESSION SERVICE TESTS
# ============================================================================

class TestTelehealthSessionService:
    """Tests for TelehealthSessionService"""

    @pytest.mark.asyncio
    async def test_create_session(self, mock_db, tenant_id):
        """Test creating a new telehealth session"""
        service = TelehealthSessionService(mock_db, tenant_id)

        # Mock the db operations
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        session = await service.create_session(
            session_type="video_visit",
            scheduled_duration_minutes=30,
            waiting_room_enabled=True
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_add_participant(self, mock_db, tenant_id, user_id):
        """Test adding a participant to a session"""
        service = TelehealthSessionService(mock_db, tenant_id)

        session_id = uuid4()
        mock_session = MagicMock()
        mock_session.id = session_id
        mock_session.max_participants = 10
        mock_session.participants = []

        mock_db.query.return_value.filter.return_value.first.return_value = mock_session
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        participant = await service.add_participant(
            session_id=session_id,
            user_id=user_id,
            role=ParticipantRole.PATIENT,
            display_name="Test Patient"
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_generate_join_token(self, mock_db, tenant_id):
        """Test generating a join token for a participant"""
        service = TelehealthSessionService(mock_db, tenant_id)

        session_id = uuid4()
        participant_id = uuid4()

        mock_session = MagicMock()
        mock_session.id = session_id
        mock_session.room_name = "test-room-123"
        mock_session.room_token = "encryption_key"

        mock_participant = MagicMock()
        mock_participant.id = participant_id
        mock_participant.user_id = uuid4()
        mock_participant.role = ParticipantRole.PROVIDER
        mock_participant.display_name = "Dr. Test"
        mock_participant.can_share_screen = True
        mock_participant.can_record = False

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_session, mock_participant
        ]

        result = await service.generate_join_token(session_id, participant_id)

        assert "token" in result
        assert "room_name" in result
        assert result["room_name"] == "test-room-123"

    @pytest.mark.asyncio
    async def test_start_session(self, mock_db, tenant_id):
        """Test starting a session"""
        service = TelehealthSessionService(mock_db, tenant_id)

        session_id = uuid4()
        mock_session = MagicMock()
        mock_session.id = session_id
        mock_session.status = SessionStatus.SCHEDULED
        mock_session.started_at = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_session
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        session = await service.start_session(session_id)

        assert mock_session.status == SessionStatus.IN_PROGRESS
        assert mock_session.started_at is not None

    @pytest.mark.asyncio
    async def test_end_session(self, mock_db, tenant_id):
        """Test ending a session"""
        service = TelehealthSessionService(mock_db, tenant_id)

        session_id = uuid4()
        mock_session = MagicMock()
        mock_session.id = session_id
        mock_session.status = SessionStatus.IN_PROGRESS
        mock_session.started_at = datetime.utcnow() - timedelta(minutes=30)
        mock_session.ended_at = None
        mock_session.actual_duration_seconds = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_session
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        session = await service.end_session(session_id, reason="completed")

        assert mock_session.status == SessionStatus.COMPLETED
        assert mock_session.ended_at is not None


# ============================================================================
# APPOINTMENT SERVICE TESTS
# ============================================================================

class TestTelehealthAppointmentService:
    """Tests for TelehealthAppointmentService"""

    @pytest.mark.asyncio
    async def test_book_appointment(self, mock_db, tenant_id, patient_id, provider_id):
        """Test booking a telehealth appointment"""
        service = TelehealthAppointmentService(mock_db, tenant_id)

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        scheduled_start = datetime.now() + timedelta(days=1)
        appointment = await service.book_appointment(
            patient_id=patient_id,
            provider_id=provider_id,
            appointment_type=AppointmentType.VIDEO_VISIT,
            scheduled_start=scheduled_start,
            duration_minutes=30,
            patient_timezone="America/New_York"
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_confirm_appointment(self, mock_db, tenant_id):
        """Test confirming an appointment"""
        service = TelehealthAppointmentService(mock_db, tenant_id)

        appointment_id = uuid4()
        mock_appointment = MagicMock()
        mock_appointment.id = appointment_id
        mock_appointment.status = AppointmentStatus.SCHEDULED
        mock_appointment.confirmed_at = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_appointment
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        appointment = await service.confirm_appointment(appointment_id)

        assert mock_appointment.status == AppointmentStatus.CONFIRMED
        assert mock_appointment.confirmed_at is not None

    @pytest.mark.asyncio
    async def test_cancel_appointment(self, mock_db, tenant_id):
        """Test cancelling an appointment"""
        service = TelehealthAppointmentService(mock_db, tenant_id)

        appointment_id = uuid4()
        cancelled_by = uuid4()
        mock_appointment = MagicMock()
        mock_appointment.id = appointment_id
        mock_appointment.status = AppointmentStatus.SCHEDULED

        mock_db.query.return_value.filter.return_value.first.return_value = mock_appointment
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        appointment = await service.cancel_appointment(
            appointment_id=appointment_id,
            reason="Patient requested",
            cancelled_by=cancelled_by
        )

        assert mock_appointment.status == AppointmentStatus.CANCELLED
        assert mock_appointment.cancellation_reason == "Patient requested"
        assert mock_appointment.cancelled_by == cancelled_by

    @pytest.mark.asyncio
    async def test_reschedule_appointment(self, mock_db, tenant_id):
        """Test rescheduling an appointment"""
        service = TelehealthAppointmentService(mock_db, tenant_id)

        appointment_id = uuid4()
        mock_appointment = MagicMock()
        mock_appointment.id = appointment_id
        mock_appointment.status = AppointmentStatus.SCHEDULED
        mock_appointment.patient_id = uuid4()
        mock_appointment.provider_id = uuid4()
        mock_appointment.appointment_type = AppointmentType.VIDEO_VISIT
        mock_appointment.duration_minutes = 30
        mock_appointment.patient_timezone = "America/New_York"
        mock_appointment.reason_for_visit = "Follow-up"
        mock_appointment.copay_amount = 25.0

        mock_db.query.return_value.filter.return_value.first.return_value = mock_appointment
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        new_start = datetime.now() + timedelta(days=3)
        new_appointment = await service.reschedule_appointment(
            appointment_id=appointment_id,
            new_start_time=new_start
        )

        assert mock_appointment.status == AppointmentStatus.RESCHEDULED
        assert mock_db.add.called

    @pytest.mark.asyncio
    async def test_get_available_slots(self, mock_db, tenant_id, provider_id):
        """Test getting available appointment slots"""
        service = TelehealthAppointmentService(mock_db, tenant_id)

        mock_schedule = MagicMock()
        mock_schedule.weekly_hours = {
            "0": [["09:00", "12:00"], ["13:00", "17:00"]],
            "1": [["09:00", "12:00"], ["13:00", "17:00"]],
            "2": [["09:00", "12:00"], ["13:00", "17:00"]]
        }
        mock_schedule.timezone = "America/New_York"
        mock_schedule.default_duration_minutes = 30
        mock_schedule.buffer_minutes = 5
        mock_schedule.appointment_types = ["video_visit"]

        mock_db.query.return_value.filter.return_value.first.return_value = mock_schedule
        mock_db.query.return_value.filter.return_value.all.return_value = []

        start_date = date.today()
        end_date = date.today() + timedelta(days=7)

        slots = await service.get_available_slots(
            provider_id=provider_id,
            appointment_type=AppointmentType.VIDEO_VISIT,
            start_date=start_date,
            end_date=end_date,
            patient_timezone="America/New_York"
        )

        assert isinstance(slots, list)


# ============================================================================
# WAITING ROOM SERVICE TESTS
# ============================================================================

class TestWaitingRoomService:
    """Tests for WaitingRoomServiceDB"""

    @pytest.mark.asyncio
    async def test_create_waiting_room(self, mock_db, tenant_id, provider_id):
        """Test creating a waiting room"""
        service = WaitingRoomServiceDB(mock_db, tenant_id)

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        room = await service.create_waiting_room(
            name="Test Waiting Room",
            provider_id=provider_id,
            device_check_required=True,
            forms_required=True
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_check_in(self, mock_db, tenant_id, patient_id, provider_id):
        """Test checking into a waiting room"""
        service = WaitingRoomServiceDB(mock_db, tenant_id)

        room_id = uuid4()
        mock_room = MagicMock()
        mock_room.id = room_id
        mock_room.is_open = True
        mock_room.device_check_required = True
        mock_room.forms_required = True
        mock_room.entries = []

        mock_db.query.return_value.filter.return_value.first.return_value = mock_room
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        entry = await service.check_in(
            room_id=room_id,
            patient_id=patient_id,
            provider_id=provider_id
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_submit_device_check(self, mock_db, tenant_id):
        """Test submitting device check results"""
        service = WaitingRoomServiceDB(mock_db, tenant_id)

        entry_id = uuid4()
        mock_entry = MagicMock()
        mock_entry.id = entry_id
        mock_entry.device_check_status = DeviceCheckStatus.NOT_STARTED

        mock_db.query.return_value.filter.return_value.first.return_value = mock_entry
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        device_check = {
            "camera_available": True,
            "camera_working": True,
            "microphone_available": True,
            "microphone_working": True,
            "speaker_available": True,
            "speaker_working": True,
            "connection_speed_mbps": 50.0,
            "latency_ms": 20.0,
            "browser_name": "Chrome",
            "webrtc_supported": True
        }

        result = await service.submit_device_check(entry_id, device_check)

        assert mock_entry.device_check_status == DeviceCheckStatus.PASSED

    @pytest.mark.asyncio
    async def test_admit_patient(self, mock_db, tenant_id):
        """Test admitting a patient from waiting room"""
        service = WaitingRoomServiceDB(mock_db, tenant_id)

        entry_id = uuid4()
        mock_entry = MagicMock()
        mock_entry.id = entry_id
        mock_entry.status = WaitingStatus.READY

        mock_db.query.return_value.filter.return_value.first.return_value = mock_entry
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        entry = await service.admit_patient(entry_id)

        assert mock_entry.status == WaitingStatus.IN_CALL


# ============================================================================
# PAYMENT SERVICE TESTS
# ============================================================================

class TestTelehealthPaymentService:
    """Tests for TelehealthPaymentService"""

    @pytest.mark.asyncio
    async def test_create_payment(self, mock_db, tenant_id, patient_id):
        """Test creating a payment"""
        service = TelehealthPaymentService(mock_db, tenant_id)

        appointment_id = uuid4()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        payment = await service.create_payment(
            appointment_id=appointment_id,
            patient_id=patient_id,
            amount_cents=2500,
            currency="USD"
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_authorize_payment(self, mock_db, tenant_id):
        """Test authorizing a payment"""
        service = TelehealthPaymentService(mock_db, tenant_id)

        payment_id = uuid4()
        mock_payment = MagicMock()
        mock_payment.id = payment_id
        mock_payment.status = PaymentStatus.PENDING
        mock_payment.authorized_at = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_payment
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        payment = await service.authorize_payment(payment_id)

        assert mock_payment.status == PaymentStatus.AUTHORIZED
        assert mock_payment.authorized_at is not None

    @pytest.mark.asyncio
    async def test_capture_payment(self, mock_db, tenant_id):
        """Test capturing a payment"""
        service = TelehealthPaymentService(mock_db, tenant_id)

        payment_id = uuid4()
        mock_payment = MagicMock()
        mock_payment.id = payment_id
        mock_payment.status = PaymentStatus.AUTHORIZED
        mock_payment.captured_at = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_payment
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        payment = await service.capture_payment(payment_id)

        assert mock_payment.status == PaymentStatus.CAPTURED
        assert mock_payment.captured_at is not None

    @pytest.mark.asyncio
    async def test_refund_payment(self, mock_db, tenant_id):
        """Test refunding a payment"""
        service = TelehealthPaymentService(mock_db, tenant_id)

        payment_id = uuid4()
        mock_payment = MagicMock()
        mock_payment.id = payment_id
        mock_payment.status = PaymentStatus.CAPTURED
        mock_payment.amount_cents = 2500
        mock_payment.refunded_at = None
        mock_payment.refund_amount_cents = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_payment
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        payment = await service.refund_payment(
            payment_id=payment_id,
            reason="Patient cancelled",
            amount_cents=2500
        )

        assert mock_payment.status == PaymentStatus.REFUNDED
        assert mock_payment.refunded_at is not None
        assert mock_payment.refund_amount_cents == 2500


# ============================================================================
# ANALYTICS SERVICE TESTS
# ============================================================================

class TestTelehealthAnalyticsService:
    """Tests for TelehealthAnalyticsService"""

    @pytest.mark.asyncio
    async def test_submit_satisfaction_survey(self, mock_db, tenant_id, patient_id):
        """Test submitting a satisfaction survey"""
        service = TelehealthAnalyticsService(mock_db, tenant_id)

        session_id = uuid4()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        survey = await service.submit_satisfaction_survey(
            session_id=session_id,
            overall_rating=5,
            video_quality_rating=4,
            audio_quality_rating=5,
            provider_rating=5,
            ease_of_use_rating=4,
            would_recommend=True,
            nps_score=9,
            feedback_text="Great experience!"
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_get_metrics(self, mock_db, tenant_id, provider_id):
        """Test getting telehealth metrics"""
        service = TelehealthAnalyticsService(mock_db, tenant_id)

        # Mock query results
        mock_db.query.return_value.filter.return_value.count.return_value = 100
        mock_db.query.return_value.filter.return_value.all.return_value = []

        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        metrics = await service.get_metrics(
            provider_id=provider_id,
            start_date=start_date,
            end_date=end_date
        )

        assert "total_sessions" in metrics
        assert "completed_sessions" in metrics


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_session_not_found(self, mock_db, tenant_id):
        """Test handling session not found"""
        service = TelehealthSessionService(mock_db, tenant_id)

        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(Exception):
            await service.start_session(uuid4())

    @pytest.mark.asyncio
    async def test_waiting_room_closed(self, mock_db, tenant_id, patient_id):
        """Test checking into closed waiting room"""
        service = WaitingRoomServiceDB(mock_db, tenant_id)

        room_id = uuid4()
        mock_room = MagicMock()
        mock_room.id = room_id
        mock_room.is_open = False

        mock_db.query.return_value.filter.return_value.first.return_value = mock_room

        with pytest.raises(Exception):
            await service.check_in(room_id, patient_id)

    @pytest.mark.asyncio
    async def test_payment_already_captured(self, mock_db, tenant_id):
        """Test capturing already captured payment"""
        service = TelehealthPaymentService(mock_db, tenant_id)

        payment_id = uuid4()
        mock_payment = MagicMock()
        mock_payment.id = payment_id
        mock_payment.status = PaymentStatus.CAPTURED

        mock_db.query.return_value.filter.return_value.first.return_value = mock_payment

        with pytest.raises(Exception):
            await service.capture_payment(payment_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
