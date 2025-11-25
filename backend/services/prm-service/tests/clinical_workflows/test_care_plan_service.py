"""
Test Care Plan Service
Unit tests for care plan management (US-006.7)
"""
import pytest
from uuid import uuid4, UUID
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../..")))

from services.prm_service.modules.clinical_workflows.models import (
    Base, CarePlan, CareGoal, GoalProgress, CareIntervention, CareTeamMember
)
from services.prm_service.modules.clinical_workflows.schemas import (
    CarePlanCreate, CareGoalCreate, GoalProgressCreate, CareInterventionCreate,
    CarePlanStatus, CarePlanCategory, GoalStatus, GoalPriority
)
from services.prm_service.modules.clinical_workflows.service import CarePlanService


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
def care_plan_service(db_session):
    """Create a care plan service instance"""
    return CarePlanService(db_session)


@pytest.fixture
def tenant_id():
    """Test tenant ID"""
    return UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def patient_id():
    """Test patient ID"""
    return UUID("00000000-0000-0000-0000-000000000002")


@pytest.fixture
def author_id():
    """Test author ID"""
    return UUID("00000000-0000-0000-0000-000000000003")


@pytest.fixture
def sample_care_plan_data(patient_id, author_id):
    """Sample care plan data"""
    return CarePlanCreate(
        patient_id=patient_id,
        author_id=author_id,
        title="Diabetes Management Plan",
        description="Comprehensive care plan for Type 2 diabetes management",
        category=CarePlanCategory.CHRONIC_DISEASE,
        conditions=["E11.9 - Type 2 diabetes mellitus without complications"],
        start_date=date.today(),
        end_date=date.today() + timedelta(days=365),
        review_date=date.today() + timedelta(days=90)
    )


@pytest.fixture
def sample_goal_data(patient_id):
    """Sample care goal data"""
    return CareGoalCreate(
        patient_id=patient_id,
        description="Reduce HbA1c to below 7%",
        target_value="< 7%",
        current_value="8.5%",
        priority=GoalPriority.HIGH,
        due_date=date.today() + timedelta(days=90),
        measure="HbA1c percentage"
    )


# ============================================================================
# CREATE CARE PLAN TESTS
# ============================================================================

def test_create_care_plan(care_plan_service, tenant_id, sample_care_plan_data):
    """Test creating a new care plan"""
    plan = care_plan_service.create_care_plan(
        tenant_id=tenant_id,
        data=sample_care_plan_data
    )

    assert plan is not None
    assert plan.id is not None
    assert plan.title == "Diabetes Management Plan"
    assert plan.status == CarePlanStatus.DRAFT
    assert plan.tenant_id == tenant_id


def test_create_care_plan_different_categories(
    care_plan_service, tenant_id, patient_id, author_id
):
    """Test creating care plans with different categories"""
    categories = [
        (CarePlanCategory.PREVENTIVE, "Annual Wellness Plan"),
        (CarePlanCategory.CHRONIC_DISEASE, "Heart Failure Management"),
        (CarePlanCategory.POST_SURGICAL, "Post Knee Replacement Care"),
        (CarePlanCategory.MENTAL_HEALTH, "Depression Treatment Plan"),
        (CarePlanCategory.REHABILITATION, "Stroke Rehabilitation Plan")
    ]

    for category, title in categories:
        data = CarePlanCreate(
            patient_id=patient_id,
            author_id=author_id,
            title=title,
            description=f"Care plan for {title}",
            category=category,
            start_date=date.today()
        )

        plan = care_plan_service.create_care_plan(
            tenant_id=tenant_id,
            data=data
        )

        assert plan.category == category
        assert plan.title == title


# ============================================================================
# CARE PLAN STATUS WORKFLOW TESTS
# ============================================================================

def test_activate_care_plan(care_plan_service, tenant_id, sample_care_plan_data):
    """Test activating a draft care plan"""
    plan = care_plan_service.create_care_plan(
        tenant_id=tenant_id,
        data=sample_care_plan_data
    )

    activated = care_plan_service.activate_care_plan(
        tenant_id=tenant_id,
        plan_id=plan.id
    )

    assert activated.status == CarePlanStatus.ACTIVE
    assert activated.activated_at is not None


def test_suspend_care_plan(care_plan_service, tenant_id, sample_care_plan_data):
    """Test suspending an active care plan"""
    plan = care_plan_service.create_care_plan(
        tenant_id=tenant_id,
        data=sample_care_plan_data
    )

    care_plan_service.activate_care_plan(
        tenant_id=tenant_id,
        plan_id=plan.id
    )

    suspended = care_plan_service.suspend_care_plan(
        tenant_id=tenant_id,
        plan_id=plan.id,
        reason="Patient hospitalized"
    )

    assert suspended.status == CarePlanStatus.ON_HOLD


def test_complete_care_plan(care_plan_service, tenant_id, sample_care_plan_data):
    """Test completing a care plan"""
    plan = care_plan_service.create_care_plan(
        tenant_id=tenant_id,
        data=sample_care_plan_data
    )

    care_plan_service.activate_care_plan(
        tenant_id=tenant_id,
        plan_id=plan.id
    )

    completed = care_plan_service.complete_care_plan(
        tenant_id=tenant_id,
        plan_id=plan.id,
        outcome="Goals achieved"
    )

    assert completed.status == CarePlanStatus.COMPLETED
    assert completed.completed_at is not None


def test_revoke_care_plan(care_plan_service, tenant_id, sample_care_plan_data):
    """Test revoking a care plan"""
    plan = care_plan_service.create_care_plan(
        tenant_id=tenant_id,
        data=sample_care_plan_data
    )

    revoked = care_plan_service.revoke_care_plan(
        tenant_id=tenant_id,
        plan_id=plan.id,
        reason="Patient transferred to another provider"
    )

    assert revoked.status == CarePlanStatus.REVOKED


# ============================================================================
# CARE GOAL TESTS
# ============================================================================

def test_add_goal_to_plan(
    care_plan_service, tenant_id, sample_care_plan_data, sample_goal_data
):
    """Test adding a goal to a care plan"""
    plan = care_plan_service.create_care_plan(
        tenant_id=tenant_id,
        data=sample_care_plan_data
    )

    goal = care_plan_service.add_goal(
        tenant_id=tenant_id,
        plan_id=plan.id,
        data=sample_goal_data
    )

    assert goal is not None
    assert goal.care_plan_id == plan.id
    assert goal.status == GoalStatus.PROPOSED


def test_achieve_goal(
    care_plan_service, tenant_id, sample_care_plan_data, sample_goal_data
):
    """Test marking a goal as achieved"""
    plan = care_plan_service.create_care_plan(
        tenant_id=tenant_id,
        data=sample_care_plan_data
    )

    goal = care_plan_service.add_goal(
        tenant_id=tenant_id,
        plan_id=plan.id,
        data=sample_goal_data
    )

    # Start the goal
    care_plan_service.start_goal(
        tenant_id=tenant_id,
        goal_id=goal.id
    )

    # Achieve the goal
    achieved = care_plan_service.achieve_goal(
        tenant_id=tenant_id,
        goal_id=goal.id,
        outcome="HbA1c reduced to 6.8%"
    )

    assert achieved.status == GoalStatus.ACHIEVED
    assert achieved.achieved_at is not None


def test_cancel_goal(
    care_plan_service, tenant_id, sample_care_plan_data, sample_goal_data
):
    """Test canceling a goal"""
    plan = care_plan_service.create_care_plan(
        tenant_id=tenant_id,
        data=sample_care_plan_data
    )

    goal = care_plan_service.add_goal(
        tenant_id=tenant_id,
        plan_id=plan.id,
        data=sample_goal_data
    )

    cancelled = care_plan_service.cancel_goal(
        tenant_id=tenant_id,
        goal_id=goal.id,
        reason="Goal no longer clinically appropriate"
    )

    assert cancelled.status == GoalStatus.CANCELLED


# ============================================================================
# GOAL PROGRESS TESTS
# ============================================================================

def test_record_goal_progress(
    care_plan_service, tenant_id, sample_care_plan_data, sample_goal_data, author_id
):
    """Test recording progress toward a goal"""
    plan = care_plan_service.create_care_plan(
        tenant_id=tenant_id,
        data=sample_care_plan_data
    )

    goal = care_plan_service.add_goal(
        tenant_id=tenant_id,
        plan_id=plan.id,
        data=sample_goal_data
    )

    care_plan_service.start_goal(
        tenant_id=tenant_id,
        goal_id=goal.id
    )

    progress_data = GoalProgressCreate(
        goal_id=goal.id,
        recorded_by=author_id,
        value="7.8%",
        notes="Improvement from initial 8.5%"
    )

    progress = care_plan_service.record_progress(
        tenant_id=tenant_id,
        data=progress_data
    )

    assert progress is not None
    assert progress.value == "7.8%"


def test_get_goal_progress_history(
    care_plan_service, tenant_id, sample_care_plan_data, sample_goal_data, author_id
):
    """Test retrieving goal progress history"""
    plan = care_plan_service.create_care_plan(
        tenant_id=tenant_id,
        data=sample_care_plan_data
    )

    goal = care_plan_service.add_goal(
        tenant_id=tenant_id,
        plan_id=plan.id,
        data=sample_goal_data
    )

    care_plan_service.start_goal(
        tenant_id=tenant_id,
        goal_id=goal.id
    )

    # Record multiple progress entries
    values = ["8.2%", "7.9%", "7.5%", "7.1%"]
    for value in values:
        progress_data = GoalProgressCreate(
            goal_id=goal.id,
            recorded_by=author_id,
            value=value,
            notes=f"Progress measurement: {value}"
        )
        care_plan_service.record_progress(
            tenant_id=tenant_id,
            data=progress_data
        )

    history = care_plan_service.get_goal_progress(
        tenant_id=tenant_id,
        goal_id=goal.id
    )

    assert len(history) == 4


# ============================================================================
# CARE INTERVENTION TESTS
# ============================================================================

def test_add_intervention(
    care_plan_service, tenant_id, sample_care_plan_data, patient_id
):
    """Test adding an intervention to a care plan"""
    plan = care_plan_service.create_care_plan(
        tenant_id=tenant_id,
        data=sample_care_plan_data
    )

    intervention_data = CareInterventionCreate(
        patient_id=patient_id,
        care_plan_id=plan.id,
        name="Dietary Counseling",
        description="Meet with dietitian for meal planning",
        frequency="Monthly",
        responsible_party="Dietitian"
    )

    intervention = care_plan_service.add_intervention(
        tenant_id=tenant_id,
        data=intervention_data
    )

    assert intervention is not None
    assert intervention.name == "Dietary Counseling"


def test_complete_intervention(
    care_plan_service, tenant_id, sample_care_plan_data, patient_id, author_id
):
    """Test completing an intervention"""
    plan = care_plan_service.create_care_plan(
        tenant_id=tenant_id,
        data=sample_care_plan_data
    )

    intervention_data = CareInterventionCreate(
        patient_id=patient_id,
        care_plan_id=plan.id,
        name="Blood glucose monitoring training",
        description="Teach patient to use glucometer",
        frequency="Once",
        responsible_party="Nurse Educator"
    )

    intervention = care_plan_service.add_intervention(
        tenant_id=tenant_id,
        data=intervention_data
    )

    completed = care_plan_service.complete_intervention(
        tenant_id=tenant_id,
        intervention_id=intervention.id,
        completed_by=author_id,
        notes="Patient demonstrated competency"
    )

    assert completed.completed_at is not None


# ============================================================================
# CARE TEAM TESTS
# ============================================================================

def test_add_care_team_member(
    care_plan_service, tenant_id, sample_care_plan_data
):
    """Test adding a member to the care team"""
    plan = care_plan_service.create_care_plan(
        tenant_id=tenant_id,
        data=sample_care_plan_data
    )

    member = care_plan_service.add_care_team_member(
        tenant_id=tenant_id,
        plan_id=plan.id,
        member_id=uuid4(),
        role="Primary Care Physician",
        responsibilities="Overall care coordination"
    )

    assert member is not None
    assert member.role == "Primary Care Physician"


