"""Pharmacy AI Orchestrator Service Schemas"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

class PharmacyAITaskCreate(BaseModel):
    patient_id: Optional[UUID] = None
    medication_order_id: Optional[UUID] = None
    task_type: str = Field(..., description="interaction_check, dose_suggestion, reconciliation_assist, inventory_forecast")

class PharmacyAITaskResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    patient_id: Optional[UUID]
    medication_order_id: Optional[UUID]
    task_type: str
    status: str
    requested_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

class PharmacyAIOutputCreate(BaseModel):
    pharmacy_ai_task_id: UUID
    output_type: str = Field(..., description="interaction_summary, dose_recommendation, reconciliation_proposal, forecast")
    payload: Dict[str, Any]

class PharmacyAIOutputResponse(BaseModel):
    id: UUID
    pharmacy_ai_task_id: UUID
    output_type: str
    payload: Dict[str, Any]
    created_at: datetime
    class Config:
        from_attributes = True
