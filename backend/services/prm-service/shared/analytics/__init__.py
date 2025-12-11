"""
Advanced Analytics Module - EPIC-011: Advanced Analytics Platform

This module provides comprehensive analytics capabilities for healthcare organizations:
- Executive Dashboard Platform (US-011.1)
- Clinical Quality Analytics (US-011.2)
- Population Health Management (US-011.3)
- Financial Performance Analytics (US-011.4)
- Operational Efficiency Analytics (US-011.5)
- Predictive Analytics Engine (US-011.6)
- Custom Report Builder (US-011.7)
"""

# Executive Dashboard
from backend.shared.analytics.executive_dashboard import (
    executive_dashboard_service,
    ExecutiveDashboardService,
    ExecutiveDashboardData,
    FinancialMetrics,
    ClinicalMetrics,
    OperationalMetrics,
    QualityMetrics,
    KPIValue,
    MetricTrendData,
    MetricTrend,
    PerformanceLevel,
    ComparisonPeriod,
    BenchmarkComparison,
    DepartmentPerformance,
    ProviderPerformance,
)

# Clinical Quality Analytics
from backend.shared.analytics.clinical_quality import (
    clinical_quality_service,
    ClinicalQualityService,
    QualityMeasure,
    MeasureResult,
    MeasureCategory,
    MeasureProgram,
    PerformanceStatus,
    ProviderScorecard,
    SafetyIndicator,
    ControlChartData,
    ControlChartPoint,
    ControlChartStatus,
    OutcomeAnalysis,
    QualityImprovementProject,
)

# Population Health Management
from backend.shared.analytics.population_health import (
    population_health_service,
    PopulationHealthService,
    RiskLevel,
    RiskScore,
    PatientRiskProfile,
    CareGap,
    CareGapPriority,
    PopulationRegistry,
    ChronicCondition,
    SDOHFactor,
    InterventionCampaign,
    InterventionStatus,
    CohortComparison,
    OutcomeAttribution,
)

# Financial Performance Analytics
from backend.shared.analytics.financial_analytics import (
    financial_analytics_service,
    FinancialAnalyticsService,
    RevenueMetrics,
    PayerAnalysis,
    PayerType,
    ServiceLineMetrics,
    ServiceLine,
    DenialAnalysis,
    DenialReason,
    ARAgingData,
    ARAgingBucket,
    CashFlowForecast,
    ContractPerformance,
    RevenueOpportunity,
)

# Operational Efficiency Analytics
from backend.shared.analytics.operational_analytics import (
    operational_analytics_service,
    OperationalAnalyticsService,
    DepartmentType,
    DepartmentProductivity,
    StaffProductivity,
    ResourceType,
    ResourceUtilization,
    PatientFlowAnalysis,
    PatientFlowStep,
    Bottleneck,
    BottleneckSeverity,
    WaitTimeMetrics,
    ThroughputMetrics,
    StaffingRecommendation,
)

# Predictive Analytics Engine
from backend.shared.analytics.predictive_engine import (
    predictive_engine,
    PredictiveAnalyticsEngine,
    ModelType,
    ModelStatus,
    ModelMetadata,
    PredictionResult,
    PredictionConfidence,
    FeatureImportance,
    BatchPredictionJob,
    ModelPerformance,
    DriftMetrics,
    ABTestResult,
    RetrainingJob,
)

# Report Builder
from backend.shared.analytics.report_builder import (
    report_builder_service,
    ReportBuilderService,
    ReportType,
    ReportDefinition,
    ReportTemplate,
    ReportExecution,
    VisualizationType,
    VisualizationConfig,
    ExportFormat,
    ScheduleFrequency,
    ScheduledReport,
    ReportSubscription,
    DataField,
    FilterCondition,
    QueryResult,
)

__all__ = [
    # Executive Dashboard
    "executive_dashboard_service",
    "ExecutiveDashboardService",
    "ExecutiveDashboardData",
    "FinancialMetrics",
    "ClinicalMetrics",
    "OperationalMetrics",
    "QualityMetrics",
    "KPIValue",
    "MetricTrendData",
    "MetricTrend",
    "PerformanceLevel",
    "ComparisonPeriod",
    "BenchmarkComparison",
    "DepartmentPerformance",
    "ProviderPerformance",
    # Clinical Quality
    "clinical_quality_service",
    "ClinicalQualityService",
    "QualityMeasure",
    "MeasureResult",
    "MeasureCategory",
    "MeasureProgram",
    "PerformanceStatus",
    "ProviderScorecard",
    "SafetyIndicator",
    "ControlChartData",
    "ControlChartPoint",
    "ControlChartStatus",
    "OutcomeAnalysis",
    "QualityImprovementProject",
    # Population Health
    "population_health_service",
    "PopulationHealthService",
    "RiskLevel",
    "RiskScore",
    "PatientRiskProfile",
    "CareGap",
    "CareGapPriority",
    "PopulationRegistry",
    "ChronicCondition",
    "SDOHFactor",
    "InterventionCampaign",
    "InterventionStatus",
    "CohortComparison",
    "OutcomeAttribution",
    # Financial Analytics
    "financial_analytics_service",
    "FinancialAnalyticsService",
    "RevenueMetrics",
    "PayerAnalysis",
    "PayerType",
    "ServiceLineMetrics",
    "ServiceLine",
    "DenialAnalysis",
    "DenialReason",
    "ARAgingData",
    "ARAgingBucket",
    "CashFlowForecast",
    "ContractPerformance",
    "RevenueOpportunity",
    # Operational Analytics
    "operational_analytics_service",
    "OperationalAnalyticsService",
    "DepartmentType",
    "DepartmentProductivity",
    "StaffProductivity",
    "ResourceType",
    "ResourceUtilization",
    "PatientFlowAnalysis",
    "PatientFlowStep",
    "Bottleneck",
    "BottleneckSeverity",
    "WaitTimeMetrics",
    "ThroughputMetrics",
    "StaffingRecommendation",
    # Predictive Engine
    "predictive_engine",
    "PredictiveAnalyticsEngine",
    "ModelType",
    "ModelStatus",
    "ModelMetadata",
    "PredictionResult",
    "PredictionConfidence",
    "FeatureImportance",
    "BatchPredictionJob",
    "ModelPerformance",
    "DriftMetrics",
    "ABTestResult",
    "RetrainingJob",
    # Report Builder
    "report_builder_service",
    "ReportBuilderService",
    "ReportType",
    "ReportDefinition",
    "ReportTemplate",
    "ReportExecution",
    "VisualizationType",
    "VisualizationConfig",
    "ExportFormat",
    "ScheduleFrequency",
    "ScheduledReport",
    "ReportSubscription",
    "DataField",
    "FilterCondition",
    "QueryResult",
]
