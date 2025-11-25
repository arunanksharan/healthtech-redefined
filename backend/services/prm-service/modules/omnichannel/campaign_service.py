"""
Campaign Service
Multi-channel campaign management with A/B testing and analytics
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from uuid import UUID
import asyncio
import random
from sqlalchemy import select, update, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from .models import (
    Campaign,
    CampaignRecipient,
    OmnichannelMessage,
    OmnichannelTemplate,
    CommunicationPreference,
    CampaignStatus,
    OmniChannelType,
    DeliveryStatus,
)


class CampaignService:
    """
    Manages multi-channel marketing and engagement campaigns.

    Features:
    - Multi-channel campaign orchestration
    - Patient segmentation
    - A/B testing
    - Scheduling and throttling
    - Performance analytics
    - Regulatory compliance
    """

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def create_campaign(
        self,
        name: str,
        campaign_type: str,
        channels: List[OmniChannelType],
        content_config: Dict[str, Any],
        audience_criteria: Dict[str, Any],
        schedule_config: Optional[Dict[str, Any]] = None,
        ab_test_config: Optional[Dict[str, Any]] = None,
        created_by: Optional[UUID] = None
    ) -> Campaign:
        """
        Create a new campaign.

        Args:
            name: Campaign name
            campaign_type: Type (appointment_reminder, health_education, etc.)
            channels: Target channels
            content_config: Message content configuration
            audience_criteria: Patient selection criteria
            schedule_config: Scheduling configuration
            ab_test_config: A/B testing configuration
            created_by: Creator UUID

        Returns:
            Created campaign
        """
        campaign = Campaign(
            tenant_id=self.tenant_id,
            name=name,
            campaign_type=campaign_type,
            status=CampaignStatus.DRAFT,
            channels=channels,
            content_config=content_config,
            audience_criteria=audience_criteria,
            schedule_config=schedule_config or {},
            ab_test_config=ab_test_config or {},
            created_by=created_by,
            created_at=datetime.utcnow()
        )

        self.db.add(campaign)
        await self.db.flush()

        logger.info(f"Created campaign {campaign.id}: {name}")
        return campaign

    async def update_campaign(
        self,
        campaign_id: UUID,
        updates: Dict[str, Any]
    ) -> Optional[Campaign]:
        """
        Update campaign configuration.

        Args:
            campaign_id: Campaign UUID
            updates: Fields to update

        Returns:
            Updated campaign
        """
        result = await self.db.execute(
            select(Campaign)
            .where(
                and_(
                    Campaign.id == campaign_id,
                    Campaign.tenant_id == self.tenant_id,
                    Campaign.status == CampaignStatus.DRAFT
                )
            )
        )
        campaign = result.scalar_one_or_none()

        if not campaign:
            return None

        for key, value in updates.items():
            if hasattr(campaign, key):
                setattr(campaign, key, value)

        campaign.updated_at = datetime.utcnow()
        return campaign

    async def build_audience(
        self,
        campaign_id: UUID
    ) -> int:
        """
        Build campaign audience based on criteria.

        Args:
            campaign_id: Campaign UUID

        Returns:
            Number of recipients added
        """
        result = await self.db.execute(
            select(Campaign)
            .where(Campaign.id == campaign_id)
        )
        campaign = result.scalar_one_or_none()

        if not campaign:
            return 0

        criteria = campaign.audience_criteria or {}

        # Build query based on criteria
        # This is a simplified implementation
        # Production would have complex patient segmentation

        # Get patients with communication preferences
        query = select(CommunicationPreference).where(
            and_(
                CommunicationPreference.tenant_id == self.tenant_id,
                CommunicationPreference.marketing_opt_in == True
            )
        )

        # Apply channel filter
        if campaign.channels:
            channel_conditions = []
            for channel in campaign.channels:
                if channel == OmniChannelType.EMAIL:
                    channel_conditions.append(CommunicationPreference.email_enabled == True)
                elif channel == OmniChannelType.SMS:
                    channel_conditions.append(CommunicationPreference.sms_enabled == True)
                elif channel == OmniChannelType.WHATSAPP:
                    channel_conditions.append(CommunicationPreference.whatsapp_enabled == True)

            if channel_conditions:
                query = query.where(or_(*channel_conditions))

        # Apply limit if specified
        if criteria.get('max_recipients'):
            query = query.limit(criteria['max_recipients'])

        result = await self.db.execute(query)
        preferences = result.scalars().all()

        # Create recipient records
        recipient_count = 0
        ab_variants = campaign.ab_test_config.get('variants', ['control']) if campaign.ab_test_config else ['control']

        for pref in preferences:
            # Assign A/B variant
            variant = random.choice(ab_variants)

            # Determine preferred channel for this recipient
            preferred_channel = self._get_preferred_channel(pref, campaign.channels)

            recipient = CampaignRecipient(
                campaign_id=campaign_id,
                patient_id=pref.patient_id,
                channel=preferred_channel,
                ab_variant=variant,
                status='pending',
                created_at=datetime.utcnow()
            )

            self.db.add(recipient)
            recipient_count += 1

        # Update campaign stats
        campaign.total_recipients = recipient_count
        campaign.updated_at = datetime.utcnow()

        await self.db.flush()
        logger.info(f"Built audience for campaign {campaign_id}: {recipient_count} recipients")

        return recipient_count

    def _get_preferred_channel(
        self,
        preference: CommunicationPreference,
        available_channels: List[OmniChannelType]
    ) -> OmniChannelType:
        """
        Determine best channel for recipient based on preferences.

        Args:
            preference: Patient's communication preferences
            available_channels: Campaign's available channels

        Returns:
            Best channel for this recipient
        """
        # Priority order based on preference
        channel_priority = [
            (OmniChannelType.WHATSAPP, preference.whatsapp_enabled),
            (OmniChannelType.SMS, preference.sms_enabled),
            (OmniChannelType.EMAIL, preference.email_enabled),
            (OmniChannelType.VOICE, preference.voice_enabled),
        ]

        for channel, enabled in channel_priority:
            if enabled and channel in available_channels:
                return channel

        # Default to first available
        return available_channels[0] if available_channels else OmniChannelType.SMS

    async def schedule_campaign(
        self,
        campaign_id: UUID,
        scheduled_at: datetime
    ) -> bool:
        """
        Schedule campaign for execution.

        Args:
            campaign_id: Campaign UUID
            scheduled_at: When to start sending

        Returns:
            True if scheduled
        """
        result = await self.db.execute(
            update(Campaign)
            .where(
                and_(
                    Campaign.id == campaign_id,
                    Campaign.tenant_id == self.tenant_id,
                    Campaign.status.in_([CampaignStatus.DRAFT, CampaignStatus.PAUSED])
                )
            )
            .values(
                status=CampaignStatus.SCHEDULED,
                scheduled_at=scheduled_at,
                updated_at=datetime.utcnow()
            )
        )

        if result.rowcount > 0:
            logger.info(f"Scheduled campaign {campaign_id} for {scheduled_at}")
            return True

        return False

    async def start_campaign(
        self,
        campaign_id: UUID
    ) -> bool:
        """
        Start campaign execution immediately.

        Args:
            campaign_id: Campaign UUID

        Returns:
            True if started
        """
        result = await self.db.execute(
            update(Campaign)
            .where(
                and_(
                    Campaign.id == campaign_id,
                    Campaign.tenant_id == self.tenant_id,
                    Campaign.status.in_([CampaignStatus.DRAFT, CampaignStatus.SCHEDULED])
                )
            )
            .values(
                status=CampaignStatus.ACTIVE,
                started_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )

        if result.rowcount > 0:
            logger.info(f"Started campaign {campaign_id}")
            return True

        return False

    async def pause_campaign(
        self,
        campaign_id: UUID
    ) -> bool:
        """
        Pause active campaign.

        Args:
            campaign_id: Campaign UUID

        Returns:
            True if paused
        """
        result = await self.db.execute(
            update(Campaign)
            .where(
                and_(
                    Campaign.id == campaign_id,
                    Campaign.tenant_id == self.tenant_id,
                    Campaign.status == CampaignStatus.ACTIVE
                )
            )
            .values(
                status=CampaignStatus.PAUSED,
                updated_at=datetime.utcnow()
            )
        )

        if result.rowcount > 0:
            logger.info(f"Paused campaign {campaign_id}")
            return True

        return False

    async def complete_campaign(
        self,
        campaign_id: UUID
    ) -> bool:
        """
        Mark campaign as completed.

        Args:
            campaign_id: Campaign UUID

        Returns:
            True if completed
        """
        result = await self.db.execute(
            update(Campaign)
            .where(
                and_(
                    Campaign.id == campaign_id,
                    Campaign.tenant_id == self.tenant_id
                )
            )
            .values(
                status=CampaignStatus.COMPLETED,
                completed_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )

        if result.rowcount > 0:
            logger.info(f"Completed campaign {campaign_id}")
            return True

        return False

    async def get_pending_recipients(
        self,
        campaign_id: UUID,
        batch_size: int = 100
    ) -> List[CampaignRecipient]:
        """
        Get batch of pending recipients for sending.

        Args:
            campaign_id: Campaign UUID
            batch_size: Maximum recipients to return

        Returns:
            List of pending recipients
        """
        result = await self.db.execute(
            select(CampaignRecipient)
            .where(
                and_(
                    CampaignRecipient.campaign_id == campaign_id,
                    CampaignRecipient.status == 'pending'
                )
            )
            .limit(batch_size)
        )

        return list(result.scalars().all())

    async def update_recipient_status(
        self,
        recipient_id: UUID,
        status: str,
        message_id: Optional[UUID] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Update recipient delivery status.

        Args:
            recipient_id: Recipient UUID
            status: New status
            message_id: Associated message UUID
            error_message: Error message if failed

        Returns:
            True if updated
        """
        values = {
            'status': status,
            'updated_at': datetime.utcnow()
        }

        if message_id:
            values['message_id'] = message_id

        if status == 'sent':
            values['sent_at'] = datetime.utcnow()
        elif status == 'delivered':
            values['delivered_at'] = datetime.utcnow()
        elif status == 'failed':
            values['error_message'] = error_message

        result = await self.db.execute(
            update(CampaignRecipient)
            .where(CampaignRecipient.id == recipient_id)
            .values(**values)
        )

        return result.rowcount > 0

    async def get_campaign_analytics(
        self,
        campaign_id: UUID
    ) -> Dict[str, Any]:
        """
        Get comprehensive campaign analytics.

        Args:
            campaign_id: Campaign UUID

        Returns:
            Analytics dictionary
        """
        # Get campaign
        result = await self.db.execute(
            select(Campaign)
            .where(Campaign.id == campaign_id)
        )
        campaign = result.scalar_one_or_none()

        if not campaign:
            return {}

        # Get recipient stats by status
        result = await self.db.execute(
            select(
                CampaignRecipient.status,
                func.count(CampaignRecipient.id).label('count')
            )
            .where(CampaignRecipient.campaign_id == campaign_id)
            .group_by(CampaignRecipient.status)
        )
        status_counts = {row.status: row.count for row in result}

        # Get channel breakdown
        result = await self.db.execute(
            select(
                CampaignRecipient.channel,
                func.count(CampaignRecipient.id).label('count')
            )
            .where(CampaignRecipient.campaign_id == campaign_id)
            .group_by(CampaignRecipient.channel)
        )
        channel_counts = {
            row.channel.value if row.channel else 'unknown': row.count
            for row in result
        }

        # Get A/B test results if applicable
        ab_results = {}
        if campaign.ab_test_config and campaign.ab_test_config.get('variants'):
            result = await self.db.execute(
                select(
                    CampaignRecipient.ab_variant,
                    CampaignRecipient.status,
                    func.count(CampaignRecipient.id).label('count')
                )
                .where(CampaignRecipient.campaign_id == campaign_id)
                .group_by(CampaignRecipient.ab_variant, CampaignRecipient.status)
            )

            for row in result:
                variant = row.ab_variant or 'control'
                if variant not in ab_results:
                    ab_results[variant] = {}
                ab_results[variant][row.status] = row.count

        # Calculate rates
        total = sum(status_counts.values())
        sent = status_counts.get('sent', 0) + status_counts.get('delivered', 0)
        delivered = status_counts.get('delivered', 0)
        failed = status_counts.get('failed', 0)

        return {
            "campaign_id": str(campaign_id),
            "campaign_name": campaign.name,
            "status": campaign.status.value if campaign.status else None,
            "total_recipients": total,
            "sent": sent,
            "delivered": delivered,
            "failed": failed,
            "pending": status_counts.get('pending', 0),
            "delivery_rate": (delivered / sent * 100) if sent > 0 else 0,
            "failure_rate": (failed / total * 100) if total > 0 else 0,
            "status_breakdown": status_counts,
            "channel_breakdown": channel_counts,
            "ab_test_results": ab_results,
            "started_at": campaign.started_at.isoformat() if campaign.started_at else None,
            "completed_at": campaign.completed_at.isoformat() if campaign.completed_at else None,
            "duration_minutes": (
                (campaign.completed_at - campaign.started_at).total_seconds() / 60
                if campaign.started_at and campaign.completed_at else None
            )
        }

    async def get_ab_test_winner(
        self,
        campaign_id: UUID,
        metric: str = 'delivery_rate'
    ) -> Optional[Dict[str, Any]]:
        """
        Determine A/B test winner based on specified metric.

        Args:
            campaign_id: Campaign UUID
            metric: Metric to compare

        Returns:
            Winner analysis
        """
        analytics = await self.get_campaign_analytics(campaign_id)
        ab_results = analytics.get('ab_test_results', {})

        if not ab_results or len(ab_results) < 2:
            return None

        variant_metrics = {}

        for variant, statuses in ab_results.items():
            total = sum(statuses.values())
            delivered = statuses.get('delivered', 0)
            sent = statuses.get('sent', 0) + delivered

            if metric == 'delivery_rate':
                variant_metrics[variant] = (delivered / sent * 100) if sent > 0 else 0
            else:
                variant_metrics[variant] = delivered

        if not variant_metrics:
            return None

        winner = max(variant_metrics, key=variant_metrics.get)

        return {
            "winner": winner,
            "metric": metric,
            "results": variant_metrics,
            "improvement": (
                (variant_metrics[winner] - min(variant_metrics.values())) /
                min(variant_metrics.values()) * 100
                if min(variant_metrics.values()) > 0 else 0
            )
        }

    async def get_campaigns(
        self,
        status_filter: Optional[List[CampaignStatus]] = None,
        campaign_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Campaign]:
        """
        Get campaigns with optional filters.

        Args:
            status_filter: Filter by status
            campaign_type: Filter by type
            limit: Max results
            offset: Pagination offset

        Returns:
            List of campaigns
        """
        query = select(Campaign).where(Campaign.tenant_id == self.tenant_id)

        if status_filter:
            query = query.where(Campaign.status.in_(status_filter))

        if campaign_type:
            query = query.where(Campaign.campaign_type == campaign_type)

        query = query.order_by(desc(Campaign.created_at))
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def clone_campaign(
        self,
        campaign_id: UUID,
        new_name: str
    ) -> Optional[Campaign]:
        """
        Clone an existing campaign.

        Args:
            campaign_id: Source campaign UUID
            new_name: Name for the clone

        Returns:
            New campaign
        """
        result = await self.db.execute(
            select(Campaign)
            .where(Campaign.id == campaign_id)
        )
        source = result.scalar_one_or_none()

        if not source:
            return None

        clone = Campaign(
            tenant_id=self.tenant_id,
            name=new_name,
            campaign_type=source.campaign_type,
            status=CampaignStatus.DRAFT,
            channels=source.channels,
            content_config=source.content_config,
            audience_criteria=source.audience_criteria,
            schedule_config={},  # Clear schedule
            ab_test_config=source.ab_test_config,
            created_at=datetime.utcnow()
        )

        self.db.add(clone)
        await self.db.flush()

        logger.info(f"Cloned campaign {campaign_id} to {clone.id}")
        return clone


