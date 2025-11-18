"""De-identification Service Schemas"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

# Config Schemas
class DeidConfigCreate(BaseModel):
    tenant_id: UUID
    code: str = Field(..., description="SAFE_HARBOR, LIMITED_DATASET")
    name: str
    description: Optional[str] = None
    mode: str = Field(..., description="deidentification, pseudonymization, both")
    rules: Dict[str, Any] = Field(..., description="De-id rules DSL")

class DeidConfigResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    code: str
    name: str
    mode: str
    rules: Dict[str, Any]
    created_at: datetime
    class Config:
        from_attributes = True

# Pseudo ID Space Schemas
class PseudoIdSpaceCreate(BaseModel):
    tenant_id: UUID
    code: str
    name: str
    scope: str = Field(..., description="patient, practitioner, org")

class PseudoIdSpaceResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    code: str
    name: str
    scope: str
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

# Job Schemas
class DeidJobCreate(BaseModel):
    deid_config_code: str
    pseudo_id_space_code: Optional[str] = None
    job_type: str = Field(..., description="snapshot, incremental, export")
    filters: Optional[Dict[str, Any]] = None

class DeidJobResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    deid_config_id: UUID
    job_type: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    class Config:
        from_attributes = True

class DeidJobOutputResponse(BaseModel):
    id: UUID
    deid_job_id: UUID
    output_type: str
    location: str
    row_count: Optional[int] = None
    created_at: datetime
    class Config:
        from_attributes = True
