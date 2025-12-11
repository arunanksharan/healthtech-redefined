"""
Event Bus for Real-Time Broadcasting

Advanced event broadcasting system with:
- Topic-based pub/sub with wildcard patterns
- Event persistence for replay/recovery
- Redis pub/sub adapter for horizontal scaling
- Event history and replay capability
- Cross-server event distribution
- Dead letter queue for failed deliveries

EPIC-001: US-001.7 Real-Time Event Broadcasting
"""

import asyncio
import json
import fnmatch
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set, Any, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import logging

import redis.asyncio as redis
from redis.asyncio.client import PubSub

logger = logging.getLogger(__name__)


class EventPriority(str, Enum):
    """Event priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class EventCategory(str, Enum):
    """Event categories for healthcare system."""
    # System events
    SYSTEM = "system"

    # Patient events
    PATIENT = "patient"
    PATIENT_CREATED = "patient.created"
    PATIENT_UPDATED = "patient.updated"

    # Appointment events
    APPOINTMENT = "appointment"
    APPOINTMENT_CREATED = "appointment.created"
    APPOINTMENT_UPDATED = "appointment.updated"
    APPOINTMENT_CANCELLED = "appointment.cancelled"
    APPOINTMENT_REMINDER = "appointment.reminder"

    # Clinical events
    CLINICAL = "clinical"
    ENCOUNTER_STARTED = "clinical.encounter.started"
    ENCOUNTER_ENDED = "clinical.encounter.ended"
    VITALS_RECORDED = "clinical.vitals.recorded"
    LAB_RESULT_AVAILABLE = "clinical.lab.result"
    PRESCRIPTION_CREATED = "clinical.prescription.created"

    # Communication events
    COMMUNICATION = "communication"
    MESSAGE_RECEIVED = "communication.message.received"

    # Telehealth events
    TELEHEALTH = "telehealth"
    VIDEO_CALL_STARTED = "telehealth.video.started"
    VIDEO_CALL_ENDED = "telehealth.video.ended"
    WAITING_ROOM_UPDATE = "telehealth.waiting_room.update"

    # Billing events
    BILLING = "billing"
    CLAIM_SUBMITTED = "billing.claim.submitted"
    PAYMENT_RECEIVED = "billing.payment.received"


@dataclass
class Event:
    """Event structure for broadcasting."""
    event_id: str
    topic: str
    category: str
    tenant_id: str
    payload: Dict[str, Any]
    priority: EventPriority = EventPriority.NORMAL
    source: str = ""  # Source service/component
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None  # ID of event that caused this one
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "eventId": self.event_id,
            "topic": self.topic,
            "category": self.category,
            "tenantId": self.tenant_id,
            "payload": self.payload,
            "priority": self.priority.value,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "correlationId": self.correlation_id,
            "causationId": self.causation_id,
            "metadata": self.metadata,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        return cls(
            event_id=data["eventId"],
            topic=data["topic"],
            category=data["category"],
            tenant_id=data["tenantId"],
            payload=data["payload"],
            priority=EventPriority(data.get("priority", "normal")),
            source=data.get("source", ""),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(timezone.utc),
            correlation_id=data.get("correlationId"),
            causation_id=data.get("causationId"),
            metadata=data.get("metadata", {}),
            version=data.get("version", 1),
        )


@dataclass
class Subscription:
    """Event subscription."""
    subscription_id: str
    pattern: str  # Topic pattern (supports wildcards)
    tenant_id: Optional[str]  # None = all tenants
    handler: Callable[[Event], Awaitable[None]]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    filters: Dict[str, Any] = field(default_factory=dict)  # Additional filters
    priority_threshold: Optional[EventPriority] = None
    active: bool = True


@dataclass
class EventHistoryQuery:
    """Query parameters for event history."""
    tenant_id: str
    topics: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    correlation_id: Optional[str] = None
    limit: int = 100
    offset: int = 0


class EventBus:
    """
    Event bus for real-time event broadcasting.

    Features:
    - Topic-based pub/sub with wildcard pattern matching
    - Redis pub/sub for horizontal scaling
    - Event persistence for history/replay
    - Dead letter queue for failed events
    - Cross-server event distribution
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        server_id: Optional[str] = None,
        event_ttl: int = 86400 * 7,  # 7 days
        max_history_per_tenant: int = 10000,
        enable_persistence: bool = True,
    ):
        self.redis_url = redis_url
        self.server_id = server_id or str(uuid4())[:8]
        self.event_ttl = event_ttl
        self.max_history_per_tenant = max_history_per_tenant
        self.enable_persistence = enable_persistence

        self._redis: Optional[redis.Redis] = None
        self._pubsub: Optional[PubSub] = None
        self._subscriptions: Dict[str, Subscription] = {}
        self._topic_subscriptions: Dict[str, Set[str]] = {}  # topic -> subscription_ids
        self._running = False
        self._listener_task: Optional[asyncio.Task] = None

        # Dead letter queue
        self._dlq: List[Dict[str, Any]] = []
        self._max_dlq_size = 1000

        # Metrics
        self._metrics = {
            "events_published": 0,
            "events_received": 0,
            "events_delivered": 0,
            "delivery_errors": 0,
            "dlq_size": 0,
        }

    async def start(self):
        """Start the event bus."""
        if self._running:
            return

        try:
            self._redis = redis.from_url(self.redis_url, decode_responses=True)
            await self._redis.ping()

            # Setup pub/sub
            self._pubsub = self._redis.pubsub()
            await self._pubsub.psubscribe("event:*")

            self._running = True
            self._listener_task = asyncio.create_task(self._listen_for_events())

            logger.info(f"EventBus started (server: {self.server_id})")

        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}. Event bus running in local mode.")
            self._redis = None
            self._running = True

    async def stop(self):
        """Stop the event bus."""
        self._running = False

        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass

        if self._pubsub:
            await self._pubsub.unsubscribe()
            await self._pubsub.close()

        if self._redis:
            await self._redis.close()

        logger.info("EventBus stopped")

    def _event_channel(self, topic: str) -> str:
        """Get Redis channel for a topic."""
        return f"event:{topic}"

    def _history_key(self, tenant_id: str) -> str:
        """Get Redis key for event history."""
        return f"event_history:{tenant_id}"

    def _event_key(self, event_id: str) -> str:
        """Get Redis key for event data."""
        return f"event:{event_id}"

    def _dlq_key(self) -> str:
        """Get Redis key for dead letter queue."""
        return "event_dlq"

    async def publish(
        self,
        topic: str,
        tenant_id: str,
        payload: Dict[str, Any],
        category: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL,
        source: Optional[str] = None,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Event:
        """
        Publish an event to a topic.

        Args:
            topic: Event topic (e.g., "patient.created", "appointment.*")
            tenant_id: Tenant ID for scoping
            payload: Event payload data
            category: Event category
            priority: Event priority
            source: Source service/component
            correlation_id: Correlation ID for tracing
            causation_id: ID of event that caused this
            metadata: Additional metadata

        Returns:
            Published Event
        """
        event = Event(
            event_id=str(uuid4()),
            topic=topic,
            category=category or topic.split(".")[0] if "." in topic else topic,
            tenant_id=tenant_id,
            payload=payload,
            priority=priority,
            source=source or f"server:{self.server_id}",
            correlation_id=correlation_id,
            causation_id=causation_id,
            metadata=metadata or {},
        )

        # Add server ID to metadata
        event.metadata["serverId"] = self.server_id

        event_data = json.dumps(event.to_dict())

        if self._redis:
            try:
                # Publish to Redis pub/sub
                await self._redis.publish(self._event_channel(topic), event_data)

                # Persist event if enabled
                if self.enable_persistence:
                    # Store event data
                    await self._redis.setex(
                        self._event_key(event.event_id),
                        self.event_ttl,
                        event_data,
                    )

                    # Add to tenant history
                    await self._redis.zadd(
                        self._history_key(tenant_id),
                        {event.event_id: event.timestamp.timestamp()},
                    )

                    # Trim history
                    await self._redis.zremrangebyrank(
                        self._history_key(tenant_id),
                        0,
                        -self.max_history_per_tenant - 1,
                    )

            except Exception as e:
                logger.error(f"Error publishing event to Redis: {e}")
                # Fall back to local delivery
                await self._deliver_locally(event)
        else:
            # Local delivery only
            await self._deliver_locally(event)

        self._metrics["events_published"] += 1
        logger.debug(f"Event published: {event.event_id} ({topic})")

        return event

    async def _deliver_locally(self, event: Event):
        """Deliver event to local subscribers."""
        for sub in self._subscriptions.values():
            if not sub.active:
                continue

            # Check tenant
            if sub.tenant_id and sub.tenant_id != event.tenant_id:
                continue

            # Check pattern match
            if not self._matches_pattern(event.topic, sub.pattern):
                continue

            # Check priority threshold
            if sub.priority_threshold:
                priority_order = {
                    EventPriority.LOW: 1,
                    EventPriority.NORMAL: 2,
                    EventPriority.HIGH: 3,
                    EventPriority.CRITICAL: 4,
                }
                if priority_order.get(event.priority, 0) < priority_order.get(sub.priority_threshold, 0):
                    continue

            # Check additional filters
            if sub.filters:
                if not self._matches_filters(event, sub.filters):
                    continue

            # Deliver to handler
            try:
                await sub.handler(event)
                self._metrics["events_delivered"] += 1
            except Exception as e:
                logger.error(f"Error delivering event to subscription {sub.subscription_id}: {e}")
                self._metrics["delivery_errors"] += 1
                await self._add_to_dlq(event, sub.subscription_id, str(e))

    def _matches_pattern(self, topic: str, pattern: str) -> bool:
        """Check if topic matches subscription pattern."""
        # Support wildcards: * matches one level, # matches multiple levels
        if pattern == "*" or pattern == "#":
            return True

        # Convert to fnmatch pattern
        fnmatch_pattern = pattern.replace("#", "**").replace(".", "/")
        fnmatch_topic = topic.replace(".", "/")

        # Simple pattern matching
        pattern_parts = pattern.split(".")
        topic_parts = topic.split(".")

        if len(pattern_parts) > len(topic_parts) and "#" not in pattern:
            return False

        for i, part in enumerate(pattern_parts):
            if part == "#":
                return True
            if part == "*":
                if i >= len(topic_parts):
                    return False
                continue
            if i >= len(topic_parts) or part != topic_parts[i]:
                return False

        return len(pattern_parts) == len(topic_parts) or pattern_parts[-1] == "#"

    def _matches_filters(self, event: Event, filters: Dict[str, Any]) -> bool:
        """Check if event matches additional filters."""
        for key, value in filters.items():
            if key == "category" and event.category != value:
                return False
            if key == "source" and event.source != value:
                return False
            # Check in payload
            if key.startswith("payload."):
                payload_key = key[8:]
                if event.payload.get(payload_key) != value:
                    return False
        return True

    async def _add_to_dlq(self, event: Event, subscription_id: str, error: str):
        """Add failed event to dead letter queue."""
        dlq_entry = {
            "event": event.to_dict(),
            "subscriptionId": subscription_id,
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "retryCount": 0,
        }

        if self._redis:
            try:
                await self._redis.lpush(self._dlq_key(), json.dumps(dlq_entry))
                await self._redis.ltrim(self._dlq_key(), 0, self._max_dlq_size - 1)
            except Exception as e:
                logger.error(f"Error adding to DLQ: {e}")

        self._dlq.append(dlq_entry)
        self._dlq = self._dlq[-self._max_dlq_size:]
        self._metrics["dlq_size"] = len(self._dlq)

    async def subscribe(
        self,
        pattern: str,
        handler: Callable[[Event], Awaitable[None]],
        tenant_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        priority_threshold: Optional[EventPriority] = None,
    ) -> str:
        """
        Subscribe to events matching a pattern.

        Args:
            pattern: Topic pattern (supports * and # wildcards)
            handler: Async handler function
            tenant_id: Optional tenant filter
            filters: Additional filters
            priority_threshold: Minimum priority to receive

        Returns:
            Subscription ID
        """
        subscription = Subscription(
            subscription_id=str(uuid4()),
            pattern=pattern,
            tenant_id=tenant_id,
            handler=handler,
            filters=filters or {},
            priority_threshold=priority_threshold,
        )

        self._subscriptions[subscription.subscription_id] = subscription

        # Index by pattern
        if pattern not in self._topic_subscriptions:
            self._topic_subscriptions[pattern] = set()
        self._topic_subscriptions[pattern].add(subscription.subscription_id)

        logger.info(f"Subscription created: {subscription.subscription_id} ({pattern})")
        return subscription.subscription_id

    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from events.

        Args:
            subscription_id: Subscription to cancel

        Returns:
            True if unsubscribed
        """
        subscription = self._subscriptions.pop(subscription_id, None)
        if not subscription:
            return False

        # Remove from index
        if subscription.pattern in self._topic_subscriptions:
            self._topic_subscriptions[subscription.pattern].discard(subscription_id)

        logger.info(f"Subscription cancelled: {subscription_id}")
        return True

    async def _listen_for_events(self):
        """Background task to listen for Redis pub/sub events."""
        while self._running and self._pubsub:
            try:
                message = await self._pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message["type"] == "pmessage":
                    await self._handle_pubsub_message(message)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in event listener: {e}")
                await asyncio.sleep(1)

    async def _handle_pubsub_message(self, message: Dict[str, Any]):
        """Handle incoming pub/sub message."""
        try:
            event_data = json.loads(message["data"])
            event = Event.from_dict(event_data)

            # Skip events from this server
            if event.metadata.get("serverId") == self.server_id:
                return

            self._metrics["events_received"] += 1

            # Deliver to local subscribers
            await self._deliver_locally(event)

        except Exception as e:
            logger.error(f"Error handling pub/sub message: {e}")

    async def get_event(self, event_id: str) -> Optional[Event]:
        """Get a specific event by ID."""
        if self._redis:
            try:
                data = await self._redis.get(self._event_key(event_id))
                if data:
                    return Event.from_dict(json.loads(data))
            except Exception as e:
                logger.error(f"Error getting event: {e}")
        return None

    async def get_history(self, query: EventHistoryQuery) -> List[Event]:
        """
        Get event history based on query.

        Args:
            query: Query parameters

        Returns:
            List of events
        """
        events = []

        if not self._redis:
            return events

        try:
            # Get event IDs from sorted set
            start_score = query.start_time.timestamp() if query.start_time else "-inf"
            end_score = query.end_time.timestamp() if query.end_time else "+inf"

            event_ids = await self._redis.zrangebyscore(
                self._history_key(query.tenant_id),
                start_score,
                end_score,
                start=query.offset,
                num=query.limit,
            )

            # Fetch event data
            for event_id in event_ids:
                event = await self.get_event(event_id)
                if event:
                    # Apply filters
                    if query.topics and event.topic not in query.topics:
                        continue
                    if query.categories and event.category not in query.categories:
                        continue
                    if query.correlation_id and event.correlation_id != query.correlation_id:
                        continue
                    events.append(event)

        except Exception as e:
            logger.error(f"Error getting event history: {e}")

        return events

    async def replay_events(
        self,
        tenant_id: str,
        handler: Callable[[Event], Awaitable[None]],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        topics: Optional[List[str]] = None,
    ) -> int:
        """
        Replay historical events to a handler.

        Args:
            tenant_id: Tenant ID
            handler: Handler to receive replayed events
            start_time: Start of replay window
            end_time: End of replay window
            topics: Topics to replay

        Returns:
            Number of events replayed
        """
        query = EventHistoryQuery(
            tenant_id=tenant_id,
            start_time=start_time,
            end_time=end_time,
            topics=topics,
            limit=10000,
        )

        events = await self.get_history(query)
        replayed = 0

        for event in sorted(events, key=lambda e: e.timestamp):
            try:
                await handler(event)
                replayed += 1
            except Exception as e:
                logger.error(f"Error replaying event {event.event_id}: {e}")

        logger.info(f"Replayed {replayed} events for tenant {tenant_id}")
        return replayed

    async def get_dlq_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get events from dead letter queue."""
        if self._redis:
            try:
                data_list = await self._redis.lrange(self._dlq_key(), 0, limit - 1)
                return [json.loads(d) for d in data_list]
            except Exception as e:
                logger.error(f"Error getting DLQ: {e}")

        return self._dlq[:limit]

    async def retry_dlq_event(self, index: int) -> bool:
        """Retry a dead letter queue event."""
        dlq_events = await self.get_dlq_events(index + 1)
        if index >= len(dlq_events):
            return False

        dlq_entry = dlq_events[index]
        event = Event.from_dict(dlq_entry["event"])

        # Re-deliver
        await self._deliver_locally(event)

        # Remove from DLQ
        if self._redis:
            try:
                await self._redis.lrem(self._dlq_key(), 1, json.dumps(dlq_entry))
            except Exception as e:
                logger.error(f"Error removing from DLQ: {e}")

        return True

    def get_metrics(self) -> Dict[str, Any]:
        """Get event bus metrics."""
        return {
            **self._metrics,
            "subscriptions": len(self._subscriptions),
            "server_id": self.server_id,
            "redis_connected": self._redis is not None,
        }

    def get_subscriptions(self) -> List[Dict[str, Any]]:
        """Get list of active subscriptions."""
        return [
            {
                "id": sub.subscription_id,
                "pattern": sub.pattern,
                "tenantId": sub.tenant_id,
                "active": sub.active,
                "createdAt": sub.created_at.isoformat(),
            }
            for sub in self._subscriptions.values()
        ]


# Convenience decorators
def event_handler(pattern: str, tenant_id: Optional[str] = None):
    """
    Decorator to register an event handler.

    Usage:
        @event_handler("patient.*")
        async def handle_patient_events(event: Event):
            ...
    """
    def decorator(handler: Callable[[Event], Awaitable[None]]):
        handler._event_pattern = pattern
        handler._event_tenant_id = tenant_id
        return handler
    return decorator


# Global event bus instance
event_bus = EventBus()
