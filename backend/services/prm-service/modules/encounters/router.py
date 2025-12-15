"""
Encounters Router
API endpoints for clinical encounter/visit management
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from loguru import logger

from shared.database.connection import get_db
from shared.database.models import Encounter

from .schemas import (
    EncounterCreate,
    EncounterUpdate,
    EncounterResponse,
    EncounterListResponse
)


router = APIRouter(prefix="/encounters", tags=["Encounters"])


@router.get("", response_model=EncounterListResponse)
async def list_encounters(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    patient_id: Optional[UUID] = Query(None, description="Filter by patient"),
    practitioner_id: Optional[UUID] = Query(None, description="Filter by practitioner"),
    status: Optional[str] = Query(None, description="Filter by status"),
    class_code: Optional[str] = Query(None, description="Filter by class (AMB, IMP, EMER)"),
    db: Session = Depends(get_db)
):
    """
    List encounters with pagination and filters

    Status: planned, in-progress, completed, cancelled
    Class: AMB (outpatient), IMP (inpatient), EMER (emergency)
    """
    query = db.query(Encounter)

    if tenant_id:
        query = query.filter(Encounter.tenant_id == tenant_id)

    if patient_id:
        query = query.filter(Encounter.patient_id == patient_id)

    if practitioner_id:
        query = query.filter(Encounter.practitioner_id == practitioner_id)

    if status:
        query = query.filter(Encounter.status == status)

    if class_code:
        query = query.filter(Encounter.class_code == class_code)

    total = query.count()
    offset = (page - 1) * page_size
    encounters = query.order_by(Encounter.started_at.desc()).offset(offset).limit(page_size).all()

    return EncounterListResponse(
        items=[EncounterResponse.model_validate(enc) for enc in encounters],
        total=total,
        page=page,
        page_size=page_size,
        has_next=offset + len(encounters) < total,
        has_previous=page > 1
    )


@router.post("", response_model=EncounterResponse, status_code=status.HTTP_201_CREATED)
async def create_encounter(
    enc_data: EncounterCreate,
    db: Session = Depends(get_db)
):
    """Record a new clinical encounter"""
    fhir_id = enc_data.encounter_fhir_id or f"enc-{uuid4()}"

    encounter = Encounter(
        id=uuid4(),
        tenant_id=enc_data.tenant_id,
        encounter_fhir_id=fhir_id,
        patient_id=enc_data.patient_id,
        practitioner_id=enc_data.practitioner_id,
        appointment_id=enc_data.appointment_id,
        status=enc_data.status,
        class_code=enc_data.class_code,
        started_at=enc_data.started_at or datetime.utcnow(),
        ended_at=enc_data.ended_at,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(encounter)
    db.commit()
    db.refresh(encounter)

    logger.info(f"Created encounter: {encounter.id}")
    return EncounterResponse.model_validate(encounter)


@router.get("/{encounter_id}", response_model=EncounterResponse)
async def get_encounter(
    encounter_id: UUID,
    db: Session = Depends(get_db)
):
    """Get encounter by ID"""
    encounter = db.query(Encounter).filter(Encounter.id == encounter_id).first()

    if not encounter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found")

    return EncounterResponse.model_validate(encounter)


@router.put("/{encounter_id}", response_model=EncounterResponse)
async def update_encounter(
    encounter_id: UUID,
    update_data: EncounterUpdate,
    db: Session = Depends(get_db)
):
    """Update encounter details"""
    encounter = db.query(Encounter).filter(Encounter.id == encounter_id).first()

    if not encounter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found")

    update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in update_dict.items():
        if hasattr(encounter, field):
            setattr(encounter, field, value)

    encounter.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(encounter)

    logger.info(f"Updated encounter: {encounter_id}")
    return EncounterResponse.model_validate(encounter)
