"""Medication Reconciliation Service Schemas"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

# Medication History Source Schemas
class MedicationHistorySourceCreate(BaseModel):
    patient_id: UUID
    source_type: str = Field(..., description="patient, caregiver, external_record, pharmacy")
    description: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

class MedicationHistorySourceResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    patient_id: UUID
    source_type: str
    description: Optional[str]
    recorded_by_user_id: Optional[UUID]
    recorded_at: datetime
    raw_data: Optional[Dict[str, Any]]
    created_at: datetime
    class Config:
        from_attributes = True

# Medication Reconciliation Session Schemas
class MedicationReconciliationSessionCreate(BaseModel):
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    reconciliation_type: str = Field(..., description="admission, transfer, discharge")
    comments: Optional[str] = None

class MedicationReconciliationSessionUpdate(BaseModel):
    status: Optional[str] = Field(None, description="in_progress, completed")
    comments: Optional[str] = None

class MedicationReconciliationSessionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    patient_id: UUID
    encounter_id: Optional[UUID]
    reconciliation_type: str
    status: str
    performed_by_user_id: Optional[UUID]
    performed_at: Optional[datetime]
    comments: Optional[str]
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# Medication Reconciliation Line Schemas
class MedicationReconciliationLineCreate(BaseModel):
    reconciliation_session_id: UUID
    source_medication_statement_id: Optional[str] = None
    medication_product_id: Optional[UUID] = None
    molecule_id: Optional[UUID] = None
    home_regimen: Optional[str] = None
    decision: str = Field(..., description="continue, modify, stop, new")
    decision_reason: Optional[str] = None
    linked_medication_order_id: Optional[UUID] = None
    comments: Optional[str] = None

class MedicationReconciliationLineUpdate(BaseModel):
    decision: Optional[str] = None
    decision_reason: Optional[str] = None
    linked_medication_order_id: Optional[UUID] = None
    comments: Optional[str] = None

class MedicationReconciliationLineResponse(BaseModel):
    id: UUID
    reconciliation_session_id: UUID
    source_medication_statement_id: Optional[str]
    medication_product_id: Optional[UUID]
    molecule_id: Optional[UUID]
    home_regimen: Optional[str]
    decision: str
    decision_reason: Optional[str]
    linked_medication_order_id: Optional[UUID]
    comments: Optional[str]
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
