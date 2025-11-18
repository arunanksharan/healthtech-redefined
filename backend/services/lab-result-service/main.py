"""
Lab Result Service - Port 8039
Manages lab results from analyzers/LIS including core lab and microbiology
"""
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from shared.database.models import (
    LabResult, LabResultValue, LabMicroOrganism, LabMicroSusceptibility,
    LabOrder, LabTest, Patient, Tenant
)
from shared.events.types import EventType
from shared.events.publisher import publish_event
from schemas import (
    LabResultCreate, LabResultUpdate, LabResultResponse,
    LabResultValueResponse, LabMicroOrganismResponse, LabMicroSusceptibilityResponse
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Lab Result Service", version="0.1.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Lab Result Endpoints
@app.post("/api/v1/lab-results", response_model=LabResultResponse, status_code=201, tags=["Lab Results"])
async def create_lab_result(
    result_data: LabResultCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Create lab result (LIS/analyzer imports or manual entry)
    Supports multi-component tests and microbiology results
    """
    # Verify lab order exists
    lab_order = db.query(LabOrder).filter(LabOrder.id == result_data.lab_order_id).first()
    if not lab_order:
        raise HTTPException(status_code=404, detail="Lab order not found")

    # Verify lab test exists
    lab_test = db.query(LabTest).filter(LabTest.id == result_data.lab_test_id).first()
    if not lab_test:
        raise HTTPException(status_code=404, detail="Lab test not found")

    # Create lab result
    lab_result = LabResult(
        tenant_id=lab_order.tenant_id,
        lab_order_id=result_data.lab_order_id,
        lab_order_item_id=result_data.lab_order_item_id,
        lab_test_id=result_data.lab_test_id,
        patient_id=result_data.patient_id,
        specimen_id=result_data.specimen_id,
        analyzer_run_id=result_data.analyzer_run_id,
        status='preliminary',
        result_time=result_data.result_time,
        entered_by_user_id=current_user_id,
        entry_source=result_data.entry_source,
        comments=result_data.comments
    )
    db.add(lab_result)
    db.flush()  # Get the ID before adding child records

    # Create result values (for multi-component tests/panels)
    if result_data.result_values:
        for value_data in result_data.result_values:
            result_value = LabResultValue(
                lab_result_id=lab_result.id,
                component_lab_test_id=value_data.component_lab_test_id,
                component_code=value_data.component_code,
                value_numeric=value_data.value_numeric,
                value_text=value_data.value_text,
                value_code=value_data.value_code,
                unit=value_data.unit,
                reference_range=value_data.reference_range,
                flag=value_data.flag
            )
            db.add(result_value)

    # Create microbiology organisms and susceptibilities
    if result_data.micro_organisms:
        for organism_data in result_data.micro_organisms:
            organism = LabMicroOrganism(
                lab_result_id=lab_result.id,
                organism_code=organism_data.organism_code,
                organism_name=organism_data.organism_name,
                quantity=organism_data.quantity,
                comments=organism_data.comments
            )
            db.add(organism)
            db.flush()  # Get organism ID

            # Add susceptibilities
            if organism_data.susceptibilities:
                for susc_data in organism_data.susceptibilities:
                    susceptibility = LabMicroSusceptibility(
                        lab_micro_organism_id=organism.id,
                        antibiotic_code=susc_data.antibiotic_code,
                        antibiotic_name=susc_data.antibiotic_name,
                        mic_value=susc_data.mic_value,
                        mic_unit=susc_data.mic_unit,
                        interpretation=susc_data.interpretation
                    )
                    db.add(susceptibility)

    db.commit()
    db.refresh(lab_result)

    await publish_event(EventType.LAB_RESULT_CREATED, {
        "lab_result_id": str(lab_result.id),
        "patient_id": str(lab_result.patient_id),
        "lab_test_id": str(lab_result.lab_test_id),
        "status": lab_result.status
    })

    logger.info(f"Lab result created: {lab_result.id} for patient {result_data.patient_id}")
    return lab_result

@app.get("/api/v1/lab-results", response_model=List[LabResultResponse], tags=["Lab Results"])
async def list_lab_results(
    patient_id: Optional[UUID] = Query(None),
    lab_order_id: Optional[UUID] = Query(None),
    test_code: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List lab results with filters"""
    query = db.query(LabResult)
    if patient_id:
        query = query.filter(LabResult.patient_id == patient_id)
    if lab_order_id:
        query = query.filter(LabResult.lab_order_id == lab_order_id)
    if test_code:
        # Join with LabTest to filter by code
        query = query.join(LabTest).filter(LabTest.code == test_code)
    if from_date:
        query = query.filter(LabResult.result_time >= from_date)
    if to_date:
        query = query.filter(LabResult.result_time <= to_date)
    if status:
        query = query.filter(LabResult.status == status)
    return query.order_by(LabResult.result_time.desc()).all()

@app.get("/api/v1/lab-results/{id}", response_model=LabResultResponse, tags=["Lab Results"])
async def get_lab_result(id: UUID, db: Session = Depends(get_db)):
    """Get lab result details"""
    lab_result = db.query(LabResult).filter(LabResult.id == id).first()
    if not lab_result:
        raise HTTPException(status_code=404, detail="Lab result not found")
    return lab_result

@app.patch("/api/v1/lab-results/{id}", response_model=LabResultResponse, tags=["Lab Results"])
async def update_lab_result(
    id: UUID,
    update_data: LabResultUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Update lab result (set status to final, mark as critical, etc.)
    Typically called by lab staff during validation workflow
    """
    lab_result = db.query(LabResult).filter(LabResult.id == id).first()
    if not lab_result:
        raise HTTPException(status_code=404, detail="Lab result not found")

    old_status = lab_result.status
    old_critical = lab_result.is_critical

    if update_data.status:
        lab_result.status = update_data.status
        if update_data.status == 'final':
            lab_result.validated_at = datetime.utcnow()
            lab_result.validated_by_user_id = current_user_id

    if update_data.is_critical is not None:
        lab_result.is_critical = update_data.is_critical

    if update_data.critical_notified is not None:
        lab_result.critical_notified = update_data.critical_notified

    if update_data.critical_notification_details:
        lab_result.critical_notification_details = update_data.critical_notification_details

    if update_data.comments:
        lab_result.comments = update_data.comments

    db.commit()
    db.refresh(lab_result)

    # Publish status change events
    if update_data.status and update_data.status != old_status:
        if update_data.status == 'final':
            await publish_event(EventType.LAB_RESULT_FINALIZED, {
                "lab_result_id": str(lab_result.id),
                "patient_id": str(lab_result.patient_id)
            })

    # Publish critical result notification event
    if lab_result.is_critical and not old_critical:
        await publish_event(EventType.LAB_CRITICAL_RESULT, {
            "lab_result_id": str(lab_result.id),
            "patient_id": str(lab_result.patient_id),
            "lab_test_id": str(lab_result.lab_test_id)
        })

    logger.info(f"Lab result updated: {id} - status: {lab_result.status}")
    return lab_result

# Microbiology Endpoints
@app.get("/api/v1/lab-results/micro", response_model=List[LabResultResponse], tags=["Microbiology"])
async def list_micro_results(
    patient_id: Optional[UUID] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    organism: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List microbiology results with filters"""
    query = db.query(LabResult).join(LabTest).filter(LabTest.category == 'micro')

    if patient_id:
        query = query.filter(LabResult.patient_id == patient_id)
    if from_date:
        query = query.filter(LabResult.result_time >= from_date)
    if to_date:
        query = query.filter(LabResult.result_time <= to_date)
    if organism:
        query = query.join(LabMicroOrganism).filter(
            LabMicroOrganism.organism_name.ilike(f"%{organism}%")
        )

    return query.order_by(LabResult.result_time.desc()).all()

@app.get("/health", tags=["System"])
async def health_check():
    return {"service": "lab-result-service", "status": "healthy", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8039)
