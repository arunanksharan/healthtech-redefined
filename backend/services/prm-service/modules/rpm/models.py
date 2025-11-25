"""
Remote Patient Monitoring (RPM) Database Models

SQLAlchemy models for persistent storage of RPM data:
- Device registry and management
- Device readings and measurements
- Alert rules and notifications
- Care protocols and automation
- RPM billing and enrollment
- Patient engagement tracking

EPIC-019: Remote Patient Monitoring
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Float, DateTime, Date,
    ForeignKey, JSON, Enum as SQLEnum, Index, UniqueConstraint,
    CheckConstraint, Numeric
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
import uuid
import enum

from shared.database import Base


# ============================================================================
# ENUMS
# ============================================================================

class DeviceType(str, enum.Enum):
    """Types of RPM devices."""
    BLOOD_PRESSURE_MONITOR = "blood_pressure_monitor"
    GLUCOMETER = "glucometer"
    PULSE_OXIMETER = "pulse_oximeter"
    WEIGHT_SCALE = "weight_scale"
    THERMOMETER = "thermometer"
    ECG_MONITOR = "ecg_monitor"
    SPIROMETER = "spirometer"
    ACTIVITY_TRACKER = "activity_tracker"
    CONTINUOUS_GLUCOSE_MONITOR = "continuous_glucose_monitor"
    HEART_RATE_MONITOR = "heart_rate_monitor"
    SLEEP_TRACKER = "sleep_tracker"
    SMART_WATCH = "smart_watch"
    OTHER = "other"


class DeviceStatus(str, enum.Enum):
    """Device operational status."""
    UNREGISTERED = "unregistered"
    REGISTERED = "registered"
    PAIRED = "paired"
    ACTIVE = "active"
    LOW_BATTERY = "low_battery"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    DEACTIVATED = "deactivated"
    LOST = "lost"


class DeviceVendor(str, enum.Enum):
    """Supported device vendors."""
    WITHINGS = "withings"
    OMRON = "omron"
    IHEALTH = "ihealth"
    APPLE_HEALTH = "apple_health"
    GOOGLE_FIT = "google_fit"
    FITBIT = "fitbit"
    GARMIN = "garmin"
    DEXCOM = "dexcom"
    ABBOTT_LIBRE = "abbott_libre"
    MANUAL_ENTRY = "manual_entry"
    BLE_DIRECT = "ble_direct"
    OTHER = "other"


class ReadingType(str, enum.Enum):
    """Types of health readings."""
    BLOOD_PRESSURE_SYSTOLIC = "blood_pressure_systolic"
    BLOOD_PRESSURE_DIASTOLIC = "blood_pressure_diastolic"
    HEART_RATE = "heart_rate"
    BLOOD_GLUCOSE = "blood_glucose"
    OXYGEN_SATURATION = "oxygen_saturation"
    BODY_WEIGHT = "body_weight"
    BODY_TEMPERATURE = "body_temperature"
    RESPIRATORY_RATE = "respiratory_rate"
    STEPS = "steps"
    DISTANCE = "distance"
    CALORIES_BURNED = "calories_burned"
    SLEEP_DURATION = "sleep_duration"
    SLEEP_QUALITY = "sleep_quality"
    HRV = "hrv"
    ECG = "ecg"
    SPIROMETRY_FEV1 = "spirometry_fev1"
    SPIROMETRY_FVC = "spirometry_fvc"
    PEAK_FLOW = "peak_flow"
    PAIN_LEVEL = "pain_level"
    MOOD = "mood"


class ReadingStatus(str, enum.Enum):
    """Status of a device reading."""
    PENDING = "pending"
    VALIDATED = "validated"
    FLAGGED = "flagged"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"


class AlertSeverity(str, enum.Enum):
    """Alert severity levels."""
    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, enum.Enum):
    """Alert lifecycle status."""
    TRIGGERED = "triggered"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    AUTO_RESOLVED = "auto_resolved"


class AlertType(str, enum.Enum):
    """Types of alerts."""
    THRESHOLD_BREACH = "threshold_breach"
    TREND_ANOMALY = "trend_anomaly"
    PATTERN_DEVIATION = "pattern_deviation"
    MISSED_READING = "missed_reading"
    DEVICE_OFFLINE = "device_offline"
    CRITICAL_VALUE = "critical_value"
    PROTOCOL_VIOLATION = "protocol_violation"
    CARE_GAP = "care_gap"


class ProtocolStatus(str, enum.Enum):
    """Care protocol status."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    TERMINATED = "terminated"


class ProtocolTriggerType(str, enum.Enum):
    """Types of protocol triggers."""
    THRESHOLD = "threshold"
    TREND = "trend"
    SCHEDULE = "schedule"
    MANUAL = "manual"
    AI_RECOMMENDATION = "ai_recommendation"


class ProtocolActionType(str, enum.Enum):
    """Types of protocol actions."""
    SEND_MESSAGE = "send_message"
    MAKE_CALL = "make_call"
    SCHEDULE_APPOINTMENT = "schedule_appointment"
    ALERT_PROVIDER = "alert_provider"
    ADJUST_MEDICATION = "adjust_medication"
    ORDER_LAB = "order_lab"
    UPDATE_CARE_PLAN = "update_care_plan"
    ESCALATE = "escalate"


class EnrollmentStatus(str, enum.Enum):
    """RPM enrollment status."""
    PENDING = "pending"
    ENROLLED = "enrolled"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    WITHDRAWN = "withdrawn"
    DISCHARGED = "discharged"


class BillingCodeType(str, enum.Enum):
    """RPM billing CPT codes."""
    CPT_99453 = "99453"  # Device setup
    CPT_99454 = "99454"  # Device supply with daily monitoring (16+ days)
    CPT_99457 = "99457"  # First 20 min clinical time
    CPT_99458 = "99458"  # Additional 20 min clinical time
    CPT_99091 = "99091"  # Data interpretation (deprecated)


class OutreachChannel(str, enum.Enum):
    """Patient outreach channels."""
    SMS = "sms"
    VOICE_CALL = "voice_call"
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    PUSH_NOTIFICATION = "push"
    IN_APP = "in_app"


# ============================================================================
# DEVICE MODELS
# ============================================================================

class RPMDevice(Base):
    """A registered RPM device."""
    __tablename__ = "rpm_devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Device identification
    serial_number = Column(String(100), nullable=True)
    mac_address = Column(String(50), nullable=True)
    device_identifier = Column(String(200), nullable=False)  # Unique per vendor
    vendor = Column(SQLEnum(DeviceVendor), nullable=False)
    device_type = Column(SQLEnum(DeviceType), nullable=False)
    model = Column(String(200), nullable=True)
    firmware_version = Column(String(50), nullable=True)

    # FHIR reference
    fhir_device_id = Column(UUID(as_uuid=True), nullable=True)

    # Status
    status = Column(SQLEnum(DeviceStatus), default=DeviceStatus.REGISTERED)
    battery_level = Column(Integer, nullable=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    last_reading_at = Column(DateTime(timezone=True), nullable=True)

    # OAuth for vendor APIs
    oauth_access_token = Column(Text, nullable=True)
    oauth_refresh_token = Column(Text, nullable=True)
    oauth_token_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assignments = relationship("DeviceAssignment", back_populates="device", cascade="all, delete-orphan")
    readings = relationship("DeviceReading", back_populates="device", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("tenant_id", "vendor", "device_identifier", name="uq_rpm_device_identifier"),
        Index("idx_rpm_devices_tenant_status", "tenant_id", "status"),
        Index("idx_rpm_devices_vendor", "vendor"),
    )


class DeviceAssignment(Base):
    """Assignment of a device to a patient."""
    __tablename__ = "rpm_device_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    device_id = Column(UUID(as_uuid=True), ForeignKey("rpm_devices.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("rpm_enrollments.id"), nullable=True)

    # Assignment period
    assigned_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    assigned_by = Column(UUID(as_uuid=True), nullable=False)
    unassigned_at = Column(DateTime(timezone=True), nullable=True)
    unassigned_by = Column(UUID(as_uuid=True), nullable=True)
    is_active = Column(Boolean, default=True)

    # Configuration
    reading_frequency = Column(String(50), default="daily")  # daily, twice_daily, as_needed
    target_readings_per_day = Column(Integer, default=1)
    reminder_times = Column(ARRAY(String), default=list)

    # Metadata
    notes = Column(Text, nullable=True)
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    device = relationship("RPMDevice", back_populates="assignments")
    enrollment = relationship("RPMEnrollment", back_populates="device_assignments")

    __table_args__ = (
        Index("idx_device_assignments_patient_active", "patient_id", "is_active"),
        Index("idx_device_assignments_device_active", "device_id", "is_active"),
    )


