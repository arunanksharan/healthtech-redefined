"""Formulary Service Schemas"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

# Formulary Entry Schemas
class FormularyEntryCreate(BaseModel):
    tenant_id: UUID
    medication_product_id: UUID
    is_formulary: bool = True
    restriction_level: str = Field(default="none", description="none, restricted, non_formulary")
    default_route_id: Optional[UUID] = None
    default_frequency: Optional[str] = None
    notes: Optional[str] = None

class FormularyEntryResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    medication_product_id: UUID
    is_formulary: bool
    restriction_level: str
    default_route_id: Optional[UUID]
    default_frequency: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# Formulary Restriction Schemas
class FormularyRestrictionCreate(BaseModel):
    formulary_entry_id: UUID
    restriction_type: str = Field(..., description="specialist_only, indication_based")
    allowed_specialties: Optional[List[str]] = None
    indication_regex: Optional[str] = None
    approval_required: bool = False
    approval_role: Optional[str] = None

class FormularyRestrictionResponse(BaseModel):
    id: UUID
    formulary_entry_id: UUID
    restriction_type: str
    allowed_specialties: Optional[List[str]]
    indication_regex: Optional[str]
    approval_required: bool
    approval_role: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

# Formulary Substitution Rule Schemas
class FormularySubstitutionRuleCreate(BaseModel):
    tenant_id: UUID
    from_molecule_id: UUID
    to_molecule_id: UUID
    rule_type: str = Field(..., description="automatic_generic, therapeutic")
    conditions: Optional[Dict[str, Any]] = None

class FormularySubstitutionRuleResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    from_molecule_id: UUID
    to_molecule_id: UUID
    rule_type: str
    conditions: Optional[Dict[str, Any]]
    created_at: datetime
    class Config:
        from_attributes = True

# Alternative product search response
class FormularyAlternativeResponse(BaseModel):
    product_id: UUID
    brand_name: Optional[str]
    molecule_name: str
    strength: Optional[str]
    route_code: Optional[str]
    is_formulary: bool
    restriction_level: str
    substitution_rule_type: Optional[str] = None
