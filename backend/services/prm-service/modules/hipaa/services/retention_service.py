"""
Data Retention Service

Data retention, legal hold, and secure destruction for HIPAA compliance.
Includes Right of Access (patient data export) workflow.
"""

import hashlib
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from modules.hipaa.models import (
    RetentionPolicy,
    RetentionSchedule,
    LegalHold,
    DestructionCertificate,
    RightOfAccessRequest,
    RetentionCategory,
    RetentionStatus,
    LegalHoldType,
    LegalHoldStatus,
    DestructionMethod,
    RightOfAccessStatus,
)


# Default retention periods by category (in years)
DEFAULT_RETENTION_PERIODS = {
    RetentionCategory.MEDICAL_RECORD: 7,
    RetentionCategory.MINOR_RECORD: 7,  # Plus time until age of majority
    RetentionCategory.BILLING_RECORD: 7,
    RetentionCategory.AUDIT_LOG: 7,
    RetentionCategory.CORRESPONDENCE: 5,
    RetentionCategory.CONSENT_FORM: 10,
    RetentionCategory.RESEARCH_DATA: 7,  # Or per protocol
    RetentionCategory.IMAGING: 7,
    RetentionCategory.LAB_RESULT: 7,
    RetentionCategory.PRESCRIPTION: 7,
}


