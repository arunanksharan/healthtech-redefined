"""
AI Platform Schemas
Pydantic schemas for AI API requests and responses

EPIC-009: Core AI Integration
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field, validator


# ==================== Enums ====================

class AIProviderType(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    LOCAL = "local"
    HUGGINGFACE = "huggingface"


class AIRequestType(str, Enum):
    CHAT_COMPLETION = "chat_completion"
    STREAMING = "streaming"
    EMBEDDING = "embedding"
    NER = "ner"
    CLASSIFICATION = "classification"
    TRIAGE = "triage"
    DOCUMENTATION = "documentation"
    SEMANTIC_SEARCH = "semantic_search"
    FUNCTION_CALL = "function_call"


class ConversationStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    WAITING_INPUT = "waiting_input"
    COMPLETED = "completed"
    ESCALATED = "escalated"


class ConversationType(str, Enum):
    GENERAL_INQUIRY = "general_inquiry"
    APPOINTMENT_BOOKING = "appointment_booking"
    SYMPTOM_ASSESSMENT = "symptom_assessment"
    MEDICATION_QUESTION = "medication_question"
    BILLING_INQUIRY = "billing_inquiry"
    PRESCRIPTION_REFILL = "prescription_refill"
    LAB_RESULTS = "lab_results"
    PROVIDER_MESSAGE = "provider_message"


class DocumentType(str, Enum):
    CLINICAL_GUIDELINE = "clinical_guideline"
    DRUG_INFO = "drug_info"
    MEDICAL_LITERATURE = "medical_literature"
    PROTOCOL = "protocol"
    POLICY = "policy"
    FAQ = "faq"
    PATIENT_EDUCATION = "patient_education"
    PROCEDURE = "procedure"
    DIAGNOSIS = "diagnosis"
    TREATMENT = "treatment"


class EvidenceLevel(str, Enum):
    LEVEL_A = "A"
    LEVEL_B = "B"
    LEVEL_C = "C"
    LEVEL_D = "D"
    NOT_APPLICABLE = "N/A"


class UrgencyLevel(str, Enum):
    EMERGENCY = "emergency"
    URGENT = "urgent"
    SOON = "soon"
    ROUTINE = "routine"
    SELF_CARE = "self_care"


class QualityRating(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    FAILED = "failed"


class MaskingStrategy(str, Enum):
    REDACT = "redact"
    PSEUDONYMIZE = "pseudonymize"
    HASH = "hash"
    GENERALIZE = "generalize"
    SUPPRESS = "suppress"


class PHIType(str, Enum):
    NAME = "name"
    DATE_OF_BIRTH = "date_of_birth"
    SSN = "ssn"
    MRN = "mrn"
    PHONE = "phone"
    EMAIL = "email"
    ADDRESS = "address"
    ZIP_CODE = "zip_code"
    ACCOUNT_NUMBER = "account_number"
    INSURANCE_ID = "insurance_id"
    IP_ADDRESS = "ip_address"


# ==================== Chat Completion Schemas ====================

class ChatMessage(BaseModel):
    """Chat message."""
    role: str = Field(..., description="Message role: system, user, assistant, function")
    content: str = Field(..., description="Message content")
    name: Optional[str] = Field(None, description="Name for function messages")
    function_call: Optional[Dict[str, Any]] = Field(None, description="Function call details")


class ChatCompletionRequest(BaseModel):
    """Request for chat completion."""
    messages: List[ChatMessage] = Field(..., min_items=1, description="Conversation messages")
    model: Optional[str] = Field("gpt-4", description="Model to use")
    temperature: Optional[float] = Field(0.7, ge=0, le=2, description="Sampling temperature")
    max_tokens: Optional[int] = Field(1000, ge=1, le=8000, description="Maximum tokens")
    stream: Optional[bool] = Field(False, description="Enable streaming")
    functions: Optional[List[Dict[str, Any]]] = Field(None, description="Function definitions")

    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {"role": "system", "content": "You are a helpful medical assistant."},
                    {"role": "user", "content": "What are the symptoms of diabetes?"}
                ],
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 500
            }
        }


class ChatCompletionResponse(BaseModel):
    """Response from chat completion."""
    completion_id: UUID
    model: str
    message: ChatMessage
    finish_reason: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_ms: float
    estimated_cost_usd: float
    created_at: datetime


# ==================== Conversation Schemas ====================

class ConversationCreate(BaseModel):
    """Create a new conversation."""
    conversation_type: ConversationType = ConversationType.GENERAL_INQUIRY
    patient_id: Optional[UUID] = None
    channel: Optional[str] = Field("web", description="Channel: web, whatsapp, voice")
    language: Optional[str] = Field("en", description="Language code")
    initial_context: Optional[Dict[str, Any]] = Field(None, description="Initial context")


class ConversationMessageSend(BaseModel):
    """Send a message in a conversation."""
    content: str = Field(..., min_length=1, max_length=5000, description="Message content")


class ConversationMessageResponse(BaseModel):
    """Response message in a conversation."""
    message_id: UUID
    role: str
    content: str
    intent_type: Optional[str] = None
    intent_confidence: Optional[float] = None
    created_at: datetime


class ConversationResponse(BaseModel):
    """Full conversation response."""
    conversation_id: UUID
    conversation_type: ConversationType
    status: ConversationStatus
    patient_id: Optional[UUID]
    channel: str
    language: str
    turn_count: int
    total_tokens_used: int
    total_cost_usd: float
    messages: List[ConversationMessageResponse]
    context: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    ended_at: Optional[datetime]


class ConversationEndRequest(BaseModel):
    """End a conversation."""
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=5, description="Rating 1-5")
    feedback: Optional[str] = Field(None, max_length=2000, description="User feedback")


# ==================== Triage Schemas ====================

class SymptomInput(BaseModel):
    """Input symptom for triage."""
    name: str = Field(..., description="Symptom name")
    description: Optional[str] = Field(None, description="Symptom description")
    severity: int = Field(5, ge=1, le=10, description="Severity 1-10")
    duration: Optional[str] = Field(None, description="Duration: '2 days', '1 week'")
    onset: Optional[str] = Field(None, description="Onset: 'sudden', 'gradual'")
    location: Optional[str] = Field(None, description="Body location")
    aggravating_factors: Optional[List[str]] = Field(None, description="What makes it worse")
    relieving_factors: Optional[List[str]] = Field(None, description="What makes it better")
    associated_symptoms: Optional[List[str]] = Field(None, description="Related symptoms")


class TriageRequest(BaseModel):
    """Request for symptom triage."""
    symptoms: List[SymptomInput] = Field(..., min_items=1, description="Patient symptoms")
    patient_age: Optional[int] = Field(None, ge=0, le=150, description="Patient age")
    patient_sex: Optional[str] = Field(None, description="Patient sex: M, F, Other")
    medical_history: Optional[List[str]] = Field(None, description="Medical history")
    current_medications: Optional[List[str]] = Field(None, description="Current medications")

    class Config:
        json_schema_extra = {
            "example": {
                "symptoms": [
                    {
                        "name": "chest pain",
                        "severity": 7,
                        "duration": "2 hours",
                        "onset": "sudden"
                    }
                ],
                "patient_age": 55,
                "patient_sex": "M",
                "medical_history": ["hypertension", "diabetes"]
            }
        }


class TriageResponse(BaseModel):
    """Triage assessment response."""
    triage_id: UUID
    urgency_level: UrgencyLevel
    urgency_score: int = Field(..., ge=0, le=100)
    primary_concern: str
    contributing_factors: List[str]
    red_flags_identified: List[str]
    recommended_action: str
    timeframe: str
    care_setting: str
    self_care_advice: List[str]
    warning_signs: List[str]
    confidence_score: float
    disclaimer: str
    created_at: datetime


# ==================== NLP Schemas ====================

class EntityExtractionRequest(BaseModel):
    """Request for medical entity extraction."""
    text: str = Field(..., min_length=1, max_length=10000, description="Text to analyze")
    entity_types: Optional[List[str]] = Field(None, description="Entity types to extract")


class ClinicalEntityResponse(BaseModel):
    """Extracted clinical entity."""
    entity_id: UUID
    entity_type: str
    text: str
    normalized_text: str
    start_offset: int
    end_offset: int
    codes: List[Dict[str, str]]  # [{"system": "SNOMED", "code": "...", "display": "..."}]
    negation_status: str
    confidence: float


class EntityExtractionResponse(BaseModel):
    """Response from entity extraction."""
    extraction_id: UUID
    entities: List[ClinicalEntityResponse]
    processing_time_ms: float
    created_at: datetime


class CodingSuggestionRequest(BaseModel):
    """Request for medical coding suggestions."""
    text: str = Field(..., min_length=1, max_length=10000)
    code_system: str = Field("ICD-10", description="Code system: ICD-10, SNOMED, CPT")
    max_suggestions: int = Field(5, ge=1, le=20)


class CodingSuggestionResponse(BaseModel):
    """Suggested medical code."""
    code: str
    system: str
    display: str
    confidence: float
    evidence_text: str


# ==================== Knowledge Base Schemas ====================

class KnowledgeDocumentCreate(BaseModel):
    """Create a medical knowledge document."""
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=10, max_length=100000)
    document_type: DocumentType
    specialty: Optional[str] = Field(None, max_length=100)
    condition_codes: Optional[List[str]] = Field(None, description="ICD-10 codes")
    procedure_codes: Optional[List[str]] = Field(None, description="CPT codes")
    snomed_codes: Optional[List[str]] = Field(None, description="SNOMED CT codes")
    drug_codes: Optional[List[str]] = Field(None, description="RxNorm codes")
    source: Optional[str] = Field(None, max_length=500)
    source_url: Optional[str] = Field(None, max_length=1000)
    author: Optional[str] = Field(None, max_length=200)
    publication_date: Optional[datetime] = None
    evidence_level: EvidenceLevel = EvidenceLevel.NOT_APPLICABLE


class KnowledgeDocumentResponse(BaseModel):
    """Knowledge document response."""
    document_id: UUID
    title: str
    content: str
    document_type: DocumentType
    specialty: Optional[str]
    condition_codes: List[str]
    procedure_codes: List[str]
    snomed_codes: List[str]
    drug_codes: List[str]
    keywords: List[str]
    source: Optional[str]
    evidence_level: EvidenceLevel
    is_indexed: bool
    chunk_count: int
    created_at: datetime
    indexed_at: Optional[datetime]


class SemanticSearchRequest(BaseModel):
    """Request for semantic search."""
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(10, ge=1, le=50)
    document_types: Optional[List[DocumentType]] = None
    specialties: Optional[List[str]] = None
    evidence_levels: Optional[List[EvidenceLevel]] = None
    condition_codes: Optional[List[str]] = None
    min_similarity: float = Field(0.5, ge=0, le=1)

    class Config:
        json_schema_extra = {
            "example": {
                "query": "treatment for hypertension in diabetic patients",
                "top_k": 5,
                "document_types": ["clinical_guideline"],
                "evidence_levels": ["A", "B"]
            }
        }


class SearchResultResponse(BaseModel):
    """Search result."""
    chunk_id: UUID
    document_id: UUID
    text: str
    similarity_score: float
    keyword_score: float
    combined_score: float
    document_title: str
    document_type: Optional[DocumentType]
    specialty: Optional[str]
    evidence_level: Optional[EvidenceLevel]
    source: Optional[str]


class RAGContextResponse(BaseModel):
    """RAG context for generation."""
    query: str
    context_text: str
    sources: List[Dict[str, str]]
    total_chunks: int
    total_tokens_estimate: int


# ==================== PHI Protection Schemas ====================

class PHIDetectionRequest(BaseModel):
    """Request for PHI detection."""
    text: str = Field(..., min_length=1, max_length=50000)
    phi_types: Optional[List[PHIType]] = Field(None, description="Specific PHI types to detect")


class PHIEntityResponse(BaseModel):
    """Detected PHI entity."""
    entity_id: UUID
    phi_type: PHIType
    original_text: str
    start_offset: int
    end_offset: int
    confidence: float
    masked_text: Optional[str]


class DeidentificationRequest(BaseModel):
    """Request for text de-identification."""
    text: str = Field(..., min_length=1, max_length=50000)
    strategy: MaskingStrategy = MaskingStrategy.PSEUDONYMIZE
    phi_types: Optional[List[PHIType]] = None
    preserve_format: bool = True
    reason: Optional[str] = Field(None, max_length=500)


class DeidentificationResponse(BaseModel):
    """De-identification response."""
    result_id: UUID
    deidentified_text: str
    phi_entities: List[PHIEntityResponse]
    phi_count: int
    processing_time_ms: float
    created_at: datetime


class ReidentificationRequest(BaseModel):
    """Request for re-identification."""
    result_id: UUID = Field(..., description="Original de-identification result ID")
    text: str = Field(..., description="De-identified text to restore")
    reason: str = Field(..., min_length=1, max_length=500, description="Reason for re-identification")
    consent_verified: bool = Field(False, description="Whether consent was verified")


# ==================== Consent Schemas ====================

class ConsentCreate(BaseModel):
    """Create patient consent for AI processing."""
    patient_id: UUID
    purpose: str = Field(..., description="Purpose: ai_processing, research, analytics")
    granted: bool = True
    allowed_phi_types: Optional[List[PHIType]] = None
    allowed_uses: Optional[List[str]] = None
    expires_at: Optional[datetime] = None


class ConsentResponse(BaseModel):
    """Consent record response."""
    consent_id: UUID
    patient_id: UUID
    purpose: str
    granted: bool
    granted_at: datetime
    expires_at: Optional[datetime]
    allowed_phi_types: List[str]
    allowed_uses: List[str]
    revoked: bool
    revoked_at: Optional[datetime]


# ==================== Monitoring Schemas ====================

class AIMetricsRequest(BaseModel):
    """Request for AI metrics."""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    request_type: Optional[AIRequestType] = None
    provider: Optional[AIProviderType] = None
    model: Optional[str] = None


class AIMetricsResponse(BaseModel):
    """AI metrics response."""
    period_start: datetime
    period_end: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    total_cost_usd: float
    avg_cost_per_request_usd: float
    error_rate: float
    by_request_type: Dict[str, int]
    by_provider: Dict[str, int]
    by_model: Dict[str, int]
    errors_by_type: Dict[str, int]


class CostSummaryResponse(BaseModel):
    """Cost summary response."""
    period: str  # hourly, daily
    costs: Dict[str, float]  # {date: cost}
    total_cost_usd: float


# ==================== A/B Testing Schemas ====================

class ExperimentCreate(BaseModel):
    """Create an A/B experiment."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    variants: Dict[str, Dict[str, Any]] = Field(..., description="Variant configurations")
    traffic_split: Dict[str, float] = Field(..., description="Traffic allocation per variant")
    primary_metric: Optional[str] = Field(None, description="Primary metric to track")

    @validator("traffic_split")
    def validate_traffic_split(cls, v):
        if abs(sum(v.values()) - 1.0) > 0.001:
            raise ValueError("Traffic split must sum to 1.0")
        return v


class ExperimentResponse(BaseModel):
    """Experiment response."""
    experiment_id: UUID
    name: str
    description: Optional[str]
    status: str
    variants: Dict[str, Dict[str, Any]]
    traffic_split: Dict[str, float]
    results: Dict[str, Any]
    winning_variant: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    ended_at: Optional[datetime]


# ==================== Prompt Template Schemas ====================

class PromptTemplateCreate(BaseModel):
    """Create a prompt template."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    category: str = Field(..., description="Category: triage, documentation, chat")
    system_prompt: str = Field(..., min_length=1, max_length=10000)
    user_template: str = Field(..., min_length=1, max_length=10000)
    variables: List[str] = Field(default_factory=list)
    default_model: Optional[str] = None
    default_temperature: float = Field(0.7, ge=0, le=2)
    default_max_tokens: int = Field(1000, ge=1, le=8000)


class PromptTemplateResponse(BaseModel):
    """Prompt template response."""
    template_id: UUID
    name: str
    description: Optional[str]
    category: str
    version: int
    system_prompt: str
    user_template: str
    variables: List[str]
    default_model: Optional[str]
    default_temperature: float
    default_max_tokens: int
    use_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PromptTemplateRenderRequest(BaseModel):
    """Render a prompt template."""
    template_id: UUID
    variables: Dict[str, Any] = Field(..., description="Variable values")


# ==================== Cost Alert Schemas ====================

class CostAlertCreate(BaseModel):
    """Create a cost alert."""
    name: str = Field(..., min_length=1, max_length=200)
    threshold_usd: float = Field(..., gt=0)
    period: str = Field(..., description="Alert period: hourly, daily, monthly")
    notify_emails: Optional[List[str]] = None
    notify_webhook_url: Optional[str] = None


class CostAlertResponse(BaseModel):
    """Cost alert response."""
    alert_id: UUID
    name: str
    threshold_usd: float
    period: str
    notify_emails: List[str]
    notify_webhook_url: Optional[str]
    is_active: bool
    last_triggered_at: Optional[datetime]
    trigger_count: int
    created_at: datetime


# ==================== Quality Rating Schemas ====================

class QualityRatingRequest(BaseModel):
    """Rate AI response quality."""
    request_id: UUID
    rating: QualityRating
    feedback: Optional[str] = Field(None, max_length=2000)


class QualityMetricsResponse(BaseModel):
    """Quality metrics response."""
    total_requests: int
    rated_requests: int
    rating_rate: float
    quality_distribution: Dict[str, int]
    avg_confidence_score: Optional[float]
    excellent_rate: float
    poor_rate: float


# ==================== Documentation Schemas ====================

class DocumentationRequest(BaseModel):
    """Request for clinical documentation generation."""
    documentation_type: str = Field(..., description="Type: soap_note, progress_note, discharge_summary")
    clinical_input: str = Field(..., min_length=10, max_length=20000)
    patient_context: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "documentation_type": "soap_note",
                "clinical_input": "Patient presents with 2-day history of sore throat and fever. Temperature 101.2F. Throat exam shows erythema and tonsillar exudate."
            }
        }


class DocumentationResponse(BaseModel):
    """Generated documentation response."""
    suggestion_id: UUID
    documentation_type: str
    suggested_text: str
    sections: Dict[str, str]
    extracted_codes: List[Dict[str, str]]
    extracted_medications: List[str]
    extracted_diagnoses: List[str]
    confidence_score: float
    requires_review: bool
    disclaimer: str
    created_at: datetime


# ==================== Health Check ====================

class AIHealthResponse(BaseModel):
    """AI module health check response."""
    status: str
    module: str
    features: List[str]
    llm_provider: str
    embedding_model: str
    knowledge_base_documents: int
    knowledge_base_chunks: int
    active_experiments: int
