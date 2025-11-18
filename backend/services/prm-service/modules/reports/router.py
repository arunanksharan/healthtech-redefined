"""
Reports Router
API endpoints for report generation
"""
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from loguru import logger
import io

from shared.database.connection import get_db
from modules.reports.schemas import (
    ReportRequest,
    ReportResponse,
    ReportFormat,
    ReportType,
    ScheduledReportCreate,
    ScheduledReportResponse
)
from modules.reports.service import ReportService, get_report_service


router = APIRouter(prefix="/reports", tags=["Reports"])


# ==================== Report Generation ====================

@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a report in the specified format (PDF, CSV, or Excel)

    This endpoint:
      1. Fetches analytics data based on report type
      2. Generates report in requested format
      3. Saves to storage
      4. Returns download URL

    Report Types:
      - appointments: Appointment analytics
      - journeys: Journey progress metrics
      - communication: Message and conversation analytics
      - voice_calls: Voice call performance
      - dashboard: Complete overview

    Formats:
      - pdf: Professional PDF report with charts
      - csv: Comma-separated values for data analysis
      - excel: Excel workbook with multiple sheets

    Example request:
    ```json
    {
      "tenant_id": "uuid",
      "report_type": "appointments",
      "format": "pdf",
      "time_period": "last_30_days",
      "include_charts": true,
      "include_breakdown": true,
      "title": "Monthly Appointment Report"
    }
    ```

    Returns:
      - Report metadata with download URL
      - URL expires after 7 days
    """
    service = get_report_service(db)

    try:
        report = await service.generate_report(request)
        return report

    except ValueError as e:
        logger.warning(f"Invalid report request: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate report: {str(e)}"
        )


@router.get("/download/{report_id}")
async def download_report(
    report_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Download a generated report

    This endpoint:
      1. Retrieves report from storage
      2. Returns file with appropriate Content-Type

    Note: In production, this would be replaced with:
      - Pre-signed S3 URLs
      - CloudFront CDN
      - Proper authentication
    """
    # TODO: Implement actual file retrieval from storage
    # For now, return a placeholder
    raise HTTPException(
        status_code=501,
        detail="Report download not yet implemented. Use direct file access or S3 pre-signed URLs."
    )


# ==================== Quick Export Endpoints ====================

@router.post("/export/appointments/csv")
async def export_appointments_csv(
    request: ReportRequest,
    db: Session = Depends(get_db)
):
    """Quick export appointments data as CSV"""
    service = get_report_service(db)

    try:
        request.report_type = ReportType.APPOINTMENTS
        request.format = ReportFormat.CSV

        # Generate CSV directly
        data = await service._fetch_report_data(request)
        csv_content = await service._generate_csv(data, request)

        return StreamingResponse(
            io.BytesIO(csv_content),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=appointments_{request.time_period.value}.csv"
            }
        )

    except Exception as e:
        logger.error(f"CSV export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/dashboard/pdf")
async def export_dashboard_pdf(
    request: ReportRequest,
    db: Session = Depends(get_db)
):
    """Quick export dashboard overview as PDF"""
    service = get_report_service(db)

    try:
        request.report_type = ReportType.DASHBOARD
        request.format = ReportFormat.PDF

        # Generate PDF directly
        data = await service._fetch_report_data(request)
        pdf_content = await service._generate_pdf(data, request)

        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=dashboard_{request.time_period.value}.pdf"
            }
        )

    except Exception as e:
        logger.error(f"PDF export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/all/excel")
async def export_all_excel(
    request: ReportRequest,
    db: Session = Depends(get_db)
):
    """Quick export all metrics as Excel"""
    service = get_report_service(db)

    try:
        request.report_type = ReportType.DASHBOARD
        request.format = ReportFormat.EXCEL

        # Generate Excel directly
        data = await service._fetch_report_data(request)
        excel_content = await service._generate_excel(data, request)

        return StreamingResponse(
            io.BytesIO(excel_content),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=prm_report_{request.time_period.value}.xlsx"
            }
        )

    except Exception as e:
        logger.error(f"Excel export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Scheduled Reports (Future) ====================

@router.post("/scheduled", response_model=ScheduledReportResponse)
async def create_scheduled_report(
    request: ScheduledReportCreate,
    db: Session = Depends(get_db)
):
    """
    Create a scheduled report (runs automatically)

    Schedule Configuration:
      - Use cron expression (e.g., "0 9 * * 1" for every Monday at 9 AM)
      - Specify timezone
      - Configure email recipients or webhook

    Example:
    ```json
    {
      "tenant_id": "uuid",
      "report_type": "appointments",
      "format": "pdf",
      "schedule_cron": "0 9 * * 1",
      "timezone": "America/New_York",
      "time_period": "last_week",
      "email_recipients": ["admin@example.com"],
      "name": "Weekly Appointment Report"
    }
    ```

    Note: This is a placeholder. Full implementation requires:
      - Background job scheduler (Celery, APScheduler)
      - Email service integration
      - Storage for generated reports
    """
    raise HTTPException(
        status_code=501,
        detail="Scheduled reports not yet implemented. Coming soon!"
    )


@router.get("/scheduled", response_model=List[ScheduledReportResponse])
async def list_scheduled_reports(
    tenant_id: UUID,
    db: Session = Depends(get_db)
):
    """List all scheduled reports for a tenant"""
    raise HTTPException(
        status_code=501,
        detail="Scheduled reports not yet implemented. Coming soon!"
    )


@router.delete("/scheduled/{report_id}")
async def delete_scheduled_report(
    report_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a scheduled report"""
    raise HTTPException(
        status_code=501,
        detail="Scheduled reports not yet implemented. Coming soon!"
    )


# ==================== Health Check ====================

@router.get("/health/check")
async def reports_health_check():
    """Health check for reports module"""
    return {
        "status": "healthy",
        "module": "reports",
        "features": [
            "pdf_generation",
            "csv_export",
            "excel_export",
            "scheduled_reports (coming soon)"
        ],
        "supported_formats": ["pdf", "csv", "excel"],
        "supported_report_types": [
            "appointments",
            "journeys",
            "communication",
            "voice_calls",
            "dashboard"
        ]
    }
