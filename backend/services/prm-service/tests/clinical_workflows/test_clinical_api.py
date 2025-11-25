"""
Test Clinical Workflows API
Integration tests for clinical workflows REST endpoints
"""
import pytest
from uuid import uuid4, UUID
from datetime import datetime, date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../..")))

from services.prm_service.modules.clinical_workflows.models import Base
from services.prm_service.modules.clinical_workflows.router import router
from fastapi import FastAPI


# Create test app
@pytest.fixture
def app():
    """Create a test FastAPI app"""
    test_app = FastAPI()
    test_app.include_router(router)
    return test_app


@pytest.fixture
def client(app):
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Create a test database session"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def tenant_id():
    """Test tenant ID"""
    return str(UUID("00000000-0000-0000-0000-000000000001"))


@pytest.fixture
def patient_id():
    """Test patient ID"""
    return str(UUID("00000000-0000-0000-0000-000000000002"))


@pytest.fixture
def provider_id():
    """Test provider ID"""
    return str(UUID("00000000-0000-0000-0000-000000000003"))


@pytest.fixture
def auth_headers(tenant_id):
    """Mock authentication headers"""
    return {
        "X-Tenant-ID": tenant_id,
        "Authorization": "Bearer test-token"
    }


# ============================================================================
# PRESCRIPTION API TESTS
# ============================================================================

class TestPrescriptionAPI:
    """Tests for prescription endpoints"""

    def test_create_prescription(self, client, auth_headers, patient_id, provider_id):
        """Test POST /prescriptions"""
        data = {
            "patient_id": patient_id,
            "prescriber_id": provider_id,
            "medication_name": "Amoxicillin",
            "medication_code": "RX12345",
            "rxnorm_code": "723",
            "dosage": "500mg",
            "frequency": "3 times daily",
            "route": "oral",
            "quantity": 30,
            "quantity_unit": "capsules",
            "refills_allowed": 2,
            "days_supply": 10,
            "sig": "Take 1 capsule by mouth 3 times daily",
            "drug_schedule": "non_controlled"
        }

        response = client.post(
            "/api/v1/clinical/prescriptions",
            json=data,
            headers=auth_headers
        )

        assert response.status_code in [200, 201]
        result = response.json()
        assert result["medication_name"] == "Amoxicillin"
        assert "id" in result

    def test_get_prescription(self, client, auth_headers, patient_id, provider_id):
        """Test GET /prescriptions/{id}"""
        # First create a prescription
        create_data = {
            "patient_id": patient_id,
            "prescriber_id": provider_id,
            "medication_name": "Lisinopril",
            "dosage": "10mg",
            "frequency": "once daily",
            "route": "oral",
            "quantity": 30,
            "quantity_unit": "tablets",
            "drug_schedule": "non_controlled"
        }

        create_response = client.post(
            "/api/v1/clinical/prescriptions",
            json=create_data,
            headers=auth_headers
        )

        if create_response.status_code in [200, 201]:
            prescription_id = create_response.json()["id"]

            # Get the prescription
            get_response = client.get(
                f"/api/v1/clinical/prescriptions/{prescription_id}",
                headers=auth_headers
            )

            assert get_response.status_code == 200
            assert get_response.json()["id"] == prescription_id

    def test_list_patient_prescriptions(self, client, auth_headers, patient_id):
        """Test GET /patients/{patient_id}/prescriptions"""
        response = client.get(
            f"/api/v1/clinical/patients/{patient_id}/prescriptions",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)


# ============================================================================
# LAB ORDER API TESTS
# ============================================================================

