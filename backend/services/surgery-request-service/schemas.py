"""Surgery Request Service Schemas"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

# Surgery Procedure Catalog Schemas
class SurgeryProcedureCatalogCreate(BaseModel):
    tenant_id: UUID
    code: str
    name: str
    specialty: str
    body_site: Optional[str] = None
    description: Optional[str] = None
    typical_duration_minutes: Optional[int] = None
    fhir_code: Optional[str] = None
    default_priority: str = 'elective'
    default_anaesthesia_type: Optional[str] = None
    preop_required_labs: Optional[List[str]] = None
    preop_required_imaging: Optional[List[str]] = None

class SurgeryProcedureCatalogResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    code: str
    name: str
    specialty: str
    body_site: Optional[str]
    description: Optional[str]
    typical_duration_minutes: Optional[int]
    fhir_code: Optional[str]
    default_priority: str
    default_anaesthesia_type: Optional[str]
    preop_required_labs: Optional[List[str]]
    preop_required_imaging: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# Surgery Request Schemas
class SurgeryRequestCreate(BaseModel):
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    episode_id: Optional[UUID] = None
    procedure_catalog_id: UUID
    additional_procedure_text: Optional[str] = None
    indication: str
    urgency: str = Field(default='elective', description="elective, urgent, emergency")
    comments: Optional[str] = None

class SurgeryRequestUpdate(BaseModel):
    status: Optional[str] = None
    comments: Optional[str] = None
    urgency: Optional[str] = None

class SurgeryRequestResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    patient_id: UUID
    encounter_id: Optional[UUID]
    episode_id: Optional[UUID]
    requesting_practitioner_id: Optional[UUID]
    requesting_department_id: Optional[UUID]
    procedure_catalog_id: UUID
    additional_procedure_text: Optional[str]
    indication: str
    urgency: str
    status: str
    requested_date: datetime
    comments: Optional[str]
    fhir_service_request_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
