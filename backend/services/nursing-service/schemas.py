"""
Nursing Service Pydantic Schemas
Request/Response models for nursing tasks and observations
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator


# ==================== Nursing Task Schemas ====================

class NursingTaskCreate(BaseModel):
    """Schema for creating a nursing task"""

    tenant_id: UUID
    admission_id: UUID
    encounter_id: UUID
    patient_id: UUID
    bed_assignment_id: Optional[UUID] = None
    ward_id: Optional[UUID] = None
    created_by_user_id: Optional[UUID] = None
    assigned_to_user_id: Optional[UUID] = None
    task_type: str = Field(..., description="medication, vitals, procedure, education, hygiene, assessment")
    description: str = Field(..., min_length=1)
    priority: str = Field(default="normal", description="low, normal, high, critical")
    due_at: Optional[datetime] = None

    @validator("task_type")
    def validate_task_type(cls, v):
        valid_types = ["medication", "vitals", "procedure", "education", "hygiene", "assessment", "other"]
        if v.lower() not in valid_types:
            raise ValueError(f"task_type must be one of: {', '.join(valid_types)}")
        return v.lower()

    @validator("priority")
    def validate_priority(cls, v):
        valid_priorities = ["low", "normal", "high", "critical"]
        if v.lower() not in valid_priorities:
            raise ValueError(f"priority must be one of: {', '.join(valid_priorities)}")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "admission_id": "admission-uuid",
                "encounter_id": "encounter-uuid",
                "patient_id": "patient-uuid",
                "ward_id": "ward-uuid",
                "task_type": "vitals",
                "description": "Record BP, HR, Temp, SpO2",
                "priority": "normal",
                "due_at": "2025-01-15T14:00:00Z"
            }
        }


class NursingTaskUpdate(BaseModel):
    """Schema for updating a nursing task"""

    assigned_to_user_id: Optional[UUID] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    due_at: Optional[datetime] = None
    status: Optional[str] = Field(None, description="open, in_progress, completed, cancelled")

    @validator("status")
    def validate_status(cls, v):
        if v:
            valid_statuses = ["open", "in_progress", "completed", "cancelled"]
            if v.lower() not in valid_statuses:
                raise ValueError(f"status must be one of: {', '.join(valid_statuses)}")
            return v.lower()
        return v


class NursingTaskComplete(BaseModel):
    """Schema for completing a nursing task"""

    completed_at: Optional[datetime] = None
    completion_notes: Optional[str] = None


class NursingTaskResponse(BaseModel):
    """Response schema for nursing task"""

    id: UUID
    tenant_id: UUID
    admission_id: UUID
    encounter_id: UUID
    patient_id: UUID
    bed_assignment_id: Optional[UUID] = None
    ward_id: Optional[UUID] = None
    created_by_user_id: Optional[UUID] = None
    assigned_to_user_id: Optional[UUID] = None
    task_type: str
    description: str
    priority: str
    due_at: Optional[datetime] = None
    status: str
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NursingTaskWithDetails(BaseModel):
    """Nursing task with patient and ward details"""

    id: UUID
    patient_id: UUID
    patient_name: str
    ward_name: Optional[str] = None
    bed_code: Optional[str] = None
    task_type: str
    description: str
    priority: str
    due_at: Optional[datetime] = None
    status: str
    assigned_to_user_id: Optional[UUID] = None
    overdue: bool = False


class NursingTaskListResponse(BaseModel):
    """Response for list of nursing tasks"""

    total: int
    tasks: List[NursingTaskResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== Nursing Observation Schemas ====================

class NursingObservationCreate(BaseModel):
    """Schema for creating a nursing observation"""

    tenant_id: UUID
    admission_id: UUID
    encounter_id: UUID
    patient_id: UUID
    bed_assignment_id: Optional[UUID] = None
    observed_by_user_id: Optional[UUID] = None
    observation_type: str = Field(..., description="vitals, pain, wound, io, other")
    observation_time: Optional[datetime] = None
    data: Dict[str, Any] = Field(..., description="Structured observation data")

    @validator("observation_type")
    def validate_observation_type(cls, v):
        valid_types = ["vitals", "pain", "wound", "io", "assessment", "other"]
        if v.lower() not in valid_types:
            raise ValueError(f"observation_type must be one of: {', '.join(valid_types)}")
        return v.lower()

    @validator("data")
    def validate_vitals_data(cls, v, values):
        """Validate vitals data structure"""
        if values.get("observation_type") == "vitals":
            # Common vital signs
            valid_fields = [
                "temperature", "temp_unit",
                "bp_systolic", "bp_diastolic",
                "heart_rate", "respiratory_rate",
                "spo2", "pain_score",
                "consciousness_level", "urine_output"
            ]

            # At least one vital sign should be present
            if not any(field in v for field in valid_fields):
                raise ValueError("Vitals observation must contain at least one vital sign")

        return v

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "admission_id": "admission-uuid",
                "encounter_id": "encounter-uuid",
                "patient_id": "patient-uuid",
                "observation_type": "vitals",
                "observation_time": "2025-01-15T14:30:00Z",
                "data": {
                    "temperature": 37.5,
                    "temp_unit": "C",
                    "bp_systolic": 120,
                    "bp_diastolic": 80,
                    "heart_rate": 72,
                    "respiratory_rate": 16,
                    "spo2": 98,
                    "pain_score": 2
                }
            }
        }


class NursingObservationResponse(BaseModel):
    """Response schema for nursing observation"""

    id: UUID
    tenant_id: UUID
    admission_id: UUID
    encounter_id: UUID
    patient_id: UUID
    bed_assignment_id: Optional[UUID] = None
    observed_by_user_id: Optional[UUID] = None
    observation_type: str
    observation_time: datetime
    data: Dict[str, Any]
    fhir_observation_ids: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NursingObservationListResponse(BaseModel):
    """Response for list of nursing observations"""

    total: int
    observations: List[NursingObservationResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== Vitals Chart Schema ====================

class VitalsChartResponse(BaseModel):
    """Response for vitals chart/trend"""

    patient_id: UUID
    from_date: datetime
    to_date: datetime
    data_points: List[Dict[str, Any]]
    summary: Dict[str, Any]