class RetentionService:
    """
    Service for HIPAA data retention and destruction.

    Features:
    - Configurable retention policies by data category
    - Legal hold management
    - Secure data destruction with certificates
    - Right of Access (patient data export) workflow
    - State-specific retention rules
    """

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    # =========================================================================
    # Retention Policy Management
    # =========================================================================

    async def create_retention_policy(
        self,
        name: str,
        category: RetentionCategory,
        retention_years: int,
        retention_months: int = 0,
        description: Optional[str] = None,
        resource_types: Optional[List[str]] = None,
        applies_to_minors: bool = False,
        minor_retention_from_age: int = 18,
        minor_additional_years: int = 0,
        jurisdiction: Optional[str] = None,
        regulation_reference: Optional[str] = None,
        destruction_method: DestructionMethod = DestructionMethod.CRYPTOGRAPHIC_ERASURE,
        require_destruction_certificate: bool = True,
        archive_before_destruction: bool = True,
        archive_storage_class: str = "GLACIER",
        is_default: bool = False,
        created_by: Optional[UUID] = None,
    ) -> RetentionPolicy:
        """Create a data retention policy."""
        if is_default:
            # Clear existing default for this category
            query = select(RetentionPolicy).where(
                and_(
                    RetentionPolicy.tenant_id == self.tenant_id,
                    RetentionPolicy.category == category,
                    RetentionPolicy.is_default == True
                )
            )
            result = await self.db.execute(query)
            existing_default = result.scalar_one_or_none()
            if existing_default:
                existing_default.is_default = False

        policy = RetentionPolicy(
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            category=category,
            resource_types=resource_types,
            retention_years=retention_years,
            retention_months=retention_months,
            applies_to_minors=applies_to_minors,
            minor_retention_from_age=minor_retention_from_age,
            minor_additional_years=minor_additional_years,
            jurisdiction=jurisdiction,
            regulation_reference=regulation_reference,
            destruction_method=destruction_method,
            require_destruction_certificate=require_destruction_certificate,
            archive_before_destruction=archive_before_destruction,
            archive_storage_class=archive_storage_class,
            is_default=is_default,
            created_by=created_by,
        )

        self.db.add(policy)
        await self.db.commit()
        await self.db.refresh(policy)

        return policy

    async def get_policy_for_category(
        self,
        category: RetentionCategory,
        jurisdiction: Optional[str] = None,
    ) -> Optional[RetentionPolicy]:
        """Get the applicable retention policy for a category."""
        query = select(RetentionPolicy).where(
            and_(
                RetentionPolicy.tenant_id == self.tenant_id,
                RetentionPolicy.category == category,
                RetentionPolicy.is_active == True
            )
        )

        if jurisdiction:
            query = query.where(
                or_(
                    RetentionPolicy.jurisdiction == jurisdiction,
                    RetentionPolicy.jurisdiction.is_(None)
                )
            )

        query = query.order_by(
            RetentionPolicy.is_default.desc(),
            RetentionPolicy.created_at.desc()
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_retention_policies(
        self,
        active_only: bool = True,
        category: Optional[RetentionCategory] = None,
    ) -> List[RetentionPolicy]:
        """List retention policies."""
        query = select(RetentionPolicy).where(
            RetentionPolicy.tenant_id == self.tenant_id
        )

        if active_only:
            query = query.where(RetentionPolicy.is_active == True)

        if category:
            query = query.where(RetentionPolicy.category == category)

        query = query.order_by(RetentionPolicy.category, RetentionPolicy.created_at)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # =========================================================================
    # Retention Schedule Management
    # =========================================================================

    async def create_retention_schedule(
        self,
        resource_type: str,
        resource_id: UUID,
        policy_id: UUID,
        record_date: date,
        patient_id: Optional[UUID] = None,
        patient_dob: Optional[date] = None,  # For minor calculations
    ) -> RetentionSchedule:
        """Create a retention schedule for a record."""
        # Get policy
        query = select(RetentionPolicy).where(RetentionPolicy.id == policy_id)
        result = await self.db.execute(query)
        policy = result.scalar_one()

        # Calculate destruction date
        retention_start = record_date
        total_months = policy.retention_years * 12 + policy.retention_months

        # Handle minor records
        if policy.applies_to_minors and patient_dob:
            age_of_majority_date = patient_dob.replace(
                year=patient_dob.year + policy.minor_retention_from_age
            )
            if age_of_majority_date > retention_start:
                retention_start = age_of_majority_date
            total_months += policy.minor_additional_years * 12

        destruction_date = retention_start + timedelta(days=total_months * 30)

        schedule = RetentionSchedule(
            tenant_id=self.tenant_id,
            resource_type=resource_type,
            resource_id=resource_id,
            patient_id=patient_id,
            policy_id=policy_id,
            record_date=record_date,
            retention_start_date=retention_start,
            scheduled_destruction_date=destruction_date,
            status=RetentionStatus.ACTIVE,
        )

        self.db.add(schedule)
        await self.db.commit()
        await self.db.refresh(schedule)

        return schedule

    async def get_records_pending_destruction(
        self,
        before_date: Optional[date] = None,
    ) -> List[RetentionSchedule]:
        """Get records scheduled for destruction."""
        if before_date is None:
            before_date = date.today()

        query = select(RetentionSchedule).where(
            and_(
                RetentionSchedule.tenant_id == self.tenant_id,
                RetentionSchedule.scheduled_destruction_date <= before_date,
                RetentionSchedule.status == RetentionStatus.ACTIVE
            )
        ).order_by(RetentionSchedule.scheduled_destruction_date)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def check_legal_hold(self, resource_id: UUID) -> Tuple[bool, Optional[LegalHold]]:
        """Check if a resource is under legal hold."""
        # Get the schedule
        schedule_query = select(RetentionSchedule).where(
            and_(
                RetentionSchedule.tenant_id == self.tenant_id,
                RetentionSchedule.resource_id == resource_id
            )
        )
        schedule_result = await self.db.execute(schedule_query)
        schedule = schedule_result.scalar_one_or_none()

        if not schedule or schedule.status != RetentionStatus.LEGAL_HOLD:
            return False, None

        # Find the active hold
        hold_query = select(LegalHold).where(
            and_(
                LegalHold.tenant_id == self.tenant_id,
                LegalHold.status == LegalHoldStatus.ACTIVE
            )
        )
        hold_result = await self.db.execute(hold_query)

        for hold in hold_result.scalars().all():
            if schedule.patient_id and hold.affected_patient_ids:
                if schedule.patient_id in hold.affected_patient_ids:
                    return True, hold

        return False, None

    # =========================================================================
    # Legal Hold Management
    # =========================================================================

    async def create_legal_hold(
        self,
        name: str,
        hold_type: LegalHoldType,
        scope_type: str,
        scope_criteria: Dict[str, Any],
        effective_date: date,
        created_by: UUID,
        description: Optional[str] = None,
        matter_reference: Optional[str] = None,
        affected_patient_ids: Optional[List[UUID]] = None,
        legal_contact_name: Optional[str] = None,
        legal_contact_email: Optional[str] = None,
    ) -> LegalHold:
        """Create a legal hold to suspend data destruction."""
        hold_number = f"LH-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"

        hold = LegalHold(
            tenant_id=self.tenant_id,
            hold_number=hold_number,
            name=name,
            description=description,
            hold_type=hold_type,
            matter_reference=matter_reference,
            scope_type=scope_type,
            scope_criteria=scope_criteria,
            affected_patient_ids=affected_patient_ids,
            legal_contact_name=legal_contact_name,
            legal_contact_email=legal_contact_email,
            status=LegalHoldStatus.ACTIVE,
            effective_date=effective_date,
            created_by=created_by,
        )

        self.db.add(hold)

        # Apply hold to affected records
        if affected_patient_ids:
            for patient_id in affected_patient_ids:
                schedule_query = select(RetentionSchedule).where(
                    and_(
                        RetentionSchedule.tenant_id == self.tenant_id,
                        RetentionSchedule.patient_id == patient_id,
                        RetentionSchedule.status == RetentionStatus.ACTIVE
                    )
                )
                schedule_result = await self.db.execute(schedule_query)
                for schedule in schedule_result.scalars().all():
                    schedule.status = RetentionStatus.LEGAL_HOLD
                    hold.affected_record_count += 1

        await self.db.commit()
        await self.db.refresh(hold)

        return hold

    async def release_legal_hold(
        self,
        hold_id: UUID,
        released_by: UUID,
        release_reason: str,
        approved_by: Optional[UUID] = None,
    ) -> Optional[LegalHold]:
        """Release a legal hold."""
        query = select(LegalHold).where(
            and_(
                LegalHold.id == hold_id,
                LegalHold.tenant_id == self.tenant_id,
                LegalHold.status == LegalHoldStatus.ACTIVE
            )
        )
        result = await self.db.execute(query)
        hold = result.scalar_one_or_none()

        if hold:
            hold.status = LegalHoldStatus.RELEASED
            hold.release_date = date.today()
            hold.released_by = released_by
            hold.release_approved_by = approved_by
            hold.release_reason = release_reason
            hold.released_at = datetime.utcnow()
            hold.updated_at = datetime.utcnow()

            # Release affected records
            if hold.affected_patient_ids:
                for patient_id in hold.affected_patient_ids:
                    schedule_query = select(RetentionSchedule).where(
                        and_(
                            RetentionSchedule.tenant_id == self.tenant_id,
                            RetentionSchedule.patient_id == patient_id,
                            RetentionSchedule.status == RetentionStatus.LEGAL_HOLD
                        )
                    )
                    schedule_result = await self.db.execute(schedule_query)
                    for schedule in schedule_result.scalars().all():
                        schedule.status = RetentionStatus.ACTIVE

            await self.db.commit()
            await self.db.refresh(hold)

        return hold

    async def list_legal_holds(
        self,
        active_only: bool = True,
    ) -> List[LegalHold]:
        """List legal holds."""
        query = select(LegalHold).where(
            LegalHold.tenant_id == self.tenant_id
        )

        if active_only:
            query = query.where(LegalHold.status == LegalHoldStatus.ACTIVE)

        query = query.order_by(desc(LegalHold.created_at))

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # =========================================================================
    # Data Destruction
    # =========================================================================

    async def create_destruction_certificate(
        self,
        destruction_date: datetime,
        destruction_method: DestructionMethod,
        record_count: int,
        record_summary: Dict[str, Any],
        resource_types: List[str],
        authorized_by: UUID,
        created_by: UUID,
        affected_patient_ids: Optional[List[UUID]] = None,
    ) -> DestructionCertificate:
        """Create a destruction certificate documenting data destruction."""
        certificate_number = f"DC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8].upper()}"

        # Calculate certificate hash
        hash_input = {
            "certificate_number": certificate_number,
            "destruction_date": destruction_date.isoformat(),
            "destruction_method": destruction_method.value,
            "record_count": record_count,
            "resource_types": resource_types,
            "authorized_by": str(authorized_by),
        }
        import json
        certificate_hash = hashlib.sha256(
            json.dumps(hash_input, sort_keys=True).encode()
        ).hexdigest()

        # Certificate retained for 7 years after destruction
        certificate_retention_date = destruction_date.date() + timedelta(days=2555)

        certificate = DestructionCertificate(
            tenant_id=self.tenant_id,
            certificate_number=certificate_number,
            destruction_date=destruction_date,
            destruction_method=destruction_method,
            record_count=record_count,
            record_summary=record_summary,
            resource_types=resource_types,
            affected_patient_ids=affected_patient_ids,
            authorized_by=authorized_by,
            authorization_date=datetime.utcnow(),
            certificate_hash=certificate_hash,
            certificate_retention_date=certificate_retention_date,
            created_by=created_by,
        )

        self.db.add(certificate)
        await self.db.commit()
        await self.db.refresh(certificate)

        return certificate

    async def verify_destruction(
        self,
        certificate_id: UUID,
        verified_by: UUID,
        verification_method: str,
    ) -> Optional[DestructionCertificate]:
        """Verify that destruction was completed properly."""
        query = select(DestructionCertificate).where(
            and_(
                DestructionCertificate.id == certificate_id,
                DestructionCertificate.tenant_id == self.tenant_id
            )
        )
        result = await self.db.execute(query)
        certificate = result.scalar_one_or_none()

        if certificate:
            certificate.verified = True
            certificate.verified_by = verified_by
            certificate.verified_at = datetime.utcnow()
            certificate.verification_method = verification_method

            await self.db.commit()
            await self.db.refresh(certificate)

        return certificate

    async def mark_records_destroyed(
        self,
        schedule_ids: List[UUID],
        certificate_id: UUID,
    ) -> int:
        """Mark retention schedules as destroyed."""
        count = 0
        for schedule_id in schedule_ids:
            query = select(RetentionSchedule).where(
                and_(
                    RetentionSchedule.id == schedule_id,
                    RetentionSchedule.tenant_id == self.tenant_id
                )
            )
            result = await self.db.execute(query)
            schedule = result.scalar_one_or_none()

            if schedule:
                schedule.status = RetentionStatus.DESTROYED
                schedule.destroyed_at = datetime.utcnow()
                schedule.destruction_certificate_id = certificate_id
                schedule.updated_at = datetime.utcnow()
                count += 1

        await self.db.commit()
        return count

    # =========================================================================
    # Right of Access (Patient Data Export)
    # =========================================================================

    async def create_right_of_access_request(
        self,
        patient_id: UUID,
        requestor_type: str,
        delivery_method: str,
        requested_records: Dict[str, Any],
        representative_name: Optional[str] = None,
        representative_relationship: Optional[str] = None,
        delivery_email: Optional[str] = None,
        delivery_address: Optional[str] = None,
        date_range_start: Optional[date] = None,
        date_range_end: Optional[date] = None,
    ) -> RightOfAccessRequest:
        """Create a Right of Access request for patient data export."""
        request_number = f"ROA-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"

        # 30-day deadline (can be extended to 60 days with notice)
        due_date = datetime.utcnow() + timedelta(days=30)

        request = RightOfAccessRequest(
            tenant_id=self.tenant_id,
            request_number=request_number,
            patient_id=patient_id,
            requestor_type=requestor_type,
            representative_name=representative_name,
            representative_relationship=representative_relationship,
            delivery_email=delivery_email,
            delivery_address=delivery_address,
            delivery_method=delivery_method,
            requested_records=requested_records,
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            status=RightOfAccessStatus.RECEIVED,
            received_date=datetime.utcnow(),
            due_date=due_date,
        )

        self.db.add(request)
        await self.db.commit()
        await self.db.refresh(request)

        return request

    async def verify_identity(
        self,
        request_id: UUID,
        verification_method: str,
        verified_by: UUID,
    ) -> Optional[RightOfAccessRequest]:
        """Verify requestor identity."""
        query = select(RightOfAccessRequest).where(
            and_(
                RightOfAccessRequest.id == request_id,
                RightOfAccessRequest.tenant_id == self.tenant_id
            )
        )
        result = await self.db.execute(query)
        request = result.scalar_one_or_none()

        if request:
            request.identity_verified = True
            request.verification_method = verification_method
            request.verification_date = datetime.utcnow()
            request.verified_by = verified_by
            request.status = RightOfAccessStatus.PROCESSING
            request.processing_started_at = datetime.utcnow()
            request.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(request)

        return request

    async def extend_deadline(
        self,
        request_id: UUID,
        extension_reason: str,
    ) -> Optional[RightOfAccessRequest]:
        """Extend Right of Access deadline (30-day extension allowed)."""
        query = select(RightOfAccessRequest).where(
            and_(
                RightOfAccessRequest.id == request_id,
                RightOfAccessRequest.tenant_id == self.tenant_id,
                RightOfAccessRequest.extension_granted == False
            )
        )
        result = await self.db.execute(query)
        request = result.scalar_one_or_none()

        if request:
            request.extension_granted = True
            request.extension_reason = extension_reason
            request.extended_due_date = request.due_date + timedelta(days=30)
            request.status = RightOfAccessStatus.EXTENDED
            request.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(request)

        return request

    async def mark_ready_for_delivery(
        self,
        request_id: UUID,
        export_format: str,
        export_location: str,
        export_size_bytes: int,
    ) -> Optional[RightOfAccessRequest]:
        """Mark Right of Access export as ready for delivery."""
        query = select(RightOfAccessRequest).where(
            and_(
                RightOfAccessRequest.id == request_id,
                RightOfAccessRequest.tenant_id == self.tenant_id
            )
        )
        result = await self.db.execute(query)
        request = result.scalar_one_or_none()

        if request:
            request.status = RightOfAccessStatus.READY
            request.export_format = export_format
            request.export_location = export_location
            request.export_size_bytes = export_size_bytes
            request.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(request)

        return request

    async def mark_delivered(
        self,
        request_id: UUID,
        delivery_confirmation: Optional[str] = None,
    ) -> Optional[RightOfAccessRequest]:
        """Mark Right of Access as delivered."""
        query = select(RightOfAccessRequest).where(
            and_(
                RightOfAccessRequest.id == request_id,
                RightOfAccessRequest.tenant_id == self.tenant_id
            )
        )
        result = await self.db.execute(query)
        request = result.scalar_one_or_none()

        if request:
            request.status = RightOfAccessStatus.DELIVERED
            request.delivered_at = datetime.utcnow()
            request.delivery_confirmation = delivery_confirmation
            request.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(request)

        return request

    async def deny_request(
        self,
        request_id: UUID,
        denial_reason: str,
        denial_code: str,
    ) -> Optional[RightOfAccessRequest]:
        """Deny Right of Access request."""
        query = select(RightOfAccessRequest).where(
            and_(
                RightOfAccessRequest.id == request_id,
                RightOfAccessRequest.tenant_id == self.tenant_id
            )
        )
        result = await self.db.execute(query)
        request = result.scalar_one_or_none()

        if request:
            request.status = RightOfAccessStatus.DENIED
            request.denied = True
            request.denial_reason = denial_reason
            request.denial_code = denial_code
            request.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(request)

        return request

    async def list_pending_roa_requests(self) -> List[RightOfAccessRequest]:
        """List pending Right of Access requests."""
        query = select(RightOfAccessRequest).where(
            and_(
                RightOfAccessRequest.tenant_id == self.tenant_id,
                RightOfAccessRequest.status.in_([
                    RightOfAccessStatus.RECEIVED,
                    RightOfAccessStatus.IDENTITY_VERIFICATION,
                    RightOfAccessStatus.PROCESSING,
                    RightOfAccessStatus.READY,
                    RightOfAccessStatus.EXTENDED,
                ])
            )
        ).order_by(RightOfAccessRequest.due_date)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_overdue_roa_requests(self) -> List[RightOfAccessRequest]:
        """Get overdue Right of Access requests."""
        now = datetime.utcnow()

        query = select(RightOfAccessRequest).where(
            and_(
                RightOfAccessRequest.tenant_id == self.tenant_id,
                RightOfAccessRequest.status.in_([
                    RightOfAccessStatus.RECEIVED,
                    RightOfAccessStatus.IDENTITY_VERIFICATION,
                    RightOfAccessStatus.PROCESSING,
                    RightOfAccessStatus.EXTENDED,
                ]),
                or_(
                    and_(
                        RightOfAccessRequest.extension_granted == False,
                        RightOfAccessRequest.due_date < now
                    ),
                    and_(
                        RightOfAccessRequest.extension_granted == True,
                        RightOfAccessRequest.extended_due_date < now
                    )
                )
            )
        ).order_by(RightOfAccessRequest.due_date)

        result = await self.db.execute(query)
        return list(result.scalars().all())
