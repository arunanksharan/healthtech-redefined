"""
Intelligent Workflow Automation Engine
EPIC-012: Intelligent Automation Platform - US-012.1

Provides:
- Visual workflow execution engine
- Trigger management (time, event, condition, manual, API, file)
- Action library (database, API, email, SMS, document, human tasks)
- Conditional logic, branching, loops, parallel execution
- Error handling and retry logic
- Workflow versioning and state management
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Union
from uuid import uuid4
import asyncio
import json
import re
import operator
from functools import reduce


class WorkflowStatus(Enum):
    """Workflow execution status"""
    DRAFT = "draft"
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING_HUMAN = "waiting_human"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


class TriggerType(Enum):
    """Workflow trigger types"""
    SCHEDULE = "schedule"  # Cron-based
    EVENT = "event"  # Event-driven
    WEBHOOK = "webhook"  # HTTP webhook
    CONDITION = "condition"  # Threshold-based
    MANUAL = "manual"  # User-initiated
    API = "api"  # API call
    FILE_UPLOAD = "file_upload"  # File arrival


class ActionType(Enum):
    """Workflow action types"""
    HTTP_REQUEST = "http_request"
    DATABASE_QUERY = "database_query"
    DATABASE_INSERT = "database_insert"
    DATABASE_UPDATE = "database_update"
    EMAIL = "email"
    SMS = "sms"
    PUSH_NOTIFICATION = "push_notification"
    DOCUMENT_GENERATE = "document_generate"
    TRANSFORM_DATA = "transform_data"
    HUMAN_TASK = "human_task"
    APPROVAL = "approval"
    ML_PREDICTION = "ml_prediction"
    FHIR_OPERATION = "fhir_operation"
    CALL_WORKFLOW = "call_workflow"
    WAIT = "wait"
    LOG = "log"


class StepType(Enum):
    """Workflow step types"""
    ACTION = "action"
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"
    SWITCH = "switch"
    ERROR_HANDLER = "error_handler"
    SUB_WORKFLOW = "sub_workflow"


class RetryStrategy(Enum):
    """Retry strategies for failed steps"""
    NONE = "none"
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"


@dataclass
class RetryPolicy:
    """Retry policy for workflow steps"""
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    max_attempts: int = 3
    initial_delay_seconds: int = 5
    max_delay_seconds: int = 300
    backoff_multiplier: float = 2.0
    retryable_errors: List[str] = field(default_factory=list)


@dataclass
class Trigger:
    """Workflow trigger definition"""
    id: str
    type: TriggerType
    name: str
    config: Dict[str, Any]
    enabled: bool = True
    description: Optional[str] = None

    @staticmethod
    def schedule(cron_expression: str, timezone: str = "UTC", name: str = "Schedule Trigger") -> "Trigger":
        """Create a schedule-based trigger"""
        return Trigger(
            id=str(uuid4()),
            type=TriggerType.SCHEDULE,
            name=name,
            config={
                "cron": cron_expression,
                "timezone": timezone
            }
        )

    @staticmethod
    def event(event_type: str, filters: Optional[Dict] = None, name: str = "Event Trigger") -> "Trigger":
        """Create an event-based trigger"""
        return Trigger(
            id=str(uuid4()),
            type=TriggerType.EVENT,
            name=name,
            config={
                "event_type": event_type,
                "filters": filters or {}
            }
        )

    @staticmethod
    def webhook(path: str, method: str = "POST", name: str = "Webhook Trigger") -> "Trigger":
        """Create a webhook trigger"""
        return Trigger(
            id=str(uuid4()),
            type=TriggerType.WEBHOOK,
            name=name,
            config={
                "path": path,
                "method": method
            }
        )

    @staticmethod
    def condition(metric: str, operator: str, threshold: Any, name: str = "Condition Trigger") -> "Trigger":
        """Create a condition-based trigger"""
        return Trigger(
            id=str(uuid4()),
            type=TriggerType.CONDITION,
            name=name,
            config={
                "metric": metric,
                "operator": operator,
                "threshold": threshold
            }
        )


@dataclass
class Action:
    """Workflow action definition"""
    type: ActionType
    config: Dict[str, Any]
    timeout_seconds: int = 60
    retry_policy: Optional[RetryPolicy] = None

    @staticmethod
    def http_request(
        url: str,
        method: str = "GET",
        headers: Optional[Dict] = None,
        body: Optional[Dict] = None,
        timeout: int = 30
    ) -> "Action":
        """Create an HTTP request action"""
        return Action(
            type=ActionType.HTTP_REQUEST,
            config={
                "url": url,
                "method": method,
                "headers": headers or {},
                "body": body
            },
            timeout_seconds=timeout
        )

    @staticmethod
    def database_query(query: str, params: Optional[List] = None, connection: str = "default") -> "Action":
        """Create a database query action"""
        return Action(
            type=ActionType.DATABASE_QUERY,
            config={
                "query": query,
                "params": params or [],
                "connection": connection
            }
        )

    @staticmethod
    def send_email(
        to: Union[str, List[str]],
        subject: str,
        template: str,
        template_data: Optional[Dict] = None
    ) -> "Action":
        """Create an email action"""
        return Action(
            type=ActionType.EMAIL,
            config={
                "to": to if isinstance(to, list) else [to],
                "subject": subject,
                "template": template,
                "template_data": template_data or {}
            }
        )

    @staticmethod
    def send_sms(to: str, message: str, template: Optional[str] = None) -> "Action":
        """Create an SMS action"""
        return Action(
            type=ActionType.SMS,
            config={
                "to": to,
                "message": message,
                "template": template
            }
        )

    @staticmethod
    def human_task(
        title: str,
        description: str,
        assignee: Optional[str] = None,
        assignee_role: Optional[str] = None,
        priority: str = "normal",
        due_hours: int = 24
    ) -> "Action":
        """Create a human task action"""
        return Action(
            type=ActionType.HUMAN_TASK,
            config={
                "title": title,
                "description": description,
                "assignee": assignee,
                "assignee_role": assignee_role,
                "priority": priority,
                "due_hours": due_hours
            }
        )

    @staticmethod
    def approval(
        title: str,
        description: str,
        approvers: List[str],
        approval_type: str = "any",  # any, all, majority
        timeout_hours: int = 48
    ) -> "Action":
        """Create an approval action"""
        return Action(
            type=ActionType.APPROVAL,
            config={
                "title": title,
                "description": description,
                "approvers": approvers,
                "approval_type": approval_type,
                "timeout_hours": timeout_hours
            }
        )

    @staticmethod
    def ml_prediction(model_name: str, features: Dict[str, Any]) -> "Action":
        """Create an ML prediction action"""
        return Action(
            type=ActionType.ML_PREDICTION,
            config={
                "model_name": model_name,
                "features": features
            }
        )

    @staticmethod
    def transform_data(transformations: List[Dict[str, Any]]) -> "Action":
        """Create a data transformation action"""
        return Action(
            type=ActionType.TRANSFORM_DATA,
            config={
                "transformations": transformations
            }
        )


@dataclass
class Condition:
    """Condition for conditional steps"""
    field: str
    operator: str  # eq, ne, gt, gte, lt, lte, in, not_in, contains, starts_with, ends_with, regex, exists
    value: Any
    logic: str = "AND"  # AND, OR

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate condition against context"""
        field_value = self._get_field_value(self.field, context)

        operators = {
            'eq': operator.eq,
            'ne': operator.ne,
            'gt': operator.gt,
            'gte': operator.ge,
            'lt': operator.lt,
            'lte': operator.le,
            'in': lambda x, y: x in y,
            'not_in': lambda x, y: x not in y,
            'contains': lambda x, y: y in str(x) if x else False,
            'starts_with': lambda x, y: str(x).startswith(y) if x else False,
            'ends_with': lambda x, y: str(x).endswith(y) if x else False,
            'regex': lambda x, y: bool(re.match(y, str(x))) if x else False,
            'exists': lambda x, y: x is not None,
            'is_empty': lambda x, y: not x,
            'is_not_empty': lambda x, y: bool(x),
        }

        op_func = operators.get(self.operator)
        if not op_func:
            raise ValueError(f"Unknown operator: {self.operator}")

        try:
            return op_func(field_value, self.value)
        except Exception:
            return False

    def _get_field_value(self, field_path: str, context: Dict) -> Any:
        """Get field value using dot notation"""
        parts = field_path.split('.')
        value = context
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif isinstance(value, list) and part.isdigit():
                idx = int(part)
                value = value[idx] if idx < len(value) else None
            else:
                return None
        return value


@dataclass
class WorkflowStep:
    """Individual workflow step"""
    id: str
    name: str
    type: StepType
    action: Optional[Action] = None
    conditions: Optional[List[Condition]] = None
    then_steps: Optional[List[str]] = None  # Step IDs to execute if condition true
    else_steps: Optional[List[str]] = None  # Step IDs to execute if condition false
    loop_items: Optional[str] = None  # Expression for items to iterate
    loop_body: Optional[List[str]] = None  # Step IDs for loop body
    parallel_branches: Optional[List[List[str]]] = None  # Parallel step ID lists
    switch_cases: Optional[Dict[str, List[str]]] = None  # Case value -> step IDs
    default_case: Optional[List[str]] = None
    error_handlers: Optional[List[Dict]] = None
    retry_policy: Optional[RetryPolicy] = None
    timeout_seconds: int = 300
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowDefinition:
    """Complete workflow definition"""
    id: str
    name: str
    version: str
    description: Optional[str]
    triggers: List[Trigger]
    steps: List[WorkflowStep]
    variables: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 3600
    retry_policy: Optional[RetryPolicy] = None
    tags: List[str] = field(default_factory=list)
    category: Optional[str] = None
    owner: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    is_template: bool = False


@dataclass
class StepExecution:
    """Individual step execution record"""
    step_id: str
    step_name: str
    status: WorkflowStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    retry_count: int = 0
    duration_ms: Optional[float] = None


@dataclass
class WorkflowExecution:
    """Workflow execution instance"""
    execution_id: str
    workflow_id: str
    workflow_version: str
    tenant_id: str
    status: WorkflowStatus
    trigger_type: TriggerType
    trigger_data: Dict[str, Any]
    input_data: Dict[str, Any]
    context: Dict[str, Any] = field(default_factory=dict)
    step_executions: List[StepExecution] = field(default_factory=list)
    current_step_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    correlation_id: Optional[str] = None
    parent_execution_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkflowAutomationEngine:
    """
    Core workflow automation engine for healthcare workflows.
    Supports visual workflow design, triggers, actions, and monitoring.
    """

    def __init__(self):
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.action_handlers: Dict[ActionType, Callable] = {}
        self.trigger_handlers: Dict[TriggerType, Callable] = {}
        self._setup_default_handlers()

    def _setup_default_handlers(self):
        """Setup default action and trigger handlers"""
        # Action handlers
        self.action_handlers = {
            ActionType.HTTP_REQUEST: self._handle_http_request,
            ActionType.DATABASE_QUERY: self._handle_database_query,
            ActionType.DATABASE_INSERT: self._handle_database_insert,
            ActionType.DATABASE_UPDATE: self._handle_database_update,
            ActionType.EMAIL: self._handle_email,
            ActionType.SMS: self._handle_sms,
            ActionType.PUSH_NOTIFICATION: self._handle_push_notification,
            ActionType.DOCUMENT_GENERATE: self._handle_document_generate,
            ActionType.TRANSFORM_DATA: self._handle_transform_data,
            ActionType.HUMAN_TASK: self._handle_human_task,
            ActionType.APPROVAL: self._handle_approval,
            ActionType.ML_PREDICTION: self._handle_ml_prediction,
            ActionType.FHIR_OPERATION: self._handle_fhir_operation,
            ActionType.CALL_WORKFLOW: self._handle_call_workflow,
            ActionType.WAIT: self._handle_wait,
            ActionType.LOG: self._handle_log,
        }

    # ==================== Workflow Management ====================

    async def register_workflow(self, definition: WorkflowDefinition) -> str:
        """Register a new workflow definition"""
        # Validate workflow
        await self._validate_workflow(definition)

        # Store definition
        self.workflows[definition.id] = definition

        return definition.id

    async def update_workflow(self, workflow_id: str, definition: WorkflowDefinition) -> str:
        """Update an existing workflow definition"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Validate workflow
        await self._validate_workflow(definition)

        # Increment version
        old_version = self.workflows[workflow_id].version
        definition.version = self._increment_version(old_version)
        definition.updated_at = datetime.utcnow()

        self.workflows[workflow_id] = definition
        return definition.id

    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow definition"""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            return True
        return False

    async def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Get a workflow definition by ID"""
        return self.workflows.get(workflow_id)

    async def list_workflows(
        self,
        tenant_id: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        tags: Optional[List[str]] = None
    ) -> List[WorkflowDefinition]:
        """List workflows with optional filtering"""
        workflows = list(self.workflows.values())

        if is_active is not None:
            workflows = [w for w in workflows if w.is_active == is_active]

        if category:
            workflows = [w for w in workflows if w.category == category]

        if tags:
            workflows = [w for w in workflows if any(t in w.tags for t in tags)]

        return workflows

    # ==================== Workflow Execution ====================

    async def execute_workflow(
        self,
        workflow_id: str,
        tenant_id: str,
        input_data: Dict[str, Any],
        trigger_type: TriggerType = TriggerType.API,
        trigger_data: Optional[Dict] = None,
        correlation_id: Optional[str] = None,
        parent_execution_id: Optional[str] = None
    ) -> str:
        """Execute a workflow instance"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        definition = self.workflows[workflow_id]

        # Create execution record
        execution_id = str(uuid4())
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            workflow_version=definition.version,
            tenant_id=tenant_id,
            status=WorkflowStatus.PENDING,
            trigger_type=trigger_type,
            trigger_data=trigger_data or {},
            input_data=input_data,
            context={**definition.variables, **input_data},
            correlation_id=correlation_id or str(uuid4()),
            parent_execution_id=parent_execution_id,
            started_at=datetime.utcnow()
        )

        self.executions[execution_id] = execution

        # Execute workflow asynchronously
        asyncio.create_task(self._run_workflow(execution_id))

        return execution_id

    async def _run_workflow(self, execution_id: str) -> None:
        """Internal workflow execution runner"""
        execution = self.executions.get(execution_id)
        if not execution:
            return

        definition = self.workflows.get(execution.workflow_id)
        if not definition:
            execution.status = WorkflowStatus.FAILED
            execution.error = "Workflow definition not found"
            return

        try:
            execution.status = WorkflowStatus.RUNNING

            # Build step execution order
            step_map = {step.id: step for step in definition.steps}
            executed_steps: set = set()

            # Execute steps in order
            for step in definition.steps:
                if step.id in executed_steps:
                    continue

                execution.current_step_id = step.id
                result = await self._execute_step(step, execution, step_map, executed_steps)

                if execution.status in [WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
                    break

            if execution.status == WorkflowStatus.RUNNING:
                execution.status = WorkflowStatus.COMPLETED

        except asyncio.TimeoutError:
            execution.status = WorkflowStatus.TIMED_OUT
            execution.error = "Workflow execution timed out"
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error = str(e)
        finally:
            execution.completed_at = datetime.utcnow()

    async def _execute_step(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution,
        step_map: Dict[str, WorkflowStep],
        executed_steps: set
    ) -> Dict[str, Any]:
        """Execute a single workflow step"""
        step_execution = StepExecution(
            step_id=step.id,
            step_name=step.name,
            status=WorkflowStatus.RUNNING,
            started_at=datetime.utcnow(),
            input_data=dict(execution.context)
        )
        execution.step_executions.append(step_execution)

        try:
            result = {}

            if step.type == StepType.ACTION:
                result = await self._execute_action(step.action, execution.context)

            elif step.type == StepType.CONDITION:
                condition_met = self._evaluate_conditions(step.conditions, execution.context)
                next_steps = step.then_steps if condition_met else step.else_steps

                if next_steps:
                    for next_step_id in next_steps:
                        if next_step_id in step_map and next_step_id not in executed_steps:
                            await self._execute_step(
                                step_map[next_step_id], execution, step_map, executed_steps
                            )
                            executed_steps.add(next_step_id)

                result = {"condition_met": condition_met}

            elif step.type == StepType.LOOP:
                items = self._resolve_expression(step.loop_items, execution.context)
                loop_results = []

                for idx, item in enumerate(items or []):
                    loop_context = {**execution.context, "item": item, "index": idx}
                    for body_step_id in step.loop_body or []:
                        if body_step_id in step_map:
                            body_step = step_map[body_step_id]
                            body_result = await self._execute_action(
                                body_step.action, loop_context
                            )
                            loop_results.append(body_result)
                            loop_context.update(body_result)

                result = {"loop_results": loop_results}

            elif step.type == StepType.PARALLEL:
                parallel_tasks = []
                for branch in step.parallel_branches or []:
                    branch_task = self._execute_parallel_branch(
                        branch, execution, step_map, executed_steps
                    )
                    parallel_tasks.append(branch_task)

                branch_results = await asyncio.gather(*parallel_tasks, return_exceptions=True)
                result = {"parallel_results": branch_results}

            elif step.type == StepType.SWITCH:
                switch_value = self._resolve_expression(
                    step.conditions[0].field if step.conditions else "", execution.context
                )
                case_steps = step.switch_cases.get(str(switch_value), step.default_case)

                if case_steps:
                    for case_step_id in case_steps:
                        if case_step_id in step_map and case_step_id not in executed_steps:
                            await self._execute_step(
                                step_map[case_step_id], execution, step_map, executed_steps
                            )
                            executed_steps.add(case_step_id)

                result = {"switch_value": switch_value}

            # Update context with result
            execution.context[f"step_{step.id}_result"] = result
            execution.context.update(result)

            step_execution.status = WorkflowStatus.COMPLETED
            step_execution.output_data = result
            executed_steps.add(step.id)

            return result

        except Exception as e:
            step_execution.status = WorkflowStatus.FAILED
            step_execution.error = str(e)

            # Check for retry
            if step.retry_policy and step_execution.retry_count < step.retry_policy.max_attempts:
                step_execution.retry_count += 1
                delay = self._calculate_retry_delay(step.retry_policy, step_execution.retry_count)
                await asyncio.sleep(delay)
                return await self._execute_step(step, execution, step_map, executed_steps)

            # Check for error handlers
            if step.error_handlers:
                await self._handle_step_error(e, step, execution, step_map)
            else:
                raise

        finally:
            step_execution.completed_at = datetime.utcnow()
            if step_execution.started_at:
                step_execution.duration_ms = (
                    step_execution.completed_at - step_execution.started_at
                ).total_seconds() * 1000

        return {}

    async def _execute_parallel_branch(
        self,
        branch_step_ids: List[str],
        execution: WorkflowExecution,
        step_map: Dict[str, WorkflowStep],
        executed_steps: set
    ) -> List[Dict]:
        """Execute a parallel branch"""
        results = []
        for step_id in branch_step_ids:
            if step_id in step_map:
                result = await self._execute_step(
                    step_map[step_id], execution, step_map, executed_steps
                )
                results.append(result)
        return results

    async def _execute_action(self, action: Action, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow action"""
        if not action:
            return {}

        handler = self.action_handlers.get(action.type)
        if not handler:
            raise ValueError(f"No handler for action type: {action.type}")

        # Resolve variable references in config
        resolved_config = self._resolve_config(action.config, context)

        return await handler(resolved_config, context)

    # ==================== Action Handlers ====================

    async def _handle_http_request(self, config: Dict, context: Dict) -> Dict:
        """Handle HTTP request action"""
        # In production, use httpx or aiohttp
        return {
            "status": "success",
            "status_code": 200,
            "response": {"mock": "response"},
            "url": config.get("url"),
            "method": config.get("method", "GET")
        }

    async def _handle_database_query(self, config: Dict, context: Dict) -> Dict:
        """Handle database query action"""
        return {
            "status": "success",
            "rows": [],
            "query": config.get("query")
        }

    async def _handle_database_insert(self, config: Dict, context: Dict) -> Dict:
        """Handle database insert action"""
        return {
            "status": "success",
            "inserted_id": str(uuid4()),
            "table": config.get("table")
        }

    async def _handle_database_update(self, config: Dict, context: Dict) -> Dict:
        """Handle database update action"""
        return {
            "status": "success",
            "affected_rows": 1,
            "table": config.get("table")
        }

    async def _handle_email(self, config: Dict, context: Dict) -> Dict:
        """Handle email action"""
        return {
            "status": "success",
            "message_id": str(uuid4()),
            "recipients": config.get("to", []),
            "subject": config.get("subject")
        }

    async def _handle_sms(self, config: Dict, context: Dict) -> Dict:
        """Handle SMS action"""
        return {
            "status": "success",
            "message_id": str(uuid4()),
            "recipient": config.get("to")
        }

    async def _handle_push_notification(self, config: Dict, context: Dict) -> Dict:
        """Handle push notification action"""
        return {
            "status": "success",
            "notification_id": str(uuid4()),
            "recipients": config.get("recipients", [])
        }

    async def _handle_document_generate(self, config: Dict, context: Dict) -> Dict:
        """Handle document generation action"""
        return {
            "status": "success",
            "document_id": str(uuid4()),
            "template": config.get("template"),
            "format": config.get("format", "pdf")
        }

    async def _handle_transform_data(self, config: Dict, context: Dict) -> Dict:
        """Handle data transformation action"""
        result = dict(context)
        for transform in config.get("transformations", []):
            transform_type = transform.get("type")
            if transform_type == "map":
                source = transform.get("source")
                target = transform.get("target")
                if source in result:
                    result[target] = result[source]
            elif transform_type == "filter":
                field = transform.get("field")
                condition = transform.get("condition")
                # Apply filter logic
            elif transform_type == "aggregate":
                # Apply aggregation logic
                pass

        return {"transformed_data": result}

    async def _handle_human_task(self, config: Dict, context: Dict) -> Dict:
        """Handle human task creation"""
        return {
            "status": "created",
            "task_id": str(uuid4()),
            "title": config.get("title"),
            "assignee": config.get("assignee"),
            "priority": config.get("priority", "normal"),
            "due_date": (datetime.utcnow() + timedelta(hours=config.get("due_hours", 24))).isoformat()
        }

    async def _handle_approval(self, config: Dict, context: Dict) -> Dict:
        """Handle approval request"""
        return {
            "status": "pending_approval",
            "approval_id": str(uuid4()),
            "title": config.get("title"),
            "approvers": config.get("approvers", []),
            "approval_type": config.get("approval_type", "any")
        }

    async def _handle_ml_prediction(self, config: Dict, context: Dict) -> Dict:
        """Handle ML prediction action"""
        return {
            "status": "success",
            "prediction_id": str(uuid4()),
            "model": config.get("model_name"),
            "prediction": 0.75,  # Mock prediction
            "confidence": 0.85
        }

    async def _handle_fhir_operation(self, config: Dict, context: Dict) -> Dict:
        """Handle FHIR operation action"""
        return {
            "status": "success",
            "operation": config.get("operation"),
            "resource_type": config.get("resource_type"),
            "resource_id": str(uuid4())
        }

    async def _handle_call_workflow(self, config: Dict, context: Dict) -> Dict:
        """Handle sub-workflow call"""
        sub_workflow_id = config.get("workflow_id")
        # Would execute sub-workflow here
        return {
            "status": "success",
            "sub_workflow_id": sub_workflow_id,
            "execution_id": str(uuid4())
        }

    async def _handle_wait(self, config: Dict, context: Dict) -> Dict:
        """Handle wait action"""
        wait_seconds = config.get("seconds", 0)
        await asyncio.sleep(wait_seconds)
        return {
            "status": "completed",
            "waited_seconds": wait_seconds
        }

    async def _handle_log(self, config: Dict, context: Dict) -> Dict:
        """Handle log action"""
        return {
            "status": "logged",
            "level": config.get("level", "info"),
            "message": config.get("message")
        }

    # ==================== Helper Methods ====================

    def _evaluate_conditions(self, conditions: List[Condition], context: Dict) -> bool:
        """Evaluate a list of conditions"""
        if not conditions:
            return True

        # Group by logic operator
        and_conditions = [c for c in conditions if c.logic == "AND"]
        or_conditions = [c for c in conditions if c.logic == "OR"]

        and_result = all(c.evaluate(context) for c in and_conditions) if and_conditions else True
        or_result = any(c.evaluate(context) for c in or_conditions) if or_conditions else True

        return and_result and (or_result if or_conditions else True)

    def _resolve_expression(self, expression: str, context: Dict) -> Any:
        """Resolve a variable expression like ${variable.path}"""
        if not expression:
            return None

        if not expression.startswith("${"):
            return expression

        path = expression[2:-1]  # Remove ${ and }
        return self._get_nested_value(path, context)

    def _resolve_config(self, config: Dict, context: Dict) -> Dict:
        """Resolve all variable references in config"""
        resolved = {}
        for key, value in config.items():
            if isinstance(value, str) and "${" in value:
                resolved[key] = self._resolve_expression(value, context)
            elif isinstance(value, dict):
                resolved[key] = self._resolve_config(value, context)
            elif isinstance(value, list):
                resolved[key] = [
                    self._resolve_expression(v, context) if isinstance(v, str) and "${" in v else v
                    for v in value
                ]
            else:
                resolved[key] = value
        return resolved

    def _get_nested_value(self, path: str, context: Dict) -> Any:
        """Get nested value from context using dot notation"""
        parts = path.split('.')
        value = context
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif isinstance(value, list) and part.isdigit():
                idx = int(part)
                value = value[idx] if idx < len(value) else None
            else:
                return None
        return value

    def _calculate_retry_delay(self, policy: RetryPolicy, attempt: int) -> float:
        """Calculate delay before retry"""
        if policy.strategy == RetryStrategy.FIXED:
            return policy.initial_delay_seconds
        elif policy.strategy == RetryStrategy.LINEAR:
            return policy.initial_delay_seconds * attempt
        elif policy.strategy == RetryStrategy.EXPONENTIAL:
            delay = policy.initial_delay_seconds * (policy.backoff_multiplier ** (attempt - 1))
            return min(delay, policy.max_delay_seconds)
        return 0

    def _increment_version(self, version: str) -> str:
        """Increment semantic version"""
        parts = version.split('.')
        if len(parts) == 3:
            parts[2] = str(int(parts[2]) + 1)
        return '.'.join(parts)

    async def _validate_workflow(self, definition: WorkflowDefinition) -> None:
        """Validate workflow definition"""
        if not definition.id:
            raise ValueError("Workflow ID is required")

        if not definition.name:
            raise ValueError("Workflow name is required")

        if not definition.triggers:
            raise ValueError("At least one trigger is required")

        if not definition.steps:
            raise ValueError("At least one step is required")

        # Validate step references
        step_ids = {step.id for step in definition.steps}
        for step in definition.steps:
            if step.then_steps:
                for ref in step.then_steps:
                    if ref not in step_ids:
                        raise ValueError(f"Invalid step reference: {ref}")
            if step.else_steps:
                for ref in step.else_steps:
                    if ref not in step_ids:
                        raise ValueError(f"Invalid step reference: {ref}")

    async def _handle_step_error(
        self,
        error: Exception,
        step: WorkflowStep,
        execution: WorkflowExecution,
        step_map: Dict[str, WorkflowStep]
    ) -> None:
        """Handle step error with error handlers"""
        for handler in step.error_handlers or []:
            error_type = handler.get("error_type", "*")
            if error_type == "*" or error_type in str(type(error).__name__):
                handler_action = handler.get("action")
                if handler_action:
                    action = Action(
                        type=ActionType(handler_action.get("type", "log")),
                        config=handler_action
                    )
                    await self._execute_action(action, {
                        **execution.context,
                        "error": str(error),
                        "error_type": type(error).__name__
                    })

    # ==================== Execution Management ====================

    async def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get execution status"""
        return self.executions.get(execution_id)

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution"""
        execution = self.executions.get(execution_id)
        if execution and execution.status == WorkflowStatus.RUNNING:
            execution.status = WorkflowStatus.CANCELLED
            execution.completed_at = datetime.utcnow()
            return True
        return False

    async def pause_execution(self, execution_id: str) -> bool:
        """Pause a running execution"""
        execution = self.executions.get(execution_id)
        if execution and execution.status == WorkflowStatus.RUNNING:
            execution.status = WorkflowStatus.PAUSED
            return True
        return False

    async def resume_execution(self, execution_id: str) -> bool:
        """Resume a paused execution"""
        execution = self.executions.get(execution_id)
        if execution and execution.status == WorkflowStatus.PAUSED:
            execution.status = WorkflowStatus.RUNNING
            asyncio.create_task(self._run_workflow(execution_id))
            return True
        return False

    async def list_executions(
        self,
        tenant_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        status: Optional[WorkflowStatus] = None,
        limit: int = 100
    ) -> List[WorkflowExecution]:
        """List workflow executions"""
        executions = list(self.executions.values())

        if tenant_id:
            executions = [e for e in executions if e.tenant_id == tenant_id]

        if workflow_id:
            executions = [e for e in executions if e.workflow_id == workflow_id]

        if status:
            executions = [e for e in executions if e.status == status]

        # Sort by start time descending
        executions.sort(key=lambda x: x.started_at or datetime.min, reverse=True)

        return executions[:limit]


# Singleton instance
workflow_automation_engine = WorkflowAutomationEngine()


def get_workflow_automation_engine() -> WorkflowAutomationEngine:
    """Get the singleton workflow automation engine instance"""
    return workflow_automation_engine
