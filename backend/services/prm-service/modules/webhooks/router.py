"""
Webhooks Router
API endpoints for external webhook integrations (Twilio, Voice Agent)
"""
from fastapi import APIRouter, Request, Response, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from loguru import logger
from typing import Optional
from datetime import datetime

from shared.database.connection import get_db
from modules.webhooks.schemas import (
    TwilioWebhookPayload,
    VoiceAgentWebhookPayload,
    WebhookProcessingResult,
    WebhookHealthResponse
)


router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


# ==================== Twilio Signature Validation ====================

def validate_twilio_signature(request: Request) -> bool:
    """
    Validate Twilio webhook signature for security

    See: https://www.twilio.com/docs/usage/webhooks/webhooks-security
    """
    # TODO: Implement actual Twilio signature validation
    # from twilio.request_validator import RequestValidator
    # validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
    # signature = request.headers.get("X-Twilio-Signature", "")
    # url = str(request.url)
    # params = await request.form()
    # return validator.validate(url, params, signature)

    # For now, skip validation in development
    # IMPORTANT: Enable this in production!
    logger.warning("Twilio signature validation is currently disabled")
    return True


# ==================== Twilio WhatsApp Webhook ====================

@router.post("/twilio", status_code=204, response_class=Response)
async def handle_twilio_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Handle incoming WhatsApp messages from Twilio

    This endpoint receives messages from Twilio's WhatsApp API and:
    1. Validates the request signature (security)
    2. Parses the webhook payload
    3. Handles text messages and voice messages
    4. Routes to conversation flow or appointment slot selection

    Returns 204 No Content (Twilio doesn't need response body)
    """
    try:
        # 1. Validate Twilio signature
        if not validate_twilio_signature(request):
            logger.error("Invalid Twilio signature")
            raise HTTPException(status_code=401, detail="Invalid signature")

        # 2. Parse form data into Pydantic model
        form_data = await request.form()

        try:
            payload = TwilioWebhookPayload.model_validate(form_data)
        except Exception as e:
            logger.error(f"Failed to parse Twilio webhook payload: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")

        # 3. Log incoming message
        logger.info(
            f"Received Twilio message from {payload.From} "
            f"(type: {payload.message_type.value}, "
            f"media: {payload.has_media}, "
            f"voice: {payload.is_voice_message})"
        )

        # 4. Delegate to service layer for processing
        # Import here to avoid circular dependency
        from modules.webhooks.service import WebhookService

        webhook_service = WebhookService(db)

        # Process in background to respond to Twilio quickly
        background_tasks.add_task(
            webhook_service.process_twilio_message,
            payload=payload
        )

        # 5. Return 204 immediately (Twilio doesn't need response)
        return Response(status_code=204)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in Twilio webhook: {e}", exc_info=True)
        # Still return 204 to avoid Twilio retries for non-recoverable errors
        return Response(status_code=204)


# ==================== Voice Agent Webhook ====================

@router.post("/voice-agent", response_model=WebhookProcessingResult)
async def handle_voice_agent_webhook(
    payload: VoiceAgentWebhookPayload,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Handle call transcripts from Voice Agent (zoice)

    This endpoint receives structured call data including:
    - Full transcript
    - Extracted structured data
    - Detected intent (e.g., book_appointment)
    - Call recording URL

    If the intent is appointment booking, it triggers the booking flow.
    Otherwise, it creates a support ticket or inquiry.
    """
    try:
        logger.info(
            f"Received voice agent callback for call {payload.call_id} "
            f"from {payload.patient_phone} "
            f"(intent: {payload.detected_intent}, "
            f"duration: {payload.duration_seconds}s)"
        )

        # Delegate to service layer
        from modules.webhooks.service import WebhookService

        webhook_service = WebhookService(db)

        # Process voice callback
        result = await webhook_service.process_voice_agent_callback(
            payload=payload,
            background_tasks=background_tasks
        )

        return result

    except Exception as e:
        logger.error(f"Error processing voice agent webhook: {e}", exc_info=True)
        return WebhookProcessingResult(
            success=False,
            message=f"Failed to process voice callback: {str(e)}",
            errors=[str(e)]
        )


# ==================== Status Callback (Twilio) ====================

@router.post("/twilio/status", status_code=204, response_class=Response)
async def handle_twilio_status_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Twilio message status callbacks

    Twilio calls this endpoint to notify us about message delivery status:
    - queued, sending, sent, delivered, undelivered, failed

    We can use this to update message status in the database.
    """
    try:
        # Parse status callback
        form_data = await request.form()

        message_sid = form_data.get("MessageSid")
        message_status = form_data.get("MessageStatus")
        error_code = form_data.get("ErrorCode")

        logger.info(
            f"Message status update: {message_sid} -> {message_status} "
            f"(error: {error_code})" if error_code else f"Message status update: {message_sid} -> {message_status}"
        )

        # TODO: Update message status in database
        # from modules.communications.service import CommunicationService
        # comm_service = CommunicationService(db)
        # await comm_service.update_message_status(message_sid, message_status)

        return Response(status_code=204)

    except Exception as e:
        logger.error(f"Error handling status callback: {e}")
        return Response(status_code=204)


# ==================== Health Check ====================

@router.get("/health", response_model=WebhookHealthResponse)
async def webhook_health():
    """
    Health check for webhook endpoints

    Returns basic status and metrics
    """
    # TODO: Implement actual health metrics from Redis/DB
    return WebhookHealthResponse(
        status="healthy",
        webhook_type="all",
        last_received=datetime.utcnow(),
        total_processed=0,
        error_rate=0.0
    )
