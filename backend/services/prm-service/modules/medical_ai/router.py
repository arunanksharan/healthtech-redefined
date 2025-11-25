"""
Medical AI Router
EPIC-010: Medical AI Capabilities API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from loguru import logger

from shared.database.connection import get_db

from modules.medical_ai.schemas import (
    # Triage
    TriageRequest,
    TriageResponse,
    BatchTriageRequest,
    BatchTriageResponse,
    # Documentation
    TranscriptionRequest,
    TranscriptionResponse,
    SOAPNoteRequest,
    SOAPNoteResponse,
    CodeSuggestionRequest,
    CodeSuggestionResponse,
    # Entity Recognition
    EntityExtractionRequest,
    EntityExtractionResponse,
    BatchEntityExtractionRequest,
    BatchEntityExtractionResponse,
    # Clinical Decision Support
    ClinicalDecisionRequest,
    ClinicalDecisionResponse,
    # Predictive Analytics
    PredictiveAnalyticsRequest,
    PredictiveAnalyticsResponse,
    # Image Analysis
    ImageAnalysisRequest,
    ImageAnalysisResponse,
    ImageTypeEnum,
    # NLP Pipeline
    NLPPipelineRequest,
    NLPPipelineResponse,
    # Voice Biomarkers
    VoiceBiomarkerRequest,
    VoiceBiomarkerResponse,
    # Statistics
    MedicalAIStatistics,
    MedicalAIHealthCheck,
)
from modules.medical_ai.service import MedicalAIService


router = APIRouter(prefix="/medical-ai", tags=["Medical AI"])


# ==================== Triage Endpoints ====================

@router.post("/triage", response_model=TriageResponse)
async def perform_triage(
    request: TriageRequest,
    db: Session = Depends(get_db)
):
    """
    AI-Powered Medical Triage (US-010.1)

    Performs intelligent symptom analysis and triage assessment:
    - Analyzes symptoms with NLP
    - Detects red flags with 100% sensitivity target
    - Assigns ESI-based urgency level
    - Routes to appropriate department
    - Provides full explainability

    Target metrics:
    - 92% triage accuracy
    - 100% red flag sensitivity
    - <3 second response time

    Example request:
    ```json
    {
      "symptoms": ["chest pain", "shortness of breath", "sweating"],
      "chief_complaint": "Sudden chest pain for 30 minutes",
      "age": 55,
      "gender": "male",
      "vital_signs": {
        "heart_rate": 110,
        "blood_pressure_systolic": 160
      }
    }
    ```
    """
    service = MedicalAIService(db)

    try:
        # TODO: Get org_id from auth context
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")

        result = await service.perform_triage(org_id, request)
        return result

    except ValueError as e:
        logger.warning(f"Invalid triage request: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Triage failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Triage failed: {str(e)}")


@router.post("/triage/batch", response_model=BatchTriageResponse)
async def batch_triage(
    request: BatchTriageRequest,
    db: Session = Depends(get_db)
):
    """
    Batch triage processing for multiple cases

    Process multiple triage cases in a single request.
    Useful for:
    - Processing queued patients
    - Bulk re-assessment
    - Simulation and training
    """
    service = MedicalAIService(db)

    try:
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")

        import time
        start_time = time.time()

        results = []
        failures = 0

        for case in request.cases:
            try:
                result = await service.perform_triage(org_id, case)
                results.append(result)
            except Exception as e:
                logger.warning(f"Batch triage case failed: {e}")
                failures += 1

        processing_time = (time.time() - start_time) * 1000

        return BatchTriageResponse(
            results=results,
            processing_time_ms=processing_time,
            success_count=len(results),
            failure_count=failures,
        )

    except Exception as e:
        logger.error(f"Batch triage failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch triage failed: {str(e)}")


# ==================== Documentation AI Endpoints ====================

@router.post("/documentation/transcribe", response_model=TranscriptionResponse)
async def transcribe_encounter(
    request: TranscriptionRequest,
    db: Session = Depends(get_db)
):
    """
    Ambient Clinical Transcription (US-010.2)

    Transcribes clinical encounters with:
    - Speaker diarization (patient vs provider)
    - Medical terminology recognition
    - Clinical summary generation

    Accepts audio via URL or base64-encoded data.
    """
    service = MedicalAIService(db)

    try:
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")

        if not request.audio_url and not request.audio_base64:
            raise HTTPException(
                status_code=400,
                detail="Either audio_url or audio_base64 must be provided"
            )

        result = await service.transcribe_encounter(org_id, request)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/documentation/soap", response_model=SOAPNoteResponse)
async def generate_soap_note(
    request: SOAPNoteRequest,
    db: Session = Depends(get_db)
):
    """
    SOAP Note Generation (US-010.2)

    Generates structured SOAP notes from:
    - Encounter transcripts
    - Provider notes
    - Previous documentation

    Includes ICD-10, CPT, and HCC code suggestions.
    """
    service = MedicalAIService(db)

    try:
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")

        if not request.transcript and not request.transcription_id:
            raise HTTPException(
                status_code=400,
                detail="Either transcript or transcription_id must be provided"
            )

        result = await service.generate_soap_note(org_id, request)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SOAP note generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"SOAP note generation failed: {str(e)}")


@router.post("/documentation/codes", response_model=List[CodeSuggestionResponse])
async def suggest_codes(
    request: CodeSuggestionRequest,
    db: Session = Depends(get_db)
):
    """
    Medical Code Suggestion (US-010.2)

    Suggests medical codes from clinical text:
    - ICD-10 diagnosis codes
    - CPT procedure codes
    - HCC risk adjustment codes

    Returns ranked suggestions with confidence scores.
    """
    service = MedicalAIService(db)

    try:
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")

        result = await service.suggest_codes(org_id, request)
        return result

    except Exception as e:
        logger.error(f"Code suggestion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Code suggestion failed: {str(e)}")


# ==================== Entity Recognition Endpoints ====================

@router.post("/entities/extract", response_model=EntityExtractionResponse)
async def extract_entities(
    request: EntityExtractionRequest,
    db: Session = Depends(get_db)
):
    """
    Medical Entity Extraction (US-010.3)

    Extracts medical entities with:
    - 95%+ precision target
    - 20+ condition patterns
    - SNOMED CT, RxNorm, LOINC normalization
    - Negation detection (NegEx-style)
    - Entity relationship extraction

    Entity types:
    - condition, medication, procedure
    - anatomy, laboratory, vital_sign
    - symptom, device

    Example request:
    ```json
    {
      "text": "Patient has type 2 diabetes mellitus, no hypertension. Taking metformin 500mg twice daily.",
      "include_negation": true,
      "include_relationships": true
    }
    ```
    """
    service = MedicalAIService(db)

    try:
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")

        result = await service.extract_entities(org_id, request)
        return result

    except Exception as e:
        logger.error(f"Entity extraction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Entity extraction failed: {str(e)}")


@router.post("/entities/batch", response_model=BatchEntityExtractionResponse)
async def batch_extract_entities(
    request: BatchEntityExtractionRequest,
    db: Session = Depends(get_db)
):
    """
    Batch Entity Extraction

    Extract entities from multiple texts in a single request.
    Useful for processing clinical documents in bulk.
    """
    service = MedicalAIService(db)

    try:
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")

        import time
        start_time = time.time()

        results = []
        for text in request.texts:
            extraction_request = EntityExtractionRequest(
                text=text,
                entity_types=request.entity_types,
            )
            result = await service.extract_entities(org_id, extraction_request)
            results.append(result)

        processing_time = (time.time() - start_time) * 1000

        return BatchEntityExtractionResponse(
            results=results,
            processing_time_ms=processing_time,
        )

    except Exception as e:
        logger.error(f"Batch entity extraction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch extraction failed: {str(e)}")


# ==================== Clinical Decision Support Endpoints ====================

@router.post("/decision-support", response_model=ClinicalDecisionResponse)
async def get_clinical_decision_support(
    request: ClinicalDecisionRequest,
    db: Session = Depends(get_db)
):
    """
    Clinical Decision Intelligence (US-010.4)

    Provides comprehensive decision support:
    - Guideline-based recommendations
    - Drug-drug interaction checking
    - Differential diagnosis generation
    - Treatment recommendations

    Supported guidelines:
    - Hypertension (JNC 8, AHA/ACC)
    - Diabetes (ADA)
    - Heart Failure (ACC/AHA)
    - COPD (GOLD)
    - Asthma (GINA)

    Example request:
    ```json
    {
      "conditions": ["hypertension", "type 2 diabetes"],
      "medications": ["metformin", "lisinopril"],
      "lab_results": {"HbA1c": 7.5, "eGFR": 60}
    }
    ```
    """
    service = MedicalAIService(db)

    try:
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")

        result = await service.get_clinical_decision_support(org_id, request)
        return result

    except Exception as e:
        logger.error(f"Decision support failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Decision support failed: {str(e)}")


# ==================== Predictive Analytics Endpoints ====================

@router.post("/predictions", response_model=PredictiveAnalyticsResponse)
async def get_predictions(
    request: PredictiveAnalyticsRequest,
    db: Session = Depends(get_db)
):
    """
    Predictive Health Analytics (US-010.5)

    Provides multiple predictive models:

    1. Readmission Risk (LACE Score)
       - Length of stay, Acuity, Comorbidities, ED visits
       - 30-day readmission prediction

    2. Deterioration Detection (MEWS)
       - Modified Early Warning Score
       - Vital sign trend analysis

    3. No-Show Prediction
       - Historical patterns
       - Appointment factors

    4. Fall Risk (Morse Scale)
       - History, secondary diagnosis
       - Ambulatory aid, IV/heparin lock
       - Gait, mental status

    Example request:
    ```json
    {
      "patient_id": "uuid",
      "include_readmission": true,
      "admission_data": {
        "length_of_stay": 5,
        "acuity": "high",
        "ed_visits_6mo": 2
      }
    }
    ```
    """
    service = MedicalAIService(db)

    try:
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")

        result = await service.get_predictions(org_id, request)
        return result

    except Exception as e:
        logger.error(f"Prediction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


# ==================== Image Analysis Endpoints ====================

@router.post("/images/analyze", response_model=ImageAnalysisResponse)
async def analyze_image(
    request: ImageAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Medical Image Analysis (US-010.6)

    Analyzes medical images:

    1. Chest X-ray
       - 8 finding patterns (cardiomegaly, pneumonia, etc.)
       - Structured reporting
       - Critical finding alerts

    2. Skin Lesion
       - ABCDE criteria analysis
       - Melanoma risk assessment
       - Differential diagnoses

    3. Wound
       - Tissue composition analysis
       - Healing trajectory prediction
       - Treatment recommendations

    Accepts image via URL or base64-encoded data.

    Example request:
    ```json
    {
      "image_url": "https://...",
      "image_type": "chest_xray",
      "clinical_context": "Cough and fever for 3 days"
    }
    ```
    """
    service = MedicalAIService(db)

    try:
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")

        if not request.image_url and not request.image_base64:
            raise HTTPException(
                status_code=400,
                detail="Either image_url or image_base64 must be provided"
            )

        result = await service.analyze_image(org_id, request)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")