# ============================================================================
# READING MODELS
# ============================================================================

class DeviceReading(Base):
    """A single device reading/measurement."""
    __tablename__ = "rpm_device_readings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Source
    device_id = Column(UUID(as_uuid=True), ForeignKey("rpm_devices.id"), nullable=True)
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("rpm_enrollments.id"), nullable=True)

    # Reading data
    reading_type = Column(SQLEnum(ReadingType), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    secondary_value = Column(Float, nullable=True)  # For BP diastolic, etc.
    secondary_unit = Column(String(50), nullable=True)

    # Timing
    measured_at = Column(DateTime(timezone=True), nullable=False)
    received_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    timezone = Column(String(50), nullable=True)

    # Status
    status = Column(SQLEnum(ReadingStatus), default=ReadingStatus.PENDING)
    is_manual = Column(Boolean, default=False)
    source = Column(String(100), nullable=True)  # withings, apple_health, manual, etc.

    # Validation
    is_valid = Column(Boolean, default=True)
    validation_errors = Column(ARRAY(String), default=list)
    flagged_reason = Column(String(500), nullable=True)

    # FHIR reference
    fhir_observation_id = Column(UUID(as_uuid=True), nullable=True)

    # Context
    context = Column(JSONB, default=dict)  # meal, exercise, position, etc.
    raw_data = Column(JSONB, default=dict)
    metadata = Column(JSONB, default=dict)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    device = relationship("RPMDevice", back_populates="readings")
    enrollment = relationship("RPMEnrollment", back_populates="readings")
    alerts = relationship("RPMAlert", back_populates="reading")

    __table_args__ = (
        Index("idx_readings_patient_type_time", "patient_id", "reading_type", "measured_at"),
        Index("idx_readings_tenant_time", "tenant_id", "measured_at"),
        Index("idx_readings_enrollment_time", "enrollment_id", "measured_at"),
        Index("idx_readings_device_time", "device_id", "measured_at"),
    )


class ReadingBatch(Base):
    """Batch of readings for bulk processing."""
    __tablename__ = "rpm_reading_batches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Batch info
    source = Column(String(100), nullable=False)  # webhook, sync, import
    source_reference = Column(String(200), nullable=True)
    total_readings = Column(Integer, default=0)
    processed_readings = Column(Integer, default=0)
    failed_readings = Column(Integer, default=0)
    duplicate_readings = Column(Integer, default=0)

    # Status
    status = Column(String(50), default="pending")
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    # Metadata
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("idx_reading_batches_tenant_status", "tenant_id", "status"),
    )


class DataQualityMetric(Base):
    """Data quality metrics per patient/device."""
    __tablename__ = "rpm_data_quality_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Context
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("rpm_devices.id"), nullable=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # Metrics
    expected_readings = Column(Integer, default=0)
    actual_readings = Column(Integer, default=0)
    valid_readings = Column(Integer, default=0)
    flagged_readings = Column(Integer, default=0)
    compliance_rate = Column(Float, default=0.0)  # actual/expected * 100

    # Connectivity
    days_with_data = Column(Integer, default=0)
    longest_gap_hours = Column(Float, default=0.0)
    avg_reading_interval_hours = Column(Float, nullable=True)

    # Quality scores
    data_quality_score = Column(Float, default=100.0)  # 0-100
    consistency_score = Column(Float, default=100.0)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("patient_id", "device_id", "period_start", "period_end",
                         name="uq_data_quality_period"),
        Index("idx_data_quality_patient_period", "patient_id", "period_start"),
    )


# ============================================================================
# ALERT MODELS
# ============================================================================

class AlertRule(Base):
    """Configurable alert rules."""
    __tablename__ = "rpm_alert_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Rule definition
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    reading_type = Column(SQLEnum(ReadingType), nullable=True)  # null = applies to all
    is_global = Column(Boolean, default=False)  # Applies to all patients

    # Thresholds
    threshold_low = Column(Float, nullable=True)
    threshold_high = Column(Float, nullable=True)
    threshold_critical_low = Column(Float, nullable=True)
    threshold_critical_high = Column(Float, nullable=True)

    # Trend detection
    trend_direction = Column(String(20), nullable=True)  # up, down
    trend_threshold_percent = Column(Float, nullable=True)
    trend_window_hours = Column(Integer, nullable=True)

    # Alert configuration
    severity = Column(SQLEnum(AlertSeverity), default=AlertSeverity.MEDIUM)
    alert_type = Column(SQLEnum(AlertType), default=AlertType.THRESHOLD_BREACH)
    cooldown_minutes = Column(Integer, default=60)  # Prevent duplicate alerts

    # Routing
    notify_provider = Column(Boolean, default=True)
    notify_patient = Column(Boolean, default=False)
    notify_care_team = Column(Boolean, default=True)
    escalation_minutes = Column(Integer, default=30)

    # Status
    is_active = Column(Boolean, default=True)
    conditions = Column(JSONB, default=dict)  # Complex conditions
    metadata = Column(JSONB, default=dict)

    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    alerts = relationship("RPMAlert", back_populates="rule")
    patient_rules = relationship("PatientAlertRule", back_populates="rule", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_alert_rules_tenant_type", "tenant_id", "reading_type"),
        Index("idx_alert_rules_active", "is_active"),
    )


