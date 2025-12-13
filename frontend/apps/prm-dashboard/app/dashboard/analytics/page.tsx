"use client";

import * as React from "react";
import {
  Calendar,
  Users,
  DollarSign,
  Clock,
  Activity,
  Download,
  RefreshCw,
  ChevronDown,
  Sparkles,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Target,
  Star,
  Search,
  Filter,
} from "lucide-react";
import { format, subDays } from "date-fns";
import toast from "react-hot-toast";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { MagicCard } from "@/components/ui/magic-card";
import { NumberTicker } from "@/components/ui/number-ticker";
import { BorderBeam } from "@/components/ui/border-beam";
import { cn } from '@/lib/utils/cn';

// Analytics Components
import {
  TimeSeriesChart,
  BarChart,
  DonutChart,
  AIInsightsPanel,
  ProactiveAlertsPanel,
  SentimentHeatmap,
  DashboardSelector,
  AnalyticsQueryInput,
  AnalyticsAssistantDialog,
} from "@/components/analytics";

import { useAnalyticsStore } from "@/lib/store/analytics-store";
import type { AIInsight, ProactiveAlert, SentimentData } from "@/lib/store/analytics-store";
import { useQuery } from "@tanstack/react-query";
import { analyticsAPI } from "@/lib/api/analytics";

// ============================================================================
// Types & Constants
// ============================================================================

type TimePeriod = "today" | "yesterday" | "last_7_days" | "last_30_days" | "this_month" | "this_quarter";

const TIME_PERIODS: { value: TimePeriod; label: string }[] = [
  { value: "today", label: "Today" },
  { value: "yesterday", label: "Yesterday" },
  { value: "last_7_days", label: "Last 7 Days" },
  { value: "last_30_days", label: "Last 30 Days" },
  { value: "this_month", label: "This Month" },
  { value: "this_quarter", label: "This Quarter" },
];

// ============================================================================
// Main Analytics Dashboard Page
// ============================================================================

