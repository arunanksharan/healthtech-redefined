"""
Encounter Service Pydantic Schemas
Request/Response models for encounter management
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, validator


class EncounterCreate(BaseModel):
    """Schema for creating an encounter"""

    tenant_id: UUID
    patient_id: UUID
    practitioner_id: UUID
    appointment_id: Optional[UUID] = Field(
        None,
        description="Link to appointment if this encounter is from a scheduled appointment"
    )
    class_code: str = Field(
        default="AMB",
        description="Encounter class: AMB (ambulatory/outpatient), IMP (inpatient), EMER (emergency)"
    )

    @validator("class_code")
    def validate_class_code(cls, v):
        valid_codes = ["AMB", "IMP", "EMER", "VR", "HH"]  # AMB, Inpatient, Emergency, Virtual, Home Health
        if v.upper() not in valid_codes:
            raise ValueError(f"class_code must be one of: {', '.join(valid_codes)}")
        return v.upper()

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "patient_id": "patient-uuid",
                "practitioner_id": "practitioner-uuid",
                "appointment_id": "appointment-uuid",
                "class_code": "AMB"
            }
        }


class EncounterUpdate(BaseModel):
    """Schema for updating an encounter"""

    status: Optional[str] = Field(
        None,
        description="Encounter status: planned, in-progress, completed, cancelled"
    )
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

    @validator("status")
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = ["planned", "in-progress", "completed", "cancelled"]
            if v.lower() not in valid_statuses:
                raise ValueError(f"status must be one of: {', '.join(valid_statuses)}")
            return v.lower()
        return v

    @validator("ended_at")
    def validate_ended_at(cls, v, values):
        if v and "started_at" in values and values["started_at"]:
            if v <= values["started_at"]:
                raise ValueError("ended_at must be after started_at")
        return v


class EncounterResponse(BaseModel):
    """Response schema for encounter"""

    id: UUID
    tenant_id: UUID
    encounter_fhir_id: str
    patient_id: UUID
    practitioner_id: UUID
    appointment_id: Optional[UUID] = None
    status: str
    class_code: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "encounter-uuid",
                "tenant_id": "tenant-uuid",
                "encounter_fhir_id": "enc-12345",
                "patient_id": "patient-uuid",
                "practitioner_id": "practitioner-uuid",
                "appointment_id": "appointment-uuid",
                "status": "in-progress",
                "class_code": "AMB",
                "started_at": "2025-01-15T10:00:00Z",
                "ended_at": None,
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z"
            }
        }


class EncounterListResponse(BaseModel):
    """Response for list of encounters"""

    total: int
    encounters: list[EncounterResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


class EncounterWithDetails(BaseModel):
    """Encounter with full details including patient and practitioner names"""

    id: UUID
    tenant_id: UUID
    encounter_fhir_id: str
    patient_id: UUID
    patient_name: Optional[str] = None
    practitioner_id: UUID
    practitioner_name: Optional[str] = None
    status: str
    class_code: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    created_at: datetime


class EncounterCompleteRequest(BaseModel):
    """Request to complete an encounter"""

    ended_at: Optional[datetime] = Field(
        None,
        description="Time encounter ended (defaults to now)"
    )
    notes: Optional[str] = Field(
        None,
        max_length=5000,
        description="Optional completion notes"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "ended_at": "2025-01-15T10:30:00Z",
                "notes": "Patient stable, follow-up in 2 weeks"
            }
        }
