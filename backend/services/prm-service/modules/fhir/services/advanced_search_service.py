"""
FHIR Advanced Search Service

Implements comprehensive FHIR R4 search capabilities:
- All search parameter types (string, token, date, number, reference, composite, quantity, uri)
- Chained searches (e.g., Observation?patient.name=Smith)
- Reverse chaining (_has parameter)
- _include and _revinclude for related resources
- Search modifiers (:exact, :contains, :missing, :not, :above, :below)
- Sorting and pagination
"""

from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
import re
from dataclasses import dataclass, field
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, not_, func, text
from loguru import logger


class SearchParamType(str, Enum):
    """FHIR Search parameter types."""
    STRING = "string"
    TOKEN = "token"
    DATE = "date"
    NUMBER = "number"
    REFERENCE = "reference"
    COMPOSITE = "composite"
    QUANTITY = "quantity"
    URI = "uri"
    SPECIAL = "special"


class SearchModifier(str, Enum):
    """FHIR Search modifiers."""
    EXACT = "exact"
    CONTAINS = "contains"
    MISSING = "missing"
    NOT = "not"
    ABOVE = "above"
    BELOW = "below"
    TEXT = "text"
    IN = "in"
    NOT_IN = "not-in"
    OF_TYPE = "of-type"
    IDENTIFIER = "identifier"


class SearchPrefix(str, Enum):
    """FHIR Search prefixes for comparisons."""
    EQ = "eq"  # equals (default)
    NE = "ne"  # not equals
    GT = "gt"  # greater than
    LT = "lt"  # less than
    GE = "ge"  # greater than or equals
    LE = "le"  # less than or equals
    SA = "sa"  # starts after
    EB = "eb"  # ends before
    AP = "ap"  # approximately


@dataclass
class SearchParameter:
    """Parsed search parameter."""
    name: str
    value: Any
    modifier: Optional[SearchModifier] = None
    prefix: Optional[SearchPrefix] = None
    chain: List[str] = field(default_factory=list)  # For chained params
    param_type: SearchParamType = SearchParamType.STRING


@dataclass
class IncludeParameter:
    """Parsed _include/_revinclude parameter."""
    source_type: str
    search_param: str
    target_type: Optional[str] = None
    iterate: bool = False


@dataclass
class SearchResult:
    """Search operation result."""
    resources: List[Dict[str, Any]]
    total: int
    included_resources: List[Dict[str, Any]] = field(default_factory=list)


