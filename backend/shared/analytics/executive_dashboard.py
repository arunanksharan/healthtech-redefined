"""
Executive Dashboard Service - EPIC-011: US-011.1
Provides comprehensive organizational KPIs and real-time executive metrics.

Features:
- Financial performance metrics (revenue, costs, margins)
- Clinical quality indicators (readmissions, mortality, infections)
- Operational efficiency metrics (throughput, utilization, wait times)
- Patient satisfaction scores and trends
- Comparative benchmarks against industry standards
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID
import json


class MetricTrend(Enum):
    """Trend direction for metrics."""
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    VOLATILE = "volatile"


class PerformanceLevel(Enum):
    """Performance level compared to target."""
    EXCEEDING = "exceeding"
    MEETING = "meeting"
    BELOW = "below"
    CRITICAL = "critical"


class ComparisonPeriod(Enum):
    """Time period for comparisons."""
    PREVIOUS_DAY = "previous_day"
    PREVIOUS_WEEK = "previous_week"
    PREVIOUS_MONTH = "previous_month"
    PREVIOUS_QUARTER = "previous_quarter"
    PREVIOUS_YEAR = "previous_year"
    SAME_PERIOD_LAST_YEAR = "same_period_last_year"


@dataclass
class KPIValue:
    """Single KPI value with metadata."""
    value: float
    unit: str
    formatted: str
    target: Optional[float] = None
    target_formatted: Optional[str] = None
    variance_from_target: Optional[float] = None
    variance_percentage: Optional[float] = None
    performance_level: Optional[PerformanceLevel] = None


@dataclass
class MetricTrendData:
    """Trend data for a metric over time."""
    current_value: float
    previous_value: float
    change_value: float
    change_percentage: float
    trend: MetricTrend
    sparkline_data: List[float] = field(default_factory=list)
    time_labels: List[str] = field(default_factory=list)


@dataclass
class FinancialMetrics:
    """Financial performance metrics."""
    total_revenue: KPIValue
    total_costs: KPIValue
    gross_margin: KPIValue
    operating_margin: KPIValue
    net_margin: KPIValue
    ar_days: KPIValue
    collection_rate: KPIValue
    denial_rate: KPIValue
    revenue_per_patient: KPIValue
    cost_per_patient: KPIValue
    revenue_trend: MetricTrendData
    payer_mix: Dict[str, float] = field(default_factory=dict)
    revenue_by_service_line: Dict[str, float] = field(default_factory=dict)


@dataclass
class ClinicalMetrics:
    """Clinical quality metrics."""
    total_patients: KPIValue
    total_encounters: KPIValue
    readmission_rate_30day: KPIValue
    mortality_rate: KPIValue
    infection_rate: KPIValue
    complication_rate: KPIValue
    average_los: KPIValue
    emergency_visits: KPIValue
    patient_safety_score: KPIValue
    quality_composite_score: KPIValue
    patient_trend: MetricTrendData
    readmission_trend: MetricTrendData


@dataclass
class OperationalMetrics:
    """Operational efficiency metrics."""
    bed_occupancy_rate: KPIValue
    or_utilization: KPIValue
    er_wait_time: KPIValue
    door_to_provider_time: KPIValue
    patient_throughput: KPIValue
    staff_productivity: KPIValue
    appointment_utilization: KPIValue
    no_show_rate: KPIValue
    average_turnaround_time: KPIValue
    resource_utilization: KPIValue
    occupancy_trend: MetricTrendData
    wait_time_trend: MetricTrendData


@dataclass
class QualityMetrics:
    """Patient satisfaction and quality metrics."""
    patient_satisfaction_score: KPIValue
    nps_score: KPIValue
    hcahps_score: KPIValue
    complaint_rate: KPIValue
    grievance_rate: KPIValue
    quality_score: KPIValue
    safety_score: KPIValue
    compliance_rate: KPIValue
    satisfaction_trend: MetricTrendData
    satisfaction_breakdown: Dict[str, float] = field(default_factory=dict)


@dataclass
class BenchmarkComparison:
    """Comparison against benchmarks."""
    metric_name: str
    current_value: float
    benchmark_value: float
    benchmark_source: str
    percentile_rank: int
    variance: float
    variance_percentage: float
    performance_level: PerformanceLevel


@dataclass
class ExecutiveDashboardData:
    """Complete executive dashboard data."""
    generated_at: datetime
    period_start: date
    period_end: date
    facility_id: Optional[str]
    facility_name: Optional[str]
    financial: FinancialMetrics
    clinical: ClinicalMetrics
    operational: OperationalMetrics
    quality: QualityMetrics
    benchmarks: List[BenchmarkComparison] = field(default_factory=list)
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    last_refresh: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DepartmentPerformance:
    """Performance metrics for a department."""
    department_id: str
    department_name: str
    efficiency_score: float
    quality_score: float
    satisfaction_score: float
    patient_volume: int
    revenue: float
    cost: float
    margin: float
    trend: MetricTrend


@dataclass
class ProviderPerformance:
    """Performance metrics for a provider."""
    provider_id: str
    provider_name: str
    specialty: str
    patient_volume: int
    quality_score: float
    satisfaction_score: float
    productivity_score: float
    revenue_generated: float
    avg_encounter_duration: float
    readmission_rate: float


class ExecutiveDashboardService:
    """
    Service for generating executive dashboard metrics.

    Provides real-time and historical KPIs for healthcare executives
    with drill-down capabilities and benchmark comparisons.
    """

    def __init__(self):
        self.cache_ttl = 300  # 5 minutes
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}

        # Industry benchmarks
        self.benchmarks = {
            "readmission_rate": {"value": 15.0, "source": "CMS National Average"},
            "mortality_rate": {"value": 2.0, "source": "CMS National Average"},
            "infection_rate": {"value": 1.0, "source": "CDC NHSN"},
            "bed_occupancy": {"value": 65.0, "source": "AHA Average"},
            "er_wait_time": {"value": 45.0, "source": "CMS ED Benchmarks"},
            "patient_satisfaction": {"value": 75.0, "source": "HCAHPS National"},
            "ar_days": {"value": 45.0, "source": "HFMA Median"},
            "collection_rate": {"value": 95.0, "source": "MGMA Benchmark"},
        }

    def _format_currency(self, value: float) -> str:
        """Format value as currency."""
        if value >= 1_000_000:
            return f"${value / 1_000_000:.2f}M"
        elif value >= 1_000:
            return f"${value / 1_000:.1f}K"
        else:
            return f"${value:.2f}"

    def _format_percentage(self, value: float) -> str:
        """Format value as percentage."""
        return f"{value:.1f}%"

    def _format_number(self, value: float) -> str:
        """Format value as number."""
        if value >= 1_000_000:
            return f"{value / 1_000_000:.2f}M"
        elif value >= 1_000:
            return f"{value / 1_000:.1f}K"
        else:
            return f"{value:,.0f}"

    def _calculate_variance(
        self,
        actual: float,
        target: float
    ) -> tuple[float, float, PerformanceLevel]:
        """Calculate variance from target."""
        variance = actual - target
        variance_pct = ((actual - target) / target * 100) if target != 0 else 0

        # Determine performance level
        if variance_pct >= 10:
            level = PerformanceLevel.EXCEEDING
        elif variance_pct >= -5:
            level = PerformanceLevel.MEETING
        elif variance_pct >= -20:
            level = PerformanceLevel.BELOW
        else:
            level = PerformanceLevel.CRITICAL

        return variance, variance_pct, level

    def _calculate_trend(
        self,
        current: float,
        previous: float,
        history: List[float]
    ) -> MetricTrendData:
        """Calculate trend data for a metric."""
        change = current - previous
        change_pct = ((current - previous) / previous * 100) if previous != 0 else 0

        # Determine trend direction
        if len(history) >= 3:
            recent_avg = sum(history[-3:]) / 3
            older_avg = sum(history[:3]) / 3 if len(history) >= 6 else history[0]

            if recent_avg > older_avg * 1.05:
                trend = MetricTrend.IMPROVING
            elif recent_avg < older_avg * 0.95:
                trend = MetricTrend.DECLINING
            else:
                # Check volatility
                if len(history) >= 5:
                    variance = sum((x - sum(history)/len(history))**2 for x in history) / len(history)
                    if variance > (sum(history)/len(history) * 0.2) ** 2:
                        trend = MetricTrend.VOLATILE
                    else:
                        trend = MetricTrend.STABLE
                else:
                    trend = MetricTrend.STABLE
        else:
            trend = MetricTrend.STABLE if abs(change_pct) < 5 else (
                MetricTrend.IMPROVING if change_pct > 0 else MetricTrend.DECLINING
            )

        return MetricTrendData(
            current_value=current,
            previous_value=previous,
            change_value=change,
            change_percentage=change_pct,
            trend=trend,
            sparkline_data=history,
            time_labels=[]  # Would be populated with actual dates
        )

    def _create_kpi(
        self,
        value: float,
        unit: str,
        formatter: str,
        target: Optional[float] = None
    ) -> KPIValue:
        """Create a KPI value with formatting."""
        if formatter == "currency":
            formatted = self._format_currency(value)
            target_formatted = self._format_currency(target) if target else None
        elif formatter == "percentage":
            formatted = self._format_percentage(value)
            target_formatted = self._format_percentage(target) if target else None
        else:
            formatted = self._format_number(value)
            target_formatted = self._format_number(target) if target else None

        variance, variance_pct, level = (
            self._calculate_variance(value, target) if target else (None, None, None)
        )

        return KPIValue(
            value=value,
            unit=unit,
            formatted=formatted,
            target=target,
            target_formatted=target_formatted,
            variance_from_target=variance,
            variance_percentage=variance_pct,
            performance_level=level
        )

    async def get_executive_dashboard(
        self,
        start_date: date,
        end_date: date,
        facility_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> ExecutiveDashboardData:
        """
        Get comprehensive executive dashboard data.

        Args:
            start_date: Start of reporting period
            end_date: End of reporting period
            facility_id: Optional facility filter
            tenant_id: Tenant ID for multi-tenancy

        Returns:
            Complete dashboard data with all metrics
        """
        # Generate simulated metrics (would query actual data warehouse)
        financial = self._generate_financial_metrics(start_date, end_date)
        clinical = self._generate_clinical_metrics(start_date, end_date)
        operational = self._generate_operational_metrics(start_date, end_date)
        quality = self._generate_quality_metrics(start_date, end_date)
        benchmarks = self._generate_benchmark_comparisons(financial, clinical, operational, quality)
        alerts = self._generate_alerts(financial, clinical, operational, quality)

        return ExecutiveDashboardData(
            generated_at=datetime.utcnow(),
            period_start=start_date,
            period_end=end_date,
            facility_id=facility_id,
            facility_name="Main Hospital" if facility_id else None,
            financial=financial,
            clinical=clinical,
            operational=operational,
            quality=quality,
            benchmarks=benchmarks,
            alerts=alerts,
            last_refresh=datetime.utcnow()
        )

    def _generate_financial_metrics(
        self,
        start_date: date,
        end_date: date
    ) -> FinancialMetrics:
        """Generate financial metrics."""
        # Simulated data - would query actual financial systems
        revenue = 15_250_000.0
        costs = 12_450_000.0

        # Historical data for trends
        revenue_history = [14_800_000, 14_950_000, 15_100_000, 15_050_000, 15_200_000, 15_250_000]

        return FinancialMetrics(
            total_revenue=self._create_kpi(revenue, "USD", "currency", 15_000_000),
            total_costs=self._create_kpi(costs, "USD", "currency", 12_000_000),
            gross_margin=self._create_kpi(18.36, "%", "percentage", 20.0),
            operating_margin=self._create_kpi(12.5, "%", "percentage", 15.0),
            net_margin=self._create_kpi(8.2, "%", "percentage", 10.0),
            ar_days=self._create_kpi(42.0, "days", "number", 45.0),
            collection_rate=self._create_kpi(96.5, "%", "percentage", 95.0),
            denial_rate=self._create_kpi(8.2, "%", "percentage", 5.0),
            revenue_per_patient=self._create_kpi(2850.0, "USD", "currency", 2500.0),
            cost_per_patient=self._create_kpi(2325.0, "USD", "currency", 2200.0),
            revenue_trend=self._calculate_trend(
                revenue, revenue_history[-2], revenue_history
            ),
            payer_mix={
                "Medicare": 42.0,
                "Medicaid": 18.0,
                "Commercial": 32.0,
                "Self-Pay": 8.0
            },
            revenue_by_service_line={
                "Inpatient": 45.0,
                "Outpatient": 30.0,
                "Emergency": 15.0,
                "Ambulatory": 10.0
            }
        )

    def _generate_clinical_metrics(
        self,
        start_date: date,
        end_date: date
    ) -> ClinicalMetrics:
        """Generate clinical metrics."""
        patient_count = 5350
        patient_history = [5100, 5200, 5180, 5280, 5320, 5350]
        readmission_history = [13.5, 14.0, 13.8, 13.2, 12.9, 12.5]

        return ClinicalMetrics(
            total_patients=self._create_kpi(patient_count, "patients", "number", 5000),
            total_encounters=self._create_kpi(12500, "encounters", "number", 12000),
            readmission_rate_30day=self._create_kpi(12.5, "%", "percentage", 15.0),
            mortality_rate=self._create_kpi(1.8, "%", "percentage", 2.0),
            infection_rate=self._create_kpi(0.85, "%", "percentage", 1.0),
            complication_rate=self._create_kpi(3.2, "%", "percentage", 4.0),
            average_los=self._create_kpi(4.2, "days", "number", 4.5),
            emergency_visits=self._create_kpi(2850, "visits", "number"),
            patient_safety_score=self._create_kpi(92.5, "%", "percentage", 90.0),
            quality_composite_score=self._create_kpi(88.5, "%", "percentage", 85.0),
            patient_trend=self._calculate_trend(
                patient_count, patient_history[-2], patient_history
            ),
            readmission_trend=self._calculate_trend(
                12.5, readmission_history[-2], readmission_history
            )
        )

    def _generate_operational_metrics(
        self,
        start_date: date,
        end_date: date
    ) -> OperationalMetrics:
        """Generate operational metrics."""
        occupancy_history = [78.0, 80.0, 82.0, 81.0, 83.0, 85.0]
        wait_time_history = [38.0, 40.0, 42.0, 39.0, 37.0, 35.0]

        return OperationalMetrics(
            bed_occupancy_rate=self._create_kpi(85.0, "%", "percentage", 80.0),
            or_utilization=self._create_kpi(78.5, "%", "percentage", 75.0),
            er_wait_time=self._create_kpi(35.0, "minutes", "number", 45.0),
            door_to_provider_time=self._create_kpi(22.0, "minutes", "number", 30.0),
            patient_throughput=self._create_kpi(125, "patients/day", "number", 120),
            staff_productivity=self._create_kpi(92.0, "%", "percentage", 90.0),
            appointment_utilization=self._create_kpi(88.5, "%", "percentage", 85.0),
            no_show_rate=self._create_kpi(8.5, "%", "percentage", 10.0),
            average_turnaround_time=self._create_kpi(45.0, "minutes", "number", 60.0),
            resource_utilization=self._create_kpi(82.0, "%", "percentage", 80.0),
            occupancy_trend=self._calculate_trend(85.0, occupancy_history[-2], occupancy_history),
            wait_time_trend=self._calculate_trend(35.0, wait_time_history[-2], wait_time_history)
        )

    def _generate_quality_metrics(
        self,
        start_date: date,
        end_date: date
    ) -> QualityMetrics:
        """Generate quality metrics."""
        satisfaction_history = [82.0, 83.0, 84.0, 85.0, 86.0, 87.5]

        return QualityMetrics(
            patient_satisfaction_score=self._create_kpi(87.5, "%", "percentage", 85.0),
            nps_score=self._create_kpi(62.0, "NPS", "number", 50.0),
            hcahps_score=self._create_kpi(78.0, "%", "percentage", 75.0),
            complaint_rate=self._create_kpi(2.5, "%", "percentage", 3.0),
            grievance_rate=self._create_kpi(0.8, "%", "percentage", 1.0),
            quality_score=self._create_kpi(91.0, "%", "percentage", 90.0),
            safety_score=self._create_kpi(94.0, "%", "percentage", 92.0),
            compliance_rate=self._create_kpi(98.5, "%", "percentage", 95.0),
            satisfaction_trend=self._calculate_trend(
                87.5, satisfaction_history[-2], satisfaction_history
            ),
            satisfaction_breakdown={
                "Very Satisfied": 45.0,
                "Satisfied": 35.0,
                "Neutral": 12.0,
                "Dissatisfied": 5.0,
                "Very Dissatisfied": 3.0
            }
        )

    def _generate_benchmark_comparisons(
        self,
        financial: FinancialMetrics,
        clinical: ClinicalMetrics,
        operational: OperationalMetrics,
        quality: QualityMetrics
    ) -> List[BenchmarkComparison]:
        """Generate benchmark comparisons."""
        comparisons = []

        metrics_to_benchmark = [
            ("Readmission Rate", clinical.readmission_rate_30day.value, "readmission_rate", True),
            ("Mortality Rate", clinical.mortality_rate.value, "mortality_rate", True),
            ("Infection Rate", clinical.infection_rate.value, "infection_rate", True),
            ("Bed Occupancy", operational.bed_occupancy_rate.value, "bed_occupancy", False),
            ("ER Wait Time", operational.er_wait_time.value, "er_wait_time", True),
            ("Patient Satisfaction", quality.patient_satisfaction_score.value, "patient_satisfaction", False),
            ("AR Days", financial.ar_days.value, "ar_days", True),
            ("Collection Rate", financial.collection_rate.value, "collection_rate", False),
        ]

        for name, current, benchmark_key, lower_is_better in metrics_to_benchmark:
            benchmark = self.benchmarks.get(benchmark_key, {})
            benchmark_value = benchmark.get("value", 0)
            benchmark_source = benchmark.get("source", "Industry Average")

            variance = current - benchmark_value
            variance_pct = ((current - benchmark_value) / benchmark_value * 100) if benchmark_value else 0

            # Determine performance level
            if lower_is_better:
                if variance_pct <= -20:
                    level = PerformanceLevel.EXCEEDING
                elif variance_pct <= 0:
                    level = PerformanceLevel.MEETING
                elif variance_pct <= 20:
                    level = PerformanceLevel.BELOW
                else:
                    level = PerformanceLevel.CRITICAL
                percentile = max(0, min(100, 100 - int(50 + variance_pct)))
            else:
                if variance_pct >= 20:
                    level = PerformanceLevel.EXCEEDING
                elif variance_pct >= 0:
                    level = PerformanceLevel.MEETING
                elif variance_pct >= -20:
                    level = PerformanceLevel.BELOW
                else:
                    level = PerformanceLevel.CRITICAL
                percentile = max(0, min(100, int(50 + variance_pct)))

            comparisons.append(BenchmarkComparison(
                metric_name=name,
                current_value=current,
                benchmark_value=benchmark_value,
                benchmark_source=benchmark_source,
                percentile_rank=percentile,
                variance=variance,
                variance_percentage=variance_pct,
                performance_level=level
            ))

        return comparisons

    def _generate_alerts(
        self,
        financial: FinancialMetrics,
        clinical: ClinicalMetrics,
        operational: OperationalMetrics,
        quality: QualityMetrics
    ) -> List[Dict[str, Any]]:
        """Generate alerts for KPIs that need attention."""
        alerts = []

        # Check for critical performance levels
        for metric_name, kpi in [
            ("Denial Rate", financial.denial_rate),
            ("Readmission Rate", clinical.readmission_rate_30day),
            ("Infection Rate", clinical.infection_rate),
            ("ER Wait Time", operational.er_wait_time),
            ("No-Show Rate", operational.no_show_rate),
        ]:
            if kpi.performance_level == PerformanceLevel.CRITICAL:
                alerts.append({
                    "level": "critical",
                    "metric": metric_name,
                    "message": f"{metric_name} is critically below target",
                    "current": kpi.formatted,
                    "target": kpi.target_formatted,
                    "variance": f"{kpi.variance_percentage:.1f}%",
                    "timestamp": datetime.utcnow().isoformat()
                })
            elif kpi.performance_level == PerformanceLevel.BELOW:
                alerts.append({
                    "level": "warning",
                    "metric": metric_name,
                    "message": f"{metric_name} is below target",
                    "current": kpi.formatted,
                    "target": kpi.target_formatted,
                    "variance": f"{kpi.variance_percentage:.1f}%",
                    "timestamp": datetime.utcnow().isoformat()
                })

        return alerts

    async def get_department_performance(
        self,
        facility_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> List[DepartmentPerformance]:
        """Get performance metrics by department."""
        # Simulated department data
        departments = [
            DepartmentPerformance(
                department_id="dept-001",
                department_name="Emergency",
                efficiency_score=88.5,
                quality_score=92.0,
                satisfaction_score=85.0,
                patient_volume=2850,
                revenue=4_500_000,
                cost=3_800_000,
                margin=15.6,
                trend=MetricTrend.IMPROVING
            ),
            DepartmentPerformance(
                department_id="dept-002",
                department_name="Surgery",
                efficiency_score=92.0,
                quality_score=95.0,
                satisfaction_score=90.0,
                patient_volume=1200,
                revenue=6_200_000,
                cost=4_900_000,
                margin=21.0,
                trend=MetricTrend.STABLE
            ),
            DepartmentPerformance(
                department_id="dept-003",
                department_name="Cardiology",
                efficiency_score=85.0,
                quality_score=91.0,
                satisfaction_score=88.0,
                patient_volume=980,
                revenue=3_800_000,
                cost=3_100_000,
                margin=18.4,
                trend=MetricTrend.IMPROVING
            ),
            DepartmentPerformance(
                department_id="dept-004",
                department_name="Oncology",
                efficiency_score=90.0,
                quality_score=93.0,
                satisfaction_score=92.0,
                patient_volume=650,
                revenue=4_100_000,
                cost=3_400_000,
                margin=17.1,
                trend=MetricTrend.STABLE
            ),
            DepartmentPerformance(
                department_id="dept-005",
                department_name="Pediatrics",
                efficiency_score=87.0,
                quality_score=94.0,
                satisfaction_score=95.0,
                patient_volume=1500,
                revenue=2_200_000,
                cost=1_800_000,
                margin=18.2,
                trend=MetricTrend.DECLINING
            ),
        ]

        return departments

    async def get_provider_performance(
        self,
        department_id: Optional[str] = None,
        facility_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> List[ProviderPerformance]:
        """Get performance metrics by provider."""
        # Simulated provider data
        providers = [
            ProviderPerformance(
                provider_id="prov-001",
                provider_name="Dr. Sarah Johnson",
                specialty="Cardiology",
                patient_volume=180,
                quality_score=95.0,
                satisfaction_score=92.0,
                productivity_score=88.0,
                revenue_generated=450_000,
                avg_encounter_duration=35.0,
                readmission_rate=8.5
            ),
            ProviderPerformance(
                provider_id="prov-002",
                provider_name="Dr. Michael Chen",
                specialty="Surgery",
                patient_volume=120,
                quality_score=97.0,
                satisfaction_score=90.0,
                productivity_score=92.0,
                revenue_generated=680_000,
                avg_encounter_duration=45.0,
                readmission_rate=5.2
            ),
            ProviderPerformance(
                provider_id="prov-003",
                provider_name="Dr. Emily Williams",
                specialty="Emergency Medicine",
                patient_volume=450,
                quality_score=91.0,
                satisfaction_score=85.0,
                productivity_score=95.0,
                revenue_generated=380_000,
                avg_encounter_duration=22.0,
                readmission_rate=12.0
            ),
        ]

        return providers

    async def get_kpi_drill_down(
        self,
        kpi_name: str,
        start_date: date,
        end_date: date,
        dimensions: List[str],
        facility_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get detailed drill-down data for a specific KPI.

        Args:
            kpi_name: Name of the KPI to drill down
            start_date: Start date for analysis
            end_date: End date for analysis
            dimensions: Dimensions to break down by (e.g., department, provider, time)
            facility_id: Optional facility filter
            tenant_id: Tenant ID

        Returns:
            Detailed breakdown data for the KPI
        """
        return {
            "kpi_name": kpi_name,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "summary": {
                "current_value": 12.5,
                "previous_value": 13.2,
                "change": -0.7,
                "change_percentage": -5.3
            },
            "breakdown_by_dimension": {
                dim: self._generate_dimension_breakdown(kpi_name, dim)
                for dim in dimensions
            },
            "time_series": self._generate_time_series(kpi_name, start_date, end_date),
            "contributing_factors": [
                {"factor": "Improved discharge planning", "impact": -2.0},
                {"factor": "Care coordination program", "impact": -1.5},
                {"factor": "Patient education", "impact": -0.8},
            ]
        }

    def _generate_dimension_breakdown(
        self,
        kpi_name: str,
        dimension: str
    ) -> List[Dict[str, Any]]:
        """Generate breakdown by a dimension."""
        if dimension == "department":
            return [
                {"name": "Emergency", "value": 15.2, "volume": 850},
                {"name": "Cardiology", "value": 12.8, "volume": 320},
                {"name": "Surgery", "value": 8.5, "volume": 280},
                {"name": "Medicine", "value": 11.2, "volume": 520},
            ]
        elif dimension == "provider":
            return [
                {"name": "Dr. Johnson", "value": 10.5, "volume": 120},
                {"name": "Dr. Chen", "value": 8.2, "volume": 95},
                {"name": "Dr. Williams", "value": 14.8, "volume": 180},
            ]
        elif dimension == "payer":
            return [
                {"name": "Medicare", "value": 14.5, "volume": 580},
                {"name": "Medicaid", "value": 16.2, "volume": 290},
                {"name": "Commercial", "value": 9.8, "volume": 420},
                {"name": "Self-Pay", "value": 11.0, "volume": 150},
            ]
        return []

    def _generate_time_series(
        self,
        kpi_name: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Generate time series data."""
        days = (end_date - start_date).days
        series = []

        base_value = 12.5
        for i in range(min(days, 30)):
            current_date = start_date + timedelta(days=i)
            # Simulated variation
            value = base_value + (i % 5 - 2) * 0.5
            series.append({
                "date": current_date.isoformat(),
                "value": round(value, 1)
            })

        return series


# Global service instance
executive_dashboard_service = ExecutiveDashboardService()
