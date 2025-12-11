"""
Presence Management System

Manages user presence and status including:
- Online/offline status tracking
- Custom status messages
- Typing indicators
- Last seen timestamps
- Multi-device presence synchronization

EPIC-001: US-001.3 Presence Management System
"""

import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import logging

import redis.asyncio as redis
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class PresenceStatus(str, Enum):
    """User presence status."""
    ONLINE = "online"
    AWAY = "away"
    BUSY = "busy"
    DO_NOT_DISTURB = "dnd"
    OFFLINE = "offline"
    INVISIBLE = "invisible"


class ActivityType(str, Enum):
    """Type of user activity."""
    ACTIVE = "active"
    IDLE = "idle"
    TYPING = "typing"
    IN_CALL = "in_call"
    IN_MEETING = "in_meeting"


@dataclass
class UserPresence:
    """User presence information."""
    user_id: str
    tenant_id: str
    status: PresenceStatus = PresenceStatus.OFFLINE
    status_message: Optional[str] = None
    activity: ActivityType = ActivityType.IDLE
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    devices: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "userId": self.user_id,
            "tenantId": self.tenant_id,
            "status": self.status.value,
            "statusMessage": self.status_message,
            "activity": self.activity.value,
            "lastSeen": self.last_seen.isoformat(),
            "lastActivity": self.last_activity.isoformat(),
            "devices": list(self.devices),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserPresence":
        return cls(
            user_id=data["userId"],
            tenant_id=data["tenantId"],
            status=PresenceStatus(data.get("status", "offline")),
            status_message=data.get("statusMessage"),
            activity=ActivityType(data.get("activity", "idle")),
            last_seen=datetime.fromisoformat(data["lastSeen"]) if "lastSeen" in data else datetime.now(timezone.utc),
            last_activity=datetime.fromisoformat(data["lastActivity"]) if "lastActivity" in data else datetime.now(timezone.utc),
            devices=set(data.get("devices", [])),
            metadata=data.get("metadata", {}),
        )


@dataclass
class TypingIndicator:
    """Typing indicator for a conversation."""
    user_id: str
    conversation_id: str
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(seconds=10))


