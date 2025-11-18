"""
Admission Service API
Manages inpatient (IPD) admissions, discharges, and admission workflows
"""
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, case, and_, or_, extract
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID
import logging
import os

from shared.database.connection import get_db
from shared.database.models import (
    Admission, Patient, Practitioner, Encounter, BedAssignment, Bed, Ward
)
from shared.events.publisher import publish_event
from shared.events.types import EventType
from .schemas import (
    AdmissionCreate, AdmissionUpdate, AdmissionDischarge, AdmissionCancel,
    AdmissionLinkBed, AdmissionResponse, AdmissionWithDetails,
    AdmissionListResponse, AdmissionStats
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Admission Service",
    description="Manages inpatient (IPD) admissions and discharges",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Helper Functions ====================

async def create_fhir_encounter(
    db: Session,
    admission_data: AdmissionCreate,
    admission_id: UUID
) -> UUID:
    """Create FHIR Encounter for inpatient admission"""
    from shared.database.models import FHIRResource

    # Create IPD Encounter
    encounter = Encounter(
        tenant_id=admission_data.tenant_id,
        patient_id=admission_data.patient_id,
        practitioner_id=admission_data.primary_practitioner_id,
        class_code="IMP",  # Inpatient
        status="in-progress",
        period_start=admission_data.admitted_at or datetime.utcnow(),
        service_type=admission_data.admitting_department,
        reason_text=admission_data.admission_reason
    )
    db.add(encounter)
    db.flush()

    # Create FHIR Encounter resource
    fhir_encounter = {
        "resourceType": "Encounter",
        "id": str(encounter.id),
        "status": "in-progress",
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "IMP",
            "display": "inpatient encounter"
        },
        "subject": {
            "reference": f"Patient/{admission_data.patient_id}"
        },
        "participant": [
            {
                "individual": {
                    "reference": f"Practitioner/{admission_data.primary_practitioner_id}"
                }
            }
        ],
        "period": {
            "start": (admission_data.admitted_at or datetime.utcnow()).isoformat()
        },
        "reasonCode": [
            {
                "text": admission_data.admission_reason or "Inpatient admission"
            }
        ]
    }

    fhir_resource = FHIRResource(
        tenant_id=admission_data.tenant_id,
        resource_type="Encounter",
        fhir_id=str(encounter.id),
        resource_data=fhir_encounter
    )
    db.add(fhir_resource)

    return encounter.id


async def create_fhir_episode_of_care(
    db: Session,
    admission_data: AdmissionCreate,
    admission_id: UUID,
    encounter_id: UUID
) -> str:
    """Create FHIR EpisodeOfCare for admission"""
    from shared.database.models import FHIRResource

    fhir_id = f"EpisodeOfCare/{admission_id}"

    fhir_episode = {
        "resourceType": "EpisodeOfCare",
        "id": str(admission_id),
        "status": "active",
        "type": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/episodeofcare-type",
                        "code": "inpatient",
                        "display": "Inpatient"
                    }
                ]
            }
        ],
        "patient": {
            "reference": f"Patient/{admission_data.patient_id}"
        },
        "managingOrganization": {
            "reference": f"Organization/{admission_data.tenant_id}"
        },
        "period": {
            "start": (admission_data.admitted_at or datetime.utcnow()).isoformat()
        },
        "careManager": {
            "reference": f"Practitioner/{admission_data.primary_practitioner_id}"
        }
    }

    fhir_resource = FHIRResource(
        tenant_id=admission_data.tenant_id,
        resource_type="EpisodeOfCare",
        fhir_id=str(admission_id),
        resource_data=fhir_episode
    )
    db.add(fhir_resource)

    return fhir_id


# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "admission-service",
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== Admission Endpoints ====================