class PatientAlertRule(Base):
    """Patient-specific alert rule overrides."""
    __tablename__ = "rpm_patient_alert_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    rule_id = Column(UUID(as_uuid=True), ForeignKey("rpm_alert_rules.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("rpm_enrollments.id"), nullable=True)

    # Overrides
    threshold_low = Column(Float, nullable=True)
    threshold_high = Column(Float, nullable=True)
    threshold_critical_low = Column(Float, nullable=True)
    threshold_critical_high = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    is_muted = Column(Boolean, default=False)
    muted_until = Column(DateTime(timezone=True), nullable=True)

    # Provider approval for custom thresholds
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    rule = relationship("AlertRule", back_populates="patient_rules")

    __table_args__ = (
        UniqueConstraint("rule_id", "patient_id", name="uq_patient_rule"),
        Index("idx_patient_rules_patient", "patient_id"),
    )


class RPMAlert(Base):
    """Generated alerts from readings."""
    __tablename__ = "rpm_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Context
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("rpm_enrollments.id"), nullable=True)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("rpm_alert_rules.id"), nullable=True)
    reading_id = Column(UUID(as_uuid=True), ForeignKey("rpm_device_readings.id"), nullable=True)

    # Alert details
    alert_type = Column(SQLEnum(AlertType), nullable=False)
    severity = Column(SQLEnum(AlertSeverity), nullable=False)
    status = Column(SQLEnum(AlertStatus), default=AlertStatus.TRIGGERED)

    # Content
    title = Column(String(300), nullable=False)
    message = Column(Text, nullable=False)
    reading_value = Column(Float, nullable=True)
    threshold_value = Column(Float, nullable=True)
    reading_type = Column(SQLEnum(ReadingType), nullable=True)

    # AI insights
    ai_analysis = Column(Text, nullable=True)
    ai_recommendation = Column(Text, nullable=True)
    ai_confidence = Column(Float, nullable=True)

    # Timestamps
    triggered_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(UUID(as_uuid=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(UUID(as_uuid=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Escalation
    escalated_at = Column(DateTime(timezone=True), nullable=True)
    escalation_level = Column(Integer, default=0)
    escalated_to = Column(ARRAY(UUID(as_uuid=True)), default=list)

    # Metadata
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    rule = relationship("AlertRule", back_populates="alerts")
    reading = relationship("DeviceReading", back_populates="alerts")
    notifications = relationship("AlertNotification", back_populates="alert", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_alerts_patient_status", "patient_id", "status"),
        Index("idx_alerts_tenant_severity", "tenant_id", "severity", "status"),
        Index("idx_alerts_triggered_at", "triggered_at"),
    )


class AlertNotification(Base):
    """Notifications sent for alerts."""
    __tablename__ = "rpm_alert_notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    alert_id = Column(UUID(as_uuid=True), ForeignKey("rpm_alerts.id"), nullable=False)
    recipient_id = Column(UUID(as_uuid=True), nullable=False)
    recipient_type = Column(String(50), nullable=False)  # provider, patient, care_team

    channel = Column(SQLEnum(OutreachChannel), nullable=False)
    sent_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="sent")
    external_id = Column(String(200), nullable=True)

    metadata = Column(JSONB, default=dict)

    # Relationships
    alert = relationship("RPMAlert", back_populates="notifications")

    __table_args__ = (
        Index("idx_alert_notifications_alert", "alert_id"),
    )


# ============================================================================
# CARE PROTOCOL MODELS
# ============================================================================

class CareProtocol(Base):
    """Care protocol template."""
    __tablename__ = "rpm_care_protocols"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Protocol definition
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    condition = Column(String(100), nullable=False)  # HTN, DM, CHF, COPD
    version = Column(String(20), default="1.0")

    # Configuration
    duration_days = Column(Integer, nullable=True)
    reading_types = Column(ARRAY(String), default=list)
    target_readings_per_day = Column(Integer, default=1)

    # Status
    status = Column(SQLEnum(ProtocolStatus), default=ProtocolStatus.DRAFT)
    is_template = Column(Boolean, default=False)

    # Evidence & guidelines
    clinical_guidelines = Column(JSONB, default=dict)
    evidence_references = Column(ARRAY(String), default=list)

    # Metadata
    created_by = Column(UUID(as_uuid=True), nullable=False)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    triggers = relationship("ProtocolTrigger", back_populates="protocol", cascade="all, delete-orphan")
    enrollments = relationship("RPMEnrollment", back_populates="protocol")

    __table_args__ = (
        Index("idx_protocols_tenant_condition", "tenant_id", "condition"),
        Index("idx_protocols_status", "status"),
    )


class ProtocolTrigger(Base):
    """Triggers within a care protocol."""
    __tablename__ = "rpm_protocol_triggers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    protocol_id = Column(UUID(as_uuid=True), ForeignKey("rpm_care_protocols.id"), nullable=False)

    # Trigger definition
    name = Column(String(200), nullable=False)
    trigger_type = Column(SQLEnum(ProtocolTriggerType), nullable=False)
    reading_type = Column(SQLEnum(ReadingType), nullable=True)

    # Conditions
    condition_operator = Column(String(20), nullable=True)  # gt, lt, eq, between, trend
    condition_value = Column(Float, nullable=True)
    condition_value_2 = Column(Float, nullable=True)  # For between
    condition_unit = Column(String(50), nullable=True)
    consecutive_count = Column(Integer, default=1)  # Readings in a row

    # Schedule (for scheduled triggers)
    schedule_cron = Column(String(100), nullable=True)
    schedule_days = Column(ARRAY(Integer), default=list)  # 0=Mon, 6=Sun

    # Priority
    priority = Column(Integer, default=50)
    is_active = Column(Boolean, default=True)

    conditions = Column(JSONB, default=dict)  # Complex conditions
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    protocol = relationship("CareProtocol", back_populates="triggers")
    actions = relationship("ProtocolAction", back_populates="trigger", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_triggers_protocol", "protocol_id"),
    )


class ProtocolAction(Base):
    """Actions to execute when triggers fire."""
    __tablename__ = "rpm_protocol_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trigger_id = Column(UUID(as_uuid=True), ForeignKey("rpm_protocol_triggers.id"), nullable=False)

    # Action definition
    action_type = Column(SQLEnum(ProtocolActionType), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Configuration per action type
    message_template = Column(Text, nullable=True)
    channel = Column(SQLEnum(OutreachChannel), nullable=True)
    recipient_type = Column(String(50), nullable=True)  # patient, provider, care_team
    delay_minutes = Column(Integer, default=0)

    # Approval requirements
    requires_approval = Column(Boolean, default=False)
    approval_role = Column(String(50), nullable=True)

    # Order
    sequence = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    config = Column(JSONB, default=dict)
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    trigger = relationship("ProtocolTrigger", back_populates="actions")
    executions = relationship("ProtocolExecution", back_populates="action")

    __table_args__ = (
        Index("idx_actions_trigger", "trigger_id"),
    )


class ProtocolExecution(Base):
    """Execution log for protocol actions."""
    __tablename__ = "rpm_protocol_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("rpm_enrollments.id"), nullable=False)
    action_id = Column(UUID(as_uuid=True), ForeignKey("rpm_protocol_actions.id"), nullable=False)
    trigger_reading_id = Column(UUID(as_uuid=True), ForeignKey("rpm_device_readings.id"), nullable=True)

    # Execution details
    status = Column(String(50), default="pending")  # pending, executing, completed, failed, cancelled
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Approval workflow
    requires_approval = Column(Boolean, default=False)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Result
    success = Column(Boolean, nullable=True)
    error_message = Column(Text, nullable=True)
    result_data = Column(JSONB, default=dict)
    external_reference = Column(String(200), nullable=True)

    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    action = relationship("ProtocolAction", back_populates="executions")

    __table_args__ = (
        Index("idx_executions_enrollment", "enrollment_id"),
        Index("idx_executions_status", "status"),
    )


# ============================================================================
# ENROLLMENT & BILLING MODELS
# ============================================================================

class RPMEnrollment(Base):
    """Patient RPM program enrollment."""
    __tablename__ = "rpm_enrollments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Patient
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    fhir_patient_id = Column(UUID(as_uuid=True), nullable=True)

    # Program
    protocol_id = Column(UUID(as_uuid=True), ForeignKey("rpm_care_protocols.id"), nullable=True)
    program_name = Column(String(200), nullable=False)
    primary_condition = Column(String(100), nullable=False)  # HTN, DM, CHF, COPD
    secondary_conditions = Column(ARRAY(String), default=list)

    # Care team
    primary_provider_id = Column(UUID(as_uuid=True), nullable=False)
    care_team_ids = Column(ARRAY(UUID(as_uuid=True)), default=list)

    # Status
    status = Column(SQLEnum(EnrollmentStatus), default=EnrollmentStatus.PENDING)
    enrolled_at = Column(DateTime(timezone=True), nullable=True)
    activated_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    discharge_reason = Column(String(200), nullable=True)

    # Consent
    consent_obtained = Column(Boolean, default=False)
    consent_date = Column(Date, nullable=True)
    consent_document_id = Column(UUID(as_uuid=True), nullable=True)

    # Goals
    target_readings_per_day = Column(Integer, default=1)
    goals = Column(JSONB, default=dict)

    # Metadata
    enrolled_by = Column(UUID(as_uuid=True), nullable=False)
    notes = Column(Text, nullable=True)
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    protocol = relationship("CareProtocol", back_populates="enrollments")
    device_assignments = relationship("DeviceAssignment", back_populates="enrollment")
    readings = relationship("DeviceReading", back_populates="enrollment")
    billing_events = relationship("RPMBillingEvent", back_populates="enrollment")
    monitoring_periods = relationship("MonitoringPeriod", back_populates="enrollment", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_enrollments_patient_status", "patient_id", "status"),
        Index("idx_enrollments_tenant_condition", "tenant_id", "primary_condition"),
        Index("idx_enrollments_provider", "primary_provider_id"),
    )


class MonitoringPeriod(Base):
    """Monthly monitoring period for billing."""
    __tablename__ = "rpm_monitoring_periods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("rpm_enrollments.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Period
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    period_month = Column(Integer, nullable=False)  # YYYYMM format
    is_current = Column(Boolean, default=True)

    # Device monitoring (99454)
    days_with_readings = Column(Integer, default=0)
    total_readings = Column(Integer, default=0)
    qualifies_for_99454 = Column(Boolean, default=False)  # 16+ days

    # Clinical time (99457, 99458)
    clinical_time_minutes = Column(Integer, default=0)
    interactive_time_minutes = Column(Integer, default=0)
    qualifies_for_99457 = Column(Boolean, default=False)  # 20+ min
    qualifies_for_99458 = Column(Boolean, default=False)  # 40+ min

    # Device setup (99453)
    device_setup_done = Column(Boolean, default=False)
    device_setup_date = Column(Date, nullable=True)

    # Billing status
    billing_generated = Column(Boolean, default=False)
    billing_generated_at = Column(DateTime(timezone=True), nullable=True)
    billing_codes = Column(ARRAY(String), default=list)

    # Audit
    time_entries = Column(JSONB, default=list)  # List of time log entries
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    enrollment = relationship("RPMEnrollment", back_populates="monitoring_periods")

    __table_args__ = (
        UniqueConstraint("enrollment_id", "period_month", name="uq_monitoring_period"),
        Index("idx_monitoring_periods_patient_month", "patient_id", "period_month"),
    )


class ClinicalTimeEntry(Base):
    """Time entries for clinical monitoring."""
    __tablename__ = "rpm_clinical_time_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    monitoring_period_id = Column(UUID(as_uuid=True), ForeignKey("rpm_monitoring_periods.id"), nullable=False)
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("rpm_enrollments.id"), nullable=False)

    # Time tracking
    provider_id = Column(UUID(as_uuid=True), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, nullable=False)

    # Activity
    activity_type = Column(String(100), nullable=False)  # review, call, message, alert_response
    is_interactive = Column(Boolean, default=False)  # Patient interaction
    description = Column(Text, nullable=True)

    # Related entities
    alert_id = Column(UUID(as_uuid=True), ForeignKey("rpm_alerts.id"), nullable=True)
    reading_ids = Column(ARRAY(UUID(as_uuid=True)), default=list)

    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("idx_time_entries_period", "monitoring_period_id"),
        Index("idx_time_entries_provider", "provider_id"),
    )


class RPMBillingEvent(Base):
    """RPM billing events for claims."""
    __tablename__ = "rpm_billing_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("rpm_enrollments.id"), nullable=False)
    monitoring_period_id = Column(UUID(as_uuid=True), ForeignKey("rpm_monitoring_periods.id"), nullable=True)
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Billing code
    cpt_code = Column(SQLEnum(BillingCodeType), nullable=False)
    service_date = Column(Date, nullable=False)
    units = Column(Integer, default=1)

    # Provider
    billing_provider_id = Column(UUID(as_uuid=True), nullable=False)
    supervising_provider_id = Column(UUID(as_uuid=True), nullable=True)

    # Status
    status = Column(String(50), default="pending")  # pending, submitted, paid, denied, adjusted
    claim_id = Column(UUID(as_uuid=True), nullable=True)
    external_claim_id = Column(String(200), nullable=True)

    # Amounts
    billed_amount = Column(Numeric(10, 2), nullable=True)
    allowed_amount = Column(Numeric(10, 2), nullable=True)
    paid_amount = Column(Numeric(10, 2), nullable=True)

    # Supporting documentation
    documentation = Column(JSONB, default=dict)
    days_with_data = Column(Integer, nullable=True)
    clinical_minutes = Column(Integer, nullable=True)

    # Audit
    generated_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    adjudicated_at = Column(DateTime(timezone=True), nullable=True)
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    enrollment = relationship("RPMEnrollment", back_populates="billing_events")

    __table_args__ = (
        Index("idx_billing_events_patient_date", "patient_id", "service_date"),
        Index("idx_billing_events_status", "status"),
        Index("idx_billing_events_claim", "claim_id"),
    )


# ============================================================================
# PATIENT ENGAGEMENT MODELS
# ============================================================================

class PatientReminder(Base):
    """Reminders for patient readings."""
    __tablename__ = "rpm_patient_reminders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("rpm_enrollments.id"), nullable=True)
    device_assignment_id = Column(UUID(as_uuid=True), ForeignKey("rpm_device_assignments.id"), nullable=True)

    # Schedule
    reminder_type = Column(String(50), nullable=False)  # reading, medication, appointment
    reading_type = Column(SQLEnum(ReadingType), nullable=True)
    scheduled_time = Column(String(10), nullable=False)  # HH:MM format
    days_of_week = Column(ARRAY(Integer), default=[0, 1, 2, 3, 4, 5, 6])  # 0=Mon
    timezone = Column(String(50), default="UTC")

    # Channel
    channel = Column(SQLEnum(OutreachChannel), default=OutreachChannel.PUSH_NOTIFICATION)
    message_template = Column(Text, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    last_sent_at = Column(DateTime(timezone=True), nullable=True)
    next_scheduled_at = Column(DateTime(timezone=True), nullable=True)

    # Effectiveness tracking
    reminders_sent = Column(Integer, default=0)
    readings_after_reminder = Column(Integer, default=0)
    response_rate = Column(Float, default=0.0)

    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_reminders_patient_active", "patient_id", "is_active"),
        Index("idx_reminders_next_scheduled", "next_scheduled_at"),
    )


class PatientGoal(Base):
    """Patient health goals."""
    __tablename__ = "rpm_patient_goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("rpm_enrollments.id"), nullable=True)

    # Goal definition
    reading_type = Column(SQLEnum(ReadingType), nullable=False)
    goal_type = Column(String(50), nullable=False)  # target, range, trend
    target_value = Column(Float, nullable=True)
    target_low = Column(Float, nullable=True)
    target_high = Column(Float, nullable=True)
    unit = Column(String(50), nullable=False)

    # Period
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)

    # Progress
    current_value = Column(Float, nullable=True)
    progress_percent = Column(Float, default=0.0)
    is_achieved = Column(Boolean, default=False)
    achieved_at = Column(DateTime(timezone=True), nullable=True)

    # Source
    set_by = Column(UUID(as_uuid=True), nullable=False)
    set_by_type = Column(String(50), nullable=False)  # provider, patient, ai

    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_goals_patient_active", "patient_id", "is_active"),
        Index("idx_goals_reading_type", "reading_type"),
    )


