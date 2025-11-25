"""
Telehealth Platform Module

Comprehensive telehealth capabilities including:
- Video consultation with WebRTC/LiveKit
- Virtual waiting room management
- Session recording and compliance
- Screen sharing and collaboration
- In-call clinical tools integration
- Multi-party calls (interpreters)

EPIC-007: Telehealth Platform
"""

from .session_manager import (
    TelehealthSession,
    SessionStatus,
    Participant,
    SessionManager,
)
from .waiting_room import (
    WaitingRoom,
    WaitingRoomEntry,
    WaitingRoomService,
)
from .video_service import (
    VideoService,
    VideoQuality,
    ConnectionStats,
)
from .scheduling import (
    TelehealthAppointment,
    TelehealthScheduler,
    AppointmentType,
)
from .recording import (
    RecordingService,
    SessionRecording,
    RecordingStatus,
)

__all__ = [
    # Session Management
    "TelehealthSession",
    "SessionStatus",
    "Participant",
    "SessionManager",
    # Waiting Room
    "WaitingRoom",
    "WaitingRoomEntry",
    "WaitingRoomService",
    # Video Service
    "VideoService",
    "VideoQuality",
    "ConnectionStats",
    # Scheduling
    "TelehealthAppointment",
    "TelehealthScheduler",
    "AppointmentType",
    # Recording
    "RecordingService",
    "SessionRecording",
    "RecordingStatus",
]
