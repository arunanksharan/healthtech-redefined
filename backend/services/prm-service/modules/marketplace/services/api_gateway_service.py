"""
API Gateway Service
Handles rate limiting, circuit breaker, and request/response management.
"""

import asyncio
import hashlib
import json
import time
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    APIKey,
    APIKeyStatus,
    APIUsageLog,
    OAuthApplication,
    OAuthToken,
    RateLimitBucket,
)
from ..schemas import (
    APIUsageLogCreate,
    APIUsageLogResponse,
    APIUsageSummary,
    RateLimitConfig,
    RateLimitStatus,
    UsageAnalytics,
)


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class RateLimitResult:
    """Result of rate limit check."""

    def __init__(
        self,
        allowed: bool,
        remaining: int,
        limit: int,
        reset_at: datetime,
        retry_after: Optional[int] = None
    ):
        self.allowed = allowed
        self.remaining = remaining
        self.limit = limit
        self.reset_at = reset_at
        self.retry_after = retry_after


class CircuitBreakerResult:
    """Result of circuit breaker check."""

    def __init__(
        self,
        allowed: bool,
        state: CircuitState,
        failure_count: int,
        last_failure: Optional[datetime] = None
    ):
        self.allowed = allowed
        self.state = state
        self.failure_count = failure_count
        self.last_failure = last_failure


