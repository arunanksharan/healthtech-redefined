"""Pharmacy Verification & Dispense Service Schemas"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

# Pharmacy Verification Queue Schemas
class PharmacyVerificationQueueResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    medication_order_id: UUID
    patient_id: UUID
    status: str
    pharmacist_id: Optional[UUID]
    review_notes: Optional[str]
    rejection_reason: Optional[str]
    clinical_checks: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class VerificationApprovalRequest(BaseModel):
    review_notes: Optional[str] = None
    clinical_checks: Optional[Dict[str, Any]] = None

class VerificationRejectionRequest(BaseModel):
    rejection_reason: str
    review_notes: Optional[str] = None

# Medication Dispensation Schemas
class MedicationDispensationCreate(BaseModel):
    medication_order_id: Optional[UUID] = None
    patient_id: UUID
    destination_location_id: Optional[UUID] = None
    comments: Optional[str] = None
    items: List[Dict[str, Any]] = Field(..., description="List of {medication_product_id, quantity_dispensed, quantity_unit, inventory_batch_id}")

class MedicationDispensationResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    medication_order_id: Optional[UUID]
    patient_id: UUID
    dispensed_by_user_id: Optional[UUID]
    dispensed_at: datetime
    destination_location_id: Optional[UUID]
    status: str
    comments: Optional[str]
    fhir_medication_dispense_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class MedicationDispensationItemResponse(BaseModel):
    id: UUID
    medication_dispensation_id: UUID
    medication_product_id: UUID
    quantity_dispensed: float
    quantity_unit: Optional[str]
    inventory_batch_id: Optional[UUID]
    created_at: datetime
    class Config:
        from_attributes = True

class MedicationDispensationDetailResponse(MedicationDispensationResponse):
    """Extended dispensation response with items"""
    items: List[MedicationDispensationItemResponse] = []
    class Config:
        from_attributes = True
