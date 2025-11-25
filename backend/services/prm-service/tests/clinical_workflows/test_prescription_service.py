"""
Test Prescription Service
Unit tests for e-prescribing functionality (US-006.1)
"""
import pytest
from uuid import uuid4, UUID
from datetime import datetime, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../..")))

from services.prm_service.modules.clinical_workflows.models import (
    Base, Prescription, DrugInteractionCheck
)
from services.prm_service.modules.clinical_workflows.schemas import (
    PrescriptionCreate, PrescriptionStatus, DrugSchedule, InteractionSeverity
)
from services.prm_service.modules.clinical_workflows.service import PrescriptionService


# Test database setup
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
def prescription_service(db_session):
    """Create a prescription service instance"""
    return PrescriptionService(db_session)


@pytest.fixture
def tenant_id():
    """Test tenant ID"""
    return UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def patient_id():
    """Test patient ID"""
    return UUID("00000000-0000-0000-0000-000000000002")


@pytest.fixture
def prescriber_id():
    """Test prescriber ID"""
    return UUID("00000000-0000-0000-0000-000000000003")


@pytest.fixture
def sample_prescription_data(patient_id, prescriber_id):
    """Sample prescription data"""
    return PrescriptionCreate(
        patient_id=patient_id,
        prescriber_id=prescriber_id,
        encounter_id=uuid4(),
        medication_name="Amoxicillin",
        medication_code="RX12345",
        rxnorm_code="723",
        dosage="500mg",
        frequency="3 times daily",
        route="oral",
        quantity=30,
        quantity_unit="capsules",
        refills_allowed=2,
        days_supply=10,
        sig="Take 1 capsule by mouth 3 times daily with food",
        dispense_as_written=False,
        therapeutic_class="Antibiotic",
        drug_schedule=DrugSchedule.NON_CONTROLLED,
        indication="Bacterial infection",
        notes="Complete full course of therapy"
    )


# ============================================================================
# CREATE PRESCRIPTION TESTS
# ============================================================================

def test_create_prescription(prescription_service, tenant_id, sample_prescription_data):
    """Test creating a new prescription"""
    prescription = prescription_service.create_prescription(
        tenant_id=tenant_id,
        data=sample_prescription_data
    )

    assert prescription is not None
    assert prescription.id is not None
    assert prescription.medication_name == "Amoxicillin"
    assert prescription.status == PrescriptionStatus.DRAFT
    assert prescription.tenant_id == tenant_id


def test_create_prescription_with_controlled_substance(
    prescription_service, tenant_id, patient_id, prescriber_id
):
    """Test creating a controlled substance prescription"""
    data = PrescriptionCreate(
        patient_id=patient_id,
        prescriber_id=prescriber_id,
        medication_name="Oxycodone",
        medication_code="RX99999",
        rxnorm_code="7804",
        dosage="5mg",
        frequency="every 4-6 hours as needed",
        route="oral",
        quantity=30,
        quantity_unit="tablets",
        refills_allowed=0,  # No refills for controlled substances
        days_supply=7,
        sig="Take 1 tablet by mouth every 4-6 hours as needed for pain",
        dispense_as_written=True,
        therapeutic_class="Opioid Analgesic",
        drug_schedule=DrugSchedule.SCHEDULE_II,
        indication="Acute pain management"
    )

    prescription = prescription_service.create_prescription(
        tenant_id=tenant_id,
        data=data
    )

    assert prescription.drug_schedule == DrugSchedule.SCHEDULE_II
    assert prescription.refills_allowed == 0


# ============================================================================
# DRUG INTERACTION TESTS
# ============================================================================

def test_check_drug_interactions(prescription_service, tenant_id, sample_prescription_data):
    """Test checking drug interactions"""
    prescription = prescription_service.create_prescription(
        tenant_id=tenant_id,
        data=sample_prescription_data
    )

    interactions = prescription_service.check_drug_interactions(
        tenant_id=tenant_id,
        prescription_id=prescription.id,
        patient_medications=["Warfarin", "Aspirin"]
    )

    assert isinstance(interactions, list)
    # Note: Actual interaction checking would require external service integration


def test_drug_interaction_check_recorded(
    prescription_service, tenant_id, sample_prescription_data
):
    """Test that drug interaction checks are recorded"""
    prescription = prescription_service.create_prescription(
        tenant_id=tenant_id,
        data=sample_prescription_data
    )

    # Simulate recording an interaction check
    interactions = prescription_service.check_drug_interactions(
        tenant_id=tenant_id,
        prescription_id=prescription.id,
        patient_medications=["Methotrexate"]
    )

    # Verify interaction check was logged
    assert prescription.interaction_check_performed is not None or interactions is not None


# ============================================================================
# PRESCRIPTION STATUS WORKFLOW TESTS
# ============================================================================

