"""
Tickets Router
API endpoints for support ticket management
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.orm import Session
from loguru import logger

from shared.database.connection import get_db

from .schemas import (
    TicketCreate,
    TicketUpdate,
    TicketResponse,
    TicketResponse,
    TicketListResponse,
    TicketStats,
    TicketStats
)
from .service import TicketService


router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.post(
    "",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_ticket(
    ticket_data: TicketCreate,
    db: Session = Depends(get_db)
):
    """
    Create a support ticket

    Tickets can be linked to journey instances for contextual support.
    """
    service = TicketService(db)
    return await service.create_ticket(ticket_data)


@router.get("", response_model=TicketListResponse)
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
    service = TicketService(db)
    return await service.list_tickets(
        patient_id=patient_id,
        status=status,
        priority=priority,
        assigned_to=assigned_to,
        page=page,
        page_size=page_size
    )



@router.get("/stats", response_model=TicketStats)
async def get_ticket_stats(
    db: Session = Depends(get_db)
):
    """Get ticket statistics"""
    service = TicketService(db)
    return await service.get_stats()


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: UUID,
    db: Session = Depends(get_db)
):
    """Get ticket by ID"""
    service = TicketService(db)
    ticket = await service.get_ticket(ticket_id)

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    return ticket


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: UUID,
    ticket_update: TicketUpdate,
    db: Session = Depends(get_db)
):
    """Update a ticket"""
    service = TicketService(db)
    ticket = await service.update_ticket(ticket_id, ticket_update)

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    return ticket
