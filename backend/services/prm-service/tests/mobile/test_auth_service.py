"""
Mobile Auth Service Tests
EPIC-016: Unit tests for mobile authentication
"""
import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from modules.mobile.services.auth_service import MobileAuthService
from modules.mobile.models import (
    MobileDevice, MobileSession, MobileAuditLog,
    DevicePlatform, DeviceStatus, SessionStatus, BiometricType
)
from modules.mobile.schemas import (
    SessionCreate, SessionRefresh, BiometricAuthRequest,
    BiometricTypeSchema
)


@pytest.fixture
def auth_service():
    return MobileAuthService()


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def sample_device():
    return MobileDevice(
        id=uuid4(),
        tenant_id=uuid4(),
        user_id=uuid4(),
        device_id="device123",
        device_token="fcm_token_123",
        platform=DevicePlatform.IOS,
        status=DeviceStatus.ACTIVE,
        biometric_enabled=True,
        biometric_type=BiometricType.FACE_ID,
        last_active_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def sample_session():
    return MobileSession(
        id=uuid4(),
        tenant_id=uuid4(),
        device_id=uuid4(),
        user_id=uuid4(),
        access_token_hash="hash123",
        refresh_token_hash="hash456",
        access_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        refresh_token_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        status=SessionStatus.ACTIVE,
        auth_method="password",
        created_at=datetime.now(timezone.utc)
    )


class TestMobileAuthService:
    """Test cases for MobileAuthService"""

    @pytest.mark.asyncio
    async def test_create_session_success(self, auth_service, mock_db, sample_device):
        """Test creating a new session successfully"""
        # Arrange
        data = SessionCreate(
            auth_method="password",
            app_version="2.0.0"
        )

        with patch.object(auth_service, '_get_active_device', return_value=sample_device):
            with patch.object(auth_service, '_is_locked_out', return_value=False):
                with patch.object(auth_service, '_cleanup_old_sessions', return_value=None):
                    # Act
                    result = await auth_service.create_session(
                        mock_db, sample_device.id, sample_device.user_id,
                        sample_device.tenant_id, data, "192.168.1.1"
                    )

                    # Assert
                    mock_db.add.assert_called()
                    mock_db.commit.assert_called()
                    assert result.access_token is not None
                    assert result.refresh_token is not None
                    assert result.auth_method == "password"

    @pytest.mark.asyncio
    async def test_create_session_device_not_found(self, auth_service, mock_db):
        """Test creating session with inactive device"""
        # Arrange
        data = SessionCreate(auth_method="password", app_version="2.0.0")

        with patch.object(auth_service, '_get_active_device', return_value=None):
            # Act & Assert
            with pytest.raises(ValueError, match="Device not found"):
                await auth_service.create_session(
                    mock_db, uuid4(), uuid4(), uuid4(), data
                )

    @pytest.mark.asyncio
    async def test_create_session_locked_out(self, auth_service, mock_db, sample_device):
        """Test creating session when device is locked out"""
        # Arrange
        data = SessionCreate(auth_method="password", app_version="2.0.0")

        with patch.object(auth_service, '_get_active_device', return_value=sample_device):
            with patch.object(auth_service, '_is_locked_out', return_value=True):
                # Act & Assert
                with pytest.raises(ValueError, match="temporarily locked"):
                    await auth_service.create_session(
                        mock_db, sample_device.id, sample_device.user_id,
                        sample_device.tenant_id, data
                    )

    @pytest.mark.asyncio
    async def test_refresh_session_success(self, auth_service, mock_db, sample_session, sample_device):
        """Test refreshing a session successfully"""
        # Arrange
        data = SessionRefresh(refresh_token="valid_refresh_token")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_session
        mock_db.execute.return_value = mock_result

        with patch.object(auth_service, '_hash_token', return_value="hash456"):
            with patch.object(auth_service, '_get_active_device', return_value=sample_device):
                with patch.object(auth_service, '_generate_token', side_effect=["new_access", "new_refresh"]):
                    # Act
                    result = await auth_service.refresh_session(mock_db, data, "192.168.1.1")

                    # Assert
                    mock_db.commit.assert_called()
                    assert result.access_token is not None
                    assert result.refresh_token is not None

    @pytest.mark.asyncio
    async def test_refresh_session_invalid_token(self, auth_service, mock_db):
        """Test refreshing with invalid token"""
        # Arrange
        data = SessionRefresh(refresh_token="invalid_token")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid or expired"):
            await auth_service.refresh_session(mock_db, data)

    @pytest.mark.asyncio
    async def test_refresh_session_expired_token(self, auth_service, mock_db, sample_session):
        """Test refreshing with expired token"""
        # Arrange
        sample_session.refresh_token_expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        data = SessionRefresh(refresh_token="expired_token")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_session
        mock_db.execute.return_value = mock_result

        # Act & Assert
        with pytest.raises(ValueError, match="has expired"):
            await auth_service.refresh_session(mock_db, data)

    @pytest.mark.asyncio
    async def test_validate_access_token_valid(self, auth_service, mock_db, sample_session):
        """Test validating a valid access token"""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_session
        mock_db.execute.return_value = mock_result

        # Act
        result = await auth_service.validate_access_token(mock_db, "valid_token")

        # Assert
        assert result is not None
        assert result["session_id"] == str(sample_session.id)
        assert result["user_id"] == str(sample_session.user_id)

    @pytest.mark.asyncio
    async def test_validate_access_token_invalid(self, auth_service, mock_db):
        """Test validating an invalid access token"""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Act
        result = await auth_service.validate_access_token(mock_db, "invalid_token")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_validate_access_token_expired(self, auth_service, mock_db, sample_session):
        """Test validating an expired access token"""
        # Arrange
        sample_session.access_token_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_session
        mock_db.execute.return_value = mock_result

        # Act
        result = await auth_service.validate_access_token(mock_db, "expired_token")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_biometric_success(self, auth_service, mock_db, sample_device):
        """Test successful biometric authentication"""
        # Arrange
        data = BiometricAuthRequest(
            biometric_type=BiometricTypeSchema.FACE_ID,
            signature="valid_signature",
            challenge="challenge123",
            app_version="2.0.0"
        )

        with patch.object(auth_service, '_get_active_device', return_value=sample_device):
            with patch.object(auth_service, '_verify_biometric_signature', return_value=True):
                with patch.object(auth_service, 'create_session') as mock_create:
                    mock_create.return_value = MagicMock(
                        session_id=uuid4(),
                        access_token="token",
                        refresh_token="refresh",
                        access_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
                        refresh_token_expires_at=datetime.now(timezone.utc) + timedelta(days=30)
                    )

                    # Act
                    result = await auth_service.authenticate_biometric(
                        mock_db, sample_device.id, sample_device.user_id,
                        sample_device.tenant_id, data, "192.168.1.1"
                    )

                    # Assert
                    assert result.success is True

    @pytest.mark.asyncio
    async def test_authenticate_biometric_not_enabled(self, auth_service, mock_db, sample_device):
        """Test biometric auth when not enabled on device"""
        # Arrange
        sample_device.biometric_enabled = False
        data = BiometricAuthRequest(
            biometric_type=BiometricTypeSchema.FACE_ID,
            signature="sig",
            challenge="challenge"
        )

        with patch.object(auth_service, '_get_active_device', return_value=sample_device):
            # Act & Assert
            with pytest.raises(ValueError, match="not enabled"):
                await auth_service.authenticate_biometric(
                    mock_db, sample_device.id, sample_device.user_id,
                    sample_device.tenant_id, data
                )

    @pytest.mark.asyncio
    async def test_authenticate_biometric_type_mismatch(self, auth_service, mock_db, sample_device):
        """Test biometric auth with wrong biometric type"""
        # Arrange
        data = BiometricAuthRequest(
            biometric_type=BiometricTypeSchema.TOUCH_ID,  # Device has Face ID
            signature="sig",
            challenge="challenge"
        )

        with patch.object(auth_service, '_get_active_device', return_value=sample_device):
            # Act & Assert
            with pytest.raises(ValueError, match="mismatch"):
                await auth_service.authenticate_biometric(
                    mock_db, sample_device.id, sample_device.user_id,
                    sample_device.tenant_id, data
                )

    @pytest.mark.asyncio
    async def test_enable_biometric(self, auth_service, mock_db, sample_device):
        """Test enabling biometric authentication"""
        # Arrange
        sample_device.biometric_enabled = False
        sample_device.biometric_type = None

        with patch.object(auth_service, '_get_active_device', return_value=sample_device):
            # Act
            await auth_service.enable_biometric(
                mock_db, sample_device.id, sample_device.user_id,
                BiometricType.FACE_ID, "public_key_123"
            )

            # Assert
            mock_db.commit.assert_called()
            assert sample_device.biometric_enabled is True
            assert sample_device.biometric_type == BiometricType.FACE_ID

    @pytest.mark.asyncio
    async def test_disable_biometric(self, auth_service, mock_db, sample_device):
        """Test disabling biometric authentication"""
        # Arrange
        with patch.object(auth_service, '_get_active_device', return_value=sample_device):
            # Act
            await auth_service.disable_biometric(
                mock_db, sample_device.id, sample_device.user_id
            )

            # Assert
            mock_db.commit.assert_called()
            assert sample_device.biometric_enabled is False
            assert sample_device.biometric_type is None

    @pytest.mark.asyncio
    async def test_end_session(self, auth_service, mock_db, sample_session):
        """Test ending a session (logout)"""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_session
        mock_db.execute.return_value = mock_result

        # Act
        await auth_service.end_session(
            mock_db, sample_session.id, sample_session.user_id, "192.168.1.1"
        )

        # Assert
        mock_db.commit.assert_called()
        assert sample_session.status == SessionStatus.ENDED

    @pytest.mark.asyncio
    async def test_end_all_sessions(self, auth_service, mock_db):
        """Test ending all sessions for a user"""
        # Arrange
        mock_result = MagicMock()
        mock_result.rowcount = 3
        mock_db.execute.return_value = mock_result

        # Act
        count = await auth_service.end_all_sessions(mock_db, uuid4(), uuid4())

        # Assert
        mock_db.execute.assert_called()
        mock_db.commit.assert_called()
        assert count == 3

    @pytest.mark.asyncio
    async def test_generate_biometric_challenge(self, auth_service, mock_db):
        """Test generating biometric challenge"""
        # Arrange
        device_id = uuid4()

        # Act
        result = await auth_service.generate_biometric_challenge(mock_db, device_id)

        # Assert
        assert "challenge" in result
        assert "expires_at" in result
        assert result["device_id"] == str(device_id)
        assert len(result["challenge"]) == 64  # hex token


class TestTokenManagement:
    """Test cases for token management"""

    def test_generate_token(self, auth_service):
        """Test token generation"""
        token = auth_service._generate_token()
        assert token is not None
        assert len(token) > 0

    def test_hash_token(self, auth_service):
        """Test token hashing"""
        token = "test_token_123"
        hash1 = auth_service._hash_token(token)
        hash2 = auth_service._hash_token(token)

        # Same token should produce same hash
        assert hash1 == hash2
        # Hash should be different from original
        assert hash1 != token

    def test_verify_biometric_signature(self, auth_service):
        """Test biometric signature verification"""
        # Valid signature and challenge
        result = auth_service._verify_biometric_signature("signature", "challenge")
        assert result is True

        # Missing signature
        result = auth_service._verify_biometric_signature(None, "challenge")
        assert result is False

        # Missing challenge
        result = auth_service._verify_biometric_signature("signature", None)
        assert result is False
