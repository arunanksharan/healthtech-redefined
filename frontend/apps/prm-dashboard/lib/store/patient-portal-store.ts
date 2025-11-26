// Patient Portal Store
// EPIC-UX-011: Patient Self-Service Portal

import { create } from "zustand";
import { devtools, subscribeWithSelector } from "zustand/middleware";

// =============================================================================
// TYPE DEFINITIONS
// =============================================================================

export interface PatientProfile {
  id: string;
  mrn: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  dateOfBirth: string;
  gender: string;
  address: {
    street: string;
    city: string;
    state: string;
    zipCode: string;
  };
  emergencyContact: {
    name: string;
    relationship: string;
    phone: string;
  };
  insuranceInfo?: {
    payerName: string;
    memberId: string;
    groupNumber: string;
  };
  avatar?: string;
  preferredLanguage: string;
  communicationPreferences: {
    email: boolean;
    sms: boolean;
    phone: boolean;
  };
}

export interface HealthCondition {
  id: string;
  name: string;
  icdCode: string;
  diagnosedDate: string;
  status: "active" | "resolved" | "chronic";
}

export interface Allergy {
  id: string;
  allergen: string;
  reaction: string;
  severity: "mild" | "moderate" | "severe";
}

export interface LabResult {
  id: string;
  testName: string;
  result: string;
  unit: string;
  normalRange: string;
  status: "normal" | "abnormal" | "critical";
  date: string;
  orderedBy: string;
  notes?: string;
}

export interface LabReport {
  id: string;
  date: string;
  orderingProvider: string;
  results: LabResult[];
  providerNote?: string;
}

export interface VisitSummary {
  id: string;
  date: string;
  provider: string;
  specialty: string;
  location: string;
  visitType: string;
  chiefComplaint: string;
  diagnosis: string[];
  treatmentPlan: string;
  followUpDate?: string;
}

export interface Immunization {
  id: string;
  name: string;
  date: string;
  administeredBy: string;
  site: string;
  lotNumber: string;
  nextDueDate?: string;
}

export interface HealthSummary {
  conditions: HealthCondition[];
  allergies: Allergy[];
  recentLabs: LabReport[];
  visits: VisitSummary[];
  immunizations: Immunization[];
}

export interface Medication {
  id: string;
  name: string;
  dosage: string;
  frequency: string;
  instructions: string;
  prescriber: string;
  pharmacy: string;
  startDate: string;
  endDate?: string;
  refillsRemaining: number;
  totalRefills: number;
  lastFilledDate: string;
  nextRefillDate: string;
  status: "active" | "discontinued" | "completed";
}

export interface RefillRequest {
  id: string;
  medicationId: string;
  medicationName: string;
  status: "pending" | "approved" | "denied" | "ready_for_pickup";
  requestedAt: string;
  processedAt?: string;
  notes?: string;
}

export type AppointmentStatus = "scheduled" | "confirmed" | "checked_in" | "completed" | "cancelled" | "no_show";

export interface Appointment {
  id: string;
  date: string;
  time: string;
  endTime: string;
  provider: {
    id: string;
    name: string;
    specialty: string;
    avatar?: string;
    rating?: number;
  };
  location: {
    name: string;
    address: string;
  };
  visitType: string;
  status: AppointmentStatus;
  notes?: string;
  telehealth?: boolean;
  telehealthUrl?: string;
  preVisitInstructions?: string[];
}

export interface AvailableSlot {
  date: string;
  time: string;
  endTime: string;
  providerId: string;
  providerName: string;
  locationId: string;
  locationName: string;
}

export interface PortalMessage {
  id: string;
  threadId: string;
  senderId: string;
  senderName: string;
  senderRole: "patient" | "provider" | "staff";
  subject: string;
  content: string;
  attachments?: Array<{ name: string; url: string; type: string }>;
  timestamp: string;
  read: boolean;
}

export interface MessageThread {
  id: string;
  subject: string;
  recipientName: string;
  recipientRole: string;
  lastMessage: string;
  lastMessageTime: string;
  unreadCount: number;
  messages: PortalMessage[];
}

export interface Bill {
  id: string;
  date: string;
  description: string;
  provider: string;
  serviceDate: string;
  totalAmount: number;
  insurancePaid: number;
  patientResponsibility: number;
  amountPaid: number;
  balance: number;
  dueDate: string;
  status: "pending" | "paid" | "overdue" | "payment_plan";
  lineItems: Array<{
    description: string;
    amount: number;
    insuranceCovered: number;
    patientOwes: number;
  }>;
}

export interface PaymentMethod {
  id: string;
  type: "card" | "bank" | "upi";
  last4: string;
  brand?: string;
  isDefault: boolean;
  expiryMonth?: number;
  expiryYear?: number;
}

export interface PaymentPlan {
  id: string;
  totalAmount: number;
  monthlyPayment: number;
  remainingPayments: number;
  nextPaymentDate: string;
  status: "active" | "completed" | "defaulted";
}

// =============================================================================
// STORE STATE
// =============================================================================

interface PatientPortalState {
  // Patient profile
  patient: PatientProfile | null;
  isLoadingProfile: boolean;

  // Health records
  healthSummary: HealthSummary | null;
  isLoadingHealth: boolean;

  // Medications
  medications: Medication[];
  refillRequests: RefillRequest[];
  isLoadingMedications: boolean;
  isRequestingRefill: boolean;

  // Appointments
  appointments: Appointment[];
  availableSlots: AvailableSlot[];
  isLoadingAppointments: boolean;
  isBookingAppointment: boolean;

  // Messages
  messageThreads: MessageThread[];
  activeThread: MessageThread | null;
  isLoadingMessages: boolean;
  isSendingMessage: boolean;

  // Billing
  bills: Bill[];
  totalBalance: number;
  paymentMethods: PaymentMethod[];
  paymentPlan: PaymentPlan | null;
  isLoadingBills: boolean;
  isProcessingPayment: boolean;

  // Actions
  fetchProfile: () => Promise<void>;
  updateProfile: (updates: Partial<PatientProfile>) => Promise<void>;

  fetchHealthSummary: () => Promise<void>;
  downloadHealthRecord: (type: string) => Promise<void>;

  fetchMedications: () => Promise<void>;
  requestRefill: (medicationId: string) => Promise<void>;

  fetchAppointments: () => Promise<void>;
  searchAvailableSlots: (providerId: string, startDate: string, endDate: string) => Promise<void>;
  bookAppointment: (slot: AvailableSlot, visitType: string, notes?: string) => Promise<void>;
  rescheduleAppointment: (appointmentId: string, newSlot: AvailableSlot) => Promise<void>;
  cancelAppointment: (appointmentId: string, reason: string) => Promise<void>;

  fetchMessageThreads: () => Promise<void>;
  selectThread: (threadId: string) => void;
  sendMessage: (threadId: string, content: string, attachments?: File[]) => Promise<void>;
  createNewThread: (recipientId: string, subject: string, content: string) => Promise<void>;
  markAsRead: (threadId: string) => void;

  fetchBills: () => Promise<void>;
  makePayment: (billId: string, amount: number, paymentMethodId: string) => Promise<void>;
  setupPaymentPlan: (billId: string, months: number) => Promise<void>;
  addPaymentMethod: (method: Partial<PaymentMethod>) => Promise<void>;
}

// =============================================================================
// MOCK DATA GENERATORS
// =============================================================================

const mockPatient: PatientProfile = {
  id: "patient-001",
  mrn: "MRN-12345",
  firstName: "John",
  lastName: "Doe",
  email: "john.doe@email.com",
  phone: "+91 98765 43210",
  dateOfBirth: "1965-03-15",
  gender: "Male",
  address: {
    street: "123 Main Street",
    city: "Bangalore",
    state: "Karnataka",
    zipCode: "560001",
  },
  emergencyContact: {
    name: "Jane Doe",
    relationship: "Spouse",
    phone: "+91 98765 43211",
  },
  insuranceInfo: {
    payerName: "Star Health Insurance",
    memberId: "SH123456789",
    groupNumber: "GRP-001",
  },
  preferredLanguage: "English",
  communicationPreferences: {
    email: true,
    sms: true,
    phone: false,
  },
};

