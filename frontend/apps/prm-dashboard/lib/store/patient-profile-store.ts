"use client";

import { create } from "zustand";
import { devtools, subscribeWithSelector } from "zustand/middleware";

// ============================================================================
// Types & Interfaces
// ============================================================================

export type Gender = "male" | "female" | "other" | "unknown";
export type AlertSeverity = "critical" | "high" | "medium" | "low";
export type AlertType = "allergy" | "condition" | "care-gap" | "fall-risk" | "medication" | "flag";
export type VitalStatus = "normal" | "warning" | "critical";
export type TrendDirection = "up" | "down" | "stable";
export type EventType = "encounter" | "call" | "message" | "lab" | "prescription" | "appointment" | "document" | "referral";
export type ChannelType = "fhir" | "zoice" | "whatsapp" | "email" | "sms" | "app";
export type CareGapStatus = "overdue" | "due-soon" | "up-to-date" | "not-applicable";
export type ViewMode = "story" | "clinical" | "engagement" | "analytics";

export interface Address {
  line1: string;
  line2?: string;
  city: string;
  state: string;
  postalCode: string;
  country: string;
}

export interface InsuranceInfo {
  provider: string;
  planName: string;
  memberId: string;
  groupId?: string;
  status: "active" | "inactive" | "pending";
  effectiveDate?: Date;
  expirationDate?: Date;
}

export interface Practitioner {
  id: string;
  name: string;
  specialty?: string;
  phone?: string;
  email?: string;
}

export interface PatientAlert {
  id: string;
  type: AlertType;
  severity: AlertSeverity;
  title: string;
  description?: string;
  source?: string;
  createdAt: Date;
  acknowledgedAt?: Date;
  acknowledgedBy?: string;
}

export interface VitalSign {
  name: string;
  code: string;
  value: number | string;
  unit: string;
  status: VitalStatus;
  trend: TrendDirection;
  trendValue?: string;
  lastUpdated: Date;
  referenceRange?: {
    low?: number;
    high?: number;
  };
}

export interface HealthScore {
  score: number; // 0-100
  trend: TrendDirection;
  label: "Excellent" | "Good" | "Fair" | "Poor" | "Critical";
  lastUpdated: Date;
  components: HealthScoreComponent[];
}

export interface HealthScoreComponent {
  name: string;
  value: number | string;
  unit?: string;
  status: VitalStatus;
  trend: TrendDirection;
  trendValue?: string;
}

export interface TimelineEvent {
  id: string;
  type: EventType;
  channel: ChannelType;
  timestamp: Date;
  title: string;
  summary: string;
  content?: string;
  sentiment?: {
    label: string;
    score: number;
    emoji: string;
  };
  relatedEvents?: string[];
  episodeId?: string;
  metadata?: Record<string, unknown>;
  actions?: TimelineAction[];
}

export interface TimelineAction {
  id: string;
  label: string;
  type: string;
  isPrimary?: boolean;
}

export interface Episode {
  id: string;
  title: string;
  type: string;
  startDate: Date;
  endDate?: Date;
  trigger: string;
  outcome?: string;
  events: TimelineEvent[];
  isExpanded: boolean;
}

export interface CareGap {
  id: string;
  title: string;
  description?: string;
  category: "preventive" | "chronic" | "wellness" | "screening";
  status: CareGapStatus;
  dueDate?: Date;
  lastCompletedDate?: Date;
  overdueDays?: number;
  actions: CareGapAction[];
}

export interface CareGapAction {
  id: string;
  label: string;
  type: string;
}

export interface Communication {
  id: string;
  channel: ChannelType;
  direction: "inbound" | "outbound";
  timestamp: Date;
  subject?: string;
  preview: string;
  content?: string;
  sentiment?: {
    label: string;
    score: number;
    emoji: string;
  };
  duration?: number; // For calls, in seconds
  status: "delivered" | "read" | "replied" | "failed" | "pending";
  attachments?: Attachment[];
}

export interface Attachment {
  id: string;
  name: string;
  type: string;
  url: string;
  size?: number;
}

export interface AISummary {
  id: string;
  content: string;
  recentActivity: string[];
  keyConcerns: string[];
  suggestedDiscussionPoints: string[];
  generatedAt: Date;
  isLoading: boolean;
}

