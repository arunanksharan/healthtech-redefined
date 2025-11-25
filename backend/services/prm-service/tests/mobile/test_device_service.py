"""
Device Service Tests
EPIC-016: Unit tests for device management
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from modules.mobile.services.device_service import DeviceService
from modules.mobile.models import (
    MobileDevice, MobileSession, MobileAuditLog,
    DevicePlatform, DeviceStatus, SessionStatus, BiometricType
)
from modules.mobile.schemas import (
    DeviceRegister, DeviceUpdate, DeviceSecurityUpdate,
    DevicePlatformSchema, BiometricTypeSchema
)


@pytest.fixture
def device_service():
    return DeviceService()


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
        user_type="patient",
        device_id="device123",
        device_token="token123",
        platform=DevicePlatform.IOS,
        platform_version="17.0",
        device_model="iPhone 15 Pro",
        device_name="John's iPhone",
        app_version="2.0.0",
        app_build="100",
        bundle_id="com.healthcare.app",
        locale="en",
        timezone="America/New_York",
        biometric_enabled=True,
        biometric_type=BiometricType.FACE_ID,
        status=DeviceStatus.ACTIVE,
        notification_enabled=True,
        last_active_at=datetime.now(timezone.utc),
        registered_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


class TestDeviceService:
    """Test cases for DeviceService"""

    @pytest.mark.asyncio
    async def test_register_new_device(self, device_service, mock_db):
        """Test registering a new device"""
        # Arrange
        user_id = uuid4()
        tenant_id = uuid4()
        data = DeviceRegister(
            device_id="new_device_123",
            device_token="fcm_token_123",
            platform=DevicePlatformSchema.IOS,
            platform_version="17.0",
            device_model="iPhone 15",
            device_name="Test iPhone",
            app_version="2.0.0",
            app_build="100",
            bundle_id="com.healthcare.app",
            locale="en",
            timezone="America/New_York",
            biometric_enabled=False
        )

        # Mock no existing device
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Act
        result = await device_service.register_device(
            mock_db, user_id, "patient", tenant_id, data, "192.168.1.1"
        )

        # Assert
        mock_db.add.assert_called()
        mock_db.commit.assert_called_once()
        assert result is not None

    @pytest.mark.asyncio
    async def test_register_existing_device_updates(self, device_service, mock_db, sample_device):
        """Test registering an existing device updates it"""
        # Arrange
        data = DeviceRegister(
            device_id=sample_device.device_id,
            device_token="new_token",
            platform=DevicePlatformSchema.IOS,
            platform_version="17.1",
            device_model="iPhone 15 Pro Max",
            device_name="Updated iPhone",
            app_version="2.1.0",
            app_build="101",
            bundle_id="com.healthcare.app"
        )

        # Mock existing device
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_device
        mock_db.execute.return_value = mock_result

        # Act
        result = await device_service.register_device(
            mock_db, sample_device.user_id, "patient",
            sample_device.tenant_id, data, "192.168.1.1"
        )

        # Assert
        mock_db.commit.assert_called_once()
        assert sample_device.platform_version == "17.1"
        assert sample_device.device_name == "Updated iPhone"
        assert sample_device.app_version == "2.1.0"

    @pytest.mark.asyncio
    async def test_update_device(self, device_service, mock_db, sample_device):
        """Test updating device information"""
        # Arrange
        data = DeviceUpdate(
            device_name="New Device Name",
            app_version="2.2.0",
            locale="es",
            notification_enabled=False
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_device
        mock_db.execute.return_value = mock_result

        # Act
        result = await device_service.update_device(
            mock_db, sample_device.id, sample_device.user_id, data
        )

        # Assert
        mock_db.commit.assert_called_once()
        assert sample_device.device_name == "New Device Name"
        assert sample_device.app_version == "2.2.0"
        assert sample_device.locale == "es"
        assert sample_device.notification_enabled is False

    @pytest.mark.asyncio
    async def test_update_device_not_found(self, device_service, mock_db):
        """Test updating a non-existent device raises error"""
        # Arrange
        data = DeviceUpdate(device_name="New Name")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Act & Assert
        with pytest.raises(ValueError, match="Device not found"):
            await device_service.update_device(
                mock_db, uuid4(), uuid4(), data
            )

    @pytest.mark.asyncio
    async def test_update_device_security_jailbroken(self, device_service, mock_db, sample_device):
        """Test that jailbroken device gets suspended"""
        # Arrange
        data = DeviceSecurityUpdate(
            is_jailbroken=True,
            is_rooted=False
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_device
        mock_db.execute.return_value = mock_result

        # Act
        result = await device_service.update_device_security(
            mock_db, sample_device.id, data, "192.168.1.1"
        )

        # Assert
        mock_db.add.assert_called()  # Audit log added
        mock_db.commit.assert_called_once()
        assert sample_device.status == DeviceStatus.SUSPENDED
        assert sample_device.is_jailbroken is True

    @pytest.mark.asyncio
    async def test_update_device_security_rooted(self, device_service, mock_db, sample_device):
        """Test that rooted device gets suspended"""
        # Arrange
        sample_device.platform = DevicePlatform.ANDROID
        data = DeviceSecurityUpdate(
            is_jailbroken=False,
            is_rooted=True
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_device
        mock_db.execute.return_value = mock_result

        # Act
        result = await device_service.update_device_security(
            mock_db, sample_device.id, data, "192.168.1.1"
        )

        # Assert
        assert sample_device.status == DeviceStatus.SUSPENDED
        assert sample_device.is_rooted is True

    @pytest.mark.asyncio
    async def test_get_device(self, device_service, mock_db, sample_device):
        """Test getting a device by ID"""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_device
        mock_db.execute.return_value = mock_result

        # Act
        result = await device_service.get_device(
            mock_db, sample_device.id, sample_device.user_id
        )

        # Assert
        assert result.id == sample_device.id
        assert result.device_id == sample_device.device_id
        assert result.platform == sample_device.platform.value

    @pytest.mark.asyncio
    async def test_get_device_not_found(self, device_service, mock_db):
        """Test getting a non-existent device raises error"""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Act & Assert
        with pytest.raises(ValueError, match="Device not found"):
            await device_service.get_device(mock_db, uuid4(), uuid4())

    @pytest.mark.asyncio
    async def test_list_user_devices(self, device_service, mock_db, sample_device):
        """Test listing all devices for a user"""
        # Arrange
        device2 = MagicMock()
        device2.id = uuid4()
        device2.device_id = "device2"
        device2.platform = DevicePlatform.ANDROID
        device2.platform_version = "14.0"
        device2.device_model = "Pixel 8"
        device2.device_name = "Work Phone"
        device2.app_version = "2.0.0"
        device2.app_build = "100"
        device2.status = DeviceStatus.ACTIVE
        device2.notification_enabled = True
        device2.biometric_enabled = False
        device2.biometric_type = None
        device2.locale = "en"
        device2.timezone = "America/New_York"
        device2.registered_at = datetime.now(timezone.utc)
        device2.last_active_at = datetime.now(timezone.utc)
        device2.last_sync_at = None

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_device, device2]
        mock_db.execute.return_value = mock_result

        # Act
        result = await device_service.list_user_devices(
            mock_db, sample_device.user_id, sample_device.tenant_id
        )

        # Assert
        assert result.total == 2
        assert len(result.devices) == 2

    @pytest.mark.asyncio
    async def test_deactivate_device(self, device_service, mock_db, sample_device):
        """Test deactivating a device"""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_device
        mock_db.execute.return_value = mock_result

        # Act
        await device_service.deactivate_device(
            mock_db, sample_device.id, sample_device.user_id, "192.168.1.1"
        )

        # Assert
        mock_db.commit.assert_called_once()
        assert sample_device.status == DeviceStatus.INACTIVE
        assert sample_device.device_token is None

    @pytest.mark.asyncio
    async def test_revoke_device(self, device_service, mock_db, sample_device):
        """Test revoking device access (admin action)"""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_device
        mock_db.execute.return_value = mock_result

        # Act
        await device_service.revoke_device(
            mock_db, sample_device.id, sample_device.tenant_id,
            "Security violation", "192.168.1.1"
        )

        # Assert
        mock_db.commit.assert_called_once()
        assert sample_device.status == DeviceStatus.REVOKED
        assert sample_device.device_token is None

    @pytest.mark.asyncio
    async def test_update_device_token(self, device_service, mock_db):
        """Test updating device push token"""
        # Arrange
        device_id = uuid4()
        new_token = "new_fcm_token_123"

        # Act
        await device_service.update_device_token(mock_db, device_id, new_token)

        # Assert
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_devices_for_notification(self, device_service, mock_db, sample_device):
        """Test getting devices eligible for notifications"""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_device]
        mock_db.execute.return_value = mock_result

        # Act
        result = await device_service.get_devices_for_notification(
            mock_db, sample_device.user_id, sample_device.tenant_id
        )

        # Assert
        assert len(result) == 1
        assert result[0].notification_enabled is True
        assert result[0].device_token is not None


class TestDeviceResponseConversion:
    """Test cases for response conversion"""

    def test_device_to_response(self, device_service, sample_device):
        """Test converting device model to response"""
        # Act
        result = device_service._device_to_response(sample_device)

        # Assert
        assert result.id == sample_device.id
        assert result.device_id == sample_device.device_id
        assert result.platform == sample_device.platform.value
        assert result.platform_version == sample_device.platform_version
        assert result.device_model == sample_device.device_model
        assert result.device_name == sample_device.device_name
        assert result.app_version == sample_device.app_version
        assert result.status == sample_device.status.value
        assert result.notification_enabled == sample_device.notification_enabled
        assert result.biometric_enabled == sample_device.biometric_enabled
        assert result.biometric_type == sample_device.biometric_type.value

    def test_device_to_response_no_biometric(self, device_service, sample_device):
        """Test converting device without biometric to response"""
        # Arrange
        sample_device.biometric_enabled = False
        sample_device.biometric_type = None

        # Act
        result = device_service._device_to_response(sample_device)

        # Assert
        assert result.biometric_enabled is False
        assert result.biometric_type is None
