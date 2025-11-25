"""
Intelligent Automation Router
EPIC-012: Intelligent Automation Platform API Endpoints
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from loguru import logger

from core.deps import get_db, get_current_user, get_current_org_id
from modules.automation.service import AutomationService
from modules.automation.schemas import (
    # Workflow
    CreateWorkflowRequest,
    WorkflowResponse,
    ExecuteWorkflowRequest,
    WorkflowExecutionResponse,
    # Appointment
    NoShowPredictionRequest,
    NoShowPredictionResponse,
    ScheduleOptimizationRequest,
    ScheduleOptimizationResponse,
    WaitlistRequest,
    WaitlistResponse,
    # Care Gap
    CareGapRuleRequest,
    CareGapRuleResponse,
    DetectCareGapsRequest,
    DetectedCareGapResponse,
    CareGapInterventionRequest,
    CareGapInterventionResponse,
    # Document
    ProcessDocumentRequest,
    DocumentProcessingResponse,
    ApproveDocumentExtractionRequest,
    # Campaign
    CreateSegmentRequest,
    SegmentResponse,
    CreateTemplateRequest,
    TemplateResponse,
    CreateCampaignRequest,
    CampaignResponse,
    CampaignAnalyticsResponse,
    QuickCampaignRequest,
    # Clinical Task
    CreateClinicalTaskRequest,
    ClinicalTaskResponse,
    LabTriageRequest,
    LabTriageResponse,
    RefillRequest,
    RefillResponse,
    ReferralRequest,
    ReferralResponse,
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
    TaskStateEnum,
    # Statistics
    AutomationStatistics,
    AutomationHealthCheck,
)

router = APIRouter(prefix="/automation", tags=["Intelligent Automation"])


def get_automation_service(db: Session = Depends(get_db)) -> AutomationService:
    """Get automation service instance"""
    return AutomationService(db)


# ==================== Workflow Management ====================

@router.post("/workflows", response_model=WorkflowResponse)
async def create_workflow(
    request: CreateWorkflowRequest,
    org_id: UUID = Depends(get_current_org_id),
    user: dict = Depends(get_current_user),
    service: AutomationService = Depends(get_automation_service),
):
    """Create a new workflow definition"""
    try:
        return await service.create_workflow(org_id, request)
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows", response_model=List[WorkflowResponse])
async def list_workflows(
    is_active: Optional[bool] = Query(None),
    org_id: UUID = Depends(get_current_org_id),
    user: dict = Depends(get_current_user),
    service: AutomationService = Depends(get_automation_service),
):
    """List workflows for organization"""
    try:
        return await service.list_workflows(org_id, is_active)
    except Exception as e:
        logger.error(f"Failed to list workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflows/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    request: ExecuteWorkflowRequest,
    org_id: UUID = Depends(get_current_org_id),
    user: dict = Depends(get_current_user),
    service: AutomationService = Depends(get_automation_service),
):
    """Execute a workflow"""
    try:
        return await service.execute_workflow(org_id, request)
    except Exception as e:
        logger.error(f"Failed to execute workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Appointment Optimization ====================

@router.post("/appointments/predict-no-show", response_model=NoShowPredictionResponse)
async def predict_no_show(
    request: NoShowPredictionRequest,
    org_id: UUID = Depends(get_current_org_id),
    user: dict = Depends(get_current_user),
    service: AutomationService = Depends(get_automation_service),
):
    """Predict no-show risk for an appointment"""
    try:
        return await service.predict_no_show(org_id, request)
    except Exception as e:
        logger.error(f"Failed to predict no-show: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/appointments/optimize-schedule", response_model=ScheduleOptimizationResponse)
async def optimize_schedule(
    request: ScheduleOptimizationRequest,
    org_id: UUID = Depends(get_current_org_id),
    user: dict = Depends(get_current_user),
    service: AutomationService = Depends(get_automation_service),
):
    """Optimize provider schedule"""
    try:
        return await service.optimize_schedule(org_id, request)
    except Exception as e:
        logger.error(f"Failed to optimize schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/appointments/waitlist", response_model=WaitlistResponse)
async def add_to_waitlist(
    request: WaitlistRequest,
    org_id: UUID = Depends(get_current_org_id),
    user: dict = Depends(get_current_user),
    service: AutomationService = Depends(get_automation_service),
):
    """Add patient to waitlist"""
    try:
        return await service.add_to_waitlist(org_id, request)
    except Exception as e:
        logger.error(f"Failed to add to waitlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Care Gap Detection ====================

@router.post("/care-gaps/detect", response_model=List[DetectedCareGapResponse])
async def detect_care_gaps(
    request: DetectCareGapsRequest,
    org_id: UUID = Depends(get_current_org_id),
    user: dict = Depends(get_current_user),
    service: AutomationService = Depends(get_automation_service),
):
    """Detect care gaps for patients"""
    try:
        return await service.detect_care_gaps(org_id, request)
    except Exception as e:
        logger.error(f"Failed to detect care gaps: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/care-gaps/interventions", response_model=CareGapInterventionResponse)
async def create_care_gap_intervention(
    request: CareGapInterventionRequest,
    org_id: UUID = Depends(get_current_org_id),
    user: dict = Depends(get_current_user),
    service: AutomationService = Depends(get_automation_service),
):
    """Create intervention for care gap"""
    try:
        return await service.create_care_gap_intervention(org_id, request)
    except Exception as e:
        logger.error(f"Failed to create intervention: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Document Processing ====================

@router.post("/documents/process", response_model=DocumentProcessingResponse)
async def process_document(
    request: ProcessDocumentRequest,
    org_id: UUID = Depends(get_current_org_id),
    user: dict = Depends(get_current_user),
    service: AutomationService = Depends(get_automation_service),
):
    """Process a document with OCR and extraction"""
    try:
        return await service.process_document(org_id, request)
    except Exception as e:
        logger.error(f"Failed to process document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/approve", response_model=DocumentProcessingResponse)
async def approve_document_extraction(
    request: ApproveDocumentExtractionRequest,
    org_id: UUID = Depends(get_current_org_id),
    user: dict = Depends(get_current_user),
    service: AutomationService = Depends(get_automation_service),
):
    """Approve document extraction after human review"""
    try:
        return await service.approve_document_extraction(org_id, UUID(user["id"]), request)
    except Exception as e:
        logger.error(f"Failed to approve extraction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Campaign Management ====================

@router.post("/campaigns/segments", response_model=SegmentResponse)
async def create_segment(
    request: CreateSegmentRequest,
    org_id: UUID = Depends(get_current_org_id),
    user: dict = Depends(get_current_user),
    service: AutomationService = Depends(get_automation_service),
):
    """Create a patient segment"""
    try:
        return await service.create_segment(org_id, request)
    except Exception as e:
        logger.error(f"Failed to create segment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/campaigns/templates", response_model=TemplateResponse)
async def create_template(
    request: CreateTemplateRequest,
    org_id: UUID = Depends(get_current_org_id),
    user: dict = Depends(get_current_user),
    service: AutomationService = Depends(get_automation_service),
):
    """Create a message template"""
    try:
        return await service.create_template(org_id, request)
    except Exception as e:
        logger.error(f"Failed to create template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/campaigns", response_model=CampaignResponse)
async def create_campaign(
    request: CreateCampaignRequest,
    org_id: UUID = Depends(get_current_org_id),
    user: dict = Depends(get_current_user),
    service: AutomationService = Depends(get_automation_service),
):
    """Create an outreach campaign"""
    try:
        return await service.create_campaign(org_id, UUID(user["id"]), request)
    except Exception as e:
        logger.error(f"Failed to create campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/campaigns/{campaign_id}/analytics", response_model=CampaignAnalyticsResponse)
async def get_campaign_analytics(
    campaign_id: UUID,
    org_id: UUID = Depends(get_current_org_id),
    user: dict = Depends(get_current_user),
    service: AutomationService = Depends(get_automation_service),
):
    """Get campaign analytics"""
    try:
        return await service.get_campaign_analytics(org_id, campaign_id)
    except Exception as e:
        logger.error(f"Failed to get campaign analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Clinical Task Automation ====================

@router.post("/clinical/lab-triage", response_model=LabTriageResponse)
async def triage_lab_result(
    request: LabTriageRequest,
    org_id: UUID = Depends(get_current_org_id),
    user: dict = Depends(get_current_user),
    service: AutomationService = Depends(get_automation_service),
):
    """Triage a lab result"""
    try:
        return await service.triage_lab_result(org_id, request)
    except Exception as e:
        logger.error(f"Failed to triage lab result: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clinical/refills", response_model=RefillResponse)
async def process_refill_request(
    request: RefillRequest,
    org_id: UUID = Depends(get_current_org_id),
    user: dict = Depends(get_current_user),
    service: AutomationService = Depends(get_automation_service),
):
    """Process a medication refill request"""
    try:
        return await service.process_refill_request(org_id, request)
    except Exception as e:
        logger.error(f"Failed to process refill: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clinical/referrals", response_model=ReferralResponse)
async def process_referral(
    request: ReferralRequest,
    org_id: UUID = Depends(get_current_org_id),
    user: dict = Depends(get_current_user),
    service: AutomationService = Depends(get_automation_service),
):
    """Process a patient referral"""
    try:
        return await service.process_referral(org_id, request)
    except Exception as e:
        logger.error(f"Failed to process referral: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Revenue Cycle ====================

@router.post("/revenue/claims", response_model=ClaimResponse)
async def create_claim(
    request: CreateClaimRequest,
    org_id: UUID = Depends(get_current_org_id),
    user: dict = Depends(get_current_user),
    service: AutomationService = Depends(get_automation_service),
):
    """Create a claim"""
    try:
        return await service.create_claim(org_id, request)
    except Exception as e:
        logger.error(f"Failed to create claim: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/revenue/claims/submit", response_model=ClaimResponse)
async def submit_claim(
    request: SubmitClaimRequest,
    org_id: UUID = Depends(get_current_org_id),
    user: dict = Depends(get_current_user),
    service: AutomationService = Depends(get_automation_service),
):
    """Submit a claim"""
    try:
        return await service.submit_claim(org_id, request)
    except Exception as e:
        logger.error(f"Failed to submit claim: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/revenue/ar-aging", response_model=ARAgingResponse)
async def get_ar_aging(
    org_id: UUID = Depends(get_current_org_id),
    user: dict = Depends(get_current_user),
    service: AutomationService = Depends(get_automation_service),
):
    """Get accounts receivable aging"""
    try:
        return await service.get_ar_aging(org_id)
    except Exception as e:
        logger.error(f"Failed to get AR aging: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Human Task Management ====================

@router.post("/tasks", response_model=HumanTaskResponse)
async def create_human_task(
    request: CreateHumanTaskRequest,
    org_id: UUID = Depends(get_current_org_id),
    user: dict = Depends(get_current_user),
    service: AutomationService = Depends(get_automation_service),
):
    """Create a human task"""
    try:
        return await service.create_human_task(org_id, UUID(user["id"]), request)
    except Exception as e:
        logger.error(f"Failed to create human task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks", response_model=List[HumanTaskResponse])
async def get_task_queue(
    queue_id: Optional[UUID] = Query(None),
    state: Optional[TaskStateEnum] = Query(None),
    my_tasks: bool = Query(False),
    org_id: UUID = Depends(get_current_org_id),
    user: dict = Depends(get_current_user),
    service: AutomationService = Depends(get_automation_service),
):
    """Get task queue"""
    try:
        user_id = UUID(user["id"]) if my_tasks else None
        return await service.get_task_queue(org_id, user_id, queue_id, state)
    except Exception as e:
        logger.error(f"Failed to get task queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/claim", response_model=HumanTaskResponse)
async def claim_task(
    request: ClaimTaskRequest,
    org_id: UUID = Depends(get_current_org_id),
    user: dict = Depends(get_current_user),
    service: AutomationService = Depends(get_automation_service),
):
    """Claim a task"""
    try:
        return await service.claim_task(org_id, UUID(user["id"]), request)
    except Exception as e:
        logger.error(f"Failed to claim task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/complete", response_model=HumanTaskResponse)
async def complete_task(
    request: CompleteTaskRequest,
    org_id: UUID = Depends(get_current_org_id),
    user: dict = Depends(get_current_user),
    service: AutomationService = Depends(get_automation_service),
):
    """Complete a task"""
    try:
        return await service.complete_task(org_id, UUID(user["id"]), request)
    except Exception as e:
        logger.error(f"Failed to complete task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/stats", response_model=WorkerStatsResponse)
async def get_worker_stats(
    org_id: UUID = Depends(get_current_org_id),
    user: dict = Depends(get_current_user),
    service: AutomationService = Depends(get_automation_service),
):
    """Get worker statistics"""
    try:
        return await service.get_worker_stats(org_id, UUID(user["id"]))
    except Exception as e:
        logger.error(f"Failed to get worker stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Statistics & Health ====================

@router.get("/statistics", response_model=AutomationStatistics)
async def get_statistics(
    org_id: UUID = Depends(get_current_org_id),
    user: dict = Depends(get_current_user),
    service: AutomationService = Depends(get_automation_service),
):
    """Get automation statistics"""
    try:
        return await service.get_statistics(org_id)
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=AutomationHealthCheck)
async def health_check(
    service: AutomationService = Depends(get_automation_service),
):
    """Health check for automation module"""
    return await service.health_check()
