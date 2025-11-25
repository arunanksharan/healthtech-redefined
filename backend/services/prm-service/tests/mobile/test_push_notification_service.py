"""
Push Notification Service Tests
EPIC-016: Unit tests for push notification handling
"""
import pytest
from datetime import datetime, timezone, time, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal

from modules.mobile.services.push_notification_service import PushNotificationService
from modules.mobile.models import (
    MobileDevice, PushNotification, NotificationPreference,
    DevicePlatform, DeviceStatus, NotificationType,
    NotificationPriority, NotificationStatus
)
from modules.mobile.schemas import (
    NotificationSend, NotificationBulkSend, NotificationPreferenceUpdate,
    NotificationTypeSchema, NotificationPrioritySchema
)


@pytest.fixture
def notification_service():
    return PushNotificationService()


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
        notification_enabled=True
    )


@pytest.fixture
def sample_notification():
    return PushNotification(
        id=uuid4(),
        tenant_id=uuid4(),
        user_id=uuid4(),
        notification_type=NotificationType.APPOINTMENT_REMINDER,
        priority=NotificationPriority.NORMAL,
        title="Appointment Reminder",
        body="You have an appointment tomorrow at 10:00 AM",
        data_payload={"appointment_id": "123"},
        status=NotificationStatus.PENDING,
        created_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def sample_preferences():
    return NotificationPreference(
        id=uuid4(),
        tenant_id=uuid4(),
        user_id=uuid4(),
        device_id=uuid4(),
        enabled=True,
        appointment_reminders=True,
        medication_reminders=True,
        health_alerts=True,
        lab_results=True,
        messages=True,
        billing_alerts=True,
        marketing=False,
        quiet_hours_enabled=False,
        sound_enabled=True,
        vibration_enabled=True,
        badge_enabled=True
    )


class TestPushNotificationService:
    """Test cases for PushNotificationService"""

    @pytest.mark.asyncio
    async def test_send_notification_success(self, notification_service, mock_db, sample_device):
        """Test sending a notification successfully"""
        # Arrange
        data = NotificationSend(
            notification_type=NotificationTypeSchema.APPOINTMENT_REMINDER,
            priority=NotificationPrioritySchema.NORMAL,
            title="Appointment Reminder",
            body="You have an appointment tomorrow"
        )

        # Mock device service
        with patch.object(notification_service, '_get_user_preferences', return_value=None):
            with patch('modules.mobile.services.push_notification_service.DeviceService') as MockDeviceService:
                mock_device_service = MockDeviceService.return_value
                mock_device_service.get_devices_for_notification = AsyncMock(return_value=[sample_device])

                with patch.object(notification_service, '_send_to_device', return_value=True):
                    # Act
                    result = await notification_service.send_notification(
                        mock_db, sample_device.tenant_id, sample_device.user_id, data
                    )

                    # Assert
                    mock_db.add.assert_called()
                    mock_db.commit.assert_called()
                    assert result is not None

    @pytest.mark.asyncio
    async def test_send_notification_no_devices(self, notification_service, mock_db):
        """Test sending notification when user has no devices"""
        # Arrange
        data = NotificationSend(
            notification_type=NotificationTypeSchema.GENERAL,
            title="Test",
            body="Test body"
        )

        with patch('modules.mobile.services.push_notification_service.DeviceService') as MockDeviceService:
            mock_device_service = MockDeviceService.return_value
            mock_device_service.get_devices_for_notification = AsyncMock(return_value=[])

            # Act & Assert
            with pytest.raises(ValueError, match="No devices available"):
                await notification_service.send_notification(
                    mock_db, uuid4(), uuid4(), data
                )

    @pytest.mark.asyncio
    async def test_send_notification_respects_preferences(self, notification_service, mock_db, sample_device, sample_preferences):
        """Test that notifications respect user preferences"""
        # Arrange
        sample_preferences.marketing = False
        data = NotificationSend(
            notification_type=NotificationTypeSchema.PROMOTIONAL,
            title="Special Offer",
            body="Get 20% off"
        )

        with patch.object(notification_service, '_get_user_preferences', return_value=sample_preferences):
            with patch('modules.mobile.services.push_notification_service.DeviceService') as MockDeviceService:
                mock_device_service = MockDeviceService.return_value
                mock_device_service.get_devices_for_notification = AsyncMock(return_value=[sample_device])

                # Act & Assert
                with pytest.raises(ValueError, match="User has disabled"):
                    await notification_service.send_notification(
                        mock_db, sample_device.tenant_id, sample_device.user_id, data
                    )

    @pytest.mark.asyncio
    async def test_schedule_notification(self, notification_service, mock_db):
        """Test scheduling a notification for later"""
        # Arrange
        data = NotificationSend(
            notification_type=NotificationTypeSchema.APPOINTMENT_REMINDER,
            title="Upcoming Appointment",
            body="Your appointment is in 1 hour"
        )
        scheduled_time = datetime.now(timezone.utc) + timedelta(hours=1)

        # Act
        result = await notification_service.schedule_notification(
            mock_db, uuid4(), uuid4(), data, scheduled_time
        )

        # Assert
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_notification_read(self, notification_service, mock_db):
        """Test marking a notification as read"""
        # Arrange
        notification_id = uuid4()
        user_id = uuid4()

        # Act
        await notification_service.mark_notification_read(mock_db, notification_id, user_id)

        # Assert
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_notification_clicked(self, notification_service, mock_db):
        """Test marking a notification as clicked"""
        # Arrange
        notification_id = uuid4()
        user_id = uuid4()

        # Act
        await notification_service.mark_notification_clicked(mock_db, notification_id, user_id)

        # Assert
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_scheduled_notification(self, notification_service, mock_db, sample_notification):
        """Test cancelling a scheduled notification"""
        # Arrange
        sample_notification.status = NotificationStatus.SCHEDULED
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_notification
        mock_db.execute.return_value = mock_result

        # Act
        await notification_service.cancel_notification(
            mock_db, sample_notification.id, sample_notification.tenant_id
        )

        # Assert
        mock_db.commit.assert_called_once()
        assert sample_notification.status == NotificationStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_notification_not_found(self, notification_service, mock_db):
        """Test cancelling a non-existent notification raises error"""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Act & Assert
        with pytest.raises(ValueError, match="Notification not found"):
            await notification_service.cancel_notification(mock_db, uuid4(), uuid4())

    @pytest.mark.asyncio
    async def test_mark_all_read(self, notification_service, mock_db):
        """Test marking all notifications as read"""
        # Arrange
        mock_result = MagicMock()
        mock_result.rowcount = 5
        mock_db.execute.return_value = mock_result

        # Act
        count = await notification_service.mark_all_read(mock_db, uuid4(), uuid4())

        # Assert
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()
        assert count == 5

    @pytest.mark.asyncio
    async def test_update_preferences(self, notification_service, mock_db, sample_preferences):
        """Test updating notification preferences"""
        # Arrange
        data = NotificationPreferenceUpdate(
            enabled=True,
            appointment_reminders=False,
            quiet_hours_enabled=True,
            quiet_hours_start="22:00",
            quiet_hours_end="07:00"
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_preferences
        mock_db.execute.return_value = mock_result

        # Act
        result = await notification_service.update_preferences(
            mock_db, sample_preferences.user_id, sample_preferences.tenant_id,
            sample_preferences.device_id, data
        )

        # Assert
        mock_db.commit.assert_called_once()
        assert sample_preferences.appointment_reminders is False
        assert sample_preferences.quiet_hours_enabled is True

    @pytest.mark.asyncio
    async def test_update_preferences_creates_new(self, notification_service, mock_db):
        """Test updating preferences creates new record if none exists"""
        # Arrange
        user_id = uuid4()
        tenant_id = uuid4()
        device_id = uuid4()
        data = NotificationPreferenceUpdate(
            enabled=True,
            marketing=False
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Act
        result = await notification_service.update_preferences(
            mock_db, user_id, tenant_id, device_id, data
        )

        # Assert
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_preferences_returns_defaults(self, notification_service, mock_db):
        """Test getting preferences returns defaults when none exist"""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Act
        result = await notification_service.get_preferences(mock_db, uuid4(), uuid4())

        # Assert
        assert result.enabled is True
        assert result.appointment_reminders is True
        assert result.marketing is False


class TestNotificationPreferenceLogic:
    """Test cases for notification preference logic"""

    def test_should_send_appointment_reminder(self, notification_service, sample_preferences):
        """Test appointment reminders are sent when enabled"""
        result = notification_service._should_send(
            NotificationType.APPOINTMENT_REMINDER, sample_preferences
        )
        assert result is True

    def test_should_not_send_marketing_disabled(self, notification_service, sample_preferences):
        """Test marketing notifications blocked when disabled"""
        sample_preferences.marketing = False
        result = notification_service._should_send(
            NotificationType.PROMOTIONAL, sample_preferences
        )
        assert result is False

    def test_should_not_send_when_all_disabled(self, notification_service, sample_preferences):
        """Test no notifications sent when globally disabled"""
        sample_preferences.enabled = False
        result = notification_service._should_send(
            NotificationType.GENERAL, sample_preferences
        )
        assert result is False

    def test_in_quiet_hours_disabled(self, notification_service, sample_preferences):
        """Test quiet hours check when disabled"""
        sample_preferences.quiet_hours_enabled = False
        result = notification_service._in_quiet_hours(sample_preferences)
        assert result is False

    def test_in_quiet_hours_no_times_set(self, notification_service, sample_preferences):
        """Test quiet hours check when times not set"""
        sample_preferences.quiet_hours_enabled = True
        sample_preferences.quiet_hours_start = None
        sample_preferences.quiet_hours_end = None
        result = notification_service._in_quiet_hours(sample_preferences)
        assert result is False


class TestNotificationResponseConversion:
    """Test cases for response conversion"""

    def test_notification_to_response(self, notification_service, sample_notification):
        """Test converting notification model to response"""
        # Act
        result = notification_service._notification_to_response(sample_notification)

        # Assert
        assert result.id == sample_notification.id
        assert result.notification_type == sample_notification.notification_type.value
        assert result.priority == sample_notification.priority.value
        assert result.title == sample_notification.title
        assert result.body == sample_notification.body
        assert result.status == sample_notification.status.value

    def test_preferences_to_response(self, notification_service, sample_preferences):
        """Test converting preferences model to response"""
        # Act
        result = notification_service._preferences_to_response(sample_preferences)

        # Assert
        assert result.enabled == sample_preferences.enabled
        assert result.appointment_reminders == sample_preferences.appointment_reminders
        assert result.marketing == sample_preferences.marketing
        assert result.quiet_hours_enabled == sample_preferences.quiet_hours_enabled
