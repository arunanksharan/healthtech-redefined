"""Payer Master Service Schemas"""
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


# Payer Schemas
class PayerResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    code: str
    name: str
    type: str
    contact_details: Optional[dict]
    portal_url: Optional[str]
    api_endpoint_config: Optional[dict]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Payer Plan Schemas
class PayerPlanResponse(BaseModel):
    id: UUID
    payer_id: UUID
    code: str
    name: str
    coverage_type: Optional[str]
    product_type: Optional[str]
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Network Contract Schemas
class PayerNetworkContractResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    payer_plan_id: UUID
    hospital_location_id: Optional[UUID]
    network_type: str
    effective_from: Optional[date]
    effective_to: Optional[date]
    discount_model: Optional[str]
    discount_details: Optional[dict]
    cashless_allowed: bool
    preauth_required: bool
    remarks: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Payer Rule Schemas
class PayerRuleResponse(BaseModel):
    id: UUID
    payer_plan_id: UUID
    rule_type: str
    rule_name: str
    rule_payload: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
