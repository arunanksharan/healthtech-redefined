"""
Pydantic schemas for Identity Service
Request/response models with validation
"""
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator


# ============================================================================
# BASE SCHEMAS
# ============================================================================

class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
    }


# ============================================================================
# ADDRESS & IDENTIFIER SCHEMAS
# ============================================================================

class AddressInput(BaseModel):
    """Address information"""
    line1: Optional[str] = None
    line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "India"


class IdentifierInput(BaseModel):
    """Patient/Practitioner identifier"""
    system: str = Field(..., description="Identifier system (MRN, ABHA, NATIONAL_ID, etc.)")
    value: str = Field(..., description="Identifier value")
    is_primary: bool = Field(default=False, description="Whether this is the primary identifier")

    @validator('system')
    def validate_system(cls, v):
        allowed_systems = ['MRN', 'ABHA', 'NATIONAL_ID', 'PASSPORT', 'DRIVER_LICENSE', 'AADHAR']
        if v.upper() not in allowed_systems:
            raise ValueError(f"System must be one of {allowed_systems}")
        return v.upper()


class IdentifierResponse(BaseSchema):
    """Identifier response"""
    system: str
    value: str
    is_primary: bool


# ============================================================================
# PATIENT SCHEMAS
# ============================================================================

class PatientCreate(BaseModel):
    """Schema for creating a patient"""
    tenant_id: UUID
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: date
    gender: str = Field(..., description="male, female, other, unknown")

    # Contact
    phone_primary: Optional[str] = Field(None, max_length=20)
    phone_secondary: Optional[str] = Field(None, max_length=20)
    email_primary: Optional[EmailStr] = None
    email_secondary: Optional[EmailStr] = None

    # Additional demographics
    marital_status: Optional[str] = Field(None, max_length=20)
    blood_group: Optional[str] = Field(None, max_length=10)
    language_preferred: Optional[str] = Field(None, max_length=50)

    # Address
    address: Optional[AddressInput] = None

    # Identifiers
    identifiers: Optional[List[IdentifierInput]] = None

    @validator('gender')
    def validate_gender(cls, v):
        allowed = ['male', 'female', 'other', 'unknown']
        if v.lower() not in allowed:
            raise ValueError(f"Gender must be one of {allowed}")
        return v.lower()

    @validator('blood_group')
    def validate_blood_group(cls, v):
        if v is None:
            return v
        allowed = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        if v.upper() not in allowed:
            raise ValueError(f"Blood group must be one of {allowed}")
        return v.upper()


class PatientUpdate(BaseModel):
    """Schema for updating a patient"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)

    phone_primary: Optional[str] = Field(None, max_length=20)
    phone_secondary: Optional[str] = Field(None, max_length=20)
    email_primary: Optional[EmailStr] = None
    email_secondary: Optional[EmailStr] = None

    marital_status: Optional[str] = Field(None, max_length=20)
    blood_group: Optional[str] = Field(None, max_length=10)
    language_preferred: Optional[str] = Field(None, max_length=50)

    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None


class PatientResponse(BaseSchema):
    """Schema for patient response"""
    id: UUID
    tenant_id: UUID

    first_name: Optional[str]
    last_name: Optional[str]
    middle_name: Optional[str]
    date_of_birth: Optional[date]
    gender: Optional[str]

    phone_primary: Optional[str]
    phone_secondary: Optional[str]
    email_primary: Optional[str]
    email_secondary: Optional[str]

    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    postal_code: Optional[str]
    country: Optional[str]

    marital_status: Optional[str]
    blood_group: Optional[str]
    language_preferred: Optional[str]

    is_deceased: bool
    deceased_date: Optional[datetime]

    created_at: datetime
    updated_at: datetime

    # Relationships
    identifiers: List[IdentifierResponse] = []


class PatientSearchResponse(BaseModel):
    """Paginated patient search response"""
    total: int = Field(..., description="Total number of results")
    offset: int = Field(..., description="Current offset")
    limit: int = Field(..., description="Results per page")
    patients: List[PatientResponse]


class MergeRequest(BaseModel):
    """Request to merge patient records"""
    target_patient_id: UUID = Field(..., description="Patient to merge into")
    source_patient_ids: List[UUID] = Field(..., description="Patients to merge from")
    reason: str = Field(..., description="Reason for merge")


# ============================================================================
# PRACTITIONER SCHEMAS
# ============================================================================

class PractitionerCreate(BaseModel):
    """Schema for creating a practitioner"""
    tenant_id: UUID
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    gender: Optional[str] = Field(None, max_length=20)

    # Professional info
    qualification: Optional[str] = Field(None, max_length=255)
    speciality: Optional[str] = Field(None, max_length=100)
    sub_speciality: Optional[str] = Field(None, max_length=100)
    license_number: Optional[str] = Field(None, max_length=100)
    registration_number: Optional[str] = Field(None, max_length=100)

    # Contact
    phone_primary: Optional[str] = Field(None, max_length=20)
    email_primary: Optional[EmailStr] = None


class PractitionerUpdate(BaseModel):
    """Schema for updating a practitioner"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)

    qualification: Optional[str] = Field(None, max_length=255)
    speciality: Optional[str] = Field(None, max_length=100)
    sub_speciality: Optional[str] = Field(None, max_length=100)

    phone_primary: Optional[str] = Field(None, max_length=20)
    email_primary: Optional[EmailStr] = None

    is_active: Optional[bool] = None


