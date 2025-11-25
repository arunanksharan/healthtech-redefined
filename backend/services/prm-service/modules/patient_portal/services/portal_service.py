"""
Patient Portal Service
EPIC-014: Core patient portal operations including profile, health records, messaging
"""
from datetime import datetime, date, timedelta, timezone
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
import secrets

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, desc
from sqlalchemy.orm import selectinload, joinedload

from modules.patient_portal.models import (
    PortalUser, PortalPreference, PortalAuditLog, PortalNotification,
    MessageThread, SecureMessage, MessageAttachmentPortal,
    ProxyAccess, RecordAccessLog, RecordShareLink,
    AuditAction, MessageStatus, MessagePriority, MessageFolder,
    ProxyRelationship, ProxyAccessLevel
)
from modules.patient_portal.schemas import (
    PatientProfileResponse, PatientProfileUpdateRequest,
    PortalPreferencesResponse, PortalPreferencesUpdate,
    HealthRecordResponse, LabResultResponse, HealthSummaryResponse,
    RecordFilter, RecordDownloadRequest, RecordShareRequest, RecordShareResponse,
    MessageThreadCreate, MessageThreadResponse, MessageCreate, MessageResponse,
    MessageListResponse, MessageSearchRequest,
    NotificationResponse, NotificationListResponse,
    ProxyAccessRequest, ProxyAccessResponse, ProxyPatientSummary,
    EmergencyContact, HealthMetrics, AccessibilitySettings, NotificationSettings,
    PrivacySettings, CommunicationPreferences
)


