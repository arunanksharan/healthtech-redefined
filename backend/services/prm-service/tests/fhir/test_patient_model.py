"""
Unit tests for FHIR Patient resource model
"""
import pytest
from datetime import date, datetime
from pydantic import ValidationError

from modules.fhir.models import Patient, HumanName, ContactPoint, Address, Identifier


class TestPatientModel:
    """Test suite for Patient FHIR resource"""
    
    def test_minimal_patient(self):
        """Test creating a minimal patient"""
        patient = Patient(
            resourceType="Patient"
        )
        
        assert patient.resourceType == "Patient"
        assert patient.id is None
        assert patient.name is None
    
    def test_patient_with_basic_demographics(self):
        """Test patient with basic demographic information"""
        patient = Patient(
            resourceType="Patient",
            id="example-123",
            name=[
                HumanName(
                    use="official",
                    family="Smith",
                    given=["John", "Michael"]
                )
            ],
            gender="male",
            birthDate=date(1974, 12, 25)
        )
        
        assert patient.id == "example-123"
        assert len(patient.name) == 1
        assert patient.name[0].family == "Smith"
        assert patient.gender == "male"
        assert patient.birthDate == date(1974, 12, 25)
    
    def test_patient_with_identifiers(self):
        """Test patient with multiple identifiers"""
        patient = Patient(
            resourceType="Patient",
            identifier=[
                Identifier(
                    use="official",
                    system="http://hospital.org/patients",
                    value="MRN123456"
                ),
                Identifier(
                    use="secondary",
                    system="http://hl7.org/fhir/sid/us-ssn",
                    value="123-45-6789"
                )
            ]
        )
        
        assert len(patient.identifier) == 2
        assert patient.identifier[0].value == "MRN123456"
        assert patient.identifier[1].system == "http://hl7.org/fhir/sid/us-ssn"
    
    def test_patient_with_contact(self):
        """Test patient with contact information"""
        patient = Patient(
            resourceType="Patient",
            telecom=[
                ContactPoint(
                    system="phone",
                    value="+1-555-1234",
                    use="mobile",
                    rank=1
                ),
                ContactPoint(
                    system="email",
                    value="john.smith@example.com",
                    use="home"
                )
            ]
        )
        
        assert len(patient.telecom) == 2
        assert patient.telecom[0].system == "phone"
        assert patient.telecom[1].system == "email"
    
    def test_patient_with_address(self):
        """Test patient with address"""
        patient = Patient(
            resourceType="Patient",
            address=[
                Address(
                    use="home",
                    type="physical",
                    line=["123 Main Street", "Apt 4B"],
                    city="Springfield",
                    state="IL",
                    postalCode="62701",
                    country="US"
                )
            ]
        )
        
        assert len(patient.address) == 1
        assert patient.address[0].city == "Springfield"
        assert len(patient.address[0].line) == 2
    
    def test_patient_birth_date_validation(self):
        """Test that birth date cannot be in the future"""
        future_date = date(2030, 1, 1)
        
        with pytest.raises(ValidationError) as exc_info:
            Patient(
                resourceType="Patient",
                birthDate=future_date
            )
        
        assert "Birth date cannot be in the future" in str(exc_info.value)
    
    def test_patient_deceased_validation(self):
        """Test deceased date validation"""
        with pytest.raises(ValidationError) as exc_info:
            Patient(
                resourceType="Patient",
                birthDate=date(1980, 1, 1),
                deceasedDateTime=datetime(1970, 1, 1, 0, 0, 0)
            )
        
        assert "Deceased date cannot be before birth date" in str(exc_info.value)
    
    def test_patient_serialization(self):
        """Test patient serialization to dict"""
        patient = Patient(
            resourceType="Patient",
            id="test-123",
            active=True,
            gender="female"
        )
        
        data = patient.dict()
        
        assert data["resourceType"] == "Patient"
        assert data["id"] == "test-123"
        assert data["active"] is True
        assert data["gender"] == "female"
        
        # Check that None values are excluded
        assert "name" not in data
        assert "birthDate" not in data
    
    def test_patient_with_meta(self):
        """Test patient with meta information"""
        from modules.fhir.models import Meta
        
        patient = Patient(
            resourceType="Patient",
            meta=Meta(
                versionId="1",
                lastUpdated=datetime(2024, 11, 24, 10, 30, 0)
            )
        )
        
        assert patient.meta.versionId == "1"
        assert patient.meta.lastUpdated.year == 2024
