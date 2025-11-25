"""
Test Decision Support Service
Unit tests for clinical decision support (US-006.9)
"""
import pytest
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../..")))

from services.prm_service.modules.clinical_workflows.models import (
    Base, ClinicalAlert, CDSRule
)
from services.prm_service.modules.clinical_workflows.schemas import (
    ClinicalAlertCreate, CDSRuleCreate, AlertSeverity, AlertCategory
)
from services.prm_service.modules.clinical_workflows.service import DecisionSupportService


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
def cds_service(db_session):
    """Create a decision support service instance"""
    return DecisionSupportService(db_session)


@pytest.fixture
def tenant_id():
    """Test tenant ID"""
    return UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def patient_id():
    """Test patient ID"""
    return UUID("00000000-0000-0000-0000-000000000002")


@pytest.fixture
def provider_id():
    """Test provider ID"""
    return UUID("00000000-0000-0000-0000-000000000003")


@pytest.fixture
def sample_alert_data(patient_id):
    """Sample clinical alert data"""
    return ClinicalAlertCreate(
        patient_id=patient_id,
        title="Drug-Drug Interaction Alert",
        message="Potential interaction between Warfarin and Aspirin",
        severity=AlertSeverity.HIGH,
        category=AlertCategory.DRUG_INTERACTION,
        source_system="Prescription Module",
        related_resource_type="Prescription",
        related_resource_id=str(uuid4())
    )


@pytest.fixture
def sample_rule_data():
    """Sample CDS rule data"""
    return CDSRuleCreate(
        name="Diabetic A1c Monitoring",
        description="Alert if diabetic patient HbA1c not checked in 90 days",
        rule_type="reminder",
        conditions={
            "condition": "diabetes",
            "last_a1c_days": "> 90"
        },
        actions={
            "alert_type": "reminder",
            "message": "HbA1c overdue for diabetic patient"
        },
        severity=AlertSeverity.MEDIUM,
        category=AlertCategory.CARE_GAP,
        is_active=True
    )


# ============================================================================
# CLINICAL ALERT TESTS
# ============================================================================

def test_create_alert(cds_service, tenant_id, sample_alert_data):
    """Test creating a clinical alert"""
    alert = cds_service.create_alert(
        tenant_id=tenant_id,
        data=sample_alert_data
    )

    assert alert is not None
    assert alert.id is not None
    assert alert.title == "Drug-Drug Interaction Alert"
    assert alert.severity == AlertSeverity.HIGH
    assert alert.acknowledged is False


def test_create_critical_alert(cds_service, tenant_id, patient_id):
    """Test creating a critical severity alert"""
    data = ClinicalAlertCreate(
        patient_id=patient_id,
        title="Critical Lab Value",
        message="Potassium level critically elevated: 6.8 mEq/L",
        severity=AlertSeverity.CRITICAL,
        category=AlertCategory.ABNORMAL_RESULT,
        source_system="Lab Module",
        requires_acknowledgment=True
    )

    alert = cds_service.create_alert(
        tenant_id=tenant_id,
        data=data
    )

    assert alert.severity == AlertSeverity.CRITICAL
    assert alert.requires_acknowledgment is True


def test_acknowledge_alert(cds_service, tenant_id, sample_alert_data, provider_id):
    """Test acknowledging a clinical alert"""
    alert = cds_service.create_alert(
        tenant_id=tenant_id,
        data=sample_alert_data
    )

    acknowledged = cds_service.acknowledge_alert(
        tenant_id=tenant_id,
        alert_id=alert.id,
        acknowledged_by=provider_id,
        acknowledgment_notes="Reviewed and will monitor"
    )

    assert acknowledged.acknowledged is True
    assert acknowledged.acknowledged_at is not None
    assert acknowledged.acknowledged_by == provider_id


def test_dismiss_alert(cds_service, tenant_id, sample_alert_data, provider_id):
    """Test dismissing a clinical alert"""
    alert = cds_service.create_alert(
        tenant_id=tenant_id,
        data=sample_alert_data
    )

    dismissed = cds_service.dismiss_alert(
        tenant_id=tenant_id,
        alert_id=alert.id,
        dismissed_by=provider_id,
        reason="Not clinically relevant"
    )

    assert dismissed.dismissed is True
    assert dismissed.dismissed_at is not None


