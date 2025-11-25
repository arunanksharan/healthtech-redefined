"""
Advanced Analytics Module
EPIC-011: Advanced Analytics Platform

This module provides API endpoints for:
- Executive Dashboard Platform (US-011.1)
- Clinical Quality Analytics (US-011.2)
- Population Health Management (US-011.3)
- Financial Performance Analytics (US-011.4)
- Operational Efficiency Analytics (US-011.5)
- Predictive Analytics Engine (US-011.6)
- Custom Report Builder (US-011.7)
"""

from modules.advanced_analytics.router import router
from modules.advanced_analytics.service import AdvancedAnalyticsService, get_advanced_analytics_service
from modules.advanced_analytics.schemas import (
    # Executive Dashboard
    ExecutiveDashboardRequest,
    ExecutiveDashboardResponse,
    KPIValueSchema,
    FinancialMetricsSchema,
    ClinicalMetricsSchema,
    OperationalMetricsSchema,
    QualityMetricsSchema,
    # Clinical Quality
    QualityMeasureRequest,
    QualityMeasuresResponse,
    MeasureResultSchema,
    ProviderScorecardSchema,
    SafetyIndicatorSchema,
    ControlChartResponse,
    # Population Health
    RiskStratificationRequest,
    RiskStratificationResponse,
    CareGapsRequest,
    CareGapsResponse,
    PopulationRegistryResponse,
    # Financial
    RevenueSummaryResponse,
    PayerMixResponse,
    DenialAnalysisResponse,
    ARAgingResponse,
    CashFlowForecastResponse,
    # Operational
    DepartmentProductivityResponse,
    ResourceUtilizationResponse,
    PatientFlowResponse,
    BottleneckResponse,
    WaitTimeResponse,
    PredictiveStaffingResponse,
    # Predictive
    PredictionRequest,
    PredictionResponse,
    BatchPredictionResponse,
    ModelPerformanceResponse,
    DriftDetectionResponse,
    # Reports
    ReportDefinitionSchema,
    ReportExecutionResponse,
    ExportReportResponse,
    ScheduledReportSchema,
    ReportTemplateSchema,
    QueryBuilderResponse,
    # Statistics
    AnalyticsStatisticsResponse,
    HealthCheckResponse,
)

__all__ = [
    "router",
    "AdvancedAnalyticsService",
    "get_advanced_analytics_service",
    # Executive Dashboard
    "ExecutiveDashboardRequest",
    "ExecutiveDashboardResponse",
    "KPIValueSchema",
    "FinancialMetricsSchema",
    "ClinicalMetricsSchema",
    "OperationalMetricsSchema",
    "QualityMetricsSchema",
    # Clinical Quality
    "QualityMeasureRequest",
    "QualityMeasuresResponse",
    "MeasureResultSchema",
    "ProviderScorecardSchema",
    "SafetyIndicatorSchema",
    "ControlChartResponse",
    # Population Health
    "RiskStratificationRequest",
    "RiskStratificationResponse",
    "CareGapsRequest",
    "CareGapsResponse",
    "PopulationRegistryResponse",
    # Financial
    "RevenueSummaryResponse",
    "PayerMixResponse",
    "DenialAnalysisResponse",
    "ARAgingResponse",
    "CashFlowForecastResponse",
    # Operational
    "DepartmentProductivityResponse",
    "ResourceUtilizationResponse",
    "PatientFlowResponse",
    "BottleneckResponse",
    "WaitTimeResponse",
    "PredictiveStaffingResponse",
    # Predictive
    "PredictionRequest",
    "PredictionResponse",
    "BatchPredictionResponse",
    "ModelPerformanceResponse",
    "DriftDetectionResponse",
    # Reports
    "ReportDefinitionSchema",
    "ReportExecutionResponse",
    "ExportReportResponse",
    "ScheduledReportSchema",
    "ReportTemplateSchema",
    "QueryBuilderResponse",
    # Statistics
    "AnalyticsStatisticsResponse",
    "HealthCheckResponse",
]
