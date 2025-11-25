"""
Test Lab Order Service
Unit tests for laboratory order management (US-006.2)
"""
import pytest
from uuid import uuid4, UUID
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../..")))

from services.prm_service.modules.clinical_workflows.models import (
    Base, LabOrder, LabResult
)
from services.prm_service.modules.clinical_workflows.schemas import (
    LabOrderCreate, LabResultCreate, LabOrderStatus, OrderPriority, InterpretationFlag
)
from services.prm_service.modules.clinical_workflows.service import LabOrderService


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
def lab_order_service(db_session):
    """Create a lab order service instance"""
    return LabOrderService(db_session)


@pytest.fixture
def tenant_id():
    """Test tenant ID"""
    return UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def patient_id():
    """Test patient ID"""
    return UUID("00000000-0000-0000-0000-000000000002")


@pytest.fixture
def ordering_provider_id():
    """Test ordering provider ID"""
    return UUID("00000000-0000-0000-0000-000000000003")


@pytest.fixture
def sample_lab_order_data(patient_id, ordering_provider_id):
    """Sample lab order data"""
    return LabOrderCreate(
        patient_id=patient_id,
        ordering_provider_id=ordering_provider_id,
        encounter_id=uuid4(),
        test_name="Complete Blood Count (CBC)",
        test_code="LAB001",
        loinc_code="58410-2",
        priority=OrderPriority.ROUTINE,
        clinical_indication="Annual physical examination",
        fasting_required=False,
        special_instructions="None",
        panels=["CBC with Differential"],
        collection_instructions="Standard venipuncture"
    )


@pytest.fixture
def sample_stat_order_data(patient_id, ordering_provider_id):
    """Sample STAT lab order data"""
    return LabOrderCreate(
        patient_id=patient_id,
        ordering_provider_id=ordering_provider_id,
        test_name="Troponin I",
        test_code="LAB999",
        loinc_code="10839-9",
        priority=OrderPriority.STAT,
        clinical_indication="Chest pain, rule out MI",
        fasting_required=False,
        special_instructions="Draw immediately"
    )


# ============================================================================
# CREATE LAB ORDER TESTS
# ============================================================================

def test_create_lab_order(lab_order_service, tenant_id, sample_lab_order_data):
    """Test creating a new lab order"""
    order = lab_order_service.create_lab_order(
        tenant_id=tenant_id,
        data=sample_lab_order_data
    )

    assert order is not None
    assert order.id is not None
    assert order.test_name == "Complete Blood Count (CBC)"
    assert order.status == LabOrderStatus.PENDING
    assert order.tenant_id == tenant_id


def test_create_stat_order(lab_order_service, tenant_id, sample_stat_order_data):
    """Test creating a STAT priority order"""
    order = lab_order_service.create_lab_order(
        tenant_id=tenant_id,
        data=sample_stat_order_data
    )

    assert order.priority == OrderPriority.STAT
    assert order.test_name == "Troponin I"


def test_create_fasting_order(lab_order_service, tenant_id, patient_id, ordering_provider_id):
    """Test creating an order requiring fasting"""
    data = LabOrderCreate(
        patient_id=patient_id,
        ordering_provider_id=ordering_provider_id,
        test_name="Lipid Panel",
        test_code="LAB002",
        loinc_code="24331-1",
        priority=OrderPriority.ROUTINE,
        clinical_indication="Cardiovascular risk assessment",
        fasting_required=True,
        fasting_hours=12,
        special_instructions="Patient must fast for 12 hours before collection"
    )

    order = lab_order_service.create_lab_order(
        tenant_id=tenant_id,
        data=data
    )

    assert order.fasting_required is True
    assert order.fasting_hours == 12


# ============================================================================
# ORDER STATUS WORKFLOW TESTS
# ============================================================================

def test_collect_specimen(lab_order_service, tenant_id, sample_lab_order_data):
    """Test recording specimen collection"""
    order = lab_order_service.create_lab_order(
        tenant_id=tenant_id,
        data=sample_lab_order_data
    )

    collected = lab_order_service.collect_specimen(
        tenant_id=tenant_id,
        order_id=order.id,
        collector_id=uuid4(),
        collection_time=datetime.utcnow(),
        specimen_id="SPEC-12345",
        specimen_type="Blood",
        collection_site="Left arm"
    )

    assert collected.status == LabOrderStatus.COLLECTED
    assert collected.specimen_collected_at is not None


def test_process_specimen(lab_order_service, tenant_id, sample_lab_order_data):
    """Test marking specimen as processing"""
    order = lab_order_service.create_lab_order(
        tenant_id=tenant_id,
        data=sample_lab_order_data
    )

    # Collect specimen first
    lab_order_service.collect_specimen(
        tenant_id=tenant_id,
        order_id=order.id,
        collector_id=uuid4(),
        collection_time=datetime.utcnow(),
        specimen_id="SPEC-12345",
        specimen_type="Blood"
    )

    # Mark as processing
    processing = lab_order_service.start_processing(
        tenant_id=tenant_id,
        order_id=order.id
    )

    assert processing.status == LabOrderStatus.PROCESSING


