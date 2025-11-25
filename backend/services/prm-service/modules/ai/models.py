"""
AI Platform Models
SQLAlchemy models for AI platform persistence

EPIC-009: Core AI Integration
"""

from datetime import datetime, timezone
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime,
    ForeignKey, Enum, JSON, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import enum

from shared.database.connection import Base


# ==================== Enums ====================

class AIProviderType(str, enum.Enum):
    """AI provider types."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    LOCAL = "local"
    HUGGINGFACE = "huggingface"


class AIRequestType(str, enum.Enum):
    """Types of AI requests."""
    CHAT_COMPLETION = "chat_completion"
    STREAMING = "streaming"
    EMBEDDING = "embedding"
    NER = "ner"
    CLASSIFICATION = "classification"
    TRIAGE = "triage"
    DOCUMENTATION = "documentation"
    SEMANTIC_SEARCH = "semantic_search"
    FUNCTION_CALL = "function_call"


class ConversationStatus(str, enum.Enum):
    """Conversation status."""
    ACTIVE = "active"
    PAUSED = "paused"
    WAITING_INPUT = "waiting_input"
    COMPLETED = "completed"
    ESCALATED = "escalated"


class ConversationType(str, enum.Enum):
    """Conversation type."""
    GENERAL_INQUIRY = "general_inquiry"
    APPOINTMENT_BOOKING = "appointment_booking"
    SYMPTOM_ASSESSMENT = "symptom_assessment"
    MEDICATION_QUESTION = "medication_question"
    BILLING_INQUIRY = "billing_inquiry"
    PRESCRIPTION_REFILL = "prescription_refill"
    LAB_RESULTS = "lab_results"
    PROVIDER_MESSAGE = "provider_message"


class DocumentType(str, enum.Enum):
    """Medical document types."""
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


class EvidenceLevel(str, enum.Enum):
    """Evidence level for medical content."""
    LEVEL_A = "A"
    LEVEL_B = "B"
    LEVEL_C = "C"
    LEVEL_D = "D"
    NOT_APPLICABLE = "N/A"


class PHIActionType(str, enum.Enum):
    """PHI audit action types."""
    DETECT = "detect"
    DEIDENTIFY = "deidentify"
    REIDENTIFY = "reidentify"
    ACCESS = "access"
    CONSENT_RECORD = "consent_record"
    CONSENT_REVOKE = "consent_revoke"


class ExperimentStatus(str, enum.Enum):
    """A/B experiment status."""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"


# ==================== AI Request Logging ====================

class AIRequestLog(Base):
    """Log of AI API requests for monitoring and cost tracking."""
    __tablename__ = "ai_request_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Request details
    request_type = Column(Enum(AIRequestType), nullable=False)
    provider = Column(Enum(AIProviderType), nullable=False)
    model = Column(String(100), nullable=False)
    prompt_hash = Column(String(64), nullable=False)  # SHA256 hash for privacy

    # Token usage
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)

    # Performance
    latency_ms = Column(Float, default=0)
    time_to_first_token_ms = Column(Float, nullable=True)
    finish_reason = Column(String(50), default="stop")

    # Cost
    estimated_cost_usd = Column(Float, default=0)

    # Status
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    error_type = Column(String(100), nullable=True)

    # Quality
    confidence_score = Column(Float, nullable=True)
    quality_rating = Column(String(20), nullable=True)  # excellent, good, acceptable, poor

    # Context
    user_id = Column(UUID(as_uuid=True), nullable=True)
    session_id = Column(UUID(as_uuid=True), nullable=True)
    conversation_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    feature = Column(String(50), nullable=True)  # triage, documentation, etc.

    # A/B Testing
    experiment_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    variant = Column(String(50), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_ai_request_logs_tenant_created", "tenant_id", "created_at"),
        Index("ix_ai_request_logs_model", "model"),
        Index("ix_ai_request_logs_request_type", "request_type"),
    )


# ==================== AI Conversations ====================

class AIConversation(Base):
    """AI conversation session."""
    __tablename__ = "ai_conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Conversation details
    conversation_type = Column(Enum(ConversationType), nullable=False)
    status = Column(Enum(ConversationStatus), default=ConversationStatus.ACTIVE)

    # Participants
    patient_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    assigned_agent_id = Column(UUID(as_uuid=True), nullable=True)

    # Channel
    channel = Column(String(50), default="web")  # web, whatsapp, voice
    language = Column(String(10), default="en")

    # Context
    context = Column(JSON, default=dict)  # Conversation context data

    # Metrics
    turn_count = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    total_cost_usd = Column(Float, default=0)

    # Escalation
    escalation_reason = Column(Text, nullable=True)
    escalated_at = Column(DateTime(timezone=True), nullable=True)

    # Satisfaction
    satisfaction_rating = Column(Integer, nullable=True)  # 1-5
    feedback = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    messages = relationship("AIConversationMessage", back_populates="conversation", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_ai_conversations_tenant_status", "tenant_id", "status"),
        Index("ix_ai_conversations_patient", "patient_id"),
    )


class AIConversationMessage(Base):
    """Individual message in an AI conversation."""
    __tablename__ = "ai_conversation_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False)

    # Message content
    role = Column(String(20), nullable=False)  # system, user, assistant, function
    content = Column(Text, nullable=False)

    # Intent (for user messages)
    intent_type = Column(String(50), nullable=True)
    intent_confidence = Column(Float, nullable=True)
    intent_entities = Column(JSON, nullable=True)

    # AI details (for assistant messages)
    model_used = Column(String(100), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    latency_ms = Column(Float, nullable=True)

    # Function call
    function_name = Column(String(100), nullable=True)
    function_args = Column(JSON, nullable=True)
    function_result = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    conversation = relationship("AIConversation", back_populates="messages")

    __table_args__ = (
        Index("ix_ai_messages_conversation", "conversation_id", "created_at"),
    )


# ==================== Medical Knowledge Base ====================

class MedicalKnowledgeDocument(Base):
    """Medical knowledge document for RAG."""
    __tablename__ = "medical_knowledge_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Document info
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)

    # Medical metadata
    specialty = Column(String(100), nullable=True)
    condition_codes = Column(ARRAY(String), default=list)  # ICD-10
    procedure_codes = Column(ARRAY(String), default=list)  # CPT
    snomed_codes = Column(ARRAY(String), default=list)
    drug_codes = Column(ARRAY(String), default=list)  # RxNorm
    keywords = Column(ARRAY(String), default=list)

    # Source
    source = Column(String(500), nullable=True)
    source_url = Column(String(1000), nullable=True)
    author = Column(String(200), nullable=True)
    publication_date = Column(DateTime(timezone=True), nullable=True)

    # Evidence
    evidence_level = Column(Enum(EvidenceLevel), default=EvidenceLevel.NOT_APPLICABLE)

    # Indexing status
    is_indexed = Column(Boolean, default=False)
    indexed_at = Column(DateTime(timezone=True), nullable=True)
    chunk_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    chunks = relationship("MedicalKnowledgeChunk", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_knowledge_docs_tenant_type", "tenant_id", "document_type"),
        Index("ix_knowledge_docs_specialty", "specialty"),
    )


class MedicalKnowledgeChunk(Base):
    """Chunk of a medical knowledge document for vector indexing."""
    __tablename__ = "medical_knowledge_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("medical_knowledge_documents.id", ondelete="CASCADE"), nullable=False)

    # Chunk content
    text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    start_offset = Column(Integer, nullable=False)
    end_offset = Column(Integer, nullable=False)

    # Embedding (stored as JSON for compatibility)
    embedding = Column(JSON, nullable=True)  # In production, use pgvector

    # Metadata
    metadata = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    document = relationship("MedicalKnowledgeDocument", back_populates="chunks")

    __table_args__ = (
        Index("ix_knowledge_chunks_document", "document_id", "chunk_index"),
    )


# ==================== PHI Audit Logging ====================

class PHIAuditLog(Base):
    """Audit log for PHI access and processing."""
    __tablename__ = "phi_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Action
    action = Column(Enum(PHIActionType), nullable=False)
    resource_type = Column(String(50), nullable=False)  # text, document, record
    resource_id = Column(String(255), nullable=True)

    # Actor
    user_id = Column(UUID(as_uuid=True), nullable=True)
    service_name = Column(String(100), nullable=True)

    # PHI details
    phi_types_detected = Column(ARRAY(String), default=list)
    phi_count = Column(Integer, default=0)

    # Consent
    consent_verified = Column(Boolean, default=False)
    consent_id = Column(UUID(as_uuid=True), nullable=True)

    # Context
    reason = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_phi_audit_tenant_action", "tenant_id", "action"),
        Index("ix_phi_audit_created", "created_at"),
    )


class PatientAIConsent(Base):
    """Patient consent for AI processing of their data."""
    __tablename__ = "patient_ai_consents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Consent details
    purpose = Column(String(100), nullable=False)  # ai_processing, research, analytics
    granted = Column(Boolean, default=True)
    granted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Scope
    allowed_phi_types = Column(ARRAY(String), default=list)
    allowed_uses = Column(ARRAY(String), default=list)

    # Revocation
    revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by = Column(UUID(as_uuid=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "patient_id", "purpose", name="uq_patient_consent_purpose"),
        Index("ix_patient_consent_patient", "patient_id"),
    )


# ==================== A/B Testing ====================

class AIExperiment(Base):
    """A/B testing experiment for AI features."""
    __tablename__ = "ai_experiments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Experiment info
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(ExperimentStatus), default=ExperimentStatus.DRAFT)

    # Configuration
    variants = Column(JSON, nullable=False)  # {"control": {...}, "treatment": {...}}
    traffic_split = Column(JSON, nullable=False)  # {"control": 0.5, "treatment": 0.5}

    # Metrics to track
    primary_metric = Column(String(100), nullable=True)  # latency, cost, quality
    secondary_metrics = Column(ARRAY(String), default=list)

    # Results
    results = Column(JSON, default=dict)
    winning_variant = Column(String(50), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_ai_experiments_tenant_status", "tenant_id", "status"),
    )


# ==================== Prompt Templates ====================

class PromptTemplate(Base):
    """Reusable prompt templates."""
    __tablename__ = "prompt_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Template info
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)  # triage, documentation, chat
    version = Column(Integer, default=1)

    # Content
    system_prompt = Column(Text, nullable=False)
    user_template = Column(Text, nullable=False)  # With {placeholders}
    variables = Column(ARRAY(String), default=list)

    # Configuration
    default_model = Column(String(100), nullable=True)
    default_temperature = Column(Float, default=0.7)
    default_max_tokens = Column(Integer, default=1000)

    # Usage stats
    use_count = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", "version", name="uq_prompt_template_name_version"),
        Index("ix_prompt_templates_category", "category"),
    )


# ==================== Cost Tracking ====================

class AICostSummary(Base):
    """Daily AI cost summary by tenant."""
    __tablename__ = "ai_cost_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    summary_date = Column(DateTime(timezone=True), nullable=False)

    # Token usage
    total_input_tokens = Column(Integer, default=0)
    total_output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)

    # Cost
    total_cost_usd = Column(Float, default=0)
    cost_by_model = Column(JSON, default=dict)  # {"gpt-4": 10.50, "gpt-3.5-turbo": 2.30}
    cost_by_feature = Column(JSON, default=dict)  # {"triage": 5.00, "documentation": 7.80}

    # Request counts
    total_requests = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)

    # Performance
    avg_latency_ms = Column(Float, default=0)
    p95_latency_ms = Column(Float, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "summary_date", name="uq_cost_summary_tenant_date"),
        Index("ix_cost_summary_date", "summary_date"),
    )


class AICostAlert(Base):
    """Cost alert configuration."""
    __tablename__ = "ai_cost_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Alert config
    name = Column(String(200), nullable=False)
    threshold_usd = Column(Float, nullable=False)
    period = Column(String(20), nullable=False)  # hourly, daily, monthly

    # Notification
    notify_emails = Column(ARRAY(String), default=list)
    notify_webhook_url = Column(String(1000), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    trigger_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_cost_alerts_tenant_active", "tenant_id", "is_active"),
    )
