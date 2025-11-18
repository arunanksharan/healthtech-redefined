"""
Encounter Service - Clinical Encounter Management
Manages OPD and clinical encounters
"""
import os
import sys
from datetime import datetime, date
from typing import List, Optional
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from loguru import logger

from shared.database.connection import get_db, engine
from shared.database.models import Base, Encounter, Patient, Practitioner, Appointment
from shared.events.publisher import publish_event
from shared.events.types import EventType

from .schemas import (
    EncounterCreate,
    EncounterUpdate,
    EncounterResponse,
    EncounterListResponse,
    EncounterCompleteRequest
)

# Initialize FastAPI app
app = FastAPI(
    title="Encounter Service",
    description="Clinical encounter management for OPD workflows",
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
        "service": "encounter-service",
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== Encounter Management ====================

@app.post(
    "/api/v1/encounters",
    response_model=EncounterResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Encounters"]
)
async def create_encounter(
    encounter_data: EncounterCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new clinical encounter

    Can be created from an appointment or ad-hoc.
    Automatically sets status to 'in-progress' and started_at to now.
    """
    try:
        # Validate patient exists
        patient = db.query(Patient).filter(
            Patient.id == encounter_data.patient_id,
            Patient.tenant_id == encounter_data.tenant_id
        ).first()

        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )

        # Validate practitioner exists
        practitioner = db.query(Practitioner).filter(
            Practitioner.id == encounter_data.practitioner_id,
            Practitioner.tenant_id == encounter_data.tenant_id
        ).first()

        if not practitioner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Practitioner not found"
            )

        # If appointment_id provided, validate and link
        appointment = None
        if encounter_data.appointment_id:
            appointment = db.query(Appointment).filter(
                Appointment.id == encounter_data.appointment_id,
                Appointment.tenant_id == encounter_data.tenant_id
            ).first()

            if not appointment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Appointment not found"
                )

            # Check if encounter already exists for this appointment
            existing_encounter = db.query(Encounter).filter(
                Encounter.appointment_id == encounter_data.appointment_id
            ).first()

            if existing_encounter:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Encounter already exists for this appointment: {existing_encounter.id}"
                )

        # Generate FHIR encounter ID
        import uuid
        fhir_encounter_id = f"enc-{uuid.uuid4().hex[:12]}"

        # Create encounter
        encounter = Encounter(
            tenant_id=encounter_data.tenant_id,
            encounter_fhir_id=fhir_encounter_id,
            patient_id=encounter_data.patient_id,
            practitioner_id=encounter_data.practitioner_id,
            appointment_id=encounter_data.appointment_id,
            status="in-progress",
            class_code=encounter_data.class_code,
            started_at=datetime.utcnow()
        )

        db.add(encounter)

        # Update appointment if linked
        if appointment:
            appointment.encounter_id = encounter.id

        db.commit()
        db.refresh(encounter)

        logger.info(
            f"Created encounter {encounter.id} for patient {encounter_data.patient_id}"
        )

        # Publish event
        await publish_event(
            event_type=EventType.ENCOUNTER_CREATED,
            tenant_id=str(encounter_data.tenant_id),
            payload={
                "encounter_id": str(encounter.id),
                "encounter_fhir_id": fhir_encounter_id,
                "patient_id": str(encounter_data.patient_id),
                "practitioner_id": str(encounter_data.practitioner_id),
                "appointment_id": str(encounter_data.appointment_id) if encounter_data.appointment_id else None,
                "class_code": encounter_data.class_code
            },
            source_service="encounter-service"
        )

        # Also create FHIR Encounter resource
        fhir_encounter = _create_fhir_encounter(encounter, patient, practitioner)

        # Store in FHIR resources table
        from shared.database.models import FHIRResource
        fhir_resource = FHIRResource(
            tenant_id=encounter.tenant_id,
            resource_type="Encounter",
            resource_data=fhir_encounter,
            subject_id=encounter.patient_id,
            author_id=encounter.practitioner_id,
            version=1
        )
        db.add(fhir_resource)
        db.commit()

        return encounter

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating encounter: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create encounter: {str(e)}"
        )


@app.get(
    "/api/v1/encounters/{encounter_id}",
    response_model=EncounterResponse,
    tags=["Encounters"]
)
async def get_encounter(
    encounter_id: UUID,
    db: Session = Depends(get_db)
):
    """Get encounter by ID"""
    try:
        encounter = db.query(Encounter).filter(
            Encounter.id == encounter_id
        ).first()

        if not encounter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Encounter not found"
            )

        return encounter

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving encounter: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve encounter"
        )


@app.get(
    "/api/v1/encounters",
    response_model=EncounterListResponse,
    tags=["Encounters"]
)
async def list_encounters(
    patient_id: Optional[UUID] = Query(None),
    practitioner_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List encounters with filters

    Search by patient, practitioner, status, date range, etc.
    """
    try:
        query = db.query(Encounter)

        if patient_id:
            query = query.filter(Encounter.patient_id == patient_id)

        if practitioner_id:
            query = query.filter(Encounter.practitioner_id == practitioner_id)

        if status:
            query = query.filter(Encounter.status == status.lower())

        if from_date:
            from_datetime = datetime.combine(from_date, datetime.min.time())
            query = query.filter(Encounter.started_at >= from_datetime)

        if to_date:
            to_datetime = datetime.combine(to_date, datetime.max.time())
            query = query.filter(Encounter.started_at <= to_datetime)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        encounters = query.order_by(
            Encounter.started_at.desc()
        ).offset(offset).limit(page_size).all()

        has_next = (offset + page_size) < total
        has_previous = page > 1

        return EncounterListResponse(
            total=total,
            encounters=encounters,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous
        )

    except Exception as e:
        logger.error(f"Error listing encounters: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list encounters"
        )


@app.patch(
    "/api/v1/encounters/{encounter_id}",
    response_model=EncounterResponse,
    tags=["Encounters"]
)
async def update_encounter(
    encounter_id: UUID,
    encounter_update: EncounterUpdate,
    db: Session = Depends(get_db)
):
    """
    Update encounter

    Can update status, timestamps, etc.
    """
    try:
        encounter = db.query(Encounter).filter(
            Encounter.id == encounter_id
        ).first()

        if not encounter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Encounter not found"
            )

        # Update fields
        if encounter_update.status:
            encounter.status = encounter_update.status

        if encounter_update.started_at:
            encounter.started_at = encounter_update.started_at

        if encounter_update.ended_at:
            encounter.ended_at = encounter_update.ended_at

        encounter.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(encounter)

        logger.info(f"Updated encounter {encounter_id}")

        # Publish event
        await publish_event(
            event_type=EventType.ENCOUNTER_UPDATED,
            tenant_id=str(encounter.tenant_id),
            payload={
                "encounter_id": str(encounter.id),
                "patient_id": str(encounter.patient_id),
                "status": encounter.status
            },
            source_service="encounter-service"
        )

        return encounter

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating encounter: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update encounter"
        )


@app.post(
    "/api/v1/encounters/{encounter_id}/complete",
    response_model=EncounterResponse,
    tags=["Encounters"]
)
async def complete_encounter(
    encounter_id: UUID,
    complete_data: Optional[EncounterCompleteRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Complete an encounter

    Sets status to 'completed' and ended_at to now (or provided time).
    """
    try:
        encounter = db.query(Encounter).filter(
            Encounter.id == encounter_id,
            Encounter.status == "in-progress"
        ).first()

        if not encounter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="In-progress encounter not found"
            )

        encounter.status = "completed"
        encounter.ended_at = complete_data.ended_at if complete_data and complete_data.ended_at else datetime.utcnow()
        encounter.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(encounter)

        logger.info(f"Completed encounter {encounter_id}")

        # Publish event
        await publish_event(
            event_type=EventType.ENCOUNTER_COMPLETED,
            tenant_id=str(encounter.tenant_id),
            payload={
                "encounter_id": str(encounter.id),
                "patient_id": str(encounter.patient_id),
                "practitioner_id": str(encounter.practitioner_id),
                "appointment_id": str(encounter.appointment_id) if encounter.appointment_id else None,
                "duration_minutes": (
                    (encounter.ended_at - encounter.started_at).total_seconds() / 60
                ) if encounter.started_at and encounter.ended_at else None
            },
            source_service="encounter-service"
        )

        return encounter

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error completing encounter: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete encounter"
        )


# ==================== Helper Functions ====================

def _create_fhir_encounter(encounter: Encounter, patient: Patient, practitioner: Practitioner) -> dict:
    """Create FHIR R4 Encounter resource from encounter model"""

    fhir_encounter = {
        "resourceType": "Encounter",
        "id": encounter.encounter_fhir_id,
        "status": _map_status_to_fhir(encounter.status),
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": encounter.class_code,
            "display": _get_class_display(encounter.class_code)
        },
        "subject": {
            "reference": f"Patient/{patient.id}",
            "display": f"{patient.first_name} {patient.last_name}"
        },
        "participant": [
            {
                "type": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                        "code": "PPRF",
                        "display": "primary performer"
                    }]
                }],
                "individual": {
                    "reference": f"Practitioner/{practitioner.id}",
                    "display": f"Dr. {practitioner.first_name} {practitioner.last_name}"
                }
            }
        ]
    }

    if encounter.started_at:
        fhir_encounter["period"] = {
            "start": encounter.started_at.isoformat()
        }

    if encounter.ended_at:
        if "period" not in fhir_encounter:
            fhir_encounter["period"] = {}
        fhir_encounter["period"]["end"] = encounter.ended_at.isoformat()

    if encounter.appointment_id:
        fhir_encounter["appointment"] = [{
            "reference": f"Appointment/{encounter.appointment_id}"
        }]

    return fhir_encounter


def _map_status_to_fhir(status: str) -> str:
    """Map internal status to FHIR status"""
    status_map = {
        "planned": "planned",
        "in-progress": "in-progress",
        "completed": "finished",
        "cancelled": "cancelled"
    }
    return status_map.get(status, "unknown")


def _get_class_display(class_code: str) -> str:
    """Get display name for class code"""
    class_displays = {
        "AMB": "ambulatory",
        "IMP": "inpatient encounter",
        "EMER": "emergency",
        "VR": "virtual",
        "HH": "home health"
    }
    return class_displays.get(class_code, class_code)


# ==================== Startup ====================

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("Encounter Service starting up...")

    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

    logger.info("Encounter Service ready!")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006, reload=True)
