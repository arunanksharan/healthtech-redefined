"""
Unit tests for APIGatewayService
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from modules.marketplace.services.api_gateway_service import (
    APIGatewayService,
    CircuitState,
    RateLimitResult,
    CircuitBreakerResult,
    rate_limit_middleware,
    circuit_breaker_middleware,
)
from modules.marketplace.models import (
    OAuthApplication,
    RateLimitBucket,
    APIUsageLog,
    APIKey,
    APIKeyStatus,
    OAuthToken,
)
from modules.marketplace.schemas import (
    APIUsageLogCreate,
    RateLimitConfig,
)


@pytest.fixture
def gateway_service():
    service = APIGatewayService()
    # Reset circuit breakers between tests
    service._circuit_breakers = {}
    return service


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def sample_application():
    app = MagicMock(spec=OAuthApplication)
    app.id = uuid4()
    app.metadata = {"tier": "professional"}
    return app


@pytest.fixture
def sample_rate_limit_bucket():
    bucket = MagicMock(spec=RateLimitBucket)
    bucket.id = uuid4()
    bucket.bucket_key = "test_key"
    bucket.window_start = datetime.utcnow()
    bucket.request_count = 50
    bucket.last_request_at = datetime.utcnow()
    return bucket


class TestRateLimiting:
    """Tests for rate limiting functionality."""

    @pytest.mark.asyncio
    async def test_check_rate_limit_allowed(
        self, gateway_service, mock_db, sample_application, sample_rate_limit_bucket
    ):
        """Test rate limit check when under limit."""
        application_id = sample_application.id

        # Mock bucket lookup
        bucket_result = AsyncMock()
        bucket_result.scalar_one_or_none.return_value = sample_rate_limit_bucket

        # Mock application lookup
        app_result = AsyncMock()
        app_result.scalar_one_or_none.return_value = sample_application

        mock_db.execute.side_effect = [bucket_result, app_result]

        result = await gateway_service.check_rate_limit(mock_db, application_id)

        assert isinstance(result, RateLimitResult)
        assert result.allowed is True
        assert result.remaining > 0

    @pytest.mark.asyncio
    async def test_check_rate_limit_exceeded(
        self, gateway_service, mock_db, sample_application
    ):
        """Test rate limit check when limit exceeded."""
        application_id = sample_application.id

        # Mock bucket at limit
        exceeded_bucket = MagicMock(spec=RateLimitBucket)
        exceeded_bucket.window_start = datetime.utcnow()
        exceeded_bucket.request_count = 1000  # At limit for professional tier
        exceeded_bucket.last_request_at = datetime.utcnow()

        bucket_result = AsyncMock()
        bucket_result.scalar_one_or_none.return_value = exceeded_bucket

        app_result = AsyncMock()
        app_result.scalar_one_or_none.return_value = sample_application

        mock_db.execute.side_effect = [bucket_result, app_result]

        result = await gateway_service.check_rate_limit(mock_db, application_id)

        assert isinstance(result, RateLimitResult)
        assert result.allowed is False
        assert result.retry_after is not None

    @pytest.mark.asyncio
    async def test_check_rate_limit_new_bucket(
        self, gateway_service, mock_db, sample_application
    ):
        """Test rate limit check creates new bucket."""
        application_id = sample_application.id

        # Mock no existing bucket
        bucket_result = AsyncMock()
        bucket_result.scalar_one_or_none.return_value = None

        app_result = AsyncMock()
        app_result.scalar_one_or_none.return_value = sample_application

        mock_db.execute.side_effect = [bucket_result, app_result]

        result = await gateway_service.check_rate_limit(mock_db, application_id)

        assert isinstance(result, RateLimitResult)
        assert result.allowed is True
        assert mock_db.add.called

    @pytest.mark.asyncio
    async def test_check_rate_limit_window_reset(
        self, gateway_service, mock_db, sample_application
    ):
        """Test rate limit resets after window expires."""
        application_id = sample_application.id

        # Mock bucket with old window
        old_bucket = MagicMock(spec=RateLimitBucket)
        old_bucket.window_start = datetime.utcnow() - timedelta(minutes=2)  # Old window
        old_bucket.request_count = 1000  # Was at limit
        old_bucket.last_request_at = datetime.utcnow() - timedelta(minutes=2)

        bucket_result = AsyncMock()
        bucket_result.scalar_one_or_none.return_value = old_bucket

        app_result = AsyncMock()
        app_result.scalar_one_or_none.return_value = sample_application

        mock_db.execute.side_effect = [bucket_result, app_result]

        result = await gateway_service.check_rate_limit(mock_db, application_id)

        # Window should reset, request allowed
        assert result.allowed is True


class TestQuotaManagement:
    """Tests for quota management."""

    @pytest.mark.asyncio
    async def test_check_quota_under_limit(
        self, gateway_service, mock_db, sample_application
    ):
        """Test quota check when under limit."""
        # Mock application lookup
        app_result = AsyncMock()
        app_result.scalar_one_or_none.return_value = sample_application

        # Mock usage count
        count_result = AsyncMock()
        count_result.scalar.return_value = 5000000  # Under limit

        mock_db.execute.side_effect = [app_result, count_result]

        allowed, used, limit = await gateway_service.check_quota(
            mock_db, sample_application.id
        )

        assert allowed is True
        assert used == 5000000

    @pytest.mark.asyncio
    async def test_check_quota_exceeded(
        self, gateway_service, mock_db, sample_application
    ):
        """Test quota check when exceeded."""
        # Mock application lookup
        app_result = AsyncMock()
        app_result.scalar_one_or_none.return_value = sample_application

        # Mock usage count at limit
        count_result = AsyncMock()
        count_result.scalar.return_value = 10000000  # At limit

        mock_db.execute.side_effect = [app_result, count_result]

        allowed, used, limit = await gateway_service.check_quota(
            mock_db, sample_application.id
        )

        assert allowed is False

    @pytest.mark.asyncio
    async def test_check_quota_unlimited(self, gateway_service, mock_db):
        """Test quota check for unlimited tier."""
        # Mock enterprise app with unlimited quota
        enterprise_app = MagicMock(spec=OAuthApplication)
        enterprise_app.id = uuid4()
        enterprise_app.metadata = {"tier": "enterprise"}

        app_result = AsyncMock()
        app_result.scalar_one_or_none.return_value = enterprise_app
        mock_db.execute.return_value = app_result

        allowed, used, limit = await gateway_service.check_quota(
            mock_db, enterprise_app.id
        )

        assert allowed is True
        assert limit is None


class TestCircuitBreaker:
    """Tests for circuit breaker functionality."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self, gateway_service):
        """Test circuit breaker in closed state."""
        service_name = "test_service"

        result = await gateway_service.check_circuit_breaker(service_name)

        assert isinstance(result, CircuitBreakerResult)
        assert result.allowed is True
        assert result.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(self, gateway_service):
        """Test circuit breaker opens after threshold failures."""
        service_name = "failing_service"

        # Record failures to exceed threshold
        for _ in range(5):
            await gateway_service.record_circuit_failure(service_name)

        result = await gateway_service.check_circuit_breaker(service_name)

        assert result.allowed is False
        assert result.state == CircuitState.OPEN
        assert result.failure_count >= 5

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_after_timeout(self, gateway_service):
        """Test circuit breaker transitions to half-open after timeout."""
        service_name = "recovering_service"

        # Open the circuit
        for _ in range(5):
            await gateway_service.record_circuit_failure(service_name)

        # Manually set last state change to simulate timeout
        gateway_service._circuit_breakers[service_name]["last_state_change"] = (
            datetime.utcnow() - timedelta(seconds=35)
        )

        result = await gateway_service.check_circuit_breaker(service_name)

        assert result.allowed is True
        assert result.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_circuit_breaker_closes_after_successes(self, gateway_service):
        """Test circuit breaker closes after successful requests in half-open."""
        service_name = "recovered_service"

        # Set up half-open state
        gateway_service._circuit_breakers[service_name] = {
            "state": CircuitState.HALF_OPEN,
            "failure_count": 5,
            "success_count": 0,
            "last_failure": datetime.utcnow(),
            "last_state_change": datetime.utcnow()
        }

        # Record successes
        for _ in range(3):
            await gateway_service.record_circuit_success(service_name)

        assert gateway_service._circuit_breakers[service_name]["state"] == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_reopens_on_half_open_failure(self, gateway_service):
        """Test circuit breaker reopens on failure during half-open."""
        service_name = "unstable_service"

        # Set up half-open state
        gateway_service._circuit_breakers[service_name] = {
            "state": CircuitState.HALF_OPEN,
            "failure_count": 5,
            "success_count": 0,
            "last_failure": datetime.utcnow(),
            "last_state_change": datetime.utcnow()
        }

        # Record failure
        await gateway_service.record_circuit_failure(service_name)

        assert gateway_service._circuit_breakers[service_name]["state"] == CircuitState.OPEN


