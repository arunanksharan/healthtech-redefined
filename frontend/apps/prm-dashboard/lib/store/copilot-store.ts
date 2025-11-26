"use client";

import { create } from "zustand";
import { devtools, subscribeWithSelector } from "zustand/middleware";

// ============================================================================
// Types & Interfaces
// ============================================================================

export type EntityType =
  | "patient"
  | "practitioner"
  | "location"
  | "time"
  | "date"
  | "action"
  | "medication"
  | "department"
  | "duration"
  | "visit_type"
  | "recurrence"
  | "phone"
  | "mrn"
  | "unknown";

export type IntentType =
  // Appointment Commands
  | "book_appointment"
  | "reschedule_appointment"
  | "cancel_appointment"
  | "view_schedule"
  | "find_slot"
  | "block_calendar"
  // Patient Commands
  | "find_patient"
  | "add_patient"
  | "update_patient"
  | "view_patient_history"
  | "add_allergy"
  | "record_vitals"
  // Clinical Commands
  | "prescribe_medication"
  | "order_lab"
  | "create_referral"
  | "add_clinical_note"
  | "start_telehealth"
  // Communication Commands
  | "send_whatsapp"
  | "send_reminder"
  | "broadcast_message"
  | "call_patient"
  // Analytics Commands
  | "show_appointments"
  | "show_analytics"
  | "generate_report"
  // Administrative Commands
  | "add_slot"
  | "set_leave"
  | "add_department"
  | "show_tasks"
  | "export_data"
  // Unknown
  | "unknown";

export type ExecutionState =
  | "idle"
  | "parsing"
  | "parsed"
  | "confirming"
  | "executing"
  | "success"
  | "error"
  | "partial_success";

export type VoiceState =
  | "inactive"
  | "listening"
  | "processing"
  | "error";

export interface ParsedEntity {
  id: string;
  type: EntityType;
  value: string;
  rawValue: string;
  confidence: number; // 0-100
  isVerified: boolean;
  alternatives?: EntityOption[];
  metadata?: Record<string, unknown>;
}

export interface EntityOption {
  id: string;
  label: string;
  value: string;
  sublabel?: string;
  metadata?: Record<string, unknown>;
}

export interface ParsedIntent {
  intent: IntentType;
  confidence: number;
  entities: ParsedEntity[];
  missingRequired: EntityType[];
  suggestions?: string[];
}

export interface MultiStepOperation {
  id: string;
  title: string;
  steps: OperationStep[];
  currentStepIndex: number;
  totalSteps: number;
  overallProgress: number; // 0-100
}

export interface OperationStep {
  id: string;
  title: string;
  description?: string;
  status: "pending" | "in_progress" | "completed" | "error" | "skipped";
  progress?: number; // For steps with sub-progress
  result?: {
    success: boolean;
    message: string;
    data?: unknown;
  };
  previewData?: unknown;
  canRetry?: boolean;
}

export interface ExecutionResult {
  success: boolean;
  message: string;
  data?: unknown;
  actions?: SuggestedAction[];
}

export interface SuggestedAction {
  id: string;
  label: string;
  action: string;
  isPrimary?: boolean;
}

export interface QuickAction {
  id: string;
  label: string;
  icon: string;
  command: string;
  contextRequired?: boolean;
}

export interface RecentCommand {
  id: string;
  input: string;
  intent: IntentType;
  timestamp: Date;
  success: boolean;
}

export interface CopilotContext {
  currentPage: string;
  currentPatient?: {
    id: string;
    name: string;
    mrn?: string;
    phone?: string;
  };
  currentPractitioner?: {
    id: string;
    name: string;
    specialty?: string;
  };
  selectedEntities?: Record<string, unknown>;
}

export interface CopilotState {
  // Command bar state
  isOpen: boolean;
  inputValue: string;

  // Voice input state
  voiceState: VoiceState;
  voiceTranscript: string;

  // Parsing state
  executionState: ExecutionState;
  parsedIntent: ParsedIntent | null;
  parseError: string | null;

  // Multi-step operation state
  multiStepOperation: MultiStepOperation | null;

  // Execution result
  executionResult: ExecutionResult | null;

  // Context
  context: CopilotContext;

  // History
  recentCommands: RecentCommand[];

  // Quick actions
  quickActions: QuickAction[];

  // UI state
  selectedSuggestionIndex: number;
  isShowingEntityCorrection: boolean;
  correctionEntityId: string | null;
}

export interface CopilotActions {
  // Command bar actions
  openCommandBar: () => void;
  closeCommandBar: () => void;
  toggleCommandBar: () => void;
  setInputValue: (value: string) => void;
  clearInput: () => void;

  // Voice actions
  startVoiceInput: () => void;
  stopVoiceInput: () => void;
  setVoiceTranscript: (transcript: string) => void;
  setVoiceState: (state: VoiceState) => void;

  // Parsing actions
  parseInput: (input: string) => Promise<void>;
  setParsedIntent: (intent: ParsedIntent | null) => void;
  setParseError: (error: string | null) => void;
  setExecutionState: (state: ExecutionState) => void;

  // Entity actions
  updateEntity: (entityId: string, updates: Partial<ParsedEntity>) => void;
  verifyEntity: (entityId: string) => void;
  selectEntityAlternative: (entityId: string, alternativeId: string) => void;
  showEntityCorrection: (entityId: string) => void;
  hideEntityCorrection: () => void;

  // Multi-step operations
  setMultiStepOperation: (operation: MultiStepOperation | null) => void;
  updateStepStatus: (stepId: string, status: OperationStep["status"], result?: OperationStep["result"]) => void;
  advanceStep: () => void;
  cancelOperation: () => void;

  // Execution actions
  executeCommand: () => Promise<void>;
  executeWithoutConfirmation: () => Promise<void>;
  setExecutionResult: (result: ExecutionResult | null) => void;
  retryExecution: () => Promise<void>;

  // Context actions
  setContext: (context: Partial<CopilotContext>) => void;
  setCurrentPatient: (patient: CopilotContext["currentPatient"]) => void;
  setCurrentPractitioner: (practitioner: CopilotContext["currentPractitioner"]) => void;
  clearContext: () => void;

  // History actions
  addToHistory: (command: Omit<RecentCommand, "id" | "timestamp">) => void;
  clearHistory: () => void;

  // Navigation actions
  navigateSuggestions: (direction: "up" | "down") => void;
  selectSuggestion: () => void;
  resetSuggestionIndex: () => void;

  // Quick actions
  setQuickActions: (actions: QuickAction[]) => void;
  executeQuickAction: (actionId: string) => void;

  // Reset
  reset: () => void;
}

// ============================================================================
// Default Values
// ============================================================================

const defaultQuickActions: QuickAction[] = [
  { id: "book_appointment", label: "Book Appointment", icon: "📅", command: "Book appointment" },
  { id: "find_patient", label: "Find Patient", icon: "👤", command: "Find patient" },
  { id: "view_schedule", label: "View Schedule", icon: "📊", command: "Show today's schedule" },
  { id: "send_message", label: "Send Message", icon: "💬", command: "Send WhatsApp to", contextRequired: true },
];

const contextualQuickActions: QuickAction[] = [
  { id: "book_for_patient", label: "Book Appointment", icon: "📅", command: "Book appointment for this patient", contextRequired: true },
  { id: "prescribe", label: "Prescribe", icon: "💊", command: "Prescribe medication", contextRequired: true },
  { id: "add_note", label: "Add Note", icon: "📝", command: "Add clinical note", contextRequired: true },
  { id: "send_message_patient", label: "Send Message", icon: "📤", command: "Send WhatsApp message", contextRequired: true },
];

const initialState: CopilotState = {
  isOpen: false,
  inputValue: "",
  voiceState: "inactive",
  voiceTranscript: "",
  executionState: "idle",
  parsedIntent: null,
  parseError: null,
  multiStepOperation: null,
  executionResult: null,
  context: {
    currentPage: "/",
  },
  recentCommands: [],
  quickActions: defaultQuickActions,
  selectedSuggestionIndex: -1,
  isShowingEntityCorrection: false,
  correctionEntityId: null,
};

// ============================================================================
// Store
// ============================================================================

