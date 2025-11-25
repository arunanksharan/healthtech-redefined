"""
Intelligent Automation Module
EPIC-012: Intelligent Automation Platform

This module provides comprehensive automation capabilities for healthcare operations:

1. Workflow Automation Engine
   - Visual workflow builder
   - Event-driven triggers
   - Conditional logic and loops
   - Human-in-the-loop steps

2. Smart Appointment Management
   - No-show prediction
   - Schedule optimization
   - Overbooking recommendations
   - Waitlist management

3. Care Gap Detection
   - Automated gap identification
   - HEDIS/NQF quality measures
   - Intervention campaigns
   - Closure tracking

4. Intelligent Document Processing
   - OCR extraction
   - Document classification
   - Data validation
   - Human review workflow

5. Patient Outreach Campaigns
   - Multi-channel communication
   - Patient segmentation
   - Personalized messaging
   - Campaign analytics

6. Clinical Task Automation
   - Lab result triage
   - Medication refill processing
   - Referral management
   - Auto-escalation

7. Revenue Cycle Automation
   - Claims processing
   - Prior authorization
   - Payment posting
   - Collection workflows

8. Human Task Management
   - Task queues
   - Skill-based routing
   - SLA monitoring
   - Performance tracking
"""

from modules.automation.router import router
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
    # Care Gap
    DetectCareGapsRequest,
    DetectedCareGapResponse,
    CareGapInterventionRequest,
    CareGapInterventionResponse,
    # Document
    ProcessDocumentRequest,
    DocumentProcessingResponse,
    # Campaign
    CreateCampaignRequest,
    CampaignResponse,
    CampaignAnalyticsResponse,
    # Clinical
    LabTriageRequest,
    LabTriageResponse,
    RefillRequest,
    RefillResponse,
    ReferralRequest,
    ReferralResponse,
    # Revenue
    CreateClaimRequest,
    ClaimResponse,
    ARAgingResponse,
    # Human Task
    CreateHumanTaskRequest,
    HumanTaskResponse,
    WorkerStatsResponse,
    # Statistics
    AutomationStatistics,
    AutomationHealthCheck,
)

__all__ = [
    "router",
    "AutomationService",
    # Workflow
    "CreateWorkflowRequest",
    "WorkflowResponse",
    "ExecuteWorkflowRequest",
    "WorkflowExecutionResponse",
    # Appointment
    "NoShowPredictionRequest",
    "NoShowPredictionResponse",
    "ScheduleOptimizationRequest",
    "ScheduleOptimizationResponse",
    # Care Gap
    "DetectCareGapsRequest",
    "DetectedCareGapResponse",
    "CareGapInterventionRequest",
    "CareGapInterventionResponse",
    # Document
    "ProcessDocumentRequest",
    "DocumentProcessingResponse",
    # Campaign
    "CreateCampaignRequest",
    "CampaignResponse",
    "CampaignAnalyticsResponse",
    # Clinical
    "LabTriageRequest",
    "LabTriageResponse",
    "RefillRequest",
    "RefillResponse",
    "ReferralRequest",
    "ReferralResponse",
    # Revenue
    "CreateClaimRequest",
    "ClaimResponse",
    "ARAgingResponse",
    # Human Task
    "CreateHumanTaskRequest",
    "HumanTaskResponse",
    "WorkerStatsResponse",
    # Statistics
    "AutomationStatistics",
    "AutomationHealthCheck",
]