def test_get_care_team(
    care_plan_service, tenant_id, sample_care_plan_data
):
    """Test retrieving the care team for a plan"""
    plan = care_plan_service.create_care_plan(
        tenant_id=tenant_id,
        data=sample_care_plan_data
    )

    # Add multiple team members
    roles = [
        ("Primary Care Physician", "Care coordination"),
        ("Endocrinologist", "Diabetes specialist"),
        ("Dietitian", "Nutrition counseling"),
        ("Diabetes Educator", "Patient education")
    ]

    for role, responsibilities in roles:
        care_plan_service.add_care_team_member(
            tenant_id=tenant_id,
            plan_id=plan.id,
            member_id=uuid4(),
            role=role,
            responsibilities=responsibilities
        )

    team = care_plan_service.get_care_team(
        tenant_id=tenant_id,
        plan_id=plan.id
    )

    assert len(team) == 4


# ============================================================================
# CARE PLAN RETRIEVAL TESTS
# ============================================================================

def test_get_care_plan_by_id(care_plan_service, tenant_id, sample_care_plan_data):
    """Test retrieving a care plan by ID"""
    created = care_plan_service.create_care_plan(
        tenant_id=tenant_id,
        data=sample_care_plan_data
    )

    retrieved = care_plan_service.get_care_plan(
        tenant_id=tenant_id,
        plan_id=created.id
    )

    assert retrieved is not None
    assert retrieved.id == created.id


def test_get_patient_care_plans(care_plan_service, tenant_id, patient_id, author_id):
    """Test retrieving all care plans for a patient"""
    # Create multiple care plans
    titles = ["Diabetes Plan", "Hypertension Plan", "Weight Loss Plan"]
    for title in titles:
        data = CarePlanCreate(
            patient_id=patient_id,
            author_id=author_id,
            title=title,
            description=f"Care plan: {title}",
            category=CarePlanCategory.CHRONIC_DISEASE,
            start_date=date.today()
        )
        care_plan_service.create_care_plan(
            tenant_id=tenant_id,
            data=data
        )

    plans = care_plan_service.get_patient_care_plans(
        tenant_id=tenant_id,
        patient_id=patient_id
    )

    assert len(plans) >= 3


def test_get_active_care_plans(care_plan_service, tenant_id, patient_id, author_id):
    """Test retrieving only active care plans"""
    # Create and activate plans
    for i in range(3):
        data = CarePlanCreate(
            patient_id=patient_id,
            author_id=author_id,
            title=f"Active Plan {i}",
            description="Active care plan",
            category=CarePlanCategory.CHRONIC_DISEASE,
            start_date=date.today()
        )
        plan = care_plan_service.create_care_plan(
            tenant_id=tenant_id,
            data=data
        )
        care_plan_service.activate_care_plan(
            tenant_id=tenant_id,
            plan_id=plan.id
        )

    # Create a draft plan (should not be in active list)
    draft_data = CarePlanCreate(
        patient_id=patient_id,
        author_id=author_id,
        title="Draft Plan",
        description="Draft care plan",
        category=CarePlanCategory.CHRONIC_DISEASE,
        start_date=date.today()
    )
    care_plan_service.create_care_plan(
        tenant_id=tenant_id,
        data=draft_data
    )

    active = care_plan_service.get_active_care_plans(
        tenant_id=tenant_id,
        patient_id=patient_id
    )

    assert all(p.status == CarePlanStatus.ACTIVE for p in active)


# ============================================================================
# MULTI-TENANCY TESTS
# ============================================================================

def test_tenant_isolation(care_plan_service, sample_care_plan_data):
    """Test that care plans are isolated by tenant"""
    tenant1 = UUID("00000000-0000-0000-0000-000000000001")
    tenant2 = UUID("00000000-0000-0000-0000-000000000002")

    # Create plan for tenant1
    created = care_plan_service.create_care_plan(
        tenant_id=tenant1,
        data=sample_care_plan_data
    )

    # Try to retrieve it as tenant2
    retrieved = care_plan_service.get_care_plan(
        tenant_id=tenant2,
        plan_id=created.id
    )

    assert retrieved is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
