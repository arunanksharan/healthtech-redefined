"""
Analytics API Router
REST API endpoints for analytics and metrics
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from shared.database.connection import get_db
from .schemas import (
    TimePeriod,
    AppointmentAnalyticsRequest,
    AppointmentAnalyticsResponse,
    JourneyAnalyticsRequest,
    JourneyAnalyticsResponse,
    CommunicationAnalyticsRequest,
    CommunicationAnalyticsResponse,
    VoiceCallAnalyticsRequest,
    VoiceCallAnalyticsResponse,
    DashboardOverviewResponse,
    AIAnalyticsQuery,
    AIAnalyticsResponse,
)
from .service import get_analytics_service


router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ==================== Appointment Analytics ====================

@router.get("/appointments", response_model=AppointmentAnalyticsResponse)
def get_appointment_analytics(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    time_period: TimePeriod = Query(TimePeriod.LAST_30_DAYS, description="Time period"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD) for custom period"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD) for custom period"),
    channel_origin: Optional[str] = Query(None, description="Filter by channel (whatsapp, phone, web, voice_agent)"),
    practitioner_id: Optional[UUID] = Query(None, description="Filter by practitioner"),
    department_id: Optional[UUID] = Query(None, description="Filter by department"),
    location_id: Optional[UUID] = Query(None, description="Filter by location"),
    include_breakdown: bool = Query(True, description="Include breakdowns by dimension"),
    db: Session = Depends(get_db),
):
    """
    Get appointment analytics

    Returns comprehensive appointment metrics including:
    - Total appointments by status
    - Rates (no-show, completion, cancellation)
    - Time series trend
    - Breakdowns by channel, practitioner, hour of day, etc.
    """
    from datetime import date as date_type

    # Parse dates if provided
    start_date_parsed = date_type.fromisoformat(start_date) if start_date else None
    end_date_parsed = date_type.fromisoformat(end_date) if end_date else None

    request = AppointmentAnalyticsRequest(
        tenant_id=tenant_id,
        time_period=time_period,
        start_date=start_date_parsed,
        end_date=end_date_parsed,
        channel_origin=channel_origin,
        practitioner_id=practitioner_id,
        department_id=department_id,
        location_id=location_id,
        include_breakdown=include_breakdown,
    )

    service = get_analytics_service(db)
    return service.get_appointment_analytics(request)


# ==================== Journey Analytics ====================

@router.get("/journeys", response_model=JourneyAnalyticsResponse)
def get_journey_analytics(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    time_period: TimePeriod = Query(TimePeriod.LAST_30_DAYS, description="Time period"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    journey_id: Optional[UUID] = Query(None, description="Filter by specific journey"),
    journey_type: Optional[str] = Query(None, description="Filter by journey type"),
    department_id: Optional[UUID] = Query(None, description="Filter by department"),
    include_stage_details: bool = Query(True, description="Include stage breakdowns"),
    db: Session = Depends(get_db),
):
    """
    Get journey analytics

    Returns journey metrics including:
    - Active, completed, paused, canceled journeys
    - Completion rates and progress
    - Overdue steps
    - Breakdowns by type and stage
    """
    from datetime import date as date_type

    start_date_parsed = date_type.fromisoformat(start_date) if start_date else None
    end_date_parsed = date_type.fromisoformat(end_date) if end_date else None

    request = JourneyAnalyticsRequest(
        tenant_id=tenant_id,
        time_period=time_period,
        start_date=start_date_parsed,
        end_date=end_date_parsed,
        journey_id=journey_id,
        journey_type=journey_type,
        department_id=department_id,
        include_stage_details=include_stage_details,
    )

    service = get_analytics_service(db)
    return service.get_journey_analytics(request)


# ==================== Communication Analytics ====================

@router.get("/communication", response_model=CommunicationAnalyticsResponse)
def get_communication_analytics(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    time_period: TimePeriod = Query(TimePeriod.LAST_30_DAYS, description="Time period"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    channel_type: Optional[str] = Query(None, description="Filter by channel (whatsapp, sms, email)"),
    direction: Optional[str] = Query(None, description="Filter by direction (inbound, outbound)"),
    include_sentiment: bool = Query(True, description="Include sentiment analysis"),
    db: Session = Depends(get_db),
):
    """
    Get communication analytics

    Returns messaging metrics including:
    - Total messages and conversations
    - Response times and rates
    - Conversation duration
    - Sentiment breakdown
    """
    from datetime import date as date_type

    start_date_parsed = date_type.fromisoformat(start_date) if start_date else None
    end_date_parsed = date_type.fromisoformat(end_date) if end_date else None

    request = CommunicationAnalyticsRequest(
        tenant_id=tenant_id,
        time_period=time_period,
        start_date=start_date_parsed,
        end_date=end_date_parsed,
        channel_type=channel_type,
        direction=direction,
        include_sentiment=include_sentiment,
    )

    service = get_analytics_service(db)
    return service.get_communication_analytics(request)


# ==================== Voice Call Analytics ====================

@router.get("/voice-calls", response_model=VoiceCallAnalyticsResponse)
def get_voice_call_analytics(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    time_period: TimePeriod = Query(TimePeriod.LAST_30_DAYS, description="Time period"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    call_type: Optional[str] = Query(None, description="Filter by call type (inbound, outbound)"),
    detected_intent: Optional[str] = Query(None, description="Filter by detected intent"),
    include_quality_metrics: bool = Query(True, description="Include quality metrics"),
    db: Session = Depends(get_db),
):
    """
    Get voice call analytics

    Returns voice agent metrics including:
    - Total calls by status
    - Call duration metrics
    - Audio and transcription quality
    - Booking and resolution success rates
    """
    from datetime import date as date_type

    start_date_parsed = date_type.fromisoformat(start_date) if start_date else None
    end_date_parsed = date_type.fromisoformat(end_date) if end_date else None

    request = VoiceCallAnalyticsRequest(
        tenant_id=tenant_id,
        time_period=time_period,
        start_date=start_date_parsed,
        end_date=end_date_parsed,
        call_type=call_type,
        detected_intent=detected_intent,
        include_quality_metrics=include_quality_metrics,
    )

    service = get_analytics_service(db)
    return service.get_voice_call_analytics(request)


# ==================== Dashboard Overview ====================

@router.get("/dashboard", response_model=DashboardOverviewResponse)
def get_dashboard_overview(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    time_period: TimePeriod = Query(TimePeriod.LAST_30_DAYS, description="Time period"),
    db: Session = Depends(get_db),
):
    """
    Get complete dashboard overview

    Returns all metrics in a single response:
    - Appointment metrics
    - Journey metrics
    - Communication metrics
    - Voice call metrics
    - Patient metrics

    This is optimized for loading the main dashboard.
    """
    service = get_analytics_service(db)
    return service.get_dashboard_overview(tenant_id, time_period)


# ==================== AI-Powered Analytics ====================

@router.post("/query", response_model=AIAnalyticsResponse)
def query_analytics_with_ai(
    query: AIAnalyticsQuery,
    db: Session = Depends(get_db),
):
    """
    Query analytics using natural language

    This endpoint is called by the AI Assistant to answer user questions about metrics.

    Example queries:
    - "How many appointments were booked last week?"
    - "What's our no-show rate this month?"
    - "Show me voice call performance for yesterday"
    """
    # TODO: Implement AI-powered query parsing and execution
    # For now, return a placeholder response

    return AIAnalyticsResponse(
        answer="AI-powered analytics query execution is not yet implemented.",
        data={},
        visualization_type=None,
        visualization_data=None,
    )


# ==================== Real-time Metrics (SSE) ====================

@router.get("/realtime")
async def realtime_metrics_stream(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: Session = Depends(get_db),
):
    """
    Real-time metrics stream using Server-Sent Events (SSE)

    This endpoint streams metric updates every 30 seconds.
    Clients should use EventSource to connect.

    Example client code:
    ```javascript
    const eventSource = new EventSource('/api/v1/analytics/realtime?tenant_id=xxx');
    eventSource.onmessage = (event) => {
      const metrics = JSON.parse(event.data);
      console.log('New metrics:', metrics);
    };
    ```
    """
    from fastapi.responses import StreamingResponse
    import asyncio
    import json

    async def event_generator():
        """Generate SSE events"""
        service = get_analytics_service(db)

        while True:
            try:
                # Get current metrics
                overview = service.get_dashboard_overview(tenant_id, TimePeriod.TODAY)

                # Format as SSE event
                data = overview.dict()
                yield f"data: {json.dumps(data)}\n\n"

                # Wait 30 seconds before next update
                await asyncio.sleep(30)

            except Exception as e:
                # Send error event
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