export interface Patient {
  id: string;
  name: string;
  firstName: string;
  lastName: string;
  dob: Date;
  age: number;
  gender: Gender;
  mrn: string;
  ssn?: string;
  phone: string;
  email?: string;
  address?: Address;
  photo?: string;
  primaryProvider?: Practitioner;
  insurance?: InsuranceInfo;
  nextAppointment?: {
    id: string;
    dateTime: Date;
    provider: string;
    type: string;
    status: string;
  };
  preferredLanguage?: string;
  preferredContact?: "phone" | "email" | "sms" | "whatsapp";
}

export interface QueryResponse {
  id: string;
  query: string;
  type: "text" | "chart" | "table" | "document" | "list";
  content: unknown;
  analysis?: string;
  actions?: TimelineAction[];
  timestamp: Date;
}

// ============================================================================
// State Interface
// ============================================================================

export interface PatientProfileState {
  // Patient data
  patient: Patient | null;
  isLoadingPatient: boolean;
  patientError: string | null;

  // Alerts
  alerts: PatientAlert[];
  isLoadingAlerts: boolean;

  // Health score and vitals
  healthScore: HealthScore | null;
  vitals: VitalSign[];
  isLoadingVitals: boolean;

  // AI Summary
  aiSummary: AISummary | null;
  isGeneratingSummary: boolean;

  // Timeline
  timelineEvents: TimelineEvent[];
  episodes: Episode[];
  isLoadingTimeline: boolean;
  hasMoreTimeline: boolean;
  timelineFilter: {
    eventTypes: EventType[];
    channels: ChannelType[];
    dateRange?: { from: Date; to: Date };
  };

  // Care gaps
  careGaps: CareGap[];
  isLoadingCareGaps: boolean;

  // Communications
  communications: Communication[];
  isLoadingCommunications: boolean;
  communicationFilter: ChannelType | "all";

  // Query interface
  queryHistory: QueryResponse[];
  isQueryLoading: boolean;
  currentQuery: string;

  // UI state
  viewMode: ViewMode;
  activeTab: string;
  expandedEpisodes: Set<string>;
}

// ============================================================================
// Actions Interface
// ============================================================================

export interface PatientProfileActions {
  // Patient actions
  setPatient: (patient: Patient | null) => void;
  loadPatient: (patientId: string) => Promise<void>;
  updatePatient: (updates: Partial<Patient>) => void;

  // Alert actions
  setAlerts: (alerts: PatientAlert[]) => void;
  acknowledgeAlert: (alertId: string) => void;
  dismissAlert: (alertId: string) => void;

  // Health score actions
  setHealthScore: (score: HealthScore | null) => void;
  setVitals: (vitals: VitalSign[]) => void;

  // AI Summary actions
  setAISummary: (summary: AISummary | null) => void;
  regenerateSummary: () => Promise<void>;
  setGeneratingSummary: (loading: boolean) => void;

  // Timeline actions
  setTimelineEvents: (events: TimelineEvent[]) => void;
  addTimelineEvent: (event: TimelineEvent) => void;
  setEpisodes: (episodes: Episode[]) => void;
  loadMoreTimeline: () => Promise<void>;
  setTimelineFilter: (filter: Partial<PatientProfileState["timelineFilter"]>) => void;
  toggleEpisodeExpand: (episodeId: string) => void;

  // Care gap actions
  setCareGaps: (gaps: CareGap[]) => void;
  updateCareGapStatus: (gapId: string, status: CareGapStatus) => void;

  // Communication actions
  setCommunications: (communications: Communication[]) => void;
  setCommunicationFilter: (filter: ChannelType | "all") => void;

  // Query actions
  submitQuery: (query: string) => Promise<void>;
  setCurrentQuery: (query: string) => void;
  clearQueryHistory: () => void;

  // UI actions
  setViewMode: (mode: ViewMode) => void;
  setActiveTab: (tab: string) => void;

  // Reset
  reset: () => void;
}

// ============================================================================
// Initial State
// ============================================================================

