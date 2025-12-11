"""
Notification Service

Multi-channel notification delivery with:
- Push notifications
- Email notifications
- SMS notifications
- In-app notifications
- Notification preferences
- Delivery tracking

EPIC-001: US-001.7 Notification Service
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import logging

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    IN_APP = "in_app"
    PUSH = "push"
    EMAIL = "email"
    SMS = "sms"
    WEBSOCKET = "websocket"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationType(str, Enum):
    """Types of notifications."""
    # System
    SYSTEM = "system"
    ALERT = "alert"
    REMINDER = "reminder"

    # Communication
    MESSAGE = "message"
    MENTION = "mention"
    REPLY = "reply"

    # Clinical
    APPOINTMENT = "appointment"
    LAB_RESULT = "lab_result"
    MEDICATION = "medication"
    VITAL_ALERT = "vital_alert"
    CARE_PLAN = "care_plan"

    # Administrative
    TASK_ASSIGNED = "task_assigned"
    APPROVAL_REQUIRED = "approval_required"
    DOCUMENT_SIGNED = "document_signed"

    # Telehealth
    VIDEO_CALL_INCOMING = "video_call_incoming"
    WAITING_ROOM = "waiting_room"


@dataclass
class Notification:
    """Notification structure."""
    notification_id: str
    tenant_id: str
    recipient_id: str
    notification_type: NotificationType
    title: str
    body: str
    priority: NotificationPriority = NotificationPriority.NORMAL
    channels: List[NotificationChannel] = field(default_factory=lambda: [NotificationChannel.IN_APP])
    data: Dict[str, Any] = field(default_factory=dict)
    action_url: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    scheduled_for: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    read: bool = False
    read_at: Optional[datetime] = None
    delivered: Dict[str, bool] = field(default_factory=dict)  # channel -> delivered
    delivery_errors: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "notificationId": self.notification_id,
            "tenantId": self.tenant_id,
            "recipientId": self.recipient_id,
            "notificationType": self.notification_type.value,
            "title": self.title,
            "body": self.body,
            "priority": self.priority.value,
            "channels": [c.value for c in self.channels],
            "data": self.data,
            "actionUrl": self.action_url,
            "imageUrl": self.image_url,
            "createdAt": self.created_at.isoformat(),
            "scheduledFor": self.scheduled_for.isoformat() if self.scheduled_for else None,
            "expiresAt": self.expires_at.isoformat() if self.expires_at else None,
            "read": self.read,
            "readAt": self.read_at.isoformat() if self.read_at else None,
            "delivered": self.delivered,
            "deliveryErrors": self.delivery_errors,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Notification":
        return cls(
            notification_id=data["notificationId"],
            tenant_id=data["tenantId"],
            recipient_id=data["recipientId"],
            notification_type=NotificationType(data["notificationType"]),
            title=data["title"],
            body=data["body"],
            priority=NotificationPriority(data.get("priority", "normal")),
            channels=[NotificationChannel(c) for c in data.get("channels", ["in_app"])],
            data=data.get("data", {}),
            action_url=data.get("actionUrl"),
            image_url=data.get("imageUrl"),
            created_at=datetime.fromisoformat(data["createdAt"]) if "createdAt" in data else datetime.now(timezone.utc),
            scheduled_for=datetime.fromisoformat(data["scheduledFor"]) if data.get("scheduledFor") else None,
            expires_at=datetime.fromisoformat(data["expiresAt"]) if data.get("expiresAt") else None,
            read=data.get("read", False),
            read_at=datetime.fromisoformat(data["readAt"]) if data.get("readAt") else None,
            delivered=data.get("delivered", {}),
            delivery_errors=data.get("deliveryErrors", {}),
        )


@dataclass
class NotificationPreferences:
    """User notification preferences."""
    user_id: str
    channels_enabled: Dict[NotificationChannel, bool] = field(default_factory=lambda: {
        NotificationChannel.IN_APP: True,
        NotificationChannel.PUSH: True,
        NotificationChannel.EMAIL: True,
        NotificationChannel.SMS: False,
        NotificationChannel.WEBSOCKET: True,
    })
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[str] = None  # HH:MM format
    quiet_hours_end: Optional[str] = None
    type_preferences: Dict[NotificationType, List[NotificationChannel]] = field(default_factory=dict)
    muted_conversations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "userId": self.user_id,
            "channelsEnabled": {c.value: v for c, v in self.channels_enabled.items()},
            "quietHoursEnabled": self.quiet_hours_enabled,
            "quietHoursStart": self.quiet_hours_start,
            "quietHoursEnd": self.quiet_hours_end,
            "typePreferences": {
                t.value: [c.value for c in channels]
                for t, channels in self.type_preferences.items()
            },
            "mutedConversations": self.muted_conversations,
        }


class NotificationService:
    """
    Manages notification creation and delivery.

    Features:
    - Multi-channel delivery
    - Notification preferences
    - Scheduled notifications
    - Delivery tracking
    - Notification history
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        max_notifications_per_user: int = 1000,
        notification_ttl: int = 86400 * 30,  # 30 days
    ):
        self.redis_url = redis_url
        self.max_notifications_per_user = max_notifications_per_user
        self.notification_ttl = notification_ttl

        self._redis: Optional[redis.Redis] = None
        self._delivery_handlers: Dict[NotificationChannel, Callable] = {}
        self._local_notifications: Dict[str, Notification] = {}
        self._user_notifications: Dict[str, List[str]] = {}  # user_id -> notification_ids
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None

    async def start(self):
        """Initialize the notification service."""
        if self._running:
            return

        try:
            self._redis = redis.from_url(self.redis_url, decode_responses=True)
            await self._redis.ping()
            logger.info("NotificationService connected to Redis")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}. Using local storage.")
            self._redis = None

        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("NotificationService started")

    async def stop(self):
        """Stop the notification service."""
        self._running = False

        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass

        if self._redis:
            await self._redis.close()

        logger.info("NotificationService stopped")

    def _notification_key(self, notification_id: str) -> str:
        return f"notification:{notification_id}"

    def _user_notifications_key(self, user_id: str) -> str:
        return f"user_notifications:{user_id}"

    def _preferences_key(self, user_id: str) -> str:
        return f"notification_preferences:{user_id}"

    def _scheduled_key(self) -> str:
        return "scheduled_notifications"

    def register_delivery_handler(
        self,
        channel: NotificationChannel,
        handler: Callable,
    ):
        """
        Register a delivery handler for a channel.

        Args:
            channel: Notification channel
            handler: Async function to deliver notification
        """
        self._delivery_handlers[channel] = handler
        logger.info(f"Registered delivery handler for {channel.value}")

    async def send_notification(
        self,
        tenant_id: str,
        recipient_id: str,
        notification_type: NotificationType,
        title: str,
        body: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        channels: Optional[List[NotificationChannel]] = None,
        data: Optional[Dict[str, Any]] = None,
        action_url: Optional[str] = None,
        image_url: Optional[str] = None,
        scheduled_for: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
    ) -> Notification:
        """
        Send a notification.

        Args:
            tenant_id: Tenant ID
            recipient_id: Recipient user ID
            notification_type: Type of notification
            title: Notification title
            body: Notification body
            priority: Priority level
            channels: Delivery channels (uses preferences if not specified)
            data: Additional data payload
            action_url: Action URL when clicked
            image_url: Image URL
            scheduled_for: Schedule delivery time
            expires_at: Expiration time

        Returns:
            Created Notification
        """
        notification = Notification(
            notification_id=str(uuid4()),
            tenant_id=tenant_id,
            recipient_id=recipient_id,
            notification_type=notification_type,
            title=title,
            body=body,
            priority=priority,
            channels=channels or [NotificationChannel.IN_APP],
            data=data or {},
            action_url=action_url,
            image_url=image_url,
            scheduled_for=scheduled_for,
            expires_at=expires_at,
        )

        # Get user preferences
        preferences = await self.get_preferences(recipient_id)
        if preferences:
            # Filter channels based on preferences
            enabled_channels = []
            for channel in notification.channels:
                if preferences.channels_enabled.get(channel, False):
                    enabled_channels.append(channel)
            notification.channels = enabled_channels or [NotificationChannel.IN_APP]

        # Store notification
        await self._store_notification(notification)

        # If scheduled, add to schedule queue
        if scheduled_for and scheduled_for > datetime.now(timezone.utc):
            if self._redis:
                try:
                    await self._redis.zadd(
                        self._scheduled_key(),
                        {notification.notification_id: scheduled_for.timestamp()},
                    )
                except Exception as e:
                    logger.error(f"Redis error scheduling notification: {e}")
            logger.info(f"Notification scheduled: {notification.notification_id}")
        else:
            # Deliver immediately
            await self._deliver_notification(notification)

        logger.info(f"Notification created: {notification.notification_id}")
        return notification

    async def get_notification(self, notification_id: str) -> Optional[Notification]:
        """Get a notification by ID."""
        if self._redis:
            try:
                data = await self._redis.get(self._notification_key(notification_id))
                if data:
                    return Notification.from_dict(json.loads(data))
            except Exception as e:
                logger.error(f"Redis error getting notification: {e}")

        return self._local_notifications.get(notification_id)

    async def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        notification_type: Optional[NotificationType] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Notification]:
        """
        Get notifications for a user.

        Args:
            user_id: User ID
            unread_only: Only return unread notifications
            notification_type: Filter by type
            limit: Maximum notifications to return
            offset: Offset for pagination

        Returns:
            List of notifications
        """
        notifications = []

        if self._redis:
            try:
                notification_ids = await self._redis.lrange(
                    self._user_notifications_key(user_id),
                    offset,
                    offset + limit - 1,
                )
                for nid in notification_ids:
                    notification = await self.get_notification(nid)
                    if notification:
                        notifications.append(notification)
            except Exception as e:
                logger.error(f"Redis error getting user notifications: {e}")

        # Also check local storage
        if user_id in self._user_notifications:
            for nid in self._user_notifications[user_id][offset:offset + limit]:
                notification = self._local_notifications.get(nid)
                if notification and notification not in notifications:
                    notifications.append(notification)

        # Filter
        filtered = []
        for notification in notifications:
            if unread_only and notification.read:
                continue
            if notification_type and notification.notification_type != notification_type:
                continue
            filtered.append(notification)

        return filtered

    async def mark_as_read(
        self,
        notification_id: str,
        user_id: str,
    ) -> bool:
        """Mark a notification as read."""
        notification = await self.get_notification(notification_id)
        if not notification or notification.recipient_id != user_id:
            return False

        notification.read = True
        notification.read_at = datetime.now(timezone.utc)
        await self._store_notification(notification)

        logger.debug(f"Notification {notification_id} marked as read")
        return True

    async def mark_all_as_read(self, user_id: str) -> int:
        """Mark all notifications for a user as read."""
        notifications = await self.get_user_notifications(user_id, unread_only=True)
        count = 0

        for notification in notifications:
            notification.read = True
            notification.read_at = datetime.now(timezone.utc)
            await self._store_notification(notification)
            count += 1

        logger.info(f"Marked {count} notifications as read for {user_id}")
        return count

    async def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications."""
        notifications = await self.get_user_notifications(user_id, unread_only=True)
        return len(notifications)

    async def delete_notification(self, notification_id: str, user_id: str) -> bool:
        """Delete a notification."""
        notification = await self.get_notification(notification_id)
        if not notification or notification.recipient_id != user_id:
            return False

        if self._redis:
            try:
                await self._redis.delete(self._notification_key(notification_id))
                await self._redis.lrem(
                    self._user_notifications_key(user_id),
                    0,
                    notification_id,
                )
            except Exception as e:
                logger.error(f"Redis error deleting notification: {e}")

        self._local_notifications.pop(notification_id, None)
        if user_id in self._user_notifications:
            try:
                self._user_notifications[user_id].remove(notification_id)
            except ValueError:
                pass

        logger.info(f"Notification deleted: {notification_id}")
        return True

    async def get_preferences(self, user_id: str) -> Optional[NotificationPreferences]:
        """Get notification preferences for a user."""
        if self._redis:
            try:
                data = await self._redis.get(self._preferences_key(user_id))
                if data:
                    pref_data = json.loads(data)
                    return NotificationPreferences(
                        user_id=pref_data["userId"],
                        channels_enabled={
                            NotificationChannel(c): v
                            for c, v in pref_data.get("channelsEnabled", {}).items()
                        },
                        quiet_hours_enabled=pref_data.get("quietHoursEnabled", False),
                        quiet_hours_start=pref_data.get("quietHoursStart"),
                        quiet_hours_end=pref_data.get("quietHoursEnd"),
                        muted_conversations=pref_data.get("mutedConversations", []),
                    )
            except Exception as e:
                logger.error(f"Redis error getting preferences: {e}")

        return None

    async def update_preferences(
        self,
        user_id: str,
        preferences: NotificationPreferences,
    ):
        """Update notification preferences."""
        if self._redis:
            try:
                await self._redis.set(
                    self._preferences_key(user_id),
                    json.dumps(preferences.to_dict()),
                )
            except Exception as e:
                logger.error(f"Redis error updating preferences: {e}")

        logger.info(f"Updated notification preferences for {user_id}")

    async def _store_notification(self, notification: Notification):
        """Store notification data."""
        if self._redis:
            try:
                await self._redis.setex(
                    self._notification_key(notification.notification_id),
                    self.notification_ttl,
                    json.dumps(notification.to_dict()),
                )
                await self._redis.lpush(
                    self._user_notifications_key(notification.recipient_id),
                    notification.notification_id,
                )
                await self._redis.ltrim(
                    self._user_notifications_key(notification.recipient_id),
                    0,
                    self.max_notifications_per_user - 1,
                )
            except Exception as e:
                logger.error(f"Redis error storing notification: {e}")
                self._local_notifications[notification.notification_id] = notification
        else:
            self._local_notifications[notification.notification_id] = notification
            if notification.recipient_id not in self._user_notifications:
                self._user_notifications[notification.recipient_id] = []
            self._user_notifications[notification.recipient_id].insert(0, notification.notification_id)
            self._user_notifications[notification.recipient_id] = self._user_notifications[notification.recipient_id][:self.max_notifications_per_user]

    async def _deliver_notification(self, notification: Notification):
        """Deliver notification through registered channels."""
        for channel in notification.channels:
            handler = self._delivery_handlers.get(channel)
            if handler:
                try:
                    await handler(notification)
                    notification.delivered[channel.value] = True
                    logger.debug(f"Delivered notification {notification.notification_id} via {channel.value}")
                except Exception as e:
                    notification.delivered[channel.value] = False
                    notification.delivery_errors[channel.value] = str(e)
                    logger.error(f"Failed to deliver notification via {channel.value}: {e}")
            else:
                logger.warning(f"No handler registered for channel {channel.value}")

        # Update notification with delivery status
        await self._store_notification(notification)

    async def _scheduler_loop(self):
        """Background task to deliver scheduled notifications."""
        while self._running:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds

                now = datetime.now(timezone.utc).timestamp()

                if self._redis:
                    try:
                        # Get notifications due for delivery
                        due_notifications = await self._redis.zrangebyscore(
                            self._scheduled_key(),
                            "-inf",
                            now,
                        )

                        for notification_id in due_notifications:
                            notification = await self.get_notification(notification_id)
                            if notification:
                                await self._deliver_notification(notification)
                                await self._redis.zrem(self._scheduled_key(), notification_id)

                    except Exception as e:
                        logger.error(f"Redis error in scheduler: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in notification scheduler: {e}")


# Global notification service instance
notification_service = NotificationService()