@app.post("/api/v1/admissions", response_model=AdmissionResponse, status_code=201)
async def create_admission(
    admission_data: AdmissionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new inpatient admission

    Workflow:
    1. Validate patient and practitioner exist
    2. Create IPD Encounter (FHIR)
    3. Create EpisodeOfCare (FHIR)
    4. Create admission record
    5. Emit Admission.Created event
    """
    try:
        # Validate patient exists
        patient = db.query(Patient).filter(
            Patient.id == admission_data.patient_id,
            Patient.tenant_id == admission_data.tenant_id
        ).first()

        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        # Validate practitioner exists
        practitioner = db.query(Practitioner).filter(
            Practitioner.id == admission_data.primary_practitioner_id,
            Practitioner.tenant_id == admission_data.tenant_id
        ).first()

        if not practitioner:
            raise HTTPException(status_code=404, detail="Practitioner not found")

        # Check for active admissions
        existing_admission = db.query(Admission).filter(
            Admission.patient_id == admission_data.patient_id,
            Admission.tenant_id == admission_data.tenant_id,
            Admission.status == "admitted"
        ).first()

        if existing_admission:
            raise HTTPException(
                status_code=409,
                detail="Patient already has an active admission"
            )

        # Create FHIR Encounter
        admission_id = None  # Temporary
        encounter_id = await create_fhir_encounter(db, admission_data, admission_id)

        # Create admission record
        admission = Admission(
            tenant_id=admission_data.tenant_id,
            patient_id=admission_data.patient_id,
            primary_practitioner_id=admission_data.primary_practitioner_id,
            admitting_department=admission_data.admitting_department,
            admission_type=admission_data.admission_type.lower(),
            admission_reason=admission_data.admission_reason,
            source_type=admission_data.source_type.upper() if admission_data.source_type else None,
            source_appointment_id=admission_data.source_appointment_id,
            encounter_id=encounter_id,
            status="admitted",
            admitted_at=admission_data.admitted_at or datetime.utcnow()
        )
        db.add(admission)
        db.flush()

        # Create FHIR EpisodeOfCare
        episode_fhir_id = await create_fhir_episode_of_care(
            db, admission_data, admission.id, encounter_id
        )
        admission.episode_of_care_fhir_id = episode_fhir_id

        db.commit()
        db.refresh(admission)

        # Publish event
        await publish_event(
            EventType.ADMISSION_CREATED,
            {
                "admission_id": str(admission.id),
                "tenant_id": str(admission.tenant_id),
                "patient_id": str(admission.patient_id),
                "practitioner_id": str(admission.primary_practitioner_id),
                "encounter_id": str(admission.encounter_id),
                "admission_type": admission.admission_type,
                "admitted_at": admission.admitted_at.isoformat(),
                "department": admission.admitting_department
            }
        )

        logger.info(f"Created admission {admission.id} for patient {admission.patient_id}")
        return admission

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating admission: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/admissions/{admission_id}", response_model=AdmissionResponse)
async def get_admission(
    admission_id: UUID,
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Get admission by ID"""
    admission = db.query(Admission).filter(
        Admission.id == admission_id,
        Admission.tenant_id == tenant_id
    ).first()

    if not admission:
        raise HTTPException(status_code=404, detail="Admission not found")

    return admission


@app.get("/api/v1/admissions", response_model=AdmissionListResponse)
async def list_admissions(
    tenant_id: UUID = Query(...),
    patient_id: Optional[UUID] = Query(None),
    primary_practitioner_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None, description="admitted, discharged, cancelled"),
    admission_type: Optional[str] = Query(None, description="elective, emergency, transfer"),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List admissions with filtering

    Filters:
    - patient_id: Filter by patient
    - primary_practitioner_id: Filter by admitting doctor
    - status: Filter by status (admitted, discharged, cancelled)
    - admission_type: Filter by type (elective, emergency, transfer)
    - from_date / to_date: Filter by admitted_at range
    """
    query = db.query(Admission).filter(Admission.tenant_id == tenant_id)

    # Apply filters
    if patient_id:
        query = query.filter(Admission.patient_id == patient_id)

    if primary_practitioner_id:
        query = query.filter(Admission.primary_practitioner_id == primary_practitioner_id)

    if status:
        query = query.filter(Admission.status == status.lower())

    if admission_type:
        query = query.filter(Admission.admission_type == admission_type.lower())

    if from_date:
        query = query.filter(Admission.admitted_at >= from_date)

    if to_date:
        query = query.filter(Admission.admitted_at <= to_date)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    admissions = query.order_by(Admission.admitted_at.desc()).offset(offset).limit(page_size).all()

    # Calculate pagination metadata
    has_next = (offset + page_size) < total
    has_previous = page > 1

    return AdmissionListResponse(
        total=total,
        admissions=admissions,
        page=page,
        page_size=page_size,
        has_next=has_next,
        has_previous=has_previous
    )


@app.patch("/api/v1/admissions/{admission_id}", response_model=AdmissionResponse)
async def update_admission(
    admission_id: UUID,
    update_data: AdmissionUpdate,
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Update admission details"""
    try:
        admission = db.query(Admission).filter(
            Admission.id == admission_id,
            Admission.tenant_id == tenant_id
        ).first()

        if not admission:
            raise HTTPException(status_code=404, detail="Admission not found")

        # Validate status transitions
        if update_data.status:
            if admission.status == "discharged" and update_data.status != "discharged":
                raise HTTPException(
                    status_code=400,
                    detail="Cannot change status of discharged admission"
                )

            if admission.status == "cancelled":
                raise HTTPException(
                    status_code=400,
                    detail="Cannot modify cancelled admission"
                )

        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(admission, field, value)

        admission.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(admission)

        # Publish event
        await publish_event(
            EventType.ADMISSION_UPDATED,
            {
                "admission_id": str(admission.id),
                "tenant_id": str(admission.tenant_id),
                "patient_id": str(admission.patient_id),
                "updated_fields": list(update_dict.keys()),
                "status": admission.status
            }
        )

        logger.info(f"Updated admission {admission.id}")
        return admission

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating admission: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/admissions/{admission_id}/discharge", response_model=AdmissionResponse)
async def discharge_patient(
    admission_id: UUID,
    discharge_data: AdmissionDischarge,
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """
    Discharge a patient from admission

    Workflow:
    1. Validate admission is active
    2. End all active bed assignments
    3. Update admission status to discharged
    4. Update FHIR Encounter status to finished
    5. Emit Admission.Discharged event
    """
    try:
        admission = db.query(Admission).filter(
            Admission.id == admission_id,
            Admission.tenant_id == tenant_id
        ).first()

        if not admission:
            raise HTTPException(status_code=404, detail="Admission not found")

        if admission.status == "discharged":
            raise HTTPException(status_code=400, detail="Admission already discharged")

        if admission.status == "cancelled":
            raise HTTPException(status_code=400, detail="Cannot discharge cancelled admission")

        # End all active bed assignments
        active_assignments = db.query(BedAssignment).filter(
            BedAssignment.admission_id == admission_id,
            BedAssignment.status == "active"
        ).all()

        discharged_time = discharge_data.discharged_at or datetime.utcnow()

        for assignment in active_assignments:
            assignment.end_time = discharged_time
            assignment.status = "discharged"

            # Update bed status
            bed = db.query(Bed).filter(Bed.id == assignment.bed_id).first()
            if bed:
                bed.status = "cleaning"

        # Update admission
        admission.status = "discharged"
        admission.discharged_at = discharged_time
        admission.updated_at = datetime.utcnow()

        # Store discharge details in metadata
        if not admission.meta_data:
            admission.meta_data = {}

        admission.meta_data["discharge"] = {
            "reason": discharge_data.discharge_reason,
            "disposition": discharge_data.discharge_disposition,
            "summary": discharge_data.discharge_summary,
            "discharged_at": discharged_time.isoformat()
        }

        # Update FHIR Encounter
        encounter = db.query(Encounter).filter(
            Encounter.id == admission.encounter_id
        ).first()

        if encounter:
            encounter.status = "finished"
            encounter.period_end = discharged_time

        db.commit()
        db.refresh(admission)

        # Publish event
        await publish_event(
            EventType.ADMISSION_DISCHARGED,
            {
                "admission_id": str(admission.id),
                "tenant_id": str(admission.tenant_id),
                "patient_id": str(admission.patient_id),
                "discharged_at": discharged_time.isoformat(),
                "disposition": discharge_data.discharge_disposition,
                "beds_released": len(active_assignments)
            }
        )

        logger.info(f"Discharged admission {admission.id}")
        return admission

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error discharging admission: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/admissions/{admission_id}/cancel", response_model=AdmissionResponse)
async def cancel_admission(
    admission_id: UUID,
    cancel_data: AdmissionCancel,
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """
    Cancel a planned admission

    Used for admissions that were scheduled but not completed.
    """
    try:
        admission = db.query(Admission).filter(
            Admission.id == admission_id,
            Admission.tenant_id == tenant_id
        ).first()

        if not admission:
            raise HTTPException(status_code=404, detail="Admission not found")

        if admission.status == "discharged":
            raise HTTPException(status_code=400, detail="Cannot cancel discharged admission")

        if admission.status == "cancelled":
            raise HTTPException(status_code=400, detail="Admission already cancelled")

        # Cancel any bed assignments
        active_assignments = db.query(BedAssignment).filter(
            BedAssignment.admission_id == admission_id,
            BedAssignment.status == "active"
        ).all()

        cancelled_time = cancel_data.cancelled_at or datetime.utcnow()

        for assignment in active_assignments:
            assignment.end_time = cancelled_time
            assignment.status = "cancelled"

            # Release bed
            bed = db.query(Bed).filter(Bed.id == assignment.bed_id).first()
            if bed:
                bed.status = "available"

        # Update admission
        admission.status = "cancelled"
        admission.updated_at = datetime.utcnow()

        # Store cancellation details
        if not admission.meta_data:
            admission.meta_data = {}

        admission.meta_data["cancellation"] = {
            "reason": cancel_data.cancel_reason,
            "cancelled_at": cancelled_time.isoformat()
        }

        # Update FHIR Encounter
        encounter = db.query(Encounter).filter(
            Encounter.id == admission.encounter_id
        ).first()

        if encounter:
            encounter.status = "cancelled"

        db.commit()
        db.refresh(admission)

        # Publish event
        await publish_event(
            EventType.ADMISSION_CANCELLED,
            {
                "admission_id": str(admission.id),
                "tenant_id": str(admission.tenant_id),
                "patient_id": str(admission.patient_id),
                "cancel_reason": cancel_data.cancel_reason,
                "cancelled_at": cancelled_time.isoformat()
            }
        )

        logger.info(f"Cancelled admission {admission.id}")
        return admission

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error cancelling admission: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/admissions/{admission_id}/link-bed-assignment")
async def link_bed_assignment(
    admission_id: UUID,
    link_data: AdmissionLinkBed,
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """
    Link an existing bed assignment to an admission

    Used when bed assignment is created separately and needs to be linked.
    """
    try:
        # Validate admission exists
        admission = db.query(Admission).filter(
            Admission.id == admission_id,
            Admission.tenant_id == tenant_id
        ).first()

        if not admission:
            raise HTTPException(status_code=404, detail="Admission not found")

        # Validate bed assignment exists
        bed_assignment = db.query(BedAssignment).filter(
            BedAssignment.id == link_data.bed_assignment_id,
            BedAssignment.tenant_id == tenant_id
        ).first()

        if not bed_assignment:
            raise HTTPException(status_code=404, detail="Bed assignment not found")

        # Link bed assignment to admission
        bed_assignment.admission_id = admission_id

        db.commit()

        logger.info(f"Linked bed assignment {bed_assignment.id} to admission {admission_id}")

        return {
            "message": "Bed assignment linked successfully",
            "admission_id": str(admission_id),
            "bed_assignment_id": str(link_data.bed_assignment_id)
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error linking bed assignment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/admissions/stats/overview", response_model=AdmissionStats)
async def get_admission_stats(
    tenant_id: UUID = Query(...),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get admission statistics for a time period

    Returns:
    - Total admissions
    - Active admissions
    - Discharged today
    - Average length of stay
    - Admission type breakdown
    - Department breakdown
    """
    query = db.query(Admission).filter(Admission.tenant_id == tenant_id)

    if from_date:
        query = query.filter(Admission.admitted_at >= from_date)

    if to_date:
        query = query.filter(Admission.admitted_at <= to_date)

    # Total admissions
    total_admissions = query.count()

    # Active admissions
    active_admissions = query.filter(Admission.status == "admitted").count()

    # Discharged today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    discharged_today = db.query(Admission).filter(
        Admission.tenant_id == tenant_id,
        Admission.status == "discharged",
        Admission.discharged_at >= today_start,
        Admission.discharged_at < today_end
    ).count()

    # Average length of stay (for discharged admissions)
    discharged_admissions = query.filter(
        Admission.status == "discharged",
        Admission.discharged_at.isnot(None)
    ).all()

    if discharged_admissions:
        total_los = sum([
            (adm.discharged_at - adm.admitted_at).days
            for adm in discharged_admissions
        ])
        avg_los = total_los / len(discharged_admissions)
    else:
        avg_los = None

    # Admission type breakdown
    type_breakdown = db.query(
        Admission.admission_type,
        func.count(Admission.id).label("count")
    ).filter(
        Admission.tenant_id == tenant_id
    ).group_by(Admission.admission_type).all()

    admission_type_breakdown = {
        row.admission_type: row.count for row in type_breakdown
    }

    # Department breakdown
    dept_breakdown = db.query(
        Admission.admitting_department,
        func.count(Admission.id).label("count")
    ).filter(
        Admission.tenant_id == tenant_id,
        Admission.admitting_department.isnot(None)
    ).group_by(Admission.admitting_department).all()

    department_breakdown = {
        row.admitting_department: row.count for row in dept_breakdown
    }

    return AdmissionStats(
        total_admissions=total_admissions,
        active_admissions=active_admissions,
        discharged_today=discharged_today,
        average_length_of_stay_days=avg_los,
        admission_type_breakdown=admission_type_breakdown,
        department_breakdown=department_breakdown
    )


# ==================== Root ====================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "admission-service",
        "version": "1.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8010))
    uvicorn.run(app, host="0.0.0.0", port=port)
