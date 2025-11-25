"""
Provider Collaboration Platform - SQLAlchemy Models
EPIC-015: Clinical communication and coordination among healthcare providers
"""
from datetime import datetime, date, time
from typing import Optional, List
from uuid import uuid4
import enum

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Float, DateTime, Date, Time,
    ForeignKey, Enum, BigInteger, Numeric, UniqueConstraint, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from shared.database.connection import Base


def generate_uuid():
    return uuid4()


# ==================== Enums ====================

class ConversationType(str, enum.Enum):
    """Provider conversation types"""
    DIRECT = "direct"
    GROUP = "group"
    CONSULTATION = "consultation"
    CARE_TEAM = "care_team"
    CASE_DISCUSSION = "case_discussion"
    HANDOFF = "handoff"
    ON_CALL = "on_call"
    BROADCAST = "broadcast"


class MessageType(str, enum.Enum):
    """Provider message types"""
    TEXT = "text"
    VOICE = "voice"
    IMAGE = "image"
    DOCUMENT = "document"
    DICOM = "dicom"
    VIDEO = "video"
    SYSTEM = "system"
    ALERT = "alert"


class MessagePriority(str, enum.Enum):
    """Message priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    EMERGENT = "emergent"


class MessageStatus(str, enum.Enum):
    """Message status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    RECALLED = "recalled"


class PresenceStatus(str, enum.Enum):
    """Provider presence status"""
    ONLINE = "online"
    AWAY = "away"
    BUSY = "busy"
    DO_NOT_DISTURB = "do_not_disturb"
    IN_PROCEDURE = "in_procedure"
    ON_CALL = "on_call"
    OFFLINE = "offline"


class ConsultationStatus(str, enum.Enum):
    """Consultation request status"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    IN_PROGRESS = "in_progress"
    AWAITING_RESPONSE = "awaiting_response"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ConsultationUrgency(str, enum.Enum):
    """Consultation urgency levels"""
    ROUTINE = "routine"
    URGENT = "urgent"
    EMERGENT = "emergent"
    STAT = "stat"


class CareTeamRole(str, enum.Enum):
    """Care team member roles"""
    ATTENDING_PHYSICIAN = "attending_physician"
    CONSULTING_PHYSICIAN = "consulting_physician"
    PRIMARY_NURSE = "primary_nurse"
    CHARGE_NURSE = "charge_nurse"
    CARE_COORDINATOR = "care_coordinator"
    CASE_MANAGER = "case_manager"
    SOCIAL_WORKER = "social_worker"
    PHARMACIST = "pharmacist"
    PHYSICAL_THERAPIST = "physical_therapist"
    OCCUPATIONAL_THERAPIST = "occupational_therapist"
    DIETITIAN = "dietitian"
    RESPIRATORY_THERAPIST = "respiratory_therapist"
    RESIDENT = "resident"
    MEDICAL_STUDENT = "medical_student"
    OTHER = "other"


class CareTeamStatus(str, enum.Enum):
    """Care team status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCHARGED = "discharged"
    TRANSFERRED = "transferred"


class HandoffStatus(str, enum.Enum):
    """Shift handoff status"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    INCOMPLETE = "incomplete"


class HandoffType(str, enum.Enum):
    """Type of handoff"""
    SHIFT_CHANGE = "shift_change"
    PATIENT_TRANSFER = "patient_transfer"
    SERVICE_TRANSFER = "service_transfer"
    ESCALATION = "escalation"
    TEMPORARY_COVERAGE = "temporary_coverage"


class OnCallStatus(str, enum.Enum):
    """On-call schedule status"""
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    TRADED = "traded"
    CANCELLED = "cancelled"


class OnCallRequestStatus(str, enum.Enum):
    """On-call request status"""
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    TIMED_OUT = "timed_out"


class AlertType(str, enum.Enum):
    """Clinical alert types"""
    CRITICAL_LAB = "critical_lab"
    VITAL_SIGN = "vital_sign"
    MEDICATION = "medication"
    CLINICAL_DETERIORATION = "clinical_deterioration"
    CARE_GAP = "care_gap"
    TASK_DUE = "task_due"
    CONSULT_RESPONSE = "consult_response"
    HANDOFF_REQUIRED = "handoff_required"
    ON_CALL_REQUEST = "on_call_request"
    SYSTEM = "system"
    CUSTOM = "custom"


class AlertSeverity(str, enum.Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    LIFE_THREATENING = "life_threatening"


class AlertStatus(str, enum.Enum):
    """Alert status"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    SNOOZED = "snoozed"
    RESOLVED = "resolved"
    EXPIRED = "expired"
    ESCALATED = "escalated"


class CaseDiscussionType(str, enum.Enum):
    """Case discussion types"""
    CLINICAL_CASE = "clinical_case"
    TEACHING_CASE = "teaching_case"
    MORBIDITY_MORTALITY = "morbidity_mortality"
    TUMOR_BOARD = "tumor_board"
    PEER_REVIEW = "peer_review"
    GRAND_ROUNDS = "grand_rounds"


class VoteType(str, enum.Enum):
    """Clinical decision vote types"""
    AGREE = "agree"
    DISAGREE = "disagree"
    ABSTAIN = "abstain"
    NEED_MORE_INFO = "need_more_info"


# ==================== Provider Presence ====================

class ProviderPresence(Base):
    """Real-time provider presence and status"""
    __tablename__ = "provider_presence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False, index=True)

    # Status
    status = Column(Enum(PresenceStatus), default=PresenceStatus.OFFLINE)
    status_message = Column(String(255))
    custom_status = Column(String(100))

    # Device info
    device_type = Column(String(50))  # web, mobile, desktop
    device_id = Column(String(255))
    ip_address = Column(INET)
    location = Column(String(100))  # Building, unit, floor

    # Activity
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())
    is_typing_in = Column(UUID(as_uuid=True))  # Conversation ID if typing

    # Availability
    auto_away_enabled = Column(Boolean, default=True)
    auto_away_after_minutes = Column(Integer, default=5)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('tenant_id', 'provider_id', name='uq_provider_presence'),
        Index('ix_provider_presence_status', 'tenant_id', 'status'),
    )


# ==================== Provider Conversations ====================

class ProviderConversation(Base):
    """Conversation threads between providers"""
    __tablename__ = "provider_conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Conversation details
    type = Column(Enum(ConversationType), nullable=False)
    name = Column(String(255))
    description = Column(Text)
    avatar_url = Column(String(500))

    # Patient context (optional)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), index=True)
    encounter_id = Column(UUID(as_uuid=True))

    # Linked entities
    consultation_id = Column(UUID(as_uuid=True))
    care_team_id = Column(UUID(as_uuid=True))
    handoff_id = Column(UUID(as_uuid=True))
    case_discussion_id = Column(UUID(as_uuid=True))

    # Creator
    created_by = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False)

    # Settings
    settings = Column(JSONB, default={})
    is_encrypted = Column(Boolean, default=True)
    message_retention_days = Column(Integer, default=90)
    allow_file_sharing = Column(Boolean, default=True)
    allow_video_calls = Column(Boolean, default=True)
    is_read_only = Column(Boolean, default=False)

    # Status
    is_active = Column(Boolean, default=True)
    is_archived = Column(Boolean, default=False)
    archived_at = Column(DateTime(timezone=True))

    # Activity tracking
    last_message_at = Column(DateTime(timezone=True))
    last_message_preview = Column(String(255))
    message_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    participants = relationship("ConversationParticipant", back_populates="conversation")
    messages = relationship("ProviderMessage", back_populates="conversation")

    __table_args__ = (
        Index('ix_provider_conv_patient', 'tenant_id', 'patient_id'),
        Index('ix_provider_conv_type', 'tenant_id', 'type', 'is_active'),
    )


class ConversationParticipant(Base):
    """Participants in provider conversations"""
    __tablename__ = "conversation_participants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("provider_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False, index=True)

    # Role in conversation
    role = Column(String(50))  # owner, admin, member
    care_team_role = Column(Enum(CareTeamRole))

    # Notification settings
    notifications_enabled = Column(Boolean, default=True)
    notification_sound = Column(String(50), default="default")
    muted_until = Column(DateTime(timezone=True))

    # Read tracking
    last_read_at = Column(DateTime(timezone=True))
    last_read_message_id = Column(UUID(as_uuid=True))
    unread_count = Column(Integer, default=0)

    # Participation
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    left_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)

    # Permissions
    can_add_members = Column(Boolean, default=False)
    can_remove_members = Column(Boolean, default=False)
    can_edit_settings = Column(Boolean, default=False)
    can_delete_messages = Column(Boolean, default=False)

    # Relationship
    conversation = relationship("ProviderConversation", back_populates="participants")

    __table_args__ = (
        UniqueConstraint('conversation_id', 'provider_id', name='uq_conversation_participant'),
    )


