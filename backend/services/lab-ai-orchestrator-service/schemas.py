"""Lab AI Orchestrator Service Schemas"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

# Lab AI Model Schemas
class LabAIModelCreate(BaseModel):
    tenant_id: Optional[UUID] = None
    code: str = Field(..., description="LFT_INTERPRETER, CBC_TREND, MICRO_ABX_ANALYTICS")
    name: str
    description: Optional[str] = None
    domain: str = Field(..., description="core_lab, micro, ap")
    capabilities: Optional[Dict[str, Any]] = None
    endpoint_config: Optional[Dict[str, Any]] = None

class LabAIModelResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str]
    domain: str
    capabilities: Optional[Dict[str, Any]]
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

# Lab AI Task Schemas
class LabAITaskCreate(BaseModel):
    domain: str = Field(..., description="core_lab, micro, ap")
    patient_id: Optional[UUID] = None
    lab_result_id: Optional[UUID] = None
    ap_report_id: Optional[UUID] = None
    ai_model_id: UUID
    task_type: str = Field(..., description="interpretation, trend_summary, reflex_suggestion, synoptic_suggestion")

class LabAITaskResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    domain: str
    patient_id: Optional[UUID]
    lab_result_id: Optional[UUID]
    ap_report_id: Optional[UUID]
    ai_model_id: UUID
    task_type: str
    status: str
    requested_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

# Lab AI Output Schemas
class LabAIOutputCreate(BaseModel):
    lab_ai_task_id: UUID
    output_type: str = Field(..., description="patient_summary, clinician_comment, ap_synoptic")
    payload: Dict[str, Any]

class LabAIOutputResponse(BaseModel):
    id: UUID
    lab_ai_task_id: UUID
    output_type: str
    payload: Dict[str, Any]
    created_at: datetime
    class Config:
        from_attributes = True
