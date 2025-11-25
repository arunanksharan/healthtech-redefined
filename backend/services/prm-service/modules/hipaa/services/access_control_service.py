"""
Access Control Service

Minimum Necessary Access Controls for HIPAA compliance.
Includes treatment relationship verification, break-the-glass, and anomaly detection.
"""

from datetime import datetime, timedelta, time
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from modules.hipaa.models import (
    TreatmentRelationship,
    AccessRequest,
    AccessCertification,
    CertificationCampaign,
    AccessAnomaly,
    VIPPatient,
    RelationshipType,
    RelationshipStatus,
    AccessRequestStatus,
    CertificationStatus,
    AnomalyType,
    AnomalySeverity,
    AccessJustification,
)


# Normal working hours configuration
NORMAL_WORKING_HOURS = {
    "start": time(6, 0),   # 6:00 AM
    "end": time(22, 0),    # 10:00 PM
}


class AccessControlService:
    """
    Service for HIPAA Minimum Necessary access controls.

    Features:
    - Treatment relationship verification
    - Break-the-glass emergency access
    - Access request workflows
    - Periodic access certification
    - Anomaly detection and alerting
    - VIP patient monitoring
    """

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    # =========================================================================
    # Treatment Relationship Management
    # =========================================================================

    async def create_treatment_relationship(
        self,
        patient_id: UUID,
        provider_id: UUID,
        provider_type: str,
        relationship_type: RelationshipType,
        effective_date: datetime,
        expiration_date: Optional[datetime] = None,
        referral_id: Optional[UUID] = None,
        authorization_number: Optional[str] = None,
        care_team_id: Optional[UUID] = None,
        care_team_role: Optional[str] = None,
        facility_id: Optional[UUID] = None,
        department: Optional[str] = None,
        allowed_phi_categories: Optional[List[str]] = None,
        restricted_phi_categories: Optional[List[str]] = None,
        created_by: Optional[UUID] = None,
    ) -> TreatmentRelationship:
        """Create a treatment relationship between patient and provider."""
        relationship = TreatmentRelationship(
            tenant_id=self.tenant_id,
            patient_id=patient_id,
            provider_id=provider_id,
            provider_type=provider_type,
            relationship_type=relationship_type,
            status=RelationshipStatus.ACTIVE,
            effective_date=effective_date,
            expiration_date=expiration_date,
            referral_id=referral_id,
            authorization_number=authorization_number,
            care_team_id=care_team_id,
            care_team_role=care_team_role,
            facility_id=facility_id,
            department=department,
            allowed_phi_categories=allowed_phi_categories,
            restricted_phi_categories=restricted_phi_categories,
            created_by=created_by,
        )

        self.db.add(relationship)
        await self.db.commit()
        await self.db.refresh(relationship)

        return relationship

    async def verify_treatment_relationship(
        self,
        patient_id: UUID,
        provider_id: UUID,
        phi_category: Optional[str] = None,
    ) -> Tuple[bool, Optional[TreatmentRelationship], str]:
        """
        Verify if a provider has an active treatment relationship with a patient.
        Returns (is_valid, relationship, reason).
        """
        today = datetime.utcnow().date()

        query = select(TreatmentRelationship).where(
            and_(
                TreatmentRelationship.tenant_id == self.tenant_id,
                TreatmentRelationship.patient_id == patient_id,
                TreatmentRelationship.provider_id == provider_id,
                TreatmentRelationship.status == RelationshipStatus.ACTIVE,
                TreatmentRelationship.effective_date <= today,
                or_(
                    TreatmentRelationship.expiration_date.is_(None),
                    TreatmentRelationship.expiration_date >= today
                )
            )
        )

        result = await self.db.execute(query)
        relationship = result.scalar_one_or_none()

        if not relationship:
            return False, None, "No active treatment relationship found"

        # Check PHI category restrictions if specified
        if phi_category:
            if relationship.restricted_phi_categories and phi_category in relationship.restricted_phi_categories:
                return False, relationship, f"Access to {phi_category} is restricted for this relationship"

            if relationship.allowed_phi_categories and phi_category not in relationship.allowed_phi_categories:
                return False, relationship, f"Access to {phi_category} is not allowed for this relationship"

        return True, relationship, "Valid treatment relationship"

    async def get_patient_relationships(
        self,
        patient_id: UUID,
        active_only: bool = True,
    ) -> List[TreatmentRelationship]:
        """Get all treatment relationships for a patient."""
        query = select(TreatmentRelationship).where(
            and_(
                TreatmentRelationship.tenant_id == self.tenant_id,
                TreatmentRelationship.patient_id == patient_id
            )
        )

        if active_only:
            query = query.where(TreatmentRelationship.status == RelationshipStatus.ACTIVE)

        query = query.order_by(desc(TreatmentRelationship.created_at))

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_provider_patients(
        self,
        provider_id: UUID,
        active_only: bool = True,
    ) -> List[TreatmentRelationship]:
        """Get all patients assigned to a provider."""
        query = select(TreatmentRelationship).where(
            and_(
                TreatmentRelationship.tenant_id == self.tenant_id,
                TreatmentRelationship.provider_id == provider_id
            )
        )

        if active_only:
            query = query.where(TreatmentRelationship.status == RelationshipStatus.ACTIVE)

        query = query.order_by(desc(TreatmentRelationship.created_at))

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def terminate_relationship(
        self,
        relationship_id: UUID,
    ) -> Optional[TreatmentRelationship]:
        """Terminate a treatment relationship."""
        query = select(TreatmentRelationship).where(
            and_(
                TreatmentRelationship.id == relationship_id,
                TreatmentRelationship.tenant_id == self.tenant_id
            )
        )
        result = await self.db.execute(query)
        relationship = result.scalar_one_or_none()

        if relationship:
            relationship.status = RelationshipStatus.TERMINATED
            relationship.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(relationship)

        return relationship

    # =========================================================================
    # Access Request Workflow
    # =========================================================================

    async def create_access_request(
        self,
        requester_id: UUID,
        patient_id: UUID,
        requested_phi_categories: List[str],
        justification: AccessJustification,
        justification_details: str,
        requester_name: Optional[str] = None,
        requester_role: Optional[str] = None,
        requested_resources: Optional[Dict[str, Any]] = None,
        clinical_context: Optional[str] = None,
        access_duration_hours: int = 24,
    ) -> AccessRequest:
        """Create a PHI access request for cases without direct treatment relationship."""
        request_number = f"AR-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"

        request = AccessRequest(
            tenant_id=self.tenant_id,
            request_number=request_number,
            requester_id=requester_id,
            requester_name=requester_name,
            requester_role=requester_role,
            patient_id=patient_id,
            requested_phi_categories=requested_phi_categories,
            requested_resources=requested_resources,
            justification=justification,
            justification_details=justification_details,
            clinical_context=clinical_context,
            status=AccessRequestStatus.PENDING,
        )

        self.db.add(request)
        await self.db.commit()
        await self.db.refresh(request)

        return request

    async def approve_access_request(
        self,
        request_id: UUID,
        approver_id: UUID,
        approver_name: Optional[str] = None,
        access_duration_hours: int = 24,
    ) -> Optional[AccessRequest]:
        """Approve a PHI access request."""
        query = select(AccessRequest).where(
            and_(
                AccessRequest.id == request_id,
                AccessRequest.tenant_id == self.tenant_id,
                AccessRequest.status == AccessRequestStatus.PENDING
            )
        )
        result = await self.db.execute(query)
        request = result.scalar_one_or_none()

        if request:
            request.status = AccessRequestStatus.APPROVED
            request.approver_id = approver_id
            request.approver_name = approver_name
            request.approval_date = datetime.utcnow()
            request.access_start = datetime.utcnow()
            request.access_end = datetime.utcnow() + timedelta(hours=access_duration_hours)
            request.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(request)

        return request

    async def deny_access_request(
        self,
        request_id: UUID,
        approver_id: UUID,
        denial_reason: str,
        approver_name: Optional[str] = None,
    ) -> Optional[AccessRequest]:
        """Deny a PHI access request."""
        query = select(AccessRequest).where(
            and_(
                AccessRequest.id == request_id,
                AccessRequest.tenant_id == self.tenant_id,
                AccessRequest.status == AccessRequestStatus.PENDING
            )
        )
        result = await self.db.execute(query)
        request = result.scalar_one_or_none()

        if request:
            request.status = AccessRequestStatus.DENIED
            request.approver_id = approver_id
            request.approver_name = approver_name
            request.approval_date = datetime.utcnow()
            request.denial_reason = denial_reason
            request.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(request)

        return request

    async def check_access_request(
        self,
        user_id: UUID,
        patient_id: UUID,
    ) -> Tuple[bool, Optional[AccessRequest]]:
        """Check if user has an approved, non-expired access request for patient."""
        now = datetime.utcnow()

        query = select(AccessRequest).where(
            and_(
                AccessRequest.tenant_id == self.tenant_id,
                AccessRequest.requester_id == user_id,
                AccessRequest.patient_id == patient_id,
                AccessRequest.status == AccessRequestStatus.APPROVED,
                AccessRequest.access_start <= now,
                AccessRequest.access_end >= now
            )
        )

        result = await self.db.execute(query)
        request = result.scalar_one_or_none()

        return (request is not None, request)

    async def list_pending_access_requests(self) -> List[AccessRequest]:
        """List all pending access requests."""
        query = select(AccessRequest).where(
            and_(
                AccessRequest.tenant_id == self.tenant_id,
                AccessRequest.status == AccessRequestStatus.PENDING
            )
        ).order_by(AccessRequest.created_at)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # =========================================================================
    # Access Certification
    # =========================================================================

    async def create_certification_campaign(
        self,
        name: str,
        start_date: datetime,
        end_date: datetime,
        scope_type: str,
        description: Optional[str] = None,
        scope_criteria: Optional[Dict[str, Any]] = None,
        created_by: Optional[UUID] = None,
    ) -> CertificationCampaign:
        """Create an access certification campaign."""
        campaign = CertificationCampaign(
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            start_date=start_date,
            end_date=end_date,
            scope_type=scope_type,
            scope_criteria=scope_criteria,
            is_active=True,
            created_by=created_by,
        )

        self.db.add(campaign)
        await self.db.commit()
        await self.db.refresh(campaign)

        return campaign

    async def create_certification_item(
        self,
        campaign_id: UUID,
        user_id: UUID,
        reviewer_id: UUID,
        access_type: str,
        access_details: Dict[str, Any],
        due_date: datetime,
        user_name: Optional[str] = None,
        role_id: Optional[UUID] = None,
        role_name: Optional[str] = None,
        reviewer_name: Optional[str] = None,
        campaign_name: Optional[str] = None,
    ) -> AccessCertification:
        """Create an access certification item for review."""
        certification = AccessCertification(
            tenant_id=self.tenant_id,
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            user_id=user_id,
            user_name=user_name,
            role_id=role_id,
            role_name=role_name,
            access_type=access_type,
            access_details=access_details,
            reviewer_id=reviewer_id,
            reviewer_name=reviewer_name,
            status=CertificationStatus.PENDING,
            due_date=due_date,
        )

        self.db.add(certification)

        # Update campaign count
        query = select(CertificationCampaign).where(
            CertificationCampaign.id == campaign_id
        )
        result = await self.db.execute(query)
        campaign = result.scalar_one_or_none()
        if campaign:
            campaign.total_certifications += 1

        await self.db.commit()
        await self.db.refresh(certification)

        return certification

    async def certify_access(
        self,
        certification_id: UUID,
        certified: bool,
        comments: Optional[str] = None,
    ) -> Optional[AccessCertification]:
        """Certify or decertify access."""
        query = select(AccessCertification).where(
            and_(
                AccessCertification.id == certification_id,
                AccessCertification.tenant_id == self.tenant_id
            )
        )
        result = await self.db.execute(query)
        certification = result.scalar_one_or_none()

        if certification:
            certification.status = CertificationStatus.CERTIFIED if certified else CertificationStatus.DECERTIFIED
            certification.certification_date = datetime.utcnow()
            certification.comments = comments
            certification.updated_at = datetime.utcnow()

            # Update campaign counts
            campaign_query = select(CertificationCampaign).where(
                CertificationCampaign.id == certification.campaign_id
            )
            campaign_result = await self.db.execute(campaign_query)
            campaign = campaign_result.scalar_one_or_none()

            if campaign:
                campaign.completed_certifications += 1
                if certified:
                    campaign.certified_count += 1
                else:
                    campaign.decertified_count += 1

            await self.db.commit()
            await self.db.refresh(certification)

        return certification

    async def get_pending_certifications(
        self,
        reviewer_id: UUID,
    ) -> List[AccessCertification]:
        """Get pending certifications for a reviewer."""
        query = select(AccessCertification).where(
            and_(
                AccessCertification.tenant_id == self.tenant_id,
                AccessCertification.reviewer_id == reviewer_id,
                AccessCertification.status == CertificationStatus.PENDING
            )
        ).order_by(AccessCertification.due_date)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # =========================================================================
    # Anomaly Detection
    # =========================================================================

    async def detect_after_hours_access(
        self,
        user_id: UUID,
        access_time: datetime,
        patient_id: UUID,
        evidence: Dict[str, Any],
    ) -> Optional[AccessAnomaly]:
        """Detect and record after-hours PHI access."""
        access_time_only = access_time.time()

        if access_time_only < NORMAL_WORKING_HOURS["start"] or access_time_only > NORMAL_WORKING_HOURS["end"]:
            return await self._create_anomaly(
                anomaly_type=AnomalyType.AFTER_HOURS,
                severity=AnomalySeverity.MEDIUM,
                user_id=user_id,
                description=f"PHI access outside normal hours at {access_time.strftime('%H:%M')}",
                evidence=evidence,
                affected_patient_ids=[patient_id],
            )
        return None

    async def detect_bulk_access(
        self,
        user_id: UUID,
        record_count: int,
        time_window_minutes: int,
        patient_ids: List[UUID],
        threshold: int = 50,
    ) -> Optional[AccessAnomaly]:
        """Detect bulk data access patterns."""
        if record_count > threshold:
            return await self._create_anomaly(
                anomaly_type=AnomalyType.BULK_ACCESS,
                severity=AnomalySeverity.HIGH,
                user_id=user_id,
                description=f"Accessed {record_count} records in {time_window_minutes} minutes",
                evidence={
                    "record_count": record_count,
                    "time_window_minutes": time_window_minutes,
                    "threshold": threshold,
                },
                affected_patient_ids=patient_ids,
            )
        return None

    async def detect_vip_access(
        self,
        user_id: UUID,
        user_name: Optional[str],
        patient_id: UUID,
        evidence: Dict[str, Any],
    ) -> Optional[AccessAnomaly]:
        """Detect access to VIP patient records."""
        # Check if patient is VIP
        query = select(VIPPatient).where(
            and_(
                VIPPatient.tenant_id == self.tenant_id,
                VIPPatient.patient_id == patient_id,
                VIPPatient.is_active == True
            )
        )
        result = await self.db.execute(query)
        vip = result.scalar_one_or_none()

        if vip and vip.access_alerts_enabled:
            # Check if user is in allowed list
            if vip.allowed_user_ids and user_id in vip.allowed_user_ids:
                return None

            return await self._create_anomaly(
                anomaly_type=AnomalyType.VIP_ACCESS,
                severity=AnomalySeverity.HIGH,
                user_id=user_id,
                user_name=user_name,
                description=f"Access to VIP patient record ({vip.vip_reason})",
                evidence=evidence,
                affected_patient_ids=[patient_id],
            )
        return None

    async def _create_anomaly(
        self,
        anomaly_type: AnomalyType,
        severity: AnomalySeverity,
        user_id: UUID,
        description: str,
        evidence: Dict[str, Any],
        user_name: Optional[str] = None,
        user_role: Optional[str] = None,
        source_ip: Optional[str] = None,
        affected_patient_ids: Optional[List[UUID]] = None,
        audit_log_ids: Optional[List[UUID]] = None,
    ) -> AccessAnomaly:
        """Create an access anomaly record."""
        anomaly = AccessAnomaly(
            tenant_id=self.tenant_id,
            anomaly_type=anomaly_type,
            severity=severity,
            user_id=user_id,
            user_name=user_name,
            user_role=user_role,
            source_ip=source_ip,
            description=description,
            evidence=evidence,
            affected_patient_ids=affected_patient_ids,
            audit_log_ids=audit_log_ids,
        )

        self.db.add(anomaly)
        await self.db.commit()
        await self.db.refresh(anomaly)

        return anomaly

    async def acknowledge_anomaly(
        self,
        anomaly_id: UUID,
        acknowledged_by: UUID,
        investigation_notes: Optional[str] = None,
    ) -> Optional[AccessAnomaly]:
        """Acknowledge an access anomaly."""
        query = select(AccessAnomaly).where(
            and_(
                AccessAnomaly.id == anomaly_id,
                AccessAnomaly.tenant_id == self.tenant_id
            )
        )
        result = await self.db.execute(query)
        anomaly = result.scalar_one_or_none()

        if anomaly:
            anomaly.acknowledged = True
            anomaly.acknowledged_by = acknowledged_by
            anomaly.acknowledged_at = datetime.utcnow()
            anomaly.investigation_notes = investigation_notes
            anomaly.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(anomaly)

        return anomaly

    async def resolve_anomaly(
        self,
        anomaly_id: UUID,
        resolution: str,
        false_positive: bool = False,
    ) -> Optional[AccessAnomaly]:
        """Resolve an access anomaly."""
        query = select(AccessAnomaly).where(
            and_(
                AccessAnomaly.id == anomaly_id,
                AccessAnomaly.tenant_id == self.tenant_id
            )
        )
        result = await self.db.execute(query)
        anomaly = result.scalar_one_or_none()

        if anomaly:
            anomaly.resolved = True
            anomaly.resolution = resolution
            anomaly.false_positive = false_positive
            anomaly.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(anomaly)

        return anomaly

    async def list_open_anomalies(
        self,
        severity: Optional[AnomalySeverity] = None,
    ) -> List[AccessAnomaly]:
        """List open (unresolved) anomalies."""
        query = select(AccessAnomaly).where(
            and_(
                AccessAnomaly.tenant_id == self.tenant_id,
                AccessAnomaly.resolved == False
            )
        )

        if severity:
            query = query.where(AccessAnomaly.severity == severity)

        query = query.order_by(
            desc(AccessAnomaly.severity),
            desc(AccessAnomaly.detected_at)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_anomaly_statistics(self) -> Dict[str, Any]:
        """Get anomaly statistics for dashboard."""
        # Total open anomalies
        open_query = select(func.count()).select_from(AccessAnomaly).where(
            and_(
                AccessAnomaly.tenant_id == self.tenant_id,
                AccessAnomaly.resolved == False
            )
        )
        open_result = await self.db.execute(open_query)
        total_open = open_result.scalar()

        # By severity
        severity_query = (
            select(AccessAnomaly.severity, func.count(AccessAnomaly.id))
            .where(
                and_(
                    AccessAnomaly.tenant_id == self.tenant_id,
                    AccessAnomaly.resolved == False
                )
            )
            .group_by(AccessAnomaly.severity)
        )
        severity_result = await self.db.execute(severity_query)
        by_severity = {row[0].value: row[1] for row in severity_result.all()}

        # By type
        type_query = (
            select(AccessAnomaly.anomaly_type, func.count(AccessAnomaly.id))
            .where(
                and_(
                    AccessAnomaly.tenant_id == self.tenant_id,
                    AccessAnomaly.resolved == False
                )
            )
            .group_by(AccessAnomaly.anomaly_type)
        )
        type_result = await self.db.execute(type_query)
        by_type = {row[0].value: row[1] for row in type_result.all()}

        return {
            "total_open": total_open,
            "by_severity": by_severity,
            "by_type": by_type,
        }

    # =========================================================================
    # VIP Patient Management
    # =========================================================================

    async def designate_vip_patient(
        self,
        patient_id: UUID,
        vip_reason: str,
        enhanced_monitoring: bool = True,
        access_alerts_enabled: bool = True,
        allowed_user_ids: Optional[List[UUID]] = None,
        allowed_roles: Optional[List[str]] = None,
        alert_recipients: Optional[List[str]] = None,
        created_by: Optional[UUID] = None,
    ) -> VIPPatient:
        """Designate a patient as VIP for enhanced monitoring."""
        vip = VIPPatient(
            tenant_id=self.tenant_id,
            patient_id=patient_id,
            vip_reason=vip_reason,
            enhanced_monitoring=enhanced_monitoring,
            access_alerts_enabled=access_alerts_enabled,
            allowed_user_ids=allowed_user_ids,
            allowed_roles=allowed_roles,
            alert_recipients=alert_recipients,
            created_by=created_by,
        )

        self.db.add(vip)
        await self.db.commit()
        await self.db.refresh(vip)

        return vip

    async def is_vip_patient(self, patient_id: UUID) -> bool:
        """Check if a patient is designated as VIP."""
        query = select(VIPPatient).where(
            and_(
                VIPPatient.tenant_id == self.tenant_id,
                VIPPatient.patient_id == patient_id,
                VIPPatient.is_active == True
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def list_vip_patients(self) -> List[VIPPatient]:
        """List all VIP patients."""
        query = select(VIPPatient).where(
            and_(
                VIPPatient.tenant_id == self.tenant_id,
                VIPPatient.is_active == True
            )
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())
