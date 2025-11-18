"""
Scribe Service Pydantic Schemas
Request/Response models for AI-powered clinical documentation
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator


# ==================== SOAP Note Schemas ====================

class SOAPNoteRequest(BaseModel):
    """Request to generate SOAP note from transcript"""

    tenant_id: UUID
    encounter_id: UUID
    patient_id: UUID
    practitioner_id: UUID
    transcript: str = Field(
        ...,
        min_length=10,
        max_length=50000,
        description="Clinical conversation transcript"
    )
    encounter_type: str = Field(
        default="opd",
        description="Type of encounter: opd, ipd, emergency, followup"
    )
    additional_context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional context like chief complaint, vitals, etc."
    )

    @validator("encounter_type")
    def validate_encounter_type(cls, v):
        valid_types = ["opd", "ipd", "emergency", "followup", "procedure"]
        if v.lower() not in valid_types:
            raise ValueError(f"encounter_type must be one of: {', '.join(valid_types)}")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "encounter_id": "encounter-uuid",
                "patient_id": "patient-uuid",
                "practitioner_id": "practitioner-uuid",
                "transcript": "Patient presents with fever for 3 days. Temperature 101F. No cough. Chest clear. Diagnosed with viral fever. Advised rest and paracetamol.",
                "encounter_type": "opd",
                "additional_context": {
                    "chief_complaint": "Fever",
                    "vitals": {
                        "temperature": "101F",
                        "bp": "120/80",
                        "pulse": "82"
                    }
                }
            }
        }


class SOAPNote(BaseModel):
    """Structured SOAP note"""

    subjective: str = Field(..., description="Subjective findings (patient's complaint)")
    objective: str = Field(..., description="Objective findings (examination, vitals)")
    assessment: str = Field(..., description="Assessment and diagnosis")
    plan: str = Field(..., description="Treatment plan")
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for the generated note (0-1)"
    )


class Problem(BaseModel):
    """Extracted clinical problem with coding"""

    description: str = Field(..., description="Problem description in plain text")
    icd10_code: Optional[str] = Field(None, description="ICD-10 code")
    icd10_description: Optional[str] = Field(None, description="ICD-10 code description")
    snomed_code: Optional[str] = Field(None, description="SNOMED CT code")
    snomed_description: Optional[str] = Field(None, description="SNOMED CT description")
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in the problem extraction and coding"
    )
    is_primary: bool = Field(
        default=False,
        description="Whether this is the primary diagnosis"
    )


class MedicationOrder(BaseModel):
    """Suggested medication order"""

    medication_name: str
    dosage: str
    frequency: str
    duration: str
    route: str = Field(default="oral")
    instructions: Optional[str] = None
    confidence_score: float = Field(..., ge=0.0, le=1.0)


class LabOrder(BaseModel):
    """Suggested lab test order"""

    test_name: str
    loinc_code: Optional[str] = Field(None, description="LOINC code for the test")
    urgency: str = Field(default="routine", description="routine, urgent, stat")
    instructions: Optional[str] = None
    confidence_score: float = Field(..., ge=0.0, le=1.0)

    @validator("urgency")
    def validate_urgency(cls, v):
        valid_urgencies = ["routine", "urgent", "stat"]
        if v.lower() not in valid_urgencies:
            raise ValueError(f"urgency must be one of: {', '.join(valid_urgencies)}")
        return v.lower()


class ImagingOrder(BaseModel):
    """Suggested imaging order"""

    study_name: str
    modality: str = Field(
        ...,
        description="Imaging modality: xray, ct, mri, ultrasound, etc."
    )
    body_part: str
    urgency: str = Field(default="routine")
    clinical_indication: Optional[str] = None
    confidence_score: float = Field(..., ge=0.0, le=1.0)


class SOAPNoteResponse(BaseModel):
    """Complete response with SOAP note, problems, and orders"""

    soap_note: SOAPNote
    problems: List[Problem] = Field(default_factory=list)
    medication_orders: List[MedicationOrder] = Field(default_factory=list)
    lab_orders: List[LabOrder] = Field(default_factory=list)
    imaging_orders: List[ImagingOrder] = Field(default_factory=list)
    fhir_resources: Optional[Dict[str, Any]] = Field(
        None,
        description="Draft FHIR resources (Composition, Condition, etc.)"
    )
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")


# ==================== Problem Extraction Schemas ====================

class ProblemExtractionRequest(BaseModel):
    """Request to extract problems from clinical text"""

    tenant_id: UUID
    clinical_text: str = Field(
        ...,
        min_length=10,
        max_length=10000,
        description="Clinical text to extract problems from"
    )
    include_coding: bool = Field(
        default=True,
        description="Whether to include ICD-10 and SNOMED coding"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "clinical_text": "Patient has diabetes mellitus type 2, hypertension, and newly diagnosed atrial fibrillation.",
                "include_coding": True
            }
        }


class ProblemExtractionResponse(BaseModel):
    """Response with extracted problems"""

    problems: List[Problem]
    processing_time_ms: int


# ==================== Order Suggestion Schemas ====================

class OrderSuggestionRequest(BaseModel):
    """Request for order suggestions based on assessment"""

    tenant_id: UUID
    assessment: str = Field(
        ...,
        description="Clinical assessment and diagnosis"
    )
    encounter_type: str = Field(default="opd")
    patient_context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Patient context (age, allergies, existing conditions, etc.)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "assessment": "Type 2 Diabetes Mellitus, uncontrolled. HbA1c 9.2%",
                "encounter_type": "opd",
                "patient_context": {
                    "age": 55,
                    "allergies": [],
                    "existing_conditions": ["hypertension"]
                }
            }
        }


class OrderSuggestionResponse(BaseModel):
    """Response with suggested orders"""

    medication_orders: List[MedicationOrder] = Field(default_factory=list)
    lab_orders: List[LabOrder] = Field(default_factory=list)
    imaging_orders: List[ImagingOrder] = Field(default_factory=list)
    processing_time_ms: int


# ==================== FHIR Draft Schemas ====================

class FHIRDraftRequest(BaseModel):
    """Request to generate FHIR resource drafts"""

    tenant_id: UUID
    encounter_id: UUID
    patient_id: UUID
    practitioner_id: UUID
    soap_note: SOAPNote
    problems: List[Problem] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "encounter_id": "encounter-uuid",
                "patient_id": "patient-uuid",
                "practitioner_id": "practitioner-uuid",
                "soap_note": {
                    "subjective": "Patient complains of fever for 3 days",
                    "objective": "Temp 101F, BP 120/80, chest clear",
                    "assessment": "Viral fever",
                    "plan": "Rest, paracetamol 500mg TID x 3 days",
                    "confidence_score": 0.92
                },
                "problems": [
                    {
                        "description": "Viral fever",
                        "icd10_code": "A99",
                        "confidence_score": 0.85,
                        "is_primary": True
                    }
                ]
            }
        }


class FHIRDraftResponse(BaseModel):
    """Response with FHIR resource drafts"""

    composition: Dict[str, Any] = Field(
        ...,
        description="FHIR Composition resource (clinical document)"
    )
    conditions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="FHIR Condition resources for problems"
    )
    observations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="FHIR Observation resources"
    )
    processing_time_ms: int


# ==================== Validation Schemas ====================

class ValidationIssue(BaseModel):
    """Issue found during validation"""

    severity: str = Field(..., description="error, warning, info")
    code: str = Field(..., description="Issue code")
    message: str = Field(..., description="Human-readable message")
    location: Optional[str] = Field(None, description="Location in the document")

    @validator("severity")
    def validate_severity(cls, v):
        valid_severities = ["error", "warning", "info"]
        if v.lower() not in valid_severities:
            raise ValueError(f"severity must be one of: {', '.join(valid_severities)}")
        return v.lower()


class SOAPNoteValidationRequest(BaseModel):
    """Request to validate a SOAP note"""

    soap_note: SOAPNote
    problems: List[Problem] = Field(default_factory=list)


class SOAPNoteValidationResponse(BaseModel):
    """Response with validation results"""

    is_valid: bool
    issues: List[ValidationIssue] = Field(default_factory=list)
    suggestions: List[str] = Field(
        default_factory=list,
        description="Suggestions for improvement"
    )
