"""
Journey Management Schemas
Request/Response models for journey orchestration
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum


# ==================== Enums ====================

class JourneyType(str, Enum):
    """Journey type enumeration"""
    OPD = "opd"
    IPD = "ipd"
    PROCEDURE = "procedure"
    CHRONIC_CARE = "chronic_care"
    WELLNESS = "wellness"


class JourneyStatus(str, Enum):
    """Journey status enumeration"""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class StageStatus(str, Enum):
    """Stage status enumeration"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


# ==================== Journey Schemas ====================

class JourneyStageCreate(BaseModel):
    """Schema for creating a journey stage"""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    order_index: int = Field(..., ge=0)
    trigger_event: Optional[str] = None
    actions: Optional[Dict[str, Any]] = Field(default_factory=dict)


class JourneyStageUpdate(BaseModel):
    """Schema for updating a journey stage"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    order_index: Optional[int] = Field(None, ge=0)
    trigger_event: Optional[str] = None
    actions: Optional[Dict[str, Any]] = None


class JourneyStageResponse(BaseModel):
    """Response schema for journey stage"""

    id: UUID
    journey_id: UUID
    name: str
    description: Optional[str] = None
    order_index: int
    trigger_event: Optional[str] = None
    actions: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JourneyCreate(BaseModel):
    """Schema for creating a journey definition"""

    tenant_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    journey_type: JourneyType
    is_default: bool = Field(default=False)
    trigger_conditions: Optional[Dict[str, Any]] = Field(default_factory=dict)
    stages: Optional[List[JourneyStageCreate]] = Field(default_factory=list)


class JourneyUpdate(BaseModel):
    """Schema for updating a journey definition"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_default: Optional[bool] = None
    trigger_conditions: Optional[Dict[str, Any]] = None


class JourneyResponse(BaseModel):
    """Response schema for journey definition"""

    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str] = None
    journey_type: str
    is_default: bool
    trigger_conditions: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    stages: List[JourneyStageResponse] = []

    class Config:
        from_attributes = True


class JourneyListResponse(BaseModel):
    """Response for list of journeys"""

    total: int
    journeys: List[JourneyResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== Journey Instance Schemas ====================

class JourneyInstanceCreate(BaseModel):
    """Schema for creating a journey instance"""

    tenant_id: UUID
    journey_id: UUID
    patient_id: UUID
    appointment_id: Optional[UUID] = None
    encounter_id: Optional[UUID] = None
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)


class JourneyInstanceUpdate(BaseModel):
    """Schema for updating a journey instance"""

    status: Optional[JourneyStatus] = None
    current_stage_id: Optional[UUID] = None
    context: Optional[Dict[str, Any]] = None
    completed_at: Optional[datetime] = None


class JourneyInstanceResponse(BaseModel):
    """Response schema for journey instance"""

    id: UUID
    tenant_id: UUID
    journey_id: UUID
    patient_id: UUID
    appointment_id: Optional[UUID] = None
    encounter_id: Optional[UUID] = None
    status: str
    current_stage_id: Optional[UUID] = None
    context: Optional[Dict[str, Any]] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JourneyInstanceWithStages(BaseModel):
    """Journey instance with stage statuses"""

    id: UUID
    tenant_id: UUID
    journey_id: UUID
    journey_name: str
    patient_id: UUID
    status: str
    current_stage_id: Optional[UUID] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    stages: List[Dict[str, Any]] = Field(default_factory=list)


class JourneyInstanceListResponse(BaseModel):
    """Response for list of journey instances"""

    total: int
    instances: List[JourneyInstanceResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


class AdvanceStageRequest(BaseModel):
    """Request to advance journey to next stage"""

    force: bool = Field(default=False)
    notes: Optional[str] = Field(None, max_length=2000)
