// Mobile Store - Mobile Applications
// EPIC-UX-012: Native Mobile Experience for Patients and Providers

import { create } from "zustand";
import { devtools, subscribeWithSelector, persist } from "zustand/middleware";

// =============================================================================
// TYPE DEFINITIONS
// =============================================================================

export interface DeviceInfo {
  id: string;
  platform: "ios" | "android" | "web";
  model: string;
  osVersion: string;
  appVersion: string;
  pushToken?: string;
  biometricEnabled: boolean;
  lastSyncAt?: string;
}

export interface PushNotification {
  id: string;
  type: "appointment" | "telehealth" | "message" | "lab_result" | "medication" | "bill" | "alert" | "consult";
  title: string;
  body: string;
  data?: Record<string, string>;
  timestamp: string;
  read: boolean;
  actionUrl?: string;
}

export interface MedicationReminder {
  id: string;
  medicationId: string;
  medicationName: string;
  dosage: string;
  scheduledTime: string;
  taken: boolean;
  takenAt?: string;
  snoozedUntil?: string;
}

export interface HealthDataPoint {
  type: "heart_rate" | "blood_pressure" | "steps" | "weight" | "sleep" | "glucose";
  value: number | string;
  unit: string;
  timestamp: string;
  source: "apple_health" | "google_fit" | "manual";
}

export interface HealthIntegration {
  id: string;
  provider: "apple_health" | "google_fit";
  enabled: boolean;
  permissions: {
    heartRate: boolean;
    bloodPressure: boolean;
    steps: boolean;
    weight: boolean;
    sleep: boolean;
    glucose: boolean;
  };
  lastSyncAt?: string;
}

export interface ProviderAlert {
  id: string;
  type: "critical_lab" | "consult_request" | "rx_refill" | "patient_message" | "schedule_change";
  priority: "high" | "medium" | "low";
  title: string;
  patientName?: string;
  patientMrn?: string;
  message: string;
  timestamp: string;
  acknowledged: boolean;
  actionUrl?: string;
}

export interface QuickPatient {
  id: string;
  mrn: string;
  name: string;
  age: number;
  gender: string;
  lastVisit: string;
  allergies: string[];
  conditions: string[];
  hasActiveAlerts: boolean;
}

export interface SyncStatus {
  isOnline: boolean;
  lastSyncAt: string;
  pendingChanges: number;
  syncInProgress: boolean;
}

// =============================================================================
// STORE STATE
// =============================================================================

interface MobileState {
  // Device
  device: DeviceInfo | null;
  isDeviceRegistered: boolean;

  // Authentication
  isBiometricEnabled: boolean;
  isAppLocked: boolean;
  lastActiveAt: string | null;

  // Notifications
  notifications: PushNotification[];
  unreadCount: number;
  pushEnabled: boolean;

  // Medication reminders
  medicationReminders: MedicationReminder[];
  activeReminder: MedicationReminder | null;

  // Health integration
  healthIntegration: HealthIntegration | null;
  recentHealthData: HealthDataPoint[];
  isHealthSyncing: boolean;

  // Provider alerts (for provider app)
  providerAlerts: ProviderAlert[];
  unacknowledgedAlerts: number;

  // Patient search (for provider app)
  recentPatients: QuickPatient[];
  searchResults: QuickPatient[];
  isSearching: boolean;

  // Sync
  syncStatus: SyncStatus;

  // Onboarding
  onboardingComplete: boolean;
  currentOnboardingStep: number;

  // Actions
  registerDevice: (device: Partial<DeviceInfo>) => Promise<void>;
  enableBiometrics: (enabled: boolean) => void;
  lockApp: () => void;
  unlockApp: () => void;

  fetchNotifications: () => Promise<void>;
  markNotificationRead: (id: string) => void;
  clearAllNotifications: () => void;
  enablePushNotifications: (enabled: boolean) => Promise<void>;

  fetchMedicationReminders: () => Promise<void>;
  markMedicationTaken: (reminderId: string) => void;
  snoozeMedicationReminder: (reminderId: string, minutes: number) => void;

