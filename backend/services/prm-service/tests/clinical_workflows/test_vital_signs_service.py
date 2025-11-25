"""
Test Vital Signs Service
Unit tests for vital signs management (US-006.10)
"""
import pytest
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../..")))

from services.prm_service.modules.clinical_workflows.models import (
    Base, VitalSign, EarlyWarningScore
)
from services.prm_service.modules.clinical_workflows.schemas import (
    VitalSignCreate, VitalType
)
from services.prm_service.modules.clinical_workflows.service import VitalSignsService


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
def vital_signs_service(db_session):
    """Create a vital signs service instance"""
    return VitalSignsService(db_session)


@pytest.fixture
def tenant_id():
    """Test tenant ID"""
    return UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def patient_id():
    """Test patient ID"""
    return UUID("00000000-0000-0000-0000-000000000002")


@pytest.fixture
def recorder_id():
    """Test recorder ID"""
    return UUID("00000000-0000-0000-0000-000000000003")


@pytest.fixture
def normal_vitals_set(patient_id, recorder_id):
    """Normal vital signs data set"""
    return [
        VitalSignCreate(
            patient_id=patient_id,
            recorder_id=recorder_id,
            vital_type=VitalType.HEART_RATE,
            value=72.0,
            unit="bpm"
        ),
        VitalSignCreate(
            patient_id=patient_id,
            recorder_id=recorder_id,
            vital_type=VitalType.BLOOD_PRESSURE_SYSTOLIC,
            value=120.0,
            unit="mmHg"
        ),
        VitalSignCreate(
            patient_id=patient_id,
            recorder_id=recorder_id,
            vital_type=VitalType.BLOOD_PRESSURE_DIASTOLIC,
            value=80.0,
            unit="mmHg"
        ),
        VitalSignCreate(
            patient_id=patient_id,
            recorder_id=recorder_id,
            vital_type=VitalType.RESPIRATORY_RATE,
            value=16.0,
            unit="breaths/min"
        ),
        VitalSignCreate(
            patient_id=patient_id,
            recorder_id=recorder_id,
            vital_type=VitalType.TEMPERATURE,
            value=98.6,
            unit="F"
        ),
        VitalSignCreate(
            patient_id=patient_id,
            recorder_id=recorder_id,
            vital_type=VitalType.OXYGEN_SATURATION,
            value=98.0,
            unit="%"
        )
    ]


@pytest.fixture
def abnormal_vitals_set(patient_id, recorder_id):
    """Abnormal vital signs indicating deterioration"""
    return [
        VitalSignCreate(
            patient_id=patient_id,
            recorder_id=recorder_id,
            vital_type=VitalType.HEART_RATE,
            value=110.0,
            unit="bpm"
        ),
        VitalSignCreate(
            patient_id=patient_id,
            recorder_id=recorder_id,
            vital_type=VitalType.BLOOD_PRESSURE_SYSTOLIC,
            value=90.0,
            unit="mmHg"
        ),
        VitalSignCreate(
            patient_id=patient_id,
            recorder_id=recorder_id,
            vital_type=VitalType.BLOOD_PRESSURE_DIASTOLIC,
            value=60.0,
            unit="mmHg"
        ),
        VitalSignCreate(
            patient_id=patient_id,
            recorder_id=recorder_id,
            vital_type=VitalType.RESPIRATORY_RATE,
            value=24.0,
            unit="breaths/min"
        ),
        VitalSignCreate(
            patient_id=patient_id,
            recorder_id=recorder_id,
            vital_type=VitalType.TEMPERATURE,
            value=101.5,
            unit="F"
        ),
        VitalSignCreate(
            patient_id=patient_id,
            recorder_id=recorder_id,
            vital_type=VitalType.OXYGEN_SATURATION,
            value=92.0,
            unit="%"
        )
    ]


# ============================================================================
# RECORD VITAL SIGN TESTS
# ============================================================================

