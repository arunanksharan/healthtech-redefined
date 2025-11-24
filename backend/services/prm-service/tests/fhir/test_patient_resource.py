"""Tests for FHIR Patient Resource"""
import pytest
from datetime import date
from modules.fhir.models import Patient, HumanName


class TestPatientResource:
    def test_create_minimal_patient(self):
        """Test creating minimal patient"""
        patient = Patient(resourceType="Patient", id="example-001")
        assert patient.resourceType == "Patient"
        assert patient.id == "example-001"

    def test_create_complete_patient(self):
        """Test creating complete patient"""
        patient = Patient(
            resourceType="Patient",
            id="example-002",
            active=True,
            name=[HumanName(use="official", family="Smith", given=["John"])],
            gender="male",
            birthDate=date(1990, 1, 15)
        )
        assert patient.name[0].family == "Smith"
