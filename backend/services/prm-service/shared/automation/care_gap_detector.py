"""
Automated Care Gap Detection & Intervention
EPIC-012: Intelligent Automation Platform - US-012.3

Provides:
- Real-time care gap detection
- Preventive care gap analysis
- Medication adherence gaps
- Follow-up appointment gaps
- Automated interventions and outreach
- Priority-based intervention scheduling
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Callable
from uuid import uuid4


class CareGapType(Enum):
    """Types of care gaps"""
    PREVENTIVE_SCREENING = "preventive_screening"
    VACCINATION = "vaccination"
    CHRONIC_DISEASE_MONITORING = "chronic_disease_monitoring"
    MEDICATION_ADHERENCE = "medication_adherence"
    FOLLOW_UP_APPOINTMENT = "follow_up_appointment"
    LAB_TEST = "lab_test"
    IMAGING = "imaging"
    SPECIALIST_REFERRAL = "specialist_referral"
    ANNUAL_WELLNESS = "annual_wellness"
    DENTAL = "dental"
    VISION = "vision"
    MENTAL_HEALTH = "mental_health"


class CareGapPriority(Enum):
    """Care gap priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CareGapStatus(Enum):
    """Care gap status"""
    OPEN = "open"
    OUTREACH_SCHEDULED = "outreach_scheduled"
    OUTREACH_IN_PROGRESS = "outreach_in_progress"
    APPOINTMENT_SCHEDULED = "appointment_scheduled"
    COMPLETED = "completed"
    PATIENT_DECLINED = "patient_declined"
    NOT_APPLICABLE = "not_applicable"
    EXPIRED = "expired"


class InterventionChannel(Enum):
    """Intervention communication channels"""
    PATIENT_PORTAL = "patient_portal"
    SMS = "sms"
    EMAIL = "email"
    PHONE_CALL = "phone_call"
    MAIL = "mail"
    PROVIDER_ALERT = "provider_alert"
    CARE_TEAM_ALERT = "care_team_alert"


@dataclass
class CareGapRule:
    """Rule for detecting care gaps"""
    rule_id: str
    name: str
    description: str
    gap_type: CareGapType
    measure_id: Optional[str]  # Quality measure ID (e.g., HEDIS, NQF)

    # Eligibility criteria
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    gender: Optional[str] = None  # M, F, or None for both
    conditions: List[str] = field(default_factory=list)  # Required conditions
    exclusion_conditions: List[str] = field(default_factory=list)

    # Gap criteria
    service_codes: List[str] = field(default_factory=list)  # CPT, LOINC, etc.
    interval_days: int = 365  # How often the service is needed
    lookback_days: int = 365  # How far back to look for completed service

    # Priority
    priority: CareGapPriority = CareGapPriority.MEDIUM
    clinical_urgency_score: float = 0.5

    # Enabled
    is_active: bool = True


@dataclass
class DetectedCareGap:
    """A detected care gap for a patient"""
    gap_id: str
    patient_id: str
    rule_id: str
    gap_type: CareGapType
    gap_name: str
    description: str
    measure_id: Optional[str]

    # Status
    status: CareGapStatus = CareGapStatus.OPEN
    priority: CareGapPriority = CareGapPriority.MEDIUM

    # Dates
    detected_date: date = field(default_factory=date.today)
    due_date: Optional[date] = None
    last_service_date: Optional[date] = None
    days_overdue: int = 0

    # Intervention
    recommended_intervention: Optional[str] = None
    assigned_provider_id: Optional[str] = None
    outreach_attempts: int = 0
    last_outreach_date: Optional[date] = None
    next_outreach_date: Optional[date] = None

    # Resolution
    closed_date: Optional[date] = None
    closed_reason: Optional[str] = None

    # Financial
    estimated_revenue: float = 0.0
    quality_points: float = 0.0

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InterventionAction:
    """Automated intervention action"""
    action_id: str
    gap_id: str
    patient_id: str
    channel: InterventionChannel
    action_type: str  # reminder, education, scheduling, provider_alert

    # Content
    template_id: str
    template_data: Dict[str, Any] = field(default_factory=dict)

    # Scheduling
    scheduled_datetime: datetime = field(default_factory=datetime.utcnow)
    executed_datetime: Optional[datetime] = None

    # Status
    status: str = "scheduled"  # scheduled, sent, delivered, responded, failed
    response: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InterventionCampaign:
    """Campaign for closing care gaps"""
    campaign_id: str
    name: str
    description: str
    gap_type: CareGapType

    # Target
    target_patient_count: int = 0
    target_closure_rate: float = 0.5

    # Channels
    channels: List[InterventionChannel] = field(default_factory=list)
    channel_sequence: List[InterventionChannel] = field(default_factory=list)

    # Timing
    start_date: date = field(default_factory=date.today)
    end_date: Optional[date] = None
    outreach_interval_days: int = 7
    max_outreach_attempts: int = 3

    # Status
    status: str = "draft"  # draft, active, paused, completed

    # Results
    patients_contacted: int = 0
    gaps_closed: int = 0
    response_rate: float = 0.0


class CareGapDetector:
    """
    Automated care gap detection and intervention engine.
    Identifies care gaps and orchestrates closing interventions.
    """

    def __init__(self):
        self.rules: Dict[str, CareGapRule] = {}
        self.detected_gaps: Dict[str, DetectedCareGap] = {}
        self.interventions: Dict[str, InterventionAction] = {}
        self.campaigns: Dict[str, InterventionCampaign] = {}
        self._setup_default_rules()

    def _setup_default_rules(self):
        """Setup default care gap detection rules"""
        default_rules = [
            # Preventive screenings
            CareGapRule(
                rule_id="hba1c_screening",
                name="HbA1c Screening for Diabetics",
                description="HbA1c test every 6 months for diabetic patients",
                gap_type=CareGapType.LAB_TEST,
                measure_id="NQF0059",
                conditions=["diabetes"],
                service_codes=["83036"],
                interval_days=180,
                priority=CareGapPriority.HIGH,
                clinical_urgency_score=0.8
            ),
            CareGapRule(
                rule_id="mammogram_screening",
                name="Breast Cancer Screening",
                description="Annual mammogram for women 50-74",
                gap_type=CareGapType.PREVENTIVE_SCREENING,
                measure_id="NQF2372",
                age_min=50,
                age_max=74,
                gender="F",
                service_codes=["77067"],
                interval_days=365,
                priority=CareGapPriority.HIGH,
                clinical_urgency_score=0.7
            ),
            CareGapRule(
                rule_id="colonoscopy_screening",
                name="Colorectal Cancer Screening",
                description="Colonoscopy every 10 years for adults 50-75",
                gap_type=CareGapType.PREVENTIVE_SCREENING,
                measure_id="NQF0034",
                age_min=50,
                age_max=75,
                service_codes=["45378", "45380", "45381"],
                interval_days=3650,  # 10 years
                priority=CareGapPriority.HIGH,
                clinical_urgency_score=0.7
            ),
            CareGapRule(
                rule_id="flu_vaccination",
                name="Annual Flu Vaccination",
                description="Annual influenza vaccination for all patients",
                gap_type=CareGapType.VACCINATION,
                measure_id="NQF0041",
                service_codes=["90686", "90688"],
                interval_days=365,
                priority=CareGapPriority.MEDIUM,
                clinical_urgency_score=0.5
            ),
            CareGapRule(
                rule_id="annual_wellness",
                name="Annual Wellness Visit",
                description="Annual preventive wellness visit",
                gap_type=CareGapType.ANNUAL_WELLNESS,
                measure_id="AWV001",
                age_min=18,
                service_codes=["G0438", "G0439"],
                interval_days=365,
                priority=CareGapPriority.MEDIUM,
                clinical_urgency_score=0.4
            ),
            CareGapRule(
                rule_id="eye_exam_diabetics",
                name="Diabetic Eye Exam",
                description="Annual retinal eye exam for diabetics",
                gap_type=CareGapType.CHRONIC_DISEASE_MONITORING,
                measure_id="NQF0055",
                conditions=["diabetes"],
                service_codes=["92004", "92014", "2022F"],
                interval_days=365,
                priority=CareGapPriority.HIGH,
                clinical_urgency_score=0.75
            ),
            CareGapRule(
                rule_id="bp_control",
                name="Blood Pressure Control",
                description="Blood pressure monitoring for hypertensive patients",
                gap_type=CareGapType.CHRONIC_DISEASE_MONITORING,
                measure_id="NQF0018",
                conditions=["hypertension"],
                interval_days=90,
                priority=CareGapPriority.HIGH,
                clinical_urgency_score=0.8
            ),
            CareGapRule(
                rule_id="statin_adherence",
                name="Statin Therapy Adherence",
                description="Statin adherence for cardiovascular patients",
                gap_type=CareGapType.MEDICATION_ADHERENCE,
                measure_id="NQF0543",
                conditions=["cardiovascular_disease", "diabetes"],
                interval_days=365,
                priority=CareGapPriority.HIGH,
                clinical_urgency_score=0.7
            ),
            CareGapRule(
                rule_id="depression_screening",
                name="Depression Screening",
                description="Annual depression screening",
                gap_type=CareGapType.MENTAL_HEALTH,
                measure_id="NQF0418",
                age_min=12,
                service_codes=["G8431", "G8510"],
                interval_days=365,
                priority=CareGapPriority.MEDIUM,
                clinical_urgency_score=0.6
            ),
        ]

        for rule in default_rules:
            self.rules[rule.rule_id] = rule

    # ==================== Rule Management ====================

    def add_rule(self, rule: CareGapRule) -> str:
        """Add a care gap detection rule"""
        self.rules[rule.rule_id] = rule
        return rule.rule_id

    def update_rule(self, rule_id: str, rule: CareGapRule) -> bool:
        """Update an existing rule"""
        if rule_id in self.rules:
            self.rules[rule_id] = rule
            return True
        return False

    def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            return True
        return False

    def get_rule(self, rule_id: str) -> Optional[CareGapRule]:
        """Get a rule by ID"""
        return self.rules.get(rule_id)

    def list_rules(
        self,
        gap_type: Optional[CareGapType] = None,
        is_active: Optional[bool] = None
    ) -> List[CareGapRule]:
        """List rules with optional filtering"""
        rules = list(self.rules.values())

        if gap_type:
            rules = [r for r in rules if r.gap_type == gap_type]

        if is_active is not None:
            rules = [r for r in rules if r.is_active == is_active]

        return rules

    # ==================== Gap Detection ====================

    async def detect_gaps_for_patient(
        self,
        patient_id: str,
        patient_data: Dict[str, Any]
    ) -> List[DetectedCareGap]:
        """Detect all care gaps for a patient"""
        detected = []

        for rule in self.rules.values():
            if not rule.is_active:
                continue

            # Check eligibility
            if not self._check_eligibility(rule, patient_data):
                continue

            # Check if gap exists
            gap = await self._evaluate_gap(rule, patient_id, patient_data)
            if gap:
                detected.append(gap)
                self.detected_gaps[gap.gap_id] = gap

        return detected

    def _check_eligibility(self, rule: CareGapRule, patient_data: Dict) -> bool:
        """Check if patient is eligible for this care gap rule"""
        # Age check
        patient_age = patient_data.get("age")
        if patient_age is not None:
            if rule.age_min and patient_age < rule.age_min:
                return False
            if rule.age_max and patient_age > rule.age_max:
                return False

        # Gender check
        if rule.gender:
            patient_gender = patient_data.get("gender", "").upper()
            if patient_gender and patient_gender != rule.gender:
                return False

        # Condition check
        patient_conditions = patient_data.get("conditions", [])
        if rule.conditions:
            if not any(c in patient_conditions for c in rule.conditions):
                return False

        # Exclusion check
        if rule.exclusion_conditions:
            if any(c in patient_conditions for c in rule.exclusion_conditions):
                return False

        return True

    async def _evaluate_gap(
        self,
        rule: CareGapRule,
        patient_id: str,
        patient_data: Dict
    ) -> Optional[DetectedCareGap]:
        """Evaluate if a care gap exists for this rule"""
        # Check for recent service completion
        services_history = patient_data.get("services", [])
        last_service_date = None

        for service in services_history:
            service_code = service.get("code")
            service_date = service.get("date")

            if service_code in rule.service_codes:
                if isinstance(service_date, str):
                    service_date = date.fromisoformat(service_date)
                if last_service_date is None or service_date > last_service_date:
                    last_service_date = service_date

        # Calculate due date and check if gap exists
        today = date.today()

        if last_service_date:
            due_date = last_service_date + timedelta(days=rule.interval_days)
            if due_date > today:
                # Service not yet due
                return None
            days_overdue = (today - due_date).days
        else:
            # Never had the service
            due_date = today
            days_overdue = rule.interval_days

        # Create care gap
        return DetectedCareGap(
            gap_id=str(uuid4()),
            patient_id=patient_id,
            rule_id=rule.rule_id,
            gap_type=rule.gap_type,
            gap_name=rule.name,
            description=rule.description,
            measure_id=rule.measure_id,
            priority=rule.priority,
            due_date=due_date,
            last_service_date=last_service_date,
            days_overdue=days_overdue,
            clinical_urgency_score=rule.clinical_urgency_score,
            estimated_revenue=self._estimate_revenue(rule),
            quality_points=self._estimate_quality_points(rule)
        )

    def _estimate_revenue(self, rule: CareGapRule) -> float:
        """Estimate potential revenue for closing the gap"""
        # Simplified revenue estimation
        revenue_by_type = {
            CareGapType.PREVENTIVE_SCREENING: 150.0,
            CareGapType.LAB_TEST: 75.0,
            CareGapType.VACCINATION: 50.0,
            CareGapType.ANNUAL_WELLNESS: 200.0,
            CareGapType.CHRONIC_DISEASE_MONITORING: 125.0,
            CareGapType.SPECIALIST_REFERRAL: 250.0,
            CareGapType.IMAGING: 300.0,
        }
        return revenue_by_type.get(rule.gap_type, 100.0)

    def _estimate_quality_points(self, rule: CareGapRule) -> float:
        """Estimate quality measure points for closing the gap"""
        if rule.measure_id:
            return 1.0
        return 0.5

    # ==================== Gap Management ====================

    async def get_patient_gaps(
        self,
        patient_id: str,
        status: Optional[CareGapStatus] = None,
        priority: Optional[CareGapPriority] = None
    ) -> List[DetectedCareGap]:
        """Get care gaps for a patient"""
        gaps = [g for g in self.detected_gaps.values() if g.patient_id == patient_id]

        if status:
            gaps = [g for g in gaps if g.status == status]

        if priority:
            gaps = [g for g in gaps if g.priority == priority]

        # Sort by priority and days overdue
        priority_order = {
            CareGapPriority.CRITICAL: 0,
            CareGapPriority.HIGH: 1,
            CareGapPriority.MEDIUM: 2,
            CareGapPriority.LOW: 3
        }
        gaps.sort(key=lambda x: (priority_order.get(x.priority, 4), -x.days_overdue))

        return gaps

    async def update_gap_status(
        self,
        gap_id: str,
        status: CareGapStatus,
        reason: Optional[str] = None
    ) -> bool:
        """Update care gap status"""
        gap = self.detected_gaps.get(gap_id)
        if not gap:
            return False

        gap.status = status

        if status == CareGapStatus.COMPLETED:
            gap.closed_date = date.today()
            gap.closed_reason = reason or "Service completed"
        elif status == CareGapStatus.PATIENT_DECLINED:
            gap.closed_date = date.today()
            gap.closed_reason = reason or "Patient declined"

        return True

    async def close_gap(
        self,
        gap_id: str,
        service_date: date,
        service_code: Optional[str] = None
    ) -> bool:
        """Close a care gap as completed"""
        gap = self.detected_gaps.get(gap_id)
        if not gap:
            return False

        gap.status = CareGapStatus.COMPLETED
        gap.closed_date = date.today()
        gap.closed_reason = f"Service completed on {service_date.isoformat()}"
        gap.metadata["service_date"] = service_date.isoformat()
        if service_code:
            gap.metadata["service_code"] = service_code

        return True

    # ==================== Automated Interventions ====================

    async def schedule_intervention(
        self,
        gap_id: str,
        channel: InterventionChannel,
        template_id: str,
        scheduled_datetime: datetime,
        template_data: Optional[Dict] = None
    ) -> str:
        """Schedule an automated intervention"""
        gap = self.detected_gaps.get(gap_id)
        if not gap:
            raise ValueError(f"Care gap {gap_id} not found")

        action = InterventionAction(
            action_id=str(uuid4()),
            gap_id=gap_id,
            patient_id=gap.patient_id,
            channel=channel,
            action_type="outreach",
            template_id=template_id,
            template_data=template_data or {},
            scheduled_datetime=scheduled_datetime
        )

        self.interventions[action.action_id] = action

        # Update gap
        gap.status = CareGapStatus.OUTREACH_SCHEDULED
        gap.next_outreach_date = scheduled_datetime.date()

        return action.action_id

    async def execute_intervention(self, action_id: str) -> Dict[str, Any]:
        """Execute a scheduled intervention"""
        action = self.interventions.get(action_id)
        if not action:
            raise ValueError(f"Intervention {action_id} not found")

        # In production, this would send actual communications
        result = {
            "action_id": action_id,
            "channel": action.channel.value,
            "status": "sent",
            "sent_datetime": datetime.utcnow().isoformat()
        }

        action.executed_datetime = datetime.utcnow()
        action.status = "sent"

        # Update gap
        gap = self.detected_gaps.get(action.gap_id)
        if gap:
            gap.outreach_attempts += 1
            gap.last_outreach_date = date.today()
            gap.status = CareGapStatus.OUTREACH_IN_PROGRESS

        return result

    async def generate_intervention_plan(
        self,
        gap_id: str,
        patient_preferences: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Generate an intervention plan for a care gap"""
        gap = self.detected_gaps.get(gap_id)
        if not gap:
            return []

        prefs = patient_preferences or {}
        preferred_channels = prefs.get("communication_channels", ["email", "sms"])

        plan = []

        # Day 0: Initial outreach
        plan.append({
            "day": 0,
            "channel": preferred_channels[0] if preferred_channels else "email",
            "action": "initial_reminder",
            "template": f"care_gap_reminder_{gap.gap_type.value}"
        })

        # Day 7: Follow-up if high priority
        if gap.priority in [CareGapPriority.CRITICAL, CareGapPriority.HIGH]:
            plan.append({
                "day": 7,
                "channel": preferred_channels[1] if len(preferred_channels) > 1 else "sms",
                "action": "follow_up_reminder",
                "template": f"care_gap_urgent_{gap.gap_type.value}"
            })

        # Day 14: Phone call for high priority
        if gap.priority == CareGapPriority.CRITICAL:
            plan.append({
                "day": 14,
                "channel": "phone_call",
                "action": "phone_outreach",
                "template": "care_gap_phone_script"
            })

        # Day 21: Provider alert
        if gap.days_overdue > 60:
            plan.append({
                "day": 21,
                "channel": "provider_alert",
                "action": "provider_notification",
                "template": "provider_care_gap_alert"
            })

        return plan

    # ==================== Campaign Management ====================

    async def create_campaign(self, campaign: InterventionCampaign) -> str:
        """Create an intervention campaign"""
        self.campaigns[campaign.campaign_id] = campaign
        return campaign.campaign_id

    async def start_campaign(self, campaign_id: str) -> bool:
        """Start an intervention campaign"""
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            return False

        campaign.status = "active"
        return True

    async def get_campaign_gaps(
        self,
        campaign_id: str,
        limit: int = 100
    ) -> List[DetectedCareGap]:
        """Get care gaps that match a campaign"""
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            return []

        matching_gaps = [
            g for g in self.detected_gaps.values()
            if g.gap_type == campaign.gap_type and g.status == CareGapStatus.OPEN
        ]

        # Sort by priority and days overdue
        matching_gaps.sort(key=lambda x: (-x.days_overdue, x.priority.value))

        return matching_gaps[:limit]

    async def process_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Process a campaign - schedule interventions for matching gaps"""
        campaign = self.campaigns.get(campaign_id)
        if not campaign or campaign.status != "active":
            return {"error": "Campaign not active"}

        gaps = await self.get_campaign_gaps(campaign_id)
        scheduled_count = 0

        for gap in gaps:
            if gap.outreach_attempts >= campaign.max_outreach_attempts:
                continue

            # Determine channel based on sequence
            channel_idx = gap.outreach_attempts % len(campaign.channel_sequence)
            channel = campaign.channel_sequence[channel_idx] if campaign.channel_sequence else campaign.channels[0]

            # Schedule intervention
            scheduled_time = datetime.utcnow() + timedelta(hours=1)
            await self.schedule_intervention(
                gap_id=gap.gap_id,
                channel=channel,
                template_id=f"campaign_{campaign_id}_{channel.value}",
                scheduled_datetime=scheduled_time
            )
            scheduled_count += 1

        campaign.patients_contacted = scheduled_count

        return {
            "campaign_id": campaign_id,
            "gaps_processed": len(gaps),
            "interventions_scheduled": scheduled_count
        }

    # ==================== Analytics ====================

    async def get_gap_summary(
        self,
        tenant_id: Optional[str] = None,
        provider_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get summary of care gaps"""
        gaps = list(self.detected_gaps.values())

        # Filter if needed
        if provider_id:
            gaps = [g for g in gaps if g.assigned_provider_id == provider_id]

        total_gaps = len(gaps)
        open_gaps = len([g for g in gaps if g.status == CareGapStatus.OPEN])
        closed_gaps = len([g for g in gaps if g.status == CareGapStatus.COMPLETED])

        # By type
        by_type = {}
        for gap in gaps:
            gap_type = gap.gap_type.value
            if gap_type not in by_type:
                by_type[gap_type] = {"total": 0, "open": 0, "closed": 0}
            by_type[gap_type]["total"] += 1
            if gap.status == CareGapStatus.OPEN:
                by_type[gap_type]["open"] += 1
            elif gap.status == CareGapStatus.COMPLETED:
                by_type[gap_type]["closed"] += 1

        # By priority
        by_priority = {}
        for gap in gaps:
            priority = gap.priority.value
            if priority not in by_priority:
                by_priority[priority] = 0
            by_priority[priority] += 1

        # Financial impact
        total_potential_revenue = sum(g.estimated_revenue for g in gaps if g.status == CareGapStatus.OPEN)
        total_quality_points = sum(g.quality_points for g in gaps if g.status == CareGapStatus.OPEN)

        return {
            "total_gaps": total_gaps,
            "open_gaps": open_gaps,
            "closed_gaps": closed_gaps,
            "closure_rate": closed_gaps / total_gaps if total_gaps > 0 else 0,
            "by_type": by_type,
            "by_priority": by_priority,
            "potential_revenue": total_potential_revenue,
            "potential_quality_points": total_quality_points,
            "average_days_overdue": sum(g.days_overdue for g in gaps) / len(gaps) if gaps else 0
        }

    async def get_high_impact_gaps(
        self,
        limit: int = 50
    ) -> List[DetectedCareGap]:
        """Get high-impact care gaps for prioritization"""
        open_gaps = [
            g for g in self.detected_gaps.values()
            if g.status == CareGapStatus.OPEN
        ]

        # Score each gap by impact
        def impact_score(gap: DetectedCareGap) -> float:
            priority_weight = {
                CareGapPriority.CRITICAL: 4,
                CareGapPriority.HIGH: 3,
                CareGapPriority.MEDIUM: 2,
                CareGapPriority.LOW: 1
            }
            return (
                priority_weight.get(gap.priority, 1) * 10 +
                gap.estimated_revenue * 0.1 +
                gap.quality_points * 5 +
                min(gap.days_overdue, 365) * 0.05
            )

        open_gaps.sort(key=impact_score, reverse=True)
        return open_gaps[:limit]


# Singleton instance
care_gap_detector = CareGapDetector()


def get_care_gap_detector() -> CareGapDetector:
    """Get the singleton care gap detector instance"""
    return care_gap_detector
