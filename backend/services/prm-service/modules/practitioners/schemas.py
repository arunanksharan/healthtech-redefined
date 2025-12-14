"""
Practitioner Schemas
Pydantic models for practitioner API
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class PractitionerResponse(BaseModel):
    """Practitioner response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    gender: Optional[str] = None
    qualification: Optional[str] = None
    speciality: Optional[str] = None
    sub_speciality: Optional[str] = None
    license_number: Optional[str] = None
    registration_number: Optional[str] = None
    phone_primary: Optional[str] = None
    email_primary: Optional[str] = None
    is_active: bool = True
    meta_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def name(self) -> str:
        """Full name of practitioner"""
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        return " ".join(parts)


class PractitionerSimpleResponse(BaseModel):
    """Simplified practitioner for dropdowns"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    speciality: Optional[str] = None
    is_active: bool = True


class PractitionerListResponse(BaseModel):
    """Paginated practitioner list response"""
    items: List[PractitionerResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool
