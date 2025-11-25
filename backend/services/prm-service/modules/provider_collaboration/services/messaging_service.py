"""
Provider Collaboration Messaging Service
EPIC-015: Secure clinical messaging and presence management
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from modules.provider_collaboration.models import (
    ProviderPresence, ProviderConversation, ConversationParticipant,
    ProviderMessage, MessageReceipt, MessageReaction, CollaborationAuditLog,
    PresenceStatus, ConversationType, MessageType, MessagePriority, MessageStatus
)
from modules.provider_collaboration.schemas import (
    PresenceUpdate, PresenceResponse, BulkPresenceResponse,
    ConversationCreate, ConversationUpdate, ConversationResponse,
    ParticipantResponse, ConversationParticipantAdd,
    MessageCreate, MessageResponse, MessageListResponse,
    MessageReactionCreate, MessageReceiptResponse, MessageReactionResponse
)


class MessagingService:
    """
    Handles provider messaging including:
    - Presence management
    - Conversation management
    - Message sending/receiving
    - Read receipts and reactions
    """

    def __init__(self):
        pass

    # ==================== Presence Management ====================

    async def update_presence(
        self,
        db: AsyncSession,
        provider_id: UUID,
        tenant_id: UUID,
        update: PresenceUpdate,
        device_info: Dict[str, Any] = None,
        ip_address: str = None
    ) -> PresenceResponse:
        """Update provider presence status"""

        result = await db.execute(
            select(ProviderPresence).where(
                and_(
                    ProviderPresence.tenant_id == tenant_id,
                    ProviderPresence.provider_id == provider_id
                )
            )
        )
        presence = result.scalar_one_or_none()

        if not presence:
            presence = ProviderPresence(
                id=uuid4(),
                tenant_id=tenant_id,
                provider_id=provider_id
            )
            db.add(presence)

        presence.status = PresenceStatus(update.status.value)
        presence.status_message = update.status_message
        presence.custom_status = update.custom_status
        presence.location = update.location
        presence.last_activity_at = datetime.now(timezone.utc)

        if device_info:
            presence.device_type = device_info.get('device_type')
            presence.device_id = device_info.get('device_id')

        if ip_address:
            presence.ip_address = ip_address

        await db.commit()
        await db.refresh(presence)

        return PresenceResponse(
            provider_id=presence.provider_id,
            status=presence.status.value,
            status_message=presence.status_message,
            custom_status=presence.custom_status,
            device_type=presence.device_type,
            location=presence.location,
            last_activity_at=presence.last_activity_at,
            is_typing_in=presence.is_typing_in
        )

    async def get_presence(
        self,
        db: AsyncSession,
        provider_id: UUID,
        tenant_id: UUID
    ) -> PresenceResponse:
        """Get provider presence"""

        result = await db.execute(
            select(ProviderPresence).where(
                and_(
                    ProviderPresence.tenant_id == tenant_id,
                    ProviderPresence.provider_id == provider_id
                )
            )
        )
        presence = result.scalar_one_or_none()

        if not presence:
            return PresenceResponse(
                provider_id=provider_id,
                status=PresenceStatus.OFFLINE.value,
                last_activity_at=None
            )

        # Check if presence is stale (> 5 minutes)
        if presence.last_activity_at:
            stale_threshold = datetime.now(timezone.utc) - timedelta(minutes=5)
            if presence.last_activity_at < stale_threshold:
                presence.status = PresenceStatus.OFFLINE

        return PresenceResponse(
            provider_id=presence.provider_id,
            status=presence.status.value,
            status_message=presence.status_message,
            custom_status=presence.custom_status,
            device_type=presence.device_type,
            location=presence.location,
            last_activity_at=presence.last_activity_at,
            is_typing_in=presence.is_typing_in
        )

    async def get_bulk_presence(
        self,
        db: AsyncSession,
        provider_ids: List[UUID],
        tenant_id: UUID
    ) -> Dict[str, PresenceResponse]:
        """Get presence for multiple providers"""

        result = await db.execute(
            select(ProviderPresence).where(
                and_(
                    ProviderPresence.tenant_id == tenant_id,
                    ProviderPresence.provider_id.in_(provider_ids)
                )
            )
        )
        presences = result.scalars().all()

        presence_map = {str(p.provider_id): p for p in presences}
        response = {}

        stale_threshold = datetime.now(timezone.utc) - timedelta(minutes=5)

        for provider_id in provider_ids:
            presence = presence_map.get(str(provider_id))
            if presence:
                status = presence.status.value
                if presence.last_activity_at and presence.last_activity_at < stale_threshold:
                    status = PresenceStatus.OFFLINE.value

                response[str(provider_id)] = PresenceResponse(
                    provider_id=presence.provider_id,
                    status=status,
                    status_message=presence.status_message,
                    custom_status=presence.custom_status,
                    device_type=presence.device_type,
                    location=presence.location,
                    last_activity_at=presence.last_activity_at
                )
            else:
                response[str(provider_id)] = PresenceResponse(
                    provider_id=provider_id,
                    status=PresenceStatus.OFFLINE.value
                )

        return response

    async def set_typing(
        self,
        db: AsyncSession,
        provider_id: UUID,
        tenant_id: UUID,
        conversation_id: Optional[UUID]
    ):
        """Set typing indicator"""

        await db.execute(
            update(ProviderPresence).where(
                and_(
                    ProviderPresence.tenant_id == tenant_id,
                    ProviderPresence.provider_id == provider_id
                )
            ).values(
                is_typing_in=conversation_id,
                last_activity_at=datetime.now(timezone.utc)
            )
        )
        await db.commit()

    # ==================== Conversation Management ====================

    async def create_conversation(
        self,
        db: AsyncSession,
        provider_id: UUID,
        tenant_id: UUID,
        data: ConversationCreate
    ) -> ConversationResponse:
        """Create a new conversation"""

        conversation = ProviderConversation(
            id=uuid4(),
            tenant_id=tenant_id,
            type=ConversationType(data.type.value),
            name=data.name,
            description=data.description,
            patient_id=data.patient_id,
            encounter_id=data.encounter_id,
            created_by=provider_id,
            settings=data.settings or {},
            is_encrypted=data.is_encrypted,
            message_retention_days=data.message_retention_days
        )
        db.add(conversation)

        # Add creator as owner
        creator_participant = ConversationParticipant(
            id=uuid4(),
            conversation_id=conversation.id,
            provider_id=provider_id,
            role="owner",
            can_add_members=True,
            can_remove_members=True,
            can_edit_settings=True,
            can_delete_messages=True
        )
        db.add(creator_participant)

        # Add other participants
        for participant_id in data.participant_ids:
            if participant_id != provider_id:
                participant = ConversationParticipant(
                    id=uuid4(),
                    conversation_id=conversation.id,
                    provider_id=participant_id,
                    role="member"
                )
                db.add(participant)

        # Log action
        audit_log = CollaborationAuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            provider_id=provider_id,
            action="conversation_created",
            action_category="messaging",
            action_description=f"Created {data.type.value} conversation",
            entity_type="conversation",
            entity_id=conversation.id,
            patient_id=data.patient_id,
            details={"type": data.type.value, "participant_count": len(data.participant_ids)}
        )
        db.add(audit_log)

        await db.commit()

        return await self.get_conversation(db, provider_id, tenant_id, conversation.id)

    async def get_conversation(
        self,
        db: AsyncSession,
        provider_id: UUID,
        tenant_id: UUID,
        conversation_id: UUID
    ) -> ConversationResponse:
        """Get conversation details"""

        result = await db.execute(
            select(ProviderConversation)
            .options(selectinload(ProviderConversation.participants))
            .where(
                and_(
                    ProviderConversation.id == conversation_id,
                    ProviderConversation.tenant_id == tenant_id
                )
            )
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise ValueError("Conversation not found")

        # Check if provider is participant
        is_participant = any(p.provider_id == provider_id for p in conversation.participants)
        if not is_participant:
            raise ValueError("Not authorized to access this conversation")

        # Get unread count for this provider
        unread_count = 0
        for p in conversation.participants:
            if p.provider_id == provider_id:
                unread_count = p.unread_count
                break

        participants = [
            ParticipantResponse(
                id=p.id,
                provider_id=p.provider_id,
                role=p.role,
                care_team_role=p.care_team_role.value if p.care_team_role else None,
                is_active=p.is_active,
                last_read_at=p.last_read_at,
                unread_count=p.unread_count,
                joined_at=p.joined_at
            )
            for p in conversation.participants
        ]

        return ConversationResponse(
            id=conversation.id,
            type=conversation.type.value,
            name=conversation.name,
            description=conversation.description,
            avatar_url=conversation.avatar_url,
            patient_id=conversation.patient_id,
            is_encrypted=conversation.is_encrypted,
            is_active=conversation.is_active,
            is_archived=conversation.is_archived,
            last_message_at=conversation.last_message_at,
            last_message_preview=conversation.last_message_preview,
            message_count=conversation.message_count,
            unread_count=unread_count,
            participants=participants,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at
        )

    async def list_conversations(
        self,
        db: AsyncSession,
        provider_id: UUID,
        tenant_id: UUID,
        conversation_type: Optional[ConversationType] = None,
        patient_id: Optional[UUID] = None,
        include_archived: bool = False,
        page: int = 1,
        page_size: int = 50
    ) -> Dict:
        """List provider's conversations"""

        # Subquery to get conversation IDs where provider is participant
        participant_subquery = (
            select(ConversationParticipant.conversation_id)
            .where(
                and_(
                    ConversationParticipant.provider_id == provider_id,
                    ConversationParticipant.is_active == True
                )
            )
        )

        query = (
            select(ProviderConversation)
            .options(selectinload(ProviderConversation.participants))
            .where(
                and_(
                    ProviderConversation.tenant_id == tenant_id,
                    ProviderConversation.id.in_(participant_subquery),
                    ProviderConversation.is_active == True
                )
            )
        )

        if conversation_type:
            query = query.where(ProviderConversation.type == conversation_type)

        if patient_id:
            query = query.where(ProviderConversation.patient_id == patient_id)

        if not include_archived:
            query = query.where(ProviderConversation.is_archived == False)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Get paginated results
        query = query.order_by(desc(ProviderConversation.last_message_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        conversations = result.scalars().all()

        conversation_responses = []
        for conv in conversations:
            unread_count = 0
            for p in conv.participants:
                if p.provider_id == provider_id:
                    unread_count = p.unread_count
                    break

            participants = [
                ParticipantResponse(
                    id=p.id,
                    provider_id=p.provider_id,
                    role=p.role,
                    is_active=p.is_active,
                    last_read_at=p.last_read_at,
                    unread_count=p.unread_count,
                    joined_at=p.joined_at
                )
                for p in conv.participants
            ]

            conversation_responses.append(ConversationResponse(
                id=conv.id,
                type=conv.type.value,
                name=conv.name,
                description=conv.description,
                avatar_url=conv.avatar_url,
                patient_id=conv.patient_id,
                is_encrypted=conv.is_encrypted,
                is_active=conv.is_active,
                is_archived=conv.is_archived,
                last_message_at=conv.last_message_at,
                last_message_preview=conv.last_message_preview,
                message_count=conv.message_count,
                unread_count=unread_count,
                participants=participants,
                created_at=conv.created_at,
                updated_at=conv.updated_at
            ))

        return {
            "conversations": conversation_responses,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    async def add_participant(
        self,
        db: AsyncSession,
        provider_id: UUID,
        tenant_id: UUID,
        conversation_id: UUID,
        data: ConversationParticipantAdd
    ) -> ParticipantResponse:
        """Add participant to conversation"""

        # Verify requester has permission
        result = await db.execute(
            select(ConversationParticipant).where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.provider_id == provider_id
                )
            )
        )
        requester = result.scalar_one_or_none()

        if not requester or not requester.can_add_members:
            raise ValueError("Not authorized to add members")

        # Check if already participant
        result = await db.execute(
            select(ConversationParticipant).where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.provider_id == data.provider_id
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            if existing.is_active:
                raise ValueError("Provider is already a participant")
            # Reactivate
            existing.is_active = True
            existing.left_at = None
            await db.commit()
            await db.refresh(existing)
            return ParticipantResponse(
                id=existing.id,
                provider_id=existing.provider_id,
                role=existing.role,
                is_active=existing.is_active,
                joined_at=existing.joined_at
            )

        participant = ConversationParticipant(
            id=uuid4(),
            conversation_id=conversation_id,
            provider_id=data.provider_id,
            role=data.role,
            care_team_role=data.care_team_role,
            can_add_members=data.can_add_members,
            can_remove_members=data.can_remove_members
        )
        db.add(participant)
        await db.commit()
        await db.refresh(participant)

        return ParticipantResponse(
            id=participant.id,
            provider_id=participant.provider_id,
            role=participant.role,
            is_active=participant.is_active,
            joined_at=participant.joined_at
        )

    async def remove_participant(
        self,
        db: AsyncSession,
        provider_id: UUID,
        conversation_id: UUID,
        participant_provider_id: UUID
    ):
        """Remove participant from conversation"""

        # Verify requester has permission
        result = await db.execute(
            select(ConversationParticipant).where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.provider_id == provider_id
                )
            )
        )
        requester = result.scalar_one_or_none()

        if not requester or not requester.can_remove_members:
            raise ValueError("Not authorized to remove members")

        await db.execute(
            update(ConversationParticipant).where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.provider_id == participant_provider_id
                )
            ).values(
                is_active=False,
                left_at=datetime.now(timezone.utc)
            )
        )
        await db.commit()

    # ==================== Message Management ====================

    async def send_message(
        self,
        db: AsyncSession,
        provider_id: UUID,
        tenant_id: UUID,
        conversation_id: UUID,
        data: MessageCreate,
        ip_address: str = None
    ) -> MessageResponse:
        """Send a message"""

        # Verify sender is participant
        result = await db.execute(
            select(ConversationParticipant).where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.provider_id == provider_id,
                    ConversationParticipant.is_active == True
                )
            )
        )
        participant = result.scalar_one_or_none()

        if not participant:
            raise ValueError("Not authorized to send messages in this conversation")

        # Check if conversation is read-only
        result = await db.execute(
            select(ProviderConversation).where(
                ProviderConversation.id == conversation_id
            )
        )
        conversation = result.scalar_one()

        if conversation.is_read_only:
            raise ValueError("Conversation is read-only")

        # Detect PHI in content
        contains_phi = False
        phi_types = []
        if data.content:
            contains_phi, phi_types = self._detect_phi(data.content)

        message = ProviderMessage(
            id=uuid4(),
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            sender_id=provider_id,
            content=data.content,
            message_type=MessageType(data.message_type.value),
            priority=MessagePriority(data.priority.value),
            attachments=data.attachments if data.attachments else [],
            formatted_content=data.formatted_content,
            mentions=[m.dict() for m in data.mentions] if data.mentions else None,
            reply_to_id=data.reply_to_id,
            thread_root_id=data.reply_to_id,  # Will be updated for threading
            status=MessageStatus.SENT,
            scheduled_at=data.scheduled_at,
            is_scheduled=data.scheduled_at is not None,
            metadata=data.metadata or {},
            client_message_id=data.client_message_id,
            contains_phi=contains_phi,
            phi_detected_types=phi_types if phi_types else None
        )

        # Handle threading
        if data.reply_to_id:
            result = await db.execute(
                select(ProviderMessage).where(
                    ProviderMessage.id == data.reply_to_id
                )
            )
            reply_to = result.scalar_one_or_none()
            if reply_to:
                message.thread_root_id = reply_to.thread_root_id or reply_to.id
                # Increment thread count on root
                await db.execute(
                    update(ProviderMessage).where(
                        ProviderMessage.id == message.thread_root_id
                    ).values(
                        thread_count=ProviderMessage.thread_count + 1
                    )
                )

        db.add(message)

        # Update conversation
        preview = data.content[:100] if data.content else f"[{data.message_type.value}]"
        await db.execute(
            update(ProviderConversation).where(
                ProviderConversation.id == conversation_id
            ).values(
                last_message_at=datetime.now(timezone.utc),
                last_message_preview=preview,
                message_count=ProviderConversation.message_count + 1
            )
        )

        # Update unread counts for other participants
        await db.execute(
            update(ConversationParticipant).where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.provider_id != provider_id,
                    ConversationParticipant.is_active == True
                )
            ).values(
                unread_count=ConversationParticipant.unread_count + 1
            )
        )

        # Log action
        audit_log = CollaborationAuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            provider_id=provider_id,
            action="message_sent",
            action_category="messaging",
            entity_type="message",
            entity_id=message.id,
            patient_id=conversation.patient_id,
            details={
                "conversation_id": str(conversation_id),
                "message_type": data.message_type.value,
                "contains_phi": contains_phi
            },
            ip_address=ip_address
        )
        db.add(audit_log)

        await db.commit()

        return MessageResponse(
            id=message.id,
            conversation_id=message.conversation_id,
            sender_id=message.sender_id,
            content=message.content,
            message_type=message.message_type.value,
            priority=message.priority.value,
            attachments=message.attachments,
            formatted_content=message.formatted_content,
            mentions=message.mentions,
            reply_to_id=message.reply_to_id,
            thread_root_id=message.thread_root_id,
            thread_count=message.thread_count,
            status=message.status.value,
            is_edited=message.is_edited,
            is_recalled=message.is_recalled,
            contains_phi=message.contains_phi,
            receipts=[],
            reactions=[],
            created_at=message.created_at,
            updated_at=message.updated_at
        )

    async def get_messages(
        self,
        db: AsyncSession,
        provider_id: UUID,
        tenant_id: UUID,
        conversation_id: UUID,
        before: Optional[datetime] = None,
        after: Optional[datetime] = None,
        limit: int = 50
    ) -> MessageListResponse:
        """Get messages in a conversation"""

        # Verify requester is participant
        result = await db.execute(
            select(ConversationParticipant).where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.provider_id == provider_id,
                    ConversationParticipant.is_active == True
                )
            )
        )
        if not result.scalar_one_or_none():
            raise ValueError("Not authorized to view messages")

        query = (
            select(ProviderMessage)
            .options(
                selectinload(ProviderMessage.receipts),
                selectinload(ProviderMessage.reactions)
            )
            .where(
                and_(
                    ProviderMessage.conversation_id == conversation_id,
                    ProviderMessage.is_deleted == False
                )
            )
        )

        if before:
            query = query.where(ProviderMessage.created_at < before)

        if after:
            query = query.where(ProviderMessage.created_at > after)

        query = query.order_by(desc(ProviderMessage.created_at)).limit(limit + 1)

        result = await db.execute(query)
        messages = result.scalars().all()

        has_more = len(messages) > limit
        if has_more:
            messages = messages[:limit]

        message_responses = [
            MessageResponse(
                id=msg.id,
                conversation_id=msg.conversation_id,
                sender_id=msg.sender_id,
                content=msg.content if not msg.is_recalled else "[Message recalled]",
                message_type=msg.message_type.value,
                priority=msg.priority.value,
                attachments=msg.attachments if not msg.is_recalled else [],
                formatted_content=msg.formatted_content if not msg.is_recalled else None,
                mentions=msg.mentions,
                reply_to_id=msg.reply_to_id,
                thread_root_id=msg.thread_root_id,
                thread_count=msg.thread_count,
                status=msg.status.value,
                is_edited=msg.is_edited,
                is_recalled=msg.is_recalled,
                contains_phi=msg.contains_phi,
                receipts=[
                    MessageReceiptResponse(
                        provider_id=r.provider_id,
                        delivered_at=r.delivered_at,
                        read_at=r.read_at
                    ) for r in msg.receipts
                ],
                reactions=[
                    MessageReactionResponse(
                        id=r.id,
                        provider_id=r.provider_id,
                        emoji=r.emoji,
                        created_at=r.created_at
                    ) for r in msg.reactions
                ],
                created_at=msg.created_at,
                updated_at=msg.updated_at
            )
            for msg in messages
        ]

        return MessageListResponse(
            messages=message_responses,
            total=len(message_responses),
            has_more=has_more
        )

    async def mark_messages_read(
        self,
        db: AsyncSession,
        provider_id: UUID,
        conversation_id: UUID,
        up_to_message_id: Optional[UUID] = None
    ):
        """Mark messages as read"""

        # Update participant's read status
        await db.execute(
            update(ConversationParticipant).where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.provider_id == provider_id
                )
            ).values(
                last_read_at=datetime.now(timezone.utc),
                last_read_message_id=up_to_message_id,
                unread_count=0
            )
        )

        # Create/update read receipts
        if up_to_message_id:
            # Get messages before this one that don't have read receipt
            result = await db.execute(
                select(ProviderMessage.id).where(
                    and_(
                        ProviderMessage.conversation_id == conversation_id,
                        ProviderMessage.sender_id != provider_id,
                        ~ProviderMessage.id.in_(
                            select(MessageReceipt.message_id).where(
                                and_(
                                    MessageReceipt.provider_id == provider_id,
                                    MessageReceipt.read_at.isnot(None)
                                )
                            )
                        )
                    )
                )
            )
            unread_message_ids = [row[0] for row in result.fetchall()]

            for msg_id in unread_message_ids:
                # Check if receipt exists
                result = await db.execute(
                    select(MessageReceipt).where(
                        and_(
                            MessageReceipt.message_id == msg_id,
                            MessageReceipt.provider_id == provider_id
                        )
                    )
                )
                receipt = result.scalar_one_or_none()

                if receipt:
                    receipt.read_at = datetime.now(timezone.utc)
                else:
                    receipt = MessageReceipt(
                        id=uuid4(),
                        message_id=msg_id,
                        provider_id=provider_id,
                        delivered_at=datetime.now(timezone.utc),
                        read_at=datetime.now(timezone.utc)
                    )
                    db.add(receipt)

        await db.commit()

    async def recall_message(
        self,
        db: AsyncSession,
        provider_id: UUID,
        message_id: UUID,
        reason: Optional[str] = None
    ):
        """Recall a message (within 5 minutes)"""

        result = await db.execute(
            select(ProviderMessage).where(
                ProviderMessage.id == message_id
            )
        )
        message = result.scalar_one_or_none()

        if not message:
            raise ValueError("Message not found")

        if message.sender_id != provider_id:
            raise ValueError("Can only recall your own messages")

        # Check time limit (5 minutes)
        recall_limit = datetime.now(timezone.utc) - timedelta(minutes=5)
        if message.created_at < recall_limit:
            raise ValueError("Message can only be recalled within 5 minutes")

        message.is_recalled = True
        message.recalled_at = datetime.now(timezone.utc)
        message.recall_reason = reason
        message.status = MessageStatus.RECALLED

        await db.commit()

    async def add_reaction(
        self,
        db: AsyncSession,
        provider_id: UUID,
        message_id: UUID,
        data: MessageReactionCreate
    ) -> MessageReactionResponse:
        """Add reaction to a message"""

        # Check if reaction already exists
        result = await db.execute(
            select(MessageReaction).where(
                and_(
                    MessageReaction.message_id == message_id,
                    MessageReaction.provider_id == provider_id,
                    MessageReaction.emoji == data.emoji
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise ValueError("Reaction already exists")

        reaction = MessageReaction(
            id=uuid4(),
            message_id=message_id,
            provider_id=provider_id,
            emoji=data.emoji
        )
        db.add(reaction)
        await db.commit()
        await db.refresh(reaction)

        return MessageReactionResponse(
            id=reaction.id,
            provider_id=reaction.provider_id,
            emoji=reaction.emoji,
            created_at=reaction.created_at
        )

    async def remove_reaction(
        self,
        db: AsyncSession,
        provider_id: UUID,
        message_id: UUID,
        emoji: str
    ):
        """Remove reaction from a message"""

        result = await db.execute(
            select(MessageReaction).where(
                and_(
                    MessageReaction.message_id == message_id,
                    MessageReaction.provider_id == provider_id,
                    MessageReaction.emoji == emoji
                )
            )
        )
        reaction = result.scalar_one_or_none()

        if reaction:
            await db.delete(reaction)
            await db.commit()

    # ==================== Helper Methods ====================

    def _detect_phi(self, content: str) -> tuple[bool, List[str]]:
        """Detect potential PHI in message content"""
        import re

        phi_patterns = {
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'mrn': r'\bMRN[:\s]*\d+\b',
            'dob': r'\b(0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])[-/](\d{4}|\d{2})\b',
        }

        detected_types = []
        for phi_type, pattern in phi_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                detected_types.append(phi_type)

        return len(detected_types) > 0, detected_types
