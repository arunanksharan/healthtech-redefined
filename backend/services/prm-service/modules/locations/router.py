"""
Locations Router
API endpoints for physical location management
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from loguru import logger

from shared.database.connection import get_db
from shared.database.models import Location

from .schemas import (
    LocationCreate,
    LocationUpdate,
    LocationResponse,
    LocationListResponse
)


router = APIRouter(prefix="/locations", tags=["Locations"])


@router.get("", response_model=LocationListResponse)
async def list_locations(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    organization_id: Optional[UUID] = Query(None, description="Filter by organization"),
    type: Optional[str] = Query(None, description="Filter by type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name"),
    db: Session = Depends(get_db)
):
    """
    List locations with pagination and filters

    Supports filtering by type (ward, room, bed, clinic, department).
    """
    query = db.query(Location)

    if tenant_id:
        query = query.filter(Location.tenant_id == tenant_id)

    if organization_id:
        query = query.filter(Location.organization_id == organization_id)

    if type:
        query = query.filter(Location.type.ilike(f"%{type}%"))

    if is_active is not None:
        query = query.filter(Location.is_active == is_active)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Location.name.ilike(search_term),
                Location.code.ilike(search_term),
                Location.building.ilike(search_term)
            )
        )

    total = query.count()
    offset = (page - 1) * page_size
    locations = query.order_by(Location.name).offset(offset).limit(page_size).all()

    return LocationListResponse(
        items=[LocationResponse.model_validate(loc) for loc in locations],
        total=total,
        page=page,
        page_size=page_size,
        has_next=offset + len(locations) < total,
        has_previous=page > 1
    )


@router.post("", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    loc_data: LocationCreate,
    db: Session = Depends(get_db)
):
    """Create a new location"""
    location = Location(
        id=uuid4(),
        tenant_id=loc_data.tenant_id,
        organization_id=loc_data.organization_id,
        parent_location_id=loc_data.parent_location_id,
        name=loc_data.name,
        type=loc_data.type,
        code=loc_data.code,
        building=loc_data.building,
        floor=loc_data.floor,
        room=loc_data.room,
        is_active=loc_data.is_active,
        operational_status=loc_data.operational_status,
        meta_data=loc_data.meta_data,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(location)
    db.commit()
    db.refresh(location)

    logger.info(f"Created location: {location.id} - {location.name}")
    return LocationResponse.model_validate(location)


@router.get("/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: UUID,
    db: Session = Depends(get_db)
):
    """Get location by ID"""
    location = db.query(Location).filter(Location.id == location_id).first()

    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")

    return LocationResponse.model_validate(location)


@router.put("/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: UUID,
    update_data: LocationUpdate,
    db: Session = Depends(get_db)
):
    """Update location details"""
    location = db.query(Location).filter(Location.id == location_id).first()

    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")

    update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in update_dict.items():
        if hasattr(location, field):
            setattr(location, field, value)

    location.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(location)

    logger.info(f"Updated location: {location_id}")
    return LocationResponse.model_validate(location)
