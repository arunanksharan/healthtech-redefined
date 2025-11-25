"""
Telehealth Platform Database Models

SQLAlchemy models for persistent storage of telehealth data:
- Video sessions
- Telehealth appointments
- Waiting room entries
- Session recordings
- Device checks
- Connection analytics

EPIC-007: Telehealth Platform
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Float, DateTime, Date,
    ForeignKey, JSON, Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import uuid
import enum

Base = declarative_base()


# ============================================================================
# ENUMS
# ============================================================================

class SessionStatus(str, enum.Enum):
    """Telehealth session status."""
    SCHEDULED = "scheduled"
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    TECHNICAL_FAILURE = "technical_failure"


class ParticipantRole(str, enum.Enum):
    """Participant roles in a telehealth session."""
    PATIENT = "patient"
    PROVIDER = "provider"
    INTERPRETER = "interpreter"
    CAREGIVER = "caregiver"
    OBSERVER = "observer"
    TECH_SUPPORT = "tech_support"


class ParticipantStatus(str, enum.Enum):
    """Participant connection status."""
    INVITED = "invited"
    WAITING = "waiting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"


class AppointmentType(str, enum.Enum):
    """Types of telehealth appointments."""
    VIDEO_VISIT = "video_visit"
    PHONE_CALL = "phone_call"
    FOLLOW_UP = "follow_up"
    NEW_PATIENT = "new_patient"
    GROUP_THERAPY = "group_therapy"
    URGENT_CARE = "urgent_care"
    MENTAL_HEALTH = "mental_health"
    CHRONIC_CARE = "chronic_care"


class AppointmentStatus(str, enum.Enum):
    """Telehealth appointment status."""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


class WaitingStatus(str, enum.Enum):
    """Status of a waiting room entry."""
    CHECKED_IN = "checked_in"
    DEVICE_CHECK = "device_check"
    READY = "ready"
    IN_CALL = "in_call"
    DEPARTED = "departed"
    NO_SHOW = "no_show"


class DeviceCheckStatus(str, enum.Enum):
    """Device check status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"


class RecordingStatus(str, enum.Enum):
    """Recording status."""
    INITIALIZING = "initializing"
    RECORDING = "recording"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


class PaymentStatus(str, enum.Enum):
    """Payment status for telehealth visits."""
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"
    WAIVED = "waived"


# ============================================================================
# VIDEO SESSION MODELS
# ============================================================================

