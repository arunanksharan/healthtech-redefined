"use client";

import { create } from "zustand";
import { devtools, subscribeWithSelector } from "zustand/middleware";

// ============================================================================
// Types & Interfaces
// ============================================================================

export type MetricTrend = "up" | "down" | "stable";
export type MetricStatus = "good" | "warning" | "critical" | "neutral";
export type AlertPriority = "high" | "medium" | "low";
export type AlertStatus = "active" | "acknowledged" | "resolved" | "dismissed";
export type ChartType = "line" | "area" | "bar" | "pie" | "heatmap" | "gauge";
export type TimePeriod = "day" | "week" | "month" | "quarter" | "year" | "custom";
export type DashboardRole = "executive" | "clinical" | "operations" | "financial" | "patient_experience";

// Metric data point
export interface DataPoint {
  date: Date;
  value: number;
  label?: string;
  metadata?: Record<string, unknown>;
}

// Base metric interface
export interface Metric {
  id: string;
  name: string;
  value: number;
  previousValue?: number;
  target?: number;
  unit?: string;
  format: "number" | "currency" | "percentage" | "rating" | "duration";
  trend: MetricTrend;
  trendValue?: number;
  trendPercentage?: number;
  status: MetricStatus;
  benchmark?: number;
  sparklineData?: DataPoint[];
  lastUpdated: Date;
}

// KPI Card configuration
export interface KPICard {
  id: string;
  title: string;
  metric: Metric;
  size: "small" | "medium" | "large" | "wide";
  variant: "simple" | "progress" | "trend" | "comparison" | "action";
  icon?: string;
  color?: string;
  actionLabel?: string;
  actionType?: string;
  drilldownPath?: string;
}

// Chart configuration
export interface ChartConfig {
  id: string;
  title: string;
  type: ChartType;
  data: DataPoint[];
  comparisonData?: DataPoint[];
  benchmark?: number;
  xLabel?: string;
  yLabel?: string;
  showLegend?: boolean;
  showGrid?: boolean;
  colors?: string[];
  period: TimePeriod;
}

// AI Insight - Comprehensive type for all insight variations
export type InsightCategory = "revenue" | "operations" | "clinical" | "experience" | "prediction";
export type InsightSentiment = "positive" | "negative" | "neutral" | "warning";
export type InsightImpact = "high" | "medium" | "low";
export type InsightType = "positive" | "warning" | "info" | "action";

export interface InsightMetric {
  label: string;
  value: string;
  change?: number;
}

export interface InsightAction {
  id: string;
  label: string;
  type?: string;
}

export interface AIInsight {
  id: string;
  type: InsightType;
  title: string;
  description: string;
  // Category and sentiment are required for UI display
  category: InsightCategory;
  sentiment: InsightSentiment;
  impact: InsightImpact;
  // Optional metric reference
  metric?: string;
  metrics?: InsightMetric[];
  suggestedActions?: InsightAction[];
  // Timestamp for display - createdAt is the ISO string format
  createdAt: string;
  isRead: boolean;
}

// Proactive Alert - Comprehensive type for all alert variations
export type AlertType = "no_show_risk" | "cancellation" | "sentiment" | "capacity" | "follow_up" | "system";

export interface AlertAffectedItem {
  id?: string;
  name: string;
  time?: string;
  detail?: string;
  riskScore?: number;
  reason?: string;
}

export interface ProactiveAlert {
  id: string;
  priority: AlertPriority;
  status: AlertStatus;
  title: string;
  description: string;
  // Source and type information
  source: string;
  type?: AlertType;
  // Affected items with flexible structure
  affectedItems?: AlertAffectedItem[];
  // Suggested action as display string
  suggestedAction?: string;
  // Action button labels
  primaryAction?: string;
  secondaryAction?: string;
  // Timestamps - createdAt as ISO string for consistency
  createdAt: string;
  acknowledgedAt?: Date;
  resolvedAt?: Date;
}

// Sentiment Theme
export interface SentimentTheme {
  theme: string;
  count: number;
  sentiment: "positive" | "negative" | "neutral";
}

// Sentiment Sources
export interface SentimentSources {
  voice: number;
  whatsapp: number;
  survey: number;
  email: number;
}

// Department Sentiment - individual department data used in heatmap
export interface DepartmentSentiment {
  id: string;
  name: string;
  score: number;
  previousScore?: number;
  change?: number;
  // Required for heatmap display
  totalFeedback: number;
  sources: SentimentSources;
  topThemes: {
    positive: string[];
    negative: string[];
  };
}

// Sentiment data - supports both individual and aggregate formats
export interface SentimentData {
  // For individual department view
  id: string;
  department: string;
  location?: string;
  score: number;
  previousScore?: number;
  trend: MetricTrend;
  changePercent?: number;
  status: MetricStatus;
  topThemes: SentimentTheme[];
  sampleFeedback?: string[];
}

// Aggregate Sentiment Data - for dashboard overview
export interface SentimentDataAggregate {
  overallScore: number;
  previousScore: number;
  totalFeedback: number;
  departments: DepartmentSentiment[];
}

// Dashboard widget
export interface DashboardWidget {
  id: string;
  type: "kpi" | "chart" | "alerts" | "insights" | "sentiment" | "list" | "custom";
  config: KPICard | ChartConfig | { [key: string]: unknown };
  position: { x: number; y: number };
  size: { width: number; height: number };
  isVisible: boolean;
}

// Dashboard layout
export interface DashboardLayout {
  id: string;
  name: string;
  role: DashboardRole;
  widgets: DashboardWidget[];
  isDefault: boolean;
  createdAt: Date;
  updatedAt: Date;
}

// Analytics query
export interface AnalyticsQuery {
  id: string;
  query: string;
  response: {
    type: "text" | "chart" | "table" | "mixed";
    content: unknown;
    analysis?: string;
    followUpQuestions?: string[];
  };
  timestamp: Date;
}

// ============================================================================
// State Interface
// ============================================================================

export interface AnalyticsState {
  // Core metrics
  metrics: Metric[];
  kpiCards: KPICard[];
  isLoadingMetrics: boolean;

  // Charts
  charts: ChartConfig[];
  isLoadingCharts: boolean;

  // AI Insights
  insights: AIInsight[];
  isLoadingInsights: boolean;

  // Alerts
  alerts: ProactiveAlert[];
  isLoadingAlerts: boolean;

  // Sentiment
  sentimentData: SentimentData[];
  isLoadingSentiment: boolean;

  // Dashboard
  dashboardLayouts: DashboardLayout[];
  activeLayout: DashboardLayout | null;
  isCustomizing: boolean;

  // Query
  queryHistory: AnalyticsQuery[];
  isQueryLoading: boolean;
  currentQuery: string;

  // Filters
  selectedPeriod: TimePeriod;
  selectedDepartment: string;
  selectedLocation: string;
  dateRange: { start: Date; end: Date };

  // UI State
  greeting: string;
  lastRefresh: Date;

  // Aliases for compatibility
  isLoading: boolean;
  timeRange: TimePeriod;
}

// ============================================================================
// Actions Interface
// ============================================================================

export interface AnalyticsActions {
  // Metrics
  setMetrics: (metrics: Metric[]) => void;
  setKPICards: (cards: KPICard[]) => void;
  loadMetrics: () => Promise<void>;
  refreshMetric: (metricId: string) => Promise<void>;

  // Charts
  setCharts: (charts: ChartConfig[]) => void;
  loadCharts: () => Promise<void>;
  updateChartPeriod: (chartId: string, period: TimePeriod) => void;

  // Insights
  setInsights: (insights: AIInsight[]) => void;
  loadInsights: () => Promise<void>;
  markInsightRead: (insightId: string) => void;

  // Alerts
  setAlerts: (alerts: ProactiveAlert[]) => void;
  loadAlerts: () => Promise<void>;
  acknowledgeAlert: (alertId: string) => void;
  dismissAlert: (alertId: string) => void;
  executeAlertAction: (alertId: string, actionType: string) => Promise<void>;

  // Sentiment
  setSentimentData: (data: SentimentData[]) => void;
  loadSentimentData: () => Promise<void>;

  // Dashboard
  setActiveLayout: (layout: DashboardLayout) => void;
  saveLayout: (layout: DashboardLayout) => Promise<void>;
  addWidget: (widget: DashboardWidget) => void;
  removeWidget: (widgetId: string) => void;
  updateWidgetPosition: (widgetId: string, position: { x: number; y: number }) => void;
  setCustomizing: (isCustomizing: boolean) => void;

  // Query
  submitQuery: (query: string) => Promise<void>;
  setCurrentQuery: (query: string) => void;
  clearQueryHistory: () => void;

  // Filters
  setSelectedPeriod: (period: TimePeriod) => void;
  setSelectedDepartment: (departmentId: string) => void;
  setSelectedLocation: (locationId: string) => void;
  setDateRange: (range: { start: Date; end: Date }) => void;

  // Refresh
  refreshAll: () => Promise<void>;

  // Reset
  reset: () => void;

  // Aliases for compatibility
  setTimeRange: (range: TimePeriod) => void;
  fetchDashboardData: () => Promise<void>;
}

// ============================================================================
// Initial State
// ============================================================================

const getGreeting = (): string => {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
};

const getDefaultDateRange = (): { start: Date; end: Date } => {
  const end = new Date();
  const start = new Date();
  start.setDate(start.getDate() - 30);
  return { start, end };
};

const initialState: AnalyticsState = {
  metrics: [],
  kpiCards: [],
  isLoadingMetrics: false,

  charts: [],
  isLoadingCharts: false,

  insights: [],
  isLoadingInsights: false,

  alerts: [],
  isLoadingAlerts: false,

  sentimentData: [],
  isLoadingSentiment: false,

  dashboardLayouts: [],
  activeLayout: null,
  isCustomizing: false,

  queryHistory: [],
  isQueryLoading: false,
  currentQuery: "",

  selectedPeriod: "month",
  selectedDepartment: "all",
  selectedLocation: "all",
  dateRange: getDefaultDateRange(),

  greeting: getGreeting(),
  lastRefresh: new Date(),

  // Aliases
  isLoading: false,
  timeRange: "month",
};

// ============================================================================
// Store
// ============================================================================

export const useAnalyticsStore = create<AnalyticsState & AnalyticsActions>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      ...initialState,

      // ========================================================================
      // Metrics Actions
      // ========================================================================

      setMetrics: (metrics) => set({ metrics }),

      setKPICards: (kpiCards) => set({ kpiCards }),

      loadMetrics: async () => {
        set({ isLoadingMetrics: true });
        try {
          await new Promise((resolve) => setTimeout(resolve, 800));
          const mockMetrics = createMockMetrics();
          const mockKPICards = createMockKPICards(mockMetrics);
          set({ metrics: mockMetrics, kpiCards: mockKPICards, isLoadingMetrics: false });
        } catch {
          set({ isLoadingMetrics: false });
        }
      },

      refreshMetric: async (metricId) => {
        const { metrics } = get();
        await new Promise((resolve) => setTimeout(resolve, 300));
        set({
          metrics: metrics.map((m) =>
            m.id === metricId ? { ...m, lastUpdated: new Date() } : m
          ),
        });
      },

      // ========================================================================
      // Charts Actions
      // ========================================================================

      setCharts: (charts) => set({ charts }),

      loadCharts: async () => {
        set({ isLoadingCharts: true });
        try {
          await new Promise((resolve) => setTimeout(resolve, 600));
          const mockCharts = createMockCharts();
          set({ charts: mockCharts, isLoadingCharts: false });
        } catch {
          set({ isLoadingCharts: false });
        }
      },

      updateChartPeriod: (chartId, period) => {
        const { charts } = get();
        set({
          charts: charts.map((c) => (c.id === chartId ? { ...c, period } : c)),
        });
      },

      // ========================================================================
      // Insights Actions
      // ========================================================================

      setInsights: (insights) => set({ insights }),

      loadInsights: async () => {
        set({ isLoadingInsights: true });
        try {
          await new Promise((resolve) => setTimeout(resolve, 500));
          const mockInsights = createMockInsights();
          set({ insights: mockInsights, isLoadingInsights: false });
        } catch {
          set({ isLoadingInsights: false });
        }
      },

      markInsightRead: (insightId) => {
        const { insights } = get();
        set({
          insights: insights.map((i) =>
            i.id === insightId ? { ...i, isRead: true } : i
          ),
        });
      },

      // ========================================================================
      // Alerts Actions
      // ========================================================================

      setAlerts: (alerts) => set({ alerts }),

      loadAlerts: async () => {
        set({ isLoadingAlerts: true });
        try {
          await new Promise((resolve) => setTimeout(resolve, 500));
          const mockAlerts = createMockAlerts();
          set({ alerts: mockAlerts, isLoadingAlerts: false });
        } catch {
          set({ isLoadingAlerts: false });
        }
      },

      acknowledgeAlert: (alertId) => {
        const { alerts } = get();
        set({
          alerts: alerts.map((a) =>
            a.id === alertId
              ? { ...a, status: "acknowledged" as AlertStatus, acknowledgedAt: new Date() }
              : a
          ),
        });
      },

      dismissAlert: (alertId) => {
        const { alerts } = get();
        set({
          alerts: alerts.map((a) =>
            a.id === alertId ? { ...a, status: "dismissed" as AlertStatus } : a
          ),
        });
      },

      executeAlertAction: async (alertId, actionType) => {
        const { alerts } = get();
        await new Promise((resolve) => setTimeout(resolve, 1000));
        set({
          alerts: alerts.map((a) =>
            a.id === alertId
              ? { ...a, status: "resolved" as AlertStatus, resolvedAt: new Date() }
              : a
          ),
        });
      },

      // ========================================================================
      // Sentiment Actions
      // ========================================================================

      setSentimentData: (sentimentData) => set({ sentimentData }),

      loadSentimentData: async () => {
        set({ isLoadingSentiment: true });
        try {
          await new Promise((resolve) => setTimeout(resolve, 600));
          const mockSentiment = createMockSentimentData();
          set({ sentimentData: mockSentiment, isLoadingSentiment: false });
        } catch {
          set({ isLoadingSentiment: false });
        }
      },

      // ========================================================================
      // Dashboard Actions
      // ========================================================================

      setActiveLayout: (layout) => set({ activeLayout: layout }),

      saveLayout: async (layout) => {
        const { dashboardLayouts } = get();
        await new Promise((resolve) => setTimeout(resolve, 500));
        const exists = dashboardLayouts.find((l) => l.id === layout.id);
        if (exists) {
          set({
            dashboardLayouts: dashboardLayouts.map((l) =>
              l.id === layout.id ? { ...layout, updatedAt: new Date() } : l
            ),
          });
        } else {
          set({ dashboardLayouts: [...dashboardLayouts, layout] });
        }
      },

      addWidget: (widget) => {
        const { activeLayout } = get();
        if (!activeLayout) return;
        set({
          activeLayout: {
            ...activeLayout,
            widgets: [...activeLayout.widgets, widget],
            updatedAt: new Date(),
          },
        });
      },

      removeWidget: (widgetId) => {
        const { activeLayout } = get();
        if (!activeLayout) return;
        set({
          activeLayout: {
            ...activeLayout,
            widgets: activeLayout.widgets.filter((w) => w.id !== widgetId),
            updatedAt: new Date(),
          },
        });
      },

      updateWidgetPosition: (widgetId, position) => {
        const { activeLayout } = get();
        if (!activeLayout) return;
        set({
          activeLayout: {
            ...activeLayout,
            widgets: activeLayout.widgets.map((w) =>
              w.id === widgetId ? { ...w, position } : w
            ),
            updatedAt: new Date(),
          },
        });
      },

      setCustomizing: (isCustomizing) => set({ isCustomizing }),

      // ========================================================================
      // Query Actions
      // ========================================================================

      submitQuery: async (query) => {
        set({ isQueryLoading: true, currentQuery: query });
        try {
          await new Promise((resolve) => setTimeout(resolve, 1500));
          const response = createMockQueryResponse(query);
          const { queryHistory } = get();
          set({
            queryHistory: [response, ...queryHistory],
            isQueryLoading: false,
            currentQuery: "",
          });
        } catch {
          set({ isQueryLoading: false });
        }
      },

      setCurrentQuery: (query) => set({ currentQuery: query }),

      clearQueryHistory: () => set({ queryHistory: [] }),

      // ========================================================================
      // Filter Actions
      // ========================================================================

      setSelectedPeriod: (period) => set({ selectedPeriod: period }),

      setSelectedDepartment: (departmentId) => set({ selectedDepartment: departmentId }),

      setSelectedLocation: (locationId) => set({ selectedLocation: locationId }),

      setDateRange: (range) => set({ dateRange: range }),

      // ========================================================================
      // Refresh All
      // ========================================================================

      refreshAll: async () => {
        const { loadMetrics, loadCharts, loadInsights, loadAlerts, loadSentimentData } = get();
        set({ greeting: getGreeting() });
        await Promise.all([
          loadMetrics(),
          loadCharts(),
          loadInsights(),
          loadAlerts(),
          loadSentimentData(),
        ]);
        set({ lastRefresh: new Date() });
      },

      // ========================================================================
      // Reset
      // ========================================================================

      reset: () => set(initialState),

      // ========================================================================
      // Aliases for compatibility
      // ========================================================================

      setTimeRange: (range) => set({ selectedPeriod: range, timeRange: range }),

      fetchDashboardData: async () => {
        const { loadMetrics, loadCharts, loadInsights, loadAlerts, loadSentimentData } = get();
        set({ isLoading: true });
        await Promise.all([
          loadMetrics(),
          loadCharts(),
          loadInsights(),
          loadAlerts(),
          loadSentimentData(),
        ]);
        set({ isLoading: false, lastRefresh: new Date() });
      },
    })),
    { name: "analytics-store" }
  )
);

