"""
Unit Tests for Advanced FHIR Search Service

Tests for the AdvancedSearchService including:
- Search parameter parsing
- Query building
- Filter construction
- Include/revinclude resolution
"""

import pytest
from uuid import UUID
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../..")))

from services.prm_service.modules.fhir.services.advanced_search_service import (
    AdvancedSearchService,
    SearchParameter,
    SearchParamType,
    SearchModifier,
    SearchPrefix,
    IncludeParameter,
    SEARCH_PARAM_DEFINITIONS,
)


class TestSearchParameterParsing:
    """Tests for search parameter parsing"""

    def test_parse_simple_string_parameter(self):
        """Test parsing a simple string parameter"""
        service = AdvancedSearchService(None)
        params, control = service.parse_search_parameters(
            "Patient",
            {"name": "Smith"}
        )

        assert len(params) == 1
        assert params[0].name == "name"
        assert params[0].value == "Smith"
        assert params[0].modifier is None
        assert params[0].param_type == SearchParamType.STRING

    def test_parse_parameter_with_modifier(self):
        """Test parsing a parameter with modifier"""
        service = AdvancedSearchService(None)
        params, control = service.parse_search_parameters(
            "Patient",
            {"name:exact": "Smith"}
        )

        assert len(params) == 1
        assert params[0].name == "name"
        assert params[0].modifier == SearchModifier.EXACT

    def test_parse_contains_modifier(self):
        """Test parsing :contains modifier"""
        service = AdvancedSearchService(None)
        params, control = service.parse_search_parameters(
            "Patient",
            {"name:contains": "mit"}
        )

        assert params[0].modifier == SearchModifier.CONTAINS

    def test_parse_missing_modifier(self):
        """Test parsing :missing modifier"""
        service = AdvancedSearchService(None)
        params, control = service.parse_search_parameters(
            "Patient",
            {"birthdate:missing": "true"}
        )

        assert params[0].modifier == SearchModifier.MISSING
        assert params[0].value == "true"

    def test_parse_token_parameter(self):
        """Test parsing token parameter with system|code"""
        service = AdvancedSearchService(None)
        params, control = service.parse_search_parameters(
            "Patient",
            {"identifier": "http://hospital.example.org|MRN123"}
        )

        assert params[0].param_type == SearchParamType.TOKEN
        assert "|" in params[0].value

    def test_parse_date_parameter_with_prefix(self):
        """Test parsing date parameter with comparison prefix"""
        service = AdvancedSearchService(None)
        params, control = service.parse_search_parameters(
            "Patient",
            {"birthdate": "ge1980-01-01"}
        )

        assert params[0].prefix == SearchPrefix.GE
        assert params[0].value == "1980-01-01"

    def test_parse_multiple_parameters(self):
        """Test parsing multiple parameters"""
        service = AdvancedSearchService(None)
        params, control = service.parse_search_parameters(
            "Patient",
            {
                "name": "Smith",
                "birthdate": "1980-01-01",
                "gender": "male"
            }
        )

        assert len(params) == 3

    def test_parse_control_parameters(self):
        """Test parsing control parameters"""
        service = AdvancedSearchService(None)
        params, control = service.parse_search_parameters(
            "Patient",
            {
                "_count": "50",
                "_offset": "10",
                "_sort": "birthdate"
            }
        )

        assert len(params) == 0
        assert control["_count"] == 50
        assert control["_offset"] == 10
        assert control["_sort"] == "birthdate"

    def test_parse_chained_parameter(self):
        """Test parsing chained parameter"""
        service = AdvancedSearchService(None)
        params, control = service.parse_search_parameters(
            "Observation",
            {"subject.name": "Smith"}
        )

        assert params[0].name == "subject"
        assert params[0].chain == ["name"]

    def test_parse_deep_chained_parameter(self):
        """Test parsing deep chained parameter"""
        service = AdvancedSearchService(None)
        params, control = service.parse_search_parameters(
            "Observation",
            {"subject.organization.name": "Hospital"}
        )

        assert params[0].name == "subject"
        assert params[0].chain == ["organization", "name"]


