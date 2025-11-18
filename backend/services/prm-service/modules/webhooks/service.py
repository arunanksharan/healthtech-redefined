"""
Webhooks Service
Business logic for processing webhook events from Twilio and Voice Agent
"""
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks
from loguru import logger
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from core.redis_client import redis_manager
from core.twilio_client import twilio_client
from core.speech_to_text import speech_to_text_service
from core.config import settings

from modules.webhooks.schemas import (
    TwilioWebhookPayload,
    VoiceAgentWebhookPayload,
    VoiceAgentIntent,
    WebhookProcessingResult
)


class WebhookService:
    """Service for processing webhook events"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== Twilio Message Processing ====================

    async def process_twilio_message(self, payload: TwilioWebhookPayload) -> WebhookProcessingResult:
        """
        Process incoming WhatsApp message from Twilio

        Flow:
        1. Extract/transcribe message content
        2. Get or create conversation
        3. Check if in appointment slot selection flow
        4. Route to appropriate handler
        """
        try:
            # 1. Extract message content
            message_text = await self._extract_message_content(payload)

            if not message_text:
                logger.warning(f"No message text extracted from {payload.MessageSid}")
                return WebhookProcessingResult(
                    success=False,
                    message="No message content",
                    action_taken="ignored"
                )

            # 2. Get or create conversation
            conversation_id = await self._get_or_create_conversation(
                patient_phone=payload.From
            )

            logger.info(
                f"Processing message for conversation {conversation_id}: "
                f"'{message_text[:100]}...'"
            )

            # 3. Check conversation state - are we waiting for slot selection?
            is_awaiting_slot = await self._is_awaiting_slot_selection(conversation_id)

            if is_awaiting_slot:
                # Route to appointment slot selection
                logger.info(f"Routing to slot selection for conversation {conversation_id}")
                result = await self._handle_slot_selection_reply(
                    conversation_id=conversation_id,
                    message_text=message_text,
                    patient_phone=payload.From
                )
                return result

            # 4. Route to conversation flow (intake, general inquiry)
            logger.info(f"Routing to conversation flow for conversation {conversation_id}")
            result = await self._handle_conversation_message(
                conversation_id=conversation_id,
                message_text=message_text,
                patient_phone=payload.From
            )

            return result

        except Exception as e:
            logger.error(f"Error processing Twilio message: {e}", exc_info=True)
            return WebhookProcessingResult(
                success=False,
                message=f"Processing failed: {str(e)}",
                errors=[str(e)]
            )

    async def _extract_message_content(self, payload: TwilioWebhookPayload) -> Optional[str]:
        """
        Extract message content from Twilio payload

        Handles:
        - Text messages (direct)
        - Voice messages (transcribe with Whisper)
        - Media messages with captions
        """
        # Voice message - transcribe it
        if payload.is_voice_message:
            logger.info(f"Transcribing voice message from {payload.MediaUrl0}")
            try:
                transcript = await speech_to_text_service.transcribe_audio_url(
                    payload.MediaUrl0
                )
                if transcript:
                    logger.info(f"Voice transcription successful: '{transcript[:100]}...'")
                    return transcript
                else:
                    logger.warning("Voice transcription returned empty")
                    return None
            except Exception as e:
                logger.error(f"Voice transcription failed: {e}")
                return None

        # Text message or media with caption
        return payload.Body.strip() if payload.Body else None

    async def _get_or_create_conversation(self, patient_phone: str) -> str:
        """
        Get existing conversation or create new one

        Uses Redis to track phone -> conversation_id mapping
        Expires after 15 minutes of inactivity
        """
        convo_key = f"phone_to_convo:{patient_phone}"

        # Check if existing conversation
        existing_convo_id = await redis_manager.hget("conversations", convo_key)

        if existing_convo_id:
            # Verify conversation state still exists
            state_key = f"conversation:{existing_convo_id}:state"
            state_exists = await redis_manager.exists(state_key)

            if state_exists:
                # Extend expiry for active conversation
                await redis_manager.expire(state_key, 900)  # 15 minutes
                logger.info(f"Continuing conversation {existing_convo_id}")
                return existing_convo_id
            else:
                # State expired, clean up mapping
                await redis_manager.hdel("conversations", convo_key)

        # Create new conversation
        conversation_id = str(uuid4())
        await redis_manager.hset("conversations", convo_key, conversation_id)

        # Initialize conversation state
        state_key = f"conversation:{conversation_id}:state"
        await redis_manager.hset(state_key, "patient_phone", patient_phone)
        await redis_manager.hset(state_key, "created_at", datetime.utcnow().isoformat())
        await redis_manager.expire(state_key, 900)

        logger.info(f"Created new conversation {conversation_id} for {patient_phone}")
        return conversation_id

    async def _is_awaiting_slot_selection(self, conversation_id: str) -> bool:
        """
        Check if conversation is in slot selection phase

        This happens when:
        1. Available slots were presented to patient
        2. We're waiting for them to choose a slot number
        """
        state_key = f"conversation:{conversation_id}:state"

        # Check if available_slots field exists
        available_slots = await redis_manager.hget(state_key, "available_slots")
        awaiting_reply = await redis_manager.hget(state_key, "awaiting_slot_reply")

        return bool(available_slots or awaiting_reply == "True")

    async def _handle_slot_selection_reply(
        self,
        conversation_id: str,
        message_text: str,
        patient_phone: str
    ) -> WebhookProcessingResult:
        """
        Handle patient's reply when selecting appointment slot

        Expected: User sends a number (1, 2, 3, etc.) to select slot
        """
        # This will be implemented once we create the Appointments module
        # For now, delegate to a placeholder

        logger.info(f"Slot selection handler called for conversation {conversation_id}")

        # TODO: Implement slot selection logic
        # from modules.appointments.service import AppointmentService
        # appointment_service = AppointmentService(self.db)
        # result = await appointment_service.handle_slot_reply(conversation_id, message_text)

        # Placeholder response
        if twilio_client:
            twilio_client.send_message(
                to=patient_phone,
                body="Thank you for your response. Appointment booking is being set up. You'll receive confirmation shortly."
            )

        return WebhookProcessingResult(
            success=True,
            message="Slot selection processed",
            conversation_id=UUID(conversation_id),
            action_taken="slot_selection"
        )

    async def _handle_conversation_message(
        self,
        conversation_id: str,
        message_text: str,
        patient_phone: str
    ) -> WebhookProcessingResult:
        """
        Handle general conversation message (intake, inquiry)

        Routes message to n8n workflow for AI processing
        """
        try:
            # Get conversation state
            state_key = f"conversation:{conversation_id}:state"

            # Check if this is first message in conversation
            message_count = await redis_manager.hget(state_key, "message_count")
            is_new = not message_count

            # Increment message count
            new_count = int(message_count or 0) + 1
            await redis_manager.hset(state_key, "message_count", str(new_count))

            # Store message in conversation history
            history_key = f"conversation:{conversation_id}:messages"
            message_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "from": "patient",
                "text": message_text
            }
            await redis_manager.rpush(history_key, str(message_data))
            await redis_manager.expire(history_key, 900)

            # Trigger n8n workflow for AI processing
            if settings.N8N_WEBHOOK_URL:
                await self._trigger_n8n_workflow(
                    conversation_id=conversation_id,
                    message_text=message_text,
                    patient_phone=patient_phone,
                    is_new=is_new
                )

            return WebhookProcessingResult(
                success=True,
                message="Message processed",
                conversation_id=UUID(conversation_id),
                action_taken="conversation_flow"
            )

        except Exception as e:
            logger.error(f"Error handling conversation message: {e}", exc_info=True)
            return WebhookProcessingResult(
                success=False,
                message=f"Failed to process message: {str(e)}",
                errors=[str(e)]
            )

    async def _trigger_n8n_workflow(
        self,
        conversation_id: str,
        message_text: str,
        patient_phone: str,
        is_new: bool
    ):
        """
        Trigger n8n workflow for AI message processing

        n8n will:
        1. Extract intent and entities
        2. Determine required fields
        3. Generate appropriate response
        4. Trigger booking if intent detected
        """
        import httpx

        # Get current extracted data
        state_key = f"conversation:{conversation_id}:state"
        required_fields = []  # TODO: Get from state

        payload = {
            "conversation_id": conversation_id,
            "user_text": message_text,
            "user_phone": patient_phone,
            "is_new_conversation": is_new,
            "required_fields": required_fields,
            "booking_intent": 0  # Will be set by n8n
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.N8N_WEBHOOK_URL,
                    json=payload,
                    timeout=5.0
                )
                logger.info(
                    f"Triggered n8n workflow for conversation {conversation_id}: "
                    f"status={response.status_code}"
                )
        except httpx.RequestError as e:
            logger.error(f"Failed to trigger n8n workflow: {e}")
            # Don't raise - this is non-critical, we can continue

    # ==================== Voice Agent Callback Processing ====================

    async def process_voice_agent_callback(
        self,
        payload: VoiceAgentWebhookPayload,
        background_tasks: BackgroundTasks
    ) -> WebhookProcessingResult:
        """
        Process call transcript from Voice Agent (zoice)

        Flow:
        1. Create conversation from call transcript
        2. Check detected intent
        3. If booking intent → trigger appointment flow
        4. Otherwise → create inquiry/support ticket
        """
        try:
            logger.info(
                f"Processing voice agent callback: call_id={payload.call_id}, "
                f"intent={payload.detected_intent}"
            )

            # Create conversation from voice call
            conversation_id = await self._create_voice_conversation(payload)

            # Route based on detected intent
            if payload.is_booking_intent:
                # Trigger appointment booking flow
                action_taken = await self._handle_booking_from_voice(
                    conversation_id=conversation_id,
                    payload=payload,
                    background_tasks=background_tasks
                )
                message = "Appointment booking initiated from voice call"
            else:
                # Create inquiry or support ticket
                action_taken = await self._handle_inquiry_from_voice(
                    conversation_id=conversation_id,
                    payload=payload
                )
                message = "Inquiry created from voice call"

            return WebhookProcessingResult(
                success=True,
                message=message,
                conversation_id=conversation_id,
                action_taken=action_taken
            )

        except Exception as e:
            logger.error(f"Error processing voice agent callback: {e}", exc_info=True)
            return WebhookProcessingResult(
                success=False,
                message=f"Failed to process voice callback: {str(e)}",
                errors=[str(e)]
            )

    async def _create_voice_conversation(
        self,
        payload: VoiceAgentWebhookPayload
    ) -> UUID:
        """
        Create conversation record from voice call

        Stores:
        - Call transcript
        - Recording URL
        - Extracted data
        - Call metadata
        """
        # For now, use call_id as conversation_id
        # In production, create proper Conversation record in DB
        conversation_id = payload.call_id

        # Store in Redis
        state_key = f"conversation:{conversation_id}:state"
        await redis_manager.hset(state_key, "source", "voice_call")
        await redis_manager.hset(state_key, "patient_phone", payload.patient_phone)
        await redis_manager.hset(state_key, "transcript", payload.transcript)
        await redis_manager.hset(state_key, "recording_url", payload.recording_url)
        await redis_manager.hset(state_key, "detected_intent", payload.detected_intent or "")
        await redis_manager.hset(state_key, "confidence_score", str(payload.confidence_score))
        await redis_manager.expire(state_key, 3600)  # 1 hour for voice calls

        # Store extracted data
        if payload.has_extracted_data:
            for key, value in payload.extracted_data.items():
                await redis_manager.hset(state_key, f"extracted_{key}", str(value))

        logger.info(f"Created voice conversation {conversation_id}")
        return conversation_id

    async def _handle_booking_from_voice(
        self,
        conversation_id: UUID,
        payload: VoiceAgentWebhookPayload,
        background_tasks: BackgroundTasks
    ) -> str:
        """
        Handle appointment booking from voice call

        If sufficient data was extracted, trigger booking flow
        Otherwise, send WhatsApp follow-up
        """
        # TODO: Implement once Appointments module is ready
        # from modules.appointments.service import AppointmentService
        # appointment_service = AppointmentService(self.db)
        # await appointment_service.initiate_booking_from_voice(conversation_id, payload.extracted_data)

        logger.info(f"Booking from voice call {conversation_id} - placeholder")

        # Send WhatsApp follow-up
        if twilio_client and payload.patient_phone:
            twilio_client.send_message(
                to=payload.patient_phone,
                body=(
                    "Thank you for your call! I've noted your appointment request. "
                    "I'll send you available time slots shortly via WhatsApp."
                )
            )

        return "booking_initiated_from_voice"

    async def _handle_inquiry_from_voice(
        self,
        conversation_id: UUID,
        payload: VoiceAgentWebhookPayload
    ) -> str:
        """
        Handle general inquiry from voice call

        Creates support ticket or inquiry record
        """
        # TODO: Create ticket via Tickets module
        # from modules.tickets.service import TicketService
        # ticket_service = TicketService(self.db)
        # await ticket_service.create_from_voice_call(conversation_id, payload.transcript)

        logger.info(f"Inquiry from voice call {conversation_id} - placeholder")

        # Send WhatsApp acknowledgment
        if twilio_client and payload.patient_phone:
            twilio_client.send_message(
                to=payload.patient_phone,
                body=(
                    "Thank you for your call! Our team will review your inquiry "
                    "and get back to you shortly."
                )
            )

        return "inquiry_created_from_voice"
