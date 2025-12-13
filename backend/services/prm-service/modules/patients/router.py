"""
Patients Router
API endpoints for FHIR-compliant patient management
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from loguru import logger

from shared.database.connection import get_db

from modules.patients.schemas import (
    PatientCreate,
    PatientUpdate,
    PatientSearch,
    PatientResponse,
    PatientDetailResponse,
    DuplicatePatient,
    PatientMergeRequest,
    PatientMergeResult,
    PatientStatistics,
    PatientSimpleResponse,
    PatientSimpleListResponse,
    Patient360Response,
    SearchType
)
from modules.patients.service import PatientService


router = APIRouter(prefix="/patients", tags=["Patients"])


# ==================== List & Search (GET) ====================

@router.get("", response_model=PatientSimpleListResponse)
async def list_patients(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str = Query(None, description="Search query (name, phone, email)"),
    tenant_id: UUID = Query(None, description="Filter by tenant"),
    status: str = Query(None, description="Filter by status (active, inactive)"),
    db: Session = Depends(get_db)
):
    """
    List patients with pagination and optional filters

    Returns paginated list of patients. Supports:
    - Full-text search across name, phone, email
    - Filter by tenant/organization
    - Filter by status
    """
    from shared.database.models import Patient
    from sqlalchemy import or_

    query = db.query(Patient)

    # Apply filters
    if tenant_id:
        query = query.filter(Patient.tenant_id == tenant_id)

    if status:
        query = query.filter(Patient.is_deceased == (status == "deceased"))

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Patient.first_name.ilike(search_term),
                Patient.last_name.ilike(search_term),
                Patient.phone_primary.ilike(search_term),
                Patient.email_primary.ilike(search_term)
            )
        )

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    patients = query.order_by(Patient.created_at.desc()).offset(offset).limit(page_size).all()

    return PatientSimpleListResponse(
        items=[PatientSimpleResponse.model_validate(p) for p in patients],
        total=total,
        page=page,
        page_size=page_size,
        has_next=offset + len(patients) < total,
        has_previous=page > 1
    )


@router.get("/search", response_model=List[PatientSimpleResponse])
async def search_patients_get(
    query: str = Query(..., min_length=2, description="Search query"),
    type: SearchType = Query(SearchType.NAME, description="Search type"),
    limit: int = Query(20, ge=1, le=50, description="Max results"),
    db: Session = Depends(get_db)
):
    """
    Quick search patients by specific field type

    Search types:
    - name: Search by first/last name
    - phone: Search by phone number
    - mrn: Search by MRN in patient_identifiers
    - email: Search by email
    """
    from shared.database.models import Patient, PatientIdentifier
    from sqlalchemy import or_

    search_term = f"%{query}%"

    if type == SearchType.NAME:
        patients = db.query(Patient).filter(
            or_(
                Patient.first_name.ilike(search_term),
                Patient.last_name.ilike(search_term)
            )
        ).limit(limit).all()

    elif type == SearchType.PHONE:
        # Clean phone number for search
        phone_digits = ''.join(c for c in query if c.isdigit())
        patients = db.query(Patient).filter(
            Patient.phone_primary.contains(phone_digits)
        ).limit(limit).all()

    elif type == SearchType.MRN:
        # Search in patient_identifiers table
        patient_ids = db.query(PatientIdentifier.patient_id).filter(
            PatientIdentifier.system == "MRN",
            PatientIdentifier.value.ilike(search_term)
        ).all()

        patient_id_list = [pid[0] for pid in patient_ids]
        patients = db.query(Patient).filter(
            Patient.id.in_(patient_id_list)
        ).limit(limit).all()

    elif type == SearchType.EMAIL:
        patients = db.query(Patient).filter(
            Patient.email_primary.ilike(search_term)
        ).limit(limit).all()

    else:
        patients = []

    return [PatientSimpleResponse.model_validate(p) for p in patients]


@router.get("/{patient_id}/360", response_model=Patient360Response)
async def get_patient_360(
    patient_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get 360-degree patient view

    Aggregates:
    - Patient demographics
    - Recent appointments (last 5)
    - Active journey instances
    - Open tickets
    - Recent communications

    Includes counts and timeline information.
    """
    from shared.database.models import (
        Patient, Appointment, JourneyInstance,
        Ticket, Communication
    )
    from datetime import datetime

    # Get patient
    patient = db.query(Patient).filter(Patient.id == patient_id).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Get appointments (join with TimeSlot to get scheduled time)
    from shared.database.models import TimeSlot
    appointments = db.query(Appointment).join(
        TimeSlot, Appointment.time_slot_id == TimeSlot.id
    ).filter(
        Appointment.patient_id == patient_id
    ).order_by(TimeSlot.start_datetime.desc()).limit(10).all()

    total_appointments = db.query(Appointment).filter(
        Appointment.patient_id == patient_id
    ).count()

    upcoming_appointments = db.query(Appointment).join(
        TimeSlot, Appointment.time_slot_id == TimeSlot.id
    ).filter(
        Appointment.patient_id == patient_id,
        TimeSlot.start_datetime >= datetime.utcnow(),
        Appointment.status.in_(["scheduled", "confirmed", "booked"])
    ).count()

    # Get journey instances
    journeys = db.query(JourneyInstance).filter(
        JourneyInstance.patient_id == patient_id
    ).order_by(JourneyInstance.created_at.desc()).limit(5).all()

    active_journeys = db.query(JourneyInstance).filter(
        JourneyInstance.patient_id == patient_id,
        JourneyInstance.status == "active"
    ).count()

    # Get tickets
    tickets = db.query(Ticket).filter(
        Ticket.patient_id == patient_id
    ).order_by(Ticket.created_at.desc()).limit(5).all()

    open_tickets = db.query(Ticket).filter(
        Ticket.patient_id == patient_id,
        Ticket.status.in_(["open", "in_progress"])
    ).count()

    # Get communications
    communications = db.query(Communication).filter(
        Communication.patient_id == patient_id
    ).order_by(Communication.created_at.desc()).limit(10).all()

    recent_communications = db.query(Communication).filter(
        Communication.patient_id == patient_id
    ).count()

    # Get timeline dates (last completed appointment)
    last_visit_apt = db.query(Appointment).join(
        TimeSlot, Appointment.time_slot_id == TimeSlot.id
    ).filter(
        Appointment.patient_id == patient_id,
        Appointment.status == "completed"
    ).order_by(TimeSlot.start_datetime.desc()).first()

    # Get next upcoming appointment
    next_apt = db.query(Appointment).join(
        TimeSlot, Appointment.time_slot_id == TimeSlot.id
    ).filter(
        Appointment.patient_id == patient_id,
        TimeSlot.start_datetime >= datetime.utcnow(),
        Appointment.status.in_(["scheduled", "confirmed", "booked"])
    ).order_by(TimeSlot.start_datetime.asc()).first()

    # Helper to get scheduled time from appointment
    def get_apt_time(apt):
        if apt and apt.time_slot:
            return apt.time_slot.start_datetime
        return None

    return Patient360Response(
        patient=PatientSimpleResponse.model_validate(patient),
        appointments=[{
            "id": str(a.id),
            "scheduled_at": a.time_slot.start_datetime.isoformat() if a.time_slot and a.time_slot.start_datetime else None,
            "status": a.status,
            "appointment_type": a.appointment_type,
            "practitioner_id": str(a.practitioner_id) if a.practitioner_id else None
        } for a in appointments],
        journeys=[{
            "id": str(j.id),
            "journey_id": str(j.journey_id),
            "status": j.status,
            "current_stage_id": str(j.current_stage_id) if j.current_stage_id else None
        } for j in journeys],
        tickets=[{
            "id": str(t.id),
            "title": t.title,
            "status": t.status,
            "priority": t.priority
        } for t in tickets],
        communications=[{
            "id": str(c.id),
            "channel": c.channel,
            "direction": c.direction,
            "sent_at": c.created_at.isoformat() if c.created_at else None,
            "message_type": getattr(c, 'message_type', None) or c.channel
        } for c in communications],
        total_appointments=total_appointments,
        upcoming_appointments=upcoming_appointments,
        active_journeys=active_journeys,
        open_tickets=open_tickets,
        recent_communications=recent_communications,
        last_visit_date=get_apt_time(last_visit_apt),
        next_appointment_date=get_apt_time(next_apt)
    )


