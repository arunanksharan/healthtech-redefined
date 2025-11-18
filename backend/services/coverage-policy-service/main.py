"""
Coverage Policy Service - Port 8059
Manages patient-level insurance coverage and benefit limits
Maps to FHIR Coverage
"""
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from shared.database.models import Coverage, CoverageBenefitLimit, Patient, PayerPlan
from shared.events.types import EventType
from shared.events.publisher import publish_event
from schemas import (
    CoverageCreate, CoverageUpdate, CoverageResponse, CoverageBenefitLimitResponse
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Coverage Policy Service", version="0.1.0")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Coverage Endpoints
@app.post("/api/v1/coverages", response_model=CoverageResponse, status_code=201, tags=["Coverage"])
async def create_coverage(
    coverage_data: CoverageCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Capture insurance coverage at registration/admission"""
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == coverage_data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Verify payer plan exists
    payer_plan = db.query(PayerPlan).filter(PayerPlan.id == coverage_data.payer_plan_id).first()
    if not payer_plan:
        raise HTTPException(status_code=404, detail="Payer plan not found")

    # If this is primary coverage, mark other coverages as non-primary
    if coverage_data.is_primary:
        db.query(Coverage).filter(
            Coverage.patient_id == coverage_data.patient_id,
            Coverage.is_primary == True
        ).update({"is_primary": False})

    coverage = Coverage(
        tenant_id=patient.tenant_id,
        patient_id=coverage_data.patient_id,
        payer_plan_id=coverage_data.payer_plan_id,
        policy_number=coverage_data.policy_number,
        insured_person_name=coverage_data.insured_person_name,
        relationship_to_insured=coverage_data.relationship_to_insured,
        sum_insured=coverage_data.sum_insured,
        remaining_eligible_amount=coverage_data.remaining_eligible_amount or coverage_data.sum_insured,
        valid_from=coverage_data.valid_from,
        valid_to=coverage_data.valid_to,
        network_contract_id=coverage_data.network_contract_id,
        is_primary=coverage_data.is_primary,
        verification_status='unverified',
        verification_details=coverage_data.verification_details
    )
    db.add(coverage)
    db.commit()
    db.refresh(coverage)

    await publish_event(EventType.COVERAGE_CREATED, {
        "coverage_id": str(coverage.id),
        "patient_id": str(coverage.patient_id),
        "payer_plan_id": str(coverage.payer_plan_id),
        "policy_number": coverage.policy_number
    })

    logger.info(f"Coverage created: {coverage.id} for patient {coverage.patient_id}")
    return coverage


@app.get("/api/v1/coverages", response_model=List[CoverageResponse], tags=["Coverage"])
async def list_coverages(
    patient_id: Optional[UUID] = Query(None),
    tenant_id: Optional[UUID] = Query(None),
    active_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """List coverages with filters"""
    query = db.query(Coverage)

    if patient_id:
        query = query.filter(Coverage.patient_id == patient_id)

    if tenant_id:
        query = query.filter(Coverage.tenant_id == tenant_id)

    if active_only:
        # Filter for coverages that are currently active (within valid dates)
        today = datetime.now().date()
        query = query.filter(
            Coverage.valid_from <= today,
            Coverage.valid_to >= today,
            Coverage.verification_status == 'verified'
        )

    return query.order_by(Coverage.is_primary.desc(), Coverage.created_at.desc()).all()


@app.get("/api/v1/coverages/{coverage_id}", response_model=CoverageResponse, tags=["Coverage"])
async def get_coverage(coverage_id: UUID, db: Session = Depends(get_db)):
    """Get coverage details"""
    coverage = db.query(Coverage).filter(Coverage.id == coverage_id).first()
    if not coverage:
        raise HTTPException(status_code=404, detail="Coverage not found")
    return coverage


@app.patch("/api/v1/coverages/{coverage_id}", response_model=CoverageResponse, tags=["Coverage"])
async def update_coverage(
    coverage_id: UUID,
    update_data: CoverageUpdate,
    db: Session = Depends(get_db)
):
    """Update coverage verification status, network contract, etc."""
    coverage = db.query(Coverage).filter(Coverage.id == coverage_id).first()
    if not coverage:
        raise HTTPException(status_code=404, detail="Coverage not found")

    old_verification_status = coverage.verification_status

    if update_data.verification_status is not None:
        coverage.verification_status = update_data.verification_status
    if update_data.verification_details is not None:
        coverage.verification_details = update_data.verification_details
    if update_data.network_contract_id is not None:
        coverage.network_contract_id = update_data.network_contract_id
    if update_data.remaining_eligible_amount is not None:
        coverage.remaining_eligible_amount = update_data.remaining_eligible_amount
    if update_data.is_primary is not None:
        # If marking as primary, unmark others
        if update_data.is_primary:
            db.query(Coverage).filter(
                Coverage.patient_id == coverage.patient_id,
                Coverage.id != coverage_id,
                Coverage.is_primary == True
            ).update({"is_primary": False})
        coverage.is_primary = update_data.is_primary

    coverage.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(coverage)

    # Publish verification event
    if old_verification_status != coverage.verification_status and coverage.verification_status == 'verified':
        await publish_event(EventType.COVERAGE_VERIFIED, {
            "coverage_id": str(coverage.id),
            "patient_id": str(coverage.patient_id)
        })

    logger.info(f"Coverage updated: {coverage_id}")
    return coverage


@app.get("/api/v1/coverages/{coverage_id}/benefit-limits", response_model=List[CoverageBenefitLimitResponse], tags=["Benefit Limits"])
async def list_benefit_limits(coverage_id: UUID, db: Session = Depends(get_db)):
    """List benefit limits for a coverage"""
    # Verify coverage exists
    coverage = db.query(Coverage).filter(Coverage.id == coverage_id).first()
    if not coverage:
        raise HTTPException(status_code=404, detail="Coverage not found")

    return db.query(CoverageBenefitLimit).filter(
        CoverageBenefitLimit.coverage_id == coverage_id
    ).all()


@app.get("/health", tags=["System"])
async def health_check():
    return {"service": "coverage-policy-service", "status": "healthy", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8059)
