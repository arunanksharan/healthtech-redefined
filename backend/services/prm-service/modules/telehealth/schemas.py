"""
Telehealth Platform API Schemas

Pydantic schemas for request/response validation:
- Session management
- Appointment booking
- Waiting room operations
- Recording management
- Payment processing

EPIC-007: Telehealth Platform
"""

from datetime import datetime, date, time
from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel, Field, validator
from uuid import UUID
from enum import Enum


# ============================================================================
# ENUMS (matching models.py)
# ============================================================================

class SessionStatus(str, Enum):
    SCHEDULED = "scheduled"
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    TECHNICAL_FAILURE = "technical_failure"


class ParticipantRole(str, Enum):
    PATIENT = "patient"
    PROVIDER = "provider"
    INTERPRETER = "interpreter"
    CAREGIVER = "caregiver"
    OBSERVER = "observer"
    TECH_SUPPORT = "tech_support"


class ParticipantStatus(str, Enum):
    INVITED = "invited"
    WAITING = "waiting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"


class AppointmentType(str, Enum):
    VIDEO_VISIT = "video_visit"
    PHONE_CALL = "phone_call"
    FOLLOW_UP = "follow_up"
    NEW_PATIENT = "new_patient"
    GROUP_THERAPY = "group_therapy"
    URGENT_CARE = "urgent_care"
    MENTAL_HEALTH = "mental_health"
    CHRONIC_CARE = "chronic_care"


class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


class WaitingStatus(str, Enum):
    CHECKED_IN = "checked_in"
    DEVICE_CHECK = "device_check"
    READY = "ready"
    IN_CALL = "in_call"
    DEPARTED = "departed"
    NO_SHOW = "no_show"


class DeviceCheckStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"


class RecordingStatus(str, Enum):
    INITIALIZING = "initializing"
    RECORDING = "recording"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"
    WAIVED = "waived"


class ReminderType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


# ============================================================================
# SESSION SCHEMAS
# ============================================================================

class SessionCreate(BaseModel):
    """Create a new telehealth session."""
    session_type: str = Field(default="video_visit", description="Type of session")
    appointment_id: Optional[UUID] = None
    scheduled_duration_minutes: int = Field(default=30, ge=5, le=240)
    waiting_room_enabled: bool = True
    max_participants: int = Field(default=10, ge=2, le=50)
    screen_sharing_enabled: bool = True
    chat_enabled: bool = True
    whiteboard_enabled: bool = False
    metadata: Optional[Dict[str, Any]] = None


class SessionResponse(BaseModel):
    """Session response."""
    id: UUID
    room_name: str
    session_type: str
    status: SessionStatus
    appointment_id: Optional[UUID]
    scheduled_duration_minutes: int
    max_participants: int
    waiting_room_enabled: bool
    screen_sharing_enabled: bool
    chat_enabled: bool
    is_recording: bool
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    participant_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class JoinTokenRequest(BaseModel):
    """Request to generate a join token."""
    participant_id: UUID


class JoinTokenResponse(BaseModel):
    """Join token response."""
    token: str
    room_name: str
    livekit_url: Optional[str] = None
    expires_at: datetime


class ParticipantCreate(BaseModel):
    """Add a participant to a session."""
    user_id: UUID
    role: ParticipantRole
    display_name: str
    avatar_url: Optional[str] = None


class ParticipantResponse(BaseModel):
    """Participant response."""
    id: UUID
    user_id: UUID
    role: ParticipantRole
    display_name: str
    avatar_url: Optional[str]
    status: ParticipantStatus
    video_enabled: bool
    audio_enabled: bool
    screen_sharing: bool
    joined_at: Optional[datetime]
    connection_quality: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class MediaStateUpdate(BaseModel):
    """Update participant media state."""
    video_enabled: Optional[bool] = None
    audio_enabled: Optional[bool] = None
    screen_sharing: Optional[bool] = None


class ConnectionQualityUpdate(BaseModel):
    """Update connection quality metrics."""
    latency_ms: float
    packet_loss_percent: float
    jitter_ms: float
    bandwidth_kbps: int
    video_bitrate_kbps: int
    audio_bitrate_kbps: int


class SessionEndRequest(BaseModel):
    """End a session."""
    reason: str = "completed"


# ============================================================================
# APPOINTMENT SCHEMAS
# ============================================================================

class AppointmentCreate(BaseModel):
    """Create a telehealth appointment."""
    patient_id: UUID
    provider_id: UUID
    appointment_type: AppointmentType = AppointmentType.VIDEO_VISIT
    scheduled_start: datetime
    duration_minutes: int = Field(default=30, ge=5, le=240)
    patient_timezone: str = "UTC"
    reason_for_visit: Optional[str] = None
    chief_complaint: Optional[str] = None
    patient_name: Optional[str] = None
    provider_name: Optional[str] = None
    copay_amount: float = 0
    metadata: Optional[Dict[str, Any]] = None


class AppointmentResponse(BaseModel):
    """Appointment response."""
    id: UUID
    patient_id: UUID
    provider_id: UUID
    patient_name: Optional[str]
    provider_name: Optional[str]
    appointment_type: AppointmentType
    scheduled_start: datetime
    scheduled_end: datetime
    duration_minutes: int
    patient_timezone: str
    provider_timezone: str
    reason_for_visit: Optional[str]
    status: AppointmentStatus
    session_id: Optional[UUID]
    join_url: Optional[str]
    copay_amount: float
    payment_status: PaymentStatus
    confirmed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class AppointmentReschedule(BaseModel):
    """Reschedule an appointment."""
    new_start_time: datetime


class AppointmentCancel(BaseModel):
    """Cancel an appointment."""
    reason: str
    cancelled_by: Optional[UUID] = None


class AvailableSlotsRequest(BaseModel):
    """Request available slots."""
    provider_id: UUID
    appointment_type: AppointmentType = AppointmentType.VIDEO_VISIT
    start_date: date
    end_date: date
    patient_timezone: str = "UTC"


class AvailableSlot(BaseModel):
    """An available appointment slot."""
    slot_id: str
    provider_id: UUID
    start_time: datetime
    end_time: datetime
    appointment_type: AppointmentType
    is_available: bool = True


class ProviderScheduleCreate(BaseModel):
    """Create/update provider schedule."""
    weekly_hours: Dict[int, List[Tuple[str, str]]] = Field(
        description="Weekly hours: {0: [('09:00', '12:00'), ('13:00', '17:00')], ...}"
    )
    timezone: str = "America/New_York"
    appointment_types: Optional[List[AppointmentType]] = None
    default_duration_minutes: int = 30
    buffer_minutes: int = 5


class ProviderScheduleResponse(BaseModel):
    """Provider schedule response."""
    id: UUID
    provider_id: UUID
    weekly_hours: Dict[int, List[List[str]]]
    timezone: str
    appointment_types: List[str]
    default_duration_minutes: int
    buffer_minutes: int
    is_active: bool

    class Config:
        from_attributes = True


class BlockedTimeCreate(BaseModel):
    """Block time on schedule."""
    start_time: datetime
    end_time: datetime
    reason: Optional[str] = None
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None


# ============================================================================
# WAITING ROOM SCHEMAS
# ============================================================================

class WaitingRoomCreate(BaseModel):
    """Create a waiting room."""
    name: str
    provider_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    device_check_required: bool = True
    forms_required: bool = True
    max_wait_minutes: int = 60
    auto_notify_minutes: int = 5


class WaitingRoomResponse(BaseModel):
    """Waiting room response."""
    id: UUID
    name: str
    provider_id: Optional[UUID]
    location_id: Optional[UUID]
    is_open: bool
    current_delay_minutes: int
    device_check_required: bool
    forms_required: bool
    total_waiting: int = 0
    ready_count: int = 0

    class Config:
        from_attributes = True


class CheckInRequest(BaseModel):
    """Check into waiting room."""
    session_id: Optional[UUID] = None
    appointment_id: Optional[UUID] = None
    patient_id: UUID
    provider_id: Optional[UUID] = None
    scheduled_time: Optional[datetime] = None
    priority: int = 0
    required_forms: Optional[List[str]] = None


class WaitingRoomEntryResponse(BaseModel):
    """Waiting room entry response."""
    id: UUID
    patient_id: UUID
    status: WaitingStatus
    priority: int
    queue_position: int
    estimated_wait_minutes: int
    checked_in_at: datetime
    scheduled_time: Optional[datetime]
    provider_id: Optional[UUID]
    provider_name: Optional[str]
    provider_available: bool
    device_check_status: DeviceCheckStatus
    forms_completed: bool
    unread_messages: int = 0

    class Config:
        from_attributes = True


class DeviceCheckResult(BaseModel):
    """Device check results."""
    camera_available: bool
    camera_working: bool
    camera_device: Optional[str] = None
    microphone_available: bool
    microphone_working: bool
    microphone_device: Optional[str] = None
    speaker_available: bool
    speaker_working: bool
    speaker_device: Optional[str] = None
    connection_speed_mbps: float
    latency_ms: float
    jitter_ms: float = 0
    packet_loss_percent: float = 0
    browser_name: str
    browser_version: Optional[str] = None
    webrtc_supported: bool


class DeviceCheckResponse(BaseModel):
    """Device check response."""
    check_id: UUID
    status: DeviceCheckStatus
    issues: List[str] = []
    checked_at: Optional[datetime]


class FormSubmission(BaseModel):
    """Pre-visit form submission."""
    form_id: UUID
    responses: Dict[str, Any]


class ChatMessageCreate(BaseModel):
    """Send a chat message."""
    content: str
    sender_type: str = Field(description="patient or staff")


class ChatMessageResponse(BaseModel):
    """Chat message response."""
    id: UUID
    sender_id: UUID
    sender_type: str
    content: str
    timestamp: datetime
    read: bool

    class Config:
        from_attributes = True


