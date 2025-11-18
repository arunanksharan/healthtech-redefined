"""
Reports Schemas
Data models for report generation
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, date
from enum import Enum


class ReportFormat(str, Enum):
    """Report output format"""
    PDF = "pdf"
    CSV = "csv"
    EXCEL = "excel"


class ReportType(str, Enum):
    """Type of report to generate"""
    APPOINTMENTS = "appointments"
    JOURNEYS = "journeys"
    COMMUNICATION = "communication"
    VOICE_CALLS = "voice_calls"
    DASHBOARD = "dashboard"
    CUSTOM = "custom"


class TimePeriod(str, Enum):
    """Time period for report data"""
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


class ReportRequest(BaseModel):
    """Request to generate a report"""
    tenant_id: UUID
    report_type: ReportType
    format: ReportFormat
    time_period: TimePeriod = TimePeriod.LAST_30_DAYS
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    # Filters
    practitioner_id: Optional[UUID] = None
    department: Optional[str] = None
    location_id: Optional[UUID] = None

    # Report customization
    include_charts: bool = True
    include_breakdown: bool = True
    include_trends: bool = True

    # Metadata
    title: Optional[str] = None
    description: Optional[str] = None


class ReportResponse(BaseModel):
    """Response containing generated report"""
    id: UUID
    report_type: str
    format: str
    filename: str
    file_size_bytes: int
    download_url: str
    generated_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True


class ScheduledReportCreate(BaseModel):
    """Create a scheduled report"""
    tenant_id: UUID
    report_type: ReportType
    format: ReportFormat

    # Schedule configuration
    schedule_cron: str = Field(..., description="Cron expression (e.g., '0 9 * * 1' for every Monday at 9 AM)")
    timezone: str = Field(default="UTC", description="Timezone for schedule")

    # Report configuration
    time_period: TimePeriod = TimePeriod.LAST_WEEK
    include_charts: bool = True
    include_breakdown: bool = True

    # Delivery
    email_recipients: List[str] = Field(default_factory=list)
    webhook_url: Optional[str] = None

    # Metadata
    name: str
    description: Optional[str] = None
    is_active: bool = True


class ScheduledReportUpdate(BaseModel):
    """Update a scheduled report"""
    schedule_cron: Optional[str] = None
    timezone: Optional[str] = None
    time_period: Optional[TimePeriod] = None
    email_recipients: Optional[List[str]] = None
    webhook_url: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ScheduledReportResponse(BaseModel):
    """Response for scheduled report"""
    id: UUID
    tenant_id: UUID
    report_type: str
    format: str
    schedule_cron: str
    timezone: str
    time_period: str
    email_recipients: List[str]
    webhook_url: Optional[str]
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]

    class Config:
        from_attributes = True


class ReportExecution(BaseModel):
    """Execution record for a scheduled report"""
    id: UUID
    scheduled_report_id: UUID
    executed_at: datetime
    status: str  # success, failed, partial
    file_url: Optional[str]
    error_message: Optional[str]

    class Config:
        from_attributes = True
