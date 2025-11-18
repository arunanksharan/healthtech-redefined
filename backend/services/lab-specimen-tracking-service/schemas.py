"""Lab Specimen Tracking Service Schemas"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

# Lab Specimen Event Schemas
class LabSpecimenEventCreate(BaseModel):
    event_type: str = Field(..., description="label_printed, collected, sent_to_lab, received, aliquoted, stored, discarded")
    event_time: datetime
    location_id: Optional[UUID] = None
    performed_by_user_id: Optional[UUID] = None
    details: Optional[Dict[str, Any]] = None

class LabSpecimenEventResponse(BaseModel):
    id: UUID
    lab_specimen_id: UUID
    event_type: str
    event_time: datetime
    location_id: Optional[UUID]
    performed_by_user_id: Optional[UUID]
    details: Optional[Dict[str, Any]]
    created_at: datetime
    class Config:
        from_attributes = True

# Lab Specimen Schemas
class LabSpecimenCreate(BaseModel):
    lab_order_id: UUID
    specimen_type_id: UUID
    patient_id: UUID
    collection_time: Optional[datetime] = None
    collection_location_id: Optional[UUID] = None
    collected_by_user_id: Optional[UUID] = None
    volume_ml: Optional[float] = None
    comments: Optional[str] = None

class LabSpecimenLabelRequest(BaseModel):
    lab_order_id: UUID
    specimen_type_id: UUID
    count: int = Field(default=1, description="Number of specimens to label")

class LabSpecimenUpdate(BaseModel):
    status: Optional[str] = None
    collection_time: Optional[datetime] = None
    received_time: Optional[datetime] = None
    volume_ml: Optional[float] = None
    comments: Optional[str] = None

class LabSpecimenResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    lab_order_id: UUID
    specimen_identifier: str
    specimen_type_id: UUID
    patient_id: UUID
    collection_time: Optional[datetime]
    collection_location_id: Optional[UUID]
    collected_by_user_id: Optional[UUID]
    status: str
    received_time: Optional[datetime]
    received_location_id: Optional[UUID]
    volume_ml: Optional[float]
    comments: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True
