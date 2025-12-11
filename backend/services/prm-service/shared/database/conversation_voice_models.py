"""
Conversation and Voice Call Models
Database models for WhatsApp conversations and voice agent integration
"""
from datetime import datetime
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


def generate_uuid() -> uuid.UUID:
    """Generate a new UUID4"""
    return uuid.uuid4()


# ============================================================================
# CONVERSATION MANAGEMENT (WhatsApp, SMS, Email, etc.)
# ============================================================================


class Conversation(Base):
    """
    Conversation thread between patient and healthcare provider
    Supports multi-channel communication (WhatsApp, SMS, Email, Voice, WebChat)
    """

    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=True, index=True)

    # Conversation metadata
    subject = Column(String(200))  # Optional subject/title
    status = Column(String(20), nullable=False, default="open", index=True)  # open, pending, snoozed, closed
    priority = Column(String(10), nullable=False, default="p2")  # p0 (critical), p1, p2 (default), p3

    # Channel information
    channel_type = Column(String(20), nullable=False, default="whatsapp", index=True)  # whatsapp, sms, email, phone, webchat, in_person
    external_id = Column(String(255), index=True)  # External system ID (Twilio conversation SID, etc.)

    # Ownership and routing
    current_owner_id = Column(UUID(as_uuid=True), ForeignKey("practitioners.id"), nullable=True)  # Assigned practitioner/agent
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)  # Routed department

    # State management (for conversational AI)
    state_data = Column(JSONB, default=dict)  # Current conversation state (for multi-turn dialogs)
    extracted_data = Column(JSONB, default=dict)  # Data extracted from conversation
    is_intake_complete = Column(Boolean, default=False)  # Whether intake conversation is complete

    # Related entities
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=True)  # If related to appointment
    journey_instance_id = Column(UUID(as_uuid=True), ForeignKey("journey_instances.id"), nullable=True)  # If part of journey

    # Timestamps
    first_message_at = Column(DateTime(timezone=True))  # When conversation started
    last_message_at = Column(DateTime(timezone=True))  # Last activity
    closed_at = Column(DateTime(timezone=True))  # When conversation was closed
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_conversations_patient_status", "patient_id", "status"),
        Index("idx_conversations_channel_status", "channel_type", "status"),
        Index("idx_conversations_owner", "current_owner_id", "status"),
        Index("idx_conversations_last_message", "last_message_at"),
    )


class ConversationMessage(Base):
    """
    Individual message within a conversation thread
    Supports text, media, voice, and file attachments
    """

    __tablename__ = "conversation_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)

    # Message metadata
    direction = Column(String(10), nullable=False)  # inbound (from patient) or outbound (to patient)
    actor_type = Column(String(20), nullable=False)  # patient, related_person, agent (human), bot, system
    actor_id = Column(UUID(as_uuid=True))  # ID of actor (patient_id, practitioner_id, etc.)

    # Content
    content_type = Column(String(20), nullable=False, default="text")  # text, media, voice, file
    text_body = Column(Text)  # Message text content
    media_url = Column(String(512))  # URL to media file (image, video, audio, document)
    media_type = Column(String(100))  # MIME type
    media_size_bytes = Column(Integer)  # File size

    # Message delivery (for outbound messages)
    external_message_id = Column(String(255), index=True)  # External system message ID (Twilio SID, etc.)
    delivery_status = Column(String(20))  # queued, sending, sent, delivered, failed, read
    delivery_error = Column(Text)  # Error message if delivery failed
    delivered_at = Column(DateTime(timezone=True))  # When message was delivered
    read_at = Column(DateTime(timezone=True))  # When message was read (if supported)

    # AI/NLP metadata
    sentiment = Column(String(20))  # positive, neutral, negative, mixed
    intent = Column(String(50))  # Detected intent (book_appointment, ask_question, etc.)
    entities = Column(JSONB, default=dict)  # Named entities extracted
    language = Column(String(10))  # Language code (en, hi, es, etc.)

    # Metadata
    metadata = Column(JSONB, default=dict)  # Additional metadata

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    # Indexes
    __table_args__ = (
        Index("idx_conv_messages_conversation_created", "conversation_id", "created_at"),
        Index("idx_conv_messages_direction", "direction", "created_at"),
        Index("idx_conv_messages_external_id", "external_message_id"),
    )


