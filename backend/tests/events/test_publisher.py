"""
Unit tests for event publisher
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

from shared.events import EventPublisher, publish_event, EventType


@pytest.fixture
def mock_producer():
    """Mock Kafka producer"""
    with patch("shared.events.publisher.Producer") as mock:
        producer = Mock()
        producer.produce = Mock()
        producer.poll = Mock()
        producer.flush = Mock()
        mock.return_value = producer
        yield producer


@pytest.fixture
def publisher(mock_producer):
    """Create event publisher instance"""
    return EventPublisher()


class TestEventPublisher:
    """Test EventPublisher class"""

    def test_init(self, publisher):
        """Test publisher initialization"""
        assert publisher is not None
        assert publisher.topic_prefix == "healthtech"

    def test_get_topic(self, publisher):
        """Test topic routing"""
        topic = publisher._get_topic(EventType.PATIENT_CREATED)
        assert topic == "healthtech.patient.events"

        topic = publisher._get_topic(EventType.APPOINTMENT_CREATED)
        assert topic == "healthtech.appointment.events"

    @pytest.mark.asyncio
    async def test_publish_event(self, publisher, mock_producer):
        """Test event publishing"""
        tenant_id = str(uuid4())
        payload = {"patient_id": "PAT-123", "name": "John Doe"}

        event_id = await publisher.publish(
            event_type=EventType.PATIENT_CREATED,
            tenant_id=tenant_id,
            payload=payload,
            source_service="test-service",
        )

        assert event_id is not None
        assert mock_producer.produce.called

    @pytest.mark.asyncio
    async def test_publish_with_metadata(self, publisher):
        """Test publishing with metadata"""
        metadata = {"request_id": "REQ-123"}

        event_id = await publisher.publish(
            event_type=EventType.PATIENT_CREATED,
            tenant_id="tenant-1",
            payload={"patient_id": "PAT-123"},
            metadata=metadata,
        )

        assert event_id is not None

    @pytest.mark.asyncio
    async def test_publish_multiple_events(self, publisher):
        """Test publishing multiple events"""
        events = []

        for i in range(10):
            event_id = await publisher.publish(
                event_type=EventType.PATIENT_CREATED,
                tenant_id="tenant-1",
                payload={"patient_id": f"PAT-{i}"},
            )
            events.append(event_id)

        assert len(events) == 10
        assert len(set(events)) == 10  # All unique


@pytest.mark.asyncio
async def test_publish_event_convenience_function():
    """Test publish_event convenience function"""
    with patch("shared.events.publisher.get_publisher") as mock_get_pub:
        mock_pub = Mock()
        mock_pub.publish = AsyncMock(return_value="event-123")
        mock_get_pub.return_value = mock_pub

        event_id = await publish_event(
            event_type=EventType.PATIENT_CREATED,
            tenant_id="tenant-1",
            payload={"patient_id": "PAT-123"},
        )

        assert event_id == "event-123"
        assert mock_pub.publish.called
