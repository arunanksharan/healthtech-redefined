"""
Medical AI Module - EPIC-010: Medical AI Capabilities

This module provides advanced healthcare-specific AI services including:
- AI-powered medical triage with symptom analysis
- Clinical documentation AI (SOAP notes, coding)
- Medical entity recognition and normalization
- Clinical decision intelligence and guidelines
- Predictive health analytics
- Medical image analysis
- Clinical NLP pipeline
- Voice biomarker analysis
"""

from backend.shared.medical_ai.triage_engine import (
    triage_engine,
    TriageEngine,
    SymptomAnalyzer,
    RedFlagDetector,
    DepartmentRouter,
    TriageResult,
    SymptomAnalysis,
    RedFlagAlert,
    UrgencyLevel,
    TriageExplanation,
)

from backend.shared.medical_ai.documentation_ai import (
    ambient_transcription_service,
    soap_generator,
    code_suggester,
    template_engine,
    AmbientTranscriptionService,
    SOAPNoteGenerator,
    MedicalCodeSuggester,
    DocumentationTemplateEngine,
    TranscriptionResult,
    SpeakerSegment,
    SOAPNote,
    CodeSuggestion,
    DocumentTemplate,
)

from backend.shared.medical_ai.entity_recognition import (
    medical_entity_extractor,
    MedicalEntityExtractor,
    MedicalEntity,
    EntityRelationship,
    NegationStatus,
    EntityType,
)

from backend.shared.medical_ai.decision_intelligence import (
    clinical_decision_intelligence,
    ClinicalDecisionIntelligence,
    ClinicalGuidelineEngine,
    DrugInteractionChecker,
    DiagnosticEngine,
    GuidelineRecommendation,
    DrugInteraction,
    DifferentialDiagnosis,
    TreatmentRecommendation,
    InteractionSeverity,
)

from backend.shared.medical_ai.predictive_analytics import (
    predictive_analytics_service,
    PredictiveAnalyticsService,
    ReadmissionRiskModel,
    DeteriorationDetector,
    NoShowPredictor,
    ReadmissionRisk,
    DeteriorationAlert,
    NoShowPrediction,
    RiskLevel,
    LACEScore,
    MEWSScore,
    MorseFallScore,
)

from backend.shared.medical_ai.image_analysis import (
    medical_image_analysis_service,
    MedicalImageAnalysisService,
    ChestXrayAnalyzer,
    SkinLesionAnalyzer,
    WoundAnalyzer,
    ChestXrayResult,
    RadiologyFinding,
    SkinLesionResult,
    ABCDEScore,
    WoundAssessment,
    WoundTissueComposition,
)

from backend.shared.medical_ai.nlp_pipeline import (
    clinical_nlp_pipeline,
    ClinicalNLPPipeline,
    ClinicalSectionSplitter,
    ProblemListExtractor,
    MedicationExtractor,
    SocialDeterminantsExtractor,
    QualityMeasureIdentifier,
    ClinicalSection,
    ProblemEntry,
    MedicationEntry,
    SocialDeterminant,
    QualityMeasure,
)

from backend.shared.medical_ai.voice_biomarkers import (
    voice_biomarker_service,
    VoiceBiomarkerService,
    AudioFeatureExtractor,
    DepressionDetector,
    CognitiveAssessor,
    RespiratoryAnalyzer,
    AudioFeatures,
    DepressionAssessment,
    CognitiveAssessment,
    RespiratoryAssessment,
    VoiceBiomarkerAnalysis,
)

__all__ = [
    # Triage Engine
    "triage_engine",
    "TriageEngine",
    "SymptomAnalyzer",
    "RedFlagDetector",
    "DepartmentRouter",
    "TriageResult",
    "SymptomAnalysis",
    "RedFlagAlert",
    "UrgencyLevel",
    "TriageExplanation",
    # Documentation AI
    "ambient_transcription_service",
    "soap_generator",
    "code_suggester",
    "template_engine",
    "AmbientTranscriptionService",
    "SOAPNoteGenerator",
    "MedicalCodeSuggester",
    "DocumentationTemplateEngine",
    "TranscriptionResult",
    "SpeakerSegment",
    "SOAPNote",
    "CodeSuggestion",
    "DocumentTemplate",
    # Entity Recognition
    "medical_entity_extractor",
    "MedicalEntityExtractor",
    "MedicalEntity",
    "EntityRelationship",
    "NegationStatus",
    "EntityType",
    # Decision Intelligence
    "clinical_decision_intelligence",
    "ClinicalDecisionIntelligence",
    "ClinicalGuidelineEngine",
    "DrugInteractionChecker",
    "DiagnosticEngine",
    "GuidelineRecommendation",
    "DrugInteraction",
    "DifferentialDiagnosis",
    "TreatmentRecommendation",
    "InteractionSeverity",
    # Predictive Analytics
    "predictive_analytics_service",
    "PredictiveAnalyticsService",
    "ReadmissionRiskModel",
    "DeteriorationDetector",
    "NoShowPredictor",
    "ReadmissionRisk",
    "DeteriorationAlert",
    "NoShowPrediction",
    "RiskLevel",
    "LACEScore",
    "MEWSScore",
    "MorseFallScore",
    # Image Analysis
    "medical_image_analysis_service",
    "MedicalImageAnalysisService",
    "ChestXrayAnalyzer",
    "SkinLesionAnalyzer",
    "WoundAnalyzer",
    "ChestXrayResult",
    "RadiologyFinding",
    "SkinLesionResult",
    "ABCDEScore",
    "WoundAssessment",
    "WoundTissueComposition",
    # NLP Pipeline
    "clinical_nlp_pipeline",
    "ClinicalNLPPipeline",
    "ClinicalSectionSplitter",
    "ProblemListExtractor",
    "MedicationExtractor",
    "SocialDeterminantsExtractor",
    "QualityMeasureIdentifier",
    "ClinicalSection",
    "ProblemEntry",
    "MedicationEntry",
    "SocialDeterminant",
    "QualityMeasure",
    # Voice Biomarkers
    "voice_biomarker_service",
    "VoiceBiomarkerService",
    "AudioFeatureExtractor",
    "DepressionDetector",
    "CognitiveAssessor",
    "RespiratoryAnalyzer",
    "AudioFeatures",
    "DepressionAssessment",
    "CognitiveAssessment",
    "RespiratoryAssessment",
    "VoiceBiomarkerAnalysis",
]
