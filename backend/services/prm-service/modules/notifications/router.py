"""
Notifications Router
API endpoints for notifications and message templates
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime, timedelta
from loguru import logger

from shared.database.connection import get_db

from modules.notifications.schemas import (
    MessageTemplateCreate,
    MessageTemplateUpdate,
    MessageTemplateResponse,
    NotificationSend,
    NotificationSendWithTemplate,
    NotificationResponse,
    BulkNotificationSend,
    BulkNotificationResult,
    TemplateListFilters,
    NotificationListFilters,
    NotificationStatistics,
    TemplateRenderRequest,
    TemplateRenderResponse
)
from modules.notifications.service import NotificationService


router = APIRouter(prefix="/notifications", tags=["Notifications"])


# ==================== Template Management ====================

@router.post("/templates", response_model=MessageTemplateResponse, status_code=201)
async def create_template(
    template_data: MessageTemplateCreate,
    db: Session = Depends(get_db)
):
    """
    Create message template

    Templates support variable substitution using {variable_name} syntax.

    Example template body:
    ```
    Hi {patient_name}! Your appointment with Dr. {practitioner_name}
    is confirmed for {appointment_date} at {appointment_time}.
    ```

    Template names must be unique per channel.
    """
    service = NotificationService(db)

    try:
        template = await service.create_template(template_data)
        return MessageTemplateResponse.from_orm(template)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/templates", response_model=List[MessageTemplateResponse])
async def list_templates(
    channel: str = None,
    category: str = None,
    is_active: bool = None,
    search_query: str = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List message templates with filters

    Filters:
    - channel: whatsapp, sms, email, voice
    - category: appointment, reminder, confirmation, etc.
    - is_active: true/false
    - search_query: Search in name and description

    Pagination:
    - limit: Number of results (1-100, default 50)
    - offset: Skip N results
    """
    try:
        filters = TemplateListFilters(
            channel=channel,
            category=category,
            is_active=is_active,
            search_query=search_query,
            limit=limit,
            offset=offset
        )

        service = NotificationService(db)
        templates = await service.list_templates(filters)

        return [MessageTemplateResponse.from_orm(t) for t in templates]

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/templates/{template_id}", response_model=MessageTemplateResponse)
async def get_template(
    template_id: UUID,
    db: Session = Depends(get_db)
):
    """Get template by ID"""
    service = NotificationService(db)
    template = await service.get_template(template_id)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return MessageTemplateResponse.from_orm(template)


