"""Radiology Worklist Service Schemas"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

# Radiology Reading Profile Schemas
class RadiologyReadingProfileCreate(BaseModel):
    tenant_id: UUID
    practitioner_id: UUID
    allowed_modalities: Optional[List[str]] = Field(None, description="['CT', 'MR', 'US']")
    allowed_body_parts: Optional[List[str]] = Field(None, description="['BRAIN', 'CHEST']")
    max_concurrent_cases: int = Field(default=5)
    reading_locations: Optional[List[str]] = Field(None, description="['MAIN_RAD_DEPT', 'REMOTE']")

class RadiologyReadingProfileUpdate(BaseModel):
    allowed_modalities: Optional[List[str]] = None
    allowed_body_parts: Optional[List[str]] = None
    max_concurrent_cases: Optional[int] = None
    reading_locations: Optional[List[str]] = None
    is_active: Optional[bool] = None

class RadiologyReadingProfileResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    practitioner_id: UUID
    allowed_modalities: Optional[List[str]]
    allowed_body_parts: Optional[List[str]]
    max_concurrent_cases: int
    reading_locations: Optional[List[str]]
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

# Radiology Worklist Item Schemas
class RadiologyWorklistItemCreate(BaseModel):
    imaging_study_id: UUID
    imaging_order_id: Optional[UUID] = None
    patient_id: UUID
    modality_code: str
    body_part: Optional[str] = None
    priority: str = Field(..., description="routine, urgent, stat")

class RadiologyWorklistItemUpdate(BaseModel):
    status: Optional[str] = None
    assigned_radiologist_id: Optional[UUID] = None
    ai_triage_score: Optional[float] = None
    ai_triage_flags: Optional[Dict[str, Any]] = None

class RadiologyWorklistItemResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    imaging_study_id: UUID
    imaging_order_id: Optional[UUID]
    patient_id: UUID
    modality_code: str
    body_part: Optional[str]
    priority: str
    status: str
    assigned_radiologist_id: Optional[UUID]
    claimed_at: Optional[datetime]
    last_activity_at: Optional[datetime]
    ai_triage_score: Optional[float]
    ai_triage_flags: Optional[Dict[str, Any]]
    created_at: datetime
    class Config:
        from_attributes = True