export const useCopilotStore = create<CopilotState & CopilotActions>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      ...initialState,

      // ========================================================================
      // Command Bar Actions
      // ========================================================================

      openCommandBar: () => {
        set({ isOpen: true, executionState: "idle", parseError: null });
      },

      closeCommandBar: () => {
        const { executionState } = get();
        // Don't close if executing
        if (executionState === "executing") return;

        set({
          isOpen: false,
          inputValue: "",
          voiceTranscript: "",
          voiceState: "inactive",
          parsedIntent: null,
          parseError: null,
          executionResult: null,
          multiStepOperation: null,
          selectedSuggestionIndex: -1,
          isShowingEntityCorrection: false,
          correctionEntityId: null,
          executionState: "idle",
        });
      },

      toggleCommandBar: () => {
        const { isOpen, openCommandBar, closeCommandBar } = get();
        if (isOpen) {
          closeCommandBar();
        } else {
          openCommandBar();
        }
      },

      setInputValue: (value: string) => {
        set({
          inputValue: value,
          // Reset parsing state when input changes
          executionState: value.length > 0 ? "parsing" : "idle",
          parsedIntent: null,
          parseError: null,
        });
      },

      clearInput: () => {
        set({
          inputValue: "",
          voiceTranscript: "",
          parsedIntent: null,
          parseError: null,
          executionState: "idle",
        });
      },

      // ========================================================================
      // Voice Actions
      // ========================================================================

      startVoiceInput: () => {
        set({ voiceState: "listening", voiceTranscript: "" });
      },

      stopVoiceInput: () => {
        const { voiceTranscript, setInputValue } = get();
        if (voiceTranscript) {
          setInputValue(voiceTranscript);
        }
        set({ voiceState: "processing" });
      },

      setVoiceTranscript: (transcript: string) => {
        set({ voiceTranscript: transcript });
      },

      setVoiceState: (state: VoiceState) => {
        set({ voiceState: state });
      },

      // ========================================================================
      // Parsing Actions
      // ========================================================================

      parseInput: async (input: string) => {
        set({ executionState: "parsing", parseError: null });

        try {
          // In production, this would call the AI parsing API
          // For now, we'll simulate parsing with a delay
          await new Promise((resolve) => setTimeout(resolve, 500));

          // Mock parsed intent - in production, this comes from AI
          const mockParsedIntent: ParsedIntent = simulateAIParsing(input);

          set({
            parsedIntent: mockParsedIntent,
            executionState: "parsed",
          });
        } catch (error) {
          set({
            parseError: error instanceof Error ? error.message : "Failed to parse command",
            executionState: "error",
          });
        }
      },

      setParsedIntent: (intent: ParsedIntent | null) => {
        set({ parsedIntent: intent });
      },

      setParseError: (error: string | null) => {
        set({ parseError: error });
      },

      setExecutionState: (state: ExecutionState) => {
        set({ executionState: state });
      },

      // ========================================================================
      // Entity Actions
      // ========================================================================

      updateEntity: (entityId: string, updates: Partial<ParsedEntity>) => {
        const { parsedIntent } = get();
        if (!parsedIntent) return;

        const updatedEntities = parsedIntent.entities.map((entity) =>
          entity.id === entityId ? { ...entity, ...updates } : entity
        );

        set({
          parsedIntent: {
            ...parsedIntent,
            entities: updatedEntities,
          },
        });
      },

      verifyEntity: (entityId: string) => {
        const { updateEntity } = get();
        updateEntity(entityId, { isVerified: true });
      },

      selectEntityAlternative: (entityId: string, alternativeId: string) => {
        const { parsedIntent, updateEntity, hideEntityCorrection } = get();
        if (!parsedIntent) return;

        const entity = parsedIntent.entities.find((e) => e.id === entityId);
        if (!entity?.alternatives) return;

        const alternative = entity.alternatives.find((a) => a.id === alternativeId);
        if (!alternative) return;

        updateEntity(entityId, {
          value: alternative.value,
          rawValue: alternative.label,
          isVerified: true,
          confidence: 100,
        });

        hideEntityCorrection();
      },

      showEntityCorrection: (entityId: string) => {
        set({
          isShowingEntityCorrection: true,
          correctionEntityId: entityId,
        });
      },

      hideEntityCorrection: () => {
        set({
          isShowingEntityCorrection: false,
          correctionEntityId: null,
        });
      },

      // ========================================================================
      // Multi-Step Operations
      // ========================================================================

      setMultiStepOperation: (operation: MultiStepOperation | null) => {
        set({ multiStepOperation: operation });
      },

      updateStepStatus: (stepId: string, status: OperationStep["status"], result?: OperationStep["result"]) => {
        const { multiStepOperation } = get();
        if (!multiStepOperation) return;

        const updatedSteps = multiStepOperation.steps.map((step) =>
          step.id === stepId ? { ...step, status, result } : step
        );

        // Calculate overall progress
        const completedSteps = updatedSteps.filter((s) => s.status === "completed").length;
        const overallProgress = Math.round((completedSteps / multiStepOperation.totalSteps) * 100);

        set({
          multiStepOperation: {
            ...multiStepOperation,
            steps: updatedSteps,
            overallProgress,
          },
        });
      },

      advanceStep: () => {
        const { multiStepOperation } = get();
        if (!multiStepOperation) return;

        const nextIndex = multiStepOperation.currentStepIndex + 1;
        if (nextIndex >= multiStepOperation.totalSteps) return;

        set({
          multiStepOperation: {
            ...multiStepOperation,
            currentStepIndex: nextIndex,
          },
        });
      },

      cancelOperation: () => {
        set({
          multiStepOperation: null,
          executionState: "idle",
        });
      },

      // ========================================================================
      // Execution Actions
      // ========================================================================

      executeCommand: async () => {
        const { parsedIntent, context, addToHistory, inputValue } = get();
        if (!parsedIntent) return;

        set({ executionState: "executing" });

        try {
          // In production, this would call the appropriate API based on intent
          await new Promise((resolve) => setTimeout(resolve, 1000));

          const result: ExecutionResult = {
            success: true,
            message: `Successfully completed: ${parsedIntent.intent.replace(/_/g, " ")}`,
            actions: [
              { id: "view", label: "View Details", action: "view" },
              { id: "another", label: "Do Another", action: "reset" },
            ],
          };

          set({
            executionState: "success",
            executionResult: result,
          });

          addToHistory({
            input: inputValue,
            intent: parsedIntent.intent,
            success: true,
          });
        } catch (error) {
          const errorResult: ExecutionResult = {
            success: false,
            message: error instanceof Error ? error.message : "Failed to execute command",
          };

          set({
            executionState: "error",
            executionResult: errorResult,
          });

          addToHistory({
            input: inputValue,
            intent: parsedIntent.intent,
            success: false,
          });
        }
      },

      executeWithoutConfirmation: async () => {
        const { parseInput, inputValue, executeCommand } = get();
        await parseInput(inputValue);
        await executeCommand();
      },

      setExecutionResult: (result: ExecutionResult | null) => {
        set({ executionResult: result });
      },

      retryExecution: async () => {
        const { executeCommand } = get();
        set({ executionState: "idle", executionResult: null });
        await executeCommand();
      },

      // ========================================================================
      // Context Actions
      // ========================================================================

      setContext: (context: Partial<CopilotContext>) => {
        const { context: currentContext } = get();
        const newContext = { ...currentContext, ...context };

        // Update quick actions based on context
        const hasPatientContext = !!newContext.currentPatient;
        const quickActions = hasPatientContext
          ? [...contextualQuickActions, ...defaultQuickActions]
          : defaultQuickActions;

        set({
          context: newContext,
          quickActions,
        });
      },

      setCurrentPatient: (patient: CopilotContext["currentPatient"]) => {
        const { setContext } = get();
        setContext({ currentPatient: patient });
      },

      setCurrentPractitioner: (practitioner: CopilotContext["currentPractitioner"]) => {
        const { setContext } = get();
        setContext({ currentPractitioner: practitioner });
      },

      clearContext: () => {
        set({
          context: { currentPage: "/" },
          quickActions: defaultQuickActions,
        });
      },

      // ========================================================================
      // History Actions
      // ========================================================================

      addToHistory: (command: Omit<RecentCommand, "id" | "timestamp">) => {
        const { recentCommands } = get();
        const newCommand: RecentCommand = {
          ...command,
          id: `cmd-${Date.now()}`,
          timestamp: new Date(),
        };

        // Keep only the last 10 commands
        const updatedHistory = [newCommand, ...recentCommands].slice(0, 10);
        set({ recentCommands: updatedHistory });
      },

      clearHistory: () => {
        set({ recentCommands: [] });
      },

      // ========================================================================
      // Navigation Actions
      // ========================================================================

      navigateSuggestions: (direction: "up" | "down") => {
        const { selectedSuggestionIndex, quickActions, recentCommands } = get();
        const totalItems = quickActions.length + recentCommands.length;

        if (totalItems === 0) return;

        let newIndex = selectedSuggestionIndex;
        if (direction === "down") {
          newIndex = selectedSuggestionIndex >= totalItems - 1 ? 0 : selectedSuggestionIndex + 1;
        } else {
          newIndex = selectedSuggestionIndex <= 0 ? totalItems - 1 : selectedSuggestionIndex - 1;
        }

        set({ selectedSuggestionIndex: newIndex });
      },

      selectSuggestion: () => {
        const { selectedSuggestionIndex, quickActions, recentCommands, setInputValue } = get();

        if (selectedSuggestionIndex < 0) return;

        if (selectedSuggestionIndex < quickActions.length) {
          const action = quickActions[selectedSuggestionIndex];
          setInputValue(action.command);
        } else {
          const commandIndex = selectedSuggestionIndex - quickActions.length;
          const command = recentCommands[commandIndex];
          if (command) {
            setInputValue(command.input);
          }
        }

        set({ selectedSuggestionIndex: -1 });
      },

      resetSuggestionIndex: () => {
        set({ selectedSuggestionIndex: -1 });
      },

      // ========================================================================
      // Quick Actions
      // ========================================================================

      setQuickActions: (actions: QuickAction[]) => {
        set({ quickActions: actions });
      },

      executeQuickAction: (actionId: string) => {
        const { quickActions, setInputValue } = get();
        const action = quickActions.find((a) => a.id === actionId);
        if (action) {
          setInputValue(action.command);
        }
      },

      // ========================================================================
      // Reset
      // ========================================================================

      reset: () => {
        set(initialState);
      },
    })),
    { name: "copilot-store" }
  )
);

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Simulate AI parsing - in production, this would be an API call
 */
