"""
FHIR R4 CodeSystem Resource
Declares the existence of and describes a code system
"""

from datetime import datetime
from typing import List, Optional, Literal
from pydantic import Field
from enum import Enum

from .base import (
    FHIRResource,
    Identifier,
    CodeableConcept,
    Coding
)


class CodeSystemStatus(str, Enum):
    """Status of the code system"""
    DRAFT = "draft"
    ACTIVE = "active"
    RETIRED = "retired"
    UNKNOWN = "unknown"


class CodeSystemContentMode(str, Enum):
    """How much of the content is represented"""
    NOT_PRESENT = "not-present"
    EXAMPLE = "example"
    FRAGMENT = "fragment"
    COMPLETE = "complete"
    SUPPLEMENT = "supplement"


class CodeSystemHierarchyMeaning(str, Enum):
    """Meaning of the hierarchy of concepts"""
    GROUPED_BY = "grouped-by"
    IS_A = "is-a"
    PART_OF = "part-of"
    CLASSIFIED_WITH = "classified-with"


class PropertyType(str, Enum):
    """Type of a property value"""
    CODE = "code"
    CODING = "Coding"
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    DATETIME = "dateTime"
    DECIMAL = "decimal"


class CodeSystemProperty(FHIRResource):
    """Additional information supplied about each concept"""

    code: str = Field(..., description="Identifies the property")
    uri: Optional[str] = Field(None, description="Formal identifier")
    description: Optional[str] = Field(None, description="Why the property is defined")
    type: PropertyType = Field(..., description="code | Coding | string | integer | boolean | dateTime | decimal")


class CodeSystemConceptDesignation(FHIRResource):
    """Additional representations for the concept"""

    language: Optional[str] = Field(None, description="Human language")
    use: Optional[Coding] = Field(None, description="Details how this designation would be used")
    value: str = Field(..., description="The text value")


class CodeSystemConceptProperty(FHIRResource):
    """Property value for the concept"""

    code: str = Field(..., description="Reference to CodeSystem.property.code")
    valueCode: Optional[str] = None
    valueCoding: Optional[Coding] = None
    valueString: Optional[str] = None
    valueInteger: Optional[int] = None
    valueBoolean: Optional[bool] = None
    valueDateTime: Optional[datetime] = None
    valueDecimal: Optional[float] = None


class CodeSystemConcept(FHIRResource):
    """Concepts in the code system"""

    code: str = Field(..., description="Code that identifies concept")
    display: Optional[str] = Field(None, description="Text to display")
    definition: Optional[str] = Field(None, description="Formal definition")
    designation: Optional[List[CodeSystemConceptDesignation]] = Field(
        None,
        description="Additional representations"
    )
    property: Optional[List[CodeSystemConceptProperty]] = Field(
        None,
        description="Property value for the concept"
    )
    concept: Optional[List['CodeSystemConcept']] = Field(
        None,
        description="Child Concepts"
    )


class CodeSystem(FHIRResource):
    """
    FHIR R4 CodeSystem Resource
    A code system resource specifies a set of codes drawn from one or more code systems.
    """

    resourceType: Literal["CodeSystem"] = "CodeSystem"

    url: Optional[str] = Field(
        None,
        description="Canonical identifier"
    )
    identifier: Optional[List[Identifier]] = Field(
        None,
        description="Additional identifier"
    )
    version: Optional[str] = Field(
        None,
        description="Business version"
    )
    name: Optional[str] = Field(
        None,
        description="Name (computer friendly)"
    )
    title: Optional[str] = Field(
        None,
        description="Name (human friendly)"
    )
    status: CodeSystemStatus = Field(
        ...,
        description="draft | active | retired | unknown"
    )
    experimental: Optional[bool] = Field(
        None,
        description="For testing purposes"
    )
    date: Optional[datetime] = Field(
        None,
        description="Date last changed"
    )
    publisher: Optional[str] = Field(
        None,
        description="Name of the publisher"
    )
    contact: Optional[List[dict]] = Field(
        None,
        description="Contact details"
    )
    description: Optional[str] = Field(
        None,
        description="Natural language description"
    )
    useContext: Optional[List[dict]] = Field(
        None,
        description="Context of use"
    )
    jurisdiction: Optional[List[CodeableConcept]] = Field(
        None,
        description="Intended jurisdiction"
    )
    purpose: Optional[str] = Field(
        None,
        description="Why this is defined"
    )
    copyright: Optional[str] = Field(
        None,
        description="Use and/or publishing restrictions"
    )
    caseSensitive: Optional[bool] = Field(
        None,
        description="If code comparison is case sensitive"
    )
    valueSet: Optional[str] = Field(
        None,
        description="Canonical reference to value set"
    )
    hierarchyMeaning: Optional[CodeSystemHierarchyMeaning] = Field(
        None,
        description="grouped-by | is-a | part-of | classified-with"
    )
    compositional: Optional[bool] = Field(
        None,
        description="If defines a compositional grammar"
    )
    versionNeeded: Optional[bool] = Field(
        None,
        description="If definitions are not stable"
    )
    content: CodeSystemContentMode = Field(
        ...,
        description="not-present | example | fragment | complete | supplement"
    )
    supplements: Optional[str] = Field(
        None,
        description="Canonical URL of Code System this supplements"
    )
    count: Optional[int] = Field(
        None,
        description="Total concepts in the code system",
        ge=0
    )
    property: Optional[List[CodeSystemProperty]] = Field(
        None,
        description="Additional information"
    )
    concept: Optional[List[CodeSystemConcept]] = Field(
        None,
        description="Concepts in the code system"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "resourceType": "CodeSystem",
                "id": "example",
                "url": "http://hl7.org/fhir/CodeSystem/example",
                "identifier": [{
                    "system": "http://acme.com/identifiers/codesystems",
                    "value": "internal-cholesterol"
                }],
                "version": "20210721",
                "name": "ACMECholCodes",
                "title": "ACME Codes for Cholesterol",
                "status": "active",
                "experimental": True,
                "date": "2024-01-15",
                "publisher": "ACME Co",
                "description": "Example code system",
                "caseSensitive": True,
                "content": "complete",
                "count": 3,
                "concept": [{
                    "code": "chol-mmol",
                    "display": "SChol (mmol/L)",
                    "definition": "Serum Cholesterol in mmol/L"
                }, {
                    "code": "chol-mass",
                    "display": "SChol (mg/L)",
                    "definition": "Serum Cholesterol in mg/L"
                }, {
                    "code": "chol",
                    "display": "SChol",
                    "definition": "Serum Cholesterol"
                }]
            }
        }
