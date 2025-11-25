"""
Enrollment Service for RPM

Handles patient RPM program enrollments.

EPIC-019: Remote Patient Monitoring
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
import logging

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import (
    RPMEnrollment, MonitoringPeriod, DeviceAssignment, DeviceReading,
    CareProtocol, EnrollmentStatus
)
from ..schemas import (
    EnrollmentCreate, EnrollmentUpdate, EnrollmentResponse,
    EnrollmentFilters
)

logger = logging.getLogger(__name__)


class EnrollmentService:
    """Service for managing RPM enrollments."""

    async def create_enrollment(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        enrolled_by: UUID,
        enrollment_data: EnrollmentCreate
    ) -> RPMEnrollment:
        """Create a new RPM enrollment."""
        # Check for existing active enrollment
        existing = await db.execute(
            select(RPMEnrollment).where(
                and_(
                    RPMEnrollment.tenant_id == tenant_id,
                    RPMEnrollment.patient_id == enrollment_data.patient_id,
                    RPMEnrollment.status.in_([
                        EnrollmentStatus.PENDING,
                        EnrollmentStatus.ENROLLED,
                        EnrollmentStatus.ACTIVE
                    ])
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Patient already has an active RPM enrollment")

        # Verify protocol if provided
        if enrollment_data.protocol_id:
            protocol_result = await db.execute(
                select(CareProtocol).where(
                    and_(
                        CareProtocol.id == enrollment_data.protocol_id,
                        CareProtocol.tenant_id == tenant_id
                    )
                )
            )
            if not protocol_result.scalar_one_or_none():
                raise ValueError("Protocol not found")

        enrollment = RPMEnrollment(
            tenant_id=tenant_id,
            patient_id=enrollment_data.patient_id,
            fhir_patient_id=enrollment_data.fhir_patient_id,
            protocol_id=enrollment_data.protocol_id,
            program_name=enrollment_data.program_name,
            primary_condition=enrollment_data.primary_condition,
            secondary_conditions=enrollment_data.secondary_conditions or [],
            primary_provider_id=enrollment_data.primary_provider_id,
            care_team_ids=enrollment_data.care_team_ids or [],
            status=EnrollmentStatus.PENDING,
            target_readings_per_day=enrollment_data.target_readings_per_day,
            goals=enrollment_data.goals or {},
            consent_obtained=enrollment_data.consent_obtained,
            consent_date=enrollment_data.consent_date,
            consent_document_id=enrollment_data.consent_document_id,
            enrolled_by=enrolled_by,
            notes=enrollment_data.notes
        )

        db.add(enrollment)
        await db.commit()
        await db.refresh(enrollment)

        logger.info(
            f"Created enrollment {enrollment.id} for patient "
            f"{enrollment_data.patient_id}"
        )
        return enrollment

    async def get_enrollment(
        self,
        db: AsyncSession,
        enrollment_id: UUID,
        tenant_id: UUID
    ) -> Optional[RPMEnrollment]:
        """Get enrollment by ID."""
        result = await db.execute(
            select(RPMEnrollment)
            .options(
                selectinload(RPMEnrollment.protocol),
                selectinload(RPMEnrollment.device_assignments).selectinload(
                    DeviceAssignment.device
                )
            )
            .where(
                and_(
                    RPMEnrollment.id == enrollment_id,
                    RPMEnrollment.tenant_id == tenant_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_patient_enrollment(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        patient_id: UUID,
        active_only: bool = True
    ) -> Optional[RPMEnrollment]:
        """Get patient's current enrollment."""
        query = select(RPMEnrollment).options(
            selectinload(RPMEnrollment.protocol),
            selectinload(RPMEnrollment.device_assignments).selectinload(
                DeviceAssignment.device
            )
        ).where(
            and_(
                RPMEnrollment.tenant_id == tenant_id,
                RPMEnrollment.patient_id == patient_id
            )
        )

        if active_only:
            query = query.where(
                RPMEnrollment.status.in_([
                    EnrollmentStatus.ENROLLED,
                    EnrollmentStatus.ACTIVE
                ])
            )

        query = query.order_by(RPMEnrollment.created_at.desc())
        result = await db.execute(query)
        return result.scalars().first()

    async def list_enrollments(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        filters: EnrollmentFilters,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[RPMEnrollment], int]:
        """List enrollments with filters."""
        query = select(RPMEnrollment).where(RPMEnrollment.tenant_id == tenant_id)

        if filters.patient_id:
            query = query.where(RPMEnrollment.patient_id == filters.patient_id)
        if filters.provider_id:
            query = query.where(RPMEnrollment.primary_provider_id == filters.provider_id)
        if filters.condition:
            query = query.where(RPMEnrollment.primary_condition == filters.condition)
        if filters.status:
            query = query.where(RPMEnrollment.status == filters.status)
        if filters.protocol_id:
            query = query.where(RPMEnrollment.protocol_id == filters.protocol_id)

        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()

        query = query.offset(skip).limit(limit).order_by(
            RPMEnrollment.created_at.desc()
        )
        result = await db.execute(query)
        enrollments = result.scalars().all()

        return list(enrollments), total

    async def update_enrollment(
        self,
        db: AsyncSession,
        enrollment_id: UUID,
        tenant_id: UUID,
        update_data: EnrollmentUpdate
    ) -> Optional[RPMEnrollment]:
        """Update enrollment."""
        enrollment = await self.get_enrollment(db, enrollment_id, tenant_id)
        if not enrollment:
            return None

        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(enrollment, field, value)

        enrollment.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(enrollment)
        return enrollment

    async def activate_enrollment(
        self,
        db: AsyncSession,
        enrollment_id: UUID,
        tenant_id: UUID
    ) -> Optional[RPMEnrollment]:
        """Activate an enrollment."""
        enrollment = await self.get_enrollment(db, enrollment_id, tenant_id)
        if not enrollment:
            return None

        if enrollment.status not in [EnrollmentStatus.PENDING, EnrollmentStatus.ENROLLED]:
            raise ValueError(f"Cannot activate enrollment in {enrollment.status.value} status")

        if not enrollment.consent_obtained:
            raise ValueError("Cannot activate enrollment without patient consent")

        enrollment.status = EnrollmentStatus.ACTIVE
        enrollment.activated_at = datetime.utcnow()
        enrollment.enrolled_at = enrollment.enrolled_at or datetime.utcnow()
        enrollment.updated_at = datetime.utcnow()

        # Create initial monitoring period
        await self._create_monitoring_period(db, enrollment)

        await db.commit()
        await db.refresh(enrollment)

        logger.info(f"Activated enrollment {enrollment_id}")
        return enrollment

    async def record_consent(
        self,
        db: AsyncSession,
        enrollment_id: UUID,
        tenant_id: UUID,
        consent_date: date,
        consent_document_id: Optional[UUID] = None
    ) -> Optional[RPMEnrollment]:
        """Record patient consent."""
        enrollment = await self.get_enrollment(db, enrollment_id, tenant_id)
        if not enrollment:
            return None

        enrollment.consent_obtained = True
        enrollment.consent_date = consent_date
        enrollment.consent_document_id = consent_document_id
        enrollment.status = EnrollmentStatus.ENROLLED
        enrollment.enrolled_at = datetime.utcnow()
        enrollment.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(enrollment)
        return enrollment

    async def discharge_enrollment(
        self,
        db: AsyncSession,
        enrollment_id: UUID,
        tenant_id: UUID,
        reason: str
    ) -> Optional[RPMEnrollment]:
        """Discharge patient from RPM program."""
        enrollment = await self.get_enrollment(db, enrollment_id, tenant_id)
        if not enrollment:
            return None

        enrollment.status = EnrollmentStatus.DISCHARGED
        enrollment.completed_at = datetime.utcnow()
        enrollment.discharge_reason = reason
        enrollment.updated_at = datetime.utcnow()

        # Deactivate device assignments
        for assignment in enrollment.device_assignments:
            if assignment.is_active:
                assignment.is_active = False
                assignment.unassigned_at = datetime.utcnow()

        await db.commit()
        await db.refresh(enrollment)

        logger.info(f"Discharged enrollment {enrollment_id}: {reason}")
        return enrollment

    async def _create_monitoring_period(
        self,
        db: AsyncSession,
        enrollment: RPMEnrollment
    ) -> MonitoringPeriod:
        """Create a monitoring period for the current month."""
        today = date.today()
        period_start = today.replace(day=1)

        # Calculate period end (last day of month)
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        period_end = next_month - timedelta(days=1)

        period = MonitoringPeriod(
            tenant_id=enrollment.tenant_id,
            enrollment_id=enrollment.id,
            patient_id=enrollment.patient_id,
            period_start=period_start,
            period_end=period_end,
            period_month=today.year * 100 + today.month,
            is_current=True
        )

        db.add(period)
        return period

    async def get_enrollment_statistics(
        self,
        db: AsyncSession,
        tenant_id: UUID
    ) -> Dict[str, Any]:
        """Get enrollment statistics."""
        # Total enrollments
        total_result = await db.execute(
            select(func.count()).select_from(RPMEnrollment).where(
                RPMEnrollment.tenant_id == tenant_id
            )
        )
        total = total_result.scalar()

        # By status
        status_result = await db.execute(
            select(
                RPMEnrollment.status,
                func.count(RPMEnrollment.id)
            ).where(
                RPMEnrollment.tenant_id == tenant_id
            ).group_by(RPMEnrollment.status)
        )
        by_status = {row[0].value: row[1] for row in status_result.all()}

        # By condition
        condition_result = await db.execute(
            select(
                RPMEnrollment.primary_condition,
                func.count(RPMEnrollment.id)
            ).where(
                and_(
                    RPMEnrollment.tenant_id == tenant_id,
                    RPMEnrollment.status == EnrollmentStatus.ACTIVE
                )
            ).group_by(RPMEnrollment.primary_condition)
        )
        by_condition = {row[0]: row[1] for row in condition_result.all()}

        # Active this month
        today = date.today()
        month_start = today.replace(day=1)

        active_result = await db.execute(
            select(func.count()).select_from(RPMEnrollment).where(
                and_(
                    RPMEnrollment.tenant_id == tenant_id,
                    RPMEnrollment.status == EnrollmentStatus.ACTIVE,
                    RPMEnrollment.activated_at >= month_start
                )
            )
        )
        new_this_month = active_result.scalar()

        return {
            "total_enrollments": total,
            "by_status": by_status,
            "by_condition": by_condition,
            "active_count": by_status.get("active", 0),
            "new_this_month": new_this_month
        }

    async def get_patients_needing_attention(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        days_threshold: int = 3
    ) -> List[RPMEnrollment]:
        """Get enrollments where patients haven't submitted readings recently."""
        threshold_date = datetime.utcnow() - timedelta(days=days_threshold)

        # Get active enrollments
        enrollments_result = await db.execute(
            select(RPMEnrollment).where(
                and_(
                    RPMEnrollment.tenant_id == tenant_id,
                    RPMEnrollment.status == EnrollmentStatus.ACTIVE
                )
            )
        )
        enrollments = enrollments_result.scalars().all()

        needing_attention = []
        for enrollment in enrollments:
            # Check for recent readings
            reading_result = await db.execute(
                select(DeviceReading).where(
                    and_(
                        DeviceReading.enrollment_id == enrollment.id,
                        DeviceReading.received_at > threshold_date
                    )
                ).limit(1)
            )
            if not reading_result.scalar_one_or_none():
                needing_attention.append(enrollment)

        return needing_attention


from datetime import timedelta
