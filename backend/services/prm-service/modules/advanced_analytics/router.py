"""
Advanced Analytics API Router - EPIC-011
REST API endpoints for the Advanced Analytics Platform.
"""

from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Header

from .service import AdvancedAnalyticsService, get_advanced_analytics_service
from .schemas import (
    # Executive Dashboard
    ExecutiveDashboardRequest,
    ExecutiveDashboardResponse,
    # Clinical Quality
    QualityMeasureRequest,
    QualityMeasuresResponse,
    ProviderScorecardSchema,
    SafetyIndicatorSchema,
    ControlChartRequest,
    ControlChartResponse,
    MeasureCategoryEnum,
    MeasureProgramEnum,
    # Population Health
    RiskStratificationRequest,
    RiskStratificationResponse,
    CareGapsRequest,
    CareGapsResponse,
    PopulationRegistryRequest,
    PopulationRegistryResponse,
    RiskLevelEnum,
    ChronicConditionEnum,
    CareGapPriorityEnum,
    # Financial
    RevenueSummaryRequest,
    RevenueSummaryResponse,
    PayerMixResponse,
    DenialAnalysisRequest,
    DenialAnalysisResponse,
    ARAgingResponse,
    CashFlowForecastRequest,
    CashFlowForecastResponse,
    PayerTypeEnum,
    # Operational
    DepartmentProductivityRequest,
    DepartmentProductivityResponse,
    DepartmentTypeEnum,
    ResourceUtilizationResponse,
    PatientFlowRequest,
    PatientFlowResponse,
    BottleneckResponse,
    WaitTimeResponse,
    PredictiveStaffingRequest,
    PredictiveStaffingResponse,
    # Predictive
    PredictionRequest,
    PredictionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
    ModelPerformanceResponse,
    DriftDetectionResponse,
    ModelTypeEnum,
    # Reports
    CreateReportRequest,
    ReportDefinitionSchema,
    ReportExecutionRequest,
    ReportExecutionResponse,
    ExportReportRequest,
    ExportReportResponse,
    ScheduleReportRequest,
    ScheduledReportSchema,
    ReportTemplateSchema,
    QueryBuilderRequest,
    QueryBuilderResponse,
    # Statistics
    AnalyticsStatisticsResponse,
    HealthCheckResponse,
)


router = APIRouter(prefix="/advanced-analytics", tags=["Advanced Analytics"])


def get_tenant_id(x_tenant_id: Optional[str] = Header(None)) -> Optional[str]:
    """Extract tenant ID from header."""
    return x_tenant_id


# ==================== Executive Dashboard ====================

