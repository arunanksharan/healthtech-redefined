"""
Event type definitions and schemas
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Enumeration of all system events"""

    # Patient Events
    PATIENT_CREATED = "Patient.Created"
    PATIENT_UPDATED = "Patient.Updated"
    PATIENT_MERGED = "Patient.Merged"
    PATIENT_DECEASED = "Patient.Deceased"

    # Practitioner Events
    PRACTITIONER_CREATED = "Practitioner.Created"
    PRACTITIONER_UPDATED = "Practitioner.Updated"

    # Consent Events
    CONSENT_CREATED = "Consent.Created"
    CONSENT_UPDATED = "Consent.Updated"
    CONSENT_WITHDRAWN = "Consent.Withdrawn"

    # Appointment Events (Phase 2)
    APPOINTMENT_CREATED = "Appointment.Created"
    APPOINTMENT_UPDATED = "Appointment.Updated"
    APPOINTMENT_CANCELLED = "Appointment.Cancelled"
    APPOINTMENT_CHECKED_IN = "Appointment.CheckedIn"
    APPOINTMENT_NO_SHOW = "Appointment.NoShow"
    APPOINTMENT_COMPLETED = "Appointment.Completed"

    # Encounter Events
    ENCOUNTER_CREATED = "Encounter.Created"
    ENCOUNTER_UPDATED = "Encounter.Updated"
    ENCOUNTER_COMPLETED = "Encounter.Completed"
    ENCOUNTER_CANCELLED = "Encounter.Cancelled"

    # Journey Events (PRM)
    JOURNEY_CREATED = "Journey.Created"
    JOURNEY_INSTANCE_CREATED = "Journey.Instance.Created"
    JOURNEY_STAGE_ENTERED = "Journey.StageEntered"
    JOURNEY_STAGE_COMPLETED = "Journey.StageCompleted"
    JOURNEY_INSTANCE_COMPLETED = "Journey.Instance.Completed"
    JOURNEY_INSTANCE_CANCELLED = "Journey.Instance.Cancelled"
    JOURNEY_COMPLETED = "Journey.Completed"

    # Communication Events
    COMMUNICATION_SENT = "Communication.Sent"
    COMMUNICATION_DELIVERED = "Communication.Delivered"
    COMMUNICATION_FAILED = "Communication.Failed"
    COMMUNICATION_RECEIVED = "Communication.Received"

    # Ticket Events (PRM Support)
    TICKET_CREATED = "Ticket.Created"
    TICKET_UPDATED = "Ticket.Updated"
    TICKET_RESOLVED = "Ticket.Resolved"
    TICKET_CLOSED = "Ticket.Closed"

    # Ward & Bed Events (Phase 3)
    WARD_CREATED = "Ward.Created"
    WARD_UPDATED = "Ward.Updated"
    BED_CREATED = "Bed.Created"
    BED_UPDATED = "Bed.Updated"
    BED_STATUS_CHANGED = "Bed.StatusChanged"
    BED_ASSIGNED = "Bed.Assigned"
    BED_RELEASED = "Bed.Released"
    BED_ASSIGNMENT_CREATED = "BedAssignment.Created"
    BED_ASSIGNMENT_ENDED = "BedAssignment.Ended"

    # Admission Events (Phase 3)
    ADMISSION_CREATED = "Admission.Created"
    ADMISSION_UPDATED = "Admission.Updated"
    ADMISSION_DISCHARGED = "Admission.Discharged"
    ADMISSION_CANCELLED = "Admission.Cancelled"
    ADMISSION_BED_TRANSFERRED = "Admission.BedTransferred"

    # Order Events (Phase 3)
    ORDER_CREATED = "Order.Created"
    ORDER_UPDATED = "Order.Updated"
    ORDER_COMPLETED = "Order.Completed"
    ORDER_CANCELLED = "Order.Cancelled"

    # Nursing Events (Phase 3)
    VITALS_RECORDED = "Vitals.Recorded"
    NURSING_TASK_CREATED = "NursingTask.Created"
    NURSING_TASK_UPDATED = "NursingTask.Updated"
    NURSING_TASK_COMPLETED = "NursingTask.Completed"
    NURSING_OBSERVATION_RECORDED = "NursingObservation.Recorded"

    # ICU Events (Phase 3)
    ICU_ALERT_CREATED = "ICU.AlertCreated"
    ICU_ALERT_UPDATED = "ICU.AlertUpdated"
    ICU_ALERT_ACKNOWLEDGED = "ICU.AlertAcknowledged"
    EWS_CALCULATED = "EWS.Calculated"

    # Billing Events
    CHARGE_CREATED = "Charge.Created"
    INVOICE_GENERATED = "Invoice.Generated"
    PAYMENT_RECEIVED = "Payment.Received"

    # FHIR Resource Events
    FHIR_RESOURCE_CREATED = "FHIRResource.Created"
    FHIR_RESOURCE_UPDATED = "FHIRResource.Updated"
    FHIR_RESOURCE_DELETED = "FHIRResource.Deleted"

    # Episode & Outcome Events (Phase 4)
    EPISODE_CREATED = "Episode.Created"
    EPISODE_UPDATED = "Episode.Updated"
    OUTCOME_RECORDED = "Outcome.Recorded"
    PROM_COMPLETED = "PROM.Completed"
    PREM_COMPLETED = "PREM.Completed"

    # Quality Metrics Events (Phase 4)
    QUALITY_METRIC_CREATED = "QualityMetric.Created"
    QUALITY_METRIC_UPDATED = "QualityMetric.Updated"
    QUALITY_METRIC_RECALCULATED = "QualityMetric.Recalculated"
    QI_PROJECT_CREATED = "QIProject.Created"
    QI_PROJECT_UPDATED = "QIProject.Updated"
    QI_PROJECT_COMPLETED = "QIProject.Completed"

    # Risk Stratification Events (Phase 4)
    RISK_MODEL_CREATED = "RiskModel.Created"
    RISK_MODEL_VERSION_ACTIVATED = "RiskModel.VersionActivated"
    RISK_MODEL_VERSION_DEPRECATED = "RiskModel.VersionDeprecated"
    RISK_SCORE_CREATED = "RiskScore.Created"
    RISK_MODEL_PERFORMANCE_UPDATED = "RiskModel.PerformanceUpdated"

    # Voice & Collaboration Events (Phase 4)
    VOICE_SESSION_STARTED = "Voice.SessionStarted"
    VOICE_SESSION_ENDED = "Voice.SessionEnded"
    COLLAB_THREAD_CREATED = "Collab.ThreadCreated"
    COLLAB_MESSAGE_POSTED = "Collab.MessagePosted"
    NOTE_REVISION_CREATED = "Note.RevisionCreated"

    # LLM & Governance Events (Phase 4)
    LLM_SESSION_STARTED = "LLM.SessionStarted"
    LLM_SESSION_ENDED = "LLM.SessionEnded"
    LLM_TOOL_CALLED = "LLM.ToolCalled"
    POLICY_VIOLATION_DETECTED = "Policy.ViolationDetected"
    POLICY_VIOLATION_RESOLVED = "Policy.ViolationResolved"
    AGENT_ACTION_APPROVED = "Agent.ActionApproved"
    AGENT_ACTION_REJECTED = "Agent.ActionRejected"

    # Interoperability Gateway Events (Phase 5)
    EXTERNAL_SYSTEM_REGISTERED = "ExternalSystem.Registered"
    EXTERNAL_SYSTEM_UPDATED = "ExternalSystem.Updated"
    INTEROP_CHANNEL_CREATED = "InteropChannel.Created"
    INTEROP_CHANNEL_UPDATED = "InteropChannel.Updated"
    FHIR_MESSAGE_RECEIVED = "FHIR.MessageReceived"
    FHIR_MESSAGE_SENT = "FHIR.MessageSent"
    HL7_MESSAGE_RECEIVED = "HL7.MessageReceived"
    HL7_MESSAGE_SENT = "HL7.MessageSent"
    MAPPING_APPLIED = "Mapping.Applied"
    INTEROP_MESSAGE_FAILED = "Interop.MessageFailed"

    # Referral Network Events (Phase 5)
    NETWORK_ORG_REGISTERED = "NetworkOrg.Registered"
    NETWORK_ORG_UPDATED = "NetworkOrg.Updated"
    REFERRAL_CREATED = "Referral.Created"
    REFERRAL_UPDATED = "Referral.Updated"
    REFERRAL_SENT = "Referral.Sent"
    REFERRAL_ACCEPTED = "Referral.Accepted"
    REFERRAL_REJECTED = "Referral.Rejected"
    REFERRAL_COMPLETED = "Referral.Completed"
    REFERRAL_CANCELLED = "Referral.Cancelled"
    REFERRAL_DOCUMENT_ATTACHED = "Referral.DocumentAttached"

    # Remote Monitoring Events (Phase 5)
    REMOTE_DEVICE_REGISTERED = "RemoteDevice.Registered"
    REMOTE_DEVICE_UPDATED = "RemoteDevice.Updated"
    DEVICE_BOUND = "Device.Bound"
    DEVICE_UNBOUND = "Device.Unbound"
    REMOTE_MEASUREMENT_INGESTED = "RemoteMeasurement.Ingested"
    REMOTE_ALERT_TRIGGERED = "RemoteAlert.Triggered"
    REMOTE_ALERT_ACKNOWLEDGED = "RemoteAlert.Acknowledged"
    REMOTE_ALERT_RESOLVED = "RemoteAlert.Resolved"

    # App Marketplace Events (Phase 5)
    APP_REGISTERED = "App.Registered"
    APP_UPDATED = "App.Updated"
    APP_DEACTIVATED = "App.Deactivated"
    APP_KEY_CREATED = "AppKey.Created"
    APP_KEY_REVOKED = "AppKey.Revoked"
    APP_SCOPE_GRANTED = "AppScope.Granted"
    APP_SCOPE_REVOKED = "AppScope.Revoked"
    APP_API_CALL = "App.APICall"

    # Consent Orchestration Events (Phase 5)
    CONSENT_POLICY_CREATED = "ConsentPolicy.Created"
    CONSENT_POLICY_UPDATED = "ConsentPolicy.Updated"
    CONSENT_GIVEN = "Consent.Given"
    CONSENT_REVOKED = "Consent.Revoked"
    CONSENT_EXPIRED = "Consent.Expired"
    CONSENT_EVALUATED = "Consent.Evaluated"

    # De-identification Events (Phase 6)
    DEID_CONFIG_CREATED = "DeidConfig.Created"
    DEID_CONFIG_UPDATED = "DeidConfig.Updated"
    PSEUDO_SPACE_CREATED = "PseudoSpace.Created"
    DEID_JOB_CREATED = "DeidJob.Created"
    DEID_JOB_STARTED = "DeidJob.Started"
    DEID_JOB_COMPLETED = "DeidJob.Completed"
    DEID_JOB_FAILED = "DeidJob.Failed"

    # Research Registry Events (Phase 6)
    REGISTRY_CREATED = "Registry.Created"
    REGISTRY_UPDATED = "Registry.Updated"
    REGISTRY_ENROLLMENT_CREATED = "Registry.EnrollmentCreated"
    REGISTRY_ENROLLMENT_WITHDRAWN = "Registry.EnrollmentWithdrawn"
    REGISTRY_DATA_REFRESHED = "Registry.DataRefreshed"

    # Trial Management Events (Phase 6)
    TRIAL_CREATED = "Trial.Created"
    TRIAL_UPDATED = "Trial.Updated"
    TRIAL_STATUS_CHANGED = "Trial.StatusChanged"
    TRIAL_SUBJECT_SCREENED = "Trial.SubjectScreened"
    TRIAL_SUBJECT_ENROLLED = "Trial.SubjectEnrolled"
    TRIAL_SUBJECT_RANDOMIZED = "Trial.SubjectRandomized"
    TRIAL_SUBJECT_WITHDRAWN = "Trial.SubjectWithdrawn"
    TRIAL_VISIT_SCHEDULED = "Trial.VisitScheduled"
    TRIAL_VISIT_COMPLETED = "Trial.VisitCompleted"
    TRIAL_VISIT_MISSED = "Trial.VisitMissed"
    TRIAL_CRF_COMPLETED = "Trial.CRFCompleted"
    TRIAL_PROTOCOL_DEVIATION = "Trial.ProtocolDeviation"

    # CDS/Guideline Events (Phase 6)
    GUIDELINE_CREATED = "Guideline.Created"
    GUIDELINE_VERSION_ACTIVATED = "Guideline.VersionActivated"
    GUIDELINE_VERSION_DEPRECATED = "Guideline.VersionDeprecated"
    CDS_RULE_CREATED = "CDSRule.Created"
    CDS_EVALUATION_FIRED = "CDS.EvaluationFired"
    CDS_CARD_ACCEPTED = "CDS.CardAccepted"
    CDS_CARD_REJECTED = "CDS.CardRejected"

    # Synthetic Data Events (Phase 6)
    SYNTHETIC_PROFILE_CREATED = "SyntheticProfile.Created"
    SYNTHETIC_JOB_CREATED = "SyntheticJob.Created"
    SYNTHETIC_JOB_COMPLETED = "SyntheticJob.Completed"
    SYNTHETIC_JOB_FAILED = "SyntheticJob.Failed"

    # Knowledge Graph Events (Phase 6)
    KG_NODE_CREATED = "KG.NodeCreated"
    KG_EDGE_CREATED = "KG.EdgeCreated"
    PATIENT_KG_UPDATED = "PatientKG.Updated"
    KG_TRAVERSAL_EXECUTED = "KG.TraversalExecuted"

    # Imaging Order Events (Phase 7)
    IMAGING_ORDER_CREATED = "ImagingOrder.Created"
    IMAGING_ORDER_SCHEDULED = "ImagingOrder.Scheduled"
    IMAGING_ORDER_IN_PROGRESS = "ImagingOrder.InProgress"
    IMAGING_ORDER_COMPLETED = "ImagingOrder.Completed"
    IMAGING_ORDER_CANCELLED = "ImagingOrder.Cancelled"

    # PACS & Imaging Study Events (Phase 7)
    IMAGING_STUDY_AVAILABLE = "ImagingStudy.Available"
    IMAGING_STUDY_ARCHIVED = "ImagingStudy.Archived"

    # Radiology Worklist Events (Phase 7)
    RADIOLOGY_WORKLIST_ITEM_CREATED = "RadiologyWorklistItem.Created"
    RADIOLOGY_WORKLIST_ITEM_CLAIMED = "RadiologyWorklistItem.Claimed"
    RADIOLOGY_WORKLIST_ITEM_RELEASED = "RadiologyWorklistItem.Released"

    # Radiology Reporting Events (Phase 7)
    RADIOLOGY_REPORT_CREATED = "RadiologyReport.Created"
    RADIOLOGY_REPORT_UPDATED = "RadiologyReport.Updated"
    RADIOLOGY_REPORT_SIGNED = "RadiologyReport.Signed"
    RADIOLOGY_REPORT_ADDENDUM_ADDED = "RadiologyReport.AddendumAdded"
    RADIOLOGY_CRITICAL_RESULT = "RadiologyReport.CriticalResult"

    # Imaging AI Events (Phase 7)
    IMAGING_AI_TASK_CREATED = "ImagingAI.TaskCreated"
    IMAGING_AI_TASK_COMPLETED = "ImagingAI.TaskCompleted"
    IMAGING_AI_TASK_FAILED = "ImagingAI.TaskFailed"
    IMAGING_AI_OUTPUT_CREATED = "ImagingAI.OutputCreated"

    # Lab Order Events (Phase 8)
    LAB_ORDER_CREATED = "LabOrder.Created"
    LAB_ORDER_COLLECTED = "LabOrder.Collected"
    LAB_ORDER_COMPLETED = "LabOrder.Completed"
    LAB_ORDER_CANCELLED = "LabOrder.Cancelled"

    # Lab Specimen Events (Phase 8)
    LAB_SPECIMEN_COLLECTED = "LabSpecimen.Collected"
    LAB_SPECIMEN_RECEIVED = "LabSpecimen.Received"

    # Lab Result Events (Phase 8)
    LAB_RESULT_CREATED = "LabResult.Created"
    LAB_RESULT_FINALIZED = "LabResult.Finalized"
    LAB_CRITICAL_RESULT = "LabResult.CriticalResult"

    # Anatomic Pathology Events (Phase 8)
    AP_CASE_CREATED = "APCase.Created"
    AP_REPORT_CREATED = "APReport.Created"
    AP_REPORT_UPDATED = "APReport.Updated"
    AP_REPORT_SIGNED = "APReport.Signed"

    # Lab AI Events (Phase 8)
    LAB_AI_TASK_CREATED = "LabAI.TaskCreated"
    LAB_AI_TASK_COMPLETED = "LabAI.TaskCompleted"
    LAB_AI_TASK_FAILED = "LabAI.TaskFailed"
    LAB_AI_OUTPUT_CREATED = "LabAI.OutputCreated"

    # Medication Order Events (Phase 9)
    MEDICATION_ORDER_CREATED = "MedicationOrder.Created"
    MEDICATION_ORDER_UPDATED = "MedicationOrder.Updated"
    MEDICATION_ORDER_CANCELLED = "MedicationOrder.Cancelled"
    MEDICATION_ORDER_COMPLETED = "MedicationOrder.Completed"

    # Pharmacy Verification Events (Phase 9)
    PHARMACY_VERIFICATION_APPROVED = "PharmacyVerification.Approved"
    PHARMACY_VERIFICATION_REJECTED = "PharmacyVerification.Rejected"

    # Medication Dispensation Events (Phase 9)
    MEDICATION_DISPENSED = "Medication.Dispensed"

    # Medication Administration Events (Phase 9)
    MEDICATION_ADMINISTERED = "Medication.Administered"
    MEDICATION_ADMINISTRATION_SKIPPED = "Medication.AdministrationSkipped"

    # Medication Reconciliation Events (Phase 9)
    MEDICATION_RECONCILIATION_STARTED = "MedicationReconciliation.Started"
    MEDICATION_RECONCILIATION_COMPLETED = "MedicationReconciliation.Completed"

    # Inventory Events (Phase 9)
    INVENTORY_TRANSACTION_CREATED = "Inventory.TransactionCreated"
    PURCHASE_ORDER_CREATED = "PurchaseOrder.Created"
    PURCHASE_ORDER_RECEIVED = "PurchaseOrder.Received"

    # Pharmacy AI Events (Phase 9)
    PHARMACY_AI_TASK_CREATED = "PharmacyAI.TaskCreated"
    PHARMACY_AI_TASK_COMPLETED = "PharmacyAI.TaskCompleted"
    PHARMACY_AI_TASK_FAILED = "PharmacyAI.TaskFailed"
    PHARMACY_AI_OUTPUT_CREATED = "PharmacyAI.OutputCreated"

    # Surgery Request Events (Phase 10)
    SURGERY_REQUEST_CREATED = "SurgeryRequest.Created"
    SURGERY_REQUEST_SCHEDULED = "SurgeryRequest.Scheduled"
    SURGERY_REQUEST_CANCELLED = "SurgeryRequest.Cancelled"
    SURGERY_REQUEST_COMPLETED = "SurgeryRequest.Completed"

    # OR Scheduling Events (Phase 10)
    OR_CASE_SCHEDULED = "ORCase.Scheduled"
    OR_CASE_STARTED = "ORCase.Started"
    OR_CASE_COMPLETED = "ORCase.Completed"
    OR_CASE_CANCELLED = "ORCase.Cancelled"

    # Preop Assessment Events (Phase 10)
    PREOP_ASSESSMENT_CREATED = "PreopAssessment.Created"
    PREOP_ASSESSMENT_CLEARED = "PreopAssessment.Cleared"
    PREOP_OPTIMIZATION_TASK_CREATED = "PreopOptimizationTask.Created"

    # Surgical Case Events (Phase 10)
    SURGICAL_CASE_CREATED = "SurgicalCase.Created"
    SURGICAL_CASE_STARTED = "SurgicalCase.Started"
    SURGICAL_CASE_COMPLETED = "SurgicalCase.Completed"

    # Anesthesia Events (Phase 10)
    ANESTHESIA_RECORD_CREATED = "AnesthesiaRecord.Created"
    ANESTHESIA_EVENT_RECORDED = "AnesthesiaEvent.Recorded"

    # PACU Events (Phase 10)
    PACU_ADMISSION = "PACU.Admission"
    PACU_DISCHARGE = "PACU.Discharge"

    # Periop AI Events (Phase 10)
    PERIOP_AI_TASK_CREATED = "PeriopAI.TaskCreated"
    PERIOP_AI_TASK_COMPLETED = "PeriopAI.TaskCompleted"
    PERIOP_AI_TASK_FAILED = "PeriopAI.TaskFailed"
    PERIOP_AI_OUTPUT_CREATED = "PeriopAI.OutputCreated"

    # Coverage / Insurance Events (Phase 11)
    COVERAGE_CREATED = "Coverage.Created"
    COVERAGE_VERIFIED = "Coverage.Verified"
    COVERAGE_UPDATED = "Coverage.Updated"
    COVERAGE_EXPIRED = "Coverage.Expired"

    # Financial Estimate Events (Phase 11)
    FINANCIAL_ESTIMATE_CREATED = "FinancialEstimate.Created"
    FINANCIAL_ESTIMATE_FINALIZED = "FinancialEstimate.Finalized"
    FINANCIAL_ESTIMATE_EXPIRED = "FinancialEstimate.Expired"

    # Pre-Authorization Events (Phase 11)
    PREAUTH_CASE_CREATED = "PreauthCase.Created"
    PREAUTH_CASE_SUBMITTED = "PreauthCase.Submitted"
    PREAUTH_CASE_QUERIED = "PreauthCase.Queried"
    PREAUTH_CASE_APPROVED = "PreauthCase.Approved"
    PREAUTH_CASE_PARTIALLY_APPROVED = "PreauthCase.PartiallyApproved"
    PREAUTH_CASE_REJECTED = "PreauthCase.Rejected"
    PREAUTH_CASE_ENHANCEMENT_REQUESTED = "PreauthCase.EnhancementRequested"
    PREAUTH_DOCUMENT_UPLOADED = "PreauthDocument.Uploaded"
    PREAUTH_DOCUMENT_OCR_COMPLETED = "PreauthDocument.OCRCompleted"

    # Account / Charge Events (Phase 11)
    ACCOUNT_CREATED = "Account.Created"
    ACCOUNT_FINALIZED = "Account.Finalized"
    ACCOUNT_CLOSED = "Account.Closed"
    CHARGE_POSTED = "Charge.Posted"
    CHARGE_ADJUSTED = "Charge.Adjusted"
    CHARGE_PACKAGE_APPLIED = "ChargePackage.Applied"

    # Claims Events (Phase 11)
    CLAIM_CREATED = "Claim.Created"
    CLAIM_SUBMITTED = "Claim.Submitted"
    CLAIM_IN_REVIEW = "Claim.InReview"
    CLAIM_PAID = "Claim.Paid"
    CLAIM_PARTIALLY_PAID = "Claim.PartiallyPaid"
    CLAIM_DENIED = "Claim.Denied"
    CLAIM_CANCELLED = "Claim.Cancelled"

    # Remittance / Payment Events (Phase 11)
    REMITTANCE_RECEIVED = "Remittance.Received"
    REMITTANCE_POSTED = "Remittance.Posted"
    REMITTANCE_LINE_MATCHED = "RemittanceLine.Matched"

    # Denial Events (Phase 11)
    DENIAL_CREATED = "Denial.Created"
    DENIAL_APPEAL_FILED = "Denial.AppealFiled"
    DENIAL_RESOLVED = "Denial.Resolved"
    DENIAL_WRITTEN_OFF = "Denial.WrittenOff"

    # Work Queue / Control Tower Events (Phase 11)
    WORK_ITEM_CREATED = "WorkItem.Created"
    WORK_ITEM_ASSIGNED = "WorkItem.Assigned"
    WORK_ITEM_COMPLETED = "WorkItem.Completed"
    WORK_ITEM_SNOOZED = "WorkItem.Snoozed"
    WORK_ITEM_SLA_BREACH_WARNING = "WorkItem.SLABreachWarning"

    # RCM AI Events (Phase 11)
    RCM_AI_TASK_CREATED = "RCMAI.TaskCreated"
    RCM_AI_TASK_COMPLETED = "RCMAI.TaskCompleted"
    RCM_AI_TASK_FAILED = "RCMAI.TaskFailed"
    RCM_AI_OUTPUT_CREATED = "RCMAI.OutputCreated"

    # Ops Event Ingestion Events (Phase 12)
    OPS_EVENT_INGESTED = "OpsEvent.Ingested"
    OPS_EVENT_PROCESSED = "OpsEvent.Processed"
    OPS_EVENT_SOURCE_REGISTERED = "OpsEventSource.Registered"

    # Ops State Projection Events (Phase 12)
    UNIT_SNAPSHOT_UPDATED = "UnitSnapshot.Updated"
    BED_SNAPSHOT_UPDATED = "BedSnapshot.Updated"
    OR_STATUS_SNAPSHOT_UPDATED = "ORStatusSnapshot.Updated"
    ED_STATUS_SNAPSHOT_UPDATED = "EDStatusSnapshot.Updated"
    LAB_WORKLOAD_SNAPSHOT_UPDATED = "LabWorkloadSnapshot.Updated"
    IMAGING_WORKLOAD_SNAPSHOT_UPDATED = "ImagingWorkloadSnapshot.Updated"
    RCM_WORKLOAD_SNAPSHOT_UPDATED = "RCMWorkloadSnapshot.Updated"
    OPS_KPI_COMPUTED = "OpsKPI.Computed"

    # Ops Alert Events (Phase 12)
    OPS_ALERT_TRIGGERED = "OpsAlert.Triggered"
    OPS_ALERT_ACKNOWLEDGED = "OpsAlert.Acknowledged"
    OPS_ALERT_ASSIGNED = "OpsAlert.Assigned"
    OPS_ALERT_RESOLVED = "OpsAlert.Resolved"
    OPS_ALERT_DISMISSED = "OpsAlert.Dismissed"
    OPS_ALERT_ESCALATED = "OpsAlert.Escalated"

    # Ops Playbook Events (Phase 12)
    OPS_PLAYBOOK_ACTIVATED = "OpsPlaybook.Activated"
    OPS_PLAYBOOK_STEP_COMPLETED = "OpsPlaybookStep.Completed"
    OPS_PLAYBOOK_COMPLETED = "OpsPlaybook.Completed"

    # Ops AI Events (Phase 12)
    OPS_AI_TASK_CREATED = "OpsAI.TaskCreated"
    OPS_AI_TASK_COMPLETED = "OpsAI.TaskCompleted"
    OPS_AI_TASK_FAILED = "OpsAI.TaskFailed"
    OPS_AI_OUTPUT_CREATED = "OpsAI.OutputCreated"

    # System Events
    SYSTEM_ERROR = "System.Error"
    SYSTEM_WARNING = "System.Warning"


