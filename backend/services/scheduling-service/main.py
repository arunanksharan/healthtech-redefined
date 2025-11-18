"""
Scheduling Service - Provider Schedules, Slots, and Appointments
Manages OPD appointment scheduling and availability
"""
import os
import sys
from datetime import datetime, date, time, timedelta
from typing import List, Optional
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from loguru import logger

from shared.database.connection import get_db, engine
from shared.database.models import (
    Base, ProviderSchedule, TimeSlot, Appointment,
    Patient, Practitioner, Location
)
from shared.events.publisher import publish_event
from shared.events.types import EventType

from .schemas import (
    ProviderScheduleCreate,
    ProviderScheduleUpdate,
    ProviderScheduleResponse,
    SlotMaterializeRequest,
    SlotMaterializeResponse,
    TimeSlotResponse,
    TimeSlotListResponse,
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
    AppointmentListResponse,
    AppointmentWithDetails,
    AppointmentCheckInRequest,
    AppointmentStatusUpdate
)

# Initialize FastAPI app
app = FastAPI(
    title="Scheduling Service",
    description="Provider schedules, slots, and appointment management",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Health Check ====================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "scheduling-service",
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== Provider Schedule Management ====================

@app.post(
    "/api/v1/scheduling/schedules",
    response_model=ProviderScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Provider Schedules"]
)
async def create_provider_schedule(
    schedule_data: ProviderScheduleCreate,
    db: Session = Depends(get_db)
):
    """
    Create a recurring provider schedule template

    Defines when a practitioner is available at a specific location.
    Slots can then be materialized from this template.
    """
    try:
        # Validate practitioner exists
        practitioner = db.query(Practitioner).filter(
            Practitioner.id == schedule_data.practitioner_id,
            Practitioner.tenant_id == schedule_data.tenant_id
        ).first()

        if not practitioner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Practitioner not found"
            )

        # Validate location exists
        location = db.query(Location).filter(
            Location.id == schedule_data.location_id,
            Location.tenant_id == schedule_data.tenant_id
        ).first()

        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Location not found"
            )

        # Create schedule
        schedule = ProviderSchedule(
            tenant_id=schedule_data.tenant_id,
            practitioner_id=schedule_data.practitioner_id,
            location_id=schedule_data.location_id,
            specialty_code=schedule_data.specialty_code,
            valid_from=schedule_data.valid_from,
            valid_to=schedule_data.valid_to,
            day_of_week=schedule_data.day_of_week,
            start_time=schedule_data.start_time,
            end_time=schedule_data.end_time,
            slot_duration_minutes=schedule_data.slot_duration_minutes,
            max_patients_per_slot=schedule_data.max_patients_per_slot
        )

        db.add(schedule)
        db.commit()
        db.refresh(schedule)

        logger.info(
            f"Created schedule {schedule.id} for practitioner {schedule_data.practitioner_id}"
        )

        return schedule

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create schedule: {str(e)}"
        )