def test_record_single_vital(vital_signs_service, tenant_id, patient_id, recorder_id):
    """Test recording a single vital sign"""
    data = VitalSignCreate(
        patient_id=patient_id,
        recorder_id=recorder_id,
        vital_type=VitalType.HEART_RATE,
        value=72.0,
        unit="bpm"
    )

    vital = vital_signs_service.record_vital(
        tenant_id=tenant_id,
        data=data
    )

    assert vital is not None
    assert vital.id is not None
    assert vital.vital_type == VitalType.HEART_RATE
    assert vital.value == 72.0
    assert vital.tenant_id == tenant_id


def test_record_blood_pressure(vital_signs_service, tenant_id, patient_id, recorder_id):
    """Test recording blood pressure (systolic and diastolic)"""
    systolic = VitalSignCreate(
        patient_id=patient_id,
        recorder_id=recorder_id,
        vital_type=VitalType.BLOOD_PRESSURE_SYSTOLIC,
        value=120.0,
        unit="mmHg"
    )

    diastolic = VitalSignCreate(
        patient_id=patient_id,
        recorder_id=recorder_id,
        vital_type=VitalType.BLOOD_PRESSURE_DIASTOLIC,
        value=80.0,
        unit="mmHg"
    )

    sys_vital = vital_signs_service.record_vital(tenant_id=tenant_id, data=systolic)
    dia_vital = vital_signs_service.record_vital(tenant_id=tenant_id, data=diastolic)

    assert sys_vital.value == 120.0
    assert dia_vital.value == 80.0


def test_record_vital_set(vital_signs_service, tenant_id, normal_vitals_set):
    """Test recording a complete set of vital signs"""
    vitals = vital_signs_service.record_vital_set(
        tenant_id=tenant_id,
        vitals=normal_vitals_set
    )

    assert len(vitals) == 6


def test_record_height_and_weight(vital_signs_service, tenant_id, patient_id, recorder_id):
    """Test recording height and weight for BMI calculation"""
    height = VitalSignCreate(
        patient_id=patient_id,
        recorder_id=recorder_id,
        vital_type=VitalType.HEIGHT,
        value=70.0,  # inches
        unit="in"
    )

    weight = VitalSignCreate(
        patient_id=patient_id,
        recorder_id=recorder_id,
        vital_type=VitalType.WEIGHT,
        value=180.0,  # pounds
        unit="lb"
    )

    h = vital_signs_service.record_vital(tenant_id=tenant_id, data=height)
    w = vital_signs_service.record_vital(tenant_id=tenant_id, data=weight)

    assert h.value == 70.0
    assert w.value == 180.0


def test_record_pain_score(vital_signs_service, tenant_id, patient_id, recorder_id):
    """Test recording pain score"""
    pain = VitalSignCreate(
        patient_id=patient_id,
        recorder_id=recorder_id,
        vital_type=VitalType.PAIN_SCORE,
        value=3.0,
        unit="0-10 scale"
    )

    vital = vital_signs_service.record_vital(tenant_id=tenant_id, data=pain)

    assert vital.vital_type == VitalType.PAIN_SCORE
    assert vital.value == 3.0


# ============================================================================
# EARLY WARNING SCORE (NEWS) TESTS
# ============================================================================

def test_calculate_news_normal_vitals(vital_signs_service, tenant_id, normal_vitals_set, patient_id):
    """Test NEWS calculation with normal vital signs"""
    # Record normal vitals
    vital_signs_service.record_vital_set(
        tenant_id=tenant_id,
        vitals=normal_vitals_set
    )

    news = vital_signs_service.calculate_news(
        tenant_id=tenant_id,
        patient_id=patient_id
    )

    assert news is not None
    assert news.total_score <= 4  # Normal should be low score