class Event(BaseModel):
    """Base event structure"""

    event_id: UUID = Field(default_factory=uuid4)
    event_type: EventType
    tenant_id: str
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    source_service: Optional[str] = None
    source_user_id: Optional[UUID] = None
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


# Domain-specific event payloads for type safety
class PatientCreatedPayload(BaseModel):
    """Payload for Patient.Created event"""

    patient_id: UUID
    identifiers: list[Dict[str, str]] = []
    name: str
    date_of_birth: Optional[str] = None


class AppointmentCreatedPayload(BaseModel):
    """Payload for Appointment.Created event"""

    appointment_id: UUID
    patient_id: UUID
    practitioner_id: UUID
    location_id: UUID
    start_time: datetime
    appointment_type: str
    specialty: Optional[str] = None


class ConsentWithdrawnPayload(BaseModel):
    """Payload for Consent.Withdrawn event"""

    consent_id: UUID
    patient_id: UUID
    reason: str
    withdrawn_at: datetime


class OrderCreatedPayload(BaseModel):
    """Payload for Order.Created event"""

    order_id: UUID
    patient_id: UUID
    encounter_id: UUID
    order_type: str  # lab, imaging, medication
    description: str
    priority: str


class VitalsRecordedPayload(BaseModel):
    """Payload for Vitals.Recorded event"""

    observation_id: UUID
    patient_id: UUID
    admission_id: Optional[UUID] = None
    vitals: Dict[str, Any]
    recorded_at: datetime


class ICUAlertCreatedPayload(BaseModel):
    """Payload for ICU.AlertCreated event"""

    alert_id: UUID
    patient_id: UUID
    admission_id: UUID
    alert_type: str
    severity: str
    message: str
    ews_score: Optional[int] = None