class TestUsageLogging:
    """Tests for API usage logging."""

    @pytest.mark.asyncio
    async def test_log_request_success(self, gateway_service, mock_db):
        """Test successful request logging."""
        application_id = uuid4()
        log_data = APIUsageLogCreate(
            endpoint="/api/v1/patients",
            method="GET",
            status_code=200,
            response_time_ms=150,
            request_size_bytes=100,
            response_size_bytes=5000,
            ip_address="192.168.1.1",
            user_agent="TestClient/1.0"
        )

        result = await gateway_service.log_request(mock_db, application_id, log_data)

        assert result is not None
        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_get_usage_summary(
        self, gateway_service, mock_db, sample_application
    ):
        """Test usage summary retrieval."""
        # Mock various count queries
        total_result = AsyncMock()
        total_result.scalar.return_value = 10000

        success_result = AsyncMock()
        success_result.scalar.return_value = 9500

        failed_result = AsyncMock()
        failed_result.scalar.return_value = 500

        avg_result = AsyncMock()
        avg_result.scalar.return_value = 150.5

        # Mock application for config
        app_result = AsyncMock()
        app_result.scalar_one_or_none.return_value = sample_application

        # Mock quota check
        quota_count = AsyncMock()
        quota_count.scalar.return_value = 5000

        mock_db.execute.side_effect = [
            total_result, success_result, failed_result, avg_result,
            app_result, quota_count
        ]

        result = await gateway_service.get_usage_summary(
            mock_db, sample_application.id
        )

        assert result is not None
        assert result.total_requests == 10000
        assert result.successful_requests == 9500
        assert result.failed_requests == 500


