"""
WebSocket Router

FastAPI WebSocket router that integrates all real-time components:
- Connection management
- Presence tracking
- Message delivery
- Room management
- Notifications

EPIC-001: Real-Time Communication Infrastructure
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .connection_manager import (
    ConnectionManager,
    Connection,
    WebSocketMessage,
    MessageType,
    connection_manager,
)
from .presence_manager import (
    PresenceManager,
    PresenceStatus,
    ActivityType,
    presence_manager,
)
from .message_broker import MessageBroker, message_broker, MessagePriority
from .room_manager import RoomManager, room_manager, RoomType, RoomPermission
from .notification_service import NotificationService, notification_service, NotificationChannel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket"])


class WebSocketAuth:
    """WebSocket authentication helper."""

    @staticmethod
    async def validate_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Validate JWT token and return user info.
        Override this method with your authentication logic.
        """
        # Placeholder - integrate with your auth system
        # This should decode the JWT and return user info
        try:
            # Example structure - replace with real JWT validation
            return {
                "user_id": "user123",
                "tenant_id": "tenant456",
                "roles": ["user"],
            }
        except Exception:
            return None


async def get_websocket_user(
    websocket: WebSocket,
    token: str = Query(..., description="JWT authentication token"),
) -> Dict[str, Any]:
    """Dependency to authenticate WebSocket connections."""
    user_info = await WebSocketAuth.validate_token(token)
    if not user_info:
        await websocket.close(code=4001, reason="Invalid authentication token")
        raise HTTPException(status_code=401, detail="Invalid token")
    return user_info


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(None, description="JWT authentication token"),
):
    """
    Main WebSocket endpoint for real-time communication.

    Query Parameters:
        token: JWT authentication token

    Message Types:
        - auth: Authenticate the connection
        - ping: Keep-alive ping
        - join_room: Join a room
        - leave_room: Leave a room
        - message: Send a message
        - typing_start: Start typing indicator
        - typing_stop: Stop typing indicator
        - presence_update: Update presence status
        - subscribe: Subscribe to events
        - unsubscribe: Unsubscribe from events
    """
    connection = None

    try:
        # Accept connection (auth happens via message)
        connection = await connection_manager.connect(websocket)
        logger.info(f"WebSocket connected: {connection.connection_id}")

        # Handle authentication if token provided
        if token:
            user_info = await WebSocketAuth.validate_token(token)
            if user_info:
                await connection_manager.authenticate(
                    connection.connection_id,
                    user_id=user_info["user_id"],
                    tenant_id=user_info["tenant_id"],
                    metadata={"roles": user_info.get("roles", [])},
                )

                # Update presence
                await presence_manager.update_presence(
                    user_id=user_info["user_id"],
                    tenant_id=user_info["tenant_id"],
                    status=PresenceStatus.ONLINE,
                    activity=ActivityType.ACTIVE,
                    device_id=connection.connection_id,
                )

        # Main message loop
        while True:
            try:
                raw_message = await websocket.receive_text()
                await handle_websocket_message(connection, raw_message)
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: {connection.connection_id}")
                break

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if connection:
            # Update presence to offline
            if connection.user_id:
                await presence_manager.set_offline(
                    connection.user_id,
                    device_id=connection.connection_id,
                )

            # Disconnect
            await connection_manager.disconnect(
                connection.connection_id,
                reason="Connection closed",
            )


async def handle_websocket_message(connection: Connection, raw_message: str):
    """Handle incoming WebSocket messages."""
    try:
        message = WebSocketMessage.from_json(raw_message)

        if message.type == MessageType.AUTH:
            await handle_auth(connection, message)
        elif message.type == MessageType.PING:
            await handle_ping(connection, message)
        elif message.type == MessageType.PRESENCE_UPDATE:
            await handle_presence_update(connection, message)
        elif message.type == MessageType.TYPING_START:
            await handle_typing_start(connection, message)
        elif message.type == MessageType.TYPING_STOP:
            await handle_typing_stop(connection, message)
        elif message.type == MessageType.MESSAGE:
            await handle_message(connection, message)
        elif message.type == MessageType.JOIN_ROOM:
            await handle_join_room(connection, message)
        elif message.type == MessageType.LEAVE_ROOM:
            await handle_leave_room(connection, message)
        elif message.type == MessageType.SUBSCRIBE:
            await handle_subscribe(connection, message)
        elif message.type == MessageType.UNSUBSCRIBE:
            await handle_unsubscribe(connection, message)
        else:
            # Pass to connection manager for default handling
            await connection_manager.handle_message(connection.connection_id, raw_message)

    except json.JSONDecodeError as e:
        logger.warning(f"Invalid message format: {e}")
        await send_error(connection, "Invalid message format", message_id=None)
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await send_error(connection, str(e), message_id=None)


