"""
AI Platform Router
FastAPI endpoints for AI capabilities

EPIC-009: Core AI Integration
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from loguru import logger

from shared.database.connection import get_db

from modules.ai.service import AIService
from modules.ai.schemas import (
    # Chat
    ChatCompletionRequest,
    ChatCompletionResponse,
    # Conversations
    ConversationCreate,
    ConversationResponse,
    ConversationMessageSend,
    ConversationMessageResponse,
    ConversationEndRequest,
    # Triage
    TriageRequest,
    TriageResponse,
    # NLP
    EntityExtractionRequest,
    EntityExtractionResponse,
    CodingSuggestionRequest,
    CodingSuggestionResponse,
    # Knowledge Base
    KnowledgeDocumentCreate,
    KnowledgeDocumentResponse,
    SemanticSearchRequest,
    SearchResultResponse,
    RAGContextResponse,
    # PHI Protection
    PHIDetectionRequest,
    DeidentificationRequest,
    DeidentificationResponse,
    ReidentificationRequest,
    ConsentCreate,
    ConsentResponse,
    # Monitoring
    AIMetricsRequest,
    AIMetricsResponse,
    CostSummaryResponse,
    QualityRatingRequest,
    QualityMetricsResponse,
    # Experiments
    ExperimentCreate,
    ExperimentResponse,
    # Templates
    PromptTemplateCreate,
    PromptTemplateResponse,
    PromptTemplateRenderRequest,
    # Alerts
    CostAlertCreate,
    CostAlertResponse,
    # Documentation
    DocumentationRequest,
    DocumentationResponse,
    # Health
    AIHealthResponse,
)


router = APIRouter(prefix="/ai", tags=["AI Platform"])


# ==================== Chat Completion ====================

@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    payload: ChatCompletionRequest,
    db: Session = Depends(get_db),
):
    """
    Create a chat completion using LLM.

    Supports multiple models (GPT-4, GPT-3.5, Claude) with:
    - Temperature control
    - Token limits
    - Function calling
    - Streaming (use /stream endpoint)

    Cost is tracked and logged for monitoring.
    """
    service = AIService(db)

    try:
        # TODO: Get tenant_id and user_id from auth context
        tenant_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")

        result = await service.chat_completion(
            tenant_id=tenant_id,
            request=payload,
            feature="chat",
        )

        return ChatCompletionResponse(**result)

    except Exception as e:
        logger.error(f"Chat completion error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Conversations ====================

@router.post("/conversations", response_model=ConversationResponse, status_code=201)
async def start_conversation(
    payload: ConversationCreate,
    db: Session = Depends(get_db),
):
    """
    Start a new AI conversation.

    Conversation types:
    - general_inquiry: General questions
    - appointment_booking: Schedule appointments
    - symptom_assessment: Symptom triage
    - medication_question: Medication info
    - billing_inquiry: Billing questions
    """
    service = AIService(db)

    try:
        tenant_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")
        conversation = await service.start_conversation(tenant_id, payload)

        return ConversationResponse(
            conversation_id=conversation.id,
            conversation_type=conversation.conversation_type,
            status=conversation.status,
            patient_id=conversation.patient_id,
            channel=conversation.channel,
            language=conversation.language,
            turn_count=conversation.turn_count,
            total_tokens_used=conversation.total_tokens_used,
            total_cost_usd=conversation.total_cost_usd,
            messages=[
                ConversationMessageResponse(
                    message_id=m.id,
                    role=m.role,
                    content=m.content,
                    intent_type=m.intent_type,
                    intent_confidence=m.intent_confidence,
                    created_at=m.created_at,
                )
                for m in conversation.messages
            ],
            context=conversation.context or {},
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            ended_at=conversation.ended_at,
        )

    except Exception as e:
        logger.error(f"Start conversation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/{conversation_id}/messages", response_model=ConversationMessageResponse)
async def send_message(
    conversation_id: UUID,
    payload: ConversationMessageSend,
    db: Session = Depends(get_db),
):
    """
    Send a message in a conversation and get AI response.

    The AI will:
    - Recognize intent
    - Extract relevant entities
    - Generate contextual response
    - Track conversation state
    """
    service = AIService(db)

    try:
        tenant_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")
        conversation, response_msg = await service.send_message(
            tenant_id, conversation_id, payload
        )

        return ConversationMessageResponse(
            message_id=response_msg.id,
            role=response_msg.role,
            content=response_msg.content,
            intent_type=response_msg.intent_type,
            intent_confidence=response_msg.intent_confidence,
            created_at=response_msg.created_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Send message error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/{conversation_id}/end", response_model=ConversationResponse)
async def end_conversation(
    conversation_id: UUID,
    payload: Optional[ConversationEndRequest] = None,
    db: Session = Depends(get_db),
):
    """End a conversation with optional feedback."""
    service = AIService(db)

    try:
        tenant_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")
        conversation = await service.end_conversation(
            tenant_id,
            conversation_id,
            satisfaction_rating=payload.satisfaction_rating if payload else None,
            feedback=payload.feedback if payload else None,
        )

        return ConversationResponse(
            conversation_id=conversation.id,
            conversation_type=conversation.conversation_type,
            status=conversation.status,
            patient_id=conversation.patient_id,
            channel=conversation.channel,
            language=conversation.language,
            turn_count=conversation.turn_count,
            total_tokens_used=conversation.total_tokens_used,
            total_cost_usd=conversation.total_cost_usd,
            messages=[
                ConversationMessageResponse(
                    message_id=m.id,
                    role=m.role,
                    content=m.content,
                    intent_type=m.intent_type,
                    intent_confidence=m.intent_confidence,
                    created_at=m.created_at,
                )
                for m in conversation.messages
            ],
            context=conversation.context or {},
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            ended_at=conversation.ended_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"End conversation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Triage ====================

@router.post("/triage", response_model=TriageResponse)
async def perform_triage(
    payload: TriageRequest,
    db: Session = Depends(get_db),
):
    """
    Perform AI-powered symptom triage.

    Urgency levels:
    - emergency: Call 911 immediately
    - urgent: Same-day care needed
    - soon: Within 24-48 hours
    - routine: Schedule regular appointment
    - self_care: Can manage at home

    Includes red flag detection and care recommendations.
    """
    service = AIService(db)

    try:
        tenant_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")
        result = await service.perform_triage(tenant_id, payload)
        return TriageResponse(**result)

    except Exception as e:
        logger.error(f"Triage error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== NLP ====================

@router.post("/nlp/entities", response_model=EntityExtractionResponse)
async def extract_entities(
    payload: EntityExtractionRequest,
    db: Session = Depends(get_db),
):
    """
    Extract medical entities from text.

    Entity types:
    - condition: Medical conditions (diabetes, hypertension)
    - symptom: Symptoms (headache, fever)
    - medication: Drug names (metformin, lisinopril)
    - procedure: Medical procedures
    - anatomy: Body parts
    - lab_test: Laboratory tests

    Includes SNOMED CT and ICD-10 code mapping.
    """
    service = AIService(db)

    try:
        tenant_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")
        result = await service.extract_entities(tenant_id, payload)
        return EntityExtractionResponse(**result)

    except Exception as e:
        logger.error(f"Entity extraction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/nlp/codes", response_model=List[CodingSuggestionResponse])
async def suggest_codes(
    payload: CodingSuggestionRequest,
    db: Session = Depends(get_db),
):
    """
    Suggest medical codes from clinical text.

    Supported code systems:
    - ICD-10: Diagnosis codes
    - SNOMED: Clinical terminology
    - CPT: Procedure codes
    """
    service = AIService(db)

    try:
        tenant_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")
        results = await service.suggest_codes(tenant_id, payload)
        return [CodingSuggestionResponse(**r) for r in results]

    except Exception as e:
        logger.error(f"Code suggestion error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Knowledge Base ====================

@router.post("/knowledge/documents", response_model=KnowledgeDocumentResponse, status_code=201)
async def index_document(
    payload: KnowledgeDocumentCreate,
    db: Session = Depends(get_db),
):
    """
    Index a medical knowledge document.

    Document types:
    - clinical_guideline: Clinical practice guidelines
    - drug_info: Drug information
    - protocol: Treatment protocols
    - patient_education: Patient education materials
    - faq: Frequently asked questions

    Documents are chunked and embedded for semantic search.
    """
    service = AIService(db)

    try:
        tenant_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")
        doc = await service.index_document(tenant_id, payload)

        return KnowledgeDocumentResponse(
            document_id=doc.id,
            title=doc.title,
            content=doc.content,
            document_type=doc.document_type,
            specialty=doc.specialty,
            condition_codes=doc.condition_codes,
            procedure_codes=doc.procedure_codes,
            snomed_codes=doc.snomed_codes,
            drug_codes=doc.drug_codes,
            keywords=doc.keywords,
            source=doc.source,
            evidence_level=doc.evidence_level,
            is_indexed=doc.is_indexed,
            chunk_count=doc.chunk_count,
            created_at=doc.created_at,
            indexed_at=doc.indexed_at,
        )

    except Exception as e:
        logger.error(f"Index document error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge/search", response_model=List[SearchResultResponse])
async def semantic_search(
    payload: SemanticSearchRequest,
    db: Session = Depends(get_db),
):
    """
    Search knowledge base using semantic similarity.

    Combines:
    - Vector similarity search
    - Keyword matching
    - Evidence level filtering

    Returns ranked results with relevance scores.
    """
    service = AIService(db)

    try:
        tenant_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")
        results = await service.semantic_search(tenant_id, payload)
        return [SearchResultResponse(**r) for r in results]

    except Exception as e:
        logger.error(f"Semantic search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge/rag-context", response_model=RAGContextResponse)
async def get_rag_context(
    query: str = Query(..., description="Query for RAG context"),
    max_chunks: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """
    Build RAG (Retrieval-Augmented Generation) context.

    Retrieves relevant knowledge chunks and formats them
    for use in LLM prompts with source citations.
    """
    service = AIService(db)

    try:
        tenant_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")
        result = await service.build_rag_context(tenant_id, query, max_chunks)
        return RAGContextResponse(**result)

    except Exception as e:
        logger.error(f"RAG context error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge/stats")
async def get_knowledge_stats(
    db: Session = Depends(get_db),
):
    """Get knowledge base statistics."""
    service = AIService(db)

    try:
        tenant_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")
        stats = await service.get_knowledge_stats(tenant_id)
        return stats

    except Exception as e:
        logger.error(f"Knowledge stats error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PHI Protection ====================

@router.post("/phi/deidentify", response_model=DeidentificationResponse)
async def deidentify_text(
    payload: DeidentificationRequest,
    db: Session = Depends(get_db),
):
    """
    De-identify text containing PHI.

    Masking strategies:
    - redact: Replace with [REDACTED]
    - pseudonymize: Replace with fake data
    - hash: Replace with hash value
    - generalize: Generalize (e.g., age to range)
    - suppress: Remove entirely

    Audit logged for HIPAA compliance.
    """
    service = AIService(db)

    try:
        tenant_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")
        result = await service.deidentify_text(tenant_id, payload)
        return DeidentificationResponse(**result)

    except Exception as e:
        logger.error(f"De-identification error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/phi/consent", response_model=ConsentResponse, status_code=201)
async def record_consent(
    payload: ConsentCreate,
    db: Session = Depends(get_db),
):
    """
    Record patient consent for AI processing.

    Consent purposes:
    - ai_processing: General AI processing
    - research: Research use
    - analytics: Analytics use

    Required for PHI re-identification in strict mode.
    """
    service = AIService(db)

    try:
        tenant_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")
        consent = await service.record_consent(tenant_id, payload)

        return ConsentResponse(
            consent_id=consent.id,
            patient_id=consent.patient_id,
            purpose=consent.purpose,
            granted=consent.granted,
            granted_at=consent.granted_at,
            expires_at=consent.expires_at,
            allowed_phi_types=consent.allowed_phi_types,
            allowed_uses=consent.allowed_uses,
            revoked=consent.revoked,
            revoked_at=consent.revoked_at,
        )

    except Exception as e:
        logger.error(f"Record consent error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Documentation ====================

@router.post("/documentation/generate", response_model=DocumentationResponse)
async def generate_documentation(
    payload: DocumentationRequest,
    db: Session = Depends(get_db),
):
    """
    Generate clinical documentation from input.

    Documentation types:
    - soap_note: SOAP format note
    - progress_note: Progress note
    - discharge_summary: Discharge summary
    - referral_letter: Referral letter

    Extracts codes and medications automatically.
    Provider review required before use.
    """
    service = AIService(db)

    try:
        tenant_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")
        result = await service.generate_documentation(tenant_id, payload)
        return DocumentationResponse(**result)

    except Exception as e:
        logger.error(f"Documentation generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Monitoring ====================

@router.post("/monitoring/metrics", response_model=AIMetricsResponse)
async def get_metrics(
    payload: Optional[AIMetricsRequest] = None,
    db: Session = Depends(get_db),
):
    """
    Get AI usage metrics.

    Includes:
    - Request counts and success rates
    - Token usage
    - Latency percentiles (p50, p95, p99)
    - Cost tracking
    - Breakdown by model and feature
    """
    service = AIService(db)

    try:
        tenant_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")
        result = await service.get_metrics(
            tenant_id,
            payload or AIMetricsRequest(),
        )
        return AIMetricsResponse(**result)

    except Exception as e:
        logger.error(f"Get metrics error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/costs", response_model=CostSummaryResponse)
async def get_cost_summary(
    period: str = Query("daily", description="Period: hourly, daily"),
    lookback: int = Query(7, ge=1, le=90, description="Number of periods"),
    db: Session = Depends(get_db),
):
    """Get cost summary for AI usage."""
    service = AIService(db)

    try:
        tenant_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")
        result = await service.get_cost_summary(tenant_id, period, lookback)
        return CostSummaryResponse(**result)

    except Exception as e:
        logger.error(f"Get cost summary error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Experiments ====================

@router.post("/experiments", response_model=ExperimentResponse, status_code=201)
async def create_experiment(
    payload: ExperimentCreate,
    db: Session = Depends(get_db),
):
    """
    Create an A/B experiment.

    Define variants with different configurations
    (e.g., different models, temperatures) and
    track performance metrics.
    """
    service = AIService(db)

    try:
        tenant_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")
        experiment = await service.create_experiment(tenant_id, payload)

        return ExperimentResponse(
            experiment_id=experiment.id,
            name=experiment.name,
            description=experiment.description,
            status=experiment.status.value,
            variants=experiment.variants,
            traffic_split=experiment.traffic_split,
            results=experiment.results or {},
            winning_variant=experiment.winning_variant,
            created_at=experiment.created_at,
            started_at=experiment.started_at,
            ended_at=experiment.ended_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Create experiment error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/experiments/{experiment_id}/start", response_model=ExperimentResponse)
async def start_experiment(
    experiment_id: UUID,
    db: Session = Depends(get_db),
):
    """Start an A/B experiment."""
    service = AIService(db)

    try:
        tenant_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")
        experiment = await service.start_experiment(tenant_id, experiment_id)

        return ExperimentResponse(
            experiment_id=experiment.id,
            name=experiment.name,
            description=experiment.description,
            status=experiment.status.value,
            variants=experiment.variants,
            traffic_split=experiment.traffic_split,
            results=experiment.results or {},
            winning_variant=experiment.winning_variant,
            created_at=experiment.created_at,
            started_at=experiment.started_at,
            ended_at=experiment.ended_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Start experiment error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Prompt Templates ====================

@router.post("/templates", response_model=PromptTemplateResponse, status_code=201)
async def create_prompt_template(
    payload: PromptTemplateCreate,
    db: Session = Depends(get_db),
):
    """
    Create a reusable prompt template.

    Templates can include variables using {placeholder} syntax.
    Version history is maintained automatically.
    """
    service = AIService(db)

    try:
        tenant_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")
        template = await service.create_prompt_template(tenant_id, payload)

        return PromptTemplateResponse(
            template_id=template.id,
            name=template.name,
            description=template.description,
            category=template.category,
            version=template.version,
            system_prompt=template.system_prompt,
            user_template=template.user_template,
            variables=template.variables,
            default_model=template.default_model,
            default_temperature=template.default_temperature,
            default_max_tokens=template.default_max_tokens,
            use_count=template.use_count,
            is_active=template.is_active,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )

    except Exception as e:
        logger.error(f"Create template error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates", response_model=List[PromptTemplateResponse])
async def list_prompt_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db),
):
    """List prompt templates."""
    service = AIService(db)

    try:
        tenant_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")
        templates = await service.list_prompt_templates(tenant_id, category)

        return [
            PromptTemplateResponse(
                template_id=t.id,
                name=t.name,
                description=t.description,
                category=t.category,
                version=t.version,
                system_prompt=t.system_prompt,
                user_template=t.user_template,
                variables=t.variables,
                default_model=t.default_model,
                default_temperature=t.default_temperature,
                default_max_tokens=t.default_max_tokens,
                use_count=t.use_count,
                is_active=t.is_active,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in templates
        ]

    except Exception as e:
        logger.error(f"List templates error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Cost Alerts ====================

@router.post("/alerts", response_model=CostAlertResponse, status_code=201)
async def create_cost_alert(
    payload: CostAlertCreate,
    db: Session = Depends(get_db),
):
    """
    Create a cost alert.

    Alerts when AI costs exceed threshold for period:
    - hourly: Hourly spend threshold
    - daily: Daily spend threshold
    - monthly: Monthly spend threshold
    """
    service = AIService(db)

    try:
        tenant_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")
        alert = await service.create_cost_alert(tenant_id, payload)

        return CostAlertResponse(
            alert_id=alert.id,
            name=alert.name,
            threshold_usd=alert.threshold_usd,
            period=alert.period,
            notify_emails=alert.notify_emails,
            notify_webhook_url=alert.notify_webhook_url,
            is_active=alert.is_active,
            last_triggered_at=alert.last_triggered_at,
            trigger_count=alert.trigger_count,
            created_at=alert.created_at,
        )

    except Exception as e:
        logger.error(f"Create alert error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Health Check ====================

@router.get("/health/check", response_model=AIHealthResponse)
async def ai_health_check(
    db: Session = Depends(get_db),
):
    """
    AI module health check.

    Returns status of all AI capabilities and services.
    """
    service = AIService(db)

    try:
        tenant_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")
        knowledge_stats = await service.get_knowledge_stats(tenant_id)

        return AIHealthResponse(
            status="healthy",
            module="ai",
            features=[
                "chat_completion",
                "conversations",
                "triage",
                "entity_extraction",
                "code_suggestion",
                "semantic_search",
                "rag_context",
                "phi_deidentification",
                "documentation_generation",
                "monitoring",
                "experiments",
                "templates",
                "cost_alerts",
            ],
            llm_provider="openai",
            embedding_model="text-embedding-3-small",
            knowledge_base_documents=knowledge_stats.get("total_documents", 0),
            knowledge_base_chunks=knowledge_stats.get("total_chunks", 0),
            active_experiments=0,  # Would query from DB
        )

    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        return AIHealthResponse(
            status="unhealthy",
            module="ai",
            features=[],
            llm_provider="unknown",
            embedding_model="unknown",
            knowledge_base_documents=0,
            knowledge_base_chunks=0,
            active_experiments=0,
        )
