"""
Analytics Service
Business logic for analytics queries and metric computations
"""
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from sqlalchemy import and_, func, case, cast, Date
from sqlalchemy.orm import Session

from backend.shared.database.models import (
    Appointment,
    Journey,
    JourneyInstance,
    Patient,
)
from .schemas import (
    TimePeriod,
    AggregationLevel,
    AppointmentAnalyticsRequest,
    AppointmentMetrics,
    AppointmentBreakdown,
    AppointmentAnalyticsResponse,
    JourneyAnalyticsRequest,
    JourneyMetrics,
    JourneyBreakdown,
    JourneyAnalyticsResponse,
    CommunicationAnalyticsRequest,
    CommunicationMetrics,
    CommunicationBreakdown,
    CommunicationAnalyticsResponse,
    VoiceCallAnalyticsRequest,
    VoiceCallMetrics,
    VoiceCallBreakdown,
    VoiceCallAnalyticsResponse,
    TimeSeriesDataPoint,
    DashboardOverviewResponse,
    PatientMetrics,
)


class AnalyticsService:
    """Service for analytics queries and computations"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== Helper Methods ====================

    def _get_date_range(
        self, time_period: TimePeriod, start_date: Optional[date], end_date: Optional[date]
    ) -> Tuple[date, date]:
        """
        Convert time period to date range
        Returns (start_date, end_date) tuple
        """
        today = date.today()

        if time_period == TimePeriod.CUSTOM:
            if not start_date or not end_date:
                raise ValueError("start_date and end_date required for custom time period")
            return start_date, end_date

        elif time_period == TimePeriod.TODAY:
            return today, today

        elif time_period == TimePeriod.YESTERDAY:
            yesterday = today - timedelta(days=1)
            return yesterday, yesterday

        elif time_period == TimePeriod.LAST_7_DAYS:
            start = today - timedelta(days=7)
            return start, today

        elif time_period == TimePeriod.LAST_30_DAYS:
            start = today - timedelta(days=30)
            return start, today

        elif time_period == TimePeriod.THIS_WEEK:
            # Monday to today
            start = today - timedelta(days=today.weekday())
            return start, today

        elif time_period == TimePeriod.LAST_WEEK:
            # Previous Monday to Sunday
            end = today - timedelta(days=today.weekday() + 1)
            start = end - timedelta(days=6)
            return start, end

        elif time_period == TimePeriod.THIS_MONTH:
            start = today.replace(day=1)
            return start, today

        elif time_period == TimePeriod.LAST_MONTH:
            first_this_month = today.replace(day=1)
            end = first_this_month - timedelta(days=1)
            start = end.replace(day=1)
            return start, end

        elif time_period == TimePeriod.THIS_QUARTER:
            quarter = (today.month - 1) // 3
            start = date(today.year, quarter * 3 + 1, 1)
            return start, today

        elif time_period == TimePeriod.LAST_QUARTER:
            quarter = (today.month - 1) // 3
            if quarter == 0:
                # Previous year Q4
                start = date(today.year - 1, 10, 1)
                end = date(today.year - 1, 12, 31)
            else:
                start = date(today.year, (quarter - 1) * 3 + 1, 1)
                end_month = quarter * 3
                end = date(today.year, end_month, 1) - timedelta(days=1)
            return start, end

        elif time_period == TimePeriod.THIS_YEAR:
            start = date(today.year, 1, 1)
            return start, today

        else:
            raise ValueError(f"Unknown time period: {time_period}")

    # ==================== Appointment Analytics ====================

    def get_appointment_analytics(
        self, request: AppointmentAnalyticsRequest
    ) -> AppointmentAnalyticsResponse:
        """Get comprehensive appointment analytics"""

        start_date, end_date = self._get_date_range(
            request.time_period, request.start_date, request.end_date
        )

        # Build base query with filters
        query = self.db.query(Appointment).filter(
            Appointment.tenant_id == request.tenant_id,
            cast(Appointment.created_at, Date) >= start_date,
            cast(Appointment.created_at, Date) <= end_date,
        )

        # Apply filters
        if request.department_id:
            query = query.filter(Appointment.department_id == request.department_id)
        if request.practitioner_id:
            query = query.filter(Appointment.practitioner_id == request.practitioner_id)
        if request.location_id:
            query = query.filter(Appointment.location_id == request.location_id)
        if request.channel_origin:
            query = query.filter(Appointment.channel_origin == request.channel_origin)

        # Get summary metrics
        summary = self._compute_appointment_metrics(query, start_date, end_date)

        # Get breakdown if requested
        breakdown = None
        if request.include_breakdown:
            breakdown = self._compute_appointment_breakdown(query)

        return AppointmentAnalyticsResponse(
            summary=summary,
            breakdown=breakdown,
            time_period=request.time_period.value,
            start_date=start_date,
            end_date=end_date,
        )

    def _compute_appointment_metrics(
        self, query, start_date: date, end_date: date
    ) -> AppointmentMetrics:
        """Compute appointment summary metrics"""

        # Count by status
        status_counts = (
            query.with_entities(
                Appointment.status, func.count(Appointment.id).label("count")
            )
            .group_by(Appointment.status)
            .all()
        )

        status_dict = {status: count for status, count in status_counts}

        total = sum(status_dict.values())
        scheduled = status_dict.get("scheduled", 0)
        confirmed = status_dict.get("confirmed", 0)
        completed = status_dict.get("completed", 0)
        canceled = status_dict.get("canceled", 0)
        no_show = status_dict.get("no_show", 0)
        rescheduled = status_dict.get("rescheduled", 0)

        # Calculate rates
        no_show_rate = (no_show / total * 100) if total > 0 else 0.0
        completion_rate = (completed / total * 100) if total > 0 else 0.0
        cancellation_rate = (canceled / total * 100) if total > 0 else 0.0

        # Get time series trend (daily aggregation)
        trend_data = (
            query.with_entities(
                cast(Appointment.created_at, Date).label("date"),
                func.count(Appointment.id).label("count"),
            )
            .group_by(cast(Appointment.created_at, Date))
            .order_by(cast(Appointment.created_at, Date))
            .all()
        )

        trend = [
            TimeSeriesDataPoint(date=d, value=float(count)) for d, count in trend_data
        ]

        return AppointmentMetrics(
            total_appointments=total,
            scheduled=scheduled,
            confirmed=confirmed,
            completed=completed,
            canceled=canceled,
            no_show=no_show,
            rescheduled=rescheduled,
            no_show_rate=round(no_show_rate, 2),
            completion_rate=round(completion_rate, 2),
            cancellation_rate=round(cancellation_rate, 2),
            trend=trend,
        )

    def _compute_appointment_breakdown(self, query) -> AppointmentBreakdown:
        """Compute appointment breakdowns by various dimensions"""

        # By channel
        by_channel = dict(
            query.with_entities(
                Appointment.channel_origin, func.count(Appointment.id)
            )
            .group_by(Appointment.channel_origin)
            .all()
        )

        # By practitioner (top 10)
        by_practitioner_raw = (
            query.join(Appointment.practitioner)
            .with_entities(
                func.concat(
                    Appointment.practitioner.has(first_name="first_name"),
                    " ",
                    Appointment.practitioner.has(last_name="last_name"),
                ).label("name"),
                func.count(Appointment.id).label("count"),
            )
            .group_by("name")
            .order_by(func.count(Appointment.id).desc())
            .limit(10)
            .all()
        )
        by_practitioner = {name: count for name, count in by_practitioner_raw}

        # By hour of day
        by_hour_raw = (
            query.with_entities(
                func.extract("hour", Appointment.confirmed_start).label("hour"),
                func.count(Appointment.id).label("count"),
            )
            .filter(Appointment.confirmed_start.isnot(None))
            .group_by("hour")
            .all()
        )
        by_hour_of_day = {int(hour): count for hour, count in by_hour_raw}

        # By day of week (0=Monday, 6=Sunday)
        by_dow_raw = (
            query.with_entities(
                func.extract("dow", Appointment.confirmed_start).label("dow"),
                func.count(Appointment.id).label("count"),
            )
            .filter(Appointment.confirmed_start.isnot(None))
            .group_by("dow")
            .all()
        )
        by_day_of_week = {int(dow): count for dow, count in by_dow_raw}

        return AppointmentBreakdown(
            by_channel=by_channel,
            by_practitioner=by_practitioner,
            by_hour_of_day=by_hour_of_day,
            by_day_of_week=by_day_of_week,
        )

    # ==================== Journey Analytics ====================

    def get_journey_analytics(
        self, request: JourneyAnalyticsRequest
    ) -> JourneyAnalyticsResponse:
        """Get comprehensive journey analytics"""

        start_date, end_date = self._get_date_range(
            request.time_period, request.start_date, request.end_date
        )

        # Build base query
        query = self.db.query(JourneyInstance).filter(
            JourneyInstance.tenant_id == request.tenant_id,
            cast(JourneyInstance.created_at, Date) >= start_date,
            cast(JourneyInstance.created_at, Date) <= end_date,
        )

        # Apply filters
        if request.journey_id:
            query = query.filter(JourneyInstance.journey_id == request.journey_id)
        if request.department_id:
            query = query.join(Journey).filter(Journey.department_id == request.department_id)

        # Get summary metrics
        summary = self._compute_journey_metrics(query, start_date, end_date)

        # Get breakdown if requested
        breakdown = None
        if request.include_stage_details:
            breakdown = self._compute_journey_breakdown(query)

        return JourneyAnalyticsResponse(
            summary=summary,
            breakdown=breakdown,
            time_period=request.time_period.value,
            start_date=start_date,
            end_date=end_date,
        )

    def _compute_journey_metrics(
        self, query, start_date: date, end_date: date
    ) -> JourneyMetrics:
        """Compute journey summary metrics"""

        # Count by status
        status_counts = (
            query.with_entities(
                JourneyInstance.status, func.count(JourneyInstance.id)
            )
            .group_by(JourneyInstance.status)
            .all()
        )

        status_dict = {status: count for status, count in status_counts}

        total_active = status_dict.get("active", 0)
        completed = status_dict.get("completed", 0)
        paused = status_dict.get("paused", 0)
        canceled = status_dict.get("cancelled", 0)

        # New journeys started in period
        new_started = query.filter(
            cast(JourneyInstance.started_at, Date) >= start_date,
            cast(JourneyInstance.started_at, Date) <= end_date,
        ).count()

        # Time series trend
        trend_data = (
            query.filter(JourneyInstance.status == "active")
            .with_entities(
                cast(JourneyInstance.created_at, Date).label("date"),
                func.count(JourneyInstance.id).label("count"),
            )
            .group_by(cast(JourneyInstance.created_at, Date))
            .order_by(cast(JourneyInstance.created_at, Date))
            .all()
        )

        trend = [
            TimeSeriesDataPoint(date=d, value=float(count)) for d, count in trend_data
        ]

        return JourneyMetrics(
            total_active=total_active,
            completed=completed,
            paused=paused,
            canceled=canceled,
            new_started=new_started,
            avg_completion_percentage=0.0,  # TODO: Calculate from stage statuses
            overdue_steps=0,  # TODO: Calculate from stage statuses
            total_steps_completed=0,  # TODO: Calculate from stage statuses
            avg_steps_per_journey=0.0,  # TODO: Calculate from stage statuses
            trend=trend,
        )

    def _compute_journey_breakdown(self, query) -> JourneyBreakdown:
        """Compute journey breakdowns by various dimensions"""

        # By journey type
        by_type_raw = (
            query.join(Journey)
            .with_entities(Journey.journey_type, func.count(JourneyInstance.id))
            .group_by(Journey.journey_type)
            .all()
        )
        by_type = {jtype: count for jtype, count in by_type_raw}

        return JourneyBreakdown(by_type=by_type)

    # ==================== Communication Analytics ====================

    def get_communication_analytics(
        self, request: CommunicationAnalyticsRequest
    ) -> CommunicationAnalyticsResponse:
        """Get comprehensive communication analytics"""

        start_date, end_date = self._get_date_range(
            request.time_period, request.start_date, request.end_date
        )

        # For now, return mock data structure
        # TODO: Implement actual queries against conversation_messages table

        summary = CommunicationMetrics(
            total_messages=0,
            total_conversations=0,
            new_conversations=0,
            closed_conversations=0,
            avg_response_time_seconds=0.0,
            median_response_time_seconds=0.0,
            response_rate_percentage=0.0,
            avg_messages_per_conversation=0.0,
            avg_conversation_duration_hours=0.0,
            positive_sentiment=0,
            neutral_sentiment=0,
            negative_sentiment=0,
            trend=[],
        )

        breakdown = CommunicationBreakdown() if request.include_sentiment else None

        return CommunicationAnalyticsResponse(
            summary=summary,
            breakdown=breakdown,
            time_period=request.time_period.value,
            start_date=start_date,
            end_date=end_date,
        )

    # ==================== Voice Call Analytics ====================

    def get_voice_call_analytics(
        self, request: VoiceCallAnalyticsRequest
    ) -> VoiceCallAnalyticsResponse:
        """Get comprehensive voice call analytics"""

        start_date, end_date = self._get_date_range(
            request.time_period, request.start_date, request.end_date
        )

        # For now, return mock data structure
        # TODO: Implement actual queries against voice_calls table

        summary = VoiceCallMetrics(
            total_calls=0,
            completed_calls=0,
            failed_calls=0,
            no_answer_calls=0,
            avg_call_duration_seconds=0.0,
            median_call_duration_seconds=0.0,
            total_call_minutes=0,
            avg_audio_quality=0.0,
            avg_transcription_quality=0.0,
            avg_confidence_score=0.0,
            appointments_booked=0,
            queries_resolved=0,
            transferred_to_human=0,
            booking_success_rate=0.0,
            query_resolution_rate=0.0,
            trend=[],
        )

        breakdown = VoiceCallBreakdown() if request.include_quality_metrics else None

        return VoiceCallAnalyticsResponse(
            summary=summary,
            breakdown=breakdown,
            time_period=request.time_period.value,
            start_date=start_date,
            end_date=end_date,
        )

    # ==================== Dashboard Overview ====================

    def get_dashboard_overview(
        self, tenant_id: UUID, time_period: TimePeriod = TimePeriod.LAST_30_DAYS
    ) -> DashboardOverviewResponse:
        """Get complete dashboard overview with all metrics"""

        start_date, end_date = self._get_date_range(time_period, None, None)

        # Get all metrics
        appointment_req = AppointmentAnalyticsRequest(
            tenant_id=tenant_id, time_period=time_period, include_breakdown=False
        )
        appointment_metrics = self.get_appointment_analytics(appointment_req).summary

        journey_req = JourneyAnalyticsRequest(
            tenant_id=tenant_id, time_period=time_period, include_stage_details=False
        )
        journey_metrics = self.get_journey_analytics(journey_req).summary

        communication_req = CommunicationAnalyticsRequest(
            tenant_id=tenant_id, time_period=time_period, include_sentiment=False
        )
        communication_metrics = self.get_communication_analytics(communication_req).summary

        voice_call_req = VoiceCallAnalyticsRequest(
            tenant_id=tenant_id, time_period=time_period, include_quality_metrics=False
        )
        voice_call_metrics = self.get_voice_call_analytics(voice_call_req).summary

        # Get patient metrics
        patient_metrics = self._get_patient_metrics(tenant_id, start_date, end_date)

        return DashboardOverviewResponse(
            appointments=appointment_metrics,
            journeys=journey_metrics,
            communication=communication_metrics,
            voice_calls=voice_call_metrics,
            patients=patient_metrics,
            generated_at=datetime.utcnow(),
            time_period=time_period.value,
            start_date=start_date,
            end_date=end_date,
        )

    def _get_patient_metrics(
        self, tenant_id: UUID, start_date: date, end_date: date
    ) -> PatientMetrics:
        """Get patient metrics summary"""

        # Total patients
        total_patients = (
            self.db.query(func.count(Patient.id))
            .filter(Patient.tenant_id == tenant_id)
            .scalar()
        )

        # New patients in period
        new_patients = (
            self.db.query(func.count(Patient.id))
            .filter(
                Patient.tenant_id == tenant_id,
                cast(Patient.created_at, Date) >= start_date,
                cast(Patient.created_at, Date) <= end_date,
            )
            .scalar()
        )

        return PatientMetrics(
            total_patients=total_patients or 0,
            new_patients=new_patients or 0,
            active_patients=0,  # TODO: Define "active" criteria
            inactive_patients=0,
            avg_appointments_per_patient=0.0,
            avg_messages_per_patient=0.0,
            high_risk_patients=0,
        )


# ==================== Service Instance ====================

def get_analytics_service(db: Session) -> AnalyticsService:
    """Get analytics service instance"""
    return AnalyticsService(db)
