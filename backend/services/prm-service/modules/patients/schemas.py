"""
Patient Schemas
FHIR-compliant patient management schemas
"""
from datetime import date, datetime
from typing import List, Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator, EmailStr
from enum import Enum
import re


# ==================== Enums ====================

class Gender(str, Enum):
    """FHIR gender codes"""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"


class PatientStatus(str, Enum):
    """Patient status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DECEASED = "deceased"


class MaritalStatus(str, Enum):
    """FHIR marital status codes"""
    SINGLE = "S"
    MARRIED = "M"
    DIVORCED = "D"
    WIDOWED = "W"
    SEPARATED = "L"
    UNKNOWN = "UNK"


class ContactMethod(str, Enum):
    """Preferred contact method"""
    PHONE = "phone"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    SMS = "sms"
    MAIL = "mail"


# ==================== Sub-Models ====================

class EmergencyContact(BaseModel):
    """Emergency contact information"""
    name: str = Field(..., min_length=1, max_length=200)
    relationship: str = Field(..., max_length=100)
    phone: str = Field(..., description="Phone number")
    email: Optional[EmailStr] = None

    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format"""
        # Remove non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', v)

        # Check for minimum length
        if len(cleaned) < 10:
            raise ValueError('Phone number too short')

        # Add + if not present and doesn't start with 1
        if not cleaned.startswith('+'):
            if cleaned.startswith('1') and len(cleaned) == 11:
                cleaned = '+' + cleaned
            elif len(cleaned) == 10:
                cleaned = '+1' + cleaned
            else:
                cleaned = '+' + cleaned

        return cleaned


class Address(BaseModel):
    """FHIR-compliant address"""
    use: Optional[str] = Field("home", description="home | work | temp | old")
    line1: str = Field(..., max_length=200, description="Street address line 1")
    line2: Optional[str] = Field(None, max_length=200, description="Street address line 2")
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=2, description="Two-letter state code")
    postal_code: str = Field(..., max_length=10, description="ZIP code")
    country: str = Field("US", max_length=2, description="ISO country code")

    @validator('state')
    def validate_state(cls, v):
        """Validate state code"""
        return v.upper()

    @validator('postal_code')
    def validate_postal_code(cls, v):
        """Validate ZIP code format"""
        # Remove spaces and dashes
        cleaned = re.sub(r'[\s-]', '', v)

        # Check format (5 digits or 5+4 digits)
        if not re.match(r'^\d{5}(\d{4})?$', cleaned):
            raise ValueError('Invalid ZIP code format')

        return cleaned


class InsuranceInfo(BaseModel):
    """Insurance information"""
    provider_name: str = Field(..., max_length=200)
    policy_number: str = Field(..., max_length=100)
    group_number: Optional[str] = Field(None, max_length=100)
    subscriber_name: Optional[str] = Field(None, max_length=200)
    subscriber_relationship: Optional[str] = Field(None, max_length=50)
    effective_date: Optional[date] = None
    expiration_date: Optional[date] = None


# ==================== Request Schemas ====================

