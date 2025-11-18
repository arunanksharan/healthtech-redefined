"""
WhatsApp Webhooks Service
Business logic for processing Twilio WhatsApp webhooks
"""
from typing import Optional, Tuple, List
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc
from loguru import logger

from shared.database.conversation_voice_models import Conversation, ConversationMessage
from shared.database.models import Patient
from modules.whatsapp_webhooks.schemas import (
    TwilioWebhookRequest,
    TwilioWebhookResponse,
    WhatsAppStatusWebhook,
    SendWhatsAppMessageRequest,
    SendWhatsAppMessageResponse,
    MessageDirection,
    MessageStatus
)


class WhatsAppWebhookService:
    """Service for processing WhatsApp webhooks from Twilio"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== Incoming Message Processing ====================

    async def process_incoming_message(
        self,
        webhook: TwilioWebhookRequest,
        tenant_id: UUID
    ) -> TwilioWebhookResponse:
        """
        Process incoming WhatsApp message from Twilio

        Flow:
          1. Extract phone number and identify/create patient
          2. Find or create conversation thread
          3. Store message in conversation_messages table
          4. Optionally trigger n8n workflow for AI processing
          5. Return success response

        Args:
            webhook: Twilio webhook payload
            tenant_id: Organization ID

        Returns:
            TwilioWebhookResponse with conversation and message IDs
        """
        actions_taken = []

        # Extract phone numbers (remove 'whatsapp:' prefix)
        from_phone = webhook.From.replace("whatsapp:", "")
        to_phone = webhook.To.replace("whatsapp:", "")

        # Step 1: Identify or create patient
        patient_id, patient_created = self._identify_or_create_patient(
            from_phone,
            webhook.ProfileName or webhook.WaId,
            tenant_id
        )

        if patient_created:
            actions_taken.append("patient_created")

        # Step 2: Find or create conversation
        conversation = self._find_or_create_conversation(
            tenant_id,
            patient_id,
            from_phone,
            "whatsapp"
        )

        if conversation.created_at == conversation.updated_at:
            actions_taken.append("conversation_created")

        # Step 3: Store message
        message = self._store_message(
            conversation_id=conversation.id,
            message_sid=webhook.MessageSid,
            direction=MessageDirection.INBOUND,
            from_number=from_phone,
            to_number=to_phone,
            text_body=webhook.Body,
            media_urls=self._extract_media_urls(webhook),
            media_types=self._extract_media_types(webhook),
            profile_name=webhook.ProfileName,
            wa_id=webhook.WaId
        )

        actions_taken.append("message_stored")

        # Step 4: Update conversation metadata
        conversation.last_message_at = datetime.utcnow()
        conversation.message_count = conversation.message_count + 1

        # Auto-reopen conversation if it was closed
        if conversation.status == "closed":
            conversation.status = "open"
            actions_taken.append("conversation_reopened")

        self.db.commit()

        logger.info(
            f"Processed WhatsApp message {webhook.MessageSid} "
            f"for conversation {conversation.id}"
        )

        return TwilioWebhookResponse(
            success=True,
            conversation_id=str(conversation.id),
            message_id=str(message.id),
            actions_taken=actions_taken
        )

    async def process_status_update(
        self,
        webhook: WhatsAppStatusWebhook,
        tenant_id: UUID
    ) -> TwilioWebhookResponse:
        """
        Process message status update from Twilio

        Updates message delivery status (sent, delivered, read, failed)

        Args:
            webhook: Status update webhook
            tenant_id: Organization ID

        Returns:
            TwilioWebhookResponse
        """
        # Find message by Twilio MessageSid
        query = select(ConversationMessage).where(
            ConversationMessage.twilio_message_sid == webhook.MessageSid
        )

        result = self.db.execute(query)
        message = result.scalar_one_or_none()

        if not message:
            logger.warning(f"Message {webhook.MessageSid} not found for status update")
            return TwilioWebhookResponse(
                success=False,
                actions_taken=["message_not_found"]
            )

        # Update status
        old_status = message.delivery_status
        message.delivery_status = webhook.MessageStatus.lower()

        if webhook.ErrorCode:
            message.error_code = webhook.ErrorCode
            message.error_message = webhook.ErrorMessage

        self.db.commit()

        logger.info(
            f"Updated message {webhook.MessageSid} status: "
            f"{old_status} -> {webhook.MessageStatus}"
        )

        return TwilioWebhookResponse(
            success=True,
            message_id=str(message.id),
            actions_taken=["status_updated"]
        )

    # ==================== Outgoing Messages ====================

    async def send_message(
        self,
        request: SendWhatsAppMessageRequest,
        tenant_id: UUID
    ) -> SendWhatsAppMessageResponse:
        """
        Send a WhatsApp message via Twilio

        Note: This requires Twilio API credentials.
        In production, this would call Twilio's REST API.

        Args:
            request: Message send request
            tenant_id: Organization ID

        Returns:
            SendWhatsAppMessageResponse with message SID
        """
        # TODO: Implement actual Twilio API call
        # For now, create a mock response and store in DB

        # Format phone number with whatsapp: prefix
        to_number = request.to if request.to.startswith("whatsapp:") else f"whatsapp:{request.to}"

        # Mock Twilio message SID
        message_sid = f"SM{uuid4().hex[:32]}"

        # Store outbound message in conversation
        if request.conversation_id:
            conversation = self.db.get(Conversation, UUID(request.conversation_id))
            if conversation:
                self._store_message(
                    conversation_id=conversation.id,
                    message_sid=message_sid,
                    direction=MessageDirection.OUTBOUND,
                    from_number="whatsapp:+14155238886",  # Twilio sandbox number
                    to_number=to_number,
                    text_body=request.body,
                    media_urls=[request.media_url] if request.media_url else [],
                    media_types=[]
                )

                conversation.last_message_at = datetime.utcnow()
                conversation.message_count = conversation.message_count + 1
                self.db.commit()

        logger.info(f"Sent WhatsApp message {message_sid} to {request.to}")

        return SendWhatsAppMessageResponse(
            message_sid=message_sid,
            status="queued",
            conversation_id=request.conversation_id,
            to=request.to,
            body=request.body
        )

    # ==================== Helper Methods ====================

    def _identify_or_create_patient(
        self,
        phone: str,
        name: Optional[str],
        tenant_id: UUID
    ) -> Tuple[UUID, bool]:
        """
        Identify patient by phone number or create new patient

        Returns:
            Tuple of (patient_id, was_created)
        """
        # Try to find existing patient by phone
        query = select(Patient).where(
            and_(
                Patient.tenant_id == tenant_id,
                Patient.phone_number == phone
            )
        )

        result = self.db.execute(query)
        patient = result.scalar_one_or_none()

        if patient:
            return patient.id, False

        # Create new patient
        patient = Patient(
            id=uuid4(),
            tenant_id=tenant_id,
            phone_number=phone,
            name=name or f"WhatsApp User ({phone})",
            contact_method="whatsapp",
            metadata={"source": "whatsapp", "first_contact": datetime.utcnow().isoformat()}
        )

        self.db.add(patient)
        self.db.flush()

        logger.info(f"Created new patient {patient.id} from WhatsApp ({phone})")

        return patient.id, True

    def _find_or_create_conversation(
        self,
        tenant_id: UUID,
        patient_id: UUID,
        phone: str,
        channel_type: str
    ) -> Conversation:
        """
        Find active conversation or create new one

        Returns:
            Conversation object
        """
        # Find most recent open/pending conversation for this patient
        query = (
            select(Conversation)
            .where(
                and_(
                    Conversation.tenant_id == tenant_id,
                    Conversation.patient_id == patient_id,
                    Conversation.channel_type == channel_type,
                    Conversation.status.in_(["open", "pending"])
                )
            )
            .order_by(desc(Conversation.last_message_at))
            .limit(1)
        )

        result = self.db.execute(query)
        conversation = result.scalar_one_or_none()

        if conversation:
            return conversation

        # Create new conversation
        conversation = Conversation(
            id=uuid4(),
            tenant_id=tenant_id,
            patient_id=patient_id,
            channel_type=channel_type,
            status="open",
            priority="p2",
            participant_phone=phone,
            message_count=0
        )

        self.db.add(conversation)
        self.db.flush()

        logger.info(f"Created new conversation {conversation.id} for patient {patient_id}")

        return conversation

    def _store_message(
        self,
        conversation_id: UUID,
        message_sid: str,
        direction: MessageDirection,
        from_number: str,
        to_number: str,
        text_body: str,
        media_urls: List[str],
        media_types: List[str],
        profile_name: Optional[str] = None,
        wa_id: Optional[str] = None
    ) -> ConversationMessage:
        """Store message in database"""

        # Determine actor type
        actor_type = "patient" if direction == MessageDirection.INBOUND else "agent"

        # Determine content type
        if media_urls:
            content_type = "media"
        else:
            content_type = "text"

        message = ConversationMessage(
            id=uuid4(),
            conversation_id=conversation_id,
            twilio_message_sid=message_sid,
            direction=direction.value,
            actor_type=actor_type,
            content_type=content_type,
            text_body=text_body,
            media_url=media_urls[0] if media_urls else None,
            media_type=media_types[0] if media_types else None,
            delivery_status="received" if direction == MessageDirection.INBOUND else "queued",
            metadata={
                "from": from_number,
                "to": to_number,
                "profile_name": profile_name,
                "wa_id": wa_id,
                "all_media_urls": media_urls,
                "all_media_types": media_types
            }
        )

        self.db.add(message)
        self.db.flush()

        return message

    def _extract_media_urls(self, webhook: TwilioWebhookRequest) -> List[str]:
        """Extract all media URLs from webhook"""
        urls = []
        num_media = int(webhook.NumMedia or "0")

        for i in range(num_media):
            media_url = getattr(webhook, f"MediaUrl{i}", None)
            if media_url:
                urls.append(media_url)

        return urls

    def _extract_media_types(self, webhook: TwilioWebhookRequest) -> List[str]:
        """Extract all media content types from webhook"""
        types = []
        num_media = int(webhook.NumMedia or "0")

        for i in range(num_media):
            media_type = getattr(webhook, f"MediaContentType{i}", None)
            if media_type:
                types.append(media_type)

        return types


def get_whatsapp_webhook_service(db: Session) -> WhatsAppWebhookService:
    """Dependency injection for WhatsAppWebhookService"""
    return WhatsAppWebhookService(db)
