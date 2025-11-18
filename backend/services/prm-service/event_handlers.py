"""
PRM Service Event Handlers
Consume events from other services to orchestrate journeys
"""
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from loguru import logger
from sqlalchemy.orm import Session, joinedload

from shared.database.connection import get_db_session
from shared.database.models import (
    Journey, JourneyInstance, JourneyStage, JourneyInstanceStageStatus,
    Appointment, Patient, Communication
)
from shared.events.publisher import publish_event
from shared.events.types import EventType
from shared.events.consumer import EventConsumer


class PRMEventHandler:
    """Handler for PRM-related events"""

    def __init__(self):
        self.consumer = EventConsumer(
            group_id="prm-service",
            topics=[
                "appointment.created",
                "appointment.checked_in",
                "appointment.cancelled",
                "encounter.created",
                "encounter.completed"
            ]
        )

    async def start(self):
        """Start consuming events"""
        logger.info("Starting PRM event consumer...")

        await self.consumer.consume(
            handlers={
                "appointment.created": self.handle_appointment_created,
                "appointment.checked_in": self.handle_appointment_checked_in,
                "appointment.cancelled": self.handle_appointment_cancelled,
                "encounter.created": self.handle_encounter_created,
                "encounter.completed": self.handle_encounter_completed
            }
        )

    async def handle_appointment_created(self, event: Dict[str, Any]):
        """
        Handle Appointment.Created event

        Auto-create journey instance if default journey exists for OPD
        """
        try:
            logger.info(f"Handling Appointment.Created event: {event.get('event_id')}")

            payload = event.get("payload", {})
            tenant_id = UUID(event.get("tenant_id"))
            appointment_id = UUID(payload.get("appointment_id"))
            patient_id = UUID(payload.get("patient_id"))

            db = next(get_db_session())

            try:
                # Find default OPD journey for this tenant
                default_journey = db.query(Journey).options(
                    joinedload(Journey.stages)
                ).filter(
                    Journey.tenant_id == tenant_id,
                    Journey.journey_type == "opd",
                    Journey.is_default == True
                ).first()

                if not default_journey:
                    logger.info(f"No default OPD journey found for tenant {tenant_id}")
                    return

                # Check if journey instance already exists for this appointment
                existing_instance = db.query(JourneyInstance).filter(
                    JourneyInstance.appointment_id == appointment_id
                ).first()

                if existing_instance:
                    logger.info(
                        f"Journey instance already exists for appointment {appointment_id}"
                    )
                    return

                # Get first stage
                first_stage = sorted(
                    default_journey.stages,
                    key=lambda s: s.order_index
                )[0] if default_journey.stages else None

                # Create journey instance
                instance = JourneyInstance(
                    tenant_id=tenant_id,
                    journey_id=default_journey.id,
                    patient_id=patient_id,
                    appointment_id=appointment_id,
                    status="active",
                    current_stage_id=first_stage.id if first_stage else None,
                    context={
                        "created_by": "auto",
                        "trigger_event": "appointment.created",
                        "appointment_type": payload.get("appointment_type")
                    },
                    started_at=datetime.utcnow()
                )

                db.add(instance)
                db.flush()

                # Create stage status records
                for stage in default_journey.stages:
                    stage_status = JourneyInstanceStageStatus(
                        journey_instance_id=instance.id,
                        stage_id=stage.id,
                        status="in_progress" if stage.id == first_stage.id else "not_started",
                        entered_at=datetime.utcnow() if stage.id == first_stage.id else None
                    )
                    db.add(stage_status)

                db.commit()

                logger.info(
                    f"Auto-created journey instance {instance.id} for appointment {appointment_id}"
                )

                # Publish event
                await publish_event(
                    event_type=EventType.JOURNEY_INSTANCE_CREATED,
                    tenant_id=str(tenant_id),
                    payload={
                        "journey_instance_id": str(instance.id),
                        "journey_id": str(default_journey.id),
                        "patient_id": str(patient_id),
                        "appointment_id": str(appointment_id),
                        "auto_created": True
                    },
                    source_service="prm-service"
                )

                # Execute first stage actions
                if first_stage and first_stage.actions:
                    await self._execute_stage_actions(
                        instance.id,
                        first_stage,
                        db
                    )

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error handling Appointment.Created event: {e}")

    async def handle_appointment_checked_in(self, event: Dict[str, Any]):
        """
        Handle Appointment.CheckedIn event

        Advance journey to "day-of-visit" stage
        """
        try:
            logger.info(f"Handling Appointment.CheckedIn event: {event.get('event_id')}")

            payload = event.get("payload", {})
            appointment_id = UUID(payload.get("appointment_id"))

            db = next(get_db_session())

            try:
                # Find active journey instance for this appointment
                instance = db.query(JourneyInstance).options(
                    joinedload(JourneyInstance.journey).joinedload(Journey.stages)
                ).filter(
                    JourneyInstance.appointment_id == appointment_id,
                    JourneyInstance.status == "active"
                ).first()

                if not instance:
                    logger.info(
                        f"No active journey instance found for appointment {appointment_id}"
                    )
                    return

                # Find stage with trigger_event "Appointment.CheckedIn"
                target_stage = next(
                    (s for s in instance.journey.stages
                     if s.trigger_event == "Appointment.CheckedIn"),
                    None
                )

                if not target_stage:
                    logger.info("No stage configured for Appointment.CheckedIn trigger")
                    return

                # Advance to this stage
                await self._advance_to_stage(instance, target_stage, db)

                logger.info(
                    f"Advanced journey instance {instance.id} to stage {target_stage.id} "
                    f"on check-in"
                )

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error handling Appointment.CheckedIn event: {e}")

    async def handle_appointment_cancelled(self, event: Dict[str, Any]):
        """
        Handle Appointment.Cancelled event

        Cancel or pause associated journey instance
        """
        try:
            logger.info(f"Handling Appointment.Cancelled event: {event.get('event_id')}")

            payload = event.get("payload", {})
            appointment_id = UUID(payload.get("appointment_id"))

            db = next(get_db_session())

            try:
                # Find active journey instance for this appointment
                instance = db.query(JourneyInstance).filter(
                    JourneyInstance.appointment_id == appointment_id,
                    JourneyInstance.status == "active"
                ).first()

                if not instance:
                    logger.info(
                        f"No active journey instance found for appointment {appointment_id}"
                    )
                    return

                # Cancel the journey
                instance.status = "cancelled"
                instance.updated_at = datetime.utcnow()

                db.commit()

                logger.info(f"Cancelled journey instance {instance.id}")

                # Publish event
                await publish_event(
                    event_type=EventType.JOURNEY_INSTANCE_CANCELLED,
                    tenant_id=str(instance.tenant_id),
                    payload={
                        "journey_instance_id": str(instance.id),
                        "patient_id": str(instance.patient_id),
                        "reason": "appointment_cancelled"
                    },
                    source_service="prm-service"
                )

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error handling Appointment.Cancelled event: {e}")

    async def handle_encounter_created(self, event: Dict[str, Any]):
        """
        Handle Encounter.Created event

        Link encounter to journey instance if exists
        """
        try:
            logger.info(f"Handling Encounter.Created event: {event.get('event_id')}")

            payload = event.get("payload", {})
            encounter_id = UUID(payload.get("encounter_id"))
            appointment_id = payload.get("appointment_id")

            if not appointment_id:
                logger.info("Encounter not linked to appointment, skipping")
                return

            appointment_id = UUID(appointment_id)

            db = next(get_db_session())

            try:
                # Find journey instance for this appointment
                instance = db.query(JourneyInstance).filter(
                    JourneyInstance.appointment_id == appointment_id,
                    JourneyInstance.status == "active"
                ).first()

                if not instance:
                    logger.info(
                        f"No active journey instance found for appointment {appointment_id}"
                    )
                    return

                # Link encounter to journey instance
                instance.encounter_id = encounter_id
                instance.updated_at = datetime.utcnow()

                db.commit()

                logger.info(
                    f"Linked encounter {encounter_id} to journey instance {instance.id}"
                )

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error handling Encounter.Created event: {e}")

    async def handle_encounter_completed(self, event: Dict[str, Any]):
        """
        Handle Encounter.Completed event

        Advance journey to "post-visit" stage
        """
        try:
            logger.info(f"Handling Encounter.Completed event: {event.get('event_id')}")

            payload = event.get("payload", {})
            encounter_id = UUID(payload.get("encounter_id"))

            db = next(get_db_session())

            try:
                # Find journey instance for this encounter
                instance = db.query(JourneyInstance).options(
                    joinedload(JourneyInstance.journey).joinedload(Journey.stages)
                ).filter(
                    JourneyInstance.encounter_id == encounter_id,
                    JourneyInstance.status == "active"
                ).first()

                if not instance:
                    logger.info(
                        f"No active journey instance found for encounter {encounter_id}"
                    )
                    return

                # Find stage with trigger_event "Encounter.Completed"
                target_stage = next(
                    (s for s in instance.journey.stages
                     if s.trigger_event == "Encounter.Completed"),
                    None
                )

                if not target_stage:
                    logger.info("No stage configured for Encounter.Completed trigger")
                    return

                # Advance to this stage
                await self._advance_to_stage(instance, target_stage, db)

                logger.info(
                    f"Advanced journey instance {instance.id} to stage {target_stage.id} "
                    f"on encounter completion"
                )

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error handling Encounter.Completed event: {e}")

    async def _advance_to_stage(
        self,
        instance: JourneyInstance,
        target_stage: JourneyStage,
        db: Session
    ):
        """Advance journey instance to a specific stage"""
        try:
            # Mark current stage as completed if exists
            if instance.current_stage_id:
                current_stage_status = db.query(JourneyInstanceStageStatus).filter(
                    JourneyInstanceStageStatus.journey_instance_id == instance.id,
                    JourneyInstanceStageStatus.stage_id == instance.current_stage_id
                ).first()

                if current_stage_status:
                    current_stage_status.status = "completed"
                    current_stage_status.completed_at = datetime.utcnow()

            # Update instance current stage
            instance.current_stage_id = target_stage.id
            instance.updated_at = datetime.utcnow()

            # Update target stage status
            target_stage_status = db.query(JourneyInstanceStageStatus).filter(
                JourneyInstanceStageStatus.journey_instance_id == instance.id,
                JourneyInstanceStageStatus.stage_id == target_stage.id
            ).first()

            if target_stage_status:
                target_stage_status.status = "in_progress"
                target_stage_status.entered_at = datetime.utcnow()

            db.commit()

            # Publish stage entered event
            await publish_event(
                event_type=EventType.JOURNEY_STAGE_ENTERED,
                tenant_id=str(instance.tenant_id),
                payload={
                    "journey_instance_id": str(instance.id),
                    "stage_id": str(target_stage.id),
                    "stage_name": target_stage.name,
                    "patient_id": str(instance.patient_id)
                },
                source_service="prm-service"
            )

            # Execute stage actions
            if target_stage.actions:
                await self._execute_stage_actions(instance.id, target_stage, db)

        except Exception as e:
            db.rollback()
            logger.error(f"Error advancing to stage: {e}")
            raise

    async def _execute_stage_actions(
        self,
        instance_id: UUID,
        stage: JourneyStage,
        db: Session
    ):
        """Execute actions configured in a journey stage"""
        try:
            actions = stage.actions or {}

            # Get instance for context
            instance = db.query(JourneyInstance).options(
                joinedload(JourneyInstance.patient)
            ).filter(JourneyInstance.id == instance_id).first()

            if not instance:
                logger.error(f"Journey instance {instance_id} not found")
                return

            # Handle send_communication action
            if "send_communication" in actions:
                await self._send_stage_communication(
                    instance,
                    actions["send_communication"],
                    db
                )

            # Handle create_task action
            if "create_task" in actions:
                logger.info(f"Task creation action (not yet implemented)")

            # Handle notify_staff action
            if "notify_staff" in actions:
                logger.info(f"Staff notification action (not yet implemented)")

        except Exception as e:
            logger.error(f"Error executing stage actions: {e}")

    async def _send_stage_communication(
        self,
        instance: JourneyInstance,
        comm_config: Dict[str, Any],
        db: Session
    ):
        """Send communication as defined in stage action"""
        try:
            patient = instance.patient

            # Get patient contact info
            recipient = None
            channel = comm_config.get("channel", "whatsapp")

            if channel in ["whatsapp", "sms"]:
                recipient = patient.phone
            elif channel == "email":
                recipient = patient.email

            if not recipient:
                logger.warning(
                    f"No {channel} contact info for patient {patient.id}"
                )
                return

            # Render message from template
            template_name = comm_config.get("template")
            message = comm_config.get("message", "")

            if template_name:
                # TODO: Load and render template with patient/appointment data
                message = f"Template: {template_name}"

            # Create communication
            communication = Communication(
                tenant_id=instance.tenant_id,
                patient_id=instance.patient_id,
                journey_instance_id=instance.id,
                channel=channel,
                recipient=recipient,
                subject=comm_config.get("subject"),
                message=message,
                template_name=template_name,
                status="pending"
            )

            db.add(communication)
            db.commit()

            logger.info(
                f"Created communication {communication.id} from stage action "
                f"for journey instance {instance.id}"
            )

            # TODO: Trigger actual sending via communication provider
            # For now, just mark as sent
            communication.status = "sent"
            communication.sent_at = datetime.utcnow()
            db.commit()

        except Exception as e:
            logger.error(f"Error sending stage communication: {e}")


# ==================== Standalone Runner ====================

async def main():
    """Main entry point for event consumer"""
    handler = PRMEventHandler()
    await handler.start()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
