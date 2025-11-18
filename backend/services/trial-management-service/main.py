"""
Trial Management Service - Port 8027
Clinical trial protocol management, subject enrollment, visit tracking, and CRF management
"""
import logging
import random
from datetime import datetime, date, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import Session, sessionmaker

from shared.database.models import (
    Trial, TrialArm, TrialVisit, TrialSubject, TrialSubjectVisit,
    TrialCRF, TrialCRFResponse, TrialProtocolDeviation,
    Patient, PseudoIdSpace, Tenant
)
from shared.events.types import EventType
from shared.events.publisher import publish_event
from schemas import (
    TrialCreate, TrialUpdate, TrialResponse,
    TrialArmCreate, TrialArmResponse,
    TrialVisitCreate, TrialVisitResponse,
    TrialSubjectCreate, TrialSubjectUpdate, TrialSubjectResponse, SubjectRandomizeRequest,
    TrialSubjectVisitCreate, TrialSubjectVisitUpdate, TrialSubjectVisitResponse,
    TrialCRFCreate, TrialCRFResponse,
    TrialCRFResponseCreate, TrialCRFResponseResponse,
    TrialProtocolDeviationCreate, TrialProtocolDeviationResponse
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Trial Management Service", version="0.1.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Trial Endpoints
@app.post("/api/v1/trials", response_model=TrialResponse, status_code=201, tags=["Trials"])
async def create_trial(
    trial_data: TrialCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create a new clinical trial"""
    # Check for duplicate code
    existing = db.query(Trial).filter(and_(
        Trial.tenant_id == trial_data.tenant_id,
        Trial.code == trial_data.code
    )).first()
    if existing:
        raise HTTPException(status_code=400, detail="Trial code already exists")

    trial = Trial(
        tenant_id=trial_data.tenant_id,
        code=trial_data.code,
        title=trial_data.title,
        description=trial_data.description,
        phase=trial_data.phase,
        sponsor_org_id=trial_data.sponsor_org_id,
        status=trial_data.status,
        target_enrollment=trial_data.target_enrollment,
        inclusion_criteria=trial_data.inclusion_criteria,
        exclusion_criteria=trial_data.exclusion_criteria,
        registry_reference=trial_data.registry_reference
    )
    db.add(trial)
    db.commit()
    db.refresh(trial)

    await publish_event(EventType.TRIAL_CREATED, {
        "trial_id": str(trial.id),
        "code": trial.code,
        "title": trial.title,
        "phase": trial.phase
    })

    logger.info(f"Trial created: {trial.code}")
    return trial

@app.get("/api/v1/trials", response_model=List[TrialResponse], tags=["Trials"])
async def list_trials(
    tenant_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    phase: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List all trials with optional filters"""
    query = db.query(Trial)
    if tenant_id:
        query = query.filter(Trial.tenant_id == tenant_id)
    if status:
        query = query.filter(Trial.status == status)
    if phase:
        query = query.filter(Trial.phase == phase)
    return query.order_by(Trial.created_at.desc()).all()

@app.get("/api/v1/trials/{trial_id}", response_model=TrialResponse, tags=["Trials"])
async def get_trial(trial_id: UUID, db: Session = Depends(get_db)):
    """Get trial details"""
    trial = db.query(Trial).filter(Trial.id == trial_id).first()
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    return trial

@app.put("/api/v1/trials/{trial_id}", response_model=TrialResponse, tags=["Trials"])
async def update_trial(
    trial_id: UUID,
    trial_data: TrialUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Update trial details"""
    trial = db.query(Trial).filter(Trial.id == trial_id).first()
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")

    update_data = trial_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(trial, field, value)

    trial.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(trial)

    await publish_event(EventType.TRIAL_UPDATED, {
        "trial_id": str(trial.id),
        "code": trial.code,
        "updated_fields": list(update_data.keys())
    })

    logger.info(f"Trial updated: {trial.code}")
    return trial

# Trial Arm Endpoints
@app.post("/api/v1/trials/{trial_id}/arms", response_model=TrialArmResponse, status_code=201, tags=["Trial Arms"])
async def add_trial_arm(
    trial_id: UUID,
    arm_data: TrialArmCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Add randomization arm to trial"""
    # Verify trial exists
    trial = db.query(Trial).filter(Trial.id == trial_id).first()
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")

    # Ensure arm belongs to the trial
    if arm_data.trial_id != trial_id:
        raise HTTPException(status_code=400, detail="Trial ID mismatch")

    # Check for duplicate code
    existing = db.query(TrialArm).filter(and_(
        TrialArm.trial_id == trial_id,
        TrialArm.code == arm_data.code
    )).first()
    if existing:
        raise HTTPException(status_code=400, detail="Arm code already exists")

    arm = TrialArm(
        trial_id=arm_data.trial_id,
        code=arm_data.code,
        name=arm_data.name,
        description=arm_data.description,
        randomization_ratio=arm_data.randomization_ratio
    )
    db.add(arm)
    db.commit()
    db.refresh(arm)

    logger.info(f"Trial arm added: {trial.code} - {arm.code}")
    return arm

@app.get("/api/v1/trials/{trial_id}/arms", response_model=List[TrialArmResponse], tags=["Trial Arms"])
async def list_trial_arms(trial_id: UUID, db: Session = Depends(get_db)):
    """List all arms for a trial"""
    return db.query(TrialArm).filter(TrialArm.trial_id == trial_id).all()

# Trial Visit Endpoints
@app.post("/api/v1/trials/{trial_id}/visits", response_model=TrialVisitResponse, status_code=201, tags=["Trial Visits"])
async def add_trial_visit(
    trial_id: UUID,
    visit_data: TrialVisitCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Add visit definition to trial protocol"""
    # Verify trial exists
    trial = db.query(Trial).filter(Trial.id == trial_id).first()
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")

    # Ensure visit belongs to the trial
    if visit_data.trial_id != trial_id:
        raise HTTPException(status_code=400, detail="Trial ID mismatch")

    # Check for duplicate code
    existing = db.query(TrialVisit).filter(and_(
        TrialVisit.trial_id == trial_id,
        TrialVisit.code == visit_data.code
    )).first()
    if existing:
        raise HTTPException(status_code=400, detail="Visit code already exists")

    visit = TrialVisit(
        trial_id=visit_data.trial_id,
        code=visit_data.code,
        name=visit_data.name,
        visit_day=visit_data.visit_day,
        window_days_before=visit_data.window_days_before,
        window_days_after=visit_data.window_days_after,
        is_required=visit_data.is_required
    )
    db.add(visit)
    db.commit()
    db.refresh(visit)

    logger.info(f"Trial visit added: {trial.code} - {visit.code}")
    return visit

@app.get("/api/v1/trials/{trial_id}/visits", response_model=List[TrialVisitResponse], tags=["Trial Visits"])
async def list_trial_visits(trial_id: UUID, db: Session = Depends(get_db)):
    """List all visit definitions for a trial"""
    return db.query(TrialVisit).filter(
        TrialVisit.trial_id == trial_id
    ).order_by(TrialVisit.visit_day).all()

# Trial Subject Endpoints
@app.post("/api/v1/trials/subjects", response_model=TrialSubjectResponse, status_code=201, tags=["Trial Subjects"])
async def screen_trial_subject(
    subject_data: TrialSubjectCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Screen a patient for trial enrollment"""
    # Verify trial exists
    trial = db.query(Trial).filter(Trial.id == subject_data.trial_id).first()
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")

    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == subject_data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Check for existing screening
    existing = db.query(TrialSubject).filter(and_(
        TrialSubject.trial_id == subject_data.trial_id,
        TrialSubject.patient_id == subject_data.patient_id
    )).first()
    if existing:
        raise HTTPException(status_code=400, detail="Patient already screened for this trial")

    subject = TrialSubject(
        trial_id=subject_data.trial_id,
        patient_id=subject_data.patient_id,
        pseudo_id_space_id=subject_data.pseudo_id_space_id,
        screening_status=subject_data.screening_status,
        consent_record_id=subject_data.consent_record_id,
        status='screening',
        screening_notes=subject_data.screening_notes
    )
    db.add(subject)
    db.commit()
    db.refresh(subject)

    await publish_event(EventType.TRIAL_SUBJECT_SCREENED, {
        "subject_id": str(subject.id),
        "trial_id": str(trial.id),
        "trial_code": trial.code,
        "patient_id": str(subject.patient_id),
        "screening_status": subject.screening_status
    })

    logger.info(f"Trial subject screened: {trial.code} - Patient {patient.id}")
    return subject

@app.get("/api/v1/trials/subjects", response_model=List[TrialSubjectResponse], tags=["Trial Subjects"])
async def list_trial_subjects(
    trial_id: Optional[UUID] = Query(None),
    patient_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    screening_status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List trial subjects with filters"""
    query = db.query(TrialSubject)
    if trial_id:
        query = query.filter(TrialSubject.trial_id == trial_id)
    if patient_id:
        query = query.filter(TrialSubject.patient_id == patient_id)
    if status:
        query = query.filter(TrialSubject.status == status)
    if screening_status:
        query = query.filter(TrialSubject.screening_status == screening_status)
    return query.order_by(TrialSubject.created_at.desc()).all()

@app.put("/api/v1/trials/subjects/{subject_id}", response_model=TrialSubjectResponse, tags=["Trial Subjects"])
async def update_trial_subject(
    subject_id: UUID,
    subject_data: TrialSubjectUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Update trial subject (screening status, enrollment, withdrawal)"""
    subject = db.query(TrialSubject).filter(TrialSubject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Trial subject not found")

    update_data = subject_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(subject, field, value)

    db.commit()
    db.refresh(subject)

    # Publish withdrawal event if withdrawn
    if subject.status == 'withdrawn':
        await publish_event(EventType.TRIAL_SUBJECT_WITHDRAWN, {
            "subject_id": str(subject.id),
            "trial_id": str(subject.trial_id),
            "patient_id": str(subject.patient_id),
            "withdrawal_reason": subject.withdrawal_reason
        })

    logger.info(f"Trial subject updated: {subject_id}")
    return subject

@app.post("/api/v1/trials/subjects/{subject_id}/randomize", response_model=TrialSubjectResponse, tags=["Trial Subjects"])
async def randomize_trial_subject(
    subject_id: UUID,
    randomize_data: SubjectRandomizeRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Randomize subject to trial arm"""
    subject = db.query(TrialSubject).filter(TrialSubject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Trial subject not found")

    if subject.screening_status != 'enrolled':
        raise HTTPException(status_code=400, detail="Subject must have screening_status='enrolled' before randomization")

    # Get trial arms
    arms = db.query(TrialArm).filter(TrialArm.trial_id == subject.trial_id).all()
    if not arms:
        raise HTTPException(status_code=400, detail="No trial arms defined")

    # Weighted randomization based on ratios
    weights = [arm.randomization_ratio for arm in arms]
    selected_arm = random.choices(arms, weights=weights, k=1)[0]

    subject.arm_id = selected_arm.id
    subject.enrollment_date = randomize_data.enrollment_date
    subject.status = 'enrolled'

    db.commit()
    db.refresh(subject)

    await publish_event(EventType.TRIAL_SUBJECT_RANDOMIZED, {
        "subject_id": str(subject.id),
        "trial_id": str(subject.trial_id),
        "arm_id": str(selected_arm.id),
        "arm_code": selected_arm.code,
        "enrollment_date": randomize_data.enrollment_date.isoformat()
    })

    logger.info(f"Trial subject randomized: {subject_id} to arm {selected_arm.code}")
    return subject

@app.post("/api/v1/trials/subjects/{subject_id}/generate-visits", status_code=201, tags=["Trial Subjects"])
async def generate_subject_visits(
    subject_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Generate visit schedule for enrolled subject based on trial protocol"""
    subject = db.query(TrialSubject).filter(TrialSubject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Trial subject not found")

    if not subject.enrollment_date:
        raise HTTPException(status_code=400, detail="Subject must have enrollment_date")

    # Get all trial visits
    trial_visits = db.query(TrialVisit).filter(TrialVisit.trial_id == subject.trial_id).all()
    if not trial_visits:
        raise HTTPException(status_code=400, detail="No trial visits defined")

    created_visits = []
    for trial_visit in trial_visits:
        scheduled_date = subject.enrollment_date + timedelta(days=trial_visit.visit_day)

        # Check if visit already exists
        existing = db.query(TrialSubjectVisit).filter(and_(
            TrialSubjectVisit.trial_subject_id == subject_id,
            TrialSubjectVisit.trial_visit_id == trial_visit.id
        )).first()

        if not existing:
            subject_visit = TrialSubjectVisit(
                trial_subject_id=subject_id,
                trial_visit_id=trial_visit.id,
                scheduled_date=scheduled_date,
                status='scheduled'
            )
            db.add(subject_visit)
            created_visits.append({
                "visit_code": trial_visit.code,
                "scheduled_date": scheduled_date.isoformat()
            })

    db.commit()

    await publish_event(EventType.TRIAL_VISIT_SCHEDULED, {
        "subject_id": str(subject_id),
        "trial_id": str(subject.trial_id),
        "visits_created": len(created_visits),
        "visits": created_visits
    })

    logger.info(f"Generated {len(created_visits)} visits for subject {subject_id}")
    return {"message": f"Generated {len(created_visits)} visits", "visits": created_visits}

# Trial Subject Visit Endpoints
@app.get("/api/v1/trials/subject-visits", response_model=List[TrialSubjectVisitResponse], tags=["Subject Visits"])
async def list_subject_visits(
    trial_subject_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List subject visits with filters"""
    query = db.query(TrialSubjectVisit)
    if trial_subject_id:
        query = query.filter(TrialSubjectVisit.trial_subject_id == trial_subject_id)
    if status:
        query = query.filter(TrialSubjectVisit.status == status)
    return query.order_by(TrialSubjectVisit.scheduled_date).all()

@app.put("/api/v1/trials/subject-visits/{visit_id}", response_model=TrialSubjectVisitResponse, tags=["Subject Visits"])
async def update_subject_visit(
    visit_id: UUID,
    visit_data: TrialSubjectVisitUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Update subject visit (mark completed, missed, etc)"""
    visit = db.query(TrialSubjectVisit).filter(TrialSubjectVisit.id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Subject visit not found")

    update_data = visit_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(visit, field, value)

    # Calculate adherence status if actual_date provided
    if visit.actual_date:
        trial_visit = db.query(TrialVisit).filter(TrialVisit.id == visit.trial_visit_id).first()
        if trial_visit:
            days_diff = (visit.actual_date - visit.scheduled_date).days
            if abs(days_diff) <= trial_visit.window_days_before or abs(days_diff) <= trial_visit.window_days_after:
                visit.adherence_status = 'within_window'
            else:
                visit.adherence_status = 'out_of_window'

    db.commit()
    db.refresh(visit)

    # Publish event if completed
    if visit.status == 'completed':
        await publish_event(EventType.TRIAL_VISIT_COMPLETED, {
            "visit_id": str(visit.id),
            "subject_id": str(visit.trial_subject_id),
            "actual_date": visit.actual_date.isoformat() if visit.actual_date else None,
            "adherence_status": visit.adherence_status
        })
    elif visit.status == 'missed':
        await publish_event(EventType.TRIAL_VISIT_MISSED, {
            "visit_id": str(visit.id),
            "subject_id": str(visit.trial_subject_id),
            "scheduled_date": visit.scheduled_date.isoformat()
        })

    logger.info(f"Subject visit updated: {visit_id}")
    return visit

# Trial CRF Endpoints
@app.post("/api/v1/trials/{trial_id}/crfs", response_model=TrialCRFResponse, status_code=201, tags=["CRFs"])
async def add_trial_crf(
    trial_id: UUID,
    crf_data: TrialCRFCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Add CRF definition to trial"""
    # Verify trial exists
    trial = db.query(Trial).filter(Trial.id == trial_id).first()
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")

    # Ensure CRF belongs to the trial
    if crf_data.trial_id != trial_id:
        raise HTTPException(status_code=400, detail="Trial ID mismatch")

    # Check for duplicate code
    existing = db.query(TrialCRF).filter(and_(
        TrialCRF.trial_id == trial_id,
        TrialCRF.code == crf_data.code
    )).first()
    if existing:
        raise HTTPException(status_code=400, detail="CRF code already exists")

    crf = TrialCRF(
        trial_id=crf_data.trial_id,
        code=crf_data.code,
        name=crf_data.name,
        form_version=crf_data.form_version,
        field_definitions=crf_data.field_definitions,
        associated_visit_codes=crf_data.associated_visit_codes
    )
    db.add(crf)
    db.commit()
    db.refresh(crf)

    logger.info(f"Trial CRF added: {trial.code} - {crf.code}")
    return crf

@app.get("/api/v1/trials/{trial_id}/crfs", response_model=List[TrialCRFResponse], tags=["CRFs"])
async def list_trial_crfs(trial_id: UUID, db: Session = Depends(get_db)):
    """List all CRF definitions for a trial"""
    return db.query(TrialCRF).filter(TrialCRF.trial_id == trial_id).all()

# CRF Response Endpoints
@app.post("/api/v1/trials/crf-responses", response_model=TrialCRFResponseResponse, status_code=201, tags=["CRF Responses"])
async def submit_crf_response(
    response_data: TrialCRFResponseCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Submit completed CRF for a trial subject"""
    # Verify subject exists
    subject = db.query(TrialSubject).filter(TrialSubject.id == response_data.trial_subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Trial subject not found")

    # Verify CRF exists
    crf = db.query(TrialCRF).filter(TrialCRF.id == response_data.trial_crf_id).first()
    if not crf:
        raise HTTPException(status_code=404, detail="Trial CRF not found")

    crf_response = TrialCRFResponse(
        trial_subject_id=response_data.trial_subject_id,
        trial_crf_id=response_data.trial_crf_id,
        trial_subject_visit_id=response_data.trial_subject_visit_id,
        response_data=response_data.response_data,
        completed_at=datetime.utcnow(),
        completed_by_user_id=response_data.completed_by_user_id or current_user_id
    )
    db.add(crf_response)
    db.commit()
    db.refresh(crf_response)

    await publish_event(EventType.TRIAL_CRF_COMPLETED, {
        "crf_response_id": str(crf_response.id),
        "subject_id": str(subject.id),
        "crf_code": crf.code,
        "visit_id": str(response_data.trial_subject_visit_id) if response_data.trial_subject_visit_id else None
    })

    logger.info(f"CRF response submitted: {crf.code} for subject {subject.id}")
    return crf_response

@app.get("/api/v1/trials/crf-responses", response_model=List[TrialCRFResponseResponse], tags=["CRF Responses"])
async def list_crf_responses(
    trial_subject_id: Optional[UUID] = Query(None),
    trial_crf_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db)
):
    """List CRF responses with filters"""
    query = db.query(TrialCRFResponse)
    if trial_subject_id:
        query = query.filter(TrialCRFResponse.trial_subject_id == trial_subject_id)
    if trial_crf_id:
        query = query.filter(TrialCRFResponse.trial_crf_id == trial_crf_id)
    return query.order_by(TrialCRFResponse.completed_at.desc()).all()

# Protocol Deviation Endpoints
@app.post("/api/v1/trials/protocol-deviations", response_model=TrialProtocolDeviationResponse, status_code=201, tags=["Protocol Deviations"])
async def create_protocol_deviation(
    deviation_data: TrialProtocolDeviationCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Record protocol deviation for trial subject"""
    # Verify subject exists
    subject = db.query(TrialSubject).filter(TrialSubject.id == deviation_data.trial_subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Trial subject not found")

    deviation = TrialProtocolDeviation(
        trial_subject_id=deviation_data.trial_subject_id,
        deviation_type=deviation_data.deviation_type,
        severity=deviation_data.severity,
        description=deviation_data.description,
        related_visit_id=deviation_data.related_visit_id,
        corrective_action=deviation_data.corrective_action,
        detected_at=datetime.utcnow()
    )
    db.add(deviation)
    db.commit()
    db.refresh(deviation)

    await publish_event(EventType.TRIAL_PROTOCOL_DEVIATION, {
        "deviation_id": str(deviation.id),
        "subject_id": str(subject.id),
        "deviation_type": deviation.deviation_type,
        "severity": deviation.severity
    })

    logger.info(f"Protocol deviation recorded: {deviation.deviation_type} for subject {subject.id}")
    return deviation

@app.get("/api/v1/trials/protocol-deviations", response_model=List[TrialProtocolDeviationResponse], tags=["Protocol Deviations"])
async def list_protocol_deviations(
    trial_subject_id: Optional[UUID] = Query(None),
    severity: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List protocol deviations with filters"""
    query = db.query(TrialProtocolDeviation)
    if trial_subject_id:
        query = query.filter(TrialProtocolDeviation.trial_subject_id == trial_subject_id)
    if severity:
        query = query.filter(TrialProtocolDeviation.severity == severity)
    return query.order_by(TrialProtocolDeviation.detected_at.desc()).all()

@app.get("/health", tags=["System"])
async def health_check():
    return {"service": "trial-management-service", "status": "healthy", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8027)
