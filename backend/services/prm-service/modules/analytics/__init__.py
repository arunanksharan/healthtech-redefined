"""
Analytics Module
Comprehensive analytics and reporting for PRM Dashboard
"""
from .router import router
from .service import AnalyticsService, get_analytics_service
from .schemas import (
    TimePeriod,
    MetricCategory,
    AppointmentAnalyticsRequest,
    AppointmentAnalyticsResponse,
    JourneyAnalyticsRequest,
    JourneyAnalyticsResponse,
    CommunicationAnalyticsRequest,
    CommunicationAnalyticsResponse,
    VoiceCallAnalyticsRequest,
    VoiceCallAnalyticsResponse,
    DashboardOverviewResponse,
)

__all__ = [
    "router",
    "AnalyticsService",
    "get_analytics_service",
    "TimePeriod",
    "MetricCategory",
    "AppointmentAnalyticsRequest",
    "AppointmentAnalyticsResponse",
    "JourneyAnalyticsRequest",
    "JourneyAnalyticsResponse",
    "CommunicationAnalyticsRequest",
    "CommunicationAnalyticsResponse",
    "VoiceCallAnalyticsRequest",
    "VoiceCallAnalyticsResponse",
    "DashboardOverviewResponse",
]
