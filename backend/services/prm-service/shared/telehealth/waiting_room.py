"""
Virtual Waiting Room

Manages the pre-call experience:
- Queue management
- Device checks
- Pre-visit forms
- Staff chat
- Wait time estimation

EPIC-007: US-007.2 Virtual Waiting Room
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import asyncio
import logging

logger = logging.getLogger(__name__)


class WaitingStatus(str, Enum):
    """Status of a waiting room entry."""
    CHECKED_IN = "checked_in"
    DEVICE_CHECK = "device_check"
    READY = "ready"
    IN_CALL = "in_call"
    DEPARTED = "departed"
    NO_SHOW = "no_show"


class DeviceCheckStatus(str, Enum):
    """Device check status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"


@dataclass
class DeviceCheckResult:
    """Results of pre-call device check."""
    check_id: str

    # Camera check
    camera_available: bool = False
    camera_working: bool = False
    camera_device: Optional[str] = None

    # Microphone check
    microphone_available: bool = False
    microphone_working: bool = False
    microphone_device: Optional[str] = None

    # Speaker check
    speaker_available: bool = False
    speaker_working: bool = False
    speaker_device: Optional[str] = None

    # Network check
    connection_speed_mbps: float = 0
    latency_ms: float = 0
    jitter_ms: float = 0
    packet_loss_percent: float = 0

    # Browser compatibility
    browser_name: str = ""
    browser_version: str = ""
    webrtc_supported: bool = False

    # Overall
    status: DeviceCheckStatus = DeviceCheckStatus.NOT_STARTED
    issues: List[str] = field(default_factory=list)
    checked_at: Optional[datetime] = None


@dataclass
class PreVisitForm:
    """Pre-visit form submission."""
    form_id: str
    form_type: str  # intake, consent, symptom_checker
    patient_id: str
    session_id: str

    questions: List[Dict[str, Any]] = field(default_factory=list)
    responses: Dict[str, Any] = field(default_factory=dict)

    status: str = "pending"  # pending, in_progress, completed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class ChatMessage:
    """Chat message in waiting room."""
    message_id: str
    session_id: str
    sender_id: str
    sender_type: str  # patient, staff
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    read: bool = False


@dataclass
class WaitingRoomEntry:
    """Entry for a patient in the waiting room."""
    entry_id: str
    session_id: str
    patient_id: str
    tenant_id: str

    # Status
    status: WaitingStatus = WaitingStatus.CHECKED_IN
    priority: int = 0  # Higher = more urgent

    # Check-in
    checked_in_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    scheduled_time: Optional[datetime] = None

    # Provider
    provider_id: Optional[str] = None
    provider_name: Optional[str] = None
    provider_available: bool = False

    # Device check
    device_check: Optional[DeviceCheckResult] = None

    # Forms
    forms: List[PreVisitForm] = field(default_factory=list)
    forms_completed: bool = False

    # Queue
    queue_position: int = 0
    estimated_wait_minutes: int = 0

    # Chat
    messages: List[ChatMessage] = field(default_factory=list)
    unread_messages: int = 0

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WaitingRoom:
    """A virtual waiting room for a provider or location."""
    room_id: str
    tenant_id: str

    # Identity
    name: str = ""
    location_id: Optional[str] = None
    provider_id: Optional[str] = None

    # Entries
    entries: Dict[str, WaitingRoomEntry] = field(default_factory=dict)

    # Configuration
    max_wait_minutes: int = 60
    auto_notify_minutes: int = 5  # Notify when wait time < this
    device_check_required: bool = True
    forms_required: bool = True

    # Status
    is_open: bool = True
    current_delay_minutes: int = 0