// ============================================================================
// Mock Data Generators
// ============================================================================

function createMockMetrics(): Metric[] {
  return [
    {
      id: "appointments-today",
      name: "Today's Appointments",
      value: 142,
      previousValue: 131,
      target: 150,
      format: "number",
      trend: "up",
      trendPercentage: 8.4,
      status: "good",
      lastUpdated: new Date(),
      sparklineData: generateSparklineData(30, 100, 160),
    },
    {
      id: "revenue-mtd",
      name: "Revenue (MTD)",
      value: 4520000,
      previousValue: 4100000,
      target: 5800000,
      unit: "₹",
      format: "currency",
      trend: "up",
      trendPercentage: 10.2,
      status: "good",
      lastUpdated: new Date(),
      sparklineData: generateSparklineData(30, 100000, 200000),
    },
    {
      id: "patient-satisfaction",
      name: "Patient Satisfaction",
      value: 4.6,
      previousValue: 4.4,
      target: 4.8,
      format: "rating",
      trend: "up",
      trendValue: 0.2,
      status: "good",
      lastUpdated: new Date(),
      sparklineData: generateSparklineData(30, 4.0, 5.0),
    },
    {
      id: "avg-wait-time",
      name: "Avg Wait Time",
      value: 18,
      previousValue: 23,
      target: 15,
      unit: "min",
      format: "duration",
      trend: "down",
      trendValue: -5,
      status: "good",
      lastUpdated: new Date(),
      sparklineData: generateSparklineData(30, 10, 30),
    },
    {
      id: "no-show-rate",
      name: "No-Show Rate",
      value: 12,
      previousValue: 10,
      target: 8,
      unit: "%",
      format: "percentage",
      trend: "up",
      trendPercentage: 20,
      status: "warning",
      benchmark: 10,
      lastUpdated: new Date(),
      sparklineData: generateSparklineData(30, 5, 15),
    },
    {
      id: "slot-utilization",
      name: "Slot Utilization",
      value: 85,
      previousValue: 82,
      target: 90,
      unit: "%",
      format: "percentage",
      trend: "up",
      trendPercentage: 3.7,
      status: "good",
      lastUpdated: new Date(),
      sparklineData: generateSparklineData(30, 70, 95),
    },
  ];
}

