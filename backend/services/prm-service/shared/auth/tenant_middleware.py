"""
Tenant Middleware

EPIC-004: Multi-Tenancy Implementation

Provides automatic tenant resolution and context injection:
- Subdomain resolution (tenant.example.com)
- Header-based resolution (X-Tenant-ID)
- API key resolution
- JWT token resolution
- Rate limiting per tenant
- Request scoping

"""

import time
import logging
from datetime import datetime, timezone
from typing import Callable, Optional, Dict, Any, List
from uuid import UUID

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from ..database.tenant_context import (
    TenantContext,
    TenantStatus,
    set_tenant_context,
    clear_tenant_context,
    get_current_tenant,
)
from ..database.tenant_service import TenantServiceImpl
from .jwt import verify_token

logger = logging.getLogger(__name__)


# Paths that don't require tenant context
PUBLIC_PATHS = [
    "/",
    "/health",
    "/healthz",
    "/ready",
    "/readyz",
    "/metrics",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
    "/api/v1/auth/forgot-password",
    "/api/v1/auth/reset-password",
    "/api/v1/tenants/signup",  # New tenant signup
    "/api/v1/webhooks",  # Webhook endpoints handle their own auth
]

# Paths that bypass tenant check but may still use tenant context
OPTIONAL_TENANT_PATHS = [
    "/api/v1/admin",  # Super admin paths
]


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic tenant resolution and context injection.

    Resolution order:
    1. JWT token claim (for authenticated requests)
    2. X-Tenant-ID header (for server-to-server)
    3. API key (X-API-Key header)
    4. Subdomain (tenant.example.com)

    Features:
    - Automatic tenant context injection
    - Request-scoped tenant isolation
    - Rate limiting support
    - Audit logging support
    """

    def __init__(
        self,
        app: ASGIApp,
        db_session_factory: Callable,
        cache_manager=None,
        rate_limiter=None,
        exclude_paths: Optional[List[str]] = None,
    ):
        super().__init__(app)
        self.db_session_factory = db_session_factory
        self.cache = cache_manager
        self.rate_limiter = rate_limiter
        self.exclude_paths = exclude_paths or []

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint
    ) -> Response:
        """Process request with tenant context."""
        start_time = time.time()
        tenant_context: Optional[TenantContext] = None

        try:
            # Check if path is excluded
            path = request.url.path
            if self._is_excluded_path(path):
                return await call_next(request)

            # Try to resolve tenant
            tenant_id = await self._resolve_tenant(request)

            if tenant_id:
                # Get full tenant context
                db = self.db_session_factory()
                try:
                    service = TenantServiceImpl(db, self.cache)
                    tenant_context = await service.get_tenant_context(tenant_id)

                    if tenant_context:
                        # Check tenant status
                        if not tenant_context.is_active():
                            return JSONResponse(
                                status_code=status.HTTP_403_FORBIDDEN,
                                content={
                                    "error": "tenant_inactive",
                                    "message": f"Tenant is {tenant_context.status.value}",
                                    "tenant_id": tenant_id,
                                }
                            )

                        # Set tenant context for the request
                        set_tenant_context(tenant_context)

                        # Store in request state for downstream use
                        request.state.tenant_id = tenant_id
                        request.state.tenant_context = tenant_context

                        # Set database tenant context
                        from ..database.tenant_context import setup_tenant_rls
                        setup_tenant_rls(db, tenant_id)

                        # Check rate limit if enabled
                        if self.rate_limiter:
                            allowed, retry_after = await self._check_rate_limit(
                                tenant_id, request
                            )
                            if not allowed:
                                return JSONResponse(
                                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                                    content={
                                        "error": "rate_limit_exceeded",
                                        "message": "Too many requests",
                                        "retry_after": retry_after,
                                    },
                                    headers={"Retry-After": str(retry_after)}
                                )
                finally:
                    db.close()
            else:
                # No tenant found - check if required
                if not self._is_optional_tenant_path(path):
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={
                            "error": "tenant_required",
                            "message": "Tenant context is required for this endpoint",
                            "hint": "Provide tenant via Authorization header, X-Tenant-ID header, or X-API-Key",
                        }
                    )

            # Process request
            response = await call_next(request)

            # Add tenant headers to response
            if tenant_context:
                response.headers["X-Tenant-ID"] = tenant_context.tenant_id
                response.headers["X-Tenant-Tier"] = tenant_context.tier.value

            # Track request timing
            duration_ms = (time.time() - start_time) * 1000
            response.headers["X-Request-Duration-Ms"] = f"{duration_ms:.2f}"

            # Track usage (async, fire-and-forget)
            if tenant_context:
                await self._track_usage(tenant_context.tenant_id)

            return response

        except HTTPException as e:
            raise e
        except Exception as e:
            logger.exception(f"Error in tenant middleware: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "internal_error",
                    "message": "An internal error occurred",
                }
            )
        finally:
            # Clear tenant context
            clear_tenant_context()

    async def _resolve_tenant(self, request: Request) -> Optional[str]:
        """
        Resolve tenant from various sources.

        Resolution order:
        1. JWT token
        2. X-Tenant-ID header
        3. API key
        4. Subdomain
        """
        # 1. Try JWT token
        tenant_id = await self._resolve_from_jwt(request)
        if tenant_id:
            return tenant_id

        # 2. Try X-Tenant-ID header
        tenant_id = request.headers.get("X-Tenant-ID") or request.headers.get("x-tenant-id")
        if tenant_id:
            return tenant_id

        # 3. Try API key
        tenant_id = await self._resolve_from_api_key(request)
        if tenant_id:
            return tenant_id

        # 4. Try subdomain
        tenant_id = await self._resolve_from_subdomain(request)
        if tenant_id:
            return tenant_id

        return None

    async def _resolve_from_jwt(self, request: Request) -> Optional[str]:
        """Resolve tenant from JWT token."""
        auth_header = request.headers.get("Authorization") or request.headers.get("authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header[7:]  # Remove "Bearer " prefix

        try:
            payload = verify_token(token)
            if payload:
                return payload.get("tenant_id") or payload.get("tenantId")
        except Exception as e:
            logger.debug(f"JWT verification failed: {e}")

        return None

    async def _resolve_from_api_key(self, request: Request) -> Optional[str]:
        """Resolve tenant from API key."""
        api_key = request.headers.get("X-API-Key") or request.headers.get("x-api-key")

        if not api_key:
            return None

        # Check cache first
        if self.cache:
            cached = await self.cache.get(f"api_key:{api_key[:12]}")
            if cached:
                return cached.get("tenant_id")

        # Validate against database
        db = self.db_session_factory()
        try:
            service = TenantServiceImpl(db, self.cache)
            result = await service.validate_api_key(api_key)

            if result:
                tenant_id, scopes, rate_limit = result

                # Cache for future requests
                if self.cache:
                    await self.cache.set(
                        f"api_key:{api_key[:12]}",
                        {"tenant_id": tenant_id, "scopes": scopes, "rate_limit": rate_limit},
                        ttl=300  # 5 minutes
                    )

                # Store scopes in request state
                request.state.api_key_scopes = scopes
                request.state.api_key_rate_limit = rate_limit

                return tenant_id
        finally:
            db.close()

        return None

    async def _resolve_from_subdomain(self, request: Request) -> Optional[str]:
        """Resolve tenant from subdomain."""
        host = request.headers.get("host", "")

        if not host:
            return None

        # Parse subdomain
        parts = host.split(".")

        # Need at least subdomain.domain.tld
        if len(parts) < 3:
            return None

        subdomain = parts[0]

        # Skip common subdomains
        if subdomain in ["www", "api", "admin", "app", "localhost"]:
            return None

        # Look up tenant by slug
        if self.cache:
            cached = await self.cache.get(f"tenant_slug:{subdomain}")
            if cached:
                return cached

        db = self.db_session_factory()
        try:
            service = TenantServiceImpl(db, self.cache)
            tenant = await service.get_tenant_by_slug(subdomain)

            if tenant:
                # Cache the mapping
                if self.cache:
                    await self.cache.set(
                        f"tenant_slug:{subdomain}",
                        tenant.id,
                        ttl=3600  # 1 hour
                    )
                return tenant.id
        finally:
            db.close()

        return None

    async def _check_rate_limit(
        self,
        tenant_id: str,
        request: Request
    ) -> tuple[bool, int]:
        """
        Check rate limit for tenant.

        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        if not self.rate_limiter:
            return True, 0

        # Get rate limit from API key or tenant tier
        rate_limit = getattr(request.state, "api_key_rate_limit", None)

        if not rate_limit:
            # Get from tenant context
            context = getattr(request.state, "tenant_context", None)
            if context:
                rate_limit = context.limits.max_api_calls_per_day // (24 * 60)  # Per minute

        if not rate_limit:
            rate_limit = 100  # Default

        # Check rate limit
        return await self.rate_limiter.check(
            key=f"tenant:{tenant_id}:api",
            limit=rate_limit,
            window=60  # 1 minute window
        )

    async def _track_usage(self, tenant_id: str):
        """Track API usage for tenant."""
        try:
            if self.cache:
                # Increment counter in Redis
                key = f"usage:{tenant_id}:{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
                await self.cache.incr(key)
                await self.cache.expire(key, 86400 * 2)  # Keep for 2 days
        except Exception as e:
            logger.debug(f"Failed to track usage: {e}")

    def _is_excluded_path(self, path: str) -> bool:
        """Check if path is excluded from tenant resolution."""
        # Check exact matches
        if path in PUBLIC_PATHS:
            return True

        # Check prefixes
        for excluded in PUBLIC_PATHS + self.exclude_paths:
            if excluded.endswith("*") and path.startswith(excluded[:-1]):
                return True

        return False

    def _is_optional_tenant_path(self, path: str) -> bool:
        """Check if tenant is optional for this path."""
        for optional in OPTIONAL_TENANT_PATHS:
            if path.startswith(optional):
                return True
        return False