class PractitionerResponse(BaseSchema):
    """Schema for practitioner response"""
    id: UUID
    tenant_id: UUID

    first_name: str
    last_name: str
    middle_name: Optional[str]
    gender: Optional[str]

    qualification: Optional[str]
    speciality: Optional[str]
    sub_speciality: Optional[str]
    license_number: Optional[str]
    registration_number: Optional[str]

    phone_primary: Optional[str]
    email_primary: Optional[str]

    is_active: bool

    created_at: datetime
    updated_at: datetime


# ============================================================================
# ORGANIZATION SCHEMAS
# ============================================================================

class OrganizationCreate(BaseModel):
    """Schema for creating an organization"""
    tenant_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    type: Optional[str] = Field(None, max_length=100, description="hospital, clinic, lab, pharmacy")

    # Contact
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    website: Optional[str] = Field(None, max_length=255)

    # Address
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = "India"

    @validator('type')
    def validate_type(cls, v):
        if v is None:
            return v
        allowed = ['hospital', 'clinic', 'lab', 'pharmacy', 'imaging']
        if v.lower() not in allowed:
            raise ValueError(f"Type must be one of {allowed}")
        return v.lower()


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[str] = None

    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None

    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

    is_active: Optional[bool] = None


class OrganizationResponse(BaseSchema):
    """Schema for organization response"""
    id: UUID
    tenant_id: UUID

    name: str
    type: Optional[str]

    phone: Optional[str]
    email: Optional[str]
    website: Optional[str]

    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    postal_code: Optional[str]
    country: Optional[str]

    is_active: bool

    created_at: datetime
    updated_at: datetime


# ============================================================================
# LOCATION SCHEMAS
# ============================================================================

class LocationCreate(BaseModel):
    """Schema for creating a location"""
    tenant_id: UUID
    organization_id: Optional[UUID] = None
    parent_location_id: Optional[UUID] = None

    name: str = Field(..., min_length=1, max_length=255)
    type: Optional[str] = Field(None, max_length=100, description="ward, room, bed, clinic, department")
    code: Optional[str] = Field(None, max_length=50)

    building: Optional[str] = Field(None, max_length=100)
    floor: Optional[str] = Field(None, max_length=50)
    room: Optional[str] = Field(None, max_length=50)


class LocationUpdate(BaseModel):
    """Schema for updating a location"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[str] = None
    code: Optional[str] = None

    building: Optional[str] = None
    floor: Optional[str] = None
    room: Optional[str] = None

    operational_status: Optional[str] = None
    is_active: Optional[bool] = None


class LocationResponse(BaseSchema):
    """Schema for location response"""
    id: UUID
    tenant_id: UUID
    organization_id: Optional[UUID]
    parent_location_id: Optional[UUID]

    name: str
    type: Optional[str]
    code: Optional[str]

    building: Optional[str]
    floor: Optional[str]
    room: Optional[str]

    operational_status: Optional[str]
    is_active: bool

    created_at: datetime
    updated_at: datetime


# ============================================================================
# HEALTH CHECK SCHEMA
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="healthy or unhealthy")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    database: bool = Field(..., description="Database connection status")
