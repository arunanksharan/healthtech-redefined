"""
Intake Module Schemas
Schemas for clinical intake data collection
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, validator


# ==================== Session Management ====================

class IntakeSessionCreate(BaseModel):
    """Create intake session"""
    patient_id: Optional[UUID] = Field(None, description="Link to patient (requires consent)")
    conversation_id: Optional[UUID] = Field(None, description="Link to WhatsApp conversation")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context (channel, locale, etc.)")


class IntakeSessionOut(BaseModel):
    """Intake session response"""
    id: UUID
    org_id: UUID
    status: str  # open | submitted | closed
    patient_id: Optional[UUID]
    conversation_id: Optional[UUID]
    context: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Clinical Records ====================

class ChiefComplaint(BaseModel):
    """Primary reason for visit"""
    text: str = Field(..., min_length=1, max_length=500)
    codes: Optional[Dict[str, str]] = Field(None, description="Coded complaint: {set, code}")


class SymptomItem(BaseModel):
    """Individual symptom with clinical details"""
    client_item_id: Optional[str] = Field(None, max_length=64, description="For idempotency")
    code: Optional[Dict[str, str]] = Field(None, description="Symptom code: {set, code}")
    onset: Optional[str] = Field(None, max_length=32, description="ISO date or relative (e.g., '3 days ago')")
    duration: Optional[str] = Field(None, max_length=32)
    severity: Optional[str] = Field(None, pattern="^(mild|moderate|severe|unknown)?$")
    frequency: Optional[str] = Field(None, max_length=32)
    laterality: Optional[str] = Field(None, max_length=32, description="left | right | bilateral")
    notes: Optional[str] = Field(None, max_length=1000)


class AllergyItem(BaseModel):
    """Allergy information"""
    client_item_id: Optional[str] = Field(None, max_length=64)
    substance: str = Field(..., min_length=1, max_length=120)
    reaction: Optional[str] = Field(None, max_length=120)
    severity: Optional[str] = Field(None, pattern="^(mild|moderate|severe)?$")


class MedicationItem(BaseModel):
    """Current medication"""
    client_item_id: Optional[str] = Field(None, max_length=64)
    name: str = Field(..., min_length=1, max_length=120)
    dose: Optional[str] = Field(None, max_length=120, description="e.g., '10mg'")
    schedule: Optional[str] = Field(None, max_length=120, description="e.g., 'twice daily'")
    adherence: Optional[str] = Field(None, max_length=64, description="compliant | partial | non-compliant")


class ConditionHistoryItem(BaseModel):
    """Past medical history"""
    client_item_id: Optional[str] = Field(None, max_length=64)
    condition: str = Field(..., min_length=1, max_length=160)
    status: Optional[str] = Field(None, pattern="^(active|resolved|unknown)?$")
    year_or_age: Optional[str] = Field(None, max_length=32)


class FamilyHistoryItem(BaseModel):
    """Family medical history"""
    client_item_id: Optional[str] = Field(None, max_length=64)
    relative: str = Field(..., min_length=1, max_length=64, description="father | mother | sibling | child")
    condition: str = Field(..., min_length=1, max_length=160)
    age_of_onset: Optional[str] = Field(None, max_length=32)


class SocialHistory(BaseModel):
    """Social history data"""
    smoking_status: Optional[str] = Field(None, max_length=64)
    alcohol_use: Optional[str] = Field(None, max_length=64)
    occupation: Optional[str] = Field(None, max_length=120)
    other: Optional[Dict[str, Any]] = Field(None, description="Additional social history")


class NoteItem(BaseModel):
    """Free-text note"""
    text: str = Field(..., min_length=1, max_length=5000)
    visibility: str = Field(default="internal", pattern="^(internal|external)$")


# ==================== Bulk Update ====================

class IntakeRecordsUpsert(BaseModel):
    """
    Upsert multiple record types at once

    Supports partial updates - only provided fields are updated.

    Example:
    ```json
    {
      "chief_complaint": {
        "text": "Headache and fever"
      },
      "symptoms": [
        {
          "client_item_id": "symptom-1",
          "notes": "Severe headache",
          "severity": "severe"
        }
      ],
      "allergies": [
        {
          "client_item_id": "allergy-1",
          "substance": "Penicillin",
          "reaction": "Rash"
        }
      ]
    }
    ```
    """
    chief_complaint: Optional[ChiefComplaint] = None
    symptoms: Optional[List[SymptomItem]] = None
    allergies: Optional[List[AllergyItem]] = None
    medications: Optional[List[MedicationItem]] = None
    condition_history: Optional[List[ConditionHistoryItem]] = None
    family_history: Optional[List[FamilyHistoryItem]] = None
    social_history: Optional[SocialHistory] = None
    notes: Optional[List[NoteItem]] = None


# ==================== Summary ====================

class IntakeSummaryUpdate(BaseModel):
    """Set AI-generated summary"""
    text: str = Field(..., min_length=1, max_length=10000)


class IntakeSummaryOut(BaseModel):
    """Intake summary response"""
    id: UUID
    session_id: UUID
    text: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Submission ====================

class IntakeSubmit(BaseModel):
    """Submit intake session"""
    ready_for_booking: bool = Field(default=True, description="Mark as ready for appointment booking")


# ==================== Complete Session View ====================

class IntakeSessionComplete(BaseModel):
    """
    Complete intake session with all records

    Used for viewing full intake data in one response.
    """
    session: IntakeSessionOut
    chief_complaint: Optional[ChiefComplaint]
    symptoms: List[SymptomItem]
    allergies: List[AllergyItem]
    medications: List[MedicationItem]
    condition_history: List[ConditionHistoryItem]
    family_history: List[FamilyHistoryItem]
    social_history: Optional[SocialHistory]
    notes: List[NoteItem]
    summary: Optional[IntakeSummaryOut]


# ==================== Export ====================

class IntakeExport(BaseModel):
    """
    Export intake data for EHR integration

    Structured format compatible with FHIR or custom EHR systems.
    """
    session_id: UUID
    patient_id: Optional[UUID]
    status: str
    chief_complaint: Optional[str]
    symptoms: List[Dict[str, Any]]
    allergies: List[Dict[str, Any]]
    medications: List[Dict[str, Any]]
    condition_history: List[Dict[str, Any]]
    family_history: List[Dict[str, Any]]
    social_history: Dict[str, Any]
    notes: List[str]
    summary: Optional[str]
    created_at: datetime
    submitted_at: Optional[datetime]


# ==================== Statistics ====================

class IntakeStatistics(BaseModel):
    """Intake session statistics"""
    total_sessions: int
    open_sessions: int
    submitted_sessions: int
    closed_sessions: int
    avg_completion_time_minutes: float
    by_conversation: int = Field(..., description="Sessions linked to conversations")
    by_patient: int = Field(..., description="Sessions linked to patients")
