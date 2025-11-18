"""
Imaging Order Service - Port 8031
Manages imaging order catalog and imaging requests
"""
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import Session, sessionmaker

from shared.database.models import (
    ImagingModality, ImagingProcedure, ImagingOrder,
    Patient, Encounter, Practitioner, Tenant
)
from shared.events.types import EventType
from shared.events.publisher import publish_event
from schemas import (
    ImagingModalityCreate, ImagingModalityResponse,
    ImagingProcedureCreate, ImagingProcedureResponse,
    ImagingOrderCreate, ImagingOrderUpdate, ImagingOrderResponse
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Imaging Order Service", version="0.1.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Imaging Modality Endpoints
@app.post("/api/v1/imaging/modalities", response_model=ImagingModalityResponse, status_code=201, tags=["Modalities"])
async def create_modality(
    modality_data: ImagingModalityCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create imaging modality (CT, MR, US, etc.)"""
    existing = db.query(ImagingModality).filter(and_(
        ImagingModality.tenant_id == modality_data.tenant_id,
        ImagingModality.code == modality_data.code
    )).first()
    if existing:
        raise HTTPException(status_code=400, detail="Modality code already exists")

    modality = ImagingModality(
        tenant_id=modality_data.tenant_id,
        code=modality_data.code,
        name=modality_data.name,
        description=modality_data.description
    )
    db.add(modality)
    db.commit()
    db.refresh(modality)

    logger.info(f"Imaging modality created: {modality.code}")
    return modality

@app.get("/api/v1/imaging/modalities", response_model=List[ImagingModalityResponse], tags=["Modalities"])
async def list_modalities(
    tenant_id: Optional[UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List all imaging modalities"""
    query = db.query(ImagingModality)
    if tenant_id:
        query = query.filter(ImagingModality.tenant_id == tenant_id)
    if is_active is not None:
        query = query.filter(ImagingModality.is_active == is_active)
    return query.all()

@app.get("/api/v1/imaging/modalities/{modality_id}", response_model=ImagingModalityResponse, tags=["Modalities"])
async def get_modality(modality_id: UUID, db: Session = Depends(get_db)):
    """Get imaging modality details"""
    modality = db.query(ImagingModality).filter(ImagingModality.id == modality_id).first()
    if not modality:
        raise HTTPException(status_code=404, detail="Modality not found")
    return modality

# Imaging Procedure Endpoints
@app.post("/api/v1/imaging/procedures", response_model=ImagingProcedureResponse, status_code=201, tags=["Procedures"])
async def create_procedure(
    procedure_data: ImagingProcedureCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create imaging procedure in catalog"""
    # Verify modality exists
    modality = db.query(ImagingModality).filter(ImagingModality.id == procedure_data.modality_id).first()
    if not modality:
        raise HTTPException(status_code=404, detail="Modality not found")

    # Check for duplicate code
    existing = db.query(ImagingProcedure).filter(and_(
        ImagingProcedure.tenant_id == procedure_data.tenant_id,
        ImagingProcedure.code == procedure_data.code
    )).first()
    if existing:
        raise HTTPException(status_code=400, detail="Procedure code already exists")

    procedure = ImagingProcedure(
        tenant_id=procedure_data.tenant_id,
        code=procedure_data.code,
        name=procedure_data.name,
        modality_id=procedure_data.modality_id,
        description=procedure_data.description,
        body_part=procedure_data.body_part,
        snomed_code=procedure_data.snomed_code,
        loinc_code=procedure_data.loinc_code,
        default_duration_minutes=procedure_data.default_duration_minutes,
        preparation_instructions=procedure_data.preparation_instructions
    )
    db.add(procedure)
    db.commit()
    db.refresh(procedure)

    logger.info(f"Imaging procedure created: {procedure.code}")
    return procedure

@app.get("/api/v1/imaging/procedures", response_model=List[ImagingProcedureResponse], tags=["Procedures"])
async def list_procedures(
    tenant_id: Optional[UUID] = Query(None),
    modality_id: Optional[UUID] = Query(None),
    body_part: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List imaging procedures with filters"""
    query = db.query(ImagingProcedure)
    if tenant_id:
        query = query.filter(ImagingProcedure.tenant_id == tenant_id)
    if modality_id:
        query = query.filter(ImagingProcedure.modality_id == modality_id)
    if body_part:
        query = query.filter(ImagingProcedure.body_part.ilike(f"%{body_part}%"))
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (ImagingProcedure.name.ilike(search_term)) |
            (ImagingProcedure.code.ilike(search_term))
        )
    if is_active is not None:
        query = query.filter(ImagingProcedure.is_active == is_active)
    return query.all()

@app.get("/api/v1/imaging/procedures/{procedure_id}", response_model=ImagingProcedureResponse, tags=["Procedures"])
async def get_procedure(procedure_id: UUID, db: Session = Depends(get_db)):
    """Get imaging procedure details"""
    procedure = db.query(ImagingProcedure).filter(ImagingProcedure.id == procedure_id).first()
    if not procedure:
        raise HTTPException(status_code=404, detail="Procedure not found")
    return procedure

# Imaging Order Endpoints
@app.post("/api/v1/imaging/orders", response_model=ImagingOrderResponse, status_code=201, tags=["Orders"])
async def create_imaging_order(
    order_data: ImagingOrderCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create imaging order for a patient"""
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == order_data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Verify imaging procedure exists
    procedure = db.query(ImagingProcedure).filter(ImagingProcedure.id == order_data.imaging_procedure_id).first()
    if not procedure:
        raise HTTPException(status_code=404, detail="Imaging procedure not found")

    # Get modality for the procedure
    modality = db.query(ImagingModality).filter(ImagingModality.id == procedure.modality_id).first()

    order = ImagingOrder(
        tenant_id=patient.tenant_id,
        patient_id=order_data.patient_id,
        encounter_id=order_data.encounter_id,
        episode_id=order_data.episode_id,
        ordering_practitioner_id=order_data.ordering_practitioner_id,
        ordering_department_id=order_data.ordering_department_id,
        imaging_procedure_id=order_data.imaging_procedure_id,
        indication=order_data.indication,
        priority=order_data.priority,
        status='requested',
        requested_at=datetime.utcnow()
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    await publish_event(EventType.IMAGING_ORDER_CREATED, {
        "order_id": str(order.id),
        "patient_id": str(order.patient_id),
        "procedure_code": procedure.code,
        "procedure_name": procedure.name,
        "modality_code": modality.code if modality else None,
        "priority": order.priority,
        "indication": order.indication
    })

    logger.info(f"Imaging order created: {order.id} - {procedure.code}")
    return order

@app.get("/api/v1/imaging/orders", response_model=List[ImagingOrderResponse], tags=["Orders"])
async def list_imaging_orders(
    patient_id: Optional[UUID] = Query(None),
    encounter_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """List imaging orders with filters"""
    query = db.query(ImagingOrder)
    if patient_id:
        query = query.filter(ImagingOrder.patient_id == patient_id)
    if encounter_id:
        query = query.filter(ImagingOrder.encounter_id == encounter_id)
    if status:
        query = query.filter(ImagingOrder.status == status)
    if priority:
        query = query.filter(ImagingOrder.priority == priority)
    if from_date:
        query = query.filter(ImagingOrder.requested_at >= from_date)
    if to_date:
        query = query.filter(ImagingOrder.requested_at <= to_date)
    return query.order_by(ImagingOrder.requested_at.desc()).all()

@app.get("/api/v1/imaging/orders/{order_id}", response_model=ImagingOrderResponse, tags=["Orders"])
async def get_imaging_order(order_id: UUID, db: Session = Depends(get_db)):
    """Get imaging order details"""
    order = db.query(ImagingOrder).filter(ImagingOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Imaging order not found")
    return order

@app.patch("/api/v1/imaging/orders/{order_id}", response_model=ImagingOrderResponse, tags=["Orders"])
async def update_imaging_order(
    order_id: UUID,
    order_data: ImagingOrderUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Update imaging order status or details"""
    order = db.query(ImagingOrder).filter(ImagingOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Imaging order not found")

    update_data = order_data.dict(exclude_unset=True)
    old_status = order.status

    for field, value in update_data.items():
        setattr(order, field, value)

    order.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(order)

    # Publish status change events
    if 'status' in update_data and old_status != order.status:
        if order.status == 'scheduled':
            await publish_event(EventType.IMAGING_ORDER_SCHEDULED, {
                "order_id": str(order.id),
                "patient_id": str(order.patient_id),
                "scheduled_slot_id": str(order.scheduled_slot_id) if order.scheduled_slot_id else None
            })
        elif order.status == 'in_progress':
            await publish_event(EventType.IMAGING_ORDER_IN_PROGRESS, {
                "order_id": str(order.id),
                "patient_id": str(order.patient_id),
                "started_at": order.performed_start_at.isoformat() if order.performed_start_at else None
            })
        elif order.status == 'completed':
            await publish_event(EventType.IMAGING_ORDER_COMPLETED, {
                "order_id": str(order.id),
                "patient_id": str(order.patient_id),
                "completed_at": order.performed_end_at.isoformat() if order.performed_end_at else None
            })
        elif order.status == 'cancelled':
            await publish_event(EventType.IMAGING_ORDER_CANCELLED, {
                "order_id": str(order.id),
                "patient_id": str(order.patient_id)
            })

    logger.info(f"Imaging order updated: {order_id}")
    return order

@app.get("/health", tags=["System"])
async def health_check():
    return {"service": "imaging-order-service", "status": "healthy", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8031)
