"""
Telehealth Platform Service Layer

Business logic for telehealth operations:
- Session management with persistence
- Appointment booking and scheduling
- Waiting room operations
- Recording management
- Payment processing
- Analytics

Integrates with shared telehealth modules for core functionality.

EPIC-007: Telehealth Platform
"""

from datetime import datetime, timezone, timedelta, date
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import logging
import os

from .models import (
    TelehealthSession, SessionParticipant, SessionEvent,
    TelehealthAppointment, AppointmentReminder, ProviderSchedule, ScheduleBlockedTime,
    WaitingRoom, WaitingRoomEntry, WaitingRoomMessage, PreVisitForm,
    SessionRecording, RecordingConsent,
    SessionAnalytics, TelehealthPayment, PatientSatisfactionSurvey,
    SessionStatus, ParticipantRole, ParticipantStatus,
    AppointmentType, AppointmentStatus,
    WaitingStatus, DeviceCheckStatus, RecordingStatus, PaymentStatus
)
from .schemas import (
    SessionCreate, ParticipantCreate, MediaStateUpdate, ConnectionQualityUpdate,
    AppointmentCreate, AppointmentReschedule, AvailableSlotsRequest, AvailableSlot,
    ProviderScheduleCreate, BlockedTimeCreate,
    WaitingRoomCreate, CheckInRequest, DeviceCheckResult, FormSubmission, ChatMessageCreate,
    StartRecordingRequest, RecordingConsentRequest,
    PaymentCreate, RefundRequest,
    SatisfactionSurveyCreate
)

# Import shared telehealth services
try:
    from shared.telehealth import (
        SessionManager,
        TelehealthScheduler,
        WaitingRoomService,
        VideoService,
        RecordingService,
    )
    SHARED_MODULES_AVAILABLE = True
except ImportError:
    SHARED_MODULES_AVAILABLE = False

logger = logging.getLogger(__name__)


# ============================================================================
# SESSION SERVICE
# ============================================================================

