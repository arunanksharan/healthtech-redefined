"""
Pharmacy AI Orchestrator Service - Port 8049
AI workflows for medication safety, reconciliation, and inventory planning
"""
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from shared.database.models import (
    PharmacyAITask, PharmacyAIOutput,
    Patient, MedicationOrder, Tenant
)
from shared.events.types import EventType
from shared.events.publisher import publish_event
from schemas import (
    PharmacyAITaskCreate, PharmacyAITaskResponse,
    PharmacyAIOutputCreate, PharmacyAIOutputResponse
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Pharmacy AI Orchestrator Service", version="0.1.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pharmacy AI Task Endpoints
@app.post("/api/v1/pharmacy-ai/tasks", response_model=PharmacyAITaskResponse, status_code=201, tags=["AI Tasks"])
async def create_ai_task(
    task_data: PharmacyAITaskCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Request AI analysis for medication safety, reconciliation, or inventory
    Creates a task that will be processed by AI workers
    """
    tenant_id = None

    # Verify patient if provided
    if task_data.patient_id:
        patient = db.query(Patient).filter(Patient.id == task_data.patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        tenant_id = patient.tenant_id

    # Verify medication order if provided
    if task_data.medication_order_id:
        order = db.query(MedicationOrder).filter(MedicationOrder.id == task_data.medication_order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Medication order not found")
        tenant_id = order.tenant_id

    if not tenant_id:
        raise HTTPException(status_code=400, detail="Must specify patient_id or medication_order_id")

    ai_task = PharmacyAITask(
        tenant_id=tenant_id,
        patient_id=task_data.patient_id,
        medication_order_id=task_data.medication_order_id,
        task_type=task_data.task_type,
        status='queued',
        requested_at=datetime.utcnow()
    )
    db.add(ai_task)
    db.commit()
    db.refresh(ai_task)

    await publish_event(EventType.PHARMACY_AI_TASK_CREATED, {
        "ai_task_id": str(ai_task.id),
        "task_type": ai_task.task_type,
        "patient_id": str(ai_task.patient_id) if ai_task.patient_id else None,
        "medication_order_id": str(ai_task.medication_order_id) if ai_task.medication_order_id else None
    })

    logger.info(f"Pharmacy AI task created: {ai_task.id} - {ai_task.task_type}")
    return ai_task

@app.get("/api/v1/pharmacy-ai/tasks", response_model=List[PharmacyAITaskResponse], tags=["AI Tasks"])
async def list_ai_tasks(
    patient_id: Optional[UUID] = Query(None),
    medication_order_id: Optional[UUID] = Query(None),
    task_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List AI tasks with filters"""
    query = db.query(PharmacyAITask)

    if patient_id:
        query = query.filter(PharmacyAITask.patient_id == patient_id)
    if medication_order_id:
        query = query.filter(PharmacyAITask.medication_order_id == medication_order_id)
    if task_type:
        query = query.filter(PharmacyAITask.task_type == task_type)
    if status:
        query = query.filter(PharmacyAITask.status == status)

    return query.order_by(PharmacyAITask.requested_at.desc()).all()

@app.get("/api/v1/pharmacy-ai/tasks/{task_id}", response_model=PharmacyAITaskResponse, tags=["AI Tasks"])
async def get_ai_task(task_id: UUID, db: Session = Depends(get_db)):
    """Get AI task details and status"""
    ai_task = db.query(PharmacyAITask).filter(PharmacyAITask.id == task_id).first()
    if not ai_task:
        raise HTTPException(status_code=404, detail="AI task not found")
    return ai_task

@app.patch("/api/v1/pharmacy-ai/tasks/{task_id}/status", response_model=PharmacyAITaskResponse, tags=["AI Tasks"])
async def update_task_status(
    task_id: UUID,
    status: str,
    error_message: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Update AI task status (typically called by AI workers)
    """
    ai_task = db.query(PharmacyAITask).filter(PharmacyAITask.id == task_id).first()
    if not ai_task:
        raise HTTPException(status_code=404, detail="AI task not found")

    old_status = ai_task.status
    ai_task.status = status

    if status == 'completed':
        ai_task.completed_at = datetime.utcnow()
        await publish_event(EventType.PHARMACY_AI_TASK_COMPLETED, {
            "ai_task_id": str(ai_task.id),
            "task_type": ai_task.task_type
        })
    elif status == 'failed':
        ai_task.error_message = error_message
        ai_task.completed_at = datetime.utcnow()
        await publish_event(EventType.PHARMACY_AI_TASK_FAILED, {
            "ai_task_id": str(ai_task.id),
            "task_type": ai_task.task_type,
            "error": error_message
        })

    db.commit()
    db.refresh(ai_task)

    logger.info(f"Pharmacy AI task status updated: {task_id} - {status}")
    return ai_task

# Pharmacy AI Output Endpoints
@app.post("/api/v1/pharmacy-ai/outputs", response_model=PharmacyAIOutputResponse, status_code=201, tags=["AI Outputs"])
async def create_ai_output(
    output_data: PharmacyAIOutputCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Store AI analysis output
    Typically called by AI workers after inference completes
    """
    # Verify task exists
    ai_task = db.query(PharmacyAITask).filter(PharmacyAITask.id == output_data.pharmacy_ai_task_id).first()
    if not ai_task:
        raise HTTPException(status_code=404, detail="AI task not found")

    ai_output = PharmacyAIOutput(
        pharmacy_ai_task_id=output_data.pharmacy_ai_task_id,
        output_type=output_data.output_type,
        payload=output_data.payload
    )
    db.add(ai_output)
    db.commit()
    db.refresh(ai_output)

    await publish_event(EventType.PHARMACY_AI_OUTPUT_CREATED, {
        "output_id": str(ai_output.id),
        "ai_task_id": str(ai_task.id),
        "output_type": ai_output.output_type,
        "task_type": ai_task.task_type
    })

    logger.info(f"Pharmacy AI output created: {ai_output.id} - {output_data.output_type}")
    return ai_output

@app.get("/api/v1/pharmacy-ai/outputs", response_model=List[PharmacyAIOutputResponse], tags=["AI Outputs"])
async def list_ai_outputs(
    pharmacy_ai_task_id: UUID,
    db: Session = Depends(get_db)
):
    """List all outputs for an AI task"""
    return db.query(PharmacyAIOutput).filter(
        PharmacyAIOutput.pharmacy_ai_task_id == pharmacy_ai_task_id
    ).order_by(PharmacyAIOutput.created_at).all()

@app.get("/api/v1/pharmacy-ai/outputs/{output_id}", response_model=PharmacyAIOutputResponse, tags=["AI Outputs"])
async def get_ai_output(output_id: UUID, db: Session = Depends(get_db)):
    """Get AI output details"""
    ai_output = db.query(PharmacyAIOutput).filter(PharmacyAIOutput.id == output_id).first()
    if not ai_output:
        raise HTTPException(status_code=404, detail="AI output not found")
    return ai_output

@app.get("/health", tags=["System"])
async def health_check():
    return {"service": "pharmacy-ai-orchestrator-service", "status": "healthy", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8049)
