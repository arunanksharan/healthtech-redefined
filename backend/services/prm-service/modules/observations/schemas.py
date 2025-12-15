"""
Observation Schemas
Pydantic models for observation API
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class ObservationValue(BaseModel):
    """Value for an observation"""
    value: Optional[float] = None
    value_string: Optional[str] = None
    unit: Optional[str] = None
    system: Optional[str] = None  # UCUM, etc.
    code: Optional[str] = None


class ObservationCode(BaseModel):
    """Code for observation type"""
    system: str = "http://loinc.org"  # LOINC, SNOMED, etc.
    code: str
    display: Optional[str] = None


class ObservationCreate(BaseModel):
    """Schema for creating an observation"""
    tenant_id: UUID
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    practitioner_id: Optional[UUID] = None
    status: str = Field("final", max_length=50)  # registered, preliminary, final, amended
    category: str = Field("vital-signs", max_length=100)  # vital-signs, laboratory, imaging
    code: ObservationCode
    value: Optional[ObservationValue] = None
    effective_datetime: Optional[datetime] = None
    issued: Optional[datetime] = None
    interpretation: Optional[str] = None  # normal, abnormal, high, low
    note: Optional[str] = None
    meta_data: Dict[str, Any] = Field(default_factory=dict)


class ObservationResponse(BaseModel):
    """Observation response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    fhir_id: str
    tenant_id: UUID
    resource_type: str = "Observation"
    patient_id: Optional[UUID] = None
    encounter_id: Optional[UUID] = None
    status: str
    category: str
    code: ObservationCode
    value: Optional[ObservationValue] = None
    effective_datetime: Optional[datetime] = None
    interpretation: Optional[str] = None
    note: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ObservationListResponse(BaseModel):
    """Paginated observation list response"""
    items: List[ObservationResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool
