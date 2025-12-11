"""
Referral Management System

Comprehensive referral workflow including:
- Referral creation and tracking
- Provider network directory
- Authorization management
- Bidirectional communication
- Appointment coordination

EPIC-006: US-006.4 Referral Management System
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class ReferralStatus(str, Enum):
    """Referral workflow status."""
    DRAFT = "draft"
    PENDING_AUTH = "pending_authorization"
    AUTHORIZED = "authorized"
    SENT = "sent"
    RECEIVED = "received"
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DENIED = "denied"
    EXPIRED = "expired"


class ReferralPriority(str, Enum):
    """Referral urgency levels."""
    ROUTINE = "routine"
    URGENT = "urgent"
    EMERGENT = "emergent"
    STAT = "stat"


class ReferralType(str, Enum):
    """Types of referrals."""
    CONSULTATION = "consultation"
    PROCEDURE = "procedure"
    DIAGNOSTIC = "diagnostic"
    THERAPY = "therapy"
    SECOND_OPINION = "second_opinion"
    TRANSFER = "transfer"


@dataclass
class ProviderSpecialty:
    """Provider specialty information."""
    specialty_code: str
    specialty_name: str
    board_certified: bool = False
    subspecialties: List[str] = field(default_factory=list)


@dataclass
class ReferralProvider:
    """Provider in the referral network."""
    provider_id: str
    npi: str
    name: str
    organization: Optional[str] = None
    specialties: List[ProviderSpecialty] = field(default_factory=list)

    address: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None

    accepting_new_patients: bool = True
    in_network: bool = True
    average_wait_days: Optional[int] = None

    languages: List[str] = field(default_factory=list)
    telehealth_available: bool = False


@dataclass
class ReferralAuthorization:
    """Insurance authorization for referral."""
    auth_id: str
    referral_id: str

    insurance_id: str
    auth_number: Optional[str] = None

    status: str = "pending"  # pending, approved, denied, expired
    requested_visits: int = 1
    approved_visits: int = 0

    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

    denial_reason: Optional[str] = None
    notes: Optional[str] = None

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reviewed_at: Optional[datetime] = None


@dataclass
class ReferralDocument:
    """Document attached to a referral."""
    document_id: str
    referral_id: str
    document_type: str  # clinical_notes, lab_results, imaging, consent
    file_name: str
    mime_type: str
    storage_url: str
    uploaded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ReferralMessage:
    """Communication message between referring and receiving providers."""
    message_id: str
    referral_id: str
    sender_id: str
    sender_type: str  # referring_provider, receiving_provider, coordinator
    content: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    read_at: Optional[datetime] = None


@dataclass
class Referral:
    """Patient referral to another provider/specialist."""
    referral_id: str
    tenant_id: str

    # Patient and encounter
    patient_id: str
    encounter_id: Optional[str] = None

    # Referring provider
    referring_provider_id: str
    referring_organization_id: Optional[str] = None

    # Receiving provider
    receiving_provider_id: Optional[str] = None
    receiving_organization_id: Optional[str] = None
    target_specialty: Optional[str] = None

    # Referral details
    referral_type: ReferralType = ReferralType.CONSULTATION
    priority: ReferralPriority = ReferralPriority.ROUTINE
    reason: str = ""
    clinical_question: str = ""

    # Diagnosis and procedures
    diagnosis_codes: List[str] = field(default_factory=list)
    procedure_codes: List[str] = field(default_factory=list)

    # Authorization
    requires_authorization: bool = False
    authorization: Optional[ReferralAuthorization] = None

    # Scheduling
    preferred_date_start: Optional[datetime] = None
    preferred_date_end: Optional[datetime] = None
    scheduled_appointment_id: Optional[str] = None
    scheduled_datetime: Optional[datetime] = None

    # Status tracking
    status: ReferralStatus = ReferralStatus.DRAFT
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    sent_at: Optional[datetime] = None
    received_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Documents and notes
    documents: List[ReferralDocument] = field(default_factory=list)
    messages: List[ReferralMessage] = field(default_factory=list)

    # Response
    consultation_notes: Optional[str] = None
    recommendations: Optional[str] = None
    follow_up_needed: bool = False


class ProviderDirectory:
    """
    Provider network directory for referrals.

    Supports:
    - Provider search by specialty, location, availability
    - Network status checking
    - Provider ratings and quality metrics
    """

    def __init__(self):
        self._providers: Dict[str, ReferralProvider] = {}
        self._specialty_index: Dict[str, List[str]] = {}

    def add_provider(self, provider: ReferralProvider):
        """Add a provider to the directory."""
        self._providers[provider.provider_id] = provider

        for specialty in provider.specialties:
            if specialty.specialty_code not in self._specialty_index:
                self._specialty_index[specialty.specialty_code] = []
            self._specialty_index[specialty.specialty_code].append(provider.provider_id)

    def get_provider(self, provider_id: str) -> Optional[ReferralProvider]:
        """Get provider by ID."""
        return self._providers.get(provider_id)

    def search_providers(
        self,
        specialty_code: Optional[str] = None,
        in_network_only: bool = True,
        accepting_new_patients: bool = True,
        telehealth: Optional[bool] = None,
        language: Optional[str] = None,
        max_wait_days: Optional[int] = None,
    ) -> List[ReferralProvider]:
        """Search for providers matching criteria."""
        results = []

        # Start with specialty filter if provided
        if specialty_code and specialty_code in self._specialty_index:
            provider_ids = self._specialty_index[specialty_code]
        else:
            provider_ids = list(self._providers.keys())

        for pid in provider_ids:
            provider = self._providers[pid]

            # Apply filters
            if in_network_only and not provider.in_network:
                continue
            if accepting_new_patients and not provider.accepting_new_patients:
                continue
            if telehealth is not None and provider.telehealth_available != telehealth:
                continue
            if language and language.lower() not in [l.lower() for l in provider.languages]:
                continue
            if max_wait_days and provider.average_wait_days and provider.average_wait_days > max_wait_days:
                continue

            results.append(provider)

        # Sort by wait time (providers with shorter wait times first)
        results.sort(key=lambda p: p.average_wait_days or 999)

        return results


class ReferralService:
    """
    Referral management service.

    Handles:
    - Referral creation and submission
    - Authorization tracking
    - Provider communication
    - Appointment coordination
    - Status tracking
    """

    def __init__(self):
        self.provider_directory = ProviderDirectory()

    async def create_referral(
        self,
        tenant_id: str,
        patient_id: str,
        referring_provider_id: str,
        target_specialty: str,
        referral_type: ReferralType = ReferralType.CONSULTATION,
        priority: ReferralPriority = ReferralPriority.ROUTINE,
        reason: str = "",
        clinical_question: str = "",
        diagnosis_codes: Optional[List[str]] = None,
        receiving_provider_id: Optional[str] = None,
        encounter_id: Optional[str] = None,
    ) -> Referral:
        """Create a new referral."""
        referral = Referral(
            referral_id=str(uuid4()),
            tenant_id=tenant_id,
            patient_id=patient_id,
            referring_provider_id=referring_provider_id,
            target_specialty=target_specialty,
            referral_type=referral_type,
            priority=priority,
            reason=reason,
            clinical_question=clinical_question,
            diagnosis_codes=diagnosis_codes or [],
            receiving_provider_id=receiving_provider_id,
            encounter_id=encounter_id,
        )

        logger.info(f"Created referral: {referral.referral_id}")
        return referral

    async def check_authorization_required(
        self,
        referral: Referral,
        insurance_id: str,
    ) -> bool:
        """Check if referral requires prior authorization."""
        # Would check against payer rules
        # For now, return True for procedures and out-of-network
        if referral.referral_type == ReferralType.PROCEDURE:
            return True

        if referral.receiving_provider_id:
            provider = self.provider_directory.get_provider(referral.receiving_provider_id)
            if provider and not provider.in_network:
                return True

        return False

    async def request_authorization(
        self,
        referral: Referral,
        insurance_id: str,
        requested_visits: int = 1,
        notes: Optional[str] = None,
    ) -> ReferralAuthorization:
        """Request prior authorization for referral."""
        auth = ReferralAuthorization(
            auth_id=str(uuid4()),
            referral_id=referral.referral_id,
            insurance_id=insurance_id,
            requested_visits=requested_visits,
            notes=notes,
        )

        referral.authorization = auth
        referral.requires_authorization = True
        referral.status = ReferralStatus.PENDING_AUTH

        logger.info(f"Requested authorization for referral: {referral.referral_id}")
        return auth

    async def submit_referral(
        self,
        referral: Referral,
    ) -> Referral:
        """Submit referral to receiving provider."""
        # Check if authorization is needed and approved
        if referral.requires_authorization:
            if not referral.authorization or referral.authorization.status != "approved":
                raise ValueError("Referral requires approved authorization")

        referral.status = ReferralStatus.SENT
        referral.sent_at = datetime.now(timezone.utc)

        logger.info(f"Submitted referral: {referral.referral_id}")
        return referral

    async def receive_referral(
        self,
        referral: Referral,
    ) -> Referral:
        """Mark referral as received by receiving provider."""
        referral.status = ReferralStatus.RECEIVED
        referral.received_at = datetime.now(timezone.utc)
        return referral

    async def attach_document(
        self,
        referral: Referral,
        document_type: str,
        file_name: str,
        mime_type: str,
        storage_url: str,
    ) -> ReferralDocument:
        """Attach a document to the referral."""
        doc = ReferralDocument(
            document_id=str(uuid4()),
            referral_id=referral.referral_id,
            document_type=document_type,
            file_name=file_name,
            mime_type=mime_type,
            storage_url=storage_url,
        )
        referral.documents.append(doc)
        return doc

    async def send_message(
        self,
        referral: Referral,
        sender_id: str,
        sender_type: str,
        content: str,
    ) -> ReferralMessage:
        """Send a message between providers."""
        message = ReferralMessage(
            message_id=str(uuid4()),
            referral_id=referral.referral_id,
            sender_id=sender_id,
            sender_type=sender_type,
            content=content,
        )
        referral.messages.append(message)
        return message

    async def schedule_appointment(
        self,
        referral: Referral,
        appointment_id: str,
        scheduled_datetime: datetime,
    ) -> Referral:
        """Link scheduled appointment to referral."""
        referral.scheduled_appointment_id = appointment_id
        referral.scheduled_datetime = scheduled_datetime
        referral.status = ReferralStatus.SCHEDULED
        return referral

    async def complete_referral(
        self,
        referral: Referral,
        consultation_notes: str,
        recommendations: Optional[str] = None,
        follow_up_needed: bool = False,
    ) -> Referral:
        """Complete the referral with consultation notes."""
        referral.consultation_notes = consultation_notes
        referral.recommendations = recommendations
        referral.follow_up_needed = follow_up_needed
        referral.status = ReferralStatus.COMPLETED
        referral.completed_at = datetime.now(timezone.utc)

        logger.info(f"Completed referral: {referral.referral_id}")
        return referral

    async def get_patient_referrals(
        self,
        tenant_id: str,
        patient_id: str,
        status: Optional[ReferralStatus] = None,
        limit: int = 50,
    ) -> List[Referral]:
        """Get referrals for a patient."""
        # Would query database
        return []

    async def get_provider_referrals(
        self,
        tenant_id: str,
        provider_id: str,
        direction: str = "outgoing",  # outgoing, incoming
        status: Optional[ReferralStatus] = None,
        limit: int = 50,
    ) -> List[Referral]:
        """Get referrals for a provider."""
        # Would query database
        return []

    async def search_specialists(
        self,
        specialty_code: str,
        in_network_only: bool = True,
        accepting_new_patients: bool = True,
        telehealth: Optional[bool] = None,
        language: Optional[str] = None,
    ) -> List[ReferralProvider]:
        """Search for specialists to refer to."""
        return self.provider_directory.search_providers(
            specialty_code=specialty_code,
            in_network_only=in_network_only,
            accepting_new_patients=accepting_new_patients,
            telehealth=telehealth,
            language=language,
        )
