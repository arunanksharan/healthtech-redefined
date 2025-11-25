"""
Medical AI Module Schemas
EPIC-010: Medical AI Capabilities API Schemas
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field


# ==================== Enums ====================

class UrgencyLevelEnum(str, Enum):
    """Triage urgency levels"""
    EMERGENCY = "emergency"
    URGENT = "urgent"
    LESS_URGENT = "less_urgent"
    SEMI_URGENT = "semi_urgent"
    NON_URGENT = "non_urgent"
    SELF_CARE = "self_care"


class EntityTypeEnum(str, Enum):
    """Medical entity types"""
    CONDITION = "condition"
    MEDICATION = "medication"
    PROCEDURE = "procedure"
    ANATOMY = "anatomy"
    LABORATORY = "laboratory"
    VITAL_SIGN = "vital_sign"
    SYMPTOM = "symptom"
    DEVICE = "device"


class NegationStatusEnum(str, Enum):
    """Entity negation status"""
    AFFIRMED = "affirmed"
    NEGATED = "negated"
    UNCERTAIN = "uncertain"
    HYPOTHETICAL = "hypothetical"
    FAMILY_HISTORY = "family_history"
    HISTORICAL = "historical"


class RiskLevelEnum(str, Enum):
    """Risk levels for predictive models"""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"
    CRITICAL = "critical"


class InteractionSeverityEnum(str, Enum):
    """Drug interaction severity levels"""
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CONTRAINDICATED = "contraindicated"


class DocumentationTypeEnum(str, Enum):
    """Clinical documentation types"""
    PROGRESS_NOTE = "progress_note"
    DISCHARGE_SUMMARY = "discharge_summary"
    CONSULTATION = "consultation"
    OPERATIVE_NOTE = "operative_note"
    H_AND_P = "h_and_p"
    SOAP_NOTE = "soap_note"


class ImageTypeEnum(str, Enum):
    """Medical image types"""
    CHEST_XRAY = "chest_xray"
    SKIN_LESION = "skin_lesion"
    WOUND = "wound"


# ==================== Triage Schemas ====================

class TriageRequest(BaseModel):
    """Request for AI-powered triage"""
    patient_id: Optional[UUID] = None
    symptoms: List[str] = Field(..., min_length=1, description="List of reported symptoms")
    chief_complaint: str = Field(..., min_length=3, description="Primary complaint")
    age: Optional[int] = Field(None, ge=0, le=150)
    gender: Optional[str] = None
    vital_signs: Optional[Dict[str, Any]] = None
    medical_history: Optional[List[str]] = None
    current_medications: Optional[List[str]] = None
    duration_hours: Optional[int] = Field(None, ge=0, description="Symptom duration in hours")
    additional_context: Optional[str] = None


class RedFlagAlertResponse(BaseModel):
    """Red flag alert in triage"""
    name: str
    description: str
    severity: str
    action_required: str
    evidence: List[str]


class TriageExplanationResponse(BaseModel):
    """Explanation of triage decision"""
    decision_path: List[str]
    factors_considered: List[str]
    rationale: str
    evidence_citations: List[str]
    confidence_breakdown: Dict[str, float]
    alternative_considerations: List[str]


class TriageResponse(BaseModel):
    """Response from AI triage"""
    triage_id: UUID
    urgency_level: UrgencyLevelEnum
    esi_level: int = Field(..., ge=1, le=5)
    confidence: float = Field(..., ge=0.0, le=1.0)
    recommended_department: str
    red_flags: List[RedFlagAlertResponse]
    symptom_analysis: Dict[str, Any]
    explanation: TriageExplanationResponse
    suggested_questions: List[str]
    estimated_wait_time: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Documentation AI Schemas ====================

class TranscriptionRequest(BaseModel):
    """Request for ambient transcription"""
    audio_url: Optional[str] = None
    audio_base64: Optional[str] = None
    encounter_id: Optional[UUID] = None
    patient_id: Optional[UUID] = None
    provider_id: Optional[UUID] = None
    encounter_type: Optional[str] = "office_visit"


class SpeakerSegmentResponse(BaseModel):
    """Speaker segment from transcription"""
    speaker: str
    role: str
    text: str
    start_time: float
    end_time: float
    confidence: float


class TranscriptionResponse(BaseModel):
    """Response from transcription"""
    transcription_id: UUID
    full_text: str
    segments: List[SpeakerSegmentResponse]
    duration_seconds: float
    word_count: int
    clinical_summary: str
    created_at: datetime


class SOAPNoteRequest(BaseModel):
    """Request for SOAP note generation"""
    encounter_id: Optional[UUID] = None
    patient_id: Optional[UUID] = None
    transcript: Optional[str] = None
    transcription_id: Optional[UUID] = None
    provider_notes: Optional[str] = None
    include_coding: bool = True


class SOAPNoteResponse(BaseModel):
    """SOAP note response"""
    note_id: UUID
    subjective: str
    objective: str
    assessment: str
    plan: str
    icd10_codes: List[Dict[str, Any]]
    cpt_codes: List[Dict[str, Any]]
    hcc_codes: List[Dict[str, Any]]
    created_at: datetime


class CodeSuggestionRequest(BaseModel):
    """Request for medical code suggestions"""
    clinical_text: str = Field(..., min_length=10)
    code_types: List[str] = Field(default=["icd10", "cpt", "hcc"])
    max_suggestions: int = Field(10, ge=1, le=50)


class CodeSuggestionResponse(BaseModel):
    """Code suggestion response"""
    code: str
    description: str
    code_type: str
    confidence: float
    evidence: str
    category: Optional[str] = None


# ==================== Entity Recognition Schemas ====================

class EntityExtractionRequest(BaseModel):
    """Request for medical entity extraction"""
    text: str = Field(..., min_length=3)
    entity_types: Optional[List[EntityTypeEnum]] = None
    include_negation: bool = True
    include_relationships: bool = True
    normalize_to_standards: bool = True


class MedicalEntityResponse(BaseModel):
    """Extracted medical entity"""
    entity_id: UUID
    text: str
    entity_type: EntityTypeEnum
    start: int
    end: int
    confidence: float
    negation_status: NegationStatusEnum
    normalized_code: Optional[str] = None
    code_system: Optional[str] = None
    preferred_term: Optional[str] = None
    attributes: Dict[str, Any]


class EntityRelationshipResponse(BaseModel):
    """Relationship between entities"""
    relationship_id: UUID
    source_entity_id: UUID
    target_entity_id: UUID
    relationship_type: str
    confidence: float


class EntityExtractionResponse(BaseModel):
    """Response from entity extraction"""
    extraction_id: UUID
    entities: List[MedicalEntityResponse]
    relationships: List[EntityRelationshipResponse]
    entity_counts: Dict[str, int]
    processing_time_ms: float


# ==================== Clinical Decision Support Schemas ====================

class ClinicalDecisionRequest(BaseModel):
    """Request for clinical decision support"""
    patient_id: Optional[UUID] = None
    conditions: List[str] = Field(..., min_length=1)
    medications: Optional[List[str]] = None
    lab_results: Optional[Dict[str, Any]] = None
    vital_signs: Optional[Dict[str, Any]] = None
    include_guidelines: bool = True
    include_interactions: bool = True
    include_differentials: bool = False
    symptoms: Optional[List[str]] = None


class GuidelineRecommendationResponse(BaseModel):
    """Clinical guideline recommendation"""
    recommendation_id: UUID
    condition: str
    guideline_source: str
    recommendation: str
    evidence_level: str
    recommendation_grade: str
    monitoring_parameters: List[str]
    contraindications: List[str]
    citations: List[str]


class DrugInteractionResponse(BaseModel):
    """Drug interaction alert"""
    interaction_id: UUID
    drug_a: str
    drug_b: str
    severity: InteractionSeverityEnum
    description: str
    mechanism: str
    clinical_significance: str
    management: str
    evidence_level: str


class DifferentialDiagnosisResponse(BaseModel):
    """Differential diagnosis"""
    diagnosis: str
    icd10_code: Optional[str]
    probability: float
    supporting_evidence: List[str]
    contradicting_evidence: List[str]
    recommended_workup: List[str]


class ClinicalDecisionResponse(BaseModel):
    """Response from clinical decision support"""
    decision_id: UUID
    guidelines: List[GuidelineRecommendationResponse]
    drug_interactions: List[DrugInteractionResponse]
    differential_diagnoses: List[DifferentialDiagnosisResponse]
    treatment_recommendations: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]
    created_at: datetime


# ==================== Predictive Analytics Schemas ====================

class PredictiveAnalyticsRequest(BaseModel):
    """Request for predictive analytics"""
    patient_id: UUID
    include_readmission: bool = True
    include_deterioration: bool = True
    include_no_show: bool = True
    include_fall_risk: bool = False
    admission_data: Optional[Dict[str, Any]] = None
    vital_signs: Optional[Dict[str, Any]] = None
    appointment_data: Optional[Dict[str, Any]] = None
    mobility_data: Optional[Dict[str, Any]] = None


class ReadmissionRiskResponse(BaseModel):
    """Readmission risk prediction"""
    risk_level: RiskLevelEnum
    probability: float
    lace_score: int
    contributing_factors: List[str]
    interventions: List[str]
    risk_factors: Dict[str, Any]


class DeteriorationAlertResponse(BaseModel):
    """Clinical deterioration alert"""
    risk_level: RiskLevelEnum
    mews_score: int
    probability: float
    trigger_reasons: List[str]
    recommended_actions: List[str]
    vital_sign_trends: Dict[str, Any]


class NoShowPredictionResponse(BaseModel):
    """No-show prediction"""
    risk_level: RiskLevelEnum
    probability: float
    contributing_factors: List[str]
    recommendations: List[str]


class FallRiskResponse(BaseModel):
    """Fall risk assessment"""
    risk_level: RiskLevelEnum
    morse_score: int
    probability: float
    risk_factors: List[str]
    preventive_measures: List[str]


class PredictiveAnalyticsResponse(BaseModel):
    """Response from predictive analytics"""
    analysis_id: UUID
    patient_id: UUID
    readmission_risk: Optional[ReadmissionRiskResponse] = None
    deterioration_alert: Optional[DeteriorationAlertResponse] = None
    no_show_prediction: Optional[NoShowPredictionResponse] = None
    fall_risk: Optional[FallRiskResponse] = None
    overall_risk_summary: str
    created_at: datetime


# ==================== Medical Image Analysis Schemas ====================

class ImageAnalysisRequest(BaseModel):
    """Request for medical image analysis"""
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    image_type: ImageTypeEnum
    patient_id: Optional[UUID] = None
    clinical_context: Optional[str] = None
    comparison_study_id: Optional[UUID] = None


class RadiologyFindingResponse(BaseModel):
    """Radiology finding"""
    finding: str
    location: str
    confidence: float
    severity: Optional[str] = None
    measurements: Optional[Dict[str, Any]] = None
    related_conditions: List[str]


class ChestXrayResponse(BaseModel):
    """Chest X-ray analysis response"""
    findings: List[RadiologyFindingResponse]
    overall_impression: str
    recommendations: List[str]
    comparison_notes: Optional[str] = None
    critical_findings: List[str]


class SkinLesionResponse(BaseModel):
    """Skin lesion analysis response"""
    lesion_type: str
    malignancy_risk: str
    confidence: float
    abcde_scores: Dict[str, float]
    differential_diagnoses: List[str]
    recommendations: List[str]
    urgent_referral: bool


class WoundAssessmentResponse(BaseModel):
    """Wound assessment response"""
    wound_type: str
    stage: Optional[str] = None
    tissue_composition: Dict[str, float]
    dimensions: Dict[str, float]
    infection_risk: str
    healing_trajectory: str
    treatment_recommendations: List[str]


class ImageAnalysisResponse(BaseModel):
    """Response from image analysis"""
    analysis_id: UUID
    image_type: ImageTypeEnum
    chest_xray_result: Optional[ChestXrayResponse] = None
    skin_lesion_result: Optional[SkinLesionResponse] = None
    wound_result: Optional[WoundAssessmentResponse] = None
    processing_time_ms: float
    model_version: str
    created_at: datetime


# ==================== Clinical NLP Pipeline Schemas ====================

class NLPPipelineRequest(BaseModel):
    """Request for clinical NLP pipeline"""
    text: str = Field(..., min_length=10)
    document_type: Optional[str] = None
    include_sections: bool = True
    include_problems: bool = True
    include_medications: bool = True
    include_sdoh: bool = True
    include_quality_measures: bool = True


class ClinicalSectionResponse(BaseModel):
    """Clinical document section"""
    section_type: str
    title: str
    content: str
    start: int
    end: int


class ProblemEntryResponse(BaseModel):
    """Problem list entry"""
    problem: str
    icd10_code: Optional[str] = None
    snomed_code: Optional[str] = None
    status: str
    onset_date: Optional[str] = None
    evidence: str


class MedicationEntryResponse(BaseModel):
    """Medication entry"""
    medication: str
    rxnorm_code: Optional[str] = None
    dose: Optional[str] = None
    route: Optional[str] = None
    frequency: Optional[str] = None
    status: str
    indication: Optional[str] = None


class SocialDeterminantResponse(BaseModel):
    """Social determinant of health"""
    category: str
    description: str
    z_code: Optional[str] = None
    impact_level: str
    evidence: str
    interventions: List[str]


class QualityMeasureResponse(BaseModel):
    """Quality measure identification"""
    measure_id: str
    measure_name: str
    applicable: bool
    evidence: str
    numerator_eligible: bool
    denominator_eligible: bool
    gap_in_care: bool
    recommended_actions: List[str]


class NLPPipelineResponse(BaseModel):
    """Response from NLP pipeline"""
    pipeline_id: UUID
    sections: List[ClinicalSectionResponse]
    problems: List[ProblemEntryResponse]
    medications: List[MedicationEntryResponse]
    social_determinants: List[SocialDeterminantResponse]
    quality_measures: List[QualityMeasureResponse]
    processing_time_ms: float
    created_at: datetime


# ==================== Voice Biomarker Schemas ====================

class VoiceBiomarkerRequest(BaseModel):
    """Request for voice biomarker analysis"""
    audio_url: Optional[str] = None
    audio_base64: Optional[str] = None
    patient_id: Optional[UUID] = None
    include_depression: bool = True
    include_cognitive: bool = True
    include_respiratory: bool = True
    baseline_id: Optional[UUID] = None


class DepressionAssessmentResponse(BaseModel):
    """Depression assessment from voice"""
    depression_risk: RiskLevelEnum
    phq9_equivalent: int
    confidence: float
    vocal_markers: Dict[str, Any]
    trend: Optional[str] = None
    recommendations: List[str]


class CognitiveAssessmentResponse(BaseModel):
    """Cognitive assessment from voice"""
    cognitive_risk: RiskLevelEnum
    mci_risk_score: float
    confidence: float
    fluency_score: float
    word_finding_score: float
    coherence_score: float
    concerns: List[str]
    recommendations: List[str]


class RespiratoryAssessmentResponse(BaseModel):
    """Respiratory assessment from voice"""
    respiratory_status: str
    breath_support_score: float
    detected_patterns: List[str]
    severity: Optional[str] = None
    recommendations: List[str]


class VoiceBiomarkerResponse(BaseModel):
    """Response from voice biomarker analysis"""
    analysis_id: UUID
    patient_id: Optional[UUID]
    audio_features: Dict[str, Any]
    depression_assessment: Optional[DepressionAssessmentResponse] = None
    cognitive_assessment: Optional[CognitiveAssessmentResponse] = None
    respiratory_assessment: Optional[RespiratoryAssessmentResponse] = None
    baseline_comparison: Optional[Dict[str, Any]] = None
    overall_summary: str
    created_at: datetime


# ==================== Batch Processing Schemas ====================

class BatchTriageRequest(BaseModel):
    """Batch triage request"""
    cases: List[TriageRequest]


class BatchTriageResponse(BaseModel):
    """Batch triage response"""
    results: List[TriageResponse]
    processing_time_ms: float
    success_count: int
    failure_count: int


class BatchEntityExtractionRequest(BaseModel):
    """Batch entity extraction request"""
    texts: List[str]
    entity_types: Optional[List[EntityTypeEnum]] = None


class BatchEntityExtractionResponse(BaseModel):
    """Batch entity extraction response"""
    results: List[EntityExtractionResponse]
    processing_time_ms: float


# ==================== Statistics and Monitoring ====================

class MedicalAIStatistics(BaseModel):
    """Medical AI usage statistics"""
    total_triage_requests: int
    total_documentation_requests: int
    total_entity_extractions: int
    total_decision_support_requests: int
    total_predictions: int
    total_image_analyses: int
    total_nlp_pipeline_runs: int
    total_voice_analyses: int
    average_triage_confidence: float
    average_processing_time_ms: float
    red_flag_detection_rate: float
    model_versions: Dict[str, str]


class MedicalAIHealthCheck(BaseModel):
    """Medical AI module health check"""
    status: str
    module: str
    features: List[str]
    model_status: Dict[str, str]
    last_calibration: Optional[datetime] = None
