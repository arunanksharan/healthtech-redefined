"""
LLM Service

Large Language Model integration:
- Multi-provider support (OpenAI, Anthropic, local)
- Prompt management
- Response streaming
- Token management
- Healthcare-specific prompts

EPIC-009: US-009.1 LLM Integration
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import asyncio
import logging

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"  # Self-hosted models


class MessageRole(str, Enum):
    """Chat message roles."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


@dataclass
class ChatMessage:
    """A message in a chat conversation."""
    role: MessageRole
    content: str
    name: Optional[str] = None  # For function messages
    function_call: Optional[Dict[str, Any]] = None


@dataclass
class TokenUsage:
    """Token usage for a completion."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class ChatCompletion:
    """Result of a chat completion."""
    completion_id: str
    provider: LLMProvider
    model: str

    # Response
    message: ChatMessage
    finish_reason: str = "stop"  # stop, length, function_call

    # Usage
    usage: TokenUsage = field(default_factory=TokenUsage)

    # Metadata
    latency_ms: float = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PromptTemplate:
    """A reusable prompt template."""
    template_id: str
    name: str
    system_prompt: str
    user_template: str  # Template with {placeholders}
    category: str = ""  # triage, documentation, chat
    variables: List[str] = field(default_factory=list)


class LLMService:
    """
    LLM integration service.

    Provides:
    - Chat completions
    - Streaming responses
    - Prompt templates
    - Token management
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        default_provider: LLMProvider = LLMProvider.OPENAI,
        default_model: str = "gpt-4",
    ):
        self.openai_api_key = openai_api_key
        self.anthropic_api_key = anthropic_api_key
        self.default_provider = default_provider
        self.default_model = default_model

        # Prompt templates
        self._templates: Dict[str, PromptTemplate] = {}
        self._load_healthcare_templates()

        # Usage tracking
        self._usage_log: List[TokenUsage] = []

    def _load_healthcare_templates(self):
        """Load healthcare-specific prompt templates."""
        self._templates = {
            "medical_assistant": PromptTemplate(
                template_id="medical_assistant",
                name="Medical Assistant",
                category="chat",
                system_prompt="""You are a helpful medical assistant for a healthcare practice.
You can help with:
- Answering general health questions
- Scheduling appointments
- Providing practice information
- Explaining medical terms in simple language

Important guidelines:
- Never provide specific medical diagnoses
- Always recommend consulting a healthcare provider for medical concerns
- Be empathetic and professional
- Protect patient privacy""",
                user_template="{user_message}",
                variables=["user_message"],
            ),
            "symptom_triage": PromptTemplate(
                template_id="symptom_triage",
                name="Symptom Triage",
                category="triage",
                system_prompt="""You are a medical triage assistant. Based on the patient's symptoms,
assess the urgency level and provide guidance.

Urgency levels:
- EMERGENCY: Life-threatening, call 911
- URGENT: Needs same-day care
- SOON: Schedule within 24-48 hours
- ROUTINE: Schedule regular appointment

Always err on the side of caution. If unsure, recommend higher urgency.""",
                user_template="""Patient symptoms: {symptoms}
Duration: {duration}
Severity (1-10): {severity}
Associated symptoms: {associated_symptoms}
Medical history: {medical_history}

Assess urgency and provide guidance.""",
                variables=["symptoms", "duration", "severity", "associated_symptoms", "medical_history"],
            ),
            "clinical_note_assist": PromptTemplate(
                template_id="clinical_note_assist",
                name="Clinical Note Assistant",
                category="documentation",
                system_prompt="""You are a clinical documentation assistant. Help providers
create accurate, compliant clinical notes based on visit information.

Follow SOAP format:
- Subjective: Patient's description
- Objective: Exam findings, vitals
- Assessment: Diagnosis/differential
- Plan: Treatment plan

Use proper medical terminology while being concise.""",
                user_template="""Chief complaint: {chief_complaint}
History of present illness: {hpi}
Physical exam: {exam_findings}
Vitals: {vitals}

Generate a clinical note in SOAP format.""",
                variables=["chief_complaint", "hpi", "exam_findings", "vitals"],
            ),
            "patient_education": PromptTemplate(
                template_id="patient_education",
                name="Patient Education",
                category="education",
                system_prompt="""You are a patient education specialist. Explain medical
conditions, treatments, and instructions in clear, simple language that patients can understand.

Guidelines:
- Use plain language (6th grade reading level)
- Avoid medical jargon or explain when necessary
- Include actionable steps
- Be encouraging and supportive""",
                user_template="""Topic: {topic}
Patient context: {context}
Specific questions: {questions}

Provide clear patient education.""",
                variables=["topic", "context", "questions"],
            ),
            "medication_counseling": PromptTemplate(
                template_id="medication_counseling",
                name="Medication Counseling",
                category="pharmacy",
                system_prompt="""You are a medication counseling assistant. Provide clear
information about medications including:
- What the medication is for
- How to take it correctly
- Common side effects
- Important warnings
- Drug/food interactions

Use patient-friendly language.""",
                user_template="""Medication: {medication}
Condition: {condition}
Patient concerns: {concerns}

Provide medication counseling information.""",
                variables=["medication", "condition", "concerns"],
            ),
        }

    async def complete(
        self,
        messages: List[ChatMessage],
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        functions: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False,
    ) -> ChatCompletion:
        """
        Get a chat completion from the LLM.

        Args:
            messages: Conversation messages
            provider: LLM provider to use
            model: Model name
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum response tokens
            functions: Function definitions for function calling
            stream: Whether to stream the response

        Returns:
            ChatCompletion with the response
        """
        provider = provider or self.default_provider
        model = model or self.default_model

        start_time = datetime.now(timezone.utc)

        try:
            if provider == LLMProvider.OPENAI:
                result = await self._complete_openai(
                    messages, model, temperature, max_tokens, functions
                )
            elif provider == LLMProvider.ANTHROPIC:
                result = await self._complete_anthropic(
                    messages, model, temperature, max_tokens
                )
            else:
                result = await self._complete_local(
                    messages, model, temperature, max_tokens
                )

            # Calculate latency
            latency = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            result.latency_ms = latency

            # Log usage
            self._usage_log.append(result.usage)

            return result

        except Exception as e:
            logger.error(f"LLM completion error: {e}")
            raise

    async def _complete_openai(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float,
        max_tokens: int,
        functions: Optional[List[Dict[str, Any]]],
    ) -> ChatCompletion:
        """Complete using OpenAI API."""
        # In production, use openai library
        # Mock response for now
        response_content = self._generate_mock_response(messages)

        return ChatCompletion(
            completion_id=str(uuid4()),
            provider=LLMProvider.OPENAI,
            model=model,
            message=ChatMessage(
                role=MessageRole.ASSISTANT,
                content=response_content,
            ),
            usage=TokenUsage(
                prompt_tokens=self._estimate_tokens(messages),
                completion_tokens=len(response_content.split()),
                total_tokens=self._estimate_tokens(messages) + len(response_content.split()),
            ),
        )

    async def _complete_anthropic(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> ChatCompletion:
        """Complete using Anthropic API."""
        # In production, use anthropic library
        response_content = self._generate_mock_response(messages)

        return ChatCompletion(
            completion_id=str(uuid4()),
            provider=LLMProvider.ANTHROPIC,
            model=model,
            message=ChatMessage(
                role=MessageRole.ASSISTANT,
                content=response_content,
            ),
            usage=TokenUsage(
                prompt_tokens=self._estimate_tokens(messages),
                completion_tokens=len(response_content.split()),
            ),
        )

    async def _complete_local(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> ChatCompletion:
        """Complete using local model."""
        response_content = self._generate_mock_response(messages)

        return ChatCompletion(
            completion_id=str(uuid4()),
            provider=LLMProvider.LOCAL,
            model=model,
            message=ChatMessage(
                role=MessageRole.ASSISTANT,
                content=response_content,
            ),
        )

    def _generate_mock_response(self, messages: List[ChatMessage]) -> str:
        """Generate mock response for development."""
        last_message = messages[-1].content if messages else ""

        if "symptom" in last_message.lower() or "triage" in last_message.lower():
            return """Based on the symptoms described, I recommend:

**Urgency Level: SOON**

The symptoms suggest a condition that should be evaluated within 24-48 hours.

**Recommended Actions:**
1. Schedule an appointment with your primary care provider
2. Monitor symptoms for any worsening
3. Stay hydrated and rest

**Warning Signs to Watch For:**
- Severe worsening of symptoms
- High fever (over 103°F)
- Difficulty breathing

If any warning signs develop, seek immediate medical care."""

        elif "medication" in last_message.lower():
            return """Here's important information about your medication:

**How to Take:**
- Take as directed by your healthcare provider
- Take with food to reduce stomach upset
- Take at the same time each day

**Common Side Effects:**
- Mild drowsiness
- Dry mouth
- Headache

**Important Warnings:**
- Do not stop taking suddenly without consulting your doctor
- Avoid alcohol while taking this medication

Contact your healthcare provider if you experience severe side effects."""

        else:
            return """I'm happy to help you with your healthcare needs. How can I assist you today?

I can help with:
- Answering general health questions
- Providing appointment information
- Explaining medical terms
- General wellness guidance

Please note that I cannot provide specific medical diagnoses. For medical concerns, please consult with your healthcare provider."""

    def _estimate_tokens(self, messages: List[ChatMessage]) -> int:
        """Estimate token count for messages."""
        total_chars = sum(len(m.content) for m in messages)
        return total_chars // 4  # Rough estimate: 4 chars per token

    async def stream_complete(
        self,
        messages: List[ChatMessage],
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a chat completion.

        Yields:
            Chunks of the response text
        """
        # Get full completion (in production, use actual streaming)
        completion = await self.complete(
            messages=messages,
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Simulate streaming
        words = completion.message.content.split()
        for i in range(0, len(words), 3):
            chunk = " ".join(words[i:i+3]) + " "
            yield chunk
            await asyncio.sleep(0.05)

    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """Get a prompt template by ID."""
        return self._templates.get(template_id)

    def render_template(
        self,
        template_id: str,
        variables: Dict[str, Any],
    ) -> List[ChatMessage]:
        """Render a template into chat messages."""
        template = self._templates.get(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        # Create system message
        system_msg = ChatMessage(
            role=MessageRole.SYSTEM,
            content=template.system_prompt,
        )

        # Render user message with variables
        user_content = template.user_template.format(**variables)
        user_msg = ChatMessage(
            role=MessageRole.USER,
            content=user_content,
        )

        return [system_msg, user_msg]

    async def complete_with_template(
        self,
        template_id: str,
        variables: Dict[str, Any],
        **kwargs,
    ) -> ChatCompletion:
        """Complete using a prompt template."""
        messages = self.render_template(template_id, variables)
        return await self.complete(messages, **kwargs)

    def get_usage_summary(self) -> Dict[str, Any]:
        """Get token usage summary."""
        if not self._usage_log:
            return {"total_tokens": 0, "requests": 0}

        return {
            "total_tokens": sum(u.total_tokens for u in self._usage_log),
            "prompt_tokens": sum(u.prompt_tokens for u in self._usage_log),
            "completion_tokens": sum(u.completion_tokens for u in self._usage_log),
            "requests": len(self._usage_log),
        }


# Global LLM service instance
llm_service = LLMService()
