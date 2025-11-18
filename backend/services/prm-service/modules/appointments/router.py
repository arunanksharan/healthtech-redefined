"""
Appointments Router
API endpoints for appointment booking and management
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from loguru import logger

from shared.database.connection import get_db

from modules.appointments.schemas import (
    AppointmentBookingRequest,
    AppointmentUpdate,
    AppointmentResponse,
    SlotsAvailable,
    SlotSelectionReply,
    SlotSelectionResult,
    BookingResult,
    AppointmentListFilters
)
from modules.appointments.service import AppointmentService


router = APIRouter(prefix="/appointments", tags=["Appointments"])


# ==================== Booking Endpoints ====================

@router.post("/find-slots", response_model=SlotsAvailable)
async def find_available_slots(
    conversation_id: UUID,
    patient_phone: str,
    max_slots: int = 5,
    db: Session = Depends(get_db)
):
    """
    Find available appointment slots and present to user

    This endpoint:
    1. Extracts preferences from conversation state
    2. Finds matching practitioners
    3. Returns available slots
    4. Sends formatted message to user via WhatsApp
    """
    service = AppointmentService(db)

    slots_available = await service.present_slots_to_user(
        conversation_id=conversation_id,
        patient_phone=patient_phone,
        max_slots=max_slots
    )

    return slots_available


@router.post("/select-slot", response_model=SlotSelectionResult)
async def handle_slot_selection(
    selection: SlotSelectionReply,
    db: Session = Depends(get_db)
):
    """
    Process user's slot selection reply

    Handles:
    - Numeric selection (1, 2, 3...)
    - Text selection ("first", "second"...)
    - Rejection ("none", "no")
    - Ambiguous responses

    If selection is valid, creates confirmed appointment
    """
    service = AppointmentService(db)

    result = await service.handle_slot_reply(
        conversation_id=selection.conversation_id,
        user_text=selection.user_text
    )

    return result


# ==================== Appointment Management ====================

@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: UUID,
    db: Session = Depends(get_db)
):
    """Get appointment by ID"""
    service = AppointmentService(db)
    appointment = await service.get_appointment(appointment_id)

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    return AppointmentResponse.from_orm(appointment)


@router.patch("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: UUID,
    update_data: AppointmentUpdate,
    db: Session = Depends(get_db)
):
    """Update appointment"""
    service = AppointmentService(db)
    appointment = await service.update_appointment(appointment_id, update_data)

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    return AppointmentResponse.from_orm(appointment)


@router.post("/{appointment_id}/cancel", response_model=AppointmentResponse)
async def cancel_appointment(
    appointment_id: UUID,
    notify_patient: bool = True,
    db: Session = Depends(get_db)
):
    """Cancel appointment"""
    service = AppointmentService(db)
    appointment = await service.cancel_appointment(
        appointment_id,
        notify_patient=notify_patient
    )

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    return AppointmentResponse.from_orm(appointment)


# ==================== List/Search ====================

@router.get("", response_model=List[AppointmentResponse])
async def list_appointments(
    patient_id: UUID = None,
    practitioner_id: UUID = None,
    status: str = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List appointments with filters

    Supports:
    - Filter by patient, practitioner, status
    - Pagination
    """
    filters = AppointmentListFilters(
        patient_id=patient_id,
        practitioner_id=practitioner_id,
        status=status,
        limit=limit,
        offset=offset
    )

    query = db.query(Appointment)

    if filters.patient_id:
        query = query.filter(Appointment.patient_id == filters.patient_id)

    if filters.practitioner_id:
        query = query.filter(Appointment.practitioner_id == filters.practitioner_id)

    if filters.status:
        query = query.filter(Appointment.status == filters.status)

    if filters.start_date:
        query = query.filter(Appointment.confirmed_start >= filters.start_date)

    if filters.end_date:
        query = query.filter(Appointment.confirmed_start <= filters.end_date)

    query = query.order_by(Appointment.confirmed_start.desc())
    query = query.offset(filters.offset).limit(filters.limit)

    appointments = query.all()

    return [AppointmentResponse.from_orm(a) for a in appointments]