class PresenceManager:
    """
    Manages user presence and typing indicators.

    Features:
    - Redis-backed presence storage for scalability
    - Multi-device presence aggregation
    - Automatic offline detection
    - Typing indicator management
    - Presence subscriptions
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        presence_ttl: int = 300,  # 5 minutes
        typing_ttl: int = 10,  # 10 seconds
        idle_timeout: int = 300,  # 5 minutes until idle
        offline_timeout: int = 600,  # 10 minutes until offline
    ):
        self.redis_url = redis_url
        self.presence_ttl = presence_ttl
        self.typing_ttl = typing_ttl
        self.idle_timeout = idle_timeout
        self.offline_timeout = offline_timeout

        self._redis: Optional[redis.Redis] = None
        self._local_presence: Dict[str, UserPresence] = {}  # Fallback if Redis unavailable
        self._typing_indicators: Dict[str, Dict[str, TypingIndicator]] = {}  # conversation_id -> user_id -> indicator
        self._subscribers: Dict[str, Set[str]] = {}  # tenant_id -> set of subscriber callbacks
        self._running = False
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self):
        """Initialize Redis connection and start background tasks."""
        if self._running:
            return

        try:
            self._redis = redis.from_url(self.redis_url, decode_responses=True)
            await self._redis.ping()
            logger.info("PresenceManager connected to Redis")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}. Using local storage.")
            self._redis = None

        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("PresenceManager started")

    async def stop(self):
        """Stop the presence manager and cleanup."""
        self._running = False

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        if self._redis:
            await self._redis.close()

        logger.info("PresenceManager stopped")

    def _presence_key(self, user_id: str) -> str:
        """Generate Redis key for user presence."""
        return f"presence:{user_id}"

    def _tenant_presence_key(self, tenant_id: str) -> str:
        """Generate Redis key for tenant presence set."""
        return f"presence:tenant:{tenant_id}"

    def _typing_key(self, conversation_id: str) -> str:
        """Generate Redis key for typing indicators."""
        return f"typing:{conversation_id}"

    async def update_presence(
        self,
        user_id: str,
        tenant_id: str,
        status: Optional[PresenceStatus] = None,
        status_message: Optional[str] = None,
        activity: Optional[ActivityType] = None,
        device_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UserPresence:
        """
        Update user presence.

        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            status: New presence status
            status_message: Custom status message
            activity: Current activity type
            device_id: Device to register
            metadata: Additional metadata

        Returns:
            Updated UserPresence
        """
        presence = await self.get_presence(user_id) or UserPresence(
            user_id=user_id,
            tenant_id=tenant_id,
        )

        now = datetime.now(timezone.utc)

        if status is not None:
            presence.status = status
        if status_message is not None:
            presence.status_message = status_message
        if activity is not None:
            presence.activity = activity
        if device_id:
            presence.devices.add(device_id)
        if metadata:
            presence.metadata.update(metadata)

        presence.last_activity = now
        if presence.status != PresenceStatus.OFFLINE:
            presence.last_seen = now

        # Store presence
        if self._redis:
            try:
                await self._redis.setex(
                    self._presence_key(user_id),
                    self.presence_ttl,
                    json.dumps(presence.to_dict()),
                )
                await self._redis.sadd(self._tenant_presence_key(tenant_id), user_id)
            except Exception as e:
                logger.error(f"Redis error updating presence: {e}")
                self._local_presence[user_id] = presence
        else:
            self._local_presence[user_id] = presence

        # Notify subscribers
        await self._notify_presence_change(presence)

        logger.debug(f"Updated presence for {user_id}: {presence.status.value}")
        return presence

    async def get_presence(self, user_id: str) -> Optional[UserPresence]:
        """
        Get user presence.

        Args:
            user_id: User identifier

        Returns:
            UserPresence if found
        """
        if self._redis:
            try:
                data = await self._redis.get(self._presence_key(user_id))
                if data:
                    return UserPresence.from_dict(json.loads(data))
            except Exception as e:
                logger.error(f"Redis error getting presence: {e}")

        return self._local_presence.get(user_id)

    async def get_tenant_presence(self, tenant_id: str) -> List[UserPresence]:
        """
        Get presence for all users in a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            List of UserPresence objects
        """
        presences = []

        if self._redis:
            try:
                user_ids = await self._redis.smembers(self._tenant_presence_key(tenant_id))
                for user_id in user_ids:
                    presence = await self.get_presence(user_id)
                    if presence:
                        presences.append(presence)
            except Exception as e:
                logger.error(f"Redis error getting tenant presence: {e}")

        # Also include local presence for this tenant
        for user_id, presence in self._local_presence.items():
            if presence.tenant_id == tenant_id and presence not in presences:
                presences.append(presence)

        return presences

    async def set_offline(self, user_id: str, device_id: Optional[str] = None):
        """
        Set user as offline.

        Args:
            user_id: User identifier
            device_id: Specific device going offline
        """
        presence = await self.get_presence(user_id)
        if not presence:
            return

        if device_id:
            presence.devices.discard(device_id)

        # Only go offline if no devices remain
        if not presence.devices:
            presence.status = PresenceStatus.OFFLINE
            presence.last_seen = datetime.now(timezone.utc)

            if self._redis:
                try:
                    await self._redis.setex(
                        self._presence_key(user_id),
                        self.presence_ttl,
                        json.dumps(presence.to_dict()),
                    )
                except Exception as e:
                    logger.error(f"Redis error setting offline: {e}")
            else:
                self._local_presence[user_id] = presence

            await self._notify_presence_change(presence)

        logger.info(f"User {user_id} set offline")

    async def start_typing(self, user_id: str, conversation_id: str):
        """
        Start typing indicator.

        Args:
            user_id: User who is typing
            conversation_id: Conversation where typing
        """
        now = datetime.now(timezone.utc)
        indicator = TypingIndicator(
            user_id=user_id,
            conversation_id=conversation_id,
            started_at=now,
            expires_at=now + timedelta(seconds=self.typing_ttl),
        )

        if self._redis:
            try:
                await self._redis.hset(
                    self._typing_key(conversation_id),
                    user_id,
                    json.dumps({
                        "userId": user_id,
                        "startedAt": indicator.started_at.isoformat(),
                        "expiresAt": indicator.expires_at.isoformat(),
                    }),
                )
                await self._redis.expire(self._typing_key(conversation_id), self.typing_ttl)
            except Exception as e:
                logger.error(f"Redis error setting typing: {e}")

        # Local storage
        if conversation_id not in self._typing_indicators:
            self._typing_indicators[conversation_id] = {}
        self._typing_indicators[conversation_id][user_id] = indicator

        logger.debug(f"User {user_id} started typing in {conversation_id}")

    async def stop_typing(self, user_id: str, conversation_id: str):
        """
        Stop typing indicator.

        Args:
            user_id: User who stopped typing
            conversation_id: Conversation
        """
        if self._redis:
            try:
                await self._redis.hdel(self._typing_key(conversation_id), user_id)
            except Exception as e:
                logger.error(f"Redis error clearing typing: {e}")

        if conversation_id in self._typing_indicators:
            self._typing_indicators[conversation_id].pop(user_id, None)

        logger.debug(f"User {user_id} stopped typing in {conversation_id}")

    async def get_typing_users(self, conversation_id: str) -> List[str]:
        """
        Get users currently typing in a conversation.

        Args:
            conversation_id: Conversation to check

        Returns:
            List of user IDs currently typing
        """
        typing_users = []
        now = datetime.now(timezone.utc)

        if self._redis:
            try:
                typing_data = await self._redis.hgetall(self._typing_key(conversation_id))
                for user_id, data in typing_data.items():
                    indicator = json.loads(data)
                    expires_at = datetime.fromisoformat(indicator["expiresAt"])
                    if expires_at > now:
                        typing_users.append(user_id)
            except Exception as e:
                logger.error(f"Redis error getting typing: {e}")

        # Check local storage
        if conversation_id in self._typing_indicators:
            for user_id, indicator in list(self._typing_indicators[conversation_id].items()):
                if indicator.expires_at > now:
                    if user_id not in typing_users:
                        typing_users.append(user_id)
                else:
                    del self._typing_indicators[conversation_id][user_id]

        return typing_users

    async def heartbeat(self, user_id: str, device_id: Optional[str] = None):
        """
        Update user's last activity (heartbeat).

        Args:
            user_id: User identifier
            device_id: Device sending heartbeat
        """
        presence = await self.get_presence(user_id)
        if not presence:
            return

        now = datetime.now(timezone.utc)
        presence.last_activity = now

        # Check if should transition from idle to active
        if presence.activity == ActivityType.IDLE:
            presence.activity = ActivityType.ACTIVE

        if self._redis:
            try:
                await self._redis.setex(
                    self._presence_key(user_id),
                    self.presence_ttl,
                    json.dumps(presence.to_dict()),
                )
            except Exception as e:
                logger.error(f"Redis error updating heartbeat: {e}")
        else:
            self._local_presence[user_id] = presence

    async def subscribe_to_presence(self, tenant_id: str, callback_id: str):
        """
        Subscribe to presence changes in a tenant.

        Args:
            tenant_id: Tenant to subscribe to
            callback_id: Identifier for this subscription
        """
        if tenant_id not in self._subscribers:
            self._subscribers[tenant_id] = set()
        self._subscribers[tenant_id].add(callback_id)

    async def unsubscribe_from_presence(self, tenant_id: str, callback_id: str):
        """
        Unsubscribe from presence changes.

        Args:
            tenant_id: Tenant to unsubscribe from
            callback_id: Subscription identifier
        """
        if tenant_id in self._subscribers:
            self._subscribers[tenant_id].discard(callback_id)

    async def _notify_presence_change(self, presence: UserPresence):
        """Notify subscribers of a presence change."""
        # This would integrate with the ConnectionManager to broadcast updates
        # For now, we just log the change
        logger.debug(f"Presence change notification: {presence.user_id} -> {presence.status.value}")

    async def _cleanup_loop(self):
        """Background task to cleanup stale presence and typing indicators."""
        while self._running:
            try:
                await asyncio.sleep(60)  # Run every minute

                now = datetime.now(timezone.utc)

                # Check for idle/offline transitions
                if self._redis:
                    # Redis handles TTL, but we need to check for idle transitions
                    pass
                else:
                    # Clean up local storage
                    for user_id, presence in list(self._local_presence.items()):
                        elapsed = (now - presence.last_activity).total_seconds()

                        if presence.status == PresenceStatus.ONLINE:
                            if elapsed > self.idle_timeout:
                                presence.activity = ActivityType.IDLE
                            if elapsed > self.offline_timeout:
                                presence.status = PresenceStatus.OFFLINE
                                await self._notify_presence_change(presence)

                # Clean up expired typing indicators
                for conversation_id, indicators in list(self._typing_indicators.items()):
                    for user_id, indicator in list(indicators.items()):
                        if indicator.expires_at < now:
                            del self._typing_indicators[conversation_id][user_id]
                    if not indicators:
                        del self._typing_indicators[conversation_id]

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in presence cleanup loop: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get presence manager statistics."""
        return {
            "redis_connected": self._redis is not None,
            "local_presence_count": len(self._local_presence),
            "typing_conversations": len(self._typing_indicators),
            "subscriber_tenants": len(self._subscribers),
        }


# Global presence manager instance
presence_manager = PresenceManager()
