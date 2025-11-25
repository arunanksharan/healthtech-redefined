"""
Analytics Service
Comprehensive analytics for omnichannel communications
"""
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional, List, Tuple
from uuid import UUID
from sqlalchemy import select, update, func, and_, or_, desc, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from .models import (
    OmnichannelMessage,
    OmnichannelConversation,
    OmnichannelProvider,
    Campaign,
    CampaignRecipient,
    ChannelAnalyticsModel,
    OmniChannelType,
    DeliveryStatus,
    ConversationStatus,
)


class AnalyticsService:
    """
    Comprehensive analytics for omnichannel communications.

    Features:
    - Message delivery analytics
    - Channel performance metrics
    - Conversation analytics
    - Campaign performance
    - Cost analytics
    - Trend analysis
    - Real-time dashboards
    """

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def get_overview_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get high-level overview statistics.

        Args:
            start_date: Start of period
            end_date: End of period

        Returns:
            Overview statistics
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        # Total messages
        result = await self.db.execute(
            select(func.count(OmnichannelMessage.id))
            .where(
                and_(
                    OmnichannelMessage.tenant_id == self.tenant_id,
                    OmnichannelMessage.created_at >= start_date,
                    OmnichannelMessage.created_at <= end_date
                )
            )
        )
        total_messages = result.scalar() or 0

        # Messages by status
        result = await self.db.execute(
            select(
                OmnichannelMessage.delivery_status,
                func.count(OmnichannelMessage.id).label('count')
            )
            .where(
                and_(
                    OmnichannelMessage.tenant_id == self.tenant_id,
                    OmnichannelMessage.created_at >= start_date,
                    OmnichannelMessage.created_at <= end_date
                )
            )
            .group_by(OmnichannelMessage.delivery_status)
        )
        status_counts = {
            row.delivery_status.value if row.delivery_status else 'unknown': row.count
            for row in result
        }

        # Total conversations
        result = await self.db.execute(
            select(func.count(OmnichannelConversation.id))
            .where(
                and_(
                    OmnichannelConversation.tenant_id == self.tenant_id,
                    OmnichannelConversation.started_at >= start_date,
                    OmnichannelConversation.started_at <= end_date
                )
            )
        )
        total_conversations = result.scalar() or 0

        # Active conversations
        result = await self.db.execute(
            select(func.count(OmnichannelConversation.id))
            .where(
                and_(
                    OmnichannelConversation.tenant_id == self.tenant_id,
                    OmnichannelConversation.status.in_([
                        ConversationStatus.OPEN,
                        ConversationStatus.IN_PROGRESS
                    ])
                )
            )
        )
        active_conversations = result.scalar() or 0

        # Calculate rates
        delivered = status_counts.get('delivered', 0)
        sent = sum(status_counts.values()) - status_counts.get('pending', 0) - status_counts.get('queued', 0)
        failed = status_counts.get('failed', 0) + status_counts.get('bounced', 0)

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "messages": {
                "total": total_messages,
                "delivered": delivered,
                "failed": failed,
                "delivery_rate": (delivered / sent * 100) if sent > 0 else 0,
                "status_breakdown": status_counts
            },
            "conversations": {
                "total": total_conversations,
                "active": active_conversations,
                "resolved": total_conversations - active_conversations
            }
        }

    async def get_channel_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get analytics broken down by channel.

        Args:
            start_date: Start of period
            end_date: End of period

        Returns:
            Channel-wise analytics
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        # Messages by channel and status
        result = await self.db.execute(
            select(
                OmnichannelMessage.channel,
                OmnichannelMessage.delivery_status,
                func.count(OmnichannelMessage.id).label('count')
            )
            .where(
                and_(
                    OmnichannelMessage.tenant_id == self.tenant_id,
                    OmnichannelMessage.created_at >= start_date,
                    OmnichannelMessage.created_at <= end_date
                )
            )
            .group_by(OmnichannelMessage.channel, OmnichannelMessage.delivery_status)
        )

        channel_data = {}
        for row in result:
            channel = row.channel.value if row.channel else 'unknown'
            if channel not in channel_data:
                channel_data[channel] = {
                    'total': 0,
                    'delivered': 0,
                    'failed': 0,
                    'pending': 0,
                    'status_breakdown': {}
                }

            status = row.delivery_status.value if row.delivery_status else 'unknown'
            channel_data[channel]['status_breakdown'][status] = row.count
            channel_data[channel]['total'] += row.count

            if status == 'delivered':
                channel_data[channel]['delivered'] += row.count
            elif status in ['failed', 'bounced', 'blocked']:
                channel_data[channel]['failed'] += row.count
            elif status in ['pending', 'queued']:
                channel_data[channel]['pending'] += row.count

        # Calculate rates for each channel
        for channel, data in channel_data.items():
            sent = data['total'] - data['pending']
            data['delivery_rate'] = (data['delivered'] / sent * 100) if sent > 0 else 0
            data['failure_rate'] = (data['failed'] / sent * 100) if sent > 0 else 0

        # Get cost by channel
        result = await self.db.execute(
            select(
                OmnichannelMessage.channel,
                func.sum(OmnichannelMessage.cost).label('total_cost')
            )
            .where(
                and_(
                    OmnichannelMessage.tenant_id == self.tenant_id,
                    OmnichannelMessage.created_at >= start_date,
                    OmnichannelMessage.created_at <= end_date
                )
            )
            .group_by(OmnichannelMessage.channel)
        )

        for row in result:
            channel = row.channel.value if row.channel else 'unknown'
            if channel in channel_data:
                channel_data[channel]['total_cost'] = float(row.total_cost or 0)

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "channels": channel_data
        }

    async def get_daily_trends(
        self,
        days: int = 30,
        channel: Optional[OmniChannelType] = None
    ) -> List[Dict[str, Any]]:
        """
        Get daily message trends.

        Args:
            days: Number of days to look back
            channel: Optional channel filter

        Returns:
            Daily trend data
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        query = select(
            cast(OmnichannelMessage.created_at, Date).label('date'),
            func.count(OmnichannelMessage.id).label('total'),
            func.sum(
                func.case(
                    (OmnichannelMessage.delivery_status == DeliveryStatus.DELIVERED, 1),
                    else_=0
                )
            ).label('delivered'),
            func.sum(
                func.case(
                    (OmnichannelMessage.delivery_status.in_([
                        DeliveryStatus.FAILED,
                        DeliveryStatus.BOUNCED
                    ]), 1),
                    else_=0
                )
            ).label('failed'),
            func.sum(OmnichannelMessage.cost).label('cost')
        ).where(
            and_(
                OmnichannelMessage.tenant_id == self.tenant_id,
                OmnichannelMessage.created_at >= start_date
            )
        )

        if channel:
            query = query.where(OmnichannelMessage.channel == channel)

        query = query.group_by(cast(OmnichannelMessage.created_at, Date))
        query = query.order_by(cast(OmnichannelMessage.created_at, Date))

        result = await self.db.execute(query)

        trends = []
        for row in result:
            trends.append({
                "date": row.date.isoformat() if row.date else None,
                "total": row.total or 0,
                "delivered": row.delivered or 0,
                "failed": row.failed or 0,
                "cost": float(row.cost or 0),
                "delivery_rate": (
                    (row.delivered / row.total * 100)
                    if row.total and row.total > 0 else 0
                )
            })

        return trends

    async def get_hourly_distribution(
        self,
        days: int = 7
    ) -> Dict[int, Dict[str, Any]]:
        """
        Get message distribution by hour of day.

        Args:
            days: Number of days to analyze

        Returns:
            Hourly distribution data
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(
                func.extract('hour', OmnichannelMessage.created_at).label('hour'),
                func.count(OmnichannelMessage.id).label('count'),
                func.sum(
                    func.case(
                        (OmnichannelMessage.delivery_status == DeliveryStatus.DELIVERED, 1),
                        else_=0
                    )
                ).label('delivered')
            )
            .where(
                and_(
                    OmnichannelMessage.tenant_id == self.tenant_id,
                    OmnichannelMessage.created_at >= start_date
                )
            )
            .group_by(func.extract('hour', OmnichannelMessage.created_at))
        )

        distribution = {}
        for row in result:
            hour = int(row.hour) if row.hour is not None else 0
            distribution[hour] = {
                "total": row.count or 0,
                "delivered": row.delivered or 0,
                "delivery_rate": (
                    (row.delivered / row.count * 100)
                    if row.count and row.count > 0 else 0
                )
            }

        return distribution

    async def get_provider_performance(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get performance metrics by provider.

        Args:
            start_date: Start of period
            end_date: End of period

        Returns:
            Provider performance data
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        result = await self.db.execute(
            select(
                OmnichannelMessage.provider_id,
                func.count(OmnichannelMessage.id).label('total'),
                func.sum(
                    func.case(
                        (OmnichannelMessage.delivery_status == DeliveryStatus.DELIVERED, 1),
                        else_=0
                    )
                ).label('delivered'),
                func.sum(
                    func.case(
                        (OmnichannelMessage.delivery_status == DeliveryStatus.FAILED, 1),
                        else_=0
                    )
                ).label('failed'),
                func.sum(OmnichannelMessage.cost).label('total_cost'),
                func.avg(
                    func.extract(
                        'epoch',
                        OmnichannelMessage.delivered_at - OmnichannelMessage.sent_at
                    )
                ).label('avg_delivery_time')
            )
            .where(
                and_(
                    OmnichannelMessage.tenant_id == self.tenant_id,
                    OmnichannelMessage.created_at >= start_date,
                    OmnichannelMessage.created_at <= end_date
                )
            )
            .group_by(OmnichannelMessage.provider_id)
        )

        providers = []
        for row in result:
            providers.append({
                "provider_id": str(row.provider_id) if row.provider_id else None,
                "total_messages": row.total or 0,
                "delivered": row.delivered or 0,
                "failed": row.failed or 0,
                "delivery_rate": (
                    (row.delivered / row.total * 100)
                    if row.total and row.total > 0 else 0
                ),
                "total_cost": float(row.total_cost or 0),
                "avg_delivery_time_seconds": float(row.avg_delivery_time or 0)
            })

        return providers

    async def get_conversation_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get conversation analytics.

        Args:
            start_date: Start of period
            end_date: End of period

        Returns:
            Conversation analytics
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        # Conversations by status
        result = await self.db.execute(
            select(
                OmnichannelConversation.status,
                func.count(OmnichannelConversation.id).label('count')
            )
            .where(
                and_(
                    OmnichannelConversation.tenant_id == self.tenant_id,
                    OmnichannelConversation.started_at >= start_date,
                    OmnichannelConversation.started_at <= end_date
                )
            )
            .group_by(OmnichannelConversation.status)
        )
        status_counts = {
            row.status.value if row.status else 'unknown': row.count
            for row in result
        }

        # Average resolution time
        result = await self.db.execute(
            select(
                func.avg(
                    func.extract(
                        'epoch',
                        OmnichannelConversation.resolved_at - OmnichannelConversation.started_at
                    )
                ).label('avg_resolution_time')
            )
            .where(
                and_(
                    OmnichannelConversation.tenant_id == self.tenant_id,
                    OmnichannelConversation.status == ConversationStatus.RESOLVED,
                    OmnichannelConversation.started_at >= start_date,
                    OmnichannelConversation.resolved_at.isnot(None)
                )
            )
        )
        avg_resolution = result.scalar() or 0

        # First response time (time to first outbound message)
        # This would require a subquery in production

        # Channel crossover (conversations that used multiple channels)
        result = await self.db.execute(
            select(func.count(OmnichannelConversation.id))
            .where(
                and_(
                    OmnichannelConversation.tenant_id == self.tenant_id,
                    OmnichannelConversation.started_at >= start_date,
                    func.array_length(OmnichannelConversation.channels_used, 1) > 1
                )
            )
        )
        multi_channel_count = result.scalar() or 0

        total_conversations = sum(status_counts.values())

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_conversations": total_conversations,
            "status_breakdown": status_counts,
            "resolution": {
                "avg_resolution_time_hours": avg_resolution / 3600 if avg_resolution else 0,
                "resolved_count": status_counts.get('resolved', 0)
            },
            "channel_crossover": {
                "multi_channel_conversations": multi_channel_count,
                "percentage": (
                    multi_channel_count / total_conversations * 100
                    if total_conversations > 0 else 0
                )
            }
        }

    async def get_cost_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = 'day'  # day, week, month
    ) -> Dict[str, Any]:
        """
        Get cost analytics.

        Args:
            start_date: Start of period
            end_date: End of period
            group_by: Grouping period

        Returns:
            Cost analytics
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        # Total cost by channel
        result = await self.db.execute(
            select(
                OmnichannelMessage.channel,
                func.sum(OmnichannelMessage.cost).label('total_cost'),
                func.count(OmnichannelMessage.id).label('message_count')
            )
            .where(
                and_(
                    OmnichannelMessage.tenant_id == self.tenant_id,
                    OmnichannelMessage.created_at >= start_date,
                    OmnichannelMessage.created_at <= end_date
                )
            )
            .group_by(OmnichannelMessage.channel)
        )

        cost_by_channel = {}
        total_cost = 0
        total_messages = 0

        for row in result:
            channel = row.channel.value if row.channel else 'unknown'
            cost = float(row.total_cost or 0)
            count = row.message_count or 0

            cost_by_channel[channel] = {
                "total_cost": cost,
                "message_count": count,
                "cost_per_message": cost / count if count > 0 else 0
            }
            total_cost += cost
            total_messages += count

        # Daily cost trend
        result = await self.db.execute(
            select(
                cast(OmnichannelMessage.created_at, Date).label('date'),
                func.sum(OmnichannelMessage.cost).label('cost')
            )
            .where(
                and_(
                    OmnichannelMessage.tenant_id == self.tenant_id,
                    OmnichannelMessage.created_at >= start_date,
                    OmnichannelMessage.created_at <= end_date
                )
            )
            .group_by(cast(OmnichannelMessage.created_at, Date))
            .order_by(cast(OmnichannelMessage.created_at, Date))
        )

        daily_costs = [
            {"date": row.date.isoformat() if row.date else None, "cost": float(row.cost or 0)}
            for row in result
        ]

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_cost": total_cost,
            "total_messages": total_messages,
            "average_cost_per_message": total_cost / total_messages if total_messages > 0 else 0,
            "cost_by_channel": cost_by_channel,
            "daily_trend": daily_costs
        }

    async def get_engagement_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get patient engagement metrics.

        Args:
            start_date: Start of period
            end_date: End of period

        Returns:
            Engagement metrics
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        # Response rate (inbound messages / outbound messages)
        result = await self.db.execute(
            select(
                OmnichannelMessage.direction,
                func.count(OmnichannelMessage.id).label('count')
            )
            .where(
                and_(
                    OmnichannelMessage.tenant_id == self.tenant_id,
                    OmnichannelMessage.created_at >= start_date,
                    OmnichannelMessage.created_at <= end_date
                )
            )
            .group_by(OmnichannelMessage.direction)
        )
        direction_counts = {row.direction: row.count for row in result}

        outbound = direction_counts.get('outbound', 0)
        inbound = direction_counts.get('inbound', 0)

        # Read rate
        result = await self.db.execute(
            select(
                func.count(OmnichannelMessage.id).label('total'),
                func.sum(
                    func.case(
                        (OmnichannelMessage.read_at.isnot(None), 1),
                        else_=0
                    )
                ).label('read')
            )
            .where(
                and_(
                    OmnichannelMessage.tenant_id == self.tenant_id,
                    OmnichannelMessage.direction == 'outbound',
                    OmnichannelMessage.created_at >= start_date,
                    OmnichannelMessage.created_at <= end_date
                )
            )
        )
        read_data = result.fetchone()
        total_outbound = read_data.total or 0
        read_count = read_data.read or 0

        # Click rate for messages with links
        result = await self.db.execute(
            select(
                func.count(OmnichannelMessage.id).label('total'),
                func.sum(
                    func.case(
                        (OmnichannelMessage.metadata.op('->>')('clicked') == 'true', 1),
                        else_=0
                    )
                ).label('clicked')
            )
            .where(
                and_(
                    OmnichannelMessage.tenant_id == self.tenant_id,
                    OmnichannelMessage.direction == 'outbound',
                    OmnichannelMessage.created_at >= start_date,
                    OmnichannelMessage.created_at <= end_date,
                    OmnichannelMessage.metadata.op('->>')('has_links') == 'true'
                )
            )
        )
        click_data = result.fetchone()

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "messages": {
                "outbound": outbound,
                "inbound": inbound,
                "response_rate": (inbound / outbound * 100) if outbound > 0 else 0
            },
            "engagement": {
                "read_count": read_count,
                "read_rate": (read_count / total_outbound * 100) if total_outbound > 0 else 0,
                "click_count": click_data.clicked or 0 if click_data else 0,
                "click_rate": (
                    (click_data.clicked / click_data.total * 100)
                    if click_data and click_data.total and click_data.total > 0 else 0
                )
            }
        }

    async def record_analytics_snapshot(
        self,
        channel: OmniChannelType,
        date: date
    ) -> None:
        """
        Record daily analytics snapshot for historical tracking.

        Args:
            channel: Channel to record
            date: Date for the snapshot
        """
        start_dt = datetime.combine(date, datetime.min.time())
        end_dt = datetime.combine(date, datetime.max.time())

        # Get day's stats
        result = await self.db.execute(
            select(
                func.count(OmnichannelMessage.id).label('total'),
                func.sum(
                    func.case(
                        (OmnichannelMessage.delivery_status == DeliveryStatus.DELIVERED, 1),
                        else_=0
                    )
                ).label('delivered'),
                func.sum(
                    func.case(
                        (OmnichannelMessage.delivery_status == DeliveryStatus.FAILED, 1),
                        else_=0
                    )
                ).label('failed'),
                func.sum(OmnichannelMessage.cost).label('cost')
            )
            .where(
                and_(
                    OmnichannelMessage.tenant_id == self.tenant_id,
                    OmnichannelMessage.channel == channel,
                    OmnichannelMessage.created_at >= start_dt,
                    OmnichannelMessage.created_at <= end_dt
                )
            )
        )
        stats = result.fetchone()

        if stats and stats.total:
            # Check if record exists
            existing = await self.db.execute(
                select(ChannelAnalyticsModel)
                .where(
                    and_(
                        ChannelAnalyticsModel.tenant_id == self.tenant_id,
                        ChannelAnalyticsModel.channel == channel,
                        ChannelAnalyticsModel.date == date
                    )
                )
            )

            analytics = existing.scalar_one_or_none()

            if analytics:
                # Update existing
                analytics.messages_sent = stats.total
                analytics.messages_delivered = stats.delivered or 0
                analytics.messages_failed = stats.failed or 0
                analytics.total_cost = float(stats.cost or 0)
            else:
                # Create new
                analytics = ChannelAnalyticsModel(
                    tenant_id=self.tenant_id,
                    channel=channel,
                    date=date,
                    messages_sent=stats.total,
                    messages_delivered=stats.delivered or 0,
                    messages_failed=stats.failed or 0,
                    total_cost=float(stats.cost or 0)
                )
                self.db.add(analytics)

            await self.db.flush()
