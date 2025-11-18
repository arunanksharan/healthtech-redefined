"""
Notification Service
Multi-channel notification and template management
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from loguru import logger
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID, uuid4
from datetime import datetime
from string import Template

from shared.database.models import MessageTemplate, OutboundNotification
from shared.events.publisher import publish_event
from shared.events.schemas import EventType

from core.twilio_client import twilio_client
from modules.notifications.schemas import (
    MessageTemplateCreate,
    MessageTemplateUpdate,
    MessageTemplateResponse,
    NotificationSend,
    NotificationSendWithTemplate,
    NotificationResponse,
    BulkNotificationSend,
    BulkNotificationResult,
    TemplateListFilters,
    NotificationListFilters,
    NotificationStatistics,
    TemplateRenderRequest,
    TemplateRenderResponse,
    NotificationChannel,
    NotificationStatus,
    NotificationPriority
)


class NotificationService:
    """Service for notification and template management"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== Template Management ====================

    async def create_template(
        self,
        template_data: MessageTemplateCreate,
        org_id: Optional[UUID] = None
    ) -> MessageTemplate:
        """
        Create message template

        Templates support variable substitution using {variable_name} syntax
        """
        try:
            # Check if template with same name already exists
            existing = self.db.query(MessageTemplate).filter(
                and_(
                    MessageTemplate.name == template_data.name,
                    MessageTemplate.channel == template_data.channel.value
                )
            ).first()

            if existing:
                raise ValueError(
                    f"Template '{template_data.name}' already exists for channel {template_data.channel.value}"
                )

            # Create template
            template = MessageTemplate(
                id=uuid4(),
                org_id=org_id,
                name=template_data.name,
                channel=template_data.channel.value,
                category=template_data.category.value,
                subject=template_data.subject,
                body=template_data.body,
                description=template_data.description,
                variables_json=template_data.variables,
                is_active=template_data.is_active,
                total_sent=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.db.add(template)
            self.db.commit()
            self.db.refresh(template)

            logger.info(f"Created template: {template.name} ({template.channel})")

            return template

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error creating template: {e}", exc_info=True)
            self.db.rollback()
            raise

    async def get_template(
        self,
        template_id: UUID
    ) -> Optional[MessageTemplate]:
        """Get template by ID"""
        return self.db.query(MessageTemplate).filter(
            MessageTemplate.id == template_id
        ).first()

    async def get_template_by_name(
        self,
        name: str,
        channel: NotificationChannel
    ) -> Optional[MessageTemplate]:
        """Get template by name and channel"""
        return self.db.query(MessageTemplate).filter(
            and_(
                MessageTemplate.name == name,
                MessageTemplate.channel == channel.value
            )
        ).first()

    async def list_templates(
        self,
        filters: TemplateListFilters
    ) -> List[MessageTemplate]:
        """List templates with filters"""
        query = self.db.query(MessageTemplate)

        # Apply filters
        if filters.channel:
            query = query.filter(MessageTemplate.channel == filters.channel.value)

        if filters.category:
            query = query.filter(MessageTemplate.category == filters.category.value)

        if filters.is_active is not None:
            query = query.filter(MessageTemplate.is_active == filters.is_active)

        if filters.search_query:
            search_term = f"%{filters.search_query}%"
            query = query.filter(
                or_(
                    MessageTemplate.name.ilike(search_term),
                    MessageTemplate.description.ilike(search_term)
                )
            )

        # Order by most recently updated
        query = query.order_by(MessageTemplate.updated_at.desc())

        # Pagination
        query = query.offset(filters.offset).limit(filters.limit)

        return query.all()

    async def update_template(
        self,
        template_id: UUID,
        update_data: MessageTemplateUpdate
    ) -> Optional[MessageTemplate]:
        """Update template"""
        template = await self.get_template(template_id)

        if not template:
            return None

        # Update fields
        update_dict = update_data.dict(exclude_unset=True, exclude_none=True)

        for field, value in update_dict.items():
            if hasattr(template, field):
                # Handle enums
                if hasattr(value, 'value'):
                    setattr(template, field, value.value)
                else:
                    setattr(template, field, value)

        template.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(template)

        logger.info(f"Updated template: {template_id}")

        return template

    async def delete_template(self, template_id: UUID) -> bool:
        """Soft delete template (deactivate)"""
        template = await self.get_template(template_id)

        if not template:
            return False

        template.is_active = False
        template.updated_at = datetime.utcnow()

        self.db.commit()

        logger.info(f"Deactivated template: {template_id}")

        return True

    # ==================== Template Rendering ====================

    async def render_template(
        self,
        request: TemplateRenderRequest
    ) -> TemplateRenderResponse:
        """
        Preview template rendering with variables

        Uses Python string.Template for safe substitution
        """
        # Get template
        # Try all channels since name might be unique
        template = self.db.query(MessageTemplate).filter(
            MessageTemplate.name == request.template_name
        ).first()

        if not template:
            raise ValueError(f"Template '{request.template_name}' not found")

        # Render subject
        rendered_subject = None
        if template.subject:
            try:
                subject_template = Template(template.subject)
                rendered_subject = subject_template.safe_substitute(request.variables)
            except Exception as e:
                logger.warning(f"Error rendering subject: {e}")
                rendered_subject = template.subject

        # Render body
        try:
            body_template = Template(template.body)
            rendered_body = body_template.safe_substitute(request.variables)
        except Exception as e:
            logger.error(f"Error rendering body: {e}")
            rendered_body = template.body

        # Find missing variables
        import re
        template_vars = set(re.findall(r'\{(\w+)\}', template.body))
        provided_vars = set(request.variables.keys())
        missing_vars = list(template_vars - provided_vars)

        return TemplateRenderResponse(
            subject=rendered_subject,
            body=rendered_body,
            variables_used=list(provided_vars),
            missing_variables=missing_vars
        )

    # ==================== Notification Sending ====================

    async def send_notification(
        self,
        notification_data: NotificationSend,
        org_id: Optional[UUID] = None
    ) -> OutboundNotification:
        """
        Send notification directly (without template)

        Creates notification record and queues for sending
        """
        try:
            # Create notification record
            notification = OutboundNotification(
                id=uuid4(),
                org_id=org_id,
                channel=notification_data.channel.value,
                to=notification_data.to,
                subject=notification_data.subject,
                body=notification_data.body,
                status=NotificationStatus.QUEUED.value,
                priority=notification_data.priority.value,
                scheduled_for=notification_data.scheduled_for,
                metadata_json=notification_data.metadata,
                retry_count=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.db.add(notification)
            self.db.commit()
            self.db.refresh(notification)

            logger.info(
                f"Created notification {notification.id} "
                f"({notification.channel} to {notification.to})"
            )

            # Send immediately if not scheduled
            if not notification_data.scheduled_for:
                await self._send_notification(notification.id)

            return notification

        except Exception as e:
            logger.error(f"Error creating notification: {e}", exc_info=True)
            self.db.rollback()
            raise

    async def send_with_template(
        self,
        notification_data: NotificationSendWithTemplate,
        org_id: Optional[UUID] = None
    ) -> OutboundNotification:
        """
        Send notification using template

        1. Load template
        2. Render with variables
        3. Send notification
        """
        try:
            # Get template
            template = await self.get_template_by_name(
                notification_data.template_name,
                notification_data.channel
            )

            if not template:
                raise ValueError(
                    f"Template '{notification_data.template_name}' "
                    f"not found for channel {notification_data.channel.value}"
                )

            if not template.is_active:
                raise ValueError(
                    f"Template '{notification_data.template_name}' is inactive"
                )

            # Render template
            rendered_subject = None
            if template.subject:
                subject_template = Template(template.subject)
                rendered_subject = subject_template.safe_substitute(notification_data.variables)

            body_template = Template(template.body)
            rendered_body = body_template.safe_substitute(notification_data.variables)

            # Create notification
            notification = NotificationSend(
                channel=notification_data.channel,
                to=notification_data.to,
                subject=rendered_subject,
                body=rendered_body,
                priority=notification_data.priority,
                scheduled_for=notification_data.scheduled_for,
                metadata=notification_data.metadata
            )

            result = await self.send_notification(notification, org_id)

            # Update template reference
            result.template_id = template.id
            result.template_name = template.name

            # Update template usage stats
            template.total_sent += 1
            template.last_used_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(result)

            return result

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error sending with template: {e}", exc_info=True)
            self.db.rollback()
            raise

    async def _send_notification(self, notification_id: UUID) -> bool:
        """
        Actually send notification via channel

        This is called asynchronously to send the notification
        """
        notification = self.db.query(OutboundNotification).filter(
            OutboundNotification.id == notification_id
        ).first()

        if not notification:
            return False

        try:
            # Update status
            notification.status = NotificationStatus.SENDING.value
            self.db.commit()

            # Route to appropriate channel handler
            success = False

            if notification.channel == NotificationChannel.WHATSAPP.value:
                success = await self._send_whatsapp(notification)

            elif notification.channel == NotificationChannel.SMS.value:
                success = await self._send_sms(notification)

            elif notification.channel == NotificationChannel.EMAIL.value:
                success = await self._send_email(notification)

            elif notification.channel == NotificationChannel.VOICE.value:
                success = await self._send_voice(notification)

            else:
                logger.warning(f"Unknown channel: {notification.channel}")
                success = False

            # Update status based on result
            if success:
                notification.status = NotificationStatus.SENT.value
                notification.sent_at = datetime.utcnow()
                logger.info(f"Sent notification {notification_id} via {notification.channel}")
            else:
                notification.status = NotificationStatus.FAILED.value
                notification.error_message = "Failed to send"
                notification.retry_count += 1
                logger.error(f"Failed to send notification {notification_id}")

            notification.updated_at = datetime.utcnow()
            self.db.commit()

            # Publish event
            await publish_event(
                event_type=EventType.NOTIFICATION_SENT if success else EventType.NOTIFICATION_FAILED,
                entity_id=notification_id,
                entity_type="notification",
                data={
                    "notification_id": str(notification_id),
                    "channel": notification.channel,
                    "status": notification.status,
                    "to": notification.to
                }
            )

            return success

        except Exception as e:
            logger.error(f"Error sending notification {notification_id}: {e}", exc_info=True)

            notification.status = NotificationStatus.FAILED.value
            notification.error_message = str(e)
            notification.retry_count += 1
            notification.updated_at = datetime.utcnow()
            self.db.commit()

            return False

    # ==================== Channel Handlers ====================

    async def _send_whatsapp(self, notification: OutboundNotification) -> bool:
        """Send WhatsApp message via Twilio"""
        if not twilio_client:
            logger.error("Twilio client not configured")
            return False

        try:
            return twilio_client.send_message(
                to=notification.to,
                body=notification.body
            )
        except Exception as e:
            logger.error(f"Twilio WhatsApp error: {e}")
            return False

    async def _send_sms(self, notification: OutboundNotification) -> bool:
        """Send SMS via Twilio"""
        if not twilio_client:
            logger.error("Twilio client not configured")
            return False

        try:
            return twilio_client.send_sms(
                to=notification.to,
                body=notification.body
            )
        except Exception as e:
            logger.error(f"Twilio SMS error: {e}")
            return False

    async def _send_email(self, notification: OutboundNotification) -> bool:
        """
        Send email via SendGrid/SES

        TODO: Implement email sending
        """
        logger.warning("Email sending not yet implemented")

        # Placeholder: mark as sent for testing
        return True

    async def _send_voice(self, notification: OutboundNotification) -> bool:
        """
        Send voice call via Twilio

        TODO: Implement voice calling
        """
        logger.warning("Voice calling not yet implemented")

        # Placeholder
        return True

    # ==================== Bulk Operations ====================

    async def send_bulk_notifications(
        self,
        bulk_data: BulkNotificationSend,
        org_id: Optional[UUID] = None
    ) -> BulkNotificationResult:
        """
        Send notifications to multiple recipients

        Queues all notifications for background processing
        """
        successful = 0
        failed = 0
        notification_ids = []
        errors = []

        for recipient in bulk_data.recipients:
            try:
                # Get variables for this recipient
                variables = bulk_data.variables.copy()

                if bulk_data.per_recipient_variables and recipient in bulk_data.per_recipient_variables:
                    variables.update(bulk_data.per_recipient_variables[recipient])

                # Send notification
                notification_data = NotificationSendWithTemplate(
                    template_name=bulk_data.template_name,
                    channel=bulk_data.channel,
                    to=recipient,
                    variables=variables
                )

                result = await self.send_with_template(notification_data, org_id)

                notification_ids.append(result.id)
                successful += 1

            except Exception as e:
                logger.error(f"Error sending to {recipient}: {e}")
                errors.append(f"{recipient}: {str(e)}")
                failed += 1

        return BulkNotificationResult(
            total_recipients=len(bulk_data.recipients),
            successful=successful,
            failed=failed,
            queued_notification_ids=notification_ids,
            errors=errors
        )

    # ==================== Query Operations ====================

    async def get_notification(self, notification_id: UUID) -> Optional[OutboundNotification]:
        """Get notification by ID"""
        return self.db.query(OutboundNotification).filter(
            OutboundNotification.id == notification_id
        ).first()

    async def list_notifications(
        self,
        filters: NotificationListFilters
    ) -> List[OutboundNotification]:
        """List notifications with filters"""
        query = self.db.query(OutboundNotification)

        # Apply filters
        if filters.channel:
            query = query.filter(OutboundNotification.channel == filters.channel.value)

        if filters.status:
            query = query.filter(OutboundNotification.status == filters.status.value)

        if filters.to:
            query = query.filter(OutboundNotification.to == filters.to)

        if filters.template_id:
            query = query.filter(OutboundNotification.template_id == filters.template_id)

        if filters.sent_after:
            query = query.filter(OutboundNotification.sent_at >= filters.sent_after)

        if filters.sent_before:
            query = query.filter(OutboundNotification.sent_at <= filters.sent_before)

        # Order by most recent
        query = query.order_by(OutboundNotification.created_at.desc())

        # Pagination
        query = query.offset(filters.offset).limit(filters.limit)

        return query.all()

    # ==================== Statistics ====================

    async def get_statistics(
        self,
        start_date: datetime,
        end_date: datetime,
        org_id: Optional[UUID] = None
    ) -> NotificationStatistics:
        """Get notification statistics for time period"""
        query = self.db.query(OutboundNotification).filter(
            and_(
                OutboundNotification.created_at >= start_date,
                OutboundNotification.created_at <= end_date
            )
        )

        if org_id:
            query = query.filter(OutboundNotification.org_id == org_id)

        # Total counts
        total_sent = query.filter(
            OutboundNotification.status.in_([
                NotificationStatus.SENT.value,
                NotificationStatus.DELIVERED.value
            ])
        ).count()

        total_delivered = query.filter(
            OutboundNotification.status == NotificationStatus.DELIVERED.value
        ).count()

        total_failed = query.filter(
            OutboundNotification.status.in_([
                NotificationStatus.FAILED.value,
                NotificationStatus.BOUNCED.value
            ])
        ).count()

        # By channel
        channel_results = self.db.query(
            OutboundNotification.channel,
            func.count(OutboundNotification.id)
        ).filter(
            and_(
                OutboundNotification.created_at >= start_date,
                OutboundNotification.created_at <= end_date
            )
        ).group_by(OutboundNotification.channel).all()

        by_channel = {channel: count for channel, count in channel_results}

        # By status
        status_results = self.db.query(
            OutboundNotification.status,
            func.count(OutboundNotification.id)
        ).filter(
            and_(
                OutboundNotification.created_at >= start_date,
                OutboundNotification.created_at <= end_date
            )
        ).group_by(OutboundNotification.status).all()

        by_status = {status: count for status, count in status_results}

        # Delivery rate
        total_attempts = total_sent + total_failed
        delivery_rate = total_sent / total_attempts if total_attempts > 0 else 0.0

        # Most used templates
        template_results = self.db.query(
            MessageTemplate.name,
            MessageTemplate.total_sent
        ).order_by(MessageTemplate.total_sent.desc()).limit(10).all()

        most_used = [
            {"template_name": name, "total_sent": count}
            for name, count in template_results
        ]

        return NotificationStatistics(
            total_sent=total_sent,
            total_delivered=total_delivered,
            total_failed=total_failed,
            by_channel=by_channel,
            by_status=by_status,
            delivery_rate=delivery_rate,
            most_used_templates=most_used,
            period_start=start_date,
            period_end=end_date
        )
