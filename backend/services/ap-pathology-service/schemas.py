"""AP Pathology Service Schemas"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

# AP Report Template Schemas
class APReportTemplateCreate(BaseModel):
    tenant_id: Optional[UUID] = None
    code: str = Field(..., description="BREAST_CA_RESECTION, COLON_POLYP")
    name: str
    description: Optional[str] = None
    site: Optional[str] = None
    schema: Dict[str, Any] = Field(..., description="Synoptic fields JSON schema")
    default_narrative: Optional[str] = None

class APReportTemplateResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str]
    site: Optional[str]
    schema: Dict[str, Any]
    default_narrative: Optional[str]
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

# AP Case Schemas
class APCaseCreate(BaseModel):
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    referring_practitioner_id: Optional[UUID] = None
    referring_department_id: Optional[UUID] = None
    clinical_history: Optional[str] = None
    pathologist_id: Optional[UUID] = None

class APCaseUpdate(BaseModel):
    status: Optional[str] = Field(None, description="accessioned, in_progress, reported, amended, cancelled")
    diagnosis_summary: Optional[str] = None
    pathologist_id: Optional[UUID] = None

class APCaseResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    case_number: str
    patient_id: UUID
    encounter_id: Optional[UUID]
    referring_practitioner_id: Optional[UUID]
    referring_department_id: Optional[UUID]
    received_date: datetime
    status: str
    clinical_history: Optional[str]
    diagnosis_summary: Optional[str]
    pathologist_id: Optional[UUID]
    created_at: datetime
    class Config:
        from_attributes = True

# AP Report Synoptic Value Schemas
class APReportSynopticValueCreate(BaseModel):
    field_code: str = Field(..., description="T_STAGE, N_STAGE, M_STAGE, MARGIN_STATUS")
    value_text: Optional[str] = None
    value_code: Optional[str] = None

class APReportSynopticValueResponse(BaseModel):
    id: UUID
    ap_report_id: UUID
    field_code: str
    value_text: Optional[str]
    value_code: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

# AP Report Schemas
class APReportCreate(BaseModel):
    ap_case_id: UUID
    template_id: Optional[UUID] = None
    gross_description: Optional[str] = None
    microscopic_description: Optional[str] = None
    diagnosis_text: Optional[str] = None
    comments: Optional[str] = None
    synoptic_values: Optional[List[APReportSynopticValueCreate]] = []

class APReportUpdate(BaseModel):
    gross_description: Optional[str] = None
    microscopic_description: Optional[str] = None
    diagnosis_text: Optional[str] = None
    comments: Optional[str] = None
    synoptic_values: Optional[List[APReportSynopticValueCreate]] = None

class APReportSignRequest(BaseModel):
    final: bool = Field(default=True, description="Mark as final vs preliminary")

class APReportResponse(BaseModel):
    id: UUID
    ap_case_id: UUID
    template_id: Optional[UUID]
    status: str
    gross_description: Optional[str]
    microscopic_description: Optional[str]
    diagnosis_text: Optional[str]
    comments: Optional[str]
    signed_at: Optional[datetime]
    signed_by_pathologist_id: Optional[UUID]
    created_at: datetime
    class Config:
        from_attributes = True