@app.get(
    "/api/v1/scheduling/schedules",
    response_model=List[ProviderScheduleResponse],
    tags=["Provider Schedules"]
)
async def list_provider_schedules(
    practitioner_id: Optional[UUID] = Query(None),
    location_id: Optional[UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List provider schedules with filters"""
    try:
        query = db.query(ProviderSchedule)

        if practitioner_id:
            query = query.filter(ProviderSchedule.practitioner_id == practitioner_id)

        if location_id:
            query = query.filter(ProviderSchedule.location_id == location_id)

        if is_active is not None:
            query = query.filter(ProviderSchedule.is_active == is_active)

        schedules = query.order_by(
            ProviderSchedule.day_of_week,
            ProviderSchedule.start_time
        ).all()

        return schedules

    except Exception as e:
        logger.error(f"Error listing schedules: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list schedules"
        )


@app.get(
    "/api/v1/scheduling/schedules/{schedule_id}",
    response_model=ProviderScheduleResponse,
    tags=["Provider Schedules"]
)
async def get_provider_schedule(
    schedule_id: UUID,
    db: Session = Depends(get_db)
):
    """Get provider schedule by ID"""
    try:
        schedule = db.query(ProviderSchedule).filter(
            ProviderSchedule.id == schedule_id
        ).first()

        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found"
            )

        return schedule

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve schedule"
        )


@app.patch(
    "/api/v1/scheduling/schedules/{schedule_id}",
    response_model=ProviderScheduleResponse,
    tags=["Provider Schedules"]
)
async def update_provider_schedule(
    schedule_id: UUID,
    schedule_update: ProviderScheduleUpdate,
    db: Session = Depends(get_db)
):
    """Update provider schedule"""
    try:
        schedule = db.query(ProviderSchedule).filter(
            ProviderSchedule.id == schedule_id
        ).first()

        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found"
            )

        # Update fields
        if schedule_update.valid_to is not None:
            schedule.valid_to = schedule_update.valid_to

        if schedule_update.slot_duration_minutes is not None:
            schedule.slot_duration_minutes = schedule_update.slot_duration_minutes

        if schedule_update.max_patients_per_slot is not None:
            schedule.max_patients_per_slot = schedule_update.max_patients_per_slot

        if schedule_update.is_active is not None:
            schedule.is_active = schedule_update.is_active

        schedule.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(schedule)

        logger.info(f"Updated schedule {schedule_id}")

        return schedule

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update schedule"
        )


# ==================== Slot Materialization ====================

@app.post(
    "/api/v1/scheduling/schedules/{schedule_id}/materialize",
    response_model=SlotMaterializeResponse,
    tags=["Slots"]
)
async def materialize_slots(
    schedule_id: UUID,
    materialize_request: SlotMaterializeRequest,
    db: Session = Depends(get_db)
):
    """
    Materialize time slots from a schedule template for a date range

    Generates individual TimeSlot records based on the recurring schedule.
    """
    try:
        # Get schedule
        schedule = db.query(ProviderSchedule).filter(
            ProviderSchedule.id == schedule_id,
            ProviderSchedule.is_active == True
        ).first()

        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active schedule not found"
            )

        slots_created = 0
        current_date = materialize_request.from_date

        while current_date <= materialize_request.to_date:
            # Check if date is within schedule validity
            if current_date < schedule.valid_from:
                current_date += timedelta(days=1)
                continue

            if schedule.valid_to and current_date > schedule.valid_to:
                break

            # Check if day matches schedule
            day_of_week = current_date.isoweekday()  # 1=Mon, 7=Sun
            if day_of_week != schedule.day_of_week:
                current_date += timedelta(days=1)
                continue

            # Generate slots for this day
            current_time = schedule.start_time
            while current_time < schedule.end_time:
                # Calculate slot end time
                slot_end_time = (
                    datetime.combine(date.min, current_time) +
                    timedelta(minutes=schedule.slot_duration_minutes)
                ).time()

                if slot_end_time > schedule.end_time:
                    break

                # Create start and end datetimes
                start_datetime = datetime.combine(current_date, current_time)
                end_datetime = datetime.combine(current_date, slot_end_time)

                # Check if slot already exists
                existing_slot = db.query(TimeSlot).filter(
                    TimeSlot.schedule_id == schedule_id,
                    TimeSlot.start_datetime == start_datetime
                ).first()

                if not existing_slot:
                    # Create new slot
                    slot = TimeSlot(
                        tenant_id=schedule.tenant_id,
                        practitioner_id=schedule.practitioner_id,
                        location_id=schedule.location_id,
                        schedule_id=schedule.id,
                        start_datetime=start_datetime,
                        end_datetime=end_datetime,
                        capacity=schedule.max_patients_per_slot,
                        booked_count=0,
                        status="available"
                    )
                    db.add(slot)
                    slots_created += 1

                # Move to next slot
                current_time = slot_end_time

            current_date += timedelta(days=1)

        db.commit()

        logger.info(
            f"Materialized {slots_created} slots for schedule {schedule_id}"
        )

        return SlotMaterializeResponse(
            schedule_id=schedule_id,
            slots_created=slots_created,
            from_date=materialize_request.from_date,
            to_date=materialize_request.to_date,
            message=f"Successfully created {slots_created} slots"
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error materializing slots: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to materialize slots: {str(e)}"
        )


@app.get(
    "/api/v1/scheduling/slots",
    response_model=TimeSlotListResponse,
    tags=["Slots"]
)
async def search_available_slots(
    practitioner_id: Optional[UUID] = Query(None),
    location_id: Optional[UUID] = Query(None),
    from_datetime: Optional[datetime] = Query(None),
    to_datetime: Optional[datetime] = Query(None),
    status: str = Query("available"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search available time slots

    Find slots that match criteria and are available for booking.
    """
    try:
        query = db.query(TimeSlot)

        # Apply filters
        if practitioner_id:
            query = query.filter(TimeSlot.practitioner_id == practitioner_id)

        if location_id:
            query = query.filter(TimeSlot.location_id == location_id)

        if from_datetime:
            query = query.filter(TimeSlot.start_datetime >= from_datetime)

        if to_datetime:
            query = query.filter(TimeSlot.start_datetime <= to_datetime)

        if status:
            query = query.filter(TimeSlot.status == status.lower())

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        slots = query.order_by(
            TimeSlot.start_datetime
        ).offset(offset).limit(page_size).all()

        has_next = (offset + page_size) < total
        has_previous = page > 1

        return TimeSlotListResponse(
            total=total,
            slots=slots,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous
        )

    except Exception as e:
        logger.error(f"Error searching slots: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search slots"
        )


# ==================== Appointment Management ====================

@app.post(
    "/api/v1/scheduling/appointments",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Appointments"]
)
async def create_appointment(
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new appointment

    Books a patient into a specific time slot with capacity validation.
    """
    try:
        # Validate patient exists
        patient = db.query(Patient).filter(
            Patient.id == appointment_data.patient_id,
            Patient.tenant_id == appointment_data.tenant_id
        ).first()

        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )

        # Get time slot and validate availability
        time_slot = db.query(TimeSlot).filter(
            TimeSlot.id == appointment_data.time_slot_id,
            TimeSlot.tenant_id == appointment_data.tenant_id
        ).first()

        if not time_slot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time slot not found"
            )

        if time_slot.status != "available":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Time slot is not available (status: {time_slot.status})"
            )

        if time_slot.booked_count >= time_slot.capacity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Time slot is full"
            )

        # Check for duplicate appointments
        existing_appointment = db.query(Appointment).filter(
            Appointment.patient_id == appointment_data.patient_id,
            Appointment.time_slot_id == appointment_data.time_slot_id,
            Appointment.status.in_(["booked", "checked_in"])
        ).first()

        if existing_appointment:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Patient already has an appointment in this slot"
            )

        # Create appointment
        appointment = Appointment(
            tenant_id=appointment_data.tenant_id,
            patient_id=appointment_data.patient_id,
            practitioner_id=appointment_data.practitioner_id,
            location_id=appointment_data.location_id,
            time_slot_id=appointment_data.time_slot_id,
            appointment_type=appointment_data.appointment_type,
            status="booked",
            reason_text=appointment_data.reason_text,
            source_channel=appointment_data.source_channel,
            metadata=appointment_data.metadata or {}
        )

        db.add(appointment)

        # Update slot booked count
        time_slot.booked_count += 1
        if time_slot.booked_count >= time_slot.capacity:
            time_slot.status = "full"

        db.commit()
        db.refresh(appointment)

        logger.info(
            f"Created appointment {appointment.id} for patient {appointment_data.patient_id}"
        )

        # Publish event
        await publish_event(
            event_type=EventType.APPOINTMENT_CREATED,
            tenant_id=str(appointment_data.tenant_id),
            payload={
                "appointment_id": str(appointment.id),
                "patient_id": str(appointment_data.patient_id),
                "practitioner_id": str(appointment_data.practitioner_id),
                "appointment_type": appointment_data.appointment_type,
                "start_datetime": time_slot.start_datetime.isoformat(),
                "specialty_code": time_slot.schedule.specialty_code if hasattr(time_slot, 'schedule') else None
            },
            source_service="scheduling-service"
        )

        return appointment

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating appointment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create appointment: {str(e)}"
        )


@app.get(
    "/api/v1/scheduling/appointments/{appointment_id}",
    response_model=AppointmentResponse,
    tags=["Appointments"]
)
async def get_appointment(
    appointment_id: UUID,
    db: Session = Depends(get_db)
):
    """Get appointment by ID"""
    try:
        appointment = db.query(Appointment).filter(
            Appointment.id == appointment_id
        ).first()

        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )

        return appointment

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving appointment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve appointment"
        )


@app.get(
    "/api/v1/scheduling/appointments",
    response_model=AppointmentListResponse,
    tags=["Appointments"]
)
async def list_appointments(
    patient_id: Optional[UUID] = Query(None),
    practitioner_id: Optional[UUID] = Query(None),
    location_id: Optional[UUID] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List appointments with filters

    Search by patient, practitioner, date range, status, etc.
    """
    try:
        query = db.query(Appointment)

        if patient_id:
            query = query.filter(Appointment.patient_id == patient_id)

        if practitioner_id:
            query = query.filter(Appointment.practitioner_id == practitioner_id)

        if location_id:
            query = query.filter(Appointment.location_id == location_id)

        if status:
            query = query.filter(Appointment.status == status.lower())

        # Filter by date range using time_slot join
        if from_date or to_date:
            query = query.join(TimeSlot)

            if from_date:
                from_datetime = datetime.combine(from_date, time.min)
                query = query.filter(TimeSlot.start_datetime >= from_datetime)

            if to_date:
                to_datetime = datetime.combine(to_date, time.max)
                query = query.filter(TimeSlot.start_datetime <= to_datetime)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        appointments = query.order_by(
            Appointment.created_at.desc()
        ).offset(offset).limit(page_size).all()

        has_next = (offset + page_size) < total
        has_previous = page > 1

        return AppointmentListResponse(
            total=total,
            appointments=appointments,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous
        )

    except Exception as e:
        logger.error(f"Error listing appointments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list appointments"
        )


@app.patch(
    "/api/v1/scheduling/appointments/{appointment_id}",
    response_model=AppointmentResponse,
    tags=["Appointments"]
)
async def update_appointment(
    appointment_id: UUID,
    appointment_update: AppointmentUpdate,
    db: Session = Depends(get_db)
):
    """
    Update appointment (reschedule or change status)

    Can be used to reschedule by changing time_slot_id.
    """
    try:
        appointment = db.query(Appointment).filter(
            Appointment.id == appointment_id
        ).first()

        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )

        old_slot_id = appointment.time_slot_id

        # Handle rescheduling
        if appointment_update.time_slot_id and appointment_update.time_slot_id != old_slot_id:
            # Validate new slot
            new_slot = db.query(TimeSlot).filter(
                TimeSlot.id == appointment_update.time_slot_id
            ).first()

            if not new_slot:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="New time slot not found"
                )

            if new_slot.status != "available":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="New time slot is not available"
                )

            if new_slot.booked_count >= new_slot.capacity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="New time slot is full"
                )

            # Update old slot
            old_slot = db.query(TimeSlot).filter(
                TimeSlot.id == old_slot_id
            ).first()

            if old_slot:
                old_slot.booked_count = max(0, old_slot.booked_count - 1)
                if old_slot.booked_count < old_slot.capacity:
                    old_slot.status = "available"

            # Update new slot
            new_slot.booked_count += 1
            if new_slot.booked_count >= new_slot.capacity:
                new_slot.status = "full"

            appointment.time_slot_id = appointment_update.time_slot_id

        # Update other fields
        if appointment_update.status:
            old_status = appointment.status
            appointment.status = appointment_update.status

            # If cancelling, free up the slot
            if appointment_update.status == "cancelled" and old_status in ["booked", "checked_in"]:
                slot = db.query(TimeSlot).filter(
                    TimeSlot.id == appointment.time_slot_id
                ).first()

                if slot:
                    slot.booked_count = max(0, slot.booked_count - 1)
                    if slot.booked_count < slot.capacity:
                        slot.status = "available"

        if appointment_update.reason_text is not None:
            appointment.reason_text = appointment_update.reason_text

        if appointment_update.metadata is not None:
            appointment.metadata = appointment_update.metadata

        appointment.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(appointment)

        logger.info(f"Updated appointment {appointment_id}")

        # Publish event
        await publish_event(
            event_type=EventType.APPOINTMENT_UPDATED,
            tenant_id=str(appointment.tenant_id),
            payload={
                "appointment_id": str(appointment.id),
                "patient_id": str(appointment.patient_id),
                "status": appointment.status,
                "rescheduled": appointment_update.time_slot_id is not None
            },
            source_service="scheduling-service"
        )

        return appointment

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating appointment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update appointment"
        )


@app.post(
    "/api/v1/scheduling/appointments/{appointment_id}/check-in",
    response_model=AppointmentResponse,
    tags=["Appointments"]
)
async def check_in_appointment(
    appointment_id: UUID,
    check_in_data: Optional[AppointmentCheckInRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Check in an appointment

    Marks appointment as checked_in when patient arrives.
    """
    try:
        appointment = db.query(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.status == "booked"
        ).first()

        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booked appointment not found"
            )

        appointment.status = "checked_in"
        appointment.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(appointment)

        logger.info(f"Checked in appointment {appointment_id}")

        # Publish event
        await publish_event(
            event_type=EventType.APPOINTMENT_CHECKED_IN,
            tenant_id=str(appointment.tenant_id),
            payload={
                "appointment_id": str(appointment.id),
                "patient_id": str(appointment.patient_id),
                "practitioner_id": str(appointment.practitioner_id)
            },
            source_service="scheduling-service"
        )

        return appointment

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error checking in appointment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check in appointment"
        )


@app.post(
    "/api/v1/scheduling/appointments/{appointment_id}/no-show",
    response_model=AppointmentResponse,
    tags=["Appointments"]
)
async def mark_no_show(
    appointment_id: UUID,
    db: Session = Depends(get_db)
):
    """Mark appointment as no-show"""
    try:
        appointment = db.query(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.status.in_(["booked", "checked_in"])
        ).first()

        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active appointment not found"
            )

        appointment.status = "no_show"
        appointment.updated_at = datetime.utcnow()

        # Free up the slot
        slot = db.query(TimeSlot).filter(
            TimeSlot.id == appointment.time_slot_id
        ).first()

        if slot:
            slot.booked_count = max(0, slot.booked_count - 1)
            if slot.booked_count < slot.capacity:
                slot.status = "available"

        db.commit()
        db.refresh(appointment)

        logger.warning(f"Marked appointment {appointment_id} as no-show")

        # Publish event
        await publish_event(
            event_type=EventType.APPOINTMENT_NO_SHOW,
            tenant_id=str(appointment.tenant_id),
            payload={
                "appointment_id": str(appointment.id),
                "patient_id": str(appointment.patient_id),
                "practitioner_id": str(appointment.practitioner_id)
            },
            source_service="scheduling-service"
        )

        return appointment

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error marking no-show: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark no-show"
        )


@app.post(
    "/api/v1/scheduling/appointments/{appointment_id}/complete",
    response_model=AppointmentResponse,
    tags=["Appointments"]
)
async def complete_appointment(
    appointment_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Mark appointment as completed

    Usually done after encounter is completed.
    """
    try:
        appointment = db.query(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.status.in_(["booked", "checked_in"])
        ).first()

        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active appointment not found"
            )

        appointment.status = "completed"
        appointment.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(appointment)

        logger.info(f"Completed appointment {appointment_id}")

        # Publish event
        await publish_event(
            event_type=EventType.APPOINTMENT_COMPLETED,
            tenant_id=str(appointment.tenant_id),
            payload={
                "appointment_id": str(appointment.id),
                "patient_id": str(appointment.patient_id),
                "practitioner_id": str(appointment.practitioner_id)
            },
            source_service="scheduling-service"
        )

        return appointment

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error completing appointment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete appointment"
        )


# ==================== Startup ====================

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("Scheduling Service starting up...")

    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

    logger.info("Scheduling Service ready!")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005, reload=True)
