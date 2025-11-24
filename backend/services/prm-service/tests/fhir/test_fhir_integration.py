"""
FHIR Integration Tests
End-to-end tests for FHIR API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from uuid import UUID
import json

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../..")))


# Sample FHIR resources for testing
SAMPLE_PATIENT = {
    "resourceType": "Patient",
    "identifier": [
        {
            "system": "http://hospital.example.org/mrn",
            "value": "MRN123456"
        }
    ],
    "name": [
        {
            "family": "Doe",
            "given": ["John", "Michael"]
        }
    ],
    "gender": "male",
    "birthDate": "1985-03-15",
    "telecom": [
        {
            "system": "phone",
            "value": "+1-555-0123",
            "use": "home"
        }
    ]
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
                "code": "85354-9",
                "display": "Blood pressure"
            }
        ]
    },
    "valueQuantity": {
        "value": 120,
        "unit": "mm[Hg]",
        "system": "http://unitsofmeasure.org",
        "code": "mm[Hg]"
    }
}


@pytest.mark.integration
class TestFHIRAPI:
    """Integration tests for FHIR REST API"""

    def test_metadata_endpoint(self, client):
        """Test CapabilityStatement endpoint"""
        response = client.get("/api/v1/prm/fhir/metadata")

        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "CapabilityStatement"
        assert data["fhirVersion"] == "4.0.1"
        assert data["status"] == "active"

    def test_create_patient(self, client):
        """Test creating a Patient resource"""
        response = client.post(
            "/api/v1/prm/fhir/Patient",
            json=SAMPLE_PATIENT
        )

        assert response.status_code == 201
        data = response.json()
        assert data["resourceType"] == "Patient"
        assert "id" in data
        assert data["name"][0]["family"] == "Doe"

        # Check headers
        assert "Location" in response.headers
        assert "ETag" in response.headers

    def test_read_patient(self, client):
        """Test reading a Patient resource"""
        # Create a patient
        create_response = client.post(
            "/api/v1/prm/fhir/Patient",
            json=SAMPLE_PATIENT
        )
        patient_id = create_response.json()["id"]

        # Read it back
        read_response = client.get(f"/api/v1/prm/fhir/Patient/{patient_id}")

        assert read_response.status_code == 200
        data = read_response.json()
        assert data["id"] == patient_id
        assert data["resourceType"] == "Patient"

    def test_update_patient(self, client):
        """Test updating a Patient resource"""
        # Create a patient
        create_response = client.post(
            "/api/v1/prm/fhir/Patient",
            json=SAMPLE_PATIENT
        )
        patient = create_response.json()

        # Update it
        patient["name"][0]["family"] = "Smith"
        update_response = client.put(
            f"/api/v1/prm/fhir/Patient/{patient['id']}",
            json=patient
        )

        assert update_response.status_code == 200
        data = update_response.json()
        assert data["name"][0]["family"] == "Smith"
        assert data["meta"]["versionId"] == "2"

    def test_delete_patient(self, client):
        """Test deleting a Patient resource"""
        # Create a patient
        create_response = client.post(
            "/api/v1/prm/fhir/Patient",
            json=SAMPLE_PATIENT
        )
        patient_id = create_response.json()["id"]

        # Delete it
        delete_response = client.delete(f"/api/v1/prm/fhir/Patient/{patient_id}")

        assert delete_response.status_code == 204

        # Verify it's gone
        read_response = client.get(f"/api/v1/prm/fhir/Patient/{patient_id}")
        assert read_response.status_code == 404

    def test_search_patients(self, client):
        """Test searching for Patient resources"""
        # Create multiple patients
        for i in range(3):
            patient = SAMPLE_PATIENT.copy()
            patient["name"][0]["family"] = f"Smith-{i}"
            client.post("/api/v1/prm/fhir/Patient", json=patient)

        # Search
        response = client.get("/api/v1/prm/fhir/Patient")

        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Bundle"
        assert data["type"] == "searchset"
        assert data["total"] >= 3

    def test_get_history(self, client):
        """Test retrieving resource history"""
        # Create a patient
        create_response = client.post(
            "/api/v1/prm/fhir/Patient",
            json=SAMPLE_PATIENT
        )
        patient = create_response.json()

        # Update it
        patient["name"][0]["family"] = "Updated"
        client.put(f"/api/v1/prm/fhir/Patient/{patient['id']}", json=patient)

        # Get history
        history_response = client.get(
            f"/api/v1/prm/fhir/Patient/{patient['id']}/_history"
        )

        assert history_response.status_code == 200
        data = history_response.json()
        assert data["resourceType"] == "Bundle"
        assert data["type"] == "history"
        assert data["total"] >= 2

    def test_validate_resource(self, client):
        """Test resource validation"""
        response = client.post(
            "/api/v1/prm/fhir/Patient/$validate",
            json=SAMPLE_PATIENT
        )

        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "OperationOutcome"

    def test_transaction_bundle(self, client):
        """Test processing a transaction bundle"""
        bundle = {
            "resourceType": "Bundle",
            "type": "transaction",
            "entry": [
                {
                    "request": {
                        "method": "POST",
                        "url": "Patient"
                    },
                    "resource": SAMPLE_PATIENT
                },
                {
                    "request": {
                        "method": "POST",
                        "url": "Observation"
                    },
                    "resource": SAMPLE_OBSERVATION
                }
            ]
        }

        response = client.post("/api/v1/prm/fhir/", json=bundle)

        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Bundle"
        assert data["type"] == "transaction-response"
        assert len(data["entry"]) == 2

    def test_batch_bundle(self, client):
        """Test processing a batch bundle"""
        bundle = {
            "resourceType": "Bundle",
            "type": "batch",
            "entry": [
                {
                    "request": {
                        "method": "POST",
                        "url": "Patient"
                    },
                    "resource": SAMPLE_PATIENT
                }
            ]
        }

        response = client.post("/api/v1/prm/fhir/", json=bundle)

        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Bundle"
        assert data["type"] == "batch-response"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
