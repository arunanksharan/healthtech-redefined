"""Coverage Policy Service Schemas"""
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel
from decimal import Decimal


# Coverage Schemas
class CoverageCreate(BaseModel):
    patient_id: UUID
    payer_plan_id: UUID
    policy_number: str
    insured_person_name: Optional[str] = None
    relationship_to_insured: Optional[str] = None
    sum_insured: Optional[Decimal] = None
    remaining_eligible_amount: Optional[Decimal] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    network_contract_id: Optional[UUID] = None
    is_primary: bool = True
    verification_details: Optional[dict] = None


class CoverageUpdate(BaseModel):
    verification_status: Optional[str] = None
    verification_details: Optional[dict] = None
    network_contract_id: Optional[UUID] = None
    remaining_eligible_amount: Optional[Decimal] = None
    is_primary: Optional[bool] = None


class CoverageResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    patient_id: UUID
    payer_plan_id: UUID
    policy_number: str
    insured_person_name: Optional[str]
    relationship_to_insured: Optional[str]
    sum_insured: Optional[Decimal]
    remaining_eligible_amount: Optional[Decimal]
    valid_from: Optional[date]
    valid_to: Optional[date]
    network_contract_id: Optional[UUID]
    is_primary: bool
    verification_status: str
    verification_details: Optional[dict]
    fhir_coverage_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Coverage Benefit Limit Schemas
class CoverageBenefitLimitResponse(BaseModel):
    id: UUID
    coverage_id: UUID
    benefit_type: str
    benefit_code: Optional[str]
    limit_type: str
    limit_amount: Optional[Decimal]
    currency: str
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
