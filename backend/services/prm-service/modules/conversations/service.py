"""
Conversations Service
Business logic for conversation and message management
"""
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from loguru import logger
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from shared.database.models import Conversation, Message, Patient
from shared.events.publisher import publish_event
from shared.events.schemas import EventType

from modules.conversations.schemas import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationDetailResponse,
    MessageCreate,
    MessageResponse,
    ConversationStateResponse,
    ConversationListFilters,
    ConversationStatus
)
from modules.conversations.state_service import (
    ConversationStateService,
    get_conversation_for_phone,
    set_conversation_for_phone
)


class ConversationService:
    """Service for conversation management"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== Conversation CRUD ====================

    async def create_conversation(
        self,
        conversation_data: ConversationCreate
    ) -> Optional[Conversation]:
        """
        Create new conversation

        Also initializes state in Redis if patient_phone available
        """
        try:
            # Create database record
            conversation = Conversation(
                id=uuid4(),
                patient_id=conversation_data.patient_id,
                subject=conversation_data.subject,
                status=conversation_data.status.value,
                priority=conversation_data.priority.value,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.db.add(conversation)
            self.db.commit()
            self.db.refresh(conversation)

            logger.info(f"Created conversation {conversation.id}")

            # Publish event
            await publish_event(
                event_type=EventType.CONVERSATION_CREATED,
                entity_id=conversation.id,
                entity_type="conversation",
                data={
                    "conversation_id": str(conversation.id),
                    "patient_id": str(conversation.patient_id) if conversation.patient_id else None,
                    "status": conversation.status
                }
            )

            # Create initial message if provided
            if conversation_data.initial_message:
                await self.create_message(
                    MessageCreate(
                        conversation_id=conversation.id,
                        direction="outbound",
                        actor_type="bot",
                        text_body=conversation_data.initial_message
                    )
                )

            return conversation

        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            self.db.rollback()
            return None

    async def get_conversation(self, conversation_id: UUID) -> Optional[Conversation]:
        """Get conversation by ID"""
        return self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

    async def get_conversation_with_messages(
        self,
        conversation_id: UUID,
        message_limit: int = 50
    ) -> Optional[ConversationDetailResponse]:
        """
        Get conversation with recent messages

        Combines database conversation with messages
        """
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            return None

        # Get recent messages
        messages = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(
            Message.created_at.desc()
        ).limit(message_limit).all()

        # Convert to response models
        message_responses = [
            MessageResponse.from_orm(msg) for msg in reversed(messages)
        ]

        return ConversationDetailResponse(
            **ConversationResponse.from_orm(conversation).dict(),
            messages=message_responses
        )

    async def list_conversations(
        self,
        filters: ConversationListFilters
    ) -> List[ConversationResponse]:
        """
        List conversations with filters

        Supports:
        - Filter by patient, status, priority, owner
        - Search in subject
        - Pagination
        """
        query = self.db.query(Conversation)

        # Apply filters
        if filters.patient_id:
            query = query.filter(Conversation.patient_id == filters.patient_id)

        if filters.status:
            query = query.filter(Conversation.status == filters.status.value)

        if filters.priority:
            query = query.filter(Conversation.priority == filters.priority.value)

        if filters.owner_id:
            query = query.filter(Conversation.current_owner_id == filters.owner_id)

        if filters.search_query:
            query = query.filter(
                Conversation.subject.ilike(f"%{filters.search_query}%")
            )

        # Order by most recent
        query = query.order_by(Conversation.updated_at.desc())

        # Pagination
        query = query.offset(filters.offset).limit(filters.limit)

        conversations = query.all()

        return [ConversationResponse.from_orm(c) for c in conversations]

    async def update_conversation(
        self,
        conversation_id: UUID,
        update_data: ConversationUpdate
    ) -> Optional[Conversation]:
        """Update conversation"""
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            return None

        # Update fields
        if update_data.subject is not None:
            conversation.subject = update_data.subject

        if update_data.status is not None:
            conversation.status = update_data.status.value

        if update_data.priority is not None:
            conversation.priority = update_data.priority.value

        if update_data.current_owner_id is not None:
            conversation.current_owner_id = update_data.current_owner_id

        conversation.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(conversation)

        logger.info(f"Updated conversation {conversation_id}")

        # Publish event
        await publish_event(
            event_type=EventType.CONVERSATION_UPDATED,
            entity_id=conversation_id,
            entity_type="conversation",
            data=update_data.dict(exclude_none=True)
        )

        return conversation

    # ==================== Message Management ====================

    async def create_message(
        self,
        message_data: MessageCreate
    ) -> Optional[Message]:
        """Create message in conversation"""
        try:
            message = Message(
                id=uuid4(),
                conversation_id=message_data.conversation_id,
                direction=message_data.direction.value,
                actor_type=message_data.actor_type.value,
                content_type=message_data.content_type.value,
                text_body=message_data.text_body,
                locale=message_data.locale,
                created_at=datetime.utcnow()
            )

            self.db.add(message)

            # Update conversation timestamp
            conversation = await self.get_conversation(message_data.conversation_id)
            if conversation:
                conversation.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(message)

            logger.info(
                f"Created message {message.id} in conversation {message_data.conversation_id} "
                f"({message_data.direction.value})"
            )

            # Also store in Redis for quick access
            state_service = ConversationStateService(str(message_data.conversation_id))
            await state_service.add_message(
                direction=message_data.direction.value,
                content=message_data.text_body or "",
                actor_type=message_data.actor_type.value
            )

            return message

        except Exception as e:
            logger.error(f"Error creating message: {e}")
            self.db.rollback()
            return None

    async def get_messages(
        self,
        conversation_id: UUID,
        limit: int = 50
    ) -> List[MessageResponse]:
        """Get messages for conversation"""
        messages = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(
            Message.created_at.desc()
        ).limit(limit).all()

        return [MessageResponse.from_orm(msg) for msg in reversed(messages)]

    # ==================== State Management ====================

    async def get_conversation_state(
        self,
        conversation_id: UUID
    ) -> ConversationStateResponse:
        """
        Get current conversation state from Redis

        Returns ephemeral state (required fields, extracted data, etc.)
        """
        state_service = ConversationStateService(str(conversation_id))

        # Get state data
        state = await state_service.get_state()
        required_fields = await state_service.get_required_fields()
        extracted_data = await state_service.get_extracted_data()
        is_complete = await state_service.is_complete()

        return ConversationStateResponse(
            conversation_id=conversation_id,
            patient_phone=state.get("patient_phone"),
            required_fields=required_fields,
            extracted_data=extracted_data,
            is_complete=is_complete,
            message_count=int(state.get("message_count", 0)),
            created_at=datetime.fromisoformat(state["created_at"]) if state.get("created_at") else None,
            last_message_at=datetime.fromisoformat(state["last_message_at"]) if state.get("last_message_at") else None
        )

    async def initialize_conversation_state(
        self,
        conversation_id: UUID,
        patient_phone: str,
        required_fields: Optional[List[str]] = None
    ) -> bool:
        """
        Initialize conversation state in Redis

        Used for new intake conversations
        """
        state_service = ConversationStateService(str(conversation_id))
        success = await state_service.initialize_session(patient_phone, required_fields)

        if success:
            # Map phone to conversation
            await set_conversation_for_phone(patient_phone, str(conversation_id))

        return success

    # ==================== Helper Methods ====================

    async def get_or_create_for_patient(
        self,
        patient_id: UUID,
        channel_type: str = "whatsapp"
    ) -> Conversation:
        """
        Get open conversation for patient or create new one

        Used to continue existing conversations
        """
        # Check for open conversation
        existing = self.db.query(Conversation).filter(
            Conversation.patient_id == patient_id,
            Conversation.status == ConversationStatus.OPEN.value
        ).order_by(
            Conversation.updated_at.desc()
        ).first()

        if existing:
            return existing

        # Create new conversation
        conversation = await self.create_conversation(
            ConversationCreate(
                patient_id=patient_id,
                subject=f"Conversation via {channel_type}",
                status=ConversationStatus.OPEN
            )
        )

        return conversation

    async def close_conversation(self, conversation_id: UUID) -> Optional[Conversation]:
        """Close conversation"""
        return await self.update_conversation(
            conversation_id,
            ConversationUpdate(status=ConversationStatus.CLOSED)
        )
