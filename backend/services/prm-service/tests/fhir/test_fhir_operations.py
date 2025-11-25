"""
FHIR Operations Integration Tests

Tests for FHIR operations including:
- Patient/$everything and Encounter/$everything
- $meta, $meta-add, $meta-delete
- Terminology operations ($lookup, $expand, $validate-code, $translate)
- Subscription management
- Advanced search features
"""

import pytest
from fastapi.testclient import TestClient
from uuid import UUID, uuid4
import json
import asyncio

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../..")))


# Sample FHIR resources for testing
SAMPLE_PATIENT = {
    "resourceType": "Patient",
    "identifier": [
        {
            "system": "http://hospital.example.org/mrn",
            "value": "MRN-TEST-001"
        }
    ],
    "name": [
        {
            "family": "TestPatient",
            "given": ["Alice", "Marie"]
        }
    ],
    "gender": "female",
    "birthDate": "1990-05-20",
    "telecom": [
        {
            "system": "phone",
            "value": "+1-555-0100",
            "use": "home"
        },
        {
            "system": "email",
            "value": "alice@example.com"
        }
    ],
    "address": [
        {
            "use": "home",
            "line": ["123 Main St"],
            "city": "Boston",
            "state": "MA",
            "postalCode": "02115"
        }
    ]
}


SAMPLE_ENCOUNTER = {
    "resourceType": "Encounter",
    "status": "finished",
    "class": {
        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
        "code": "AMB",
        "display": "ambulatory"
    },
    "type": [
        {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "308335008",
                    "display": "Patient encounter procedure"
                }
            ]
        }
    ],
    "period": {
        "start": "2024-11-01T09:00:00Z",
        "end": "2024-11-01T09:30:00Z"
    }
}


SAMPLE_OBSERVATION = {
    "resourceType": "Observation",
    "status": "final",
    "category": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs"
                }
            ]
        }
    ],
    "code": {
        "coding": [
            {
                "system": "http://loinc.org",
                "code": "8867-4",
                "display": "Heart rate"
            }
        ]
    },
    "valueQuantity": {
        "value": 72,
        "unit": "/min",
        "system": "http://unitsofmeasure.org",
        "code": "/min"
    }
}


SAMPLE_CONDITION = {
    "resourceType": "Condition",
    "clinicalStatus": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                "code": "active"
            }
        ]
    },
    "verificationStatus": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                "code": "confirmed"
            }
        ]
    },
    "code": {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "38341003",
                "display": "Hypertensive disorder"
            }
        ]
    }
}


@pytest.mark.integration
class TestTerminologyOperations:
    """Tests for FHIR Terminology operations"""

    def test_codesystem_lookup(self, client):
        """Test CodeSystem $lookup operation"""
        response = client.get(
            "/api/v1/prm/fhir/CodeSystem/$lookup",
            params={
                "system": "http://loinc.org",
                "code": "8867-4"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Parameters"

        # Find the display parameter
        display_param = next(
            (p for p in data["parameter"] if p["name"] == "display"),
            None
        )
        assert display_param is not None
        assert "Heart rate" in display_param["valueString"]

    def test_codesystem_lookup_not_found(self, client):
        """Test CodeSystem $lookup for non-existent code"""
        response = client.get(
            "/api/v1/prm/fhir/CodeSystem/$lookup",
            params={
                "system": "http://loinc.org",
                "code": "invalid-code"
            }
        )

        assert response.status_code == 200
        data = response.json()

        result_param = next(
            (p for p in data["parameter"] if p["name"] == "result"),
            None
        )
        assert result_param is not None
        assert result_param["valueBoolean"] is False

    def test_valueset_expand(self, client):
        """Test ValueSet $expand operation"""
        response = client.get(
            "/api/v1/prm/fhir/ValueSet/$expand",
            params={
                "url": "http://hl7.org/fhir/ValueSet/administrative-gender"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "ValueSet"
        assert "expansion" in data
        assert len(data["expansion"]["contains"]) > 0

    def test_valueset_expand_with_filter(self, client):
        """Test ValueSet $expand with filter"""
        response = client.get(
            "/api/v1/prm/fhir/ValueSet/$expand",
            params={
                "url": "http://hl7.org/fhir/ValueSet/administrative-gender",
                "filter": "male"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Should only return concepts matching "male"
        concepts = data["expansion"]["contains"]
        assert all("male" in c["display"].lower() for c in concepts)

    def test_valueset_validate_code(self, client):
        """Test ValueSet $validate-code operation"""
        response = client.get(
            "/api/v1/prm/fhir/ValueSet/$validate-code",
            params={
                "url": "http://hl7.org/fhir/ValueSet/administrative-gender",
                "code": "male",
                "system": "http://hl7.org/fhir/administrative-gender"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Parameters"

        result_param = next(
            (p for p in data["parameter"] if p["name"] == "result"),
            None
        )
        assert result_param is not None
        assert result_param["valueBoolean"] is True

    def test_conceptmap_translate(self, client):
        """Test ConceptMap $translate operation"""
        response = client.get(
            "/api/v1/prm/fhir/ConceptMap/$translate",
            params={
                "url": "http://example.org/fhir/ConceptMap/snomed-to-icd10",
                "code": "38341003"  # Hypertensive disorder (SNOMED)
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Parameters"

        result_param = next(
            (p for p in data["parameter"] if p["name"] == "result"),
            None
        )
        assert result_param is not None
        assert result_param["valueBoolean"] is True

    def test_codesystem_subsumes(self, client):
        """Test CodeSystem $subsumes operation"""
        response = client.get(
            "/api/v1/prm/fhir/CodeSystem/$subsumes",
            params={
                "system": "http://snomed.info/sct",
                "codeA": "38341003",
                "codeB": "38341003"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Parameters"

        outcome_param = next(
            (p for p in data["parameter"] if p["name"] == "outcome"),
            None
        )
        assert outcome_param is not None
        assert outcome_param["valueCode"] == "equivalent"


@pytest.mark.integration
class TestEverythingOperations:
    """Tests for $everything operations"""

    def test_patient_everything(self, client):
        """Test Patient/$everything operation"""
        # Create a patient
        patient_response = client.post(
            "/api/v1/prm/fhir/Patient",
            json=SAMPLE_PATIENT
        )
        patient_id = patient_response.json()["id"]

        # Create an observation for the patient
        observation = SAMPLE_OBSERVATION.copy()
        observation["subject"] = {"reference": f"Patient/{patient_id}"}
        client.post("/api/v1/prm/fhir/Observation", json=observation)

        # Create a condition for the patient
        condition = SAMPLE_CONDITION.copy()
        condition["subject"] = {"reference": f"Patient/{patient_id}"}
        client.post("/api/v1/prm/fhir/Condition", json=condition)

        # Get everything
        response = client.get(f"/api/v1/prm/fhir/Patient/{patient_id}/$everything")

        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Bundle"
        assert data["type"] == "searchset"
        assert data["total"] >= 1  # At least the patient

        # Check that patient is in the bundle
        resource_types = [
            e["resource"]["resourceType"]
            for e in data["entry"]
        ]
        assert "Patient" in resource_types

    def test_patient_everything_with_type_filter(self, client):
        """Test Patient/$everything with _type filter"""
        # Create a patient
        patient_response = client.post(
            "/api/v1/prm/fhir/Patient",
            json=SAMPLE_PATIENT
        )
        patient_id = patient_response.json()["id"]

        # Get only Observation and Condition
        response = client.get(
            f"/api/v1/prm/fhir/Patient/{patient_id}/$everything",
            params={"_type": "Patient,Observation"}
        )

        assert response.status_code == 200
        data = response.json()

        # Should only include specified types
        resource_types = set(
            e["resource"]["resourceType"]
            for e in data["entry"]
        )
        assert resource_types <= {"Patient", "Observation"}

    def test_patient_everything_not_found(self, client):
        """Test Patient/$everything for non-existent patient"""
        response = client.get(
            "/api/v1/prm/fhir/Patient/non-existent-id/$everything"
        )

        assert response.status_code == 404

    def test_encounter_everything(self, client):
        """Test Encounter/$everything operation"""
        # Create a patient
        patient_response = client.post(
            "/api/v1/prm/fhir/Patient",
            json=SAMPLE_PATIENT
        )
        patient_id = patient_response.json()["id"]

        # Create an encounter for the patient
        encounter = SAMPLE_ENCOUNTER.copy()
        encounter["subject"] = {"reference": f"Patient/{patient_id}"}
        encounter_response = client.post(
            "/api/v1/prm/fhir/Encounter",
            json=encounter
        )
        encounter_id = encounter_response.json()["id"]

        # Create an observation for the encounter
        observation = SAMPLE_OBSERVATION.copy()
        observation["subject"] = {"reference": f"Patient/{patient_id}"}
        observation["encounter"] = {"reference": f"Encounter/{encounter_id}"}
        client.post("/api/v1/prm/fhir/Observation", json=observation)

        # Get everything
        response = client.get(
            f"/api/v1/prm/fhir/Encounter/{encounter_id}/$everything"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Bundle"
        assert data["type"] == "searchset"
        assert data["total"] >= 1


@pytest.mark.integration
class TestMetaOperations:
    """Tests for $meta operations"""

    def test_get_meta(self, client):
        """Test $meta operation"""
        # Create a patient
        patient_response = client.post(
            "/api/v1/prm/fhir/Patient",
            json=SAMPLE_PATIENT
        )
        patient_id = patient_response.json()["id"]

        # Get meta
        response = client.get(
            f"/api/v1/prm/fhir/Patient/{patient_id}/$meta"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Parameters"

        return_param = next(
            (p for p in data["parameter"] if p["name"] == "return"),
            None
        )
        assert return_param is not None
        assert "valueMeta" in return_param

    def test_meta_add(self, client):
        """Test $meta-add operation"""
        # Create a patient
        patient_response = client.post(
            "/api/v1/prm/fhir/Patient",
            json=SAMPLE_PATIENT
        )
        patient_id = patient_response.json()["id"]

        # Add a tag
        parameters = {
            "resourceType": "Parameters",
            "parameter": [
                {
                    "name": "meta",
                    "valueMeta": {
                        "tag": [
                            {
                                "system": "http://example.org/tags",
                                "code": "test-tag"
                            }
                        ]
                    }
                }
            ]
        }

        response = client.post(
            f"/api/v1/prm/fhir/Patient/{patient_id}/$meta-add",
            json=parameters
        )

        assert response.status_code == 200
        data = response.json()

        return_param = next(
            (p for p in data["parameter"] if p["name"] == "return"),
            None
        )
        assert return_param is not None
        meta = return_param["valueMeta"]
        assert any(t["code"] == "test-tag" for t in meta.get("tag", []))

    def test_meta_delete(self, client):
        """Test $meta-delete operation"""
        # Create a patient
        patient_response = client.post(
            "/api/v1/prm/fhir/Patient",
            json=SAMPLE_PATIENT
        )
        patient_id = patient_response.json()["id"]

        # First add a tag
        add_params = {
            "resourceType": "Parameters",
            "parameter": [
                {
                    "name": "meta",
                    "valueMeta": {
                        "tag": [
                            {
                                "system": "http://example.org/tags",
                                "code": "to-remove"
                            }
                        ]
                    }
                }
            ]
        }
        client.post(
            f"/api/v1/prm/fhir/Patient/{patient_id}/$meta-add",
            json=add_params
        )

        # Then remove it
        response = client.post(
            f"/api/v1/prm/fhir/Patient/{patient_id}/$meta-delete",
            json=add_params
        )

        assert response.status_code == 200
        data = response.json()

        return_param = next(
            (p for p in data["parameter"] if p["name"] == "return"),
            None
        )
        assert return_param is not None
        meta = return_param["valueMeta"]
        assert not any(t["code"] == "to-remove" for t in meta.get("tag", []))


@pytest.mark.integration
class TestSubscriptions:
    """Tests for FHIR Subscription management"""

    def test_create_subscription(self, client):
        """Test creating a subscription"""
        subscription = {
            "resourceType": "Subscription",
            "status": "requested",
            "criteria": "Observation?code=85354-9",
            "channel": {
                "type": "rest-hook",
                "endpoint": "https://example.org/webhook",
                "payload": "application/fhir+json"
            },
            "reason": "Test subscription"
        }

        response = client.post(
            "/api/v1/prm/fhir/Subscription",
            json=subscription
        )

        assert response.status_code == 201
        data = response.json()
        assert data["resourceType"] == "Subscription"
        assert "id" in data
        assert data["status"] in ["requested", "active"]
        assert "Location" in response.headers

    def test_get_subscription(self, client):
        """Test retrieving a subscription"""
        # Create a subscription
        subscription = {
            "resourceType": "Subscription",
            "criteria": "Patient",
            "channel": {
                "type": "rest-hook",
                "endpoint": "https://example.org/hook"
            },
            "reason": "Test"
        }

        create_response = client.post(
            "/api/v1/prm/fhir/Subscription",
            json=subscription
        )
        subscription_id = create_response.json()["id"]

        # Get it
        response = client.get(
            f"/api/v1/prm/fhir/Subscription/{subscription_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == subscription_id
        assert data["resourceType"] == "Subscription"

    def test_delete_subscription(self, client):
        """Test deleting a subscription"""
        # Create a subscription
        subscription = {
            "resourceType": "Subscription",
            "criteria": "Observation",
            "channel": {
                "type": "rest-hook",
                "endpoint": "https://example.org/hook"
            },
            "reason": "Test"
        }

        create_response = client.post(
            "/api/v1/prm/fhir/Subscription",
            json=subscription
        )
        subscription_id = create_response.json()["id"]

        # Delete it
        response = client.delete(
            f"/api/v1/prm/fhir/Subscription/{subscription_id}"
        )

        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(
            f"/api/v1/prm/fhir/Subscription/{subscription_id}"
        )
        assert get_response.status_code == 404

    def test_search_subscriptions(self, client):
        """Test searching for subscriptions"""
        # Create a few subscriptions
        for i in range(3):
            subscription = {
                "resourceType": "Subscription",
                "criteria": f"Patient?_id={i}",
                "channel": {
                    "type": "rest-hook",
                    "endpoint": f"https://example.org/hook{i}"
                },
                "reason": f"Test {i}"
            }
            client.post("/api/v1/prm/fhir/Subscription", json=subscription)

        # Search
        response = client.get("/api/v1/prm/fhir/Subscription")

        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Bundle"
        assert data["type"] == "searchset"
        assert data["total"] >= 3


@pytest.mark.integration
class TestAdvancedSearch:
    """Tests for advanced FHIR search features"""

    def test_search_with_identifier(self, client):
        """Test searching by identifier"""
        # Create a patient with unique identifier
        unique_mrn = f"MRN-{uuid4().hex[:8]}"
        patient = SAMPLE_PATIENT.copy()
        patient["identifier"][0]["value"] = unique_mrn

        client.post("/api/v1/prm/fhir/Patient", json=patient)

        # Search by identifier
        response = client.get(
            "/api/v1/prm/fhir/Patient",
            params={"identifier": unique_mrn}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    def test_search_with_name(self, client):
        """Test searching by name"""
        response = client.get(
            "/api/v1/prm/fhir/Patient",
            params={"name": "TestPatient"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Bundle"

    def test_search_with_pagination(self, client):
        """Test search pagination"""
        # Create multiple patients
        for i in range(5):
            patient = SAMPLE_PATIENT.copy()
            patient["name"][0]["family"] = f"PaginationTest-{i}"
            patient["identifier"][0]["value"] = f"MRN-PAGE-{i}"
            client.post("/api/v1/prm/fhir/Patient", json=patient)

        # Get first page
        response = client.get(
            "/api/v1/prm/fhir/Patient",
            params={"_count": 2, "_offset": 0}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["entry"]) <= 2
        assert "link" in data

    def test_search_with_date(self, client):
        """Test searching with date parameter"""
        response = client.get(
            "/api/v1/prm/fhir/Patient",
            params={"birthdate": "1990-05-20"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Bundle"

    def test_search_with_token(self, client):
        """Test searching with token parameter"""
        response = client.get(
            "/api/v1/prm/fhir/Patient",
            params={"gender": "female"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Bundle"

    def test_search_observations_by_code(self, client):
        """Test searching observations by code"""
        # Create a patient and observation
        patient_response = client.post(
            "/api/v1/prm/fhir/Patient",
            json=SAMPLE_PATIENT
        )
        patient_id = patient_response.json()["id"]

        observation = SAMPLE_OBSERVATION.copy()
        observation["subject"] = {"reference": f"Patient/{patient_id}"}
        client.post("/api/v1/prm/fhir/Observation", json=observation)

        # Search by code
        response = client.get(
            "/api/v1/prm/fhir/Observation",
            params={"code": "8867-4"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Bundle"


@pytest.mark.integration
class TestValidation:
    """Tests for resource validation"""

    def test_validate_valid_patient(self, client):
        """Test validating a valid Patient"""
        response = client.post(
            "/api/v1/prm/fhir/Patient/$validate",
            json=SAMPLE_PATIENT
        )

        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "OperationOutcome"

    def test_validate_invalid_resource(self, client):
        """Test validating an invalid resource"""
        invalid_patient = {
            "resourceType": "Patient",
            # Missing required elements
        }

        response = client.post(
            "/api/v1/prm/fhir/Patient/$validate",
            json=invalid_patient
        )

        # Should return 200 or 400 depending on severity
        assert response.status_code in [200, 400]
        data = response.json()
        assert data["resourceType"] == "OperationOutcome"

    def test_validate_observation(self, client):
        """Test validating an Observation"""
        response = client.post(
            "/api/v1/prm/fhir/Observation/$validate",
            json=SAMPLE_OBSERVATION
        )

        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "OperationOutcome"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
