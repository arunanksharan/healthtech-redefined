"""
Service Integration for Event-Driven Architecture

Provides integration helpers for all healthcare services:
- Event publishing decorators
- Consumer registration utilities
- Service-specific event handlers
- Cross-service event correlation
- Transactional outbox pattern

EPIC-002: US-002.8 Service Integration
"""

import asyncio
import functools
import json
import os
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set, Type
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from enum import Enum
import logging
import threading

from .types import Event, EventType
from .publisher import publish_event, EventPublisher
from .consumer import EventConsumer
from .dlq_handler import get_dlq_handler, DLQHandler

logger = logging.getLogger(__name__)


class ServiceType(str, Enum):
    """Healthcare service types."""
    PRM_SERVICE = "prm-service"
    FHIR_SERVICE = "fhir-service"
    AI_SERVICE = "ai-service"
    BILLING_SERVICE = "billing-service"
    TELEHEALTH_SERVICE = "telehealth-service"
    COMMUNICATION_SERVICE = "communication-service"
    ANALYTICS_SERVICE = "analytics-service"
    WORKFLOW_SERVICE = "workflow-service"


@dataclass
class ServiceEventConfig:
    """Configuration for service event integration."""
    service_name: str
    service_type: ServiceType
    published_events: List[EventType] = field(default_factory=list)
    consumed_events: List[EventType] = field(default_factory=list)
    consumer_group_suffix: str = ""

    @property
    def consumer_group_id(self) -> str:
        """Get consumer group ID for this service."""
        suffix = self.consumer_group_suffix or "consumer"
        return f"{self.service_name}-{suffix}-group"


@dataclass
class EventCorrelation:
    """Tracks event correlation across services."""
    correlation_id: str
    causation_id: Optional[str] = None
    root_event_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    parent_span_id: Optional[str] = None


# Thread-local storage for correlation context
_correlation_context = threading.local()


def get_correlation_context() -> Optional[EventCorrelation]:
    """Get current correlation context."""
    return getattr(_correlation_context, "correlation", None)


def set_correlation_context(correlation: EventCorrelation):
    """Set current correlation context."""
    _correlation_context.correlation = correlation


def clear_correlation_context():
    """Clear current correlation context."""
    _correlation_context.correlation = None


def with_correlation(
    correlation_id: Optional[str] = None,
    causation_id: Optional[str] = None,
):
    """
    Decorator to set correlation context for a function.

    Usage:
        @with_correlation()
        async def handle_request():
            await publish_event(...)  # Will include correlation
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            correlation = EventCorrelation(
                correlation_id=correlation_id or str(uuid4()),
                causation_id=causation_id,
                trace_id=str(uuid4()),
                span_id=str(uuid4())[:16],
            )
            set_correlation_context(correlation)
            try:
                return await func(*args, **kwargs)
            finally:
                clear_correlation_context()
        return wrapper
    return decorator


def on_event(*event_types: EventType):
    """
    Decorator to register a function as an event handler.

    Usage:
        @on_event(EventType.PATIENT_CREATED, EventType.PATIENT_UPDATED)
        async def handle_patient_event(event: Event):
            ...
    """
    def decorator(func: Callable):
        func._event_types = event_types
        return func
    return decorator


def publishes(*event_types: EventType):
    """
    Decorator to document events published by a function.

    Usage:
        @publishes(EventType.APPOINTMENT_CREATED)
        async def create_appointment():
            ...
    """
    def decorator(func: Callable):
        func._publishes = event_types
        return func
    return decorator


async def publish_with_correlation(
    event_type: EventType,
    tenant_id: str,
    payload: Dict[str, Any],
    source_service: Optional[str] = None,
    source_user_id: Optional[UUID] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Publish event with automatic correlation context.

    Args:
        event_type: Type of event
        tenant_id: Tenant identifier
        payload: Event payload
        source_service: Source service name
        source_user_id: User who triggered the event
        metadata: Additional metadata

    Returns:
        Event ID
    """
    # Get correlation context
    correlation = get_correlation_context()

    # Build metadata with correlation
    full_metadata = metadata or {}
    if correlation:
        full_metadata.update({
            "correlation_id": correlation.correlation_id,
            "causation_id": correlation.causation_id,
            "trace_id": correlation.trace_id,
            "span_id": correlation.span_id,
        })

    return await publish_event(
        event_type=event_type,
        tenant_id=tenant_id,
        payload=payload,
        source_service=source_service,
        source_user_id=source_user_id,
        metadata=full_metadata,
    )


