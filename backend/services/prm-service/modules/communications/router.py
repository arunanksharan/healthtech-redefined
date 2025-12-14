"""
Communications Router
API endpoints for multi-channel patient communications
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
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


# ==================== Templates ====================

@router.get("/templates")
async def list_communication_templates(
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    channel: Optional[str] = Query(None, description="Filter by channel (whatsapp, sms, email)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db)
):
    """
    List available communication templates

    Returns templates for quick replies and automated messages.
    Templates are pre-approved message formats for different channels.
    """
    # Default templates - in production these would come from a templates table
    templates = [
        {
            "id": "apt_reminder",
            "name": "Appointment Reminder",
            "channel": "whatsapp",
            "category": "appointment",
            "subject": "Appointment Reminder",
            "body": "Hi {{patient_name}}, this is a reminder for your appointment on {{appointment_date}} at {{appointment_time}} with {{practitioner_name}}.",
            "variables": ["patient_name", "appointment_date", "appointment_time", "practitioner_name"]
        },
        {
            "id": "apt_confirmation",
            "name": "Appointment Confirmation",
            "channel": "whatsapp",
            "category": "appointment",
            "subject": "Appointment Confirmed",
            "body": "Your appointment has been confirmed for {{appointment_date}} at {{appointment_time}}. Location: {{location_name}}.",
            "variables": ["appointment_date", "appointment_time", "location_name"]
        },
        {
            "id": "apt_cancelled",
            "name": "Appointment Cancelled",
            "channel": "whatsapp",
            "category": "appointment",
            "subject": "Appointment Cancelled",
            "body": "Your appointment on {{appointment_date}} has been cancelled. Please contact us to reschedule.",
            "variables": ["appointment_date"]
        },
        {
            "id": "pre_visit",
            "name": "Pre-Visit Instructions",
            "channel": "whatsapp",
            "category": "instructions",
            "subject": "Pre-Visit Instructions",
            "body": "Hi {{patient_name}}, please remember to {{instructions}} before your visit on {{appointment_date}}.",
            "variables": ["patient_name", "instructions", "appointment_date"]
        },
        {
            "id": "post_visit",
            "name": "Post-Visit Follow-up",
            "channel": "whatsapp",
            "category": "follow_up",
            "subject": "Follow-up After Your Visit",
            "body": "Hi {{patient_name}}, thank you for visiting us. {{follow_up_message}}",
            "variables": ["patient_name", "follow_up_message"]
        },
        {
            "id": "lab_results",
            "name": "Lab Results Available",
            "channel": "sms",
            "category": "results",
            "subject": "Lab Results Ready",
            "body": "Your lab results are now available. Please log in to the patient portal or contact our office.",
            "variables": []
        },
        {
            "id": "prescription_ready",
            "name": "Prescription Ready",
            "channel": "sms",
            "category": "pharmacy",
            "subject": "Prescription Ready",
            "body": "Your prescription is ready for pickup at {{pharmacy_name}}.",
            "variables": ["pharmacy_name"]
        },
        {
            "id": "payment_reminder",
            "name": "Payment Reminder",
            "channel": "email",
            "category": "billing",
            "subject": "Payment Reminder",
            "body": "This is a reminder that you have an outstanding balance of {{amount}}. Please contact our billing department.",
            "variables": ["amount"]
        },
        {
            "id": "general_message",
            "name": "General Message",
            "channel": "whatsapp",
            "category": "general",
            "subject": "Message from {{clinic_name}}",
            "body": "{{message}}",
            "variables": ["clinic_name", "message"]
        }
    ]

    # Filter templates
    filtered = templates

    if channel:
        filtered = [t for t in filtered if t["channel"] == channel.lower()]

    if category:
        filtered = [t for t in filtered if t["category"] == category.lower()]

    return {
        "templates": filtered,
        "total": len(filtered),
        "channels": ["whatsapp", "sms", "email"],
        "categories": ["appointment", "instructions", "follow_up", "results", "pharmacy", "billing", "general"]
    }


# ==================== Search ====================

@router.get("/search", response_model=CommunicationListResponse)
async def search_communications(
    query: str = Query(..., min_length=2, description="Search query"),
    patient_id: Optional[UUID] = Query(None, description="Filter by patient"),
    channel: Optional[str] = Query(None, description="Filter by channel"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Server-side search for communications

    Searches across message content, subject, and recipient.
    More efficient than client-side filtering for large datasets.
    """
    search_term = f"%{query}%"

    db_query = db.query(Communication).filter(
        or_(
            Communication.message.ilike(search_term),
            Communication.subject.ilike(search_term),
            Communication.recipient.ilike(search_term)
        )
    )

    # Apply additional filters
    if patient_id:
        db_query = db_query.filter(Communication.patient_id == patient_id)

    if channel:
        db_query = db_query.filter(Communication.channel == channel.lower())

    if date_from:
        db_query = db_query.filter(Communication.created_at >= date_from)

    if date_to:
        db_query = db_query.filter(Communication.created_at <= date_to)

    # Get total count
    total = db_query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    communications = db_query.order_by(
        Communication.created_at.desc()
    ).offset(offset).limit(page_size).all()

    return CommunicationListResponse(
        items=[CommunicationResponse.model_validate(c) for c in communications],
        total=total,
        page=page,
        page_size=page_size,
        has_next=offset + len(communications) < total,
        has_previous=page > 1
    )


# ==================== Mark as Read ====================

@router.patch("/{communication_id}/read", response_model=CommunicationResponse)
async def mark_communication_read(
    communication_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Mark a communication as read

    Convenience endpoint for marking a message as read.
    Sets status to 'read' and read_at to current time.
    """
    communication = db.query(Communication).filter(
        Communication.id == communication_id
    ).first()

    if not communication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Communication not found"
        )

    communication.status = "read"
    communication.read_at = datetime.utcnow()
    communication.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(communication)

    logger.info(f"Marked communication as read: {communication_id}")

    return CommunicationResponse.model_validate(communication)


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


# ==================== Delete Communication ====================

@router.delete("/{communication_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_communication(
    communication_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a communication

    Permanently removes a communication record from the system.
    Note: For audit purposes, consider archiving instead of deleting.
    """
    communication = db.query(Communication).filter(
        Communication.id == communication_id
    ).first()

    if not communication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Communication not found"
        )

    db.delete(communication)
    db.commit()

    logger.info(f"Deleted communication: {communication_id}")

    return None
