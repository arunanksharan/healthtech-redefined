"""
Event publisher using Kafka with database fallback
"""
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from confluent_kafka import Producer
from loguru import logger

from .types import Event, EventType


class EventPublisher:
    """
    Event publisher with Kafka integration

    Features:
    - Asynchronous event publishing to Kafka
    - Automatic fallback to database if Kafka unavailable
    - Topic routing based on event type
    - Delivery confirmation
    """

    def __init__(self):
        self.producer: Optional[Producer] = None
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.topic_prefix = os.getenv("KAFKA_TOPIC_PREFIX", "healthtech")
        self.enabled = os.getenv("KAFKA_ENABLED", "true").lower() == "true"
        self._init_producer()

    def _init_producer(self):
        """Initialize Kafka producer"""
        if not self.enabled:
            logger.info("Kafka publishing disabled, using database fallback only")
            return

        try:
            conf = {
                "bootstrap.servers": self.bootstrap_servers,
                "client.id": "healthtech-producer",
                "acks": "all",  # Wait for all replicas
                "retries": 3,
                "max.in.flight.requests.per.connection": 1,
                "compression.type": "gzip",
                "linger.ms": 10,  # Batch messages for efficiency
                "batch.size": 16384,
            }
            self.producer = Producer(conf)
            logger.info(f"Kafka producer initialized: {self.bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            logger.warning("Events will be logged to database only")
            self.producer = None

    def _get_topic(self, event_type: EventType) -> str:
        """
        Determine Kafka topic for event type

        Topic structure: {prefix}.{domain}.events
        Examples:
            - Patient.Created -> healthtech.patient.events
            - Appointment.Created -> healthtech.appointment.events
            - Order.Created -> healthtech.order.events
        """
        domain = event_type.value.split(".")[0].lower()
        return f"{self.topic_prefix}.{domain}.events"

    def _delivery_report(self, err, msg):
        """Callback for Kafka delivery reports"""
        if err is not None:
            logger.error(f"Event delivery failed: {err}")
        else:
            logger.debug(
                f"Event delivered to {msg.topic()} [{msg.partition()}] @ offset {msg.offset()}"
            )

    async def publish(
        self,
        event_type: EventType,
        tenant_id: str,
        payload: Dict[str, Any],
        source_service: Optional[str] = None,
        source_user_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Publish an event to Kafka and database

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
        # Create event
        event = Event(
            event_type=event_type,
            tenant_id=tenant_id,
            payload=payload,
            source_service=source_service,
            source_user_id=source_user_id,
            metadata=metadata or {},
        )

        # Serialize event
        event_json = event.model_dump_json()
        event_id = str(event.event_id)

        # Publish to Kafka if available
        if self.producer:
            try:
                topic = self._get_topic(event_type)
                self.producer.produce(
                    topic=topic,
                    key=tenant_id.encode("utf-8"),
                    value=event_json.encode("utf-8"),
                    callback=self._delivery_report,
                )
                self.producer.poll(0)  # Trigger delivery reports
                logger.debug(f"Event {event_id} published to Kafka: {event_type.value}")
            except Exception as e:
                logger.error(f"Failed to publish event to Kafka: {e}")
                # Continue to database fallback

        # Always log to database as well
        await self._log_event_to_db(event)

        return event_id

    async def _log_event_to_db(self, event: Event):
        """
        Log event to database as fallback/permanent record

        Args:
            event: Event to log
        """
        try:
            from shared.database.connection import get_db_session
            from shared.database.models import EventLog

            with get_db_session() as db:
                db_event = EventLog(
                    tenant_id=event.tenant_id,
                    event_type=event.event_type.value,
                    event_payload=event.payload,
                    occurred_at=event.occurred_at,
                    published_at=datetime.utcnow(),
                    source_service=event.source_service,
                    source_user_id=event.source_user_id,
                    meta_data=event.metadata,
                )
                db.add(db_event)
                # Session will commit via context manager

            logger.debug(f"Event {event.event_id} logged to database")
        except Exception as e:
            logger.error(f"Failed to log event to database: {e}")

    def flush(self):
        """Flush any pending events"""
        if self.producer:
            self.producer.flush()

    def close(self):
        """Close the producer"""
        if self.producer:
            self.producer.flush()
            logger.info("Kafka producer closed")


# Global publisher instance
_publisher: Optional[EventPublisher] = None


def get_publisher() -> EventPublisher:
    """Get or create global event publisher"""
    global _publisher
    if _publisher is None:
        _publisher = EventPublisher()
    return _publisher


async def publish_event(
    event_type: EventType,
    tenant_id: str,
    payload: Dict[str, Any],
    source_service: Optional[str] = None,
    source_user_id: Optional[UUID] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Convenience function to publish an event

    Args:
        event_type: Type of event
        tenant_id: Tenant identifier
        payload: Event payload data
        source_service: Service that generated the event
        source_user_id: User who triggered the event
        metadata: Additional metadata

    Returns:
        str: Event ID

    Example:
        await publish_event(
            event_type=EventType.PATIENT_CREATED,
            tenant_id=str(tenant_id),
            payload={
                "patient_id": str(patient.id),
                "name": f"{patient.first_name} {patient.last_name}",
            },
            source_service="identity-service",
        )
    """
    publisher = get_publisher()
    return await publisher.publish(
        event_type=event_type,
        tenant_id=tenant_id,
        payload=payload,
        source_service=source_service,
        source_user_id=source_user_id,
        metadata=metadata,
    )
