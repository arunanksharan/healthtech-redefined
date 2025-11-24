"""
FHIR R4 Observation Resource
Measurements and simple assertions made about a patient
"""

from datetime import datetime
from typing import List, Optional, Union, Literal
from pydantic import Field
from enum import Enum

from .base import (
    FHIRResource,
    Identifier,
    CodeableConcept,
    Reference,
    Period,
    Quantity,
    Range,
    Ratio,
    Attachment,
    Annotation
)


class ObservationStatus(str, Enum):
    """Status of the observation"""
    REGISTERED = "registered"
    PRELIMINARY = "preliminary"
    FINAL = "final"
    AMENDED = "amended"
    CORRECTED = "corrected"
    CANCELLED = "cancelled"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"


class ObservationReferenceRange(FHIRResource):
    """Provides guide for interpretation of observation value"""
    low: Optional[Quantity] = Field(
        None,
        description="Low Range, if relevant"
    )
    high: Optional[Quantity] = Field(
        None,
        description="High Range, if relevant"
    )
    type: Optional[CodeableConcept] = Field(
        None,
        description="Reference range qualifier"
    )
    appliesTo: Optional[List[CodeableConcept]] = Field(
        None,
        description="Reference range population"
    )
    age: Optional[Range] = Field(
        None,
        description="Applicable age range, if relevant"
    )
    text: Optional[str] = Field(
        None,
        description="Text based reference range in an observation"
    )


class ObservationComponent(FHIRResource):
    """Component results for observations with multiple values"""
    code: CodeableConcept = Field(
        ...,
        description="Type of component observation"
    )

    # Value can be multiple types
    valueQuantity: Optional[Quantity] = None
    valueCodeableConcept: Optional[CodeableConcept] = None
    valueString: Optional[str] = None
    valueBoolean: Optional[bool] = None
    valueInteger: Optional[int] = None
    valueRange: Optional[Range] = None
    valueRatio: Optional[Ratio] = None
    valueDateTime: Optional[datetime] = None
    valuePeriod: Optional[Period] = None

    dataAbsentReason: Optional[CodeableConcept] = Field(
        None,
        description="Why the component result is missing"
    )

    interpretation: Optional[List[CodeableConcept]] = Field(
        None,
        description="High, low, normal, etc."
    )

    referenceRange: Optional[List[ObservationReferenceRange]] = Field(
        None,
        description="Provides guide for interpretation of component result"
    )


class Observation(FHIRResource):
    """
    FHIR R4 Observation Resource
    Measurements and simple assertions made about a patient, device or other subject.
    """

    resourceType: Literal["Observation"] = "Observation"

    # Identifiers
    identifier: Optional[List[Identifier]] = Field(
        None,
        description="Business Identifier for observation"
    )

    # Based on
    basedOn: Optional[List[Reference]] = Field(
        None,
        description="Fulfills plan, proposal or order"
    )

    # Part of
    partOf: Optional[List[Reference]] = Field(
        None,
        description="Part of referenced event"
    )

    # Status
    status: ObservationStatus = Field(
        ...,
        description="registered | preliminary | final | amended | corrected | cancelled | entered-in-error | unknown"
    )

    # Category
    category: Optional[List[CodeableConcept]] = Field(
        None,
        description="Classification of type of observation"
    )

    # Code (what was observed)
    code: CodeableConcept = Field(
        ...,
        description="Type of observation (code / type)"
    )

    # Subject
    subject: Optional[Reference] = Field(
        None,
        description="Who and/or what the observation is about"
    )

    # Focus
    focus: Optional[List[Reference]] = Field(
        None,
        description="What the observation is about, when it is not about the subject of record"
    )

    # Encounter
    encounter: Optional[Reference] = Field(
        None,
        description="Healthcare event during which this observation is made"
    )

    # Effective time
    effectiveDateTime: Optional[datetime] = Field(
        None,
        description="Clinically relevant time/time-period for observation"
    )
    effectivePeriod: Optional[Period] = None
    effectiveInstant: Optional[datetime] = None

    # Issued
    issued: Optional[datetime] = Field(
        None,
        description="Date/Time this version was made available"
    )

    # Performer
    performer: Optional[List[Reference]] = Field(
        None,
        description="Who is responsible for the observation"
    )

    # Value - can be of multiple types
    valueQuantity: Optional[Quantity] = None
    valueCodeableConcept: Optional[CodeableConcept] = None
    valueString: Optional[str] = None
    valueBoolean: Optional[bool] = None
    valueInteger: Optional[int] = None
    valueRange: Optional[Range] = None
    valueRatio: Optional[Ratio] = None
    valueDateTime: Optional[datetime] = None
    valuePeriod: Optional[Period] = None
    valueAttachment: Optional[Attachment] = None

    # Data absent reason
    dataAbsentReason: Optional[CodeableConcept] = Field(
        None,
        description="Why the result is missing"
    )

    # Interpretation
    interpretation: Optional[List[CodeableConcept]] = Field(
        None,
        description="High, low, normal, etc."
    )

    # Notes
    note: Optional[List[Annotation]] = Field(
        None,
        description="Comments about the observation"
    )

    # Body site
    bodySite: Optional[CodeableConcept] = Field(
        None,
        description="Observed body part"
    )

    # Method
    method: Optional[CodeableConcept] = Field(
        None,
        description="How it was done"
    )

    # Specimen
    specimen: Optional[Reference] = Field(
        None,
        description="Specimen used for this observation"
    )

    # Device
    device: Optional[Reference] = Field(
        None,
        description="Device used for observation"
    )

    # Reference range
    referenceRange: Optional[List[ObservationReferenceRange]] = Field(
        None,
        description="Provides guide for interpretation"
    )

    # Has member
    hasMember: Optional[List[Reference]] = Field(
        None,
        description="Related resource that belongs to the Observation group"
    )

    # Derived from
    derivedFrom: Optional[List[Reference]] = Field(
        None,
        description="Related measurements the observation is made from"
    )

    # Component
    component: Optional[List[ObservationComponent]] = Field(
        None,
        description="Component results for multi-valued observations"
    )

    class Config:
        schema_extra = {
            "example": {
                "resourceType": "Observation",
                "id": "example",
                "status": "final",
                "category": [
                    {
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "vital-signs",
                            "display": "Vital Signs"
                        }]
                    }
                ],
                "code": {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": "85354-9",
                        "display": "Blood pressure panel"
                    }]
                },
                "subject": {
                    "reference": "Patient/example",
                    "display": "John Smith"
                },
                "effectiveDateTime": "2024-01-15T09:30:00Z",
                "component": [
                    {
                        "code": {
                            "coding": [{
                                "system": "http://loinc.org",
                                "code": "8480-6",
                                "display": "Systolic blood pressure"
                            }]
                        },
                        "valueQuantity": {
                            "value": 120,
                            "unit": "mmHg",
                            "system": "http://unitsofmeasure.org",
                            "code": "mm[Hg]"
                        }
                    },
                    {
                        "code": {
                            "coding": [{
                                "system": "http://loinc.org",
                                "code": "8462-4",
                                "display": "Diastolic blood pressure"
                            }]
                        },
                        "valueQuantity": {
                            "value": 80,
                            "unit": "mmHg",
                            "system": "http://unitsofmeasure.org",
                            "code": "mm[Hg]"
                        }
                    }
                ]
            }
        }


# Update forward references
