// Billing & Revenue Store
// EPIC-UX-009: Billing & Revenue Portal

import { create } from "zustand";
import { devtools, subscribeWithSelector } from "zustand/middleware";

// ============================================================================
// Types
// ============================================================================

export type ClaimStatus = "draft" | "pending" | "submitted" | "accepted" | "denied" | "paid" | "appealed";
export type PaymentStatus = "pending" | "processing" | "completed" | "failed" | "refunded";
export type EligibilityStatus = "verified" | "pending" | "failed" | "expired";

export interface Insurance {
  id: string;
  payerName: string;
  payerId: string;
  memberId: string;
  groupNumber?: string;
  subscriberName: string;
  subscriberRelationship: "self" | "spouse" | "child" | "other";
  planType: "PPO" | "HMO" | "EPO" | "POS" | "HDHP" | "Medicare" | "Medicaid";
  effectiveDate: string;
  termDate?: string;
  isPrimary: boolean;
}

export interface EligibilityResult {
  id: string;
  patientId: string;
  insurance: Insurance;
  status: EligibilityStatus;
  verifiedAt: string;
  coverageActive: boolean;
  benefits: {
    copay: number;
    deductible: { total: number; met: number; remaining: number };
    coinsurance: number;
    outOfPocketMax: { total: number; met: number };
    priorAuthRequired: boolean;
  };
  serviceType?: string;
  collectToday: number;
}

export interface ClaimLineItem {
  id: string;
  cptCode: string;
  description: string;
  modifiers: string[];
  units: number;
  chargeAmount: number;
  allowedAmount?: number;
  paidAmount?: number;
  adjustmentAmount?: number;
  status: "pending" | "paid" | "denied" | "adjusted";
  denialCode?: string;
}

export interface Claim {
  id: string;
  claimNumber: string;
  patientId: string;
  patientName: string;
  providerId: string;
  providerName: string;
  insurance: Insurance;
  dateOfService: string;
  submittedDate?: string;
  lineItems: ClaimLineItem[];
  totalCharged: number;
  totalAllowed?: number;
  totalPaid?: number;
  patientResponsibility?: number;
  status: ClaimStatus;
  denialCode?: string;
  denialReason?: string;
  appealDeadline?: string;
  notes?: string;
}

export interface Denial {
  id: string;
  claimId: string;
  claim: Claim;
  denialCode: string;
  denialReason: string;
  deniedDate: string;
  appealDeadline: string;
  daysRemaining: number;
  aiAnalysis?: {
    issueIdentified: string;
    suggestedAction: string;
    successProbability: number;
  };
  status: "new" | "in_review" | "appealed" | "overturned" | "upheld";
}

export interface Payment {
  id: string;
  patientId: string;
  statementId?: string;
  amount: number;
  method: "card" | "bank" | "cash" | "check" | "insurance";
  status: PaymentStatus;
  transactionId?: string;
  processedAt?: string;
  cardLast4?: string;
  receiptUrl?: string;
}

export interface Statement {
  id: string;
  patientId: string;
  patientName: string;
  statementDate: string;
  dueDate: string;
  visits: {
    date: string;
    provider: string;
    location: string;
    visitType: string;
    services: { description: string; amount: number }[];
    totalCharges: number;
    insurancePaid: number;
    adjustments: number;
    copayCollected: number;
  }[];
  totalDue: number;
  minimumPayment?: number;
  paymentPlanAvailable: boolean;
  status: "sent" | "viewed" | "partial" | "paid" | "overdue";
}

export interface RevenueMetrics {
  period: string;
  grossRevenue: number;
  netRevenue: number;
  collections: number;
  collectionRate: number;
  daysInAR: number;
  denialRate: number;
  byDepartment: { name: string; amount: number; percentage: number }[];
  byPayer: { name: string; denialRate: number; avgDaysToPayment: number }[];
  arAging: { bucket: string; amount: number }[];
  trend: { date: string; revenue: number; collections: number }[];
}

// ============================================================================
// State Interface
// ============================================================================

interface BillingState {
  // Eligibility
  eligibilityResults: EligibilityResult[];
  currentEligibility: EligibilityResult | null;
  isVerifyingEligibility: boolean;

  // Claims
  claims: Claim[];
  selectedClaim: Claim | null;
  claimFilters: {
    status?: ClaimStatus;
    payer?: string;
    dateRange?: { start: string; end: string };
    search?: string;
  };
  claimsPagination: { page: number; pageSize: number; total: number };
  isLoadingClaims: boolean;

  // Denials
  denials: Denial[];
  selectedDenial: Denial | null;
  isLoadingDenials: boolean;

  // Payments
  payments: Payment[];
  isProcessingPayment: boolean;

  // Statements
  statements: Statement[];
  currentStatement: Statement | null;
  isLoadingStatements: boolean;

