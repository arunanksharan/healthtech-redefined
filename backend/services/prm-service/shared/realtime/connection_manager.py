"""
WebSocket Connection Manager

Manages WebSocket connections with support for:
- Connection pooling per tenant
- User session management
- Heartbeat/ping-pong mechanism
- Graceful shutdown handling
- Multi-device support

EPIC-001: US-001.1 WebSocket Server Infrastructure
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import logging

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ConnectionState(str, Enum):
    """Connection lifecycle states."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"


class MessageType(str, Enum):
    """WebSocket message types."""
    # System messages
    PING = "ping"
    PONG = "pong"
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    ERROR = "error"
    ACK = "ack"

    # Authentication
    AUTH = "auth"
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"

    # Presence
    PRESENCE_UPDATE = "presence_update"
    TYPING_START = "typing_start"
    TYPING_STOP = "typing_stop"

    # Messaging
    MESSAGE = "message"
    MESSAGE_DELIVERED = "message_delivered"
    MESSAGE_READ = "message_read"

    # Rooms
    JOIN_ROOM = "join_room"
    LEAVE_ROOM = "leave_room"
    ROOM_UPDATE = "room_update"

    # Notifications
    NOTIFICATION = "notification"

    # Events
    EVENT = "event"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"


@dataclass
class WebSocketMessage:
    """Structured WebSocket message."""
    type: MessageType
    payload: Dict[str, Any]
    message_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps({
            "type": self.type.value,
            "payload": self.payload,
            "messageId": self.message_id,
            "timestamp": self.timestamp.isoformat(),
            "correlationId": self.correlation_id,
        })

    @classmethod
    def from_json(cls, data: str) -> "WebSocketMessage":
        parsed = json.loads(data)
        return cls(
            type=MessageType(parsed.get("type", "message")),
            payload=parsed.get("payload", {}),
            message_id=parsed.get("messageId", str(uuid4())),
            timestamp=datetime.fromisoformat(parsed["timestamp"]) if "timestamp" in parsed else datetime.now(timezone.utc),
            correlation_id=parsed.get("correlationId"),
        )