def test_calculate_news_abnormal_vitals(vital_signs_service, tenant_id, abnormal_vitals_set, patient_id):
    """Test NEWS calculation with abnormal vital signs"""
    # Record abnormal vitals
    vital_signs_service.record_vital_set(
        tenant_id=tenant_id,
        vitals=abnormal_vitals_set
    )

    news = vital_signs_service.calculate_news(
        tenant_id=tenant_id,
        patient_id=patient_id
    )

    assert news is not None
    assert news.total_score >= 5  # Abnormal should have higher score


def test_news_triggers_alert_high_score(vital_signs_service, tenant_id, abnormal_vitals_set, patient_id):
    """Test that high NEWS score triggers clinical alert"""
    # Record very abnormal vitals
    vital_signs_service.record_vital_set(
        tenant_id=tenant_id,
        vitals=abnormal_vitals_set
    )

    news = vital_signs_service.calculate_news(
        tenant_id=tenant_id,
        patient_id=patient_id
    )

    # NEWS >= 5 should flag for escalation
    if news.total_score >= 5:
        assert news.escalation_required is True


def test_news_clinical_response_low(vital_signs_service, tenant_id, normal_vitals_set, patient_id):
    """Test clinical response recommendation for low NEWS"""
    vital_signs_service.record_vital_set(
        tenant_id=tenant_id,
        vitals=normal_vitals_set
    )

    news = vital_signs_service.calculate_news(
        tenant_id=tenant_id,
        patient_id=patient_id
    )

    if news.total_score <= 4:
        assert news.clinical_response in ["routine", "continue monitoring"]


# ============================================================================
# VITAL TRENDS TESTS
# ============================================================================

def test_get_vital_trends(vital_signs_service, tenant_id, patient_id, recorder_id):
    """Test getting vital sign trends over time"""
    # Record vitals over time
    for i in range(5):
        data = VitalSignCreate(
            patient_id=patient_id,
            recorder_id=recorder_id,
            vital_type=VitalType.HEART_RATE,
            value=70.0 + i * 2,  # Gradually increasing
            unit="bpm",
            recorded_at=datetime.utcnow() - timedelta(hours=4 * (4 - i))
        )
        vital_signs_service.record_vital(tenant_id=tenant_id, data=data)

    trends = vital_signs_service.get_vital_trends(
        tenant_id=tenant_id,
        patient_id=patient_id,
        vital_type=VitalType.HEART_RATE,
        hours=24
    )

    assert len(trends) >= 5


def test_get_latest_vitals(vital_signs_service, tenant_id, normal_vitals_set, patient_id):
    """Test getting the most recent vital signs"""
    vital_signs_service.record_vital_set(
        tenant_id=tenant_id,
        vitals=normal_vitals_set
    )

    latest = vital_signs_service.get_latest_vitals(
        tenant_id=tenant_id,
        patient_id=patient_id
    )

    assert latest is not None
    assert VitalType.HEART_RATE in latest
    assert VitalType.BLOOD_PRESSURE_SYSTOLIC in latest


def test_detect_vital_deterioration(vital_signs_service, tenant_id, patient_id, recorder_id):
    """Test detection of vital sign deterioration"""
    # Record declining oxygen saturation
    for i in range(4):
        data = VitalSignCreate(
            patient_id=patient_id,
            recorder_id=recorder_id,
            vital_type=VitalType.OXYGEN_SATURATION,
            value=98.0 - i * 2,  # Declining from 98% to 92%
            unit="%",
            recorded_at=datetime.utcnow() - timedelta(hours=4 * (3 - i))
        )
        vital_signs_service.record_vital(tenant_id=tenant_id, data=data)

    deterioration = vital_signs_service.detect_deterioration(
        tenant_id=tenant_id,
        patient_id=patient_id,
        vital_type=VitalType.OXYGEN_SATURATION,
        threshold_percent=5.0
    )

    assert deterioration is True


# ============================================================================
# VITAL RETRIEVAL TESTS
# ============================================================================

