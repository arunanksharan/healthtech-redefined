"""
Medication Order Service - Port 8044
FHIR-aligned medication ordering (MedicationRequest)
"""
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from shared.database.models import (
    MedicationOrder, MedicationProduct, MedicationMolecule,
    Patient, Encounter, Episode, Practitioner, Department, Tenant
)
from shared.events.types import EventType
from shared.events.publisher import publish_event
from schemas import (
    MedicationOrderCreate, MedicationOrderUpdate, MedicationOrderResponse
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Medication Order Service", version="0.1.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/v1/medication-orders", response_model=MedicationOrderResponse, status_code=201, tags=["Medication Orders"])
async def create_medication_order(
    order_data: MedicationOrderCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Create a medication order (inpatient, outpatient, or discharge)
    Maps to FHIR MedicationRequest
    """
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == order_data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Verify encounter if provided
    if order_data.encounter_id:
        encounter = db.query(Encounter).filter(Encounter.id == order_data.encounter_id).first()
        if not encounter:
            raise HTTPException(status_code=404, detail="Encounter not found")

    # Verify episode if provided
    if order_data.episode_id:
        episode = db.query(Episode).filter(Episode.id == order_data.episode_id).first()
        if not episode:
            raise HTTPException(status_code=404, detail="Episode not found")

    # Verify prescriber if provided
    if order_data.prescriber_id:
        prescriber = db.query(Practitioner).filter(Practitioner.id == order_data.prescriber_id).first()
        if not prescriber:
            raise HTTPException(status_code=404, detail="Prescriber not found")

    # Verify medication product if provided
    if order_data.medication_product_id:
        product = db.query(MedicationProduct).filter(MedicationProduct.id == order_data.medication_product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Medication product not found")

    # Verify molecule if provided
    if order_data.molecule_id:
        molecule = db.query(MedicationMolecule).filter(MedicationMolecule.id == order_data.molecule_id).first()
        if not molecule:
            raise HTTPException(status_code=404, detail="Molecule not found")

    # Must have either product or molecule
    if not order_data.medication_product_id and not order_data.molecule_id:
        raise HTTPException(status_code=400, detail="Either medication_product_id or molecule_id must be provided")

    medication_order = MedicationOrder(
        tenant_id=patient.tenant_id,
        patient_id=order_data.patient_id,
        encounter_id=order_data.encounter_id,
        episode_id=order_data.episode_id,
        prescriber_id=order_data.prescriber_id,
        department_id=order_data.department_id,
        medication_product_id=order_data.medication_product_id,
        molecule_id=order_data.molecule_id,
        order_type=order_data.order_type,
        status='active',
        intent='order',
        dose_amount_numeric=order_data.dose_amount_numeric,
        dose_amount_unit=order_data.dose_amount_unit,
        dose_form_id=order_data.dose_form_id,
        route_id=order_data.route_id,
        frequency=order_data.frequency,
        as_needed=order_data.as_needed,
        as_needed_reason=order_data.as_needed_reason,
        start_datetime=order_data.start_datetime or datetime.utcnow(),
        end_datetime=order_data.end_datetime,
        indication=order_data.indication,
        instructions_for_patient=order_data.instructions_for_patient,
        instructions_for_pharmacist=order_data.instructions_for_pharmacist,
        is_prn=order_data.is_prn,
        linked_discharge_order_id=order_data.linked_discharge_order_id
    )
    db.add(medication_order)
    db.commit()
    db.refresh(medication_order)

    # Publish event
    await publish_event(EventType.MEDICATION_ORDER_CREATED, {
        "medication_order_id": str(medication_order.id),
        "patient_id": str(medication_order.patient_id),
        "order_type": medication_order.order_type,
        "status": medication_order.status
    })

    logger.info(f"Medication order created: {medication_order.id} for patient {medication_order.patient_id}")
    return medication_order

@app.get("/api/v1/medication-orders", response_model=List[MedicationOrderResponse], tags=["Medication Orders"])
async def list_medication_orders(
    patient_id: Optional[UUID] = Query(None),
    encounter_id: Optional[UUID] = Query(None),
    episode_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    order_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List medication orders with filters"""
    query = db.query(MedicationOrder)

    if patient_id:
        query = query.filter(MedicationOrder.patient_id == patient_id)
    if encounter_id:
        query = query.filter(MedicationOrder.encounter_id == encounter_id)
    if episode_id:
        query = query.filter(MedicationOrder.episode_id == episode_id)
    if status:
        query = query.filter(MedicationOrder.status == status)
    if order_type:
        query = query.filter(MedicationOrder.order_type == order_type)

    return query.order_by(MedicationOrder.start_datetime.desc()).all()

@app.get("/api/v1/medication-orders/{order_id}", response_model=MedicationOrderResponse, tags=["Medication Orders"])
async def get_medication_order(order_id: UUID, db: Session = Depends(get_db)):
    """Get medication order details"""
    order = db.query(MedicationOrder).filter(MedicationOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Medication order not found")
    return order

@app.patch("/api/v1/medication-orders/{order_id}", response_model=MedicationOrderResponse, tags=["Medication Orders"])
async def update_medication_order(
    order_id: UUID,
    update_data: MedicationOrderUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Update medication order (modify, hold, cancel, complete)
    """
    order = db.query(MedicationOrder).filter(MedicationOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Medication order not found")

    old_status = order.status

    if update_data.status is not None:
        order.status = update_data.status
    if update_data.end_datetime is not None:
        order.end_datetime = update_data.end_datetime
    if update_data.instructions_for_pharmacist is not None:
        order.instructions_for_pharmacist = update_data.instructions_for_pharmacist

    db.commit()
    db.refresh(order)

    # Publish event if status changed
    if old_status != order.status:
        if order.status == 'cancelled':
            await publish_event(EventType.MEDICATION_ORDER_CANCELLED, {
                "medication_order_id": str(order.id),
                "patient_id": str(order.patient_id)
            })
        elif order.status == 'completed':
            await publish_event(EventType.MEDICATION_ORDER_COMPLETED, {
                "medication_order_id": str(order.id),
                "patient_id": str(order.patient_id)
            })
        else:
            await publish_event(EventType.MEDICATION_ORDER_UPDATED, {
                "medication_order_id": str(order.id),
                "patient_id": str(order.patient_id),
                "old_status": old_status,
                "new_status": order.status
            })

    logger.info(f"Medication order updated: {order_id} - status: {order.status}")
    return order

@app.get("/health", tags=["System"])
async def health_check():
    return {"service": "medication-order-service", "status": "healthy", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8044)
