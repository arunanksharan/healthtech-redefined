"""
Pharmacy Verification & Dispense Service - Port 8045
Inpatient verification queue, dispensation tasks, FHIR MedicationDispense
"""
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, joinedload

from shared.database.models import (
    PharmacyVerificationQueue, MedicationDispensation, MedicationDispensationItem,
    MedicationOrder, MedicationProduct, Patient, Location, InventoryBatch, Tenant
)
from shared.events.types import EventType
from shared.events.publisher import publish_event
from schemas import (
    PharmacyVerificationQueueResponse,
    VerificationApprovalRequest, VerificationRejectionRequest,
    MedicationDispensationCreate, MedicationDispensationResponse,
    MedicationDispensationItemResponse, MedicationDispensationDetailResponse
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Pharmacy Verification & Dispense Service", version="0.1.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pharmacy Verification Queue Endpoints
@app.get("/api/v1/pharmacy/verification", response_model=List[PharmacyVerificationQueueResponse], tags=["Verification Queue"])
async def list_verification_queue(
    tenant_id: UUID = Query(...),
    status: Optional[str] = Query(None),
    patient_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db)
):
    """
    List medication orders pending pharmacy verification
    """
    query = db.query(PharmacyVerificationQueue).filter(
        PharmacyVerificationQueue.tenant_id == tenant_id
    )

    if status:
        query = query.filter(PharmacyVerificationQueue.status == status)
    if patient_id:
        query = query.filter(PharmacyVerificationQueue.patient_id == patient_id)

    return query.order_by(PharmacyVerificationQueue.created_at).all()