  setupHealthIntegration: (provider: "apple_health" | "google_fit") => Promise<void>;
  updateHealthPermissions: (permissions: Partial<HealthIntegration["permissions"]>) => void;
  syncHealthData: () => Promise<void>;

  fetchProviderAlerts: () => Promise<void>;
  acknowledgeAlert: (id: string) => void;

  searchPatients: (query: string) => Promise<void>;
  addToRecentPatients: (patient: QuickPatient) => void;
  clearRecentPatients: () => void;

  syncOfflineChanges: () => Promise<void>;
  updateSyncStatus: (status: Partial<SyncStatus>) => void;

  completeOnboarding: () => void;
  setOnboardingStep: (step: number) => void;
}

// =============================================================================
// MOCK DATA
// =============================================================================

const mockNotifications: PushNotification[] = [
  { id: "notif1", type: "appointment", title: "Appointment Tomorrow", body: "Your appointment with Dr. Sharma is tomorrow at 2:00 PM", timestamp: new Date(Date.now() - 3600000).toISOString(), read: false, actionUrl: "/appointments/apt1" },
  { id: "notif2", type: "medication", title: "Time for Medication", body: "Take Metformin 1000mg with dinner", timestamp: new Date(Date.now() - 7200000).toISOString(), read: false },
  { id: "notif3", type: "message", title: "New Message", body: "Dr. Sharma's office sent you a message about your lab results", timestamp: new Date(Date.now() - 86400000).toISOString(), read: true, actionUrl: "/messages/thread1" },
  { id: "notif4", type: "lab_result", title: "Lab Results Ready", body: "Your recent lab results are now available to view", timestamp: new Date(Date.now() - 172800000).toISOString(), read: true, actionUrl: "/records/labs" },
];

const mockMedicationReminders: MedicationReminder[] = [
  { id: "rem1", medicationId: "med1", medicationName: "Metformin 1000mg", dosage: "1 tablet", scheduledTime: "08:00", taken: true, takenAt: new Date().toISOString() },
  { id: "rem2", medicationId: "med1", medicationName: "Metformin 1000mg", dosage: "1 tablet", scheduledTime: "19:00", taken: false },
  { id: "rem3", medicationId: "med2", medicationName: "Lisinopril 10mg", dosage: "1 tablet", scheduledTime: "09:00", taken: false },
];

const mockHealthData: HealthDataPoint[] = [
  { type: "steps", value: 8432, unit: "steps", timestamp: new Date().toISOString(), source: "apple_health" },
  { type: "heart_rate", value: 72, unit: "bpm", timestamp: new Date().toISOString(), source: "apple_health" },
  { type: "blood_pressure", value: "128/82", unit: "mmHg", timestamp: new Date().toISOString(), source: "manual" },
  { type: "weight", value: 185, unit: "lbs", timestamp: new Date(Date.now() - 86400000).toISOString(), source: "apple_health" },
];

const mockProviderAlerts: ProviderAlert[] = [
  { id: "alert1", type: "critical_lab", priority: "high", title: "Critical Lab Result", patientName: "Mary Johnson", patientMrn: "67890", message: "Critical value - Potassium 6.2 mEq/L", timestamp: new Date(Date.now() - 1800000).toISOString(), acknowledged: false },
  { id: "alert2", type: "consult_request", priority: "medium", title: "Consult Request", patientName: "John Doe", patientMrn: "12345", message: "Dr. Patel requested Cardiology consult", timestamp: new Date(Date.now() - 3600000).toISOString(), acknowledged: false },
  { id: "alert3", type: "rx_refill", priority: "medium", title: "Rx Refill Needed", patientName: "Bob Wilson", patientMrn: "11111", message: "Lisinopril refill request - no refills remaining", timestamp: new Date(Date.now() - 7200000).toISOString(), acknowledged: false },
];

