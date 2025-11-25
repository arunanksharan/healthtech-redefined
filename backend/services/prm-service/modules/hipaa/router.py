"""
HIPAA Compliance Router

FastAPI router for EPIC-022: HIPAA Compliance
Includes endpoints for audit logging, access control, retention, breach management,
BAA tracking, training, and risk assessment.
"""

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from modules.hipaa.schemas import (
    # Audit
    PHIAuditLogCreate,
    PHIAuditLogResponse,
    AuditLogSearchRequest,
    AuditLogSearchResponse,
    AuditRetentionPolicyCreate,
    AuditRetentionPolicyResponse,
    # Access Control
    TreatmentRelationshipCreate,
    TreatmentRelationshipResponse,
    AccessRequestCreate,
    AccessRequestResponse,
    AccessRequestApproval,
    AccessCertificationResponse,
    CertificationCampaignCreate,
    CertificationCampaignResponse,
    AccessAnomalyResponse,
    AnomalyAcknowledge,
    AnomalyResolve,
    VIPPatientCreate,
    VIPPatientResponse,
    # Retention
    RetentionPolicyCreate,
    RetentionPolicyResponse,
    RetentionScheduleResponse,
    LegalHoldCreate,
    LegalHoldResponse,
    LegalHoldRelease,
    DestructionCertificateResponse,
    RightOfAccessRequestCreate,
    RightOfAccessRequestResponse,
    RightOfAccessVerifyIdentity,
    RightOfAccessExtend,
    RightOfAccessDeliver,
    RightOfAccessDeny,
    # Breach
    BreachIncidentCreate,
    BreachIncidentResponse,
    BreachIncidentUpdate,
    BreachAssessmentCreate,
    BreachAssessmentResponse,
    BreachNotificationCreate,
    BreachNotificationResponse,
    BreachNotificationSend,
    # BAA
    BusinessAssociateAgreementCreate,
    BusinessAssociateAgreementResponse,
    BAAExecute,
    BAATerminate,
    BAAAmendmentCreate,
    BAAAmendmentResponse,
    BAATemplateCreate,
    BAATemplateResponse,
    # Training
    TrainingModuleCreate,
    TrainingModuleResponse,
    TrainingAssignmentCreate,
    TrainingAssignmentResponse,
    TrainingComplete,
    PolicyDocumentCreate,
    PolicyDocumentResponse,
    PolicyAcknowledgmentResponse,
    # Risk
    RiskAssessmentCreate,
    RiskAssessmentResponse,
    RiskAssessmentComplete,
    RiskItemCreate,
    RiskItemResponse,
    RemediationPlanCreate,
    RemediationPlanResponse,
    RemediationUpdate,
    RemediationVerify,
    RiskAcceptance,
    RiskRegisterResponse,
    # Dashboard
    ComplianceDashboard,
    AuditReport,
    BAAComplianceReport,
    TrainingComplianceReport,
    RiskSummaryReport,
    # Enums
    AuditAction,
    PHICategory,
    AuditOutcome,
    AnomalySeverity,
    RetentionCategory,
    BreachStatus,
    BAAType,
    BAAStatus,
    TrainingType,
    TrainingStatus,
    RiskLevel,
    RiskCategory,
    RemediationStatus,
    AccessJustification,
)
from modules.hipaa.services import (
    AuditService,
    AccessControlService,
    RetentionService,
    BreachService,
    BAAService,
    TrainingService,
    RiskService,
)

router = APIRouter(prefix="/hipaa", tags=["hipaa-compliance"])


# ============================================================================
# Dependency helpers
# ============================================================================

async def get_db() -> AsyncSession:
    """Database session dependency - placeholder for actual implementation."""
    # This would be replaced with actual database session management
    raise NotImplementedError("Database session dependency not configured")


async def get_current_tenant_id(request: Request) -> UUID:
    """Extract tenant ID from request - placeholder for actual implementation."""
    # This would be replaced with actual tenant extraction logic
    tenant_id = request.headers.get("X-Tenant-ID")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant ID required")
    return UUID(tenant_id)


async def get_current_user_id(request: Request) -> UUID:
    """Extract current user ID from request - placeholder for actual implementation."""
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return UUID(user_id)


# ============================================================================
# Audit Logging Endpoints
# ============================================================================

@router.post("/audit/logs", response_model=PHIAuditLogResponse)
async def create_audit_log(
    data: PHIAuditLogCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
):
    """Create a PHI audit log entry."""
    service = AuditService(db, tenant_id)
    log = await service.log_phi_access(
        event_type=data.event_type,
        action=data.action,
        phi_category=data.phi_category,
        resource_type=data.resource_type,
        resource_id=data.resource_id,
        patient_id=data.patient_id,
        user_id=data.user_id or user_id,
        user_name=data.user_name,
        user_type=data.user_type,
        user_role=data.user_role,
        source_ip=data.source_ip,
        user_agent=data.user_agent,
        session_id=data.session_id,
        request_id=data.request_id,
        patient_mrn=data.patient_mrn,
        encounter_id=data.encounter_id,
        justification=data.justification,
        justification_details=data.justification_details,
        fields_accessed=data.fields_accessed,
        query_parameters=data.query_parameters,
        data_before=data.data_before,
        data_after=data.data_after,
        outcome=data.outcome,
        service_name=data.service_name,
        api_endpoint=data.api_endpoint,
        http_method=data.http_method,
        response_code=data.response_code,
    )
    return log


