"""
Cache Manager

Comprehensive caching strategy implementation with:
- Redis-backed caching
- Cache-aside pattern
- Write-through caching
- Cache invalidation
- TTL management
- Multi-level caching
- Cache statistics

EPIC-003: US-003.4 Caching Strategy Implementation
"""

import asyncio
import functools
import hashlib
import json
import os
import pickle
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from dataclasses import dataclass, field
import logging

import redis.asyncio as aioredis
import redis

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class CacheConfig:
    """Cache configuration."""
    redis_url: str = "redis://localhost:6379"
    default_ttl: int = 3600  # 1 hour
    max_memory: str = "256mb"
    eviction_policy: str = "allkeys-lru"
    key_prefix: str = "healthtech:"
    enable_stats: bool = True
    compression_threshold: int = 1024  # Compress values larger than 1KB


@dataclass
class CacheStats:
    """Cache statistics."""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    errors: int = 0
    bytes_read: int = 0
    bytes_written: int = 0

    @property
    def hit_ratio(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class CacheSerializer:
    """Handles serialization/deserialization of cache values."""

    @staticmethod
    def serialize(value: Any, compress: bool = False) -> bytes:
        """Serialize a value for cache storage."""
        try:
            # Try JSON first (more portable)
            json_str = json.dumps(value, default=str)
            data = json_str.encode("utf-8")
            prefix = b"J:"  # JSON marker
        except (TypeError, ValueError):
            # Fall back to pickle for complex objects
            data = pickle.dumps(value)
            prefix = b"P:"  # Pickle marker

        if compress and len(data) > 1024:
            import zlib
            data = zlib.compress(data)
            prefix = b"Z" + prefix  # Compressed marker

        return prefix + data

    @staticmethod
    def deserialize(data: bytes) -> Any:
        """Deserialize a cached value."""
        if data is None:
            return None

        # Check for compression
        compressed = data.startswith(b"Z")
        if compressed:
            import zlib
            data = zlib.decompress(data[1:])

        # Check format marker
        marker = data[:2]
        payload = data[2:]

        if marker == b"J:":
            return json.loads(payload.decode("utf-8"))
        elif marker == b"P:":
            return pickle.loads(payload)
        else:
            # Legacy format - try JSON then pickle
            try:
                return json.loads(data.decode("utf-8"))
            except:
                return pickle.loads(data)


class CacheManager:
    """
    Redis-backed cache manager with comprehensive caching features.

    Features:
    - Automatic serialization/deserialization
    - TTL management
    - Pattern-based invalidation
    - Cache statistics
    - Multi-tenant support
    - Async and sync interfaces
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig(
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        )
        self._async_redis: Optional[aioredis.Redis] = None
        self._sync_redis: Optional[redis.Redis] = None
        self._local_cache: Dict[str, tuple] = {}  # key -> (value, expires_at)
        self._stats = CacheStats()
        self._serializer = CacheSerializer()

    async def connect_async(self):
        """Initialize async Redis connection."""
        if self._async_redis is None:
            self._async_redis = await aioredis.from_url(
                self.config.redis_url,
                encoding="utf-8",
                decode_responses=False,  # Handle binary data
            )
            logger.info("CacheManager async connection established")

    def connect_sync(self):
        """Initialize sync Redis connection."""
        if self._sync_redis is None:
            self._sync_redis = redis.from_url(
                self.config.redis_url,
                decode_responses=False,
            )
            logger.info("CacheManager sync connection established")

    async def close(self):
        """Close Redis connections."""
        if self._async_redis:
            await self._async_redis.close()
        if self._sync_redis:
            self._sync_redis.close()

    def _make_key(self, key: str, tenant_id: Optional[str] = None) -> str:
        """Generate full cache key with prefix and tenant."""
        parts = [self.config.key_prefix]
        if tenant_id:
            parts.append(f"t:{tenant_id}:")
        parts.append(key)
        return "".join(parts)

    async def get(
        self,
        key: str,
        tenant_id: Optional[str] = None,
        default: Any = None,
    ) -> Any:
        """
        Get a value from cache.

        Args:
            key: Cache key
            tenant_id: Optional tenant ID for isolation
            default: Default value if not found

        Returns:
            Cached value or default
        """
        full_key = self._make_key(key, tenant_id)

        # Check local cache first (L1)
        if full_key in self._local_cache:
            value, expires_at = self._local_cache[full_key]
            if expires_at > time.time():
                self._stats.hits += 1
                return value
            else:
                del self._local_cache[full_key]

        # Check Redis (L2)
        try:
            await self.connect_async()
            data = await self._async_redis.get(full_key)

            if data:
                self._stats.hits += 1
                self._stats.bytes_read += len(data)
                value = self._serializer.deserialize(data)

                # Store in local cache with short TTL
                ttl = await self._async_redis.ttl(full_key)
                if ttl > 0:
                    local_ttl = min(ttl, 60)  # Max 60 seconds in L1
                    self._local_cache[full_key] = (value, time.time() + local_ttl)

                return value
            else:
                self._stats.misses += 1
                return default

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self._stats.errors += 1
            return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tenant_id: Optional[str] = None,
        compress: bool = False,
    ) -> bool:
        """
        Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
            tenant_id: Optional tenant ID
            compress: Whether to compress the value

        Returns:
            True if successful
        """
        full_key = self._make_key(key, tenant_id)
        ttl = ttl or self.config.default_ttl

        try:
            await self.connect_async()
            data = self._serializer.serialize(value, compress)

            await self._async_redis.setex(full_key, ttl, data)

            self._stats.sets += 1
            self._stats.bytes_written += len(data)

            # Update local cache
            self._local_cache[full_key] = (value, time.time() + min(ttl, 60))

            return True

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            self._stats.errors += 1
            return False

    async def delete(
        self,
        key: str,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """Delete a key from cache."""
        full_key = self._make_key(key, tenant_id)

        try:
            await self.connect_async()
            await self._async_redis.delete(full_key)

            self._stats.deletes += 1
            self._local_cache.pop(full_key, None)

            return True

        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            self._stats.errors += 1
            return False

    async def delete_pattern(
        self,
        pattern: str,
        tenant_id: Optional[str] = None,
    ) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Key pattern (supports * wildcards)
            tenant_id: Optional tenant ID

        Returns:
            Number of keys deleted
        """
        full_pattern = self._make_key(pattern, tenant_id)

        try:
            await self.connect_async()
            deleted = 0

            async for key in self._async_redis.scan_iter(match=full_pattern):
                await self._async_redis.delete(key)
                deleted += 1

            self._stats.deletes += deleted

            # Clear matching keys from local cache
            to_remove = [k for k in self._local_cache if k.startswith(full_pattern.replace("*", ""))]
            for k in to_remove:
                del self._local_cache[k]

            return deleted

        except Exception as e:
            logger.error(f"Cache delete_pattern error: {e}")
            self._stats.errors += 1
            return 0

    async def get_or_set(
        self,
        key: str,
        fetch_func: Callable[[], Any],
        ttl: Optional[int] = None,
        tenant_id: Optional[str] = None,
    ) -> Any:
        """
        Get from cache or fetch and cache the result.

        Args:
            key: Cache key
            fetch_func: Function to fetch data if not cached
            ttl: Time-to-live
            tenant_id: Optional tenant ID

        Returns:
            Cached or freshly fetched value
        """
        # Try cache first
        value = await self.get(key, tenant_id)
        if value is not None:
            return value

        # Fetch data
        if asyncio.iscoroutinefunction(fetch_func):
            value = await fetch_func()
        else:
            value = fetch_func()

        # Cache result
        if value is not None:
            await self.set(key, value, ttl, tenant_id)

        return value

    async def mget(
        self,
        keys: List[str],
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get multiple values from cache.

        Args:
            keys: List of cache keys
            tenant_id: Optional tenant ID

        Returns:
            Dictionary of key -> value pairs
        """
        full_keys = [self._make_key(k, tenant_id) for k in keys]

        try:
            await self.connect_async()
            values = await self._async_redis.mget(full_keys)

            result = {}
            for key, value in zip(keys, values):
                if value:
                    result[key] = self._serializer.deserialize(value)
                    self._stats.hits += 1
                else:
                    self._stats.misses += 1

            return result

        except Exception as e:
            logger.error(f"Cache mget error: {e}")
            self._stats.errors += 1
            return {}

    async def mset(
        self,
        mapping: Dict[str, Any],
        ttl: Optional[int] = None,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """
        Set multiple values in cache.

        Args:
            mapping: Dictionary of key -> value pairs
            ttl: Time-to-live (applied to all keys)
            tenant_id: Optional tenant ID

        Returns:
            True if successful
        """
        ttl = ttl or self.config.default_ttl

        try:
            await self.connect_async()
            pipe = self._async_redis.pipeline()

            for key, value in mapping.items():
                full_key = self._make_key(key, tenant_id)
                data = self._serializer.serialize(value)
                pipe.setex(full_key, ttl, data)

            await pipe.execute()
            self._stats.sets += len(mapping)
            return True

        except Exception as e:
            logger.error(f"Cache mset error: {e}")
            self._stats.errors += 1
            return False

    async def incr(
        self,
        key: str,
        amount: int = 1,
        tenant_id: Optional[str] = None,
    ) -> int:
        """Increment a counter in cache."""
        full_key = self._make_key(key, tenant_id)

        try:
            await self.connect_async()
            return await self._async_redis.incrby(full_key, amount)
        except Exception as e:
            logger.error(f"Cache incr error: {e}")
            self._stats.errors += 1
            return 0

    async def expire(
        self,
        key: str,
        ttl: int,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """Set expiration on a key."""
        full_key = self._make_key(key, tenant_id)

        try:
            await self.connect_async()
            return await self._async_redis.expire(full_key, ttl)
        except Exception as e:
            logger.error(f"Cache expire error: {e}")
            self._stats.errors += 1
            return False

    async def exists(
        self,
        key: str,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """Check if a key exists in cache."""
        full_key = self._make_key(key, tenant_id)

        try:
            await self.connect_async()
            return await self._async_redis.exists(full_key)
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            self._stats.errors += 1
            return False

    async def lock(
        self,
        name: str,
        timeout: int = 10,
        tenant_id: Optional[str] = None,
    ):
        """
        Acquire a distributed lock.

        Usage:
            async with cache.lock("my-lock"):
                # Critical section
                pass
        """
        full_key = self._make_key(f"lock:{name}", tenant_id)
        await self.connect_async()
        return self._async_redis.lock(full_key, timeout=timeout)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "hits": self._stats.hits,
            "misses": self._stats.misses,
            "hit_ratio": self._stats.hit_ratio,
            "sets": self._stats.sets,
            "deletes": self._stats.deletes,
            "errors": self._stats.errors,
            "bytes_read": self._stats.bytes_read,
            "bytes_written": self._stats.bytes_written,
            "local_cache_size": len(self._local_cache),
        }

    async def get_redis_info(self) -> Dict[str, Any]:
        """Get Redis server info."""
        try:
            await self.connect_async()
            info = await self._async_redis.info()
            return {
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses"),
            }
        except Exception as e:
            logger.error(f"Error getting Redis info: {e}")
            return {}


def cached(
    ttl: int = 3600,
    key_prefix: str = "",
    tenant_aware: bool = True,
):
    """
    Decorator for caching function results.

    Args:
        ttl: Time-to-live in seconds
        key_prefix: Prefix for cache key
        tenant_aware: Whether to include tenant in cache key

    Usage:
        @cached(ttl=300, key_prefix="user")
        async def get_user(user_id: str):
            return await db.query(User).filter(User.id == user_id).first()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [key_prefix or func.__name__]

            # Add positional args
            for arg in args:
                if hasattr(arg, "__dict__"):
                    # Skip complex objects like db sessions
                    continue
                key_parts.append(str(arg))

            # Add keyword args (sorted for consistency)
            for k, v in sorted(kwargs.items()):
                if k == "db" or k == "session":
                    continue
                key_parts.append(f"{k}:{v}")

            cache_key = ":".join(key_parts)

            # Get tenant from context if tenant_aware
            tenant_id = None
            if tenant_aware:
                from .tenant_context import get_current_tenant
                tenant_id = get_current_tenant()

            # Try cache
            value = await cache_manager.get(cache_key, tenant_id)
            if value is not None:
                return value

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            if result is not None:
                await cache_manager.set(cache_key, result, ttl, tenant_id)

            return result

        return wrapper
    return decorator


# Global cache manager instance
cache_manager = CacheManager()


@dataclass
class WarmingTask:
    """A cache warming task."""
    name: str
    key_pattern: str
    fetch_func: Callable
    ttl: int = 3600
    priority: int = 1  # 1 = highest
    tenant_ids: Optional[List[str]] = None  # None = all tenants
    schedule_cron: Optional[str] = None  # e.g., "0 */6 * * *" for every 6 hours


class CacheWarmer:
    """
    Cache warming service for pre-populating frequently accessed data.

    Features:
    - Schedule-based warming
    - Priority-based warming
    - Multi-tenant support
    - Warming progress tracking
    - Configurable warming tasks
    """

    def __init__(self, cache: CacheManager):
        self.cache = cache
        self._tasks: Dict[str, WarmingTask] = {}
        self._warming_in_progress: bool = False
        self._last_warm: Optional[datetime] = None
        self._warm_stats: Dict[str, int] = {"total": 0, "success": 0, "failed": 0}

    def register_task(self, task: WarmingTask):
        """Register a warming task."""
        self._tasks[task.name] = task
        logger.info(f"Registered cache warming task: {task.name}")

    def register_default_healthcare_tasks(self, db_session_factory: Callable):
        """Register default healthcare warming tasks."""

        # Reference data - changes rarely
        self.register_task(WarmingTask(
            name="icd10_codes",
            key_pattern="ref:icd10:*",
            fetch_func=lambda: self._fetch_reference_data(db_session_factory, "icd10_codes"),
            ttl=86400,  # 24 hours
            priority=1,
        ))

        self.register_task(WarmingTask(
            name="cpt_codes",
            key_pattern="ref:cpt:*",
            fetch_func=lambda: self._fetch_reference_data(db_session_factory, "cpt_codes"),
            ttl=86400,
            priority=1,
        ))

        self.register_task(WarmingTask(
            name="snomed_codes",
            key_pattern="ref:snomed:*",
            fetch_func=lambda: self._fetch_reference_data(db_session_factory, "snomed_codes"),
            ttl=86400,
            priority=1,
        ))

        # Provider schedules - moderate TTL
        self.register_task(WarmingTask(
            name="provider_schedules",
            key_pattern="schedule:provider:*",
            fetch_func=lambda tenant_id: self._fetch_provider_schedules(db_session_factory, tenant_id),
            ttl=1800,  # 30 minutes
            priority=2,
        ))

        # Appointment slots - short TTL, high priority
        self.register_task(WarmingTask(
            name="available_slots",
            key_pattern="slots:*",
            fetch_func=lambda tenant_id: self._fetch_available_slots(db_session_factory, tenant_id),
            ttl=300,  # 5 minutes
            priority=1,
        ))

        # Organization settings - rarely changes
        self.register_task(WarmingTask(
            name="org_settings",
            key_pattern="org:settings:*",
            fetch_func=lambda tenant_id: self._fetch_org_settings(db_session_factory, tenant_id),
            ttl=3600,  # 1 hour
            priority=2,
        ))

    async def _fetch_reference_data(self, db_session_factory, ref_type: str) -> Dict[str, Any]:
        """Fetch reference data from database."""
        # Placeholder - actual implementation would query the database
        return {"type": ref_type, "loaded": True}

    async def _fetch_provider_schedules(self, db_session_factory, tenant_id: str) -> Dict[str, Any]:
        """Fetch provider schedules for a tenant."""
        return {"tenant_id": tenant_id, "schedules": []}

    async def _fetch_available_slots(self, db_session_factory, tenant_id: str) -> Dict[str, Any]:
        """Fetch available appointment slots."""
        return {"tenant_id": tenant_id, "slots": []}

    async def _fetch_org_settings(self, db_session_factory, tenant_id: str) -> Dict[str, Any]:
        """Fetch organization settings."""
        return {"tenant_id": tenant_id, "settings": {}}

    async def warm(
        self,
        task_names: Optional[List[str]] = None,
        tenant_ids: Optional[List[str]] = None,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute cache warming.

        Args:
            task_names: Specific tasks to warm (None = all)
            tenant_ids: Specific tenants to warm (None = all)
            force: Force warming even if recently warmed

        Returns:
            Warming results
        """
        if self._warming_in_progress and not force:
            return {"status": "skipped", "reason": "warming already in progress"}

        self._warming_in_progress = True
        self._warm_stats = {"total": 0, "success": 0, "failed": 0}

        start_time = time.time()
        results = {"tasks": {}}

        try:
            # Get tasks to warm
            tasks = self._tasks
            if task_names:
                tasks = {k: v for k, v in tasks.items() if k in task_names}

            # Sort by priority
            sorted_tasks = sorted(tasks.values(), key=lambda t: t.priority)

            for task in sorted_tasks:
                task_result = await self._warm_task(task, tenant_ids)
                results["tasks"][task.name] = task_result

            self._last_warm = datetime.now(timezone.utc)

        except Exception as e:
            logger.error(f"Cache warming error: {e}")
            results["error"] = str(e)

        finally:
            self._warming_in_progress = False

        results["duration_ms"] = (time.time() - start_time) * 1000
        results["stats"] = self._warm_stats

        return results

    async def _warm_task(
        self,
        task: WarmingTask,
        tenant_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Warm a single task."""
        result = {"success": 0, "failed": 0, "keys": []}

        try:
            # Determine which tenants to warm
            tenants = tenant_ids or task.tenant_ids or [None]

            for tenant_id in tenants:
                try:
                    self._warm_stats["total"] += 1

                    # Fetch data
                    if tenant_id:
                        data = await task.fetch_func(tenant_id)
                    else:
                        data = await task.fetch_func()

                    # Generate cache key
                    key = task.key_pattern.replace("*", tenant_id or "global")

                    # Store in cache
                    await self.cache.set(key, data, task.ttl, tenant_id)

                    result["success"] += 1
                    result["keys"].append(key)
                    self._warm_stats["success"] += 1

                except Exception as e:
                    logger.error(f"Error warming {task.name} for tenant {tenant_id}: {e}")
                    result["failed"] += 1
                    self._warm_stats["failed"] += 1

        except Exception as e:
            logger.error(f"Error warming task {task.name}: {e}")
            result["error"] = str(e)

        return result

    async def warm_on_startup(self, tenant_ids: Optional[List[str]] = None):
        """Warm cache on application startup."""
        logger.info("Starting cache warm-up on startup...")
        results = await self.warm(tenant_ids=tenant_ids)
        logger.info(
            f"Cache warm-up complete: "
            f"{results['stats']['success']} success, "
            f"{results['stats']['failed']} failed, "
            f"{results['duration_ms']:.0f}ms"
        )
        return results

    def get_warming_status(self) -> Dict[str, Any]:
        """Get current warming status."""
        return {
            "in_progress": self._warming_in_progress,
            "last_warm": self._last_warm.isoformat() if self._last_warm else None,
            "stats": self._warm_stats,
            "registered_tasks": list(self._tasks.keys()),
        }


# Global cache warmer instance
cache_warmer = CacheWarmer(cache_manager)