const mockHealthSummary: HealthSummary = {
  conditions: [
    { id: "cond1", name: "Type 2 Diabetes Mellitus", icdCode: "E11.9", diagnosedDate: "2020-05-15", status: "chronic" },
    { id: "cond2", name: "Essential Hypertension", icdCode: "I10", diagnosedDate: "2019-08-20", status: "chronic" },
    { id: "cond3", name: "Hyperlipidemia", icdCode: "E78.5", diagnosedDate: "2021-01-10", status: "active" },
  ],
  allergies: [
    { id: "all1", allergen: "Penicillin", reaction: "Rash, difficulty breathing", severity: "severe" },
    { id: "all2", allergen: "Sulfa drugs", reaction: "Skin rash", severity: "moderate" },
  ],
  recentLabs: [
    {
      id: "lab1",
      date: "2024-11-25",
      orderingProvider: "Dr. Rohit Sharma",
      results: [
        { id: "r1", testName: "Hemoglobin A1C", result: "7.2", unit: "%", normalRange: "<7.0%", status: "abnormal", date: "2024-11-25", orderedBy: "Dr. Sharma" },
        { id: "r2", testName: "Total Cholesterol", result: "195", unit: "mg/dL", normalRange: "<200 mg/dL", status: "normal", date: "2024-11-25", orderedBy: "Dr. Sharma" },
        { id: "r3", testName: "LDL Cholesterol", result: "118", unit: "mg/dL", normalRange: "<100 mg/dL", status: "abnormal", date: "2024-11-25", orderedBy: "Dr. Sharma" },
        { id: "r4", testName: "HDL Cholesterol", result: "52", unit: "mg/dL", normalRange: ">40 mg/dL", status: "normal", date: "2024-11-25", orderedBy: "Dr. Sharma" },
        { id: "r5", testName: "Triglycerides", result: "145", unit: "mg/dL", normalRange: "<150 mg/dL", status: "normal", date: "2024-11-25", orderedBy: "Dr. Sharma" },
      ],
      providerNote: "Your A1C is slightly above our target of 7.0%. Let's discuss dietary adjustments at your next visit. Cholesterol looks good!",
    },
  ],
  visits: [
    {
      id: "visit1",
      date: "2024-11-20",
      provider: "Dr. Rohit Sharma",
      specialty: "Cardiology",
      location: "Surya Whitefield",
      visitType: "Follow-up",
      chiefComplaint: "Routine cardiology follow-up",
      diagnosis: ["Essential Hypertension", "Type 2 Diabetes Mellitus"],
      treatmentPlan: "Continue current medications. Follow low-sodium diet. Follow up in 3 months.",
      followUpDate: "2024-12-23",
    },
  ],
  immunizations: [
    { id: "imm1", name: "Influenza (Flu) Vaccine", date: "2024-10-15", administeredBy: "Nurse Sarah", site: "Left Arm", lotNumber: "FL2024-001", nextDueDate: "2025-10-15" },
    { id: "imm2", name: "COVID-19 Booster", date: "2024-09-01", administeredBy: "Nurse Mike", site: "Right Arm", lotNumber: "CV2024-005" },
  ],
};

