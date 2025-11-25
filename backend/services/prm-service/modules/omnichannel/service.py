"""
Omnichannel Communications Service
Main service orchestrating all omnichannel communication operations
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
import hashlib

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func
from loguru import logger

from shared.events.publisher import publish_event
from shared.events.types import EventType

from .models import (
    OmnichannelProvider, OmnichannelTemplate, OmnichannelConversation,
    OmnichannelMessage, MessageAttachment, MessageDeliveryStatus,
    CommunicationPreference, ConsentRecord, OptOutRecord,
    Campaign, CampaignSegment, CampaignExecution, ABTestVariant,
    InboxAssignment, CannedResponse, SLAConfiguration, SLATracking,
    ChannelAnalyticsDaily, EngagementScore, CommunicationAuditLog,
    OmniChannelType, MessageDirection, DeliveryStatus, ConversationStatus,
    ConversationPriority, TemplateStatus, CampaignStatus, ConsentStatus, ConsentType
)
from .schemas import (
    SendMessageRequest, MessageResponse, BulkSendRequest,
    ConversationCreate, ConversationUpdate, ConversationResponse,
    PreferenceCreate, PreferenceUpdate, PreferenceResponse,
    ConsentCreate, ConsentResponse, OptOutRequest,
    ProviderCreate, ProviderUpdate, ProviderResponse,
    TemplateCreate, TemplateUpdate, TemplateResponse,
    ChannelType, MessageStatusUpdate
)
from .providers import ProviderFactory, get_provider, MessagePayload, ProviderResult


class OmnichannelService:
    """
    Main omnichannel communication service.
    Handles message sending, routing, conversations, and preferences.
    """

    def __init__(self, db: Session):
        self.db = db

    # ==================== Message Operations ====================

    async def send_message(
        self,
        request: SendMessageRequest,
        user_id: Optional[UUID] = None
    ) -> MessageResponse:
        """
        Send a message through the omnichannel platform.
        Handles channel selection, preference checking, and delivery.
        """
        try:
            # Check consent and opt-out status
            if not await self._check_consent(request.tenant_id, request.recipient, request.channel):
                raise ValueError("Recipient has not consented to receive messages")

            if await self._is_opted_out(request.tenant_id, request.recipient, request.channel):
                raise ValueError("Recipient has opted out of messages")

            # Get or create conversation
            conversation = await self._get_or_create_conversation(
                tenant_id=request.tenant_id,
                patient_id=request.patient_id,
                contact_id=request.recipient,
                channel=request.channel or await self._select_channel(request),
                conversation_id=request.conversation_id
            )

            # Select channel if not specified
            channel = request.channel or await self._select_channel(request)

            # Get provider for channel
            provider_config = await self._get_provider_for_channel(request.tenant_id, channel)
            if not provider_config:
                raise ValueError(f"No active provider configured for channel: {channel}")

            # Render template if specified
            content = request.content
            subject = request.subject
            if request.template_id:
                content, subject = await self._render_template(
                    request.template_id,
                    request.template_variables
                )

            # Create message record
            message = OmnichannelMessage(
                id=uuid4(),
                tenant_id=request.tenant_id,
                conversation_id=conversation.id,
                patient_id=request.patient_id,
                provider_id=provider_config.id,
                channel=OmniChannelType(channel.value if hasattr(channel, 'value') else channel),
                direction=MessageDirection.OUTBOUND,
                sender_type="system" if not user_id else "agent",
                sender_id=user_id,
                recipient_contact=request.recipient,
                message_type=request.message_type,
                content=content,
                subject=subject,
                template_id=request.template_id,
                template_variables=request.template_variables,
                buttons=request.buttons if request.buttons else None,
                status=DeliveryStatus.PENDING,
                metadata=request.metadata,
                created_by=user_id
            )

            self.db.add(message)
            self.db.commit()
            self.db.refresh(message)

            # Handle scheduled messages
            if request.scheduled_at:
                # Queue for later delivery
                message.status = DeliveryStatus.QUEUED
                message.queued_at = datetime.utcnow()
                message.metadata['scheduled_at'] = request.scheduled_at.isoformat()
                self.db.commit()

                return self._message_to_response(message)

            # Send immediately
            result = await self._send_via_provider(provider_config, message, content)

            # Update message status
            if result.success:
                message.status = DeliveryStatus.SENT
                message.external_id = result.external_id
                message.sent_at = datetime.utcnow()
                message.cost = result.cost
                message.segments = result.segments
            else:
                message.status = DeliveryStatus.FAILED
                message.error_code = result.error_code
                message.error_message = result.error_message
                message.failed_at = datetime.utcnow()

                if result.is_retriable:
                    message.retry_count += 1
                    message.next_retry_at = datetime.utcnow() + timedelta(minutes=5)

            self.db.commit()

            # Update conversation
            await self._update_conversation_on_message(conversation, message)

            # Record delivery status
            delivery_status = MessageDeliveryStatus(
                id=uuid4(),
                message_id=message.id,
                tenant_id=request.tenant_id,
                status=message.status,
                provider_id=provider_config.id,
                provider_response=result.metadata
            )
            self.db.add(delivery_status)
            self.db.commit()

            # Publish event
            await self._publish_message_event(message, "sent" if result.success else "failed")

            # Audit log
            await self._log_audit(
                tenant_id=request.tenant_id,
                resource_type="message",
                resource_id=message.id,
                patient_id=request.patient_id,
                action="send",
                actor_id=user_id
            )

            return self._message_to_response(message)

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.db.rollback()
            raise

    async def send_bulk_messages(
        self,
        request: BulkSendRequest,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Send messages to multiple recipients"""
        results = {
            "total": len(request.recipients),
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "details": []
        }

        for recipient in request.recipients:
            try:
                # Check opt-out
                if await self._is_opted_out(request.tenant_id, recipient, request.channel):
                    results["skipped"] += 1
                    results["details"].append({
                        "recipient": recipient,
                        "status": "skipped",
                        "reason": "opted_out"
                    })
                    continue

                # Get personalization for this recipient
                variables = request.template_variables.copy()
                if request.personalization and recipient in request.personalization:
                    variables.update(request.personalization[recipient])

                msg_request = SendMessageRequest(
                    tenant_id=request.tenant_id,
                    recipient=recipient,
                    channel=request.channel,
                    content=request.content,
                    template_id=request.template_id,
                    template_variables=variables,
                    scheduled_at=request.scheduled_at
                )

                response = await self.send_message(msg_request, user_id)
                results["successful"] += 1
                results["details"].append({
                    "recipient": recipient,
                    "status": "sent",
                    "message_id": str(response.id)
                })

            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "recipient": recipient,
                    "status": "failed",
                    "error": str(e)
                })

        return results

    async def update_message_status(
        self,
        external_id: str,
        status_update: MessageStatusUpdate
    ) -> Optional[OmnichannelMessage]:
        """Update message status from webhook"""
        try:
            message = self.db.query(OmnichannelMessage).filter(
                OmnichannelMessage.external_id == external_id
            ).first()

            if not message:
                logger.warning(f"Message not found for external_id: {external_id}")
                return None

            # Map status
            status_mapping = {
                'sent': DeliveryStatus.SENT,
                'delivered': DeliveryStatus.DELIVERED,
                'read': DeliveryStatus.READ,
                'failed': DeliveryStatus.FAILED,
                'bounced': DeliveryStatus.BOUNCED,
                'blocked': DeliveryStatus.BLOCKED
            }

            new_status = status_mapping.get(status_update.status.value, status_update.status)
            message.status = new_status

            # Update timestamps
            if new_status == DeliveryStatus.DELIVERED:
                message.delivered_at = status_update.timestamp or datetime.utcnow()
            elif new_status == DeliveryStatus.READ:
                message.read_at = status_update.timestamp or datetime.utcnow()
            elif new_status in [DeliveryStatus.FAILED, DeliveryStatus.BOUNCED, DeliveryStatus.BLOCKED]:
                message.failed_at = status_update.timestamp or datetime.utcnow()
                message.error_code = status_update.error_code
                message.error_message = status_update.error_message

            # Record status change
            delivery_status = MessageDeliveryStatus(
                id=uuid4(),
                message_id=message.id,
                tenant_id=message.tenant_id,
                status=new_status,
                provider_id=message.provider_id,
                provider_response=status_update.provider_response,
                error_code=status_update.error_code,
                error_message=status_update.error_message,
                webhook_received_at=datetime.utcnow()
            )
            self.db.add(delivery_status)

            self.db.commit()

            # Publish status event
            await self._publish_message_event(message, "status_updated")

            return message

        except Exception as e:
            logger.error(f"Error updating message status: {e}")
            self.db.rollback()
            raise

    # ==================== Channel Selection ====================

    async def _select_channel(self, request: SendMessageRequest) -> ChannelType:
        """
        Intelligent channel selection based on:
        1. Patient preferences
        2. Message type/urgency
        3. Channel availability
        4. Cost optimization
        """
        # Get patient preferences if patient_id provided
        if request.patient_id:
            preference = await self.get_preference(request.tenant_id, request.patient_id)
            if preference and preference.preferred_channel:
                # Check if provider is available for preferred channel
                if await self._get_provider_for_channel(request.tenant_id, preference.preferred_channel):
                    return preference.preferred_channel

                # Try fallback channel
                if preference.fallback_channel:
                    if await self._get_provider_for_channel(request.tenant_id, preference.fallback_channel):
                        return preference.fallback_channel

        # Default channel selection based on recipient format
        recipient = request.recipient
        if '@' in recipient:
            return ChannelType.EMAIL
        elif recipient.startswith('whatsapp:') or '+' in recipient:
            # Check if WhatsApp is available
            if await self._get_provider_for_channel(request.tenant_id, ChannelType.WHATSAPP):
                return ChannelType.WHATSAPP
            return ChannelType.SMS

        # Default to SMS
        return ChannelType.SMS

    async def _get_provider_for_channel(
        self,
        tenant_id: UUID,
        channel: ChannelType
    ) -> Optional[OmnichannelProvider]:
        """Get the primary active provider for a channel"""
        channel_value = channel.value if hasattr(channel, 'value') else channel

        provider = self.db.query(OmnichannelProvider).filter(
            OmnichannelProvider.tenant_id == tenant_id,
            OmnichannelProvider.channel == channel_value,
            OmnichannelProvider.is_active == True
        ).order_by(
            OmnichannelProvider.is_primary.desc(),
            OmnichannelProvider.priority.desc()
        ).first()

        return provider

    async def _send_via_provider(
        self,
        provider_config: OmnichannelProvider,
        message: OmnichannelMessage,
        content: str
    ) -> ProviderResult:
        """Send message via provider"""
        try:
            # Build provider config
            config = {
                'provider_id': provider_config.id,
                'tenant_id': provider_config.tenant_id,
                'provider_type': provider_config.provider_type.value,
                'credentials': provider_config.credentials,
                'config': provider_config.config or {},
                'from_phone_number': provider_config.from_phone_number,
                'from_email': provider_config.from_email,
                'from_name': provider_config.from_name,
                'reply_to_email': provider_config.reply_to_email,
                'whatsapp_phone_number_id': provider_config.whatsapp_phone_number_id,
                'whatsapp_business_account_id': provider_config.whatsapp_business_account_id,
                'rate_limit_per_second': provider_config.rate_limit_per_second,
                'rate_limit_per_day': provider_config.rate_limit_per_day
            }

            # Get or create provider instance
            provider = get_provider(
                provider_config.id,
                provider_config.provider_type.value,
                config
            )

            if not provider:
                return ProviderResult(
                    success=False,
                    error_code="PROVIDER_NOT_FOUND",
                    error_message="Could not create provider instance"
                )

            # Initialize if needed
            if not provider.is_initialized:
                await provider.initialize()

            # Build message payload
            payload = MessagePayload(
                recipient=message.recipient_contact,
                content=content,
                subject=message.subject,
                attachments=[],  # Handle attachments separately
                buttons=message.buttons or [],
                metadata={
                    'message_id': str(message.id),
                    'patient_id': str(message.patient_id) if message.patient_id else None,
                    'content_html': message.content_structured.get('html') if message.content_structured else None
                }
            )

            # Send with retry
            result = await provider.send_with_retry(payload, max_retries=3)

            # Update provider usage
            if result.success:
                provider_config.daily_usage_count = (provider_config.daily_usage_count or 0) + 1
                self.db.commit()

            return result

        except Exception as e:
            logger.error(f"Provider send error: {e}")
            return ProviderResult(
                success=False,
                error_code="PROVIDER_ERROR",
                error_message=str(e),
                is_retriable=True
            )

    # ==================== Conversation Operations ====================

    async def _get_or_create_conversation(
        self,
        tenant_id: UUID,
        patient_id: Optional[UUID],
        contact_id: str,
        channel: ChannelType,
        conversation_id: Optional[UUID] = None
    ) -> OmnichannelConversation:
        """Get existing conversation or create new one"""

        # If conversation_id provided, use it
        if conversation_id:
            conversation = self.db.query(OmnichannelConversation).filter(
                OmnichannelConversation.id == conversation_id,
                OmnichannelConversation.tenant_id == tenant_id
            ).first()

            if conversation:
                return conversation

        # Generate conversation key for deduplication
        key_parts = [str(tenant_id), contact_id]
        if patient_id:
            key_parts.append(str(patient_id))
        conversation_key = hashlib.md5('|'.join(key_parts).encode()).hexdigest()

        # Try to find existing active conversation
        conversation = self.db.query(OmnichannelConversation).filter(
            OmnichannelConversation.tenant_id == tenant_id,
            OmnichannelConversation.conversation_key == conversation_key,
            OmnichannelConversation.status.in_([
                ConversationStatus.NEW,
                ConversationStatus.OPEN,
                ConversationStatus.PENDING
            ])
        ).first()

        if conversation:
            # Update channels used
            channel_value = channel.value if hasattr(channel, 'value') else channel
            if channel_value not in (conversation.channels_used or []):
                conversation.channels_used = (conversation.channels_used or []) + [channel_value]
                self.db.commit()
            return conversation

        # Create new conversation
        channel_value = channel.value if hasattr(channel, 'value') else channel
        conversation = OmnichannelConversation(
            id=uuid4(),
            tenant_id=tenant_id,
            patient_id=patient_id,
            external_contact_id=contact_id,
            conversation_key=conversation_key,
            primary_channel=OmniChannelType(channel_value),
            channels_used=[channel_value],
            status=ConversationStatus.NEW,
            priority=ConversationPriority.NORMAL,
            first_message_at=datetime.utcnow()
        )

        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)

        return conversation

    async def _update_conversation_on_message(
        self,
        conversation: OmnichannelConversation,
        message: OmnichannelMessage
    ):
        """Update conversation stats after message"""
        conversation.message_count = (conversation.message_count or 0) + 1
        conversation.last_message_at = datetime.utcnow()

        if message.direction == MessageDirection.OUTBOUND:
            conversation.outbound_count = (conversation.outbound_count or 0) + 1
            conversation.last_agent_reply_at = datetime.utcnow()

            # Check first response SLA
            if not conversation.first_response_at and conversation.status == ConversationStatus.NEW:
                conversation.first_response_at = datetime.utcnow()
                conversation.status = ConversationStatus.OPEN
        else:
            conversation.inbound_count = (conversation.inbound_count or 0) + 1
            conversation.last_patient_message_at = datetime.utcnow()
            conversation.unread_count = (conversation.unread_count or 0) + 1

        self.db.commit()

    async def get_conversation(
        self,
        tenant_id: UUID,
        conversation_id: UUID
    ) -> Optional[OmnichannelConversation]:
        """Get conversation by ID"""
        return self.db.query(OmnichannelConversation).filter(
            OmnichannelConversation.id == conversation_id,
            OmnichannelConversation.tenant_id == tenant_id
        ).first()

    async def list_conversations(
        self,
        tenant_id: UUID,
        status: Optional[List[ConversationStatus]] = None,
        assigned_agent_id: Optional[UUID] = None,
        patient_id: Optional[UUID] = None,
        channel: Optional[ChannelType] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[OmnichannelConversation], int]:
        """List conversations with filters"""
        query = self.db.query(OmnichannelConversation).filter(
            OmnichannelConversation.tenant_id == tenant_id
        )

        if status:
            query = query.filter(OmnichannelConversation.status.in_(status))

        if assigned_agent_id:
            query = query.filter(OmnichannelConversation.assigned_agent_id == assigned_agent_id)

        if patient_id:
            query = query.filter(OmnichannelConversation.patient_id == patient_id)

        if channel:
            channel_value = channel.value if hasattr(channel, 'value') else channel
            query = query.filter(OmnichannelConversation.primary_channel == channel_value)

        total = query.count()

        conversations = query.order_by(
            desc(OmnichannelConversation.last_message_at)
        ).offset((page - 1) * page_size).limit(page_size).all()

        return conversations, total

    async def update_conversation(
        self,
        tenant_id: UUID,
        conversation_id: UUID,
        update: ConversationUpdate,
        user_id: Optional[UUID] = None
    ) -> Optional[OmnichannelConversation]:
        """Update conversation"""
        conversation = await self.get_conversation(tenant_id, conversation_id)
        if not conversation:
            return None

        if update.status:
            conversation.status = update.status
            if update.status == ConversationStatus.RESOLVED:
                conversation.resolved_at = datetime.utcnow()
                conversation.resolved_by = user_id
            elif update.status == ConversationStatus.CLOSED:
                conversation.closed_at = datetime.utcnow()
                conversation.closed_by = user_id

        if update.priority:
            conversation.priority = update.priority

        if update.assigned_agent_id is not None:
            conversation.assigned_agent_id = update.assigned_agent_id
            conversation.assigned_at = datetime.utcnow()

        if update.assigned_team_id is not None:
            conversation.assigned_team_id = update.assigned_team_id

        if update.topic:
            conversation.topic = update.topic

        if update.sub_topic:
            conversation.sub_topic = update.sub_topic

        if update.tags is not None:
            conversation.tags = update.tags

        if update.context is not None:
            conversation.context = update.context

        self.db.commit()
        self.db.refresh(conversation)

        return conversation

    # ==================== Preference Operations ====================

    async def get_preference(
        self,
        tenant_id: UUID,
        patient_id: UUID
    ) -> Optional[CommunicationPreference]:
        """Get patient communication preference"""
        return self.db.query(CommunicationPreference).filter(
            CommunicationPreference.tenant_id == tenant_id,
            CommunicationPreference.patient_id == patient_id,
            CommunicationPreference.is_active == True
        ).first()

    async def create_or_update_preference(
        self,
        data: PreferenceCreate,
        user_id: Optional[UUID] = None
    ) -> CommunicationPreference:
        """Create or update communication preference"""
        existing = await self.get_preference(data.tenant_id, data.patient_id)

        if existing:
            # Update existing
            for field, value in data.dict(exclude_unset=True, exclude={'tenant_id', 'patient_id'}).items():
                if value is not None:
                    setattr(existing, field, value)
            existing.updated_by = user_id
            self.db.commit()
            self.db.refresh(existing)
            return existing

        # Create new
        preference = CommunicationPreference(
            id=uuid4(),
            **data.dict()
        )
        preference.updated_by = user_id

        self.db.add(preference)
        self.db.commit()
        self.db.refresh(preference)

        return preference

    # ==================== Consent Operations ====================

    async def _check_consent(
        self,
        tenant_id: UUID,
        recipient: str,
        channel: Optional[ChannelType]
    ) -> bool:
        """Check if recipient has granted consent"""
        # For now, assume consent is granted
        # Full implementation would check consent_records table
        return True

    async def _is_opted_out(
        self,
        tenant_id: UUID,
        recipient: str,
        channel: Optional[ChannelType]
    ) -> bool:
        """Check if recipient has opted out"""
        query = self.db.query(OptOutRecord).filter(
            OptOutRecord.tenant_id == tenant_id,
            OptOutRecord.contact_value == recipient,
            OptOutRecord.is_active == True
        )

        if channel:
            channel_value = channel.value if hasattr(channel, 'value') else channel
            query = query.filter(
                or_(
                    OptOutRecord.channel == None,
                    OptOutRecord.channel == channel_value
                )
            )

        return query.first() is not None

    async def record_opt_out(
        self,
        request: OptOutRequest
    ) -> OptOutRecord:
        """Record an opt-out"""
        opt_out = OptOutRecord(
            id=uuid4(),
            tenant_id=request.tenant_id,
            contact_type=request.contact_type,
            contact_value=request.contact_value,
            channel=OmniChannelType(request.channel.value) if request.channel else None,
            opt_out_type=request.opt_out_type,
            reason=request.reason,
            method=request.method,
            source_message_id=request.source_message_id,
            is_active=True,
            opted_out_at=datetime.utcnow()
        )

        self.db.add(opt_out)
        self.db.commit()
        self.db.refresh(opt_out)

        return opt_out

    # ==================== Template Operations ====================

    async def _render_template(
        self,
        template_id: UUID,
        variables: Dict[str, Any]
    ) -> Tuple[str, Optional[str]]:
        """Render template with variables"""
        template = self.db.query(OmnichannelTemplate).filter(
            OmnichannelTemplate.id == template_id,
            OmnichannelTemplate.status == TemplateStatus.APPROVED
        ).first()

        if not template:
            raise ValueError(f"Template not found or not approved: {template_id}")

        # Render body
        body = template.body
        subject = template.subject

        # Replace variables
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            body = body.replace(placeholder, str(value))
            if subject:
                subject = subject.replace(placeholder, str(value))

        # Update usage stats
        template.usage_count = (template.usage_count or 0) + 1
        template.last_used_at = datetime.utcnow()
        self.db.commit()

        return body, subject

    async def get_template(
        self,
        tenant_id: UUID,
        template_id: UUID
    ) -> Optional[OmnichannelTemplate]:
        """Get template by ID"""
        return self.db.query(OmnichannelTemplate).filter(
            OmnichannelTemplate.id == template_id,
            OmnichannelTemplate.tenant_id == tenant_id
        ).first()

    async def list_templates(
        self,
        tenant_id: UUID,
        channel: Optional[ChannelType] = None,
        status: Optional[TemplateStatus] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[OmnichannelTemplate], int]:
        """List templates"""
        query = self.db.query(OmnichannelTemplate).filter(
            OmnichannelTemplate.tenant_id == tenant_id,
            OmnichannelTemplate.is_active == True
        )

        if channel:
            channel_value = channel.value if hasattr(channel, 'value') else channel
            query = query.filter(OmnichannelTemplate.channel == channel_value)

        if status:
            query = query.filter(OmnichannelTemplate.status == status)

        total = query.count()
        templates = query.order_by(
            desc(OmnichannelTemplate.created_at)
        ).offset((page - 1) * page_size).limit(page_size).all()

        return templates, total

    async def create_template(
        self,
        data: TemplateCreate,
        user_id: Optional[UUID] = None
    ) -> OmnichannelTemplate:
        """Create a new template"""
        template = OmnichannelTemplate(
            id=uuid4(),
            tenant_id=data.tenant_id,
            name=data.name,
            code=data.code,
            description=data.description,
            channel=OmniChannelType(data.channel.value),
            category=data.category,
            subject=data.subject,
            body=data.body,
            body_html=data.body_html,
            header_text=data.header_text,
            footer_text=data.footer_text,
            variables=data.variables,
            default_values=data.default_values,
            buttons=[b.dict() for b in data.buttons] if data.buttons else [],
            quick_replies=data.quick_replies,
            media_type=data.media_type,
            media_url=data.media_url,
            language=data.language,
            status=TemplateStatus.DRAFT,
            created_by=user_id
        )

        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)

        return template

    # ==================== Provider Operations ====================

    async def get_provider(
        self,
        tenant_id: UUID,
        provider_id: UUID
    ) -> Optional[OmnichannelProvider]:
        """Get provider by ID"""
        return self.db.query(OmnichannelProvider).filter(
            OmnichannelProvider.id == provider_id,
            OmnichannelProvider.tenant_id == tenant_id
        ).first()

    async def list_providers(
        self,
        tenant_id: UUID,
        channel: Optional[ChannelType] = None,
        is_active: Optional[bool] = True,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[OmnichannelProvider], int]:
        """List providers"""
        query = self.db.query(OmnichannelProvider).filter(
            OmnichannelProvider.tenant_id == tenant_id
        )

        if channel:
            channel_value = channel.value if hasattr(channel, 'value') else channel
            query = query.filter(OmnichannelProvider.channel == channel_value)

        if is_active is not None:
            query = query.filter(OmnichannelProvider.is_active == is_active)

        total = query.count()
        providers = query.order_by(
            OmnichannelProvider.channel,
            desc(OmnichannelProvider.is_primary)
        ).offset((page - 1) * page_size).limit(page_size).all()

        return providers, total

    async def create_provider(
        self,
        data: ProviderCreate,
        user_id: Optional[UUID] = None
    ) -> OmnichannelProvider:
        """Create a new provider"""
        from .models import ProviderType as ProviderTypeEnum

        provider = OmnichannelProvider(
            id=uuid4(),
            tenant_id=data.tenant_id,
            name=data.name,
            provider_type=ProviderTypeEnum(data.provider_type.value),
            channel=OmniChannelType(data.channel.value),
            is_primary=data.is_primary,
            is_fallback=data.is_fallback,
            priority=data.priority,
            credentials=data.credentials,
            config=data.config,
            rate_limit_per_second=data.rate_limit_per_second,
            rate_limit_per_day=data.rate_limit_per_day,
            from_phone_number=data.from_phone_number,
            from_email=data.from_email,
            from_name=data.from_name,
            reply_to_email=data.reply_to_email,
            whatsapp_business_account_id=data.whatsapp_business_account_id,
            whatsapp_phone_number_id=data.whatsapp_phone_number_id,
            created_by=user_id
        )

        self.db.add(provider)
        self.db.commit()
        self.db.refresh(provider)

        return provider

    # ==================== Helper Methods ====================

    def _message_to_response(self, message: OmnichannelMessage) -> MessageResponse:
        """Convert message model to response schema"""
        return MessageResponse(
            id=message.id,
            tenant_id=message.tenant_id,
            conversation_id=message.conversation_id,
            patient_id=message.patient_id,
            external_id=message.external_id,
            channel=ChannelType(message.channel.value),
            direction=MessageDirection(message.direction.value),
            sender_type=message.sender_type,
            sender_name=message.sender_name,
            sender_contact=message.sender_contact,
            recipient_contact=message.recipient_contact,
            message_type=message.message_type,
            content=message.content,
            subject=message.subject,
            template_id=message.template_id,
            template_variables=message.template_variables,
            attachments=[],
            buttons=message.buttons,
            status=DeliveryStatus(message.status.value),
            error_message=message.error_message,
            sent_at=message.sent_at,
            delivered_at=message.delivered_at,
            read_at=message.read_at,
            intent=message.intent,
            sentiment=message.sentiment,
            created_at=message.created_at
        )

    async def _publish_message_event(
        self,
        message: OmnichannelMessage,
        action: str
    ):
        """Publish message event"""
        try:
            event_type = {
                'sent': EventType.COMMUNICATION_SENT,
                'delivered': EventType.COMMUNICATION_DELIVERED,
                'failed': EventType.COMMUNICATION_FAILED,
                'received': EventType.COMMUNICATION_RECEIVED,
                'status_updated': EventType.COMMUNICATION_DELIVERED
            }.get(action, EventType.COMMUNICATION_SENT)

            await publish_event(
                event_type=event_type,
                tenant_id=str(message.tenant_id),
                payload={
                    'message_id': str(message.id),
                    'conversation_id': str(message.conversation_id),
                    'patient_id': str(message.patient_id) if message.patient_id else None,
                    'channel': message.channel.value,
                    'direction': message.direction.value,
                    'status': message.status.value
                },
                source_service="prm-service"
            )
        except Exception as e:
            logger.error(f"Failed to publish message event: {e}")

    async def _log_audit(
        self,
        tenant_id: UUID,
        resource_type: str,
        resource_id: UUID,
        patient_id: Optional[UUID],
        action: str,
        actor_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log audit entry"""
        try:
            audit = CommunicationAuditLog(
                id=uuid4(),
                tenant_id=tenant_id,
                resource_type=resource_type,
                resource_id=resource_id,
                patient_id=patient_id,
                action=action,
                action_details=details,
                actor_type='user' if actor_id else 'system',
                actor_id=actor_id,
                contains_phi=True
            )

            self.db.add(audit)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log audit: {e}")
