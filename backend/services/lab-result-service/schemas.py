"""Lab Result Service Schemas"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, Decimal
from pydantic import BaseModel, Field

# Lab Result Value Schemas
class LabResultValueCreate(BaseModel):
    component_lab_test_id: Optional[UUID] = None
    component_code: Optional[str] = None
    value_numeric: Optional[float] = None
    value_text: Optional[str] = None
    value_code: Optional[str] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    flag: Optional[str] = Field(None, description="L, H, LL, HH, N, A")

class LabResultValueResponse(BaseModel):
    id: UUID
    lab_result_id: UUID
    component_lab_test_id: Optional[UUID]
    component_code: Optional[str]
    value_numeric: Optional[float]
    value_text: Optional[str]
    value_code: Optional[str]
    unit: Optional[str]
    reference_range: Optional[str]
    flag: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

# Microbiology Schemas
class LabMicroSusceptibilityCreate(BaseModel):
    antibiotic_code: Optional[str] = None
    antibiotic_name: str
    mic_value: Optional[float] = None
    mic_unit: Optional[str] = None
    interpretation: str = Field(..., description="S, I, R")

class LabMicroSusceptibilityResponse(BaseModel):
    id: UUID
    antibiotic_code: Optional[str]
    antibiotic_name: str
    mic_value: Optional[float]
    mic_unit: Optional[str]
    interpretation: str
    created_at: datetime
    class Config:
        from_attributes = True

class LabMicroOrganismCreate(BaseModel):
    organism_code: Optional[str] = None
    organism_name: str
    quantity: Optional[str] = Field(None, description="heavy growth, scanty")
    comments: Optional[str] = None
    susceptibilities: Optional[List[LabMicroSusceptibilityCreate]] = []

class LabMicroOrganismResponse(BaseModel):
    id: UUID
    organism_code: Optional[str]
    organism_name: str
    quantity: Optional[str]
    comments: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

# Lab Result Schemas
class LabResultCreate(BaseModel):
    lab_order_id: UUID
    lab_order_item_id: Optional[UUID] = None
    lab_test_id: UUID
    patient_id: UUID
    specimen_id: Optional[UUID] = None
    analyzer_run_id: Optional[str] = None
    result_time: datetime
    entry_source: str = Field(default='manual', description="manual, analyzer_import")
    comments: Optional[str] = None
    result_values: Optional[List[LabResultValueCreate]] = []
    micro_organisms: Optional[List[LabMicroOrganismCreate]] = []

class LabResultUpdate(BaseModel):
    status: Optional[str] = Field(None, description="preliminary, final, corrected, cancelled")
    is_critical: Optional[bool] = None
    critical_notified: Optional[bool] = None
    critical_notification_details: Optional[str] = None
    comments: Optional[str] = None

class LabResultResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    lab_order_id: UUID
    lab_order_item_id: Optional[UUID]
    lab_test_id: UUID
    patient_id: UUID
    specimen_id: Optional[UUID]
    analyzer_run_id: Optional[str]
    status: str
    result_time: datetime
    validated_by_user_id: Optional[UUID]
    validated_at: Optional[datetime]
    entered_by_user_id: Optional[UUID]
    entry_source: str
    comments: Optional[str]
    is_critical: bool
    critical_notified: bool
    critical_notification_details: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True