function simulateAIParsing(input: string): ParsedIntent {
  const lowerInput = input.toLowerCase();

  // Detect intent based on keywords
  let intent: IntentType = "unknown";
  const entities: ParsedEntity[] = [];
  const missingRequired: EntityType[] = [];

  // Appointment booking
  if (lowerInput.includes("book") && (lowerInput.includes("appointment") || lowerInput.includes("slot"))) {
    intent = "book_appointment";

    // Extract time
    const timeMatch = lowerInput.match(/(\d{1,2}(?::\d{2})?\s*(?:am|pm))/i);
    if (timeMatch) {
      entities.push({
        id: `entity-${Date.now()}-time`,
        type: "time",
        value: timeMatch[1],
        rawValue: timeMatch[1],
        confidence: 95,
        isVerified: false,
      });
    } else {
      missingRequired.push("time");
    }

    // Extract patient phone
    const phoneMatch = lowerInput.match(/(\d{10})/);
    if (phoneMatch) {
      entities.push({
        id: `entity-${Date.now()}-patient`,
        type: "patient",
        value: phoneMatch[1],
        rawValue: phoneMatch[1],
        confidence: 88,
        isVerified: false,
        alternatives: [
          { id: "alt1", label: "Rajesh Kumar", value: "patient-123", sublabel: "+91 " + phoneMatch[1] },
          { id: "alt2", label: "Create New Patient", value: "new", sublabel: "Register new patient" },
        ],
      });
    } else {
      missingRequired.push("patient");
    }

    // Extract doctor
    const drMatch = lowerInput.match(/(?:dr\.?|doctor)\s+(\w+(?:\s+\w+)?)/i);
    if (drMatch) {
      entities.push({
        id: `entity-${Date.now()}-practitioner`,
        type: "practitioner",
        value: drMatch[1],
        rawValue: `Dr. ${drMatch[1]}`,
        confidence: 92,
        isVerified: false,
        alternatives: [
          { id: "dr1", label: `Dr. ${drMatch[1]}`, value: "prac-123", sublabel: "Cardiology" },
        ],
      });
    } else {
      missingRequired.push("practitioner");
    }
  }

  // Find patient
  else if (lowerInput.includes("find") && lowerInput.includes("patient")) {
    intent = "find_patient";

    const nameOrPhone = lowerInput.replace(/find\s+patient\s*/i, "").trim();
    if (nameOrPhone) {
      entities.push({
        id: `entity-${Date.now()}-search`,
        type: /^\d+$/.test(nameOrPhone) ? "phone" : "patient",
        value: nameOrPhone,
        rawValue: nameOrPhone,
        confidence: 90,
        isVerified: false,
      });
    }
  }

  // View schedule
  else if (lowerInput.includes("schedule") || lowerInput.includes("appointments")) {
    intent = "view_schedule";

    // Extract date/time reference
    if (lowerInput.includes("today")) {
      entities.push({
        id: `entity-${Date.now()}-date`,
        type: "date",
        value: "today",
        rawValue: "today",
        confidence: 99,
        isVerified: true,
      });
    } else if (lowerInput.includes("tomorrow")) {
      entities.push({
        id: `entity-${Date.now()}-date`,
        type: "date",
        value: "tomorrow",
        rawValue: "tomorrow",
        confidence: 99,
        isVerified: true,
      });
    }

    // Extract doctor
    const drMatch = lowerInput.match(/(?:dr\.?|doctor)\s+(\w+)/i);
    if (drMatch) {
      entities.push({
        id: `entity-${Date.now()}-practitioner`,
        type: "practitioner",
        value: drMatch[1],
        rawValue: `Dr. ${drMatch[1]}`,
        confidence: 92,
        isVerified: false,
      });
    }
  }

  // Send WhatsApp
  else if (lowerInput.includes("whatsapp") || lowerInput.includes("send message")) {
    intent = "send_whatsapp";

    const phoneMatch = lowerInput.match(/(\d{10})/);
    if (phoneMatch) {
      entities.push({
        id: `entity-${Date.now()}-patient`,
        type: "patient",
        value: phoneMatch[1],
        rawValue: phoneMatch[1],
        confidence: 90,
        isVerified: false,
      });
    } else {
      missingRequired.push("patient");
    }
  }

  // Prescribe medication
  else if (lowerInput.includes("prescribe")) {
    intent = "prescribe_medication";

    // Extract medication name (simple extraction)
    const words = lowerInput.split(/\s+/);
    const prescribeIndex = words.findIndex(w => w === "prescribe");
    if (prescribeIndex >= 0 && prescribeIndex < words.length - 1) {
      const medication = words.slice(prescribeIndex + 1).join(" ");
      entities.push({
        id: `entity-${Date.now()}-medication`,
        type: "medication",
        value: medication,
        rawValue: medication,
        confidence: 75,
        isVerified: false,
      });
    }

    missingRequired.push("patient");
  }

  // Add slot
  else if (lowerInput.includes("add") && lowerInput.includes("slot")) {
    intent = "add_slot";

    // Extract time range
    const timeRangeMatch = lowerInput.match(/(\d{1,2}(?::\d{2})?\s*(?:am|pm))\s*(?:to|-)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm))/i);
    if (timeRangeMatch) {
      entities.push({
        id: `entity-${Date.now()}-time`,
        type: "time",
        value: `${timeRangeMatch[1]} - ${timeRangeMatch[2]}`,
        rawValue: `${timeRangeMatch[1]} to ${timeRangeMatch[2]}`,
        confidence: 95,
        isVerified: false,
      });
    } else {
      missingRequired.push("time");
    }

    // Extract doctor
    const drMatch = lowerInput.match(/(?:dr\.?|doctor)\s+(\w+(?:\s+\w+)?)/i);
    if (drMatch) {
      entities.push({
        id: `entity-${Date.now()}-practitioner`,
        type: "practitioner",
        value: drMatch[1],
        rawValue: `Dr. ${drMatch[1]}`,
        confidence: 90,
        isVerified: false,
      });
    } else {
      missingRequired.push("practitioner");
    }
  }

  return {
    intent,
    confidence: intent === "unknown" ? 20 : 85,
    entities,
    missingRequired,
    suggestions: intent === "unknown"
      ? ["Book an appointment", "Find a patient", "View schedule"]
      : undefined,
  };
}

