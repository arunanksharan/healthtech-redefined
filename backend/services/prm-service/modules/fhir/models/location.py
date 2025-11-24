"""
FHIR R4 Location Resource
Details and position information for a physical place
"""

from typing import List, Optional, Literal
from pydantic import Field
from enum import Enum

from .base import (
    FHIRResource,
    Identifier,
    ContactPoint,
    Address,
    CodeableConcept,
    Coding,
    Reference,
    Extension
)


class LocationStatus(str, Enum):
    """Status of the location"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"


class LocationMode(str, Enum):
    """Mode of the location"""
    INSTANCE = "instance"  # The Location resource represents a specific instance
    KIND = "kind"  # The Location represents a class of locations


class LocationPosition(FHIRResource):
    """The absolute geographic location"""
    longitude: float = Field(..., description="Longitude with WGS84 datum")
    latitude: float = Field(..., description="Latitude with WGS84 datum")
    altitude: Optional[float] = Field(None, description="Altitude with WGS84 datum")


class LocationHoursOfOperation(FHIRResource):
    """What days/times during a week is this location usually open"""
    daysOfWeek: Optional[List[str]] = Field(
        None,
        description="mon | tue | wed | thu | fri | sat | sun"
    )
    allDay: Optional[bool] = Field(
        None,
        description="The Location is open all day"
    )
    openingTime: Optional[str] = Field(
        None,
        description="Time that the Location opens"
    )
    closingTime: Optional[str] = Field(
        None,
        description="Time that the Location closes"
    )


class Location(FHIRResource):
    """
    FHIR R4 Location Resource
    Details and position information for a physical place where services are provided and resources and participants may be stored, found, contained, or accommodated.
    """

    resourceType: Literal["Location"] = "Location"

    # Identifiers
    identifier: Optional[List[Identifier]] = Field(
        None,
        description="Unique code or number identifying the location to its users"
    )

    # Status
    status: Optional[LocationStatus] = Field(
        None,
        description="active | suspended | inactive"
    )

    # Operational status
    operationalStatus: Optional[Coding] = Field(
        None,
        description="The operational status of the location (e.g. contaminated, housekeeping)"
    )

    # Name
    name: Optional[str] = Field(
        None,
        description="Name of the location as used by humans"
    )

    # Alias
    alias: Optional[List[str]] = Field(
        None,
        description="A list of alternate names that the location is known as"
    )

    # Description
    description: Optional[str] = Field(
        None,
        description="Additional details about the location"
    )

    # Mode
    mode: Optional[LocationMode] = Field(
        None,
        description="instance | kind"
    )

    # Type
    type: Optional[List[CodeableConcept]] = Field(
        None,
        description="Type of function performed (e.g., ward, clinic, OR)"
    )

    # Telecom
    telecom: Optional[List[ContactPoint]] = Field(
        None,
        description="Contact details of the location"
    )

    # Address
    address: Optional[Address] = Field(
        None,
        description="Physical location"
    )

    # Physical type
    physicalType: Optional[CodeableConcept] = Field(
        None,
        description="Physical form of the location (e.g., building, room, vehicle)"
    )

    # Position
    position: Optional[LocationPosition] = Field(
        None,
        description="The absolute geographic location"
    )

    # Managing organization
    managingOrganization: Optional[Reference] = Field(
        None,
        description="Organization responsible for provisioning and upkeep"
    )

    # Part of
    partOf: Optional[Reference] = Field(
        None,
        description="Another Location this one is physically a part of"
    )

    # Hours of operation
    hoursOfOperation: Optional[List[LocationHoursOfOperation]] = Field(
        None,
        description="What days/times during a week is this location usually open"
    )

    # Availability exceptions
    availabilityExceptions: Optional[str] = Field(
        None,
        description="Description of availability exceptions"
    )

    # Endpoint
    endpoint: Optional[List[Reference]] = Field(
        None,
        description="Technical endpoints providing access to services operated for the location"
    )

    class Config:
        schema_extra = {
            "example": {
                "resourceType": "Location",
                "id": "example",
                "status": "active",
                "name": "Emergency Room",
                "description": "Emergency Department on the second floor",
                "mode": "instance",
                "type": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                        "code": "ER",
                        "display": "Emergency room"
                    }]
                }],
                "telecom": [{
                    "system": "phone",
                    "value": "+1-555-ER-ROOM"
                }],
                "address": {
                    "line": ["General Hospital", "2nd Floor"],
                    "city": "Springfield",
                    "state": "IL",
                    "postalCode": "62701"
                },
                "physicalType": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/location-physical-type",
                        "code": "wa",
                        "display": "Ward"
                    }]
                },
                "managingOrganization": {
                    "reference": "Organization/example",
                    "display": "General Hospital"
                }
            }
        }


# Update forward references
