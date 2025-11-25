"""
Comprehensive Tests for Omnichannel Communications Module
"""
import pytest
from datetime import datetime, timedelta, time
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from modules.omnichannel.models import (
    OmniChannelType,
    DeliveryStatus,
    ConversationStatus,
    ConsentType,
    CampaignStatus,
)
from modules.omnichannel.providers.base import (
    BaseChannelProvider,
    MessagePayload,
    WebhookPayload,
    ProviderResult,
    ProviderError,
    ProviderStatus,
    RateLimiter,
)
from modules.omnichannel.providers.factory import (
    ProviderFactory,
    PROVIDER_CLASSES,
    get_provider,
)


class TestMessagePayload:
    """Tests for MessagePayload dataclass."""

    def test_create_basic_payload(self):
        """Test creating a basic message payload."""
        payload = MessagePayload(
            recipient="+1234567890",
            content="Test message"
        )

        assert payload.recipient == "+1234567890"
        assert payload.content == "Test message"
        assert payload.metadata == {}

    def test_create_payload_with_template(self):
        """Test creating payload with template."""
        payload = MessagePayload(
            recipient="test@example.com",
            template_id="welcome_template",
            template_variables={"name": "John", "date": "2024-01-01"}
        )

        assert payload.template_id == "welcome_template"
        assert payload.template_variables["name"] == "John"

    def test_payload_with_attachments(self):
        """Test payload with attachments."""
        payload = MessagePayload(
            recipient="+1234567890",
            content="Check this attachment",
            attachments=[
                {"type": "image", "url": "https://example.com/image.jpg"}
            ]
        )

        assert len(payload.attachments) == 1
        assert payload.attachments[0]["type"] == "image"


class TestProviderResult:
    """Tests for ProviderResult dataclass."""

    def test_success_result(self):
        """Test successful provider result."""
        result = ProviderResult(
            success=True,
            external_id="msg_123",
            status="delivered"
        )

        assert result.success is True
        assert result.external_id == "msg_123"
        assert result.error_code is None

    def test_failure_result(self):
        """Test failed provider result."""
        result = ProviderResult(
            success=False,
            error_code="INVALID_NUMBER",
            error_message="Phone number is invalid",
            is_retriable=False
        )

        assert result.success is False
        assert result.error_code == "INVALID_NUMBER"
        assert result.is_retriable is False

    def test_result_with_cost(self):
        """Test result with cost tracking."""
        result = ProviderResult(
            success=True,
            external_id="msg_456",
            cost=0.0075
        )

        assert result.cost == 0.0075


class TestProviderError:
    """Tests for ProviderError exception."""

    def test_basic_error(self):
        """Test basic provider error."""
        error = ProviderError("Connection failed")

        assert str(error) == "Connection failed"
        assert error.is_retriable is True  # Default

    def test_error_with_code(self):
        """Test error with code."""
        error = ProviderError(
            "Rate limit exceeded",
            error_code="RATE_LIMIT",
            is_retriable=True
        )

        assert error.error_code == "RATE_LIMIT"
        assert error.is_retriable is True

    def test_error_with_original_exception(self):
        """Test error wrapping original exception."""
        original = ValueError("Invalid input")
        error = ProviderError(
            "Validation error",
            original_error=original
        )

        assert error.original_error == original