# Search parameter definitions for core FHIR resources
SEARCH_PARAM_DEFINITIONS: Dict[str, Dict[str, SearchParamType]] = {
    "Patient": {
        "_id": SearchParamType.TOKEN,
        "identifier": SearchParamType.TOKEN,
        "name": SearchParamType.STRING,
        "family": SearchParamType.STRING,
        "given": SearchParamType.STRING,
        "birthdate": SearchParamType.DATE,
        "gender": SearchParamType.TOKEN,
        "phone": SearchParamType.TOKEN,
        "email": SearchParamType.TOKEN,
        "address": SearchParamType.STRING,
        "address-city": SearchParamType.STRING,
        "address-state": SearchParamType.STRING,
        "address-postalcode": SearchParamType.STRING,
        "active": SearchParamType.TOKEN,
        "deceased": SearchParamType.TOKEN,
        "general-practitioner": SearchParamType.REFERENCE,
        "organization": SearchParamType.REFERENCE,
    },
    "Practitioner": {
        "_id": SearchParamType.TOKEN,
        "identifier": SearchParamType.TOKEN,
        "name": SearchParamType.STRING,
        "family": SearchParamType.STRING,
        "given": SearchParamType.STRING,
        "active": SearchParamType.TOKEN,
        "phone": SearchParamType.TOKEN,
        "email": SearchParamType.TOKEN,
        "address": SearchParamType.STRING,
    },
    "Organization": {
        "_id": SearchParamType.TOKEN,
        "identifier": SearchParamType.TOKEN,
        "name": SearchParamType.STRING,
        "type": SearchParamType.TOKEN,
        "address": SearchParamType.STRING,
        "active": SearchParamType.TOKEN,
        "partof": SearchParamType.REFERENCE,
    },
    "Encounter": {
        "_id": SearchParamType.TOKEN,
        "identifier": SearchParamType.TOKEN,
        "status": SearchParamType.TOKEN,
        "class": SearchParamType.TOKEN,
        "type": SearchParamType.TOKEN,
        "subject": SearchParamType.REFERENCE,
        "patient": SearchParamType.REFERENCE,
        "participant": SearchParamType.REFERENCE,
        "practitioner": SearchParamType.REFERENCE,
        "location": SearchParamType.REFERENCE,
        "date": SearchParamType.DATE,
        "service-provider": SearchParamType.REFERENCE,
        "diagnosis": SearchParamType.REFERENCE,
    },
    "Observation": {
        "_id": SearchParamType.TOKEN,
        "identifier": SearchParamType.TOKEN,
        "status": SearchParamType.TOKEN,
        "code": SearchParamType.TOKEN,
        "category": SearchParamType.TOKEN,
        "subject": SearchParamType.REFERENCE,
        "patient": SearchParamType.REFERENCE,
        "encounter": SearchParamType.REFERENCE,
        "performer": SearchParamType.REFERENCE,
        "date": SearchParamType.DATE,
        "value-quantity": SearchParamType.QUANTITY,
        "value-string": SearchParamType.STRING,
        "value-concept": SearchParamType.TOKEN,
    },
    "Condition": {
        "_id": SearchParamType.TOKEN,
        "identifier": SearchParamType.TOKEN,
        "clinical-status": SearchParamType.TOKEN,
        "verification-status": SearchParamType.TOKEN,
        "code": SearchParamType.TOKEN,
        "category": SearchParamType.TOKEN,
        "severity": SearchParamType.TOKEN,
        "subject": SearchParamType.REFERENCE,
        "patient": SearchParamType.REFERENCE,
        "encounter": SearchParamType.REFERENCE,
        "onset-date": SearchParamType.DATE,
        "recorded-date": SearchParamType.DATE,
    },
    "Procedure": {
        "_id": SearchParamType.TOKEN,
        "identifier": SearchParamType.TOKEN,
        "status": SearchParamType.TOKEN,
        "code": SearchParamType.TOKEN,
        "category": SearchParamType.TOKEN,
        "subject": SearchParamType.REFERENCE,
        "patient": SearchParamType.REFERENCE,
        "encounter": SearchParamType.REFERENCE,
        "date": SearchParamType.DATE,
        "performer": SearchParamType.REFERENCE,
    },
    "MedicationRequest": {
        "_id": SearchParamType.TOKEN,
        "identifier": SearchParamType.TOKEN,
        "status": SearchParamType.TOKEN,
        "intent": SearchParamType.TOKEN,
        "medication": SearchParamType.REFERENCE,
        "subject": SearchParamType.REFERENCE,
        "patient": SearchParamType.REFERENCE,
        "encounter": SearchParamType.REFERENCE,
        "requester": SearchParamType.REFERENCE,
        "authoredon": SearchParamType.DATE,
    },
    "AllergyIntolerance": {
        "_id": SearchParamType.TOKEN,
        "identifier": SearchParamType.TOKEN,
        "clinical-status": SearchParamType.TOKEN,
        "verification-status": SearchParamType.TOKEN,
        "type": SearchParamType.TOKEN,
        "category": SearchParamType.TOKEN,
        "criticality": SearchParamType.TOKEN,
        "code": SearchParamType.TOKEN,
        "patient": SearchParamType.REFERENCE,
        "onset": SearchParamType.DATE,
    },
    "Location": {
        "_id": SearchParamType.TOKEN,
        "identifier": SearchParamType.TOKEN,
        "name": SearchParamType.STRING,
        "status": SearchParamType.TOKEN,
        "type": SearchParamType.TOKEN,
        "address": SearchParamType.STRING,
        "organization": SearchParamType.REFERENCE,
        "partof": SearchParamType.REFERENCE,
    },
}

# Reference target types for each search parameter
REFERENCE_TARGETS: Dict[str, Dict[str, List[str]]] = {
    "Patient": {
        "general-practitioner": ["Practitioner", "Organization", "PractitionerRole"],
        "organization": ["Organization"],
    },
    "Encounter": {
        "subject": ["Patient"],
        "patient": ["Patient"],
        "participant": ["Practitioner", "PractitionerRole"],
        "practitioner": ["Practitioner"],
        "location": ["Location"],
        "service-provider": ["Organization"],
        "diagnosis": ["Condition"],
    },
    "Observation": {
        "subject": ["Patient", "Group", "Device", "Location"],
        "patient": ["Patient"],
        "encounter": ["Encounter"],
        "performer": ["Practitioner", "PractitionerRole", "Organization"],
    },
    "Condition": {
        "subject": ["Patient"],
        "patient": ["Patient"],
        "encounter": ["Encounter"],
    },
}


