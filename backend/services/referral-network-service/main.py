"""
Referral Network Service
FastAPI service for multi-organization referral management
Port: 8021
"""
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID
import json

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import IntegrityError

from shared.database.models import (
    NetworkOrganization,
    Referral,
    ReferralDocument,
    Patient,
    User,
    Tenant
)
from shared.events.types import EventType
from shared.events.publisher import publish_event
from schemas import (
    NetworkOrganizationCreate,
    NetworkOrganizationUpdate,
    NetworkOrganizationResponse,
    NetworkOrganizationListResponse,
    ReferralCreate,
    ReferralUpdate,
    ReferralStatusUpdate,
    ReferralResponse,
    ReferralListResponse,
    ReferralDocumentCreate,
    ReferralDocumentResponse,
    ReferralDocumentListResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# FastAPI app
app = FastAPI(
    title="Referral Network Service",
    description="Multi-organization referral management with lifecycle tracking",
    version="0.1.0"
)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== Network Organization Endpoints ====================

@app.post(
    "/api/v1/referrals/network-organizations",
    response_model=NetworkOrganizationResponse,
    status_code=201,
    tags=["Network Organizations"]
)
async def create_network_organization(
    org_data: NetworkOrganizationCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None  # From auth middleware
):
    """
    Register a partner organization in the referral network.

    - **code**: Unique organization code
    - **org_type**: HOSPITAL, CLINIC, LAB, etc.
    - **is_internal**: True if this is our own organization
    - **interop_system_id**: Link to external system for data exchange
    """
    # Check if code already exists
    existing = db.query(NetworkOrganization).filter(
        NetworkOrganization.code == org_data.code
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Organization with code '{org_data.code}' already exists"
        )

    # Create network organization
    network_org = NetworkOrganization(
        code=org_data.code,
        name=org_data.name,
        org_type=org_data.org_type,
        address=org_data.address,
        contact=org_data.contact,
        interop_system_id=org_data.interop_system_id,
        capabilities=org_data.capabilities,
        is_internal=org_data.is_internal,
        is_active=org_data.is_active
    )

    db.add(network_org)

    try:
        db.commit()
        db.refresh(network_org)

        # Publish event
        await publish_event(
            EventType.NETWORK_ORG_REGISTERED,
            {
                "organization_id": str(network_org.id),
                "code": network_org.code,
                "org_type": network_org.org_type,
                "is_internal": network_org.is_internal
            }
        )

        logger.info(f"Network organization registered: {network_org.code}")
        return network_org

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")


@app.get(
    "/api/v1/referrals/network-organizations",
    response_model=NetworkOrganizationListResponse,
    tags=["Network Organizations"]
)
async def list_network_organizations(
    org_type: Optional[str] = Query(None, description="Filter by org type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_internal: Optional[bool] = Query(None, description="Filter internal/external"),
    search: Optional[str] = Query(None, description="Search by name or code"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List network organizations with optional filtering.

    Supports filtering by type, active status, and search.
    """
    query = db.query(NetworkOrganization)

    # Apply filters
    if org_type:
        query = query.filter(NetworkOrganization.org_type == org_type.upper())

    if is_active is not None:
        query = query.filter(NetworkOrganization.is_active == is_active)

    if is_internal is not None:
        query = query.filter(NetworkOrganization.is_internal == is_internal)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                NetworkOrganization.name.ilike(search_pattern),
                NetworkOrganization.code.ilike(search_pattern)
            )
        )

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    organizations = query.order_by(
        NetworkOrganization.name
    ).offset(offset).limit(page_size).all()

    return NetworkOrganizationListResponse(
        total=total,
        organizations=organizations,
        page=page,
        page_size=page_size,
        has_next=offset + page_size < total,
        has_previous=page > 1
    )


@app.get(
    "/api/v1/referrals/network-organizations/{org_id}",
    response_model=NetworkOrganizationResponse,
    tags=["Network Organizations"]
)
async def get_network_organization(
    org_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a network organization by ID."""
    org = db.query(NetworkOrganization).filter(NetworkOrganization.id == org_id).first()

    if not org:
        raise HTTPException(status_code=404, detail="Network organization not found")

    return org


@app.patch(
    "/api/v1/referrals/network-organizations/{org_id}",
    response_model=NetworkOrganizationResponse,
    tags=["Network Organizations"]
)
async def update_network_organization(
    org_id: UUID,
    update_data: NetworkOrganizationUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Update a network organization's details."""
    org = db.query(NetworkOrganization).filter(NetworkOrganization.id == org_id).first()

    if not org:
        raise HTTPException(status_code=404, detail="Network organization not found")

    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(org, field, value)

    org.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(org)

    logger.info(f"Network organization updated: {org.code}")
    return org


# ==================== Referral Endpoints ====================

@app.post(
    "/api/v1/referrals/referrals",
    response_model=ReferralResponse,
    status_code=201,
    tags=["Referrals"]
)
async def create_referral(
    referral_data: ReferralCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Create a new referral to a partner organization.

    - **referral_type**: OPD, IPD_TRANSFER, DIAGNOSTIC, HOMECARE
    - **priority**: routine, urgent, emergency
    - **status**: Initially set to 'draft'
    """
    # Validate patient exists
    patient = db.query(Patient).filter(Patient.id == referral_data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Validate organizations exist
    source_org = db.query(NetworkOrganization).filter(
        NetworkOrganization.id == referral_data.source_org_id
    ).first()

    target_org = db.query(NetworkOrganization).filter(
        NetworkOrganization.id == referral_data.target_org_id
    ).first()

    if not source_org or not target_org:
        raise HTTPException(status_code=404, detail="Source or target organization not found")

    if not target_org.is_active:
        raise HTTPException(status_code=400, detail="Target organization is not active")

    # Create referral
    referral = Referral(
        patient_id=referral_data.patient_id,
        source_org_id=referral_data.source_org_id,
        target_org_id=referral_data.target_org_id,
        referral_type=referral_data.referral_type,
        service_line=referral_data.service_line,
        specialty=referral_data.specialty,
        priority=referral_data.priority,
        clinical_summary=referral_data.clinical_summary,
        provisional_diagnosis=referral_data.provisional_diagnosis,
        requested_services=referral_data.requested_services,
        requested_appointment_date=referral_data.requested_appointment_date,
        transport_required=referral_data.transport_required,
        status="draft",
        metadata=referral_data.metadata
    )

    db.add(referral)
    db.commit()
    db.refresh(referral)

    # Create FHIR ServiceRequest
    fhir_service_request = create_fhir_service_request(referral, patient, source_org, target_org)
    referral.fhir_service_request_id = fhir_service_request.get("id")
    db.commit()

    # Publish event
    await publish_event(
        EventType.REFERRAL_CREATED,
        {
            "referral_id": str(referral.id),
            "patient_id": str(referral.patient_id),
            "source_org_code": source_org.code,
            "target_org_code": target_org.code,
            "referral_type": referral.referral_type,
            "priority": referral.priority
        }
    )

    logger.info(f"Referral created: {referral.id} from {source_org.code} to {target_org.code}")
    return referral


@app.get(
    "/api/v1/referrals/referrals",
    response_model=ReferralListResponse,
    tags=["Referrals"]
)
async def list_referrals(
    patient_id: Optional[UUID] = Query(None, description="Filter by patient"),
    source_org_id: Optional[UUID] = Query(None, description="Filter by source org"),
    target_org_id: Optional[UUID] = Query(None, description="Filter by target org"),
    status: Optional[str] = Query(None, description="Filter by status"),
    referral_type: Optional[str] = Query(None, description="Filter by type"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    from_date: Optional[datetime] = Query(None, description="Created after"),
    to_date: Optional[datetime] = Query(None, description="Created before"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List referrals with comprehensive filtering options.

    Supports filtering by patient, organizations, status, type, priority, and date range.
    """
    query = db.query(Referral)

    # Apply filters
    if patient_id:
        query = query.filter(Referral.patient_id == patient_id)

    if source_org_id:
        query = query.filter(Referral.source_org_id == source_org_id)

    if target_org_id:
        query = query.filter(Referral.target_org_id == target_org_id)

    if status:
        query = query.filter(Referral.status == status.lower())

    if referral_type:
        query = query.filter(Referral.referral_type == referral_type.upper())

    if priority:
        query = query.filter(Referral.priority == priority.lower())

    if from_date:
        query = query.filter(Referral.created_at >= from_date)

    if to_date:
        query = query.filter(Referral.created_at <= to_date)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    referrals = query.order_by(
        Referral.created_at.desc()
    ).offset(offset).limit(page_size).all()

    return ReferralListResponse(
        total=total,
        referrals=referrals,
        page=page,
        page_size=page_size,
        has_next=offset + page_size < total,
        has_previous=page > 1
    )


@app.get(
    "/api/v1/referrals/referrals/{referral_id}",
    response_model=ReferralResponse,
    tags=["Referrals"]
)
async def get_referral(
    referral_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a referral by ID."""
    referral = db.query(Referral).filter(Referral.id == referral_id).first()

    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")

    return referral


@app.patch(
    "/api/v1/referrals/referrals/{referral_id}",
    response_model=ReferralResponse,
    tags=["Referrals"]
)
async def update_referral(
    referral_id: UUID,
    update_data: ReferralUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Update referral details (clinical summary, requested date, etc.)."""
    referral = db.query(Referral).filter(Referral.id == referral_id).first()

    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")

    # Only allow updates if not completed/cancelled
    if referral.status in ["completed", "cancelled"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot update referral in '{referral.status}' status"
        )

    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(referral, field, value)

    referral.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(referral)

    logger.info(f"Referral updated: {referral.id}")
    return referral


@app.post(
    "/api/v1/referrals/referrals/{referral_id}/send",
    response_model=ReferralResponse,
    tags=["Referrals"]
)
async def send_referral(
    referral_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Send referral to target organization.

    Transitions status from 'draft' to 'sent' and triggers notification to target org.
    """
    referral = db.query(Referral).filter(Referral.id == referral_id).first()

    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")

    if referral.status != "draft":
        raise HTTPException(
            status_code=400,
            detail=f"Can only send referrals in 'draft' status. Current status: {referral.status}"
        )

    # Update status
    referral.status = "sent"
    referral.sent_at = datetime.utcnow()
    referral.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(referral)

    # Get orgs for event
    target_org = db.query(NetworkOrganization).filter(
        NetworkOrganization.id == referral.target_org_id
    ).first()

    # Publish event
    await publish_event(
        EventType.REFERRAL_SENT,
        {
            "referral_id": str(referral.id),
            "patient_id": str(referral.patient_id),
            "target_org_code": target_org.code if target_org else None,
            "priority": referral.priority,
            "sent_at": referral.sent_at.isoformat()
        }
    )

    # TODO: Trigger notification to target org (email, webhook, FHIR messaging)

    logger.info(f"Referral sent: {referral.id} to {target_org.code if target_org else 'unknown'}")
    return referral


@app.post(
    "/api/v1/referrals/referrals/{referral_id}/accept",
    response_model=ReferralResponse,
    tags=["Referrals"]
)
async def accept_referral(
    referral_id: UUID,
    status_update: ReferralStatusUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Accept a referral from source organization.

    Transitions to 'accepted' or 'scheduled' status.
    Optionally provide scheduled appointment time.
    """
    referral = db.query(Referral).filter(Referral.id == referral_id).first()

    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")

    if referral.status not in ["sent"]:
        raise HTTPException(
            status_code=400,
            detail=f"Can only accept referrals in 'sent' status. Current: {referral.status}"
        )

    # Validate status
    if status_update.status not in ["accepted", "scheduled"]:
        raise HTTPException(
            status_code=400,
            detail="When accepting, status must be 'accepted' or 'scheduled'"
        )

    # Update status
    referral.status = status_update.status
    referral.status_reason = status_update.status_reason
    referral.scheduled_appointment_time = status_update.scheduled_appointment_time
    referral.responded_at = datetime.utcnow()
    referral.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(referral)

    # Publish event
    await publish_event(
        EventType.REFERRAL_ACCEPTED,
        {
            "referral_id": str(referral.id),
            "patient_id": str(referral.patient_id),
            "status": referral.status,
            "scheduled_time": referral.scheduled_appointment_time.isoformat() if referral.scheduled_appointment_time else None
        }
    )

    logger.info(f"Referral accepted: {referral.id}, status: {referral.status}")
    return referral


@app.post(
    "/api/v1/referrals/referrals/{referral_id}/reject",
    response_model=ReferralResponse,
    tags=["Referrals"]
)
async def reject_referral(
    referral_id: UUID,
    status_update: ReferralStatusUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Reject a referral from source organization.

    Requires a reason for rejection.
    """
    referral = db.query(Referral).filter(Referral.id == referral_id).first()

    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")

    if referral.status not in ["sent"]:
        raise HTTPException(
            status_code=400,
            detail=f"Can only reject referrals in 'sent' status. Current: {referral.status}"
        )

    if not status_update.status_reason:
        raise HTTPException(
            status_code=400,
            detail="Rejection reason is required"
        )

    # Update status
    referral.status = "rejected"
    referral.status_reason = status_update.status_reason
    referral.responded_at = datetime.utcnow()
    referral.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(referral)

    # Publish event
    await publish_event(
        EventType.REFERRAL_REJECTED,
        {
            "referral_id": str(referral.id),
            "patient_id": str(referral.patient_id),
            "reason": referral.status_reason
        }
    )

    logger.info(f"Referral rejected: {referral.id}, reason: {referral.status_reason}")
    return referral


@app.post(
    "/api/v1/referrals/referrals/{referral_id}/complete",
    response_model=ReferralResponse,
    tags=["Referrals"]
)
async def complete_referral(
    referral_id: UUID,
    status_update: ReferralStatusUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Mark referral as completed with outcome summary.

    Provide outcome summary of services delivered.
    """
    referral = db.query(Referral).filter(Referral.id == referral_id).first()

    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")

    if referral.status in ["draft", "sent", "rejected", "cancelled"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot complete referral in '{referral.status}' status"
        )

    # Update status
    referral.status = "completed"
    referral.outcome_summary = status_update.outcome_summary
    referral.completed_at = datetime.utcnow()
    referral.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(referral)

    # Publish event
    await publish_event(
        EventType.REFERRAL_COMPLETED,
        {
            "referral_id": str(referral.id),
            "patient_id": str(referral.patient_id),
            "completed_at": referral.completed_at.isoformat()
        }
    )

    logger.info(f"Referral completed: {referral.id}")
    return referral


# ==================== Referral Document Endpoints ====================

@app.post(
    "/api/v1/referrals/referrals/{referral_id}/documents",
    response_model=ReferralDocumentResponse,
    status_code=201,
    tags=["Referral Documents"]
)
async def attach_document(
    referral_id: UUID,
    document_data: ReferralDocumentCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Attach a document to a referral.

    Documents can include clinical summaries, lab reports, imaging, consent forms, etc.
    """
    # Validate referral exists
    referral = db.query(Referral).filter(Referral.id == referral_id).first()
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")

    # Create document record
    document = ReferralDocument(
        referral_id=referral_id,
        document_type=document_data.document_type,
        file_url=document_data.file_url,
        file_name=document_data.file_name,
        mime_type=document_data.mime_type,
        file_size_bytes=document_data.file_size_bytes,
        description=document_data.description,
        uploaded_by_user_id=current_user_id,  # From auth middleware
        fhir_document_reference_id=document_data.fhir_document_reference_id
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    # Create FHIR DocumentReference if not provided
    if not document.fhir_document_reference_id:
        fhir_doc_ref = create_fhir_document_reference(document, referral)
        document.fhir_document_reference_id = fhir_doc_ref.get("id")
        db.commit()

    logger.info(f"Document attached to referral {referral_id}: {document.file_name}")
    return document


@app.get(
    "/api/v1/referrals/referrals/{referral_id}/documents",
    response_model=ReferralDocumentListResponse,
    tags=["Referral Documents"]
)
async def list_referral_documents(
    referral_id: UUID,
    db: Session = Depends(get_db)
):
    """List all documents attached to a referral."""
    # Validate referral exists
    referral = db.query(Referral).filter(Referral.id == referral_id).first()
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")

    documents = db.query(ReferralDocument).filter(
        ReferralDocument.referral_id == referral_id
    ).order_by(ReferralDocument.created_at.desc()).all()

    return ReferralDocumentListResponse(
        total=len(documents),
        documents=documents
    )


# ==================== Helper Functions ====================

def create_fhir_service_request(
    referral: Referral,
    patient: Patient,
    source_org: NetworkOrganization,
    target_org: NetworkOrganization
) -> dict:
    """
    Create FHIR R4 ServiceRequest for referral.

    This will be stored in the FHIR service and linked to the referral.
    """
    fhir_service_request = {
        "resourceType": "ServiceRequest",
        "id": f"referral-{referral.id}",
        "status": "active",
        "intent": "order",
        "priority": referral.priority,
        "category": [{
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": "3457005",
                "display": "Patient referral"
            }]
        }],
        "code": {
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": "308292007",
                "display": referral.service_line or "Transfer of care"
            }],
            "text": referral.clinical_summary[:100]
        },
        "subject": {
            "reference": f"Patient/{patient.fhir_patient_id}",
            "display": f"{patient.first_name} {patient.last_name}"
        },
        "authoredOn": referral.created_at.isoformat(),
        "requester": {
            "reference": f"Organization/{source_org.code}",
            "display": source_org.name
        },
        "performer": [{
            "reference": f"Organization/{target_org.code}",
            "display": target_org.name
        }],
        "reasonCode": [
            {"text": diag} for diag in (referral.provisional_diagnosis or [])
        ],
        "note": [{
            "text": referral.clinical_summary
        }]
    }

    # TODO: Actually POST this to FHIR service
    # For now, just return mock response
    return {"id": f"ServiceRequest-{referral.id}"}


def create_fhir_document_reference(document: ReferralDocument, referral: Referral) -> dict:
    """
    Create FHIR R4 DocumentReference for referral document.
    """
    fhir_doc_ref = {
        "resourceType": "DocumentReference",
        "id": f"referral-doc-{document.id}",
        "status": "current",
        "type": {
            "coding": [{
                "system": "http://loinc.org",
                "code": "11488-4",
                "display": "Consultation note"
            }],
            "text": document.document_type
        },
        "subject": {
            "reference": f"Patient/{referral.patient_id}"
        },
        "date": document.created_at.isoformat(),
        "author": [{
            "reference": f"User/{document.uploaded_by_user_id}"
        }],
        "content": [{
            "attachment": {
                "contentType": document.mime_type,
                "url": document.file_url,
                "size": document.file_size_bytes,
                "title": document.file_name
            }
        }],
        "context": {
            "related": [{
                "reference": f"ServiceRequest/{referral.fhir_service_request_id}"
            }]
        }
    }

    # TODO: POST to FHIR service
    return {"id": f"DocumentReference-{document.id}"}


# Health check
@app.get("/health", tags=["System"])
async def health_check():
    """Service health check endpoint."""
    return {
        "service": "referral-network-service",
        "status": "healthy",
        "version": "0.1.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8021)
