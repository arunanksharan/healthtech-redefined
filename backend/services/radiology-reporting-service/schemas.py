"""Radiology Reporting Service Schemas"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

# Radiology Report Template Schemas
class RadiologyReportTemplateCreate(BaseModel):
    tenant_id: UUID
    code: str = Field(..., description="CT_HEAD_STROKE, US_ABD_GENERAL")
    name: str
    modality_code: Optional[str] = None
    body_part: Optional[str] = None
    description: Optional[str] = None
    template_type: str = Field(..., description="free_text, structured, hybrid")
    schema: Optional[Dict[str, Any]] = Field(None, description="For structured fields")
    default_text: Optional[str] = Field(None, description="Base narrative template")

class RadiologyReportTemplateResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    code: str
    name: str
    modality_code: Optional[str]
    body_part: Optional[str]
    template_type: str
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

# Radiology Report Schemas
class RadiologyReportCreate(BaseModel):
    imaging_study_id: UUID
    imaging_order_id: Optional[UUID] = None
    patient_id: UUID
    radiologist_id: Optional[UUID] = None
    template_id: Optional[UUID] = None
    clinical_history: Optional[str] = None
    technique: Optional[str] = None
    findings: Optional[str] = None
    impression: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None

class RadiologyReportUpdate(BaseModel):
    clinical_history: Optional[str] = None
    technique: Optional[str] = None
    findings: Optional[str] = None
    impression: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    ai_assist_summary: Optional[Dict[str, Any]] = None
    critical_result: Optional[bool] = None

class RadiologyReportResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    imaging_study_id: UUID
    patient_id: UUID
    radiologist_id: Optional[UUID]
    template_id: Optional[UUID]
    status: str
    clinical_history: Optional[str]
    technique: Optional[str]
    findings: Optional[str]
    impression: Optional[str]
    structured_data: Optional[Dict[str, Any]]
    critical_result: bool
    signed_at: Optional[datetime]
    signed_by_radiologist_id: Optional[UUID]
    created_at: datetime
    class Config:
        from_attributes = True

# Report Signing Schema
class ReportSignRequest(BaseModel):
    final: bool = Field(default=True, description="True for final, False for preliminary")

# Report Addendum Schemas
class RadiologyReportAddendumCreate(BaseModel):
    radiology_report_id: UUID
    added_by_radiologist_id: Optional[UUID] = None
    content: str

class RadiologyReportAddendumResponse(BaseModel):
    id: UUID
    radiology_report_id: UUID
    added_by_radiologist_id: Optional[UUID]
    content: str
    created_at: datetime
    class Config:
        from_attributes = True
