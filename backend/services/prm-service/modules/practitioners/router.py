"""
Practitioners Router
API endpoints for practitioner/provider management
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from loguru import logger

from shared.database.connection import get_db
from shared.database.models import Practitioner

from .schemas import (
    PractitionerCreate,
    PractitionerUpdate,
    PractitionerResponse,
    PractitionerSimpleResponse,
    PractitionerListResponse
)


router = APIRouter(prefix="/practitioners", tags=["Practitioners"])


@router.get("", response_model=PractitionerListResponse)
async def list_practitioners(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    speciality: Optional[str] = Query(None, description="Filter by speciality"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name"),
    db: Session = Depends(get_db)
):
    """
    List practitioners with pagination and filters

    Used for:
    - Populating practitioner dropdowns in appointment forms
    - Provider directory listings
    - Staff management views
    """
    from sqlalchemy import or_

    query = db.query(Practitioner)

    # Apply filters
    if tenant_id:
        query = query.filter(Practitioner.tenant_id == tenant_id)

    if speciality:
        query = query.filter(Practitioner.speciality.ilike(f"%{speciality}%"))

    if is_active is not None:
        query = query.filter(Practitioner.is_active == is_active)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Practitioner.first_name.ilike(search_term),
                Practitioner.last_name.ilike(search_term),
                Practitioner.speciality.ilike(search_term)
            )
        )

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    practitioners = query.order_by(
        Practitioner.last_name,
        Practitioner.first_name
    ).offset(offset).limit(page_size).all()

    # Build response items with computed name
    items = []
    for p in practitioners:
        resp = PractitionerResponse.model_validate(p)
        items.append(resp)

    return PractitionerListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=offset + len(practitioners) < total,
        has_previous=page > 1
    )


@router.get("/simple", response_model=List[PractitionerSimpleResponse])
async def list_practitioners_simple(
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    speciality: Optional[str] = Query(None, description="Filter by speciality"),
    active_only: bool = Query(True, description="Only active practitioners"),
    db: Session = Depends(get_db)
):
    """
    Get simplified practitioner list for dropdowns

    Returns minimal data optimized for select/dropdown components.
    Typically used in appointment creation forms.
    """
    query = db.query(Practitioner)

    if tenant_id:
        query = query.filter(Practitioner.tenant_id == tenant_id)

    if speciality:
        query = query.filter(Practitioner.speciality.ilike(f"%{speciality}%"))

    if active_only:
        query = query.filter(Practitioner.is_active == True)

    practitioners = query.order_by(
        Practitioner.last_name,
        Practitioner.first_name
    ).all()

    return [
        PractitionerSimpleResponse(
            id=p.id,
            name=f"{p.first_name} {p.last_name}".strip(),
            speciality=p.speciality,
            is_active=p.is_active
        )
        for p in practitioners
    ]


@router.get("/specialities", response_model=List[str])
async def list_specialities(
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    db: Session = Depends(get_db)
):
    """
    Get list of unique specialities

    Used for filtering dropdowns.
    """
    from sqlalchemy import distinct

    query = db.query(distinct(Practitioner.speciality)).filter(
        Practitioner.speciality.isnot(None),
        Practitioner.is_active == True
    )

    if tenant_id:
        query = query.filter(Practitioner.tenant_id == tenant_id)

    specialities = [row[0] for row in query.all() if row[0]]
    return sorted(specialities)


@router.get("/{practitioner_id}", response_model=PractitionerResponse)
async def get_practitioner(
    practitioner_id: UUID,
    db: Session = Depends(get_db)
):
    """Get practitioner by ID"""
    practitioner = db.query(Practitioner).filter(
        Practitioner.id == practitioner_id
    ).first()

    if not practitioner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Practitioner not found"
        )

    return PractitionerResponse.model_validate(practitioner)


# ==================== Create Practitioner ====================

@router.post("", response_model=PractitionerResponse, status_code=status.HTTP_201_CREATED)
async def create_practitioner(
    practitioner_data: PractitionerCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new practitioner

    Creates a healthcare provider record with credentials and contact info.
    """
    # Create new practitioner
    practitioner = Practitioner(
        id=uuid4(),
        tenant_id=practitioner_data.tenant_id,
        first_name=practitioner_data.first_name,
        last_name=practitioner_data.last_name,
        middle_name=practitioner_data.middle_name,
        gender=practitioner_data.gender,
        qualification=practitioner_data.qualification,
        speciality=practitioner_data.speciality,
        sub_speciality=practitioner_data.sub_speciality,
        license_number=practitioner_data.license_number,
        registration_number=practitioner_data.registration_number,
        phone_primary=practitioner_data.phone_primary,
        email_primary=practitioner_data.email_primary,
        is_active=practitioner_data.is_active,
        meta_data=practitioner_data.meta_data,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(practitioner)
    db.commit()
    db.refresh(practitioner)

    logger.info(f"Created practitioner: {practitioner.id} - {practitioner.first_name} {practitioner.last_name}")

    return PractitionerResponse.model_validate(practitioner)


# ==================== Update Practitioner ====================

@router.patch("/{practitioner_id}", response_model=PractitionerResponse)
async def update_practitioner(
    practitioner_id: UUID,
    update_data: PractitionerUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a practitioner

    Partial update - only provided fields will be modified.
    """
    practitioner = db.query(Practitioner).filter(
        Practitioner.id == practitioner_id
    ).first()

    if not practitioner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Practitioner not found"
        )

    # Update only provided fields
    update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)

    for field, value in update_dict.items():
        if hasattr(practitioner, field):
            setattr(practitioner, field, value)

    practitioner.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(practitioner)

    logger.info(f"Updated practitioner: {practitioner_id}")

    return PractitionerResponse.model_validate(practitioner)


# ==================== Delete Practitioner ====================

@router.delete("/{practitioner_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_practitioner(
    practitioner_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a practitioner

    Permanently removes a practitioner from the system.
    Consider setting is_active=false for soft delete instead.
    """
    practitioner = db.query(Practitioner).filter(
        Practitioner.id == practitioner_id
    ).first()

    if not practitioner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Practitioner not found"
        )

    db.delete(practitioner)
    db.commit()

    logger.info(f"Deleted practitioner: {practitioner_id}")

    return None