# ==================== Provider Messages ====================

class ProviderMessage(Base):
    """Messages in provider conversations"""
    __tablename__ = "provider_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("provider_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False, index=True)

    # Message content
    content = Column(Text)
    content_encrypted = Column(Boolean, default=True)
    message_type = Column(Enum(MessageType), default=MessageType.TEXT)
    priority = Column(Enum(MessagePriority), default=MessagePriority.NORMAL)

    # Attachments
    attachments = Column(JSONB, default=[])  # [{id, name, type, size, url}]
    dicom_references = Column(JSONB)  # For medical imaging

    # Rich content
    formatted_content = Column(Text)  # HTML/Markdown
    mentions = Column(JSONB)  # [{provider_id, start, end}]
    patient_references = Column(JSONB)  # [{patient_id, context}]

    # Threading
    reply_to_id = Column(UUID(as_uuid=True), ForeignKey("provider_messages.id"))
    thread_root_id = Column(UUID(as_uuid=True))
    thread_count = Column(Integer, default=0)

    # Status
    status = Column(Enum(MessageStatus), default=MessageStatus.SENT)
    is_edited = Column(Boolean, default=False)
    edited_at = Column(DateTime(timezone=True))
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True))

    # Recall
    is_recalled = Column(Boolean, default=False)
    recalled_at = Column(DateTime(timezone=True))
    recall_reason = Column(String(255))

    # Scheduling
    scheduled_at = Column(DateTime(timezone=True))
    is_scheduled = Column(Boolean, default=False)

    # Metadata
    metadata = Column(JSONB, default={})
    client_message_id = Column(String(100))  # For deduplication

    # PHI detection
    contains_phi = Column(Boolean, default=False)
    phi_detected_types = Column(ARRAY(String))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    conversation = relationship("ProviderConversation", back_populates="messages")
    receipts = relationship("MessageReceipt", back_populates="message")
    reactions = relationship("MessageReaction", back_populates="message")

    __table_args__ = (
        Index('ix_provider_msg_conv_created', 'conversation_id', 'created_at'),
        Index('ix_provider_msg_thread', 'thread_root_id'),
    )


class MessageReceipt(Base):
    """Message delivery and read receipts"""
    __tablename__ = "message_receipts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    message_id = Column(UUID(as_uuid=True), ForeignKey("provider_messages.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False, index=True)

    # Receipt timestamps
    delivered_at = Column(DateTime(timezone=True))
    read_at = Column(DateTime(timezone=True))

    # Device info
    device_type = Column(String(50))

    # Relationship
    message = relationship("ProviderMessage", back_populates="receipts")

    __table_args__ = (
        UniqueConstraint('message_id', 'provider_id', name='uq_message_receipt'),
    )


class MessageReaction(Base):
    """Reactions to messages"""
    __tablename__ = "message_reactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    message_id = Column(UUID(as_uuid=True), ForeignKey("provider_messages.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False)

    # Reaction
    emoji = Column(String(50), nullable=False)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    message = relationship("ProviderMessage", back_populates="reactions")

    __table_args__ = (
        UniqueConstraint('message_id', 'provider_id', 'emoji', name='uq_message_reaction'),
    )


# ==================== Consultations ====================