# ==================== CRUD Operations ====================

@router.post("", response_model=PatientResponse, status_code=201)
async def create_patient(
    patient_data: PatientCreate,
    db: Session = Depends(get_db)
):
    """
    Create new patient

    FHIR-compliant patient registration with:
    - Auto-generated MRN (Medical Record Number)
    - Comprehensive demographics
    - Contact information
    - Emergency contacts
    - Insurance information
    - Duplicate detection (warns but doesn't block)

    Phone numbers are automatically normalized to E.164 format.
    SSN is encrypted before storage.
    """
    service = PatientService(db)

    patient = await service.create_patient(patient_data)

    return PatientResponse.from_orm(patient)


@router.get("/{patient_id}", response_model=PatientDetailResponse)
async def get_patient(
    patient_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get patient by ID with statistics

    Includes:
    - Full patient demographics
    - Appointment counts (total, upcoming)
    - Conversation count
    - Media files count
    - Last visit date
    - Next appointment date
    """
    service = PatientService(db)

    patient_detail = await service.get_patient_detail(patient_id)

    if not patient_detail:
        raise HTTPException(status_code=404, detail="Patient not found")

    return patient_detail


@router.get("/mrn/{mrn}", response_model=PatientResponse)
async def get_patient_by_mrn(
    mrn: str,
    db: Session = Depends(get_db)
):
    """
    Get patient by Medical Record Number (MRN)
    """
    service = PatientService(db)

    patient = await service.get_patient_by_mrn(mrn)

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    return PatientResponse.from_orm(patient)


@router.patch("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: UUID,
    update_data: PatientUpdate,
    db: Session = Depends(get_db)
):
    """
    Update patient information

    All fields are optional - only provided fields will be updated.
    """
    service = PatientService(db)

    patient = await service.update_patient(patient_id, update_data)

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    return PatientResponse.from_orm(patient)


@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Soft delete patient

    Sets patient status to 'inactive'.
    Patient data is retained for compliance and historical records.
    """
    service = PatientService(db)

    success = await service.delete_patient(patient_id)

    if not success:
        raise HTTPException(status_code=404, detail="Patient not found")

    return {
        "success": True,
        "message": "Patient deleted successfully",
        "patient_id": str(patient_id)
    }


# ==================== Search ====================

@router.post("/search", response_model=List[PatientResponse])
async def search_patients(
    search_params: PatientSearch,
    db: Session = Depends(get_db)
):
    """
    Advanced patient search

    Search by:
    - General query (searches name, MRN, phone, email)
    - Specific fields (name, phone, DOB, gender, status)
    - Date ranges (created_after, created_before)
    - Primary care provider

    Supports fuzzy name matching and phone number normalization.

    Pagination:
    - limit: Number of results (1-100, default 50)
    - offset: Skip N results

    Results ordered by most recent first.
    """
    service = PatientService(db)

    patients = await service.search_patients(search_params)

    return [PatientResponse.from_orm(p) for p in patients]


# ==================== Duplicate Detection ====================

@router.get("/{patient_id}/duplicates", response_model=List[DuplicatePatient])
async def find_duplicates(
    patient_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Find potential duplicate patients

    Checks for duplicates based on:
    - Exact name + date of birth
    - Same phone number
    - Similar names (fuzzy matching)

    Returns list of potential duplicates with match scores.
    """
    service = PatientService(db)

    duplicates = await service.find_duplicates(patient_id)

    return duplicates


@router.post("/merge", response_model=PatientMergeResult)
async def merge_patients(
    merge_request: PatientMergeRequest,
    db: Session = Depends(get_db)
):
    """
    Merge duplicate patients

    Process:
    1. Moves all appointments to primary patient
    2. Moves all conversations to primary patient
    3. Moves all media files to primary patient
    4. Deactivates duplicate patient
    5. Records merge in audit log

    WARNING: This operation cannot be easily undone.
    Ensure you've verified the patients are actually duplicates.

    Returns summary of merged data.
    """
    service = PatientService(db)

    result = await service.merge_patients(merge_request)

    if not result.success:
        raise HTTPException(
            status_code=400,
            detail=f"Merge failed: {', '.join(result.errors)}"
        )

    return result


# ==================== Statistics ====================

@router.get("/stats/demographics", response_model=PatientStatistics)
async def get_patient_statistics(
    org_id: UUID = None,
    db: Session = Depends(get_db)
):
    """
    Get patient demographics and statistics

    Includes:
    - Total, active, inactive patient counts
    - New patients this month
    - Breakdown by gender
    - Breakdown by age group (0-18, 19-35, 36-50, 51-65, 66+)
    - Breakdown by status
    - Average age
    """
    service = PatientService(db)

    stats = await service.get_statistics(org_id=org_id)

    return stats


# ==================== Related Data ====================

@router.get("/{patient_id}/appointments")
async def get_patient_appointments(
    patient_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get all appointments for patient

    Returns list of appointments ordered by date (most recent first).
    """
    from shared.database.models import Appointment

    # Verify patient exists
    service = PatientService(db)
    patient = await service.get_patient(patient_id)

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Get appointments
    appointments = db.query(Appointment).filter(
        Appointment.patient_id == patient_id
    ).order_by(Appointment.confirmed_start.desc()).all()

    from modules.appointments.schemas import AppointmentResponse
    return [AppointmentResponse.from_orm(a) for a in appointments]


@router.get("/{patient_id}/conversations")
async def get_patient_conversations(
    patient_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get all conversations for patient

    Returns list of conversations ordered by date (most recent first).
    """
    from shared.database.models import Conversation

    # Verify patient exists
    service = PatientService(db)
    patient = await service.get_patient(patient_id)

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Get conversations
    conversations = db.query(Conversation).filter(
        Conversation.patient_id == patient_id
    ).order_by(Conversation.updated_at.desc()).all()

    from modules.conversations.schemas import ConversationResponse
    return [ConversationResponse.from_orm(c) for c in conversations]


@router.get("/{patient_id}/media")
async def get_patient_media(
    patient_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get all media files for patient

    Includes:
    - Insurance cards
    - Lab results
    - Medical records
    - Profile photos
    - Other documents

    Returns list ordered by upload date (most recent first).
    
    Note: MediaAsset model not yet implemented - returns empty list
    """
    # Verify patient exists
    service = PatientService(db)
    patient = await service.get_patient(patient_id)

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # TODO: Implement when MediaAsset model is created
    # MediaAsset model doesn't exist yet, return empty list
    return []


# ==================== Activation ====================

@router.post("/{patient_id}/activate", response_model=PatientResponse)
async def activate_patient(
    patient_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Reactivate an inactive patient

    Sets patient status back to 'active'.
    """
    from modules.patients.schemas import PatientUpdate, PatientStatus

    service = PatientService(db)

    patient = await service.update_patient(
        patient_id,
        PatientUpdate(status=PatientStatus.ACTIVE)
    )

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    return PatientResponse.from_orm(patient)


# ==================== Health Check ====================

@router.get("/health/check")
async def patients_health_check():
    """Health check for patients module"""
    return {
        "status": "healthy",
        "module": "patients",
        "features": [
            "FHIR-compliant",
            "duplicate_detection",
            "patient_merge",
            "advanced_search",
            "statistics"
        ]
    }
