"""
Provider Collaboration Router
API endpoints for provider collaboration platform
EPIC-015: Provider Collaboration Platform
"""
from datetime import date, datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from shared.database.connection import get_async_db

from .services import (
    messaging_service, consultation_service, care_team_service,
    handoff_service, on_call_service, alert_service
)
from .schemas import (
    # Presence schemas
    PresenceUpdate, PresenceResponse, BulkPresenceResponse,
    # Conversation schemas
    ConversationCreate, ConversationUpdate, ConversationResponse, ConversationListResponse,
    ParticipantAdd, ParticipantResponse,
    # Message schemas
    MessageCreate, MessageResponse, MessageListResponse, ReactionCreate,
    # Consultation schemas
    ConsultationCreate, ConsultationResponse, ConsultationListResponse,
    ConsultationAccept, ConsultationDecline, ConsultationReportCreate, ConsultationReportResponse,
    # Care Team schemas
    CareTeamCreate, CareTeamUpdate, CareTeamResponse, CareTeamListResponse,
    CareTeamMemberAdd, CareTeamMemberUpdate, CareTeamMemberResponse,
    CareTeamTaskCreate, CareTeamTaskUpdate, CareTeamTaskResponse, CareTeamTaskListResponse,
    CareTeamGoalsUpdate,
    # Handoff schemas
    HandoffCreate, PatientHandoffUpdate, HandoffAcknowledge, HandoffQuestion,
    HandoffResponse, PatientHandoffResponse, HandoffListResponse,
    # On-Call schemas
    OnCallScheduleCreate, OnCallScheduleUpdate, OnCallScheduleResponse, OnCallScheduleListResponse,
    OnCallRequestCreate, OnCallRequestResponse, OnCallRequestListResponse,
    # Alert schemas
    AlertCreate, AlertResponse, AlertListResponse,
    AlertRuleCreate, AlertRuleUpdate, AlertRuleResponse, AlertRuleListResponse,
    # Case Discussion schemas
    CaseDiscussionCreate, CaseDiscussionResponse, CaseDiscussionListResponse,
    CaseDiscussionCommentCreate, CaseDiscussionVoteCreate,
    # Enums
    PresenceStatusSchema, ConversationTypeSchema, ConsultationStatusSchema,
    CareTeamStatusSchema, TaskStatusSchema, HandoffStatusSchema,
    OnCallStatusSchema, AlertPrioritySchema, AlertStatusSchema
)
from .models import (
    PresenceStatus, ConversationType, ConsultationStatus, ConsultationUrgency,
    CareTeamStatus, TaskStatus, HandoffStatus, OnCallStatus,
    AlertPriority, AlertStatus, OnCallRequestStatus, RequestUrgency
)


router = APIRouter(prefix="/collaboration", tags=["Provider Collaboration"])


# Helper function to get provider_id and tenant_id from request
# In production, these would come from JWT token
def get_provider_context(request: Request):
    # These would be extracted from JWT in production
    provider_id = request.headers.get("X-Provider-ID")
    tenant_id = request.headers.get("X-Tenant-ID")
    if not provider_id or not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Provider ID and Tenant ID required"
        )
    return UUID(provider_id), UUID(tenant_id)


def get_client_ip(request: Request) -> str:
    return request.client.host if request.client else None


# ==================== Presence Endpoints ====================

