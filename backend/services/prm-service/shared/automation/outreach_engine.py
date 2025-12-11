"""
Proactive Patient Outreach Engine

Provides intelligent campaign management, personalized messaging,
and multi-channel communication for patient engagement.

Part of EPIC-012: Intelligent Automation Platform
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


class CampaignType(str, Enum):
    """Types of outreach campaigns"""
    APPOINTMENT_REMINDER = "appointment_reminder"
    PREVENTIVE_CARE = "preventive_care"
    CHRONIC_CARE = "chronic_care"
    WELLNESS = "wellness"
    SEASONAL = "seasonal"
    REACTIVATION = "reactivation"
    SATISFACTION = "satisfaction"
    EDUCATIONAL = "educational"
    BILLING = "billing"
    REFERRAL = "referral"
    POST_VISIT = "post_visit"
    PRE_VISIT = "pre_visit"
    CUSTOM = "custom"


class CampaignStatus(str, Enum):
    """Campaign execution status"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OutreachChannel(str, Enum):
    """Communication channels"""
    SMS = "sms"
    EMAIL = "email"
    VOICE = "voice"
    WHATSAPP = "whatsapp"
    PUSH_NOTIFICATION = "push_notification"
    PATIENT_PORTAL = "patient_portal"
    MAIL = "mail"


class MessageStatus(str, Enum):
    """Individual message status"""
    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    RESPONDED = "responded"
    BOUNCED = "bounced"
    FAILED = "failed"
    OPTED_OUT = "opted_out"
    UNSUBSCRIBED = "unsubscribed"


