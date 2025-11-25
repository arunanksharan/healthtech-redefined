"""
Clinical Decision Support (CDS) Router

FastAPI router for CDS endpoints:
- Drug interaction checking
- Drug-allergy alerts
- Clinical guidelines
- Quality measures and care gaps
- CDS Hooks
- Alert management
- AI diagnostic support

EPIC-020: Clinical Decision Support
"""

from datetime import date
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db

# Import schemas
from modules.cds.schemas import (
    # Drug Interactions
    MedicationInput,
    MedicationListInput,
    DrugInteractionRuleCreate,
    DrugInteractionRuleUpdate,
    DrugInteractionRuleResponse,
    InteractionCheckResponse,
    # Alerts
    CDSAlertCreate,
    CDSAlertResponse,
    AlertAcknowledge,
    AlertOverrideCreate,
    AlertOverrideResponse,
    AlertDismiss,
    AlertConfigurationCreate,
    AlertConfigurationUpdate,
    AlertConfigurationResponse,
    AlertAnalyticsResponse,
    # Guidelines
    GuidelineCreate,
    GuidelineUpdate,
    GuidelineResponse,
    GuidelineSearchRequest,
    GuidelineRecommendation,
    GuidelineAccessLog,
    # Quality Measures
    QualityMeasureCreate,
    QualityMeasureUpdate,
    QualityMeasureResponse,
    MeasureEvaluationRequest,
    MeasureEvaluationResponse,
    PatientMeasureResponse,
    CareGapCreate,
    CareGapUpdate,
    CareGapResponse,
    CareGapClose,
    PatientCareGapSummary,
    # CDS Hooks
    CDSServiceCreate,
    CDSServiceUpdate,
    CDSServiceResponse,
    CDSHookRequest,
    CDSHookResponse,
    CDSCardInteraction,
    # Diagnostics
    DiagnosticSessionCreate,
    DiagnosticSessionUpdate,
    DiagnosticSessionResponse,
    DifferentialDiagnosisRequest,
    DifferentialDiagnosisResponse,
    DiagnosisFeedback,
    # Dashboard
    CDSDashboard,
    OrganizationCDSMetrics,
    DrugDatabaseStats,
    # Enums
    InteractionSeverity,
    InteractionType,
    AlertStatus,
    GuidelineCategory,
    GuidelineSource,
    MeasureType,
    CareGapStatus,
    CareGapPriority,
    CDSHookType,
)

# Import services
from modules.cds.services import (
    DrugInteractionService,
    AllergyService,
    GuidelineService,
    QualityMeasureService,
    CDSHooksService,
    AlertManagementService,
    DiagnosticService,
)

router = APIRouter(prefix="/cds", tags=["Clinical Decision Support"])


# Dependency to get tenant_id (simplified - would come from auth in production)
async def get_tenant_id() -> UUID:
    # In production, this would extract tenant_id from JWT token
    return UUID("00000000-0000-0000-0000-000000000001")


async def get_provider_id() -> UUID:
    # In production, this would extract provider_id from JWT token
    return UUID("00000000-0000-0000-0000-000000000002")


# ============================================================================
# DRUG INTERACTION ENDPOINTS
# ============================================================================

