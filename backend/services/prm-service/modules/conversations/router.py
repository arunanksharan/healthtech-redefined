"""
Conversations Router
API endpoints for conversation and message management
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from loguru import logger

from shared.database.connection import get_db

from modules.conversations.schemas import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationDetailResponse,
    MessageCreate,
    MessageResponse,
    ConversationStateResponse,
    ConversationListFilters
)
from modules.conversations.service import ConversationService


router = APIRouter(prefix="/conversations", tags=["Conversations"])


# ==================== Conversation Endpoints ====================

@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    conversation_data: ConversationCreate,
    db: Session = Depends(get_db)
):
    """
    Create new conversation

    Use this to start a new conversation thread with a patient.
    Can optionally include an initial message.
    """
    service = ConversationService(db)
    conversation = await service.create_conversation(conversation_data)

    if not conversation:
        raise HTTPException(status_code=500, detail="Failed to create conversation")

    return ConversationResponse.from_orm(conversation)


@router.get("", response_model=List[ConversationResponse])
async def list_conversations(
    patient_id: UUID = None,
    status: str = None,
    priority: str = None,
    owner_id: UUID = None,
    search_query: str = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List conversations with optional filters

    Supports:
    - Filter by patient_id, status, priority, owner_id
    - Search in conversation subject
    - Pagination with limit/offset
    """
    filters = ConversationListFilters(
        patient_id=patient_id,
        status=status,
        priority=priority,
        owner_id=owner_id,
        search_query=search_query,
        limit=limit,
        offset=offset
    )

    service = ConversationService(db)
    conversations = await service.list_conversations(filters)

    return conversations


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: UUID,
    message_limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get conversation by ID with recent messages

    Returns full conversation details including:
    - Conversation metadata
    - Recent messages (default: last 50)
    """
    service = ConversationService(db)
    conversation = await service.get_conversation_with_messages(
        conversation_id,
        message_limit=message_limit
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    update_data: ConversationUpdate,
    db: Session = Depends(get_db)
):
    """
    Update conversation

    Can update:
    - subject
    - status (open, pending, snoozed, closed)
    - priority (p0-p3)
    - current_owner_id (assign to agent)
    """
    service = ConversationService(db)
    conversation = await service.update_conversation(conversation_id, update_data)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return ConversationResponse.from_orm(conversation)


@router.post("/{conversation_id}/close", response_model=ConversationResponse)
async def close_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Close conversation

    Convenience endpoint to set status to "closed"
    """
    service = ConversationService(db)
    conversation = await service.close_conversation(conversation_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return ConversationResponse.from_orm(conversation)


# ==================== Message Endpoints ====================

@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=201)
async def create_message(
    conversation_id: UUID,
    message_data: MessageCreate,
    db: Session = Depends(get_db)
):
    """
    Create message in conversation

    Use this to add messages to an existing conversation.
    Message direction can be:
    - inbound: From patient
    - outbound: To patient
    """
    # Ensure conversation_id matches route parameter
    if message_data.conversation_id != conversation_id:
        raise HTTPException(
            status_code=400,
            detail="Conversation ID mismatch"
        )

    service = ConversationService(db)

    # Verify conversation exists
    conversation = await service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    message = await service.create_message(message_data)

    if not message:
        raise HTTPException(status_code=500, detail="Failed to create message")

    return MessageResponse.from_orm(message)


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: UUID,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get messages for conversation

    Returns messages in chronological order (oldest first)
    """
    service = ConversationService(db)

    # Verify conversation exists
    conversation = await service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = await service.get_messages(conversation_id, limit=limit)

    return messages


# ==================== State Endpoints ====================

@router.get("/{conversation_id}/state", response_model=ConversationStateResponse)
async def get_conversation_state(
    conversation_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get conversation state from Redis

    Returns ephemeral state including:
    - Required fields (for intake)
    - Extracted data
    - Message count
    - Completion status
    """
    service = ConversationService(db)

    state = await service.get_conversation_state(conversation_id)

    return state


@router.post("/{conversation_id}/state/initialize", response_model=dict)
async def initialize_conversation_state(
    conversation_id: UUID,
    patient_phone: str,
    required_fields: List[str] = None,
    db: Session = Depends(get_db)
):
    """
    Initialize conversation state in Redis

    Use this to start intake flow for a conversation.
    Optionally provide custom required_fields list.
    """
    service = ConversationService(db)

    # Verify conversation exists
    conversation = await service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    success = await service.initialize_conversation_state(
        conversation_id,
        patient_phone,
        required_fields
    )

    if not success:
        raise HTTPException(
            status_code=400,
            detail="State already initialized or failed to initialize"
        )

    return {
        "success": True,
        "message": "Conversation state initialized",
        "conversation_id": str(conversation_id)
    }
