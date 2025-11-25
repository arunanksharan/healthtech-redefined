"""
Provider Collaboration Services
EPIC-015: Service layer for provider collaboration module
"""
from modules.provider_collaboration.services.messaging_service import MessagingService
from modules.provider_collaboration.services.consultation_service import ConsultationService
from modules.provider_collaboration.services.care_team_service import CareTeamService
from modules.provider_collaboration.services.handoff_service import HandoffService
from modules.provider_collaboration.services.on_call_service import OnCallService
from modules.provider_collaboration.services.alert_service import AlertService

__all__ = [
    "MessagingService",
    "ConsultationService",
    "CareTeamService",
    "HandoffService",
    "OnCallService",
    "AlertService"
]

# Service instances (singleton pattern)
messaging_service = MessagingService()
consultation_service = ConsultationService()
care_team_service = CareTeamService()
handoff_service = HandoffService()
on_call_service = OnCallService()
alert_service = AlertService()