const initialState: PatientProfileState = {
  patient: null,
  isLoadingPatient: false,
  patientError: null,

  alerts: [],
  isLoadingAlerts: false,

  healthScore: null,
  vitals: [],
  isLoadingVitals: false,

  aiSummary: null,
  isGeneratingSummary: false,

  timelineEvents: [],
  episodes: [],
  isLoadingTimeline: false,
  hasMoreTimeline: true,
  timelineFilter: {
    eventTypes: [],
    channels: [],
  },

  careGaps: [],
  isLoadingCareGaps: false,

  communications: [],
  isLoadingCommunications: false,
  communicationFilter: "all",

  queryHistory: [],
  isQueryLoading: false,
  currentQuery: "",

  viewMode: "story",
  activeTab: "overview",
  expandedEpisodes: new Set(),
};

// ============================================================================
// Store
// ============================================================================

export const usePatientProfileStore = create<PatientProfileState & PatientProfileActions>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      ...initialState,

      // ========================================================================
      // Patient Actions
      // ========================================================================

      setPatient: (patient) => {
        set({ patient, patientError: null });
      },

      loadPatient: async (patientId: string) => {
        set({ isLoadingPatient: true, patientError: null });

        try {
          // In production, this would be an API call
          await new Promise((resolve) => setTimeout(resolve, 500));

          // Mock patient data
          const mockPatient = createMockPatient(patientId);
          set({ patient: mockPatient, isLoadingPatient: false });

          // Load related data
          const { setAlerts, setHealthScore, setVitals, setAISummary, setTimelineEvents, setCareGaps, setCommunications } = get();

          setAlerts(createMockAlerts());
          setHealthScore(createMockHealthScore());
          setVitals(createMockVitals());
          setAISummary(createMockAISummary());
          setTimelineEvents(createMockTimelineEvents());
          setCareGaps(createMockCareGaps());
          setCommunications(createMockCommunications());
        } catch (error) {
          set({
            patientError: error instanceof Error ? error.message : "Failed to load patient",
            isLoadingPatient: false,
          });
        }
      },

      updatePatient: (updates) => {
        const { patient } = get();
        if (!patient) return;
        set({ patient: { ...patient, ...updates } });
      },

      // ========================================================================
      // Alert Actions
      // ========================================================================

      setAlerts: (alerts) => {
        set({ alerts });
      },

      acknowledgeAlert: (alertId) => {
        const { alerts } = get();
        set({
          alerts: alerts.map((alert) =>
            alert.id === alertId
              ? { ...alert, acknowledgedAt: new Date(), acknowledgedBy: "current_user" }
              : alert
          ),
        });
      },

      dismissAlert: (alertId) => {
        const { alerts } = get();
        set({ alerts: alerts.filter((alert) => alert.id !== alertId) });
      },

      // ========================================================================
      // Health Score Actions
      // ========================================================================

      setHealthScore: (score) => {
        set({ healthScore: score });
      },

      setVitals: (vitals) => {
        set({ vitals });
      },

      // ========================================================================
      // AI Summary Actions
      // ========================================================================

      setAISummary: (summary) => {
        set({ aiSummary: summary });
      },

      regenerateSummary: async () => {
        set({ isGeneratingSummary: true });

        try {
          // In production, this would call the AI API
          await new Promise((resolve) => setTimeout(resolve, 2000));

          const newSummary = createMockAISummary();
          newSummary.generatedAt = new Date();
          set({ aiSummary: newSummary, isGeneratingSummary: false });
        } catch (error) {
          set({ isGeneratingSummary: false });
        }
      },

      setGeneratingSummary: (loading) => {
        set({ isGeneratingSummary: loading });
      },

      // ========================================================================
      // Timeline Actions
      // ========================================================================

      setTimelineEvents: (events) => {
        set({ timelineEvents: events });
      },

      addTimelineEvent: (event) => {
        const { timelineEvents } = get();
        set({ timelineEvents: [event, ...timelineEvents] });
      },

      setEpisodes: (episodes) => {
        set({ episodes });
      },

      loadMoreTimeline: async () => {
        const { isLoadingTimeline, timelineEvents } = get();
        if (isLoadingTimeline) return;

        set({ isLoadingTimeline: true });

        try {
          // In production, this would be paginated API call
          await new Promise((resolve) => setTimeout(resolve, 500));

          // Mock loading more events
          const moreEvents = createMockTimelineEvents().map((event) => ({
            ...event,
            id: `${event.id}-${Date.now()}`,
            timestamp: new Date(event.timestamp.getTime() - 30 * 24 * 60 * 60 * 1000),
          }));

          set({
            timelineEvents: [...timelineEvents, ...moreEvents],
            isLoadingTimeline: false,
            hasMoreTimeline: moreEvents.length > 0,
          });
        } catch (error) {
          set({ isLoadingTimeline: false });
        }
      },

      setTimelineFilter: (filter) => {
        const { timelineFilter } = get();
        set({ timelineFilter: { ...timelineFilter, ...filter } });
      },

      toggleEpisodeExpand: (episodeId) => {
        const { expandedEpisodes } = get();
        const newExpanded = new Set(expandedEpisodes);
        if (newExpanded.has(episodeId)) {
          newExpanded.delete(episodeId);
        } else {
          newExpanded.add(episodeId);
        }
        set({ expandedEpisodes: newExpanded });
      },

      // ========================================================================
      // Care Gap Actions
      // ========================================================================

      setCareGaps: (gaps) => {
        set({ careGaps: gaps });
      },

      updateCareGapStatus: (gapId, status) => {
        const { careGaps } = get();
        set({
          careGaps: careGaps.map((gap) =>
            gap.id === gapId ? { ...gap, status } : gap
          ),
        });
      },

      // ========================================================================
      // Communication Actions
      // ========================================================================

      setCommunications: (communications) => {
        set({ communications });
      },

      setCommunicationFilter: (filter) => {
        set({ communicationFilter: filter });
      },

      // ========================================================================
      // Query Actions
      // ========================================================================

      submitQuery: async (query: string) => {
        set({ isQueryLoading: true, currentQuery: query });

        try {
          // In production, this would call the AI API
          await new Promise((resolve) => setTimeout(resolve, 1500));

          const response: QueryResponse = {
            id: `query-${Date.now()}`,
            query,
            type: "text",
            content: `This is a mock response for: "${query}"`,
            analysis: "Based on the patient's data, here's the analysis...",
            timestamp: new Date(),
          };

          const { queryHistory } = get();
          set({
            queryHistory: [response, ...queryHistory],
            isQueryLoading: false,
            currentQuery: "",
          });
        } catch (error) {
          set({ isQueryLoading: false });
        }
      },

      setCurrentQuery: (query) => {
        set({ currentQuery: query });
      },

      clearQueryHistory: () => {
        set({ queryHistory: [] });
      },

      // ========================================================================
      // UI Actions
      // ========================================================================

      setViewMode: (mode) => {
        set({ viewMode: mode });
      },

      setActiveTab: (tab) => {
        set({ activeTab: tab });
      },

      // ========================================================================
      // Reset
      // ========================================================================

      reset: () => {
        set(initialState);
      },
    })),
    { name: "patient-profile-store" }
  )
);