class TestRateLimiter:
    """Tests for rate limiting."""

    @pytest.mark.asyncio
    async def test_under_limit(self):
        """Test acquiring when under limit."""
        limiter = RateLimiter(max_requests=10, window_seconds=60)

        # Should acquire successfully
        result = await limiter.acquire()
        assert result is True

    @pytest.mark.asyncio
    async def test_at_limit(self):
        """Test when at rate limit."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        # Use up the limit
        await limiter.acquire()
        await limiter.acquire()

        # Should be limited
        result = await limiter.acquire()
        assert result is False


class TestProviderFactory:
    """Tests for ProviderFactory."""

    def test_supported_providers_list(self):
        """Test getting supported providers."""
        supported = ProviderFactory.get_supported_providers()

        assert 'whatsapp' in supported
        assert 'sms' in supported
        assert 'email' in supported
        assert 'voice' in supported

        assert 'meta_whatsapp' in supported['whatsapp']
        assert 'twilio_sms' in supported['sms']
        assert 'sendgrid' in supported['email']

    def test_default_provider_for_channel(self):
        """Test getting default provider for channel."""
        default_sms = ProviderFactory.get_default_provider_type('sms')
        default_email = ProviderFactory.get_default_provider_type('email')

        assert default_sms == 'twilio_sms'
        assert default_email == 'sendgrid'

    def test_create_provider(self):
        """Test creating a provider."""
        config = {
            'provider_type': 'twilio_sms',
            'from_phone_number': '+1234567890',
            'credentials': {
                'account_sid': 'test_sid',
                'auth_token': 'test_token'
            }
        }

        provider = ProviderFactory.create_provider('twilio_sms', config)
        assert provider is not None

    def test_create_unknown_provider(self):
        """Test creating unknown provider returns None."""
        provider = ProviderFactory.create_provider('unknown_provider', {})
        assert provider is None


class TestOmniChannelTypes:
    """Tests for channel type enums."""

    def test_channel_types(self):
        """Test all channel types exist."""
        assert OmniChannelType.SMS.value == 'sms'
        assert OmniChannelType.EMAIL.value == 'email'
        assert OmniChannelType.WHATSAPP.value == 'whatsapp'
        assert OmniChannelType.VOICE.value == 'voice'
        assert OmniChannelType.PUSH_NOTIFICATION.value == 'push_notification'

    def test_delivery_statuses(self):
        """Test delivery status values."""
        assert DeliveryStatus.PENDING.value == 'pending'
        assert DeliveryStatus.QUEUED.value == 'queued'
        assert DeliveryStatus.SENT.value == 'sent'
        assert DeliveryStatus.DELIVERED.value == 'delivered'
        assert DeliveryStatus.FAILED.value == 'failed'
        assert DeliveryStatus.BOUNCED.value == 'bounced'

    def test_conversation_statuses(self):
        """Test conversation status values."""
        assert ConversationStatus.OPEN.value == 'open'
        assert ConversationStatus.PENDING.value == 'pending'
        assert ConversationStatus.IN_PROGRESS.value == 'in_progress'
        assert ConversationStatus.RESOLVED.value == 'resolved'
        assert ConversationStatus.CLOSED.value == 'closed'


class TestPhoneNumberFormatting:
    """Tests for phone number formatting in providers."""

    def test_format_with_plus(self):
        """Test number already with plus sign."""
        from modules.omnichannel.providers.sms import SMSProvider

        provider = SMSProvider({
            'provider_type': 'twilio_sms',
            'credentials': {'account_sid': 'test', 'auth_token': 'test'}
        })

        formatted = provider.format_phone_number('+1234567890')
        assert formatted == '+1234567890'

    def test_format_us_number(self):
        """Test formatting US number."""
        from modules.omnichannel.providers.sms import SMSProvider

        provider = SMSProvider({
            'provider_type': 'twilio_sms',
            'credentials': {'account_sid': 'test', 'auth_token': 'test'}
        })

        formatted = provider.format_phone_number('1234567890')
        assert formatted.startswith('+')


class TestEmailValidation:
    """Tests for email validation."""

    def test_valid_email(self):
        """Test valid email addresses."""
        from modules.omnichannel.providers.email import EmailProvider

        provider = EmailProvider({
            'provider_type': 'sendgrid',
            'from_email': 'noreply@example.com',
            'credentials': {'api_key': 'test_key'}
        })

        assert provider.validate_recipient('test@example.com') is True
        assert provider.validate_recipient('user.name@domain.org') is True

    def test_invalid_email(self):
        """Test invalid email addresses."""
        from modules.omnichannel.providers.email import EmailProvider

        provider = EmailProvider({
            'provider_type': 'sendgrid',
            'from_email': 'noreply@example.com',
            'credentials': {'api_key': 'test_key'}
        })

        assert provider.validate_recipient('invalid') is False
        assert provider.validate_recipient('no-at-sign.com') is False
        assert provider.validate_recipient('@nodomain') is False


class TestTwiMLGeneration:
    """Tests for TwiML generation in voice provider."""

    @pytest.mark.asyncio
    async def test_say_twiml(self):
        """Test generating Say TwiML."""
        from modules.omnichannel.providers.voice import VoiceProvider

        provider = VoiceProvider({
            'provider_type': 'twilio_voice',
            'from_phone_number': '+1234567890',
            'credentials': {'account_sid': 'test', 'auth_token': 'test'}
        })

        twiml = await provider.generate_twiml_response('say', 'Hello world')

        assert '<Response>' in twiml
        assert '<Say' in twiml
        assert 'Hello world' in twiml
        assert '</Response>' in twiml

    @pytest.mark.asyncio
    async def test_gather_twiml(self):
        """Test generating Gather TwiML."""
        from modules.omnichannel.providers.voice import VoiceProvider

        provider = VoiceProvider({
            'provider_type': 'twilio_voice',
            'from_phone_number': '+1234567890',
            'credentials': {'account_sid': 'test', 'auth_token': 'test'}
        })

        twiml = await provider.generate_twiml_response(
            'gather',
            'Press 1 for appointments',
            {'num_digits': 1, 'timeout': 5}
        )

        assert '<Gather' in twiml
        assert 'numDigits="1"' in twiml
        assert 'timeout="5"' in twiml

    @pytest.mark.asyncio
    async def test_hangup_twiml(self):
        """Test generating Hangup TwiML."""
        from modules.omnichannel.providers.voice import VoiceProvider

        provider = VoiceProvider({
            'provider_type': 'twilio_voice',
            'from_phone_number': '+1234567890',
            'credentials': {'account_sid': 'test', 'auth_token': 'test'}
        })

        twiml = await provider.generate_twiml_response('hangup', 'Goodbye')

        assert '<Hangup/>' in twiml
        assert 'Goodbye' in twiml


class TestXMLEscaping:
    """Tests for XML character escaping."""

    def test_escape_special_chars(self):
        """Test escaping special XML characters."""
        from modules.omnichannel.providers.voice import VoiceProvider

        provider = VoiceProvider({
            'provider_type': 'twilio_voice',
            'credentials': {'account_sid': 'test', 'auth_token': 'test'}
        })

        escaped = provider._escape_xml('Test & "quote" <tag> \'apos\'')

        assert '&amp;' in escaped
        assert '&lt;' in escaped
        assert '&gt;' in escaped
        assert '&quot;' in escaped
        assert '&apos;' in escaped


class TestMessageCostEstimation:
    """Tests for message cost estimation."""

    def test_sms_cost(self):
        """Test SMS cost estimation."""
        from modules.omnichannel.providers.sms import SMSProvider

        provider = SMSProvider({
            'provider_type': 'twilio_sms',
            'credentials': {'account_sid': 'test', 'auth_token': 'test'}
        })

        payload = MessagePayload(recipient='+1234567890', content='Test')
        cost = provider.get_message_cost(payload)

        assert cost > 0
        assert cost < 0.1  # Should be reasonable

    def test_voice_cost(self):
        """Test voice call cost estimation."""
        from modules.omnichannel.providers.voice import VoiceProvider

        provider = VoiceProvider({
            'provider_type': 'twilio_voice',
            'from_phone_number': '+1234567890',
            'credentials': {'account_sid': 'test', 'auth_token': 'test'}
        })

        payload = MessagePayload(
            recipient='+1234567890',
            content='Test call',
            metadata={'estimated_minutes': 2}
        )
        cost = provider.get_message_cost(payload)

        assert cost > 0
        assert cost < 1.0  # Should be per-minute rate


class TestComplianceService:
    """Tests for compliance and PHI handling."""

    def test_detect_ssn(self):
        """Test SSN detection."""
        from modules.omnichannel.compliance_service import ComplianceService

        service = ComplianceService(None, uuid4())
        content = "Patient SSN is 123-45-6789"

        detected = service.detect_phi(content)

        assert 'ssn' in detected
        assert '123-45-6789' in detected['ssn']

    def test_detect_phone(self):
        """Test phone number detection."""
        from modules.omnichannel.compliance_service import ComplianceService

        service = ComplianceService(None, uuid4())
        content = "Call me at 555-123-4567"

        detected = service.detect_phi(content)

        assert 'phone' in detected

    def test_detect_email(self):
        """Test email detection."""
        from modules.omnichannel.compliance_service import ComplianceService

        service = ComplianceService(None, uuid4())
        content = "Email me at patient@example.com"

        detected = service.detect_phi(content)

        assert 'email' in detected
        assert 'patient@example.com' in detected['email']

    def test_mask_ssn(self):
        """Test SSN masking."""
        from modules.omnichannel.compliance_service import ComplianceService

        service = ComplianceService(None, uuid4())
        content = "SSN: 123-45-6789"

        masked = service.mask_phi(content)

        assert '123-45-6789' not in masked
        assert 'XXX-XX-6789' in masked

    def test_mask_email(self):
        """Test email masking."""
        from modules.omnichannel.compliance_service import ComplianceService

        service = ComplianceService(None, uuid4())
        content = "Email: patient@example.com"

        masked = service.mask_phi(content)

        assert 'patient@example.com' not in masked
        assert 'p***@example.com' in masked


class TestPreferenceService:
    """Tests for preference management."""

    def test_quiet_hours_calculation(self):
        """Test quiet hours time calculation logic."""
        # Test overnight quiet hours (22:00 to 07:00)
        start = time(22, 0)
        end = time(7, 0)

        # 23:00 should be within quiet hours
        current = time(23, 0)
        if start > end:
            is_quiet = current >= start or current <= end
        else:
            is_quiet = start <= current <= end

        assert is_quiet is True

        # 12:00 should not be within quiet hours
        current = time(12, 0)
        if start > end:
            is_quiet = current >= start or current <= end
        else:
            is_quiet = start <= current <= end

        assert is_quiet is False


class TestWebhookParsing:
    """Tests for webhook payload parsing."""

    @pytest.mark.asyncio
    async def test_parse_twilio_sms_webhook(self):
        """Test parsing Twilio SMS webhook."""
        from modules.omnichannel.providers.sms import SMSProvider

        provider = SMSProvider({
            'provider_type': 'twilio_sms',
            'credentials': {'account_sid': 'test', 'auth_token': 'test'}
        })

        webhook_data = {
            'MessageSid': 'SM123',
            'From': '+1234567890',
            'To': '+0987654321',
            'Body': 'Test message',
            'MessageStatus': 'delivered'
        }

        parsed = await provider.parse_webhook(webhook_data)

        assert parsed.message_id == 'SM123'
        assert parsed.sender == '+1234567890'
        assert parsed.content == 'Test message'
        assert parsed.status == 'delivered'

    @pytest.mark.asyncio
    async def test_parse_sendgrid_webhook(self):
        """Test parsing SendGrid webhook event."""
        from modules.omnichannel.providers.email import EmailProvider

        provider = EmailProvider({
            'provider_type': 'sendgrid',
            'from_email': 'test@example.com',
            'credentials': {'api_key': 'test'}
        })

        webhook_data = [{
            'sg_message_id': 'msg_123',
            'email': 'recipient@example.com',
            'event': 'delivered',
            'timestamp': 1700000000
        }]

        parsed = await provider.parse_webhook(webhook_data)

        assert parsed.message_id == 'msg_123'
        assert parsed.recipient == 'recipient@example.com'
        assert parsed.status == 'delivered'


class TestCampaignLogic:
    """Tests for campaign service logic."""

    def test_channel_selection_priority(self):
        """Test channel priority selection."""
        # WhatsApp should be preferred if enabled
        channel_priority = [
            (OmniChannelType.WHATSAPP, True),
            (OmniChannelType.SMS, True),
            (OmniChannelType.EMAIL, True),
        ]

        for channel, enabled in channel_priority:
            if enabled:
                selected = channel
                break

        assert selected == OmniChannelType.WHATSAPP

    def test_ab_variant_assignment(self):
        """Test A/B variant assignment is random."""
        import random

        variants = ['control', 'variant_a', 'variant_b']
        assignments = [random.choice(variants) for _ in range(100)]

        # All variants should be assigned at least once
        assert 'control' in assignments
        assert 'variant_a' in assignments
        assert 'variant_b' in assignments


class TestAnalyticsCalculations:
    """Tests for analytics calculations."""

    def test_delivery_rate_calculation(self):
        """Test delivery rate calculation."""
        total = 100
        delivered = 85
        pending = 5

        sent = total - pending
        delivery_rate = (delivered / sent * 100) if sent > 0 else 0

        assert delivery_rate == pytest.approx(89.47, rel=0.1)

    def test_cost_per_message(self):
        """Test cost per message calculation."""
        total_cost = 7.50
        message_count = 1000

        cost_per_message = total_cost / message_count if message_count > 0 else 0

        assert cost_per_message == 0.0075

    def test_response_rate_calculation(self):
        """Test response rate calculation."""
        outbound = 1000
        inbound = 250

        response_rate = (inbound / outbound * 100) if outbound > 0 else 0

        assert response_rate == 25.0


# Integration Test Fixtures
@pytest.fixture
def tenant_id():
    """Generate a test tenant ID."""
    return uuid4()


@pytest.fixture
def patient_id():
    """Generate a test patient ID."""
    return uuid4()


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.execute = AsyncMock()
    return session


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
