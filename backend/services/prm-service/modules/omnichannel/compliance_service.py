"""
Compliance Service
HIPAA compliance, audit logging, and PHI protection for omnichannel communications
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from uuid import UUID
import hashlib
import json
import re
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from cryptography.fernet import Fernet
import base64

from .models import (
    OmnichannelMessage,
    OmnichannelConversation,
    CommunicationAuditLog,
    OmniChannelType,
)


class ComplianceService:
    """
    HIPAA compliance and audit logging for omnichannel communications.

    Features:
    - PHI detection and masking
    - Message encryption at rest
    - Comprehensive audit logging
    - Access control verification
    - Data retention management
    - Compliance reporting
    """

    # Common PHI patterns
    PHI_PATTERNS = {
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'mrn': r'\bMRN[:\s]*\d{6,}\b',
        'dob': r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
        'credit_card': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
    }

    # HIPAA-defined PHI identifiers
    HIPAA_IDENTIFIERS = [
        'name', 'address', 'dates', 'phone', 'fax', 'email',
        'ssn', 'mrn', 'health_plan', 'account_number', 'license',
        'vehicle_id', 'device_serial', 'url', 'ip_address',
        'biometric', 'photo', 'other_unique'
    ]

    def __init__(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        encryption_key: Optional[str] = None
    ):
        self.db = db
        self.tenant_id = tenant_id

        # Initialize encryption
        if encryption_key:
            self.cipher = Fernet(encryption_key.encode())
        else:
            # Generate a key for development (in production, use secure key management)
            self.cipher = None
            logger.warning("No encryption key provided - PHI encryption disabled")

    async def log_audit_event(
        self,
        event_type: str,
        resource_type: str,
        resource_id: UUID,
        action: str,
        actor_id: Optional[UUID] = None,
        actor_type: str = 'user',
        patient_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        phi_accessed: bool = False
    ) -> CommunicationAuditLog:
        """
        Log an audit event for HIPAA compliance.

        Args:
            event_type: Type of event (access, create, update, delete, send, etc.)
            resource_type: Type of resource (message, conversation, preference, etc.)
            resource_id: Resource UUID
            action: Specific action taken
            actor_id: Who performed the action
            actor_type: Type of actor (user, system, api)
            patient_id: Related patient if applicable
            details: Additional event details
            ip_address: Source IP
            user_agent: Client user agent
            phi_accessed: Whether PHI was accessed

        Returns:
            Created audit log entry
        """
        audit_log = CommunicationAuditLog(
            tenant_id=self.tenant_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            actor_id=actor_id,
            actor_type=actor_type,
            patient_id=patient_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            phi_accessed=phi_accessed,
            timestamp=datetime.utcnow()
        )

        self.db.add(audit_log)
        await self.db.flush()

        if phi_accessed:
            logger.info(
                f"HIPAA Audit: PHI accessed - {event_type} on {resource_type} "
                f"by {actor_type}:{actor_id}"
            )

        return audit_log

    async def log_message_sent(
        self,
        message: OmnichannelMessage,
        actor_id: Optional[UUID] = None,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Log message sent event.

        Args:
            message: The sent message
            actor_id: Who initiated the send
            ip_address: Source IP
        """
        await self.log_audit_event(
            event_type='send',
            resource_type='message',
            resource_id=message.id,
            action='message_sent',
            actor_id=actor_id,
            patient_id=message.patient_id,
            details={
                'channel': message.channel.value if message.channel else None,
                'direction': message.direction,
                'content_hash': self._hash_content(message.content or ''),
                'has_attachments': bool(message.attachments)
            },
            ip_address=ip_address,
            phi_accessed=True  # Messages may contain PHI
        )

    async def log_message_read(
        self,
        message_id: UUID,
        patient_id: UUID,
        reader_id: UUID,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Log message read/viewed event.

        Args:
            message_id: Message UUID
            patient_id: Patient UUID
            reader_id: Who read the message
            ip_address: Source IP
        """
        await self.log_audit_event(
            event_type='access',
            resource_type='message',
            resource_id=message_id,
            action='message_read',
            actor_id=reader_id,
            patient_id=patient_id,
            ip_address=ip_address,
            phi_accessed=True
        )

    async def log_conversation_access(
        self,
        conversation_id: UUID,
        patient_id: UUID,
        accessor_id: UUID,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Log conversation access event.

        Args:
            conversation_id: Conversation UUID
            patient_id: Patient UUID
            accessor_id: Who accessed
            ip_address: Source IP
        """
        await self.log_audit_event(
            event_type='access',
            resource_type='conversation',
            resource_id=conversation_id,
            action='conversation_viewed',
            actor_id=accessor_id,
            patient_id=patient_id,
            ip_address=ip_address,
            phi_accessed=True
        )

    def detect_phi(self, content: str) -> Dict[str, List[str]]:
        """
        Detect potential PHI in content.

        Args:
            content: Text content to scan

        Returns:
            Dictionary of PHI types and matches found
        """
        if not content:
            return {}

        detected = {}

        for phi_type, pattern in self.PHI_PATTERNS.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                detected[phi_type] = matches

        return detected

    def mask_phi(self, content: str) -> str:
        """
        Mask PHI in content for safe logging/display.

        Args:
            content: Text content to mask

        Returns:
            Masked content
        """
        if not content:
            return content

        masked = content

        # Mask SSN: XXX-XX-1234
        masked = re.sub(
            self.PHI_PATTERNS['ssn'],
            lambda m: 'XXX-XX-' + m.group()[-4:],
            masked
        )

        # Mask phone: XXX-XXX-1234
        masked = re.sub(
            self.PHI_PATTERNS['phone'],
            lambda m: 'XXX-XXX-' + ''.join(c for c in m.group() if c.isdigit())[-4:],
            masked
        )

        # Mask email: a***@domain.com
        def mask_email(match):
            email = match.group()
            local, domain = email.split('@')
            return local[0] + '***@' + domain

        masked = re.sub(self.PHI_PATTERNS['email'], mask_email, masked)

        # Mask credit card: XXXX-XXXX-XXXX-1234
        masked = re.sub(
            self.PHI_PATTERNS['credit_card'],
            lambda m: 'XXXX-XXXX-XXXX-' + ''.join(c for c in m.group() if c.isdigit())[-4:],
            masked
        )

        return masked

    def encrypt_content(self, content: str) -> str:
        """
        Encrypt content for storage.

        Args:
            content: Plain text content

        Returns:
            Encrypted content (base64 encoded)
        """
        if not content:
            return content

        if not self.cipher:
            logger.warning("Encryption not configured - storing unencrypted")
            return content

        encrypted = self.cipher.encrypt(content.encode())
        return base64.b64encode(encrypted).decode()

    def decrypt_content(self, encrypted_content: str) -> str:
        """
        Decrypt stored content.

        Args:
            encrypted_content: Base64 encoded encrypted content

        Returns:
            Decrypted plain text
        """
        if not encrypted_content:
            return encrypted_content

        if not self.cipher:
            return encrypted_content  # Return as-is if not encrypted

        try:
            decoded = base64.b64decode(encrypted_content.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return encrypted_content  # Return as-is on failure

    def _hash_content(self, content: str) -> str:
        """Create SHA-256 hash of content for audit logging."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    async def verify_access_authorization(
        self,
        actor_id: UUID,
        patient_id: UUID,
        resource_type: str,
        action: str
    ) -> bool:
        """
        Verify actor is authorized to access patient data.

        Args:
            actor_id: Who is requesting access
            patient_id: Patient being accessed
            resource_type: Type of resource
            action: Action being performed

        Returns:
            True if authorized
        """
        # In production, this would check:
        # 1. Actor's role and permissions
        # 2. Care team membership
        # 3. Break-the-glass override
        # 4. Active consent
        # For now, return True (implement actual checks based on your auth system)

        logger.debug(
            f"Access check: {actor_id} accessing {resource_type} for {patient_id}"
        )

        return True

    async def get_audit_trail(
        self,
        resource_type: Optional[str] = None,
        resource_id: Optional[UUID] = None,
        patient_id: Optional[UUID] = None,
        actor_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[CommunicationAuditLog]:
        """
        Get audit trail with filters.

        Args:
            resource_type: Filter by resource type
            resource_id: Filter by specific resource
            patient_id: Filter by patient
            actor_id: Filter by actor
            start_date: Start of date range
            end_date: End of date range
            limit: Max results
            offset: Pagination offset

        Returns:
            List of audit log entries
        """
        query = select(CommunicationAuditLog).where(
            CommunicationAuditLog.tenant_id == self.tenant_id
        )

        if resource_type:
            query = query.where(CommunicationAuditLog.resource_type == resource_type)
        if resource_id:
            query = query.where(CommunicationAuditLog.resource_id == resource_id)
        if patient_id:
            query = query.where(CommunicationAuditLog.patient_id == patient_id)
        if actor_id:
            query = query.where(CommunicationAuditLog.actor_id == actor_id)
        if start_date:
            query = query.where(CommunicationAuditLog.timestamp >= start_date)
        if end_date:
            query = query.where(CommunicationAuditLog.timestamp <= end_date)

        query = query.order_by(desc(CommunicationAuditLog.timestamp))
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Generate HIPAA compliance report.

        Args:
            start_date: Report start date
            end_date: Report end date

        Returns:
            Compliance report data
        """
        # Total PHI access events
        result = await self.db.execute(
            select(func.count(CommunicationAuditLog.id))
            .where(
                and_(
                    CommunicationAuditLog.tenant_id == self.tenant_id,
                    CommunicationAuditLog.phi_accessed == True,
                    CommunicationAuditLog.timestamp >= start_date,
                    CommunicationAuditLog.timestamp <= end_date
                )
            )
        )
        phi_access_count = result.scalar() or 0

        # Events by type
        result = await self.db.execute(
            select(
                CommunicationAuditLog.event_type,
                func.count(CommunicationAuditLog.id).label('count')
            )
            .where(
                and_(
                    CommunicationAuditLog.tenant_id == self.tenant_id,
                    CommunicationAuditLog.timestamp >= start_date,
                    CommunicationAuditLog.timestamp <= end_date
                )
            )
            .group_by(CommunicationAuditLog.event_type)
        )
        events_by_type = {row.event_type: row.count for row in result}

        # Unique patients accessed
        result = await self.db.execute(
            select(func.count(func.distinct(CommunicationAuditLog.patient_id)))
            .where(
                and_(
                    CommunicationAuditLog.tenant_id == self.tenant_id,
                    CommunicationAuditLog.patient_id.isnot(None),
                    CommunicationAuditLog.timestamp >= start_date,
                    CommunicationAuditLog.timestamp <= end_date
                )
            )
        )
        unique_patients = result.scalar() or 0

        # Unique actors
        result = await self.db.execute(
            select(func.count(func.distinct(CommunicationAuditLog.actor_id)))
            .where(
                and_(
                    CommunicationAuditLog.tenant_id == self.tenant_id,
                    CommunicationAuditLog.actor_id.isnot(None),
                    CommunicationAuditLog.timestamp >= start_date,
                    CommunicationAuditLog.timestamp <= end_date
                )
            )
        )
        unique_actors = result.scalar() or 0

        return {
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_phi_access_events": phi_access_count,
                "unique_patients_accessed": unique_patients,
                "unique_actors": unique_actors
            },
            "events_by_type": events_by_type,
            "compliance_status": "compliant"  # Would have actual checks in production
        }

    async def apply_retention_policy(
        self,
        retention_days: int = 2555  # 7 years for HIPAA
    ) -> Dict[str, int]:
        """
        Apply data retention policy.

        Args:
            retention_days: Days to retain data

        Returns:
            Count of records affected
        """
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        # Archive old messages
        # In production, this would archive to cold storage before deletion
        result = await self.db.execute(
            select(func.count(OmnichannelMessage.id))
            .where(
                and_(
                    OmnichannelMessage.tenant_id == self.tenant_id,
                    OmnichannelMessage.created_at < cutoff_date
                )
            )
        )
        messages_to_archive = result.scalar() or 0

        # Archive old conversations
        result = await self.db.execute(
            select(func.count(OmnichannelConversation.id))
            .where(
                and_(
                    OmnichannelConversation.tenant_id == self.tenant_id,
                    OmnichannelConversation.started_at < cutoff_date
                )
            )
        )
        conversations_to_archive = result.scalar() or 0

        logger.info(
            f"Retention policy: {messages_to_archive} messages and "
            f"{conversations_to_archive} conversations eligible for archival"
        )

        return {
            "messages_eligible": messages_to_archive,
            "conversations_eligible": conversations_to_archive,
            "retention_days": retention_days,
            "cutoff_date": cutoff_date.isoformat()
        }

    async def validate_message_compliance(
        self,
        content: str,
        channel: OmniChannelType
    ) -> Dict[str, Any]:
        """
        Validate message content for compliance.

        Args:
            content: Message content
            channel: Target channel

        Returns:
            Validation result
        """
        issues = []
        warnings = []

        # Check for exposed PHI
        phi_detected = self.detect_phi(content)
        if phi_detected:
            warnings.append({
                "type": "phi_detected",
                "message": f"Potential PHI detected: {list(phi_detected.keys())}",
                "phi_types": list(phi_detected.keys())
            })

        # Check message length for SMS
        if channel == OmniChannelType.SMS and len(content) > 1600:
            issues.append({
                "type": "length_exceeded",
                "message": "SMS content exceeds 1600 character limit"
            })

        # Check for required disclosures
        if channel in [OmniChannelType.SMS, OmniChannelType.EMAIL]:
            if 'opt-out' not in content.lower() and 'unsubscribe' not in content.lower():
                warnings.append({
                    "type": "missing_opt_out",
                    "message": "Consider adding opt-out instructions for regulatory compliance"
                })

        return {
            "compliant": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "phi_detected": phi_detected
        }
