"""
Analytics Module Schemas
Request/Response models for analytics and reporting
"""
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum


# ==================== Enums ====================

class TimePeriod(str, Enum):
    """Time period for analytics queries"""
    TODAY = "today"
    YESTERDAY = "yesterday"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    THIS_WEEK = "this_week"
    LAST_WEEK = "last_week"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    THIS_QUARTER = "this_quarter"
    LAST_QUARTER = "last_quarter"
    THIS_YEAR = "this_year"
    CUSTOM = "custom"


class MetricCategory(str, Enum):
    """Category of metrics"""
    APPOINTMENTS = "appointments"
    JOURNEYS = "journeys"
    COMMUNICATION = "communication"
    VOICE_CALLS = "voice_calls"
    PATIENTS = "patients"
    PERFORMANCE = "performance"


class AggregationLevel(str, Enum):
    """Aggregation level for time-series data"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ExportFormat(str, Enum):
    """Export format for reports"""
    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"
    JSON = "json"


# ==================== Request Schemas ====================

class AnalyticsQueryRequest(BaseModel):
    """Base request for analytics queries"""
    tenant_id: UUID
    time_period: TimePeriod = TimePeriod.LAST_30_DAYS
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    aggregation: AggregationLevel = AggregationLevel.DAILY

    # Filters
    department_id: Optional[UUID] = None
    practitioner_id: Optional[UUID] = None
    location_id: Optional[UUID] = None


class AppointmentAnalyticsRequest(AnalyticsQueryRequest):
    """Request for appointment analytics"""
    channel_origin: Optional[str] = None  # whatsapp, phone, web, voice_agent
    include_breakdown: bool = True  # Include breakdowns by status, channel, etc.


class JourneyAnalyticsRequest(AnalyticsQueryRequest):
    """Request for journey analytics"""
    journey_id: Optional[UUID] = None
    journey_type: Optional[str] = None  # opd, ipd, procedure, chronic_care, wellness
    include_stage_details: bool = True


class CommunicationAnalyticsRequest(AnalyticsQueryRequest):
    """Request for communication analytics"""
    channel_type: Optional[str] = None  # whatsapp, sms, email, phone
    direction: Optional[str] = None  # inbound, outbound
    include_sentiment: bool = True


class VoiceCallAnalyticsRequest(AnalyticsQueryRequest):
    """Request for voice call analytics"""
    call_type: Optional[str] = None  # inbound, outbound
    detected_intent: Optional[str] = None
    include_quality_metrics: bool = True


class ReportRequest(BaseModel):
    """Request to generate a report"""
    tenant_id: UUID
    report_type: MetricCategory
    time_period: TimePeriod
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    format: ExportFormat = ExportFormat.PDF

    # Filters
    filters: Dict[str, Any] = Field(default_factory=dict)

    # Email options
    send_email: bool = False
    email_recipients: List[str] = Field(default_factory=list)


# ==================== Response Schemas ====================

class TimeSeriesDataPoint(BaseModel):
    """Single data point in time series"""
    date: date
    hour: Optional[int] = None  # For hourly aggregation
    value: float
    label: Optional[str] = None


class AppointmentMetrics(BaseModel):
    """Appointment metrics snapshot"""
    total_appointments: int
    scheduled: int
    confirmed: int
    completed: int
    canceled: int
    no_show: int
    rescheduled: int

    # Rates (percentages)
    no_show_rate: float
    completion_rate: float
    cancellation_rate: float

    # Time series
    trend: List[TimeSeriesDataPoint] = Field(default_factory=list)


class AppointmentBreakdown(BaseModel):
    """Breakdown of appointments by dimension"""
    by_channel: Dict[str, int] = Field(default_factory=dict)
    by_practitioner: Dict[str, int] = Field(default_factory=dict)
    by_department: Dict[str, int] = Field(default_factory=dict)
    by_location: Dict[str, int] = Field(default_factory=dict)
    by_hour_of_day: Dict[int, int] = Field(default_factory=dict)
    by_day_of_week: Dict[int, int] = Field(default_factory=dict)


class AppointmentAnalyticsResponse(BaseModel):
    """Complete appointment analytics response"""
    summary: AppointmentMetrics
    breakdown: Optional[AppointmentBreakdown] = None
    time_period: str
    start_date: date
    end_date: date


class JourneyMetrics(BaseModel):
    """Journey metrics snapshot"""
    total_active: int
    completed: int
    paused: int
    canceled: int
    new_started: int

    # Progress metrics
    avg_completion_percentage: float
    overdue_steps: int
    total_steps_completed: int
    avg_steps_per_journey: float

    # Time series
    trend: List[TimeSeriesDataPoint] = Field(default_factory=list)


class JourneyBreakdown(BaseModel):
    """Breakdown of journeys by dimension"""
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_department: Dict[str, int] = Field(default_factory=dict)
    by_stage: Dict[str, int] = Field(default_factory=dict)


class JourneyAnalyticsResponse(BaseModel):
    """Complete journey analytics response"""
    summary: JourneyMetrics
    breakdown: Optional[JourneyBreakdown] = None
    time_period: str
    start_date: date
    end_date: date


class CommunicationMetrics(BaseModel):
    """Communication metrics snapshot"""
    total_messages: int
    total_conversations: int
    new_conversations: int
    closed_conversations: int

    # Response metrics
    avg_response_time_seconds: float
    median_response_time_seconds: float
    response_rate_percentage: float

    # Engagement
    avg_messages_per_conversation: float
    avg_conversation_duration_hours: float

    # Sentiment (counts)
    positive_sentiment: int
    neutral_sentiment: int
    negative_sentiment: int

    # Time series
    trend: List[TimeSeriesDataPoint] = Field(default_factory=list)


class CommunicationBreakdown(BaseModel):
    """Breakdown of communication by dimension"""
    by_channel: Dict[str, int] = Field(default_factory=dict)
    by_direction: Dict[str, int] = Field(default_factory=dict)
    by_hour_of_day: Dict[int, int] = Field(default_factory=dict)
    by_sentiment: Dict[str, int] = Field(default_factory=dict)


class CommunicationAnalyticsResponse(BaseModel):
    """Complete communication analytics response"""
    summary: CommunicationMetrics
    breakdown: Optional[CommunicationBreakdown] = None
    time_period: str
    start_date: date
    end_date: date


class VoiceCallMetrics(BaseModel):
    """Voice call metrics snapshot"""
    total_calls: int
    completed_calls: int
    failed_calls: int
    no_answer_calls: int

    # Duration metrics
    avg_call_duration_seconds: float
    median_call_duration_seconds: float
    total_call_minutes: int

    # Quality metrics
    avg_audio_quality: float
    avg_transcription_quality: float
    avg_confidence_score: float

    # Success metrics
    appointments_booked: int
    queries_resolved: int
    transferred_to_human: int

    # Success rates (percentages)
    booking_success_rate: float
    query_resolution_rate: float

    # Time series
    trend: List[TimeSeriesDataPoint] = Field(default_factory=list)


class VoiceCallBreakdown(BaseModel):
    """Breakdown of voice calls by dimension"""
    by_intent: Dict[str, int] = Field(default_factory=dict)
    by_outcome: Dict[str, int] = Field(default_factory=dict)
    by_call_type: Dict[str, int] = Field(default_factory=dict)
    by_hour_of_day: Dict[int, int] = Field(default_factory=dict)


class VoiceCallAnalyticsResponse(BaseModel):
    """Complete voice call analytics response"""
    summary: VoiceCallMetrics
    breakdown: Optional[VoiceCallBreakdown] = None
    time_period: str
    start_date: date
    end_date: date


class PatientMetrics(BaseModel):
    """Patient metrics snapshot"""
    total_patients: int
    new_patients: int
    active_patients: int
    inactive_patients: int

    # Engagement
    avg_appointments_per_patient: float
    avg_messages_per_patient: float
    high_risk_patients: int

    # Demographics breakdown
    by_age_group: Dict[str, int] = Field(default_factory=dict)
    by_gender: Dict[str, int] = Field(default_factory=dict)


class DashboardOverviewResponse(BaseModel):
    """Complete dashboard overview with all metrics"""
    appointments: AppointmentMetrics
    journeys: JourneyMetrics
    communication: CommunicationMetrics
    voice_calls: VoiceCallMetrics
    patients: PatientMetrics

    # Metadata
    generated_at: datetime
    time_period: str
    start_date: date
    end_date: date


class ReportResponse(BaseModel):
    """Response after generating a report"""
    report_id: UUID
    report_type: MetricCategory
    format: ExportFormat
    file_url: Optional[str] = None  # URL to download report
    status: str  # generating, ready, failed
    generated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


# ==================== AI Assistant Tool Schemas ====================

class AIAnalyticsQuery(BaseModel):
    """Natural language analytics query from AI Assistant"""
    tenant_id: UUID
    query: str = Field(..., description="Natural language query (e.g., 'How many appointments were booked last week?')")
    user_id: Optional[UUID] = None  # User asking the question


class AIAnalyticsResponse(BaseModel):
    """Response to AI analytics query"""
    answer: str = Field(..., description="Natural language answer")
    data: Dict[str, Any] = Field(default_factory=dict, description="Structured data used to answer")
    visualization_type: Optional[str] = None  # chart, table, metric_card, etc.
    visualization_data: Optional[Dict[str, Any]] = None


# ==================== Real-time Metrics Schemas ====================

class RealtimeMetric(BaseModel):
    """Real-time metric update"""
    metric_type: str
    metric_name: str
    value: float
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RealtimeMetricsSubscription(BaseModel):
    """Subscription request for real-time metrics"""
    tenant_id: UUID
    metric_categories: List[MetricCategory] = Field(default_factory=list)
    update_interval_seconds: int = Field(30, ge=5, le=300)  # 5s to 5 minutes
