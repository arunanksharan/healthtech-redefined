"""
Provider Collaboration Consultation Service
EPIC-015: Specialist consultation management
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from modules.provider_collaboration.models import (
    Consultation, ConsultationReport, ProviderConversation, ConversationParticipant,
    CollaborationAuditLog, ConsultationStatus, ConsultationUrgency, ConversationType
)
from modules.provider_collaboration.schemas import (
    ConsultationCreate, ConsultationAccept, ConsultationDecline,
    ConsultationReportCreate, ConsultationReportAddendum, ConsultationQualityRating,
    ConsultationResponse, ConsultationReportResponse, ConsultationListResponse
)


class ConsultationService:
    """
    Handles specialist consultations including:
    - Consultation requests
    - Acceptance/decline workflow
    - Report generation
    - Quality tracking
    """

    def __init__(self):
        # SLA response times by urgency (in hours)
        self.sla_hours = {
            ConsultationUrgency.ROUTINE: 24,
            ConsultationUrgency.URGENT: 4,
            ConsultationUrgency.EMERGENT: 1,
            ConsultationUrgency.STAT: 0.5  # 30 minutes
        }

    async def create_consultation(
        self,
        db: AsyncSession,
        provider_id: UUID,
        tenant_id: UUID,
        data: ConsultationCreate,
        ip_address: str = None
    ) -> ConsultationResponse:
        """Create a consultation request"""

        # Calculate response deadline based on urgency
        urgency = ConsultationUrgency(data.urgency.value)
        sla_hours = self.sla_hours.get(urgency, 24)
        response_deadline = datetime.now(timezone.utc) + timedelta(hours=sla_hours)

        consultation = Consultation(
            id=uuid4(),
            tenant_id=tenant_id,
            requesting_provider_id=provider_id,
            consultant_specialty=data.consultant_specialty,
            preferred_consultant_id=data.preferred_consultant_id,
            patient_id=data.patient_id,
            encounter_id=data.encounter_id,
            urgency=urgency,
            clinical_question=data.clinical_question,
            relevant_history=data.relevant_history,
            working_diagnosis=data.working_diagnosis,
            reason_for_consult=data.reason_for_consult,
            attachments=data.attachments or [],
            lab_references=data.lab_references,
            imaging_references=data.imaging_references,
            medication_list=data.medication_list,
            status=ConsultationStatus.PENDING,
            status_updated_at=datetime.now(timezone.utc),
            response_deadline=response_deadline,
            expected_response_hours=int(sla_hours)
        )
        db.add(consultation)

        # Create consultation conversation
        conversation = ProviderConversation(
            id=uuid4(),
            tenant_id=tenant_id,
            type=ConversationType.CONSULTATION,
            name=f"Consultation: {data.consultant_specialty}",
            patient_id=data.patient_id,
            encounter_id=data.encounter_id,
            consultation_id=consultation.id,
            created_by=provider_id,
            is_encrypted=True
        )
        db.add(conversation)

        consultation.conversation_id = conversation.id

        # Add requesting provider to conversation
        requester_participant = ConversationParticipant(
            id=uuid4(),
            conversation_id=conversation.id,
            provider_id=provider_id,
            role="requester",
            can_add_members=False
        )
        db.add(requester_participant)

        # Add preferred consultant if specified
        if data.preferred_consultant_id:
            consultation.consultant_id = data.preferred_consultant_id
            consultant_participant = ConversationParticipant(
                id=uuid4(),
                conversation_id=conversation.id,
                provider_id=data.preferred_consultant_id,
                role="consultant"
            )
            db.add(consultant_participant)

        # Log action
        audit_log = CollaborationAuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            provider_id=provider_id,
            action="consultation_requested",
            action_category="consultation",
            action_description=f"Requested {data.consultant_specialty} consultation",
            entity_type="consultation",
            entity_id=consultation.id,
            patient_id=data.patient_id,
            details={
                "specialty": data.consultant_specialty,
                "urgency": data.urgency.value
            },
            ip_address=ip_address
        )
        db.add(audit_log)

        await db.commit()

        return await self.get_consultation(db, provider_id, tenant_id, consultation.id)

    async def get_consultation(
        self,
        db: AsyncSession,
        provider_id: UUID,
        tenant_id: UUID,
        consultation_id: UUID
    ) -> ConsultationResponse:
        """Get consultation details"""

        result = await db.execute(
            select(Consultation)
            .options(selectinload(Consultation.report))
            .where(
                and_(
                    Consultation.id == consultation_id,
                    Consultation.tenant_id == tenant_id
                )
            )
        )
        consultation = result.scalar_one_or_none()

        if not consultation:
            raise ValueError("Consultation not found")

        # Check access - requesting provider, consultant, or preferred consultant
        if provider_id not in [
            consultation.requesting_provider_id,
            consultation.consultant_id,
            consultation.preferred_consultant_id
        ]:
            raise ValueError("Not authorized to view this consultation")

        report_response = None
        if consultation.report:
            report_response = ConsultationReportResponse(
                id=consultation.report.id,
                consultation_id=consultation.report.consultation_id,
                author_id=consultation.report.author_id,
                impression=consultation.report.impression,
                recommendations=consultation.report.recommendations,
                assessment=consultation.report.assessment,
                plan=consultation.report.plan,
                follow_up_required=consultation.report.follow_up_required,
                follow_up_instructions=consultation.report.follow_up_instructions,
                diagnoses=consultation.report.diagnoses,
                is_draft=consultation.report.is_draft,
                is_signed=consultation.report.is_signed,
                signed_at=consultation.report.signed_at,
                addendums=consultation.report.addendums or [],
                created_at=consultation.report.created_at,
                updated_at=consultation.report.updated_at
            )

        return ConsultationResponse(
            id=consultation.id,
            requesting_provider_id=consultation.requesting_provider_id,
            requesting_service=consultation.requesting_service,
            consultant_id=consultation.consultant_id,
            consultant_specialty=consultation.consultant_specialty,
            patient_id=consultation.patient_id,
            urgency=consultation.urgency.value,
            clinical_question=consultation.clinical_question,
            status=consultation.status.value,
            response_deadline=consultation.response_deadline,
            first_response_at=consultation.first_response_at,
            sla_met=consultation.sla_met,
            conversation_id=consultation.conversation_id,
            has_report=consultation.has_report,
            report=report_response,
            quality_rating=consultation.quality_rating,
            created_at=consultation.created_at,
            updated_at=consultation.updated_at
        )

    async def list_consultations(
        self,
        db: AsyncSession,
        provider_id: UUID,
        tenant_id: UUID,
        role: str = "all",  # "requested", "received", "all"
        status: Optional[ConsultationStatus] = None,
        urgency: Optional[ConsultationUrgency] = None,
        patient_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20
    ) -> ConsultationListResponse:
        """List consultations for a provider"""

        query = select(Consultation).where(
            Consultation.tenant_id == tenant_id
        )

        # Filter by role
        if role == "requested":
            query = query.where(Consultation.requesting_provider_id == provider_id)
        elif role == "received":
            query = query.where(
                or_(
                    Consultation.consultant_id == provider_id,
                    Consultation.preferred_consultant_id == provider_id
                )
            )
        else:
            query = query.where(
                or_(
                    Consultation.requesting_provider_id == provider_id,
                    Consultation.consultant_id == provider_id,
                    Consultation.preferred_consultant_id == provider_id
                )
            )

        if status:
            query = query.where(Consultation.status == status)

        if urgency:
            query = query.where(Consultation.urgency == urgency)

        if patient_id:
            query = query.where(Consultation.patient_id == patient_id)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Get paginated results
        query = query.order_by(desc(Consultation.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        consultations = result.scalars().all()

        return ConsultationListResponse(
            consultations=[
                ConsultationResponse(
                    id=c.id,
                    requesting_provider_id=c.requesting_provider_id,
                    requesting_service=c.requesting_service,
                    consultant_id=c.consultant_id,
                    consultant_specialty=c.consultant_specialty,
                    patient_id=c.patient_id,
                    urgency=c.urgency.value,
                    clinical_question=c.clinical_question,
                    status=c.status.value,
                    response_deadline=c.response_deadline,
                    first_response_at=c.first_response_at,
                    sla_met=c.sla_met,
                    conversation_id=c.conversation_id,
                    has_report=c.has_report,
                    quality_rating=c.quality_rating,
                    created_at=c.created_at,
                    updated_at=c.updated_at
                )
                for c in consultations
            ],
            total=total,
            page=page,
            page_size=page_size
        )

    async def accept_consultation(
        self,
        db: AsyncSession,
        provider_id: UUID,
        tenant_id: UUID,
        consultation_id: UUID,
        data: ConsultationAccept
    ) -> ConsultationResponse:
        """Accept a consultation request"""

        result = await db.execute(
            select(Consultation).where(
                and_(
                    Consultation.id == consultation_id,
                    Consultation.tenant_id == tenant_id
                )
            )
        )
        consultation = result.scalar_one_or_none()

        if not consultation:
            raise ValueError("Consultation not found")

        if consultation.status != ConsultationStatus.PENDING:
            raise ValueError("Consultation is not pending")

        # Check if this provider can accept
        if consultation.preferred_consultant_id and consultation.preferred_consultant_id != provider_id:
            raise ValueError("Not authorized to accept this consultation")

        now = datetime.now(timezone.utc)

        consultation.status = ConsultationStatus.ACCEPTED
        consultation.status_updated_at = now
        consultation.consultant_id = provider_id
        consultation.accepted_at = now
        consultation.accepted_by = provider_id
        consultation.first_response_at = now

        # Check SLA
        if consultation.response_deadline:
            consultation.sla_met = now <= consultation.response_deadline

        if data.estimated_response_hours:
            consultation.expected_response_hours = data.estimated_response_hours

        # Add consultant to conversation if not already
        result = await db.execute(
            select(ConversationParticipant).where(
                and_(
                    ConversationParticipant.conversation_id == consultation.conversation_id,
                    ConversationParticipant.provider_id == provider_id
                )
            )
        )
        if not result.scalar_one_or_none():
            participant = ConversationParticipant(
                id=uuid4(),
                conversation_id=consultation.conversation_id,
                provider_id=provider_id,
                role="consultant"
            )
            db.add(participant)

        # Log action
        audit_log = CollaborationAuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            provider_id=provider_id,
            action="consultation_accepted",
            action_category="consultation",
            entity_type="consultation",
            entity_id=consultation.id,
            patient_id=consultation.patient_id,
            details={"sla_met": consultation.sla_met}
        )
        db.add(audit_log)

        await db.commit()

        return await self.get_consultation(db, provider_id, tenant_id, consultation_id)

    async def decline_consultation(
        self,
        db: AsyncSession,
        provider_id: UUID,
        tenant_id: UUID,
        consultation_id: UUID,
        data: ConsultationDecline
    ) -> ConsultationResponse:
        """Decline a consultation request"""

        result = await db.execute(
            select(Consultation).where(
                and_(
                    Consultation.id == consultation_id,
                    Consultation.tenant_id == tenant_id
                )
            )
        )
        consultation = result.scalar_one_or_none()

        if not consultation:
            raise ValueError("Consultation not found")

        if consultation.status != ConsultationStatus.PENDING:
            raise ValueError("Consultation is not pending")

        consultation.status = ConsultationStatus.DECLINED
        consultation.status_updated_at = datetime.now(timezone.utc)
        consultation.decline_reason = data.reason
        consultation.declined_at = datetime.now(timezone.utc)

        # If alternative suggested, update preferred consultant
        if data.suggest_alternative:
            consultation.preferred_consultant_id = data.suggest_alternative
            consultation.status = ConsultationStatus.PENDING
            consultation.decline_reason = None
            consultation.declined_at = None

        await db.commit()

        return await self.get_consultation(db, provider_id, tenant_id, consultation_id)

    async def create_report(
        self,
        db: AsyncSession,
        provider_id: UUID,
        tenant_id: UUID,
        consultation_id: UUID,
        data: ConsultationReportCreate
    ) -> ConsultationReportResponse:
        """Create consultation report"""

        result = await db.execute(
            select(Consultation).where(
                and_(
                    Consultation.id == consultation_id,
                    Consultation.tenant_id == tenant_id
                )
            )
        )
        consultation = result.scalar_one_or_none()

        if not consultation:
            raise ValueError("Consultation not found")

        if consultation.consultant_id != provider_id:
            raise ValueError("Only assigned consultant can create report")

        if consultation.has_report:
            raise ValueError("Report already exists")

        report = ConsultationReport(
            id=uuid4(),
            consultation_id=consultation_id,
            tenant_id=tenant_id,
            author_id=provider_id,
            impression=data.impression,
            recommendations=data.recommendations,
            assessment=data.assessment,
            plan=data.plan,
            follow_up_required=data.follow_up_required,
            follow_up_instructions=data.follow_up_instructions,
            diagnoses=data.diagnoses,
            differential_diagnoses=data.differential_diagnoses,
            recommended_tests=data.recommended_tests,
            recommended_procedures=data.recommended_procedures,
            medication_recommendations=data.medication_recommendations,
            is_draft=True
        )
        db.add(report)

        consultation.has_report = True
        consultation.report_id = report.id
        consultation.status = ConsultationStatus.AWAITING_RESPONSE
        consultation.status_updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(report)

        return ConsultationReportResponse(
            id=report.id,
            consultation_id=report.consultation_id,
            author_id=report.author_id,
            impression=report.impression,
            recommendations=report.recommendations,
            assessment=report.assessment,
            plan=report.plan,
            follow_up_required=report.follow_up_required,
            follow_up_instructions=report.follow_up_instructions,
            diagnoses=report.diagnoses,
            is_draft=report.is_draft,
            is_signed=report.is_signed,
            signed_at=report.signed_at,
            addendums=report.addendums or [],
            created_at=report.created_at,
            updated_at=report.updated_at
        )

    async def sign_report(
        self,
        db: AsyncSession,
        provider_id: UUID,
        tenant_id: UUID,
        consultation_id: UUID
    ) -> ConsultationReportResponse:
        """Sign and finalize consultation report"""

        result = await db.execute(
            select(ConsultationReport).where(
                and_(
                    ConsultationReport.consultation_id == consultation_id,
                    ConsultationReport.tenant_id == tenant_id
                )
            )
        )
        report = result.scalar_one_or_none()

        if not report:
            raise ValueError("Report not found")

        if report.author_id != provider_id:
            raise ValueError("Only report author can sign")

        if report.is_signed:
            raise ValueError("Report already signed")

        now = datetime.now(timezone.utc)
        report.is_draft = False
        report.is_signed = True
        report.signed_at = now
        report.signed_by = provider_id

        # Update consultation status
        await db.execute(
            update(Consultation).where(
                Consultation.id == consultation_id
            ).values(
                status=ConsultationStatus.COMPLETED,
                status_updated_at=now,
                completed_at=now
            )
        )

        await db.commit()
        await db.refresh(report)

        return ConsultationReportResponse(
            id=report.id,
            consultation_id=report.consultation_id,
            author_id=report.author_id,
            impression=report.impression,
            recommendations=report.recommendations,
            assessment=report.assessment,
            plan=report.plan,
            follow_up_required=report.follow_up_required,
            follow_up_instructions=report.follow_up_instructions,
            diagnoses=report.diagnoses,
            is_draft=report.is_draft,
            is_signed=report.is_signed,
            signed_at=report.signed_at,
            addendums=report.addendums or [],
            created_at=report.created_at,
            updated_at=report.updated_at
        )

    async def add_addendum(
        self,
        db: AsyncSession,
        provider_id: UUID,
        consultation_id: UUID,
        data: ConsultationReportAddendum
    ) -> ConsultationReportResponse:
        """Add addendum to signed report"""

        result = await db.execute(
            select(ConsultationReport).where(
                ConsultationReport.consultation_id == consultation_id
            )
        )
        report = result.scalar_one_or_none()

        if not report:
            raise ValueError("Report not found")

        if not report.is_signed:
            raise ValueError("Can only add addendum to signed reports")

        addendum = {
            "id": str(uuid4()),
            "author_id": str(provider_id),
            "content": data.content,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        addendums = report.addendums or []
        addendums.append(addendum)
        report.addendums = addendums

        await db.commit()
        await db.refresh(report)

        return ConsultationReportResponse(
            id=report.id,
            consultation_id=report.consultation_id,
            author_id=report.author_id,
            impression=report.impression,
            recommendations=report.recommendations,
            assessment=report.assessment,
            plan=report.plan,
            follow_up_required=report.follow_up_required,
            follow_up_instructions=report.follow_up_instructions,
            diagnoses=report.diagnoses,
            is_draft=report.is_draft,
            is_signed=report.is_signed,
            signed_at=report.signed_at,
            addendums=report.addendums,
            created_at=report.created_at,
            updated_at=report.updated_at
        )

    async def rate_consultation(
        self,
        db: AsyncSession,
        provider_id: UUID,
        consultation_id: UUID,
        data: ConsultationQualityRating
    ):
        """Rate consultation quality"""

        result = await db.execute(
            select(Consultation).where(
                Consultation.id == consultation_id
            )
        )
        consultation = result.scalar_one_or_none()

        if not consultation:
            raise ValueError("Consultation not found")

        if consultation.requesting_provider_id != provider_id:
            raise ValueError("Only requesting provider can rate")

        if consultation.status != ConsultationStatus.COMPLETED:
            raise ValueError("Can only rate completed consultations")

        consultation.quality_rating = data.rating
        consultation.quality_feedback = data.feedback
        consultation.rated_by = provider_id
        consultation.rated_at = datetime.now(timezone.utc)

        await db.commit()
