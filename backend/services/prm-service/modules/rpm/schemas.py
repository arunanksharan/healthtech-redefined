"""
Remote Patient Monitoring (RPM) API Schemas

Pydantic schemas for request/response validation:
- Device management
- Reading ingestion
- Alert management
- Care protocols
- RPM billing
- Patient engagement

EPIC-019: Remote Patient Monitoring
"""

from datetime import datetime, date, time
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator, root_validator
from uuid import UUID
from enum import Enum
from decimal import Decimal


# ============================================================================
# ENUMS (matching models.py)
# ============================================================================

class DeviceType(str, Enum):
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


class DeviceStatus(str, Enum):
    UNREGISTERED = "unregistered"
    REGISTERED = "registered"
    PAIRED = "paired"
    ACTIVE = "active"
    LOW_BATTERY = "low_battery"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    DEACTIVATED = "deactivated"
    LOST = "lost"


class DeviceVendor(str, Enum):
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


class ReadingType(str, Enum):
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


class ReadingStatus(str, Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    FLAGGED = "flagged"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"


class AlertSeverity(str, Enum):
    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    TRIGGERED = "triggered"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    AUTO_RESOLVED = "auto_resolved"


class AlertType(str, Enum):
    THRESHOLD_BREACH = "threshold_breach"
    TREND_ANOMALY = "trend_anomaly"
    PATTERN_DEVIATION = "pattern_deviation"
    MISSED_READING = "missed_reading"
    DEVICE_OFFLINE = "device_offline"
    CRITICAL_VALUE = "critical_value"
    PROTOCOL_VIOLATION = "protocol_violation"
    CARE_GAP = "care_gap"


class ProtocolStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    TERMINATED = "terminated"


class ProtocolTriggerType(str, Enum):
    THRESHOLD = "threshold"
    TREND = "trend"
    SCHEDULE = "schedule"
    MANUAL = "manual"
    AI_RECOMMENDATION = "ai_recommendation"


class ProtocolActionType(str, Enum):
    SEND_MESSAGE = "send_message"
    MAKE_CALL = "make_call"
    SCHEDULE_APPOINTMENT = "schedule_appointment"
    ALERT_PROVIDER = "alert_provider"
    ADJUST_MEDICATION = "adjust_medication"
    ORDER_LAB = "order_lab"
    UPDATE_CARE_PLAN = "update_care_plan"
    ESCALATE = "escalate"


class EnrollmentStatus(str, Enum):
    PENDING = "pending"
    ENROLLED = "enrolled"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    WITHDRAWN = "withdrawn"
    DISCHARGED = "discharged"


class BillingCodeType(str, Enum):
    CPT_99453 = "99453"
    CPT_99454 = "99454"
    CPT_99457 = "99457"
    CPT_99458 = "99458"
    CPT_99091 = "99091"


class OutreachChannel(str, Enum):
    SMS = "sms"
    VOICE_CALL = "voice_call"
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    PUSH_NOTIFICATION = "push"
    IN_APP = "in_app"


# ============================================================================
# DEVICE SCHEMAS
# ============================================================================

class DeviceCreate(BaseModel):
    """Create a new RPM device."""
    device_identifier: str = Field(..., max_length=200)
    vendor: DeviceVendor
    device_type: DeviceType
    serial_number: Optional[str] = Field(None, max_length=100)
    mac_address: Optional[str] = Field(None, max_length=50)
    model: Optional[str] = Field(None, max_length=200)
    firmware_version: Optional[str] = Field(None, max_length=50)
    metadata: Optional[Dict[str, Any]] = None


class DeviceUpdate(BaseModel):
    """Update device information."""
    serial_number: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=200)
    firmware_version: Optional[str] = Field(None, max_length=50)
    status: Optional[DeviceStatus] = None
    metadata: Optional[Dict[str, Any]] = None


