"""
Voice Agent Webhook Router
API endpoints for receiving Zucol/Zoice webhooks and tool calls
"""
from uuid import UUID
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from backend.shared.database.session import get_db
from shared.auth.webhooks import verify_webhook_secret, verify_api_key
from .schemas import (
    VoiceAgentWebhookRequest,
    VoiceCallWebhookResponse,
    PatientLookupRequest,
    PatientLookupResponse,
    AvailableSlotsRequest,
    AvailableSlotsResponse,
    BookAppointmentRequest,
    BookAppointmentResponse,
)
from .service import get_voice_webhook_service


router = APIRouter(prefix="/voice", tags=["Voice Agent Integration"])


# ==================== Webhook Endpoint ====================

@router.post("/webhook", response_model=VoiceCallWebhookResponse)
def receive_voice_call_webhook(
    webhook: VoiceAgentWebhookRequest,
    x_tenant_id: UUID = Header(..., description="Tenant ID"),
    x_webhook_secret: str = Header(..., description="Webhook secret for verification"),
    db: Session = Depends(get_db),
):
    """
    Receive voice call data from Zucol/Zoice

    This endpoint is called by the Zucol/Zoice platform after a call completes.
    It processes the call data and creates records in the PRM system.

    **Security:**
    - Requires `X-Tenant-Id` header
    - Requires `X-Webhook-Secret` header for verification

    **Processing:**
    1. Identify or create patient from phone number
    2. Create VoiceCall record with transcript and recording
    3. Extract structured data (appointment info, patient info)
    4. Create Conversation thread
    5. Book appointment if intent detected

    **Webhook Configuration in Zucol/Zoice:**
    ```
    URL: https://api.healthtech.com/api/v1/prm/voice/webhook
    Method: POST
    Headers:
      X-Tenant-Id: <your-tenant-id>
      X-Webhook-Secret: <your-secret>
    Environment Variable: ZOICE_WEBHOOK_SECRET=your-secret-key-here
    ```
    """
    # Verify webhook secret
    verify_webhook_secret(
        x_webhook_secret,
        "ZOICE_WEBHOOK_SECRET",
        "Zucol/Zoice"
    )

    service = get_voice_webhook_service(db)
    return service.process_call_webhook(webhook, x_tenant_id)


# ==================== Tool API Endpoints (for Voice Agent to call during call) ====================

@router.post("/tools/patient-lookup", response_model=PatientLookupResponse)
def lookup_patient(
    request: PatientLookupRequest,
    x_api_key: str = Header(..., description="API key for authentication"),
    db: Session = Depends(get_db),
):
    """
    Lookup patient by phone number

    **Called by voice agent during call** to check if patient exists.

    **Example:**
    When patient says their phone number, the voice agent calls this endpoint
    to retrieve patient information.

    **Request:**
    ```json
    {
      "call_id": "uuid",
      "tenant_id": "uuid",
      "phone": "+1234567890"
    }
    ```

    **Response:**
    ```json
    {
      "found": true,
      "patient_id": "uuid",
      "patient_name": "John Doe",
      "patient_data": {
        "email": "john@example.com",
        "date_of_birth": "1990-01-01"
      }
    }
    ```

    **Security:**
    Set ZOICE_API_KEY environment variable with the API key.
    """
    # Verify API key
    verify_api_key(x_api_key, "ZOICE_API_KEY", "Zucol/Zoice Tool")

    service = get_voice_webhook_service(db)
    return service.lookup_patient(request)


@router.post("/tools/available-slots", response_model=AvailableSlotsResponse)
def get_available_slots(
    request: AvailableSlotsRequest,
    x_api_key: str = Header(..., description="API key for authentication"),
    db: Session = Depends(get_db),
):
    """
    Get available appointment slots

    **Called by voice agent during call** to find available times for booking.

    **Example:**
    When patient requests an appointment, the voice agent calls this to get
    available slots matching the patient's preferences.

    **Request:**
    ```json
    {
      "call_id": "uuid",
      "tenant_id": "uuid",
      "practitioner_name": "Dr. Smith",
      "preferred_date": "2024-11-20",
      "preferred_time": "morning"
    }
    ```

    **Response:**
    ```json
    {
      "slots": [
        {
          "datetime": "2024-11-20T10:00:00Z",
          "practitioner_name": "Dr. Smith",
          "location_name": "Main Clinic",
          "formatted_time": "Wednesday, Nov 20 at 10:00 AM"
        }
      ],
      "total_found": 5
    }
    ```
    """
    # Verify API key
    verify_api_key(x_api_key, "ZOICE_API_KEY", "Zucol/Zoice Tool")

    service = get_voice_webhook_service(db)
    return service.get_available_slots(request)


@router.post("/tools/book-appointment", response_model=BookAppointmentResponse)
def book_appointment(
    request: BookAppointmentRequest,
    x_api_key: str = Header(..., description="API key for authentication"),
    db: Session = Depends(get_db),
):
    """
    Book an appointment

    **Called by voice agent during call** to book an appointment after
    patient confirms a time slot.

    **Example:**
    After patient confirms "yes, book me for 10 AM", the voice agent
    calls this endpoint to create the appointment.

    **Request:**
    ```json
    {
      "call_id": "uuid",
      "tenant_id": "uuid",
      "patient_phone": "+1234567890",
      "slot_datetime": "2024-11-20T10:00:00Z",
      "practitioner_id": "uuid",
      "location_id": "uuid",
      "reason": "Regular checkup"
    }
    ```

    **Response:**
    ```json
    {
      "success": true,
      "appointment_id": "uuid",
      "message": "Appointment booked successfully",
      "confirmation_details": {
        "patient_name": "John Doe",
        "datetime": "2024-11-20T10:00:00Z",
        "practitioner": "Dr. Smith",
        "location": "Main Clinic"
      }
    }
    ```
    """
    # Verify API key
    verify_api_key(x_api_key, "ZOICE_API_KEY", "Zucol/Zoice Tool")

    service = get_voice_webhook_service(db)
    return service.book_appointment(request)


# ==================== Health Check ====================

@router.get("/webhook/health")
def webhook_health():
    """
    Health check for webhook endpoint

    Used by Zucol/Zoice to verify webhook is reachable.
    """
    return {
        "status": "healthy",
        "service": "voice-webhook",
        "timestamp": "2024-11-19T00:00:00Z",
    }
