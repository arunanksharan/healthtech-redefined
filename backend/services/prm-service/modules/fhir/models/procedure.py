"""
FHIR R4 Procedure Resource
An action that is or was performed on or for a patient
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
    Range,
    Annotation
)


class ProcedureStatus(str, Enum):
    """Status of the procedure"""
    PREPARATION = "preparation"
    IN_PROGRESS = "in-progress"
    NOT_DONE = "not-done"
    ON_HOLD = "on-hold"
    STOPPED = "stopped"
    COMPLETED = "completed"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"


class ProcedurePerformer(FHIRResource):
    """The people who performed the procedure"""
    function: Optional[CodeableConcept] = Field(
        None,
        description="Type of performance"
    )
    actor: Reference = Field(
        ...,
        description="The reference to the practitioner"
    )
    onBehalfOf: Optional[Reference] = Field(
        None,
        description="Organization the device or practitioner was acting for"
    )


class ProcedureFocalDevice(FHIRResource):
    """Device changed in procedure"""
    action: Optional[CodeableConcept] = Field(
        None,
        description="Kind of change to device"
    )
    manipulated: Reference = Field(
        ...,
        description="Device that was changed"
    )


class Procedure(FHIRResource):
    """
    FHIR R4 Procedure Resource
    An action that is or was performed on or for a patient. This can be a physical intervention like an operation,
    or less invasive like long term services, counseling, or hypnotherapy.
    """

    resourceType: Literal["Procedure"] = "Procedure"

    # Identifiers
    identifier: Optional[List[Identifier]] = Field(
        None,
        description="External Identifiers for this procedure"
    )

    # Instantiates
    instantiatesCanonical: Optional[List[str]] = Field(
        None,
        description="Instantiates FHIR protocol or definition"
    )
    instantiatesUri: Optional[List[str]] = Field(
        None,
        description="Instantiates external protocol or definition"
    )

    # Based on
    basedOn: Optional[List[Reference]] = Field(
        None,
        description="A request for this procedure"
    )

    # Part of
    partOf: Optional[List[Reference]] = Field(
        None,
        description="Part of referenced event"
    )

    # Status
    status: ProcedureStatus = Field(
        ...,
        description="preparation | in-progress | not-done | on-hold | stopped | completed | entered-in-error | unknown"
    )

    # Status reason
    statusReason: Optional[CodeableConcept] = Field(
        None,
        description="Reason for current status"
    )

    # Category
    category: Optional[CodeableConcept] = Field(
        None,
        description="Classification of the procedure"
    )

    # Code
    code: Optional[CodeableConcept] = Field(
        None,
        description="Identification of the procedure"
    )

    # Subject
    subject: Reference = Field(
        ...,
        description="Who the procedure was performed on"
    )

    # Encounter
    encounter: Optional[Reference] = Field(
        None,
        description="Encounter created as part of"
    )

    # Performed
    performedDateTime: Optional[datetime] = Field(
        None,
        description="When the procedure was performed"
    )
    performedPeriod: Optional[Period] = Field(
        None,
        description="When the procedure was performed"
    )
    performedString: Optional[str] = Field(
        None,
        description="When the procedure was performed"
    )
    performedAge: Optional[dict] = Field(
        None,
        description="When the procedure was performed (age)"
    )
    performedRange: Optional[Range] = Field(
        None,
        description="When the procedure was performed"
    )

    # Recorder
    recorder: Optional[Reference] = Field(
        None,
        description="Who recorded the procedure"
    )

    # Asserter
    asserter: Optional[Reference] = Field(
        None,
        description="Person who asserts this procedure"
    )

    # Performers
    performer: Optional[List[ProcedurePerformer]] = Field(
        None,
        description="The people who performed the procedure"
    )

    # Location
    location: Optional[Reference] = Field(
        None,
        description="Where the procedure happened"
    )

    # Reason code
    reasonCode: Optional[List[CodeableConcept]] = Field(
        None,
        description="Coded reason procedure performed"
    )

    # Reason reference
    reasonReference: Optional[List[Reference]] = Field(
        None,
        description="The justification that the procedure was performed"
    )

    # Body site
    bodySite: Optional[List[CodeableConcept]] = Field(
        None,
        description="Target body sites"
    )

    # Outcome
    outcome: Optional[CodeableConcept] = Field(
        None,
        description="The result of procedure"
    )

    # Report
    report: Optional[List[Reference]] = Field(
        None,
        description="Any report resulting from the procedure"
    )

    # Complication
    complication: Optional[List[CodeableConcept]] = Field(
        None,
        description="Complication following the procedure"
    )

    # Complication detail
    complicationDetail: Optional[List[Reference]] = Field(
        None,
        description="A condition that is a result of the procedure"
    )

    # Follow up
    followUp: Optional[List[CodeableConcept]] = Field(
        None,
        description="Instructions for follow up"
    )

    # Note
    note: Optional[List[Annotation]] = Field(
        None,
        description="Additional information about the procedure"
    )

    # Focal device
    focalDevice: Optional[List[ProcedureFocalDevice]] = Field(
        None,
        description="Manipulated, implanted, or removed device"
    )

    # Used reference
    usedReference: Optional[List[Reference]] = Field(
        None,
        description="Items used during procedure"
    )

    # Used code
    usedCode: Optional[List[CodeableConcept]] = Field(
        None,
        description="Coded items used during the procedure"
    )

    class Config:
        schema_extra = {
            "example": {
                "resourceType": "Procedure",
                "id": "example",
                "status": "completed",
                "category": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "387713003",
                        "display": "Surgical procedure"
                    }]
                },
                "code": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "80146002",
                        "display": "Appendectomy"
                    }],
                    "text": "Appendectomy"
                },
                "subject": {
                    "reference": "Patient/example"
                },
                "encounter": {
                    "reference": "Encounter/example"
                },
                "performedDateTime": "2024-01-15T14:30:00Z",
                "performer": [{
                    "actor": {
                        "reference": "Practitioner/example",
                        "display": "Dr. Sarah Johnson"
                    }
                }],
                "location": {
                    "reference": "Location/OR1",
                    "display": "Operating Room 1"
                },
                "outcome": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "385669000",
                        "display": "Successful"
                    }]
                }
            }
        }


# Update forward references
