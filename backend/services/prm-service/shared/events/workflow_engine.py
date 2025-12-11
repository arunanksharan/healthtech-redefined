"""
Event-driven workflow engine with saga pattern support
Orchestrates complex multi-step healthcare workflows
"""
import asyncio
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID, uuid4

from loguru import logger
from pydantic import BaseModel

from .publisher import publish_event
from .types import Event, EventType


class WorkflowState(str, Enum):
    """Workflow execution states"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"  # Rolling back
    COMPENSATED = "compensated"  # Rolled back


class StepState(str, Enum):
    """Workflow step states"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"


class WorkflowStep(BaseModel):
    """Individual step in a workflow"""

    step_id: str
    name: str
    action: str  # Function name or action identifier
    compensation_action: Optional[str] = None  # Compensation function
    timeout_seconds: int = 300
    retry_count: int = 3
    state: StepState = StepState.PENDING
    input_data: Dict[str, Any] = {}
    output_data: Dict[str, Any] = {}
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class WorkflowDefinition(BaseModel):
    """Definition of a workflow"""

    workflow_id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    enable_compensation: bool = True  # Enable saga pattern
    metadata: Dict[str, Any] = {}


class WorkflowInstance(BaseModel):
    """Running instance of a workflow"""

    instance_id: UUID
    workflow_id: str
    tenant_id: str
    state: WorkflowState = WorkflowState.PENDING
    current_step_index: int = 0
    steps: List[WorkflowStep]
    context: Dict[str, Any] = {}  # Shared context across steps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class WorkflowEngine:
    """
    Event-driven workflow engine with saga pattern

    Features:
    - State machine for workflow execution
    - Step-by-step execution with retry
    - Saga pattern for distributed transactions
    - Compensation/rollback on failure
    - Event-driven state transitions
    - Long-running workflow support
    """

    def __init__(self):
        """Initialize workflow engine"""
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.instances: Dict[UUID, WorkflowInstance] = {}
        self.action_handlers: Dict[str, Callable] = {}
        self.compensation_handlers: Dict[str, Callable] = {}

    def register_workflow(self, workflow: WorkflowDefinition):
        """
        Register a workflow definition

        Args:
            workflow: Workflow definition to register
        """
        self.workflows[workflow.workflow_id] = workflow
        logger.info(f"Workflow registered: {workflow.name} ({workflow.workflow_id})")

    def register_action(self, action_name: str, handler: Callable):
        """
        Register an action handler

        Args:
            action_name: Name of action
            handler: Async function to execute action
        """
        self.action_handlers[action_name] = handler
        logger.info(f"Action registered: {action_name}")

    def register_compensation(self, action_name: str, handler: Callable):
        """
        Register a compensation handler

        Args:
            action_name: Name of compensation action
            handler: Async function to execute compensation
        """
        self.compensation_handlers[action_name] = handler
        logger.info(f"Compensation registered: {action_name}")

    async def start_workflow(
        self,
        workflow_id: str,
        tenant_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> UUID:
        """
        Start a new workflow instance

        Args:
            workflow_id: ID of workflow definition
            tenant_id: Tenant identifier
            context: Initial context data

        Returns:
            UUID: Instance ID

        Raises:
            ValueError: If workflow not found
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow_def = self.workflows[workflow_id]
        instance_id = uuid4()

        # Create instance with copied steps
        instance = WorkflowInstance(
            instance_id=instance_id,
            workflow_id=workflow_id,
            tenant_id=tenant_id,
            state=WorkflowState.RUNNING,
            steps=[step.model_copy(deep=True) for step in workflow_def.steps],
            context=context or {},
            started_at=datetime.utcnow(),
        )

        self.instances[instance_id] = instance

        logger.info(
            f"Started workflow: {workflow_def.name} "
            f"(instance_id={instance_id})"
        )

        # Publish workflow started event
        await publish_event(
            event_type=EventType.JOURNEY_INSTANCE_CREATED,
            tenant_id=tenant_id,
            payload={
                "instance_id": str(instance_id),
                "workflow_id": workflow_id,
                "workflow_name": workflow_def.name,
            },
            source_service="workflow-engine",
        )

        # Start execution
        asyncio.create_task(self._execute_workflow(instance_id))

        return instance_id

    async def _execute_workflow(self, instance_id: UUID):
        """
        Execute workflow steps

        Args:
            instance_id: Workflow instance ID
        """
        instance = self.instances[instance_id]

        try:
            while instance.current_step_index < len(instance.steps):
                step = instance.steps[instance.current_step_index]

                # Execute step
                success = await self._execute_step(instance, step)

                if not success:
                    # Step failed, trigger compensation if enabled
                    if instance.steps[0].model_dump().get("enable_compensation", True):
                        await self._compensate_workflow(instance)
                    else:
                        instance.state = WorkflowState.FAILED
                    return

                # Move to next step
                instance.current_step_index += 1

            # All steps completed
            instance.state = WorkflowState.COMPLETED
            instance.completed_at = datetime.utcnow()

            logger.info(f"Workflow completed: {instance_id}")

            # Publish completion event
            await publish_event(
                event_type=EventType.JOURNEY_INSTANCE_COMPLETED,
                tenant_id=instance.tenant_id,
                payload={
                    "instance_id": str(instance_id),
                    "workflow_id": instance.workflow_id,
                },
                source_service="workflow-engine",
            )

        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            instance.state = WorkflowState.FAILED
            instance.error = str(e)

    async def _execute_step(
        self, instance: WorkflowInstance, step: WorkflowStep
    ) -> bool:
        """
        Execute a workflow step with retry

        Args:
            instance: Workflow instance
            step: Step to execute

        Returns:
            bool: True if successful, False if failed
        """
        step.state = StepState.RUNNING
        step.started_at = datetime.utcnow()

        logger.info(
            f"Executing step: {step.name} "
            f"(workflow={instance.instance_id}, step={step.step_id})"
        )

        # Publish step started event
        await publish_event(
            event_type=EventType.JOURNEY_STAGE_ENTERED,
            tenant_id=instance.tenant_id,
            payload={
                "instance_id": str(instance.instance_id),
                "step_id": step.step_id,
                "step_name": step.name,
            },
            source_service="workflow-engine",
        )

        # Get action handler
        if step.action not in self.action_handlers:
            logger.error(f"Action handler not found: {step.action}")
            step.state = StepState.FAILED
            step.error = f"Handler not found: {step.action}"
            return False

        handler = self.action_handlers[step.action]

        # Execute with retry
        for attempt in range(step.retry_count):
            try:
                # Execute action
                result = await asyncio.wait_for(
                    handler(instance.context, step.input_data),
                    timeout=step.timeout_seconds,
                )

                # Store output
                step.output_data = result or {}
                step.state = StepState.COMPLETED
                step.completed_at = datetime.utcnow()

                logger.info(f"Step completed: {step.name}")

                # Publish step completed event
                await publish_event(
                    event_type=EventType.JOURNEY_STAGE_COMPLETED,
                    tenant_id=instance.tenant_id,
                    payload={
                        "instance_id": str(instance.instance_id),
                        "step_id": step.step_id,
                        "step_name": step.name,
                    },
                    source_service="workflow-engine",
                )

                return True

            except asyncio.TimeoutError:
                logger.warning(
                    f"Step timeout: {step.name} (attempt {attempt + 1})"
                )
            except Exception as e:
                logger.error(
                    f"Step execution error: {step.name} - {e} "
                    f"(attempt {attempt + 1})"
                )

            # Retry delay with exponential backoff
            if attempt < step.retry_count - 1:
                await asyncio.sleep(2 ** attempt)

        # All retries failed
        step.state = StepState.FAILED
        step.error = f"Failed after {step.retry_count} attempts"
        instance.state = WorkflowState.FAILED
        return False

    async def _compensate_workflow(self, instance: WorkflowInstance):
        """
        Compensate (rollback) workflow using saga pattern

        Args:
            instance: Workflow instance
        """
        logger.warning(
            f"Starting compensation for workflow: {instance.instance_id}"
        )

        instance.state = WorkflowState.COMPENSATING

        # Compensate completed steps in reverse order
        for i in range(instance.current_step_index - 1, -1, -1):
            step = instance.steps[i]

            if step.state != StepState.COMPLETED:
                continue  # Skip non-completed steps

            if not step.compensation_action:
                logger.warning(
                    f"No compensation action for step: {step.name}"
                )
                continue

            await self._compensate_step(instance, step)

        instance.state = WorkflowState.COMPENSATED
        instance.completed_at = datetime.utcnow()

        logger.info(f"Workflow compensated: {instance.instance_id}")

    async def _compensate_step(
        self, instance: WorkflowInstance, step: WorkflowStep
    ):
        """
        Compensate a single step

        Args:
            instance: Workflow instance
            step: Step to compensate
        """
        step.state = StepState.COMPENSATING

        logger.info(f"Compensating step: {step.name}")

        if step.compensation_action not in self.compensation_handlers:
            logger.error(
                f"Compensation handler not found: {step.compensation_action}"
            )
            return

        handler = self.compensation_handlers[step.compensation_action]

        try:
            await handler(instance.context, step.output_data)
            step.state = StepState.COMPENSATED
            logger.info(f"Step compensated: {step.name}")

        except Exception as e:
            logger.error(f"Compensation failed for step {step.name}: {e}")
            # Continue with other compensations

    def get_instance(self, instance_id: UUID) -> Optional[WorkflowInstance]:
        """Get workflow instance by ID"""
        return self.instances.get(instance_id)

    def get_instance_state(self, instance_id: UUID) -> Optional[WorkflowState]:
        """Get workflow instance state"""
        instance = self.instances.get(instance_id)
        return instance.state if instance else None


# Global workflow engine instance
_workflow_engine: Optional[WorkflowEngine] = None


def get_workflow_engine() -> WorkflowEngine:
    """Get or create global workflow engine"""
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = WorkflowEngine()
    return _workflow_engine


# Example workflow definition
async def example_patient_onboarding_workflow():
    """Example: Patient onboarding workflow"""
    engine = get_workflow_engine()

    # Define workflow
    workflow = WorkflowDefinition(
        workflow_id="patient-onboarding",
        name="Patient Onboarding",
        description="Complete patient onboarding process",
        steps=[
            WorkflowStep(
                step_id="validate-identity",
                name="Validate Patient Identity",
                action="validate_identity",
                compensation_action="revert_identity_validation",
            ),
            WorkflowStep(
                step_id="create-patient-record",
                name="Create Patient Record",
                action="create_patient_record",
                compensation_action="delete_patient_record",
            ),
            WorkflowStep(
                step_id="setup-consents",
                name="Setup Consent Preferences",
                action="setup_consents",
                compensation_action="revoke_consents",
            ),
            WorkflowStep(
                step_id="send-welcome-message",
                name="Send Welcome Message",
                action="send_welcome_message",
            ),
        ],
    )

    engine.register_workflow(workflow)

    # Register action handlers
    async def validate_identity(context: Dict, input_data: Dict) -> Dict:
        logger.info("Validating patient identity...")
        await asyncio.sleep(1)  # Simulate work
        return {"validated": True, "patient_id": "PAT123"}

    async def create_patient_record(context: Dict, input_data: Dict) -> Dict:
        logger.info("Creating patient record...")
        patient_id = context.get("patient_id", "PAT123")
        await asyncio.sleep(1)
        return {"record_id": "REC456", "patient_id": patient_id}

    async def setup_consents(context: Dict, input_data: Dict) -> Dict:
        logger.info("Setting up consents...")
        await asyncio.sleep(1)
        return {"consents_created": True}

    async def send_welcome_message(context: Dict, input_data: Dict) -> Dict:
        logger.info("Sending welcome message...")
        await asyncio.sleep(1)
        return {"message_sent": True}

    # Register compensation handlers
    async def delete_patient_record(context: Dict, output_data: Dict):
        logger.info("Compensating: Deleting patient record...")
        await asyncio.sleep(1)

    async def revoke_consents(context: Dict, output_data: Dict):
        logger.info("Compensating: Revoking consents...")
        await asyncio.sleep(1)

    engine.register_action("validate_identity", validate_identity)
    engine.register_action("create_patient_record", create_patient_record)
    engine.register_action("setup_consents", setup_consents)
    engine.register_action("send_welcome_message", send_welcome_message)

    engine.register_compensation("delete_patient_record", delete_patient_record)
    engine.register_compensation("revoke_consents", revoke_consents)

    # Start workflow
    instance_id = await engine.start_workflow(
        workflow_id="patient-onboarding",
        tenant_id="hospital-1",
        context={"patient_name": "John Doe"},
    )

    return instance_id
