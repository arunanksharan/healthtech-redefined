/**
 * Admin Store
 *
 * Manages admin mode state for accessing Zoice integration features.
 * When admin mode is enabled, additional navigation items appear in the sidebar
 * for managing Zoice pipelines, agents, calls, and telephony configurations.
 */

import { create } from "zustand";
import { devtools, persist } from "zustand/middleware";

// =============================================================================
// TYPES
// =============================================================================

export interface ZoicePipeline {
  id: string;
  name: string;
  description?: string;
  pipeline_type: "realtime" | "turn_based";
  status: "active" | "inactive" | "draft";
  agent_id?: string;
  phone_numbers?: string[];
  created_at: string;
  updated_at: string;
}

export interface ZoiceAgent {
  id: string;
  name: string;
  description?: string;
  system_prompt?: string;
  language?: string;
  voice_id?: string;
  llm_config_id?: string;
  stt_config_id?: string;
  tts_config_id?: string;
  created_at: string;
  updated_at: string;
}

export interface ZoiceCall {
  id: string;
  pipeline_id?: string;
  call_type: "inbound" | "outbound";
  status: "queued" | "in_progress" | "completed" | "failed";
  from_number: string;
  to_number: string;
  duration_seconds?: number;
  transcript?: string;
  recording_url?: string;
  created_at: string;
  ended_at?: string;
}

export interface ZoicePhoneNumber {
  id: string;
  phone_number: string;
  provider: string;
  status: "active" | "inactive";
  pipeline_id?: string;
  created_at: string;
}

export interface ZoiceAnalytics {
  total_calls: number;
  completed_calls: number;
  failed_calls: number;
  average_duration: number;
  calls_by_day: { date: string; count: number }[];
  calls_by_intent: { intent: string; count: number }[];
}

// =============================================================================
// STATE INTERFACE
// =============================================================================

interface AdminState {
  // Admin mode toggle
  isAdminMode: boolean;

  // Zoice data
  pipelines: ZoicePipeline[];
  agents: ZoiceAgent[];
  calls: ZoiceCall[];
  phoneNumbers: ZoicePhoneNumber[];
  analytics: ZoiceAnalytics | null;

  // Selected items
  selectedPipelineId: string | null;
  selectedAgentId: string | null;
  selectedCallId: string | null;

  // Loading states
  isLoadingPipelines: boolean;
  isLoadingAgents: boolean;
  isLoadingCalls: boolean;
  isLoadingPhoneNumbers: boolean;
  isLoadingAnalytics: boolean;

  // Error states
  pipelinesError: string | null;
  agentsError: string | null;
  callsError: string | null;
  phoneNumbersError: string | null;
  analyticsError: string | null;

  // UI state
  activeZoiceTab: "pipelines" | "agents" | "calls" | "phone-numbers" | "analytics";
  pipelineViewMode: "list" | "grid";
  callsFilter: {
    status?: string;
    callType?: string;
    dateRange?: { start: string; end: string };
  };
}

// =============================================================================
// ACTIONS INTERFACE
// =============================================================================

interface AdminActions {
  // Admin mode toggle
  setAdminMode: (enabled: boolean) => void;
  toggleAdminMode: () => void;

  // Pipelines
  setPipelines: (pipelines: ZoicePipeline[]) => void;
  addPipeline: (pipeline: ZoicePipeline) => void;
  updatePipeline: (id: string, updates: Partial<ZoicePipeline>) => void;
  removePipeline: (id: string) => void;
  setSelectedPipelineId: (id: string | null) => void;
  setLoadingPipelines: (loading: boolean) => void;
  setPipelinesError: (error: string | null) => void;

  // Agents
  setAgents: (agents: ZoiceAgent[]) => void;
  addAgent: (agent: ZoiceAgent) => void;
  updateAgent: (id: string, updates: Partial<ZoiceAgent>) => void;
  removeAgent: (id: string) => void;
  setSelectedAgentId: (id: string | null) => void;
  setLoadingAgents: (loading: boolean) => void;
  setAgentsError: (error: string | null) => void;

  // Calls
  setCalls: (calls: ZoiceCall[]) => void;
  addCall: (call: ZoiceCall) => void;
  updateCall: (id: string, updates: Partial<ZoiceCall>) => void;
  setSelectedCallId: (id: string | null) => void;
  setLoadingCalls: (loading: boolean) => void;
  setCallsError: (error: string | null) => void;
  setCallsFilter: (filter: AdminState["callsFilter"]) => void;

  // Phone Numbers
  setPhoneNumbers: (phoneNumbers: ZoicePhoneNumber[]) => void;
  setLoadingPhoneNumbers: (loading: boolean) => void;
  setPhoneNumbersError: (error: string | null) => void;

  // Analytics
  setAnalytics: (analytics: ZoiceAnalytics | null) => void;
  setLoadingAnalytics: (loading: boolean) => void;
  setAnalyticsError: (error: string | null) => void;

  // UI
  setActiveZoiceTab: (tab: AdminState["activeZoiceTab"]) => void;
  setPipelineViewMode: (mode: "list" | "grid") => void;

  // Reset
  resetZoiceData: () => void;
}

// =============================================================================
// INITIAL STATE
// =============================================================================

const initialState: AdminState = {
  isAdminMode: false,
  pipelines: [],
  agents: [],
  calls: [],
  phoneNumbers: [],
  analytics: null,
  selectedPipelineId: null,
  selectedAgentId: null,
  selectedCallId: null,
  isLoadingPipelines: false,
  isLoadingAgents: false,
  isLoadingCalls: false,
  isLoadingPhoneNumbers: false,
  isLoadingAnalytics: false,
  pipelinesError: null,
  agentsError: null,
  callsError: null,
  phoneNumbersError: null,
  analyticsError: null,
  activeZoiceTab: "pipelines",
  pipelineViewMode: "list",
  callsFilter: {},
};

// =============================================================================
// STORE CREATION
// =============================================================================

export const useAdminStore = create<AdminState & AdminActions>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,

        // Admin mode toggle
        setAdminMode: (enabled) => set({ isAdminMode: enabled }, false, "setAdminMode"),
        toggleAdminMode: () =>
          set((state) => ({ isAdminMode: !state.isAdminMode }), false, "toggleAdminMode"),

        // Pipelines
        setPipelines: (pipelines) => set({ pipelines }, false, "setPipelines"),
        addPipeline: (pipeline) =>
          set(
            (state) => ({ pipelines: [...state.pipelines, pipeline] }),
            false,
            "addPipeline"
          ),
        updatePipeline: (id, updates) =>
          set(
            (state) => ({
              pipelines: state.pipelines.map((p) =>
                p.id === id ? { ...p, ...updates } : p
              ),
            }),
            false,
            "updatePipeline"
          ),
        removePipeline: (id) =>
          set(
            (state) => ({
              pipelines: state.pipelines.filter((p) => p.id !== id),
              selectedPipelineId:
                state.selectedPipelineId === id ? null : state.selectedPipelineId,
            }),
            false,
            "removePipeline"
          ),
        setSelectedPipelineId: (id) =>
          set({ selectedPipelineId: id }, false, "setSelectedPipelineId"),
        setLoadingPipelines: (loading) =>
          set({ isLoadingPipelines: loading }, false, "setLoadingPipelines"),
        setPipelinesError: (error) =>
          set({ pipelinesError: error }, false, "setPipelinesError"),

        // Agents
        setAgents: (agents) => set({ agents }, false, "setAgents"),
        addAgent: (agent) =>
          set((state) => ({ agents: [...state.agents, agent] }), false, "addAgent"),
        updateAgent: (id, updates) =>
          set(
            (state) => ({
              agents: state.agents.map((a) => (a.id === id ? { ...a, ...updates } : a)),
            }),
            false,
            "updateAgent"
          ),
        removeAgent: (id) =>
          set(
            (state) => ({
              agents: state.agents.filter((a) => a.id !== id),
              selectedAgentId: state.selectedAgentId === id ? null : state.selectedAgentId,
            }),
            false,
            "removeAgent"
          ),
        setSelectedAgentId: (id) =>
          set({ selectedAgentId: id }, false, "setSelectedAgentId"),
        setLoadingAgents: (loading) =>
          set({ isLoadingAgents: loading }, false, "setLoadingAgents"),
        setAgentsError: (error) => set({ agentsError: error }, false, "setAgentsError"),

        // Calls
        setCalls: (calls) => set({ calls }, false, "setCalls"),
        addCall: (call) =>
          set((state) => ({ calls: [call, ...state.calls] }), false, "addCall"),
        updateCall: (id, updates) =>
          set(
            (state) => ({
              calls: state.calls.map((c) => (c.id === id ? { ...c, ...updates } : c)),
            }),
            false,
            "updateCall"
          ),
        setSelectedCallId: (id) => set({ selectedCallId: id }, false, "setSelectedCallId"),
        setLoadingCalls: (loading) =>
          set({ isLoadingCalls: loading }, false, "setLoadingCalls"),
        setCallsError: (error) => set({ callsError: error }, false, "setCallsError"),
        setCallsFilter: (filter) =>
          set({ callsFilter: filter }, false, "setCallsFilter"),

        // Phone Numbers
        setPhoneNumbers: (phoneNumbers) =>
          set({ phoneNumbers }, false, "setPhoneNumbers"),
        setLoadingPhoneNumbers: (loading) =>
          set({ isLoadingPhoneNumbers: loading }, false, "setLoadingPhoneNumbers"),
        setPhoneNumbersError: (error) =>
          set({ phoneNumbersError: error }, false, "setPhoneNumbersError"),

        // Analytics
        setAnalytics: (analytics) => set({ analytics }, false, "setAnalytics"),
        setLoadingAnalytics: (loading) =>
          set({ isLoadingAnalytics: loading }, false, "setLoadingAnalytics"),
        setAnalyticsError: (error) =>
          set({ analyticsError: error }, false, "setAnalyticsError"),

        // UI
        setActiveZoiceTab: (tab) => set({ activeZoiceTab: tab }, false, "setActiveZoiceTab"),
        setPipelineViewMode: (mode) =>
          set({ pipelineViewMode: mode }, false, "setPipelineViewMode"),

        // Reset
        resetZoiceData: () =>
          set(
            {
              pipelines: [],
              agents: [],
              calls: [],
              phoneNumbers: [],
              analytics: null,
              selectedPipelineId: null,
              selectedAgentId: null,
              selectedCallId: null,
              pipelinesError: null,
              agentsError: null,
              callsError: null,
              phoneNumbersError: null,
              analyticsError: null,
            },
            false,
            "resetZoiceData"
          ),
      }),
      {
        name: "prm-admin-store",
        // Only persist admin mode toggle, not the data
        partialize: (state) => ({ isAdminMode: state.isAdminMode }),
      }
    ),
    { name: "AdminStore" }
  )
);

// =============================================================================
// SELECTORS
// =============================================================================

export const selectIsAdminMode = (state: AdminState) => state.isAdminMode;
export const selectPipelines = (state: AdminState) => state.pipelines;
export const selectAgents = (state: AdminState) => state.agents;
export const selectCalls = (state: AdminState) => state.calls;
export const selectPhoneNumbers = (state: AdminState) => state.phoneNumbers;
export const selectAnalytics = (state: AdminState) => state.analytics;

export const selectSelectedPipeline = (state: AdminState & AdminActions) =>
  state.pipelines.find((p) => p.id === state.selectedPipelineId) || null;

export const selectSelectedAgent = (state: AdminState & AdminActions) =>
  state.agents.find((a) => a.id === state.selectedAgentId) || null;

export const selectSelectedCall = (state: AdminState & AdminActions) =>
  state.calls.find((c) => c.id === state.selectedCallId) || null;

export const selectActivePipelines = (state: AdminState) =>
  state.pipelines.filter((p) => p.status === "active");

export const selectRealtimePipelines = (state: AdminState) =>
  state.pipelines.filter((p) => p.pipeline_type === "realtime");

export const selectTurnBasedPipelines = (state: AdminState) =>
  state.pipelines.filter((p) => p.pipeline_type === "turn_based");

export const selectFilteredCalls = (state: AdminState) => {
  let filtered = state.calls;
  const { status, callType, dateRange } = state.callsFilter;

  if (status) {
    filtered = filtered.filter((c) => c.status === status);
  }
  if (callType) {
    filtered = filtered.filter((c) => c.call_type === callType);
  }
  if (dateRange?.start && dateRange?.end) {
    filtered = filtered.filter((c) => {
      const callDate = new Date(c.created_at);
      return (
        callDate >= new Date(dateRange.start) && callDate <= new Date(dateRange.end)
      );
    });
  }

  return filtered;
};

export const selectAssignedPhoneNumbers = (state: AdminState) =>
  state.phoneNumbers.filter((p) => p.pipeline_id);

export const selectAvailablePhoneNumbers = (state: AdminState) =>
  state.phoneNumbers.filter((p) => !p.pipeline_id && p.status === "active");
