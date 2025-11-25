"""
Provider Collaboration Handoff Service
EPIC-015: Shift handoff management with SBAR format
"""
from datetime import datetime, date, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from modules.provider_collaboration.models import (
    ShiftHandoff, PatientHandoff, ProviderConversation, ConversationParticipant,
    CollaborationAuditLog, HandoffStatus, HandoffType, ConversationType
)
from modules.provider_collaboration.schemas import (
    HandoffCreate, PatientHandoffUpdate, HandoffAcknowledge, HandoffQuestion,
    HandoffResponse, PatientHandoffResponse, HandoffListResponse
)


class HandoffService:
    """
    Handles shift handoffs including:
    - Handoff session management
    - SBAR format patient handoffs
    - Handoff verification and acknowledgment
    - Quality tracking
    """

    def __init__(self):
        pass

    async def create_handoff(
        self,
        db: AsyncSession,
        provider_id: UUID,
        tenant_id: UUID,
        data: HandoffCreate,
        ip_address: str = None
    ) -> HandoffResponse:
        """Create a shift handoff session"""

        handoff = ShiftHandoff(
            id=uuid4(),
            tenant_id=tenant_id,
            outgoing_provider_id=provider_id,
            incoming_provider_id=data.incoming_provider_id,
            handoff_type=HandoffType(data.handoff_type.value),
            service=data.service,
            unit=data.unit,
            shift_date=data.shift_date,
            scheduled_time=data.scheduled_time,
            status=HandoffStatus.SCHEDULED,
            status_updated_at=datetime.now(timezone.utc),
            patient_ids=data.patient_ids,
            patient_count=len(data.patient_ids)
        )
        db.add(handoff)

        # Create handoff conversation
        conversation = ProviderConversation(
            id=uuid4(),
            tenant_id=tenant_id,
            type=ConversationType.HANDOFF,
            name=f"Handoff - {data.shift_date}",
            handoff_id=handoff.id,
            created_by=provider_id,
            is_encrypted=True
        )
        db.add(conversation)

        handoff.conversation_id = conversation.id

        # Add participants
        outgoing_participant = ConversationParticipant(
            id=uuid4(),
            conversation_id=conversation.id,
            provider_id=provider_id,
            role="outgoing"
        )
        db.add(outgoing_participant)

        incoming_participant = ConversationParticipant(
            id=uuid4(),
            conversation_id=conversation.id,
            provider_id=data.incoming_provider_id,
            role="incoming"
        )
        db.add(incoming_participant)

        # Generate patient handoff entries
        for patient_id in data.patient_ids:
            patient_handoff = PatientHandoff(
                id=uuid4(),
                shift_handoff_id=handoff.id,
                patient_id=patient_id
            )
            db.add(patient_handoff)

        # Log action
        audit_log = CollaborationAuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            provider_id=provider_id,
            action="handoff_created",
            action_category="handoff",
            action_description=f"Created handoff for {len(data.patient_ids)} patients",
            entity_type="handoff",
            entity_id=handoff.id,
            details={
                "patient_count": len(data.patient_ids),
                "handoff_type": data.handoff_type.value
            },
            ip_address=ip_address
        )
        db.add(audit_log)

        await db.commit()

        return await self.get_handoff(db, provider_id, tenant_id, handoff.id)

    async def get_handoff(
        self,
        db: AsyncSession,
        provider_id: UUID,
        tenant_id: UUID,
        handoff_id: UUID
    ) -> HandoffResponse:
        """Get handoff details"""

        result = await db.execute(
            select(ShiftHandoff)
            .options(selectinload(ShiftHandoff.patient_handoffs))
            .where(
                and_(
                    ShiftHandoff.id == handoff_id,
                    ShiftHandoff.tenant_id == tenant_id
                )
            )
        )
        handoff = result.scalar_one_or_none()

        if not handoff:
            raise ValueError("Handoff not found")

        # Check access
        if provider_id not in [handoff.outgoing_provider_id, handoff.incoming_provider_id]:
            raise ValueError("Not authorized to view this handoff")

        patient_handoffs = [
            PatientHandoffResponse(
                id=ph.id,
                patient_id=ph.patient_id,
                situation=ph.situation,
                background=ph.background,
                assessment=ph.assessment,
                recommendations=ph.recommendations,
                critical_items=ph.critical_items or [],
                has_critical_items=ph.has_critical_items,
                pending_tasks=ph.pending_tasks or [],
                reviewed=ph.reviewed,
                questions_raised=ph.questions_raised or [],
                questions_resolved=ph.questions_resolved
            )
            for ph in handoff.patient_handoffs
        ]

        return HandoffResponse(
            id=handoff.id,
            outgoing_provider_id=handoff.outgoing_provider_id,
            incoming_provider_id=handoff.incoming_provider_id,
            handoff_type=handoff.handoff_type.value,
            service=handoff.service,
            unit=handoff.unit,
            shift_date=handoff.shift_date,
            scheduled_time=handoff.scheduled_time,
            started_at=handoff.started_at,
            completed_at=handoff.completed_at,
            duration_minutes=handoff.duration_minutes,
            status=handoff.status.value,
            patient_count=handoff.patient_count,
            patient_handoffs=patient_handoffs,
            conversation_id=handoff.conversation_id,
            acknowledged=handoff.acknowledged,
            quality_score=float(handoff.quality_score) if handoff.quality_score else None,
            created_at=handoff.created_at
        )

    async def list_handoffs(
        self,
        db: AsyncSession,
        provider_id: UUID,
        tenant_id: UUID,
        role: str = "all",  # "outgoing", "incoming", "all"
        shift_date: Optional[date] = None,
        status: Optional[HandoffStatus] = None,
        page: int = 1,
        page_size: int = 20
    ) -> HandoffListResponse:
        """List handoffs for a provider"""

        query = select(ShiftHandoff).where(
            ShiftHandoff.tenant_id == tenant_id
        )

        if role == "outgoing":
            query = query.where(ShiftHandoff.outgoing_provider_id == provider_id)
        elif role == "incoming":
            query = query.where(ShiftHandoff.incoming_provider_id == provider_id)
        else:
            query = query.where(
                or_(
                    ShiftHandoff.outgoing_provider_id == provider_id,
                    ShiftHandoff.incoming_provider_id == provider_id
                )
            )

        if shift_date:
            query = query.where(ShiftHandoff.shift_date == shift_date)

        if status:
            query = query.where(ShiftHandoff.status == status)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Get paginated results
        query = query.order_by(desc(ShiftHandoff.shift_date), desc(ShiftHandoff.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        handoffs = result.scalars().all()

        return HandoffListResponse(
            handoffs=[
                HandoffResponse(
                    id=h.id,
                    outgoing_provider_id=h.outgoing_provider_id,
                    incoming_provider_id=h.incoming_provider_id,
                    handoff_type=h.handoff_type.value,
                    service=h.service,
                    unit=h.unit,
                    shift_date=h.shift_date,
                    scheduled_time=h.scheduled_time,
                    started_at=h.started_at,
                    completed_at=h.completed_at,
                    duration_minutes=h.duration_minutes,
                    status=h.status.value,
                    patient_count=h.patient_count,
                    patient_handoffs=[],
                    conversation_id=h.conversation_id,
                    acknowledged=h.acknowledged,
                    quality_score=float(h.quality_score) if h.quality_score else None,
                    created_at=h.created_at
                )
                for h in handoffs
            ],
            total=total,
            page=page,
            page_size=page_size
        )

    async def start_handoff(
        self,
        db: AsyncSession,
        provider_id: UUID,
        handoff_id: UUID
    ) -> HandoffResponse:
        """Start a handoff session"""

        result = await db.execute(
            select(ShiftHandoff).where(ShiftHandoff.id == handoff_id)
        )
        handoff = result.scalar_one_or_none()

        if not handoff:
            raise ValueError("Handoff not found")

        if handoff.outgoing_provider_id != provider_id:
            raise ValueError("Only outgoing provider can start handoff")

        if handoff.status != HandoffStatus.SCHEDULED:
            raise ValueError("Handoff is not in scheduled status")

        handoff.status = HandoffStatus.IN_PROGRESS
        handoff.status_updated_at = datetime.now(timezone.utc)
        handoff.started_at = datetime.now(timezone.utc)

        await db.commit()

        return await self.get_handoff(db, provider_id, handoff.tenant_id, handoff_id)

    async def update_patient_handoff(
        self,
        db: AsyncSession,
        provider_id: UUID,
        patient_handoff_id: UUID,
        data: PatientHandoffUpdate
    ) -> PatientHandoffResponse:
        """Update patient handoff SBAR data"""

        result = await db.execute(
            select(PatientHandoff)
            .options(selectinload(PatientHandoff.shift_handoff))
            .where(PatientHandoff.id == patient_handoff_id)
        )
        patient_handoff = result.scalar_one_or_none()

        if not patient_handoff:
            raise ValueError("Patient handoff not found")

        if patient_handoff.shift_handoff.outgoing_provider_id != provider_id:
            raise ValueError("Only outgoing provider can update patient handoff")

        if data.situation is not None:
            patient_handoff.situation = data.situation
        if data.background is not None:
            patient_handoff.background = data.background
        if data.assessment is not None:
            patient_handoff.assessment = data.assessment
        if data.recommendations is not None:
            patient_handoff.recommendations = data.recommendations
        if data.critical_items is not None:
            patient_handoff.critical_items = data.critical_items
            patient_handoff.has_critical_items = len(data.critical_items) > 0

        await db.commit()
        await db.refresh(patient_handoff)

        return PatientHandoffResponse(
            id=patient_handoff.id,
            patient_id=patient_handoff.patient_id,
            situation=patient_handoff.situation,
            background=patient_handoff.background,
            assessment=patient_handoff.assessment,
            recommendations=patient_handoff.recommendations,
            critical_items=patient_handoff.critical_items or [],
            has_critical_items=patient_handoff.has_critical_items,
            pending_tasks=patient_handoff.pending_tasks or [],
            reviewed=patient_handoff.reviewed,
            questions_raised=patient_handoff.questions_raised or [],
            questions_resolved=patient_handoff.questions_resolved
        )

    async def raise_question(
        self,
        db: AsyncSession,
        provider_id: UUID,
        handoff_id: UUID,
        data: HandoffQuestion
    ):
        """Raise a question about a patient handoff"""

        result = await db.execute(
            select(ShiftHandoff)
            .options(selectinload(ShiftHandoff.patient_handoffs))
            .where(ShiftHandoff.id == handoff_id)
        )
        handoff = result.scalar_one_or_none()

        if not handoff:
            raise ValueError("Handoff not found")

        if handoff.incoming_provider_id != provider_id:
            raise ValueError("Only incoming provider can raise questions")

        # Find patient handoff
        patient_handoff = next(
            (ph for ph in handoff.patient_handoffs if ph.patient_id == data.patient_id),
            None
        )

        if not patient_handoff:
            raise ValueError("Patient not in handoff list")

        question = {
            "id": str(uuid4()),
            "question": data.question,
            "priority": data.priority.value,
            "asked_at": datetime.now(timezone.utc).isoformat(),
            "resolved": False
        }

        questions = patient_handoff.questions_raised or []
        questions.append(question)
        patient_handoff.questions_raised = questions
        patient_handoff.questions_resolved = False

        await db.commit()

    async def acknowledge_handoff(
        self,
        db: AsyncSession,
        provider_id: UUID,
        handoff_id: UUID,
        data: HandoffAcknowledge
    ) -> HandoffResponse:
        """Acknowledge receipt of handoff"""

        result = await db.execute(
            select(ShiftHandoff).where(ShiftHandoff.id == handoff_id)
        )
        handoff = result.scalar_one_or_none()

        if not handoff:
            raise ValueError("Handoff not found")

        if handoff.incoming_provider_id != provider_id:
            raise ValueError("Only incoming provider can acknowledge")

        if handoff.status != HandoffStatus.IN_PROGRESS:
            raise ValueError("Handoff is not in progress")

        now = datetime.now(timezone.utc)

        handoff.acknowledged = True
        handoff.acknowledged_at = now
        handoff.signature_incoming = data.signature
        handoff.feedback = data.feedback

        # Complete handoff
        handoff.status = HandoffStatus.COMPLETED
        handoff.status_updated_at = now
        handoff.completed_at = now

        if handoff.started_at:
            duration = (now - handoff.started_at).total_seconds() / 60
            handoff.duration_minutes = int(duration)

        # Mark all patient handoffs as reviewed
        await db.execute(
            update(PatientHandoff).where(
                PatientHandoff.shift_handoff_id == handoff_id
            ).values(
                reviewed=True,
                reviewed_at=now
            )
        )

        await db.commit()

        return await self.get_handoff(db, provider_id, handoff.tenant_id, handoff_id)

    async def generate_patient_sbar(
        self,
        db: AsyncSession,
        patient_id: UUID,
        provider_id: UUID
    ) -> Dict[str, Any]:
        """Generate SBAR data for a patient (would integrate with clinical data)"""

        # In production, this would fetch real patient data
        # from FHIR resources, orders, vitals, etc.

        return {
            "situation": {
                "chief_complaint": "",
                "admission_date": None,
                "current_status": "",
                "code_status": "Full Code"
            },
            "background": {
                "history": "",
                "allergies": [],
                "medications": [],
                "recent_procedures": []
            },
            "assessment": {
                "vital_signs": {},
                "labs": [],
                "imaging": [],
                "concerns": []
            },
            "recommendations": {
                "pending_tasks": [],
                "contingencies": "",
                "family_updates": "",
                "estimated_discharge": None
            }
        }