class TestIncludeParameterParsing:
    """Tests for _include/_revinclude parameter parsing"""

    def test_parse_include(self):
        """Test parsing _include parameter"""
        service = AdvancedSearchService(None)
        params, control = service.parse_search_parameters(
            "Observation",
            {"_include": "Observation:patient"}
        )

        assert len(control["_include"]) == 1
        include = control["_include"][0]
        assert include.source_type == "Observation"
        assert include.search_param == "patient"

    def test_parse_include_with_target(self):
        """Test parsing _include with target type"""
        service = AdvancedSearchService(None)
        params, control = service.parse_search_parameters(
            "Observation",
            {"_include": "Observation:performer:Practitioner"}
        )

        include = control["_include"][0]
        assert include.target_type == "Practitioner"

    def test_parse_revinclude(self):
        """Test parsing _revinclude parameter"""
        service = AdvancedSearchService(None)
        params, control = service.parse_search_parameters(
            "Patient",
            {"_revinclude": "Observation:patient"}
        )

        assert len(control["_revinclude"]) == 1
        revinclude = control["_revinclude"][0]
        assert revinclude.source_type == "Observation"
        assert revinclude.search_param == "patient"

    def test_parse_multiple_includes(self):
        """Test parsing multiple _include parameters"""
        service = AdvancedSearchService(None)
        params, control = service.parse_search_parameters(
            "Observation",
            {
                "_include": [
                    "Observation:patient",
                    "Observation:encounter"
                ]
            }
        )

        assert len(control["_include"]) == 2


class TestHasParameterParsing:
    """Tests for _has reverse chaining parameter"""

    def test_parse_has_parameter(self):
        """Test parsing _has parameter"""
        service = AdvancedSearchService(None)
        params, control = service.parse_search_parameters(
            "Patient",
            {"_has:Observation:patient:code": "8867-4"}
        )

        assert len(params) == 1
        assert params[0].name == "_has"
        assert params[0].chain == ["Observation", "patient"]
        assert params[0].value == "8867-4"


class TestFilterBuilding:
    """Tests for filter construction"""

    def test_build_string_filter(self):
        """Test building string filter"""
        service = AdvancedSearchService(None)
        param = SearchParameter(
            name="name",
            value="Smith",
            param_type=SearchParamType.STRING
        )

        filter_spec = service._build_string_filter(param)

        assert filter_spec["type"] == "string_startswith"
        assert filter_spec["field"] == "name"
        assert filter_spec["value"] == "Smith"

    def test_build_string_exact_filter(self):
        """Test building exact string filter"""
        service = AdvancedSearchService(None)
        param = SearchParameter(
            name="name",
            value="Smith",
            modifier=SearchModifier.EXACT,
            param_type=SearchParamType.STRING
        )

        filter_spec = service._build_string_filter(param)

        assert filter_spec["type"] == "string_exact"

    def test_build_token_filter(self):
        """Test building token filter"""
        service = AdvancedSearchService(None)
        param = SearchParameter(
            name="gender",
            value="male",
            param_type=SearchParamType.TOKEN
        )

        filter_spec = service._build_token_filter(param)

        assert filter_spec["type"] == "token"
        assert filter_spec["code"] == "male"
        assert filter_spec["system"] is None

    def test_build_token_filter_with_system(self):
        """Test building token filter with system"""
        service = AdvancedSearchService(None)
        param = SearchParameter(
            name="identifier",
            value="http://hospital.org|MRN123",
            param_type=SearchParamType.TOKEN
        )

        filter_spec = service._build_token_filter(param)

        assert filter_spec["system"] == "http://hospital.org"
        assert filter_spec["code"] == "MRN123"

    def test_build_date_filter(self):
        """Test building date filter"""
        service = AdvancedSearchService(None)
        param = SearchParameter(
            name="birthdate",
            value="1980-01-01",
            prefix=SearchPrefix.GE,
            param_type=SearchParamType.DATE
        )

        filter_spec = service._build_date_filter(param)

        assert filter_spec["type"] == "date"
        assert filter_spec["prefix"] == "ge"
        assert filter_spec["value"] == "1980-01-01"

    def test_build_reference_filter(self):
        """Test building reference filter"""
        service = AdvancedSearchService(None)
        param = SearchParameter(
            name="subject",
            value="Patient/123",
            param_type=SearchParamType.REFERENCE
        )

        filter_spec = service._build_reference_filter(param)

        assert filter_spec["type"] == "reference"
        assert filter_spec["reference_type"] == "Patient"
        assert filter_spec["reference_id"] == "123"

    def test_build_quantity_filter(self):
        """Test building quantity filter"""
        service = AdvancedSearchService(None)
        param = SearchParameter(
            name="value-quantity",
            value="120||mm[Hg]",
            prefix=SearchPrefix.LT,
            param_type=SearchParamType.QUANTITY
        )

        filter_spec = service._build_quantity_filter(param)

        assert filter_spec["type"] == "quantity"
        assert filter_spec["value"] == 120.0
        assert filter_spec["prefix"] == "lt"


