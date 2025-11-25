"""
FHIR DiagnosticReport Resource Model

The findings and interpretation of diagnostic tests performed on patients,
groups of patients, devices, and locations.

Spec: https://www.hl7.org/fhir/R4/diagnosticreport.html
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class DiagnosticReportStatus(str, Enum):
    """Status of the diagnostic report."""
    REGISTERED = "registered"
    PARTIAL = "partial"
    PRELIMINARY = "preliminary"
    FINAL = "final"
    AMENDED = "amended"
    CORRECTED = "corrected"
    APPENDED = "appended"
    CANCELLED = "cancelled"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"


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


class DiagnosticReportMedia(BaseModel):
    """Key images associated with the report."""
    comment: Optional[str] = None
    link: Reference


class DiagnosticReport(BaseModel):
    """
    FHIR DiagnosticReport Resource

    The findings and interpretation of diagnostic tests performed on patients,
    groups of patients, devices, and locations.
    """
    resourceType: str = Field(default="DiagnosticReport", const=True)

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

    # What request this fulfills
    basedOn: Optional[List[Reference]] = None

    # Status
    status: DiagnosticReportStatus = DiagnosticReportStatus.FINAL

    # Service category
    category: Optional[List[CodeableConcept]] = None

    # Report code/name
    code: CodeableConcept

    # Subject of the report
    subject: Optional[Reference] = None

    # Healthcare event context
    encounter: Optional[Reference] = None

    # Clinically relevant time
    effectiveDateTime: Optional[datetime] = None
    effectivePeriod: Optional[Period] = None

    # When report was released
    issued: Optional[datetime] = None

    # Who is responsible for the report
    performer: Optional[List[Reference]] = None
    resultsInterpreter: Optional[List[Reference]] = None

    # Specimens used
    specimen: Optional[List[Reference]] = None

    # Observations
    result: Optional[List[Reference]] = None

    # Reference to imaging study
    imagingStudy: Optional[List[Reference]] = None

    # Key images
    media: Optional[List[DiagnosticReportMedia]] = None

    # Clinical conclusion
    conclusion: Optional[str] = None
    conclusionCode: Optional[List[CodeableConcept]] = None

    # Entire report as attachment
    presentedForm: Optional[List[Attachment]] = None

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
    def from_fhir_json(cls, data: Dict[str, Any]) -> "DiagnosticReport":
        """Create from FHIR JSON representation."""
        return cls(**data)


# FHIR search parameter definitions for DiagnosticReport
DIAGNOSTIC_REPORT_SEARCH_PARAMS = {
    "based-on": {"type": "reference", "path": "basedOn"},
    "category": {"type": "token", "path": "category"},
    "code": {"type": "token", "path": "code"},
    "conclusion": {"type": "token", "path": "conclusionCode"},
    "date": {"type": "date", "path": "effective[x]"},
    "encounter": {"type": "reference", "path": "encounter"},
    "identifier": {"type": "token", "path": "identifier"},
    "issued": {"type": "date", "path": "issued"},
    "media": {"type": "reference", "path": "media.link"},
    "patient": {"type": "reference", "path": "subject", "target": ["Patient"]},
    "performer": {"type": "reference", "path": "performer"},
    "result": {"type": "reference", "path": "result"},
    "results-interpreter": {"type": "reference", "path": "resultsInterpreter"},
    "specimen": {"type": "reference", "path": "specimen"},
    "status": {"type": "token", "path": "status"},
    "subject": {"type": "reference", "path": "subject"},
}
