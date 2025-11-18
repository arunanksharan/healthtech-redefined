"""
n8n Integration Service
Business logic for processing n8n workflow callbacks
"""
from sqlalchemy.orm import Session
from loguru import logger
from typing import Optional, Dict, Any
from uuid import UUID
import json

from core.twilio_client import twilio_client
from modules.conversations.state_service import ConversationStateService
from modules.appointments.service import AppointmentService

from modules.n8n_integration.schemas import (
    IntakeResponsePayload,
    DepartmentTriagePayload,
    BookingResponsePayload,
    N8nCallbackResponse
)


class N8nIntegrationService:
    """Service for processing n8n callbacks"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== Intake Response Processing ====================

    async def process_intake_response(
        self,
        payload: IntakeResponsePayload
    ) -> N8nCallbackResponse:
        """
        Process AI response from n8n intake workflow

        Flow:
        1. Update conversation state with extracted data
        2. Mark completed fields
        3. Send next question to user OR
        4. If conversation complete, trigger department triage
        """
        try:
            conversation_id = payload.conversation_id
            state_service = ConversationStateService(conversation_id)

            logger.info(
                f"Processing intake response for conversation {conversation_id}: "
                f"{len(payload.extracted_fields)} fields extracted"
            )

            # 1. Update state with extracted data
            if payload.extracted_fields:
                # Parse any JSON-encoded fields
                parsed_fields = self._parse_extracted_fields(payload.extracted_fields)

                # Determine completed fields
                completed_fields = [
                    field for field, value in parsed_fields.items()
                    if value and str(value).lower() not in ("none", "null", "")
                ]

                # Update state
                await state_service.update_state(
                    new_data=parsed_fields,
                    completed_fields=completed_fields,
                    next_field=payload.next_field
                )

                logger.info(f"Updated state: {completed_fields} fields completed")

            # 2. Get user phone
            user_phone = await state_service.get_patient_phone()

            if not user_phone:
                logger.error(f"No user phone found for conversation {conversation_id}")
                return N8nCallbackResponse(
                    status="error",
                    message="User phone not found",
                    conversation_id=conversation_id
                )

            # 3. Check if conversation is complete
            is_complete = not payload.next_question or not payload.next_question.strip()

            if is_complete:
                # Conversation complete - trigger next stage
                logger.info(f"Intake complete for conversation {conversation_id}")

                # Note: Department triage should be triggered by n8n workflow
                # We just acknowledge completion here
                return N8nCallbackResponse(
                    status="success",
                    message="Intake complete, awaiting department triage",
                    conversation_id=conversation_id,
                    action_taken="intake_complete"
                )

            else:
                # Send next question to user
                if twilio_client:
                    twilio_client.send_message(
                        to=user_phone,
                        body=payload.next_question
                    )
                    logger.info(f"Sent next question to {user_phone}")

                    # Store message in conversation
                    await state_service.add_message(
                        direction="outbound",
                        content=payload.next_question,
                        actor_type="bot"
                    )

                return N8nCallbackResponse(
                    status="success",
                    message="Next question sent to user",
                    conversation_id=conversation_id,
                    action_taken="question_sent"
                )

        except Exception as e:
            logger.error(f"Error processing intake response: {e}", exc_info=True)
            return N8nCallbackResponse(
                status="error",
                message=f"Failed to process intake response: {str(e)}",
                conversation_id=payload.conversation_id
            )

    def _parse_extracted_fields(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Parse JSON-encoded field values"""
        parsed = {}

        for key, value in fields.items():
            if isinstance(value, str):
                try:
                    # Try to parse as JSON
                    parsed[key] = json.loads(value)
                except json.JSONDecodeError:
                    # Keep as string
                    parsed[key] = value
            else:
                parsed[key] = value

        return parsed

    # ==================== Department Triage Processing ====================

    async def process_department_triage(
        self,
        payload: DepartmentTriagePayload
    ) -> N8nCallbackResponse:
        """
        Process department triage result from n8n

        Flow:
        1. Save best department to conversation state
        2. Trigger appointment slot finding
        3. Send slots to user OR send "no slots" message
        """
        try:
            conversation_id = str(payload.conversation_id)
            state_service = ConversationStateService(conversation_id)

            logger.info(
                f"Processing department triage for conversation {conversation_id}: "
                f"department={payload.best_department.name}"
            )

            # 1. Save department to state
            await state_service.set_field(
                "appointment_request.best_department",
                payload.best_department.name
            )

            # Save alternative departments if provided
            if payload.alternative_departments:
                alt_depts = [dept.name for dept in payload.alternative_departments]
                await state_service.set_field(
                    "appointment_request.alternative_departments",
                    json.dumps(alt_depts)
                )

            # 2. Get user phone
            user_phone = await state_service.get_patient_phone()

            if not user_phone:
                logger.error(f"No user phone found for conversation {conversation_id}")
                return N8nCallbackResponse(
                    status="error",
                    message="User phone not found",
                    conversation_id=conversation_id
                )

            # 3. Find available slots
            appointment_service = AppointmentService(self.db)

            slots_available = await appointment_service.present_slots_to_user(
                conversation_id=payload.conversation_id,
                patient_phone=user_phone,
                max_slots=5
            )

            if slots_available.total_slots > 0:
                # Slots found and sent to user
                logger.info(
                    f"Found and sent {slots_available.total_slots} slots to user "
                    f"for conversation {conversation_id}"
                )

                return N8nCallbackResponse(
                    status="success",
                    message="Slots sent to user",
                    conversation_id=conversation_id,
                    action_taken="slots_presented",
                    data={
                        "slots_count": slots_available.total_slots
                    }
                )

            else:
                # No slots available
                logger.warning(f"No slots found for conversation {conversation_id}")

                # Clean up conversation state
                await state_service.delete()

                return N8nCallbackResponse(
                    status="success",
                    message="No slots available, user notified",
                    conversation_id=conversation_id,
                    action_taken="no_slots_found"
                )

        except Exception as e:
            logger.error(f"Error processing department triage: {e}", exc_info=True)
            return N8nCallbackResponse(
                status="error",
                message=f"Failed to process triage: {str(e)}",
                conversation_id=str(payload.conversation_id)
            )

    # ==================== Booking Response Processing ====================

    async def process_booking_response(
        self,
        payload: BookingResponsePayload
    ) -> N8nCallbackResponse:
        """
        Process booking confirmation/cancellation from n8n

        This is called when n8n processes user's slot selection
        """
        try:
            conversation_id = payload.conversation_id
            state_service = ConversationStateService(conversation_id)

            logger.info(
                f"Processing booking response for conversation {conversation_id}: "
                f"action={payload.action}"
            )

            # Get user phone
            user_phone = await state_service.get_patient_phone()

            # Handle different actions
            if payload.action == "confirm_slot":
                # Slot confirmed - appointment should already be created by appointment service
                # Just send confirmation message if provided
                if payload.reply_to_user and twilio_client and user_phone:
                    twilio_client.send_message(to=user_phone, body=payload.reply_to_user)

                return N8nCallbackResponse(
                    status="success",
                    message="Booking confirmed",
                    conversation_id=conversation_id,
                    action_taken="booking_confirmed"
                )

            elif payload.action == "reject_slots":
                # User rejected slots - find new ones
                logger.info(f"User rejected slots for conversation {conversation_id}")

                # Clear current slots
                await state_service.clear_slot_selection()

                # Send reply
                if payload.reply_to_user and twilio_client and user_phone:
                    twilio_client.send_message(to=user_phone, body=payload.reply_to_user)

                return N8nCallbackResponse(
                    status="success",
                    message="Slots rejected, finding new options",
                    conversation_id=conversation_id,
                    action_taken="slots_rejected"
                )

            elif payload.action == "cancel_booking":
                # User wants to cancel
                logger.info(f"User canceled booking for conversation {conversation_id}")

                # Clean up state
                await state_service.delete()

                # Send reply
                if payload.reply_to_user and twilio_client and user_phone:
                    twilio_client.send_message(to=user_phone, body=payload.reply_to_user)

                return N8nCallbackResponse(
                    status="success",
                    message="Booking canceled",
                    conversation_id=conversation_id,
                    action_taken="booking_canceled"
                )

            elif payload.action == "ambiguous":
                # Couldn't understand user's response
                if payload.reply_to_user and twilio_client and user_phone:
                    twilio_client.send_message(to=user_phone, body=payload.reply_to_user)

                return N8nCallbackResponse(
                    status="success",
                    message="Clarification sent to user",
                    conversation_id=conversation_id,
                    action_taken="clarification_sent"
                )

            else:
                logger.warning(f"Unknown action: {payload.action}")
                return N8nCallbackResponse(
                    status="error",
                    message=f"Unknown action: {payload.action}",
                    conversation_id=conversation_id
                )

        except Exception as e:
            logger.error(f"Error processing booking response: {e}", exc_info=True)
            return N8nCallbackResponse(
                status="error",
                message=f"Failed to process booking response: {str(e)}",
                conversation_id=payload.conversation_id
            )
