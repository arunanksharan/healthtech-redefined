"""
Mobile Applications Platform Schemas
EPIC-016: Pydantic schemas for mobile application API
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, validator


# ==================== Enum Schemas ====================

class DevicePlatformSchema(str, Enum):
    IOS = "ios"
    ANDROID = "android"
    WEB = "web"
    WATCHOS = "watchos"
    WEAROS = "wearos"


class DeviceStatusSchema(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


class NotificationTypeSchema(str, Enum):
    APPOINTMENT_REMINDER = "appointment_reminder"
    MEDICATION_REMINDER = "medication_reminder"
    LAB_RESULT = "lab_result"
    MESSAGE = "message"
    HEALTH_ALERT = "health_alert"
    HEALTH_TIP = "health_tip"
    EMERGENCY = "emergency"
    SYSTEM = "system"
    PROMOTIONAL = "promotional"


class NotificationPrioritySchema(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationStatusSchema(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    EXPIRED = "expired"


class SyncEntityTypeSchema(str, Enum):
    PATIENT = "patient"
    APPOINTMENT = "appointment"
    HEALTH_RECORD = "health_record"
    MEDICATION = "medication"
    MESSAGE = "message"
    DOCUMENT = "document"
    PROVIDER = "provider"
    CARE_TEAM = "care_team"
    NOTIFICATION = "notification"


class SyncOperationTypeSchema(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class SyncStatusSchema(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"


class WearableTypeSchema(str, Enum):
    APPLE_WATCH = "apple_watch"
    WEAR_OS = "wear_os"
    FITBIT = "fitbit"
    GARMIN = "garmin"
    SAMSUNG_GALAXY = "samsung_galaxy"
    WHOOP = "whoop"
    OURA = "oura"
    OTHER = "other"


class HealthMetricTypeSchema(str, Enum):
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


class SessionStatusSchema(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    LOCKED = "locked"


class BiometricTypeSchema(str, Enum):
    FACE_ID = "face_id"
    TOUCH_ID = "touch_id"
    FINGERPRINT = "fingerprint"
    IRIS = "iris"
    VOICE = "voice"


class AppUpdateChannelSchema(str, Enum):
    PRODUCTION = "production"
    STAGING = "staging"
    BETA = "beta"
    ALPHA = "alpha"


# ==================== Device Schemas ====================

class DeviceRegister(BaseModel):
    """Register a new mobile device"""
    device_id: str = Field(..., description="Unique device identifier")
    device_token: Optional[str] = Field(None, description="Push notification token")
    platform: DevicePlatformSchema
    platform_version: Optional[str] = None
    device_model: Optional[str] = None
    device_name: Optional[str] = None
    app_version: str
    app_build: Optional[str] = None
    bundle_id: Optional[str] = None
    locale: Optional[str] = "en"
    timezone: Optional[str] = None
    biometric_enabled: Optional[bool] = False
    biometric_type: Optional[BiometricTypeSchema] = None


class DeviceUpdate(BaseModel):
    """Update device information"""
    device_token: Optional[str] = None
    platform_version: Optional[str] = None
    device_name: Optional[str] = None
    app_version: Optional[str] = None
    app_build: Optional[str] = None
    locale: Optional[str] = None
    timezone: Optional[str] = None
    notification_enabled: Optional[bool] = None
    notification_preferences: Optional[Dict[str, Any]] = None
    biometric_enabled: Optional[bool] = None
    biometric_type: Optional[BiometricTypeSchema] = None


class DeviceSecurityUpdate(BaseModel):
    """Update device security flags"""
    is_jailbroken: Optional[bool] = None
    is_rooted: Optional[bool] = None
    device_fingerprint: Optional[str] = None


class DeviceResponse(BaseModel):
    """Device response"""
    id: UUID
    device_id: str
    platform: str
    platform_version: Optional[str]
    device_model: Optional[str]
    device_name: Optional[str]
    app_version: str
    app_build: Optional[str]
    status: str
    notification_enabled: bool
    biometric_enabled: bool
    biometric_type: Optional[str]
    locale: str
    timezone: Optional[str]
    registered_at: datetime
    last_active_at: datetime
    last_sync_at: Optional[datetime]

    class Config:
        from_attributes = True


class DeviceListResponse(BaseModel):
    """List of devices"""
    devices: List[DeviceResponse]
    total: int


# ==================== Session Schemas ====================

class SessionCreate(BaseModel):
    """Create a new mobile session"""
    device_id: UUID
    auth_method: str = Field(..., description="Authentication method used")
    biometric_verified: Optional[bool] = False
    mfa_verified: Optional[bool] = False


class SessionResponse(BaseModel):
    """Session response"""
    id: UUID
    session_token: str
    refresh_token: Optional[str]
    status: str
    auth_method: str
    biometric_verified: bool
    mfa_verified: bool
    started_at: datetime
    last_activity_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True


class SessionRefresh(BaseModel):
    """Refresh session tokens"""
    refresh_token: str


class BiometricAuthRequest(BaseModel):
    """Biometric authentication request"""
    device_id: UUID
    biometric_type: BiometricTypeSchema
    challenge: Optional[str] = None


class BiometricAuthResponse(BaseModel):
    """Biometric authentication response"""
    success: bool
    session_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    error: Optional[str] = None


# ==================== Push Notification Schemas ====================

class NotificationSend(BaseModel):
    """Send a push notification"""
    user_id: UUID
    device_id: Optional[UUID] = None
    notification_type: NotificationTypeSchema
    priority: Optional[NotificationPrioritySchema] = NotificationPrioritySchema.NORMAL
    title: str = Field(..., max_length=255)
    body: str
    subtitle: Optional[str] = None
    image_url: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    action_url: Optional[str] = None
    actions: Optional[List[Dict[str, str]]] = None
    scheduled_at: Optional[datetime] = None
    ttl: Optional[int] = None  # Time to live in seconds
    collapse_key: Optional[str] = None


class NotificationBulkSend(BaseModel):
    """Send notifications to multiple users"""
    user_ids: List[UUID]
    notification_type: NotificationTypeSchema
    priority: Optional[NotificationPrioritySchema] = NotificationPrioritySchema.NORMAL
    title: str
    body: str
    data: Optional[Dict[str, Any]] = None
    action_url: Optional[str] = None


class NotificationResponse(BaseModel):
    """Notification response"""
    id: UUID
    notification_type: str
    priority: str
    title: str
    body: str
    subtitle: Optional[str]
    image_url: Optional[str]
    data: Optional[Dict[str, Any]]
    action_url: Optional[str]
    status: str
    scheduled_at: Optional[datetime]
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]
    opened: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """List of notifications"""
    notifications: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    page_size: int


class NotificationPreferenceUpdate(BaseModel):
    """Update notification preferences"""
    push_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    type_preferences: Optional[Dict[str, Dict[str, Any]]] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None  # "22:00"
    quiet_hours_end: Optional[str] = None  # "07:00"
    quiet_hours_days: Optional[List[int]] = None
    sound_enabled: Optional[bool] = None
    vibration_enabled: Optional[bool] = None
    custom_sound: Optional[str] = None


class NotificationPreferenceResponse(BaseModel):
    """Notification preferences response"""
    push_enabled: bool
    email_enabled: bool
    sms_enabled: bool
    type_preferences: Dict[str, Any]
    quiet_hours_enabled: bool
    quiet_hours_start: Optional[str]
    quiet_hours_end: Optional[str]
    quiet_hours_days: Optional[List[int]]
    sound_enabled: bool
    vibration_enabled: bool
    custom_sound: Optional[str]

    class Config:
        from_attributes = True


# ==================== Sync Schemas ====================

class SyncRequest(BaseModel):
    """Request sync for entities"""
    entity_types: List[SyncEntityTypeSchema]
    since_token: Optional[str] = None
    full_sync: Optional[bool] = False


class SyncChange(BaseModel):
    """A single sync change"""
    operation: SyncOperationTypeSchema
    entity_type: SyncEntityTypeSchema
    entity_id: UUID
    data: Optional[Dict[str, Any]] = None
    version: int
    timestamp: datetime


class SyncResponse(BaseModel):
    """Sync response with changes"""
    changes: List[SyncChange]
    next_token: str
    has_more: bool
    server_timestamp: datetime


class SyncPush(BaseModel):
    """Push local changes to server"""
    operations: List[SyncChange]


class SyncPushResult(BaseModel):
    """Result of sync push"""
    successful: List[UUID]
    failed: List[Dict[str, Any]]
    conflicts: List[Dict[str, Any]]


class SyncConflictResolve(BaseModel):
    """Resolve a sync conflict"""
    conflict_id: UUID
    resolution: str = Field(..., description="local_wins, server_wins, or merged")
    merged_data: Optional[Dict[str, Any]] = None


class SyncStatusResponse(BaseModel):
    """Sync status for device"""
    entity_type: str
    last_sync_token: Optional[str]
    last_sync_timestamp: Optional[datetime]
    records_synced: int
    pending_operations: int


# ==================== Wearable Schemas ====================

class WearableConnect(BaseModel):
    """Connect a wearable device"""
    wearable_type: WearableTypeSchema
    device_name: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    data_sources: Optional[List[str]] = None
    access_token: Optional[str] = None  # For cloud-connected
    refresh_token: Optional[str] = None


class WearableUpdate(BaseModel):
    """Update wearable settings"""
    device_name: Optional[str] = None
    sync_enabled: Optional[bool] = None
    auto_sync: Optional[bool] = None
    sync_frequency_minutes: Optional[int] = None
    data_sources: Optional[List[str]] = None


class WearableResponse(BaseModel):
    """Wearable device response"""
    id: UUID
    wearable_type: str
    device_name: Optional[str]
    model: Optional[str]
    manufacturer: Optional[str]
    is_connected: bool
    last_connected_at: Optional[datetime]
    data_sources: Optional[List[str]]
    sync_enabled: bool
    auto_sync: bool
    sync_frequency_minutes: int
    battery_level: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class WearableListResponse(BaseModel):
    """List of wearables"""
    wearables: List[WearableResponse]
    total: int


# ==================== Health Metric Schemas ====================

class HealthMetricRecord(BaseModel):
    """Record a health metric"""
    metric_type: HealthMetricTypeSchema
    value: float
    unit: str
    secondary_value: Optional[float] = None
    secondary_unit: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    recorded_at: datetime
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    source: Optional[str] = None
    is_manual_entry: Optional[bool] = False
    wearable_id: Optional[UUID] = None


class HealthMetricBulkRecord(BaseModel):
    """Record multiple health metrics"""
    metrics: List[HealthMetricRecord]


class HealthMetricResponse(BaseModel):
    """Health metric response"""
    id: UUID
    metric_type: str
    value: float
    unit: str
    secondary_value: Optional[float]
    secondary_unit: Optional[str]
    metadata: Optional[Dict[str, Any]]
    recorded_at: datetime
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    source: Optional[str]
    is_manual_entry: bool
    is_abnormal: bool
    confidence: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class HealthMetricListResponse(BaseModel):
    """List of health metrics"""
    metrics: List[HealthMetricResponse]
    total: int
    page: int
    page_size: int


class HealthMetricSummary(BaseModel):
    """Summary of health metrics"""
    metric_type: str
    latest_value: float
    unit: str
    min_value: float
    max_value: float
    avg_value: float
    count: int
    period: str
    trend: Optional[str]  # "up", "down", "stable"
    goal_progress: Optional[float]


class HealthMetricGoalCreate(BaseModel):
    """Create a health metric goal"""
    metric_type: HealthMetricTypeSchema
    target_value: float
    target_unit: str
    frequency: Optional[str] = "daily"
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None


class HealthMetricGoalResponse(BaseModel):
    """Health metric goal response"""
    id: UUID
    metric_type: str
    target_value: float
    target_unit: str
    frequency: str
    min_value: Optional[float]
    max_value: Optional[float]
    is_active: bool
    start_date: Optional[date]
    end_date: Optional[date]
    current_progress: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Analytics Schemas ====================

class AppUsageEventRecord(BaseModel):
    """Record app usage event"""
    event_name: str
    event_category: Optional[str] = None
    screen_name: Optional[str] = None
    action: Optional[str] = None
    label: Optional[str] = None
    value: Optional[float] = None
    properties: Optional[Dict[str, Any]] = None
    duration_ms: Optional[int] = None
    timestamp: Optional[datetime] = None


class AppUsageEventBatch(BaseModel):
    """Batch of app usage events"""
    events: List[AppUsageEventRecord]
    session_id: Optional[UUID] = None


class AppCrashReportCreate(BaseModel):
    """Report an app crash"""
    crash_type: str
    exception_type: Optional[str] = None
    exception_message: Optional[str] = None
    stack_trace: Optional[str] = None
    screen_name: Optional[str] = None
    app_state: Optional[Dict[str, Any]] = None
    user_actions: Optional[List[Dict[str, Any]]] = None
    memory_free_mb: Optional[float] = None
    disk_free_mb: Optional[float] = None
    battery_level: Optional[int] = None
    is_charging: Optional[bool] = None
    network_type: Optional[str] = None
    app_version: str
    app_build: Optional[str] = None
    occurred_at: datetime


class AppVersionCheck(BaseModel):
    """Check for app updates"""
    current_version: str
    platform: DevicePlatformSchema
    update_channel: Optional[AppUpdateChannelSchema] = AppUpdateChannelSchema.PRODUCTION


class AppVersionResponse(BaseModel):
    """App version check response"""
    latest_version: str
    minimum_version: str
    update_available: bool
    force_update: bool
    release_notes: Optional[str]
    download_url: Optional[str]


# ==================== Deep Link Schemas ====================

class DeepLinkCreate(BaseModel):
    """Create a deep link"""
    target_type: str  # "appointment", "message", "record", etc.
    target_id: UUID
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class DeepLinkResponse(BaseModel):
    """Deep link response"""
    deep_link: str
    universal_link: str
    target_type: str
    target_id: UUID
    expires_at: Optional[datetime]


class DeepLinkResolve(BaseModel):
    """Resolve a deep link"""
    link: str


class DeepLinkResolveResponse(BaseModel):
    """Resolved deep link"""
    target_type: str
    target_id: UUID
    metadata: Optional[Dict[str, Any]]
    valid: bool
    error: Optional[str]


# ==================== Storage Schemas ====================

class StorageInfoResponse(BaseModel):
    """Local storage information"""
    total_size_bytes: int
    cache_size_bytes: int
    records_count: int
    available_space_bytes: int
    by_entity: Dict[str, int]


class CacheClearRequest(BaseModel):
    """Clear cache request"""
    entity_types: Optional[List[SyncEntityTypeSchema]] = None
    older_than_days: Optional[int] = None
    clear_all: Optional[bool] = False