class EducationalContent(Base):
    """Educational content for patients."""
    __tablename__ = "rpm_educational_content"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Content details
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    content_type = Column(String(50), nullable=False)  # article, video, infographic, quiz
    content_url = Column(String(500), nullable=True)
    content_body = Column(Text, nullable=True)

    # Categorization
    condition = Column(String(100), nullable=True)  # HTN, DM, etc.
    tags = Column(ARRAY(String), default=list)
    reading_types = Column(ARRAY(String), default=list)

    # Metadata
    duration_minutes = Column(Integer, nullable=True)
    difficulty_level = Column(String(20), default="beginner")
    language = Column(String(10), default="en")

    # Status
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    published_at = Column(DateTime(timezone=True), nullable=True)

    # Analytics
    view_count = Column(Integer, default=0)
    completion_count = Column(Integer, default=0)
    average_rating = Column(Float, nullable=True)

    created_by = Column(UUID(as_uuid=True), nullable=False)
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_content_condition", "condition"),
        Index("idx_content_active_featured", "is_active", "is_featured"),
    )


class PatientContentEngagement(Base):
    """Track patient engagement with educational content."""
    __tablename__ = "rpm_patient_content_engagement"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    content_id = Column(UUID(as_uuid=True), ForeignKey("rpm_educational_content.id"), nullable=False)

    # Engagement
    viewed_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    time_spent_seconds = Column(Integer, default=0)
    progress_percent = Column(Float, default=0.0)

    # Feedback
    rating = Column(Integer, nullable=True)
    feedback = Column(Text, nullable=True)

    # Quiz results (if applicable)
    quiz_score = Column(Float, nullable=True)
    quiz_attempts = Column(Integer, default=0)

    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("patient_id", "content_id", name="uq_patient_content"),
        Index("idx_engagement_patient", "patient_id"),
    )


