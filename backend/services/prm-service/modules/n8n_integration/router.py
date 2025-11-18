"""
n8n Integration Router
Webhook endpoints for n8n workflow callbacks
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from loguru import logger

from shared.database.connection import get_db

from modules.n8n_integration.schemas import (
    IntakeResponsePayload,
    DepartmentTriagePayload,
    BookingResponsePayload,
    N8nCallbackResponse
)
from modules.n8n_integration.service import N8nIntegrationService


router = APIRouter(prefix="/n8n", tags=["n8n Integration"])


# ==================== Intake Flow ====================

@router.post("/intake-response", response_model=N8nCallbackResponse)
async def handle_intake_response(
    payload: IntakeResponsePayload,
    db: Session = Depends(get_db)
):
    """
    Handle callback from n8n intake workflow

    Called by n8n after:
    1. Processing user's message with AI/GPT
    2. Extracting structured data (patient name, symptoms, etc.)
    3. Determining next question to ask

    If `next_question` is empty, intake is complete and department
    triage should be triggered by n8n.
    """
    service = N8nIntegrationService(db)

    result = await service.process_intake_response(payload)

    return result


@router.post("/triage-response", response_model=N8nCallbackResponse)
async def handle_triage_response(
    payload: DepartmentTriagePayload,
    db: Session = Depends(get_db)
):
    """
    Handle callback from n8n department triage workflow

    Called by n8n after:
    1. Intake conversation is complete
    2. AI analyzes chief complaint + symptoms
    3. Determines best department/specialty

    This endpoint:
    1. Saves department to conversation state
    2. Triggers appointment slot finding
    3. Sends available slots to user
    """
    service = N8nIntegrationService(db)

    result = await service.process_department_triage(payload)

    return result


# ==================== Booking Flow ====================

@router.post("/booking-response", response_model=N8nCallbackResponse)
async def handle_booking_response(
    payload: BookingResponsePayload,
    db: Session = Depends(get_db)
):
    """
    Handle booking confirmation/cancellation from n8n

    Called when n8n processes user's slot selection response.

    Actions:
    - confirm_slot: Book the selected slot
    - reject_slots: Find new slots
    - cancel_booking: Cancel entire booking process
    - ambiguous: Send clarification to user
    """
    service = N8nIntegrationService(db)

    result = await service.process_booking_response(payload)

    return result


# ==================== Health Check ====================

@router.get("/health")
async def n8n_health():
    """Health check for n8n integration endpoints"""
    return {
        "status": "healthy",
        "service": "n8n-integration",
        "endpoints": [
            "/intake-response",
            "/triage-response",
            "/booking-response"
        ]
    }
