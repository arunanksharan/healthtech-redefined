// Collaboration Store - Provider Collaboration Hub
// EPIC-UX-010: Real-Time Care Team Communication

import { create } from "zustand";
import { devtools, subscribeWithSelector } from "zustand/middleware";

// =============================================================================
// TYPE DEFINITIONS
// =============================================================================

export type PresenceStatus = "online" | "busy" | "away" | "offline";
export type MessageType = "text" | "file" | "patient_link" | "system";
export type ConsultPriority = "routine" | "urgent" | "emergent";
export type ConsultType = "opinion" | "co_management" | "transfer";
export type ConsultStatus = "pending" | "accepted" | "in_progress" | "completed" | "declined";
export type HandoffStatus = "draft" | "pending_acknowledgment" | "acknowledged" | "completed";

export interface User {
  id: string;
  name: string;
  role: string;
  department: string;
  avatar?: string;
  presence: PresenceStatus;
  lastSeen?: string;
  phone?: string;
  email?: string;
  specialty?: string;
}

export interface PatientContext {
  id: string;
  mrn: string;
  name: string;
  age: number;
  gender: string;
  room?: string;
  primaryDiagnosis?: string;
}

export interface Attachment {
  id: string;
  name: string;
  type: string;
  size: number;
  url: string;
  uploadedAt: string;
}

export interface Message {
  id: string;
  conversationId: string;
  senderId: string;
  senderName: string;
  type: MessageType;
  content: string;
  attachments?: Attachment[];
  patientContext?: PatientContext;
  timestamp: string;
  readBy: string[];
  deliveredAt?: string;
  readAt?: string;
}

export interface Conversation {
  id: string;
  type: "direct" | "group" | "department";
  name?: string;
  participants: User[];
  lastMessage?: Message;
  unreadCount: number;
  patientContext?: PatientContext;
  createdAt: string;
  updatedAt: string;
  isPinned?: boolean;
  isMuted?: boolean;
}

export interface ConsultationRequest {
  id: string;
  requesterId: string;
  requesterName: string;
  requesterDepartment: string;
  consultantId?: string;
  consultantName?: string;
  specialty: string;
  patient: PatientContext;
  priority: ConsultPriority;
  consultType: ConsultType;
  reason: string;
  clinicalQuestion: string;
  attachments: Attachment[];
  status: ConsultStatus;
  createdAt: string;
  responseDeadline: string;
  response?: {
    text: string;
    recommendations: string[];
    respondedAt: string;
  };
  notes: Array<{ userId: string; text: string; timestamp: string }>;
}

export interface SBARHandoff {
  id: string;
  fromUserId: string;
  fromUserName: string;
  toUserId: string;
  toUserName: string;
  ward: string;
  shiftType: "night_to_day" | "day_to_night" | "custom";
  patients: SBARPatient[];
  status: HandoffStatus;
  createdAt: string;
  acknowledgedAt?: string;
  notes?: string;
}

export interface SBARPatient {
  id: string;
  patientId: string;
  patientName: string;
  room: string;
  situation: string;
  background: string;
  assessment: string;
  recommendation: string;
  alerts: string[];
  tasks: Array<{ task: string; priority: "high" | "medium" | "low"; completed: boolean }>;
}

export interface OnCallSlot {
  id: string;
  userId: string;
  userName: string;
  phone: string;
  department: string;
  date: string;
  shiftType: "day" | "night" | "24hr";
  startTime: string;
  endTime: string;
  isBackup?: boolean;
}

export interface SwapRequest {
  id: string;
  requesterId: string;
  requesterName: string;
  originalSlotId: string;
  targetUserId?: string;
  targetSlotId?: string;
  reason: string;
  status: "pending" | "approved" | "declined";
  createdAt: string;
}

// =============================================================================
// STORE STATE
// =============================================================================

interface CollaborationState {
  // Current user
  currentUser: User | null;

  // Conversations
  conversations: Conversation[];
  activeConversationId: string | null;
  messages: Record<string, Message[]>;
  isLoadingConversations: boolean;
  isLoadingMessages: boolean;

  // Consultations
  consultations: ConsultationRequest[];
  activeConsultation: ConsultationRequest | null;
  isLoadingConsultations: boolean;
  isSubmittingConsultation: boolean;

  // Handoffs
  handoffs: SBARHandoff[];
  activeHandoff: SBARHandoff | null;
  handoffDraft: Partial<SBARHandoff> | null;
  isLoadingHandoffs: boolean;

  // On-Call
  onCallSchedule: OnCallSlot[];
  currentOnCall: Record<string, OnCallSlot>;
  swapRequests: SwapRequest[];
  isLoadingOnCall: boolean;

  // Online users
  onlineUsers: User[];

  // Actions
  setCurrentUser: (user: User) => void;

  // Conversation actions
  fetchConversations: () => Promise<void>;
  selectConversation: (id: string) => void;
  fetchMessages: (conversationId: string) => Promise<void>;
  sendMessage: (conversationId: string, message: Partial<Message>) => Promise<void>;
  createConversation: (participants: string[], patientId?: string) => Promise<string>;
  markAsRead: (conversationId: string) => void;

  // Consultation actions
  fetchConsultations: () => Promise<void>;
  createConsultation: (request: Partial<ConsultationRequest>) => Promise<void>;
  acceptConsultation: (id: string) => Promise<void>;
  respondToConsultation: (id: string, response: string, recommendations: string[]) => Promise<void>;
  declineConsultation: (id: string, reason: string) => Promise<void>;

  // Handoff actions
  fetchHandoffs: () => Promise<void>;
  createHandoff: (handoff: Partial<SBARHandoff>) => Promise<void>;
  updateHandoffDraft: (draft: Partial<SBARHandoff>) => void;
  acknowledgeHandoff: (id: string) => Promise<void>;
  completeHandoff: (id: string) => Promise<void>;

  // On-Call actions
  fetchOnCallSchedule: (department: string, startDate: string, endDate: string) => Promise<void>;
  createSwapRequest: (request: Partial<SwapRequest>) => Promise<void>;
  approveSwapRequest: (id: string) => Promise<void>;
  declineSwapRequest: (id: string) => Promise<void>;

  // Presence actions
  updatePresence: (status: PresenceStatus) => void;
  fetchOnlineUsers: () => Promise<void>;
}

// =============================================================================
// MOCK DATA GENERATORS
// =============================================================================

const mockUsers: User[] = [
  { id: "u1", name: "Dr. Rohit Sharma", role: "Cardiologist", department: "Cardiology", presence: "online", phone: "+91 98765 43210", specialty: "Interventional Cardiology" },
  { id: "u2", name: "Dr. Priya Mehta", role: "Endocrinologist", department: "Endocrinology", presence: "online", phone: "+91 98765 43211", specialty: "Diabetes Management" },
  { id: "u3", name: "Dr. Arun Gupta", role: "Nephrologist", department: "Nephrology", presence: "busy", phone: "+91 98765 43212", specialty: "Dialysis" },
  { id: "u4", name: "Nurse Sarah", role: "RN", department: "Cardiology", presence: "online", phone: "+91 98765 43213" },
  { id: "u5", name: "Nurse Mike", role: "RN", department: "Cardiology", presence: "away", phone: "+91 98765 43214" },
  { id: "u6", name: "Dr. Kavita Patel", role: "Pulmonologist", department: "Pulmonology", presence: "offline", phone: "+91 98765 43215", specialty: "Critical Care" },
];

const mockPatient: PatientContext = {
  id: "p1",
  mrn: "MRN-12345",
  name: "John Doe",
  age: 59,
  gender: "Male",
  room: "301",
  primaryDiagnosis: "CHF Exacerbation",
};