class PatientCreate(BaseModel):
    """Create new patient"""
    # Identity
    legal_name: str = Field(..., min_length=1, max_length=200, description="Full legal name")
    preferred_name: Optional[str] = Field(None, max_length=200)
    date_of_birth: date = Field(..., description="Date of birth")
    gender: Gender
    ssn: Optional[str] = Field(None, description="Social Security Number (encrypted)")

    # Contact
    primary_phone: str = Field(..., description="Primary phone number")
    secondary_phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[Address] = None
    preferred_contact_method: ContactMethod = ContactMethod.PHONE

    # Demographics
    race: Optional[str] = Field(None, max_length=100)
    ethnicity: Optional[str] = Field(None, max_length=100)
    preferred_language: str = Field("en", max_length=10, description="ISO language code")
    marital_status: Optional[MaritalStatus] = None

    # Care
    primary_care_provider_id: Optional[UUID] = None
    emergency_contact: Optional[EmergencyContact] = None
    insurance: Optional[InsuranceInfo] = None

    @validator('primary_phone', 'secondary_phone')
    def validate_phone(cls, v):
        """Validate and normalize phone numbers"""
        if not v:
            return v

        # Remove non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', v)

        # Check for minimum length
        if len(cleaned) < 10:
            raise ValueError('Phone number too short')

        # Add + if not present
        if not cleaned.startswith('+'):
            if cleaned.startswith('1') and len(cleaned) == 11:
                cleaned = '+' + cleaned
            elif len(cleaned) == 10:
                cleaned = '+1' + cleaned
            else:
                cleaned = '+' + cleaned

        return cleaned

    @validator('ssn')
    def validate_ssn(cls, v):
        """Validate SSN format"""
        if not v:
            return v

        # Remove non-digit characters
        cleaned = re.sub(r'\D', '', v)

        # Check length
        if len(cleaned) != 9:
            raise ValueError('SSN must be 9 digits')

        # Return formatted (will be encrypted before storage)
        return f"{cleaned[:3]}-{cleaned[3:5]}-{cleaned[5:]}"

    @validator('date_of_birth')
    def validate_dob(cls, v):
        """Validate date of birth"""
        if v > date.today():
            raise ValueError('Date of birth cannot be in the future')

        # Check age is reasonable (not older than 150 years)
        age = (date.today() - v).days / 365.25
        if age > 150:
            raise ValueError('Date of birth is too far in the past')

        return v


class PatientUpdate(BaseModel):
    """Update patient information"""
    legal_name: Optional[str] = Field(None, max_length=200)
    preferred_name: Optional[str] = Field(None, max_length=200)
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None

    # Contact
    primary_phone: Optional[str] = None
    secondary_phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[Address] = None
    preferred_contact_method: Optional[ContactMethod] = None

    # Demographics
    race: Optional[str] = Field(None, max_length=100)
    ethnicity: Optional[str] = Field(None, max_length=100)
    preferred_language: Optional[str] = Field(None, max_length=10)
    marital_status: Optional[MaritalStatus] = None

    # Care
    primary_care_provider_id: Optional[UUID] = None
    emergency_contact: Optional[EmergencyContact] = None
    insurance: Optional[InsuranceInfo] = None
    status: Optional[PatientStatus] = None


class PatientSearch(BaseModel):
    """Search/filter patients"""
    query: Optional[str] = Field(None, description="Search name, MRN, phone, email")
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    status: Optional[PatientStatus] = None
    primary_care_provider_id: Optional[UUID] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)


# ==================== Response Schemas ====================

class PatientResponse(BaseModel):
    """Patient response"""
    id: UUID
    org_id: Optional[UUID] = None

    # Identity
    mrn: str = Field(..., description="Medical Record Number")
    legal_name: str
    preferred_name: Optional[str]
    date_of_birth: date
    gender: Gender
    age: Optional[int] = None  # Calculated

    # Contact
    primary_phone: str
    secondary_phone: Optional[str]
    email: Optional[str]
    address: Optional[Address]
    preferred_contact_method: ContactMethod

    # Demographics
    race: Optional[str]
    ethnicity: Optional[str]
    preferred_language: str
    marital_status: Optional[MaritalStatus]

    # Care
    primary_care_provider_id: Optional[UUID]
    emergency_contact: Optional[EmergencyContact]
    insurance: Optional[InsuranceInfo]

    # Status
    status: PatientStatus

    # Audit
    created_at: datetime
    updated_at: datetime

    @property
    def display_name(self) -> str:
        """Get display name (preferred or legal)"""
        return self.preferred_name or self.legal_name

    @property
    def calculated_age(self) -> int:
        """Calculate current age"""
        today = date.today()
        age = today.year - self.date_of_birth.year

        # Adjust if birthday hasn't occurred this year
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            age -= 1

        return age

    class Config:
        from_attributes = True


class PatientDetailResponse(PatientResponse):
    """Detailed patient response with statistics"""
    total_appointments: int = 0
    upcoming_appointments: int = 0
    total_conversations: int = 0
    total_media_files: int = 0
    last_visit_date: Optional[datetime] = None
    next_appointment_date: Optional[datetime] = None