  // Revenue Analytics
  revenueMetrics: RevenueMetrics | null;
  isLoadingMetrics: boolean;

  // Summary Stats
  claimsSummary: {
    pending: { count: number; amount: number };
    submitted: { count: number; amount: number };
    denied: { count: number; amount: number };
    paid: { count: number; amount: number };
  };

  // Actions
  verifyEligibility: (patientId: string, insuranceId: string, serviceType?: string) => Promise<EligibilityResult>;
  fetchClaims: (filters?: BillingState["claimFilters"]) => Promise<void>;
  fetchClaimDetail: (claimId: string) => Promise<Claim>;
  createClaim: (claim: Partial<Claim>) => Promise<Claim>;
  updateClaim: (claimId: string, updates: Partial<Claim>) => Promise<void>;
  submitClaim: (claimId: string) => Promise<void>;
  resubmitClaim: (claimId: string, corrections: Partial<ClaimLineItem>[]) => Promise<void>;
  fetchDenials: () => Promise<void>;
  applyDenialFix: (denialId: string) => Promise<void>;
  appealDenial: (denialId: string, appealNotes: string) => Promise<void>;
  fetchStatements: (patientId: string) => Promise<void>;
  processPayment: (payment: Omit<Payment, "id" | "status" | "processedAt">) => Promise<Payment>;
  setupPaymentPlan: (statementId: string, months: number) => Promise<void>;
  fetchRevenueMetrics: (period: string) => Promise<void>;
  setClaimFilters: (filters: BillingState["claimFilters"]) => void;
  setClaimsPagination: (page: number) => void;
}

// ============================================================================
// Mock Data Generators
// ============================================================================

function generateMockClaims(): Claim[] {
  const statuses: ClaimStatus[] = ["pending", "submitted", "denied", "paid"];
  const payers = ["Aetna PPO", "Blue Cross", "United Healthcare", "Medicare"];
  const patients = [
    { id: "pat-1", name: "John Doe" },
    { id: "pat-2", name: "Jane Smith" },
    { id: "pat-3", name: "Bob Wilson" },
  ];

  return Array.from({ length: 20 }, (_, i) => {
    const status = statuses[i % 4];
    const patient = patients[i % 3];
    const totalCharged = Math.floor(Math.random() * 5000) + 500;

    return {
      id: `claim-${i + 1}`,
      claimNumber: `CLM-2024-${1234 + i}`,
      patientId: patient.id,
      patientName: patient.name,
      providerId: "prov-1",
      providerName: "Dr. Rohit Sharma",
      insurance: {
        id: `ins-${i}`,
        payerName: payers[i % 4],
        payerId: `payer-${i % 4}`,
        memberId: `XYZ${123456 + i}`,
        subscriberName: patient.name,
        subscriberRelationship: "self",
        planType: "PPO",
        effectiveDate: "2024-01-01",
        isPrimary: true,
      },
      dateOfService: new Date(Date.now() - (i * 2) * 24 * 60 * 60 * 1000).toISOString().split("T")[0],
      submittedDate: status !== "pending" ? new Date(Date.now() - i * 24 * 60 * 60 * 1000).toISOString() : undefined,
      lineItems: [
        {
          id: `line-${i}-1`,
          cptCode: "99214",
          description: "Office Visit Level 4",
          modifiers: [],
          units: 1,
          chargeAmount: totalCharged * 0.6,
          status: status === "paid" ? "paid" : "pending",
        },
        {
          id: `line-${i}-2`,
          cptCode: "93000",
          description: "ECG with Interpretation",
          modifiers: [],
          units: 1,
          chargeAmount: totalCharged * 0.4,
          status: status === "paid" ? "paid" : "pending",
        },
      ],
      totalCharged,
      totalPaid: status === "paid" ? totalCharged * 0.8 : undefined,
      patientResponsibility: status === "paid" ? totalCharged * 0.2 : undefined,
      status,
      denialCode: status === "denied" ? "CO-4" : undefined,
      denialReason: status === "denied" ? "Modifier missing or inconsistent" : undefined,
      appealDeadline: status === "denied" ? new Date(Date.now() + 60 * 24 * 60 * 60 * 1000).toISOString() : undefined,
    };
  });
}

function generateMockDenials(claims: Claim[]): Denial[] {
  return claims
    .filter((c) => c.status === "denied")
    .map((claim) => ({
      id: `denial-${claim.id}`,
      claimId: claim.id,
      claim,
      denialCode: claim.denialCode || "CO-4",
      denialReason: claim.denialReason || "Modifier missing",
      deniedDate: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
      appealDeadline: claim.appealDeadline || new Date(Date.now() + 55 * 24 * 60 * 60 * 1000).toISOString(),
      daysRemaining: 55,
      aiAnalysis: {
        issueIdentified: "CPT code 99214 was billed without modifier 25, which is required when a significant E/M service is performed same day as a procedure.",
        suggestedAction: "Add modifier 25 to CPT 99214 and resubmit claim.",
        successProbability: 92,
      },
      status: "new",
    }));
}

