"""
Provider Collaboration On-Call Service
EPIC-015: On-call schedule and request management
"""
from datetime import datetime, date, time, timezone, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from modules.provider_collaboration.models import (
    OnCallSchedule, OnCallRequest, ProviderPresence, CollaborationAuditLog,
    OnCallStatus, OnCallRequestStatus, RequestUrgency
)
from modules.provider_collaboration.schemas import (
    OnCallScheduleCreate, OnCallScheduleUpdate, OnCallRequestCreate,
    OnCallScheduleResponse, OnCallRequestResponse, OnCallScheduleListResponse,
    OnCallRequestListResponse
)


class OnCallService:
    """
    Handles on-call management including:
    - Schedule creation and updates
    - On-call request routing
    - Escalation management
    - Coverage tracking
    """

    def __init__(self):
        # Escalation timeout in minutes by urgency
        self.escalation_timeouts = {
            RequestUrgency.ROUTINE: 60,
            RequestUrgency.URGENT: 15,
            RequestUrgency.EMERGENT: 5,
            RequestUrgency.STAT: 2
        }

    async def create_schedule(
        self,
        db: AsyncSession,
        provider_id: UUID,
        tenant_id: UUID,
        data: OnCallScheduleCreate,
        ip_address: str = None
    ) -> OnCallScheduleResponse:
        """Create an on-call schedule entry"""

        # Check for overlapping schedules
        overlap_check = await db.execute(
            select(OnCallSchedule).where(
                and_(
                    OnCallSchedule.tenant_id == tenant_id,
                    OnCallSchedule.provider_id == data.provider_id,
                    OnCallSchedule.specialty == data.specialty,
                    OnCallSchedule.status != OnCallStatus.CANCELLED,
                    or_(
                        and_(
                            OnCallSchedule.start_time <= data.start_time,
                            OnCallSchedule.end_time > data.start_time
                        ),
                        and_(
                            OnCallSchedule.start_time < data.end_time,
                            OnCallSchedule.end_time >= data.end_time
                        ),
                        and_(
                            OnCallSchedule.start_time >= data.start_time,
                            OnCallSchedule.end_time <= data.end_time
                        )
                    )
                )
            )
        )
        existing = overlap_check.scalar_one_or_none()
        if existing:
            raise ValueError("Overlapping schedule exists for this provider and specialty")

        schedule = OnCallSchedule(
            id=uuid4(),
            tenant_id=tenant_id,
            provider_id=data.provider_id,
            specialty=data.specialty,
            service=data.service,
            facility_id=data.facility_id,
            start_time=data.start_time,
            end_time=data.end_time,
            is_primary=data.is_primary,
            backup_provider_id=data.backup_provider_id,
            status=OnCallStatus.SCHEDULED,
            contact_preferences=data.contact_preferences,
            notes=data.notes,
            created_by=provider_id
        )
        db.add(schedule)

        # Log action
        audit_log = CollaborationAuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            provider_id=provider_id,
            action="oncall_schedule_created",
            action_category="oncall",
            action_description=f"Created on-call schedule for {data.specialty}",
            entity_type="oncall_schedule",
            entity_id=schedule.id,
            details={
                "scheduled_provider": str(data.provider_id),
                "specialty": data.specialty,
                "start_time": data.start_time.isoformat(),
                "end_time": data.end_time.isoformat()
            },
            ip_address=ip_address
        )
        db.add(audit_log)

        await db.commit()
        await db.refresh(schedule)

        return self._schedule_to_response(schedule)

    async def update_schedule(
        self,
        db: AsyncSession,
        provider_id: UUID,
        tenant_id: UUID,
        schedule_id: UUID,
        data: OnCallScheduleUpdate
    ) -> OnCallScheduleResponse:
        """Update an on-call schedule"""

        result = await db.execute(
            select(OnCallSchedule).where(
                and_(
                    OnCallSchedule.id == schedule_id,
                    OnCallSchedule.tenant_id == tenant_id
                )
            )
        )
        schedule = result.scalar_one_or_none()

        if not schedule:
            raise ValueError("Schedule not found")

        if schedule.status == OnCallStatus.CANCELLED:
            raise ValueError("Cannot update cancelled schedule")

        if data.start_time is not None:
            schedule.start_time = data.start_time
        if data.end_time is not None:
            schedule.end_time = data.end_time
        if data.backup_provider_id is not None:
            schedule.backup_provider_id = data.backup_provider_id
        if data.contact_preferences is not None:
            schedule.contact_preferences = data.contact_preferences
        if data.notes is not None:
            schedule.notes = data.notes

        schedule.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(schedule)

        return self._schedule_to_response(schedule)

    async def cancel_schedule(
        self,
        db: AsyncSession,
        provider_id: UUID,
        tenant_id: UUID,
        schedule_id: UUID,
        reason: str = None
    ) -> OnCallScheduleResponse:
        """Cancel an on-call schedule"""

        result = await db.execute(
            select(OnCallSchedule).where(
                and_(
                    OnCallSchedule.id == schedule_id,
                    OnCallSchedule.tenant_id == tenant_id
                )
            )
        )
        schedule = result.scalar_one_or_none()

        if not schedule:
            raise ValueError("Schedule not found")

        schedule.status = OnCallStatus.CANCELLED
        schedule.notes = f"{schedule.notes or ''}\nCancelled: {reason}" if reason else schedule.notes
        schedule.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(schedule)

        return self._schedule_to_response(schedule)

    async def get_schedule(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        schedule_id: UUID
    ) -> OnCallScheduleResponse:
        """Get on-call schedule details"""

        result = await db.execute(
            select(OnCallSchedule).where(
                and_(
                    OnCallSchedule.id == schedule_id,
                    OnCallSchedule.tenant_id == tenant_id
                )
            )
        )
        schedule = result.scalar_one_or_none()

        if not schedule:
            raise ValueError("Schedule not found")

        return self._schedule_to_response(schedule)

    async def list_schedules(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        provider_id: Optional[UUID] = None,
        specialty: Optional[str] = None,
        facility_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[OnCallStatus] = None,
        page: int = 1,
        page_size: int = 20
    ) -> OnCallScheduleListResponse:
        """List on-call schedules with filters"""

        query = select(OnCallSchedule).where(
            OnCallSchedule.tenant_id == tenant_id
        )

        if provider_id:
            query = query.where(OnCallSchedule.provider_id == provider_id)

        if specialty:
            query = query.where(OnCallSchedule.specialty == specialty)

        if facility_id:
            query = query.where(OnCallSchedule.facility_id == facility_id)

        if start_date:
            query = query.where(OnCallSchedule.start_time >= datetime.combine(start_date, time.min))

        if end_date:
            query = query.where(OnCallSchedule.end_time <= datetime.combine(end_date, time.max))

        if status:
            query = query.where(OnCallSchedule.status == status)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Get paginated results
        query = query.order_by(OnCallSchedule.start_time)
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        schedules = result.scalars().all()

        return OnCallScheduleListResponse(
            schedules=[self._schedule_to_response(s) for s in schedules],
            total=total,
            page=page,
            page_size=page_size
        )

    async def get_current_oncall(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        specialty: str,
        facility_id: Optional[UUID] = None
    ) -> Optional[OnCallScheduleResponse]:
        """Get current on-call provider for a specialty"""

        now = datetime.now(timezone.utc)
        query = select(OnCallSchedule).where(
            and_(
                OnCallSchedule.tenant_id == tenant_id,
                OnCallSchedule.specialty == specialty,
                OnCallSchedule.status == OnCallStatus.ACTIVE,
                OnCallSchedule.start_time <= now,
                OnCallSchedule.end_time > now,
                OnCallSchedule.is_primary == True
            )
        )

        if facility_id:
            query = query.where(OnCallSchedule.facility_id == facility_id)

        result = await db.execute(query)
        schedule = result.scalar_one_or_none()

        if schedule:
            return self._schedule_to_response(schedule)

        return None

    async def activate_schedule(
        self,
        db: AsyncSession,
        provider_id: UUID,
        schedule_id: UUID
    ) -> OnCallScheduleResponse:
        """Activate an on-call schedule (start on-call shift)"""

        result = await db.execute(
            select(OnCallSchedule).where(OnCallSchedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()

        if not schedule:
            raise ValueError("Schedule not found")

        if schedule.provider_id != provider_id:
            raise ValueError("Only scheduled provider can activate")

        if schedule.status != OnCallStatus.SCHEDULED:
            raise ValueError("Schedule is not in scheduled status")

        schedule.status = OnCallStatus.ACTIVE
        schedule.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(schedule)

        return self._schedule_to_response(schedule)

    async def complete_schedule(
        self,
        db: AsyncSession,
        provider_id: UUID,
        schedule_id: UUID
    ) -> OnCallScheduleResponse:
        """Complete an on-call schedule (end on-call shift)"""

        result = await db.execute(
            select(OnCallSchedule).where(OnCallSchedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()

        if not schedule:
            raise ValueError("Schedule not found")

        if schedule.provider_id != provider_id:
            raise ValueError("Only scheduled provider can complete")

        if schedule.status != OnCallStatus.ACTIVE:
            raise ValueError("Schedule is not active")

        schedule.status = OnCallStatus.COMPLETED
        schedule.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(schedule)

        return self._schedule_to_response(schedule)

    # On-Call Request Management

    async def create_request(
        self,
        db: AsyncSession,
        requester_id: UUID,
        tenant_id: UUID,
        data: OnCallRequestCreate,
        ip_address: str = None
    ) -> OnCallRequestResponse:
        """Create an on-call request"""

        # Find current on-call provider
        oncall = await self.get_current_oncall(
            db, tenant_id, data.specialty, data.facility_id
        )

        if not oncall:
            raise ValueError(f"No on-call provider found for {data.specialty}")

        timeout = self.escalation_timeouts.get(
            RequestUrgency(data.urgency.value),
            30
        )
        escalation_time = datetime.now(timezone.utc) + timedelta(minutes=timeout)

        request = OnCallRequest(
            id=uuid4(),
            tenant_id=tenant_id,
            schedule_id=oncall.id,
            requester_id=requester_id,
            patient_id=data.patient_id,
            urgency=RequestUrgency(data.urgency.value),
            reason=data.reason,
            clinical_summary=data.clinical_summary,
            callback_number=data.callback_number,
            status=OnCallRequestStatus.PENDING,
            status_updated_at=datetime.now(timezone.utc),
            escalation_level=1,
            escalation_time=escalation_time
        )
        db.add(request)

        # Log action
        audit_log = CollaborationAuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            provider_id=requester_id,
            action="oncall_request_created",
            action_category="oncall",
            action_description=f"Created {data.urgency.value} on-call request for {data.specialty}",
            entity_type="oncall_request",
            entity_id=request.id,
            details={
                "specialty": data.specialty,
                "urgency": data.urgency.value,
                "patient_id": str(data.patient_id) if data.patient_id else None
            },
            ip_address=ip_address
        )
        db.add(audit_log)

        await db.commit()
        await db.refresh(request)

        return self._request_to_response(request)

    async def get_request(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        request_id: UUID
    ) -> OnCallRequestResponse:
        """Get on-call request details"""

        result = await db.execute(
            select(OnCallRequest)
            .options(selectinload(OnCallRequest.schedule))
            .where(
                and_(
                    OnCallRequest.id == request_id,
                    OnCallRequest.tenant_id == tenant_id
                )
            )
        )
        request = result.scalar_one_or_none()

        if not request:
            raise ValueError("Request not found")

        return self._request_to_response(request)

    async def list_requests(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        provider_id: Optional[UUID] = None,
        schedule_id: Optional[UUID] = None,
        status: Optional[OnCallRequestStatus] = None,
        urgency: Optional[RequestUrgency] = None,
        page: int = 1,
        page_size: int = 20
    ) -> OnCallRequestListResponse:
        """List on-call requests with filters"""

        query = select(OnCallRequest).where(
            OnCallRequest.tenant_id == tenant_id
        )

        if provider_id:
            # Filter by requests for schedules belonging to this provider
            subquery = select(OnCallSchedule.id).where(
                OnCallSchedule.provider_id == provider_id
            )
            query = query.where(OnCallRequest.schedule_id.in_(subquery))

        if schedule_id:
            query = query.where(OnCallRequest.schedule_id == schedule_id)

        if status:
            query = query.where(OnCallRequest.status == status)

        if urgency:
            query = query.where(OnCallRequest.urgency == urgency)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Get paginated results
        query = query.order_by(desc(OnCallRequest.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        requests = result.scalars().all()

        return OnCallRequestListResponse(
            requests=[self._request_to_response(r) for r in requests],
            total=total,
            page=page,
            page_size=page_size
        )

    async def acknowledge_request(
        self,
        db: AsyncSession,
        provider_id: UUID,
        request_id: UUID
    ) -> OnCallRequestResponse:
        """Acknowledge an on-call request"""

        result = await db.execute(
            select(OnCallRequest)
            .options(selectinload(OnCallRequest.schedule))
            .where(OnCallRequest.id == request_id)
        )
        request = result.scalar_one_or_none()

        if not request:
            raise ValueError("Request not found")

        if request.schedule.provider_id != provider_id:
            raise ValueError("Only on-call provider can acknowledge")

        if request.status != OnCallRequestStatus.PENDING:
            raise ValueError("Request is not pending")

        request.status = OnCallRequestStatus.ACKNOWLEDGED
        request.status_updated_at = datetime.now(timezone.utc)
        request.acknowledged_at = datetime.now(timezone.utc)
        request.response_time_minutes = int(
            (request.acknowledged_at - request.created_at).total_seconds() / 60
        )

        await db.commit()
        await db.refresh(request)

        return self._request_to_response(request)

    async def respond_to_request(
        self,
        db: AsyncSession,
        provider_id: UUID,
        request_id: UUID,
        response: str,
        accept: bool = True
    ) -> OnCallRequestResponse:
        """Respond to an on-call request (accept or decline)"""

        result = await db.execute(
            select(OnCallRequest)
            .options(selectinload(OnCallRequest.schedule))
            .where(OnCallRequest.id == request_id)
        )
        request = result.scalar_one_or_none()

        if not request:
            raise ValueError("Request not found")

        if request.schedule.provider_id != provider_id:
            raise ValueError("Only on-call provider can respond")

        if request.status not in [OnCallRequestStatus.PENDING, OnCallRequestStatus.ACKNOWLEDGED]:
            raise ValueError("Request is not in respondable status")

        now = datetime.now(timezone.utc)

        if accept:
            request.status = OnCallRequestStatus.IN_PROGRESS
            request.responded_at = now
        else:
            request.status = OnCallRequestStatus.ESCALATED
            request.escalation_level += 1
            request.escalation_time = now + timedelta(
                minutes=self.escalation_timeouts.get(request.urgency, 30)
            )

        request.status_updated_at = now
        request.response_notes = response

        if not request.acknowledged_at:
            request.acknowledged_at = now
            request.response_time_minutes = int((now - request.created_at).total_seconds() / 60)

        await db.commit()
        await db.refresh(request)

        return self._request_to_response(request)

    async def complete_request(
        self,
        db: AsyncSession,
        provider_id: UUID,
        request_id: UUID,
        resolution: str
    ) -> OnCallRequestResponse:
        """Complete an on-call request"""

        result = await db.execute(
            select(OnCallRequest)
            .options(selectinload(OnCallRequest.schedule))
            .where(OnCallRequest.id == request_id)
        )
        request = result.scalar_one_or_none()

        if not request:
            raise ValueError("Request not found")

        if request.schedule.provider_id != provider_id:
            raise ValueError("Only on-call provider can complete")

        if request.status != OnCallRequestStatus.IN_PROGRESS:
            raise ValueError("Request is not in progress")

        request.status = OnCallRequestStatus.COMPLETED
        request.status_updated_at = datetime.now(timezone.utc)
        request.completed_at = datetime.now(timezone.utc)
        request.resolution = resolution

        await db.commit()
        await db.refresh(request)

        return self._request_to_response(request)

    async def escalate_request(
        self,
        db: AsyncSession,
        request_id: UUID
    ) -> OnCallRequestResponse:
        """Escalate an on-call request to backup provider"""

        result = await db.execute(
            select(OnCallRequest)
            .options(selectinload(OnCallRequest.schedule))
            .where(OnCallRequest.id == request_id)
        )
        request = result.scalar_one_or_none()

        if not request:
            raise ValueError("Request not found")

        if request.status == OnCallRequestStatus.COMPLETED:
            raise ValueError("Cannot escalate completed request")

        schedule = request.schedule
        now = datetime.now(timezone.utc)

        # Check if backup provider is available
        if schedule.backup_provider_id:
            # Find backup provider's schedule
            backup_schedule = await db.execute(
                select(OnCallSchedule).where(
                    and_(
                        OnCallSchedule.provider_id == schedule.backup_provider_id,
                        OnCallSchedule.specialty == schedule.specialty,
                        OnCallSchedule.status == OnCallStatus.ACTIVE,
                        OnCallSchedule.start_time <= now,
                        OnCallSchedule.end_time > now
                    )
                )
            )
            backup = backup_schedule.scalar_one_or_none()

            if backup:
                request.schedule_id = backup.id
                request.escalation_level += 1
                request.status = OnCallRequestStatus.PENDING
                request.status_updated_at = now
                request.escalation_time = now + timedelta(
                    minutes=self.escalation_timeouts.get(request.urgency, 30) // 2
                )

                await db.commit()
                await db.refresh(request)

                return self._request_to_response(request)

        # No backup available, mark as escalated
        request.status = OnCallRequestStatus.ESCALATED
        request.escalation_level += 1
        request.status_updated_at = now

        await db.commit()
        await db.refresh(request)

        return self._request_to_response(request)

    async def get_pending_requests_for_provider(
        self,
        db: AsyncSession,
        provider_id: UUID,
        tenant_id: UUID
    ) -> List[OnCallRequestResponse]:
        """Get all pending requests for a provider's on-call schedules"""

        # Get provider's active schedules
        schedule_result = await db.execute(
            select(OnCallSchedule.id).where(
                and_(
                    OnCallSchedule.provider_id == provider_id,
                    OnCallSchedule.tenant_id == tenant_id,
                    OnCallSchedule.status == OnCallStatus.ACTIVE
                )
            )
        )
        schedule_ids = [row[0] for row in schedule_result.fetchall()]

        if not schedule_ids:
            return []

        # Get pending requests
        result = await db.execute(
            select(OnCallRequest).where(
                and_(
                    OnCallRequest.schedule_id.in_(schedule_ids),
                    OnCallRequest.status.in_([
                        OnCallRequestStatus.PENDING,
                        OnCallRequestStatus.ACKNOWLEDGED
                    ])
                )
            ).order_by(
                # Order by urgency (STAT first) then by created_at
                OnCallRequest.urgency,
                OnCallRequest.created_at
            )
        )
        requests = result.scalars().all()

        return [self._request_to_response(r) for r in requests]

    def _schedule_to_response(self, schedule: OnCallSchedule) -> OnCallScheduleResponse:
        """Convert schedule model to response schema"""
        return OnCallScheduleResponse(
            id=schedule.id,
            provider_id=schedule.provider_id,
            specialty=schedule.specialty,
            service=schedule.service,
            facility_id=schedule.facility_id,
            start_time=schedule.start_time,
            end_time=schedule.end_time,
            is_primary=schedule.is_primary,
            backup_provider_id=schedule.backup_provider_id,
            status=schedule.status.value,
            contact_preferences=schedule.contact_preferences or {},
            notes=schedule.notes,
            created_at=schedule.created_at
        )

    def _request_to_response(self, request: OnCallRequest) -> OnCallRequestResponse:
        """Convert request model to response schema"""
        return OnCallRequestResponse(
            id=request.id,
            schedule_id=request.schedule_id,
            requester_id=request.requester_id,
            patient_id=request.patient_id,
            urgency=request.urgency.value,
            reason=request.reason,
            clinical_summary=request.clinical_summary,
            callback_number=request.callback_number,
            status=request.status.value,
            acknowledged_at=request.acknowledged_at,
            responded_at=request.responded_at,
            completed_at=request.completed_at,
            response_time_minutes=request.response_time_minutes,
            resolution=request.resolution,
            escalation_level=request.escalation_level,
            created_at=request.created_at
        )
