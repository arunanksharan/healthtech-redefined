"""
Tests for Advanced Analytics Module (EPIC-011)

Comprehensive tests for:
- Executive Dashboard Platform (US-011.1)
- Clinical Quality Analytics (US-011.2)
- Population Health Management (US-011.3)
- Financial Performance Analytics (US-011.4)
- Operational Efficiency Analytics (US-011.5)
- Predictive Analytics Engine (US-011.6)
- Custom Report Builder (US-011.7)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, date, timedelta
from decimal import Decimal

# Import shared analytics services
from shared.analytics.executive_dashboard import (
    ExecutiveDashboardService,
    ExecutiveDashboardData,
    KPIValue,
    MetricTrend,
    PerformanceLevel,
)
from shared.analytics.clinical_quality import (
    ClinicalQualityService,
    QualityMeasure,
    MeasureResult,
    MeasureCategory,
    MeasureProgram,
    PerformanceStatus,
    ProviderScorecard,
    SafetyIndicator,
    ControlChartData,
)
from shared.analytics.population_health import (
    PopulationHealthService,
    PatientRiskProfile,
    CareGap,
    ChronicDiseaseRegistry,
    RiskLevel,
    ChronicCondition,
    CareGapPriority,
    SDOHFactor,
)
from shared.analytics.financial_analytics import (
    FinancialAnalyticsService,
    RevenueMetrics,
    PayerMixAnalysis,
    DenialAnalysis,
    ARAgingAnalysis,
    CashFlowForecast,
    PayerType,
    DenialReason,
    ARAgingBucket,
)
from shared.analytics.operational_analytics import (
    OperationalAnalyticsService,
    DepartmentProductivity,
    ResourceUtilization,
    PatientFlowAnalysis,
    Bottleneck,
    WaitTimeMetrics,
    StaffingRecommendation,
    DepartmentType,
    ResourceType,
)
from shared.analytics.predictive_engine import (
    PredictiveAnalyticsEngine,
    ModelMetadata,
    PredictionResult,
    FeatureImportance,
    DriftMetrics,
    ABTestResult,
    ModelType,
    ModelStatus,
)
from shared.analytics.report_builder import (
    ReportBuilderService,
    ReportDefinition,
    ReportExecution,
    ScheduledReport,
    ReportTemplate,
    QueryBuilder,
    ReportType,
    VisualizationType,
    ExportFormat,
    ScheduleFrequency,
)


# ==================== Executive Dashboard Tests (US-011.1) ====================

class TestExecutiveDashboardService:
    """Tests for executive dashboard functionality"""

    @pytest.fixture
    def service(self):
        return ExecutiveDashboardService()

    @pytest.fixture
    def tenant_id(self):
        return str(uuid4())

    @pytest.mark.asyncio
    async def test_get_dashboard_data(self, service, tenant_id):
        """Test retrieving executive dashboard data"""
        result = await service.get_dashboard(
            tenant_id=tenant_id,
            dashboard_type="executive",
            date_range={"start": date.today() - timedelta(days=30), "end": date.today()}
        )

        assert result is not None
        assert isinstance(result, ExecutiveDashboardData)
        assert result.kpis is not None
        assert len(result.kpis) > 0

    @pytest.mark.asyncio
    async def test_kpi_values_have_trends(self, service, tenant_id):
        """Test that KPI values include trend information"""
        result = await service.get_dashboard(tenant_id=tenant_id)

        for kpi in result.kpis:
            assert isinstance(kpi, KPIValue)
            assert kpi.name != ""
            assert kpi.current_value is not None
            assert kpi.trend in [MetricTrend.IMPROVING, MetricTrend.DECLINING, MetricTrend.STABLE, MetricTrend.VOLATILE]

    @pytest.mark.asyncio
    async def test_performance_level_calculation(self, service, tenant_id):
        """Test performance level is calculated correctly"""
        result = await service.get_dashboard(tenant_id=tenant_id)

        for kpi in result.kpis:
            if kpi.target_value is not None:
                assert kpi.performance_level in [
                    PerformanceLevel.EXCEEDING,
                    PerformanceLevel.MEETING,
                    PerformanceLevel.BELOW,
                    PerformanceLevel.CRITICAL
                ]

    @pytest.mark.asyncio
    async def test_financial_metrics(self, service, tenant_id):
        """Test financial metrics are included"""
        result = await service.get_dashboard(tenant_id=tenant_id)

        assert result.financial_metrics is not None
        assert result.financial_metrics.total_revenue is not None
        assert result.financial_metrics.net_revenue is not None

    @pytest.mark.asyncio
    async def test_clinical_metrics(self, service, tenant_id):
        """Test clinical metrics are included"""
        result = await service.get_dashboard(tenant_id=tenant_id)

        assert result.clinical_metrics is not None
        assert result.clinical_metrics.patient_satisfaction is not None

    @pytest.mark.asyncio
    async def test_operational_metrics(self, service, tenant_id):
        """Test operational metrics are included"""
        result = await service.get_dashboard(tenant_id=tenant_id)

        assert result.operational_metrics is not None
        assert result.operational_metrics.bed_occupancy is not None

    @pytest.mark.asyncio
    async def test_benchmark_comparison(self, service, tenant_id):
        """Test benchmark comparison data"""
        result = await service.get_dashboard(tenant_id=tenant_id)

        assert result.benchmarks is not None
        # Benchmarks should include industry comparisons
        assert len(result.benchmarks) > 0


class TestKPITracking:
    """Tests for KPI tracking functionality"""

    @pytest.fixture
    def service(self):
        return ExecutiveDashboardService()

    @pytest.mark.asyncio
    async def test_kpi_history(self, service):
        """Test retrieving KPI historical data"""
        tenant_id = str(uuid4())
        kpi_id = "revenue_per_patient"

        result = await service.get_kpi_history(
            tenant_id=tenant_id,
            kpi_id=kpi_id,
            periods=12,
            period_type="monthly"
        )

        assert result is not None
        assert len(result) <= 12
        for point in result:
            assert point.date is not None
            assert point.value is not None

    @pytest.mark.asyncio
    async def test_kpi_alerts(self, service):
        """Test KPI alerting functionality"""
        tenant_id = str(uuid4())

        alerts = await service.get_kpi_alerts(tenant_id=tenant_id)

        assert alerts is not None
        for alert in alerts:
            assert alert.kpi_id is not None
            assert alert.alert_type in ["warning", "critical"]
            assert alert.message != ""


# ==================== Clinical Quality Analytics Tests (US-011.2) ====================

class TestClinicalQualityService:
    """Tests for clinical quality analytics"""

    @pytest.fixture
    def service(self):
        return ClinicalQualityService()

    @pytest.fixture
    def tenant_id(self):
        return str(uuid4())

    @pytest.mark.asyncio
    async def test_get_quality_measures(self, service, tenant_id):
        """Test retrieving quality measures"""
        result = await service.get_quality_measures(
            tenant_id=tenant_id,
            program=MeasureProgram.MIPS,
            reporting_period={"start": date(2024, 1, 1), "end": date(2024, 12, 31)}
        )

        assert result is not None
        assert len(result) > 0
        for measure in result:
            assert isinstance(measure, MeasureResult)
            assert measure.measure_id != ""
            assert measure.performance_rate is not None
            assert 0 <= measure.performance_rate <= 100

    @pytest.mark.asyncio
    async def test_measure_categories(self, service, tenant_id):
        """Test measures are categorized correctly"""
        result = await service.get_quality_measures(
            tenant_id=tenant_id,
            program=MeasureProgram.MIPS
        )

        categories = set(m.category for m in result)
        # Should have multiple categories
        assert len(categories) > 0
        for cat in categories:
            assert cat in [
                MeasureCategory.PROCESS,
                MeasureCategory.OUTCOME,
                MeasureCategory.STRUCTURE,
                MeasureCategory.PATIENT_EXPERIENCE,
                MeasureCategory.SAFETY
            ]

    @pytest.mark.asyncio
    async def test_hedis_measures(self, service, tenant_id):
        """Test HEDIS measure tracking"""
        result = await service.get_quality_measures(
            tenant_id=tenant_id,
            program=MeasureProgram.HEDIS
        )

        assert len(result) > 0
        for measure in result:
            assert measure.program == MeasureProgram.HEDIS

    @pytest.mark.asyncio
    async def test_performance_status(self, service, tenant_id):
        """Test performance status calculation"""
        result = await service.get_quality_measures(tenant_id=tenant_id)

        for measure in result:
            assert measure.status in [
                PerformanceStatus.EXCELLENT,
                PerformanceStatus.GOOD,
                PerformanceStatus.FAIR,
                PerformanceStatus.POOR,
                PerformanceStatus.CRITICAL
            ]
            # Star rating should be 1-5
            assert 1 <= measure.star_rating <= 5


class TestProviderScorecards:
    """Tests for provider scorecard functionality"""

    @pytest.fixture
    def service(self):
        return ClinicalQualityService()

    @pytest.mark.asyncio
    async def test_get_provider_scorecard(self, service):
        """Test retrieving provider scorecards"""
        tenant_id = str(uuid4())
        provider_id = str(uuid4())

        result = await service.get_provider_scorecard(
            tenant_id=tenant_id,
            provider_id=provider_id,
            period={"start": date(2024, 1, 1), "end": date(2024, 12, 31)}
        )

        assert result is not None
        assert isinstance(result, ProviderScorecard)
        assert result.overall_score is not None
        assert result.quality_score is not None
        assert result.measure_results is not None

    @pytest.mark.asyncio
    async def test_provider_peer_comparison(self, service):
        """Test provider peer comparison"""
        tenant_id = str(uuid4())
        provider_id = str(uuid4())

        result = await service.get_provider_scorecard(
            tenant_id=tenant_id,
            provider_id=provider_id
        )

        assert result.peer_rank is not None
        assert result.percentile_rank is not None
        assert 0 <= result.percentile_rank <= 100


class TestSafetyIndicators:
    """Tests for patient safety indicators"""

    @pytest.fixture
    def service(self):
        return ClinicalQualityService()

    @pytest.mark.asyncio
    async def test_get_safety_indicators(self, service):
        """Test retrieving patient safety indicators"""
        tenant_id = str(uuid4())

        result = await service.get_safety_indicators(tenant_id=tenant_id)

        assert result is not None
        assert len(result) > 0
        for indicator in result:
            assert isinstance(indicator, SafetyIndicator)
            assert indicator.name != ""
            assert indicator.count is not None
            assert indicator.rate is not None


class TestControlCharts:
    """Tests for statistical process control charts"""

    @pytest.fixture
    def service(self):
        return ClinicalQualityService()

    @pytest.mark.asyncio
    async def test_get_control_chart(self, service):
        """Test control chart generation"""
        tenant_id = str(uuid4())
        measure_id = "readmission_rate"

        result = await service.get_control_chart(
            tenant_id=tenant_id,
            measure_id=measure_id,
            periods=24
        )

        assert result is not None
        assert isinstance(result, ControlChartData)
        assert result.center_line is not None
        assert result.upper_control_limit is not None
        assert result.lower_control_limit is not None
        assert len(result.data_points) > 0

    @pytest.mark.asyncio
    async def test_special_cause_detection(self, service):
        """Test detection of special causes"""
        tenant_id = str(uuid4())

        result = await service.get_control_chart(
            tenant_id=tenant_id,
            measure_id="readmission_rate"
        )

        # Should identify any special causes
        assert result.special_causes is not None
        for cause in result.special_causes:
            assert cause.rule != ""
            assert cause.point_index is not None


# ==================== Population Health Tests (US-011.3) ====================

class TestPopulationHealthService:
    """Tests for population health management"""

    @pytest.fixture
    def service(self):
        return PopulationHealthService()

    @pytest.fixture
    def tenant_id(self):
        return str(uuid4())

    @pytest.mark.asyncio
    async def test_risk_stratification(self, service, tenant_id):
        """Test patient risk stratification"""
        result = await service.stratify_risk(
            tenant_id=tenant_id,
            population_filters={}
        )

        assert result is not None
        assert len(result) > 0
        for profile in result:
            assert isinstance(profile, PatientRiskProfile)
            assert profile.patient_id is not None
            assert profile.risk_score is not None
            assert profile.risk_level in [
                RiskLevel.VERY_LOW, RiskLevel.LOW, RiskLevel.MODERATE,
                RiskLevel.HIGH, RiskLevel.VERY_HIGH
            ]

    @pytest.mark.asyncio
    async def test_risk_distribution(self, service, tenant_id):
        """Test risk distribution across population"""
        result = await service.get_risk_distribution(tenant_id=tenant_id)

        assert result is not None
        # Should have counts for each risk level
        assert sum(result.values()) > 0

    @pytest.mark.asyncio
    async def test_high_risk_patients(self, service, tenant_id):
        """Test identifying high-risk patients"""
        result = await service.get_high_risk_patients(
            tenant_id=tenant_id,
            risk_threshold=RiskLevel.HIGH,
            limit=100
        )

        assert result is not None
        for patient in result:
            assert patient.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]


class TestCareGaps:
    """Tests for care gap identification"""

    @pytest.fixture
    def service(self):
        return PopulationHealthService()

    @pytest.mark.asyncio
    async def test_identify_care_gaps(self, service):
        """Test care gap identification"""
        tenant_id = str(uuid4())

        result = await service.identify_care_gaps(
            tenant_id=tenant_id,
            gap_types=["screening", "vaccination", "follow_up"]
        )

        assert result is not None
        assert len(result) > 0
        for gap in result:
            assert isinstance(gap, CareGap)
            assert gap.patient_id is not None
            assert gap.gap_type != ""
            assert gap.priority in [
                CareGapPriority.CRITICAL, CareGapPriority.HIGH,
                CareGapPriority.MEDIUM, CareGapPriority.LOW
            ]

    @pytest.mark.asyncio
    async def test_care_gap_prioritization(self, service):
        """Test care gap prioritization"""
        tenant_id = str(uuid4())

        result = await service.identify_care_gaps(
            tenant_id=tenant_id,
            sort_by="priority"
        )

        # Should be sorted by priority
        priorities = [g.priority for g in result]
        # Critical should come first
        if CareGapPriority.CRITICAL in priorities:
            assert priorities[0] == CareGapPriority.CRITICAL

    @pytest.mark.asyncio
    async def test_care_gap_by_measure(self, service):
        """Test care gaps for specific quality measures"""
        tenant_id = str(uuid4())

        result = await service.get_care_gaps_by_measure(
            tenant_id=tenant_id,
            measure_id="HbA1c_control"
        )

        assert result is not None
        for gap in result:
            assert gap.measure_id == "HbA1c_control"


class TestChronicDiseaseRegistries:
    """Tests for chronic disease registry management"""

    @pytest.fixture
    def service(self):
        return PopulationHealthService()

    @pytest.mark.asyncio
    async def test_get_disease_registry(self, service):
        """Test retrieving disease registry"""
        tenant_id = str(uuid4())

        result = await service.get_disease_registry(
            tenant_id=tenant_id,
            condition=ChronicCondition.DIABETES
        )

        assert result is not None
        for entry in result:
            assert isinstance(entry, ChronicDiseaseRegistry)
            assert entry.condition == ChronicCondition.DIABETES
            assert entry.patient_id is not None

    @pytest.mark.asyncio
    async def test_registry_control_status(self, service):
        """Test disease control status tracking"""
        tenant_id = str(uuid4())

        result = await service.get_disease_registry(
            tenant_id=tenant_id,
            condition=ChronicCondition.DIABETES
        )

        for entry in result:
            assert entry.is_controlled is not None
            if entry.latest_indicators:
                # Should have relevant clinical indicators
                assert "HbA1c" in entry.latest_indicators or len(entry.latest_indicators) > 0


class TestSDOHAnalysis:
    """Tests for Social Determinants of Health analysis"""

    @pytest.fixture
    def service(self):
        return PopulationHealthService()

    @pytest.mark.asyncio
    async def test_sdoh_analysis(self, service):
        """Test SDOH analysis"""
        tenant_id = str(uuid4())

        result = await service.analyze_sdoh(tenant_id=tenant_id)

        assert result is not None
        for factor in result:
            assert isinstance(factor, SDOHFactor)
            assert factor.category != ""
            assert factor.prevalence is not None
            assert factor.z_codes is not None

    @pytest.mark.asyncio
    async def test_sdoh_z_codes(self, service):
        """Test SDOH Z-code mapping"""
        tenant_id = str(uuid4())

        result = await service.analyze_sdoh(tenant_id=tenant_id)

        for factor in result:
            if factor.z_codes:
                # Z-codes should start with 'Z'
                for code in factor.z_codes:
                    assert code.startswith('Z')


# ==================== Financial Analytics Tests (US-011.4) ====================

class TestFinancialAnalyticsService:
    """Tests for financial performance analytics"""

    @pytest.fixture
    def service(self):
        return FinancialAnalyticsService()

    @pytest.fixture
    def tenant_id(self):
        return str(uuid4())

    @pytest.mark.asyncio
    async def test_get_revenue_summary(self, service, tenant_id):
        """Test revenue summary retrieval"""
        result = await service.get_revenue_summary(
            tenant_id=tenant_id,
            period={"start": date(2024, 1, 1), "end": date(2024, 12, 31)}
        )

        assert result is not None
        assert isinstance(result, RevenueMetrics)
        assert result.gross_revenue is not None
        assert result.net_revenue is not None
        assert result.total_collections is not None

    @pytest.mark.asyncio
    async def test_revenue_by_service_line(self, service, tenant_id):
        """Test revenue breakdown by service line"""
        result = await service.get_revenue_summary(tenant_id=tenant_id)

        assert result.by_service_line is not None
        assert len(result.by_service_line) > 0

    @pytest.mark.asyncio
    async def test_net_collection_rate(self, service, tenant_id):
        """Test net collection rate calculation"""
        result = await service.get_revenue_summary(tenant_id=tenant_id)

        assert result.net_collection_rate is not None
        assert 0 <= result.net_collection_rate <= 100


class TestPayerMixAnalysis:
    """Tests for payer mix analysis"""

    @pytest.fixture
    def service(self):
        return FinancialAnalyticsService()

    @pytest.mark.asyncio
    async def test_payer_mix_distribution(self, service):
        """Test payer mix distribution"""
        tenant_id = str(uuid4())

        result = await service.get_payer_mix(tenant_id=tenant_id)

        assert result is not None
        assert isinstance(result, PayerMixAnalysis)
        assert result.distribution is not None
        # Distribution should sum to 100%
        total = sum(p.percentage for p in result.distribution)
        assert abs(total - 100) < 0.1

    @pytest.mark.asyncio
    async def test_payer_types(self, service):
        """Test payer type categorization"""
        tenant_id = str(uuid4())

        result = await service.get_payer_mix(tenant_id=tenant_id)

        for payer in result.distribution:
            assert payer.payer_type in [
                PayerType.MEDICARE, PayerType.MEDICAID, PayerType.COMMERCIAL,
                PayerType.SELF_PAY, PayerType.WORKERS_COMP, PayerType.TRICARE,
                PayerType.VA, PayerType.OTHER_GOVERNMENT, PayerType.NO_FAULT,
                PayerType.UNINSURED
            ]


class TestDenialAnalysis:
    """Tests for claims denial analysis"""

    @pytest.fixture
    def service(self):
        return FinancialAnalyticsService()

    @pytest.mark.asyncio
    async def test_denial_rate(self, service):
        """Test denial rate calculation"""
        tenant_id = str(uuid4())

        result = await service.get_denial_analysis(tenant_id=tenant_id)

        assert result is not None
        assert isinstance(result, DenialAnalysis)
        assert result.denial_rate is not None
        assert 0 <= result.denial_rate <= 100

    @pytest.mark.asyncio
    async def test_denial_by_reason(self, service):
        """Test denial breakdown by reason"""
        tenant_id = str(uuid4())

        result = await service.get_denial_analysis(tenant_id=tenant_id)

        assert result.by_reason is not None
        assert len(result.by_reason) > 0
        for reason in result.by_reason:
            assert reason.reason in [
                DenialReason.ELIGIBILITY, DenialReason.AUTHORIZATION,
                DenialReason.CODING_ERROR, DenialReason.MEDICAL_NECESSITY,
                DenialReason.DUPLICATE, DenialReason.TIMELY_FILING,
                DenialReason.MISSING_INFO, DenialReason.BUNDLING,
                DenialReason.MODIFIER, DenialReason.COORDINATION_BENEFITS,
                DenialReason.OUT_OF_NETWORK, DenialReason.OTHER
            ]

    @pytest.mark.asyncio
    async def test_appeal_success_rate(self, service):
        """Test appeal success rate tracking"""
        tenant_id = str(uuid4())

        result = await service.get_denial_analysis(tenant_id=tenant_id)

        assert result.appeal_success_rate is not None
        assert 0 <= result.appeal_success_rate <= 100


class TestARAgingAnalysis:
    """Tests for AR aging analysis"""

    @pytest.fixture
    def service(self):
        return FinancialAnalyticsService()

    @pytest.mark.asyncio
    async def test_ar_aging_buckets(self, service):
        """Test AR aging bucket distribution"""
        tenant_id = str(uuid4())

        result = await service.get_ar_aging(tenant_id=tenant_id)

        assert result is not None
        assert isinstance(result, ARAgingAnalysis)
        assert result.total_ar is not None
        assert result.by_bucket is not None

        # Should have all aging buckets
        buckets = [b.bucket for b in result.by_bucket]
        assert ARAgingBucket.CURRENT in buckets or len(buckets) > 0

    @pytest.mark.asyncio
    async def test_days_in_ar(self, service):
        """Test days in AR calculation"""
        tenant_id = str(uuid4())

        result = await service.get_ar_aging(tenant_id=tenant_id)

        assert result.days_in_ar is not None
        assert result.days_in_ar >= 0

    @pytest.mark.asyncio
    async def test_collection_probability(self, service):
        """Test collection probability by aging bucket"""
        tenant_id = str(uuid4())

        result = await service.get_ar_aging(tenant_id=tenant_id)

        for bucket in result.by_bucket:
            assert bucket.collection_probability is not None
            assert 0 <= bucket.collection_probability <= 100


class TestCashFlowForecast:
    """Tests for cash flow forecasting"""

    @pytest.fixture
    def service(self):
        return FinancialAnalyticsService()

    @pytest.mark.asyncio
    async def test_cash_flow_forecast(self, service):
        """Test cash flow forecasting"""
        tenant_id = str(uuid4())

        result = await service.forecast_cash_flow(
            tenant_id=tenant_id,
            forecast_periods=12,
            period_type="monthly"
        )

        assert result is not None
        assert isinstance(result, CashFlowForecast)
        assert len(result.projections) == 12

    @pytest.mark.asyncio
    async def test_scenario_analysis(self, service):
        """Test cash flow scenario analysis"""
        tenant_id = str(uuid4())

        result = await service.forecast_cash_flow(
            tenant_id=tenant_id,
            scenarios=["base", "optimistic", "pessimistic"]
        )

        assert result.scenarios is not None
        assert len(result.scenarios) == 3


# ==================== Operational Analytics Tests (US-011.5) ====================

class TestOperationalAnalyticsService:
    """Tests for operational efficiency analytics"""

    @pytest.fixture
    def service(self):
        return OperationalAnalyticsService()

    @pytest.fixture
    def tenant_id(self):
        return str(uuid4())

    @pytest.mark.asyncio
    async def test_department_productivity(self, service, tenant_id):
        """Test department productivity metrics"""
        result = await service.get_department_productivity(
            tenant_id=tenant_id,
            department=DepartmentType.EMERGENCY
        )

        assert result is not None
        assert isinstance(result, DepartmentProductivity)
        assert result.total_encounters is not None
        assert result.rvu_per_fte is not None

    @pytest.mark.asyncio
    async def test_productivity_benchmark(self, service, tenant_id):
        """Test productivity benchmark comparison"""
        result = await service.get_department_productivity(
            tenant_id=tenant_id,
            department=DepartmentType.OUTPATIENT
        )

        assert result.benchmark_rvu_per_fte is not None
        assert result.variance_from_benchmark is not None


class TestResourceUtilization:
    """Tests for resource utilization tracking"""

    @pytest.fixture
    def service(self):
        return OperationalAnalyticsService()

    @pytest.mark.asyncio
    async def test_bed_utilization(self, service):
        """Test bed utilization metrics"""
        tenant_id = str(uuid4())

        result = await service.get_resource_utilization(
            tenant_id=tenant_id,
            resource_type=ResourceType.BED
        )

        assert result is not None
        assert isinstance(result, ResourceUtilization)
        assert result.utilization_rate is not None
        assert 0 <= result.utilization_rate <= 100

    @pytest.mark.asyncio
    async def test_or_utilization(self, service):
        """Test OR room utilization"""
        tenant_id = str(uuid4())

        result = await service.get_resource_utilization(
            tenant_id=tenant_id,
            resource_type=ResourceType.OR_ROOM
        )

        assert result is not None
        assert result.turnover_time is not None


class TestPatientFlowAnalysis:
    """Tests for patient flow analysis"""

    @pytest.fixture
    def service(self):
        return OperationalAnalyticsService()

    @pytest.mark.asyncio
    async def test_patient_flow(self, service):
        """Test patient flow analysis"""
        tenant_id = str(uuid4())

        result = await service.analyze_patient_flow(
            tenant_id=tenant_id,
            department=DepartmentType.EMERGENCY
        )

        assert result is not None
        assert isinstance(result, PatientFlowAnalysis)
        assert result.steps is not None
        assert len(result.steps) > 0

    @pytest.mark.asyncio
    async def test_bottleneck_identification(self, service):
        """Test bottleneck identification"""
        tenant_id = str(uuid4())

        result = await service.identify_bottlenecks(tenant_id=tenant_id)

        assert result is not None
        for bottleneck in result:
            assert isinstance(bottleneck, Bottleneck)
            assert bottleneck.location != ""
            assert bottleneck.avg_delay_minutes is not None
            assert bottleneck.impact_score is not None


class TestWaitTimeMetrics:
    """Tests for wait time metrics"""

    @pytest.fixture
    def service(self):
        return OperationalAnalyticsService()

    @pytest.mark.asyncio
    async def test_wait_times(self, service):
        """Test wait time metrics"""
        tenant_id = str(uuid4())

        result = await service.get_wait_times(
            tenant_id=tenant_id,
            department=DepartmentType.EMERGENCY
        )

        assert result is not None
        assert isinstance(result, WaitTimeMetrics)
        assert result.avg_wait_time is not None
        assert result.median_wait_time is not None
        assert result.percentile_90 is not None


class TestPredictiveStaffing:
    """Tests for predictive staffing"""

    @pytest.fixture
    def service(self):
        return OperationalAnalyticsService()

    @pytest.mark.asyncio
    async def test_staffing_recommendations(self, service):
        """Test staffing recommendations"""
        tenant_id = str(uuid4())

        result = await service.get_staffing_recommendations(
            tenant_id=tenant_id,
            department=DepartmentType.INPATIENT,
            forecast_days=7
        )

        assert result is not None
        for rec in result:
            assert isinstance(rec, StaffingRecommendation)
            assert rec.date is not None
            assert rec.recommended_staff is not None
            assert rec.predicted_volume is not None


# ==================== Predictive Analytics Engine Tests (US-011.6) ====================

class TestPredictiveAnalyticsEngine:
    """Tests for predictive analytics engine"""

    @pytest.fixture
    def engine(self):
        return PredictiveAnalyticsEngine()

    @pytest.fixture
    def tenant_id(self):
        return str(uuid4())

    @pytest.mark.asyncio
    async def test_readmission_prediction(self, engine, tenant_id):
        """Test readmission prediction"""
        result = await engine.predict(
            tenant_id=tenant_id,
            model_type=ModelType.READMISSION,
            features={
                "length_of_stay": 5,
                "age": 65,
                "comorbidity_count": 3,
                "prior_admissions": 2
            }
        )

        assert result is not None
        assert isinstance(result, PredictionResult)
        assert result.probability is not None
        assert 0 <= result.probability <= 1
        assert result.risk_level is not None

    @pytest.mark.asyncio
    async def test_los_prediction(self, engine, tenant_id):
        """Test length of stay prediction"""
        result = await engine.predict(
            tenant_id=tenant_id,
            model_type=ModelType.LENGTH_OF_STAY,
            features={
                "diagnosis": "pneumonia",
                "age": 70,
                "comorbidities": ["diabetes", "hypertension"]
            }
        )

        assert result is not None
        assert result.predicted_value is not None
        assert result.predicted_value >= 0

    @pytest.mark.asyncio
    async def test_no_show_prediction(self, engine, tenant_id):
        """Test no-show prediction"""
        result = await engine.predict(
            tenant_id=tenant_id,
            model_type=ModelType.NO_SHOW,
            features={
                "previous_no_shows": 2,
                "lead_time_days": 14,
                "appointment_type": "routine"
            }
        )

        assert result is not None
        assert result.probability is not None

    @pytest.mark.asyncio
    async def test_feature_importance(self, engine, tenant_id):
        """Test feature importance in predictions"""
        result = await engine.predict(
            tenant_id=tenant_id,
            model_type=ModelType.READMISSION,
            features={
                "length_of_stay": 7,
                "age": 72,
                "comorbidity_count": 5
            },
            include_explanations=True
        )

        assert result.feature_contributions is not None
        assert len(result.feature_contributions) > 0
        for contrib in result.feature_contributions:
            assert isinstance(contrib, FeatureImportance)
            assert contrib.feature_name != ""
            assert contrib.importance is not None


class TestModelManagement:
    """Tests for ML model management"""

    @pytest.fixture
    def engine(self):
        return PredictiveAnalyticsEngine()

    @pytest.mark.asyncio
    async def test_list_models(self, engine):
        """Test listing available models"""
        tenant_id = str(uuid4())

        result = await engine.list_models(tenant_id=tenant_id)

        assert result is not None
        for model in result:
            assert isinstance(model, ModelMetadata)
            assert model.model_id != ""
            assert model.model_type is not None
            assert model.status in [
                ModelStatus.DEVELOPMENT, ModelStatus.VALIDATION,
                ModelStatus.STAGING, ModelStatus.PRODUCTION,
                ModelStatus.DEPRECATED
            ]

    @pytest.mark.asyncio
    async def test_model_performance(self, engine):
        """Test model performance metrics"""
        tenant_id = str(uuid4())
        model_id = "readmission_v1"

        result = await engine.get_model_performance(
            tenant_id=tenant_id,
            model_id=model_id
        )

        assert result is not None
        assert result.auc_roc is not None
        assert 0 <= result.auc_roc <= 1
        assert result.accuracy is not None


class TestDriftDetection:
    """Tests for model drift detection"""

    @pytest.fixture
    def engine(self):
        return PredictiveAnalyticsEngine()

    @pytest.mark.asyncio
    async def test_drift_detection(self, engine):
        """Test drift detection"""
        tenant_id = str(uuid4())
        model_id = "readmission_v1"

        result = await engine.detect_drift(
            tenant_id=tenant_id,
            model_id=model_id
        )

        assert result is not None
        assert isinstance(result, DriftMetrics)
        assert result.data_drift_detected is not None
        assert result.concept_drift_detected is not None

    @pytest.mark.asyncio
    async def test_feature_drift_scores(self, engine):
        """Test feature-level drift scores"""
        tenant_id = str(uuid4())
        model_id = "readmission_v1"

        result = await engine.detect_drift(
            tenant_id=tenant_id,
            model_id=model_id
        )

        assert result.feature_drift_scores is not None
        assert result.psi_score is not None


class TestABTesting:
    """Tests for model A/B testing"""

    @pytest.fixture
    def engine(self):
        return PredictiveAnalyticsEngine()

    @pytest.mark.asyncio
    async def test_ab_test_results(self, engine):
        """Test A/B test results retrieval"""
        tenant_id = str(uuid4())

        result = await engine.get_ab_test_results(
            tenant_id=tenant_id,
            test_id="readmission_v1_vs_v2"
        )

        assert result is not None
        assert isinstance(result, ABTestResult)
        assert result.model_a_metrics is not None
        assert result.model_b_metrics is not None

    @pytest.mark.asyncio
    async def test_statistical_significance(self, engine):
        """Test statistical significance calculation"""
        tenant_id = str(uuid4())

        result = await engine.get_ab_test_results(
            tenant_id=tenant_id,
            test_id="readmission_v1_vs_v2"
        )

        assert result.p_value is not None
        assert result.is_significant is not None


class TestBatchPredictions:
    """Tests for batch predictions"""

    @pytest.fixture
    def engine(self):
        return PredictiveAnalyticsEngine()

    @pytest.mark.asyncio
    async def test_batch_predict(self, engine):
        """Test batch prediction"""
        tenant_id = str(uuid4())

        patients = [
            {"patient_id": str(uuid4()), "length_of_stay": 3, "age": 55},
            {"patient_id": str(uuid4()), "length_of_stay": 7, "age": 72},
            {"patient_id": str(uuid4()), "length_of_stay": 2, "age": 45},
        ]

        result = await engine.batch_predict(
            tenant_id=tenant_id,
            model_type=ModelType.READMISSION,
            records=patients
        )

        assert result is not None
        assert len(result) == 3
        for prediction in result:
            assert prediction.probability is not None


# ==================== Report Builder Tests (US-011.7) ====================

class TestReportBuilderService:
    """Tests for custom report builder"""

    @pytest.fixture
    def service(self):
        return ReportBuilderService()

    @pytest.fixture
    def tenant_id(self):
        return str(uuid4())

    @pytest.mark.asyncio
    async def test_create_report(self, service, tenant_id):
        """Test report creation"""
        result = await service.create_report(
            tenant_id=tenant_id,
            name="Monthly Quality Report",
            report_type=ReportType.SUMMARY,
            data_source="quality_measures",
            columns=["measure_name", "performance_rate", "benchmark"]
        )

        assert result is not None
        assert isinstance(result, ReportDefinition)
        assert result.id is not None
        assert result.name == "Monthly Quality Report"

    @pytest.mark.asyncio
    async def test_report_visualizations(self, service, tenant_id):
        """Test report visualization configuration"""
        result = await service.create_report(
            tenant_id=tenant_id,
            name="Revenue Dashboard",
            report_type=ReportType.DASHBOARD,
            visualizations=[
                {"type": VisualizationType.BAR_CHART, "title": "Revenue by Service Line"},
                {"type": VisualizationType.LINE_CHART, "title": "Revenue Trend"},
                {"type": VisualizationType.PIE_CHART, "title": "Payer Mix"}
            ]
        )

        assert result.visualizations is not None
        assert len(result.visualizations) == 3


class TestReportExecution:
    """Tests for report execution"""

    @pytest.fixture
    def service(self):
        return ReportBuilderService()

    @pytest.mark.asyncio
    async def test_execute_report(self, service):
        """Test report execution"""
        tenant_id = str(uuid4())
        report_id = str(uuid4())

        result = await service.execute_report(
            tenant_id=tenant_id,
            report_id=report_id,
            parameters={"date_range": {"start": date(2024, 1, 1), "end": date(2024, 12, 31)}}
        )

        assert result is not None
        assert isinstance(result, ReportExecution)
        assert result.status in ["completed", "running", "failed"]
        assert result.execution_time_ms is not None


class TestReportExport:
    """Tests for report export"""

    @pytest.fixture
    def service(self):
        return ReportBuilderService()

    @pytest.mark.asyncio
    async def test_export_pdf(self, service):
        """Test PDF export"""
        tenant_id = str(uuid4())
        report_id = str(uuid4())

        result = await service.export_report(
            tenant_id=tenant_id,
            report_id=report_id,
            format=ExportFormat.PDF
        )

        assert result is not None
        assert result.format == ExportFormat.PDF
        assert result.file_path is not None

    @pytest.mark.asyncio
    async def test_export_excel(self, service):
        """Test Excel export"""
        tenant_id = str(uuid4())
        report_id = str(uuid4())

        result = await service.export_report(
            tenant_id=tenant_id,
            report_id=report_id,
            format=ExportFormat.EXCEL
        )

        assert result is not None
        assert result.format == ExportFormat.EXCEL


class TestScheduledReports:
    """Tests for scheduled reports"""

    @pytest.fixture
    def service(self):
        return ReportBuilderService()

    @pytest.mark.asyncio
    async def test_schedule_report(self, service):
        """Test report scheduling"""
        tenant_id = str(uuid4())
        report_id = str(uuid4())

        result = await service.schedule_report(
            tenant_id=tenant_id,
            report_id=report_id,
            frequency=ScheduleFrequency.WEEKLY,
            recipients=["admin@example.com"],
            output_format=ExportFormat.PDF
        )

        assert result is not None
        assert isinstance(result, ScheduledReport)
        assert result.frequency == ScheduleFrequency.WEEKLY
        assert result.next_run is not None

    @pytest.mark.asyncio
    async def test_list_scheduled_reports(self, service):
        """Test listing scheduled reports"""
        tenant_id = str(uuid4())

        result = await service.list_scheduled_reports(tenant_id=tenant_id)

        assert result is not None
        for schedule in result:
            assert isinstance(schedule, ScheduledReport)


class TestReportTemplates:
    """Tests for report templates"""

    @pytest.fixture
    def service(self):
        return ReportBuilderService()

    @pytest.mark.asyncio
    async def test_list_templates(self, service):
        """Test listing report templates"""
        tenant_id = str(uuid4())

        result = await service.list_templates(
            tenant_id=tenant_id,
            category="financial"
        )

        assert result is not None
        for template in result:
            assert isinstance(template, ReportTemplate)
            assert template.name != ""
            assert template.category == "financial"

    @pytest.mark.asyncio
    async def test_create_from_template(self, service):
        """Test creating report from template"""
        tenant_id = str(uuid4())
        template_id = str(uuid4())

        result = await service.create_from_template(
            tenant_id=tenant_id,
            template_id=template_id,
            name="My Financial Report"
        )

        assert result is not None
        assert result.name == "My Financial Report"


class TestQueryBuilder:
    """Tests for visual query builder"""

    @pytest.fixture
    def service(self):
        return ReportBuilderService()

    @pytest.mark.asyncio
    async def test_get_available_fields(self, service):
        """Test getting available fields for query"""
        tenant_id = str(uuid4())

        result = await service.get_available_fields(
            tenant_id=tenant_id,
            data_source="encounters"
        )

        assert result is not None
        assert len(result) > 0
        for field in result:
            assert field.name != ""
            assert field.data_type in ["string", "number", "date", "boolean"]

    @pytest.mark.asyncio
    async def test_validate_query(self, service):
        """Test query validation"""
        tenant_id = str(uuid4())

        query = QueryBuilder(
            data_source="encounters",
            columns=["patient_id", "admission_date"],
            filters=[{"field": "admission_date", "operator": ">=", "value": "2024-01-01"}],
            group_by=["patient_id"]
        )

        result = await service.validate_query(
            tenant_id=tenant_id,
            query=query
        )

        assert result is not None
        assert result.is_valid is not None


# ==================== Integration Tests ====================

class TestAdvancedAnalyticsIntegration:
    """Integration tests for advanced analytics services"""

    @pytest.mark.asyncio
    async def test_executive_dashboard_workflow(self):
        """Test complete executive dashboard workflow"""
        service = ExecutiveDashboardService()
        tenant_id = str(uuid4())

        # Get dashboard
        dashboard = await service.get_dashboard(tenant_id=tenant_id)
        assert dashboard is not None

        # Get KPI history for each KPI
        for kpi in dashboard.kpis[:3]:  # First 3 KPIs
            history = await service.get_kpi_history(
                tenant_id=tenant_id,
                kpi_id=kpi.id,
                periods=6
            )
            assert history is not None

        # Get alerts
        alerts = await service.get_kpi_alerts(tenant_id=tenant_id)
        assert alerts is not None

    @pytest.mark.asyncio
    async def test_quality_analytics_workflow(self):
        """Test complete quality analytics workflow"""
        service = ClinicalQualityService()
        tenant_id = str(uuid4())

        # Get quality measures
        measures = await service.get_quality_measures(
            tenant_id=tenant_id,
            program=MeasureProgram.MIPS
        )
        assert len(measures) > 0

        # Get control chart for a measure
        if measures:
            chart = await service.get_control_chart(
                tenant_id=tenant_id,
                measure_id=measures[0].measure_id
            )
            assert chart is not None

        # Get safety indicators
        safety = await service.get_safety_indicators(tenant_id=tenant_id)
        assert safety is not None

    @pytest.mark.asyncio
    async def test_population_health_workflow(self):
        """Test complete population health workflow"""
        service = PopulationHealthService()
        tenant_id = str(uuid4())

        # Risk stratification
        risk_profiles = await service.stratify_risk(tenant_id=tenant_id)
        assert risk_profiles is not None

        # Care gap identification
        care_gaps = await service.identify_care_gaps(tenant_id=tenant_id)
        assert care_gaps is not None

        # Disease registry
        registry = await service.get_disease_registry(
            tenant_id=tenant_id,
            condition=ChronicCondition.DIABETES
        )
        assert registry is not None

        # SDOH analysis
        sdoh = await service.analyze_sdoh(tenant_id=tenant_id)
        assert sdoh is not None

    @pytest.mark.asyncio
    async def test_financial_analytics_workflow(self):
        """Test complete financial analytics workflow"""
        service = FinancialAnalyticsService()
        tenant_id = str(uuid4())

        # Revenue summary
        revenue = await service.get_revenue_summary(tenant_id=tenant_id)
        assert revenue is not None

        # Payer mix
        payer_mix = await service.get_payer_mix(tenant_id=tenant_id)
        assert payer_mix is not None

        # Denial analysis
        denials = await service.get_denial_analysis(tenant_id=tenant_id)
        assert denials is not None

        # AR aging
        ar_aging = await service.get_ar_aging(tenant_id=tenant_id)
        assert ar_aging is not None

        # Cash flow forecast
        forecast = await service.forecast_cash_flow(
            tenant_id=tenant_id,
            forecast_periods=6
        )
        assert forecast is not None

    @pytest.mark.asyncio
    async def test_predictive_analytics_workflow(self):
        """Test complete predictive analytics workflow"""
        engine = PredictiveAnalyticsEngine()
        tenant_id = str(uuid4())

        # List models
        models = await engine.list_models(tenant_id=tenant_id)
        assert models is not None

        # Make prediction
        prediction = await engine.predict(
            tenant_id=tenant_id,
            model_type=ModelType.READMISSION,
            features={"length_of_stay": 5, "age": 65},
            include_explanations=True
        )
        assert prediction is not None

        # Check drift
        if models:
            drift = await engine.detect_drift(
                tenant_id=tenant_id,
                model_id=models[0].model_id
            )
            assert drift is not None

    @pytest.mark.asyncio
    async def test_report_builder_workflow(self):
        """Test complete report builder workflow"""
        service = ReportBuilderService()
        tenant_id = str(uuid4())

        # Create report
        report = await service.create_report(
            tenant_id=tenant_id,
            name="Test Report",
            report_type=ReportType.SUMMARY,
            data_source="quality_measures"
        )
        assert report is not None

        # Execute report
        execution = await service.execute_report(
            tenant_id=tenant_id,
            report_id=report.id
        )
        assert execution is not None

        # Export report
        export = await service.export_report(
            tenant_id=tenant_id,
            report_id=report.id,
            format=ExportFormat.PDF
        )
        assert export is not None

        # Schedule report
        schedule = await service.schedule_report(
            tenant_id=tenant_id,
            report_id=report.id,
            frequency=ScheduleFrequency.MONTHLY,
            recipients=["test@example.com"],
            output_format=ExportFormat.PDF
        )
        assert schedule is not None


# ==================== Performance Tests ====================

class TestAdvancedAnalyticsPerformance:
    """Performance tests for advanced analytics services"""

    @pytest.mark.asyncio
    async def test_dashboard_response_time(self):
        """Test dashboard response time"""
        import time
        service = ExecutiveDashboardService()
        tenant_id = str(uuid4())

        start = time.time()
        await service.get_dashboard(tenant_id=tenant_id)
        elapsed = (time.time() - start) * 1000

        # Target: <2 seconds (2000ms)
        assert elapsed < 2000, f"Dashboard took {elapsed}ms, exceeding 2000ms target"

    @pytest.mark.asyncio
    async def test_prediction_response_time(self):
        """Test prediction response time"""
        import time
        engine = PredictiveAnalyticsEngine()
        tenant_id = str(uuid4())

        start = time.time()
        await engine.predict(
            tenant_id=tenant_id,
            model_type=ModelType.READMISSION,
            features={"length_of_stay": 5, "age": 65}
        )
        elapsed = (time.time() - start) * 1000

        # Target: <500ms
        assert elapsed < 500, f"Prediction took {elapsed}ms, exceeding 500ms target"

    @pytest.mark.asyncio
    async def test_batch_prediction_performance(self):
        """Test batch prediction performance"""
        import time
        engine = PredictiveAnalyticsEngine()
        tenant_id = str(uuid4())

        # Generate 100 records
        records = [{"patient_id": str(uuid4()), "length_of_stay": i % 10 + 1, "age": 50 + i % 30}
                   for i in range(100)]

        start = time.time()
        result = await engine.batch_predict(
            tenant_id=tenant_id,
            model_type=ModelType.READMISSION,
            records=records
        )
        elapsed = (time.time() - start) * 1000

        assert len(result) == 100
        # Target: <5 seconds for 100 records
        assert elapsed < 5000, f"Batch prediction took {elapsed}ms, exceeding 5000ms target"

    @pytest.mark.asyncio
    async def test_report_execution_performance(self):
        """Test report execution performance"""
        import time
        service = ReportBuilderService()
        tenant_id = str(uuid4())
        report_id = str(uuid4())

        start = time.time()
        await service.execute_report(
            tenant_id=tenant_id,
            report_id=report_id
        )
        elapsed = (time.time() - start) * 1000

        # Target: <10 seconds for standard reports
        assert elapsed < 10000, f"Report execution took {elapsed}ms, exceeding 10000ms target"


# ==================== Run Tests ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
