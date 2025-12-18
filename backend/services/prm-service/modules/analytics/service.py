"""
Analytics Service
Business logic for analytics queries and metric computations
Queries REAL data from the database
"""
from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID
from sqlalchemy import func, and_, cast, Date
from sqlalchemy.orm import Session

from shared.database.models import Appointment, Patient
from .schemas import (
    TimePeriod,
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
    """Service for analytics queries and computations - queries REAL data"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== Helper Methods ====================

    def _get_date_range(
        self, time_period: TimePeriod, start_date: Optional[date], end_date: Optional[date]
    ) -> tuple[date, date]:
        """Convert time period to date range"""
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
            start = today - timedelta(days=today.weekday())
            return start, today

        elif time_period == TimePeriod.LAST_WEEK:
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
            # Default to last 30 days
            start = today - timedelta(days=30)
            return start, today

    def _generate_trend_from_db(self, tenant_id: UUID, start_date: date, end_date: date) -> list[TimeSeriesDataPoint]:
        """Generate time series data from real appointments"""
        trend = []
        
        # Query appointments grouped by date
        results = self.db.query(
            cast(Appointment.created_at, Date).label('date'),
            func.count(Appointment.id).label('count')
        ).filter(
            Appointment.tenant_id == tenant_id,
            cast(Appointment.created_at, Date) >= start_date,
            cast(Appointment.created_at, Date) <= end_date
        ).group_by(
            cast(Appointment.created_at, Date)
        ).order_by(
            cast(Appointment.created_at, Date)
        ).all()
        
        # Create a dict for quick lookup
        counts_by_date = {r.date: r.count for r in results}
        
        # Fill in all dates in range
        current = start_date
        while current <= end_date:
            trend.append(TimeSeriesDataPoint(
                date=current,
                value=float(counts_by_date.get(current, 0))
            ))
            current += timedelta(days=1)
        
        return trend[-30:]  # Limit to last 30 data points

    # ==================== Appointment Analytics ====================

    def get_appointment_analytics(
        self, request: AppointmentAnalyticsRequest
    ) -> AppointmentAnalyticsResponse:
        """Get comprehensive appointment analytics from REAL data"""
        start_date, end_date = self._get_date_range(
            request.time_period, request.start_date, request.end_date
        )
        
        # Base query filter
        base_filter = and_(
            Appointment.tenant_id == request.tenant_id,
            cast(Appointment.created_at, Date) >= start_date,
            cast(Appointment.created_at, Date) <= end_date
        )
        
        # Count by status
        total = self.db.query(func.count(Appointment.id)).filter(base_filter).scalar() or 0
        
        status_counts = self.db.query(
            Appointment.status,
            func.count(Appointment.id)
        ).filter(base_filter).group_by(Appointment.status).all()
        
        # Create case-insensitive status dict
        status_dict = {}
        for status, count in status_counts:
            if status:
                status_dict[status.lower()] = status_dict.get(status.lower(), 0) + count
            else:
                status_dict['unknown'] = status_dict.get('unknown', 0) + count
        
        # Map various status names to standard categories
        scheduled = (
            status_dict.get('booked', 0) + 
            status_dict.get('scheduled', 0) +
            status_dict.get('pending', 0)
        )
        confirmed = (
            status_dict.get('checked_in', 0) + 
            status_dict.get('confirmed', 0) +
            status_dict.get('arrived', 0)
        )
        completed = status_dict.get('completed', 0) + status_dict.get('fulfilled', 0)
        canceled = status_dict.get('cancelled', 0) + status_dict.get('canceled', 0)
        no_show = status_dict.get('no_show', 0) + status_dict.get('noshow', 0) + status_dict.get('no-show', 0)
        rescheduled = status_dict.get('rescheduled', 0)
        
        # If no standard statuses found, count unknown/other as scheduled
        if scheduled == 0 and confirmed == 0 and completed == 0 and total > 0:
            # Fallback: treat all appointments as their actual status
            scheduled = status_dict.get('unknown', 0)
        
        # Calculate rates
        no_show_rate = (no_show / total * 100) if total > 0 else 0
        completion_rate = (completed / total * 100) if total > 0 else 0
        cancellation_rate = (canceled / total * 100) if total > 0 else 0

        summary = AppointmentMetrics(
            total_appointments=total,
            scheduled=scheduled,
            confirmed=confirmed,
            completed=completed,
            canceled=canceled,
            no_show=no_show,
            rescheduled=rescheduled,
            no_show_rate=round(no_show_rate, 1),
            completion_rate=round(completion_rate, 1),
            cancellation_rate=round(cancellation_rate, 1),
            trend=self._generate_trend_from_db(request.tenant_id, start_date, end_date)
        )

        breakdown = None
        if request.include_breakdown:
            # Count by channel
            channel_counts = self.db.query(
                Appointment.source_channel,
                func.count(Appointment.id)
            ).filter(base_filter).group_by(Appointment.source_channel).all()
            
            breakdown = AppointmentBreakdown(
                by_channel={c or 'unknown': cnt for c, cnt in channel_counts},
            )

        return AppointmentAnalyticsResponse(
            summary=summary,
            breakdown=breakdown,
            time_period=request.time_period.value,
            start_date=start_date,
            end_date=end_date,
        )

    # ==================== Journey Analytics ====================

    def get_journey_analytics(
        self, request: JourneyAnalyticsRequest
    ) -> JourneyAnalyticsResponse:
        """Get journey analytics (mock for now - no journey tables yet)"""
        start_date, end_date = self._get_date_range(
            request.time_period, request.start_date, request.end_date
        )

        summary = JourneyMetrics(
            total_active=0,
            completed=0,
            paused=0,
            canceled=0,
            new_started=0,
            avg_completion_percentage=0,
            overdue_steps=0,
            total_steps_completed=0,
            avg_steps_per_journey=0,
            trend=[]
        )

        return JourneyAnalyticsResponse(
            summary=summary,
            breakdown=None,
            time_period=request.time_period.value,
            start_date=start_date,
            end_date=end_date,
        )

    # ==================== Communication Analytics ====================

    def get_communication_analytics(
        self, request: CommunicationAnalyticsRequest
    ) -> CommunicationAnalyticsResponse:
        """Get communication analytics (mock for now)"""
        start_date, end_date = self._get_date_range(
            request.time_period, request.start_date, request.end_date
        )

        summary = CommunicationMetrics(
            total_messages=0,
            total_conversations=0,
            new_conversations=0,
            closed_conversations=0,
            avg_response_time_seconds=0,
            median_response_time_seconds=0,
            response_rate_percentage=0,
            avg_messages_per_conversation=0,
            avg_conversation_duration_hours=0,
            positive_sentiment=0,
            neutral_sentiment=0,
            negative_sentiment=0,
            trend=[]
        )

        return CommunicationAnalyticsResponse(
            summary=summary,
            breakdown=None,
            time_period=request.time_period.value,
            start_date=start_date,
            end_date=end_date,
        )

    # ==================== Voice Call Analytics ====================

    def get_voice_call_analytics(
        self, request: VoiceCallAnalyticsRequest
    ) -> VoiceCallAnalyticsResponse:
        """Get voice call analytics (mock for now)"""
        start_date, end_date = self._get_date_range(
            request.time_period, request.start_date, request.end_date
        )

        summary = VoiceCallMetrics(
            total_calls=0,
            completed_calls=0,
            failed_calls=0,
            no_answer_calls=0,
            avg_call_duration_seconds=0,
            median_call_duration_seconds=0,
            total_call_minutes=0,
            avg_audio_quality=0,
            avg_transcription_quality=0,
            avg_confidence_score=0,
            appointments_booked=0,
            queries_resolved=0,
            transferred_to_human=0,
            booking_success_rate=0,
            query_resolution_rate=0,
            trend=[]
        )

        return VoiceCallAnalyticsResponse(
            summary=summary,
            breakdown=None,
            time_period=request.time_period.value,
            start_date=start_date,
            end_date=end_date,
        )

    # ==================== Dashboard Overview ====================

    def get_dashboard_overview(
        self, tenant_id: UUID, time_period: TimePeriod = TimePeriod.LAST_30_DAYS
    ) -> DashboardOverviewResponse:
        """Get complete dashboard overview with REAL data"""
        start_date, end_date = self._get_date_range(time_period, None, None)

        # Get appointment metrics from real data
        appointment_req = AppointmentAnalyticsRequest(
            tenant_id=tenant_id, time_period=time_period, include_breakdown=False
        )
        appointment_metrics = self.get_appointment_analytics(appointment_req).summary

        # Journey metrics (empty for now)
        journey_metrics = JourneyMetrics(
            total_active=0,
            completed=0,
            paused=0,
            canceled=0,
            new_started=0,
            avg_completion_percentage=0,
            overdue_steps=0,
            total_steps_completed=0,
            avg_steps_per_journey=0,
            trend=[]
        )

        # Communication metrics (empty for now)
        communication_metrics = CommunicationMetrics(
            total_messages=0,
            total_conversations=0,
            new_conversations=0,
            closed_conversations=0,
            avg_response_time_seconds=0,
            median_response_time_seconds=0,
            response_rate_percentage=0,
            avg_messages_per_conversation=0,
            avg_conversation_duration_hours=0,
            positive_sentiment=0,
            neutral_sentiment=0,
            negative_sentiment=0,
            trend=[]
        )

        # Voice call metrics (empty for now)
        voice_call_metrics = VoiceCallMetrics(
            total_calls=0,
            completed_calls=0,
            failed_calls=0,
            no_answer_calls=0,
            avg_call_duration_seconds=0,
            median_call_duration_seconds=0,
            total_call_minutes=0,
            avg_audio_quality=0,
            avg_transcription_quality=0,
            avg_confidence_score=0,
            appointments_booked=0,
            queries_resolved=0,
            transferred_to_human=0,
            booking_success_rate=0,
            query_resolution_rate=0,
            trend=[]
        )

        # Get REAL patient metrics
        total_patients = self.db.query(func.count(Patient.id)).filter(
            Patient.tenant_id == tenant_id
        ).scalar() or 0
        
        # Count patients created in last 30 days
        new_patients = self.db.query(func.count(Patient.id)).filter(
            Patient.tenant_id == tenant_id,
            Patient.created_at >= datetime.utcnow() - timedelta(days=30)
        ).scalar() or 0
        
        # High risk patients (those with appointments marked as no_show)
        high_risk_count = self.db.query(func.count(func.distinct(Appointment.patient_id))).filter(
            Appointment.tenant_id == tenant_id,
            Appointment.status == 'no_show'
        ).scalar() or 0

        patient_metrics = PatientMetrics(
            total_patients=total_patients,
            new_patients=new_patients,
            active_patients=total_patients,  # All are active for now
            inactive_patients=0,
            avg_appointments_per_patient=0,
            avg_messages_per_patient=0,
            high_risk_patients=high_risk_count,
            by_age_group={},
            by_gender={}
        )

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


# ==================== Service Instance ====================

def get_analytics_service(db: Session) -> AnalyticsService:
    """Get analytics service instance"""
    return AnalyticsService(db)