@router.post("/images/upload", response_model=ImageAnalysisResponse)
async def upload_and_analyze_image(
    image_type: ImageTypeEnum,
    clinical_context: str = None,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and analyze medical image

    Alternative endpoint that accepts file upload directly.
    Supported formats: JPEG, PNG, DICOM
    """
    service = MedicalAIService(db)

    try:
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")

        import base64
        content = await file.read()
        image_base64 = base64.b64encode(content).decode()

        request = ImageAnalysisRequest(
            image_base64=image_base64,
            image_type=image_type,
            clinical_context=clinical_context,
        )

        result = await service.analyze_image(org_id, request)
        return result

    except Exception as e:
        logger.error(f"Image upload and analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")


# ==================== NLP Pipeline Endpoints ====================

@router.post("/nlp/process", response_model=NLPPipelineResponse)
async def run_nlp_pipeline(
    request: NLPPipelineRequest,
    db: Session = Depends(get_db)
):
    """
    Clinical NLP Pipeline (US-010.7)

    Comprehensive clinical text processing:

    1. Section Splitting
       - 18 clinical section types
       - Structured document parsing

    2. Problem List Extraction
       - ICD-10/SNOMED mapping
       - Status tracking

    3. Medication Extraction
       - RxNorm normalization
       - Dose, route, frequency

    4. SDOH Extraction
       - 12 social determinant categories
       - Z-code mapping
       - Intervention suggestions

    5. Quality Measure Identification
       - CMS measures (CMS165, CMS122, etc.)
       - Gap in care detection

    Example request:
    ```json
    {
      "text": "HISTORY OF PRESENT ILLNESS: 55-year-old male with hypertension...",
      "include_sections": true,
      "include_problems": true,
      "include_medications": true,
      "include_sdoh": true,
      "include_quality_measures": true
    }
    ```
    """
    service = MedicalAIService(db)

    try:
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")

        result = await service.run_nlp_pipeline(org_id, request)
        return result

    except Exception as e:
        logger.error(f"NLP pipeline failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"NLP pipeline failed: {str(e)}")


# ==================== Voice Biomarker Endpoints ====================

@router.post("/voice/analyze", response_model=VoiceBiomarkerResponse)
async def analyze_voice(
    request: VoiceBiomarkerRequest,
    db: Session = Depends(get_db)
):
    """
    Voice Biomarker Analysis (US-010.8)

    Analyzes voice for health indicators:

    1. Depression Detection
       - Prosody, pitch, speech rate analysis
       - PHQ-9 equivalent scoring
       - Vocal marker identification

    2. Cognitive Assessment
       - Fluency and word-finding analysis
       - Coherence scoring
       - MCI risk detection

    3. Respiratory Assessment
       - Breath support scoring
       - Cough/wheeze/stridor detection
       - Pattern classification

    4. Longitudinal Tracking
       - Baseline comparison
       - Trend analysis

    Accepts audio via URL or base64-encoded data.
    """
    service = MedicalAIService(db)

    try:
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")

        if not request.audio_url and not request.audio_base64:
            raise HTTPException(
                status_code=400,
                detail="Either audio_url or audio_base64 must be provided"
            )

        result = await service.analyze_voice(org_id, request)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Voice analysis failed: {str(e)}")


@router.post("/voice/upload", response_model=VoiceBiomarkerResponse)
async def upload_and_analyze_voice(
    include_depression: bool = True,
    include_cognitive: bool = True,
    include_respiratory: bool = True,
    patient_id: UUID = None,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and analyze voice recording

    Alternative endpoint that accepts file upload directly.
    Supported formats: WAV, MP3, M4A, OGG
    """
    service = MedicalAIService(db)

    try:
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")

        import base64
        content = await file.read()
        audio_base64 = base64.b64encode(content).decode()

        request = VoiceBiomarkerRequest(
            audio_base64=audio_base64,
            patient_id=patient_id,
            include_depression=include_depression,
            include_cognitive=include_cognitive,
            include_respiratory=include_respiratory,
        )

        result = await service.analyze_voice(org_id, request)
        return result

    except Exception as e:
        logger.error(f"Voice upload and analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Voice analysis failed: {str(e)}")


# ==================== Statistics and Health ====================

@router.get("/stats", response_model=MedicalAIStatistics)
async def get_statistics(
    db: Session = Depends(get_db)
):
    """
    Get Medical AI usage statistics

    Returns:
    - Request counts by feature
    - Average confidence scores
    - Processing times
    - Model versions
    """
    service = MedicalAIService(db)

    try:
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")
        return service.get_statistics(org_id)

    except Exception as e:
        logger.error(f"Error getting statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get("/health/check", response_model=MedicalAIHealthCheck)
async def health_check():
    """
    Health check for Medical AI module

    Returns:
    - Module status
    - Available features
    - Model status
    - Last calibration time
    """
    service = MedicalAIService(None)
    return service.health_check()
