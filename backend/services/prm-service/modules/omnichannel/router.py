"""
Omnichannel Communications Router
API endpoints for omnichannel communication platform
EPIC-013: Omnichannel Communications Platform
"""
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query, status, BackgroundTasks, Request
from sqlalchemy.orm import Session
from loguru import logger

from shared.database.connection import get_db

from .service import OmnichannelService
from .schemas import (
    # Message schemas
    SendMessageRequest, MessageResponse, MessageListResponse,
    BulkSendRequest, MessageStatusUpdate,
    # Conversation schemas
    ConversationCreate, ConversationUpdate, ConversationResponse,
    ConversationListResponse, ConversationDetailResponse,
    ConversationAssign, ConversationTransfer,
    # Preference schemas
    PreferenceCreate, PreferenceUpdate, PreferenceResponse,
    # Consent schemas
    ConsentCreate, ConsentResponse, ConsentListResponse, OptOutRequest, OptOutResponse,
    # Provider schemas
    ProviderCreate, ProviderUpdate, ProviderResponse, ProviderListResponse,
    # Template schemas
    TemplateCreate, TemplateUpdate, TemplateResponse, TemplateListResponse,
    TemplateRenderRequest, TemplateRenderResponse,
    # Campaign schemas
    CampaignCreate, CampaignUpdate, CampaignResponse, CampaignListResponse, CampaignAction,
    # Segment schemas
    SegmentCreate, SegmentUpdate, SegmentResponse, SegmentListResponse, SegmentEstimateResponse,
    # Unified Inbox schemas
    InboxFilter, InboxListResponse, CannedResponseCreate, CannedResponseResponse, CannedResponseListResponse,
    # Analytics schemas
    AnalyticsSummary, CampaignMetrics, EngagementScoreResponse,
    # SLA schemas
    SLAConfigCreate, SLAConfigResponse, SLATrackingResponse,
    # Webhook schemas
    WhatsAppWebhookPayload, TwilioWebhookPayload, SendGridWebhookPayload,
    # Enums
    ChannelType, ConversationStatus, ConversationPriority, TemplateStatus, CampaignStatus
)
from .models import DeliveryStatus


router = APIRouter(prefix="/omnichannel", tags=["Omnichannel Communications"])


# ==================== Message Endpoints ====================

