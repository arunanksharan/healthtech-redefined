"""
Tests for WhatsApp Webhook Service
Tests Twilio WhatsApp webhook processing
"""
import pytest
from uuid import uuid4
from datetime import datetime

from modules.whatsapp_webhooks.service import WhatsAppWebhookService
from modules.whatsapp_webhooks.schemas import (
    TwilioWebhookRequest,
    WhatsAppStatusWebhook,
    SendWhatsAppMessageRequest,
    MessageDirection
)
from shared.database.conversation_voice_models import Conversation, ConversationMessage


class TestWhatsAppWebhookService:
    """Test suite for WhatsAppWebhookService"""

    @pytest.fixture
    def whatsapp_service(self, db_session):
        """Create WhatsApp webhook service instance"""
        return WhatsAppWebhookService(db_session)

    @pytest.fixture
    def mock_twilio_webhook(self):
        """Mock Twilio webhook payload"""
        return TwilioWebhookRequest(
            MessageSid=f"SM{uuid4().hex[:32]}",
            AccountSid=f"AC{uuid4().hex[:32]}",
            From="whatsapp:+1234567890",
            To="whatsapp:+0987654321",
            Body="Hello, I need help booking an appointment",
            NumMedia="0",
            ProfileName="John Doe",
            WaId="1234567890"
        )

    @pytest.mark.asyncio
    async def test_process_incoming_message_new_patient(
        self,
        whatsapp_service,
        db_session,
        test_org_id,
        mock_twilio_webhook
    ):
        """Test processing message from new patient"""
        result = await whatsapp_service.process_incoming_message(
            mock_twilio_webhook,
            test_org_id
        )

        assert result.success is True
        assert result.conversation_id is not None
        assert result.message_id is not None
        assert "patient_created" in result.actions_taken
        assert "conversation_created" in result.actions_taken
        assert "message_stored" in result.actions_taken

        # Verify patient was created
        from shared.database.models import Patient
        from sqlalchemy import select
        query = select(Patient).where(Patient.phone_number == "+1234567890")
        patient = db_session.execute(query).scalar_one_or_none()
        assert patient is not None
        assert patient.phone_number == "+1234567890"

    @pytest.mark.asyncio
    async def test_process_incoming_message_existing_patient(
        self,
        whatsapp_service,
        db_session,
        test_org_id,
        test_patient,
        mock_twilio_webhook
    ):
        """Test processing message from existing patient"""
        # Update mock to use existing patient's phone
        mock_twilio_webhook.From = f"whatsapp:{test_patient.phone_primary}"

        result = await whatsapp_service.process_incoming_message(
            mock_twilio_webhook,
            test_org_id
        )

        assert result.success is True
        assert "patient_created" not in result.actions_taken
        assert "message_stored" in result.actions_taken

    @pytest.mark.asyncio
    async def test_process_incoming_message_creates_conversation(
        self,
        whatsapp_service,
        db_session,
        test_org_id,
        mock_twilio_webhook
    ):
        """Test conversation creation on first message"""
        result = await whatsapp_service.process_incoming_message(
            mock_twilio_webhook,
            test_org_id
        )

        # Verify conversation was created
        from sqlalchemy import select
        query = select(Conversation).where(
            Conversation.id == result.conversation_id
        )
        conversation = db_session.execute(query).scalar_one_or_none()

        assert conversation is not None
        assert conversation.channel_type == "whatsapp"
        assert conversation.status == "open"
        assert conversation.message_count > 0

    @pytest.mark.asyncio
    async def test_process_incoming_message_with_media(
        self,
        whatsapp_service,
        test_org_id,
        mock_twilio_webhook
    ):
        """Test processing message with media attachments"""
        mock_twilio_webhook.NumMedia = "1"
        mock_twilio_webhook.MediaUrl0 = "https://api.twilio.com/media/image.jpg"
        mock_twilio_webhook.MediaContentType0 = "image/jpeg"

        result = await whatsapp_service.process_incoming_message(
            mock_twilio_webhook,
            test_org_id
        )

        assert result.success is True
        assert result.message_id is not None

    @pytest.mark.asyncio
    async def test_process_incoming_message_reopens_closed_conversation(
        self,
        whatsapp_service,
        db_session,
        test_org_id,
        test_patient,
        mock_twilio_webhook
    ):
        """Test that closed conversation is reopened on new message"""
        # Create a closed conversation
        conversation = Conversation(
            id=uuid4(),
            tenant_id=test_org_id,
            patient_id=test_patient.id,
            channel_type="whatsapp",
            status="closed",
            priority="p2",
            participant_phone=test_patient.phone_primary,
            message_count=5
        )
        db_session.add(conversation)
        db_session.commit()

        # Update mock to use existing patient's phone
        mock_twilio_webhook.From = f"whatsapp:{test_patient.phone_primary}"

        result = await whatsapp_service.process_incoming_message(
            mock_twilio_webhook,
            test_org_id
        )

        assert result.success is True
        assert "conversation_reopened" in result.actions_taken

        # Verify conversation is now open
        db_session.refresh(conversation)
        assert conversation.status == "open"

    @pytest.mark.asyncio
    async def test_process_status_update(
        self,
        whatsapp_service,
        db_session,
        test_org_id
    ):
        """Test processing message status update"""
        # First create a conversation and message
        conversation = Conversation(
            id=uuid4(),
            tenant_id=test_org_id,
            channel_type="whatsapp",
            status="open",
            priority="p2",
            participant_phone="+1234567890",
            message_count=1
        )
        db_session.add(conversation)

        message_sid = f"SM{uuid4().hex[:32]}"
        message = ConversationMessage(
            id=uuid4(),
            conversation_id=conversation.id,
            twilio_message_sid=message_sid,
            direction="outbound",
            actor_type="agent",
            content_type="text",
            text_body="Test message",
            delivery_status="sent"
        )
        db_session.add(message)
        db_session.commit()

        # Process status update
        status_webhook = WhatsAppStatusWebhook(
            MessageSid=message_sid,
            MessageStatus="delivered",
            AccountSid=f"AC{uuid4().hex[:32]}",
            From="whatsapp:+0987654321",
            To="whatsapp:+1234567890"
        )

        result = await whatsapp_service.process_status_update(
            status_webhook,
            test_org_id
        )

        assert result.success is True
        assert "status_updated" in result.actions_taken

        # Verify status was updated
        db_session.refresh(message)
        assert message.delivery_status == "delivered"

    @pytest.mark.asyncio
    async def test_send_message(
        self,
        whatsapp_service,
        db_session,
        test_org_id,
        test_patient
    ):
        """Test sending outbound WhatsApp message"""
        # Create conversation
        conversation = Conversation(
            id=uuid4(),
            tenant_id=test_org_id,
            patient_id=test_patient.id,
            channel_type="whatsapp",
            status="open",
            priority="p2",
            participant_phone=test_patient.phone_primary,
            message_count=0
        )
        db_session.add(conversation)
        db_session.commit()

        request = SendWhatsAppMessageRequest(
            to=test_patient.phone_primary,
            body="Your appointment is confirmed",
            conversation_id=str(conversation.id)
        )

        result = await whatsapp_service.send_message(request, test_org_id)

        assert result.message_sid is not None
        assert result.status == "queued"
        assert result.conversation_id == str(conversation.id)

        # Verify message was stored
        db_session.refresh(conversation)
        assert conversation.message_count == 1