class ServiceEventIntegration:
    """
    Service-level event integration manager.

    Features:
    - Automatic consumer setup
    - Handler registration
    - Correlation tracking
    - Error handling with DLQ
    - Metrics collection
    """

    def __init__(
        self,
        config: ServiceEventConfig,
        dlq_handler: Optional[DLQHandler] = None,
    ):
        self.config = config
        self.dlq_handler = dlq_handler or get_dlq_handler()

        self._consumer: Optional[EventConsumer] = None
        self._handlers: Dict[EventType, List[Callable]] = {}
        self._running = False

        # Metrics
        self._events_processed = 0
        self._events_failed = 0
        self._events_published = 0

    def register_handler(
        self,
        event_type: EventType,
        handler: Callable,
    ):
        """Register an event handler."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.info(
            f"[{self.config.service_name}] Registered handler for {event_type.value}"
        )

    def register_handlers_from_module(self, module):
        """
        Register all handlers decorated with @on_event from a module.

        Args:
            module: Module containing handler functions
        """
        for name in dir(module):
            obj = getattr(module, name)
            if callable(obj) and hasattr(obj, "_event_types"):
                for event_type in obj._event_types:
                    self.register_handler(event_type, obj)

    async def start(self):
        """Start consuming events."""
        if self._running:
            return

        # Determine topics to subscribe to
        topics = self._get_topics_for_events(self.config.consumed_events)

        if not topics:
            logger.warning(
                f"[{self.config.service_name}] No events configured for consumption"
            )
            return

        # Create consumer
        self._consumer = EventConsumer(
            group_id=self.config.consumer_group_id,
            topics=topics,
        )

        # Register internal handler
        for event_type in self.config.consumed_events:
            self._consumer.register_handler(event_type, self._handle_event)

        self._running = True
        logger.info(
            f"[{self.config.service_name}] Starting event consumer for topics: {topics}"
        )

        # Start consumer
        await self._consumer.start()

    def stop(self):
        """Stop consuming events."""
        self._running = False
        if self._consumer:
            self._consumer.stop()
        logger.info(f"[{self.config.service_name}] Event consumer stopped")

    async def _handle_event(self, event: Event):
        """Internal event handler with error handling."""
        # Set correlation context
        correlation = EventCorrelation(
            correlation_id=event.metadata.get("correlation_id", str(uuid4())),
            causation_id=str(event.event_id),
            trace_id=event.metadata.get("trace_id"),
            span_id=str(uuid4())[:16],
            parent_span_id=event.metadata.get("span_id"),
        )
        set_correlation_context(correlation)

        try:
            handlers = self._handlers.get(event.event_type, [])

            for handler in handlers:
                try:
                    await handler(event)
                    self._events_processed += 1
                except Exception as e:
                    logger.error(
                        f"[{self.config.service_name}] Handler error for "
                        f"{event.event_type.value}: {e}"
                    )
                    self._events_failed += 1

                    # Send to DLQ
                    if self.dlq_handler:
                        self.dlq_handler.send_to_dlq(
                            event=event,
                            error=e,
                            retry_count=0,
                            metadata={
                                "service": self.config.service_name,
                                "handler": handler.__name__,
                            },
                        )

        finally:
            clear_correlation_context()

    def _get_topics_for_events(self, event_types: List[EventType]) -> List[str]:
        """Get Kafka topics for event types."""
        topics = set()
        for event_type in event_types:
            domain = event_type.value.split(".")[0].lower()
            topics.add(f"healthtech.{domain}.events")
        return list(topics)

    async def publish(
        self,
        event_type: EventType,
        tenant_id: str,
        payload: Dict[str, Any],
        source_user_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Publish an event from this service."""
        event_id = await publish_with_correlation(
            event_type=event_type,
            tenant_id=tenant_id,
            payload=payload,
            source_service=self.config.service_name,
            source_user_id=source_user_id,
            metadata=metadata,
        )
        self._events_published += 1
        return event_id

    def get_metrics(self) -> Dict[str, Any]:
        """Get integration metrics."""
        return {
            "service": self.config.service_name,
            "events_processed": self._events_processed,
            "events_failed": self._events_failed,
            "events_published": self._events_published,
            "handlers_registered": sum(len(h) for h in self._handlers.values()),
            "running": self._running,
        }


