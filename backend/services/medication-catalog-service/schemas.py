"""Medication Catalog Service Schemas"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

# Medication Molecule Schemas
class MedicationMoleculeCreate(BaseModel):
    tenant_id: Optional[UUID] = None
    global_code: Optional[str] = None
    name: str
    synonyms: Optional[List[str]] = None
    atc_code: Optional[str] = None
    drug_class: Optional[str] = None
    is_controlled_substance: bool = False
    is_high_alert: bool = False

class MedicationMoleculeResponse(BaseModel):
    id: UUID
    tenant_id: Optional[UUID]
    global_code: Optional[str]
    name: str
    synonyms: Optional[List[str]]
    atc_code: Optional[str]
    drug_class: Optional[str]
    is_controlled_substance: bool
    is_high_alert: bool
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# Medication Route Schemas
class MedicationRouteCreate(BaseModel):
    code: str = Field(..., description="PO, IV, IM, SC, TOP, SL")
    name: str
    description: Optional[str] = None

class MedicationRouteResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

# Medication Dose Form Schemas
class MedicationDoseFormCreate(BaseModel):
    code: str = Field(..., description="TAB, CAP, SUSP, INJ, SR_TAB")
    name: str
    description: Optional[str] = None

class MedicationDoseFormResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

# Medication Product Schemas
class MedicationProductCreate(BaseModel):
    tenant_id: Optional[UUID] = None
    molecule_id: UUID
    brand_name: Optional[str] = None
    strength: Optional[str] = None
    strength_numeric: Optional[float] = None
    strength_unit: Optional[str] = None
    dose_form_id: Optional[UUID] = None
    route_id: Optional[UUID] = None
    pack_size: Optional[int] = None
    pack_unit: Optional[str] = None
    is_generic: bool = False
    is_active: bool = True

class MedicationProductResponse(BaseModel):
    id: UUID
    tenant_id: Optional[UUID]
    molecule_id: UUID
    brand_name: Optional[str]
    strength: Optional[str]
    strength_numeric: Optional[float]
    strength_unit: Optional[str]
    dose_form_id: Optional[UUID]
    route_id: Optional[UUID]
    pack_size: Optional[int]
    pack_unit: Optional[str]
    is_generic: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class MedicationProductDetailResponse(MedicationProductResponse):
    """Extended product response with related entities"""
    molecule: Optional[MedicationMoleculeResponse] = None
    dose_form: Optional[MedicationDoseFormResponse] = None
    route: Optional[MedicationRouteResponse] = None
    class Config:
        from_attributes = True
