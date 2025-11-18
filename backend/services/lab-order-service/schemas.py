"""Lab Order Service Schemas"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

# Lab Order Item Schemas
class LabOrderItemCreate(BaseModel):
    lab_test_id: UUID
    is_panel: bool = False
    requested_specimen_type_id: Optional[UUID] = None

class LabOrderItemResponse(BaseModel):
    id: UUID
    lab_order_id: UUID
    lab_test_id: UUID
    is_panel: bool
    status: str
    requested_specimen_type_id: Optional[UUID]
    created_at: datetime
    class Config:
        from_attributes = True

# Lab Order Schemas
class LabOrderCreate(BaseModel):
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    episode_id: Optional[UUID] = None
    ordering_practitioner_id: Optional[UUID] = None
    ordering_department_id: Optional[UUID] = None
    priority: str = Field(default='routine', description="routine, urgent, stat")
    clinical_indication: Optional[str] = None
    items: List[LabOrderItemCreate]

class LabOrderUpdate(BaseModel):
    status: Optional[str] = None
    collected_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class LabOrderResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    patient_id: UUID
    encounter_id: Optional[UUID]
    episode_id: Optional[UUID]
    ordering_practitioner_id: Optional[UUID]
    ordering_department_id: Optional[UUID]
    priority: str
    status: str
    clinical_indication: Optional[str]
    requested_at: datetime
    collected_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    class Config:
        from_attributes = True
