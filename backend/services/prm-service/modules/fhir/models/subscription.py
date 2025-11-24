"""
FHIR R4 Subscription Resource
Server push subscription criteria
"""

from datetime import datetime
from typing import List, Optional, Literal
from pydantic import Field
from enum import Enum

from .base import (
    FHIRResource,
    ContactPoint,
    Extension
)


class SubscriptionStatus(str, Enum):
    """Status of the subscription"""
    REQUESTED = "requested"
    ACTIVE = "active"
    ERROR = "error"
    OFF = "off"


class SubscriptionChannelType(str, Enum):
    """Type of channel to send notifications on"""
    REST_HOOK = "rest-hook"
    WEBSOCKET = "websocket"
    EMAIL = "email"
    SMS = "sms"
    MESSAGE = "message"


class SubscriptionChannel(FHIRResource):
    """The channel on which to report matches to the criteria"""

    type: SubscriptionChannelType = Field(
        ...,
        description="rest-hook | websocket | email | sms | message"
    )
    endpoint: Optional[str] = Field(
        None,
        description="Where the channel points to"
    )
    payload: Optional[str] = Field(
        None,
        description="MIME type to send, or omit for no payload"
    )
    header: Optional[List[str]] = Field(
        None,
        description="Usage depends on the channel type"
    )


class Subscription(FHIRResource):
    """
    FHIR R4 Subscription Resource
    The subscription resource is used to define a push-based subscription from a server to another system.
    """

    resourceType: Literal["Subscription"] = "Subscription"

    status: SubscriptionStatus = Field(
        ...,
        description="requested | active | error | off"
    )
    contact: Optional[List[ContactPoint]] = Field(
        None,
        description="Contact details for source (e.g. troubleshooting)"
    )
    end: Optional[datetime] = Field(
        None,
        description="When to automatically delete the subscription"
    )
    reason: str = Field(
        ...,
        description="Description of why this subscription was created"
    )
    criteria: str = Field(
        ...,
        description="Rule for server push"
    )
    error: Optional[str] = Field(
        None,
        description="Latest error note"
    )
    channel: SubscriptionChannel = Field(
        ...,
        description="The channel on which to report matches to the criteria"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "resourceType": "Subscription",
                "id": "example",
                "status": "active",
                "contact": [{
                    "system": "phone",
                    "value": "+1-555-1234"
                }],
                "end": "2025-12-31T23:59:59Z",
                "reason": "Monitor new patient registrations",
                "criteria": "Patient?active=true",
                "channel": {
                    "type": "rest-hook",
                    "endpoint": "https://example.org/patient-notifications",
                    "payload": "application/fhir+json",
                    "header": ["Authorization: Bearer secret-token"]
                }
            }
        }
