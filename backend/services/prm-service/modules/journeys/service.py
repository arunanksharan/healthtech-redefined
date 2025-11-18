"""
Journey Management Service
Business logic for journey orchestration
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from loguru import logger

from shared.database.models import (
    Journey, JourneyStage, JourneyInstance, JourneyInstanceStageStatus,
    Patient, Communication
)
from shared.events.publisher import publish_event
from shared.events.types import EventType

from .schemas import (
    JourneyCreate, JourneyUpdate, JourneyResponse, JourneyListResponse,
    JourneyStageCreate, JourneyStageUpdate,
    JourneyInstanceCreate, JourneyInstanceResponse,
    JourneyInstanceListResponse, JourneyInstanceWithStages,
    AdvanceStageRequest
)


class JourneyService:
    """Service class for journey management operations"""

    def __init__(self, db: Session):
        self.db = db

    async def create_journey(self, journey_data: JourneyCreate) -> Journey:
        """Create a new journey definition"""
        try:
            # Create journey
            journey = Journey(
                tenant_id=journey_data.tenant_id,
                name=journey_data.name,
                description=journey_data.description,
                journey_type=journey_data.journey_type.value,
                is_default=journey_data.is_default,
                trigger_conditions=journey_data.trigger_conditions
            )

            self.db.add(journey)
            self.db.flush()  # Get journey ID

            # Create stages if provided
            if journey_data.stages:
                for stage_data in journey_data.stages:
                    stage = JourneyStage(
                        journey_id=journey.id,
                        name=stage_data.name,
                        description=stage_data.description,
                        order_index=stage_data.order_index,
                        trigger_event=stage_data.trigger_event,
                        actions=stage_data.actions
                    )
                    self.db.add(stage)

            self.db.commit()
            self.db.refresh(journey)

            logger.info(f"Created journey {journey.id}: {journey.name}")

            # Publish event
            await publish_event(
                event_type=EventType.JOURNEY_CREATED,
                tenant_id=str(journey_data.tenant_id),
                payload={
                    "journey_id": str(journey.id),
                    "name": journey.name,
                    "journey_type": journey.journey_type,
                    "is_default": journey.is_default
                },
                source_service="prm-service"
            )

            return journey

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating journey: {e}")
            raise

    async def list_journeys(
        self,
        tenant_id: Optional[UUID] = None,
        journey_type: Optional[str] = None,
        is_default: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> JourneyListResponse:
        """List journeys with filters"""
        try:
            query = self.db.query(Journey).options(joinedload(Journey.stages))

            if tenant_id:
                query = query.filter(Journey.tenant_id == tenant_id)

            if journey_type:
                query = query.filter(Journey.journey_type == journey_type.lower())

            if is_default is not None:
                query = query.filter(Journey.is_default == is_default)

            # Get total count
            total = query.count()

            # Apply pagination
            offset = (page - 1) * page_size
            journeys = query.order_by(
                desc(Journey.is_default),
                Journey.name
            ).offset(offset).limit(page_size).all()

            has_next = (offset + page_size) < total
            has_previous = page > 1

            return JourneyListResponse(
                total=total,
                journeys=journeys,
                page=page,
                page_size=page_size,
                has_next=has_next,
                has_previous=has_previous
            )

        except Exception as e:
            logger.error(f"Error listing journeys: {e}")
            raise

    async def get_journey(self, journey_id: UUID) -> Optional[Journey]:
        """Get journey by ID with stages"""
        try:
            journey = self.db.query(Journey).options(
                joinedload(Journey.stages)
            ).filter(Journey.id == journey_id).first()

            return journey

        except Exception as e:
            logger.error(f"Error retrieving journey: {e}")
            raise

    async def update_journey(
        self,
        journey_id: UUID,
        journey_update: JourneyUpdate
    ) -> Optional[Journey]:
        """Update journey definition"""
        try:
            journey = self.db.query(Journey).filter(Journey.id == journey_id).first()

            if not journey:
                return None

            # Update fields
            if journey_update.name:
                journey.name = journey_update.name

            if journey_update.description is not None:
                journey.description = journey_update.description

            if journey_update.is_default is not None:
                journey.is_default = journey_update.is_default

            if journey_update.trigger_conditions is not None:
                journey.trigger_conditions = journey_update.trigger_conditions

            journey.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(journey)

            logger.info(f"Updated journey {journey_id}")

            return journey

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating journey: {e}")
            raise

    async def add_stage(
        self,
        journey_id: UUID,
        stage_data: JourneyStageCreate
    ) -> Optional[JourneyStage]:
        """Add a stage to a journey"""
        try:
            # Validate journey exists
            journey = self.db.query(Journey).filter(Journey.id == journey_id).first()

            if not journey:
                return None

            # Create stage
            stage = JourneyStage(
                journey_id=journey_id,
                name=stage_data.name,
                description=stage_data.description,
                order_index=stage_data.order_index,
                trigger_event=stage_data.trigger_event,
                actions=stage_data.actions
            )

            self.db.add(stage)
            self.db.commit()
            self.db.refresh(stage)

            logger.info(f"Added stage {stage.id} to journey {journey_id}")

            return stage

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding journey stage: {e}")
            raise

    async def update_stage(
        self,
        journey_id: UUID,
        stage_id: UUID,
        stage_update: JourneyStageUpdate
    ) -> Optional[JourneyStage]:
        """Update a journey stage"""
        try:
            stage = self.db.query(JourneyStage).filter(
                JourneyStage.id == stage_id,
                JourneyStage.journey_id == journey_id
            ).first()

            if not stage:
                return None

            # Update fields
            if stage_update.name:
                stage.name = stage_update.name

            if stage_update.description is not None:
                stage.description = stage_update.description

            if stage_update.order_index is not None:
                stage.order_index = stage_update.order_index

            if stage_update.trigger_event is not None:
                stage.trigger_event = stage_update.trigger_event

            if stage_update.actions is not None:
                stage.actions = stage_update.actions

            stage.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(stage)

            logger.info(f"Updated stage {stage_id}")

            return stage

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating journey stage: {e}")
            raise

    # ==================== Journey Instances ====================

    async def create_instance(
        self,
        instance_data: JourneyInstanceCreate,
        background_tasks: BackgroundTasks
    ) -> Optional[JourneyInstance]:
        """Create a journey instance for a patient"""
        try:
            # Validate journey exists
            journey = self.db.query(Journey).options(
                joinedload(Journey.stages)
            ).filter(
                Journey.id == instance_data.journey_id,
                Journey.tenant_id == instance_data.tenant_id
            ).first()

            if not journey:
                return None

            # Validate patient exists
            patient = self.db.query(Patient).filter(
                Patient.id == instance_data.patient_id,
                Patient.tenant_id == instance_data.tenant_id
            ).first()

            if not patient:
                return None

            # Get first stage (lowest order_index)
            first_stage = sorted(journey.stages, key=lambda s: s.order_index)[0] if journey.stages else None

            # Create journey instance
            instance = JourneyInstance(
                tenant_id=instance_data.tenant_id,
                journey_id=instance_data.journey_id,
                patient_id=instance_data.patient_id,
                appointment_id=instance_data.appointment_id,
                encounter_id=instance_data.encounter_id,
                status="active",
                current_stage_id=first_stage.id if first_stage else None,
                context=instance_data.context,
                started_at=datetime.utcnow()
            )

            self.db.add(instance)
            self.db.flush()  # Get instance ID

            # Create stage status records for all stages
            for stage in journey.stages:
                stage_status = JourneyInstanceStageStatus(
                    journey_instance_id=instance.id,
                    stage_id=stage.id,
                    status="in_progress" if stage.id == first_stage.id else "not_started",
                    entered_at=datetime.utcnow() if stage.id == first_stage.id else None
                )
                self.db.add(stage_status)

            self.db.commit()
            self.db.refresh(instance)

            logger.info(
                f"Created journey instance {instance.id} for patient {instance_data.patient_id}"
            )

            # Publish event
            await publish_event(
                event_type=EventType.JOURNEY_INSTANCE_CREATED,
                tenant_id=str(instance_data.tenant_id),
                payload={
                    "journey_instance_id": str(instance.id),
                    "journey_id": str(instance_data.journey_id),
                    "patient_id": str(instance_data.patient_id),
                    "appointment_id": str(instance_data.appointment_id) if instance_data.appointment_id else None,
                    "current_stage_id": str(first_stage.id) if first_stage else None
                },
                source_service="prm-service"
            )

            # Execute first stage actions if any
            if first_stage and first_stage.actions:
                background_tasks.add_task(
                    self._execute_stage_actions,
                    instance.id,
                    first_stage.id,
                    first_stage.actions
                )

            return instance

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating journey instance: {e}")
            raise

    async def list_instances(
        self,
        patient_id: Optional[UUID] = None,
        journey_id: Optional[UUID] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> JourneyInstanceListResponse:
        """List journey instances with filters"""
        try:
            query = self.db.query(JourneyInstance)

            if patient_id:
                query = query.filter(JourneyInstance.patient_id == patient_id)

            if journey_id:
                query = query.filter(JourneyInstance.journey_id == journey_id)

            if status:
                query = query.filter(JourneyInstance.status == status.lower())

            # Get total count
            total = query.count()

            # Apply pagination
            offset = (page - 1) * page_size
            instances = query.order_by(
                desc(JourneyInstance.started_at)
            ).offset(offset).limit(page_size).all()

            has_next = (offset + page_size) < total
            has_previous = page > 1

            return JourneyInstanceListResponse(
                total=total,
                instances=instances,
                page=page,
                page_size=page_size,
                has_next=has_next,
                has_previous=has_previous
            )

        except Exception as e:
            logger.error(f"Error listing journey instances: {e}")
            raise

    async def get_instance_with_stages(self, instance_id: UUID) -> Optional[JourneyInstanceWithStages]:
        """Get journey instance with stage statuses"""
        try:
            instance = self.db.query(JourneyInstance).options(
                joinedload(JourneyInstance.journey).joinedload(Journey.stages),
                joinedload(JourneyInstance.stage_statuses)
            ).filter(JourneyInstance.id == instance_id).first()

            if not instance:
                return None

            # Build response with stage details
            stages = []
            for stage in sorted(instance.journey.stages, key=lambda s: s.order_index):
                # Find status for this stage
                stage_status = next(
                    (ss for ss in instance.stage_statuses if ss.stage_id == stage.id),
                    None
                )

                stages.append({
                    "stage_id": str(stage.id),
                    "name": stage.name,
                    "description": stage.description,
                    "order_index": stage.order_index,
                    "status": stage_status.status if stage_status else "not_started",
                    "entered_at": stage_status.entered_at.isoformat() if stage_status and stage_status.entered_at else None,
                    "completed_at": stage_status.completed_at.isoformat() if stage_status and stage_status.completed_at else None,
                    "notes": stage_status.notes if stage_status else None
                })

            return JourneyInstanceWithStages(
                id=instance.id,
                tenant_id=instance.tenant_id,
                journey_id=instance.journey_id,
                journey_name=instance.journey.name,
                patient_id=instance.patient_id,
                status=instance.status,
                current_stage_id=instance.current_stage_id,
                started_at=instance.started_at,
                completed_at=instance.completed_at,
                stages=stages
            )

        except Exception as e:
            logger.error(f"Error retrieving journey instance: {e}")
            raise

    async def advance_stage(
        self,
        instance_id: UUID,
        advance_request: AdvanceStageRequest,
        background_tasks: BackgroundTasks
    ) -> Optional[JourneyInstance]:
        """Advance journey to next stage"""
        try:
            instance = self.db.query(JourneyInstance).options(
                joinedload(JourneyInstance.journey).joinedload(Journey.stages)
            ).filter(
                JourneyInstance.id == instance_id,
                JourneyInstance.status == "active"
            ).first()

            if not instance:
                return None

            if not instance.current_stage_id:
                logger.warning(f"Journey {instance_id} has no current stage")
                return None

            # Get current stage
            current_stage = next(
                (s for s in instance.journey.stages if s.id == instance.current_stage_id),
                None
            )

            if not current_stage:
                logger.error(f"Current stage not found for instance {instance_id}")
                return None

            # Mark current stage as completed
            current_stage_status = self.db.query(JourneyInstanceStageStatus).filter(
                JourneyInstanceStageStatus.journey_instance_id == instance_id,
                JourneyInstanceStageStatus.stage_id == instance.current_stage_id
            ).first()

            if current_stage_status:
                current_stage_status.status = "completed"
                current_stage_status.completed_at = datetime.utcnow()
                if advance_request.notes:
                    current_stage_status.notes = advance_request.notes

            # Find next stage
            sorted_stages = sorted(instance.journey.stages, key=lambda s: s.order_index)
            current_index = next(
                (i for i, s in enumerate(sorted_stages) if s.id == instance.current_stage_id),
                None
            )

            if current_index is None or current_index >= len(sorted_stages) - 1:
                # No more stages, complete journey
                instance.status = "completed"
                instance.current_stage_id = None
                instance.completed_at = datetime.utcnow()

                self.db.commit()
                self.db.refresh(instance)

                logger.info(f"Completed journey instance {instance_id}")

                # Publish completion event
                await publish_event(
                    event_type=EventType.JOURNEY_INSTANCE_COMPLETED,
                    tenant_id=str(instance.tenant_id),
                    payload={
                        "journey_instance_id": str(instance.id),
                        "patient_id": str(instance.patient_id)
                    },
                    source_service="prm-service"
                )

                return instance

            # Move to next stage
            next_stage = sorted_stages[current_index + 1]
            instance.current_stage_id = next_stage.id

            # Update next stage status
            next_stage_status = self.db.query(JourneyInstanceStageStatus).filter(
                JourneyInstanceStageStatus.journey_instance_id == instance_id,
                JourneyInstanceStageStatus.stage_id == next_stage.id
            ).first()

            if next_stage_status:
                next_stage_status.status = "in_progress"
                next_stage_status.entered_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(instance)

            logger.info(
                f"Advanced journey instance {instance_id} to stage {next_stage.id}"
            )

            # Publish stage entered event
            await publish_event(
                event_type=EventType.JOURNEY_STAGE_ENTERED,
                tenant_id=str(instance.tenant_id),
                payload={
                    "journey_instance_id": str(instance.id),
                    "stage_id": str(next_stage.id),
                    "stage_name": next_stage.name,
                    "patient_id": str(instance.patient_id)
                },
                source_service="prm-service"
            )

            # Execute next stage actions if any
            if next_stage.actions:
                background_tasks.add_task(
                    self._execute_stage_actions,
                    instance.id,
                    next_stage.id,
                    next_stage.actions
                )

            return instance

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error advancing journey stage: {e}")
            raise

    # ==================== Helper Methods ====================

    async def _execute_stage_actions(
        self,
        instance_id: UUID,
        stage_id: UUID,
        actions: dict
    ):
        """Execute actions defined in a journey stage"""
        try:
            logger.info(f"Executing actions for stage {stage_id} in instance {instance_id}")

            # Example: Send communication action
            if "send_communication" in actions:
                comm_action = actions["send_communication"]

                # Get instance to access patient info
                instance = self.db.query(JourneyInstance).filter(
                    JourneyInstance.id == instance_id
                ).first()

                if instance:
                    # Create communication based on action config
                    communication = Communication(
                        tenant_id=instance.tenant_id,
                        patient_id=instance.patient_id,
                        journey_instance_id=instance_id,
                        channel=comm_action.get("channel", "whatsapp"),
                        recipient=comm_action.get("recipient", ""),  # Should be populated from patient data
                        message=comm_action.get("message", ""),
                        template_name=comm_action.get("template"),
                        status="pending"
                    )
                    self.db.add(communication)
                    self.db.commit()

                    logger.info(f"Created communication {communication.id} from stage action")

        except Exception as e:
            logger.error(f"Error executing stage actions: {e}")
