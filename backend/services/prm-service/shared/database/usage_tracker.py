"""
Usage Tracking and Metering Service

EPIC-004: Multi-Tenancy Implementation
US-004.4: Tenant Resource Management
US-004.8: Tenant Monitoring & Analytics

Provides comprehensive usage tracking:
- Real-time usage collection
- Daily aggregation
- Usage analytics
- Billing metrics
- SLA tracking
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

import redis.asyncio as aioredis
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class UsageMetric(str, Enum):
    """Types of usage metrics."""
    API_CALLS = "api_calls"
    STORAGE_BYTES = "storage_bytes"
    ACTIVE_USERS = "active_users"
    PATIENTS_ACCESSED = "patients_accessed"
    APPOINTMENTS_CREATED = "appointments_created"
    ENCOUNTERS_CREATED = "encounters_created"
    DOCUMENTS_UPLOADED = "documents_uploaded"
    DOCUMENTS_BYTES = "documents_bytes"
    AI_REQUESTS = "ai_requests"
    AI_TOKENS = "ai_tokens"
    TELEHEALTH_MINUTES = "telehealth_minutes"
    SMS_SENT = "sms_sent"
    EMAILS_SENT = "emails_sent"
    WHATSAPP_MESSAGES = "whatsapp_messages"
    ERRORS = "errors"


@dataclass
class UsageEvent:
    """A single usage event."""
    tenant_id: str
    metric: UsageMetric
    value: int = 1
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UsageSummary:
    """Summary of usage for a period."""
    tenant_id: str
    period_start: datetime
    period_end: datetime
    metrics: Dict[str, int] = field(default_factory=dict)
    by_endpoint: Dict[str, int] = field(default_factory=dict)
    by_user: Dict[str, int] = field(default_factory=dict)
    errors_by_type: Dict[str, int] = field(default_factory=dict)


class UsageTracker:
    """
    Tracks and aggregates usage metrics for tenants.

    Uses a two-tier system:
    1. Redis for real-time counters
    2. PostgreSQL for daily aggregates
    """

    def __init__(
        self,
        redis_client: aioredis.Redis,
        db_session_factory,
        flush_interval: int = 60,  # Flush to DB every 60 seconds
    ):
        self.redis = redis_client
        self.db_factory = db_session_factory
        self.flush_interval = flush_interval
        self._buffer: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._flush_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the background flush task."""
        if self._flush_task is None:
            self._flush_task = asyncio.create_task(self._flush_loop())
            logger.info("Usage tracker started")

    async def stop(self):
        """Stop the background flush task."""
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
            self._flush_task = None

        # Final flush
        await self.flush()
        logger.info("Usage tracker stopped")

    async def track(self, event: UsageEvent):
        """
        Track a usage event.

        Args:
            event: Usage event to track
        """
        # Update Redis counter (real-time)
        key = self._get_redis_key(event.tenant_id, event.metric, event.timestamp)
        await self.redis.incrby(key, event.value)
        await self.redis.expire(key, 86400 * 2)  # Keep for 2 days

        # Update local buffer (for batch DB writes)
        buffer_key = f"{event.tenant_id}:{event.timestamp.date()}"
        self._buffer[buffer_key][event.metric.value] += event.value

        # Track by endpoint if provided
        if event.metadata.get("endpoint"):
            endpoint_key = f"{buffer_key}:endpoint:{event.metadata['endpoint']}"
            self._buffer[buffer_key][f"endpoint:{event.metadata['endpoint']}"] += event.value

        # Track by user if provided
        if event.user_id:
            self._buffer[buffer_key][f"user:{event.user_id}"] = 1  # Unique user flag

        logger.debug(f"Tracked {event.metric.value}={event.value} for tenant {event.tenant_id}")

    async def track_simple(
        self,
        tenant_id: str,
        metric: UsageMetric,
        value: int = 1,
        **metadata,
    ):
        """Simplified tracking interface."""
        await self.track(UsageEvent(
            tenant_id=tenant_id,
            metric=metric,
            value=value,
            metadata=metadata,
        ))

    async def get_realtime_count(
        self,
        tenant_id: str,
        metric: UsageMetric,
        timestamp: Optional[datetime] = None,
    ) -> int:
        """Get real-time count for a metric."""
        ts = timestamp or datetime.now(timezone.utc)
        key = self._get_redis_key(tenant_id, metric, ts)
        value = await self.redis.get(key)
        return int(value) if value else 0

    async def get_daily_usage(
        self,
        tenant_id: str,
        date: datetime,
    ) -> Dict[str, int]:
        """Get aggregated daily usage."""
        db = self.db_factory()
        try:
            result = db.execute(
                text("""
                    SELECT
                        api_calls, storage_bytes, active_users, unique_patients_accessed,
                        appointments_created, encounters_created, documents_uploaded,
                        documents_bytes, ai_requests, ai_tokens_used, telehealth_minutes,
                        sms_sent, emails_sent, whatsapp_messages, errors,
                        api_calls_by_endpoint, errors_by_type
                    FROM tenant_usage_daily
                    WHERE tenant_id = :tenant_id AND date = :date
                """),
                {"tenant_id": tenant_id, "date": date.date()}
            ).fetchone()

            if not result:
                return {}

            return {
                "api_calls": result.api_calls,
                "storage_bytes": result.storage_bytes,
                "active_users": result.active_users,
                "unique_patients_accessed": result.unique_patients_accessed,
                "appointments_created": result.appointments_created,
                "encounters_created": result.encounters_created,
                "documents_uploaded": result.documents_uploaded,
                "documents_bytes": result.documents_bytes,
                "ai_requests": result.ai_requests,
                "ai_tokens_used": result.ai_tokens_used,
                "telehealth_minutes": result.telehealth_minutes,
                "sms_sent": result.sms_sent,
                "emails_sent": result.emails_sent,
                "whatsapp_messages": result.whatsapp_messages,
                "errors": result.errors,
                "api_calls_by_endpoint": result.api_calls_by_endpoint or {},
                "errors_by_type": result.errors_by_type or {},
            }
        finally:
            db.close()

    async def get_usage_summary(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> UsageSummary:
        """Get usage summary for a date range."""
        db = self.db_factory()
        try:
            result = db.execute(
                text("""
                    SELECT
                        SUM(api_calls) as api_calls,
                        MAX(storage_bytes) as storage_bytes,
                        SUM(active_users) as active_users,
                        SUM(unique_patients_accessed) as patients_accessed,
                        SUM(appointments_created) as appointments_created,
                        SUM(encounters_created) as encounters_created,
                        SUM(documents_uploaded) as documents_uploaded,
                        SUM(documents_bytes) as documents_bytes,
                        SUM(ai_requests) as ai_requests,
                        SUM(ai_tokens_used) as ai_tokens,
                        SUM(telehealth_minutes) as telehealth_minutes,
                        SUM(sms_sent) as sms_sent,
                        SUM(emails_sent) as emails_sent,
                        SUM(whatsapp_messages) as whatsapp_messages,
                        SUM(errors) as errors
                    FROM tenant_usage_daily
                    WHERE tenant_id = :tenant_id
                      AND date >= :start_date
                      AND date <= :end_date
                """),
                {
                    "tenant_id": tenant_id,
                    "start_date": start_date.date(),
                    "end_date": end_date.date(),
                }
            ).fetchone()

            metrics = {}
            if result:
                for col in result._mapping.keys():
                    val = getattr(result, col)
                    if val is not None:
                        metrics[col] = int(val)

            return UsageSummary(
                tenant_id=tenant_id,
                period_start=start_date,
                period_end=end_date,
                metrics=metrics,
            )
        finally:
            db.close()

    async def get_usage_trend(
        self,
        tenant_id: str,
        metric: UsageMetric,
        days: int = 30,
    ) -> List[Tuple[datetime, int]]:
        """Get usage trend for a metric over time."""
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=days)

        # Map metric to column name
        column_map = {
            UsageMetric.API_CALLS: "api_calls",
            UsageMetric.STORAGE_BYTES: "storage_bytes",
            UsageMetric.ACTIVE_USERS: "active_users",
            UsageMetric.PATIENTS_ACCESSED: "unique_patients_accessed",
            UsageMetric.APPOINTMENTS_CREATED: "appointments_created",
            UsageMetric.ENCOUNTERS_CREATED: "encounters_created",
            UsageMetric.DOCUMENTS_UPLOADED: "documents_uploaded",
            UsageMetric.AI_REQUESTS: "ai_requests",
            UsageMetric.TELEHEALTH_MINUTES: "telehealth_minutes",
            UsageMetric.SMS_SENT: "sms_sent",
            UsageMetric.EMAILS_SENT: "emails_sent",
            UsageMetric.WHATSAPP_MESSAGES: "whatsapp_messages",
            UsageMetric.ERRORS: "errors",
        }

        column = column_map.get(metric, "api_calls")

        db = self.db_factory()
        try:
            results = db.execute(
                text(f"""
                    SELECT date, COALESCE({column}, 0) as value
                    FROM tenant_usage_daily
                    WHERE tenant_id = :tenant_id
                      AND date >= :start_date
                      AND date <= :end_date
                    ORDER BY date
                """),
                {
                    "tenant_id": tenant_id,
                    "start_date": start_date,
                    "end_date": end_date,
                }
            ).fetchall()

            return [
                (datetime.combine(r.date, datetime.min.time(), tzinfo=timezone.utc), r.value)
                for r in results
            ]
        finally:
            db.close()

    async def flush(self):
        """Flush buffered data to database."""
        if not self._buffer:
            return

        # Swap buffer
        buffer = self._buffer
        self._buffer = defaultdict(lambda: defaultdict(int))

        db = self.db_factory()
        try:
            for key, metrics in buffer.items():
                parts = key.split(":")
                tenant_id = parts[0]
                date_str = parts[1]

                # Separate out by-endpoint and by-user metrics
                endpoint_metrics = {}
                regular_metrics = {}

                for metric_name, value in metrics.items():
                    if metric_name.startswith("endpoint:"):
                        endpoint_metrics[metric_name[9:]] = value
                    elif metric_name.startswith("user:"):
                        pass  # Count unique users differently
                    else:
                        regular_metrics[metric_name] = value

                # Count unique users
                unique_users = sum(1 for k in metrics.keys() if k.startswith("user:"))
                if unique_users > 0:
                    regular_metrics["active_users"] = unique_users

                # Build upsert query
                columns = list(regular_metrics.keys())
                if not columns:
                    continue

                update_parts = [f"{col} = tenant_usage_daily.{col} + EXCLUDED.{col}" for col in columns]

                import json
                db.execute(
                    text(f"""
                        INSERT INTO tenant_usage_daily (
                            tenant_id, date, {', '.join(columns)},
                            api_calls_by_endpoint, created_at, updated_at
                        )
                        VALUES (
                            :tenant_id, :date, {', '.join(f':{col}' for col in columns)},
                            :endpoint_metrics, :now, :now
                        )
                        ON CONFLICT (tenant_id, date)
                        DO UPDATE SET
                            {', '.join(update_parts)},
                            api_calls_by_endpoint = tenant_usage_daily.api_calls_by_endpoint || EXCLUDED.api_calls_by_endpoint,
                            updated_at = :now
                    """),
                    {
                        "tenant_id": tenant_id,
                        "date": date_str,
                        **regular_metrics,
                        "endpoint_metrics": json.dumps(endpoint_metrics),
                        "now": datetime.now(timezone.utc),
                    }
                )

            db.commit()
            logger.debug(f"Flushed {len(buffer)} tenant usage records to database")

        except Exception as e:
            logger.error(f"Error flushing usage data: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    async def _flush_loop(self):
        """Background task to periodically flush data."""
        while True:
            try:
                await asyncio.sleep(self.flush_interval)
                await self.flush()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in flush loop: {e}")

    def _get_redis_key(
        self,
        tenant_id: str,
        metric: UsageMetric,
        timestamp: datetime,
    ) -> str:
        """Generate Redis key for a metric counter."""
        date_str = timestamp.strftime("%Y-%m-%d")
        hour = timestamp.hour
        return f"usage:{tenant_id}:{metric.value}:{date_str}:{hour}"


class BillingMetricsCollector:
    """
    Collects and aggregates metrics for billing purposes.
    """

    def __init__(self, usage_tracker: UsageTracker):
        self.tracker = usage_tracker

    async def get_billing_summary(
        self,
        tenant_id: str,
        billing_period_start: datetime,
        billing_period_end: datetime,
    ) -> Dict[str, Any]:
        """
        Get billing summary for a period.

        Returns aggregated metrics that can be used for invoicing.
        """
        summary = await self.tracker.get_usage_summary(
            tenant_id, billing_period_start, billing_period_end
        )

        # Calculate billable items
        return {
            "tenant_id": tenant_id,
            "period_start": billing_period_start.isoformat(),
            "period_end": billing_period_end.isoformat(),
            "metrics": {
                "api_calls": summary.metrics.get("api_calls", 0),
                "storage_gb": summary.metrics.get("storage_bytes", 0) / (1024**3),
                "ai_requests": summary.metrics.get("ai_requests", 0),
                "ai_tokens": summary.metrics.get("ai_tokens", 0),
                "telehealth_minutes": summary.metrics.get("telehealth_minutes", 0),
                "sms_sent": summary.metrics.get("sms_sent", 0),
                "emails_sent": summary.metrics.get("emails_sent", 0),
                "whatsapp_messages": summary.metrics.get("whatsapp_messages", 0),
            },
            "peak_active_users": summary.metrics.get("active_users", 0),
            "total_patients_accessed": summary.metrics.get("patients_accessed", 0),
            "documents_uploaded": summary.metrics.get("documents_uploaded", 0),
            "documents_storage_gb": summary.metrics.get("documents_bytes", 0) / (1024**3),
        }

    async def calculate_overage(
        self,
        tenant_id: str,
        billing_period_start: datetime,
        billing_period_end: datetime,
    ) -> Dict[str, Any]:
        """Calculate overage charges beyond plan limits."""
        summary = await self.get_billing_summary(
            tenant_id, billing_period_start, billing_period_end
        )

        # Get tenant limits
        db = self.tracker.db_factory()
        try:
            result = db.execute(
                text("SELECT tier, limits FROM tenants WHERE id = :id"),
                {"id": tenant_id}
            ).fetchone()

            if not result:
                return {"error": "Tenant not found"}

            limits = result.limits or {}

            # Calculate overages
            overages = {}
            metrics = summary["metrics"]

            overage_rates = {
                "api_calls": 0.001,  # $0.001 per API call over limit
                "storage_gb": 0.10,  # $0.10 per GB over limit
                "ai_requests": 0.01,  # $0.01 per AI request over limit
                "telehealth_minutes": 0.05,  # $0.05 per minute over limit
                "sms_sent": 0.05,  # $0.05 per SMS over limit
            }

            for metric, rate in overage_rates.items():
                limit_key = f"max_{metric}"
                limit = limits.get(limit_key, 0)
                actual = metrics.get(metric, 0)

                if actual > limit > 0:
                    overage = actual - limit
                    overages[metric] = {
                        "limit": limit,
                        "actual": actual,
                        "overage": overage,
                        "rate": rate,
                        "charge": round(overage * rate, 2),
                    }

            total_overage = sum(o["charge"] for o in overages.values())

            return {
                "tenant_id": tenant_id,
                "period": {
                    "start": billing_period_start.isoformat(),
                    "end": billing_period_end.isoformat(),
                },
                "tier": result.tier,
                "overages": overages,
                "total_overage_charge": total_overage,
            }
        finally:
            db.close()


# Global tracker instance (initialized at app startup)
usage_tracker: Optional[UsageTracker] = None


async def init_usage_tracker(redis_client: aioredis.Redis, db_session_factory):
    """Initialize the global usage tracker."""
    global usage_tracker
    usage_tracker = UsageTracker(redis_client, db_session_factory)
    await usage_tracker.start()
    return usage_tracker


async def shutdown_usage_tracker():
    """Shutdown the global usage tracker."""
    global usage_tracker
    if usage_tracker:
        await usage_tracker.stop()
        usage_tracker = None
