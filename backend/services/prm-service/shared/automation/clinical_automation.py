"""
Clinical Task Automation Service

Automates clinical workflows including lab result triage,
medication refills, referral processing, and care coordination.

Part of EPIC-012: Intelligent Automation Platform
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


class ClinicalTaskType(str, Enum):
    """Types of clinical tasks"""
    LAB_REVIEW = "lab_review"
    LAB_CRITICAL = "lab_critical"
    MEDICATION_REFILL = "medication_refill"
    PRIOR_AUTH = "prior_auth"
    REFERRAL_PROCESSING = "referral_processing"
    PRESCRIPTION_RENEWAL = "prescription_renewal"
    PATIENT_MESSAGE = "patient_message"
    DOCUMENT_REVIEW = "document_review"
    ORDER_FOLLOWUP = "order_followup"
    CARE_COORDINATION = "care_coordination"
    IMMUNIZATION_DUE = "immunization_due"
    QUALITY_MEASURE = "quality_measure"


class TaskPriority(str, Enum):
    """Task priority levels"""
    STAT = "stat"  # Immediate
    URGENT = "urgent"  # Within hours
    HIGH = "high"  # Same day
    NORMAL = "normal"  # Within 24-48 hours
    LOW = "low"  # Within week


class TaskStatus(str, Enum):
    """Task lifecycle status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED = "approved"
    COMPLETED = "completed"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    CANCELLED = "cancelled"


class LabResultStatus(str, Enum):
    """Lab result classification"""
    NORMAL = "normal"
    ABNORMAL = "abnormal"
    CRITICAL = "critical"
    PENDING = "pending"


class RefillStatus(str, Enum):
    """Medication refill status"""
    REQUESTED = "requested"
    AUTO_APPROVED = "auto_approved"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    DENIED = "denied"
    SENT_TO_PHARMACY = "sent_to_pharmacy"
    FILLED = "filled"
    CANCELLED = "cancelled"


class ReferralStatus(str, Enum):
    """Referral processing status"""
    RECEIVED = "received"
    REVIEWING = "reviewing"
    PENDING_AUTH = "pending_auth"
    AUTHORIZED = "authorized"
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    DENIED = "denied"
    CANCELLED = "cancelled"


@dataclass
class LabResult:
    """Lab result for triage"""
    result_id: str
    patient_id: str
    test_code: str
    test_name: str
    value: float
    unit: str
    reference_low: Optional[float]
    reference_high: Optional[float]
    status: LabResultStatus
    collected_date: datetime
    reported_date: datetime
    ordering_provider_id: str
    is_critical: bool = False
    critical_notified: bool = False
    interpretation: Optional[str] = None
    previous_value: Optional[float] = None
    trend: Optional[str] = None  # increasing, decreasing, stable


@dataclass
class LabTriageRule:
    """Rule for lab result triage"""
    rule_id: str
    test_code: str
    test_name: str
    critical_low: Optional[float] = None
    critical_high: Optional[float] = None
    abnormal_low: Optional[float] = None
    abnormal_high: Optional[float] = None
    auto_notify_critical: bool = True
    auto_notify_abnormal: bool = False
    escalation_minutes: int = 30
    required_actions: list[str] = field(default_factory=list)


@dataclass
class MedicationRefillRequest:
    """Medication refill request"""
    request_id: str
    tenant_id: str
    patient_id: str
    medication_name: str
    medication_id: Optional[str]
    strength: str
    quantity: int
    days_supply: int
    refills_remaining: int
    last_fill_date: Optional[datetime]
    prescriber_id: str
    pharmacy_id: Optional[str]
    status: RefillStatus
    requested_at: datetime
    processed_at: Optional[datetime] = None
    processed_by: Optional[str] = None
    denial_reason: Optional[str] = None
    notes: Optional[str] = None
    is_controlled: bool = False
    requires_review: bool = False


@dataclass
class RefillAutoApprovalRule:
    """Rule for auto-approving refills"""
    rule_id: str
    medication_class: Optional[str] = None
    medication_name: Optional[str] = None
    max_days_since_visit: int = 365
    min_refills_remaining: int = 1
    require_recent_labs: bool = False
    required_lab_tests: list[str] = field(default_factory=list)
    max_lab_age_days: int = 90
    exclude_controlled: bool = True
    exclude_high_risk: bool = True
    active: bool = True


@dataclass
class Referral:
    """Patient referral"""
    referral_id: str
    tenant_id: str
    patient_id: str
    referring_provider_id: str
    specialty: str
    referred_to_provider_id: Optional[str]
    referred_to_organization: Optional[str]
    reason: str
    diagnosis_codes: list[str]
    urgency: TaskPriority
    status: ReferralStatus
    created_at: datetime
    auth_required: bool = False
    auth_number: Optional[str] = None
    auth_expiry: Optional[datetime] = None
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    notes: Optional[str] = None
    clinical_notes: Optional[str] = None
    attachments: list[str] = field(default_factory=list)


@dataclass
class ClinicalTask:
    """A clinical task requiring action"""
    task_id: str
    tenant_id: str
    task_type: ClinicalTaskType
    priority: TaskPriority
    status: TaskStatus
    patient_id: str
    provider_id: Optional[str]
    assigned_to: Optional[str]
    assigned_role: Optional[str]
    title: str
    description: str
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    completed_by: Optional[str] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[str] = None
    auto_action_taken: Optional[str] = None
    escalation_level: int = 0
    notes: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AutomationAction:
    """Action taken by automation"""
    action_id: str
    task_id: str
    action_type: str
    action_data: dict[str, Any]
    performed_at: datetime
    success: bool
    result_message: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None


