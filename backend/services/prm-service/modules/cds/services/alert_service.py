"""
Alert Management Service

Provides alert configuration, analytics, optimization,
and override tracking for CDS alerts.

EPIC-020: Clinical Decision Support
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from modules.cds.models import (
    CDSAlert,
    AlertOverride,
    AlertConfiguration,
    AlertAnalytics,
    InteractionType,
    InteractionSeverity,
    AlertTier,
    AlertStatus,
    OverrideReason,
)
from modules.cds.schemas import (
    CDSAlertCreate,
    CDSAlertResponse,
    AlertAcknowledge,
    AlertOverrideCreate,
    AlertOverrideResponse,
    AlertConfigurationCreate,
    AlertConfigurationUpdate,
    AlertAnalyticsResponse,
)


class AlertManagementService:
    """Service for CDS alert management and optimization."""

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    # Alert CRUD Methods

    async def create_alert(
        self,
        data: CDSAlertCreate,
    ) -> CDSAlert:
        """Create a new CDS alert."""
        alert = CDSAlert(
            tenant_id=self.tenant_id,
            patient_id=data.patient_id,
            encounter_id=data.encounter_id,
            provider_id=data.provider_id,
            order_id=data.order_id,
            alert_type=data.alert_type,
            severity=data.severity,
            tier=data.tier,
            title=data.title,
            message=data.message,
            details=data.details,
            recommendation=data.recommendation,
            drug1_rxnorm=data.drug1_rxnorm,
            drug1_name=data.drug1_name,
            drug2_rxnorm=data.drug2_rxnorm,
            drug2_name=data.drug2_name,
            allergy_code=data.allergy_code,
            condition_code=data.condition_code,
            rule_id=data.rule_id,
            expires_at=data.expires_at,
        )
        self.db.add(alert)
        await self.db.flush()
        return alert

    async def get_alert(self, alert_id: UUID) -> Optional[CDSAlert]:
        """Get an alert by ID."""
        query = select(CDSAlert).where(
            and_(
                CDSAlert.id == alert_id,
                CDSAlert.tenant_id == self.tenant_id,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_alerts(
        self,
        patient_id: Optional[UUID] = None,
        provider_id: Optional[UUID] = None,
        encounter_id: Optional[UUID] = None,
        status: Optional[AlertStatus] = None,
        severity: Optional[InteractionSeverity] = None,
        alert_type: Optional[InteractionType] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[CDSAlert]:
        """List alerts with optional filters."""
        query = select(CDSAlert).where(CDSAlert.tenant_id == self.tenant_id)

        if patient_id:
            query = query.where(CDSAlert.patient_id == patient_id)
        if provider_id:
            query = query.where(CDSAlert.provider_id == provider_id)
        if encounter_id:
            query = query.where(CDSAlert.encounter_id == encounter_id)
        if status:
            query = query.where(CDSAlert.status == status)
        if severity:
            query = query.where(CDSAlert.severity == severity)
        if alert_type:
            query = query.where(CDSAlert.alert_type == alert_type)

        query = query.order_by(CDSAlert.triggered_at.desc())
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_active_alerts(
        self,
        patient_id: UUID,
        encounter_id: Optional[UUID] = None,
    ) -> List[CDSAlert]:
        """Get active alerts for a patient."""
        query = select(CDSAlert).where(
            and_(
                CDSAlert.tenant_id == self.tenant_id,
                CDSAlert.patient_id == patient_id,
                CDSAlert.status == AlertStatus.ACTIVE,
            )
        )

        if encounter_id:
            query = query.where(CDSAlert.encounter_id == encounter_id)

        # Exclude expired alerts
        query = query.where(
            or_(
                CDSAlert.expires_at.is_(None),
                CDSAlert.expires_at > datetime.utcnow(),
            )
        )

        query = query.order_by(CDSAlert.severity, CDSAlert.triggered_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # Alert Actions

    async def acknowledge_alert(
        self,
        alert_id: UUID,
        data: AlertAcknowledge,
    ) -> Optional[CDSAlert]:
        """Acknowledge an alert."""
        alert = await self.get_alert(alert_id)
        if not alert:
            return None

        # Calculate response time
        response_time_ms = None
        if alert.displayed_at:
            response_time_ms = int(
                (datetime.utcnow() - alert.displayed_at).total_seconds() * 1000
            )

        alert.status = AlertStatus.ACKNOWLEDGED
        alert.responded_at = datetime.utcnow()
        alert.response_time_ms = response_time_ms
        alert.was_helpful = data.was_helpful

        await self.db.flush()
        return alert

    async def override_alert(
        self,
        alert_id: UUID,
        data: AlertOverrideCreate,
    ) -> Optional[AlertOverride]:
        """Override an alert with documentation."""
        alert = await self.get_alert(alert_id)
        if not alert:
            return None

        # Calculate response time
        response_time_ms = None
        if alert.displayed_at:
            response_time_ms = int(
                (datetime.utcnow() - alert.displayed_at).total_seconds() * 1000
            )

        # Update alert status
        alert.status = AlertStatus.OVERRIDDEN
        alert.responded_at = datetime.utcnow()
        alert.response_time_ms = response_time_ms

        # Create override record
        override = AlertOverride(
            tenant_id=self.tenant_id,
            alert_id=alert_id,
            provider_id=data.provider_id,
            reason=data.reason,
            reason_other=data.reason_other,
            clinical_justification=data.clinical_justification,
            will_monitor=data.will_monitor,
            monitoring_plan=data.monitoring_plan,
            supervising_provider_id=data.supervising_provider_id,
            was_emergency=data.was_emergency,
            patient_consented=data.patient_consented,
        )
        self.db.add(override)

        await self.db.flush()
        return override

    async def dismiss_alert(
        self,
        alert_id: UUID,
        dismissed_by: UUID,
        reason: Optional[str] = None,
    ) -> Optional[CDSAlert]:
        """Dismiss an alert."""
        alert = await self.get_alert(alert_id)
        if not alert:
            return None

        # Only allow dismissing soft stops and informational
        if alert.tier == AlertTier.HARD_STOP:
            raise ValueError("Hard stop alerts cannot be dismissed without override")

        alert.status = AlertStatus.DISMISSED
        alert.responded_at = datetime.utcnow()

        if alert.displayed_at:
            alert.response_time_ms = int(
                (datetime.utcnow() - alert.displayed_at).total_seconds() * 1000
            )

        await self.db.flush()
        return alert

    async def mark_alert_displayed(
        self,
        alert_id: UUID,
    ) -> Optional[CDSAlert]:
        """Mark alert as displayed to track response time."""
        alert = await self.get_alert(alert_id)
        if alert and not alert.displayed_at:
            alert.displayed_at = datetime.utcnow()
            await self.db.flush()
        return alert

    # Alert Configuration

    async def create_configuration(
        self,
        data: AlertConfigurationCreate,
        configured_by: UUID,
    ) -> AlertConfiguration:
        """Create alert configuration."""
        config = AlertConfiguration(
            tenant_id=self.tenant_id,
            alert_type=data.alert_type,
            severity=data.severity,
            drug_class=data.drug_class,
            tier=data.tier,
            is_enabled=data.is_enabled,
            is_suppressible=data.is_suppressible,
            requires_override_reason=data.requires_override_reason,
            min_severity=data.min_severity,
            exclude_conditions=data.exclude_conditions,
            provider_roles=data.provider_roles,
            care_settings=data.care_settings,
            notes=data.notes,
            configured_by=configured_by,
        )
        self.db.add(config)
        await self.db.flush()
        return config

    async def get_configuration(
        self,
        alert_type: Optional[InteractionType] = None,
        severity: Optional[InteractionSeverity] = None,
        drug_class: Optional[str] = None,
    ) -> Optional[AlertConfiguration]:
        """Get alert configuration for specific criteria."""
        query = select(AlertConfiguration).where(
            AlertConfiguration.tenant_id == self.tenant_id
        )

        if alert_type:
            query = query.where(
                or_(
                    AlertConfiguration.alert_type == alert_type,
                    AlertConfiguration.alert_type.is_(None),
                )
            )

        if severity:
            query = query.where(
                or_(
                    AlertConfiguration.severity == severity,
                    AlertConfiguration.severity.is_(None),
                )
            )

        if drug_class:
            query = query.where(
                or_(
                    AlertConfiguration.drug_class == drug_class,
                    AlertConfiguration.drug_class.is_(None),
                )
            )

        # Get most specific configuration
        query = query.order_by(
            AlertConfiguration.alert_type.desc().nullslast(),
            AlertConfiguration.severity.desc().nullslast(),
            AlertConfiguration.drug_class.desc().nullslast(),
        )

        result = await self.db.execute(query)
        return result.scalars().first()

    async def list_configurations(self) -> List[AlertConfiguration]:
        """List all alert configurations."""
        query = select(AlertConfiguration).where(
            AlertConfiguration.tenant_id == self.tenant_id
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_configuration(
        self,
        config_id: UUID,
        data: AlertConfigurationUpdate,
    ) -> Optional[AlertConfiguration]:
        """Update alert configuration."""
        query = select(AlertConfiguration).where(
            and_(
                AlertConfiguration.id == config_id,
                AlertConfiguration.tenant_id == self.tenant_id,
            )
        )
        result = await self.db.execute(query)
        config = result.scalar_one_or_none()

        if config:
            update_data = data.dict(exclude_unset=True)
            for key, value in update_data.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            await self.db.flush()

        return config

    # Alert Analytics

    async def get_analytics(
        self,
        start_date: date,
        end_date: date,
        alert_type: Optional[InteractionType] = None,
        severity: Optional[InteractionSeverity] = None,
        provider_id: Optional[UUID] = None,
    ) -> List[AlertAnalyticsResponse]:
        """Get alert analytics for a period."""
        query = select(AlertAnalytics).where(
            and_(
                AlertAnalytics.tenant_id == self.tenant_id,
                AlertAnalytics.period_date >= start_date,
                AlertAnalytics.period_date <= end_date,
            )
        )

        if alert_type:
            query = query.where(AlertAnalytics.alert_type == alert_type)
        if severity:
            query = query.where(AlertAnalytics.severity == severity)
        if provider_id:
            query = query.where(AlertAnalytics.provider_id == provider_id)

        query = query.order_by(AlertAnalytics.period_date)
        result = await self.db.execute(query)
        analytics = result.scalars().all()

        return [AlertAnalyticsResponse.from_orm(a) for a in analytics]

    async def calculate_analytics(
        self,
        for_date: date,
        period_type: str = "daily",
    ) -> List[AlertAnalytics]:
        """Calculate and store analytics for a date."""
        # Get alerts for the period
        if period_type == "daily":
            start_dt = datetime.combine(for_date, datetime.min.time())
            end_dt = datetime.combine(for_date, datetime.max.time())
        elif period_type == "weekly":
            start_dt = datetime.combine(for_date - timedelta(days=for_date.weekday()), datetime.min.time())
            end_dt = datetime.combine(start_dt.date() + timedelta(days=6), datetime.max.time())
        else:  # monthly
            start_dt = datetime.combine(for_date.replace(day=1), datetime.min.time())
            if for_date.month == 12:
                end_dt = datetime.combine(date(for_date.year + 1, 1, 1) - timedelta(days=1), datetime.max.time())
            else:
                end_dt = datetime.combine(date(for_date.year, for_date.month + 1, 1) - timedelta(days=1), datetime.max.time())

        # Query alerts
        query = select(CDSAlert).where(
            and_(
                CDSAlert.tenant_id == self.tenant_id,
                CDSAlert.triggered_at >= start_dt,
                CDSAlert.triggered_at <= end_dt,
            )
        )
        result = await self.db.execute(query)
        alerts = list(result.scalars().all())

        # Group by alert_type and severity
        groups: Dict[tuple, List[CDSAlert]] = {}
        for alert in alerts:
            key = (alert.alert_type, alert.severity)
            if key not in groups:
                groups[key] = []
            groups[key].append(alert)

        # Calculate analytics for each group
        analytics_records = []
        for (alert_type, severity), group_alerts in groups.items():
            total = len(group_alerts)
            acknowledged = sum(1 for a in group_alerts if a.status == AlertStatus.ACKNOWLEDGED)
            overridden = sum(1 for a in group_alerts if a.status == AlertStatus.OVERRIDDEN)
            dismissed = sum(1 for a in group_alerts if a.status == AlertStatus.DISMISSED)

            response_times = [a.response_time_ms for a in group_alerts if a.response_time_ms]
            avg_response_time = int(sum(response_times) / len(response_times)) if response_times else None

            override_rate = (overridden / total * 100) if total > 0 else None

            # Get override reasons distribution
            override_reasons = {}
            for alert in group_alerts:
                if alert.status == AlertStatus.OVERRIDDEN and alert.overrides:
                    for override in alert.overrides:
                        reason = override.reason.value
                        override_reasons[reason] = override_reasons.get(reason, 0) + 1

            # Create or update analytics record
            analytics = AlertAnalytics(
                tenant_id=self.tenant_id,
                period_date=for_date,
                period_type=period_type,
                alert_type=alert_type,
                severity=severity,
                total_alerts=total,
                acknowledged_count=acknowledged,
                overridden_count=overridden,
                dismissed_count=dismissed,
                avg_response_time_ms=avg_response_time,
                override_rate=override_rate,
                override_reasons=override_reasons,
            )
            self.db.add(analytics)
            analytics_records.append(analytics)

        await self.db.flush()
        return analytics_records

    async def get_override_patterns(
        self,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """Analyze override patterns for alert optimization."""
        # Get overrides in period
        query = select(AlertOverride).where(
            and_(
                AlertOverride.tenant_id == self.tenant_id,
                AlertOverride.override_at >= datetime.combine(start_date, datetime.min.time()),
                AlertOverride.override_at <= datetime.combine(end_date, datetime.max.time()),
            )
        )
        result = await self.db.execute(query)
        overrides = list(result.scalars().all())

        # Analyze by reason
        reason_counts = {}
        for override in overrides:
            reason = override.reason.value
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

        # Get high-override alerts
        query = select(
            CDSAlert.alert_type,
            CDSAlert.drug1_rxnorm,
            CDSAlert.drug2_rxnorm,
            func.count(CDSAlert.id).label("total"),
            func.sum(func.cast(CDSAlert.status == AlertStatus.OVERRIDDEN, Integer)).label("overridden"),
        ).where(
            and_(
                CDSAlert.tenant_id == self.tenant_id,
                CDSAlert.triggered_at >= datetime.combine(start_date, datetime.min.time()),
                CDSAlert.triggered_at <= datetime.combine(end_date, datetime.max.time()),
            )
        ).group_by(
            CDSAlert.alert_type,
            CDSAlert.drug1_rxnorm,
            CDSAlert.drug2_rxnorm,
        ).having(
            func.count(CDSAlert.id) >= 5
        )

        result = await self.db.execute(query)
        high_override_alerts = []
        for row in result:
            override_rate = (row.overridden / row.total * 100) if row.total > 0 else 0
            if override_rate >= 80:  # 80%+ override rate
                high_override_alerts.append({
                    "alert_type": row.alert_type.value if row.alert_type else None,
                    "drug1": row.drug1_rxnorm,
                    "drug2": row.drug2_rxnorm,
                    "total_alerts": row.total,
                    "override_rate": round(override_rate, 2),
                })

        return {
            "total_overrides": len(overrides),
            "reason_distribution": reason_counts,
            "high_override_alerts": high_override_alerts,
            "recommendations": self._generate_optimization_recommendations(
                reason_counts, high_override_alerts
            ),
        }

    def _generate_optimization_recommendations(
        self,
        reason_counts: Dict[str, int],
        high_override_alerts: List[Dict[str, Any]],
    ) -> List[str]:
        """Generate recommendations for alert optimization."""
        recommendations = []

        # Check for common override reasons
        total_overrides = sum(reason_counts.values())
        if total_overrides > 0:
            for reason, count in reason_counts.items():
                percentage = count / total_overrides * 100
                if percentage >= 30:
                    if reason == "patient_tolerated_previously":
                        recommendations.append(
                            "Consider implementing 'previously tolerated' auto-suppression"
                        )
                    elif reason == "benefit_outweighs_risk":
                        recommendations.append(
                            "Review alert severity levels - many may be over-classified"
                        )
                    elif reason == "clinical_judgment":
                        recommendations.append(
                            "Consider making some alerts informational instead of hard stops"
                        )

        # Check for high-override alerts
        if high_override_alerts:
            recommendations.append(
                f"Review {len(high_override_alerts)} alert rules with >80% override rate"
            )

        return recommendations

    async def get_alert_effectiveness_report(
        self,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """Generate alert effectiveness report."""
        # Get all alerts in period
        query = select(CDSAlert).where(
            and_(
                CDSAlert.tenant_id == self.tenant_id,
                CDSAlert.triggered_at >= datetime.combine(start_date, datetime.min.time()),
                CDSAlert.triggered_at <= datetime.combine(end_date, datetime.max.time()),
            )
        )
        result = await self.db.execute(query)
        alerts = list(result.scalars().all())

        total_alerts = len(alerts)
        by_status = {}
        by_severity = {}
        by_type = {}

        for alert in alerts:
            by_status[alert.status.value] = by_status.get(alert.status.value, 0) + 1
            by_severity[alert.severity.value] = by_severity.get(alert.severity.value, 0) + 1
            by_type[alert.alert_type.value] = by_type.get(alert.alert_type.value, 0) + 1

        # Calculate overall override rate
        overridden = by_status.get("overridden", 0)
        responded = total_alerts - by_status.get("active", 0) - by_status.get("expired", 0)
        override_rate = (overridden / responded * 100) if responded > 0 else 0

        # Average response time
        response_times = [a.response_time_ms for a in alerts if a.response_time_ms]
        avg_response_time = int(sum(response_times) / len(response_times)) if response_times else 0

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "total_alerts": total_alerts,
            "by_status": by_status,
            "by_severity": by_severity,
            "by_type": by_type,
            "override_rate": round(override_rate, 2),
            "avg_response_time_ms": avg_response_time,
            "alerts_per_day": round(total_alerts / max((end_date - start_date).days, 1), 2),
        }
