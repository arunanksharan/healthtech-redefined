// Analytics Components - Barrel Export
// EPIC-UX-006: Analytics & Intelligence Dashboard

// Stat Cards
export {
  SimpleStatCard,
  ProgressStatCard,
  TrendStatCard,
  ComparisonStatCard,
  ActionStatCard,
  StatCardSkeleton,
  StatCardsGrid,
} from "./stat-cards";
export type { StatStatus, TrendDirection } from "./stat-cards";

// Charts
export {
  TimeSeriesChart,
  BarChart,
  Heatmap,
  DonutChart,
  ChartSkeleton,
} from "./charts";
export type {
  TimeSeriesDataPoint,
  TimeSeriesChartProps,
  BarChartDataPoint,
  BarChartProps,
  HeatmapDataPoint,
  HeatmapProps,
  DonutChartDataPoint,
  DonutChartProps,
} from "./charts";

// AI Insights
export {
  AIInsightCard,
  AIInsightsPanel,
  AIInsightsExpanded,
} from "./ai-insights-panel";
export type {
  InsightCategory,
  InsightSentiment,
  InsightImpact,
  AIInsightCardProps,
  AIInsightsPanelProps,
  AIInsightsExpandedProps,
} from "./ai-insights-panel";

// Proactive Alerts
export {
  ProactiveAlertCard,
  ProactiveAlertsPanel,
  AlertDetailDialog,
  AlertBadge,
} from "./proactive-alerts";
export type {
  AlertPriority,
  AlertType,
  AlertPatient,
  ProactiveAlertCardProps,
  ProactiveAlertsPanelProps,
  AlertDetailDialogProps,
  AlertBadgeProps,
} from "./proactive-alerts";

// Sentiment Heatmap
export {
  SentimentHeatmap,
  SentimentSummary,
} from "./sentiment-heatmap";
export type {
  SentimentLevel,
  SentimentDepartment,
  FeedbackItem,
  SentimentHeatmapProps,
  SentimentSummaryProps,
} from "./sentiment-heatmap";

// Dashboard Layout
export {
  DashboardWidgetWrapper,
  BentoGridLayout,
  DashboardHeader,
  WidgetLibraryDialog,
  DashboardSelector,
  DASHBOARD_PRESETS,
} from "./dashboard-layout";
export type { WidgetSize, DashboardWidgetConfig, AvailableWidget } from "./dashboard-layout";

// Analytics Query
export {
  AnalyticsQueryInput,
  QueryResponseDisplay,
  AnalyticsAssistantDialog,
  CompactQueryWidget,
} from "./analytics-query";
export type {
  QueryResponseType,
  QueryResponse,
  QueryHistoryItem,
} from "./analytics-query";