class DeviceResponse(BaseModel):
    """Device response."""
    id: UUID
    device_identifier: str
    vendor: DeviceVendor
    device_type: DeviceType
    serial_number: Optional[str]
    mac_address: Optional[str]
    model: Optional[str]
    firmware_version: Optional[str]
    fhir_device_id: Optional[UUID]
    status: DeviceStatus
    battery_level: Optional[int]
    last_sync_at: Optional[datetime]
    last_reading_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeviceAssignmentCreate(BaseModel):
    """Assign a device to a patient."""
    device_id: UUID
    patient_id: UUID
    enrollment_id: Optional[UUID] = None
    reading_frequency: str = Field(default="daily")
    target_readings_per_day: int = Field(default=1, ge=1, le=10)
    reminder_times: Optional[List[str]] = None
    notes: Optional[str] = None


class DeviceAssignmentUpdate(BaseModel):
    """Update device assignment."""
    reading_frequency: Optional[str] = None
    target_readings_per_day: Optional[int] = Field(None, ge=1, le=10)
    reminder_times: Optional[List[str]] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class DeviceAssignmentResponse(BaseModel):
    """Device assignment response."""
    id: UUID
    device_id: UUID
    patient_id: UUID
    enrollment_id: Optional[UUID]
    reading_frequency: str
    target_readings_per_day: int
    reminder_times: List[str]
    is_active: bool
    assigned_at: datetime
    assigned_by: UUID
    unassigned_at: Optional[datetime]
    notes: Optional[str]
    device: Optional[DeviceResponse] = None

    class Config:
        from_attributes = True


# ============================================================================
# READING SCHEMAS
# ============================================================================

class ReadingCreate(BaseModel):
    """Create a device reading."""
    patient_id: UUID
    device_id: Optional[UUID] = None
    enrollment_id: Optional[UUID] = None
    reading_type: ReadingType
    value: float
    unit: str = Field(..., max_length=50)
    secondary_value: Optional[float] = None
    secondary_unit: Optional[str] = Field(None, max_length=50)
    measured_at: datetime
    timezone: Optional[str] = Field(None, max_length=50)
    is_manual: bool = False
    source: Optional[str] = Field(None, max_length=100)
    context: Optional[Dict[str, Any]] = None
    raw_data: Optional[Dict[str, Any]] = None

    @validator('value')
    def validate_value(cls, v, values):
        if v < 0:
            raise ValueError('Value cannot be negative')
        return v


class ReadingBatchCreate(BaseModel):
    """Create multiple readings in batch."""
    readings: List[ReadingCreate]
    source: str = Field(..., max_length=100)
    source_reference: Optional[str] = Field(None, max_length=200)


class ReadingUpdate(BaseModel):
    """Update a reading."""
    status: Optional[ReadingStatus] = None
    is_valid: Optional[bool] = None
    flagged_reason: Optional[str] = Field(None, max_length=500)


class ReadingResponse(BaseModel):
    """Reading response."""
    id: UUID
    patient_id: UUID
    device_id: Optional[UUID]
    enrollment_id: Optional[UUID]
    reading_type: ReadingType
    value: float
    unit: str
    secondary_value: Optional[float]
    secondary_unit: Optional[str]
    measured_at: datetime
    received_at: datetime
    timezone: Optional[str]
    status: ReadingStatus
    is_manual: bool
    source: Optional[str]
    is_valid: bool
    validation_errors: List[str]
    flagged_reason: Optional[str]
    fhir_observation_id: Optional[UUID]
    context: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class ReadingBatchResponse(BaseModel):
    """Batch processing response."""
    batch_id: UUID
    total_readings: int
    processed_readings: int
    failed_readings: int
    duplicate_readings: int
    status: str
    errors: List[Dict[str, Any]] = []


class BloodPressureReading(BaseModel):
    """Convenience schema for blood pressure readings."""
    patient_id: UUID
    device_id: Optional[UUID] = None
    enrollment_id: Optional[UUID] = None
    systolic: float = Field(..., ge=40, le=300)
    diastolic: float = Field(..., ge=20, le=200)
    pulse: Optional[float] = Field(None, ge=20, le=300)
    measured_at: datetime
    position: Optional[str] = None  # sitting, standing, lying
    arm: Optional[str] = None  # left, right
    is_manual: bool = False
    context: Optional[Dict[str, Any]] = None