class APIGatewayService:
    """
    API Gateway Service providing rate limiting, circuit breaker,
    request logging, and usage analytics.
    """

    # Default rate limit configurations by tier
    RATE_LIMIT_TIERS = {
        "free": RateLimitConfig(
            requests_per_minute=60,
            requests_per_hour=1000,
            requests_per_day=10000,
            burst_size=10,
            quota_monthly=100000
        ),
        "starter": RateLimitConfig(
            requests_per_minute=300,
            requests_per_hour=10000,
            requests_per_day=100000,
            burst_size=50,
            quota_monthly=1000000
        ),
        "professional": RateLimitConfig(
            requests_per_minute=1000,
            requests_per_hour=50000,
            requests_per_day=500000,
            burst_size=100,
            quota_monthly=10000000
        ),
        "enterprise": RateLimitConfig(
            requests_per_minute=5000,
            requests_per_hour=200000,
            requests_per_day=2000000,
            burst_size=500,
            quota_monthly=None  # Unlimited
        )
    }

    # Circuit breaker configuration
    CIRCUIT_BREAKER_CONFIG = {
        "failure_threshold": 5,  # Failures before opening
        "recovery_timeout": 30,  # Seconds before half-open
        "success_threshold": 3,  # Successes to close from half-open
        "timeout_seconds": 10,  # Request timeout
    }

    # In-memory circuit breaker state (should use Redis in production)
    _circuit_breakers: dict[str, dict] = {}

    async def check_rate_limit(
        self,
        db: AsyncSession,
        application_id: UUID,
        api_key_id: Optional[UUID] = None,
        endpoint: Optional[str] = None
    ) -> RateLimitResult:
        """
        Check and update rate limit for an application/API key.
        Uses sliding window algorithm.
        """
        now = datetime.utcnow()
        bucket_key = self._get_bucket_key(application_id, api_key_id, endpoint)

        # Get or create rate limit bucket
        result = await db.execute(
            select(RateLimitBucket).where(
                RateLimitBucket.bucket_key == bucket_key
            )
        )
        bucket = result.scalar_one_or_none()

        # Get rate limit config for the application
        config = await self._get_rate_limit_config(db, application_id)

        if not bucket:
            # Create new bucket
            bucket = RateLimitBucket(
                id=uuid4(),
                bucket_key=bucket_key,
                application_id=application_id,
                api_key_id=api_key_id,
                window_start=now,
                request_count=0,
                last_request_at=now
            )
            db.add(bucket)

        # Check if we need to reset the window (1 minute sliding window)
        window_duration = timedelta(minutes=1)
        if now - bucket.window_start > window_duration:
            # Reset window
            bucket.window_start = now
            bucket.request_count = 0

        # Calculate remaining requests
        limit = config.requests_per_minute
        remaining = max(0, limit - bucket.request_count)
        reset_at = bucket.window_start + window_duration

        # Check burst limit
        if bucket.request_count >= limit:
            # Check burst allowance
            burst_window = timedelta(seconds=1)
            if bucket.last_request_at and now - bucket.last_request_at < burst_window:
                retry_after = int((reset_at - now).total_seconds())
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    limit=limit,
                    reset_at=reset_at,
                    retry_after=max(1, retry_after)
                )

        # Allow request and increment counter
        bucket.request_count += 1
        bucket.last_request_at = now
        await db.commit()

        return RateLimitResult(
            allowed=True,
            remaining=max(0, remaining - 1),
            limit=limit,
            reset_at=reset_at
        )

    async def check_quota(
        self,
        db: AsyncSession,
        application_id: UUID
    ) -> tuple[bool, Optional[int], Optional[int]]:
        """
        Check monthly quota for an application.
        Returns (allowed, used, limit).
        """
        config = await self._get_rate_limit_config(db, application_id)

        if config.quota_monthly is None:
            return True, None, None  # Unlimited

        # Calculate current month usage
        month_start = datetime.utcnow().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        result = await db.execute(
            select(func.count(APIUsageLog.id)).where(
                and_(
                    APIUsageLog.application_id == application_id,
                    APIUsageLog.timestamp >= month_start
                )
            )
        )
        used = result.scalar() or 0

        return used < config.quota_monthly, used, config.quota_monthly

    async def check_circuit_breaker(
        self,
        service_name: str
    ) -> CircuitBreakerResult:
        """
        Check circuit breaker state for a downstream service.
        """
        now = datetime.utcnow()

        if service_name not in self._circuit_breakers:
            self._circuit_breakers[service_name] = {
                "state": CircuitState.CLOSED,
                "failure_count": 0,
                "success_count": 0,
                "last_failure": None,
                "last_state_change": now
            }

        cb = self._circuit_breakers[service_name]
        config = self.CIRCUIT_BREAKER_CONFIG

        if cb["state"] == CircuitState.OPEN:
            # Check if recovery timeout has passed
            time_since_open = (now - cb["last_state_change"]).total_seconds()
            if time_since_open >= config["recovery_timeout"]:
                # Transition to half-open
                cb["state"] = CircuitState.HALF_OPEN
                cb["success_count"] = 0
                cb["last_state_change"] = now
                return CircuitBreakerResult(
                    allowed=True,
                    state=CircuitState.HALF_OPEN,
                    failure_count=cb["failure_count"],
                    last_failure=cb["last_failure"]
                )
            else:
                return CircuitBreakerResult(
                    allowed=False,
                    state=CircuitState.OPEN,
                    failure_count=cb["failure_count"],
                    last_failure=cb["last_failure"]
                )

        return CircuitBreakerResult(
            allowed=True,
            state=cb["state"],
            failure_count=cb["failure_count"],
            last_failure=cb["last_failure"]
        )

    async def record_circuit_success(self, service_name: str) -> None:
        """Record a successful request for circuit breaker."""
        if service_name not in self._circuit_breakers:
            return

        cb = self._circuit_breakers[service_name]
        config = self.CIRCUIT_BREAKER_CONFIG

        if cb["state"] == CircuitState.HALF_OPEN:
            cb["success_count"] += 1
            if cb["success_count"] >= config["success_threshold"]:
                # Close the circuit
                cb["state"] = CircuitState.CLOSED
                cb["failure_count"] = 0
                cb["success_count"] = 0
                cb["last_state_change"] = datetime.utcnow()

    async def record_circuit_failure(self, service_name: str) -> None:
        """Record a failed request for circuit breaker."""
        now = datetime.utcnow()

        if service_name not in self._circuit_breakers:
            self._circuit_breakers[service_name] = {
                "state": CircuitState.CLOSED,
                "failure_count": 0,
                "success_count": 0,
                "last_failure": None,
                "last_state_change": now
            }

        cb = self._circuit_breakers[service_name]
        config = self.CIRCUIT_BREAKER_CONFIG

        cb["failure_count"] += 1
        cb["last_failure"] = now

        if cb["state"] == CircuitState.HALF_OPEN:
            # Any failure in half-open reopens the circuit
            cb["state"] = CircuitState.OPEN
            cb["last_state_change"] = now
        elif cb["state"] == CircuitState.CLOSED:
            if cb["failure_count"] >= config["failure_threshold"]:
                # Open the circuit
                cb["state"] = CircuitState.OPEN
                cb["last_state_change"] = now

    async def log_request(
        self,
        db: AsyncSession,
        application_id: UUID,
        data: APIUsageLogCreate
    ) -> APIUsageLogResponse:
        """
        Log an API request for analytics and auditing.
        """
        log_entry = APIUsageLog(
            id=uuid4(),
            application_id=application_id,
            api_key_id=data.api_key_id,
            tenant_id=data.tenant_id,
            user_id=data.user_id,
            endpoint=data.endpoint,
            method=data.method,
            status_code=data.status_code,
            response_time_ms=data.response_time_ms,
            request_size_bytes=data.request_size_bytes,
            response_size_bytes=data.response_size_bytes,
            ip_address=data.ip_address,
            user_agent=data.user_agent,
            error_code=data.error_code,
            error_message=data.error_message,
            timestamp=datetime.utcnow()
        )

        db.add(log_entry)
        await db.commit()
        await db.refresh(log_entry)

        return APIUsageLogResponse(
            id=log_entry.id,
            application_id=log_entry.application_id,
            api_key_id=log_entry.api_key_id,
            tenant_id=log_entry.tenant_id,
            endpoint=log_entry.endpoint,
            method=log_entry.method,
            status_code=log_entry.status_code,
            response_time_ms=log_entry.response_time_ms,
            timestamp=log_entry.timestamp
        )

    async def get_usage_summary(
        self,
        db: AsyncSession,
        application_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> APIUsageSummary:
        """
        Get usage summary for an application.
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        # Total requests
        total_result = await db.execute(
            select(func.count(APIUsageLog.id)).where(
                and_(
                    APIUsageLog.application_id == application_id,
                    APIUsageLog.timestamp >= start_date,
                    APIUsageLog.timestamp <= end_date
                )
            )
        )
        total_requests = total_result.scalar() or 0

        # Successful requests (2xx)
        success_result = await db.execute(
            select(func.count(APIUsageLog.id)).where(
                and_(
                    APIUsageLog.application_id == application_id,
                    APIUsageLog.timestamp >= start_date,
                    APIUsageLog.timestamp <= end_date,
                    APIUsageLog.status_code >= 200,
                    APIUsageLog.status_code < 300
                )
            )
        )
        successful_requests = success_result.scalar() or 0

        # Failed requests (4xx, 5xx)
        failed_result = await db.execute(
            select(func.count(APIUsageLog.id)).where(
                and_(
                    APIUsageLog.application_id == application_id,
                    APIUsageLog.timestamp >= start_date,
                    APIUsageLog.timestamp <= end_date,
                    APIUsageLog.status_code >= 400
                )
            )
        )
        failed_requests = failed_result.scalar() or 0

        # Average response time
        avg_result = await db.execute(
            select(func.avg(APIUsageLog.response_time_ms)).where(
                and_(
                    APIUsageLog.application_id == application_id,
                    APIUsageLog.timestamp >= start_date,
                    APIUsageLog.timestamp <= end_date
                )
            )
        )
        avg_response_time = avg_result.scalar() or 0

        # Get rate limit status
        config = await self._get_rate_limit_config(db, application_id)
        quota_allowed, quota_used, quota_limit = await self.check_quota(
            db, application_id
        )

        return APIUsageSummary(
            application_id=application_id,
            period_start=start_date,
            period_end=end_date,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time_ms=float(avg_response_time),
            quota_used=quota_used,
            quota_limit=quota_limit,
            rate_limit_config=config
        )

    async def get_usage_analytics(
        self,
        db: AsyncSession,
        application_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        granularity: str = "hour"
    ) -> UsageAnalytics:
        """
        Get detailed usage analytics with time series data.
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=7)
        if not end_date:
            end_date = datetime.utcnow()

        # Get summary first
        summary = await self.get_usage_summary(
            db, application_id, start_date, end_date
        )

        # Requests by endpoint
        endpoint_result = await db.execute(
            select(
                APIUsageLog.endpoint,
                func.count(APIUsageLog.id).label("count")
            ).where(
                and_(
                    APIUsageLog.application_id == application_id,
                    APIUsageLog.timestamp >= start_date,
                    APIUsageLog.timestamp <= end_date
                )
            ).group_by(APIUsageLog.endpoint).order_by(
                func.count(APIUsageLog.id).desc()
            ).limit(20)
        )
        requests_by_endpoint = {
            row.endpoint: row.count for row in endpoint_result.fetchall()
        }

        # Requests by status code
        status_result = await db.execute(
            select(
                APIUsageLog.status_code,
                func.count(APIUsageLog.id).label("count")
            ).where(
                and_(
                    APIUsageLog.application_id == application_id,
                    APIUsageLog.timestamp >= start_date,
                    APIUsageLog.timestamp <= end_date
                )
            ).group_by(APIUsageLog.status_code)
        )
        requests_by_status = {
            str(row.status_code): row.count for row in status_result.fetchall()
        }

        # Response time percentiles (simplified - would use proper percentile functions)
        p50_result = await db.execute(
            select(func.percentile_cont(0.5).within_group(
                APIUsageLog.response_time_ms
            )).where(
                and_(
                    APIUsageLog.application_id == application_id,
                    APIUsageLog.timestamp >= start_date,
                    APIUsageLog.timestamp <= end_date
                )
            )
        )
        p50 = p50_result.scalar() or 0

        p95_result = await db.execute(
            select(func.percentile_cont(0.95).within_group(
                APIUsageLog.response_time_ms
            )).where(
                and_(
                    APIUsageLog.application_id == application_id,
                    APIUsageLog.timestamp >= start_date,
                    APIUsageLog.timestamp <= end_date
                )
            )
        )
        p95 = p95_result.scalar() or 0

        p99_result = await db.execute(
            select(func.percentile_cont(0.99).within_group(
                APIUsageLog.response_time_ms
            )).where(
                and_(
                    APIUsageLog.application_id == application_id,
                    APIUsageLog.timestamp >= start_date,
                    APIUsageLog.timestamp <= end_date
                )
            )
        )
        p99 = p99_result.scalar() or 0

        # Top errors
        error_result = await db.execute(
            select(
                APIUsageLog.error_code,
                APIUsageLog.error_message,
                func.count(APIUsageLog.id).label("count")
            ).where(
                and_(
                    APIUsageLog.application_id == application_id,
                    APIUsageLog.timestamp >= start_date,
                    APIUsageLog.timestamp <= end_date,
                    APIUsageLog.error_code.isnot(None)
                )
            ).group_by(
                APIUsageLog.error_code, APIUsageLog.error_message
            ).order_by(
                func.count(APIUsageLog.id).desc()
            ).limit(10)
        )
        top_errors = [
            {
                "code": row.error_code,
                "message": row.error_message,
                "count": row.count
            }
            for row in error_result.fetchall()
        ]

        return UsageAnalytics(
            summary=summary,
            requests_by_endpoint=requests_by_endpoint,
            requests_by_status=requests_by_status,
            response_time_p50_ms=float(p50),
            response_time_p95_ms=float(p95),
            response_time_p99_ms=float(p99),
            top_errors=top_errors,
            time_series=[]  # Would implement with date_trunc grouping
        )

    async def get_rate_limit_status(
        self,
        db: AsyncSession,
        application_id: UUID,
        api_key_id: Optional[UUID] = None
    ) -> RateLimitStatus:
        """
        Get current rate limit status for an application/API key.
        """
        bucket_key = self._get_bucket_key(application_id, api_key_id)

        result = await db.execute(
            select(RateLimitBucket).where(
                RateLimitBucket.bucket_key == bucket_key
            )
        )
        bucket = result.scalar_one_or_none()

        config = await self._get_rate_limit_config(db, application_id)
        now = datetime.utcnow()

        if not bucket:
            return RateLimitStatus(
                requests_remaining=config.requests_per_minute,
                requests_limit=config.requests_per_minute,
                window_reset_at=now + timedelta(minutes=1),
                quota_remaining=config.quota_monthly,
                quota_limit=config.quota_monthly
            )

        # Check if window needs reset
        window_duration = timedelta(minutes=1)
        if now - bucket.window_start > window_duration:
            requests_used = 0
        else:
            requests_used = bucket.request_count

        # Get quota status
        quota_allowed, quota_used, quota_limit = await self.check_quota(
            db, application_id
        )

        return RateLimitStatus(
            requests_remaining=max(0, config.requests_per_minute - requests_used),
            requests_limit=config.requests_per_minute,
            window_reset_at=bucket.window_start + window_duration,
            quota_remaining=quota_limit - quota_used if quota_limit else None,
            quota_limit=quota_limit
        )

    async def validate_api_key(
        self,
        db: AsyncSession,
        api_key: str
    ) -> Optional[tuple[UUID, UUID, list[str]]]:
        """
        Validate an API key and return (application_id, api_key_id, scopes).
        Returns None if invalid.
        """
        # Hash the key prefix for lookup
        key_prefix = api_key[:16] if len(api_key) >= 16 else api_key
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        result = await db.execute(
            select(APIKey).where(
                and_(
                    APIKey.key_prefix == key_prefix,
                    APIKey.key_hash == key_hash,
                    APIKey.status == APIKeyStatus.ACTIVE
                )
            )
        )
        api_key_obj = result.scalar_one_or_none()

        if not api_key_obj:
            return None

        # Check expiration
        if api_key_obj.expires_at and api_key_obj.expires_at < datetime.utcnow():
            return None

        # Update last used
        api_key_obj.last_used_at = datetime.utcnow()
        await db.commit()

        return (
            api_key_obj.application_id,
            api_key_obj.id,
            api_key_obj.allowed_scopes or []
        )

    async def validate_bearer_token(
        self,
        db: AsyncSession,
        token: str
    ) -> Optional[dict[str, Any]]:
        """
        Validate a bearer token and return token claims.
        Returns None if invalid.
        """
        # Hash token for lookup
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        result = await db.execute(
            select(OAuthToken).where(
                and_(
                    OAuthToken.access_token_hash == token_hash,
                    OAuthToken.revoked_at.is_(None)
                )
            )
        )
        token_obj = result.scalar_one_or_none()

        if not token_obj:
            return None

        # Check expiration
        if token_obj.access_token_expires_at < datetime.utcnow():
            return None

        return {
            "application_id": token_obj.application_id,
            "tenant_id": token_obj.tenant_id,
            "user_id": token_obj.user_id,
            "patient_id": token_obj.patient_id,
            "scopes": token_obj.scopes or [],
            "token_id": token_obj.id
        }

    async def _get_rate_limit_config(
        self,
        db: AsyncSession,
        application_id: UUID
    ) -> RateLimitConfig:
        """Get rate limit configuration for an application."""
        # Get application to check tier
        result = await db.execute(
            select(OAuthApplication).where(
                OAuthApplication.id == application_id
            )
        )
        app = result.scalar_one_or_none()

        if not app:
            return self.RATE_LIMIT_TIERS["free"]

        # Check app metadata for tier
        tier = "free"
        if app.metadata:
            tier = app.metadata.get("tier", "free")

        return self.RATE_LIMIT_TIERS.get(tier, self.RATE_LIMIT_TIERS["free"])

    def _get_bucket_key(
        self,
        application_id: UUID,
        api_key_id: Optional[UUID] = None,
        endpoint: Optional[str] = None
    ) -> str:
        """Generate a unique bucket key for rate limiting."""
        parts = [str(application_id)]
        if api_key_id:
            parts.append(str(api_key_id))
        if endpoint:
            parts.append(endpoint)
        return ":".join(parts)


# Middleware helper functions
async def rate_limit_middleware(
    gateway: APIGatewayService,
    db: AsyncSession,
    application_id: UUID,
    api_key_id: Optional[UUID] = None,
    endpoint: Optional[str] = None
) -> dict[str, Any]:
    """
    Middleware helper to check rate limits.
    Returns headers to include in response.
    """
    result = await gateway.check_rate_limit(
        db, application_id, api_key_id, endpoint
    )

    headers = {
        "X-RateLimit-Limit": str(result.limit),
        "X-RateLimit-Remaining": str(result.remaining),
        "X-RateLimit-Reset": result.reset_at.isoformat()
    }

    if not result.allowed:
        headers["Retry-After"] = str(result.retry_after)

    return {
        "allowed": result.allowed,
        "headers": headers,
        "retry_after": result.retry_after
    }


async def circuit_breaker_middleware(
    gateway: APIGatewayService,
    service_name: str
) -> dict[str, Any]:
    """
    Middleware helper to check circuit breaker.
    """
    result = await gateway.check_circuit_breaker(service_name)

    return {
        "allowed": result.allowed,
        "state": result.state.value,
        "failure_count": result.failure_count
    }