// ============================================================================
// Mock Data Generators
// ============================================================================

function createMockPatient(id: string): Patient {
  return {
    id,
    name: "John Doe",
    firstName: "John",
    lastName: "Doe",
    dob: new Date(1965, 0, 15),
    age: 59,
    gender: "male",
    mrn: "12345",
    ssn: "***-**-6789",
    phone: "+1 (555) 123-4567",
    email: "john.doe@email.com",
    address: {
      line1: "123 Main Street",
      city: "Bangalore",
      state: "Karnataka",
      postalCode: "560001",
      country: "India",
    },
    primaryProvider: {
      id: "prac-1",
      name: "Dr. Rohit Sharma",
      specialty: "Cardiology",
    },
    insurance: {
      provider: "Aetna",
      planName: "PPO",
      memberId: "XYZ123456",
      status: "active",
    },
    nextAppointment: {
      id: "appt-1",
      dateTime: new Date(),
      provider: "Dr. Sharma",
      type: "Follow-up",
      status: "confirmed",
    },
    preferredLanguage: "English",
    preferredContact: "phone",
  };
}

function createMockAlerts(): PatientAlert[] {
  return [
    {
      id: "alert-1",
      type: "allergy",
      severity: "critical",
      title: "Allergy: Penicillin (Severe - Anaphylaxis)",
      createdAt: new Date(),
    },
    {
      id: "alert-2",
      type: "fall-risk",
      severity: "medium",
      title: "Fall Risk: High (Age + Medication)",
      createdAt: new Date(),
    },
    {
      id: "alert-3",
      type: "care-gap",
      severity: "medium",
      title: "Care Gap: Overdue for A1C (Last: 6 months ago)",
      createdAt: new Date(),
    },
  ];
}