class OutreachPriority(str, Enum):
    """Outreach priority levels"""
    URGENT = "urgent"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class SegmentOperator(str, Enum):
    """Operators for segment criteria"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    BETWEEN = "between"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    DAYS_AGO = "days_ago"
    DAYS_FROM_NOW = "days_from_now"


@dataclass
class SegmentCriteria:
    """Criteria for patient segmentation"""
    field: str
    operator: SegmentOperator
    value: Any
    logical_operator: str = "AND"  # AND, OR


@dataclass
class PatientSegment:
    """Patient segment definition"""
    segment_id: str
    tenant_id: str
    name: str
    description: str
    criteria: list[SegmentCriteria]
    estimated_size: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_dynamic: bool = True  # Re-evaluate on each use
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MessageTemplate:
    """Message template with personalization"""
    template_id: str
    tenant_id: str
    name: str
    channel: OutreachChannel
    subject: Optional[str]  # For email
    body: str
    variables: list[str]  # Personalization variables like {{patient_name}}
    language: str = "en"
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CampaignSchedule:
    """Campaign scheduling configuration"""
    start_date: datetime
    end_date: Optional[datetime] = None
    send_times: list[str] = field(default_factory=list)  # ["09:00", "14:00"]
    send_days: list[int] = field(default_factory=list)  # 0=Mon, 6=Sun
    timezone: str = "UTC"
    max_per_day: Optional[int] = None
    max_per_patient: int = 1
    cooldown_days: int = 7  # Days between messages to same patient


@dataclass
class CampaignStep:
    """Step in multi-step campaign"""
    step_id: str
    step_number: int
    name: str
    channel: OutreachChannel
    template_id: str
    delay_days: int = 0  # Days after previous step
    delay_hours: int = 0
    condition: Optional[dict[str, Any]] = None  # Condition to execute
    fallback_channel: Optional[OutreachChannel] = None


@dataclass
class Campaign:
    """Outreach campaign definition"""
    campaign_id: str
    tenant_id: str
    name: str
    description: str
    campaign_type: CampaignType
    status: CampaignStatus
    segment_id: str
    steps: list[CampaignStep]
    schedule: CampaignSchedule
    priority: OutreachPriority = OutreachPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    goals: dict[str, Any] = field(default_factory=dict)
    ab_test_config: Optional[dict[str, Any]] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class OutreachMessage:
    """Individual outreach message"""
    message_id: str
    tenant_id: str
    campaign_id: str
    step_id: str
    patient_id: str
    channel: OutreachChannel
    status: MessageStatus
    template_id: str
    personalized_content: str
    scheduled_at: datetime
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    response_content: Optional[str] = None
    error_message: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CampaignAnalytics:
    """Campaign performance analytics"""
    campaign_id: str
    total_targeted: int
    total_sent: int
    total_delivered: int
    total_opened: int
    total_clicked: int
    total_responded: int
    total_bounced: int
    total_opted_out: int
    delivery_rate: float
    open_rate: float
    click_rate: float
    response_rate: float
    cost: float
    roi: Optional[float] = None
    by_channel: dict[str, dict[str, int]] = field(default_factory=dict)
    by_day: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class PatientPreferences:
    """Patient communication preferences"""
    patient_id: str
    preferred_channel: OutreachChannel
    preferred_language: str
    preferred_time: Optional[str] = None  # HH:MM
    opted_out_channels: list[OutreachChannel] = field(default_factory=list)
    opted_out_types: list[CampaignType] = field(default_factory=list)
    do_not_contact: bool = False
    last_contact_date: Optional[datetime] = None
    contact_frequency_limit: Optional[int] = None  # Max contacts per month


class PatientOutreachEngine:
    """
    Intelligent patient outreach and campaign management engine.
    Handles segmentation, personalization, scheduling, and analytics.
    """

    def __init__(self):
        self.campaigns: dict[str, Campaign] = {}
        self.segments: dict[str, PatientSegment] = {}
        self.templates: dict[str, MessageTemplate] = {}
        self.messages: dict[str, OutreachMessage] = {}
        self.patient_preferences: dict[str, PatientPreferences] = {}
        self.personalization_functions: dict[str, callable] = {}
        self._initialize_personalization()

    def _initialize_personalization(self):
        """Initialize personalization functions"""
        self.personalization_functions = {
            "patient_name": lambda p: p.get("name", "Patient"),
            "first_name": lambda p: p.get("name", "").split()[0] if p.get("name") else "there",
            "provider_name": lambda p: p.get("provider_name", "your provider"),
            "appointment_date": lambda p: p.get("appointment_date", ""),
            "appointment_time": lambda p: p.get("appointment_time", ""),
            "location": lambda p: p.get("location", "our office"),
            "procedure": lambda p: p.get("procedure", "your appointment"),
            "care_gap": lambda p: p.get("care_gap", "preventive care"),
            "medication": lambda p: p.get("medication", "your medication"),
            "balance": lambda p: f"${p.get('balance', 0):.2f}",
            "portal_link": lambda p: p.get("portal_link", "https://portal.example.com"),
            "unsubscribe_link": lambda p: p.get("unsubscribe_link", "#"),
        }

    async def create_segment(
        self,
        tenant_id: str,
        name: str,
        description: str,
        criteria: list[dict[str, Any]],
        is_dynamic: bool = True
    ) -> PatientSegment:
        """Create a patient segment"""
        segment = PatientSegment(
            segment_id=str(uuid4()),
            tenant_id=tenant_id,
            name=name,
            description=description,
            criteria=[
                SegmentCriteria(
                    field=c["field"],
                    operator=SegmentOperator(c["operator"]),
                    value=c["value"],
                    logical_operator=c.get("logical_operator", "AND")
                )
                for c in criteria
            ],
            is_dynamic=is_dynamic
        )

        self.segments[segment.segment_id] = segment
        return segment

    async def evaluate_segment(
        self,
        segment_id: str,
        patients: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Evaluate which patients match segment criteria"""
        segment = self.segments.get(segment_id)
        if not segment:
            return []

        matching_patients = []

        for patient in patients:
            if self._patient_matches_criteria(patient, segment.criteria):
                matching_patients.append(patient)

        segment.estimated_size = len(matching_patients)
        return matching_patients

    def _patient_matches_criteria(
        self,
        patient: dict[str, Any],
        criteria: list[SegmentCriteria]
    ) -> bool:
        """Check if patient matches all criteria"""
        results = []

        for criterion in criteria:
            field_value = self._get_nested_value(patient, criterion.field)
            matches = self._evaluate_criterion(field_value, criterion)

            if criterion.logical_operator == "OR" and results:
                results[-1] = results[-1] or matches
            else:
                results.append(matches)

        return all(results) if results else True

    def _get_nested_value(self, obj: dict, path: str) -> Any:
        """Get nested value from dict using dot notation"""
        keys = path.split(".")
        value = obj
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value

    def _evaluate_criterion(
        self,
        value: Any,
        criterion: SegmentCriteria
    ) -> bool:
        """Evaluate a single criterion"""
        target = criterion.value

        if criterion.operator == SegmentOperator.EQUALS:
            return value == target
        elif criterion.operator == SegmentOperator.NOT_EQUALS:
            return value != target
        elif criterion.operator == SegmentOperator.GREATER_THAN:
            return value is not None and value > target
        elif criterion.operator == SegmentOperator.LESS_THAN:
            return value is not None and value < target
        elif criterion.operator == SegmentOperator.BETWEEN:
            return target[0] <= value <= target[1] if value else False
        elif criterion.operator == SegmentOperator.IN:
            return value in target
        elif criterion.operator == SegmentOperator.NOT_IN:
            return value not in target
        elif criterion.operator == SegmentOperator.CONTAINS:
            return target.lower() in str(value).lower() if value else False
        elif criterion.operator == SegmentOperator.STARTS_WITH:
            return str(value).lower().startswith(target.lower()) if value else False
        elif criterion.operator == SegmentOperator.IS_NULL:
            return value is None
        elif criterion.operator == SegmentOperator.IS_NOT_NULL:
            return value is not None
        elif criterion.operator == SegmentOperator.DAYS_AGO:
            if not value:
                return False
            date_val = datetime.fromisoformat(str(value)) if isinstance(value, str) else value
            return (datetime.utcnow() - date_val).days >= target
        elif criterion.operator == SegmentOperator.DAYS_FROM_NOW:
            if not value:
                return False
            date_val = datetime.fromisoformat(str(value)) if isinstance(value, str) else value
            return (date_val - datetime.utcnow()).days <= target

        return False

    async def create_template(
        self,
        tenant_id: str,
        name: str,
        channel: OutreachChannel,
        body: str,
        subject: Optional[str] = None,
        language: str = "en"
    ) -> MessageTemplate:
        """Create a message template"""
        # Extract variables from template
        import re
        variables = re.findall(r"\{\{(\w+)\}\}", body)
        if subject:
            variables.extend(re.findall(r"\{\{(\w+)\}\}", subject))
        variables = list(set(variables))

        template = MessageTemplate(
            template_id=str(uuid4()),
            tenant_id=tenant_id,
            name=name,
            channel=channel,
            subject=subject,
            body=body,
            variables=variables,
            language=language
        )

        self.templates[template.template_id] = template
        return template

    async def create_campaign(
        self,
        tenant_id: str,
        name: str,
        description: str,
        campaign_type: CampaignType,
        segment_id: str,
        steps: list[dict[str, Any]],
        schedule: dict[str, Any],
        priority: OutreachPriority = OutreachPriority.NORMAL,
        created_by: Optional[str] = None
    ) -> Campaign:
        """Create an outreach campaign"""
        campaign_steps = [
            CampaignStep(
                step_id=str(uuid4()),
                step_number=i + 1,
                name=s["name"],
                channel=OutreachChannel(s["channel"]),
                template_id=s["template_id"],
                delay_days=s.get("delay_days", 0),
                delay_hours=s.get("delay_hours", 0),
                condition=s.get("condition"),
                fallback_channel=OutreachChannel(s["fallback_channel"]) if s.get("fallback_channel") else None
            )
            for i, s in enumerate(steps)
        ]

        campaign_schedule = CampaignSchedule(
            start_date=datetime.fromisoformat(schedule["start_date"]) if isinstance(schedule["start_date"], str) else schedule["start_date"],
            end_date=datetime.fromisoformat(schedule["end_date"]) if schedule.get("end_date") and isinstance(schedule["end_date"], str) else schedule.get("end_date"),
            send_times=schedule.get("send_times", ["09:00"]),
            send_days=schedule.get("send_days", [0, 1, 2, 3, 4]),  # Weekdays
            timezone=schedule.get("timezone", "UTC"),
            max_per_day=schedule.get("max_per_day"),
            max_per_patient=schedule.get("max_per_patient", 1),
            cooldown_days=schedule.get("cooldown_days", 7)
        )

        campaign = Campaign(
            campaign_id=str(uuid4()),
            tenant_id=tenant_id,
            name=name,
            description=description,
            campaign_type=campaign_type,
            status=CampaignStatus.DRAFT,
            segment_id=segment_id,
            steps=campaign_steps,
            schedule=campaign_schedule,
            priority=priority,
            created_by=created_by
        )

        self.campaigns[campaign.campaign_id] = campaign
        return campaign

    async def activate_campaign(self, campaign_id: str) -> Campaign:
        """Activate a campaign for execution"""
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign not found: {campaign_id}")

        if campaign.status not in [CampaignStatus.DRAFT, CampaignStatus.PAUSED]:
            raise ValueError(f"Campaign cannot be activated from status: {campaign.status}")

        campaign.status = CampaignStatus.ACTIVE
        campaign.updated_at = datetime.utcnow()
        return campaign

    async def pause_campaign(self, campaign_id: str) -> Campaign:
        """Pause an active campaign"""
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign not found: {campaign_id}")

        if campaign.status != CampaignStatus.ACTIVE:
            raise ValueError("Only active campaigns can be paused")

        campaign.status = CampaignStatus.PAUSED
        campaign.updated_at = datetime.utcnow()
        return campaign

    async def execute_campaign(
        self,
        campaign_id: str,
        patients: list[dict[str, Any]]
    ) -> list[OutreachMessage]:
        """Execute campaign for a batch of patients"""
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign not found: {campaign_id}")

        if campaign.status != CampaignStatus.ACTIVE:
            raise ValueError("Campaign must be active to execute")

        messages = []

        for patient in patients:
            # Check patient preferences
            prefs = self.patient_preferences.get(patient.get("id"))
            if prefs and prefs.do_not_contact:
                continue
            if prefs and campaign.campaign_type in prefs.opted_out_types:
                continue

            # Check cooldown
            if not self._check_cooldown(patient, campaign):
                continue

            # Process each step
            for step in campaign.steps:
                # Check step condition
                if step.condition and not self._evaluate_step_condition(patient, step.condition):
                    continue

                # Determine channel
                channel = step.channel
                if prefs and channel in prefs.opted_out_channels:
                    if step.fallback_channel and step.fallback_channel not in prefs.opted_out_channels:
                        channel = step.fallback_channel
                    else:
                        continue

                # Get template and personalize
                template = self.templates.get(step.template_id)
                if not template:
                    continue

                personalized_content = self._personalize_message(
                    template.body,
                    patient
                )

                # Calculate send time
                scheduled_at = self._calculate_send_time(
                    campaign.schedule,
                    step.delay_days,
                    step.delay_hours
                )

                # Create message
                message = OutreachMessage(
                    message_id=str(uuid4()),
                    tenant_id=campaign.tenant_id,
                    campaign_id=campaign_id,
                    step_id=step.step_id,
                    patient_id=patient.get("id", ""),
                    channel=channel,
                    status=MessageStatus.PENDING,
                    template_id=step.template_id,
                    personalized_content=personalized_content,
                    scheduled_at=scheduled_at
                )

                self.messages[message.message_id] = message
                messages.append(message)

        return messages

    def _check_cooldown(
        self,
        patient: dict[str, Any],
        campaign: Campaign
    ) -> bool:
        """Check if patient is within cooldown period"""
        patient_id = patient.get("id")
        prefs = self.patient_preferences.get(patient_id)

        if prefs and prefs.last_contact_date:
            days_since = (datetime.utcnow() - prefs.last_contact_date).days
            if days_since < campaign.schedule.cooldown_days:
                return False

        return True

    def _evaluate_step_condition(
        self,
        patient: dict[str, Any],
        condition: dict[str, Any]
    ) -> bool:
        """Evaluate step condition"""
        # Simple condition evaluation
        field = condition.get("field")
        operator = condition.get("operator", "equals")
        value = condition.get("value")

        patient_value = self._get_nested_value(patient, field)

        if operator == "equals":
            return patient_value == value
        elif operator == "not_equals":
            return patient_value != value
        elif operator == "exists":
            return patient_value is not None
        elif operator == "not_exists":
            return patient_value is None

        return True

    def _personalize_message(
        self,
        template: str,
        patient: dict[str, Any]
    ) -> str:
        """Personalize message with patient data"""
        import re

        def replace_variable(match):
            var_name = match.group(1)
            if var_name in self.personalization_functions:
                return str(self.personalization_functions[var_name](patient))
            return patient.get(var_name, match.group(0))

        return re.sub(r"\{\{(\w+)\}\}", replace_variable, template)

    def _calculate_send_time(
        self,
        schedule: CampaignSchedule,
        delay_days: int,
        delay_hours: int
    ) -> datetime:
        """Calculate message send time"""
        base_time = datetime.utcnow() + timedelta(days=delay_days, hours=delay_hours)

        # Adjust to next valid send day
        while base_time.weekday() not in schedule.send_days:
            base_time += timedelta(days=1)

        # Set to first valid send time
        if schedule.send_times:
            time_str = schedule.send_times[0]
            hour, minute = map(int, time_str.split(":"))
            base_time = base_time.replace(hour=hour, minute=minute, second=0)

        return base_time

    async def send_message(self, message_id: str) -> OutreachMessage:
        """Send a queued message"""
        message = self.messages.get(message_id)
        if not message:
            raise ValueError(f"Message not found: {message_id}")

        # Simulate sending based on channel
        await asyncio.sleep(0.1)

        message.status = MessageStatus.SENT
        message.sent_at = datetime.utcnow()

        # Simulate delivery for most messages
        if message.channel != OutreachChannel.MAIL:
            message.status = MessageStatus.DELIVERED
            message.delivered_at = datetime.utcnow()

        return message

    async def track_engagement(
        self,
        message_id: str,
        event_type: str,
        metadata: Optional[dict[str, Any]] = None
    ) -> OutreachMessage:
        """Track message engagement events"""
        message = self.messages.get(message_id)
        if not message:
            raise ValueError(f"Message not found: {message_id}")

        now = datetime.utcnow()

        if event_type == "opened":
            message.status = MessageStatus.OPENED
            message.opened_at = now
        elif event_type == "clicked":
            message.status = MessageStatus.CLICKED
            message.clicked_at = now
        elif event_type == "responded":
            message.status = MessageStatus.RESPONDED
            message.responded_at = now
            message.response_content = metadata.get("content") if metadata else None
        elif event_type == "bounced":
            message.status = MessageStatus.BOUNCED
            message.error_message = metadata.get("reason") if metadata else "Bounced"
        elif event_type == "opted_out":
            message.status = MessageStatus.OPTED_OUT

        return message

    async def set_patient_preferences(
        self,
        patient_id: str,
        preferred_channel: OutreachChannel,
        preferred_language: str = "en",
        preferred_time: Optional[str] = None,
        opted_out_channels: Optional[list[OutreachChannel]] = None,
        opted_out_types: Optional[list[CampaignType]] = None,
        do_not_contact: bool = False
    ) -> PatientPreferences:
        """Set patient communication preferences"""
        prefs = PatientPreferences(
            patient_id=patient_id,
            preferred_channel=preferred_channel,
            preferred_language=preferred_language,
            preferred_time=preferred_time,
            opted_out_channels=opted_out_channels or [],
            opted_out_types=opted_out_types or [],
            do_not_contact=do_not_contact
        )

        self.patient_preferences[patient_id] = prefs
        return prefs

    async def get_campaign_analytics(
        self,
        campaign_id: str
    ) -> CampaignAnalytics:
        """Get campaign performance analytics"""
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign not found: {campaign_id}")

        # Aggregate message stats
        campaign_messages = [
            m for m in self.messages.values()
            if m.campaign_id == campaign_id
        ]

        total = len(campaign_messages)
        sent = sum(1 for m in campaign_messages if m.sent_at)
        delivered = sum(1 for m in campaign_messages if m.delivered_at)
        opened = sum(1 for m in campaign_messages if m.opened_at)
        clicked = sum(1 for m in campaign_messages if m.clicked_at)
        responded = sum(1 for m in campaign_messages if m.responded_at)
        bounced = sum(1 for m in campaign_messages if m.status == MessageStatus.BOUNCED)
        opted_out = sum(1 for m in campaign_messages if m.status == MessageStatus.OPTED_OUT)

        # By channel breakdown
        by_channel = {}
        for channel in OutreachChannel:
            channel_msgs = [m for m in campaign_messages if m.channel == channel]
            if channel_msgs:
                by_channel[channel.value] = {
                    "sent": sum(1 for m in channel_msgs if m.sent_at),
                    "delivered": sum(1 for m in channel_msgs if m.delivered_at),
                    "opened": sum(1 for m in channel_msgs if m.opened_at),
                    "clicked": sum(1 for m in channel_msgs if m.clicked_at)
                }

        return CampaignAnalytics(
            campaign_id=campaign_id,
            total_targeted=total,
            total_sent=sent,
            total_delivered=delivered,
            total_opened=opened,
            total_clicked=clicked,
            total_responded=responded,
            total_bounced=bounced,
            total_opted_out=opted_out,
            delivery_rate=delivered / sent if sent > 0 else 0,
            open_rate=opened / delivered if delivered > 0 else 0,
            click_rate=clicked / delivered if delivered > 0 else 0,
            response_rate=responded / delivered if delivered > 0 else 0,
            cost=0.0,  # Would be calculated based on channel costs
            by_channel=by_channel
        )

    async def create_quick_campaign(
        self,
        tenant_id: str,
        campaign_type: CampaignType,
        patients: list[dict[str, Any]],
        message: str,
        channel: OutreachChannel = OutreachChannel.SMS,
        send_immediately: bool = True
    ) -> tuple[Campaign, list[OutreachMessage]]:
        """Create and optionally send a quick one-off campaign"""
        # Create segment
        segment = await self.create_segment(
            tenant_id=tenant_id,
            name=f"Quick Campaign - {datetime.utcnow().isoformat()}",
            description="Auto-generated segment for quick campaign",
            criteria=[{"field": "id", "operator": "in", "value": [p["id"] for p in patients]}],
            is_dynamic=False
        )

        # Create template
        template = await self.create_template(
            tenant_id=tenant_id,
            name=f"Quick Template - {datetime.utcnow().isoformat()}",
            channel=channel,
            body=message
        )

        # Create campaign
        campaign = await self.create_campaign(
            tenant_id=tenant_id,
            name=f"Quick Campaign - {campaign_type.value}",
            description="Quick one-off campaign",
            campaign_type=campaign_type,
            segment_id=segment.segment_id,
            steps=[{
                "name": "Send Message",
                "channel": channel.value,
                "template_id": template.template_id
            }],
            schedule={
                "start_date": datetime.utcnow(),
                "send_times": ["09:00"],
                "send_days": [0, 1, 2, 3, 4, 5, 6]
            }
        )

        messages = []
        if send_immediately:
            campaign = await self.activate_campaign(campaign.campaign_id)
            messages = await self.execute_campaign(campaign.campaign_id, patients)

            # Send all messages
            for msg in messages:
                await self.send_message(msg.message_id)

        return campaign, messages

    def register_personalization(self, name: str, func: callable):
        """Register custom personalization function"""
        self.personalization_functions[name] = func

    async def list_campaigns(
        self,
        tenant_id: str,
        status: Optional[CampaignStatus] = None,
        campaign_type: Optional[CampaignType] = None
    ) -> list[Campaign]:
        """List campaigns for tenant"""
        campaigns = [
            c for c in self.campaigns.values()
            if c.tenant_id == tenant_id
        ]

        if status:
            campaigns = [c for c in campaigns if c.status == status]
        if campaign_type:
            campaigns = [c for c in campaigns if c.campaign_type == campaign_type]

        return sorted(campaigns, key=lambda x: x.created_at, reverse=True)


