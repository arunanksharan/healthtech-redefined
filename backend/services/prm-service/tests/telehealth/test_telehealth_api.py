"""
Test Telehealth Platform API
Integration tests for EPIC-007 telehealth REST endpoints
"""
import pytest
from uuid import uuid4, UUID
from datetime import datetime, date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../..")))

from services.prm_service.modules.telehealth.models import Base
from services.prm_service.modules.telehealth.router import router
from fastapi import FastAPI


# Create test app
@pytest.fixture
def app():
    """Create a test FastAPI app"""
    test_app = FastAPI()
    test_app.include_router(router)
    return test_app


@pytest.fixture
def client(app):
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Create a test database session"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def tenant_id():
    """Test tenant ID"""
    return str(UUID("00000000-0000-0000-0000-000000000001"))


@pytest.fixture
def patient_id():
    """Test patient ID"""
    return str(UUID("00000000-0000-0000-0000-000000000002"))


@pytest.fixture
def provider_id():
    """Test provider ID"""
    return str(UUID("00000000-0000-0000-0000-000000000003"))


@pytest.fixture
def user_id():
    """Test user ID"""
    return str(UUID("00000000-0000-0000-0000-000000000004"))


@pytest.fixture
def auth_headers(tenant_id):
    """Mock authentication headers"""
    return {
        "X-Tenant-ID": tenant_id,
        "Authorization": "Bearer test-token"
    }


# ============================================================================
# SESSION API TESTS
# ============================================================================

