"""
De-identification Service - Port 8025
Manages PHI removal, pseudonymization, and privacy-safe research data
"""
import logging
import hashlib
import secrets
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import Session, sessionmaker

from shared.database.models import (
    DeidConfig, PseudoIdSpace, PseudoIdMapping, DeidJob, DeidJobOutput, Tenant, User
)
from shared.events.types import EventType
from shared.events.publisher import publish_event
from schemas import (
    DeidConfigCreate, DeidConfigResponse,
    PseudoIdSpaceCreate, PseudoIdSpaceResponse,
    DeidJobCreate, DeidJobResponse, DeidJobOutputResponse
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="De-identification Service", version="0.1.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Config Endpoints
@app.post("/api/v1/deid/configs", response_model=DeidConfigResponse, status_code=201, tags=["Configs"])
async def create_deid_config(config_data: DeidConfigCreate, db: Session = Depends(get_db), current_user_id: UUID = None):
    existing = db.query(DeidConfig).filter(and_(
        DeidConfig.tenant_id == config_data.tenant_id,
        DeidConfig.code == config_data.code
    )).first()
    if existing:
        raise HTTPException(status_code=400, detail="Config code already exists")

    config = DeidConfig(
        tenant_id=config_data.tenant_id,
        code=config_data.code,
        name=config_data.name,
        description=config_data.description,
        mode=config_data.mode,
        rules=config_data.rules
    )
    db.add(config)
    db.commit()
    db.refresh(config)

    await publish_event(EventType.DEID_CONFIG_CREATED, {
        "config_id": str(config.id),
        "code": config.code,
        "mode": config.mode
    })

    logger.info(f"De-id config created: {config.code}")
    return config

@app.get("/api/v1/deid/configs", response_model=List[DeidConfigResponse], tags=["Configs"])
async def list_deid_configs(tenant_id: Optional[UUID] = Query(None), db: Session = Depends(get_db)):
    query = db.query(DeidConfig)
    if tenant_id:
        query = query.filter(DeidConfig.tenant_id == tenant_id)
    return query.all()

@app.get("/api/v1/deid/configs/{config_id}", response_model=DeidConfigResponse, tags=["Configs"])
async def get_deid_config(config_id: UUID, db: Session = Depends(get_db)):
    config = db.query(DeidConfig).filter(DeidConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return config

# Pseudo ID Space Endpoints
@app.post("/api/v1/deid/pseudo-spaces", response_model=PseudoIdSpaceResponse, status_code=201, tags=["Pseudo ID"])
async def create_pseudo_space(space_data: PseudoIdSpaceCreate, db: Session = Depends(get_db), current_user_id: UUID = None):
    existing = db.query(PseudoIdSpace).filter(and_(
        PseudoIdSpace.tenant_id == space_data.tenant_id,
        PseudoIdSpace.code == space_data.code
    )).first()
    if existing:
        raise HTTPException(status_code=400, detail="Pseudo space code already exists")

    space = PseudoIdSpace(
        tenant_id=space_data.tenant_id,
        code=space_data.code,
        name=space_data.name,
        scope=space_data.scope,
        is_active=True
    )
    db.add(space)
    db.commit()
    db.refresh(space)

    logger.info(f"Pseudo ID space created: {space.code}")
    return space

@app.get("/api/v1/deid/pseudo-spaces", response_model=List[PseudoIdSpaceResponse], tags=["Pseudo ID"])
async def list_pseudo_spaces(tenant_id: Optional[UUID] = Query(None), db: Session = Depends(get_db)):
    query = db.query(PseudoIdSpace)
    if tenant_id:
        query = query.filter(PseudoIdSpace.tenant_id == tenant_id)
    return query.all()

@app.get("/api/v1/deid/pseudo-spaces/{space_id}", response_model=PseudoIdSpaceResponse, tags=["Pseudo ID"])
async def get_pseudo_space(space_id: UUID, db: Session = Depends(get_db)):
    space = db.query(PseudoIdSpace).filter(PseudoIdSpace.id == space_id).first()
    if not space:
        raise HTTPException(status_code=404, detail="Pseudo space not found")
    return space

# Job Endpoints
@app.post("/api/v1/deid/jobs", response_model=DeidJobResponse, status_code=201, tags=["Jobs"])
async def create_deid_job(job_data: DeidJobCreate, db: Session = Depends(get_db), current_user_id: UUID = None):
    # Get config
    config = db.query(DeidConfig).filter(DeidConfig.code == job_data.deid_config_code).first()
    if not config:
        raise HTTPException(status_code=404, detail="De-id config not found")

    # Get pseudo space if provided
    pseudo_space_id = None
    if job_data.pseudo_id_space_code:
        space = db.query(PseudoIdSpace).filter(PseudoIdSpace.code == job_data.pseudo_id_space_code).first()
        if not space:
            raise HTTPException(status_code=404, detail="Pseudo ID space not found")
        pseudo_space_id = space.id

    job = DeidJob(
        tenant_id=config.tenant_id,
        deid_config_id=config.id,
        pseudo_id_space_id=pseudo_space_id,
        job_type=job_data.job_type,
        status='queued',
        requested_by_user_id=current_user_id or UUID('00000000-0000-0000-0000-000000000000'),
        filters=job_data.filters
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    await publish_event(EventType.DEID_JOB_CREATED, {
        "job_id": str(job.id),
        "config_code": config.code,
        "job_type": job.job_type
    })

    logger.info(f"De-id job created: {job.id}")
    return job

@app.get("/api/v1/deid/jobs", response_model=List[DeidJobResponse], tags=["Jobs"])
async def list_deid_jobs(
    status: Optional[str] = Query(None),
    requested_by: Optional[UUID] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(DeidJob)
    if status:
        query = query.filter(DeidJob.status == status)
    if requested_by:
        query = query.filter(DeidJob.requested_by_user_id == requested_by)
    return query.order_by(DeidJob.created_at.desc()).all()

@app.get("/api/v1/deid/jobs/{job_id}", response_model=DeidJobResponse, tags=["Jobs"])
async def get_deid_job(job_id: UUID, db: Session = Depends(get_db)):
    job = db.query(DeidJob).filter(DeidJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/api/v1/deid/jobs/{job_id}/outputs", response_model=List[DeidJobOutputResponse], tags=["Jobs"])
async def get_job_outputs(job_id: UUID, db: Session = Depends(get_db)):
    job = db.query(DeidJob).filter(DeidJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return db.query(DeidJobOutput).filter(DeidJobOutput.deid_job_id == job_id).all()

# Helper Functions
def get_or_create_pseudo_id(pseudo_space_id: UUID, real_id: str, db: Session) -> str:
    """Get existing or create new pseudo ID mapping"""
    mapping = db.query(PseudoIdMapping).filter(and_(
        PseudoIdMapping.pseudo_id_space_id == pseudo_space_id,
        PseudoIdMapping.real_id == real_id
    )).first()

    if mapping:
        mapping.last_used_at = datetime.utcnow()
        db.commit()
        return mapping.pseudo_id

    # Generate new pseudo ID
    pseudo_id = f"PSEUDO-{secrets.token_hex(16)}"

    new_mapping = PseudoIdMapping(
        pseudo_id_space_id=pseudo_space_id,
        real_id=real_id,
        pseudo_id=pseudo_id,
        last_used_at=datetime.utcnow()
    )
    db.add(new_mapping)
    db.commit()

    return pseudo_id

@app.get("/health", tags=["System"])
async def health_check():
    return {"service": "deidentification-service", "status": "healthy", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8025)
