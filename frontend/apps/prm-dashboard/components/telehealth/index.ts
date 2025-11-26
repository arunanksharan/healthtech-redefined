// Telehealth Components - Barrel Export
// EPIC-UX-008: Telehealth Experience

// Device Check
export {
  DeviceCheck,
  ProviderPreCallCheck,
  DeviceCheckSkeleton,
} from "./device-check";

// Waiting Room
export {
  WaitingRoom,
  ProviderWaitingView,
  WaitingRoomSkeleton,
} from "./waiting-room";

// Video Call
export {
  VideoCall,
  PatientVideoCall,
  VideoCallSkeleton,
} from "./video-call";

// Session Summary
export {
  ProviderSessionSummary,
  PatientFeedbackForm,
  VisitCompleteDialog,
  SessionSummarySkeleton,
} from "./session-summary";

// Telehealth Dashboard
export {
  TelehealthDashboard,
  TelehealthDashboardSkeleton,
} from "./telehealth-dashboard";

// Re-export types from store for convenience
export type {
  DeviceType,
  DeviceInfo,
  DeviceStatus,
  SessionStatus,
  NetworkQuality,
  ParticipantRole,
  RecordingStatus,
  TelehealthSession,
  WaitingRoomPatient,
  Participant,
  ChatMessage,
  TranscriptionEntry,
  AISuggestion,
  SessionSummary,
  PatientFeedback,
  Recording,
} from "@/lib/store/telehealth-store";
