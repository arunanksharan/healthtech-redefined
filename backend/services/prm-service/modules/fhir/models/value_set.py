"""
FHIR R4 ValueSet Resource
A set of codes drawn from one or more code systems
"""

from datetime import datetime
from typing import List, Optional, Literal
from pydantic import Field, validator
from enum import Enum

from .base import (
    FHIRResource,
    Identifier,
    ContactPoint,
    CodeableConcept,
    Coding,
    Extension
)


class ValueSetStatus(str, Enum):
    """Status of the value set"""
    DRAFT = "draft"
    ACTIVE = "active"
    RETIRED = "retired"
    UNKNOWN = "unknown"


class FilterOperator(str, Enum):
    """Operators for value set filters"""
    EQUALS = "="
    IS_A = "is-a"
    DESCENDENT_OF = "descendent-of"
    IS_NOT_A = "is-not-a"
    REGEX = "regex"
    IN = "in"
    NOT_IN = "not-in"
    GENERALIZES = "generalizes"
    EXISTS = "exists"


class ValueSetComposeIncludeConceptDesignation(FHIRResource):
    """Additional representations for this concept"""

    # Language
    language: Optional[str] = Field(
        None,
        description="Human language of the designation"
    )

    # Use
    use: Optional[Coding] = Field(
        None,
        description="Types of uses of designations"
    )

    # Value (required)
    value: str = Field(
        ...,
        description="The text value for this designation"
    )


class ValueSetComposeIncludeConcept(FHIRResource):
    """Concept to include or exclude"""

    # Code (required)
    code: str = Field(
        ...,
        description="Code or expression from system"
    )

    # Display
    display: Optional[str] = Field(
        None,
        description="Text to display for this code for this value set in this valueset"
    )

    # Designation
    designation: Optional[List[ValueSetComposeIncludeConceptDesignation]] = Field(
        None,
        description="Additional representations for this concept"
    )


class ValueSetComposeIncludeFilter(FHIRResource):
    """Select codes/concepts by their properties"""

    # Property (required)
    property: str = Field(
        ...,
        description="A property/filter defined by the code system"
    )

    # Op (required)
    op: FilterOperator = Field(
        ...,
        description="= | is-a | descendent-of | is-not-a | regex | in | not-in | generalizes | exists"
    )

    # Value (required)
    value: str = Field(
        ...,
        description="Code from the system, or regex criteria, or boolean value"
    )


class ValueSetComposeInclude(FHIRResource):
    """Include one or more codes from a code system or other value set"""

    # System
    system: Optional[str] = Field(
        None,
        description="The system the codes come from"
    )

    # Version
    version: Optional[str] = Field(
        None,
        description="Specific version of the code system referred to"
    )

    # Concept
    concept: Optional[List[ValueSetComposeIncludeConcept]] = Field(
        None,
        description="A concept defined in the system"
    )

    # Filter
    filter: Optional[List[ValueSetComposeIncludeFilter]] = Field(
        None,
        description="Select codes/concepts by their properties (including relationships)"
    )

    # Value set
    valueSet: Optional[List[str]] = Field(
        None,
        description="Select the contents included in this value set"
    )


class ValueSetCompose(FHIRResource):
    """Content logical definition of the value set (CLD)"""

    # Locked date
    lockedDate: Optional[datetime] = Field(
        None,
        description="Fixed date for references with no specified version"
    )

    # Inactive
    inactive: Optional[bool] = Field(
        None,
        description="Whether inactive codes are in the value set"
    )

    # Include (required)
    include: List[ValueSetComposeInclude] = Field(
        ...,
        description="Include one or more codes from a code system or other value set(s)"
    )

    # Exclude
    exclude: Optional[List[ValueSetComposeInclude]] = Field(
        None,
        description="Explicitly exclude codes from a code system or other value sets"
    )


class ValueSetExpansionParameter(FHIRResource):
    """Parameter that controlled the expansion process"""

    # Name (required)
    name: str = Field(
        ...,
        description="Name as assigned by the client or server"
    )

    # Value (one of the following)
    valueString: Optional[str] = Field(
        None,
        description="Value of the named parameter"
    )
    valueBoolean: Optional[bool] = Field(
        None,
        description="Value of the named parameter"
    )
    valueInteger: Optional[int] = Field(
        None,
        description="Value of the named parameter"
    )
    valueDecimal: Optional[float] = Field(
        None,
        description="Value of the named parameter"
    )
    valueUri: Optional[str] = Field(
        None,
        description="Value of the named parameter"
    )
    valueCode: Optional[str] = Field(
        None,
        description="Value of the named parameter"
    )
    valueDateTime: Optional[datetime] = Field(
        None,
        description="Value of the named parameter"
    )


class ValueSetExpansionContains(FHIRResource):
    """Codes in the value set"""

    # System
    system: Optional[str] = Field(
        None,
        description="System value for the code"
    )

    # Abstract
    abstract: Optional[bool] = Field(
        None,
        description="If user cannot select this entry"
    )

    # Inactive
    inactive: Optional[bool] = Field(
        None,
        description="If concept is inactive in the code system"
    )

    # Version
    version: Optional[str] = Field(
        None,
        description="Version in which this code/display is defined"
    )

    # Code
    code: Optional[str] = Field(
        None,
        description="Code - if blank, this is not a selectable code"
    )

    # Display
    display: Optional[str] = Field(
        None,
        description="User display for the concept"
    )

    # Designation
    designation: Optional[List[ValueSetComposeIncludeConceptDesignation]] = Field(
        None,
        description="Additional representations for this item"
    )

    # Contains (recursive)
    contains: Optional[List['ValueSetExpansionContains']] = Field(
        None,
        description="Codes contained under this entry"
    )


class ValueSetExpansion(FHIRResource):
    """Used when the value set is "expanded"""

    # Identifier
    identifier: Optional[str] = Field(
        None,
        description="Identifies the value set expansion (business identifier)"
    )

    # Timestamp (required)
    timestamp: datetime = Field(
        ...,
        description="Time ValueSet expansion happened"
    )

    # Total
    total: Optional[int] = Field(
        None,
        description="Total number of codes in the expansion",
        ge=0
    )

    # Offset
    offset: Optional[int] = Field(
        None,
        description="Offset at which this resource starts",
        ge=0
    )

    # Parameter
    parameter: Optional[List[ValueSetExpansionParameter]] = Field(
        None,
        description="Parameter that controlled the expansion process"
    )

    # Contains
    contains: Optional[List[ValueSetExpansionContains]] = Field(
        None,
        description="Codes in the value set"
    )


class ValueSet(FHIRResource):
    """
    FHIR R4 ValueSet Resource
    A value set specifies a set of codes drawn from one or more code systems.
    """

    resourceType: Literal["ValueSet"] = "ValueSet"

    # URL
    url: Optional[str] = Field(
        None,
        description="Canonical identifier for this value set"
    )

    # Identifier
    identifier: Optional[List[Identifier]] = Field(
        None,
        description="Additional identifier for the value set"
    )

    # Version
    version: Optional[str] = Field(
        None,
        description="Business version of the value set"
    )

    # Name
    name: Optional[str] = Field(
        None,
        description="Name for this value set (computer friendly)"
    )

    # Title
    title: Optional[str] = Field(
        None,
        description="Name for this value set (human friendly)"
    )

    # Status (required)
    status: ValueSetStatus = Field(
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
        description="Natural language description of the value set"
    )

    # Use context
    useContext: Optional[List[dict]] = Field(
        None,
        description="The context that the content is intended to support"
    )

    # Jurisdiction
    jurisdiction: Optional[List[CodeableConcept]] = Field(
        None,
        description="Intended jurisdiction for value set"
    )

    # Immutable
    immutable: Optional[bool] = Field(
        None,
        description="Indicates whether or not any change to the content logical definition may occur"
    )

    # Purpose
    purpose: Optional[str] = Field(
        None,
        description="Why this value set is defined"
    )

    # Copyright
    copyright: Optional[str] = Field(
        None,
        description="Use and/or publishing restrictions"
    )

    # Compose
    compose: Optional[ValueSetCompose] = Field(
        None,
        description="Content logical definition of the value set (CLD)"
    )

    # Expansion
    expansion: Optional[ValueSetExpansion] = Field(
        None,
        description="Used when the value set is expanded"
    )

    class Config:
        schema_extra = {
            "example": {
                "resourceType": "ValueSet",
                "id": "example",
                "url": "http://hl7.org/fhir/ValueSet/example-extensional",
                "identifier": [{
                    "system": "http://acme.com/identifiers/valuesets",
                    "value": "loinc-cholesterol-incode"
                }],
                "version": "20150622",
                "name": "LOINCCodesForCholesterolInSerumPlasma",
                "title": "LOINC Codes for Cholesterol in Serum/Plasma",
                "status": "active",
                "experimental": True,
                "date": "2024-01-15T10:30:00Z",
                "publisher": "HL7 International",
                "description": "This is an example value set that includes all the LOINC codes for serum/plasma cholesterol from v2.36",
                "compose": {
                    "lockedDate": "2012-06-13",
                    "include": [{
                        "system": "http://loinc.org",
                        "version": "2.36",
                        "concept": [{
                            "code": "14647-2",
                            "display": "Cholesterol [Moles/volume] in Serum or Plasma"
                        }, {
                            "code": "2093-3",
                            "display": "Cholesterol [Mass/volume] in Serum or Plasma"
                        }, {
                            "code": "35200-5",
                            "display": "Cholesterol [Mass or Moles/volume] in Serum or Plasma"
                        }]
                    }]
                },
                "expansion": {
                    "identifier": "urn:uuid:42316ff8-2714-4680-9980-f37a6d1a71bc",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "total": 3,
                    "contains": [{
                        "system": "http://loinc.org",
                        "code": "14647-2",
                        "display": "Cholesterol [Moles/volume] in Serum or Plasma"
                    }, {
                        "system": "http://loinc.org",
                        "code": "2093-3",
                        "display": "Cholesterol [Mass/volume] in Serum or Plasma"
                    }, {
                        "system": "http://loinc.org",
                        "code": "35200-5",
                        "display": "Cholesterol [Mass or Moles/volume] in Serum or Plasma"
                    }]
                }
            }
        }


# Update forward references
