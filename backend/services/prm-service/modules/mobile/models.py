"""
Mobile Applications Platform Models
EPIC-016: Database models for mobile application backend support
"""
import enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Float, DateTime, Date,
    ForeignKey, Enum, Index, CheckConstraint, UniqueConstraint, JSON
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from shared.database.connection import Base


def generate_uuid():
    return uuid4()


# ==================== Enums ====================

class DevicePlatform(enum.Enum):
    """Mobile device platforms"""
    IOS = "ios"
    ANDROID = "android"
    WEB = "web"
    WATCHOS = "watchos"
    WEAROS = "wearos"


class DeviceStatus(enum.Enum):
    """Device registration status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


class NotificationType(enum.Enum):
    """Push notification types"""
    APPOINTMENT_REMINDER = "appointment_reminder"
    MEDICATION_REMINDER = "medication_reminder"
    LAB_RESULT = "lab_result"
    MESSAGE = "message"
    HEALTH_ALERT = "health_alert"
    HEALTH_TIP = "health_tip"
    EMERGENCY = "emergency"
    SYSTEM = "system"
    PROMOTIONAL = "promotional"


class NotificationPriority(enum.Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationStatus(enum.Enum):
    """Notification delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    EXPIRED = "expired"


class SyncEntityType(enum.Enum):
    """Entities that can be synced"""
    PATIENT = "patient"
    APPOINTMENT = "appointment"
    HEALTH_RECORD = "health_record"
    MEDICATION = "medication"
    MESSAGE = "message"
    DOCUMENT = "document"
    PROVIDER = "provider"
    CARE_TEAM = "care_team"
    NOTIFICATION = "notification"


class SyncOperationType(enum.Enum):
    """Sync operation types"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class SyncStatus(enum.Enum):
    """Sync operation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"


class WearableType(enum.Enum):
    """Wearable device types"""
    APPLE_WATCH = "apple_watch"
    WEAR_OS = "wear_os"
    FITBIT = "fitbit"
    GARMIN = "garmin"
    SAMSUNG_GALAXY = "samsung_galaxy"
    WHOOP = "whoop"
    OURA = "oura"
    OTHER = "other"


class HealthMetricType(enum.Enum):
    """Types of health metrics from wearables"""
    HEART_RATE = "heart_rate"
    HEART_RATE_VARIABILITY = "heart_rate_variability"
    BLOOD_OXYGEN = "blood_oxygen"
    BLOOD_PRESSURE = "blood_pressure"
    BLOOD_GLUCOSE = "blood_glucose"
    STEPS = "steps"
    DISTANCE = "distance"
    CALORIES = "calories"
    ACTIVE_MINUTES = "active_minutes"
    SLEEP = "sleep"
    WEIGHT = "weight"
    BODY_TEMPERATURE = "body_temperature"
    RESPIRATORY_RATE = "respiratory_rate"
    ECG = "ecg"
    FALL_DETECTION = "fall_detection"
    STRESS = "stress"
    MINDFULNESS = "mindfulness"