class TestWhatsAppHelperMethods:
    """Test helper methods in WhatsAppWebhookService"""

    @pytest.fixture
    def whatsapp_service(self, db_session):
        return WhatsAppWebhookService(db_session)

    def test_identify_or_create_patient_new(
        self,
        whatsapp_service,
        test_org_id
    ):
        """Test patient creation"""
        patient_id, created = whatsapp_service._identify_or_create_patient(
            phone="+1234567890",
            name="John Doe",
            tenant_id=test_org_id
        )

        assert created is True
        assert patient_id is not None

    def test_identify_or_create_patient_existing(
        self,
        whatsapp_service,
        test_patient
    ):
        """Test patient identification"""
        patient_id, created = whatsapp_service._identify_or_create_patient(
            phone=test_patient.phone_primary,
            name="John Doe",
            tenant_id=test_patient.tenant_id
        )

        assert created is False
        assert patient_id == test_patient.id

    def test_find_or_create_conversation_new(
        self,
        whatsapp_service,
        test_org_id,
        test_patient
    ):
        """Test conversation creation"""
        conversation = whatsapp_service._find_or_create_conversation(
            tenant_id=test_org_id,
            patient_id=test_patient.id,
            phone=test_patient.phone_primary,
            channel_type="whatsapp"
        )

        assert conversation is not None
        assert conversation.channel_type == "whatsapp"
        assert conversation.status == "open"

    def test_extract_media_urls(self, whatsapp_service):
        """Test media URL extraction"""
        webhook = TwilioWebhookRequest(
            MessageSid="SM123",
            AccountSid="AC123",
            From="whatsapp:+1234567890",
            To="whatsapp:+0987654321",
            Body="Check out these images",
            NumMedia="2",
            MediaUrl0="https://example.com/image1.jpg",
            MediaContentType0="image/jpeg",
            MediaUrl1="https://example.com/image2.jpg",
            MediaContentType1="image/jpeg"
        )

        urls = whatsapp_service._extract_media_urls(webhook)

        assert len(urls) == 2
        assert urls[0] == "https://example.com/image1.jpg"
        assert urls[1] == "https://example.com/image2.jpg"

    def test_extract_media_types(self, whatsapp_service):
        """Test media type extraction"""
        webhook = TwilioWebhookRequest(
            MessageSid="SM123",
            AccountSid="AC123",
            From="whatsapp:+1234567890",
            To="whatsapp:+0987654321",
            Body="Media message",
            NumMedia="2",
            MediaUrl0="https://example.com/image.jpg",
            MediaContentType0="image/jpeg",
            MediaUrl1="https://example.com/video.mp4",
            MediaContentType1="video/mp4"
        )

        types = whatsapp_service._extract_media_types(webhook)

        assert len(types) == 2
        assert types[0] == "image/jpeg"
        assert types[1] == "video/mp4"


