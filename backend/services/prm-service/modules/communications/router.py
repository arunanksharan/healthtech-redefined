"""
Communications Router
API endpoints for multi-channel patient communications
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query, status, BackgroundTasks
from sqlalchemy.orm import Session
from loguru import logger

from shared.database.connection import get_db

from .schemas import (
    CommunicationCreate,
    CommunicationResponse,
    CommunicationListResponse
)
from .service import CommunicationService


router = APIRouter(prefix="/communications", tags=["Communications"])


@router.post(
    "",
    response_model=CommunicationResponse,
    status_code=status.HTTP_201_CREATED
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
    service = CommunicationService(db)
    return await service.create_communication(comm_data, background_tasks)


@router.get("", response_model=CommunicationListResponse)
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
    service = CommunicationService(db)
    return await service.list_communications(
        patient_id=patient_id,
        journey_instance_id=journey_instance_id,
        channel=channel,
        status=status,
        page=page,
        page_size=page_size
    )