class WaitingRoomService:
    """
    Virtual waiting room management.

    Handles:
    - Check-in process
    - Queue management
    - Device checks
    - Pre-visit forms
    - Staff-patient chat
    - Wait time estimation
    """

    def __init__(self):
        self._waiting_rooms: Dict[str, WaitingRoom] = {}
        self._entries_by_patient: Dict[str, str] = {}  # patient_id -> entry_id
        self._notification_handlers: List[Callable] = []

        # Average service times for estimation
        self._service_times: Dict[str, List[int]] = {}  # provider_id -> list of durations

    async def create_waiting_room(
        self,
        tenant_id: str,
        name: str,
        provider_id: Optional[str] = None,
        location_id: Optional[str] = None,
        device_check_required: bool = True,
        forms_required: bool = True,
    ) -> WaitingRoom:
        """Create a new waiting room."""
        room = WaitingRoom(
            room_id=str(uuid4()),
            tenant_id=tenant_id,
            name=name,
            provider_id=provider_id,
            location_id=location_id,
            device_check_required=device_check_required,
            forms_required=forms_required,
        )

        self._waiting_rooms[room.room_id] = room
        logger.info(f"Created waiting room: {room.room_id}")

        return room

    async def check_in(
        self,
        room_id: str,
        session_id: str,
        patient_id: str,
        provider_id: Optional[str] = None,
        scheduled_time: Optional[datetime] = None,
        priority: int = 0,
        required_forms: Optional[List[str]] = None,
    ) -> WaitingRoomEntry:
        """Check a patient into the waiting room."""
        room = self._waiting_rooms.get(room_id)
        if not room:
            raise ValueError(f"Waiting room not found: {room_id}")

        if not room.is_open:
            raise ValueError("Waiting room is currently closed")

        entry = WaitingRoomEntry(
            entry_id=str(uuid4()),
            session_id=session_id,
            patient_id=patient_id,
            tenant_id=room.tenant_id,
            provider_id=provider_id or room.provider_id,
            scheduled_time=scheduled_time,
            priority=priority,
        )

        # Create pre-visit forms
        if required_forms:
            for form_type in required_forms:
                form = PreVisitForm(
                    form_id=str(uuid4()),
                    form_type=form_type,
                    patient_id=patient_id,
                    session_id=session_id,
                )
                entry.forms.append(form)

        # Add to room
        room.entries[entry.entry_id] = entry
        self._entries_by_patient[patient_id] = entry.entry_id

        # Update queue positions
        await self._update_queue_positions(room_id)

        logger.info(f"Patient {patient_id} checked into waiting room {room_id}")
        return entry

    async def start_device_check(
        self,
        entry_id: str,
    ) -> DeviceCheckResult:
        """Start device check for a waiting room entry."""
        entry = await self._get_entry(entry_id)
        if not entry:
            raise ValueError(f"Entry not found: {entry_id}")

        check = DeviceCheckResult(
            check_id=str(uuid4()),
            status=DeviceCheckStatus.IN_PROGRESS,
        )

        entry.device_check = check
        entry.status = WaitingStatus.DEVICE_CHECK

        return check

    async def complete_device_check(
        self,
        entry_id: str,
        camera_available: bool,
        camera_working: bool,
        microphone_available: bool,
        microphone_working: bool,
        speaker_available: bool,
        speaker_working: bool,
        connection_speed_mbps: float,
        latency_ms: float,
        browser_name: str,
        webrtc_supported: bool,
    ) -> DeviceCheckResult:
        """Complete device check with results."""
        entry = await self._get_entry(entry_id)
        if not entry or not entry.device_check:
            raise ValueError(f"Entry or device check not found: {entry_id}")

        check = entry.device_check
        check.camera_available = camera_available
        check.camera_working = camera_working
        check.microphone_available = microphone_available
        check.microphone_working = microphone_working
        check.speaker_available = speaker_available
        check.speaker_working = speaker_working
        check.connection_speed_mbps = connection_speed_mbps
        check.latency_ms = latency_ms
        check.browser_name = browser_name
        check.webrtc_supported = webrtc_supported
        check.checked_at = datetime.now(timezone.utc)

        # Determine issues
        issues = []
        if not camera_working:
            issues.append("Camera not working")
        if not microphone_working:
            issues.append("Microphone not working")
        if not speaker_working:
            issues.append("Speaker not working")
        if connection_speed_mbps < 1.0:
            issues.append("Internet connection too slow")
        if latency_ms > 300:
            issues.append("High network latency")
        if not webrtc_supported:
            issues.append("Browser does not support video calls")

        check.issues = issues
        check.status = DeviceCheckStatus.PASSED if not issues else DeviceCheckStatus.FAILED

        # Update entry status
        if check.status == DeviceCheckStatus.PASSED:
            await self._check_ready_status(entry)

        return check

    async def submit_form_response(
        self,
        entry_id: str,
        form_id: str,
        responses: Dict[str, Any],
    ) -> PreVisitForm:
        """Submit responses for a pre-visit form."""
        entry = await self._get_entry(entry_id)
        if not entry:
            raise ValueError(f"Entry not found: {entry_id}")

        form = None
        for f in entry.forms:
            if f.form_id == form_id:
                form = f
                break

        if not form:
            raise ValueError(f"Form not found: {form_id}")

        form.responses = responses
        form.status = "completed"
        form.completed_at = datetime.now(timezone.utc)

        # Check if all forms are complete
        entry.forms_completed = all(f.status == "completed" for f in entry.forms)

        # Update entry status
        await self._check_ready_status(entry)

        return form

    async def _check_ready_status(self, entry: WaitingRoomEntry):
        """Check if entry is ready to join call."""
        room = await self._get_room_for_entry(entry)

        # Check device requirements
        device_ok = True
        if room and room.device_check_required:
            device_ok = entry.device_check and entry.device_check.status == DeviceCheckStatus.PASSED

        # Check form requirements
        forms_ok = True
        if room and room.forms_required:
            forms_ok = entry.forms_completed or len(entry.forms) == 0

        if device_ok and forms_ok:
            entry.status = WaitingStatus.READY
            await self._notify_ready(entry)

    async def _notify_ready(self, entry: WaitingRoomEntry):
        """Notify that patient is ready."""
        for handler in self._notification_handlers:
            try:
                await handler("patient_ready", entry)
            except Exception as e:
                logger.error(f"Notification handler error: {e}")

    async def send_chat_message(
        self,
        entry_id: str,
        sender_id: str,
        sender_type: str,
        content: str,
    ) -> ChatMessage:
        """Send a chat message in the waiting room."""
        entry = await self._get_entry(entry_id)
        if not entry:
            raise ValueError(f"Entry not found: {entry_id}")

        message = ChatMessage(
            message_id=str(uuid4()),
            session_id=entry.session_id,
            sender_id=sender_id,
            sender_type=sender_type,
            content=content,
        )

        entry.messages.append(message)

        if sender_type == "staff":
            entry.unread_messages += 1

        return message

    async def mark_messages_read(
        self,
        entry_id: str,
        reader_type: str,
    ):
        """Mark messages as read."""
        entry = await self._get_entry(entry_id)
        if not entry:
            return

        for message in entry.messages:
            if not message.read and message.sender_type != reader_type:
                message.read = True

        if reader_type == "patient":
            entry.unread_messages = 0

    async def admit_to_call(
        self,
        entry_id: str,
    ) -> WaitingRoomEntry:
        """Admit patient from waiting room to the call."""
        entry = await self._get_entry(entry_id)
        if not entry:
            raise ValueError(f"Entry not found: {entry_id}")

        entry.status = WaitingStatus.IN_CALL

        # Update queue for remaining entries
        room = await self._get_room_for_entry(entry)
        if room:
            await self._update_queue_positions(room.room_id)

        logger.info(f"Admitted entry {entry_id} to call")
        return entry

    async def depart(
        self,
        entry_id: str,
        reason: str = "completed",
    ) -> WaitingRoomEntry:
        """Remove patient from waiting room."""
        entry = await self._get_entry(entry_id)
        if not entry:
            raise ValueError(f"Entry not found: {entry_id}")

        if reason == "no_show":
            entry.status = WaitingStatus.NO_SHOW
        else:
            entry.status = WaitingStatus.DEPARTED

        # Remove from patient lookup
        self._entries_by_patient.pop(entry.patient_id, None)

        # Update queue
        room = await self._get_room_for_entry(entry)
        if room:
            await self._update_queue_positions(room.room_id)

        return entry

    async def _update_queue_positions(self, room_id: str):
        """Update queue positions for all entries in a room."""
        room = self._waiting_rooms.get(room_id)
        if not room:
            return

        # Get waiting entries sorted by priority and check-in time
        waiting = [
            e for e in room.entries.values()
            if e.status in (WaitingStatus.CHECKED_IN, WaitingStatus.DEVICE_CHECK, WaitingStatus.READY)
        ]

        # Sort: higher priority first, then earlier check-in
        waiting.sort(key=lambda e: (-e.priority, e.checked_in_at))

        # Update positions and estimates
        for i, entry in enumerate(waiting):
            entry.queue_position = i + 1
            entry.estimated_wait_minutes = await self._estimate_wait_time(
                room, entry, i + 1
            )

    async def _estimate_wait_time(
        self,
        room: WaitingRoom,
        entry: WaitingRoomEntry,
        position: int,
    ) -> int:
        """Estimate wait time for an entry."""
        # Get average service time for provider
        provider_id = entry.provider_id or room.provider_id
        avg_service_time = 15  # Default 15 minutes

        if provider_id and provider_id in self._service_times:
            times = self._service_times[provider_id]
            if times:
                avg_service_time = sum(times) / len(times)

        # Estimate based on position
        estimated = (position - 1) * avg_service_time

        # Add current delay
        estimated += room.current_delay_minutes

        # Consider scheduled time
        if entry.scheduled_time:
            now = datetime.now(timezone.utc)
            if entry.scheduled_time > now:
                # If scheduled for later, use that
                minutes_until = (entry.scheduled_time - now).total_seconds() / 60
                estimated = max(estimated, int(minutes_until))

        return int(estimated)

    async def record_service_time(
        self,
        provider_id: str,
        duration_minutes: int,
    ):
        """Record a service time for wait time estimation."""
        if provider_id not in self._service_times:
            self._service_times[provider_id] = []

        self._service_times[provider_id].append(duration_minutes)

        # Keep only last 50 times
        if len(self._service_times[provider_id]) > 50:
            self._service_times[provider_id] = self._service_times[provider_id][-50:]

    async def get_entry(
        self,
        entry_id: str,
    ) -> Optional[WaitingRoomEntry]:
        """Get a waiting room entry."""
        return await self._get_entry(entry_id)

    async def _get_entry(self, entry_id: str) -> Optional[WaitingRoomEntry]:
        """Internal method to get entry from any room."""
        for room in self._waiting_rooms.values():
            if entry_id in room.entries:
                return room.entries[entry_id]
        return None

    async def _get_room_for_entry(self, entry: WaitingRoomEntry) -> Optional[WaitingRoom]:
        """Get the room containing an entry."""
        for room in self._waiting_rooms.values():
            if entry.entry_id in room.entries:
                return room
        return None

    async def get_entry_by_patient(
        self,
        patient_id: str,
    ) -> Optional[WaitingRoomEntry]:
        """Get active entry for a patient."""
        entry_id = self._entries_by_patient.get(patient_id)
        if entry_id:
            return await self._get_entry(entry_id)
        return None

    async def get_waiting_room(
        self,
        room_id: str,
    ) -> Optional[WaitingRoom]:
        """Get a waiting room."""
        return self._waiting_rooms.get(room_id)

    async def get_provider_waiting_rooms(
        self,
        tenant_id: str,
        provider_id: str,
    ) -> List[WaitingRoom]:
        """Get waiting rooms for a provider."""
        return [
            r for r in self._waiting_rooms.values()
            if r.tenant_id == tenant_id and r.provider_id == provider_id
        ]

    async def get_queue_status(
        self,
        room_id: str,
    ) -> Dict[str, Any]:
        """Get current queue status for a waiting room."""
        room = self._waiting_rooms.get(room_id)
        if not room:
            return {}

        waiting_entries = [
            e for e in room.entries.values()
            if e.status in (WaitingStatus.CHECKED_IN, WaitingStatus.DEVICE_CHECK, WaitingStatus.READY)
        ]

        return {
            "room_id": room_id,
            "is_open": room.is_open,
            "total_waiting": len(waiting_entries),
            "ready_count": sum(1 for e in waiting_entries if e.status == WaitingStatus.READY),
            "current_delay_minutes": room.current_delay_minutes,
            "entries": [
                {
                    "entry_id": e.entry_id,
                    "position": e.queue_position,
                    "status": e.status.value,
                    "estimated_wait": e.estimated_wait_minutes,
                    "checked_in_at": e.checked_in_at.isoformat(),
                }
                for e in waiting_entries
            ],
        }

    def on_notification(self, handler: Callable):
        """Register a notification handler."""
        self._notification_handlers.append(handler)
