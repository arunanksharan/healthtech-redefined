"""Medication Order Service Schemas"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

class MedicationOrderCreate(BaseModel):
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    episode_id: Optional[UUID] = None
    prescriber_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    medication_product_id: Optional[UUID] = None
    molecule_id: Optional[UUID] = None
    order_type: str = Field(..., description="inpatient, outpatient, discharge")
    dose_amount_numeric: Optional[float] = None
    dose_amount_unit: Optional[str] = None
    dose_form_id: Optional[UUID] = None
    route_id: Optional[UUID] = None
    frequency: Optional[str] = None
    as_needed: bool = False
    as_needed_reason: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    indication: Optional[str] = None
    instructions_for_patient: Optional[str] = None
    instructions_for_pharmacist: Optional[str] = None
    is_prn: bool = False
    linked_discharge_order_id: Optional[UUID] = None

class MedicationOrderUpdate(BaseModel):
    status: Optional[str] = None
    end_datetime: Optional[datetime] = None
    instructions_for_pharmacist: Optional[str] = None

class MedicationOrderResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    patient_id: UUID
    encounter_id: Optional[UUID]
    episode_id: Optional[UUID]
    prescriber_id: Optional[UUID]
    department_id: Optional[UUID]
    medication_product_id: Optional[UUID]
    molecule_id: Optional[UUID]
    order_type: str
    status: str
    intent: str
    dose_amount_numeric: Optional[float]
    dose_amount_unit: Optional[str]
    dose_form_id: Optional[UUID]
    route_id: Optional[UUID]
    frequency: Optional[str]
    as_needed: bool
    as_needed_reason: Optional[str]
    start_datetime: Optional[datetime]
    end_datetime: Optional[datetime]
    indication: Optional[str]
    instructions_for_patient: Optional[str]
    instructions_for_pharmacist: Optional[str]
    is_prn: bool
    linked_discharge_order_id: Optional[UUID]
    fhir_medication_request_id: Optional[str]
    formulary_status: Optional[str]
    substitution_details: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
