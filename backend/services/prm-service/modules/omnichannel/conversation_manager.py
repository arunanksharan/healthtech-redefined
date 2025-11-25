"""
Conversation Manager
Cross-channel conversation threading and context management
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from uuid import UUID
import asyncio
from sqlalchemy import select, update, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from .models import (
    OmnichannelConversation,
    OmnichannelMessage,
    ConversationStatus,
    OmniChannelType,
    DeliveryStatus,
    CommunicationPreference,
)


class ConversationManager:
    """
    Manages cross-channel conversation threading and patient context.

    Features:
    - Automatic conversation threading based on patient and time window
    - Cross-channel conversation continuity
    - Context preservation across channel switches
    - Conversation state management
    - Agent assignment and routing
    """

    # Time window for considering messages part of same conversation
    CONVERSATION_WINDOW_HOURS = 24

    # Maximum messages per conversation before starting new thread
    MAX_MESSAGES_PER_CONVERSATION = 500

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def get_or_create_conversation(
        self,
        patient_id: UUID,
        channel: OmniChannelType,
        external_contact: Optional[str] = None,
        subject: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[OmnichannelConversation, bool]:
        """
        Get existing active conversation or create new one.

        Threading rules:
        1. Look for active conversation with same patient on any channel
        2. If found within time window, add to existing conversation
        3. If not found or outside window, create new conversation

        Args:
            patient_id: Patient UUID
            channel: Channel type for this message
            external_contact: External contact identifier
            subject: Optional subject for the conversation
            metadata: Additional metadata

        Returns:
            Tuple of (conversation, is_new)
        """
        # Calculate time window
        window_start = datetime.utcnow() - timedelta(hours=self.CONVERSATION_WINDOW_HOURS)

        # Find active conversation for this patient
        result = await self.db.execute(
            select(OmnichannelConversation)
            .where(
                and_(
                    OmnichannelConversation.tenant_id == self.tenant_id,
                    OmnichannelConversation.patient_id == patient_id,
                    OmnichannelConversation.status.in_([
                        ConversationStatus.OPEN,
                        ConversationStatus.PENDING,
                        ConversationStatus.IN_PROGRESS
                    ]),
                    OmnichannelConversation.last_message_at >= window_start
                )
            )
            .order_by(desc(OmnichannelConversation.last_message_at))
            .limit(1)
        )

        conversation = result.scalar_one_or_none()

        if conversation:
            # Check message count limit
            msg_count = await self._get_message_count(conversation.id)

            if msg_count < self.MAX_MESSAGES_PER_CONVERSATION:
                # Update conversation with new channel if different
                if channel not in (conversation.channels_used or []):
                    conversation.channels_used = (conversation.channels_used or []) + [channel]

                return conversation, False

        # Create new conversation
        new_conversation = OmnichannelConversation(
            tenant_id=self.tenant_id,
            patient_id=patient_id,
            initial_channel=channel,
            current_channel=channel,
            channels_used=[channel],
            status=ConversationStatus.OPEN,
            subject=subject or "Patient Communication",
            external_contact=external_contact,
            metadata=metadata or {},
            started_at=datetime.utcnow(),
            last_message_at=datetime.utcnow()
        )

        self.db.add(new_conversation)
        await self.db.flush()

        logger.info(f"Created new conversation {new_conversation.id} for patient {patient_id}")
        return new_conversation, True

    async def add_message_to_conversation(
        self,
        conversation_id: UUID,
        message: OmnichannelMessage
    ) -> None:
        """
        Add a message to conversation and update conversation metadata.

        Args:
            conversation_id: Conversation UUID
            message: Message to add
        """
        # Link message to conversation
        message.conversation_id = conversation_id

        # Update conversation
        result = await self.db.execute(
            select(OmnichannelConversation)
            .where(OmnichannelConversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()

        if conversation:
            conversation.last_message_at = datetime.utcnow()
            conversation.message_count = (conversation.message_count or 0) + 1

            # Update current channel if different
            if message.channel != conversation.current_channel:
                conversation.current_channel = message.channel

                # Add to channels used if new
                if message.channel not in (conversation.channels_used or []):
                    conversation.channels_used = (conversation.channels_used or []) + [message.channel]

            # Update direction counts
            if message.direction == 'outbound':
                conversation.outbound_count = (conversation.outbound_count or 0) + 1
            else:
                conversation.inbound_count = (conversation.inbound_count or 0) + 1
                conversation.unread_count = (conversation.unread_count or 0) + 1

    async def find_conversation_by_external_id(
        self,
        external_conversation_id: str,
        channel: Optional[OmniChannelType] = None
    ) -> Optional[OmnichannelConversation]:
        """
        Find conversation by external provider conversation ID.

        Args:
            external_conversation_id: Provider's conversation identifier
            channel: Optional channel filter

        Returns:
            Conversation if found
        """
        query = select(OmnichannelConversation).where(
            and_(
                OmnichannelConversation.tenant_id == self.tenant_id,
                OmnichannelConversation.external_conversation_id == external_conversation_id
            )
        )

        if channel:
            query = query.where(
                or_(
                    OmnichannelConversation.initial_channel == channel,
                    OmnichannelConversation.current_channel == channel
                )
            )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def find_conversation_by_contact(
        self,
        external_contact: str,
        channel: OmniChannelType
    ) -> Optional[OmnichannelConversation]:
        """
        Find active conversation by external contact (phone/email).

        Args:
            external_contact: Phone number or email
            channel: Channel type

        Returns:
            Active conversation if found
        """
        window_start = datetime.utcnow() - timedelta(hours=self.CONVERSATION_WINDOW_HOURS)

        result = await self.db.execute(
            select(OmnichannelConversation)
            .where(
                and_(
                    OmnichannelConversation.tenant_id == self.tenant_id,
                    OmnichannelConversation.external_contact == external_contact,
                    OmnichannelConversation.status.in_([
                        ConversationStatus.OPEN,
                        ConversationStatus.PENDING,
                        ConversationStatus.IN_PROGRESS
                    ]),
                    OmnichannelConversation.last_message_at >= window_start
                )
            )
            .order_by(desc(OmnichannelConversation.last_message_at))
            .limit(1)
        )

        return result.scalar_one_or_none()

    async def assign_conversation(
        self,
        conversation_id: UUID,
        assigned_to: UUID,
        assigned_by: Optional[UUID] = None
    ) -> bool:
        """
        Assign conversation to an agent.

        Args:
            conversation_id: Conversation to assign
            assigned_to: Agent UUID
            assigned_by: Who made the assignment

        Returns:
            True if successful
        """
        result = await self.db.execute(
            update(OmnichannelConversation)
            .where(
                and_(
                    OmnichannelConversation.id == conversation_id,
                    OmnichannelConversation.tenant_id == self.tenant_id
                )
            )
            .values(
                assigned_to=assigned_to,
                status=ConversationStatus.IN_PROGRESS,
                assigned_at=datetime.utcnow()
            )
        )

        if result.rowcount > 0:
            logger.info(f"Assigned conversation {conversation_id} to {assigned_to}")
            return True

        return False

    async def resolve_conversation(
        self,
        conversation_id: UUID,
        resolution_notes: Optional[str] = None,
        resolved_by: Optional[UUID] = None
    ) -> bool:
        """
        Mark conversation as resolved.

        Args:
            conversation_id: Conversation to resolve
            resolution_notes: Optional notes
            resolved_by: Who resolved it

        Returns:
            True if successful
        """
        result = await self.db.execute(
            update(OmnichannelConversation)
            .where(
                and_(
                    OmnichannelConversation.id == conversation_id,
                    OmnichannelConversation.tenant_id == self.tenant_id
                )
            )
            .values(
                status=ConversationStatus.RESOLVED,
                resolved_at=datetime.utcnow(),
                resolution_notes=resolution_notes
            )
        )

        if result.rowcount > 0:
            logger.info(f"Resolved conversation {conversation_id}")
            return True

        return False

    async def get_conversation_context(
        self,
        conversation_id: UUID,
        max_messages: int = 20
    ) -> Dict[str, Any]:
        """
        Get conversation context for AI/agent use.

        Args:
            conversation_id: Conversation UUID
            max_messages: Maximum recent messages to include

        Returns:
            Context dictionary with conversation history and metadata
        """
        # Get conversation
        result = await self.db.execute(
            select(OmnichannelConversation)
            .where(OmnichannelConversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            return {}

        # Get recent messages
        result = await self.db.execute(
            select(OmnichannelMessage)
            .where(OmnichannelMessage.conversation_id == conversation_id)
            .order_by(desc(OmnichannelMessage.created_at))
            .limit(max_messages)
        )
        messages = result.scalars().all()

        # Build context
        context = {
            "conversation_id": str(conversation.id),
            "patient_id": str(conversation.patient_id),
            "status": conversation.status.value if conversation.status else None,
            "channels_used": conversation.channels_used or [],
            "current_channel": conversation.current_channel.value if conversation.current_channel else None,
            "started_at": conversation.started_at.isoformat() if conversation.started_at else None,
            "subject": conversation.subject,
            "message_count": conversation.message_count or 0,
            "messages": [
                {
                    "id": str(msg.id),
                    "direction": msg.direction,
                    "channel": msg.channel.value if msg.channel else None,
                    "content": msg.content,
                    "sent_at": msg.sent_at.isoformat() if msg.sent_at else None,
                    "status": msg.delivery_status.value if msg.delivery_status else None
                }
                for msg in reversed(messages)  # Oldest first
            ],
            "metadata": conversation.metadata or {}
        }

        return context

    async def mark_messages_read(
        self,
        conversation_id: UUID,
        read_by: Optional[UUID] = None
    ) -> int:
        """
        Mark all unread messages in conversation as read.

        Args:
            conversation_id: Conversation UUID
            read_by: User who read the messages

        Returns:
            Number of messages marked as read
        """
        # Update messages
        result = await self.db.execute(
            update(OmnichannelMessage)
            .where(
                and_(
                    OmnichannelMessage.conversation_id == conversation_id,
                    OmnichannelMessage.read_at.is_(None),
                    OmnichannelMessage.direction == 'inbound'
                )
            )
            .values(read_at=datetime.utcnow())
        )

        # Update conversation unread count
        await self.db.execute(
            update(OmnichannelConversation)
            .where(OmnichannelConversation.id == conversation_id)
            .values(unread_count=0)
        )

        return result.rowcount

    async def get_patient_conversations(
        self,
        patient_id: UUID,
        status_filter: Optional[List[ConversationStatus]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[OmnichannelConversation]:
        """
        Get all conversations for a patient.

        Args:
            patient_id: Patient UUID
            status_filter: Optional status filter
            limit: Max results
            offset: Pagination offset

        Returns:
            List of conversations
        """
        query = select(OmnichannelConversation).where(
            and_(
                OmnichannelConversation.tenant_id == self.tenant_id,
                OmnichannelConversation.patient_id == patient_id
            )
        )

        if status_filter:
            query = query.where(OmnichannelConversation.status.in_(status_filter))

        query = query.order_by(desc(OmnichannelConversation.last_message_at))
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def switch_channel(
        self,
        conversation_id: UUID,
        new_channel: OmniChannelType
    ) -> bool:
        """
        Switch conversation to a different channel.

        Args:
            conversation_id: Conversation UUID
            new_channel: Channel to switch to

        Returns:
            True if successful
        """
        result = await self.db.execute(
            select(OmnichannelConversation)
            .where(OmnichannelConversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            return False

        # Update current channel
        conversation.current_channel = new_channel

        # Add to channels used if not already present
        if new_channel not in (conversation.channels_used or []):
            conversation.channels_used = (conversation.channels_used or []) + [new_channel]

        logger.info(f"Switched conversation {conversation_id} to channel {new_channel}")
        return True

    async def merge_conversations(
        self,
        primary_conversation_id: UUID,
        secondary_conversation_id: UUID
    ) -> bool:
        """
        Merge two conversations (e.g., when patient identified across channels).

        Args:
            primary_conversation_id: Main conversation to keep
            secondary_conversation_id: Conversation to merge into primary

        Returns:
            True if successful
        """
        # Get both conversations
        result = await self.db.execute(
            select(OmnichannelConversation)
            .where(OmnichannelConversation.id.in_([
                primary_conversation_id,
                secondary_conversation_id
            ]))
        )
        conversations = {str(c.id): c for c in result.scalars().all()}

        primary = conversations.get(str(primary_conversation_id))
        secondary = conversations.get(str(secondary_conversation_id))

        if not primary or not secondary:
            return False

        # Move all messages from secondary to primary
        await self.db.execute(
            update(OmnichannelMessage)
            .where(OmnichannelMessage.conversation_id == secondary_conversation_id)
            .values(conversation_id=primary_conversation_id)
        )

        # Merge channels used
        all_channels = list(set(
            (primary.channels_used or []) +
            (secondary.channels_used or [])
        ))
        primary.channels_used = all_channels

        # Update counts
        primary.message_count = (primary.message_count or 0) + (secondary.message_count or 0)
        primary.inbound_count = (primary.inbound_count or 0) + (secondary.inbound_count or 0)
        primary.outbound_count = (primary.outbound_count or 0) + (secondary.outbound_count or 0)

        # Mark secondary as merged
        secondary.status = ConversationStatus.CLOSED
        secondary.metadata = secondary.metadata or {}
        secondary.metadata['merged_into'] = str(primary_conversation_id)

        logger.info(f"Merged conversation {secondary_conversation_id} into {primary_conversation_id}")
        return True

    async def get_unassigned_conversations(
        self,
        limit: int = 50
    ) -> List[OmnichannelConversation]:
        """
        Get conversations awaiting assignment.

        Args:
            limit: Max results

        Returns:
            List of unassigned conversations
        """
        result = await self.db.execute(
            select(OmnichannelConversation)
            .where(
                and_(
                    OmnichannelConversation.tenant_id == self.tenant_id,
                    OmnichannelConversation.assigned_to.is_(None),
                    OmnichannelConversation.status.in_([
                        ConversationStatus.OPEN,
                        ConversationStatus.PENDING
                    ])
                )
            )
            .order_by(OmnichannelConversation.last_message_at)
            .limit(limit)
        )

        return list(result.scalars().all())

    async def get_agent_workload(
        self,
        agent_id: UUID
    ) -> Dict[str, Any]:
        """
        Get agent's current workload.

        Args:
            agent_id: Agent UUID

        Returns:
            Workload statistics
        """
        # Count active conversations
        result = await self.db.execute(
            select(func.count(OmnichannelConversation.id))
            .where(
                and_(
                    OmnichannelConversation.tenant_id == self.tenant_id,
                    OmnichannelConversation.assigned_to == agent_id,
                    OmnichannelConversation.status == ConversationStatus.IN_PROGRESS
                )
            )
        )
        active_count = result.scalar() or 0

        # Count pending conversations
        result = await self.db.execute(
            select(func.count(OmnichannelConversation.id))
            .where(
                and_(
                    OmnichannelConversation.tenant_id == self.tenant_id,
                    OmnichannelConversation.assigned_to == agent_id,
                    OmnichannelConversation.status == ConversationStatus.PENDING
                )
            )
        )
        pending_count = result.scalar() or 0

        # Count resolved today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.db.execute(
            select(func.count(OmnichannelConversation.id))
            .where(
                and_(
                    OmnichannelConversation.tenant_id == self.tenant_id,
                    OmnichannelConversation.assigned_to == agent_id,
                    OmnichannelConversation.status == ConversationStatus.RESOLVED,
                    OmnichannelConversation.resolved_at >= today_start
                )
            )
        )
        resolved_today = result.scalar() or 0

        return {
            "agent_id": str(agent_id),
            "active_conversations": active_count,
            "pending_conversations": pending_count,
            "resolved_today": resolved_today,
            "total_workload": active_count + pending_count
        }

    async def _get_message_count(self, conversation_id: UUID) -> int:
        """Get message count for a conversation."""
        result = await self.db.execute(
            select(func.count(OmnichannelMessage.id))
            .where(OmnichannelMessage.conversation_id == conversation_id)
        )
        return result.scalar() or 0


class ConversationRouter:
    """
    Intelligent conversation routing based on skills and availability.
    """

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.conversation_manager = ConversationManager(db, tenant_id)

    async def route_conversation(
        self,
        conversation_id: UUID,
        routing_rules: Optional[Dict[str, Any]] = None
    ) -> Optional[UUID]:
        """
        Route conversation to best available agent.

        Args:
            conversation_id: Conversation to route
            routing_rules: Optional routing configuration

        Returns:
            Assigned agent UUID or None
        """
        # Get conversation details
        result = await self.db.execute(
            select(OmnichannelConversation)
            .where(OmnichannelConversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            return None

        # For now, implement round-robin or least-loaded routing
        # This would be extended with skill-based routing in production

        # Get agents with lowest workload
        # This is a simplified implementation
        # Production would check agent online status, skills, etc.

        logger.info(f"Routing conversation {conversation_id}")

        # Return None to indicate manual assignment needed
        # In production, this would return an agent_id
        return None

    async def auto_assign_conversations(
        self,
        max_conversations: int = 10
    ) -> Dict[str, Any]:
        """
        Auto-assign unassigned conversations.

        Args:
            max_conversations: Maximum to assign in one batch

        Returns:
            Assignment results
        """
        unassigned = await self.conversation_manager.get_unassigned_conversations(
            limit=max_conversations
        )

        assigned_count = 0
        failed_count = 0

        for conversation in unassigned:
            agent_id = await self.route_conversation(conversation.id)

            if agent_id:
                success = await self.conversation_manager.assign_conversation(
                    conversation.id,
                    agent_id
                )
                if success:
                    assigned_count += 1
                else:
                    failed_count += 1
            else:
                failed_count += 1

        return {
            "processed": len(unassigned),
            "assigned": assigned_count,
            "failed": failed_count
        }
