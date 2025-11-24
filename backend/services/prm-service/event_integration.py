"""
PRM Service Event Integration
Enhanced event publishing and consumption for PRM workflows
"""
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID

from loguru import logger
from sqlalchemy.orm import Session, joinedload

from shared.database.connection import get_db_session
from shared.database.models import (
    Journey,
    JourneyInstance,
    JourneyStage,
    JourneyInstanceStageStatus,
    Appointment,
    Patient,
)
from shared.events import (
    publish_event,
    EventType,
    EventConsumer,
    Event,
    get_workflow_engine,
    WorkflowDefinition,
    WorkflowStep,
)


class PRMEventIntegration:
    """
    Enhanced event integration for PRM service

    Features:
    - Publishes events on journey state changes
    - Consumes events from other services
    - Integrates with workflow engine for complex flows
    - Automatic journey instance creation
    """

    def __init__(self):
        """Initialize PRM event integration"""
        self.consumer = EventConsumer(
            group_id="prm-service-consumer",
            topics=[
                "healthtech.patient.events",
                "healthtech.appointment.events",
                "healthtech.encounter.events",
                "healthtech.clinical.events",
            ],
        )

    async def start(self):
        """Start event consumer"""
        logger.info("Starting PRM event integration...")

        # Register event handlers
        self.consumer.register_handler(
            EventType.PATIENT_CREATED, self._handle_patient_created
        )
        self.consumer.register_handler(
            EventType.APPOINTMENT_CREATED, self._handle_appointment_created
        )
        self.consumer.register_handler(
            EventType.APPOINTMENT_CHECKED_IN, self._handle_appointment_checked_in
        )
        self.consumer.register_handler(
            EventType.APPOINTMENT_CANCELLED, self._handle_appointment_cancelled
        )
        self.consumer.register_handler(
            EventType.ENCOUNTER_CREATED, self._handle_encounter_created
        )
        self.consumer.register_handler(
            EventType.ENCOUNTER_COMPLETED, self._handle_encounter_completed
        )

        # Start consuming
        logger.info("PRM event consumer started")
        await self.consumer.start()

    async def _handle_patient_created(self, event: Event):
        """
        Handle Patient.Created event

        Create welcome journey instance if configured
        """
        try:
            logger.info(f"Handling Patient.Created: {event.event_id}")

            patient_id = UUID(event.payload["patient_id"])
            tenant_id = event.tenant_id

            with get_db_session() as db:
                # Find welcome journey
                welcome_journey = (
                    db.query(Journey)
                    .filter(
                        Journey.tenant_id == UUID(tenant_id),
                        Journey.journey_type == "welcome",
                        Journey.is_default == True,
                    )
                    .first()
                )

                if welcome_journey:
                    await self._create_journey_instance(
                        db=db,
                        journey=welcome_journey,
                        patient_id=patient_id,
                        tenant_id=tenant_id,
                        trigger_event="patient_created",
                    )

        except Exception as e:
            logger.error(f"Error handling Patient.Created: {e}")

    async def _handle_appointment_created(self, event: Event):
        """
        Handle Appointment.Created event

        Create OPD journey instance automatically
        """
        try:
            logger.info(f"Handling Appointment.Created: {event.event_id}")

            appointment_id = UUID(event.payload["appointment_id"])
            patient_id = UUID(event.payload["patient_id"])
            tenant_id = event.tenant_id

            with get_db_session() as db:
                # Find default OPD journey
                opd_journey = (
                    db.query(Journey)
                    .options(joinedload(Journey.stages))
                    .filter(
                        Journey.tenant_id == UUID(tenant_id),
                        Journey.journey_type == "opd",
                        Journey.is_default == True,
                    )
                    .first()
                )

                if not opd_journey:
                    logger.info(f"No default OPD journey for tenant {tenant_id}")
                    return

                # Check if instance already exists
                existing = (
                    db.query(JourneyInstance)
                    .filter(JourneyInstance.appointment_id == appointment_id)
                    .first()
                )

                if existing:
                    logger.info(f"Journey instance already exists: {existing.id}")
                    return

                # Create journey instance
                await self._create_journey_instance(
                    db=db,
                    journey=opd_journey,
                    patient_id=patient_id,
                    tenant_id=tenant_id,
                    appointment_id=appointment_id,
                    trigger_event="appointment_created",
                )

        except Exception as e:
            logger.error(f"Error handling Appointment.Created: {e}")

    async def _handle_appointment_checked_in(self, event: Event):
        """
        Handle Appointment.CheckedIn event

        Move journey to "checked-in" stage
        """
        try:
            logger.info(f"Handling Appointment.CheckedIn: {event.event_id}")

            appointment_id = UUID(event.payload["appointment_id"])
            tenant_id = event.tenant_id

            with get_db_session() as db:
                # Find journey instance
                instance = (
                    db.query(JourneyInstance)
                    .filter(JourneyInstance.appointment_id == appointment_id)
                    .first()
                )

                if not instance:
                    logger.info(f"No journey instance for appointment {appointment_id}")
                    return

                # Complete check-in stage
                await self._complete_stage(
                    db=db,
                    instance=instance,
                    stage_name="check-in",
                    tenant_id=tenant_id,
                )

        except Exception as e:
            logger.error(f"Error handling Appointment.CheckedIn: {e}")

    async def _handle_appointment_cancelled(self, event: Event):
        """Handle Appointment.Cancelled event"""
        try:
            logger.info(f"Handling Appointment.Cancelled: {event.event_id}")

            appointment_id = UUID(event.payload["appointment_id"])
            tenant_id = event.tenant_id

            with get_db_session() as db:
                instance = (
                    db.query(JourneyInstance)
                    .filter(JourneyInstance.appointment_id == appointment_id)
                    .first()
                )

                if instance and instance.status != "completed":
                    instance.status = "cancelled"
                    instance.cancelled_at = datetime.utcnow()
                    db.commit()

                    # Publish event
                    await publish_event(
                        event_type=EventType.JOURNEY_INSTANCE_CANCELLED,
                        tenant_id=tenant_id,
                        payload={
                            "instance_id": str(instance.id),
                            "journey_id": str(instance.journey_id),
                            "patient_id": str(instance.patient_id),
                            "reason": "appointment_cancelled",
                        },
                        source_service="prm-service",
                    )

        except Exception as e:
            logger.error(f"Error handling Appointment.Cancelled: {e}")

    async def _handle_encounter_created(self, event: Event):
        """Handle Encounter.Created event"""
        try:
            logger.info(f"Handling Encounter.Created: {event.event_id}")

            # Move journey to "consultation" stage
            appointment_id = event.payload.get("appointment_id")
            if appointment_id:
                tenant_id = event.tenant_id

                with get_db_session() as db:
                    instance = (
                        db.query(JourneyInstance)
                        .filter(JourneyInstance.appointment_id == UUID(appointment_id))
                        .first()
                    )

                    if instance:
                        await self._complete_stage(
                            db=db,
                            instance=instance,
                            stage_name="consultation",
                            tenant_id=tenant_id,
                        )

        except Exception as e:
            logger.error(f"Error handling Encounter.Created: {e}")

    async def _handle_encounter_completed(self, event: Event):
        """Handle Encounter.Completed event"""
        try:
            logger.info(f"Handling Encounter.Completed: {event.event_id}")

            encounter_id = UUID(event.payload["encounter_id"])
            tenant_id = event.tenant_id

            # Mark journey instance as completed
            with get_db_session() as db:
                instance = (
                    db.query(JourneyInstance)
                    .filter(
                        JourneyInstance.encounter_id == encounter_id,
                        JourneyInstance.status == "active",
                    )
                    .first()
                )

                if instance:
                    instance.status = "completed"
                    instance.completed_at = datetime.utcnow()
                    db.commit()

                    # Publish event
                    await publish_event(
                        event_type=EventType.JOURNEY_INSTANCE_COMPLETED,
                        tenant_id=tenant_id,
                        payload={
                            "instance_id": str(instance.id),
                            "journey_id": str(instance.journey_id),
                            "patient_id": str(instance.patient_id),
                        },
                        source_service="prm-service",
                    )

        except Exception as e:
            logger.error(f"Error handling Encounter.Completed: {e}")

    async def _create_journey_instance(
        self,
        db: Session,
        journey: Journey,
        patient_id: UUID,
        tenant_id: str,
        appointment_id: Optional[UUID] = None,
        trigger_event: Optional[str] = None,
    ):
        """
        Create a journey instance

        Args:
            db: Database session
            journey: Journey template
            patient_id: Patient ID
            tenant_id: Tenant ID
            appointment_id: Optional appointment ID
            trigger_event: Event that triggered creation
        """
        try:
            # Create instance
            instance = JourneyInstance(
                tenant_id=UUID(tenant_id),
                journey_id=journey.id,
                patient_id=patient_id,
                appointment_id=appointment_id,
                status="active",
                started_at=datetime.utcnow(),
            )

            db.add(instance)
            db.flush()

            # Create stage statuses
            if journey.stages:
                first_stage = sorted(journey.stages, key=lambda s: s.order_index)[0]

                for stage in journey.stages:
                    stage_status = JourneyInstanceStageStatus(
                        tenant_id=UUID(tenant_id),
                        instance_id=instance.id,
                        stage_id=stage.id,
                        status="active" if stage.id == first_stage.id else "pending",
                        started_at=(
                            datetime.utcnow() if stage.id == first_stage.id else None
                        ),
                    )
                    db.add(stage_status)

            db.commit()

            logger.info(f"Created journey instance: {instance.id}")

            # Publish event
            await publish_event(
                event_type=EventType.JOURNEY_INSTANCE_CREATED,
                tenant_id=tenant_id,
                payload={
                    "instance_id": str(instance.id),
                    "journey_id": str(journey.id),
                    "journey_name": journey.name,
                    "patient_id": str(patient_id),
                    "appointment_id": str(appointment_id) if appointment_id else None,
                    "trigger_event": trigger_event,
                },
                source_service="prm-service",
            )

        except Exception as e:
            logger.error(f"Error creating journey instance: {e}")
            db.rollback()
            raise

    async def _complete_stage(
        self,
        db: Session,
        instance: JourneyInstance,
        stage_name: str,
        tenant_id: str,
    ):
        """
        Complete a journey stage and move to next

        Args:
            db: Database session
            instance: Journey instance
            stage_name: Name of stage to complete
            tenant_id: Tenant ID
        """
        try:
            # Find current stage
            current_stage_status = (
                db.query(JourneyInstanceStageStatus)
                .join(JourneyStage)
                .filter(
                    JourneyInstanceStageStatus.instance_id == instance.id,
                    JourneyInstanceStageStatus.status == "active",
                    JourneyStage.name.ilike(f"%{stage_name}%"),
                )
                .first()
            )

            if not current_stage_status:
                logger.info(f"No active stage matching '{stage_name}'")
                return

            # Complete current stage
            current_stage_status.status = "completed"
            current_stage_status.completed_at = datetime.utcnow()

            # Publish stage completed event
            await publish_event(
                event_type=EventType.JOURNEY_STAGE_COMPLETED,
                tenant_id=tenant_id,
                payload={
                    "instance_id": str(instance.id),
                    "stage_id": str(current_stage_status.stage_id),
                    "stage_name": current_stage_status.stage.name,
                },
                source_service="prm-service",
            )

            # Find next stage
            next_stage = (
                db.query(JourneyInstanceStageStatus)
                .join(JourneyStage)
                .filter(
                    JourneyInstanceStageStatus.instance_id == instance.id,
                    JourneyInstanceStageStatus.status == "pending",
                    JourneyStage.order_index
                    > current_stage_status.stage.order_index,
                )
                .order_by(JourneyStage.order_index)
                .first()
            )

            if next_stage:
                next_stage.status = "active"
                next_stage.started_at = datetime.utcnow()

                # Publish stage entered event
                await publish_event(
                    event_type=EventType.JOURNEY_STAGE_ENTERED,
                    tenant_id=tenant_id,
                    payload={
                        "instance_id": str(instance.id),
                        "stage_id": str(next_stage.stage_id),
                        "stage_name": next_stage.stage.name,
                    },
                    source_service="prm-service",
                )

            db.commit()
            logger.info(f"Completed stage '{stage_name}' for instance {instance.id}")

        except Exception as e:
            logger.error(f"Error completing stage: {e}")
            db.rollback()


# Standalone script to run PRM event consumer
async def main():
    """Run PRM event consumer"""
    integration = PRMEventIntegration()

    logger.info("Starting PRM service event integration...")

    try:
        await integration.start()
    except KeyboardInterrupt:
        logger.info("Shutting down PRM event integration...")
    except Exception as e:
        logger.error(f"PRM event integration error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
