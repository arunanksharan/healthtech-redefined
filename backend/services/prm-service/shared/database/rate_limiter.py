"""
Rate Limiter and Quota Management

EPIC-004: Multi-Tenancy Implementation
US-004.4: Tenant Resource Management

Provides comprehensive rate limiting and quota management:
- Token bucket rate limiting
- Sliding window rate limiting
- Per-tenant quotas
- Resource usage tracking
- Quota enforcement
- Automatic alert on threshold breach
"""

import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

import redis.asyncio as aioredis
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class QuotaType(str, Enum):
    """Types of quotas that can be enforced."""
    USERS = "users"
    PATIENTS = "patients"
    API_CALLS = "api_calls"
    STORAGE = "storage"
    APPOINTMENTS = "appointments"
    ENCOUNTERS = "encounters"
    DOCUMENTS = "documents"
    AI_REQUESTS = "ai_requests"
    TELEHEALTH_MINUTES = "telehealth_minutes"
    SMS = "sms"
    EMAILS = "emails"
    WHATSAPP = "whatsapp"


class RateLimitWindow(str, Enum):
    """Rate limit window types."""
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"


@dataclass
class RateLimitConfig:
    """Configuration for a rate limit."""
    limit: int
    window: RateLimitWindow
    burst: Optional[int] = None  # Burst capacity for token bucket

    @property
    def window_seconds(self) -> int:
        """Get window size in seconds."""
        return {
            RateLimitWindow.SECOND: 1,
            RateLimitWindow.MINUTE: 60,
            RateLimitWindow.HOUR: 3600,
            RateLimitWindow.DAY: 86400,
        }[self.window]


@dataclass
class QuotaConfig:
    """Configuration for a quota."""
    quota_type: QuotaType
    limit: int
    warning_threshold: float = 0.8  # Alert at 80% usage
    period: str = "monthly"  # daily, monthly, yearly
    soft_limit: bool = False  # Allow exceeding with warning vs hard block


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""
    allowed: bool
    remaining: int
    limit: int
    reset_at: datetime
    retry_after: Optional[int] = None


