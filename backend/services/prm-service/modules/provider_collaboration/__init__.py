"""
Provider Collaboration Module
EPIC-015: Provider Collaboration Platform

This module provides comprehensive provider collaboration functionality including:
- Real-time messaging with presence tracking
- Specialist consultation management
- Care team coordination
- Shift handoff management (SBAR format)
- On-call schedule and request management
- Clinical alerts and notifications
"""
from .router import router
from .models import (
    # Presence
    ProviderPresence,
    # Messaging
    ProviderConversation, ConversationParticipant, ProviderMessage,
    MessageReceipt, MessageReaction,
    # Consultation
    Consultation, ConsultationReport,
    # Care Team
    CareTeam, CareTeamMember, CareTeamTask,
    # Handoff
    ShiftHandoff, PatientHandoff,
    # On-Call
    OnCallSchedule, OnCallRequest,
    # Alerts
    ClinicalAlert, AlertRule,
    # Case Discussion
    CaseDiscussion, CaseDiscussionParticipant, CaseDiscussionVote,
    # Audit
    CollaborationAuditLog,
    # Enums
    PresenceStatus, ConversationType, MessageType, MessagePriority,
    ConsultationStatus, ConsultationUrgency, CareTeamStatus, CareTeamRole,
    TaskStatus, TaskPriority, HandoffStatus, HandoffType,
    OnCallStatus, OnCallRequestStatus, RequestUrgency,
    AlertPriority, AlertStatus, AlertDeliveryStatus, AlertRuleType,
    DiscussionStatus, VoteType
)
from .services import (
    messaging_service,
    consultation_service,
    care_team_service,
    handoff_service,
    on_call_service,
    alert_service
)

__all__ = [
    # Router
    "router",
    # Models
    "ProviderPresence",
    "ProviderConversation",
    "ConversationParticipant",
    "ProviderMessage",
    "MessageReceipt",
    "MessageReaction",
    "Consultation",
    "ConsultationReport",
    "CareTeam",
    "CareTeamMember",
    "CareTeamTask",
    "ShiftHandoff",
    "PatientHandoff",
    "OnCallSchedule",
    "OnCallRequest",
    "ClinicalAlert",
    "AlertRule",
    "CaseDiscussion",
    "CaseDiscussionParticipant",
    "CaseDiscussionVote",
    "CollaborationAuditLog",
    # Enums
    "PresenceStatus",
    "ConversationType",
    "MessageType",
    "MessagePriority",
    "ConsultationStatus",
    "ConsultationUrgency",
    "CareTeamStatus",
    "CareTeamRole",
    "TaskStatus",
    "TaskPriority",
    "HandoffStatus",
    "HandoffType",
    "OnCallStatus",
    "OnCallRequestStatus",
    "RequestUrgency",
    "AlertPriority",
    "AlertStatus",
    "AlertDeliveryStatus",
    "AlertRuleType",
    "DiscussionStatus",
    "VoteType",
    # Services
    "messaging_service",
    "consultation_service",
    "care_team_service",
    "handoff_service",
    "on_call_service",
    "alert_service"
]
