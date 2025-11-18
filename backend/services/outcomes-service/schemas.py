"""
Outcomes Service Pydantic Schemas
Request/Response models for episodes, outcomes, PROMs, and PREMs
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator


# ==================== Episode Schemas ====================

class EpisodeCreate(BaseModel):
    """Schema for creating an episode"""

    tenant_id: UUID
    patient_id: UUID
    index_encounter_id: Optional[UUID] = None
    index_admission_id: Optional[UUID] = None
    care_type: str = Field(..., description="OPD, IPD, OPD_IPD, DAY_CARE")
    specialty: Optional[str] = None
    primary_condition_code: Optional[str] = Field(None, description="SNOMED or ICD code")
    started_at: Optional[datetime] = None

    @validator("care_type")
    def validate_care_type(cls, v):
        valid_types = ["OPD", "IPD", "OPD_IPD", "DAY_CARE"]
        if v.upper() not in valid_types:
            raise ValueError(f"care_type must be one of: {', '.join(valid_types)}")
        return v.upper()

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "patient_id": "patient-uuid",
                "index_encounter_id": "encounter-uuid",
                "care_type": "OPD",
                "specialty": "CARDIOLOGY",
                "primary_condition_code": "I21.9",
                "started_at": "2025-01-15T09:00:00Z"
            }
        }


class EpisodeUpdate(BaseModel):
    """Schema for updating an episode"""

    specialty: Optional[str] = None
    primary_condition_code: Optional[str] = None
    ended_at: Optional[datetime] = None
    status: Optional[str] = Field(None, description="active, completed, abandoned")

    @validator("status")
    def validate_status(cls, v):
        if v:
            valid_statuses = ["active", "completed", "abandoned"]
            if v.lower() not in valid_statuses:
                raise ValueError(f"status must be one of: {', '.join(valid_statuses)}")
            return v.lower()
        return v


class EpisodeResponse(BaseModel):
    """Response schema for episode"""

    id: UUID
    tenant_id: UUID
    patient_id: UUID
    episode_of_care_fhir_id: Optional[str] = None
    index_encounter_id: Optional[UUID] = None
    index_admission_id: Optional[UUID] = None
    care_type: str
    specialty: Optional[str] = None
    primary_condition_code: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EpisodeListResponse(BaseModel):
    """Response for list of episodes"""

    total: int
    episodes: List[EpisodeResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== Outcome Schemas ====================

class OutcomeCreate(BaseModel):
    """Schema for creating an outcome"""

    tenant_id: UUID
    episode_id: UUID
    outcome_type: str = Field(..., description="mortality, readmission_30d, complication, functional_status")
    outcome_subtype: Optional[str] = Field(None, description="all_cause, cardiac, AKI_stage2")
    value: Optional[str] = None
    numeric_value: Optional[float] = None
    unit: Optional[str] = None
    occurred_at: Optional[datetime] = None
    derived_from: str = Field(default="manual_entry", description="manual_entry, rules_engine, ml_model")
    source_event_id: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "episode_id": "episode-uuid",
                "outcome_type": "readmission_30d",
                "outcome_subtype": "all_cause",
                "value": "yes",
                "occurred_at": "2025-02-14T10:00:00Z",
                "derived_from": "rules_engine"
            }
        }


class OutcomeResponse(BaseModel):
    """Response schema for outcome"""

    id: UUID
    tenant_id: UUID
    episode_id: UUID
    outcome_type: str
    outcome_subtype: Optional[str] = None
    value: Optional[str] = None
    numeric_value: Optional[float] = None
    unit: Optional[str] = None
    occurred_at: Optional[datetime] = None
    derived_from: str
    source_event_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class OutcomeListResponse(BaseModel):
    """Response for list of outcomes"""

    total: int
    outcomes: List[OutcomeResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== PROM Schemas ====================

class PROMCreate(BaseModel):
    """Schema for creating a PROM"""

    tenant_id: UUID
    episode_id: UUID
    patient_id: UUID
    instrument_code: str = Field(..., description="EQ5D, PROMIS_PAIN, etc.")
    version: Optional[str] = None
    responses: Dict[str, Any] = Field(..., description="Question-answer map")
    score: Optional[float] = None
    completed_at: Optional[datetime] = None
    mode: str = Field(default="web", description="web, sms, phone, in_clinic")

    @validator("mode")
    def validate_mode(cls, v):
        valid_modes = ["web", "sms", "phone", "in_clinic", "app"]
        if v.lower() not in valid_modes:
            raise ValueError(f"mode must be one of: {', '.join(valid_modes)}")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "episode_id": "episode-uuid",
                "patient_id": "patient-uuid",
                "instrument_code": "EQ5D",
                "version": "5L",
                "responses": {
                    "mobility": "no_problems",
                    "self_care": "no_problems",
                    "usual_activities": "slight_problems",
                    "pain_discomfort": "moderate_problems",
                    "anxiety_depression": "no_problems"
                },
                "score": 0.85,
                "completed_at": "2025-01-15T14:00:00Z",
                "mode": "web"
            }
        }


class PROMResponse(BaseModel):
    """Response schema for PROM"""

    id: UUID
    tenant_id: UUID
    episode_id: UUID
    patient_id: UUID
    instrument_code: str
    version: Optional[str] = None
    responses: Dict[str, Any]
    score: Optional[float] = None
    completed_at: datetime
    mode: str
    created_at: datetime

    class Config:
        from_attributes = True


class PROMListResponse(BaseModel):
    """Response for list of PROMs"""

    total: int
    proms: List[PROMResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== PREM Schemas ====================

class PREMCreate(BaseModel):
    """Schema for creating a PREM"""

    tenant_id: UUID
    episode_id: UUID
    patient_id: UUID
    instrument_code: str = Field(..., description="HCAHPS, NPS, etc.")
    responses: Dict[str, Any] = Field(..., description="Question-answer map")
    score: Optional[float] = None
    completed_at: Optional[datetime] = None
    mode: str = Field(default="web")

    @validator("mode")
    def validate_mode(cls, v):
        valid_modes = ["web", "sms", "phone", "in_clinic", "app"]
        if v.lower() not in valid_modes:
            raise ValueError(f"mode must be one of: {', '.join(valid_modes)}")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "episode_id": "episode-uuid",
                "patient_id": "patient-uuid",
                "instrument_code": "NPS",
                "responses": {
                    "likelihood_to_recommend": 9,
                    "reason": "Excellent care and attentive staff"
                },
                "score": 9.0,
                "completed_at": "2025-01-15T16:00:00Z",
                "mode": "sms"
            }
        }


class PREMResponse(BaseModel):
    """Response schema for PREM"""

    id: UUID
    tenant_id: UUID
    episode_id: UUID
    patient_id: UUID
    instrument_code: str
    responses: Dict[str, Any]
    score: Optional[float] = None
    completed_at: datetime
    mode: str
    created_at: datetime

    class Config:
        from_attributes = True


class PREMListResponse(BaseModel):
    """Response for list of PREMs"""

    total: int
    prems: List[PREMResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool
