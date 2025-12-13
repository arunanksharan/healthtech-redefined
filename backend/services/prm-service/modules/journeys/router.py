"""
Journey Management Router
API endpoints for journey orchestration
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query, status, BackgroundTasks
from sqlalchemy.orm import Session
from loguru import logger

from shared.database.connection import get_db
from shared.events.publisher import publish_event
from shared.events.types import EventType

from .schemas import (
    JourneyCreate, JourneyUpdate, JourneyResponse, JourneyListResponse,
    JourneyStageCreate, JourneyStageUpdate, JourneyStageResponse,
    JourneyInstanceCreate, JourneyInstanceResponse,
    JourneyInstanceListResponse, JourneyInstanceWithStages,
    AdvanceStageRequest
)
from .service import JourneyService


router = APIRouter(prefix="/journeys", tags=["Journeys"])


# ==================== Journey Definitions ====================

@router.post(
    "",
    response_model=JourneyResponse,
    status_code=status.HTTP_201_CREATED
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
    service = JourneyService(db)
    return await service.create_journey(journey_data)


@router.get("", response_model=JourneyListResponse)
async def list_journeys(
    tenant_id: Optional[UUID] = Query(None),
    journey_type: Optional[str] = Query(None),
    is_default: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List journey definitions with filters"""
    service = JourneyService(db)
    return await service.list_journeys(
        tenant_id=tenant_id,
        journey_type=journey_type,
        is_default=is_default,
        page=page,
        page_size=page_size
    )


@router.get("/{journey_id}", response_model=JourneyResponse)
async def get_journey(
    journey_id: UUID,
    db: Session = Depends(get_db)
):
    """Get journey definition with stages"""
    service = JourneyService(db)
    journey = await service.get_journey(journey_id)

    if not journey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Journey not found"
        )

    return journey


@router.patch("/{journey_id}", response_model=JourneyResponse)
async def update_journey(
    journey_id: UUID,
    journey_update: JourneyUpdate,
    db: Session = Depends(get_db)
):
    """Update journey definition"""
    service = JourneyService(db)
    journey = await service.update_journey(journey_id, journey_update)

    if not journey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Journey not found"
        )

    return journey


# ==================== Journey Stages ====================

@router.post(
    "/{journey_id}/stages",
    response_model=JourneyStageResponse,
    status_code=status.HTTP_201_CREATED
)
async def add_journey_stage(
    journey_id: UUID,
    stage_data: JourneyStageCreate,
    db: Session = Depends(get_db)
):
    """Add a stage to a journey"""
    service = JourneyService(db)
    stage = await service.add_stage(journey_id, stage_data)

    if not stage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Journey not found"
        )

    return stage


@router.patch(
    "/{journey_id}/stages/{stage_id}",
    response_model=JourneyStageResponse
)
async def update_journey_stage(
    journey_id: UUID,
    stage_id: UUID,
    stage_update: JourneyStageUpdate,
    db: Session = Depends(get_db)
):
    """Update a journey stage"""
    service = JourneyService(db)
    stage = await service.update_stage(journey_id, stage_id, stage_update)

    if not stage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Journey stage not found"
        )

    return stage


# ==================== Journey Instances ====================

@router.post(
    "/instances",
    response_model=JourneyInstanceResponse,
    status_code=status.HTTP_201_CREATED
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
    service = JourneyService(db)
    instance = await service.create_instance(instance_data, background_tasks)

    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Journey or patient not found"
        )

    return instance


@router.get("/instances", response_model=JourneyInstanceListResponse)
async def list_journey_instances(
    patient_id: Optional[UUID] = Query(None),
    journey_id: Optional[UUID] = Query(None),
    instance_status: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List journey instances with filters"""
    service = JourneyService(db)
    return await service.list_instances(
        patient_id=patient_id,
        journey_id=journey_id,
        status=instance_status,
        page=page,
        page_size=page_size
    )


@router.get("/instances/stats")
async def get_journey_instance_stats(
    tenant_id: Optional[UUID] = Query(None),
    journey_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get journey instance statistics

    Returns counts by status and journey type.
    Used for dashboard "Active Journeys" card.
    """
    from shared.database.models import JourneyInstance, Journey
    from sqlalchemy import func

    query = db.query(JourneyInstance)

    if tenant_id:
        query = query.filter(JourneyInstance.tenant_id == tenant_id)

    if journey_id:
        query = query.filter(JourneyInstance.journey_id == journey_id)

    # Total
    total = query.count()

    # Active count
    active = query.filter(JourneyInstance.status == "active").count()

    # Completed count
    completed = query.filter(JourneyInstance.status == "completed").count()

    # Cancelled count
    cancelled = query.filter(JourneyInstance.status == "cancelled").count()

    # By status
    status_counts = db.query(
        JourneyInstance.status,
        func.count(JourneyInstance.id)
    ).group_by(JourneyInstance.status).all()

    by_status = {s: count for s, count in status_counts}

    # By journey
    journey_counts = db.query(
        Journey.name,
        func.count(JourneyInstance.id)
    ).join(
        Journey, JourneyInstance.journey_id == Journey.id
    ).group_by(Journey.name).all()

    by_journey = {name: count for name, count in journey_counts}

    return {
        "total": total,
        "active": active,
        "completed": completed,
        "cancelled": cancelled,
        "by_status": by_status,
        "by_journey": by_journey
    }


@router.get("/instances/{instance_id}", response_model=JourneyInstanceWithStages)
async def get_journey_instance(
    instance_id: UUID,
    db: Session = Depends(get_db)
):
    """Get journey instance with stage statuses"""
    service = JourneyService(db)
    instance = await service.get_instance_with_stages(instance_id)

    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Journey instance not found"
        )

    return instance


@router.post("/instances/{instance_id}/advance", response_model=JourneyInstanceResponse)
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
    service = JourneyService(db)
    instance = await service.advance_stage(instance_id, advance_request, background_tasks)

    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active journey instance not found"
        )

    return instance