class TelehealthSession(Base):
    """A telehealth video consultation session."""
    __tablename__ = "telehealth_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Appointment reference
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("telehealth_appointments.id"), nullable=True)
    encounter_id = Column(UUID(as_uuid=True), nullable=True)

    # Room configuration
    room_name = Column(String(100), nullable=False, unique=True)
    room_token = Column(Text, nullable=True)

    # Session details
    session_type = Column(String(50), default="video_visit")
    scheduled_duration_minutes = Column(Integer, default=30)
    max_participants = Column(Integer, default=10)

    # Status
    status = Column(SQLEnum(SessionStatus), default=SessionStatus.SCHEDULED, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    actual_duration_seconds = Column(Integer, nullable=True)

    # Recording
    is_recording = Column(Boolean, default=False)
    recording_id = Column(UUID(as_uuid=True), nullable=True)
    consent_obtained = Column(Boolean, default=False)

    # Security
    encryption_key_id = Column(String(100), nullable=True)
    join_password = Column(String(100), nullable=True)
    waiting_room_enabled = Column(Boolean, default=True)

    # Features
    screen_sharing_enabled = Column(Boolean, default=True)
    chat_enabled = Column(Boolean, default=True)
    file_sharing_enabled = Column(Boolean, default=True)
    whiteboard_enabled = Column(Boolean, default=False)

    # Metadata
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    participants = relationship("SessionParticipant", back_populates="session", cascade="all, delete-orphan")
    events = relationship("SessionEvent", back_populates="session", cascade="all, delete-orphan")
    recording = relationship("SessionRecording", back_populates="session", uselist=False)

    __table_args__ = (
        Index("idx_telehealth_sessions_tenant_status", "tenant_id", "status"),
        Index("idx_telehealth_sessions_appointment", "appointment_id"),
    )


class SessionParticipant(Base):
    """Participant in a telehealth session."""
    __tablename__ = "session_participants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("telehealth_sessions.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Identity
    user_id = Column(UUID(as_uuid=True), nullable=False)
    role = Column(SQLEnum(ParticipantRole), nullable=False)
    display_name = Column(String(200), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # Connection
    status = Column(SQLEnum(ParticipantStatus), default=ParticipantStatus.INVITED)
    connection_id = Column(String(100), nullable=True)

    # Device capabilities
    device_info = Column(JSONB, default=dict)  # browser, os, video_resolution, etc.

    # Connection quality
    connection_quality = Column(JSONB, default=dict)  # latency, packet_loss, jitter, etc.

    # Media state
    video_enabled = Column(Boolean, default=True)
    audio_enabled = Column(Boolean, default=True)
    screen_sharing = Column(Boolean, default=False)

    # Timestamps
    invited_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    joined_at = Column(DateTime(timezone=True), nullable=True)
    left_at = Column(DateTime(timezone=True), nullable=True)

    # Permissions
    can_share_screen = Column(Boolean, default=True)
    can_record = Column(Boolean, default=False)
    can_admit_participants = Column(Boolean, default=False)

    # Relationship
    session = relationship("TelehealthSession", back_populates="participants")

    __table_args__ = (
        Index("idx_session_participants_session", "session_id"),
        Index("idx_session_participants_user", "user_id"),
    )


class SessionEvent(Base):
    """Event that occurred during a session."""
    __tablename__ = "session_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("telehealth_sessions.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    event_type = Column(String(100), nullable=False)  # session_created, participant_joined, etc.
    participant_id = Column(UUID(as_uuid=True), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)
    data = Column(JSONB, default=dict)

    # Relationship
    session = relationship("TelehealthSession", back_populates="events")

    __table_args__ = (
        Index("idx_session_events_session", "session_id"),
        Index("idx_session_events_type", "event_type"),
    )


# ============================================================================
# TELEHEALTH APPOINTMENT MODELS
# ============================================================================

class TelehealthAppointment(Base):
    """A telehealth appointment."""
    __tablename__ = "telehealth_appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Participants
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    provider_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    patient_name = Column(String(200), nullable=True)
    provider_name = Column(String(200), nullable=True)

    # Type and timing
    appointment_type = Column(SQLEnum(AppointmentType), default=AppointmentType.VIDEO_VISIT)
    scheduled_start = Column(DateTime(timezone=True), nullable=False)
    scheduled_end = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, default=30)

    # Time zones
    patient_timezone = Column(String(50), default="UTC")
    provider_timezone = Column(String(50), default="UTC")

    # Reason
    reason_for_visit = Column(Text, nullable=True)
    chief_complaint = Column(Text, nullable=True)
    diagnosis_codes = Column(ARRAY(String), default=list)

    # Session
    session_id = Column(UUID(as_uuid=True), nullable=True)
    join_url = Column(String(500), nullable=True)

    # Status
    status = Column(SQLEnum(AppointmentStatus), default=AppointmentStatus.SCHEDULED, index=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    cancelled_by = Column(UUID(as_uuid=True), nullable=True)

    # Rescheduling
    rescheduled_from = Column(UUID(as_uuid=True), nullable=True)
    rescheduled_to = Column(UUID(as_uuid=True), nullable=True)

    # Billing
    copay_amount = Column(Float, default=0)
    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    payment_id = Column(String(100), nullable=True)

    # Insurance
    insurance_verified = Column(Boolean, default=False)
    insurance_verification_id = Column(String(100), nullable=True)

    # Notes
    pre_visit_notes = Column(Text, nullable=True)
    post_visit_notes = Column(Text, nullable=True)

    # Metadata
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    reminders = relationship("AppointmentReminder", back_populates="appointment", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_telehealth_appointments_patient", "tenant_id", "patient_id"),
        Index("idx_telehealth_appointments_provider", "tenant_id", "provider_id"),
        Index("idx_telehealth_appointments_scheduled", "tenant_id", "scheduled_start"),
        Index("idx_telehealth_appointments_status", "tenant_id", "status"),
    )


class AppointmentReminder(Base):
    """Appointment reminder."""
    __tablename__ = "appointment_reminders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("telehealth_appointments.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    reminder_type = Column(String(20), nullable=False)  # email, sms, push
    scheduled_for = Column(DateTime(timezone=True), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    content = Column(Text, nullable=True)

    # Delivery status
    delivery_status = Column(String(50), default="pending")  # pending, sent, delivered, failed
    delivery_error = Column(Text, nullable=True)

    # Relationship
    appointment = relationship("TelehealthAppointment", back_populates="reminders")

    __table_args__ = (
        Index("idx_appointment_reminders_scheduled", "scheduled_for"),
        Index("idx_appointment_reminders_status", "delivery_status"),
    )


class ProviderSchedule(Base):
    """Provider's weekly schedule for telehealth."""
    __tablename__ = "provider_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    provider_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Weekly hours: {0: [["09:00", "12:00"], ["13:00", "17:00"]], ...}
    weekly_hours = Column(JSONB, default=dict)

    # Time zone
    timezone = Column(String(50), default="America/New_York")

    # Appointment types offered
    appointment_types = Column(ARRAY(String), default=list)

    # Default settings
    default_duration_minutes = Column(Integer, default=30)
    buffer_minutes = Column(Integer, default=5)
    max_daily_appointments = Column(Integer, nullable=True)

    # Active status
    is_active = Column(Boolean, default=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    blocked_times = relationship("ScheduleBlockedTime", back_populates="schedule", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("tenant_id", "provider_id", name="uq_provider_schedule"),
    )


class ScheduleBlockedTime(Base):
    """Blocked time periods for a provider."""
    __tablename__ = "schedule_blocked_times"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    schedule_id = Column(UUID(as_uuid=True), ForeignKey("provider_schedules.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Time range
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)

    # Reason
    reason = Column(String(200), nullable=True)
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String(50), nullable=True)  # daily, weekly, etc.

    # Relationship
    schedule = relationship("ProviderSchedule", back_populates="blocked_times")


# ============================================================================
# WAITING ROOM MODELS
# ============================================================================

class WaitingRoom(Base):
    """A virtual waiting room for a provider or location."""
    __tablename__ = "waiting_rooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Identity
    name = Column(String(200), nullable=False)
    location_id = Column(UUID(as_uuid=True), nullable=True)
    provider_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Configuration
    max_wait_minutes = Column(Integer, default=60)
    auto_notify_minutes = Column(Integer, default=5)
    device_check_required = Column(Boolean, default=True)
    forms_required = Column(Boolean, default=True)

    # Status
    is_open = Column(Boolean, default=True)
    current_delay_minutes = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    entries = relationship("WaitingRoomEntry", back_populates="waiting_room", cascade="all, delete-orphan")


class WaitingRoomEntry(Base):
    """Entry for a patient in the waiting room."""
    __tablename__ = "waiting_room_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    waiting_room_id = Column(UUID(as_uuid=True), ForeignKey("waiting_rooms.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # References
    session_id = Column(UUID(as_uuid=True), nullable=True)
    appointment_id = Column(UUID(as_uuid=True), nullable=True)
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Status
    status = Column(SQLEnum(WaitingStatus), default=WaitingStatus.CHECKED_IN, index=True)
    priority = Column(Integer, default=0)

    # Check-in
    checked_in_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    scheduled_time = Column(DateTime(timezone=True), nullable=True)

    # Provider
    provider_id = Column(UUID(as_uuid=True), nullable=True)
    provider_name = Column(String(200), nullable=True)
    provider_available = Column(Boolean, default=False)

    # Device check
    device_check_status = Column(SQLEnum(DeviceCheckStatus), default=DeviceCheckStatus.NOT_STARTED)
    device_check_result = Column(JSONB, default=dict)

    # Queue
    queue_position = Column(Integer, default=0)
    estimated_wait_minutes = Column(Integer, default=0)

    # Forms completed
    forms_completed = Column(Boolean, default=False)

    # Metadata
    metadata = Column(JSONB, default=dict)
    departed_at = Column(DateTime(timezone=True), nullable=True)
    departure_reason = Column(String(100), nullable=True)

    # Relationships
    waiting_room = relationship("WaitingRoom", back_populates="entries")
    messages = relationship("WaitingRoomMessage", back_populates="entry", cascade="all, delete-orphan")
    forms = relationship("PreVisitForm", back_populates="entry", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_waiting_room_entries_patient", "tenant_id", "patient_id"),
        Index("idx_waiting_room_entries_status", "waiting_room_id", "status"),
    )


class WaitingRoomMessage(Base):
    """Chat message in waiting room."""
    __tablename__ = "waiting_room_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entry_id = Column(UUID(as_uuid=True), ForeignKey("waiting_room_entries.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    sender_id = Column(UUID(as_uuid=True), nullable=False)
    sender_type = Column(String(20), nullable=False)  # patient, staff
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)
    read = Column(Boolean, default=False)

    # Relationship
    entry = relationship("WaitingRoomEntry", back_populates="messages")


class PreVisitForm(Base):
    """Pre-visit form submission."""
    __tablename__ = "pre_visit_forms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entry_id = Column(UUID(as_uuid=True), ForeignKey("waiting_room_entries.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    form_type = Column(String(50), nullable=False)  # intake, consent, symptom_checker
    patient_id = Column(UUID(as_uuid=True), nullable=False)

    # Form content
    questions = Column(JSONB, default=list)
    responses = Column(JSONB, default=dict)

    # Status
    status = Column(String(20), default="pending")  # pending, in_progress, completed
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship
    entry = relationship("WaitingRoomEntry", back_populates="forms")


# ============================================================================
# RECORDING MODELS
# ============================================================================

class SessionRecording(Base):
    """Recording of a telehealth session."""
    __tablename__ = "session_recordings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("telehealth_sessions.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Recording details
    status = Column(SQLEnum(RecordingStatus), default=RecordingStatus.INITIALIZING)
    format = Column(String(20), default="mp4")
    duration_seconds = Column(Integer, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)

    # Storage
    storage_path = Column(String(500), nullable=True)
    storage_bucket = Column(String(100), nullable=True)
    storage_provider = Column(String(50), default="s3")

    # Encryption
    encryption_key_id = Column(String(100), nullable=True)
    encryption_algorithm = Column(String(50), default="AES-256-GCM")

    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # Retention
    retention_days = Column(Integer, default=365)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship
    session = relationship("TelehealthSession", back_populates="recording")
    consents = relationship("RecordingConsent", back_populates="recording", cascade="all, delete-orphan")


class RecordingConsent(Base):
    """Consent record for session recording."""
    __tablename__ = "recording_consents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recording_id = Column(UUID(as_uuid=True), ForeignKey("session_recordings.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Participant
    participant_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)

    # Consent details
    consented = Column(Boolean, nullable=False)
    consented_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Relationship
    recording = relationship("SessionRecording", back_populates="consents")


# ============================================================================
# ANALYTICS MODELS
# ============================================================================

class SessionAnalytics(Base):
    """Analytics for a telehealth session."""
    __tablename__ = "session_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Call quality
    avg_latency_ms = Column(Float, nullable=True)
    avg_packet_loss_percent = Column(Float, nullable=True)
    avg_jitter_ms = Column(Float, nullable=True)
    avg_mos_score = Column(Float, nullable=True)  # Mean Opinion Score 1-5

    # Video metrics
    avg_video_bitrate_kbps = Column(Integer, nullable=True)
    video_quality_changes = Column(Integer, default=0)
    video_freeze_count = Column(Integer, default=0)
    video_freeze_duration_seconds = Column(Integer, default=0)

    # Audio metrics
    avg_audio_bitrate_kbps = Column(Integer, nullable=True)
    audio_dropout_count = Column(Integer, default=0)
    audio_dropout_duration_seconds = Column(Integer, default=0)

    # Connection
    connection_attempts = Column(Integer, default=1)
    reconnection_count = Column(Integer, default=0)
    total_connection_time_seconds = Column(Integer, nullable=True)

    # Technical issues
    technical_issues = Column(JSONB, default=list)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("idx_session_analytics_tenant", "tenant_id"),
    )


class TelehealthPayment(Base):
    """Payment for a telehealth visit."""
    __tablename__ = "telehealth_payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    appointment_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Patient
    patient_id = Column(UUID(as_uuid=True), nullable=False)

    # Amount
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="USD")

    # Payment details
    payment_method = Column(String(50), nullable=True)  # card, ach, hsa
    payment_provider = Column(String(50), default="stripe")  # stripe, square
    external_payment_id = Column(String(100), nullable=True)

    # Status
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, index=True)

    # Card details (tokenized)
    card_last_four = Column(String(4), nullable=True)
    card_brand = Column(String(20), nullable=True)

    # Timestamps
    authorized_at = Column(DateTime(timezone=True), nullable=True)
    captured_at = Column(DateTime(timezone=True), nullable=True)
    refunded_at = Column(DateTime(timezone=True), nullable=True)

    # Refund
    refund_amount_cents = Column(Integer, nullable=True)
    refund_reason = Column(String(200), nullable=True)

    # Receipt
    receipt_url = Column(String(500), nullable=True)

    # Metadata
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_telehealth_payments_appointment", "appointment_id"),
    )


class PatientSatisfactionSurvey(Base):
    """Post-visit satisfaction survey."""
    __tablename__ = "patient_satisfaction_surveys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    appointment_id = Column(UUID(as_uuid=True), nullable=True)

    # Patient
    patient_id = Column(UUID(as_uuid=True), nullable=False)

    # Ratings (1-5)
    overall_rating = Column(Integer, nullable=True)
    video_quality_rating = Column(Integer, nullable=True)
    audio_quality_rating = Column(Integer, nullable=True)
    provider_rating = Column(Integer, nullable=True)
    ease_of_use_rating = Column(Integer, nullable=True)

    # Would recommend
    would_recommend = Column(Boolean, nullable=True)
    nps_score = Column(Integer, nullable=True)  # Net Promoter Score 0-10

    # Feedback
    feedback_text = Column(Text, nullable=True)
    technical_issues_reported = Column(JSONB, default=list)

    # Timestamps
    sent_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_satisfaction_surveys_session", "session_id"),
    )
