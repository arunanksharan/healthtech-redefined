"""
Guideline Engine / CDS Service - Port 8028
Clinical decision support with guideline management and rule evaluation
"""
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import Session, sessionmaker

from shared.database.models import (
    Guideline, GuidelineVersion, CDSRule, CDSRuleTrigger, CDSEvaluation,
    Patient, Encounter, Tenant
)
from shared.events.types import EventType
from shared.events.publisher import publish_event
from schemas import (
    GuidelineCreate, GuidelineResponse,
    GuidelineVersionCreate, GuidelineVersionUpdate, GuidelineVersionResponse,
    CDSRuleCreate, CDSRuleResponse,
    CDSRuleTriggerCreate, CDSRuleTriggerResponse,
    CDSEvaluationRequest, CDSEvaluationResponse,
    CDSFeedbackRequest
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Guideline Engine / CDS Service", version="0.1.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Guideline Endpoints
@app.post("/api/v1/guidelines", response_model=GuidelineResponse, status_code=201, tags=["Guidelines"])
async def create_guideline(
    guideline_data: GuidelineCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create a new clinical guideline"""
    # Check for duplicate code
    existing = db.query(Guideline).filter(and_(
        Guideline.tenant_id == guideline_data.tenant_id,
        Guideline.code == guideline_data.code
    )).first()
    if existing:
        raise HTTPException(status_code=400, detail="Guideline code already exists")

    guideline = Guideline(
        tenant_id=guideline_data.tenant_id,
        code=guideline_data.code,
        name=guideline_data.name,
        description=guideline_data.description,
        specialty=guideline_data.specialty,
        source=guideline_data.source,
        category=guideline_data.category
    )
    db.add(guideline)
    db.commit()
    db.refresh(guideline)

    await publish_event(EventType.GUIDELINE_CREATED, {
        "guideline_id": str(guideline.id),
        "code": guideline.code,
        "name": guideline.name,
        "specialty": guideline.specialty
    })

    logger.info(f"Guideline created: {guideline.code}")
    return guideline

@app.get("/api/v1/guidelines", response_model=List[GuidelineResponse], tags=["Guidelines"])
async def list_guidelines(
    tenant_id: Optional[UUID] = Query(None),
    specialty: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List all guidelines with optional filters"""
    query = db.query(Guideline)
    if tenant_id:
        query = query.filter(Guideline.tenant_id == tenant_id)
    if specialty:
        query = query.filter(Guideline.specialty == specialty)
    if category:
        query = query.filter(Guideline.category == category)
    return query.order_by(Guideline.created_at.desc()).all()

@app.get("/api/v1/guidelines/{guideline_id}", response_model=GuidelineResponse, tags=["Guidelines"])
async def get_guideline(guideline_id: UUID, db: Session = Depends(get_db)):
    """Get guideline details"""
    guideline = db.query(Guideline).filter(Guideline.id == guideline_id).first()
    if not guideline:
        raise HTTPException(status_code=404, detail="Guideline not found")
    return guideline

# Guideline Version Endpoints
@app.post("/api/v1/guidelines/{guideline_id}/versions", response_model=GuidelineVersionResponse, status_code=201, tags=["Guideline Versions"])
async def create_guideline_version(
    guideline_id: UUID,
    version_data: GuidelineVersionCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create a new version of a guideline"""
    # Verify guideline exists
    guideline = db.query(Guideline).filter(Guideline.id == guideline_id).first()
    if not guideline:
        raise HTTPException(status_code=404, detail="Guideline not found")

    # Ensure version belongs to the guideline
    if version_data.guideline_id != guideline_id:
        raise HTTPException(status_code=400, detail="Guideline ID mismatch")

    # Check for duplicate version code
    existing = db.query(GuidelineVersion).filter(and_(
        GuidelineVersion.guideline_id == guideline_id,
        GuidelineVersion.version_code == version_data.version_code
    )).first()
    if existing:
        raise HTTPException(status_code=400, detail="Version code already exists")

    version = GuidelineVersion(
        guideline_id=version_data.guideline_id,
        version_code=version_data.version_code,
        description=version_data.description,
        effective_from=version_data.effective_from,
        effective_to=version_data.effective_to,
        status=version_data.status,
        content=version_data.content
    )
    db.add(version)
    db.commit()
    db.refresh(version)

    logger.info(f"Guideline version created: {guideline.code} - {version.version_code}")
    return version

@app.get("/api/v1/guidelines/{guideline_id}/versions", response_model=List[GuidelineVersionResponse], tags=["Guideline Versions"])
async def list_guideline_versions(
    guideline_id: UUID,
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List all versions for a guideline"""
    query = db.query(GuidelineVersion).filter(GuidelineVersion.guideline_id == guideline_id)
    if status:
        query = query.filter(GuidelineVersion.status == status)
    return query.order_by(GuidelineVersion.effective_from.desc()).all()

@app.put("/api/v1/guidelines/versions/{version_id}", response_model=GuidelineVersionResponse, tags=["Guideline Versions"])
async def update_guideline_version(
    version_id: UUID,
    version_data: GuidelineVersionUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Update guideline version (typically to activate or deprecate)"""
    version = db.query(GuidelineVersion).filter(GuidelineVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Guideline version not found")

    update_data = version_data.dict(exclude_unset=True)
    old_status = version.status

    for field, value in update_data.items():
        setattr(version, field, value)

    db.commit()
    db.refresh(version)

    # Publish activation/deprecation events
    if old_status != 'active' and version.status == 'active':
        await publish_event(EventType.GUIDELINE_VERSION_ACTIVATED, {
            "version_id": str(version.id),
            "guideline_id": str(version.guideline_id),
            "version_code": version.version_code
        })
    elif old_status == 'active' and version.status == 'deprecated':
        await publish_event(EventType.GUIDELINE_VERSION_DEPRECATED, {
            "version_id": str(version.id),
            "guideline_id": str(version.guideline_id),
            "version_code": version.version_code
        })

    logger.info(f"Guideline version updated: {version_id}")
    return version

# CDS Rule Endpoints
@app.post("/api/v1/guidelines/versions/{version_id}/rules", response_model=CDSRuleResponse, status_code=201, tags=["CDS Rules"])
async def create_cds_rule(
    version_id: UUID,
    rule_data: CDSRuleCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create a CDS rule for a guideline version"""
    # Verify version exists
    version = db.query(GuidelineVersion).filter(GuidelineVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Guideline version not found")

    # Ensure rule belongs to the version
    if rule_data.guideline_version_id != version_id:
        raise HTTPException(status_code=400, detail="Version ID mismatch")

    # Check for duplicate code
    existing = db.query(CDSRule).filter(and_(
        CDSRule.guideline_version_id == version_id,
        CDSRule.code == rule_data.code
    )).first()
    if existing:
        raise HTTPException(status_code=400, detail="Rule code already exists")

    rule = CDSRule(
        guideline_version_id=rule_data.guideline_version_id,
        code=rule_data.code,
        name=rule_data.name,
        description=rule_data.description,
        trigger_context=rule_data.trigger_context,
        priority=rule_data.priority,
        logic_expression=rule_data.logic_expression,
        action_suggestions=rule_data.action_suggestions
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    await publish_event(EventType.CDS_RULE_CREATED, {
        "rule_id": str(rule.id),
        "version_id": str(version.id),
        "rule_code": rule.code,
        "trigger_context": rule.trigger_context
    })

    logger.info(f"CDS rule created: {rule.code}")
    return rule

@app.get("/api/v1/guidelines/versions/{version_id}/rules", response_model=List[CDSRuleResponse], tags=["CDS Rules"])
async def list_cds_rules(
    version_id: UUID,
    trigger_context: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List all CDS rules for a guideline version"""
    query = db.query(CDSRule).filter(CDSRule.guideline_version_id == version_id)
    if trigger_context:
        query = query.filter(CDSRule.trigger_context == trigger_context)
    if priority:
        query = query.filter(CDSRule.priority == priority)
    return query.all()

@app.get("/api/v1/cds/rules/{rule_id}", response_model=CDSRuleResponse, tags=["CDS Rules"])
async def get_cds_rule(rule_id: UUID, db: Session = Depends(get_db)):
    """Get CDS rule details"""
    rule = db.query(CDSRule).filter(CDSRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="CDS rule not found")
    return rule

# CDS Rule Trigger Endpoints
@app.post("/api/v1/cds/rules/{rule_id}/triggers", response_model=CDSRuleTriggerResponse, status_code=201, tags=["CDS Triggers"])
async def add_rule_trigger(
    rule_id: UUID,
    trigger_data: CDSRuleTriggerCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Add event-based trigger to CDS rule"""
    # Verify rule exists
    rule = db.query(CDSRule).filter(CDSRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="CDS rule not found")

    # Ensure trigger belongs to the rule
    if trigger_data.cds_rule_id != rule_id:
        raise HTTPException(status_code=400, detail="Rule ID mismatch")

    trigger = CDSRuleTrigger(
        cds_rule_id=trigger_data.cds_rule_id,
        trigger_event_type=trigger_data.trigger_event_type,
        filter_criteria=trigger_data.filter_criteria
    )
    db.add(trigger)
    db.commit()
    db.refresh(trigger)

    logger.info(f"CDS rule trigger added: {rule.code} - {trigger.trigger_event_type}")
    return trigger

@app.get("/api/v1/cds/rules/{rule_id}/triggers", response_model=List[CDSRuleTriggerResponse], tags=["CDS Triggers"])
async def list_rule_triggers(rule_id: UUID, db: Session = Depends(get_db)):
    """List all triggers for a CDS rule"""
    return db.query(CDSRuleTrigger).filter(CDSRuleTrigger.cds_rule_id == rule_id).all()

# CDS Evaluation Endpoints
@app.post("/api/v1/cds/evaluate", response_model=List[CDSEvaluationResponse], tags=["CDS Evaluation"])
async def evaluate_cds_rules(
    eval_request: CDSEvaluationRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Evaluate CDS rules for a patient context
    Returns list of fired CDS cards
    """
    # Get active guideline versions
    query = db.query(GuidelineVersion).filter(GuidelineVersion.status == 'active')

    if eval_request.guideline_code:
        guideline = db.query(Guideline).filter(Guideline.code == eval_request.guideline_code).first()
        if guideline:
            query = query.filter(GuidelineVersion.guideline_id == guideline.id)

    active_versions = query.all()

    # Get all active CDS rules for the trigger context
    rules = []
    for version in active_versions:
        version_rules = db.query(CDSRule).filter(and_(
            CDSRule.guideline_version_id == version.id,
            CDSRule.trigger_context == eval_request.trigger_context
        )).all()
        rules.extend(version_rules)

    # Evaluate each rule (simplified - in production would use DSL evaluator)
    fired_evaluations = []
    for rule in rules:
        # In production: evaluate rule.logic_expression against eval_request.context_data
        # For now, we'll create a simple evaluation record

        evaluation = CDSEvaluation(
            cds_rule_id=rule.id,
            patient_id=eval_request.patient_id,
            encounter_id=eval_request.encounter_id,
            evaluated_at=datetime.utcnow(),
            result='fired',  # In production: 'fired' or 'not_fired' based on logic evaluation
            card_payload={
                "rule_code": rule.code,
                "rule_name": rule.name,
                "priority": rule.priority,
                "description": rule.description,
                "action_suggestions": rule.action_suggestions,
                "context": eval_request.trigger_context
            }
        )
        db.add(evaluation)
        fired_evaluations.append(evaluation)

    db.commit()

    # Publish event for each fired rule
    for evaluation in fired_evaluations:
        await publish_event(EventType.CDS_EVALUATION_FIRED, {
            "evaluation_id": str(evaluation.id),
            "rule_id": str(evaluation.cds_rule_id),
            "patient_id": str(evaluation.patient_id),
            "encounter_id": str(evaluation.encounter_id) if evaluation.encounter_id else None,
            "priority": evaluation.card_payload.get("priority")
        })

    logger.info(f"CDS evaluation completed: {len(fired_evaluations)} rules fired")

    # Refresh all to get IDs
    for evaluation in fired_evaluations:
        db.refresh(evaluation)

    return fired_evaluations

@app.get("/api/v1/cds/evaluations", response_model=List[CDSEvaluationResponse], tags=["CDS Evaluation"])
async def list_cds_evaluations(
    patient_id: Optional[UUID] = Query(None),
    encounter_id: Optional[UUID] = Query(None),
    result: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List CDS evaluations with filters"""
    query = db.query(CDSEvaluation)
    if patient_id:
        query = query.filter(CDSEvaluation.patient_id == patient_id)
    if encounter_id:
        query = query.filter(CDSEvaluation.encounter_id == encounter_id)
    if result:
        query = query.filter(CDSEvaluation.result == result)
    return query.order_by(CDSEvaluation.evaluated_at.desc()).all()

@app.post("/api/v1/cds/evaluations/{evaluation_id}/feedback", tags=["CDS Evaluation"])
async def record_cds_feedback(
    evaluation_id: UUID,
    feedback: CDSFeedbackRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Record clinician feedback on CDS recommendation"""
    evaluation = db.query(CDSEvaluation).filter(CDSEvaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    evaluation.accepted = feedback.accepted
    evaluation.feedback_notes = feedback.feedback_notes

    db.commit()

    # Publish acceptance/rejection events
    if feedback.accepted:
        await publish_event(EventType.CDS_CARD_ACCEPTED, {
            "evaluation_id": str(evaluation.id),
            "rule_id": str(evaluation.cds_rule_id),
            "patient_id": str(evaluation.patient_id),
            "action_taken": feedback.action_taken
        })
    else:
        await publish_event(EventType.CDS_CARD_REJECTED, {
            "evaluation_id": str(evaluation.id),
            "rule_id": str(evaluation.cds_rule_id),
            "patient_id": str(evaluation.patient_id),
            "feedback_notes": feedback.feedback_notes
        })

    logger.info(f"CDS feedback recorded: {evaluation_id} - {'accepted' if feedback.accepted else 'rejected'}")
    return {
        "message": "Feedback recorded",
        "evaluation_id": str(evaluation_id),
        "accepted": feedback.accepted
    }

@app.get("/health", tags=["System"])
async def health_check():
    return {"service": "guideline-engine-service", "status": "healthy", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8028)
