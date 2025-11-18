"""
Consent Service - Privacy and Consent Management
Manages patient consents for data access and sharing
"""
import os
import sys
from datetime import datetime
from typing import List, Optional
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from loguru import logger

from shared.database.connection import get_db, engine
from shared.database.models import Base, Consent
from shared.events.publisher import publish_event
from shared.events.types import EventType

from .schemas import (
    ConsentCreate,
    ConsentUpdate,
    ConsentResponse,
    ConsentListResponse,
    ConsentRevoke,
    AccessCheckRequest,
    AccessCheckResponse,
    ConsentAuditResponse
)

# Initialize FastAPI app
app = FastAPI(
    title="Consent Service",
    description="Privacy and consent management for patient data access",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Health Check ====================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "consent-service",
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== Consent Management ====================

@app.post(
    "/api/v1/consents",
    response_model=ConsentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Consents"]
)
async def create_consent(
    consent_data: ConsentCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new consent record

    Patient grants permission for specific grantee to access their data.
    """
    try:
        # Determine initial status based on dates
        now = datetime.utcnow()
        if consent_data.start_date > now:
            consent_status = "pending"
        elif consent_data.end_date and consent_data.end_date < now:
            consent_status = "expired"
        else:
            consent_status = "active"

        # Create consent
        consent = Consent(
            tenant_id=consent_data.tenant_id,
            patient_id=consent_data.patient_id,
            grantee_id=consent_data.grantee_id,
            grantee_type=consent_data.grantee_type,
            purpose=consent_data.purpose,
            scope=consent_data.scope,
            resource_types=consent_data.resource_types,
            status=consent_status,
            start_date=consent_data.start_date,
            end_date=consent_data.end_date,
            privacy_level=consent_data.privacy_level,
            notes=consent_data.notes
        )

        db.add(consent)
        db.commit()
        db.refresh(consent)

        logger.info(
            f"Created consent {consent.id} for patient {consent_data.patient_id} "
            f"to grantee {consent_data.grantee_id}"
        )

        # Publish event
        await publish_event(
            event_type=EventType.CONSENT_CREATED,
            tenant_id=str(consent_data.tenant_id),
            payload={
                "consent_id": str(consent.id),
                "patient_id": str(consent_data.patient_id),
                "grantee_id": str(consent_data.grantee_id),
                "purpose": consent_data.purpose,
                "status": consent_status
            },
            source_service="consent-service"
        )

        return consent

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating consent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create consent: {str(e)}"
        )


@app.get(
    "/api/v1/consents/{consent_id}",
    response_model=ConsentResponse,
    tags=["Consents"]
)
async def get_consent(
    consent_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a consent record by ID"""
    try:
        consent = db.query(Consent).filter(
            Consent.id == consent_id
        ).first()

        if not consent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Consent not found: {consent_id}"
            )

        # Update status if expired
        _update_consent_status(consent, db)

        return consent

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving consent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve consent: {str(e)}"
        )


