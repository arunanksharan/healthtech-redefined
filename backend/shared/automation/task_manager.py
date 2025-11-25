"""
Human-in-the-Loop Task Management Service

Manages tasks that require human review, approval, or intervention.
Provides task routing, assignment, escalation, and completion tracking.

Part of EPIC-012: Intelligent Automation Platform
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional
from uuid import uuid4


class HumanTaskType(str, Enum):
    """Types of human tasks"""
    APPROVAL = "approval"
    REVIEW = "review"
    DATA_ENTRY = "data_entry"
    VERIFICATION = "verification"
    DECISION = "decision"
    EXCEPTION = "exception"
    ESCALATION = "escalation"
    QUALITY_CHECK = "quality_check"
    CLINICAL_REVIEW = "clinical_review"
    FINANCIAL_REVIEW = "financial_review"
    DOCUMENT_REVIEW = "document_review"
    PATIENT_OUTREACH = "patient_outreach"


class TaskPriority(str, Enum):
    """Task priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskState(str, Enum):
    """Task lifecycle state"""
    CREATED = "created"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    PENDING_INFO = "pending_info"
    COMPLETED = "completed"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class AssignmentStrategy(str, Enum):
    """Task assignment strategies"""
    ROUND_ROBIN = "round_robin"
    LOAD_BALANCED = "load_balanced"
    SKILL_BASED = "skill_based"
    RANDOM = "random"
    MANUAL = "manual"
    QUEUE_BASED = "queue_based"


@dataclass
class TaskComment:
    """Comment on a task"""
    comment_id: str
    task_id: str
    user_id: str
    content: str
    created_at: datetime
    is_internal: bool = False  # Internal vs visible to patient
    attachments: list[str] = field(default_factory=list)


@dataclass
class TaskHistory:
    """Task history entry"""
    entry_id: str
    task_id: str
    action: str
    from_state: Optional[TaskState]
    to_state: Optional[TaskState]
    performed_by: str
    performed_at: datetime
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskAttachment:
    """Task attachment"""
    attachment_id: str
    task_id: str
    file_name: str
    file_type: str
    file_size: int
    file_path: str
    uploaded_by: str
    uploaded_at: datetime


@dataclass
class TaskDefinition:
    """Definition of a task type"""
    definition_id: str
    tenant_id: str
    task_type: HumanTaskType
    name: str
    description: str
    default_priority: TaskPriority
    default_due_hours: int
    required_fields: list[str]
    form_schema: dict[str, Any]  # JSON Schema for task form
    allowed_actions: list[str]
    assignment_strategy: AssignmentStrategy
    eligible_roles: list[str]
    eligible_users: list[str] = field(default_factory=list)
    auto_escalate: bool = True
    escalation_hours: int = 24
    sla_hours: Optional[int] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HumanTask:
    """A human task requiring action"""
    task_id: str
    tenant_id: str
    task_type: HumanTaskType
    definition_id: Optional[str]
    title: str
    description: str
    priority: TaskPriority
    state: TaskState
    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime]
    assigned_to: Optional[str]
    assigned_at: Optional[datetime]
    claimed_at: Optional[datetime]
    completed_at: Optional[datetime]
    completed_by: Optional[str]
    outcome: Optional[str]
    outcome_data: dict[str, Any] = field(default_factory=dict)
    form_data: dict[str, Any] = field(default_factory=dict)
    source_system: Optional[str] = None
    source_entity_type: Optional[str] = None
    source_entity_id: Optional[str] = None
    patient_id: Optional[str] = None
    provider_id: Optional[str] = None
    queue_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    escalation_level: int = 0
    sla_deadline: Optional[datetime] = None
    sla_breached: bool = False
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskQueue:
    """A queue for routing tasks"""
    queue_id: str
    tenant_id: str
    name: str
    description: str
    task_types: list[HumanTaskType]
    assignment_strategy: AssignmentStrategy
    eligible_roles: list[str]
    eligible_users: list[str]
    is_active: bool = True
    max_concurrent_per_user: int = 10
    auto_assign: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkerProfile:
    """Profile for task workers"""
    user_id: str
    tenant_id: str
    roles: list[str]
    skills: list[str]
    queues: list[str]
    max_concurrent_tasks: int = 10
    current_task_count: int = 0
    is_available: bool = True
    last_assignment: Optional[datetime] = None
    performance_score: float = 1.0
    completed_today: int = 0
    average_completion_time: float = 0  # minutes


