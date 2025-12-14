"""
Event consumer using Kafka
Subscribe to events and process them
"""
import json
import os
from typing import Callable, Dict, List, Optional
from loguru import logger

# Optional Kafka support
try:
    from confluent_kafka import Consumer, KafkaError, KafkaException
    KAFKA_AVAILABLE = True
except ImportError:
    Consumer = None  # type: ignore
    KafkaError = None  # type: ignore
    KafkaException = Exception  # type: ignore
    KAFKA_AVAILABLE = False

from .types import Event, EventType


class EventConsumer:
    """
    Event consumer for subscribing to Kafka topics

    Features:
    - Subscribe to multiple topics
    - Process events with handlers
    - Auto-commit with error handling
    - Graceful shutdown
    """

    def __init__(
        self,
        group_id: str,
        topics: List[str],
        auto_offset_reset: str = "earliest"
    ):
        """
        Initialize event consumer

        Args:
            group_id: Consumer group ID
            topics: List of topics to subscribe to
            auto_offset_reset: Where to start reading ('earliest' or 'latest')
        """
        self.group_id = group_id
        self.topics = topics
        self.consumer: Optional[Consumer] = None
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.enabled = os.getenv("KAFKA_ENABLED", "true").lower() == "true"
        self.handlers: Dict[EventType, List[Callable]] = {}
        self._running = False

        if self.enabled:
            self._init_consumer(auto_offset_reset)

    def _init_consumer(self, auto_offset_reset: str):
        """Initialize Kafka consumer"""
        try:
            conf = {
                "bootstrap.servers": self.bootstrap_servers,
                "group.id": self.group_id,
                "auto.offset.reset": auto_offset_reset,
                "enable.auto.commit": True,
                "auto.commit.interval.ms": 5000,
                "session.timeout.ms": 45000,
            }
            self.consumer = Consumer(conf)
            self.consumer.subscribe(self.topics)
            logger.info(
                f"Kafka consumer initialized: group={self.group_id}, topics={self.topics}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Kafka consumer: {e}")
            self.consumer = None

    def register_handler(self, event_type: EventType, handler: Callable):
        """
        Register a handler function for an event type

        Args:
            event_type: Type of event to handle
            handler: Async function to call when event is received
                    Signature: async def handler(event: Event) -> None
        """
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
        logger.info(f"Registered handler for {event_type.value}")

    async def process_event(self, event: Event):
        """
        Process a received event by calling registered handlers

        Args:
            event: Event to process
        """
        event_type = event.event_type

        if event_type in self.handlers:
            for handler in self.handlers[event_type]:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(
                        f"Error processing event {event.event_id} with handler: {e}"
                    )
        else:
            logger.debug(f"No handlers registered for {event_type.value}")

    async def start(self):
        """Start consuming events"""
        if not self.consumer:
            logger.warning("Consumer not initialized, cannot start")
            return

        self._running = True
        logger.info("Starting event consumer...")

        try:
            while self._running:
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.debug(
                            f"Reached end of partition {msg.topic()} [{msg.partition()}]"
                        )
                    else:
                        logger.error(f"Consumer error: {msg.error()}")
                    continue

                try:
                    # Decode message
                    event_data = json.loads(msg.value().decode("utf-8"))
                    event = Event(**event_data)

                    logger.debug(
                        f"Received event: {event.event_type.value} (ID: {event.event_id})"
                    )

                    # Process event
                    await self.process_event(event)

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode event: {e}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

        except KafkaException as e:
            logger.error(f"Kafka exception: {e}")
        finally:
            self.stop()

    def stop(self):
        """Stop consuming events and close consumer"""
        self._running = False
        if self.consumer:
            self.consumer.close()
            logger.info("Event consumer stopped")


# Example usage and helper functions
def create_consumer_for_service(
    service_name: str,
    topics: Optional[List[str]] = None
) -> EventConsumer:
    """
    Create a consumer for a specific service

    Args:
        service_name: Name of the service (e.g., 'prm-service')
        topics: List of topics to subscribe to. If None, subscribes to all.

    Returns:
        EventConsumer instance
    """
    if topics is None:
        # Subscribe to all healthtech topics
        topics = ["healthtech.*.events"]

    group_id = f"{service_name}-consumer-group"
    return EventConsumer(group_id=group_id, topics=topics)


# Example handler function
async def example_event_handler(event: Event):
    """
    Example event handler

    Args:
        event: Event to handle
    """
    logger.info(f"Handling event: {event.event_type.value}")
    logger.debug(f"Event payload: {event.payload}")

    # Process event based on type
    if event.event_type == EventType.PATIENT_CREATED:
        patient_id = event.payload.get("patient_id")
        logger.info(f"New patient created: {patient_id}")
        # Perform any necessary actions
        # e.g., create journey instance, send welcome message, etc.

    elif event.event_type == EventType.APPOINTMENT_CREATED:
        appointment_id = event.payload.get("appointment_id")
        logger.info(f"New appointment created: {appointment_id}")
        # e.g., send confirmation, create reminders, etc.
