"""
Telehealth Platform API Router

FastAPI endpoints for telehealth operations:
- Video sessions
- Appointments and scheduling
- Virtual waiting room
- Recordings
- Payments
- Analytics

EPIC-007: Telehealth Platform
"""

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session

from .schemas import (
    # Session schemas
    SessionCreate, SessionResponse, JoinTokenRequest, JoinTokenResponse,
    ParticipantCreate, ParticipantResponse, MediaStateUpdate, SessionEndRequest,
    # Appointment schemas
    AppointmentCreate, AppointmentResponse, AppointmentReschedule, AppointmentCancel,
    AvailableSlotsRequest, AvailableSlot, ProviderScheduleCreate, ProviderScheduleResponse,
    BlockedTimeCreate,
    # Waiting room schemas
    WaitingRoomCreate, WaitingRoomResponse, CheckInRequest, WaitingRoomEntryResponse,
    DeviceCheckResult, DeviceCheckResponse, FormSubmission, ChatMessageCreate, ChatMessageResponse,
    QueueStatus,
    # Recording schemas
    StartRecordingRequest, RecordingResponse, RecordingConsentRequest,
    # Payment schemas
    PaymentCreate, PaymentResponse, PaymentIntentCreate, PaymentIntentResponse, RefundRequest,
    # Analytics schemas
    SessionAnalyticsResponse, SatisfactionSurveyCreate, TelehealthMetricsResponse,
    # Other schemas
    CalendarExportResponse, InterpreterRequest, InterpreterResponse,
    PaginatedResponse,
)
from .service import (
    TelehealthSessionService,
    TelehealthAppointmentService,
    WaitingRoomServiceDB,
    TelehealthPaymentService,
    TelehealthAnalyticsService,
)

# Create router
router = APIRouter(prefix="/telehealth", tags=["Telehealth"])


# Dependency for getting database session
def get_db():
    """Get database session - should be injected from main app."""
    # This will be overridden by the main application
    pass


