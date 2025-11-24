"""
FHIR R4 Resource Models
Pydantic models for FHIR R4 resources
"""

from .base import (
    FHIRResource,
    Meta,
    Identifier,
    HumanName,
    ContactPoint,
    Address,
    CodeableConcept,
    Coding,
    Reference,
    Period,
    Quantity,
    Range,
    Ratio,
    Attachment,
    Annotation
)

from .patient import Patient
from .practitioner import Practitioner, PractitionerRole
from .organization import Organization
from .encounter import Encounter
from .observation import Observation
from .condition import Condition

__all__ = [
    "FHIRResource",
    "Meta",
    "Identifier",
    "HumanName",
    "ContactPoint",
    "Address",
    "CodeableConcept",
    "Coding",
    "Reference",
    "Period",
    "Quantity",
    "Range",
    "Ratio",
    "Attachment",
    "Annotation",
    "Patient",
    "Practitioner",
    "PractitionerRole",
    "Organization",
    "Encounter",
    "Observation",
    "Condition",
]
