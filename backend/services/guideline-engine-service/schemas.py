"""Guideline Engine / CDS Service Schemas"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

# Guideline Schemas
class GuidelineCreate(BaseModel):
    tenant_id: UUID
    code: str = Field(..., description="HF_CHRONIC, SEPSIS_ED, STROKE_TPA")
    name: str
    description: Optional[str] = None
    specialty: str = Field(..., description="cardiology, emergency, neurology")
    source: str = Field(..., description="AHA_2023, NICE, WHO")
    category: str = Field(..., description="treatment, diagnosis, screening")

class GuidelineResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    code: str
    name: str
    description: Optional[str]
    specialty: str
    source: str
    category: str
    created_at: datetime
    class Config:
        from_attributes = True

# Guideline Version Schemas
class GuidelineVersionCreate(BaseModel):
    guideline_id: UUID
    version_code: str = Field(..., description="v1, v1.1, 2025")
    description: Optional[str] = None
    effective_from: datetime
    effective_to: Optional[datetime] = None
    status: str = Field(default='draft', description="draft, active, deprecated")
    content: Dict[str, Any] = Field(..., description="Guideline content and logic")

class GuidelineVersionUpdate(BaseModel):
    status: Optional[str] = None
    effective_to: Optional[datetime] = None

class GuidelineVersionResponse(BaseModel):
    id: UUID
    guideline_id: UUID
    version_code: str
    description: Optional[str]
    effective_from: datetime
    effective_to: Optional[datetime]
    status: str
    content: Dict[str, Any]
    created_at: datetime
    class Config:
        from_attributes = True

# CDS Rule Schemas
class CDSRuleCreate(BaseModel):
    guideline_version_id: UUID
    code: str = Field(..., description="RULE_HF_START_ACEI, RULE_SEPSIS_LACTATE")
    name: str
    description: Optional[str] = None
    trigger_context: str = Field(..., description="OPD_VISIT, IPD_ADMISSION, LAB_RESULT")
    priority: str = Field(default='info', description="info, warning, critical")
    logic_expression: Dict[str, Any] = Field(..., description="DSL for rule evaluation")
    action_suggestions: Optional[Dict[str, Any]] = None

class CDSRuleResponse(BaseModel):
    id: UUID
    guideline_version_id: UUID
    code: str
    name: str
    description: Optional[str]
    trigger_context: str
    priority: str
    logic_expression: Dict[str, Any]
    action_suggestions: Optional[Dict[str, Any]]
    created_at: datetime
    class Config:
        from_attributes = True

# CDS Rule Trigger Schemas
class CDSRuleTriggerCreate(BaseModel):
    cds_rule_id: UUID
    trigger_event_type: str = Field(..., description="Admission.Created, Lab.Resulted")
    filter_criteria: Optional[Dict[str, Any]] = None

class CDSRuleTriggerResponse(BaseModel):
    id: UUID
    cds_rule_id: UUID
    trigger_event_type: str
    filter_criteria: Optional[Dict[str, Any]]
    created_at: datetime
    class Config:
        from_attributes = True

# CDS Evaluation Schemas
class CDSEvaluationRequest(BaseModel):
    guideline_code: Optional[str] = None
    trigger_context: str
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    context_data: Dict[str, Any] = Field(..., description="Patient data for evaluation")

class CDSEvaluationResponse(BaseModel):
    id: UUID
    cds_rule_id: UUID
    patient_id: Optional[UUID]
    encounter_id: Optional[UUID]
    evaluated_at: datetime
    result: str
    card_payload: Optional[Dict[str, Any]]
    accepted: Optional[bool]
    feedback_notes: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

# CDS Feedback Schema
class CDSFeedbackRequest(BaseModel):
    evaluation_id: UUID
    accepted: bool
    feedback_notes: Optional[str] = None
    action_taken: Optional[str] = None