@app.get("/api/v1/pharmacy/verification/{queue_id}", response_model=PharmacyVerificationQueueResponse, tags=["Verification Queue"])
async def get_verification_item(queue_id: UUID, db: Session = Depends(get_db)):
    """Get verification queue item details"""
    item = db.query(PharmacyVerificationQueue).filter(PharmacyVerificationQueue.id == queue_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Verification item not found")
    return item

@app.post("/api/v1/pharmacy/verification/{queue_id}/approve", response_model=PharmacyVerificationQueueResponse, tags=["Verification Queue"])
async def approve_verification(
    queue_id: UUID,
    approval_data: VerificationApprovalRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Approve medication order after pharmacist review
    """
    item = db.query(PharmacyVerificationQueue).filter(PharmacyVerificationQueue.id == queue_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Verification item not found")

    if item.status != 'pending' and item.status != 'under_review':
        raise HTTPException(status_code=400, detail="Item is not pending verification")

    item.status = 'approved'
    item.pharmacist_id = current_user_id
    item.review_notes = approval_data.review_notes
    item.clinical_checks = approval_data.clinical_checks
    item.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(item)

    await publish_event(EventType.PHARMACY_VERIFICATION_APPROVED, {
        "verification_id": str(item.id),
        "medication_order_id": str(item.medication_order_id),
        "patient_id": str(item.patient_id),
        "pharmacist_id": str(current_user_id) if current_user_id else None
    })

    logger.info(f"Verification approved: {queue_id} by pharmacist {current_user_id}")
    return item

@app.post("/api/v1/pharmacy/verification/{queue_id}/reject", response_model=PharmacyVerificationQueueResponse, tags=["Verification Queue"])
async def reject_verification(
    queue_id: UUID,
    rejection_data: VerificationRejectionRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Reject medication order with reason
    """
    item = db.query(PharmacyVerificationQueue).filter(PharmacyVerificationQueue.id == queue_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Verification item not found")

    if item.status != 'pending' and item.status != 'under_review':
        raise HTTPException(status_code=400, detail="Item is not pending verification")

    item.status = 'rejected'
    item.pharmacist_id = current_user_id
    item.rejection_reason = rejection_data.rejection_reason
    item.review_notes = rejection_data.review_notes
    item.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(item)

    await publish_event(EventType.PHARMACY_VERIFICATION_REJECTED, {
        "verification_id": str(item.id),
        "medication_order_id": str(item.medication_order_id),
        "patient_id": str(item.patient_id),
        "rejection_reason": rejection_data.rejection_reason,
        "pharmacist_id": str(current_user_id) if current_user_id else None
    })

    logger.info(f"Verification rejected: {queue_id} - {rejection_data.rejection_reason}")
    return item

# Medication Dispensation Endpoints
@app.post("/api/v1/pharmacy/dispense", response_model=MedicationDispensationDetailResponse, status_code=201, tags=["Dispensation"])
async def create_dispensation(
    dispensation_data: MedicationDispensationCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Create medication dispensation record
    Maps to FHIR MedicationDispense
    """
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == dispensation_data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Verify medication order if provided
    if dispensation_data.medication_order_id:
        order = db.query(MedicationOrder).filter(MedicationOrder.id == dispensation_data.medication_order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Medication order not found")

    # Verify destination location if provided
    if dispensation_data.destination_location_id:
        location = db.query(Location).filter(Location.id == dispensation_data.destination_location_id).first()
        if not location:
            raise HTTPException(status_code=404, detail="Destination location not found")

    # Create dispensation
    dispensation = MedicationDispensation(
        tenant_id=patient.tenant_id,
        medication_order_id=dispensation_data.medication_order_id,
        patient_id=dispensation_data.patient_id,
        dispensed_by_user_id=current_user_id,
        dispensed_at=datetime.utcnow(),
        destination_location_id=dispensation_data.destination_location_id,
        status='completed',
        comments=dispensation_data.comments
    )
    db.add(dispensation)
    db.flush()  # Get dispensation ID

    # Create dispensation items
    for item_data in dispensation_data.items:
        # Verify medication product
        product = db.query(MedicationProduct).filter(
            MedicationProduct.id == item_data['medication_product_id']
        ).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Medication product not found: {item_data['medication_product_id']}")

        # Verify inventory batch if provided
        if item_data.get('inventory_batch_id'):
            batch = db.query(InventoryBatch).filter(
                InventoryBatch.id == item_data['inventory_batch_id']
            ).first()
            if not batch:
                raise HTTPException(status_code=404, detail=f"Inventory batch not found: {item_data['inventory_batch_id']}")

        item = MedicationDispensationItem(
            medication_dispensation_id=dispensation.id,
            medication_product_id=item_data['medication_product_id'],
            quantity_dispensed=item_data['quantity_dispensed'],
            quantity_unit=item_data.get('quantity_unit'),
            inventory_batch_id=item_data.get('inventory_batch_id')
        )
        db.add(item)

    db.commit()
    db.refresh(dispensation)

    # Reload with items
    dispensation = db.query(MedicationDispensation).options(
        joinedload(MedicationDispensation.medication_dispensation_items)
    ).filter(MedicationDispensation.id == dispensation.id).first()

    await publish_event(EventType.MEDICATION_DISPENSED, {
        "dispensation_id": str(dispensation.id),
        "patient_id": str(dispensation.patient_id),
        "medication_order_id": str(dispensation.medication_order_id) if dispensation.medication_order_id else None,
        "dispensed_by": str(current_user_id) if current_user_id else None
    })

    logger.info(f"Medication dispensation created: {dispensation.id} for patient {dispensation.patient_id}")
    return dispensation

@app.get("/api/v1/pharmacy/dispensations", response_model=List[MedicationDispensationResponse], tags=["Dispensation"])
async def list_dispensations(
    patient_id: Optional[UUID] = Query(None),
    medication_order_id: Optional[UUID] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """List medication dispensations with filters"""
    query = db.query(MedicationDispensation)

    if patient_id:
        query = query.filter(MedicationDispensation.patient_id == patient_id)
    if medication_order_id:
        query = query.filter(MedicationDispensation.medication_order_id == medication_order_id)
    if from_date:
        query = query.filter(MedicationDispensation.dispensed_at >= from_date)
    if to_date:
        query = query.filter(MedicationDispensation.dispensed_at <= to_date)

    return query.order_by(MedicationDispensation.dispensed_at.desc()).all()

@app.get("/api/v1/pharmacy/dispensations/{dispensation_id}", response_model=MedicationDispensationDetailResponse, tags=["Dispensation"])
async def get_dispensation(dispensation_id: UUID, db: Session = Depends(get_db)):
    """Get dispensation details with items"""
    dispensation = db.query(MedicationDispensation).options(
        joinedload(MedicationDispensation.medication_dispensation_items)
    ).filter(MedicationDispensation.id == dispensation_id).first()

    if not dispensation:
        raise HTTPException(status_code=404, detail="Dispensation not found")
    return dispensation

@app.get("/health", tags=["System"])
async def health_check():
    return {"service": "pharmacy-verification-dispense-service", "status": "healthy", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8045)
