"""
Analytics Service for RPM

Handles trend analysis and population health metrics.

EPIC-019: Remote Patient Monitoring
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
import logging
import statistics

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    DeviceReading, PatientTrendAnalysis, PopulationHealthMetric,
    DataQualityMetric, RPMEnrollment, PatientGoal,
    ReadingType, EnrollmentStatus
)
from ..schemas import (
    TrendAnalysisResponse, PopulationMetricsResponse, DataQualityResponse
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for RPM analytics."""

    # =========================================================================
    # Trend Analysis
    # =========================================================================

    async def analyze_patient_trends(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        patient_id: UUID,
        reading_type: ReadingType,
        period_days: int = 30
    ) -> PatientTrendAnalysis:
        """Analyze trends for a patient's readings."""
        end_date = date.today()
        start_date = end_date - timedelta(days=period_days)

        # Get readings
        result = await db.execute(
            select(DeviceReading).where(
                and_(
                    DeviceReading.tenant_id == tenant_id,
                    DeviceReading.patient_id == patient_id,
                    DeviceReading.reading_type == reading_type,
                    DeviceReading.measured_at >= datetime.combine(start_date, datetime.min.time()),
                    DeviceReading.measured_at <= datetime.combine(end_date, datetime.max.time()),
                    DeviceReading.is_valid == True
                )
            ).order_by(DeviceReading.measured_at)
        )
        readings = result.scalars().all()

        if not readings:
            # No readings, create empty analysis
            analysis = PatientTrendAnalysis(
                tenant_id=tenant_id,
                patient_id=patient_id,
                reading_type=reading_type,
                analysis_date=end_date,
                period_days=period_days,
                reading_count=0
            )
            db.add(analysis)
            await db.commit()
            await db.refresh(analysis)
            return analysis

        values = [r.value for r in readings]

        # Calculate statistics
        avg_value = statistics.mean(values)
        min_value = min(values)
        max_value = max(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0

        # Calculate trend
        trend_direction, trend_slope = self._calculate_trend(readings)

        # Get baseline (first week average)
        baseline_end = start_date + timedelta(days=7)
        baseline_readings = [
            r.value for r in readings
            if r.measured_at.date() <= baseline_end
        ]
        baseline_value = (
            statistics.mean(baseline_readings)
            if baseline_readings else avg_value
        )
        baseline_deviation = (
            ((avg_value - baseline_value) / baseline_value * 100)
            if baseline_value else 0
        )

        # Check goal adherence
        goal_result = await db.execute(
            select(PatientGoal).where(
                and_(
                    PatientGoal.patient_id == patient_id,
                    PatientGoal.reading_type == reading_type,
                    PatientGoal.is_active == True
                )
            ).limit(1)
        )
        goal = goal_result.scalar_one_or_none()

        in_goal_range_percent = None
        if goal:
            in_range_count = 0
            for value in values:
                in_range = True
                if goal.target_low and value < goal.target_low:
                    in_range = False
                if goal.target_high and value > goal.target_high:
                    in_range = False
                if goal.target_value and abs(value - goal.target_value) > goal.target_value * 0.1:
                    in_range = False
                if in_range:
                    in_range_count += 1
            in_goal_range_percent = (in_range_count / len(values) * 100) if values else 0

        # Count anomalies (values > 2 std dev from mean)
        anomaly_count = sum(
            1 for v in values
            if abs(v - avg_value) > 2 * std_dev
        ) if std_dev > 0 else 0

        # Generate AI summary (placeholder)
        ai_summary = self._generate_trend_summary(
            reading_type, avg_value, trend_direction, trend_slope,
            baseline_deviation, in_goal_range_percent
        )

        # Check for existing analysis
        existing_result = await db.execute(
            select(PatientTrendAnalysis).where(
                and_(
                    PatientTrendAnalysis.patient_id == patient_id,
                    PatientTrendAnalysis.reading_type == reading_type,
                    PatientTrendAnalysis.analysis_date == end_date
                )
            )
        )
        analysis = existing_result.scalar_one_or_none()

        if analysis:
            # Update existing
            analysis.reading_count = len(readings)
            analysis.avg_value = avg_value
            analysis.min_value = min_value
            analysis.max_value = max_value
            analysis.std_dev = std_dev
            analysis.trend_direction = trend_direction
            analysis.trend_slope = trend_slope
            analysis.baseline_value = baseline_value
            analysis.baseline_deviation_percent = baseline_deviation
            analysis.in_goal_range_percent = in_goal_range_percent
            analysis.ai_summary = ai_summary
            analysis.anomaly_count = anomaly_count
            analysis.goal_id = goal.id if goal else None
        else:
            # Create new
            analysis = PatientTrendAnalysis(
                tenant_id=tenant_id,
                patient_id=patient_id,
                reading_type=reading_type,
                analysis_date=end_date,
                period_days=period_days,
                reading_count=len(readings),
                avg_value=avg_value,
                min_value=min_value,
                max_value=max_value,
                std_dev=std_dev,
                trend_direction=trend_direction,
                trend_slope=trend_slope,
                baseline_value=baseline_value,
                baseline_deviation_percent=baseline_deviation,
                goal_id=goal.id if goal else None,
                in_goal_range_percent=in_goal_range_percent,
                ai_summary=ai_summary,
                anomaly_count=anomaly_count
            )
            db.add(analysis)

        await db.commit()
        await db.refresh(analysis)
        return analysis

    def _calculate_trend(
        self,
        readings: List[DeviceReading]
    ) -> Tuple[Optional[str], Optional[float]]:
        """Calculate trend direction and slope using linear regression."""
        if len(readings) < 3:
            return None, None

        # Simple linear regression
        n = len(readings)
        x_values = list(range(n))
        y_values = [r.value for r in readings]

        x_mean = sum(x_values) / n
        y_mean = sum(y_values) / n

        numerator = sum(
            (x - x_mean) * (y - y_mean)
            for x, y in zip(x_values, y_values)
        )
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        if denominator == 0:
            return "stable", 0.0

        slope = numerator / denominator

        # Determine direction based on slope significance
        if abs(slope) < 0.1:  # Threshold for "stable"
            return "stable", slope
        elif slope > 0:
            return "up", slope
        else:
            return "down", slope

    def _generate_trend_summary(
        self,
        reading_type: ReadingType,
        avg_value: float,
        trend_direction: Optional[str],
        trend_slope: Optional[float],
        baseline_deviation: float,
        in_goal_range_percent: Optional[float]
    ) -> str:
        """Generate human-readable trend summary."""
        parts = []

        # Average description
        parts.append(
            f"Average {reading_type.value.replace('_', ' ')}: {avg_value:.1f}"
        )

        # Trend description
        if trend_direction == "up":
            parts.append("Values are trending upward")
        elif trend_direction == "down":
            parts.append("Values are trending downward")
        else:
            parts.append("Values are relatively stable")

        # Baseline comparison
        if abs(baseline_deviation) > 5:
            direction = "higher" if baseline_deviation > 0 else "lower"
            parts.append(
                f"Current values are {abs(baseline_deviation):.1f}% {direction} "
                f"than baseline"
            )

        # Goal adherence
        if in_goal_range_percent is not None:
            if in_goal_range_percent >= 80:
                parts.append(f"Excellent goal adherence ({in_goal_range_percent:.0f}%)")
            elif in_goal_range_percent >= 60:
                parts.append(f"Good goal adherence ({in_goal_range_percent:.0f}%)")
            else:
                parts.append(f"Goal adherence needs improvement ({in_goal_range_percent:.0f}%)")

        return ". ".join(parts) + "."

    async def get_patient_trend(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        patient_id: UUID,
        reading_type: ReadingType,
        analysis_date: Optional[date] = None
    ) -> Optional[PatientTrendAnalysis]:
        """Get existing trend analysis."""
        query = select(PatientTrendAnalysis).where(
            and_(
                PatientTrendAnalysis.tenant_id == tenant_id,
                PatientTrendAnalysis.patient_id == patient_id,
                PatientTrendAnalysis.reading_type == reading_type
            )
        )

        if analysis_date:
            query = query.where(PatientTrendAnalysis.analysis_date == analysis_date)
        else:
            query = query.order_by(PatientTrendAnalysis.analysis_date.desc())

        result = await db.execute(query.limit(1))
        return result.scalar_one_or_none()

    # =========================================================================
    # Population Health Metrics
    # =========================================================================

    async def calculate_population_metrics(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        metric_date: date,
        condition: Optional[str] = None,
        reading_type: Optional[ReadingType] = None
    ) -> PopulationHealthMetric:
        """Calculate population health metrics."""
        # Get active enrollments
        enrollment_query = select(RPMEnrollment).where(
            and_(
                RPMEnrollment.tenant_id == tenant_id,
                RPMEnrollment.status == EnrollmentStatus.ACTIVE
            )
        )

        if condition:
            enrollment_query = enrollment_query.where(
                RPMEnrollment.primary_condition == condition
            )

        enrollments_result = await db.execute(enrollment_query)
        enrollments = enrollments_result.scalars().all()

        total_patients = len(enrollments)
        patient_ids = [e.patient_id for e in enrollments]

        if not patient_ids:
            # Return empty metrics
            metric = PopulationHealthMetric(
                tenant_id=tenant_id,
                metric_date=metric_date,
                condition=condition,
                reading_type=reading_type,
                total_patients=0,
                active_patients=0,
                compliant_patients=0,
                at_goal_patients=0
            )
            db.add(metric)
            await db.commit()
            await db.refresh(metric)
            return metric

        # Calculate metrics
        period_start = metric_date - timedelta(days=30)

        # Active patients (had readings in last 7 days)
        active_result = await db.execute(
            select(func.count(func.distinct(DeviceReading.patient_id))).where(
                and_(
                    DeviceReading.tenant_id == tenant_id,
                    DeviceReading.patient_id.in_(patient_ids),
                    DeviceReading.measured_at >= datetime.combine(
                        metric_date - timedelta(days=7),
                        datetime.min.time()
                    )
                )
            )
        )
        active_patients = active_result.scalar()

        # Compliant patients (16+ days data in last 30)
        compliant_patients = 0
        for patient_id in patient_ids:
            days_result = await db.execute(
                select(func.count(func.distinct(
                    func.date(DeviceReading.measured_at)
                ))).where(
                    and_(
                        DeviceReading.patient_id == patient_id,
                        DeviceReading.measured_at >= datetime.combine(
                            period_start, datetime.min.time()
                        )
                    )
                )
            )
            if days_result.scalar() >= 16:
                compliant_patients += 1

        # At-goal patients
        at_goal_result = await db.execute(
            select(func.count(func.distinct(PatientGoal.patient_id))).where(
                and_(
                    PatientGoal.patient_id.in_(patient_ids),
                    PatientGoal.is_active == True,
                    PatientGoal.is_achieved == True
                )
            )
        )
        at_goal_patients = at_goal_result.scalar()

        # Average readings per patient
        readings_result = await db.execute(
            select(func.count()).select_from(DeviceReading).where(
                and_(
                    DeviceReading.patient_id.in_(patient_ids),
                    DeviceReading.measured_at >= datetime.combine(
                        period_start, datetime.min.time()
                    )
                )
            )
        )
        total_readings = readings_result.scalar()
        avg_readings = total_readings / total_patients if total_patients > 0 else 0

        # Compliance rate
        avg_compliance = (
            compliant_patients / total_patients * 100
            if total_patients > 0 else 0
        )

        # Check for existing metric
        existing_result = await db.execute(
            select(PopulationHealthMetric).where(
                and_(
                    PopulationHealthMetric.tenant_id == tenant_id,
                    PopulationHealthMetric.metric_date == metric_date,
                    PopulationHealthMetric.condition == condition,
                    PopulationHealthMetric.reading_type == reading_type
                )
            )
        )
        metric = existing_result.scalar_one_or_none()

        if metric:
            metric.total_patients = total_patients
            metric.active_patients = active_patients
            metric.compliant_patients = compliant_patients
            metric.at_goal_patients = at_goal_patients
            metric.avg_compliance_rate = avg_compliance
            metric.avg_readings_per_patient = avg_readings
        else:
            metric = PopulationHealthMetric(
                tenant_id=tenant_id,
                metric_date=metric_date,
                condition=condition,
                reading_type=reading_type,
                total_patients=total_patients,
                active_patients=active_patients,
                compliant_patients=compliant_patients,
                at_goal_patients=at_goal_patients,
                avg_compliance_rate=avg_compliance,
                avg_readings_per_patient=avg_readings
            )
            db.add(metric)

        await db.commit()
        await db.refresh(metric)
        return metric

    async def get_population_metrics(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        start_date: date,
        end_date: date,
        condition: Optional[str] = None
    ) -> List[PopulationHealthMetric]:
        """Get population metrics for a date range."""
        query = select(PopulationHealthMetric).where(
            and_(
                PopulationHealthMetric.tenant_id == tenant_id,
                PopulationHealthMetric.metric_date.between(start_date, end_date)
            )
        )

        if condition:
            query = query.where(PopulationHealthMetric.condition == condition)

        query = query.order_by(PopulationHealthMetric.metric_date)
        result = await db.execute(query)
        return list(result.scalars().all())

    # =========================================================================
    # Data Quality
    # =========================================================================

    async def calculate_data_quality(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        patient_id: UUID,
        device_id: Optional[UUID],
        period_start: date,
        period_end: date,
        expected_readings_per_day: int = 1
    ) -> DataQualityMetric:
        """Calculate data quality metrics."""
        days_in_period = (period_end - period_start).days + 1
        expected_readings = days_in_period * expected_readings_per_day

        # Query readings
        reading_query = select(DeviceReading).where(
            and_(
                DeviceReading.tenant_id == tenant_id,
                DeviceReading.patient_id == patient_id,
                DeviceReading.measured_at.between(
                    datetime.combine(period_start, datetime.min.time()),
                    datetime.combine(period_end, datetime.max.time())
                )
            )
        )

        if device_id:
            reading_query = reading_query.where(DeviceReading.device_id == device_id)

        result = await db.execute(reading_query.order_by(DeviceReading.measured_at))
        readings = result.scalars().all()

        actual_readings = len(readings)
        valid_readings = sum(1 for r in readings if r.is_valid)
        flagged_readings = sum(1 for r in readings if not r.is_valid)

        # Days with data
        reading_dates = set(r.measured_at.date() for r in readings)
        days_with_data = len(reading_dates)

        # Calculate gaps
        longest_gap_hours = 0
        intervals = []
        for i in range(1, len(readings)):
            gap = (readings[i].measured_at - readings[i-1].measured_at).total_seconds() / 3600
            intervals.append(gap)
            if gap > longest_gap_hours:
                longest_gap_hours = gap

        avg_interval = statistics.mean(intervals) if intervals else None

        # Compliance rate
        compliance_rate = (
            actual_readings / expected_readings * 100
            if expected_readings > 0 else 0
        )

        # Data quality score (weighted average of factors)
        quality_factors = [
            min(compliance_rate, 100),  # Cap at 100
            (valid_readings / actual_readings * 100) if actual_readings > 0 else 100,
            max(0, 100 - (longest_gap_hours / 24 * 10))  # Penalty for gaps
        ]
        data_quality_score = statistics.mean(quality_factors)

        # Consistency score (based on interval variance)
        if len(intervals) > 1:
            interval_variance = statistics.variance(intervals)
            consistency_score = max(0, 100 - interval_variance)
        else:
            consistency_score = 100

        # Check for existing metric
        existing_result = await db.execute(
            select(DataQualityMetric).where(
                and_(
                    DataQualityMetric.patient_id == patient_id,
                    DataQualityMetric.device_id == device_id,
                    DataQualityMetric.period_start == period_start,
                    DataQualityMetric.period_end == period_end
                )
            )
        )
        metric = existing_result.scalar_one_or_none()

        if metric:
            metric.expected_readings = expected_readings
            metric.actual_readings = actual_readings
            metric.valid_readings = valid_readings
            metric.flagged_readings = flagged_readings
            metric.compliance_rate = compliance_rate
            metric.days_with_data = days_with_data
            metric.longest_gap_hours = longest_gap_hours
            metric.avg_reading_interval_hours = avg_interval
            metric.data_quality_score = data_quality_score
            metric.consistency_score = consistency_score
        else:
            metric = DataQualityMetric(
                tenant_id=tenant_id,
                patient_id=patient_id,
                device_id=device_id,
                period_start=period_start,
                period_end=period_end,
                expected_readings=expected_readings,
                actual_readings=actual_readings,
                valid_readings=valid_readings,
                flagged_readings=flagged_readings,
                compliance_rate=compliance_rate,
                days_with_data=days_with_data,
                longest_gap_hours=longest_gap_hours,
                avg_reading_interval_hours=avg_interval,
                data_quality_score=data_quality_score,
                consistency_score=consistency_score
            )
            db.add(metric)

        await db.commit()
        await db.refresh(metric)
        return metric

    async def get_data_quality(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        patient_id: UUID,
        start_date: date,
        end_date: date
    ) -> List[DataQualityMetric]:
        """Get data quality metrics for a patient."""
        result = await db.execute(
            select(DataQualityMetric).where(
                and_(
                    DataQualityMetric.tenant_id == tenant_id,
                    DataQualityMetric.patient_id == patient_id,
                    DataQualityMetric.period_start >= start_date,
                    DataQualityMetric.period_end <= end_date
                )
            ).order_by(DataQualityMetric.period_start)
        )
        return list(result.scalars().all())