# ============================================================================
# VOICE CALL MANAGEMENT (Zucol/Zoice Integration)
# ============================================================================


class VoiceCall(Base):
    """
    Voice call record from Zucol/Zoice voice agent platform
    Represents a phone call handled by the AI voice agent
    """

    __tablename__ = "voice_calls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=True, index=True)

    # Call identifiers
    zoice_call_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)  # Zucol/Zoice call ID
    plivo_call_id = Column(String(255), index=True)  # Telephony provider call ID

    # Call participants
    patient_phone = Column(String(20), nullable=False, index=True)  # Patient phone number (E.164)
    agent_phone = Column(String(20))  # Voice agent phone number

    # Call metadata
    call_type = Column(String(20), nullable=False, default="inbound")  # inbound, outbound
    call_status = Column(String(20), nullable=False, default="scheduled", index=True)  # scheduled, in_progress, completed, failed, no_answer

    # Call timing
    scheduled_at = Column(DateTime(timezone=True))  # When call was scheduled (for outbound calls)
    started_at = Column(DateTime(timezone=True), index=True)  # When call started
    ended_at = Column(DateTime(timezone=True))  # When call ended
    duration_seconds = Column(Integer)  # Total call duration

    # Voice agent configuration
    pipeline_id = Column(UUID(as_uuid=True))  # Zucol/Zoice pipeline ID
    agent_name = Column(String(100))  # Name of voice agent

    # Call intent and outcome
    detected_intent = Column(String(50), index=True)  # book_appointment, cancel_appointment, inquiry, emergency, etc.
    call_outcome = Column(String(50))  # appointment_booked, query_answered, transferred, voicemail, etc.
    confidence_score = Column(Float)  # Overall confidence score (0.0 to 1.0)

    # Related entities (created from call)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True)  # Associated conversation thread
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=True)  # Appointment booked during call

    # AI/NLP metadata
    language = Column(String(10))  # Language used in call
    sentiment = Column(String(20))  # Overall call sentiment

    # Call quality metrics
    audio_quality_score = Column(Float)  # Audio quality (0.0 to 1.0)
    transcription_quality_score = Column(Float)  # Transcription confidence

    # Metadata
    metadata = Column(JSONB, default=dict)  # Additional call metadata

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    transcripts = relationship("VoiceCallTranscript", back_populates="call", cascade="all, delete-orphan")
    recordings = relationship("VoiceCallRecording", back_populates="call", cascade="all, delete-orphan")
    extractions = relationship("VoiceCallExtraction", back_populates="call", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_voice_calls_patient_started", "patient_id", "started_at"),
        Index("idx_voice_calls_phone_started", "patient_phone", "started_at"),
        Index("idx_voice_calls_status_started", "call_status", "started_at"),
        Index("idx_voice_calls_intent", "detected_intent"),
    )


class VoiceCallTranscript(Base):
    """
    Transcript of a voice call
    Generated by speech-to-text service
    """

    __tablename__ = "voice_call_transcripts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    call_id = Column(UUID(as_uuid=True), ForeignKey("voice_calls.id"), nullable=False, index=True)

    # Transcript content
    full_transcript = Column(Text, nullable=False)  # Complete call transcript
    turns = Column(JSONB, default=list)  # Turn-by-turn transcript with timestamps [{"speaker": "agent|patient", "text": "...", "timestamp": "..."}]

    # Transcript metadata
    provider = Column(String(50), nullable=False)  # whisper, google_stt, gladia, etc.
    language = Column(String(10))  # Detected/configured language
    confidence_score = Column(Float)  # Overall transcription confidence
    word_count = Column(Integer)  # Number of words

    # Processing metadata
    processing_duration_ms = Column(Integer)  # How long transcription took

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    call = relationship("VoiceCall", back_populates="transcripts")

    # Indexes
    __table_args__ = (
        Index("idx_voice_transcripts_call", "call_id"),
    )


class VoiceCallRecording(Base):
    """
    Audio recording of a voice call
    Storage reference to call audio file
    """

    __tablename__ = "voice_call_recordings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    call_id = Column(UUID(as_uuid=True), ForeignKey("voice_calls.id"), nullable=False, index=True)

    # Recording storage
    recording_url = Column(String(512), nullable=False)  # URL to audio file (S3, CDN, etc.)
    storage_provider = Column(String(50))  # s3, gcs, azure_blob, local, etc.
    storage_path = Column(String(512))  # Path/key in storage system

    # Recording metadata
    format = Column(String(20))  # mp3, wav, ogg, etc.
    codec = Column(String(50))  # Audio codec used
    sample_rate = Column(Integer)  # Sample rate in Hz
    channels = Column(Integer)  # Number of audio channels (1=mono, 2=stereo)
    duration_seconds = Column(Integer)  # Recording duration
    file_size_bytes = Column(Integer)  # File size

    # Quality metadata
    audio_quality = Column(String(20))  # low, medium, high
    bitrate_kbps = Column(Integer)  # Audio bitrate

    # Access control
    is_redacted = Column(Boolean, default=False)  # Whether PHI has been redacted
    retention_expires_at = Column(DateTime(timezone=True))  # When recording should be deleted

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    call = relationship("VoiceCall", back_populates="recordings")

    # Indexes
    __table_args__ = (
        Index("idx_voice_recordings_call", "call_id"),
        Index("idx_voice_recordings_retention", "retention_expires_at"),
    )


class VoiceCallExtraction(Base):
    """
    Structured data extracted from voice call
    Output from AI/NLP processing of transcript
    """

    __tablename__ = "voice_call_extractions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    call_id = Column(UUID(as_uuid=True), ForeignKey("voice_calls.id"), nullable=False, index=True)

    # Extraction metadata
    extraction_type = Column(String(50), nullable=False, index=True)  # appointment_booking, patient_info, complaint, etc.
    pipeline_id = Column(UUID(as_uuid=True))  # Zucol/Zoice pipeline used
    prompt_template = Column(String(100))  # Extraction prompt template name

    # Extracted structured data
    extracted_data = Column(JSONB, nullable=False, default=dict)  # Structured output from extraction
    confidence_scores = Column(JSONB, default=dict)  # Per-field confidence scores

    # Extraction quality
    overall_confidence = Column(Float)  # Overall extraction confidence
    is_validated = Column(Boolean, default=False)  # Whether extraction has been human-validated
    validation_errors = Column(JSONB, default=list)  # Validation issues found

    # Processing metadata
    model_used = Column(String(100))  # AI model used (gpt-4, claude-3, etc.)
    processing_duration_ms = Column(Integer)  # Processing time
    tokens_used = Column(Integer)  # LLM tokens consumed

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    call = relationship("VoiceCall", back_populates="extractions")

    # Indexes
    __table_args__ = (
        Index("idx_voice_extractions_call", "call_id"),
        Index("idx_voice_extractions_type", "extraction_type"),
    )


# ============================================================================
# ANALYTICS AGGREGATION TABLES (Materialized Views for Performance)
# ============================================================================


class AnalyticsAppointmentDaily(Base):
    """
    Daily aggregated appointment metrics
    Pre-computed for fast dashboard loading
    """

    __tablename__ = "analytics_appointment_daily"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Time dimension
    date = Column(Date, nullable=False, index=True)
    hour = Column(Integer)  # Hour of day (0-23) for hourly breakdowns

    # Dimensions
    channel_origin = Column(String(20))  # whatsapp, phone, web, voice_agent, in_person
    practitioner_id = Column(UUID(as_uuid=True), ForeignKey("practitioners.id"))
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"))

    # Metrics
    total_appointments = Column(Integer, default=0)
    scheduled_count = Column(Integer, default=0)
    confirmed_count = Column(Integer, default=0)
    completed_count = Column(Integer, default=0)
    canceled_count = Column(Integer, default=0)
    no_show_count = Column(Integer, default=0)
    rescheduled_count = Column(Integer, default=0)

    # Derived metrics
    no_show_rate = Column(Float)  # Percentage
    completion_rate = Column(Float)  # Percentage
    cancellation_rate = Column(Float)  # Percentage

    # Timestamps
    computed_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index("idx_analytics_appt_tenant_date", "tenant_id", "date"),
        Index("idx_analytics_appt_channel_date", "channel_origin", "date"),
        Index("idx_analytics_appt_practitioner_date", "practitioner_id", "date"),
        Index("idx_analytics_appt_dept_date", "department_id", "date"),
    )


