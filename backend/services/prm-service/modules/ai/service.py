"""
AI Platform Service
Business logic for AI operations with database persistence

EPIC-009: Core AI Integration
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, desc
import logging

from shared.ai import (
    LLMService,
    MedicalNLPService,
    ConversationalAI,
    MedicalAIService,
    AIMonitoringService,
    PHIProtectionService,
    VectorSearchService,
    ChatMessage as SharedChatMessage,
    MessageRole,
    ai_monitoring_service,
    phi_protection_service,
    vector_search_service,
)
from shared.ai.monitoring import AIRequestType as MonitoringRequestType, AIProvider as MonitoringProvider
from shared.ai.vector_search import DocumentType as VectorDocumentType, EvidenceLevel as VectorEvidenceLevel, SearchQuery

from modules.ai.models import (
    AIRequestLog,
    AIConversation,
    AIConversationMessage,
    MedicalKnowledgeDocument,
    MedicalKnowledgeChunk,
    PHIAuditLog,
    PatientAIConsent,
    AIExperiment,
    PromptTemplate,
    AICostSummary,
    AICostAlert,
    AIProviderType,
    AIRequestType,
    ConversationStatus,
    ConversationType,
    DocumentType,
    EvidenceLevel,
    PHIActionType,
    ExperimentStatus,
)

from modules.ai.schemas import (
    ChatCompletionRequest,
    ConversationCreate,
    ConversationMessageSend,
    TriageRequest,
    EntityExtractionRequest,
    CodingSuggestionRequest,
    KnowledgeDocumentCreate,
    SemanticSearchRequest,
    DeidentificationRequest,
    ConsentCreate,
    AIMetricsRequest,
    ExperimentCreate,
    PromptTemplateCreate,
    CostAlertCreate,
    QualityRatingRequest,
    DocumentationRequest,
)

logger = logging.getLogger(__name__)


class AIService:
    """
    Main AI service coordinating all AI capabilities.

    Integrates:
    - LLM for chat completions
    - Medical NLP for entity extraction
    - Conversational AI for multi-turn conversations
    - Medical AI for triage and documentation
    - Monitoring for cost and quality tracking
    - PHI protection for HIPAA compliance
    - Vector search for knowledge retrieval
    """

    def __init__(self, db: Session):
        self.db = db

        # Initialize shared services
        self.llm_service = LLMService()
        self.nlp_service = MedicalNLPService()
        self.conversational_ai = ConversationalAI(self.llm_service)
        self.medical_ai = MedicalAIService(self.llm_service, self.nlp_service)
        self.monitoring = ai_monitoring_service
        self.phi_protection = phi_protection_service
        self.vector_search = vector_search_service

    # ==================== Chat Completion ====================

    async def chat_completion(
        self,
        tenant_id: UUID,
        request: ChatCompletionRequest,
        user_id: Optional[UUID] = None,
        feature: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a chat completion with monitoring and logging.

        Args:
            tenant_id: Tenant identifier
            request: Chat completion request
            user_id: User identifier
            feature: Feature name for tracking

        Returns:
            Chat completion response
        """
        start_time = datetime.now(timezone.utc)

        # Convert messages
        messages = [
            SharedChatMessage(
                role=MessageRole(msg.role),
                content=msg.content,
                name=msg.name,
                function_call=msg.function_call,
            )
            for msg in request.messages
        ]

        # Estimate input tokens
        input_prompt = " ".join(msg.content for msg in request.messages)
        input_tokens = len(input_prompt) // 4

        try:
            # Execute completion
            completion = await self.llm_service.complete(
                messages=messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                functions=request.functions,
                stream=request.stream,
            )

            # Calculate metrics
            latency_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

            # Log request
            log_entry = await self.monitoring.log_request(
                tenant_id=str(tenant_id),
                request_type=MonitoringRequestType.CHAT_COMPLETION,
                provider=MonitoringProvider.OPENAI,
                model=request.model or "gpt-4",
                prompt=input_prompt[:500],  # Truncate for logging
                input_tokens=completion.usage.prompt_tokens,
                output_tokens=completion.usage.completion_tokens,
                latency_ms=latency_ms,
                success=True,
                finish_reason=completion.finish_reason,
                user_id=str(user_id) if user_id else None,
                feature=feature,
            )

            # Persist to database
            db_log = AIRequestLog(
                id=uuid4(),
                tenant_id=tenant_id,
                request_type=AIRequestType.CHAT_COMPLETION,
                provider=AIProviderType.OPENAI,
                model=request.model or "gpt-4",
                prompt_hash=log_entry.prompt_hash,
                input_tokens=completion.usage.prompt_tokens,
                output_tokens=completion.usage.completion_tokens,
                total_tokens=completion.usage.total_tokens,
                latency_ms=latency_ms,
                finish_reason=completion.finish_reason,
                estimated_cost_usd=log_entry.estimated_cost_usd,
                success=True,
                user_id=user_id,
                feature=feature,
            )
            self.db.add(db_log)
            self.db.commit()

            return {
                "completion_id": str(completion.completion_id),
                "model": completion.model,
                "message": {
                    "role": completion.message.role.value,
                    "content": completion.message.content,
                },
                "finish_reason": completion.finish_reason,
                "input_tokens": completion.usage.prompt_tokens,
                "output_tokens": completion.usage.completion_tokens,
                "total_tokens": completion.usage.total_tokens,
                "latency_ms": latency_ms,
                "estimated_cost_usd": log_entry.estimated_cost_usd,
                "created_at": completion.created_at.isoformat(),
            }

        except Exception as e:
            latency_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

            # Log error
            await self.monitoring.log_request(
                tenant_id=str(tenant_id),
                request_type=MonitoringRequestType.CHAT_COMPLETION,
                provider=MonitoringProvider.OPENAI,
                model=request.model or "gpt-4",
                prompt=input_prompt[:500],
                input_tokens=input_tokens,
                output_tokens=0,
                latency_ms=latency_ms,
                success=False,
                error_message=str(e),
                error_type=type(e).__name__,
                user_id=str(user_id) if user_id else None,
                feature=feature,
            )

            logger.error(f"Chat completion error: {e}")
            raise

    # ==================== Conversations ====================

    async def start_conversation(
        self,
        tenant_id: UUID,
        request: ConversationCreate,
    ) -> AIConversation:
        """
        Start a new AI conversation.

        Args:
            tenant_id: Tenant identifier
            request: Conversation creation request

        Returns:
            Created AIConversation
        """
        # Start conversation in shared service
        shared_conversation = await self.conversational_ai.start_conversation(
            tenant_id=str(tenant_id),
            conversation_type=request.conversation_type.value,
            patient_id=str(request.patient_id) if request.patient_id else None,
            channel=request.channel,
            language=request.language,
            initial_context=request.initial_context,
        )

        # Persist to database
        db_conversation = AIConversation(
            id=UUID(shared_conversation.conversation_id),
            tenant_id=tenant_id,
            conversation_type=ConversationType(request.conversation_type.value),
            status=ConversationStatus.ACTIVE,
            patient_id=request.patient_id,
            channel=request.channel,
            language=request.language,
            context=request.initial_context or {},
            turn_count=1,  # Initial greeting
        )
        self.db.add(db_conversation)

        # Add initial greeting message
        if shared_conversation.turns:
            initial_turn = shared_conversation.turns[0]
            db_message = AIConversationMessage(
                id=UUID(initial_turn.turn_id),
                conversation_id=db_conversation.id,
                role=initial_turn.role.value,
                content=initial_turn.content,
            )
            self.db.add(db_message)

        self.db.commit()
        self.db.refresh(db_conversation)

        logger.info(f"Started conversation {db_conversation.id}")
        return db_conversation

    async def send_message(
        self,
        tenant_id: UUID,
        conversation_id: UUID,
        request: ConversationMessageSend,
    ) -> Tuple[AIConversation, AIConversationMessage]:
        """
        Send a message in a conversation and get AI response.

        Args:
            tenant_id: Tenant identifier
            conversation_id: Conversation ID
            request: Message to send

        Returns:
            Tuple of (updated conversation, response message)
        """
        # Get conversation
        conversation = self.db.query(AIConversation).filter(
            AIConversation.id == conversation_id,
            AIConversation.tenant_id == tenant_id,
        ).first()

        if not conversation:
            raise ValueError(f"Conversation not found: {conversation_id}")

        if conversation.status == ConversationStatus.COMPLETED:
            raise ValueError("Conversation has ended")

        start_time = datetime.now(timezone.utc)

        # Process message
        response_text = await self.conversational_ai.process_message(
            conversation_id=str(conversation_id),
            user_message=request.content,
        )

        latency_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

        # Add user message
        user_message = AIConversationMessage(
            id=uuid4(),
            conversation_id=conversation_id,
            role="user",
            content=request.content,
        )
        self.db.add(user_message)

        # Add assistant message
        assistant_message = AIConversationMessage(
            id=uuid4(),
            conversation_id=conversation_id,
            role="assistant",
            content=response_text,
            latency_ms=latency_ms,
        )
        self.db.add(assistant_message)

        # Update conversation
        conversation.turn_count += 2
        conversation.updated_at = datetime.now(timezone.utc)

        # Check if escalated
        shared_conv = await self.conversational_ai.get_conversation(str(conversation_id))
        if shared_conv and shared_conv.state.value == "escalated":
            conversation.status = ConversationStatus.ESCALATED
            conversation.escalation_reason = shared_conv.escalation_reason
            conversation.escalated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(conversation)

        return conversation, assistant_message

    async def end_conversation(
        self,
        tenant_id: UUID,
        conversation_id: UUID,
        satisfaction_rating: Optional[int] = None,
        feedback: Optional[str] = None,
    ) -> AIConversation:
        """End a conversation."""
        conversation = self.db.query(AIConversation).filter(
            AIConversation.id == conversation_id,
            AIConversation.tenant_id == tenant_id,
        ).first()

        if not conversation:
            raise ValueError(f"Conversation not found: {conversation_id}")

        conversation.status = ConversationStatus.COMPLETED
        conversation.ended_at = datetime.now(timezone.utc)
        conversation.satisfaction_rating = satisfaction_rating
        conversation.feedback = feedback

        self.db.commit()
        self.db.refresh(conversation)

        logger.info(f"Ended conversation {conversation_id}")
        return conversation

    # ==================== Triage ====================

    async def perform_triage(
        self,
        tenant_id: UUID,
        request: TriageRequest,
        patient_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Perform symptom triage assessment.

        Args:
            tenant_id: Tenant identifier
            request: Triage request
            patient_id: Patient identifier

        Returns:
            Triage result
        """
        from shared.ai.medical_ai import Symptom

        # Convert symptoms
        symptoms = [
            Symptom(
                name=s.name,
                description=s.description,
                severity=s.severity,
                duration=s.duration,
                onset=s.onset,
                location=s.location,
                aggravating_factors=s.aggravating_factors or [],
                relieving_factors=s.relieving_factors or [],
                associated_symptoms=s.associated_symptoms or [],
            )
            for s in request.symptoms
        ]

        # Perform triage
        result = await self.medical_ai.triage_symptoms(
            symptoms=symptoms,
            patient_age=request.patient_age,
            patient_sex=request.patient_sex,
            medical_history=request.medical_history,
        )

        # Log request
        await self.monitoring.log_request(
            tenant_id=str(tenant_id),
            request_type=MonitoringRequestType.TRIAGE,
            provider=MonitoringProvider.OPENAI,
            model="gpt-4",
            prompt=str(request.symptoms),
            input_tokens=100,
            output_tokens=200,
            latency_ms=0,
            success=True,
            confidence_score=result.confidence_score,
            feature="triage",
        )

        return {
            "triage_id": result.triage_id,
            "urgency_level": result.urgency_level.value,
            "urgency_score": result.urgency_score,
            "primary_concern": result.primary_concern,
            "contributing_factors": result.contributing_factors,
            "red_flags_identified": result.red_flags_identified,
            "recommended_action": result.recommended_action,
            "timeframe": result.timeframe,
            "care_setting": result.care_setting,
            "self_care_advice": result.self_care_advice,
            "warning_signs": result.warning_signs,
            "confidence_score": result.confidence_score,
            "disclaimer": result.disclaimer,
            "created_at": result.timestamp.isoformat(),
        }

    # ==================== NLP ====================

    async def extract_entities(
        self,
        tenant_id: UUID,
        request: EntityExtractionRequest,
    ) -> Dict[str, Any]:
        """Extract medical entities from text."""
        extraction = await self.nlp_service.extract_entities(
            text=request.text,
            entity_types=request.entity_types,
        )

        return {
            "extraction_id": extraction.extraction_id,
            "entities": [
                {
                    "entity_id": e.entity_id,
                    "entity_type": e.entity_type.value,
                    "text": e.text,
                    "normalized_text": e.normalized_text,
                    "start_offset": e.start_offset,
                    "end_offset": e.end_offset,
                    "codes": e.codes,
                    "negation_status": e.negation_status.value,
                    "confidence": e.confidence,
                }
                for e in extraction.entities
            ],
            "processing_time_ms": extraction.processing_time_ms,
            "created_at": extraction.created_at.isoformat(),
        }

    async def suggest_codes(
        self,
        tenant_id: UUID,
        request: CodingSuggestionRequest,
    ) -> List[Dict[str, Any]]:
        """Suggest medical codes from text."""
        suggestions = await self.nlp_service.suggest_codes(
            text=request.text,
            code_system=request.code_system,
            max_suggestions=request.max_suggestions,
        )

        return [
            {
                "code": s.code,
                "system": s.system,
                "display": s.display,
                "confidence": s.confidence,
                "evidence_text": s.evidence_text,
            }
            for s in suggestions
        ]

    # ==================== Knowledge Base ====================

    async def index_document(
        self,
        tenant_id: UUID,
        request: KnowledgeDocumentCreate,
    ) -> MedicalKnowledgeDocument:
        """Index a medical knowledge document."""
        # Index in vector service
        vector_doc = await self.vector_search.index_document(
            tenant_id=str(tenant_id),
            title=request.title,
            content=request.content,
            document_type=VectorDocumentType(request.document_type.value),
            specialty=request.specialty,
            condition_codes=request.condition_codes,
            procedure_codes=request.procedure_codes,
            snomed_codes=request.snomed_codes,
            drug_codes=request.drug_codes,
            source=request.source,
            source_url=request.source_url,
            author=request.author,
            publication_date=request.publication_date,
            evidence_level=VectorEvidenceLevel(request.evidence_level.value),
        )

        # Persist to database
        db_doc = MedicalKnowledgeDocument(
            id=UUID(vector_doc.document_id),
            tenant_id=tenant_id,
            title=request.title,
            content=request.content,
            document_type=DocumentType(request.document_type.value),
            specialty=request.specialty,
            condition_codes=request.condition_codes or [],
            procedure_codes=request.procedure_codes or [],
            snomed_codes=request.snomed_codes or [],
            drug_codes=request.drug_codes or [],
            keywords=vector_doc.keywords,
            source=request.source,
            source_url=request.source_url,
            author=request.author,
            publication_date=request.publication_date,
            evidence_level=EvidenceLevel(request.evidence_level.value),
            is_indexed=True,
            indexed_at=datetime.now(timezone.utc),
            chunk_count=len(vector_doc.chunks),
        )
        self.db.add(db_doc)

        # Add chunks
        for chunk in vector_doc.chunks:
            db_chunk = MedicalKnowledgeChunk(
                id=UUID(chunk.chunk_id),
                document_id=db_doc.id,
                text=chunk.text,
                chunk_index=chunk.chunk_index,
                start_offset=chunk.start_offset,
                end_offset=chunk.end_offset,
                embedding=chunk.embedding,
                metadata=chunk.metadata,
            )
            self.db.add(db_chunk)

        self.db.commit()
        self.db.refresh(db_doc)

        logger.info(f"Indexed document {db_doc.id}: {request.title}")
        return db_doc

    async def semantic_search(
        self,
        tenant_id: UUID,
        request: SemanticSearchRequest,
    ) -> List[Dict[str, Any]]:
        """Perform semantic search on knowledge base."""
        search_query = SearchQuery(
            query=request.query,
            top_k=request.top_k,
            document_types=[VectorDocumentType(dt.value) for dt in request.document_types] if request.document_types else None,
            specialties=request.specialties,
            evidence_levels=[VectorEvidenceLevel(el.value) for el in request.evidence_levels] if request.evidence_levels else None,
            condition_codes=request.condition_codes,
            min_similarity=request.min_similarity,
        )

        results = await self.vector_search.search(str(tenant_id), search_query)

        return [
            {
                "chunk_id": r.chunk_id,
                "document_id": r.document_id,
                "text": r.text,
                "similarity_score": r.similarity_score,
                "keyword_score": r.keyword_score,
                "combined_score": r.combined_score,
                "document_title": r.document_title,
                "document_type": r.document_type.value if r.document_type else None,
                "specialty": r.specialty,
                "evidence_level": r.evidence_level.value if r.evidence_level else None,
                "source": r.source,
            }
            for r in results
        ]

    async def build_rag_context(
        self,
        tenant_id: UUID,
        query: str,
        max_chunks: int = 5,
    ) -> Dict[str, Any]:
        """Build RAG context for a query."""
        context = await self.vector_search.build_rag_context(
            tenant_id=str(tenant_id),
            query=query,
            max_chunks=max_chunks,
        )

        return {
            "query": context.query,
            "context_text": context.context_text,
            "sources": context.sources,
            "total_chunks": context.total_chunks,
            "total_tokens_estimate": context.total_tokens_estimate,
        }

    # ==================== PHI Protection ====================

    async def deidentify_text(
        self,
        tenant_id: UUID,
        request: DeidentificationRequest,
        user_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """De-identify text containing PHI."""
        from shared.ai.phi_protection import MaskingStrategy as PHIMaskingStrategy

        result = await self.phi_protection.deidentify(
            text=request.text,
            tenant_id=str(tenant_id),
            strategy=PHIMaskingStrategy(request.strategy.value),
            preserve_format=request.preserve_format,
            user_id=str(user_id) if user_id else None,
            reason=request.reason,
        )

        # Persist audit log
        db_audit = PHIAuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            action=PHIActionType.DEIDENTIFY,
            resource_type="text",
            resource_id=result.result_id,
            user_id=user_id,
            phi_types_detected=[e.phi_type.value for e in result.phi_entities],
            phi_count=result.phi_count,
            reason=request.reason,
        )
        self.db.add(db_audit)
        self.db.commit()

        return {
            "result_id": result.result_id,
            "deidentified_text": result.deidentified_text,
            "phi_entities": [
                {
                    "entity_id": e.entity_id,
                    "phi_type": e.phi_type.value,
                    "original_text": e.original_text,
                    "start_offset": e.start_offset,
                    "end_offset": e.end_offset,
                    "confidence": e.confidence,
                    "masked_text": e.masked_text,
                }
                for e in result.phi_entities
            ],
            "phi_count": result.phi_count,
            "processing_time_ms": result.processing_time_ms,
            "created_at": result.timestamp.isoformat(),
        }

    async def record_consent(
        self,
        tenant_id: UUID,
        request: ConsentCreate,
    ) -> PatientAIConsent:
        """Record patient consent for AI processing."""
        db_consent = PatientAIConsent(
            id=uuid4(),
            tenant_id=tenant_id,
            patient_id=request.patient_id,
            purpose=request.purpose,
            granted=request.granted,
            allowed_phi_types=[t.value for t in request.allowed_phi_types] if request.allowed_phi_types else [],
            allowed_uses=request.allowed_uses or [],
            expires_at=request.expires_at,
        )
        self.db.add(db_consent)

        # Audit log
        db_audit = PHIAuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            action=PHIActionType.CONSENT_RECORD,
            resource_type="consent",
            resource_id=str(db_consent.id),
            reason=f"Consent {'granted' if request.granted else 'denied'} for {request.purpose}",
        )
        self.db.add(db_audit)

        self.db.commit()
        self.db.refresh(db_consent)

        # Also record in shared service
        await self.phi_protection.record_consent(
            patient_id=str(request.patient_id),
            tenant_id=str(tenant_id),
            purpose=request.purpose,
            granted=request.granted,
        )

        return db_consent

    # ==================== Monitoring ====================

    async def get_metrics(
        self,
        tenant_id: UUID,
        request: AIMetricsRequest,
    ) -> Dict[str, Any]:
        """Get AI metrics."""
        metrics = await self.monitoring.get_metrics(
            tenant_id=str(tenant_id),
            start_time=request.start_time,
            end_time=request.end_time,
            request_type=MonitoringRequestType(request.request_type.value) if request.request_type else None,
            provider=MonitoringProvider(request.provider.value) if request.provider else None,
            model=request.model,
        )

        return {
            "period_start": metrics.period_start.isoformat(),
            "period_end": metrics.period_end.isoformat(),
            "total_requests": metrics.total_requests,
            "successful_requests": metrics.successful_requests,
            "failed_requests": metrics.failed_requests,
            "total_input_tokens": metrics.total_input_tokens,
            "total_output_tokens": metrics.total_output_tokens,
            "total_tokens": metrics.total_tokens,
            "avg_latency_ms": metrics.avg_latency_ms,
            "p50_latency_ms": metrics.p50_latency_ms,
            "p95_latency_ms": metrics.p95_latency_ms,
            "p99_latency_ms": metrics.p99_latency_ms,
            "total_cost_usd": metrics.total_cost_usd,
            "avg_cost_per_request_usd": metrics.avg_cost_per_request_usd,
            "error_rate": metrics.error_rate,
            "by_request_type": metrics.by_request_type,
            "by_provider": metrics.by_provider,
            "by_model": metrics.by_model,
            "errors_by_type": metrics.errors_by_type,
        }

    async def get_cost_summary(
        self,
        tenant_id: UUID,
        period: str = "daily",
        lookback: int = 7,
    ) -> Dict[str, Any]:
        """Get cost summary."""
        costs = await self.monitoring.get_cost_summary(
            tenant_id=str(tenant_id),
            period=period,
            lookback=lookback,
        )

        return {
            "period": period,
            "costs": costs,
            "total_cost_usd": sum(costs.values()),
        }

    # ==================== Experiments ====================

    async def create_experiment(
        self,
        tenant_id: UUID,
        request: ExperimentCreate,
    ) -> AIExperiment:
        """Create an A/B experiment."""
        db_experiment = AIExperiment(
            id=uuid4(),
            tenant_id=tenant_id,
            name=request.name,
            description=request.description,
            variants=request.variants,
            traffic_split=request.traffic_split,
            primary_metric=request.primary_metric,
            status=ExperimentStatus.DRAFT,
        )
        self.db.add(db_experiment)
        self.db.commit()
        self.db.refresh(db_experiment)

        # Also create in shared service
        self.monitoring.create_experiment(
            name=request.name,
            description=request.description or "",
            variants=request.variants,
            traffic_split=request.traffic_split,
        )

        return db_experiment

    async def start_experiment(
        self,
        tenant_id: UUID,
        experiment_id: UUID,
    ) -> AIExperiment:
        """Start an experiment."""
        experiment = self.db.query(AIExperiment).filter(
            AIExperiment.id == experiment_id,
            AIExperiment.tenant_id == tenant_id,
        ).first()

        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_id}")

        experiment.status = ExperimentStatus.RUNNING
        experiment.started_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(experiment)

        return experiment

    # ==================== Documentation ====================

    async def generate_documentation(
        self,
        tenant_id: UUID,
        request: DocumentationRequest,
    ) -> Dict[str, Any]:
        """Generate clinical documentation."""
        from shared.ai.medical_ai import DocumentationType as MedicalDocType

        doc_type_map = {
            "soap_note": MedicalDocType.SOAP_NOTE,
            "progress_note": MedicalDocType.PROGRESS_NOTE,
            "discharge_summary": MedicalDocType.DISCHARGE_SUMMARY,
            "referral_letter": MedicalDocType.REFERRAL_LETTER,
            "procedure_note": MedicalDocType.PROCEDURE_NOTE,
            "consultation": MedicalDocType.CONSULTATION,
        }

        doc_type = doc_type_map.get(request.documentation_type, MedicalDocType.PROGRESS_NOTE)

        suggestion = await self.medical_ai.generate_documentation(
            documentation_type=doc_type,
            clinical_input=request.clinical_input,
            patient_context=request.patient_context,
        )

        # Log request
        await self.monitoring.log_request(
            tenant_id=str(tenant_id),
            request_type=MonitoringRequestType.DOCUMENTATION,
            provider=MonitoringProvider.OPENAI,
            model="gpt-4",
            prompt=request.clinical_input[:500],
            input_tokens=len(request.clinical_input) // 4,
            output_tokens=len(suggestion.suggested_text) // 4,
            latency_ms=0,
            success=True,
            confidence_score=suggestion.confidence_score,
            feature="documentation",
        )

        return {
            "suggestion_id": suggestion.suggestion_id,
            "documentation_type": request.documentation_type,
            "suggested_text": suggestion.suggested_text,
            "sections": suggestion.sections,
            "extracted_codes": suggestion.extracted_codes,
            "extracted_medications": suggestion.extracted_medications,
            "extracted_diagnoses": suggestion.extracted_diagnoses,
            "confidence_score": suggestion.confidence_score,
            "requires_review": suggestion.requires_review,
            "disclaimer": suggestion.disclaimer,
            "created_at": suggestion.timestamp.isoformat(),
        }

    # ==================== Prompt Templates ====================

    async def create_prompt_template(
        self,
        tenant_id: UUID,
        request: PromptTemplateCreate,
    ) -> PromptTemplate:
        """Create a prompt template."""
        # Get latest version
        latest = self.db.query(func.max(PromptTemplate.version)).filter(
            PromptTemplate.tenant_id == tenant_id,
            PromptTemplate.name == request.name,
        ).scalar() or 0

        db_template = PromptTemplate(
            id=uuid4(),
            tenant_id=tenant_id,
            name=request.name,
            description=request.description,
            category=request.category,
            version=latest + 1,
            system_prompt=request.system_prompt,
            user_template=request.user_template,
            variables=request.variables,
            default_model=request.default_model,
            default_temperature=request.default_temperature,
            default_max_tokens=request.default_max_tokens,
        )
        self.db.add(db_template)
        self.db.commit()
        self.db.refresh(db_template)

        return db_template

    async def list_prompt_templates(
        self,
        tenant_id: UUID,
        category: Optional[str] = None,
    ) -> List[PromptTemplate]:
        """List prompt templates."""
        query = self.db.query(PromptTemplate).filter(
            PromptTemplate.tenant_id == tenant_id,
            PromptTemplate.is_active == True,
        )

        if category:
            query = query.filter(PromptTemplate.category == category)

        return query.order_by(desc(PromptTemplate.created_at)).all()

    # ==================== Cost Alerts ====================

    async def create_cost_alert(
        self,
        tenant_id: UUID,
        request: CostAlertCreate,
    ) -> AICostAlert:
        """Create a cost alert."""
        db_alert = AICostAlert(
            id=uuid4(),
            tenant_id=tenant_id,
            name=request.name,
            threshold_usd=request.threshold_usd,
            period=request.period,
            notify_emails=request.notify_emails or [],
            notify_webhook_url=request.notify_webhook_url,
        )
        self.db.add(db_alert)
        self.db.commit()
        self.db.refresh(db_alert)

        # Also create in monitoring service
        self.monitoring.create_cost_alert(
            name=request.name,
            threshold_usd=request.threshold_usd,
            period=request.period,
            tenant_id=str(tenant_id),
        )

        return db_alert

    # ==================== Knowledge Base Stats ====================

    async def get_knowledge_stats(
        self,
        tenant_id: UUID,
    ) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        stats = await self.vector_search.get_statistics(str(tenant_id))
        return stats
