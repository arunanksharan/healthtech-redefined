"""
Lab AI Orchestrator Service - Port 8041
Manages AI workflows for lab interpretation and pathology assistance
"""
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from shared.database.models import (
    LabAIModel, LabAITask, LabAIOutput,
    LabResult, APReport, Patient, Tenant
)
from shared.events.types import EventType
from shared.events.publisher import publish_event
from schemas import (
    LabAIModelCreate, LabAIModelResponse,
    LabAITaskCreate, LabAITaskResponse,
    LabAIOutputCreate, LabAIOutputResponse
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Lab AI Orchestrator Service", version="0.1.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Lab AI Model Endpoints
@app.post("/api/v1/lab-ai/models", response_model=LabAIModelResponse, status_code=201, tags=["AI Models"])
async def create_ai_model(
    model_data: LabAIModelCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Register a lab AI model"""
    existing = db.query(LabAIModel).filter(LabAIModel.code == model_data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="AI model code already exists")

    ai_model = LabAIModel(
        tenant_id=model_data.tenant_id,
        code=model_data.code,
        name=model_data.name,
        description=model_data.description,
        domain=model_data.domain,
        capabilities=model_data.capabilities,
        endpoint_config=model_data.endpoint_config
    )
    db.add(ai_model)
    db.commit()
    db.refresh(ai_model)

    logger.info(f"Lab AI model registered: {ai_model.code}")
    return ai_model

@app.get("/api/v1/lab-ai/models", response_model=List[LabAIModelResponse], tags=["AI Models"])
async def list_ai_models(
    domain: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List all lab AI models"""
    query = db.query(LabAIModel)
    if domain:
        query = query.filter(LabAIModel.domain == domain)
    if is_active is not None:
        query = query.filter(LabAIModel.is_active == is_active)
    return query.all()

@app.get("/api/v1/lab-ai/models/{model_id}", response_model=LabAIModelResponse, tags=["AI Models"])
async def get_ai_model(model_id: UUID, db: Session = Depends(get_db)):
    """Get AI model details"""
    ai_model = db.query(LabAIModel).filter(LabAIModel.id == model_id).first()
    if not ai_model:
        raise HTTPException(status_code=404, detail="AI model not found")
    return ai_model

# Lab AI Task Endpoints
@app.post("/api/v1/lab-ai/tasks", response_model=LabAITaskResponse, status_code=201, tags=["AI Tasks"])
async def create_ai_task(
    task_data: LabAITaskCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Request AI analysis for lab results or pathology reports
    Creates a task that will be processed by AI workers
    """
    # Verify AI model exists
    ai_model = db.query(LabAIModel).filter(LabAIModel.id == task_data.ai_model_id).first()
    if not ai_model:
        raise HTTPException(status_code=404, detail="AI model not found")

    # Verify domain-specific entity exists
    tenant_id = None
    if task_data.lab_result_id:
        lab_result = db.query(LabResult).filter(LabResult.id == task_data.lab_result_id).first()
        if not lab_result:
            raise HTTPException(status_code=404, detail="Lab result not found")
        tenant_id = lab_result.tenant_id
    elif task_data.ap_report_id:
        ap_report = db.query(APReport).filter(APReport.id == task_data.ap_report_id).first()
        if not ap_report:
            raise HTTPException(status_code=404, detail="AP report not found")
        # Get tenant_id from case
        tenant_id = ap_report.ap_case.tenant_id
    elif task_data.patient_id:
        patient = db.query(Patient).filter(Patient.id == task_data.patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        tenant_id = patient.tenant_id

    if not tenant_id:
        raise HTTPException(status_code=400, detail="Must specify patient_id, lab_result_id, or ap_report_id")

    ai_task = LabAITask(
        tenant_id=tenant_id,
        domain=task_data.domain,
        patient_id=task_data.patient_id,
        lab_result_id=task_data.lab_result_id,
        ap_report_id=task_data.ap_report_id,
        ai_model_id=task_data.ai_model_id,
        task_type=task_data.task_type,
        status='queued',
        requested_at=datetime.utcnow()
    )
    db.add(ai_task)
    db.commit()
    db.refresh(ai_task)

    await publish_event(EventType.LAB_AI_TASK_CREATED, {
        "ai_task_id": str(ai_task.id),
        "domain": ai_task.domain,
        "task_type": ai_task.task_type,
        "ai_model_code": ai_model.code
    })

    logger.info(f"Lab AI task created: {ai_task.id} - {ai_task.task_type}")
    return ai_task

@app.get("/api/v1/lab-ai/tasks", response_model=List[LabAITaskResponse], tags=["AI Tasks"])
async def list_ai_tasks(
    patient_id: Optional[UUID] = Query(None),
    lab_result_id: Optional[UUID] = Query(None),
    ap_report_id: Optional[UUID] = Query(None),
    domain: Optional[str] = Query(None),
    task_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List AI tasks with filters"""
    query = db.query(LabAITask)
    if patient_id:
        query = query.filter(LabAITask.patient_id == patient_id)
    if lab_result_id:
        query = query.filter(LabAITask.lab_result_id == lab_result_id)
    if ap_report_id:
        query = query.filter(LabAITask.ap_report_id == ap_report_id)
    if domain:
        query = query.filter(LabAITask.domain == domain)
    if task_type:
        query = query.filter(LabAITask.task_type == task_type)
    if status:
        query = query.filter(LabAITask.status == status)
    return query.order_by(LabAITask.requested_at.desc()).all()

@app.get("/api/v1/lab-ai/tasks/{task_id}", response_model=LabAITaskResponse, tags=["AI Tasks"])
async def get_ai_task(task_id: UUID, db: Session = Depends(get_db)):
    """Get AI task details and status"""
    ai_task = db.query(LabAITask).filter(LabAITask.id == task_id).first()
    if not ai_task:
        raise HTTPException(status_code=404, detail="AI task not found")
    return ai_task

@app.patch("/api/v1/lab-ai/tasks/{task_id}/status", response_model=LabAITaskResponse, tags=["AI Tasks"])
async def update_task_status(
    task_id: UUID,
    status: str,
    error_message: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Update AI task status (typically called by AI workers)
    """
    ai_task = db.query(LabAITask).filter(LabAITask.id == task_id).first()
    if not ai_task:
        raise HTTPException(status_code=404, detail="AI task not found")

    old_status = ai_task.status
    ai_task.status = status

    if status == 'completed':
        ai_task.completed_at = datetime.utcnow()
        await publish_event(EventType.LAB_AI_TASK_COMPLETED, {
            "ai_task_id": str(ai_task.id),
            "domain": ai_task.domain,
            "task_type": ai_task.task_type
        })
    elif status == 'failed':
        ai_task.error_message = error_message
        ai_task.completed_at = datetime.utcnow()
        await publish_event(EventType.LAB_AI_TASK_FAILED, {
            "ai_task_id": str(ai_task.id),
            "domain": ai_task.domain,
            "task_type": ai_task.task_type,
            "error": error_message
        })

    db.commit()
    db.refresh(ai_task)

    logger.info(f"Lab AI task status updated: {task_id} - {status}")
    return ai_task

# Lab AI Output Endpoints
@app.post("/api/v1/lab-ai/outputs", response_model=LabAIOutputResponse, status_code=201, tags=["AI Outputs"])
async def create_ai_output(
    output_data: LabAIOutputCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Store AI analysis output
    Typically called by AI workers after inference completes
    """
    # Verify task exists
    ai_task = db.query(LabAITask).filter(LabAITask.id == output_data.lab_ai_task_id).first()
    if not ai_task:
        raise HTTPException(status_code=404, detail="AI task not found")

    ai_output = LabAIOutput(
        lab_ai_task_id=output_data.lab_ai_task_id,
        output_type=output_data.output_type,
        payload=output_data.payload
    )
    db.add(ai_output)
    db.commit()
    db.refresh(ai_output)

    await publish_event(EventType.LAB_AI_OUTPUT_CREATED, {
        "output_id": str(ai_output.id),
        "ai_task_id": str(ai_task.id),
        "output_type": ai_output.output_type,
        "domain": ai_task.domain
    })

    logger.info(f"Lab AI output created: {ai_output.id} - {output_data.output_type}")
    return ai_output

@app.get("/api/v1/lab-ai/outputs", response_model=List[LabAIOutputResponse], tags=["AI Outputs"])
async def list_ai_outputs(
    lab_ai_task_id: UUID,
    db: Session = Depends(get_db)
):
    """List all outputs for an AI task"""
    return db.query(LabAIOutput).filter(
        LabAIOutput.lab_ai_task_id == lab_ai_task_id
    ).order_by(LabAIOutput.created_at).all()

@app.get("/api/v1/lab-ai/outputs/{output_id}", response_model=LabAIOutputResponse, tags=["AI Outputs"])
async def get_ai_output(output_id: UUID, db: Session = Depends(get_db)):
    """Get AI output details"""
    ai_output = db.query(LabAIOutput).filter(LabAIOutput.id == output_id).first()
    if not ai_output:
        raise HTTPException(status_code=404, detail="AI output not found")
    return ai_output

@app.get("/health", tags=["System"])
async def health_check():
    return {"service": "lab-ai-orchestrator-service", "status": "healthy", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8041)
