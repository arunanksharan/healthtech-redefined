"""Trial Management Service Schemas"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

# Trial Schemas
class TrialCreate(BaseModel):
    tenant_id: UUID
    code: str = Field(..., description="HF_TRIAL_001, STROKE_RCT_2025")
    title: str
    description: Optional[str] = None
    phase: str = Field(..., description="Phase I, Phase II, Phase III, Registry")
    sponsor_org_id: Optional[UUID] = None
    status: str = Field(default='draft', description="draft, recruiting, active, paused, completed, terminated")
    target_enrollment: Optional[int] = None
    inclusion_criteria: Optional[Dict[str, Any]] = None
    exclusion_criteria: Optional[Dict[str, Any]] = None
    registry_reference: Optional[str] = Field(None, description="ClinicalTrials.gov NCT number")

class TrialUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    target_enrollment: Optional[int] = None
    inclusion_criteria: Optional[Dict[str, Any]] = None
    exclusion_criteria: Optional[Dict[str, Any]] = None

class TrialResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    code: str
    title: str
    description: Optional[str]
    phase: str
    status: str
    target_enrollment: Optional[int]
    registry_reference: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    class Config:
        from_attributes = True

# Trial Arm Schemas
class TrialArmCreate(BaseModel):
    trial_id: UUID
    code: str = Field(..., description="CONTROL, INTERVENTION, PLACEBO")
    name: str
    description: Optional[str] = None
    randomization_ratio: int = Field(default=1, description="For 2:1, intervention=2, control=1")

class TrialArmResponse(BaseModel):
    id: UUID
    trial_id: UUID
    code: str
    name: str
    description: Optional[str]
    randomization_ratio: int
    created_at: datetime
    class Config:
        from_attributes = True

# Trial Visit Schemas
class TrialVisitCreate(BaseModel):
    trial_id: UUID
    code: str = Field(..., description="V1_BASELINE, V2_WEEK1, V3_MONTH1")
    name: str
    visit_day: int = Field(..., description="0 for baseline, 7 for week 1, etc")
    window_days_before: int = Field(default=0)
    window_days_after: int = Field(default=0)
    is_required: bool = Field(default=True)

class TrialVisitResponse(BaseModel):
    id: UUID
    trial_id: UUID
    code: str
    name: str
    visit_day: int
    window_days_before: int
    window_days_after: int
    is_required: bool
    created_at: datetime
    class Config:
        from_attributes = True

# Trial Subject Schemas
class TrialSubjectCreate(BaseModel):
    trial_id: UUID
    patient_id: UUID
    pseudo_id_space_id: Optional[UUID] = None
    screening_status: str = Field(default='screening', description="screening, screen_failed, enrolled")
    consent_record_id: Optional[UUID] = None
    screening_notes: Optional[str] = None

class TrialSubjectUpdate(BaseModel):
    screening_status: Optional[str] = None
    arm_id: Optional[UUID] = None
    enrollment_date: Optional[date] = None
    withdrawal_date: Optional[date] = None
    withdrawal_reason: Optional[str] = None
    status: Optional[str] = None

class TrialSubjectResponse(BaseModel):
    id: UUID
    trial_id: UUID
    patient_id: UUID
    pseudo_patient_id: Optional[str]
    arm_id: Optional[UUID]
    screening_status: str
    enrollment_date: Optional[date]
    status: str
    withdrawal_date: Optional[date]
    withdrawal_reason: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

# Subject Randomization Request
class SubjectRandomizeRequest(BaseModel):
    subject_id: UUID
    enrollment_date: date

# Trial Subject Visit Schemas
class TrialSubjectVisitCreate(BaseModel):
    trial_subject_id: UUID
    trial_visit_id: UUID
    scheduled_date: date
    actual_date: Optional[date] = None
    status: str = Field(default='scheduled', description="scheduled, completed, missed, out_of_window")
    notes: Optional[str] = None

class TrialSubjectVisitUpdate(BaseModel):
    actual_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class TrialSubjectVisitResponse(BaseModel):
    id: UUID
    trial_subject_id: UUID
    trial_visit_id: UUID
    scheduled_date: date
    actual_date: Optional[date]
    status: str
    adherence_status: Optional[str]
    notes: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

# Trial CRF Schemas
class TrialCRFCreate(BaseModel):
    trial_id: UUID
    code: str = Field(..., description="CRF_BASELINE, CRF_AE, CRF_VITALS")
    name: str
    form_version: str = Field(default='1.0')
    field_definitions: Dict[str, Any] = Field(..., description="JSON schema for form fields")
    associated_visit_codes: Optional[List[str]] = None

class TrialCRFResponse(BaseModel):
    id: UUID
    trial_id: UUID
    code: str
    name: str
    form_version: str
    field_definitions: Dict[str, Any]
    associated_visit_codes: Optional[List[str]]
    created_at: datetime
    class Config:
        from_attributes = True

# Trial CRF Response Schemas
class TrialCRFResponseCreate(BaseModel):
    trial_subject_id: UUID
    trial_crf_id: UUID
    trial_subject_visit_id: Optional[UUID] = None
    response_data: Dict[str, Any] = Field(..., description="Actual form data")
    completed_by_user_id: Optional[UUID] = None

class TrialCRFResponseResponse(BaseModel):
    id: UUID
    trial_subject_id: UUID
    trial_crf_id: UUID
    trial_subject_visit_id: Optional[UUID]
    response_data: Dict[str, Any]
    completed_at: datetime
    completed_by_user_id: Optional[UUID]
    created_at: datetime
    class Config:
        from_attributes = True

# Trial Protocol Deviation Schemas
class TrialProtocolDeviationCreate(BaseModel):
    trial_subject_id: UUID
    deviation_type: str = Field(..., description="missed_visit, out_of_window, protocol_violation")
    severity: str = Field(..., description="minor, major, critical")
    description: str
    related_visit_id: Optional[UUID] = None
    corrective_action: Optional[str] = None

class TrialProtocolDeviationResponse(BaseModel):
    id: UUID
    trial_subject_id: UUID
    deviation_type: str
    severity: str
    description: str
    related_visit_id: Optional[UUID]
    corrective_action: Optional[str]
    detected_at: datetime
    resolved_at: Optional[datetime]
    created_at: datetime
    class Config:
        from_attributes = True
