"""
Outcomes Service API
Manages episodes, clinical outcomes, PROMs, and PREMs
"""
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import Optional, List
from uuid import UUID
import logging
import os

from shared.database.connection import get_db
from shared.database.models import Episode, Outcome, PROM, PREM, Patient, Encounter, Admission
from shared.events.publisher import publish_event
from shared.events.types import EventType
from .schemas import (
    EpisodeCreate, EpisodeUpdate, EpisodeResponse, EpisodeListResponse,
    OutcomeCreate, OutcomeResponse, OutcomeListResponse,
    PROMCreate, PROMResponse, PROMListResponse,
    PREMCreate, PREMResponse, PREMListResponse
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Outcomes Service",
    description="Manages episodes, clinical outcomes, PROMs, and PREMs",
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

async def create_fhir_episode_of_care(
    db: Session,
    episode_data: EpisodeCreate,
    episode_id: UUID
) -> str:
    """Create FHIR EpisodeOfCare"""
    from shared.database.models import FHIRResource

    fhir_id = f"EpisodeOfCare/{episode_id}"

    # Determine type based on care_type
    type_mapping = {
        "OPD": "outpatient",
        "IPD": "inpatient",
        "OPD_IPD": "mixed",
        "DAY_CARE": "daycare"
    }

    fhir_episode = {
        "resourceType": "EpisodeOfCare",
        "id": str(episode_id),
        "status": "active",
        "type": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/episodeofcare-type",
                        "code": type_mapping.get(episode_data.care_type, "other"),
                        "display": episode_data.care_type
                    }
                ]
            }
        ],
        "patient": {
            "reference": f"Patient/{episode_data.patient_id}"
        },
        "period": {
            "start": (episode_data.started_at or datetime.utcnow()).isoformat()
        }
    }

    if episode_data.specialty:
        fhir_episode["type"][0]["text"] = episode_data.specialty

    fhir_resource = FHIRResource(
        tenant_id=episode_data.tenant_id,
        resource_type="EpisodeOfCare",
        fhir_id=fhir_id,
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
        "service": "outcomes-service",
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== Episode Endpoints ====================

@app.post("/api/v1/outcomes/episodes", response_model=EpisodeResponse, status_code=201)
async def create_episode(
    episode_data: EpisodeCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new episode for outcomes tracking

    Episodes unify OPD and IPD care for longitudinal outcome tracking.
    """
    try:
        # Validate patient exists
        patient = db.query(Patient).filter(
            Patient.id == episode_data.patient_id,
            Patient.tenant_id == episode_data.tenant_id
        ).first()

        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        # Create episode
        episode = Episode(
            tenant_id=episode_data.tenant_id,
            patient_id=episode_data.patient_id,
            index_encounter_id=episode_data.index_encounter_id,
            index_admission_id=episode_data.index_admission_id,
            care_type=episode_data.care_type.upper(),
            specialty=episode_data.specialty,
            primary_condition_code=episode_data.primary_condition_code,
            started_at=episode_data.started_at or datetime.utcnow(),
            status="active"
        )
        db.add(episode)
        db.flush()

        # Create FHIR EpisodeOfCare
        fhir_id = await create_fhir_episode_of_care(db, episode_data, episode.id)
        episode.episode_of_care_fhir_id = fhir_id

        db.commit()
        db.refresh(episode)

        # Publish event
        await publish_event(
            EventType.EPISODE_CREATED,
            {
                "episode_id": str(episode.id),
                "tenant_id": str(episode.tenant_id),
                "patient_id": str(episode.patient_id),
                "care_type": episode.care_type,
                "specialty": episode.specialty
            }
        )

        logger.info(f"Created episode {episode.id} for patient {episode.patient_id}")
        return episode

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating episode: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/outcomes/episodes/{episode_id}", response_model=EpisodeResponse)
async def get_episode(
    episode_id: UUID,
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Get episode by ID"""
    episode = db.query(Episode).filter(
        Episode.id == episode_id,
        Episode.tenant_id == tenant_id
    ).first()

    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    return episode


@app.get("/api/v1/outcomes/episodes", response_model=EpisodeListResponse)
async def list_episodes(
    tenant_id: UUID = Query(...),
    patient_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None, description="active, completed, abandoned"),
    care_type: Optional[str] = Query(None, description="OPD, IPD, OPD_IPD, DAY_CARE"),
    specialty: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List episodes with filtering"""
    query = db.query(Episode).filter(Episode.tenant_id == tenant_id)

    if patient_id:
        query = query.filter(Episode.patient_id == patient_id)

    if status:
        query = query.filter(Episode.status == status.lower())

    if care_type:
        query = query.filter(Episode.care_type == care_type.upper())

    if specialty:
        query = query.filter(Episode.specialty == specialty.upper())

    if from_date:
        query = query.filter(Episode.started_at >= from_date)

    if to_date:
        query = query.filter(Episode.started_at <= to_date)

    total = query.count()
    offset = (page - 1) * page_size
    episodes = query.order_by(Episode.started_at.desc()).offset(offset).limit(page_size).all()

    has_next = (offset + page_size) < total
    has_previous = page > 1

    return EpisodeListResponse(
        total=total,
        episodes=episodes,
        page=page,
        page_size=page_size,
        has_next=has_next,
        has_previous=has_previous
    )


@app.patch("/api/v1/outcomes/episodes/{episode_id}", response_model=EpisodeResponse)
async def update_episode(
    episode_id: UUID,
    update_data: EpisodeUpdate,
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Update episode"""
    try:
        episode = db.query(Episode).filter(
            Episode.id == episode_id,
            Episode.tenant_id == tenant_id
        ).first()

        if not episode:
            raise HTTPException(status_code=404, detail="Episode not found")

        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(episode, field, value)

        episode.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(episode)

        # Publish event
        await publish_event(
            EventType.EPISODE_UPDATED,
            {
                "episode_id": str(episode.id),
                "tenant_id": str(episode.tenant_id),
                "patient_id": str(episode.patient_id),
                "updated_fields": list(update_dict.keys()),
                "status": episode.status
            }
        )

        logger.info(f"Updated episode {episode.id}")
        return episode

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating episode: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Outcome Endpoints ====================

@app.post("/api/v1/outcomes/episodes/{episode_id}/outcomes", response_model=OutcomeResponse, status_code=201)
async def create_outcome(
    episode_id: UUID,
    outcome_data: OutcomeCreate,
    db: Session = Depends(get_db)
):
    """Create an outcome for an episode"""
    try:
        # Validate episode exists
        episode = db.query(Episode).filter(
            Episode.id == episode_id,
            Episode.tenant_id == outcome_data.tenant_id
        ).first()

        if not episode:
            raise HTTPException(status_code=404, detail="Episode not found")

        # Create outcome
        outcome = Outcome(
            tenant_id=outcome_data.tenant_id,
            episode_id=episode_id,
            outcome_type=outcome_data.outcome_type,
            outcome_subtype=outcome_data.outcome_subtype,
            value=outcome_data.value,
            numeric_value=outcome_data.numeric_value,
            unit=outcome_data.unit,
            occurred_at=outcome_data.occurred_at or datetime.utcnow(),
            derived_from=outcome_data.derived_from,
            source_event_id=outcome_data.source_event_id,
            notes=outcome_data.notes
        )
        db.add(outcome)
        db.commit()
        db.refresh(outcome)

        # Publish event
        await publish_event(
            EventType.OUTCOME_RECORDED,
            {
                "outcome_id": str(outcome.id),
                "episode_id": str(episode_id),
                "tenant_id": str(outcome.tenant_id),
                "outcome_type": outcome.outcome_type,
                "outcome_subtype": outcome.outcome_subtype,
                "value": outcome.value
            }
        )

        logger.info(f"Recorded outcome {outcome.id} for episode {episode_id}")
        return outcome

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating outcome: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/outcomes/episodes/{episode_id}/outcomes", response_model=OutcomeListResponse)
async def list_episode_outcomes(
    episode_id: UUID,
    tenant_id: UUID = Query(...),
    outcome_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List outcomes for an episode"""
    query = db.query(Outcome).filter(
        Outcome.episode_id == episode_id,
        Outcome.tenant_id == tenant_id
    )

    if outcome_type:
        query = query.filter(Outcome.outcome_type == outcome_type)

    total = query.count()
    offset = (page - 1) * page_size
    outcomes = query.order_by(Outcome.occurred_at.desc()).offset(offset).limit(page_size).all()

    has_next = (offset + page_size) < total
    has_previous = page > 1

    return OutcomeListResponse(
        total=total,
        outcomes=outcomes,
        page=page,
        page_size=page_size,
        has_next=has_next,
        has_previous=has_previous
    )


@app.get("/api/v1/outcomes/outcomes", response_model=OutcomeListResponse)
async def list_outcomes(
    tenant_id: UUID = Query(...),
    outcome_type: Optional[str] = Query(None),
    specialty: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List all outcomes with filtering"""
    query = db.query(Outcome).filter(Outcome.tenant_id == tenant_id)

    if outcome_type:
        query = query.filter(Outcome.outcome_type == outcome_type)

    if specialty:
        query = query.join(Episode).filter(Episode.specialty == specialty.upper())

    if from_date:
        query = query.filter(Outcome.occurred_at >= from_date)

    if to_date:
        query = query.filter(Outcome.occurred_at <= to_date)

    total = query.count()
    offset = (page - 1) * page_size
    outcomes = query.order_by(Outcome.occurred_at.desc()).offset(offset).limit(page_size).all()

    has_next = (offset + page_size) < total
    has_previous = page > 1

    return OutcomeListResponse(
        total=total,
        outcomes=outcomes,
        page=page,
        page_size=page_size,
        has_next=has_next,
        has_previous=has_previous
    )


# ==================== PROM Endpoints ====================

@app.post("/api/v1/outcomes/episodes/{episode_id}/proms", response_model=PROMResponse, status_code=201)
async def create_prom(
    episode_id: UUID,
    prom_data: PROMCreate,
    db: Session = Depends(get_db)
):
    """Create a PROM for an episode"""
    try:
        # Validate episode exists
        episode = db.query(Episode).filter(
            Episode.id == episode_id,
            Episode.tenant_id == prom_data.tenant_id
        ).first()

        if not episode:
            raise HTTPException(status_code=404, detail="Episode not found")

        # Create PROM
        prom = PROM(
            tenant_id=prom_data.tenant_id,
            episode_id=episode_id,
            patient_id=prom_data.patient_id,
            instrument_code=prom_data.instrument_code,
            version=prom_data.version,
            responses=prom_data.responses,
            score=prom_data.score,
            completed_at=prom_data.completed_at or datetime.utcnow(),
            mode=prom_data.mode
        )
        db.add(prom)
        db.commit()
        db.refresh(prom)

        # Publish event
        await publish_event(
            EventType.PROM_COMPLETED,
            {
                "prom_id": str(prom.id),
                "episode_id": str(episode_id),
                "tenant_id": str(prom.tenant_id),
                "patient_id": str(prom.patient_id),
                "instrument_code": prom.instrument_code,
                "score": prom.score
            }
        )

        logger.info(f"Recorded PROM {prom.id} for episode {episode_id}")
        return prom

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating PROM: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/outcomes/episodes/{episode_id}/proms", response_model=PROMListResponse)
async def list_episode_proms(
    episode_id: UUID,
    tenant_id: UUID = Query(...),
    instrument_code: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List PROMs for an episode"""
    query = db.query(PROM).filter(
        PROM.episode_id == episode_id,
        PROM.tenant_id == tenant_id
    )

    if instrument_code:
        query = query.filter(PROM.instrument_code == instrument_code)

    total = query.count()
    offset = (page - 1) * page_size
    proms = query.order_by(PROM.completed_at.desc()).offset(offset).limit(page_size).all()

    has_next = (offset + page_size) < total
    has_previous = page > 1

    return PROMListResponse(
        total=total,
        proms=proms,
        page=page,
        page_size=page_size,
        has_next=has_next,
        has_previous=has_previous
    )


# ==================== PREM Endpoints ====================

@app.post("/api/v1/outcomes/episodes/{episode_id}/prems", response_model=PREMResponse, status_code=201)
async def create_prem(
    episode_id: UUID,
    prem_data: PREMCreate,
    db: Session = Depends(get_db)
):
    """Create a PREM for an episode"""
    try:
        # Validate episode exists
        episode = db.query(Episode).filter(
            Episode.id == episode_id,
            Episode.tenant_id == prem_data.tenant_id
        ).first()

        if not episode:
            raise HTTPException(status_code=404, detail="Episode not found")

        # Create PREM
        prem = PREM(
            tenant_id=prem_data.tenant_id,
            episode_id=episode_id,
            patient_id=prem_data.patient_id,
            instrument_code=prem_data.instrument_code,
            responses=prem_data.responses,
            score=prem_data.score,
            completed_at=prem_data.completed_at or datetime.utcnow(),
            mode=prem_data.mode
        )
        db.add(prem)
        db.commit()
        db.refresh(prem)

        # Publish event
        await publish_event(
            EventType.PREM_COMPLETED,
            {
                "prem_id": str(prem.id),
                "episode_id": str(episode_id),
                "tenant_id": str(prem.tenant_id),
                "patient_id": str(prem.patient_id),
                "instrument_code": prem.instrument_code,
                "score": prem.score
            }
        )

        logger.info(f"Recorded PREM {prem.id} for episode {episode_id}")
        return prem

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating PREM: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/outcomes/episodes/{episode_id}/prems", response_model=PREMListResponse)
async def list_episode_prems(
    episode_id: UUID,
    tenant_id: UUID = Query(...),
    instrument_code: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List PREMs for an episode"""
    query = db.query(PREM).filter(
        PREM.episode_id == episode_id,
        PREM.tenant_id == tenant_id
    )

    if instrument_code:
        query = query.filter(PREM.instrument_code == instrument_code)

    total = query.count()
    offset = (page - 1) * page_size
    prems = query.order_by(PREM.completed_at.desc()).offset(offset).limit(page_size).all()

    has_next = (offset + page_size) < total
    has_previous = page > 1

    return PREMListResponse(
        total=total,
        prems=prems,
        page=page,
        page_size=page_size,
        has_next=has_next,
        has_previous=has_previous
    )


# ==================== Root ====================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "outcomes-service",
        "version": "1.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8014))
    uvicorn.run(app, host="0.0.0.0", port=port)