class ClinicalTaskAutomation:
    """
    Clinical task automation engine.
    Handles lab triage, medication refills, referrals, and care coordination.
    """

    def __init__(self):
        self.tasks: dict[str, ClinicalTask] = {}
        self.lab_triage_rules: dict[str, LabTriageRule] = {}
        self.refill_approval_rules: list[RefillAutoApprovalRule] = []
        self.refill_requests: dict[str, MedicationRefillRequest] = {}
        self.referrals: dict[str, Referral] = {}
        self.automation_actions: dict[str, AutomationAction] = {}
        self._initialize_default_rules()

    def _initialize_default_rules(self):
        """Initialize default clinical rules"""
        # Lab triage rules for common tests
        self._add_lab_rule("GLU", "Glucose", 40, 500, 70, 100)
        self._add_lab_rule("K", "Potassium", 2.5, 6.5, 3.5, 5.0)
        self._add_lab_rule("NA", "Sodium", 120, 160, 136, 145)
        self._add_lab_rule("HGB", "Hemoglobin", 7.0, 20.0, 12.0, 17.5)
        self._add_lab_rule("PLT", "Platelets", 50, 1000, 150, 400)
        self._add_lab_rule("WBC", "White Blood Cells", 2.0, 30.0, 4.5, 11.0)
        self._add_lab_rule("CREAT", "Creatinine", None, 10.0, 0.7, 1.3)
        self._add_lab_rule("TROP", "Troponin", None, 0.04, None, 0.01)
        self._add_lab_rule("HBA1C", "Hemoglobin A1c", None, None, None, 5.7)
        self._add_lab_rule("TSH", "Thyroid Stimulating Hormone", None, None, 0.4, 4.0)
        self._add_lab_rule("INR", "INR", None, 5.0, 0.9, 1.1)

        # Default refill auto-approval rules
        self.refill_approval_rules = [
            RefillAutoApprovalRule(
                rule_id="maintenance-meds",
                medication_class="maintenance",
                max_days_since_visit=365,
                min_refills_remaining=1,
                exclude_controlled=True
            ),
            RefillAutoApprovalRule(
                rule_id="diabetes-with-labs",
                medication_class="antidiabetic",
                max_days_since_visit=180,
                require_recent_labs=True,
                required_lab_tests=["HBA1C"],
                max_lab_age_days=90
            ),
            RefillAutoApprovalRule(
                rule_id="hypertension",
                medication_class="antihypertensive",
                max_days_since_visit=365,
                min_refills_remaining=0  # Allow even with 0 refills
            ),
            RefillAutoApprovalRule(
                rule_id="thyroid",
                medication_class="thyroid",
                require_recent_labs=True,
                required_lab_tests=["TSH"],
                max_lab_age_days=180
            )
        ]

    def _add_lab_rule(
        self,
        code: str,
        name: str,
        crit_low: Optional[float],
        crit_high: Optional[float],
        abnormal_low: Optional[float],
        abnormal_high: Optional[float]
    ):
        """Add a lab triage rule"""
        rule = LabTriageRule(
            rule_id=code,
            test_code=code,
            test_name=name,
            critical_low=crit_low,
            critical_high=crit_high,
            abnormal_low=abnormal_low,
            abnormal_high=abnormal_high
        )
        self.lab_triage_rules[code] = rule

    async def triage_lab_result(
        self,
        tenant_id: str,
        result: LabResult
    ) -> tuple[LabResult, Optional[ClinicalTask]]:
        """Triage a lab result and create task if needed"""
        rule = self.lab_triage_rules.get(result.test_code)

        if not rule:
            # No rule - mark as normal unless obviously abnormal
            if result.reference_high and result.value > result.reference_high:
                result.status = LabResultStatus.ABNORMAL
            elif result.reference_low and result.value < result.reference_low:
                result.status = LabResultStatus.ABNORMAL
            else:
                result.status = LabResultStatus.NORMAL
            return result, None

        # Check critical values
        if rule.critical_high and result.value >= rule.critical_high:
            result.status = LabResultStatus.CRITICAL
            result.is_critical = True
        elif rule.critical_low and result.value <= rule.critical_low:
            result.status = LabResultStatus.CRITICAL
            result.is_critical = True
        # Check abnormal values
        elif rule.abnormal_high and result.value > rule.abnormal_high:
            result.status = LabResultStatus.ABNORMAL
        elif rule.abnormal_low and result.value < rule.abnormal_low:
            result.status = LabResultStatus.ABNORMAL
        else:
            result.status = LabResultStatus.NORMAL
            return result, None

        # Calculate trend if previous value exists
        if result.previous_value:
            change = result.value - result.previous_value
            if abs(change) < 0.01 * result.previous_value:
                result.trend = "stable"
            elif change > 0:
                result.trend = "increasing"
            else:
                result.trend = "decreasing"

        # Create task for abnormal/critical results
        task = await self._create_lab_review_task(tenant_id, result, rule)
        return result, task

    async def _create_lab_review_task(
        self,
        tenant_id: str,
        result: LabResult,
        rule: LabTriageRule
    ) -> ClinicalTask:
        """Create a lab review task"""
        task_type = ClinicalTaskType.LAB_CRITICAL if result.is_critical else ClinicalTaskType.LAB_REVIEW
        priority = TaskPriority.STAT if result.is_critical else TaskPriority.HIGH

        # Determine due date based on criticality
        if result.is_critical:
            due_date = datetime.utcnow() + timedelta(minutes=rule.escalation_minutes)
        else:
            due_date = datetime.utcnow() + timedelta(hours=24)

        status_text = "CRITICAL" if result.is_critical else "ABNORMAL"
        task = ClinicalTask(
            task_id=str(uuid4()),
            tenant_id=tenant_id,
            task_type=task_type,
            priority=priority,
            status=TaskStatus.PENDING,
            patient_id=result.patient_id,
            provider_id=result.ordering_provider_id,
            assigned_to=result.ordering_provider_id,
            title=f"{status_text}: {result.test_name} - {result.value} {result.unit}",
            description=f"Patient's {result.test_name} result is {status_text.lower()}. "
                       f"Value: {result.value} {result.unit}. "
                       f"Reference range: {result.reference_low or 'N/A'} - {result.reference_high or 'N/A'}",
            due_date=due_date,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            related_entity_type="lab_result",
            related_entity_id=result.result_id,
            metadata={
                "test_code": result.test_code,
                "test_name": result.test_name,
                "value": result.value,
                "unit": result.unit,
                "is_critical": result.is_critical,
                "trend": result.trend
            }
        )

        self.tasks[task.task_id] = task

        # Auto-notify for critical results
        if result.is_critical and rule.auto_notify_critical:
            await self._send_critical_notification(result, task)
            result.critical_notified = True

        return task

    async def _send_critical_notification(
        self,
        result: LabResult,
        task: ClinicalTask
    ):
        """Send notification for critical lab result"""
        # In production, this would integrate with notification system
        action = AutomationAction(
            action_id=str(uuid4()),
            task_id=task.task_id,
            action_type="critical_notification",
            action_data={
                "patient_id": result.patient_id,
                "provider_id": result.ordering_provider_id,
                "test": result.test_name,
                "value": result.value,
                "notification_channels": ["sms", "push", "email"]
            },
            performed_at=datetime.utcnow(),
            success=True,
            result_message="Critical lab notification sent to ordering provider"
        )
        self.automation_actions[action.action_id] = action

    async def process_refill_request(
        self,
        tenant_id: str,
        request: MedicationRefillRequest,
        patient_data: dict[str, Any]
    ) -> MedicationRefillRequest:
        """Process a medication refill request"""
        self.refill_requests[request.request_id] = request

        # Check if controlled substance - always require review
        if request.is_controlled:
            request.requires_review = True
            request.status = RefillStatus.PENDING_REVIEW
            await self._create_refill_review_task(tenant_id, request)
            return request

        # Try auto-approval
        can_auto_approve, reason = await self._check_auto_approval(request, patient_data)

        if can_auto_approve:
            request.status = RefillStatus.AUTO_APPROVED
            request.processed_at = datetime.utcnow()
            request.notes = f"Auto-approved: {reason}"

            # Create automation action record
            action = AutomationAction(
                action_id=str(uuid4()),
                task_id="",
                action_type="refill_auto_approve",
                action_data={
                    "request_id": request.request_id,
                    "medication": request.medication_name,
                    "reason": reason
                },
                performed_at=datetime.utcnow(),
                success=True,
                result_message=f"Refill auto-approved: {reason}"
            )
            self.automation_actions[action.action_id] = action

            # Auto-send to pharmacy
            await self._send_to_pharmacy(request)
        else:
            request.requires_review = True
            request.status = RefillStatus.PENDING_REVIEW
            request.notes = f"Requires review: {reason}"
            await self._create_refill_review_task(tenant_id, request)

        return request

    async def _check_auto_approval(
        self,
        request: MedicationRefillRequest,
        patient_data: dict[str, Any]
    ) -> tuple[bool, str]:
        """Check if refill can be auto-approved"""
        for rule in self.refill_approval_rules:
            if not rule.active:
                continue

            # Check medication match
            if rule.medication_name and rule.medication_name.lower() not in request.medication_name.lower():
                continue
            if rule.medication_class and patient_data.get("medication_class") != rule.medication_class:
                continue

            # Check controlled substance
            if rule.exclude_controlled and request.is_controlled:
                continue

            # Check refills remaining
            if request.refills_remaining < rule.min_refills_remaining:
                continue

            # Check days since last visit
            last_visit = patient_data.get("last_visit_date")
            if last_visit:
                days_since = (datetime.utcnow() - last_visit).days
                if days_since > rule.max_days_since_visit:
                    continue

            # Check required labs
            if rule.require_recent_labs:
                has_recent_labs = await self._check_recent_labs(
                    patient_data,
                    rule.required_lab_tests,
                    rule.max_lab_age_days
                )
                if not has_recent_labs:
                    continue

            return True, f"Matched rule: {rule.rule_id}"

        return False, "No auto-approval rule matched"

    async def _check_recent_labs(
        self,
        patient_data: dict[str, Any],
        required_tests: list[str],
        max_age_days: int
    ) -> bool:
        """Check if patient has recent required lab results"""
        labs = patient_data.get("recent_labs", {})
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)

        for test in required_tests:
            lab = labs.get(test)
            if not lab:
                return False
            lab_date = lab.get("date")
            if lab_date and lab_date < cutoff_date:
                return False

        return True

    async def _send_to_pharmacy(self, request: MedicationRefillRequest):
        """Send refill to pharmacy"""
        request.status = RefillStatus.SENT_TO_PHARMACY
        # In production, this would integrate with pharmacy network
        await asyncio.sleep(0.1)

    async def _create_refill_review_task(
        self,
        tenant_id: str,
        request: MedicationRefillRequest
    ) -> ClinicalTask:
        """Create task for refill review"""
        task = ClinicalTask(
            task_id=str(uuid4()),
            tenant_id=tenant_id,
            task_type=ClinicalTaskType.MEDICATION_REFILL,
            priority=TaskPriority.NORMAL,
            status=TaskStatus.PENDING,
            patient_id=request.patient_id,
            provider_id=request.prescriber_id,
            assigned_to=request.prescriber_id,
            title=f"Refill Review: {request.medication_name} {request.strength}",
            description=f"Review refill request for {request.medication_name} {request.strength}. "
                       f"Quantity: {request.quantity}, Days supply: {request.days_supply}. "
                       f"Refills remaining: {request.refills_remaining}",
            due_date=datetime.utcnow() + timedelta(hours=48),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            related_entity_type="refill_request",
            related_entity_id=request.request_id,
            metadata={
                "medication_name": request.medication_name,
                "is_controlled": request.is_controlled,
                "requires_review_reason": request.notes
            }
        )

        self.tasks[task.task_id] = task
        return task

    async def approve_refill(
        self,
        request_id: str,
        approved_by: str,
        notes: Optional[str] = None
    ) -> MedicationRefillRequest:
        """Approve a refill request"""
        request = self.refill_requests.get(request_id)
        if not request:
            raise ValueError(f"Refill request not found: {request_id}")

        request.status = RefillStatus.APPROVED
        request.processed_at = datetime.utcnow()
        request.processed_by = approved_by
        if notes:
            request.notes = (request.notes or "") + f" | Approved: {notes}"

        await self._send_to_pharmacy(request)
        return request

    async def deny_refill(
        self,
        request_id: str,
        denied_by: str,
        reason: str
    ) -> MedicationRefillRequest:
        """Deny a refill request"""
        request = self.refill_requests.get(request_id)
        if not request:
            raise ValueError(f"Refill request not found: {request_id}")

        request.status = RefillStatus.DENIED
        request.processed_at = datetime.utcnow()
        request.processed_by = denied_by
        request.denial_reason = reason

        return request

    async def process_referral(
        self,
        tenant_id: str,
        referral: Referral
    ) -> Referral:
        """Process a patient referral"""
        self.referrals[referral.referral_id] = referral
        referral.status = ReferralStatus.REVIEWING

        # Check if authorization is required
        auth_required = await self._check_auth_required(referral)
        referral.auth_required = auth_required

        if auth_required:
            referral.status = ReferralStatus.PENDING_AUTH
            await self._create_prior_auth_task(tenant_id, referral)
        else:
            referral.status = ReferralStatus.AUTHORIZED
            # Auto-schedule if provider available
            await self._attempt_auto_schedule(referral)

        return referral

    async def _check_auth_required(self, referral: Referral) -> bool:
        """Check if prior authorization is required"""
        # In production, this would check payer rules
        high_cost_specialties = [
            "surgery", "oncology", "neurology", "cardiology",
            "orthopedics", "transplant"
        ]
        return referral.specialty.lower() in high_cost_specialties

    async def _create_prior_auth_task(
        self,
        tenant_id: str,
        referral: Referral
    ) -> ClinicalTask:
        """Create task for prior authorization"""
        task = ClinicalTask(
            task_id=str(uuid4()),
            tenant_id=tenant_id,
            task_type=ClinicalTaskType.PRIOR_AUTH,
            priority=TaskPriority.HIGH if referral.urgency == TaskPriority.URGENT else TaskPriority.NORMAL,
            status=TaskStatus.PENDING,
            patient_id=referral.patient_id,
            provider_id=referral.referring_provider_id,
            assigned_role="authorization_specialist",
            title=f"Prior Auth: {referral.specialty} Referral",
            description=f"Prior authorization needed for {referral.specialty} referral. "
                       f"Reason: {referral.reason}. "
                       f"Diagnosis codes: {', '.join(referral.diagnosis_codes)}",
            due_date=datetime.utcnow() + timedelta(days=3),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            related_entity_type="referral",
            related_entity_id=referral.referral_id
        )

        self.tasks[task.task_id] = task
        return task

    async def _attempt_auto_schedule(self, referral: Referral):
        """Attempt to auto-schedule the referral"""
        # In production, would check provider availability
        pass

    async def complete_prior_auth(
        self,
        referral_id: str,
        auth_number: str,
        expiry_date: datetime,
        completed_by: str
    ) -> Referral:
        """Complete prior authorization for referral"""
        referral = self.referrals.get(referral_id)
        if not referral:
            raise ValueError(f"Referral not found: {referral_id}")

        referral.auth_number = auth_number
        referral.auth_expiry = expiry_date
        referral.status = ReferralStatus.AUTHORIZED

        await self._attempt_auto_schedule(referral)
        return referral

    async def escalate_task(
        self,
        task_id: str,
        reason: str,
        escalate_to: Optional[str] = None
    ) -> ClinicalTask:
        """Escalate a task"""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        task.status = TaskStatus.ESCALATED
        task.escalation_level += 1
        task.updated_at = datetime.utcnow()

        # Increase priority
        priority_order = [TaskPriority.LOW, TaskPriority.NORMAL, TaskPriority.HIGH, TaskPriority.URGENT, TaskPriority.STAT]
        current_idx = priority_order.index(task.priority)
        if current_idx < len(priority_order) - 1:
            task.priority = priority_order[current_idx + 1]

        # Reassign if specified
        if escalate_to:
            task.assigned_to = escalate_to

        # Add escalation note
        task.notes.append({
            "timestamp": datetime.utcnow().isoformat(),
            "type": "escalation",
            "message": reason,
            "escalation_level": task.escalation_level
        })

        return task

    async def complete_task(
        self,
        task_id: str,
        completed_by: str,
        resolution: str,
        outcome_data: Optional[dict[str, Any]] = None
    ) -> ClinicalTask:
        """Complete a clinical task"""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        task.completed_by = completed_by
        task.updated_at = datetime.utcnow()

        task.notes.append({
            "timestamp": datetime.utcnow().isoformat(),
            "type": "completion",
            "message": resolution,
            "completed_by": completed_by,
            "outcome_data": outcome_data
        })

        return task

    async def get_task_queue(
        self,
        tenant_id: str,
        assigned_to: Optional[str] = None,
        assigned_role: Optional[str] = None,
        task_types: Optional[list[ClinicalTaskType]] = None,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None
    ) -> list[ClinicalTask]:
        """Get task queue with filters"""
        tasks = [t for t in self.tasks.values() if t.tenant_id == tenant_id]

        if assigned_to:
            tasks = [t for t in tasks if t.assigned_to == assigned_to]
        if assigned_role:
            tasks = [t for t in tasks if t.assigned_role == assigned_role]
        if task_types:
            tasks = [t for t in tasks if t.task_type in task_types]
        if status:
            tasks = [t for t in tasks if t.status == status]
        if priority:
            tasks = [t for t in tasks if t.priority == priority]

        # Sort by priority and due date
        priority_order = {
            TaskPriority.STAT: 0,
            TaskPriority.URGENT: 1,
            TaskPriority.HIGH: 2,
            TaskPriority.NORMAL: 3,
            TaskPriority.LOW: 4
        }
        tasks.sort(key=lambda t: (priority_order[t.priority], t.due_date or datetime.max))

        return tasks

    async def auto_escalate_overdue(self, tenant_id: str) -> list[ClinicalTask]:
        """Auto-escalate overdue tasks"""
        now = datetime.utcnow()
        escalated = []

        pending_tasks = [
            t for t in self.tasks.values()
            if t.tenant_id == tenant_id
            and t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]
            and t.due_date
            and t.due_date < now
        ]

        for task in pending_tasks:
            await self.escalate_task(
                task.task_id,
                f"Auto-escalated: overdue by {(now - task.due_date).total_seconds() / 60:.0f} minutes"
            )
            escalated.append(task)

        return escalated

    def add_lab_triage_rule(self, rule: LabTriageRule):
        """Add custom lab triage rule"""
        self.lab_triage_rules[rule.test_code] = rule

    def add_refill_approval_rule(self, rule: RefillAutoApprovalRule):
        """Add custom refill approval rule"""
        self.refill_approval_rules.append(rule)


# Singleton instance
_clinical_automation: Optional[ClinicalTaskAutomation] = None


def get_clinical_automation() -> ClinicalTaskAutomation:
    """Get singleton clinical automation instance"""
    global _clinical_automation
    if _clinical_automation is None:
        _clinical_automation = ClinicalTaskAutomation()
    return _clinical_automation