class AnalyticsJourneyDaily(Base):
    """
    Daily aggregated journey metrics
    Pre-computed journey progress analytics
    """

    __tablename__ = "analytics_journey_daily"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Time dimension
    date = Column(Date, nullable=False, index=True)

    # Dimensions
    journey_id = Column(UUID(as_uuid=True), ForeignKey("journeys.id"))
    journey_type = Column(String(50))  # opd, ipd, procedure, chronic_care, wellness
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))

    # Metrics
    total_active_journeys = Column(Integer, default=0)
    completed_journeys = Column(Integer, default=0)
    paused_journeys = Column(Integer, default=0)
    canceled_journeys = Column(Integer, default=0)
    new_journeys_started = Column(Integer, default=0)

    # Progress metrics
    avg_completion_percentage = Column(Float)  # Average % complete
    overdue_steps_count = Column(Integer, default=0)  # Total overdue steps across all journeys

    # Engagement metrics
    total_journey_steps_completed = Column(Integer, default=0)
    avg_steps_per_journey = Column(Float)

    # Timestamps
    computed_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index("idx_analytics_journey_tenant_date", "tenant_id", "date"),
        Index("idx_analytics_journey_type_date", "journey_type", "date"),
        Index("idx_analytics_journey_dept_date", "department_id", "date"),
    )


class AnalyticsCommunicationDaily(Base):
    """
    Daily aggregated communication metrics
    Tracks messages and calls across all channels
    """

    __tablename__ = "analytics_communication_daily"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Time dimension
    date = Column(Date, nullable=False, index=True)
    hour = Column(Integer)  # Hour of day for hourly breakdowns

    # Dimensions
    channel_type = Column(String(20), index=True)  # whatsapp, sms, email, phone, webchat
    direction = Column(String(10))  # inbound, outbound

    # Message metrics
    total_messages = Column(Integer, default=0)
    total_conversations = Column(Integer, default=0)
    new_conversations = Column(Integer, default=0)
    closed_conversations = Column(Integer, default=0)

    # Response metrics
    avg_response_time_seconds = Column(Float)  # Average time to first response
    median_response_time_seconds = Column(Float)
    response_rate_percentage = Column(Float)  # % of messages that got responses

    # Engagement metrics
    avg_messages_per_conversation = Column(Float)
    avg_conversation_duration_hours = Column(Float)

    # Sentiment metrics (for channels with NLP)
    positive_sentiment_count = Column(Integer, default=0)
    neutral_sentiment_count = Column(Integer, default=0)
    negative_sentiment_count = Column(Integer, default=0)

    # Timestamps
    computed_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index("idx_analytics_comm_tenant_date", "tenant_id", "date"),
        Index("idx_analytics_comm_channel_date", "channel_type", "date"),
    )


class AnalyticsVoiceCallDaily(Base):
    """
    Daily aggregated voice call metrics
    Zucol/Zoice voice agent performance analytics
    """

    __tablename__ = "analytics_voice_call_daily"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Time dimension
    date = Column(Date, nullable=False, index=True)
    hour = Column(Integer)  # Hour of day

    # Dimensions
    call_type = Column(String(20))  # inbound, outbound
    detected_intent = Column(String(50))  # book_appointment, inquiry, etc.
    call_outcome = Column(String(50))  # appointment_booked, query_answered, etc.

    # Call volume metrics
    total_calls = Column(Integer, default=0)
    completed_calls = Column(Integer, default=0)
    failed_calls = Column(Integer, default=0)
    no_answer_calls = Column(Integer, default=0)

    # Duration metrics
    avg_call_duration_seconds = Column(Float)
    median_call_duration_seconds = Column(Float)
    total_call_duration_seconds = Column(Integer, default=0)

    # Quality metrics
    avg_audio_quality_score = Column(Float)
    avg_transcription_quality_score = Column(Float)
    avg_confidence_score = Column(Float)

    # Success metrics
    appointment_booked_count = Column(Integer, default=0)
    query_resolved_count = Column(Integer, default=0)
    transferred_to_human_count = Column(Integer, default=0)

    # Success rates
    booking_success_rate = Column(Float)  # % of booking intent calls that succeeded
    query_resolution_rate = Column(Float)  # % of inquiry calls resolved

    # Timestamps
    computed_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index("idx_analytics_voice_tenant_date", "tenant_id", "date"),
        Index("idx_analytics_voice_intent_date", "detected_intent", "date"),
        Index("idx_analytics_voice_outcome_date", "call_outcome", "date"),
    )
