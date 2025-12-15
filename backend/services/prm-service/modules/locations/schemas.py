"""
Location Schemas
Pydantic models for location API
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class LocationCreate(BaseModel):
    """Schema for creating a location"""
    tenant_id: UUID
    organization_id: Optional[UUID] = None
    parent_location_id: Optional[UUID] = None
    name: str = Field(..., min_length=1, max_length=255)
    type: Optional[str] = Field(None, max_length=100)  # ward, room, bed, clinic, department
    code: Optional[str] = Field(None, max_length=50)
    building: Optional[str] = Field(None, max_length=100)
    floor: Optional[str] = Field(None, max_length=50)
    room: Optional[str] = Field(None, max_length=50)
    is_active: bool = True
    operational_status: Optional[str] = Field(None, max_length=50)  # active, suspended, inactive
    meta_data: Dict[str, Any] = Field(default_factory=dict)


class LocationUpdate(BaseModel):
    """Schema for updating a location"""
    organization_id: Optional[UUID] = None
    parent_location_id: Optional[UUID] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[str] = Field(None, max_length=100)
    code: Optional[str] = Field(None, max_length=50)
    building: Optional[str] = Field(None, max_length=100)
    floor: Optional[str] = Field(None, max_length=50)
    room: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    operational_status: Optional[str] = Field(None, max_length=50)
    meta_data: Optional[Dict[str, Any]] = None


class LocationResponse(BaseModel):
    """Location response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    organization_id: Optional[UUID] = None
    parent_location_id: Optional[UUID] = None
    name: str
    type: Optional[str] = None
    code: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[str] = None
    room: Optional[str] = None
    is_active: bool = True
    operational_status: Optional[str] = None
    meta_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class LocationListResponse(BaseModel):
    """Paginated location list response"""
    items: List[LocationResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool
