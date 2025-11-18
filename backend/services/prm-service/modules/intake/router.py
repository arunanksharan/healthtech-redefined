"""
Intake Router
API endpoints for clinical intake data collection
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from loguru import logger

from shared.database.connection import get_db

from modules.intake.schemas import (
    IntakeSessionCreate,
    IntakeSessionOut,
    IntakeRecordsUpsert,
    IntakeSummaryUpdate,
    IntakeSummaryOut,
    IntakeSubmit,
    IntakeStatistics
)
from modules.intake.service import IntakeService


router = APIRouter(prefix="/intake", tags=["Clinical Intake"])


# ==================== Session Management ====================

@router.post("/sessions", response_model=IntakeSessionOut, status_code=201)
async def create_session(
    payload: IntakeSessionCreate,
    db: Session = Depends(get_db)
):
    """
    Create intake session

    Sessions can be:
      - Anonymous (no patient_id)
      - Linked to patient (requires consent)
      - Linked to conversation (WhatsApp flow)

    Workflow:
      1. Create session
      2. Collect data via PUT /sessions/{id}/records
      3. Link patient via PUT /sessions/{id}/patient/{patient_id}
      4. Submit via POST /sessions/{id}/submit

    Example:
    ```json
    {
      "conversation_id": "uuid",
      "context": {
        "channel": "whatsapp",
        "locale": "en"
      }
    }
    ```
    """
    service = IntakeService(db)

    try:
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")

        session = await service.create_session(org_id, payload)
        return IntakeSessionOut.from_orm(session)

    except Exception as e:
        logger.error(f"Error creating intake session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.get("/sessions", response_model=List[IntakeSessionOut])
async def list_sessions(
    patient_id: UUID = None,
    conversation_id: UUID = None,
    status: str = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List intake sessions

    Filters:
      - patient_id: Sessions for specific patient
      - conversation_id: Sessions from specific conversation
      - status: open | submitted | closed

    Pagination:
      - limit: Number of results (1-100, default 50)
      - offset: Skip N results
    """
    service = IntakeService(db)

    try:
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")

        sessions = await service.list_sessions(
            org_id=org_id,
            patient_id=patient_id,
            conversation_id=conversation_id,
            status=status,
            limit=limit,
            offset=offset
        )

        return [IntakeSessionOut.from_orm(s) for s in sessions]

    except Exception as e:
        logger.error(f"Error listing intake sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")


@router.get("/sessions/{session_id}", response_model=IntakeSessionOut)
async def get_session(
    session_id: UUID,
    db: Session = Depends(get_db)
):
    """Get intake session by ID"""
    service = IntakeService(db)

    try:
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")

        session = await service.get_session(org_id, session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return IntakeSessionOut.from_orm(session)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting intake session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")


@router.put("/sessions/{session_id}/patient/{patient_id}", response_model=IntakeSessionOut)
async def set_session_patient(
    session_id: UUID,
    patient_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Link patient to intake session

    Requires patient consent for data_processing.

    Use case:
      - After collecting intake data anonymously
      - Patient confirms identity
      - Link intake to patient record
    """
    service = IntakeService(db)

    try:
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")

        session, error = await service.set_session_patient(org_id, session_id, patient_id)

        if error == "consent_required":
            raise HTTPException(status_code=403, detail="Patient consent required for data_processing")

        if error == "not_found":
            raise HTTPException(status_code=404, detail="Session not found")

        return IntakeSessionOut.from_orm(session)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting session patient: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to set patient: {str(e)}")


@router.put("/sessions/{session_id}/records")
async def upsert_records(
    session_id: UUID,
    payload: IntakeRecordsUpsert,
    db: Session = Depends(get_db)
):
    """
    Upsert intake records

    Supports partial updates - only provided sections are updated.

    Client-side idempotency:
      - Items with client_item_id are upserted (update if exists)
      - Items without client_item_id are always inserted

    Example:
    ```json
    {
      "chief_complaint": {
        "text": "Headache and fever"
      },
      "symptoms": [
        {
          "client_item_id": "symptom-1",
          "notes": "Severe headache",
          "severity": "severe",
          "onset": "2 days ago"
        }
      ],
      "allergies": [
        {
          "client_item_id": "allergy-1",
          "substance": "Penicillin",
          "reaction": "Rash",
          "severity": "moderate"
        }
      ],
      "medications": [
        {
          "client_item_id": "med-1",
          "name": "Ibuprofen",
          "dose": "200mg",
          "schedule": "as needed"
        }
      ]
    }
    ```

    Returns sections that were updated.
    """
    service = IntakeService(db)

    try:
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")

        result, error = await service.upsert_records(org_id, session_id, payload)

        if error == "not_found":
            raise HTTPException(status_code=404, detail="Session not found")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error upserting records: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to upsert records: {str(e)}")


@router.put("/sessions/{session_id}/summary")
async def set_summary(
    session_id: UUID,
    payload: IntakeSummaryUpdate,
    db: Session = Depends(get_db)
):
    """
    Set AI-generated summary

    Use case:
      - After collecting all intake data
      - AI agent generates summary
      - Summary stored for clinician review

    Example:
    ```json
    {
      "text": "35-year-old patient presenting with severe headache and fever for 2 days. No known allergies. Currently taking Ibuprofen as needed."
    }
    ```
    """
    service = IntakeService(db)

    try:
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")

        summary, error = await service.set_summary(org_id, session_id, payload.text)

        if error == "not_found":
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "id": str(summary.id),
            "session_id": str(summary.session_id),
            "text": summary.text
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to set summary: {str(e)}")


@router.post("/sessions/{session_id}/submit")
async def submit_session(
    session_id: UUID,
    payload: IntakeSubmit,
    db: Session = Depends(get_db)
):
    """
    Submit intake session

    Marks session as complete and ready for:
      - Clinician review
      - Appointment booking
      - EHR integration

    Example:
    ```json
    {
      "ready_for_booking": true
    }
    ```
    """
    service = IntakeService(db)

    try:
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")

        session = await service.submit(org_id, session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "status": session.status,
            "session_id": str(session.id)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit session: {str(e)}")


# ==================== Statistics ====================

@router.get("/stats", response_model=IntakeStatistics)
async def get_statistics(
    db: Session = Depends(get_db)
):
    """
    Get intake statistics

    Returns:
      - Total sessions
      - Sessions by status (open, submitted, closed)
      - Sessions linked to conversations
      - Sessions linked to patients
      - Average completion time
    """
    service = IntakeService(db)

    try:
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")

        stats = await service.get_statistics(org_id)
        return stats

    except Exception as e:
        logger.error(f"Error getting statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


# ==================== Health Check ====================

@router.get("/health/check")
async def intake_health_check():
    """Health check for intake module"""
    return {
        "status": "healthy",
        "module": "intake",
        "features": [
            "clinical_intake",
            "multi_section_collection",
            "client_side_idempotency",
            "whatsapp_integration",
            "ehr_export_ready"
        ],
        "supported_sections": [
            "chief_complaint",
            "symptoms",
            "allergies",
            "medications",
            "condition_history",
            "family_history",
            "social_history",
            "notes",
            "summary"
        ]
    }
