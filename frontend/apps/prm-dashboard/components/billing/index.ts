// Billing & Revenue Components - Barrel Export
// EPIC-UX-009: Billing & Revenue Portal

export { EligibilityVerification, EligibilityCard, EligibilityResultCard } from "./eligibility-verification";
export { ClaimsDashboard, ClaimsTable, ClaimDetailPanel, ClaimsSummaryCards } from "./claims-dashboard";
export { DenialManagement, DenialCard, DenialDetailView, AIAnalysisCard } from "./denial-management";
export { PatientStatement, PaymentForm, PaymentPlanDialog, StatementSkeleton } from "./patient-statement";
export { RevenueAnalytics, RevenueMetricsCards, RevenueDepartmentChart, ARAgingChart } from "./revenue-analytics";

// Re-export types
export type {
  Insurance,
  EligibilityResult,
  Claim,
  ClaimLineItem,
  ClaimStatus,
  Denial,
  Payment,
  PaymentStatus,
  Statement,
  RevenueMetrics,
} from "@/lib/store/billing-store";
