// Mobile Applications Components - Barrel Export
// EPIC-UX-012: Native Mobile Experience for Patients and Providers

// Onboarding
export {
  MobileOnboarding,
  ProviderMobileOnboarding,
} from "./mobile-onboarding";

// Patient Mobile Home
export {
  MobilePatientHome,
  PatientHomeWidget,
} from "./mobile-patient-home";

// Provider Mobile Home
export {
  MobileProviderHome,
  ProviderAlertsWidget,
} from "./mobile-provider-home";

// Patient Lookup
export {
  MobilePatientLookup,
  PatientSearchWidget,
} from "./mobile-patient-lookup";

// Patient Chart
export {
  MobilePatientChart,
  PatientChartWidget,
} from "./mobile-patient-chart";

// Telehealth
export {
  MobileTelehealth,
  TelehealthWaitingRoom,
} from "./mobile-telehealth";

// Health Integration
export {
  HealthIntegrationView,
  HealthSummaryWidget,
} from "./health-integration";

// Push Notifications
export {
  PushNotificationsView,
  NotificationBellWidget,
  NotificationPreview,
} from "./push-notifications";

// Re-export types from store
export type {
  DeviceInfo,
  PushNotification,
  MedicationReminder,
  HealthDataPoint,
  HealthIntegration,
  ProviderAlert,
  QuickPatient,
  SyncStatus,
} from "@/lib/store/mobile-store";
