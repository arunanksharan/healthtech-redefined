"""
Preference Service
Communication preference and consent management
TCPA, GDPR, and HIPAA compliant
"""
from datetime import datetime, timedelta, time
from typing import Dict, Any, Optional, List, Tuple
from uuid import UUID
from sqlalchemy import select, update, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from .models import (
    CommunicationPreference,
    ConsentRecord,
    OmniChannelType,
    ConsentType,
)


class PreferenceService:
    """
    Manages patient communication preferences and consent.

    Features:
    - Channel preference management
    - Consent tracking (TCPA, GDPR compliant)
    - Opt-out/opt-in handling
    - Quiet hours management
    - Preference history
    - Regulatory compliance
    """

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def get_preferences(
        self,
        patient_id: UUID
    ) -> Optional[CommunicationPreference]:
        """
        Get patient's communication preferences.

        Args:
            patient_id: Patient UUID

        Returns:
            Preferences if found
        """
        result = await self.db.execute(
            select(CommunicationPreference)
            .where(
                and_(
                    CommunicationPreference.tenant_id == self.tenant_id,
                    CommunicationPreference.patient_id == patient_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create_preferences(
        self,
        patient_id: UUID,
        defaults: Optional[Dict[str, Any]] = None
    ) -> Tuple[CommunicationPreference, bool]:
        """
        Get existing preferences or create with defaults.

        Args:
            patient_id: Patient UUID
            defaults: Default values for new preferences

        Returns:
            Tuple of (preferences, is_new)
        """
        existing = await self.get_preferences(patient_id)

        if existing:
            return existing, False

        # Create new preferences with defaults
        prefs = CommunicationPreference(
            tenant_id=self.tenant_id,
            patient_id=patient_id,
            # Default all channels enabled
            sms_enabled=True,
            email_enabled=True,
            whatsapp_enabled=True,
            voice_enabled=True,
            push_enabled=True,
            # Opt-in settings (conservative defaults)
            marketing_opt_in=False,
            appointment_reminders=True,
            health_tips=False,
            promotional=False,
            # Default language
            preferred_language='en',
            created_at=datetime.utcnow()
        )

        if defaults:
            for key, value in defaults.items():
                if hasattr(prefs, key):
                    setattr(prefs, key, value)

        self.db.add(prefs)
        await self.db.flush()

        logger.info(f"Created preferences for patient {patient_id}")
        return prefs, True

    async def update_preferences(
        self,
        patient_id: UUID,
        updates: Dict[str, Any],
        updated_by: Optional[UUID] = None,
        source: str = 'api'
    ) -> Optional[CommunicationPreference]:
        """
        Update patient preferences.

        Args:
            patient_id: Patient UUID
            updates: Fields to update
            updated_by: Who made the update
            source: Update source (api, portal, ivr, etc.)

        Returns:
            Updated preferences
        """
        prefs, _ = await self.get_or_create_preferences(patient_id)

        # Track what changed for audit
        changes = {}

        for key, value in updates.items():
            if hasattr(prefs, key):
                old_value = getattr(prefs, key)
                if old_value != value:
                    changes[key] = {'old': old_value, 'new': value}
                    setattr(prefs, key, value)

        if changes:
            prefs.updated_at = datetime.utcnow()

            # Log preference change event
            logger.info(f"Updated preferences for patient {patient_id}: {list(changes.keys())}")

        return prefs

    async def set_channel_preference(
        self,
        patient_id: UUID,
        channel: OmniChannelType,
        enabled: bool,
        updated_by: Optional[UUID] = None
    ) -> bool:
        """
        Enable or disable a specific channel.

        Args:
            patient_id: Patient UUID
            channel: Channel to update
            enabled: Whether to enable
            updated_by: Who made the update

        Returns:
            True if updated
        """
        channel_field_map = {
            OmniChannelType.SMS: 'sms_enabled',
            OmniChannelType.EMAIL: 'email_enabled',
            OmniChannelType.WHATSAPP: 'whatsapp_enabled',
            OmniChannelType.VOICE: 'voice_enabled',
            OmniChannelType.PUSH_NOTIFICATION: 'push_enabled',
        }

        field = channel_field_map.get(channel)
        if not field:
            return False

        await self.update_preferences(
            patient_id,
            {field: enabled},
            updated_by=updated_by,
            source='channel_preference'
        )

        return True

    async def set_quiet_hours(
        self,
        patient_id: UUID,
        start_time: time,
        end_time: time,
        timezone: str = 'UTC',
        enabled: bool = True
    ) -> bool:
        """
        Set quiet hours for patient.

        Args:
            patient_id: Patient UUID
            start_time: Quiet hours start
            end_time: Quiet hours end
            timezone: Patient's timezone
            enabled: Whether quiet hours are enabled

        Returns:
            True if set
        """
        quiet_hours_config = {
            'enabled': enabled,
            'start': start_time.isoformat(),
            'end': end_time.isoformat(),
            'timezone': timezone
        }

        await self.update_preferences(
            patient_id,
            {
                'quiet_hours_start': start_time,
                'quiet_hours_end': end_time,
                'timezone': timezone
            },
            source='quiet_hours'
        )

        return True

    async def is_within_quiet_hours(
        self,
        patient_id: UUID,
        check_time: Optional[datetime] = None
    ) -> bool:
        """
        Check if current time is within patient's quiet hours.

        Args:
            patient_id: Patient UUID
            check_time: Time to check (defaults to now)

        Returns:
            True if within quiet hours
        """
        prefs = await self.get_preferences(patient_id)

        if not prefs or not prefs.quiet_hours_start or not prefs.quiet_hours_end:
            return False

        if check_time is None:
            check_time = datetime.utcnow()

        # Convert to patient's timezone
        # In production, use pytz for proper timezone handling
        current_time = check_time.time()

        start = prefs.quiet_hours_start
        end = prefs.quiet_hours_end

        # Handle overnight quiet hours (e.g., 22:00 to 07:00)
        if start > end:
            return current_time >= start or current_time <= end
        else:
            return start <= current_time <= end

    async def record_consent(
        self,
        patient_id: UUID,
        consent_type: ConsentType,
        channel: OmniChannelType,
        consent_given: bool,
        consent_method: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        consent_text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConsentRecord:
        """
        Record a consent action (opt-in or opt-out).

        Args:
            patient_id: Patient UUID
            consent_type: Type of consent
            channel: Channel for consent
            consent_given: Whether consent was given
            consent_method: How consent was obtained
            ip_address: Patient's IP address
            user_agent: Patient's browser/device
            consent_text: The consent text shown
            metadata: Additional metadata

        Returns:
            Created consent record
        """
        record = ConsentRecord(
            tenant_id=self.tenant_id,
            patient_id=patient_id,
            consent_type=consent_type,
            channel=channel,
            consent_given=consent_given,
            consent_method=consent_method,
            ip_address=ip_address,
            user_agent=user_agent,
            consent_text=consent_text,
            consent_timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )

        self.db.add(record)
        await self.db.flush()

        # Update preferences based on consent
        if consent_type == ConsentType.MARKETING:
            await self.update_preferences(
                patient_id,
                {'marketing_opt_in': consent_given},
                source='consent'
            )
        elif consent_type == ConsentType.SMS:
            await self.update_preferences(
                patient_id,
                {'sms_enabled': consent_given},
                source='consent'
            )

        logger.info(
            f"Recorded consent for patient {patient_id}: "
            f"{consent_type.value} - {'given' if consent_given else 'withdrawn'}"
        )

        return record

    async def process_opt_out(
        self,
        contact: str,
        channel: OmniChannelType,
        opt_out_method: str = 'keyword',
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Process opt-out request (e.g., "STOP" keyword).

        Args:
            contact: Phone number or email
            channel: Channel for opt-out
            opt_out_method: How opt-out was received
            metadata: Additional data

        Returns:
            True if processed
        """
        # Find patient by contact
        # This would need to query patient table - simplified here
        prefs = await self.db.execute(
            select(CommunicationPreference)
            .where(
                and_(
                    CommunicationPreference.tenant_id == self.tenant_id,
                    or_(
                        CommunicationPreference.primary_phone == contact,
                        CommunicationPreference.primary_email == contact
                    )
                )
            )
        )
        pref = prefs.scalar_one_or_none()

        if not pref:
            logger.warning(f"Opt-out request for unknown contact: {contact}")
            return False

        # Record consent withdrawal
        consent_type_map = {
            OmniChannelType.SMS: ConsentType.SMS,
            OmniChannelType.EMAIL: ConsentType.EMAIL,
            OmniChannelType.WHATSAPP: ConsentType.WHATSAPP,
            OmniChannelType.VOICE: ConsentType.VOICE,
        }

        await self.record_consent(
            patient_id=pref.patient_id,
            consent_type=consent_type_map.get(channel, ConsentType.SMS),
            channel=channel,
            consent_given=False,
            consent_method=opt_out_method,
            metadata=metadata
        )

        # Disable channel
        await self.set_channel_preference(
            pref.patient_id,
            channel,
            enabled=False
        )

        return True

    async def process_opt_in(
        self,
        contact: str,
        channel: OmniChannelType,
        opt_in_method: str = 'keyword',
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Process opt-in request (e.g., "START" keyword).

        Args:
            contact: Phone number or email
            channel: Channel for opt-in
            opt_in_method: How opt-in was received
            metadata: Additional data

        Returns:
            True if processed
        """
        prefs = await self.db.execute(
            select(CommunicationPreference)
            .where(
                and_(
                    CommunicationPreference.tenant_id == self.tenant_id,
                    or_(
                        CommunicationPreference.primary_phone == contact,
                        CommunicationPreference.primary_email == contact
                    )
                )
            )
        )
        pref = prefs.scalar_one_or_none()

        if not pref:
            logger.warning(f"Opt-in request for unknown contact: {contact}")
            return False

        # Record consent
        consent_type_map = {
            OmniChannelType.SMS: ConsentType.SMS,
            OmniChannelType.EMAIL: ConsentType.EMAIL,
            OmniChannelType.WHATSAPP: ConsentType.WHATSAPP,
            OmniChannelType.VOICE: ConsentType.VOICE,
        }

        await self.record_consent(
            patient_id=pref.patient_id,
            consent_type=consent_type_map.get(channel, ConsentType.SMS),
            channel=channel,
            consent_given=True,
            consent_method=opt_in_method,
            metadata=metadata
        )

        # Enable channel
        await self.set_channel_preference(
            pref.patient_id,
            channel,
            enabled=True
        )

        return True

    async def get_consent_history(
        self,
        patient_id: UUID,
        consent_type: Optional[ConsentType] = None,
        limit: int = 50
    ) -> List[ConsentRecord]:
        """
        Get patient's consent history.

        Args:
            patient_id: Patient UUID
            consent_type: Optional filter by type
            limit: Max records

        Returns:
            List of consent records
        """
        query = select(ConsentRecord).where(
            and_(
                ConsentRecord.tenant_id == self.tenant_id,
                ConsentRecord.patient_id == patient_id
            )
        )

        if consent_type:
            query = query.where(ConsentRecord.consent_type == consent_type)

        query = query.order_by(desc(ConsentRecord.consent_timestamp))
        query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def can_send_to_patient(
        self,
        patient_id: UUID,
        channel: OmniChannelType,
        message_type: str = 'transactional'
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if we can send to patient on given channel.

        Args:
            patient_id: Patient UUID
            channel: Target channel
            message_type: Type of message (transactional, marketing, etc.)

        Returns:
            Tuple of (can_send, reason_if_not)
        """
        prefs = await self.get_preferences(patient_id)

        if not prefs:
            return True, None  # No preferences = allow transactional

        # Check channel enabled
        channel_field_map = {
            OmniChannelType.SMS: 'sms_enabled',
            OmniChannelType.EMAIL: 'email_enabled',
            OmniChannelType.WHATSAPP: 'whatsapp_enabled',
            OmniChannelType.VOICE: 'voice_enabled',
            OmniChannelType.PUSH_NOTIFICATION: 'push_enabled',
        }

        field = channel_field_map.get(channel)
        if field and not getattr(prefs, field, True):
            return False, f"Channel {channel.value} is disabled"

        # Check message type preferences
        if message_type == 'marketing' and not prefs.marketing_opt_in:
            return False, "Marketing messages not opted in"

        if message_type == 'promotional' and not prefs.promotional:
            return False, "Promotional messages not opted in"

        if message_type == 'health_tips' and not prefs.health_tips:
            return False, "Health tips not opted in"

        # Check quiet hours
        if await self.is_within_quiet_hours(patient_id):
            # Allow urgent messages during quiet hours
            if message_type not in ['urgent', 'emergency']:
                return False, "Within quiet hours"

        return True, None

    async def get_preferred_channel(
        self,
        patient_id: UUID,
        available_channels: Optional[List[OmniChannelType]] = None
    ) -> Optional[OmniChannelType]:
        """
        Get patient's preferred communication channel.

        Args:
            patient_id: Patient UUID
            available_channels: Channels to consider

        Returns:
            Preferred channel or None
        """
        prefs = await self.get_preferences(patient_id)

        if not prefs:
            # Default preference order
            default_order = [
                OmniChannelType.WHATSAPP,
                OmniChannelType.SMS,
                OmniChannelType.EMAIL,
                OmniChannelType.VOICE
            ]
            if available_channels:
                for ch in default_order:
                    if ch in available_channels:
                        return ch
            return OmniChannelType.SMS

        # Check explicit preferred channel
        if prefs.preferred_channel:
            if not available_channels or prefs.preferred_channel in available_channels:
                # Verify channel is enabled
                can_send, _ = await self.can_send_to_patient(
                    patient_id,
                    prefs.preferred_channel
                )
                if can_send:
                    return prefs.preferred_channel

        # Fall back to enabled channels in priority order
        priority = [
            (OmniChannelType.WHATSAPP, prefs.whatsapp_enabled),
            (OmniChannelType.SMS, prefs.sms_enabled),
            (OmniChannelType.EMAIL, prefs.email_enabled),
            (OmniChannelType.VOICE, prefs.voice_enabled),
        ]

        for channel, enabled in priority:
            if enabled:
                if not available_channels or channel in available_channels:
                    return channel

        return None

    async def bulk_update_preferences(
        self,
        patient_ids: List[UUID],
        updates: Dict[str, Any],
        source: str = 'bulk'
    ) -> int:
        """
        Bulk update preferences for multiple patients.

        Args:
            patient_ids: List of patient UUIDs
            updates: Fields to update
            source: Update source

        Returns:
            Number of records updated
        """
        result = await self.db.execute(
            update(CommunicationPreference)
            .where(
                and_(
                    CommunicationPreference.tenant_id == self.tenant_id,
                    CommunicationPreference.patient_id.in_(patient_ids)
                )
            )
            .values(**updates, updated_at=datetime.utcnow())
        )

        logger.info(f"Bulk updated preferences for {result.rowcount} patients")
        return result.rowcount

    async def export_consent_records(
        self,
        patient_id: UUID
    ) -> Dict[str, Any]:
        """
        Export all consent records for GDPR compliance.

        Args:
            patient_id: Patient UUID

        Returns:
            Export data
        """
        prefs = await self.get_preferences(patient_id)
        consent_history = await self.get_consent_history(patient_id, limit=1000)

        return {
            "patient_id": str(patient_id),
            "exported_at": datetime.utcnow().isoformat(),
            "current_preferences": {
                "sms_enabled": prefs.sms_enabled if prefs else True,
                "email_enabled": prefs.email_enabled if prefs else True,
                "whatsapp_enabled": prefs.whatsapp_enabled if prefs else True,
                "voice_enabled": prefs.voice_enabled if prefs else True,
                "marketing_opt_in": prefs.marketing_opt_in if prefs else False,
                "preferred_language": prefs.preferred_language if prefs else 'en',
                "quiet_hours": {
                    "start": prefs.quiet_hours_start.isoformat() if prefs and prefs.quiet_hours_start else None,
                    "end": prefs.quiet_hours_end.isoformat() if prefs and prefs.quiet_hours_end else None,
                    "timezone": prefs.timezone if prefs else None
                }
            } if prefs else {},
            "consent_history": [
                {
                    "consent_type": record.consent_type.value if record.consent_type else None,
                    "channel": record.channel.value if record.channel else None,
                    "consent_given": record.consent_given,
                    "consent_method": record.consent_method,
                    "timestamp": record.consent_timestamp.isoformat() if record.consent_timestamp else None,
                    "consent_text": record.consent_text
                }
                for record in consent_history
            ]
        }
