"""
Omnichannel Communications Module
EPIC-013: Omnichannel Communications Platform

This module provides a unified multi-channel communication platform for healthcare:

1. Multi-Channel Message Delivery
   - WhatsApp (Meta Cloud API, Twilio)
   - SMS (Twilio, AWS SNS, MessageBird, Vonage)
   - Email (SendGrid, AWS SES)
   - Voice (Twilio Voice, AWS Connect)
   - Push Notifications (Firebase)

2. Unified Conversation Management
   - Cross-channel conversation threading
   - Patient context preservation
   - Smart channel routing
   - Conversation history

3. Communication Preferences
   - Patient-controlled channel preferences
   - Consent management (TCPA/GDPR compliant)
   - Opt-out handling
   - Quiet hours management

4. Provider Management
   - Multi-provider support per channel
   - Automatic failover
   - Rate limiting
   - Health monitoring

5. Template Management
   - Multi-channel templates
   - Variable substitution
   - Approval workflows
   - Version control

6. Campaign Management
   - Multi-channel campaigns
   - Patient segmentation
   - A/B testing
   - Performance analytics

7. Unified Inbox
   - Cross-channel message aggregation
   - Agent assignment
   - Priority routing
   - Canned responses

8. Analytics & Compliance
   - Delivery tracking
   - Engagement metrics
   - HIPAA audit logging
   - Cost analytics
"""

from modules.omnichannel.router import router
from modules.omnichannel.service import OmnichannelService
from modules.omnichannel.schemas import (
    # Messages
    SendMessageRequest,
    SendMessageResponse,
    BulkSendRequest,
    BulkSendResponse,
    MessageResponse,
    # Conversations
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationListResponse,
    # Preferences
    PreferenceCreate,
    PreferenceUpdate,
    PreferenceResponse,
    QuietHoursConfig,
    # Consent
    ConsentCreate,
    ConsentResponse,
    # Templates
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateRenderRequest,
    TemplateRenderResponse,
    # Providers
    ProviderCreate,
    ProviderUpdate,
    ProviderResponse,
    ProviderHealthResponse,
    # Campaigns
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignAnalyticsResponse,
    # Webhooks
    WhatsAppWebhookPayload,
    TwilioWebhookPayload,
    SendGridWebhookPayload,
    # Analytics
    ChannelAnalytics,
    DeliveryStats,
    EngagementStats,
    # Canned Responses
    CannedResponseCreate,
    CannedResponseResponse,
)
from modules.omnichannel.models import (
    OmniChannelType,
    DeliveryStatus,
    ConversationStatus,
    ConsentType,
    CampaignStatus,
    OmnichannelProvider,
    OmnichannelTemplate,
    OmnichannelConversation,
    OmnichannelMessage,
    CommunicationPreference,
    ConsentRecord,
    Campaign,
    CampaignRecipient,
    CannedResponse,
    ChannelAnalyticsModel,
)
from modules.omnichannel.providers import (
    BaseChannelProvider,
    ProviderFactory,
    WhatsAppProvider,
    SMSProvider,
    EmailProvider,
    VoiceProvider,
    MessagePayload,
    WebhookPayload,
    ProviderResult,
    ProviderError,
    ProviderStatus,
    get_provider,
)

__all__ = [
    # Router and Service
    "router",
    "OmnichannelService",
    # Request/Response Schemas
    "SendMessageRequest",
    "SendMessageResponse",
    "BulkSendRequest",
    "BulkSendResponse",
    "MessageResponse",
    "ConversationCreate",
    "ConversationUpdate",
    "ConversationResponse",
    "ConversationListResponse",
    "PreferenceCreate",
    "PreferenceUpdate",
    "PreferenceResponse",
    "QuietHoursConfig",
    "ConsentCreate",
    "ConsentResponse",
    "TemplateCreate",
    "TemplateUpdate",
    "TemplateResponse",
    "TemplateRenderRequest",
    "TemplateRenderResponse",
    "ProviderCreate",
    "ProviderUpdate",
    "ProviderResponse",
    "ProviderHealthResponse",
    "CampaignCreate",
    "CampaignUpdate",
    "CampaignResponse",
    "CampaignAnalyticsResponse",
    "WhatsAppWebhookPayload",
    "TwilioWebhookPayload",
    "SendGridWebhookPayload",
    "ChannelAnalytics",
    "DeliveryStats",
    "EngagementStats",
    "CannedResponseCreate",
    "CannedResponseResponse",
    # Models and Enums
    "OmniChannelType",
    "DeliveryStatus",
    "ConversationStatus",
    "ConsentType",
    "CampaignStatus",
    "OmnichannelProvider",
    "OmnichannelTemplate",
    "OmnichannelConversation",
    "OmnichannelMessage",
    "CommunicationPreference",
    "ConsentRecord",
    "Campaign",
    "CampaignRecipient",
    "CannedResponse",
    "ChannelAnalyticsModel",
    # Providers
    "BaseChannelProvider",
    "ProviderFactory",
    "WhatsAppProvider",
    "SMSProvider",
    "EmailProvider",
    "VoiceProvider",
    "MessagePayload",
    "WebhookPayload",
    "ProviderResult",
    "ProviderError",
    "ProviderStatus",
    "get_provider",
]