def get_tenant_id(x_tenant_id: str = Header(...)) -> UUID:
    """Extract tenant ID from header."""
    try:
        return UUID(x_tenant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tenant ID")


# ============================================================================
# SESSION ENDPOINTS
# ============================================================================

@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def create_session(
    data: SessionCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Create a new telehealth video session.

    US-007.1: Video Consultation Infrastructure
    """
    service = TelehealthSessionService(db)
    session = await service.create_session(tenant_id, data)
    return SessionResponse(
        id=session.id,
        room_name=session.room_name,
        session_type=session.session_type,
        status=session.status,
        appointment_id=session.appointment_id,
        scheduled_duration_minutes=session.scheduled_duration_minutes,
        max_participants=session.max_participants,
        waiting_room_enabled=session.waiting_room_enabled,
        screen_sharing_enabled=session.screen_sharing_enabled,
        chat_enabled=session.chat_enabled,
        is_recording=session.is_recording,
        started_at=session.started_at,
        ended_at=session.ended_at,
        participant_count=len(session.participants) if session.participants else 0,
        created_at=session.created_at,
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get a telehealth session by ID."""
    service = TelehealthSessionService(db)
    session = await service.get_session(tenant_id, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/sessions", response_model=List[SessionResponse])
async def list_active_sessions(
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """List all active telehealth sessions."""
    service = TelehealthSessionService(db)
    return await service.get_active_sessions(tenant_id)


@router.post("/sessions/{session_id}/participants", response_model=ParticipantResponse)
async def add_participant(
    session_id: UUID,
    data: ParticipantCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Add a participant to a session.

    US-007.1: Video Consultation Infrastructure
    """
    service = TelehealthSessionService(db)
    try:
        return await service.add_participant(tenant_id, session_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions/{session_id}/participants", response_model=List[ParticipantResponse])
async def get_session_participants(
    session_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get all participants for a session."""
    service = TelehealthSessionService(db)
    return await service.get_session_participants(tenant_id, session_id)


@router.post("/sessions/{session_id}/join-token", response_model=JoinTokenResponse)
async def generate_join_token(
    session_id: UUID,
    request: JoinTokenRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Generate a token for joining the video room.

    US-007.1: Video Consultation Infrastructure
    """
    service = TelehealthSessionService(db)
    try:
        result = await service.generate_join_token(tenant_id, session_id, request.participant_id)
        return JoinTokenResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sessions/{session_id}/participants/{participant_id}/joined")
async def participant_joined(
    session_id: UUID,
    participant_id: UUID,
    connection_id: str = Query(...),
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Handle participant joining the session."""
    service = TelehealthSessionService(db)
    try:
        return await service.participant_joined(tenant_id, session_id, participant_id, connection_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sessions/{session_id}/participants/{participant_id}/left")
async def participant_left(
    session_id: UUID,
    participant_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Handle participant leaving the session."""
    service = TelehealthSessionService(db)
    try:
        return await service.participant_left(tenant_id, session_id, participant_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/sessions/{session_id}/participants/{participant_id}/media")
async def update_media_state(
    session_id: UUID,
    participant_id: UUID,
    data: MediaStateUpdate,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Update participant media state (mute/unmute video/audio).

    US-007.3: Screen Sharing & Collaboration
    """
    service = TelehealthSessionService(db)
    try:
        return await service.update_media_state(tenant_id, session_id, participant_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sessions/{session_id}/end", response_model=SessionResponse)
async def end_session(
    session_id: UUID,
    data: SessionEndRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """End a telehealth session."""
    service = TelehealthSessionService(db)
    try:
        return await service.end_session(tenant_id, session_id, data.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# APPOINTMENT ENDPOINTS
# ============================================================================

@router.post("/appointments", response_model=AppointmentResponse, status_code=201)
async def book_appointment(
    data: AppointmentCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Book a telehealth appointment.

    US-007.4: Telehealth Scheduling
    """
    service = TelehealthAppointmentService(db)
    try:
        return await service.book_appointment(tenant_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get an appointment by ID."""
    service = TelehealthAppointmentService(db)
    appointment = await service.get_appointment(tenant_id, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment


@router.post("/appointments/{appointment_id}/confirm", response_model=AppointmentResponse)
async def confirm_appointment(
    appointment_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Confirm an appointment."""
    service = TelehealthAppointmentService(db)
    try:
        return await service.confirm_appointment(tenant_id, appointment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/appointments/{appointment_id}/cancel", response_model=AppointmentResponse)
async def cancel_appointment(
    appointment_id: UUID,
    data: AppointmentCancel,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Cancel an appointment."""
    service = TelehealthAppointmentService(db)
    try:
        return await service.cancel_appointment(tenant_id, appointment_id, data.reason, data.cancelled_by)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/appointments/{appointment_id}/reschedule", response_model=AppointmentResponse)
async def reschedule_appointment(
    appointment_id: UUID,
    data: AppointmentReschedule,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Reschedule an appointment.

    US-007.4: Telehealth Scheduling
    """
    service = TelehealthAppointmentService(db)
    try:
        return await service.reschedule_appointment(tenant_id, appointment_id, data.new_start_time)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/appointments/available-slots", response_model=List[AvailableSlot])
async def get_available_slots(
    request: AvailableSlotsRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Get available appointment slots for a provider.

    US-007.4: Telehealth Scheduling
    """
    service = TelehealthAppointmentService(db)
    return await service.get_available_slots(tenant_id, request)


@router.get("/patients/{patient_id}/appointments", response_model=List[AppointmentResponse])
async def get_patient_appointments(
    patient_id: UUID,
    include_past: bool = False,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get appointments for a patient."""
    service = TelehealthAppointmentService(db)
    return await service.get_patient_appointments(tenant_id, patient_id, include_past)


@router.get("/providers/{provider_id}/appointments", response_model=List[AppointmentResponse])
async def get_provider_appointments(
    provider_id: UUID,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get appointments for a provider."""
    service = TelehealthAppointmentService(db)
    return await service.get_provider_appointments(tenant_id, provider_id, date_from, date_to)


@router.get("/appointments/{appointment_id}/calendar", response_model=CalendarExportResponse)
async def export_appointment_calendar(
    appointment_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Export appointment as ICS calendar file.

    US-007.4: Calendar Integration
    """
    service = TelehealthAppointmentService(db)
    appointment = await service.get_appointment(tenant_id, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # Generate ICS content
    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Healthcare PRM//Telehealth//EN",
        "BEGIN:VEVENT",
        f"UID:{appointment.id}@prm.healthcare",
        f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
        f"DTSTART:{appointment.scheduled_start.strftime('%Y%m%dT%H%M%SZ')}",
        f"DTEND:{appointment.scheduled_end.strftime('%Y%m%dT%H%M%SZ')}",
        f"SUMMARY:Telehealth Appointment with {appointment.provider_name or 'Provider'}",
        f"DESCRIPTION:Join URL: {appointment.join_url}",
        f"URL:{appointment.join_url}",
        "END:VEVENT",
        "END:VCALENDAR",
    ]

    return CalendarExportResponse(
        ics_content="\r\n".join(ics_lines),
        filename=f"telehealth_appointment_{appointment.id}.ics"
    )


# ============================================================================
# PROVIDER SCHEDULE ENDPOINTS
# ============================================================================

@router.post("/providers/{provider_id}/schedule", response_model=ProviderScheduleResponse)
async def set_provider_schedule(
    provider_id: UUID,
    data: ProviderScheduleCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Set a provider's weekly schedule for telehealth.

    US-007.4: Telehealth Scheduling
    """
    service = TelehealthAppointmentService(db)
    return await service.set_provider_schedule(tenant_id, provider_id, data)


# ============================================================================
# WAITING ROOM ENDPOINTS
# ============================================================================

@router.post("/waiting-rooms", response_model=WaitingRoomResponse, status_code=201)
async def create_waiting_room(
    data: WaitingRoomCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Create a virtual waiting room.

    US-007.2: Virtual Waiting Room
    """
    service = WaitingRoomServiceDB(db)
    return await service.create_waiting_room(tenant_id, data)


@router.get("/waiting-rooms/{room_id}", response_model=WaitingRoomResponse)
async def get_waiting_room(
    room_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get a waiting room by ID."""
    service = WaitingRoomServiceDB(db)
    room = await service.get_waiting_room(tenant_id, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Waiting room not found")
    return room


@router.post("/waiting-rooms/{room_id}/check-in", response_model=WaitingRoomEntryResponse)
async def check_in_to_waiting_room(
    room_id: UUID,
    data: CheckInRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Check a patient into the waiting room.

    US-007.2: Virtual Waiting Room
    """
    service = WaitingRoomServiceDB(db)
    try:
        return await service.check_in(tenant_id, room_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/waiting-rooms/{room_id}/queue", response_model=QueueStatus)
async def get_queue_status(
    room_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Get current queue status for a waiting room.

    US-007.2: Virtual Waiting Room
    """
    service = WaitingRoomServiceDB(db)
    status = await service.get_queue_status(tenant_id, room_id)
    if not status:
        raise HTTPException(status_code=404, detail="Waiting room not found")
    return status


@router.get("/waiting-room-entries/{entry_id}", response_model=WaitingRoomEntryResponse)
async def get_waiting_room_entry(
    entry_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get a waiting room entry."""
    service = WaitingRoomServiceDB(db)
    entry = await service.get_entry(tenant_id, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.post("/waiting-room-entries/{entry_id}/device-check", response_model=DeviceCheckResponse)
async def complete_device_check(
    entry_id: UUID,
    result: DeviceCheckResult,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Complete device check for a waiting room entry.

    US-007.2: Virtual Waiting Room - Pre-call device check
    """
    service = WaitingRoomServiceDB(db)
    try:
        entry = await service.complete_device_check(tenant_id, entry_id, result)

        # Determine issues
        issues = []
        if entry.device_check_result:
            issues = entry.device_check_result.get("issues", [])

        return DeviceCheckResponse(
            check_id=entry.id,
            status=entry.device_check_status,
            issues=issues,
            checked_at=datetime.utcnow(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/waiting-room-entries/{entry_id}/forms", response_model=dict)
async def submit_form_response(
    entry_id: UUID,
    submission: FormSubmission,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Submit responses for a pre-visit form.

    US-007.2: Virtual Waiting Room - Pre-visit forms
    """
    service = WaitingRoomServiceDB(db)
    try:
        form = await service.submit_form_response(tenant_id, entry_id, submission)
        return {"form_id": str(form.id), "status": form.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/waiting-room-entries/{entry_id}/messages", response_model=ChatMessageResponse)
async def send_chat_message(
    entry_id: UUID,
    data: ChatMessageCreate,
    sender_id: UUID = Query(...),
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Send a chat message in the waiting room.

    US-007.2: Virtual Waiting Room - Chat with staff
    """
    service = WaitingRoomServiceDB(db)
    try:
        return await service.send_chat_message(tenant_id, entry_id, sender_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/waiting-room-entries/{entry_id}/admit", response_model=WaitingRoomEntryResponse)
async def admit_to_call(
    entry_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Admit patient from waiting room to the call.

    US-007.2: Virtual Waiting Room
    """
    service = WaitingRoomServiceDB(db)
    try:
        return await service.admit_to_call(tenant_id, entry_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/waiting-room-entries/{entry_id}/depart", response_model=WaitingRoomEntryResponse)
async def depart_from_waiting_room(
    entry_id: UUID,
    reason: str = "completed",
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Remove patient from waiting room."""
    service = WaitingRoomServiceDB(db)
    try:
        return await service.depart(tenant_id, entry_id, reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# PAYMENT ENDPOINTS
# ============================================================================

@router.post("/payments", response_model=PaymentResponse, status_code=201)
async def create_payment(
    data: PaymentCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Create a payment for a telehealth visit.

    US-007.6: Payment Processing
    """
    service = TelehealthPaymentService(db)
    return await service.create_payment(tenant_id, data)


@router.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Get a payment by ID."""
    service = TelehealthPaymentService(db)
    payment = await service.get_payment(tenant_id, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.post("/payments/{payment_id}/authorize", response_model=PaymentResponse)
async def authorize_payment(
    payment_id: UUID,
    external_payment_id: str = Query(...),
    card_last_four: Optional[str] = None,
    card_brand: Optional[str] = None,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Authorize a payment (after Stripe/Square returns).

    US-007.6: Payment Processing
    """
    service = TelehealthPaymentService(db)
    try:
        return await service.authorize_payment(
            tenant_id, payment_id, external_payment_id, card_last_four, card_brand
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/payments/{payment_id}/capture", response_model=PaymentResponse)
async def capture_payment(
    payment_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Capture an authorized payment.

    US-007.6: Payment Processing
    """
    service = TelehealthPaymentService(db)
    try:
        return await service.capture_payment(tenant_id, payment_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/payments/{payment_id}/refund", response_model=PaymentResponse)
async def refund_payment(
    payment_id: UUID,
    data: RefundRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Refund a payment.

    US-007.6: Payment Processing
    """
    service = TelehealthPaymentService(db)
    try:
        return await service.refund_payment(tenant_id, payment_id, data.amount_cents, data.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@router.post("/sessions/{session_id}/analytics", response_model=SessionAnalyticsResponse)
async def record_session_analytics(
    session_id: UUID,
    analytics: dict,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Record analytics for a session.

    US-007.8: Telehealth Analytics
    """
    service = TelehealthAnalyticsService(db)
    return await service.record_session_analytics(tenant_id, session_id, analytics)


@router.post("/surveys", status_code=201)
async def submit_satisfaction_survey(
    data: SatisfactionSurveyCreate,
    patient_id: UUID = Query(...),
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Submit a post-visit satisfaction survey.

    US-007.8: Telehealth Analytics - Patient satisfaction
    """
    service = TelehealthAnalyticsService(db)
    return await service.submit_satisfaction_survey(tenant_id, patient_id, data)


@router.get("/metrics", response_model=TelehealthMetricsResponse)
async def get_telehealth_metrics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Get telehealth utilization metrics.

    US-007.8: Telehealth Analytics
    """
    service = TelehealthAnalyticsService(db)
    return await service.get_telehealth_metrics(tenant_id, start_date, end_date)


# ============================================================================
# INTERPRETER ENDPOINTS
# ============================================================================

@router.post("/interpreter-requests", response_model=InterpreterResponse, status_code=201)
async def request_interpreter(
    data: InterpreterRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Request an interpreter for a session.

    US-007.9: Interpreter Services
    """
    # Placeholder - would integrate with interpreter service
    return InterpreterResponse(
        request_id=UUID("00000000-0000-0000-0000-000000000000"),
        session_id=data.session_id,
        language=data.language,
        status="pending",
        estimated_wait_minutes=5,
    )


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def health_check():
    """Health check for telehealth module."""
    return {
        "status": "healthy",
        "module": "telehealth",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }
