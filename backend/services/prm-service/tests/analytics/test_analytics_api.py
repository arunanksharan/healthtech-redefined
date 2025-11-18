"""
Tests for Analytics API
Tests analytics endpoints and metrics calculations
"""
import pytest
from datetime import date, timedelta
from uuid import UUID

from modules.analytics.service import AnalyticsService
from modules.analytics.schemas import (
    AnalyticsQueryParams,
    TimePeriod,
    AggregationLevel
)


class TestAnalyticsService:
    """Test suite for AnalyticsService"""

    @pytest.fixture
    def analytics_service(self, db_session):
        """Create analytics service instance"""
        return AnalyticsService(db_session)

    def test_get_appointment_analytics(self, analytics_service, test_org_id):
        """Test fetching appointment analytics"""
        params = AnalyticsQueryParams(
            tenant_id=test_org_id,
            time_period=TimePeriod.LAST_30_DAYS,
            include_breakdown=True
        )

        result = analytics_service.get_appointment_analytics(params)

        assert result is not None
        assert hasattr(result, 'summary')
        assert hasattr(result, 'breakdown')
        assert result.time_period == TimePeriod.LAST_30_DAYS.value

    def test_get_journey_analytics(self, analytics_service, test_org_id):
        """Test fetching journey analytics"""
        params = AnalyticsQueryParams(
            tenant_id=test_org_id,
            time_period=TimePeriod.LAST_7_DAYS,
            include_breakdown=True
        )

        result = analytics_service.get_journey_analytics(params)

        assert result is not None
        assert hasattr(result, 'summary')
        assert hasattr(result.summary, 'total_active')
        assert hasattr(result.summary, 'completed')

    def test_get_communication_analytics(self, analytics_service, test_org_id):
        """Test fetching communication analytics"""
        params = AnalyticsQueryParams(
            tenant_id=test_org_id,
            time_period=TimePeriod.TODAY,
            include_breakdown=True
        )

        result = analytics_service.get_communication_analytics(params)

        assert result is not None
        assert hasattr(result.summary, 'total_messages')
        assert hasattr(result.summary, 'total_conversations')

    def test_get_voice_call_analytics(self, analytics_service, test_org_id):
        """Test fetching voice call analytics"""
        params = AnalyticsQueryParams(
            tenant_id=test_org_id,
            time_period=TimePeriod.LAST_30_DAYS,
            include_breakdown=True
        )

        result = analytics_service.get_voice_call_analytics(params)

        assert result is not None
        assert hasattr(result.summary, 'total_calls')
        assert hasattr(result.summary, 'booking_success_rate')

    def test_get_dashboard_overview(self, analytics_service, test_org_id):
        """Test fetching complete dashboard overview"""
        result = analytics_service.get_dashboard_overview(
            test_org_id,
            TimePeriod.LAST_30_DAYS
        )

        assert result is not None
        assert hasattr(result, 'appointments')
        assert hasattr(result, 'journeys')
        assert hasattr(result, 'communication')
        assert hasattr(result, 'voice_calls')

    def test_custom_date_range(self, analytics_service, test_org_id):
        """Test analytics with custom date range"""
        start_date = date.today() - timedelta(days=14)
        end_date = date.today()

        params = AnalyticsQueryParams(
            tenant_id=test_org_id,
            time_period=TimePeriod.CUSTOM,
            start_date=start_date,
            end_date=end_date
        )

        result = analytics_service.get_appointment_analytics(params)

        assert result.start_date == start_date
        assert result.end_date == end_date

    def test_aggregation_levels(self, analytics_service, test_org_id):
        """Test different aggregation levels"""
        for aggregation in [AggregationLevel.DAILY, AggregationLevel.WEEKLY, AggregationLevel.MONTHLY]:
            params = AnalyticsQueryParams(
                tenant_id=test_org_id,
                time_period=TimePeriod.LAST_30_DAYS,
                aggregation=aggregation
            )

            result = analytics_service.get_appointment_analytics(params)
            assert result is not None

    def test_filtering_by_practitioner(self, analytics_service, test_org_id, test_user_id):
        """Test filtering analytics by practitioner"""
        params = AnalyticsQueryParams(
            tenant_id=test_org_id,
            time_period=TimePeriod.LAST_30_DAYS,
            practitioner_id=test_user_id
        )

        result = analytics_service.get_appointment_analytics(params)
        assert result is not None

    def test_filtering_by_department(self, analytics_service, test_org_id):
        """Test filtering analytics by department"""
        params = AnalyticsQueryParams(
            tenant_id=test_org_id,
            time_period=TimePeriod.LAST_30_DAYS,
            department="Cardiology"
        )

        result = analytics_service.get_journey_analytics(params)
        assert result is not None


