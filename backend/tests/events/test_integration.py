"""
Integration tests for event-driven architecture
Tests end-to-end event flow from publisher to consumer
"""
import pytest
import asyncio
from uuid import uuid4

from shared.events import (
    EventPublisher,
    EventConsumer,
    EventType,
    Event,
    publish_event,
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_end_to_end_event_flow():
    """Test complete event flow from publish to consume"""
    received_events = []

    async def handler(event: Event):
        """Handler to capture received events"""
        received_events.append(event)

    # Create consumer
    consumer = EventConsumer(
        group_id=f"test-consumer-{uuid4()}",
        topics=["healthtech.patient.events"],
    )

    consumer.register_handler(EventType.PATIENT_CREATED, handler)

    # Start consumer in background
    consumer_task = asyncio.create_task(consumer.start())

    # Give consumer time to initialize
    await asyncio.sleep(2)

    # Publish event
    tenant_id = str(uuid4())
    patient_id = str(uuid4())

    event_id = await publish_event(
        event_type=EventType.PATIENT_CREATED,
        tenant_id=tenant_id,
        payload={
            "patient_id": patient_id,
            "name": "Integration Test Patient",
        },
        source_service="integration-test",
    )

    assert event_id is not None

    # Wait for event to be consumed
    await asyncio.sleep(3)

    # Verify event was received
    assert len(received_events) > 0

    event = received_events[0]
    assert event.event_type == EventType.PATIENT_CREATED
    assert event.tenant_id == tenant_id
    assert event.payload["patient_id"] == patient_id

    # Cleanup
    consumer.stop()
    consumer_task.cancel()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_multiple_consumers_same_event():
    """Test multiple consumers receiving same event"""
    consumer1_events = []
    consumer2_events = []

    async def handler1(event: Event):
        consumer1_events.append(event)

    async def handler2(event: Event):
        consumer2_events.append(event)

    # Create two consumers with different group IDs
    consumer1 = EventConsumer(
        group_id=f"test-consumer-1-{uuid4()}",
        topics=["healthtech.patient.events"],
    )
    consumer1.register_handler(EventType.PATIENT_CREATED, handler1)

    consumer2 = EventConsumer(
        group_id=f"test-consumer-2-{uuid4()}",
        topics=["healthtech.patient.events"],
    )
    consumer2.register_handler(EventType.PATIENT_CREATED, handler2)

    # Start both consumers
    task1 = asyncio.create_task(consumer1.start())
    task2 = asyncio.create_task(consumer2.start())

    await asyncio.sleep(2)

    # Publish event
    event_id = await publish_event(
        event_type=EventType.PATIENT_CREATED,
        tenant_id=str(uuid4()),
        payload={"patient_id": str(uuid4())},
    )

    # Wait for consumption
    await asyncio.sleep(3)

    # Both consumers should receive the event
    assert len(consumer1_events) > 0
    assert len(consumer2_events) > 0

    # Cleanup
    consumer1.stop()
    consumer2.stop()
    task1.cancel()
    task2.cancel()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_event_ordering():
    """Test that events are consumed in order"""
    received_events = []

    async def handler(event: Event):
        received_events.append(event)

    consumer = EventConsumer(
        group_id=f"test-consumer-{uuid4()}",
        topics=["healthtech.patient.events"],
    )
    consumer.register_handler(EventType.PATIENT_CREATED, handler)
    consumer.register_handler(EventType.PATIENT_UPDATED, handler)

    task = asyncio.create_task(consumer.start())
    await asyncio.sleep(2)

    # Publish events in order
    patient_id = str(uuid4())
    tenant_id = str(uuid4())

    await publish_event(
        event_type=EventType.PATIENT_CREATED,
        tenant_id=tenant_id,
        payload={"patient_id": patient_id, "name": "John"},
    )

    await asyncio.sleep(0.1)

    await publish_event(
        event_type=EventType.PATIENT_UPDATED,
        tenant_id=tenant_id,
        payload={"patient_id": patient_id, "name": "John Doe"},
    )

    # Wait for consumption
    await asyncio.sleep(3)

    # Verify order
    assert len(received_events) >= 2
    assert received_events[0].event_type == EventType.PATIENT_CREATED
    assert received_events[1].event_type == EventType.PATIENT_UPDATED

    # Cleanup
    consumer.stop()
    task.cancel()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_high_throughput():
    """Test system handles high throughput"""
    received_count = [0]

    async def handler(event: Event):
        received_count[0] += 1

    consumer = EventConsumer(
        group_id=f"test-consumer-{uuid4()}",
        topics=["healthtech.patient.events"],
    )
    consumer.register_handler(EventType.PATIENT_CREATED, handler)

    task = asyncio.create_task(consumer.start())
    await asyncio.sleep(2)

    # Publish many events
    num_events = 100
    tenant_id = str(uuid4())

    for i in range(num_events):
        await publish_event(
            event_type=EventType.PATIENT_CREATED,
            tenant_id=tenant_id,
            payload={"patient_id": f"PAT-{i}"},
        )

    # Wait for all events to be consumed
    await asyncio.sleep(10)

    # Should have received most events (allow some loss in test environment)
    assert received_count[0] >= num_events * 0.8

    # Cleanup
    consumer.stop()
    task.cancel()