class GlucoseReading(BaseModel):
    """Convenience schema for glucose readings."""
    patient_id: UUID
    device_id: Optional[UUID] = None
    enrollment_id: Optional[UUID] = None
    value: float = Field(..., ge=10, le=700)
    unit: str = Field(default="mg/dL")
    measured_at: datetime
    meal_context: Optional[str] = None  # fasting, before_meal, after_meal, bedtime
    is_manual: bool = False
    context: Optional[Dict[str, Any]] = None


class WeightReading(BaseModel):
    """Convenience schema for weight readings."""
    patient_id: UUID
    device_id: Optional[UUID] = None
    enrollment_id: Optional[UUID] = None
    value: float = Field(..., ge=1, le=1000)
    unit: str = Field(default="kg")
    measured_at: datetime
    body_fat_percent: Optional[float] = Field(None, ge=0, le=100)
    muscle_mass_kg: Optional[float] = None
    water_percent: Optional[float] = Field(None, ge=0, le=100)
    is_manual: bool = False
    context: Optional[Dict[str, Any]] = None


class OxygenSaturationReading(BaseModel):
    """Convenience schema for SpO2 readings."""
    patient_id: UUID
    device_id: Optional[UUID] = None
    enrollment_id: Optional[UUID] = None
    spo2: float = Field(..., ge=50, le=100)
    pulse: Optional[float] = Field(None, ge=20, le=300)
    measured_at: datetime
    perfusion_index: Optional[float] = None
    is_manual: bool = False
    context: Optional[Dict[str, Any]] = None


# ============================================================================
# ALERT SCHEMAS
# ============================================================================

class AlertRuleCreate(BaseModel):
    """Create an alert rule."""
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    reading_type: Optional[ReadingType] = None
    is_global: bool = False
    threshold_low: Optional[float] = None
    threshold_high: Optional[float] = None
    threshold_critical_low: Optional[float] = None
    threshold_critical_high: Optional[float] = None
    trend_direction: Optional[str] = None
    trend_threshold_percent: Optional[float] = None
    trend_window_hours: Optional[int] = None
    severity: AlertSeverity = AlertSeverity.MEDIUM
    alert_type: AlertType = AlertType.THRESHOLD_BREACH
    cooldown_minutes: int = Field(default=60, ge=0)
    notify_provider: bool = True
    notify_patient: bool = False
    notify_care_team: bool = True
    escalation_minutes: int = Field(default=30, ge=0)
    conditions: Optional[Dict[str, Any]] = None


class AlertRuleUpdate(BaseModel):
    """Update an alert rule."""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    threshold_low: Optional[float] = None
    threshold_high: Optional[float] = None
    threshold_critical_low: Optional[float] = None
    threshold_critical_high: Optional[float] = None
    severity: Optional[AlertSeverity] = None
    cooldown_minutes: Optional[int] = Field(None, ge=0)
    notify_provider: Optional[bool] = None
    notify_patient: Optional[bool] = None
    notify_care_team: Optional[bool] = None
    is_active: Optional[bool] = None
    conditions: Optional[Dict[str, Any]] = None


class AlertRuleResponse(BaseModel):
    """Alert rule response."""
    id: UUID
    name: str
    description: Optional[str]
    reading_type: Optional[ReadingType]
    is_global: bool
    threshold_low: Optional[float]
    threshold_high: Optional[float]
    threshold_critical_low: Optional[float]
    threshold_critical_high: Optional[float]
    severity: AlertSeverity
    alert_type: AlertType
    cooldown_minutes: int
    notify_provider: bool
    notify_patient: bool
    notify_care_team: bool
    is_active: bool
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PatientAlertRuleCreate(BaseModel):
    """Create patient-specific alert rule."""
    rule_id: UUID
    patient_id: UUID
    enrollment_id: Optional[UUID] = None
    threshold_low: Optional[float] = None
    threshold_high: Optional[float] = None
    threshold_critical_low: Optional[float] = None
    threshold_critical_high: Optional[float] = None
    notes: Optional[str] = None


