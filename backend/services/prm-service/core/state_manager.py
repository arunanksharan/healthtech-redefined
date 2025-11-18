"""
Conversation state management using Redis
"""
import json
from typing import Optional, Dict, Any, List
from loguru import logger

from .redis_client import redis_manager


class ConversationStateService:
    """
    Manages conversation state in Redis
    Used for WhatsApp conversations and appointment booking flows
    """

    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.extracted_data_key = f"conversation:{conversation_id}:extracted_data"
        self.metadata_key = f"conversation:{conversation_id}:metadata"

    async def initialize_session(self, user_phone: str):
        """Initialize a new conversation session"""
        await redis_manager.hset(self.metadata_key, "user_phone", user_phone)
        await redis_manager.hset(self.metadata_key, "conversation_id", self.conversation_id)
        await redis_manager.expire(self.metadata_key, 900)  # 15 minutes
        logger.info(f"Initialized conversation session: {self.conversation_id}")

    async def set_user_phone(self, phone: str):
        """Set user phone number"""
        await redis_manager.hset(self.metadata_key, "user_phone", phone)
        await redis_manager.expire(self.metadata_key, 900)

    async def get_user_phone(self) -> Optional[str]:
        """Get user phone number"""
        return await redis_manager.hget(self.metadata_key, "user_phone")

    async def set_extracted_field(self, field: str, value: str):
        """Set an extracted data field"""
        await redis_manager.hset(self.extracted_data_key, field, value)
        await redis_manager.expire(self.extracted_data_key, 900)

    async def get_extracted_field(self, field: str) -> Optional[str]:
        """Get an extracted data field"""
        return await redis_manager.hget(self.extracted_data_key, field)

    async def get_all_extracted_data(self) -> Dict[str, Any]:
        """Get all extracted data"""
        if not redis_manager.redis:
            return {}

        data = await redis_manager.redis.hgetall(self.extracted_data_key)
        return data or {}

    async def get_required_fields(self) -> List[str]:
        """Get list of required fields that haven't been collected yet"""
        required = ["patient_name", "patient_phone", "practitioner_name", "preferred_date"]
        extracted_data = await self.get_all_extracted_data()

        missing = []
        for field in required:
            if field not in extracted_data or not extracted_data[field]:
                missing.append(field)

        return missing

    async def set_booking_intent(self, intent: int):
        """Set booking intent (0 or 1)"""
        await redis_manager.hset(self.extracted_data_key, "booking_intent", str(intent))

    async def clear_session(self):
        """Clear conversation session data"""
        await redis_manager.delete(self.extracted_data_key, self.metadata_key)
        logger.info(f"Cleared conversation session: {self.conversation_id}")


async def get_or_create_conversation_id(user_phone: str) -> tuple[str, bool]:
    """
    Get existing conversation ID for user or create new one

    Returns:
        (conversation_id, is_new)
    """
    import uuid

    convo_id_key = f"phone_to_convo:{user_phone}"
    stored_conversation_id = await redis_manager.get(convo_id_key)

    if stored_conversation_id:
        # Check if conversation data exists
        state_service = ConversationStateService(stored_conversation_id)
        exists = await redis_manager.exists(state_service.extracted_data_key)

        if exists:
            # Extend expiry
            await redis_manager.expire(convo_id_key, 900)
            logger.info(f"Continuing conversation: {stored_conversation_id}")
            return stored_conversation_id, False
        else:
            # Stale conversation, clean up
            await redis_manager.delete(convo_id_key)

    # Create new conversation
    conversation_id = str(uuid.uuid4())
    await redis_manager.set(convo_id_key, conversation_id, ex=900)
    logger.info(f"New conversation started: {conversation_id}")
    return conversation_id, True