@app.get(
    "/api/v1/consents",
    response_model=ConsentListResponse,
    tags=["Consents"]
)
async def list_consents(
    patient_id: Optional[UUID] = Query(None, description="Filter by patient"),
    grantee_id: Optional[UUID] = Query(None, description="Filter by grantee"),
    purpose: Optional[str] = Query(None, description="Filter by purpose"),
    status: Optional[str] = Query(None, description="Filter by status"),
    include_revoked: bool = Query(False, description="Include revoked consents"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List consents with filters

    Supports filtering by patient, grantee, purpose, and status.
    """
    try:
        # Build query
        query = db.query(Consent)

        if patient_id:
            query = query.filter(Consent.patient_id == patient_id)

        if grantee_id:
            query = query.filter(Consent.grantee_id == grantee_id)

        if purpose:
            query = query.filter(Consent.purpose == purpose.lower())

        if status:
            query = query.filter(Consent.status == status.lower())

        if not include_revoked:
            query = query.filter(Consent.is_revoked == False)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        consents = query.order_by(
            Consent.created_at.desc()
        ).offset(offset).limit(page_size).all()

        # Update status for all consents
        for consent in consents:
            _update_consent_status(consent, db, commit=False)
        db.commit()

        # Calculate pagination metadata
        has_next = (offset + page_size) < total
        has_previous = page > 1

        return ConsentListResponse(
            total=total,
            consents=consents,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous
        )

    except Exception as e:
        logger.error(f"Error listing consents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list consents: {str(e)}"
        )


@app.patch(
    "/api/v1/consents/{consent_id}",
    response_model=ConsentResponse,
    tags=["Consents"]
)
async def update_consent(
    consent_id: UUID,
    consent_update: ConsentUpdate,
    db: Session = Depends(get_db)
):
    """Update a consent record"""
    try:
        consent = db.query(Consent).filter(
            Consent.id == consent_id,
            Consent.is_revoked == False
        ).first()

        if not consent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Active consent not found: {consent_id}"
            )

        # Update fields
        if consent_update.end_date is not None:
            consent.end_date = consent_update.end_date

        if consent_update.notes is not None:
            consent.notes = consent_update.notes

        if consent_update.privacy_level is not None:
            consent.privacy_level = consent_update.privacy_level

        consent.updated_at = datetime.utcnow()

        # Update status
        _update_consent_status(consent, db)

        db.commit()
        db.refresh(consent)

        logger.info(f"Updated consent {consent_id}")

        # Publish event
        await publish_event(
            event_type=EventType.CONSENT_UPDATED,
            tenant_id=str(consent.tenant_id),
            payload={
                "consent_id": str(consent.id),
                "patient_id": str(consent.patient_id),
                "status": consent.status
            },
            source_service="consent-service"
        )

        return consent

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating consent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update consent: {str(e)}"
        )


@app.post(
    "/api/v1/consents/{consent_id}/revoke",
    response_model=ConsentResponse,
    tags=["Consents"]
)
async def revoke_consent(
    consent_id: UUID,
    revoke_data: ConsentRevoke,
    db: Session = Depends(get_db)
):
    """
    Revoke a consent

    Patient can revoke consent at any time.
    """
    try:
        consent = db.query(Consent).filter(
            Consent.id == consent_id,
            Consent.is_revoked == False
        ).first()

        if not consent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Active consent not found: {consent_id}"
            )

        # Revoke consent
        consent.is_revoked = True
        consent.revoked_at = datetime.utcnow()
        consent.revoked_reason = revoke_data.reason
        consent.status = "revoked"
        consent.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(consent)

        logger.warning(
            f"Consent {consent_id} revoked. Reason: {revoke_data.reason}"
        )

        # Publish event
        await publish_event(
            event_type=EventType.CONSENT_WITHDRAWN,
            tenant_id=str(consent.tenant_id),
            payload={
                "consent_id": str(consent.id),
                "patient_id": str(consent.patient_id),
                "grantee_id": str(consent.grantee_id),
                "reason": revoke_data.reason
            },
            source_service="consent-service"
        )

        return consent

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error revoking consent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke consent: {str(e)}"
        )


# ==================== Access Control ====================

@app.post(
    "/api/v1/consents/check-access",
    response_model=AccessCheckResponse,
    tags=["Access Control"]
)
async def check_access(
    access_request: AccessCheckRequest,
    db: Session = Depends(get_db)
):
    """
    Check if access is permitted based on consents

    Validates whether a grantee can access patient data for a specific purpose.
    """
    try:
        now = datetime.utcnow()

        # Find applicable consents
        query = db.query(Consent).filter(
            Consent.patient_id == access_request.patient_id,
            Consent.grantee_id == access_request.grantee_id,
            Consent.purpose == access_request.purpose.lower(),
            Consent.is_revoked == False,
            Consent.start_date <= now
        )

        # Filter by end_date (None means no expiration)
        query = query.filter(
            or_(
                Consent.end_date.is_(None),
                Consent.end_date >= now
            )
        )

        # Filter by resource type if specified
        if access_request.resource_type:
            query = query.filter(
                or_(
                    Consent.scope == "full_record",
                    Consent.resource_types.contains([access_request.resource_type])
                )
            )

        consents = query.all()

        if not consents:
            return AccessCheckResponse(
                permitted=False,
                reason="No active consent found for this access request",
                applicable_consents=[],
                privacy_level=None
            )

        # Access is permitted
        consent_ids = [consent.id for consent in consents]

        # Get highest privacy level
        privacy_levels = ["normal", "sensitive", "highly_sensitive"]
        max_privacy_level = max(
            (consent.privacy_level for consent in consents),
            key=lambda x: privacy_levels.index(x)
        )

        return AccessCheckResponse(
            permitted=True,
            reason="Active consent exists",
            applicable_consents=consent_ids,
            privacy_level=max_privacy_level
        )

    except Exception as e:
        logger.error(f"Error checking access: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Access check failed: {str(e)}"
        )


@app.get(
    "/api/v1/consents/patient/{patient_id}/active",
    response_model=List[ConsentResponse],
    tags=["Access Control"]
)
async def get_active_consents(
    patient_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get all active consents for a patient

    Returns consents that are currently valid and not revoked.
    """
    try:
        now = datetime.utcnow()

        consents = db.query(Consent).filter(
            Consent.patient_id == patient_id,
            Consent.is_revoked == False,
            Consent.start_date <= now,
            or_(
                Consent.end_date.is_(None),
                Consent.end_date >= now
            )
        ).all()

        # Update status for all consents
        for consent in consents:
            _update_consent_status(consent, db, commit=False)
        db.commit()

        return consents

    except Exception as e:
        logger.error(f"Error fetching active consents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch active consents: {str(e)}"
        )


@app.get(
    "/api/v1/consents/expiring-soon",
    response_model=List[ConsentResponse],
    tags=["Monitoring"]
)
async def get_expiring_consents(
    days: int = Query(30, ge=1, le=365, description="Days until expiration"),
    db: Session = Depends(get_db)
):
    """
    Get consents expiring within specified days

    Useful for sending renewal reminders.
    """
    try:
        from datetime import timedelta

        now = datetime.utcnow()
        threshold = now + timedelta(days=days)

        consents = db.query(Consent).filter(
            Consent.is_revoked == False,
            Consent.status == "active",
            Consent.end_date.isnot(None),
            Consent.end_date <= threshold,
            Consent.end_date >= now
        ).order_by(Consent.end_date.asc()).all()

        return consents

    except Exception as e:
        logger.error(f"Error fetching expiring consents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch expiring consents: {str(e)}"
        )


# ==================== Helper Functions ====================

def _update_consent_status(
    consent: Consent,
    db: Session,
    commit: bool = True
) -> None:
    """
    Update consent status based on dates

    Args:
        consent: Consent object to update
        db: Database session
        commit: Whether to commit changes
    """
    if consent.is_revoked:
        consent.status = "revoked"
        return

    now = datetime.utcnow()

    if consent.start_date > now:
        consent.status = "pending"
    elif consent.end_date and consent.end_date < now:
        consent.status = "expired"
    else:
        consent.status = "active"

    if commit:
        db.commit()


# ==================== Startup ====================

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("Consent Service starting up...")

    # Create tables if they don't exist
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

    logger.info("Consent Service ready!")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003, reload=True)
