"""
FHIR R4 Condition Resource
A clinical condition, problem, diagnosis, or other event, situation, issue, or clinical concept
"""

from datetime import datetime, date
from typing import List, Optional
from pydantic import Field
from enum import Enum

from .base import (
    FHIRResource,
    Identifier,
    CodeableConcept,
    Reference,
    Period,
    Range,
    Annotation
)


class ConditionClinicalStatus(str, Enum):
    """Clinical status of the condition"""
    ACTIVE = "active"
    RECURRENCE = "recurrence"
    RELAPSE = "relapse"
    INACTIVE = "inactive"
    REMISSION = "remission"
    RESOLVED = "resolved"


class ConditionVerificationStatus(str, Enum):
    """Verification status of the condition"""
    UNCONFIRMED = "unconfirmed"
    PROVISIONAL = "provisional"
    DIFFERENTIAL = "differential"
    CONFIRMED = "confirmed"
    REFUTED = "refuted"
    ENTERED_IN_ERROR = "entered-in-error"


class ConditionStage(FHIRResource):
    """Stage/grade of condition"""
    summary: Optional[CodeableConcept] = Field(
        None,
        description="Simple summary (disease specific)"
    )
    assessment: Optional[List[Reference]] = Field(
        None,
        description="Formal record of assessment"
    )
    type: Optional[CodeableConcept] = Field(
        None,
        description="Kind of staging"
    )


class ConditionEvidence(FHIRResource):
    """Supporting evidence for the condition"""
    code: Optional[List[CodeableConcept]] = Field(
        None,
        description="Manifestation/symptom"
    )
    detail: Optional[List[Reference]] = Field(
        None,
        description="Supporting information found elsewhere"
    )


class Condition(FHIRResource):
    """
    FHIR R4 Condition Resource
    A clinical condition, problem, diagnosis, or other event, situation, issue, or clinical concept that has risen to a level of concern.
    """

    resourceType: str = Field("Condition", const=True)

    # Identifiers
    identifier: Optional[List[Identifier]] = Field(
        None,
        description="External Ids for this condition"
    )

    # Clinical status
    clinicalStatus: Optional[CodeableConcept] = Field(
        None,
        description="active | recurrence | relapse | inactive | remission | resolved"
    )

    # Verification status
    verificationStatus: Optional[CodeableConcept] = Field(
        None,
        description="unconfirmed | provisional | differential | confirmed | refuted | entered-in-error"
    )

    # Category
    category: Optional[List[CodeableConcept]] = Field(
        None,
        description="problem-list-item | encounter-diagnosis | health-concern"
    )

    # Severity
    severity: Optional[CodeableConcept] = Field(
        None,
        description="Subjective severity of condition"
    )

    # Code
    code: Optional[CodeableConcept] = Field(
        None,
        description="Identification of the condition, problem or diagnosis"
    )

    # Body site
    bodySite: Optional[List[CodeableConcept]] = Field(
        None,
        description="Anatomical location, if relevant"
    )

    # Subject
    subject: Reference = Field(
        ...,
        description="Who has the condition?"
    )

    # Encounter
    encounter: Optional[Reference] = Field(
        None,
        description="Encounter created as part of"
    )

    # Onset
    onsetDateTime: Optional[datetime] = Field(
        None,
        description="Estimated or actual date, date-time, or age"
    )
    onsetAge: Optional[dict] = Field(
        None,
        description="Estimated or actual age"
    )
    onsetPeriod: Optional[Period] = Field(
        None,
        description="Estimated or actual period"
    )
    onsetRange: Optional[Range] = Field(
        None,
        description="Estimated or actual range"
    )
    onsetString: Optional[str] = Field(
        None,
        description="Estimated or actual date (string)"
    )

    # Abatement
    abatementDateTime: Optional[datetime] = Field(
        None,
        description="When in resolution/remission"
    )
    abatementAge: Optional[dict] = Field(
        None,
        description="When in resolution/remission (age)"
    )
    abatementPeriod: Optional[Period] = Field(
        None,
        description="When in resolution/remission (period)"
    )
    abatementRange: Optional[Range] = Field(
        None,
        description="When in resolution/remission (range)"
    )
    abatementString: Optional[str] = Field(
        None,
        description="When in resolution/remission (string)"
    )

    # Recorded date
    recordedDate: Optional[datetime] = Field(
        None,
        description="Date record was first recorded"
    )

    # Recorder
    recorder: Optional[Reference] = Field(
        None,
        description="Who recorded the condition"
    )

    # Asserter
    asserter: Optional[Reference] = Field(
        None,
        description="Person who asserts this condition"
    )

    # Stage
    stage: Optional[List[ConditionStage]] = Field(
        None,
        description="Stage/grade, usually assessed formally"
    )

    # Evidence
    evidence: Optional[List[ConditionEvidence]] = Field(
        None,
        description="Supporting evidence"
    )

    # Note
    note: Optional[List[Annotation]] = Field(
        None,
        description="Additional information about the Condition"
    )

    class Config:
        schema_extra = {
            "example": {
                "resourceType": "Condition",
                "id": "example",
                "clinicalStatus": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": "active",
                        "display": "Active"
                    }]
                },
                "verificationStatus": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                        "code": "confirmed",
                        "display": "Confirmed"
                    }]
                },
                "category": [
                    {
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                            "code": "encounter-diagnosis",
                            "display": "Encounter Diagnosis"
                        }]
                    }
                ],
                "severity": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "24484000",
                        "display": "Severe"
                    }]
                },
                "code": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "38341003",
                        "display": "Hypertensive disorder"
                    }],
                    "text": "Hypertension"
                },
                "subject": {
                    "reference": "Patient/example",
                    "display": "John Smith"
                },
                "onsetDateTime": "2020-05-15",
                "recordedDate": "2020-05-20T10:30:00Z"
            }
        }


# Update forward references
ConditionStage.update_forward_refs()
ConditionEvidence.update_forward_refs()
Condition.update_forward_refs()
