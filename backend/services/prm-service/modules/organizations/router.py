"""
Organizations Router
API endpoints for healthcare organization management
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from loguru import logger

from shared.database.connection import get_db
from shared.database.models import Organization

from .schemas import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationListResponse
)


router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get("", response_model=OrganizationListResponse)
async def list_organizations(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    type: Optional[str] = Query(None, description="Filter by type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name"),
    db: Session = Depends(get_db)
):
    """
    List organizations with pagination and filters

    Supports filtering by type (hospital, clinic, lab, etc.) and search.
    """
    query = db.query(Organization)

    if tenant_id:
        query = query.filter(Organization.tenant_id == tenant_id)

    if type:
        query = query.filter(Organization.type.ilike(f"%{type}%"))

    if is_active is not None:
        query = query.filter(Organization.is_active == is_active)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Organization.name.ilike(search_term),
                Organization.city.ilike(search_term)
            )
        )

    total = query.count()
    offset = (page - 1) * page_size
    organizations = query.order_by(Organization.name).offset(offset).limit(page_size).all()

    return OrganizationListResponse(
        items=[OrganizationResponse.model_validate(o) for o in organizations],
        total=total,
        page=page,
        page_size=page_size,
        has_next=offset + len(organizations) < total,
        has_previous=page > 1
    )


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrganizationCreate,
    db: Session = Depends(get_db)
):
    """Create a new organization"""
    organization = Organization(
        id=uuid4(),
        tenant_id=org_data.tenant_id,
        name=org_data.name,
        type=org_data.type,
        phone=org_data.phone,
        email=org_data.email,
        website=org_data.website,
        address_line1=org_data.address_line1,
        address_line2=org_data.address_line2,
        city=org_data.city,
        state=org_data.state,
        postal_code=org_data.postal_code,
        country=org_data.country,
        is_active=org_data.is_active,
        meta_data=org_data.meta_data,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(organization)
    db.commit()
    db.refresh(organization)

    logger.info(f"Created organization: {organization.id} - {organization.name}")
    return OrganizationResponse.model_validate(organization)


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: UUID,
    db: Session = Depends(get_db)
):
    """Get organization by ID"""
    organization = db.query(Organization).filter(Organization.id == organization_id).first()

    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    return OrganizationResponse.model_validate(organization)


@router.put("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: UUID,
    update_data: OrganizationUpdate,
    db: Session = Depends(get_db)
):
    """Update organization details"""
    organization = db.query(Organization).filter(Organization.id == organization_id).first()

    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in update_dict.items():
        if hasattr(organization, field):
            setattr(organization, field, value)

    organization.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(organization)

    logger.info(f"Updated organization: {organization_id}")
    return OrganizationResponse.model_validate(organization)


@router.delete("/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    organization_id: UUID,
    archive: bool = Query(True, description="Archive instead of delete"),
    db: Session = Depends(get_db)
):
    """
    Delete or archive an organization

    By default, archives (sets is_active=False) instead of hard delete.
    """
    organization = db.query(Organization).filter(Organization.id == organization_id).first()

    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    if archive:
        organization.is_active = False
        organization.updated_at = datetime.utcnow()
        db.commit()
        logger.info(f"Archived organization: {organization_id}")
    else:
        db.delete(organization)
        db.commit()
        logger.info(f"Deleted organization: {organization_id}")

    return None
