"""
Alert Service for RPM

Handles alert rules, evaluation, and notifications.

EPIC-019: Remote Patient Monitoring
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
import logging

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import (
    AlertRule, PatientAlertRule, RPMAlert, AlertNotification,
    DeviceReading, AlertSeverity, AlertStatus, AlertType,
    ReadingType, OutreachChannel
)
from ..schemas import (
    AlertRuleCreate, AlertRuleUpdate, AlertRuleResponse,
    PatientAlertRuleCreate, PatientAlertRuleUpdate,
    AlertResponse, AlertAcknowledge, AlertResolve, AlertEscalate,
    AlertFilters
)

logger = logging.getLogger(__name__)


class AlertService:
    """Service for managing RPM alerts."""

    async def create_alert_rule(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        created_by: UUID,
        rule_data: AlertRuleCreate
    ) -> AlertRule:
        """Create a new alert rule."""
        rule = AlertRule(
            tenant_id=tenant_id,
            name=rule_data.name,
            description=rule_data.description,
            reading_type=rule_data.reading_type,
            is_global=rule_data.is_global,
            threshold_low=rule_data.threshold_low,
            threshold_high=rule_data.threshold_high,
            threshold_critical_low=rule_data.threshold_critical_low,
            threshold_critical_high=rule_data.threshold_critical_high,
            trend_direction=rule_data.trend_direction,
            trend_threshold_percent=rule_data.trend_threshold_percent,
            trend_window_hours=rule_data.trend_window_hours,
            severity=rule_data.severity,
            alert_type=rule_data.alert_type,
            cooldown_minutes=rule_data.cooldown_minutes,
            notify_provider=rule_data.notify_provider,
            notify_patient=rule_data.notify_patient,
            notify_care_team=rule_data.notify_care_team,
            escalation_minutes=rule_data.escalation_minutes,
            conditions=rule_data.conditions or {},
            is_active=True,
            created_by=created_by
        )

        db.add(rule)
        await db.commit()
        await db.refresh(rule)

        logger.info(f"Created alert rule {rule.id}: {rule.name}")
        return rule

    async def get_alert_rule(
        self,
        db: AsyncSession,
        rule_id: UUID,
        tenant_id: UUID
    ) -> Optional[AlertRule]:
        """Get alert rule by ID."""
        result = await db.execute(
            select(AlertRule).where(
                and_(
                    AlertRule.id == rule_id,
                    AlertRule.tenant_id == tenant_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_alert_rules(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        reading_type: Optional[ReadingType] = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[AlertRule], int]:
        """List alert rules."""
        query = select(AlertRule).where(AlertRule.tenant_id == tenant_id)

        if reading_type:
            query = query.where(
                or_(
                    AlertRule.reading_type == reading_type,
                    AlertRule.reading_type.is_(None)  # Global rules
                )
            )
        if active_only:
            query = query.where(AlertRule.is_active == True)

        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()

        query = query.offset(skip).limit(limit).order_by(AlertRule.created_at.desc())
        result = await db.execute(query)
        rules = result.scalars().all()

        return list(rules), total

    async def update_alert_rule(
        self,
        db: AsyncSession,
        rule_id: UUID,
        tenant_id: UUID,
        update_data: AlertRuleUpdate
    ) -> Optional[AlertRule]:
        """Update alert rule."""
        rule = await self.get_alert_rule(db, rule_id, tenant_id)
        if not rule:
            return None

        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(rule, field, value)

        rule.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(rule)
        return rule

    async def delete_alert_rule(
        self,
        db: AsyncSession,
        rule_id: UUID,
        tenant_id: UUID
    ) -> bool:
        """Delete (deactivate) alert rule."""
        rule = await self.get_alert_rule(db, rule_id, tenant_id)
        if not rule:
            return False

        rule.is_active = False
        rule.updated_at = datetime.utcnow()
        await db.commit()
        return True

    # =========================================================================
    # Patient-specific rules
    # =========================================================================

    async def create_patient_rule(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        rule_data: PatientAlertRuleCreate
    ) -> PatientAlertRule:
        """Create patient-specific alert rule override."""
        # Verify base rule exists
        base_rule = await self.get_alert_rule(db, rule_data.rule_id, tenant_id)
        if not base_rule:
            raise ValueError("Base alert rule not found")

        patient_rule = PatientAlertRule(
            tenant_id=tenant_id,
            rule_id=rule_data.rule_id,
            patient_id=rule_data.patient_id,
            enrollment_id=rule_data.enrollment_id,
            threshold_low=rule_data.threshold_low,
            threshold_high=rule_data.threshold_high,
            threshold_critical_low=rule_data.threshold_critical_low,
            threshold_critical_high=rule_data.threshold_critical_high,
            notes=rule_data.notes,
            is_active=True
        )

        db.add(patient_rule)
        await db.commit()
        await db.refresh(patient_rule)
        return patient_rule

    async def get_patient_rules(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        patient_id: UUID
    ) -> List[PatientAlertRule]:
        """Get all patient-specific rules."""
        result = await db.execute(
            select(PatientAlertRule)
            .options(selectinload(PatientAlertRule.rule))
            .where(
                and_(
                    PatientAlertRule.tenant_id == tenant_id,
                    PatientAlertRule.patient_id == patient_id,
                    PatientAlertRule.is_active == True
                )
            )
        )
        return list(result.scalars().all())

    async def get_effective_thresholds(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        patient_id: UUID,
        rule_id: UUID
    ) -> Dict[str, Optional[float]]:
        """Get effective thresholds (base rule + patient overrides)."""
        base_rule = await self.get_alert_rule(db, rule_id, tenant_id)
        if not base_rule:
            return {}

        # Check for patient override
        result = await db.execute(
            select(PatientAlertRule).where(
                and_(
                    PatientAlertRule.rule_id == rule_id,
                    PatientAlertRule.patient_id == patient_id,
                    PatientAlertRule.is_active == True
                )
            )
        )
        patient_rule = result.scalar_one_or_none()

        return {
            "threshold_low": (
                patient_rule.threshold_low if patient_rule and patient_rule.threshold_low
                else base_rule.threshold_low
            ),
            "threshold_high": (
                patient_rule.threshold_high if patient_rule and patient_rule.threshold_high
                else base_rule.threshold_high
            ),
            "threshold_critical_low": (
                patient_rule.threshold_critical_low if patient_rule and patient_rule.threshold_critical_low
                else base_rule.threshold_critical_low
            ),
            "threshold_critical_high": (
                patient_rule.threshold_critical_high if patient_rule and patient_rule.threshold_critical_high
                else base_rule.threshold_critical_high
            ),
        }

    # =========================================================================
    # Alert evaluation
    # =========================================================================

    async def evaluate_reading(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        reading: DeviceReading
    ) -> List[RPMAlert]:
        """Evaluate a reading against all applicable rules."""
        if not reading.is_valid:
            return []

        # Get applicable rules
        rules_result = await db.execute(
            select(AlertRule).where(
                and_(
                    AlertRule.tenant_id == tenant_id,
                    AlertRule.is_active == True,
                    or_(
                        AlertRule.reading_type == reading.reading_type,
                        AlertRule.reading_type.is_(None)
                    )
                )
            )
        )
        rules = rules_result.scalars().all()

        alerts = []
        for rule in rules:
            alert = await self._evaluate_rule(db, tenant_id, reading, rule)
            if alert:
                alerts.append(alert)

        return alerts

    async def _evaluate_rule(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        reading: DeviceReading,
        rule: AlertRule
    ) -> Optional[RPMAlert]:
        """Evaluate a single rule against a reading."""
        # Check cooldown
        if not await self._check_cooldown(db, tenant_id, reading.patient_id, rule.id):
            return None

        # Get effective thresholds
        thresholds = await self.get_effective_thresholds(
            db, tenant_id, reading.patient_id, rule.id
        )

        # Check if patient rule is muted
        result = await db.execute(
            select(PatientAlertRule).where(
                and_(
                    PatientAlertRule.rule_id == rule.id,
                    PatientAlertRule.patient_id == reading.patient_id,
                    PatientAlertRule.is_muted == True,
                    or_(
                        PatientAlertRule.muted_until.is_(None),
                        PatientAlertRule.muted_until > datetime.utcnow()
                    )
                )
            )
        )
        if result.scalar_one_or_none():
            return None

        # Evaluate thresholds
        value = reading.value
        severity = None
        message = None

        # Critical thresholds take precedence
        if thresholds.get("threshold_critical_high") and value >= thresholds["threshold_critical_high"]:
            severity = AlertSeverity.CRITICAL
            message = f"Critical high: {value} >= {thresholds['threshold_critical_high']}"
        elif thresholds.get("threshold_critical_low") and value <= thresholds["threshold_critical_low"]:
            severity = AlertSeverity.CRITICAL
            message = f"Critical low: {value} <= {thresholds['threshold_critical_low']}"
        elif thresholds.get("threshold_high") and value >= thresholds["threshold_high"]:
            severity = rule.severity
            message = f"High threshold: {value} >= {thresholds['threshold_high']}"
        elif thresholds.get("threshold_low") and value <= thresholds["threshold_low"]:
            severity = rule.severity
            message = f"Low threshold: {value} <= {thresholds['threshold_low']}"

        if not severity:
            return None

        # Create alert
        alert = RPMAlert(
            tenant_id=tenant_id,
            patient_id=reading.patient_id,
            enrollment_id=reading.enrollment_id,
            rule_id=rule.id,
            reading_id=reading.id,
            alert_type=rule.alert_type,
            severity=severity,
            status=AlertStatus.TRIGGERED,
            title=f"{rule.name} - {reading.reading_type.value}",
            message=message,
            reading_value=value,
            threshold_value=thresholds.get("threshold_high") or thresholds.get("threshold_low"),
            reading_type=reading.reading_type
        )

        db.add(alert)
        await db.commit()
        await db.refresh(alert)

        logger.info(
            f"Alert triggered: {alert.id} for patient {reading.patient_id}, "
            f"severity {severity.value}"
        )

        # Create notifications
        await self._create_notifications(db, alert, rule)

        return alert

    async def _check_cooldown(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        patient_id: UUID,
        rule_id: UUID
    ) -> bool:
        """Check if we're within the cooldown period for this rule."""
        rule_result = await db.execute(
            select(AlertRule).where(AlertRule.id == rule_id)
        )
        rule = rule_result.scalar_one_or_none()
        if not rule:
            return False

        cooldown_start = datetime.utcnow() - timedelta(minutes=rule.cooldown_minutes)

        result = await db.execute(
            select(func.count()).select_from(RPMAlert).where(
                and_(
                    RPMAlert.tenant_id == tenant_id,
                    RPMAlert.patient_id == patient_id,
                    RPMAlert.rule_id == rule_id,
                    RPMAlert.triggered_at > cooldown_start
                )
            )
        )
        count = result.scalar()
        return count == 0

    async def _create_notifications(
        self,
        db: AsyncSession,
        alert: RPMAlert,
        rule: AlertRule
    ) -> List[AlertNotification]:
        """Create notifications for an alert."""
        notifications = []

        # This would integrate with the notification service
        # For now, create notification records

        if rule.notify_provider:
            notification = AlertNotification(
                tenant_id=alert.tenant_id,
                alert_id=alert.id,
                recipient_id=UUID("00000000-0000-0000-0000-000000000000"),  # Placeholder
                recipient_type="provider",
                channel=OutreachChannel.PUSH_NOTIFICATION,
                status="pending"
            )
            db.add(notification)
            notifications.append(notification)

        if rule.notify_patient:
            notification = AlertNotification(
                tenant_id=alert.tenant_id,
                alert_id=alert.id,
                recipient_id=alert.patient_id,
                recipient_type="patient",
                channel=OutreachChannel.PUSH_NOTIFICATION,
                status="pending"
            )
            db.add(notification)
            notifications.append(notification)

        await db.commit()
        return notifications

    # =========================================================================
    # Alert management
    # =========================================================================

    async def get_alert(
        self,
        db: AsyncSession,
        alert_id: UUID,
        tenant_id: UUID
    ) -> Optional[RPMAlert]:
        """Get alert by ID."""
        result = await db.execute(
            select(RPMAlert)
            .options(
                selectinload(RPMAlert.rule),
                selectinload(RPMAlert.reading),
                selectinload(RPMAlert.notifications)
            )
            .where(
                and_(
                    RPMAlert.id == alert_id,
                    RPMAlert.tenant_id == tenant_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_alerts(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        filters: AlertFilters,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[RPMAlert], int]:
        """List alerts with filters."""
        query = select(RPMAlert).where(RPMAlert.tenant_id == tenant_id)

        if filters.patient_id:
            query = query.where(RPMAlert.patient_id == filters.patient_id)
        if filters.enrollment_id:
            query = query.where(RPMAlert.enrollment_id == filters.enrollment_id)
        if filters.severity:
            query = query.where(RPMAlert.severity == filters.severity)
        if filters.status:
            query = query.where(RPMAlert.status == filters.status)
        if filters.alert_type:
            query = query.where(RPMAlert.alert_type == filters.alert_type)
        if filters.start_date:
            query = query.where(RPMAlert.triggered_at >= filters.start_date)
        if filters.end_date:
            query = query.where(RPMAlert.triggered_at <= filters.end_date)

        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()

        query = query.offset(skip).limit(limit).order_by(
            RPMAlert.triggered_at.desc()
        )
        result = await db.execute(query)
        alerts = result.scalars().all()

        return list(alerts), total

    async def get_active_alerts(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        patient_id: Optional[UUID] = None
    ) -> List[RPMAlert]:
        """Get all active (unresolved) alerts."""
        query = select(RPMAlert).where(
            and_(
                RPMAlert.tenant_id == tenant_id,
                RPMAlert.status.in_([
                    AlertStatus.TRIGGERED,
                    AlertStatus.ACKNOWLEDGED,
                    AlertStatus.IN_PROGRESS,
                    AlertStatus.ESCALATED
                ])
            )
        )

        if patient_id:
            query = query.where(RPMAlert.patient_id == patient_id)

        query = query.order_by(RPMAlert.severity.desc(), RPMAlert.triggered_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def acknowledge_alert(
        self,
        db: AsyncSession,
        alert_id: UUID,
        tenant_id: UUID,
        acknowledged_by: UUID,
        ack_data: AlertAcknowledge
    ) -> Optional[RPMAlert]:
        """Acknowledge an alert."""
        alert = await self.get_alert(db, alert_id, tenant_id)
        if not alert:
            return None

        if alert.status not in [AlertStatus.TRIGGERED, AlertStatus.ESCALATED]:
            raise ValueError(f"Cannot acknowledge alert in {alert.status.value} status")

        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = acknowledged_by
        if ack_data.notes:
            alert.metadata = alert.metadata or {}
            alert.metadata["acknowledge_notes"] = ack_data.notes

        alert.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(alert)

        logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
        return alert

    async def resolve_alert(
        self,
        db: AsyncSession,
        alert_id: UUID,
        tenant_id: UUID,
        resolved_by: UUID,
        resolve_data: AlertResolve
    ) -> Optional[RPMAlert]:
        """Resolve an alert."""
        alert = await self.get_alert(db, alert_id, tenant_id)
        if not alert:
            return None

        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by = resolved_by
        alert.resolution_notes = resolve_data.resolution_notes
        if resolve_data.action_taken:
            alert.metadata = alert.metadata or {}
            alert.metadata["action_taken"] = resolve_data.action_taken

        alert.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(alert)

        logger.info(f"Alert {alert_id} resolved by {resolved_by}")
        return alert

    async def escalate_alert(
        self,
        db: AsyncSession,
        alert_id: UUID,
        tenant_id: UUID,
        escalate_data: AlertEscalate
    ) -> Optional[RPMAlert]:
        """Escalate an alert."""
        alert = await self.get_alert(db, alert_id, tenant_id)
        if not alert:
            return None

        alert.status = AlertStatus.ESCALATED
        alert.escalated_at = datetime.utcnow()
        alert.escalation_level += 1
        alert.escalated_to = escalate_data.escalate_to
        alert.metadata = alert.metadata or {}
        alert.metadata["escalation_reason"] = escalate_data.reason

        alert.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(alert)

        # Create notifications for escalated recipients
        for recipient_id in escalate_data.escalate_to:
            notification = AlertNotification(
                tenant_id=tenant_id,
                alert_id=alert.id,
                recipient_id=recipient_id,
                recipient_type="escalation",
                channel=OutreachChannel.PUSH_NOTIFICATION,
                status="pending"
            )
            db.add(notification)

        await db.commit()

        logger.info(f"Alert {alert_id} escalated to level {alert.escalation_level}")
        return alert

    async def dismiss_alert(
        self,
        db: AsyncSession,
        alert_id: UUID,
        tenant_id: UUID,
        dismissed_by: UUID,
        reason: str
    ) -> Optional[RPMAlert]:
        """Dismiss an alert."""
        alert = await self.get_alert(db, alert_id, tenant_id)
        if not alert:
            return None

        alert.status = AlertStatus.DISMISSED
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by = dismissed_by
        alert.resolution_notes = f"Dismissed: {reason}"
        alert.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(alert)
        return alert

    async def get_alert_statistics(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime,
        patient_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get alert statistics."""
        base_filter = and_(
            RPMAlert.tenant_id == tenant_id,
            RPMAlert.triggered_at.between(start_date, end_date)
        )

        if patient_id:
            base_filter = and_(base_filter, RPMAlert.patient_id == patient_id)

        # Total alerts
        total_result = await db.execute(
            select(func.count()).select_from(RPMAlert).where(base_filter)
        )
        total = total_result.scalar()

        # By severity
        severity_result = await db.execute(
            select(
                RPMAlert.severity,
                func.count(RPMAlert.id)
            ).where(base_filter).group_by(RPMAlert.severity)
        )
        by_severity = {row[0].value: row[1] for row in severity_result.all()}

        # By status
        status_result = await db.execute(
            select(
                RPMAlert.status,
                func.count(RPMAlert.id)
            ).where(base_filter).group_by(RPMAlert.status)
        )
        by_status = {row[0].value: row[1] for row in status_result.all()}

        # Response time (triggered -> acknowledged)
        response_result = await db.execute(
            select(
                func.avg(
                    func.extract('epoch', RPMAlert.acknowledged_at - RPMAlert.triggered_at)
                )
            ).where(
                and_(
                    base_filter,
                    RPMAlert.acknowledged_at.isnot(None)
                )
            )
        )
        avg_response_seconds = response_result.scalar()

        return {
            "total_alerts": total,
            "by_severity": by_severity,
            "by_status": by_status,
            "avg_response_time_seconds": float(avg_response_seconds) if avg_response_seconds else None,
        }