class TestLabOrderAPI:
    """Tests for lab order endpoints"""

    def test_create_lab_order(self, client, auth_headers, patient_id, provider_id):
        """Test POST /lab-orders"""
        data = {
            "patient_id": patient_id,
            "ordering_provider_id": provider_id,
            "test_name": "Complete Blood Count",
            "test_code": "CBC001",
            "loinc_code": "58410-2",
            "priority": "routine",
            "clinical_indication": "Annual exam",
            "fasting_required": False
        }

        response = client.post(
            "/api/v1/clinical/lab-orders",
            json=data,
            headers=auth_headers
        )

        assert response.status_code in [200, 201]
        result = response.json()
        assert result["test_name"] == "Complete Blood Count"

    def test_get_lab_order(self, client, auth_headers, patient_id, provider_id):
        """Test GET /lab-orders/{id}"""
        # First create an order
        create_data = {
            "patient_id": patient_id,
            "ordering_provider_id": provider_id,
            "test_name": "Metabolic Panel",
            "test_code": "BMP001",
            "priority": "routine"
        }

        create_response = client.post(
            "/api/v1/clinical/lab-orders",
            json=create_data,
            headers=auth_headers
        )

        if create_response.status_code in [200, 201]:
            order_id = create_response.json()["id"]

            get_response = client.get(
                f"/api/v1/clinical/lab-orders/{order_id}",
                headers=auth_headers
            )

            assert get_response.status_code == 200

    def test_record_lab_result(self, client, auth_headers, patient_id, provider_id):
        """Test POST /lab-orders/{id}/results"""
        # Create order first
        order_data = {
            "patient_id": patient_id,
            "ordering_provider_id": provider_id,
            "test_name": "Glucose",
            "test_code": "GLU001",
            "priority": "routine"
        }

        order_response = client.post(
            "/api/v1/clinical/lab-orders",
            json=order_data,
            headers=auth_headers
        )

        if order_response.status_code in [200, 201]:
            order_id = order_response.json()["id"]

            result_data = {
                "component_name": "Glucose",
                "component_code": "GLU",
                "value": "95",
                "value_numeric": 95.0,
                "unit": "mg/dL",
                "reference_range_low": 70.0,
                "reference_range_high": 100.0,
                "interpretation_flag": "normal"
            }

            result_response = client.post(
                f"/api/v1/clinical/lab-orders/{order_id}/results",
                json=result_data,
                headers=auth_headers
            )

            assert result_response.status_code in [200, 201]


# ============================================================================
# VITAL SIGNS API TESTS
# ============================================================================

