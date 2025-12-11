"""
Real-Time Performance Optimization

Performance enhancements for real-time communication:
- Message batching for efficient delivery
- Connection state caching
- Redis cluster adapter for horizontal scaling
- Message compression
- Rate limiting
- Circuit breaker for external services

EPIC-001: US-001.8 Performance Optimization
"""

import asyncio
import json
import zlib
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set, Any, Callable, Awaitable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import logging

import redis.asyncio as redis
from redis.asyncio.cluster import RedisCluster

logger = logging.getLogger(__name__)


class CompressionLevel(str, Enum):
    """Compression levels for messages."""
    NONE = "none"
    FAST = "fast"
    BALANCED = "balanced"
    BEST = "best"


@dataclass
class BatchConfig:
    """Configuration for message batching."""
    enabled: bool = True
    max_batch_size: int = 100
    max_wait_ms: int = 50  # Max time to wait for batch
    compress_threshold: int = 1024  # Compress messages larger than this
    compression_level: CompressionLevel = CompressionLevel.BALANCED


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    enabled: bool = True
    messages_per_second: int = 100
    burst_size: int = 200
    per_user_limit: int = 50
    per_tenant_limit: int = 1000


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    enabled: bool = True
    failure_threshold: int = 5
    reset_timeout_seconds: int = 30
    half_open_requests: int = 3


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class BatchedMessage:
    """A message in a batch."""
    connection_id: str
    data: str
    priority: int = 0
    timestamp: float = field(default_factory=time.time)


@dataclass
class MessageBatch:
    """A batch of messages to deliver."""
    batch_id: str
    messages: List[BatchedMessage]
    created_at: float
    compressed: bool = False


class MessageBatcher:
    """
    Batches messages for efficient delivery.

    Instead of sending messages one at a time, batches them
    and sends in groups to reduce overhead.
    """

    def __init__(self, config: Optional[BatchConfig] = None):
        self.config = config or BatchConfig()

        # Batches per connection
        self._batches: Dict[str, List[BatchedMessage]] = defaultdict(list)
        self._batch_locks: Dict[str, asyncio.Lock] = {}
        self._batch_timers: Dict[str, asyncio.Task] = {}

        # Delivery callback
        self._deliver_callback: Optional[Callable[[str, List[str]], Awaitable[None]]] = None

        self._running = False
        self._flush_task: Optional[asyncio.Task] = None

    def set_delivery_callback(
        self,
        callback: Callable[[str, List[str]], Awaitable[None]],
    ):
        """
        Set the callback for delivering batched messages.

        Args:
            callback: Async function(connection_id, messages) -> None
        """
        self._deliver_callback = callback

    async def start(self):
        """Start the batcher."""
        self._running = True
        self._flush_task = asyncio.create_task(self._flush_loop())
        logger.info("MessageBatcher started")

    async def stop(self):
        """Stop the batcher and flush remaining messages."""
        self._running = False

        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        # Flush all remaining batches
        for connection_id in list(self._batches.keys()):
            await self._flush_batch(connection_id)

        logger.info("MessageBatcher stopped")

    async def add_message(
        self,
        connection_id: str,
        data: str,
        priority: int = 0,
        immediate: bool = False,
    ):
        """
        Add a message to the batch.

        Args:
            connection_id: Target connection
            data: Message data
            priority: Message priority (higher = more important)
            immediate: If True, send immediately without batching
        """
        if not self.config.enabled or immediate:
            if self._deliver_callback:
                await self._deliver_callback(connection_id, [data])
            return

        # Get or create lock for this connection
        if connection_id not in self._batch_locks:
            self._batch_locks[connection_id] = asyncio.Lock()

        async with self._batch_locks[connection_id]:
            message = BatchedMessage(
                connection_id=connection_id,
                data=data,
                priority=priority,
            )

            self._batches[connection_id].append(message)

            # Check if batch is full
            if len(self._batches[connection_id]) >= self.config.max_batch_size:
                await self._flush_batch(connection_id)
            else:
                # Start timer for this batch if not already started
                if connection_id not in self._batch_timers:
                    self._batch_timers[connection_id] = asyncio.create_task(
                        self._batch_timeout(connection_id)
                    )

    async def _batch_timeout(self, connection_id: str):
        """Timer to flush batch after max wait time."""
        await asyncio.sleep(self.config.max_wait_ms / 1000)
        await self._flush_batch(connection_id)

    async def _flush_batch(self, connection_id: str):
        """Flush messages for a connection."""
        if connection_id not in self._batches:
            return

        # Cancel timer if exists
        if connection_id in self._batch_timers:
            self._batch_timers[connection_id].cancel()
            del self._batch_timers[connection_id]

        async with self._batch_locks.get(connection_id, asyncio.Lock()):
            messages = self._batches.pop(connection_id, [])

        if not messages or not self._deliver_callback:
            return

        # Sort by priority (higher first)
        messages.sort(key=lambda m: m.priority, reverse=True)

        # Compress if needed
        message_data = [m.data for m in messages]

        if len(messages) > 1:
            # Send as batched message
            batch_data = json.dumps({
                "type": "batch",
                "messages": message_data,
            })

            # Compress if large enough
            if len(batch_data) > self.config.compress_threshold:
                batch_data = self._compress(batch_data)

            await self._deliver_callback(connection_id, [batch_data])
        else:
            # Single message, send as-is
            await self._deliver_callback(connection_id, message_data)

    def _compress(self, data: str) -> str:
        """Compress message data."""
        level_map = {
            CompressionLevel.NONE: 0,
            CompressionLevel.FAST: 1,
            CompressionLevel.BALANCED: 6,
            CompressionLevel.BEST: 9,
        }
        level = level_map.get(self.config.compression_level, 6)

        if level == 0:
            return data

        compressed = zlib.compress(data.encode(), level)
        # Return base64 encoded with marker
        import base64
        return "Z:" + base64.b64encode(compressed).decode()

    async def _flush_loop(self):
        """Periodic flush of all batches."""
        while self._running:
            try:
                await asyncio.sleep(self.config.max_wait_ms / 1000)

                # Flush any batches that are ready
                for connection_id in list(self._batches.keys()):
                    if self._batches.get(connection_id):
                        await self._flush_batch(connection_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in flush loop: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get batcher statistics."""
        return {
            "pending_batches": len(self._batches),
            "pending_messages": sum(len(m) for m in self._batches.values()),
            "config": {
                "max_batch_size": self.config.max_batch_size,
                "max_wait_ms": self.config.max_wait_ms,
            },
        }


class RateLimiter:
    """
    Rate limiter using token bucket algorithm.

    Limits message rate per user, tenant, and globally.
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()

        # Token buckets: {identifier: (tokens, last_update)}
        self._buckets: Dict[str, Tuple[float, float]] = {}
        self._lock = asyncio.Lock()

    async def check_rate_limit(
        self,
        identifier: str,
        limit: int,
        burst: int,
    ) -> Tuple[bool, float]:
        """
        Check if request is within rate limit.

        Args:
            identifier: Rate limit identifier (user_id, tenant_id, etc.)
            limit: Tokens per second
            burst: Maximum burst size

        Returns:
            (allowed, retry_after_seconds)
        """
        if not self.config.enabled:
            return True, 0

        async with self._lock:
            now = time.time()

            if identifier not in self._buckets:
                self._buckets[identifier] = (burst, now)
                return True, 0

            tokens, last_update = self._buckets[identifier]

            # Add tokens based on time passed
            elapsed = now - last_update
            new_tokens = min(burst, tokens + elapsed * limit)

            if new_tokens >= 1:
                self._buckets[identifier] = (new_tokens - 1, now)
                return True, 0
            else:
                # Calculate retry time
                retry_after = (1 - new_tokens) / limit
                return False, retry_after

    async def is_allowed_user(self, user_id: str) -> Tuple[bool, float]:
        """Check rate limit for a user."""
        return await self.check_rate_limit(
            f"user:{user_id}",
            self.config.per_user_limit,
            self.config.per_user_limit * 2,
        )

    async def is_allowed_tenant(self, tenant_id: str) -> Tuple[bool, float]:
        """Check rate limit for a tenant."""
        return await self.check_rate_limit(
            f"tenant:{tenant_id}",
            self.config.per_tenant_limit,
            self.config.per_tenant_limit * 2,
        )

    async def is_allowed_global(self) -> Tuple[bool, float]:
        """Check global rate limit."""
        return await self.check_rate_limit(
            "global",
            self.config.messages_per_second,
            self.config.burst_size,
        )

    async def cleanup_old_buckets(self, max_age_seconds: int = 3600):
        """Remove stale bucket entries."""
        async with self._lock:
            now = time.time()
            stale = [
                key for key, (_, last) in self._buckets.items()
                if now - last > max_age_seconds
            ]
            for key in stale:
                del self._buckets[key]


class CircuitBreaker:
    """
    Circuit breaker for external service calls.

    Prevents cascading failures by failing fast when a service is down.
    """

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()

        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None

    @property
    def state(self) -> CircuitBreakerState:
        """Get current circuit breaker state."""
        if self._state == CircuitBreakerState.OPEN:
            # Check if should transition to half-open
            if self._last_failure_time:
                elapsed = time.time() - self._last_failure_time
                if elapsed >= self.config.reset_timeout_seconds:
                    self._state = CircuitBreakerState.HALF_OPEN
                    self._success_count = 0

        return self._state

    async def execute(
        self,
        func: Callable[[], Awaitable[Any]],
        fallback: Optional[Callable[[], Awaitable[Any]]] = None,
    ) -> Any:
        """
        Execute a function with circuit breaker protection.

        Args:
            func: Function to execute
            fallback: Optional fallback function

        Returns:
            Function result or fallback result

        Raises:
            Exception if circuit is open and no fallback
        """
        if not self.config.enabled:
            return await func()

        state = self.state

        if state == CircuitBreakerState.OPEN:
            if fallback:
                return await fallback()
            raise Exception(f"Circuit breaker {self.name} is OPEN")

        try:
            result = await func()
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            if fallback:
                return await fallback()
            raise

    def _on_success(self):
        """Handle successful call."""
        if self._state == CircuitBreakerState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.config.half_open_requests:
                self._state = CircuitBreakerState.CLOSED
                self._failure_count = 0
        else:
            self._failure_count = max(0, self._failure_count - 1)

    def _on_failure(self):
        """Handle failed call."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._failure_count >= self.config.failure_threshold:
            self._state = CircuitBreakerState.OPEN

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
        }


class ConnectionStateCache:
    """
    Caches connection state for fast lookups.

    Uses Redis for distributed caching across servers.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        ttl: int = 300,  # 5 minutes
    ):
        self.redis_url = redis_url
        self.ttl = ttl
        self._redis: Optional[redis.Redis] = None
        self._local_cache: Dict[str, Dict[str, Any]] = {}

    async def start(self):
        """Initialize cache."""
        try:
            self._redis = redis.from_url(self.redis_url, decode_responses=True)
            await self._redis.ping()
            logger.info("ConnectionStateCache connected to Redis")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}. Using local cache.")
            self._redis = None

    async def stop(self):
        """Stop cache."""
        if self._redis:
            await self._redis.close()

    def _key(self, connection_id: str) -> str:
        """Get Redis key for connection."""
        return f"conn_state:{connection_id}"

    async def set(self, connection_id: str, state: Dict[str, Any]):
        """Cache connection state."""
        self._local_cache[connection_id] = state

        if self._redis:
            try:
                await self._redis.setex(
                    self._key(connection_id),
                    self.ttl,
                    json.dumps(state),
                )
            except Exception as e:
                logger.error(f"Redis error caching state: {e}")

    async def get(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get cached connection state."""
        # Check local cache first
        if connection_id in self._local_cache:
            return self._local_cache[connection_id]

        if self._redis:
            try:
                data = await self._redis.get(self._key(connection_id))
                if data:
                    state = json.loads(data)
                    self._local_cache[connection_id] = state
                    return state
            except Exception as e:
                logger.error(f"Redis error getting state: {e}")

        return None

    async def delete(self, connection_id: str):
        """Delete cached state."""
        self._local_cache.pop(connection_id, None)

        if self._redis:
            try:
                await self._redis.delete(self._key(connection_id))
            except Exception as e:
                logger.error(f"Redis error deleting state: {e}")

    async def get_user_connections(self, user_id: str) -> List[str]:
        """Get all connection IDs for a user."""
        # This is a simplified implementation
        # In production, maintain a separate index
        return [
            conn_id for conn_id, state in self._local_cache.items()
            if state.get("user_id") == user_id
        ]


class RedisClusterAdapter:
    """
    Redis cluster adapter for horizontal scaling.

    Provides pub/sub across Redis cluster for multi-server setups.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        cluster_mode: bool = False,
    ):
        self.redis_url = redis_url
        self.cluster_mode = cluster_mode
        self._redis: Optional[redis.Redis] = None
        self._cluster: Optional[RedisCluster] = None

    async def start(self):
        """Initialize Redis connection."""
        try:
            if self.cluster_mode:
                # Parse URL for cluster connection
                # In production, use proper cluster URL parsing
                self._cluster = RedisCluster.from_url(
                    self.redis_url,
                    decode_responses=True,
                )
                await self._cluster.ping()
                logger.info("Connected to Redis cluster")
            else:
                self._redis = redis.from_url(self.redis_url, decode_responses=True)
                await self._redis.ping()
                logger.info("Connected to Redis")

        except Exception as e:
            logger.error(f"Redis connection error: {e}")
            raise

    async def stop(self):
        """Close Redis connection."""
        if self._cluster:
            await self._cluster.close()
        if self._redis:
            await self._redis.close()

    @property
    def client(self) -> redis.Redis:
        """Get Redis client."""
        return self._cluster or self._redis

    async def publish(self, channel: str, message: str) -> int:
        """Publish message to channel."""
        return await self.client.publish(channel, message)

    async def subscribe(self, *channels: str):
        """Subscribe to channels."""
        pubsub = self.client.pubsub()
        await pubsub.subscribe(*channels)
        return pubsub

    async def psubscribe(self, *patterns: str):
        """Subscribe to channel patterns."""
        pubsub = self.client.pubsub()
        await pubsub.psubscribe(*patterns)
        return pubsub


class PerformanceMonitor:
    """
    Monitors real-time communication performance.

    Collects metrics and provides insights.
    """

    def __init__(self):
        self._metrics = {
            "messages_sent": 0,
            "messages_received": 0,
            "bytes_sent": 0,
            "bytes_received": 0,
            "latency_samples": [],
            "errors": 0,
        }
        self._start_time = time.time()

    def record_message_sent(self, size: int):
        """Record a sent message."""
        self._metrics["messages_sent"] += 1
        self._metrics["bytes_sent"] += size

    def record_message_received(self, size: int):
        """Record a received message."""
        self._metrics["messages_received"] += 1
        self._metrics["bytes_received"] += size

    def record_latency(self, latency_ms: float):
        """Record message latency."""
        samples = self._metrics["latency_samples"]
        samples.append(latency_ms)
        # Keep last 1000 samples
        if len(samples) > 1000:
            self._metrics["latency_samples"] = samples[-1000:]

    def record_error(self):
        """Record an error."""
        self._metrics["errors"] += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        samples = self._metrics["latency_samples"]
        uptime = time.time() - self._start_time

        return {
            "uptime_seconds": uptime,
            "messages": {
                "sent": self._metrics["messages_sent"],
                "received": self._metrics["messages_received"],
                "rate_per_second": self._metrics["messages_sent"] / max(1, uptime),
            },
            "bytes": {
                "sent": self._metrics["bytes_sent"],
                "received": self._metrics["bytes_received"],
            },
            "latency": {
                "samples": len(samples),
                "avg_ms": sum(samples) / max(1, len(samples)),
                "min_ms": min(samples) if samples else 0,
                "max_ms": max(samples) if samples else 0,
                "p95_ms": sorted(samples)[int(len(samples) * 0.95)] if samples else 0,
            },
            "errors": self._metrics["errors"],
        }


# Global instances
message_batcher = MessageBatcher()
rate_limiter = RateLimiter()
performance_monitor = PerformanceMonitor()
connection_cache = ConnectionStateCache()