@router.put(
    "/presence",
    response_model=PresenceResponse,
    summary="Update provider presence",
    description="Update online status and availability"
)
async def update_presence(
    data: PresenceUpdate,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Update provider's presence status."""
    provider_id, tenant_id = get_provider_context(request)
    device_info = {
        "user_agent": request.headers.get("User-Agent"),
        "device_id": request.headers.get("X-Device-ID")
    }
    try:
        return await messaging_service.update_presence(
            db, provider_id, tenant_id, data, device_info, get_client_ip(request)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/presence/{provider_id}",
    response_model=PresenceResponse,
    summary="Get provider presence",
    description="Get online status for a specific provider"
)
async def get_presence(
    provider_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Get a provider's presence status."""
    _, tenant_id = get_provider_context(request)
    try:
        return await messaging_service.get_presence(db, provider_id, tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/presence/bulk",
    response_model=BulkPresenceResponse,
    summary="Get bulk presence status",
    description="Get presence status for multiple providers"
)
async def get_bulk_presence(
    provider_ids: List[UUID],
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Get presence status for multiple providers."""
    _, tenant_id = get_provider_context(request)
    return await messaging_service.get_bulk_presence(db, provider_ids, tenant_id)


# ==================== Conversation Endpoints ====================

@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create conversation",
    description="Create a new conversation thread"
)
async def create_conversation(
    data: ConversationCreate,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new provider conversation."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await messaging_service.create_conversation(
            db, provider_id, tenant_id, data, get_client_ip(request)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/conversations",
    response_model=ConversationListResponse,
    summary="List conversations",
    description="List provider conversations with filters"
)
async def list_conversations(
    request: Request,
    conversation_type: Optional[ConversationTypeSchema] = None,
    patient_id: Optional[UUID] = None,
    unread_only: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db)
):
    """List conversations for the current provider."""
    provider_id, tenant_id = get_provider_context(request)
    conv_type = ConversationType(conversation_type.value) if conversation_type else None
    return await messaging_service.list_conversations(
        db, provider_id, tenant_id, conv_type, patient_id, unread_only, page, page_size
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
    summary="Get conversation",
    description="Get conversation details"
)
async def get_conversation(
    conversation_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Get conversation details."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await messaging_service.get_conversation(db, provider_id, tenant_id, conversation_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/conversations/{conversation_id}/participants",
    response_model=ParticipantResponse,
    summary="Add participant",
    description="Add a participant to a conversation"
)
async def add_participant(
    conversation_id: UUID,
    data: ParticipantAdd,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Add a participant to a conversation."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await messaging_service.add_participant(
            db, provider_id, tenant_id, conversation_id, data
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/conversations/{conversation_id}/participants/{participant_provider_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove participant",
    description="Remove a participant from a conversation"
)
async def remove_participant(
    conversation_id: UUID,
    participant_provider_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Remove a participant from a conversation."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        await messaging_service.remove_participant(
            db, provider_id, tenant_id, conversation_id, participant_provider_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================== Message Endpoints ====================

@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send message",
    description="Send a message in a conversation"
)
async def send_message(
    conversation_id: UUID,
    data: MessageCreate,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Send a message in a conversation."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await messaging_service.send_message(
            db, provider_id, tenant_id, conversation_id, data, get_client_ip(request)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=MessageListResponse,
    summary="Get messages",
    description="Get messages in a conversation"
)
async def get_messages(
    conversation_id: UUID,
    request: Request,
    before: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db)
):
    """Get messages in a conversation."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await messaging_service.get_messages(
            db, provider_id, tenant_id, conversation_id, before, page, page_size
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/messages/{message_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mark message read",
    description="Mark a message as read"
)
async def mark_message_read(
    message_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Mark a message as read."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        await messaging_service.mark_messages_read(db, provider_id, tenant_id, [message_id])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/conversations/{conversation_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mark conversation read",
    description="Mark all messages in a conversation as read"
)
async def mark_conversation_read(
    conversation_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Mark all messages in a conversation as read."""
    provider_id, tenant_id = get_provider_context(request)
    # Get all unread messages and mark them read
    try:
        messages = await messaging_service.get_messages(
            db, provider_id, tenant_id, conversation_id, None, 1, 1000
        )
        message_ids = [m.id for m in messages.messages]
        if message_ids:
            await messaging_service.mark_messages_read(db, provider_id, tenant_id, message_ids)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/messages/{message_id}/reactions",
    status_code=status.HTTP_201_CREATED,
    summary="Add reaction",
    description="Add a reaction to a message"
)
async def add_reaction(
    message_id: UUID,
    data: ReactionCreate,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Add a reaction to a message."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        await messaging_service.add_reaction(db, provider_id, message_id, data.emoji)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/messages/{message_id}/reactions/{emoji}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove reaction",
    description="Remove a reaction from a message"
)
async def remove_reaction(
    message_id: UUID,
    emoji: str,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Remove a reaction from a message."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        await messaging_service.remove_reaction(db, provider_id, message_id, emoji)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/messages/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Recall message",
    description="Recall (delete) a sent message"
)
async def recall_message(
    message_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Recall a sent message."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        await messaging_service.recall_message(db, provider_id, message_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================== Consultation Endpoints ====================

@router.post(
    "/consultations",
    response_model=ConsultationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request consultation",
    description="Request a specialist consultation"
)
async def create_consultation(
    data: ConsultationCreate,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Request a specialist consultation."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await consultation_service.create_consultation(
            db, provider_id, tenant_id, data, get_client_ip(request)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/consultations",
    response_model=ConsultationListResponse,
    summary="List consultations",
    description="List consultations with filters"
)
async def list_consultations(
    request: Request,
    role: str = Query("all", regex="^(requester|consultant|all)$"),
    specialty: Optional[str] = None,
    consultation_status: Optional[ConsultationStatusSchema] = Query(None, alias="status"),
    patient_id: Optional[UUID] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db)
):
    """List consultations for the current provider."""
    provider_id, tenant_id = get_provider_context(request)
    cons_status = ConsultationStatus(consultation_status.value) if consultation_status else None
    return await consultation_service.list_consultations(
        db, provider_id, tenant_id, role, specialty, cons_status, patient_id, page, page_size
    )


@router.get(
    "/consultations/{consultation_id}",
    response_model=ConsultationResponse,
    summary="Get consultation",
    description="Get consultation details"
)
async def get_consultation(
    consultation_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Get consultation details."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await consultation_service.get_consultation(
            db, provider_id, tenant_id, consultation_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/consultations/{consultation_id}/accept",
    response_model=ConsultationResponse,
    summary="Accept consultation",
    description="Accept a consultation request"
)
async def accept_consultation(
    consultation_id: UUID,
    data: ConsultationAccept,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Accept a consultation request."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await consultation_service.accept_consultation(
            db, provider_id, consultation_id, data
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/consultations/{consultation_id}/decline",
    response_model=ConsultationResponse,
    summary="Decline consultation",
    description="Decline a consultation request"
)
async def decline_consultation(
    consultation_id: UUID,
    data: ConsultationDecline,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Decline a consultation request."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await consultation_service.decline_consultation(
            db, provider_id, consultation_id, data
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/consultations/{consultation_id}/start",
    response_model=ConsultationResponse,
    summary="Start consultation",
    description="Start a consultation session"
)
async def start_consultation(
    consultation_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Start a consultation session."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await consultation_service.start_consultation(db, provider_id, consultation_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/consultations/{consultation_id}/report",
    response_model=ConsultationReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create consultation report",
    description="Create a consultation report"
)
async def create_consultation_report(
    consultation_id: UUID,
    data: ConsultationReportCreate,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Create a consultation report."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await consultation_service.create_report(
            db, provider_id, consultation_id, data
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/consultations/{consultation_id}/report/sign",
    response_model=ConsultationReportResponse,
    summary="Sign consultation report",
    description="Sign and finalize a consultation report"
)
async def sign_consultation_report(
    consultation_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Sign and finalize a consultation report."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await consultation_service.sign_report(db, provider_id, consultation_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/consultations/{consultation_id}/complete",
    response_model=ConsultationResponse,
    summary="Complete consultation",
    description="Complete a consultation"
)
async def complete_consultation(
    consultation_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Complete a consultation."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await consultation_service.complete_consultation(db, provider_id, consultation_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================== Care Team Endpoints ====================

@router.post(
    "/care-teams",
    response_model=CareTeamResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create care team",
    description="Create a new care team"
)
async def create_care_team(
    data: CareTeamCreate,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new care team."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await care_team_service.create_care_team(
            db, provider_id, tenant_id, data, get_client_ip(request)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/care-teams",
    response_model=CareTeamListResponse,
    summary="List care teams",
    description="List care teams with filters"
)
async def list_care_teams(
    request: Request,
    patient_id: Optional[UUID] = None,
    team_status: Optional[CareTeamStatusSchema] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db)
):
    """List care teams for the current provider."""
    provider_id, tenant_id = get_provider_context(request)
    ct_status = CareTeamStatus(team_status.value) if team_status else None
    return await care_team_service.list_care_teams(
        db, provider_id, tenant_id, patient_id, ct_status, page, page_size
    )


@router.get(
    "/care-teams/{care_team_id}",
    response_model=CareTeamResponse,
    summary="Get care team",
    description="Get care team details"
)
async def get_care_team(
    care_team_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Get care team details."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await care_team_service.get_care_team(db, provider_id, tenant_id, care_team_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/care-teams/{care_team_id}",
    response_model=CareTeamResponse,
    summary="Update care team",
    description="Update care team details"
)
async def update_care_team(
    care_team_id: UUID,
    data: CareTeamUpdate,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Update care team details."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await care_team_service.update_care_team(
            db, provider_id, tenant_id, care_team_id, data
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put(
    "/care-teams/{care_team_id}/goals",
    response_model=CareTeamResponse,
    summary="Update care goals",
    description="Update care team goals"
)
async def update_care_goals(
    care_team_id: UUID,
    data: CareTeamGoalsUpdate,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Update care team goals."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await care_team_service.update_goals(
            db, provider_id, tenant_id, care_team_id, data
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/care-teams/{care_team_id}/members",
    response_model=CareTeamMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add team member",
    description="Add a member to a care team"
)
async def add_care_team_member(
    care_team_id: UUID,
    data: CareTeamMemberAdd,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Add a member to a care team."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await care_team_service.add_member(
            db, provider_id, tenant_id, care_team_id, data
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put(
    "/care-teams/{care_team_id}/members/{member_id}",
    response_model=CareTeamMemberResponse,
    summary="Update team member",
    description="Update a care team member"
)
async def update_care_team_member(
    care_team_id: UUID,
    member_id: UUID,
    data: CareTeamMemberUpdate,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Update a care team member."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await care_team_service.update_member(
            db, provider_id, tenant_id, member_id, data
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/care-teams/{care_team_id}/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove team member",
    description="Remove a member from a care team"
)
async def remove_care_team_member(
    care_team_id: UUID,
    member_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Remove a member from a care team."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        await care_team_service.remove_member(db, provider_id, tenant_id, member_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================== Care Team Task Endpoints ====================

@router.post(
    "/care-teams/{care_team_id}/tasks",
    response_model=CareTeamTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create task",
    description="Create a care team task"
)
async def create_care_team_task(
    care_team_id: UUID,
    data: CareTeamTaskCreate,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Create a care team task."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await care_team_service.create_task(
            db, provider_id, tenant_id, care_team_id, data
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/care-teams/{care_team_id}/tasks",
    response_model=CareTeamTaskListResponse,
    summary="List tasks",
    description="List care team tasks"
)
async def list_care_team_tasks(
    care_team_id: UUID,
    request: Request,
    assignee_id: Optional[UUID] = None,
    task_status: Optional[TaskStatusSchema] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db)
):
    """List care team tasks."""
    provider_id, tenant_id = get_provider_context(request)
    t_status = TaskStatus(task_status.value) if task_status else None
    return await care_team_service.list_tasks(
        db, provider_id, tenant_id, care_team_id, assignee_id, t_status, page, page_size
    )


@router.put(
    "/tasks/{task_id}",
    response_model=CareTeamTaskResponse,
    summary="Update task",
    description="Update a care team task"
)
async def update_care_team_task(
    task_id: UUID,
    data: CareTeamTaskUpdate,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Update a care team task."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await care_team_service.update_task(db, provider_id, task_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/tasks/{task_id}/complete",
    response_model=CareTeamTaskResponse,
    summary="Complete task",
    description="Mark a task as completed"
)
async def complete_care_team_task(
    task_id: UUID,
    request: Request,
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """Complete a care team task."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await care_team_service.complete_task(db, provider_id, task_id, notes)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================== Handoff Endpoints ====================

@router.post(
    "/handoffs",
    response_model=HandoffResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create handoff",
    description="Create a shift handoff session"
)
async def create_handoff(
    data: HandoffCreate,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Create a shift handoff session."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await handoff_service.create_handoff(
            db, provider_id, tenant_id, data, get_client_ip(request)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/handoffs",
    response_model=HandoffListResponse,
    summary="List handoffs",
    description="List shift handoffs with filters"
)
async def list_handoffs(
    request: Request,
    role: str = Query("all", regex="^(outgoing|incoming|all)$"),
    shift_date: Optional[date] = None,
    handoff_status: Optional[HandoffStatusSchema] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db)
):
    """List handoffs for the current provider."""
    provider_id, tenant_id = get_provider_context(request)
    h_status = HandoffStatus(handoff_status.value) if handoff_status else None
    return await handoff_service.list_handoffs(
        db, provider_id, tenant_id, role, shift_date, h_status, page, page_size
    )


@router.get(
    "/handoffs/{handoff_id}",
    response_model=HandoffResponse,
    summary="Get handoff",
    description="Get handoff details"
)
async def get_handoff(
    handoff_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Get handoff details."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await handoff_service.get_handoff(db, provider_id, tenant_id, handoff_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/handoffs/{handoff_id}/start",
    response_model=HandoffResponse,
    summary="Start handoff",
    description="Start a handoff session"
)
async def start_handoff(
    handoff_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Start a handoff session."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await handoff_service.start_handoff(db, provider_id, handoff_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put(
    "/handoffs/patients/{patient_handoff_id}",
    response_model=PatientHandoffResponse,
    summary="Update patient handoff",
    description="Update patient SBAR data"
)
async def update_patient_handoff(
    patient_handoff_id: UUID,
    data: PatientHandoffUpdate,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Update patient handoff SBAR data."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await handoff_service.update_patient_handoff(
            db, provider_id, patient_handoff_id, data
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/handoffs/{handoff_id}/questions",
    status_code=status.HTTP_201_CREATED,
    summary="Raise question",
    description="Raise a question about a patient handoff"
)
async def raise_handoff_question(
    handoff_id: UUID,
    data: HandoffQuestion,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Raise a question about a patient handoff."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        await handoff_service.raise_question(db, provider_id, handoff_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/handoffs/{handoff_id}/acknowledge",
    response_model=HandoffResponse,
    summary="Acknowledge handoff",
    description="Acknowledge receipt of handoff"
)
async def acknowledge_handoff(
    handoff_id: UUID,
    data: HandoffAcknowledge,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Acknowledge receipt of handoff."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await handoff_service.acknowledge_handoff(db, provider_id, handoff_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/handoffs/patients/{patient_id}/sbar",
    summary="Generate SBAR",
    description="Generate SBAR data for a patient"
)
async def generate_patient_sbar(
    patient_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Generate SBAR data for a patient."""
    provider_id, tenant_id = get_provider_context(request)
    return await handoff_service.generate_patient_sbar(db, patient_id, provider_id)


# ==================== On-Call Endpoints ====================

@router.post(
    "/oncall/schedules",
    response_model=OnCallScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create on-call schedule",
    description="Create an on-call schedule entry"
)
async def create_oncall_schedule(
    data: OnCallScheduleCreate,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Create an on-call schedule entry."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await on_call_service.create_schedule(
            db, provider_id, tenant_id, data, get_client_ip(request)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/oncall/schedules",
    response_model=OnCallScheduleListResponse,
    summary="List on-call schedules",
    description="List on-call schedules with filters"
)
async def list_oncall_schedules(
    request: Request,
    provider_id_filter: Optional[UUID] = Query(None, alias="provider_id"),
    specialty: Optional[str] = None,
    facility_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    schedule_status: Optional[OnCallStatusSchema] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db)
):
    """List on-call schedules."""
    _, tenant_id = get_provider_context(request)
    oc_status = OnCallStatus(schedule_status.value) if schedule_status else None
    return await on_call_service.list_schedules(
        db, tenant_id, provider_id_filter, specialty, facility_id,
        start_date, end_date, oc_status, page, page_size
    )


@router.get(
    "/oncall/schedules/{schedule_id}",
    response_model=OnCallScheduleResponse,
    summary="Get on-call schedule",
    description="Get on-call schedule details"
)
async def get_oncall_schedule(
    schedule_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Get on-call schedule details."""
    _, tenant_id = get_provider_context(request)
    try:
        return await on_call_service.get_schedule(db, tenant_id, schedule_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/oncall/schedules/{schedule_id}",
    response_model=OnCallScheduleResponse,
    summary="Update on-call schedule",
    description="Update an on-call schedule"
)
async def update_oncall_schedule(
    schedule_id: UUID,
    data: OnCallScheduleUpdate,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Update an on-call schedule."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await on_call_service.update_schedule(
            db, provider_id, tenant_id, schedule_id, data
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/oncall/schedules/{schedule_id}",
    response_model=OnCallScheduleResponse,
    summary="Cancel on-call schedule",
    description="Cancel an on-call schedule"
)
async def cancel_oncall_schedule(
    schedule_id: UUID,
    request: Request,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """Cancel an on-call schedule."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await on_call_service.cancel_schedule(
            db, provider_id, tenant_id, schedule_id, reason
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/oncall/schedules/{schedule_id}/activate",
    response_model=OnCallScheduleResponse,
    summary="Activate on-call",
    description="Activate on-call shift"
)
async def activate_oncall_schedule(
    schedule_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Activate an on-call shift."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await on_call_service.activate_schedule(db, provider_id, schedule_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/oncall/schedules/{schedule_id}/complete",
    response_model=OnCallScheduleResponse,
    summary="Complete on-call",
    description="Complete on-call shift"
)
async def complete_oncall_schedule(
    schedule_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Complete an on-call shift."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await on_call_service.complete_schedule(db, provider_id, schedule_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/oncall/current",
    response_model=Optional[OnCallScheduleResponse],
    summary="Get current on-call",
    description="Get current on-call provider for a specialty"
)
async def get_current_oncall(
    specialty: str,
    request: Request,
    facility_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """Get current on-call provider for a specialty."""
    _, tenant_id = get_provider_context(request)
    return await on_call_service.get_current_oncall(db, tenant_id, specialty, facility_id)


# ==================== On-Call Request Endpoints ====================

@router.post(
    "/oncall/requests",
    response_model=OnCallRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create on-call request",
    description="Create an on-call request"
)
async def create_oncall_request(
    data: OnCallRequestCreate,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Create an on-call request."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await on_call_service.create_request(
            db, provider_id, tenant_id, data, get_client_ip(request)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/oncall/requests",
    response_model=OnCallRequestListResponse,
    summary="List on-call requests",
    description="List on-call requests with filters"
)
async def list_oncall_requests(
    request: Request,
    provider_id_filter: Optional[UUID] = Query(None, alias="provider_id"),
    schedule_id: Optional[UUID] = None,
    request_status: Optional[str] = Query(None, alias="status"),
    urgency: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db)
):
    """List on-call requests."""
    _, tenant_id = get_provider_context(request)
    req_status = OnCallRequestStatus(request_status) if request_status else None
    req_urgency = RequestUrgency(urgency) if urgency else None
    return await on_call_service.list_requests(
        db, tenant_id, provider_id_filter, schedule_id, req_status, req_urgency, page, page_size
    )


@router.get(
    "/oncall/requests/pending",
    response_model=List[OnCallRequestResponse],
    summary="Get pending requests",
    description="Get pending on-call requests for current provider"
)
async def get_pending_oncall_requests(
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Get pending on-call requests for current provider."""
    provider_id, tenant_id = get_provider_context(request)
    return await on_call_service.get_pending_requests_for_provider(
        db, provider_id, tenant_id
    )


@router.get(
    "/oncall/requests/{request_id}",
    response_model=OnCallRequestResponse,
    summary="Get on-call request",
    description="Get on-call request details"
)
async def get_oncall_request(
    request_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Get on-call request details."""
    _, tenant_id = get_provider_context(request)
    try:
        return await on_call_service.get_request(db, tenant_id, request_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/oncall/requests/{request_id}/acknowledge",
    response_model=OnCallRequestResponse,
    summary="Acknowledge request",
    description="Acknowledge an on-call request"
)
async def acknowledge_oncall_request(
    request_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Acknowledge an on-call request."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await on_call_service.acknowledge_request(db, provider_id, request_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/oncall/requests/{request_id}/respond",
    response_model=OnCallRequestResponse,
    summary="Respond to request",
    description="Respond to an on-call request"
)
async def respond_to_oncall_request(
    request_id: UUID,
    request: Request,
    response_text: str,
    accept: bool = True,
    db: AsyncSession = Depends(get_async_db)
):
    """Respond to an on-call request."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await on_call_service.respond_to_request(
            db, provider_id, request_id, response_text, accept
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/oncall/requests/{request_id}/complete",
    response_model=OnCallRequestResponse,
    summary="Complete request",
    description="Complete an on-call request"
)
async def complete_oncall_request(
    request_id: UUID,
    resolution: str,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Complete an on-call request."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await on_call_service.complete_request(db, provider_id, request_id, resolution)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================== Alert Endpoints ====================

@router.post(
    "/alerts",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create alert",
    description="Create a clinical alert"
)
async def create_alert(
    data: AlertCreate,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Create a clinical alert."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await alert_service.create_alert(
            db, provider_id, tenant_id, data, get_client_ip(request)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/alerts",
    response_model=AlertListResponse,
    summary="List alerts",
    description="List clinical alerts with filters"
)
async def list_alerts(
    request: Request,
    recipient_id: Optional[UUID] = None,
    patient_id: Optional[UUID] = None,
    priority: Optional[AlertPrioritySchema] = None,
    alert_status: Optional[AlertStatusSchema] = Query(None, alias="status"),
    alert_type: Optional[str] = None,
    unread_only: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db)
):
    """List clinical alerts."""
    provider_id, tenant_id = get_provider_context(request)
    a_priority = AlertPriority(priority.value) if priority else None
    a_status = AlertStatus(alert_status.value) if alert_status else None
    return await alert_service.list_alerts(
        db, tenant_id, recipient_id or provider_id, patient_id,
        a_priority, a_status, alert_type, unread_only, page, page_size
    )


@router.get(
    "/alerts/{alert_id}",
    response_model=AlertResponse,
    summary="Get alert",
    description="Get alert details"
)
async def get_alert(
    alert_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Get alert details."""
    _, tenant_id = get_provider_context(request)
    try:
        return await alert_service.get_alert(db, tenant_id, alert_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/alerts/{alert_id}/read",
    response_model=AlertResponse,
    summary="Mark alert read",
    description="Mark an alert as read"
)
async def mark_alert_read(
    alert_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Mark an alert as read."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await alert_service.mark_as_read(db, provider_id, alert_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/alerts/read",
    summary="Mark alerts read",
    description="Mark multiple alerts as read"
)
async def mark_alerts_read(
    alert_ids: List[UUID],
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Mark multiple alerts as read."""
    provider_id, tenant_id = get_provider_context(request)
    count = await alert_service.mark_multiple_as_read(db, provider_id, tenant_id, alert_ids)
    return {"marked_read": count}


@router.post(
    "/alerts/{alert_id}/acknowledge",
    response_model=AlertResponse,
    summary="Acknowledge alert",
    description="Acknowledge an alert"
)
async def acknowledge_alert(
    alert_id: UUID,
    request: Request,
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """Acknowledge an alert."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await alert_service.acknowledge_alert(db, provider_id, alert_id, notes)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/alerts/{alert_id}/resolve",
    response_model=AlertResponse,
    summary="Resolve alert",
    description="Resolve an alert"
)
async def resolve_alert(
    alert_id: UUID,
    resolution: str,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Resolve an alert."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await alert_service.resolve_alert(db, provider_id, alert_id, resolution)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/alerts/{alert_id}/dismiss",
    response_model=AlertResponse,
    summary="Dismiss alert",
    description="Dismiss an alert"
)
async def dismiss_alert(
    alert_id: UUID,
    request: Request,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """Dismiss an alert."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await alert_service.dismiss_alert(db, provider_id, alert_id, reason)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================== Alert Rule Endpoints ====================

@router.post(
    "/alerts/rules",
    response_model=AlertRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create alert rule",
    description="Create an alert rule"
)
async def create_alert_rule(
    data: AlertRuleCreate,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Create an alert rule."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await alert_service.create_rule(
            db, provider_id, tenant_id, data, get_client_ip(request)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/alerts/rules",
    response_model=AlertRuleListResponse,
    summary="List alert rules",
    description="List alert rules"
)
async def list_alert_rules(
    request: Request,
    rule_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db)
):
    """List alert rules."""
    _, tenant_id = get_provider_context(request)
    from .models import AlertRuleType
    r_type = AlertRuleType(rule_type) if rule_type else None
    return await alert_service.list_rules(db, tenant_id, r_type, is_active, page, page_size)


@router.get(
    "/alerts/rules/{rule_id}",
    response_model=AlertRuleResponse,
    summary="Get alert rule",
    description="Get alert rule details"
)
async def get_alert_rule(
    rule_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Get alert rule details."""
    _, tenant_id = get_provider_context(request)
    try:
        return await alert_service.get_rule(db, tenant_id, rule_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/alerts/rules/{rule_id}",
    response_model=AlertRuleResponse,
    summary="Update alert rule",
    description="Update an alert rule"
)
async def update_alert_rule(
    rule_id: UUID,
    data: AlertRuleUpdate,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Update an alert rule."""
    provider_id, tenant_id = get_provider_context(request)
    try:
        return await alert_service.update_rule(db, provider_id, tenant_id, rule_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/alerts/rules/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete alert rule",
    description="Delete an alert rule"
)
async def delete_alert_rule(
    rule_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Delete an alert rule."""
    _, tenant_id = get_provider_context(request)
    try:
        await alert_service.delete_rule(db, tenant_id, rule_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/alerts/rules/{rule_id}/toggle",
    response_model=AlertRuleResponse,
    summary="Toggle alert rule",
    description="Toggle alert rule active status"
)
async def toggle_alert_rule(
    rule_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Toggle alert rule active status."""
    _, tenant_id = get_provider_context(request)
    try:
        return await alert_service.toggle_rule(db, tenant_id, rule_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
