"""
Real-Time Communication Module

Comprehensive real-time communication infrastructure including:
- WebSocket server with authentication and reconnection
- Multi-tenant connection management with quotas
- Presence management (online/offline, typing indicators)
- Real-time messaging with delivery receipts
- Multi-channel notification framework
- Room/conversation management with permissions
- Event broadcasting with pub/sub
- Performance optimizations (batching, caching, rate limiting)

EPIC-001: Real-Time Communication Infrastructure
"""

# Connection Management
from .connection_manager import (
    ConnectionManager,
    Connection,
    ConnectionState,
    WebSocketMessage,
    MessageType,
    connection_manager,
)

# Presence Management
from .presence_manager import (
    PresenceManager,
    UserPresence,
    PresenceStatus,
    ActivityType,
    TypingIndicator,
    presence_manager,
)

# Message Broker
from .message_broker import (
    MessageBroker,
    Message,
    MessageStatus,
    MessagePriority,
    DeliveryReceipt,
    message_broker,
)

# Notification Service
from .notification_service import (
    NotificationService,
    Notification,
    NotificationChannel,
    NotificationPriority,
    NotificationType,
    NotificationPreferences,
    notification_service,
)

# Room Management
from .room_manager import (
    RoomManager,
    Room,
    RoomMember,
    RoomType,
    RoomPermission,
    RoomVisibility,
    room_manager,
)

# Event Bus
from .event_bus import (
    EventBus,
    Event,
    EventPriority,
    EventCategory,
    Subscription,
    EventHistoryQuery,
    event_handler,
    event_bus,
)

# Performance Optimization
from .performance import (
    MessageBatcher,
    BatchConfig,
    RateLimiter,
    RateLimitConfig,
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerState,
    ConnectionStateCache,
    RedisClusterAdapter,
    PerformanceMonitor,
    message_batcher,
    rate_limiter,
    performance_monitor,
    connection_cache,
)

# WebSocket Router
from .websocket_router import (
    router as websocket_router,
    startup_realtime,
    shutdown_realtime,
)

__all__ = [
    # Connection Manager
    "ConnectionManager",
    "Connection",
    "ConnectionState",
    "WebSocketMessage",
    "MessageType",
    "connection_manager",
    # Presence Manager
    "PresenceManager",
    "UserPresence",
    "PresenceStatus",
    "ActivityType",
    "TypingIndicator",
    "presence_manager",
    # Message Broker
    "MessageBroker",
    "Message",
    "MessageStatus",
    "MessagePriority",
    "DeliveryReceipt",
    "message_broker",
    # Notification Service
    "NotificationService",
    "Notification",
    "NotificationChannel",
    "NotificationPriority",
    "NotificationType",
    "NotificationPreferences",
    "notification_service",
    # Room Manager
    "RoomManager",
    "Room",
    "RoomMember",
    "RoomType",
    "RoomPermission",
    "RoomVisibility",
    "room_manager",
    # Event Bus
    "EventBus",
    "Event",
    "EventPriority",
    "EventCategory",
    "Subscription",
    "EventHistoryQuery",
    "event_handler",
    "event_bus",
    # Performance
    "MessageBatcher",
    "BatchConfig",
    "RateLimiter",
    "RateLimitConfig",
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerState",
    "ConnectionStateCache",
    "RedisClusterAdapter",
    "PerformanceMonitor",
    "message_batcher",
    "rate_limiter",
    "performance_monitor",
    "connection_cache",
    # Router
    "websocket_router",
    "startup_realtime",
    "shutdown_realtime",
]
