"""
Synthetic Data Service - Port 8029
Privacy-safe synthetic dataset generation for development and testing
"""
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import Session, sessionmaker

from shared.database.models import (
    SyntheticDataProfile, SyntheticDataJob, SyntheticDataOutput, Tenant
)
from shared.events.types import EventType
from shared.events.publisher import publish_event
from schemas import (
    SyntheticDataProfileCreate, SyntheticDataProfileUpdate, SyntheticDataProfileResponse,
    SyntheticDataJobCreate, SyntheticDataJobResponse,
    SyntheticDataOutputResponse
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Synthetic Data Service", version="0.1.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Synthetic Data Profile Endpoints
@app.post("/api/v1/synthetic/profiles", response_model=SyntheticDataProfileResponse, status_code=201, tags=["Profiles"])
async def create_synthetic_profile(
    profile_data: SyntheticDataProfileCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create a new synthetic data generation profile"""
    # Check for duplicate code
    existing = db.query(SyntheticDataProfile).filter(and_(
        SyntheticDataProfile.tenant_id == profile_data.tenant_id,
        SyntheticDataProfile.code == profile_data.code
    )).first()
    if existing:
        raise HTTPException(status_code=400, detail="Profile code already exists")

    profile = SyntheticDataProfile(
        tenant_id=profile_data.tenant_id,
        code=profile_data.code,
        name=profile_data.name,
        description=profile_data.description,
        base_population_criteria=profile_data.base_population_criteria,
        generation_config=profile_data.generation_config,
        privacy_level=profile_data.privacy_level
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    await publish_event(EventType.SYNTHETIC_PROFILE_CREATED, {
        "profile_id": str(profile.id),
        "code": profile.code,
        "name": profile.name,
        "privacy_level": profile.privacy_level
    })

    logger.info(f"Synthetic data profile created: {profile.code}")
    return profile

@app.get("/api/v1/synthetic/profiles", response_model=List[SyntheticDataProfileResponse], tags=["Profiles"])
async def list_synthetic_profiles(
    tenant_id: Optional[UUID] = Query(None),
    privacy_level: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List all synthetic data profiles with optional filters"""
    query = db.query(SyntheticDataProfile)
    if tenant_id:
        query = query.filter(SyntheticDataProfile.tenant_id == tenant_id)
    if privacy_level:
        query = query.filter(SyntheticDataProfile.privacy_level == privacy_level)
    return query.order_by(SyntheticDataProfile.created_at.desc()).all()

@app.get("/api/v1/synthetic/profiles/{profile_id}", response_model=SyntheticDataProfileResponse, tags=["Profiles"])
async def get_synthetic_profile(profile_id: UUID, db: Session = Depends(get_db)):
    """Get synthetic data profile details"""
    profile = db.query(SyntheticDataProfile).filter(SyntheticDataProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@app.put("/api/v1/synthetic/profiles/{profile_id}", response_model=SyntheticDataProfileResponse, tags=["Profiles"])
async def update_synthetic_profile(
    profile_id: UUID,
    profile_data: SyntheticDataProfileUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Update synthetic data profile"""
    profile = db.query(SyntheticDataProfile).filter(SyntheticDataProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    update_data = profile_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)

    logger.info(f"Synthetic data profile updated: {profile.code}")
    return profile

# Synthetic Data Job Endpoints
@app.post("/api/v1/synthetic/jobs", response_model=SyntheticDataJobResponse, status_code=201, tags=["Jobs"])
async def create_synthetic_job(
    job_data: SyntheticDataJobCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create a synthetic data generation job"""
    # Verify profile exists
    profile = db.query(SyntheticDataProfile).filter(
        SyntheticDataProfile.id == job_data.synthetic_profile_id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Synthetic data profile not found")

    job = SyntheticDataJob(
        tenant_id=profile.tenant_id,
        synthetic_profile_id=job_data.synthetic_profile_id,
        target_record_count=job_data.target_record_count,
        output_format=job_data.output_format,
        status='queued',
        seed=job_data.seed,
        job_parameters=job_data.job_parameters
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    await publish_event(EventType.SYNTHETIC_JOB_CREATED, {
        "job_id": str(job.id),
        "profile_id": str(profile.id),
        "profile_code": profile.code,
        "target_record_count": job.target_record_count,
        "output_format": job.output_format
    })

    logger.info(f"Synthetic data job created: {job.id} for profile {profile.code}")
    return job

@app.get("/api/v1/synthetic/jobs", response_model=List[SyntheticDataJobResponse], tags=["Jobs"])
async def list_synthetic_jobs(
    synthetic_profile_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List synthetic data generation jobs with filters"""
    query = db.query(SyntheticDataJob)
    if synthetic_profile_id:
        query = query.filter(SyntheticDataJob.synthetic_profile_id == synthetic_profile_id)
    if status:
        query = query.filter(SyntheticDataJob.status == status)
    return query.order_by(SyntheticDataJob.created_at.desc()).all()

@app.get("/api/v1/synthetic/jobs/{job_id}", response_model=SyntheticDataJobResponse, tags=["Jobs"])
async def get_synthetic_job(job_id: UUID, db: Session = Depends(get_db)):
    """Get synthetic data job details and status"""
    job = db.query(SyntheticDataJob).filter(SyntheticDataJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Synthetic data job not found")
    return job

@app.post("/api/v1/synthetic/jobs/{job_id}/start", tags=["Jobs"])
async def start_synthetic_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Start synthetic data generation job
    In production, this would queue the job to a background worker
    """
    job = db.query(SyntheticDataJob).filter(SyntheticDataJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Synthetic data job not found")

    if job.status != 'queued':
        raise HTTPException(status_code=400, detail=f"Job cannot be started from status: {job.status}")

    job.status = 'running'
    job.started_at = datetime.utcnow()
    db.commit()

    await publish_event(EventType.SYNTHETIC_JOB_STARTED, {
        "job_id": str(job.id),
        "profile_id": str(job.synthetic_profile_id),
        "target_record_count": job.target_record_count
    })

    logger.info(f"Synthetic data job started: {job_id}")

    # In production, this would:
    # 1. Queue job to background worker (Celery, etc)
    # 2. Worker would:
    #    - Load profile configuration
    #    - Analyze base population if specified
    #    - Generate synthetic data using GAN/VAE/copula
    #    - Create output files
    #    - Update job status to 'completed'

    return {
        "message": "Synthetic data generation job started",
        "job_id": str(job_id),
        "status": job.status
    }

@app.get("/api/v1/synthetic/jobs/{job_id}/outputs", response_model=List[SyntheticDataOutputResponse], tags=["Jobs"])
async def get_job_outputs(job_id: UUID, db: Session = Depends(get_db)):
    """Get outputs from completed synthetic data job"""
    job = db.query(SyntheticDataJob).filter(SyntheticDataJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Synthetic data job not found")

    outputs = db.query(SyntheticDataOutput).filter(
        SyntheticDataOutput.synthetic_job_id == job_id
    ).all()

    return outputs

@app.get("/health", tags=["System"])
async def health_check():
    return {"service": "synthetic-data-service", "status": "healthy", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8029)
