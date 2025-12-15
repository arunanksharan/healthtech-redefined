"""
Medication Schemas
Pydantic models for medication API
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class MedicationCode(BaseModel):
    """Code for medication (RxNorm, SNOMED)"""
    system: str = "http://www.nlm.nih.gov/research/umls/rxnorm"
    code: str
    display: Optional[str] = None


class Dosage(BaseModel):
    """Dosage instructions"""
    text: Optional[str] = None
    timing: Optional[str] = None  # QD, BID, TID, etc.
    route: Optional[str] = None  # oral, IV, etc.
    dose_value: Optional[float] = None
    dose_unit: Optional[str] = None


class MedicationCreate(BaseModel):
    """Schema for creating a medication request"""
    tenant_id: UUID
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    requester_id: Optional[UUID] = None  # Prescribing practitioner
    status: str = Field("active", max_length=50)  # active, on-hold, cancelled, completed, stopped
    intent: str = Field("order", max_length=50)  # proposal, plan, order, reflex-order
    medication: MedicationCode
    dosage: Optional[Dosage] = None
    quantity: Optional[int] = None
    days_supply: Optional[int] = None
    refills: Optional[int] = Field(None, ge=0)
    authored_on: Optional[datetime] = None
    note: Optional[str] = None
    meta_data: Dict[str, Any] = Field(default_factory=dict)


class MedicationResponse(BaseModel):
    """Medication response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    fhir_id: str
    tenant_id: UUID
    resource_type: str = "MedicationRequest"
    patient_id: Optional[UUID] = None
    encounter_id: Optional[UUID] = None
    requester_id: Optional[UUID] = None
    status: str
    intent: str
    medication: MedicationCode
    dosage: Optional[Dosage] = None
    quantity: Optional[int] = None
    days_supply: Optional[int] = None
    refills: Optional[int] = None
    authored_on: Optional[datetime] = None
    note: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MedicationListResponse(BaseModel):
    """Paginated medication list response"""
    items: List[MedicationResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool
