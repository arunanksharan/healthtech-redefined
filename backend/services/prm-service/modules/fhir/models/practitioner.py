"""
FHIR R4 Practitioner and PractitionerRole Resources
Healthcare professionals and their roles
"""

from datetime import date
from typing import List, Optional
from pydantic import Field

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


class PractitionerQualification(FHIRResource):
    """Qualifications obtained by the practitioner"""
    identifier: Optional[List[Identifier]] = Field(
        None,
        description="An identifier for this qualification for the practitioner"
    )
    code: CodeableConcept = Field(
        ...,
        description="Coded representation of the qualification"
    )
    period: Optional[Period] = Field(
        None,
        description="Period during which the qualification is valid"
    )
    issuer: Optional[Reference] = Field(
        None,
        description="Organization that regulates and issues the qualification"
    )


class Practitioner(FHIRResource):
    """
    FHIR R4 Practitioner Resource
    A person who is directly or indirectly involved in the provisioning of healthcare.
    """

    resourceType: str = Field("Practitioner", const=True)

    # Identifiers
    identifier: Optional[List[Identifier]] = Field(
        None,
        description="An identifier for the practitioner (e.g., license number, NPI)"
    )

    # Status
    active: Optional[bool] = Field(
        None,
        description="Whether this practitioner's record is in active use"
    )

    # Names
    name: Optional[List[HumanName]] = Field(
        None,
        description="The name(s) associated with the practitioner"
    )

    # Contact information
    telecom: Optional[List[ContactPoint]] = Field(
        None,
        description="Contact details (telephone, email, etc.)"
    )

    # Address
    address: Optional[List[Address]] = Field(
        None,
        description="Address(es) of the practitioner"
    )

    # Demographics
    gender: Optional[AdministrativeGender] = Field(
        None,
        description="male | female | other | unknown"
    )

    birthDate: Optional[date] = Field(
        None,
        description="The date of birth for the practitioner"
    )

    # Photo
    photo: Optional[List[Attachment]] = Field(
        None,
        description="Image of the practitioner"
    )

    # Qualifications
    qualification: Optional[List[PractitionerQualification]] = Field(
        None,
        description="Qualifications obtained by training and certification"
    )

    # Communication
    communication: Optional[List[CodeableConcept]] = Field(
        None,
        description="Languages which may be used to communicate with the practitioner"
    )

    class Config:
        schema_extra = {
            "example": {
                "resourceType": "Practitioner",
                "id": "example",
                "identifier": [
                    {
                        "system": "http://hl7.org/fhir/sid/us-npi",
                        "value": "1234567890"
                    }
                ],
                "active": True,
                "name": [
                    {
                        "use": "official",
                        "family": "Johnson",
                        "given": ["Sarah"],
                        "prefix": ["Dr."]
                    }
                ],
                "telecom": [
                    {
                        "system": "phone",
                        "value": "+1-555-5678",
                        "use": "work"
                    }
                ],
                "gender": "female",
                "qualification": [
                    {
                        "code": {
                            "coding": [{
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0360",
                                "code": "MD",
                                "display": "Doctor of Medicine"
                            }]
                        }
                    }
                ]
            }
        }


class PractitionerRoleAvailableTime(FHIRResource):
    """Times the practitioner is available at this location/organization"""
    daysOfWeek: Optional[List[str]] = Field(
        None,
        description="mon | tue | wed | thu | fri | sat | sun"
    )
    allDay: Optional[bool] = Field(
        None,
        description="Always available? (e.g., 24 hour service)"
    )
    availableStartTime: Optional[str] = Field(
        None,
        description="Opening time of day (ignored if allDay = true)"
    )
    availableEndTime: Optional[str] = Field(
        None,
        description="Closing time of day (ignored if allDay = true)"
    )


class PractitionerRoleNotAvailable(FHIRResource):
    """Times the practitioner is not available"""
    description: str = Field(
        ...,
        description="Reason presented to the user explaining why time not available"
    )
    during: Optional[Period] = Field(
        None,
        description="Service not available from this date"
    )


class PractitionerRole(FHIRResource):
    """
    FHIR R4 PractitionerRole Resource
    A specific set of Roles/Locations/specialties/services that a practitioner may perform at an organization.
    """

    resourceType: str = Field("PractitionerRole", const=True)

    # Identifiers
    identifier: Optional[List[Identifier]] = Field(
        None,
        description="Business identifiers for this role"
    )

    # Status
    active: Optional[bool] = Field(
        None,
        description="Whether this practitioner role record is in active use"
    )

    # Period
    period: Optional[Period] = Field(
        None,
        description="The period during which the practitioner is authorized to perform in these role(s)"
    )

    # References
    practitioner: Optional[Reference] = Field(
        None,
        description="Practitioner that is able to provide the defined services for the organization"
    )

    organization: Optional[Reference] = Field(
        None,
        description="Organization where the roles are available"
    )

    # Role details
    code: Optional[List[CodeableConcept]] = Field(
        None,
        description="Roles which this practitioner may perform"
    )

    specialty: Optional[List[CodeableConcept]] = Field(
        None,
        description="Specific specialty of the practitioner"
    )

    # Locations
    location: Optional[List[Reference]] = Field(
        None,
        description="Locations where the practitioner provides care"
    )

    # Services
    healthcareService: Optional[List[Reference]] = Field(
        None,
        description="Healthcare services provided for this role's Organization/Location(s)"
    )

    # Contact
    telecom: Optional[List[ContactPoint]] = Field(
        None,
        description="Contact details for this role"
    )

    # Availability
    availableTime: Optional[List[PractitionerRoleAvailableTime]] = Field(
        None,
        description="Times the practitioner is available at this location/organization"
    )

    notAvailable: Optional[List[PractitionerRoleNotAvailable]] = Field(
        None,
        description="Times the practitioner is not available"
    )

    # Appointment requirements
    availabilityExceptions: Optional[str] = Field(
        None,
        description="Description of availability exceptions"
    )

    # Endpoints
    endpoint: Optional[List[Reference]] = Field(
        None,
        description="Technical endpoints providing access to services operated for the practitioner with this role"
    )

    class Config:
        schema_extra = {
            "example": {
                "resourceType": "PractitionerRole",
                "id": "example",
                "active": True,
                "practitioner": {
                    "reference": "Practitioner/example",
                    "display": "Dr. Sarah Johnson"
                },
                "organization": {
                    "reference": "Organization/hospital",
                    "display": "General Hospital"
                },
                "code": [
                    {
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/practitioner-role",
                            "code": "doctor",
                            "display": "Doctor"
                        }]
                    }
                ],
                "specialty": [
                    {
                        "coding": [{
                            "system": "http://snomed.info/sct",
                            "code": "394579002",
                            "display": "Cardiology"
                        }]
                    }
                ]
            }
        }


# Update forward references
PractitionerQualification.update_forward_refs()
Practitioner.update_forward_refs()
PractitionerRoleAvailableTime.update_forward_refs()
PractitionerRoleNotAvailable.update_forward_refs()
PractitionerRole.update_forward_refs()
