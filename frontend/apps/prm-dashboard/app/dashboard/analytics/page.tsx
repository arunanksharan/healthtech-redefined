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

  // Generate mock time series data
  const appointmentTrendData = React.useMemo(() => {
    const data = [];
    for (let i = 29; i >= 0; i--) {
      const date = subDays(new Date(), i);
      data.push({
        date: date.toISOString(),
        value: Math.floor(100 + Math.random() * 60),
        label: format(date, "MMM d"),
      });
    }
    return data;
  }, []);

  // Generate mock department data
  const departmentRevenueData = React.useMemo(() => [
    { category: "Cardiology", value: 3210000, color: "#6366f1" },
    { category: "Orthopedics", value: 2580000, color: "#22c55e" },
    { category: "General Med", value: 1720000, color: "#f59e0b" },
    { category: "Pediatrics", value: 1610000, color: "#ec4899" },
    { category: "Dermatology", value: 1340000, color: "#8b5cf6" },
  ], []);

  const appointmentStatusData = React.useMemo(() => [
    { name: "Completed", value: 65, color: "#22c55e" },
    { name: "Scheduled", value: 20, color: "#6366f1" },
    { name: "Canceled", value: 10, color: "#ef4444" },
    { name: "No-Show", value: 5, color: "#f59e0b" },
  ], []);

  // Mock insights
  const mockInsights: AIInsight[] = React.useMemo(() => [
    {
      id: "1",
      title: "Cardiology revenue is 15% above target",
      description: "Cardiology department has exceeded revenue targets for the 3rd consecutive month, driven by increased referrals and new patient volume.",
      category: "revenue",
      sentiment: "positive",
      impact: "high",
      metrics: [
        { label: "Current Revenue", value: "₹32.1L", change: 12.6 },
        { label: "Target", value: "₹28L" },
      ],
      suggestedActions: [
        { id: "1", label: "View revenue breakdown" },
        { id: "2", label: "Analyze top procedures" },
      ],
      createdAt: new Date().toISOString(),
    },
    {
      id: "2",
      title: "Pediatrics no-show rate spiked to 22%",
      description: "No-show rate in Pediatrics increased significantly compared to last week. Contributing factors: first-time appointments and Monday mornings.",
      category: "operations",
      sentiment: "warning",
      impact: "high",
      metrics: [
        { label: "Current Rate", value: "22%", change: -7 },
        { label: "Benchmark", value: "10%" },
      ],
      suggestedActions: [
        { id: "3", label: "Enable WhatsApp reminders" },
        { id: "4", label: "View high-risk patients" },
      ],
      createdAt: new Date().toISOString(),
    },
    {
      id: "3",
      title: "3 high-risk patients identified for outreach",
      description: "AI has identified 3 patients with high readmission risk who may benefit from proactive outreach.",
      category: "clinical",
      sentiment: "neutral",
      impact: "medium",
      suggestedActions: [
        { id: "5", label: "View patient list" },
        { id: "6", label: "Schedule follow-ups" },
      ],
      createdAt: new Date().toISOString(),
    },
  ], []);

  // Mock alerts
  const mockAlerts: ProactiveAlert[] = React.useMemo(() => [
    {
      id: "1",
      title: "No-Show Prediction Alert",
      description: "8 appointments tomorrow flagged as 'High No-Show Risk' based on past behavior, distance, and weather forecast.",
      type: "no_show_risk",
      priority: "high",
      affectedItems: [
        { name: "Rahul Verma", time: "9:00 AM", riskScore: 85, reason: "3 past no-shows" },
        { name: "Sunita Devi", time: "10:30 AM", riskScore: 78, reason: "Far distance" },
        { name: "Amit Kumar", time: "11:00 AM", riskScore: 72, reason: "First visit" },
        { name: "Priya Sharma", time: "2:00 PM", riskScore: 68, reason: "Weather alert" },
      ],
      suggestedAction: "Send WhatsApp confirmation request to all 8 patients",
      primaryAction: "Send Confirmations Now",
      secondaryAction: "Review List",
      createdAt: new Date().toISOString(),
    },
    {
      id: "2",
      title: "Dr. Sharma has 3 cancellations tomorrow",
      description: "3 appointment slots became available due to last-minute cancellations.",
      type: "cancellation",
      priority: "medium",
      affectedItems: [
        { name: "Slot 1", time: "10:00 AM" },
        { name: "Slot 2", time: "11:30 AM" },
        { name: "Slot 3", time: "3:00 PM" },
      ],
      suggestedAction: "Notify waitlisted patients about available slots",
      primaryAction: "Notify Waitlist",
      secondaryAction: "Ignore",
      createdAt: new Date().toISOString(),
    },
  ], []);

  // Mock sentiment data
  const mockSentimentData: SentimentData = React.useMemo(() => ({
    overallScore: 76,
    previousScore: 78,
    totalFeedback: 1250,
    departments: [
      { id: "1", name: "Cardiology", score: 85, previousScore: 82, change: 3, totalFeedback: 180, sources: { voice: 45, whatsapp: 80, survey: 40, email: 15 }, topThemes: { positive: ["Friendly staff", "Quick service"], negative: ["Wait times"] } },
      { id: "2", name: "Orthopedics", score: 82, previousScore: 81, change: 1, totalFeedback: 150, sources: { voice: 30, whatsapp: 70, survey: 35, email: 15 }, topThemes: { positive: ["Expert care", "Clean facility"], negative: ["Parking"] } },
      { id: "3", name: "Pediatrics", score: 68, previousScore: 76, change: -8, totalFeedback: 200, sources: { voice: 60, whatsapp: 90, survey: 35, email: 15 }, topThemes: { positive: ["Child-friendly"], negative: ["Long wait", "Scheduling issues"] } },
      { id: "4", name: "General Med", score: 78, previousScore: 80, change: -2, totalFeedback: 300, sources: { voice: 80, whatsapp: 120, survey: 70, email: 30 }, topThemes: { positive: ["Convenient location"], negative: ["Crowded"] } },
      { id: "5", name: "Dermatology", score: 90, previousScore: 85, change: 5, totalFeedback: 120, sources: { voice: 25, whatsapp: 50, survey: 35, email: 10 }, topThemes: { positive: ["Professional", "Great results"], negative: [] } },
      { id: "6", name: "Reception", score: 52, previousScore: 67, change: -15, totalFeedback: 300, sources: { voice: 100, whatsapp: 80, survey: 80, email: 40 }, topThemes: { positive: [], negative: ["Long wait times", "Rude staff", "Billing confusion"] } },
    ],
  }), []);

  // Handle analytics query
  const handleAnalyticsQuery = async (query: string) => {
    // Mock response
    await new Promise((resolve) => setTimeout(resolve, 1500));
    return {
      type: "table" as const,
      content: {
        headers: ["Department", "Q3 2024", "Q4 2024", "Change", "Trend"],
        rows: [
          ["Cardiology", "₹28.5L", "₹32.1L", "+12.6%", "📈"],
          ["Orthopedics", "₹24.2L", "₹25.8L", "+6.6%", "📈"],
          ["General Med", "₹18.7L", "₹17.2L", "-8.0%", "📉"],
          ["Pediatrics", "₹15.3L", "₹16.1L", "+5.2%", "📈"],
          ["Dermatology", "₹12.1L", "₹13.4L", "+10.7%", "📈"],
        ],
      },
      insights: [
        "Overall revenue grew 5.9% quarter-over-quarter",
        "Cardiology is the top performer with 12.6% growth",
        "General Medicine declined 8% - warrants investigation",
      ],
      followUpQuestions: [
        "Why did General Medicine revenue decline?",
        "Show me Cardiology revenue breakdown by doctor",
        "What's the forecast for next quarter?",
      ],
    };
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
          <div className="flex items-center gap-2">
            <DashboardSelector
              currentPreset={dashboardPreset}
              onPresetChange={setDashboardPreset}
            />
            <Button variant="outline" size="icon" onClick={() => toast("Refreshed data")}>
              <RefreshCw className="h-4 w-4 text-gray-500" />
            </Button>
            <Button variant="outline" size="icon">
              <Download className="h-4 w-4 text-gray-500" />
            </Button>
          </div>
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
      </header>

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
                <NumberTicker value={142} />
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
                ₹<NumberTicker value={4520000} className="tabular-nums" />
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
              <span className="text-2xl font-bold text-foreground">4.6</span>
              <span className="text-xs text-muted-foreground mb-1">/ 5.0</span>
            </div>
            <div className="flex gap-0.5 mt-2">
              {[1, 2, 3, 4, 5].map(i => (
                <div key={i} className={cn("h-1 flex-1 rounded-full", i <= 4 ? "bg-purple-500" : "bg-purple-100")} />
              ))}
            </div>
          </MagicCard>

          <MagicCard className="bg-card border border-border shadow-sm p-5" gradientColor="#fff7ed">
            <div className="flex justify-between items-start mb-2">
              <p className="text-sm font-medium text-muted-foreground">No-Show Rate</p>
              <Activity className="h-4 w-4 text-orange-600" />
            </div>
            <div className="flex items-end gap-2">
              <span className="text-2xl font-bold text-foreground">12%</span>
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
              <span className="text-2xl font-bold text-foreground">8</span>
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
              centerValue="142"
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
    </div>
  );
}