class TelehealthSessionService:
    """
    Service for managing telehealth video sessions.

    Handles session lifecycle, participants, and WebRTC/LiveKit integration.
    """

    def __init__(self, db: Session):
        self.db = db

        # Initialize shared session manager if available
        self._session_manager = None
        if SHARED_MODULES_AVAILABLE:
            self._session_manager = SessionManager(
                livekit_url=os.getenv("LIVEKIT_URL"),
                livekit_api_key=os.getenv("LIVEKIT_API_KEY"),
                livekit_api_secret=os.getenv("LIVEKIT_API_SECRET"),
            )

    async def create_session(
        self,
        tenant_id: UUID,
        data: SessionCreate,
    ) -> TelehealthSession:
        """Create a new telehealth session."""
        session_id = uuid4()
        room_name = f"telehealth-{str(session_id)[:8]}"

        session = TelehealthSession(
            id=session_id,
            tenant_id=tenant_id,
            room_name=room_name,
            session_type=data.session_type,
            appointment_id=data.appointment_id,
            scheduled_duration_minutes=data.scheduled_duration_minutes,
            max_participants=data.max_participants,
            waiting_room_enabled=data.waiting_room_enabled,
            screen_sharing_enabled=data.screen_sharing_enabled,
            chat_enabled=data.chat_enabled,
            whiteboard_enabled=data.whiteboard_enabled,
            metadata=data.metadata or {},
        )

        self.db.add(session)

        # Log event
        event = SessionEvent(
            session_id=session_id,
            tenant_id=tenant_id,
            event_type="session_created",
            data={"session_type": data.session_type},
        )
        self.db.add(event)

        self.db.commit()
        self.db.refresh(session)

        logger.info(f"Created telehealth session: {session_id}")
        return session

    async def add_participant(
        self,
        tenant_id: UUID,
        session_id: UUID,
        data: ParticipantCreate,
    ) -> SessionParticipant:
        """Add a participant to a session."""
        session = self.db.query(TelehealthSession).filter(
            TelehealthSession.id == session_id,
            TelehealthSession.tenant_id == tenant_id
        ).first()

        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Check capacity
        participant_count = self.db.query(SessionParticipant).filter(
            SessionParticipant.session_id == session_id
        ).count()

        if participant_count >= session.max_participants:
            raise ValueError("Session is at maximum capacity")

        participant = SessionParticipant(
            session_id=session_id,
            tenant_id=tenant_id,
            user_id=data.user_id,
            role=data.role,
            display_name=data.display_name,
            avatar_url=data.avatar_url,
            can_record=data.role == ParticipantRole.PROVIDER,
            can_admit_participants=data.role == ParticipantRole.PROVIDER,
        )

        self.db.add(participant)

        # Log event
        event = SessionEvent(
            session_id=session_id,
            tenant_id=tenant_id,
            event_type="participant_added",
            participant_id=participant.id,
            data={"role": data.role.value, "user_id": str(data.user_id)},
        )
        self.db.add(event)

        self.db.commit()
        self.db.refresh(participant)

        return participant

    async def generate_join_token(
        self,
        tenant_id: UUID,
        session_id: UUID,
        participant_id: UUID,
    ) -> Dict[str, Any]:
        """Generate a token for joining the video room."""
        session = self.db.query(TelehealthSession).filter(
            TelehealthSession.id == session_id,
            TelehealthSession.tenant_id == tenant_id
        ).first()

        if not session:
            raise ValueError(f"Session not found: {session_id}")

        participant = self.db.query(SessionParticipant).filter(
            SessionParticipant.id == participant_id,
            SessionParticipant.session_id == session_id
        ).first()

        if not participant:
            raise ValueError(f"Participant not found: {participant_id}")

        # Generate token using shared module or simple fallback
        if self._session_manager:
            token = await self._session_manager._generate_simple_token(
                type('obj', (object,), {'session_id': str(session_id), 'room_name': session.room_name})(),
                type('obj', (object,), {
                    'participant_id': str(participant_id),
                    'role': participant.role,
                    'display_name': participant.display_name
                })()
            )
        else:
            # Simple token generation
            import base64
            import json
            token_data = {
                "session_id": str(session_id),
                "participant_id": str(participant_id),
                "room_name": session.room_name,
                "role": participant.role.value,
                "exp": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
            }
            token = base64.urlsafe_b64encode(json.dumps(token_data).encode()).decode()

        return {
            "token": token,
            "room_name": session.room_name,
            "livekit_url": os.getenv("LIVEKIT_URL"),
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=2),
        }

    async def participant_joined(
        self,
        tenant_id: UUID,
        session_id: UUID,
        participant_id: UUID,
        connection_id: str,
        device_info: Optional[Dict[str, Any]] = None,
    ) -> SessionParticipant:
        """Handle participant joining the session."""
        session = self.db.query(TelehealthSession).filter(
            TelehealthSession.id == session_id,
            TelehealthSession.tenant_id == tenant_id
        ).first()

        if not session:
            raise ValueError(f"Session not found: {session_id}")

        participant = self.db.query(SessionParticipant).filter(
            SessionParticipant.id == participant_id,
            SessionParticipant.session_id == session_id
        ).first()

        if not participant:
            raise ValueError(f"Participant not found: {participant_id}")

        participant.status = ParticipantStatus.CONNECTED
        participant.connection_id = connection_id
        participant.device_info = device_info or {}
        participant.joined_at = datetime.now(timezone.utc)

        # Update session status
        if participant.role == ParticipantRole.PROVIDER and session.status == SessionStatus.SCHEDULED:
            session.status = SessionStatus.WAITING

        # Check if both patient and provider are connected
        connected_roles = self.db.query(SessionParticipant.role).filter(
            SessionParticipant.session_id == session_id,
            SessionParticipant.status == ParticipantStatus.CONNECTED
        ).all()
        roles = {r[0] for r in connected_roles}

        if ParticipantRole.PATIENT in roles and ParticipantRole.PROVIDER in roles:
            if session.status in (SessionStatus.SCHEDULED, SessionStatus.WAITING):
                session.status = SessionStatus.IN_PROGRESS
                session.started_at = datetime.now(timezone.utc)

        # Log event
        event = SessionEvent(
            session_id=session_id,
            tenant_id=tenant_id,
            event_type="participant_joined",
            participant_id=participant_id,
            data={"connection_id": connection_id},
        )
        self.db.add(event)

        self.db.commit()
        self.db.refresh(participant)

        return participant

    async def participant_left(
        self,
        tenant_id: UUID,
        session_id: UUID,
        participant_id: UUID,
    ) -> SessionParticipant:
        """Handle participant leaving the session."""
        participant = self.db.query(SessionParticipant).filter(
            SessionParticipant.id == participant_id,
            SessionParticipant.session_id == session_id,
            SessionParticipant.tenant_id == tenant_id
        ).first()

        if not participant:
            raise ValueError(f"Participant not found: {participant_id}")

        participant.status = ParticipantStatus.DISCONNECTED
        participant.left_at = datetime.now(timezone.utc)
        participant.connection_id = None

        # Log event
        event = SessionEvent(
            session_id=session_id,
            tenant_id=tenant_id,
            event_type="participant_left",
            participant_id=participant_id,
            data={},
        )
        self.db.add(event)

        self.db.commit()
        self.db.refresh(participant)

        return participant

    async def update_media_state(
        self,
        tenant_id: UUID,
        session_id: UUID,
        participant_id: UUID,
        data: MediaStateUpdate,
    ) -> SessionParticipant:
        """Update participant media state."""
        participant = self.db.query(SessionParticipant).filter(
            SessionParticipant.id == participant_id,
            SessionParticipant.session_id == session_id,
            SessionParticipant.tenant_id == tenant_id
        ).first()

        if not participant:
            raise ValueError(f"Participant not found: {participant_id}")

        if data.video_enabled is not None:
            participant.video_enabled = data.video_enabled
        if data.audio_enabled is not None:
            participant.audio_enabled = data.audio_enabled
        if data.screen_sharing is not None:
            if data.screen_sharing and not participant.can_share_screen:
                raise ValueError("Participant does not have screen sharing permission")
            participant.screen_sharing = data.screen_sharing

        # Log event
        event = SessionEvent(
            session_id=session_id,
            tenant_id=tenant_id,
            event_type="media_state_changed",
            participant_id=participant_id,
            data={
                "video_enabled": participant.video_enabled,
                "audio_enabled": participant.audio_enabled,
                "screen_sharing": participant.screen_sharing,
            },
        )
        self.db.add(event)

        self.db.commit()
        self.db.refresh(participant)

        return participant

    async def end_session(
        self,
        tenant_id: UUID,
        session_id: UUID,
        reason: str = "completed",
    ) -> TelehealthSession:
        """End a telehealth session."""
        session = self.db.query(TelehealthSession).filter(
            TelehealthSession.id == session_id,
            TelehealthSession.tenant_id == tenant_id
        ).first()

        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Determine final status
        if session.status == SessionStatus.WAITING:
            session.status = SessionStatus.NO_SHOW
        elif reason == "technical_failure":
            session.status = SessionStatus.TECHNICAL_FAILURE
        elif reason == "cancelled":
            session.status = SessionStatus.CANCELLED
        else:
            session.status = SessionStatus.COMPLETED

        session.ended_at = datetime.now(timezone.utc)

        # Calculate duration
        if session.started_at:
            duration = (session.ended_at - session.started_at).total_seconds()
            session.actual_duration_seconds = int(duration)

        # Disconnect all participants
        self.db.query(SessionParticipant).filter(
            SessionParticipant.session_id == session_id,
            SessionParticipant.status == ParticipantStatus.CONNECTED
        ).update({
            "status": ParticipantStatus.DISCONNECTED,
            "left_at": datetime.now(timezone.utc),
        })

        # Log event
        event = SessionEvent(
            session_id=session_id,
            tenant_id=tenant_id,
            event_type="session_ended",
            data={
                "status": session.status.value,
                "reason": reason,
                "duration_seconds": session.actual_duration_seconds,
            },
        )
        self.db.add(event)

        self.db.commit()
        self.db.refresh(session)

        logger.info(f"Ended telehealth session: {session_id}")
        return session

    async def get_session(
        self,
        tenant_id: UUID,
        session_id: UUID,
    ) -> Optional[TelehealthSession]:
        """Get a session by ID."""
        return self.db.query(TelehealthSession).filter(
            TelehealthSession.id == session_id,
            TelehealthSession.tenant_id == tenant_id
        ).first()

    async def get_active_sessions(
        self,
        tenant_id: UUID,
    ) -> List[TelehealthSession]:
        """Get all active sessions for a tenant."""
        return self.db.query(TelehealthSession).filter(
            TelehealthSession.tenant_id == tenant_id,
            TelehealthSession.status.in_([
                SessionStatus.SCHEDULED,
                SessionStatus.WAITING,
                SessionStatus.IN_PROGRESS
            ])
        ).all()

    async def get_session_participants(
        self,
        tenant_id: UUID,
        session_id: UUID,
    ) -> List[SessionParticipant]:
        """Get all participants for a session."""
        return self.db.query(SessionParticipant).filter(
            SessionParticipant.session_id == session_id,
            SessionParticipant.tenant_id == tenant_id
        ).all()


