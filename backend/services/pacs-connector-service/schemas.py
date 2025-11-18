"""PACS Connector Service Schemas"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

# PACS Endpoint Schemas
class PACSEndpointCreate(BaseModel):
    tenant_id: UUID
    code: str = Field(..., description="MAIN_PACS, CLOUD_PACS")
    name: str
    description: Optional[str] = None
    ae_title: Optional[str] = Field(None, description="DICOM AE title")
    host: Optional[str] = None
    port: Optional[int] = None
    protocol: str = Field(..., description="DICOM, DICOMWeb, WADO_RS")
    auth_config: Optional[Dict[str, Any]] = None
    viewer_launch_url: Optional[str] = None

class PACSEndpointResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    code: str
    name: str
    protocol: str
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

# Imaging Study Schemas
class ImagingStudyCreate(BaseModel):
    imaging_order_id: Optional[UUID] = None
    patient_id: UUID
    pacs_endpoint_id: UUID
    study_instance_uid: str
    accession_number: Optional[str] = None
    modality_code: str = Field(..., description="CT, MR, US, etc.")
    description: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    number_of_series: Optional[int] = None
    number_of_instances: Optional[int] = None

class ImagingStudyUpdate(BaseModel):
    status: Optional[str] = None
    number_of_series: Optional[int] = None
    number_of_instances: Optional[int] = None
    ended_at: Optional[datetime] = None
    viewer_url: Optional[str] = None

class ImagingStudyResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    imaging_order_id: Optional[UUID]
    patient_id: UUID
    pacs_endpoint_id: UUID
    study_instance_uid: str
    accession_number: Optional[str]
    modality_code: str
    description: Optional[str]
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    number_of_series: Optional[int]
    number_of_instances: Optional[int]
    viewer_url: Optional[str]
    status: str
    created_at: datetime
    class Config:
        from_attributes = True

# Imaging Series Schemas
class ImagingSeriesCreate(BaseModel):
    imaging_study_id: UUID
    series_instance_uid: str
    series_number: Optional[int] = None
    body_part: Optional[str] = None
    modality_code: Optional[str] = None
    number_of_instances: Optional[int] = None
    description: Optional[str] = None

class ImagingSeriesResponse(BaseModel):
    id: UUID
    imaging_study_id: UUID
    series_instance_uid: str
    series_number: Optional[int]
    body_part: Optional[str]
    modality_code: Optional[str]
    number_of_instances: Optional[int]
    description: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

# Imaging Instance Schemas
class ImagingInstanceCreate(BaseModel):
    imaging_series_id: UUID
    sop_instance_uid: str
    instance_number: Optional[int] = None

class ImagingInstanceResponse(BaseModel):
    id: UUID
    imaging_series_id: UUID
    sop_instance_uid: str
    instance_number: Optional[int]
    created_at: datetime
    class Config:
        from_attributes = True

# Study Sync Schema (for PACS webhooks)
class StudySyncRequest(BaseModel):
    pacs_endpoint_code: str
    study_instance_uid: str
    patient_id: UUID
    modality_code: str
    accession_number: Optional[str] = None
    description: Optional[str] = None
    started_at: Optional[datetime] = None
    series: Optional[List[Dict[str, Any]]] = Field(None, description="Series metadata")