@router.post(
    "/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a message",
    description="Send a message through the omnichannel platform"
)
async def send_message(
    request: SendMessageRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Send a message to a recipient.

    - Automatically selects the best channel based on patient preferences
    - Supports WhatsApp, SMS, Email, Voice
    - Can use pre-approved templates
    - Respects consent and opt-out preferences
    """
    service = OmnichannelService(db)
    return await service.send_message(request)


@router.post(
    "/messages/bulk",
    summary="Send bulk messages",
    description="Send messages to multiple recipients"
)
async def send_bulk_messages(
    request: BulkSendRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Send messages to multiple recipients.

    - Supports personalization per recipient
    - Respects individual opt-out preferences
    - Returns detailed results for each recipient
    """
    service = OmnichannelService(db)
    return await service.send_bulk_messages(request)


@router.get(
    "/messages/{message_id}",
    response_model=MessageResponse,
    summary="Get message details"
)
async def get_message(
    message_id: UUID,
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Get details of a specific message"""
    service = OmnichannelService(db)
    message = service.db.query(service.OmnichannelMessage).filter(
        service.OmnichannelMessage.id == message_id,
        service.OmnichannelMessage.tenant_id == tenant_id
    ).first()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    return service._message_to_response(message)


@router.get(
    "/messages",
    response_model=MessageListResponse,
    summary="List messages"
)
async def list_messages(
    tenant_id: UUID = Query(...),
    conversation_id: Optional[UUID] = Query(None),
    patient_id: Optional[UUID] = Query(None),
    channel: Optional[ChannelType] = Query(None),
    status: Optional[DeliveryStatus] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List messages with optional filters"""
    from .models import OmnichannelMessage
    from sqlalchemy import desc

    query = db.query(OmnichannelMessage).filter(
        OmnichannelMessage.tenant_id == tenant_id
    )

    if conversation_id:
        query = query.filter(OmnichannelMessage.conversation_id == conversation_id)
    if patient_id:
        query = query.filter(OmnichannelMessage.patient_id == patient_id)
    if channel:
        query = query.filter(OmnichannelMessage.channel == channel.value)
    if status:
        query = query.filter(OmnichannelMessage.status == status)

    total = query.count()
    messages = query.order_by(desc(OmnichannelMessage.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    service = OmnichannelService(db)
    return MessageListResponse(
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
        has_previous=page > 1,
        messages=[service._message_to_response(m) for m in messages]
    )


# ==================== Conversation Endpoints ====================

@router.get(
    "/conversations",
    response_model=ConversationListResponse,
    summary="List conversations"
)
async def list_conversations(
    tenant_id: UUID = Query(...),
    status: Optional[List[ConversationStatus]] = Query(None),
    assigned_agent_id: Optional[UUID] = Query(None),
    patient_id: Optional[UUID] = Query(None),
    channel: Optional[ChannelType] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List conversations with filters"""
    service = OmnichannelService(db)
    conversations, total = await service.list_conversations(
        tenant_id=tenant_id,
        status=status,
        assigned_agent_id=assigned_agent_id,
        patient_id=patient_id,
        channel=channel,
        page=page,
        page_size=page_size
    )

    return ConversationListResponse(
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
        has_previous=page > 1,
        conversations=conversations
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetailResponse,
    summary="Get conversation details"
)
async def get_conversation(
    conversation_id: UUID,
    tenant_id: UUID = Query(...),
    include_messages: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Get conversation with messages"""
    service = OmnichannelService(db)
    conversation = await service.get_conversation(tenant_id, conversation_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    response = ConversationDetailResponse(
        id=conversation.id,
        tenant_id=conversation.tenant_id,
        patient_id=conversation.patient_id,
        external_contact_id=conversation.external_contact_id,
        external_contact_name=conversation.external_contact_name,
        conversation_key=conversation.conversation_key,
        primary_channel=ChannelType(conversation.primary_channel.value),
        channels_used=conversation.channels_used or [],
        status=conversation.status,
        priority=conversation.priority,
        sentiment=conversation.sentiment,
        assigned_agent_id=conversation.assigned_agent_id,
        assigned_team_id=conversation.assigned_team_id,
        message_count=conversation.message_count,
        unread_count=conversation.unread_count,
        topic=conversation.topic,
        tags=conversation.tags or [],
        first_message_at=conversation.first_message_at,
        last_message_at=conversation.last_message_at,
        first_response_at=conversation.first_response_at,
        first_response_sla_met=conversation.first_response_sla_met,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[service._message_to_response(m) for m in conversation.messages] if include_messages else [],
        context=conversation.context or {}
    )

    return response


@router.patch(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
    summary="Update conversation"
)
async def update_conversation(
    conversation_id: UUID,
    update: ConversationUpdate,
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Update conversation status, assignment, etc."""
    service = OmnichannelService(db)
    conversation = await service.update_conversation(tenant_id, conversation_id, update)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation


@router.post(
    "/conversations/{conversation_id}/assign",
    response_model=ConversationResponse,
    summary="Assign conversation to agent"
)
async def assign_conversation(
    conversation_id: UUID,
    assignment: ConversationAssign,
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Assign conversation to an agent"""
    update = ConversationUpdate(assigned_agent_id=assignment.agent_id)
    service = OmnichannelService(db)
    conversation = await service.update_conversation(tenant_id, conversation_id, update)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation


@router.post(
    "/conversations/{conversation_id}/resolve",
    response_model=ConversationResponse,
    summary="Resolve conversation"
)
async def resolve_conversation(
    conversation_id: UUID,
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Mark conversation as resolved"""
    update = ConversationUpdate(status=ConversationStatus.RESOLVED)
    service = OmnichannelService(db)
    conversation = await service.update_conversation(tenant_id, conversation_id, update)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation


# ==================== Preference Endpoints ====================

@router.get(
    "/preferences/{patient_id}",
    response_model=PreferenceResponse,
    summary="Get patient preferences"
)
async def get_preference(
    patient_id: UUID,
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Get communication preferences for a patient"""
    service = OmnichannelService(db)
    preference = await service.get_preference(tenant_id, patient_id)

    if not preference:
        raise HTTPException(status_code=404, detail="Preferences not found")

    return preference


@router.post(
    "/preferences",
    response_model=PreferenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or update preferences"
)
async def create_or_update_preference(
    data: PreferenceCreate,
    db: Session = Depends(get_db)
):
    """Create or update patient communication preferences"""
    service = OmnichannelService(db)
    return await service.create_or_update_preference(data)


@router.patch(
    "/preferences/{patient_id}",
    response_model=PreferenceResponse,
    summary="Update preferences"
)
async def update_preference(
    patient_id: UUID,
    update: PreferenceUpdate,
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Update patient preferences"""
    data = PreferenceCreate(
        tenant_id=tenant_id,
        patient_id=patient_id,
        **update.dict(exclude_unset=True)
    )
    service = OmnichannelService(db)
    return await service.create_or_update_preference(data)


# ==================== Consent/Opt-out Endpoints ====================

@router.post(
    "/opt-out",
    response_model=OptOutResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record opt-out"
)
async def record_opt_out(
    request: OptOutRequest,
    db: Session = Depends(get_db)
):
    """Record an opt-out for a contact"""
    service = OmnichannelService(db)
    return await service.record_opt_out(request)


@router.get(
    "/opt-out/check",
    summary="Check opt-out status"
)
async def check_opt_out(
    tenant_id: UUID = Query(...),
    contact: str = Query(...),
    channel: Optional[ChannelType] = Query(None),
    db: Session = Depends(get_db)
):
    """Check if a contact has opted out"""
    service = OmnichannelService(db)
    is_opted_out = await service._is_opted_out(tenant_id, contact, channel)
    return {"opted_out": is_opted_out}


# ==================== Provider Endpoints ====================

@router.get(
    "/providers",
    response_model=ProviderListResponse,
    summary="List providers"
)
async def list_providers(
    tenant_id: UUID = Query(...),
    channel: Optional[ChannelType] = Query(None),
    is_active: Optional[bool] = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List configured providers"""
    service = OmnichannelService(db)
    providers, total = await service.list_providers(
        tenant_id=tenant_id,
        channel=channel,
        is_active=is_active,
        page=page,
        page_size=page_size
    )

    return ProviderListResponse(
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
        has_previous=page > 1,
        providers=providers
    )


@router.post(
    "/providers",
    response_model=ProviderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create provider"
)
async def create_provider(
    data: ProviderCreate,
    db: Session = Depends(get_db)
):
    """Configure a new communication provider"""
    service = OmnichannelService(db)
    return await service.create_provider(data)


@router.get(
    "/providers/{provider_id}",
    response_model=ProviderResponse,
    summary="Get provider"
)
async def get_provider(
    provider_id: UUID,
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Get provider details"""
    service = OmnichannelService(db)
    provider = await service.get_provider(tenant_id, provider_id)

    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    return provider


# ==================== Template Endpoints ====================

@router.get(
    "/templates",
    response_model=TemplateListResponse,
    summary="List templates"
)
async def list_templates(
    tenant_id: UUID = Query(...),
    channel: Optional[ChannelType] = Query(None),
    status: Optional[TemplateStatus] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List message templates"""
    service = OmnichannelService(db)
    templates, total = await service.list_templates(
        tenant_id=tenant_id,
        channel=channel,
        status=status,
        page=page,
        page_size=page_size
    )

    return TemplateListResponse(
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
        has_previous=page > 1,
        templates=templates
    )


@router.post(
    "/templates",
    response_model=TemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create template"
)
async def create_template(
    data: TemplateCreate,
    db: Session = Depends(get_db)
):
    """Create a new message template"""
    service = OmnichannelService(db)
    return await service.create_template(data)


@router.get(
    "/templates/{template_id}",
    response_model=TemplateResponse,
    summary="Get template"
)
async def get_template(
    template_id: UUID,
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Get template details"""
    service = OmnichannelService(db)
    template = await service.get_template(tenant_id, template_id)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return template


@router.post(
    "/templates/{template_id}/render",
    response_model=TemplateRenderResponse,
    summary="Render template"
)
async def render_template(
    template_id: UUID,
    request: TemplateRenderRequest,
    db: Session = Depends(get_db)
):
    """Render a template with variables"""
    service = OmnichannelService(db)
    body, subject = await service._render_template(template_id, request.variables)
    return TemplateRenderResponse(subject=subject, body=body, body_html=None)


# ==================== Webhook Endpoints ====================

@router.post(
    "/webhooks/whatsapp",
    summary="WhatsApp webhook receiver"
)
async def whatsapp_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Receive WhatsApp webhook callbacks.
    Handles message status updates and incoming messages.
    """
    try:
        data = await request.json()
        logger.info(f"WhatsApp webhook received: {data.get('entry', [{}])[0].get('id', 'unknown')}")

        service = OmnichannelService(db)

        # Process webhook
        for entry in data.get('entry', []):
            for change in entry.get('changes', []):
                value = change.get('value', {})

                # Handle status updates
                for status in value.get('statuses', []):
                    message_id = status.get('id')
                    message_status = status.get('status')

                    status_mapping = {
                        'sent': DeliveryStatus.SENT,
                        'delivered': DeliveryStatus.DELIVERED,
                        'read': DeliveryStatus.READ,
                        'failed': DeliveryStatus.FAILED
                    }

                    if message_id and message_status in status_mapping:
                        await service.update_message_status(
                            external_id=message_id,
                            status_update=MessageStatusUpdate(
                                external_id=message_id,
                                status=status_mapping[message_status],
                                provider_response=status
                            )
                        )

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/webhooks/whatsapp",
    summary="WhatsApp webhook verification"
)
async def verify_whatsapp_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """
    WhatsApp webhook verification endpoint.
    Required for initial webhook setup.
    """
    # In production, verify hub_verify_token matches your configured token
    if hub_mode == "subscribe":
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post(
    "/webhooks/twilio",
    summary="Twilio webhook receiver"
)
async def twilio_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Receive Twilio webhook callbacks.
    Handles SMS and Voice status updates.
    """
    try:
        form = await request.form()
        data = dict(form)
        logger.info(f"Twilio webhook received: {data.get('MessageSid', data.get('CallSid', 'unknown'))}")

        service = OmnichannelService(db)

        # Get message ID
        message_sid = data.get('MessageSid') or data.get('SmsSid')
        call_sid = data.get('CallSid')
        external_id = message_sid or call_sid

        if external_id:
            message_status = data.get('MessageStatus') or data.get('SmsStatus') or data.get('CallStatus')

            status_mapping = {
                'queued': DeliveryStatus.QUEUED,
                'sent': DeliveryStatus.SENT,
                'delivered': DeliveryStatus.DELIVERED,
                'failed': DeliveryStatus.FAILED,
                'undelivered': DeliveryStatus.FAILED,
                'completed': DeliveryStatus.DELIVERED,  # For voice
            }

            if message_status and message_status.lower() in status_mapping:
                await service.update_message_status(
                    external_id=external_id,
                    status_update=MessageStatusUpdate(
                        external_id=external_id,
                        status=status_mapping[message_status.lower()],
                        error_code=data.get('ErrorCode'),
                        error_message=data.get('ErrorMessage'),
                        provider_response=data
                    )
                )

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Twilio webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/webhooks/sendgrid",
    summary="SendGrid webhook receiver"
)
async def sendgrid_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Receive SendGrid webhook callbacks.
    Handles email delivery status updates.
    """
    try:
        data = await request.json()
        logger.info(f"SendGrid webhook received: {len(data)} events")

        service = OmnichannelService(db)

        # SendGrid sends an array of events
        events = data if isinstance(data, list) else [data]

        for event in events:
            message_id = event.get('sg_message_id')
            event_type = event.get('event')

            if message_id:
                status_mapping = {
                    'processed': DeliveryStatus.QUEUED,
                    'delivered': DeliveryStatus.DELIVERED,
                    'open': DeliveryStatus.READ,
                    'click': DeliveryStatus.READ,
                    'bounce': DeliveryStatus.BOUNCED,
                    'dropped': DeliveryStatus.FAILED,
                    'deferred': DeliveryStatus.PENDING,
                    'blocked': DeliveryStatus.BLOCKED,
                    'spam_report': DeliveryStatus.BLOCKED,
                }

                if event_type in status_mapping:
                    await service.update_message_status(
                        external_id=message_id.split('.')[0],  # Remove .filter suffix
                        status_update=MessageStatusUpdate(
                            external_id=message_id,
                            status=status_mapping[event_type],
                            error_message=event.get('reason'),
                            provider_response=event
                        )
                    )

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"SendGrid webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Analytics Endpoints ====================

@router.get(
    "/analytics/summary",
    response_model=AnalyticsSummary,
    summary="Get analytics summary"
)
async def get_analytics_summary(
    tenant_id: UUID = Query(...),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get communication analytics summary"""
    from datetime import date
    from .models import ChannelAnalyticsDaily, OmniChannelType
    from sqlalchemy import func

    # Default to last 30 days
    end = date.today() if not end_date else date.fromisoformat(end_date)
    start = end - timedelta(days=30) if not start_date else date.fromisoformat(start_date)

    # Query analytics
    analytics = db.query(
        ChannelAnalyticsDaily.channel,
        func.sum(ChannelAnalyticsDaily.messages_sent).label('sent'),
        func.sum(ChannelAnalyticsDaily.messages_delivered).label('delivered'),
        func.sum(ChannelAnalyticsDaily.messages_failed).label('failed'),
        func.sum(ChannelAnalyticsDaily.messages_received).label('received'),
        func.sum(ChannelAnalyticsDaily.conversations_started).label('conversations_started'),
        func.sum(ChannelAnalyticsDaily.conversations_resolved).label('conversations_resolved'),
        func.avg(ChannelAnalyticsDaily.delivery_rate).label('delivery_rate'),
        func.avg(ChannelAnalyticsDaily.avg_first_response_seconds).label('avg_response'),
        func.sum(ChannelAnalyticsDaily.total_cost).label('total_cost')
    ).filter(
        ChannelAnalyticsDaily.tenant_id == tenant_id,
        ChannelAnalyticsDaily.date >= start,
        ChannelAnalyticsDaily.date <= end
    ).group_by(ChannelAnalyticsDaily.channel).all()

    # Build response
    channel_breakdown = []
    total_sent = 0
    total_delivered = 0
    total_conversations = 0
    total_cost = 0

    for row in analytics:
        channel_breakdown.append({
            'channel': row.channel.value if row.channel else 'unknown',
            'messages_sent': row.sent or 0,
            'messages_delivered': row.delivered or 0,
            'messages_failed': row.failed or 0,
            'messages_received': row.received or 0,
            'delivery_rate': row.delivery_rate,
            'avg_response_time_seconds': row.avg_response,
            'total_cost': float(row.total_cost or 0)
        })

        total_sent += row.sent or 0
        total_delivered += row.delivered or 0
        total_conversations += row.conversations_started or 0
        total_cost += float(row.total_cost or 0)

    return AnalyticsSummary(
        period_start=datetime.combine(start, datetime.min.time()),
        period_end=datetime.combine(end, datetime.max.time()),
        total_messages_sent=total_sent,
        total_messages_delivered=total_delivered,
        total_conversations=total_conversations,
        total_conversations_resolved=sum(r.conversations_resolved or 0 for r in analytics),
        overall_delivery_rate=(total_delivered / total_sent * 100) if total_sent > 0 else None,
        total_cost=total_cost,
        channel_breakdown=channel_breakdown
    )


# ==================== Unified Inbox Endpoints ====================

@router.get(
    "/inbox",
    response_model=InboxListResponse,
    summary="Get unified inbox"
)
async def get_inbox(
    tenant_id: UUID = Query(...),
    agent_id: Optional[UUID] = Query(None),
    status: Optional[List[ConversationStatus]] = Query(None),
    channel: Optional[List[ChannelType]] = Query(None),
    priority: Optional[List[ConversationPriority]] = Query(None),
    unassigned_only: bool = Query(False),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get unified inbox for agent"""
    from .models import OmnichannelConversation
    from sqlalchemy import desc, func, or_

    query = db.query(OmnichannelConversation).filter(
        OmnichannelConversation.tenant_id == tenant_id
    )

    if agent_id:
        query = query.filter(OmnichannelConversation.assigned_agent_id == agent_id)

    if unassigned_only:
        query = query.filter(OmnichannelConversation.assigned_agent_id == None)

    if status:
        query = query.filter(OmnichannelConversation.status.in_(status))
    else:
        # Default to open conversations
        query = query.filter(OmnichannelConversation.status.in_([
            ConversationStatus.NEW,
            ConversationStatus.OPEN,
            ConversationStatus.PENDING
        ]))

    if channel:
        channel_values = [c.value for c in channel]
        query = query.filter(OmnichannelConversation.primary_channel.in_(channel_values))

    if priority:
        query = query.filter(OmnichannelConversation.priority.in_(priority))

    if search:
        query = query.filter(
            or_(
                OmnichannelConversation.external_contact_id.ilike(f"%{search}%"),
                OmnichannelConversation.external_contact_name.ilike(f"%{search}%"),
                OmnichannelConversation.topic.ilike(f"%{search}%")
            )
        )

    # Get unread total
    unread_total = query.with_entities(
        func.sum(OmnichannelConversation.unread_count)
    ).scalar() or 0

    # Get status counts
    status_counts = db.query(
        OmnichannelConversation.status,
        func.count(OmnichannelConversation.id)
    ).filter(
        OmnichannelConversation.tenant_id == tenant_id
    ).group_by(OmnichannelConversation.status).all()

    counts_by_status = {s.value: c for s, c in status_counts}

    total = query.count()
    conversations = query.order_by(
        desc(OmnichannelConversation.last_message_at)
    ).offset((page - 1) * page_size).limit(page_size).all()

    return InboxListResponse(
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
        has_previous=page > 1,
        conversations=conversations,
        unread_total=unread_total,
        counts_by_status=counts_by_status
    )


# ==================== Canned Responses Endpoints ====================

@router.get(
    "/canned-responses",
    response_model=CannedResponseListResponse,
    summary="List canned responses"
)
async def list_canned_responses(
    tenant_id: UUID = Query(...),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List canned responses for quick replies"""
    from .models import CannedResponse
    from sqlalchemy import or_

    query = db.query(CannedResponse).filter(
        CannedResponse.tenant_id == tenant_id,
        CannedResponse.is_active == True
    )

    if category:
        query = query.filter(CannedResponse.category == category)

    if search:
        query = query.filter(
            or_(
                CannedResponse.name.ilike(f"%{search}%"),
                CannedResponse.shortcut.ilike(f"%{search}%"),
                CannedResponse.content.ilike(f"%{search}%")
            )
        )

    total = query.count()
    responses = query.order_by(CannedResponse.name).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return CannedResponseListResponse(
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
        has_previous=page > 1,
        responses=responses
    )


@router.post(
    "/canned-responses",
    response_model=CannedResponseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create canned response"
)
async def create_canned_response(
    data: CannedResponseCreate,
    db: Session = Depends(get_db)
):
    """Create a new canned response"""
    from .models import CannedResponse
    from uuid import uuid4

    response = CannedResponse(
        id=uuid4(),
        tenant_id=data.tenant_id,
        name=data.name,
        shortcut=data.shortcut,
        content=data.content,
        category=data.category,
        tags=data.tags,
        is_global=data.is_global,
        variables=data.variables
    )

    db.add(response)
    db.commit()
    db.refresh(response)

    return response