# Pre-configured service integrations
PRM_SERVICE_CONFIG = ServiceEventConfig(
    service_name="prm-service",
    service_type=ServiceType.PRM_SERVICE,
    published_events=[
        EventType.PATIENT_CREATED,
        EventType.PATIENT_UPDATED,
        EventType.PATIENT_MERGED,
        EventType.APPOINTMENT_CREATED,
        EventType.APPOINTMENT_UPDATED,
        EventType.APPOINTMENT_CANCELLED,
        EventType.JOURNEY_CREATED,
        EventType.JOURNEY_INSTANCE_CREATED,
        EventType.JOURNEY_STAGE_ENTERED,
        EventType.JOURNEY_STAGE_COMPLETED,
        EventType.COMMUNICATION_SENT,
    ],
    consumed_events=[
        EventType.FHIR_RESOURCE_CREATED,
        EventType.FHIR_RESOURCE_UPDATED,
        EventType.LAB_RESULT_CREATED,
        EventType.LAB_RESULT_FINALIZED,
        EventType.APPOINTMENT_CHECKED_IN,
        EventType.APPOINTMENT_COMPLETED,
    ],
)

FHIR_SERVICE_CONFIG = ServiceEventConfig(
    service_name="fhir-service",
    service_type=ServiceType.FHIR_SERVICE,
    published_events=[
        EventType.FHIR_RESOURCE_CREATED,
        EventType.FHIR_RESOURCE_UPDATED,
        EventType.FHIR_RESOURCE_DELETED,
        EventType.FHIR_MESSAGE_RECEIVED,
        EventType.FHIR_MESSAGE_SENT,
    ],
    consumed_events=[
        EventType.PATIENT_CREATED,
        EventType.PATIENT_UPDATED,
        EventType.ENCOUNTER_CREATED,
        EventType.ENCOUNTER_UPDATED,
        EventType.VITALS_RECORDED,
    ],
)

AI_SERVICE_CONFIG = ServiceEventConfig(
    service_name="ai-service",
    service_type=ServiceType.AI_SERVICE,
    published_events=[
        EventType.LLM_SESSION_STARTED,
        EventType.LLM_SESSION_ENDED,
        EventType.LLM_TOOL_CALLED,
        EventType.RISK_SCORE_CREATED,
    ],
    consumed_events=[
        EventType.PATIENT_CREATED,
        EventType.VITALS_RECORDED,
        EventType.LAB_RESULT_FINALIZED,
        EventType.ENCOUNTER_COMPLETED,
    ],
)

BILLING_SERVICE_CONFIG = ServiceEventConfig(
    service_name="billing-service",
    service_type=ServiceType.BILLING_SERVICE,
    published_events=[
        EventType.CHARGE_CREATED,
        EventType.CHARGE_POSTED,
        EventType.CLAIM_CREATED,
        EventType.CLAIM_SUBMITTED,
        EventType.PAYMENT_RECEIVED,
        EventType.INVOICE_GENERATED,
    ],
    consumed_events=[
        EventType.ENCOUNTER_COMPLETED,
        EventType.ORDER_COMPLETED,
        EventType.MEDICATION_DISPENSED,
        EventType.LAB_ORDER_COMPLETED,
        EventType.IMAGING_ORDER_COMPLETED,
    ],
)

TELEHEALTH_SERVICE_CONFIG = ServiceEventConfig(
    service_name="telehealth-service",
    service_type=ServiceType.TELEHEALTH_SERVICE,
    published_events=[
        EventType.VOICE_SESSION_STARTED,
        EventType.VOICE_SESSION_ENDED,
    ],
    consumed_events=[
        EventType.APPOINTMENT_CREATED,
        EventType.APPOINTMENT_CANCELLED,
    ],
)