class CampaignExecutor:
    """
    Executes campaign message delivery.
    """

    def __init__(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        omnichannel_service: Any  # OmnichannelService
    ):
        self.db = db
        self.tenant_id = tenant_id
        self.omnichannel_service = omnichannel_service
        self.campaign_service = CampaignService(db, tenant_id)

    async def execute_batch(
        self,
        campaign_id: UUID,
        batch_size: int = 100,
        delay_ms: int = 100
    ) -> Dict[str, Any]:
        """
        Execute a batch of campaign messages.

        Args:
            campaign_id: Campaign UUID
            batch_size: Number of messages to send
            delay_ms: Delay between messages (rate limiting)

        Returns:
            Execution results
        """
        # Get campaign
        result = await self.db.execute(
            select(Campaign)
            .where(Campaign.id == campaign_id)
        )
        campaign = result.scalar_one_or_none()

        if not campaign or campaign.status != CampaignStatus.ACTIVE:
            return {"error": "Campaign not active"}

        # Get pending recipients
        recipients = await self.campaign_service.get_pending_recipients(
            campaign_id,
            batch_size
        )

        if not recipients:
            # Check if campaign is complete
            remaining = await self.db.execute(
                select(func.count(CampaignRecipient.id))
                .where(
                    and_(
                        CampaignRecipient.campaign_id == campaign_id,
                        CampaignRecipient.status == 'pending'
                    )
                )
            )
            if remaining.scalar() == 0:
                await self.campaign_service.complete_campaign(campaign_id)

            return {"sent": 0, "remaining": remaining.scalar() or 0}

        sent_count = 0
        failed_count = 0

        for recipient in recipients:
            try:
                # Get content for this recipient (handle A/B variants)
                content = self._get_content_for_variant(
                    campaign.content_config,
                    recipient.ab_variant
                )

                # Send message
                message_result = await self.omnichannel_service.send_message(
                    patient_id=recipient.patient_id,
                    channel=recipient.channel,
                    content=content.get('body', ''),
                    subject=content.get('subject'),
                    template_id=content.get('template_id'),
                    template_variables=content.get('variables', {}),
                    metadata={
                        'campaign_id': str(campaign_id),
                        'ab_variant': recipient.ab_variant
                    }
                )

                if message_result.get('success'):
                    await self.campaign_service.update_recipient_status(
                        recipient.id,
                        'sent',
                        message_id=message_result.get('message_id')
                    )
                    sent_count += 1
                else:
                    await self.campaign_service.update_recipient_status(
                        recipient.id,
                        'failed',
                        error_message=message_result.get('error')
                    )
                    failed_count += 1

                # Rate limiting delay
                if delay_ms > 0:
                    await asyncio.sleep(delay_ms / 1000)

            except Exception as e:
                logger.error(f"Failed to send campaign message: {e}")
                await self.campaign_service.update_recipient_status(
                    recipient.id,
                    'failed',
                    error_message=str(e)
                )
                failed_count += 1

        # Update campaign stats
        await self._update_campaign_stats(campaign_id)

        return {
            "sent": sent_count,
            "failed": failed_count,
            "batch_size": len(recipients)
        }

    def _get_content_for_variant(
        self,
        content_config: Dict[str, Any],
        variant: Optional[str]
    ) -> Dict[str, Any]:
        """
        Get content for specific A/B variant.

        Args:
            content_config: Campaign content configuration
            variant: A/B variant name

        Returns:
            Content for this variant
        """
        if not variant or variant == 'control':
            return content_config.get('default', content_config)

        variants = content_config.get('variants', {})
        return variants.get(variant, content_config.get('default', content_config))

    async def _update_campaign_stats(self, campaign_id: UUID) -> None:
        """Update campaign statistics."""
        # Get counts
        result = await self.db.execute(
            select(
                CampaignRecipient.status,
                func.count(CampaignRecipient.id).label('count')
            )
            .where(CampaignRecipient.campaign_id == campaign_id)
            .group_by(CampaignRecipient.status)
        )
        counts = {row.status: row.count for row in result}

        # Update campaign
        await self.db.execute(
            update(Campaign)
            .where(Campaign.id == campaign_id)
            .values(
                sent_count=counts.get('sent', 0) + counts.get('delivered', 0),
                delivered_count=counts.get('delivered', 0),
                failed_count=counts.get('failed', 0),
                updated_at=datetime.utcnow()
            )
        )
