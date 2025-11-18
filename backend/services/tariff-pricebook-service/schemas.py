"""Tariff Pricebook Service Schemas"""
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel
from decimal import Decimal


# Service Item Schemas
class ServiceItemResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    code: str
    name: str
    category: str
    description: Optional[str]
    clinical_code: Optional[str]
    unit: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Tariff Group Schemas
class TariffGroupResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    code: str
    name: str
    payer_plan_id: Optional[UUID]
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Tariff Rate Schemas
class TariffRateResponse(BaseModel):
    id: UUID
    tariff_group_id: UUID
    service_item_id: UUID
    base_rate: Decimal
    currency: str
    effective_from: Optional[date]
    effective_to: Optional[date]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Package Definition Schemas
class PackageDefinitionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    code: str
    name: str
    procedure_catalog_id: Optional[UUID]
    payer_plan_id: Optional[UUID]
    tariff_group_id: Optional[UUID]
    package_rate: Decimal
    currency: str
    length_of_stay_days: Optional[int]
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Package Inclusion Schemas
class PackageInclusionResponse(BaseModel):
    id: UUID
    package_definition_id: UUID
    inclusion_type: str
    service_item_id: Optional[UUID]
    rule_payload: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True
