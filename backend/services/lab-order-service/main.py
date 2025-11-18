"""
Lab Order Service - Port 8037
Manages lab orders (requests) from OPD/IPD/ED
"""
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from shared.database.models import (
    LabOrder, LabOrderItem, LabTest, Patient, Encounter, Tenant
)
from shared.events.types import EventType
from shared.events.publisher import publish_event
from schemas import (
    LabOrderCreate, LabOrderUpdate, LabOrderResponse,
    LabOrderItemResponse
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Lab Order Service", version="0.1.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Lab Order Endpoints
@app.post("/api/v1/lab-orders", response_model=LabOrderResponse, status_code=201, tags=["Lab Orders"])
async def create_lab_order(
    order_data: LabOrderCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create a lab order for a patient"""
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == order_data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Verify all lab tests exist
    for item in order_data.items:
        lab_test = db.query(LabTest).filter(LabTest.id == item.lab_test_id).first()
        if not lab_test:
            raise HTTPException(status_code=404, detail=f"Lab test {item.lab_test_id} not found")

    # Create lab order
    lab_order = LabOrder(
        tenant_id=patient.tenant_id,
        patient_id=order_data.patient_id,
        encounter_id=order_data.encounter_id,
        episode_id=order_data.episode_id,
        ordering_practitioner_id=order_data.ordering_practitioner_id,
        ordering_department_id=order_data.ordering_department_id,
        priority=order_data.priority,
        status='requested',
        clinical_indication=order_data.clinical_indication,
        requested_at=datetime.utcnow()
    )
    db.add(lab_order)
    db.flush()  # Get the ID before adding items

    # Create order items
    for item_data in order_data.items:
        order_item = LabOrderItem(
            lab_order_id=lab_order.id,
            lab_test_id=item_data.lab_test_id,
            is_panel=item_data.is_panel,
            requested_specimen_type_id=item_data.requested_specimen_type_id,
            status='ordered'
        )
        db.add(order_item)

    db.commit()
    db.refresh(lab_order)

    await publish_event(EventType.LAB_ORDER_CREATED, {
        "lab_order_id": str(lab_order.id),
        "patient_id": str(lab_order.patient_id),
        "priority": lab_order.priority,
        "test_count": len(order_data.items)
    })

    logger.info(f"Lab order created: {lab_order.id} for patient {patient.id}")
    return lab_order

@app.get("/api/v1/lab-orders", response_model=List[LabOrderResponse], tags=["Lab Orders"])
async def list_lab_orders(
    patient_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List lab orders with filters"""
    query = db.query(LabOrder)
    if patient_id:
        query = query.filter(LabOrder.patient_id == patient_id)
    if status:
        query = query.filter(LabOrder.status == status)
    if from_date:
        query = query.filter(LabOrder.requested_at >= from_date)
    if to_date:
        query = query.filter(LabOrder.requested_at <= to_date)
    return query.order_by(LabOrder.requested_at.desc()).all()

@app.get("/api/v1/lab-orders/{id}", response_model=LabOrderResponse, tags=["Lab Orders"])
async def get_lab_order(id: UUID, db: Session = Depends(get_db)):
    """Get lab order details"""
    lab_order = db.query(LabOrder).filter(LabOrder.id == id).first()
    if not lab_order:
        raise HTTPException(status_code=404, detail="Lab order not found")
    return lab_order

@app.patch("/api/v1/lab-orders/{id}", response_model=LabOrderResponse, tags=["Lab Orders"])
async def update_lab_order(
    id: UUID,
    update_data: LabOrderUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Update lab order status"""
    lab_order = db.query(LabOrder).filter(LabOrder.id == id).first()
    if not lab_order:
        raise HTTPException(status_code=404, detail="Lab order not found")

    old_status = lab_order.status

    if update_data.status:
        lab_order.status = update_data.status
    if update_data.collected_at:
        lab_order.collected_at = update_data.collected_at
    if update_data.completed_at:
        lab_order.completed_at = update_data.completed_at

    db.commit()
    db.refresh(lab_order)

    # Publish status change events
    if update_data.status and update_data.status != old_status:
        if update_data.status == 'collected':
            await publish_event(EventType.LAB_ORDER_COLLECTED, {
                "lab_order_id": str(lab_order.id),
                "patient_id": str(lab_order.patient_id)
            })
        elif update_data.status == 'completed':
            await publish_event(EventType.LAB_ORDER_COMPLETED, {
                "lab_order_id": str(lab_order.id),
                "patient_id": str(lab_order.patient_id)
            })
        elif update_data.status == 'cancelled':
            await publish_event(EventType.LAB_ORDER_CANCELLED, {
                "lab_order_id": str(lab_order.id),
                "patient_id": str(lab_order.patient_id)
            })

    logger.info(f"Lab order updated: {id} - status: {lab_order.status}")
    return lab_order

@app.get("/health", tags=["System"])
async def health_check():
    return {"service": "lab-order-service", "status": "healthy", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8037)