const generateMockConversations = (): Conversation[] => [
  {
    id: "conv1",
    type: "direct",
    participants: [mockUsers[0], mockUsers[1]],
    lastMessage: { id: "m1", conversationId: "conv1", senderId: "u2", senderName: "Dr. Priya Mehta", type: "text", content: "Sure, I can see him next week. Can you send me his recent labs and A1C?", timestamp: new Date(Date.now() - 2 * 60000).toISOString(), readBy: ["u1", "u2"] },
    unreadCount: 0,
    patientContext: mockPatient,
    createdAt: new Date(Date.now() - 86400000).toISOString(),
    updatedAt: new Date(Date.now() - 2 * 60000).toISOString(),
  },
  {
    id: "conv2",
    type: "direct",
    participants: [mockUsers[0], mockUsers[2]],
    lastMessage: { id: "m2", conversationId: "conv2", senderId: "u3", senderName: "Dr. Arun Gupta", type: "text", content: "About Mr. Wilson's creatinine levels...", timestamp: new Date(Date.now() - 3600000).toISOString(), readBy: ["u3"] },
    unreadCount: 1,
    createdAt: new Date(Date.now() - 172800000).toISOString(),
    updatedAt: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    id: "conv3",
    type: "department",
    name: "Cardiology Team",
    participants: [mockUsers[0], mockUsers[3], mockUsers[4]],
    lastMessage: { id: "m3", conversationId: "conv3", senderId: "u4", senderName: "Nurse Sarah", type: "text", content: "Code Blue Room 302 - Responded", timestamp: new Date(Date.now() - 86400000).toISOString(), readBy: ["u4", "u5"] },
    unreadCount: 0,
    createdAt: new Date(Date.now() - 604800000).toISOString(),
    updatedAt: new Date(Date.now() - 86400000).toISOString(),
  },
];

const generateMockMessages = (conversationId: string): Message[] => {
  if (conversationId === "conv1") {
    return [
      { id: "m1a", conversationId: "conv1", senderId: "u1", senderName: "Dr. Rohit Sharma", type: "patient_link", content: "Re: John Doe (MRN: 12345)", patientContext: mockPatient, timestamp: new Date(Date.now() - 10 * 60000).toISOString(), readBy: ["u1", "u2"] },
      { id: "m1b", conversationId: "conv1", senderId: "u1", senderName: "Dr. Rohit Sharma", type: "text", content: "Hi Priya, I have a patient with T2DM who's not responding well to Metformin. Would you be able to see him for a consult?", timestamp: new Date(Date.now() - 8 * 60000).toISOString(), readBy: ["u1", "u2"] },
      { id: "m1c", conversationId: "conv1", senderId: "u2", senderName: "Dr. Priya Mehta", type: "text", content: "Sure, I can see him next week. Can you send me his recent labs and A1C?", timestamp: new Date(Date.now() - 2 * 60000).toISOString(), readBy: ["u1", "u2"] },
    ];
  }
  return [];
};

const generateMockConsultations = (): ConsultationRequest[] => [
  {
    id: "consult1",
    requesterId: "u1",
    requesterName: "Dr. Rohit Sharma",
    requesterDepartment: "Cardiology",
    consultantId: "u2",
    consultantName: "Dr. Priya Mehta",
    specialty: "Endocrinology",
    patient: mockPatient,
    priority: "urgent",
    consultType: "opinion",
    reason: "Patient with T2DM not achieving glycemic control on Metformin 1000mg BID. A1C remains 7.2% (target <7.0%). Experiencing GI side effects. Requesting evaluation for alternative therapy.",
    clinicalQuestion: "Should we switch to SGLT2 inhibitor or add to current regimen?",
    attachments: [{ id: "att1", name: "Recent A1C Results.pdf", type: "application/pdf", size: 245000, url: "/files/a1c.pdf", uploadedAt: new Date().toISOString() }],
    status: "pending",
    createdAt: new Date(Date.now() - 3600000).toISOString(),
    responseDeadline: new Date(Date.now() + 86400000).toISOString(),
    notes: [],
  },
  {
    id: "consult2",
    requesterId: "u3",
    requesterName: "Dr. Arun Gupta",
    requesterDepartment: "Nephrology",
    specialty: "Cardiology",
    patient: { ...mockPatient, id: "p2", name: "Mary Johnson", mrn: "MRN-67890", room: "205" },
    priority: "routine",
    consultType: "co_management",
    reason: "CKD patient with new onset atrial fibrillation. Need cardiology input on anticoagulation.",
    clinicalQuestion: "Is anticoagulation safe given GFR of 35?",
    attachments: [],
    status: "completed",
    createdAt: new Date(Date.now() - 172800000).toISOString(),
    responseDeadline: new Date(Date.now() - 86400000).toISOString(),
    response: { text: "Recommend apixaban 2.5mg BID given renal function. Monitor for bleeding.", recommendations: ["Start Apixaban 2.5mg BID", "Weekly CBC for 4 weeks", "Recheck renal function in 1 week"], respondedAt: new Date(Date.now() - 100000000).toISOString() },
    notes: [],
  },
];

