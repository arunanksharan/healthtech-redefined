"""
Voice Agent Webhook Module
Integration with Zucol/Zoice voice agent platform
"""
from .router import router
from .service import VoiceWebhookService, get_voice_webhook_service
from .schemas import (
    VoiceAgentWebhookRequest,
    VoiceCallWebhookResponse,
    PatientLookupRequest,
    PatientLookupResponse,
    BookAppointmentRequest,
    BookAppointmentResponse,
)

__all__ = [
    "router",
    "VoiceWebhookService",
    "get_voice_webhook_service",
    "VoiceAgentWebhookRequest",
    "VoiceCallWebhookResponse",
    "PatientLookupRequest",
    "PatientLookupResponse",
    "BookAppointmentRequest",
    "BookAppointmentResponse",
]