class PatientAlertRuleUpdate(BaseModel):
    """Update patient alert rule."""
    threshold_low: Optional[float] = None
    threshold_high: Optional[float] = None
    threshold_critical_low: Optional[float] = None
    threshold_critical_high: Optional[float] = None
    is_active: Optional[bool] = None
    is_muted: Optional[bool] = None
    muted_until: Optional[datetime] = None
    notes: Optional[str] = None


class PatientAlertRuleResponse(BaseModel):
    """Patient alert rule response."""
    id: UUID
    rule_id: UUID
    patient_id: UUID
    enrollment_id: Optional[UUID]
    threshold_low: Optional[float]
    threshold_high: Optional[float]
    threshold_critical_low: Optional[float]
    threshold_critical_high: Optional[float]
    is_active: bool
    is_muted: bool
    muted_until: Optional[datetime]
    approved_by: Optional[UUID]
    approved_at: Optional[datetime]
    notes: Optional[str]
    rule: Optional[AlertRuleResponse] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    """Alert response."""
    id: UUID
    patient_id: UUID
    enrollment_id: Optional[UUID]
    rule_id: Optional[UUID]
    reading_id: Optional[UUID]
    alert_type: AlertType
    severity: AlertSeverity
    status: AlertStatus
    title: str
    message: str
    reading_value: Optional[float]
    threshold_value: Optional[float]
    reading_type: Optional[ReadingType]
    ai_analysis: Optional[str]
    ai_recommendation: Optional[str]
    triggered_at: datetime
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[UUID]
    resolved_at: Optional[datetime]
    resolved_by: Optional[UUID]
    resolution_notes: Optional[str]
    escalation_level: int
    created_at: datetime

    class Config:
        from_attributes = True


class AlertAcknowledge(BaseModel):
    """Acknowledge an alert."""
    notes: Optional[str] = None


class AlertResolve(BaseModel):
    """Resolve an alert."""
    resolution_notes: str
    action_taken: Optional[str] = None


class AlertEscalate(BaseModel):
    """Escalate an alert."""
    escalate_to: List[UUID]
    reason: str


# ============================================================================
# PROTOCOL SCHEMAS
# ============================================================================

class ProtocolTriggerCreate(BaseModel):
    """Create protocol trigger."""
    name: str = Field(..., max_length=200)
    trigger_type: ProtocolTriggerType
    reading_type: Optional[ReadingType] = None
    condition_operator: Optional[str] = None
    condition_value: Optional[float] = None
    condition_value_2: Optional[float] = None
    condition_unit: Optional[str] = None
    consecutive_count: int = Field(default=1, ge=1)
    schedule_cron: Optional[str] = None
    schedule_days: Optional[List[int]] = None
    priority: int = Field(default=50, ge=0, le=100)
    conditions: Optional[Dict[str, Any]] = None


class ProtocolActionCreate(BaseModel):
    """Create protocol action."""
    action_type: ProtocolActionType
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    message_template: Optional[str] = None
    channel: Optional[OutreachChannel] = None
    recipient_type: Optional[str] = None
    delay_minutes: int = Field(default=0, ge=0)
    requires_approval: bool = False
    approval_role: Optional[str] = None
    sequence: int = Field(default=0, ge=0)
    config: Optional[Dict[str, Any]] = None


class ProtocolCreate(BaseModel):
    """Create a care protocol."""
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    condition: str = Field(..., max_length=100)
    version: str = Field(default="1.0", max_length=20)
    duration_days: Optional[int] = Field(None, ge=1)
    reading_types: Optional[List[str]] = None
    target_readings_per_day: int = Field(default=1, ge=1)
    is_template: bool = False
    clinical_guidelines: Optional[Dict[str, Any]] = None
    evidence_references: Optional[List[str]] = None
    triggers: Optional[List[ProtocolTriggerCreate]] = None