class TestVitalSignsAPI:
    """Tests for vital signs endpoints"""

    def test_record_vital_sign(self, client, auth_headers, patient_id, provider_id):
        """Test POST /vital-signs"""
        data = {
            "patient_id": patient_id,
            "recorder_id": provider_id,
            "vital_type": "heart_rate",
            "value": 72.0,
            "unit": "bpm"
        }

        response = client.post(
            "/api/v1/clinical/vital-signs",
            json=data,
            headers=auth_headers
        )

        assert response.status_code in [200, 201]
        result = response.json()
        assert result["value"] == 72.0

    def test_record_vital_set(self, client, auth_headers, patient_id, provider_id):
        """Test POST /vital-signs/set"""
        data = {
            "vitals": [
                {"patient_id": patient_id, "recorder_id": provider_id, "vital_type": "heart_rate", "value": 72.0, "unit": "bpm"},
                {"patient_id": patient_id, "recorder_id": provider_id, "vital_type": "blood_pressure_systolic", "value": 120.0, "unit": "mmHg"},
                {"patient_id": patient_id, "recorder_id": provider_id, "vital_type": "blood_pressure_diastolic", "value": 80.0, "unit": "mmHg"},
                {"patient_id": patient_id, "recorder_id": provider_id, "vital_type": "temperature", "value": 98.6, "unit": "F"},
                {"patient_id": patient_id, "recorder_id": provider_id, "vital_type": "respiratory_rate", "value": 16.0, "unit": "breaths/min"},
                {"patient_id": patient_id, "recorder_id": provider_id, "vital_type": "oxygen_saturation", "value": 98.0, "unit": "%"}
            ]
        }

        response = client.post(
            "/api/v1/clinical/vital-signs/set",
            json=data,
            headers=auth_headers
        )

        assert response.status_code in [200, 201]

    def test_get_latest_vitals(self, client, auth_headers, patient_id):
        """Test GET /patients/{patient_id}/vital-signs/latest"""
        response = client.get(
            f"/api/v1/clinical/patients/{patient_id}/vital-signs/latest",
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_calculate_news(self, client, auth_headers, patient_id):
        """Test GET /patients/{patient_id}/vital-signs/news"""
        response = client.get(
            f"/api/v1/clinical/patients/{patient_id}/vital-signs/news",
            headers=auth_headers
        )

        # May return 200 with score or 404 if no vitals
        assert response.status_code in [200, 404]


# ============================================================================
# CARE PLAN API TESTS
# ============================================================================

class TestCarePlanAPI:
    """Tests for care plan endpoints"""

    def test_create_care_plan(self, client, auth_headers, patient_id, provider_id):
        """Test POST /care-plans"""
        data = {
            "patient_id": patient_id,
            "author_id": provider_id,
            "title": "Diabetes Management Plan",
            "description": "Comprehensive diabetes care plan",
            "category": "chronic_disease",
            "start_date": str(date.today())
        }

        response = client.post(
            "/api/v1/clinical/care-plans",
            json=data,
            headers=auth_headers
        )

        assert response.status_code in [200, 201]
        result = response.json()
        assert result["title"] == "Diabetes Management Plan"

    def test_activate_care_plan(self, client, auth_headers, patient_id, provider_id):
        """Test POST /care-plans/{id}/activate"""
        # Create plan first
        create_data = {
            "patient_id": patient_id,
            "author_id": provider_id,
            "title": "Test Care Plan",
            "category": "chronic_disease",
            "start_date": str(date.today())
        }

        create_response = client.post(
            "/api/v1/clinical/care-plans",
            json=create_data,
            headers=auth_headers
        )

        if create_response.status_code in [200, 201]:
            plan_id = create_response.json()["id"]

            activate_response = client.post(
                f"/api/v1/clinical/care-plans/{plan_id}/activate",
                headers=auth_headers
            )

            assert activate_response.status_code == 200
            assert activate_response.json()["status"] == "active"

    def test_add_goal_to_care_plan(self, client, auth_headers, patient_id, provider_id):
        """Test POST /care-plans/{id}/goals"""
        # Create plan
        plan_data = {
            "patient_id": patient_id,
            "author_id": provider_id,
            "title": "Test Plan",
            "category": "chronic_disease",
            "start_date": str(date.today())
        }

        plan_response = client.post(
            "/api/v1/clinical/care-plans",
            json=plan_data,
            headers=auth_headers
        )

        if plan_response.status_code in [200, 201]:
            plan_id = plan_response.json()["id"]

            goal_data = {
                "patient_id": patient_id,
                "description": "Reduce HbA1c to below 7%",
                "target_value": "< 7%",
                "priority": "high",
                "due_date": str(date.today() + timedelta(days=90))
            }

            goal_response = client.post(
                f"/api/v1/clinical/care-plans/{plan_id}/goals",
                json=goal_data,
                headers=auth_headers
            )

            assert goal_response.status_code in [200, 201]


# ============================================================================
# CLINICAL ALERT API TESTS
# ============================================================================

class TestClinicalAlertAPI:
    """Tests for clinical alert endpoints"""

    def test_create_alert(self, client, auth_headers, patient_id):
        """Test POST /alerts"""
        data = {
            "patient_id": patient_id,
            "title": "Drug Interaction Alert",
            "message": "Potential interaction detected",
            "severity": "high",
            "category": "drug_interaction"
        }

        response = client.post(
            "/api/v1/clinical/alerts",
            json=data,
            headers=auth_headers
        )

        assert response.status_code in [200, 201]
        result = response.json()
        assert result["title"] == "Drug Interaction Alert"

    def test_acknowledge_alert(self, client, auth_headers, patient_id, provider_id):
        """Test POST /alerts/{id}/acknowledge"""
        # Create alert first
        create_data = {
            "patient_id": patient_id,
            "title": "Test Alert",
            "message": "Test message",
            "severity": "medium",
            "category": "reminder"
        }

        create_response = client.post(
            "/api/v1/clinical/alerts",
            json=create_data,
            headers=auth_headers
        )

        if create_response.status_code in [200, 201]:
            alert_id = create_response.json()["id"]

            ack_data = {
                "acknowledged_by": provider_id,
                "notes": "Reviewed"
            }

            ack_response = client.post(
                f"/api/v1/clinical/alerts/{alert_id}/acknowledge",
                json=ack_data,
                headers=auth_headers
            )

            assert ack_response.status_code == 200
            assert ack_response.json()["acknowledged"] is True

    def test_get_active_alerts(self, client, auth_headers, patient_id):
        """Test GET /patients/{patient_id}/alerts/active"""
        response = client.get(
            f"/api/v1/clinical/patients/{patient_id}/alerts/active",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)


# ============================================================================
# DOCUMENTATION API TESTS
# ============================================================================

class TestDocumentationAPI:
    """Tests for clinical documentation endpoints"""

    def test_create_clinical_note(self, client, auth_headers, patient_id, provider_id):
        """Test POST /notes"""
        data = {
            "patient_id": patient_id,
            "author_id": provider_id,
            "note_type": "progress",
            "title": "Follow-up Visit",
            "content": "Patient presents for follow-up...",
            "format": "text"
        }

        response = client.post(
            "/api/v1/clinical/notes",
            json=data,
            headers=auth_headers
        )

        assert response.status_code in [200, 201]

    def test_sign_clinical_note(self, client, auth_headers, patient_id, provider_id):
        """Test POST /notes/{id}/sign"""
        # Create note first
        note_data = {
            "patient_id": patient_id,
            "author_id": provider_id,
            "note_type": "progress",
            "title": "Test Note",
            "content": "Test content"
        }

        create_response = client.post(
            "/api/v1/clinical/notes",
            json=note_data,
            headers=auth_headers
        )

        if create_response.status_code in [200, 201]:
            note_id = create_response.json()["id"]

            sign_data = {"signer_id": provider_id}

            sign_response = client.post(
                f"/api/v1/clinical/notes/{note_id}/sign",
                json=sign_data,
                headers=auth_headers
            )

            assert sign_response.status_code == 200


# ============================================================================
# DISCHARGE API TESTS
# ============================================================================

class TestDischargeAPI:
    """Tests for discharge management endpoints"""

    def test_create_discharge_record(self, client, auth_headers, patient_id, provider_id):
        """Test POST /discharges"""
        data = {
            "patient_id": patient_id,
            "encounter_id": str(uuid4()),
            "discharge_date": str(date.today()),
            "discharge_disposition": "home",
            "discharge_instructions": "Rest and follow up in 1 week",
            "attending_provider_id": provider_id
        }

        response = client.post(
            "/api/v1/clinical/discharges",
            json=data,
            headers=auth_headers
        )

        assert response.status_code in [200, 201]

    def test_get_discharge_checklist(self, client, auth_headers, patient_id, provider_id):
        """Test GET /discharges/{id}/checklist"""
        # Create discharge first
        discharge_data = {
            "patient_id": patient_id,
            "encounter_id": str(uuid4()),
            "discharge_date": str(date.today()),
            "discharge_disposition": "home",
            "attending_provider_id": provider_id
        }

        create_response = client.post(
            "/api/v1/clinical/discharges",
            json=discharge_data,
            headers=auth_headers
        )

        if create_response.status_code in [200, 201]:
            discharge_id = create_response.json()["id"]

            checklist_response = client.get(
                f"/api/v1/clinical/discharges/{discharge_id}/checklist",
                headers=auth_headers
            )

            assert checklist_response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
