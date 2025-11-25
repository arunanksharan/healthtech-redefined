"""
Reading Service for RPM

Handles device readings ingestion, validation, and storage.

EPIC-019: Remote Patient Monitoring
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
import logging
import hashlib

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    DeviceReading, ReadingBatch, DataQualityMetric, RPMDevice,
    ReadingType, ReadingStatus, DeviceStatus
)
from ..schemas import (
    ReadingCreate, ReadingBatchCreate, ReadingUpdate,
    ReadingResponse, ReadingBatchResponse, ReadingFilters,
    BloodPressureReading, GlucoseReading, WeightReading, OxygenSaturationReading
)

logger = logging.getLogger(__name__)


# Validation ranges for different reading types
READING_VALIDATION_RANGES = {
    ReadingType.BLOOD_PRESSURE_SYSTOLIC: (40, 300),
    ReadingType.BLOOD_PRESSURE_DIASTOLIC: (20, 200),
    ReadingType.HEART_RATE: (20, 300),
    ReadingType.BLOOD_GLUCOSE: (10, 700),
    ReadingType.OXYGEN_SATURATION: (50, 100),
    ReadingType.BODY_WEIGHT: (1, 500),  # kg
    ReadingType.BODY_TEMPERATURE: (30, 45),  # Celsius
    ReadingType.RESPIRATORY_RATE: (4, 60),
    ReadingType.STEPS: (0, 100000),
}


class ReadingService:
    """Service for managing device readings."""

    def _validate_reading(
        self,
        reading_type: ReadingType,
        value: float
    ) -> Tuple[bool, List[str]]:
        """Validate reading value against physiological ranges."""
        errors = []

        if reading_type in READING_VALIDATION_RANGES:
            min_val, max_val = READING_VALIDATION_RANGES[reading_type]
            if value < min_val or value > max_val:
                errors.append(
                    f"Value {value} outside valid range [{min_val}, {max_val}]"
                )

        return len(errors) == 0, errors

    def _generate_reading_hash(
        self,
        patient_id: UUID,
        reading_type: ReadingType,
        measured_at: datetime,
        value: float
    ) -> str:
        """Generate hash for duplicate detection."""
        data = f"{patient_id}:{reading_type.value}:{measured_at.isoformat()}:{value}"
        return hashlib.md5(data.encode()).hexdigest()

    async def _check_duplicate(
        self,
        db: AsyncSession,
        patient_id: UUID,
        reading_type: ReadingType,
        measured_at: datetime,
        value: float,
        window_seconds: int = 60
    ) -> bool:
        """Check if a similar reading exists within time window."""
        window_start = measured_at - timedelta(seconds=window_seconds)
        window_end = measured_at + timedelta(seconds=window_seconds)

        result = await db.execute(
            select(DeviceReading).where(
                and_(
                    DeviceReading.patient_id == patient_id,
                    DeviceReading.reading_type == reading_type,
                    DeviceReading.measured_at.between(window_start, window_end),
                    DeviceReading.value == value,
                    DeviceReading.status != ReadingStatus.DUPLICATE
                )
            ).limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def create_reading(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        reading_data: ReadingCreate
    ) -> DeviceReading:
        """Create a single device reading."""
        # Validate reading
        is_valid, errors = self._validate_reading(
            reading_data.reading_type,
            reading_data.value
        )

        # Check for duplicates
        is_duplicate = await self._check_duplicate(
            db,
            reading_data.patient_id,
            reading_data.reading_type,
            reading_data.measured_at,
            reading_data.value
        )

        status = ReadingStatus.PENDING
        if is_duplicate:
            status = ReadingStatus.DUPLICATE
        elif not is_valid:
            status = ReadingStatus.FLAGGED

        reading = DeviceReading(
            tenant_id=tenant_id,
            patient_id=reading_data.patient_id,
            device_id=reading_data.device_id,
            enrollment_id=reading_data.enrollment_id,
            reading_type=reading_data.reading_type,
            value=reading_data.value,
            unit=reading_data.unit,
            secondary_value=reading_data.secondary_value,
            secondary_unit=reading_data.secondary_unit,
            measured_at=reading_data.measured_at,
            timezone=reading_data.timezone,
            status=status,
            is_manual=reading_data.is_manual,
            source=reading_data.source,
            is_valid=is_valid and not is_duplicate,
            validation_errors=errors,
            context=reading_data.context or {},
            raw_data=reading_data.raw_data or {}
        )

        db.add(reading)

        # Update device last reading timestamp
        if reading_data.device_id:
            device_result = await db.execute(
                select(RPMDevice).where(RPMDevice.id == reading_data.device_id)
            )
            device = device_result.scalar_one_or_none()
            if device:
                device.last_reading_at = datetime.utcnow()
                device.status = DeviceStatus.ACTIVE

        await db.commit()
        await db.refresh(reading)

        logger.debug(
            f"Created reading {reading.id} for patient {reading_data.patient_id}"
        )
        return reading

    async def create_batch_readings(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        batch_data: ReadingBatchCreate
    ) -> ReadingBatchResponse:
        """Process a batch of readings."""
        batch = ReadingBatch(
            tenant_id=tenant_id,
            source=batch_data.source,
            source_reference=batch_data.source_reference,
            total_readings=len(batch_data.readings),
            status="processing",
            started_at=datetime.utcnow()
        )
        db.add(batch)
        await db.flush()

        processed = 0
        failed = 0
        duplicates = 0
        errors = []

        for i, reading_data in enumerate(batch_data.readings):
            try:
                reading = await self.create_reading(db, tenant_id, reading_data)
                if reading.status == ReadingStatus.DUPLICATE:
                    duplicates += 1
                processed += 1
            except Exception as e:
                failed += 1
                errors.append({
                    "index": i,
                    "patient_id": str(reading_data.patient_id),
                    "error": str(e)
                })
                logger.error(f"Failed to process reading {i}: {e}")

        batch.processed_readings = processed
        batch.failed_readings = failed
        batch.duplicate_readings = duplicates
        batch.status = "completed" if failed == 0 else "completed_with_errors"
        batch.completed_at = datetime.utcnow()

        await db.commit()

        logger.info(
            f"Batch {batch.id}: {processed} processed, {failed} failed, "
            f"{duplicates} duplicates"
        )

        return ReadingBatchResponse(
            batch_id=batch.id,
            total_readings=batch.total_readings,
            processed_readings=processed,
            failed_readings=failed,
            duplicate_readings=duplicates,
            status=batch.status,
            errors=errors
        )

    async def get_reading(
        self,
        db: AsyncSession,
        reading_id: UUID,
        tenant_id: UUID
    ) -> Optional[DeviceReading]:
        """Get reading by ID."""
        result = await db.execute(
            select(DeviceReading).where(
                and_(
                    DeviceReading.id == reading_id,
                    DeviceReading.tenant_id == tenant_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_readings(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        filters: ReadingFilters,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[DeviceReading], int]:
        """List readings with filters."""
        query = select(DeviceReading).where(DeviceReading.tenant_id == tenant_id)

        if filters.patient_id:
            query = query.where(DeviceReading.patient_id == filters.patient_id)
        if filters.device_id:
            query = query.where(DeviceReading.device_id == filters.device_id)
        if filters.enrollment_id:
            query = query.where(DeviceReading.enrollment_id == filters.enrollment_id)
        if filters.reading_type:
            query = query.where(DeviceReading.reading_type == filters.reading_type)
        if filters.status:
            query = query.where(DeviceReading.status == filters.status)
        if filters.start_date:
            query = query.where(DeviceReading.measured_at >= filters.start_date)
        if filters.end_date:
            query = query.where(DeviceReading.measured_at <= filters.end_date)
        if filters.is_manual is not None:
            query = query.where(DeviceReading.is_manual == filters.is_manual)
        if filters.is_valid is not None:
            query = query.where(DeviceReading.is_valid == filters.is_valid)

        # Count
        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()

        # Paginate
        query = query.offset(skip).limit(limit).order_by(
            DeviceReading.measured_at.desc()
        )
        result = await db.execute(query)
        readings = result.scalars().all()

        return list(readings), total

    async def get_patient_readings(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        patient_id: UUID,
        reading_type: Optional[ReadingType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[DeviceReading]:
        """Get readings for a specific patient."""
        query = select(DeviceReading).where(
            and_(
                DeviceReading.tenant_id == tenant_id,
                DeviceReading.patient_id == patient_id,
                DeviceReading.is_valid == True
            )
        )

        if reading_type:
            query = query.where(DeviceReading.reading_type == reading_type)
        if start_date:
            query = query.where(DeviceReading.measured_at >= start_date)
        if end_date:
            query = query.where(DeviceReading.measured_at <= end_date)

        query = query.order_by(DeviceReading.measured_at.desc()).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def update_reading(
        self,
        db: AsyncSession,
        reading_id: UUID,
        tenant_id: UUID,
        update_data: ReadingUpdate
    ) -> Optional[DeviceReading]:
        """Update reading status."""
        reading = await self.get_reading(db, reading_id, tenant_id)
        if not reading:
            return None

        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(reading, field, value)

        await db.commit()
        await db.refresh(reading)
        return reading

    async def validate_reading(
        self,
        db: AsyncSession,
        reading_id: UUID,
        tenant_id: UUID,
        validated_by: UUID
    ) -> Optional[DeviceReading]:
        """Mark reading as validated."""
        reading = await self.get_reading(db, reading_id, tenant_id)
        if not reading:
            return None

        reading.status = ReadingStatus.VALIDATED
        reading.is_valid = True
        reading.metadata = reading.metadata or {}
        reading.metadata["validated_by"] = str(validated_by)
        reading.metadata["validated_at"] = datetime.utcnow().isoformat()

        await db.commit()
        await db.refresh(reading)
        return reading

    async def get_latest_reading(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        patient_id: UUID,
        reading_type: ReadingType
    ) -> Optional[DeviceReading]:
        """Get the most recent reading of a specific type."""
        result = await db.execute(
            select(DeviceReading).where(
                and_(
                    DeviceReading.tenant_id == tenant_id,
                    DeviceReading.patient_id == patient_id,
                    DeviceReading.reading_type == reading_type,
                    DeviceReading.is_valid == True
                )
            ).order_by(DeviceReading.measured_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_reading_stats(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        patient_id: UUID,
        reading_type: ReadingType,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get statistical summary of readings."""
        result = await db.execute(
            select(
                func.count(DeviceReading.id).label("count"),
                func.avg(DeviceReading.value).label("avg"),
                func.min(DeviceReading.value).label("min"),
                func.max(DeviceReading.value).label("max"),
                func.stddev(DeviceReading.value).label("stddev")
            ).where(
                and_(
                    DeviceReading.tenant_id == tenant_id,
                    DeviceReading.patient_id == patient_id,
                    DeviceReading.reading_type == reading_type,
                    DeviceReading.measured_at.between(start_date, end_date),
                    DeviceReading.is_valid == True
                )
            )
        )
        row = result.one()

        return {
            "count": row.count or 0,
            "avg": float(row.avg) if row.avg else None,
            "min": float(row.min) if row.min else None,
            "max": float(row.max) if row.max else None,
            "stddev": float(row.stddev) if row.stddev else None
        }

    # =========================================================================
    # Convenience methods for specific reading types
    # =========================================================================

    async def create_blood_pressure_reading(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        bp_data: BloodPressureReading
    ) -> List[DeviceReading]:
        """Create blood pressure readings (systolic and diastolic)."""
        readings = []

        # Systolic
        systolic = ReadingCreate(
            patient_id=bp_data.patient_id,
            device_id=bp_data.device_id,
            enrollment_id=bp_data.enrollment_id,
            reading_type=ReadingType.BLOOD_PRESSURE_SYSTOLIC,
            value=bp_data.systolic,
            unit="mmHg",
            secondary_value=bp_data.diastolic,
            secondary_unit="mmHg",
            measured_at=bp_data.measured_at,
            is_manual=bp_data.is_manual,
            context={
                "position": bp_data.position,
                "arm": bp_data.arm,
                **(bp_data.context or {})
            }
        )
        readings.append(await self.create_reading(db, tenant_id, systolic))

        # Heart rate if provided
        if bp_data.pulse:
            pulse = ReadingCreate(
                patient_id=bp_data.patient_id,
                device_id=bp_data.device_id,
                enrollment_id=bp_data.enrollment_id,
                reading_type=ReadingType.HEART_RATE,
                value=bp_data.pulse,
                unit="bpm",
                measured_at=bp_data.measured_at,
                is_manual=bp_data.is_manual,
                context=bp_data.context
            )
            readings.append(await self.create_reading(db, tenant_id, pulse))

        return readings

    async def create_glucose_reading(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        glucose_data: GlucoseReading
    ) -> DeviceReading:
        """Create glucose reading."""
        reading = ReadingCreate(
            patient_id=glucose_data.patient_id,
            device_id=glucose_data.device_id,
            enrollment_id=glucose_data.enrollment_id,
            reading_type=ReadingType.BLOOD_GLUCOSE,
            value=glucose_data.value,
            unit=glucose_data.unit,
            measured_at=glucose_data.measured_at,
            is_manual=glucose_data.is_manual,
            context={
                "meal_context": glucose_data.meal_context,
                **(glucose_data.context or {})
            }
        )
        return await self.create_reading(db, tenant_id, reading)

    async def create_weight_reading(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        weight_data: WeightReading
    ) -> DeviceReading:
        """Create weight reading."""
        reading = ReadingCreate(
            patient_id=weight_data.patient_id,
            device_id=weight_data.device_id,
            enrollment_id=weight_data.enrollment_id,
            reading_type=ReadingType.BODY_WEIGHT,
            value=weight_data.value,
            unit=weight_data.unit,
            measured_at=weight_data.measured_at,
            is_manual=weight_data.is_manual,
            context={
                "body_fat_percent": weight_data.body_fat_percent,
                "muscle_mass_kg": weight_data.muscle_mass_kg,
                "water_percent": weight_data.water_percent,
                **(weight_data.context or {})
            }
        )
        return await self.create_reading(db, tenant_id, reading)

    async def create_spo2_reading(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        spo2_data: OxygenSaturationReading
    ) -> List[DeviceReading]:
        """Create SpO2 reading."""
        readings = []

        # SpO2
        spo2 = ReadingCreate(
            patient_id=spo2_data.patient_id,
            device_id=spo2_data.device_id,
            enrollment_id=spo2_data.enrollment_id,
            reading_type=ReadingType.OXYGEN_SATURATION,
            value=spo2_data.spo2,
            unit="%",
            measured_at=spo2_data.measured_at,
            is_manual=spo2_data.is_manual,
            context={
                "perfusion_index": spo2_data.perfusion_index,
                **(spo2_data.context or {})
            }
        )
        readings.append(await self.create_reading(db, tenant_id, spo2))

        # Pulse if provided
        if spo2_data.pulse:
            pulse = ReadingCreate(
                patient_id=spo2_data.patient_id,
                device_id=spo2_data.device_id,
                enrollment_id=spo2_data.enrollment_id,
                reading_type=ReadingType.HEART_RATE,
                value=spo2_data.pulse,
                unit="bpm",
                measured_at=spo2_data.measured_at,
                is_manual=spo2_data.is_manual,
                context=spo2_data.context
            )
            readings.append(await self.create_reading(db, tenant_id, pulse))

        return readings
