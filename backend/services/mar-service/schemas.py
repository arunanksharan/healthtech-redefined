"""MAR Service Schemas"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

class MedicationAdministrationCreate(BaseModel):
    medication_order_id: Optional[UUID] = None
    medication_product_id: Optional[UUID] = None
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    scheduled_time: Optional[datetime] = None
    dose_given_numeric: Optional[float] = None
    dose_given_unit: Optional[str] = None
    route_id: Optional[UUID] = None
    comments: Optional[str] = None

class MedicationAdministrationUpdate(BaseModel):
    administration_time: Optional[datetime] = None
    dose_given_numeric: Optional[float] = None
    dose_given_unit: Optional[str] = None
    status: Optional[str] = Field(None, description="scheduled, completed, skipped, refused, partial")
    reason_skipped: Optional[str] = None
    comments: Optional[str] = None

class MedicationAdministrationResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    medication_order_id: Optional[UUID]
    medication_product_id: Optional[UUID]
    patient_id: UUID
    encounter_id: Optional[UUID]
    scheduled_time: Optional[datetime]
    administration_time: Optional[datetime]
    administered_by_user_id: Optional[UUID]
    dose_given_numeric: Optional[float]
    dose_given_unit: Optional[str]
    route_id: Optional[UUID]
    status: str
    reason_skipped: Optional[str]
    comments: Optional[str]
    fhir_medication_administration_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
