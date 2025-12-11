"""
Session Recording Service

HIPAA-compliant telehealth recording:
- Session recording management
- Encrypted storage
- Retention policies
- Playback access control
- Audit logging

EPIC-007: US-007.1 Video Consultation Infrastructure (Recording)
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import logging
import hashlib

logger = logging.getLogger(__name__)


class RecordingStatus(str, Enum):
    """Recording status."""
    INITIALIZING = "initializing"
    RECORDING = "recording"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


class RecordingFormat(str, Enum):
    """Recording output formats."""
    MP4 = "mp4"
    WEBM = "webm"
    MKV = "mkv"


@dataclass
class RecordingConsent:
    """Recording consent record."""
    consent_id: str
    recording_id: str
    participant_id: str
    participant_name: str
    consented: bool = False
    consent_timestamp: Optional[datetime] = None
    ip_address: Optional[str] = None


@dataclass
class RecordingSegment:
    """A segment of a recording."""
    segment_id: str
    recording_id: str
    sequence_number: int
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    file_path: str
    file_size_bytes: int = 0


@dataclass
class SessionRecording:
    """A telehealth session recording."""
    recording_id: str
    session_id: str
    tenant_id: str

    # Status
    status: RecordingStatus = RecordingStatus.INITIALIZING
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: float = 0

    # Storage
    storage_bucket: str = ""
    storage_path: str = ""
    file_size_bytes: int = 0
    format: RecordingFormat = RecordingFormat.MP4

    # Encryption
    encrypted: bool = True
    encryption_key_id: Optional[str] = None

    # Consent
    consents: List[RecordingConsent] = field(default_factory=list)
    all_consented: bool = False

    # Participants recorded
    participants: List[str] = field(default_factory=list)

    # Segments (for long recordings)
    segments: List[RecordingSegment] = field(default_factory=list)

    # Quality
    video_resolution: str = "720p"
    video_bitrate_kbps: int = 1500
    audio_bitrate_kbps: int = 128

    # Retention
    retention_days: int = 365
    expires_at: Optional[datetime] = None
    legal_hold: bool = False

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class RecordingAccessLog:
    """Log of recording access."""
    access_id: str
    recording_id: str
    accessed_by: str
    access_type: str  # view, download, share
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class RecordingPlaybackToken:
    """Token for secure playback access."""
    token: str
    recording_id: str
    user_id: str
    expires_at: datetime
    allowed_actions: List[str] = field(default_factory=lambda: ["view"])


class RecordingService:
    """
    Telehealth session recording service.

    Handles:
    - Recording lifecycle
    - Consent management
    - Encrypted storage
    - Playback access control
    - Retention policies
    """

    def __init__(
        self,
        storage_bucket: str = "telehealth-recordings",
        default_retention_days: int = 365,
    ):
        self.storage_bucket = storage_bucket
        self.default_retention_days = default_retention_days

        self._recordings: Dict[str, SessionRecording] = {}
        self._access_logs: List[RecordingAccessLog] = []
        self._playback_tokens: Dict[str, RecordingPlaybackToken] = {}

    async def create_recording(
        self,
        session_id: str,
        tenant_id: str,
        participants: List[str],
        video_resolution: str = "720p",
        retention_days: Optional[int] = None,
    ) -> SessionRecording:
        """Create a new recording for a session."""
        recording_id = str(uuid4())

        recording = SessionRecording(
            recording_id=recording_id,
            session_id=session_id,
            tenant_id=tenant_id,
            participants=participants,
            video_resolution=video_resolution,
            retention_days=retention_days or self.default_retention_days,
            storage_bucket=self.storage_bucket,
            storage_path=f"{tenant_id}/{session_id}/{recording_id}",
        )

        # Generate encryption key reference
        recording.encryption_key_id = f"enc-{recording_id[:8]}"

        self._recordings[recording_id] = recording

        logger.info(f"Created recording: {recording_id} for session {session_id}")
        return recording

    async def record_consent(
        self,
        recording_id: str,
        participant_id: str,
        participant_name: str,
        consented: bool,
        ip_address: Optional[str] = None,
    ) -> RecordingConsent:
        """Record participant consent for recording."""
        recording = self._recordings.get(recording_id)
        if not recording:
            raise ValueError(f"Recording not found: {recording_id}")

        consent = RecordingConsent(
            consent_id=str(uuid4()),
            recording_id=recording_id,
            participant_id=participant_id,
            participant_name=participant_name,
            consented=consented,
            consent_timestamp=datetime.now(timezone.utc) if consented else None,
            ip_address=ip_address,
        )

        recording.consents.append(consent)

        # Check if all participants have consented
        recording.all_consented = all(
            c.consented for c in recording.consents
        ) and len(recording.consents) >= len(recording.participants)

        return consent

    async def start_recording(
        self,
        recording_id: str,
    ) -> SessionRecording:
        """Start the recording process."""
        recording = self._recordings.get(recording_id)
        if not recording:
            raise ValueError(f"Recording not found: {recording_id}")

        if not recording.all_consented:
            raise ValueError("All participants must consent before recording")

        recording.status = RecordingStatus.RECORDING
        recording.started_at = datetime.now(timezone.utc)

        logger.info(f"Started recording: {recording_id}")
        return recording

    async def add_segment(
        self,
        recording_id: str,
        file_path: str,
        duration_seconds: float,
        file_size_bytes: int,
    ) -> RecordingSegment:
        """Add a recording segment."""
        recording = self._recordings.get(recording_id)
        if not recording:
            raise ValueError(f"Recording not found: {recording_id}")

        sequence = len(recording.segments)

        segment = RecordingSegment(
            segment_id=str(uuid4()),
            recording_id=recording_id,
            sequence_number=sequence,
            start_time=recording.started_at + timedelta(seconds=recording.duration_seconds),
            end_time=recording.started_at + timedelta(seconds=recording.duration_seconds + duration_seconds),
            duration_seconds=duration_seconds,
            file_path=file_path,
            file_size_bytes=file_size_bytes,
        )

        recording.segments.append(segment)
        recording.duration_seconds += duration_seconds
        recording.file_size_bytes += file_size_bytes

        return segment

    async def stop_recording(
        self,
        recording_id: str,
    ) -> SessionRecording:
        """Stop recording and begin processing."""
        recording = self._recordings.get(recording_id)
        if not recording:
            raise ValueError(f"Recording not found: {recording_id}")

        recording.status = RecordingStatus.PROCESSING
        recording.ended_at = datetime.now(timezone.utc)

        # Calculate actual duration
        if recording.started_at:
            recording.duration_seconds = (recording.ended_at - recording.started_at).total_seconds()

        logger.info(f"Stopped recording: {recording_id}, duration: {recording.duration_seconds}s")
        return recording

    async def complete_processing(
        self,
        recording_id: str,
        final_file_path: str,
        final_file_size: int,
    ) -> SessionRecording:
        """Mark recording processing as complete."""
        recording = self._recordings.get(recording_id)
        if not recording:
            raise ValueError(f"Recording not found: {recording_id}")

        recording.status = RecordingStatus.COMPLETED
        recording.storage_path = final_file_path
        recording.file_size_bytes = final_file_size

        # Set expiration date
        recording.expires_at = datetime.now(timezone.utc) + timedelta(days=recording.retention_days)

        logger.info(f"Completed recording: {recording_id}")
        return recording

    async def fail_recording(
        self,
        recording_id: str,
        error: str,
    ) -> SessionRecording:
        """Mark recording as failed."""
        recording = self._recordings.get(recording_id)
        if not recording:
            raise ValueError(f"Recording not found: {recording_id}")

        recording.status = RecordingStatus.FAILED
        recording.metadata["error"] = error
        recording.ended_at = datetime.now(timezone.utc)

        logger.error(f"Recording failed: {recording_id} - {error}")
        return recording

    async def get_recording(
        self,
        recording_id: str,
    ) -> Optional[SessionRecording]:
        """Get a recording by ID."""
        return self._recordings.get(recording_id)

    async def get_session_recordings(
        self,
        session_id: str,
    ) -> List[SessionRecording]:
        """Get all recordings for a session."""
        return [
            r for r in self._recordings.values()
            if r.session_id == session_id and r.status != RecordingStatus.DELETED
        ]

    async def generate_playback_token(
        self,
        recording_id: str,
        user_id: str,
        allowed_actions: Optional[List[str]] = None,
        expires_in_minutes: int = 60,
    ) -> RecordingPlaybackToken:
        """Generate a secure token for playback access."""
        recording = self._recordings.get(recording_id)
        if not recording:
            raise ValueError(f"Recording not found: {recording_id}")

        if recording.status != RecordingStatus.COMPLETED:
            raise ValueError("Recording is not available for playback")

        # Generate token
        token_data = f"{recording_id}:{user_id}:{datetime.now(timezone.utc).isoformat()}"
        token = hashlib.sha256(token_data.encode()).hexdigest()[:32]

        playback_token = RecordingPlaybackToken(
            token=token,
            recording_id=recording_id,
            user_id=user_id,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes),
            allowed_actions=allowed_actions or ["view"],
        )

        self._playback_tokens[token] = playback_token

        # Log access
        await self._log_access(recording_id, user_id, "token_generated")

        return playback_token

    async def validate_playback_token(
        self,
        token: str,
        action: str = "view",
    ) -> Optional[SessionRecording]:
        """Validate a playback token and return the recording if valid."""
        playback_token = self._playback_tokens.get(token)

        if not playback_token:
            return None

        if playback_token.expires_at < datetime.now(timezone.utc):
            del self._playback_tokens[token]
            return None

        if action not in playback_token.allowed_actions:
            return None

        recording = self._recordings.get(playback_token.recording_id)

        # Log access
        if recording:
            await self._log_access(
                recording.recording_id,
                playback_token.user_id,
                action
            )

        return recording

    async def get_playback_url(
        self,
        recording_id: str,
        user_id: str,
    ) -> str:
        """Get a secure playback URL for a recording."""
        token = await self.generate_playback_token(recording_id, user_id)
        return f"/api/telehealth/recordings/{recording_id}/playback?token={token.token}"

    async def set_legal_hold(
        self,
        recording_id: str,
        hold: bool,
        reason: Optional[str] = None,
    ) -> SessionRecording:
        """Set or remove legal hold on a recording."""
        recording = self._recordings.get(recording_id)
        if not recording:
            raise ValueError(f"Recording not found: {recording_id}")

        recording.legal_hold = hold

        if hold:
            recording.expires_at = None  # Remove expiration
            recording.metadata["legal_hold_reason"] = reason
            recording.metadata["legal_hold_date"] = datetime.now(timezone.utc).isoformat()
        else:
            # Restore expiration
            created = recording.created_at
            recording.expires_at = created + timedelta(days=recording.retention_days)
            recording.metadata.pop("legal_hold_reason", None)

        logger.info(f"Legal hold {'set' if hold else 'removed'} on recording: {recording_id}")
        return recording

    async def delete_recording(
        self,
        recording_id: str,
        deleted_by: str,
        reason: str = "",
    ) -> bool:
        """Delete a recording (soft delete)."""
        recording = self._recordings.get(recording_id)
        if not recording:
            return False

        if recording.legal_hold:
            raise ValueError("Cannot delete recording under legal hold")

        recording.status = RecordingStatus.DELETED
        recording.metadata["deleted_by"] = deleted_by
        recording.metadata["deleted_at"] = datetime.now(timezone.utc).isoformat()
        recording.metadata["deletion_reason"] = reason

        # Log deletion
        await self._log_access(recording_id, deleted_by, "delete")

        logger.info(f"Deleted recording: {recording_id}")
        return True

    async def get_expired_recordings(self) -> List[SessionRecording]:
        """Get recordings that have passed retention period."""
        now = datetime.now(timezone.utc)

        return [
            r for r in self._recordings.values()
            if r.expires_at and r.expires_at < now
            and r.status != RecordingStatus.DELETED
            and not r.legal_hold
        ]

    async def _log_access(
        self,
        recording_id: str,
        user_id: str,
        access_type: str,
        ip_address: Optional[str] = None,
    ):
        """Log recording access for audit."""
        log = RecordingAccessLog(
            access_id=str(uuid4()),
            recording_id=recording_id,
            accessed_by=user_id,
            access_type=access_type,
            ip_address=ip_address,
        )
        self._access_logs.append(log)

    async def get_access_logs(
        self,
        recording_id: str,
    ) -> List[RecordingAccessLog]:
        """Get access logs for a recording."""
        return [
            log for log in self._access_logs
            if log.recording_id == recording_id
        ]

    async def get_tenant_recordings(
        self,
        tenant_id: str,
        status: Optional[RecordingStatus] = None,
        limit: int = 100,
    ) -> List[SessionRecording]:
        """Get recordings for a tenant."""
        recordings = [
            r for r in self._recordings.values()
            if r.tenant_id == tenant_id
        ]

        if status:
            recordings = [r for r in recordings if r.status == status]

        # Sort by creation date descending
        recordings.sort(key=lambda r: r.created_at, reverse=True)

        return recordings[:limit]


# Global recording service instance
recording_service = RecordingService()