def test_override_alert(cds_service, tenant_id, sample_alert_data, provider_id):
    """Test overriding an alert with reason"""
    alert = cds_service.create_alert(
        tenant_id=tenant_id,
        data=sample_alert_data
    )

    overridden = cds_service.override_alert(
        tenant_id=tenant_id,
        alert_id=alert.id,
        overridden_by=provider_id,
        reason="Benefit outweighs risk in this case"
    )

    assert overridden.overridden is True
    assert overridden.override_reason is not None


# ============================================================================
# ALERT RETRIEVAL TESTS
# ============================================================================

def test_get_patient_alerts(cds_service, tenant_id, patient_id):
    """Test retrieving all alerts for a patient"""
    # Create multiple alerts
    for i in range(3):
        data = ClinicalAlertCreate(
            patient_id=patient_id,
            title=f"Alert {i}",
            message=f"Alert message {i}",
            severity=AlertSeverity.MEDIUM,
            category=AlertCategory.REMINDER
        )
        cds_service.create_alert(tenant_id=tenant_id, data=data)

    alerts = cds_service.get_patient_alerts(
        tenant_id=tenant_id,
        patient_id=patient_id
    )

    assert len(alerts) >= 3


def test_get_active_alerts(cds_service, tenant_id, patient_id, provider_id):
    """Test retrieving only active (unacknowledged) alerts"""
    # Create some alerts
    for i in range(3):
        data = ClinicalAlertCreate(
            patient_id=patient_id,
            title=f"Alert {i}",
            message=f"Alert message {i}",
            severity=AlertSeverity.MEDIUM,
            category=AlertCategory.REMINDER
        )
        alert = cds_service.create_alert(tenant_id=tenant_id, data=data)

        # Acknowledge one
        if i == 0:
            cds_service.acknowledge_alert(
                tenant_id=tenant_id,
                alert_id=alert.id,
                acknowledged_by=provider_id
            )

    active = cds_service.get_active_alerts(
        tenant_id=tenant_id,
        patient_id=patient_id
    )

    assert all(not a.acknowledged for a in active)


def test_get_alerts_by_severity(cds_service, tenant_id, patient_id):
    """Test filtering alerts by severity"""
    severities = [AlertSeverity.LOW, AlertSeverity.MEDIUM, AlertSeverity.HIGH, AlertSeverity.CRITICAL]

    for severity in severities:
        data = ClinicalAlertCreate(
            patient_id=patient_id,
            title=f"{severity.value} Alert",
            message=f"Alert with {severity.value} severity",
            severity=severity,
            category=AlertCategory.REMINDER
        )
        cds_service.create_alert(tenant_id=tenant_id, data=data)

    high_alerts = cds_service.get_alerts_by_severity(
        tenant_id=tenant_id,
        patient_id=patient_id,
        severity=AlertSeverity.HIGH
    )

    assert all(a.severity == AlertSeverity.HIGH for a in high_alerts)


def test_get_alerts_by_category(cds_service, tenant_id, patient_id):
    """Test filtering alerts by category"""
    categories = [
        AlertCategory.DRUG_INTERACTION,
        AlertCategory.ALLERGY,
        AlertCategory.CARE_GAP,
        AlertCategory.ABNORMAL_RESULT
    ]

    for category in categories:
        data = ClinicalAlertCreate(
            patient_id=patient_id,
            title=f"{category.value} Alert",
            message=f"Alert for {category.value}",
            severity=AlertSeverity.MEDIUM,
            category=category
        )
        cds_service.create_alert(tenant_id=tenant_id, data=data)

    drug_alerts = cds_service.get_alerts_by_category(
        tenant_id=tenant_id,
        patient_id=patient_id,
        category=AlertCategory.DRUG_INTERACTION
    )

    assert all(a.category == AlertCategory.DRUG_INTERACTION for a in drug_alerts)


# ============================================================================
# CDS RULE TESTS
# ============================================================================

