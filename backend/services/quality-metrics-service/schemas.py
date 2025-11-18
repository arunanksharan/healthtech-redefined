"""
Quality Metrics Service Pydantic Schemas
Request/Response models for quality metrics, QI projects, and metric values
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator


# ==================== Quality Metric Schemas ====================

class QualityMetricCreate(BaseModel):
    """Schema for creating a quality metric"""

    tenant_id: UUID
    code: str = Field(..., description="Unique metric code (e.g., CAUTI_RATE, READMIT_30D)")
    name: str = Field(..., description="Human-readable metric name")
    category: str = Field(..., description="safety, effectiveness, patient_experience, efficiency, equity, timeliness")
    description: Optional[str] = None
    definition_dsl: Dict[str, Any] = Field(..., description="JSON DSL for metric calculation")
    unit: Optional[str] = Field(None, description="%, count, days, etc.")
    target_operator: Optional[str] = Field(None, description="<, <=, >, >=, =")
    target_value: Optional[float] = None
    calculation_frequency: str = Field(default="daily", description="hourly, daily, weekly, monthly")
    is_active: bool = Field(default=True)

    @validator("category")
    def validate_category(cls, v):
        valid_categories = ["safety", "effectiveness", "patient_experience", "efficiency", "equity", "timeliness"]
        if v.lower() not in valid_categories:
            raise ValueError(f"category must be one of: {', '.join(valid_categories)}")
        return v.lower()

    @validator("calculation_frequency")
    def validate_frequency(cls, v):
        valid_frequencies = ["hourly", "daily", "weekly", "monthly", "quarterly", "yearly"]
        if v.lower() not in valid_frequencies:
            raise ValueError(f"calculation_frequency must be one of: {', '.join(valid_frequencies)}")
        return v.lower()

    @validator("target_operator")
    def validate_operator(cls, v):
        if v:
            valid_operators = ["<", "<=", ">", ">=", "="]
            if v not in valid_operators:
                raise ValueError(f"target_operator must be one of: {', '.join(valid_operators)}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "code": "READMIT_30D_CARDIO",
                "name": "30-Day Readmission Rate - Cardiology",
                "category": "effectiveness",
                "description": "All-cause 30-day readmission rate for cardiology patients",
                "definition_dsl": {
                    "numerator": {
                        "type": "count",
                        "entity": "outcome",
                        "filters": [
                            {"field": "outcome_type", "op": "=", "value": "readmission_30d"},
                            {"field": "episode.specialty", "op": "=", "value": "CARDIOLOGY"}
                        ]
                    },
                    "denominator": {
                        "type": "count",
                        "entity": "episode",
                        "filters": [
                            {"field": "specialty", "op": "=", "value": "CARDIOLOGY"},
                            {"field": "status", "op": "=", "value": "completed"}
                        ]
                    }
                },
                "unit": "%",
                "target_operator": "<",
                "target_value": 15.0,
                "calculation_frequency": "daily"
            }
        }


class QualityMetricUpdate(BaseModel):
    """Schema for updating a quality metric"""

    name: Optional[str] = None
    description: Optional[str] = None
    definition_dsl: Optional[Dict[str, Any]] = None
    unit: Optional[str] = None
    target_operator: Optional[str] = None
    target_value: Optional[float] = None
    calculation_frequency: Optional[str] = None
    is_active: Optional[bool] = None

    @validator("target_operator")
    def validate_operator(cls, v):
        if v:
            valid_operators = ["<", "<=", ">", ">=", "="]
            if v not in valid_operators:
                raise ValueError(f"target_operator must be one of: {', '.join(valid_operators)}")
        return v


class QualityMetricResponse(BaseModel):
    """Response schema for quality metric"""

    id: UUID
    tenant_id: UUID
    code: str
    name: str
    category: str
    description: Optional[str] = None
    definition_dsl: Dict[str, Any]
    unit: Optional[str] = None
    target_operator: Optional[str] = None
    target_value: Optional[float] = None
    calculation_frequency: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QualityMetricListResponse(BaseModel):
    """Response for list of quality metrics"""

    total: int
    metrics: List[QualityMetricResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== Quality Metric Value Schemas ====================

class QualityMetricValueResponse(BaseModel):
    """Response schema for quality metric value (time-series data point)"""

    id: UUID
    tenant_id: UUID
    quality_metric_id: UUID
    period_start: datetime
    period_end: datetime
    numerator: Optional[float] = None
    denominator: Optional[float] = None
    value: float
    meets_target: Optional[bool] = None
    calculation_metadata: Optional[Dict[str, Any]] = None
    calculated_at: datetime

    class Config:
        from_attributes = True


class QualityMetricValueListResponse(BaseModel):
    """Response for list of quality metric values"""

    total: int
    values: List[QualityMetricValueResponse]
    metric: QualityMetricResponse
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


class RecalculateRequest(BaseModel):
    """Request to trigger metric recalculation"""

    period_start: Optional[datetime] = Field(None, description="Start of recalculation period")
    period_end: Optional[datetime] = Field(None, description="End of recalculation period")
    force: bool = Field(default=False, description="Force recalculation even if values exist")

    class Config:
        json_schema_extra = {
            "example": {
                "period_start": "2025-01-01T00:00:00Z",
                "period_end": "2025-01-15T23:59:59Z",
                "force": False
            }
        }


class RecalculateResponse(BaseModel):
    """Response from recalculation request"""

    quality_metric_id: UUID
    periods_calculated: int
    values_created: int
    values_updated: int
    started_at: datetime
    completed_at: datetime
    errors: Optional[List[str]] = None


# ==================== QI Project Schemas ====================

class QIProjectCreate(BaseModel):
    """Schema for creating a QI project"""

    tenant_id: UUID
    title: str = Field(..., description="Project title")
    description: Optional[str] = None
    category: str = Field(..., description="safety, effectiveness, patient_experience, efficiency, equity, timeliness")
    status: str = Field(default="planning", description="planning, active, on_hold, completed, cancelled")
    owner_id: Optional[UUID] = Field(None, description="User ID of project owner")
    team_members: Optional[List[UUID]] = Field(default_factory=list, description="List of team member user IDs")
    target_start_date: Optional[datetime] = None
    target_end_date: Optional[datetime] = None
    baseline_start: Optional[datetime] = None
    baseline_end: Optional[datetime] = None
    intervention_description: Optional[str] = None
    success_criteria: Optional[str] = None

    @validator("category")
    def validate_category(cls, v):
        valid_categories = ["safety", "effectiveness", "patient_experience", "efficiency", "equity", "timeliness"]
        if v.lower() not in valid_categories:
            raise ValueError(f"category must be one of: {', '.join(valid_categories)}")
        return v.lower()

    @validator("status")
    def validate_status(cls, v):
        valid_statuses = ["planning", "active", "on_hold", "completed", "cancelled"]
        if v.lower() not in valid_statuses:
            raise ValueError(f"status must be one of: {', '.join(valid_statuses)}")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "title": "Reduce Cardiology 30-Day Readmissions",
                "description": "PDSA cycle to reduce readmissions through enhanced discharge planning and 48hr follow-up calls",
                "category": "effectiveness",
                "status": "planning",
                "owner_id": "user-uuid-doctor-sharma",
                "team_members": ["user-uuid-nurse-patel", "user-uuid-pharmacist-kumar"],
                "target_start_date": "2025-02-01T00:00:00Z",
                "target_end_date": "2025-05-31T23:59:59Z",
                "baseline_start": "2024-11-01T00:00:00Z",
                "baseline_end": "2025-01-31T23:59:59Z",
                "intervention_description": "1. Enhanced discharge checklist, 2. Automated 48hr follow-up calls, 3. Medication reconciliation",
                "success_criteria": "Reduce readmission rate from 18% to below 12%"
            }
        }


class QIProjectUpdate(BaseModel):
    """Schema for updating a QI project"""

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    owner_id: Optional[UUID] = None
    team_members: Optional[List[UUID]] = None
    target_start_date: Optional[datetime] = None
    target_end_date: Optional[datetime] = None
    baseline_start: Optional[datetime] = None
    baseline_end: Optional[datetime] = None
    intervention_description: Optional[str] = None
    success_criteria: Optional[str] = None
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    results_summary: Optional[str] = None

    @validator("status")
    def validate_status(cls, v):
        if v:
            valid_statuses = ["planning", "active", "on_hold", "completed", "cancelled"]
            if v.lower() not in valid_statuses:
                raise ValueError(f"status must be one of: {', '.join(valid_statuses)}")
            return v.lower()
        return v


class QIProjectResponse(BaseModel):
    """Response schema for QI project"""

    id: UUID
    tenant_id: UUID
    title: str
    description: Optional[str] = None
    category: str
    status: str
    owner_id: Optional[UUID] = None
    team_members: List[UUID]
    target_start_date: Optional[datetime] = None
    target_end_date: Optional[datetime] = None
    baseline_start: Optional[datetime] = None
    baseline_end: Optional[datetime] = None
    intervention_description: Optional[str] = None
    success_criteria: Optional[str] = None
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    results_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QIProjectListResponse(BaseModel):
    """Response for list of QI projects"""

    total: int
    projects: List[QIProjectResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== QI Project Metric Schemas ====================

class QIProjectMetricCreate(BaseModel):
    """Schema for linking a metric to a QI project"""

    quality_metric_id: UUID
    is_primary: bool = Field(default=False, description="Is this the primary outcome metric?")
    baseline_value: Optional[float] = None
    target_value: Optional[float] = None
    notes: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "quality_metric_id": "metric-uuid-readmit-30d",
                "is_primary": True,
                "baseline_value": 18.0,
                "target_value": 12.0,
                "notes": "Primary outcome metric - calculated from historical baseline period"
            }
        }


class QIProjectMetricResponse(BaseModel):
    """Response schema for QI project metric"""

    id: UUID
    qi_project_id: UUID
    quality_metric_id: UUID
    is_primary: bool
    baseline_value: Optional[float] = None
    target_value: Optional[float] = None
    current_value: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime

    # Include full metric details in response
    metric: Optional[QualityMetricResponse] = None

    class Config:
        from_attributes = True


class QIProjectMetricListResponse(BaseModel):
    """Response for list of QI project metrics"""

    total: int
    project_metrics: List[QIProjectMetricResponse]
    project: QIProjectResponse
    page: int
    page_size: int
    has_next: bool
    has_previous: bool