class TestTokenValidation:
    """Tests for token and API key validation."""

    @pytest.mark.asyncio
    async def test_validate_api_key_success(self, gateway_service, mock_db):
        """Test successful API key validation."""
        api_key = "pk_test_abcdefghij1234567890"

        # Mock API key lookup
        api_key_obj = MagicMock(spec=APIKey)
        api_key_obj.id = uuid4()
        api_key_obj.application_id = uuid4()
        api_key_obj.key_prefix = api_key[:16]
        api_key_obj.status = APIKeyStatus.ACTIVE
        api_key_obj.expires_at = None
        api_key_obj.allowed_scopes = ["patient/Patient.read"]
        api_key_obj.last_used_at = None

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = api_key_obj
        mock_db.execute.return_value = mock_result

        result = await gateway_service.validate_api_key(mock_db, api_key)

        assert result is not None
        application_id, key_id, scopes = result
        assert key_id == api_key_obj.id

    @pytest.mark.asyncio
    async def test_validate_api_key_expired(self, gateway_service, mock_db):
        """Test validation fails for expired API key."""
        api_key = "pk_test_expired_key_123456"

        # Mock expired API key
        expired_key = MagicMock(spec=APIKey)
        expired_key.key_prefix = api_key[:16]
        expired_key.status = APIKeyStatus.ACTIVE
        expired_key.expires_at = datetime.utcnow() - timedelta(days=1)

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = expired_key
        mock_db.execute.return_value = mock_result

        result = await gateway_service.validate_api_key(mock_db, api_key)

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_bearer_token_success(self, gateway_service, mock_db):
        """Test successful bearer token validation."""
        token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9..."

        # Mock token lookup
        token_obj = MagicMock(spec=OAuthToken)
        token_obj.id = uuid4()
        token_obj.application_id = uuid4()
        token_obj.tenant_id = uuid4()
        token_obj.user_id = uuid4()
        token_obj.patient_id = uuid4()
        token_obj.scopes = ["patient/Patient.read"]
        token_obj.access_token_expires_at = datetime.utcnow() + timedelta(hours=1)
        token_obj.revoked_at = None

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = token_obj
        mock_db.execute.return_value = mock_result

        result = await gateway_service.validate_bearer_token(mock_db, token)

        assert result is not None
        assert "application_id" in result
        assert "scopes" in result

    @pytest.mark.asyncio
    async def test_validate_bearer_token_expired(self, gateway_service, mock_db):
        """Test validation fails for expired bearer token."""
        token = "expired_token_12345"

        # Mock expired token
        expired_token = MagicMock(spec=OAuthToken)
        expired_token.access_token_expires_at = datetime.utcnow() - timedelta(hours=1)
        expired_token.revoked_at = None

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = expired_token
        mock_db.execute.return_value = mock_result

        result = await gateway_service.validate_bearer_token(mock_db, token)

        assert result is None


