"""
Protocol Service for RPM

Handles care protocols, triggers, and automated actions.

EPIC-019: Remote Patient Monitoring
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
import logging

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import (
    CareProtocol, ProtocolTrigger, ProtocolAction, ProtocolExecution,
    RPMEnrollment, DeviceReading, ProtocolStatus, ProtocolTriggerType,
    ProtocolActionType, ReadingType
)
from ..schemas import (
    ProtocolCreate, ProtocolUpdate, ProtocolResponse,
    ProtocolTriggerCreate, ProtocolActionCreate,
    TriggerResponse, ActionResponse, ProtocolExecutionResponse
)

logger = logging.getLogger(__name__)


class ProtocolService:
    """Service for managing care protocols."""

    async def create_protocol(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        created_by: UUID,
        protocol_data: ProtocolCreate
    ) -> CareProtocol:
        """Create a new care protocol."""
        protocol = CareProtocol(
            tenant_id=tenant_id,
            name=protocol_data.name,
            description=protocol_data.description,
            condition=protocol_data.condition,
            version=protocol_data.version,
            duration_days=protocol_data.duration_days,
            reading_types=protocol_data.reading_types or [],
            target_readings_per_day=protocol_data.target_readings_per_day,
            status=ProtocolStatus.DRAFT,
            is_template=protocol_data.is_template,
            clinical_guidelines=protocol_data.clinical_guidelines or {},
            evidence_references=protocol_data.evidence_references or [],
            created_by=created_by
        )

        db.add(protocol)
        await db.flush()

        # Create triggers if provided
        if protocol_data.triggers:
            for i, trigger_data in enumerate(protocol_data.triggers):
                trigger = await self._create_trigger(db, protocol.id, trigger_data)
                protocol.triggers.append(trigger)

        await db.commit()
        await db.refresh(protocol)

        logger.info(f"Created protocol {protocol.id}: {protocol.name}")
        return protocol

    async def _create_trigger(
        self,
        db: AsyncSession,
        protocol_id: UUID,
        trigger_data: ProtocolTriggerCreate
    ) -> ProtocolTrigger:
        """Create a protocol trigger."""
        trigger = ProtocolTrigger(
            protocol_id=protocol_id,
            name=trigger_data.name,
            trigger_type=trigger_data.trigger_type,
            reading_type=trigger_data.reading_type,
            condition_operator=trigger_data.condition_operator,
            condition_value=trigger_data.condition_value,
            condition_value_2=trigger_data.condition_value_2,
            condition_unit=trigger_data.condition_unit,
            consecutive_count=trigger_data.consecutive_count,
            schedule_cron=trigger_data.schedule_cron,
            schedule_days=trigger_data.schedule_days,
            priority=trigger_data.priority,
            conditions=trigger_data.conditions or {},
            is_active=True
        )
        db.add(trigger)
        return trigger

    async def add_trigger(
        self,
        db: AsyncSession,
        protocol_id: UUID,
        tenant_id: UUID,
        trigger_data: ProtocolTriggerCreate
    ) -> Optional[ProtocolTrigger]:
        """Add a trigger to an existing protocol."""
        protocol = await self.get_protocol(db, protocol_id, tenant_id)
        if not protocol:
            return None

        trigger = await self._create_trigger(db, protocol_id, trigger_data)
        await db.commit()
        await db.refresh(trigger)
        return trigger

    async def add_action(
        self,
        db: AsyncSession,
        trigger_id: UUID,
        tenant_id: UUID,
        action_data: ProtocolActionCreate
    ) -> Optional[ProtocolAction]:
        """Add an action to a trigger."""
        # Verify trigger exists
        trigger_result = await db.execute(
            select(ProtocolTrigger)
            .join(CareProtocol)
            .where(
                and_(
                    ProtocolTrigger.id == trigger_id,
                    CareProtocol.tenant_id == tenant_id
                )
            )
        )
        trigger = trigger_result.scalar_one_or_none()
        if not trigger:
            return None

        action = ProtocolAction(
            trigger_id=trigger_id,
            action_type=action_data.action_type,
            name=action_data.name,
            description=action_data.description,
            message_template=action_data.message_template,
            channel=action_data.channel,
            recipient_type=action_data.recipient_type,
            delay_minutes=action_data.delay_minutes,
            requires_approval=action_data.requires_approval,
            approval_role=action_data.approval_role,
            sequence=action_data.sequence,
            config=action_data.config or {},
            is_active=True
        )

        db.add(action)
        await db.commit()
        await db.refresh(action)
        return action

    async def get_protocol(
        self,
        db: AsyncSession,
        protocol_id: UUID,
        tenant_id: UUID
    ) -> Optional[CareProtocol]:
        """Get protocol by ID."""
        result = await db.execute(
            select(CareProtocol)
            .options(
                selectinload(CareProtocol.triggers).selectinload(ProtocolTrigger.actions)
            )
            .where(
                and_(
                    CareProtocol.id == protocol_id,
                    CareProtocol.tenant_id == tenant_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_protocols(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        condition: Optional[str] = None,
        status: Optional[ProtocolStatus] = None,
        template_only: bool = False,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[CareProtocol], int]:
        """List protocols with filters."""
        query = select(CareProtocol).where(CareProtocol.tenant_id == tenant_id)

        if condition:
            query = query.where(CareProtocol.condition == condition)
        if status:
            query = query.where(CareProtocol.status == status)
        if template_only:
            query = query.where(CareProtocol.is_template == True)

        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()

        query = query.offset(skip).limit(limit).order_by(CareProtocol.created_at.desc())
        result = await db.execute(query)
        protocols = result.scalars().all()

        return list(protocols), total

    async def update_protocol(
        self,
        db: AsyncSession,
        protocol_id: UUID,
        tenant_id: UUID,
        update_data: ProtocolUpdate
    ) -> Optional[CareProtocol]:
        """Update protocol."""
        protocol = await self.get_protocol(db, protocol_id, tenant_id)
        if not protocol:
            return None

        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(protocol, field, value)

        protocol.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(protocol)
        return protocol

    async def activate_protocol(
        self,
        db: AsyncSession,
        protocol_id: UUID,
        tenant_id: UUID,
        approved_by: UUID
    ) -> Optional[CareProtocol]:
        """Activate a protocol."""
        protocol = await self.get_protocol(db, protocol_id, tenant_id)
        if not protocol:
            return None

        if protocol.status != ProtocolStatus.DRAFT:
            raise ValueError("Only draft protocols can be activated")

        protocol.status = ProtocolStatus.ACTIVE
        protocol.approved_by = approved_by
        protocol.approved_at = datetime.utcnow()
        protocol.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(protocol)
        return protocol

    async def copy_protocol(
        self,
        db: AsyncSession,
        protocol_id: UUID,
        tenant_id: UUID,
        created_by: UUID,
        new_name: str
    ) -> Optional[CareProtocol]:
        """Copy a protocol (useful for templates)."""
        source = await self.get_protocol(db, protocol_id, tenant_id)
        if not source:
            return None

        # Create new protocol
        new_protocol = CareProtocol(
            tenant_id=tenant_id,
            name=new_name,
            description=source.description,
            condition=source.condition,
            version="1.0",
            duration_days=source.duration_days,
            reading_types=source.reading_types,
            target_readings_per_day=source.target_readings_per_day,
            status=ProtocolStatus.DRAFT,
            is_template=False,
            clinical_guidelines=source.clinical_guidelines,
            evidence_references=source.evidence_references,
            created_by=created_by
        )

        db.add(new_protocol)
        await db.flush()

        # Copy triggers and actions
        for trigger in source.triggers:
            new_trigger = ProtocolTrigger(
                protocol_id=new_protocol.id,
                name=trigger.name,
                trigger_type=trigger.trigger_type,
                reading_type=trigger.reading_type,
                condition_operator=trigger.condition_operator,
                condition_value=trigger.condition_value,
                condition_value_2=trigger.condition_value_2,
                condition_unit=trigger.condition_unit,
                consecutive_count=trigger.consecutive_count,
                schedule_cron=trigger.schedule_cron,
                schedule_days=trigger.schedule_days,
                priority=trigger.priority,
                conditions=trigger.conditions,
                is_active=True
            )
            db.add(new_trigger)
            await db.flush()

            for action in trigger.actions:
                new_action = ProtocolAction(
                    trigger_id=new_trigger.id,
                    action_type=action.action_type,
                    name=action.name,
                    description=action.description,
                    message_template=action.message_template,
                    channel=action.channel,
                    recipient_type=action.recipient_type,
                    delay_minutes=action.delay_minutes,
                    requires_approval=action.requires_approval,
                    approval_role=action.approval_role,
                    sequence=action.sequence,
                    config=action.config,
                    is_active=True
                )
                db.add(new_action)

        await db.commit()
        await db.refresh(new_protocol)
        return new_protocol

    # =========================================================================
    # Protocol execution
    # =========================================================================

    async def evaluate_triggers(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        enrollment_id: UUID,
        reading: DeviceReading
    ) -> List[ProtocolExecution]:
        """Evaluate protocol triggers for a new reading."""
        # Get enrollment with protocol
        enrollment_result = await db.execute(
            select(RPMEnrollment)
            .options(selectinload(RPMEnrollment.protocol))
            .where(RPMEnrollment.id == enrollment_id)
        )
        enrollment = enrollment_result.scalar_one_or_none()

        if not enrollment or not enrollment.protocol:
            return []

        if enrollment.protocol.status != ProtocolStatus.ACTIVE:
            return []

        executions = []

        for trigger in enrollment.protocol.triggers:
            if not trigger.is_active:
                continue

            if trigger.reading_type and trigger.reading_type != reading.reading_type:
                continue

            if await self._evaluate_trigger(db, trigger, reading):
                # Schedule actions
                for action in trigger.actions:
                    if not action.is_active:
                        continue

                    execution = await self._schedule_action(
                        db, tenant_id, enrollment_id, action, reading.id
                    )
                    executions.append(execution)

        return executions

    async def _evaluate_trigger(
        self,
        db: AsyncSession,
        trigger: ProtocolTrigger,
        reading: DeviceReading
    ) -> bool:
        """Evaluate if a trigger condition is met."""
        if trigger.trigger_type == ProtocolTriggerType.THRESHOLD:
            value = reading.value
            operator = trigger.condition_operator
            threshold = trigger.condition_value
            threshold_2 = trigger.condition_value_2

            if operator == "gt" and value > threshold:
                return True
            elif operator == "lt" and value < threshold:
                return True
            elif operator == "gte" and value >= threshold:
                return True
            elif operator == "lte" and value <= threshold:
                return True
            elif operator == "eq" and value == threshold:
                return True
            elif operator == "between" and threshold <= value <= threshold_2:
                return True

        elif trigger.trigger_type == ProtocolTriggerType.TREND:
            # Would need historical readings to evaluate trends
            pass

        return False

    async def _schedule_action(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        enrollment_id: UUID,
        action: ProtocolAction,
        trigger_reading_id: UUID
    ) -> ProtocolExecution:
        """Schedule a protocol action for execution."""
        scheduled_at = datetime.utcnow() + timedelta(minutes=action.delay_minutes)

        execution = ProtocolExecution(
            tenant_id=tenant_id,
            enrollment_id=enrollment_id,
            action_id=action.id,
            trigger_reading_id=trigger_reading_id,
            status="pending" if not action.requires_approval else "pending_approval",
            scheduled_at=scheduled_at,
            requires_approval=action.requires_approval
        )

        db.add(execution)
        await db.commit()
        await db.refresh(execution)

        logger.info(
            f"Scheduled action {action.name} for enrollment {enrollment_id} "
            f"at {scheduled_at}"
        )
        return execution

    async def approve_execution(
        self,
        db: AsyncSession,
        execution_id: UUID,
        tenant_id: UUID,
        approved_by: UUID
    ) -> Optional[ProtocolExecution]:
        """Approve a pending execution."""
        result = await db.execute(
            select(ProtocolExecution).where(
                and_(
                    ProtocolExecution.id == execution_id,
                    ProtocolExecution.tenant_id == tenant_id
                )
            )
        )
        execution = result.scalar_one_or_none()

        if not execution:
            return None

        if execution.status != "pending_approval":
            raise ValueError("Execution is not pending approval")

        execution.status = "pending"
        execution.approved_by = approved_by
        execution.approved_at = datetime.utcnow()

        await db.commit()
        await db.refresh(execution)
        return execution

    async def reject_execution(
        self,
        db: AsyncSession,
        execution_id: UUID,
        tenant_id: UUID,
        rejected_by: UUID,
        reason: str
    ) -> Optional[ProtocolExecution]:
        """Reject a pending execution."""
        result = await db.execute(
            select(ProtocolExecution).where(
                and_(
                    ProtocolExecution.id == execution_id,
                    ProtocolExecution.tenant_id == tenant_id
                )
            )
        )
        execution = result.scalar_one_or_none()

        if not execution:
            return None

        execution.status = "cancelled"
        execution.rejection_reason = reason
        execution.metadata = execution.metadata or {}
        execution.metadata["rejected_by"] = str(rejected_by)

        await db.commit()
        await db.refresh(execution)
        return execution

    async def execute_pending_actions(
        self,
        db: AsyncSession,
        tenant_id: UUID
    ) -> List[ProtocolExecution]:
        """Execute actions that are due."""
        now = datetime.utcnow()

        result = await db.execute(
            select(ProtocolExecution)
            .options(selectinload(ProtocolExecution.action))
            .where(
                and_(
                    ProtocolExecution.tenant_id == tenant_id,
                    ProtocolExecution.status == "pending",
                    ProtocolExecution.scheduled_at <= now
                )
            ).limit(100)
        )
        executions = result.scalars().all()

        executed = []
        for execution in executions:
            try:
                await self._execute_action(db, execution)
                executed.append(execution)
            except Exception as e:
                logger.error(f"Failed to execute action {execution.id}: {e}")
                execution.status = "failed"
                execution.error_message = str(e)
                await db.commit()

        return executed

    async def _execute_action(
        self,
        db: AsyncSession,
        execution: ProtocolExecution
    ) -> None:
        """Execute a single protocol action."""
        execution.status = "executing"
        execution.executed_at = datetime.utcnow()
        await db.commit()

        action = execution.action

        try:
            # Execute based on action type
            if action.action_type == ProtocolActionType.SEND_MESSAGE:
                # Integration with messaging service
                result = {"status": "message_queued"}

            elif action.action_type == ProtocolActionType.MAKE_CALL:
                # Integration with Zoice
                result = {"status": "call_scheduled"}

            elif action.action_type == ProtocolActionType.ALERT_PROVIDER:
                # Integration with alert service
                result = {"status": "provider_notified"}

            elif action.action_type == ProtocolActionType.SCHEDULE_APPOINTMENT:
                # Integration with appointment service
                result = {"status": "appointment_created"}

            else:
                result = {"status": "action_logged"}

            execution.status = "completed"
            execution.completed_at = datetime.utcnow()
            execution.success = True
            execution.result_data = result

        except Exception as e:
            execution.status = "failed"
            execution.success = False
            execution.error_message = str(e)

        await db.commit()

    async def get_pending_executions(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        enrollment_id: Optional[UUID] = None
    ) -> List[ProtocolExecution]:
        """Get pending executions."""
        query = select(ProtocolExecution).options(
            selectinload(ProtocolExecution.action)
        ).where(
            and_(
                ProtocolExecution.tenant_id == tenant_id,
                ProtocolExecution.status.in_(["pending", "pending_approval"])
            )
        )

        if enrollment_id:
            query = query.where(ProtocolExecution.enrollment_id == enrollment_id)

        query = query.order_by(ProtocolExecution.scheduled_at.asc())
        result = await db.execute(query)
        return list(result.scalars().all())