class SessionStatus(enum.Enum):
    """Mobile session status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    LOCKED = "locked"


class BiometricType(enum.Enum):
    """Biometric authentication types"""
    FACE_ID = "face_id"
    TOUCH_ID = "touch_id"
    FINGERPRINT = "fingerprint"
    IRIS = "iris"
    VOICE = "voice"


class AppUpdateChannel(enum.Enum):
    """App update channels"""
    PRODUCTION = "production"
    STAGING = "staging"
    BETA = "beta"
    ALPHA = "alpha"


# ==================== Device Management Models ====================

class MobileDevice(Base):
    """Registered mobile devices"""
    __tablename__ = "mobile_devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # patient or provider
    user_type = Column(String(20), nullable=False)  # "patient" or "provider"

    # Device identification
    device_id = Column(String(255), nullable=False)  # Unique device identifier
    device_token = Column(Text)  # Push notification token (FCM/APNs)
    platform = Column(Enum(DevicePlatform), nullable=False)
    platform_version = Column(String(50))  # e.g., "iOS 17.0", "Android 14"
    device_model = Column(String(100))  # e.g., "iPhone 15 Pro", "Pixel 8"
    device_name = Column(String(255))  # User's device name

    # App information
    app_version = Column(String(20), nullable=False)
    app_build = Column(String(20))
    bundle_id = Column(String(255))  # com.healthcare.app
    update_channel = Column(Enum(AppUpdateChannel), default=AppUpdateChannel.PRODUCTION)

    # Security
    status = Column(Enum(DeviceStatus), default=DeviceStatus.ACTIVE)
    biometric_enabled = Column(Boolean, default=False)
    biometric_type = Column(Enum(BiometricType))
    pin_enabled = Column(Boolean, default=False)
    is_jailbroken = Column(Boolean, default=False)
    is_rooted = Column(Boolean, default=False)
    device_fingerprint = Column(String(255))  # Device integrity fingerprint

    # Settings
    notification_enabled = Column(Boolean, default=True)
    notification_preferences = Column(JSONB, default=dict)  # Per-type settings
    locale = Column(String(10), default="en")
    timezone = Column(String(50))

    # Network info
    last_ip_address = Column(INET)
    carrier = Column(String(100))

    # Timestamps
    registered_at = Column(DateTime(timezone=True), default=func.now())
    last_active_at = Column(DateTime(timezone=True), default=func.now())
    last_sync_at = Column(DateTime(timezone=True))
    token_updated_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    sessions = relationship("MobileSession", back_populates="device", cascade="all, delete-orphan")
    notifications = relationship("PushNotification", back_populates="device")

    __table_args__ = (
        UniqueConstraint("tenant_id", "device_id", name="uq_mobile_device_tenant_device"),
        Index("ix_mobile_device_user", "user_id", "user_type"),
        Index("ix_mobile_device_token", "device_token"),
    )


class MobileSession(Base):
    """Mobile app sessions for security tracking"""
    __tablename__ = "mobile_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    device_id = Column(UUID(as_uuid=True), ForeignKey("mobile_devices.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Session details
    session_token = Column(String(255), nullable=False, unique=True)
    refresh_token = Column(String(255))
    status = Column(Enum(SessionStatus), default=SessionStatus.ACTIVE)

    # Authentication
    auth_method = Column(String(50), nullable=False)  # "password", "biometric", "sso"
    biometric_verified = Column(Boolean, default=False)
    mfa_verified = Column(Boolean, default=False)

    # Security
    ip_address = Column(INET)
    user_agent = Column(Text)
    location = Column(JSONB)  # {latitude, longitude, city, country}

    # Timing
    started_at = Column(DateTime(timezone=True), default=func.now())
    last_activity_at = Column(DateTime(timezone=True), default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True))

    # Metadata
    app_state = Column(JSONB)  # Last app state for restoration
    failed_attempts = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), default=func.now())

    # Relationships
    device = relationship("MobileDevice", back_populates="sessions")

    __table_args__ = (
        Index("ix_mobile_session_token", "session_token"),
        Index("ix_mobile_session_expires", "expires_at"),
    )


# ==================== Push Notification Models ====================

class PushNotification(Base):
    """Push notification records"""
    __tablename__ = "push_notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("mobile_devices.id"), index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Notification content
    notification_type = Column(Enum(NotificationType), nullable=False)
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.NORMAL)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    subtitle = Column(String(255))
    image_url = Column(Text)

    # Rich notification data
    data = Column(JSONB)  # Custom payload
    action_url = Column(Text)  # Deep link URL
    actions = Column(JSONB)  # Action buttons

    # Delivery
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING)
    platform = Column(Enum(DevicePlatform))

    # FCM/APNs specific
    fcm_message_id = Column(String(255))
    apns_id = Column(String(255))
    collapse_key = Column(String(255))  # For grouping
    ttl = Column(Integer)  # Time to live in seconds

    # Tracking
    scheduled_at = Column(DateTime(timezone=True))
    sent_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    read_at = Column(DateTime(timezone=True))
    failed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)

    # Analytics
    opened = Column(Boolean, default=False)
    opened_at = Column(DateTime(timezone=True))
    dismissed = Column(Boolean, default=False)
    dismissed_at = Column(DateTime(timezone=True))
    action_taken = Column(String(50))
    action_taken_at = Column(DateTime(timezone=True))

    # Source
    triggered_by = Column(String(100))  # "system", "provider", "automation"
    source_entity_type = Column(String(50))
    source_entity_id = Column(UUID(as_uuid=True))

    created_at = Column(DateTime(timezone=True), default=func.now())

    # Relationships
    device = relationship("MobileDevice", back_populates="notifications")

    __table_args__ = (
        Index("ix_push_notification_status", "status"),
        Index("ix_push_notification_type", "notification_type"),
        Index("ix_push_notification_scheduled", "scheduled_at"),
    )


class NotificationPreference(Base):
    """User notification preferences"""
    __tablename__ = "notification_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Global settings
    push_enabled = Column(Boolean, default=True)
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=True)

    # Per-type settings
    type_preferences = Column(JSONB, default=dict)  # {type: {enabled, channels, sound, vibrate}}

    # Quiet hours
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(String(5))  # "22:00"
    quiet_hours_end = Column(String(5))  # "07:00"
    quiet_hours_days = Column(ARRAY(Integer))  # [0, 1, 2, 3, 4, 5, 6] for weekdays

    # Sound settings
    sound_enabled = Column(Boolean, default=True)
    vibration_enabled = Column(Boolean, default=True)
    custom_sound = Column(String(100))

    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_notification_pref_user"),
    )


# ==================== Sync Models ====================

class SyncCheckpoint(Base):
    """Sync checkpoints for delta sync"""
    __tablename__ = "sync_checkpoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    device_id = Column(UUID(as_uuid=True), ForeignKey("mobile_devices.id"), nullable=False, index=True)
    entity_type = Column(Enum(SyncEntityType), nullable=False)

    # Checkpoint data
    last_sync_token = Column(String(255))
    last_sync_timestamp = Column(DateTime(timezone=True))
    server_timestamp = Column(DateTime(timezone=True))

    # Stats
    records_synced = Column(Integer, default=0)
    last_full_sync = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("device_id", "entity_type", name="uq_sync_checkpoint_device_entity"),
    )


class SyncQueue(Base):
    """Pending sync operations queue"""
    __tablename__ = "sync_queue"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("mobile_devices.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)

    # Operation details
    operation_type = Column(Enum(SyncOperationType), nullable=False)
    entity_type = Column(Enum(SyncEntityType), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    entity_data = Column(JSONB)  # Encrypted entity data

    # Status tracking
    status = Column(Enum(SyncStatus), default=SyncStatus.PENDING)
    retries = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    error_message = Column(Text)

    # Conflict resolution
    local_version = Column(Integer)
    server_version = Column(Integer)
    conflict_data = Column(JSONB)  # Server data if conflict
    resolution = Column(String(50))  # "local_wins", "server_wins", "merged"

    # Timing
    created_at = Column(DateTime(timezone=True), default=func.now())
    processed_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_sync_queue_status", "status"),
        Index("ix_sync_queue_device", "device_id", "status"),
    )


class SyncConflict(Base):
    """Sync conflicts for manual resolution"""
    __tablename__ = "sync_conflicts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    sync_queue_id = Column(UUID(as_uuid=True), ForeignKey("sync_queue.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Conflict details
    entity_type = Column(Enum(SyncEntityType), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    local_data = Column(JSONB, nullable=False)
    server_data = Column(JSONB, nullable=False)
    merged_data = Column(JSONB)

    # Resolution
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True))
    resolved_by = Column(UUID(as_uuid=True))
    resolution_type = Column(String(50))

    created_at = Column(DateTime(timezone=True), default=func.now())


# ==================== Wearable Integration Models ====================

class WearableDevice(Base):
    """Connected wearable devices"""
    __tablename__ = "wearable_devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    mobile_device_id = Column(UUID(as_uuid=True), ForeignKey("mobile_devices.id"), index=True)

    # Device info
    wearable_type = Column(Enum(WearableType), nullable=False)
    device_name = Column(String(255))
    model = Column(String(100))
    manufacturer = Column(String(100))
    serial_number = Column(String(255))
    firmware_version = Column(String(50))

    # Connection
    is_connected = Column(Boolean, default=True)
    connection_type = Column(String(50))  # "bluetooth", "wifi", "cloud"
    last_connected_at = Column(DateTime(timezone=True))

    # Data sources
    data_sources = Column(ARRAY(String))  # ["heart_rate", "steps", "sleep"]
    sync_enabled = Column(Boolean, default=True)
    auto_sync = Column(Boolean, default=True)
    sync_frequency_minutes = Column(Integer, default=15)

    # OAuth tokens for cloud-connected devices
    access_token = Column(Text)  # Encrypted
    refresh_token = Column(Text)  # Encrypted
    token_expires_at = Column(DateTime(timezone=True))

    # Status
    battery_level = Column(Integer)  # 0-100
    is_charging = Column(Boolean)

    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    health_metrics = relationship("HealthMetric", back_populates="wearable", cascade="all, delete-orphan")


class HealthMetric(Base):
    """Health metrics from wearable devices"""
    __tablename__ = "health_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    wearable_id = Column(UUID(as_uuid=True), ForeignKey("wearable_devices.id"), index=True)

    # Metric details
    metric_type = Column(Enum(HealthMetricType), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)  # "bpm", "steps", "mg/dL", etc.

    # Additional values for complex metrics
    secondary_value = Column(Float)  # e.g., diastolic for BP
    secondary_unit = Column(String(20))
    metadata = Column(JSONB)  # Additional metric-specific data

    # Time range (for aggregated metrics)
    recorded_at = Column(DateTime(timezone=True), nullable=False, index=True)
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))

    # Source
    source = Column(String(100))  # "apple_health", "google_fit", "device_direct"
    source_device_id = Column(String(255))
    is_manual_entry = Column(Boolean, default=False)

    # Quality
    confidence = Column(Float)  # 0-1
    is_anomaly = Column(Boolean, default=False)

    # Clinical flags
    is_abnormal = Column(Boolean, default=False)
    alert_triggered = Column(Boolean, default=False)
    reviewed_by_provider = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), default=func.now())

    # Relationships
    wearable = relationship("WearableDevice", back_populates="health_metrics")

    __table_args__ = (
        Index("ix_health_metric_type_time", "user_id", "metric_type", "recorded_at"),
        Index("ix_health_metric_recorded", "recorded_at"),
    )


class HealthMetricGoal(Base):
    """User health goals for metrics"""
    __tablename__ = "health_metric_goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    metric_type = Column(Enum(HealthMetricType), nullable=False)
    target_value = Column(Float, nullable=False)
    target_unit = Column(String(20), nullable=False)
    frequency = Column(String(20), default="daily")  # "daily", "weekly", "monthly"

    # Range (optional)
    min_value = Column(Float)
    max_value = Column(Float)

    # Status
    is_active = Column(Boolean, default=True)
    start_date = Column(Date)
    end_date = Column(Date)

    # Set by
    set_by_provider = Column(Boolean, default=False)
    provider_id = Column(UUID(as_uuid=True))
    notes = Column(Text)

    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "metric_type", name="uq_health_goal_user_metric"),
    )


# ==================== Mobile Analytics Models ====================

class AppUsageEvent(Base):
    """Mobile app usage analytics"""
    __tablename__ = "app_usage_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("mobile_devices.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), index=True)
    session_id = Column(UUID(as_uuid=True), index=True)

    # Event details
    event_name = Column(String(100), nullable=False, index=True)
    event_category = Column(String(50))  # "navigation", "action", "error"
    screen_name = Column(String(100))
    action = Column(String(100))
    label = Column(String(255))
    value = Column(Float)

    # Context
    properties = Column(JSONB)  # Event-specific data
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())

    # Performance
    duration_ms = Column(Integer)
    memory_usage_mb = Column(Float)
    cpu_usage_percent = Column(Float)
    network_type = Column(String(20))  # "wifi", "cellular", "offline"

    created_at = Column(DateTime(timezone=True), default=func.now())

    __table_args__ = (
        Index("ix_app_usage_event_name", "event_name"),
        Index("ix_app_usage_timestamp", "timestamp"),
    )


class AppCrashReport(Base):
    """Mobile app crash reports"""
    __tablename__ = "app_crash_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("mobile_devices.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True))
    session_id = Column(UUID(as_uuid=True))

    # Crash details
    crash_type = Column(String(50), nullable=False)  # "exception", "anr", "native"
    exception_type = Column(String(255))
    exception_message = Column(Text)
    stack_trace = Column(Text)

    # Context
    screen_name = Column(String(100))
    app_state = Column(JSONB)  # App state at crash time
    user_actions = Column(JSONB)  # Breadcrumb of recent actions

    # Device state
    memory_free_mb = Column(Float)
    disk_free_mb = Column(Float)
    battery_level = Column(Integer)
    is_charging = Column(Boolean)
    network_type = Column(String(20))

    # App info
    app_version = Column(String(20))
    app_build = Column(String(20))

    # Tracking
    is_resolved = Column(Boolean, default=False)
    resolved_in_version = Column(String(20))
    issue_id = Column(String(100))  # External issue tracker ID

    occurred_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())

    __table_args__ = (
        Index("ix_crash_report_type", "crash_type"),
        Index("ix_crash_report_version", "app_version"),
    )


# ==================== Mobile Audit Log ====================

class MobileAuditLog(Base):
    """Mobile-specific audit logging"""
    __tablename__ = "mobile_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), index=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("mobile_devices.id"), index=True)
    session_id = Column(UUID(as_uuid=True))

    # Action details
    action = Column(String(100), nullable=False, index=True)
    action_category = Column(String(50), nullable=False)  # "auth", "data", "sync", "notification"
    action_description = Column(Text)

    # Target
    entity_type = Column(String(50))
    entity_id = Column(UUID(as_uuid=True))

    # Context
    details = Column(JSONB)
    ip_address = Column(INET)
    location = Column(JSONB)  # {latitude, longitude, city, country}

    # Status
    success = Column(Boolean, default=True)
    error_message = Column(Text)

    # HIPAA compliance
    phi_accessed = Column(Boolean, default=False)
    phi_types = Column(ARRAY(String))  # Types of PHI accessed

    created_at = Column(DateTime(timezone=True), default=func.now())

    __table_args__ = (
        Index("ix_mobile_audit_action", "action"),
        Index("ix_mobile_audit_category", "action_category"),
        Index("ix_mobile_audit_created", "created_at"),
    )
