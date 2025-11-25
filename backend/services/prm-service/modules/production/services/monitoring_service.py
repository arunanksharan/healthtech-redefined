"""
Monitoring Service

Service for managing metrics, dashboards, health checks, and SLO/SLI tracking.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    MetricDefinition, Dashboard, HealthCheck, SLODefinition, SLIRecord,
    MetricType, MetricCategory, HealthCheckType, HealthStatus
)
from ..schemas import (
    MetricDefinitionCreate, DashboardCreate, HealthCheckCreate,
    SLODefinitionCreate, SLIRecordCreate, MonitoringSummary
)


class MonitoringService:
    """Service for monitoring and observability."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Metric Definitions
    # =========================================================================

    async def create_metric(
        self,
        tenant_id: UUID,
        data: MetricDefinitionCreate
    ) -> MetricDefinition:
        """Create a new metric definition."""
        metric = MetricDefinition(
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            metric_type=data.metric_type,
            category=data.category,
            prometheus_query=data.prometheus_query,
            labels=data.labels or [],
            unit=data.unit,
            display_name=data.display_name,
            warning_threshold=data.warning_threshold,
            critical_threshold=data.critical_threshold,
            aggregation_method=data.aggregation_method,
            aggregation_interval=data.aggregation_interval,
            enabled=data.enabled
        )
        self.db.add(metric)
        await self.db.commit()
        await self.db.refresh(metric)
        return metric

    async def get_metric(
        self,
        tenant_id: UUID,
        metric_id: UUID
    ) -> Optional[MetricDefinition]:
        """Get metric by ID."""
        result = await self.db.execute(
            select(MetricDefinition).where(
                and_(
                    MetricDefinition.tenant_id == tenant_id,
                    MetricDefinition.id == metric_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_metric_by_name(
        self,
        tenant_id: UUID,
        name: str
    ) -> Optional[MetricDefinition]:
        """Get metric by name."""
        result = await self.db.execute(
            select(MetricDefinition).where(
                and_(
                    MetricDefinition.tenant_id == tenant_id,
                    MetricDefinition.name == name
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_metrics(
        self,
        tenant_id: UUID,
        category: Optional[MetricCategory] = None,
        enabled_only: bool = False
    ) -> List[MetricDefinition]:
        """List metric definitions."""
        query = select(MetricDefinition).where(
            MetricDefinition.tenant_id == tenant_id
        )
        if category:
            query = query.where(MetricDefinition.category == category)
        if enabled_only:
            query = query.where(MetricDefinition.enabled == True)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_metric_thresholds(
        self,
        tenant_id: UUID,
        metric_id: UUID,
        warning_threshold: Optional[float] = None,
        critical_threshold: Optional[float] = None
    ) -> Optional[MetricDefinition]:
        """Update metric thresholds."""
        metric = await self.get_metric(tenant_id, metric_id)
        if metric:
            if warning_threshold is not None:
                metric.warning_threshold = warning_threshold
            if critical_threshold is not None:
                metric.critical_threshold = critical_threshold
            metric.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(metric)
        return metric

    # =========================================================================
    # Dashboards
    # =========================================================================

    async def create_dashboard(
        self,
        tenant_id: UUID,
        data: DashboardCreate,
        owner_id: Optional[UUID] = None
    ) -> Dashboard:
        """Create a new dashboard."""
        dashboard = Dashboard(
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            dashboard_type=data.dashboard_type,
            grafana_uid=data.grafana_uid,
            grafana_url=data.grafana_url,
            grafana_json=data.grafana_json,
            panels=data.panels or [],
            is_public=data.is_public,
            allowed_roles=data.allowed_roles or [],
            auto_refresh_interval=data.auto_refresh_interval,
            time_range=data.time_range,
            owner_id=owner_id,
            folder=data.folder,
            tags=data.tags or []
        )
        self.db.add(dashboard)
        await self.db.commit()
        await self.db.refresh(dashboard)
        return dashboard

    async def get_dashboard(
        self,
        tenant_id: UUID,
        dashboard_id: UUID
    ) -> Optional[Dashboard]:
        """Get dashboard by ID."""
        result = await self.db.execute(
            select(Dashboard).where(
                and_(
                    Dashboard.tenant_id == tenant_id,
                    Dashboard.id == dashboard_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_dashboards(
        self,
        tenant_id: UUID,
        dashboard_type: Optional[str] = None,
        folder: Optional[str] = None
    ) -> List[Dashboard]:
        """List dashboards."""
        query = select(Dashboard).where(Dashboard.tenant_id == tenant_id)
        if dashboard_type:
            query = query.where(Dashboard.dashboard_type == dashboard_type)
        if folder:
            query = query.where(Dashboard.folder == folder)
        query = query.order_by(Dashboard.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def star_dashboard(
        self,
        tenant_id: UUID,
        dashboard_id: UUID,
        starred: bool = True
    ) -> Optional[Dashboard]:
        """Star or unstar a dashboard."""
        dashboard = await self.get_dashboard(tenant_id, dashboard_id)
        if dashboard:
            dashboard.starred = starred
            dashboard.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(dashboard)
        return dashboard

    # =========================================================================
    # Health Checks
    # =========================================================================

    async def create_health_check(
        self,
        tenant_id: UUID,
        data: HealthCheckCreate
    ) -> HealthCheck:
        """Create a new health check."""
        health_check = HealthCheck(
            tenant_id=tenant_id,
            service_name=data.service_name,
            check_type=data.check_type,
            endpoint=data.endpoint,
            method=data.method,
            expected_status_code=data.expected_status_code,
            expected_response=data.expected_response,
            interval_seconds=data.interval_seconds,
            timeout_seconds=data.timeout_seconds,
            success_threshold=data.success_threshold,
            failure_threshold=data.failure_threshold,
            dependencies=data.dependencies or [],
            enabled=data.enabled
        )
        self.db.add(health_check)
        await self.db.commit()
        await self.db.refresh(health_check)
        return health_check

    async def get_health_check(
        self,
        tenant_id: UUID,
        health_check_id: UUID
    ) -> Optional[HealthCheck]:
        """Get health check by ID."""
        result = await self.db.execute(
            select(HealthCheck).where(
                and_(
                    HealthCheck.tenant_id == tenant_id,
                    HealthCheck.id == health_check_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_health_checks(
        self,
        tenant_id: UUID,
        service_name: Optional[str] = None,
        check_type: Optional[HealthCheckType] = None,
        enabled_only: bool = False
    ) -> List[HealthCheck]:
        """List health checks."""
        query = select(HealthCheck).where(HealthCheck.tenant_id == tenant_id)
        if service_name:
            query = query.where(HealthCheck.service_name == service_name)
        if check_type:
            query = query.where(HealthCheck.check_type == check_type)
        if enabled_only:
            query = query.where(HealthCheck.enabled == True)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_health_check_status(
        self,
        tenant_id: UUID,
        health_check_id: UUID,
        status: HealthStatus,
        is_success: bool
    ) -> Optional[HealthCheck]:
        """Update health check status after a check."""
        health_check = await self.get_health_check(tenant_id, health_check_id)
        if health_check:
            health_check.current_status = status
            health_check.last_check_at = datetime.utcnow()

            if is_success:
                health_check.last_success_at = datetime.utcnow()
                health_check.consecutive_failures = 0
            else:
                health_check.last_failure_at = datetime.utcnow()
                health_check.consecutive_failures += 1

            health_check.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(health_check)
        return health_check

    async def get_service_health_status(
        self,
        tenant_id: UUID
    ) -> Dict[str, HealthStatus]:
        """Get health status for all services."""
        health_checks = await self.list_health_checks(tenant_id, enabled_only=True)
        service_status = {}
        for check in health_checks:
            if check.service_name not in service_status:
                service_status[check.service_name] = check.current_status
            elif check.current_status == HealthStatus.UNHEALTHY:
                service_status[check.service_name] = HealthStatus.UNHEALTHY
            elif check.current_status == HealthStatus.DEGRADED and \
                    service_status[check.service_name] == HealthStatus.HEALTHY:
                service_status[check.service_name] = HealthStatus.DEGRADED
        return service_status

    # =========================================================================
    # SLO/SLI Management
    # =========================================================================

    async def create_slo(
        self,
        tenant_id: UUID,
        data: SLODefinitionCreate
    ) -> SLODefinition:
        """Create a new SLO definition."""
        # Calculate error budget in minutes
        window_minutes = data.window_days * 24 * 60
        error_budget_minutes = window_minutes * (1 - data.target_percentage / 100)

        slo = SLODefinition(
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            service_name=data.service_name,
            target_percentage=data.target_percentage,
            window_days=data.window_days,
            error_budget_minutes=error_budget_minutes,
            error_budget_remaining=error_budget_minutes,
            sli_query=data.sli_query,
            sli_type=data.sli_type,
            burn_rate_alert_enabled=data.burn_rate_alert_enabled,
            fast_burn_threshold=data.fast_burn_threshold,
            slow_burn_threshold=data.slow_burn_threshold,
            enabled=data.enabled
        )
        self.db.add(slo)
        await self.db.commit()
        await self.db.refresh(slo)
        return slo

    async def get_slo(
        self,
        tenant_id: UUID,
        slo_id: UUID
    ) -> Optional[SLODefinition]:
        """Get SLO by ID."""
        result = await self.db.execute(
            select(SLODefinition).where(
                and_(
                    SLODefinition.tenant_id == tenant_id,
                    SLODefinition.id == slo_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_slos(
        self,
        tenant_id: UUID,
        service_name: Optional[str] = None,
        enabled_only: bool = False
    ) -> List[SLODefinition]:
        """List SLO definitions."""
        query = select(SLODefinition).where(SLODefinition.tenant_id == tenant_id)
        if service_name:
            query = query.where(SLODefinition.service_name == service_name)
        if enabled_only:
            query = query.where(SLODefinition.enabled == True)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def record_sli(
        self,
        tenant_id: UUID,
        data: SLIRecordCreate
    ) -> SLIRecord:
        """Record an SLI measurement."""
        sli_value = (data.good_events / data.total_events * 100) if data.total_events > 0 else 0

        record = SLIRecord(
            tenant_id=tenant_id,
            slo_id=data.slo_id,
            timestamp=data.timestamp,
            good_events=data.good_events,
            total_events=data.total_events,
            sli_value=sli_value,
            window_start=data.window_start,
            window_end=data.window_end
        )
        self.db.add(record)

        # Update SLO with current value
        slo = await self.get_slo(tenant_id, data.slo_id)
        if slo:
            slo.current_sli_value = sli_value
            slo.slo_met = sli_value >= slo.target_percentage
            slo.last_calculated_at = datetime.utcnow()

            # Update error budget consumed
            if slo.error_budget_minutes and slo.error_budget_minutes > 0:
                downtime_minutes = ((100 - sli_value) / 100) * (slo.window_days * 24 * 60)
                slo.error_budget_remaining = max(0, slo.error_budget_minutes - downtime_minutes)
                slo.error_budget_consumed_percent = (
                    (slo.error_budget_minutes - slo.error_budget_remaining) / slo.error_budget_minutes * 100
                )

        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def get_sli_history(
        self,
        tenant_id: UUID,
        slo_id: UUID,
        days: int = 30
    ) -> List[SLIRecord]:
        """Get SLI history for an SLO."""
        since = datetime.utcnow() - timedelta(days=days)
        result = await self.db.execute(
            select(SLIRecord).where(
                and_(
                    SLIRecord.tenant_id == tenant_id,
                    SLIRecord.slo_id == slo_id,
                    SLIRecord.timestamp >= since
                )
            ).order_by(SLIRecord.timestamp)
        )
        return list(result.scalars().all())

    async def calculate_error_budget_burn_rate(
        self,
        tenant_id: UUID,
        slo_id: UUID,
        window_hours: int = 1
    ) -> float:
        """Calculate current error budget burn rate."""
        since = datetime.utcnow() - timedelta(hours=window_hours)
        result = await self.db.execute(
            select(SLIRecord).where(
                and_(
                    SLIRecord.tenant_id == tenant_id,
                    SLIRecord.slo_id == slo_id,
                    SLIRecord.timestamp >= since
                )
            )
        )
        records = list(result.scalars().all())

        if not records:
            return 0.0

        total_good = sum(r.good_events for r in records)
        total_events = sum(r.total_events for r in records)

        if total_events == 0:
            return 0.0

        slo = await self.get_slo(tenant_id, slo_id)
        if not slo:
            return 0.0

        actual_error_rate = 1 - (total_good / total_events)
        allowed_error_rate = (100 - slo.target_percentage) / 100

        if allowed_error_rate == 0:
            return float('inf') if actual_error_rate > 0 else 0.0

        return actual_error_rate / allowed_error_rate

    # =========================================================================
    # Summary
    # =========================================================================

    async def get_monitoring_summary(
        self,
        tenant_id: UUID
    ) -> MonitoringSummary:
        """Get monitoring summary."""
        # Metrics count
        metrics_result = await self.db.execute(
            select(func.count(MetricDefinition.id)).where(
                and_(
                    MetricDefinition.tenant_id == tenant_id,
                    MetricDefinition.enabled == True
                )
            )
        )
        total_metrics = metrics_result.scalar() or 0

        # Dashboards count
        dashboards_result = await self.db.execute(
            select(func.count(Dashboard.id)).where(Dashboard.tenant_id == tenant_id)
        )
        total_dashboards = dashboards_result.scalar() or 0

        # Health checks
        health_checks_result = await self.db.execute(
            select(func.count(HealthCheck.id)).where(
                and_(
                    HealthCheck.tenant_id == tenant_id,
                    HealthCheck.enabled == True
                )
            )
        )
        total_health_checks = health_checks_result.scalar() or 0

        # Health status counts
        health_status = await self.get_service_health_status(tenant_id)
        healthy_services = sum(1 for s in health_status.values() if s == HealthStatus.HEALTHY)
        unhealthy_services = sum(1 for s in health_status.values() if s == HealthStatus.UNHEALTHY)
        degraded_services = sum(1 for s in health_status.values() if s == HealthStatus.DEGRADED)

        # SLOs
        slos_result = await self.db.execute(
            select(func.count(SLODefinition.id)).where(
                and_(
                    SLODefinition.tenant_id == tenant_id,
                    SLODefinition.enabled == True
                )
            )
        )
        total_slos = slos_result.scalar() or 0

        slos_met_result = await self.db.execute(
            select(func.count(SLODefinition.id)).where(
                and_(
                    SLODefinition.tenant_id == tenant_id,
                    SLODefinition.enabled == True,
                    SLODefinition.slo_met == True
                )
            )
        )
        slos_met = slos_met_result.scalar() or 0

        # SLOs at risk (error budget > 80% consumed)
        slos_at_risk_result = await self.db.execute(
            select(func.count(SLODefinition.id)).where(
                and_(
                    SLODefinition.tenant_id == tenant_id,
                    SLODefinition.enabled == True,
                    SLODefinition.error_budget_consumed_percent > 80
                )
            )
        )
        slos_at_risk = slos_at_risk_result.scalar() or 0

        return MonitoringSummary(
            total_metrics=total_metrics,
            total_dashboards=total_dashboards,
            total_health_checks=total_health_checks,
            healthy_services=healthy_services,
            unhealthy_services=unhealthy_services,
            degraded_services=degraded_services,
            total_slos=total_slos,
            slos_met=slos_met,
            slos_at_risk=slos_at_risk
        )
