"""
Nursing Service API
Manages nursing tasks, vitals, and nursing observations
"""
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging
import os

from shared.database.connection import get_db
from shared.database.models import (
    NursingTask, NursingObservation, Patient, Admission,
    Encounter, Ward, BedAssignment, Bed
)
from shared.events.publisher import publish_event
from shared.events.types import EventType
from .schemas import (
    NursingTaskCreate, NursingTaskUpdate, NursingTaskComplete,
    NursingTaskResponse, NursingTaskListResponse,
    NursingObservationCreate, NursingObservationResponse,
    NursingObservationListResponse, VitalsChartResponse
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Nursing Service",
    description="Manages nursing tasks, vitals, and nursing observations",
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

async def create_fhir_vitals_observations(
    db: Session,
    observation_data: NursingObservationCreate,
    observation_id: UUID,
    vitals: Dict[str, Any]
) -> Dict[str, str]:
    """Create FHIR Observation resources for vital signs"""
    from shared.database.models import FHIRResource

    fhir_ids = {}
    observation_time = observation_data.observation_time or datetime.utcnow()

    # Map vital signs to LOINC codes
    vitals_mapping = {
        "temperature": {
            "code": "8310-5",
            "display": "Body temperature",
            "unit": vitals.get("temp_unit", "Cel")
        },
        "bp_systolic": {
            "code": "8480-6",
            "display": "Systolic blood pressure",
            "unit": "mm[Hg]"
        },
        "bp_diastolic": {
            "code": "8462-4",
            "display": "Diastolic blood pressure",
            "unit": "mm[Hg]"
        },
        "heart_rate": {
            "code": "8867-4",
            "display": "Heart rate",
            "unit": "/min"
        },
        "respiratory_rate": {
            "code": "9279-1",
            "display": "Respiratory rate",
            "unit": "/min"
        },
        "spo2": {
            "code": "2708-6",
            "display": "Oxygen saturation",
            "unit": "%"
        }
    }

    # Create FHIR Observation for each vital sign
    for vital_field, mapping in vitals_mapping.items():
        if vital_field in vitals and vitals[vital_field] is not None:
            fhir_obs_id = f"Observation/{observation_id}-{vital_field}"

            fhir_observation = {
                "resourceType": "Observation",
                "id": fhir_obs_id,
                "status": "final",
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                "code": "vital-signs",
                                "display": "Vital Signs"
                            }
                        ]
                    }
                ],
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": mapping["code"],
                            "display": mapping["display"]
                        }
                    ],
                    "text": mapping["display"]
                },
                "subject": {
                    "reference": f"Patient/{observation_data.patient_id}"
                },
                "encounter": {
                    "reference": f"Encounter/{observation_data.encounter_id}"
                },
                "effectiveDateTime": observation_time.isoformat(),
                "valueQuantity": {
                    "value": float(vitals[vital_field]),
                    "unit": mapping["unit"],
                    "system": "http://unitsofmeasure.org",
                    "code": mapping["unit"]
                }
            }

            fhir_resource = FHIRResource(
                tenant_id=observation_data.tenant_id,
                resource_type="Observation",
                fhir_id=fhir_obs_id,
                resource_data=fhir_observation
            )
            db.add(fhir_resource)
            fhir_ids[vital_field] = fhir_obs_id

    return fhir_ids


# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "nursing-service",
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== Nursing Task Endpoints ====================

@app.post("/api/v1/nursing/tasks", response_model=NursingTaskResponse, status_code=201)
async def create_nursing_task(
    task_data: NursingTaskCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new nursing task

    Task types: medication, vitals, procedure, education, hygiene, assessment
    """
    try:
        # Validate patient and admission
        admission = db.query(Admission).filter(
            Admission.id == task_data.admission_id,
            Admission.tenant_id == task_data.tenant_id
        ).first()

        if not admission:
            raise HTTPException(status_code=404, detail="Admission not found")

        if admission.status != "admitted":
            raise HTTPException(status_code=400, detail="Admission is not active")

        # Create nursing task
        task = NursingTask(
            tenant_id=task_data.tenant_id,
            admission_id=task_data.admission_id,
            encounter_id=task_data.encounter_id,
            patient_id=task_data.patient_id,
            bed_assignment_id=task_data.bed_assignment_id,
            ward_id=task_data.ward_id,
            created_by_user_id=task_data.created_by_user_id,
            assigned_to_user_id=task_data.assigned_to_user_id,
            task_type=task_data.task_type.lower(),
            description=task_data.description,
            priority=task_data.priority.lower(),
            due_at=task_data.due_at,
            status="open"
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        # Publish event
        await publish_event(
            EventType.NURSING_TASK_CREATED,
            {
                "task_id": str(task.id),
                "tenant_id": str(task.tenant_id),
                "patient_id": str(task.patient_id),
                "admission_id": str(task.admission_id),
                "task_type": task.task_type,
                "priority": task.priority,
                "assigned_to": str(task.assigned_to_user_id) if task.assigned_to_user_id else None,
                "due_at": task.due_at.isoformat() if task.due_at else None
            }
        )

        logger.info(f"Created nursing task {task.id} for patient {task.patient_id}")
        return task

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating nursing task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/nursing/tasks/{task_id}", response_model=NursingTaskResponse)
async def get_nursing_task(
    task_id: UUID,
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Get nursing task by ID"""
    task = db.query(NursingTask).filter(
        NursingTask.id == task_id,
        NursingTask.tenant_id == tenant_id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="Nursing task not found")

    return task


@app.get("/api/v1/nursing/tasks", response_model=NursingTaskListResponse)
async def list_nursing_tasks(
    tenant_id: UUID = Query(...),
    ward_id: Optional[UUID] = Query(None),
    patient_id: Optional[UUID] = Query(None),
    admission_id: Optional[UUID] = Query(None),
    assigned_to_user_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None, description="open, in_progress, completed, cancelled"),
    priority: Optional[str] = Query(None, description="low, normal, high, critical"),
    task_type: Optional[str] = Query(None),
    due_before: Optional[datetime] = Query(None),
    overdue_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List nursing tasks with filtering

    Filters:
    - ward_id: Filter by ward
    - patient_id: Filter by patient
    - admission_id: Filter by admission
    - assigned_to_user_id: Filter by assigned nurse
    - status: Filter by status
    - priority: Filter by priority
    - task_type: Filter by task type
    - due_before: Tasks due before this time
    - overdue_only: Only show overdue tasks
    """
    query = db.query(NursingTask).filter(NursingTask.tenant_id == tenant_id)

    # Apply filters
    if ward_id:
        query = query.filter(NursingTask.ward_id == ward_id)

    if patient_id:
        query = query.filter(NursingTask.patient_id == patient_id)

    if admission_id:
        query = query.filter(NursingTask.admission_id == admission_id)

    if assigned_to_user_id:
        query = query.filter(NursingTask.assigned_to_user_id == assigned_to_user_id)

    if status:
        query = query.filter(NursingTask.status == status.lower())

    if priority:
        query = query.filter(NursingTask.priority == priority.lower())

    if task_type:
        query = query.filter(NursingTask.task_type == task_type.lower())

    if due_before:
        query = query.filter(NursingTask.due_at <= due_before)

    if overdue_only:
        query = query.filter(
            NursingTask.due_at < datetime.utcnow(),
            NursingTask.status.in_(["open", "in_progress"])
        )

    # Get total count
    total = query.count()

    # Apply pagination and ordering
    offset = (page - 1) * page_size
    tasks = query.order_by(
        NursingTask.priority.desc(),
        NursingTask.due_at.asc()
    ).offset(offset).limit(page_size).all()

    # Calculate pagination metadata
    has_next = (offset + page_size) < total
    has_previous = page > 1

    return NursingTaskListResponse(
        total=total,
        tasks=tasks,
        page=page,
        page_size=page_size,
        has_next=has_next,
        has_previous=has_previous
    )


@app.patch("/api/v1/nursing/tasks/{task_id}", response_model=NursingTaskResponse)
async def update_nursing_task(
    task_id: UUID,
    update_data: NursingTaskUpdate,
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Update nursing task"""
    try:
        task = db.query(NursingTask).filter(
            NursingTask.id == task_id,
            NursingTask.tenant_id == tenant_id
        ).first()

        if not task:
            raise HTTPException(status_code=404, detail="Nursing task not found")

        # Validate status transitions
        if update_data.status == "completed" and task.status == "completed":
            raise HTTPException(status_code=400, detail="Task already completed")

        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(task, field, value)

        task.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(task)

        # Publish event
        await publish_event(
            EventType.NURSING_TASK_UPDATED,
            {
                "task_id": str(task.id),
                "tenant_id": str(task.tenant_id),
                "patient_id": str(task.patient_id),
                "updated_fields": list(update_dict.keys()),
                "status": task.status
            }
        )

        logger.info(f"Updated nursing task {task.id}")
        return task

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating nursing task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/nursing/tasks/{task_id}/complete", response_model=NursingTaskResponse)
async def complete_nursing_task(
    task_id: UUID,
    complete_data: NursingTaskComplete,
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Complete a nursing task"""
    try:
        task = db.query(NursingTask).filter(
            NursingTask.id == task_id,
            NursingTask.tenant_id == tenant_id
        ).first()

        if not task:
            raise HTTPException(status_code=404, detail="Nursing task not found")

        if task.status == "completed":
            raise HTTPException(status_code=400, detail="Task already completed")

        if task.status == "cancelled":
            raise HTTPException(status_code=400, detail="Cannot complete cancelled task")

        # Mark as completed
        task.status = "completed"
        task.completed_at = complete_data.completed_at or datetime.utcnow()
        task.updated_at = datetime.utcnow()

        # Store completion notes
        if complete_data.completion_notes:
            if not task.meta_data:
                task.meta_data = {}
            task.meta_data["completion_notes"] = complete_data.completion_notes

        db.commit()
        db.refresh(task)

        # Publish event
        await publish_event(
            EventType.NURSING_TASK_UPDATED,
            {
                "task_id": str(task.id),
                "tenant_id": str(task.tenant_id),
                "patient_id": str(task.patient_id),
                "status": "completed",
                "completed_at": task.completed_at.isoformat()
            }
        )

        logger.info(f"Completed nursing task {task.id}")
        return task

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error completing nursing task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Nursing Observation Endpoints ====================

@app.post("/api/v1/nursing/observations", response_model=NursingObservationResponse, status_code=201)
async def create_nursing_observation(
    observation_data: NursingObservationCreate,
    db: Session = Depends(get_db)
):
    """
    Record a nursing observation

    Observation types: vitals, pain, wound, io (intake/output), assessment

    For vitals, creates FHIR Observation resources for each vital sign.
    """
    try:
        # Validate patient and admission
        admission = db.query(Admission).filter(
            Admission.id == observation_data.admission_id,
            Admission.tenant_id == observation_data.tenant_id
        ).first()

        if not admission:
            raise HTTPException(status_code=404, detail="Admission not found")

        observation_time = observation_data.observation_time or datetime.utcnow()

        # Create nursing observation
        observation = NursingObservation(
            tenant_id=observation_data.tenant_id,
            admission_id=observation_data.admission_id,
            encounter_id=observation_data.encounter_id,
            patient_id=observation_data.patient_id,
            bed_assignment_id=observation_data.bed_assignment_id,
            observed_by_user_id=observation_data.observed_by_user_id,
            observation_type=observation_data.observation_type.lower(),
            observation_time=observation_time,
            data=observation_data.data
        )
        db.add(observation)
        db.flush()

        # Create FHIR Observations for vitals
        fhir_ids = {}
        if observation_data.observation_type.lower() == "vitals":
            fhir_ids = await create_fhir_vitals_observations(
                db, observation_data, observation.id, observation_data.data
            )
            observation.fhir_observation_ids = fhir_ids

        db.commit()
        db.refresh(observation)

        # Publish event
        await publish_event(
            EventType.NURSING_OBSERVATION_RECORDED,
            {
                "observation_id": str(observation.id),
                "tenant_id": str(observation.tenant_id),
                "patient_id": str(observation.patient_id),
                "admission_id": str(observation.admission_id),
                "observation_type": observation.observation_type,
                "observation_time": observation_time.isoformat(),
                "data": observation_data.data
            }
        )

        logger.info(f"Created nursing observation {observation.id} for patient {observation.patient_id}")
        return observation

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating nursing observation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/nursing/observations/{observation_id}", response_model=NursingObservationResponse)
async def get_nursing_observation(
    observation_id: UUID,
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Get nursing observation by ID"""
    observation = db.query(NursingObservation).filter(
        NursingObservation.id == observation_id,
        NursingObservation.tenant_id == tenant_id
    ).first()

    if not observation:
        raise HTTPException(status_code=404, detail="Nursing observation not found")

    return observation


@app.get("/api/v1/nursing/observations", response_model=NursingObservationListResponse)
async def list_nursing_observations(
    tenant_id: UUID = Query(...),
    patient_id: Optional[UUID] = Query(None),
    admission_id: Optional[UUID] = Query(None),
    observation_type: Optional[str] = Query(None, description="vitals, pain, wound, io, assessment"),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List nursing observations with filtering

    Filters:
    - patient_id: Filter by patient
    - admission_id: Filter by admission
    - observation_type: Filter by type (vitals, pain, wound, io, assessment)
    - from_date / to_date: Filter by observation time range
    """
    query = db.query(NursingObservation).filter(NursingObservation.tenant_id == tenant_id)

    # Apply filters
    if patient_id:
        query = query.filter(NursingObservation.patient_id == patient_id)

    if admission_id:
        query = query.filter(NursingObservation.admission_id == admission_id)

    if observation_type:
        query = query.filter(NursingObservation.observation_type == observation_type.lower())

    if from_date:
        query = query.filter(NursingObservation.observation_time >= from_date)

    if to_date:
        query = query.filter(NursingObservation.observation_time <= to_date)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    observations = query.order_by(
        NursingObservation.observation_time.desc()
    ).offset(offset).limit(page_size).all()

    # Calculate pagination metadata
    has_next = (offset + page_size) < total
    has_previous = page > 1

    return NursingObservationListResponse(
        total=total,
        observations=observations,
        page=page,
        page_size=page_size,
        has_next=has_next,
        has_previous=has_previous
    )


@app.get("/api/v1/nursing/observations/vitals-chart", response_model=VitalsChartResponse)
async def get_vitals_chart(
    tenant_id: UUID = Query(...),
    patient_id: UUID = Query(...),
    admission_id: Optional[UUID] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get vitals chart/trends for a patient

    Returns time-series data for vital signs to support charting.
    """
    query = db.query(NursingObservation).filter(
        NursingObservation.tenant_id == tenant_id,
        NursingObservation.patient_id == patient_id,
        NursingObservation.observation_type == "vitals"
    )

    if admission_id:
        query = query.filter(NursingObservation.admission_id == admission_id)

    # Default to last 7 days if no dates specified
    if not from_date:
        from_date = datetime.utcnow() - timedelta(days=7)

    if not to_date:
        to_date = datetime.utcnow()

    query = query.filter(
        NursingObservation.observation_time >= from_date,
        NursingObservation.observation_time <= to_date
    )

    observations = query.order_by(NursingObservation.observation_time.asc()).all()

    # Format data points
    data_points = []
    for obs in observations:
        data_point = {
            "timestamp": obs.observation_time.isoformat(),
            **obs.data
        }
        data_points.append(data_point)

    # Calculate summary statistics
    summary = {
        "total_readings": len(data_points),
        "from_date": from_date.isoformat(),
        "to_date": to_date.isoformat()
    }

    # Calculate averages for numeric vitals
    if data_points:
        numeric_fields = ["temperature", "bp_systolic", "bp_diastolic", "heart_rate", "respiratory_rate", "spo2"]
        for field in numeric_fields:
            values = [dp.get(field) for dp in data_points if dp.get(field) is not None]
            if values:
                summary[f"{field}_avg"] = sum(values) / len(values)
                summary[f"{field}_min"] = min(values)
                summary[f"{field}_max"] = max(values)

    return VitalsChartResponse(
        patient_id=patient_id,
        from_date=from_date,
        to_date=to_date,
        data_points=data_points,
        summary=summary
    )


# ==================== Root ====================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "nursing-service",
        "version": "1.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8011))
    uvicorn.run(app, host="0.0.0.0", port=port)
