"""
MAR Service - Port 8046
Medication Administration Record (FHIR MedicationAdministration)
"""
import logging
from datetime import datetime, date
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from shared.database.models import (
    MedicationAdministration, MedicationOrder, MedicationProduct,
    Patient, Encounter, MedicationRoute, Tenant
)
from shared.events.types import EventType
from shared.events.publisher import publish_event
from schemas import (
    MedicationAdministrationCreate, MedicationAdministrationUpdate,
    MedicationAdministrationResponse
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="MAR Service", version="0.1.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/v1/mar", response_model=MedicationAdministrationResponse, status_code=201, tags=["MAR"])
async def create_administration_record(
    admin_data: MedicationAdministrationCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Create a medication administration record (scheduled or completed)
    Maps to FHIR MedicationAdministration
    """
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == admin_data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Verify medication order if provided
    if admin_data.medication_order_id:
        order = db.query(MedicationOrder).filter(MedicationOrder.id == admin_data.medication_order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Medication order not found")

    # Verify medication product if provided
    if admin_data.medication_product_id:
        product = db.query(MedicationProduct).filter(MedicationProduct.id == admin_data.medication_product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Medication product not found")

    # Verify encounter if provided
    if admin_data.encounter_id:
        encounter = db.query(Encounter).filter(Encounter.id == admin_data.encounter_id).first()
        if not encounter:
            raise HTTPException(status_code=404, detail="Encounter not found")

    # Verify route if provided
    if admin_data.route_id:
        route = db.query(MedicationRoute).filter(MedicationRoute.id == admin_data.route_id).first()
        if not route:
            raise HTTPException(status_code=404, detail="Route not found")

    administration = MedicationAdministration(
        tenant_id=patient.tenant_id,
        medication_order_id=admin_data.medication_order_id,
        medication_product_id=admin_data.medication_product_id,
        patient_id=admin_data.patient_id,
        encounter_id=admin_data.encounter_id,
        scheduled_time=admin_data.scheduled_time,
        dose_given_numeric=admin_data.dose_given_numeric,
        dose_given_unit=admin_data.dose_given_unit,
        route_id=admin_data.route_id,
        status='scheduled',
        comments=admin_data.comments
    )
    db.add(administration)
    db.commit()
    db.refresh(administration)

    logger.info(f"Medication administration record created: {administration.id} for patient {administration.patient_id}")
    return administration

@app.get("/api/v1/mar", response_model=List[MedicationAdministrationResponse], tags=["MAR"])
async def list_administration_records(
    patient_id: Optional[UUID] = Query(None),
    encounter_id: Optional[UUID] = Query(None),
    medication_order_id: Optional[UUID] = Query(None),
    date: Optional[date] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    List medication administration records with filters
    Used by nursing staff to view MAR
    """
    query = db.query(MedicationAdministration)

    if patient_id:
        query = query.filter(MedicationAdministration.patient_id == patient_id)
    if encounter_id:
        query = query.filter(MedicationAdministration.encounter_id == encounter_id)
    if medication_order_id:
        query = query.filter(MedicationAdministration.medication_order_id == medication_order_id)
    if date:
        # Filter by date of scheduled_time
        start_of_day = datetime.combine(date, datetime.min.time())
        end_of_day = datetime.combine(date, datetime.max.time())
        query = query.filter(
            MedicationAdministration.scheduled_time >= start_of_day,
            MedicationAdministration.scheduled_time <= end_of_day
        )
    if status:
        query = query.filter(MedicationAdministration.status == status)

    return query.order_by(MedicationAdministration.scheduled_time).all()

@app.get("/api/v1/mar/{administration_id}", response_model=MedicationAdministrationResponse, tags=["MAR"])
async def get_administration_record(administration_id: UUID, db: Session = Depends(get_db)):
    """Get medication administration record details"""
    administration = db.query(MedicationAdministration).filter(
        MedicationAdministration.id == administration_id
    ).first()
    if not administration:
        raise HTTPException(status_code=404, detail="Administration record not found")
    return administration

@app.post("/api/v1/mar/administer", response_model=MedicationAdministrationResponse, tags=["MAR"])
async def administer_medication(
    administration_id: UUID = Query(...),
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Mark medication as administered (quick action for nurses)
    """
    administration = db.query(MedicationAdministration).filter(
        MedicationAdministration.id == administration_id
    ).first()
    if not administration:
        raise HTTPException(status_code=404, detail="Administration record not found")

    administration.status = 'completed'
    administration.administration_time = datetime.utcnow()
    administration.administered_by_user_id = current_user_id
    administration.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(administration)

    await publish_event(EventType.MEDICATION_ADMINISTERED, {
        "administration_id": str(administration.id),
        "patient_id": str(administration.patient_id),
        "medication_order_id": str(administration.medication_order_id) if administration.medication_order_id else None,
        "administered_by": str(current_user_id) if current_user_id else None,
        "administration_time": administration.administration_time.isoformat()
    })

    logger.info(f"Medication administered: {administration_id} by user {current_user_id}")
    return administration

@app.patch("/api/v1/mar/{administration_id}", response_model=MedicationAdministrationResponse, tags=["MAR"])
async def update_administration_record(
    administration_id: UUID,
    update_data: MedicationAdministrationUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Update medication administration record
    Used to mark as completed, skipped, refused, or partial
    """
    administration = db.query(MedicationAdministration).filter(
        MedicationAdministration.id == administration_id
    ).first()
    if not administration:
        raise HTTPException(status_code=404, detail="Administration record not found")

    old_status = administration.status

    if update_data.administration_time is not None:
        administration.administration_time = update_data.administration_time
    if update_data.dose_given_numeric is not None:
        administration.dose_given_numeric = update_data.dose_given_numeric
    if update_data.dose_given_unit is not None:
        administration.dose_given_unit = update_data.dose_given_unit
    if update_data.status is not None:
        administration.status = update_data.status
        if update_data.status == 'completed' and not administration.administration_time:
            administration.administration_time = datetime.utcnow()
        if update_data.status in ['completed', 'skipped', 'refused', 'partial']:
            administration.administered_by_user_id = current_user_id
    if update_data.reason_skipped is not None:
        administration.reason_skipped = update_data.reason_skipped
    if update_data.comments is not None:
        administration.comments = update_data.comments

    administration.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(administration)

    # Publish event based on status
    if old_status != administration.status:
        if administration.status == 'completed':
            await publish_event(EventType.MEDICATION_ADMINISTERED, {
                "administration_id": str(administration.id),
                "patient_id": str(administration.patient_id),
                "medication_order_id": str(administration.medication_order_id) if administration.medication_order_id else None,
                "administered_by": str(current_user_id) if current_user_id else None
            })
        elif administration.status in ['skipped', 'refused']:
            await publish_event(EventType.MEDICATION_ADMINISTRATION_SKIPPED, {
                "administration_id": str(administration.id),
                "patient_id": str(administration.patient_id),
                "status": administration.status,
                "reason": administration.reason_skipped
            })

    logger.info(f"Medication administration updated: {administration_id} - status: {administration.status}")
    return administration

@app.get("/health", tags=["System"])
async def health_check():
    return {"service": "mar-service", "status": "healthy", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8046)
