"""
Device Service for RPM

Handles device registration, assignment, and management.

EPIC-019: Remote Patient Monitoring
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import (
    RPMDevice, DeviceAssignment, DeviceStatus, DeviceType, DeviceVendor
)
from ..schemas import (
    DeviceCreate, DeviceUpdate, DeviceResponse,
    DeviceAssignmentCreate, DeviceAssignmentUpdate, DeviceAssignmentResponse
)

logger = logging.getLogger(__name__)


class DeviceService:
    """Service for managing RPM devices."""

    async def register_device(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        device_data: DeviceCreate
    ) -> RPMDevice:
        """Register a new RPM device."""
        # Check for existing device with same identifier
        existing = await db.execute(
            select(RPMDevice).where(
                and_(
                    RPMDevice.tenant_id == tenant_id,
                    RPMDevice.vendor == device_data.vendor,
                    RPMDevice.device_identifier == device_data.device_identifier
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Device already registered with this identifier")

        device = RPMDevice(
            tenant_id=tenant_id,
            device_identifier=device_data.device_identifier,
            vendor=device_data.vendor,
            device_type=device_data.device_type,
            serial_number=device_data.serial_number,
            mac_address=device_data.mac_address,
            model=device_data.model,
            firmware_version=device_data.firmware_version,
            status=DeviceStatus.REGISTERED,
            metadata=device_data.metadata or {}
        )

        db.add(device)
        await db.commit()
        await db.refresh(device)

        logger.info(f"Registered device {device.id} for tenant {tenant_id}")
        return device

    async def get_device(
        self,
        db: AsyncSession,
        device_id: UUID,
        tenant_id: UUID
    ) -> Optional[RPMDevice]:
        """Get device by ID."""
        result = await db.execute(
            select(RPMDevice).where(
                and_(
                    RPMDevice.id == device_id,
                    RPMDevice.tenant_id == tenant_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_device_by_identifier(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        vendor: DeviceVendor,
        device_identifier: str
    ) -> Optional[RPMDevice]:
        """Get device by vendor and identifier."""
        result = await db.execute(
            select(RPMDevice).where(
                and_(
                    RPMDevice.tenant_id == tenant_id,
                    RPMDevice.vendor == vendor,
                    RPMDevice.device_identifier == device_identifier
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_devices(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        device_type: Optional[DeviceType] = None,
        vendor: Optional[DeviceVendor] = None,
        status: Optional[DeviceStatus] = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[RPMDevice], int]:
        """List devices with filters."""
        query = select(RPMDevice).where(RPMDevice.tenant_id == tenant_id)

        if device_type:
            query = query.where(RPMDevice.device_type == device_type)
        if vendor:
            query = query.where(RPMDevice.vendor == vendor)
        if status:
            query = query.where(RPMDevice.status == status)

        # Count
        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()

        # Paginate
        query = query.offset(skip).limit(limit).order_by(RPMDevice.created_at.desc())
        result = await db.execute(query)
        devices = result.scalars().all()

        return list(devices), total

    async def update_device(
        self,
        db: AsyncSession,
        device_id: UUID,
        tenant_id: UUID,
        update_data: DeviceUpdate
    ) -> Optional[RPMDevice]:
        """Update device information."""
        device = await self.get_device(db, device_id, tenant_id)
        if not device:
            return None

        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(device, field, value)

        device.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(device)

        logger.info(f"Updated device {device_id}")
        return device

    async def update_device_status(
        self,
        db: AsyncSession,
        device_id: UUID,
        tenant_id: UUID,
        status: DeviceStatus,
        battery_level: Optional[int] = None
    ) -> Optional[RPMDevice]:
        """Update device status."""
        device = await self.get_device(db, device_id, tenant_id)
        if not device:
            return None

        device.status = status
        if battery_level is not None:
            device.battery_level = battery_level
        device.last_sync_at = datetime.utcnow()
        device.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(device)
        return device

    async def store_oauth_tokens(
        self,
        db: AsyncSession,
        device_id: UUID,
        tenant_id: UUID,
        access_token: str,
        refresh_token: Optional[str],
        expires_at: Optional[datetime]
    ) -> Optional[RPMDevice]:
        """Store OAuth tokens for vendor API access."""
        device = await self.get_device(db, device_id, tenant_id)
        if not device:
            return None

        device.oauth_access_token = access_token
        device.oauth_refresh_token = refresh_token
        device.oauth_token_expires_at = expires_at
        device.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(device)
        return device

    async def deactivate_device(
        self,
        db: AsyncSession,
        device_id: UUID,
        tenant_id: UUID
    ) -> bool:
        """Deactivate a device."""
        device = await self.get_device(db, device_id, tenant_id)
        if not device:
            return False

        device.status = DeviceStatus.DEACTIVATED
        device.updated_at = datetime.utcnow()

        # Deactivate all assignments
        await db.execute(
            select(DeviceAssignment).where(
                and_(
                    DeviceAssignment.device_id == device_id,
                    DeviceAssignment.is_active == True
                )
            )
        )
        # Note: In production, update assignments here

        await db.commit()
        logger.info(f"Deactivated device {device_id}")
        return True

    # =========================================================================
    # Device Assignments
    # =========================================================================

    async def assign_device(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        assigned_by: UUID,
        assignment_data: DeviceAssignmentCreate
    ) -> DeviceAssignment:
        """Assign a device to a patient."""
        # Verify device exists and is available
        device = await self.get_device(db, assignment_data.device_id, tenant_id)
        if not device:
            raise ValueError("Device not found")

        if device.status in [DeviceStatus.DEACTIVATED, DeviceStatus.LOST]:
            raise ValueError(f"Device is {device.status.value} and cannot be assigned")

        # Check for existing active assignment
        existing = await db.execute(
            select(DeviceAssignment).where(
                and_(
                    DeviceAssignment.device_id == assignment_data.device_id,
                    DeviceAssignment.is_active == True
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Device is already assigned to another patient")

        assignment = DeviceAssignment(
            tenant_id=tenant_id,
            device_id=assignment_data.device_id,
            patient_id=assignment_data.patient_id,
            enrollment_id=assignment_data.enrollment_id,
            assigned_by=assigned_by,
            reading_frequency=assignment_data.reading_frequency,
            target_readings_per_day=assignment_data.target_readings_per_day,
            reminder_times=assignment_data.reminder_times or [],
            notes=assignment_data.notes,
            is_active=True
        )

        # Update device status
        device.status = DeviceStatus.PAIRED

        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)

        logger.info(
            f"Assigned device {assignment_data.device_id} to patient "
            f"{assignment_data.patient_id}"
        )
        return assignment

    async def get_assignment(
        self,
        db: AsyncSession,
        assignment_id: UUID,
        tenant_id: UUID
    ) -> Optional[DeviceAssignment]:
        """Get assignment by ID."""
        result = await db.execute(
            select(DeviceAssignment)
            .options(selectinload(DeviceAssignment.device))
            .where(
                and_(
                    DeviceAssignment.id == assignment_id,
                    DeviceAssignment.tenant_id == tenant_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_patient_assignments(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        patient_id: UUID,
        active_only: bool = True
    ) -> List[DeviceAssignment]:
        """Get all device assignments for a patient."""
        query = select(DeviceAssignment).options(
            selectinload(DeviceAssignment.device)
        ).where(
            and_(
                DeviceAssignment.tenant_id == tenant_id,
                DeviceAssignment.patient_id == patient_id
            )
        )

        if active_only:
            query = query.where(DeviceAssignment.is_active == True)

        result = await db.execute(query.order_by(DeviceAssignment.assigned_at.desc()))
        return list(result.scalars().all())

    async def update_assignment(
        self,
        db: AsyncSession,
        assignment_id: UUID,
        tenant_id: UUID,
        update_data: DeviceAssignmentUpdate
    ) -> Optional[DeviceAssignment]:
        """Update device assignment."""
        assignment = await self.get_assignment(db, assignment_id, tenant_id)
        if not assignment:
            return None

        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(assignment, field, value)

        assignment.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(assignment)
        return assignment

    async def unassign_device(
        self,
        db: AsyncSession,
        assignment_id: UUID,
        tenant_id: UUID,
        unassigned_by: UUID
    ) -> bool:
        """Unassign a device from a patient."""
        assignment = await self.get_assignment(db, assignment_id, tenant_id)
        if not assignment or not assignment.is_active:
            return False

        assignment.is_active = False
        assignment.unassigned_at = datetime.utcnow()
        assignment.unassigned_by = unassigned_by
        assignment.updated_at = datetime.utcnow()

        # Update device status
        if assignment.device:
            assignment.device.status = DeviceStatus.REGISTERED

        await db.commit()
        logger.info(f"Unassigned device {assignment.device_id} from patient")
        return True

    async def get_devices_needing_sync(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        hours_threshold: int = 24
    ) -> List[RPMDevice]:
        """Get devices that haven't synced recently."""
        threshold = datetime.utcnow() - timedelta(hours=hours_threshold)

        result = await db.execute(
            select(RPMDevice).where(
                and_(
                    RPMDevice.tenant_id == tenant_id,
                    RPMDevice.status == DeviceStatus.ACTIVE,
                    or_(
                        RPMDevice.last_sync_at < threshold,
                        RPMDevice.last_sync_at.is_(None)
                    )
                )
            )
        )
        return list(result.scalars().all())


from datetime import timedelta