# ============================================================================
# APPOINTMENT SERVICE
# ============================================================================

class TelehealthAppointmentService:
    """
    Service for managing telehealth appointments.

    Handles scheduling, availability, and reminders.
    """

    def __init__(self, db: Session):
        self.db = db

    async def book_appointment(
        self,
        tenant_id: UUID,
        data: AppointmentCreate,
    ) -> TelehealthAppointment:
        """Book a telehealth appointment."""
        # Calculate end time
        scheduled_end = data.scheduled_start + timedelta(minutes=data.duration_minutes)

        # Verify slot is available
        if not await self._check_slot_available(
            tenant_id, data.provider_id, data.scheduled_start, scheduled_end
        ):
            raise ValueError("Selected time slot is not available")

        # Get provider timezone
        schedule = self.db.query(ProviderSchedule).filter(
            ProviderSchedule.tenant_id == tenant_id,
            ProviderSchedule.provider_id == data.provider_id
        ).first()
        provider_timezone = schedule.timezone if schedule else "UTC"

        appointment = TelehealthAppointment(
            tenant_id=tenant_id,
            patient_id=data.patient_id,
            provider_id=data.provider_id,
            patient_name=data.patient_name,
            provider_name=data.provider_name,
            appointment_type=data.appointment_type,
            scheduled_start=data.scheduled_start,
            scheduled_end=scheduled_end,
            duration_minutes=data.duration_minutes,
            patient_timezone=data.patient_timezone,
            provider_timezone=provider_timezone,
            reason_for_visit=data.reason_for_visit,
            chief_complaint=data.chief_complaint,
            copay_amount=data.copay_amount,
            metadata=data.metadata or {},
        )

        # Generate join URL
        appointment.join_url = f"/telehealth/join/{appointment.id}"

        self.db.add(appointment)

        # Create reminders
        await self._create_reminders(appointment)

        self.db.commit()
        self.db.refresh(appointment)

        logger.info(f"Booked telehealth appointment: {appointment.id}")
        return appointment

    async def _check_slot_available(
        self,
        tenant_id: UUID,
        provider_id: UUID,
        start_time: datetime,
        end_time: datetime,
    ) -> bool:
        """Check if a slot conflicts with existing appointments."""
        conflict = self.db.query(TelehealthAppointment).filter(
            TelehealthAppointment.tenant_id == tenant_id,
            TelehealthAppointment.provider_id == provider_id,
            TelehealthAppointment.status.notin_([
                AppointmentStatus.CANCELLED,
                AppointmentStatus.RESCHEDULED
            ]),
            # Check overlap
            TelehealthAppointment.scheduled_start < end_time,
            TelehealthAppointment.scheduled_end > start_time,
        ).first()

        return conflict is None

    async def _create_reminders(self, appointment: TelehealthAppointment):
        """Create appointment reminders."""
        reminders_config = [
            ("email", timedelta(hours=24)),
            ("sms", timedelta(hours=1)),
            ("push", timedelta(minutes=15)),
        ]

        for reminder_type, delta in reminders_config:
            reminder = AppointmentReminder(
                appointment_id=appointment.id,
                tenant_id=appointment.tenant_id,
                reminder_type=reminder_type,
                scheduled_for=appointment.scheduled_start - delta,
                content=f"Your telehealth appointment is coming up. Join: {appointment.join_url}",
            )
            self.db.add(reminder)

    async def confirm_appointment(
        self,
        tenant_id: UUID,
        appointment_id: UUID,
    ) -> TelehealthAppointment:
        """Confirm an appointment."""
        appointment = self.db.query(TelehealthAppointment).filter(
            TelehealthAppointment.id == appointment_id,
            TelehealthAppointment.tenant_id == tenant_id
        ).first()

        if not appointment:
            raise ValueError(f"Appointment not found: {appointment_id}")

        appointment.status = AppointmentStatus.CONFIRMED
        appointment.confirmed_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(appointment)

        return appointment

    async def cancel_appointment(
        self,
        tenant_id: UUID,
        appointment_id: UUID,
        reason: str,
        cancelled_by: Optional[UUID] = None,
    ) -> TelehealthAppointment:
        """Cancel an appointment."""
        appointment = self.db.query(TelehealthAppointment).filter(
            TelehealthAppointment.id == appointment_id,
            TelehealthAppointment.tenant_id == tenant_id
        ).first()

        if not appointment:
            raise ValueError(f"Appointment not found: {appointment_id}")

        appointment.status = AppointmentStatus.CANCELLED
        appointment.cancelled_at = datetime.now(timezone.utc)
        appointment.cancellation_reason = reason
        appointment.cancelled_by = cancelled_by

        self.db.commit()
        self.db.refresh(appointment)

        logger.info(f"Cancelled appointment: {appointment_id}")
        return appointment

    async def reschedule_appointment(
        self,
        tenant_id: UUID,
        appointment_id: UUID,
        new_start_time: datetime,
    ) -> TelehealthAppointment:
        """Reschedule an appointment."""
        original = self.db.query(TelehealthAppointment).filter(
            TelehealthAppointment.id == appointment_id,
            TelehealthAppointment.tenant_id == tenant_id
        ).first()

        if not original:
            raise ValueError(f"Appointment not found: {appointment_id}")

        # Calculate new end time
        new_end_time = new_start_time + timedelta(minutes=original.duration_minutes)

        # Check availability
        if not await self._check_slot_available(
            tenant_id, original.provider_id, new_start_time, new_end_time
        ):
            raise ValueError("New time slot is not available")

        # Mark original as rescheduled
        original.status = AppointmentStatus.RESCHEDULED

        # Create new appointment
        new_appointment = TelehealthAppointment(
            tenant_id=tenant_id,
            patient_id=original.patient_id,
            provider_id=original.provider_id,
            patient_name=original.patient_name,
            provider_name=original.provider_name,
            appointment_type=original.appointment_type,
            scheduled_start=new_start_time,
            scheduled_end=new_end_time,
            duration_minutes=original.duration_minutes,
            patient_timezone=original.patient_timezone,
            provider_timezone=original.provider_timezone,
            reason_for_visit=original.reason_for_visit,
            rescheduled_from=original.id,
            metadata={"rescheduled_from": str(original.id)},
        )
        new_appointment.join_url = f"/telehealth/join/{new_appointment.id}"

        original.rescheduled_to = new_appointment.id

        self.db.add(new_appointment)
        await self._create_reminders(new_appointment)

        self.db.commit()
        self.db.refresh(new_appointment)

        logger.info(f"Rescheduled appointment {appointment_id} to {new_appointment.id}")
        return new_appointment

    async def get_available_slots(
        self,
        tenant_id: UUID,
        request: AvailableSlotsRequest,
    ) -> List[AvailableSlot]:
        """Get available appointment slots for a provider."""
        import pytz

        schedule = self.db.query(ProviderSchedule).filter(
            ProviderSchedule.tenant_id == tenant_id,
            ProviderSchedule.provider_id == request.provider_id,
            ProviderSchedule.is_active == True
        ).first()

        if not schedule:
            return []

        slots = []
        provider_tz = pytz.timezone(schedule.timezone)
        patient_tz = pytz.timezone(request.patient_timezone)

        duration_minutes = schedule.default_duration_minutes
        buffer_minutes = schedule.buffer_minutes

        current_date = request.start_date
        while current_date <= request.end_date:
            weekday = current_date.weekday()
            day_hours = schedule.weekly_hours.get(str(weekday), [])

            for time_range in day_hours:
                start_str, end_str = time_range
                start_hour, start_min = map(int, start_str.split(":"))
                end_hour, end_min = map(int, end_str.split(":"))

                day_start = provider_tz.localize(datetime(
                    current_date.year, current_date.month, current_date.day,
                    start_hour, start_min
                ))
                day_end = provider_tz.localize(datetime(
                    current_date.year, current_date.month, current_date.day,
                    end_hour, end_min
                ))

                slot_start = day_start
                while slot_start + timedelta(minutes=duration_minutes) <= day_end:
                    slot_end = slot_start + timedelta(minutes=duration_minutes)

                    # Check availability
                    is_available = await self._check_slot_available(
                        tenant_id, request.provider_id,
                        slot_start.astimezone(timezone.utc),
                        slot_end.astimezone(timezone.utc)
                    )

                    # Only include future slots
                    if slot_start > datetime.now(provider_tz) and is_available:
                        slots.append(AvailableSlot(
                            slot_id=str(uuid4()),
                            provider_id=request.provider_id,
                            start_time=slot_start.astimezone(patient_tz),
                            end_time=slot_end.astimezone(patient_tz),
                            appointment_type=request.appointment_type,
                            is_available=True,
                        ))

                    slot_start = slot_end + timedelta(minutes=buffer_minutes)

            current_date += timedelta(days=1)

        return slots

    async def get_appointment(
        self,
        tenant_id: UUID,
        appointment_id: UUID,
    ) -> Optional[TelehealthAppointment]:
        """Get an appointment by ID."""
        return self.db.query(TelehealthAppointment).filter(
            TelehealthAppointment.id == appointment_id,
            TelehealthAppointment.tenant_id == tenant_id
        ).first()

    async def get_patient_appointments(
        self,
        tenant_id: UUID,
        patient_id: UUID,
        include_past: bool = False,
    ) -> List[TelehealthAppointment]:
        """Get appointments for a patient."""
        query = self.db.query(TelehealthAppointment).filter(
            TelehealthAppointment.tenant_id == tenant_id,
            TelehealthAppointment.patient_id == patient_id
        )

        if not include_past:
            query = query.filter(
                TelehealthAppointment.scheduled_end > datetime.now(timezone.utc)
            )

        return query.order_by(TelehealthAppointment.scheduled_start).all()

    async def get_provider_appointments(
        self,
        tenant_id: UUID,
        provider_id: UUID,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[TelehealthAppointment]:
        """Get appointments for a provider."""
        query = self.db.query(TelehealthAppointment).filter(
            TelehealthAppointment.tenant_id == tenant_id,
            TelehealthAppointment.provider_id == provider_id
        )

        if date_from:
            start_datetime = datetime.combine(date_from, datetime.min.time()).replace(tzinfo=timezone.utc)
            query = query.filter(TelehealthAppointment.scheduled_start >= start_datetime)

        if date_to:
            end_datetime = datetime.combine(date_to, datetime.max.time()).replace(tzinfo=timezone.utc)
            query = query.filter(TelehealthAppointment.scheduled_start <= end_datetime)

        return query.order_by(TelehealthAppointment.scheduled_start).all()

    async def set_provider_schedule(
        self,
        tenant_id: UUID,
        provider_id: UUID,
        data: ProviderScheduleCreate,
    ) -> ProviderSchedule:
        """Set a provider's weekly schedule."""
        existing = self.db.query(ProviderSchedule).filter(
            ProviderSchedule.tenant_id == tenant_id,
            ProviderSchedule.provider_id == provider_id
        ).first()

        if existing:
            existing.weekly_hours = data.weekly_hours
            existing.timezone = data.timezone
            existing.appointment_types = [t.value for t in data.appointment_types] if data.appointment_types else []
            existing.default_duration_minutes = data.default_duration_minutes
            existing.buffer_minutes = data.buffer_minutes
            schedule = existing
        else:
            schedule = ProviderSchedule(
                tenant_id=tenant_id,
                provider_id=provider_id,
                weekly_hours=data.weekly_hours,
                timezone=data.timezone,
                appointment_types=[t.value for t in data.appointment_types] if data.appointment_types else [],
                default_duration_minutes=data.default_duration_minutes,
                buffer_minutes=data.buffer_minutes,
            )
            self.db.add(schedule)

        self.db.commit()
        self.db.refresh(schedule)

        return schedule


# ============================================================================
# WAITING ROOM SERVICE
# ============================================================================

class WaitingRoomServiceDB:
    """
    Service for managing virtual waiting rooms.

    Handles check-in, device checks, forms, and queue management.
    """

    def __init__(self, db: Session):
        self.db = db

    async def create_waiting_room(
        self,
        tenant_id: UUID,
        data: WaitingRoomCreate,
    ) -> WaitingRoom:
        """Create a new waiting room."""
        room = WaitingRoom(
            tenant_id=tenant_id,
            name=data.name,
            provider_id=data.provider_id,
            location_id=data.location_id,
            device_check_required=data.device_check_required,
            forms_required=data.forms_required,
            max_wait_minutes=data.max_wait_minutes,
            auto_notify_minutes=data.auto_notify_minutes,
        )

        self.db.add(room)
        self.db.commit()
        self.db.refresh(room)

        logger.info(f"Created waiting room: {room.id}")
        return room

    async def check_in(
        self,
        tenant_id: UUID,
        room_id: UUID,
        data: CheckInRequest,
    ) -> WaitingRoomEntry:
        """Check a patient into the waiting room."""
        room = self.db.query(WaitingRoom).filter(
            WaitingRoom.id == room_id,
            WaitingRoom.tenant_id == tenant_id
        ).first()

        if not room:
            raise ValueError(f"Waiting room not found: {room_id}")

        if not room.is_open:
            raise ValueError("Waiting room is currently closed")

        entry = WaitingRoomEntry(
            waiting_room_id=room_id,
            tenant_id=tenant_id,
            session_id=data.session_id,
            appointment_id=data.appointment_id,
            patient_id=data.patient_id,
            provider_id=data.provider_id or room.provider_id,
            scheduled_time=data.scheduled_time,
            priority=data.priority,
        )

        self.db.add(entry)

        # Create pre-visit forms
        if data.required_forms:
            for form_type in data.required_forms:
                form = PreVisitForm(
                    entry_id=entry.id,
                    tenant_id=tenant_id,
                    form_type=form_type,
                    patient_id=data.patient_id,
                )
                self.db.add(form)

        self.db.commit()
        self.db.refresh(entry)

        # Update queue positions
        await self._update_queue_positions(room_id)

        logger.info(f"Patient {data.patient_id} checked into waiting room {room_id}")
        return entry

    async def complete_device_check(
        self,
        tenant_id: UUID,
        entry_id: UUID,
        result: DeviceCheckResult,
    ) -> WaitingRoomEntry:
        """Complete device check with results."""
        entry = self.db.query(WaitingRoomEntry).filter(
            WaitingRoomEntry.id == entry_id,
            WaitingRoomEntry.tenant_id == tenant_id
        ).first()

        if not entry:
            raise ValueError(f"Entry not found: {entry_id}")

        # Determine issues
        issues = []
        if not result.camera_working:
            issues.append("Camera not working")
        if not result.microphone_working:
            issues.append("Microphone not working")
        if not result.speaker_working:
            issues.append("Speaker not working")
        if result.connection_speed_mbps < 1.0:
            issues.append("Internet connection too slow")
        if result.latency_ms > 300:
            issues.append("High network latency")
        if not result.webrtc_supported:
            issues.append("Browser does not support video calls")

        entry.device_check_status = DeviceCheckStatus.PASSED if not issues else DeviceCheckStatus.FAILED
        entry.device_check_result = {
            "camera": {"available": result.camera_available, "working": result.camera_working},
            "microphone": {"available": result.microphone_available, "working": result.microphone_working},
            "speaker": {"available": result.speaker_available, "working": result.speaker_working},
            "network": {
                "speed_mbps": result.connection_speed_mbps,
                "latency_ms": result.latency_ms,
            },
            "browser": result.browser_name,
            "webrtc_supported": result.webrtc_supported,
            "issues": issues,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

        # Update status
        if entry.device_check_status == DeviceCheckStatus.PASSED:
            await self._check_ready_status(entry)

        self.db.commit()
        self.db.refresh(entry)

        return entry

    async def _check_ready_status(self, entry: WaitingRoomEntry):
        """Check if entry is ready to join call."""
        room = self.db.query(WaitingRoom).filter(
            WaitingRoom.id == entry.waiting_room_id
        ).first()

        device_ok = True
        if room and room.device_check_required:
            device_ok = entry.device_check_status == DeviceCheckStatus.PASSED

        forms_ok = True
        if room and room.forms_required:
            forms_ok = entry.forms_completed

        if device_ok and forms_ok:
            entry.status = WaitingStatus.READY

    async def submit_form_response(
        self,
        tenant_id: UUID,
        entry_id: UUID,
        submission: FormSubmission,
    ) -> PreVisitForm:
        """Submit responses for a pre-visit form."""
        form = self.db.query(PreVisitForm).filter(
            PreVisitForm.id == submission.form_id,
            PreVisitForm.entry_id == entry_id,
            PreVisitForm.tenant_id == tenant_id
        ).first()

        if not form:
            raise ValueError(f"Form not found: {submission.form_id}")

        form.responses = submission.responses
        form.status = "completed"
        form.completed_at = datetime.now(timezone.utc)

        # Check if all forms are complete
        entry = self.db.query(WaitingRoomEntry).filter(
            WaitingRoomEntry.id == entry_id
        ).first()

        if entry:
            all_complete = self.db.query(PreVisitForm).filter(
                PreVisitForm.entry_id == entry_id,
                PreVisitForm.status != "completed"
            ).count() == 0

            entry.forms_completed = all_complete
            await self._check_ready_status(entry)

        self.db.commit()
        self.db.refresh(form)

        return form

    async def send_chat_message(
        self,
        tenant_id: UUID,
        entry_id: UUID,
        sender_id: UUID,
        data: ChatMessageCreate,
    ) -> WaitingRoomMessage:
        """Send a chat message in the waiting room."""
        entry = self.db.query(WaitingRoomEntry).filter(
            WaitingRoomEntry.id == entry_id,
            WaitingRoomEntry.tenant_id == tenant_id
        ).first()

        if not entry:
            raise ValueError(f"Entry not found: {entry_id}")

        message = WaitingRoomMessage(
            entry_id=entry_id,
            tenant_id=tenant_id,
            sender_id=sender_id,
            sender_type=data.sender_type,
            content=data.content,
        )

        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)

        return message

    async def admit_to_call(
        self,
        tenant_id: UUID,
        entry_id: UUID,
    ) -> WaitingRoomEntry:
        """Admit patient from waiting room to the call."""
        entry = self.db.query(WaitingRoomEntry).filter(
            WaitingRoomEntry.id == entry_id,
            WaitingRoomEntry.tenant_id == tenant_id
        ).first()

        if not entry:
            raise ValueError(f"Entry not found: {entry_id}")

        entry.status = WaitingStatus.IN_CALL

        self.db.commit()
        self.db.refresh(entry)

        # Update queue
        await self._update_queue_positions(entry.waiting_room_id)

        logger.info(f"Admitted entry {entry_id} to call")
        return entry

    async def depart(
        self,
        tenant_id: UUID,
        entry_id: UUID,
        reason: str = "completed",
    ) -> WaitingRoomEntry:
        """Remove patient from waiting room."""
        entry = self.db.query(WaitingRoomEntry).filter(
            WaitingRoomEntry.id == entry_id,
            WaitingRoomEntry.tenant_id == tenant_id
        ).first()

        if not entry:
            raise ValueError(f"Entry not found: {entry_id}")

        entry.status = WaitingStatus.NO_SHOW if reason == "no_show" else WaitingStatus.DEPARTED
        entry.departed_at = datetime.now(timezone.utc)
        entry.departure_reason = reason

        self.db.commit()
        self.db.refresh(entry)

        # Update queue
        await self._update_queue_positions(entry.waiting_room_id)

        return entry

    async def _update_queue_positions(self, room_id: UUID):
        """Update queue positions for all entries in a room."""
        waiting_entries = self.db.query(WaitingRoomEntry).filter(
            WaitingRoomEntry.waiting_room_id == room_id,
            WaitingRoomEntry.status.in_([
                WaitingStatus.CHECKED_IN,
                WaitingStatus.DEVICE_CHECK,
                WaitingStatus.READY
            ])
        ).order_by(
            WaitingRoomEntry.priority.desc(),
            WaitingRoomEntry.checked_in_at
        ).all()

        for i, entry in enumerate(waiting_entries):
            entry.queue_position = i + 1
            entry.estimated_wait_minutes = (i * 15)  # Simple estimation

        self.db.commit()

    async def get_waiting_room(
        self,
        tenant_id: UUID,
        room_id: UUID,
    ) -> Optional[WaitingRoom]:
        """Get a waiting room."""
        return self.db.query(WaitingRoom).filter(
            WaitingRoom.id == room_id,
            WaitingRoom.tenant_id == tenant_id
        ).first()

    async def get_entry(
        self,
        tenant_id: UUID,
        entry_id: UUID,
    ) -> Optional[WaitingRoomEntry]:
        """Get a waiting room entry."""
        return self.db.query(WaitingRoomEntry).filter(
            WaitingRoomEntry.id == entry_id,
            WaitingRoomEntry.tenant_id == tenant_id
        ).first()

    async def get_queue_status(
        self,
        tenant_id: UUID,
        room_id: UUID,
    ) -> Dict[str, Any]:
        """Get current queue status for a waiting room."""
        room = self.db.query(WaitingRoom).filter(
            WaitingRoom.id == room_id,
            WaitingRoom.tenant_id == tenant_id
        ).first()

        if not room:
            return {}

        waiting_entries = self.db.query(WaitingRoomEntry).filter(
            WaitingRoomEntry.waiting_room_id == room_id,
            WaitingRoomEntry.status.in_([
                WaitingStatus.CHECKED_IN,
                WaitingStatus.DEVICE_CHECK,
                WaitingStatus.READY
            ])
        ).all()

        return {
            "room_id": str(room_id),
            "is_open": room.is_open,
            "total_waiting": len(waiting_entries),
            "ready_count": sum(1 for e in waiting_entries if e.status == WaitingStatus.READY),
            "current_delay_minutes": room.current_delay_minutes,
            "entries": [
                {
                    "entry_id": str(e.id),
                    "position": e.queue_position,
                    "status": e.status.value,
                    "estimated_wait": e.estimated_wait_minutes,
                    "checked_in_at": e.checked_in_at.isoformat(),
                }
                for e in waiting_entries
            ],
        }


# ============================================================================
# PAYMENT SERVICE
# ============================================================================

class TelehealthPaymentService:
    """
    Service for processing telehealth payments.

    Handles copay collection, refunds, and payment tracking.
    """

    def __init__(self, db: Session):
        self.db = db

    async def create_payment(
        self,
        tenant_id: UUID,
        data: PaymentCreate,
    ) -> TelehealthPayment:
        """Create a payment record."""
        payment = TelehealthPayment(
            tenant_id=tenant_id,
            appointment_id=data.appointment_id,
            patient_id=data.patient_id,
            amount_cents=data.amount_cents,
            currency=data.currency,
            payment_method=data.payment_method,
        )

        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)

        return payment

    async def authorize_payment(
        self,
        tenant_id: UUID,
        payment_id: UUID,
        external_payment_id: str,
        card_last_four: Optional[str] = None,
        card_brand: Optional[str] = None,
    ) -> TelehealthPayment:
        """Mark payment as authorized."""
        payment = self.db.query(TelehealthPayment).filter(
            TelehealthPayment.id == payment_id,
            TelehealthPayment.tenant_id == tenant_id
        ).first()

        if not payment:
            raise ValueError(f"Payment not found: {payment_id}")

        payment.status = PaymentStatus.AUTHORIZED
        payment.authorized_at = datetime.now(timezone.utc)
        payment.external_payment_id = external_payment_id
        payment.card_last_four = card_last_four
        payment.card_brand = card_brand

        # Update appointment payment status
        if payment.appointment_id:
            appointment = self.db.query(TelehealthAppointment).filter(
                TelehealthAppointment.id == payment.appointment_id
            ).first()
            if appointment:
                appointment.payment_status = PaymentStatus.AUTHORIZED
                appointment.payment_id = external_payment_id

        self.db.commit()
        self.db.refresh(payment)

        return payment

    async def capture_payment(
        self,
        tenant_id: UUID,
        payment_id: UUID,
    ) -> TelehealthPayment:
        """Capture an authorized payment."""
        payment = self.db.query(TelehealthPayment).filter(
            TelehealthPayment.id == payment_id,
            TelehealthPayment.tenant_id == tenant_id
        ).first()

        if not payment:
            raise ValueError(f"Payment not found: {payment_id}")

        if payment.status != PaymentStatus.AUTHORIZED:
            raise ValueError("Payment must be authorized before capture")

        payment.status = PaymentStatus.CAPTURED
        payment.captured_at = datetime.now(timezone.utc)

        # Update appointment
        if payment.appointment_id:
            appointment = self.db.query(TelehealthAppointment).filter(
                TelehealthAppointment.id == payment.appointment_id
            ).first()
            if appointment:
                appointment.payment_status = PaymentStatus.CAPTURED

        self.db.commit()
        self.db.refresh(payment)

        return payment

    async def refund_payment(
        self,
        tenant_id: UUID,
        payment_id: UUID,
        amount_cents: Optional[int] = None,
        reason: str = "",
    ) -> TelehealthPayment:
        """Refund a payment."""
        payment = self.db.query(TelehealthPayment).filter(
            TelehealthPayment.id == payment_id,
            TelehealthPayment.tenant_id == tenant_id
        ).first()

        if not payment:
            raise ValueError(f"Payment not found: {payment_id}")

        if payment.status not in (PaymentStatus.AUTHORIZED, PaymentStatus.CAPTURED):
            raise ValueError("Payment cannot be refunded")

        payment.status = PaymentStatus.REFUNDED
        payment.refunded_at = datetime.now(timezone.utc)
        payment.refund_amount_cents = amount_cents or payment.amount_cents
        payment.refund_reason = reason

        # Update appointment
        if payment.appointment_id:
            appointment = self.db.query(TelehealthAppointment).filter(
                TelehealthAppointment.id == payment.appointment_id
            ).first()
            if appointment:
                appointment.payment_status = PaymentStatus.REFUNDED

        self.db.commit()
        self.db.refresh(payment)

        return payment

    async def get_payment(
        self,
        tenant_id: UUID,
        payment_id: UUID,
    ) -> Optional[TelehealthPayment]:
        """Get a payment by ID."""
        return self.db.query(TelehealthPayment).filter(
            TelehealthPayment.id == payment_id,
            TelehealthPayment.tenant_id == tenant_id
        ).first()