function createMockHealthScore(): HealthScore {
  return {
    score: 72,
    trend: "stable",
    label: "Fair",
    lastUpdated: new Date(),
    components: [
      { name: "BP", value: "138/88", status: "warning", trend: "up", trendValue: "+5" },
      { name: "HR", value: 78, unit: "bpm", status: "normal", trend: "stable" },
      { name: "Weight", value: 185, unit: "lbs", status: "warning", trend: "up", trendValue: "+3 lbs" },
      { name: "A1C", value: "7.2%", status: "warning", trend: "up", trendValue: "+0.1" },
      { name: "Cholesterol", value: 220, unit: "mg/dL", status: "normal", trend: "down", trendValue: "-15" },
    ],
  };
}

function createMockVitals(): VitalSign[] {
  return [
    {
      name: "Blood Pressure",
      code: "BP",
      value: "138/88",
      unit: "mmHg",
      status: "warning",
      trend: "up",
      trendValue: "+5",
      lastUpdated: new Date(),
      referenceRange: { high: 130 },
    },
    {
      name: "Heart Rate",
      code: "HR",
      value: 78,
      unit: "bpm",
      status: "normal",
      trend: "stable",
      lastUpdated: new Date(),
      referenceRange: { low: 60, high: 100 },
    },
    {
      name: "Temperature",
      code: "TEMP",
      value: 98.6,
      unit: "°F",
      status: "normal",
      trend: "stable",
      lastUpdated: new Date(),
    },
    {
      name: "Oxygen Saturation",
      code: "SpO2",
      value: 98,
      unit: "%",
      status: "normal",
      trend: "stable",
      lastUpdated: new Date(),
    },
  ];
}

function createMockAISummary(): AISummary {
  return {
    id: "summary-1",
    content: `John Doe is a 59-year-old male with a history of Type 2 Diabetes (diagnosed 2018), Hypertension (2015), and Hyperlipidemia (2019).`,
    recentActivity: [
      "Last visit Nov 20, 2024 - BP elevated, Metformin increased",
      "Called Nov 22 via Zoice - frustrated about medication side effects",
      "Sent WhatsApp Nov 23 - confirmed today's appointment",
    ],
    keyConcerns: [
      "BP trending upward despite medication increase",
      "A1C above target (7.2% vs 7.0% goal)",
      "Patient expressed medication adherence challenges",
    ],
    suggestedDiscussionPoints: [
      "Review BP management strategy",
      "Discuss A1C and dietary compliance",
      "Address medication side effect concerns from recent call",
    ],
    generatedAt: new Date(),
    isLoading: false,
  };
}

function createMockTimelineEvents(): TimelineEvent[] {
  const now = new Date();
  return [
    {
      id: "event-1",
      type: "appointment",
      channel: "fhir",
      timestamp: now,
      title: "Scheduled Appointment",
      summary: "Cardiology Follow-up with Dr. Sharma",
      actions: [
        { id: "start", label: "Start Visit", type: "start_visit", isPrimary: true },
        { id: "reschedule", label: "Reschedule", type: "reschedule" },
      ],
    },
    {
      id: "event-2",
      type: "message",
      channel: "whatsapp",
      timestamp: new Date(now.getTime() - 24 * 60 * 60 * 1000),
      title: "WhatsApp Message",
      summary: "Yes, I'll be there for my appointment tomorrow",
      actions: [{ id: "view", label: "View Conversation", type: "view" }],
    },
    {
      id: "event-3",
      type: "call",
      channel: "zoice",
      timestamp: new Date(now.getTime() - 2 * 24 * 60 * 60 * 1000),
      title: "Zoice Call (4 min)",
      summary: "Patient complained about medication side effects. Experiencing stomach upset with new Metformin dosage.",
      sentiment: { label: "frustrated", score: 87, emoji: "😤" },
      metadata: { duration: 272 },
      actions: [
        { id: "play", label: "Play Recording", type: "play" },
        { id: "transcript", label: "View Transcript", type: "transcript" },
      ],
    },
    {
      id: "event-4",
      type: "encounter",
      channel: "fhir",
      timestamp: new Date(now.getTime() - 4 * 24 * 60 * 60 * 1000),
      title: "Office Visit - Cardiology Follow-up",
      summary: "Chief Complaint: Routine follow-up, BP monitoring. Assessment: Hypertension - suboptimal control.",
      content: `Vitals: BP 142/90 mmHg, HR 76 bpm, Weight 185 lbs (+3).
Plan: Increase Metformin to 1000mg BID, Add Lisinopril 10mg daily, Follow-up in 1 week.`,
      actions: [
        { id: "note", label: "View Full Note", type: "view_note" },
        { id: "orders", label: "View Orders", type: "view_orders" },
      ],
    },
  ];
}

