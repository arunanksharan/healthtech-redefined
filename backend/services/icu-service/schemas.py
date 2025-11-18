"""
ICU Service Pydantic Schemas
Request/Response models for EWS scores and ICU alerts
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator


# ==================== EWS Score Schemas ====================

class EWSCalculateRequest(BaseModel):
    """Schema for calculating EWS from vitals"""

    tenant_id: UUID
    admission_id: UUID
    encounter_id: UUID
    patient_id: UUID
    score_type: str = Field(default="NEWS2", description="NEWS2, MEWS, SOFA")
    vitals: Dict[str, Any] = Field(
        ...,
        description="Vitals data: heart_rate, respiratory_rate, bp_systolic, spo2, temperature, consciousness_level"
    )
    source_observation_id: Optional[UUID] = None
    calculated_at: Optional[datetime] = None

    @validator("score_type")
    def validate_score_type(cls, v):
        valid_types = ["NEWS2", "MEWS", "SOFA"]
        if v.upper() not in valid_types:
            raise ValueError(f"score_type must be one of: {', '.join(valid_types)}")
        return v.upper()

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "admission_id": "admission-uuid",
                "encounter_id": "encounter-uuid",
                "patient_id": "patient-uuid",
                "score_type": "NEWS2",
                "vitals": {
                    "respiratory_rate": 18,
                    "spo2": 96,
                    "bp_systolic": 110,
                    "heart_rate": 75,
                    "temperature": 37.2,
                    "consciousness_level": "alert"
                }
            }
        }


class EWSScoreResponse(BaseModel):
    """Response schema for EWS score"""

    id: UUID
    tenant_id: UUID
    admission_id: UUID
    encounter_id: UUID
    patient_id: UUID
    score_type: str
    score_value: int
    risk_level: str
    calculated_at: datetime
    source_observation_ids: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class EWSScoreWithDetails(BaseModel):
    """EWS score with breakdown and patient details"""

    id: UUID
    patient_id: UUID
    patient_name: str
    admission_id: UUID
    score_type: str
    score_value: int
    risk_level: str
    calculated_at: datetime
    score_breakdown: Optional[Dict[str, Any]] = None
    vitals_snapshot: Optional[Dict[str, Any]] = None


class EWSScoreListResponse(BaseModel):
    """Response for list of EWS scores"""

    total: int
    scores: List[EWSScoreResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== ICU Alert Schemas ====================

class ICUAlertCreate(BaseModel):
    """Schema for creating an ICU alert"""

    tenant_id: UUID
    admission_id: UUID
    encounter_id: UUID
    patient_id: UUID
    alert_type: str = Field(..., description="ews_high, vitals_trend, device_alarm, manual")
    message: str = Field(..., min_length=1)
    severity: str = Field(..., description="info, warning, critical")
    triggered_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    @validator("alert_type")
    def validate_alert_type(cls, v):
        valid_types = ["ews_high", "vitals_trend", "device_alarm", "manual", "other"]
        if v.lower() not in valid_types:
            raise ValueError(f"alert_type must be one of: {', '.join(valid_types)}")
        return v.lower()

    @validator("severity")
    def validate_severity(cls, v):
        valid_severities = ["info", "warning", "critical"]
        if v.lower() not in valid_severities:
            raise ValueError(f"severity must be one of: {', '.join(valid_severities)}")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "admission_id": "admission-uuid",
                "encounter_id": "encounter-uuid",
                "patient_id": "patient-uuid",
                "alert_type": "ews_high",
                "message": "NEWS2 score of 8 - High risk",
                "severity": "critical"
            }
        }


class ICUAlertUpdate(BaseModel):
    """Schema for updating an ICU alert"""

    status: Optional[str] = Field(None, description="open, acknowledged, resolved")
    acknowledged_by_user_id: Optional[UUID] = None
    notes: Optional[str] = None

    @validator("status")
    def validate_status(cls, v):
        if v:
            valid_statuses = ["open", "acknowledged", "resolved"]
            if v.lower() not in valid_statuses:
                raise ValueError(f"status must be one of: {', '.join(valid_statuses)}")
            return v.lower()
        return v


class ICUAlertResponse(BaseModel):
    """Response schema for ICU alert"""

    id: UUID
    tenant_id: UUID
    admission_id: UUID
    encounter_id: UUID
    patient_id: UUID
    alert_type: str
    message: str
    severity: str
    status: str
    triggered_at: datetime
    acknowledged_by_user_id: Optional[UUID] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ICUAlertWithDetails(BaseModel):
    """ICU alert with patient and ward details"""

    id: UUID
    patient_id: UUID
    patient_name: str
    ward_name: Optional[str] = None
    bed_code: Optional[str] = None
    alert_type: str
    message: str
    severity: str
    status: str
    triggered_at: datetime
    age_minutes: int


class ICUAlertListResponse(BaseModel):
    """Response for list of ICU alerts"""

    total: int
    alerts: List[ICUAlertResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== Dashboard Schemas ====================

class ICUDashboardStats(BaseModel):
    """ICU dashboard statistics"""

    total_icu_patients: int = 0
    total_hdu_patients: int = 0
    active_critical_alerts: int = 0
    active_warning_alerts: int = 0
    high_risk_patients: int = 0
    medium_risk_patients: int = 0
    average_news2_score: Optional[float] = None
