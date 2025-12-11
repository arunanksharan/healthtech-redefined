"""
Intelligent Automation Platform

A comprehensive automation suite for healthcare operations including:
- Workflow automation engine
- Business rule engine
- Smart appointment optimization
- Care gap detection
- Intelligent document processing
- Patient outreach campaigns
- Clinical task automation
- Revenue cycle automation
- Human-in-the-loop task management

Part of EPIC-012: Intelligent Automation Platform
"""

from .workflow_engine import (
    WorkflowAutomationEngine,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowStep,
    Trigger,
    Action,
    Condition,
    WorkflowStatus,
    TriggerType,
    ActionType,
    StepType,
    RetryStrategy,
    get_workflow_automation_engine,
)

from .rule_engine import (
    BusinessRuleEngine,
    Rule,
    RuleCondition,
    RuleAction,
    DecisionTable,
    DecisionTree,
    ScoringRule,
    RuleType,
    RuleCategory,
    RulePriority,
    ActionStatus,
    HealthcareRules,
    get_business_rule_engine,
)

from .appointment_optimizer import (
    AppointmentOptimizer,
    NoShowPrediction,
    TimeSlot,
    ProviderSchedule,
    PatientPreferences,
    WaitlistEntry,
    AppointmentType,
    AppointmentStatus,
    NoShowRiskLevel,
    InterventionType,
    get_appointment_optimizer,
)

from .care_gap_detector import (
    CareGapDetector,
    CareGapRule,
    DetectedCareGap,
    InterventionAction,
    InterventionCampaign,
    CareGapType,
    CareGapPriority,
    CareGapStatus,
    InterventionChannel,
    get_care_gap_detector,
)

from .document_processor import (
    IntelligentDocumentProcessor,
    DocumentProcessingJob,
    OCRResult,
    ClassificationResult,
    ExtractedField,
    ExtractionTemplate,
    DocumentType,
    ProcessingStatus,
    ExtractionConfidence,
    ValidationStatus,
    get_document_processor,
)

from .outreach_engine import (
    PatientOutreachEngine,
    Campaign,
    CampaignStep,
    CampaignSchedule,
    PatientSegment,
    MessageTemplate,
    OutreachMessage,
    CampaignAnalytics,
    CampaignType,
    CampaignStatus,
    OutreachChannel,
    MessageStatus,
    OutreachPriority,
    CampaignTemplates,
    get_outreach_engine,
)

from .clinical_automation import (
    ClinicalTaskAutomation,
    ClinicalTask,
    LabResult,
    LabTriageRule,
    MedicationRefillRequest,
    RefillAutoApprovalRule,
    Referral,
    AutomationAction,
    ClinicalTaskType,
    TaskPriority as ClinicalTaskPriority,
    TaskStatus as ClinicalTaskStatus,
    LabResultStatus,
    RefillStatus,
    ReferralStatus,
    get_clinical_automation,
)

from .revenue_automation import (
    RevenueCycleAutomation,
    Claim,
    ClaimLine,
    DenialRecord,
    PriorAuthorization,
    PaymentRecord,
    PatientBalance,
    PaymentPlan,
    CollectionAction,
    ClaimStatus,
    DenialReasonCategory,
    PriorAuthStatus,
    PaymentStatus,
    CollectionStatus,
    PaymentPlanStatus,
    get_revenue_automation,
)

from .task_manager import (
    HumanTaskManager,
    HumanTask,
    TaskQueue,
    WorkerProfile,
    TaskComment,
    TaskHistory,
    TaskDefinition,
    EscalationRule,
    HumanTaskType,
    TaskPriority,
    TaskState,
    AssignmentStrategy,
    get_task_manager,
)


__all__ = [
    # Workflow Engine
    "WorkflowAutomationEngine",
    "WorkflowDefinition",
    "WorkflowExecution",
    "WorkflowStep",
    "Trigger",
    "Action",
    "Condition",
    "WorkflowStatus",
    "TriggerType",
    "ActionType",
    "StepType",
    "RetryStrategy",
    "get_workflow_automation_engine",

    # Rule Engine
    "BusinessRuleEngine",
    "Rule",
    "RuleCondition",
    "RuleAction",
    "DecisionTable",
    "DecisionTree",
    "ScoringRule",
    "RuleType",
    "RuleCategory",
    "RulePriority",
    "ActionStatus",
    "HealthcareRules",
    "get_business_rule_engine",

    # Appointment Optimizer
    "AppointmentOptimizer",
    "NoShowPrediction",
    "TimeSlot",
    "ProviderSchedule",
    "PatientPreferences",
    "WaitlistEntry",
    "AppointmentType",
    "AppointmentStatus",
    "NoShowRiskLevel",
    "InterventionType",
    "get_appointment_optimizer",

    # Care Gap Detector
    "CareGapDetector",
    "CareGapRule",
    "DetectedCareGap",
    "InterventionAction",
    "InterventionCampaign",
    "CareGapType",
    "CareGapPriority",
    "CareGapStatus",
    "InterventionChannel",
    "get_care_gap_detector",

    # Document Processor
    "IntelligentDocumentProcessor",
    "DocumentProcessingJob",
    "OCRResult",
    "ClassificationResult",
    "ExtractedField",
    "ExtractionTemplate",
    "DocumentType",
    "ProcessingStatus",
    "ExtractionConfidence",
    "ValidationStatus",
    "get_document_processor",

    # Outreach Engine
    "PatientOutreachEngine",
    "Campaign",
    "CampaignStep",
    "CampaignSchedule",
    "PatientSegment",
    "MessageTemplate",
    "OutreachMessage",
    "CampaignAnalytics",
    "CampaignType",
    "CampaignStatus",
    "OutreachChannel",
    "MessageStatus",
    "OutreachPriority",
    "CampaignTemplates",
    "get_outreach_engine",

    # Clinical Automation
    "ClinicalTaskAutomation",
    "ClinicalTask",
    "LabResult",
    "LabTriageRule",
    "MedicationRefillRequest",
    "RefillAutoApprovalRule",
    "Referral",
    "AutomationAction",
    "ClinicalTaskType",
    "ClinicalTaskPriority",
    "ClinicalTaskStatus",
    "LabResultStatus",
    "RefillStatus",
    "ReferralStatus",
    "get_clinical_automation",

    # Revenue Automation
    "RevenueCycleAutomation",
    "Claim",
    "ClaimLine",
    "DenialRecord",
    "PriorAuthorization",
    "PaymentRecord",
    "PatientBalance",
    "PaymentPlan",
    "CollectionAction",
    "ClaimStatus",
    "DenialReasonCategory",
    "PriorAuthStatus",
    "PaymentStatus",
    "CollectionStatus",
    "PaymentPlanStatus",
    "get_revenue_automation",

    # Task Manager
    "HumanTaskManager",
    "HumanTask",
    "TaskQueue",
    "WorkerProfile",
    "TaskComment",
    "TaskHistory",
    "TaskDefinition",
    "EscalationRule",
    "HumanTaskType",
    "TaskPriority",
    "TaskState",
    "AssignmentStrategy",
    "get_task_manager",
]
