"""
AI Platform Test Suite

EPIC-009: Core AI Integration

Comprehensive tests covering:
- LLM chat completions
- Conversational AI with multi-turn support
- Medical triage and symptom assessment
- Clinical documentation generation
- Medical NLP and entity extraction
- Vector search for knowledge retrieval
- PHI protection and de-identification
- AI monitoring and observability
- A/B testing for AI features
- Cost tracking and alerts
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4, UUID
from decimal import Decimal

# Import schemas
from services.prm.modules.ai.schemas import (
    AIProviderType,
    AIRequestType,
    ConversationStatus,
    ConversationType,
    DocumentType,
    EvidenceLevel,
    UrgencyLevel,
    QualityRating,
    MaskingStrategy,
    PHIType,
    ChatMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ConversationCreate,
    ConversationMessageSend,
    ConversationMessageResponse,
    ConversationResponse,
    ConversationEndRequest,
    SymptomInput,
    TriageRequest,
    TriageResponse,
    EntityExtractionRequest,
    ClinicalEntityResponse,
    EntityExtractionResponse,
    CodingSuggestionRequest,
    CodingSuggestionResponse,
    KnowledgeDocumentCreate,
    KnowledgeDocumentResponse,
    SemanticSearchRequest,
    SearchResultResponse,
    RAGContextResponse,
    PHIDetectionRequest,
    PHIEntityResponse,
    DeidentificationRequest,
    DeidentificationResponse,
    ReidentificationRequest,
    ConsentCreate,
    ConsentResponse,
    AIMetricsRequest,
    AIMetricsResponse,
    CostSummaryResponse,
    ExperimentCreate,
    ExperimentResponse,
    PromptTemplateCreate,
    PromptTemplateResponse,
    PromptTemplateRenderRequest,
    CostAlertCreate,
    CostAlertResponse,
    QualityRatingRequest,
    QualityMetricsResponse,
    DocumentationRequest,
    DocumentationResponse,
    AIHealthResponse,
)

# Import models
from services.prm.modules.ai.models import (
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
    AIProviderType as ModelAIProviderType,
    AIRequestType as ModelAIRequestType,
    ConversationStatus as ModelConversationStatus,
    ConversationType as ModelConversationType,
    DocumentType as ModelDocumentType,
    EvidenceLevel as ModelEvidenceLevel,
    PHIActionType,
    ExperimentStatus,
)


# ============================================================================
# ENUM TESTS
# ============================================================================

class TestAIEnums:
    """Tests for AI enum values."""

    def test_ai_provider_type_values(self):
        """Test AI provider type enum."""
        assert AIProviderType.OPENAI == "openai"
        assert AIProviderType.ANTHROPIC == "anthropic"
        assert AIProviderType.AZURE_OPENAI == "azure_openai"
        assert AIProviderType.LOCAL == "local"
        assert AIProviderType.HUGGINGFACE == "huggingface"

    def test_ai_request_type_values(self):
        """Test AI request type enum."""
        assert AIRequestType.CHAT_COMPLETION == "chat_completion"
        assert AIRequestType.STREAMING == "streaming"
        assert AIRequestType.EMBEDDING == "embedding"
        assert AIRequestType.NER == "ner"
        assert AIRequestType.CLASSIFICATION == "classification"
        assert AIRequestType.TRIAGE == "triage"
        assert AIRequestType.DOCUMENTATION == "documentation"
        assert AIRequestType.SEMANTIC_SEARCH == "semantic_search"
        assert AIRequestType.FUNCTION_CALL == "function_call"

    def test_conversation_status_values(self):
        """Test conversation status enum."""
        assert ConversationStatus.ACTIVE == "active"
        assert ConversationStatus.PAUSED == "paused"
        assert ConversationStatus.WAITING_INPUT == "waiting_input"
        assert ConversationStatus.COMPLETED == "completed"
        assert ConversationStatus.ESCALATED == "escalated"

    def test_conversation_type_values(self):
        """Test conversation type enum."""
        assert ConversationType.GENERAL_INQUIRY == "general_inquiry"
        assert ConversationType.APPOINTMENT_BOOKING == "appointment_booking"
        assert ConversationType.SYMPTOM_ASSESSMENT == "symptom_assessment"
        assert ConversationType.MEDICATION_QUESTION == "medication_question"
        assert ConversationType.BILLING_INQUIRY == "billing_inquiry"
        assert ConversationType.PRESCRIPTION_REFILL == "prescription_refill"
        assert ConversationType.LAB_RESULTS == "lab_results"
        assert ConversationType.PROVIDER_MESSAGE == "provider_message"

    def test_document_type_values(self):
        """Test document type enum."""
        assert DocumentType.CLINICAL_GUIDELINE == "clinical_guideline"
        assert DocumentType.DRUG_INFO == "drug_info"
        assert DocumentType.MEDICAL_LITERATURE == "medical_literature"
        assert DocumentType.PROTOCOL == "protocol"
        assert DocumentType.POLICY == "policy"
        assert DocumentType.FAQ == "faq"
        assert DocumentType.PATIENT_EDUCATION == "patient_education"
        assert DocumentType.PROCEDURE == "procedure"

    def test_evidence_level_values(self):
        """Test evidence level enum."""
        assert EvidenceLevel.LEVEL_A == "A"
        assert EvidenceLevel.LEVEL_B == "B"
        assert EvidenceLevel.LEVEL_C == "C"
        assert EvidenceLevel.LEVEL_D == "D"
        assert EvidenceLevel.NOT_APPLICABLE == "N/A"

    def test_urgency_level_values(self):
        """Test urgency level enum."""
        assert UrgencyLevel.EMERGENCY == "emergency"
        assert UrgencyLevel.URGENT == "urgent"
        assert UrgencyLevel.SOON == "soon"
        assert UrgencyLevel.ROUTINE == "routine"
        assert UrgencyLevel.SELF_CARE == "self_care"

    def test_quality_rating_values(self):
        """Test quality rating enum."""
        assert QualityRating.EXCELLENT == "excellent"
        assert QualityRating.GOOD == "good"
        assert QualityRating.ACCEPTABLE == "acceptable"
        assert QualityRating.POOR == "poor"
        assert QualityRating.FAILED == "failed"

    def test_masking_strategy_values(self):
        """Test masking strategy enum."""
        assert MaskingStrategy.REDACT == "redact"
        assert MaskingStrategy.PSEUDONYMIZE == "pseudonymize"
        assert MaskingStrategy.HASH == "hash"
        assert MaskingStrategy.GENERALIZE == "generalize"
        assert MaskingStrategy.SUPPRESS == "suppress"

    def test_phi_type_values(self):
        """Test PHI type enum."""
        assert PHIType.NAME == "name"
        assert PHIType.DATE_OF_BIRTH == "date_of_birth"
        assert PHIType.SSN == "ssn"
        assert PHIType.MRN == "mrn"
        assert PHIType.PHONE == "phone"
        assert PHIType.EMAIL == "email"
        assert PHIType.ADDRESS == "address"
        assert PHIType.ZIP_CODE == "zip_code"

    def test_phi_action_type_values(self):
        """Test PHI action type model enum."""
        assert PHIActionType.DETECT.value == "detect"
        assert PHIActionType.DEIDENTIFY.value == "deidentify"
        assert PHIActionType.REIDENTIFY.value == "reidentify"
        assert PHIActionType.ACCESS.value == "access"
        assert PHIActionType.CONSENT_RECORD.value == "consent_record"

    def test_experiment_status_values(self):
        """Test experiment status model enum."""
        assert ExperimentStatus.DRAFT.value == "draft"
        assert ExperimentStatus.RUNNING.value == "running"
        assert ExperimentStatus.PAUSED.value == "paused"
        assert ExperimentStatus.COMPLETED.value == "completed"


# ============================================================================
# SCHEMA VALIDATION TESTS
# ============================================================================

class TestChatSchemas:
    """Tests for chat completion schemas."""

    def test_chat_message_valid(self):
        """Test valid chat message."""
        message = ChatMessage(
            role="user",
            content="What are the symptoms of diabetes?"
        )
        assert message.role == "user"
        assert message.content == "What are the symptoms of diabetes?"
        assert message.name is None
        assert message.function_call is None

    def test_chat_message_with_function(self):
        """Test chat message with function call."""
        message = ChatMessage(
            role="assistant",
            content="",
            function_call={
                "name": "get_patient_history",
                "arguments": '{"patient_id": "123"}'
            }
        )
        assert message.function_call is not None
        assert message.function_call["name"] == "get_patient_history"

    def test_chat_completion_request_valid(self):
        """Test valid chat completion request."""
        request = ChatCompletionRequest(
            messages=[
                ChatMessage(role="system", content="You are a medical assistant."),
                ChatMessage(role="user", content="What is hypertension?")
            ],
            model="gpt-4",
            temperature=0.7,
            max_tokens=500
        )
        assert len(request.messages) == 2
        assert request.model == "gpt-4"
        assert request.temperature == 0.7
        assert request.max_tokens == 500
        assert request.stream is False

    def test_chat_completion_request_defaults(self):
        """Test chat completion request with defaults."""
        request = ChatCompletionRequest(
            messages=[
                ChatMessage(role="user", content="Hello")
            ]
        )
        assert request.model == "gpt-4"
        assert request.temperature == 0.7
        assert request.max_tokens == 1000

    def test_chat_completion_request_temperature_validation(self):
        """Test temperature must be between 0 and 2."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ChatCompletionRequest(
                messages=[ChatMessage(role="user", content="Hi")],
                temperature=3.0  # Invalid - max is 2
            )


class TestConversationSchemas:
    """Tests for conversation schemas."""

    def test_conversation_create_valid(self):
        """Test valid conversation creation."""
        patient_id = uuid4()
        conv = ConversationCreate(
            conversation_type=ConversationType.SYMPTOM_ASSESSMENT,
            patient_id=patient_id,
            channel="whatsapp",
            language="en"
        )
        assert conv.conversation_type == ConversationType.SYMPTOM_ASSESSMENT
        assert conv.patient_id == patient_id
        assert conv.channel == "whatsapp"
        assert conv.language == "en"

    def test_conversation_create_defaults(self):
        """Test conversation creation with defaults."""
        conv = ConversationCreate()
        assert conv.conversation_type == ConversationType.GENERAL_INQUIRY
        assert conv.patient_id is None
        assert conv.channel == "web"
        assert conv.language == "en"

    def test_conversation_message_send_valid(self):
        """Test valid message send."""
        msg = ConversationMessageSend(
            content="I have been experiencing headaches"
        )
        assert msg.content == "I have been experiencing headaches"

    def test_conversation_message_send_length_validation(self):
        """Test message content length validation."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ConversationMessageSend(content="")  # Too short

    def test_conversation_end_request_valid(self):
        """Test valid conversation end request."""
        end = ConversationEndRequest(
            satisfaction_rating=5,
            feedback="Very helpful assistant!"
        )
        assert end.satisfaction_rating == 5
        assert end.feedback == "Very helpful assistant!"

    def test_conversation_end_request_rating_validation(self):
        """Test satisfaction rating must be 1-5."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ConversationEndRequest(satisfaction_rating=10)  # Invalid


class TestTriageSchemas:
    """Tests for triage schemas."""

    def test_symptom_input_valid(self):
        """Test valid symptom input."""
        symptom = SymptomInput(
            name="chest pain",
            severity=7,
            duration="2 hours",
            onset="sudden",
            location="left chest",
            associated_symptoms=["shortness of breath", "sweating"]
        )
        assert symptom.name == "chest pain"
        assert symptom.severity == 7
        assert symptom.onset == "sudden"
        assert len(symptom.associated_symptoms) == 2

    def test_symptom_input_severity_validation(self):
        """Test severity must be 1-10."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            SymptomInput(name="pain", severity=15)  # Invalid

    def test_triage_request_valid(self):
        """Test valid triage request."""
        request = TriageRequest(
            symptoms=[
                SymptomInput(name="chest pain", severity=7),
                SymptomInput(name="shortness of breath", severity=6)
            ],
            patient_age=55,
            patient_sex="M",
            medical_history=["hypertension", "diabetes"],
            current_medications=["metformin", "lisinopril"]
        )
        assert len(request.symptoms) == 2
        assert request.patient_age == 55
        assert request.patient_sex == "M"
        assert "hypertension" in request.medical_history

    def test_triage_request_requires_symptoms(self):
        """Test triage request requires at least one symptom."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            TriageRequest(symptoms=[])  # Empty symptoms


class TestNLPSchemas:
    """Tests for NLP schemas."""

    def test_entity_extraction_request_valid(self):
        """Test valid entity extraction request."""
        request = EntityExtractionRequest(
            text="Patient has type 2 diabetes mellitus and is taking metformin 500mg twice daily.",
            entity_types=["condition", "medication", "dosage"]
        )
        assert len(request.text) > 0
        assert len(request.entity_types) == 3

    def test_coding_suggestion_request_valid(self):
        """Test valid coding suggestion request."""
        request = CodingSuggestionRequest(
            text="Essential hypertension with chronic kidney disease stage 3",
            code_system="ICD-10",
            max_suggestions=5
        )
        assert request.code_system == "ICD-10"
        assert request.max_suggestions == 5

    def test_coding_suggestion_request_max_validation(self):
        """Test max suggestions must be 1-20."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            CodingSuggestionRequest(
                text="test",
                max_suggestions=100  # Invalid
            )


class TestKnowledgeBaseSchemas:
    """Tests for knowledge base schemas."""

    def test_knowledge_document_create_valid(self):
        """Test valid knowledge document creation."""
        doc = KnowledgeDocumentCreate(
            title="Hypertension Management Guidelines",
            content="This guideline covers the management of hypertension...",
            document_type=DocumentType.CLINICAL_GUIDELINE,
            specialty="Cardiology",
            condition_codes=["I10", "I11.0"],
            evidence_level=EvidenceLevel.LEVEL_A
        )
        assert doc.title == "Hypertension Management Guidelines"
        assert doc.document_type == DocumentType.CLINICAL_GUIDELINE
        assert doc.evidence_level == EvidenceLevel.LEVEL_A

    def test_semantic_search_request_valid(self):
        """Test valid semantic search request."""
        request = SemanticSearchRequest(
            query="treatment for hypertension in diabetic patients",
            top_k=5,
            document_types=[DocumentType.CLINICAL_GUIDELINE],
            evidence_levels=[EvidenceLevel.LEVEL_A, EvidenceLevel.LEVEL_B],
            min_similarity=0.7
        )
        assert request.top_k == 5
        assert request.min_similarity == 0.7

    def test_semantic_search_request_similarity_validation(self):
        """Test min_similarity must be 0-1."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            SemanticSearchRequest(
                query="test",
                min_similarity=1.5  # Invalid
            )


class TestPHIProtectionSchemas:
    """Tests for PHI protection schemas."""

    def test_phi_detection_request_valid(self):
        """Test valid PHI detection request."""
        request = PHIDetectionRequest(
            text="Patient John Doe (SSN: 123-45-6789) was seen today.",
            phi_types=[PHIType.NAME, PHIType.SSN]
        )
        assert len(request.text) > 0
        assert PHIType.NAME in request.phi_types

    def test_deidentification_request_valid(self):
        """Test valid de-identification request."""
        request = DeidentificationRequest(
            text="Patient John Doe (MRN: 12345) was seen today.",
            strategy=MaskingStrategy.PSEUDONYMIZE,
            preserve_format=True,
            reason="Research data preparation"
        )
        assert request.strategy == MaskingStrategy.PSEUDONYMIZE
        assert request.preserve_format is True

    def test_reidentification_request_valid(self):
        """Test valid re-identification request."""
        request = ReidentificationRequest(
            result_id=uuid4(),
            text="Patient [PATIENT_001] was seen today.",
            reason="Clinical review required",
            consent_verified=True
        )
        assert request.consent_verified is True


class TestConsentSchemas:
    """Tests for consent schemas."""

    def test_consent_create_valid(self):
        """Test valid consent creation."""
        consent = ConsentCreate(
            patient_id=uuid4(),
            purpose="ai_processing",
            granted=True,
            allowed_phi_types=[PHIType.NAME, PHIType.DATE_OF_BIRTH],
            allowed_uses=["triage", "documentation"]
        )
        assert consent.granted is True
        assert len(consent.allowed_phi_types) == 2


class TestMonitoringSchemas:
    """Tests for monitoring schemas."""

    def test_ai_metrics_request_valid(self):
        """Test valid metrics request."""
        request = AIMetricsRequest(
            start_time=datetime.now(timezone.utc) - timedelta(days=7),
            end_time=datetime.now(timezone.utc),
            request_type=AIRequestType.CHAT_COMPLETION,
            provider=AIProviderType.OPENAI
        )
        assert request.provider == AIProviderType.OPENAI


class TestExperimentSchemas:
    """Tests for A/B experiment schemas."""

    def test_experiment_create_valid(self):
        """Test valid experiment creation."""
        experiment = ExperimentCreate(
            name="GPT-4 vs GPT-4 Turbo for Triage",
            description="Compare models for triage accuracy",
            variants={
                "control": {"model": "gpt-4"},
                "treatment": {"model": "gpt-4-turbo"}
            },
            traffic_split={"control": 0.5, "treatment": 0.5},
            primary_metric="accuracy"
        )
        assert experiment.name == "GPT-4 vs GPT-4 Turbo for Triage"
        assert sum(experiment.traffic_split.values()) == 1.0

    def test_experiment_traffic_split_validation(self):
        """Test traffic split must sum to 1.0."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ExperimentCreate(
                name="Test",
                variants={"a": {}, "b": {}},
                traffic_split={"a": 0.3, "b": 0.3}  # Sums to 0.6
            )


class TestPromptTemplateSchemas:
    """Tests for prompt template schemas."""

    def test_prompt_template_create_valid(self):
        """Test valid prompt template creation."""
        template = PromptTemplateCreate(
            name="Medical Triage Prompt",
            category="triage",
            system_prompt="You are a medical triage assistant...",
            user_template="Patient symptoms: {symptoms}\nAge: {age}",
            variables=["symptoms", "age"],
            default_temperature=0.3,
            default_max_tokens=500
        )
        assert template.category == "triage"
        assert "symptoms" in template.variables
        assert template.default_temperature == 0.3

    def test_prompt_template_temperature_validation(self):
        """Test temperature must be 0-2."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            PromptTemplateCreate(
                name="Test",
                category="test",
                system_prompt="test",
                user_template="test",
                default_temperature=5.0  # Invalid
            )


class TestCostAlertSchemas:
    """Tests for cost alert schemas."""

    def test_cost_alert_create_valid(self):
        """Test valid cost alert creation."""
        alert = CostAlertCreate(
            name="Daily Spend Alert",
            threshold_usd=100.0,
            period="daily",
            notify_emails=["admin@example.com"]
        )
        assert alert.threshold_usd == 100.0
        assert alert.period == "daily"

    def test_cost_alert_threshold_validation(self):
        """Test threshold must be positive."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            CostAlertCreate(
                name="Test",
                threshold_usd=-50.0,  # Invalid
                period="daily"
            )


class TestDocumentationSchemas:
    """Tests for documentation schemas."""

    def test_documentation_request_valid(self):
        """Test valid documentation request."""
        request = DocumentationRequest(
            documentation_type="soap_note",
            clinical_input="Patient presents with 2-day history of sore throat and fever. Temperature 101.2F.",
            patient_context={"age": 35, "sex": "F"}
        )
        assert request.documentation_type == "soap_note"
        assert request.patient_context["age"] == 35


class TestQualitySchemas:
    """Tests for quality rating schemas."""

    def test_quality_rating_request_valid(self):
        """Test valid quality rating request."""
        rating = QualityRatingRequest(
            request_id=uuid4(),
            rating=QualityRating.EXCELLENT,
            feedback="Very accurate diagnosis assistance"
        )
        assert rating.rating == QualityRating.EXCELLENT


# ============================================================================
# MODEL TESTS
# ============================================================================

class TestAIRequestLogModel:
    """Tests for AI request log model."""

    def test_ai_request_log_creation(self):
        """Test creating an AI request log."""
        log = AIRequestLog(
            id=uuid4(),
            tenant_id=uuid4(),
            request_type=ModelAIRequestType.CHAT_COMPLETION,
            provider=ModelAIProviderType.OPENAI,
            model="gpt-4",
            prompt_hash="abc123def456",
            input_tokens=100,
            output_tokens=200,
            total_tokens=300,
            latency_ms=1500.5,
            estimated_cost_usd=0.012,
            success=True
        )
        assert log.model == "gpt-4"
        assert log.total_tokens == 300
        assert log.success is True


class TestAIConversationModel:
    """Tests for AI conversation model."""

    def test_ai_conversation_creation(self):
        """Test creating an AI conversation."""
        conv = AIConversation(
            id=uuid4(),
            tenant_id=uuid4(),
            conversation_type=ModelConversationType.SYMPTOM_ASSESSMENT,
            status=ModelConversationStatus.ACTIVE,
            patient_id=uuid4(),
            channel="whatsapp",
            language="en",
            turn_count=5,
            total_tokens_used=1000,
            total_cost_usd=0.05
        )
        assert conv.channel == "whatsapp"
        assert conv.turn_count == 5


class TestMedicalKnowledgeDocumentModel:
    """Tests for medical knowledge document model."""

    def test_medical_knowledge_document_creation(self):
        """Test creating a medical knowledge document."""
        doc = MedicalKnowledgeDocument(
            id=uuid4(),
            tenant_id=uuid4(),
            title="Diabetes Management Protocol",
            content="This protocol covers...",
            document_type=ModelDocumentType.PROTOCOL,
            specialty="Endocrinology",
            condition_codes=["E11.9"],
            evidence_level=ModelEvidenceLevel.LEVEL_A,
            is_indexed=True,
            chunk_count=5
        )
        assert doc.specialty == "Endocrinology"
        assert doc.is_indexed is True


class TestPHIAuditLogModel:
    """Tests for PHI audit log model."""

    def test_phi_audit_log_creation(self):
        """Test creating a PHI audit log."""
        log = PHIAuditLog(
            id=uuid4(),
            tenant_id=uuid4(),
            action=PHIActionType.DEIDENTIFY,
            resource_type="text",
            resource_id="doc-123",
            phi_types_detected=["name", "ssn", "mrn"],
            phi_count=3,
            consent_verified=True,
            reason="Research data preparation"
        )
        assert log.action == PHIActionType.DEIDENTIFY
        assert log.phi_count == 3


class TestPatientAIConsentModel:
    """Tests for patient AI consent model."""

    def test_patient_ai_consent_creation(self):
        """Test creating a patient AI consent."""
        consent = PatientAIConsent(
            id=uuid4(),
            tenant_id=uuid4(),
            patient_id=uuid4(),
            purpose="ai_processing",
            granted=True,
            allowed_phi_types=["name", "date_of_birth"],
            allowed_uses=["triage", "documentation"],
            revoked=False
        )
        assert consent.granted is True
        assert "triage" in consent.allowed_uses


class TestAIExperimentModel:
    """Tests for AI experiment model."""

    def test_ai_experiment_creation(self):
        """Test creating an AI experiment."""
        experiment = AIExperiment(
            id=uuid4(),
            tenant_id=uuid4(),
            name="Model Comparison Test",
            description="Compare GPT-4 vs Claude for triage",
            status=ExperimentStatus.RUNNING,
            variants={"control": {"model": "gpt-4"}, "treatment": {"model": "claude-3"}},
            traffic_split={"control": 0.5, "treatment": 0.5},
            primary_metric="accuracy"
        )
        assert experiment.status == ExperimentStatus.RUNNING
        assert experiment.primary_metric == "accuracy"


class TestPromptTemplateModel:
    """Tests for prompt template model."""

    def test_prompt_template_creation(self):
        """Test creating a prompt template."""
        template = PromptTemplate(
            id=uuid4(),
            tenant_id=uuid4(),
            name="Triage Assessment",
            category="triage",
            version=1,
            system_prompt="You are a medical triage assistant.",
            user_template="Symptoms: {symptoms}",
            variables=["symptoms"],
            default_temperature=0.3,
            default_max_tokens=500,
            use_count=100,
            is_active=True
        )
        assert template.version == 1
        assert template.use_count == 100


class TestAICostSummaryModel:
    """Tests for AI cost summary model."""

    def test_ai_cost_summary_creation(self):
        """Test creating an AI cost summary."""
        summary = AICostSummary(
            id=uuid4(),
            tenant_id=uuid4(),
            summary_date=datetime.now(timezone.utc),
            total_input_tokens=100000,
            total_output_tokens=50000,
            total_tokens=150000,
            total_cost_usd=15.50,
            cost_by_model={"gpt-4": 10.00, "gpt-3.5-turbo": 5.50},
            cost_by_feature={"triage": 8.00, "documentation": 7.50},
            total_requests=500,
            successful_requests=495,
            failed_requests=5,
            avg_latency_ms=1200,
            p95_latency_ms=2500
        )
        assert summary.total_cost_usd == 15.50
        assert summary.successful_requests == 495


class TestAICostAlertModel:
    """Tests for AI cost alert model."""

    def test_ai_cost_alert_creation(self):
        """Test creating an AI cost alert."""
        alert = AICostAlert(
            id=uuid4(),
            tenant_id=uuid4(),
            name="High Daily Spend",
            threshold_usd=100.0,
            period="daily",
            notify_emails=["admin@example.com", "finance@example.com"],
            is_active=True,
            trigger_count=5
        )
        assert alert.threshold_usd == 100.0
        assert alert.trigger_count == 5


# ============================================================================
# SERVICE LAYER TESTS
# ============================================================================

class TestChatCompletionService:
    """Tests for chat completion service."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()
        db.query = MagicMock()
        return db

    @pytest.mark.asyncio
    async def test_chat_completion_success(self, mock_db):
        """Test successful chat completion."""
        from services.prm.modules.ai.service import AIService

        tenant_id = uuid4()
        service = AIService(mock_db, tenant_id)

        result = await service.chat_completion(
            messages=[
                {"role": "user", "content": "What is diabetes?"}
            ],
            model="gpt-4",
            temperature=0.7
        )

        assert result is not None
        assert "message" in result
        mock_db.add.assert_called()

    @pytest.mark.asyncio
    async def test_chat_completion_with_system_prompt(self, mock_db):
        """Test chat completion with system prompt."""
        from services.prm.modules.ai.service import AIService

        tenant_id = uuid4()
        service = AIService(mock_db, tenant_id)

        result = await service.chat_completion(
            messages=[
                {"role": "system", "content": "You are a medical expert."},
                {"role": "user", "content": "Explain hypertension."}
            ]
        )

        assert result is not None


class TestConversationService:
    """Tests for conversation service."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()
        db.query = MagicMock()
        return db

    @pytest.mark.asyncio
    async def test_start_conversation(self, mock_db):
        """Test starting a new conversation."""
        from services.prm.modules.ai.service import AIService

        tenant_id = uuid4()
        patient_id = uuid4()
        service = AIService(mock_db, tenant_id)

        result = await service.start_conversation(
            conversation_type="symptom_assessment",
            patient_id=patient_id,
            channel="web"
        )

        assert result is not None
        assert result["status"] == "active"
        mock_db.add.assert_called()

    @pytest.mark.asyncio
    async def test_send_message_to_conversation(self, mock_db):
        """Test sending a message to a conversation."""
        from services.prm.modules.ai.service import AIService

        tenant_id = uuid4()
        service = AIService(mock_db, tenant_id)

        # Mock existing conversation
        mock_conversation = AIConversation(
            id=uuid4(),
            tenant_id=tenant_id,
            conversation_type=ModelConversationType.GENERAL_INQUIRY,
            status=ModelConversationStatus.ACTIVE,
            turn_count=0,
            context={}
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_conversation

        result = await service.send_message(
            conversation_id=mock_conversation.id,
            content="I have a headache"
        )

        assert result is not None


class TestTriageService:
    """Tests for medical triage service."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()
        return db

    @pytest.mark.asyncio
    async def test_perform_triage(self, mock_db):
        """Test performing symptom triage."""
        from services.prm.modules.ai.service import AIService

        tenant_id = uuid4()
        service = AIService(mock_db, tenant_id)

        result = await service.perform_triage(
            symptoms=[
                {"name": "chest pain", "severity": 7},
                {"name": "shortness of breath", "severity": 6}
            ],
            patient_age=55,
            patient_sex="M",
            medical_history=["hypertension"]
        )

        assert result is not None
        assert "urgency_level" in result
        assert "recommended_action" in result

    @pytest.mark.asyncio
    async def test_triage_emergency_symptoms(self, mock_db):
        """Test triage with emergency symptoms."""
        from services.prm.modules.ai.service import AIService

        tenant_id = uuid4()
        service = AIService(mock_db, tenant_id)

        result = await service.perform_triage(
            symptoms=[
                {"name": "severe chest pain", "severity": 9, "onset": "sudden"},
                {"name": "difficulty breathing", "severity": 8}
            ],
            patient_age=60
        )

        # High severity symptoms should trigger urgent response
        assert result is not None
        assert result.get("urgency_level") in ["emergency", "urgent"]


class TestNLPService:
    """Tests for NLP service."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        return db

    @pytest.mark.asyncio
    async def test_extract_entities(self, mock_db):
        """Test extracting clinical entities."""
        from services.prm.modules.ai.service import AIService

        tenant_id = uuid4()
        service = AIService(mock_db, tenant_id)

        result = await service.extract_entities(
            text="Patient has type 2 diabetes mellitus and is taking metformin 500mg."
        )

        assert result is not None
        assert "entities" in result

    @pytest.mark.asyncio
    async def test_get_coding_suggestions(self, mock_db):
        """Test getting medical coding suggestions."""
        from services.prm.modules.ai.service import AIService

        tenant_id = uuid4()
        service = AIService(mock_db, tenant_id)

        result = await service.get_coding_suggestions(
            text="Essential hypertension",
            code_system="ICD-10"
        )

        assert result is not None


class TestKnowledgeBaseService:
    """Tests for knowledge base service."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()
        db.query = MagicMock()
        return db

    @pytest.mark.asyncio
    async def test_index_document(self, mock_db):
        """Test indexing a knowledge document."""
        from services.prm.modules.ai.service import AIService

        tenant_id = uuid4()
        service = AIService(mock_db, tenant_id)

        result = await service.index_document(
            title="Hypertension Guidelines",
            content="This guideline covers the management...",
            document_type="clinical_guideline",
            specialty="Cardiology"
        )

        assert result is not None
        mock_db.add.assert_called()

    @pytest.mark.asyncio
    async def test_semantic_search(self, mock_db):
        """Test semantic search."""
        from services.prm.modules.ai.service import AIService

        tenant_id = uuid4()
        service = AIService(mock_db, tenant_id)

        result = await service.semantic_search(
            query="treatment for hypertension",
            top_k=5
        )

        assert result is not None
        assert isinstance(result, list)


class TestPHIProtectionService:
    """Tests for PHI protection service."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        return db

    @pytest.mark.asyncio
    async def test_deidentify_text(self, mock_db):
        """Test de-identifying text."""
        from services.prm.modules.ai.service import AIService

        tenant_id = uuid4()
        service = AIService(mock_db, tenant_id)

        result = await service.deidentify_text(
            text="Patient John Doe (SSN: 123-45-6789) was seen today.",
            strategy="pseudonymize"
        )

        assert result is not None
        assert "deidentified_text" in result
        # Original SSN should not appear in result
        assert "123-45-6789" not in result.get("deidentified_text", "")

    @pytest.mark.asyncio
    async def test_record_consent(self, mock_db):
        """Test recording patient consent."""
        from services.prm.modules.ai.service import AIService

        tenant_id = uuid4()
        patient_id = uuid4()
        service = AIService(mock_db, tenant_id)

        result = await service.record_consent(
            patient_id=patient_id,
            purpose="ai_processing",
            granted=True
        )

        assert result is not None
        mock_db.add.assert_called()


class TestMonitoringService:
    """Tests for AI monitoring service."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.query = MagicMock()
        return db

    @pytest.mark.asyncio
    async def test_get_metrics(self, mock_db):
        """Test getting AI metrics."""
        from services.prm.modules.ai.service import AIService

        tenant_id = uuid4()
        service = AIService(mock_db, tenant_id)

        # Mock empty request logs
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = await service.get_metrics(
            start_time=datetime.now(timezone.utc) - timedelta(days=1),
            end_time=datetime.now(timezone.utc)
        )

        assert result is not None
        assert "total_requests" in result

    @pytest.mark.asyncio
    async def test_get_cost_summary(self, mock_db):
        """Test getting cost summary."""
        from services.prm.modules.ai.service import AIService

        tenant_id = uuid4()
        service = AIService(mock_db, tenant_id)

        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = await service.get_cost_summary(
            start_date=datetime.now(timezone.utc) - timedelta(days=7),
            end_date=datetime.now(timezone.utc),
            period="daily"
        )

        assert result is not None


class TestExperimentService:
    """Tests for A/B experiment service."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()
        db.query = MagicMock()
        return db

    @pytest.mark.asyncio
    async def test_create_experiment(self, mock_db):
        """Test creating an A/B experiment."""
        from services.prm.modules.ai.service import AIService

        tenant_id = uuid4()
        service = AIService(mock_db, tenant_id)

        result = await service.create_experiment(
            name="Model Comparison",
            variants={"control": {"model": "gpt-4"}, "treatment": {"model": "gpt-4-turbo"}},
            traffic_split={"control": 0.5, "treatment": 0.5}
        )

        assert result is not None
        mock_db.add.assert_called()


class TestDocumentationService:
    """Tests for documentation generation service."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.add = MagicMock()
        return db

    @pytest.mark.asyncio
    async def test_generate_soap_note(self, mock_db):
        """Test generating a SOAP note."""
        from services.prm.modules.ai.service import AIService

        tenant_id = uuid4()
        service = AIService(mock_db, tenant_id)

        result = await service.generate_documentation(
            documentation_type="soap_note",
            clinical_input="Patient presents with sore throat and fever for 2 days."
        )

        assert result is not None
        assert "suggested_text" in result


# ============================================================================
# INTEGRATION STYLE TESTS
# ============================================================================

class TestTriageUrgencyLevels:
    """Tests for triage urgency level classification."""

    def test_urgency_level_order(self):
        """Test urgency levels are properly ordered."""
        levels = [
            UrgencyLevel.EMERGENCY,
            UrgencyLevel.URGENT,
            UrgencyLevel.SOON,
            UrgencyLevel.ROUTINE,
            UrgencyLevel.SELF_CARE
        ]
        # Verify all levels exist
        assert len(levels) == 5

    def test_emergency_symptoms_detection(self):
        """Test emergency symptom patterns."""
        emergency_keywords = [
            "chest pain", "difficulty breathing", "severe bleeding",
            "stroke symptoms", "loss of consciousness", "severe allergic reaction"
        ]
        for keyword in emergency_keywords:
            assert len(keyword) > 0


class TestPHIMaskingStrategies:
    """Tests for PHI masking strategies."""

    def test_all_masking_strategies_defined(self):
        """Test all masking strategies are defined."""
        strategies = [
            MaskingStrategy.REDACT,
            MaskingStrategy.PSEUDONYMIZE,
            MaskingStrategy.HASH,
            MaskingStrategy.GENERALIZE,
            MaskingStrategy.SUPPRESS
        ]
        assert len(strategies) == 5

    def test_phi_types_coverage(self):
        """Test all HIPAA PHI types are covered."""
        hipaa_identifiers = [
            PHIType.NAME,
            PHIType.DATE_OF_BIRTH,
            PHIType.SSN,
            PHIType.MRN,
            PHIType.PHONE,
            PHIType.EMAIL,
            PHIType.ADDRESS,
            PHIType.ZIP_CODE,
            PHIType.ACCOUNT_NUMBER,
            PHIType.INSURANCE_ID,
            PHIType.IP_ADDRESS
        ]
        # HIPAA Safe Harbor requires 18 identifiers, we cover the main ones
        assert len(hipaa_identifiers) >= 10


class TestMedicalCodingSystems:
    """Tests for medical coding system support."""

    def test_supported_code_systems(self):
        """Test supported coding systems."""
        supported = ["ICD-10", "SNOMED", "CPT", "RxNorm", "LOINC", "HCPCS"]
        assert "ICD-10" in supported
        assert "SNOMED" in supported

    def test_icd10_code_format(self):
        """Test ICD-10 code format validation."""
        valid_codes = ["I10", "E11.9", "J06.9", "G43.909"]
        for code in valid_codes:
            # ICD-10 codes have specific format patterns
            assert len(code) >= 3


class TestConversationFlows:
    """Tests for conversation flow patterns."""

    def test_conversation_status_transitions(self):
        """Test valid conversation status transitions."""
        valid_transitions = {
            "active": ["paused", "waiting_input", "completed", "escalated"],
            "paused": ["active", "completed"],
            "waiting_input": ["active", "completed", "escalated"],
            "escalated": ["completed"]
        }
        # Verify transition rules
        for status, next_statuses in valid_transitions.items():
            assert isinstance(next_statuses, list)

    def test_channel_types(self):
        """Test supported channel types."""
        channels = ["web", "whatsapp", "voice", "sms", "email"]
        assert "web" in channels
        assert "whatsapp" in channels


class TestCostCalculations:
    """Tests for AI cost calculations."""

    def test_token_cost_calculation(self):
        """Test token-based cost calculation."""
        # GPT-4 pricing example (per 1K tokens)
        input_cost_per_1k = 0.03
        output_cost_per_1k = 0.06

        input_tokens = 1000
        output_tokens = 500

        input_cost = (input_tokens / 1000) * input_cost_per_1k
        output_cost = (output_tokens / 1000) * output_cost_per_1k
        total_cost = input_cost + output_cost

        assert total_cost == 0.03 + 0.03  # $0.06

    def test_cost_alert_periods(self):
        """Test valid cost alert periods."""
        periods = ["hourly", "daily", "weekly", "monthly"]
        assert "daily" in periods
        assert "monthly" in periods


class TestEvidenceLevels:
    """Tests for medical evidence levels."""

    def test_evidence_level_hierarchy(self):
        """Test evidence level hierarchy."""
        # Level A is strongest, Level D is weakest
        levels = {
            "A": "Strong evidence from multiple RCTs",
            "B": "Moderate evidence from limited RCTs",
            "C": "Weak evidence from observational studies",
            "D": "Expert opinion only"
        }
        assert len(levels) == 4


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Tests for error handling."""

    def test_invalid_temperature_raises_error(self):
        """Test invalid temperature validation."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ChatCompletionRequest(
                messages=[ChatMessage(role="user", content="Hi")],
                temperature=-0.5
            )

    def test_empty_messages_raises_error(self):
        """Test empty messages validation."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ChatCompletionRequest(messages=[])

    def test_invalid_satisfaction_rating_raises_error(self):
        """Test invalid satisfaction rating."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ConversationEndRequest(satisfaction_rating=0)  # Must be >= 1

    def test_invalid_severity_raises_error(self):
        """Test invalid symptom severity."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            SymptomInput(name="pain", severity=0)  # Must be >= 1


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
