"""
Tickets Service
Business logic for support ticket management
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import desc
from loguru import logger

from shared.database.models import Ticket, Patient
from shared.events.publisher import publish_event
from shared.events.types import EventType

from .schemas import (
    TicketCreate,
    TicketUpdate,
    TicketListResponse,
    TicketStatus
)


class TicketService:
    """Service class for ticket operations"""

    def __init__(self, db: Session):
        self.db = db

    async def create_ticket(self, ticket_data: TicketCreate) -> Ticket:
        """Create a support ticket"""
        try:
            # Validate patient exists
            patient = self.db.query(Patient).filter(
                Patient.id == ticket_data.patient_id,
                Patient.tenant_id == ticket_data.tenant_id
            ).first()

            if not patient:
                raise ValueError("Patient not found")

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

            self.db.add(ticket)
            self.db.commit()
            self.db.refresh(ticket)

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

        except ValueError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating ticket: {e}")
            raise

    async def list_tickets(
        self,
        patient_id: Optional[UUID] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_to: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20
    ) -> TicketListResponse:
        """List tickets with filters"""
        try:
            query = self.db.query(Ticket)

            if patient_id:
                query = query.filter(Ticket.patient_id == patient_id)

            if status:
                query = query.filter(Ticket.status == status.lower())

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
            raise

    async def get_ticket(self, ticket_id: UUID) -> Optional[Ticket]:
        """Get ticket by ID"""
        try:
            ticket = self.db.query(Ticket).filter(Ticket.id == ticket_id).first()
            return ticket

        except Exception as e:
            logger.error(f"Error retrieving ticket: {e}")
            raise

    async def update_ticket(
        self,
        ticket_id: UUID,
        ticket_update: TicketUpdate
    ) -> Optional[Ticket]:
        """Update a ticket"""
        try:
            ticket = self.db.query(Ticket).filter(Ticket.id == ticket_id).first()

            if not ticket:
                return None

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

            self.db.commit()
            self.db.refresh(ticket)

            logger.info(f"Updated ticket {ticket_id}")

            return ticket

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating ticket: {e}")
            raise
