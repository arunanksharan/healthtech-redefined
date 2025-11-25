"""
PHI Protection Service

HIPAA-compliant PHI (Protected Health Information) handling:
- PHI detection and identification
- De-identification for AI processing
- Re-identification for results
- Data masking
- Audit logging
- Consent verification

EPIC-009: US-009.8 HIPAA-Compliant AI Processing
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import re
import hashlib
import logging

logger = logging.getLogger(__name__)


class PHIType(str, Enum):
    """Types of Protected Health Information."""
    # Direct identifiers
    NAME = "name"
    DATE_OF_BIRTH = "date_of_birth"
    SSN = "ssn"
    MRN = "mrn"  # Medical Record Number
    PHONE = "phone"
    EMAIL = "email"
    ADDRESS = "address"
    ZIP_CODE = "zip_code"

    # Other identifiers
    ACCOUNT_NUMBER = "account_number"
    LICENSE_NUMBER = "license_number"
    VEHICLE_ID = "vehicle_id"
    DEVICE_ID = "device_id"
    IP_ADDRESS = "ip_address"
    URL = "url"
    BIOMETRIC = "biometric"
    PHOTO = "photo"

    # Medical identifiers
    INSURANCE_ID = "insurance_id"
    PRESCRIPTION_NUMBER = "prescription_number"


class MaskingStrategy(str, Enum):
    """Strategies for masking PHI."""
    REDACT = "redact"  # Replace with [REDACTED]
    PSEUDONYMIZE = "pseudonymize"  # Replace with consistent fake data
    HASH = "hash"  # Replace with hash
    GENERALIZE = "generalize"  # e.g., exact age -> age range
    SUPPRESS = "suppress"  # Remove entirely


@dataclass
class PHIEntity:
    """A detected PHI entity in text."""
    entity_id: str
    phi_type: PHIType
    original_text: str
    start_offset: int
    end_offset: int
    confidence: float = 0.9
    masked_text: Optional[str] = None


@dataclass
class DeidentificationResult:
    """Result of de-identification process."""
    result_id: str
    original_text: str
    deidentified_text: str

    # Detected PHI
    phi_entities: List[PHIEntity] = field(default_factory=list)

    # Mapping for re-identification
    token_mapping: Dict[str, str] = field(default_factory=dict)
    # Maps masked tokens to original values

    # Metadata
    phi_count: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    processing_time_ms: float = 0


@dataclass
class PHIAuditLog:
    """Audit log entry for PHI access."""
    audit_id: str
    timestamp: datetime
    tenant_id: str

    # Action
    action: str  # detect, deidentify, reidentify, access
    resource_type: str  # text, document, record
    resource_id: Optional[str] = None

    # Actor
    user_id: Optional[str] = None
    service_name: Optional[str] = None

    # Details
    phi_types_detected: List[str] = field(default_factory=list)
    phi_count: int = 0
    reason: Optional[str] = None

    # Consent
    consent_verified: bool = False
    consent_id: Optional[str] = None


@dataclass
class ConsentRecord:
    """Patient consent record for data processing."""
    consent_id: str
    patient_id: str
    tenant_id: str

    # Consent details
    purpose: str  # ai_processing, research, analytics
    granted: bool = True
    granted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None

    # Scope
    allowed_phi_types: List[PHIType] = field(default_factory=list)
    allowed_uses: List[str] = field(default_factory=list)

    # Revocation
    revoked: bool = False
    revoked_at: Optional[datetime] = None


class PHIProtectionService:
    """
    PHI Protection Service for HIPAA-compliant AI processing.

    Provides:
    - PHI detection in text
    - De-identification for safe AI processing
    - Re-identification when needed
    - Audit logging
    - Consent verification
    """

    def __init__(
        self,
        default_strategy: MaskingStrategy = MaskingStrategy.PSEUDONYMIZE,
        strict_mode: bool = True,
    ):
        self.default_strategy = default_strategy
        self.strict_mode = strict_mode  # Fail if PHI detected without consent

        # PHI detection patterns
        self._patterns = self._build_detection_patterns()

        # Pseudonymization counters for consistent replacement
        self._pseudonym_counters: Dict[PHIType, int] = {t: 0 for t in PHIType}

        # Token mappings for re-identification
        self._token_mappings: Dict[str, Dict[str, str]] = {}

        # Audit logs
        self._audit_logs: List[PHIAuditLog] = []

        # Consent records
        self._consent_records: Dict[str, ConsentRecord] = {}

    def _build_detection_patterns(self) -> Dict[PHIType, List[re.Pattern]]:
        """Build regex patterns for PHI detection."""
        return {
            PHIType.SSN: [
                re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
                re.compile(r'\b\d{9}\b'),  # SSN without dashes
            ],
            PHIType.PHONE: [
                re.compile(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'),
                re.compile(r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}'),
                re.compile(r'\+1[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'),
            ],
            PHIType.EMAIL: [
                re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            ],
            PHIType.DATE_OF_BIRTH: [
                re.compile(r'\b(?:DOB|D\.O\.B\.?|Date of Birth)[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b', re.IGNORECASE),
                re.compile(r'\bborn\s+(?:on\s+)?(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b', re.IGNORECASE),
            ],
            PHIType.MRN: [
                re.compile(r'\b(?:MRN|Medical Record|Patient ID)[:\s#]*([A-Z0-9]{6,12})\b', re.IGNORECASE),
            ],
            PHIType.ZIP_CODE: [
                re.compile(r'\b\d{5}(?:-\d{4})?\b'),
            ],
            PHIType.IP_ADDRESS: [
                re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),
            ],
            PHIType.ADDRESS: [
                re.compile(r'\b\d{1,5}\s+(?:[A-Za-z]+\s*){1,4}(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Way|Place|Pl)\b', re.IGNORECASE),
            ],
            PHIType.INSURANCE_ID: [
                re.compile(r'\b(?:Insurance ID|Member ID|Policy)[:\s#]*([A-Z0-9]{8,15})\b', re.IGNORECASE),
            ],
            PHIType.ACCOUNT_NUMBER: [
                re.compile(r'\b(?:Account|Acct)[:\s#]*(\d{8,16})\b', re.IGNORECASE),
            ],
            PHIType.NAME: [
                # Names are harder to detect - use context clues
                re.compile(r'(?:Patient|Mr\.|Mrs\.|Ms\.|Dr\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b'),
                re.compile(r'\bName[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b', re.IGNORECASE),
            ],
        }

    async def detect_phi(
        self,
        text: str,
        phi_types: Optional[List[PHIType]] = None,
    ) -> List[PHIEntity]:
        """
        Detect PHI in text.

        Args:
            text: Text to analyze
            phi_types: Specific PHI types to detect (all if None)

        Returns:
            List of detected PHI entities
        """
        phi_types = phi_types or list(PHIType)
        entities = []

        for phi_type in phi_types:
            if phi_type not in self._patterns:
                continue

            for pattern in self._patterns[phi_type]:
                for match in pattern.finditer(text):
                    # Get the actual matched group (handle groups)
                    if match.groups():
                        matched_text = match.group(1)
                        start = match.start(1)
                        end = match.end(1)
                    else:
                        matched_text = match.group(0)
                        start = match.start()
                        end = match.end()

                    # Check for overlapping entities
                    overlapping = any(
                        e.start_offset < end and e.end_offset > start
                        for e in entities
                    )

                    if not overlapping:
                        entities.append(PHIEntity(
                            entity_id=str(uuid4()),
                            phi_type=phi_type,
                            original_text=matched_text,
                            start_offset=start,
                            end_offset=end,
                        ))

        # Sort by position
        entities.sort(key=lambda e: e.start_offset)

        logger.debug(f"Detected {len(entities)} PHI entities in text")
        return entities

    async def deidentify(
        self,
        text: str,
        tenant_id: str,
        strategy: Optional[MaskingStrategy] = None,
        phi_types: Optional[List[PHIType]] = None,
        preserve_format: bool = True,
        user_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> DeidentificationResult:
        """
        De-identify text by masking PHI.

        Args:
            text: Text to de-identify
            tenant_id: Tenant identifier
            strategy: Masking strategy to use
            phi_types: Specific PHI types to mask
            preserve_format: Preserve text format/structure
            user_id: User performing de-identification
            reason: Reason for de-identification

        Returns:
            DeidentificationResult with masked text and mapping
        """
        start_time = datetime.now(timezone.utc)
        strategy = strategy or self.default_strategy

        # Detect PHI
        entities = await self.detect_phi(text, phi_types)

        # Generate result ID for re-identification
        result_id = str(uuid4())
        token_mapping: Dict[str, str] = {}

        # Apply masking from end to start to preserve offsets
        deidentified_text = text
        for entity in reversed(entities):
            masked_text = self._mask_entity(entity, strategy, preserve_format)
            entity.masked_text = masked_text

            # Store mapping for re-identification
            token_mapping[masked_text] = entity.original_text

            # Replace in text
            deidentified_text = (
                deidentified_text[:entity.start_offset] +
                masked_text +
                deidentified_text[entity.end_offset:]
            )

        # Store mapping for later re-identification
        self._token_mappings[result_id] = token_mapping

        # Calculate processing time
        processing_time = (
            datetime.now(timezone.utc) - start_time
        ).total_seconds() * 1000

        result = DeidentificationResult(
            result_id=result_id,
            original_text=text,
            deidentified_text=deidentified_text,
            phi_entities=entities,
            token_mapping=token_mapping,
            phi_count=len(entities),
            processing_time_ms=processing_time,
        )

        # Audit log
        await self._log_audit(
            tenant_id=tenant_id,
            action="deidentify",
            resource_type="text",
            resource_id=result_id,
            user_id=user_id,
            phi_types_detected=[e.phi_type.value for e in entities],
            phi_count=len(entities),
            reason=reason,
        )

        logger.info(
            f"De-identified text: {len(entities)} PHI entities masked, "
            f"result_id: {result_id}"
        )

        return result

    def _mask_entity(
        self,
        entity: PHIEntity,
        strategy: MaskingStrategy,
        preserve_format: bool,
    ) -> str:
        """Apply masking strategy to a PHI entity."""
        if strategy == MaskingStrategy.REDACT:
            return f"[{entity.phi_type.value.upper()}]"

        elif strategy == MaskingStrategy.HASH:
            hash_value = hashlib.sha256(entity.original_text.encode()).hexdigest()[:8]
            return f"[HASH:{hash_value}]"

        elif strategy == MaskingStrategy.SUPPRESS:
            return ""

        elif strategy == MaskingStrategy.PSEUDONYMIZE:
            return self._generate_pseudonym(entity, preserve_format)

        elif strategy == MaskingStrategy.GENERALIZE:
            return self._generalize_value(entity)

        return f"[{entity.phi_type.value.upper()}]"

    def _generate_pseudonym(
        self,
        entity: PHIEntity,
        preserve_format: bool,
    ) -> str:
        """Generate a consistent pseudonym for PHI."""
        self._pseudonym_counters[entity.phi_type] += 1
        counter = self._pseudonym_counters[entity.phi_type]

        if entity.phi_type == PHIType.NAME:
            # Generate fake name
            fake_first_names = ["John", "Jane", "Michael", "Sarah", "David", "Emily"]
            fake_last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Davis"]
            return f"{fake_first_names[counter % len(fake_first_names)]} {fake_last_names[counter % len(fake_last_names)]}"

        elif entity.phi_type == PHIType.SSN:
            if preserve_format:
                return f"XXX-XX-{counter:04d}"
            return f"XXX-XX-{counter:04d}"

        elif entity.phi_type == PHIType.PHONE:
            if preserve_format:
                return f"(555) 000-{counter:04d}"
            return f"555-000-{counter:04d}"

        elif entity.phi_type == PHIType.EMAIL:
            return f"patient{counter}@example.com"

        elif entity.phi_type == PHIType.DATE_OF_BIRTH:
            return "[DOB-REDACTED]"

        elif entity.phi_type == PHIType.MRN:
            return f"MRN{counter:08d}"

        elif entity.phi_type == PHIType.ZIP_CODE:
            # Generalize to first 3 digits
            if len(entity.original_text) >= 3:
                return entity.original_text[:3] + "XX"
            return "XXXXX"

        elif entity.phi_type == PHIType.ADDRESS:
            return f"[ADDRESS-{counter}]"

        elif entity.phi_type == PHIType.IP_ADDRESS:
            return "XXX.XXX.XXX.XXX"

        elif entity.phi_type == PHIType.INSURANCE_ID:
            return f"INS{counter:010d}"

        elif entity.phi_type == PHIType.ACCOUNT_NUMBER:
            return f"ACCT{counter:012d}"

        return f"[{entity.phi_type.value.upper()}-{counter}]"

    def _generalize_value(self, entity: PHIEntity) -> str:
        """Generalize PHI value (e.g., age range instead of exact age)."""
        if entity.phi_type == PHIType.ZIP_CODE:
            # Keep only first 3 digits
            if len(entity.original_text) >= 3:
                return entity.original_text[:3] + "00"

        elif entity.phi_type == PHIType.DATE_OF_BIRTH:
            # Convert to age range if possible
            return "[AGE RANGE]"

        return f"[{entity.phi_type.value.upper()}-GENERALIZED]"

    async def reidentify(
        self,
        result_id: str,
        text: str,
        tenant_id: str,
        user_id: Optional[str] = None,
        reason: Optional[str] = None,
        consent_verified: bool = False,
    ) -> str:
        """
        Re-identify text using stored token mapping.

        Args:
            result_id: Result ID from de-identification
            text: De-identified text to restore
            tenant_id: Tenant identifier
            user_id: User requesting re-identification
            reason: Reason for re-identification
            consent_verified: Whether consent was verified

        Returns:
            Re-identified text with original PHI restored
        """
        token_mapping = self._token_mappings.get(result_id)
        if not token_mapping:
            logger.warning(f"No token mapping found for result_id: {result_id}")
            return text

        # Verify consent if in strict mode
        if self.strict_mode and not consent_verified:
            raise PermissionError(
                "Re-identification requires verified consent in strict mode"
            )

        # Replace masked tokens with original values
        reidentified_text = text
        for masked, original in token_mapping.items():
            reidentified_text = reidentified_text.replace(masked, original)

        # Audit log
        await self._log_audit(
            tenant_id=tenant_id,
            action="reidentify",
            resource_type="text",
            resource_id=result_id,
            user_id=user_id,
            phi_count=len(token_mapping),
            reason=reason,
            consent_verified=consent_verified,
        )

        logger.info(f"Re-identified text for result_id: {result_id}")
        return reidentified_text

    async def safe_process(
        self,
        text: str,
        tenant_id: str,
        processor: Any,  # Callable or coroutine
        patient_id: Optional[str] = None,
        user_id: Optional[str] = None,
        purpose: str = "ai_processing",
    ) -> Tuple[Any, DeidentificationResult]:
        """
        Safely process text with PHI protection.

        1. Verify consent if patient_id provided
        2. De-identify text
        3. Process with provided processor
        4. Return result and de-identification info

        Args:
            text: Text to process
            tenant_id: Tenant identifier
            processor: Processing function/coroutine
            patient_id: Patient ID for consent verification
            user_id: User performing processing
            purpose: Processing purpose

        Returns:
            Tuple of (processing result, de-identification result)
        """
        # Verify consent if patient_id provided
        if patient_id:
            has_consent = await self.verify_consent(
                patient_id=patient_id,
                tenant_id=tenant_id,
                purpose=purpose,
            )

            if not has_consent and self.strict_mode:
                raise PermissionError(
                    f"Patient {patient_id} has not consented to {purpose}"
                )

        # De-identify
        deident_result = await self.deidentify(
            text=text,
            tenant_id=tenant_id,
            user_id=user_id,
            reason=purpose,
        )

        # Process de-identified text
        if asyncio.iscoroutinefunction(processor):
            process_result = await processor(deident_result.deidentified_text)
        else:
            process_result = processor(deident_result.deidentified_text)

        return process_result, deident_result

    # ==================== Consent Management ====================

    async def record_consent(
        self,
        patient_id: str,
        tenant_id: str,
        purpose: str,
        granted: bool = True,
        allowed_phi_types: Optional[List[PHIType]] = None,
        allowed_uses: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None,
    ) -> ConsentRecord:
        """
        Record patient consent for data processing.

        Args:
            patient_id: Patient identifier
            tenant_id: Tenant identifier
            purpose: Purpose of consent (ai_processing, research, etc.)
            granted: Whether consent is granted
            allowed_phi_types: Specific PHI types allowed
            allowed_uses: Specific uses allowed
            expires_at: Consent expiration date

        Returns:
            ConsentRecord
        """
        consent = ConsentRecord(
            consent_id=str(uuid4()),
            patient_id=patient_id,
            tenant_id=tenant_id,
            purpose=purpose,
            granted=granted,
            allowed_phi_types=allowed_phi_types or [],
            allowed_uses=allowed_uses or [],
            expires_at=expires_at,
        )

        # Store consent
        consent_key = f"{tenant_id}:{patient_id}:{purpose}"
        self._consent_records[consent_key] = consent

        # Audit log
        await self._log_audit(
            tenant_id=tenant_id,
            action="consent_record",
            resource_type="consent",
            resource_id=consent.consent_id,
            reason=f"Consent {'granted' if granted else 'denied'} for {purpose}",
        )

        logger.info(
            f"Recorded consent for patient {patient_id}: "
            f"{purpose} = {granted}"
        )

        return consent

    async def revoke_consent(
        self,
        patient_id: str,
        tenant_id: str,
        purpose: str,
        user_id: Optional[str] = None,
    ) -> bool:
        """Revoke patient consent."""
        consent_key = f"{tenant_id}:{patient_id}:{purpose}"
        consent = self._consent_records.get(consent_key)

        if not consent:
            return False

        consent.revoked = True
        consent.revoked_at = datetime.now(timezone.utc)
        consent.granted = False

        await self._log_audit(
            tenant_id=tenant_id,
            action="consent_revoke",
            resource_type="consent",
            resource_id=consent.consent_id,
            user_id=user_id,
            reason=f"Consent revoked for {purpose}",
        )

        logger.info(f"Revoked consent for patient {patient_id}: {purpose}")
        return True

    async def verify_consent(
        self,
        patient_id: str,
        tenant_id: str,
        purpose: str,
        phi_type: Optional[PHIType] = None,
    ) -> bool:
        """
        Verify patient has valid consent for processing.

        Args:
            patient_id: Patient identifier
            tenant_id: Tenant identifier
            purpose: Processing purpose
            phi_type: Specific PHI type being processed

        Returns:
            True if consent is valid
        """
        consent_key = f"{tenant_id}:{patient_id}:{purpose}"
        consent = self._consent_records.get(consent_key)

        if not consent:
            return False

        # Check if revoked
        if consent.revoked:
            return False

        # Check if expired
        if consent.expires_at and consent.expires_at < datetime.now(timezone.utc):
            return False

        # Check if granted
        if not consent.granted:
            return False

        # Check specific PHI type if provided
        if phi_type and consent.allowed_phi_types:
            if phi_type not in consent.allowed_phi_types:
                return False

        return True

    async def get_patient_consents(
        self,
        patient_id: str,
        tenant_id: str,
    ) -> List[ConsentRecord]:
        """Get all consents for a patient."""
        return [
            consent for consent in self._consent_records.values()
            if consent.patient_id == patient_id
            and consent.tenant_id == tenant_id
        ]

    # ==================== Audit Logging ====================

    async def _log_audit(
        self,
        tenant_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        service_name: Optional[str] = None,
        phi_types_detected: Optional[List[str]] = None,
        phi_count: int = 0,
        reason: Optional[str] = None,
        consent_verified: bool = False,
        consent_id: Optional[str] = None,
    ):
        """Log PHI-related action to audit trail."""
        log_entry = PHIAuditLog(
            audit_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc),
            tenant_id=tenant_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            service_name=service_name,
            phi_types_detected=phi_types_detected or [],
            phi_count=phi_count,
            reason=reason,
            consent_verified=consent_verified,
            consent_id=consent_id,
        )

        self._audit_logs.append(log_entry)

        # In production, also write to persistent storage
        logger.info(
            f"PHI Audit: {action} on {resource_type} "
            f"(tenant: {tenant_id}, user: {user_id}, phi_count: {phi_count})"
        )

    async def get_audit_logs(
        self,
        tenant_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        action: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[PHIAuditLog]:
        """
        Get PHI audit logs.

        Args:
            tenant_id: Tenant identifier
            start_time: Filter start time
            end_time: Filter end time
            action: Filter by action type
            user_id: Filter by user
            limit: Maximum logs to return

        Returns:
            List of PHIAuditLog entries
        """
        logs = [
            log for log in self._audit_logs
            if log.tenant_id == tenant_id
            and (start_time is None or log.timestamp >= start_time)
            and (end_time is None or log.timestamp <= end_time)
            and (action is None or log.action == action)
            and (user_id is None or log.user_id == user_id)
        ]

        # Sort by timestamp descending
        logs.sort(key=lambda x: x.timestamp, reverse=True)

        return logs[:limit]

    async def get_phi_access_summary(
        self,
        tenant_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get summary of PHI access for compliance reporting."""
        logs = await self.get_audit_logs(
            tenant_id=tenant_id,
            start_time=start_time,
            end_time=end_time,
            limit=10000,
        )

        if not logs:
            return {"status": "no_data"}

        # Aggregate
        by_action: Dict[str, int] = {}
        by_user: Dict[str, int] = {}
        by_phi_type: Dict[str, int] = {}
        total_phi_accessed = 0

        for log in logs:
            by_action[log.action] = by_action.get(log.action, 0) + 1

            if log.user_id:
                by_user[log.user_id] = by_user.get(log.user_id, 0) + 1

            for phi_type in log.phi_types_detected:
                by_phi_type[phi_type] = by_phi_type.get(phi_type, 0) + 1

            total_phi_accessed += log.phi_count

        return {
            "period": {
                "start": start_time.isoformat() if start_time else None,
                "end": end_time.isoformat() if end_time else None,
            },
            "total_events": len(logs),
            "total_phi_accessed": total_phi_accessed,
            "by_action": by_action,
            "by_user": by_user,
            "by_phi_type": by_phi_type,
            "consent_verified_rate": (
                sum(1 for log in logs if log.consent_verified) / len(logs)
                if logs else 0
            ),
        }


# Global PHI protection service instance
phi_protection_service = PHIProtectionService()