function createMockCareGaps(): CareGap[] {
  return [
    {
      id: "gap-1",
      title: "A1C Test",
      description: "Hemoglobin A1C test for diabetes monitoring",
      category: "chronic",
      status: "overdue",
      dueDate: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000),
      lastCompletedDate: new Date(Date.now() - 180 * 24 * 60 * 60 * 1000),
      overdueDays: 60,
      actions: [
        { id: "order", label: "Order Now", type: "order_lab" },
        { id: "schedule", label: "Schedule Lab Visit", type: "schedule" },
      ],
    },
    {
      id: "gap-2",
      title: "Diabetic Eye Exam",
      description: "Annual dilated eye examination",
      category: "preventive",
      status: "overdue",
      dueDate: new Date(Date.now() - 120 * 24 * 60 * 60 * 1000),
      lastCompletedDate: new Date(Date.now() - 500 * 24 * 60 * 60 * 1000),
      overdueDays: 120,
      actions: [
        { id: "referral", label: "Create Referral", type: "create_referral" },
        { id: "remind", label: "Send Reminder", type: "send_reminder" },
      ],
    },
    {
      id: "gap-3",
      title: "Flu Vaccination",
      description: "Annual influenza vaccination",
      category: "preventive",
      status: "due-soon",
      dueDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
      actions: [
        { id: "schedule", label: "Schedule", type: "schedule" },
        { id: "mark", label: "Mark Administered Elsewhere", type: "mark_done" },
      ],
    },
    {
      id: "gap-4",
      title: "Lipid Panel",
      description: "Cholesterol and lipid profile",
      category: "chronic",
      status: "up-to-date",
      lastCompletedDate: new Date(Date.now() - 45 * 24 * 60 * 60 * 1000),
      actions: [],
    },
  ];
}

function createMockCommunications(): Communication[] {
  const now = new Date();
  return [
    {
      id: "comm-1",
      channel: "whatsapp",
      direction: "inbound",
      timestamp: new Date(now.getTime() - 24 * 60 * 60 * 1000),
      preview: "Yes, I'll be there for my appointment tomorrow",
      status: "read",
    },
    {
      id: "comm-2",
      channel: "zoice",
      direction: "inbound",
      timestamp: new Date(now.getTime() - 2 * 24 * 60 * 60 * 1000),
      preview: "Patient complained about medication side effects...",
      duration: 272,
      status: "read",
      sentiment: { label: "frustrated", score: 87, emoji: "😤" },
    },
    {
      id: "comm-3",
      channel: "email",
      direction: "outbound",
      timestamp: new Date(now.getTime() - 4 * 24 * 60 * 60 * 1000),
      subject: "Your Visit Summary - Dr. Sharma",
      preview: "Dear John, Thank you for visiting...",
      status: "delivered",
    },
  ];
}

// ============================================================================
// Selectors
// ============================================================================

export const selectPatient = (state: PatientProfileState) => state.patient;
export const selectAlerts = (state: PatientProfileState) => state.alerts;
export const selectCriticalAlerts = (state: PatientProfileState) =>
  state.alerts.filter((a) => a.severity === "critical");
export const selectHealthScore = (state: PatientProfileState) => state.healthScore;
export const selectVitals = (state: PatientProfileState) => state.vitals;
export const selectAISummary = (state: PatientProfileState) => state.aiSummary;
export const selectTimelineEvents = (state: PatientProfileState) => state.timelineEvents;
export const selectCareGaps = (state: PatientProfileState) => state.careGaps;
export const selectOverdueCareGaps = (state: PatientProfileState) =>
  state.careGaps.filter((g) => g.status === "overdue");
export const selectCommunications = (state: PatientProfileState) => state.communications;
export const selectFilteredCommunications = (state: PatientProfileState) => {
  if (state.communicationFilter === "all") return state.communications;
  return state.communications.filter((c) => c.channel === state.communicationFilter);
};
