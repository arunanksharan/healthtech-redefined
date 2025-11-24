"""
FHIR R4 MedicationRequest Resource
An order or request for medication supply and administration instructions
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
    Quantity
)


class MedicationRequestStatus(str, Enum):
    """Status of the medication request"""
    ACTIVE = "active"
    ON_HOLD = "on-hold"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    ENTERED_IN_ERROR = "entered-in-error"
    STOPPED = "stopped"
    DRAFT = "draft"
    UNKNOWN = "unknown"


class MedicationRequestIntent(str, Enum):
    """Intent of the medication request"""
    PROPOSAL = "proposal"
    PLAN = "plan"
    ORDER = "order"
    ORIGINAL_ORDER = "original-order"
    REFLEX_ORDER = "reflex-order"
    FILLER_ORDER = "filler-order"
    INSTANCE_ORDER = "instance-order"
    OPTION = "option"


class MedicationRequestPriority(str, Enum):
    """Priority of the medication request"""
    ROUTINE = "routine"
    URGENT = "urgent"
    ASAP = "asap"
    STAT = "stat"


class MedicationRequestDispenseRequest(FHIRResource):
    """Medication supply authorization"""

    initialFill: Optional[dict] = Field(None, description="First fill details")
    dispenseInterval: Optional[dict] = Field(None, description="Minimum period between dispenses")
    validityPeriod: Optional[dict] = Field(None, description="Time period authorized for")
    numberOfRepeatsAllowed: Optional[int] = Field(None, description="Refills authorized", ge=0)
    quantity: Optional[Quantity] = Field(None, description="Amount per dispense")
    expectedSupplyDuration: Optional[dict] = Field(None, description="Days supply per dispense")
    performer: Optional[Reference] = Field(None, description="Intended dispenser")


class MedicationRequestSubstitution(FHIRResource):
    """Restrictions on medication substitution"""

    allowedBoolean: Optional[bool] = Field(None, description="Whether substitution is allowed")
    allowedCodeableConcept: Optional[CodeableConcept] = Field(None, description="Whether substitution is allowed")
    reason: Optional[CodeableConcept] = Field(None, description="Why substitution should/should not be made")


class DosageInstruction(FHIRResource):
    """How medication should be taken"""

    sequence: Optional[int] = Field(None, description="Order of dosage instructions")
    text: Optional[str] = Field(None, description="Free text dosage instructions")
    additionalInstruction: Optional[List[CodeableConcept]] = Field(
        None,
        description="Supplemental instructions"
    )
    patientInstruction: Optional[str] = Field(None, description="Patient oriented instructions")
    timing: Optional[dict] = Field(None, description="When medication should be administered")
    asNeededBoolean: Optional[bool] = Field(None, description="Take as needed")
    asNeededCodeableConcept: Optional[CodeableConcept] = Field(None, description="Take as needed for x")
    site: Optional[CodeableConcept] = Field(None, description="Body site to administer to")
    route: Optional[CodeableConcept] = Field(None, description="How drug should enter body")
    method: Optional[CodeableConcept] = Field(None, description="Technique for administering")
    doseAndRate: Optional[List[dict]] = Field(None, description="Amount of medication")
    maxDosePerPeriod: Optional[dict] = Field(None, description="Upper limit per unit of time")
    maxDosePerAdministration: Optional[Quantity] = Field(None, description="Upper limit per administration")
    maxDosePerLifetime: Optional[Quantity] = Field(None, description="Upper limit per lifetime")


class MedicationRequest(FHIRResource):
    """
    FHIR R4 MedicationRequest Resource
    An order or request for medication supply and administration instructions.
    """

    resourceType: Literal["MedicationRequest"] = "MedicationRequest"

    identifier: Optional[List[Identifier]] = Field(
        None,
        description="External ids"
    )
    status: MedicationRequestStatus = Field(
        ...,
        description="active | on-hold | cancelled | completed | entered-in-error | stopped | draft | unknown"
    )
    statusReason: Optional[CodeableConcept] = Field(
        None,
        description="Reason for current status"
    )
    intent: MedicationRequestIntent = Field(
        ...,
        description="proposal | plan | order | original-order | reflex-order | filler-order | instance-order | option"
    )
    category: Optional[List[CodeableConcept]] = Field(
        None,
        description="Type of medication usage"
    )
    priority: Optional[MedicationRequestPriority] = Field(
        None,
        description="routine | urgent | asap | stat"
    )
    doNotPerform: Optional[bool] = Field(
        None,
        description="True if prohibiting action"
    )
    reportedBoolean: Optional[bool] = Field(
        None,
        description="Reported rather than primary record"
    )
    reportedReference: Optional[Reference] = Field(
        None,
        description="Reported rather than primary record"
    )
    medicationCodeableConcept: Optional[CodeableConcept] = Field(
        None,
        description="Medication to be taken"
    )
    medicationReference: Optional[Reference] = Field(
        None,
        description="Medication to be taken"
    )
    subject: Reference = Field(
        ...,
        description="Who medication is for"
    )
    encounter: Optional[Reference] = Field(
        None,
        description="Encounter created as part of"
    )
    supportingInformation: Optional[List[Reference]] = Field(
        None,
        description="Information to support ordering"
    )
    authoredOn: Optional[datetime] = Field(
        None,
        description="When request was initially authored"
    )
    requester: Optional[Reference] = Field(
        None,
        description="Who/What requested the Request"
    )
    performer: Optional[Reference] = Field(
        None,
        description="Intended performer of administration"
    )
    performerType: Optional[CodeableConcept] = Field(
        None,
        description="Desired kind of performer"
    )
    recorder: Optional[Reference] = Field(
        None,
        description="Person who entered the request"
    )
    reasonCode: Optional[List[CodeableConcept]] = Field(
        None,
        description="Reason for ordering"
    )
    reasonReference: Optional[List[Reference]] = Field(
        None,
        description="Condition or observation supporting prescription"
    )
    instantiatesCanonical: Optional[List[str]] = Field(
        None,
        description="Instantiates FHIR protocol"
    )
    instantiatesUri: Optional[List[str]] = Field(
        None,
        description="Instantiates external protocol"
    )
    basedOn: Optional[List[Reference]] = Field(
        None,
        description="What request fulfills"
    )
    groupIdentifier: Optional[Identifier] = Field(
        None,
        description="Composite request this is part of"
    )
    courseOfTherapyType: Optional[CodeableConcept] = Field(
        None,
        description="Overall pattern of administration"
    )
    insurance: Optional[List[Reference]] = Field(
        None,
        description="Associated insurance coverage"
    )
    note: Optional[List[Annotation]] = Field(
        None,
        description="Information about the prescription"
    )
    dosageInstruction: Optional[List[DosageInstruction]] = Field(
        None,
        description="How medication should be taken"
    )
    dispenseRequest: Optional[MedicationRequestDispenseRequest] = Field(
        None,
        description="Medication supply authorization"
    )
    substitution: Optional[MedicationRequestSubstitution] = Field(
        None,
        description="Restrictions on substitution"
    )
    priorPrescription: Optional[Reference] = Field(
        None,
        description="Order being replaced"
    )
    detectedIssue: Optional[List[Reference]] = Field(
        None,
        description="Clinical Issue with action"
    )
    eventHistory: Optional[List[Reference]] = Field(
        None,
        description="Lifecycle events"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "resourceType": "MedicationRequest",
                "id": "example",
                "status": "active",
                "intent": "order",
                "medicationCodeableConcept": {
                    "coding": [{
                        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                        "code": "582620",
                        "display": "Nizatidine 15 MG/ML Oral Solution"
                    }]
                },
                "subject": {
                    "reference": "Patient/example"
                },
                "authoredOn": "2024-01-15T10:30:00Z",
                "requester": {
                    "reference": "Practitioner/example"
                },
                "dosageInstruction": [{
                    "sequence": 1,
                    "text": "Take 15 mL by mouth twice daily",
                    "timing": {
                        "repeat": {
                            "frequency": 2,
                            "period": 1,
                            "periodUnit": "d"
                        }
                    },
                    "route": {
                        "coding": [{
                            "system": "http://snomed.info/sct",
                            "code": "26643006",
                            "display": "Oral route"
                        }]
                    }
                }],
                "dispenseRequest": {
                    "numberOfRepeatsAllowed": 3,
                    "quantity": {
                        "value": 480,
                        "unit": "mL",
                        "system": "http://unitsofmeasure.org",
                        "code": "mL"
                    }
                }
            }
        }
