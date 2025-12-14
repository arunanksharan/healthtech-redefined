"""
Batch event publisher for high-throughput scenarios
Accumulates events and publishes in batches for efficiency
"""
import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from loguru import logger

# Optional Kafka support - graceful fallback if not installed
try:
    from confluent_kafka import Producer
    KAFKA_AVAILABLE = True
except ImportError:
    Producer = None  # type: ignore
    KAFKA_AVAILABLE = False

from .types import Event, EventType


class BatchEventPublisher:
    """
    Batch event publisher for high-throughput scenarios

    Features:
    - Accumulate events in memory
    - Flush on size threshold or time interval
    - Transactional batch publishing
    - Automatic retry on failure
    """

    def __init__(
        self,
        bootstrap_servers: str,
        batch_size: int = 100,
        flush_interval: float = 5.0,
        enable_transactions: bool = False,
    ):
        """
        Initialize batch publisher

        Args:
            bootstrap_servers: Kafka bootstrap servers
            batch_size: Number of events to accumulate before flush
            flush_interval: Maximum seconds between flushes
            enable_transactions: Enable transactional publishing
        """
        self.bootstrap_servers = bootstrap_servers
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.enable_transactions = enable_transactions

        self.batch: List[Event] = []
        self.last_flush_time = datetime.utcnow()
        self.producer: Optional[Producer] = None
        self._running = False
        self._flush_task: Optional[asyncio.Task] = None

        self._init_producer()

    def _init_producer(self):
        """Initialize Kafka producer"""
        try:
            conf = {
                "bootstrap.servers": self.bootstrap_servers,
                "client.id": "batch-publisher",
                "acks": "all",
                "retries": 3,
                "compression.type": "gzip",
                "linger.ms": 100,
                "batch.size": 32768,
            }

            if self.enable_transactions:
                conf["transactional.id"] = "healthtech-batch-publisher"

            self.producer = Producer(conf)

            if self.enable_transactions:
                self.producer.init_transactions()

            logger.info(
                f"Batch publisher initialized: batch_size={self.batch_size}, "
                f"flush_interval={self.flush_interval}s, "
                f"transactions={'enabled' if self.enable_transactions else 'disabled'}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize batch publisher: {e}")
            self.producer = None

    async def add_event(
        self,
        event_type: EventType,
        tenant_id: str,
        payload: Dict[str, Any],
        source_service: Optional[str] = None,
        source_user_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add event to batch

        Args:
            event_type: Type of event
            tenant_id: Tenant identifier
            payload: Event payload data
            source_service: Service that generated the event
            source_user_id: User who triggered the event
            metadata: Additional metadata

        Returns:
            str: Event ID
        """
        event = Event(
            event_type=event_type,
            tenant_id=tenant_id,
            payload=payload,
            source_service=source_service,
            source_user_id=source_user_id,
            metadata=metadata or {},
        )

        self.batch.append(event)

        # Check if batch is full
        if len(self.batch) >= self.batch_size:
            await self.flush()

        return str(event.event_id)

    async def flush(self):
        """Flush accumulated events to Kafka"""
        if not self.batch:
            return

        if not self.producer:
            logger.error("Producer not initialized, cannot flush batch")
            return

        events_to_publish = self.batch.copy()
        self.batch.clear()

        try:
            if self.enable_transactions:
                await self._publish_transactional(events_to_publish)
            else:
                await self._publish_regular(events_to_publish)

            self.last_flush_time = datetime.utcnow()
            logger.debug(f"Flushed batch of {len(events_to_publish)} events")

        except Exception as e:
            logger.error(f"Failed to flush batch: {e}")
            # Add events back to batch for retry
            self.batch.extend(events_to_publish)

    async def _publish_regular(self, events: List[Event]):
        """Publish events without transactions"""
        for event in events:
            topic = self._get_topic(event.event_type)
            event_json = event.model_dump_json()

            self.producer.produce(
                topic=topic,
                key=event.tenant_id.encode("utf-8"),
                value=event_json.encode("utf-8"),
            )

        # Wait for delivery
        self.producer.flush()

    async def _publish_transactional(self, events: List[Event]):
        """Publish events within transaction"""
        self.producer.begin_transaction()

        try:
            for event in events:
                topic = self._get_topic(event.event_type)
                event_json = event.model_dump_json()

                self.producer.produce(
                    topic=topic,
                    key=event.tenant_id.encode("utf-8"),
                    value=event_json.encode("utf-8"),
                )

            self.producer.commit_transaction()
            logger.debug(f"Transaction committed with {len(events)} events")

        except Exception as e:
            logger.error(f"Transaction failed, aborting: {e}")
            self.producer.abort_transaction()
            raise

    def _get_topic(self, event_type: EventType) -> str:
        """Get topic name for event type"""
        domain = event_type.value.split(".")[0].lower()
        return f"healthtech.{domain}.events"

    async def start_auto_flush(self):
        """Start automatic flush on time interval"""
        self._running = True
        self._flush_task = asyncio.create_task(self._auto_flush_loop())
        logger.info("Batch publisher auto-flush started")

    async def _auto_flush_loop(self):
        """Auto-flush loop"""
        while self._running:
            await asyncio.sleep(self.flush_interval)
            if self.batch:
                await self.flush()

    async def stop(self):
        """Stop batch publisher and flush remaining events"""
        self._running = False

        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        # Final flush
        await self.flush()

        if self.producer:
            self.producer.flush()

        logger.info("Batch publisher stopped")

    @property
    def batch_count(self) -> int:
        """Get current batch size"""
        return len(self.batch)


# Example usage
async def example_batch_publishing():
    """Example of batch event publishing"""
    publisher = BatchEventPublisher(
        bootstrap_servers="localhost:9092",
        batch_size=50,
        flush_interval=5.0,
    )

    await publisher.start_auto_flush()

    try:
        # Add multiple events
        for i in range(100):
            await publisher.add_event(
                event_type=EventType.PATIENT_CREATED,
                tenant_id="hospital-1",
                payload={"patient_id": f"patient-{i}", "name": f"Patient {i}"},
                source_service="test-service",
            )

        # Wait for auto-flush or manually flush
        await publisher.flush()

    finally:
        await publisher.stop()