# Pre-built campaign templates
class CampaignTemplates:
    """Pre-built campaign templates for common use cases"""

    @staticmethod
    def appointment_reminder(days_before: int = 1) -> dict[str, Any]:
        """Appointment reminder campaign template"""
        return {
            "name": f"Appointment Reminder - {days_before} Day(s)",
            "campaign_type": CampaignType.APPOINTMENT_REMINDER,
            "steps": [
                {
                    "name": "SMS Reminder",
                    "channel": "sms",
                    "delay_days": -days_before,
                    "template_body": "Hi {{first_name}}, this is a reminder about your appointment with {{provider_name}} on {{appointment_date}} at {{appointment_time}}. Reply C to confirm or R to reschedule."
                }
            ]
        }

    @staticmethod
    def preventive_care_outreach() -> dict[str, Any]:
        """Preventive care outreach campaign template"""
        return {
            "name": "Preventive Care Outreach",
            "campaign_type": CampaignType.PREVENTIVE_CARE,
            "steps": [
                {
                    "name": "Initial Email",
                    "channel": "email",
                    "delay_days": 0,
                    "template_body": "Dear {{patient_name}},\n\nOur records show you're due for {{care_gap}}. Schedule your appointment today!\n\n{{portal_link}}"
                },
                {
                    "name": "SMS Follow-up",
                    "channel": "sms",
                    "delay_days": 7,
                    "template_body": "Hi {{first_name}}, just a reminder - you're due for {{care_gap}}. Call us to schedule or visit {{portal_link}}"
                },
                {
                    "name": "Final Reminder",
                    "channel": "voice",
                    "delay_days": 14,
                    "template_body": "Voice call reminder for preventive care appointment"
                }
            ]
        }

    @staticmethod
    def patient_reactivation() -> dict[str, Any]:
        """Patient reactivation campaign template"""
        return {
            "name": "Patient Reactivation",
            "campaign_type": CampaignType.REACTIVATION,
            "steps": [
                {
                    "name": "We Miss You Email",
                    "channel": "email",
                    "delay_days": 0,
                    "template_body": "Dear {{patient_name}},\n\nWe haven't seen you in a while. It's time for your regular checkup!\n\nSchedule now: {{portal_link}}"
                },
                {
                    "name": "SMS with Offer",
                    "channel": "sms",
                    "delay_days": 14,
                    "template_body": "{{first_name}}, we'd love to see you! Schedule your appointment this month and receive a free wellness consultation. {{portal_link}}"
                }
            ]
        }

    @staticmethod
    def post_visit_followup() -> dict[str, Any]:
        """Post-visit follow-up campaign template"""
        return {
            "name": "Post-Visit Follow-up",
            "campaign_type": CampaignType.POST_VISIT,
            "steps": [
                {
                    "name": "Thank You SMS",
                    "channel": "sms",
                    "delay_days": 1,
                    "template_body": "Thank you for visiting {{location}} yesterday, {{first_name}}! If you have any questions about your visit, please call us."
                },
                {
                    "name": "Satisfaction Survey",
                    "channel": "email",
                    "delay_days": 3,
                    "template_body": "Dear {{patient_name}},\n\nWe value your feedback! Please take a moment to rate your recent visit.\n\n{{survey_link}}"
                }
            ]
        }


# Singleton instance
_outreach_engine: Optional[PatientOutreachEngine] = None


def get_outreach_engine() -> PatientOutreachEngine:
    """Get singleton outreach engine instance"""
    global _outreach_engine
    if _outreach_engine is None:
        _outreach_engine = PatientOutreachEngine()
    return _outreach_engine