const mockMedications: Medication[] = [
  {
    id: "med1",
    name: "Metformin 1000mg Tablet",
    dosage: "1000mg",
    frequency: "Twice daily",
    instructions: "Take 1 tablet by mouth twice daily with meals",
    prescriber: "Dr. Rohit Sharma",
    pharmacy: "Apollo Pharmacy, Whitefield",
    startDate: "2020-06-01",
    refillsRemaining: 2,
    totalRefills: 3,
    lastFilledDate: "2024-11-20",
    nextRefillDate: "2024-12-15",
    status: "active",
  },
  {
    id: "med2",
    name: "Lisinopril 10mg Tablet",
    dosage: "10mg",
    frequency: "Once daily",
    instructions: "Take 1 tablet by mouth once daily",
    prescriber: "Dr. Rohit Sharma",
    pharmacy: "Apollo Pharmacy, Whitefield",
    startDate: "2019-09-01",
    refillsRemaining: 0,
    totalRefills: 3,
    lastFilledDate: "2024-10-01",
    nextRefillDate: "2024-11-01",
    status: "active",
  },
  {
    id: "med3",
    name: "Atorvastatin 20mg Tablet",
    dosage: "20mg",
    frequency: "Once daily at bedtime",
    instructions: "Take 1 tablet by mouth at bedtime",
    prescriber: "Dr. Rohit Sharma",
    pharmacy: "Apollo Pharmacy, Whitefield",
    startDate: "2021-02-01",
    refillsRemaining: 1,
    totalRefills: 3,
    lastFilledDate: "2024-11-01",
    nextRefillDate: "2024-12-01",
    status: "active",
  },
];

const mockAppointments: Appointment[] = [
  {
    id: "apt1",
    date: "2024-12-23",
    time: "14:00",
    endTime: "14:30",
    provider: { id: "doc1", name: "Dr. Rohit Sharma", specialty: "Cardiology", rating: 4.8 },
    location: { name: "Surya Whitefield", address: "123 Tech Park, Whitefield, Bangalore" },
    visitType: "Follow-up",
    status: "confirmed",
    preVisitInstructions: ["Bring list of current medications", "Fast for 8 hours before appointment (for labs)"],
  },
  {
    id: "apt2",
    date: "2024-11-20",
    time: "10:00",
    endTime: "10:30",
    provider: { id: "doc1", name: "Dr. Rohit Sharma", specialty: "Cardiology", rating: 4.8 },
    location: { name: "Surya Whitefield", address: "123 Tech Park, Whitefield, Bangalore" },
    visitType: "Follow-up",
    status: "completed",
  },
];

const mockMessageThreads: MessageThread[] = [
  {
    id: "thread1",
    subject: "Your A1C Results",
    recipientName: "Dr. Sharma's Office",
    recipientRole: "Cardiology",
    lastMessage: "Try to reduce carbohydrate intake and increase fiber.",
    lastMessageTime: new Date(Date.now() - 3600000).toISOString(),
    unreadCount: 0,
    messages: [
      { id: "msg1", threadId: "thread1", senderId: "doc1", senderName: "Dr. Sharma's Office", senderRole: "provider", subject: "Your A1C Results", content: "Hi John, your A1C results are in. It's 7.2%, which is slightly above our target. Let's discuss at your next visit.", timestamp: new Date(Date.now() - 7200000).toISOString(), read: true },
      { id: "msg2", threadId: "thread1", senderId: "patient-001", senderName: "John Doe", senderRole: "patient", subject: "Re: Your A1C Results", content: "Thank you doctor. Should I make any changes to my diet before our next appointment?", timestamp: new Date(Date.now() - 5400000).toISOString(), read: true },
      { id: "msg3", threadId: "thread1", senderId: "doc1", senderName: "Dr. Sharma's Office", senderRole: "provider", subject: "Re: Your A1C Results", content: "Try to reduce carbohydrate intake and increase fiber. I'll send you a dietary guide. Keep taking Metformin with meals.", timestamp: new Date(Date.now() - 3600000).toISOString(), read: true, attachments: [{ name: "Diabetic_Diet_Guide.pdf", url: "/files/diet-guide.pdf", type: "application/pdf" }] },
    ],
  },
  {
    id: "thread2",
    subject: "Payment Received",
    recipientName: "Billing Department",
    recipientRole: "Billing",
    lastMessage: "Thank you for your payment of ₹2,500.",
    lastMessageTime: new Date(Date.now() - 432000000).toISOString(),
    unreadCount: 0,
    messages: [
      { id: "msg4", threadId: "thread2", senderId: "billing", senderName: "Billing Department", senderRole: "staff", subject: "Payment Received", content: "Thank you for your payment of ₹2,500. Your account has been credited.", timestamp: new Date(Date.now() - 432000000).toISOString(), read: true },
    ],
  },
];