// ============================================================================
// Selectors
// ============================================================================

export const selectIsCommandBarOpen = (state: CopilotState) => state.isOpen;
export const selectInputValue = (state: CopilotState) => state.inputValue;
export const selectVoiceState = (state: CopilotState) => state.voiceState;
export const selectExecutionState = (state: CopilotState) => state.executionState;
export const selectParsedIntent = (state: CopilotState) => state.parsedIntent;
export const selectContext = (state: CopilotState) => state.context;
export const selectRecentCommands = (state: CopilotState) => state.recentCommands;
export const selectQuickActions = (state: CopilotState) => state.quickActions;
export const selectMultiStepOperation = (state: CopilotState) => state.multiStepOperation;

export const selectHasPatientContext = (state: CopilotState) => !!state.context.currentPatient;
export const selectCanExecute = (state: CopilotState) =>
  state.parsedIntent !== null &&
  state.parsedIntent.missingRequired.length === 0 &&
  state.executionState === "parsed";

export const selectAllEntitiesVerified = (state: CopilotState) =>
  state.parsedIntent?.entities.every((e) => e.isVerified || e.confidence >= 90) ?? false;

export const selectLowConfidenceEntities = (state: CopilotState) =>
  state.parsedIntent?.entities.filter((e) => e.confidence < 80 && !e.isVerified) ?? [];
