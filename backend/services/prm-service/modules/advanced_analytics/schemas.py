"""
Advanced Analytics Module Schemas - EPIC-011
Pydantic models for API request/response validation.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID

from pydantic import BaseModel, Field


# ==================== Enums ====================

class MetricTrendEnum(str, Enum):
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    VOLATILE = "volatile"


class PerformanceLevelEnum(str, Enum):
    EXCEEDING = "exceeding"
    MEETING = "meeting"
    BELOW = "below"
    CRITICAL = "critical"


class MeasureCategoryEnum(str, Enum):
    PROCESS = "process"
    OUTCOME = "outcome"
    STRUCTURE = "structure"
    PATIENT_EXPERIENCE = "patient_experience"
    EFFICIENCY = "efficiency"
    SAFETY = "safety"


class MeasureProgramEnum(str, Enum):
    MIPS = "mips"
    ACO = "aco"
    HEDIS = "hedis"
    CMS_CORE = "cms_core"
    TJC = "the_joint_commission"
    NQF = "nqf"


class RiskLevelEnum(str, Enum):
    VERY_HIGH = "very_high"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    VERY_LOW = "very_low"


class ChronicConditionEnum(str, Enum):
    DIABETES = "diabetes"
    HYPERTENSION = "hypertension"
    HEART_FAILURE = "heart_failure"
    COPD = "copd"
    ASTHMA = "asthma"
    CKD = "chronic_kidney_disease"
    DEPRESSION = "depression"
    OBESITY = "obesity"


class CareGapPriorityEnum(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PayerTypeEnum(str, Enum):
    MEDICARE = "medicare"
    MEDICAID = "medicaid"
    COMMERCIAL = "commercial"
    MANAGED_CARE = "managed_care"
    SELF_PAY = "self_pay"
    OTHER = "other"


class ServiceLineEnum(str, Enum):
    INPATIENT = "inpatient"
    OUTPATIENT = "outpatient"
    EMERGENCY = "emergency"
    AMBULATORY_SURGERY = "ambulatory_surgery"
    IMAGING = "imaging"
    LABORATORY = "laboratory"


class DepartmentTypeEnum(str, Enum):
    EMERGENCY = "emergency"
    INPATIENT = "inpatient"
    OUTPATIENT = "outpatient"
    SURGERY = "surgery"
    IMAGING = "imaging"
    LABORATORY = "laboratory"


class ModelTypeEnum(str, Enum):
    READMISSION = "readmission"
    LENGTH_OF_STAY = "length_of_stay"
    NO_SHOW = "no_show"
    DETERIORATION = "deterioration"
    COST = "cost"
    MORTALITY = "mortality"


class ReportTypeEnum(str, Enum):
    DASHBOARD = "dashboard"
    TABULAR = "tabular"
    SUMMARY = "summary"
    DETAIL = "detail"
    TRENDING = "trending"


class VisualizationTypeEnum(str, Enum):
    BAR_CHART = "bar_chart"
    LINE_CHART = "line_chart"
    PIE_CHART = "pie_chart"
    AREA_CHART = "area_chart"
    HEAT_MAP = "heat_map"
    KPI_CARD = "kpi_card"
    TABLE = "table"
    GAUGE = "gauge"


class ExportFormatEnum(str, Enum):
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    POWERPOINT = "powerpoint"
    JSON = "json"


class ScheduleFrequencyEnum(str, Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


# ==================== Executive Dashboard ====================

class KPIValueSchema(BaseModel):
    """Single KPI value."""
    value: float
    unit: str
    formatted: str
    target: Optional[float] = None
    target_formatted: Optional[str] = None
    variance_from_target: Optional[float] = None
    variance_percentage: Optional[float] = None
    performance_level: Optional[PerformanceLevelEnum] = None


class MetricTrendSchema(BaseModel):
    """Trend data for a metric."""
    current_value: float
    previous_value: float
    change_value: float
    change_percentage: float
    trend: MetricTrendEnum
    sparkline_data: List[float] = []


class FinancialMetricsSchema(BaseModel):
    """Financial metrics."""
    total_revenue: KPIValueSchema
    total_costs: KPIValueSchema
    gross_margin: KPIValueSchema
    operating_margin: KPIValueSchema
    ar_days: KPIValueSchema
    collection_rate: KPIValueSchema
    denial_rate: KPIValueSchema
    revenue_trend: MetricTrendSchema
    payer_mix: Dict[str, float] = {}


class ClinicalMetricsSchema(BaseModel):
    """Clinical metrics."""
    total_patients: KPIValueSchema
    total_encounters: KPIValueSchema
    readmission_rate_30day: KPIValueSchema
    mortality_rate: KPIValueSchema
    infection_rate: KPIValueSchema
    average_los: KPIValueSchema
    quality_composite_score: KPIValueSchema
    patient_trend: MetricTrendSchema


class OperationalMetricsSchema(BaseModel):
    """Operational metrics."""
    bed_occupancy_rate: KPIValueSchema
    or_utilization: KPIValueSchema
    er_wait_time: KPIValueSchema
    patient_throughput: KPIValueSchema
    staff_productivity: KPIValueSchema
    no_show_rate: KPIValueSchema
    occupancy_trend: MetricTrendSchema


class QualityMetricsSchema(BaseModel):
    """Quality metrics."""
    patient_satisfaction_score: KPIValueSchema
    nps_score: KPIValueSchema
    quality_score: KPIValueSchema
    safety_score: KPIValueSchema
    compliance_rate: KPIValueSchema
    satisfaction_trend: MetricTrendSchema
    satisfaction_breakdown: Dict[str, float] = {}


class ExecutiveDashboardRequest(BaseModel):
    """Executive dashboard request."""
    start_date: date
    end_date: date
    facility_id: Optional[str] = None


class ExecutiveDashboardResponse(BaseModel):
    """Executive dashboard response."""
    generated_at: datetime
    period_start: date
    period_end: date
    facility_id: Optional[str] = None
    facility_name: Optional[str] = None
    financial: FinancialMetricsSchema
    clinical: ClinicalMetricsSchema
    operational: OperationalMetricsSchema
    quality: QualityMetricsSchema
    benchmarks: List[Dict[str, Any]] = []
    alerts: List[Dict[str, Any]] = []


# ==================== Clinical Quality ====================

class QualityMeasureRequest(BaseModel):
    """Quality measures request."""
    measure_ids: Optional[List[str]] = None
    category: Optional[MeasureCategoryEnum] = None
    program: Optional[MeasureProgramEnum] = None
    provider_id: Optional[str] = None
    department: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class MeasureResultSchema(BaseModel):
    """Quality measure result."""
    measure_id: str
    measure_name: str
    numerator: int
    denominator: int
    rate: float
    rate_formatted: str
    benchmark: float
    benchmark_formatted: str
    variance_from_benchmark: float
    percentile_rank: int
    performance_status: str
    trend_direction: str
    trend_data: List[float] = []


class QualityMeasuresResponse(BaseModel):
    """Quality measures response."""
    measures: List[MeasureResultSchema]
    summary: Dict[str, Any] = {}


class ProviderScorecardSchema(BaseModel):
    """Provider scorecard."""
    provider_id: str
    provider_name: str
    specialty: str
    department: str
    overall_score: float
    quality_score: float
    safety_score: float
    patient_experience_score: float
    efficiency_score: float
    rank_overall: int
    measures: List[MeasureResultSchema] = []


class SafetyIndicatorSchema(BaseModel):
    """Safety indicator."""
    indicator_id: str
    indicator_name: str
    category: str
    event_count: int
    patient_days: int
    rate_per_1000: float
    benchmark_rate: float
    trend: str
    severity_breakdown: Dict[str, int] = {}


class ControlChartRequest(BaseModel):
    """Control chart request."""
    measure_id: str
    start_date: date
    end_date: date


class ControlChartResponse(BaseModel):
    """Control chart response."""
    measure_id: str
    measure_name: str
    points: List[Dict[str, Any]]
    mean: float
    std_dev: float
    ucl: float
    lcl: float
    current_status: str
    rules_violated: List[str] = []


# ==================== Population Health ====================

class RiskStratificationRequest(BaseModel):
    """Risk stratification request."""
    population_type: Optional[str] = None
    risk_level: Optional[RiskLevelEnum] = None
    chronic_conditions: Optional[List[ChronicConditionEnum]] = None
    pcp_id: Optional[str] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)


class PatientRiskSchema(BaseModel):
    """Patient risk profile."""
    patient_id: str
    patient_name: str
    age: int
    gender: str
    risk_score: float
    risk_level: RiskLevelEnum
    chronic_conditions: List[str] = []
    care_gaps_count: int
    predicted_cost: float
    last_pcp_visit: Optional[str] = None


class RiskStratificationResponse(BaseModel):
    """Risk stratification response."""
    summary: Dict[str, Any]
    patients: List[PatientRiskSchema]
    pagination: Dict[str, Any]


class CareGapsRequest(BaseModel):
    """Care gaps request."""
    gap_types: Optional[List[str]] = None
    priority: Optional[CareGapPriorityEnum] = None
    patient_id: Optional[str] = None
    overdue_only: bool = False
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)


class CareGapSchema(BaseModel):
    """Care gap."""
    gap_id: str
    gap_type: str
    description: str
    priority: CareGapPriorityEnum
    due_date: Optional[str] = None
    overdue_days: int
    patient_id: str
    patient_name: str
    recommended_action: str
    potential_value: float


class CareGapsResponse(BaseModel):
    """Care gaps response."""
    summary: Dict[str, Any]
    gaps: List[CareGapSchema]
    pagination: Dict[str, Any]


class PopulationRegistryRequest(BaseModel):
    """Population registry request."""
    condition: ChronicConditionEnum


class PopulationRegistryResponse(BaseModel):
    """Population registry response."""
    condition: str
    total_patients: int
    risk_distribution: Dict[str, int]
    average_risk_score: float
    controlled_count: int
    uncontrolled_count: int
    care_gap_count: int
    key_metrics: Dict[str, Any] = {}
    trends: Dict[str, List[float]] = {}


# ==================== Financial Analytics ====================

class RevenueSummaryRequest(BaseModel):
    """Revenue summary request."""
    start_date: date
    end_date: date
    facility_id: Optional[str] = None
    department: Optional[str] = None


class RevenueSummaryResponse(BaseModel):
    """Revenue summary response."""
    gross_revenue: float
    net_revenue: float
    contractual_adjustments: float
    bad_debt: float
    charity_care: float
    net_collection_rate: float
    revenue_per_patient: float
    yoy_growth: float


class PayerMixResponse(BaseModel):
    """Payer mix response."""
    payers: List[Dict[str, Any]]
    total_gross_charges: float
    total_net_revenue: float


class DenialAnalysisRequest(BaseModel):
    """Denial analysis request."""
    start_date: date
    end_date: date
    payer_type: Optional[PayerTypeEnum] = None


class DenialAnalysisResponse(BaseModel):
    """Denial analysis response."""
    summary: Dict[str, Any]
    by_reason: List[Dict[str, Any]]
    trends: Dict[str, List[float]] = {}
    recommendations: List[Dict[str, str]] = []


class ARAgingResponse(BaseModel):
    """AR aging response."""
    summary: Dict[str, Any]
    buckets: List[Dict[str, Any]]
    by_payer: List[Dict[str, Any]] = []


class CashFlowForecastRequest(BaseModel):
    """Cash flow forecast request."""
    forecast_days: int = Field(default=90, le=365)


class CashFlowForecastResponse(BaseModel):
    """Cash flow forecast response."""
    summary: Dict[str, Any]
    daily: List[Dict[str, Any]]
    weekly: List[Dict[str, Any]]
    scenarios: Dict[str, float]


# ==================== Operational Analytics ====================

class DepartmentProductivityRequest(BaseModel):
    """Department productivity request."""
    department: Optional[DepartmentTypeEnum] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class DepartmentProductivityResponse(BaseModel):
    """Department productivity response."""
    departments: List[Dict[str, Any]]
    summary: Dict[str, Any] = {}


class ResourceUtilizationResponse(BaseModel):
    """Resource utilization response."""
    summary: Dict[str, Any]
    by_type: Dict[str, Any]
    resources: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]] = []


class PatientFlowRequest(BaseModel):
    """Patient flow request."""
    flow_type: str  # ED, Inpatient, Outpatient, Surgery
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class PatientFlowResponse(BaseModel):
    """Patient flow response."""
    flow_type: str
    total_patients: int
    avg_total_time: float
    median_total_time: float
    steps: List[Dict[str, Any]]
    bottlenecks: List[str]
    recommendations: List[str]


class BottleneckResponse(BaseModel):
    """Bottleneck response."""
    bottlenecks: List[Dict[str, Any]]
    summary: Dict[str, Any] = {}


class WaitTimeResponse(BaseModel):
    """Wait time response."""
    summary: Dict[str, Any]
    by_department: List[Dict[str, Any]]
    hourly_distribution: Dict[str, float]


class PredictiveStaffingRequest(BaseModel):
    """Predictive staffing request."""
    department: DepartmentTypeEnum
    forecast_days: int = Field(default=7, le=30)


class PredictiveStaffingResponse(BaseModel):
    """Predictive staffing response."""
    department: str
    forecast_period: Dict[str, Any]
    summary: Dict[str, Any]
    by_date: Dict[str, List[Dict[str, Any]]]
    alerts: List[Dict[str, Any]] = []


# ==================== Predictive Analytics ====================

class PredictionRequest(BaseModel):
    """Prediction request."""
    model_type: ModelTypeEnum
    patient_id: str
    features: Dict[str, Any]
    include_explanations: bool = True


class FeatureContributionSchema(BaseModel):
    """Feature contribution."""
    feature_name: str
    importance_score: float
    direction: str
    category: str
    description: str


class PredictionResponse(BaseModel):
    """Prediction response."""
    prediction_id: str
    model_id: str
    model_version: str
    patient_id: str
    prediction_type: str
    predicted_value: float
    confidence: str
    confidence_score: float
    risk_level: str
    feature_contributions: List[FeatureContributionSchema] = []
    recommended_actions: List[str] = []


class BatchPredictionRequest(BaseModel):
    """Batch prediction request."""
    model_type: ModelTypeEnum
    patient_ids: List[str]


class BatchPredictionResponse(BaseModel):
    """Batch prediction response."""
    job_id: str
    model_id: str
    status: str
    total_records: int
    processed_records: int
    output_location: Optional[str] = None


class ModelPerformanceResponse(BaseModel):
    """Model performance response."""
    model: Dict[str, Any]
    current_performance: Dict[str, float]
    trends: Dict[str, List[Dict[str, Any]]]
    alerts: List[Dict[str, str]] = []


class DriftDetectionResponse(BaseModel):
    """Drift detection response."""
    model_id: str
    detection_date: datetime
    feature_drift: Dict[str, float]
    prediction_drift: float
    is_drifting: bool
    drift_severity: str
    recommended_action: str


class ABTestResponse(BaseModel):
    """A/B test response."""
    test_id: str
    test_name: str
    model_a_id: str
    model_b_id: str
    status: str
    model_a_metrics: Dict[str, float]
    model_b_metrics: Dict[str, float]
    winner: Optional[str] = None
    statistical_significance: float
    recommendation: str


# ==================== Report Builder ====================

class ReportDefinitionSchema(BaseModel):
    """Report definition."""
    report_id: Optional[str] = None
    report_name: str
    description: str = ""
    report_type: ReportTypeEnum = ReportTypeEnum.TABULAR
    data_source: str = "analytics_warehouse"
    fields: List[Dict[str, Any]] = []
    filters: List[Dict[str, Any]] = []
    sort_order: List[Dict[str, Any]] = []
    visualizations: List[Dict[str, Any]] = []
    parameters: Dict[str, Any] = {}
    is_public: bool = False
    tags: List[str] = []


class CreateReportRequest(BaseModel):
    """Create report request."""
    name: str
    description: str = ""
    type: ReportTypeEnum = ReportTypeEnum.TABULAR
    data_source: str = "analytics_warehouse"
    fields: List[Dict[str, Any]] = []
    filters: List[Dict[str, Any]] = []
    visualizations: List[Dict[str, Any]] = []
    is_public: bool = False
    tags: List[str] = []


class ReportExecutionRequest(BaseModel):
    """Report execution request."""
    report_id: str
    parameters: Optional[Dict[str, Any]] = None
    limit: int = Field(default=1000, le=10000)


class ReportExecutionResponse(BaseModel):
    """Report execution response."""
    report: Dict[str, Any]
    data: Dict[str, Any]
    execution: Dict[str, Any]
    visualizations: List[Dict[str, Any]] = []


class ExportReportRequest(BaseModel):
    """Export report request."""
    report_id: str
    export_format: ExportFormatEnum
    parameters: Optional[Dict[str, Any]] = None


class ExportReportResponse(BaseModel):
    """Export report response."""
    export_id: str
    report_id: str
    format: str
    status: str
    download_url: str
    expires_at: str


class ScheduleReportRequest(BaseModel):
    """Schedule report request."""
    report_id: str
    report_name: str
    frequency: ScheduleFrequencyEnum
    schedule_time: str = "08:00"
    day_of_week: Optional[int] = None
    day_of_month: Optional[int] = None
    recipients: List[str] = []
    export_format: ExportFormatEnum = ExportFormatEnum.PDF
    parameters: Dict[str, Any] = {}


class ScheduledReportSchema(BaseModel):
    """Scheduled report."""
    schedule_id: str
    report_id: str
    report_name: str
    frequency: str
    schedule_time: str
    recipients: List[str]
    export_format: str
    is_active: bool
    next_run: Optional[datetime] = None


class ReportTemplateSchema(BaseModel):
    """Report template."""
    template_id: str
    template_name: str
    description: str
    category: str
    popularity: int
    tags: List[str] = []


class QueryBuilderRequest(BaseModel):
    """Query builder request."""
    table: str
    fields: List[str] = []
    filters: List[Dict[str, Any]] = []
    group_by: List[str] = []
    order_by: List[Dict[str, Any]] = []


class QueryBuilderResponse(BaseModel):
    """Query builder response."""
    sql: str
    preview: Dict[str, Any]
    estimated_rows: int
    estimated_time_ms: int


# ==================== Statistics and Health ====================

class AnalyticsStatisticsResponse(BaseModel):
    """Analytics platform statistics."""
    total_reports: int
    total_executions_today: int
    total_scheduled_reports: int
    total_models: int
    avg_query_time_ms: float
    cache_hit_rate: float
    active_users_today: int
    data_freshness: Dict[str, str]


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    components: Dict[str, str]
    version: str
    uptime_seconds: float
