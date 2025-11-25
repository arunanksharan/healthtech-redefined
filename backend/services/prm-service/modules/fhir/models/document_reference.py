"""
FHIR DocumentReference Resource Model

A reference to a document of any kind for any purpose. Provides metadata about
the document and a link to the document itself.

Spec: https://www.hl7.org/fhir/R4/documentreference.html
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class DocumentReferenceStatus(str, Enum):
    """Status of the document reference."""
    CURRENT = "current"
    SUPERSEDED = "superseded"
    ENTERED_IN_ERROR = "entered-in-error"


class DocumentRelationshipType(str, Enum):
    """Type of document relationship."""
    REPLACES = "replaces"
    TRANSFORMS = "transforms"
    SIGNS = "signs"
    APPENDS = "appends"


class CompositionStatus(str, Enum):
    """Document composition status."""
    PRELIMINARY = "preliminary"
    FINAL = "final"
    AMENDED = "amended"
    ENTERED_IN_ERROR = "entered-in-error"


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


class Period(BaseModel):
    """A time period defined by a start and end date/time."""
    start: Optional[datetime] = None
    end: Optional[datetime] = None


class Attachment(BaseModel):
    """Content in a format defined elsewhere."""
    contentType: Optional[str] = None
    language: Optional[str] = None
    data: Optional[str] = None  # Base64 encoded
    url: Optional[str] = None
    size: Optional[int] = None
    hash: Optional[str] = None  # Base64 encoded SHA-1
    title: Optional[str] = None
    creation: Optional[datetime] = None


class DocumentReferenceRelatesTo(BaseModel):
    """Relationships to other documents."""
    code: DocumentRelationshipType
    target: Reference


class DocumentReferenceContent(BaseModel):
    """Document content."""
    attachment: Attachment
    format: Optional[Dict[str, Any]] = None  # Coding


class DocumentReferenceContext(BaseModel):
    """Clinical context of document."""
    encounter: Optional[List[Reference]] = None
    event: Optional[List[CodeableConcept]] = None
    period: Optional[Period] = None
    facilityType: Optional[CodeableConcept] = None
    practiceSetting: Optional[CodeableConcept] = None
    sourcePatientInfo: Optional[Reference] = None
    related: Optional[List[Reference]] = None


class DocumentReference(BaseModel):
    """
    FHIR DocumentReference Resource

    A reference to a document of any kind for any purpose. Provides metadata
    about the document so that the document can be discovered and managed.
    """
    resourceType: str = Field(default="DocumentReference", const=True)

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

    # Master version identifier
    masterIdentifier: Optional[Identifier] = None

    # Business identifiers
    identifier: Optional[List[Identifier]] = None

    # Status
    status: DocumentReferenceStatus = DocumentReferenceStatus.CURRENT
    docStatus: Optional[CompositionStatus] = None

    # Kind of document
    type: Optional[CodeableConcept] = None

    # Categorization of document
    category: Optional[List[CodeableConcept]] = None

    # Who/what is the subject
    subject: Optional[Reference] = None

    # When document was created
    date: Optional[datetime] = None

    # Who and/or what authored the document
    author: Optional[List[Reference]] = None

    # Who/what authenticated the document
    authenticator: Optional[Reference] = None

    # Organization which maintains the document
    custodian: Optional[Reference] = None

    # Relationships to other documents
    relatesTo: Optional[List[DocumentReferenceRelatesTo]] = None

    # Human-readable description
    description: Optional[str] = None

    # Document security-tags
    securityLabel: Optional[List[CodeableConcept]] = None

    # Document referenced
    content: List[DocumentReferenceContent]

    # Clinical context
    context: Optional[DocumentReferenceContext] = None

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
    def from_fhir_json(cls, data: Dict[str, Any]) -> "DocumentReference":
        """Create from FHIR JSON representation."""
        return cls(**data)


# FHIR search parameter definitions for DocumentReference
DOCUMENT_REFERENCE_SEARCH_PARAMS = {
    "authenticator": {"type": "reference", "path": "authenticator"},
    "author": {"type": "reference", "path": "author"},
    "category": {"type": "token", "path": "category"},
    "contenttype": {"type": "token", "path": "content.attachment.contentType"},
    "custodian": {"type": "reference", "path": "custodian"},
    "date": {"type": "date", "path": "date"},
    "description": {"type": "string", "path": "description"},
    "encounter": {"type": "reference", "path": "context.encounter"},
    "event": {"type": "token", "path": "context.event"},
    "facility": {"type": "token", "path": "context.facilityType"},
    "format": {"type": "token", "path": "content.format"},
    "identifier": {"type": "token", "path": "identifier"},
    "language": {"type": "token", "path": "content.attachment.language"},
    "location": {"type": "uri", "path": "content.attachment.url"},
    "patient": {"type": "reference", "path": "subject", "target": ["Patient"]},
    "period": {"type": "date", "path": "context.period"},
    "related": {"type": "reference", "path": "context.related"},
    "relatesto": {"type": "reference", "path": "relatesTo.target"},
    "relation": {"type": "token", "path": "relatesTo.code"},
    "security-label": {"type": "token", "path": "securityLabel"},
    "setting": {"type": "token", "path": "context.practiceSetting"},
    "status": {"type": "token", "path": "status"},
    "subject": {"type": "reference", "path": "subject"},
    "type": {"type": "token", "path": "type"},
}
