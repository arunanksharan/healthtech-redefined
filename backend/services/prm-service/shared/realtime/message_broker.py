"""
Real-Time Message Broker

Handles real-time message delivery with:
- Message delivery guarantees
- Delivery receipts (sent/delivered/read)
- Message ordering
- Offline message queue
- File attachment support

EPIC-001: US-001.4 Real-Time Messaging System
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
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class MessageStatus(str, Enum):
    """Message delivery status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class MessagePriority(str, Enum):
    """Message priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Message:
    """Real-time message structure."""
    message_id: str
    conversation_id: str
    sender_id: str
    tenant_id: str
    content: Dict[str, Any]
    content_type: str = "text"  # text, file, image, system
    priority: MessagePriority = MessagePriority.NORMAL
    status: MessageStatus = MessageStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    reply_to: Optional[str] = None
    attachments: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "messageId": self.message_id,
            "conversationId": self.conversation_id,
            "senderId": self.sender_id,
            "tenantId": self.tenant_id,
            "content": self.content,
            "contentType": self.content_type,
            "priority": self.priority.value,
            "status": self.status.value,
            "createdAt": self.created_at.isoformat(),
            "sentAt": self.sent_at.isoformat() if self.sent_at else None,
            "deliveredAt": self.delivered_at.isoformat() if self.delivered_at else None,
            "readAt": self.read_at.isoformat() if self.read_at else None,
            "metadata": self.metadata,
            "replyTo": self.reply_to,
            "attachments": self.attachments,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        return cls(
            message_id=data["messageId"],
            conversation_id=data["conversationId"],
            sender_id=data["senderId"],
            tenant_id=data["tenantId"],
            content=data["content"],
            content_type=data.get("contentType", "text"),
            priority=MessagePriority(data.get("priority", "normal")),
            status=MessageStatus(data.get("status", "pending")),
            created_at=datetime.fromisoformat(data["createdAt"]) if "createdAt" in data else datetime.now(timezone.utc),
            sent_at=datetime.fromisoformat(data["sentAt"]) if data.get("sentAt") else None,
            delivered_at=datetime.fromisoformat(data["deliveredAt"]) if data.get("deliveredAt") else None,
            read_at=datetime.fromisoformat(data["readAt"]) if data.get("readAt") else None,
            metadata=data.get("metadata", {}),
            reply_to=data.get("replyTo"),
            attachments=data.get("attachments", []),
        )


@dataclass
class DeliveryReceipt:
    """Message delivery receipt."""
    message_id: str
    user_id: str
    status: MessageStatus
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class MessageBroker:
    """
    Real-time message broker for delivering messages.

    Features:
    - Message delivery with status tracking
    - Offline queue for disconnected users
    - Delivery receipts
    - Message ordering via sequence numbers
    - Priority-based delivery
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        max_offline_messages: int = 1000,
        message_ttl: int = 86400 * 7,  # 7 days
    ):
        self.redis_url = redis_url
        self.max_offline_messages = max_offline_messages
        self.message_ttl = message_ttl

        self._redis: Optional[redis.Redis] = None
        self._message_handlers: List[Callable] = []
        self._receipt_handlers: List[Callable] = []
        self._offline_queue: Dict[str, List[Message]] = {}  # user_id -> messages
        self._sequence_numbers: Dict[str, int] = {}  # conversation_id -> sequence
        self._running = False

    async def start(self):
        """Initialize the message broker."""
        if self._running:
            return

        try:
            self._redis = redis.from_url(self.redis_url, decode_responses=True)
            await self._redis.ping()
            logger.info("MessageBroker connected to Redis")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}. Using local storage.")
            self._redis = None

        self._running = True
        logger.info("MessageBroker started")

    async def stop(self):
        """Stop the message broker."""
        self._running = False
        if self._redis:
            await self._redis.close()
        logger.info("MessageBroker stopped")

    def _message_key(self, message_id: str) -> str:
        return f"message:{message_id}"

    def _conversation_key(self, conversation_id: str) -> str:
        return f"conversation:{conversation_id}:messages"

    def _offline_key(self, user_id: str) -> str:
        return f"offline:{user_id}"

    def _sequence_key(self, conversation_id: str) -> str:
        return f"sequence:{conversation_id}"

    async def _get_next_sequence(self, conversation_id: str) -> int:
        """Get next sequence number for a conversation."""
        if self._redis:
            try:
                return await self._redis.incr(self._sequence_key(conversation_id))
            except Exception as e:
                logger.error(f"Redis error getting sequence: {e}")

        # Local fallback
        if conversation_id not in self._sequence_numbers:
            self._sequence_numbers[conversation_id] = 0
        self._sequence_numbers[conversation_id] += 1
        return self._sequence_numbers[conversation_id]

    async def send_message(
        self,
        conversation_id: str,
        sender_id: str,
        tenant_id: str,
        content: Dict[str, Any],
        content_type: str = "text",
        priority: MessagePriority = MessagePriority.NORMAL,
        reply_to: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Message:
        """
        Send a message to a conversation.

        Args:
            conversation_id: Target conversation
            sender_id: Sender user ID
            tenant_id: Tenant ID
            content: Message content
            content_type: Type of content
            priority: Message priority
            reply_to: Message ID being replied to
            attachments: File attachments
            metadata: Additional metadata

        Returns:
            The created Message
        """
        message = Message(
            message_id=str(uuid4()),
            conversation_id=conversation_id,
            sender_id=sender_id,
            tenant_id=tenant_id,
            content=content,
            content_type=content_type,
            priority=priority,
            reply_to=reply_to,
            attachments=attachments or [],
            metadata=metadata or {},
        )

        # Get sequence number
        sequence = await self._get_next_sequence(conversation_id)
        message.metadata["sequence"] = sequence

        # Store message
        if self._redis:
            try:
                # Store message data
                await self._redis.setex(
                    self._message_key(message.message_id),
                    self.message_ttl,
                    json.dumps(message.to_dict()),
                )
                # Add to conversation timeline
                await self._redis.zadd(
                    self._conversation_key(conversation_id),
                    {message.message_id: sequence},
                )
            except Exception as e:
                logger.error(f"Redis error storing message: {e}")

        message.status = MessageStatus.SENT
        message.sent_at = datetime.now(timezone.utc)

        # Notify handlers
        for handler in self._message_handlers:
            try:
                await handler(message)
            except Exception as e:
                logger.error(f"Message handler error: {e}")

        logger.debug(f"Message sent: {message.message_id}")
        return message

    async def get_message(self, message_id: str) -> Optional[Message]:
        """Get a message by ID."""
        if self._redis:
            try:
                data = await self._redis.get(self._message_key(message_id))
                if data:
                    return Message.from_dict(json.loads(data))
            except Exception as e:
                logger.error(f"Redis error getting message: {e}")
        return None

    async def get_conversation_messages(
        self,
        conversation_id: str,
        limit: int = 50,
        before_sequence: Optional[int] = None,
    ) -> List[Message]:
        """
        Get messages from a conversation.

        Args:
            conversation_id: Conversation to fetch
            limit: Maximum messages to return
            before_sequence: Get messages before this sequence

        Returns:
            List of messages ordered by sequence
        """
        messages = []

        if self._redis:
            try:
                # Get message IDs from sorted set
                if before_sequence:
                    message_ids = await self._redis.zrangebyscore(
                        self._conversation_key(conversation_id),
                        "-inf",
                        before_sequence - 1,
                        start=0,
                        num=limit,
                        withscores=False,
                    )
                else:
                    message_ids = await self._redis.zrange(
                        self._conversation_key(conversation_id),
                        -limit,
                        -1,
                    )

                # Fetch message data
                for message_id in message_ids:
                    message = await self.get_message(message_id)
                    if message:
                        messages.append(message)
            except Exception as e:
                logger.error(f"Redis error getting conversation messages: {e}")

        return sorted(messages, key=lambda m: m.metadata.get("sequence", 0))

    async def mark_delivered(self, message_id: str, user_id: str) -> Optional[DeliveryReceipt]:
        """
        Mark a message as delivered.

        Args:
            message_id: Message ID
            user_id: User who received the message

        Returns:
            DeliveryReceipt
        """
        message = await self.get_message(message_id)
        if not message:
            return None

        if message.status not in [MessageStatus.SENT, MessageStatus.PENDING]:
            return None

        message.status = MessageStatus.DELIVERED
        message.delivered_at = datetime.now(timezone.utc)

        # Update stored message
        if self._redis:
            try:
                await self._redis.setex(
                    self._message_key(message_id),
                    self.message_ttl,
                    json.dumps(message.to_dict()),
                )
            except Exception as e:
                logger.error(f"Redis error updating delivery status: {e}")

        receipt = DeliveryReceipt(
            message_id=message_id,
            user_id=user_id,
            status=MessageStatus.DELIVERED,
        )

        # Notify receipt handlers
        for handler in self._receipt_handlers:
            try:
                await handler(receipt)
            except Exception as e:
                logger.error(f"Receipt handler error: {e}")

        logger.debug(f"Message {message_id} marked delivered")
        return receipt

    async def mark_read(self, message_id: str, user_id: str) -> Optional[DeliveryReceipt]:
        """
        Mark a message as read.

        Args:
            message_id: Message ID
            user_id: User who read the message

        Returns:
            DeliveryReceipt
        """
        message = await self.get_message(message_id)
        if not message:
            return None

        message.status = MessageStatus.READ
        message.read_at = datetime.now(timezone.utc)

        # Update stored message
        if self._redis:
            try:
                await self._redis.setex(
                    self._message_key(message_id),
                    self.message_ttl,
                    json.dumps(message.to_dict()),
                )
            except Exception as e:
                logger.error(f"Redis error updating read status: {e}")

        receipt = DeliveryReceipt(
            message_id=message_id,
            user_id=user_id,
            status=MessageStatus.READ,
        )

        # Notify receipt handlers
        for handler in self._receipt_handlers:
            try:
                await handler(receipt)
            except Exception as e:
                logger.error(f"Receipt handler error: {e}")

        logger.debug(f"Message {message_id} marked read")
        return receipt

    async def queue_offline_message(self, user_id: str, message: Message):
        """
        Queue a message for an offline user.

        Args:
            user_id: Offline user ID
            message: Message to queue
        """
        if self._redis:
            try:
                await self._redis.lpush(
                    self._offline_key(user_id),
                    json.dumps(message.to_dict()),
                )
                await self._redis.ltrim(
                    self._offline_key(user_id),
                    0,
                    self.max_offline_messages - 1,
                )
            except Exception as e:
                logger.error(f"Redis error queuing offline message: {e}")
                if user_id not in self._offline_queue:
                    self._offline_queue[user_id] = []
                self._offline_queue[user_id].insert(0, message)
                self._offline_queue[user_id] = self._offline_queue[user_id][:self.max_offline_messages]
        else:
            if user_id not in self._offline_queue:
                self._offline_queue[user_id] = []
            self._offline_queue[user_id].insert(0, message)
            self._offline_queue[user_id] = self._offline_queue[user_id][:self.max_offline_messages]

        logger.debug(f"Queued offline message for {user_id}")

    async def get_offline_messages(self, user_id: str, clear: bool = True) -> List[Message]:
        """
        Get queued messages for a user.

        Args:
            user_id: User ID
            clear: Whether to clear the queue after retrieval

        Returns:
            List of queued messages
        """
        messages = []

        if self._redis:
            try:
                data_list = await self._redis.lrange(
                    self._offline_key(user_id),
                    0,
                    -1,
                )
                for data in data_list:
                    messages.append(Message.from_dict(json.loads(data)))

                if clear:
                    await self._redis.delete(self._offline_key(user_id))
            except Exception as e:
                logger.error(f"Redis error getting offline messages: {e}")

        # Also check local queue
        if user_id in self._offline_queue:
            messages.extend(self._offline_queue[user_id])
            if clear:
                del self._offline_queue[user_id]

        return messages

    def on_message(self, handler: Callable):
        """Register a message handler."""
        self._message_handlers.append(handler)

    def on_receipt(self, handler: Callable):
        """Register a delivery receipt handler."""
        self._receipt_handlers.append(handler)


# Global message broker instance
message_broker = MessageBroker()
