"""
Tenant Monitoring and Analytics Service

EPIC-004: Multi-Tenancy Implementation
US-004.8: Tenant Monitoring & Analytics

Provides comprehensive tenant monitoring:
- Health dashboards
- Performance metrics
- Error tracking
- SLA monitoring
- Capacity planning
- Alerting
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


class HealthStatus(str, Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Types of alerts."""
    QUOTA_WARNING = "quota_warning"
    QUOTA_EXCEEDED = "quota_exceeded"
    ERROR_RATE_HIGH = "error_rate_high"
    LATENCY_HIGH = "latency_high"
    SLA_BREACH = "sla_breach"
    SECURITY_EVENT = "security_event"
    USAGE_SPIKE = "usage_spike"


@dataclass
class TenantHealthMetrics:
    """Health metrics for a tenant."""
    tenant_id: str
    status: HealthStatus
    api_health: HealthStatus
    database_health: HealthStatus
    cache_health: HealthStatus
    error_rate: float  # Percentage
    avg_latency_ms: float
    p99_latency_ms: float
    active_users: int
    requests_per_minute: int
    uptime_percent: float
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SLAMetrics:
    """SLA tracking metrics."""
    tenant_id: str
    period_start: datetime
    period_end: datetime
    uptime_target: float = 99.9
    uptime_actual: float = 100.0
    latency_target_ms: float = 200.0
    latency_actual_ms: float = 0.0
    error_rate_target: float = 0.1
    error_rate_actual: float = 0.0
    sla_met: bool = True
    violations: List[Dict] = field(default_factory=list)


