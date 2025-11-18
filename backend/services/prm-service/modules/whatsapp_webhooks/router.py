"""
WhatsApp Webhooks Router
API endpoints for Twilio WhatsApp webhooks
"""
from fastapi import APIRouter, Depends, HTTPException, Header, Form
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from loguru import logger

from shared.database.connection import get_db
from modules.whatsapp_webhooks.schemas import (
    TwilioWebhookRequest,
    TwilioWebhookResponse,
    WhatsAppStatusWebhook,
    SendWhatsAppMessageRequest,
    SendWhatsAppMessageResponse
)
from modules.whatsapp_webhooks.service import WhatsAppWebhookService, get_whatsapp_webhook_service


router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])


# ==================== Incoming Message Webhook ====================

@router.post("/webhook", response_model=TwilioWebhookResponse)
async def receive_whatsapp_message(
    # Twilio sends form-encoded data, so we use Form() parameters
    MessageSid: str = Form(...),
    AccountSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    Body: str = Form(...),
    NumMedia: str = Form(default="0"),
    ProfileName: Optional[str] = Form(None),
    WaId: Optional[str] = Form(None),
    MediaUrl0: Optional[str] = Form(None),
    MediaContentType0: Optional[str] = Form(None),
    MediaUrl1: Optional[str] = Form(None),
    MediaContentType1: Optional[str] = Form(None),
    SmsStatus: Optional[str] = Form(None),
    MessagingServiceSid: Optional[str] = Form(None),
    Latitude: Optional[str] = Form(None),
    Longitude: Optional[str] = Form(None),
    ApiVersion: Optional[str] = Form(None),
    # Custom headers
    x_tenant_id: UUID = Header(..., description="Organization ID"),
    db: Session = Depends(get_db)
):
    """
    Receive incoming WhatsApp message from Twilio

    Twilio Configuration:
      1. Go to Twilio Console > WhatsApp Senders
      2. Configure webhook URL: https://your-domain.com/api/v1/whatsapp/webhook
      3. Set HTTP method: POST
      4. Include custom header: x-tenant-id with your organization UUID

    Webhook Flow:
      1. User sends WhatsApp message
      2. Twilio forwards to this endpoint
      3. We identify/create patient
      4. Find/create conversation thread
      5. Store message in database
      6. Return 200 OK to Twilio

    Security:
      - Verify request came from Twilio using X-Twilio-Signature header
      - Validate tenant_id exists
      - Rate limit by phone number

    Note: Twilio expects a 200 response within 15 seconds.
    Long-running operations should be queued.
    """
    service = get_whatsapp_webhook_service(db)

    try:
        # Build webhook request object
        webhook = TwilioWebhookRequest(
            MessageSid=MessageSid,
            AccountSid=AccountSid,
            From=From,
            To=To,
            Body=Body,
            NumMedia=NumMedia,
            ProfileName=ProfileName,
            WaId=WaId,
            MediaUrl0=MediaUrl0,
            MediaContentType0=MediaContentType0,
            MediaUrl1=MediaUrl1,
            MediaContentType1=MediaContentType1,
            SmsStatus=SmsStatus,
            MessagingServiceSid=MessagingServiceSid,
            Latitude=Latitude,
            Longitude=Longitude,
            ApiVersion=ApiVersion
        )

        # Process message
        result = await service.process_incoming_message(webhook, x_tenant_id)

        logger.info(
            f"Processed WhatsApp webhook: MessageSid={MessageSid}, "
            f"ConversationId={result.conversation_id}"
        )

        # Twilio expects 200 OK
        return result

    except Exception as e:
        logger.error(f"WhatsApp webhook processing failed: {e}", exc_info=True)

        # Still return 200 to Twilio to avoid retries
        # Log the error for manual investigation
        return TwilioWebhookResponse(
            success=False,
            actions_taken=["error_logged"]
        )


# ==================== Status Update Webhook ====================

@router.post("/status", response_model=TwilioWebhookResponse)
async def receive_status_update(
    MessageSid: str = Form(...),
    MessageStatus: str = Form(...),
    AccountSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    ChannelToAddress: Optional[str] = Form(None),
    EventType: Optional[str] = Form(None),
    ErrorCode: Optional[str] = Form(None),
    ErrorMessage: Optional[str] = Form(None),
    x_tenant_id: UUID = Header(...),
    db: Session = Depends(get_db)
):
    """
    Receive message status update from Twilio

    Twilio sends status updates when:
      - Message is sent from their servers
      - Message is delivered to WhatsApp
      - Message is read by recipient
      - Message fails to deliver

    Status values:
      - queued: Queued in Twilio
      - sending: Being sent
      - sent: Sent to WhatsApp
      - delivered: Delivered to device
      - read: Read by recipient
      - failed: Failed to deliver
      - undelivered: Could not be delivered

    Configure in Twilio:
      1. WhatsApp Sender settings
      2. Status Callback URL: https://your-domain.com/api/v1/whatsapp/status
    """
    service = get_whatsapp_webhook_service(db)

    try:
        webhook = WhatsAppStatusWebhook(
            MessageSid=MessageSid,
            MessageStatus=MessageStatus,
            AccountSid=AccountSid,
            From=From,
            To=To,
            ChannelToAddress=ChannelToAddress,
            EventType=EventType,
            ErrorCode=ErrorCode,
            ErrorMessage=ErrorMessage
        )

        result = await service.process_status_update(webhook, x_tenant_id)

        logger.info(f"Updated message {MessageSid} status to {MessageStatus}")

        return result

    except Exception as e:
        logger.error(f"Status update webhook failed: {e}", exc_info=True)
        return TwilioWebhookResponse(
            success=False,
            actions_taken=["error_logged"]
        )


# ==================== Send Message ====================

@router.post("/send", response_model=SendWhatsAppMessageResponse)
async def send_whatsapp_message(
    request: SendWhatsAppMessageRequest,
    x_tenant_id: UUID = Header(...),
    db: Session = Depends(get_db)
):
    """
    Send a WhatsApp message via Twilio

    Use cases:
      - Agent sends message to patient
      - Automated notification
      - Response to incoming message

    Requirements:
      - Twilio Account SID and Auth Token
      - Twilio WhatsApp number (or approved sender)
      - Recipient must have messaged your number first (24-hour window)

    Example request:
    ```json
    {
      "to": "+1234567890",
      "body": "Your appointment is confirmed for tomorrow at 2 PM",
      "conversation_id": "uuid-of-conversation"
    }
    ```

    Note: This is a placeholder. Full implementation requires:
      - Twilio Python SDK
      - Account credentials from environment
      - Template message support for out-of-session messages
    """
    service = get_whatsapp_webhook_service(db)

    try:
        result = await service.send_message(request, x_tenant_id)
        return result

    except Exception as e:
        logger.error(f"Failed to send WhatsApp message: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send message: {str(e)}"
        )


# ==================== Health Check ====================

@router.get("/health/check")
async def whatsapp_health_check():
    """Health check for WhatsApp webhooks module"""
    return {
        "status": "healthy",
        "module": "whatsapp_webhooks",
        "features": [
            "incoming_message_webhook",
            "status_update_webhook",
            "send_message_api",
            "conversation_threading",
            "patient_identification"
        ],
        "integration": "twilio",
        "channel": "whatsapp"
    }


# ==================== Webhook Verification ====================

@router.get("/webhook")
async def verify_webhook():
    """
    Webhook verification endpoint

    Some webhook providers (like Facebook) send GET request for verification.
    Twilio doesn't require this, but keeping for compatibility.
    """
    return {"status": "webhook_endpoint_active"}
