"""
Clinical Decision Support (CDS) Module

This module provides comprehensive CDS capabilities including:
- Drug-drug interaction checking
- Drug-allergy alert system
- Drug-disease contraindication checking
- Clinical guidelines integration
- Quality measure evaluation (CQL-based)
- Care gap detection and management
- CDS Hooks implementation for EHR integration
- Alert management and optimization
- AI-powered diagnostic support

EPIC-020: Clinical Decision Support
"""

from modules.cds.models import (
    # Enums
    InteractionSeverity,
    InteractionType,
    AlertTier,
    AlertStatus,
    OverrideReason,
    GuidelineCategory,
    GuidelineSource,
    MeasureType,
    MeasureStatus,
    CareGapPriority,
    CareGapStatus,
    CDSHookType,
    CDSCardType,
    DiagnosisSuggestionSource,
    # Drug Models
    DrugDatabase,
    DrugInteractionRule,
    DrugAllergyMapping,
    DrugDiseaseContraindication,
    # Alert Models
    CDSAlert,
    AlertOverride,
    AlertConfiguration,
    AlertAnalytics,
    # Guideline Models
    ClinicalGuideline,
    GuidelineAccess,
    # Quality Measure Models
    QualityMeasure,
    PatientMeasure,
    CareGap,
    # CDS Hooks Models
    CDSService,
    CDSHookInvocation,
    CDSCard,
    # Diagnostic Models
    DiagnosticSession,
    DiagnosisSuggestion,
    DiagnosticFeedback,
)

from modules.cds.router import router

from modules.cds.services import (
    DrugInteractionService,
    AllergyService,
    GuidelineService,
    QualityMeasureService,
    CDSHooksService,
    AlertManagementService,
    DiagnosticService,
)

__all__ = [
    # Router
    "router",
    # Enums
    "InteractionSeverity",
    "InteractionType",
    "AlertTier",
    "AlertStatus",
    "OverrideReason",
    "GuidelineCategory",
    "GuidelineSource",
    "MeasureType",
    "MeasureStatus",
    "CareGapPriority",
    "CareGapStatus",
    "CDSHookType",
    "CDSCardType",
    "DiagnosisSuggestionSource",
    # Drug Models
    "DrugDatabase",
    "DrugInteractionRule",
    "DrugAllergyMapping",
    "DrugDiseaseContraindication",
    # Alert Models
    "CDSAlert",
    "AlertOverride",
    "AlertConfiguration",
    "AlertAnalytics",
    # Guideline Models
    "ClinicalGuideline",
    "GuidelineAccess",
    # Quality Measure Models
    "QualityMeasure",
    "PatientMeasure",
    "CareGap",
    # CDS Hooks Models
    "CDSService",
    "CDSHookInvocation",
    "CDSCard",
    # Diagnostic Models
    "DiagnosticSession",
    "DiagnosisSuggestion",
    "DiagnosticFeedback",
    # Services
    "DrugInteractionService",
    "AllergyService",
    "GuidelineService",
    "QualityMeasureService",
    "CDSHooksService",
    "AlertManagementService",
    "DiagnosticService",
]
