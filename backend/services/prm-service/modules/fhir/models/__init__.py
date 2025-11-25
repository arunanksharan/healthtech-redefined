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
from .location import Location
from .procedure import Procedure
from .medication_request import MedicationRequest
from .allergy_intolerance import AllergyIntolerance
from .code_system import CodeSystem
from .value_set import ValueSet
from .concept_map import ConceptMap
from .subscription import Subscription
from .service_request import ServiceRequest, SERVICE_REQUEST_SEARCH_PARAMS
from .diagnostic_report import DiagnosticReport, DIAGNOSTIC_REPORT_SEARCH_PARAMS
from .document_reference import DocumentReference, DOCUMENT_REFERENCE_SEARCH_PARAMS

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
    "Location",
    "Procedure",
    "MedicationRequest",
    "AllergyIntolerance",
    "CodeSystem",
    "ValueSet",
    "ConceptMap",
    "Subscription",
    "ServiceRequest",
    "SERVICE_REQUEST_SEARCH_PARAMS",
    "DiagnosticReport",
    "DIAGNOSTIC_REPORT_SEARCH_PARAMS",
    "DocumentReference",
    "DOCUMENT_REFERENCE_SEARCH_PARAMS",
]