class Consultation(Base):
    """Specialist consultation requests"""
    __tablename__ = "consultations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Requesting provider
    requesting_provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False, index=True)
    requesting_service = Column(String(100))
    requesting_department = Column(String(100))

    # Consultant
    consultant_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), index=True)
    consultant_specialty = Column(String(100), nullable=False)
    preferred_consultant_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"))

    # Patient
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    encounter_id = Column(UUID(as_uuid=True))

    # Consultation details
    urgency = Column(Enum(ConsultationUrgency), default=ConsultationUrgency.ROUTINE)
    clinical_question = Column(Text, nullable=False)
    relevant_history = Column(Text)
    working_diagnosis = Column(Text)
    reason_for_consult = Column(Text)

    # Attachments
    attachments = Column(JSONB, default=[])
    lab_references = Column(JSONB)  # [{lab_id, name, value, date}]
    imaging_references = Column(JSONB)  # [{study_id, modality, description, date}]
    medication_list = Column(JSONB)

    # Status workflow
    status = Column(Enum(ConsultationStatus), default=ConsultationStatus.PENDING)
    status_updated_at = Column(DateTime(timezone=True))

    # SLA tracking
    response_deadline = Column(DateTime(timezone=True))
    expected_response_hours = Column(Integer)
    first_response_at = Column(DateTime(timezone=True))
    sla_met = Column(Boolean)

    # Acceptance
    accepted_at = Column(DateTime(timezone=True))
    accepted_by = Column(UUID(as_uuid=True), ForeignKey("providers.id"))
    decline_reason = Column(Text)
    declined_at = Column(DateTime(timezone=True))

    # Completion
    completed_at = Column(DateTime(timezone=True))
    completion_notes = Column(Text)

    # Associated conversation
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("provider_conversations.id"))

    # Report
    has_report = Column(Boolean, default=False)
    report_id = Column(UUID(as_uuid=True))

    # Quality
    quality_rating = Column(Integer)  # 1-5
    quality_feedback = Column(Text)
    rated_by = Column(UUID(as_uuid=True), ForeignKey("providers.id"))
    rated_at = Column(DateTime(timezone=True))

    # Billing
    billing_code = Column(String(20))
    is_billable = Column(Boolean, default=True)
    billed_at = Column(DateTime(timezone=True))

    # CME
    cme_eligible = Column(Boolean, default=False)
    cme_credit_hours = Column(Numeric(4, 2))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    report = relationship("ConsultationReport", back_populates="consultation", uselist=False)

    __table_args__ = (
        Index('ix_consultation_status', 'tenant_id', 'status', 'urgency'),
        Index('ix_consultation_consultant', 'consultant_id', 'status'),
    )


class ConsultationReport(Base):
    """Formal consultation reports"""
    __tablename__ = "consultation_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    consultation_id = Column(UUID(as_uuid=True), ForeignKey("consultations.id"), nullable=False, unique=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Report author
    author_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False)

    # Report content
    impression = Column(Text, nullable=False)
    recommendations = Column(Text, nullable=False)
    assessment = Column(Text)
    plan = Column(Text)
    follow_up_required = Column(Boolean, default=False)
    follow_up_instructions = Column(Text)

    # Diagnoses
    diagnoses = Column(JSONB)  # [{code, system, description}]
    differential_diagnoses = Column(JSONB)

    # Additional tests/procedures recommended
    recommended_tests = Column(JSONB)
    recommended_procedures = Column(JSONB)
    medication_recommendations = Column(JSONB)

    # Status
    is_draft = Column(Boolean, default=True)
    is_signed = Column(Boolean, default=False)
    signed_at = Column(DateTime(timezone=True))
    signed_by = Column(UUID(as_uuid=True), ForeignKey("providers.id"))

    # Addendums
    addendums = Column(JSONB, default=[])

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    consultation = relationship("Consultation", back_populates="report")


# ==================== Care Teams ====================

class CareTeam(Base):
    """Patient care teams"""
    __tablename__ = "care_teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Patient
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    encounter_id = Column(UUID(as_uuid=True))

    # Team details
    name = Column(String(255), nullable=False)
    description = Column(Text)
    team_type = Column(String(50))  # inpatient, outpatient, oncology, cardiology, etc.

    # Lead provider
    lead_provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"))

    # Status
    status = Column(Enum(CareTeamStatus), default=CareTeamStatus.ACTIVE)
    status_updated_at = Column(DateTime(timezone=True))

    # Associated conversation
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("provider_conversations.id"))

    # Care plan
    care_plan = Column(JSONB)
    care_plan_updated_at = Column(DateTime(timezone=True))

    # Goals
    goals = Column(JSONB, default=[])  # [{id, description, target_date, status}]

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    discharged_at = Column(DateTime(timezone=True))

    # Relationships
    members = relationship("CareTeamMember", back_populates="care_team")
    tasks = relationship("CareTeamTask", back_populates="care_team")

    __table_args__ = (
        Index('ix_care_team_patient', 'tenant_id', 'patient_id', 'status'),
    )