@dataclass
class Alert:
    """An alert notification."""
    alert_id: str
    tenant_id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class TenantMonitor:
    """
    Monitors tenant health, performance, and SLA compliance.
    """

    def __init__(
        self,
        db_session_factory,
        redis_client: aioredis.Redis,
        alert_callback=None,
    ):
        self.db_factory = db_session_factory
        self.redis = redis_client
        self.alert_callback = alert_callback

    async def get_health(self, tenant_id: str) -> TenantHealthMetrics:
        """
        Get comprehensive health metrics for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            TenantHealthMetrics with current status
        """
        # Gather metrics from various sources
        api_metrics = await self._get_api_metrics(tenant_id)
        db_metrics = await self._get_database_metrics(tenant_id)
        cache_metrics = await self._get_cache_metrics(tenant_id)

        # Calculate overall health
        error_rate = api_metrics.get("error_rate", 0)
        avg_latency = api_metrics.get("avg_latency_ms", 0)
        p99_latency = api_metrics.get("p99_latency_ms", 0)

        # Determine status based on thresholds
        status = HealthStatus.HEALTHY

        if error_rate > 5 or avg_latency > 1000:
            status = HealthStatus.CRITICAL
        elif error_rate > 1 or avg_latency > 500:
            status = HealthStatus.UNHEALTHY
        elif error_rate > 0.5 or avg_latency > 200:
            status = HealthStatus.DEGRADED

        return TenantHealthMetrics(
            tenant_id=tenant_id,
            status=status,
            api_health=self._get_component_health(error_rate, avg_latency),
            database_health=db_metrics.get("health", HealthStatus.HEALTHY),
            cache_health=cache_metrics.get("health", HealthStatus.HEALTHY),
            error_rate=error_rate,
            avg_latency_ms=avg_latency,
            p99_latency_ms=p99_latency,
            active_users=api_metrics.get("active_users", 0),
            requests_per_minute=api_metrics.get("rpm", 0),
            uptime_percent=api_metrics.get("uptime", 100.0),
            last_error=api_metrics.get("last_error"),
            last_error_time=api_metrics.get("last_error_time"),
        )

    async def _get_api_metrics(self, tenant_id: str) -> Dict[str, Any]:
        """Get API metrics from Redis."""
        now = datetime.now(timezone.utc)
        hour_ago = now - timedelta(hours=1)

        # Get request counts
        total_key = f"metrics:{tenant_id}:requests:total"
        error_key = f"metrics:{tenant_id}:requests:errors"
        latency_key = f"metrics:{tenant_id}:latency"

        pipe = self.redis.pipeline()
        pipe.get(total_key)
        pipe.get(error_key)
        pipe.get(latency_key)

        results = await pipe.execute()

        total_requests = int(results[0] or 0)
        error_requests = int(results[1] or 0)
        avg_latency = float(results[2] or 0)

        error_rate = (error_requests / total_requests * 100) if total_requests > 0 else 0

        # Get active users
        active_users_key = f"metrics:{tenant_id}:active_users"
        active_users = await self.redis.scard(active_users_key)

        # Get last error
        last_error_key = f"metrics:{tenant_id}:last_error"
        last_error_data = await self.redis.hgetall(last_error_key)

        return {
            "total_requests": total_requests,
            "error_rate": error_rate,
            "avg_latency_ms": avg_latency,
            "p99_latency_ms": avg_latency * 1.5,  # Simplified estimation
            "active_users": active_users,
            "rpm": total_requests / 60 if total_requests > 0 else 0,
            "uptime": 99.9,  # Would calculate from actual downtime events
            "last_error": last_error_data.get(b"message", b"").decode() if last_error_data else None,
        }

    async def _get_database_metrics(self, tenant_id: str) -> Dict[str, Any]:
        """Get database metrics for tenant."""
        db = self.db_factory()
        try:
            # Check connection
            db.execute(text("SELECT 1"))

            # Get query stats (simplified)
            return {
                "health": HealthStatus.HEALTHY,
                "connections": 1,
                "slow_queries": 0,
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "health": HealthStatus.UNHEALTHY,
                "error": str(e),
            }
        finally:
            db.close()

    async def _get_cache_metrics(self, tenant_id: str) -> Dict[str, Any]:
        """Get cache metrics for tenant."""
        try:
            await self.redis.ping()
            return {"health": HealthStatus.HEALTHY}
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {"health": HealthStatus.UNHEALTHY, "error": str(e)}

    def _get_component_health(self, error_rate: float, latency: float) -> HealthStatus:
        """Determine component health from metrics."""
        if error_rate > 5 or latency > 1000:
            return HealthStatus.CRITICAL
        elif error_rate > 1 or latency > 500:
            return HealthStatus.UNHEALTHY
        elif error_rate > 0.5 or latency > 200:
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY

    async def check_sla(
        self,
        tenant_id: str,
        period_start: datetime,
        period_end: datetime,
    ) -> SLAMetrics:
        """
        Check SLA compliance for a period.

        Args:
            tenant_id: Tenant identifier
            period_start: Start of SLA period
            period_end: End of SLA period

        Returns:
            SLAMetrics with compliance status
        """
        db = self.db_factory()
        try:
            # Get aggregated metrics for period
            result = db.execute(
                text("""
                    SELECT
                        COALESCE(AVG(api_calls), 0) as avg_requests,
                        COALESCE(AVG(errors), 0) as avg_errors,
                        COUNT(*) as days_in_period
                    FROM tenant_usage_daily
                    WHERE tenant_id = :tenant_id
                      AND date >= :start_date
                      AND date <= :end_date
                """),
                {
                    "tenant_id": tenant_id,
                    "start_date": period_start.date(),
                    "end_date": period_end.date(),
                }
            ).fetchone()

            # Get SLA targets from tenant config
            tenant = db.execute(
                text("SELECT tier, settings FROM tenants WHERE id = :id"),
                {"id": tenant_id}
            ).fetchone()

            # Default targets by tier
            tier_sla = {
                "free": {"uptime": 99.0, "latency": 500, "error_rate": 1.0},
                "starter": {"uptime": 99.5, "latency": 300, "error_rate": 0.5},
                "professional": {"uptime": 99.9, "latency": 200, "error_rate": 0.1},
                "enterprise": {"uptime": 99.99, "latency": 100, "error_rate": 0.05},
            }

            tier = tenant.tier if tenant else "free"
            targets = tier_sla.get(tier, tier_sla["free"])

            # Calculate actuals
            avg_requests = result.avg_requests if result else 0
            avg_errors = result.avg_errors if result else 0
            error_rate_actual = (avg_errors / avg_requests * 100) if avg_requests > 0 else 0

            # Check violations
            violations = []
            sla_met = True

            if error_rate_actual > targets["error_rate"]:
                violations.append({
                    "metric": "error_rate",
                    "target": targets["error_rate"],
                    "actual": error_rate_actual,
                })
                sla_met = False

            # TODO: Calculate actual uptime and latency from detailed metrics

            return SLAMetrics(
                tenant_id=tenant_id,
                period_start=period_start,
                period_end=period_end,
                uptime_target=targets["uptime"],
                uptime_actual=99.9,  # Would calculate from actual data
                latency_target_ms=targets["latency"],
                latency_actual_ms=150,  # Would calculate from actual data
                error_rate_target=targets["error_rate"],
                error_rate_actual=error_rate_actual,
                sla_met=sla_met,
                violations=violations,
            )
        finally:
            db.close()

    async def record_metric(
        self,
        tenant_id: str,
        metric_name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
    ):
        """
        Record a metric for a tenant.

        Args:
            tenant_id: Tenant identifier
            metric_name: Name of the metric
            value: Metric value
            tags: Optional metric tags
        """
        now = datetime.now(timezone.utc)
        key = f"metrics:{tenant_id}:{metric_name}"

        # Store with timestamp for time-series analysis
        await self.redis.zadd(key, {f"{now.timestamp()}:{value}": now.timestamp()})

        # Keep only last 24 hours
        cutoff = (now - timedelta(hours=24)).timestamp()
        await self.redis.zremrangebyscore(key, 0, cutoff)

        # Update running average
        avg_key = f"{key}:avg"
        count_key = f"{key}:count"

        pipe = self.redis.pipeline()
        pipe.incrbyfloat(avg_key, value)
        pipe.incr(count_key)
        await pipe.execute()

    async def record_error(
        self,
        tenant_id: str,
        error_type: str,
        error_message: str,
        endpoint: Optional[str] = None,
    ):
        """Record an error occurrence."""
        now = datetime.now(timezone.utc)

        # Increment error counter
        error_key = f"metrics:{tenant_id}:requests:errors"
        await self.redis.incr(error_key)
        await self.redis.expire(error_key, 3600)

        # Store last error details
        last_error_key = f"metrics:{tenant_id}:last_error"
        await self.redis.hset(last_error_key, mapping={
            "type": error_type,
            "message": error_message,
            "endpoint": endpoint or "",
            "time": now.isoformat(),
        })
        await self.redis.expire(last_error_key, 86400)

        # Track error by type
        error_type_key = f"metrics:{tenant_id}:errors:{error_type}"
        await self.redis.incr(error_type_key)
        await self.redis.expire(error_type_key, 86400)

        # Check if error rate is high
        total_key = f"metrics:{tenant_id}:requests:total"
        total = int(await self.redis.get(total_key) or 0)
        errors = int(await self.redis.get(error_key) or 0)

        if total > 100 and errors / total > 0.05:  # 5% error rate
            await self._create_alert(
                tenant_id=tenant_id,
                alert_type=AlertType.ERROR_RATE_HIGH,
                severity=AlertSeverity.WARNING,
                title="High Error Rate Detected",
                message=f"Error rate is {errors/total*100:.1f}% (threshold: 5%)",
                metadata={"error_count": errors, "total_requests": total},
            )

    async def record_latency(
        self,
        tenant_id: str,
        latency_ms: float,
        endpoint: Optional[str] = None,
    ):
        """Record a request latency."""
        # Update average latency
        latency_key = f"metrics:{tenant_id}:latency"

        # Use exponential moving average
        current = float(await self.redis.get(latency_key) or latency_ms)
        alpha = 0.1  # Smoothing factor
        new_avg = alpha * latency_ms + (1 - alpha) * current
        await self.redis.set(latency_key, new_avg)
        await self.redis.expire(latency_key, 3600)

        # Check for high latency
        if latency_ms > 1000:  # 1 second
            await self._create_alert(
                tenant_id=tenant_id,
                alert_type=AlertType.LATENCY_HIGH,
                severity=AlertSeverity.WARNING,
                title="High Latency Detected",
                message=f"Request latency of {latency_ms:.0f}ms detected",
                metadata={"latency_ms": latency_ms, "endpoint": endpoint},
            )

    async def record_request(self, tenant_id: str, user_id: Optional[str] = None):
        """Record a request occurrence."""
        # Increment request counter
        total_key = f"metrics:{tenant_id}:requests:total"
        await self.redis.incr(total_key)
        await self.redis.expire(total_key, 3600)

        # Track active users
        if user_id:
            active_users_key = f"metrics:{tenant_id}:active_users"
            await self.redis.sadd(active_users_key, user_id)
            await self.redis.expire(active_users_key, 3600)

    async def _create_alert(
        self,
        tenant_id: str,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        message: str,
        metadata: Optional[Dict] = None,
    ):
        """Create and dispatch an alert."""
        from uuid import uuid4

        # Check if similar alert exists in cooldown
        cooldown_key = f"alert_cooldown:{tenant_id}:{alert_type.value}"
        if await self.redis.exists(cooldown_key):
            return  # Skip duplicate alert

        # Set cooldown (1 hour)
        await self.redis.setex(cooldown_key, 3600, "1")

        alert = Alert(
            alert_id=str(uuid4()),
            tenant_id=tenant_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            metadata=metadata or {},
        )

        # Store alert
        alert_key = f"alerts:{tenant_id}:{alert.alert_id}"
        import json
        await self.redis.hset(alert_key, mapping={
            "id": alert.alert_id,
            "type": alert_type.value,
            "severity": severity.value,
            "title": title,
            "message": message,
            "metadata": json.dumps(metadata or {}),
            "created_at": alert.created_at.isoformat(),
        })
        await self.redis.expire(alert_key, 86400 * 7)  # Keep for 7 days

        # Add to alert list
        await self.redis.lpush(f"alerts:{tenant_id}:list", alert.alert_id)
        await self.redis.ltrim(f"alerts:{tenant_id}:list", 0, 99)  # Keep last 100

        # Call alert callback if provided
        if self.alert_callback:
            await self.alert_callback(alert)

        logger.warning(f"Alert created for tenant {tenant_id}: {title}")

    async def get_alerts(
        self,
        tenant_id: str,
        limit: int = 50,
        include_resolved: bool = False,
    ) -> List[Alert]:
        """Get alerts for a tenant."""
        import json

        alert_ids = await self.redis.lrange(f"alerts:{tenant_id}:list", 0, limit - 1)

        alerts = []
        for alert_id in alert_ids:
            alert_key = f"alerts:{tenant_id}:{alert_id.decode()}"
            data = await self.redis.hgetall(alert_key)

            if data:
                alerts.append(Alert(
                    alert_id=data[b"id"].decode(),
                    tenant_id=tenant_id,
                    alert_type=AlertType(data[b"type"].decode()),
                    severity=AlertSeverity(data[b"severity"].decode()),
                    title=data[b"title"].decode(),
                    message=data[b"message"].decode(),
                    metadata=json.loads(data[b"metadata"].decode()),
                    created_at=datetime.fromisoformat(data[b"created_at"].decode()),
                ))

        return alerts

    async def get_dashboard_data(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data for a tenant.

        Returns all metrics needed for a monitoring dashboard.
        """
        health = await self.get_health(tenant_id)
        alerts = await self.get_alerts(tenant_id, limit=10)

        # Get usage trends
        db = self.db_factory()
        try:
            # Last 7 days of usage
            results = db.execute(
                text("""
                    SELECT date, api_calls, errors, active_users
                    FROM tenant_usage_daily
                    WHERE tenant_id = :tenant_id
                      AND date >= CURRENT_DATE - INTERVAL '7 days'
                    ORDER BY date
                """),
                {"tenant_id": tenant_id}
            ).fetchall()

            usage_trend = [
                {
                    "date": r.date.isoformat(),
                    "api_calls": r.api_calls,
                    "errors": r.errors,
                    "active_users": r.active_users,
                }
                for r in results
            ]
        finally:
            db.close()

        return {
            "tenant_id": tenant_id,
            "health": {
                "status": health.status.value,
                "api": health.api_health.value,
                "database": health.database_health.value,
                "cache": health.cache_health.value,
            },
            "metrics": {
                "error_rate": health.error_rate,
                "avg_latency_ms": health.avg_latency_ms,
                "p99_latency_ms": health.p99_latency_ms,
                "requests_per_minute": health.requests_per_minute,
                "active_users": health.active_users,
                "uptime_percent": health.uptime_percent,
            },
            "alerts": [
                {
                    "id": a.alert_id,
                    "type": a.alert_type.value,
                    "severity": a.severity.value,
                    "title": a.title,
                    "created_at": a.created_at.isoformat(),
                }
                for a in alerts
            ],
            "usage_trend": usage_trend,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