function createMockKPICards(metrics: Metric[]): KPICard[] {
  return [
    {
      id: "kpi-appointments",
      title: "Today's Appointments",
      metric: metrics.find((m) => m.id === "appointments-today")!,
      size: "medium",
      variant: "progress",
      icon: "calendar",
      drilldownPath: "/appointments",
    },
    {
      id: "kpi-revenue",
      title: "Revenue (MTD)",
      metric: metrics.find((m) => m.id === "revenue-mtd")!,
      size: "medium",
      variant: "progress",
      icon: "currency",
      drilldownPath: "/analytics/financial",
    },
    {
      id: "kpi-satisfaction",
      title: "Patient Satisfaction",
      metric: metrics.find((m) => m.id === "patient-satisfaction")!,
      size: "small",
      variant: "trend",
      icon: "star",
      drilldownPath: "/analytics/sentiment",
    },
    {
      id: "kpi-wait-time",
      title: "Avg Wait Time",
      metric: metrics.find((m) => m.id === "avg-wait-time")!,
      size: "small",
      variant: "simple",
      icon: "clock",
      drilldownPath: "/analytics/operations",
    },
    {
      id: "kpi-noshow",
      title: "No-Show Rate",
      metric: metrics.find((m) => m.id === "no-show-rate")!,
      size: "small",
      variant: "comparison",
      icon: "alert",
      drilldownPath: "/analytics/no-shows",
      actionLabel: "Analyze",
      actionType: "drill-down",
    },
    {
      id: "kpi-utilization",
      title: "Slot Utilization",
      metric: metrics.find((m) => m.id === "slot-utilization")!,
      size: "small",
      variant: "progress",
      icon: "gauge",
      drilldownPath: "/schedule",
    },
  ];
}

function createMockCharts(): ChartConfig[] {
  return [
    {
      id: "appointments-trend",
      title: "Appointment Volume - Last 30 Days",
      type: "area",
      data: generateSparklineData(30, 100, 160),
      showLegend: false,
      showGrid: true,
      period: "month",
      xLabel: "Date",
      yLabel: "Appointments",
      colors: ["#6366f1"],
    },
    {
      id: "revenue-by-dept",
      title: "Revenue by Department",
      type: "bar",
      data: [
        { date: new Date(), value: 3210000, label: "Cardiology" },
        { date: new Date(), value: 2580000, label: "Orthopedics" },
        { date: new Date(), value: 1720000, label: "General Med" },
        { date: new Date(), value: 1610000, label: "Pediatrics" },
        { date: new Date(), value: 1340000, label: "Dermatology" },
      ],
      comparisonData: [
        { date: new Date(), value: 2850000, label: "Cardiology" },
        { date: new Date(), value: 2420000, label: "Orthopedics" },
        { date: new Date(), value: 1870000, label: "General Med" },
        { date: new Date(), value: 1530000, label: "Pediatrics" },
        { date: new Date(), value: 1210000, label: "Dermatology" },
      ],
      showLegend: true,
      period: "quarter",
      xLabel: "Department",
      yLabel: "Revenue (₹)",
      colors: ["#6366f1", "#94a3b8"],
    },
    {
      id: "noshow-by-dept",
      title: "No-Show Rate by Department",
      type: "bar",
      data: [
        { date: new Date(), value: 22, label: "Pediatrics" },
        { date: new Date(), value: 14, label: "Orthopedics" },
        { date: new Date(), value: 12, label: "Cardiology" },
        { date: new Date(), value: 8, label: "General Med" },
        { date: new Date(), value: 6, label: "Dermatology" },
      ],
      benchmark: 10,
      showLegend: false,
      period: "month",
      xLabel: "Department",
      yLabel: "No-Show Rate (%)",
      colors: ["#ef4444", "#f97316", "#eab308", "#22c55e", "#22c55e"],
    },
  ];
}

