"""
FHIR R4 Organization Resource
Formally or informally recognized grouping of people or organizations
"""

from typing import List, Optional
from pydantic import Field

from .base import (
    FHIRResource,
    Identifier,
    ContactPoint,
    Address,
    CodeableConcept,
    Reference,
    HumanName
)


class OrganizationContact(FHIRResource):
    """Contact for the organization for a certain purpose"""
    purpose: Optional[CodeableConcept] = Field(
        None,
        description="The type of contact (e.g., administrative, billing)"
    )
    name: Optional[HumanName] = Field(
        None,
        description="Name of the contact person"
    )
    telecom: Optional[List[ContactPoint]] = Field(
        None,
        description="Contact details (telephone, email, etc.)"
    )
    address: Optional[Address] = Field(
        None,
        description="Address for the contact"
    )


class Organization(FHIRResource):
    """
    FHIR R4 Organization Resource
    A formally or informally recognized grouping of people or organizations formed for the purpose of achieving some form of collective action.
    """

    resourceType: str = Field("Organization", const=True)

    # Identifiers
    identifier: Optional[List[Identifier]] = Field(
        None,
        description="Identifies this organization across multiple systems"
    )

    # Status
    active: Optional[bool] = Field(
        None,
        description="Whether the organization's record is still in active use"
    )

    # Type
    type: Optional[List[CodeableConcept]] = Field(
        None,
        description="Kind of organization (e.g., Healthcare Provider, Hospital Department)"
    )

    # Name
    name: Optional[str] = Field(
        None,
        description="Name used for the organization"
    )

    # Alias
    alias: Optional[List[str]] = Field(
        None,
        description="A list of alternate names that the organization is known as"
    )

    # Contact information
    telecom: Optional[List[ContactPoint]] = Field(
        None,
        description="Contact details for the organization"
    )

    # Address
    address: Optional[List[Address]] = Field(
        None,
        description="An address for the organization"
    )

    # Hierarchy
    partOf: Optional[Reference] = Field(
        None,
        description="The organization of which this organization forms a part"
    )

    # Contact
    contact: Optional[List[OrganizationContact]] = Field(
        None,
        description="Contact for the organization for a certain purpose"
    )

    # Endpoints
    endpoint: Optional[List[Reference]] = Field(
        None,
        description="Technical endpoints providing access to services operated for the organization"
    )

    class Config:
        schema_extra = {
            "example": {
                "resourceType": "Organization",
                "id": "example",
                "identifier": [
                    {
                        "system": "http://hospital.org/organizations",
                        "value": "ORG-001"
                    }
                ],
                "active": True,
                "type": [
                    {
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/organization-type",
                            "code": "prov",
                            "display": "Healthcare Provider"
                        }]
                    }
                ],
                "name": "General Hospital",
                "telecom": [
                    {
                        "system": "phone",
                        "value": "+1-555-0000",
                        "use": "work"
                    }
                ],
                "address": [
                    {
                        "use": "work",
                        "line": ["456 Hospital Drive"],
                        "city": "Springfield",
                        "state": "IL",
                        "postalCode": "62702",
                        "country": "US"
                    }
                ]
            }
        }


# Update forward references
OrganizationContact.update_forward_refs()
Organization.update_forward_refs()
