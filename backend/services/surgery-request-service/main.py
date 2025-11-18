"""
Surgery Request Service - Port 8050
Surgical/procedure requests from clinics/wards/ED
Maps to FHIR ServiceRequest
"""
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from shared.database.models import (
    SurgeryProcedureCatalog, SurgeryRequest,
    Patient, Encounter, Episode, Tenant
)
from shared.events.types import EventType
from shared.events.publisher import publish_event
from schemas import (
    SurgeryProcedureCatalogCreate, SurgeryProcedureCatalogResponse,
    SurgeryRequestCreate, SurgeryRequestUpdate, SurgeryRequestResponse
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Surgery Request Service", version="0.1.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Surgery Procedure Catalog Endpoints
@app.post("/api/v1/surgery-procedure-catalog", response_model=SurgeryProcedureCatalogResponse, status_code=201, tags=["Procedure Catalog"])
async def create_procedure_catalog(
    catalog_data: SurgeryProcedureCatalogCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create a surgery procedure catalog entry"""
    # Check for duplicate code
    existing = db.query(SurgeryProcedureCatalog).filter(
        SurgeryProcedureCatalog.tenant_id == catalog_data.tenant_id,
        SurgeryProcedureCatalog.code == catalog_data.code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Procedure code already exists for this tenant")

    catalog = SurgeryProcedureCatalog(
        tenant_id=catalog_data.tenant_id,
        code=catalog_data.code,
        name=catalog_data.name,
        specialty=catalog_data.specialty,
        body_site=catalog_data.body_site,
        description=catalog_data.description,
        typical_duration_minutes=catalog_data.typical_duration_minutes,
        fhir_code=catalog_data.fhir_code,
        default_priority=catalog_data.default_priority,
        default_anaesthesia_type=catalog_data.default_anaesthesia_type,
        preop_required_labs=catalog_data.preop_required_labs,
        preop_required_imaging=catalog_data.preop_required_imaging
    )
    db.add(catalog)
    db.commit()
    db.refresh(catalog)

    logger.info(f"Surgery procedure catalog created: {catalog.code}")
    return catalog

@app.get("/api/v1/surgery-procedure-catalog", response_model=List[SurgeryProcedureCatalogResponse], tags=["Procedure Catalog"])
async def list_procedure_catalog(
    tenant_id: UUID = Query(...),
    specialty: Optional[str] = Query(None),
    search_text: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List surgery procedures from catalog"""
    query = db.query(SurgeryProcedureCatalog).filter(
        SurgeryProcedureCatalog.tenant_id == tenant_id
    )

    if specialty:
        query = query.filter(SurgeryProcedureCatalog.specialty == specialty)
    if search_text:
        query = query.filter(
            (SurgeryProcedureCatalog.name.ilike(f"%{search_text}%")) |
            (SurgeryProcedureCatalog.code.ilike(f"%{search_text}%"))
        )

    return query.order_by(SurgeryProcedureCatalog.name).all()

# Surgery Request Endpoints
@app.post("/api/v1/surgery-requests", response_model=SurgeryRequestResponse, status_code=201, tags=["Surgery Requests"])
async def create_surgery_request(
    request_data: SurgeryRequestCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create a surgery request"""
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == request_data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Verify procedure catalog
    catalog = db.query(SurgeryProcedureCatalog).filter(
        SurgeryProcedureCatalog.id == request_data.procedure_catalog_id
    ).first()
    if not catalog:
        raise HTTPException(status_code=404, detail="Procedure catalog not found")

    # Verify encounter if provided
    if request_data.encounter_id:
        encounter = db.query(Encounter).filter(Encounter.id == request_data.encounter_id).first()
        if not encounter:
            raise HTTPException(status_code=404, detail="Encounter not found")

    # Verify episode if provided
    if request_data.episode_id:
        episode = db.query(Episode).filter(Episode.id == request_data.episode_id).first()
        if not episode:
            raise HTTPException(status_code=404, detail="Episode not found")

    surgery_request = SurgeryRequest(
        tenant_id=patient.tenant_id,
        patient_id=request_data.patient_id,
        encounter_id=request_data.encounter_id,
        episode_id=request_data.episode_id,
        requesting_practitioner_id=current_user_id,
        procedure_catalog_id=request_data.procedure_catalog_id,
        additional_procedure_text=request_data.additional_procedure_text,
        indication=request_data.indication,
        urgency=request_data.urgency,
        status='requested',
        requested_date=datetime.utcnow(),
        comments=request_data.comments
    )
    db.add(surgery_request)
    db.commit()
    db.refresh(surgery_request)

    await publish_event(EventType.SURGERY_REQUEST_CREATED, {
        "surgery_request_id": str(surgery_request.id),
        "patient_id": str(surgery_request.patient_id),
        "procedure_code": catalog.code,
        "urgency": surgery_request.urgency
    })

    logger.info(f"Surgery request created: {surgery_request.id} for patient {surgery_request.patient_id}")
    return surgery_request

@app.get("/api/v1/surgery-requests", response_model=List[SurgeryRequestResponse], tags=["Surgery Requests"])
async def list_surgery_requests(
    patient_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    urgency: Optional[str] = Query(None),
    specialty: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """List surgery requests with filters"""
    query = db.query(SurgeryRequest)

    if patient_id:
        query = query.filter(SurgeryRequest.patient_id == patient_id)
    if status:
        query = query.filter(SurgeryRequest.status == status)
    if urgency:
        query = query.filter(SurgeryRequest.urgency == urgency)
    if specialty:
        query = query.join(SurgeryProcedureCatalog).filter(
            SurgeryProcedureCatalog.specialty == specialty
        )
    if from_date:
        query = query.filter(SurgeryRequest.requested_date >= from_date)
    if to_date:
        query = query.filter(SurgeryRequest.requested_date <= to_date)

    return query.order_by(SurgeryRequest.requested_date.desc()).all()

@app.get("/api/v1/surgery-requests/{request_id}", response_model=SurgeryRequestResponse, tags=["Surgery Requests"])
async def get_surgery_request(request_id: UUID, db: Session = Depends(get_db)):
    """Get surgery request details"""
    request = db.query(SurgeryRequest).filter(SurgeryRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Surgery request not found")
    return request

@app.patch("/api/v1/surgery-requests/{request_id}", response_model=SurgeryRequestResponse, tags=["Surgery Requests"])
async def update_surgery_request(
    request_id: UUID,
    update_data: SurgeryRequestUpdate,
    db: Session = Depends(get_db)
):
    """Update surgery request status or comments"""
    request = db.query(SurgeryRequest).filter(SurgeryRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Surgery request not found")

    old_status = request.status

    if update_data.status is not None:
        request.status = update_data.status
    if update_data.comments is not None:
        request.comments = update_data.comments
    if update_data.urgency is not None:
        request.urgency = update_data.urgency

    request.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(request)

    # Publish event if status changed
    if old_status != request.status:
        if request.status == 'scheduled':
            await publish_event(EventType.SURGERY_REQUEST_SCHEDULED, {
                "surgery_request_id": str(request.id),
                "patient_id": str(request.patient_id)
            })
        elif request.status == 'cancelled':
            await publish_event(EventType.SURGERY_REQUEST_CANCELLED, {
                "surgery_request_id": str(request.id),
                "patient_id": str(request.patient_id)
            })

    logger.info(f"Surgery request updated: {request_id} - status: {request.status}")
    return request

@app.get("/health", tags=["System"])
async def health_check():
    return {"service": "surgery-request-service", "status": "healthy", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8050)
