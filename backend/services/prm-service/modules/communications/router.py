"""
Communications Router
API endpoints for multi-channel patient communications
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from loguru import logger

from shared.database.connection import get_db
from shared.database.models import Communication

from .schemas import (
    CommunicationCreate,
    CommunicationUpdate,
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
    comm_status: Optional[str] = Query(None, alias="status"),
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
        status=comm_status,
        page=page,
        page_size=page_size
    )


@router.get("/stats")
async def get_communication_stats(
    tenant_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get communication statistics

    Returns counts by channel and status.
    """
    query = db.query(Communication)

    if tenant_id:
        query = query.filter(Communication.tenant_id == tenant_id)

    # Total
    total = query.count()

    # By channel
    channel_counts = db.query(
        Communication.channel,
        func.count(Communication.id)
    ).group_by(Communication.channel).all()

    by_channel = {channel: count for channel, count in channel_counts}

    # By status
    status_counts = db.query(
        Communication.status,
        func.count(Communication.id)
    ).group_by(Communication.status).all()

    by_status = {s: count for s, count in status_counts}

    return {
        "total": total,
        "by_channel": by_channel,
        "by_status": by_status,
        "sent": by_status.get("sent", 0) + by_status.get("delivered", 0) + by_status.get("read", 0),
        "pending": by_status.get("pending", 0),
        "failed": by_status.get("failed", 0)
    }


@router.get("/{communication_id}", response_model=CommunicationResponse)
async def get_communication(
    communication_id: UUID,
    db: Session = Depends(get_db)
):
    """Get communication by ID"""
    communication = db.query(Communication).filter(
        Communication.id == communication_id
    ).first()

    if not communication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Communication not found"
        )

    return CommunicationResponse.model_validate(communication)


@router.patch("/{communication_id}", response_model=CommunicationResponse)
async def update_communication(
    communication_id: UUID,
    update_data: CommunicationUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a communication

    Common uses:
    - Mark as read: status="read", read_at=now
    - Mark as delivered: status="delivered", delivered_at=now
    - Mark as failed: status="failed", error_message="..."
    """
    communication = db.query(Communication).filter(
        Communication.id == communication_id
    ).first()

    if not communication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Communication not found"
        )

    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)

    for field, value in update_dict.items():
        if hasattr(communication, field):
            setattr(communication, field, value)

    communication.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(communication)

    logger.info(f"Updated communication: {communication_id}")

    return CommunicationResponse.model_validate(communication)
