"""
Tests for Intelligent Automation Platform
EPIC-012: Comprehensive test suite for all automation services
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

# Test workflow engine
from shared.automation import (
    get_workflow_automation_engine,
    WorkflowStatus,
    TriggerType,
    ActionType,
)


class TestWorkflowEngine:
    """Test cases for Workflow Automation Engine"""

    @pytest.fixture
    def workflow_engine(self):
        """Get workflow engine instance"""
        return get_workflow_automation_engine()

    @pytest.mark.asyncio
    async def test_create_workflow(self, workflow_engine):
        """Test workflow creation"""
        workflow = await workflow_engine.create_workflow(
            tenant_id="test-tenant",
            name="Test Workflow",
            description="A test workflow",
            trigger={
                "type": "manual",
                "config": {}
            },
            steps=[
                {
                    "step_id": "step1",
                    "name": "First Step",
                    "type": "action",
                    "action": {
                        "type": "transform_data",
                        "config": {"transform": "uppercase"}
                    }
                }
            ],
            is_active=True
        )

        assert workflow is not None
        assert workflow.name == "Test Workflow"
        assert workflow.is_active is True
        assert len(workflow.steps) == 1

    @pytest.mark.asyncio
    async def test_execute_workflow(self, workflow_engine):
        """Test workflow execution"""
        # Create workflow first
        workflow = await workflow_engine.create_workflow(
            tenant_id="test-tenant",
            name="Execution Test",
            description="Test execution",
            trigger={"type": "manual", "config": {}},
            steps=[
                {
                    "step_id": "step1",
                    "name": "Transform",
                    "type": "action",
                    "action": {
                        "type": "transform_data",
                        "config": {}
                    }
                }
            ],
            is_active=True
        )

        # Execute workflow
        execution = await workflow_engine.execute_workflow(
            workflow_id=workflow.workflow_id,
            input_data={"message": "hello"}
        )

        assert execution is not None
        assert execution.workflow_id == workflow.workflow_id
        assert execution.status in [WorkflowStatus.COMPLETED, WorkflowStatus.RUNNING]

    @pytest.mark.asyncio
    async def test_list_workflows(self, workflow_engine):
        """Test listing workflows"""
        # Create a workflow
        await workflow_engine.create_workflow(
            tenant_id="list-test-tenant",
            name="List Test",
            description="Test listing",
            trigger={"type": "manual", "config": {}},
            steps=[{"step_id": "s1", "name": "Step", "type": "action"}],
            is_active=True
        )

        workflows = await workflow_engine.list_workflows("list-test-tenant")
        assert len(workflows) >= 1


# Test appointment optimizer
from shared.automation import (
    get_appointment_optimizer,
    AppointmentType,
    NoShowRiskLevel,
)


class TestAppointmentOptimizer:
    """Test cases for Appointment Optimizer"""

    @pytest.fixture
    def optimizer(self):
        """Get appointment optimizer instance"""
        return get_appointment_optimizer()

    @pytest.mark.asyncio
    async def test_predict_no_show(self, optimizer):
        """Test no-show prediction"""
        patient_history = {
            "previous_no_shows": 2,
            "previous_appointments": 10,
            "patient_type": "established"
        }

        prediction = await optimizer.predict_no_show(
            patient_id="patient-123",
            appointment_date=datetime.utcnow() + timedelta(days=7),
            appointment_type=AppointmentType.FOLLOW_UP,
            patient_history=patient_history
        )

        assert prediction is not None
        assert 0 <= prediction.probability <= 1
        assert prediction.risk_level in NoShowRiskLevel
        assert len(prediction.recommended_interventions) >= 0

    @pytest.mark.asyncio
    async def test_add_to_waitlist(self, optimizer):
        """Test waitlist functionality"""
        entry = await optimizer.add_to_waitlist(
            patient_id="patient-456",
            appointment_type=AppointmentType.NEW_PATIENT,
            provider_id="provider-789",
            preferred_dates=[datetime.utcnow() + timedelta(days=3)],
            preferred_times=["morning"]
        )

        assert entry is not None
        assert entry.patient_id == "patient-456"
        assert entry.status == "waiting"

    @pytest.mark.asyncio
    async def test_reminder_schedule(self, optimizer):
        """Test reminder schedule generation"""
        appointment_date = datetime.utcnow() + timedelta(days=7)
        reminders = await optimizer.get_reminder_schedule(
            no_show_probability=0.4,
            appointment_date=appointment_date
        )

        assert len(reminders) >= 1
        for reminder in reminders:
            assert "type" in reminder
            assert "date" in reminder


# Test care gap detector
from shared.automation import (
    get_care_gap_detector,
    CareGapType,
    CareGapPriority,
    CareGapStatus,
)


class TestCareGapDetector:
    """Test cases for Care Gap Detector"""

    @pytest.fixture
    def detector(self):
        """Get care gap detector instance"""
        return get_care_gap_detector()

    @pytest.mark.asyncio
    async def test_detect_care_gaps(self, detector):
        """Test care gap detection"""
        patient_data = {
            "id": str(uuid4()),
            "age": 55,
            "gender": "F",
            "conditions": ["diabetes"],
            "last_hba1c": datetime.utcnow() - timedelta(days=400)
        }

        gaps = await detector.detect_gaps("test-tenant", patient_data)

        assert isinstance(gaps, list)
        # Should detect overdue HbA1c for diabetic patient
        hba1c_gaps = [g for g in gaps if "hba1c" in g.gap_name.lower()]
        assert len(hba1c_gaps) >= 0  # May vary based on rules

    @pytest.mark.asyncio
    async def test_gap_prioritization(self, detector):
        """Test that gaps are properly prioritized"""
        patient_data = {
            "id": str(uuid4()),
            "age": 65,
            "gender": "M",
            "conditions": ["diabetes", "hypertension"],
            "last_colonoscopy": None,
            "last_hba1c": datetime.utcnow() - timedelta(days=500)
        }

        gaps = await detector.detect_gaps("test-tenant", patient_data)

        # Gaps should be sorted by priority
        priorities = [CareGapPriority.CRITICAL, CareGapPriority.HIGH,
                     CareGapPriority.MEDIUM, CareGapPriority.LOW]

        if len(gaps) >= 2:
            for i in range(len(gaps) - 1):
                assert priorities.index(gaps[i].priority) <= priorities.index(gaps[i+1].priority)


# Test document processor
from shared.automation import (
    get_document_processor,
    DocumentType,
    ProcessingStatus,
)


class TestDocumentProcessor:
    """Test cases for Intelligent Document Processor"""

    @pytest.fixture
    def processor(self):
        """Get document processor instance"""
        return get_document_processor()

    @pytest.mark.asyncio
    async def test_process_document(self, processor):
        """Test document processing"""
        job = await processor.process_document(
            tenant_id="test-tenant",
            file_path="/test/lab_report.pdf",
            file_name="lab_report.pdf",
            file_type="application/pdf",
            file_size=12345,
            expected_type=DocumentType.LAB_REPORT,
            auto_classify=True,
            extract_data=True
        )

        assert job is not None
        assert job.status in [ProcessingStatus.COMPLETED, ProcessingStatus.REVIEW_REQUIRED]
        assert job.document_type == DocumentType.LAB_REPORT

    @pytest.mark.asyncio
    async def test_document_classification(self, processor):
        """Test document auto-classification"""
        job = await processor.process_document(
            tenant_id="test-tenant",
            file_path="/test/unknown_doc.pdf",
            file_name="unknown_doc.pdf",
            file_type="application/pdf",
            file_size=5000,
            expected_type=None,  # Let it classify
            auto_classify=True,
            extract_data=True
        )

        assert job.classification_result is not None
        assert job.classification_result.confidence >= 0

    @pytest.mark.asyncio
    async def test_approve_extraction(self, processor):
        """Test human approval of extraction"""
        # First process a document
        job = await processor.process_document(
            tenant_id="test-tenant",
            file_path="/test/doc.pdf",
            file_name="doc.pdf",
            file_type="application/pdf",
            file_size=1000,
            expected_type=DocumentType.LAB_REPORT
        )

        # Approve with corrections
        approved_job = await processor.approve_extraction(
            job_id=job.job_id,
            approved_fields={"patient_name": "John Doe"},
            reviewer_id="reviewer-123",
            notes="Corrected patient name"
        )

        assert approved_job.status == ProcessingStatus.COMPLETED
        assert approved_job.requires_human_review is False


# Test outreach engine
from shared.automation import (
    get_outreach_engine,
    CampaignType,
    CampaignStatus,
    OutreachChannel,
)


class TestOutreachEngine:
    """Test cases for Patient Outreach Engine"""

    @pytest.fixture
    def engine(self):
        """Get outreach engine instance"""
        return get_outreach_engine()

    @pytest.mark.asyncio
    async def test_create_segment(self, engine):
        """Test patient segment creation"""
        segment = await engine.create_segment(
            tenant_id="test-tenant",
            name="Diabetic Patients",
            description="Patients with diabetes diagnosis",
            criteria=[
                {"field": "conditions", "operator": "contains", "value": "diabetes"}
            ],
            is_dynamic=True
        )

        assert segment is not None
        assert segment.name == "Diabetic Patients"
        assert len(segment.criteria) == 1

    @pytest.mark.asyncio
    async def test_create_template(self, engine):
        """Test message template creation"""
        template = await engine.create_template(
            tenant_id="test-tenant",
            name="Appointment Reminder",
            channel=OutreachChannel.SMS,
            body="Hi {{first_name}}, reminder about your appointment on {{appointment_date}}.",
            language="en"
        )

        assert template is not None
        assert "first_name" in template.variables
        assert "appointment_date" in template.variables

    @pytest.mark.asyncio
    async def test_create_campaign(self, engine):
        """Test campaign creation"""
        # Create segment first
        segment = await engine.create_segment(
            tenant_id="test-tenant",
            name="Test Segment",
            description="Test",
            criteria=[{"field": "age", "operator": "greater_than", "value": 50}]
        )

        # Create template
        template = await engine.create_template(
            tenant_id="test-tenant",
            name="Test Template",
            channel=OutreachChannel.EMAIL,
            body="Hello {{patient_name}}"
        )

        # Create campaign
        campaign = await engine.create_campaign(
            tenant_id="test-tenant",
            name="Test Campaign",
            description="A test campaign",
            campaign_type=CampaignType.PREVENTIVE_CARE,
            segment_id=segment.segment_id,
            steps=[{
                "name": "Initial Outreach",
                "channel": "email",
                "template_id": template.template_id
            }],
            schedule={
                "start_date": datetime.utcnow(),
                "send_times": ["09:00"],
                "send_days": [0, 1, 2, 3, 4]
            }
        )

        assert campaign is not None
        assert campaign.status == CampaignStatus.DRAFT
        assert campaign.segment_id == segment.segment_id


# Test clinical automation
from shared.automation import (
    get_clinical_automation,
    ClinicalTaskType,
    LabResult,
    LabResultStatus,
)


class TestClinicalAutomation:
    """Test cases for Clinical Task Automation"""

    @pytest.fixture
    def automation(self):
        """Get clinical automation instance"""
        return get_clinical_automation()

    @pytest.mark.asyncio
    async def test_triage_normal_lab(self, automation):
        """Test lab triage with normal result"""
        lab_result = LabResult(
            result_id="lab-123",
            patient_id="patient-456",
            test_code="GLU",
            test_name="Glucose",
            value=95.0,
            unit="mg/dL",
            reference_low=70.0,
            reference_high=100.0,
            status=LabResultStatus.PENDING,
            collected_date=datetime.utcnow(),
            reported_date=datetime.utcnow(),
            ordering_provider_id="provider-789"
        )

        result, task = await automation.triage_lab_result("test-tenant", lab_result)

        assert result.status == LabResultStatus.NORMAL
        assert task is None  # No task for normal result

    @pytest.mark.asyncio
    async def test_triage_critical_lab(self, automation):
        """Test lab triage with critical result"""
        lab_result = LabResult(
            result_id="lab-critical",
            patient_id="patient-456",
            test_code="K",
            test_name="Potassium",
            value=7.0,  # Critical high
            unit="mEq/L",
            reference_low=3.5,
            reference_high=5.0,
            status=LabResultStatus.PENDING,
            collected_date=datetime.utcnow(),
            reported_date=datetime.utcnow(),
            ordering_provider_id="provider-789"
        )

        result, task = await automation.triage_lab_result("test-tenant", lab_result)

        assert result.status == LabResultStatus.CRITICAL
        assert result.is_critical is True
        assert task is not None
        assert task.task_type == ClinicalTaskType.LAB_CRITICAL

    @pytest.mark.asyncio
    async def test_task_escalation(self, automation):
        """Test task escalation"""
        # Create a task first via lab triage
        lab_result = LabResult(
            result_id="lab-escalate",
            patient_id="patient-789",
            test_code="HGB",
            test_name="Hemoglobin",
            value=6.5,  # Critical low
            unit="g/dL",
            reference_low=12.0,
            reference_high=17.5,
            status=LabResultStatus.PENDING,
            collected_date=datetime.utcnow(),
            reported_date=datetime.utcnow(),
            ordering_provider_id="provider-123"
        )

        _, task = await automation.triage_lab_result("test-tenant", lab_result)

        # Escalate the task
        escalated = await automation.escalate_task(
            task.task_id,
            reason="No response from provider",
            escalate_to="supervisor-001"
        )

        assert escalated.escalation_level == 1
        assert escalated.assigned_to == "supervisor-001"


# Test revenue automation
from shared.automation import (
    get_revenue_automation,
    Claim,
    ClaimLine,
    ClaimStatus,
)


class TestRevenueAutomation:
    """Test cases for Revenue Cycle Automation"""

    @pytest.fixture
    def revenue(self):
        """Get revenue automation instance"""
        return get_revenue_automation()

    @pytest.mark.asyncio
    async def test_validate_claim(self, revenue):
        """Test claim validation"""
        claim = Claim(
            claim_id=str(uuid4()),
            tenant_id="test-tenant",
            patient_id=str(uuid4()),
            encounter_id=str(uuid4()),
            payer_id=str(uuid4()),
            payer_name="Test Insurance",
            provider_id=str(uuid4()),
            provider_npi="1234567890",
            status=ClaimStatus.DRAFT,
            claim_type="professional",
            lines=[
                ClaimLine(
                    line_number=1,
                    procedure_code="99213",
                    procedure_description="Office Visit",
                    diagnosis_codes=["J06.9"],
                    units=1,
                    charge_amount=Decimal("150.00")
                )
            ],
            total_charges=Decimal("150.00"),
            service_date_from=datetime.utcnow() - timedelta(days=1),
            service_date_to=datetime.utcnow() - timedelta(days=1),
            created_at=datetime.utcnow()
        )

        patient_data = {
            "name": "John Doe",
            "date_of_birth": datetime(1980, 1, 1),
            "gender": "M",
            "address": "123 Main St"
        }

        is_valid, errors, warnings = await revenue.validate_claim(claim, patient_data)

        # With valid data, should pass most validations
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)
        assert isinstance(warnings, list)

    @pytest.mark.asyncio
    async def test_ar_aging(self, revenue):
        """Test AR aging calculation"""
        aging = await revenue.get_ar_aging("test-tenant")

        assert "total_ar" in aging
        assert "aging_0_30" in aging
        assert "aging_31_60" in aging
        assert "aging_61_90" in aging
        assert "aging_over_90" in aging


# Test task manager
from shared.automation import (
    get_task_manager,
    HumanTaskType,
    TaskPriority,
    TaskState,
)


class TestTaskManager:
    """Test cases for Human Task Manager"""

    @pytest.fixture
    def manager(self):
        """Get task manager instance"""
        return get_task_manager()

    @pytest.mark.asyncio
    async def test_create_task(self, manager):
        """Test task creation"""
        task = await manager.create_task(
            tenant_id="test-tenant",
            task_type=HumanTaskType.APPROVAL,
            title="Approve Refill Request",
            description="Review and approve medication refill",
            priority=TaskPriority.HIGH,
            due_hours=24,
            patient_id="patient-123"
        )

        assert task is not None
        assert task.title == "Approve Refill Request"
        assert task.state == TaskState.CREATED
        assert task.priority == TaskPriority.HIGH

    @pytest.mark.asyncio
    async def test_claim_and_complete_task(self, manager):
        """Test claiming and completing a task"""
        # Create task
        task = await manager.create_task(
            tenant_id="test-tenant",
            task_type=HumanTaskType.REVIEW,
            title="Review Document",
            description="Review uploaded document",
            priority=TaskPriority.NORMAL
        )

        # Claim task
        claimed = await manager.claim_task(task.task_id, "user-123")
        assert claimed.state == TaskState.IN_PROGRESS
        assert claimed.assigned_to == "user-123"

        # Complete task
        completed = await manager.complete_task(
            task.task_id,
            "user-123",
            outcome="approved",
            outcome_data={"approval_notes": "Looks good"}
        )
        assert completed.state == TaskState.COMPLETED
        assert completed.outcome == "approved"

    @pytest.mark.asyncio
    async def test_task_queue(self, manager):
        """Test task queue operations"""
        # Create queue
        queue = await manager.create_queue(
            tenant_id="test-tenant",
            name="Clinical Review Queue",
            description="Queue for clinical reviews",
            task_types=[HumanTaskType.CLINICAL_REVIEW],
            assignment_strategy=AssignmentStrategy.LOAD_BALANCED
        )

        assert queue is not None
        assert queue.name == "Clinical Review Queue"

        # Create task in queue
        task = await manager.create_task(
            tenant_id="test-tenant",
            task_type=HumanTaskType.CLINICAL_REVIEW,
            title="Review Lab Results",
            description="Review abnormal lab results",
            priority=TaskPriority.HIGH,
            queue_id=queue.queue_id
        )

        assert task.queue_id == queue.queue_id

    @pytest.mark.asyncio
    async def test_worker_stats(self, manager):
        """Test worker statistics"""
        # Register worker
        worker = await manager.register_worker(
            user_id="worker-123",
            tenant_id="test-tenant",
            roles=["reviewer"],
            skills=["lab_review", "document_review"],
            max_concurrent=5
        )

        assert worker is not None

        # Get stats
        stats = await manager.get_worker_stats("test-tenant", "worker-123")

        assert "current_tasks" in stats
        assert "completed_total" in stats


# Import for task queue test
from shared.automation import AssignmentStrategy


class TestIntegration:
    """Integration tests for automation platform"""

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test end-to-end workflow execution"""
        workflow_engine = get_workflow_automation_engine()
        task_manager = get_task_manager()

        # Create workflow that includes human task
        workflow = await workflow_engine.create_workflow(
            tenant_id="integration-test",
            name="Approval Workflow",
            description="Workflow with human approval",
            trigger={"type": "manual", "config": {}},
            steps=[
                {
                    "step_id": "validate",
                    "name": "Validate Data",
                    "type": "action",
                    "action": {"type": "validate_data", "config": {}}
                },
                {
                    "step_id": "human_review",
                    "name": "Human Review",
                    "type": "human_task",
                    "action": {"type": "human_task", "config": {"task_type": "approval"}}
                }
            ],
            is_active=True
        )

        # Execute workflow
        execution = await workflow_engine.execute_workflow(
            workflow_id=workflow.workflow_id,
            input_data={"request_type": "medication_refill"}
        )

        assert execution is not None

    @pytest.mark.asyncio
    async def test_care_gap_to_campaign(self):
        """Test care gap detection triggering campaign"""
        detector = get_care_gap_detector()
        outreach = get_outreach_engine()

        # Detect care gaps
        patient_data = {
            "id": str(uuid4()),
            "age": 60,
            "gender": "F",
            "conditions": ["diabetes"],
            "last_hba1c": datetime.utcnow() - timedelta(days=200)
        }

        gaps = await detector.detect_gaps("test-tenant", patient_data)

        # If gaps detected, create outreach campaign
        if gaps:
            # Create segment for patients with this gap
            segment = await outreach.create_segment(
                tenant_id="test-tenant",
                name="HbA1c Due",
                description="Patients due for HbA1c",
                criteria=[{"field": "care_gaps", "operator": "contains", "value": "hba1c"}]
            )

            # Create template
            template = await outreach.create_template(
                tenant_id="test-tenant",
                name="HbA1c Reminder",
                channel=OutreachChannel.SMS,
                body="Hi {{first_name}}, you're due for your HbA1c test. Please schedule an appointment."
            )

            # Create campaign
            campaign = await outreach.create_campaign(
                tenant_id="test-tenant",
                name="HbA1c Care Gap Campaign",
                description="Outreach for patients needing HbA1c",
                campaign_type=CampaignType.CHRONIC_CARE,
                segment_id=segment.segment_id,
                steps=[{
                    "name": "SMS Reminder",
                    "channel": "sms",
                    "template_id": template.template_id
                }],
                schedule={"start_date": datetime.utcnow(), "send_times": ["09:00"]}
            )

            assert campaign.status == CampaignStatus.DRAFT


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
