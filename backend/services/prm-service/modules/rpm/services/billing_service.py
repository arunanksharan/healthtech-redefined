"""
Billing Service for RPM

Handles RPM billing code generation and tracking.

EPIC-019: Remote Patient Monitoring
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from decimal import Decimal
import logging

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    RPMEnrollment, MonitoringPeriod, ClinicalTimeEntry, RPMBillingEvent,
    DeviceReading, BillingCodeType, EnrollmentStatus
)
from ..schemas import (
    MonitoringPeriodResponse, ClinicalTimeEntryCreate, ClinicalTimeEntryResponse,
    BillingEventCreate, BillingEventResponse, BillingSummary
)

logger = logging.getLogger(__name__)

# CMS RPM billing requirements
RPM_BILLING_REQUIREMENTS = {
    BillingCodeType.CPT_99453: {
        "description": "Remote monitoring device setup",
        "requirements": "Initial device setup and patient education",
        "frequency": "once_per_enrollment"
    },
    BillingCodeType.CPT_99454: {
        "description": "Remote monitoring device supply",
        "requirements": "16+ days of data in calendar month",
        "frequency": "monthly",
        "min_days": 16
    },
    BillingCodeType.CPT_99457: {
        "description": "Remote monitoring treatment management",
        "requirements": "20+ minutes clinical time per month",
        "frequency": "monthly",
        "min_minutes": 20
    },
    BillingCodeType.CPT_99458: {
        "description": "Additional treatment management time",
        "requirements": "Each additional 20 minutes (after 99457)",
        "frequency": "monthly",
        "min_minutes": 20
    }
}


class BillingService:
    """Service for managing RPM billing."""

    async def get_monitoring_period(
        self,
        db: AsyncSession,
        period_id: UUID,
        tenant_id: UUID
    ) -> Optional[MonitoringPeriod]:
        """Get monitoring period by ID."""
        result = await db.execute(
            select(MonitoringPeriod).where(
                and_(
                    MonitoringPeriod.id == period_id,
                    MonitoringPeriod.tenant_id == tenant_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_current_period(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        enrollment_id: UUID
    ) -> Optional[MonitoringPeriod]:
        """Get current monitoring period for enrollment."""
        result = await db.execute(
            select(MonitoringPeriod).where(
                and_(
                    MonitoringPeriod.tenant_id == tenant_id,
                    MonitoringPeriod.enrollment_id == enrollment_id,
                    MonitoringPeriod.is_current == True
                )
            )
        )
        return result.scalar_one_or_none()

    async def ensure_monitoring_period(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        enrollment_id: UUID,
        patient_id: UUID
    ) -> MonitoringPeriod:
        """Ensure monitoring period exists for current month."""
        today = date.today()
        period_month = today.year * 100 + today.month

        # Check if exists
        result = await db.execute(
            select(MonitoringPeriod).where(
                and_(
                    MonitoringPeriod.enrollment_id == enrollment_id,
                    MonitoringPeriod.period_month == period_month
                )
            )
        )
        period = result.scalar_one_or_none()

        if period:
            return period

        # Mark previous periods as not current
        await db.execute(
            select(MonitoringPeriod).where(
                and_(
                    MonitoringPeriod.enrollment_id == enrollment_id,
                    MonitoringPeriod.is_current == True
                )
            )
        )
        # Note: In production, update these to is_current=False

        # Create new period
        period_start = today.replace(day=1)
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        period_end = next_month - timedelta(days=1)

        period = MonitoringPeriod(
            tenant_id=tenant_id,
            enrollment_id=enrollment_id,
            patient_id=patient_id,
            period_start=period_start,
            period_end=period_end,
            period_month=period_month,
            is_current=True
        )

        db.add(period)
        await db.commit()
        await db.refresh(period)
        return period

    async def update_period_metrics(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        enrollment_id: UUID
    ) -> Optional[MonitoringPeriod]:
        """Update monitoring period metrics based on readings and time entries."""
        period = await self.get_current_period(db, tenant_id, enrollment_id)
        if not period:
            return None

        # Count days with readings
        days_result = await db.execute(
            select(func.count(func.distinct(
                func.date(DeviceReading.measured_at)
            ))).where(
                and_(
                    DeviceReading.enrollment_id == enrollment_id,
                    DeviceReading.measured_at.between(
                        datetime.combine(period.period_start, datetime.min.time()),
                        datetime.combine(period.period_end, datetime.max.time())
                    ),
                    DeviceReading.is_valid == True
                )
            )
        )
        period.days_with_readings = days_result.scalar() or 0

        # Count total readings
        readings_result = await db.execute(
            select(func.count()).select_from(DeviceReading).where(
                and_(
                    DeviceReading.enrollment_id == enrollment_id,
                    DeviceReading.measured_at.between(
                        datetime.combine(period.period_start, datetime.min.time()),
                        datetime.combine(period.period_end, datetime.max.time())
                    ),
                    DeviceReading.is_valid == True
                )
            )
        )
        period.total_readings = readings_result.scalar() or 0

        # Sum clinical time
        time_result = await db.execute(
            select(
                func.sum(ClinicalTimeEntry.duration_minutes).label("total"),
                func.sum(
                    ClinicalTimeEntry.duration_minutes
                ).filter(ClinicalTimeEntry.is_interactive == True).label("interactive")
            ).where(
                ClinicalTimeEntry.monitoring_period_id == period.id
            )
        )
        row = time_result.one()
        period.clinical_time_minutes = row.total or 0
        period.interactive_time_minutes = row.interactive or 0

        # Determine qualification
        period.qualifies_for_99454 = period.days_with_readings >= 16
        period.qualifies_for_99457 = period.clinical_time_minutes >= 20
        period.qualifies_for_99458 = period.clinical_time_minutes >= 40

        period.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(period)
        return period

    async def log_clinical_time(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        provider_id: UUID,
        entry_data: ClinicalTimeEntryCreate
    ) -> ClinicalTimeEntry:
        """Log clinical time for billing."""
        # Calculate duration
        duration = int((entry_data.end_time - entry_data.start_time).total_seconds() / 60)

        entry = ClinicalTimeEntry(
            tenant_id=tenant_id,
            monitoring_period_id=entry_data.monitoring_period_id,
            enrollment_id=entry_data.enrollment_id,
            provider_id=provider_id,
            start_time=entry_data.start_time,
            end_time=entry_data.end_time,
            duration_minutes=duration,
            activity_type=entry_data.activity_type,
            is_interactive=entry_data.is_interactive,
            description=entry_data.description,
            alert_id=entry_data.alert_id,
            reading_ids=entry_data.reading_ids or []
        )

        db.add(entry)
        await db.commit()
        await db.refresh(entry)

        # Update period metrics
        await self.update_period_metrics(db, tenant_id, entry_data.enrollment_id)

        logger.info(
            f"Logged {duration} minutes clinical time for enrollment "
            f"{entry_data.enrollment_id}"
        )
        return entry

    async def get_time_entries(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        enrollment_id: Optional[UUID] = None,
        period_id: Optional[UUID] = None,
        provider_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ClinicalTimeEntry]:
        """Get clinical time entries."""
        query = select(ClinicalTimeEntry).where(
            ClinicalTimeEntry.tenant_id == tenant_id
        )

        if enrollment_id:
            query = query.where(ClinicalTimeEntry.enrollment_id == enrollment_id)
        if period_id:
            query = query.where(ClinicalTimeEntry.monitoring_period_id == period_id)
        if provider_id:
            query = query.where(ClinicalTimeEntry.provider_id == provider_id)
        if start_date:
            query = query.where(ClinicalTimeEntry.start_time >= start_date)
        if end_date:
            query = query.where(ClinicalTimeEntry.end_time <= end_date)

        query = query.order_by(ClinicalTimeEntry.start_time.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def generate_billing_events(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        period_month: int
    ) -> List[RPMBillingEvent]:
        """Generate billing events for a period."""
        # Get all periods for the month
        periods_result = await db.execute(
            select(MonitoringPeriod).where(
                and_(
                    MonitoringPeriod.tenant_id == tenant_id,
                    MonitoringPeriod.period_month == period_month,
                    MonitoringPeriod.billing_generated == False
                )
            )
        )
        periods = periods_result.scalars().all()

        events = []
        for period in periods:
            period_events = await self._generate_period_billing(db, period)
            events.extend(period_events)

        return events

    async def _generate_period_billing(
        self,
        db: AsyncSession,
        period: MonitoringPeriod
    ) -> List[RPMBillingEvent]:
        """Generate billing events for a single period."""
        events = []
        enrollment_result = await db.execute(
            select(RPMEnrollment).where(RPMEnrollment.id == period.enrollment_id)
        )
        enrollment = enrollment_result.scalar_one_or_none()

        if not enrollment:
            return events

        service_date = period.period_end

        # 99454 - Device supply with monitoring (16+ days)
        if period.qualifies_for_99454:
            event = RPMBillingEvent(
                tenant_id=period.tenant_id,
                enrollment_id=period.enrollment_id,
                monitoring_period_id=period.id,
                patient_id=period.patient_id,
                cpt_code=BillingCodeType.CPT_99454,
                service_date=service_date,
                billing_provider_id=enrollment.primary_provider_id,
                status="pending",
                days_with_data=period.days_with_readings,
                documentation={
                    "days_with_readings": period.days_with_readings,
                    "total_readings": period.total_readings,
                    "period_start": period.period_start.isoformat(),
                    "period_end": period.period_end.isoformat()
                }
            )
            db.add(event)
            events.append(event)
            period.billing_codes.append(BillingCodeType.CPT_99454.value)

        # 99457 - First 20 minutes
        if period.qualifies_for_99457:
            event = RPMBillingEvent(
                tenant_id=period.tenant_id,
                enrollment_id=period.enrollment_id,
                monitoring_period_id=period.id,
                patient_id=period.patient_id,
                cpt_code=BillingCodeType.CPT_99457,
                service_date=service_date,
                billing_provider_id=enrollment.primary_provider_id,
                status="pending",
                clinical_minutes=min(period.clinical_time_minutes, 20),
                documentation={
                    "clinical_time_minutes": period.clinical_time_minutes,
                    "interactive_time_minutes": period.interactive_time_minutes
                }
            )
            db.add(event)
            events.append(event)
            period.billing_codes.append(BillingCodeType.CPT_99457.value)

        # 99458 - Additional 20 minutes (can bill multiple)
        if period.qualifies_for_99458:
            additional_units = (period.clinical_time_minutes - 20) // 20
            for i in range(additional_units):
                event = RPMBillingEvent(
                    tenant_id=period.tenant_id,
                    enrollment_id=period.enrollment_id,
                    monitoring_period_id=period.id,
                    patient_id=period.patient_id,
                    cpt_code=BillingCodeType.CPT_99458,
                    service_date=service_date,
                    billing_provider_id=enrollment.primary_provider_id,
                    status="pending",
                    clinical_minutes=20,
                    documentation={
                        "unit_number": i + 1,
                        "total_clinical_minutes": period.clinical_time_minutes
                    }
                )
                db.add(event)
                events.append(event)

            if additional_units > 0:
                period.billing_codes.append(BillingCodeType.CPT_99458.value)

        # Check for device setup (99453) - once per enrollment
        if not period.device_setup_done:
            setup_check = await db.execute(
                select(RPMBillingEvent).where(
                    and_(
                        RPMBillingEvent.enrollment_id == period.enrollment_id,
                        RPMBillingEvent.cpt_code == BillingCodeType.CPT_99453
                    )
                ).limit(1)
            )
            if not setup_check.scalar_one_or_none():
                # Check if device was setup this period
                first_reading = await db.execute(
                    select(DeviceReading).where(
                        DeviceReading.enrollment_id == period.enrollment_id
                    ).order_by(DeviceReading.measured_at.asc()).limit(1)
                )
                reading = first_reading.scalar_one_or_none()

                if reading and period.period_start <= reading.measured_at.date() <= period.period_end:
                    event = RPMBillingEvent(
                        tenant_id=period.tenant_id,
                        enrollment_id=period.enrollment_id,
                        monitoring_period_id=period.id,
                        patient_id=period.patient_id,
                        cpt_code=BillingCodeType.CPT_99453,
                        service_date=reading.measured_at.date(),
                        billing_provider_id=enrollment.primary_provider_id,
                        status="pending",
                        documentation={
                            "setup_date": reading.measured_at.date().isoformat(),
                            "first_reading_id": str(reading.id)
                        }
                    )
                    db.add(event)
                    events.append(event)
                    period.device_setup_done = True
                    period.device_setup_date = reading.measured_at.date()
                    period.billing_codes.append(BillingCodeType.CPT_99453.value)

        period.billing_generated = True
        period.billing_generated_at = datetime.utcnow()
        await db.commit()

        logger.info(
            f"Generated {len(events)} billing events for period {period.id}"
        )
        return events

    async def get_billing_events(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        enrollment_id: Optional[UUID] = None,
        patient_id: Optional[UUID] = None,
        cpt_code: Optional[BillingCodeType] = None,
        status: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[RPMBillingEvent], int]:
        """Get billing events."""
        query = select(RPMBillingEvent).where(
            RPMBillingEvent.tenant_id == tenant_id
        )

        if enrollment_id:
            query = query.where(RPMBillingEvent.enrollment_id == enrollment_id)
        if patient_id:
            query = query.where(RPMBillingEvent.patient_id == patient_id)
        if cpt_code:
            query = query.where(RPMBillingEvent.cpt_code == cpt_code)
        if status:
            query = query.where(RPMBillingEvent.status == status)
        if start_date:
            query = query.where(RPMBillingEvent.service_date >= start_date)
        if end_date:
            query = query.where(RPMBillingEvent.service_date <= end_date)

        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()

        query = query.offset(skip).limit(limit).order_by(
            RPMBillingEvent.service_date.desc()
        )
        result = await db.execute(query)
        events = result.scalars().all()

        return list(events), total

    async def update_billing_event_status(
        self,
        db: AsyncSession,
        event_id: UUID,
        tenant_id: UUID,
        status: str,
        claim_id: Optional[UUID] = None,
        external_claim_id: Optional[str] = None,
        paid_amount: Optional[Decimal] = None
    ) -> Optional[RPMBillingEvent]:
        """Update billing event status."""
        result = await db.execute(
            select(RPMBillingEvent).where(
                and_(
                    RPMBillingEvent.id == event_id,
                    RPMBillingEvent.tenant_id == tenant_id
                )
            )
        )
        event = result.scalar_one_or_none()

        if not event:
            return None

        event.status = status
        if claim_id:
            event.claim_id = claim_id
        if external_claim_id:
            event.external_claim_id = external_claim_id
        if paid_amount is not None:
            event.paid_amount = paid_amount
            event.adjudicated_at = datetime.utcnow()

        if status == "submitted":
            event.submitted_at = datetime.utcnow()

        event.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(event)
        return event

    async def get_billing_summary(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        period_month: int
    ) -> BillingSummary:
        """Get billing summary for a period."""
        # Get periods for month
        periods_result = await db.execute(
            select(MonitoringPeriod).where(
                and_(
                    MonitoringPeriod.tenant_id == tenant_id,
                    MonitoringPeriod.period_month == period_month
                )
            )
        )
        periods = periods_result.scalars().all()

        total_enrolled = len(periods)
        eligible_99453 = sum(1 for p in periods if p.device_setup_done)
        eligible_99454 = sum(1 for p in periods if p.qualifies_for_99454)
        eligible_99457 = sum(1 for p in periods if p.qualifies_for_99457)
        eligible_99458 = sum(1 for p in periods if p.qualifies_for_99458)

        # Get billing event totals
        events_result = await db.execute(
            select(
                RPMBillingEvent.status,
                func.count(RPMBillingEvent.id).label("count"),
                func.coalesce(func.sum(RPMBillingEvent.billed_amount), 0).label("billed"),
                func.coalesce(func.sum(RPMBillingEvent.paid_amount), 0).label("paid")
            ).where(
                and_(
                    RPMBillingEvent.tenant_id == tenant_id,
                    RPMBillingEvent.monitoring_period_id.in_([p.id for p in periods])
                )
            ).group_by(RPMBillingEvent.status)
        )

        total_submitted = 0
        total_paid = 0
        total_denied = 0
        revenue_collected = Decimal(0)
        revenue_pending = Decimal(0)

        for row in events_result.all():
            if row.status == "submitted":
                total_submitted += row.count
                revenue_pending += row.billed
            elif row.status == "paid":
                total_paid += row.count
                revenue_collected += row.paid
            elif row.status == "denied":
                total_denied += row.count

        return BillingSummary(
            period_month=period_month,
            total_patients_enrolled=total_enrolled,
            patients_eligible_99453=eligible_99453,
            patients_eligible_99454=eligible_99454,
            patients_eligible_99457=eligible_99457,
            patients_eligible_99458=eligible_99458,
            total_billable_amount=revenue_pending + revenue_collected,
            total_submitted=total_submitted,
            total_paid=total_paid,
            total_denied=total_denied,
            revenue_collected=revenue_collected,
            revenue_pending=revenue_pending
        )
