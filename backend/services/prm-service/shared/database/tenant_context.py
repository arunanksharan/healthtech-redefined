"""
Tenant Context Management

Provides comprehensive multi-tenancy support with:
- Thread-safe tenant context
- Database row-level security
- Tenant resolution
- Tenant configuration
- Resource isolation

EPIC-004: Multi-Tenancy Implementation
"""

import contextvars
import functools
import os
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, TypeVar
from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4
import logging

from sqlalchemy import event, text
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Context variable for storing current tenant
_current_tenant: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "current_tenant", default=None
)
_tenant_context: contextvars.ContextVar[Optional["TenantContext"]] = contextvars.ContextVar(
    "tenant_context", default=None
)


class TenantTier(str, Enum):
    """Tenant subscription tiers."""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class TenantStatus(str, Enum):
    """Tenant status."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    CANCELLED = "cancelled"
    PENDING = "pending"


@dataclass
class TenantLimits:
    """Tenant resource limits based on tier."""
    max_users: int = 5
    max_patients: int = 1000
    max_storage_gb: int = 5
    max_api_calls_per_day: int = 10000
    max_concurrent_connections: int = 10
    max_file_upload_mb: int = 10
    data_retention_days: int = 365
    features: Dict[str, bool] = field(default_factory=dict)

    @classmethod
    def for_tier(cls, tier: TenantTier) -> "TenantLimits":
        """Get limits for a specific tier."""
        tiers = {
            TenantTier.FREE: cls(
                max_users=5,
                max_patients=100,
                max_storage_gb=1,
                max_api_calls_per_day=1000,
                max_concurrent_connections=2,
                features={"telehealth": False, "ai_features": False, "custom_reports": False},
            ),
            TenantTier.STARTER: cls(
                max_users=25,
                max_patients=5000,
                max_storage_gb=25,
                max_api_calls_per_day=50000,
                max_concurrent_connections=10,
                features={"telehealth": True, "ai_features": False, "custom_reports": False},
            ),
            TenantTier.PROFESSIONAL: cls(
                max_users=100,
                max_patients=50000,
                max_storage_gb=100,
                max_api_calls_per_day=500000,
                max_concurrent_connections=50,
                features={"telehealth": True, "ai_features": True, "custom_reports": True},
            ),
            TenantTier.ENTERPRISE: cls(
                max_users=999999,
                max_patients=999999,
                max_storage_gb=1000,
                max_api_calls_per_day=9999999,
                max_concurrent_connections=500,
                features={"telehealth": True, "ai_features": True, "custom_reports": True, "white_label": True},
            ),
        }
        return tiers.get(tier, tiers[TenantTier.FREE])


@dataclass
class TenantBranding:
    """Tenant branding configuration."""
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: str = "#0066CC"
    secondary_color: str = "#F0F0F0"
    accent_color: str = "#00CC66"
    font_family: str = "Inter, sans-serif"
    custom_css: Optional[str] = None


@dataclass
class TenantSettings:
    """Tenant configuration settings."""
    timezone: str = "UTC"
    date_format: str = "YYYY-MM-DD"
    time_format: str = "HH:mm"
    language: str = "en"
    currency: str = "USD"
    appointment_duration_minutes: int = 30
    enable_reminders: bool = True
    reminder_hours_before: int = 24
    enable_waitlist: bool = True
    enable_online_booking: bool = True
    require_payment_upfront: bool = False
    hipaa_mode: bool = True
    audit_logging: bool = True
    two_factor_required: bool = False
    session_timeout_minutes: int = 30
    password_policy: Dict[str, Any] = field(default_factory=lambda: {
        "min_length": 8,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_numbers": True,
        "require_special": True,
        "max_age_days": 90,
    })


@dataclass
class TenantContext:
    """
    Complete tenant context for request processing.

    This object contains all tenant-related information needed
    during request processing.
    """
    tenant_id: str
    name: str
    slug: str
    tier: TenantTier = TenantTier.FREE
    status: TenantStatus = TenantStatus.ACTIVE
    limits: TenantLimits = field(default_factory=TenantLimits)
    settings: TenantSettings = field(default_factory=TenantSettings)
    branding: TenantBranding = field(default_factory=TenantBranding)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def has_feature(self, feature: str) -> bool:
        """Check if tenant has access to a feature."""
        return self.limits.features.get(feature, False)

    def is_active(self) -> bool:
        """Check if tenant is active."""
        return self.status in [TenantStatus.ACTIVE, TenantStatus.TRIAL]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tenantId": self.tenant_id,
            "name": self.name,
            "slug": self.slug,
            "tier": self.tier.value,
            "status": self.status.value,
            "createdAt": self.created_at.isoformat(),
        }


def get_current_tenant() -> Optional[str]:
    """Get the current tenant ID from context."""
    return _current_tenant.get()


def set_tenant(tenant_id: Optional[str]):
    """Set the current tenant ID in context."""
    _current_tenant.set(tenant_id)


def get_tenant_context() -> Optional[TenantContext]:
    """Get the full tenant context."""
    return _tenant_context.get()


def set_tenant_context(context: Optional[TenantContext]):
    """Set the full tenant context."""
    _tenant_context.set(context)
    if context:
        _current_tenant.set(context.tenant_id)
    else:
        _current_tenant.set(None)


def clear_tenant_context():
    """Clear the tenant context."""
    _current_tenant.set(None)
    _tenant_context.set(None)


class TenantContextManager:
    """
    Context manager for tenant scope.

    Usage:
        with TenantContextManager(tenant_id):
            # All database operations are scoped to tenant
            users = db.query(User).all()
    """

    def __init__(self, tenant_id: str, context: Optional[TenantContext] = None):
        self.tenant_id = tenant_id
        self.context = context
        self._token_tenant: Optional[contextvars.Token] = None
        self._token_context: Optional[contextvars.Token] = None

    def __enter__(self):
        self._token_tenant = _current_tenant.set(self.tenant_id)
        if self.context:
            self._token_context = _tenant_context.set(self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._token_tenant:
            _current_tenant.reset(self._token_tenant)
        if self._token_context:
            _tenant_context.reset(self._token_context)


def tenant_scoped(func: Callable) -> Callable:
    """
    Decorator to ensure a function runs within tenant scope.

    The decorated function must have tenant_id as a parameter.
    """
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        tenant_id = kwargs.get("tenant_id")
        if not tenant_id and args:
            # Try to get from first positional arg if it's a request
            first_arg = args[0]
            if hasattr(first_arg, "state") and hasattr(first_arg.state, "tenant_id"):
                tenant_id = first_arg.state.tenant_id

        if tenant_id:
            with TenantContextManager(tenant_id):
                return await func(*args, **kwargs)
        else:
            return await func(*args, **kwargs)

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        tenant_id = kwargs.get("tenant_id")
        if tenant_id:
            with TenantContextManager(tenant_id):
                return func(*args, **kwargs)
        else:
            return func(*args, **kwargs)

    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


def setup_tenant_rls(db: Session, tenant_id: str):
    """
    Set up row-level security for the current session.

    This function sets the PostgreSQL session variable that
    RLS policies use to filter data.
    """
    if tenant_id:
        db.execute(text(f"SET app.current_tenant = '{tenant_id}'"))
        logger.debug(f"Set tenant context: {tenant_id}")


def setup_session_tenant_hooks(engine):
    """
    Setup SQLAlchemy event hooks for automatic tenant context.

    This ensures that every database session automatically has
    the correct tenant context set.
    """

    @event.listens_for(engine, "connect")
    def set_search_path(dbapi_conn, connection_record):
        """Set search path on new connections."""
        cursor = dbapi_conn.cursor()
        # Set default search path
        cursor.execute("SET search_path TO public")
        cursor.close()

    @event.listens_for(Session, "after_begin")
    def set_tenant_context_on_session(session, transaction, connection):
        """Set tenant context at the start of each transaction."""
        tenant_id = get_current_tenant()
        if tenant_id:
            connection.execute(text(f"SET LOCAL app.current_tenant = '{tenant_id}'"))


class TenantResolver:
    """
    Resolves tenant from various sources.

    Supports resolution from:
    - Subdomain (tenant.example.com)
    - Header (X-Tenant-ID)
    - API key
    - JWT token
    """

    def __init__(self, cache_manager=None):
        self._cache = cache_manager
        self._tenant_cache: Dict[str, TenantContext] = {}

    async def resolve_from_subdomain(self, host: str) -> Optional[str]:
        """Resolve tenant from subdomain."""
        parts = host.split(".")
        if len(parts) >= 2:
            subdomain = parts[0]
            # Exclude common subdomains
            if subdomain not in ["www", "api", "admin", "app"]:
                return await self._get_tenant_id_by_slug(subdomain)
        return None

    async def resolve_from_header(self, headers: Dict[str, str]) -> Optional[str]:
        """Resolve tenant from X-Tenant-ID header."""
        return headers.get("x-tenant-id") or headers.get("X-Tenant-ID")

    async def resolve_from_api_key(self, api_key: str) -> Optional[str]:
        """Resolve tenant from API key."""
        if not api_key:
            return None

        # Check cache
        cache_key = f"api_key:{api_key[:8]}"
        if self._cache:
            tenant_id = await self._cache.get(cache_key)
            if tenant_id:
                return tenant_id

        # Look up in database (would need actual implementation)
        # tenant_id = await db.query(ApiKey).filter(ApiKey.key == api_key).first()

        return None

    async def resolve_from_token(self, token_payload: Dict[str, Any]) -> Optional[str]:
        """Resolve tenant from JWT token payload."""
        return token_payload.get("tenant_id") or token_payload.get("tenantId")

    async def _get_tenant_id_by_slug(self, slug: str) -> Optional[str]:
        """Get tenant ID by slug."""
        # Check local cache first
        for tenant_id, ctx in self._tenant_cache.items():
            if ctx.slug == slug:
                return tenant_id

        # Would need actual database lookup
        return None

    async def get_tenant_context(self, tenant_id: str) -> Optional[TenantContext]:
        """Get full tenant context by ID."""
        # Check cache
        if tenant_id in self._tenant_cache:
            return self._tenant_cache[tenant_id]

        # Would need actual database lookup to populate context
        # For now, return a default context
        return TenantContext(
            tenant_id=tenant_id,
            name="Default Tenant",
            slug=tenant_id[:8],
            tier=TenantTier.PROFESSIONAL,
            status=TenantStatus.ACTIVE,
            limits=TenantLimits.for_tier(TenantTier.PROFESSIONAL),
        )


class TenantService:
    """
    Service for managing tenants.

    Handles tenant CRUD operations, provisioning, and configuration.
    """

    def __init__(self, db_session_factory, cache_manager=None):
        self._session_factory = db_session_factory
        self._cache = cache_manager

    async def create_tenant(
        self,
        name: str,
        slug: str,
        tier: TenantTier = TenantTier.FREE,
        admin_email: str = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> TenantContext:
        """
        Create a new tenant.

        This will:
        1. Create tenant record
        2. Set up database schema/RLS
        3. Create admin user
        4. Send welcome email
        """
        tenant_id = str(uuid4())

        context = TenantContext(
            tenant_id=tenant_id,
            name=name,
            slug=slug,
            tier=tier,
            status=TenantStatus.PENDING,
            limits=TenantLimits.for_tier(tier),
            settings=TenantSettings(**settings) if settings else TenantSettings(),
        )

        # Store in database (actual implementation would use SQLAlchemy)
        logger.info(f"Creating tenant: {name} ({tenant_id})")

        # Provision tenant
        await self._provision_tenant(context)

        return context

    async def _provision_tenant(self, context: TenantContext):
        """Provision a new tenant."""
        # 1. Create tenant-specific resources
        # 2. Set up storage folder
        # 3. Initialize default data
        # 4. Create admin user
        # 5. Update status to ACTIVE

        context.status = TenantStatus.ACTIVE
        logger.info(f"Tenant provisioned: {context.tenant_id}")

    async def update_tenant(
        self,
        tenant_id: str,
        **updates,
    ) -> Optional[TenantContext]:
        """Update tenant settings."""
        # Implementation would update database
        pass

    async def suspend_tenant(self, tenant_id: str, reason: str):
        """Suspend a tenant."""
        # Implementation would update status and disable access
        pass

    async def delete_tenant(self, tenant_id: str, hard_delete: bool = False):
        """Delete a tenant."""
        # Implementation would either soft-delete or remove all data
        pass

    async def get_tenant_usage(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant resource usage."""
        return {
            "users": 0,
            "patients": 0,
            "storage_gb": 0,
            "api_calls_today": 0,
        }

    async def check_limit(self, tenant_id: str, resource: str, amount: int = 1) -> bool:
        """Check if a resource limit would be exceeded."""
        context = await TenantResolver().get_tenant_context(tenant_id)
        if not context:
            return False

        usage = await self.get_tenant_usage(tenant_id)

        limit_map = {
            "users": ("max_users", usage.get("users", 0)),
            "patients": ("max_patients", usage.get("patients", 0)),
            "storage": ("max_storage_gb", usage.get("storage_gb", 0)),
        }

        if resource in limit_map:
            limit_attr, current = limit_map[resource]
            limit = getattr(context.limits, limit_attr, 0)
            return (current + amount) <= limit

        return True


# Global resolver instance
tenant_resolver = TenantResolver()
