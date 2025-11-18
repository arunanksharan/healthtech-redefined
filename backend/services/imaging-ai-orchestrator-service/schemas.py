"""Imaging AI Orchestrator Service Schemas"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

# Imaging AI Model Schemas
class ImagingAIModelCreate(BaseModel):
    tenant_id: Optional[UUID] = None
    code: str = Field(..., description="CT_HEAD_ICH_TRIAGE, CXR_PNEUMONIA_DET")
    name: str
    description: Optional[str] = None
    modality_code: Optional[str] = None
    body_part: Optional[str] = None
    capabilities: Dict[str, Any] = Field(..., description='{"triage": true, "segmentation": false}')
    vendor: Optional[str] = None
    version: Optional[str] = None
    endpoint_config: Optional[Dict[str, Any]] = Field(None, description="Inference endpoint details")

class ImagingAIModelResponse(BaseModel):
    id: UUID
    code: str
    name: str
    modality_code: Optional[str]
    body_part: Optional[str]
    capabilities: Dict[str, Any]
    vendor: Optional[str]
    version: Optional[str]
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

# Imaging AI Task Schemas
class ImagingAITaskCreate(BaseModel):
    imaging_study_id: UUID
    ai_model_id: UUID
    task_type: str = Field(..., description="triage, quality, pre_report, comparison")

class ImagingAITaskResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    imaging_study_id: UUID
    ai_model_id: UUID
    task_type: str
    status: str
    requested_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

# Imaging AI Output Schemas
class ImagingAIOutputCreate(BaseModel):
    imaging_ai_task_id: UUID
    output_type: str = Field(..., description="triage, finding_list, bbox, suggested_report")
    payload: Dict[str, Any]

class ImagingAIOutputResponse(BaseModel):
    id: UUID
    imaging_ai_task_id: UUID
    output_type: str
    payload: Dict[str, Any]
    created_at: datetime
    class Config:
        from_attributes = True