class TransactionalOutbox:
    """
    Transactional outbox pattern for guaranteed event delivery.

    Events are first written to a database table in the same transaction
    as the business operation, then published to Kafka asynchronously.
    """

    def __init__(self, db_session_factory: Callable):
        self.db_session_factory = db_session_factory
        self._running = False
        self._poll_task: Optional[asyncio.Task] = None
        self._poll_interval = 1.0  # seconds

    async def save_event(
        self,
        event_type: EventType,
        tenant_id: str,
        payload: Dict[str, Any],
        aggregate_type: str,
        aggregate_id: str,
        db_session,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Save event to outbox table within existing transaction.

        Args:
            event_type: Type of event
            tenant_id: Tenant identifier
            payload: Event payload
            aggregate_type: Type of aggregate
            aggregate_id: ID of aggregate
            db_session: Active database session
            metadata: Additional metadata

        Returns:
            Event ID
        """
        from shared.database.models import OutboxEvent

        event_id = str(uuid4())
        correlation = get_correlation_context()

        outbox_event = OutboxEvent(
            event_id=event_id,
            event_type=event_type.value,
            tenant_id=tenant_id,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=payload,
            metadata={
                **(metadata or {}),
                "correlation_id": correlation.correlation_id if correlation else None,
                "causation_id": correlation.causation_id if correlation else None,
            },
            created_at=datetime.now(timezone.utc),
            published=False,
        )

        db_session.add(outbox_event)
        # Don't commit - let the caller's transaction commit

        return event_id

    async def start_publisher(self):
        """Start the outbox publisher background task."""
        if self._running:
            return

        self._running = True
        self._poll_task = asyncio.create_task(self._poll_outbox())
        logger.info("Transactional outbox publisher started")

    async def stop_publisher(self):
        """Stop the outbox publisher."""
        self._running = False
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        logger.info("Transactional outbox publisher stopped")

    async def _poll_outbox(self):
        """Poll outbox table and publish events."""
        while self._running:
            try:
                await self._publish_pending_events()
            except Exception as e:
                logger.error(f"Outbox polling error: {e}")

            await asyncio.sleep(self._poll_interval)

    async def _publish_pending_events(self):
        """Publish pending events from outbox."""
        from shared.database.models import OutboxEvent

        with self.db_session_factory() as db:
            # Get unpublished events
            pending_events = (
                db.query(OutboxEvent)
                .filter(OutboxEvent.published == False)
                .order_by(OutboxEvent.created_at)
                .limit(100)
                .all()
            )

            for outbox_event in pending_events:
                try:
                    # Publish to Kafka
                    await publish_event(
                        event_type=EventType(outbox_event.event_type),
                        tenant_id=outbox_event.tenant_id,
                        payload=outbox_event.payload,
                        metadata=outbox_event.metadata,
                    )

                    # Mark as published
                    outbox_event.published = True
                    outbox_event.published_at = datetime.now(timezone.utc)

                except Exception as e:
                    logger.error(
                        f"Failed to publish outbox event {outbox_event.event_id}: {e}"
                    )
                    outbox_event.error = str(e)
                    outbox_event.retry_count = (outbox_event.retry_count or 0) + 1

            db.commit()


def create_service_integration(
    service_type: ServiceType,
) -> ServiceEventIntegration:
    """
    Create a service integration for a specific service type.

    Args:
        service_type: Type of service

    Returns:
        Configured ServiceEventIntegration
    """
    configs = {
        ServiceType.PRM_SERVICE: PRM_SERVICE_CONFIG,
        ServiceType.FHIR_SERVICE: FHIR_SERVICE_CONFIG,
        ServiceType.AI_SERVICE: AI_SERVICE_CONFIG,
        ServiceType.BILLING_SERVICE: BILLING_SERVICE_CONFIG,
        ServiceType.TELEHEALTH_SERVICE: TELEHEALTH_SERVICE_CONFIG,
    }

    config = configs.get(service_type)
    if not config:
        raise ValueError(f"Unknown service type: {service_type}")

    return ServiceEventIntegration(config)


# Global service integrations
_service_integrations: Dict[ServiceType, ServiceEventIntegration] = {}


def get_service_integration(
    service_type: ServiceType,
) -> ServiceEventIntegration:
    """Get or create service integration."""
    if service_type not in _service_integrations:
        _service_integrations[service_type] = create_service_integration(service_type)
    return _service_integrations[service_type]
