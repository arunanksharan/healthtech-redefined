"""
Patients Router
API endpoints for FHIR-compliant patient management
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
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
    PatientStatistics
)
from modules.patients.service import PatientService


router = APIRouter(prefix="/patients", tags=["Patients"])


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
    """
    from shared.database.models import MediaAsset

    # Verify patient exists
    service = PatientService(db)
    patient = await service.get_patient(patient_id)

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Get media
    media_files = db.query(MediaAsset).filter(
        MediaAsset.patient_id == patient_id
    ).order_by(MediaAsset.created_at.desc()).all()

    from modules.media.schemas import MediaResponse
    return [MediaResponse.from_orm(m) for m in media_files]


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