const mockBills: Bill[] = [
  {
    id: "bill1",
    date: "2024-11-25",
    description: "Cardiology Visit",
    provider: "Dr. Rohit Sharma",
    serviceDate: "2024-11-20",
    totalAmount: 3500,
    insurancePaid: 2250,
    patientResponsibility: 1250,
    amountPaid: 0,
    balance: 1250,
    dueDate: "2024-12-15",
    status: "pending",
    lineItems: [
      { description: "Office Visit - Established Patient", amount: 2500, insuranceCovered: 1750, patientOwes: 750 },
      { description: "ECG/EKG", amount: 1000, insuranceCovered: 500, patientOwes: 500 },
    ],
  },
  {
    id: "bill2",
    date: "2024-10-20",
    description: "Lab Work - Routine Labs",
    provider: "Surya Labs",
    serviceDate: "2024-10-15",
    totalAmount: 2500,
    insurancePaid: 2500,
    patientResponsibility: 0,
    amountPaid: 0,
    balance: 0,
    dueDate: "2024-11-01",
    status: "paid",
    lineItems: [
      { description: "Complete Blood Count", amount: 500, insuranceCovered: 500, patientOwes: 0 },
      { description: "Lipid Panel", amount: 1000, insuranceCovered: 1000, patientOwes: 0 },
      { description: "HbA1C", amount: 1000, insuranceCovered: 1000, patientOwes: 0 },
    ],
  },
];

const mockPaymentMethods: PaymentMethod[] = [
  { id: "pm1", type: "card", last4: "4242", brand: "Visa", isDefault: true, expiryMonth: 12, expiryYear: 2026 },
];

// =============================================================================
// STORE IMPLEMENTATION
// =============================================================================