class CareTeamMember(Base):
    """Members of care teams"""
    __tablename__ = "care_team_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    care_team_id = Column(UUID(as_uuid=True), ForeignKey("care_teams.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False, index=True)

    # Role
    role = Column(Enum(CareTeamRole), nullable=False)
    custom_role = Column(String(100))
    responsibilities = Column(ARRAY(String))

    # Status
    is_active = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=False)

    # Notifications
    notifications_enabled = Column(Boolean, default=True)
    notify_on_updates = Column(Boolean, default=True)
    notify_on_tasks = Column(Boolean, default=True)

    # Timestamps
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    left_at = Column(DateTime(timezone=True))

    # Relationship
    care_team = relationship("CareTeam", back_populates="members")

    __table_args__ = (
        UniqueConstraint('care_team_id', 'provider_id', name='uq_care_team_member'),
    )


class CareTeamTask(Base):
    """Tasks for care team members"""
    __tablename__ = "care_team_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    care_team_id = Column(UUID(as_uuid=True), ForeignKey("care_teams.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Task details
    title = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(50))  # clinical, administrative, follow-up

    # Assignment
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("providers.id"), index=True)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("providers.id"))
    assigned_role = Column(Enum(CareTeamRole))

    # Priority and timing
    priority = Column(Enum(MessagePriority), default=MessagePriority.NORMAL)
    due_date = Column(DateTime(timezone=True))
    reminder_at = Column(DateTime(timezone=True))

    # Status
    status = Column(String(20), default="pending")  # pending, in_progress, completed, cancelled
    completed_at = Column(DateTime(timezone=True))
    completed_by = Column(UUID(as_uuid=True), ForeignKey("providers.id"))
    completion_notes = Column(Text)

    # Linked entities
    linked_order_id = Column(UUID(as_uuid=True))
    linked_medication_id = Column(UUID(as_uuid=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    care_team = relationship("CareTeam", back_populates="tasks")

    __table_args__ = (
        Index('ix_care_team_task_assigned', 'assigned_to', 'status'),
        Index('ix_care_team_task_due', 'due_date', 'status'),
    )


# ==================== Shift Handoffs ====================

class ShiftHandoff(Base):
    """Shift handoff sessions"""
    __tablename__ = "shift_handoffs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Providers
    outgoing_provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False, index=True)
    incoming_provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False, index=True)

    # Handoff type
    handoff_type = Column(Enum(HandoffType), default=HandoffType.SHIFT_CHANGE)

    # Location/Service
    service = Column(String(100))
    unit = Column(String(100))
    location = Column(String(100))

    # Timing
    shift_date = Column(Date, nullable=False)
    scheduled_time = Column(DateTime(timezone=True))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_minutes = Column(Integer)

    # Status
    status = Column(Enum(HandoffStatus), default=HandoffStatus.SCHEDULED)
    status_updated_at = Column(DateTime(timezone=True))

    # Patient list
    patient_ids = Column(ARRAY(UUID(as_uuid=True)))
    patient_count = Column(Integer, default=0)

    # Conversation for handoff discussion
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("provider_conversations.id"))

    # Recording (optional)
    audio_recording_url = Column(String(500))
    recording_duration_seconds = Column(Integer)
    transcription = Column(Text)

    # Verification
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime(timezone=True))
    signature_outgoing = Column(String(255))  # Digital signature
    signature_incoming = Column(String(255))

    # Quality
    quality_score = Column(Numeric(3, 2))
    feedback = Column(Text)
    incident_reported = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    patient_handoffs = relationship("PatientHandoff", back_populates="shift_handoff")

    __table_args__ = (
        Index('ix_handoff_date', 'tenant_id', 'shift_date', 'service'),
        Index('ix_handoff_outgoing', 'outgoing_provider_id', 'shift_date'),
    )