const mockQuickPatients: QuickPatient[] = [
  { id: "p1", mrn: "12345", name: "John Doe", age: 59, gender: "M", lastVisit: "2024-11-20", allergies: ["Penicillin"], conditions: ["T2DM", "HTN"], hasActiveAlerts: false },
  { id: "p2", mrn: "67890", name: "Mary Johnson", age: 45, gender: "F", lastVisit: "2024-11-25", allergies: [], conditions: ["CKD", "A-fib"], hasActiveAlerts: true },
  { id: "p3", mrn: "11111", name: "Bob Wilson", age: 72, gender: "M", lastVisit: "2024-10-15", allergies: ["Sulfa"], conditions: ["CHF"], hasActiveAlerts: false },
];

// =============================================================================
// STORE IMPLEMENTATION
// =============================================================================

export const useMobileStore = create<MobileState>()(
  devtools(
    persist(
      subscribeWithSelector((set, get) => ({
        // Initial state
        device: null,
        isDeviceRegistered: false,
        isBiometricEnabled: false,
        isAppLocked: false,
        lastActiveAt: null,
        notifications: [],
        unreadCount: 0,
        pushEnabled: true,
        medicationReminders: [],
        activeReminder: null,
        healthIntegration: null,
        recentHealthData: [],
        isHealthSyncing: false,
        providerAlerts: [],
        unacknowledgedAlerts: 0,
        recentPatients: [],
        searchResults: [],
        isSearching: false,
        syncStatus: {
          isOnline: true,
          lastSyncAt: new Date().toISOString(),
          pendingChanges: 0,
          syncInProgress: false,
        },
        onboardingComplete: false,
        currentOnboardingStep: 0,

        // Device actions
        registerDevice: async (device) => {
          await new Promise((r) => setTimeout(r, 500));
          const fullDevice: DeviceInfo = {
            id: `device-${Date.now()}`,
            platform: device.platform || "web",
            model: device.model || "Unknown",
            osVersion: device.osVersion || "Unknown",
            appVersion: device.appVersion || "1.0.0",
            biometricEnabled: false,
            ...device,
          };
          set({ device: fullDevice, isDeviceRegistered: true });
        },

        enableBiometrics: (enabled) => {
          set((state) => ({
            isBiometricEnabled: enabled,
            device: state.device ? { ...state.device, biometricEnabled: enabled } : null,
          }));
        },

        lockApp: () => set({ isAppLocked: true }),
        unlockApp: () => set({ isAppLocked: false, lastActiveAt: new Date().toISOString() }),

        // Notification actions
        fetchNotifications: async () => {
          await new Promise((r) => setTimeout(r, 300));
          const unread = mockNotifications.filter((n) => !n.read).length;
          set({ notifications: mockNotifications, unreadCount: unread });
        },

        markNotificationRead: (id) => {
          set((state) => {
            const updated = state.notifications.map((n) => (n.id === id ? { ...n, read: true } : n));
            return { notifications: updated, unreadCount: updated.filter((n) => !n.read).length };
          });
        },

        clearAllNotifications: () => {
          set({ notifications: [], unreadCount: 0 });
        },

        enablePushNotifications: async (enabled) => {
          await new Promise((r) => setTimeout(r, 500));
          set({ pushEnabled: enabled });
        },

        // Medication reminder actions
        fetchMedicationReminders: async () => {
          await new Promise((r) => setTimeout(r, 300));
          const now = new Date();
          const currentHour = now.getHours();
          const activeReminder = mockMedicationReminders.find((r) => {
            const hour = parseInt(r.scheduledTime.split(":")[0]);
            return !r.taken && hour <= currentHour;
          });
          set({ medicationReminders: mockMedicationReminders, activeReminder: activeReminder || null });
        },

        markMedicationTaken: (reminderId) => {
          set((state) => ({
            medicationReminders: state.medicationReminders.map((r) =>
              r.id === reminderId ? { ...r, taken: true, takenAt: new Date().toISOString() } : r
            ),
            activeReminder: state.activeReminder?.id === reminderId ? null : state.activeReminder,
          }));
        },

        snoozeMedicationReminder: (reminderId, minutes) => {
          const snoozedUntil = new Date(Date.now() + minutes * 60000).toISOString();
          set((state) => ({
            medicationReminders: state.medicationReminders.map((r) =>
              r.id === reminderId ? { ...r, snoozedUntil } : r
            ),
            activeReminder: state.activeReminder?.id === reminderId ? null : state.activeReminder,
          }));
        },

        // Health integration actions
        setupHealthIntegration: async (provider) => {
          await new Promise((r) => setTimeout(r, 1000));
          const integration: HealthIntegration = {
            id: `health-${Date.now()}`,
            provider,
            enabled: true,
            permissions: {
              heartRate: true,
              bloodPressure: true,
              steps: true,
              weight: true,
              sleep: false,
              glucose: false,
            },
            lastSyncAt: new Date().toISOString(),
          };
          set({ healthIntegration: integration, recentHealthData: mockHealthData });
        },

        updateHealthPermissions: (permissions) => {
          set((state) => ({
            healthIntegration: state.healthIntegration
              ? { ...state.healthIntegration, permissions: { ...state.healthIntegration.permissions, ...permissions } }
              : null,
          }));
        },

        syncHealthData: async () => {
          set({ isHealthSyncing: true });
          await new Promise((r) => setTimeout(r, 1500));
          set((state) => ({
            isHealthSyncing: false,
            healthIntegration: state.healthIntegration
              ? { ...state.healthIntegration, lastSyncAt: new Date().toISOString() }
              : null,
            recentHealthData: mockHealthData,
          }));
        },

        // Provider alert actions
        fetchProviderAlerts: async () => {
          await new Promise((r) => setTimeout(r, 300));
          const unacknowledged = mockProviderAlerts.filter((a) => !a.acknowledged).length;
          set({ providerAlerts: mockProviderAlerts, unacknowledgedAlerts: unacknowledged });
        },

        acknowledgeAlert: (id) => {
          set((state) => {
            const updated = state.providerAlerts.map((a) => (a.id === id ? { ...a, acknowledged: true } : a));
            return { providerAlerts: updated, unacknowledgedAlerts: updated.filter((a) => !a.acknowledged).length };
          });
        },

        // Patient search actions
        searchPatients: async (query) => {
          set({ isSearching: true });
          await new Promise((r) => setTimeout(r, 500));
          const results = mockQuickPatients.filter(
            (p) =>
              p.name.toLowerCase().includes(query.toLowerCase()) ||
              p.mrn.includes(query)
          );
          set({ searchResults: results, isSearching: false });
        },

        addToRecentPatients: (patient) => {
          set((state) => {
            const existing = state.recentPatients.filter((p) => p.id !== patient.id);
            return { recentPatients: [patient, ...existing].slice(0, 10) };
          });
        },

        clearRecentPatients: () => set({ recentPatients: [] }),

        // Sync actions
        syncOfflineChanges: async () => {
          set((state) => ({ syncStatus: { ...state.syncStatus, syncInProgress: true } }));
          await new Promise((r) => setTimeout(r, 2000));
          set((state) => ({
            syncStatus: {
              ...state.syncStatus,
              syncInProgress: false,
              lastSyncAt: new Date().toISOString(),
              pendingChanges: 0,
            },
          }));
        },

        updateSyncStatus: (status) => {
          set((state) => ({ syncStatus: { ...state.syncStatus, ...status } }));
        },

        // Onboarding actions
        completeOnboarding: () => set({ onboardingComplete: true }),
        setOnboardingStep: (step) => set({ currentOnboardingStep: step }),
      })),
      {
        name: "mobile-store",
        partialize: (state) => ({
          device: state.device,
          isBiometricEnabled: state.isBiometricEnabled,
          pushEnabled: state.pushEnabled,
          healthIntegration: state.healthIntegration,
          recentPatients: state.recentPatients,
          onboardingComplete: state.onboardingComplete,
        }),
      }
    ),
    { name: "mobile-store" }
  )
);

export default useMobileStore;
