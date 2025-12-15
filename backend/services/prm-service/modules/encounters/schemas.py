"""
Encounter Schemas
Pydantic models for encounter API
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class EncounterCreate(BaseModel):
    """Schema for creating an encounter"""
    tenant_id: UUID
    patient_id: UUID
    practitioner_id: UUID
    appointment_id: Optional[UUID] = None
    encounter_fhir_id: Optional[str] = Field(None, max_length=255)
    status: str = Field(..., max_length=50)  # planned, in-progress, completed, cancelled
    class_code: str = Field("AMB", max_length=50)  # AMB=outpatient, IMP=inpatient, EMER=emergency
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None


class EncounterUpdate(BaseModel):
    """Schema for updating an encounter"""
    status: Optional[str] = Field(None, max_length=50)
    class_code: Optional[str] = Field(None, max_length=50)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None


class EncounterResponse(BaseModel):
    """Encounter response schema"""
    model_config = ConfigDict(from_attributes=True)

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
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class EncounterListResponse(BaseModel):
    """Paginated encounter list response"""
    items: List[EncounterResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool
