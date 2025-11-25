"""
AI Integration Module

Comprehensive AI capabilities for healthcare:
- LLM integration for conversational AI
- Medical NLP for clinical text processing
- Clinical decision support AI
- Triage and symptom analysis
- Documentation assistance
- Predictive analytics
- AI monitoring and observability
- PHI protection and de-identification
- Vector search for medical knowledge

EPIC-009: Core AI Integration
EPIC-010: Medical AI Capabilities
"""

from .llm_service import (
    LLMService,
    LLMProvider,
    ChatMessage,
    ChatCompletion,
)
from .medical_nlp import (
    MedicalNLPService,
    EntityExtraction,
    ClinicalEntity,
)
from .conversational import (
    ConversationalAI,
    Conversation,
    ConversationContext,
)
from .medical_ai import (
    MedicalAIService,
    TriageResult,
    SymptomAnalysis,
    DocumentationSuggestion,
)
from .monitoring import (
    AIMonitoringService,
    AIRequestLog,
    AIMetrics,
    AIRequestType,
    AIProvider,
    CostAlert,
    ABExperiment,
    ai_monitoring_service,
)
from .phi_protection import (
    PHIProtectionService,
    PHIType,
    MaskingStrategy,
    PHIEntity,
    DeidentificationResult,
    PHIAuditLog,
    ConsentRecord,
    phi_protection_service,
)
from .vector_search import (
    VectorSearchService,
    DocumentType,
    EvidenceLevel,
    MedicalDocument,
    DocumentChunk,
    SearchResult,
    SearchQuery,
    RAGContext,
    vector_search_service,
)

__all__ = [
    # LLM Service
    "LLMService",
    "LLMProvider",
    "ChatMessage",
    "ChatCompletion",
    # Medical NLP
    "MedicalNLPService",
    "EntityExtraction",
    "ClinicalEntity",
    # Conversational AI
    "ConversationalAI",
    "Conversation",
    "ConversationContext",
    # Medical AI
    "MedicalAIService",
    "TriageResult",
    "SymptomAnalysis",
    "DocumentationSuggestion",
    # AI Monitoring (US-009.7)
    "AIMonitoringService",
    "AIRequestLog",
    "AIMetrics",
    "AIRequestType",
    "AIProvider",
    "CostAlert",
    "ABExperiment",
    "ai_monitoring_service",
    # PHI Protection (US-009.8)
    "PHIProtectionService",
    "PHIType",
    "MaskingStrategy",
    "PHIEntity",
    "DeidentificationResult",
    "PHIAuditLog",
    "ConsentRecord",
    "phi_protection_service",
    # Vector Search (US-009.5)
    "VectorSearchService",
    "DocumentType",
    "EvidenceLevel",
    "MedicalDocument",
    "DocumentChunk",
    "SearchResult",
    "SearchQuery",
    "RAGContext",
    "vector_search_service",
]
