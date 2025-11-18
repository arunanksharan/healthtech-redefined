"""
Medication Reconciliation Service - Port 8047
Home medication list reconciliation at admission, transfer, and discharge
"""
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from shared.database.models import (
    MedicationHistorySource, MedicationReconciliationSession,
    MedicationReconciliationLine, MedicationProduct, MedicationMolecule,
    MedicationOrder, Patient, Encounter, Tenant
)
from shared.events.types import EventType
from shared.events.publisher import publish_event
from schemas import (
    MedicationHistorySourceCreate, MedicationHistorySourceResponse,
    MedicationReconciliationSessionCreate, MedicationReconciliationSessionUpdate,
    MedicationReconciliationSessionResponse,
    MedicationReconciliationLineCreate, MedicationReconciliationLineUpdate,
    MedicationReconciliationLineResponse
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Medication Reconciliation Service", version="0.1.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Medication History Source Endpoints
@app.post("/api/v1/medication-reconciliation/history-sources", response_model=MedicationHistorySourceResponse, status_code=201, tags=["History Sources"])
async def create_history_source(
    source_data: MedicationHistorySourceCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Record a medication history source
    (patient interview, external records, pharmacy records, etc.)
    """
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == source_data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    history_source = MedicationHistorySource(
        tenant_id=patient.tenant_id,
        patient_id=source_data.patient_id,
        source_type=source_data.source_type,
        description=source_data.description,
        recorded_by_user_id=current_user_id,
        recorded_at=datetime.utcnow(),
        raw_data=source_data.raw_data
    )
    db.add(history_source)
    db.commit()
    db.refresh(history_source)

    logger.info(f"Medication history source created for patient: {source_data.patient_id}")
    return history_source

@app.get("/api/v1/medication-reconciliation/history-sources", response_model=List[MedicationHistorySourceResponse], tags=["History Sources"])
async def list_history_sources(
    patient_id: UUID = Query(...),
    source_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List medication history sources for a patient"""
    query = db.query(MedicationHistorySource).filter(
        MedicationHistorySource.patient_id == patient_id
    )

    if source_type:
        query = query.filter(MedicationHistorySource.source_type == source_type)

    return query.order_by(MedicationHistorySource.recorded_at.desc()).all()

# Medication Reconciliation Session Endpoints
@app.post("/api/v1/medication-reconciliation/sessions", response_model=MedicationReconciliationSessionResponse, status_code=201, tags=["Reconciliation Sessions"])
async def create_reconciliation_session(
    session_data: MedicationReconciliationSessionCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Start a medication reconciliation session
    (admission, transfer, or discharge)
    """
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == session_data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Verify encounter if provided
    if session_data.encounter_id:
        encounter = db.query(Encounter).filter(Encounter.id == session_data.encounter_id).first()
        if not encounter:
            raise HTTPException(status_code=404, detail="Encounter not found")

    reconciliation_session = MedicationReconciliationSession(
        tenant_id=patient.tenant_id,
        patient_id=session_data.patient_id,
        encounter_id=session_data.encounter_id,
        reconciliation_type=session_data.reconciliation_type,
        status='in_progress',
        performed_by_user_id=current_user_id,
        comments=session_data.comments
    )
    db.add(reconciliation_session)
    db.commit()
    db.refresh(reconciliation_session)

    await publish_event(EventType.MEDICATION_RECONCILIATION_STARTED, {
        "session_id": str(reconciliation_session.id),
        "patient_id": str(reconciliation_session.patient_id),
        "reconciliation_type": reconciliation_session.reconciliation_type,
        "performed_by": str(current_user_id) if current_user_id else None
    })

    logger.info(f"Medication reconciliation session started: {reconciliation_session.id} - {session_data.reconciliation_type}")
    return reconciliation_session

@app.get("/api/v1/medication-reconciliation/sessions", response_model=List[MedicationReconciliationSessionResponse], tags=["Reconciliation Sessions"])
async def list_reconciliation_sessions(
    patient_id: Optional[UUID] = Query(None),
    encounter_id: Optional[UUID] = Query(None),
    reconciliation_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List medication reconciliation sessions with filters"""
    query = db.query(MedicationReconciliationSession)

    if patient_id:
        query = query.filter(MedicationReconciliationSession.patient_id == patient_id)
    if encounter_id:
        query = query.filter(MedicationReconciliationSession.encounter_id == encounter_id)
    if reconciliation_type:
        query = query.filter(MedicationReconciliationSession.reconciliation_type == reconciliation_type)
    if status:
        query = query.filter(MedicationReconciliationSession.status == status)

    return query.order_by(MedicationReconciliationSession.created_at.desc()).all()

@app.get("/api/v1/medication-reconciliation/sessions/{session_id}", response_model=MedicationReconciliationSessionResponse, tags=["Reconciliation Sessions"])
async def get_reconciliation_session(session_id: UUID, db: Session = Depends(get_db)):
    """Get reconciliation session details"""
    session = db.query(MedicationReconciliationSession).filter(
        MedicationReconciliationSession.id == session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Reconciliation session not found")
    return session

@app.patch("/api/v1/medication-reconciliation/sessions/{session_id}", response_model=MedicationReconciliationSessionResponse, tags=["Reconciliation Sessions"])
async def update_reconciliation_session(
    session_id: UUID,
    update_data: MedicationReconciliationSessionUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Update reconciliation session (typically to mark as completed)
    """
    session = db.query(MedicationReconciliationSession).filter(
        MedicationReconciliationSession.id == session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Reconciliation session not found")

    old_status = session.status

    if update_data.status is not None:
        session.status = update_data.status
        if update_data.status == 'completed' and not session.performed_at:
            session.performed_at = datetime.utcnow()
    if update_data.comments is not None:
        session.comments = update_data.comments

    session.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(session)

    # Publish event if completed
    if old_status != 'completed' and session.status == 'completed':
        await publish_event(EventType.MEDICATION_RECONCILIATION_COMPLETED, {
            "session_id": str(session.id),
            "patient_id": str(session.patient_id),
            "reconciliation_type": session.reconciliation_type
        })

    logger.info(f"Medication reconciliation session updated: {session_id} - status: {session.status}")
    return session

# Medication Reconciliation Line Endpoints
@app.post("/api/v1/medication-reconciliation/sessions/{session_id}/lines", response_model=MedicationReconciliationLineResponse, status_code=201, tags=["Reconciliation Lines"])
async def create_reconciliation_line(
    session_id: UUID,
    line_data: MedicationReconciliationLineCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Add a reconciliation line (medication decision)
    """
    # Verify session exists
    session = db.query(MedicationReconciliationSession).filter(
        MedicationReconciliationSession.id == session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Reconciliation session not found")

    # Override session_id from URL
    line_data.reconciliation_session_id = session_id

    # Verify medication product if provided
    if line_data.medication_product_id:
        product = db.query(MedicationProduct).filter(
            MedicationProduct.id == line_data.medication_product_id
        ).first()
        if not product:
            raise HTTPException(status_code=404, detail="Medication product not found")

    # Verify molecule if provided
    if line_data.molecule_id:
        molecule = db.query(MedicationMolecule).filter(
            MedicationMolecule.id == line_data.molecule_id
        ).first()
        if not molecule:
            raise HTTPException(status_code=404, detail="Molecule not found")

    # Verify linked order if provided
    if line_data.linked_medication_order_id:
        order = db.query(MedicationOrder).filter(
            MedicationOrder.id == line_data.linked_medication_order_id
        ).first()
        if not order:
            raise HTTPException(status_code=404, detail="Linked medication order not found")

    reconciliation_line = MedicationReconciliationLine(
        reconciliation_session_id=line_data.reconciliation_session_id,
        source_medication_statement_id=line_data.source_medication_statement_id,
        medication_product_id=line_data.medication_product_id,
        molecule_id=line_data.molecule_id,
        home_regimen=line_data.home_regimen,
        decision=line_data.decision,
        decision_reason=line_data.decision_reason,
        linked_medication_order_id=line_data.linked_medication_order_id,
        comments=line_data.comments
    )
    db.add(reconciliation_line)
    db.commit()
    db.refresh(reconciliation_line)

    logger.info(f"Reconciliation line added to session {session_id}: decision={line_data.decision}")
    return reconciliation_line

@app.get("/api/v1/medication-reconciliation/sessions/{session_id}/lines", response_model=List[MedicationReconciliationLineResponse], tags=["Reconciliation Lines"])
async def list_reconciliation_lines(
    session_id: UUID,
    db: Session = Depends(get_db)
):
    """List all reconciliation lines for a session"""
    return db.query(MedicationReconciliationLine).filter(
        MedicationReconciliationLine.reconciliation_session_id == session_id
    ).order_by(MedicationReconciliationLine.created_at).all()

@app.patch("/api/v1/medication-reconciliation/lines/{line_id}", response_model=MedicationReconciliationLineResponse, tags=["Reconciliation Lines"])
async def update_reconciliation_line(
    line_id: UUID,
    update_data: MedicationReconciliationLineUpdate,
    db: Session = Depends(get_db)
):
    """Update a reconciliation line"""
    line = db.query(MedicationReconciliationLine).filter(
        MedicationReconciliationLine.id == line_id
    ).first()
    if not line:
        raise HTTPException(status_code=404, detail="Reconciliation line not found")

    if update_data.decision is not None:
        line.decision = update_data.decision
    if update_data.decision_reason is not None:
        line.decision_reason = update_data.decision_reason
    if update_data.linked_medication_order_id is not None:
        line.linked_medication_order_id = update_data.linked_medication_order_id
    if update_data.comments is not None:
        line.comments = update_data.comments

    line.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(line)

    logger.info(f"Reconciliation line updated: {line_id}")
    return line

@app.get("/health", tags=["System"])
async def health_check():
    return {"service": "medication-reconciliation-service", "status": "healthy", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8047)
