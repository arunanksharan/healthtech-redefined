"""
FHIR Subscription Service

Implements FHIR R4 Subscriptions for real-time notifications:
- REST hook notifications (webhooks)
- WebSocket notifications
- Email notifications
- Retry logic with exponential backoff
- Dead letter queue handling
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import asyncio
import logging
import json
import hashlib
import hmac

logger = logging.getLogger(__name__)


class SubscriptionStatus(str, Enum):
    """FHIR Subscription status."""
    REQUESTED = "requested"
    ACTIVE = "active"
    ERROR = "error"
    OFF = "off"


class ChannelType(str, Enum):
    """Subscription channel types."""
    REST_HOOK = "rest-hook"
    WEBSOCKET = "websocket"
    EMAIL = "email"
    MESSAGE = "message"


@dataclass
class SubscriptionChannel:
    """Subscription channel configuration."""
    channel_type: ChannelType
    endpoint: str
    payload: str = "application/fhir+json"  # Content type for notifications
    header: List[str] = field(default_factory=list)  # Custom headers

    # Security
    secret: Optional[str] = None  # For HMAC signature


@dataclass
class DeliveryAttempt:
    """Record of a notification delivery attempt."""
    attempt_id: str
    subscription_id: str
    notification_id: str
    timestamp: datetime
    status_code: Optional[int] = None
    success: bool = False
    error_message: Optional[str] = None
    response_time_ms: Optional[float] = None


@dataclass
class Subscription:
    """FHIR Subscription resource."""
    subscription_id: str
    tenant_id: str

    # Status
    status: SubscriptionStatus = SubscriptionStatus.REQUESTED
    reason: str = ""
    error: Optional[str] = None

    # Criteria
    criteria: str = ""  # FHIR search query (e.g., "Observation?code=85354-9")
    resource_type: str = ""  # Extracted from criteria

    # Channel
    channel: Optional[SubscriptionChannel] = None

    # Timing
    end: Optional[datetime] = None  # When subscription expires
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Delivery tracking
    last_notification_at: Optional[datetime] = None
    notification_count: int = 0
    error_count: int = 0
    consecutive_failures: int = 0


@dataclass
class NotificationEvent:
    """A notification to be delivered."""
    event_id: str
    subscription_id: str
    tenant_id: str

    resource_type: str
    resource_id: str
    resource: Dict[str, Any]

    trigger: str = "create"  # create, update, delete
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Delivery status
    delivered: bool = False
    delivery_attempts: List[DeliveryAttempt] = field(default_factory=list)


class SubscriptionMatcher:
    """
    Matches resources against subscription criteria.

    Evaluates FHIR search criteria to determine if a resource
    matches a subscription.
    """

    def matches(
        self,
        subscription: Subscription,
        resource: Dict[str, Any],
        trigger: str,
    ) -> bool:
        """
        Check if a resource matches subscription criteria.

        Args:
            subscription: Subscription to check
            resource: FHIR resource that was created/updated
            trigger: Type of trigger (create, update, delete)

        Returns:
            True if resource matches subscription criteria
        """
        # Parse criteria
        criteria = subscription.criteria
        if "?" not in criteria:
            # Simple resource type match
            return resource.get("resourceType") == criteria

        resource_type, query_string = criteria.split("?", 1)

        # Check resource type
        if resource.get("resourceType") != resource_type:
            return False

        # Parse query parameters
        params = self._parse_query_string(query_string)

        # Evaluate each parameter
        for param_name, param_value in params.items():
            if not self._matches_parameter(resource, param_name, param_value):
                return False

        return True

    def _parse_query_string(self, query_string: str) -> Dict[str, str]:
        """Parse query string into parameter dict."""
        params = {}
        for part in query_string.split("&"):
            if "=" in part:
                key, value = part.split("=", 1)
                params[key] = value
        return params

    def _matches_parameter(
        self,
        resource: Dict[str, Any],
        param_name: str,
        param_value: str,
    ) -> bool:
        """Check if resource matches a single search parameter."""
        # Handle common parameters
        if param_name == "code":
            return self._matches_code(resource, param_value)
        elif param_name == "patient":
            return self._matches_reference(resource, "subject", param_value)
        elif param_name == "subject":
            return self._matches_reference(resource, "subject", param_value)
        elif param_name == "status":
            return resource.get("status") == param_value
        elif param_name == "category":
            return self._matches_code_in_field(resource, "category", param_value)

        # Default: simple field match
        return str(resource.get(param_name, "")) == param_value

    def _matches_code(
        self,
        resource: Dict[str, Any],
        param_value: str,
    ) -> bool:
        """Match code parameter against resource."""
        code_field = resource.get("code", {})

        # Check in codings
        for coding in code_field.get("coding", []):
            if param_value in (coding.get("code"), f"{coding.get('system')}|{coding.get('code')}"):
                return True

        return False

    def _matches_reference(
        self,
        resource: Dict[str, Any],
        field_name: str,
        param_value: str,
    ) -> bool:
        """Match reference parameter."""
        ref = resource.get(field_name, {})
        ref_string = ref.get("reference", "")

        # Handle different reference formats
        if param_value in ref_string:
            return True
        if ref_string.endswith(f"/{param_value}"):
            return True

        return False

    def _matches_code_in_field(
        self,
        resource: Dict[str, Any],
        field_name: str,
        param_value: str,
    ) -> bool:
        """Match code within a field (which may be a list)."""
        field_value = resource.get(field_name, [])
        if not isinstance(field_value, list):
            field_value = [field_value]

        for item in field_value:
            for coding in item.get("coding", []):
                if param_value in (coding.get("code"), f"{coding.get('system')}|{coding.get('code')}"):
                    return True

        return False


class NotificationDelivery:
    """
    Handles delivery of subscription notifications.

    Supports:
    - REST hook (HTTP POST)
    - WebSocket
    - Email
    - Retry with exponential backoff
    """

    def __init__(self):
        self._websocket_handlers: Dict[str, Callable] = {}
        self._email_handler: Optional[Callable] = None

        # Retry configuration
        self.max_retries = 5
        self.base_delay_seconds = 10
        self.max_delay_seconds = 3600

    def register_websocket_handler(
        self,
        subscription_id: str,
        handler: Callable[[Dict[str, Any]], None],
    ):
        """Register a WebSocket handler for a subscription."""
        self._websocket_handlers[subscription_id] = handler

    def unregister_websocket_handler(self, subscription_id: str):
        """Unregister a WebSocket handler."""
        self._websocket_handlers.pop(subscription_id, None)

    def register_email_handler(
        self,
        handler: Callable[[str, str, str], None],
    ):
        """Register an email sending handler."""
        self._email_handler = handler

    async def deliver(
        self,
        subscription: Subscription,
        event: NotificationEvent,
    ) -> DeliveryAttempt:
        """
        Deliver a notification.

        Args:
            subscription: Subscription to notify
            event: Event to deliver

        Returns:
            DeliveryAttempt record
        """
        channel = subscription.channel
        if not channel:
            return self._create_failed_attempt(
                subscription, event, "No channel configured"
            )

        if channel.channel_type == ChannelType.REST_HOOK:
            return await self._deliver_rest_hook(subscription, event)
        elif channel.channel_type == ChannelType.WEBSOCKET:
            return await self._deliver_websocket(subscription, event)
        elif channel.channel_type == ChannelType.EMAIL:
            return await self._deliver_email(subscription, event)
        else:
            return self._create_failed_attempt(
                subscription, event, f"Unsupported channel type: {channel.channel_type}"
            )

    async def _deliver_rest_hook(
        self,
        subscription: Subscription,
        event: NotificationEvent,
    ) -> DeliveryAttempt:
        """Deliver via REST hook (HTTP POST)."""
        import aiohttp

        channel = subscription.channel
        start_time = datetime.now(timezone.utc)

        # Build notification bundle
        bundle = self._build_notification_bundle(subscription, event)

        # Build headers
        headers = {
            "Content-Type": channel.payload,
        }

        # Add custom headers
        for header in channel.header:
            if ":" in header:
                name, value = header.split(":", 1)
                headers[name.strip()] = value.strip()

        # Add HMAC signature if secret is configured
        if channel.secret:
            payload_bytes = json.dumps(bundle).encode()
            signature = hmac.new(
                channel.secret.encode(),
                payload_bytes,
                hashlib.sha256
            ).hexdigest()
            headers["X-Hub-Signature-256"] = f"sha256={signature}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    channel.endpoint,
                    json=bundle,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    end_time = datetime.now(timezone.utc)
                    response_time = (end_time - start_time).total_seconds() * 1000

                    success = 200 <= response.status < 300

                    attempt = DeliveryAttempt(
                        attempt_id=str(uuid4()),
                        subscription_id=subscription.subscription_id,
                        notification_id=event.event_id,
                        timestamp=start_time,
                        status_code=response.status,
                        success=success,
                        response_time_ms=response_time,
                    )

                    if not success:
                        attempt.error_message = f"HTTP {response.status}"

                    return attempt

        except asyncio.TimeoutError:
            return self._create_failed_attempt(
                subscription, event, "Request timeout"
            )
        except Exception as e:
            return self._create_failed_attempt(
                subscription, event, str(e)
            )

    async def _deliver_websocket(
        self,
        subscription: Subscription,
        event: NotificationEvent,
    ) -> DeliveryAttempt:
        """Deliver via WebSocket."""
        handler = self._websocket_handlers.get(subscription.subscription_id)

        if not handler:
            return self._create_failed_attempt(
                subscription, event, "No WebSocket connection"
            )

        try:
            bundle = self._build_notification_bundle(subscription, event)
            handler(bundle)

            return DeliveryAttempt(
                attempt_id=str(uuid4()),
                subscription_id=subscription.subscription_id,
                notification_id=event.event_id,
                timestamp=datetime.now(timezone.utc),
                success=True,
            )

        except Exception as e:
            return self._create_failed_attempt(
                subscription, event, str(e)
            )

    async def _deliver_email(
        self,
        subscription: Subscription,
        event: NotificationEvent,
    ) -> DeliveryAttempt:
        """Deliver via email."""
        if not self._email_handler:
            return self._create_failed_attempt(
                subscription, event, "Email handler not configured"
            )

        channel = subscription.channel

        try:
            subject = f"FHIR Notification: {event.resource_type}/{event.resource_id}"
            body = json.dumps(event.resource, indent=2)

            self._email_handler(channel.endpoint, subject, body)

            return DeliveryAttempt(
                attempt_id=str(uuid4()),
                subscription_id=subscription.subscription_id,
                notification_id=event.event_id,
                timestamp=datetime.now(timezone.utc),
                success=True,
            )

        except Exception as e:
            return self._create_failed_attempt(
                subscription, event, str(e)
            )

    def _build_notification_bundle(
        self,
        subscription: Subscription,
        event: NotificationEvent,
    ) -> Dict[str, Any]:
        """Build a FHIR notification bundle."""
        return {
            "resourceType": "Bundle",
            "type": "history",
            "timestamp": event.timestamp.isoformat(),
            "entry": [
                {
                    "fullUrl": f"{event.resource_type}/{event.resource_id}",
                    "resource": event.resource,
                    "request": {
                        "method": self._trigger_to_method(event.trigger),
                        "url": f"{event.resource_type}/{event.resource_id}",
                    },
                }
            ],
        }

    def _trigger_to_method(self, trigger: str) -> str:
        """Convert trigger to HTTP method."""
        return {
            "create": "POST",
            "update": "PUT",
            "delete": "DELETE",
        }.get(trigger, "PUT")

    def _create_failed_attempt(
        self,
        subscription: Subscription,
        event: NotificationEvent,
        error: str,
    ) -> DeliveryAttempt:
        """Create a failed delivery attempt."""
        return DeliveryAttempt(
            attempt_id=str(uuid4()),
            subscription_id=subscription.subscription_id,
            notification_id=event.event_id,
            timestamp=datetime.now(timezone.utc),
            success=False,
            error_message=error,
        )

    def calculate_retry_delay(self, attempt_number: int) -> int:
        """Calculate retry delay with exponential backoff."""
        delay = self.base_delay_seconds * (2 ** (attempt_number - 1))
        return min(delay, self.max_delay_seconds)


class SubscriptionService:
    """
    FHIR Subscription management service.

    Handles:
    - Subscription CRUD
    - Event processing
    - Notification delivery
    - Retry logic
    - Dead letter handling
    """

    def __init__(self):
        self._subscriptions: Dict[str, Subscription] = {}
        self._matcher = SubscriptionMatcher()
        self._delivery = NotificationDelivery()

        # Dead letter queue
        self._dead_letters: List[NotificationEvent] = []

        # Event queue
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._processing = False

    async def create_subscription(
        self,
        tenant_id: str,
        criteria: str,
        channel_type: ChannelType,
        endpoint: str,
        reason: str = "",
        payload: str = "application/fhir+json",
        headers: Optional[List[str]] = None,
        secret: Optional[str] = None,
        end: Optional[datetime] = None,
    ) -> Subscription:
        """Create a new subscription."""
        # Extract resource type from criteria
        resource_type = criteria.split("?")[0] if "?" in criteria else criteria

        channel = SubscriptionChannel(
            channel_type=channel_type,
            endpoint=endpoint,
            payload=payload,
            header=headers or [],
            secret=secret,
        )

        subscription = Subscription(
            subscription_id=str(uuid4()),
            tenant_id=tenant_id,
            status=SubscriptionStatus.ACTIVE,
            reason=reason,
            criteria=criteria,
            resource_type=resource_type,
            channel=channel,
            end=end,
        )

        self._subscriptions[subscription.subscription_id] = subscription
        logger.info(f"Created subscription: {subscription.subscription_id}")

        return subscription

    async def get_subscription(
        self,
        subscription_id: str,
    ) -> Optional[Subscription]:
        """Get a subscription by ID."""
        return self._subscriptions.get(subscription_id)

    async def update_subscription(
        self,
        subscription_id: str,
        status: Optional[SubscriptionStatus] = None,
        criteria: Optional[str] = None,
        endpoint: Optional[str] = None,
    ) -> Optional[Subscription]:
        """Update a subscription."""
        subscription = self._subscriptions.get(subscription_id)
        if not subscription:
            return None

        if status:
            subscription.status = status
        if criteria:
            subscription.criteria = criteria
            subscription.resource_type = criteria.split("?")[0]
        if endpoint and subscription.channel:
            subscription.channel.endpoint = endpoint

        return subscription

    async def delete_subscription(
        self,
        subscription_id: str,
    ) -> bool:
        """Delete a subscription."""
        if subscription_id in self._subscriptions:
            del self._subscriptions[subscription_id]
            self._delivery.unregister_websocket_handler(subscription_id)
            return True
        return False

    async def get_tenant_subscriptions(
        self,
        tenant_id: str,
        status: Optional[SubscriptionStatus] = None,
    ) -> List[Subscription]:
        """Get all subscriptions for a tenant."""
        subscriptions = [
            s for s in self._subscriptions.values()
            if s.tenant_id == tenant_id
        ]

        if status:
            subscriptions = [s for s in subscriptions if s.status == status]

        return subscriptions

    async def notify_resource_event(
        self,
        tenant_id: str,
        resource: Dict[str, Any],
        trigger: str = "create",
    ):
        """
        Process a resource event and notify matching subscriptions.

        Args:
            tenant_id: Tenant the resource belongs to
            resource: FHIR resource that was created/updated/deleted
            trigger: Type of event (create, update, delete)
        """
        resource_type = resource.get("resourceType")
        resource_id = resource.get("id")

        # Find matching subscriptions
        matching = []
        for subscription in self._subscriptions.values():
            if subscription.tenant_id != tenant_id:
                continue
            if subscription.status != SubscriptionStatus.ACTIVE:
                continue
            if subscription.end and subscription.end < datetime.now(timezone.utc):
                subscription.status = SubscriptionStatus.OFF
                continue

            if self._matcher.matches(subscription, resource, trigger):
                matching.append(subscription)

        # Create events and queue for delivery
        for subscription in matching:
            event = NotificationEvent(
                event_id=str(uuid4()),
                subscription_id=subscription.subscription_id,
                tenant_id=tenant_id,
                resource_type=resource_type,
                resource_id=resource_id,
                resource=resource,
                trigger=trigger,
            )

            await self._event_queue.put((subscription, event))

        logger.info(f"Queued {len(matching)} notifications for {resource_type}/{resource_id}")

    async def process_events(self):
        """Process queued notification events."""
        self._processing = True

        while self._processing:
            try:
                subscription, event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0
                )

                await self._deliver_with_retry(subscription, event)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")

    def stop_processing(self):
        """Stop event processing."""
        self._processing = False

    async def _deliver_with_retry(
        self,
        subscription: Subscription,
        event: NotificationEvent,
    ):
        """Deliver event with retry logic."""
        for attempt_num in range(1, self._delivery.max_retries + 1):
            attempt = await self._delivery.deliver(subscription, event)
            event.delivery_attempts.append(attempt)

            if attempt.success:
                event.delivered = True
                subscription.last_notification_at = datetime.now(timezone.utc)
                subscription.notification_count += 1
                subscription.consecutive_failures = 0
                return

            # Update error tracking
            subscription.error_count += 1
            subscription.consecutive_failures += 1

            # Check if subscription should be disabled
            if subscription.consecutive_failures >= 10:
                subscription.status = SubscriptionStatus.ERROR
                subscription.error = "Too many consecutive failures"
                logger.warning(f"Disabled subscription {subscription.subscription_id} due to failures")
                break

            # Wait before retry
            if attempt_num < self._delivery.max_retries:
                delay = self._delivery.calculate_retry_delay(attempt_num)
                await asyncio.sleep(delay)

        # All retries failed - move to dead letter queue
        if not event.delivered:
            self._dead_letters.append(event)
            logger.error(f"Event {event.event_id} moved to dead letter queue")

    async def get_dead_letters(
        self,
        tenant_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[NotificationEvent]:
        """Get events in the dead letter queue."""
        events = self._dead_letters

        if tenant_id:
            events = [e for e in events if e.tenant_id == tenant_id]

        return events[:limit]

    async def retry_dead_letter(
        self,
        event_id: str,
    ) -> bool:
        """Retry a dead letter event."""
        for event in self._dead_letters:
            if event.event_id == event_id:
                subscription = self._subscriptions.get(event.subscription_id)
                if subscription and subscription.status == SubscriptionStatus.ACTIVE:
                    await self._event_queue.put((subscription, event))
                    self._dead_letters.remove(event)
                    return True
        return False

    def to_fhir_resource(self, subscription: Subscription) -> Dict[str, Any]:
        """Convert subscription to FHIR resource format."""
        resource = {
            "resourceType": "Subscription",
            "id": subscription.subscription_id,
            "status": subscription.status.value,
            "reason": subscription.reason,
            "criteria": subscription.criteria,
        }

        if subscription.channel:
            resource["channel"] = {
                "type": subscription.channel.channel_type.value,
                "endpoint": subscription.channel.endpoint,
                "payload": subscription.channel.payload,
                "header": subscription.channel.header,
            }

        if subscription.end:
            resource["end"] = subscription.end.isoformat()

        if subscription.error:
            resource["error"] = subscription.error

        return resource

    def from_fhir_resource(
        self,
        resource: Dict[str, Any],
        tenant_id: str,
    ) -> Subscription:
        """Create subscription from FHIR resource."""
        channel_data = resource.get("channel", {})

        channel = SubscriptionChannel(
            channel_type=ChannelType(channel_data.get("type", "rest-hook")),
            endpoint=channel_data.get("endpoint", ""),
            payload=channel_data.get("payload", "application/fhir+json"),
            header=channel_data.get("header", []),
        )

        end = None
        if "end" in resource:
            end = datetime.fromisoformat(resource["end"].replace("Z", "+00:00"))

        return Subscription(
            subscription_id=resource.get("id", str(uuid4())),
            tenant_id=tenant_id,
            status=SubscriptionStatus(resource.get("status", "requested")),
            reason=resource.get("reason", ""),
            criteria=resource.get("criteria", ""),
            resource_type=resource.get("criteria", "").split("?")[0],
            channel=channel,
            end=end,
        )


# Global instance
subscription_service = SubscriptionService()
