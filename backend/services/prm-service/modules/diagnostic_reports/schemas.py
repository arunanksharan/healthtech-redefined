"""
Diagnostic Report Schemas
Pydantic models for diagnostic report API
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class ReportCode(BaseModel):
    """Code for report type (LOINC)"""
    system: str = "http://loinc.org"
    code: str
    display: Optional[str] = None


class ReportCreate(BaseModel):
    """Schema for creating a diagnostic report"""
    tenant_id: UUID
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    performer_id: Optional[UUID] = None  # Lab/Radiologist
    status: str = Field("final", max_length=50)  # registered, partial, preliminary, final, amended
    category: str = Field("LAB", max_length=100)  # LAB, RAD, etc.
    code: ReportCode
    effective_datetime: Optional[datetime] = None
    issued: Optional[datetime] = None
    conclusion: Optional[str] = None
    result_ids: List[UUID] = Field(default_factory=list)  # Observation IDs
    presented_form_url: Optional[str] = None  # PDF/Image URL
    note: Optional[str] = None
    meta_data: Dict[str, Any] = Field(default_factory=dict)


class ReportResponse(BaseModel):
    """Diagnostic report response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    fhir_id: str
    tenant_id: UUID
    resource_type: str = "DiagnosticReport"
    patient_id: Optional[UUID] = None
    encounter_id: Optional[UUID] = None
    performer_id: Optional[UUID] = None
    status: str
    category: str
    code: ReportCode
    effective_datetime: Optional[datetime] = None
    issued: Optional[datetime] = None
    conclusion: Optional[str] = None
    result_ids: List[UUID] = Field(default_factory=list)
    presented_form_url: Optional[str] = None
    note: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ReportListResponse(BaseModel):
    """Paginated diagnostic report list response"""
    items: List[ReportResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool
