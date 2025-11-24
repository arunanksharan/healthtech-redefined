"""
Unit tests for event store
"""
import pytest
from unittest.mock import Mock, MagicMock
from uuid import uuid4
from datetime import datetime

from shared.events import EventStore, ConcurrencyError, EventType, PatientAggregate


@pytest.fixture
def mock_db():
    """Mock database session"""
    db = Mock()
    db.add = Mock()
    db.commit = Mock()
    db.query = Mock()
    return db


@pytest.fixture
def event_store(mock_db):
    """Create event store instance"""
    return EventStore(mock_db)


class TestEventStore:
    """Test EventStore class"""

    @pytest.mark.asyncio
    async def test_append_event(self, event_store, mock_db):
        """Test appending event to store"""
        patient_id = uuid4()

        # Mock version check
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0

        event_id = await event_store.append_event(
            aggregate_type="Patient",
            aggregate_id=patient_id,
            event_type=EventType.PATIENT_CREATED,
            event_data={"name": "John Doe"},
            tenant_id="tenant-1",
            version=1,
        )

        assert event_id is not None
        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_concurrency_error(self, event_store, mock_db):
        """Test concurrency error on version mismatch"""
        patient_id = uuid4()

        # Mock version check - current version is 2
        mock_db.query.return_value.filter.return_value.scalar.return_value = 2

        with pytest.raises(ConcurrencyError):
            await event_store.append_event(
                aggregate_type="Patient",
                aggregate_id=patient_id,
                event_type=EventType.PATIENT_UPDATED,
                event_data={"name": "Jane Doe"},
                tenant_id="tenant-1",
                version=1,  # Trying to append version 1 when current is 2
            )

    def test_get_aggregate_version(self, event_store, mock_db):
        """Test getting aggregate version"""
        patient_id = uuid4()

        mock_db.query.return_value.filter.return_value.scalar.return_value = 5

        version = event_store.get_aggregate_version(patient_id)

        assert version == 5

    def test_get_aggregate_version_no_events(self, event_store, mock_db):
        """Test getting version for aggregate with no events"""
        patient_id = uuid4()

        mock_db.query.return_value.filter.return_value.scalar.return_value = None

        version = event_store.get_aggregate_version(patient_id)

        assert version == 0

    @pytest.mark.asyncio
    async def test_save_snapshot(self, event_store, mock_db):
        """Test saving aggregate snapshot"""
        patient_id = uuid4()

        await event_store.save_snapshot(
            aggregate_type="Patient",
            aggregate_id=patient_id,
            state={"name": "John Doe", "email": "john@example.com"},
            version=10,
            tenant_id="tenant-1",
        )

        assert mock_db.add.called
        assert mock_db.commit.called


class TestPatientAggregate:
    """Test PatientAggregate class"""

    def test_apply_patient_created(self):
        """Test applying PatientCreated event"""
        from shared.events.types import Event

        aggregate = PatientAggregate()
        patient_id = uuid4()

        event = Event(
            event_type=EventType.PATIENT_CREATED,
            tenant_id="tenant-1",
            payload={
                "patient_id": str(patient_id),
                "name": "John Doe",
                "email": "john@example.com",
            },
        )

        aggregate.apply_event(event)

        assert aggregate.id == patient_id
        assert aggregate.name == "John Doe"
        assert aggregate.email == "john@example.com"
        assert aggregate.version == 1

    def test_apply_patient_updated(self):
        """Test applying PatientUpdated event"""
        from shared.events.types import Event

        aggregate = PatientAggregate()
        patient_id = uuid4()

        # First create
        create_event = Event(
            event_type=EventType.PATIENT_CREATED,
            tenant_id="tenant-1",
            payload={
                "patient_id": str(patient_id),
                "name": "John Doe",
                "email": "john@example.com",
            },
        )
        aggregate.apply_event(create_event)

        # Then update
        update_event = Event(
            event_type=EventType.PATIENT_UPDATED,
            tenant_id="tenant-1",
            payload={"email": "john.doe@example.com"},
        )
        aggregate.apply_event(update_event)

        assert aggregate.email == "john.doe@example.com"
        assert aggregate.version == 2

    def test_to_snapshot(self):
        """Test converting aggregate to snapshot"""
        aggregate = PatientAggregate()
        aggregate.id = uuid4()
        aggregate.name = "John Doe"
        aggregate.email = "john@example.com"
        aggregate.version = 5

        snapshot = aggregate.to_snapshot()

        assert snapshot["id"] == str(aggregate.id)
        assert snapshot["name"] == "John Doe"
        assert snapshot["email"] == "john@example.com"
        assert snapshot["version"] == 5

    def test_from_snapshot(self):
        """Test creating aggregate from snapshot"""
        patient_id = uuid4()
        snapshot = {
            "id": str(patient_id),
            "name": "John Doe",
            "email": "john@example.com",
            "version": 5,
        }

        aggregate = PatientAggregate.from_snapshot(snapshot)

        assert aggregate.id == patient_id
        assert aggregate.name == "John Doe"
        assert aggregate.email == "john@example.com"
        assert aggregate.version == 5