@router.post("/audit/logs/search", response_model=AuditLogSearchResponse)
async def search_audit_logs(
    search: AuditLogSearchRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Search audit logs with filtering."""
    service = AuditService(db, tenant_id)
    logs, total = await service.search_logs(
        user_id=search.user_id,
        patient_id=search.patient_id,
        action=search.action,
        phi_category=search.phi_category,
        resource_type=search.resource_type,
        outcome=search.outcome,
        start_date=search.start_date,
        end_date=search.end_date,
        source_ip=search.source_ip,
        limit=search.limit,
        offset=search.offset,
    )
    return AuditLogSearchResponse(
        logs=logs,
        total=total,
        has_more=total > search.offset + len(logs)
    )


@router.get("/audit/logs/{log_id}", response_model=PHIAuditLogResponse)
async def get_audit_log(
    log_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Get a specific audit log entry."""
    service = AuditService(db, tenant_id)
    log = await service.get_log_by_id(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return log


@router.get("/audit/logs/{log_id}/verify")
async def verify_audit_log_integrity(
    log_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Verify audit log integrity and hash chain."""
    service = AuditService(db, tenant_id)
    result = await service.verify_log_integrity(log_id)
    return result


@router.get("/audit/patient/{patient_id}/history", response_model=List[PHIAuditLogResponse])
async def get_patient_access_history(
    patient_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Get complete access history for a patient."""
    service = AuditService(db, tenant_id)
    logs = await service.get_patient_access_history(patient_id, start_date, end_date)
    return logs


@router.get("/audit/statistics")
async def get_audit_statistics(
    start_date: datetime,
    end_date: datetime,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Get audit log statistics for reporting."""
    service = AuditService(db, tenant_id)
    return await service.get_audit_statistics(start_date, end_date)


@router.post("/audit/retention-policies", response_model=AuditRetentionPolicyResponse)
async def create_audit_retention_policy(
    data: AuditRetentionPolicyCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
):
    """Create an audit retention policy."""
    service = AuditService(db, tenant_id)
    policy = await service.create_retention_policy(
        name=data.name,
        description=data.description,
        retention_days=data.retention_days,
        archive_after_days=data.archive_after_days,
        archive_storage_class=data.archive_storage_class,
        applies_to_actions=data.applies_to_actions,
        applies_to_categories=data.applies_to_categories,
        is_default=data.is_default,
        created_by=user_id,
    )
    return policy


@router.get("/audit/retention-policies", response_model=List[AuditRetentionPolicyResponse])
async def list_audit_retention_policies(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """List audit retention policies."""
    service = AuditService(db, tenant_id)
    return await service.list_retention_policies(active_only)


# ============================================================================
# Access Control Endpoints
# ============================================================================

@router.post("/access/relationships", response_model=TreatmentRelationshipResponse)
async def create_treatment_relationship(
    data: TreatmentRelationshipCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
):
    """Create a treatment relationship."""
    service = AccessControlService(db, tenant_id)
    relationship = await service.create_treatment_relationship(
        patient_id=data.patient_id,
        provider_id=data.provider_id,
        provider_type=data.provider_type,
        relationship_type=data.relationship_type,
        effective_date=datetime.combine(data.effective_date, datetime.min.time()),
        expiration_date=datetime.combine(data.expiration_date, datetime.min.time()) if data.expiration_date else None,
        referral_id=data.referral_id,
        authorization_number=data.authorization_number,
        care_team_id=data.care_team_id,
        care_team_role=data.care_team_role,
        facility_id=data.facility_id,
        department=data.department,
        allowed_phi_categories=data.allowed_phi_categories,
        restricted_phi_categories=data.restricted_phi_categories,
        created_by=user_id,
    )
    return relationship


@router.get("/access/relationships/verify")
async def verify_treatment_relationship(
    patient_id: UUID,
    provider_id: UUID,
    phi_category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Verify treatment relationship between patient and provider."""
    service = AccessControlService(db, tenant_id)
    is_valid, relationship, reason = await service.verify_treatment_relationship(
        patient_id, provider_id, phi_category
    )
    return {
        "is_valid": is_valid,
        "relationship_id": str(relationship.id) if relationship else None,
        "reason": reason,
    }


@router.get("/access/relationships/patient/{patient_id}", response_model=List[TreatmentRelationshipResponse])
async def get_patient_relationships(
    patient_id: UUID,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Get all treatment relationships for a patient."""
    service = AccessControlService(db, tenant_id)
    return await service.get_patient_relationships(patient_id, active_only)


@router.post("/access/requests", response_model=AccessRequestResponse)
async def create_access_request(
    data: AccessRequestCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
):
    """Create a PHI access request."""
    service = AccessControlService(db, tenant_id)
    request = await service.create_access_request(
        requester_id=user_id,
        patient_id=data.patient_id,
        requested_phi_categories=data.requested_phi_categories,
        justification=data.justification,
        justification_details=data.justification_details,
        requested_resources=data.requested_resources,
        clinical_context=data.clinical_context,
    )
    return request


@router.post("/access/requests/{request_id}/approve", response_model=AccessRequestResponse)
async def approve_access_request(
    request_id: UUID,
    data: AccessRequestApproval,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
):
    """Approve or deny an access request."""
    service = AccessControlService(db, tenant_id)
    if data.approved:
        request = await service.approve_access_request(
            request_id, user_id, access_duration_hours=data.access_duration_hours or 24
        )
    else:
        request = await service.deny_access_request(
            request_id, user_id, data.denial_reason or "Access denied"
        )

    if not request:
        raise HTTPException(status_code=404, detail="Access request not found")
    return request


@router.get("/access/requests/pending", response_model=List[AccessRequestResponse])
async def list_pending_access_requests(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """List pending access requests."""
    service = AccessControlService(db, tenant_id)
    return await service.list_pending_access_requests()


@router.post("/access/certifications/campaigns", response_model=CertificationCampaignResponse)
async def create_certification_campaign(
    data: CertificationCampaignCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
):
    """Create an access certification campaign."""
    service = AccessControlService(db, tenant_id)
    campaign = await service.create_certification_campaign(
        name=data.name,
        description=data.description,
        start_date=data.start_date,
        end_date=data.end_date,
        scope_type=data.scope_type,
        scope_criteria=data.scope_criteria,
        created_by=user_id,
    )
    return campaign


@router.get("/access/certifications/pending", response_model=List[AccessCertificationResponse])
async def get_pending_certifications(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
):
    """Get pending certifications for current user."""
    service = AccessControlService(db, tenant_id)
    return await service.get_pending_certifications(user_id)


@router.post("/access/certifications/{certification_id}/certify")
async def certify_access(
    certification_id: UUID,
    certified: bool,
    comments: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Certify or decertify access."""
    service = AccessControlService(db, tenant_id)
    certification = await service.certify_access(certification_id, certified, comments)
    if not certification:
        raise HTTPException(status_code=404, detail="Certification not found")
    return certification


@router.get("/access/anomalies", response_model=List[AccessAnomalyResponse])
async def list_open_anomalies(
    severity: Optional[AnomalySeverity] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """List open access anomalies."""
    service = AccessControlService(db, tenant_id)
    return await service.list_open_anomalies(severity)


@router.post("/access/anomalies/{anomaly_id}/acknowledge")
async def acknowledge_anomaly(
    anomaly_id: UUID,
    data: AnomalyAcknowledge,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
):
    """Acknowledge an access anomaly."""
    service = AccessControlService(db, tenant_id)
    anomaly = await service.acknowledge_anomaly(anomaly_id, user_id, data.investigation_notes)
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    return anomaly


@router.post("/access/anomalies/{anomaly_id}/resolve")
async def resolve_anomaly(
    anomaly_id: UUID,
    data: AnomalyResolve,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Resolve an access anomaly."""
    service = AccessControlService(db, tenant_id)
    anomaly = await service.resolve_anomaly(anomaly_id, data.resolution, data.false_positive)
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    return anomaly


@router.post("/access/vip-patients", response_model=VIPPatientResponse)
async def designate_vip_patient(
    data: VIPPatientCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
):
    """Designate a patient as VIP."""
    service = AccessControlService(db, tenant_id)
    vip = await service.designate_vip_patient(
        patient_id=data.patient_id,
        vip_reason=data.vip_reason,
        enhanced_monitoring=data.enhanced_monitoring,
        access_alerts_enabled=data.access_alerts_enabled,
        allowed_user_ids=data.allowed_user_ids,
        allowed_roles=data.allowed_roles,
        alert_recipients=data.alert_recipients,
        created_by=user_id,
    )
    return vip


@router.get("/access/vip-patients", response_model=List[VIPPatientResponse])
async def list_vip_patients(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """List VIP patients."""
    service = AccessControlService(db, tenant_id)
    return await service.list_vip_patients()


# ============================================================================
# Retention Endpoints
# ============================================================================

@router.post("/retention/policies", response_model=RetentionPolicyResponse)
async def create_retention_policy(
    data: RetentionPolicyCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
):
    """Create a data retention policy."""
    service = RetentionService(db, tenant_id)
    policy = await service.create_retention_policy(
        name=data.name,
        description=data.description,
        category=data.category,
        resource_types=data.resource_types,
        retention_years=data.retention_years,
        retention_months=data.retention_months,
        applies_to_minors=data.applies_to_minors,
        minor_retention_from_age=data.minor_retention_from_age,
        minor_additional_years=data.minor_additional_years,
        jurisdiction=data.jurisdiction,
        regulation_reference=data.regulation_reference,
        destruction_method=data.destruction_method,
        require_destruction_certificate=data.require_destruction_certificate,
        archive_before_destruction=data.archive_before_destruction,
        is_default=data.is_default,
        created_by=user_id,
    )
    return policy


@router.get("/retention/policies", response_model=List[RetentionPolicyResponse])
async def list_retention_policies(
    active_only: bool = True,
    category: Optional[RetentionCategory] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """List retention policies."""
    service = RetentionService(db, tenant_id)
    return await service.list_retention_policies(active_only, category)


@router.post("/retention/legal-holds", response_model=LegalHoldResponse)
async def create_legal_hold(
    data: LegalHoldCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
):
    """Create a legal hold."""
    service = RetentionService(db, tenant_id)
    hold = await service.create_legal_hold(
        name=data.name,
        description=data.description,
        hold_type=data.hold_type,
        matter_reference=data.matter_reference,
        scope_type=data.scope_type,
        scope_criteria=data.scope_criteria,
        effective_date=data.effective_date,
        created_by=user_id,
        affected_patient_ids=data.affected_patient_ids,
        legal_contact_name=data.legal_contact_name,
        legal_contact_email=data.legal_contact_email,
    )
    return hold


@router.get("/retention/legal-holds", response_model=List[LegalHoldResponse])
async def list_legal_holds(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """List legal holds."""
    service = RetentionService(db, tenant_id)
    return await service.list_legal_holds(active_only)


@router.post("/retention/legal-holds/{hold_id}/release", response_model=LegalHoldResponse)
async def release_legal_hold(
    hold_id: UUID,
    data: LegalHoldRelease,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
):
    """Release a legal hold."""
    service = RetentionService(db, tenant_id)
    hold = await service.release_legal_hold(hold_id, user_id, data.release_reason)
    if not hold:
        raise HTTPException(status_code=404, detail="Legal hold not found")
    return hold


@router.post("/retention/right-of-access", response_model=RightOfAccessRequestResponse)
async def create_right_of_access_request(
    data: RightOfAccessRequestCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Create a Right of Access (patient data export) request."""
    service = RetentionService(db, tenant_id)
    request = await service.create_right_of_access_request(
        patient_id=data.patient_id,
        requestor_type=data.requestor_type,
        representative_name=data.representative_name,
        representative_relationship=data.representative_relationship,
        delivery_email=data.delivery_email,
        delivery_address=data.delivery_address,
        delivery_method=data.delivery_method,
        requested_records=data.requested_records,
        date_range_start=data.date_range_start,
        date_range_end=data.date_range_end,
    )
    return request


@router.get("/retention/right-of-access/pending", response_model=List[RightOfAccessRequestResponse])
async def list_pending_roa_requests(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """List pending Right of Access requests."""
    service = RetentionService(db, tenant_id)
    return await service.list_pending_roa_requests()


@router.post("/retention/right-of-access/{request_id}/verify-identity")
async def verify_roa_identity(
    request_id: UUID,
    data: RightOfAccessVerifyIdentity,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
):
    """Verify identity for Right of Access request."""
    service = RetentionService(db, tenant_id)
    request = await service.verify_identity(request_id, data.verification_method, user_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    return request


@router.post("/retention/right-of-access/{request_id}/extend")
async def extend_roa_deadline(
    request_id: UUID,
    data: RightOfAccessExtend,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Extend Right of Access deadline."""
    service = RetentionService(db, tenant_id)
    request = await service.extend_deadline(request_id, data.extension_reason)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found or already extended")
    return request


# ============================================================================
# Breach Management Endpoints
# ============================================================================

@router.post("/breach/incidents", response_model=BreachIncidentResponse)
async def create_breach_incident(
    data: BreachIncidentCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
):
    """Create a breach incident."""
    service = BreachService(db, tenant_id)
    incident = await service.create_breach_incident(
        breach_type=data.breach_type,
        description=data.description,
        phi_categories_involved=data.phi_categories_involved,
        discovered_date=data.discovered_date,
        discovered_by=user_id,
        discovery_method=data.discovery_method,
        breach_date=data.breach_date,
        phi_description=data.phi_description,
        breach_source=data.breach_source,
    )
    return incident


@router.get("/breach/incidents", response_model=List[BreachIncidentResponse])
async def list_breach_incidents(
    status: Optional[BreachStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """List breach incidents."""
    service = BreachService(db, tenant_id)
    return await service.list_incidents(status, start_date, end_date)


@router.get("/breach/incidents/active", response_model=List[BreachIncidentResponse])
async def get_active_investigations(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Get active breach investigations."""
    service = BreachService(db, tenant_id)
    return await service.get_active_investigations()


@router.get("/breach/incidents/{incident_id}", response_model=BreachIncidentResponse)
async def get_breach_incident(
    incident_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Get a breach incident."""
    service = BreachService(db, tenant_id)
    incident = await service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.patch("/breach/incidents/{incident_id}", response_model=BreachIncidentResponse)
async def update_breach_incident(
    incident_id: UUID,
    data: BreachIncidentUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Update a breach incident."""
    service = BreachService(db, tenant_id)
    incident = await service.update_incident_status(
        incident_id=incident_id,
        status=data.status,
        affected_individuals_count=data.affected_individuals_count,
        affected_patient_ids=data.affected_patient_ids,
        root_cause=data.root_cause,
        containment_actions=data.containment_actions,
        remediation_actions=data.remediation_actions,
        lessons_learned=data.lessons_learned,
    )
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("/breach/incidents/{incident_id}/assessment", response_model=BreachAssessmentResponse)
async def create_breach_assessment(
    incident_id: UUID,
    data: BreachAssessmentCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
):
    """Create a breach risk assessment."""
    service = BreachService(db, tenant_id)
    assessment = await service.create_breach_assessment(
        incident_id=incident_id,
        assessed_by=user_id,
        factor1_phi_nature=data.factor1_phi_nature,
        factor1_phi_types=data.factor1_phi_types,
        factor1_identifiability=data.factor1_identifiability,
        factor1_score=data.factor1_score,
        factor2_recipient_description=data.factor2_recipient_description,
        factor2_recipient_type=data.factor2_recipient_type,
        factor2_obligation_to_protect=data.factor2_obligation_to_protect,
        factor2_score=data.factor2_score,
        factor3_phi_accessed=data.factor3_phi_accessed,
        factor3_access_evidence=data.factor3_access_evidence,
        factor3_score=data.factor3_score,
        factor4_mitigation_actions=data.factor4_mitigation_actions,
        factor4_assurances_obtained=data.factor4_assurances_obtained,
        factor4_phi_returned_destroyed=data.factor4_phi_returned_destroyed,
        factor4_score=data.factor4_score,
        low_probability_exception=data.low_probability_exception,
        exception_justification=data.exception_justification,
    )
    return assessment


@router.post("/breach/incidents/{incident_id}/notifications", response_model=BreachNotificationResponse)
async def create_breach_notification(
    incident_id: UUID,
    data: BreachNotificationCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
):
    """Create a breach notification."""
    service = BreachService(db, tenant_id)
    notification = await service.create_notification(
        incident_id=incident_id,
        notification_type=data.notification_type,
        recipient_type=data.recipient_type,
        recipient_name=data.recipient_name,
        recipient_email=data.recipient_email,
        recipient_address=data.recipient_address,
        patient_id=data.patient_id,
        notification_content=data.notification_content,
        letter_template_used=data.letter_template_used,
        delivery_method=data.delivery_method,
        scheduled_date=data.scheduled_date,
        created_by=user_id,
    )
    return notification


@router.get("/breach/statistics")
async def get_breach_statistics(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Get breach statistics for dashboard."""
    service = BreachService(db, tenant_id)
    return await service.get_breach_statistics()


# ============================================================================
# BAA Management Endpoints
# ============================================================================

@router.post("/baa", response_model=BusinessAssociateAgreementResponse)
async def create_baa(
    data: BusinessAssociateAgreementCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
):
    """Create a Business Associate Agreement."""
    service = BAAService(db, tenant_id)
    baa = await service.create_baa(
        baa_type=data.baa_type,
        counterparty_name=data.counterparty_name,
        counterparty_type=data.counterparty_type,
        counterparty_address=data.counterparty_address,
        counterparty_contact_name=data.counterparty_contact_name,
        counterparty_contact_email=data.counterparty_contact_email,
        counterparty_contact_phone=data.counterparty_contact_phone,
        services_description=data.services_description,
        phi_categories_covered=data.phi_categories_covered,
        template_used=data.template_used,
        effective_date=data.effective_date,
        expiration_date=data.expiration_date,
        auto_renew=data.auto_renew,
        renewal_term_months=data.renewal_term_months,
        parent_baa_id=data.parent_baa_id,
        created_by=user_id,
    )
    return baa


@router.get("/baa", response_model=List[BusinessAssociateAgreementResponse])
async def list_baas(
    baa_type: Optional[BAAType] = None,
    status: Optional[BAAStatus] = None,
    counterparty_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """List Business Associate Agreements."""
    service = BAAService(db, tenant_id)
    return await service.list_baas(baa_type, status, counterparty_name)


@router.get("/baa/expiring", response_model=List[BusinessAssociateAgreementResponse])
async def get_expiring_baas(
    days_ahead: int = 90,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Get BAAs expiring within specified days."""
    service = BAAService(db, tenant_id)
    return await service.get_expiring_baas(days_ahead)


@router.post("/baa/{baa_id}/execute", response_model=BusinessAssociateAgreementResponse)
async def execute_baa(
    baa_id: UUID,
    data: BAAExecute,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Execute (sign) a BAA."""
    service = BAAService(db, tenant_id)
    baa = await service.execute_baa(
        baa_id=baa_id,
        our_signatory_name=data.our_signatory_name,
        our_signatory_title=data.our_signatory_title,
        counterparty_signatory_name=data.counterparty_signatory_name,
        counterparty_signatory_title=data.counterparty_signatory_title,
        execution_date=data.execution_date,
        effective_date=data.effective_date,
        document_url=data.document_url,
    )
    if not baa:
        raise HTTPException(status_code=404, detail="BAA not found")
    return baa


@router.post("/baa/{baa_id}/terminate", response_model=BusinessAssociateAgreementResponse)
async def terminate_baa(
    baa_id: UUID,
    data: BAATerminate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Terminate a BAA."""
    service = BAAService(db, tenant_id)
    baa = await service.terminate_baa(baa_id, data.termination_date, data.termination_reason)
    if not baa:
        raise HTTPException(status_code=404, detail="BAA not found")
    return baa


@router.post("/baa/templates", response_model=BAATemplateResponse)
async def create_baa_template(
    data: BAATemplateCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
):
    """Create a BAA template."""
    service = BAAService(db, tenant_id)
    template = await service.create_template(
        name=data.name,
        description=data.description,
        template_type=data.template_type,
        template_content=data.template_content,
        variable_fields=data.variable_fields,
        version=data.version,
        is_default=data.is_default,
        created_by=user_id,
    )
    return template


@router.get("/baa/templates", response_model=List[BAATemplateResponse])
async def list_baa_templates(
    template_type: Optional[BAAType] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """List BAA templates."""
    service = BAAService(db, tenant_id)
    return await service.list_templates(template_type, active_only)


@router.get("/baa/compliance-report")
async def get_baa_compliance_report(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Get BAA compliance report."""
    service = BAAService(db, tenant_id)
    return await service.get_baa_compliance_report()


# ============================================================================
# Training Endpoints
# ============================================================================

@router.post("/training/modules", response_model=TrainingModuleResponse)
async def create_training_module(
    data: TrainingModuleCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
):
    """Create a training module."""
    service = TrainingService(db, tenant_id)
    module = await service.create_training_module(
        name=data.name,
        description=data.description,
        training_type=data.training_type,
        content_url=data.content_url,
        duration_minutes=data.duration_minutes,
        passing_score=data.passing_score,
        required_for_roles=data.required_for_roles,
        required_for_all=data.required_for_all,
        required_for_phi_access=data.required_for_phi_access,
        recurrence_months=data.recurrence_months,
        version=data.version,
        effective_date=data.effective_date,
        created_by=user_id,
    )
    return module


@router.get("/training/modules", response_model=List[TrainingModuleResponse])
async def list_training_modules(
    training_type: Optional[TrainingType] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """List training modules."""
    service = TrainingService(db, tenant_id)
    return await service.list_modules(training_type, active_only)


@router.post("/training/assignments", response_model=TrainingAssignmentResponse)
async def create_training_assignment(
    data: TrainingAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
):
    """Assign training to a user."""
    service = TrainingService(db, tenant_id)
    assignment = await service.assign_training(
        module_id=data.module_id,
        user_id=data.user_id,
        due_date=data.due_date,
        user_name=data.user_name,
        user_email=data.user_email,
        user_role=data.user_role,
        assigned_by=user_id,
    )
    return assignment


@router.get("/training/assignments/user/{user_id}", response_model=List[TrainingAssignmentResponse])
async def get_user_training_assignments(
    user_id: UUID,
    status: Optional[TrainingStatus] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Get training assignments for a user."""
    service = TrainingService(db, tenant_id)
    return await service.get_user_assignments(user_id, status)


@router.post("/training/assignments/{assignment_id}/start")
async def start_training(
    assignment_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Start training."""
    service = TrainingService(db, tenant_id)
    assignment = await service.start_training(assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


@router.post("/training/assignments/{assignment_id}/complete")
async def complete_training(
    assignment_id: UUID,
    data: TrainingComplete,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Complete training with score."""
    service = TrainingService(db, tenant_id)
    assignment = await service.complete_training(assignment_id, data.score)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


@router.get("/training/assignments/overdue", response_model=List[TrainingAssignmentResponse])
async def get_overdue_trainings(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Get overdue training assignments."""
    service = TrainingService(db, tenant_id)
    return await service.get_overdue_assignments()


@router.post("/training/policies", response_model=PolicyDocumentResponse)
async def create_policy_document(
    data: PolicyDocumentCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
):
    """Create a policy document."""
    service = TrainingService(db, tenant_id)
    policy = await service.create_policy(
        title=data.title,
        policy_number=data.policy_number,
        category=data.category,
        content=data.content,
        summary=data.summary,
        version=data.version,
        effective_date=data.effective_date,
        review_date=data.review_date,
        requires_acknowledgment=data.requires_acknowledgment,
        required_for_roles=data.required_for_roles,
        required_for_all=data.required_for_all,
        created_by=user_id,
    )
    return policy


@router.get("/training/policies", response_model=List[PolicyDocumentResponse])
async def list_policy_documents(
    category: Optional[str] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """List policy documents."""
    service = TrainingService(db, tenant_id)
    return await service.list_policies(category, active_only)


@router.post("/training/policies/{policy_id}/acknowledge")
async def acknowledge_policy(
    policy_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
    request: Request = None,
):
    """Acknowledge a policy."""
    service = TrainingService(db, tenant_id)
    source_ip = request.client.host if request else None
    user_agent = request.headers.get("User-Agent") if request else None

    acknowledgment = await service.acknowledge_policy(
        policy_id=policy_id,
        user_id=user_id,
        signature_ip=source_ip,
        signature_user_agent=user_agent,
    )
    return acknowledgment


@router.get("/training/compliance-report")
async def get_training_compliance_report(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Get training compliance report."""
    service = TrainingService(db, tenant_id)
    return await service.get_training_compliance_report()


# ============================================================================
# Risk Assessment Endpoints
# ============================================================================

@router.post("/risk/assessments", response_model=RiskAssessmentResponse)
async def create_risk_assessment(
    data: RiskAssessmentCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
):
    """Create a risk assessment."""
    service = RiskService(db, tenant_id)
    assessment = await service.create_assessment(
        name=data.name,
        description=data.description,
        assessment_type=data.assessment_type,
        scope_description=data.scope_description,
        systems_in_scope=data.systems_in_scope,
        departments_in_scope=data.departments_in_scope,
        start_date=data.start_date,
        target_completion_date=data.target_completion_date,
        lead_assessor_id=user_id,
        methodology=data.methodology,
        methodology_version=data.methodology_version,
        assessment_team=data.assessment_team,
        created_by=user_id,
    )
    return assessment


@router.get("/risk/assessments", response_model=List[RiskAssessmentResponse])
async def list_risk_assessments(
    status: Optional[str] = None,
    assessment_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """List risk assessments."""
    service = RiskService(db, tenant_id)
    return await service.list_assessments(status, assessment_type)


@router.get("/risk/assessments/{assessment_id}", response_model=RiskAssessmentResponse)
async def get_risk_assessment(
    assessment_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Get a risk assessment."""
    service = RiskService(db, tenant_id)
    assessment = await service.get_assessment(assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment


@router.post("/risk/assessments/{assessment_id}/complete", response_model=RiskAssessmentResponse)
async def complete_risk_assessment(
    assessment_id: UUID,
    data: RiskAssessmentComplete,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Complete a risk assessment."""
    service = RiskService(db, tenant_id)
    assessment = await service.complete_assessment(
        assessment_id,
        data.executive_summary,
        data.overall_risk_level,
        data.report_url,
    )
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment


@router.post("/risk/items", response_model=RiskItemResponse)
async def create_risk_item(
    data: RiskItemCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Create a risk item."""
    service = RiskService(db, tenant_id)
    risk_item = await service.create_risk_item(
        assessment_id=data.assessment_id,
        risk_number=data.risk_number,
        title=data.title,
        description=data.description,
        category=data.category,
        likelihood=data.likelihood,
        impact=data.impact,
        safeguard_type=data.safeguard_type,
        hipaa_reference=data.hipaa_reference,
        threat_source=data.threat_source,
        vulnerability=data.vulnerability,
        existing_controls=data.existing_controls,
        control_effectiveness=data.control_effectiveness,
        evidence=data.evidence,
        affected_assets=data.affected_assets,
    )
    return risk_item


@router.get("/risk/items", response_model=List[RiskItemResponse])
async def list_risk_items(
    assessment_id: Optional[UUID] = None,
    risk_level: Optional[RiskLevel] = None,
    category: Optional[RiskCategory] = None,
    status: Optional[RemediationStatus] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """List risk items."""
    service = RiskService(db, tenant_id)
    return await service.list_risk_items(assessment_id, risk_level, category, status)


@router.post("/risk/remediation-plans", response_model=RemediationPlanResponse)
async def create_remediation_plan(
    data: RemediationPlanCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
):
    """Create a remediation plan."""
    service = RiskService(db, tenant_id)
    plan = await service.create_remediation_plan(
        risk_id=data.risk_id,
        title=data.title,
        description=data.description,
        owner_id=data.owner_id,
        owner_name=data.owner_name,
        planned_start_date=data.planned_start_date,
        target_completion_date=data.target_completion_date,
        estimated_cost=data.estimated_cost,
        verification_required=data.verification_required,
        created_by=user_id,
    )
    return plan


@router.get("/risk/remediation-plans", response_model=List[RemediationPlanResponse])
async def list_remediation_plans(
    status: Optional[RemediationStatus] = None,
    owner_id: Optional[UUID] = None,
    overdue_only: bool = False,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """List remediation plans."""
    service = RiskService(db, tenant_id)
    return await service.list_remediation_plans(status, owner_id, overdue_only)


@router.patch("/risk/remediation-plans/{plan_id}", response_model=RemediationPlanResponse)
async def update_remediation_progress(
    plan_id: UUID,
    data: RemediationUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Update remediation plan progress."""
    service = RiskService(db, tenant_id)
    plan = await service.update_remediation_progress(
        plan_id,
        status=data.status,
        percent_complete=data.percent_complete,
        actual_start_date=data.actual_start_date,
        actual_cost=data.actual_cost,
        implementation_notes=data.implementation_notes,
    )
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.post("/risk/remediation-plans/{plan_id}/verify", response_model=RemediationPlanResponse)
async def verify_remediation(
    plan_id: UUID,
    data: RemediationVerify,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
):
    """Verify remediation completion."""
    service = RiskService(db, tenant_id)
    plan = await service.verify_remediation(plan_id, user_id, data.verification_evidence)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.post("/risk/remediation-plans/{plan_id}/accept-risk", response_model=RemediationPlanResponse)
async def accept_risk(
    plan_id: UUID,
    data: RiskAcceptance,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
):
    """Accept risk instead of remediating."""
    service = RiskService(db, tenant_id)
    plan = await service.accept_risk(
        plan_id,
        user_id,
        data.risk_acceptance_reason,
        data.risk_acceptance_expiration,
    )
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.get("/risk/register", response_model=List[RiskRegisterResponse])
async def list_risk_register(
    risk_level: Optional[RiskLevel] = None,
    category: Optional[RiskCategory] = None,
    status: Optional[RemediationStatus] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """List risk register entries."""
    service = RiskService(db, tenant_id)
    return await service.list_risk_register(risk_level, category, status, active_only)


@router.get("/risk/dashboard")
async def get_risk_dashboard(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Get risk dashboard statistics."""
    service = RiskService(db, tenant_id)
    return await service.get_risk_dashboard()


@router.get("/risk/assessments/{assessment_id}/report")
async def get_risk_assessment_report(
    assessment_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Generate risk assessment report."""
    service = RiskService(db, tenant_id)
    return await service.generate_risk_report(assessment_id)


# ============================================================================
# Compliance Dashboard
# ============================================================================

@router.get("/dashboard", response_model=ComplianceDashboard)
async def get_compliance_dashboard(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Get comprehensive HIPAA compliance dashboard."""
    audit_service = AuditService(db, tenant_id)
    access_service = AccessControlService(db, tenant_id)
    retention_service = RetentionService(db, tenant_id)
    breach_service = BreachService(db, tenant_id)
    baa_service = BAAService(db, tenant_id)
    training_service = TrainingService(db, tenant_id)
    risk_service = RiskService(db, tenant_id)

    # Get various statistics
    from datetime import datetime, timedelta
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    audit_stats = await audit_service.get_audit_statistics(today_start, today_end)
    anomaly_stats = await access_service.get_anomaly_statistics()
    breach_stats = await breach_service.get_breach_statistics()
    baa_report = await baa_service.get_baa_compliance_report()
    training_report = await training_service.get_training_compliance_report()
    risk_dashboard = await risk_service.get_risk_dashboard()

    # Get counts
    pending_requests = await access_service.list_pending_access_requests()
    active_holds = await retention_service.list_legal_holds(active_only=True)
    pending_roa = await retention_service.list_pending_roa_requests()
    overdue_trainings = await training_service.get_overdue_assignments()

    return ComplianceDashboard(
        # Audit metrics
        total_audit_logs_today=audit_stats.get("total_events", 0),
        audit_logs_by_action=audit_stats.get("events_by_action", {}),
        audit_logs_by_outcome=audit_stats.get("events_by_outcome", {}),
        # Access metrics
        active_treatment_relationships=0,  # Would need additional query
        pending_access_requests=len(pending_requests),
        open_anomalies=anomaly_stats.get("total_open", 0),
        anomalies_by_severity=anomaly_stats.get("by_severity", {}),
        # Retention metrics
        records_pending_destruction=0,  # Would need additional query
        active_legal_holds=len(active_holds),
        pending_roa_requests=len(pending_roa),
        # Breach metrics
        active_breach_investigations=breach_stats.get("active_investigations", 0),
        breaches_by_status=breach_stats.get("by_status", {}),
        # BAA metrics
        active_baas=baa_report.get("total_active_baas", 0),
        baas_expiring_soon=baa_report.get("expiring_within_90_days", 0),
        pending_baa_signatures=baa_report.get("pending_signatures", 0),
        # Training metrics
        overdue_trainings=len(overdue_trainings),
        training_completion_rate=training_report.get("completion_rate", 0.0),
        pending_policy_acknowledgments=0,  # Would need additional query
        # Risk metrics
        open_risk_items=risk_dashboard.get("total_open_risks", 0),
        risks_by_level=risk_dashboard.get("risks_by_level", {}),
        overdue_remediations=risk_dashboard.get("overdue_remediations", 0),
    )
