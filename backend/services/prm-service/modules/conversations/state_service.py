"""
Conversation State Service
Manages ephemeral conversation state in Redis
"""
import json
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from loguru import logger

from core.redis_client import redis_manager


class ConversationStateService:
    """
    Manages conversation state in Redis

    Redis Keys:
    - conversation:{id}:state - Hash with conversation state data
    - conversation:{id}:required_fields - List of fields still needed
    - conversation:{id}:messages - List of recent messages
    - phone_to_convo:{phone} - Mapping from phone to active conversation
    """

    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.state_key = f"conversation:{conversation_id}:state"
        self.required_fields_key = f"conversation:{conversation_id}:required_fields"
        self.messages_key = f"conversation:{conversation_id}:messages"

    # ==================== Initialization ====================

    async def initialize_session(
        self,
        patient_phone: str,
        required_fields: Optional[List[str]] = None
    ) -> bool:
        """
        Initialize a new conversation session in Redis

        Args:
            patient_phone: Patient's phone number
            required_fields: List of fields to collect (defaults to standard intake)

        Returns:
            True if created new session, False if already exists
        """
        # Check if already initialized
        exists = await redis_manager.exists(self.state_key)
        if exists:
            logger.info(f"Conversation {self.conversation_id} already initialized")
            return False

        # Default required fields for intake
        if required_fields is None:
            required_fields = [
                "patient.name",
                "patient.dob",
                "intake.chief_complaint.text",
                "intake.symptoms",
                "intake.allergies",
                "intake.medications",
                "appointment_request.preferred_location",
                "appointment_request.preferred_day",
                "appointment_request.preferred_time"
            ]

        # Initialize state
        await redis_manager.hset(self.state_key, "patient_phone", patient_phone)
        await redis_manager.hset(self.state_key, "created_at", datetime.utcnow().isoformat())
        await redis_manager.hset(self.state_key, "message_count", "0")
        await redis_manager.expire(self.state_key, 900)  # 15 minutes

        # Set required fields
        if required_fields:
            for field in required_fields:
                await redis_manager.rpush(self.required_fields_key, field)
            await redis_manager.expire(self.required_fields_key, 900)

        logger.info(
            f"Initialized conversation {self.conversation_id} for {patient_phone} "
            f"with {len(required_fields)} required fields"
        )
        return True

    # ==================== State Access ====================

    async def get_state(self) -> Dict[str, Any]:
        """Get all conversation state data"""
        state = await redis_manager.hgetall(self.state_key)
        return state or {}

    async def get_field(self, field: str) -> Optional[str]:
        """Get specific state field"""
        return await redis_manager.hget(self.state_key, field)

    async def set_field(self, field: str, value: str):
        """Set specific state field and extend expiry"""
        await redis_manager.hset(self.state_key, field, value)
        await redis_manager.expire(self.state_key, 900)

    async def get_patient_phone(self) -> Optional[str]:
        """Get patient phone number"""
        return await self.get_field("patient_phone")

    async def set_patient_phone(self, phone: str):
        """Set patient phone number"""
        await self.set_field("patient_phone", phone)

    # ==================== Required Fields Management ====================

    async def get_required_fields(self) -> List[str]:
        """Get list of fields still needed"""
        fields = await redis_manager.lrange(self.required_fields_key, 0, -1)
        return fields or []

    async def remove_required_field(self, field: str):
        """Remove field from required list (field has been collected)"""
        await redis_manager.lrem(self.required_fields_key, 0, field)
        await redis_manager.expire(self.required_fields_key, 900)
        logger.debug(f"Removed required field: {field}")

    async def remove_required_fields(self, fields: List[str]):
        """Remove multiple fields from required list"""
        for field in fields:
            await self.remove_required_field(field)

    async def add_required_field(self, field: str):
        """Add field to required list"""
        await redis_manager.rpush(self.required_fields_key, field)
        await redis_manager.expire(self.required_fields_key, 900)
        logger.debug(f"Added required field: {field}")

    async def is_complete(self) -> bool:
        """Check if all required fields have been collected"""
        count = await redis_manager.llen(self.required_fields_key)
        return count == 0

    # ==================== Extracted Data Management ====================

    async def get_extracted_data(self) -> Dict[str, Any]:
        """
        Get all extracted data from conversation

        Extracted data is stored as fields in the state hash with 'extracted_' prefix
        """
        state = await self.get_state()
        extracted = {}

        for key, value in state.items():
            if key.startswith("extracted_"):
                field_name = key.replace("extracted_", "")
                # Try to parse JSON for complex types
                try:
                    extracted[field_name] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    extracted[field_name] = value

        return extracted

    async def set_extracted_field(self, field: str, value: Any):
        """
        Set extracted data field

        Args:
            field: Field name (e.g., "patient.name")
            value: Value (will be JSON-encoded if dict/list)
        """
        # Encode complex types as JSON
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        else:
            value = str(value)

        await redis_manager.hset(self.state_key, f"extracted_{field}", value)
        await redis_manager.expire(self.state_key, 900)
        logger.debug(f"Set extracted field: {field} = {value[:100]}...")

    async def update_extracted_data(self, data: Dict[str, Any]):
        """
        Bulk update extracted data

        Args:
            data: Dictionary of field -> value
        """
        for field, value in data.items():
            await self.set_extracted_field(field, value)

    # ==================== State Update (from n8n/AI) ====================

    async def update_state(
        self,
        new_data: Dict[str, Any],
        completed_fields: Optional[List[str]] = None,
        next_field: Optional[str] = None
    ):
        """
        Update conversation state from AI/n8n response

        Args:
            new_data: Newly extracted data fields
            completed_fields: Fields that have been completed
            next_field: Next field AI is asking about
        """
        # Store extracted data
        if new_data:
            await self.update_extracted_data(new_data)

        # Remove completed fields from required list
        if completed_fields:
            await self.remove_required_fields(completed_fields)

        # Store next field for reference
        if next_field:
            await self.set_field("next_field", next_field)

        # Auto-remove fields that have been extracted (even if not in completed_fields)
        # This handles cases where AI extracts data for fields not explicitly asked
        for field in new_data.keys():
            # Only remove if value is not "none" or empty
            value = new_data[field]
            if value and str(value).lower().strip() not in ("none", "null", ""):
                await self.remove_required_field(field)

        logger.debug(
            f"Updated state: {len(new_data)} fields extracted, "
            f"{len(completed_fields or [])} fields completed"
        )

    # ==================== Message History ====================

    async def add_message(
        self,
        direction: str,
        content: str,
        actor_type: str = "patient"
    ):
        """
        Add message to conversation history

        Stores last 50 messages in Redis for context
        """
        message_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "direction": direction,
            "actor_type": actor_type,
            "content": content
        }

        await redis_manager.rpush(self.messages_key, json.dumps(message_data))
        await redis_manager.expire(self.messages_key, 900)

        # Keep only last 50 messages
        await redis_manager.ltrim(self.messages_key, -50, -1)

        # Increment message count
        count = await self.get_field("message_count")
        new_count = int(count or 0) + 1
        await self.set_field("message_count", str(new_count))
        await self.set_field("last_message_at", datetime.utcnow().isoformat())

    async def get_messages(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent messages from conversation"""
        messages_json = await redis_manager.lrange(self.messages_key, -limit, -1)

        messages = []
        for msg_json in messages_json:
            try:
                messages.append(json.loads(msg_json))
            except json.JSONDecodeError:
                continue

        return messages

    # ==================== Appointment Slot Selection ====================

    async def set_available_slots(self, slots: List[Dict[str, Any]]):
        """
        Store available appointment slots for user selection

        Used when transitioning to slot selection phase
        """
        await self.set_field("available_slots", json.dumps(slots))
        await self.set_field("awaiting_slot_reply", "True")
        logger.info(f"Set {len(slots)} available slots for conversation {self.conversation_id}")

    async def get_available_slots(self) -> Optional[List[Dict[str, Any]]]:
        """Get available appointment slots"""
        slots_json = await self.get_field("available_slots")
        if slots_json:
            try:
                return json.loads(slots_json)
            except json.JSONDecodeError:
                return None
        return None

    async def is_awaiting_slot_reply(self) -> bool:
        """Check if waiting for user to select appointment slot"""
        awaiting = await self.get_field("awaiting_slot_reply")
        return awaiting == "True"

    async def clear_slot_selection(self):
        """Clear slot selection state after booking confirmed"""
        await redis_manager.hdel(self.state_key, "available_slots")
        await redis_manager.hdel(self.state_key, "awaiting_slot_reply")
        logger.info(f"Cleared slot selection for conversation {self.conversation_id}")

    # ==================== Cleanup ====================

    async def extend_expiry(self, seconds: int = 900):
        """Extend conversation state expiry (default 15 minutes)"""
        await redis_manager.expire(self.state_key, seconds)
        await redis_manager.expire(self.required_fields_key, seconds)
        await redis_manager.expire(self.messages_key, seconds)

    async def delete(self):
        """Delete conversation state from Redis"""
        await redis_manager.delete(self.state_key)
        await redis_manager.delete(self.required_fields_key)
        await redis_manager.delete(self.messages_key)
        logger.info(f"Deleted conversation state: {self.conversation_id}")


# ==================== Phone Mapping ====================

async def get_conversation_for_phone(phone: str) -> Optional[str]:
    """Get active conversation ID for phone number"""
    convo_key = f"phone_to_convo:{phone}"
    return await redis_manager.hget("conversations", convo_key)


async def set_conversation_for_phone(phone: str, conversation_id: str):
    """Map phone number to conversation ID"""
    convo_key = f"phone_to_convo:{phone}"
    await redis_manager.hset("conversations", convo_key, conversation_id)


async def clear_conversation_for_phone(phone: str):
    """Remove phone to conversation mapping"""
    convo_key = f"phone_to_convo:{phone}"
    await redis_manager.hdel("conversations", convo_key)
