"""
Remote Monitoring Service Pydantic Schemas
Request/Response models for devices, bindings, measurements, and alerts
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator


# ==================== Remote Device Schemas ====================

class RemoteDeviceCreate(BaseModel):
    """Schema for registering a remote device"""

    tenant_id: UUID
    device_type: str = Field(..., description="BP_CUFF, GLUCOMETER, CGM, PULSE_OXIMETER, WEIGHT_SCALE, ECG")
    manufacturer: str
    model_name: str
    device_identifier: str = Field(..., description="Unique device ID/serial number")
    vendor_system_id: Optional[UUID] = Field(None, description="External system for device vendor")
    calibration_date: Optional[datetime] = None
    firmware_version: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @validator("device_type")
    def validate_device_type(cls, v):
        valid_types = [
            "BP_CUFF", "GLUCOMETER", "CGM", "PULSE_OXIMETER",
            "WEIGHT_SCALE", "ECG", "SPIROMETER", "THERMOMETER",
            "ACTIVITY_TRACKER", "SLEEP_MONITOR"
        ]
        if v.upper() not in valid_types:
            raise ValueError(f"device_type must be one of: {', '.join(valid_types)}")
        return v.upper()

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "device_type": "BP_CUFF",
                "manufacturer": "Omron",
                "model_name": "Omron Evolv",
                "device_identifier": "OMRON-BP-12345678",
                "firmware_version": "2.1.3",
                "metadata": {
                    "connectivity": "bluetooth",
                    "battery_type": "rechargeable"
                }
            }
        }


class RemoteDeviceUpdate(BaseModel):
    """Schema for updating a remote device"""

    calibration_date: Optional[datetime] = None
    firmware_version: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class RemoteDeviceResponse(BaseModel):
    """Response schema for remote device"""

    id: UUID
    tenant_id: UUID
    device_type: str
    manufacturer: str
    model_name: str
    device_identifier: str
    vendor_system_id: Optional[UUID] = None
    calibration_date: Optional[datetime] = None
    firmware_version: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RemoteDeviceListResponse(BaseModel):
    """Response for list of remote devices"""

    total: int
    devices: List[RemoteDeviceResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== Device Binding Schemas ====================

class DeviceBindingCreate(BaseModel):
    """Schema for binding a device to a patient"""

    remote_device_id: UUID
    patient_id: UUID
    care_program_code: Optional[str] = Field(None, description="HF_HOME_MONITORING, DM2_REMOTE, etc.")
    measurement_frequency: Optional[str] = Field(None, description="daily, twice_daily, weekly")
    alert_thresholds: Optional[Dict[str, Any]] = Field(
        None,
        description="Thresholds for automated alerts"
    )
    notes: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "remote_device_id": "device-uuid-123",
                "patient_id": "patient-uuid-456",
                "care_program_code": "HF_HOME_MONITORING",
                "measurement_frequency": "twice_daily",
                "alert_thresholds": {
                    "systolic_bp": {"min": 90, "max": 140},
                    "diastolic_bp": {"min": 60, "max": 90},
                    "heart_rate": {"min": 50, "max": 100}
                },
                "notes": "Patient discharged post-CHF exacerbation. Monitor BP and weight daily."
            }
        }


class DeviceBindingUpdate(BaseModel):
    """Schema for updating a device binding"""

    measurement_frequency: Optional[str] = None
    alert_thresholds: Optional[Dict[str, Any]] = None
    binding_status: Optional[str] = Field(None, description="active, paused, discontinued")
    notes: Optional[str] = None

    @validator("binding_status")
    def validate_binding_status(cls, v):
        if v:
            valid_statuses = ["active", "paused", "discontinued"]
            if v.lower() not in valid_statuses:
                raise ValueError(f"binding_status must be one of: {', '.join(valid_statuses)}")
            return v.lower()
        return v


class DeviceBindingResponse(BaseModel):
    """Response schema for device binding"""

    id: UUID
    remote_device_id: UUID
    patient_id: UUID
    care_program_code: Optional[str] = None
    measurement_frequency: Optional[str] = None
    alert_thresholds: Optional[Dict[str, Any]] = None
    binding_status: str
    bound_at: datetime
    unbound_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeviceBindingListResponse(BaseModel):
    """Response for list of device bindings"""

    total: int
    bindings: List[DeviceBindingResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== Remote Measurement Schemas ====================

class RemoteMeasurementCreate(BaseModel):
    """Schema for ingesting a remote measurement"""

    device_binding_id: UUID
    measurement_type: str = Field(..., description="BP, GLUCOSE, WEIGHT, SPO2, HR, TEMP, etc.")
    measured_at: datetime = Field(..., description="When the measurement was taken")
    payload: Dict[str, Any] = Field(..., description="Measurement values")
    device_metadata: Optional[Dict[str, Any]] = Field(None, description="Battery level, signal strength, etc.")

    @validator("measurement_type")
    def validate_measurement_type(cls, v):
        valid_types = [
            "BP", "GLUCOSE", "WEIGHT", "SPO2", "HR", "TEMP",
            "ECG", "PEAK_FLOW", "STEPS", "SLEEP"
        ]
        if v.upper() not in valid_types:
            raise ValueError(f"measurement_type must be one of: {', '.join(valid_types)}")
        return v.upper()

    class Config:
        json_schema_extra = {
            "example": {
                "device_binding_id": "binding-uuid-789",
                "measurement_type": "BP",
                "measured_at": "2025-11-15T08:30:00Z",
                "payload": {
                    "systolic": 145,
                    "diastolic": 92,
                    "heart_rate": 78,
                    "unit": "mmHg"
                },
                "device_metadata": {
                    "battery_level": 85,
                    "signal_strength": "good"
                }
            }
        }


class RemoteMeasurementResponse(BaseModel):
    """Response schema for remote measurement"""

    id: UUID
    device_binding_id: UUID
    measurement_type: str
    measured_at: datetime
    payload: Dict[str, Any]
    device_metadata: Optional[Dict[str, Any]] = None
    fhir_observation_id: Optional[str] = None
    ingested_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class RemoteMeasurementListResponse(BaseModel):
    """Response for list of remote measurements"""

    total: int
    measurements: List[RemoteMeasurementResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== Remote Alert Schemas ====================

class RemoteAlertResponse(BaseModel):
    """Response schema for remote alert"""

    id: UUID
    device_binding_id: UUID
    measurement_id: Optional[UUID] = None
    alert_type: str
    severity: str
    title: str
    description: str
    alert_data: Optional[Dict[str, Any]] = None
    status: str
    triggered_at: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by_user_id: Optional[UUID] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    linked_task_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RemoteAlertListResponse(BaseModel):
    """Response for list of remote alerts"""

    total: int
    alerts: List[RemoteAlertResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


class RemoteAlertAcknowledge(BaseModel):
    """Schema for acknowledging an alert"""

    notes: Optional[str] = None


class RemoteAlertResolve(BaseModel):
    """Schema for resolving an alert"""

    resolution_notes: str
    linked_task_id: Optional[UUID] = Field(None, description="Nursing task if created")


# ==================== Analytics Schemas ====================

class PatientMeasurementSummary(BaseModel):
    """Summary of measurements for a patient"""

    patient_id: UUID
    device_binding_id: UUID
    measurement_type: str
    total_measurements: int
    latest_measurement: Optional[RemoteMeasurementResponse] = None
    date_range: Dict[str, datetime]
    statistics: Optional[Dict[str, Any]] = Field(
        None,
        description="Min, max, avg, trend"
    )


class PatientMonitoringDashboard(BaseModel):
    """Dashboard view for patient monitoring"""

    patient_id: UUID
    active_devices: List[DeviceBindingResponse]
    recent_measurements: List[RemoteMeasurementResponse]
    active_alerts: List[RemoteAlertResponse]
    measurement_summaries: List[PatientMeasurementSummary]
    adherence_score: Optional[float] = Field(None, description="0-100, based on expected vs actual measurements")