@dataclass
class QuotaResult:
    """Result of a quota check."""
    allowed: bool
    current: int
    limit: int
    remaining: int
    usage_percent: float
    warning: bool = False
    message: str = ""


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter using Redis sorted sets.

    Provides accurate rate limiting without the boundary issues
    of fixed window counters.
    """

    def __init__(self, redis_client: aioredis.Redis, key_prefix: str = "rl"):
        self.redis = redis_client
        self.key_prefix = key_prefix

    async def check(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitResult:
        """
        Check if request is allowed under rate limit.

        Args:
            key: Unique identifier for the rate limit (e.g., tenant:api)
            limit: Maximum requests per window
            window_seconds: Window size in seconds

        Returns:
            RateLimitResult with allowed status and metadata
        """
        now = time.time()
        window_start = now - window_seconds
        full_key = f"{self.key_prefix}:{key}"

        # Use Redis pipeline for atomic operations
        pipe = self.redis.pipeline()

        # Remove old entries outside the window
        pipe.zremrangebyscore(full_key, 0, window_start)

        # Count current entries in window
        pipe.zcard(full_key)

        # Add current request with timestamp as score
        request_id = f"{now}:{id(asyncio)}"  # Unique request ID
        pipe.zadd(full_key, {request_id: now})

        # Set expiry on the key
        pipe.expire(full_key, window_seconds + 60)

        results = await pipe.execute()
        current_count = results[1]

        # Calculate reset time
        oldest = await self.redis.zrange(full_key, 0, 0, withscores=True)
        if oldest:
            oldest_time = oldest[0][1]
            reset_at = datetime.fromtimestamp(oldest_time + window_seconds, tz=timezone.utc)
        else:
            reset_at = datetime.now(timezone.utc) + timedelta(seconds=window_seconds)

        remaining = max(0, limit - current_count)

        if current_count > limit:
            # Remove the request we just added since it's denied
            await self.redis.zrem(full_key, request_id)

            retry_after = int(oldest[0][1] + window_seconds - now) + 1 if oldest else window_seconds

            return RateLimitResult(
                allowed=False,
                remaining=0,
                limit=limit,
                reset_at=reset_at,
                retry_after=retry_after,
            )

        return RateLimitResult(
            allowed=True,
            remaining=remaining - 1,  # Account for current request
            limit=limit,
            reset_at=reset_at,
        )

    async def get_usage(self, key: str, window_seconds: int) -> Tuple[int, int]:
        """Get current usage and remaining for a key."""
        now = time.time()
        window_start = now - window_seconds
        full_key = f"{self.key_prefix}:{key}"

        # Remove old and count current
        await self.redis.zremrangebyscore(full_key, 0, window_start)
        count = await self.redis.zcard(full_key)

        return count, max(0, 0)  # Caller provides limit

    async def reset(self, key: str):
        """Reset rate limit for a key."""
        full_key = f"{self.key_prefix}:{key}"
        await self.redis.delete(full_key)


class TokenBucketRateLimiter:
    """
    Token bucket rate limiter for bursty traffic.

    Allows short bursts while maintaining long-term rate.
    """

    def __init__(self, redis_client: aioredis.Redis, key_prefix: str = "tb"):
        self.redis = redis_client
        self.key_prefix = key_prefix

    async def check(
        self,
        key: str,
        rate: int,
        capacity: int,
        tokens: int = 1,
    ) -> RateLimitResult:
        """
        Check if tokens are available.

        Args:
            key: Unique identifier
            rate: Tokens added per second
            capacity: Maximum bucket capacity
            tokens: Tokens to consume

        Returns:
            RateLimitResult
        """
        now = time.time()
        full_key = f"{self.key_prefix}:{key}"

        # Lua script for atomic token bucket
        lua_script = """
        local key = KEYS[1]
        local rate = tonumber(ARGV[1])
        local capacity = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        local tokens = tonumber(ARGV[4])

        local data = redis.call('HMGET', key, 'tokens', 'last_update')
        local current_tokens = tonumber(data[1]) or capacity
        local last_update = tonumber(data[2]) or now

        -- Calculate tokens to add based on time passed
        local elapsed = now - last_update
        local new_tokens = math.min(capacity, current_tokens + (elapsed * rate))

        if new_tokens >= tokens then
            new_tokens = new_tokens - tokens
            redis.call('HMSET', key, 'tokens', new_tokens, 'last_update', now)
            redis.call('EXPIRE', key, 3600)
            return {1, new_tokens, capacity}
        else
            redis.call('HMSET', key, 'tokens', new_tokens, 'last_update', now)
            redis.call('EXPIRE', key, 3600)
            local wait_time = (tokens - new_tokens) / rate
            return {0, new_tokens, wait_time}
        end
        """

        result = await self.redis.eval(
            lua_script,
            1,
            full_key,
            rate,
            capacity,
            now,
            tokens,
        )

        allowed = result[0] == 1
        remaining = int(result[1])

        if allowed:
            return RateLimitResult(
                allowed=True,
                remaining=remaining,
                limit=capacity,
                reset_at=datetime.now(timezone.utc) + timedelta(seconds=capacity / rate),
            )
        else:
            retry_after = int(result[2]) + 1
            return RateLimitResult(
                allowed=False,
                remaining=0,
                limit=capacity,
                reset_at=datetime.now(timezone.utc) + timedelta(seconds=retry_after),
                retry_after=retry_after,
            )


class QuotaManager:
    """
    Manages resource quotas for tenants.

    Tracks usage against limits and enforces quotas.
    """

    def __init__(
        self,
        db_session_factory,
        redis_client: aioredis.Redis,
        alert_callback=None,
    ):
        self.db_factory = db_session_factory
        self.redis = redis_client
        self.alert_callback = alert_callback

    async def check_quota(
        self,
        tenant_id: str,
        quota_type: QuotaType,
        amount: int = 1,
    ) -> QuotaResult:
        """
        Check if quota would be exceeded.

        Args:
            tenant_id: Tenant identifier
            quota_type: Type of quota to check
            amount: Amount to consume

        Returns:
            QuotaResult with allowed status and usage info
        """
        # Get tenant limits
        limits = await self._get_tenant_limits(tenant_id)
        limit = limits.get(f"max_{quota_type.value}", 0)

        if limit == 0:
            # No limit set
            return QuotaResult(
                allowed=True,
                current=0,
                limit=0,
                remaining=999999,
                usage_percent=0,
                message="No limit configured",
            )

        # Get current usage
        current = await self._get_current_usage(tenant_id, quota_type)
        new_total = current + amount
        usage_percent = (new_total / limit) * 100 if limit > 0 else 0

        # Check warning threshold
        warning = usage_percent >= 80

        if warning and usage_percent < 100:
            # Send warning alert
            await self._send_quota_warning(tenant_id, quota_type, current, limit)

        if new_total > limit:
            return QuotaResult(
                allowed=False,
                current=current,
                limit=limit,
                remaining=max(0, limit - current),
                usage_percent=min(100, usage_percent),
                warning=True,
                message=f"Quota exceeded: {current}/{limit} {quota_type.value}",
            )

        return QuotaResult(
            allowed=True,
            current=current,
            limit=limit,
            remaining=limit - new_total,
            usage_percent=usage_percent,
            warning=warning,
            message="OK" if not warning else f"Warning: {usage_percent:.1f}% of quota used",
        )

    async def consume_quota(
        self,
        tenant_id: str,
        quota_type: QuotaType,
        amount: int = 1,
    ) -> QuotaResult:
        """
        Consume quota after successful operation.

        Args:
            tenant_id: Tenant identifier
            quota_type: Type of quota
            amount: Amount consumed

        Returns:
            QuotaResult with updated usage
        """
        # First check if allowed
        result = await self.check_quota(tenant_id, quota_type, amount)

        if not result.allowed:
            return result

        # Update usage counters
        await self._increment_usage(tenant_id, quota_type, amount)

        return QuotaResult(
            allowed=True,
            current=result.current + amount,
            limit=result.limit,
            remaining=result.remaining - amount,
            usage_percent=((result.current + amount) / result.limit * 100) if result.limit > 0 else 0,
            warning=result.warning,
            message=result.message,
        )

    async def get_all_quotas(self, tenant_id: str) -> Dict[str, QuotaResult]:
        """Get usage status for all quota types."""
        results = {}

        for quota_type in QuotaType:
            try:
                results[quota_type.value] = await self.check_quota(tenant_id, quota_type, 0)
            except Exception as e:
                logger.error(f"Error checking quota {quota_type}: {e}")
                results[quota_type.value] = QuotaResult(
                    allowed=True,
                    current=0,
                    limit=0,
                    remaining=0,
                    usage_percent=0,
                    message=f"Error: {str(e)}",
                )

        return results

    async def _get_tenant_limits(self, tenant_id: str) -> Dict[str, int]:
        """Get tenant's resource limits."""
        # Check cache first
        cache_key = f"tenant_limits:{tenant_id}"
        cached = await self.redis.get(cache_key)

        if cached:
            import json
            return json.loads(cached)

        # Query database
        db = self.db_factory()
        try:
            result = db.execute(
                text("SELECT limits FROM tenants WHERE id = :id"),
                {"id": tenant_id}
            ).fetchone()

            if result and result.limits:
                limits = result.limits
            else:
                # Default limits
                limits = {
                    "max_users": 5,
                    "max_patients": 1000,
                    "max_api_calls": 10000,
                    "max_storage": 5 * 1024 * 1024 * 1024,  # 5GB in bytes
                    "max_appointments": 10000,
                    "max_encounters": 10000,
                    "max_documents": 1000,
                    "max_ai_requests": 100,
                    "max_telehealth_minutes": 1000,
                    "max_sms": 1000,
                    "max_emails": 10000,
                    "max_whatsapp": 1000,
                }

            # Cache for 5 minutes
            import json
            await self.redis.setex(cache_key, 300, json.dumps(limits))

            return limits
        finally:
            db.close()

    async def _get_current_usage(self, tenant_id: str, quota_type: QuotaType) -> int:
        """Get current usage for a quota type."""
        # Map quota types to database queries
        db = self.db_factory()
        try:
            if quota_type == QuotaType.USERS:
                result = db.execute(
                    text("SELECT COUNT(*) FROM users WHERE tenant_id = :id AND is_active = true"),
                    {"id": tenant_id}
                ).scalar()

            elif quota_type == QuotaType.PATIENTS:
                result = db.execute(
                    text("SELECT COUNT(*) FROM patients WHERE tenant_id = :id"),
                    {"id": tenant_id}
                ).scalar()

            elif quota_type == QuotaType.API_CALLS:
                today = datetime.now(timezone.utc).date()
                result = db.execute(
                    text("""
                        SELECT COALESCE(api_calls, 0)
                        FROM tenant_usage_daily
                        WHERE tenant_id = :id AND date = :date
                    """),
                    {"id": tenant_id, "date": today}
                ).scalar() or 0

            elif quota_type == QuotaType.STORAGE:
                result = db.execute(
                    text("""
                        SELECT COALESCE(storage_bytes, 0)
                        FROM tenant_usage_daily
                        WHERE tenant_id = :id
                        ORDER BY date DESC LIMIT 1
                    """),
                    {"id": tenant_id}
                ).scalar() or 0

            elif quota_type == QuotaType.APPOINTMENTS:
                result = db.execute(
                    text("SELECT COUNT(*) FROM appointments WHERE tenant_id = :id"),
                    {"id": tenant_id}
                ).scalar()

            elif quota_type == QuotaType.ENCOUNTERS:
                result = db.execute(
                    text("SELECT COUNT(*) FROM encounters WHERE tenant_id = :id"),
                    {"id": tenant_id}
                ).scalar()

            else:
                # For daily metrics, check usage table
                today = datetime.now(timezone.utc).date()
                column_map = {
                    QuotaType.DOCUMENTS: "documents_uploaded",
                    QuotaType.AI_REQUESTS: "ai_requests",
                    QuotaType.TELEHEALTH_MINUTES: "telehealth_minutes",
                    QuotaType.SMS: "sms_sent",
                    QuotaType.EMAILS: "emails_sent",
                    QuotaType.WHATSAPP: "whatsapp_messages",
                }
                column = column_map.get(quota_type, "api_calls")
                result = db.execute(
                    text(f"""
                        SELECT COALESCE({column}, 0)
                        FROM tenant_usage_daily
                        WHERE tenant_id = :id AND date = :date
                    """),
                    {"id": tenant_id, "date": today}
                ).scalar() or 0

            return result or 0
        finally:
            db.close()

    async def _increment_usage(self, tenant_id: str, quota_type: QuotaType, amount: int):
        """Increment usage counter."""
        today = datetime.now(timezone.utc).date()

        # Map to column name
        column_map = {
            QuotaType.API_CALLS: "api_calls",
            QuotaType.DOCUMENTS: "documents_uploaded",
            QuotaType.AI_REQUESTS: "ai_requests",
            QuotaType.TELEHEALTH_MINUTES: "telehealth_minutes",
            QuotaType.SMS: "sms_sent",
            QuotaType.EMAILS: "emails_sent",
            QuotaType.WHATSAPP: "whatsapp_messages",
        }

        column = column_map.get(quota_type)
        if not column:
            return  # Entity counts are tracked by actual records

        db = self.db_factory()
        try:
            db.execute(
                text(f"""
                    INSERT INTO tenant_usage_daily (tenant_id, date, {column}, created_at, updated_at)
                    VALUES (:tenant_id, :date, :amount, :now, :now)
                    ON CONFLICT (tenant_id, date)
                    DO UPDATE SET {column} = tenant_usage_daily.{column} + :amount, updated_at = :now
                """),
                {
                    "tenant_id": tenant_id,
                    "date": today,
                    "amount": amount,
                    "now": datetime.now(timezone.utc),
                }
            )
            db.commit()
        finally:
            db.close()

    async def _send_quota_warning(
        self,
        tenant_id: str,
        quota_type: QuotaType,
        current: int,
        limit: int,
    ):
        """Send quota warning notification."""
        # Check if we already sent warning today
        cache_key = f"quota_warning:{tenant_id}:{quota_type.value}:{datetime.now().date()}"
        already_warned = await self.redis.get(cache_key)

        if already_warned:
            return

        # Mark as warned
        await self.redis.setex(cache_key, 86400, "1")

        # Call alert callback if provided
        if self.alert_callback:
            await self.alert_callback(
                tenant_id=tenant_id,
                alert_type="quota_warning",
                message=f"Quota warning: {quota_type.value} at {current}/{limit} ({current/limit*100:.1f}%)",
                metadata={
                    "quota_type": quota_type.value,
                    "current": current,
                    "limit": limit,
                    "usage_percent": current / limit * 100,
                },
            )

        logger.warning(
            f"Quota warning for tenant {tenant_id}: "
            f"{quota_type.value} at {current}/{limit}"
        )