function createMockInsights(): AIInsight[] {
  const now = new Date().toISOString();
  return [
    {
      id: "insight-1",
      type: "positive",
      title: "Cardiology revenue is 15% above target",
      description: "Strong performance driven by increased procedure volume and new patient referrals.",
      category: "revenue",
      sentiment: "positive",
      impact: "high",
      metric: "revenue-mtd",
      metrics: [
        { label: "Current Revenue", value: "₹32.1L", change: 12.6 },
        { label: "Target", value: "₹28L" },
      ],
      suggestedActions: [
        { id: "1", label: "Review capacity for expansion" },
        { id: "2", label: "Analyze referral sources" },
      ],
      createdAt: now,
      isRead: false,
    },
    {
      id: "insight-2",
      type: "warning",
      title: "Pediatrics no-show rate spiked to 22%",
      description: "No-show rate increased from 15% to 22% over the past 3 weeks.",
      category: "operations",
      sentiment: "warning",
      impact: "high",
      metric: "no-show-rate",
      metrics: [
        { label: "Current Rate", value: "22%", change: -7 },
        { label: "Benchmark", value: "10%" },
      ],
      suggestedActions: [
        { id: "3", label: "Enable WhatsApp reminders" },
        { id: "4", label: "Implement overbooking" },
        { id: "5", label: "Offer evening slots" },
      ],
      createdAt: now,
      isRead: false,
    },
    {
      id: "insight-3",
      type: "action",
      title: "3 high-risk patients identified",
      description: "Predictive model identified patients requiring proactive outreach.",
      category: "clinical",
      sentiment: "neutral",
      impact: "medium",
      suggestedActions: [
        { id: "6", label: "View patient list" },
        { id: "7", label: "Assign care coordinator" },
      ],
      createdAt: now,
      isRead: false,
    },
  ];
}

function createMockAlerts(): ProactiveAlert[] {
  const now = new Date().toISOString();
  return [
    {
      id: "alert-1",
      priority: "high",
      status: "active",
      title: "No-Show Prediction Alert",
      description: "8 appointments tomorrow flagged as 'High No-Show Risk'",
      source: "Predictive Analytics",
      type: "no_show_risk",
      affectedItems: [
        { id: "p1", name: "Rahul Verma", time: "9:00 AM", riskScore: 85, reason: "3 past no-shows" },
        { id: "p2", name: "Sunita Devi", time: "10:30 AM", riskScore: 78, reason: "Far distance" },
        { id: "p3", name: "Arun Kumar", time: "11:00 AM", riskScore: 75, reason: "First visit" },
        { id: "p4", name: "Meera Sharma", time: "2:00 PM", riskScore: 72, reason: "Weather alert" },
        { id: "p5", name: "Vijay Singh", time: "3:30 PM", riskScore: 70, reason: "Late booking" },
      ],
      suggestedAction: "Send WhatsApp confirmation request to all 8 patients",
      primaryAction: "Send Confirmations Now",
      secondaryAction: "Review List",
      createdAt: now,
    },
    {
      id: "alert-2",
      priority: "medium",
      status: "active",
      title: "Dr. Sharma has 3 cancellations tomorrow",
      description: "Freed up slots available for waitlisted patients",
      source: "Schedule Management",
      type: "cancellation",
      affectedItems: [
        { id: "s1", name: "Slot 1", time: "10:00 AM" },
        { id: "s2", name: "Slot 2", time: "11:30 AM" },
        { id: "s3", name: "Slot 3", time: "3:00 PM" },
      ],
      suggestedAction: "Notify waitlisted patients about available slots",
      primaryAction: "Notify Waitlist",
      secondaryAction: "Ignore",
      createdAt: now,
    },
    {
      id: "alert-3",
      priority: "low",
      status: "active",
      title: "Reception sentiment declining",
      description: "Patient satisfaction for reception dropped 15% this week",
      source: "Sentiment Analysis",
      type: "sentiment",
      suggestedAction: "Review recent feedback and identify improvement areas",
      primaryAction: "View Feedback",
      secondaryAction: "Dismiss",
      createdAt: now,
    },
  ];
}

