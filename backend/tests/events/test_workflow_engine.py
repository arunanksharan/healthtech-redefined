"""
Unit tests for workflow engine
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from shared.events import (
    WorkflowEngine,
    WorkflowDefinition,
    WorkflowStep,
    WorkflowState,
    StepState,
)


@pytest.fixture
def engine():
    """Create workflow engine instance"""
    return WorkflowEngine()


@pytest.fixture
def simple_workflow():
    """Create simple test workflow"""
    return WorkflowDefinition(
        workflow_id="test-workflow",
        name="Test Workflow",
        description="Simple test workflow",
        steps=[
            WorkflowStep(
                step_id="step1",
                name="Step 1",
                action="action1",
            ),
            WorkflowStep(
                step_id="step2",
                name="Step 2",
                action="action2",
            ),
        ],
    )


@pytest.fixture
def workflow_with_compensation():
    """Create workflow with compensation actions"""
    return WorkflowDefinition(
        workflow_id="compensatable-workflow",
        name="Compensatable Workflow",
        description="Workflow with compensation",
        steps=[
            WorkflowStep(
                step_id="step1",
                name="Step 1",
                action="action1",
                compensation_action="compensate1",
            ),
            WorkflowStep(
                step_id="step2",
                name="Step 2",
                action="action2",
                compensation_action="compensate2",
            ),
        ],
    )


class TestWorkflowEngine:
    """Test WorkflowEngine class"""

    def test_register_workflow(self, engine, simple_workflow):
        """Test registering a workflow"""
        engine.register_workflow(simple_workflow)

        assert "test-workflow" in engine.workflows
        assert engine.workflows["test-workflow"].name == "Test Workflow"

    def test_register_action(self, engine):
        """Test registering an action handler"""
        async def test_action(context, input_data):
            return {"result": "success"}

        engine.register_action("test-action", test_action)

        assert "test-action" in engine.action_handlers

    def test_register_compensation(self, engine):
        """Test registering compensation handler"""
        async def test_compensation(context, output_data):
            pass

        engine.register_compensation("test-compensation", test_compensation)

        assert "test-compensation" in engine.compensation_handlers

    @pytest.mark.asyncio
    async def test_start_workflow(self, engine, simple_workflow):
        """Test starting a workflow"""
        engine.register_workflow(simple_workflow)

        # Register mock handlers
        async def action1(context, input_data):
            return {"step1": "done"}

        async def action2(context, input_data):
            return {"step2": "done"}

        engine.register_action("action1", action1)
        engine.register_action("action2", action2)

        instance_id = await engine.start_workflow(
            workflow_id="test-workflow",
            tenant_id="tenant-1",
        )

        assert instance_id is not None
        assert instance_id in engine.instances

        # Wait for workflow to complete
        await asyncio.sleep(0.5)

        instance = engine.get_instance(instance_id)
        assert instance.state == WorkflowState.COMPLETED

    @pytest.mark.asyncio
    async def test_workflow_step_execution(self, engine, simple_workflow):
        """Test workflow step execution"""
        engine.register_workflow(simple_workflow)

        step_executed = []

        async def action1(context, input_data):
            step_executed.append("action1")
            return {"step1": "done"}

        async def action2(context, input_data):
            step_executed.append("action2")
            return {"step2": "done"}

        engine.register_action("action1", action1)
        engine.register_action("action2", action2)

        instance_id = await engine.start_workflow(
            workflow_id="test-workflow",
            tenant_id="tenant-1",
        )

        await asyncio.sleep(0.5)

        assert len(step_executed) == 2
        assert step_executed == ["action1", "action2"]

    @pytest.mark.asyncio
    async def test_workflow_context(self, engine, simple_workflow):
        """Test workflow context sharing"""
        engine.register_workflow(simple_workflow)

        async def action1(context, input_data):
            context["data_from_step1"] = "shared_data"
            return {"step1": "done"}

        async def action2(context, input_data):
            assert "data_from_step1" in context
            assert context["data_from_step1"] == "shared_data"
            return {"step2": "done"}

        engine.register_action("action1", action1)
        engine.register_action("action2", action2)

        instance_id = await engine.start_workflow(
            workflow_id="test-workflow",
            tenant_id="tenant-1",
            context={"initial": "data"},
        )

        await asyncio.sleep(0.5)

        instance = engine.get_instance(instance_id)
        assert instance.context["initial"] == "data"
        assert instance.context["data_from_step1"] == "shared_data"

    @pytest.mark.asyncio
    async def test_workflow_compensation_on_failure(
        self, engine, workflow_with_compensation
    ):
        """Test workflow compensation when step fails"""
        engine.register_workflow(workflow_with_compensation)

        compensations_executed = []

        async def action1(context, input_data):
            return {"step1": "done"}

        async def action2(context, input_data):
            raise Exception("Step 2 failed")

        async def compensate1(context, output_data):
            compensations_executed.append("compensate1")

        async def compensate2(context, output_data):
            compensations_executed.append("compensate2")

        engine.register_action("action1", action1)
        engine.register_action("action2", action2)
        engine.register_compensation("compensate1", compensate1)
        engine.register_compensation("compensate2", compensate2)

        instance_id = await engine.start_workflow(
            workflow_id="compensatable-workflow",
            tenant_id="tenant-1",
        )

        await asyncio.sleep(0.5)

        instance = engine.get_instance(instance_id)
        assert instance.state == WorkflowState.COMPENSATED

        # Only step1 should be compensated (step2 never completed)
        assert "compensate1" in compensations_executed

    @pytest.mark.asyncio
    async def test_workflow_step_retry(self, engine):
        """Test workflow step retry on failure"""
        workflow = WorkflowDefinition(
            workflow_id="retry-workflow",
            name="Retry Workflow",
            description="Test retry",
            steps=[
                WorkflowStep(
                    step_id="step1",
                    name="Step 1",
                    action="failing_action",
                    retry_count=3,
                ),
            ],
        )

        engine.register_workflow(workflow)

        attempts = []

        async def failing_action(context, input_data):
            attempts.append(1)
            if len(attempts) < 2:
                raise Exception("Temporary failure")
            return {"success": True}

        engine.register_action("failing_action", failing_action)

        instance_id = await engine.start_workflow(
            workflow_id="retry-workflow",
            tenant_id="tenant-1",
        )

        await asyncio.sleep(3)  # Wait for retries

        # Should have retried and eventually succeeded
        assert len(attempts) >= 2

    @pytest.mark.asyncio
    async def test_get_instance_state(self, engine, simple_workflow):
        """Test getting workflow instance state"""
        engine.register_workflow(simple_workflow)

        async def action1(context, input_data):
            await asyncio.sleep(0.1)
            return {}

        async def action2(context, input_data):
            await asyncio.sleep(0.1)
            return {}

        engine.register_action("action1", action1)
        engine.register_action("action2", action2)

        instance_id = await engine.start_workflow(
            workflow_id="test-workflow",
            tenant_id="tenant-1",
        )

        # Check initial state
        state = engine.get_instance_state(instance_id)
        assert state == WorkflowState.RUNNING

        # Wait for completion
        await asyncio.sleep(0.5)

        # Check final state
        state = engine.get_instance_state(instance_id)
        assert state == WorkflowState.COMPLETED