@router.post("/dashboard/executive", response_model=ExecutiveDashboardResponse)
async def get_executive_dashboard(
    request: ExecutiveDashboardRequest,
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """
    Get comprehensive executive dashboard.

    Returns financial, clinical, operational, and quality metrics
    with trend data and benchmark comparisons.
    """
    return await service.get_executive_dashboard(request, tenant_id)


@router.get("/dashboard/departments")
async def get_department_performance(
    facility_id: Optional[str] = Query(None, description="Facility ID filter"),
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
) -> List[Dict[str, Any]]:
    """Get department performance metrics."""
    return await service.get_department_performance(facility_id, tenant_id)


@router.get("/dashboard/realtime")
async def get_realtime_dashboard(
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
) -> Dict[str, Any]:
    """Get real-time operational dashboard."""
    return await service.get_realtime_dashboard(tenant_id)


# ==================== Clinical Quality ====================

@router.post("/quality/measures", response_model=QualityMeasuresResponse)
async def get_quality_measures(
    request: QualityMeasureRequest,
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """
    Get clinical quality measures.

    Supports filtering by measure IDs, category, program, provider, and department.
    """
    return await service.get_quality_measures(request, tenant_id)


@router.get("/quality/measures")
async def get_quality_measures_simple(
    measure_ids: Optional[str] = Query(None, description="Comma-separated measure IDs"),
    category: Optional[MeasureCategoryEnum] = Query(None),
    program: Optional[MeasureProgramEnum] = Query(None),
    provider_id: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
) -> QualityMeasuresResponse:
    """Get quality measures via GET request."""
    request = QualityMeasureRequest(
        measure_ids=measure_ids.split(",") if measure_ids else None,
        category=category,
        program=program,
        provider_id=provider_id,
        department=department
    )
    return await service.get_quality_measures(request, tenant_id)


@router.get("/quality/providers/scorecards", response_model=List[ProviderScorecardSchema])
async def get_provider_scorecards(
    department: Optional[str] = Query(None, description="Department filter"),
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """Get provider performance scorecards."""
    return await service.get_provider_scorecards(department, tenant_id)


@router.get("/quality/safety", response_model=List[SafetyIndicatorSchema])
async def get_safety_indicators(
    department: Optional[str] = Query(None),
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """Get patient safety indicators."""
    return await service.get_safety_indicators(department, tenant_id)


@router.post("/quality/control-chart", response_model=ControlChartResponse)
async def get_control_chart(
    request: ControlChartRequest,
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """Get statistical process control chart for a measure."""
    return await service.get_control_chart(request, tenant_id)


# ==================== Population Health ====================

@router.post("/population/risk-stratification", response_model=RiskStratificationResponse)
async def get_risk_stratification(
    request: RiskStratificationRequest,
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """
    Get risk-stratified patient population.

    Supports filtering by risk level, chronic conditions, and PCP.
    Returns patients with risk scores and care gaps.
    """
    return await service.get_risk_stratification(request, tenant_id)


@router.get("/population/risk-stratification")
async def get_risk_stratification_simple(
    risk_level: Optional[RiskLevelEnum] = Query(None),
    conditions: Optional[str] = Query(None, description="Comma-separated chronic conditions"),
    pcp_id: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
) -> RiskStratificationResponse:
    """Get risk stratification via GET request."""
    chronic_conditions = None
    if conditions:
        chronic_conditions = [ChronicConditionEnum(c.strip()) for c in conditions.split(",")]

    request = RiskStratificationRequest(
        risk_level=risk_level,
        chronic_conditions=chronic_conditions,
        pcp_id=pcp_id,
        limit=limit,
        offset=offset
    )
    return await service.get_risk_stratification(request, tenant_id)


@router.post("/population/care-gaps", response_model=CareGapsResponse)
async def get_care_gaps(
    request: CareGapsRequest,
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """
    Get care gaps for patients.

    Supports filtering by gap type, priority, patient, and overdue status.
    """
    return await service.get_care_gaps(request, tenant_id)


@router.get("/population/care-gaps")
async def get_care_gaps_simple(
    gap_types: Optional[str] = Query(None, description="Comma-separated gap types"),
    priority: Optional[CareGapPriorityEnum] = Query(None),
    patient_id: Optional[str] = Query(None),
    overdue_only: bool = Query(False),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
) -> CareGapsResponse:
    """Get care gaps via GET request."""
    request = CareGapsRequest(
        gap_types=gap_types.split(",") if gap_types else None,
        priority=priority,
        patient_id=patient_id,
        overdue_only=overdue_only,
        limit=limit,
        offset=offset
    )
    return await service.get_care_gaps(request, tenant_id)


@router.get("/population/registry/{condition}", response_model=PopulationRegistryResponse)
async def get_population_registry(
    condition: ChronicConditionEnum,
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """Get chronic disease registry for a condition."""
    request = PopulationRegistryRequest(condition=condition)
    return await service.get_population_registry(request, tenant_id)


@router.get("/population/sdoh")
async def get_sdoh_analysis(
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
) -> Dict[str, Any]:
    """Get social determinants of health analysis."""
    return await service.get_sdoh_analysis(tenant_id)


# ==================== Financial Analytics ====================

@router.post("/financial/revenue", response_model=RevenueSummaryResponse)
async def get_revenue_summary(
    request: RevenueSummaryRequest,
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """Get revenue performance summary."""
    return await service.get_revenue_summary(request, tenant_id)


@router.get("/financial/revenue")
async def get_revenue_summary_simple(
    start_date: date = Query(...),
    end_date: date = Query(...),
    facility_id: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
) -> RevenueSummaryResponse:
    """Get revenue summary via GET request."""
    request = RevenueSummaryRequest(
        start_date=start_date,
        end_date=end_date,
        facility_id=facility_id,
        department=department
    )
    return await service.get_revenue_summary(request, tenant_id)


@router.get("/financial/payer-mix", response_model=PayerMixResponse)
async def get_payer_mix(
    start_date: date = Query(...),
    end_date: date = Query(...),
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """Get payer mix analysis."""
    return await service.get_payer_mix(start_date, end_date, tenant_id)


@router.post("/financial/denials", response_model=DenialAnalysisResponse)
async def get_denial_analysis(
    request: DenialAnalysisRequest,
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """Get claims denial analysis."""
    return await service.get_denial_analysis(request, tenant_id)


@router.get("/financial/ar-aging", response_model=ARAgingResponse)
async def get_ar_aging(
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """Get AR aging analysis."""
    return await service.get_ar_aging(tenant_id)


@router.post("/financial/cash-flow-forecast", response_model=CashFlowForecastResponse)
async def get_cash_flow_forecast(
    request: CashFlowForecastRequest,
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """Get cash flow forecast."""
    return await service.get_cash_flow_forecast(request, tenant_id)


# ==================== Operational Analytics ====================

@router.post("/operational/productivity", response_model=DepartmentProductivityResponse)
async def get_department_productivity(
    request: DepartmentProductivityRequest,
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """Get department productivity metrics."""
    return await service.get_department_productivity(request, tenant_id)


@router.get("/operational/productivity")
async def get_department_productivity_simple(
    department: Optional[DepartmentTypeEnum] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
) -> DepartmentProductivityResponse:
    """Get department productivity via GET."""
    request = DepartmentProductivityRequest(
        department=department,
        start_date=start_date,
        end_date=end_date
    )
    return await service.get_department_productivity(request, tenant_id)


@router.get("/operational/resources", response_model=ResourceUtilizationResponse)
async def get_resource_utilization(
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """Get resource utilization metrics."""
    return await service.get_resource_utilization(tenant_id)


@router.post("/operational/patient-flow", response_model=PatientFlowResponse)
async def get_patient_flow(
    request: PatientFlowRequest,
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """Get patient flow analysis."""
    return await service.get_patient_flow(request, tenant_id)


@router.get("/operational/patient-flow/{flow_type}", response_model=PatientFlowResponse)
async def get_patient_flow_by_type(
    flow_type: str,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """Get patient flow by type (ED, Inpatient, Outpatient, Surgery)."""
    request = PatientFlowRequest(
        flow_type=flow_type,
        start_date=start_date,
        end_date=end_date
    )
    return await service.get_patient_flow(request, tenant_id)


@router.get("/operational/bottlenecks", response_model=BottleneckResponse)
async def get_bottlenecks(
    department: Optional[DepartmentTypeEnum] = Query(None),
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """Identify operational bottlenecks."""
    return await service.get_bottlenecks(department, tenant_id)


@router.get("/operational/wait-times", response_model=WaitTimeResponse)
async def get_wait_times(
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """Get wait time analysis."""
    return await service.get_wait_times(tenant_id)


@router.post("/operational/staffing", response_model=PredictiveStaffingResponse)
async def get_predictive_staffing(
    request: PredictiveStaffingRequest,
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """Get predictive staffing recommendations."""
    return await service.get_predictive_staffing(request, tenant_id)


# ==================== Predictive Analytics ====================

@router.post("/predictive/predict", response_model=PredictionResponse)
async def make_prediction(
    request: PredictionRequest,
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """
    Make a prediction for a patient.

    Supports readmission, length of stay, no-show, deterioration, and cost predictions.
    Returns prediction with confidence score and recommended actions.
    """
    return await service.predict(request, tenant_id)


@router.post("/predictive/batch", response_model=BatchPredictionResponse)
async def batch_predict(
    request: BatchPredictionRequest,
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """Submit batch prediction job."""
    return await service.batch_predict(request, tenant_id)


@router.get("/predictive/models")
async def get_available_models(
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
) -> List[Dict[str, Any]]:
    """Get available prediction models."""
    return await service.get_available_models(tenant_id)


@router.get("/predictive/models/{model_id}/performance", response_model=ModelPerformanceResponse)
async def get_model_performance(
    model_id: str,
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """Get model performance metrics."""
    return await service.get_model_performance(model_id, tenant_id)


@router.get("/predictive/models/{model_id}/drift", response_model=DriftDetectionResponse)
async def detect_model_drift(
    model_id: str,
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """Detect model drift."""
    return await service.detect_drift(model_id, tenant_id)


# ==================== Report Builder ====================

@router.post("/reports", response_model=ReportDefinitionSchema)
async def create_report(
    request: CreateReportRequest,
    x_user_id: str = Header(..., description="User ID"),
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """Create a new report."""
    return await service.create_report(request, x_user_id, tenant_id)


@router.post("/reports/execute", response_model=ReportExecutionResponse)
async def execute_report(
    request: ReportExecutionRequest,
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """Execute a report and return results."""
    return await service.execute_report(request, tenant_id)


@router.get("/reports/{report_id}/execute")
async def execute_report_get(
    report_id: str,
    limit: int = Query(1000, le=10000),
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
) -> ReportExecutionResponse:
    """Execute report via GET request."""
    request = ReportExecutionRequest(report_id=report_id, limit=limit)
    return await service.execute_report(request, tenant_id)


@router.post("/reports/export", response_model=ExportReportResponse)
async def export_report(
    request: ExportReportRequest,
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """Export a report to specified format."""
    return await service.export_report(request, tenant_id)


@router.post("/reports/schedule", response_model=ScheduledReportSchema)
async def schedule_report(
    request: ScheduleReportRequest,
    x_user_id: str = Header(..., description="User ID"),
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """Schedule a report for delivery."""
    return await service.schedule_report(request, x_user_id, tenant_id)


@router.get("/reports/templates", response_model=List[ReportTemplateSchema])
async def get_report_templates(
    category: Optional[str] = Query(None),
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """Get available report templates."""
    return await service.get_templates(category, tenant_id)


@router.get("/reports/fields")
async def get_available_fields(
    data_source: str = Query("analytics_warehouse"),
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
) -> List[Dict[str, Any]]:
    """Get available fields for report building."""
    return await service.get_available_fields(data_source, tenant_id)


@router.post("/reports/query-builder", response_model=QueryBuilderResponse)
async def build_query(
    request: QueryBuilderRequest,
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """Build query from visual configuration."""
    return await service.build_query(request, tenant_id)


# ==================== Statistics & Health ====================

@router.get("/statistics", response_model=AnalyticsStatisticsResponse)
async def get_statistics(
    tenant_id: Optional[str] = Depends(get_tenant_id),
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """Get analytics platform statistics."""
    return await service.get_statistics(tenant_id)


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    service: AdvancedAnalyticsService = Depends(get_advanced_analytics_service)
):
    """Perform health check."""
    return await service.health_check()
