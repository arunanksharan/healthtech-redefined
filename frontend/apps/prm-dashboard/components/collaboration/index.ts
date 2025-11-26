// Provider Collaboration Hub Components - Barrel Export
// EPIC-UX-010: Real-Time Care Team Communication

export {
  MessagingInterface,
  MessagesWidget,
} from "./messaging-interface";

export {
  ConsultationsDashboard,
  ConsultationsWidget,
  ConsultationForm,
  ConsultationCard,
  ConsultationDetail,
  NewConsultationDialog,
} from "./consultation-request";

export {
  HandoffDashboard,
  HandoffsWidget,
  CreateHandoffForm,
  HandoffCard,
  HandoffDetail,
} from "./sbar-handoff";

export {
  OnCallSchedule,
  OnCallWidget,
  CurrentOnCallBanner,
} from "./on-call-schedule";

export {
  CollaborationDashboard,
} from "./collaboration-dashboard";

// Re-export types
export type {
  User,
  PresenceStatus,
  Message,
  MessageType,
  Conversation,
  PatientContext,
  Attachment,
  ConsultationRequest,
  ConsultPriority,
  ConsultType,
  ConsultStatus,
  SBARHandoff,
  SBARPatient,
  HandoffStatus,
  OnCallSlot,
  SwapRequest,
} from "@/lib/store/collaboration-store";