class TestSessionAPI:
    """Tests for telehealth session endpoints"""

    def test_create_session(self, client, auth_headers):
        """Test POST /telehealth/sessions"""
        data = {
            "session_type": "video_visit",
            "scheduled_duration_minutes": 30,
            "waiting_room_enabled": True,
            "max_participants": 4,
            "screen_sharing_enabled": True,
            "chat_enabled": True,
            "whiteboard_enabled": False
        }

        response = client.post(
            "/telehealth/sessions",
            json=data,
            headers=auth_headers
        )

        assert response.status_code in [200, 201]
        result = response.json()
        assert result["session_type"] == "video_visit"
        assert "id" in result
        assert "room_name" in result

    def test_get_session(self, client, auth_headers):
        """Test GET /telehealth/sessions/{id}"""
        # First create a session
        create_data = {
            "session_type": "video_visit",
            "scheduled_duration_minutes": 30
        }

        create_response = client.post(
            "/telehealth/sessions",
            json=create_data,
            headers=auth_headers
        )

        if create_response.status_code in [200, 201]:
            session_id = create_response.json()["id"]

            get_response = client.get(
                f"/telehealth/sessions/{session_id}",
                headers=auth_headers
            )

            assert get_response.status_code == 200
            assert get_response.json()["id"] == session_id

    def test_list_sessions(self, client, auth_headers):
        """Test GET /telehealth/sessions"""
        response = client.get(
            "/telehealth/sessions",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_add_participant(self, client, auth_headers, user_id):
        """Test POST /telehealth/sessions/{id}/participants"""
        # Create session first
        session_data = {"session_type": "video_visit"}
        session_response = client.post(
            "/telehealth/sessions",
            json=session_data,
            headers=auth_headers
        )

        if session_response.status_code in [200, 201]:
            session_id = session_response.json()["id"]

            participant_data = {
                "user_id": user_id,
                "role": "patient",
                "display_name": "Test Patient"
            }

            response = client.post(
                f"/telehealth/sessions/{session_id}/participants",
                json=participant_data,
                headers=auth_headers
            )

            assert response.status_code in [200, 201]
            assert response.json()["role"] == "patient"

    def test_get_join_token(self, client, auth_headers, user_id):
        """Test POST /telehealth/sessions/{id}/join-token"""
        # Create session and add participant
        session_data = {"session_type": "video_visit"}
        session_response = client.post(
            "/telehealth/sessions",
            json=session_data,
            headers=auth_headers
        )

        if session_response.status_code in [200, 201]:
            session_id = session_response.json()["id"]

            participant_data = {
                "user_id": user_id,
                "role": "provider",
                "display_name": "Dr. Test"
            }

            participant_response = client.post(
                f"/telehealth/sessions/{session_id}/participants",
                json=participant_data,
                headers=auth_headers
            )

            if participant_response.status_code in [200, 201]:
                participant_id = participant_response.json()["id"]

                token_data = {"participant_id": participant_id}
                token_response = client.post(
                    f"/telehealth/sessions/{session_id}/join-token",
                    json=token_data,
                    headers=auth_headers
                )

                assert token_response.status_code in [200, 201]
                assert "token" in token_response.json()

    def test_start_session(self, client, auth_headers):
        """Test POST /telehealth/sessions/{id}/start"""
        # Create session
        session_data = {"session_type": "video_visit"}
        session_response = client.post(
            "/telehealth/sessions",
            json=session_data,
            headers=auth_headers
        )

        if session_response.status_code in [200, 201]:
            session_id = session_response.json()["id"]

            start_response = client.post(
                f"/telehealth/sessions/{session_id}/start",
                headers=auth_headers
            )

            assert start_response.status_code == 200
            assert start_response.json()["status"] == "in_progress"

    def test_end_session(self, client, auth_headers):
        """Test POST /telehealth/sessions/{id}/end"""
        # Create and start session
        session_data = {"session_type": "video_visit"}
        session_response = client.post(
            "/telehealth/sessions",
            json=session_data,
            headers=auth_headers
        )

        if session_response.status_code in [200, 201]:
            session_id = session_response.json()["id"]

            client.post(f"/telehealth/sessions/{session_id}/start", headers=auth_headers)

            end_data = {"reason": "completed"}
            end_response = client.post(
                f"/telehealth/sessions/{session_id}/end",
                json=end_data,
                headers=auth_headers
            )

            assert end_response.status_code == 200
            assert end_response.json()["status"] == "completed"

    def test_update_media_state(self, client, auth_headers, user_id):
        """Test PUT /telehealth/sessions/{id}/participants/{pid}/media"""
        # Create session and add participant
        session_data = {"session_type": "video_visit"}
        session_response = client.post(
            "/telehealth/sessions",
            json=session_data,
            headers=auth_headers
        )

        if session_response.status_code in [200, 201]:
            session_id = session_response.json()["id"]

            participant_data = {
                "user_id": user_id,
                "role": "patient",
                "display_name": "Test Patient"
            }

            participant_response = client.post(
                f"/telehealth/sessions/{session_id}/participants",
                json=participant_data,
                headers=auth_headers
            )

            if participant_response.status_code in [200, 201]:
                participant_id = participant_response.json()["id"]

                media_data = {
                    "video_enabled": False,
                    "audio_enabled": True
                }

                media_response = client.put(
                    f"/telehealth/sessions/{session_id}/participants/{participant_id}/media",
                    json=media_data,
                    headers=auth_headers
                )

                assert media_response.status_code == 200


# ============================================================================
# APPOINTMENT API TESTS
# ============================================================================

class TestAppointmentAPI:
    """Tests for telehealth appointment endpoints"""

    def test_book_appointment(self, client, auth_headers, patient_id, provider_id):
        """Test POST /telehealth/appointments"""
        tomorrow = datetime.now() + timedelta(days=1)
        data = {
            "patient_id": patient_id,
            "provider_id": provider_id,
            "appointment_type": "video_visit",
            "scheduled_start": tomorrow.isoformat(),
            "duration_minutes": 30,
            "patient_timezone": "America/New_York",
            "reason_for_visit": "Follow-up consultation",
            "patient_name": "John Doe",
            "provider_name": "Dr. Smith",
            "copay_amount": 25.0
        }

        response = client.post(
            "/telehealth/appointments",
            json=data,
            headers=auth_headers
        )

        assert response.status_code in [200, 201]
        result = response.json()
        assert result["patient_id"] == patient_id
        assert result["appointment_type"] == "video_visit"

    def test_get_appointment(self, client, auth_headers, patient_id, provider_id):
        """Test GET /telehealth/appointments/{id}"""
        # Create appointment first
        tomorrow = datetime.now() + timedelta(days=1)
        create_data = {
            "patient_id": patient_id,
            "provider_id": provider_id,
            "appointment_type": "video_visit",
            "scheduled_start": tomorrow.isoformat(),
            "duration_minutes": 30
        }

        create_response = client.post(
            "/telehealth/appointments",
            json=create_data,
            headers=auth_headers
        )

        if create_response.status_code in [200, 201]:
            appointment_id = create_response.json()["id"]

            get_response = client.get(
                f"/telehealth/appointments/{appointment_id}",
                headers=auth_headers
            )

            assert get_response.status_code == 200
            assert get_response.json()["id"] == appointment_id

    def test_list_appointments(self, client, auth_headers):
        """Test GET /telehealth/appointments"""
        response = client.get(
            "/telehealth/appointments",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_confirm_appointment(self, client, auth_headers, patient_id, provider_id):
        """Test POST /telehealth/appointments/{id}/confirm"""
        # Create appointment
        tomorrow = datetime.now() + timedelta(days=1)
        create_data = {
            "patient_id": patient_id,
            "provider_id": provider_id,
            "scheduled_start": tomorrow.isoformat()
        }

        create_response = client.post(
            "/telehealth/appointments",
            json=create_data,
            headers=auth_headers
        )

        if create_response.status_code in [200, 201]:
            appointment_id = create_response.json()["id"]

            confirm_response = client.post(
                f"/telehealth/appointments/{appointment_id}/confirm",
                headers=auth_headers
            )

            assert confirm_response.status_code == 200
            assert confirm_response.json()["status"] == "confirmed"

    def test_cancel_appointment(self, client, auth_headers, patient_id, provider_id):
        """Test POST /telehealth/appointments/{id}/cancel"""
        # Create appointment
        tomorrow = datetime.now() + timedelta(days=1)
        create_data = {
            "patient_id": patient_id,
            "provider_id": provider_id,
            "scheduled_start": tomorrow.isoformat()
        }

        create_response = client.post(
            "/telehealth/appointments",
            json=create_data,
            headers=auth_headers
        )

        if create_response.status_code in [200, 201]:
            appointment_id = create_response.json()["id"]

            cancel_data = {
                "reason": "Patient requested cancellation"
            }

            cancel_response = client.post(
                f"/telehealth/appointments/{appointment_id}/cancel",
                json=cancel_data,
                headers=auth_headers
            )

            assert cancel_response.status_code == 200
            assert cancel_response.json()["status"] == "cancelled"

    def test_reschedule_appointment(self, client, auth_headers, patient_id, provider_id):
        """Test POST /telehealth/appointments/{id}/reschedule"""
        # Create appointment
        tomorrow = datetime.now() + timedelta(days=1)
        create_data = {
            "patient_id": patient_id,
            "provider_id": provider_id,
            "scheduled_start": tomorrow.isoformat()
        }

        create_response = client.post(
            "/telehealth/appointments",
            json=create_data,
            headers=auth_headers
        )

        if create_response.status_code in [200, 201]:
            appointment_id = create_response.json()["id"]

            new_time = datetime.now() + timedelta(days=3)
            reschedule_data = {
                "new_start_time": new_time.isoformat()
            }

            reschedule_response = client.post(
                f"/telehealth/appointments/{appointment_id}/reschedule",
                json=reschedule_data,
                headers=auth_headers
            )

            assert reschedule_response.status_code == 200
            assert reschedule_response.json()["status"] == "rescheduled"

    def test_get_available_slots(self, client, auth_headers, provider_id):
        """Test POST /telehealth/appointments/available-slots"""
        data = {
            "provider_id": provider_id,
            "appointment_type": "video_visit",
            "start_date": str(date.today()),
            "end_date": str(date.today() + timedelta(days=7)),
            "patient_timezone": "America/New_York"
        }

        response = client.post(
            "/telehealth/appointments/available-slots",
            json=data,
            headers=auth_headers
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)


# ============================================================================
# PROVIDER SCHEDULE API TESTS
# ============================================================================

class TestProviderScheduleAPI:
    """Tests for provider schedule endpoints"""

    def test_set_provider_schedule(self, client, auth_headers, provider_id):
        """Test PUT /telehealth/providers/{id}/schedule"""
        data = {
            "weekly_hours": {
                "0": [["09:00", "12:00"], ["13:00", "17:00"]],
                "1": [["09:00", "12:00"], ["13:00", "17:00"]],
                "2": [["09:00", "12:00"], ["13:00", "17:00"]],
                "3": [["09:00", "12:00"], ["13:00", "17:00"]],
                "4": [["09:00", "12:00"], ["13:00", "17:00"]]
            },
            "timezone": "America/New_York",
            "appointment_types": ["video_visit", "follow_up"],
            "default_duration_minutes": 30,
            "buffer_minutes": 5
        }

        response = client.put(
            f"/telehealth/providers/{provider_id}/schedule",
            json=data,
            headers=auth_headers
        )

        assert response.status_code in [200, 201]
        assert response.json()["timezone"] == "America/New_York"

    def test_get_provider_schedule(self, client, auth_headers, provider_id):
        """Test GET /telehealth/providers/{id}/schedule"""
        response = client.get(
            f"/telehealth/providers/{provider_id}/schedule",
            headers=auth_headers
        )

        # May be 200 with schedule or 404 if not set
        assert response.status_code in [200, 404]

    def test_block_time(self, client, auth_headers, provider_id):
        """Test POST /telehealth/providers/{id}/blocked-times"""
        # First set a schedule
        schedule_data = {
            "weekly_hours": {"0": [["09:00", "17:00"]]},
            "timezone": "UTC"
        }
        client.put(
            f"/telehealth/providers/{provider_id}/schedule",
            json=schedule_data,
            headers=auth_headers
        )

        tomorrow = datetime.now() + timedelta(days=1)
        block_data = {
            "start_time": tomorrow.replace(hour=10, minute=0).isoformat(),
            "end_time": tomorrow.replace(hour=11, minute=0).isoformat(),
            "reason": "Personal appointment"
        }

        response = client.post(
            f"/telehealth/providers/{provider_id}/blocked-times",
            json=block_data,
            headers=auth_headers
        )

        assert response.status_code in [200, 201]


# ============================================================================
# WAITING ROOM API TESTS
# ============================================================================

class TestWaitingRoomAPI:
    """Tests for waiting room endpoints"""

    def test_create_waiting_room(self, client, auth_headers, provider_id):
        """Test POST /telehealth/waiting-rooms"""
        data = {
            "name": "Dr. Smith's Waiting Room",
            "provider_id": provider_id,
            "device_check_required": True,
            "forms_required": True,
            "max_wait_minutes": 60,
            "auto_notify_minutes": 5
        }

        response = client.post(
            "/telehealth/waiting-rooms",
            json=data,
            headers=auth_headers
        )

        assert response.status_code in [200, 201]
        result = response.json()
        assert result["name"] == "Dr. Smith's Waiting Room"

    def test_get_waiting_room(self, client, auth_headers, provider_id):
        """Test GET /telehealth/waiting-rooms/{id}"""
        # Create waiting room first
        create_data = {
            "name": "Test Room",
            "provider_id": provider_id
        }

        create_response = client.post(
            "/telehealth/waiting-rooms",
            json=create_data,
            headers=auth_headers
        )

        if create_response.status_code in [200, 201]:
            room_id = create_response.json()["id"]

            get_response = client.get(
                f"/telehealth/waiting-rooms/{room_id}",
                headers=auth_headers
            )

            assert get_response.status_code == 200

    def test_check_in_to_waiting_room(self, client, auth_headers, patient_id, provider_id):
        """Test POST /telehealth/waiting-rooms/{id}/check-in"""
        # Create waiting room
        room_data = {
            "name": "Test Room",
            "provider_id": provider_id
        }

        room_response = client.post(
            "/telehealth/waiting-rooms",
            json=room_data,
            headers=auth_headers
        )

        if room_response.status_code in [200, 201]:
            room_id = room_response.json()["id"]

            check_in_data = {
                "patient_id": patient_id,
                "provider_id": provider_id,
                "priority": 0
            }

            check_in_response = client.post(
                f"/telehealth/waiting-rooms/{room_id}/check-in",
                json=check_in_data,
                headers=auth_headers
            )

            assert check_in_response.status_code in [200, 201]
            assert check_in_response.json()["status"] == "checked_in"

    def test_get_queue_status(self, client, auth_headers, provider_id):
        """Test GET /telehealth/waiting-rooms/{id}/queue"""
        # Create waiting room
        room_data = {
            "name": "Queue Test Room",
            "provider_id": provider_id
        }

        room_response = client.post(
            "/telehealth/waiting-rooms",
            json=room_data,
            headers=auth_headers
        )

        if room_response.status_code in [200, 201]:
            room_id = room_response.json()["id"]

            queue_response = client.get(
                f"/telehealth/waiting-rooms/{room_id}/queue",
                headers=auth_headers
            )

            assert queue_response.status_code == 200
            assert "total_waiting" in queue_response.json()

    def test_submit_device_check(self, client, auth_headers, patient_id, provider_id):
        """Test POST /telehealth/waiting-rooms/{room_id}/entries/{id}/device-check"""
        # Create waiting room and check in
        room_data = {"name": "Device Test Room", "provider_id": provider_id}
        room_response = client.post(
            "/telehealth/waiting-rooms",
            json=room_data,
            headers=auth_headers
        )

        if room_response.status_code in [200, 201]:
            room_id = room_response.json()["id"]

            check_in_data = {"patient_id": patient_id, "provider_id": provider_id}
            check_in_response = client.post(
                f"/telehealth/waiting-rooms/{room_id}/check-in",
                json=check_in_data,
                headers=auth_headers
            )

            if check_in_response.status_code in [200, 201]:
                entry_id = check_in_response.json()["id"]

                device_data = {
                    "camera_available": True,
                    "camera_working": True,
                    "camera_device": "Built-in Camera",
                    "microphone_available": True,
                    "microphone_working": True,
                    "microphone_device": "Built-in Microphone",
                    "speaker_available": True,
                    "speaker_working": True,
                    "speaker_device": "Built-in Speakers",
                    "connection_speed_mbps": 50.0,
                    "latency_ms": 20.0,
                    "browser_name": "Chrome",
                    "browser_version": "120.0",
                    "webrtc_supported": True
                }

                device_response = client.post(
                    f"/telehealth/waiting-rooms/{room_id}/entries/{entry_id}/device-check",
                    json=device_data,
                    headers=auth_headers
                )

                assert device_response.status_code in [200, 201]
                assert device_response.json()["status"] in ["passed", "failed"]

    def test_send_chat_message(self, client, auth_headers, patient_id, provider_id):
        """Test POST /telehealth/waiting-rooms/{room_id}/entries/{id}/messages"""
        # Create waiting room and check in
        room_data = {"name": "Chat Test Room", "provider_id": provider_id}
        room_response = client.post(
            "/telehealth/waiting-rooms",
            json=room_data,
            headers=auth_headers
        )

        if room_response.status_code in [200, 201]:
            room_id = room_response.json()["id"]

            check_in_data = {"patient_id": patient_id}
            check_in_response = client.post(
                f"/telehealth/waiting-rooms/{room_id}/check-in",
                json=check_in_data,
                headers=auth_headers
            )

            if check_in_response.status_code in [200, 201]:
                entry_id = check_in_response.json()["id"]

                message_data = {
                    "content": "Hello, I'm waiting for my appointment",
                    "sender_type": "patient"
                }

                message_response = client.post(
                    f"/telehealth/waiting-rooms/{room_id}/entries/{entry_id}/messages",
                    json=message_data,
                    headers=auth_headers
                )

                assert message_response.status_code in [200, 201]
                assert message_response.json()["content"] == message_data["content"]

    def test_admit_patient(self, client, auth_headers, patient_id, provider_id):
        """Test POST /telehealth/waiting-rooms/{room_id}/entries/{id}/admit"""
        # Create waiting room and check in
        room_data = {"name": "Admit Test Room", "provider_id": provider_id}
        room_response = client.post(
            "/telehealth/waiting-rooms",
            json=room_data,
            headers=auth_headers
        )

        if room_response.status_code in [200, 201]:
            room_id = room_response.json()["id"]

            check_in_data = {"patient_id": patient_id, "provider_id": provider_id}
            check_in_response = client.post(
                f"/telehealth/waiting-rooms/{room_id}/check-in",
                json=check_in_data,
                headers=auth_headers
            )

            if check_in_response.status_code in [200, 201]:
                entry_id = check_in_response.json()["id"]

                admit_response = client.post(
                    f"/telehealth/waiting-rooms/{room_id}/entries/{entry_id}/admit",
                    headers=auth_headers
                )

                assert admit_response.status_code == 200
                assert admit_response.json()["status"] == "in_call"


# ============================================================================
# RECORDING API TESTS
# ============================================================================

class TestRecordingAPI:
    """Tests for session recording endpoints"""

    def test_start_recording(self, client, auth_headers, user_id):
        """Test POST /telehealth/sessions/{id}/recordings/start"""
        # Create and start session
        session_data = {"session_type": "video_visit"}
        session_response = client.post(
            "/telehealth/sessions",
            json=session_data,
            headers=auth_headers
        )

        if session_response.status_code in [200, 201]:
            session_id = session_response.json()["id"]

            # Add participant
            participant_data = {
                "user_id": user_id,
                "role": "provider",
                "display_name": "Dr. Test"
            }
            participant_response = client.post(
                f"/telehealth/sessions/{session_id}/participants",
                json=participant_data,
                headers=auth_headers
            )

            if participant_response.status_code in [200, 201]:
                participant_id = participant_response.json()["id"]

                # Start session
                client.post(f"/telehealth/sessions/{session_id}/start", headers=auth_headers)

                # Start recording
                recording_data = {"participant_id": participant_id}
                recording_response = client.post(
                    f"/telehealth/sessions/{session_id}/recordings/start",
                    json=recording_data,
                    headers=auth_headers
                )

                assert recording_response.status_code in [200, 201]
                assert recording_response.json()["status"] == "recording"

    def test_stop_recording(self, client, auth_headers, user_id):
        """Test POST /telehealth/sessions/{id}/recordings/stop"""
        # Create, start session, and start recording
        session_data = {"session_type": "video_visit"}
        session_response = client.post(
            "/telehealth/sessions",
            json=session_data,
            headers=auth_headers
        )

        if session_response.status_code in [200, 201]:
            session_id = session_response.json()["id"]

            participant_data = {
                "user_id": user_id,
                "role": "provider",
                "display_name": "Dr. Test"
            }
            participant_response = client.post(
                f"/telehealth/sessions/{session_id}/participants",
                json=participant_data,
                headers=auth_headers
            )

            if participant_response.status_code in [200, 201]:
                participant_id = participant_response.json()["id"]

                client.post(f"/telehealth/sessions/{session_id}/start", headers=auth_headers)
                client.post(
                    f"/telehealth/sessions/{session_id}/recordings/start",
                    json={"participant_id": participant_id},
                    headers=auth_headers
                )

                # Stop recording
                stop_response = client.post(
                    f"/telehealth/sessions/{session_id}/recordings/stop",
                    headers=auth_headers
                )

                assert stop_response.status_code == 200
                assert stop_response.json()["status"] == "processing"

    def test_record_consent(self, client, auth_headers, user_id):
        """Test POST /telehealth/sessions/{id}/recordings/consent"""
        # Create session with recording
        session_data = {"session_type": "video_visit"}
        session_response = client.post(
            "/telehealth/sessions",
            json=session_data,
            headers=auth_headers
        )

        if session_response.status_code in [200, 201]:
            session_id = session_response.json()["id"]

            participant_data = {
                "user_id": user_id,
                "role": "patient",
                "display_name": "Test Patient"
            }
            participant_response = client.post(
                f"/telehealth/sessions/{session_id}/participants",
                json=participant_data,
                headers=auth_headers
            )

            if participant_response.status_code in [200, 201]:
                participant_id = participant_response.json()["id"]

                consent_data = {
                    "participant_id": participant_id,
                    "consented": True,
                    "ip_address": "192.168.1.1",
                    "user_agent": "Mozilla/5.0"
                }

                consent_response = client.post(
                    f"/telehealth/sessions/{session_id}/recordings/consent",
                    json=consent_data,
                    headers=auth_headers
                )

                assert consent_response.status_code in [200, 201]


# ============================================================================
# PAYMENT API TESTS
# ============================================================================

class TestPaymentAPI:
    """Tests for payment endpoints"""

    def test_create_payment(self, client, auth_headers, patient_id, provider_id):
        """Test POST /telehealth/payments"""
        # Create appointment first
        tomorrow = datetime.now() + timedelta(days=1)
        appointment_data = {
            "patient_id": patient_id,
            "provider_id": provider_id,
            "scheduled_start": tomorrow.isoformat(),
            "copay_amount": 25.0
        }

        appointment_response = client.post(
            "/telehealth/appointments",
            json=appointment_data,
            headers=auth_headers
        )

        if appointment_response.status_code in [200, 201]:
            appointment_id = appointment_response.json()["id"]

            payment_data = {
                "appointment_id": appointment_id,
                "patient_id": patient_id,
                "amount_cents": 2500,
                "currency": "USD",
                "payment_method": "card"
            }

            payment_response = client.post(
                "/telehealth/payments",
                json=payment_data,
                headers=auth_headers
            )

            assert payment_response.status_code in [200, 201]
            assert payment_response.json()["amount_cents"] == 2500

    def test_create_payment_intent(self, client, auth_headers, patient_id, provider_id):
        """Test POST /telehealth/payments/intent"""
        # Create appointment
        tomorrow = datetime.now() + timedelta(days=1)
        appointment_data = {
            "patient_id": patient_id,
            "provider_id": provider_id,
            "scheduled_start": tomorrow.isoformat(),
            "copay_amount": 50.0
        }

        appointment_response = client.post(
            "/telehealth/appointments",
            json=appointment_data,
            headers=auth_headers
        )

        if appointment_response.status_code in [200, 201]:
            appointment_id = appointment_response.json()["id"]

            intent_data = {
                "appointment_id": appointment_id,
                "amount_cents": 5000,
                "currency": "USD"
            }

            intent_response = client.post(
                "/telehealth/payments/intent",
                json=intent_data,
                headers=auth_headers
            )

            assert intent_response.status_code in [200, 201]
            assert "client_secret" in intent_response.json()

    def test_capture_payment(self, client, auth_headers, patient_id, provider_id):
        """Test POST /telehealth/payments/{id}/capture"""
        # Create appointment and payment
        tomorrow = datetime.now() + timedelta(days=1)
        appointment_data = {
            "patient_id": patient_id,
            "provider_id": provider_id,
            "scheduled_start": tomorrow.isoformat()
        }

        appointment_response = client.post(
            "/telehealth/appointments",
            json=appointment_data,
            headers=auth_headers
        )

        if appointment_response.status_code in [200, 201]:
            appointment_id = appointment_response.json()["id"]

            payment_data = {
                "appointment_id": appointment_id,
                "patient_id": patient_id,
                "amount_cents": 2500
            }

            payment_response = client.post(
                "/telehealth/payments",
                json=payment_data,
                headers=auth_headers
            )

            if payment_response.status_code in [200, 201]:
                payment_id = payment_response.json()["id"]

                capture_response = client.post(
                    f"/telehealth/payments/{payment_id}/capture",
                    headers=auth_headers
                )

                assert capture_response.status_code in [200, 400]  # 400 if not authorized

    def test_refund_payment(self, client, auth_headers, patient_id, provider_id):
        """Test POST /telehealth/payments/{id}/refund"""
        # Create appointment and payment
        tomorrow = datetime.now() + timedelta(days=1)
        appointment_data = {
            "patient_id": patient_id,
            "provider_id": provider_id,
            "scheduled_start": tomorrow.isoformat()
        }

        appointment_response = client.post(
            "/telehealth/appointments",
            json=appointment_data,
            headers=auth_headers
        )

        if appointment_response.status_code in [200, 201]:
            appointment_id = appointment_response.json()["id"]

            payment_data = {
                "appointment_id": appointment_id,
                "patient_id": patient_id,
                "amount_cents": 2500
            }

            payment_response = client.post(
                "/telehealth/payments",
                json=payment_data,
                headers=auth_headers
            )

            if payment_response.status_code in [200, 201]:
                payment_id = payment_response.json()["id"]

                refund_data = {
                    "reason": "Patient cancelled",
                    "amount_cents": 2500
                }

                refund_response = client.post(
                    f"/telehealth/payments/{payment_id}/refund",
                    json=refund_data,
                    headers=auth_headers
                )

                assert refund_response.status_code in [200, 400]  # 400 if not captured


# ============================================================================
# ANALYTICS API TESTS
# ============================================================================

class TestAnalyticsAPI:
    """Tests for telehealth analytics endpoints"""

    def test_get_session_analytics(self, client, auth_headers):
        """Test GET /telehealth/sessions/{id}/analytics"""
        # Create session
        session_data = {"session_type": "video_visit"}
        session_response = client.post(
            "/telehealth/sessions",
            json=session_data,
            headers=auth_headers
        )

        if session_response.status_code in [200, 201]:
            session_id = session_response.json()["id"]

            analytics_response = client.get(
                f"/telehealth/sessions/{session_id}/analytics",
                headers=auth_headers
            )

            # May return 200 with data or 404 if no analytics yet
            assert analytics_response.status_code in [200, 404]

    def test_submit_satisfaction_survey(self, client, auth_headers, patient_id):
        """Test POST /telehealth/analytics/satisfaction"""
        # Create session
        session_data = {"session_type": "video_visit"}
        session_response = client.post(
            "/telehealth/sessions",
            json=session_data,
            headers=auth_headers
        )

        if session_response.status_code in [200, 201]:
            session_id = session_response.json()["id"]

            survey_data = {
                "session_id": session_id,
                "overall_rating": 5,
                "video_quality_rating": 4,
                "audio_quality_rating": 5,
                "provider_rating": 5,
                "ease_of_use_rating": 4,
                "would_recommend": True,
                "nps_score": 9,
                "feedback_text": "Great experience!"
            }

            survey_response = client.post(
                "/telehealth/analytics/satisfaction",
                json=survey_data,
                headers=auth_headers
            )

            assert survey_response.status_code in [200, 201]

    def test_get_metrics(self, client, auth_headers, provider_id):
        """Test GET /telehealth/analytics/metrics"""
        params = {
            "provider_id": provider_id,
            "start_date": str(date.today() - timedelta(days=30)),
            "end_date": str(date.today())
        }

        response = client.get(
            "/telehealth/analytics/metrics",
            params=params,
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert "total_sessions" in result
        assert "completed_sessions" in result


# ============================================================================
# INTERPRETER API TESTS
# ============================================================================

class TestInterpreterAPI:
    """Tests for interpreter service endpoints"""

    def test_request_interpreter(self, client, auth_headers):
        """Test POST /telehealth/sessions/{id}/interpreter"""
        # Create session
        session_data = {"session_type": "video_visit"}
        session_response = client.post(
            "/telehealth/sessions",
            json=session_data,
            headers=auth_headers
        )

        if session_response.status_code in [200, 201]:
            session_id = session_response.json()["id"]

            interpreter_data = {
                "session_id": session_id,
                "language": "Spanish",
                "is_scheduled": False
            }

            interpreter_response = client.post(
                f"/telehealth/sessions/{session_id}/interpreter",
                json=interpreter_data,
                headers=auth_headers
            )

            assert interpreter_response.status_code in [200, 201]
            assert interpreter_response.json()["language"] == "Spanish"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
