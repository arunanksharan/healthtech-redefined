"""
Provider Collaboration Alert Service
EPIC-015: Clinical alerts and notification management
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from modules.provider_collaboration.models import (
    ClinicalAlert, AlertRule, CollaborationAuditLog,
    AlertPriority, AlertStatus, AlertDeliveryStatus, AlertRuleType
)
from modules.provider_collaboration.schemas import (
    AlertCreate, AlertRuleCreate, AlertRuleUpdate,
    AlertResponse, AlertRuleResponse, AlertListResponse, AlertRuleListResponse
)


class AlertService:
    """
    Handles clinical alerts including:
    - Alert creation and delivery
    - Alert rules management
    - Alert acknowledgment and escalation
    - Priority-based routing
    """

    def __init__(self):
        # Auto-escalation timeouts in minutes by priority
        self.escalation_timeouts = {
            AlertPriority.LOW: 120,
            AlertPriority.MEDIUM: 60,
            AlertPriority.HIGH: 15,
            AlertPriority.CRITICAL: 5
        }

    async def create_alert(
        self,
        db: AsyncSession,
        sender_id: UUID,
        tenant_id: UUID,
        data: AlertCreate,
        ip_address: str = None
    ) -> AlertResponse:
        """Create and send a clinical alert"""

        now = datetime.now(timezone.utc)
        timeout = self.escalation_timeouts.get(
            AlertPriority(data.priority.value),
            60
        )
        escalation_deadline = now + timedelta(minutes=timeout)

        alert = ClinicalAlert(
            id=uuid4(),
            tenant_id=tenant_id,
            alert_type=data.alert_type,
            priority=AlertPriority(data.priority.value),
            title=data.title,
            message=data.message,
            patient_id=data.patient_id,
            sender_id=sender_id,
            recipient_id=data.recipient_id,
            recipient_group=data.recipient_group,
            care_team_id=data.care_team_id,
            related_entity_type=data.related_entity_type,
            related_entity_id=data.related_entity_id,
            status=AlertStatus.ACTIVE,
            status_updated_at=now,
            delivery_status=AlertDeliveryStatus.PENDING,
            delivery_channels=data.delivery_channels or ["in_app"],
            requires_acknowledgment=data.requires_acknowledgment,
            escalation_deadline=escalation_deadline if data.requires_acknowledgment else None,
            action_required=data.action_required,
            action_url=data.action_url,
            metadata=data.metadata
        )
        db.add(alert)

        # Log action
        audit_log = CollaborationAuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            provider_id=sender_id,
            action="alert_created",
            action_category="alert",
            action_description=f"Created {data.priority.value} priority alert: {data.title}",
            entity_type="alert",
            entity_id=alert.id,
            details={
                "alert_type": data.alert_type,
                "priority": data.priority.value,
                "recipient_id": str(data.recipient_id) if data.recipient_id else None,
                "recipient_group": data.recipient_group
            },
            ip_address=ip_address
        )
        db.add(audit_log)

        await db.commit()
        await db.refresh(alert)

        return self._alert_to_response(alert)

    async def get_alert(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        alert_id: UUID
    ) -> AlertResponse:
        """Get alert details"""

        result = await db.execute(
            select(ClinicalAlert).where(
                and_(
                    ClinicalAlert.id == alert_id,
                    ClinicalAlert.tenant_id == tenant_id
                )
            )
        )
        alert = result.scalar_one_or_none()

        if not alert:
            raise ValueError("Alert not found")

        return self._alert_to_response(alert)

    async def list_alerts(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        recipient_id: Optional[UUID] = None,
        patient_id: Optional[UUID] = None,
        priority: Optional[AlertPriority] = None,
        status: Optional[AlertStatus] = None,
        alert_type: Optional[str] = None,
        unread_only: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> AlertListResponse:
        """List alerts with filters"""

        query = select(ClinicalAlert).where(
            ClinicalAlert.tenant_id == tenant_id
        )

        if recipient_id:
            query = query.where(ClinicalAlert.recipient_id == recipient_id)

        if patient_id:
            query = query.where(ClinicalAlert.patient_id == patient_id)

        if priority:
            query = query.where(ClinicalAlert.priority == priority)

        if status:
            query = query.where(ClinicalAlert.status == status)

        if alert_type:
            query = query.where(ClinicalAlert.alert_type == alert_type)

        if unread_only:
            query = query.where(ClinicalAlert.read_at.is_(None))

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Count unread
        unread_query = select(func.count()).select_from(
            query.where(ClinicalAlert.read_at.is_(None)).subquery()
        )
        unread_result = await db.execute(unread_query)
        unread_count = unread_result.scalar()

        # Get paginated results, ordered by priority and creation time
        query = query.order_by(
            ClinicalAlert.priority,  # CRITICAL first
            desc(ClinicalAlert.created_at)
        )
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        alerts = result.scalars().all()

        return AlertListResponse(
            alerts=[self._alert_to_response(a) for a in alerts],
            total=total,
            unread_count=unread_count,
            page=page,
            page_size=page_size
        )

    async def mark_as_read(
        self,
        db: AsyncSession,
        provider_id: UUID,
        alert_id: UUID
    ) -> AlertResponse:
        """Mark an alert as read"""

        result = await db.execute(
            select(ClinicalAlert).where(ClinicalAlert.id == alert_id)
        )
        alert = result.scalar_one_or_none()

        if not alert:
            raise ValueError("Alert not found")

        if not alert.read_at:
            alert.read_at = datetime.now(timezone.utc)
            alert.read_by = provider_id
            await db.commit()
            await db.refresh(alert)

        return self._alert_to_response(alert)

    async def mark_multiple_as_read(
        self,
        db: AsyncSession,
        provider_id: UUID,
        tenant_id: UUID,
        alert_ids: List[UUID]
    ) -> int:
        """Mark multiple alerts as read"""

        now = datetime.now(timezone.utc)
        result = await db.execute(
            update(ClinicalAlert).where(
                and_(
                    ClinicalAlert.id.in_(alert_ids),
                    ClinicalAlert.tenant_id == tenant_id,
                    ClinicalAlert.read_at.is_(None)
                )
            ).values(
                read_at=now,
                read_by=provider_id
            )
        )

        await db.commit()
        return result.rowcount

    async def acknowledge_alert(
        self,
        db: AsyncSession,
        provider_id: UUID,
        alert_id: UUID,
        notes: str = None
    ) -> AlertResponse:
        """Acknowledge an alert"""

        result = await db.execute(
            select(ClinicalAlert).where(ClinicalAlert.id == alert_id)
        )
        alert = result.scalar_one_or_none()

        if not alert:
            raise ValueError("Alert not found")

        if alert.status != AlertStatus.ACTIVE:
            raise ValueError("Alert is not active")

        now = datetime.now(timezone.utc)
        alert.acknowledged_at = now
        alert.acknowledged_by = provider_id
        alert.acknowledgment_notes = notes
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.status_updated_at = now

        if not alert.read_at:
            alert.read_at = now
            alert.read_by = provider_id

        await db.commit()
        await db.refresh(alert)

        return self._alert_to_response(alert)

    async def resolve_alert(
        self,
        db: AsyncSession,
        provider_id: UUID,
        alert_id: UUID,
        resolution: str
    ) -> AlertResponse:
        """Resolve an alert"""

        result = await db.execute(
            select(ClinicalAlert).where(ClinicalAlert.id == alert_id)
        )
        alert = result.scalar_one_or_none()

        if not alert:
            raise ValueError("Alert not found")

        if alert.status == AlertStatus.RESOLVED:
            raise ValueError("Alert is already resolved")

        now = datetime.now(timezone.utc)
        alert.resolved_at = now
        alert.resolved_by = provider_id
        alert.resolution = resolution
        alert.status = AlertStatus.RESOLVED
        alert.status_updated_at = now

        await db.commit()
        await db.refresh(alert)

        return self._alert_to_response(alert)

    async def dismiss_alert(
        self,
        db: AsyncSession,
        provider_id: UUID,
        alert_id: UUID,
        reason: str = None
    ) -> AlertResponse:
        """Dismiss an alert"""

        result = await db.execute(
            select(ClinicalAlert).where(ClinicalAlert.id == alert_id)
        )
        alert = result.scalar_one_or_none()

        if not alert:
            raise ValueError("Alert not found")

        now = datetime.now(timezone.utc)
        alert.status = AlertStatus.DISMISSED
        alert.status_updated_at = now
        alert.dismissed_at = now
        alert.dismissed_by = provider_id
        alert.dismissal_reason = reason

        await db.commit()
        await db.refresh(alert)

        return self._alert_to_response(alert)

    async def escalate_alert(
        self,
        db: AsyncSession,
        alert_id: UUID,
        new_recipient_id: UUID = None,
        new_recipient_group: str = None
    ) -> AlertResponse:
        """Escalate an unacknowledged alert"""

        result = await db.execute(
            select(ClinicalAlert).where(ClinicalAlert.id == alert_id)
        )
        alert = result.scalar_one_or_none()

        if not alert:
            raise ValueError("Alert not found")

        if alert.status != AlertStatus.ACTIVE:
            raise ValueError("Can only escalate active alerts")

        now = datetime.now(timezone.utc)
        alert.escalated_at = now
        alert.escalation_count = (alert.escalation_count or 0) + 1
        alert.status = AlertStatus.ESCALATED
        alert.status_updated_at = now

        if new_recipient_id:
            alert.recipient_id = new_recipient_id
        if new_recipient_group:
            alert.recipient_group = new_recipient_group

        # Set new escalation deadline
        timeout = self.escalation_timeouts.get(alert.priority, 60) // 2
        alert.escalation_deadline = now + timedelta(minutes=max(timeout, 5))

        await db.commit()
        await db.refresh(alert)

        return self._alert_to_response(alert)

    async def update_delivery_status(
        self,
        db: AsyncSession,
        alert_id: UUID,
        status: AlertDeliveryStatus,
        channel: str = None,
        error: str = None
    ) -> AlertResponse:
        """Update alert delivery status"""

        result = await db.execute(
            select(ClinicalAlert).where(ClinicalAlert.id == alert_id)
        )
        alert = result.scalar_one_or_none()

        if not alert:
            raise ValueError("Alert not found")

        alert.delivery_status = status
        if status == AlertDeliveryStatus.DELIVERED:
            alert.delivered_at = datetime.now(timezone.utc)
        elif status == AlertDeliveryStatus.FAILED:
            delivery_errors = alert.delivery_errors or []
            delivery_errors.append({
                "channel": channel,
                "error": error,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            alert.delivery_errors = delivery_errors

        await db.commit()
        await db.refresh(alert)

        return self._alert_to_response(alert)

    async def get_alerts_needing_escalation(
        self,
        db: AsyncSession,
        tenant_id: UUID
    ) -> List[AlertResponse]:
        """Get alerts that have passed their escalation deadline"""

        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(ClinicalAlert).where(
                and_(
                    ClinicalAlert.tenant_id == tenant_id,
                    ClinicalAlert.status == AlertStatus.ACTIVE,
                    ClinicalAlert.requires_acknowledgment == True,
                    ClinicalAlert.acknowledged_at.is_(None),
                    ClinicalAlert.escalation_deadline < now
                )
            ).order_by(ClinicalAlert.priority)
        )
        alerts = result.scalars().all()

        return [self._alert_to_response(a) for a in alerts]

    # Alert Rules Management

    async def create_rule(
        self,
        db: AsyncSession,
        provider_id: UUID,
        tenant_id: UUID,
        data: AlertRuleCreate,
        ip_address: str = None
    ) -> AlertRuleResponse:
        """Create an alert rule"""

        rule = AlertRule(
            id=uuid4(),
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            rule_type=AlertRuleType(data.rule_type.value),
            trigger_conditions=data.trigger_conditions,
            alert_template={
                "alert_type": data.alert_type,
                "priority": data.priority.value,
                "title_template": data.title_template,
                "message_template": data.message_template,
                "delivery_channels": data.delivery_channels,
                "requires_acknowledgment": data.requires_acknowledgment
            },
            recipient_config=data.recipient_config,
            is_active=data.is_active,
            created_by=provider_id
        )
        db.add(rule)

        # Log action
        audit_log = CollaborationAuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            provider_id=provider_id,
            action="alert_rule_created",
            action_category="alert",
            action_description=f"Created alert rule: {data.name}",
            entity_type="alert_rule",
            entity_id=rule.id,
            details={
                "rule_type": data.rule_type.value,
                "is_active": data.is_active
            },
            ip_address=ip_address
        )
        db.add(audit_log)

        await db.commit()
        await db.refresh(rule)

        return self._rule_to_response(rule)

    async def get_rule(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        rule_id: UUID
    ) -> AlertRuleResponse:
        """Get alert rule details"""

        result = await db.execute(
            select(AlertRule).where(
                and_(
                    AlertRule.id == rule_id,
                    AlertRule.tenant_id == tenant_id
                )
            )
        )
        rule = result.scalar_one_or_none()

        if not rule:
            raise ValueError("Rule not found")

        return self._rule_to_response(rule)

    async def list_rules(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        rule_type: Optional[AlertRuleType] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> AlertRuleListResponse:
        """List alert rules"""

        query = select(AlertRule).where(AlertRule.tenant_id == tenant_id)

        if rule_type:
            query = query.where(AlertRule.rule_type == rule_type)

        if is_active is not None:
            query = query.where(AlertRule.is_active == is_active)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Get paginated results
        query = query.order_by(AlertRule.name)
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        rules = result.scalars().all()

        return AlertRuleListResponse(
            rules=[self._rule_to_response(r) for r in rules],
            total=total,
            page=page,
            page_size=page_size
        )

    async def update_rule(
        self,
        db: AsyncSession,
        provider_id: UUID,
        tenant_id: UUID,
        rule_id: UUID,
        data: AlertRuleUpdate
    ) -> AlertRuleResponse:
        """Update an alert rule"""

        result = await db.execute(
            select(AlertRule).where(
                and_(
                    AlertRule.id == rule_id,
                    AlertRule.tenant_id == tenant_id
                )
            )
        )
        rule = result.scalar_one_or_none()

        if not rule:
            raise ValueError("Rule not found")

        if data.name is not None:
            rule.name = data.name
        if data.description is not None:
            rule.description = data.description
        if data.trigger_conditions is not None:
            rule.trigger_conditions = data.trigger_conditions
        if data.recipient_config is not None:
            rule.recipient_config = data.recipient_config
        if data.is_active is not None:
            rule.is_active = data.is_active

        rule.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(rule)

        return self._rule_to_response(rule)

    async def delete_rule(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        rule_id: UUID
    ) -> bool:
        """Delete an alert rule"""

        result = await db.execute(
            select(AlertRule).where(
                and_(
                    AlertRule.id == rule_id,
                    AlertRule.tenant_id == tenant_id
                )
            )
        )
        rule = result.scalar_one_or_none()

        if not rule:
            raise ValueError("Rule not found")

        await db.delete(rule)
        await db.commit()

        return True

    async def toggle_rule(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        rule_id: UUID
    ) -> AlertRuleResponse:
        """Toggle alert rule active status"""

        result = await db.execute(
            select(AlertRule).where(
                and_(
                    AlertRule.id == rule_id,
                    AlertRule.tenant_id == tenant_id
                )
            )
        )
        rule = result.scalar_one_or_none()

        if not rule:
            raise ValueError("Rule not found")

        rule.is_active = not rule.is_active
        rule.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(rule)

        return self._rule_to_response(rule)

    async def evaluate_rule(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        rule_id: UUID,
        context: Dict[str, Any]
    ) -> Optional[AlertResponse]:
        """Evaluate an alert rule against given context and create alert if triggered"""

        result = await db.execute(
            select(AlertRule).where(
                and_(
                    AlertRule.id == rule_id,
                    AlertRule.tenant_id == tenant_id,
                    AlertRule.is_active == True
                )
            )
        )
        rule = result.scalar_one_or_none()

        if not rule:
            return None

        # Evaluate trigger conditions
        if not self._evaluate_conditions(rule.trigger_conditions, context):
            return None

        # Create alert from template
        template = rule.alert_template
        recipient_config = rule.recipient_config or {}

        alert = ClinicalAlert(
            id=uuid4(),
            tenant_id=tenant_id,
            alert_type=template.get("alert_type", "rule_triggered"),
            priority=AlertPriority(template.get("priority", "medium")),
            title=self._interpolate_template(template.get("title_template", "Alert"), context),
            message=self._interpolate_template(template.get("message_template", ""), context),
            patient_id=context.get("patient_id"),
            sender_id=context.get("sender_id"),
            recipient_id=recipient_config.get("provider_id"),
            recipient_group=recipient_config.get("group"),
            care_team_id=recipient_config.get("care_team_id"),
            related_entity_type=context.get("entity_type"),
            related_entity_id=context.get("entity_id"),
            status=AlertStatus.ACTIVE,
            status_updated_at=datetime.now(timezone.utc),
            delivery_status=AlertDeliveryStatus.PENDING,
            delivery_channels=template.get("delivery_channels", ["in_app"]),
            requires_acknowledgment=template.get("requires_acknowledgment", False),
            triggered_by_rule_id=rule.id,
            metadata={"trigger_context": context}
        )
        db.add(alert)

        # Update rule statistics
        rule.trigger_count = (rule.trigger_count or 0) + 1
        rule.last_triggered_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(alert)

        return self._alert_to_response(alert)

    def _evaluate_conditions(
        self,
        conditions: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate trigger conditions against context"""
        # Simple condition evaluation
        # In production, this would be more sophisticated
        for key, expected in conditions.items():
            if key == "and":
                return all(self._evaluate_conditions(c, context) for c in expected)
            elif key == "or":
                return any(self._evaluate_conditions(c, context) for c in expected)
            elif key == "not":
                return not self._evaluate_conditions(expected, context)
            elif key.endswith("_gt"):
                field = key[:-3]
                if field in context:
                    return context[field] > expected
            elif key.endswith("_lt"):
                field = key[:-3]
                if field in context:
                    return context[field] < expected
            elif key.endswith("_gte"):
                field = key[:-4]
                if field in context:
                    return context[field] >= expected
            elif key.endswith("_lte"):
                field = key[:-4]
                if field in context:
                    return context[field] <= expected
            elif key.endswith("_in"):
                field = key[:-3]
                if field in context:
                    return context[field] in expected
            elif key.endswith("_contains"):
                field = key[:-9]
                if field in context:
                    return expected in context[field]
            else:
                if context.get(key) != expected:
                    return False

        return True

    def _interpolate_template(self, template: str, context: Dict[str, Any]) -> str:
        """Interpolate template string with context values"""
        try:
            return template.format(**context)
        except (KeyError, ValueError):
            return template

    def _alert_to_response(self, alert: ClinicalAlert) -> AlertResponse:
        """Convert alert model to response schema"""
        return AlertResponse(
            id=alert.id,
            alert_type=alert.alert_type,
            priority=alert.priority.value,
            title=alert.title,
            message=alert.message,
            patient_id=alert.patient_id,
            sender_id=alert.sender_id,
            recipient_id=alert.recipient_id,
            recipient_group=alert.recipient_group,
            care_team_id=alert.care_team_id,
            related_entity_type=alert.related_entity_type,
            related_entity_id=alert.related_entity_id,
            status=alert.status.value,
            delivery_status=alert.delivery_status.value,
            delivery_channels=alert.delivery_channels or [],
            requires_acknowledgment=alert.requires_acknowledgment,
            read_at=alert.read_at,
            acknowledged_at=alert.acknowledged_at,
            acknowledged_by=alert.acknowledged_by,
            resolved_at=alert.resolved_at,
            resolution=alert.resolution,
            escalated_at=alert.escalated_at,
            escalation_count=alert.escalation_count,
            action_required=alert.action_required,
            action_url=alert.action_url,
            created_at=alert.created_at
        )

    def _rule_to_response(self, rule: AlertRule) -> AlertRuleResponse:
        """Convert rule model to response schema"""
        return AlertRuleResponse(
            id=rule.id,
            name=rule.name,
            description=rule.description,
            rule_type=rule.rule_type.value,
            trigger_conditions=rule.trigger_conditions or {},
            alert_template=rule.alert_template or {},
            recipient_config=rule.recipient_config or {},
            is_active=rule.is_active,
            trigger_count=rule.trigger_count,
            last_triggered_at=rule.last_triggered_at,
            created_at=rule.created_at
        )
