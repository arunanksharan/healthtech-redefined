"""Imaging Order Service Schemas"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

# Imaging Modality Schemas
class ImagingModalityCreate(BaseModel):
    tenant_id: UUID
    code: str = Field(..., description="CR, CT, MR, US, DX, MG, XA, NM, PT")
    name: str
    description: Optional[str] = None

class ImagingModalityResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    code: str
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

# Imaging Procedure Schemas
class ImagingProcedureCreate(BaseModel):
    tenant_id: UUID
    code: str = Field(..., description="CT_BRAIN_WO_CONTRAST, US_ABD_COMPLETE")
    name: str
    modality_id: UUID
    description: Optional[str] = None
    body_part: Optional[str] = None
    snomed_code: Optional[str] = None
    loinc_code: Optional[str] = None
    default_duration_minutes: Optional[int] = None
    preparation_instructions: Optional[str] = None

class ImagingProcedureResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    code: str
    name: str
    modality_id: UUID
    description: Optional[str]
    body_part: Optional[str]
    snomed_code: Optional[str]
    loinc_code: Optional[str]
    default_duration_minutes: Optional[int]
    preparation_instructions: Optional[str]
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

# Imaging Order Schemas
class ImagingOrderCreate(BaseModel):
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    episode_id: Optional[UUID] = None
    ordering_practitioner_id: Optional[UUID] = None
    ordering_department_id: Optional[UUID] = None
    imaging_procedure_id: UUID
    indication: str = Field(..., description="Clinical indication for imaging")
    priority: str = Field(default='routine', description="routine, urgent, stat")

class ImagingOrderUpdate(BaseModel):
    status: Optional[str] = None
    scheduled_slot_id: Optional[UUID] = None
    performed_start_at: Optional[datetime] = None
    performed_end_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

class ImagingOrderResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    patient_id: UUID
    encounter_id: Optional[UUID]
    episode_id: Optional[UUID]
    ordering_practitioner_id: Optional[UUID]
    imaging_procedure_id: UUID
    indication: str
    priority: str
    status: str
    requested_at: datetime
    scheduled_slot_id: Optional[UUID]
    performed_start_at: Optional[datetime]
    performed_end_at: Optional[datetime]
    fhir_service_request_id: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    class Config:
        from_attributes = True
