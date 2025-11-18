"""
Communications Service
Business logic for multi-channel communications
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
from loguru import logger

from shared.database.models import Communication, Patient
from shared.events.publisher import publish_event
from shared.events.types import EventType

from .schemas import (
    CommunicationCreate,
    CommunicationListResponse
)


class CommunicationService:
    """Service class for communication operations"""

    def __init__(self, db: Session):
        self.db = db

    async def create_communication(
        self,
        comm_data: CommunicationCreate,
        background_tasks: BackgroundTasks
    ) -> Communication:
        """Create and optionally send a communication"""
        try:
            # Validate patient exists
            patient = self.db.query(Patient).filter(
                Patient.id == comm_data.patient_id,
                Patient.tenant_id == comm_data.tenant_id
            ).first()

            if not patient:
                raise ValueError("Patient not found")

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

            self.db.add(communication)
            self.db.commit()
            self.db.refresh(communication)

            logger.info(
                f"Created communication {communication.id} for patient {comm_data.patient_id}"
            )

            # If not scheduled, send immediately in background
            if not comm_data.scheduled_for:
                background_tasks.add_task(
                    self._send_communication,
                    communication.id
                )

            return communication

        except ValueError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating communication: {e}")
            raise

    async def list_communications(
        self,
        patient_id: Optional[UUID] = None,
        journey_instance_id: Optional[UUID] = None,
        channel: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> CommunicationListResponse:
        """List communications with filters"""
        try:
            query = self.db.query(Communication)

            if patient_id:
                query = query.filter(Communication.patient_id == patient_id)

            if journey_instance_id:
                query = query.filter(Communication.journey_instance_id == journey_instance_id)

            if channel:
                query = query.filter(Communication.channel == channel.lower())

            if status:
                query = query.filter(Communication.status == status.lower())

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
            raise

    async def _send_communication(self, communication_id: UUID):
        """Send a communication (placeholder for actual integration)"""
        try:
            communication = self.db.query(Communication).filter(
                Communication.id == communication_id
            ).first()

            if not communication:
                logger.error(f"Communication {communication_id} not found")
                return

            # TODO: Integrate with actual communication providers (Twilio, SendGrid, etc.)
            # For now, just mark as sent
            communication.status = "sent"
            communication.sent_at = datetime.utcnow()

            self.db.commit()

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
                self.db.commit()
