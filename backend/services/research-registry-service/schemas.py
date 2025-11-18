"""Research Registry Service Schemas"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

# Registry Schemas
class RegistryCreate(BaseModel):
    tenant_id: UUID
    code: str = Field(..., description="HF_REGISTRY, CKD_REGISTRY")
    name: str
    description: Optional[str] = None
    category: str = Field(..., description="disease, condition, population")
    status: str = Field(default='draft', description="draft, active, closed")
    inclusion_criteria: Optional[Dict[str, Any]] = None
    exclusion_criteria: Optional[Dict[str, Any]] = None

class RegistryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    inclusion_criteria: Optional[Dict[str, Any]] = None
    exclusion_criteria: Optional[Dict[str, Any]] = None

class RegistryResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    code: str
    name: str
    description: Optional[str]
    category: str
    status: str
    inclusion_criteria: Optional[Dict[str, Any]]
    exclusion_criteria: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]
    class Config:
        from_attributes = True

# Registry Criteria Schemas
class RegistryCriteriaCreate(BaseModel):
    registry_id: UUID
    criterion_type: str = Field(..., description="inclusion, exclusion")
    category: str = Field(..., description="diagnosis, lab, medication, age")
    logic_expression: Dict[str, Any] = Field(..., description="DSL for criteria evaluation")
    description: Optional[str] = None

class RegistryCriteriaResponse(BaseModel):
    id: UUID
    registry_id: UUID
    criterion_type: str
    category: str
    logic_expression: Dict[str, Any]
    description: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

# Registry Enrollment Schemas
class RegistryEnrollmentCreate(BaseModel):
    registry_id: UUID
    patient_id: UUID
    enrollment_date: date
    consent_record_id: Optional[UUID] = None
    enrollment_source: str = Field(default='manual', description="manual, auto, import")

class RegistryEnrollmentUpdate(BaseModel):
    status: Optional[str] = None
    withdrawal_date: Optional[date] = None
    withdrawal_reason: Optional[str] = None

class RegistryEnrollmentResponse(BaseModel):
    id: UUID
    registry_id: UUID
    patient_id: UUID
    enrollment_date: date
    status: str
    consent_record_id: Optional[UUID]
    enrollment_source: str
    withdrawal_date: Optional[date]
    withdrawal_reason: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

# Registry Data Element Schemas
class RegistryDataElementCreate(BaseModel):
    registry_id: UUID
    code: str = Field(..., description="LVEF, NYHA_CLASS, NT_PROBNP")
    name: str
    data_type: str = Field(..., description="string, number, date, code")
    unit: Optional[str] = None
    collection_frequency: str = Field(..., description="baseline, monthly, quarterly, annual, event")
    source_path: Optional[str] = Field(None, description="FHIR path or query")

class RegistryDataElementResponse(BaseModel):
    id: UUID
    registry_id: UUID
    code: str
    name: str
    data_type: str
    unit: Optional[str]
    collection_frequency: str
    source_path: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

# Registry Data Value Schemas
class RegistryDataValueCreate(BaseModel):
    registry_enrollment_id: UUID
    data_element_id: UUID
    as_of_date: date
    value_string: Optional[str] = None
    value_number: Optional[float] = None
    value_date: Optional[date] = None
    value_code: Optional[str] = None
    source_reference: Optional[str] = None

class RegistryDataValueResponse(BaseModel):
    id: UUID
    registry_enrollment_id: UUID
    data_element_id: UUID
    as_of_date: date
    value_string: Optional[str]
    value_number: Optional[float]
    value_date: Optional[date]
    value_code: Optional[str]
    source_reference: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

# Bulk Data Refresh Schema
class RegistryDataRefreshRequest(BaseModel):
    registry_id: UUID
    enrollment_ids: Optional[List[UUID]] = Field(None, description="Specific enrollments or all if None")
    data_element_codes: Optional[List[str]] = Field(None, description="Specific elements or all if None")
    start_date: Optional[date] = None
    end_date: Optional[date] = None