def test_get_patient_vitals(vital_signs_service, tenant_id, normal_vitals_set, patient_id):
    """Test retrieving all vitals for a patient"""
    vital_signs_service.record_vital_set(
        tenant_id=tenant_id,
        vitals=normal_vitals_set
    )

    vitals = vital_signs_service.get_patient_vitals(
        tenant_id=tenant_id,
        patient_id=patient_id
    )

    assert len(vitals) >= 6


def test_get_vital_by_type(vital_signs_service, tenant_id, normal_vitals_set, patient_id):
    """Test retrieving vitals by type"""
    vital_signs_service.record_vital_set(
        tenant_id=tenant_id,
        vitals=normal_vitals_set
    )

    heart_rates = vital_signs_service.get_vitals_by_type(
        tenant_id=tenant_id,
        patient_id=patient_id,
        vital_type=VitalType.HEART_RATE
    )

    assert all(v.vital_type == VitalType.HEART_RATE for v in heart_rates)


def test_get_vitals_in_date_range(vital_signs_service, tenant_id, patient_id, recorder_id):
    """Test retrieving vitals within a date range"""
    # Record vitals at different times
    for i in range(10):
        data = VitalSignCreate(
            patient_id=patient_id,
            recorder_id=recorder_id,
            vital_type=VitalType.TEMPERATURE,
            value=98.6 + (i * 0.1),
            unit="F",
            recorded_at=datetime.utcnow() - timedelta(days=i)
        )
        vital_signs_service.record_vital(tenant_id=tenant_id, data=data)

    # Get vitals from last 5 days
    vitals = vital_signs_service.get_vitals_in_range(
        tenant_id=tenant_id,
        patient_id=patient_id,
        start_date=datetime.utcnow() - timedelta(days=5),
        end_date=datetime.utcnow()
    )

    assert len(vitals) == 6  # Days 0-5 inclusive


# ============================================================================
# BMI CALCULATION TESTS
# ============================================================================

def test_calculate_bmi(vital_signs_service, tenant_id, patient_id, recorder_id):
    """Test BMI calculation from height and weight"""
    # Record height (70 inches = 1.778 meters)
    height = VitalSignCreate(
        patient_id=patient_id,
        recorder_id=recorder_id,
        vital_type=VitalType.HEIGHT,
        value=70.0,
        unit="in"
    )

    # Record weight (180 lbs = 81.6 kg)
    weight = VitalSignCreate(
        patient_id=patient_id,
        recorder_id=recorder_id,
        vital_type=VitalType.WEIGHT,
        value=180.0,
        unit="lb"
    )

    vital_signs_service.record_vital(tenant_id=tenant_id, data=height)
    vital_signs_service.record_vital(tenant_id=tenant_id, data=weight)

    bmi = vital_signs_service.calculate_bmi(
        tenant_id=tenant_id,
        patient_id=patient_id
    )

    # BMI for 180lb, 70in should be approximately 25.8
    assert 25.0 <= bmi <= 26.5


# ============================================================================
# MULTI-TENANCY TESTS
# ============================================================================

def test_tenant_isolation(vital_signs_service, patient_id, recorder_id):
    """Test that vital signs are isolated by tenant"""
    tenant1 = UUID("00000000-0000-0000-0000-000000000001")
    tenant2 = UUID("00000000-0000-0000-0000-000000000002")

    data = VitalSignCreate(
        patient_id=patient_id,
        recorder_id=recorder_id,
        vital_type=VitalType.HEART_RATE,
        value=72.0,
        unit="bpm"
    )

    # Create vital for tenant1
    created = vital_signs_service.record_vital(
        tenant_id=tenant1,
        data=data
    )

    # Try to get vitals for tenant2
    vitals = vital_signs_service.get_patient_vitals(
        tenant_id=tenant2,
        patient_id=patient_id
    )

    assert len(vitals) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