def test_cancel_order(lab_order_service, tenant_id, sample_lab_order_data):
    """Test canceling a lab order"""
    order = lab_order_service.create_lab_order(
        tenant_id=tenant_id,
        data=sample_lab_order_data
    )

    cancelled = lab_order_service.cancel_order(
        tenant_id=tenant_id,
        order_id=order.id,
        reason="Duplicate order"
    )

    assert cancelled.status == LabOrderStatus.CANCELLED


def test_cannot_cancel_completed_order(lab_order_service, tenant_id, sample_lab_order_data):
    """Test that completed orders cannot be cancelled"""
    order = lab_order_service.create_lab_order(
        tenant_id=tenant_id,
        data=sample_lab_order_data
    )

    # Complete the order workflow
    lab_order_service.collect_specimen(
        tenant_id=tenant_id,
        order_id=order.id,
        collector_id=uuid4(),
        collection_time=datetime.utcnow(),
        specimen_id="SPEC-12345",
        specimen_type="Blood"
    )

    lab_order_service.start_processing(
        tenant_id=tenant_id,
        order_id=order.id
    )

    lab_order_service.complete_order(
        tenant_id=tenant_id,
        order_id=order.id
    )

    # Try to cancel
    with pytest.raises(ValueError) as excinfo:
        lab_order_service.cancel_order(
            tenant_id=tenant_id,
            order_id=order.id,
            reason="Attempting to cancel completed order"
        )

    assert "cannot be cancelled" in str(excinfo.value).lower()


# ============================================================================
# LAB RESULT TESTS
# ============================================================================

def test_record_lab_result(lab_order_service, tenant_id, sample_lab_order_data):
    """Test recording a lab result"""
    order = lab_order_service.create_lab_order(
        tenant_id=tenant_id,
        data=sample_lab_order_data
    )

    result_data = LabResultCreate(
        order_id=order.id,
        component_name="White Blood Cell Count",
        component_code="WBC",
        loinc_code="6690-2",
        value="7.5",
        value_numeric=7.5,
        unit="10^3/uL",
        reference_range_low=4.5,
        reference_range_high=11.0,
        interpretation_flag=InterpretationFlag.NORMAL,
        performed_by=uuid4(),
        performed_at=datetime.utcnow()
    )

    result = lab_order_service.record_result(
        tenant_id=tenant_id,
        data=result_data
    )

    assert result is not None
    assert result.component_name == "White Blood Cell Count"
    assert result.value_numeric == 7.5
    assert result.interpretation_flag == InterpretationFlag.NORMAL


def test_record_abnormal_result(lab_order_service, tenant_id, sample_lab_order_data):
    """Test recording an abnormal lab result"""
    order = lab_order_service.create_lab_order(
        tenant_id=tenant_id,
        data=sample_lab_order_data
    )

    result_data = LabResultCreate(
        order_id=order.id,
        component_name="Hemoglobin",
        component_code="HGB",
        loinc_code="718-7",
        value="8.5",
        value_numeric=8.5,
        unit="g/dL",
        reference_range_low=12.0,
        reference_range_high=16.0,
        interpretation_flag=InterpretationFlag.LOW,
        performed_by=uuid4(),
        performed_at=datetime.utcnow()
    )

    result = lab_order_service.record_result(
        tenant_id=tenant_id,
        data=result_data
    )

    assert result.interpretation_flag == InterpretationFlag.LOW
    assert result.value_numeric < result.reference_range_low


def test_record_critical_result(lab_order_service, tenant_id, sample_lab_order_data):
    """Test recording a critical lab result"""
    order = lab_order_service.create_lab_order(
        tenant_id=tenant_id,
        data=sample_lab_order_data
    )

    result_data = LabResultCreate(
        order_id=order.id,
        component_name="Potassium",
        component_code="K",
        loinc_code="2823-3",
        value="6.8",
        value_numeric=6.8,
        unit="mEq/L",
        reference_range_low=3.5,
        reference_range_high=5.0,
        interpretation_flag=InterpretationFlag.CRITICAL_HIGH,
        critical_flag=True,
        performed_by=uuid4(),
        performed_at=datetime.utcnow()
    )

    result = lab_order_service.record_result(
        tenant_id=tenant_id,
        data=result_data
    )

    assert result.critical_flag is True
    assert result.interpretation_flag == InterpretationFlag.CRITICAL_HIGH


# ============================================================================
# RESULT TREND TESTS
# ============================================================================