class ProtocolUpdate(BaseModel):
    """Update a care protocol."""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    duration_days: Optional[int] = Field(None, ge=1)
    target_readings_per_day: Optional[int] = Field(None, ge=1)
    status: Optional[ProtocolStatus] = None
    clinical_guidelines: Optional[Dict[str, Any]] = None


class TriggerResponse(BaseModel):
    """Protocol trigger response."""
    id: UUID
    name: str
    trigger_type: ProtocolTriggerType
    reading_type: Optional[ReadingType]
    condition_operator: Optional[str]
    condition_value: Optional[float]
    condition_value_2: Optional[float]
    consecutive_count: int
    priority: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ActionResponse(BaseModel):
    """Protocol action response."""
    id: UUID
    action_type: ProtocolActionType
    name: str
    description: Optional[str]
    channel: Optional[OutreachChannel]
    recipient_type: Optional[str]
    delay_minutes: int
    requires_approval: bool
    sequence: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ProtocolResponse(BaseModel):
    """Care protocol response."""
    id: UUID
    name: str
    description: Optional[str]
    condition: str
    version: str
    duration_days: Optional[int]
    reading_types: List[str]
    target_readings_per_day: int
    status: ProtocolStatus
    is_template: bool
    clinical_guidelines: Dict[str, Any]
    evidence_references: List[str]
    created_by: UUID
    approved_by: Optional[UUID]
    approved_at: Optional[datetime]
    triggers: List[TriggerResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProtocolExecutionResponse(BaseModel):
    """Protocol execution response."""
    id: UUID
    enrollment_id: UUID
    action_id: UUID
    trigger_reading_id: Optional[UUID]
    status: str
    scheduled_at: datetime
    executed_at: Optional[datetime]
    completed_at: Optional[datetime]
    requires_approval: bool
    approved_by: Optional[UUID]
    approved_at: Optional[datetime]
    success: Optional[bool]
    error_message: Optional[str]
    result_data: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# ENROLLMENT SCHEMAS
# ============================================================================

class EnrollmentCreate(BaseModel):
    """Create RPM enrollment."""
    patient_id: UUID
    fhir_patient_id: Optional[UUID] = None
    protocol_id: Optional[UUID] = None
    program_name: str = Field(..., max_length=200)
    primary_condition: str = Field(..., max_length=100)
    secondary_conditions: Optional[List[str]] = None
    primary_provider_id: UUID
    care_team_ids: Optional[List[UUID]] = None
    target_readings_per_day: int = Field(default=1, ge=1)
    goals: Optional[Dict[str, Any]] = None
    consent_obtained: bool = False
    consent_date: Optional[date] = None
    consent_document_id: Optional[UUID] = None
    notes: Optional[str] = None


class EnrollmentUpdate(BaseModel):
    """Update RPM enrollment."""
    protocol_id: Optional[UUID] = None
    primary_provider_id: Optional[UUID] = None
    care_team_ids: Optional[List[UUID]] = None
    target_readings_per_day: Optional[int] = Field(None, ge=1)
    goals: Optional[Dict[str, Any]] = None
    status: Optional[EnrollmentStatus] = None
    discharge_reason: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None


class EnrollmentResponse(BaseModel):
    """Enrollment response."""
    id: UUID
    patient_id: UUID
    fhir_patient_id: Optional[UUID]
    protocol_id: Optional[UUID]
    program_name: str
    primary_condition: str
    secondary_conditions: List[str]
    primary_provider_id: UUID
    care_team_ids: List[UUID]
    status: EnrollmentStatus
    enrolled_at: Optional[datetime]
    activated_at: Optional[datetime]
    completed_at: Optional[datetime]
    discharge_reason: Optional[str]
    consent_obtained: bool
    consent_date: Optional[date]
    target_readings_per_day: int
    goals: Dict[str, Any]
    enrolled_by: UUID
    notes: Optional[str]
    protocol: Optional[ProtocolResponse] = None
    device_assignments: List[DeviceAssignmentResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# BILLING SCHEMAS
# ============================================================================

class MonitoringPeriodResponse(BaseModel):
    """Monitoring period response."""
    id: UUID
    enrollment_id: UUID
    patient_id: UUID
    period_start: date
    period_end: date
    period_month: int
    is_current: bool
    days_with_readings: int
    total_readings: int
    qualifies_for_99454: bool
    clinical_time_minutes: int
    interactive_time_minutes: int
    qualifies_for_99457: bool
    qualifies_for_99458: bool
    device_setup_done: bool
    device_setup_date: Optional[date]
    billing_generated: bool
    billing_codes: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ClinicalTimeEntryCreate(BaseModel):
    """Log clinical time."""
    monitoring_period_id: UUID
    enrollment_id: UUID
    start_time: datetime
    end_time: datetime
    activity_type: str = Field(..., max_length=100)
    is_interactive: bool = False
    description: Optional[str] = None
    alert_id: Optional[UUID] = None
    reading_ids: Optional[List[UUID]] = None

    @validator('end_time')
    def end_after_start(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v


class ClinicalTimeEntryResponse(BaseModel):
    """Clinical time entry response."""
    id: UUID
    monitoring_period_id: UUID
    enrollment_id: UUID
    provider_id: UUID
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    activity_type: str
    is_interactive: bool
    description: Optional[str]
    alert_id: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True


class BillingEventCreate(BaseModel):
    """Generate billing event."""
    enrollment_id: UUID
    monitoring_period_id: Optional[UUID] = None
    cpt_code: BillingCodeType
    service_date: date
    units: int = Field(default=1, ge=1)
    billing_provider_id: UUID
    supervising_provider_id: Optional[UUID] = None
    documentation: Optional[Dict[str, Any]] = None


class BillingEventResponse(BaseModel):
    """Billing event response."""
    id: UUID
    enrollment_id: UUID
    monitoring_period_id: Optional[UUID]
    patient_id: UUID
    cpt_code: BillingCodeType
    service_date: date
    units: int
    billing_provider_id: UUID
    supervising_provider_id: Optional[UUID]
    status: str
    claim_id: Optional[UUID]
    external_claim_id: Optional[str]
    billed_amount: Optional[Decimal]
    allowed_amount: Optional[Decimal]
    paid_amount: Optional[Decimal]
    days_with_data: Optional[int]
    clinical_minutes: Optional[int]
    generated_at: datetime
    submitted_at: Optional[datetime]
    adjudicated_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class BillingSummary(BaseModel):
    """Monthly billing summary."""
    period_month: int
    total_patients_enrolled: int
    patients_eligible_99453: int
    patients_eligible_99454: int
    patients_eligible_99457: int
    patients_eligible_99458: int
    total_billable_amount: Decimal
    total_submitted: int
    total_paid: int
    total_denied: int
    revenue_collected: Decimal
    revenue_pending: Decimal


# ============================================================================
# PATIENT ENGAGEMENT SCHEMAS
# ============================================================================

class PatientReminderCreate(BaseModel):
    """Create patient reminder."""
    patient_id: UUID
    enrollment_id: Optional[UUID] = None
    device_assignment_id: Optional[UUID] = None
    reminder_type: str = Field(..., max_length=50)
    reading_type: Optional[ReadingType] = None
    scheduled_time: str = Field(..., regex=r'^\d{2}:\d{2}$')  # HH:MM
    days_of_week: List[int] = Field(default=[0, 1, 2, 3, 4, 5, 6])
    timezone: str = Field(default="UTC", max_length=50)
    channel: OutreachChannel = OutreachChannel.PUSH_NOTIFICATION
    message_template: Optional[str] = None


class PatientReminderUpdate(BaseModel):
    """Update patient reminder."""
    scheduled_time: Optional[str] = Field(None, regex=r'^\d{2}:\d{2}$')
    days_of_week: Optional[List[int]] = None
    channel: Optional[OutreachChannel] = None
    message_template: Optional[str] = None
    is_active: Optional[bool] = None


class PatientReminderResponse(BaseModel):
    """Patient reminder response."""
    id: UUID
    patient_id: UUID
    enrollment_id: Optional[UUID]
    reminder_type: str
    reading_type: Optional[ReadingType]
    scheduled_time: str
    days_of_week: List[int]
    timezone: str
    channel: OutreachChannel
    is_active: bool
    last_sent_at: Optional[datetime]
    next_scheduled_at: Optional[datetime]
    reminders_sent: int
    readings_after_reminder: int
    response_rate: float
    created_at: datetime

    class Config:
        from_attributes = True


class PatientGoalCreate(BaseModel):
    """Create patient goal."""
    patient_id: UUID
    enrollment_id: Optional[UUID] = None
    reading_type: ReadingType
    goal_type: str = Field(..., max_length=50)  # target, range, trend
    target_value: Optional[float] = None
    target_low: Optional[float] = None
    target_high: Optional[float] = None
    unit: str = Field(..., max_length=50)
    start_date: date
    end_date: Optional[date] = None
    notes: Optional[str] = None


class PatientGoalUpdate(BaseModel):
    """Update patient goal."""
    target_value: Optional[float] = None
    target_low: Optional[float] = None
    target_high: Optional[float] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class PatientGoalResponse(BaseModel):
    """Patient goal response."""
    id: UUID
    patient_id: UUID
    enrollment_id: Optional[UUID]
    reading_type: ReadingType
    goal_type: str
    target_value: Optional[float]
    target_low: Optional[float]
    target_high: Optional[float]
    unit: str
    start_date: date
    end_date: Optional[date]
    current_value: Optional[float]
    progress_percent: float
    is_achieved: bool
    achieved_at: Optional[datetime]
    set_by: UUID
    set_by_type: str
    is_active: bool
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class EducationalContentCreate(BaseModel):
    """Create educational content."""
    title: str = Field(..., max_length=300)
    description: Optional[str] = None
    content_type: str = Field(..., max_length=50)
    content_url: Optional[str] = Field(None, max_length=500)
    content_body: Optional[str] = None
    condition: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    reading_types: Optional[List[str]] = None
    duration_minutes: Optional[int] = None
    difficulty_level: str = Field(default="beginner", max_length=20)
    language: str = Field(default="en", max_length=10)
    is_featured: bool = False


class EducationalContentResponse(BaseModel):
    """Educational content response."""
    id: UUID
    title: str
    description: Optional[str]
    content_type: str
    content_url: Optional[str]
    condition: Optional[str]
    tags: List[str]
    reading_types: List[str]
    duration_minutes: Optional[int]
    difficulty_level: str
    language: str
    is_active: bool
    is_featured: bool
    published_at: Optional[datetime]
    view_count: int
    completion_count: int
    average_rating: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class ContentEngagementCreate(BaseModel):
    """Record content engagement."""
    content_id: UUID
    time_spent_seconds: int = Field(default=0, ge=0)
    progress_percent: float = Field(default=0.0, ge=0, le=100)
    completed: bool = False
    rating: Optional[int] = Field(None, ge=1, le=5)
    feedback: Optional[str] = None
    quiz_score: Optional[float] = Field(None, ge=0, le=100)


# ============================================================================
# ANALYTICS SCHEMAS
# ============================================================================

class TrendAnalysisResponse(BaseModel):
    """Trend analysis response."""
    id: UUID
    patient_id: UUID
    reading_type: ReadingType
    analysis_date: date
    period_days: int
    reading_count: int
    avg_value: Optional[float]
    min_value: Optional[float]
    max_value: Optional[float]
    std_dev: Optional[float]
    trend_direction: Optional[str]
    trend_slope: Optional[float]
    trend_significance: Optional[float]
    baseline_value: Optional[float]
    baseline_deviation_percent: Optional[float]
    in_goal_range_percent: Optional[float]
    ai_summary: Optional[str]
    ai_recommendations: List[Dict[str, Any]]
    anomaly_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class PopulationMetricsResponse(BaseModel):
    """Population health metrics response."""
    id: UUID
    metric_date: date
    condition: Optional[str]
    reading_type: Optional[ReadingType]
    total_patients: int
    active_patients: int
    compliant_patients: int
    at_goal_patients: int
    avg_compliance_rate: float
    avg_readings_per_patient: float
    avg_value: Optional[float]
    in_control_percent: Optional[float]
    alert_rate: Optional[float]
    avg_engagement_score: Optional[float]
    education_completion_rate: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class DataQualityResponse(BaseModel):
    """Data quality metrics response."""
    id: UUID
    patient_id: UUID
    device_id: Optional[UUID]
    period_start: date
    period_end: date
    expected_readings: int
    actual_readings: int
    valid_readings: int
    flagged_readings: int
    compliance_rate: float
    days_with_data: int
    longest_gap_hours: float
    avg_reading_interval_hours: Optional[float]
    data_quality_score: float
    consistency_score: float
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# DASHBOARD SCHEMAS
# ============================================================================

class PatientRPMDashboard(BaseModel):
    """Patient RPM dashboard data."""
    patient_id: UUID
    enrollment: Optional[EnrollmentResponse]
    active_devices: List[DeviceAssignmentResponse]
    recent_readings: List[ReadingResponse]
    active_alerts: List[AlertResponse]
    goals: List[PatientGoalResponse]
    compliance_rate: float
    days_with_readings_this_month: int
    next_reminder: Optional[datetime]
    trend_summary: Dict[ReadingType, Dict[str, Any]]
    recommended_content: List[EducationalContentResponse]


class ProviderRPMDashboard(BaseModel):
    """Provider RPM dashboard data."""
    total_enrolled_patients: int
    active_patients: int
    patients_needing_attention: int
    critical_alerts: List[AlertResponse]
    pending_approvals: int
    billing_eligible_this_month: Dict[str, int]
    compliance_overview: Dict[str, float]
    recent_readings_count: int
    protocol_executions_pending: int


class RPMProgramMetrics(BaseModel):
    """Overall RPM program metrics."""
    total_enrollments: int
    active_enrollments: int
    total_devices: int
    active_devices: int
    readings_today: int
    readings_this_month: int
    alerts_triggered_today: int
    alerts_resolved_today: int
    avg_compliance_rate: float
    billing_summary: BillingSummary
    condition_breakdown: Dict[str, int]
    top_performing_protocols: List[Dict[str, Any]]


# ============================================================================
# WEBHOOK SCHEMAS (for vendor integrations)
# ============================================================================

class WithingsWebhookPayload(BaseModel):
    """Withings webhook payload."""
    userid: str
    appli: int
    startdate: int
    enddate: int
    date: Optional[int] = None


class AppleHealthExportPayload(BaseModel):
    """Apple Health export payload."""
    patient_id: UUID
    records: List[Dict[str, Any]]
    export_date: datetime


class GoogleFitDataPayload(BaseModel):
    """Google Fit data payload."""
    patient_id: UUID
    data_source_id: str
    data_points: List[Dict[str, Any]]


# ============================================================================
# PAGINATION
# ============================================================================

class PaginatedResponse(BaseModel):
    """Generic paginated response."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    pages: int


class ReadingFilters(BaseModel):
    """Filters for reading queries."""
    patient_id: Optional[UUID] = None
    device_id: Optional[UUID] = None
    enrollment_id: Optional[UUID] = None
    reading_type: Optional[ReadingType] = None
    status: Optional[ReadingStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_manual: Optional[bool] = None
    is_valid: Optional[bool] = None


class AlertFilters(BaseModel):
    """Filters for alert queries."""
    patient_id: Optional[UUID] = None
    enrollment_id: Optional[UUID] = None
    severity: Optional[AlertSeverity] = None
    status: Optional[AlertStatus] = None
    alert_type: Optional[AlertType] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class EnrollmentFilters(BaseModel):
    """Filters for enrollment queries."""
    patient_id: Optional[UUID] = None
    provider_id: Optional[UUID] = None
    condition: Optional[str] = None
    status: Optional[EnrollmentStatus] = None
    protocol_id: Optional[UUID] = None
