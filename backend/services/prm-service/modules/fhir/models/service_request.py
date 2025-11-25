"""
FHIR ServiceRequest Resource Model

A record of a request for a service such as laboratory tests, imaging, referrals,
or any other clinical service to be performed.

Spec: https://www.hl7.org/fhir/R4/servicerequest.html
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ServiceRequestStatus(str, Enum):
    """Status of the service request."""
    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on-hold"
    REVOKED = "revoked"
    COMPLETED = "completed"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"


class ServiceRequestIntent(str, Enum):
    """Intent of the service request."""
    PROPOSAL = "proposal"
    PLAN = "plan"
    DIRECTIVE = "directive"
    ORDER = "order"
    ORIGINAL_ORDER = "original-order"
    REFLEX_ORDER = "reflex-order"
    FILLER_ORDER = "filler-order"
    INSTANCE_ORDER = "instance-order"
    OPTION = "option"


class ServiceRequestPriority(str, Enum):
    """Priority of the request."""
    ROUTINE = "routine"
    URGENT = "urgent"
    ASAP = "asap"
    STAT = "stat"


class Identifier(BaseModel):
    """An identifier for this resource."""
    use: Optional[str] = None
    type: Optional[Dict[str, Any]] = None
    system: Optional[str] = None
    value: Optional[str] = None
    period: Optional[Dict[str, Any]] = None
    assigner: Optional[Dict[str, Any]] = None


class CodeableConcept(BaseModel):
    """A CodeableConcept represents a value using codes."""
    coding: Optional[List[Dict[str, Any]]] = None
    text: Optional[str] = None


class Reference(BaseModel):
    """A reference to another resource."""
    reference: Optional[str] = None
    type: Optional[str] = None
    identifier: Optional[Identifier] = None
    display: Optional[str] = None


class Quantity(BaseModel):
    """A measured or measurable quantity."""
    value: Optional[float] = None
    comparator: Optional[str] = None
    unit: Optional[str] = None
    system: Optional[str] = None
    code: Optional[str] = None


class Period(BaseModel):
    """A time period defined by a start and end date/time."""
    start: Optional[datetime] = None
    end: Optional[datetime] = None


class Timing(BaseModel):
    """Specifies an event that may occur multiple times."""
    event: Optional[List[datetime]] = None
    repeat: Optional[Dict[str, Any]] = None
    code: Optional[CodeableConcept] = None


class Annotation(BaseModel):
    """A note that holds additional information about a resource."""
    authorReference: Optional[Reference] = None
    authorString: Optional[str] = None
    time: Optional[datetime] = None
    text: str


class ServiceRequest(BaseModel):
    """
    FHIR ServiceRequest Resource

    A record of a request for service such as diagnostic investigations,
    treatments, or operations to be performed.
    """
    resourceType: str = Field(default="ServiceRequest", const=True)

    # Resource identifier
    id: Optional[str] = None

    # Metadata
    meta: Optional[Dict[str, Any]] = None
    implicitRules: Optional[str] = None
    language: Optional[str] = None
    text: Optional[Dict[str, Any]] = None
    contained: Optional[List[Dict[str, Any]]] = None
    extension: Optional[List[Dict[str, Any]]] = None
    modifierExtension: Optional[List[Dict[str, Any]]] = None

    # Business identifiers
    identifier: Optional[List[Identifier]] = None
    instantiatesCanonical: Optional[List[str]] = None
    instantiatesUri: Optional[List[str]] = None
    basedOn: Optional[List[Reference]] = None
    replaces: Optional[List[Reference]] = None
    requisition: Optional[Identifier] = None

    # Status
    status: ServiceRequestStatus = ServiceRequestStatus.DRAFT
    intent: ServiceRequestIntent = ServiceRequestIntent.ORDER
    category: Optional[List[CodeableConcept]] = None
    priority: Optional[ServiceRequestPriority] = None
    doNotPerform: Optional[bool] = None

    # What is being requested
    code: Optional[CodeableConcept] = None
    orderDetail: Optional[List[CodeableConcept]] = None

    # Quantity
    quantityQuantity: Optional[Quantity] = None
    quantityRatio: Optional[Dict[str, Any]] = None
    quantityRange: Optional[Dict[str, Any]] = None

    # Subject and context
    subject: Reference
    encounter: Optional[Reference] = None

    # When service should occur
    occurrenceDateTime: Optional[datetime] = None
    occurrencePeriod: Optional[Period] = None
    occurrenceTiming: Optional[Timing] = None

    # Conditional aspects
    asNeededBoolean: Optional[bool] = None
    asNeededCodeableConcept: Optional[CodeableConcept] = None

    # Dates
    authoredOn: Optional[datetime] = None

    # Requester
    requester: Optional[Reference] = None
    performerType: Optional[CodeableConcept] = None
    performer: Optional[List[Reference]] = None

    # Location
    locationCode: Optional[List[CodeableConcept]] = None
    locationReference: Optional[List[Reference]] = None

    # Clinical reasons
    reasonCode: Optional[List[CodeableConcept]] = None
    reasonReference: Optional[List[Reference]] = None

    # Insurance
    insurance: Optional[List[Reference]] = None

    # Supporting information
    supportingInfo: Optional[List[Reference]] = None

    # Specimen
    specimen: Optional[List[Reference]] = None

    # Body site
    bodySite: Optional[List[CodeableConcept]] = None

    # Notes
    note: Optional[List[Annotation]] = None

    # Patient instructions
    patientInstruction: Optional[str] = None

    # Related requests
    relevantHistory: Optional[List[Reference]] = None

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

    def to_fhir_json(self) -> Dict[str, Any]:
        """Convert to FHIR JSON representation."""
        data = self.dict(exclude_none=True, by_alias=True)
        return data

    @classmethod
    def from_fhir_json(cls, data: Dict[str, Any]) -> "ServiceRequest":
        """Create from FHIR JSON representation."""
        return cls(**data)


# FHIR search parameter definitions for ServiceRequest
SERVICE_REQUEST_SEARCH_PARAMS = {
    "authored": {"type": "date", "path": "authoredOn"},
    "based-on": {"type": "reference", "path": "basedOn"},
    "body-site": {"type": "token", "path": "bodySite"},
    "category": {"type": "token", "path": "category"},
    "code": {"type": "token", "path": "code"},
    "encounter": {"type": "reference", "path": "encounter"},
    "identifier": {"type": "token", "path": "identifier"},
    "instantiates-canonical": {"type": "reference", "path": "instantiatesCanonical"},
    "instantiates-uri": {"type": "uri", "path": "instantiatesUri"},
    "intent": {"type": "token", "path": "intent"},
    "occurrence": {"type": "date", "path": "occurrence[x]"},
    "patient": {"type": "reference", "path": "subject", "target": ["Patient"]},
    "performer": {"type": "reference", "path": "performer"},
    "performer-type": {"type": "token", "path": "performerType"},
    "priority": {"type": "token", "path": "priority"},
    "replaces": {"type": "reference", "path": "replaces"},
    "requester": {"type": "reference", "path": "requester"},
    "requisition": {"type": "token", "path": "requisition"},
    "specimen": {"type": "reference", "path": "specimen"},
    "status": {"type": "token", "path": "status"},
    "subject": {"type": "reference", "path": "subject"},
}
