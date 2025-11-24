"""
FHIR R4 Base Resource Models
Common FHIR data types and base resource structure
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any, Union, Literal
from pydantic import BaseModel, Field, validator, HttpUrl
from enum import Enum


# ==================== Enums ====================

class IdentifierUse(str, Enum):
    """Identifier use codes"""
    USUAL = "usual"
    OFFICIAL = "official"
    TEMP = "temp"
    SECONDARY = "secondary"
    OLD = "old"


class NameUse(str, Enum):
    """Name use codes"""
    USUAL = "usual"
    OFFICIAL = "official"
    TEMP = "temp"
    NICKNAME = "nickname"
    ANONYMOUS = "anonymous"
    OLD = "old"
    MAIDEN = "maiden"


class ContactPointSystem(str, Enum):
    """Contact point system codes"""
    PHONE = "phone"
    FAX = "fax"
    EMAIL = "email"
    PAGER = "pager"
    URL = "url"
    SMS = "sms"
    OTHER = "other"


class ContactPointUse(str, Enum):
    """Contact point use codes"""
    HOME = "home"
    WORK = "work"
    TEMP = "temp"
    OLD = "old"
    MOBILE = "mobile"


class AddressUse(str, Enum):
    """Address use codes"""
    HOME = "home"
    WORK = "work"
    TEMP = "temp"
    OLD = "old"
    BILLING = "billing"


class AddressType(str, Enum):
    """Address type codes"""
    POSTAL = "postal"
    PHYSICAL = "physical"
    BOTH = "both"


class AdministrativeGender(str, Enum):
    """FHIR administrative gender codes"""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"


class QuantityComparator(str, Enum):
    """Quantity comparator codes"""
    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="


# ==================== Base Data Types ====================

class Extension(BaseModel):
    """FHIR Extension - additional information beyond base resource"""
    url: str = Field(..., description="Identifies the meaning of the extension")
    value: Optional[Any] = Field(None, description="Value of extension")

    class Config:
        extra = "allow"


class Coding(BaseModel):
    """FHIR Coding - reference to a code defined by a terminology system"""
    system: Optional[HttpUrl] = Field(None, description="Identity of the terminology system")
    version: Optional[str] = Field(None, description="Version of the system")
    code: Optional[str] = Field(None, description="Symbol in syntax defined by the system")
    display: Optional[str] = Field(None, description="Representation defined by the system")
    userSelected: Optional[bool] = Field(None, description="If this coding was chosen directly by the user")

    class Config:
        schema_extra = {
            "example": {
                "system": "http://snomed.info/sct",
                "code": "38341003",
                "display": "Hypertensive disorder"
            }
        }


class CodeableConcept(BaseModel):
    """FHIR CodeableConcept - concept with multiple codings and text"""
    coding: Optional[List[Coding]] = Field(None, description="Code defined by a terminology system")
    text: Optional[str] = Field(None, description="Plain text representation")

    class Config:
        schema_extra = {
            "example": {
                "coding": [{
                    "system": "http://snomed.info/sct",
                    "code": "38341003",
                    "display": "Hypertensive disorder"
                }],
                "text": "High Blood Pressure"
            }
        }


class Identifier(BaseModel):
    """FHIR Identifier - unique identifier for a resource"""
    use: Optional[IdentifierUse] = Field(None, description="usual | official | temp | secondary | old")
    type: Optional[CodeableConcept] = Field(None, description="Description of identifier")
    system: Optional[HttpUrl] = Field(None, description="The namespace for the identifier value")
    value: Optional[str] = Field(None, description="The value that is unique")
    period: Optional['Period'] = Field(None, description="Time period when id is/was valid for use")
    assigner: Optional['Reference'] = Field(None, description="Organization that issued id")

    class Config:
        schema_extra = {
            "example": {
                "use": "official",
                "system": "http://hospital.org/patients",
                "value": "MRN12345"
            }
        }


class Period(BaseModel):
    """FHIR Period - time period defined by start and end date/time"""
    start: Optional[datetime] = Field(None, description="Starting time with inclusive boundary")
    end: Optional[datetime] = Field(None, description="End time with inclusive boundary")

    @validator('end')
    def end_after_start(cls, v, values):
        """Ensure end is after start"""
        if v and 'start' in values and values['start']:
            if v < values['start']:
                raise ValueError('End date must be after start date')
        return v


class HumanName(BaseModel):
    """FHIR HumanName - name of a human with text, parts and usage information"""
    use: Optional[NameUse] = Field(None, description="usual | official | temp | nickname | anonymous | old | maiden")
    text: Optional[str] = Field(None, description="Text representation of the full name")
    family: Optional[str] = Field(None, description="Family name (surname)")
    given: Optional[List[str]] = Field(None, description="Given names (not always 'first')")
    prefix: Optional[List[str]] = Field(None, description="Parts that come before the name")
    suffix: Optional[List[str]] = Field(None, description="Parts that come after the name")
    period: Optional[Period] = Field(None, description="Time period when name was/is in use")

    class Config:
        schema_extra = {
            "example": {
                "use": "official",
                "family": "Smith",
                "given": ["John", "Michael"],
                "prefix": ["Dr."]
            }
        }


class ContactPoint(BaseModel):
    """FHIR ContactPoint - details for contact purposes"""
    system: Optional[ContactPointSystem] = Field(None, description="phone | fax | email | pager | url | sms | other")
    value: Optional[str] = Field(None, description="The actual contact point details")
    use: Optional[ContactPointUse] = Field(None, description="home | work | temp | old | mobile")
    rank: Optional[int] = Field(None, description="Specify preferred order of use (1 = highest)", ge=1)
    period: Optional[Period] = Field(None, description="Time period when the contact point was/is in use")

    class Config:
        schema_extra = {
            "example": {
                "system": "phone",
                "value": "+1-555-1234",
                "use": "mobile",
                "rank": 1
            }
        }


class Address(BaseModel):
    """FHIR Address - postal address"""
    use: Optional[AddressUse] = Field(None, description="home | work | temp | old | billing")
    type: Optional[AddressType] = Field(None, description="postal | physical | both")
    text: Optional[str] = Field(None, description="Text representation of the address")
    line: Optional[List[str]] = Field(None, description="Street name, number, direction & P.O. Box etc.")
    city: Optional[str] = Field(None, description="Name of city, town etc.")
    district: Optional[str] = Field(None, description="District name (aka county)")
    state: Optional[str] = Field(None, description="Sub-unit of country (abbreviations ok)")
    postalCode: Optional[str] = Field(None, description="Postal code for area")
    country: Optional[str] = Field(None, description="Country (e.g. can be ISO 3166 2 or 3 letter code)")
    period: Optional[Period] = Field(None, description="Time period when address was/is in use")

    class Config:
        schema_extra = {
            "example": {
                "use": "home",
                "type": "physical",
                "line": ["123 Main Street", "Apt 4B"],
                "city": "Springfield",
                "state": "IL",
                "postalCode": "62701",
                "country": "US"
            }
        }


class Reference(BaseModel):
    """FHIR Reference - reference to another resource"""
    reference: Optional[str] = Field(None, description="Literal reference, Relative, internal or absolute URL")
    type: Optional[str] = Field(None, description="Type the reference refers to (e.g. 'Patient')")
    identifier: Optional[Identifier] = Field(None, description="Logical reference, when literal reference is not known")
    display: Optional[str] = Field(None, description="Text alternative for the resource")

    class Config:
        schema_extra = {
            "example": {
                "reference": "Patient/123",
                "type": "Patient",
                "display": "John Smith"
            }
        }


class Quantity(BaseModel):
    """FHIR Quantity - measured or measurable amount"""
    value: Optional[float] = Field(None, description="Numerical value (with implicit precision)")
    comparator: Optional[QuantityComparator] = Field(None, description="< | <= | >= | >")
    unit: Optional[str] = Field(None, description="Unit representation")
    system: Optional[HttpUrl] = Field(None, description="System that defines coded unit form")
    code: Optional[str] = Field(None, description="Coded form of the unit")

    class Config:
        schema_extra = {
            "example": {
                "value": 72.5,
                "unit": "kg",
                "system": "http://unitsofmeasure.org",
                "code": "kg"
            }
        }


class Range(BaseModel):
    """FHIR Range - set of values bounded by low and high"""
    low: Optional[Quantity] = Field(None, description="Low limit")
    high: Optional[Quantity] = Field(None, description="High limit")


class Ratio(BaseModel):
    """FHIR Ratio - ratio of two quantity values"""
    numerator: Optional[Quantity] = Field(None, description="Numerator value")
    denominator: Optional[Quantity] = Field(None, description="Denominator value")


class Attachment(BaseModel):
    """FHIR Attachment - content in a format defined elsewhere"""
    contentType: Optional[str] = Field(None, description="Mime type of the content")
    language: Optional[str] = Field(None, description="Human language of the content")
    data: Optional[str] = Field(None, description="Data inline, base64ed")
    url: Optional[HttpUrl] = Field(None, description="Uri where the data can be found")
    size: Optional[int] = Field(None, description="Number of bytes of content", ge=0)
    hash: Optional[str] = Field(None, description="Hash of the data (sha-1, base64ed)")
    title: Optional[str] = Field(None, description="Label to display in place of the data")
    creation: Optional[datetime] = Field(None, description="Date attachment was first created")


class Annotation(BaseModel):
    """FHIR Annotation - text node with attribution"""
    author: Optional[Union[Reference, str]] = Field(None, description="Individual responsible for the annotation")
    time: Optional[datetime] = Field(None, description="When the annotation was made")
    text: str = Field(..., description="The annotation - text content")


class Meta(BaseModel):
    """FHIR Meta - metadata about a resource"""
    versionId: Optional[str] = Field(None, description="Version specific identifier")
    lastUpdated: Optional[datetime] = Field(None, description="When the resource version last changed")
    source: Optional[HttpUrl] = Field(None, description="Identifies where the resource comes from")
    profile: Optional[List[str]] = Field(None, description="Profiles this resource claims to conform to")
    security: Optional[List[Coding]] = Field(None, description="Security Labels applied to this resource")
    tag: Optional[List[Coding]] = Field(None, description="Tags applied to this resource")


# ==================== Base Resource ====================

class FHIRResource(BaseModel):
    """Base FHIR Resource - all resources inherit from this"""
    resourceType: str = Field(..., description="Type of resource")
    id: Optional[str] = Field(None, description="Logical id of this artifact")
    meta: Optional[Meta] = Field(None, description="Metadata about the resource")
    implicitRules: Optional[HttpUrl] = Field(None, description="A set of rules under which this content was created")
    language: Optional[str] = Field(None, description="Language of the resource content")

    # Extension support
    extension: Optional[List[Extension]] = Field(None, description="Additional content defined by implementations")
    modifierExtension: Optional[List[Extension]] = Field(None, description="Extensions that cannot be ignored")

    class Config:
        extra = "forbid"
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
        }

    def dict(self, **kwargs):
        """Override dict to exclude None values"""
        kwargs.setdefault('exclude_none', True)
        return super().dict(**kwargs)


# Update forward references
Identifier.update_forward_refs()
Reference.update_forward_refs()