class PatientPortalService:
    """
    Main service for patient portal operations including:
    - Patient profile management
    - Health records access
    - Secure messaging
    - Notifications
    - Proxy access management
    """

    def __init__(self):
        self.message_response_sla_hours = 48  # 48 hour SLA for message responses

    # ==================== Profile Management ====================

    async def get_patient_profile(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        patient_id: UUID = None,
        ip_address: str = None
    ) -> PatientProfileResponse:
        """Get complete patient profile"""
        from modules.fhir.models import Patient  # Import here to avoid circular imports

        # If patient_id provided, check proxy access
        if patient_id:
            await self._verify_proxy_access(db, user_id, patient_id, "view_records")
            target_patient_id = patient_id
        else:
            # Get user's own patient ID
            result = await db.execute(
                select(PortalUser.patient_id).where(PortalUser.id == user_id)
            )
            target_patient_id = result.scalar_one()

        # Get patient data
        result = await db.execute(
            select(Patient).where(
                and_(
                    Patient.id == target_patient_id,
                    Patient.tenant_id == tenant_id
                )
            )
        )
        patient = result.scalar_one_or_none()

        if not patient:
            raise ValueError("Patient not found")

        # Get aggregated stats
        stats = await self._get_patient_stats(db, target_patient_id)

        # Log access
        await self._log_record_access(
            db, tenant_id, user_id, target_patient_id,
            "profile", "view", ip_address
        )

        return PatientProfileResponse(
            id=patient.id,
            mrn=patient.mrn,
            first_name=patient.first_name,
            last_name=patient.last_name,
            middle_name=getattr(patient, 'middle_name', None),
            date_of_birth=patient.date_of_birth,
            gender=patient.gender,
            email=patient.email,
            phone=patient.phone,
            address=patient.address if hasattr(patient, 'address') else None,
            emergency_contacts=patient.emergency_contacts if hasattr(patient, 'emergency_contacts') else None,
            insurance_info=patient.insurance_info if hasattr(patient, 'insurance_info') else None,
            preferred_language=patient.preferred_language if hasattr(patient, 'preferred_language') else None,
            photo_url=patient.photo_url if hasattr(patient, 'photo_url') else None,
            total_appointments=stats.get('total_appointments', 0),
            active_medications=stats.get('active_medications', 0),
            active_allergies=stats.get('active_allergies', 0),
            last_visit_date=stats.get('last_visit_date')
        )

    async def _get_patient_stats(self, db: AsyncSession, patient_id: UUID) -> Dict:
        """Get aggregated patient statistics"""
        # This would query various tables for stats
        return {
            'total_appointments': 0,
            'active_medications': 0,
            'active_allergies': 0,
            'last_visit_date': None
        }

    async def update_patient_profile(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        updates: PatientProfileUpdateRequest,
        ip_address: str = None
    ) -> PatientProfileResponse:
        """Update patient profile (limited fields)"""
        from modules.fhir.models import Patient

        result = await db.execute(
            select(PortalUser).where(PortalUser.id == user_id)
        )
        user = result.scalar_one()

        # Update patient record
        update_data = {}
        if updates.phone:
            update_data['phone'] = updates.phone
        if updates.email:
            update_data['email'] = updates.email
        if updates.address:
            update_data['address'] = updates.address
        if updates.emergency_contacts:
            update_data['emergency_contacts'] = [c.model_dump() for c in updates.emergency_contacts]
        if updates.preferred_language:
            update_data['preferred_language'] = updates.preferred_language

        if update_data:
            await db.execute(
                update(Patient).where(
                    Patient.id == user.patient_id
                ).values(**update_data, updated_at=datetime.now(timezone.utc))
            )

            # Log update
            audit_log = PortalAuditLog(
                id=uuid4(),
                tenant_id=tenant_id,
                user_id=user_id,
                patient_id=user.patient_id,
                action=AuditAction.PROFILE_UPDATE,
                action_category="profile",
                action_description="Patient profile updated",
                details={"fields_updated": list(update_data.keys())},
                ip_address=ip_address,
                success=True
            )
            db.add(audit_log)
            await db.commit()

        return await self.get_patient_profile(db, user_id, tenant_id)

    # ==================== Preferences ====================

    async def get_preferences(
        self,
        db: AsyncSession,
        user_id: UUID
    ) -> PortalPreferencesResponse:
        """Get user preferences"""
        result = await db.execute(
            select(PortalPreference).where(PortalPreference.user_id == user_id)
        )
        prefs = result.scalar_one_or_none()

        if not prefs:
            raise ValueError("Preferences not found")

        return PortalPreferencesResponse(
            language=prefs.language,
            timezone=prefs.timezone,
            date_format=prefs.date_format,
            time_format=prefs.time_format,
            theme=prefs.theme,
            accessibility_settings=AccessibilitySettings(**(prefs.accessibility_settings or {})),
            notification_settings=NotificationSettings(**(prefs.notification_settings or {})),
            dashboard_layout=prefs.dashboard_layout or {},
            privacy_settings=PrivacySettings(**(prefs.privacy_settings or {})),
            communication_preferences=CommunicationPreferences(**(prefs.communication_preferences or {})),
            favorite_actions=prefs.favorite_actions or [],
            onboarding_completed=prefs.onboarding_completed,
            tour_completed=prefs.tour_completed
        )

    async def update_preferences(
        self,
        db: AsyncSession,
        user_id: UUID,
        updates: PortalPreferencesUpdate
    ) -> PortalPreferencesResponse:
        """Update user preferences"""
        result = await db.execute(
            select(PortalPreference).where(PortalPreference.user_id == user_id)
        )
        prefs = result.scalar_one_or_none()

        if not prefs:
            raise ValueError("Preferences not found")

        # Update fields
        if updates.language:
            prefs.language = updates.language
        if updates.timezone:
            prefs.timezone = updates.timezone
        if updates.date_format:
            prefs.date_format = updates.date_format
        if updates.time_format:
            prefs.time_format = updates.time_format
        if updates.theme:
            prefs.theme = updates.theme
        if updates.accessibility_settings:
            prefs.accessibility_settings = updates.accessibility_settings.model_dump()
        if updates.notification_settings:
            prefs.notification_settings = updates.notification_settings.model_dump()
        if updates.dashboard_layout:
            prefs.dashboard_layout = updates.dashboard_layout
        if updates.privacy_settings:
            prefs.privacy_settings = updates.privacy_settings.model_dump()
        if updates.communication_preferences:
            prefs.communication_preferences = updates.communication_preferences.model_dump()
        if updates.favorite_actions is not None:
            prefs.favorite_actions = updates.favorite_actions

        await db.commit()
        return await self.get_preferences(db, user_id)

    # ==================== Health Records ====================

    async def get_health_records(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        patient_id: UUID = None,
        filters: RecordFilter = None,
        page: int = 1,
        page_size: int = 20,
        ip_address: str = None
    ) -> Tuple[List[HealthRecordResponse], int]:
        """Get patient health records with filtering"""

        target_patient_id = await self._get_target_patient_id(db, user_id, patient_id)

        # Build query - this would query actual health record tables
        # For now, returning placeholder structure
        records = []
        total = 0

        # Log access
        await self._log_record_access(
            db, tenant_id, user_id, target_patient_id,
            "health_records", "view", ip_address,
            record_type=filters.record_type if filters else None
        )

        return records, total

    async def get_lab_results(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        patient_id: UUID = None,
        test_type: str = None,
        date_from: date = None,
        date_to: date = None,
        ip_address: str = None
    ) -> List[LabResultResponse]:
        """Get lab results with trending"""

        target_patient_id = await self._get_target_patient_id(db, user_id, patient_id)

        # Query lab results - would integrate with FHIR Observation resources
        results = []

        await self._log_record_access(
            db, tenant_id, user_id, target_patient_id,
            "lab_results", "view", ip_address
        )

        return results

    async def get_health_summary(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        patient_id: UUID = None,
        ip_address: str = None
    ) -> HealthSummaryResponse:
        """Get patient health summary including vitals, allergies, conditions, medications"""

        target_patient_id = await self._get_target_patient_id(db, user_id, patient_id)

        # Would query FHIR resources for comprehensive summary
        return HealthSummaryResponse(
            patient_id=target_patient_id,
            metrics=HealthMetrics(),
            allergies=[],
            conditions=[],
            medications=[],
            immunizations=[],
            care_gaps=[],
            preventive_care_due=[]
        )

    async def share_records(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        request: RecordShareRequest,
        ip_address: str = None
    ) -> RecordShareResponse:
        """Create shareable link for health records"""

        result = await db.execute(
            select(PortalUser).where(PortalUser.id == user_id)
        )
        user = result.scalar_one()

        # Generate secure share token
        token = secrets.token_urlsafe(32)
        password = secrets.token_urlsafe(8) if request.password_protected else None
        password_hash = None
        if password:
            from modules.patient_portal.services.auth_service import AuthService
            auth_service = AuthService()
            password_hash, _ = auth_service.hash_password(password)

        share_link = RecordShareLink(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            patient_id=user.patient_id,
            token=token,
            share_url=f"/portal/shared/{token}",  # Would be full URL in production
            record_type=request.record_type,
            record_ids=request.record_ids,
            include_attachments=request.include_attachments,
            recipient_name=request.recipient_name,
            recipient_email=request.recipient_email,
            recipient_organization=request.recipient_organization,
            purpose=request.purpose,
            password_protected=request.password_protected,
            password_hash=password_hash,
            max_access_count=request.max_access_count,
            expires_at=datetime.now(timezone.utc) + timedelta(days=request.expires_in_days)
        )
        db.add(share_link)

        # Log sharing action
        audit_log = PortalAuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            patient_id=user.patient_id,
            action=AuditAction.RECORDS_SHARED,
            action_category="records",
            action_description=f"Records shared with {request.recipient_name}",
            details={
                "recipient_email": request.recipient_email,
                "record_type": request.record_type,
                "expires_in_days": request.expires_in_days
            },
            ip_address=ip_address,
            success=True,
            contains_phi=True
        )
        db.add(audit_log)

        await db.commit()

        # Send notification email
        await self._send_share_notification(
            request.recipient_email,
            request.recipient_name,
            share_link.share_url,
            share_link.expires_at
        )

        return RecordShareResponse(
            share_id=share_link.id,
            share_url=share_link.share_url,
            expires_at=share_link.expires_at,
            password=password,
            notification_sent=True
        )

    async def _send_share_notification(
        self,
        email: str,
        name: str,
        url: str,
        expires_at: datetime
    ):
        """Send record share notification email"""
        # Integrate with email service
        print(f"Sending share notification to {email}")

    # ==================== Secure Messaging ====================

    async def create_message_thread(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        request: MessageThreadCreate,
        ip_address: str = None
    ) -> MessageThreadResponse:
        """Create new message thread with provider"""

        result = await db.execute(
            select(PortalUser).where(PortalUser.id == user_id)
        )
        user = result.scalar_one()

        # Create thread
        thread = MessageThread(
            id=uuid4(),
            tenant_id=tenant_id,
            patient_id=user.patient_id,
            subject=request.subject,
            category=request.category,
            provider_id=request.recipient_id,
            is_urgent=request.is_urgent,
            related_appointment_id=request.related_appointment_id,
            response_due_at=datetime.now(timezone.utc) + timedelta(hours=self.message_response_sla_hours),
            first_message_at=datetime.now(timezone.utc),
            last_message_at=datetime.now(timezone.utc),
            last_patient_message_at=datetime.now(timezone.utc)
        )
        db.add(thread)

        # Create initial message
        message = SecureMessage(
            id=uuid4(),
            tenant_id=tenant_id,
            thread_id=thread.id,
            sender_id=user_id,
            sender_type="patient",
            sender_name=user.display_name,
            recipient_id=request.recipient_id,
            recipient_type="provider",
            content=request.initial_message,
            status=MessageStatus.SENT,
            priority=MessagePriority.URGENT if request.is_urgent else MessagePriority.NORMAL,
            sent_at=datetime.now(timezone.utc)
        )
        db.add(message)

        # Update thread counts
        thread.message_count = 1
        thread.unread_provider_count = 1

        # Log message sent
        audit_log = PortalAuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            patient_id=user.patient_id,
            action=AuditAction.MESSAGE_SENT,
            action_category="messaging",
            action_description=f"Message thread created: {request.subject}",
            ip_address=ip_address,
            success=True,
            contains_phi=True
        )
        db.add(audit_log)

        await db.commit()

        return MessageThreadResponse(
            id=thread.id,
            subject=thread.subject,
            category=thread.category,
            provider_id=thread.provider_id,
            provider_name=thread.provider_name,
            department=thread.department,
            is_open=thread.is_open,
            is_urgent=thread.is_urgent,
            message_count=thread.message_count,
            unread_count=thread.unread_patient_count,
            last_message_at=thread.last_message_at,
            response_due_at=thread.response_due_at,
            created_at=thread.created_at,
            updated_at=thread.updated_at
        )

    async def reply_to_thread(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        thread_id: UUID,
        request: MessageCreate,
        ip_address: str = None
    ) -> MessageResponse:
        """Reply to existing message thread"""

        result = await db.execute(
            select(PortalUser).where(PortalUser.id == user_id)
        )
        user = result.scalar_one()

        # Get thread
        result = await db.execute(
            select(MessageThread).where(
                and_(
                    MessageThread.id == thread_id,
                    MessageThread.patient_id == user.patient_id
                )
            )
        )
        thread = result.scalar_one_or_none()

        if not thread:
            raise ValueError("Thread not found")

        if not thread.is_open:
            raise ValueError("This conversation has been closed")

        # Create reply message
        message = SecureMessage(
            id=uuid4(),
            tenant_id=tenant_id,
            thread_id=thread_id,
            sender_id=user_id,
            sender_type="patient",
            sender_name=user.display_name,
            recipient_id=thread.provider_id,
            recipient_type="provider",
            content=request.content,
            status=MessageStatus.SENT,
            priority=request.priority,
            sent_at=datetime.now(timezone.utc)
        )
        db.add(message)

        # Update thread
        thread.message_count += 1
        thread.unread_provider_count += 1
        thread.last_message_at = datetime.now(timezone.utc)
        thread.last_patient_message_at = datetime.now(timezone.utc)

        await db.commit()

        return MessageResponse(
            id=message.id,
            thread_id=thread_id,
            sender_type=message.sender_type,
            sender_name=message.sender_name,
            content=message.content,
            has_attachments=message.has_attachments,
            attachment_count=message.attachment_count,
            priority=message.priority,
            status=message.status.value,
            sent_at=message.sent_at,
            read_at=message.read_at,
            is_auto_response=message.is_auto_response,
            created_at=message.created_at,
            updated_at=message.updated_at
        )

    async def get_message_threads(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        folder: MessageFolder = None,
        is_unread: bool = None,
        page: int = 1,
        page_size: int = 20
    ) -> MessageListResponse:
        """Get message threads for user"""

        result = await db.execute(
            select(PortalUser).where(PortalUser.id == user_id)
        )
        user = result.scalar_one()

        # Build query
        query = select(MessageThread).where(
            and_(
                MessageThread.patient_id == user.patient_id,
                MessageThread.tenant_id == tenant_id
            )
        )

        if is_unread:
            query = query.where(MessageThread.unread_patient_count > 0)

        # Get total unread count
        unread_result = await db.execute(
            select(func.sum(MessageThread.unread_patient_count)).where(
                and_(
                    MessageThread.patient_id == user.patient_id,
                    MessageThread.tenant_id == tenant_id
                )
            )
        )
        total_unread = unread_result.scalar() or 0

        # Get total count
        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total_count = count_result.scalar()

        # Get paginated results
        query = query.order_by(desc(MessageThread.last_message_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        threads = result.scalars().all()

        return MessageListResponse(
            threads=[
                MessageThreadResponse(
                    id=t.id,
                    subject=t.subject,
                    category=t.category,
                    provider_id=t.provider_id,
                    provider_name=t.provider_name,
                    department=t.department,
                    is_open=t.is_open,
                    is_urgent=t.is_urgent,
                    message_count=t.message_count,
                    unread_count=t.unread_patient_count,
                    last_message_at=t.last_message_at,
                    response_due_at=t.response_due_at,
                    resolved_at=t.resolved_at,
                    created_at=t.created_at,
                    updated_at=t.updated_at
                )
                for t in threads
            ],
            total_count=total_count,
            unread_count=total_unread
        )

    async def get_thread_messages(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        thread_id: UUID,
        ip_address: str = None
    ) -> List[MessageResponse]:
        """Get all messages in a thread"""

        result = await db.execute(
            select(PortalUser).where(PortalUser.id == user_id)
        )
        user = result.scalar_one()

        # Verify access
        result = await db.execute(
            select(MessageThread).where(
                and_(
                    MessageThread.id == thread_id,
                    MessageThread.patient_id == user.patient_id
                )
            )
        )
        thread = result.scalar_one_or_none()

        if not thread:
            raise ValueError("Thread not found")

        # Get messages
        result = await db.execute(
            select(SecureMessage).where(
                SecureMessage.thread_id == thread_id
            ).order_by(SecureMessage.created_at)
        )
        messages = result.scalars().all()

        # Mark provider messages as read
        unread_ids = [
            m.id for m in messages
            if m.sender_type == "provider" and not m.read_at
        ]

        if unread_ids:
            await db.execute(
                update(SecureMessage).where(
                    SecureMessage.id.in_(unread_ids)
                ).values(
                    read_at=datetime.now(timezone.utc),
                    status=MessageStatus.READ
                )
            )
            thread.unread_patient_count = 0
            await db.commit()

        return [
            MessageResponse(
                id=m.id,
                thread_id=m.thread_id,
                sender_type=m.sender_type,
                sender_name=m.sender_name,
                content=m.content,
                has_attachments=m.has_attachments,
                attachment_count=m.attachment_count,
                priority=m.priority,
                status=m.status.value,
                sent_at=m.sent_at,
                read_at=m.read_at,
                is_auto_response=m.is_auto_response,
                created_at=m.created_at,
                updated_at=m.updated_at
            )
            for m in messages
        ]

    # ==================== Notifications ====================

    async def get_notifications(
        self,
        db: AsyncSession,
        user_id: UUID,
        is_read: bool = None,
        page: int = 1,
        page_size: int = 20
    ) -> NotificationListResponse:
        """Get user notifications"""

        query = select(PortalNotification).where(
            PortalNotification.user_id == user_id
        )

        if is_read is not None:
            query = query.where(PortalNotification.is_read == is_read)

        # Get unread count
        unread_result = await db.execute(
            select(func.count()).where(
                and_(
                    PortalNotification.user_id == user_id,
                    PortalNotification.is_read == False
                )
            )
        )
        unread_count = unread_result.scalar()

        # Get total count
        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total_count = count_result.scalar()

        # Get paginated results
        query = query.order_by(desc(PortalNotification.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        notifications = result.scalars().all()

        return NotificationListResponse(
            notifications=[
                NotificationResponse(
                    id=n.id,
                    notification_type=n.notification_type,
                    title=n.title,
                    message=n.message,
                    icon=n.icon,
                    action_url=n.action_url,
                    action_text=n.action_text,
                    priority=n.priority,
                    is_urgent=n.is_urgent,
                    is_read=n.is_read,
                    read_at=n.read_at,
                    reference_type=n.reference_type,
                    reference_id=n.reference_id,
                    created_at=n.created_at
                )
                for n in notifications
            ],
            total_count=total_count,
            unread_count=unread_count
        )

    async def mark_notifications_read(
        self,
        db: AsyncSession,
        user_id: UUID,
        notification_ids: List[UUID] = None,
        mark_all: bool = False
    ):
        """Mark notifications as read"""

        if mark_all:
            await db.execute(
                update(PortalNotification).where(
                    and_(
                        PortalNotification.user_id == user_id,
                        PortalNotification.is_read == False
                    )
                ).values(
                    is_read=True,
                    read_at=datetime.now(timezone.utc)
                )
            )
        elif notification_ids:
            await db.execute(
                update(PortalNotification).where(
                    and_(
                        PortalNotification.user_id == user_id,
                        PortalNotification.id.in_(notification_ids)
                    )
                ).values(
                    is_read=True,
                    read_at=datetime.now(timezone.utc)
                )
            )

        await db.commit()

    async def create_notification(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        notification_type: str,
        title: str,
        message: str,
        action_url: str = None,
        priority: str = "normal",
        reference_type: str = None,
        reference_id: UUID = None
    ) -> UUID:
        """Create notification for user"""

        notification = PortalNotification(
            id=uuid4(),
            user_id=user_id,
            tenant_id=tenant_id,
            notification_type=notification_type,
            title=title,
            message=message,
            action_url=action_url,
            priority=priority,
            reference_type=reference_type,
            reference_id=reference_id
        )
        db.add(notification)
        await db.commit()

        return notification.id

    # ==================== Proxy Access ====================

    async def get_proxy_accounts(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID
    ) -> List[ProxyPatientSummary]:
        """Get list of patients user has proxy access to"""

        from modules.fhir.models import Patient

        result = await db.execute(
            select(ProxyAccess).where(
                and_(
                    ProxyAccess.grantee_id == user_id,
                    ProxyAccess.tenant_id == tenant_id,
                    ProxyAccess.is_active == True,
                    or_(
                        ProxyAccess.valid_until == None,
                        ProxyAccess.valid_until > datetime.now(timezone.utc)
                    )
                )
            )
        )
        proxies = result.scalars().all()

        summaries = []
        for proxy in proxies:
            # Get patient info
            result = await db.execute(
                select(Patient).where(Patient.id == proxy.grantor_id)
            )
            patient = result.scalar_one_or_none()

            if patient:
                summaries.append(ProxyPatientSummary(
                    patient_id=patient.id,
                    first_name=patient.first_name,
                    last_name=patient.last_name,
                    date_of_birth=patient.date_of_birth,
                    relationship=proxy.relationship_type,
                    access_level=proxy.access_level,
                    photo_url=getattr(patient, 'photo_url', None),
                    upcoming_appointments=0,  # Would query actual counts
                    unread_messages=0,
                    pending_refills=0
                ))

        return summaries

    async def grant_proxy_access(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        request: ProxyAccessRequest,
        ip_address: str = None
    ) -> ProxyAccessResponse:
        """Grant proxy access to another user"""

        result = await db.execute(
            select(PortalUser).where(PortalUser.id == user_id)
        )
        grantor_user = result.scalar_one()

        # Find grantee by email
        result = await db.execute(
            select(PortalUser).where(
                and_(
                    PortalUser.email == request.grantee_email.lower(),
                    PortalUser.tenant_id == tenant_id
                )
            )
        )
        grantee_user = result.scalar_one_or_none()

        if not grantee_user:
            raise ValueError("User with this email not found")

        # Check existing proxy
        result = await db.execute(
            select(ProxyAccess).where(
                and_(
                    ProxyAccess.grantor_id == grantor_user.patient_id,
                    ProxyAccess.grantee_id == grantee_user.id
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing and existing.is_active:
            raise ValueError("Proxy access already exists for this user")

        # Create proxy access
        proxy = ProxyAccess(
            id=uuid4(),
            tenant_id=tenant_id,
            grantor_id=grantor_user.patient_id,
            grantee_id=grantee_user.id,
            relationship_type=request.relationship_type,
            relationship_description=request.relationship_description,
            access_level=request.access_level,
            custom_permissions=request.custom_permissions,
            can_view_records=request.can_view_records,
            can_download_records=request.can_download_records,
            can_book_appointments=request.can_book_appointments,
            can_send_messages=request.can_send_messages,
            can_view_billing=request.can_view_billing,
            can_make_payments=request.can_make_payments,
            can_request_refills=request.can_request_refills,
            valid_until=datetime.combine(request.valid_until, datetime.min.time()) if request.valid_until else None,
            is_permanent=request.is_permanent,
            created_by=user_id
        )
        db.add(proxy)

        # Log action
        audit_log = PortalAuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            patient_id=grantor_user.patient_id,
            action=AuditAction.PROXY_ACCESS_GRANTED,
            action_category="proxy",
            action_description=f"Proxy access granted to {request.grantee_email}",
            details={
                "grantee_email": request.grantee_email,
                "relationship": request.relationship_type.value,
                "access_level": request.access_level.value
            },
            ip_address=ip_address,
            success=True
        )
        db.add(audit_log)

        await db.commit()

        return ProxyAccessResponse(
            id=proxy.id,
            grantor_name=grantor_user.display_name,
            grantee_name=grantee_user.display_name,
            relationship_type=proxy.relationship_type,
            access_level=proxy.access_level,
            can_view_records=proxy.can_view_records,
            can_download_records=proxy.can_download_records,
            can_book_appointments=proxy.can_book_appointments,
            can_send_messages=proxy.can_send_messages,
            can_view_billing=proxy.can_view_billing,
            can_make_payments=proxy.can_make_payments,
            can_request_refills=proxy.can_request_refills,
            is_active=proxy.is_active,
            verified=proxy.verified,
            valid_from=proxy.valid_from,
            valid_until=proxy.valid_until,
            is_permanent=proxy.is_permanent,
            created_at=proxy.created_at,
            updated_at=proxy.updated_at
        )

    async def revoke_proxy_access(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        proxy_id: UUID,
        reason: str = None,
        ip_address: str = None
    ):
        """Revoke proxy access"""

        result = await db.execute(
            select(PortalUser).where(PortalUser.id == user_id)
        )
        user = result.scalar_one()

        result = await db.execute(
            select(ProxyAccess).where(
                and_(
                    ProxyAccess.id == proxy_id,
                    ProxyAccess.grantor_id == user.patient_id
                )
            )
        )
        proxy = result.scalar_one_or_none()

        if not proxy:
            raise ValueError("Proxy access not found")

        proxy.is_active = False
        proxy.revoked_at = datetime.now(timezone.utc)
        proxy.revoked_by = user_id
        proxy.revocation_reason = reason

        # Log action
        audit_log = PortalAuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            patient_id=user.patient_id,
            action=AuditAction.PROXY_ACCESS_REVOKED,
            action_category="proxy",
            action_description="Proxy access revoked",
            details={"reason": reason},
            ip_address=ip_address,
            success=True
        )
        db.add(audit_log)

        await db.commit()

    # ==================== Helper Methods ====================

    async def _get_target_patient_id(
        self,
        db: AsyncSession,
        user_id: UUID,
        patient_id: UUID = None
    ) -> UUID:
        """Get target patient ID, verifying proxy access if needed"""

        if patient_id:
            await self._verify_proxy_access(db, user_id, patient_id, "view_records")
            return patient_id

        result = await db.execute(
            select(PortalUser.patient_id).where(PortalUser.id == user_id)
        )
        return result.scalar_one()

    async def _verify_proxy_access(
        self,
        db: AsyncSession,
        user_id: UUID,
        patient_id: UUID,
        permission: str
    ):
        """Verify user has proxy access to patient"""

        result = await db.execute(
            select(ProxyAccess).where(
                and_(
                    ProxyAccess.grantee_id == user_id,
                    ProxyAccess.grantor_id == patient_id,
                    ProxyAccess.is_active == True
                )
            )
        )
        proxy = result.scalar_one_or_none()

        if not proxy:
            raise ValueError("You do not have access to this patient's records")

        # Check validity
        if proxy.valid_until and proxy.valid_until < datetime.now(timezone.utc):
            raise ValueError("Proxy access has expired")

        # Check specific permission
        permission_map = {
            "view_records": proxy.can_view_records,
            "download_records": proxy.can_download_records,
            "share_records": proxy.can_share_records,
            "book_appointments": proxy.can_book_appointments,
            "send_messages": proxy.can_send_messages,
            "view_billing": proxy.can_view_billing,
            "make_payments": proxy.can_make_payments,
            "request_refills": proxy.can_request_refills
        }

        if not permission_map.get(permission, False):
            raise ValueError(f"You do not have permission to {permission.replace('_', ' ')}")

    async def _log_record_access(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        patient_id: UUID,
        record_type: str,
        action: str,
        ip_address: str = None,
        **kwargs
    ):
        """Log health record access"""

        log = RecordAccessLog(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            patient_id=patient_id,
            record_type=record_type,
            action=action,
            ip_address=ip_address
        )
        db.add(log)
        await db.commit()
