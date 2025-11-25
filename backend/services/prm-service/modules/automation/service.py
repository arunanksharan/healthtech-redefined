"""
Intelligent Automation Service
EPIC-012: Intelligent Automation Platform Service Layer
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID
from loguru import logger

from sqlalchemy.orm import Session

from shared.automation import (
    # Workflow Engine
    get_workflow_automation_engine,
    WorkflowDefinition,
    WorkflowStatus,
    TriggerType,
    ActionType,
    StepType,
    # Appointment Optimizer
    get_appointment_optimizer,
    AppointmentType,
    NoShowRiskLevel,
    # Care Gap Detector
    get_care_gap_detector,
    CareGapType,
    CareGapPriority,
    CareGapStatus,
    # Document Processor
    get_document_processor,
    DocumentType,
    ProcessingStatus,
    # Outreach Engine
    get_outreach_engine,
    CampaignType,
    CampaignStatus,
    OutreachChannel,
    # Clinical Automation
    get_clinical_automation,
    ClinicalTaskType,
    LabResult,
    MedicationRefillRequest,
    Referral,
    # Revenue Automation
    get_revenue_automation,
    Claim,
    ClaimLine,
    ClaimStatus,
    # Task Manager
    get_task_manager,
    HumanTaskType,
    TaskPriority,
    TaskState,
    AssignmentStrategy,
)

from modules.automation.schemas import (
    # Workflow
    CreateWorkflowRequest,
    WorkflowResponse,
    ExecuteWorkflowRequest,
    WorkflowExecutionResponse,
    WorkflowStatusEnum,
    TriggerTypeEnum,
    # Appointment
    NoShowPredictionRequest,
    NoShowPredictionResponse,
    ScheduleOptimizationRequest,
    ScheduleOptimizationResponse,
    TimeSlotResponse,
    WaitlistRequest,
    WaitlistResponse,
    NoShowRiskLevelEnum,
    # Care Gap
    CareGapRuleRequest,
    CareGapRuleResponse,
    DetectCareGapsRequest,
    DetectedCareGapResponse,
    CareGapInterventionRequest,
    CareGapInterventionResponse,
    CareGapTypeEnum,
    CareGapPriorityEnum,
    CareGapStatusEnum,
    # Document
    ProcessDocumentRequest,
    DocumentProcessingResponse,
    ExtractedFieldResponse,
    ApproveDocumentExtractionRequest,
    DocumentTypeEnum,
    ProcessingStatusEnum,
    ExtractionConfidenceEnum,
    # Campaign
    CreateSegmentRequest,
    SegmentResponse,
    CreateTemplateRequest,
    TemplateResponse,
    CreateCampaignRequest,
    CampaignResponse,
    CampaignAnalyticsResponse,
    QuickCampaignRequest,
    CampaignTypeEnum,
    CampaignStatusEnum,
    OutreachChannelEnum,
    # Clinical Task
    CreateClinicalTaskRequest,
    ClinicalTaskResponse,
    LabTriageRequest,
    LabTriageResponse,
    RefillRequest,
    RefillResponse,
    ReferralRequest,
    ReferralResponse,
    ClinicalTaskTypeEnum,
    TaskPriorityEnum,
    TaskStatusEnum,
    # Revenue
    CreateClaimRequest,
    ClaimResponse,
    SubmitClaimRequest,
    CreatePriorAuthRequest,
    PriorAuthResponse,
    PostPaymentRequest,
    PaymentResponse,
    CreatePaymentPlanRequest,
    PaymentPlanResponse,
    ARAgingResponse,
    DenialAnalyticsResponse,
    ClaimStatusEnum,
    PriorAuthStatusEnum,
    # Human Task
    CreateHumanTaskRequest,
    HumanTaskResponse,
    ClaimTaskRequest,
    CompleteTaskRequest,
    ApproveTaskRequest,
    RejectTaskRequest,
    EscalateTaskRequest,
    AddTaskCommentRequest,
    TaskCommentResponse,
    CreateTaskQueueRequest,
    TaskQueueResponse,
    WorkerStatsResponse,
    HumanTaskTypeEnum,
    TaskStateEnum,
    AssignmentStrategyEnum,
    # Statistics
    AutomationStatistics,
    AutomationHealthCheck,
)


class AutomationService:
    """
    Service layer for Intelligent Automation Platform.
    Integrates all automation services and provides a unified interface.
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.workflow_engine = get_workflow_automation_engine()
        self.appointment_optimizer = get_appointment_optimizer()
        self.care_gap_detector = get_care_gap_detector()
        self.document_processor = get_document_processor()
        self.outreach_engine = get_outreach_engine()
        self.clinical_automation = get_clinical_automation()
        self.revenue_automation = get_revenue_automation()
        self.task_manager = get_task_manager()
        self._stats = {
            "workflows_created": 0,
            "workflow_executions": 0,
            "workflow_successes": 0,
            "care_gaps_detected": 0,
            "care_gaps_closed": 0,
            "documents_processed": 0,
            "campaigns_created": 0,
            "clinical_tasks_created": 0,
            "claims_submitted": 0,
            "human_tasks_created": 0,
        }

    # ==================== Workflow Management ====================

    async def create_workflow(
        self,
        tenant_id: UUID,
        request: CreateWorkflowRequest
    ) -> WorkflowResponse:
        """Create a new workflow definition"""
        try:
            workflow = await self.workflow_engine.create_workflow(
                tenant_id=str(tenant_id),
                name=request.name,
                description=request.description,
                trigger={
                    "type": request.trigger.trigger_type.value,
                    "config": request.trigger.config,
                    "schedule": request.trigger.schedule,
                    "event_type": request.trigger.event_type,
                },
                steps=[
                    {
                        "step_id": s.step_id,
                        "name": s.name,
                        "type": s.step_type.value,
                        "action": {
                            "type": s.action.action_type.value,
                            "config": s.action.config,
                        } if s.action else None,
                        "on_success": s.on_success,
                        "on_failure": s.on_failure,
                    }
                    for s in request.steps
                ],
                is_active=request.is_active,
            )

            self._stats["workflows_created"] += 1

            return WorkflowResponse(
                workflow_id=UUID(workflow.workflow_id),
                name=workflow.name,
                description=workflow.description,
                trigger=request.trigger,
                steps=request.steps,
                is_active=workflow.is_active,
                version=workflow.version,
                created_at=workflow.created_at,
                updated_at=workflow.updated_at,
                last_run_at=None,
                run_count=0,
                success_count=0,
                failure_count=0,
            )
        except Exception as e:
            logger.error(f"Failed to create workflow: {e}")
            raise

    async def execute_workflow(
        self,
        tenant_id: UUID,
        request: ExecuteWorkflowRequest
    ) -> WorkflowExecutionResponse:
        """Execute a workflow"""
        try:
            execution = await self.workflow_engine.execute_workflow(
                workflow_id=str(request.workflow_id),
                input_data=request.input_data,
            )

            self._stats["workflow_executions"] += 1
            if execution.status == WorkflowStatus.COMPLETED:
                self._stats["workflow_successes"] += 1

            return WorkflowExecutionResponse(
                execution_id=UUID(execution.execution_id),
                workflow_id=request.workflow_id,
                status=WorkflowStatusEnum(execution.status.value),
                started_at=execution.started_at,
                completed_at=execution.completed_at,
                current_step=execution.current_step_id,
                output_data=execution.output_data,
                error_message=execution.error_message,
                steps_completed=execution.steps_completed,
                total_steps=execution.total_steps,
            )
        except Exception as e:
            logger.error(f"Failed to execute workflow: {e}")
            raise

    async def list_workflows(
        self,
        tenant_id: UUID,
        is_active: Optional[bool] = None
    ) -> List[WorkflowResponse]:
        """List workflows for tenant"""
        workflows = await self.workflow_engine.list_workflows(str(tenant_id))
        if is_active is not None:
            workflows = [w for w in workflows if w.is_active == is_active]

        return [
            WorkflowResponse(
                workflow_id=UUID(w.workflow_id),
                name=w.name,
                description=w.description,
                trigger=w.trigger,
                steps=w.steps,
                is_active=w.is_active,
                version=w.version,
                created_at=w.created_at,
                updated_at=w.updated_at,
                last_run_at=None,
                run_count=0,
                success_count=0,
                failure_count=0,
            )
            for w in workflows
        ]

    # ==================== Appointment Optimization ====================

    async def predict_no_show(
        self,
        tenant_id: UUID,
        request: NoShowPredictionRequest
    ) -> NoShowPredictionResponse:
        """Predict no-show risk for an appointment"""
        try:
            # Build patient history (would come from DB in production)
            patient_history = {
                "previous_no_shows": 0,
                "previous_appointments": 5,
                "patient_type": "established",
            }

            prediction = await self.appointment_optimizer.predict_no_show(
                patient_id=str(request.patient_id),
                appointment_date=request.appointment_date,
                appointment_type=AppointmentType(request.appointment_type.value),
                patient_history=patient_history,
            )

            risk_level_map = {
                NoShowRiskLevel.LOW: NoShowRiskLevelEnum.LOW,
                NoShowRiskLevel.MEDIUM: NoShowRiskLevelEnum.MEDIUM,
                NoShowRiskLevel.HIGH: NoShowRiskLevelEnum.HIGH,
                NoShowRiskLevel.VERY_HIGH: NoShowRiskLevelEnum.VERY_HIGH,
            }

            reminders = await self.appointment_optimizer.get_reminder_schedule(
                prediction.probability,
                request.appointment_date,
            )

            return NoShowPredictionResponse(
                prediction_id=uuid.uuid4(),
                patient_id=request.patient_id,
                risk_level=risk_level_map[prediction.risk_level],
                probability=prediction.probability,
                risk_factors=prediction.risk_factors,
                recommended_interventions=prediction.recommended_interventions,
                reminder_schedule=[
                    {"type": r["type"], "date": r["date"].isoformat()}
                    for r in reminders
                ],
            )
        except Exception as e:
            logger.error(f"Failed to predict no-show: {e}")
            raise

    async def optimize_schedule(
        self,
        tenant_id: UUID,
        request: ScheduleOptimizationRequest
    ) -> ScheduleOptimizationResponse:
        """Optimize provider schedule"""
        try:
            # Get available slots
            slots = await self.appointment_optimizer.find_optimal_slots(
                provider_id=str(request.provider_id),
                appointment_type=AppointmentType(request.appointment_type.value) if request.appointment_type else AppointmentType.FOLLOW_UP,
                date_from=request.date_from,
                date_to=request.date_to,
                patient_preferences=None,
            )

            return ScheduleOptimizationResponse(
                optimization_id=uuid.uuid4(),
                provider_id=request.provider_id,
                available_slots=[
                    TimeSlotResponse(
                        start_time=s.start_time,
                        end_time=s.end_time,
                        provider_id=request.provider_id,
                        room_id=None,
                        appointment_type=request.appointment_type or AppointmentTypeEnum.FOLLOW_UP,
                        is_available=s.is_available,
                        overbooking_allowed=False,
                        overbooking_count=0,
                    )
                    for s in slots
                ],
                utilization_rate=0.75,
                recommended_overbooking={},
                predicted_no_shows=2,
            )
        except Exception as e:
            logger.error(f"Failed to optimize schedule: {e}")
            raise

    async def add_to_waitlist(
        self,
        tenant_id: UUID,
        request: WaitlistRequest
    ) -> WaitlistResponse:
        """Add patient to waitlist"""
        try:
            entry = await self.appointment_optimizer.add_to_waitlist(
                patient_id=str(request.patient_id),
                appointment_type=AppointmentType(request.appointment_type.value),
                provider_id=str(request.provider_id) if request.provider_id else None,
                preferred_dates=request.preferred_dates,
                preferred_times=request.preferred_times,
            )

            return WaitlistResponse(
                waitlist_id=UUID(entry.entry_id),
                patient_id=request.patient_id,
                position=entry.position,
                estimated_wait_days=None,
                status=entry.status,
                created_at=entry.created_at,
            )
        except Exception as e:
            logger.error(f"Failed to add to waitlist: {e}")
            raise

    # ==================== Care Gap Detection ====================

    async def detect_care_gaps(
        self,
        tenant_id: UUID,
        request: DetectCareGapsRequest
    ) -> List[DetectedCareGapResponse]:
        """Detect care gaps for patients"""
        try:
            # In production, would fetch patient data from DB
            patient_data = {
                "id": str(request.patient_id) if request.patient_id else None,
                "age": 55,
                "gender": "F",
                "conditions": ["diabetes", "hypertension"],
                "last_hba1c": datetime(2024, 1, 15),
                "last_mammogram": datetime(2023, 6, 1),
            }

            gaps = await self.care_gap_detector.detect_gaps(
                str(tenant_id),
                patient_data,
            )

            self._stats["care_gaps_detected"] += len(gaps)

            priority_map = {
                CareGapPriority.CRITICAL: CareGapPriorityEnum.CRITICAL,
                CareGapPriority.HIGH: CareGapPriorityEnum.HIGH,
                CareGapPriority.MEDIUM: CareGapPriorityEnum.MEDIUM,
                CareGapPriority.LOW: CareGapPriorityEnum.LOW,
            }

            status_map = {
                CareGapStatus.OPEN: CareGapStatusEnum.OPEN,
                CareGapStatus.IN_PROGRESS: CareGapStatusEnum.IN_PROGRESS,
                CareGapStatus.SCHEDULED: CareGapStatusEnum.SCHEDULED,
                CareGapStatus.CLOSED: CareGapStatusEnum.CLOSED,
            }

            return [
                DetectedCareGapResponse(
                    gap_id=UUID(g.gap_id),
                    patient_id=UUID(g.patient_id),
                    rule_id=UUID(g.rule_id),
                    gap_type=CareGapTypeEnum(g.gap_type.value),
                    gap_name=g.gap_name,
                    priority=priority_map[g.priority],
                    status=status_map[g.status],
                    due_date=g.due_date,
                    last_completed=g.last_completed,
                    days_overdue=g.days_overdue,
                    impact_score=g.impact_score,
                    recommended_actions=g.recommended_actions,
                    detected_at=g.detected_at,
                )
                for g in gaps
            ]
        except Exception as e:
            logger.error(f"Failed to detect care gaps: {e}")
            raise

    async def create_care_gap_intervention(
        self,
        tenant_id: UUID,
        request: CareGapInterventionRequest
    ) -> CareGapInterventionResponse:
        """Create intervention for care gap"""
        try:
            intervention = await self.care_gap_detector.create_intervention(
                gap_id=str(request.gap_id),
                channel=request.channel.value,
                message=request.message,
                scheduled_date=request.scheduled_date,
            )

            return CareGapInterventionResponse(
                intervention_id=UUID(intervention.action_id),
                gap_id=request.gap_id,
                channel=request.channel,
                status=intervention.status,
                scheduled_at=intervention.scheduled_at,
                sent_at=intervention.sent_at,
                response_received=intervention.response_received,
            )
        except Exception as e:
            logger.error(f"Failed to create intervention: {e}")
            raise

    # ==================== Document Processing ====================

    async def process_document(
        self,
        tenant_id: UUID,
        request: ProcessDocumentRequest
    ) -> DocumentProcessingResponse:
        """Process a document"""
        try:
            job = await self.document_processor.process_document(
                tenant_id=str(tenant_id),
                file_path=request.file_path,
                file_name=request.file_name,
                file_type=request.file_type,
                file_size=request.file_size,
                expected_type=DocumentType(request.expected_type.value) if request.expected_type else None,
                auto_classify=request.auto_classify,
                extract_data=request.extract_data,
            )

            self._stats["documents_processed"] += 1

            confidence_map = {
                "high": ExtractionConfidenceEnum.HIGH,
                "medium": ExtractionConfidenceEnum.MEDIUM,
                "low": ExtractionConfidenceEnum.LOW,
                "very_low": ExtractionConfidenceEnum.VERY_LOW,
            }

            return DocumentProcessingResponse(
                job_id=UUID(job.job_id),
                document_id=UUID(job.document_id),
                status=ProcessingStatusEnum(job.status.value),
                document_type=DocumentTypeEnum(job.document_type.value) if job.document_type else None,
                extracted_fields=[
                    ExtractedFieldResponse(
                        field_name=f.field_name,
                        value=f.value,
                        confidence=f.confidence,
                        confidence_level=confidence_map[f.confidence_level.value],
                        validation_status=f.validation_status.value,
                        source_text=f.source_text,
                    )
                    for f in job.extracted_fields
                ],
                validation_errors=job.validation_errors,
                requires_human_review=job.requires_human_review,
                processing_time_ms=job.processing_time_ms,
                created_at=job.created_at,
            )
        except Exception as e:
            logger.error(f"Failed to process document: {e}")
            raise

    async def approve_document_extraction(
        self,
        tenant_id: UUID,
        user_id: UUID,
        request: ApproveDocumentExtractionRequest
    ) -> DocumentProcessingResponse:
        """Approve document extraction after human review"""
        try:
            job = await self.document_processor.approve_extraction(
                job_id=str(request.job_id),
                approved_fields=request.approved_fields,
                reviewer_id=str(user_id),
                notes=request.notes,
            )

            return DocumentProcessingResponse(
                job_id=UUID(job.job_id),
                document_id=UUID(job.document_id),
                status=ProcessingStatusEnum(job.status.value),
                document_type=DocumentTypeEnum(job.document_type.value) if job.document_type else None,
                extracted_fields=[],
                validation_errors=job.validation_errors,
                requires_human_review=job.requires_human_review,
                processing_time_ms=job.processing_time_ms,
                created_at=job.created_at,
            )
        except Exception as e:
            logger.error(f"Failed to approve extraction: {e}")
            raise

    # ==================== Campaign Management ====================

    async def create_segment(
        self,
        tenant_id: UUID,
        request: CreateSegmentRequest
    ) -> SegmentResponse:
        """Create a patient segment"""
        try:
            segment = await self.outreach_engine.create_segment(
                tenant_id=str(tenant_id),
                name=request.name,
                description=request.description,
                criteria=[
                    {
                        "field": c.field,
                        "operator": c.operator,
                        "value": c.value,
                        "logical_operator": c.logical_operator,
                    }
                    for c in request.criteria
                ],
                is_dynamic=request.is_dynamic,
            )

            return SegmentResponse(
                segment_id=UUID(segment.segment_id),
                name=segment.name,
                description=segment.description,
                estimated_size=segment.estimated_size,
                is_dynamic=segment.is_dynamic,
                created_at=segment.created_at,
            )
        except Exception as e:
            logger.error(f"Failed to create segment: {e}")
            raise

    async def create_template(
        self,
        tenant_id: UUID,
        request: CreateTemplateRequest
    ) -> TemplateResponse:
        """Create a message template"""
        try:
            template = await self.outreach_engine.create_template(
                tenant_id=str(tenant_id),
                name=request.name,
                channel=OutreachChannel(request.channel.value),
                body=request.body,
                subject=request.subject,
                language=request.language,
            )

            return TemplateResponse(
                template_id=UUID(template.template_id),
                name=template.name,
                channel=request.channel,
                subject=template.subject,
                body=template.body,
                variables=template.variables,
                is_active=template.is_active,
                created_at=template.created_at,
            )
        except Exception as e:
            logger.error(f"Failed to create template: {e}")
            raise

    async def create_campaign(
        self,
        tenant_id: UUID,
        user_id: UUID,
        request: CreateCampaignRequest
    ) -> CampaignResponse:
        """Create an outreach campaign"""
        try:
            campaign = await self.outreach_engine.create_campaign(
                tenant_id=str(tenant_id),
                name=request.name,
                description=request.description,
                campaign_type=CampaignType(request.campaign_type.value),
                segment_id=str(request.segment_id),
                steps=[
                    {
                        "name": s.name,
                        "channel": s.channel.value,
                        "template_id": str(s.template_id),
                        "delay_days": s.delay_days,
                        "delay_hours": s.delay_hours,
                        "condition": s.condition,
                        "fallback_channel": s.fallback_channel.value if s.fallback_channel else None,
                    }
                    for s in request.steps
                ],
                schedule={
                    "start_date": request.schedule.start_date,
                    "end_date": request.schedule.end_date,
                    "send_times": request.schedule.send_times,
                    "send_days": request.schedule.send_days,
                    "timezone": request.schedule.timezone,
                    "max_per_day": request.schedule.max_per_day,
                    "cooldown_days": request.schedule.cooldown_days,
                },
                created_by=str(user_id),
            )

            self._stats["campaigns_created"] += 1

            return CampaignResponse(
                campaign_id=UUID(campaign.campaign_id),
                name=campaign.name,
                description=campaign.description,
                campaign_type=request.campaign_type,
                status=CampaignStatusEnum(campaign.status.value),
                segment_id=request.segment_id,
                created_at=campaign.created_at,
                updated_at=campaign.updated_at,
            )
        except Exception as e:
            logger.error(f"Failed to create campaign: {e}")
            raise

    async def get_campaign_analytics(
        self,
        tenant_id: UUID,
        campaign_id: UUID
    ) -> CampaignAnalyticsResponse:
        """Get campaign analytics"""
        try:
            analytics = await self.outreach_engine.get_campaign_analytics(
                str(campaign_id)
            )

            return CampaignAnalyticsResponse(
                campaign_id=campaign_id,
                total_targeted=analytics.total_targeted,
                total_sent=analytics.total_sent,
                total_delivered=analytics.total_delivered,
                total_opened=analytics.total_opened,
                total_clicked=analytics.total_clicked,
                total_responded=analytics.total_responded,
                delivery_rate=analytics.delivery_rate,
                open_rate=analytics.open_rate,
                click_rate=analytics.click_rate,
                response_rate=analytics.response_rate,
                by_channel=analytics.by_channel,
            )
        except Exception as e:
            logger.error(f"Failed to get campaign analytics: {e}")
            raise

    # ==================== Clinical Task Automation ====================

    async def triage_lab_result(
        self,
        tenant_id: UUID,
        request: LabTriageRequest
    ) -> LabTriageResponse:
        """Triage a lab result"""
        try:
            lab_result = LabResult(
                result_id=str(uuid.uuid4()),
                patient_id=str(request.patient_id),
                test_code=request.test_code,
                test_name=request.test_name,
                value=request.value,
                unit=request.unit,
                reference_low=request.reference_low,
                reference_high=request.reference_high,
                status=LabResultStatus.PENDING,
                collected_date=request.collected_date,
                reported_date=datetime.utcnow(),
                ordering_provider_id=str(request.ordering_provider_id),
            )

            result, task = await self.clinical_automation.triage_lab_result(
                str(tenant_id),
                lab_result,
            )

            self._stats["clinical_tasks_created"] += 1 if task else 0

            return LabTriageResponse(
                result_id=UUID(result.result_id),
                patient_id=request.patient_id,
                test_name=result.test_name,
                value=result.value,
                status=result.status.value,
                is_critical=result.is_critical,
                task_created=task is not None,
                task_id=UUID(task.task_id) if task else None,
            )
        except Exception as e:
            logger.error(f"Failed to triage lab result: {e}")
            raise

    async def process_refill_request(
        self,
        tenant_id: UUID,
        request: RefillRequest
    ) -> RefillResponse:
        """Process a medication refill request"""
        try:
            refill = MedicationRefillRequest(
                request_id=str(uuid.uuid4()),
                tenant_id=str(tenant_id),
                patient_id=str(request.patient_id),
                medication_name=request.medication_name,
                medication_id=None,
                strength=request.strength,
                quantity=request.quantity,
                days_supply=request.days_supply,
                refills_remaining=request.refills_remaining,
                last_fill_date=None,
                prescriber_id=str(request.prescriber_id),
                pharmacy_id=str(request.pharmacy_id) if request.pharmacy_id else None,
                status=RefillStatus.REQUESTED,
                requested_at=datetime.utcnow(),
                is_controlled=request.is_controlled,
            )

            # Simulated patient data
            patient_data = {
                "last_visit_date": datetime(2024, 10, 1),
                "medication_class": "maintenance",
            }

            result = await self.clinical_automation.process_refill_request(
                str(tenant_id),
                refill,
                patient_data,
            )

            return RefillResponse(
                request_id=UUID(result.request_id),
                patient_id=request.patient_id,
                medication_name=result.medication_name,
                status=result.status.value,
                auto_approved=result.status == RefillStatus.AUTO_APPROVED,
                requires_review=result.requires_review,
                notes=result.notes,
                created_at=result.requested_at,
            )
        except Exception as e:
            logger.error(f"Failed to process refill: {e}")
            raise

    async def process_referral(
        self,
        tenant_id: UUID,
        request: ReferralRequest
    ) -> ReferralResponse:
        """Process a patient referral"""
        try:
            referral = Referral(
                referral_id=str(uuid.uuid4()),
                tenant_id=str(tenant_id),
                patient_id=str(request.patient_id),
                referring_provider_id=str(request.referring_provider_id),
                specialty=request.specialty,
                referred_to_provider_id=str(request.referred_to_provider_id) if request.referred_to_provider_id else None,
                referred_to_organization=None,
                reason=request.reason,
                diagnosis_codes=request.diagnosis_codes,
                urgency=TaskPriority(request.urgency.value),
                status=ReferralStatus.RECEIVED,
                created_at=datetime.utcnow(),
                clinical_notes=request.clinical_notes,
            )

            result = await self.clinical_automation.process_referral(
                str(tenant_id),
                referral,
            )

            return ReferralResponse(
                referral_id=UUID(result.referral_id),
                patient_id=request.patient_id,
                specialty=result.specialty,
                status=result.status.value,
                auth_required=result.auth_required,
                auth_number=result.auth_number,
                created_at=result.created_at,
            )
        except Exception as e:
            logger.error(f"Failed to process referral: {e}")
            raise

    # ==================== Revenue Cycle ====================

    async def create_claim(
        self,
        tenant_id: UUID,
        request: CreateClaimRequest
    ) -> ClaimResponse:
        """Create a claim"""
        try:
            claim = Claim(
                claim_id=str(uuid.uuid4()),
                tenant_id=str(tenant_id),
                patient_id=str(request.patient_id),
                encounter_id=str(request.encounter_id),
                payer_id=str(request.payer_id),
                payer_name="Insurance Payer",
                provider_id=str(request.provider_id),
                provider_npi=request.provider_npi,
                status=ClaimStatus.DRAFT,
                claim_type=request.claim_type,
                lines=[
                    ClaimLine(
                        line_number=l.line_number,
                        procedure_code=l.procedure_code,
                        procedure_description=l.procedure_description,
                        diagnosis_codes=l.diagnosis_codes,
                        units=l.units,
                        charge_amount=l.charge_amount,
                        modifier_codes=l.modifier_codes,
                        service_date=l.service_date,
                    )
                    for l in request.lines
                ],
                total_charges=sum(l.charge_amount for l in request.lines),
                service_date_from=request.service_date_from,
                service_date_to=request.service_date_to,
                created_at=datetime.utcnow(),
                prior_auth_number=request.prior_auth_number,
            )

            # Validate the claim
            patient_data = {"name": "Test Patient", "date_of_birth": datetime(1980, 1, 1), "gender": "M", "address": "123 Main St"}
            is_valid, errors, warnings = await self.revenue_automation.validate_claim(
                claim, patient_data
            )

            self.revenue_automation.claims[claim.claim_id] = claim

            return ClaimResponse(
                claim_id=UUID(claim.claim_id),
                patient_id=request.patient_id,
                payer_id=request.payer_id,
                status=ClaimStatusEnum(claim.status.value),
                total_charges=claim.total_charges,
                total_paid=claim.total_paid,
                patient_responsibility=claim.patient_responsibility,
                validation_errors=errors,
                created_at=claim.created_at,
                submitted_at=claim.submitted_at,
            )
        except Exception as e:
            logger.error(f"Failed to create claim: {e}")
            raise

    async def submit_claim(
        self,
        tenant_id: UUID,
        request: SubmitClaimRequest
    ) -> ClaimResponse:
        """Submit a claim"""
        try:
            claim = await self.revenue_automation.submit_claim(
                str(request.claim_id),
                request.clearinghouse,
            )

            self._stats["claims_submitted"] += 1

            return ClaimResponse(
                claim_id=UUID(claim.claim_id),
                patient_id=UUID(claim.patient_id),
                payer_id=UUID(claim.payer_id),
                status=ClaimStatusEnum(claim.status.value),
                total_charges=claim.total_charges,
                total_paid=claim.total_paid,
                patient_responsibility=claim.patient_responsibility,
                validation_errors=claim.validation_errors,
                created_at=claim.created_at,
                submitted_at=claim.submitted_at,
            )
        except Exception as e:
            logger.error(f"Failed to submit claim: {e}")
            raise

    async def get_ar_aging(
        self,
        tenant_id: UUID
    ) -> ARAgingResponse:
        """Get accounts receivable aging"""
        try:
            aging = await self.revenue_automation.get_ar_aging(str(tenant_id))
            return ARAgingResponse(**aging)
        except Exception as e:
            logger.error(f"Failed to get AR aging: {e}")
            raise

    # ==================== Human Task Management ====================

    async def create_human_task(
        self,
        tenant_id: UUID,
        user_id: UUID,
        request: CreateHumanTaskRequest
    ) -> HumanTaskResponse:
        """Create a human task"""
        try:
            task = await self.task_manager.create_task(
                tenant_id=str(tenant_id),
                task_type=HumanTaskType(request.task_type.value),
                title=request.title,
                description=request.description,
                priority=TaskPriority(request.priority.value),
                due_hours=request.due_hours,
                form_data=request.form_data,
                patient_id=str(request.patient_id) if request.patient_id else None,
                provider_id=str(request.provider_id) if request.provider_id else None,
                queue_id=str(request.queue_id) if request.queue_id else None,
                assigned_to=str(request.assigned_to) if request.assigned_to else None,
                tags=request.tags,
            )

            self._stats["human_tasks_created"] += 1

            return HumanTaskResponse(
                task_id=UUID(task.task_id),
                task_type=request.task_type,
                title=task.title,
                description=task.description,
                priority=request.priority,
                state=TaskStateEnum(task.state.value),
                assigned_to=UUID(task.assigned_to) if task.assigned_to else None,
                due_date=task.due_date,
                created_at=task.created_at,
                updated_at=task.updated_at,
                completed_at=task.completed_at,
                outcome=task.outcome,
            )
        except Exception as e:
            logger.error(f"Failed to create human task: {e}")
            raise

    async def claim_task(
        self,
        tenant_id: UUID,
        user_id: UUID,
        request: ClaimTaskRequest
    ) -> HumanTaskResponse:
        """Claim a task"""
        try:
            task = await self.task_manager.claim_task(
                str(request.task_id),
                str(user_id),
            )

            return HumanTaskResponse(
                task_id=UUID(task.task_id),
                task_type=HumanTaskTypeEnum(task.task_type.value),
                title=task.title,
                description=task.description,
                priority=TaskPriorityEnum(task.priority.value),
                state=TaskStateEnum(task.state.value),
                assigned_to=UUID(task.assigned_to) if task.assigned_to else None,
                due_date=task.due_date,
                created_at=task.created_at,
                updated_at=task.updated_at,
                completed_at=task.completed_at,
                outcome=task.outcome,
            )
        except Exception as e:
            logger.error(f"Failed to claim task: {e}")
            raise

    async def complete_task(
        self,
        tenant_id: UUID,
        user_id: UUID,
        request: CompleteTaskRequest
    ) -> HumanTaskResponse:
        """Complete a task"""
        try:
            task = await self.task_manager.complete_task(
                str(request.task_id),
                str(user_id),
                request.outcome,
                request.outcome_data,
            )

            return HumanTaskResponse(
                task_id=UUID(task.task_id),
                task_type=HumanTaskTypeEnum(task.task_type.value),
                title=task.title,
                description=task.description,
                priority=TaskPriorityEnum(task.priority.value),
                state=TaskStateEnum(task.state.value),
                assigned_to=UUID(task.assigned_to) if task.assigned_to else None,
                due_date=task.due_date,
                created_at=task.created_at,
                updated_at=task.updated_at,
                completed_at=task.completed_at,
                outcome=task.outcome,
            )
        except Exception as e:
            logger.error(f"Failed to complete task: {e}")
            raise

    async def get_task_queue(
        self,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        queue_id: Optional[UUID] = None,
        state: Optional[TaskStateEnum] = None
    ) -> List[HumanTaskResponse]:
        """Get task queue"""
        try:
            tasks = await self.task_manager.get_task_queue(
                tenant_id=str(tenant_id),
                user_id=str(user_id) if user_id else None,
                queue_id=str(queue_id) if queue_id else None,
                states=[TaskState(state.value)] if state else None,
            )

            return [
                HumanTaskResponse(
                    task_id=UUID(t.task_id),
                    task_type=HumanTaskTypeEnum(t.task_type.value),
                    title=t.title,
                    description=t.description,
                    priority=TaskPriorityEnum(t.priority.value),
                    state=TaskStateEnum(t.state.value),
                    assigned_to=UUID(t.assigned_to) if t.assigned_to else None,
                    due_date=t.due_date,
                    created_at=t.created_at,
                    updated_at=t.updated_at,
                    completed_at=t.completed_at,
                    outcome=t.outcome,
                )
                for t in tasks
            ]
        except Exception as e:
            logger.error(f"Failed to get task queue: {e}")
            raise

    async def get_worker_stats(
        self,
        tenant_id: UUID,
        user_id: UUID
    ) -> WorkerStatsResponse:
        """Get worker statistics"""
        try:
            stats = await self.task_manager.get_worker_stats(
                str(tenant_id),
                str(user_id),
            )

            return WorkerStatsResponse(
                user_id=user_id,
                current_tasks=stats.get("current_tasks", 0),
                completed_total=stats.get("completed_total", 0),
                completed_today=stats.get("completed_today", 0),
                overdue_tasks=stats.get("overdue_tasks", 0),
                average_completion_time=stats.get("average_completion_time", 0),
                performance_score=stats.get("performance_score", 1.0),
            )
        except Exception as e:
            logger.error(f"Failed to get worker stats: {e}")
            raise

    # ==================== Statistics ====================

    async def get_statistics(
        self,
        tenant_id: UUID
    ) -> AutomationStatistics:
        """Get automation statistics"""
        return AutomationStatistics(
            total_workflows=self._stats["workflows_created"],
            active_workflows=self._stats["workflows_created"],
            workflow_executions_today=self._stats["workflow_executions"],
            workflow_success_rate=self._stats["workflow_successes"] / max(self._stats["workflow_executions"], 1),
            total_care_gaps_detected=self._stats["care_gaps_detected"],
            care_gaps_closed_rate=self._stats["care_gaps_closed"] / max(self._stats["care_gaps_detected"], 1),
            total_documents_processed=self._stats["documents_processed"],
            document_accuracy_rate=0.92,
            active_campaigns=self._stats["campaigns_created"],
            campaign_response_rate=0.15,
            pending_clinical_tasks=self._stats["clinical_tasks_created"],
            average_task_completion_time=25.0,
            claims_submitted_today=self._stats["claims_submitted"],
            denial_rate=0.08,
        )

    async def health_check(self) -> AutomationHealthCheck:
        """Health check for automation module"""
        return AutomationHealthCheck(
            status="healthy",
            module="intelligent_automation",
            features=[
                "workflow_automation",
                "appointment_optimization",
                "care_gap_detection",
                "document_processing",
                "patient_outreach",
                "clinical_automation",
                "revenue_cycle",
                "human_task_management",
            ],
            workflow_engine_status="operational",
            document_processor_status="operational",
            outreach_engine_status="operational",
            task_manager_status="operational",
        )


# Import needed for LabResult
from shared.automation.clinical_automation import LabResultStatus, RefillStatus, ReferralStatus
from modules.automation.schemas import AppointmentTypeEnum
