"""
FHIR R4 Encounter Resource
An interaction during which services are provided to the patient
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
    Period,
    Coding
)


class EncounterStatus(str, Enum):
    """Current state of the encounter"""
    PLANNED = "planned"
    ARRIVED = "arrived"
    TRIAGED = "triaged"
    IN_PROGRESS = "in-progress"
    ONLEAVE = "onleave"
    FINISHED = "finished"
    CANCELLED = "cancelled"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"


class EncounterStatusHistory(FHIRResource):
    """List of past encounter statuses"""
    status: EncounterStatus = Field(
        ...,
        description="planned | arrived | triaged | in-progress | onleave | finished | cancelled | entered-in-error | unknown"
    )
    period: Period = Field(
        ...,
        description="The time that the status applied"
    )


class EncounterParticipant(FHIRResource):
    """List of participants involved in the encounter"""
    type: Optional[List[CodeableConcept]] = Field(
        None,
        description="Role of participant in encounter"
    )
    period: Optional[Period] = Field(
        None,
        description="Period of time during the encounter that the participant participated"
    )
    individual: Optional[Reference] = Field(
        None,
        description="Person, device, or service participating in the encounter"
    )


class EncounterDiagnosis(FHIRResource):
    """List of diagnoses relevant to this encounter"""
    condition: Reference = Field(
        ...,
        description="The diagnosis or procedure relevant to the encounter"
    )
    use: Optional[CodeableConcept] = Field(
        None,
        description="Role that this diagnosis has within the encounter"
    )
    rank: Optional[int] = Field(
        None,
        description="Ranking of the diagnosis (for each role type)",
        ge=1
    )


class EncounterHospitalization(FHIRResource):
    """Details about the admission to a healthcare service"""
    preAdmissionIdentifier: Optional[Identifier] = Field(
        None,
        description="Pre-admission identifier"
    )
    origin: Optional[Reference] = Field(
        None,
        description="The location/organization from which the patient came before admission"
    )
    admitSource: Optional[CodeableConcept] = Field(
        None,
        description="From where patient was admitted"
    )
    reAdmission: Optional[CodeableConcept] = Field(
        None,
        description="Indicates that patient is being re-admitted"
    )
    dietPreference: Optional[List[CodeableConcept]] = Field(
        None,
        description="Diet preferences reported by the patient"
    )
    specialCourtesy: Optional[List[CodeableConcept]] = Field(
        None,
        description="Special courtesies"
    )
    specialArrangement: Optional[List[CodeableConcept]] = Field(
        None,
        description="Wheelchair, translator, stretcher, etc."
    )
    destination: Optional[Reference] = Field(
        None,
        description="Location/organization to which the patient is discharged"
    )
    dischargeDisposition: Optional[CodeableConcept] = Field(
        None,
        description="Category or kind of location after discharge"
    )


class EncounterLocation(FHIRResource):
    """List of locations where the patient has been"""
    location: Reference = Field(
        ...,
        description="Location the encounter takes place"
    )
    status: Optional[str] = Field(
        None,
        description="planned | active | reserved | completed"
    )
    physicalType: Optional[CodeableConcept] = Field(
        None,
        description="The physical type of the location"
    )
    period: Optional[Period] = Field(
        None,
        description="Time period during which the patient was present at the location"
    )


class EncounterClassHistory(FHIRResource):
    """List of past encounter classes"""
    class_: Coding = Field(
        ...,
        alias="class",
        description="inpatient | outpatient | ambulatory | emergency"
    )
    period: Period = Field(
        ...,
        description="The time that the class applied"
    )


class Encounter(FHIRResource):
    """
    FHIR R4 Encounter Resource
    An interaction between a patient and healthcare provider(s) for the purpose of providing healthcare service(s) or assessing the health status of a patient.
    """

    resourceType: Literal["Encounter"] = "Encounter"

    # Identifiers
    identifier: Optional[List[Identifier]] = Field(
        None,
        description="Identifier(s) by which this encounter is known"
    )

    # Status
    status: EncounterStatus = Field(
        ...,
        description="planned | arrived | triaged | in-progress | onleave | finished | cancelled | entered-in-error | unknown"
    )

    statusHistory: Optional[List[EncounterStatusHistory]] = Field(
        None,
        description="List of past encounter statuses"
    )

    # Class
    class_: Coding = Field(
        ...,
        alias="class",
        description="Classification of patient encounter (inpatient, outpatient, ambulatory, emergency, etc.)"
    )

    classHistory: Optional[List[EncounterClassHistory]] = Field(
        None,
        description="List of past encounter classes"
    )

    # Type
    type: Optional[List[CodeableConcept]] = Field(
        None,
        description="Specific type of encounter"
    )

    # Service type
    serviceType: Optional[CodeableConcept] = Field(
        None,
        description="Specific type of service"
    )

    # Priority
    priority: Optional[CodeableConcept] = Field(
        None,
        description="Indicates the urgency of the encounter"
    )

    # Subject (patient)
    subject: Optional[Reference] = Field(
        None,
        description="The patient present at the encounter"
    )

    # Episode of care
    episodeOfCare: Optional[List[Reference]] = Field(
        None,
        description="Episode(s) of care that this encounter should be recorded against"
    )

    # Based on
    basedOn: Optional[List[Reference]] = Field(
        None,
        description="The ServiceRequest that initiated this encounter"
    )

    # Participants
    participant: Optional[List[EncounterParticipant]] = Field(
        None,
        description="List of participants involved in the encounter"
    )

    # Appointment
    appointment: Optional[List[Reference]] = Field(
        None,
        description="The appointment that scheduled this encounter"
    )

    # Period
    period: Optional[Period] = Field(
        None,
        description="The start and end time of the encounter"
    )

    # Length
    length: Optional['Quantity'] = Field(
        None,
        description="Quantity of time the encounter lasted"
    )

    # Reason
    reasonCode: Optional[List[CodeableConcept]] = Field(
        None,
        description="Coded reason the encounter takes place"
    )

    reasonReference: Optional[List[Reference]] = Field(
        None,
        description="Reason the encounter takes place (reference)"
    )

    # Diagnosis
    diagnosis: Optional[List[EncounterDiagnosis]] = Field(
        None,
        description="The list of diagnosis relevant to this encounter"
    )

    # Account
    account: Optional[List[Reference]] = Field(
        None,
        description="The set of accounts that may be used for billing"
    )

    # Hospitalization
    hospitalization: Optional[EncounterHospitalization] = Field(
        None,
        description="Details about the admission to a healthcare service"
    )

    # Location
    location: Optional[List[EncounterLocation]] = Field(
        None,
        description="List of locations where the patient has been"
    )

    # Service provider
    serviceProvider: Optional[Reference] = Field(
        None,
        description="The organization responsible for this encounter"
    )

    # Part of
    partOf: Optional[Reference] = Field(
        None,
        description="Another Encounter this encounter is part of"
    )

    class Config:
        schema_extra = {
            "example": {
                "resourceType": "Encounter",
                "id": "example",
                "status": "in-progress",
                "class": {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                    "code": "AMB",
                    "display": "ambulatory"
                },
                "type": [
                    {
                        "coding": [{
                            "system": "http://snomed.info/sct",
                            "code": "270427003",
                            "display": "Patient-initiated encounter"
                        }]
                    }
                ],
                "subject": {
                    "reference": "Patient/example",
                    "display": "John Smith"
                },
                "participant": [
                    {
                        "individual": {
                            "reference": "Practitioner/example",
                            "display": "Dr. Sarah Johnson"
                        }
                    }
                ],
                "period": {
                    "start": "2024-01-15T09:00:00Z"
                }
            }
        }


# Import Quantity after defining Encounter to avoid circular import
from .base import Quantity

# Update forward references