function createMockSentimentData(): SentimentData[] {
  return [
    {
      id: "sent-cardiology",
      department: "Cardiology",
      score: 85,
      previousScore: 82,
      trend: "up",
      changePercent: 3,
      status: "good",
      topThemes: [
        { theme: "Doctor expertise", count: 45, sentiment: "positive" },
        { theme: "Wait times", count: 12, sentiment: "negative" },
      ],
    },
    {
      id: "sent-orthopedics",
      department: "Orthopedics",
      score: 82,
      previousScore: 81,
      trend: "up",
      changePercent: 1,
      status: "good",
      topThemes: [
        { theme: "Treatment outcome", count: 38, sentiment: "positive" },
        { theme: "Appointment availability", count: 8, sentiment: "negative" },
      ],
    },
    {
      id: "sent-pediatrics",
      department: "Pediatrics",
      score: 68,
      previousScore: 76,
      trend: "down",
      changePercent: -8,
      status: "warning",
      topThemes: [
        { theme: "Long wait times", count: 23, sentiment: "negative" },
        { theme: "Friendly staff", count: 15, sentiment: "positive" },
      ],
    },
    {
      id: "sent-general",
      department: "General Medicine",
      score: 78,
      previousScore: 80,
      trend: "down",
      changePercent: -2,
      status: "good",
      topThemes: [
        { theme: "Quick service", count: 28, sentiment: "positive" },
        { theme: "Crowded waiting area", count: 10, sentiment: "negative" },
      ],
    },
    {
      id: "sent-dermatology",
      department: "Dermatology",
      score: 90,
      previousScore: 85,
      trend: "up",
      changePercent: 5,
      status: "good",
      topThemes: [
        { theme: "Excellent results", count: 52, sentiment: "positive" },
        { theme: "Premium pricing", count: 5, sentiment: "neutral" },
      ],
    },
    {
      id: "sent-reception",
      department: "Reception",
      score: 52,
      previousScore: 67,
      trend: "down",
      changePercent: -15,
      status: "critical",
      topThemes: [
        { theme: "Long wait times", count: 23, sentiment: "negative" },
        { theme: "Rude staff", count: 8, sentiment: "negative" },
        { theme: "Billing confusion", count: 12, sentiment: "negative" },
      ],
    },
  ];
}

function createMockQueryResponse(query: string): AnalyticsQuery {
  return {
    id: `query-${Date.now()}`,
    query,
    response: {
      type: "mixed",
      content: {
        summary: `Analysis for: "${query}"`,
        data: generateSparklineData(12, 100, 200),
      },
      analysis: "Based on the data analysis, here are the key findings...",
      followUpQuestions: [
        "Show breakdown by department",
        "Compare with last quarter",
        "What's the forecast for next month?",
      ],
    },
    timestamp: new Date(),
  };
}

function generateSparklineData(count: number, min: number, max: number): DataPoint[] {
  const data: DataPoint[] = [];
  let value = (min + max) / 2;

  for (let i = count - 1; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);

    // Random walk with some trend
    value = Math.max(min, Math.min(max, value + (Math.random() - 0.45) * (max - min) * 0.1));

    data.push({
      date,
      value: Math.round(value * 100) / 100,
    });
  }

  return data;
}

// ============================================================================
// Selectors
// ============================================================================

export const selectMetrics = (state: AnalyticsState) => state.metrics;
export const selectKPICards = (state: AnalyticsState) => state.kpiCards;
export const selectCharts = (state: AnalyticsState) => state.charts;
export const selectInsights = (state: AnalyticsState) => state.insights;
export const selectUnreadInsights = (state: AnalyticsState) =>
  state.insights.filter((i) => !i.isRead);
export const selectAlerts = (state: AnalyticsState) => state.alerts;
export const selectActiveAlerts = (state: AnalyticsState) =>
  state.alerts.filter((a) => a.status === "active");
export const selectSentimentData = (state: AnalyticsState) => state.sentimentData;
export const selectCriticalSentiment = (state: AnalyticsState) =>
  state.sentimentData.filter((s) => s.status === "critical");
