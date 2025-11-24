"""
FHIR R4 ConceptMap Resource
A map from one set of concepts to one or more other concepts
"""

from datetime import datetime
from typing import List, Optional, Literal
from pydantic import Field
from enum import Enum

from .base import (
    FHIRResource,
    Identifier,
    ContactPoint,
    CodeableConcept,
    Coding,
    Extension
)


class ConceptMapStatus(str, Enum):
    """Status of the concept map"""
    DRAFT = "draft"
    ACTIVE = "active"
    RETIRED = "retired"
    UNKNOWN = "unknown"


class ConceptMapEquivalence(str, Enum):
    """Degree of equivalence between concepts"""
    RELATEDTO = "relatedto"
    EQUIVALENT = "equivalent"
    EQUAL = "equal"
    WIDER = "wider"
    SUBSUMES = "subsumes"
    NARROWER = "narrower"
    SPECIALIZES = "specializes"
    INEXACT = "inexact"
    UNMATCHED = "unmatched"
    DISJOINT = "disjoint"


class ConceptMapGroupUnmapped(FHIRResource):
    """What to do when there is no mapping for the source concept"""

    # Mode (required)
    mode: str = Field(
        ...,
        description="provided | fixed | other-map"
    )

    # Code
    code: Optional[str] = Field(
        None,
        description="Fixed code when mode = fixed"
    )

    # Display
    display: Optional[str] = Field(
        None,
        description="Display for the code"
    )

    # URL
    url: Optional[str] = Field(
        None,
        description="canonical reference to an additional ConceptMap to use for mapping if mode = other-map"
    )


class ConceptMapGroupElementTargetDependsOn(FHIRResource):
    """Other elements required for this mapping"""

    # Property (required)
    property: str = Field(
        ...,
        description="Reference to property mapping depends on"
    )

    # System
    system: Optional[str] = Field(
        None,
        description="Code System (if necessary)"
    )

    # Value (required)
    value: str = Field(
        ...,
        description="Value of the referenced element"
    )

    # Display
    display: Optional[str] = Field(
        None,
        description="Display for the code"
    )


class ConceptMapGroupElementTarget(FHIRResource):
    """Concept in target system for element"""

    # Code
    code: Optional[str] = Field(
        None,
        description="Code that identifies the target element"
    )

    # Display
    display: Optional[str] = Field(
        None,
        description="Display for the code"
    )

    # Equivalence (required)
    equivalence: ConceptMapEquivalence = Field(
        ...,
        description="relatedto | equivalent | equal | wider | subsumes | narrower | specializes | inexact | unmatched | disjoint"
    )

    # Comment
    comment: Optional[str] = Field(
        None,
        description="Description of status/issues in mapping"
    )

    # Depends on
    dependsOn: Optional[List[ConceptMapGroupElementTargetDependsOn]] = Field(
        None,
        description="Other elements required for this mapping (from context)"
    )

    # Product
    product: Optional[List[ConceptMapGroupElementTargetDependsOn]] = Field(
        None,
        description="Other concepts that this mapping also produces"
    )


class ConceptMapGroupElement(FHIRResource):
    """Mappings for a concept from the source set"""

    # Code
    code: Optional[str] = Field(
        None,
        description="Identifies element being mapped"
    )

    # Display
    display: Optional[str] = Field(
        None,
        description="Display for the code"
    )

    # Target
    target: Optional[List[ConceptMapGroupElementTarget]] = Field(
        None,
        description="Concept in target system for element"
    )


class ConceptMapGroup(FHIRResource):
    """Same source and target systems"""

    # Source
    source: Optional[str] = Field(
        None,
        description="Source system where concepts to be mapped are defined"
    )

    # Source version
    sourceVersion: Optional[str] = Field(
        None,
        description="Specific version of the code system"
    )

    # Target
    target: Optional[str] = Field(
        None,
        description="Target system that the concepts are to be mapped to"
    )

    # Target version
    targetVersion: Optional[str] = Field(
        None,
        description="Specific version of the code system"
    )

    # Element (required)
    element: List[ConceptMapGroupElement] = Field(
        ...,
        description="Mappings for a concept from the source set"
    )

    # Unmapped
    unmapped: Optional[ConceptMapGroupUnmapped] = Field(
        None,
        description="What to do when there is no mapping for the source concept"
    )