# ============================================================================
# ANALYTICS MODELS
# ============================================================================

class PatientTrendAnalysis(Base):
    """Pre-computed trend analysis for patients."""
    __tablename__ = "rpm_patient_trend_analysis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    reading_type = Column(SQLEnum(ReadingType), nullable=False)

    # Analysis period
    analysis_date = Column(Date, nullable=False)
    period_days = Column(Integer, default=30)

    # Statistics
    reading_count = Column(Integer, default=0)
    avg_value = Column(Float, nullable=True)
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    std_dev = Column(Float, nullable=True)

    # Trend
    trend_direction = Column(String(20), nullable=True)  # up, down, stable
    trend_slope = Column(Float, nullable=True)
    trend_significance = Column(Float, nullable=True)  # p-value

    # Baseline comparison
    baseline_value = Column(Float, nullable=True)
    baseline_deviation_percent = Column(Float, nullable=True)

    # Goal progress
    goal_id = Column(UUID(as_uuid=True), ForeignKey("rpm_patient_goals.id"), nullable=True)
    in_goal_range_percent = Column(Float, nullable=True)

    # AI insights
    ai_summary = Column(Text, nullable=True)
    ai_recommendations = Column(JSONB, default=list)
    anomaly_count = Column(Integer, default=0)

    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("patient_id", "reading_type", "analysis_date", name="uq_trend_analysis"),
        Index("idx_trend_patient_type", "patient_id", "reading_type"),
    )


class PopulationHealthMetric(Base):
    """Population-level health metrics."""
    __tablename__ = "rpm_population_health_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Metric context
    metric_date = Column(Date, nullable=False)
    condition = Column(String(100), nullable=True)
    reading_type = Column(SQLEnum(ReadingType), nullable=True)
    cohort_filter = Column(JSONB, default=dict)

    # Population stats
    total_patients = Column(Integer, default=0)
    active_patients = Column(Integer, default=0)
    compliant_patients = Column(Integer, default=0)
    at_goal_patients = Column(Integer, default=0)

    # Compliance metrics
    avg_compliance_rate = Column(Float, default=0.0)
    avg_readings_per_patient = Column(Float, default=0.0)

    # Outcome metrics
    avg_value = Column(Float, nullable=True)
    in_control_percent = Column(Float, nullable=True)
    alert_rate = Column(Float, nullable=True)  # Alerts per 100 patients

    # Engagement
    avg_engagement_score = Column(Float, nullable=True)
    education_completion_rate = Column(Float, nullable=True)

    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("idx_population_metrics_date", "tenant_id", "metric_date"),
        Index("idx_population_metrics_condition", "condition"),
    )
