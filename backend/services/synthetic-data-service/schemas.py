"""Synthetic Data Service Schemas"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

# Synthetic Data Profile Schemas
class SyntheticDataProfileCreate(BaseModel):
    tenant_id: UUID
    code: str = Field(..., description="HF_SANDBOX, ICU_SIM_2025, RESEARCH_COHORT_A")
    name: str
    description: Optional[str] = None
    base_population_criteria: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional criteria to base synthetic data on real population patterns"
    )
    generation_config: Dict[str, Any] = Field(
        ...,
        description="Configuration for synthetic data generation algorithm"
    )
    privacy_level: str = Field(
        default='high',
        description="high, medium - controls how much synthetic data diverges from real"
    )

class SyntheticDataProfileUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    generation_config: Optional[Dict[str, Any]] = None
    privacy_level: Optional[str] = None

class SyntheticDataProfileResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    code: str
    name: str
    description: Optional[str]
    base_population_criteria: Optional[Dict[str, Any]]
    generation_config: Dict[str, Any]
    privacy_level: str
    created_at: datetime
    updated_at: Optional[datetime]
    class Config:
        from_attributes = True

# Synthetic Data Job Schemas
class SyntheticDataJobCreate(BaseModel):
    synthetic_profile_id: UUID
    target_record_count: int = Field(..., description="Number of synthetic records to generate")
    output_format: str = Field(default='fhir_bundle', description="fhir_bundle, csv, parquet")
    seed: Optional[int] = Field(None, description="Random seed for reproducibility")
    job_parameters: Optional[Dict[str, Any]] = None

class SyntheticDataJobResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    synthetic_profile_id: UUID
    target_record_count: int
    output_format: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

# Synthetic Data Output Schemas
class SyntheticDataOutputResponse(BaseModel):
    id: UUID
    synthetic_job_id: UUID
    output_type: str
    location: str
    record_count: Optional[int]
    file_size_bytes: Optional[int]
    checksum: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True