class PatientHandoff(Base):
    """Individual patient handoff in SBAR format"""
    __tablename__ = "patient_handoffs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    shift_handoff_id = Column(UUID(as_uuid=True), ForeignKey("shift_handoffs.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)

    # SBAR Format
    # Situation
    situation = Column(JSONB)  # {chief_complaint, admission_date, current_status, code_status}

    # Background
    background = Column(JSONB)  # {history, allergies, medications, recent_procedures}

    # Assessment
    assessment = Column(JSONB)  # {vital_signs, labs, imaging, concerns}

    # Recommendations
    recommendations = Column(JSONB)  # {pending_tasks, contingencies, family_updates, estimated_discharge}

    # Critical items
    critical_items = Column(JSONB, default=[])  # [{type, description, priority}]
    has_critical_items = Column(Boolean, default=False)

    # Pending tasks transfer
    pending_tasks = Column(JSONB, default=[])

    # Review status
    reviewed = Column(Boolean, default=False)
    reviewed_at = Column(DateTime(timezone=True))
    questions_raised = Column(JSONB, default=[])
    questions_resolved = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    shift_handoff = relationship("ShiftHandoff", back_populates="patient_handoffs")


# ==================== On-Call Management ====================

class OnCallSchedule(Base):
    """On-call schedule entries"""
    __tablename__ = "on_call_schedule"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Provider
    provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False, index=True)

    # Service/specialty
    service = Column(String(100), nullable=False)
    specialty = Column(String(100))
    department = Column(String(100))

    # Schedule timing
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)

    # Coverage level
    level = Column(Integer, default=1)  # 1=primary, 2=backup, 3=tertiary

    # Backup chain
    backup_providers = Column(ARRAY(UUID(as_uuid=True)))

    # Status
    status = Column(Enum(OnCallStatus), default=OnCallStatus.SCHEDULED)
    status_updated_at = Column(DateTime(timezone=True))

    # Trade tracking
    original_provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"))
    traded_at = Column(DateTime(timezone=True))
    trade_approved_by = Column(UUID(as_uuid=True), ForeignKey("providers.id"))

    # Notes
    notes = Column(Text)

    # Active flag for quick lookup
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('ix_on_call_active', 'tenant_id', 'service', 'start_time', 'end_time'),
        Index('ix_on_call_provider', 'provider_id', 'start_time'),
        CheckConstraint('end_time > start_time', name='check_on_call_time_range'),
    )


class OnCallRequest(Base):
    """Requests to on-call providers"""
    __tablename__ = "on_call_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Service
    service = Column(String(100), nullable=False)

    # Requesting entity
    requested_by = Column(UUID(as_uuid=True), ForeignKey("providers.id"), index=True)
    requested_by_name = Column(String(255))
    requested_by_unit = Column(String(100))
    callback_number = Column(String(20))

    # Patient context
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), index=True)
    patient_name = Column(String(255))
    patient_mrn = Column(String(50))
    patient_location = Column(String(100))

    # Request details
    urgency = Column(Enum(ConsultationUrgency), default=ConsultationUrgency.ROUTINE)
    reason = Column(Text, nullable=False)
    brief_description = Column(String(500))

    # On-call provider
    on_call_provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), index=True)
    schedule_id = Column(UUID(as_uuid=True), ForeignKey("on_call_schedule.id"))

    # Status workflow
    status = Column(Enum(OnCallRequestStatus), default=OnCallRequestStatus.PENDING)
    status_updated_at = Column(DateTime(timezone=True))

    # Response tracking
    acknowledged_at = Column(DateTime(timezone=True))
    response_started_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    resolution_notes = Column(Text)

    # Escalation
    escalation_level = Column(Integer, default=0)
    escalated_to = Column(UUID(as_uuid=True), ForeignKey("providers.id"))
    escalated_at = Column(DateTime(timezone=True))
    escalation_reason = Column(String(255))

    # SLA tracking
    sla_deadline = Column(DateTime(timezone=True))
    sla_met = Column(Boolean)

    # Communication
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("provider_conversations.id"))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('ix_on_call_request_status', 'tenant_id', 'service', 'status'),
    )


# ==================== Clinical Alerts ====================