def test_create_cds_rule(cds_service, tenant_id, sample_rule_data):
    """Test creating a CDS rule"""
    rule = cds_service.create_rule(
        tenant_id=tenant_id,
        data=sample_rule_data
    )

    assert rule is not None
    assert rule.id is not None
    assert rule.name == "Diabetic A1c Monitoring"
    assert rule.is_active is True


def test_deactivate_rule(cds_service, tenant_id, sample_rule_data):
    """Test deactivating a CDS rule"""
    rule = cds_service.create_rule(
        tenant_id=tenant_id,
        data=sample_rule_data
    )

    deactivated = cds_service.deactivate_rule(
        tenant_id=tenant_id,
        rule_id=rule.id
    )

    assert deactivated.is_active is False


def test_activate_rule(cds_service, tenant_id, sample_rule_data):
    """Test activating a deactivated rule"""
    rule = cds_service.create_rule(
        tenant_id=tenant_id,
        data=sample_rule_data
    )

    cds_service.deactivate_rule(
        tenant_id=tenant_id,
        rule_id=rule.id
    )

    activated = cds_service.activate_rule(
        tenant_id=tenant_id,
        rule_id=rule.id
    )

    assert activated.is_active is True


def test_get_active_rules(cds_service, tenant_id):
    """Test retrieving active CDS rules"""
    # Create some rules
    for i in range(3):
        data = CDSRuleCreate(
            name=f"Rule {i}",
            description=f"Description for rule {i}",
            rule_type="alert",
            conditions={"condition": f"test_{i}"},
            actions={"action": "alert"},
            severity=AlertSeverity.MEDIUM,
            category=AlertCategory.REMINDER,
            is_active=i != 1  # Make one inactive
        )
        cds_service.create_rule(tenant_id=tenant_id, data=data)

    active = cds_service.get_active_rules(tenant_id=tenant_id)

    assert all(r.is_active for r in active)


# ============================================================================
# RULE EVALUATION TESTS
# ============================================================================

def test_evaluate_drug_interaction_rule(cds_service, tenant_id, patient_id):
    """Test evaluating drug interaction rules"""
    # Create a drug interaction rule
    rule_data = CDSRuleCreate(
        name="Warfarin-NSAID Interaction",
        description="Alert when prescribing NSAIDs to patient on Warfarin",
        rule_type="drug_interaction",
        conditions={
            "current_medication": "Warfarin",
            "new_medication_class": "NSAID"
        },
        actions={
            "alert_type": "warning",
            "message": "NSAIDs increase bleeding risk in patients on Warfarin"
        },
        severity=AlertSeverity.HIGH,
        category=AlertCategory.DRUG_INTERACTION,
        is_active=True
    )
    cds_service.create_rule(tenant_id=tenant_id, data=rule_data)

    # Evaluate rules for a patient context
    context = {
        "patient_id": str(patient_id),
        "current_medications": ["Warfarin"],
        "new_medication": "Ibuprofen",
        "new_medication_class": "NSAID"
    }

    alerts = cds_service.evaluate_rules(
        tenant_id=tenant_id,
        context=context,
        rule_type="drug_interaction"
    )

    # Should trigger an alert
    assert len(alerts) > 0


def test_evaluate_allergy_rule(cds_service, tenant_id, patient_id):
    """Test evaluating allergy rules"""
    rule_data = CDSRuleCreate(
        name="Penicillin Allergy Check",
        description="Alert when prescribing penicillin to allergic patient",
        rule_type="allergy",
        conditions={
            "allergy": "Penicillin",
            "medication_class": "Penicillin"
        },
        actions={
            "alert_type": "warning",
            "message": "Patient has documented Penicillin allergy"
        },
        severity=AlertSeverity.CRITICAL,
        category=AlertCategory.ALLERGY,
        is_active=True
    )
    cds_service.create_rule(tenant_id=tenant_id, data=rule_data)

    context = {
        "patient_id": str(patient_id),
        "allergies": ["Penicillin"],
        "new_medication": "Amoxicillin",
        "medication_class": "Penicillin"
    }

    alerts = cds_service.evaluate_rules(
        tenant_id=tenant_id,
        context=context,
        rule_type="allergy"
    )

    assert len(alerts) > 0
    assert any(a.severity == AlertSeverity.CRITICAL for a in alerts)