class TestAnalyticsMetrics:
    """Test metrics calculation logic"""

    def test_appointment_completion_rate(self, analytics_service, test_org_id):
        """Test appointment completion rate calculation"""
        params = AnalyticsQueryParams(
            tenant_id=test_org_id,
            time_period=TimePeriod.LAST_30_DAYS
        )

        result = analytics_service.get_appointment_analytics(params)

        # Completion rate should be between 0 and 100
        assert 0 <= result.summary.completion_rate <= 100

    def test_no_show_rate(self, analytics_service, test_org_id):
        """Test no-show rate calculation"""
        params = AnalyticsQueryParams(
            tenant_id=test_org_id,
            time_period=TimePeriod.LAST_30_DAYS
        )

        result = analytics_service.get_appointment_analytics(params)

        # No-show rate should be between 0 and 100
        assert 0 <= result.summary.no_show_rate <= 100

    def test_trend_data_structure(self, analytics_service, test_org_id):
        """Test trend data has correct structure"""
        params = AnalyticsQueryParams(
            tenant_id=test_org_id,
            time_period=TimePeriod.LAST_7_DAYS
        )

        result = analytics_service.get_appointment_analytics(params)

        # Trend should be a list
        assert isinstance(result.summary.trend, list)

        # Each point should have date and value
        if result.summary.trend:
            point = result.summary.trend[0]
            assert hasattr(point, 'date')
            assert hasattr(point, 'value')


class TestAnalyticsBreakdown:
    """Test analytics breakdown functionality"""

    def test_breakdown_by_channel(self, analytics_service, test_org_id):
        """Test breakdown by channel"""
        params = AnalyticsQueryParams(
            tenant_id=test_org_id,
            time_period=TimePeriod.LAST_30_DAYS,
            include_breakdown=True
        )

        result = analytics_service.get_appointment_analytics(params)

        if result.breakdown:
            assert isinstance(result.breakdown.by_channel, dict)

    def test_breakdown_by_status(self, analytics_service, test_org_id):
        """Test breakdown by status"""
        params = AnalyticsQueryParams(
            tenant_id=test_org_id,
            time_period=TimePeriod.LAST_30_DAYS,
            include_breakdown=True
        )

        result = analytics_service.get_communication_analytics(params)

        if result.breakdown:
            assert isinstance(result.breakdown.by_status, dict)

    def test_no_breakdown_when_disabled(self, analytics_service, test_org_id):
        """Test no breakdown when include_breakdown is False"""
        params = AnalyticsQueryParams(
            tenant_id=test_org_id,
            time_period=TimePeriod.LAST_30_DAYS,
            include_breakdown=False
        )

        result = analytics_service.get_appointment_analytics(params)

        assert result.breakdown is None


@pytest.mark.asyncio
class TestAnalyticsEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_data(self, analytics_service, test_org_id):
        """Test analytics with no data"""
        params = AnalyticsQueryParams(
            tenant_id=test_org_id,
            time_period=TimePeriod.TODAY
        )

        result = analytics_service.get_appointment_analytics(params)

        # Should return zero metrics, not error
        assert result.summary.total_appointments >= 0

    def test_invalid_date_range(self, analytics_service, test_org_id):
        """Test invalid date range handling"""
        params = AnalyticsQueryParams(
            tenant_id=test_org_id,
            time_period=TimePeriod.CUSTOM,
            start_date=date.today(),
            end_date=date.today() - timedelta(days=7)  # End before start
        )

        with pytest.raises(ValueError):
            analytics_service.get_appointment_analytics(params)

    def test_missing_custom_dates(self, analytics_service, test_org_id):
        """Test custom period without dates"""
        params = AnalyticsQueryParams(
            tenant_id=test_org_id,
            time_period=TimePeriod.CUSTOM
            # Missing start_date and end_date
        )

        with pytest.raises(ValueError):
            analytics_service.get_appointment_analytics(params)
