"""
Messaging Service Tests
EPIC-015: Unit tests for provider messaging service
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from modules.provider_collaboration.services.messaging_service import MessagingService
from modules.provider_collaboration.schemas import (
    PresenceUpdate, ConversationCreate, MessageCreate,
    PresenceStatusSchema, ConversationTypeSchema, MessageTypeSchema, MessagePrioritySchema
)
from modules.provider_collaboration.models import (
    PresenceStatus, ConversationType, MessageType, MessagePriority
)


class TestMessagingService:
    """Tests for MessagingService"""

    @pytest.fixture
    def service(self):
        return MessagingService()

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def provider_id(self):
        return uuid4()

    @pytest.fixture
    def tenant_id(self):
        return uuid4()

    # ==================== Presence Tests ====================

    @pytest.mark.asyncio
    async def test_update_presence_new_provider(self, service, mock_db, provider_id, tenant_id):
        """Test creating presence for new provider"""
        # Setup mock - no existing presence
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        update = PresenceUpdate(
            status=PresenceStatusSchema.AVAILABLE,
            status_message="Ready to help",
            available_for_consult=True
        )

        # Execute
        result = await service.update_presence(
            mock_db, provider_id, tenant_id, update,
            {"user_agent": "Test", "device_id": "test-device"},
            "127.0.0.1"
        )

        # Verify
        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_update_presence_existing_provider(self, service, mock_db, provider_id, tenant_id):
        """Test updating presence for existing provider"""
        # Setup mock - existing presence
        existing_presence = MagicMock()
        existing_presence.provider_id = provider_id
        existing_presence.tenant_id = tenant_id
        existing_presence.status = PresenceStatus.OFFLINE
        existing_presence.created_at = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_presence
        mock_db.execute.return_value = mock_result

        update = PresenceUpdate(
            status=PresenceStatusSchema.AVAILABLE,
            status_message="Online now"
        )

        # Execute
        result = await service.update_presence(
            mock_db, provider_id, tenant_id, update, {}, "127.0.0.1"
        )

        # Verify
        assert existing_presence.status == PresenceStatus.AVAILABLE
        assert existing_presence.status_message == "Online now"
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_get_presence_found(self, service, mock_db, provider_id, tenant_id):
        """Test getting presence for existing provider"""
        presence = MagicMock()
        presence.provider_id = provider_id
        presence.tenant_id = tenant_id
        presence.status = PresenceStatus.AVAILABLE
        presence.status_message = "Ready"
        presence.available_for_consult = True
        presence.last_activity = datetime.now(timezone.utc)
        presence.current_device = "device-1"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = presence
        mock_db.execute.return_value = mock_result

        result = await service.get_presence(mock_db, provider_id, tenant_id)

        assert result.provider_id == provider_id
        assert result.status == "available"

    @pytest.mark.asyncio
    async def test_get_presence_not_found(self, service, mock_db, provider_id, tenant_id):
        """Test getting presence for non-existent provider"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Provider presence not found"):
            await service.get_presence(mock_db, provider_id, tenant_id)

    @pytest.mark.asyncio
    async def test_get_bulk_presence(self, service, mock_db, tenant_id):
        """Test getting presence for multiple providers"""
        provider_ids = [uuid4() for _ in range(3)]

        presences = []
        for pid in provider_ids:
            p = MagicMock()
            p.provider_id = pid
            p.status = PresenceStatus.AVAILABLE
            p.status_message = None
            p.available_for_consult = True
            p.last_activity = datetime.now(timezone.utc)
            p.current_device = None
            presences.append(p)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = presences
        mock_db.execute.return_value = mock_result

        result = await service.get_bulk_presence(mock_db, provider_ids, tenant_id)

        assert len(result.presences) == 3

    # ==================== Conversation Tests ====================

    @pytest.mark.asyncio
    async def test_create_conversation_direct(self, service, mock_db, provider_id, tenant_id):
        """Test creating a direct conversation"""
        other_provider_id = uuid4()

        # Mock no existing conversation
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        data = ConversationCreate(
            type=ConversationTypeSchema.DIRECT,
            participant_ids=[other_provider_id]
        )

        result = await service.create_conversation(
            mock_db, provider_id, tenant_id, data, "127.0.0.1"
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_create_conversation_group(self, service, mock_db, provider_id, tenant_id):
        """Test creating a group conversation"""
        participant_ids = [uuid4() for _ in range(3)]

        data = ConversationCreate(
            type=ConversationTypeSchema.GROUP,
            name="Care Team Discussion",
            participant_ids=participant_ids
        )

        # Mock execute for ID generation check
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.create_conversation(
            mock_db, provider_id, tenant_id, data, "127.0.0.1"
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_create_direct_conversation_already_exists(self, service, mock_db, provider_id, tenant_id):
        """Test that existing direct conversations are returned"""
        other_provider_id = uuid4()

        existing_conv = MagicMock()
        existing_conv.id = uuid4()
        existing_conv.tenant_id = tenant_id
        existing_conv.type = ConversationType.DIRECT
        existing_conv.name = None
        existing_conv.patient_id = None
        existing_conv.created_by = provider_id
        existing_conv.is_encrypted = True
        existing_conv.created_at = datetime.now(timezone.utc)
        existing_conv.participants = []
        existing_conv.last_message_at = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_conv
        mock_db.execute.return_value = mock_result

        data = ConversationCreate(
            type=ConversationTypeSchema.DIRECT,
            participant_ids=[other_provider_id]
        )

        result = await service.create_conversation(
            mock_db, provider_id, tenant_id, data, "127.0.0.1"
        )

        # Should return existing conversation
        assert result.id == existing_conv.id

    # ==================== Message Tests ====================

    @pytest.mark.asyncio
    async def test_send_message_success(self, service, mock_db, provider_id, tenant_id):
        """Test sending a message successfully"""
        conversation_id = uuid4()

        # Mock conversation with participant
        conversation = MagicMock()
        conversation.id = conversation_id
        conversation.tenant_id = tenant_id
        conversation.participants = [MagicMock(provider_id=provider_id)]
        conversation.settings = {}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = conversation
        mock_db.execute.return_value = mock_result

        data = MessageCreate(
            content="Hello, can you consult on this patient?",
            message_type=MessageTypeSchema.TEXT
        )

        result = await service.send_message(
            mock_db, provider_id, tenant_id, conversation_id, data, "127.0.0.1"
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_send_message_not_participant(self, service, mock_db, provider_id, tenant_id):
        """Test that non-participants cannot send messages"""
        conversation_id = uuid4()
        other_provider = uuid4()

        conversation = MagicMock()
        conversation.id = conversation_id
        conversation.tenant_id = tenant_id
        conversation.participants = [MagicMock(provider_id=other_provider)]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = conversation
        mock_db.execute.return_value = mock_result

        data = MessageCreate(content="Test message")

        with pytest.raises(ValueError, match="Not a participant"):
            await service.send_message(
                mock_db, provider_id, tenant_id, conversation_id, data, "127.0.0.1"
            )

    @pytest.mark.asyncio
    async def test_phi_detection_ssn(self, service, mock_db, provider_id, tenant_id):
        """Test PHI detection for SSN patterns"""
        has_phi, types = service._detect_phi("Patient SSN is 123-45-6789")

        assert has_phi is True
        assert "ssn" in types

    @pytest.mark.asyncio
    async def test_phi_detection_mrn(self, service, mock_db, provider_id, tenant_id):
        """Test PHI detection for MRN patterns"""
        has_phi, types = service._detect_phi("MRN: MRN12345678")

        assert has_phi is True
        assert "mrn" in types

    @pytest.mark.asyncio
    async def test_phi_detection_email(self, service, mock_db, provider_id, tenant_id):
        """Test PHI detection for email patterns"""
        has_phi, types = service._detect_phi("Contact: patient@email.com")

        assert has_phi is True
        assert "email" in types

    @pytest.mark.asyncio
    async def test_phi_detection_phone(self, service, mock_db, provider_id, tenant_id):
        """Test PHI detection for phone patterns"""
        has_phi, types = service._detect_phi("Call 555-123-4567")

        assert has_phi is True
        assert "phone" in types

    @pytest.mark.asyncio
    async def test_phi_detection_clean(self, service, mock_db, provider_id, tenant_id):
        """Test PHI detection for clean message"""
        has_phi, types = service._detect_phi("Please review the patient labs")

        assert has_phi is False
        assert len(types) == 0

    @pytest.mark.asyncio
    async def test_add_reaction(self, service, mock_db, provider_id):
        """Test adding a reaction to a message"""
        message_id = uuid4()

        message = MagicMock()
        message.id = message_id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = message
        mock_db.execute.return_value = mock_result

        await service.add_reaction(mock_db, provider_id, message_id, "👍")

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_recall_message_own_message(self, service, mock_db, provider_id):
        """Test recalling own message"""
        message_id = uuid4()

        message = MagicMock()
        message.id = message_id
        message.sender_id = provider_id
        message.recalled = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = message
        mock_db.execute.return_value = mock_result

        await service.recall_message(mock_db, provider_id, message_id)

        assert message.recalled is True
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_recall_message_not_sender(self, service, mock_db, provider_id):
        """Test that non-senders cannot recall messages"""
        message_id = uuid4()
        other_provider = uuid4()

        message = MagicMock()
        message.id = message_id
        message.sender_id = other_provider
        message.recalled = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = message
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Can only recall your own messages"):
            await service.recall_message(mock_db, provider_id, message_id)


class TestMessagingServiceIntegration:
    """Integration-style tests for MessagingService"""

    @pytest.fixture
    def service(self):
        return MessagingService()

    def test_presence_staleness_threshold(self, service):
        """Test that presence staleness is configured correctly"""
        assert service.presence_staleness_minutes == 5

    def test_phi_patterns_comprehensive(self, service):
        """Test that PHI patterns are comprehensive"""
        # SSN variations
        assert service._detect_phi("123-45-6789")[0]
        assert service._detect_phi("123 45 6789")[0]

        # MRN variations
        assert service._detect_phi("MRN123456")[0]
        assert service._detect_phi("MRN: 123456")[0]

        # Date of birth
        assert service._detect_phi("DOB: 01/15/1990")[0]
        assert service._detect_phi("Date of birth 1990-01-15")[0]

        # Credit card
        assert service._detect_phi("Card: 4111111111111111")[0]