export default function AnalyticsDashboardPage() {
  const [timePeriod, setTimePeriod] = React.useState<TimePeriod>("last_30_days");
  const [dashboardPreset, setDashboardPreset] = React.useState("executive");
  const [showQueryDialog, setShowQueryDialog] = React.useState(false);

  // Get data from store
  const {
    dismissAlert,
  } = useAnalyticsStore();

  // Fetch Analytics Data
  const { data: analyticsData, isLoading } = useQuery({
    queryKey: ['analytics-dashboard', timePeriod],
    queryFn: async () => {
      const [data, error] = await analyticsAPI.getDashboardData(timePeriod);
      if (error) throw new Error(error.message);
      return data;
    },
  });

  // Derived data with failovers for initial render
  const appointmentTrendData = analyticsData?.appointmentTrend || [];
  const departmentRevenueData = analyticsData?.revenueData || [];
  const appointmentStatusData = analyticsData?.appointmentStatus || [];
  const mockInsights = analyticsData?.insights || [];
  const mockAlerts = analyticsData?.alerts || [];
  const mockSentimentData = analyticsData?.sentiment || {
    overallScore: 0,
    previousScore: 0,
    totalFeedback: 0,
    departments: []
  };

  const kpi = analyticsData?.kpi || {
    totalAppointments: 0,
    revenue: 0,
    patientSatisfaction: 0,
    noShowRate: 0,
    riskAlerts: 0
  };



  // Handle analytics query
  const handleAnalyticsQuery = async (query: string) => {
    // Call Stub API
    return await analyticsAPI.askAI(query);
  };

  // Handle alert actions
  const handleAlertAction = (alertId: string, action: "primary" | "secondary" | "dismiss" | "review") => {
    if (action === "dismiss") {
      dismissAlert(alertId);
      toast.success("Alert dismissed");
    } else if (action === "primary") {
      toast.success("Action initiated successfully");
    }
  };

  // Get greeting based on time of day
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 17) return "Good afternoon";
    return "Good evening";
  };

  return (
    <div className="flex flex-col min-h-screen">
      {/* Sticky Glassmorphic Header */}
      <header className="sticky top-0 z-30 flex flex-col gap-4 p-6 bg-background/80 backdrop-blur-md border-b border-border/50 supports-[backdrop-filter]:bg-background/60 transition-all">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground tracking-tight">{getGreeting()}</h1>
            <p className="text-sm text-muted-foreground mt-1">Here's your daily practice intelligence briefing</p>
          </div>
          <Button variant="outline" size="icon" onClick={() => toast("Refreshed data")}>
            <RefreshCw className="h-4 w-4 text-gray-500" />
          </Button>
        </div>


        {/* Controls Row */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          {/* Time Period Selector */}
          <div className="flex items-center gap-1.5 p-1 bg-muted/50 rounded-lg overflow-x-auto max-w-full">
            {TIME_PERIODS.map((period) => (
              <button
                key={period.value}
                onClick={() => setTimePeriod(period.value)}
                className={cn(
                  "px-3 py-1.5 text-xs font-medium rounded-md transition-all whitespace-nowrap",
                  timePeriod === period.value
                    ? "bg-background text-blue-700 shadow-sm ring-1 ring-border"
                    : "text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                )}
              >
                {period.label}
              </button>
            ))}
          </div>

          <div className="w-full md:w-auto flex-1 md:max-w-md">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Ask analytics..."
                className="pl-9 h-9 bg-muted/50 border-border focus:bg-background transition-all shadow-sm"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') setShowQueryDialog(true);
                }}
              />
            </div>
          </div>
        </div>
      </header >

      <div className="p-6 space-y-6">
        {/* Magic KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <MagicCard className="bg-card border border-border shadow-sm p-5" gradientColor="#eff6ff">
            <div className="flex justify-between items-start mb-2">
              <p className="text-sm font-medium text-muted-foreground">Today's Appointments</p>
              <Calendar className="h-4 w-4 text-blue-600" />
            </div>
            <div className="flex items-end gap-2">
              <span className="text-2xl font-bold text-foreground">
                <NumberTicker value={kpi.totalAppointments} />
              </span>
              <div className="flex items-center text-xs text-green-600 mb-1">
                <TrendingUp className="w-3 h-3 mr-0.5" />
                <span>+8%</span>
              </div>
            </div>
          </MagicCard>

          <MagicCard className="bg-card border border-border shadow-sm p-5" gradientColor="#f0fdf4">
            <div className="flex justify-between items-start mb-2">
              <p className="text-sm font-medium text-muted-foreground">Revenue (MTD)</p>
              <DollarSign className="h-4 w-4 text-green-600" />
            </div>
            <div className="flex items-end gap-2">
              <span className="text-2xl font-bold text-foreground">
                ₹<NumberTicker value={kpi.revenue} className="tabular-nums" />
              </span>
            </div>
            <div className="w-full bg-muted h-1 mt-2 rounded-full overflow-hidden">
              <div className="bg-green-500 h-full rounded-full" style={{ width: '78%' }} />
            </div>
            <p className="text-[10px] text-muted-foreground mt-1">78% of monthly target</p>
          </MagicCard>

          <MagicCard className="bg-card border border-border shadow-sm p-5" gradientColor="#faf5ff">
            <div className="flex justify-between items-start mb-2">
              <p className="text-sm font-medium text-muted-foreground">Patient Satisfaction</p>
              <Star className="h-4 w-4 text-purple-600" />
            </div>
            <div className="flex items-end gap-2">
              <span className="text-2xl font-bold text-foreground">{kpi.patientSatisfaction}</span>
              <span className="text-xs text-muted-foreground mb-1">/ 5.0</span>
            </div>
            <div className="flex gap-0.5 mt-2">
              {[1, 2, 3, 4, 5].map(i => (
                <div key={i} className={cn("h-1 flex-1 rounded-full", i <= Math.round(kpi.patientSatisfaction) ? "bg-purple-500" : "bg-purple-100")} />
              ))}
            </div>
          </MagicCard>

          <MagicCard className="bg-card border border-border shadow-sm p-5" gradientColor="#fff7ed">
            <div className="flex justify-between items-start mb-2">
              <p className="text-sm font-medium text-muted-foreground">No-Show Rate</p>
              <Activity className="h-4 w-4 text-orange-600" />
            </div>
            <div className="flex items-end gap-2">
              <span className="text-2xl font-bold text-foreground">{kpi.noShowRate}%</span>
              <Badge variant="outline" className="text-[10px] border-orange-200 text-orange-700 bg-orange-50">
                High
              </Badge>
            </div>
            <p className="text-[10px] text-muted-foreground mt-2">Benchmark: 10%</p>
          </MagicCard>

          <MagicCard className="bg-card border border-border shadow-sm p-5" gradientColor="#fef2f2">
            <div className="flex justify-between items-start mb-2">
              <p className="text-sm font-medium text-muted-foreground">Risk Alerts</p>
              <AlertTriangle className="h-4 w-4 text-red-600" />
            </div>
            <div className="flex items-end gap-2">
              <span className="text-2xl font-bold text-foreground">{kpi.riskAlerts}</span>
              <span className="text-xs text-muted-foreground mb-1">Patients</span>
            </div>
            <Button size="sm" variant="ghost" className="h-6 text-[10px] w-full mt-2 -ml-2 text-red-600 hover:text-red-700 hover:bg-red-50/10">
              View List
            </Button>
          </MagicCard>
        </div>

        {/* AI Insights & Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            {/* Main Trend Chart */}
            <TimeSeriesChart
              title="Appointment Volume"
              description="Daily appointment trends over the last 30 days"
              data={appointmentTrendData}
              type="area"
              period="day"
              benchmark={120}
              benchmarkLabel="Target"
              onPeriodChange={(p) => toast(`Period: ${p}`)}
              onExport={() => toast("Exporting...")}
            />

            {/* Secondary Charts */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <BarChart
                title="Revenue by Department"
                description="Q4 2024 revenue breakdown"
                data={departmentRevenueData}
                orientation="horizontal"
                sortBy="value"
                height={300}
                onExport={() => toast("Exporting...")}
              />
              <ProactiveAlertsPanel
                alerts={mockAlerts}
                title="Proactive Alerts"
                maxVisible={3}
                showFilters
                onAlertAction={handleAlertAction}
                onSeeAll={() => toast("View all alerts")}
                onSettings={() => toast("Alert settings")}
              />
            </div>
          </div>

          <div className="space-y-6">
            {/* AI Insights Panel with Border Beam */}
            <div className="relative rounded-xl overflow-hidden shadow-sm bg-card group">
              <AIInsightsPanel
                insights={mockInsights}
                title="AI Insights"
                maxVisible={4}
                onSeeAll={() => toast("View all insights")}
                onInsightAction={(insightId, action) => toast(`Action: ${action} on insight ${insightId}`)}
                onRefresh={() => toast("Refreshing insights...")}
                className="border-none shadow-none bg-transparent"
              />

              <BorderBeam
                duration={8}
                size={200}
                borderWidth={2}
                colorFrom="#3b82f6"
                colorTo="#a855f7"
                className="z-10 pointer-events-none"
              />

              <div className="absolute inset-0 rounded-xl border border-border pointer-events-none" />
            </div>

            <DonutChart
              title="Appointment Status"
              description="Distribution by status"
              data={appointmentStatusData}
              centerValue={kpi.totalAppointments.toString()}
              centerLabel="Total"
            />
          </div>
        </div>

        {/* Sentiment Heatmap */}
        <SentimentHeatmap
          data={mockSentimentData}
          title="Patient Sentiment Analyis"
          description="Data sources: Zoice Calls, WhatsApp Messages, Post-Visit Surveys"
          period="7d"
          onPeriodChange={(p) => toast(`Period: ${p}`)}
          onDepartmentClick={(dept) => toast(`Viewing ${dept.name} details`)}
          onExport={() => toast("Exporting sentiment data...")}
          onRefresh={() => toast("Refreshing...")}
        />

        {/* Analytics Assistant Dialog */}
        <AnalyticsAssistantDialog
          isOpen={showQueryDialog}
          onClose={() => setShowQueryDialog(false)}
          onQuery={handleAnalyticsQuery}
        />
      </div>
    </div >
  );
}