@dataclass
class Connection:
    """Represents a single WebSocket connection."""
    connection_id: str
    websocket: WebSocket
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    device_id: Optional[str] = None
    state: ConnectionState = ConnectionState.CONNECTING
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    rooms: Set[str] = field(default_factory=set)
    subscriptions: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConnectionManager:
    """
    Manages WebSocket connections for real-time communication.

    Features:
    - Multi-tenant connection isolation
    - User session management across devices
    - Heartbeat monitoring
    - Room-based messaging
    - Event subscriptions
    - Graceful connection handling
    """

    def __init__(
        self,
        heartbeat_interval: int = 30,
        heartbeat_timeout: int = 60,
        max_connections_per_user: int = 5,
        max_connections_per_tenant: int = 10000,
    ):
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_timeout = heartbeat_timeout
        self.max_connections_per_user = max_connections_per_user
        self.max_connections_per_tenant = max_connections_per_tenant

        # Connection storage
        self._connections: Dict[str, Connection] = {}
        self._user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self._tenant_connections: Dict[str, Set[str]] = {}  # tenant_id -> connection_ids
        self._room_connections: Dict[str, Set[str]] = {}  # room_id -> connection_ids

        # Event handlers
        self._message_handlers: Dict[MessageType, List[Callable]] = {}

        # Background tasks
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._running = False

        # Metrics
        self._metrics = {
            "total_connections": 0,
            "total_messages_sent": 0,
            "total_messages_received": 0,
            "errors": 0,
        }

    async def start(self):
        """Start the connection manager and background tasks."""
        if self._running:
            return

        self._running = True
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info("ConnectionManager started")

    async def stop(self):
        """Stop the connection manager and close all connections."""
        self._running = False

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        # Close all connections gracefully
        for connection_id in list(self._connections.keys()):
            await self.disconnect(connection_id, reason="Server shutdown")

        logger.info("ConnectionManager stopped")

    async def connect(
        self,
        websocket: WebSocket,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        device_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Connection:
        """
        Accept a new WebSocket connection.

        Args:
            websocket: The WebSocket connection
            user_id: User identifier (can be set later after auth)
            tenant_id: Tenant identifier for isolation
            device_id: Device identifier for multi-device support
            metadata: Additional connection metadata

        Returns:
            Connection object representing this connection
        """
        # Check tenant connection limit
        if tenant_id and tenant_id in self._tenant_connections:
            if len(self._tenant_connections[tenant_id]) >= self.max_connections_per_tenant:
                await websocket.close(code=1008, reason="Tenant connection limit reached")
                raise ConnectionError("Tenant connection limit reached")

        # Check user connection limit
        if user_id and user_id in self._user_connections:
            if len(self._user_connections[user_id]) >= self.max_connections_per_user:
                # Close oldest connection for this user
                oldest_conn_id = min(
                    self._user_connections[user_id],
                    key=lambda cid: self._connections[cid].connected_at
                )
                await self.disconnect(oldest_conn_id, reason="Max connections exceeded")

        await websocket.accept()

        connection_id = str(uuid4())
        connection = Connection(
            connection_id=connection_id,
            websocket=websocket,
            user_id=user_id,
            tenant_id=tenant_id,
            device_id=device_id,
            state=ConnectionState.CONNECTED,
            metadata=metadata or {},
        )

        self._connections[connection_id] = connection

        if user_id:
            if user_id not in self._user_connections:
                self._user_connections[user_id] = set()
            self._user_connections[user_id].add(connection_id)

        if tenant_id:
            if tenant_id not in self._tenant_connections:
                self._tenant_connections[tenant_id] = set()
            self._tenant_connections[tenant_id].add(connection_id)

        self._metrics["total_connections"] += 1

        logger.info(f"Connection established: {connection_id} (user={user_id}, tenant={tenant_id})")

        # Send connection acknowledgment
        await self.send_to_connection(
            connection_id,
            WebSocketMessage(
                type=MessageType.CONNECT,
                payload={
                    "connectionId": connection_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        )

        return connection

    async def authenticate(
        self,
        connection_id: str,
        user_id: str,
        tenant_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Authenticate a connection after initial connect.

        Args:
            connection_id: The connection to authenticate
            user_id: User identifier
            tenant_id: Tenant identifier
            metadata: Additional user metadata

        Returns:
            True if authentication successful
        """
        connection = self._connections.get(connection_id)
        if not connection:
            return False

        # Update connection with auth info
        if connection.user_id and connection.user_id in self._user_connections:
            self._user_connections[connection.user_id].discard(connection_id)

        if connection.tenant_id and connection.tenant_id in self._tenant_connections:
            self._tenant_connections[connection.tenant_id].discard(connection_id)

        connection.user_id = user_id
        connection.tenant_id = tenant_id
        connection.state = ConnectionState.AUTHENTICATED

        if metadata:
            connection.metadata.update(metadata)

        if user_id not in self._user_connections:
            self._user_connections[user_id] = set()
        self._user_connections[user_id].add(connection_id)

        if tenant_id not in self._tenant_connections:
            self._tenant_connections[tenant_id] = set()
        self._tenant_connections[tenant_id].add(connection_id)

        logger.info(f"Connection authenticated: {connection_id} (user={user_id})")

        await self.send_to_connection(
            connection_id,
            WebSocketMessage(
                type=MessageType.AUTH_SUCCESS,
                payload={
                    "userId": user_id,
                    "tenantId": tenant_id,
                }
            )
        )

        return True

    async def disconnect(self, connection_id: str, reason: str = ""):
        """
        Disconnect a WebSocket connection.

        Args:
            connection_id: The connection to disconnect
            reason: Reason for disconnection
        """
        connection = self._connections.get(connection_id)
        if not connection:
            return

        connection.state = ConnectionState.DISCONNECTING

        # Remove from user connections
        if connection.user_id and connection.user_id in self._user_connections:
            self._user_connections[connection.user_id].discard(connection_id)
            if not self._user_connections[connection.user_id]:
                del self._user_connections[connection.user_id]

        # Remove from tenant connections
        if connection.tenant_id and connection.tenant_id in self._tenant_connections:
            self._tenant_connections[connection.tenant_id].discard(connection_id)
            if not self._tenant_connections[connection.tenant_id]:
                del self._tenant_connections[connection.tenant_id]

        # Remove from rooms
        for room_id in list(connection.rooms):
            await self.leave_room(connection_id, room_id)

        # Remove from subscriptions
        connection.subscriptions.clear()

        # Close WebSocket
        try:
            await connection.websocket.close(code=1000, reason=reason)
        except Exception as e:
            logger.warning(f"Error closing WebSocket: {e}")

        # Remove connection
        del self._connections[connection_id]

        logger.info(f"Connection closed: {connection_id} (reason={reason})")

    async def send_to_connection(self, connection_id: str, message: WebSocketMessage) -> bool:
        """
        Send a message to a specific connection.

        Args:
            connection_id: Target connection
            message: Message to send

        Returns:
            True if sent successfully
        """
        connection = self._connections.get(connection_id)
        if not connection or connection.state == ConnectionState.DISCONNECTING:
            return False

        try:
            await connection.websocket.send_text(message.to_json())
            self._metrics["total_messages_sent"] += 1
            return True
        except Exception as e:
            logger.error(f"Error sending to connection {connection_id}: {e}")
            self._metrics["errors"] += 1
            await self.disconnect(connection_id, reason="Send error")
            return False

    async def send_to_user(self, user_id: str, message: WebSocketMessage) -> int:
        """
        Send a message to all connections for a user.

        Args:
            user_id: Target user
            message: Message to send

        Returns:
            Number of connections that received the message
        """
        connection_ids = self._user_connections.get(user_id, set())
        sent = 0

        for connection_id in list(connection_ids):
            if await self.send_to_connection(connection_id, message):
                sent += 1

        return sent

    async def send_to_tenant(
        self,
        tenant_id: str,
        message: WebSocketMessage,
        exclude_user: Optional[str] = None,
    ) -> int:
        """
        Broadcast a message to all connections in a tenant.

        Args:
            tenant_id: Target tenant
            message: Message to send
            exclude_user: User to exclude from broadcast

        Returns:
            Number of connections that received the message
        """
        connection_ids = self._tenant_connections.get(tenant_id, set())
        sent = 0

        for connection_id in list(connection_ids):
            connection = self._connections.get(connection_id)
            if connection and connection.user_id != exclude_user:
                if await self.send_to_connection(connection_id, message):
                    sent += 1

        return sent

    async def join_room(self, connection_id: str, room_id: str) -> bool:
        """
        Add a connection to a room.

        Args:
            connection_id: Connection to add
            room_id: Room to join

        Returns:
            True if joined successfully
        """
        connection = self._connections.get(connection_id)
        if not connection:
            return False

        connection.rooms.add(room_id)

        if room_id not in self._room_connections:
            self._room_connections[room_id] = set()
        self._room_connections[room_id].add(connection_id)

        logger.debug(f"Connection {connection_id} joined room {room_id}")
        return True

    async def leave_room(self, connection_id: str, room_id: str) -> bool:
        """
        Remove a connection from a room.

        Args:
            connection_id: Connection to remove
            room_id: Room to leave

        Returns:
            True if left successfully
        """
        connection = self._connections.get(connection_id)
        if not connection:
            return False

        connection.rooms.discard(room_id)

        if room_id in self._room_connections:
            self._room_connections[room_id].discard(connection_id)
            if not self._room_connections[room_id]:
                del self._room_connections[room_id]

        logger.debug(f"Connection {connection_id} left room {room_id}")
        return True

    async def send_to_room(
        self,
        room_id: str,
        message: WebSocketMessage,
        exclude_connection: Optional[str] = None,
    ) -> int:
        """
        Send a message to all connections in a room.

        Args:
            room_id: Target room
            message: Message to send
            exclude_connection: Connection to exclude

        Returns:
            Number of connections that received the message
        """
        connection_ids = self._room_connections.get(room_id, set())
        sent = 0

        for connection_id in list(connection_ids):
            if connection_id != exclude_connection:
                if await self.send_to_connection(connection_id, message):
                    sent += 1

        return sent

    async def subscribe(self, connection_id: str, topic: str) -> bool:
        """
        Subscribe a connection to an event topic.

        Args:
            connection_id: Connection to subscribe
            topic: Event topic pattern

        Returns:
            True if subscribed successfully
        """
        connection = self._connections.get(connection_id)
        if not connection:
            return False

        connection.subscriptions.add(topic)
        logger.debug(f"Connection {connection_id} subscribed to {topic}")
        return True

    async def unsubscribe(self, connection_id: str, topic: str) -> bool:
        """
        Unsubscribe a connection from an event topic.

        Args:
            connection_id: Connection to unsubscribe
            topic: Event topic pattern

        Returns:
            True if unsubscribed successfully
        """
        connection = self._connections.get(connection_id)
        if not connection:
            return False

        connection.subscriptions.discard(topic)
        logger.debug(f"Connection {connection_id} unsubscribed from {topic}")
        return True

    async def broadcast_event(
        self,
        tenant_id: str,
        topic: str,
        payload: Dict[str, Any],
    ) -> int:
        """
        Broadcast an event to subscribed connections.

        Args:
            tenant_id: Tenant scope
            topic: Event topic
            payload: Event data

        Returns:
            Number of connections that received the event
        """
        message = WebSocketMessage(
            type=MessageType.EVENT,
            payload={"topic": topic, "data": payload},
        )

        connection_ids = self._tenant_connections.get(tenant_id, set())
        sent = 0

        for connection_id in list(connection_ids):
            connection = self._connections.get(connection_id)
            if connection and self._matches_subscription(topic, connection.subscriptions):
                if await self.send_to_connection(connection_id, message):
                    sent += 1

        return sent

    def _matches_subscription(self, topic: str, subscriptions: Set[str]) -> bool:
        """Check if a topic matches any subscription pattern."""
        for pattern in subscriptions:
            if pattern == "*" or pattern == topic:
                return True
            if pattern.endswith("*") and topic.startswith(pattern[:-1]):
                return True
        return False

    async def handle_message(self, connection_id: str, raw_message: str):
        """
        Handle an incoming WebSocket message.

        Args:
            connection_id: Source connection
            raw_message: Raw message data
        """
        connection = self._connections.get(connection_id)
        if not connection:
            return

        try:
            message = WebSocketMessage.from_json(raw_message)
            self._metrics["total_messages_received"] += 1

            # Handle ping/pong
            if message.type == MessageType.PING:
                connection.last_heartbeat = datetime.now(timezone.utc)
                await self.send_to_connection(
                    connection_id,
                    WebSocketMessage(
                        type=MessageType.PONG,
                        payload={},
                        correlation_id=message.message_id,
                    )
                )
                return

            # Handle authentication
            if message.type == MessageType.AUTH:
                # Auth should be handled by the application layer
                pass

            # Handle room operations
            if message.type == MessageType.JOIN_ROOM:
                room_id = message.payload.get("roomId")
                if room_id:
                    await self.join_room(connection_id, room_id)
                    await self.send_to_connection(
                        connection_id,
                        WebSocketMessage(
                            type=MessageType.ACK,
                            payload={"action": "join_room", "roomId": room_id},
                            correlation_id=message.message_id,
                        )
                    )
                return

            if message.type == MessageType.LEAVE_ROOM:
                room_id = message.payload.get("roomId")
                if room_id:
                    await self.leave_room(connection_id, room_id)
                    await self.send_to_connection(
                        connection_id,
                        WebSocketMessage(
                            type=MessageType.ACK,
                            payload={"action": "leave_room", "roomId": room_id},
                            correlation_id=message.message_id,
                        )
                    )
                return

            # Handle subscriptions
            if message.type == MessageType.SUBSCRIBE:
                topic = message.payload.get("topic")
                if topic:
                    await self.subscribe(connection_id, topic)
                    await self.send_to_connection(
                        connection_id,
                        WebSocketMessage(
                            type=MessageType.ACK,
                            payload={"action": "subscribe", "topic": topic},
                            correlation_id=message.message_id,
                        )
                    )
                return

            if message.type == MessageType.UNSUBSCRIBE:
                topic = message.payload.get("topic")
                if topic:
                    await self.unsubscribe(connection_id, topic)
                    await self.send_to_connection(
                        connection_id,
                        WebSocketMessage(
                            type=MessageType.ACK,
                            payload={"action": "unsubscribe", "topic": topic},
                            correlation_id=message.message_id,
                        )
                    )
                return

            # Call registered handlers
            if message.type in self._message_handlers:
                for handler in self._message_handlers[message.type]:
                    try:
                        await handler(connection, message)
                    except Exception as e:
                        logger.error(f"Handler error: {e}")
                        self._metrics["errors"] += 1

        except json.JSONDecodeError as e:
            logger.warning(f"Invalid message format from {connection_id}: {e}")
            self._metrics["errors"] += 1
        except Exception as e:
            logger.error(f"Error handling message from {connection_id}: {e}")
            self._metrics["errors"] += 1

    def on_message(self, message_type: MessageType):
        """
        Decorator to register a message handler.

        Usage:
            @manager.on_message(MessageType.MESSAGE)
            async def handle_message(connection: Connection, message: WebSocketMessage):
                ...
        """
        def decorator(handler: Callable):
            if message_type not in self._message_handlers:
                self._message_handlers[message_type] = []
            self._message_handlers[message_type].append(handler)
            return handler
        return decorator

    async def _heartbeat_loop(self):
        """Background task to monitor connection health."""
        while self._running:
            try:
                await asyncio.sleep(self.heartbeat_interval)

                now = datetime.now(timezone.utc)
                stale_connections = []

                for connection_id, connection in self._connections.items():
                    if connection.state == ConnectionState.DISCONNECTING:
                        continue

                    elapsed = (now - connection.last_heartbeat).total_seconds()
                    if elapsed > self.heartbeat_timeout:
                        stale_connections.append(connection_id)
                    elif elapsed > self.heartbeat_interval:
                        # Send ping
                        await self.send_to_connection(
                            connection_id,
                            WebSocketMessage(type=MessageType.PING, payload={})
                        )

                # Disconnect stale connections
                for connection_id in stale_connections:
                    logger.warning(f"Disconnecting stale connection: {connection_id}")
                    await self.disconnect(connection_id, reason="Heartbeat timeout")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")

    def get_connection(self, connection_id: str) -> Optional[Connection]:
        """Get a connection by ID."""
        return self._connections.get(connection_id)

    def get_user_connections(self, user_id: str) -> List[Connection]:
        """Get all connections for a user."""
        connection_ids = self._user_connections.get(user_id, set())
        return [self._connections[cid] for cid in connection_ids if cid in self._connections]

    def get_tenant_connections(self, tenant_id: str) -> List[Connection]:
        """Get all connections for a tenant."""
        connection_ids = self._tenant_connections.get(tenant_id, set())
        return [self._connections[cid] for cid in connection_ids if cid in self._connections]

    def is_user_online(self, user_id: str) -> bool:
        """Check if a user has any active connections."""
        return user_id in self._user_connections and len(self._user_connections[user_id]) > 0

    def get_metrics(self) -> Dict[str, Any]:
        """Get connection manager metrics."""
        return {
            **self._metrics,
            "active_connections": len(self._connections),
            "active_users": len(self._user_connections),
            "active_tenants": len(self._tenant_connections),
            "active_rooms": len(self._room_connections),
        }


# Global connection manager instance
connection_manager = ConnectionManager()