const generateMockHandoffs = (): SBARHandoff[] => [
  {
    id: "handoff1",
    fromUserId: "u4",
    fromUserName: "Nurse Sarah",
    toUserId: "u5",
    toUserName: "Nurse Mike",
    ward: "Cardiology Unit A",
    shiftType: "night_to_day",
    patients: [
      {
        id: "sp1",
        patientId: "p1",
        patientName: "John Doe",
        room: "301",
        situation: "59 y/o male admitted for CHF exacerbation. Day 3 of admission.",
        background: "History of T2DM, HTN, prior MI. On Lasix, Metoprolol, Lisinopril.",
        assessment: "Stable overnight. I/O: +500ml. Morning weight pending. Oxygen weaned to 2L NC. No chest pain or SOB.",
        recommendation: "Check morning weight - if down, may increase PO intake. AM labs pending - monitor K+ with Lasix. Possible discharge today if stable.",
        alerts: ["Fall risk (yellow band)"],
        tasks: [
          { task: "Check morning weight", priority: "high", completed: false },
          { task: "Review AM labs", priority: "high", completed: false },
          { task: "Call family for discharge planning", priority: "medium", completed: false },
        ],
      },
      {
        id: "sp2",
        patientId: "p3",
        patientName: "Jane Smith",
        room: "302",
        situation: "Post-op day 1 CABG. Stable overnight.",
        background: "68 y/o female, triple vessel disease. Uneventful surgery.",
        assessment: "Hemodynamically stable. Chest tubes draining serosanguinous. Pain controlled.",
        recommendation: "Continue current management. PT evaluation today. Remove foley if ambulating.",
        alerts: ["DVT prophylaxis"],
        tasks: [
          { task: "PT evaluation", priority: "medium", completed: false },
          { task: "Consider foley removal", priority: "low", completed: false },
        ],
      },
    ],
    status: "pending_acknowledgment",
    createdAt: new Date().toISOString(),
  },
];

const generateMockOnCallSchedule = (): OnCallSlot[] => {
  const baseDate = new Date();
  const slots: OnCallSlot[] = [];
  const providers = [
    { id: "u1", name: "Dr. Rohit Sharma", phone: "+91 98765 43210" },
    { id: "u2", name: "Dr. Priya Mehta", phone: "+91 98765 43211" },
    { id: "u6", name: "Dr. Kavita Patel", phone: "+91 98765 43215" },
  ];

  for (let i = 0; i < 7; i++) {
    const date = new Date(baseDate);
    date.setDate(date.getDate() + i);
    const dateStr = date.toISOString().split("T")[0];

    // Day shift
    slots.push({
      id: `slot-day-${i}`,
      userId: providers[i % 3].id,
      userName: providers[i % 3].name,
      phone: providers[i % 3].phone,
      department: "Cardiology",
      date: dateStr,
      shiftType: "day",
      startTime: "08:00",
      endTime: "20:00",
    });

    // Night shift
    slots.push({
      id: `slot-night-${i}`,
      userId: providers[(i + 1) % 3].id,
      userName: providers[(i + 1) % 3].name,
      phone: providers[(i + 1) % 3].phone,
      department: "Cardiology",
      date: dateStr,
      shiftType: "night",
      startTime: "20:00",
      endTime: "08:00",
    });
  }

  return slots;
};

// =============================================================================
// STORE IMPLEMENTATION
// =============================================================================

