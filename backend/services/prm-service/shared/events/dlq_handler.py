"""
Dead Letter Queue (DLQ) handler for failed events
Provides retry mechanism and permanent failure storage
"""
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from loguru import logger

# Optional Kafka support
try:
    from confluent_kafka import Producer
    KAFKA_AVAILABLE = True
except ImportError:
    Producer = None  # type: ignore
    KAFKA_AVAILABLE = False

from .types import Event, EventType


class DLQHandler:
    """
    Dead Letter Queue handler for failed events

    Features:
    - Store failed events in DLQ topic
    - Track retry attempts
    - Provide replay mechanism
    - Store permanent failures in database
    """

    def __init__(self, bootstrap_servers: Optional[str] = None):
        """
        Initialize DLQ handler

        Args:
            bootstrap_servers: Kafka bootstrap servers
        """
        self.bootstrap_servers = bootstrap_servers or os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
        )
        self.dlq_topic_prefix = os.getenv("KAFKA_DLQ_PREFIX", "healthtech.dlq")
        self.max_retries = int(os.getenv("DLQ_MAX_RETRIES", "3"))
        self.producer: Optional[Producer] = None
        self._init_producer()

    def _init_producer(self):
        """Initialize Kafka producer for DLQ"""
        try:
            conf = {
                "bootstrap.servers": self.bootstrap_servers,
                "client.id": "dlq-handler",
                "acks": "all",
                "retries": 1,
            }
            self.producer = Producer(conf)
            logger.info(f"DLQ handler initialized: {self.bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to initialize DLQ producer: {e}")
            self.producer = None

    def send_to_dlq(
        self,
        event: Event,
        error: Exception,
        retry_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Send failed event to Dead Letter Queue

        Args:
            event: Original event that failed
            error: Exception that caused failure
            retry_count: Number of retry attempts
            metadata: Additional metadata about failure
        """
        dlq_event = {
            "original_event": event.model_dump(),
            "error": {
                "type": type(error).__name__,
                "message": str(error),
                "timestamp": datetime.utcnow().isoformat(),
            },
            "retry_count": retry_count,
            "max_retries": self.max_retries,
            "can_retry": retry_count < self.max_retries,
            "metadata": metadata or {},
        }

        # Send to Kafka DLQ topic
        if self.producer:
            try:
                topic = self._get_dlq_topic(event.event_type)
                self.producer.produce(
                    topic=topic,
                    key=str(event.event_id).encode("utf-8"),
                    value=json.dumps(dlq_event).encode("utf-8"),
                )
                self.producer.flush()
                logger.warning(
                    f"Event {event.event_id} sent to DLQ: {topic} "
                    f"(retry {retry_count}/{self.max_retries})"
                )
            except Exception as e:
                logger.error(f"Failed to send event to DLQ: {e}")

        # Store in database if max retries exceeded
        if retry_count >= self.max_retries:
            self._store_failed_event(event, error, retry_count, metadata)

    def _get_dlq_topic(self, event_type: EventType) -> str:
        """
        Get DLQ topic name for event type

        Args:
            event_type: Type of event

        Returns:
            DLQ topic name
        """
        domain = event_type.value.split(".")[0].lower()
        return f"{self.dlq_topic_prefix}.{domain}"

    async def _store_failed_event(
        self,
        event: Event,
        error: Exception,
        retry_count: int,
        metadata: Optional[Dict[str, Any]],
    ):
        """
        Store permanently failed event in database

        Args:
            event: Failed event
            error: Exception that caused failure
            retry_count: Number of retry attempts
            metadata: Additional metadata
        """
        try:
            from shared.database.connection import get_db_session
            from shared.database.models import FailedEvent

            with get_db_session() as db:
                failed_event = FailedEvent(
                    event_id=event.event_id,
                    event_type=event.event_type.value,
                    tenant_id=event.tenant_id,
                    event_payload=event.payload,
                    error_type=type(error).__name__,
                    error_message=str(error),
                    retry_count=retry_count,
                    failed_at=datetime.utcnow(),
                    metadata=metadata or {},
                )
                db.add(failed_event)

            logger.error(
                f"Permanently failed event {event.event_id} stored in database "
                f"after {retry_count} retries"
            )
        except Exception as e:
            logger.error(f"Failed to store failed event in database: {e}")

    def retry_from_dlq(self, event_id: UUID, publisher):
        """
        Retry event from DLQ

        Args:
            event_id: ID of event to retry
            publisher: Event publisher instance
        """
        # Implementation would fetch from DLQ topic or database
        # and republish the event
        pass

    def close(self):
        """Close DLQ handler"""
        if self.producer:
            self.producer.flush()
            logger.info("DLQ handler closed")


# Global DLQ handler instance
_dlq_handler: Optional[DLQHandler] = None


def get_dlq_handler() -> DLQHandler:
    """Get or create global DLQ handler"""
    global _dlq_handler
    if _dlq_handler is None:
        _dlq_handler = DLQHandler()
    return _dlq_handler
