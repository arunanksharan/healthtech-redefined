"""
FHIR Terminology Service

Implements terminology operations for:
- CodeSystem $lookup
- ValueSet $expand and $validate-code
- ConceptMap $translate

Supports standard terminologies:
- SNOMED CT
- LOINC
- ICD-10
- RxNorm
- CPT
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class Concept:
    """A concept in a code system."""
    code: str
    display: str
    system: str
    definition: Optional[str] = None
    designations: List[Dict[str, str]] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True


@dataclass
class ValueSetExpansion:
    """Expansion of a value set."""
    identifier: str
    timestamp: datetime
    total: int
    offset: int
    contains: List[Concept]
    parameter: List[Dict[str, Any]] = field(default_factory=list)


class TerminologyService:
    """
    FHIR Terminology Service.

    Provides operations on code systems, value sets, and concept maps.
    """

    def __init__(self):
        # In-memory terminology data (would use database in production)
        self._code_systems: Dict[str, Dict[str, Concept]] = {}
        self._value_sets: Dict[str, List[str]] = {}  # URL -> list of codes
        self._concept_maps: Dict[str, Dict[str, str]] = {}  # URL -> source:target mappings

        # Load standard terminologies
        self._load_standard_terminologies()

    def _load_standard_terminologies(self):
        """Load common healthcare terminologies."""
        # SNOMED CT subset
        self._code_systems["http://snomed.info/sct"] = {
            "38341003": Concept(
                code="38341003",
                display="Hypertensive disorder",
                system="http://snomed.info/sct",
                definition="A disorder characterized by elevated blood pressure"
            ),
            "73211009": Concept(
                code="73211009",
                display="Diabetes mellitus",
                system="http://snomed.info/sct",
                definition="A metabolic disorder"
            ),
            "195967001": Concept(
                code="195967001",
                display="Asthma",
                system="http://snomed.info/sct"
            ),
            "22298006": Concept(
                code="22298006",
                display="Myocardial infarction",
                system="http://snomed.info/sct"
            ),
            "59621000": Concept(
                code="59621000",
                display="Essential hypertension",
                system="http://snomed.info/sct"
            ),
            "44054006": Concept(
                code="44054006",
                display="Type 2 diabetes mellitus",
                system="http://snomed.info/sct"
            ),
        }

        # LOINC codes
        self._code_systems["http://loinc.org"] = {
            "2339-0": Concept(
                code="2339-0",
                display="Glucose [Mass/volume] in Blood",
                system="http://loinc.org"
            ),
            "4548-4": Concept(
                code="4548-4",
                display="Hemoglobin A1c/Hemoglobin.total in Blood",
                system="http://loinc.org"
            ),
            "2093-3": Concept(
                code="2093-3",
                display="Cholesterol [Mass/volume] in Serum or Plasma",
                system="http://loinc.org"
            ),
            "2160-0": Concept(
                code="2160-0",
                display="Creatinine [Mass/volume] in Serum or Plasma",
                system="http://loinc.org"
            ),
            "8867-4": Concept(
                code="8867-4",
                display="Heart rate",
                system="http://loinc.org"
            ),
            "8310-5": Concept(
                code="8310-5",
                display="Body temperature",
                system="http://loinc.org"
            ),
            "8480-6": Concept(
                code="8480-6",
                display="Systolic blood pressure",
                system="http://loinc.org"
            ),
            "8462-4": Concept(
                code="8462-4",
                display="Diastolic blood pressure",
                system="http://loinc.org"
            ),
            "29463-7": Concept(
                code="29463-7",
                display="Body weight",
                system="http://loinc.org"
            ),
            "8302-2": Concept(
                code="8302-2",
                display="Body height",
                system="http://loinc.org"
            ),
        }

        # ICD-10 codes
        self._code_systems["http://hl7.org/fhir/sid/icd-10-cm"] = {
            "I10": Concept(
                code="I10",
                display="Essential (primary) hypertension",
                system="http://hl7.org/fhir/sid/icd-10-cm"
            ),
            "E11.9": Concept(
                code="E11.9",
                display="Type 2 diabetes mellitus without complications",
                system="http://hl7.org/fhir/sid/icd-10-cm"
            ),
            "J45.909": Concept(
                code="J45.909",
                display="Unspecified asthma, uncomplicated",
                system="http://hl7.org/fhir/sid/icd-10-cm"
            ),
            "R07.9": Concept(
                code="R07.9",
                display="Chest pain, unspecified",
                system="http://hl7.org/fhir/sid/icd-10-cm"
            ),
            "F32.9": Concept(
                code="F32.9",
                display="Major depressive disorder, single episode, unspecified",
                system="http://hl7.org/fhir/sid/icd-10-cm"
            ),
            "F41.9": Concept(
                code="F41.9",
                display="Anxiety disorder, unspecified",
                system="http://hl7.org/fhir/sid/icd-10-cm"
            ),
        }

        # RxNorm codes
        self._code_systems["http://www.nlm.nih.gov/research/umls/rxnorm"] = {
            "311036": Concept(
                code="311036",
                display="Lisinopril 10 MG Oral Tablet",
                system="http://www.nlm.nih.gov/research/umls/rxnorm"
            ),
            "860975": Concept(
                code="860975",
                display="Metformin hydrochloride 500 MG Oral Tablet",
                system="http://www.nlm.nih.gov/research/umls/rxnorm"
            ),
            "197361": Concept(
                code="197361",
                display="Amlodipine 5 MG Oral Tablet",
                system="http://www.nlm.nih.gov/research/umls/rxnorm"
            ),
            "313782": Concept(
                code="313782",
                display="Atorvastatin 20 MG Oral Tablet",
                system="http://www.nlm.nih.gov/research/umls/rxnorm"
            ),
            "200031": Concept(
                code="200031",
                display="Omeprazole 20 MG Delayed Release Oral Capsule",
                system="http://www.nlm.nih.gov/research/umls/rxnorm"
            ),
        }

        # Administrative gender
        self._code_systems["http://hl7.org/fhir/administrative-gender"] = {
            "male": Concept(code="male", display="Male", system="http://hl7.org/fhir/administrative-gender"),
            "female": Concept(code="female", display="Female", system="http://hl7.org/fhir/administrative-gender"),
            "other": Concept(code="other", display="Other", system="http://hl7.org/fhir/administrative-gender"),
            "unknown": Concept(code="unknown", display="Unknown", system="http://hl7.org/fhir/administrative-gender"),
        }

        # Observation status
        self._code_systems["http://hl7.org/fhir/observation-status"] = {
            "registered": Concept(code="registered", display="Registered", system="http://hl7.org/fhir/observation-status"),
            "preliminary": Concept(code="preliminary", display="Preliminary", system="http://hl7.org/fhir/observation-status"),
            "final": Concept(code="final", display="Final", system="http://hl7.org/fhir/observation-status"),
            "amended": Concept(code="amended", display="Amended", system="http://hl7.org/fhir/observation-status"),
            "cancelled": Concept(code="cancelled", display="Cancelled", system="http://hl7.org/fhir/observation-status"),
        }

        # Common value sets
        self._value_sets["http://hl7.org/fhir/ValueSet/administrative-gender"] = [
            "male", "female", "other", "unknown"
        ]

        self._value_sets["http://hl7.org/fhir/ValueSet/observation-status"] = [
            "registered", "preliminary", "final", "amended", "cancelled"
        ]

        # SNOMED to ICD-10 mapping
        self._concept_maps["http://example.org/fhir/ConceptMap/snomed-to-icd10"] = {
            "38341003": "I10",  # Hypertensive disorder -> Essential hypertension
            "73211009": "E11.9",  # Diabetes mellitus -> Type 2 diabetes
            "195967001": "J45.909",  # Asthma -> Unspecified asthma
        }

    def lookup(
        self,
        system: str,
        code: str,
        version: Optional[str] = None,
        properties: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        CodeSystem $lookup operation.

        Given a code/system, return details about the concept.

        Args:
            system: The code system URL
            code: The code to look up
            version: Optional version of the code system
            properties: Optional list of properties to return

        Returns:
            Parameters resource with concept details
        """
        code_system = self._code_systems.get(system, {})
        concept = code_system.get(code)

        if not concept:
            return {
                "resourceType": "Parameters",
                "parameter": [
                    {
                        "name": "result",
                        "valueBoolean": False
                    },
                    {
                        "name": "message",
                        "valueString": f"Code '{code}' not found in system '{system}'"
                    }
                ]
            }

        parameters = [
            {"name": "name", "valueString": self._get_system_name(system)},
            {"name": "display", "valueString": concept.display},
        ]

        if concept.definition:
            parameters.append({"name": "definition", "valueString": concept.definition})

        for designation in concept.designations:
            parameters.append({
                "name": "designation",
                "part": [
                    {"name": "language", "valueCode": designation.get("language", "en")},
                    {"name": "value", "valueString": designation.get("value", concept.display)},
                ]
            })

        if properties:
            for prop_name in properties:
                if prop_name in concept.properties:
                    parameters.append({
                        "name": "property",
                        "part": [
                            {"name": "code", "valueCode": prop_name},
                            {"name": "value", "valueString": str(concept.properties[prop_name])},
                        ]
                    })

        return {
            "resourceType": "Parameters",
            "parameter": parameters
        }

    def _get_system_name(self, system: str) -> str:
        """Get human-readable name for a code system."""
        names = {
            "http://snomed.info/sct": "SNOMED CT",
            "http://loinc.org": "LOINC",
            "http://hl7.org/fhir/sid/icd-10-cm": "ICD-10-CM",
            "http://www.nlm.nih.gov/research/umls/rxnorm": "RxNorm",
            "http://hl7.org/fhir/administrative-gender": "Administrative Gender",
            "http://hl7.org/fhir/observation-status": "Observation Status",
        }
        return names.get(system, system)

    def expand(
        self,
        url: Optional[str] = None,
        value_set: Optional[Dict[str, Any]] = None,
        filter_text: Optional[str] = None,
        offset: int = 0,
        count: int = 100,
    ) -> Dict[str, Any]:
        """
        ValueSet $expand operation.

        Expand a value set to list its concepts.

        Args:
            url: URL of a registered ValueSet to expand
            value_set: Inline ValueSet resource to expand
            filter_text: Text to filter concepts by
            offset: Starting offset for pagination
            count: Maximum concepts to return

        Returns:
            Expanded ValueSet resource
        """
        concepts: List[Dict[str, Any]] = []

        if url:
            # Expand registered value set
            value_set_codes = self._value_sets.get(url, [])

            # Determine the code system
            system = self._infer_system_from_valueset(url)
            code_system = self._code_systems.get(system, {})

            for code in value_set_codes:
                concept = code_system.get(code)
                if concept:
                    # Apply filter if provided
                    if filter_text:
                        if filter_text.lower() not in concept.display.lower():
                            continue

                    concepts.append({
                        "system": concept.system,
                        "code": concept.code,
                        "display": concept.display,
                    })

        elif value_set:
            # Expand inline value set
            compose = value_set.get("compose", {})
            for include in compose.get("include", []):
                system = include.get("system")
                code_system = self._code_systems.get(system, {})

                if "concept" in include:
                    # Enumerated concepts
                    for c in include["concept"]:
                        concept = code_system.get(c["code"])
                        if concept:
                            if filter_text and filter_text.lower() not in concept.display.lower():
                                continue
                            concepts.append({
                                "system": system,
                                "code": concept.code,
                                "display": concept.display,
                            })
                else:
                    # All codes from system
                    for code, concept in code_system.items():
                        if filter_text and filter_text.lower() not in concept.display.lower():
                            continue
                        concepts.append({
                            "system": system,
                            "code": concept.code,
                            "display": concept.display,
                        })

        # Apply pagination
        total = len(concepts)
        concepts = concepts[offset:offset + count]

        return {
            "resourceType": "ValueSet",
            "url": url,
            "status": "active",
            "expansion": {
                "identifier": f"urn:uuid:{datetime.now(timezone.utc).isoformat()}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total": total,
                "offset": offset,
                "contains": concepts,
            }
        }

    def _infer_system_from_valueset(self, url: str) -> str:
        """Infer the code system from a value set URL."""
        if "administrative-gender" in url:
            return "http://hl7.org/fhir/administrative-gender"
        if "observation-status" in url:
            return "http://hl7.org/fhir/observation-status"
        return ""

    def validate_code(
        self,
        url: Optional[str] = None,
        value_set: Optional[Dict[str, Any]] = None,
        code: Optional[str] = None,
        system: Optional[str] = None,
        display: Optional[str] = None,
        coding: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        ValueSet $validate-code operation.

        Validate that a code is in a value set.

        Args:
            url: URL of the ValueSet to validate against
            value_set: Inline ValueSet to validate against
            code: Code to validate
            system: System the code belongs to
            display: Display to validate
            coding: Coding object with code, system, display

        Returns:
            Parameters resource with validation result
        """
        if coding:
            code = coding.get("code")
            system = coding.get("system")
            display = coding.get("display")

        # First, check if code exists in the system
        code_system = self._code_systems.get(system, {})
        concept = code_system.get(code)

        if not concept:
            return {
                "resourceType": "Parameters",
                "parameter": [
                    {"name": "result", "valueBoolean": False},
                    {"name": "message", "valueString": f"Code '{code}' not found in system '{system}'"},
                ]
            }

        # Check if code is in value set
        in_valueset = True
        if url:
            value_set_codes = self._value_sets.get(url, [])
            in_valueset = code in value_set_codes

        # Check display if provided
        display_valid = True
        if display and display != concept.display:
            display_valid = False

        parameters = [
            {"name": "result", "valueBoolean": in_valueset and display_valid},
        ]

        if not in_valueset:
            parameters.append({
                "name": "message",
                "valueString": f"Code '{code}' is not in the value set"
            })
        elif not display_valid:
            parameters.append({
                "name": "message",
                "valueString": f"Display '{display}' does not match expected '{concept.display}'"
            })
        else:
            parameters.append({"name": "display", "valueString": concept.display})

        return {
            "resourceType": "Parameters",
            "parameter": parameters
        }

    def translate(
        self,
        url: Optional[str] = None,
        concept_map: Optional[Dict[str, Any]] = None,
        code: Optional[str] = None,
        system: Optional[str] = None,
        source: Optional[str] = None,
        target: Optional[str] = None,
        coding: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        ConceptMap $translate operation.

        Translate a code from one code system to another.

        Args:
            url: URL of the ConceptMap to use
            concept_map: Inline ConceptMap to use
            code: Code to translate
            system: System of the source code
            source: Source value set URL
            target: Target value set URL
            coding: Source coding object

        Returns:
            Parameters resource with translation result
        """
        if coding:
            code = coding.get("code")
            system = coding.get("system")

        # Get concept map
        mappings = self._concept_maps.get(url, {})

        if not mappings:
            return {
                "resourceType": "Parameters",
                "parameter": [
                    {"name": "result", "valueBoolean": False},
                    {"name": "message", "valueString": f"ConceptMap '{url}' not found"},
                ]
            }

        target_code = mappings.get(code)

        if not target_code:
            return {
                "resourceType": "Parameters",
                "parameter": [
                    {"name": "result", "valueBoolean": False},
                    {"name": "message", "valueString": f"No mapping found for code '{code}'"},
                ]
            }

        # Look up the target concept details
        # Infer target system from concept map URL
        target_system = self._infer_target_system(url)
        target_code_system = self._code_systems.get(target_system, {})
        target_concept = target_code_system.get(target_code)

        match_parameter = {
            "name": "match",
            "part": [
                {"name": "equivalence", "valueCode": "equivalent"},
                {
                    "name": "concept",
                    "valueCoding": {
                        "system": target_system,
                        "code": target_code,
                        "display": target_concept.display if target_concept else target_code,
                    }
                },
            ]
        }

        return {
            "resourceType": "Parameters",
            "parameter": [
                {"name": "result", "valueBoolean": True},
                match_parameter,
            ]
        }

    def _infer_target_system(self, concept_map_url: str) -> str:
        """Infer target code system from concept map URL."""
        if "snomed-to-icd10" in concept_map_url:
            return "http://hl7.org/fhir/sid/icd-10-cm"
        return ""

    def subsumes(
        self,
        system: str,
        code_a: str,
        code_b: str,
    ) -> Dict[str, Any]:
        """
        CodeSystem $subsumes operation.

        Test whether code A subsumes code B (A is-a B).

        Args:
            system: Code system URL
            code_a: First code
            code_b: Second code

        Returns:
            Parameters resource with subsumption result
        """
        # Simplified - would need hierarchy data for real implementation
        # For now, just check if codes are equal
        if code_a == code_b:
            outcome = "equivalent"
        else:
            outcome = "not-subsumed"

        return {
            "resourceType": "Parameters",
            "parameter": [
                {"name": "outcome", "valueCode": outcome},
            ]
        }

    def get_code_system(
        self,
        url: str,
    ) -> Optional[Dict[str, Any]]:
        """Get a CodeSystem resource by URL."""
        code_system = self._code_systems.get(url)
        if not code_system:
            return None

        concepts = [
            {
                "code": c.code,
                "display": c.display,
                "definition": c.definition,
            }
            for c in code_system.values()
        ]

        return {
            "resourceType": "CodeSystem",
            "url": url,
            "name": self._get_system_name(url),
            "status": "active",
            "content": "complete",
            "count": len(concepts),
            "concept": concepts,
        }

    def get_value_set(
        self,
        url: str,
    ) -> Optional[Dict[str, Any]]:
        """Get a ValueSet resource by URL."""
        if url not in self._value_sets:
            return None

        system = self._infer_system_from_valueset(url)

        return {
            "resourceType": "ValueSet",
            "url": url,
            "status": "active",
            "compose": {
                "include": [
                    {
                        "system": system,
                        "concept": [
                            {"code": c} for c in self._value_sets[url]
                        ]
                    }
                ]
            }
        }


# Global instance
terminology_service = TerminologyService()
