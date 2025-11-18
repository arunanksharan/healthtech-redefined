"""
Bed Management Service Pydantic Schemas
Request/Response models for wards, beds, and bed assignments
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, validator


# ==================== Ward Schemas ====================

class WardCreate(BaseModel):
    """Schema for creating a ward"""

    tenant_id: UUID
    location_id: UUID
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    type: Optional[str] = Field(None, description="general, icu, hdu, pediatrics, maternity")
    floor: Optional[str] = None
    capacity: Optional[int] = Field(None, ge=0)

    @validator("type")
    def validate_type(cls, v):
        if v:
            valid_types = ["general", "icu", "hdu", "pediatrics", "maternity", "surgical", "medical"]
            if v.lower() not in valid_types:
                raise ValueError(f"type must be one of: {', '.join(valid_types)}")
            return v.lower()
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "location_id": "location-uuid",
                "code": "WARD-3A",
                "name": "Ward 3A - General Medicine",
                "type": "general",
                "floor": "3",
                "capacity": 30
            }
        }


class WardUpdate(BaseModel):
    """Schema for updating a ward"""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    type: Optional[str] = None
    floor: Optional[str] = None
    capacity: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class WardResponse(BaseModel):
    """Response schema for ward"""

    id: UUID
    tenant_id: UUID
    location_id: UUID
    code: str
    name: str
    type: Optional[str] = None
    floor: Optional[str] = None
    capacity: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WardWithStats(BaseModel):
    """Ward with occupancy statistics"""

    id: UUID
    tenant_id: UUID
    code: str
    name: str
    type: Optional[str] = None
    floor: Optional[str] = None
    capacity: Optional[int] = None
    is_active: bool
    total_beds: int = 0
    occupied_beds: int = 0
    available_beds: int = 0
    cleaning_beds: int = 0
    occupancy_rate: float = 0.0


class WardListResponse(BaseModel):
    """Response for list of wards"""

    total: int
    wards: List[WardResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== Bed Schemas ====================

class BedCreate(BaseModel):
    """Schema for creating a bed"""

    tenant_id: UUID
    ward_id: UUID
    code: str = Field(..., min_length=1, max_length=50)
    type: Optional[str] = Field(None, description="standard, icu, isolation, ventilator")

    @validator("type")
    def validate_type(cls, v):
        if v:
            valid_types = ["standard", "icu", "isolation", "ventilator", "hdu", "private"]
            if v.lower() not in valid_types:
                raise ValueError(f"type must be one of: {', '.join(valid_types)}")
            return v.lower()
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "ward_id": "ward-uuid",
                "code": "3A-12",
                "type": "standard"
            }
        }


class BedUpdate(BaseModel):
    """Schema for updating a bed"""

    type: Optional[str] = None
    status: Optional[str] = Field(None, description="available, occupied, cleaning, maintenance, blocked")

    @validator("status")
    def validate_status(cls, v):
        if v:
            valid_statuses = ["available", "occupied", "cleaning", "maintenance", "blocked"]
            if v.lower() not in valid_statuses:
                raise ValueError(f"status must be one of: {', '.join(valid_statuses)}")
            return v.lower()
        return v


class BedResponse(BaseModel):
    """Response schema for bed"""

    id: UUID
    tenant_id: UUID
    ward_id: UUID
    code: str
    type: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BedWithDetails(BaseModel):
    """Bed with current patient and assignment details"""

    id: UUID
    tenant_id: UUID
    ward_id: UUID
    ward_code: str
    ward_name: str
    code: str
    type: Optional[str] = None
    status: str
    current_patient_id: Optional[UUID] = None
    current_patient_name: Optional[str] = None
    current_assignment_id: Optional[UUID] = None
    assigned_since: Optional[datetime] = None


class BedListResponse(BaseModel):
    """Response for list of beds"""

    total: int
    beds: List[BedResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== Bed Assignment Schemas ====================

class BedAssignmentCreate(BaseModel):
    """Schema for creating a bed assignment"""

    tenant_id: UUID
    bed_id: UUID
    patient_id: UUID
    encounter_id: UUID
    admission_id: Optional[UUID] = None
    start_time: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "bed_id": "bed-uuid",
                "patient_id": "patient-uuid",
                "encounter_id": "encounter-uuid",
                "admission_id": "admission-uuid"
            }
        }


class BedAssignmentEnd(BaseModel):
    """Schema for ending a bed assignment"""

    end_time: Optional[datetime] = None
    status: str = Field(default="discharged", description="transferred, discharged, cancelled")
    reason: Optional[str] = None

    @validator("status")
    def validate_status(cls, v):
        valid_statuses = ["transferred", "discharged", "cancelled"]
        if v.lower() not in valid_statuses:
            raise ValueError(f"status must be one of: {', '.join(valid_statuses)}")
        return v.lower()


class BedTransferRequest(BaseModel):
    """Schema for transferring patient between beds"""

    admission_id: UUID
    from_bed_id: UUID
    to_bed_id: UUID
    reason: Optional[str] = None
    transfer_time: Optional[datetime] = None


class BedAssignmentResponse(BaseModel):
    """Response schema for bed assignment"""

    id: UUID
    tenant_id: UUID
    bed_id: UUID
    patient_id: UUID
    encounter_id: UUID
    admission_id: Optional[UUID] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BedAssignmentWithDetails(BaseModel):
    """Bed assignment with patient and bed details"""

    id: UUID
    bed_code: str
    ward_code: str
    ward_name: str
    patient_id: UUID
    patient_name: str
    encounter_id: UUID
    admission_id: Optional[UUID] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str
    duration_days: Optional[int] = None


class BedAssignmentListResponse(BaseModel):
    """Response for list of bed assignments"""

    total: int
    assignments: List[BedAssignmentResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== Bulk Operations ====================

class BulkBedCreate(BaseModel):
    """Schema for creating multiple beds at once"""

    tenant_id: UUID
    ward_id: UUID
    bed_prefix: str = Field(..., description="Prefix for bed codes, e.g., '3A-'")
    start_number: int = Field(..., ge=1)
    count: int = Field(..., ge=1, le=100)
    bed_type: Optional[str] = Field(None, description="Type for all beds")

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "ward_id": "ward-uuid",
                "bed_prefix": "3A-",
                "start_number": 1,
                "count": 30,
                "bed_type": "standard"
            }
        }


class BulkBedCreateResponse(BaseModel):
    """Response for bulk bed creation"""

    created_count: int
    bed_ids: List[UUID]
    bed_codes: List[str]