class ClinicalAlert(Base):
    """Clinical alerts and notifications for providers"""
    __tablename__ = "clinical_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Alert details
    alert_type = Column(Enum(AlertType), nullable=False)
    severity = Column(Enum(AlertSeverity), default=AlertSeverity.INFO)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    # Patient context
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), index=True)
    encounter_id = Column(UUID(as_uuid=True))

    # Clinical data
    clinical_data = Column(JSONB)  # {lab_value, vital_sign, medication, etc.}
    threshold_violated = Column(String(255))
    reference_range = Column(String(100))

    # Linked entity
    source_type = Column(String(50))  # lab_result, vital_sign, order, etc.
    source_id = Column(UUID(as_uuid=True))

    # Recipient
    recipient_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), index=True)
    recipient_role = Column(String(50))
    care_team_id = Column(UUID(as_uuid=True), ForeignKey("care_teams.id"))

    # Status
    status = Column(Enum(AlertStatus), default=AlertStatus.ACTIVE)
    status_updated_at = Column(DateTime(timezone=True))

    # Acknowledgment
    acknowledged_at = Column(DateTime(timezone=True))
    acknowledged_by = Column(UUID(as_uuid=True), ForeignKey("providers.id"))
    acknowledgment_note = Column(Text)

    # Snooze
    snoozed_until = Column(DateTime(timezone=True))
    snooze_count = Column(Integer, default=0)
    max_snooze_count = Column(Integer, default=3)

    # Resolution
    resolved_at = Column(DateTime(timezone=True))
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("providers.id"))
    resolution_note = Column(Text)
    resolution_action = Column(String(100))

    # Escalation
    escalation_time = Column(DateTime(timezone=True))
    escalated = Column(Boolean, default=False)
    escalated_at = Column(DateTime(timezone=True))
    escalated_to = Column(UUID(as_uuid=True), ForeignKey("providers.id"))

    # Delivery
    delivery_channels = Column(ARRAY(String))  # ['in_app', 'sms', 'email', 'push']
    delivered_via = Column(JSONB, default={})  # {channel: timestamp}

    # Expiration
    expires_at = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('ix_clinical_alert_recipient', 'recipient_id', 'status'),
        Index('ix_clinical_alert_patient', 'patient_id', 'status'),
        Index('ix_clinical_alert_severity', 'tenant_id', 'severity', 'status'),
    )


class AlertRule(Base):
    """Custom alert rules configuration"""
    __tablename__ = "alert_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Rule details
    name = Column(String(255), nullable=False)
    description = Column(Text)
    alert_type = Column(Enum(AlertType), nullable=False)
    severity = Column(Enum(AlertSeverity), default=AlertSeverity.WARNING)

    # Trigger conditions
    trigger_conditions = Column(JSONB, nullable=False)  # {field, operator, value}
    trigger_logic = Column(String(10), default="AND")  # AND, OR

    # Scope
    applies_to_all = Column(Boolean, default=True)
    applies_to_services = Column(ARRAY(String))
    applies_to_departments = Column(ARRAY(String))
    patient_criteria = Column(JSONB)  # Additional patient filters

    # Recipients
    default_recipients = Column(ARRAY(UUID(as_uuid=True)))
    notify_care_team = Column(Boolean, default=True)
    notify_attending = Column(Boolean, default=True)
    escalation_path = Column(JSONB)  # [{delay_minutes, recipient_id or role}]

    # Delivery
    delivery_channels = Column(ARRAY(String), default=["in_app"])
    quiet_hours_start = Column(Time)
    quiet_hours_end = Column(Time)
    respect_quiet_hours = Column(Boolean, default=False)

    # Throttling
    throttle_minutes = Column(Integer, default=0)  # Min time between alerts
    max_per_day = Column(Integer)  # Max alerts per day per patient

    # Status
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # System rules can't be deleted

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("providers.id"))


# ==================== Case Discussions ====================

