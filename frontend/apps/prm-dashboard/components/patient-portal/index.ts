// Patient Self-Service Portal Components - Barrel Export
// EPIC-UX-011: Empowering Patients with Digital Healthcare Access

export {
  PatientDashboard,
  PatientDashboardSkeleton,
  PortalNavTabs,
} from "./patient-dashboard";

export {
  HealthRecords,
} from "./health-records";

export {
  AppointmentScheduler,
} from "./appointment-scheduler";

export {
  PatientMessaging,
} from "./patient-messaging";

export {
  Medications,
} from "./medications";

export {
  PatientBilling,
} from "./patient-billing";

// Re-export types
export type {
  PatientProfile,
  HealthCondition,
  Allergy,
  LabResult,
  LabReport,
  VisitSummary,
  Immunization,
  HealthSummary,
  Medication,
  RefillRequest,
  Appointment,
  AppointmentStatus,
  AvailableSlot,
  PortalMessage,
  MessageThread,
  Bill,
  PaymentMethod,
  PaymentPlan,
} from "@/lib/store/patient-portal-store";