class AdvancedSearchService:
    """
    Advanced FHIR Search Service.

    Implements comprehensive search functionality including:
    - All FHIR search parameter types
    - Chained and reverse-chained searches
    - _include and _revinclude
    - Search modifiers and prefixes
    """

    def __init__(self, repository):
        """
        Initialize the search service.

        Args:
            repository: FHIR repository for data access
        """
        self.repository = repository

    def parse_search_parameters(
        self,
        resource_type: str,
        query_params: Dict[str, Any]
    ) -> Tuple[List[SearchParameter], Dict[str, Any]]:
        """
        Parse FHIR search parameters from query string.

        Args:
            resource_type: Type of FHIR resource
            query_params: Raw query parameters

        Returns:
            Tuple of (parsed search parameters, control parameters)
        """
        search_params = []
        control_params = {
            "_count": 20,
            "_offset": 0,
            "_sort": None,
            "_include": [],
            "_revinclude": [],
            "_total": "none",
            "_elements": None,
            "_summary": None,
        }

        for key, value in query_params.items():
            # Handle control parameters
            if key == "_count":
                control_params["_count"] = min(int(value), 100)
                continue
            elif key == "_offset":
                control_params["_offset"] = max(int(value), 0)
                continue
            elif key == "_sort":
                control_params["_sort"] = value
                continue
            elif key == "_include":
                if isinstance(value, list):
                    for v in value:
                        control_params["_include"].append(self._parse_include(v))
                else:
                    control_params["_include"].append(self._parse_include(value))
                continue
            elif key == "_revinclude":
                if isinstance(value, list):
                    for v in value:
                        control_params["_revinclude"].append(self._parse_include(v))
                else:
                    control_params["_revinclude"].append(self._parse_include(value))
                continue
            elif key == "_total":
                control_params["_total"] = value
                continue
            elif key == "_elements":
                control_params["_elements"] = value.split(",")
                continue
            elif key == "_summary":
                control_params["_summary"] = value
                continue

            # Parse search parameter
            parsed = self._parse_single_parameter(resource_type, key, value)
            if parsed:
                search_params.append(parsed)

        return search_params, control_params

    def _parse_single_parameter(
        self,
        resource_type: str,
        key: str,
        value: Any
    ) -> Optional[SearchParameter]:
        """Parse a single search parameter."""
        # Handle _has (reverse chaining)
        if key.startswith("_has:"):
            return self._parse_has_parameter(key, value)

        # Check for modifier
        modifier = None
        param_name = key
        if ":" in key:
            parts = key.split(":")
            param_name = parts[0]
            modifier_str = parts[1]
            try:
                modifier = SearchModifier(modifier_str)
            except ValueError:
                # Might be a type modifier for reference
                pass

        # Check for chaining (e.g., patient.name)
        chain = []
        if "." in param_name:
            parts = param_name.split(".")
            param_name = parts[0]
            chain = parts[1:]

        # Get parameter type from definitions
        param_type = SearchParamType.STRING
        resource_params = SEARCH_PARAM_DEFINITIONS.get(resource_type, {})
        if param_name in resource_params:
            param_type = resource_params[param_name]

        # Parse value with prefix for date/number/quantity
        prefix = None
        parsed_value = value
        if param_type in [SearchParamType.DATE, SearchParamType.NUMBER, SearchParamType.QUANTITY]:
            prefix, parsed_value = self._parse_prefix(value)

        return SearchParameter(
            name=param_name,
            value=parsed_value,
            modifier=modifier,
            prefix=prefix,
            chain=chain,
            param_type=param_type
        )

    def _parse_has_parameter(self, key: str, value: Any) -> SearchParameter:
        """Parse a _has reverse chain parameter."""
        # Format: _has:ResourceType:searchParam:value
        # Example: _has:Observation:patient:code=85354-9
        parts = key.split(":")
        if len(parts) < 3:
            raise ValueError(f"Invalid _has parameter: {key}")

        target_type = parts[1]
        chain_param = parts[2]

        return SearchParameter(
            name="_has",
            value=value,
            chain=[target_type, chain_param],
            param_type=SearchParamType.SPECIAL
        )

    def _parse_include(self, value: str) -> IncludeParameter:
        """Parse an _include or _revinclude parameter."""
        # Format: ResourceType:searchParam[:targetType]
        # Example: Patient:general-practitioner:Practitioner
        parts = value.split(":")
        if len(parts) < 2:
            raise ValueError(f"Invalid include parameter: {value}")

        return IncludeParameter(
            source_type=parts[0],
            search_param=parts[1],
            target_type=parts[2] if len(parts) > 2 else None,
            iterate=":iterate" in value
        )

    def _parse_prefix(self, value: str) -> Tuple[Optional[SearchPrefix], str]:
        """Parse comparison prefix from value."""
        for prefix in SearchPrefix:
            if value.startswith(prefix.value):
                return prefix, value[2:]
        return None, value

    def search(
        self,
        tenant_id: UUID,
        resource_type: str,
        query_params: Dict[str, Any]
    ) -> SearchResult:
        """
        Execute a FHIR search.

        Args:
            tenant_id: Tenant identifier
            resource_type: Type of FHIR resource
            query_params: Search query parameters

        Returns:
            SearchResult with matching resources and includes
        """
        # Parse parameters
        search_params, control_params = self.parse_search_parameters(
            resource_type, query_params
        )

        # Build and execute search
        resources, total = self._execute_search(
            tenant_id,
            resource_type,
            search_params,
            control_params
        )

        # Apply _include and _revinclude
        included = []
        if control_params["_include"]:
            included.extend(
                self._resolve_includes(
                    tenant_id, resources, control_params["_include"]
                )
            )
        if control_params["_revinclude"]:
            included.extend(
                self._resolve_revincludes(
                    tenant_id, resource_type, resources, control_params["_revinclude"]
                )
            )

        return SearchResult(
            resources=resources,
            total=total,
            included_resources=included
        )

    def _execute_search(
        self,
        tenant_id: UUID,
        resource_type: str,
        search_params: List[SearchParameter],
        control_params: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Execute the search query."""
        # Build filter conditions
        filters = []
        for param in search_params:
            filter_condition = self._build_filter(resource_type, param)
            if filter_condition:
                filters.append(filter_condition)

        # Execute search using repository
        return self.repository.search_with_filters(
            tenant_id=tenant_id,
            resource_type=resource_type,
            filters=filters,
            limit=control_params["_count"],
            offset=control_params["_offset"],
            sort=control_params["_sort"]
        )

    def _build_filter(
        self,
        resource_type: str,
        param: SearchParameter
    ) -> Optional[Dict[str, Any]]:
        """Build a filter condition for a search parameter."""
        if param.name == "_has":
            return self._build_has_filter(resource_type, param)

        if param.chain:
            return self._build_chain_filter(resource_type, param)

        # Build filter based on parameter type
        if param.param_type == SearchParamType.STRING:
            return self._build_string_filter(param)
        elif param.param_type == SearchParamType.TOKEN:
            return self._build_token_filter(param)
        elif param.param_type == SearchParamType.DATE:
            return self._build_date_filter(param)
        elif param.param_type == SearchParamType.NUMBER:
            return self._build_number_filter(param)
        elif param.param_type == SearchParamType.REFERENCE:
            return self._build_reference_filter(param)
        elif param.param_type == SearchParamType.QUANTITY:
            return self._build_quantity_filter(param)
        elif param.param_type == SearchParamType.URI:
            return self._build_uri_filter(param)

        return None

    def _build_string_filter(self, param: SearchParameter) -> Dict[str, Any]:
        """Build filter for string search parameter."""
        value = param.value

        if param.modifier == SearchModifier.EXACT:
            return {
                "type": "string_exact",
                "field": param.name,
                "value": value
            }
        elif param.modifier == SearchModifier.CONTAINS:
            return {
                "type": "string_contains",
                "field": param.name,
                "value": value
            }
        elif param.modifier == SearchModifier.MISSING:
            return {
                "type": "missing",
                "field": param.name,
                "value": value.lower() == "true"
            }
        else:
            # Default: case-insensitive starts with
            return {
                "type": "string_startswith",
                "field": param.name,
                "value": value
            }

    def _build_token_filter(self, param: SearchParameter) -> Dict[str, Any]:
        """Build filter for token search parameter."""
        value = param.value

        # Parse system|code format
        system = None
        code = value
        if "|" in value:
            parts = value.split("|")
            system = parts[0] if parts[0] else None
            code = parts[1] if len(parts) > 1 else None

        if param.modifier == SearchModifier.NOT:
            return {
                "type": "token_not",
                "field": param.name,
                "system": system,
                "code": code
            }
        elif param.modifier == SearchModifier.TEXT:
            return {
                "type": "token_text",
                "field": param.name,
                "value": code
            }
        elif param.modifier == SearchModifier.OF_TYPE:
            return {
                "type": "token_of_type",
                "field": param.name,
                "system": system,
                "code": code
            }
        else:
            return {
                "type": "token",
                "field": param.name,
                "system": system,
                "code": code
            }

    def _build_date_filter(self, param: SearchParameter) -> Dict[str, Any]:
        """Build filter for date search parameter."""
        value = param.value
        prefix = param.prefix or SearchPrefix.EQ

        return {
            "type": "date",
            "field": param.name,
            "value": value,
            "prefix": prefix.value
        }

    def _build_number_filter(self, param: SearchParameter) -> Dict[str, Any]:
        """Build filter for number search parameter."""
        value = param.value
        prefix = param.prefix or SearchPrefix.EQ

        return {
            "type": "number",
            "field": param.name,
            "value": float(value),
            "prefix": prefix.value
        }

    def _build_reference_filter(self, param: SearchParameter) -> Dict[str, Any]:
        """Build filter for reference search parameter."""
        value = param.value

        # Parse reference value (can be just ID or Type/ID)
        reference_type = None
        reference_id = value
        if "/" in value:
            parts = value.split("/")
            reference_type = parts[0]
            reference_id = parts[1]

        if param.modifier == SearchModifier.IDENTIFIER:
            # Search by identifier in referenced resource
            return {
                "type": "reference_identifier",
                "field": param.name,
                "value": value
            }
        else:
            return {
                "type": "reference",
                "field": param.name,
                "reference_type": reference_type,
                "reference_id": reference_id
            }

    def _build_quantity_filter(self, param: SearchParameter) -> Dict[str, Any]:
        """Build filter for quantity search parameter."""
        value = param.value
        prefix = param.prefix or SearchPrefix.EQ

        # Parse value|system|code format
        parts = value.split("|")
        quantity_value = float(parts[0])
        system = parts[1] if len(parts) > 1 else None
        code = parts[2] if len(parts) > 2 else None

        return {
            "type": "quantity",
            "field": param.name,
            "value": quantity_value,
            "system": system,
            "code": code,
            "prefix": prefix.value
        }

    def _build_uri_filter(self, param: SearchParameter) -> Dict[str, Any]:
        """Build filter for URI search parameter."""
        value = param.value

        if param.modifier == SearchModifier.ABOVE:
            return {
                "type": "uri_above",
                "field": param.name,
                "value": value
            }
        elif param.modifier == SearchModifier.BELOW:
            return {
                "type": "uri_below",
                "field": param.name,
                "value": value
            }
        else:
            return {
                "type": "uri",
                "field": param.name,
                "value": value
            }

    def _build_chain_filter(
        self,
        resource_type: str,
        param: SearchParameter
    ) -> Dict[str, Any]:
        """Build filter for chained search parameter."""
        return {
            "type": "chain",
            "source_field": param.name,
            "chain": param.chain,
            "value": param.value,
            "modifier": param.modifier.value if param.modifier else None
        }

    def _build_has_filter(
        self,
        resource_type: str,
        param: SearchParameter
    ) -> Dict[str, Any]:
        """Build filter for _has reverse chain parameter."""
        target_type = param.chain[0]
        chain_param = param.chain[1]

        # Parse the target search parameter
        target_param, target_value = param.value.split("=", 1) if "=" in str(param.value) else (chain_param, param.value)

        return {
            "type": "has",
            "target_type": target_type,
            "link_param": chain_param,
            "target_param": target_param,
            "target_value": target_value
        }

    def _resolve_includes(
        self,
        tenant_id: UUID,
        resources: List[Dict[str, Any]],
        includes: List[IncludeParameter]
    ) -> List[Dict[str, Any]]:
        """Resolve _include parameters to fetch related resources."""
        included = []
        seen_ids: Set[str] = set()

        for include in includes:
            for resource in resources:
                if resource.get("resourceType") != include.source_type:
                    continue

                # Get reference from the search parameter field
                refs = self._get_references_from_resource(
                    resource, include.search_param
                )

                for ref in refs:
                    # Parse reference
                    ref_type, ref_id = self._parse_reference(ref)

                    # Apply target type filter
                    if include.target_type and ref_type != include.target_type:
                        continue

                    # Avoid duplicates
                    key = f"{ref_type}/{ref_id}"
                    if key in seen_ids:
                        continue
                    seen_ids.add(key)

                    # Fetch referenced resource
                    referenced = self.repository.get_by_id(
                        tenant_id=tenant_id,
                        resource_type=ref_type,
                        resource_id=ref_id
                    )

                    if referenced:
                        included.append(referenced)

        return included

    def _resolve_revincludes(
        self,
        tenant_id: UUID,
        resource_type: str,
        resources: List[Dict[str, Any]],
        revincludes: List[IncludeParameter]
    ) -> List[Dict[str, Any]]:
        """Resolve _revinclude parameters to fetch resources that reference these."""
        included = []
        resource_ids = [r.get("id") for r in resources]

        for revinclude in revincludes:
            # Search for resources of source_type that reference our resources
            for resource_id in resource_ids:
                reference_value = f"{resource_type}/{resource_id}"

                # Search for referencing resources
                referencing = self.repository.search(
                    tenant_id=tenant_id,
                    resource_type=revinclude.source_type,
                    search_params={
                        revinclude.search_param: reference_value
                    },
                    limit=100,
                    offset=0
                )

                for entry in referencing.get("entry", []):
                    included.append(entry.get("resource"))

        return included

    def _get_references_from_resource(
        self,
        resource: Dict[str, Any],
        field_name: str
    ) -> List[str]:
        """Extract reference values from a resource field."""
        references = []

        # Map search param names to actual field paths
        field_mapping = {
            "patient": "subject",
            "general-practitioner": "generalPractitioner",
            "service-provider": "serviceProvider",
        }

        actual_field = field_mapping.get(field_name, field_name)

        # Handle different field structures
        value = resource.get(actual_field)
        if not value:
            return references

        # Single reference
        if isinstance(value, dict) and "reference" in value:
            references.append(value["reference"])

        # Array of references
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    if "reference" in item:
                        references.append(item["reference"])
                    elif "individual" in item and "reference" in item["individual"]:
                        references.append(item["individual"]["reference"])

        return references

    def _parse_reference(self, reference: str) -> Tuple[str, str]:
        """Parse a reference string into type and ID."""
        if "/" in reference:
            parts = reference.split("/")
            return parts[-2], parts[-1]
        return "", reference


class SearchQueryBuilder:
    """
    Builds SQL queries for FHIR searches.

    Translates search filters into PostgreSQL JSONB queries.
    """

    def __init__(self, base_model):
        """
        Initialize the query builder.

        Args:
            base_model: SQLAlchemy model class for FHIR resources
        """
        self.model = base_model

    def build_query_conditions(
        self,
        filters: List[Dict[str, Any]]
    ) -> List:
        """
        Build SQLAlchemy filter conditions from search filters.

        Args:
            filters: List of filter specifications

        Returns:
            List of SQLAlchemy filter conditions
        """
        conditions = []

        for filter_spec in filters:
            filter_type = filter_spec.get("type")

            if filter_type == "string_startswith":
                conditions.append(
                    self._build_string_startswith(filter_spec)
                )
            elif filter_type == "string_exact":
                conditions.append(
                    self._build_string_exact(filter_spec)
                )
            elif filter_type == "string_contains":
                conditions.append(
                    self._build_string_contains(filter_spec)
                )
            elif filter_type == "token":
                conditions.append(
                    self._build_token(filter_spec)
                )
            elif filter_type == "token_not":
                conditions.append(
                    not_(self._build_token(filter_spec))
                )
            elif filter_type == "date":
                conditions.append(
                    self._build_date(filter_spec)
                )
            elif filter_type == "number":
                conditions.append(
                    self._build_number(filter_spec)
                )
            elif filter_type == "reference":
                conditions.append(
                    self._build_reference(filter_spec)
                )
            elif filter_type == "quantity":
                conditions.append(
                    self._build_quantity(filter_spec)
                )
            elif filter_type == "missing":
                conditions.append(
                    self._build_missing(filter_spec)
                )

        return conditions

    def _build_string_startswith(self, spec: Dict[str, Any]):
        """Build case-insensitive starts-with condition."""
        field = spec["field"]
        value = spec["value"].lower()

        # Search in JSONB field
        return func.lower(
            self.model.resource_data[field].astext
        ).startswith(value)

    def _build_string_exact(self, spec: Dict[str, Any]):
        """Build exact string match condition."""
        field = spec["field"]
        value = spec["value"]

        return self.model.resource_data[field].astext == value

    def _build_string_contains(self, spec: Dict[str, Any]):
        """Build contains string condition."""
        field = spec["field"]
        value = spec["value"].lower()

        return func.lower(
            self.model.resource_data[field].astext
        ).contains(value)

    def _build_token(self, spec: Dict[str, Any]):
        """Build token search condition."""
        field = spec["field"]
        system = spec.get("system")
        code = spec.get("code")

        if field == "_id":
            return self.model.fhir_id == code

        # For tokens, search in the search_tokens JSONB column
        if system and code:
            # Match system|code
            return self.model.search_tokens[field].astext.contains(f"{system}|{code}")
        elif code:
            # Match code only
            return self.model.search_tokens[field].astext.contains(code)
        else:
            return None

    def _build_date(self, spec: Dict[str, Any]):
        """Build date comparison condition."""
        field = spec["field"]
        value = spec["value"]
        prefix = spec.get("prefix", "eq")

        date_field = self.model.resource_data[field].astext

        if prefix == "eq":
            return date_field == value
        elif prefix == "ne":
            return date_field != value
        elif prefix == "gt":
            return date_field > value
        elif prefix == "lt":
            return date_field < value
        elif prefix == "ge":
            return date_field >= value
        elif prefix == "le":
            return date_field <= value
        else:
            return date_field == value

    def _build_number(self, spec: Dict[str, Any]):
        """Build number comparison condition."""
        field = spec["field"]
        value = spec["value"]
        prefix = spec.get("prefix", "eq")

        # Cast JSONB to numeric
        num_field = self.model.resource_data[field].cast(func.numeric)

        if prefix == "eq":
            return num_field == value
        elif prefix == "ne":
            return num_field != value
        elif prefix == "gt":
            return num_field > value
        elif prefix == "lt":
            return num_field < value
        elif prefix == "ge":
            return num_field >= value
        elif prefix == "le":
            return num_field <= value
        else:
            return num_field == value

    def _build_reference(self, spec: Dict[str, Any]):
        """Build reference search condition."""
        field = spec["field"]
        ref_type = spec.get("reference_type")
        ref_id = spec["reference_id"]

        # Build reference string
        if ref_type:
            ref_value = f"{ref_type}/{ref_id}"
        else:
            ref_value = ref_id

        # Search in JSONB - handle both direct reference and subject.reference
        return or_(
            self.model.resource_data[field]["reference"].astext.contains(ref_value),
            self.model.resource_data[field].astext.contains(ref_value)
        )

    def _build_quantity(self, spec: Dict[str, Any]):
        """Build quantity search condition."""
        field = spec["field"]
        value = spec["value"]
        prefix = spec.get("prefix", "eq")

        # Extract value from quantity structure
        qty_value = self.model.resource_data[field]["value"].cast(func.numeric)

        if prefix == "eq":
            return qty_value == value
        elif prefix == "ne":
            return qty_value != value
        elif prefix == "gt":
            return qty_value > value
        elif prefix == "lt":
            return qty_value < value
        elif prefix == "ge":
            return qty_value >= value
        elif prefix == "le":
            return qty_value <= value
        else:
            return qty_value == value

    def _build_missing(self, spec: Dict[str, Any]):
        """Build missing field condition."""
        field = spec["field"]
        is_missing = spec["value"]

        if is_missing:
            return or_(
                self.model.resource_data[field].is_(None),
                self.model.resource_data[field].astext == ""
            )
        else:
            return and_(
                self.model.resource_data[field].isnot(None),
                self.model.resource_data[field].astext != ""
            )
