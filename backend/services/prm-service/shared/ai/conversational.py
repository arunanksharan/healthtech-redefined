"""
Conversational AI Service

Manages conversational AI interactions for healthcare:
- Multi-turn conversation management
- Context persistence and retrieval
- Intent recognition
- Healthcare-specific conversation flows
- Patient communication assistance

EPIC-009: US-009.2 Conversational AI
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import asyncio
import logging

from .llm_service import LLMService, ChatMessage, MessageRole, ChatCompletion

logger = logging.getLogger(__name__)


class ConversationState(str, Enum):
    """State of a conversation."""
    ACTIVE = "active"
    PAUSED = "paused"
    WAITING_INPUT = "waiting_input"
    COMPLETED = "completed"
    ESCALATED = "escalated"


class ConversationType(str, Enum):
    """Type of conversation."""
    GENERAL_INQUIRY = "general_inquiry"
    APPOINTMENT_BOOKING = "appointment_booking"
    SYMPTOM_ASSESSMENT = "symptom_assessment"
    MEDICATION_QUESTION = "medication_question"
    BILLING_INQUIRY = "billing_inquiry"
    PRESCRIPTION_REFILL = "prescription_refill"
    LAB_RESULTS = "lab_results"
    PROVIDER_MESSAGE = "provider_message"


class IntentType(str, Enum):
    """Recognized intents in healthcare conversations."""
    BOOK_APPOINTMENT = "book_appointment"
    CANCEL_APPOINTMENT = "cancel_appointment"
    RESCHEDULE_APPOINTMENT = "reschedule_appointment"
    CHECK_SYMPTOMS = "check_symptoms"
    MEDICATION_INFO = "medication_info"
    REFILL_REQUEST = "refill_request"
    BILLING_QUESTION = "billing_question"
    INSURANCE_QUESTION = "insurance_question"
    LAB_RESULTS_INQUIRY = "lab_results_inquiry"
    PROVIDER_CONTACT = "provider_contact"
    GENERAL_QUESTION = "general_question"
    GREETING = "greeting"
    GOODBYE = "goodbye"
    UNCLEAR = "unclear"


@dataclass
class Intent:
    """Recognized intent from user input."""
    intent_type: IntentType
    confidence: float  # 0-1
    entities: Dict[str, Any] = field(default_factory=dict)
    # Extracted entities like date, time, provider name, symptom, etc.


@dataclass
class ConversationContext:
    """
    Context for a conversation.

    Stores relevant information extracted during the conversation
    that should persist across turns.
    """
    context_id: str = field(default_factory=lambda: str(uuid4()))

    # Patient context
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    patient_preferences: Dict[str, Any] = field(default_factory=dict)

    # Medical context (anonymized for AI)
    known_conditions: List[str] = field(default_factory=list)
    current_medications: List[str] = field(default_factory=list)
    allergies: List[str] = field(default_factory=list)

    # Conversation context
    current_topic: Optional[str] = None
    extracted_entities: Dict[str, Any] = field(default_factory=dict)
    pending_actions: List[Dict[str, Any]] = field(default_factory=list)

    # Appointment context
    preferred_provider: Optional[str] = None
    preferred_dates: List[str] = field(default_factory=list)
    preferred_times: List[str] = field(default_factory=list)
    appointment_reason: Optional[str] = None

    # Symptom context
    reported_symptoms: List[Dict[str, Any]] = field(default_factory=list)
    symptom_duration: Optional[str] = None
    symptom_severity: Optional[int] = None

    # Custom data
    custom_data: Dict[str, Any] = field(default_factory=dict)

    def update(self, **kwargs):
        """Update context with new values."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                self.custom_data[key] = value


@dataclass
class ConversationTurn:
    """A single turn in the conversation."""
    turn_id: str
    role: MessageRole
    content: str
    intent: Optional[Intent] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Conversation:
    """
    Represents a conversation session.

    Tracks the full conversation history and state.
    """
    conversation_id: str
    tenant_id: str
    conversation_type: ConversationType
    state: ConversationState = ConversationState.ACTIVE

    # Participants
    patient_id: Optional[str] = None
    assigned_agent: Optional[str] = None  # For human handoff

    # Context
    context: ConversationContext = field(default_factory=ConversationContext)

    # History
    turns: List[ConversationTurn] = field(default_factory=list)

    # Metadata
    channel: str = "web"  # web, whatsapp, voice, etc.
    language: str = "en"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None

    # Analytics
    turn_count: int = 0
    escalation_reason: Optional[str] = None
    satisfaction_rating: Optional[int] = None

    def add_turn(
        self,
        role: MessageRole,
        content: str,
        intent: Optional[Intent] = None,
        **metadata,
    ) -> ConversationTurn:
        """Add a turn to the conversation."""
        turn = ConversationTurn(
            turn_id=str(uuid4()),
            role=role,
            content=content,
            intent=intent,
            metadata=metadata,
        )
        self.turns.append(turn)
        self.turn_count += 1
        self.updated_at = datetime.now(timezone.utc)
        return turn

    def get_messages(self) -> List[ChatMessage]:
        """Convert turns to chat messages for LLM."""
        return [
            ChatMessage(role=turn.role, content=turn.content)
            for turn in self.turns
        ]


@dataclass
class ConversationFlow:
    """
    A conversation flow definition.

    Defines structured conversation paths for specific use cases.
    """
    flow_id: str
    name: str
    conversation_type: ConversationType

    # Flow steps
    steps: List[Dict[str, Any]] = field(default_factory=list)

    # Conditions and branching
    conditions: Dict[str, Any] = field(default_factory=dict)

    # Required entities to collect
    required_entities: List[str] = field(default_factory=list)

    # Completion actions
    completion_actions: List[Dict[str, Any]] = field(default_factory=list)


class IntentRecognizer:
    """
    Recognizes intents from user input.

    Uses pattern matching and keyword detection.
    In production, could integrate with more sophisticated NLU.
    """

    def __init__(self):
        self._intent_patterns = self._build_intent_patterns()

    def _build_intent_patterns(self) -> Dict[IntentType, List[str]]:
        """Build keyword patterns for intent recognition."""
        return {
            IntentType.BOOK_APPOINTMENT: [
                "book", "schedule", "appointment", "make an appointment",
                "see the doctor", "visit", "new appointment",
            ],
            IntentType.CANCEL_APPOINTMENT: [
                "cancel", "cancel appointment", "don't need", "can't make it",
            ],
            IntentType.RESCHEDULE_APPOINTMENT: [
                "reschedule", "change appointment", "move appointment",
                "different time", "different date",
            ],
            IntentType.CHECK_SYMPTOMS: [
                "symptom", "feeling", "pain", "sick", "hurt",
                "not feeling well", "problem", "issue",
            ],
            IntentType.MEDICATION_INFO: [
                "medication", "medicine", "drug", "prescription",
                "side effect", "dose", "dosage", "how to take",
            ],
            IntentType.REFILL_REQUEST: [
                "refill", "renew prescription", "need more",
                "running out", "out of medication",
            ],
            IntentType.BILLING_QUESTION: [
                "bill", "billing", "charge", "payment", "pay",
                "cost", "invoice", "statement",
            ],
            IntentType.INSURANCE_QUESTION: [
                "insurance", "coverage", "copay", "deductible",
                "in-network", "out-of-network", "claim",
            ],
            IntentType.LAB_RESULTS_INQUIRY: [
                "lab results", "test results", "blood work",
                "lab report", "results ready",
            ],
            IntentType.PROVIDER_CONTACT: [
                "speak to doctor", "talk to nurse", "contact provider",
                "message doctor", "human", "representative",
            ],
            IntentType.GREETING: [
                "hello", "hi", "hey", "good morning", "good afternoon",
                "good evening", "greetings",
            ],
            IntentType.GOODBYE: [
                "bye", "goodbye", "thanks", "thank you", "that's all",
                "done", "finished",
            ],
        }

    def recognize(self, text: str) -> Intent:
        """Recognize intent from user text."""
        text_lower = text.lower()

        best_intent = IntentType.UNCLEAR
        best_confidence = 0.0

        for intent_type, patterns in self._intent_patterns.items():
            matches = sum(1 for p in patterns if p in text_lower)
            if matches > 0:
                confidence = min(0.95, matches * 0.3)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_intent = intent_type

        # Extract entities based on intent
        entities = self._extract_entities(text, best_intent)

        if best_confidence < 0.3:
            best_intent = IntentType.GENERAL_QUESTION
            best_confidence = 0.5

        return Intent(
            intent_type=best_intent,
            confidence=best_confidence,
            entities=entities,
        )

    def _extract_entities(
        self,
        text: str,
        intent: IntentType,
    ) -> Dict[str, Any]:
        """Extract relevant entities based on intent."""
        entities = {}

        # Simple entity extraction - in production use NER
        # Date patterns
        import re

        date_pattern = r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b'
        dates = re.findall(date_pattern, text)
        if dates:
            entities["dates"] = dates

        # Time patterns
        time_pattern = r'\b(\d{1,2}:\d{2}\s*(?:am|pm)?)\b'
        times = re.findall(time_pattern, text.lower())
        if times:
            entities["times"] = times

        # Day patterns
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        mentioned_days = [d for d in days if d in text.lower()]
        if mentioned_days:
            entities["days"] = mentioned_days

        return entities


class ConversationalAI:
    """
    Conversational AI service for healthcare.

    Manages conversations, intent recognition, context tracking,
    and generates appropriate responses.
    """

    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
    ):
        self.llm_service = llm_service or LLMService()
        self.intent_recognizer = IntentRecognizer()

        # Active conversations
        self._conversations: Dict[str, Conversation] = {}

        # Conversation flows
        self._flows: Dict[str, ConversationFlow] = {}
        self._load_default_flows()

        # Action handlers
        self._action_handlers: Dict[str, Callable] = {}

    def _load_default_flows(self):
        """Load default conversation flows."""
        self._flows = {
            "appointment_booking": ConversationFlow(
                flow_id="appointment_booking",
                name="Appointment Booking",
                conversation_type=ConversationType.APPOINTMENT_BOOKING,
                required_entities=["reason", "preferred_date", "preferred_time"],
                steps=[
                    {"id": "greeting", "prompt": "I'd be happy to help you schedule an appointment. What is the reason for your visit?"},
                    {"id": "collect_date", "prompt": "What date works best for you?"},
                    {"id": "collect_time", "prompt": "Do you prefer morning or afternoon?"},
                    {"id": "confirm", "prompt": "Let me confirm the details..."},
                ],
                completion_actions=[
                    {"action": "create_appointment", "params": ["reason", "date", "time"]},
                ],
            ),
            "symptom_check": ConversationFlow(
                flow_id="symptom_check",
                name="Symptom Assessment",
                conversation_type=ConversationType.SYMPTOM_ASSESSMENT,
                required_entities=["symptoms", "duration", "severity"],
                steps=[
                    {"id": "ask_symptoms", "prompt": "I understand you're not feeling well. Can you describe your symptoms?"},
                    {"id": "ask_duration", "prompt": "How long have you been experiencing these symptoms?"},
                    {"id": "ask_severity", "prompt": "On a scale of 1-10, how severe are your symptoms?"},
                    {"id": "provide_guidance", "prompt": "Based on what you've told me..."},
                ],
            ),
        }

    async def start_conversation(
        self,
        tenant_id: str,
        conversation_type: ConversationType = ConversationType.GENERAL_INQUIRY,
        patient_id: Optional[str] = None,
        channel: str = "web",
        language: str = "en",
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> Conversation:
        """
        Start a new conversation.

        Args:
            tenant_id: Tenant identifier
            conversation_type: Type of conversation
            patient_id: Patient identifier if known
            channel: Communication channel
            language: Conversation language
            initial_context: Initial context data

        Returns:
            New Conversation instance
        """
        conversation = Conversation(
            conversation_id=str(uuid4()),
            tenant_id=tenant_id,
            conversation_type=conversation_type,
            patient_id=patient_id,
            channel=channel,
            language=language,
        )

        # Initialize context
        if initial_context:
            conversation.context.update(**initial_context)

        # Add system greeting
        greeting = self._get_greeting(conversation_type, channel)
        conversation.add_turn(
            role=MessageRole.ASSISTANT,
            content=greeting,
        )

        # Store conversation
        self._conversations[conversation.conversation_id] = conversation

        logger.info(
            f"Started conversation {conversation.conversation_id} "
            f"of type {conversation_type.value}"
        )

        return conversation

    def _get_greeting(
        self,
        conversation_type: ConversationType,
        channel: str,
    ) -> str:
        """Get appropriate greeting based on conversation type."""
        greetings = {
            ConversationType.GENERAL_INQUIRY: (
                "Hello! I'm your virtual health assistant. "
                "How can I help you today?"
            ),
            ConversationType.APPOINTMENT_BOOKING: (
                "Hello! I can help you schedule an appointment. "
                "What type of appointment do you need?"
            ),
            ConversationType.SYMPTOM_ASSESSMENT: (
                "Hello! I understand you may not be feeling well. "
                "I'm here to help assess your symptoms and guide you to appropriate care. "
                "Can you tell me what symptoms you're experiencing?"
            ),
            ConversationType.MEDICATION_QUESTION: (
                "Hello! I can help answer questions about your medications. "
                "What would you like to know?"
            ),
            ConversationType.BILLING_INQUIRY: (
                "Hello! I can help with billing questions. "
                "What would you like to know about your account?"
            ),
        }
        return greetings.get(
            conversation_type,
            "Hello! How can I assist you today?"
        )

    async def process_message(
        self,
        conversation_id: str,
        user_message: str,
    ) -> str:
        """
        Process a user message and generate response.

        Args:
            conversation_id: Conversation identifier
            user_message: User's message text

        Returns:
            Assistant's response text
        """
        conversation = self._conversations.get(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation not found: {conversation_id}")

        # Recognize intent
        intent = self.intent_recognizer.recognize(user_message)

        # Add user turn
        conversation.add_turn(
            role=MessageRole.USER,
            content=user_message,
            intent=intent,
        )

        # Update context based on intent
        self._update_context(conversation, intent)

        # Check for escalation triggers
        if self._should_escalate(conversation, intent):
            return await self._escalate_conversation(conversation, intent)

        # Generate response
        response = await self._generate_response(conversation, intent)

        # Add assistant turn
        conversation.add_turn(
            role=MessageRole.ASSISTANT,
            content=response,
        )

        # Check for conversation completion
        if intent.intent_type == IntentType.GOODBYE:
            conversation.state = ConversationState.COMPLETED
            conversation.ended_at = datetime.now(timezone.utc)

        return response

    def _update_context(
        self,
        conversation: Conversation,
        intent: Intent,
    ):
        """Update conversation context based on recognized intent."""
        context = conversation.context

        # Update current topic
        if intent.intent_type != IntentType.UNCLEAR:
            context.current_topic = intent.intent_type.value

        # Store extracted entities
        for key, value in intent.entities.items():
            context.extracted_entities[key] = value

        # Type-specific context updates
        if intent.intent_type == IntentType.BOOK_APPOINTMENT:
            if "dates" in intent.entities:
                context.preferred_dates.extend(intent.entities["dates"])
            if "times" in intent.entities:
                context.preferred_times.extend(intent.entities["times"])

        elif intent.intent_type == IntentType.CHECK_SYMPTOMS:
            # Would extract symptom details here
            pass

    def _should_escalate(
        self,
        conversation: Conversation,
        intent: Intent,
    ) -> bool:
        """Check if conversation should be escalated to human."""
        # Explicit request for human
        if intent.intent_type == IntentType.PROVIDER_CONTACT:
            return True

        # Low confidence repeatedly
        low_confidence_turns = sum(
            1 for turn in conversation.turns[-5:]
            if turn.intent and turn.intent.confidence < 0.4
        )
        if low_confidence_turns >= 3:
            return True

        # Too many turns without resolution
        if conversation.turn_count > 20:
            return True

        return False

    async def _escalate_conversation(
        self,
        conversation: Conversation,
        intent: Intent,
    ) -> str:
        """Escalate conversation to human agent."""
        conversation.state = ConversationState.ESCALATED
        conversation.escalation_reason = (
            f"Intent: {intent.intent_type.value}, "
            f"Confidence: {intent.confidence}"
        )

        logger.info(
            f"Escalating conversation {conversation.conversation_id}: "
            f"{conversation.escalation_reason}"
        )

        return (
            "I understand you'd like to speak with someone directly. "
            "Let me connect you with a member of our team. "
            "Please hold for a moment while I transfer you."
        )

    async def _generate_response(
        self,
        conversation: Conversation,
        intent: Intent,
    ) -> str:
        """Generate response using LLM."""
        # Build system prompt based on conversation type
        system_prompt = self._build_system_prompt(conversation)

        # Build messages
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
        ]

        # Add conversation context as system message
        context_summary = self._summarize_context(conversation)
        if context_summary:
            messages.append(
                ChatMessage(
                    role=MessageRole.SYSTEM,
                    content=f"Conversation context: {context_summary}",
                )
            )

        # Add conversation history
        messages.extend(conversation.get_messages())

        # Get completion
        try:
            completion = await self.llm_service.complete(
                messages=messages,
                temperature=0.7,
                max_tokens=500,
            )
            return completion.message.content
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._get_fallback_response(intent)

    def _build_system_prompt(self, conversation: Conversation) -> str:
        """Build system prompt for the LLM."""
        base_prompt = """You are a helpful healthcare virtual assistant for a medical practice.
You assist patients with scheduling, general questions, and healthcare guidance.

Important guidelines:
- Be empathetic, professional, and concise
- Never provide specific medical diagnoses
- Always recommend consulting a healthcare provider for medical concerns
- Protect patient privacy - never repeat sensitive information
- If unsure, offer to connect with a human representative
"""

        type_prompts = {
            ConversationType.APPOINTMENT_BOOKING: """
You are currently helping the patient schedule an appointment.
Guide them through selecting a date, time, and reason for visit.
Confirm details before finalizing.""",

            ConversationType.SYMPTOM_ASSESSMENT: """
You are helping assess the patient's symptoms.
Ask clarifying questions about symptoms, duration, and severity.
Based on responses, provide urgency guidance:
- EMERGENCY: Life-threatening, recommend calling 911
- URGENT: Needs same-day care
- SOON: Schedule within 24-48 hours
- ROUTINE: Regular appointment
Always err on the side of caution.""",

            ConversationType.MEDICATION_QUESTION: """
You are answering medication questions.
Provide general information about medications.
Always recommend consulting a pharmacist or doctor for specific medical advice.
Do not change or recommend dosages.""",

            ConversationType.BILLING_INQUIRY: """
You are helping with billing questions.
Assist with understanding charges, payment options, and insurance questions.
For specific account issues, offer to connect with billing department.""",
        }

        type_specific = type_prompts.get(conversation.conversation_type, "")
        return base_prompt + type_specific

    def _summarize_context(self, conversation: Conversation) -> str:
        """Summarize conversation context for the LLM."""
        context = conversation.context
        summary_parts = []

        if context.patient_name:
            summary_parts.append(f"Patient: {context.patient_name}")

        if context.current_topic:
            summary_parts.append(f"Topic: {context.current_topic}")

        if context.reported_symptoms:
            symptoms = ", ".join(
                s.get("name", str(s)) for s in context.reported_symptoms
            )
            summary_parts.append(f"Reported symptoms: {symptoms}")

        if context.preferred_dates:
            summary_parts.append(f"Preferred dates: {', '.join(context.preferred_dates)}")

        if context.appointment_reason:
            summary_parts.append(f"Appointment reason: {context.appointment_reason}")

        return "; ".join(summary_parts)

    def _get_fallback_response(self, intent: Intent) -> str:
        """Get fallback response when LLM fails."""
        fallbacks = {
            IntentType.BOOK_APPOINTMENT: (
                "I'd be happy to help you schedule an appointment. "
                "What date and time work best for you?"
            ),
            IntentType.CHECK_SYMPTOMS: (
                "I understand you're not feeling well. "
                "Can you tell me more about your symptoms?"
            ),
            IntentType.GREETING: (
                "Hello! How can I help you today?"
            ),
            IntentType.GOODBYE: (
                "Thank you for contacting us. Take care!"
            ),
        }
        return fallbacks.get(
            intent.intent_type,
            "I'm here to help. Could you please tell me more about what you need?"
        )

    async def get_conversation(
        self,
        conversation_id: str,
    ) -> Optional[Conversation]:
        """Get a conversation by ID."""
        return self._conversations.get(conversation_id)

    async def end_conversation(
        self,
        conversation_id: str,
        reason: str = "user_ended",
        satisfaction_rating: Optional[int] = None,
    ) -> Conversation:
        """End a conversation."""
        conversation = self._conversations.get(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation not found: {conversation_id}")

        conversation.state = ConversationState.COMPLETED
        conversation.ended_at = datetime.now(timezone.utc)
        conversation.satisfaction_rating = satisfaction_rating

        # Add closing message
        closing = "Thank you for chatting with us today. Take care!"
        conversation.add_turn(
            role=MessageRole.ASSISTANT,
            content=closing,
        )

        logger.info(
            f"Ended conversation {conversation_id}, "
            f"turns: {conversation.turn_count}, "
            f"rating: {satisfaction_rating}"
        )

        return conversation

    def register_action_handler(
        self,
        action_name: str,
        handler: Callable,
    ):
        """Register a handler for conversation actions."""
        self._action_handlers[action_name] = handler

    async def execute_action(
        self,
        conversation_id: str,
        action_name: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a conversation action (e.g., create appointment)."""
        handler = self._action_handlers.get(action_name)
        if not handler:
            raise ValueError(f"No handler for action: {action_name}")

        conversation = self._conversations.get(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation not found: {conversation_id}")

        try:
            result = await handler(conversation, params)

            # Record action in context
            conversation.context.pending_actions.append({
                "action": action_name,
                "params": params,
                "result": result,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

            return result
        except Exception as e:
            logger.error(f"Error executing action {action_name}: {e}")
            raise

    def get_conversation_analytics(
        self,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get conversation analytics."""
        conversations = [
            c for c in self._conversations.values()
            if tenant_id is None or c.tenant_id == tenant_id
        ]

        if not conversations:
            return {
                "total_conversations": 0,
                "active": 0,
                "completed": 0,
                "escalated": 0,
            }

        completed = [c for c in conversations if c.state == ConversationState.COMPLETED]
        rated = [c for c in completed if c.satisfaction_rating is not None]

        return {
            "total_conversations": len(conversations),
            "active": sum(1 for c in conversations if c.state == ConversationState.ACTIVE),
            "completed": len(completed),
            "escalated": sum(1 for c in conversations if c.state == ConversationState.ESCALATED),
            "avg_turns": sum(c.turn_count for c in conversations) / len(conversations),
            "avg_satisfaction": (
                sum(c.satisfaction_rating for c in rated) / len(rated)
                if rated else None
            ),
            "by_type": {
                ct.value: sum(1 for c in conversations if c.conversation_type == ct)
                for ct in ConversationType
            },
        }


# Global conversational AI instance
conversational_ai = ConversationalAI()
