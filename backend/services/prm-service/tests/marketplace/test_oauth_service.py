"""
Unit tests for OAuthService
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from modules.marketplace.services.oauth_service import OAuthService
from modules.marketplace.models import (
    OAuthApplication,
    OAuthToken,
    OAuthConsent,
    APIKey,
    APIKeyStatus,
    TokenType,
)
from modules.marketplace.schemas import (
    OAuthAppCreate,
    OAuthAppUpdate,
    APIKeyCreate,
    AuthorizationRequest,
    TokenExchangeRequest,
    RefreshTokenRequest,
    ClientCredentialsRequest,
    ConsentCreate,
    WebhookCreate,
)


@pytest.fixture
def oauth_service():
    return OAuthService()


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def sample_oauth_app():
    app = MagicMock(spec=OAuthApplication)
    app.id = uuid4()
    app.developer_organization_id = uuid4()
    app.name = "Test OAuth App"
    app.client_id = "test_client_id_123"
    app.client_secret_hash = "hashed_secret"
    app.redirect_uris = ["https://test.com/callback"]
    app.allowed_scopes = ["patient/Patient.read", "openid"]
    app.is_smart_on_fhir = True
    app.is_active = True
    app.created_at = datetime.utcnow()
    return app


@pytest.fixture
def sample_token():
    token = MagicMock(spec=OAuthToken)
    token.id = uuid4()
    token.application_id = uuid4()
    token.tenant_id = uuid4()
    token.user_id = uuid4()
    token.scopes = ["patient/Patient.read"]
    token.access_token_hash = "hashed_access_token"
    token.refresh_token_hash = "hashed_refresh_token"
    token.access_token_expires_at = datetime.utcnow() + timedelta(hours=1)
    token.refresh_token_expires_at = datetime.utcnow() + timedelta(days=30)
    token.revoked_at = None
    return token


class TestOAuthServiceApplications:
    """Tests for OAuth application management."""

    @pytest.mark.asyncio
    async def test_create_application_success(
        self, oauth_service, mock_db
    ):
        """Test successful OAuth application creation."""
        organization_id = uuid4()
        user_id = uuid4()
        app_data = OAuthAppCreate(
            name="Test App",
            description="A test application",
            redirect_uris=["https://test.com/callback"],
            allowed_scopes=["patient/Patient.read", "openid"],
            is_smart_on_fhir=True
        )

        # Mock no existing app with same name
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await oauth_service.create_application(
            mock_db, organization_id, app_data, user_id
        )

        assert result is not None
        assert mock_db.add.called
        assert mock_db.commit.called
        # Should return client secret on creation
        assert hasattr(result, 'client_secret') or 'client_secret' in str(result)

    @pytest.mark.asyncio
    async def test_rotate_client_secret_success(
        self, oauth_service, mock_db, sample_oauth_app
    ):
        """Test successful client secret rotation."""
        organization_id = sample_oauth_app.developer_organization_id
        user_id = uuid4()

        # Mock application lookup
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_oauth_app
        mock_db.execute.return_value = mock_result

        old_hash = sample_oauth_app.client_secret_hash

        result = await oauth_service.rotate_client_secret(
            mock_db, sample_oauth_app.id, organization_id, user_id
        )

        assert sample_oauth_app.client_secret_hash != old_hash
        assert mock_db.commit.called


class TestOAuthServiceAPIKeys:
    """Tests for API key management."""

    @pytest.mark.asyncio
    async def test_create_api_key_success(
        self, oauth_service, mock_db, sample_oauth_app
    ):
        """Test successful API key creation."""
        organization_id = sample_oauth_app.developer_organization_id
        user_id = uuid4()
        key_data = APIKeyCreate(
            name="Production Key",
            allowed_scopes=["patient/Patient.read"],
            expires_at=datetime.utcnow() + timedelta(days=365)
        )

        # Mock application lookup
        app_result = AsyncMock()
        app_result.scalar_one_or_none.return_value = sample_oauth_app

        # Mock key count check
        count_result = AsyncMock()
        count_result.scalar.return_value = 3

        mock_db.execute.side_effect = [app_result, count_result]

        result = await oauth_service.create_api_key(
            mock_db, sample_oauth_app.id, organization_id, key_data, user_id
        )

        assert result is not None
        assert mock_db.add.called
        assert mock_db.commit.called
        # Should return the full key on creation
        assert hasattr(result, 'api_key') or 'api_key' in str(result)

    @pytest.mark.asyncio
    async def test_create_api_key_limit_exceeded(
        self, oauth_service, mock_db, sample_oauth_app
    ):
        """Test API key creation fails when limit exceeded."""
        organization_id = sample_oauth_app.developer_organization_id
        user_id = uuid4()
        key_data = APIKeyCreate(
            name="Another Key",
            allowed_scopes=["patient/Patient.read"]
        )

        # Mock application lookup
        app_result = AsyncMock()
        app_result.scalar_one_or_none.return_value = sample_oauth_app

        # Mock key count at limit
        count_result = AsyncMock()
        count_result.scalar.return_value = 10  # At limit

        mock_db.execute.side_effect = [app_result, count_result]

        with pytest.raises(ValueError, match="limit"):
            await oauth_service.create_api_key(
                mock_db, sample_oauth_app.id, organization_id, key_data, user_id
            )

    @pytest.mark.asyncio
    async def test_revoke_api_key_success(
        self, oauth_service, mock_db, sample_oauth_app
    ):
        """Test successful API key revocation."""
        organization_id = sample_oauth_app.developer_organization_id
        user_id = uuid4()

        # Mock API key
        api_key = MagicMock(spec=APIKey)
        api_key.id = uuid4()
        api_key.application_id = sample_oauth_app.id
        api_key.status = APIKeyStatus.ACTIVE

        # Mock application lookup
        app_result = AsyncMock()
        app_result.scalar_one_or_none.return_value = sample_oauth_app

        # Mock key lookup
        key_result = AsyncMock()
        key_result.scalar_one_or_none.return_value = api_key

        mock_db.execute.side_effect = [app_result, key_result]

        await oauth_service.revoke_api_key(
            mock_db, api_key.id, organization_id, user_id
        )

        assert api_key.status == APIKeyStatus.REVOKED
        assert mock_db.commit.called


class TestOAuthServiceAuthorization:
    """Tests for OAuth authorization flow."""

    @pytest.mark.asyncio
    async def test_create_authorization_code_success(
        self, oauth_service, mock_db, sample_oauth_app
    ):
        """Test successful authorization code creation."""
        tenant_id = uuid4()
        user_id = uuid4()
        patient_id = uuid4()

        auth_request = AuthorizationRequest(
            client_id=sample_oauth_app.client_id,
            response_type="code",
            redirect_uri="https://test.com/callback",
            scope="patient/Patient.read openid",
            state="random_state_123",
            code_challenge="challenge_value",
            code_challenge_method="S256"
        )

        # Mock application lookup
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_oauth_app
        mock_db.execute.return_value = mock_result

        result = await oauth_service.create_authorization_code(
            mock_db, auth_request, tenant_id, user_id, patient_id
        )

        assert result is not None
        assert mock_db.add.called

    @pytest.mark.asyncio
    async def test_create_authorization_code_invalid_redirect(
        self, oauth_service, mock_db, sample_oauth_app
    ):
        """Test authorization fails with invalid redirect URI."""
        tenant_id = uuid4()
        user_id = uuid4()

        auth_request = AuthorizationRequest(
            client_id=sample_oauth_app.client_id,
            response_type="code",
            redirect_uri="https://malicious.com/callback",  # Not in allowed list
            scope="patient/Patient.read",
            state="random_state_123"
        )

        # Mock application lookup
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_oauth_app
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="redirect"):
            await oauth_service.create_authorization_code(
                mock_db, auth_request, tenant_id, user_id, None
            )


class TestOAuthServiceTokens:
    """Tests for token management."""

    @pytest.mark.asyncio
    async def test_exchange_authorization_code_success(
        self, oauth_service, mock_db, sample_oauth_app
    ):
        """Test successful authorization code exchange."""
        # Mock authorization code
        auth_code = MagicMock()
        auth_code.code_hash = "hashed_code"
        auth_code.application_id = sample_oauth_app.id
        auth_code.tenant_id = uuid4()
        auth_code.user_id = uuid4()
        auth_code.scopes = ["patient/Patient.read"]
        auth_code.redirect_uri = "https://test.com/callback"
        auth_code.code_challenge = "challenge"
        auth_code.code_challenge_method = "S256"
        auth_code.expires_at = datetime.utcnow() + timedelta(minutes=5)
        auth_code.used_at = None

        request = TokenExchangeRequest(
            grant_type="authorization_code",
            code="valid_code",
            redirect_uri="https://test.com/callback",
            client_id=sample_oauth_app.client_id,
            code_verifier="verifier_value"
        )

        # Mock lookups
        code_result = AsyncMock()
        code_result.scalar_one_or_none.return_value = auth_code

        app_result = AsyncMock()
        app_result.scalar_one_or_none.return_value = sample_oauth_app

        mock_db.execute.side_effect = [code_result, app_result]

        with patch.object(oauth_service, '_verify_code_challenge', return_value=True):
            result = await oauth_service.exchange_authorization_code(
                mock_db, request
            )

        assert result is not None
        assert 'access_token' in str(result) or hasattr(result, 'access_token')

    @pytest.mark.asyncio
    async def test_refresh_access_token_success(
        self, oauth_service, mock_db, sample_oauth_app, sample_token
    ):
        """Test successful token refresh."""
        request = RefreshTokenRequest(
            grant_type="refresh_token",
            refresh_token="valid_refresh_token",
            client_id=sample_oauth_app.client_id
        )

        # Mock token lookup
        token_result = AsyncMock()
        token_result.scalar_one_or_none.return_value = sample_token

        # Mock app lookup
        app_result = AsyncMock()
        app_result.scalar_one_or_none.return_value = sample_oauth_app

        mock_db.execute.side_effect = [token_result, app_result]

        result = await oauth_service.refresh_access_token(mock_db, request)

        assert result is not None
        assert mock_db.add.called

    @pytest.mark.asyncio
    async def test_refresh_token_expired(
        self, oauth_service, mock_db, sample_token
    ):
        """Test refresh fails with expired token."""
        sample_token.refresh_token_expires_at = datetime.utcnow() - timedelta(days=1)

        request = RefreshTokenRequest(
            grant_type="refresh_token",
            refresh_token="expired_token",
            client_id="client_123"
        )

        # Mock token lookup
        token_result = AsyncMock()
        token_result.scalar_one_or_none.return_value = sample_token
        mock_db.execute.return_value = token_result

        with pytest.raises(ValueError, match="expired"):
            await oauth_service.refresh_access_token(mock_db, request)

    @pytest.mark.asyncio
    async def test_client_credentials_grant_success(
        self, oauth_service, mock_db, sample_oauth_app
    ):
        """Test successful client credentials grant."""
        request = ClientCredentialsRequest(
            grant_type="client_credentials",
            client_id=sample_oauth_app.client_id,
            client_secret="valid_secret",
            scope="system/Patient.read"
        )

        # Mock application lookup with secret verification
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_oauth_app
        mock_db.execute.return_value = mock_result

        with patch.object(oauth_service, '_verify_client_secret', return_value=True):
            result = await oauth_service.client_credentials_grant(
                mock_db, request
            )

        assert result is not None


class TestOAuthServiceConsent:
    """Tests for consent management."""

    @pytest.mark.asyncio
    async def test_grant_consent_success(
        self, oauth_service, mock_db, sample_oauth_app
    ):
        """Test successful consent grant."""
        tenant_id = uuid4()
        user_id = uuid4()
        consent_data = ConsentCreate(
            granted_scopes=["patient/Patient.read", "openid"],
            consent_type="user"
        )

        # Mock application lookup
        app_result = AsyncMock()
        app_result.scalar_one_or_none.return_value = sample_oauth_app

        # Mock no existing consent
        consent_result = AsyncMock()
        consent_result.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [app_result, consent_result]

        result = await oauth_service.grant_consent(
            mock_db, sample_oauth_app.id, tenant_id, user_id, consent_data
        )

        assert result is not None
        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_revoke_consent_success(
        self, oauth_service, mock_db, sample_oauth_app
    ):
        """Test successful consent revocation."""
        tenant_id = uuid4()
        user_id = uuid4()

        # Mock existing consent
        consent = MagicMock(spec=OAuthConsent)
        consent.id = uuid4()
        consent.application_id = sample_oauth_app.id
        consent.tenant_id = tenant_id
        consent.user_id = user_id
        consent.revoked_at = None

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = consent
        mock_db.execute.return_value = mock_result

        await oauth_service.revoke_consent(
            mock_db, sample_oauth_app.id, tenant_id, user_id
        )

        assert consent.revoked_at is not None
        assert mock_db.commit.called


class TestOAuthServiceSMART:
    """Tests for SMART on FHIR configuration."""

    @pytest.mark.asyncio
    async def test_get_smart_configuration(self, oauth_service):
        """Test SMART configuration generation."""
        base_url = "https://api.healthtech-prm.com"

        result = await oauth_service.get_smart_configuration(base_url)

        assert result is not None
        assert "authorization_endpoint" in str(result) or hasattr(result, 'authorization_endpoint')
        assert "token_endpoint" in str(result) or hasattr(result, 'token_endpoint')
        assert "scopes_supported" in str(result) or hasattr(result, 'scopes_supported')

    def test_list_available_scopes(self, oauth_service):
        """Test listing available scopes."""
        scopes = oauth_service.list_available_scopes()

        assert scopes is not None
        assert isinstance(scopes, dict)
        assert len(scopes) > 0
        # Should include standard FHIR scopes
        assert any("patient" in key.lower() for key in scopes.keys())
