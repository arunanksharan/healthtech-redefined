"""
Provider Collaboration Platform - Pydantic Schemas
EPIC-015: API request/response schemas for clinical communication and coordination
"""
from datetime import datetime, date, time
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum
from decimal import Decimal

from pydantic import BaseModel, Field, EmailStr, validator


# ==================== Enums for Schemas ====================

class ConversationTypeEnum(str, Enum):
    DIRECT = "direct"
    GROUP = "group"
    CONSULTATION = "consultation"
    CARE_TEAM = "care_team"
    CASE_DISCUSSION = "case_discussion"
    HANDOFF = "handoff"
    ON_CALL = "on_call"
    BROADCAST = "broadcast"


class MessageTypeEnum(str, Enum):
    TEXT = "text"
    VOICE = "voice"
    IMAGE = "image"
    DOCUMENT = "document"
    DICOM = "dicom"
    VIDEO = "video"
    SYSTEM = "system"
    ALERT = "alert"


class MessagePriorityEnum(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    EMERGENT = "emergent"


class MessageStatusEnum(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    RECALLED = "recalled"


class PresenceStatusEnum(str, Enum):
    ONLINE = "online"
    AWAY = "away"
    BUSY = "busy"
    DO_NOT_DISTURB = "do_not_disturb"
    IN_PROCEDURE = "in_procedure"
    ON_CALL = "on_call"
    OFFLINE = "offline"


class ConsultationStatusEnum(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    IN_PROGRESS = "in_progress"
    AWAITING_RESPONSE = "awaiting_response"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ConsultationUrgencyEnum(str, Enum):
    ROUTINE = "routine"
    URGENT = "urgent"
    EMERGENT = "emergent"
    STAT = "stat"


class CareTeamRoleEnum(str, Enum):
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


class CareTeamStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCHARGED = "discharged"
    TRANSFERRED = "transferred"


class HandoffStatusEnum(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    INCOMPLETE = "incomplete"


class HandoffTypeEnum(str, Enum):
    SHIFT_CHANGE = "shift_change"
    PATIENT_TRANSFER = "patient_transfer"
    SERVICE_TRANSFER = "service_transfer"
    ESCALATION = "escalation"
    TEMPORARY_COVERAGE = "temporary_coverage"


class OnCallStatusEnum(str, Enum):
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    TRADED = "traded"
    CANCELLED = "cancelled"


class OnCallRequestStatusEnum(str, Enum):
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    TIMED_OUT = "timed_out"


class AlertTypeEnum(str, Enum):
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


class AlertSeverityEnum(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    LIFE_THREATENING = "life_threatening"


class AlertStatusEnum(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    SNOOZED = "snoozed"
    RESOLVED = "resolved"
    EXPIRED = "expired"
    ESCALATED = "escalated"


class CaseDiscussionTypeEnum(str, Enum):
    CLINICAL_CASE = "clinical_case"
    TEACHING_CASE = "teaching_case"
    MORBIDITY_MORTALITY = "morbidity_mortality"
    TUMOR_BOARD = "tumor_board"
    PEER_REVIEW = "peer_review"
    GRAND_ROUNDS = "grand_rounds"


class VoteTypeEnum(str, Enum):
    AGREE = "agree"
    DISAGREE = "disagree"
    ABSTAIN = "abstain"
    NEED_MORE_INFO = "need_more_info"


# ==================== Presence Schemas ====================

class PresenceUpdate(BaseModel):
    """Update provider presence status"""
    status: PresenceStatusEnum
    status_message: Optional[str] = Field(None, max_length=255)
    custom_status: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=100)


class PresenceResponse(BaseModel):
    """Provider presence information"""
    provider_id: UUID
    status: PresenceStatusEnum
    status_message: Optional[str] = None
    custom_status: Optional[str] = None
    device_type: Optional[str] = None
    location: Optional[str] = None
    last_activity_at: Optional[datetime] = None
    is_typing_in: Optional[UUID] = None

    class Config:
        from_attributes = True


class BulkPresenceRequest(BaseModel):
    """Request presence for multiple providers"""
    provider_ids: List[UUID]


class BulkPresenceResponse(BaseModel):
    """Presence for multiple providers"""
    presence: Dict[str, PresenceResponse]


# ==================== Conversation Schemas ====================

class ConversationCreate(BaseModel):
    """Create a new conversation"""
    type: ConversationTypeEnum
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    patient_id: Optional[UUID] = None
    encounter_id: Optional[UUID] = None
    participant_ids: List[UUID] = Field(..., min_length=1)
    settings: Optional[Dict[str, Any]] = None
    is_encrypted: bool = True
    message_retention_days: int = Field(90, ge=1, le=365)


class ConversationUpdate(BaseModel):
    """Update conversation settings"""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    is_read_only: Optional[bool] = None


class ConversationParticipantAdd(BaseModel):
    """Add participant to conversation"""
    provider_id: UUID
    role: Optional[str] = "member"
    care_team_role: Optional[CareTeamRoleEnum] = None
    can_add_members: bool = False
    can_remove_members: bool = False


class ConversationParticipantUpdate(BaseModel):
    """Update participant settings"""
    notifications_enabled: Optional[bool] = None
    muted_until: Optional[datetime] = None


class ParticipantResponse(BaseModel):
    """Conversation participant info"""
    id: UUID
    provider_id: UUID
    provider_name: Optional[str] = None
    provider_specialty: Optional[str] = None
    avatar_url: Optional[str] = None
    role: Optional[str] = None
    care_team_role: Optional[CareTeamRoleEnum] = None
    is_active: bool
    last_read_at: Optional[datetime] = None
    unread_count: int = 0
    joined_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Conversation details"""
    id: UUID
    type: ConversationTypeEnum
    name: Optional[str] = None
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    patient_id: Optional[UUID] = None
    patient_name: Optional[str] = None
    is_encrypted: bool
    is_active: bool
    is_archived: bool
    last_message_at: Optional[datetime] = None
    last_message_preview: Optional[str] = None
    message_count: int
    unread_count: int = 0
    participants: List[ParticipantResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """List of conversations"""
    conversations: List[ConversationResponse]
    total: int
    page: int
    page_size: int


# ==================== Message Schemas ====================

class MessageAttachment(BaseModel):
    """Message attachment"""
    id: Optional[UUID] = None
    name: str
    type: str
    size: int
    url: Optional[str] = None


class MessageMention(BaseModel):
    """Mention in message"""
    provider_id: UUID
    start: int
    end: int


class MessageCreate(BaseModel):
    """Create a new message"""
    content: Optional[str] = None
    message_type: MessageTypeEnum = MessageTypeEnum.TEXT
    priority: MessagePriorityEnum = MessagePriorityEnum.NORMAL
    attachments: Optional[List[MessageAttachment]] = None
    formatted_content: Optional[str] = None
    mentions: Optional[List[MessageMention]] = None
    reply_to_id: Optional[UUID] = None
    scheduled_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    client_message_id: Optional[str] = Field(None, max_length=100)


class MessageUpdate(BaseModel):
    """Update a message"""
    content: Optional[str] = None
    formatted_content: Optional[str] = None


class MessageRecallRequest(BaseModel):
    """Recall a message"""
    reason: Optional[str] = Field(None, max_length=255)


class MessageReactionCreate(BaseModel):
    """Add reaction to message"""
    emoji: str = Field(..., max_length=50)


class MessageReceiptResponse(BaseModel):
    """Message delivery/read receipt"""
    provider_id: UUID
    provider_name: Optional[str] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MessageReactionResponse(BaseModel):
    """Message reaction"""
    id: UUID
    provider_id: UUID
    provider_name: Optional[str] = None
    emoji: str
    created_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Message details"""
    id: UUID
    conversation_id: UUID
    sender_id: UUID
    sender_name: Optional[str] = None
    sender_avatar: Optional[str] = None
    content: Optional[str] = None
    message_type: MessageTypeEnum
    priority: MessagePriorityEnum
    attachments: Optional[List[MessageAttachment]] = None
    formatted_content: Optional[str] = None
    mentions: Optional[List[MessageMention]] = None
    reply_to_id: Optional[UUID] = None
    thread_root_id: Optional[UUID] = None
    thread_count: int = 0
    status: MessageStatusEnum
    is_edited: bool = False
    is_recalled: bool = False
    contains_phi: bool = False
    receipts: List[MessageReceiptResponse] = []
    reactions: List[MessageReactionResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """List of messages"""
    messages: List[MessageResponse]
    total: int
    has_more: bool


class MessageSearchRequest(BaseModel):
    """Search messages"""
    query: str = Field(..., min_length=2)
    conversation_id: Optional[UUID] = None
    sender_id: Optional[UUID] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    message_type: Optional[MessageTypeEnum] = None
    has_attachments: Optional[bool] = None


# ==================== Consultation Schemas ====================

class ConsultationCreate(BaseModel):
    """Create a consultation request"""
    patient_id: UUID
    consultant_specialty: str = Field(..., max_length=100)
    preferred_consultant_id: Optional[UUID] = None
    urgency: ConsultationUrgencyEnum = ConsultationUrgencyEnum.ROUTINE
    clinical_question: str = Field(..., min_length=10)
    relevant_history: Optional[str] = None
    working_diagnosis: Optional[str] = None
    reason_for_consult: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    lab_references: Optional[List[Dict[str, Any]]] = None
    imaging_references: Optional[List[Dict[str, Any]]] = None
    medication_list: Optional[List[Dict[str, Any]]] = None
    encounter_id: Optional[UUID] = None


class ConsultationAccept(BaseModel):
    """Accept a consultation"""
    estimated_response_hours: Optional[int] = None
    notes: Optional[str] = None


class ConsultationDecline(BaseModel):
    """Decline a consultation"""
    reason: str = Field(..., min_length=10)
    suggest_alternative: Optional[UUID] = None  # Alternative consultant


class ConsultationReportCreate(BaseModel):
    """Create consultation report"""
    impression: str = Field(..., min_length=10)
    recommendations: str = Field(..., min_length=10)
    assessment: Optional[str] = None
    plan: Optional[str] = None
    follow_up_required: bool = False
    follow_up_instructions: Optional[str] = None
    diagnoses: Optional[List[Dict[str, Any]]] = None
    differential_diagnoses: Optional[List[Dict[str, Any]]] = None
    recommended_tests: Optional[List[Dict[str, Any]]] = None
    recommended_procedures: Optional[List[Dict[str, Any]]] = None
    medication_recommendations: Optional[List[Dict[str, Any]]] = None


class ConsultationReportAddendum(BaseModel):
    """Add addendum to report"""
    content: str = Field(..., min_length=10)


class ConsultationQualityRating(BaseModel):
    """Rate consultation quality"""
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = None


class ConsultationReportResponse(BaseModel):
    """Consultation report"""
    id: UUID
    consultation_id: UUID
    author_id: UUID
    author_name: Optional[str] = None
    impression: str
    recommendations: str
    assessment: Optional[str] = None
    plan: Optional[str] = None
    follow_up_required: bool
    follow_up_instructions: Optional[str] = None
    diagnoses: Optional[List[Dict[str, Any]]] = None
    is_draft: bool
    is_signed: bool
    signed_at: Optional[datetime] = None
    addendums: List[Dict[str, Any]] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConsultationResponse(BaseModel):
    """Consultation details"""
    id: UUID
    requesting_provider_id: UUID
    requesting_provider_name: Optional[str] = None
    requesting_service: Optional[str] = None
    consultant_id: Optional[UUID] = None
    consultant_name: Optional[str] = None
    consultant_specialty: str
    patient_id: UUID
    patient_name: Optional[str] = None
    patient_mrn: Optional[str] = None
    urgency: ConsultationUrgencyEnum
    clinical_question: str
    status: ConsultationStatusEnum
    response_deadline: Optional[datetime] = None
    first_response_at: Optional[datetime] = None
    sla_met: Optional[bool] = None
    conversation_id: Optional[UUID] = None
    has_report: bool
    report: Optional[ConsultationReportResponse] = None
    quality_rating: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConsultationListResponse(BaseModel):
    """List of consultations"""
    consultations: List[ConsultationResponse]
    total: int
    page: int
    page_size: int


# ==================== Care Team Schemas ====================

class CareTeamCreate(BaseModel):
    """Create a care team"""
    patient_id: UUID
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    team_type: Optional[str] = Field(None, max_length=50)
    lead_provider_id: Optional[UUID] = None
    encounter_id: Optional[UUID] = None
    members: List["CareTeamMemberCreate"] = []


class CareTeamUpdate(BaseModel):
    """Update care team"""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    lead_provider_id: Optional[UUID] = None
    status: Optional[CareTeamStatusEnum] = None
    care_plan: Optional[Dict[str, Any]] = None


class CareTeamMemberCreate(BaseModel):
    """Add member to care team"""
    provider_id: UUID
    role: CareTeamRoleEnum
    custom_role: Optional[str] = Field(None, max_length=100)
    responsibilities: Optional[List[str]] = None
    is_primary: bool = False


class CareTeamMemberUpdate(BaseModel):
    """Update team member"""
    role: Optional[CareTeamRoleEnum] = None
    custom_role: Optional[str] = None
    responsibilities: Optional[List[str]] = None
    is_primary: Optional[bool] = None
    notifications_enabled: Optional[bool] = None


class CareTeamGoal(BaseModel):
    """Care team goal"""
    id: Optional[UUID] = None
    description: str
    target_date: Optional[date] = None
    status: str = "active"


class CareTeamGoalUpdate(BaseModel):
    """Update care team goals"""
    goals: List[CareTeamGoal]


class CareTeamTaskCreate(BaseModel):
    """Create care team task"""
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    assigned_to: Optional[UUID] = None
    assigned_role: Optional[CareTeamRoleEnum] = None
    priority: MessagePriorityEnum = MessagePriorityEnum.NORMAL
    due_date: Optional[datetime] = None
    reminder_at: Optional[datetime] = None


class CareTeamTaskUpdate(BaseModel):
    """Update care team task"""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    assigned_to: Optional[UUID] = None
    priority: Optional[MessagePriorityEnum] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = None
    completion_notes: Optional[str] = None


class CareTeamMemberResponse(BaseModel):
    """Care team member info"""
    id: UUID
    provider_id: UUID
    provider_name: Optional[str] = None
    provider_specialty: Optional[str] = None
    avatar_url: Optional[str] = None
    role: CareTeamRoleEnum
    custom_role: Optional[str] = None
    responsibilities: Optional[List[str]] = None
    is_active: bool
    is_primary: bool
    joined_at: datetime

    class Config:
        from_attributes = True


class CareTeamTaskResponse(BaseModel):
    """Care team task"""
    id: UUID
    care_team_id: UUID
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    assigned_to: Optional[UUID] = None
    assigned_to_name: Optional[str] = None
    assigned_by: Optional[UUID] = None
    priority: MessagePriorityEnum
    due_date: Optional[datetime] = None
    status: str
    completed_at: Optional[datetime] = None
    completed_by_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CareTeamResponse(BaseModel):
    """Care team details"""
    id: UUID
    patient_id: UUID
    patient_name: Optional[str] = None
    name: str
    description: Optional[str] = None
    team_type: Optional[str] = None
    lead_provider_id: Optional[UUID] = None
    lead_provider_name: Optional[str] = None
    status: CareTeamStatusEnum
    conversation_id: Optional[UUID] = None
    care_plan: Optional[Dict[str, Any]] = None
    goals: List[CareTeamGoal] = []
    members: List[CareTeamMemberResponse] = []
    pending_tasks_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CareTeamListResponse(BaseModel):
    """List of care teams"""
    care_teams: List[CareTeamResponse]
    total: int
    page: int
    page_size: int


# ==================== Handoff Schemas ====================

class HandoffCreate(BaseModel):
    """Create a shift handoff"""
    incoming_provider_id: UUID
    handoff_type: HandoffTypeEnum = HandoffTypeEnum.SHIFT_CHANGE
    service: Optional[str] = Field(None, max_length=100)
    unit: Optional[str] = Field(None, max_length=100)
    shift_date: date
    scheduled_time: Optional[datetime] = None
    patient_ids: List[UUID] = []


class PatientHandoffSBAR(BaseModel):
    """SBAR format patient handoff"""
    situation: Dict[str, Any]  # {chief_complaint, admission_date, current_status, code_status}
    background: Dict[str, Any]  # {history, allergies, medications, recent_procedures}
    assessment: Dict[str, Any]  # {vital_signs, labs, imaging, concerns}
    recommendations: Dict[str, Any]  # {pending_tasks, contingencies, family_updates}
    critical_items: Optional[List[Dict[str, Any]]] = None


class PatientHandoffUpdate(BaseModel):
    """Update patient handoff"""
    situation: Optional[Dict[str, Any]] = None
    background: Optional[Dict[str, Any]] = None
    assessment: Optional[Dict[str, Any]] = None
    recommendations: Optional[Dict[str, Any]] = None
    critical_items: Optional[List[Dict[str, Any]]] = None


class HandoffAcknowledge(BaseModel):
    """Acknowledge handoff"""
    signature: Optional[str] = Field(None, max_length=255)
    feedback: Optional[str] = None


class HandoffQuestion(BaseModel):
    """Raise question about handoff"""
    patient_id: UUID
    question: str
    priority: MessagePriorityEnum = MessagePriorityEnum.NORMAL


class PatientHandoffResponse(BaseModel):
    """Patient handoff details"""
    id: UUID
    patient_id: UUID
    patient_name: Optional[str] = None
    patient_mrn: Optional[str] = None
    patient_location: Optional[str] = None
    situation: Optional[Dict[str, Any]] = None
    background: Optional[Dict[str, Any]] = None
    assessment: Optional[Dict[str, Any]] = None
    recommendations: Optional[Dict[str, Any]] = None
    critical_items: List[Dict[str, Any]] = []
    has_critical_items: bool
    pending_tasks: List[Dict[str, Any]] = []
    reviewed: bool
    questions_raised: List[Dict[str, Any]] = []
    questions_resolved: bool

    class Config:
        from_attributes = True


class HandoffResponse(BaseModel):
    """Shift handoff details"""
    id: UUID
    outgoing_provider_id: UUID
    outgoing_provider_name: Optional[str] = None
    incoming_provider_id: UUID
    incoming_provider_name: Optional[str] = None
    handoff_type: HandoffTypeEnum
    service: Optional[str] = None
    unit: Optional[str] = None
    shift_date: date
    scheduled_time: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    status: HandoffStatusEnum
    patient_count: int
    patient_handoffs: List[PatientHandoffResponse] = []
    conversation_id: Optional[UUID] = None
    acknowledged: bool
    quality_score: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class HandoffListResponse(BaseModel):
    """List of handoffs"""
    handoffs: List[HandoffResponse]
    total: int
    page: int
    page_size: int


# ==================== On-Call Schemas ====================

class OnCallScheduleCreate(BaseModel):
    """Create on-call schedule entry"""
    provider_id: UUID
    service: str = Field(..., max_length=100)
    specialty: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    start_time: datetime
    end_time: datetime
    level: int = Field(1, ge=1, le=3)
    backup_providers: Optional[List[UUID]] = None
    notes: Optional[str] = None


class OnCallScheduleUpdate(BaseModel):
    """Update on-call schedule"""
    provider_id: Optional[UUID] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    level: Optional[int] = Field(None, ge=1, le=3)
    backup_providers: Optional[List[UUID]] = None
    notes: Optional[str] = None


class OnCallTradeRequest(BaseModel):
    """Request to trade on-call shift"""
    new_provider_id: UUID
    reason: Optional[str] = None


class OnCallRequestCreate(BaseModel):
    """Create on-call request"""
    service: str = Field(..., max_length=100)
    patient_id: Optional[UUID] = None
    urgency: ConsultationUrgencyEnum = ConsultationUrgencyEnum.ROUTINE
    reason: str
    brief_description: Optional[str] = Field(None, max_length=500)
    callback_number: Optional[str] = Field(None, max_length=20)


class OnCallRequestAcknowledge(BaseModel):
    """Acknowledge on-call request"""
    notes: Optional[str] = None


class OnCallRequestResolve(BaseModel):
    """Resolve on-call request"""
    resolution_notes: str


class OnCallScheduleResponse(BaseModel):
    """On-call schedule entry"""
    id: UUID
    provider_id: UUID
    provider_name: Optional[str] = None
    provider_specialty: Optional[str] = None
    service: str
    specialty: Optional[str] = None
    department: Optional[str] = None
    start_time: datetime
    end_time: datetime
    level: int
    backup_providers: Optional[List[UUID]] = None
    status: OnCallStatusEnum
    is_active: bool
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class OnCallRequestResponse(BaseModel):
    """On-call request details"""
    id: UUID
    service: str
    requested_by: Optional[UUID] = None
    requested_by_name: Optional[str] = None
    patient_id: Optional[UUID] = None
    patient_name: Optional[str] = None
    patient_location: Optional[str] = None
    urgency: ConsultationUrgencyEnum
    reason: str
    brief_description: Optional[str] = None
    on_call_provider_id: Optional[UUID] = None
    on_call_provider_name: Optional[str] = None
    status: OnCallRequestStatusEnum
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    escalation_level: int
    sla_deadline: Optional[datetime] = None
    sla_met: Optional[bool] = None
    created_at: datetime

    class Config:
        from_attributes = True


class OnCallScheduleListResponse(BaseModel):
    """List of on-call schedules"""
    schedules: List[OnCallScheduleResponse]
    total: int


class OnCallRequestListResponse(BaseModel):
    """List of on-call requests"""
    requests: List[OnCallRequestResponse]
    total: int
    page: int
    page_size: int


class CurrentOnCallResponse(BaseModel):
    """Current on-call provider for a service"""
    service: str
    provider_id: UUID
    provider_name: str
    provider_phone: Optional[str] = None
    schedule_id: UUID
    start_time: datetime
    end_time: datetime
    backup_providers: List[Dict[str, Any]] = []


# ==================== Alert Schemas ====================

class AlertCreate(BaseModel):
    """Create a clinical alert (manual)"""
    alert_type: AlertTypeEnum
    severity: AlertSeverityEnum = AlertSeverityEnum.INFO
    title: str = Field(..., max_length=255)
    message: str
    patient_id: Optional[UUID] = None
    recipient_id: Optional[UUID] = None
    care_team_id: Optional[UUID] = None
    clinical_data: Optional[Dict[str, Any]] = None
    delivery_channels: List[str] = ["in_app"]
    expires_at: Optional[datetime] = None


class AlertAcknowledge(BaseModel):
    """Acknowledge an alert"""
    note: Optional[str] = None


class AlertSnooze(BaseModel):
    """Snooze an alert"""
    snooze_until: datetime


class AlertResolve(BaseModel):
    """Resolve an alert"""
    resolution_note: Optional[str] = None
    resolution_action: Optional[str] = Field(None, max_length=100)


class AlertRuleCreate(BaseModel):
    """Create alert rule"""
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    alert_type: AlertTypeEnum
    severity: AlertSeverityEnum = AlertSeverityEnum.WARNING
    trigger_conditions: Dict[str, Any]
    trigger_logic: str = Field("AND", pattern="^(AND|OR)$")
    applies_to_all: bool = True
    applies_to_services: Optional[List[str]] = None
    applies_to_departments: Optional[List[str]] = None
    notify_care_team: bool = True
    notify_attending: bool = True
    delivery_channels: List[str] = ["in_app"]
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None
    respect_quiet_hours: bool = False
    throttle_minutes: int = 0
    max_per_day: Optional[int] = None


class AlertRuleUpdate(BaseModel):
    """Update alert rule"""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    severity: Optional[AlertSeverityEnum] = None
    trigger_conditions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    delivery_channels: Optional[List[str]] = None


class AlertResponse(BaseModel):
    """Clinical alert"""
    id: UUID
    alert_type: AlertTypeEnum
    severity: AlertSeverityEnum
    title: str
    message: str
    patient_id: Optional[UUID] = None
    patient_name: Optional[str] = None
    clinical_data: Optional[Dict[str, Any]] = None
    threshold_violated: Optional[str] = None
    status: AlertStatusEnum
    acknowledged_at: Optional[datetime] = None
    acknowledged_by_name: Optional[str] = None
    snoozed_until: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolved_by_name: Optional[str] = None
    escalated: bool
    delivery_channels: Optional[List[str]] = None
    expires_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AlertRuleResponse(BaseModel):
    """Alert rule"""
    id: UUID
    name: str
    description: Optional[str] = None
    alert_type: AlertTypeEnum
    severity: AlertSeverityEnum
    trigger_conditions: Dict[str, Any]
    trigger_logic: str
    applies_to_all: bool
    is_active: bool
    is_system: bool
    delivery_channels: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    """List of alerts"""
    alerts: List[AlertResponse]
    total: int
    page: int
    page_size: int


class AlertRuleListResponse(BaseModel):
    """List of alert rules"""
    rules: List[AlertRuleResponse]
    total: int


# ==================== Case Discussion Schemas ====================

class CaseDiscussionCreate(BaseModel):
    """Create case discussion"""
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    discussion_type: CaseDiscussionTypeEnum = CaseDiscussionTypeEnum.CLINICAL_CASE
    patient_id: Optional[UUID] = None
    is_anonymized: bool = False
    clinical_question: Optional[str] = None
    decision_required: bool = False
    case_presentation: Optional[Dict[str, Any]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    references: Optional[List[Dict[str, Any]]] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    invited_services: Optional[List[str]] = None
    invited_providers: Optional[List[UUID]] = None
    is_public: bool = False
    learning_objectives: Optional[List[str]] = None
    cme_eligible: bool = False


class CaseDiscussionUpdate(BaseModel):
    """Update case discussion"""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    clinical_question: Optional[str] = None
    case_presentation: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None
    status: Optional[str] = None
    outcome_summary: Optional[str] = None
    action_items: Optional[List[Dict[str, Any]]] = None


class CaseDiscussionVoteCreate(BaseModel):
    """Vote in case discussion"""
    question: Optional[str] = Field(None, max_length=500)
    vote: VoteTypeEnum
    rationale: Optional[str] = None


class CaseDiscussionParticipantRSVP(BaseModel):
    """RSVP to case discussion"""
    rsvp_status: str = Field(..., pattern="^(accepted|declined|tentative)$")


class CaseDiscussionParticipantResponse(BaseModel):
    """Case discussion participant"""
    id: UUID
    provider_id: UUID
    provider_name: Optional[str] = None
    provider_specialty: Optional[str] = None
    role: Optional[str] = None
    rsvp_status: Optional[str] = None
    attended: bool
    contributed: bool

    class Config:
        from_attributes = True


class CaseDiscussionVoteResponse(BaseModel):
    """Case discussion vote"""
    id: UUID
    provider_id: UUID
    provider_name: Optional[str] = None
    question: Optional[str] = None
    vote: VoteTypeEnum
    rationale: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CaseDiscussionResponse(BaseModel):
    """Case discussion details"""
    id: UUID
    title: str
    description: Optional[str] = None
    discussion_type: CaseDiscussionTypeEnum
    patient_id: Optional[UUID] = None
    patient_name: Optional[str] = None
    is_anonymized: bool
    presenter_id: UUID
    presenter_name: Optional[str] = None
    clinical_question: Optional[str] = None
    decision_required: bool
    case_presentation: Optional[Dict[str, Any]] = None
    attachments: List[Dict[str, Any]] = []
    references: List[Dict[str, Any]] = []
    conversation_id: Optional[UUID] = None
    scheduled_at: Optional[datetime] = None
    status: str
    consensus_reached: Optional[bool] = None
    outcome_summary: Optional[str] = None
    action_items: List[Dict[str, Any]] = []
    participants: List[CaseDiscussionParticipantResponse] = []
    votes: List[CaseDiscussionVoteResponse] = []
    learning_objectives: List[str] = []
    cme_eligible: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CaseDiscussionListResponse(BaseModel):
    """List of case discussions"""
    discussions: List[CaseDiscussionResponse]
    total: int
    page: int
    page_size: int


# ==================== Analytics Schemas ====================

class CollaborationStats(BaseModel):
    """Collaboration statistics"""
    total_messages: int
    messages_today: int
    active_conversations: int
    pending_consultations: int
    average_response_time_minutes: Optional[float] = None
    handoffs_completed_today: int
    active_alerts: int
    care_teams_active: int


class ProviderActivityStats(BaseModel):
    """Provider activity statistics"""
    provider_id: UUID
    provider_name: str
    messages_sent: int
    messages_received: int
    consultations_requested: int
    consultations_completed: int
    average_response_time_minutes: Optional[float] = None
    handoffs_given: int
    handoffs_received: int
    alerts_acknowledged: int


# Update forward references
CareTeamCreate.model_rebuild()
