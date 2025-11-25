"""
Medical AI Module
EPIC-010: Medical AI Capabilities

This module provides API endpoints for:
- AI-powered medical triage (US-010.1)
- Clinical documentation AI (US-010.2)
- Medical entity recognition (US-010.3)
- Clinical decision intelligence (US-010.4)
- Predictive health analytics (US-010.5)
- Medical image analysis (US-010.6)
- Clinical NLP pipeline (US-010.7)
- Voice biomarker analysis (US-010.8)
"""

from modules.medical_ai.router import router
from modules.medical_ai.service import MedicalAIService
from modules.medical_ai.schemas import (
    # Triage
    TriageRequest,
    TriageResponse,
    # Documentation
    TranscriptionRequest,
    TranscriptionResponse,
    SOAPNoteRequest,
    SOAPNoteResponse,
    # Entity Recognition
    EntityExtractionRequest,
    EntityExtractionResponse,
    # Decision Support
    ClinicalDecisionRequest,
    ClinicalDecisionResponse,
    # Predictive Analytics
    PredictiveAnalyticsRequest,
    PredictiveAnalyticsResponse,
    # Image Analysis
    ImageAnalysisRequest,
    ImageAnalysisResponse,
    # NLP Pipeline
    NLPPipelineRequest,
    NLPPipelineResponse,
    # Voice Biomarkers
    VoiceBiomarkerRequest,
    VoiceBiomarkerResponse,
)

__all__ = [
    "router",
    "MedicalAIService",
    "TriageRequest",
    "TriageResponse",
    "TranscriptionRequest",
    "TranscriptionResponse",
    "SOAPNoteRequest",
    "SOAPNoteResponse",
    "EntityExtractionRequest",
    "EntityExtractionResponse",
    "ClinicalDecisionRequest",
    "ClinicalDecisionResponse",
    "PredictiveAnalyticsRequest",
    "PredictiveAnalyticsResponse",
    "ImageAnalysisRequest",
    "ImageAnalysisResponse",
    "NLPPipelineRequest",
    "NLPPipelineResponse",
    "VoiceBiomarkerRequest",
    "VoiceBiomarkerResponse",
]
