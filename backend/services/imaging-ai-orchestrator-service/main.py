"""
Imaging AI Orchestrator Service - Port 8035
Manages AI workflows for imaging: triage, quality checks, detection, and report assistance
"""
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import Session, sessionmaker

from shared.database.models import (
    ImagingAIModel, ImagingAITask, ImagingAIOutput,
    ImagingStudy, RadiologyWorklistItem, Tenant
)
from shared.events.types import EventType
from shared.events.publisher import publish_event
from schemas import (
    ImagingAIModelCreate, ImagingAIModelResponse,
    ImagingAITaskCreate, ImagingAITaskResponse,
    ImagingAIOutputCreate, ImagingAIOutputResponse
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Imaging AI Orchestrator Service", version="0.1.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Imaging AI Model Endpoints
@app.post("/api/v1/imaging-ai/models", response_model=ImagingAIModelResponse, status_code=201, tags=["AI Models"])
async def create_ai_model(
    model_data: ImagingAIModelCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Register an imaging AI model"""
    existing = db.query(ImagingAIModel).filter(ImagingAIModel.code == model_data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="AI model code already exists")

    ai_model = ImagingAIModel(
        tenant_id=model_data.tenant_id,
        code=model_data.code,
        name=model_data.name,
        description=model_data.description,
        modality_code=model_data.modality_code,
        body_part=model_data.body_part,
        capabilities=model_data.capabilities,
        vendor=model_data.vendor,
        version=model_data.version,
        endpoint_config=model_data.endpoint_config
    )
    db.add(ai_model)
    db.commit()
    db.refresh(ai_model)

    logger.info(f"Imaging AI model registered: {ai_model.code}")
    return ai_model

@app.get("/api/v1/imaging-ai/models", response_model=List[ImagingAIModelResponse], tags=["AI Models"])
async def list_ai_models(
    modality_code: Optional[str] = Query(None),
    body_part: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List all imaging AI models"""
    query = db.query(ImagingAIModel)
    if modality_code:
        query = query.filter(ImagingAIModel.modality_code == modality_code)
    if body_part:
        query = query.filter(ImagingAIModel.body_part == body_part)
    if is_active is not None:
        query = query.filter(ImagingAIModel.is_active == is_active)
    return query.all()

@app.get("/api/v1/imaging-ai/models/{model_id}", response_model=ImagingAIModelResponse, tags=["AI Models"])
async def get_ai_model(model_id: UUID, db: Session = Depends(get_db)):
    """Get AI model details"""
    ai_model = db.query(ImagingAIModel).filter(ImagingAIModel.id == model_id).first()
    if not ai_model:
        raise HTTPException(status_code=404, detail="AI model not found")
    return ai_model

# Imaging AI Task Endpoints
@app.post("/api/v1/imaging-ai/tasks", response_model=ImagingAITaskResponse, status_code=201, tags=["AI Tasks"])
async def create_ai_task(
    task_data: ImagingAITaskCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Request AI analysis for an imaging study
    Creates a task that will be processed by AI workers
    """
    # Verify imaging study exists
    study = db.query(ImagingStudy).filter(ImagingStudy.id == task_data.imaging_study_id).first()
    if not study:
        raise HTTPException(status_code=404, detail="Imaging study not found")

    # Verify AI model exists
    ai_model = db.query(ImagingAIModel).filter(ImagingAIModel.id == task_data.ai_model_id).first()
    if not ai_model:
        raise HTTPException(status_code=404, detail="AI model not found")

    # Check if AI model supports the requested task type
    if not ai_model.capabilities.get(task_data.task_type, False):
        raise HTTPException(status_code=400, detail=f"AI model does not support {task_data.task_type}")

    # Check for duplicate task
    existing = db.query(ImagingAITask).filter(and_(
        ImagingAITask.imaging_study_id == task_data.imaging_study_id,
        ImagingAITask.ai_model_id == task_data.ai_model_id,
        ImagingAITask.task_type == task_data.task_type,
        ImagingAITask.status.in_(['queued', 'running', 'completed'])
    )).first()
    if existing:
        logger.info(f"Returning existing AI task: {existing.id}")
        return existing

    ai_task = ImagingAITask(
        tenant_id=study.tenant_id,
        imaging_study_id=task_data.imaging_study_id,
        ai_model_id=task_data.ai_model_id,
        task_type=task_data.task_type,
        status='queued',
        requested_at=datetime.utcnow()
    )
    db.add(ai_task)
    db.commit()
    db.refresh(ai_task)

    await publish_event(EventType.IMAGING_AI_TASK_CREATED, {
        "ai_task_id": str(ai_task.id),
        "imaging_study_id": str(ai_task.imaging_study_id),
        "ai_model_code": ai_model.code,
        "task_type": ai_task.task_type
    })

    logger.info(f"Imaging AI task created: {ai_task.id} - {ai_task.task_type}")
    return ai_task

@app.get("/api/v1/imaging-ai/tasks", response_model=List[ImagingAITaskResponse], tags=["AI Tasks"])
async def list_ai_tasks(
    imaging_study_id: Optional[UUID] = Query(None),
    task_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List AI tasks with filters"""
    query = db.query(ImagingAITask)
    if imaging_study_id:
        query = query.filter(ImagingAITask.imaging_study_id == imaging_study_id)
    if task_type:
        query = query.filter(ImagingAITask.task_type == task_type)
    if status:
        query = query.filter(ImagingAITask.status == status)
    return query.order_by(ImagingAITask.requested_at.desc()).all()

@app.get("/api/v1/imaging-ai/tasks/{task_id}", response_model=ImagingAITaskResponse, tags=["AI Tasks"])
async def get_ai_task(task_id: UUID, db: Session = Depends(get_db)):
    """Get AI task details and status"""
    ai_task = db.query(ImagingAITask).filter(ImagingAITask.id == task_id).first()
    if not ai_task:
        raise HTTPException(status_code=404, detail="AI task not found")
    return ai_task

@app.patch("/api/v1/imaging-ai/tasks/{task_id}/status", response_model=ImagingAITaskResponse, tags=["AI Tasks"])
async def update_task_status(
    task_id: UUID,
    status: str,
    error_message: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Update AI task status (typically called by AI workers)
    """
    ai_task = db.query(ImagingAITask).filter(ImagingAITask.id == task_id).first()
    if not ai_task:
        raise HTTPException(status_code=404, detail="AI task not found")

    old_status = ai_task.status
    ai_task.status = status

    if status == 'running' and old_status == 'queued':
        # Task started processing
        pass
    elif status == 'completed':
        ai_task.completed_at = datetime.utcnow()
        await publish_event(EventType.IMAGING_AI_TASK_COMPLETED, {
            "ai_task_id": str(ai_task.id),
            "imaging_study_id": str(ai_task.imaging_study_id),
            "task_type": ai_task.task_type
        })
    elif status == 'failed':
        ai_task.error_message = error_message
        ai_task.completed_at = datetime.utcnow()
        await publish_event(EventType.IMAGING_AI_TASK_FAILED, {
            "ai_task_id": str(ai_task.id),
            "imaging_study_id": str(ai_task.imaging_study_id),
            "task_type": ai_task.task_type,
            "error": error_message
        })

    db.commit()
    db.refresh(ai_task)

    logger.info(f"AI task status updated: {task_id} - {status}")
    return ai_task

# Imaging AI Output Endpoints
@app.post("/api/v1/imaging-ai/outputs", response_model=ImagingAIOutputResponse, status_code=201, tags=["AI Outputs"])
async def create_ai_output(
    output_data: ImagingAIOutputCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Store AI analysis output
    Typically called by AI workers after inference completes
    """
    # Verify task exists
    ai_task = db.query(ImagingAITask).filter(ImagingAITask.id == output_data.imaging_ai_task_id).first()
    if not ai_task:
        raise HTTPException(status_code=404, detail="AI task not found")

    ai_output = ImagingAIOutput(
        imaging_ai_task_id=output_data.imaging_ai_task_id,
        output_type=output_data.output_type,
        payload=output_data.payload
    )
    db.add(ai_output)
    db.commit()
    db.refresh(ai_output)

    # If this is a triage output, update worklist item
    if output_data.output_type == 'triage':
        worklist_item = db.query(RadiologyWorklistItem).filter(
            RadiologyWorklistItem.imaging_study_id == ai_task.imaging_study_id
        ).first()

        if worklist_item:
            triage_score = output_data.payload.get('triage_score')
            triage_flags = output_data.payload.get('flags', [])

            worklist_item.ai_triage_score = triage_score
            worklist_item.ai_triage_flags = {'flags': triage_flags}
            db.commit()

            logger.info(f"Worklist item updated with triage data: {worklist_item.id}")

    await publish_event(EventType.IMAGING_AI_OUTPUT_CREATED, {
        "output_id": str(ai_output.id),
        "ai_task_id": str(ai_task.id),
        "imaging_study_id": str(ai_task.imaging_study_id),
        "output_type": ai_output.output_type
    })

    logger.info(f"AI output created: {ai_output.id} - {output_data.output_type}")
    return ai_output

@app.get("/api/v1/imaging-ai/outputs", response_model=List[ImagingAIOutputResponse], tags=["AI Outputs"])
async def list_ai_outputs(
    imaging_ai_task_id: UUID,
    db: Session = Depends(get_db)
):
    """List all outputs for an AI task"""
    return db.query(ImagingAIOutput).filter(
        ImagingAIOutput.imaging_ai_task_id == imaging_ai_task_id
    ).order_by(ImagingAIOutput.created_at).all()

@app.get("/api/v1/imaging-ai/outputs/{output_id}", response_model=ImagingAIOutputResponse, tags=["AI Outputs"])
async def get_ai_output(output_id: UUID, db: Session = Depends(get_db)):
    """Get AI output details"""
    ai_output = db.query(ImagingAIOutput).filter(ImagingAIOutput.id == output_id).first()
    if not ai_output:
        raise HTTPException(status_code=404, detail="AI output not found")
    return ai_output

@app.get("/health", tags=["System"])
async def health_check():
    return {"service": "imaging-ai-orchestrator-service", "status": "healthy", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8035)
