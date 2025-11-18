"""
Orders Service Pydantic Schemas
Request/Response models for clinical orders
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator


# ==================== Order Schemas ====================

class OrderCreate(BaseModel):
    """Schema for creating a clinical order"""

    tenant_id: UUID
    admission_id: Optional[UUID] = None
    encounter_id: UUID
    patient_id: UUID
    ordering_practitioner_id: UUID
    order_type: str = Field(..., description="lab, imaging, procedure, medication")
    code: Optional[str] = Field(None, description="LOINC, SNOMED, or internal code")
    description: str = Field(..., min_length=1)
    priority: str = Field(default="routine", description="routine, urgent, stat")
    reason: Optional[str] = None

    @validator("order_type")
    def validate_order_type(cls, v):
        valid_types = ["lab", "imaging", "procedure", "medication"]
        if v.lower() not in valid_types:
            raise ValueError(f"order_type must be one of: {', '.join(valid_types)}")
        return v.lower()

    @validator("priority")
    def validate_priority(cls, v):
        valid_priorities = ["routine", "urgent", "stat", "asap"]
        if v.lower() not in valid_priorities:
            raise ValueError(f"priority must be one of: {', '.join(valid_priorities)}")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "admission_id": "admission-uuid",
                "encounter_id": "encounter-uuid",
                "patient_id": "patient-uuid",
                "ordering_practitioner_id": "doctor-uuid",
                "order_type": "lab",
                "code": "2345-7",
                "description": "Complete Blood Count (CBC)",
                "priority": "routine",
                "reason": "Routine check"
            }
        }


class OrderUpdate(BaseModel):
    """Schema for updating an order"""

    status: Optional[str] = Field(
        None,
        description="requested, in_progress, completed, cancelled, rejected"
    )
    priority: Optional[str] = None
    external_order_id: Optional[str] = Field(
        None,
        description="ID from external system (LIS, RIS, Pharmacy)"
    )
    notes: Optional[str] = None

    @validator("status")
    def validate_status(cls, v):
        if v:
            valid_statuses = ["requested", "in_progress", "completed", "cancelled", "rejected"]
            if v.lower() not in valid_statuses:
                raise ValueError(f"status must be one of: {', '.join(valid_statuses)}")
            return v.lower()
        return v


class OrderCancel(BaseModel):
    """Schema for cancelling an order"""

    cancel_reason: str = Field(..., min_length=1)
    cancelled_by_user_id: Optional[UUID] = None


class OrderResponse(BaseModel):
    """Response schema for order"""

    id: UUID
    tenant_id: UUID
    admission_id: Optional[UUID] = None
    encounter_id: UUID
    patient_id: UUID
    ordering_practitioner_id: UUID
    order_type: str
    code: Optional[str] = None
    description: str
    status: str
    priority: str
    reason: Optional[str] = None
    external_order_id: Optional[str] = None
    fhir_service_request_id: Optional[str] = None
    fhir_medication_request_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderWithDetails(BaseModel):
    """Order with patient and practitioner details"""

    id: UUID
    patient_id: UUID
    patient_name: str
    ordering_practitioner_id: UUID
    ordering_practitioner_name: str
    order_type: str
    code: Optional[str] = None
    description: str
    status: str
    priority: str
    reason: Optional[str] = None
    external_order_id: Optional[str] = None
    created_at: datetime


class OrderListResponse(BaseModel):
    """Response for list of orders"""

    total: int
    orders: List[OrderResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== Statistics Schemas ====================

class OrderStats(BaseModel):
    """Order statistics"""

    total_orders: int = 0
    pending_orders: int = 0
    completed_today: int = 0
    order_type_breakdown: Dict[str, int] = Field(default_factory=dict)
    priority_breakdown: Dict[str, int] = Field(default_factory=dict)
    status_breakdown: Dict[str, int] = Field(default_factory=dict)


# ==================== Medication Order Specific ====================

class MedicationOrderCreate(BaseModel):
    """Extended schema for medication orders"""

    tenant_id: UUID
    admission_id: Optional[UUID] = None
    encounter_id: UUID
    patient_id: UUID
    ordering_practitioner_id: UUID
    medication_name: str
    dose: str
    route: str = Field(..., description="oral, iv, im, sc, topical, etc.")
    frequency: str = Field(..., description="once, bid, tid, qid, prn, etc.")
    duration: Optional[str] = None
    priority: str = Field(default="routine")
    reason: Optional[str] = None

    @validator("route")
    def validate_route(cls, v):
        valid_routes = ["oral", "iv", "im", "sc", "topical", "inhalation", "rectal", "sublingual", "other"]
        if v.lower() not in valid_routes:
            raise ValueError(f"route must be one of: {', '.join(valid_routes)}")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "encounter_id": "encounter-uuid",
                "patient_id": "patient-uuid",
                "ordering_practitioner_id": "doctor-uuid",
                "medication_name": "Paracetamol",
                "dose": "500mg",
                "route": "oral",
                "frequency": "tid",
                "duration": "5 days",
                "priority": "routine",
                "reason": "Pain management"
            }
        }