@router.patch("/templates/{template_id}", response_model=MessageTemplateResponse)
async def update_template(
    template_id: UUID,
    update_data: MessageTemplateUpdate,
    db: Session = Depends(get_db)
):
    """
    Update message template

    All fields are optional - only provided fields will be updated.
    """
    service = NotificationService(db)
    template = await service.update_template(template_id, update_data)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return MessageTemplateResponse.from_orm(template)


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete (deactivate) template

    Sets is_active=false. Template is retained for historical records.
    """
    service = NotificationService(db)
    success = await service.delete_template(template_id)

    if not success:
        raise HTTPException(status_code=404, detail="Template not found")

    return {
        "success": True,
        "message": "Template deactivated",
        "template_id": str(template_id)
    }


@router.post("/templates/render", response_model=TemplateRenderResponse)
async def render_template(
    request: TemplateRenderRequest,
    db: Session = Depends(get_db)
):
    """
    Preview template rendering

    Useful for testing templates before sending.
    Returns rendered content and lists any missing variables.
    """
    service = NotificationService(db)

    try:
        result = await service.render_template(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==================== Notification Sending ====================

@router.post("/send", response_model=NotificationResponse, status_code=201)
async def send_notification(
    notification_data: NotificationSend,
    db: Session = Depends(get_db)
):
    """
    Send notification directly (without template)

    Use this when you have the message content ready
    and don't need template rendering.

    For scheduled notifications, set `scheduled_for` to future datetime.

    Channels:
    - whatsapp: Sends via Twilio WhatsApp
    - sms: Sends via Twilio SMS
    - email: Sends via SendGrid (TODO)
    - voice: Sends via Twilio Voice (TODO)
    """
    service = NotificationService(db)

    try:
        notification = await service.send_notification(notification_data)
        return NotificationResponse.from_orm(notification)
    except Exception as e:
        logger.error(f"Error sending notification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to send: {str(e)}")


@router.post("/send-template", response_model=NotificationResponse, status_code=201)
async def send_with_template(
    notification_data: NotificationSendWithTemplate,
    db: Session = Depends(get_db)
):
    """
    Send notification using template

    Process:
    1. Loads template by name
    2. Renders template with provided variables
    3. Sends notification

    Example:
    ```json
    {
      "template_name": "appointment_reminder_24h",
      "channel": "whatsapp",
      "to": "+14155551234",
      "variables": {
        "patient_name": "John Doe",
        "appointment_time": "10:00 AM",
        "practitioner_name": "Smith"
      }
    }
    ```
    """
    service = NotificationService(db)

    try:
        notification = await service.send_with_template(notification_data)
        return NotificationResponse.from_orm(notification)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error sending with template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to send: {str(e)}")


@router.post("/send-bulk", response_model=BulkNotificationResult)
async def send_bulk_notifications(
    bulk_data: BulkNotificationSend,
    db: Session = Depends(get_db)
):
    """
    Send notifications to multiple recipients

    Useful for:
    - Appointment reminders to multiple patients
    - Marketing campaigns
    - System alerts

    Max recipients per request: 1000

    Variables can be:
    - Global (applied to all recipients)
    - Per-recipient (specific to each recipient)

    Example:
    ```json
    {
      "template_name": "appointment_reminder",
      "channel": "whatsapp",
      "recipients": ["+14155551234", "+14155555678"],
      "variables": {
        "clinic_name": "Health Clinic"
      },
      "per_recipient_variables": {
        "+14155551234": {
          "patient_name": "John",
          "appointment_time": "10:00 AM"
        },
        "+14155555678": {
          "patient_name": "Jane",
          "appointment_time": "2:00 PM"
        }
      }
    }
    ```
    """
    service = NotificationService(db)

    try:
        result = await service.send_bulk_notifications(bulk_data)
        return result
    except Exception as e:
        logger.error(f"Error in bulk send: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Bulk send failed: {str(e)}")


# ==================== Notification Management ====================

@router.get("/", response_model=List[NotificationResponse])
async def list_notifications(
    channel: str = None,
    status: str = None,
    to: str = None,
    template_id: UUID = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List notifications with filters

    Filters:
    - channel: whatsapp, sms, email, voice
    - status: queued, sending, sent, delivered, failed
    - to: Filter by recipient
    - template_id: Filter by template used

    Pagination:
    - limit: Number of results (1-100, default 50)
    - offset: Skip N results

    Results ordered by most recent first.
    """
    try:
        filters = NotificationListFilters(
            channel=channel,
            status=status,
            to=to,
            template_id=template_id,
            limit=limit,
            offset=offset
        )

        service = NotificationService(db)
        notifications = await service.list_notifications(filters)

        return [NotificationResponse.from_orm(n) for n in notifications]

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get notification by ID

    Includes delivery status, timestamps, and error messages if failed.
    """
    service = NotificationService(db)
    notification = await service.get_notification(notification_id)

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    return NotificationResponse.from_orm(notification)


# ==================== Statistics ====================

@router.get("/stats/summary", response_model=NotificationStatistics)
async def get_notification_statistics(
    days: int = 30,
    org_id: UUID = None,
    db: Session = Depends(get_db)
):
    """
    Get notification statistics

    Returns statistics for the last N days (default: 30).

    Includes:
    - Total sent, delivered, failed counts
    - Breakdown by channel and status
    - Delivery rate
    - Most used templates
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    service = NotificationService(db)
    stats = await service.get_statistics(
        start_date=start_date,
        end_date=end_date,
        org_id=org_id
    )

    return stats


# ==================== Health Check ====================

@router.get("/health/check")
async def notifications_health_check():
    """Health check for notifications module"""
    from core.twilio_client import twilio_client

    twilio_status = "configured" if twilio_client else "not_configured"

    return {
        "status": "healthy",
        "module": "notifications",
        "channels": {
            "whatsapp": twilio_status,
            "sms": twilio_status,
            "email": "not_configured",  # TODO
            "voice": "not_configured"   # TODO
        },
        "features": [
            "templates",
            "multi_channel",
            "scheduled_sending",
            "bulk_sending",
            "statistics"
        ]
    }
