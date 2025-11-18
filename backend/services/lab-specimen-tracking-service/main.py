"""
Lab Specimen Tracking Service - Port 8038
Manages specimen lifecycle: collection, labeling, transport, receipt, processing
"""
import logging
import secrets
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from shared.database.models import (
    LabSpecimen, LabSpecimenEvent, LabSpecimenType, LabOrder, Patient, Tenant
)
from shared.events.types import EventType
from shared.events.publisher import publish_event
from schemas import (
    LabSpecimenCreate, LabSpecimenLabelRequest, LabSpecimenUpdate, LabSpecimenResponse,
    LabSpecimenEventCreate, LabSpecimenEventResponse
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Lab Specimen Tracking Service", version="0.1.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def generate_specimen_identifier():
    """Generate unique specimen barcode identifier"""
    return f"SPEC-{secrets.token_hex(8).upper()}"

# Lab Specimen Endpoints
@app.post("/api/v1/lab-specimens/label", response_model=List[LabSpecimenResponse], status_code=201, tags=["Lab Specimens"])
async def generate_specimen_labels(
    label_request: LabSpecimenLabelRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Generate specimen labels (barcodes) for a lab order"""
    # Verify lab order exists
    lab_order = db.query(LabOrder).filter(LabOrder.id == label_request.lab_order_id).first()
    if not lab_order:
        raise HTTPException(status_code=404, detail="Lab order not found")

    # Verify specimen type exists
    specimen_type = db.query(LabSpecimenType).filter(LabSpecimenType.id == label_request.specimen_type_id).first()
    if not specimen_type:
        raise HTTPException(status_code=404, detail="Specimen type not found")

    specimens = []
    for _ in range(label_request.count):
        specimen_identifier = generate_specimen_identifier()

        specimen = LabSpecimen(
            tenant_id=lab_order.tenant_id,
            lab_order_id=label_request.lab_order_id,
            specimen_identifier=specimen_identifier,
            specimen_type_id=label_request.specimen_type_id,
            patient_id=lab_order.patient_id,
            status='pending_collection'
        )
        db.add(specimen)
        db.flush()

        # Record label printed event
        event = LabSpecimenEvent(
            lab_specimen_id=specimen.id,
            event_type='label_printed',
            event_time=datetime.utcnow(),
            performed_by_user_id=current_user_id
        )
        db.add(event)

        specimens.append(specimen)

    db.commit()

    for specimen in specimens:
        db.refresh(specimen)

    logger.info(f"Generated {len(specimens)} specimen labels for lab order {lab_order.id}")
    return specimens

@app.get("/api/v1/lab-specimens", response_model=List[LabSpecimenResponse], tags=["Lab Specimens"])
async def list_lab_specimens(
    lab_order_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    specimen_identifier: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List lab specimens with filters"""
    query = db.query(LabSpecimen)
    if lab_order_id:
        query = query.filter(LabSpecimen.lab_order_id == lab_order_id)
    if status:
        query = query.filter(LabSpecimen.status == status)
    if specimen_identifier:
        query = query.filter(LabSpecimen.specimen_identifier == specimen_identifier)
    return query.order_by(LabSpecimen.created_at.desc()).all()

@app.get("/api/v1/lab-specimens/{id}", response_model=LabSpecimenResponse, tags=["Lab Specimens"])
async def get_lab_specimen(id: UUID, db: Session = Depends(get_db)):
    """Get lab specimen details"""
    specimen = db.query(LabSpecimen).filter(LabSpecimen.id == id).first()
    if not specimen:
        raise HTTPException(status_code=404, detail="Lab specimen not found")
    return specimen

@app.patch("/api/v1/lab-specimens/{id}", response_model=LabSpecimenResponse, tags=["Lab Specimens"])
async def update_lab_specimen(
    id: UUID,
    update_data: LabSpecimenUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Update lab specimen status and details"""
    specimen = db.query(LabSpecimen).filter(LabSpecimen.id == id).first()
    if not specimen:
        raise HTTPException(status_code=404, detail="Lab specimen not found")

    old_status = specimen.status

    if update_data.status:
        specimen.status = update_data.status
    if update_data.collection_time:
        specimen.collection_time = update_data.collection_time
    if update_data.received_time:
        specimen.received_time = update_data.received_time
    if update_data.volume_ml is not None:
        specimen.volume_ml = update_data.volume_ml
    if update_data.comments:
        specimen.comments = update_data.comments

    db.commit()
    db.refresh(specimen)

    # Publish status change events
    if update_data.status and update_data.status != old_status:
        if update_data.status == 'collected':
            await publish_event(EventType.LAB_SPECIMEN_COLLECTED, {
                "specimen_id": str(specimen.id),
                "specimen_identifier": specimen.specimen_identifier,
                "patient_id": str(specimen.patient_id)
            })
        elif update_data.status == 'received':
            await publish_event(EventType.LAB_SPECIMEN_RECEIVED, {
                "specimen_id": str(specimen.id),
                "specimen_identifier": specimen.specimen_identifier,
                "patient_id": str(specimen.patient_id)
            })

    logger.info(f"Lab specimen updated: {id} - status: {specimen.status}")
    return specimen

# Lab Specimen Event Endpoints
@app.post("/api/v1/lab-specimens/{specimen_id}/events", response_model=LabSpecimenEventResponse, status_code=201, tags=["Specimen Events"])
async def create_specimen_event(
    specimen_id: UUID,
    event_data: LabSpecimenEventCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Record a specimen lifecycle event (scanned at location, etc.)"""
    specimen = db.query(LabSpecimen).filter(LabSpecimen.id == specimen_id).first()
    if not specimen:
        raise HTTPException(status_code=404, detail="Lab specimen not found")

    event = LabSpecimenEvent(
        lab_specimen_id=specimen_id,
        event_type=event_data.event_type,
        event_time=event_data.event_time,
        location_id=event_data.location_id,
        performed_by_user_id=event_data.performed_by_user_id or current_user_id,
        details=event_data.details
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    logger.info(f"Specimen event recorded: {event.event_type} for specimen {specimen_id}")
    return event

@app.get("/api/v1/lab-specimens/{specimen_id}/events", response_model=List[LabSpecimenEventResponse], tags=["Specimen Events"])
async def list_specimen_events(
    specimen_id: UUID,
    db: Session = Depends(get_db)
):
    """List all events for a specimen"""
    specimen = db.query(LabSpecimen).filter(LabSpecimen.id == specimen_id).first()
    if not specimen:
        raise HTTPException(status_code=404, detail="Lab specimen not found")

    return db.query(LabSpecimenEvent).filter(
        LabSpecimenEvent.lab_specimen_id == specimen_id
    ).order_by(LabSpecimenEvent.event_time).all()

@app.get("/health", tags=["System"])
async def health_check():
    return {"service": "lab-specimen-tracking-service", "status": "healthy", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8038)