class TestSearchParamDefinitions:
    """Tests for search parameter definitions"""

    def test_patient_params_defined(self):
        """Test that Patient search params are defined"""
        assert "Patient" in SEARCH_PARAM_DEFINITIONS
        patient_params = SEARCH_PARAM_DEFINITIONS["Patient"]

        assert "identifier" in patient_params
        assert "name" in patient_params
        assert "birthdate" in patient_params
        assert "gender" in patient_params

    def test_observation_params_defined(self):
        """Test that Observation search params are defined"""
        assert "Observation" in SEARCH_PARAM_DEFINITIONS
        obs_params = SEARCH_PARAM_DEFINITIONS["Observation"]

        assert "code" in obs_params
        assert "subject" in obs_params
        assert "date" in obs_params

    def test_param_types_correct(self):
        """Test that parameter types are correct"""
        patient_params = SEARCH_PARAM_DEFINITIONS["Patient"]

        assert patient_params["identifier"] == SearchParamType.TOKEN
        assert patient_params["name"] == SearchParamType.STRING
        assert patient_params["birthdate"] == SearchParamType.DATE
        assert patient_params["general-practitioner"] == SearchParamType.REFERENCE


class TestReferenceExtraction:
    """Tests for reference extraction from resources"""

    def test_extract_single_reference(self):
        """Test extracting a single reference"""
        service = AdvancedSearchService(None)
        resource = {
            "resourceType": "Observation",
            "subject": {"reference": "Patient/123"}
        }

        refs = service._get_references_from_resource(resource, "subject")

        assert len(refs) == 1
        assert refs[0] == "Patient/123"

    def test_extract_array_reference(self):
        """Test extracting references from array"""
        service = AdvancedSearchService(None)
        resource = {
            "resourceType": "Patient",
            "generalPractitioner": [
                {"reference": "Practitioner/1"},
                {"reference": "Practitioner/2"}
            ]
        }

        refs = service._get_references_from_resource(
            resource, "general-practitioner"
        )

        assert len(refs) == 2

    def test_extract_no_reference(self):
        """Test extracting from field with no reference"""
        service = AdvancedSearchService(None)
        resource = {
            "resourceType": "Patient",
            "name": [{"family": "Smith"}]
        }

        refs = service._get_references_from_resource(resource, "subject")

        assert len(refs) == 0


class TestReferenceParsing:
    """Tests for reference string parsing"""

    def test_parse_typed_reference(self):
        """Test parsing typed reference"""
        service = AdvancedSearchService(None)
        ref_type, ref_id = service._parse_reference("Patient/123")

        assert ref_type == "Patient"
        assert ref_id == "123"

    def test_parse_url_reference(self):
        """Test parsing URL reference"""
        service = AdvancedSearchService(None)
        ref_type, ref_id = service._parse_reference(
            "http://example.org/fhir/Patient/123"
        )

        assert ref_type == "Patient"
        assert ref_id == "123"

    def test_parse_simple_id(self):
        """Test parsing simple ID without type"""
        service = AdvancedSearchService(None)
        ref_type, ref_id = service._parse_reference("123")

        assert ref_type == ""
        assert ref_id == "123"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