@pytest.mark.asyncio
class TestWhatsAppEdgeCases:
    """Test edge cases and error handling"""

    @pytest.fixture
    def whatsapp_service(self, db_session):
        return WhatsAppWebhookService(db_session)

    async def test_status_update_for_nonexistent_message(
        self,
        whatsapp_service,
        test_org_id
    ):
        """Test status update for message that doesn't exist"""
        status_webhook = WhatsAppStatusWebhook(
            MessageSid="SM_NONEXISTENT",
            MessageStatus="delivered",
            AccountSid="AC123",
            From="whatsapp:+1234567890",
            To="whatsapp:+0987654321"
        )

        result = await whatsapp_service.process_status_update(
            status_webhook,
            test_org_id
        )

        assert result.success is False
        assert "message_not_found" in result.actions_taken

    async def test_message_with_no_body(
        self,
        whatsapp_service,
        test_org_id
    ):
        """Test processing message with empty body"""
        webhook = TwilioWebhookRequest(
            MessageSid="SM123",
            AccountSid="AC123",
            From="whatsapp:+1234567890",
            To="whatsapp:+0987654321",
            Body="",  # Empty body
            NumMedia="0"
        )

        result = await whatsapp_service.process_incoming_message(
            webhook,
            test_org_id
        )

        # Should still process successfully
        assert result.success is True

    async def test_message_with_location(
        self,
        whatsapp_service,
        test_org_id
    ):
        """Test processing message with location data"""
        webhook = TwilioWebhookRequest(
            MessageSid="SM123",
            AccountSid="AC123",
            From="whatsapp:+1234567890",
            To="whatsapp:+0987654321",
            Body="Sharing my location",
            NumMedia="0",
            Latitude="37.7749",
            Longitude="-122.4194"
        )

        result = await whatsapp_service.process_incoming_message(
            webhook,
            test_org_id
        )

        assert result.success is True
