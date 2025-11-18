"""
Admission Service Pydantic Schemas
Request/Response models for inpatient admissions and discharges
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, validator


# ==================== Admission Schemas ====================

class AdmissionCreate(BaseModel):
    """Schema for creating an admission"""

    tenant_id: UUID
    patient_id: UUID
    primary_practitioner_id: UUID
    admitting_department: Optional[str] = Field(None, max_length=200)
    admission_type: str = Field(..., description="elective, emergency, transfer")
    admission_reason: Optional[str] = None
    source_type: Optional[str] = Field(None, description="OPD, ER, REFERRAL, DIRECT")
    source_appointment_id: Optional[UUID] = None
    admitted_at: Optional[datetime] = None

    @validator("admission_type")
    def validate_admission_type(cls, v):
        valid_types = ["elective", "emergency", "transfer"]
        if v.lower() not in valid_types:
            raise ValueError(f"admission_type must be one of: {', '.join(valid_types)}")
        return v.lower()

    @validator("source_type")
    def validate_source_type(cls, v):
        if v:
            valid_sources = ["opd", "er", "referral", "direct"]
            if v.lower() not in valid_sources:
                raise ValueError(f"source_type must be one of: {', '.join(valid_sources)}")
            return v.upper()
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "patient_id": "patient-uuid",
                "primary_practitioner_id": "doctor-uuid",
                "admitting_department": "General Medicine",
                "admission_type": "emergency",
                "admission_reason": "Acute chest pain",
                "source_type": "ER",
                "admitted_at": "2025-01-15T14:30:00Z"
            }
        }


class AdmissionUpdate(BaseModel):
    """Schema for updating an admission"""

    primary_practitioner_id: Optional[UUID] = None
    admitting_department: Optional[str] = None
    admission_reason: Optional[str] = None
    status: Optional[str] = Field(None, description="admitted, transferred, discharged, cancelled")

    @validator("status")
    def validate_status(cls, v):
        if v:
            valid_statuses = ["admitted", "transferred", "discharged", "cancelled"]
            if v.lower() not in valid_statuses:
                raise ValueError(f"status must be one of: {', '.join(valid_statuses)}")
            return v.lower()
        return v


class AdmissionDischarge(BaseModel):
    """Schema for discharging a patient"""

    discharged_at: Optional[datetime] = None
    discharge_reason: Optional[str] = None
    discharge_disposition: Optional[str] = Field(
        None,
        description="home, transferred, deceased, ama (against medical advice)"
    )
    discharge_summary: Optional[str] = None

    @validator("discharge_disposition")
    def validate_discharge_disposition(cls, v):
        if v:
            valid_dispositions = ["home", "transferred", "deceased", "ama"]
            if v.lower() not in valid_dispositions:
                raise ValueError(f"discharge_disposition must be one of: {', '.join(valid_dispositions)}")
            return v.lower()
        return v


class AdmissionCancel(BaseModel):
    """Schema for cancelling an admission"""

    cancel_reason: str = Field(..., min_length=1)
    cancelled_at: Optional[datetime] = None


class AdmissionLinkBed(BaseModel):
    """Schema for linking bed assignment to admission"""

    bed_assignment_id: UUID


class AdmissionResponse(BaseModel):
    """Response schema for admission"""

    id: UUID
    tenant_id: UUID
    patient_id: UUID
    primary_practitioner_id: UUID
    admitting_department: Optional[str] = None
    admission_type: str
    admission_reason: Optional[str] = None
    source_type: Optional[str] = None
    source_appointment_id: Optional[UUID] = None
    encounter_id: UUID
    episode_of_care_fhir_id: Optional[str] = None
    status: str
    admitted_at: datetime
    discharged_at: Optional[datetime] = None
    discharge_summary_fhir_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AdmissionWithDetails(BaseModel):
    """Admission with patient and practitioner details"""

    id: UUID
    patient_id: UUID
    patient_name: str
    primary_practitioner_id: UUID
    primary_practitioner_name: str
    admitting_department: Optional[str] = None
    admission_type: str
    admission_reason: Optional[str] = None
    source_type: Optional[str] = None
    encounter_id: UUID
    status: str
    admitted_at: datetime
    discharged_at: Optional[datetime] = None
    length_of_stay_days: Optional[int] = None
    current_bed_code: Optional[str] = None
    current_ward_name: Optional[str] = None


class AdmissionListResponse(BaseModel):
    """Response for list of admissions"""

    total: int
    admissions: List[AdmissionResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== Statistics Schemas ====================

class AdmissionStats(BaseModel):
    """Admission statistics for a time period"""

    total_admissions: int = 0
    active_admissions: int = 0
    discharged_today: int = 0
    average_length_of_stay_days: Optional[float] = None
    admission_type_breakdown: dict = Field(default_factory=dict)
    department_breakdown: dict = Field(default_factory=dict)
