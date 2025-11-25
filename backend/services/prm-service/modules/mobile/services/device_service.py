"""
Mobile Device Service
EPIC-016: Device registration and management
"""
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func, desc

from modules.mobile.models import (
    MobileDevice, MobileSession, MobileAuditLog,
    DevicePlatform, DeviceStatus, SessionStatus
)
from modules.mobile.schemas import (
    DeviceRegister, DeviceUpdate, DeviceSecurityUpdate,
    DeviceResponse, DeviceListResponse
)


class DeviceService:
    """
    Handles mobile device management:
    - Device registration
    - Device updates
    - Security validation
    - Device lifecycle
    """

    async def register_device(
        self,
        db: AsyncSession,
        user_id: UUID,
        user_type: str,
        tenant_id: UUID,
        data: DeviceRegister,
        ip_address: str = None
    ) -> DeviceResponse:
        """Register a new mobile device or update existing"""

        # Check if device already registered
        result = await db.execute(
            select(MobileDevice).where(
                and_(
                    MobileDevice.tenant_id == tenant_id,
                    MobileDevice.device_id == data.device_id
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing device
            existing.user_id = user_id
            existing.user_type = user_type
            existing.device_token = data.device_token
            existing.platform_version = data.platform_version
            existing.device_model = data.device_model
            existing.device_name = data.device_name
            existing.app_version = data.app_version
            existing.app_build = data.app_build
            existing.bundle_id = data.bundle_id
            existing.locale = data.locale or "en"
            existing.timezone = data.timezone
            existing.biometric_enabled = data.biometric_enabled
            if data.biometric_type:
                from modules.mobile.models import BiometricType
                existing.biometric_type = BiometricType(data.biometric_type.value)
            existing.status = DeviceStatus.ACTIVE
            existing.last_active_at = datetime.now(timezone.utc)
            existing.last_ip_address = ip_address
            existing.token_updated_at = datetime.now(timezone.utc) if data.device_token else existing.token_updated_at
            existing.updated_at = datetime.now(timezone.utc)

            device = existing
        else:
            # Create new device
            from modules.mobile.models import BiometricType
            device = MobileDevice(
                id=uuid4(),
                tenant_id=tenant_id,
                user_id=user_id,
                user_type=user_type,
                device_id=data.device_id,
                device_token=data.device_token,
                platform=DevicePlatform(data.platform.value),
                platform_version=data.platform_version,
                device_model=data.device_model,
                device_name=data.device_name,
                app_version=data.app_version,
                app_build=data.app_build,
                bundle_id=data.bundle_id,
                locale=data.locale or "en",
                timezone=data.timezone,
                biometric_enabled=data.biometric_enabled,
                biometric_type=BiometricType(data.biometric_type.value) if data.biometric_type else None,
                status=DeviceStatus.ACTIVE,
                last_ip_address=ip_address,
                token_updated_at=datetime.now(timezone.utc) if data.device_token else None
            )
            db.add(device)

        # Log registration
        audit_log = MobileAuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            device_id=device.id,
            action="device_registered" if not existing else "device_updated",
            action_category="device",
            action_description=f"Device {data.device_id} {'registered' if not existing else 'updated'}",
            details={
                "platform": data.platform.value,
                "app_version": data.app_version
            },
            ip_address=ip_address,
            success=True
        )
        db.add(audit_log)

        await db.commit()
        await db.refresh(device)

        return self._device_to_response(device)

    async def update_device(
        self,
        db: AsyncSession,
        device_id: UUID,
        user_id: UUID,
        data: DeviceUpdate
    ) -> DeviceResponse:
        """Update device information"""

        result = await db.execute(
            select(MobileDevice).where(
                and_(
                    MobileDevice.id == device_id,
                    MobileDevice.user_id == user_id
                )
            )
        )
        device = result.scalar_one_or_none()

        if not device:
            raise ValueError("Device not found")

        if data.device_token is not None:
            device.device_token = data.device_token
            device.token_updated_at = datetime.now(timezone.utc)
        if data.platform_version is not None:
            device.platform_version = data.platform_version
        if data.device_name is not None:
            device.device_name = data.device_name
        if data.app_version is not None:
            device.app_version = data.app_version
        if data.app_build is not None:
            device.app_build = data.app_build
        if data.locale is not None:
            device.locale = data.locale
        if data.timezone is not None:
            device.timezone = data.timezone
        if data.notification_enabled is not None:
            device.notification_enabled = data.notification_enabled
        if data.notification_preferences is not None:
            device.notification_preferences = data.notification_preferences
        if data.biometric_enabled is not None:
            device.biometric_enabled = data.biometric_enabled
        if data.biometric_type is not None:
            from modules.mobile.models import BiometricType
            device.biometric_type = BiometricType(data.biometric_type.value)

        device.last_active_at = datetime.now(timezone.utc)
        device.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(device)

        return self._device_to_response(device)

    async def update_device_security(
        self,
        db: AsyncSession,
        device_id: UUID,
        data: DeviceSecurityUpdate,
        ip_address: str = None
    ) -> DeviceResponse:
        """Update device security flags"""

        result = await db.execute(
            select(MobileDevice).where(MobileDevice.id == device_id)
        )
        device = result.scalar_one_or_none()

        if not device:
            raise ValueError("Device not found")

        if data.is_jailbroken is not None:
            device.is_jailbroken = data.is_jailbroken
        if data.is_rooted is not None:
            device.is_rooted = data.is_rooted
        if data.device_fingerprint is not None:
            device.device_fingerprint = data.device_fingerprint

        # Suspend if jailbroken/rooted
        if device.is_jailbroken or device.is_rooted:
            device.status = DeviceStatus.SUSPENDED

            # Log security event
            audit_log = MobileAuditLog(
                id=uuid4(),
                tenant_id=device.tenant_id,
                user_id=device.user_id,
                device_id=device.id,
                action="device_security_violation",
                action_category="security",
                action_description="Device detected as jailbroken/rooted",
                details={
                    "is_jailbroken": device.is_jailbroken,
                    "is_rooted": device.is_rooted
                },
                ip_address=ip_address,
                success=True
            )
            db.add(audit_log)

        device.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(device)

        return self._device_to_response(device)

    async def get_device(
        self,
        db: AsyncSession,
        device_id: UUID,
        user_id: UUID
    ) -> DeviceResponse:
        """Get device by ID"""

        result = await db.execute(
            select(MobileDevice).where(
                and_(
                    MobileDevice.id == device_id,
                    MobileDevice.user_id == user_id
                )
            )
        )
        device = result.scalar_one_or_none()

        if not device:
            raise ValueError("Device not found")

        return self._device_to_response(device)

    async def list_user_devices(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        status: Optional[DeviceStatus] = None
    ) -> DeviceListResponse:
        """List all devices for a user"""

        query = select(MobileDevice).where(
            and_(
                MobileDevice.user_id == user_id,
                MobileDevice.tenant_id == tenant_id
            )
        )

        if status:
            query = query.where(MobileDevice.status == status)

        query = query.order_by(desc(MobileDevice.last_active_at))

        result = await db.execute(query)
        devices = result.scalars().all()

        return DeviceListResponse(
            devices=[self._device_to_response(d) for d in devices],
            total=len(devices)
        )

    async def update_device_token(
        self,
        db: AsyncSession,
        device_id: UUID,
        device_token: str
    ) -> None:
        """Update device push notification token"""

        await db.execute(
            update(MobileDevice).where(
                MobileDevice.id == device_id
            ).values(
                device_token=device_token,
                token_updated_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
        )
        await db.commit()

    async def deactivate_device(
        self,
        db: AsyncSession,
        device_id: UUID,
        user_id: UUID,
        ip_address: str = None
    ) -> None:
        """Deactivate a device"""

        result = await db.execute(
            select(MobileDevice).where(
                and_(
                    MobileDevice.id == device_id,
                    MobileDevice.user_id == user_id
                )
            )
        )
        device = result.scalar_one_or_none()

        if not device:
            raise ValueError("Device not found")

        device.status = DeviceStatus.INACTIVE
        device.device_token = None  # Clear push token
        device.updated_at = datetime.now(timezone.utc)

        # Revoke all active sessions for this device
        await db.execute(
            update(MobileSession).where(
                and_(
                    MobileSession.device_id == device_id,
                    MobileSession.status == SessionStatus.ACTIVE
                )
            ).values(
                status=SessionStatus.REVOKED,
                ended_at=datetime.now(timezone.utc)
            )
        )

        # Log deactivation
        audit_log = MobileAuditLog(
            id=uuid4(),
            tenant_id=device.tenant_id,
            user_id=user_id,
            device_id=device_id,
            action="device_deactivated",
            action_category="device",
            action_description="Device deactivated by user",
            ip_address=ip_address,
            success=True
        )
        db.add(audit_log)

        await db.commit()

    async def revoke_device(
        self,
        db: AsyncSession,
        device_id: UUID,
        tenant_id: UUID,
        reason: str = None,
        ip_address: str = None
    ) -> None:
        """Revoke device access (admin action)"""

        result = await db.execute(
            select(MobileDevice).where(
                and_(
                    MobileDevice.id == device_id,
                    MobileDevice.tenant_id == tenant_id
                )
            )
        )
        device = result.scalar_one_or_none()

        if not device:
            raise ValueError("Device not found")

        device.status = DeviceStatus.REVOKED
        device.device_token = None
        device.updated_at = datetime.now(timezone.utc)

        # Revoke all sessions
        await db.execute(
            update(MobileSession).where(
                MobileSession.device_id == device_id
            ).values(
                status=SessionStatus.REVOKED,
                ended_at=datetime.now(timezone.utc)
            )
        )

        # Log revocation
        audit_log = MobileAuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=device.user_id,
            device_id=device_id,
            action="device_revoked",
            action_category="security",
            action_description=f"Device access revoked: {reason or 'Admin action'}",
            details={"reason": reason},
            ip_address=ip_address,
            success=True
        )
        db.add(audit_log)

        await db.commit()

    async def update_last_active(
        self,
        db: AsyncSession,
        device_id: UUID,
        ip_address: str = None
    ) -> None:
        """Update device last activity timestamp"""

        await db.execute(
            update(MobileDevice).where(
                MobileDevice.id == device_id
            ).values(
                last_active_at=datetime.now(timezone.utc),
                last_ip_address=ip_address
            )
        )
        await db.commit()

    async def get_devices_for_notification(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID
    ) -> List[MobileDevice]:
        """Get active devices with notification enabled for a user"""

        result = await db.execute(
            select(MobileDevice).where(
                and_(
                    MobileDevice.user_id == user_id,
                    MobileDevice.tenant_id == tenant_id,
                    MobileDevice.status == DeviceStatus.ACTIVE,
                    MobileDevice.notification_enabled == True,
                    MobileDevice.device_token.isnot(None)
                )
            )
        )
        return result.scalars().all()

    def _device_to_response(self, device: MobileDevice) -> DeviceResponse:
        """Convert device model to response"""
        return DeviceResponse(
            id=device.id,
            device_id=device.device_id,
            platform=device.platform.value,
            platform_version=device.platform_version,
            device_model=device.device_model,
            device_name=device.device_name,
            app_version=device.app_version,
            app_build=device.app_build,
            status=device.status.value,
            notification_enabled=device.notification_enabled,
            biometric_enabled=device.biometric_enabled,
            biometric_type=device.biometric_type.value if device.biometric_type else None,
            locale=device.locale,
            timezone=device.timezone,
            registered_at=device.registered_at,
            last_active_at=device.last_active_at,
            last_sync_at=device.last_sync_at
        )
