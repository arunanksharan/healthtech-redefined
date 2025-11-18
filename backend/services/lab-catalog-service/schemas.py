"""Lab Catalog Service Schemas"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

# Lab Specimen Type Schemas
class LabSpecimenTypeCreate(BaseModel):
    tenant_id: Optional[UUID] = None
    code: str = Field(..., description="VEN_BLOOD, URINE, CSF, TISSUE")
    name: str
    description: Optional[str] = None
    container_type: Optional[str] = Field(None, description="EDTA_TUBE, SST_TUBE, etc.")
    handling_instructions: Optional[str] = None
    storage_temperature_range: Optional[str] = Field(None, description="e.g. 2-8C")
    stability_hours: Optional[int] = None

class LabSpecimenTypeResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str]
    container_type: Optional[str]
    handling_instructions: Optional[str]
    storage_temperature_range: Optional[str]
    stability_hours: Optional[int]
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

# Lab Test Schemas
class LabTestCreate(BaseModel):
    tenant_id: Optional[UUID] = None
    code: str = Field(..., description="CBC, HB, FBS, CRP, CREAT")
    name: str
    description: Optional[str] = None
    loinc_code: Optional[str] = None
    category: Optional[str] = Field(None, description="hematology, chemistry, immunology, micro, pathology")
    default_specimen_type_id: Optional[UUID] = None
    unit: Optional[str] = None
    reference_range: Optional[Dict[str, Any]] = Field(None, description='{"adult_male": "13-17 g/dL"}')
    critical_range: Optional[Dict[str, Any]] = Field(None, description='{"low": "< 6", "high": "> 20"}')
    is_panel: bool = False
    result_type: str = Field(default='numeric', description="numeric, text, categorical, qualitative")
    result_value_set: Optional[Dict[str, Any]] = Field(None, description="for categorical e.g. ['Positive','Negative']")

class LabTestResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str]
    loinc_code: Optional[str]
    category: Optional[str]
    default_specimen_type_id: Optional[UUID]
    unit: Optional[str]
    reference_range: Optional[Dict[str, Any]]
    critical_range: Optional[Dict[str, Any]]
    is_panel: bool
    is_active: bool
    result_type: str
    result_value_set: Optional[Dict[str, Any]]
    created_at: datetime
    class Config:
        from_attributes = True

# Lab Test Panel Schemas
class LabTestPanelCreate(BaseModel):
    lab_test_id: UUID
    panel_code: str = Field(..., description="LFT, RFT, LIPID_PROFILE")
    name: str
    description: Optional[str] = None

class LabTestPanelItemCreate(BaseModel):
    child_lab_test_id: UUID
    sort_order: Optional[int] = None

class LabTestPanelResponse(BaseModel):
    id: UUID
    lab_test_id: UUID
    panel_code: str
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True
