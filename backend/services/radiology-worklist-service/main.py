"""
Radiology Worklist Service - Port 8033
Manages radiology worklist generation, assignment, and workload balancing
"""
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import Session, sessionmaker

from shared.database.models import (
    RadiologyReadingProfile, RadiologyWorklistItem,
    ImagingStudy, Patient, Practitioner, Tenant
)
from shared.events.types import EventType
from shared.events.publisher import publish_event
from schemas import (
    RadiologyReadingProfileCreate, RadiologyReadingProfileUpdate, RadiologyReadingProfileResponse,
    RadiologyWorklistItemCreate, RadiologyWorklistItemUpdate, RadiologyWorklistItemResponse
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Radiology Worklist Service", version="0.1.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Radiology Reading Profile Endpoints
@app.post("/api/v1/radiology/reading-profiles", response_model=RadiologyReadingProfileResponse, status_code=201, tags=["Reading Profiles"])
async def create_reading_profile(
    profile_data: RadiologyReadingProfileCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create radiologist reading profile with capabilities and preferences"""
    # Verify practitioner exists
    practitioner = db.query(Practitioner).filter(Practitioner.id == profile_data.practitioner_id).first()
    if not practitioner:
        raise HTTPException(status_code=404, detail="Practitioner not found")

    # Check for existing profile
    existing = db.query(RadiologyReadingProfile).filter(and_(
        RadiologyReadingProfile.tenant_id == profile_data.tenant_id,
        RadiologyReadingProfile.practitioner_id == profile_data.practitioner_id
    )).first()
    if existing:
        raise HTTPException(status_code=400, detail="Reading profile already exists for this practitioner")

    profile = RadiologyReadingProfile(
        tenant_id=profile_data.tenant_id,
        practitioner_id=profile_data.practitioner_id,
        allowed_modalities=profile_data.allowed_modalities,
        allowed_body_parts=profile_data.allowed_body_parts,
        max_concurrent_cases=profile_data.max_concurrent_cases,
        reading_locations=profile_data.reading_locations
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    logger.info(f"Reading profile created for practitioner: {practitioner.id}")
    return profile

@app.get("/api/v1/radiology/reading-profiles", response_model=List[RadiologyReadingProfileResponse], tags=["Reading Profiles"])
async def list_reading_profiles(
    tenant_id: Optional[UUID] = Query(None),
    practitioner_id: Optional[UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List radiologist reading profiles"""
    query = db.query(RadiologyReadingProfile)
    if tenant_id:
        query = query.filter(RadiologyReadingProfile.tenant_id == tenant_id)
    if practitioner_id:
        query = query.filter(RadiologyReadingProfile.practitioner_id == practitioner_id)
    if is_active is not None:
        query = query.filter(RadiologyReadingProfile.is_active == is_active)
    return query.all()

@app.put("/api/v1/radiology/reading-profiles/{profile_id}", response_model=RadiologyReadingProfileResponse, tags=["Reading Profiles"])
async def update_reading_profile(
    profile_id: UUID,
    profile_data: RadiologyReadingProfileUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Update radiologist reading profile"""
    profile = db.query(RadiologyReadingProfile).filter(RadiologyReadingProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Reading profile not found")

    update_data = profile_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)

    logger.info(f"Reading profile updated: {profile_id}")
    return profile

# Radiology Worklist Item Endpoints
@app.post("/api/v1/radiology/worklist/items", response_model=RadiologyWorklistItemResponse, status_code=201, tags=["Worklist"])
async def create_worklist_item(
    item_data: RadiologyWorklistItemCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create worklist item (typically auto-created when imaging study is available)"""
    # Verify imaging study exists
    study = db.query(ImagingStudy).filter(ImagingStudy.id == item_data.imaging_study_id).first()
    if not study:
        raise HTTPException(status_code=404, detail="Imaging study not found")

    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == item_data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Check for duplicate
    existing = db.query(RadiologyWorklistItem).filter(
        RadiologyWorklistItem.imaging_study_id == item_data.imaging_study_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Worklist item already exists for this study")

    worklist_item = RadiologyWorklistItem(
        tenant_id=patient.tenant_id,
        imaging_study_id=item_data.imaging_study_id,
        imaging_order_id=item_data.imaging_order_id,
        patient_id=item_data.patient_id,
        modality_code=item_data.modality_code,
        body_part=item_data.body_part,
        priority=item_data.priority,
        status='pending'
    )
    db.add(worklist_item)
    db.commit()
    db.refresh(worklist_item)

    await publish_event(EventType.RADIOLOGY_WORKLIST_ITEM_CREATED, {
        "worklist_item_id": str(worklist_item.id),
        "imaging_study_id": str(worklist_item.imaging_study_id),
        "patient_id": str(worklist_item.patient_id),
        "modality_code": worklist_item.modality_code,
        "priority": worklist_item.priority
    })

    logger.info(f"Worklist item created: {worklist_item.id}")
    return worklist_item

@app.get("/api/v1/radiology/worklist/items", response_model=List[RadiologyWorklistItemResponse], tags=["Worklist"])
async def list_worklist_items(
    modality: Optional[str] = Query(None),
    body_part: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assigned_to_me: Optional[bool] = Query(None),
    current_radiologist_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db)
):
    """List radiology worklist items with filters"""
    query = db.query(RadiologyWorklistItem)

    if modality:
        query = query.filter(RadiologyWorklistItem.modality_code == modality)
    if body_part:
        query = query.filter(RadiologyWorklistItem.body_part == body_part)
    if status:
        query = query.filter(RadiologyWorklistItem.status == status)
    if priority:
        query = query.filter(RadiologyWorklistItem.priority == priority)
    if assigned_to_me and current_radiologist_id:
        query = query.filter(RadiologyWorklistItem.assigned_radiologist_id == current_radiologist_id)

    return query.order_by(RadiologyWorklistItem.priority, RadiologyWorklistItem.created_at).all()

@app.post("/api/v1/radiology/worklist/items/{item_id}/claim", response_model=RadiologyWorklistItemResponse, tags=["Worklist"])
async def claim_worklist_item(
    item_id: UUID,
    current_user_id: UUID,
    db: Session = Depends(get_db)
):
    """Claim a worklist item for reading"""
    item = db.query(RadiologyWorklistItem).filter(RadiologyWorklistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Worklist item not found")

    if item.status != 'pending':
        raise HTTPException(status_code=400, detail="Item is not available for claiming")

    # Check radiologist's reading profile
    profile = db.query(RadiologyReadingProfile).filter(
        RadiologyReadingProfile.practitioner_id == current_user_id
    ).first()

    if profile:
        # Check concurrent cases limit
        current_cases = db.query(RadiologyWorklistItem).filter(and_(
            RadiologyWorklistItem.assigned_radiologist_id == current_user_id,
            RadiologyWorklistItem.status.in_(['claimed', 'in_progress'])
        )).count()

        if current_cases >= profile.max_concurrent_cases:
            raise HTTPException(status_code=400, detail="Maximum concurrent cases limit reached")

    item.assigned_radiologist_id = current_user_id
    item.status = 'claimed'
    item.claimed_at = datetime.utcnow()
    item.last_activity_at = datetime.utcnow()
    db.commit()
    db.refresh(item)

    await publish_event(EventType.RADIOLOGY_WORKLIST_ITEM_CLAIMED, {
        "worklist_item_id": str(item.id),
        "radiologist_id": str(current_user_id),
        "imaging_study_id": str(item.imaging_study_id)
    })

    logger.info(f"Worklist item claimed: {item_id} by {current_user_id}")
    return item

@app.post("/api/v1/radiology/worklist/items/{item_id}/release", response_model=RadiologyWorklistItemResponse, tags=["Worklist"])
async def release_worklist_item(
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Release a claimed worklist item back to the pool"""
    item = db.query(RadiologyWorklistItem).filter(RadiologyWorklistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Worklist item not found")

    if item.status not in ['claimed', 'in_progress']:
        raise HTTPException(status_code=400, detail="Item cannot be released")

    item.assigned_radiologist_id = None
    item.status = 'pending'
    item.last_activity_at = datetime.utcnow()
    db.commit()
    db.refresh(item)

    logger.info(f"Worklist item released: {item_id}")
    return item

@app.patch("/api/v1/radiology/worklist/items/{item_id}", response_model=RadiologyWorklistItemResponse, tags=["Worklist"])
async def update_worklist_item(
    item_id: UUID,
    item_data: RadiologyWorklistItemUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Update worklist item (status, AI triage data, etc.)"""
    item = db.query(RadiologyWorklistItem).filter(RadiologyWorklistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Worklist item not found")

    update_data = item_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    item.last_activity_at = datetime.utcnow()
    item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(item)

    logger.info(f"Worklist item updated: {item_id}")
    return item

@app.get("/health", tags=["System"])
async def health_check():
    return {"service": "radiology-worklist-service", "status": "healthy", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8033)