def test_get_result_trends(lab_order_service, tenant_id, sample_lab_order_data, patient_id):
    """Test getting historical result trends"""
    # Create multiple orders and results over time
    for i in range(3):
        order = lab_order_service.create_lab_order(
            tenant_id=tenant_id,
            data=sample_lab_order_data
        )

        result_data = LabResultCreate(
            order_id=order.id,
            component_name="Hemoglobin A1c",
            component_code="HBA1C",
            loinc_code="4548-4",
            value=str(7.0 + i * 0.5),
            value_numeric=7.0 + i * 0.5,
            unit="%",
            reference_range_low=4.0,
            reference_range_high=5.7,
            interpretation_flag=InterpretationFlag.HIGH,
            performed_by=uuid4(),
            performed_at=datetime.utcnow() - timedelta(days=90 * (2 - i))
        )

        lab_order_service.record_result(
            tenant_id=tenant_id,
            data=result_data
        )

    trends = lab_order_service.get_result_trends(
        tenant_id=tenant_id,
        patient_id=patient_id,
        component_code="HBA1C",
        days=365
    )

    assert len(trends) >= 3


# ============================================================================
# ORDER RETRIEVAL TESTS
# ============================================================================

def test_get_order_by_id(lab_order_service, tenant_id, sample_lab_order_data):
    """Test retrieving a lab order by ID"""
    created = lab_order_service.create_lab_order(
        tenant_id=tenant_id,
        data=sample_lab_order_data
    )

    retrieved = lab_order_service.get_order(
        tenant_id=tenant_id,
        order_id=created.id
    )

    assert retrieved is not None
    assert retrieved.id == created.id


def test_get_patient_orders(lab_order_service, tenant_id, sample_lab_order_data, patient_id):
    """Test retrieving all orders for a patient"""
    for i in range(3):
        lab_order_service.create_lab_order(
            tenant_id=tenant_id,
            data=sample_lab_order_data
        )

    orders = lab_order_service.get_patient_orders(
        tenant_id=tenant_id,
        patient_id=patient_id
    )

    assert len(orders) >= 3


def test_get_pending_orders(lab_order_service, tenant_id, sample_lab_order_data, patient_id):
    """Test retrieving only pending orders"""
    # Create some orders
    order1 = lab_order_service.create_lab_order(
        tenant_id=tenant_id,
        data=sample_lab_order_data
    )

    order2 = lab_order_service.create_lab_order(
        tenant_id=tenant_id,
        data=sample_lab_order_data
    )

    # Cancel one
    lab_order_service.cancel_order(
        tenant_id=tenant_id,
        order_id=order2.id,
        reason="Test cancellation"
    )

    pending = lab_order_service.get_pending_orders(
        tenant_id=tenant_id,
        patient_id=patient_id
    )

    assert all(o.status == LabOrderStatus.PENDING for o in pending)


def test_get_order_with_results(lab_order_service, tenant_id, sample_lab_order_data):
    """Test retrieving an order with its results"""
    order = lab_order_service.create_lab_order(
        tenant_id=tenant_id,
        data=sample_lab_order_data
    )

    # Add multiple results
    components = [
        ("WBC", "6690-2", 7.5, "10^3/uL"),
        ("RBC", "789-8", 4.5, "10^6/uL"),
        ("HGB", "718-7", 14.0, "g/dL")
    ]

    for name, loinc, value, unit in components:
        result_data = LabResultCreate(
            order_id=order.id,
            component_name=name,
            component_code=name,
            loinc_code=loinc,
            value=str(value),
            value_numeric=value,
            unit=unit,
            reference_range_low=value * 0.8,
            reference_range_high=value * 1.2,
            interpretation_flag=InterpretationFlag.NORMAL,
            performed_by=uuid4(),
            performed_at=datetime.utcnow()
        )
        lab_order_service.record_result(tenant_id=tenant_id, data=result_data)

    order_with_results = lab_order_service.get_order_with_results(
        tenant_id=tenant_id,
        order_id=order.id
    )

    assert order_with_results is not None
    assert len(order_with_results.results) == 3


# ============================================================================
# MULTI-TENANCY TESTS
# ============================================================================

def test_tenant_isolation(lab_order_service, sample_lab_order_data):
    """Test that lab orders are isolated by tenant"""
    tenant1 = UUID("00000000-0000-0000-0000-000000000001")
    tenant2 = UUID("00000000-0000-0000-0000-000000000002")

    # Create order for tenant1
    created = lab_order_service.create_lab_order(
        tenant_id=tenant1,
        data=sample_lab_order_data
    )

    # Try to retrieve it as tenant2
    retrieved = lab_order_service.get_order(
        tenant_id=tenant2,
        order_id=created.id
    )

    assert retrieved is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