async def handle_auth(connection: Connection, message: WebSocketMessage):
    """Handle authentication message."""
    token = message.payload.get("token")
    if not token:
        await send_error(connection, "Token required", message.message_id)
        return

    user_info = await WebSocketAuth.validate_token(token)
    if not user_info:
        await connection_manager.send_to_connection(
            connection.connection_id,
            WebSocketMessage(
                type=MessageType.AUTH_FAILURE,
                payload={"error": "Invalid token"},
                correlation_id=message.message_id,
            )
        )
        return

    # Authenticate connection
    await connection_manager.authenticate(
        connection.connection_id,
        user_id=user_info["user_id"],
        tenant_id=user_info["tenant_id"],
        metadata={"roles": user_info.get("roles", [])},
    )

    # Update presence
    await presence_manager.update_presence(
        user_id=user_info["user_id"],
        tenant_id=user_info["tenant_id"],
        status=PresenceStatus.ONLINE,
        activity=ActivityType.ACTIVE,
        device_id=connection.connection_id,
    )


async def handle_ping(connection: Connection, message: WebSocketMessage):
    """Handle ping message."""
    # Update presence heartbeat
    if connection.user_id:
        await presence_manager.heartbeat(connection.user_id, connection.connection_id)

    await connection_manager.send_to_connection(
        connection.connection_id,
        WebSocketMessage(
            type=MessageType.PONG,
            payload={},
            correlation_id=message.message_id,
        )
    )


async def handle_presence_update(connection: Connection, message: WebSocketMessage):
    """Handle presence update message."""
    if not connection.user_id or not connection.tenant_id:
        await send_error(connection, "Authentication required", message.message_id)
        return

    status = message.payload.get("status")
    status_message = message.payload.get("statusMessage")
    activity = message.payload.get("activity")

    await presence_manager.update_presence(
        user_id=connection.user_id,
        tenant_id=connection.tenant_id,
        status=PresenceStatus(status) if status else None,
        status_message=status_message,
        activity=ActivityType(activity) if activity else None,
    )

    await send_ack(connection, "presence_update", message.message_id)


async def handle_typing_start(connection: Connection, message: WebSocketMessage):
    """Handle typing start message."""
    if not connection.user_id:
        await send_error(connection, "Authentication required", message.message_id)
        return

    conversation_id = message.payload.get("conversationId")
    if not conversation_id:
        await send_error(connection, "conversationId required", message.message_id)
        return

    await presence_manager.start_typing(connection.user_id, conversation_id)

    # Broadcast typing indicator to room
    await connection_manager.send_to_room(
        conversation_id,
        WebSocketMessage(
            type=MessageType.TYPING_START,
            payload={
                "userId": connection.user_id,
                "conversationId": conversation_id,
            }
        ),
        exclude_connection=connection.connection_id,
    )


async def handle_typing_stop(connection: Connection, message: WebSocketMessage):
    """Handle typing stop message."""
    if not connection.user_id:
        return

    conversation_id = message.payload.get("conversationId")
    if not conversation_id:
        return

    await presence_manager.stop_typing(connection.user_id, conversation_id)

    # Broadcast typing stop to room
    await connection_manager.send_to_room(
        conversation_id,
        WebSocketMessage(
            type=MessageType.TYPING_STOP,
            payload={
                "userId": connection.user_id,
                "conversationId": conversation_id,
            }
        ),
        exclude_connection=connection.connection_id,
    )


async def handle_message(connection: Connection, message: WebSocketMessage):
    """Handle chat message."""
    if not connection.user_id or not connection.tenant_id:
        await send_error(connection, "Authentication required", message.message_id)
        return

    conversation_id = message.payload.get("conversationId")
    content = message.payload.get("content")

    if not conversation_id or not content:
        await send_error(connection, "conversationId and content required", message.message_id)
        return

    # Check room permission
    has_permission = await room_manager.check_permission(
        conversation_id,
        connection.user_id,
        RoomPermission.WRITE,
    )
    if not has_permission:
        await send_error(connection, "Permission denied", message.message_id)
        return

    # Send message via broker
    sent_message = await message_broker.send_message(
        conversation_id=conversation_id,
        sender_id=connection.user_id,
        tenant_id=connection.tenant_id,
        content=content,
        content_type=message.payload.get("contentType", "text"),
        priority=MessagePriority(message.payload.get("priority", "normal")),
        reply_to=message.payload.get("replyTo"),
        attachments=message.payload.get("attachments"),
        metadata=message.payload.get("metadata"),
    )

    # Send acknowledgment to sender
    await connection_manager.send_to_connection(
        connection.connection_id,
        WebSocketMessage(
            type=MessageType.ACK,
            payload={
                "action": "message",
                "messageId": sent_message.message_id,
            },
            correlation_id=message.message_id,
        )
    )

    # Broadcast message to room
    await connection_manager.send_to_room(
        conversation_id,
        WebSocketMessage(
            type=MessageType.MESSAGE,
            payload=sent_message.to_dict(),
        ),
        exclude_connection=connection.connection_id,
    )

    # Stop typing indicator
    await presence_manager.stop_typing(connection.user_id, conversation_id)


