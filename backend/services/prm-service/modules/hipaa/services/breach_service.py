"""
Breach Detection and Notification Service

HIPAA breach management including detection, assessment, and notification workflow.
Implements the 4-factor risk assessment and HHS notification requirements.
"""

from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from modules.hipaa.models import (
    BreachIncident,
    BreachAssessment,
    BreachNotification,
    BreachStatus,
    BreachType,
    NotificationType,
    NotificationStatus,
    RiskLevel,
)


class BreachService:
    """
    Service for HIPAA breach management.

    Features:
    - Breach incident tracking
    - 4-factor risk assessment
    - HHS notification generation (60-day rule)
    - Patient notification workflow
    - Media notification for >500 individuals
    - Breach log and reporting
    """

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    # =========================================================================
    # Breach Incident Management
    # =========================================================================

    async def create_breach_incident(
        self,
        breach_type: BreachType,
        description: str,
        phi_categories_involved: List[str],
        discovered_date: datetime,
        discovered_by: Optional[UUID] = None,
        discovery_method: Optional[str] = None,
        breach_date: Optional[date] = None,
        breach_start: Optional[datetime] = None,
        breach_end: Optional[datetime] = None,
        phi_description: Optional[str] = None,
        breach_source: Optional[str] = None,
    ) -> BreachIncident:
        """Create a new breach incident."""
        incident_number = f"BR-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"

        # Calculate notification deadlines
        # HHS must be notified within 60 days of discovery
        hhs_deadline = discovered_date + timedelta(days=60)
        # Patients must be notified without unreasonable delay, no later than 60 days
        patient_deadline = discovered_date + timedelta(days=60)

        incident = BreachIncident(
            tenant_id=self.tenant_id,
            incident_number=incident_number,
            discovered_date=discovered_date,
            discovered_by=discovered_by,
            discovery_method=discovery_method,
            breach_type=breach_type,
            description=description,
            breach_date=breach_date,
            breach_start=breach_start,
            breach_end=breach_end,
            status=BreachStatus.SUSPECTED,
            phi_categories_involved=phi_categories_involved,
            phi_description=phi_description,
            breach_source=breach_source,
            hhs_notification_deadline=hhs_deadline,
            patient_notification_deadline=patient_deadline,
        )

        self.db.add(incident)
        await self.db.commit()
        await self.db.refresh(incident)

        return incident

    async def get_incident(self, incident_id: UUID) -> Optional[BreachIncident]:
        """Get breach incident by ID."""
        query = select(BreachIncident).where(
            and_(
                BreachIncident.id == incident_id,
                BreachIncident.tenant_id == self.tenant_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_incident_status(
        self,
        incident_id: UUID,
        status: BreachStatus,
        affected_individuals_count: Optional[int] = None,
        affected_patient_ids: Optional[List[UUID]] = None,
        root_cause: Optional[str] = None,
        containment_actions: Optional[str] = None,
        remediation_actions: Optional[str] = None,
        lessons_learned: Optional[str] = None,
        lead_investigator: Optional[UUID] = None,
    ) -> Optional[BreachIncident]:
        """Update breach incident status and details."""
        incident = await self.get_incident(incident_id)

        if incident:
            incident.status = status
            if affected_individuals_count is not None:
                incident.affected_individuals_count = affected_individuals_count
            if affected_patient_ids is not None:
                incident.affected_patient_ids = affected_patient_ids
            if root_cause:
                incident.root_cause = root_cause
            if containment_actions:
                incident.containment_actions = containment_actions
            if remediation_actions:
                incident.remediation_actions = remediation_actions
            if lessons_learned:
                incident.lessons_learned = lessons_learned
            if lead_investigator:
                incident.lead_investigator = lead_investigator

            incident.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(incident)

        return incident

    async def close_incident(
        self,
        incident_id: UUID,
        closed_by: UUID,
        lessons_learned: Optional[str] = None,
    ) -> Optional[BreachIncident]:
        """Close a breach incident."""
        incident = await self.get_incident(incident_id)

        if incident:
            incident.status = BreachStatus.CLOSED
            incident.closed_at = datetime.utcnow()
            incident.closed_by = closed_by
            if lessons_learned:
                incident.lessons_learned = lessons_learned
            incident.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(incident)

        return incident

    async def list_incidents(
        self,
        status: Optional[BreachStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[BreachIncident]:
        """List breach incidents with filtering."""
        query = select(BreachIncident).where(
            BreachIncident.tenant_id == self.tenant_id
        )

        if status:
            query = query.where(BreachIncident.status == status)
        if start_date:
            query = query.where(BreachIncident.discovered_date >= start_date)
        if end_date:
            query = query.where(BreachIncident.discovered_date <= end_date)

        query = query.order_by(desc(BreachIncident.discovered_date))

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_active_investigations(self) -> List[BreachIncident]:
        """Get all active breach investigations."""
        query = select(BreachIncident).where(
            and_(
                BreachIncident.tenant_id == self.tenant_id,
                BreachIncident.status.in_([
                    BreachStatus.SUSPECTED,
                    BreachStatus.INVESTIGATING,
                    BreachStatus.CONFIRMED,
                    BreachStatus.NOTIFYING,
                ])
            )
        ).order_by(BreachIncident.hhs_notification_deadline)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # =========================================================================
    # Breach Risk Assessment (4-Factor Test)
    # =========================================================================

    async def create_breach_assessment(
        self,
        incident_id: UUID,
        assessed_by: UUID,
        # Factor 1: Nature and extent of PHI
        factor1_phi_nature: str,
        factor1_phi_types: List[str],
        factor1_identifiability: str,
        factor1_score: int,
        # Factor 2: Unauthorized person
        factor2_recipient_description: str,
        factor2_score: int,
        # Factor 3: PHI actually viewed/acquired
        factor3_phi_accessed: str,
        factor3_score: int,
        # Factor 4: Mitigation
        factor4_mitigation_actions: str,
        factor4_score: int,
        # Optional parameters
        factor2_recipient_type: Optional[str] = None,
        factor2_obligation_to_protect: Optional[bool] = None,
        factor3_access_evidence: Optional[str] = None,
        factor4_assurances_obtained: bool = False,
        factor4_phi_returned_destroyed: bool = False,
        low_probability_exception: bool = False,
        exception_justification: Optional[str] = None,
        assessor_name: Optional[str] = None,
    ) -> BreachAssessment:
        """
        Create a 4-factor breach risk assessment.

        The assessment determines if notification is required based on:
        1. Nature and extent of PHI involved
        2. Unauthorized person who used/received PHI
        3. Whether PHI was actually viewed/acquired
        4. Extent to which risk has been mitigated
        """
        # Calculate overall risk score (average or weighted)
        overall_risk_score = (factor1_score + factor2_score + factor3_score + factor4_score) // 4

        # Determine risk level
        if overall_risk_score >= 8:
            risk_level = RiskLevel.CRITICAL
        elif overall_risk_score >= 6:
            risk_level = RiskLevel.HIGH
        elif overall_risk_score >= 4:
            risk_level = RiskLevel.MEDIUM
        elif overall_risk_score >= 2:
            risk_level = RiskLevel.LOW
        else:
            risk_level = RiskLevel.MINIMAL

        # Determine if notification is required
        # Notification required unless low probability of compromise demonstrated
        notification_required = not low_probability_exception and overall_risk_score >= 3

        notification_determination_reason = self._generate_determination_reason(
            overall_risk_score,
            risk_level,
            notification_required,
            low_probability_exception,
            exception_justification,
        )

        assessment = BreachAssessment(
            tenant_id=self.tenant_id,
            incident_id=incident_id,
            assessed_date=datetime.utcnow(),
            assessed_by=assessed_by,
            assessor_name=assessor_name,
            factor1_phi_nature=factor1_phi_nature,
            factor1_phi_types=factor1_phi_types,
            factor1_identifiability=factor1_identifiability,
            factor1_score=factor1_score,
            factor2_recipient_description=factor2_recipient_description,
            factor2_recipient_type=factor2_recipient_type,
            factor2_obligation_to_protect=factor2_obligation_to_protect,
            factor2_score=factor2_score,
            factor3_phi_accessed=factor3_phi_accessed,
            factor3_access_evidence=factor3_access_evidence,
            factor3_score=factor3_score,
            factor4_mitigation_actions=factor4_mitigation_actions,
            factor4_assurances_obtained=factor4_assurances_obtained,
            factor4_phi_returned_destroyed=factor4_phi_returned_destroyed,
            factor4_score=factor4_score,
            overall_risk_score=overall_risk_score,
            risk_level=risk_level,
            notification_required=notification_required,
            notification_determination_reason=notification_determination_reason,
            low_probability_exception=low_probability_exception,
            exception_justification=exception_justification,
        )

        self.db.add(assessment)

        # Update incident status
        incident = await self.get_incident(incident_id)
        if incident:
            if notification_required:
                incident.status = BreachStatus.CONFIRMED
            else:
                incident.status = BreachStatus.NOT_A_BREACH

        await self.db.commit()
        await self.db.refresh(assessment)

        return assessment

    def _generate_determination_reason(
        self,
        score: int,
        risk_level: RiskLevel,
        notification_required: bool,
        low_probability: bool,
        exception_justification: Optional[str],
    ) -> str:
        """Generate explanation for notification determination."""
        if not notification_required and low_probability:
            return (
                f"Based on the 4-factor risk assessment (overall score: {score}/10, "
                f"risk level: {risk_level.value}), this incident qualifies for the "
                f"low probability of compromise exception. {exception_justification or ''}"
            )
        elif notification_required:
            return (
                f"Based on the 4-factor risk assessment (overall score: {score}/10, "
                f"risk level: {risk_level.value}), notification to affected individuals "
                f"and HHS is required within the statutory timeframes."
            )
        else:
            return (
                f"Based on the 4-factor risk assessment (overall score: {score}/10, "
                f"risk level: {risk_level.value}), this incident does not constitute "
                f"a reportable breach under HIPAA."
            )

    async def approve_assessment(
        self,
        assessment_id: UUID,
        reviewed_by: UUID,
        review_comments: Optional[str] = None,
    ) -> Optional[BreachAssessment]:
        """Approve breach assessment."""
        query = select(BreachAssessment).where(
            and_(
                BreachAssessment.id == assessment_id,
                BreachAssessment.tenant_id == self.tenant_id
            )
        )
        result = await self.db.execute(query)
        assessment = result.scalar_one_or_none()

        if assessment:
            assessment.reviewed_by = reviewed_by
            assessment.reviewed_at = datetime.utcnow()
            assessment.review_comments = review_comments
            assessment.approved = True
            assessment.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(assessment)

        return assessment

    async def get_assessment_for_incident(
        self,
        incident_id: UUID,
    ) -> Optional[BreachAssessment]:
        """Get the breach assessment for an incident."""
        query = select(BreachAssessment).where(
            and_(
                BreachAssessment.tenant_id == self.tenant_id,
                BreachAssessment.incident_id == incident_id
            )
        ).order_by(desc(BreachAssessment.assessed_date))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # =========================================================================
    # Breach Notifications
    # =========================================================================

    async def create_notification(
        self,
        incident_id: UUID,
        notification_type: NotificationType,
        recipient_type: str,
        notification_content: str,
        recipient_name: Optional[str] = None,
        recipient_email: Optional[str] = None,
        recipient_address: Optional[str] = None,
        patient_id: Optional[UUID] = None,
        letter_template_used: Optional[str] = None,
        delivery_method: Optional[str] = None,
        scheduled_date: Optional[datetime] = None,
        created_by: Optional[UUID] = None,
    ) -> BreachNotification:
        """Create a breach notification."""
        notification = BreachNotification(
            tenant_id=self.tenant_id,
            incident_id=incident_id,
            notification_type=notification_type,
            recipient_type=recipient_type,
            recipient_name=recipient_name,
            recipient_email=recipient_email,
            recipient_address=recipient_address,
            patient_id=patient_id,
            notification_content=notification_content,
            letter_template_used=letter_template_used,
            delivery_method=delivery_method,
            status=NotificationStatus.DRAFT,
            scheduled_date=scheduled_date,
            created_by=created_by,
        )

        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)

        return notification

    async def send_notification(
        self,
        notification_id: UUID,
        delivery_method: str,
        tracking_number: Optional[str] = None,
    ) -> Optional[BreachNotification]:
        """Mark notification as sent."""
        query = select(BreachNotification).where(
            and_(
                BreachNotification.id == notification_id,
                BreachNotification.tenant_id == self.tenant_id
            )
        )
        result = await self.db.execute(query)
        notification = result.scalar_one_or_none()

        if notification:
            notification.status = NotificationStatus.SENT
            notification.delivery_method = delivery_method
            notification.sent_date = datetime.utcnow()
            notification.tracking_number = tracking_number
            notification.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(notification)

        return notification

    async def mark_notification_delivered(
        self,
        notification_id: UUID,
        delivery_confirmation: Optional[str] = None,
    ) -> Optional[BreachNotification]:
        """Mark notification as delivered."""
        query = select(BreachNotification).where(
            and_(
                BreachNotification.id == notification_id,
                BreachNotification.tenant_id == self.tenant_id
            )
        )
        result = await self.db.execute(query)
        notification = result.scalar_one_or_none()

        if notification:
            notification.status = NotificationStatus.DELIVERED
            notification.delivered_date = datetime.utcnow()
            notification.delivery_confirmation = delivery_confirmation
            notification.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(notification)

        return notification

    async def mark_notification_failed(
        self,
        notification_id: UUID,
        failed_reason: str,
    ) -> Optional[BreachNotification]:
        """Mark notification as failed."""
        query = select(BreachNotification).where(
            and_(
                BreachNotification.id == notification_id,
                BreachNotification.tenant_id == self.tenant_id
            )
        )
        result = await self.db.execute(query)
        notification = result.scalar_one_or_none()

        if notification:
            notification.status = NotificationStatus.FAILED
            notification.failed_reason = failed_reason
            notification.retry_count += 1
            notification.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(notification)

        return notification

    async def get_notifications_for_incident(
        self,
        incident_id: UUID,
    ) -> List[BreachNotification]:
        """Get all notifications for an incident."""
        query = select(BreachNotification).where(
            and_(
                BreachNotification.tenant_id == self.tenant_id,
                BreachNotification.incident_id == incident_id
            )
        ).order_by(BreachNotification.created_at)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def generate_hhs_notification_content(
        self,
        incident: BreachIncident,
        assessment: Optional[BreachAssessment] = None,
    ) -> str:
        """Generate HHS breach notification content."""
        content = f"""
HIPAA BREACH NOTIFICATION TO HHS

Incident Number: {incident.incident_number}
Date of Discovery: {incident.discovered_date.strftime('%Y-%m-%d')}
Date of Breach: {incident.breach_date.strftime('%Y-%m-%d') if incident.breach_date else 'Unknown'}

Number of Individuals Affected: {incident.affected_individuals_count}

Type of Breach: {incident.breach_type.value}

Description of Incident:
{incident.description}

Types of PHI Involved:
{', '.join(incident.phi_categories_involved)}

Brief Description of What Happened:
{incident.description}

Actions Taken in Response:
Containment: {incident.containment_actions or 'In progress'}
Remediation: {incident.remediation_actions or 'In progress'}

Steps Individuals Can Take to Protect Themselves:
[Standard protective measures notification text]

Contact Information:
[Organization contact information]
"""
        return content

    async def generate_patient_notification_content(
        self,
        incident: BreachIncident,
        patient_name: Optional[str] = None,
    ) -> str:
        """Generate patient breach notification letter content."""
        content = f"""
IMPORTANT NOTICE: Privacy Incident Notification

Dear {patient_name or 'Patient'},

We are writing to inform you of a privacy incident that may have involved your protected health information.

What Happened:
{incident.description}

When it Happened:
The incident occurred on or about {incident.breach_date.strftime('%B %d, %Y') if incident.breach_date else 'a recent date'} and was discovered on {incident.discovered_date.strftime('%B %d, %Y')}.

What Information Was Involved:
The types of information that may have been affected include: {', '.join(incident.phi_categories_involved)}.

What We Are Doing:
{incident.containment_actions or 'We have taken immediate steps to contain this incident.'}
{incident.remediation_actions or 'We are implementing additional safeguards to prevent future incidents.'}

What You Can Do:
- Review your medical records and Explanation of Benefits statements for any suspicious activity
- Consider placing a fraud alert or security freeze on your credit files
- Report any suspected identity theft to the Federal Trade Commission

For More Information:
If you have questions or would like additional information, please contact our Privacy Officer at [contact information].

We sincerely apologize for any concern or inconvenience this may cause you.

Sincerely,
[Organization Name]
Privacy Officer
"""
        return content

    async def check_media_notification_required(
        self,
        incident_id: UUID,
    ) -> bool:
        """Check if media notification is required (>500 individuals in a state)."""
        incident = await self.get_incident(incident_id)
        # HIPAA requires media notification if >500 individuals in a state
        return incident is not None and incident.affected_individuals_count > 500

    # =========================================================================
    # Breach Reporting and Dashboard
    # =========================================================================

    async def get_breach_statistics(self) -> Dict[str, Any]:
        """Get breach statistics for dashboard."""
        # Total breaches by status
        status_query = (
            select(BreachIncident.status, func.count(BreachIncident.id))
            .where(BreachIncident.tenant_id == self.tenant_id)
            .group_by(BreachIncident.status)
        )
        status_result = await self.db.execute(status_query)
        by_status = {row[0].value: row[1] for row in status_result.all()}

        # Active investigations count
        active_query = select(func.count()).select_from(BreachIncident).where(
            and_(
                BreachIncident.tenant_id == self.tenant_id,
                BreachIncident.status.in_([
                    BreachStatus.SUSPECTED,
                    BreachStatus.INVESTIGATING,
                    BreachStatus.CONFIRMED,
                    BreachStatus.NOTIFYING,
                ])
            )
        )
        active_result = await self.db.execute(active_query)
        active_count = active_result.scalar()

        # Upcoming deadlines
        deadline_query = select(BreachIncident).where(
            and_(
                BreachIncident.tenant_id == self.tenant_id,
                BreachIncident.status.in_([
                    BreachStatus.CONFIRMED,
                    BreachStatus.NOTIFYING,
                ]),
                BreachIncident.hhs_notification_deadline > datetime.utcnow(),
                BreachIncident.hhs_notification_deadline <= datetime.utcnow() + timedelta(days=14)
            )
        ).order_by(BreachIncident.hhs_notification_deadline)

        deadline_result = await self.db.execute(deadline_query)
        upcoming_deadlines = [
            {
                "incident_number": inc.incident_number,
                "deadline": inc.hhs_notification_deadline.isoformat(),
                "days_remaining": (inc.hhs_notification_deadline - datetime.utcnow()).days,
            }
            for inc in deadline_result.scalars().all()
        ]

        return {
            "active_investigations": active_count,
            "by_status": by_status,
            "upcoming_deadlines": upcoming_deadlines,
        }

    async def generate_annual_breach_report(
        self,
        year: int,
    ) -> Dict[str, Any]:
        """Generate annual breach report for regulatory compliance."""
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31, 23, 59, 59)

        # Get all incidents for the year
        query = select(BreachIncident).where(
            and_(
                BreachIncident.tenant_id == self.tenant_id,
                BreachIncident.discovered_date >= start_date,
                BreachIncident.discovered_date <= end_date
            )
        )
        result = await self.db.execute(query)
        incidents = list(result.scalars().all())

        # Calculate statistics
        total_incidents = len(incidents)
        confirmed_breaches = sum(1 for i in incidents if i.status != BreachStatus.NOT_A_BREACH)
        total_affected = sum(i.affected_individuals_count for i in incidents)

        by_type = {}
        for incident in incidents:
            breach_type = incident.breach_type.value
            by_type[breach_type] = by_type.get(breach_type, 0) + 1

        return {
            "year": year,
            "total_incidents_reported": total_incidents,
            "confirmed_breaches": confirmed_breaches,
            "not_a_breach": total_incidents - confirmed_breaches,
            "total_individuals_affected": total_affected,
            "incidents_by_type": by_type,
            "incidents": [
                {
                    "incident_number": i.incident_number,
                    "discovered_date": i.discovered_date.isoformat(),
                    "breach_type": i.breach_type.value,
                    "status": i.status.value,
                    "affected_count": i.affected_individuals_count,
                }
                for i in incidents
            ],
        }
