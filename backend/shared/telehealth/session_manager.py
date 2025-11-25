"""
Telehealth Session Management

Core session management for video consultations:
- Session lifecycle management
- Participant handling
- Room creation and management
- WebRTC/LiveKit integration
- End-to-end encryption

EPIC-007: US-007.1 Video Consultation Infrastructure
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import asyncio
import logging
import secrets
import hashlib

logger = logging.getLogger(__name__)


class SessionStatus(str, Enum):
    """Telehealth session status."""
    SCHEDULED = "scheduled"
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    TECHNICAL_FAILURE = "technical_failure"


class ParticipantRole(str, Enum):
    """Participant roles in a telehealth session."""
    PATIENT = "patient"
    PROVIDER = "provider"
    INTERPRETER = "interpreter"
    CAREGIVER = "caregiver"
    OBSERVER = "observer"
    TECH_SUPPORT = "tech_support"


class ParticipantStatus(str, Enum):
    """Participant connection status."""
    INVITED = "invited"
    WAITING = "waiting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"


@dataclass
class DeviceCapabilities:
    """Device capabilities for a participant."""
    has_video: bool = True
    has_audio: bool = True
    has_screen_share: bool = False
    video_resolution: str = "720p"
    browser: Optional[str] = None
    os: Optional[str] = None
    is_mobile: bool = False


@dataclass
class ConnectionQuality:
    """Connection quality metrics."""
    latency_ms: float = 0
    packet_loss_percent: float = 0
    jitter_ms: float = 0
    bandwidth_kbps: int = 0
    video_bitrate_kbps: int = 0
    audio_bitrate_kbps: int = 0
    quality_score: float = 5.0  # 1-5 MOS score


@dataclass
class Participant:
    """Participant in a telehealth session."""
    participant_id: str
    session_id: str
    user_id: str
    role: ParticipantRole

    # Identity
    display_name: str = ""
    avatar_url: Optional[str] = None

    # Connection
    status: ParticipantStatus = ParticipantStatus.INVITED
    connection_id: Optional[str] = None
    device: Optional[DeviceCapabilities] = None
    connection_quality: Optional[ConnectionQuality] = None

    # Media state
    video_enabled: bool = True
    audio_enabled: bool = True
    screen_sharing: bool = False

    # Timestamps
    invited_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    joined_at: Optional[datetime] = None
    left_at: Optional[datetime] = None

    # Permissions
    can_share_screen: bool = True
    can_record: bool = False
    can_admit_participants: bool = False


@dataclass
class SessionEncryption:
    """Session encryption configuration."""
    encryption_key: str
    key_id: str
    algorithm: str = "AES-256-GCM"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class TelehealthSession:
    """A telehealth video consultation session."""
    session_id: str
    tenant_id: str

    # Appointment reference
    appointment_id: Optional[str] = None
    encounter_id: Optional[str] = None

    # Room configuration
    room_name: str = ""
    room_token: Optional[str] = None

    # Participants
    participants: Dict[str, Participant] = field(default_factory=dict)
    max_participants: int = 10

    # Session details
    session_type: str = "video_visit"  # video_visit, group_therapy, interpreter
    scheduled_duration_minutes: int = 30

    # Status
    status: SessionStatus = SessionStatus.SCHEDULED
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

    # Recording
    is_recording: bool = False
    recording_id: Optional[str] = None
    consent_obtained: bool = False

    # Security
    encryption: Optional[SessionEncryption] = None
    join_password: Optional[str] = None
    waiting_room_enabled: bool = True

    # Features
    screen_sharing_enabled: bool = True
    chat_enabled: bool = True
    file_sharing_enabled: bool = True
    whiteboard_enabled: bool = False

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SessionEvent:
    """Event that occurred during a session."""
    event_id: str
    session_id: str
    event_type: str
    timestamp: datetime
    participant_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)


class SessionManager:
    """
    Manages telehealth video sessions.

    Integrates with WebRTC/LiveKit for:
    - Room management
    - Participant handling
    - Media control
    - Recording
    """

    def __init__(
        self,
        livekit_url: Optional[str] = None,
        livekit_api_key: Optional[str] = None,
        livekit_api_secret: Optional[str] = None,
    ):
        self._sessions: Dict[str, TelehealthSession] = {}
        self._room_to_session: Dict[str, str] = {}  # room_name -> session_id

        # LiveKit configuration
        self.livekit_url = livekit_url
        self.livekit_api_key = livekit_api_key
        self.livekit_api_secret = livekit_api_secret

        # Event handlers
        self._event_handlers: Dict[str, List[Callable]] = {}

        # Event log
        self._events: List[SessionEvent] = []

    async def create_session(
        self,
        tenant_id: str,
        session_type: str = "video_visit",
        appointment_id: Optional[str] = None,
        scheduled_duration_minutes: int = 30,
        waiting_room_enabled: bool = True,
        max_participants: int = 10,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TelehealthSession:
        """Create a new telehealth session."""
        session_id = str(uuid4())
        room_name = f"telehealth-{session_id[:8]}"

        # Generate encryption key
        encryption = SessionEncryption(
            encryption_key=secrets.token_hex(32),
            key_id=str(uuid4()),
        )

        session = TelehealthSession(
            session_id=session_id,
            tenant_id=tenant_id,
            room_name=room_name,
            session_type=session_type,
            appointment_id=appointment_id,
            scheduled_duration_minutes=scheduled_duration_minutes,
            waiting_room_enabled=waiting_room_enabled,
            max_participants=max_participants,
            encryption=encryption,
            metadata=metadata or {},
        )

        self._sessions[session_id] = session
        self._room_to_session[room_name] = session_id

        await self._log_event(session_id, "session_created", {
            "session_type": session_type,
            "appointment_id": appointment_id,
        })

        logger.info(f"Created telehealth session: {session_id}")
        return session

    async def add_participant(
        self,
        session_id: str,
        user_id: str,
        role: ParticipantRole,
        display_name: str,
        avatar_url: Optional[str] = None,
    ) -> Participant:
        """Add a participant to a session."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        if len(session.participants) >= session.max_participants:
            raise ValueError("Session is at maximum capacity")

        participant = Participant(
            participant_id=str(uuid4()),
            session_id=session_id,
            user_id=user_id,
            role=role,
            display_name=display_name,
            avatar_url=avatar_url,
        )

        # Set permissions based on role
        if role == ParticipantRole.PROVIDER:
            participant.can_record = True
            participant.can_admit_participants = True
        elif role == ParticipantRole.PATIENT:
            participant.can_share_screen = True

        session.participants[participant.participant_id] = participant

        await self._log_event(session_id, "participant_added", {
            "participant_id": participant.participant_id,
            "user_id": user_id,
            "role": role.value,
        })

        return participant

    async def generate_join_token(
        self,
        session_id: str,
        participant_id: str,
    ) -> str:
        """Generate a token for joining the video room."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        participant = session.participants.get(participant_id)
        if not participant:
            raise ValueError(f"Participant not found: {participant_id}")

        # Generate LiveKit access token
        if self.livekit_api_key and self.livekit_api_secret:
            token = await self._generate_livekit_token(session, participant)
        else:
            # Fallback to simple token
            token = self._generate_simple_token(session, participant)

        return token

    async def _generate_livekit_token(
        self,
        session: TelehealthSession,
        participant: Participant,
    ) -> str:
        """Generate LiveKit access token."""
        # This would use the livekit-server-sdk
        # For now, returning a placeholder
        import jwt
        import time

        payload = {
            "iss": self.livekit_api_key,
            "sub": participant.participant_id,
            "exp": int(time.time()) + 3600,
            "nbf": int(time.time()),
            "video": {
                "roomCreate": participant.role == ParticipantRole.PROVIDER,
                "roomJoin": True,
                "room": session.room_name,
                "canPublish": True,
                "canSubscribe": True,
                "canPublishData": True,
            },
            "name": participant.display_name,
            "metadata": json.dumps({
                "role": participant.role.value,
                "user_id": participant.user_id,
            }),
        }

        return jwt.encode(payload, self.livekit_api_secret, algorithm="HS256")

    def _generate_simple_token(
        self,
        session: TelehealthSession,
        participant: Participant,
    ) -> str:
        """Generate a simple join token for non-LiveKit setup."""
        import json
        token_data = {
            "session_id": session.session_id,
            "participant_id": participant.participant_id,
            "room_name": session.room_name,
            "role": participant.role.value,
            "exp": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
        }
        # Simple base64 encoding (use proper JWT in production)
        import base64
        return base64.urlsafe_b64encode(json.dumps(token_data).encode()).decode()

    async def participant_joined(
        self,
        session_id: str,
        participant_id: str,
        connection_id: str,
        device: Optional[DeviceCapabilities] = None,
    ) -> Participant:
        """Handle participant joining the session."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        participant = session.participants.get(participant_id)
        if not participant:
            raise ValueError(f"Participant not found: {participant_id}")

        participant.status = ParticipantStatus.CONNECTED
        participant.connection_id = connection_id
        participant.device = device
        participant.joined_at = datetime.now(timezone.utc)

        # Start session if provider joins
        if participant.role == ParticipantRole.PROVIDER and session.status == SessionStatus.SCHEDULED:
            session.status = SessionStatus.WAITING

        # Check if both patient and provider are connected
        roles_connected = {
            p.role for p in session.participants.values()
            if p.status == ParticipantStatus.CONNECTED
        }

        if ParticipantRole.PATIENT in roles_connected and ParticipantRole.PROVIDER in roles_connected:
            if session.status in (SessionStatus.SCHEDULED, SessionStatus.WAITING):
                session.status = SessionStatus.IN_PROGRESS
                session.started_at = datetime.now(timezone.utc)

        await self._log_event(session_id, "participant_joined", {
            "participant_id": participant_id,
            "connection_id": connection_id,
        })

        return participant

    async def participant_left(
        self,
        session_id: str,
        participant_id: str,
    ) -> Participant:
        """Handle participant leaving the session."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        participant = session.participants.get(participant_id)
        if not participant:
            raise ValueError(f"Participant not found: {participant_id}")

        participant.status = ParticipantStatus.DISCONNECTED
        participant.left_at = datetime.now(timezone.utc)
        participant.connection_id = None

        await self._log_event(session_id, "participant_left", {
            "participant_id": participant_id,
        })

        # Check if session should end
        connected = [
            p for p in session.participants.values()
            if p.status == ParticipantStatus.CONNECTED
        ]

        if not connected and session.status == SessionStatus.IN_PROGRESS:
            # All participants left - end session after grace period
            asyncio.create_task(self._check_session_end(session_id, delay_seconds=60))

        return participant

    async def _check_session_end(self, session_id: str, delay_seconds: int = 60):
        """Check if session should end after delay."""
        await asyncio.sleep(delay_seconds)

        session = self._sessions.get(session_id)
        if not session:
            return

        connected = [
            p for p in session.participants.values()
            if p.status == ParticipantStatus.CONNECTED
        ]

        if not connected and session.status == SessionStatus.IN_PROGRESS:
            await self.end_session(session_id)

    async def end_session(
        self,
        session_id: str,
        reason: str = "completed",
    ) -> TelehealthSession:
        """End a telehealth session."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Determine final status
        if session.status == SessionStatus.WAITING:
            # No one showed up
            session.status = SessionStatus.NO_SHOW
        elif reason == "technical_failure":
            session.status = SessionStatus.TECHNICAL_FAILURE
        elif reason == "cancelled":
            session.status = SessionStatus.CANCELLED
        else:
            session.status = SessionStatus.COMPLETED

        session.ended_at = datetime.now(timezone.utc)

        # Disconnect all participants
        for participant in session.participants.values():
            if participant.status == ParticipantStatus.CONNECTED:
                participant.status = ParticipantStatus.DISCONNECTED
                participant.left_at = datetime.now(timezone.utc)

        await self._log_event(session_id, "session_ended", {
            "status": session.status.value,
            "reason": reason,
            "duration_seconds": self._calculate_duration(session),
        })

        logger.info(f"Ended telehealth session: {session_id}")
        return session

    def _calculate_duration(self, session: TelehealthSession) -> int:
        """Calculate session duration in seconds."""
        if not session.started_at:
            return 0

        end_time = session.ended_at or datetime.now(timezone.utc)
        return int((end_time - session.started_at).total_seconds())

    async def update_media_state(
        self,
        session_id: str,
        participant_id: str,
        video_enabled: Optional[bool] = None,
        audio_enabled: Optional[bool] = None,
        screen_sharing: Optional[bool] = None,
    ) -> Participant:
        """Update participant media state."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        participant = session.participants.get(participant_id)
        if not participant:
            raise ValueError(f"Participant not found: {participant_id}")

        if video_enabled is not None:
            participant.video_enabled = video_enabled
        if audio_enabled is not None:
            participant.audio_enabled = audio_enabled
        if screen_sharing is not None:
            if screen_sharing and not participant.can_share_screen:
                raise ValueError("Participant does not have screen sharing permission")
            participant.screen_sharing = screen_sharing

        await self._log_event(session_id, "media_state_changed", {
            "participant_id": participant_id,
            "video_enabled": participant.video_enabled,
            "audio_enabled": participant.audio_enabled,
            "screen_sharing": participant.screen_sharing,
        })

        return participant

    async def update_connection_quality(
        self,
        session_id: str,
        participant_id: str,
        quality: ConnectionQuality,
    ):
        """Update participant connection quality metrics."""
        session = self._sessions.get(session_id)
        if not session:
            return

        participant = session.participants.get(participant_id)
        if not participant:
            return

        participant.connection_quality = quality

        # Log if quality is poor
        if quality.quality_score < 3.0:
            await self._log_event(session_id, "poor_connection_quality", {
                "participant_id": participant_id,
                "quality_score": quality.quality_score,
                "packet_loss": quality.packet_loss_percent,
            })

    async def start_recording(
        self,
        session_id: str,
        participant_id: str,
    ) -> str:
        """Start recording a session."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        participant = session.participants.get(participant_id)
        if not participant or not participant.can_record:
            raise ValueError("Participant cannot start recording")

        if not session.consent_obtained:
            raise ValueError("Recording consent not obtained")

        if session.is_recording:
            raise ValueError("Session is already being recorded")

        recording_id = str(uuid4())
        session.is_recording = True
        session.recording_id = recording_id

        await self._log_event(session_id, "recording_started", {
            "recording_id": recording_id,
            "started_by": participant_id,
        })

        return recording_id

    async def stop_recording(
        self,
        session_id: str,
    ) -> Optional[str]:
        """Stop recording a session."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        if not session.is_recording:
            return None

        recording_id = session.recording_id
        session.is_recording = False

        await self._log_event(session_id, "recording_stopped", {
            "recording_id": recording_id,
        })

        return recording_id

    async def get_session(self, session_id: str) -> Optional[TelehealthSession]:
        """Get a session by ID."""
        return self._sessions.get(session_id)

    async def get_session_by_room(self, room_name: str) -> Optional[TelehealthSession]:
        """Get a session by room name."""
        session_id = self._room_to_session.get(room_name)
        if session_id:
            return self._sessions.get(session_id)
        return None

    async def get_active_sessions(
        self,
        tenant_id: str,
    ) -> List[TelehealthSession]:
        """Get all active sessions for a tenant."""
        return [
            s for s in self._sessions.values()
            if s.tenant_id == tenant_id
            and s.status in (SessionStatus.SCHEDULED, SessionStatus.WAITING, SessionStatus.IN_PROGRESS)
        ]

    async def _log_event(
        self,
        session_id: str,
        event_type: str,
        data: Dict[str, Any],
        participant_id: Optional[str] = None,
    ):
        """Log a session event."""
        event = SessionEvent(
            event_id=str(uuid4()),
            session_id=session_id,
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            participant_id=participant_id,
            data=data,
        )
        self._events.append(event)

        # Call event handlers
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")

    def on_event(self, event_type: str, handler: Callable):
        """Register an event handler."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    async def get_session_events(
        self,
        session_id: str,
    ) -> List[SessionEvent]:
        """Get all events for a session."""
        return [e for e in self._events if e.session_id == session_id]


# Import for token generation
import json