export const useCollaborationStore = create<CollaborationState>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      // Initial state
      currentUser: mockUsers[0],
      conversations: [],
      activeConversationId: null,
      messages: {},
      isLoadingConversations: false,
      isLoadingMessages: false,
      consultations: [],
      activeConsultation: null,
      isLoadingConsultations: false,
      isSubmittingConsultation: false,
      handoffs: [],
      activeHandoff: null,
      handoffDraft: null,
      isLoadingHandoffs: false,
      onCallSchedule: [],
      currentOnCall: {},
      swapRequests: [],
      isLoadingOnCall: false,
      onlineUsers: mockUsers.filter((u) => u.presence === "online" || u.presence === "busy"),

      // User actions
      setCurrentUser: (user) => set({ currentUser: user }),

      // Conversation actions
      fetchConversations: async () => {
        set({ isLoadingConversations: true });
        await new Promise((r) => setTimeout(r, 500));
        set({ conversations: generateMockConversations(), isLoadingConversations: false });
      },

      selectConversation: (id) => {
        set({ activeConversationId: id });
        get().fetchMessages(id);
      },

      fetchMessages: async (conversationId) => {
        set({ isLoadingMessages: true });
        await new Promise((r) => setTimeout(r, 300));
        const msgs = generateMockMessages(conversationId);
        set((state) => ({
          messages: { ...state.messages, [conversationId]: msgs },
          isLoadingMessages: false,
        }));
      },

      sendMessage: async (conversationId, message) => {
        const { currentUser } = get();
        if (!currentUser) return;

        const newMessage: Message = {
          id: `msg-${Date.now()}`,
          conversationId,
          senderId: currentUser.id,
          senderName: currentUser.name,
          type: message.type || "text",
          content: message.content || "",
          timestamp: new Date().toISOString(),
          readBy: [currentUser.id],
          ...message,
        };

        set((state) => ({
          messages: {
            ...state.messages,
            [conversationId]: [...(state.messages[conversationId] || []), newMessage],
          },
          conversations: state.conversations.map((c) =>
            c.id === conversationId ? { ...c, lastMessage: newMessage, updatedAt: newMessage.timestamp } : c
          ),
        }));
      },

      createConversation: async (participants, patientId) => {
        const { currentUser, onlineUsers } = get();
        if (!currentUser) return "";

        const newConv: Conversation = {
          id: `conv-${Date.now()}`,
          type: participants.length > 1 ? "group" : "direct",
          participants: [currentUser, ...onlineUsers.filter((u) => participants.includes(u.id))],
          unreadCount: 0,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };

        set((state) => ({ conversations: [newConv, ...state.conversations] }));
        return newConv.id;
      },

      markAsRead: (conversationId) => {
        set((state) => ({
          conversations: state.conversations.map((c) =>
            c.id === conversationId ? { ...c, unreadCount: 0 } : c
          ),
        }));
      },

      // Consultation actions
      fetchConsultations: async () => {
        set({ isLoadingConsultations: true });
        await new Promise((r) => setTimeout(r, 500));
        set({ consultations: generateMockConsultations(), isLoadingConsultations: false });
      },

      createConsultation: async (request) => {
        set({ isSubmittingConsultation: true });
        await new Promise((r) => setTimeout(r, 1000));

        const { currentUser } = get();
        const newConsult: ConsultationRequest = {
          id: `consult-${Date.now()}`,
          requesterId: currentUser?.id || "",
          requesterName: currentUser?.name || "",
          requesterDepartment: currentUser?.department || "",
          specialty: request.specialty || "",
          patient: request.patient || mockPatient,
          priority: request.priority || "routine",
          consultType: request.consultType || "opinion",
          reason: request.reason || "",
          clinicalQuestion: request.clinicalQuestion || "",
          attachments: request.attachments || [],
          status: "pending",
          createdAt: new Date().toISOString(),
          responseDeadline: new Date(Date.now() + (request.priority === "urgent" ? 86400000 : 172800000)).toISOString(),
          notes: [],
        };

        set((state) => ({
          consultations: [newConsult, ...state.consultations],
          isSubmittingConsultation: false,
        }));
      },

      acceptConsultation: async (id) => {
        await new Promise((r) => setTimeout(r, 500));
        const { currentUser } = get();
        set((state) => ({
          consultations: state.consultations.map((c) =>
            c.id === id
              ? { ...c, status: "in_progress", consultantId: currentUser?.id, consultantName: currentUser?.name }
              : c
          ),
        }));
      },

      respondToConsultation: async (id, response, recommendations) => {
        await new Promise((r) => setTimeout(r, 800));
        set((state) => ({
          consultations: state.consultations.map((c) =>
            c.id === id
              ? { ...c, status: "completed", response: { text: response, recommendations, respondedAt: new Date().toISOString() } }
              : c
          ),
        }));
      },

      declineConsultation: async (id, reason) => {
        await new Promise((r) => setTimeout(r, 500));
        set((state) => ({
          consultations: state.consultations.map((c) =>
            c.id === id
              ? { ...c, status: "declined", notes: [...c.notes, { userId: get().currentUser?.id || "", text: reason, timestamp: new Date().toISOString() }] }
              : c
          ),
        }));
      },

      // Handoff actions
      fetchHandoffs: async () => {
        set({ isLoadingHandoffs: true });
        await new Promise((r) => setTimeout(r, 500));
        set({ handoffs: generateMockHandoffs(), isLoadingHandoffs: false });
      },

      createHandoff: async (handoff) => {
        await new Promise((r) => setTimeout(r, 800));
        const { currentUser } = get();

        const newHandoff: SBARHandoff = {
          id: `handoff-${Date.now()}`,
          fromUserId: currentUser?.id || "",
          fromUserName: currentUser?.name || "",
          toUserId: handoff.toUserId || "",
          toUserName: handoff.toUserName || "",
          ward: handoff.ward || "",
          shiftType: handoff.shiftType || "day_to_night",
          patients: handoff.patients || [],
          status: "pending_acknowledgment",
          createdAt: new Date().toISOString(),
        };

        set((state) => ({
          handoffs: [newHandoff, ...state.handoffs],
          handoffDraft: null,
        }));
      },

      updateHandoffDraft: (draft) => {
        set((state) => ({
          handoffDraft: state.handoffDraft ? { ...state.handoffDraft, ...draft } : draft,
        }));
      },

      acknowledgeHandoff: async (id) => {
        await new Promise((r) => setTimeout(r, 500));
        set((state) => ({
          handoffs: state.handoffs.map((h) =>
            h.id === id ? { ...h, status: "acknowledged", acknowledgedAt: new Date().toISOString() } : h
          ),
        }));
      },

      completeHandoff: async (id) => {
        await new Promise((r) => setTimeout(r, 500));
        set((state) => ({
          handoffs: state.handoffs.map((h) => (h.id === id ? { ...h, status: "completed" } : h)),
        }));
      },

      // On-Call actions
      fetchOnCallSchedule: async (department, startDate, endDate) => {
        set({ isLoadingOnCall: true });
        await new Promise((r) => setTimeout(r, 500));
        const schedule = generateMockOnCallSchedule();
        const now = new Date();
        const currentSlot = schedule.find((s) => {
          const slotDate = new Date(s.date);
          return slotDate.toDateString() === now.toDateString() && ((s.shiftType === "day" && now.getHours() >= 8 && now.getHours() < 20) || (s.shiftType === "night" && (now.getHours() >= 20 || now.getHours() < 8)));
        });

        set({
          onCallSchedule: schedule,
          currentOnCall: currentSlot ? { [department]: currentSlot } : {},
          isLoadingOnCall: false,
        });
      },

      createSwapRequest: async (request) => {
        await new Promise((r) => setTimeout(r, 500));
        const { currentUser } = get();
        const newRequest: SwapRequest = {
          id: `swap-${Date.now()}`,
          requesterId: currentUser?.id || "",
          requesterName: currentUser?.name || "",
          originalSlotId: request.originalSlotId || "",
          targetUserId: request.targetUserId,
          targetSlotId: request.targetSlotId,
          reason: request.reason || "",
          status: "pending",
          createdAt: new Date().toISOString(),
        };
        set((state) => ({ swapRequests: [...state.swapRequests, newRequest] }));
      },

      approveSwapRequest: async (id) => {
        await new Promise((r) => setTimeout(r, 500));
        set((state) => ({
          swapRequests: state.swapRequests.map((r) => (r.id === id ? { ...r, status: "approved" } : r)),
        }));
      },

      declineSwapRequest: async (id) => {
        await new Promise((r) => setTimeout(r, 500));
        set((state) => ({
          swapRequests: state.swapRequests.map((r) => (r.id === id ? { ...r, status: "declined" } : r)),
        }));
      },

      // Presence actions
      updatePresence: (status) => {
        set((state) => ({
          currentUser: state.currentUser ? { ...state.currentUser, presence: status } : null,
        }));
      },

      fetchOnlineUsers: async () => {
        await new Promise((r) => setTimeout(r, 300));
        set({ onlineUsers: mockUsers.filter((u) => u.presence === "online" || u.presence === "busy") });
      },
    })),
    { name: "collaboration-store" }
  )
);

export default useCollaborationStore;
