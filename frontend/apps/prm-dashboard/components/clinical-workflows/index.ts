// Clinical Workflows Components - Barrel Export
// EPIC-UX-007: Clinical Workflows Interface

// Prescription Form
export {
  PrescriptionForm,
  PrescriptionWidget,
  PrescriptionFormSkeleton,
} from "./prescription-form";

// Vitals Entry
export {
  VitalsEntry,
  VitalsWidget,
  VitalsEntrySkeleton,
} from "./vitals-entry";

// Lab Order Form
export {
  LabOrderForm,
  LabOrderWidget,
  LabOrderFormSkeleton,
} from "./lab-order-form";

// SOAP Note Editor
export {
  SOAPNoteEditor,
  SOAPNoteWidget,
  SOAPNoteEditorSkeleton,
} from "./soap-note-editor";

// Referral Form
export {
  ReferralForm,
  ReferralWidget,
  ReferralFormSkeleton,
} from "./referral-form";

// Re-export types from store for convenience
export type {
  // Medications & Prescriptions
  Medication,
  DrugInteraction,
  Prescription,
  Pharmacy,
  // Lab Orders
  LabTest,
  LabOrder,
  LabFacility,
  LabResult,
  DiagnosisCode,
  // Clinical Notes
  ClinicalNote,
  SubjectiveSection,
  ObjectiveSection,
  AssessmentSection,
  PlanSection,
  // Vital Signs
  VitalSigns,
  VitalAbnormalFlag,
  VitalThresholds,
  // Referrals
  Referral,
  Specialist,
  AttachedDocument,
} from "@/lib/store/clinical-workflows-store";
