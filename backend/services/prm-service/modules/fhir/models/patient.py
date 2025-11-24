"""
FHIR R4 Patient Resource
Demographics and other administrative information about an individual receiving care
"""

from datetime import date, datetime
from typing import List, Optional, Union, Literal
from pydantic import Field
from enum import Enum

from .base import (
    FHIRResource,
    Identifier,
    HumanName,
    ContactPoint,
    Address,
    CodeableConcept,
    Reference,
    Period,
    Attachment,
    AdministrativeGender
)


class LinkType(str, Enum):
    """Type of link between this patient resource and another patient resource"""
    REPLACED_BY = "replaced-by"
    REPLACES = "replaces"
    REFER = "refer"
    SEEALSO = "seealso"


class PatientContact(FHIRResource):
    """Contact party for the patient"""
    relationship: Optional[List[CodeableConcept]] = Field(
        None,
        description="The kind of relationship (e.g., spouse, parent, emergency contact)"
    )
    name: Optional[HumanName] = Field(None, description="Name of the contact person")
    telecom: Optional[List[ContactPoint]] = Field(None, description="Contact details")
    address: Optional[Address] = Field(None, description="Address for the contact person")
    gender: Optional[AdministrativeGender] = Field(None, description="male | female | other | unknown")
    organization: Optional[Reference] = Field(
        None,
        description="Organization that is associated with the contact"
    )
    period: Optional[Period] = Field(None, description="Period the contact was in use")


class PatientCommunication(FHIRResource):
    """Language which may be used to communicate with the patient"""
    language: CodeableConcept = Field(
        ...,
        description="Language which may be used to communicate with the patient"
    )
    preferred: Optional[bool] = Field(None, description="Language preference indicator")


class PatientLink(FHIRResource):
    """Link to another patient resource that concerns the same actual person"""
    other: Reference = Field(
        ...,
        description="The other patient or related person resource that the link refers to"
    )
    type: LinkType = Field(..., description="replaced-by | replaces | refer | seealso")


class Patient(FHIRResource):
    """
    FHIR R4 Patient Resource
    Demographics and other administrative information about an individual or animal receiving care or other health-related services.
    """

    resourceType: Literal["Patient"] = "Patient"

    # Identifiers
    identifier: Optional[List[Identifier]] = Field(
        None,
        description="An identifier for this patient (e.g., MRN, SSN, National ID)"
    )

    # Status
    active: Optional[bool] = Field(
        None,
        description="Whether this patient's record is in active use"
    )

    # Names
    name: Optional[List[HumanName]] = Field(
        None,
        description="A name associated with the patient"
    )

    # Contact information
    telecom: Optional[List[ContactPoint]] = Field(
        None,
        description="Contact details (telephone, email, etc.) for the patient"
    )

    # Demographics
    gender: Optional[AdministrativeGender] = Field(
        None,
        description="male | female | other | unknown"
    )

    birthDate: Optional[date] = Field(
        None,
        description="The date of birth for the individual"
    )

    # Deceased indicator
    deceasedBoolean: Optional[bool] = Field(
        None,
        description="Indicates if the patient is deceased"
    )
    deceasedDateTime: Optional[datetime] = Field(
        None,
        description="Date and time of death"
    )

    # Address
    address: Optional[List[Address]] = Field(
        None,
        description="One or more addresses for the patient"
    )

    # Marital status
    maritalStatus: Optional[CodeableConcept] = Field(
        None,
        description="Marital (civil) status of a patient"
    )

    # Multiple birth
    multipleBirthBoolean: Optional[bool] = Field(
        None,
        description="Whether patient is part of a multiple birth"
    )
    multipleBirthInteger: Optional[int] = Field(
        None,
        description="Birth number in the sequence",
        ge=1
    )

    # Photo
    photo: Optional[List[Attachment]] = Field(
        None,
        description="Image of the patient"
    )

    # Contacts
    contact: Optional[List[PatientContact]] = Field(
        None,
        description="Contact party for the patient (e.g., guardian, partner, friend)"
    )

    # Communication
    communication: Optional[List[PatientCommunication]] = Field(
        None,
        description="Languages which may be used to communicate with the patient"
    )

    # Care providers
    generalPractitioner: Optional[List[Reference]] = Field(
        None,
        description="Patient's nominated primary care provider"
    )

    # Managing organization
    managingOrganization: Optional[Reference] = Field(
        None,
        description="Organization that is the custodian of the patient record"
    )

    # Links to other patient resources
    link: Optional[List[PatientLink]] = Field(
        None,
        description="Link to another patient resource that concerns the same actual person"
    )

    class Config:
        schema_extra = {
            "example": {
                "resourceType": "Patient",
                "id": "example",
                "identifier": [
                    {
                        "use": "official",
                        "system": "http://hospital.org/patients",
                        "value": "MRN12345"
                    }
                ],
                "active": True,
                "name": [
                    {
                        "use": "official",
                        "family": "Smith",
                        "given": ["John", "Michael"]
                    }
                ],
                "telecom": [
                    {
                        "system": "phone",
                        "value": "+1-555-1234",
                        "use": "mobile"
                    }
                ],
                "gender": "male",
                "birthDate": "1974-12-25",
                "address": [
                    {
                        "use": "home",
                        "line": ["123 Main Street"],
                        "city": "Springfield",
                        "state": "IL",
                        "postalCode": "62701",
                        "country": "US"
                    }
                ]
            }
        }