class CaseDiscussion(Base):
    """Clinical case discussions"""
    __tablename__ = "case_discussions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Discussion details
    title = Column(String(255), nullable=False)
    description = Column(Text)
    discussion_type = Column(Enum(CaseDiscussionType), default=CaseDiscussionType.CLINICAL_CASE)

    # Patient context (optional for teaching cases)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), index=True)
    is_anonymized = Column(Boolean, default=False)  # For teaching purposes

    # Presenter
    presenter_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False)
    presenting_service = Column(String(100))

    # Case presentation
    case_presentation = Column(JSONB)  # Structured case data
    presentation_template = Column(String(50))

    # Clinical question
    clinical_question = Column(Text)
    decision_required = Column(Boolean, default=False)

    # Attachments
    attachments = Column(JSONB, default=[])
    references = Column(JSONB, default=[])  # Literature references

    # Associated conversation
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("provider_conversations.id"))

    # Scheduling
    scheduled_at = Column(DateTime(timezone=True))
    duration_minutes = Column(Integer)
    is_recurring = Column(Boolean, default=False)
    recurrence_rule = Column(String(255))  # iCal RRULE format

    # Status
    status = Column(String(20), default="scheduled")  # scheduled, in_progress, completed, cancelled
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # Outcomes
    consensus_reached = Column(Boolean)
    outcome_summary = Column(Text)
    action_items = Column(JSONB, default=[])
    follow_up_date = Column(Date)

    # Educational
    learning_objectives = Column(JSONB, default=[])
    cme_eligible = Column(Boolean, default=False)
    cme_credit_hours = Column(Numeric(4, 2))

    # Visibility
    is_public = Column(Boolean, default=False)  # Visible to all providers
    invited_services = Column(ARRAY(String))
    invited_providers = Column(ARRAY(UUID(as_uuid=True)))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    votes = relationship("CaseDiscussionVote", back_populates="discussion")
    participants = relationship("CaseDiscussionParticipant", back_populates="discussion")


class CaseDiscussionParticipant(Base):
    """Participants in case discussions"""
    __tablename__ = "case_discussion_participants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    discussion_id = Column(UUID(as_uuid=True), ForeignKey("case_discussions.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False, index=True)

    # Role
    role = Column(String(50))  # presenter, moderator, panelist, attendee

    # Attendance
    invited_at = Column(DateTime(timezone=True), server_default=func.now())
    rsvp_status = Column(String(20))  # pending, accepted, declined
    attended = Column(Boolean, default=False)
    joined_at = Column(DateTime(timezone=True))
    left_at = Column(DateTime(timezone=True))

    # Contribution
    contributed = Column(Boolean, default=False)
    contribution_summary = Column(Text)

    # CME
    cme_claimed = Column(Boolean, default=False)
    cme_claimed_at = Column(DateTime(timezone=True))

    # Relationship
    discussion = relationship("CaseDiscussion", back_populates="participants")

    __table_args__ = (
        UniqueConstraint('discussion_id', 'provider_id', name='uq_case_discussion_participant'),
    )


class CaseDiscussionVote(Base):
    """Votes in clinical decisions"""
    __tablename__ = "case_discussion_votes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    discussion_id = Column(UUID(as_uuid=True), ForeignKey("case_discussions.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False)

    # Vote details
    question = Column(String(500))  # The decision question
    vote = Column(Enum(VoteType), nullable=False)
    rationale = Column(Text)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    discussion = relationship("CaseDiscussion", back_populates="votes")


# ==================== Audit Log ====================

class CollaborationAuditLog(Base):
    """Audit log for collaboration activities"""
    __tablename__ = "collaboration_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Actor
    provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), index=True)
    provider_name = Column(String(255))

    # Action
    action = Column(String(100), nullable=False)
    action_category = Column(String(50))  # messaging, consultation, handoff, etc.
    action_description = Column(Text)

    # Target entity
    entity_type = Column(String(50))  # conversation, message, consultation, etc.
    entity_id = Column(UUID(as_uuid=True), index=True)

    # Patient context
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), index=True)

    # Details
    details = Column(JSONB, default={})
    old_values = Column(JSONB)
    new_values = Column(JSONB)

    # Request info
    ip_address = Column(INET)
    user_agent = Column(String(500))
    device_type = Column(String(50))

    # Status
    success = Column(Boolean, default=True)
    error_message = Column(Text)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_collab_audit_action', 'tenant_id', 'action_category', 'created_at'),
        Index('ix_collab_audit_provider', 'provider_id', 'created_at'),
    )