function generateMockRevenueMetrics(): RevenueMetrics {
  return {
    period: "November 2024",
    grossRevenue: 12500000,
    netRevenue: 9550000,
    collections: 8820000,
    collectionRate: 92.4,
    daysInAR: 34,
    denialRate: 7.4,
    byDepartment: [
      { name: "Cardiology", amount: 3210000, percentage: 33.6 },
      { name: "Orthopedics", amount: 2580000, percentage: 27.0 },
      { name: "General Medicine", amount: 1720000, percentage: 18.0 },
      { name: "Pediatrics", amount: 1610000, percentage: 16.9 },
      { name: "Dermatology", amount: 430000, percentage: 4.5 },
    ],
    byPayer: [
      { name: "Aetna", denialRate: 8.2, avgDaysToPayment: 28 },
      { name: "Blue Cross", denialRate: 12.5, avgDaysToPayment: 35 },
      { name: "United", denialRate: 5.8, avgDaysToPayment: 22 },
      { name: "Medicare", denialRate: 3.2, avgDaysToPayment: 14 },
    ],
    arAging: [
      { bucket: "0-30 days", amount: 4520000 },
      { bucket: "31-60 days", amount: 2810000 },
      { bucket: "61-90 days", amount: 1530000 },
      { bucket: "90+ days", amount: 870000 },
    ],
    trend: Array.from({ length: 12 }, (_, i) => ({
      date: `2024-${String(i + 1).padStart(2, "0")}`,
      revenue: 8000000 + Math.random() * 2000000,
      collections: 7000000 + Math.random() * 2000000,
    })),
  };
}

// ============================================================================
// Store
// ============================================================================

export const useBillingStore = create<BillingState>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      // Initial State
      eligibilityResults: [],
      currentEligibility: null,
      isVerifyingEligibility: false,
      claims: [],
      selectedClaim: null,
      claimFilters: {},
      claimsPagination: { page: 1, pageSize: 20, total: 0 },
      isLoadingClaims: false,
      denials: [],
      selectedDenial: null,
      isLoadingDenials: false,
      payments: [],
      isProcessingPayment: false,
      statements: [],
      currentStatement: null,
      isLoadingStatements: false,
      revenueMetrics: null,
      isLoadingMetrics: false,
      claimsSummary: {
        pending: { count: 45, amount: 420000 },
        submitted: { count: 128, amount: 1250000 },
        denied: { count: 12, amount: 180000 },
        paid: { count: 892, amount: 8530000 },
      },

      // Actions
      verifyEligibility: async (patientId, insuranceId, serviceType) => {
        set({ isVerifyingEligibility: true });
        try {
          await new Promise((r) => setTimeout(r, 1500));

          const result: EligibilityResult = {
            id: `elig-${Date.now()}`,
            patientId,
            insurance: {
              id: insuranceId,
              payerName: "Aetna PPO",
              payerId: "aetna-001",
              memberId: "XYZ123456",
              groupNumber: "98765",
              subscriberName: "John Doe",
              subscriberRelationship: "self",
              planType: "PPO",
              effectiveDate: "2024-01-01",
              termDate: "2024-12-31",
              isPrimary: true,
            },
            status: "verified",
            verifiedAt: new Date().toISOString(),
            coverageActive: true,
            benefits: {
              copay: 500,
              deductible: { total: 5000, met: 3200, remaining: 1800 },
              coinsurance: 20,
              outOfPocketMax: { total: 15000, met: 4500 },
              priorAuthRequired: false,
            },
            serviceType,
            collectToday: 500,
          };

          set((state) => ({
            eligibilityResults: [...state.eligibilityResults, result],
            currentEligibility: result,
            isVerifyingEligibility: false,
          }));

          return result;
        } catch (error) {
          set({ isVerifyingEligibility: false });
          throw error;
        }
      },

      fetchClaims: async (filters) => {
        set({ isLoadingClaims: true, claimFilters: filters || {} });
        try {
          await new Promise((r) => setTimeout(r, 500));
          const claims = generateMockClaims();
          set({
            claims,
            claimsPagination: { page: 1, pageSize: 20, total: claims.length },
            isLoadingClaims: false,
          });
        } catch (error) {
          set({ isLoadingClaims: false });
          throw error;
        }
      },

      fetchClaimDetail: async (claimId) => {
        const claim = get().claims.find((c) => c.id === claimId);
        if (claim) {
          set({ selectedClaim: claim });
          return claim;
        }
        throw new Error("Claim not found");
      },

      createClaim: async (claimData) => {
        const newClaim: Claim = {
          ...claimData,
          id: `claim-${Date.now()}`,
          claimNumber: `CLM-2024-${Math.floor(Math.random() * 10000)}`,
          status: "draft",
          lineItems: claimData.lineItems || [],
          totalCharged: claimData.totalCharged || 0,
        } as Claim;

        set((state) => ({ claims: [newClaim, ...state.claims] }));
        return newClaim;
      },

      updateClaim: async (claimId, updates) => {
        set((state) => ({
          claims: state.claims.map((c) =>
            c.id === claimId ? { ...c, ...updates } : c
          ),
          selectedClaim:
            state.selectedClaim?.id === claimId
              ? { ...state.selectedClaim, ...updates }
              : state.selectedClaim,
        }));
      },

      submitClaim: async (claimId) => {
        await new Promise((r) => setTimeout(r, 1000));
        set((state) => ({
          claims: state.claims.map((c) =>
            c.id === claimId
              ? { ...c, status: "submitted", submittedDate: new Date().toISOString() }
              : c
          ),
        }));
      },

      resubmitClaim: async (claimId, corrections) => {
        await new Promise((r) => setTimeout(r, 1000));
        set((state) => ({
          claims: state.claims.map((c) =>
            c.id === claimId ? { ...c, status: "submitted" } : c
          ),
        }));
      },

      fetchDenials: async () => {
        set({ isLoadingDenials: true });
        try {
          await new Promise((r) => setTimeout(r, 500));
          const claims = get().claims.length > 0 ? get().claims : generateMockClaims();
          const denials = generateMockDenials(claims);
          set({ denials, isLoadingDenials: false });
        } catch (error) {
          set({ isLoadingDenials: false });
          throw error;
        }
      },

      applyDenialFix: async (denialId) => {
        await new Promise((r) => setTimeout(r, 1000));
        set((state) => ({
          denials: state.denials.map((d) =>
            d.id === denialId ? { ...d, status: "in_review" } : d
          ),
        }));
      },

      appealDenial: async (denialId, appealNotes) => {
        await new Promise((r) => setTimeout(r, 1000));
        set((state) => ({
          denials: state.denials.map((d) =>
            d.id === denialId ? { ...d, status: "appealed" } : d
          ),
        }));
      },

      fetchStatements: async (patientId) => {
        set({ isLoadingStatements: true });
        try {
          await new Promise((r) => setTimeout(r, 500));
          const statement: Statement = {
            id: `stmt-${Date.now()}`,
            patientId,
            patientName: "John Doe",
            statementDate: new Date().toISOString(),
            dueDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
            visits: [{
              date: "2024-11-20",
              provider: "Dr. Rohit Sharma",
              location: "Surya Whitefield",
              visitType: "Cardiology Follow-up",
              services: [
                { description: "Office Visit (Level 4)", amount: 1500 },
                { description: "ECG with Interpretation", amount: 1000 },
              ],
              totalCharges: 2500,
              insurancePaid: 1250,
              adjustments: 0,
              copayCollected: 500,
            }],
            totalDue: 750,
            paymentPlanAvailable: true,
            status: "sent",
          };
          set({ statements: [statement], currentStatement: statement, isLoadingStatements: false });
        } catch (error) {
          set({ isLoadingStatements: false });
          throw error;
        }
      },

      processPayment: async (paymentData) => {
        set({ isProcessingPayment: true });
        try {
          await new Promise((r) => setTimeout(r, 2000));
          const payment: Payment = {
            ...paymentData,
            id: `pmt-${Date.now()}`,
            status: "completed",
            processedAt: new Date().toISOString(),
            transactionId: `TXN${Date.now()}`,
            receiptUrl: `/receipts/${Date.now()}.pdf`,
          };
          set((state) => ({
            payments: [...state.payments, payment],
            isProcessingPayment: false,
          }));
          return payment;
        } catch (error) {
          set({ isProcessingPayment: false });
          throw error;
        }
      },

      setupPaymentPlan: async (statementId, months) => {
        await new Promise((r) => setTimeout(r, 1000));
        // In production, this would create a payment plan
      },

      fetchRevenueMetrics: async (period) => {
        set({ isLoadingMetrics: true });
        try {
          await new Promise((r) => setTimeout(r, 500));
          const metrics = generateMockRevenueMetrics();
          set({ revenueMetrics: metrics, isLoadingMetrics: false });
        } catch (error) {
          set({ isLoadingMetrics: false });
          throw error;
        }
      },

      setClaimFilters: (filters) => set({ claimFilters: filters }),
      setClaimsPagination: (page) =>
        set((state) => ({ claimsPagination: { ...state.claimsPagination, page } })),
    })),
    { name: "billing-store" }
  )
);