def test_evaluate_care_gap_rule(cds_service, tenant_id, patient_id):
    """Test evaluating care gap rules"""
    rule_data = CDSRuleCreate(
        name="Annual Diabetic Eye Exam",
        description="Alert if diabetic patient has not had eye exam in 12 months",
        rule_type="care_gap",
        conditions={
            "condition": "diabetes",
            "exam_type": "eye_exam",
            "days_since_last": "> 365"
        },
        actions={
            "alert_type": "reminder",
            "message": "Annual diabetic eye exam is overdue"
        },
        severity=AlertSeverity.MEDIUM,
        category=AlertCategory.CARE_GAP,
        is_active=True
    )
    cds_service.create_rule(tenant_id=tenant_id, data=rule_data)

    context = {
        "patient_id": str(patient_id),
        "conditions": ["diabetes"],
        "last_eye_exam_days": 400
    }

    alerts = cds_service.evaluate_rules(
        tenant_id=tenant_id,
        context=context,
        rule_type="care_gap"
    )

    assert len(alerts) > 0


# ============================================================================
# ALERT STATISTICS TESTS
# ============================================================================

def test_get_alert_statistics(cds_service, tenant_id, patient_id):
    """Test getting alert statistics"""
    # Create various alerts
    for severity in AlertSeverity:
        for i in range(2):
            data = ClinicalAlertCreate(
                patient_id=patient_id,
                title=f"{severity.value} Alert {i}",
                message=f"Message {i}",
                severity=severity,
                category=AlertCategory.REMINDER
            )
            cds_service.create_alert(tenant_id=tenant_id, data=data)

    stats = cds_service.get_alert_statistics(
        tenant_id=tenant_id,
        patient_id=patient_id
    )

    assert "total" in stats
    assert "by_severity" in stats
    assert "by_category" in stats


def test_get_override_rate(cds_service, tenant_id, patient_id, provider_id):
    """Test calculating alert override rate"""
    # Create and respond to alerts
    for i in range(10):
        data = ClinicalAlertCreate(
            patient_id=patient_id,
            title=f"Alert {i}",
            message=f"Message {i}",
            severity=AlertSeverity.MEDIUM,
            category=AlertCategory.DRUG_INTERACTION
        )
        alert = cds_service.create_alert(tenant_id=tenant_id, data=data)

        # Override some alerts
        if i < 3:
            cds_service.override_alert(
                tenant_id=tenant_id,
                alert_id=alert.id,
                overridden_by=provider_id,
                reason="Clinical judgment"
            )
        else:
            cds_service.acknowledge_alert(
                tenant_id=tenant_id,
                alert_id=alert.id,
                acknowledged_by=provider_id
            )

    override_rate = cds_service.get_override_rate(
        tenant_id=tenant_id,
        category=AlertCategory.DRUG_INTERACTION,
        days=30
    )

    assert 0.0 <= override_rate <= 1.0


# ============================================================================
# MULTI-TENANCY TESTS
# ============================================================================

def test_tenant_isolation_alerts(cds_service, sample_alert_data):
    """Test that alerts are isolated by tenant"""
    tenant1 = UUID("00000000-0000-0000-0000-000000000001")
    tenant2 = UUID("00000000-0000-0000-0000-000000000002")

    # Create alert for tenant1
    created = cds_service.create_alert(
        tenant_id=tenant1,
        data=sample_alert_data
    )

    # Try to retrieve it as tenant2
    retrieved = cds_service.get_alert(
        tenant_id=tenant2,
        alert_id=created.id
    )

    assert retrieved is None


def test_tenant_isolation_rules(cds_service, sample_rule_data):
    """Test that CDS rules are isolated by tenant"""
    tenant1 = UUID("00000000-0000-0000-0000-000000000001")
    tenant2 = UUID("00000000-0000-0000-0000-000000000002")

    # Create rule for tenant1
    created = cds_service.create_rule(
        tenant_id=tenant1,
        data=sample_rule_data
    )

    # Try to retrieve it as tenant2
    retrieved = cds_service.get_rule(
        tenant_id=tenant2,
        rule_id=created.id
    )

    assert retrieved is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
