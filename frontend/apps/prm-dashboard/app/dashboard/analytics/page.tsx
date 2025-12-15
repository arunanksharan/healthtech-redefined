"use client";

import * as React from "react";
import {
  Calendar,
  Activity,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Users,
  UserPlus,
} from "lucide-react";
import toast from "react-hot-toast";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { MagicCard } from "@/components/ui/magic-card";
import { NumberTicker } from "@/components/ui/number-ticker";
import { cn } from '@/lib/utils/cn';

// Analytics Components
import {
  TimeSeriesChart,
  BarChart,
  DonutChart,
} from "@/components/analytics";

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

  // Fetch Analytics Data from API
  const { data: analyticsData, isLoading, refetch } = useQuery({
    queryKey: ['analytics-dashboard', timePeriod],
    queryFn: async () => {
      const [data, error] = await analyticsAPI.getDashboardData(timePeriod);
      if (error) throw new Error(error.message);
      return data;
    },
  });

  // Derived data with defaults
  const appointmentTrendData = analyticsData?.appointmentTrend || [];
  const appointmentStatusData = analyticsData?.appointmentStatus || [];
  const appointmentsByChannelData = analyticsData?.appointmentsByChannel || [];

  const kpi = {
    totalAppointments: analyticsData?.kpi?.totalAppointments || 0,
    noShowRate: analyticsData?.kpi?.noShowRate || 0,
    completionRate: analyticsData?.kpi?.completionRate || 0,
    cancellationRate: analyticsData?.kpi?.cancellationRate || 0,
    riskAlerts: analyticsData?.kpi?.riskAlerts || 0,
    totalPatients: analyticsData?.kpi?.totalPatients || 0,
    newPatients: analyticsData?.kpi?.newPatients || 0,
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
            <p className="text-sm text-muted-foreground mt-1">Here's your practice analytics overview</p>
          </div>
          <Button
            variant="outline"
            size="icon"
            onClick={() => {
              refetch();
              toast.success("Refreshed data");
            }}
            disabled={isLoading}
          >
            <RefreshCw className={cn("h-4 w-4 text-gray-500", isLoading && "animate-spin")} />
          </Button>
        </div>

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
      </header>

      <div className="p-6 space-y-6">
        {/* Row 1: KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {/* Total Appointments */}
          <MagicCard className="bg-card border border-border shadow-sm p-4" gradientColor="#eff6ff">
            <div className="flex justify-between items-start mb-2">
              <p className="text-xs font-medium text-muted-foreground">Appointments</p>
              <Calendar className="h-4 w-4 text-blue-600" />
            </div>
            <span className="text-2xl font-bold text-foreground">
              <NumberTicker value={kpi.totalAppointments} />
            </span>
          </MagicCard>

          {/* Completion Rate */}
          <MagicCard className="bg-card border border-border shadow-sm p-4" gradientColor="#f0fdf4">
            <div className="flex justify-between items-start mb-2">
              <p className="text-xs font-medium text-muted-foreground">Completion Rate</p>
              <CheckCircle2 className="h-4 w-4 text-green-600" />
            </div>
            <div className="flex items-end gap-1">
              <span className="text-2xl font-bold text-foreground">{kpi.completionRate}</span>
              <span className="text-sm text-muted-foreground mb-0.5">%</span>
            </div>
          </MagicCard>

          {/* Cancellation Rate */}
          <MagicCard className="bg-card border border-border shadow-sm p-4" gradientColor="#fef2f2">
            <div className="flex justify-between items-start mb-2">
              <p className="text-xs font-medium text-muted-foreground">Cancellation Rate</p>
              <XCircle className="h-4 w-4 text-red-600" />
            </div>
            <div className="flex items-end gap-1">
              <span className="text-2xl font-bold text-foreground">{kpi.cancellationRate}</span>
              <span className="text-sm text-muted-foreground mb-0.5">%</span>
            </div>
          </MagicCard>

          {/* No-Show Rate */}
          <MagicCard className="bg-card border border-border shadow-sm p-4" gradientColor="#fff7ed">
            <div className="flex justify-between items-start mb-2">
              <p className="text-xs font-medium text-muted-foreground">No-Show Rate</p>
              <Activity className="h-4 w-4 text-orange-600" />
            </div>
            <div className="flex items-end gap-1">
              <span className="text-2xl font-bold text-foreground">{kpi.noShowRate}</span>
              <span className="text-sm text-muted-foreground mb-0.5">%</span>
            </div>
          </MagicCard>

          {/* Total Patients */}
          <MagicCard className="bg-card border border-border shadow-sm p-4" gradientColor="#faf5ff">
            <div className="flex justify-between items-start mb-2">
              <p className="text-xs font-medium text-muted-foreground">Total Patients</p>
              <Users className="h-4 w-4 text-purple-600" />
            </div>
            <span className="text-2xl font-bold text-foreground">
              <NumberTicker value={kpi.totalPatients} />
            </span>
          </MagicCard>

          {/* New Patients */}
          <MagicCard className="bg-card border border-border shadow-sm p-4" gradientColor="#ecfdf5">
            <div className="flex justify-between items-start mb-2">
              <p className="text-xs font-medium text-muted-foreground">New Patients</p>
              <UserPlus className="h-4 w-4 text-emerald-600" />
            </div>
            <span className="text-2xl font-bold text-foreground">
              <NumberTicker value={kpi.newPatients} />
            </span>
          </MagicCard>
        </div>

        {/* Row 2: Main Chart */}
        <TimeSeriesChart
          title="Appointment Volume"
          description="Daily appointment trends over the selected period"
          data={appointmentTrendData}
          type="area"
          period="day"
          onExport={() => toast("Exporting...")}
          isLoading={isLoading}
        />

        {/* Row 3: Breakdown Charts */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Appointment Status Donut */}
          <DonutChart
            title="Appointment Status"
            description="Distribution by current status"
            data={appointmentStatusData}
            centerValue={kpi.totalAppointments.toString()}
            centerLabel="Total"
            isLoading={isLoading}
          />

          {/* Appointments by Channel */}
          <BarChart
            title="Appointments by Source"
            description="Booking channel distribution"
            data={appointmentsByChannelData}
            orientation="horizontal"
            sortBy="value"
            height={280}
            onExport={() => toast("Exporting...")}
            isLoading={isLoading}
          />
        </div>

        {/* Row 4: Coming Soon */}
        <Card className="border-2 border-dashed">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <span className="text-muted-foreground">More Analytics Coming Soon</span>
              <Badge variant="outline" className="text-amber-600 border-amber-200 bg-amber-50">
                In Development
              </Badge>
            </CardTitle>
            <CardDescription>
              Journey analytics, communication metrics, and voice call analytics will be available once the respective features are implemented.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-gray-300" />
                Journey Analytics
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-gray-300" />
                Communication Metrics
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-gray-300" />
                Voice Call Analytics
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-gray-300" />
                AI Insights
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