class QueueStatus(BaseModel):
    """Queue status for waiting room."""
    room_id: UUID
    is_open: bool
    total_waiting: int
    ready_count: int
    current_delay_minutes: int
    entries: List[Dict[str, Any]]


# ============================================================================
# RECORDING SCHEMAS
# ============================================================================

class StartRecordingRequest(BaseModel):
    """Start recording a session."""
    participant_id: UUID


class RecordingResponse(BaseModel):
    """Recording response."""
    id: UUID
    session_id: UUID
    status: RecordingStatus
    duration_seconds: Optional[int]
    file_size_bytes: Optional[int]
    format: str
    started_at: Optional[datetime]
    ended_at: Optional[datetime]

    class Config:
        from_attributes = True


class RecordingConsentRequest(BaseModel):
    """Record consent for recording."""
    participant_id: UUID
    consented: bool
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


# ============================================================================
# PAYMENT SCHEMAS
# ============================================================================

class PaymentCreate(BaseModel):
    """Create a payment."""
    appointment_id: UUID
    patient_id: UUID
    amount_cents: int
    currency: str = "USD"
    payment_method: Optional[str] = None


class PaymentResponse(BaseModel):
    """Payment response."""
    id: UUID
    appointment_id: UUID
    patient_id: UUID
    amount_cents: int
    currency: str
    status: PaymentStatus
    payment_method: Optional[str]
    card_last_four: Optional[str]
    card_brand: Optional[str]
    receipt_url: Optional[str]
    authorized_at: Optional[datetime]
    captured_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentIntentCreate(BaseModel):
    """Create a payment intent."""
    appointment_id: UUID
    amount_cents: int
    currency: str = "USD"


class PaymentIntentResponse(BaseModel):
    """Payment intent response."""
    client_secret: str
    payment_id: UUID
    amount_cents: int
    currency: str


class RefundRequest(BaseModel):
    """Refund a payment."""
    amount_cents: Optional[int] = None  # Full refund if not specified
    reason: str


# ============================================================================
# ANALYTICS SCHEMAS
# ============================================================================

class SessionAnalyticsResponse(BaseModel):
    """Session analytics response."""
    session_id: UUID
    avg_latency_ms: Optional[float]
    avg_packet_loss_percent: Optional[float]
    avg_jitter_ms: Optional[float]
    avg_mos_score: Optional[float]
    avg_video_bitrate_kbps: Optional[int]
    video_freeze_count: int = 0
    audio_dropout_count: int = 0
    connection_attempts: int = 1
    reconnection_count: int = 0
    technical_issues: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True


class SatisfactionSurveyCreate(BaseModel):
    """Submit satisfaction survey."""
    session_id: UUID
    appointment_id: Optional[UUID] = None
    overall_rating: Optional[int] = Field(None, ge=1, le=5)
    video_quality_rating: Optional[int] = Field(None, ge=1, le=5)
    audio_quality_rating: Optional[int] = Field(None, ge=1, le=5)
    provider_rating: Optional[int] = Field(None, ge=1, le=5)
    ease_of_use_rating: Optional[int] = Field(None, ge=1, le=5)
    would_recommend: Optional[bool] = None
    nps_score: Optional[int] = Field(None, ge=0, le=10)
    feedback_text: Optional[str] = None
    technical_issues_reported: Optional[List[str]] = None


class TelehealthMetricsResponse(BaseModel):
    """Telehealth utilization metrics."""
    total_sessions: int
    completed_sessions: int
    no_show_count: int
    technical_failure_count: int
    avg_session_duration_minutes: float
    avg_wait_time_minutes: float
    avg_satisfaction_score: float
    total_revenue_cents: int
    sessions_by_type: Dict[str, int]
    sessions_by_status: Dict[str, int]


# ============================================================================
# INTERPRETER SCHEMAS
# ============================================================================

class InterpreterRequest(BaseModel):
    """Request an interpreter."""
    session_id: UUID
    language: str
    is_scheduled: bool = False
    scheduled_for: Optional[datetime] = None


class InterpreterResponse(BaseModel):
    """Interpreter assignment response."""
    request_id: UUID
    session_id: UUID
    language: str
    status: str  # pending, assigned, joined, completed
    interpreter_id: Optional[UUID] = None
    interpreter_name: Optional[str] = None
    assigned_at: Optional[datetime] = None
    estimated_wait_minutes: Optional[int] = None


# ============================================================================
# PAGINATION
# ============================================================================

class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# CALENDAR SCHEMAS
# ============================================================================

class CalendarExportResponse(BaseModel):
    """Calendar export response."""
    ics_content: str
    filename: str


class CalendarSyncRequest(BaseModel):
    """Calendar sync request."""
    calendar_type: str = Field(description="google, outlook, apple")
    access_token: str
    sync_direction: str = "export"  # export, import, bidirectional
