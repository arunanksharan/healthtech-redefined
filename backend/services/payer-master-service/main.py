"""
Payer Master Service - Port 8057
Manages payers (insurers, TPAs), plans, network relationships, and payer-specific rules
Maps to FHIR Organization (insurer) + InsurancePlan
"""
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import Session, sessionmaker

from shared.database.models import (
    Payer, PayerPlan, PayerNetworkContract, PayerRule, Tenant
)
from schemas import (
    PayerResponse, PayerPlanResponse, PayerNetworkContractResponse, PayerRuleResponse
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Payer Master Service", version="0.1.0")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Payer Endpoints
@app.get("/api/v1/payers", response_model=List[PayerResponse], tags=["Payers"])
async def list_payers(
    tenant_id: UUID = Query(...),
    search_text: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List payers with optional search and type filter"""
    query = db.query(Payer).filter(Payer.tenant_id == tenant_id)

    if type:
        query = query.filter(Payer.type == type)

    if search_text:
        query = query.filter(
            or_(
                Payer.name.ilike(f"%{search_text}%"),
                Payer.code.ilike(f"%{search_text}%")
            )
        )

    return query.order_by(Payer.name).all()


@app.get("/api/v1/payers/{payer_id}", response_model=PayerResponse, tags=["Payers"])
async def get_payer(payer_id: UUID, db: Session = Depends(get_db)):
    """Get payer details"""
    payer = db.query(Payer).filter(Payer.id == payer_id).first()
    if not payer:
        raise HTTPException(status_code=404, detail="Payer not found")
    return payer


@app.get("/api/v1/payers/{payer_id}/plans", response_model=List[PayerPlanResponse], tags=["Payer Plans"])
async def list_payer_plans(
    payer_id: UUID,
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List plans for a specific payer"""
    # Verify payer exists
    payer = db.query(Payer).filter(Payer.id == payer_id).first()
    if not payer:
        raise HTTPException(status_code=404, detail="Payer not found")

    query = db.query(PayerPlan).filter(PayerPlan.payer_id == payer_id)

    if is_active is not None:
        query = query.filter(PayerPlan.is_active == is_active)

    return query.order_by(PayerPlan.name).all()


@app.get("/api/v1/payers/plans/{plan_id}", response_model=PayerPlanResponse, tags=["Payer Plans"])
async def get_payer_plan(plan_id: UUID, db: Session = Depends(get_db)):
    """Get payer plan details"""
    plan = db.query(PayerPlan).filter(PayerPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Payer plan not found")
    return plan


@app.get("/api/v1/payers/plans/{plan_id}/network-contracts", response_model=List[PayerNetworkContractResponse], tags=["Network Contracts"])
async def list_network_contracts(
    plan_id: UUID,
    location_id: Optional[UUID] = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """List network contracts for a payer plan"""
    # Verify plan exists
    plan = db.query(PayerPlan).filter(PayerPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Payer plan not found")

    query = db.query(PayerNetworkContract).filter(
        PayerNetworkContract.payer_plan_id == plan_id
    )

    if location_id:
        query = query.filter(PayerNetworkContract.hospital_location_id == location_id)

    if active_only:
        # Filter for contracts that are currently active (within effective dates)
        today = datetime.now().date()
        query = query.filter(
            or_(
                PayerNetworkContract.effective_from == None,
                PayerNetworkContract.effective_from <= today
            ),
            or_(
                PayerNetworkContract.effective_to == None,
                PayerNetworkContract.effective_to >= today
            )
        )

    return query.all()


@app.get("/api/v1/payers/plans/{plan_id}/rules", response_model=List[PayerRuleResponse], tags=["Payer Rules"])
async def list_payer_rules(
    plan_id: UUID,
    rule_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List rules for a payer plan"""
    # Verify plan exists
    plan = db.query(PayerPlan).filter(PayerPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Payer plan not found")

    query = db.query(PayerRule).filter(
        PayerRule.payer_plan_id == plan_id,
        PayerRule.is_active == True
    )

    if rule_type:
        query = query.filter(PayerRule.rule_type == rule_type)

    return query.all()


@app.get("/health", tags=["System"])
async def health_check():
    return {"service": "payer-master-service", "status": "healthy", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8057)