@router.post("/interactions/check", response_model=InteractionCheckResponse)
async def check_drug_interactions(
    data: MedicationListInput,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Check for drug-drug, drug-allergy, and drug-disease interactions."""
    service = DrugInteractionService(db, tenant_id)

    # Get patient allergies and conditions from FHIR
    # This would integrate with FHIR service in production
    patient_allergies = []  # Would fetch from AllergyIntolerance
    patient_conditions = []  # Would fetch from Condition

    result = await service.check_interactions(
        medications=data.medications,
        patient_id=data.patient_id,
        current_medications=None,  # Would fetch from MedicationStatement
        patient_conditions=patient_conditions if data.include_conditions else None,
    )

    # Check allergies if requested
    if data.include_allergies and patient_allergies:
        allergy_service = AllergyService(db, tenant_id)
        allergy_alerts = await allergy_service.check_allergies(
            medications=data.medications,
            patient_allergies=patient_allergies,
        )
        result.drug_allergy_alerts = allergy_alerts
        result.total_alerts += len(allergy_alerts)

    return result


@router.post("/interactions/rules", response_model=DrugInteractionRuleResponse)
async def create_interaction_rule(
    data: DrugInteractionRuleCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Create a new drug interaction rule."""
    service = DrugInteractionService(db, tenant_id)
    rule = await service.add_interaction_rule(
        drug1_rxnorm=data.drug1_rxnorm,
        drug2_rxnorm=data.drug2_rxnorm,
        severity=data.severity,
        description=data.description,
        drug1_name=data.drug1_name,
        drug2_name=data.drug2_name,
        drug_class1=data.drug_class1,
        drug_class2=data.drug_class2,
        is_class_interaction=data.is_class_interaction,
        clinical_effect=data.clinical_effect,
        mechanism=data.mechanism,
        recommendation=data.recommendation,
        management=data.management,
        evidence_level=data.evidence_level,
        references=data.references,
    )
    await db.commit()
    return rule


@router.get("/interactions/rules", response_model=List[DrugInteractionRuleResponse])
async def list_interaction_rules(
    severity: Optional[InteractionSeverity] = None,
    drug_rxnorm: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """List drug interaction rules."""
    service = DrugInteractionService(db, tenant_id)
    rules = await service.list_interaction_rules(
        severity=severity,
        drug_rxnorm=drug_rxnorm,
        skip=skip,
        limit=limit,
    )
    return rules


@router.patch("/interactions/rules/{rule_id}", response_model=DrugInteractionRuleResponse)
async def update_interaction_rule(
    rule_id: UUID,
    data: DrugInteractionRuleUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Update a drug interaction rule."""
    service = DrugInteractionService(db, tenant_id)
    rule = await service.update_interaction_rule(rule_id, **data.dict(exclude_unset=True))
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    await db.commit()
    return rule


# ============================================================================
# CDS ALERT ENDPOINTS
# ============================================================================

@router.post("/alerts", response_model=CDSAlertResponse)
async def create_alert(
    data: CDSAlertCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Create a CDS alert."""
    service = AlertManagementService(db, tenant_id)
    alert = await service.create_alert(data)
    await db.commit()
    return alert


@router.get("/alerts", response_model=List[CDSAlertResponse])
async def list_alerts(
    patient_id: Optional[UUID] = None,
    provider_id: Optional[UUID] = None,
    encounter_id: Optional[UUID] = None,
    status: Optional[AlertStatus] = None,
    severity: Optional[InteractionSeverity] = None,
    alert_type: Optional[InteractionType] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """List CDS alerts."""
    service = AlertManagementService(db, tenant_id)
    alerts = await service.list_alerts(
        patient_id=patient_id,
        provider_id=provider_id,
        encounter_id=encounter_id,
        status=status,
        severity=severity,
        alert_type=alert_type,
        skip=skip,
        limit=limit,
    )
    return alerts


@router.get("/alerts/active/{patient_id}", response_model=List[CDSAlertResponse])
async def get_active_alerts(
    patient_id: UUID,
    encounter_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Get active alerts for a patient."""
    service = AlertManagementService(db, tenant_id)
    alerts = await service.get_active_alerts(patient_id, encounter_id)
    return alerts


@router.get("/alerts/{alert_id}", response_model=CDSAlertResponse)
async def get_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Get a specific alert."""
    service = AlertManagementService(db, tenant_id)
    alert = await service.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/alerts/{alert_id}/acknowledge", response_model=CDSAlertResponse)
async def acknowledge_alert(
    alert_id: UUID,
    data: AlertAcknowledge,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Acknowledge an alert."""
    service = AlertManagementService(db, tenant_id)
    alert = await service.acknowledge_alert(alert_id, data)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    await db.commit()
    return alert


@router.post("/alerts/{alert_id}/override", response_model=AlertOverrideResponse)
async def override_alert(
    alert_id: UUID,
    data: AlertOverrideCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Override an alert with documentation."""
    service = AlertManagementService(db, tenant_id)
    override = await service.override_alert(alert_id, data)
    if not override:
        raise HTTPException(status_code=404, detail="Alert not found")
    await db.commit()
    return override


@router.post("/alerts/{alert_id}/dismiss", response_model=CDSAlertResponse)
async def dismiss_alert(
    alert_id: UUID,
    data: AlertDismiss,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Dismiss an alert."""
    service = AlertManagementService(db, tenant_id)
    try:
        alert = await service.dismiss_alert(alert_id, data.dismissed_by, data.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    await db.commit()
    return alert


@router.post("/alerts/{alert_id}/displayed")
async def mark_alert_displayed(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Mark alert as displayed to user."""
    service = AlertManagementService(db, tenant_id)
    await service.mark_alert_displayed(alert_id)
    await db.commit()
    return {"status": "ok"}


# Alert Configuration

@router.post("/alerts/configurations", response_model=AlertConfigurationResponse)
async def create_alert_configuration(
    data: AlertConfigurationCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    provider_id: UUID = Depends(get_provider_id),
):
    """Create alert configuration."""
    service = AlertManagementService(db, tenant_id)
    config = await service.create_configuration(data, provider_id)
    await db.commit()
    return config


@router.get("/alerts/configurations", response_model=List[AlertConfigurationResponse])
async def list_alert_configurations(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """List alert configurations."""
    service = AlertManagementService(db, tenant_id)
    configs = await service.list_configurations()
    return configs


@router.patch("/alerts/configurations/{config_id}", response_model=AlertConfigurationResponse)
async def update_alert_configuration(
    config_id: UUID,
    data: AlertConfigurationUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Update alert configuration."""
    service = AlertManagementService(db, tenant_id)
    config = await service.update_configuration(config_id, data)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    await db.commit()
    return config


# Alert Analytics

@router.get("/alerts/analytics", response_model=List[AlertAnalyticsResponse])
async def get_alert_analytics(
    start_date: date,
    end_date: date,
    alert_type: Optional[InteractionType] = None,
    severity: Optional[InteractionSeverity] = None,
    provider_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Get alert analytics for a period."""
    service = AlertManagementService(db, tenant_id)
    analytics = await service.get_analytics(
        start_date=start_date,
        end_date=end_date,
        alert_type=alert_type,
        severity=severity,
        provider_id=provider_id,
    )
    return analytics


@router.get("/alerts/override-patterns")
async def get_override_patterns(
    start_date: date,
    end_date: date,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Analyze override patterns for optimization."""
    service = AlertManagementService(db, tenant_id)
    patterns = await service.get_override_patterns(start_date, end_date)
    return patterns


@router.get("/alerts/effectiveness-report")
async def get_alert_effectiveness_report(
    start_date: date,
    end_date: date,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Get alert effectiveness report."""
    service = AlertManagementService(db, tenant_id)
    report = await service.get_alert_effectiveness_report(start_date, end_date)
    return report


# ============================================================================
# CLINICAL GUIDELINE ENDPOINTS
# ============================================================================

@router.post("/guidelines", response_model=GuidelineResponse)
async def create_guideline(
    data: GuidelineCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Create a clinical guideline."""
    service = GuidelineService(db, tenant_id)
    guideline = await service.create_guideline(data)
    await db.commit()
    return guideline


@router.get("/guidelines", response_model=List[GuidelineResponse])
async def list_guidelines(
    category: Optional[GuidelineCategory] = None,
    source: Optional[GuidelineSource] = None,
    condition: Optional[str] = None,
    is_featured: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """List clinical guidelines."""
    service = GuidelineService(db, tenant_id)
    guidelines = await service.list_guidelines(
        category=category,
        source=source,
        condition=condition,
        is_featured=is_featured,
        skip=skip,
        limit=limit,
    )
    return guidelines


@router.post("/guidelines/search", response_model=List[GuidelineResponse])
async def search_guidelines(
    request: GuidelineSearchRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Search guidelines by query and filters."""
    service = GuidelineService(db, tenant_id)
    guidelines = await service.search_guidelines(request)
    return guidelines


@router.get("/guidelines/recommendations", response_model=List[GuidelineRecommendation])
async def get_guideline_recommendations(
    conditions: List[str] = Query(...),
    patient_age: Optional[int] = None,
    patient_gender: Optional[str] = None,
    max_recommendations: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Get guideline recommendations for patient context."""
    service = GuidelineService(db, tenant_id)
    recommendations = await service.get_recommendations_for_context(
        patient_conditions=conditions,
        patient_age=patient_age,
        patient_gender=patient_gender,
        max_recommendations=max_recommendations,
    )
    return recommendations


@router.get("/guidelines/{guideline_id}", response_model=GuidelineResponse)
async def get_guideline(
    guideline_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Get a specific guideline."""
    service = GuidelineService(db, tenant_id)
    guideline = await service.get_guideline(guideline_id)
    if not guideline:
        raise HTTPException(status_code=404, detail="Guideline not found")
    return guideline


@router.patch("/guidelines/{guideline_id}", response_model=GuidelineResponse)
async def update_guideline(
    guideline_id: UUID,
    data: GuidelineUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Update a guideline."""
    service = GuidelineService(db, tenant_id)
    guideline = await service.update_guideline(guideline_id, data)
    if not guideline:
        raise HTTPException(status_code=404, detail="Guideline not found")
    await db.commit()
    return guideline


@router.post("/guidelines/{guideline_id}/access")
async def log_guideline_access(
    guideline_id: UUID,
    data: GuidelineAccessLog,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Log guideline access."""
    service = GuidelineService(db, tenant_id)
    access = await service.log_access(
        guideline_id=guideline_id,
        provider_id=data.provider_id,
        patient_id=data.patient_id,
        encounter_id=data.encounter_id,
        access_context=data.access_context,
        was_helpful=data.was_helpful,
        feedback=data.feedback,
    )
    await db.commit()
    return {"access_id": access.id}


# ============================================================================
# QUALITY MEASURE ENDPOINTS
# ============================================================================

@router.post("/measures", response_model=QualityMeasureResponse)
async def create_measure(
    data: QualityMeasureCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Create a quality measure."""
    service = QualityMeasureService(db, tenant_id)
    measure = await service.create_measure(data)
    await db.commit()
    return measure


@router.get("/measures", response_model=List[QualityMeasureResponse])
async def list_measures(
    measure_type: Optional[MeasureType] = None,
    category: Optional[str] = None,
    domain: Optional[str] = None,
    is_required: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """List quality measures."""
    service = QualityMeasureService(db, tenant_id)
    measures = await service.list_measures(
        measure_type=measure_type,
        category=category,
        domain=domain,
        is_required=is_required,
        skip=skip,
        limit=limit,
    )
    return measures


@router.get("/measures/{measure_id}", response_model=QualityMeasureResponse)
async def get_measure(
    measure_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Get a specific measure."""
    service = QualityMeasureService(db, tenant_id)
    measure = await service.get_measure(measure_id)
    if not measure:
        raise HTTPException(status_code=404, detail="Measure not found")
    return measure


@router.post("/measures/evaluate", response_model=MeasureEvaluationResponse)
async def evaluate_measures(
    request: MeasureEvaluationRequest,
    patient_data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Evaluate quality measures for a patient."""
    service = QualityMeasureService(db, tenant_id)
    result = await service.evaluate_patient_measures(request, patient_data)
    await db.commit()
    return result


@router.get("/measures/{measure_id}/performance")
async def get_measure_performance(
    measure_id: UUID,
    period_start: date,
    period_end: date,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Get measure performance metrics."""
    service = QualityMeasureService(db, tenant_id)
    performance = await service.get_measure_performance(measure_id, period_start, period_end)
    return performance


# Care Gaps

@router.post("/care-gaps", response_model=CareGapResponse)
async def create_care_gap(
    data: CareGapCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Create a care gap."""
    service = QualityMeasureService(db, tenant_id)
    gap = await service.create_care_gap(data)
    await db.commit()
    return gap


@router.get("/care-gaps/patient/{patient_id}", response_model=PatientCareGapSummary)
async def get_patient_care_gaps(
    patient_id: UUID,
    status: Optional[CareGapStatus] = None,
    priority: Optional[CareGapPriority] = None,
    include_closed: bool = False,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Get care gaps for a patient."""
    service = QualityMeasureService(db, tenant_id)
    summary = await service.get_patient_care_gaps(
        patient_id=patient_id,
        status=status,
        priority=priority,
        include_closed=include_closed,
    )
    return summary


@router.get("/care-gaps/{gap_id}", response_model=CareGapResponse)
async def get_care_gap(
    gap_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Get a specific care gap."""
    service = QualityMeasureService(db, tenant_id)
    gap = await service.get_care_gap(gap_id)
    if not gap:
        raise HTTPException(status_code=404, detail="Care gap not found")
    return gap


@router.patch("/care-gaps/{gap_id}", response_model=CareGapResponse)
async def update_care_gap(
    gap_id: UUID,
    data: CareGapUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Update a care gap."""
    service = QualityMeasureService(db, tenant_id)
    gap = await service.update_care_gap(gap_id, data)
    if not gap:
        raise HTTPException(status_code=404, detail="Care gap not found")
    await db.commit()
    return gap


@router.post("/care-gaps/{gap_id}/close", response_model=CareGapResponse)
async def close_care_gap(
    gap_id: UUID,
    data: CareGapClose,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Close a care gap."""
    service = QualityMeasureService(db, tenant_id)
    gap = await service.close_care_gap(gap_id, data.closed_by_provider_id, data.closure_evidence)
    if not gap:
        raise HTTPException(status_code=404, detail="Care gap not found")
    await db.commit()
    return gap


@router.post("/care-gaps/auto-detect/{patient_id}")
async def auto_detect_care_gaps(
    patient_id: UUID,
    patient_data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Automatically detect care gaps for a patient."""
    service = QualityMeasureService(db, tenant_id)
    gaps = await service.auto_detect_care_gaps(patient_id, patient_data)
    await db.commit()
    return {"detected_gaps": len(gaps)}


# ============================================================================
# CDS HOOKS ENDPOINTS
# ============================================================================

@router.get("/cds-services")
async def get_cds_discovery(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """CDS Hooks discovery endpoint."""
    service = CDSHooksService(db, tenant_id)
    discovery = await service.get_discovery_response()
    return discovery


@router.post("/cds-services", response_model=CDSServiceResponse)
async def register_cds_service(
    data: CDSServiceCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Register a CDS service."""
    service = CDSHooksService(db, tenant_id)
    cds_service = await service.register_service(data)
    await db.commit()
    return cds_service


@router.get("/cds-services/list", response_model=List[CDSServiceResponse])
async def list_cds_services(
    hook: Optional[CDSHookType] = None,
    is_enabled: bool = True,
    is_internal: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """List registered CDS services."""
    service = CDSHooksService(db, tenant_id)
    services = await service.list_services(
        hook=hook,
        is_enabled=is_enabled,
        is_internal=is_internal,
    )
    return services


@router.patch("/cds-services/{service_id}", response_model=CDSServiceResponse)
async def update_cds_service(
    service_id: str,
    data: CDSServiceUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Update a CDS service."""
    service = CDSHooksService(db, tenant_id)
    cds_service = await service.update_service(service_id, data)
    if not cds_service:
        raise HTTPException(status_code=404, detail="Service not found")
    await db.commit()
    return cds_service


@router.delete("/cds-services/{service_id}")
async def delete_cds_service(
    service_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Delete a CDS service."""
    service = CDSHooksService(db, tenant_id)
    deleted = await service.delete_service(service_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Service not found")
    await db.commit()
    return {"status": "deleted"}


@router.post("/cds-services/{service_id}/{hook_type}", response_model=CDSHookResponse)
async def invoke_cds_hook(
    service_id: str,
    hook_type: CDSHookType,
    request: CDSHookRequest,
    patient_id: UUID = Query(...),
    provider_id: Optional[UUID] = None,
    encounter_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Invoke a CDS hook."""
    service = CDSHooksService(db, tenant_id)
    response = await service.invoke_hook(
        hook_type=hook_type,
        context=request.context,
        patient_id=patient_id,
        provider_id=provider_id,
        encounter_id=encounter_id,
        prefetch_data=request.prefetch,
    )
    await db.commit()
    return response


@router.post("/cds-services/cards/{card_id}/interaction")
async def record_card_interaction(
    card_id: UUID,
    data: CDSCardInteraction,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Record interaction with a CDS card."""
    service = CDSHooksService(db, tenant_id)
    await service.record_card_interaction(
        card_id=card_id,
        was_accepted=data.was_accepted,
        suggestion_selected=data.suggestion_selected,
        link_clicked=data.link_clicked,
    )
    await db.commit()
    return {"status": "recorded"}


@router.get("/cds-services/{service_id}/health")
async def check_service_health(
    service_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Check CDS service health."""
    service = CDSHooksService(db, tenant_id)
    health = await service.check_service_health(service_id)
    await db.commit()
    return health


# ============================================================================
# DIAGNOSTIC SUPPORT ENDPOINTS
# ============================================================================

@router.post("/diagnostics/sessions", response_model=DiagnosticSessionResponse)
async def create_diagnostic_session(
    data: DiagnosticSessionCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    provider_id: UUID = Depends(get_provider_id),
):
    """Create a diagnostic session."""
    service = DiagnosticService(db, tenant_id)
    session = await service.create_session(data, provider_id)
    await db.commit()
    return session


@router.get("/diagnostics/sessions/{session_id}", response_model=DiagnosticSessionResponse)
async def get_diagnostic_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Get a diagnostic session."""
    service = DiagnosticService(db, tenant_id)
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.patch("/diagnostics/sessions/{session_id}", response_model=DiagnosticSessionResponse)
async def update_diagnostic_session(
    session_id: UUID,
    data: DiagnosticSessionUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Update a diagnostic session."""
    service = DiagnosticService(db, tenant_id)
    session = await service.update_session(session_id, data)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.commit()
    return session


@router.post("/diagnostics/differential", response_model=DifferentialDiagnosisResponse)
async def generate_differential_diagnosis(
    request: DifferentialDiagnosisRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    provider_id: UUID = Depends(get_provider_id),
):
    """Generate differential diagnosis."""
    service = DiagnosticService(db, tenant_id)
    result = await service.generate_differential(request, provider_id)
    await db.commit()
    return result


@router.post("/diagnostics/feedback")
async def submit_diagnostic_feedback(
    data: DiagnosisFeedback,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Submit feedback on a diagnosis suggestion."""
    service = DiagnosticService(db, tenant_id)
    suggestion = await service.submit_feedback(data)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    await db.commit()
    return {"status": "feedback recorded"}


@router.get("/diagnostics/history")
async def get_diagnostic_history(
    patient_id: Optional[UUID] = None,
    provider_id: Optional[UUID] = None,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Get diagnostic session history."""
    service = DiagnosticService(db, tenant_id)
    sessions = await service.get_session_history(
        patient_id=patient_id,
        provider_id=provider_id,
        limit=limit,
    )
    return sessions


@router.get("/diagnostics/model-performance")
async def get_model_performance(
    start_date: date,
    end_date: date,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Get AI model performance metrics."""
    service = DiagnosticService(db, tenant_id)
    performance = await service.get_model_performance(start_date, end_date)
    return performance


# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@router.get("/dashboard/provider", response_model=CDSDashboard)
async def get_provider_dashboard(
    provider_id: UUID,
    period_start: date,
    period_end: date,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Get CDS dashboard for a provider."""
    alert_service = AlertManagementService(db, tenant_id)

    # Get alerts
    alerts = await alert_service.list_alerts(
        provider_id=provider_id,
    )

    # Calculate metrics
    alerts_by_type = {}
    alerts_by_severity = {}
    for alert in alerts:
        alerts_by_type[alert.alert_type.value] = alerts_by_type.get(alert.alert_type.value, 0) + 1
        alerts_by_severity[alert.severity.value] = alerts_by_severity.get(alert.severity.value, 0) + 1

    overridden = sum(1 for a in alerts if a.status == AlertStatus.OVERRIDDEN)
    responded = sum(1 for a in alerts if a.status != AlertStatus.ACTIVE)
    override_rate = (overridden / responded) if responded > 0 else 0

    response_times = [a.response_time_ms for a in alerts if a.response_time_ms]
    avg_response_time = int(sum(response_times) / len(response_times)) if response_times else 0

    return CDSDashboard(
        provider_id=provider_id,
        period_start=period_start,
        period_end=period_end,
        total_alerts=len(alerts),
        alerts_by_type=alerts_by_type,
        alerts_by_severity=alerts_by_severity,
        override_rate=override_rate,
        top_override_reasons=[],  # Would calculate from override records
        avg_response_time_ms=avg_response_time,
        patients_with_care_gaps=0,  # Would calculate
        critical_care_gaps=0,  # Would calculate
    )


@router.get("/dashboard/organization", response_model=OrganizationCDSMetrics)
async def get_organization_dashboard(
    period_start: date,
    period_end: date,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Get organization-level CDS metrics."""
    alert_service = AlertManagementService(db, tenant_id)
    report = await alert_service.get_alert_effectiveness_report(period_start, period_end)

    return OrganizationCDSMetrics(
        tenant_id=tenant_id,
        period_start=period_start,
        period_end=period_end,
        total_alerts=report["total_alerts"],
        unique_patients_alerted=0,  # Would calculate
        override_rate=report["override_rate"],
        potential_adverse_events_prevented=0,  # Would calculate
        quality_measure_performance={},  # Would calculate
        care_gap_closure_rate=0,  # Would calculate
        top_interacting_drug_pairs=[],  # Would calculate
    )


@router.get("/dashboard/drug-database", response_model=DrugDatabaseStats)
async def get_drug_database_stats(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Get drug database statistics."""
    # Would query actual counts
    return DrugDatabaseStats(
        total_drugs=0,
        total_interaction_rules=0,
        total_allergy_mappings=0,
        total_contraindications=0,
        last_updated=datetime.utcnow(),
        sources=["fdb", "medi_span"],
    )