# ============================================================================
# ANALYTICS SERVICE
# ============================================================================

class TelehealthAnalyticsService:
    """
    Service for telehealth analytics and metrics.
    """

    def __init__(self, db: Session):
        self.db = db

    async def record_session_analytics(
        self,
        tenant_id: UUID,
        session_id: UUID,
        analytics: Dict[str, Any],
    ) -> SessionAnalytics:
        """Record analytics for a session."""
        record = SessionAnalytics(
            session_id=session_id,
            tenant_id=tenant_id,
            avg_latency_ms=analytics.get("avg_latency_ms"),
            avg_packet_loss_percent=analytics.get("avg_packet_loss_percent"),
            avg_jitter_ms=analytics.get("avg_jitter_ms"),
            avg_mos_score=analytics.get("avg_mos_score"),
            avg_video_bitrate_kbps=analytics.get("avg_video_bitrate_kbps"),
            video_freeze_count=analytics.get("video_freeze_count", 0),
            audio_dropout_count=analytics.get("audio_dropout_count", 0),
            connection_attempts=analytics.get("connection_attempts", 1),
            reconnection_count=analytics.get("reconnection_count", 0),
            technical_issues=analytics.get("technical_issues", []),
        )

        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        return record

    async def submit_satisfaction_survey(
        self,
        tenant_id: UUID,
        patient_id: UUID,
        data: SatisfactionSurveyCreate,
    ) -> PatientSatisfactionSurvey:
        """Submit a satisfaction survey."""
        survey = PatientSatisfactionSurvey(
            tenant_id=tenant_id,
            session_id=data.session_id,
            appointment_id=data.appointment_id,
            patient_id=patient_id,
            overall_rating=data.overall_rating,
            video_quality_rating=data.video_quality_rating,
            audio_quality_rating=data.audio_quality_rating,
            provider_rating=data.provider_rating,
            ease_of_use_rating=data.ease_of_use_rating,
            would_recommend=data.would_recommend,
            nps_score=data.nps_score,
            feedback_text=data.feedback_text,
            technical_issues_reported=data.technical_issues_reported or [],
            completed_at=datetime.now(timezone.utc),
        )

        self.db.add(survey)
        self.db.commit()
        self.db.refresh(survey)

        return survey

    async def get_telehealth_metrics(
        self,
        tenant_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Get telehealth utilization metrics."""
        query = self.db.query(TelehealthSession).filter(
            TelehealthSession.tenant_id == tenant_id
        )

        if start_date:
            query = query.filter(TelehealthSession.created_at >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            query = query.filter(TelehealthSession.created_at <= datetime.combine(end_date, datetime.max.time()))

        sessions = query.all()

        # Calculate metrics
        total = len(sessions)
        completed = sum(1 for s in sessions if s.status == SessionStatus.COMPLETED)
        no_shows = sum(1 for s in sessions if s.status == SessionStatus.NO_SHOW)
        tech_failures = sum(1 for s in sessions if s.status == SessionStatus.TECHNICAL_FAILURE)

        durations = [s.actual_duration_seconds for s in sessions if s.actual_duration_seconds]
        avg_duration = sum(durations) / len(durations) / 60 if durations else 0

        # Get satisfaction scores
        surveys = self.db.query(PatientSatisfactionSurvey).filter(
            PatientSatisfactionSurvey.tenant_id == tenant_id,
            PatientSatisfactionSurvey.overall_rating.isnot(None)
        ).all()

        avg_satisfaction = sum(s.overall_rating for s in surveys) / len(surveys) if surveys else 0

        # Get revenue
        payments = self.db.query(func.sum(TelehealthPayment.amount_cents)).filter(
            TelehealthPayment.tenant_id == tenant_id,
            TelehealthPayment.status == PaymentStatus.CAPTURED
        ).scalar() or 0

        return {
            "total_sessions": total,
            "completed_sessions": completed,
            "no_show_count": no_shows,
            "technical_failure_count": tech_failures,
            "avg_session_duration_minutes": round(avg_duration, 1),
            "avg_wait_time_minutes": 0,  # Would need waiting room data
            "avg_satisfaction_score": round(avg_satisfaction, 2),
            "total_revenue_cents": payments,
            "sessions_by_type": {},
            "sessions_by_status": {
                status.value: sum(1 for s in sessions if s.status == status)
                for status in SessionStatus
            },
        }