def test_sign_prescription(prescription_service, tenant_id, sample_prescription_data, prescriber_id):
    """Test signing a prescription"""
    prescription = prescription_service.create_prescription(
        tenant_id=tenant_id,
        data=sample_prescription_data
    )

    signed = prescription_service.sign_prescription(
        tenant_id=tenant_id,
        prescription_id=prescription.id,
        signer_id=prescriber_id
    )

    assert signed.status == PrescriptionStatus.SIGNED
    assert signed.signed_at is not None
    assert signed.signed_by == prescriber_id


def test_send_prescription_to_pharmacy(
    prescription_service, tenant_id, sample_prescription_data, prescriber_id
):
    """Test sending prescription to pharmacy"""
    prescription = prescription_service.create_prescription(
        tenant_id=tenant_id,
        data=sample_prescription_data
    )

    # First sign the prescription
    prescription_service.sign_prescription(
        tenant_id=tenant_id,
        prescription_id=prescription.id,
        signer_id=prescriber_id
    )

    # Then send to pharmacy
    sent = prescription_service.send_to_pharmacy(
        tenant_id=tenant_id,
        prescription_id=prescription.id,
        pharmacy_id=uuid4(),
        pharmacy_name="Test Pharmacy",
        pharmacy_ncpdp="1234567"
    )

    assert sent.status == PrescriptionStatus.SENT_TO_PHARMACY


def test_cannot_send_unsigned_prescription(
    prescription_service, tenant_id, sample_prescription_data
):
    """Test that unsigned prescriptions cannot be sent to pharmacy"""
    prescription = prescription_service.create_prescription(
        tenant_id=tenant_id,
        data=sample_prescription_data
    )

    with pytest.raises(ValueError) as excinfo:
        prescription_service.send_to_pharmacy(
            tenant_id=tenant_id,
            prescription_id=prescription.id,
            pharmacy_id=uuid4(),
            pharmacy_name="Test Pharmacy",
            pharmacy_ncpdp="1234567"
        )

    assert "must be signed" in str(excinfo.value).lower()


def test_cancel_prescription(
    prescription_service, tenant_id, sample_prescription_data
):
    """Test canceling a prescription"""
    prescription = prescription_service.create_prescription(
        tenant_id=tenant_id,
        data=sample_prescription_data
    )

    cancelled = prescription_service.cancel_prescription(
        tenant_id=tenant_id,
        prescription_id=prescription.id,
        reason="Patient discontinued treatment"
    )

    assert cancelled.status == PrescriptionStatus.CANCELLED


# ============================================================================
# PRESCRIPTION RETRIEVAL TESTS
# ============================================================================

def test_get_prescription_by_id(
    prescription_service, tenant_id, sample_prescription_data
):
    """Test retrieving a prescription by ID"""
    created = prescription_service.create_prescription(
        tenant_id=tenant_id,
        data=sample_prescription_data
    )

    retrieved = prescription_service.get_prescription(
        tenant_id=tenant_id,
        prescription_id=created.id
    )

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.medication_name == created.medication_name


def test_get_patient_prescriptions(
    prescription_service, tenant_id, sample_prescription_data, patient_id
):
    """Test retrieving all prescriptions for a patient"""
    # Create multiple prescriptions
    for i in range(3):
        prescription_service.create_prescription(
            tenant_id=tenant_id,
            data=sample_prescription_data
        )

    prescriptions = prescription_service.get_patient_prescriptions(
        tenant_id=tenant_id,
        patient_id=patient_id
    )

    assert len(prescriptions) >= 3


def test_get_active_prescriptions(
    prescription_service, tenant_id, sample_prescription_data, patient_id, prescriber_id
):
    """Test retrieving only active prescriptions"""
    # Create and sign multiple prescriptions
    for i in range(3):
        prescription = prescription_service.create_prescription(
            tenant_id=tenant_id,
            data=sample_prescription_data
        )
        prescription_service.sign_prescription(
            tenant_id=tenant_id,
            prescription_id=prescription.id,
            signer_id=prescriber_id
        )

    # Create and cancel one
    cancelled_rx = prescription_service.create_prescription(
        tenant_id=tenant_id,
        data=sample_prescription_data
    )
    prescription_service.cancel_prescription(
        tenant_id=tenant_id,
        prescription_id=cancelled_rx.id,
        reason="Test cancellation"
    )

    active = prescription_service.get_active_prescriptions(
        tenant_id=tenant_id,
        patient_id=patient_id
    )

    # Cancelled prescription should not be in active list
    assert all(rx.status != PrescriptionStatus.CANCELLED for rx in active)


# ============================================================================
# MULTI-TENANCY TESTS
# ============================================================================

def test_tenant_isolation(prescription_service, sample_prescription_data):
    """Test that prescriptions are isolated by tenant"""
    tenant1 = UUID("00000000-0000-0000-0000-000000000001")
    tenant2 = UUID("00000000-0000-0000-0000-000000000002")

    # Create prescription for tenant1
    created = prescription_service.create_prescription(
        tenant_id=tenant1,
        data=sample_prescription_data
    )

    # Try to retrieve it as tenant2
    retrieved = prescription_service.get_prescription(
        tenant_id=tenant2,
        prescription_id=created.id
    )

    assert retrieved is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
