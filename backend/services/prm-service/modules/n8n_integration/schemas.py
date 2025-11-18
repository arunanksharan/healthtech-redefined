"""
n8n Integration Schemas
Schemas for n8n workflow callbacks and responses
"""
from typing import Dict, Any, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


# ==================== Intake Flow Schemas ====================

class IntakeResponsePayload(BaseModel):
    """
    Callback from n8n after processing intake message with AI

    n8n sends this after:
    1. Receiving user's message
    2. Processing with GPT/LLM
    3. Extracting structured data
    4. Determining next question to ask
    """
    conversation_id: str = Field(..., description="Conversation UUID")

    # Extracted data from user's message
    extracted_fields: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured data extracted from message (e.g., patient.name, symptoms)"
    )

    # Next steps in conversation
    next_field: Optional[str] = Field(
        None,
        description="Next field AI wants to ask about"
    )
    next_question: Optional[str] = Field(
        None,
        description="Next question to ask user (empty if conversation complete)"
    )

    # Metadata
    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="AI confidence in extraction"
    )


class DepartmentInfo(BaseModel):
    """Department/Specialty information"""
    name: str = Field(..., description="Department name (e.g., 'Cardiology', 'Orthopedics')")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    reasoning: Optional[str] = None


class DepartmentTriagePayload(BaseModel):
    """
    Callback from n8n after department triage

    n8n sends this after:
    1. Intake conversation is complete
    2. AI analyzes chief complaint + symptoms
    3. Determines best department/specialty
    """
    conversation_id: UUID = Field(..., description="Conversation UUID")

    # AI-determined department
    best_department: DepartmentInfo = Field(
        ...,
        description="Best matching department for patient's needs"
    )

    # Alternative departments (optional)
    alternative_departments: List[DepartmentInfo] = Field(
        default_factory=list,
        description="Other possible departments (in order of relevance)"
    )

    # Context from intake
    chief_complaint: Optional[str] = None
    symptoms: List[str] = Field(default_factory=list)

    # Booking intent signal
    booking_intent: int = Field(
        0,
        description="1 if booking appointment, 0 otherwise"
    )


# ==================== Booking Flow Schemas ====================

class BookingResponsePayload(BaseModel):
    """
    Response from user during slot selection

    This is sent by n8n when it needs to confirm/cancel booking
    """
    conversation_id: str

    # User's action
    action: str = Field(
        ...,
        description="confirm_slot, reject_slots, cancel_booking, or ambiguous"
    )

    # If confirming slot
    booking_response: Optional[Dict[str, Any]] = Field(
        None,
        description="Contains preferred_time and other booking details"
    )

    # Message to send to user
    reply_to_user: Optional[str] = None


# ==================== Response Schemas ====================

class N8nCallbackResponse(BaseModel):
    """Standard response for n8n callbacks"""
    status: str = Field(..., description="success or error")
    message: str
    conversation_id: Optional[str] = None
    action_taken: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
