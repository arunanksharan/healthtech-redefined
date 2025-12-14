"""
Appointments Router
API endpoints for appointment booking and management
"""
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_
from typing import List, Optional
from uuid import UUID, uuid4
from loguru import logger

from shared.database.connection import get_db
from shared.database.models import Appointment, TimeSlot, Patient, Practitioner, Location

from modules.appointments.schemas import (
    AppointmentBookingRequest,
    AppointmentUpdate,
    AppointmentResponse,
    SlotsAvailable,
    SlotSelectionReply,
    SlotSelectionResult,
    BookingResult,
    AppointmentListFilters,
    AppointmentStats,
    AppointmentListResponse,
    AppointmentDirectCreate,
    AppointmentDetailResponse
)
from modules.appointments.service import AppointmentService


router = APIRouter(prefix="/appointments", tags=["Appointments"])


# ==================== List & Search ====================

@router.get("", response_model=AppointmentListResponse)
async def list_appointments_paginated(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    patient_id: Optional[UUID] = Query(None, description="Filter by patient"),
    practitioner_id: Optional[UUID] = Query(None, description="Filter by practitioner"),
    location_id: Optional[UUID] = Query(None, description="Filter by location"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[date] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    List appointments with pagination and filters

    Supports filtering by:
    - Patient, practitioner, location
    - Status (booked, checked_in, completed, cancelled, no_show)
    - Date range (using time slot dates)
    """
    query = db.query(Appointment).join(TimeSlot)

    # Apply filters
    if patient_id:
        query = query.filter(Appointment.patient_id == patient_id)

    if practitioner_id:
        query = query.filter(Appointment.practitioner_id == practitioner_id)

    if location_id:
        query = query.filter(Appointment.location_id == location_id)

    if status:
        query = query.filter(Appointment.status == status)

    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        query = query.filter(TimeSlot.start_datetime >= start_datetime)

    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        query = query.filter(TimeSlot.start_datetime <= end_datetime)

    # Get total count
    total = query.count()

    # Apply pagination and ordering
    offset = (page - 1) * page_size
    appointments = query.order_by(TimeSlot.start_datetime.desc()).offset(offset).limit(page_size).all()

    return AppointmentListResponse(
        items=[AppointmentResponse.model_validate(a) for a in appointments],
        total=total,
        page=page,
        page_size=page_size,
        has_next=offset + len(appointments) < total,
        has_previous=page > 1
    )


@router.get("/today", response_model=List[AppointmentDetailResponse])
async def get_today_appointments(
    practitioner_id: Optional[UUID] = Query(None),
    location_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get today's appointments

    Returns all appointments scheduled for today.
    Optionally filter by practitioner, location, or status.
    """
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_end = datetime.combine(date.today(), datetime.max.time())

    query = db.query(Appointment).join(
        TimeSlot, Appointment.time_slot_id == TimeSlot.id
    ).options(
        joinedload(Appointment.patient),
        joinedload(Appointment.practitioner),
        joinedload(Appointment.location),
        joinedload(Appointment.time_slot)
    ).filter(
        TimeSlot.start_datetime >= today_start,
        TimeSlot.start_datetime <= today_end
    )

    if practitioner_id:
        query = query.filter(Appointment.practitioner_id == practitioner_id)

    if location_id:
        query = query.filter(Appointment.location_id == location_id)

    if status:
        query = query.filter(Appointment.status == status)

    appointments = query.order_by(TimeSlot.start_datetime.asc()).all()

    result = []
    for apt in appointments:
        patient_name = None
        if apt.patient:
            patient_name = f"{apt.patient.first_name or ''} {apt.patient.last_name or ''}".strip()

        practitioner_name = None
        if apt.practitioner:
            practitioner_name = apt.practitioner.name

        location_name = None
        if apt.location:
            location_name = apt.location.name

        scheduled_date = None
        scheduled_end = None
        if apt.time_slot:
            scheduled_date = apt.time_slot.start_datetime
            scheduled_end = apt.time_slot.end_datetime

        result.append(AppointmentDetailResponse(
            id=apt.id,
            tenant_id=apt.tenant_id,
            patient_id=apt.patient_id,
            practitioner_id=apt.practitioner_id,
            location_id=apt.location_id,
            time_slot_id=apt.time_slot_id,
            appointment_type=apt.appointment_type,
            status=apt.status,
            reason_text=apt.reason_text,
            source_channel=apt.source_channel,
            scheduled_date=scheduled_date,
            scheduled_end=scheduled_end,
            patient_name=patient_name,
            practitioner_name=practitioner_name,
            location_name=location_name,
            meta_data=apt.meta_data,
            created_at=apt.created_at,
            updated_at=apt.updated_at
        ))

    return result


@router.get("/upcoming", response_model=List[AppointmentDetailResponse])
async def get_upcoming_appointments(
    limit: int = Query(10, ge=1, le=50, description="Max results"),
    patient_id: Optional[UUID] = Query(None),
    practitioner_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get upcoming appointments

    Returns appointments scheduled for the future, ordered by date.
    """
    now = datetime.utcnow()

    query = db.query(Appointment).join(
        TimeSlot, Appointment.time_slot_id == TimeSlot.id
    ).options(
        joinedload(Appointment.patient),
        joinedload(Appointment.practitioner),
        joinedload(Appointment.location),
        joinedload(Appointment.time_slot)
    ).filter(
        TimeSlot.start_datetime >= now,
        Appointment.status.in_(["booked", "confirmed", "scheduled"])
    )

    if patient_id:
        query = query.filter(Appointment.patient_id == patient_id)

    if practitioner_id:
        query = query.filter(Appointment.practitioner_id == practitioner_id)

    appointments = query.order_by(TimeSlot.start_datetime.asc()).limit(limit).all()

    result = []
    for apt in appointments:
        patient_name = None
        if apt.patient:
            patient_name = f"{apt.patient.first_name or ''} {apt.patient.last_name or ''}".strip()

        practitioner_name = None
        if apt.practitioner:
            practitioner_name = apt.practitioner.name

        location_name = None
        if apt.location:
            location_name = apt.location.name

        scheduled_date = None
        scheduled_end = None
        if apt.time_slot:
            scheduled_date = apt.time_slot.start_datetime
            scheduled_end = apt.time_slot.end_datetime

        result.append(AppointmentDetailResponse(
            id=apt.id,
            tenant_id=apt.tenant_id,
            patient_id=apt.patient_id,
            practitioner_id=apt.practitioner_id,
            location_id=apt.location_id,
            time_slot_id=apt.time_slot_id,
            appointment_type=apt.appointment_type,
            status=apt.status,
            reason_text=apt.reason_text,
            source_channel=apt.source_channel,
            scheduled_date=scheduled_date,
            scheduled_end=scheduled_end,
            patient_name=patient_name,
            practitioner_name=practitioner_name,
            location_name=location_name,
            meta_data=apt.meta_data,
            created_at=apt.created_at,
            updated_at=apt.updated_at
        ))

    return result


@router.get("/stats", response_model=AppointmentStats)
async def get_appointment_stats(
    tenant_id: Optional[UUID] = Query(None),
    start_date: Optional[date] = Query(None, description="Stats from date"),
    end_date: Optional[date] = Query(None, description="Stats to date"),
    db: Session = Depends(get_db)
):
    """
    Get appointment statistics

    Returns aggregated appointment counts:
    - Total, today, upcoming, completed, cancelled, no_show
    - Breakdown by status and type
    """
    query = db.query(Appointment).join(TimeSlot)

    if tenant_id:
        query = query.filter(Appointment.tenant_id == tenant_id)

    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        query = query.filter(TimeSlot.start_datetime >= start_datetime)

    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        query = query.filter(TimeSlot.start_datetime <= end_datetime)

    # Total
    total = query.count()

    # Today
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_end = datetime.combine(date.today(), datetime.max.time())
    today_count = query.filter(
        TimeSlot.start_datetime >= today_start,
        TimeSlot.start_datetime <= today_end
    ).count()

    # Upcoming
    now = datetime.utcnow()
    upcoming_count = query.filter(
        TimeSlot.start_datetime >= now,
        Appointment.status.in_(["booked", "confirmed", "scheduled"])
    ).count()

    # By status
    status_counts = db.query(
        Appointment.status,
        func.count(Appointment.id)
    ).group_by(Appointment.status).all()

    by_status = {status: count for status, count in status_counts}

    # By type
    type_counts = db.query(
        Appointment.appointment_type,
        func.count(Appointment.id)
    ).filter(
        Appointment.appointment_type.isnot(None)
    ).group_by(Appointment.appointment_type).all()

    by_type = {apt_type or "unknown": count for apt_type, count in type_counts}

    return AppointmentStats(
        total=total,
        today=today_count,
        upcoming=upcoming_count,
        completed=by_status.get("completed", 0),
        cancelled=by_status.get("cancelled", 0),
        no_show=by_status.get("no_show", 0),
        by_status=by_status,
        by_type=by_type
    )


# ==================== Direct Appointment Creation ====================

@router.post("", response_model=AppointmentDetailResponse, status_code=201)
async def create_appointment_direct(
    appointment_data: AppointmentDirectCreate,
    db: Session = Depends(get_db)
):
    """
    Create appointment directly (without conversation flow)

    Use this endpoint for:
    - Web portal bookings
    - Admin/staff bookings
    - Walk-in registrations

    Requires a valid time_slot_id. The time slot must be available.
    """
    # Verify time slot exists and is available
    time_slot = db.query(TimeSlot).filter(
        TimeSlot.id == appointment_data.time_slot_id
    ).first()

    if not time_slot:
        raise HTTPException(status_code=404, detail="Time slot not found")

    if time_slot.status == "full":
        raise HTTPException(status_code=400, detail="Time slot is fully booked")

    if time_slot.booked_count >= time_slot.capacity:
        raise HTTPException(status_code=400, detail="Time slot is at capacity")

    # Verify patient exists
    patient = db.query(Patient).filter(
        Patient.id == appointment_data.patient_id
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Verify practitioner exists
    practitioner = db.query(Practitioner).filter(
        Practitioner.id == appointment_data.practitioner_id
    ).first()

    if not practitioner:
        raise HTTPException(status_code=404, detail="Practitioner not found")

    # Verify location exists
    location = db.query(Location).filter(
        Location.id == appointment_data.location_id
    ).first()

    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    # Create appointment
    appointment = Appointment(
        id=uuid4(),
        tenant_id=appointment_data.tenant_id,
        patient_id=appointment_data.patient_id,
        practitioner_id=appointment_data.practitioner_id,
        location_id=appointment_data.location_id,
        time_slot_id=appointment_data.time_slot_id,
        appointment_type=appointment_data.appointment_type,
        status="booked",
        reason_text=appointment_data.reason_text,
        source_channel=appointment_data.source_channel,
        meta_data=appointment_data.meta_data or {},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    # Update time slot booked count
    time_slot.booked_count += 1
    if time_slot.booked_count >= time_slot.capacity:
        time_slot.status = "full"

    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    logger.info(f"Created appointment: {appointment.id} for patient {patient.id}")

    # Build response with related data
    patient_name = f"{patient.first_name or ''} {patient.last_name or ''}".strip()

    return AppointmentDetailResponse(
        id=appointment.id,
        tenant_id=appointment.tenant_id,
        patient_id=appointment.patient_id,
        practitioner_id=appointment.practitioner_id,
        location_id=appointment.location_id,
        time_slot_id=appointment.time_slot_id,
        appointment_type=appointment.appointment_type,
        status=appointment.status,
        reason_text=appointment.reason_text,
        source_channel=appointment.source_channel,
        scheduled_date=time_slot.start_datetime,
        scheduled_end=time_slot.end_datetime,
        patient_name=patient_name,
        practitioner_name=practitioner.name,
        location_name=location.name,
        meta_data=appointment.meta_data,
        created_at=appointment.created_at,
        updated_at=appointment.updated_at
    )


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


@router.put("/{appointment_id}/cancel", response_model=AppointmentResponse)
async def cancel_appointment_put(
    appointment_id: UUID,
    notify_patient: bool = True,
    db: Session = Depends(get_db)
):
    """
    Cancel appointment (PUT variant)

    Alternative method for cancellation to support different client implementations.
    Functionally identical to POST /appointments/{id}/cancel.
    """
    service = AppointmentService(db)
    appointment = await service.cancel_appointment(
        appointment_id,
        notify_patient=notify_patient
    )

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    return AppointmentResponse.from_orm(appointment)


# ==================== Conflict Checking ====================

@router.get("/conflicts")
async def check_appointment_conflicts(
    practitioner_id: UUID = Query(..., description="Practitioner ID"),
    start_time: datetime = Query(..., description="Proposed start time"),
    end_time: datetime = Query(..., description="Proposed end time"),
    exclude_appointment_id: Optional[UUID] = Query(None, description="Exclude this appointment (for rescheduling)"),
    db: Session = Depends(get_db)
):
    """
    Check for scheduling conflicts

    Pre-flight check to verify a practitioner is available for a time slot
    before creating or updating an appointment.

    Returns:
    - has_conflict: boolean indicating if there's a scheduling conflict
    - conflicting_appointments: list of overlapping appointments if any
    """
    # Find overlapping appointments for the practitioner
    query = db.query(Appointment).join(
        TimeSlot, Appointment.time_slot_id == TimeSlot.id
    ).filter(
        Appointment.practitioner_id == practitioner_id,
        Appointment.status.in_(["booked", "confirmed", "scheduled", "checked_in"]),
        # Check for overlap: existing slot overlaps with proposed time
        TimeSlot.start_datetime < end_time,
        TimeSlot.end_datetime > start_time
    )

    # Exclude current appointment when rescheduling
    if exclude_appointment_id:
        query = query.filter(Appointment.id != exclude_appointment_id)

    conflicting = query.all()

    conflicts = []
    for apt in conflicting:
        time_slot = db.query(TimeSlot).filter(TimeSlot.id == apt.time_slot_id).first()
        conflicts.append({
            "appointment_id": str(apt.id),
            "patient_id": str(apt.patient_id),
            "status": apt.status,
            "start_time": time_slot.start_datetime.isoformat() if time_slot else None,
            "end_time": time_slot.end_datetime.isoformat() if time_slot else None
        })

    return {
        "has_conflict": len(conflicts) > 0,
        "conflict_count": len(conflicts),
        "conflicting_appointments": conflicts
    }