@dataclass
class EscalationRule:
    """Rule for task escalation"""
    rule_id: str
    tenant_id: str
    name: str
    task_types: list[HumanTaskType]
    trigger_condition: str  # overdue, sla_breach, priority_change
    hours_threshold: int
    escalate_to_role: Optional[str]
    escalate_to_user: Optional[str]
    increase_priority: bool = True
    send_notification: bool = True
    active: bool = True


class HumanTaskManager:
    """
    Human-in-the-loop task management engine.
    Handles task creation, assignment, routing, and completion.
    """

    def __init__(self):
        self.tasks: dict[str, HumanTask] = {}
        self.task_definitions: dict[str, TaskDefinition] = {}
        self.queues: dict[str, TaskQueue] = {}
        self.workers: dict[str, WorkerProfile] = {}
        self.comments: dict[str, list[TaskComment]] = {}
        self.history: dict[str, list[TaskHistory]] = {}
        self.attachments: dict[str, list[TaskAttachment]] = {}
        self.escalation_rules: list[EscalationRule] = []
        self.callbacks: dict[str, list[Callable]] = {}
        self._round_robin_index: dict[str, int] = {}

    async def create_task(
        self,
        tenant_id: str,
        task_type: HumanTaskType,
        title: str,
        description: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        due_hours: Optional[int] = None,
        form_data: Optional[dict[str, Any]] = None,
        source_system: Optional[str] = None,
        source_entity_type: Optional[str] = None,
        source_entity_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        provider_id: Optional[str] = None,
        queue_id: Optional[str] = None,
        assigned_to: Optional[str] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None
    ) -> HumanTask:
        """Create a new human task"""
        now = datetime.utcnow()

        # Calculate due date
        due_date = None
        if due_hours:
            due_date = now + timedelta(hours=due_hours)
        elif queue_id and queue_id in self.queues:
            # Get default from queue or definition
            pass

        task = HumanTask(
            task_id=str(uuid4()),
            tenant_id=tenant_id,
            task_type=task_type,
            definition_id=None,
            title=title,
            description=description,
            priority=priority,
            state=TaskState.CREATED,
            created_at=now,
            updated_at=now,
            due_date=due_date,
            form_data=form_data or {},
            source_system=source_system,
            source_entity_type=source_entity_type,
            source_entity_id=source_entity_id,
            patient_id=patient_id,
            provider_id=provider_id,
            queue_id=queue_id,
            tags=tags or [],
            metadata=metadata or {}
        )

        self.tasks[task.task_id] = task
        self.comments[task.task_id] = []
        self.history[task.task_id] = []
        self.attachments[task.task_id] = []

        # Record creation
        await self._add_history(task.task_id, "created", None, TaskState.CREATED, "system")

        # Auto-assign if specified
        if assigned_to:
            await self.assign_task(task.task_id, assigned_to, "system")
        elif queue_id:
            queue = self.queues.get(queue_id)
            if queue and queue.auto_assign:
                await self._auto_assign_task(task, queue)

        # Fire callbacks
        await self._fire_callbacks("task_created", task)

        return task

    async def assign_task(
        self,
        task_id: str,
        user_id: str,
        assigned_by: str
    ) -> HumanTask:
        """Assign a task to a user"""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        old_state = task.state
        task.assigned_to = user_id
        task.assigned_at = datetime.utcnow()
        task.state = TaskState.ASSIGNED
        task.updated_at = datetime.utcnow()

        # Update worker profile
        worker = self.workers.get(user_id)
        if worker:
            worker.current_task_count += 1
            worker.last_assignment = datetime.utcnow()

        await self._add_history(
            task_id, "assigned", old_state, TaskState.ASSIGNED, assigned_by,
            {"assigned_to": user_id}
        )

        await self._fire_callbacks("task_assigned", task)
        return task

    async def claim_task(
        self,
        task_id: str,
        user_id: str
    ) -> HumanTask:
        """User claims a task from queue"""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        if task.assigned_to and task.assigned_to != user_id:
            raise ValueError("Task is already assigned to another user")

        # Check user capacity
        worker = self.workers.get(user_id)
        if worker and worker.current_task_count >= worker.max_concurrent_tasks:
            raise ValueError("User has reached maximum concurrent tasks")

        old_state = task.state
        task.assigned_to = user_id
        task.assigned_at = datetime.utcnow()
        task.claimed_at = datetime.utcnow()
        task.state = TaskState.IN_PROGRESS
        task.updated_at = datetime.utcnow()

        if worker:
            worker.current_task_count += 1
            worker.last_assignment = datetime.utcnow()

        await self._add_history(
            task_id, "claimed", old_state, TaskState.IN_PROGRESS, user_id
        )

        await self._fire_callbacks("task_claimed", task)
        return task

    async def release_task(
        self,
        task_id: str,
        user_id: str,
        reason: Optional[str] = None
    ) -> HumanTask:
        """Release a task back to queue"""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        if task.assigned_to != user_id:
            raise ValueError("Task is not assigned to this user")

        old_state = task.state
        old_assignee = task.assigned_to

        task.assigned_to = None
        task.assigned_at = None
        task.claimed_at = None
        task.state = TaskState.QUEUED
        task.updated_at = datetime.utcnow()

        # Update worker profile
        worker = self.workers.get(user_id)
        if worker and worker.current_task_count > 0:
            worker.current_task_count -= 1

        await self._add_history(
            task_id, "released", old_state, TaskState.QUEUED, user_id,
            {"reason": reason, "previous_assignee": old_assignee}
        )

        await self._fire_callbacks("task_released", task)
        return task

    async def complete_task(
        self,
        task_id: str,
        user_id: str,
        outcome: str,
        outcome_data: Optional[dict[str, Any]] = None
    ) -> HumanTask:
        """Complete a task"""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        if task.state == TaskState.COMPLETED:
            raise ValueError("Task is already completed")

        old_state = task.state
        task.state = TaskState.COMPLETED
        task.completed_at = datetime.utcnow()
        task.completed_by = user_id
        task.outcome = outcome
        task.outcome_data = outcome_data or {}
        task.updated_at = datetime.utcnow()

        # Update worker profile
        worker = self.workers.get(user_id)
        if worker:
            if worker.current_task_count > 0:
                worker.current_task_count -= 1
            worker.completed_today += 1
            if task.claimed_at:
                completion_time = (task.completed_at - task.claimed_at).total_seconds() / 60
                worker.average_completion_time = (
                    worker.average_completion_time * 0.9 + completion_time * 0.1
                )

        await self._add_history(
            task_id, "completed", old_state, TaskState.COMPLETED, user_id,
            {"outcome": outcome, "outcome_data": outcome_data}
        )

        await self._fire_callbacks("task_completed", task)
        return task

    async def approve_task(
        self,
        task_id: str,
        user_id: str,
        comments: Optional[str] = None
    ) -> HumanTask:
        """Approve a task (for approval-type tasks)"""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        old_state = task.state
        task.state = TaskState.APPROVED
        task.completed_at = datetime.utcnow()
        task.completed_by = user_id
        task.outcome = "approved"
        task.updated_at = datetime.utcnow()

        if comments:
            await self.add_comment(task_id, user_id, comments)

        # Update worker profile
        worker = self.workers.get(user_id)
        if worker and worker.current_task_count > 0:
            worker.current_task_count -= 1

        await self._add_history(
            task_id, "approved", old_state, TaskState.APPROVED, user_id
        )

        await self._fire_callbacks("task_approved", task)
        return task

    async def reject_task(
        self,
        task_id: str,
        user_id: str,
        reason: str
    ) -> HumanTask:
        """Reject a task (for approval-type tasks)"""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        old_state = task.state
        task.state = TaskState.REJECTED
        task.completed_at = datetime.utcnow()
        task.completed_by = user_id
        task.outcome = "rejected"
        task.outcome_data["rejection_reason"] = reason
        task.updated_at = datetime.utcnow()

        await self.add_comment(task_id, user_id, f"Rejected: {reason}")

        # Update worker profile
        worker = self.workers.get(user_id)
        if worker and worker.current_task_count > 0:
            worker.current_task_count -= 1

        await self._add_history(
            task_id, "rejected", old_state, TaskState.REJECTED, user_id,
            {"reason": reason}
        )

        await self._fire_callbacks("task_rejected", task)
        return task

    async def escalate_task(
        self,
        task_id: str,
        escalated_by: str,
        reason: str,
        escalate_to: Optional[str] = None
    ) -> HumanTask:
        """Escalate a task"""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        old_state = task.state
        old_assignee = task.assigned_to

        task.state = TaskState.ESCALATED
        task.escalation_level += 1
        task.updated_at = datetime.utcnow()

        # Increase priority
        priority_order = [TaskPriority.LOW, TaskPriority.MEDIUM, TaskPriority.HIGH, TaskPriority.CRITICAL]
        current_idx = priority_order.index(task.priority)
        if current_idx < len(priority_order) - 1:
            task.priority = priority_order[current_idx + 1]

        # Update worker profile for old assignee
        if old_assignee:
            worker = self.workers.get(old_assignee)
            if worker and worker.current_task_count > 0:
                worker.current_task_count -= 1

        # Reassign if specified
        if escalate_to:
            task.assigned_to = escalate_to
            task.assigned_at = datetime.utcnow()
            new_worker = self.workers.get(escalate_to)
            if new_worker:
                new_worker.current_task_count += 1
        else:
            task.assigned_to = None
            task.assigned_at = None

        await self.add_comment(task_id, escalated_by, f"Escalated: {reason}", is_internal=True)

        await self._add_history(
            task_id, "escalated", old_state, TaskState.ESCALATED, escalated_by,
            {
                "reason": reason,
                "escalation_level": task.escalation_level,
                "escalated_to": escalate_to,
                "previous_assignee": old_assignee
            }
        )

        await self._fire_callbacks("task_escalated", task)
        return task

    async def add_comment(
        self,
        task_id: str,
        user_id: str,
        content: str,
        is_internal: bool = False,
        attachments: Optional[list[str]] = None
    ) -> TaskComment:
        """Add a comment to a task"""
        comment = TaskComment(
            comment_id=str(uuid4()),
            task_id=task_id,
            user_id=user_id,
            content=content,
            created_at=datetime.utcnow(),
            is_internal=is_internal,
            attachments=attachments or []
        )

        if task_id not in self.comments:
            self.comments[task_id] = []
        self.comments[task_id].append(comment)

        # Update task
        task = self.tasks.get(task_id)
        if task:
            task.updated_at = datetime.utcnow()

        return comment

    async def update_form_data(
        self,
        task_id: str,
        user_id: str,
        form_data: dict[str, Any]
    ) -> HumanTask:
        """Update task form data"""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        task.form_data.update(form_data)
        task.updated_at = datetime.utcnow()

        await self._add_history(
            task_id, "form_updated", task.state, task.state, user_id,
            {"updated_fields": list(form_data.keys())}
        )

        return task

    async def _auto_assign_task(self, task: HumanTask, queue: TaskQueue):
        """Auto-assign task based on queue strategy"""
        eligible_workers = [
            w for w in self.workers.values()
            if w.tenant_id == task.tenant_id
            and w.is_available
            and w.current_task_count < w.max_concurrent_tasks
            and (not queue.eligible_roles or any(r in w.roles for r in queue.eligible_roles))
            and (not queue.eligible_users or w.user_id in queue.eligible_users)
        ]

        if not eligible_workers:
            task.state = TaskState.QUEUED
            return

        selected_worker = None

        if queue.assignment_strategy == AssignmentStrategy.ROUND_ROBIN:
            idx = self._round_robin_index.get(queue.queue_id, 0)
            selected_worker = eligible_workers[idx % len(eligible_workers)]
            self._round_robin_index[queue.queue_id] = idx + 1

        elif queue.assignment_strategy == AssignmentStrategy.LOAD_BALANCED:
            selected_worker = min(eligible_workers, key=lambda w: w.current_task_count)

        elif queue.assignment_strategy == AssignmentStrategy.SKILL_BASED:
            # Match task tags to worker skills
            for worker in eligible_workers:
                if any(tag in worker.skills for tag in task.tags):
                    selected_worker = worker
                    break
            if not selected_worker:
                selected_worker = eligible_workers[0]

        elif queue.assignment_strategy == AssignmentStrategy.RANDOM:
            import random
            selected_worker = random.choice(eligible_workers)

        if selected_worker:
            await self.assign_task(task.task_id, selected_worker.user_id, "system")
        else:
            task.state = TaskState.QUEUED

    async def _add_history(
        self,
        task_id: str,
        action: str,
        from_state: Optional[TaskState],
        to_state: Optional[TaskState],
        performed_by: str,
        details: Optional[dict[str, Any]] = None
    ):
        """Add history entry"""
        entry = TaskHistory(
            entry_id=str(uuid4()),
            task_id=task_id,
            action=action,
            from_state=from_state,
            to_state=to_state,
            performed_by=performed_by,
            performed_at=datetime.utcnow(),
            details=details or {}
        )

        if task_id not in self.history:
            self.history[task_id] = []
        self.history[task_id].append(entry)

    async def _fire_callbacks(self, event: str, task: HumanTask):
        """Fire registered callbacks"""
        callbacks = self.callbacks.get(event, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(task)
                else:
                    callback(task)
            except Exception:
                pass  # Log but don't fail

    def register_callback(self, event: str, callback: Callable):
        """Register a callback for task events"""
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)

    async def create_queue(
        self,
        tenant_id: str,
        name: str,
        description: str,
        task_types: list[HumanTaskType],
        assignment_strategy: AssignmentStrategy = AssignmentStrategy.LOAD_BALANCED,
        eligible_roles: Optional[list[str]] = None,
        auto_assign: bool = True
    ) -> TaskQueue:
        """Create a task queue"""
        queue = TaskQueue(
            queue_id=str(uuid4()),
            tenant_id=tenant_id,
            name=name,
            description=description,
            task_types=task_types,
            assignment_strategy=assignment_strategy,
            eligible_roles=eligible_roles or [],
            eligible_users=[],
            auto_assign=auto_assign
        )

        self.queues[queue.queue_id] = queue
        return queue

    async def register_worker(
        self,
        user_id: str,
        tenant_id: str,
        roles: list[str],
        skills: Optional[list[str]] = None,
        queues: Optional[list[str]] = None,
        max_concurrent: int = 10
    ) -> WorkerProfile:
        """Register a worker"""
        worker = WorkerProfile(
            user_id=user_id,
            tenant_id=tenant_id,
            roles=roles,
            skills=skills or [],
            queues=queues or [],
            max_concurrent_tasks=max_concurrent
        )

        self.workers[user_id] = worker
        return worker

    async def get_task_queue(
        self,
        tenant_id: str,
        queue_id: Optional[str] = None,
        user_id: Optional[str] = None,
        task_types: Optional[list[HumanTaskType]] = None,
        states: Optional[list[TaskState]] = None,
        priority: Optional[TaskPriority] = None,
        patient_id: Optional[str] = None,
        limit: int = 50
    ) -> list[HumanTask]:
        """Get tasks from queue with filters"""
        tasks = [t for t in self.tasks.values() if t.tenant_id == tenant_id]

        if queue_id:
            tasks = [t for t in tasks if t.queue_id == queue_id]
        if user_id:
            tasks = [t for t in tasks if t.assigned_to == user_id]
        if task_types:
            tasks = [t for t in tasks if t.task_type in task_types]
        if states:
            tasks = [t for t in tasks if t.state in states]
        if priority:
            tasks = [t for t in tasks if t.priority == priority]
        if patient_id:
            tasks = [t for t in tasks if t.patient_id == patient_id]

        # Sort by priority and due date
        priority_order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3
        }
        tasks.sort(key=lambda t: (
            priority_order[t.priority],
            t.due_date or datetime.max
        ))

        return tasks[:limit]

    async def process_escalations(self, tenant_id: str) -> list[HumanTask]:
        """Process automatic escalations"""
        escalated = []
        now = datetime.utcnow()

        active_tasks = [
            t for t in self.tasks.values()
            if t.tenant_id == tenant_id
            and t.state in [TaskState.QUEUED, TaskState.ASSIGNED, TaskState.IN_PROGRESS]
        ]

        for rule in self.escalation_rules:
            if not rule.active or rule.tenant_id != tenant_id:
                continue

            for task in active_tasks:
                if task.task_type not in rule.task_types:
                    continue

                should_escalate = False

                if rule.trigger_condition == "overdue":
                    if task.due_date and task.due_date < now:
                        should_escalate = True
                elif rule.trigger_condition == "sla_breach":
                    if task.sla_deadline and task.sla_deadline < now:
                        should_escalate = True
                        task.sla_breached = True
                elif rule.trigger_condition == "stale":
                    hours_since_update = (now - task.updated_at).total_seconds() / 3600
                    if hours_since_update >= rule.hours_threshold:
                        should_escalate = True

                if should_escalate:
                    await self.escalate_task(
                        task.task_id,
                        "system",
                        f"Auto-escalated: {rule.trigger_condition}",
                        escalate_to=rule.escalate_to_user
                    )
                    escalated.append(task)

        return escalated

    async def get_worker_stats(
        self,
        tenant_id: str,
        user_id: str
    ) -> dict[str, Any]:
        """Get worker performance stats"""
        worker = self.workers.get(user_id)
        if not worker:
            return {}

        user_tasks = [
            t for t in self.tasks.values()
            if t.tenant_id == tenant_id and t.assigned_to == user_id
        ]

        completed = [t for t in user_tasks if t.state == TaskState.COMPLETED]
        in_progress = [t for t in user_tasks if t.state == TaskState.IN_PROGRESS]
        overdue = [t for t in in_progress if t.due_date and t.due_date < datetime.utcnow()]

        return {
            "user_id": user_id,
            "current_tasks": len(in_progress),
            "completed_total": len(completed),
            "completed_today": worker.completed_today,
            "overdue_tasks": len(overdue),
            "average_completion_time": worker.average_completion_time,
            "performance_score": worker.performance_score
        }


# Singleton instance
_task_manager: Optional[HumanTaskManager] = None


def get_task_manager() -> HumanTaskManager:
    """Get singleton task manager instance"""
    global _task_manager
    if _task_manager is None:
        _task_manager = HumanTaskManager()
    return _task_manager
