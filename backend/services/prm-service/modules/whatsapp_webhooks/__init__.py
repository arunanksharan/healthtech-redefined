"""
WhatsApp Webhooks Module
Integration with Twilio WhatsApp API
Receives incoming messages and stores in conversations database
"""
from .router import router
from .service import WhatsAppWebhookService, get_whatsapp_webhook_service
from .schemas import (
    TwilioWebhookRequest,
    TwilioWebhookResponse,
    WhatsAppMessageWebhook,
    WhatsAppStatusWebhook
)

__all__ = [
    "router",
    "WhatsAppWebhookService",
    "get_whatsapp_webhook_service",
    "TwilioWebhookRequest",
    "TwilioWebhookResponse",
    "WhatsAppMessageWebhook",
    "WhatsAppStatusWebhook"
]
