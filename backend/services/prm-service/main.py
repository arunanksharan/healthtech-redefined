"""
PRM Service - Patient Relationship Management
Journey orchestration, communications, and patient engagement
"""
import os
import sys
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID
import re

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from fastapi import FastAPI, HTTPException, Depends, Query, status as http_status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc
from loguru import logger

from shared.database.connection import get_db, engine
from shared.database.models import (
    Base, Journey, JourneyStage, JourneyInstance, JourneyInstanceStageStatus,
    Communication, Ticket, Patient
)
from shared.events.publisher import publish_event
from shared.events.types import EventType
from shared.realtime import (
    websocket_router,
    startup_realtime,
    shutdown_realtime,
)

from schemas import (
    JourneyCreate, JourneyUpdate, JourneyResponse, JourneyListResponse,
    JourneyStageCreate, JourneyStageUpdate, JourneyStageResponse,
    JourneyInstanceCreate, JourneyInstanceUpdate, JourneyInstanceResponse,
    JourneyInstanceListResponse, JourneyInstanceWithStages,
    JourneyInstanceStageUpdate, AdvanceStageRequest,
    CommunicationCreate, CommunicationUpdate, CommunicationResponse,
    CommunicationListResponse, SendCommunicationRequest,
    TicketCreate, TicketUpdate, TicketResponse, TicketListResponse,
    TicketCommentCreate, TicketWithComments,
    TemplateRenderRequest, TemplateRenderResponse,
    JourneyStatus, StageStatus, CommunicationStatus, TicketStatus
)

# Initialize FastAPI app
app = FastAPI(
    title="PRM Service",
    description="Patient Relationship Management - Journey orchestration and communications",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

from fastapi.responses import RedirectResponse

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include WebSocket router for real-time features
app.include_router(websocket_router)


# ==================== Health Check ====================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "prm-service",
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== Journey Management ====================

@app.post(
    "/api/v1/prm/journeys",
    response_model=JourneyResponse,
    status_code=http_status.HTTP_201_CREATED,
    tags=["Journeys"]
)
async def create_journey(
    journey_data: JourneyCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new journey definition

    Journey defines the stages and automation for patient engagement.
    Can be marked as default to auto-apply when conditions are met.
    """
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

        db.add(journey)
        db.flush()  # Get journey ID

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
                db.add(stage)

        db.commit()
        db.refresh(journey)

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
        db.rollback()
        logger.error(f"Error creating journey: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create journey: {str(e)}"
        )


@app.get(
    "/api/v1/prm/journeys",
    response_model=JourneyListResponse,
    tags=["Journeys"]
)
async def list_journeys(
    tenant_id: Optional[UUID] = Query(None),
    journey_type: Optional[str] = Query(None),
    is_default: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List journey definitions with filters"""
    try:
        query = db.query(Journey).options(joinedload(Journey.stages))

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
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list journeys"
        )


@app.get(
    "/api/v1/prm/journeys/{journey_id}",
    response_model=JourneyResponse,
    tags=["Journeys"]
)
async def get_journey(
    journey_id: UUID,
    db: Session = Depends(get_db)
):
    """Get journey definition with stages"""
    try:
        journey = db.query(Journey).options(
            joinedload(Journey.stages)
        ).filter(Journey.id == journey_id).first()

        if not journey:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Journey not found"
            )

        return journey

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving journey: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve journey"
        )


@app.patch(
    "/api/v1/prm/journeys/{journey_id}",
    response_model=JourneyResponse,
    tags=["Journeys"]
)
async def update_journey(
    journey_id: UUID,
    journey_update: JourneyUpdate,
    db: Session = Depends(get_db)
):
    """Update journey definition"""
    try:
        journey = db.query(Journey).filter(Journey.id == journey_id).first()

        if not journey:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Journey not found"
            )

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

        db.commit()
        db.refresh(journey)

        logger.info(f"Updated journey {journey_id}")

        return journey

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating journey: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update journey"
        )


# ==================== Journey Stages ====================

@app.post(
    "/api/v1/prm/journeys/{journey_id}/stages",
    response_model=JourneyStageResponse,
    status_code=http_status.HTTP_201_CREATED,
    tags=["Journeys"]
)
async def add_journey_stage(
    journey_id: UUID,
    stage_data: JourneyStageCreate,
    db: Session = Depends(get_db)
):
    """Add a stage to a journey"""
    try:
        # Validate journey exists
        journey = db.query(Journey).filter(Journey.id == journey_id).first()

        if not journey:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Journey not found"
            )

        # Create stage
        stage = JourneyStage(
            journey_id=journey_id,
            name=stage_data.name,
            description=stage_data.description,
            order_index=stage_data.order_index,
            trigger_event=stage_data.trigger_event,
            actions=stage_data.actions
        )

        db.add(stage)
        db.commit()
        db.refresh(stage)

        logger.info(f"Added stage {stage.id} to journey {journey_id}")

        return stage

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding journey stage: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add journey stage"
        )


@app.patch(
    "/api/v1/prm/journeys/{journey_id}/stages/{stage_id}",
    response_model=JourneyStageResponse,
    tags=["Journeys"]
)
async def update_journey_stage(
    journey_id: UUID,
    stage_id: UUID,
    stage_update: JourneyStageUpdate,
    db: Session = Depends(get_db)
):
    """Update a journey stage"""
    try:
        stage = db.query(JourneyStage).filter(
            JourneyStage.id == stage_id,
            JourneyStage.journey_id == journey_id
        ).first()

        if not stage:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Journey stage not found"
            )

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

        db.commit()
        db.refresh(stage)

        logger.info(f"Updated stage {stage_id}")

        return stage

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating journey stage: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update journey stage"
        )


# ==================== Journey Instances ====================

@app.post(
    "/api/v1/prm/instances",
    response_model=JourneyInstanceResponse,
    status_code=http_status.HTTP_201_CREATED,
    tags=["Journey Instances"]
)
async def create_journey_instance(
    instance_data: JourneyInstanceCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create a journey instance for a patient

    This starts a patient on a specific journey, creating stage status tracking.
    """
    try:
        # Validate journey exists
        journey = db.query(Journey).options(
            joinedload(Journey.stages)
        ).filter(
            Journey.id == instance_data.journey_id,
            Journey.tenant_id == instance_data.tenant_id
        ).first()

        if not journey:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Journey not found"
            )

        # Validate patient exists
        patient = db.query(Patient).filter(
            Patient.id == instance_data.patient_id,
            Patient.tenant_id == instance_data.tenant_id
        ).first()

        if not patient:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )

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

        db.add(instance)
        db.flush()  # Get instance ID

        # Create stage status records for all stages
        for stage in journey.stages:
            stage_status = JourneyInstanceStageStatus(
                journey_instance_id=instance.id,
                stage_id=stage.id,
                status="in_progress" if stage.id == first_stage.id else "not_started",
                entered_at=datetime.utcnow() if stage.id == first_stage.id else None
            )
            db.add(stage_status)

        db.commit()
        db.refresh(instance)

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
                _execute_stage_actions,
                instance.id,
                first_stage.id,
                first_stage.actions,
                db
            )

        return instance

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating journey instance: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create journey instance: {str(e)}"
        )


@app.get(
    "/api/v1/prm/instances",
    response_model=JourneyInstanceListResponse,
    tags=["Journey Instances"]
)
async def list_journey_instances(
    patient_id: Optional[UUID] = Query(None),
    journey_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List journey instances with filters"""
    try:
        query = db.query(JourneyInstance)

        if patient_id:
            query = query.filter(JourneyInstance.patient_id == patient_id)

        if journey_id:
            query = query.filter(JourneyInstance.journey_id == journey_id)

        if status:
            query = query.filter(JourneyInstance.status == http_status.lower())

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
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list journey instances"
        )


@app.get(
    "/api/v1/prm/instances/{instance_id}",
    response_model=JourneyInstanceWithStages,
    tags=["Journey Instances"]
)
async def get_journey_instance(
    instance_id: UUID,
    db: Session = Depends(get_db)
):
    """Get journey instance with stage statuses"""
    try:
        instance = db.query(JourneyInstance).options(
            joinedload(JourneyInstance.journey).joinedload(Journey.stages),
            joinedload(JourneyInstance.stage_statuses)
        ).filter(JourneyInstance.id == instance_id).first()

        if not instance:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Journey instance not found"
            )

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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving journey instance: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve journey instance"
        )


@app.post(
    "/api/v1/prm/instances/{instance_id}/advance",
    response_model=JourneyInstanceResponse,
    tags=["Journey Instances"]
)
async def advance_journey_stage(
    instance_id: UUID,
    advance_request: AdvanceStageRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Advance journey to next stage

    Marks current stage as completed and moves to next stage in sequence.
    """
    try:
        instance = db.query(JourneyInstance).options(
            joinedload(JourneyInstance.journey).joinedload(Journey.stages)
        ).filter(
            JourneyInstance.id == instance_id,
            JourneyInstance.status == "active"
        ).first()

        if not instance:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Active journey instance not found"
            )

        if not instance.current_stage_id:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Journey has no current stage"
            )

        # Get current stage
        current_stage = next(
            (s for s in instance.journey.stages if s.id == instance.current_stage_id),
            None
        )

        if not current_stage:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Current stage not found"
            )

        # Mark current stage as completed
        current_stage_status = db.query(JourneyInstanceStageStatus).filter(
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

            db.commit()
            db.refresh(instance)

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
        next_stage_status = db.query(JourneyInstanceStageStatus).filter(
            JourneyInstanceStageStatus.journey_instance_id == instance_id,
            JourneyInstanceStageStatus.stage_id == next_stage.id
        ).first()

        if next_stage_status:
            next_stage_status.status = "in_progress"
            next_stage_status.entered_at = datetime.utcnow()

        db.commit()
        db.refresh(instance)

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
                _execute_stage_actions,
                instance.id,
                next_stage.id,
                next_stage.actions,
                db
            )

        return instance

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error advancing journey stage: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to advance journey stage"
        )


# ==================== Communications ====================

@app.post(
    "/api/v1/prm/communications",
    response_model=CommunicationResponse,
    status_code=http_status.HTTP_201_CREATED,
    tags=["Communications"]
)
async def create_communication(
    comm_data: CommunicationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create and optionally send a communication

    Supports WhatsApp, SMS, Email, and other channels.
    Can be scheduled for future delivery.
    """
    try:
        # Validate patient exists
        patient = db.query(Patient).filter(
            Patient.id == comm_data.patient_id,
            Patient.tenant_id == comm_data.tenant_id
        ).first()

        if not patient:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )

        # Create communication
        communication = Communication(
            tenant_id=comm_data.tenant_id,
            patient_id=comm_data.patient_id,
            journey_instance_id=comm_data.journey_instance_id,
            channel=comm_data.channel.value,
            recipient=comm_data.recipient,
            subject=comm_data.subject,
            message=comm_data.message,
            template_name=comm_data.template_name,
            template_vars=comm_data.template_vars,
            status="pending",
            scheduled_for=comm_data.scheduled_for
        )

        db.add(communication)
        db.commit()
        db.refresh(communication)

        logger.info(
            f"Created communication {communication.id} for patient {comm_data.patient_id}"
        )

        # If not scheduled, send immediately in background
        if not comm_data.scheduled_for:
            background_tasks.add_task(
                _send_communication,
                communication.id,
                db
            )

        return communication

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating communication: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create communication"
        )


@app.get(
    "/api/v1/prm/communications",
    response_model=CommunicationListResponse,
    tags=["Communications"]
)
async def list_communications(
    patient_id: Optional[UUID] = Query(None),
    journey_instance_id: Optional[UUID] = Query(None),
    channel: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List communications with filters"""
    try:
        query = db.query(Communication)

        if patient_id:
            query = query.filter(Communication.patient_id == patient_id)

        if journey_instance_id:
            query = query.filter(Communication.journey_instance_id == journey_instance_id)

        if channel:
            query = query.filter(Communication.channel == channel.lower())

        if status:
            query = query.filter(Communication.status == http_status.lower())

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        communications = query.order_by(
            desc(Communication.created_at)
        ).offset(offset).limit(page_size).all()

        has_next = (offset + page_size) < total
        has_previous = page > 1

        return CommunicationListResponse(
            total=total,
            communications=communications,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous
        )

    except Exception as e:
        logger.error(f"Error listing communications: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list communications"
        )


# ==================== Tickets ====================

@app.post(
    "/api/v1/prm/tickets",
    response_model=TicketResponse,
    status_code=http_status.HTTP_201_CREATED,
    tags=["Tickets"]
)
async def create_ticket(
    ticket_data: TicketCreate,
    db: Session = Depends(get_db)
):
    """
    Create a support ticket

    Tickets can be linked to journey instances for contextual support.
    """
    try:
        # Validate patient exists
        patient = db.query(Patient).filter(
            Patient.id == ticket_data.patient_id,
            Patient.tenant_id == ticket_data.tenant_id
        ).first()

        if not patient:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )

        # Create ticket
        ticket = Ticket(
            tenant_id=ticket_data.tenant_id,
            patient_id=ticket_data.patient_id,
            journey_instance_id=ticket_data.journey_instance_id,
            title=ticket_data.title,
            description=ticket_data.description,
            status="open",
            priority=ticket_data.priority.value,
            category=ticket_data.category,
            assigned_to=ticket_data.assigned_to
        )

        db.add(ticket)
        db.commit()
        db.refresh(ticket)

        logger.info(f"Created ticket {ticket.id} for patient {ticket_data.patient_id}")

        # Publish event
        await publish_event(
            event_type=EventType.TICKET_CREATED,
            tenant_id=str(ticket_data.tenant_id),
            payload={
                "ticket_id": str(ticket.id),
                "patient_id": str(ticket_data.patient_id),
                "title": ticket.title,
                "priority": ticket.priority
            },
            source_service="prm-service"
        )

        return ticket

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating ticket: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create ticket"
        )


@app.get(
    "/api/v1/prm/tickets",
    response_model=TicketListResponse,
    tags=["Tickets"]
)
async def list_tickets(
    patient_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assigned_to: Optional[UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List tickets with filters"""
    try:
        query = db.query(Ticket)

        if patient_id:
            query = query.filter(Ticket.patient_id == patient_id)

        if status:
            query = query.filter(Ticket.status == http_status.lower())

        if priority:
            query = query.filter(Ticket.priority == priority.lower())

        if assigned_to:
            query = query.filter(Ticket.assigned_to == assigned_to)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        tickets = query.order_by(
            desc(Ticket.created_at)
        ).offset(offset).limit(page_size).all()

        has_next = (offset + page_size) < total
        has_previous = page > 1

        return TicketListResponse(
            total=total,
            tickets=tickets,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous
        )

    except Exception as e:
        logger.error(f"Error listing tickets: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list tickets"
        )


@app.patch(
    "/api/v1/prm/tickets/{ticket_id}",
    response_model=TicketResponse,
    tags=["Tickets"]
)
async def update_ticket(
    ticket_id: UUID,
    ticket_update: TicketUpdate,
    db: Session = Depends(get_db)
):
    """Update a ticket"""
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

        if not ticket:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )

        # Update fields
        if ticket_update.title:
            ticket.title = ticket_update.title

        if ticket_update.description:
            ticket.description = ticket_update.description

        if ticket_update.status:
            ticket.status = ticket_update.status.value
            if ticket_update.status == TicketStatus.RESOLVED:
                ticket.resolved_at = datetime.utcnow()

        if ticket_update.priority:
            ticket.priority = ticket_update.priority.value

        if ticket_update.assigned_to is not None:
            ticket.assigned_to = ticket_update.assigned_to

        if ticket_update.resolution_notes:
            ticket.resolution_notes = ticket_update.resolution_notes

        ticket.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(ticket)

        logger.info(f"Updated ticket {ticket_id}")

        return ticket

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating ticket: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update ticket"
        )


# ==================== Helper Functions ====================

async def _execute_stage_actions(
    instance_id: UUID,
    stage_id: UUID,
    actions: dict,
    db: Session
):
    """Execute actions defined in a journey stage"""
    try:
        logger.info(f"Executing actions for stage {stage_id} in instance {instance_id}")

        # Example: Send communication action
        if "send_communication" in actions:
            comm_action = actions["send_communication"]

            # Get instance to access patient info
            instance = db.query(JourneyInstance).filter(
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
                db.add(communication)
                db.commit()

                logger.info(f"Created communication {communication.id} from stage action")

    except Exception as e:
        logger.error(f"Error executing stage actions: {e}")


async def _send_communication(communication_id: UUID, db: Session):
    """Send a communication (placeholder for actual integration)"""
    try:
        communication = db.query(Communication).filter(
            Communication.id == communication_id
        ).first()

        if not communication:
            logger.error(f"Communication {communication_id} not found")
            return

        # TODO: Integrate with actual communication providers (Twilio, SendGrid, etc.)
        # For now, just mark as sent
        communication.status = "sent"
        communication.sent_at = datetime.utcnow()

        db.commit()

        logger.info(f"Sent communication {communication_id} via {communication.channel}")

        # Publish event
        await publish_event(
            event_type=EventType.COMMUNICATION_SENT,
            tenant_id=str(communication.tenant_id),
            payload={
                "communication_id": str(communication.id),
                "patient_id": str(communication.patient_id),
                "channel": communication.channel
            },
            source_service="prm-service"
        )

    except Exception as e:
        logger.error(f"Error sending communication: {e}")
        # Mark as failed
        if communication:
            communication.status = "failed"
            communication.error_message = str(e)
            db.commit()


# ==================== Startup & Shutdown ====================

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("PRM Service starting up...")

    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

    # Initialize real-time services
    try:
        await startup_realtime()
        logger.info("Real-time services initialized")
    except Exception as e:
        logger.error(f"Error initializing real-time services: {e}")

    logger.info("PRM Service ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("PRM Service shutting down...")

    try:
        await shutdown_realtime()
        logger.info("Real-time services stopped")
    except Exception as e:
        logger.error(f"Error stopping real-time services: {e}")

    logger.info("PRM Service shutdown complete")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007, reload=True)
