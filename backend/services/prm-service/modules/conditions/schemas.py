"""
Condition Schemas
Pydantic models for condition API
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class ConditionCode(BaseModel):
    """Code for condition (ICD-10, SNOMED)"""
    system: str = "http://snomed.info/sct"  # ICD-10, SNOMED-CT
    code: str
    display: Optional[str] = None


class ConditionCreate(BaseModel):
    """Schema for creating a condition"""
    tenant_id: UUID
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    recorder_id: Optional[UUID] = None  # Practitioner who recorded
    clinical_status: str = Field("active", max_length=50)  # active, recurrence, relapse, inactive, remission, resolved
    verification_status: str = Field("confirmed", max_length=50)  # unconfirmed, provisional, differential, confirmed
    category: str = Field("encounter-diagnosis", max_length=100)  # problem-list-item, encounter-diagnosis
    severity: Optional[str] = Field(None, max_length=50)  # mild, moderate, severe
    code: ConditionCode
    onset_datetime: Optional[datetime] = None
    abatement_datetime: Optional[datetime] = None  # When resolved
    note: Optional[str] = None
    meta_data: Dict[str, Any] = Field(default_factory=dict)


class ConditionUpdate(BaseModel):
    """Schema for updating a condition"""
    clinical_status: Optional[str] = Field(None, max_length=50)
    verification_status: Optional[str] = Field(None, max_length=50)
    severity: Optional[str] = Field(None, max_length=50)
    abatement_datetime: Optional[datetime] = None
    note: Optional[str] = None


class ConditionResponse(BaseModel):
    """Condition response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    fhir_id: str
    tenant_id: UUID
    resource_type: str = "Condition"
    patient_id: Optional[UUID] = None
    encounter_id: Optional[UUID] = None
    clinical_status: str
    verification_status: str
    category: str
    severity: Optional[str] = None
    code: ConditionCode
    onset_datetime: Optional[datetime] = None
    abatement_datetime: Optional[datetime] = None
    note: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ConditionListResponse(BaseModel):
    """Paginated condition list response"""
    items: List[ConditionResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool
