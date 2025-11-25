"""
Patient Portal Prescription Service
EPIC-014: Prescription management and refill requests
"""
from datetime import datetime, date, timedelta, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, desc

from modules.patient_portal.models import (
    PortalUser, RefillRequest, PortalAuditLog, PortalNotification,
    AuditAction, RefillStatus
)
from modules.patient_portal.schemas import (
    PrescriptionResponse, RefillRequest as RefillRequestSchema,
    RefillResponse, RefillStatusEnum
)


class PrescriptionService:
    """
    Handles prescription and medication management including:
    - Viewing active prescriptions
    - Requesting refills
    - Tracking refill status
    - Medication adherence
    """

    def __init__(self):
        pass

    # ==================== Prescriptions ====================

    async def get_prescriptions(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        patient_id: UUID = None,
        active_only: bool = True
    ) -> List[PrescriptionResponse]:
        """Get patient prescriptions"""

        result = await db.execute(
            select(PortalUser).where(PortalUser.id == user_id)
        )
        user = result.scalar_one()

        target_patient_id = patient_id or user.patient_id

        # In production, this would query the MedicationRequest FHIR resource
        # from the clinical workflows module
        prescriptions = await self._get_prescriptions_from_fhir(
            db, tenant_id, target_patient_id, active_only
        )

        return prescriptions

    async def _get_prescriptions_from_fhir(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        patient_id: UUID,
        active_only: bool
    ) -> List[PrescriptionResponse]:
        """Get prescriptions from FHIR MedicationRequest resources"""
        # Would integrate with clinical workflows module
        # For now, return empty list as placeholder
        return []

    async def get_prescription_detail(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        prescription_id: UUID
    ) -> PrescriptionResponse:
        """Get detailed prescription information"""

        result = await db.execute(
            select(PortalUser).where(PortalUser.id == user_id)
        )
        user = result.scalar_one()

        # Get from FHIR
        prescription = await self._get_prescription_by_id(
            db, tenant_id, prescription_id, user.patient_id
        )

        if not prescription:
            raise ValueError("Prescription not found")

        return prescription

    async def _get_prescription_by_id(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        prescription_id: UUID,
        patient_id: UUID
    ) -> Optional[PrescriptionResponse]:
        """Get prescription by ID from FHIR"""
        # Would integrate with clinical workflows module
        return None

    # ==================== Refill Requests ====================

    async def request_refill(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        request: RefillRequestSchema,
        ip_address: str = None
    ) -> RefillResponse:
        """Request prescription refill"""

        result = await db.execute(
            select(PortalUser).where(PortalUser.id == user_id)
        )
        user = result.scalar_one()

        # Verify prescription exists and belongs to patient
        prescription = await self._get_prescription_by_id(
            db, tenant_id, request.prescription_id, user.patient_id
        )

        # For now, create refill request with mock prescription data
        # In production, this would use actual prescription data

        refill = RefillRequest(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            patient_id=user.patient_id,
            prescription_id=request.prescription_id,
            medication_name=prescription.medication_name if prescription else "Unknown",
            medication_dosage=prescription.dosage if prescription else None,
            medication_instructions=prescription.instructions if prescription else None,
            quantity_requested=request.quantity_requested,
            days_supply_requested=request.days_supply_requested,
            notes=request.notes,
            urgent=request.urgent,
            pharmacy_id=request.pharmacy_id,
            pharmacy_name=None,  # Would look up from pharmacy service
            delivery_requested=request.delivery_requested,
            delivery_address=request.delivery_address,
            status=RefillStatus.REQUESTED,
            status_updated_at=datetime.now(timezone.utc)
        )
        db.add(refill)

        # Log refill request
        audit_log = PortalAuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            patient_id=user.patient_id,
            action=AuditAction.PRESCRIPTION_REFILL,
            action_category="prescription",
            action_description=f"Refill requested for {refill.medication_name}",
            details={
                "prescription_id": str(request.prescription_id),
                "urgent": request.urgent
            },
            ip_address=ip_address,
            success=True
        )
        db.add(audit_log)

        # Create notification for care team
        await self._notify_refill_request(db, tenant_id, refill)

        await db.commit()

        return RefillResponse(
            id=refill.id,
            prescription_id=refill.prescription_id,
            medication_name=refill.medication_name,
            medication_dosage=refill.medication_dosage,
            status=RefillStatusEnum(refill.status.value),
            pharmacy_name=refill.pharmacy_name,
            delivery_requested=refill.delivery_requested,
            tracking_number=refill.tracking_number,
            estimated_cost=float(refill.estimated_cost) if refill.estimated_cost else None,
            copay_amount=float(refill.copay_amount) if refill.copay_amount else None,
            ready_at=refill.ready_at,
            shipped_at=refill.shipped_at,
            denial_reason=refill.denial_reason,
            requires_appointment=refill.requires_appointment,
            created_at=refill.created_at,
            updated_at=refill.updated_at
        )

    async def _notify_refill_request(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        refill: RefillRequest
    ):
        """Notify care team of refill request"""
        # In production, this would create tasks/notifications for the care team
        # Could also integrate with pharmacy systems
        pass

    async def get_refill_requests(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        status: RefillStatus = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[RefillResponse]:
        """Get user's refill requests"""

        result = await db.execute(
            select(PortalUser).where(PortalUser.id == user_id)
        )
        user = result.scalar_one()

        query = select(RefillRequest).where(
            RefillRequest.patient_id == user.patient_id
        )

        if status:
            query = query.where(RefillRequest.status == status)

        query = query.order_by(desc(RefillRequest.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        refills = result.scalars().all()

        return [
            RefillResponse(
                id=r.id,
                prescription_id=r.prescription_id,
                medication_name=r.medication_name,
                medication_dosage=r.medication_dosage,
                status=RefillStatusEnum(r.status.value),
                pharmacy_name=r.pharmacy_name,
                delivery_requested=r.delivery_requested,
                tracking_number=r.tracking_number,
                estimated_cost=float(r.estimated_cost) if r.estimated_cost else None,
                copay_amount=float(r.copay_amount) if r.copay_amount else None,
                ready_at=r.ready_at,
                shipped_at=r.shipped_at,
                denial_reason=r.denial_reason,
                requires_appointment=r.requires_appointment,
                created_at=r.created_at,
                updated_at=r.updated_at
            )
            for r in refills
        ]

    async def get_refill_status(
        self,
        db: AsyncSession,
        user_id: UUID,
        refill_id: UUID
    ) -> RefillResponse:
        """Get status of specific refill request"""

        result = await db.execute(
            select(PortalUser).where(PortalUser.id == user_id)
        )
        user = result.scalar_one()

        result = await db.execute(
            select(RefillRequest).where(
                and_(
                    RefillRequest.id == refill_id,
                    RefillRequest.patient_id == user.patient_id
                )
            )
        )
        refill = result.scalar_one_or_none()

        if not refill:
            raise ValueError("Refill request not found")

        return RefillResponse(
            id=refill.id,
            prescription_id=refill.prescription_id,
            medication_name=refill.medication_name,
            medication_dosage=refill.medication_dosage,
            status=RefillStatusEnum(refill.status.value),
            pharmacy_name=refill.pharmacy_name,
            delivery_requested=refill.delivery_requested,
            tracking_number=refill.tracking_number,
            estimated_cost=float(refill.estimated_cost) if refill.estimated_cost else None,
            copay_amount=float(refill.copay_amount) if refill.copay_amount else None,
            ready_at=refill.ready_at,
            shipped_at=refill.shipped_at,
            denial_reason=refill.denial_reason,
            requires_appointment=refill.requires_appointment,
            created_at=refill.created_at,
            updated_at=refill.updated_at
        )

    async def cancel_refill_request(
        self,
        db: AsyncSession,
        user_id: UUID,
        refill_id: UUID
    ):
        """Cancel pending refill request"""

        result = await db.execute(
            select(PortalUser).where(PortalUser.id == user_id)
        )
        user = result.scalar_one()

        result = await db.execute(
            select(RefillRequest).where(
                and_(
                    RefillRequest.id == refill_id,
                    RefillRequest.patient_id == user.patient_id
                )
            )
        )
        refill = result.scalar_one_or_none()

        if not refill:
            raise ValueError("Refill request not found")

        # Can only cancel if still in early stages
        cancellable_statuses = [
            RefillStatus.REQUESTED,
            RefillStatus.PENDING_APPROVAL
        ]

        if refill.status not in cancellable_statuses:
            raise ValueError("This refill request cannot be cancelled")

        refill.status = RefillStatus.CANCELLED
        refill.status_updated_at = datetime.now(timezone.utc)

        await db.commit()

    # ==================== Medication Adherence ====================

    async def log_medication_taken(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        prescription_id: UUID,
        taken_at: datetime,
        taken: bool = True,
        notes: str = None
    ):
        """Log medication adherence"""

        result = await db.execute(
            select(PortalUser).where(PortalUser.id == user_id)
        )
        user = result.scalar_one()

        # In production, this would store in a medication adherence log table
        # and integrate with health tracking features

        # Log the adherence record
        audit_log = PortalAuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            patient_id=user.patient_id,
            action=AuditAction.PROFILE_UPDATE,  # Would use dedicated adherence action
            action_category="medication_adherence",
            action_description=f"Medication {'taken' if taken else 'missed'}",
            details={
                "prescription_id": str(prescription_id),
                "taken_at": taken_at.isoformat(),
                "taken": taken,
                "notes": notes
            },
            success=True
        )
        db.add(audit_log)
        await db.commit()

    async def get_adherence_stats(
        self,
        db: AsyncSession,
        user_id: UUID,
        prescription_id: UUID = None,
        days: int = 30
    ) -> Dict:
        """Get medication adherence statistics"""

        result = await db.execute(
            select(PortalUser).where(PortalUser.id == user_id)
        )
        user = result.scalar_one()

        # Would query adherence logs and calculate statistics
        # For now, return placeholder
        return {
            "adherence_rate": 0.0,
            "doses_taken": 0,
            "doses_missed": 0,
            "streak_days": 0,
            "period_days": days
        }

    # ==================== Pharmacy Management ====================

    async def get_pharmacies(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        search: str = None,
        latitude: float = None,
        longitude: float = None,
        radius_miles: float = 10
    ) -> List[Dict]:
        """Get list of pharmacies"""

        # Would integrate with pharmacy database or API
        # For now, return empty list
        return []

    async def set_preferred_pharmacy(
        self,
        db: AsyncSession,
        user_id: UUID,
        pharmacy_id: UUID
    ):
        """Set user's preferred pharmacy"""

        result = await db.execute(
            select(PortalUser).where(PortalUser.id == user_id)
        )
        user = result.scalar_one()

        # Would update patient's preferred pharmacy in FHIR Patient resource
        pass