async def handle_join_room(connection: Connection, message: WebSocketMessage):
    """Handle room join message."""
    if not connection.user_id:
        await send_error(connection, "Authentication required", message.message_id)
        return

    room_id = message.payload.get("roomId")
    if not room_id:
        await send_error(connection, "roomId required", message.message_id)
        return

    # Check room exists and user has access
    room = await room_manager.get_room(room_id)
    if not room:
        await send_error(connection, "Room not found", message.message_id)
        return

    if connection.user_id not in room.members:
        await send_error(connection, "Not a member of this room", message.message_id)
        return

    # Join room for WebSocket messages
    await connection_manager.join_room(connection.connection_id, room_id)

    # Send room info
    await connection_manager.send_to_connection(
        connection.connection_id,
        WebSocketMessage(
            type=MessageType.ROOM_UPDATE,
            payload={
                "action": "joined",
                "room": room.to_dict(),
            },
            correlation_id=message.message_id,
        )
    )

    # Notify other room members
    await connection_manager.send_to_room(
        room_id,
        WebSocketMessage(
            type=MessageType.ROOM_UPDATE,
            payload={
                "action": "member_joined",
                "roomId": room_id,
                "userId": connection.user_id,
            }
        ),
        exclude_connection=connection.connection_id,
    )


async def handle_leave_room(connection: Connection, message: WebSocketMessage):
    """Handle room leave message."""
    room_id = message.payload.get("roomId")
    if not room_id:
        await send_error(connection, "roomId required", message.message_id)
        return

    # Notify room before leaving
    if connection.user_id:
        await connection_manager.send_to_room(
            room_id,
            WebSocketMessage(
                type=MessageType.ROOM_UPDATE,
                payload={
                    "action": "member_left",
                    "roomId": room_id,
                    "userId": connection.user_id,
                }
            ),
            exclude_connection=connection.connection_id,
        )

    await connection_manager.leave_room(connection.connection_id, room_id)
    await send_ack(connection, "leave_room", message.message_id)


async def handle_subscribe(connection: Connection, message: WebSocketMessage):
    """Handle event subscription message."""
    topic = message.payload.get("topic")
    if not topic:
        await send_error(connection, "topic required", message.message_id)
        return

    await connection_manager.subscribe(connection.connection_id, topic)
    await send_ack(connection, "subscribe", message.message_id, {"topic": topic})


async def handle_unsubscribe(connection: Connection, message: WebSocketMessage):
    """Handle event unsubscription message."""
    topic = message.payload.get("topic")
    if not topic:
        await send_error(connection, "topic required", message.message_id)
        return

    await connection_manager.unsubscribe(connection.connection_id, topic)
    await send_ack(connection, "unsubscribe", message.message_id, {"topic": topic})


async def send_ack(
    connection: Connection,
    action: str,
    correlation_id: str,
    extra: Optional[Dict[str, Any]] = None,
):
    """Send acknowledgment message."""
    payload = {"action": action, **(extra or {})}
    await connection_manager.send_to_connection(
        connection.connection_id,
        WebSocketMessage(
            type=MessageType.ACK,
            payload=payload,
            correlation_id=correlation_id,
        )
    )


async def send_error(
    connection: Connection,
    error: str,
    correlation_id: Optional[str],
):
    """Send error message."""
    await connection_manager.send_to_connection(
        connection.connection_id,
        WebSocketMessage(
            type=MessageType.ERROR,
            payload={"error": error},
            correlation_id=correlation_id,
        )
    )


# REST endpoints for presence and notifications
@router.get("/presence/{user_id}")
async def get_user_presence(user_id: str):
    """Get presence status for a user."""
    presence = await presence_manager.get_presence(user_id)
    if not presence:
        raise HTTPException(status_code=404, detail="User not found")
    return presence.to_dict()


@router.get("/presence/tenant/{tenant_id}")
async def get_tenant_presence(tenant_id: str):
    """Get presence for all users in a tenant."""
    presences = await presence_manager.get_tenant_presence(tenant_id)
    return [p.to_dict() for p in presences]


@router.get("/rooms/{user_id}")
async def get_user_rooms(user_id: str):
    """Get all rooms for a user."""
    rooms = await room_manager.get_user_rooms(user_id)
    return [r.to_dict() for r in rooms]


@router.get("/stats")
async def get_realtime_stats():
    """Get real-time communication statistics."""
    return {
        "connections": connection_manager.get_metrics(),
        "presence": presence_manager.get_stats(),
    }


# Initialize services on startup
async def startup_realtime():
    """Initialize real-time services."""
    await connection_manager.start()
    await presence_manager.start()
    await message_broker.start()
    await room_manager.start()
    await notification_service.start()

    # Register notification delivery handler for WebSocket channel
    notification_service.register_delivery_handler(
        NotificationChannel.WEBSOCKET,
        deliver_notification_websocket,
    )

    logger.info("Real-time services started")


async def shutdown_realtime():
    """Shutdown real-time services."""
    await notification_service.stop()
    await room_manager.stop()
    await message_broker.stop()
    await presence_manager.stop()
    await connection_manager.stop()

    logger.info("Real-time services stopped")


async def deliver_notification_websocket(notification):
    """Deliver notification via WebSocket."""
    await connection_manager.send_to_user(
        notification.recipient_id,
        WebSocketMessage(
            type=MessageType.NOTIFICATION,
            payload=notification.to_dict(),
        )
    )