class TenantRateLimiter:
    """
    Combined rate limiter for tenant API requests.

    Supports multiple rate limit tiers and rules.
    """

    def __init__(
        self,
        redis_client: aioredis.Redis,
        db_session_factory,
    ):
        self.sliding = SlidingWindowRateLimiter(redis_client, "rl")
        self.token = TokenBucketRateLimiter(redis_client, "tb")
        self.quota = QuotaManager(db_session_factory, redis_client)
        self.redis = redis_client

    async def check_request(
        self,
        tenant_id: str,
        endpoint: str = "api",
        tokens: int = 1,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if API request is allowed.

        Applies both rate limiting and quota checks.

        Returns:
            Tuple of (allowed, metadata)
        """
        # Get tenant's rate limit config
        config = await self._get_rate_limit_config(tenant_id)

        # Check sliding window rate limit (per minute)
        minute_result = await self.sliding.check(
            key=f"tenant:{tenant_id}:minute",
            limit=config["requests_per_minute"],
            window_seconds=60,
        )

        if not minute_result.allowed:
            return False, {
                "error": "rate_limit_exceeded",
                "limit_type": "per_minute",
                "remaining": minute_result.remaining,
                "retry_after": minute_result.retry_after,
                "reset_at": minute_result.reset_at.isoformat(),
            }

        # Check daily quota
        quota_result = await self.quota.check_quota(tenant_id, QuotaType.API_CALLS, tokens)

        if not quota_result.allowed:
            return False, {
                "error": "quota_exceeded",
                "limit_type": "daily_quota",
                "current": quota_result.current,
                "limit": quota_result.limit,
                "message": quota_result.message,
            }

        # Consume quota
        await self.quota.consume_quota(tenant_id, QuotaType.API_CALLS, tokens)

        return True, {
            "remaining_minute": minute_result.remaining,
            "remaining_daily": quota_result.remaining,
            "usage_percent": quota_result.usage_percent,
            "warning": quota_result.warning,
        }

    async def _get_rate_limit_config(self, tenant_id: str) -> Dict[str, int]:
        """Get rate limit configuration for tenant."""
        # Check cache
        cache_key = f"rate_limit_config:{tenant_id}"
        cached = await self.redis.get(cache_key)

        if cached:
            import json
            return json.loads(cached)

        # Default configs by tier
        tier_configs = {
            "free": {"requests_per_minute": 60, "requests_per_day": 1000},
            "starter": {"requests_per_minute": 300, "requests_per_day": 50000},
            "professional": {"requests_per_minute": 1000, "requests_per_day": 500000},
            "enterprise": {"requests_per_minute": 5000, "requests_per_day": 10000000},
        }

        # Get tenant tier
        db = self.quota.db_factory()
        try:
            result = db.execute(
                text("SELECT tier FROM tenants WHERE id = :id"),
                {"id": tenant_id}
            ).fetchone()

            tier = result.tier if result else "free"
            config = tier_configs.get(tier, tier_configs["free"])

            # Cache for 5 minutes
            import json
            await self.redis.setex(cache_key, 300, json.dumps(config))

            return config
        finally:
            db.close()