class TestMiddlewareHelpers:
    """Tests for middleware helper functions."""

    @pytest.mark.asyncio
    async def test_rate_limit_middleware_allowed(self, gateway_service, mock_db):
        """Test rate limit middleware when request allowed."""
        application_id = uuid4()

        # Mock successful rate limit check
        with patch.object(
            gateway_service, 'check_rate_limit',
            return_value=RateLimitResult(
                allowed=True,
                remaining=950,
                limit=1000,
                reset_at=datetime.utcnow() + timedelta(minutes=1)
            )
        ):
            result = await rate_limit_middleware(
                gateway_service, mock_db, application_id
            )

        assert result["allowed"] is True
        assert "X-RateLimit-Limit" in result["headers"]
        assert "X-RateLimit-Remaining" in result["headers"]

    @pytest.mark.asyncio
    async def test_rate_limit_middleware_denied(self, gateway_service, mock_db):
        """Test rate limit middleware when request denied."""
        application_id = uuid4()

        # Mock rate limit exceeded
        with patch.object(
            gateway_service, 'check_rate_limit',
            return_value=RateLimitResult(
                allowed=False,
                remaining=0,
                limit=1000,
                reset_at=datetime.utcnow() + timedelta(seconds=30),
                retry_after=30
            )
        ):
            result = await rate_limit_middleware(
                gateway_service, mock_db, application_id
            )

        assert result["allowed"] is False
        assert "Retry-After" in result["headers"]

    @pytest.mark.asyncio
    async def test_circuit_breaker_middleware_allowed(self, gateway_service):
        """Test circuit breaker middleware when service healthy."""
        service_name = "healthy_service"

        result = await circuit_breaker_middleware(gateway_service, service_name)

        assert result["allowed"] is True
        assert result["state"] == "closed"

    @pytest.mark.asyncio
    async def test_circuit_breaker_middleware_denied(self, gateway_service):
        """Test circuit breaker middleware when circuit open."""
        service_name = "failing_service"

        # Open the circuit
        for _ in range(5):
            await gateway_service.record_circuit_failure(service_name)

        result = await circuit_breaker_middleware(gateway_service, service_name)

        assert result["allowed"] is False
        assert result["state"] == "open"
