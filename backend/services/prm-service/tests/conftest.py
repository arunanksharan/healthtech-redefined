"""
Shared test fixtures and configuration for PRM Service tests
"""
import sys
from pathlib import Path
from typing import Generator, AsyncGenerator
from uuid import uuid4
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from faker import Faker

# Add parent directories to path
prm_service_dir = Path(__file__).parent.parent
backend_dir = prm_service_dir.parent.parent
sys.path.insert(0, str(prm_service_dir))
sys.path.insert(0, str(backend_dir))

from shared.database.models import Base
from core.config import settings

# Initialize Faker
fake = Faker()


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def test_db_engine():
    """
    Create an in-memory SQLite database for testing.
    Using SQLite for fast, isolated tests.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_db_engine) -> Generator[Session, None, None]:
    """
    Create a new database session for each test.
    Rolls back after test to ensure isolation.
    """
    connection = test_db_engine.connect()
    transaction = connection.begin()

    # Create session bound to the connection
    TestSessionLocal = sessionmaker(bind=connection)
    session = TestSessionLocal()

    yield session

    # Rollback transaction and close
    session.close()
    transaction.rollback()
    connection.close()


# ============================================================================
# Organization & Tenant Fixtures
# ============================================================================

@pytest.fixture
def test_org_id():
    """Generate a test organization ID"""
    return uuid4()


@pytest.fixture
def test_tenant(db_session, test_org_id):
    """Create a test tenant/organization"""
    from shared.database.models import Tenant

    tenant = Tenant(
        id=test_org_id,
        name="Test Healthcare Organization",
        type="hospital",
        status="active",
        created_at=datetime.utcnow()
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    return tenant


# ============================================================================
# Patient Fixtures
# ============================================================================

@pytest.fixture
def test_patient_id():
    """Generate a test patient ID"""
    return uuid4()


@pytest.fixture
def test_patient(db_session, test_org_id, test_patient_id):
    """Create a test patient"""
    from shared.database.models import Patient

    patient = Patient(
        id=test_patient_id,
        tenant_id=test_org_id,
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=90),
        gender=fake.random_element(["male", "female", "other"]),
        phone_primary=fake.phone_number(),
        email=fake.email(),
        created_at=datetime.utcnow()
    )
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)

    return patient


@pytest.fixture
def test_patient_data(test_org_id):
    """Generate test patient data (not in DB)"""
    return {
        "tenant_id": test_org_id,
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=90).isoformat(),
        "gender": fake.random_element(["male", "female", "other"]),
        "phone_primary": fake.phone_number(),
        "email": fake.email()
    }


# ============================================================================
# User & Practitioner Fixtures
# ============================================================================

@pytest.fixture
def test_user_id():
    """Generate a test user ID"""
    return uuid4()


@pytest.fixture
def test_practitioner(db_session, test_org_id, test_user_id):
    """Create a test practitioner/provider"""
    from shared.database.models import User, Practitioner

    # Create user
    user = User(
        id=test_user_id,
        tenant_id=test_org_id,
        email=fake.email(),
        full_name=f"Dr. {fake.name()}",
        role="doctor",
        is_active=True,
        created_at=datetime.utcnow()
    )
    db_session.add(user)

    # Create practitioner
    practitioner = Practitioner(
        id=uuid4(),
        tenant_id=test_org_id,
        user_id=test_user_id,
        specialty="General Practice",
        license_number=fake.bothify(text="??####"),
        is_active=True,
        created_at=datetime.utcnow()
    )
    db_session.add(practitioner)

    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(practitioner)

    return practitioner


# ============================================================================
# Journey Fixtures
# ============================================================================

@pytest.fixture
def test_journey_definition_data(test_org_id):
    """Generate test journey definition data"""
    return {
        "name": "Patient Onboarding Journey",
        "description": "Standard onboarding workflow for new patients",
        "org_id": test_org_id,
        "is_active": True,
        "stages": [
            {
                "name": "Welcome",
                "description": "Send welcome message",
                "order": 1,
                "actions": [{"type": "send_message", "template": "welcome"}]
            },
            {
                "name": "Collect Info",
                "description": "Collect patient information",
                "order": 2,
                "actions": [{"type": "collect_data", "fields": ["symptoms"]}]
            },
            {
                "name": "Book Appointment",
                "description": "Schedule appointment",
                "order": 3,
                "actions": [{"type": "book_appointment"}]
            }
        ]
    }


# ============================================================================
# Communication Fixtures
# ============================================================================

@pytest.fixture
def test_whatsapp_communication_data(test_org_id, test_patient_id):
    """Generate WhatsApp communication data"""
    return {
        "org_id": test_org_id,
        "patient_id": test_patient_id,
        "channel": "whatsapp",
        "recipient": "+1234567890",
        "content": {
            "body": "Your appointment is confirmed for tomorrow at 10 AM",
            "template_name": "appointment_confirmation"
        },
        "scheduled_at": None
    }


# ============================================================================
# Appointment Fixtures
# ============================================================================

@pytest.fixture
def test_appointment_data(test_org_id, test_patient_id, test_user_id):
    """Generate appointment data"""
    start_time = datetime.utcnow() + timedelta(days=1)
    return {
        "org_id": test_org_id,
        "patient_id": test_patient_id,
        "provider_id": test_user_id,
        "appointment_type": "consultation",
        "start_time": start_time,
        "end_time": start_time + timedelta(minutes=30),
        "status": "scheduled",
        "reason": "General checkup"
    }


# ============================================================================
# Conversation Fixtures
# ============================================================================

@pytest.fixture
def test_conversation_data(test_org_id, test_patient_id):
    """Generate conversation data"""
    return {
        "org_id": test_org_id,
        "patient_id": test_patient_id,
        "channel": "whatsapp",
        "phone_number": "+1234567890",
        "state": "active",
        "context": {}
    }


# ============================================================================
# Ticket Fixtures
# ============================================================================

@pytest.fixture
def test_ticket_data(test_org_id, test_patient_id):
    """Generate ticket data"""
    return {
        "org_id": test_org_id,
        "patient_id": test_patient_id,
        "title": "Patient inquiry about test results",
        "description": "Patient wants to know when test results will be available",
        "category": "inquiry",
        "priority": "medium",
        "status": "open"
    }


# ============================================================================
# Intake Fixtures
# ============================================================================

@pytest.fixture
def test_intake_session_data(test_org_id, test_patient_id):
    """Generate intake session data"""
    return {
        "org_id": test_org_id,
        "patient_id": test_patient_id,
        "conversation_id": None,
        "status": "open",
        "context": {"channel": "web", "locale": "en"}
    }


@pytest.fixture
def test_intake_records_data():
    """Generate intake records data"""
    return {
        "chief_complaint": {
            "text": "Persistent headache for 3 days"
        },
        "symptoms": [
            {
                "client_item_id": "sym_001",
                "code": {"system": "SNOMED", "code": "25064002"},
                "onset": "3_days_ago",
                "severity": "moderate",
                "notes": "Pain increases in the evening"
            }
        ],
        "allergies": [
            {
                "client_item_id": "allergy_001",
                "substance": "Penicillin",
                "reaction": "Rash",
                "severity": "moderate"
            }
        ],
        "medications": [
            {
                "client_item_id": "med_001",
                "name": "Ibuprofen",
                "dose": "200mg",
                "schedule": "As needed",
                "adherence": "good"
            }
        ]
    }


# ============================================================================
# Mock Service Fixtures
# ============================================================================

@pytest.fixture
def mock_redis(mocker):
    """Mock Redis client"""
    mock = mocker.MagicMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = 1
    return mock


@pytest.fixture
def mock_twilio(mocker):
    """Mock Twilio client"""
    mock = mocker.MagicMock()
    mock.messages.create.return_value.sid = "SM" + fake.uuid4()[:32]
    return mock


@pytest.fixture
def mock_s3(mocker):
    """Mock S3/boto3 client"""
    mock = mocker.MagicMock()
    mock.generate_presigned_url.return_value = f"https://s3.amazonaws.com/test-bucket/test-file?{fake.uuid4()}"
    return mock


@pytest.fixture
def mock_openai(mocker):
    """Mock OpenAI client"""
    mock = mocker.MagicMock()

    # Mock embeddings
    mock.embeddings.create.return_value.data = [
        type('obj', (object,), {'embedding': [0.1] * 384})()
    ]

    return mock


@pytest.fixture
def mock_event_publisher(mocker):
    """Mock event publisher"""
    return mocker.patch('shared.events.publisher.publish_event')


# ============================================================================
# Time Fixtures
# ============================================================================

@pytest.fixture
def freeze_time(mocker):
    """Freeze time for consistent testing"""
    frozen_time = datetime(2024, 11, 19, 12, 0, 0)
    mocker.patch('datetime.datetime').utcnow.return_value = frozen_time
    return frozen_time


# ============================================================================
# Async Fixtures
# ============================================================================

@pytest.fixture
async def async_db_session(test_db_engine) -> AsyncGenerator[Session, None]:
    """
    Create an async database session for async tests.
    Note: For simplicity, using sync session in async context.
    """
    connection = test_db_engine.connect()
    transaction = connection.begin()

    TestSessionLocal = sessionmaker(bind=connection)
    session = TestSessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ============================================================================
# Utility Functions
# ============================================================================

def assert_dict_subset(subset: dict, superset: dict):
    """Assert that subset is contained in superset"""
    for key, value in subset.items():
        assert key in superset, f"Key '{key}' not in superset"
        assert superset[key] == value, f"Value mismatch for key '{key}': {superset[key]} != {value}"


def assert_uuid_valid(value: str):
    """Assert that string is a valid UUID"""
    from uuid import UUID
    try:
        UUID(str(value))
    except ValueError:
        pytest.fail(f"'{value}' is not a valid UUID")