class DuplicatePatient(BaseModel):
    """Potential duplicate patient"""
    patient: PatientResponse
    match_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    match_reasons: List[str] = Field(..., description="Why this is a potential duplicate")


class PatientMergeRequest(BaseModel):
    """Request to merge duplicate patients"""
    primary_patient_id: UUID = Field(..., description="Patient to keep")
    duplicate_patient_id: UUID = Field(..., description="Patient to merge and deactivate")
    reason: Optional[str] = Field(None, description="Reason for merge")


class PatientMergeResult(BaseModel):
    """Result of patient merge operation"""
    success: bool
    primary_patient: PatientResponse
    merged_data: dict = Field(..., description="Summary of merged data")
    errors: List[str] = Field(default_factory=list)


# ==================== Statistics ====================

class PatientStatistics(BaseModel):
    """Patient demographics and statistics"""
    total_patients: int
    active_patients: int
    inactive_patients: int
    new_patients_this_month: int
    patients_by_gender: dict[str, int]
    patients_by_age_group: dict[str, int]  # 0-18, 19-35, 36-50, 51-65, 66+
    patients_by_status: dict[str, int]
    average_age: float


# ==================== List Response ====================

class PatientListResponse(BaseModel):
    """Paginated patient list response"""
    items: List[PatientResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool



class PatientIdentifierSimple(BaseModel):
    system: str
    value: str
    is_primary: bool = False

    class Config:
        from_attributes = True

# ==================== Simple Patient Response (matches DB model) ====================

class PatientSimpleResponse(BaseModel):
    """Simple patient response matching database model"""
    id: UUID
    tenant_id: Optional[UUID] = None

    # Identity
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None

    # Contact
    phone_primary: Optional[str] = None
    phone_secondary: Optional[str] = None
    email_primary: Optional[str] = None

    # Address
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

    # Demographics
    marital_status: Optional[str] = None
    blood_group: Optional[str] = None
    language_preferred: Optional[str] = None

    # Status
    is_deceased: bool = False

    # Metadata
    meta_data: Optional[dict] = None

    # Audit
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Computed fields (defined last to access others in validators)
    identifiers: Optional[List[PatientIdentifierSimple]] = Field(default=None, exclude=True)
    mrn: Optional[str] = None

    @property
    def name(self) -> str:
        """Full name"""
        parts = [self.first_name, self.middle_name, self.last_name]
        return " ".join(p for p in parts if p)

    @validator("mrn", always=True)
    def get_mrn(cls, v, values):
        """Get MRN from metadata or identifiers"""
        if v:
            return v
            
        # Try metadata first
        meta_data = values.get("meta_data")
        if meta_data and isinstance(meta_data, dict) and "mrn" in meta_data:
            return meta_data["mrn"]
            
        # Try identifiers relationship
        identifiers = values.get("identifiers")
        if identifiers:
            for ident in identifiers:
                # Handle both dict (if pre-serialized) and ORM object
                if isinstance(ident, dict):
                    if ident.get("system") == "MRN":
                        return ident.get("value")
                else:
                    try:
                        if getattr(ident, "system", None) == "MRN":
                            return getattr(ident, "value", None)
                    except Exception:
                        continue
                        
        return None

    class Config:
        from_attributes = True


class PatientSimpleListResponse(BaseModel):
    """Paginated patient list response with simple model"""
    items: List[PatientSimpleResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== 360 View ====================

class Patient360Response(BaseModel):
    """360-degree patient view with all related data"""
    patient: PatientSimpleResponse

    # Related data summary
    appointments: List[dict] = []
    journeys: List[dict] = []
    tickets: List[dict] = []
    communications: List[dict] = []

    # Counts
    total_appointments: int = 0
    upcoming_appointments: int = 0
    active_journeys: int = 0
    open_tickets: int = 0
    recent_communications: int = 0

    # Timeline
    last_visit_date: Optional[datetime] = None
    next_appointment_date: Optional[datetime] = None


# ==================== Search Types ====================

class SearchType(str, Enum):
    """Search type for quick search"""
    PHONE = "phone"
    NAME = "name"
    MRN = "mrn"
    EMAIL = "email"
