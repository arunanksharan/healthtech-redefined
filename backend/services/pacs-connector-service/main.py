"""
PACS Connector Service - Port 8032
Integration with PACS/VNA and DICOM world for imaging study metadata
"""
import logging
import secrets
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import Session, sessionmaker

from shared.database.models import (
    PACSEndpoint, ImagingStudy, ImagingSeries, ImagingInstance,
    Patient, ImagingOrder, Tenant
)
from shared.events.types import EventType
from shared.events.publisher import publish_event
from schemas import (
    PACSEndpointCreate, PACSEndpointResponse,
    ImagingStudyCreate, ImagingStudyUpdate, ImagingStudyResponse,
    ImagingSeriesCreate, ImagingSeriesResponse,
    ImagingInstanceCreate, ImagingInstanceResponse,
    StudySyncRequest
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="PACS Connector Service", version="0.1.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# PACS Endpoint Endpoints
@app.post("/api/v1/pacs/endpoints", response_model=PACSEndpointResponse, status_code=201, tags=["PACS Endpoints"])
async def create_pacs_endpoint(
    endpoint_data: PACSEndpointCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create PACS endpoint configuration"""
    existing = db.query(PACSEndpoint).filter(and_(
        PACSEndpoint.tenant_id == endpoint_data.tenant_id,
        PACSEndpoint.code == endpoint_data.code
    )).first()
    if existing:
        raise HTTPException(status_code=400, detail="PACS endpoint code already exists")

    endpoint = PACSEndpoint(
        tenant_id=endpoint_data.tenant_id,
        code=endpoint_data.code,
        name=endpoint_data.name,
        description=endpoint_data.description,
        ae_title=endpoint_data.ae_title,
        host=endpoint_data.host,
        port=endpoint_data.port,
        protocol=endpoint_data.protocol,
        auth_config=endpoint_data.auth_config,
        viewer_launch_url=endpoint_data.viewer_launch_url
    )
    db.add(endpoint)
    db.commit()
    db.refresh(endpoint)

    logger.info(f"PACS endpoint created: {endpoint.code}")
    return endpoint

@app.get("/api/v1/pacs/endpoints", response_model=List[PACSEndpointResponse], tags=["PACS Endpoints"])
async def list_pacs_endpoints(
    tenant_id: Optional[UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List all PACS endpoints"""
    query = db.query(PACSEndpoint)
    if tenant_id:
        query = query.filter(PACSEndpoint.tenant_id == tenant_id)
    if is_active is not None:
        query = query.filter(PACSEndpoint.is_active == is_active)
    return query.all()

@app.get("/api/v1/pacs/endpoints/{endpoint_id}", response_model=PACSEndpointResponse, tags=["PACS Endpoints"])
async def get_pacs_endpoint(endpoint_id: UUID, db: Session = Depends(get_db)):
    """Get PACS endpoint details"""
    endpoint = db.query(PACSEndpoint).filter(PACSEndpoint.id == endpoint_id).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="PACS endpoint not found")
    return endpoint

# Imaging Study Endpoints
@app.post("/api/v1/pacs/studies/sync", response_model=ImagingStudyResponse, status_code=201, tags=["Studies"])
async def sync_imaging_study(
    sync_data: StudySyncRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Sync imaging study from PACS (webhook endpoint or polling task)
    Creates or updates imaging study
    """
    # Get PACS endpoint
    pacs_endpoint = db.query(PACSEndpoint).filter(PACSEndpoint.code == sync_data.pacs_endpoint_code).first()
    if not pacs_endpoint:
        raise HTTPException(status_code=404, detail="PACS endpoint not found")

    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == sync_data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Check if study already exists (upsert pattern)
    existing_study = db.query(ImagingStudy).filter(and_(
        ImagingStudy.tenant_id == patient.tenant_id,
        ImagingStudy.study_instance_uid == sync_data.study_instance_uid
    )).first()

    if existing_study:
        # Update existing study
        existing_study.accession_number = sync_data.accession_number or existing_study.accession_number
        existing_study.description = sync_data.description or existing_study.description
        existing_study.started_at = sync_data.started_at or existing_study.started_at
        if sync_data.series:
            existing_study.number_of_series = len(sync_data.series)
        existing_study.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_study)

        logger.info(f"Imaging study updated: {existing_study.study_instance_uid}")
        return existing_study

    # Create new study
    study = ImagingStudy(
        tenant_id=patient.tenant_id,
        patient_id=sync_data.patient_id,
        pacs_endpoint_id=pacs_endpoint.id,
        study_instance_uid=sync_data.study_instance_uid,
        accession_number=sync_data.accession_number,
        modality_code=sync_data.modality_code,
        description=sync_data.description,
        started_at=sync_data.started_at,
        number_of_series=len(sync_data.series) if sync_data.series else 0,
        status='available'
    )
    db.add(study)
    db.commit()
    db.refresh(study)

    # Create series if provided
    if sync_data.series:
        for series_data in sync_data.series:
            series = ImagingSeries(
                imaging_study_id=study.id,
                series_instance_uid=series_data.get('series_instance_uid'),
                series_number=series_data.get('series_number'),
                body_part=series_data.get('body_part'),
                modality_code=series_data.get('modality_code'),
                number_of_instances=series_data.get('number_of_instances'),
                description=series_data.get('description')
            )
            db.add(series)
        db.commit()

    await publish_event(EventType.IMAGING_STUDY_AVAILABLE, {
        "study_id": str(study.id),
        "patient_id": str(study.patient_id),
        "study_instance_uid": study.study_instance_uid,
        "modality_code": study.modality_code,
        "pacs_endpoint_code": pacs_endpoint.code
    })

    logger.info(f"Imaging study synced: {study.study_instance_uid}")
    return study

@app.get("/api/v1/pacs/studies", response_model=List[ImagingStudyResponse], tags=["Studies"])
async def list_imaging_studies(
    patient_id: Optional[UUID] = Query(None),
    modality_code: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List imaging studies with filters"""
    query = db.query(ImagingStudy)
    if patient_id:
        query = query.filter(ImagingStudy.patient_id == patient_id)
    if modality_code:
        query = query.filter(ImagingStudy.modality_code == modality_code)
    if from_date:
        query = query.filter(ImagingStudy.started_at >= from_date)
    if to_date:
        query = query.filter(ImagingStudy.started_at <= to_date)
    if status:
        query = query.filter(ImagingStudy.status == status)
    return query.order_by(ImagingStudy.started_at.desc()).all()

@app.get("/api/v1/pacs/studies/{study_id}", response_model=ImagingStudyResponse, tags=["Studies"])
async def get_imaging_study(study_id: UUID, db: Session = Depends(get_db)):
    """Get imaging study details"""
    study = db.query(ImagingStudy).filter(ImagingStudy.id == study_id).first()
    if not study:
        raise HTTPException(status_code=404, detail="Imaging study not found")
    return study

@app.get("/api/v1/pacs/studies/{study_id}/viewer-launch", tags=["Studies"])
async def get_viewer_launch_url(study_id: UUID, db: Session = Depends(get_db)):
    """
    Get viewer launch URL with signed token for embedding DICOM viewer
    """
    study = db.query(ImagingStudy).filter(ImagingStudy.id == study_id).first()
    if not study:
        raise HTTPException(status_code=404, detail="Imaging study not found")

    pacs_endpoint = db.query(PACSEndpoint).filter(PACSEndpoint.id == study.pacs_endpoint_id).first()
    if not pacs_endpoint or not pacs_endpoint.viewer_launch_url:
        raise HTTPException(status_code=404, detail="Viewer URL not configured for this PACS endpoint")

    # Generate signed token for viewer access (single-use or time-bound)
    viewer_token = secrets.token_urlsafe(32)

    # Build viewer URL with study UID and token
    viewer_url = pacs_endpoint.viewer_launch_url.format(
        study_instance_uid=study.study_instance_uid,
        token=viewer_token
    )

    # Update study with viewer URL
    study.viewer_url = viewer_url
    db.commit()

    logger.info(f"Viewer URL generated for study: {study_id}")
    return {
        "study_id": str(study_id),
        "viewer_url": viewer_url,
        "viewer_token": viewer_token
    }

@app.patch("/api/v1/pacs/studies/{study_id}", response_model=ImagingStudyResponse, tags=["Studies"])
async def update_imaging_study(
    study_id: UUID,
    study_data: ImagingStudyUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Update imaging study"""
    study = db.query(ImagingStudy).filter(ImagingStudy.id == study_id).first()
    if not study:
        raise HTTPException(status_code=404, detail="Imaging study not found")

    update_data = study_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(study, field, value)

    study.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(study)

    logger.info(f"Imaging study updated: {study_id}")
    return study

# Imaging Series Endpoints
@app.post("/api/v1/pacs/series", response_model=ImagingSeriesResponse, status_code=201, tags=["Series"])
async def create_imaging_series(
    series_data: ImagingSeriesCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create imaging series"""
    # Verify study exists
    study = db.query(ImagingStudy).filter(ImagingStudy.id == series_data.imaging_study_id).first()
    if not study:
        raise HTTPException(status_code=404, detail="Imaging study not found")

    # Check for duplicate
    existing = db.query(ImagingSeries).filter(and_(
        ImagingSeries.imaging_study_id == series_data.imaging_study_id,
        ImagingSeries.series_instance_uid == series_data.series_instance_uid
    )).first()
    if existing:
        raise HTTPException(status_code=400, detail="Series already exists")

    series = ImagingSeries(
        imaging_study_id=series_data.imaging_study_id,
        series_instance_uid=series_data.series_instance_uid,
        series_number=series_data.series_number,
        body_part=series_data.body_part,
        modality_code=series_data.modality_code,
        number_of_instances=series_data.number_of_instances,
        description=series_data.description
    )
    db.add(series)
    db.commit()
    db.refresh(series)

    logger.info(f"Imaging series created: {series.series_instance_uid}")
    return series

@app.get("/api/v1/pacs/series", response_model=List[ImagingSeriesResponse], tags=["Series"])
async def list_imaging_series(
    imaging_study_id: UUID,
    db: Session = Depends(get_db)
):
    """List all series for an imaging study"""
    return db.query(ImagingSeries).filter(
        ImagingSeries.imaging_study_id == imaging_study_id
    ).order_by(ImagingSeries.series_number).all()

# Imaging Instance Endpoints
@app.post("/api/v1/pacs/instances", response_model=ImagingInstanceResponse, status_code=201, tags=["Instances"])
async def create_imaging_instance(
    instance_data: ImagingInstanceCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create imaging instance"""
    # Verify series exists
    series = db.query(ImagingSeries).filter(ImagingSeries.id == instance_data.imaging_series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Imaging series not found")

    instance = ImagingInstance(
        imaging_series_id=instance_data.imaging_series_id,
        sop_instance_uid=instance_data.sop_instance_uid,
        instance_number=instance_data.instance_number
    )
    db.add(instance)
    db.commit()
    db.refresh(instance)

    logger.info(f"Imaging instance created: {instance.sop_instance_uid}")
    return instance

@app.get("/health", tags=["System"])
async def health_check():
    return {"service": "pacs-connector-service", "status": "healthy", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8032)
