"""
FHIR R4 AllergyIntolerance Resource
Risk of harmful or undesirable physiological response unique to an individual
"""

from datetime import datetime
from typing import List, Optional, Literal
from pydantic import Field
from enum import Enum

from .base import (
    FHIRResource,
    Identifier,
    CodeableConcept,
    Reference,
    Annotation,
    Period
)


class AllergyIntoleranceType(str, Enum):
    """Type of allergy or intolerance"""
    ALLERGY = "allergy"
    INTOLERANCE = "intolerance"


class AllergyIntoleranceCategory(str, Enum):
    """Category of the identified substance"""
    FOOD = "food"
    MEDICATION = "medication"
    ENVIRONMENT = "environment"
    BIOLOGIC = "biologic"


class AllergyIntoleranceCriticality(str, Enum):
    """Estimate of the potential clinical harm"""
    LOW = "low"
    HIGH = "high"
    UNABLE_TO_ASSESS = "unable-to-assess"


class AllergyIntoleranceSeverity(str, Enum):
    """Clinical assessment of the severity of a reaction event"""
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class AllergyIntoleranceReaction(FHIRResource):
    """Adverse reaction events linked to exposure to substance"""

    substance: Optional[CodeableConcept] = Field(
        None,
        description="Specific substance considered responsible"
    )
    manifestation: List[CodeableConcept] = Field(
        ...,
        description="Clinical symptoms/signs associated with the Event"
    )
    description: Optional[str] = Field(
        None,
        description="Description of the event"
    )
    onset: Optional[datetime] = Field(
        None,
        description="Date(/time) when manifestations showed"
    )
    severity: Optional[AllergyIntoleranceSeverity] = Field(
        None,
        description="mild | moderate | severe"
    )
    exposureRoute: Optional[CodeableConcept] = Field(
        None,
        description="How the subject was exposed"
    )
    note: Optional[List[Annotation]] = Field(
        None,
        description="Text about event"
    )


class AllergyIntolerance(FHIRResource):
    """
    FHIR R4 AllergyIntolerance Resource
    Risk of harmful or undesirable physiological response unique to an individual.
    """

    resourceType: Literal["AllergyIntolerance"] = "AllergyIntolerance"

    identifier: Optional[List[Identifier]] = Field(
        None,
        description="External ids for this item"
    )
    clinicalStatus: Optional[CodeableConcept] = Field(
        None,
        description="active | inactive | resolved"
    )
    verificationStatus: Optional[CodeableConcept] = Field(
        None,
        description="unconfirmed | confirmed | refuted | entered-in-error"
    )
    type: Optional[AllergyIntoleranceType] = Field(
        None,
        description="allergy | intolerance"
    )
    category: Optional[List[AllergyIntoleranceCategory]] = Field(
        None,
        description="food | medication | environment | biologic"
    )
    criticality: Optional[AllergyIntoleranceCriticality] = Field(
        None,
        description="low | high | unable-to-assess"
    )
    code: Optional[CodeableConcept] = Field(
        None,
        description="Code that identifies the allergy or intolerance"
    )
    patient: Reference = Field(
        ...,
        description="Who the sensitivity is for"
    )
    encounter: Optional[Reference] = Field(
        None,
        description="Encounter when the allergy was asserted"
    )
    onsetDateTime: Optional[datetime] = Field(
        None,
        description="When allergy or intolerance was identified"
    )
    onsetAge: Optional[dict] = Field(
        None,
        description="When allergy or intolerance was identified"
    )
    onsetPeriod: Optional[Period] = Field(
        None,
        description="When allergy or intolerance was identified"
    )
    onsetRange: Optional[dict] = Field(
        None,
        description="When allergy or intolerance was identified"
    )
    onsetString: Optional[str] = Field(
        None,
        description="When allergy or intolerance was identified"
    )
    recordedDate: Optional[datetime] = Field(
        None,
        description="Date first version was recorded"
    )
    recorder: Optional[Reference] = Field(
        None,
        description="Who recorded the sensitivity"
    )
    asserter: Optional[Reference] = Field(
        None,
        description="Source of the information"
    )
    lastOccurrence: Optional[datetime] = Field(
        None,
        description="Date(/time) of last known occurrence"
    )
    note: Optional[List[Annotation]] = Field(
        None,
        description="Additional text"
    )
    reaction: Optional[List[AllergyIntoleranceReaction]] = Field(
        None,
        description="Adverse Reaction Events"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "resourceType": "AllergyIntolerance",
                "id": "example",
                "clinicalStatus": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
                        "code": "active"
                    }]
                },
                "verificationStatus": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification",
                        "code": "confirmed"
                    }]
                },
                "type": "allergy",
                "category": ["medication"],
                "criticality": "high",
                "code": {
                    "coding": [{
                        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                        "code": "7980",
                        "display": "Penicillin G"
                    }]
                },
                "patient": {
                    "reference": "Patient/example"
                },
                "reaction": [{
                    "manifestation": [{
                        "coding": [{
                            "system": "http://snomed.info/sct",
                            "code": "271807003",
                            "display": "Rash"
                        }]
                    }],
                    "severity": "severe"
                }]
            }
        }
