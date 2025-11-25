"""
Multi-Tenancy Test Suite

EPIC-004: Multi-Tenancy Implementation

Comprehensive tests covering:
- Tenant data isolation
- Tenant provisioning
- Configuration management
- Resource quotas
- Rate limiting
- Audit logging
- Data export/import
- Security
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4

# Test tenant context
from shared.database.tenant_context import (
    TenantContext,
    TenantContextManager,
    TenantTier,
    TenantStatus,
    TenantLimits,
    TenantSettings,
    TenantBranding,
    get_current_tenant,
    set_tenant,
    get_tenant_context,
    set_tenant_context,
    clear_tenant_context,
    tenant_scoped,
)


class TestTenantContext:
    """Tests for tenant context management."""

    def test_tenant_tier_values(self):
        """Test tenant tier enum values."""
        assert TenantTier.FREE.value == "free"
        assert TenantTier.STARTER.value == "starter"
        assert TenantTier.PROFESSIONAL.value == "professional"
        assert TenantTier.ENTERPRISE.value == "enterprise"

    def test_tenant_status_values(self):
        """Test tenant status enum values."""
        assert TenantStatus.ACTIVE.value == "active"
        assert TenantStatus.SUSPENDED.value == "suspended"
        assert TenantStatus.TRIAL.value == "trial"
        assert TenantStatus.CANCELLED.value == "cancelled"
        assert TenantStatus.PENDING.value == "pending"

    def test_tenant_limits_for_tier_free(self):
        """Test free tier limits."""
        limits = TenantLimits.for_tier(TenantTier.FREE)
        assert limits.max_users == 5
        assert limits.max_patients == 100
        assert limits.max_storage_gb == 1
        assert limits.max_api_calls_per_day == 1000
        assert limits.features.get("telehealth") is False
        assert limits.features.get("ai_features") is False

    def test_tenant_limits_for_tier_professional(self):
        """Test professional tier limits."""
        limits = TenantLimits.for_tier(TenantTier.PROFESSIONAL)
        assert limits.max_users == 100
        assert limits.max_patients == 50000
        assert limits.max_storage_gb == 100
        assert limits.max_api_calls_per_day == 500000
        assert limits.features.get("telehealth") is True
        assert limits.features.get("ai_features") is True

    def test_tenant_limits_for_tier_enterprise(self):
        """Test enterprise tier limits."""
        limits = TenantLimits.for_tier(TenantTier.ENTERPRISE)
        assert limits.max_users == 999999
        assert limits.max_patients == 999999
        assert limits.features.get("white_label") is True

    def test_tenant_context_creation(self):
        """Test creating a tenant context."""
        context = TenantContext(
            tenant_id="test-tenant-123",
            name="Test Hospital",
            slug="test-hospital",
            tier=TenantTier.PROFESSIONAL,
            status=TenantStatus.ACTIVE,
        )

        assert context.tenant_id == "test-tenant-123"
        assert context.name == "Test Hospital"
        assert context.slug == "test-hospital"
        assert context.tier == TenantTier.PROFESSIONAL
        assert context.status == TenantStatus.ACTIVE

    def test_tenant_context_has_feature(self):
        """Test feature checking."""
        limits = TenantLimits.for_tier(TenantTier.PROFESSIONAL)
        context = TenantContext(
            tenant_id="test",
            name="Test",
            slug="test",
            limits=limits,
        )

        assert context.has_feature("telehealth") is True
        assert context.has_feature("ai_features") is True
        assert context.has_feature("nonexistent") is False

    def test_tenant_context_is_active(self):
        """Test active status checking."""
        active_context = TenantContext(
            tenant_id="test",
            name="Test",
            slug="test",
            status=TenantStatus.ACTIVE,
        )
        assert active_context.is_active() is True

        trial_context = TenantContext(
            tenant_id="test",
            name="Test",
            slug="test",
            status=TenantStatus.TRIAL,
        )
        assert trial_context.is_active() is True

        suspended_context = TenantContext(
            tenant_id="test",
            name="Test",
            slug="test",
            status=TenantStatus.SUSPENDED,
        )
        assert suspended_context.is_active() is False

    def test_tenant_context_to_dict(self):
        """Test conversion to dictionary."""
        context = TenantContext(
            tenant_id="test-123",
            name="Test Hospital",
            slug="test-hospital",
            tier=TenantTier.STARTER,
            status=TenantStatus.TRIAL,
        )

        data = context.to_dict()
        assert data["tenantId"] == "test-123"
        assert data["name"] == "Test Hospital"
        assert data["slug"] == "test-hospital"
        assert data["tier"] == "starter"
        assert data["status"] == "trial"

    def test_context_variables_get_set(self):
        """Test context variable operations."""
        # Clear any existing context
        clear_tenant_context()
        assert get_current_tenant() is None

        # Set tenant
        set_tenant("tenant-abc")
        assert get_current_tenant() == "tenant-abc"

        # Clear tenant
        clear_tenant_context()
        assert get_current_tenant() is None

    def test_context_manager(self):
        """Test tenant context manager."""
        clear_tenant_context()

        with TenantContextManager("tenant-xyz"):
            assert get_current_tenant() == "tenant-xyz"

        # Should be cleared after context manager exits
        assert get_current_tenant() is None

    def test_context_manager_with_full_context(self):
        """Test context manager with full context."""
        clear_tenant_context()

        context = TenantContext(
            tenant_id="tenant-full",
            name="Full Context Test",
            slug="full-test",
        )

        with TenantContextManager("tenant-full", context):
            assert get_current_tenant() == "tenant-full"
            full_context = get_tenant_context()
            assert full_context is not None
            assert full_context.name == "Full Context Test"

        assert get_tenant_context() is None


class TestTenantSettings:
    """Tests for tenant settings."""

    def test_default_settings(self):
        """Test default tenant settings."""
        settings = TenantSettings()

        assert settings.timezone == "UTC"
        assert settings.language == "en"
        assert settings.currency == "USD"
        assert settings.appointment_duration_minutes == 30
        assert settings.enable_reminders is True
        assert settings.hipaa_mode is True
        assert settings.audit_logging is True

    def test_password_policy_defaults(self):
        """Test default password policy."""
        settings = TenantSettings()

        assert settings.password_policy["min_length"] == 8
        assert settings.password_policy["require_uppercase"] is True
        assert settings.password_policy["require_lowercase"] is True
        assert settings.password_policy["require_numbers"] is True
        assert settings.password_policy["require_special"] is True


class TestTenantBranding:
    """Tests for tenant branding."""

    def test_default_branding(self):
        """Test default branding values."""
        branding = TenantBranding()

        assert branding.primary_color == "#0066CC"
        assert branding.secondary_color == "#F0F0F0"
        assert branding.accent_color == "#00CC66"
        assert branding.font_family == "Inter, sans-serif"
        assert branding.logo_url is None

    def test_custom_branding(self):
        """Test custom branding values."""
        branding = TenantBranding(
            logo_url="https://example.com/logo.png",
            primary_color="#FF0000",
            custom_css=".header { background: red; }",
        )

        assert branding.logo_url == "https://example.com/logo.png"
        assert branding.primary_color == "#FF0000"
        assert branding.custom_css == ".header { background: red; }"


class TestTenantScoped:
    """Tests for tenant_scoped decorator."""

    @pytest.mark.asyncio
    async def test_async_tenant_scoped(self):
        """Test async function with tenant scope."""
        clear_tenant_context()

        @tenant_scoped
        async def async_func(tenant_id: str):
            return get_current_tenant()

        result = await async_func(tenant_id="scoped-tenant")
        assert result == "scoped-tenant"

        # Context should be cleared after function
        assert get_current_tenant() is None

    def test_sync_tenant_scoped(self):
        """Test sync function with tenant scope."""
        clear_tenant_context()

        @tenant_scoped
        def sync_func(tenant_id: str):
            return get_current_tenant()

        result = sync_func(tenant_id="sync-scoped")
        assert result == "sync-scoped"


class TestRateLimiter:
    """Tests for rate limiting."""

    @pytest.mark.asyncio
    async def test_sliding_window_allows_under_limit(self):
        """Test that requests under limit are allowed."""
        from shared.database.rate_limiter import SlidingWindowRateLimiter

        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.pipeline.return_value = AsyncMock()
        mock_redis.pipeline.return_value.execute = AsyncMock(return_value=[None, 5, None, None])
        mock_redis.zrange = AsyncMock(return_value=[(b"1234", 1234)])

        limiter = SlidingWindowRateLimiter(mock_redis)
        result = await limiter.check("test-key", limit=100, window_seconds=60)

        assert result.allowed is True
        assert result.remaining > 0

    @pytest.mark.asyncio
    async def test_sliding_window_blocks_over_limit(self):
        """Test that requests over limit are blocked."""
        from shared.database.rate_limiter import SlidingWindowRateLimiter

        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.pipeline.return_value = AsyncMock()
        mock_redis.pipeline.return_value.execute = AsyncMock(return_value=[None, 101, None, None])
        mock_redis.zrange = AsyncMock(return_value=[(b"1234", 1234)])
        mock_redis.zrem = AsyncMock()

        limiter = SlidingWindowRateLimiter(mock_redis)
        result = await limiter.check("test-key", limit=100, window_seconds=60)

        assert result.allowed is False
        assert result.remaining == 0
        assert result.retry_after is not None


class TestQuotaManager:
    """Tests for quota management."""

    @pytest.mark.asyncio
    async def test_quota_check_within_limit(self):
        """Test quota check when within limits."""
        from shared.database.rate_limiter import QuotaManager, QuotaType

        mock_db_factory = MagicMock()
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()

        # Mock database returns
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = MagicMock(
            limits={"max_users": 100, "max_patients": 10000}
        )
        mock_db.execute.return_value.scalar.return_value = 50
        mock_db_factory.return_value = mock_db

        manager = QuotaManager(mock_db_factory, mock_redis)
        result = await manager.check_quota("tenant-123", QuotaType.USERS, 1)

        assert result.allowed is True
        assert result.current == 50
        assert result.remaining > 0


class TestAuditService:
    """Tests for audit logging."""

    def test_audit_entry_creation(self):
        """Test creating an audit entry."""
        from shared.database.audit_service import AuditEntry, AuditAction, AuditCategory

        entry = AuditEntry(
            tenant_id="tenant-audit",
            action=AuditAction.CREATE,
            resource_type="patient",
            resource_id="patient-123",
            user_id="user-456",
        )

        assert entry.tenant_id == "tenant-audit"
        assert entry.action == AuditAction.CREATE
        assert entry.resource_type == "patient"
        assert entry.resource_id == "patient-123"

    def test_audit_action_values(self):
        """Test audit action enum values."""
        from shared.database.audit_service import AuditAction

        assert AuditAction.CREATE.value == "CREATE"
        assert AuditAction.READ.value == "READ"
        assert AuditAction.UPDATE.value == "UPDATE"
        assert AuditAction.DELETE.value == "DELETE"
        assert AuditAction.LOGIN.value == "LOGIN"
        assert AuditAction.PHI_ACCESSED.value == "PHI_ACCESSED"


class TestUsageTracker:
    """Tests for usage tracking."""

    def test_usage_event_creation(self):
        """Test creating a usage event."""
        from shared.database.usage_tracker import UsageEvent, UsageMetric

        event = UsageEvent(
            tenant_id="tenant-usage",
            metric=UsageMetric.API_CALLS,
            value=1,
        )

        assert event.tenant_id == "tenant-usage"
        assert event.metric == UsageMetric.API_CALLS
        assert event.value == 1

    def test_usage_metric_values(self):
        """Test usage metric enum values."""
        from shared.database.usage_tracker import UsageMetric

        assert UsageMetric.API_CALLS.value == "api_calls"
        assert UsageMetric.STORAGE_BYTES.value == "storage_bytes"
        assert UsageMetric.AI_REQUESTS.value == "ai_requests"


class TestDataExport:
    """Tests for data export functionality."""

    def test_export_config_creation(self):
        """Test export configuration."""
        from shared.database.data_export import ExportConfig, ExportFormat

        config = ExportConfig(
            tenant_id="tenant-export",
            export_type="full",
            format=ExportFormat.JSON,
            compress=True,
        )

        assert config.tenant_id == "tenant-export"
        assert config.export_type == "full"
        assert config.format == ExportFormat.JSON
        assert config.compress is True

    def test_export_format_values(self):
        """Test export format enum values."""
        from shared.database.data_export import ExportFormat

        assert ExportFormat.JSON.value == "json"
        assert ExportFormat.JSON_LINES.value == "jsonl"
        assert ExportFormat.CSV.value == "csv"
        assert ExportFormat.FHIR_BUNDLE.value == "fhir_bundle"


class TestTenantMonitor:
    """Tests for tenant monitoring."""

    def test_health_status_values(self):
        """Test health status enum values."""
        from shared.database.tenant_monitoring import HealthStatus

        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.CRITICAL.value == "critical"

    def test_alert_type_values(self):
        """Test alert type enum values."""
        from shared.database.tenant_monitoring import AlertType

        assert AlertType.QUOTA_WARNING.value == "quota_warning"
        assert AlertType.ERROR_RATE_HIGH.value == "error_rate_high"
        assert AlertType.SLA_BREACH.value == "sla_breach"


class TestTenantIsolation:
    """Tests for tenant data isolation."""

    def test_rls_context_setting(self):
        """Test that RLS context is set correctly."""
        from shared.database.tenant_context import setup_tenant_rls
        from unittest.mock import MagicMock

        mock_db = MagicMock()
        setup_tenant_rls(mock_db, "tenant-rls-test")

        mock_db.execute.assert_called_once()
        call_args = str(mock_db.execute.call_args)
        assert "app.current_tenant" in call_args
        assert "tenant-rls-test" in call_args

    def test_tenant_context_isolation(self):
        """Test that tenant contexts are isolated."""
        clear_tenant_context()

        # Set context for tenant A
        with TenantContextManager("tenant-a"):
            assert get_current_tenant() == "tenant-a"

            # Nested context for tenant B should override
            with TenantContextManager("tenant-b"):
                assert get_current_tenant() == "tenant-b"

            # After exiting B, should be back to A
            assert get_current_tenant() == "tenant-a"

        # After exiting A, should be cleared
        assert get_current_tenant() is None


class TestSecurityFeatures:
    """Tests for security-related features."""

    def test_api_key_prefix_format(self):
        """Test API key format validation."""
        import secrets

        # Generate key similar to production
        raw_key = f"ht_{secrets.token_urlsafe(32)}"
        key_prefix = raw_key[:12]

        assert raw_key.startswith("ht_")
        assert len(key_prefix) == 12

    def test_password_hashing(self):
        """Test password hashing functionality."""
        from shared.auth.passwords import hash_password, verify_password

        password = "SecureP@ssw0rd!"
        hashed = hash_password(password)

        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False


# Integration-style tests (would need actual database)
class TestTenantProvisioningFlow:
    """Tests for the complete tenant provisioning flow."""

    def test_tenant_create_schema_validation(self):
        """Test tenant creation schema validation."""
        from services.prm.modules.tenants.schemas import TenantSignupRequest

        # Valid request
        valid_data = {
            "organization_name": "Test Hospital",
            "slug": "test-hospital",
            "admin_email": "admin@test.com",
            "admin_name": "Admin User",
            "admin_password": "SecurePass123!",
            "accept_terms": True,
        }

        request = TenantSignupRequest(**valid_data)
        assert request.organization_name == "Test Hospital"
        assert request.slug == "test-hospital"

    def test_tenant_slug_validation(self):
        """Test that slug follows correct pattern."""
        from services.prm.modules.tenants.schemas import TenantSignupRequest
        from pydantic import ValidationError

        # Invalid slug with uppercase should fail
        with pytest.raises(ValidationError):
            TenantSignupRequest(
                organization_name="Test",
                slug="Test-Hospital",  # Contains uppercase
                admin_email="admin@test.com",
                admin_name="Admin",
                admin_password="SecurePass123!",
                accept_terms=True,
            )

    def test_must_accept_terms(self):
        """Test that terms must be accepted."""
        from services.prm.modules.tenants.schemas import TenantSignupRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            TenantSignupRequest(
                organization_name="Test",
                slug="test-hospital",
                admin_email="admin@test.com",
                admin_name="Admin",
                admin_password="SecurePass123!",
                accept_terms=False,  # Not accepted
            )


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