class TenantRateLimiter:
    """
    Token bucket rate limiter for tenants.

    Uses Redis for distributed rate limiting.
    """

    def __init__(self, redis_client):
        self.redis = redis_client

    async def check(
        self,
        key: str,
        limit: int,
        window: int = 60
    ) -> tuple[bool, int]:
        """
        Check if request is allowed.

        Args:
            key: Rate limit key
            limit: Maximum requests per window
            window: Window size in seconds

        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        now = time.time()
        window_start = now - window

        # Use Redis sorted set for sliding window
        pipe = self.redis.pipeline()

        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)

        # Count current entries
        pipe.zcard(key)

        # Add new entry
        pipe.zadd(key, {str(now): now})

        # Set expiry
        pipe.expire(key, window * 2)

        results = await pipe.execute()
        current_count = results[1]

        if current_count >= limit:
            # Calculate retry after
            oldest = await self.redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                retry_after = int(oldest[0][1] + window - now) + 1
            else:
                retry_after = window
            return False, retry_after

        return True, 0

    async def get_remaining(self, key: str, limit: int, window: int = 60) -> int:
        """Get remaining requests in current window."""
        now = time.time()
        window_start = now - window

        await self.redis.zremrangebyscore(key, 0, window_start)
        current_count = await self.redis.zcard(key)

        return max(0, limit - current_count)


# =============================================================================
# FASTAPI DEPENDENCIES
# =============================================================================


async def get_tenant_id(request: Request) -> str:
    """FastAPI dependency to get current tenant ID."""
    tenant_id = getattr(request.state, "tenant_id", None) or get_current_tenant()

    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context not found"
        )

    return tenant_id


async def get_tenant_context(request: Request) -> TenantContext:
    """FastAPI dependency to get current tenant context."""
    context = getattr(request.state, "tenant_context", None)

    if not context:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context not found"
        )

    return context


def require_feature(feature: str):
    """
    Dependency factory to require a specific feature.

    Usage:
        @app.get("/ai/chat", dependencies=[Depends(require_feature("ai_features"))])
    """
    async def check_feature(context: TenantContext = Depends(get_tenant_context)):
        if not context.has_feature(feature):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Feature '{feature}' is not available for your plan. Please upgrade."
            )
        return True

    return check_feature


def require_tenant_active():
    """Dependency to require tenant to be active."""
    async def check_active(context: TenantContext = Depends(get_tenant_context)):
        if not context.is_active():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tenant is {context.status.value}"
            )
        return True

    return check_active


# Import Depends here to avoid circular imports
from fastapi import Depends


# =============================================================================
# REQUEST CONTEXT HELPERS
# =============================================================================


def get_request_metadata(request: Request) -> Dict[str, Any]:
    """Get metadata from request for audit logging."""
    return {
        "ip_address": get_client_ip(request),
        "user_agent": request.headers.get("user-agent"),
        "request_id": request.headers.get("x-request-id"),
        "method": request.method,
        "path": request.url.path,
        "query_params": dict(request.query_params),
    }


def get_client_ip(request: Request) -> str:
    """Get client IP from request, handling proxies."""
    # Check X-Forwarded-For
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()

    # Check X-Real-IP
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip

    # Fallback to client host
    if request.client:
        return request.client.host

    return "unknown"
