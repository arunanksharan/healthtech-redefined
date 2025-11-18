"""
Consent Orchestration Service
FastAPI service for cross-organization consent management and evaluation
Port: 8024
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID
import json

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import IntegrityError

from shared.database.models import (
    ConsentPolicy,
    ConsentRecord,
    Patient,
    NetworkOrganization,
    App,
    Tenant
)
from shared.events.types import EventType
from shared.events.publisher import publish_event
from schemas import (
    ConsentPolicyCreate,
    ConsentPolicyUpdate,
    ConsentPolicyResponse,
    ConsentPolicyListResponse,
    ConsentRecordCreate,
    ConsentRecordUpdate,
    ConsentRecordResponse,
    ConsentRecordListResponse,
    ConsentEvaluationRequest,
    ConsentEvaluationResponse,
    ConsentRevocationRequest
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
    title="Consent Orchestration Service",
    description="Cross-organization consent management with policy templates and evaluation",
    version="0.1.0"
)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== Consent Policy Endpoints ====================

@app.post(
    "/api/v1/consent/policies",
    response_model=ConsentPolicyResponse,
    status_code=201,
    tags=["Consent Policies"]
)
async def create_consent_policy(
    policy_data: ConsentPolicyCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Create a consent policy template.

    - **policy_type**: referral, research, emergency_access, app_integration
    - **data_categories**: Categories of data covered by this consent
    - **permitted_use_cases**: Allowed use cases (treatment, research, etc.)
    """
    # Check if code already exists
    existing = db.query(ConsentPolicy).filter(
        and_(
            ConsentPolicy.tenant_id == policy_data.tenant_id,
            ConsentPolicy.code == policy_data.code
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Policy with code '{policy_data.code}' already exists"
        )

    # Create policy
    policy = ConsentPolicy(
        tenant_id=policy_data.tenant_id,
        code=policy_data.code,
        name=policy_data.name,
        description=policy_data.description,
        policy_type=policy_data.policy_type,
        data_categories=policy_data.data_categories,
        permitted_use_cases=policy_data.permitted_use_cases,
        default_duration_days=policy_data.default_duration_days,
        is_revocable=policy_data.is_revocable,
        requires_patient_signature=policy_data.requires_patient_signature,
        template_text=policy_data.template_text,
        is_active=policy_data.is_active
    )

    db.add(policy)

    try:
        db.commit()
        db.refresh(policy)

        # Publish event
        await publish_event(
            EventType.CONSENT_POLICY_CREATED,
            {
                "policy_id": str(policy.id),
                "code": policy.code,
                "policy_type": policy.policy_type
            }
        )

        logger.info(f"Consent policy created: {policy.code}")
        return policy

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")


@app.get(
    "/api/v1/consent/policies",
    response_model=ConsentPolicyListResponse,
    tags=["Consent Policies"]
)
async def list_consent_policies(
    tenant_id: Optional[UUID] = Query(None),
    policy_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None, description="Search by name or code"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List consent policies with filtering."""
    query = db.query(ConsentPolicy)

    if tenant_id:
        query = query.filter(ConsentPolicy.tenant_id == tenant_id)

    if policy_type:
        query = query.filter(ConsentPolicy.policy_type == policy_type.lower())

    if is_active is not None:
        query = query.filter(ConsentPolicy.is_active == is_active)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                ConsentPolicy.name.ilike(search_pattern),
                ConsentPolicy.code.ilike(search_pattern)
            )
        )

    total = query.count()
    offset = (page - 1) * page_size
    policies = query.order_by(ConsentPolicy.created_at.desc()).offset(offset).limit(page_size).all()

    return ConsentPolicyListResponse(
        total=total,
        policies=policies,
        page=page,
        page_size=page_size,
        has_next=offset + page_size < total,
        has_previous=page > 1
    )


@app.get(
    "/api/v1/consent/policies/{policy_id}",
    response_model=ConsentPolicyResponse,
    tags=["Consent Policies"]
)
async def get_consent_policy(
    policy_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a consent policy by ID."""
    policy = db.query(ConsentPolicy).filter(ConsentPolicy.id == policy_id).first()

    if not policy:
        raise HTTPException(status_code=404, detail="Consent policy not found")

    return policy


@app.patch(
    "/api/v1/consent/policies/{policy_id}",
    response_model=ConsentPolicyResponse,
    tags=["Consent Policies"]
)
async def update_consent_policy(
    policy_id: UUID,
    update_data: ConsentPolicyUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Update a consent policy template."""
    policy = db.query(ConsentPolicy).filter(ConsentPolicy.id == policy_id).first()

    if not policy:
        raise HTTPException(status_code=404, detail="Consent policy not found")

    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(policy, field, value)

    policy.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(policy)

    logger.info(f"Consent policy updated: {policy.code}")
    return policy


# ==================== Consent Record Endpoints ====================

@app.post(
    "/api/v1/consent/consents",
    response_model=ConsentRecordResponse,
    status_code=201,
    tags=["Consent Records"]
)
async def create_consent_record(
    consent_data: ConsentRecordCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Create a consent record for data sharing.

    - **consent_type**: explicit, implied, emergency_override
    - **data_controller_org_id**: Organization that controls the data
    - **data_processor_org_id**: Organization that will access the data (optional)
    - **app_id**: App that will access the data (optional)
    """
    # Validate patient exists
    patient = db.query(Patient).filter(Patient.id == consent_data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Validate policy exists
    policy = db.query(ConsentPolicy).filter(ConsentPolicy.id == consent_data.policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Consent policy not found")

    if not policy.is_active:
        raise HTTPException(status_code=400, detail="Cannot create consent with inactive policy")

    # Validate organizations exist
    controller_org = db.query(NetworkOrganization).filter(
        NetworkOrganization.id == consent_data.data_controller_org_id
    ).first()

    if not controller_org:
        raise HTTPException(status_code=404, detail="Data controller organization not found")

    if consent_data.data_processor_org_id:
        processor_org = db.query(NetworkOrganization).filter(
            NetworkOrganization.id == consent_data.data_processor_org_id
        ).first()
        if not processor_org:
            raise HTTPException(status_code=404, detail="Data processor organization not found")

    # Validate app if provided
    if consent_data.app_id:
        app_obj = db.query(App).filter(App.id == consent_data.app_id).first()
        if not app_obj:
            raise HTTPException(status_code=404, detail="App not found")

    # Calculate expiration if not provided
    expires_at = consent_data.expires_at
    if not expires_at and policy.default_duration_days:
        expires_at = consent_data.given_at + timedelta(days=policy.default_duration_days)

    # Create consent record
    consent = ConsentRecord(
        patient_id=consent_data.patient_id,
        policy_id=consent_data.policy_id,
        data_controller_org_id=consent_data.data_controller_org_id,
        data_processor_org_id=consent_data.data_processor_org_id,
        app_id=consent_data.app_id,
        consent_type=consent_data.consent_type,
        status=consent_data.status,
        given_at=consent_data.given_at,
        expires_at=expires_at,
        scope_overrides=consent_data.scope_overrides,
        patient_signature=consent_data.patient_signature,
        witness_user_id=consent_data.witness_user_id,
        notes=consent_data.notes
    )

    db.add(consent)
    db.commit()
    db.refresh(consent)

    # Publish event
    await publish_event(
        EventType.CONSENT_GIVEN,
        {
            "consent_id": str(consent.id),
            "patient_id": str(consent.patient_id),
            "policy_type": policy.policy_type,
            "consent_type": consent.consent_type,
            "expires_at": consent.expires_at.isoformat() if consent.expires_at else None
        }
    )

    logger.info(f"Consent record created: {consent.id} for patient {consent.patient_id}")
    return consent


@app.get(
    "/api/v1/consent/consents",
    response_model=ConsentRecordListResponse,
    tags=["Consent Records"]
)
async def list_consent_records(
    patient_id: Optional[UUID] = Query(None),
    policy_id: Optional[UUID] = Query(None),
    data_controller_org_id: Optional[UUID] = Query(None),
    data_processor_org_id: Optional[UUID] = Query(None),
    app_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    consent_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List consent records with comprehensive filtering."""
    query = db.query(ConsentRecord)

    if patient_id:
        query = query.filter(ConsentRecord.patient_id == patient_id)

    if policy_id:
        query = query.filter(ConsentRecord.policy_id == policy_id)

    if data_controller_org_id:
        query = query.filter(ConsentRecord.data_controller_org_id == data_controller_org_id)

    if data_processor_org_id:
        query = query.filter(ConsentRecord.data_processor_org_id == data_processor_org_id)

    if app_id:
        query = query.filter(ConsentRecord.app_id == app_id)

    if status:
        query = query.filter(ConsentRecord.status == status.lower())

    if consent_type:
        query = query.filter(ConsentRecord.consent_type == consent_type.lower())

    total = query.count()
    offset = (page - 1) * page_size
    consents = query.order_by(ConsentRecord.given_at.desc()).offset(offset).limit(page_size).all()

    return ConsentRecordListResponse(
        total=total,
        consents=consents,
        page=page,
        page_size=page_size,
        has_next=offset + page_size < total,
        has_previous=page > 1
    )


@app.get(
    "/api/v1/consent/consents/{consent_id}",
    response_model=ConsentRecordResponse,
    tags=["Consent Records"]
)
async def get_consent_record(
    consent_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a consent record by ID."""
    consent = db.query(ConsentRecord).filter(ConsentRecord.id == consent_id).first()

    if not consent:
        raise HTTPException(status_code=404, detail="Consent record not found")

    return consent


@app.patch(
    "/api/v1/consent/consents/{consent_id}",
    response_model=ConsentRecordResponse,
    tags=["Consent Records"]
)
async def update_consent_record(
    consent_id: UUID,
    update_data: ConsentRecordUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Update a consent record (status, expiration, notes)."""
    consent = db.query(ConsentRecord).filter(ConsentRecord.id == consent_id).first()

    if not consent:
        raise HTTPException(status_code=404, detail="Consent record not found")

    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(consent, field, value)

    consent.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(consent)

    logger.info(f"Consent record updated: {consent_id}")
    return consent


@app.post(
    "/api/v1/consent/consents/{consent_id}/revoke",
    response_model=ConsentRecordResponse,
    tags=["Consent Records"]
)
async def revoke_consent(
    consent_id: UUID,
    revocation_data: ConsentRevocationRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Revoke a consent.

    Only revocable consents can be revoked.
    """
    consent = db.query(ConsentRecord).filter(ConsentRecord.id == consent_id).first()

    if not consent:
        raise HTTPException(status_code=404, detail="Consent record not found")

    if consent.status == "revoked":
        raise HTTPException(status_code=400, detail="Consent already revoked")

    # Check if consent is revocable
    policy = db.query(ConsentPolicy).filter(ConsentPolicy.id == consent.policy_id).first()
    if policy and not policy.is_revocable:
        raise HTTPException(
            status_code=400,
            detail="This consent type is not revocable per policy"
        )

    # Revoke consent
    consent.status = "revoked"
    consent.revoked_at = datetime.utcnow()
    consent.updated_at = datetime.utcnow()

    if revocation_data.reason:
        consent.notes = f"{consent.notes or ''}\nRevocation reason: {revocation_data.reason}"

    db.commit()
    db.refresh(consent)

    # Publish event
    await publish_event(
        EventType.CONSENT_REVOKED,
        {
            "consent_id": str(consent.id),
            "patient_id": str(consent.patient_id),
            "revoked_at": consent.revoked_at.isoformat(),
            "reason": revocation_data.reason
        }
    )

    logger.info(f"Consent revoked: {consent_id} by user {current_user_id}")
    return consent


# ==================== Consent Evaluation Endpoint ====================

@app.post(
    "/api/v1/consent/consents/evaluate",
    response_model=ConsentEvaluationResponse,
    tags=["Consent Evaluation"]
)
async def evaluate_consent(
    evaluation_request: ConsentEvaluationRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluate if consent exists for a data access operation.

    Used by other services to check consent before allowing data access.

    Returns:
    - has_consent: True if valid consent exists
    - consent_records: Matching active consents
    - permitted_data_categories: What data can be accessed
    - restrictions: Any scope restrictions
    """
    # Validate patient exists
    patient = db.query(Patient).filter(Patient.id == evaluation_request.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Build query for matching consents
    query = db.query(ConsentRecord).filter(
        and_(
            ConsentRecord.patient_id == evaluation_request.patient_id,
            ConsentRecord.data_controller_org_id == evaluation_request.data_controller_org_id,
            ConsentRecord.status == "active"
        )
    )

    # Filter by processor org or app
    if evaluation_request.data_processor_org_id:
        query = query.filter(
            ConsentRecord.data_processor_org_id == evaluation_request.data_processor_org_id
        )

    if evaluation_request.app_id:
        query = query.filter(ConsentRecord.app_id == evaluation_request.app_id)

    # Get active consents
    current_time = datetime.utcnow()
    active_consents = []

    for consent in query.all():
        # Check if not expired
        if consent.expires_at and consent.expires_at < current_time:
            # Auto-expire
            consent.status = "expired"
            db.commit()
            continue

        active_consents.append(consent)

    if not active_consents:
        # Check if emergency override is available
        emergency_policy = db.query(ConsentPolicy).filter(
            and_(
                ConsentPolicy.policy_type == "emergency_access",
                ConsentPolicy.is_active == True
            )
        ).first()

        return ConsentEvaluationResponse(
            has_consent=False,
            reason="No active consent found for this operation",
            emergency_override_available=emergency_policy is not None
        )

    # Evaluate data categories and use cases
    permitted_categories = set()
    all_restrictions = {}

    for consent in active_consents:
        policy = db.query(ConsentPolicy).filter(ConsentPolicy.id == consent.policy_id).first()

        if not policy:
            continue

        # Check if use case is permitted
        if evaluation_request.use_case.lower() not in [uc.lower() for uc in policy.permitted_use_cases]:
            continue

        # Add permitted categories from policy
        permitted_categories.update(policy.data_categories)

        # Apply scope overrides
        if consent.scope_overrides:
            # Remove excluded categories
            if "exclude_categories" in consent.scope_overrides:
                for excluded in consent.scope_overrides["exclude_categories"]:
                    permitted_categories.discard(excluded)

            # Merge restrictions
            all_restrictions.update(consent.scope_overrides)

    # Check if requested categories are permitted
    requested_categories = set(evaluation_request.requested_data_categories)
    if not requested_categories.issubset(permitted_categories):
        denied_categories = requested_categories - permitted_categories
        return ConsentEvaluationResponse(
            has_consent=False,
            consent_records=active_consents,
            permitted_data_categories=list(permitted_categories),
            restrictions=all_restrictions if all_restrictions else None,
            reason=f"Data categories not permitted by consent: {', '.join(denied_categories)}"
        )

    # Consent granted
    policy_types = [
        db.query(ConsentPolicy).filter(ConsentPolicy.id == c.policy_id).first().policy_type
        for c in active_consents
        if db.query(ConsentPolicy).filter(ConsentPolicy.id == c.policy_id).first()
    ]

    return ConsentEvaluationResponse(
        has_consent=True,
        consent_records=active_consents,
        policy_type=policy_types[0] if policy_types else None,
        permitted_data_categories=list(permitted_categories),
        restrictions=all_restrictions if all_restrictions else None
    )


# ==================== Helper Functions ====================

def check_consent_expiration(db: Session):
    """
    Background task to auto-expire consents.
    Should be called periodically.
    """
    current_time = datetime.utcnow()

    expired_consents = db.query(ConsentRecord).filter(
        and_(
            ConsentRecord.status == "active",
            ConsentRecord.expires_at.isnot(None),
            ConsentRecord.expires_at < current_time
        )
    ).all()

    for consent in expired_consents:
        consent.status = "expired"

    if expired_consents:
        db.commit()
        logger.info(f"Auto-expired {len(expired_consents)} consents")

    return len(expired_consents)


# Health check
@app.get("/health", tags=["System"])
async def health_check():
    """Service health check endpoint."""
    return {
        "service": "consent-orchestration-service",
        "status": "healthy",
        "version": "0.1.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8024)