class ConceptMap(FHIRResource):
    """
    FHIR R4 ConceptMap Resource
    A statement of relationships from one set of concepts to one or more other concepts - either concepts in code systems,
    or data element/data element concepts, or classes in class models.
    """

    resourceType: Literal["ConceptMap"] = "ConceptMap"

    # URL
    url: Optional[str] = Field(
        None,
        description="Canonical identifier for this concept map"
    )

    # Identifier
    identifier: Optional[Identifier] = Field(
        None,
        description="Additional identifier for the concept map"
    )

    # Version
    version: Optional[str] = Field(
        None,
        description="Business version of the concept map"
    )

    # Name
    name: Optional[str] = Field(
        None,
        description="Name for this concept map (computer friendly)"
    )

    # Title
    title: Optional[str] = Field(
        None,
        description="Name for this concept map (human friendly)"
    )

    # Status (required)
    status: ConceptMapStatus = Field(
        ...,
        description="draft | active | retired | unknown"
    )

    # Experimental
    experimental: Optional[bool] = Field(
        None,
        description="For testing purposes, not real usage"
    )

    # Date
    date: Optional[datetime] = Field(
        None,
        description="Date last changed"
    )

    # Publisher
    publisher: Optional[str] = Field(
        None,
        description="Name of the publisher"
    )

    # Contact
    contact: Optional[List[dict]] = Field(
        None,
        description="Contact details for the publisher"
    )

    # Description
    description: Optional[str] = Field(
        None,
        description="Natural language description of the concept map"
    )

    # Use context
    useContext: Optional[List[dict]] = Field(
        None,
        description="The context that the content is intended to support"
    )

    # Jurisdiction
    jurisdiction: Optional[List[CodeableConcept]] = Field(
        None,
        description="Intended jurisdiction for concept map"
    )

    # Purpose
    purpose: Optional[str] = Field(
        None,
        description="Why this concept map is defined"
    )

    # Copyright
    copyright: Optional[str] = Field(
        None,
        description="Use and/or publishing restrictions"
    )

    # Source
    sourceUri: Optional[str] = Field(
        None,
        description="The source value set that contains the concepts that are being mapped"
    )
    sourceCanonical: Optional[str] = Field(
        None,
        description="The source value set that contains the concepts that are being mapped"
    )

    # Target
    targetUri: Optional[str] = Field(
        None,
        description="The target value set which provides context for the mappings"
    )
    targetCanonical: Optional[str] = Field(
        None,
        description="The target value set which provides context for the mappings"
    )

    # Group
    group: Optional[List[ConceptMapGroup]] = Field(
        None,
        description="Same source and target systems"
    )

    class Config:
        schema_extra = {
            "example": {
                "resourceType": "ConceptMap",
                "id": "example",
                "url": "http://hl7.org/fhir/ConceptMap/example",
                "identifier": {
                    "system": "urn:ietf:rfc:3986",
                    "value": "urn:uuid:53cd62ee-033e-414c-9f58-3ca97b5ffc3b"
                },
                "version": "20210721",
                "name": "FHIR_v3_Address_Use_Mapping",
                "title": "FHIR/v3 Address Use Mapping",
                "status": "active",
                "experimental": True,
                "date": "2024-01-15T10:30:00Z",
                "publisher": "HL7, Inc",
                "description": "A mapping between the FHIR and HL7 v3 AddressUse Code systems",
                "sourceCanonical": "http://hl7.org/fhir/ValueSet/address-use",
                "targetCanonical": "http://terminology.hl7.org/ValueSet/v3-AddressUse",
                "group": [{
                    "source": "http://hl7.org/fhir/address-use",
                    "target": "http://terminology.hl7.org/CodeSystem/v3-AddressUse",
                    "element": [{
                        "code": "home",
                        "display": "home",
                        "target": [{
                            "code": "H",
                            "display": "home",
                            "equivalence": "equivalent"
                        }]
                    }, {
                        "code": "work",
                        "display": "work",
                        "target": [{
                            "code": "WP",
                            "display": "work place",
                            "equivalence": "equivalent"
                        }]
                    }, {
                        "code": "temp",
                        "display": "temp",
                        "target": [{
                            "code": "TMP",
                            "display": "temporary address",
                            "equivalence": "equivalent"
                        }]
                    }, {
                        "code": "old",
                        "display": "old",
                        "target": [{
                            "code": "OLD",
                            "display": "no longer in use",
                            "equivalence": "narrower",
                            "comment": "In FHIR 'old' covers 'bad' and 'old'. In v3, 'old' is only for addresses no longer in use."
                        }]
                    }]
                }]
            }
        }


# Update forward references