export const usePatientPortalStore = create<PatientPortalState>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      // Initial state
      patient: null,
      isLoadingProfile: false,
      healthSummary: null,
      isLoadingHealth: false,
      medications: [],
      refillRequests: [],
      isLoadingMedications: false,
      isRequestingRefill: false,
      appointments: [],
      availableSlots: [],
      isLoadingAppointments: false,
      isBookingAppointment: false,
      messageThreads: [],
      activeThread: null,
      isLoadingMessages: false,
      isSendingMessage: false,
      bills: [],
      totalBalance: 0,
      paymentMethods: [],
      paymentPlan: null,
      isLoadingBills: false,
      isProcessingPayment: false,

      // Profile actions
      fetchProfile: async () => {
        set({ isLoadingProfile: true });
        await new Promise((r) => setTimeout(r, 500));
        set({ patient: mockPatient, isLoadingProfile: false });
      },

      updateProfile: async (updates) => {
        await new Promise((r) => setTimeout(r, 500));
        set((state) => ({
          patient: state.patient ? { ...state.patient, ...updates } : null,
        }));
      },

      // Health records actions
      fetchHealthSummary: async () => {
        set({ isLoadingHealth: true });
        await new Promise((r) => setTimeout(r, 500));
        set({ healthSummary: mockHealthSummary, isLoadingHealth: false });
      },

      downloadHealthRecord: async (type) => {
        await new Promise((r) => setTimeout(r, 1000));
        // Simulate download
        console.log(`Downloading ${type} health record...`);
      },

      // Medication actions
      fetchMedications: async () => {
        set({ isLoadingMedications: true });
        await new Promise((r) => setTimeout(r, 500));
        set({ medications: mockMedications, isLoadingMedications: false });
      },

      requestRefill: async (medicationId) => {
        set({ isRequestingRefill: true });
        await new Promise((r) => setTimeout(r, 1000));
        const med = get().medications.find((m) => m.id === medicationId);
        const newRequest: RefillRequest = {
          id: `refill-${Date.now()}`,
          medicationId,
          medicationName: med?.name || "",
          status: "pending",
          requestedAt: new Date().toISOString(),
        };
        set((state) => ({
          refillRequests: [...state.refillRequests, newRequest],
          isRequestingRefill: false,
        }));
      },

      // Appointment actions
      fetchAppointments: async () => {
        set({ isLoadingAppointments: true });
        await new Promise((r) => setTimeout(r, 500));
        set({ appointments: mockAppointments, isLoadingAppointments: false });
      },

      searchAvailableSlots: async (providerId, startDate, endDate) => {
        await new Promise((r) => setTimeout(r, 500));
        // Generate mock slots
        const slots: AvailableSlot[] = [];
        const times = ["09:00", "09:30", "10:00", "10:30", "11:00", "14:00", "14:30", "15:00", "15:30"];
        const date = new Date(startDate);
        for (let d = 0; d < 7; d++) {
          const currentDate = new Date(date);
          currentDate.setDate(currentDate.getDate() + d);
          if (currentDate.getDay() !== 0 && currentDate.getDay() !== 6) {
            times.forEach((time) => {
              if (Math.random() > 0.3) {
                slots.push({
                  date: currentDate.toISOString().split("T")[0],
                  time,
                  endTime: `${parseInt(time.split(":")[0])}:${parseInt(time.split(":")[1]) + 30}`,
                  providerId,
                  providerName: "Dr. Rohit Sharma",
                  locationId: "loc1",
                  locationName: "Surya Whitefield",
                });
              }
            });
          }
        }
        set({ availableSlots: slots });
      },

      bookAppointment: async (slot, visitType, notes) => {
        set({ isBookingAppointment: true });
        await new Promise((r) => setTimeout(r, 1000));
        const newAppointment: Appointment = {
          id: `apt-${Date.now()}`,
          date: slot.date,
          time: slot.time,
          endTime: slot.endTime,
          provider: { id: slot.providerId, name: slot.providerName, specialty: "Cardiology" },
          location: { name: slot.locationName, address: "123 Tech Park, Whitefield, Bangalore" },
          visitType,
          status: "scheduled",
          notes,
        };
        set((state) => ({
          appointments: [newAppointment, ...state.appointments],
          isBookingAppointment: false,
        }));
      },

      rescheduleAppointment: async (appointmentId, newSlot) => {
        await new Promise((r) => setTimeout(r, 800));
        set((state) => ({
          appointments: state.appointments.map((apt) =>
            apt.id === appointmentId
              ? { ...apt, date: newSlot.date, time: newSlot.time, endTime: newSlot.endTime, status: "scheduled" }
              : apt
          ),
        }));
      },

      cancelAppointment: async (appointmentId, reason) => {
        await new Promise((r) => setTimeout(r, 500));
        set((state) => ({
          appointments: state.appointments.map((apt) =>
            apt.id === appointmentId ? { ...apt, status: "cancelled", notes: reason } : apt
          ),
        }));
      },

      // Messaging actions
      fetchMessageThreads: async () => {
        set({ isLoadingMessages: true });
        await new Promise((r) => setTimeout(r, 500));
        set({ messageThreads: mockMessageThreads, isLoadingMessages: false });
      },

      selectThread: (threadId) => {
        const thread = get().messageThreads.find((t) => t.id === threadId);
        set({ activeThread: thread || null });
        if (thread) {
          get().markAsRead(threadId);
        }
      },

      sendMessage: async (threadId, content, attachments) => {
        set({ isSendingMessage: true });
        await new Promise((r) => setTimeout(r, 500));
        const { patient } = get();
        const newMessage: PortalMessage = {
          id: `msg-${Date.now()}`,
          threadId,
          senderId: patient?.id || "",
          senderName: `${patient?.firstName} ${patient?.lastName}`,
          senderRole: "patient",
          subject: "",
          content,
          timestamp: new Date().toISOString(),
          read: true,
        };
        set((state) => ({
          messageThreads: state.messageThreads.map((t) =>
            t.id === threadId
              ? { ...t, messages: [...t.messages, newMessage], lastMessage: content, lastMessageTime: newMessage.timestamp }
              : t
          ),
          activeThread: state.activeThread?.id === threadId
            ? { ...state.activeThread, messages: [...state.activeThread.messages, newMessage] }
            : state.activeThread,
          isSendingMessage: false,
        }));
      },

      createNewThread: async (recipientId, subject, content) => {
        await new Promise((r) => setTimeout(r, 500));
        const { patient } = get();
        const newThread: MessageThread = {
          id: `thread-${Date.now()}`,
          subject,
          recipientName: "Dr. Sharma's Office",
          recipientRole: "Cardiology",
          lastMessage: content,
          lastMessageTime: new Date().toISOString(),
          unreadCount: 0,
          messages: [
            {
              id: `msg-${Date.now()}`,
              threadId: `thread-${Date.now()}`,
              senderId: patient?.id || "",
              senderName: `${patient?.firstName} ${patient?.lastName}`,
              senderRole: "patient",
              subject,
              content,
              timestamp: new Date().toISOString(),
              read: true,
            },
          ],
        };
        set((state) => ({ messageThreads: [newThread, ...state.messageThreads] }));
      },

      markAsRead: (threadId) => {
        set((state) => ({
          messageThreads: state.messageThreads.map((t) =>
            t.id === threadId ? { ...t, unreadCount: 0, messages: t.messages.map((m) => ({ ...m, read: true })) } : t
          ),
        }));
      },

      // Billing actions
      fetchBills: async () => {
        set({ isLoadingBills: true });
        await new Promise((r) => setTimeout(r, 500));
        const balance = mockBills.reduce((sum, b) => sum + b.balance, 0);
        set({
          bills: mockBills,
          totalBalance: balance,
          paymentMethods: mockPaymentMethods,
          isLoadingBills: false,
        });
      },

      makePayment: async (billId, amount, paymentMethodId) => {
        set({ isProcessingPayment: true });
        await new Promise((r) => setTimeout(r, 1500));
        set((state) => ({
          bills: state.bills.map((b) =>
            b.id === billId
              ? { ...b, amountPaid: b.amountPaid + amount, balance: b.balance - amount, status: b.balance - amount <= 0 ? "paid" : b.status }
              : b
          ),
          totalBalance: state.totalBalance - amount,
          isProcessingPayment: false,
        }));
      },

      setupPaymentPlan: async (billId, months) => {
        await new Promise((r) => setTimeout(r, 800));
        const bill = get().bills.find((b) => b.id === billId);
        if (bill) {
          const plan: PaymentPlan = {
            id: `plan-${Date.now()}`,
            totalAmount: bill.balance,
            monthlyPayment: Math.ceil(bill.balance / months),
            remainingPayments: months,
            nextPaymentDate: new Date(Date.now() + 2592000000).toISOString(),
            status: "active",
          };
          set((state) => ({
            paymentPlan: plan,
            bills: state.bills.map((b) => (b.id === billId ? { ...b, status: "payment_plan" } : b)),
          }));
        }
      },

      addPaymentMethod: async (method) => {
        await new Promise((r) => setTimeout(r, 500));
        const newMethod: PaymentMethod = {
          id: `pm-${Date.now()}`,
          type: method.type || "card",
          last4: method.last4 || "0000",
          brand: method.brand,
          isDefault: method.isDefault || false,
          expiryMonth: method.expiryMonth,
          expiryYear: method.expiryYear,
        };
        set((state) => ({ paymentMethods: [...state.paymentMethods, newMethod] }));
      },
    })),
    { name: "patient-portal-store" }
  )
);

export default usePatientPortalStore;
