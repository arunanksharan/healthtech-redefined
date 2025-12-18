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
import { useToast } from "@/hooks/use-toast";
import { Skeleton } from "@/components/ui/skeleton";

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
  const { toast } = useToast();
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
      {/* Flat Header */}
      <header className="sticky top-0 z-30 flex flex-col gap-4 p-6 bg-white dark:bg-gray-900 border-b-2 border-gray-100 dark:border-gray-800">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-heading text-gray-900 dark:text-white">{getGreeting()}</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Here's your practice analytics overview</p>
          </div>
          <Button
            variant="outline"
            size="icon"
            onClick={() => {
              refetch();
              toast({ title: "Refreshed", description: "Dashboard data updated" });
            }}
            disabled={isLoading}
            className="border-2 border-gray-200 dark:border-gray-600 rounded-lg"
          >
            <RefreshCw className={cn("h-4 w-4 text-gray-500", isLoading && "animate-spin")} />
          </Button>
        </div>

        {/* Time Period Selector */}
        <div className="flex items-center gap-1.5 p-1 bg-gray-100 dark:bg-gray-800 border-2 border-gray-200 dark:border-gray-700 rounded-lg overflow-x-auto max-w-full">
          {TIME_PERIODS.map((period) => (
            <button
              key={period.value}
              onClick={() => setTimePeriod(period.value)}
              className={cn(
                "px-3 py-1.5 text-xs font-medium rounded-md transition-all whitespace-nowrap",
                timePeriod === period.value
                  ? "bg-white dark:bg-gray-900 text-blue-600 dark:text-blue-400"
                  : "text-gray-500 hover:bg-gray-200/50 dark:hover:bg-gray-700/50 hover:text-gray-900 dark:hover:text-white"
              )}
            >
              {period.label}
            </button>
          ))}
        </div>
      </header>

      <div className="p-6 space-y-6">
        {/* Row 1: Flat KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {/* Total Appointments */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-200 dark:border-blue-800 rounded-lg p-4 transition-all hover:scale-[1.02]">
            <div className="flex justify-between items-start mb-2">
              <p className="text-xs font-medium text-gray-600 dark:text-gray-400">Appointments</p>
              <Calendar className="h-5 w-5 text-blue-500" />
            </div>
            <span className="text-3xl font-bold text-blue-600 dark:text-blue-400">
              {kpi.totalAppointments}
            </span>
          </div>

          {/* Completion Rate */}
          <div className="bg-emerald-50 dark:bg-emerald-900/20 border-2 border-emerald-200 dark:border-emerald-800 rounded-lg p-4 transition-all hover:scale-[1.02]">
            <div className="flex justify-between items-start mb-2">
              <p className="text-xs font-medium text-gray-600 dark:text-gray-400">Completion Rate</p>
              <CheckCircle2 className="h-5 w-5 text-emerald-500" />
            </div>
            <div className="flex items-end gap-1">
              <span className="text-3xl font-bold text-emerald-600 dark:text-emerald-400">{kpi.completionRate}</span>
              <span className="text-sm text-gray-500 mb-0.5">%</span>
            </div>
          </div>

          {/* Cancellation Rate */}
          <div className="bg-red-50 dark:bg-red-900/20 border-2 border-red-200 dark:border-red-800 rounded-lg p-4 transition-all hover:scale-[1.02]">
            <div className="flex justify-between items-start mb-2">
              <p className="text-xs font-medium text-gray-600 dark:text-gray-400">Cancellation Rate</p>
              <XCircle className="h-5 w-5 text-red-500" />
            </div>
            <div className="flex items-end gap-1">
              <span className="text-3xl font-bold text-red-600 dark:text-red-400">{kpi.cancellationRate}</span>
              <span className="text-sm text-gray-500 mb-0.5">%</span>
            </div>
          </div>

          {/* No-Show Rate */}
          <div className="bg-orange-50 dark:bg-orange-900/20 border-2 border-orange-200 dark:border-orange-800 rounded-lg p-4 transition-all hover:scale-[1.02]">
            <div className="flex justify-between items-start mb-2">
              <p className="text-xs font-medium text-gray-600 dark:text-gray-400">No-Show Rate</p>
              <Activity className="h-5 w-5 text-orange-500" />
            </div>
            <div className="flex items-end gap-1">
              <span className="text-3xl font-bold text-orange-600 dark:text-orange-400">{kpi.noShowRate}</span>
              <span className="text-sm text-gray-500 mb-0.5">%</span>
            </div>
          </div>

          {/* Total Patients */}
          <div className="bg-purple-50 dark:bg-purple-900/20 border-2 border-purple-200 dark:border-purple-800 rounded-lg p-4 transition-all hover:scale-[1.02]">
            <div className="flex justify-between items-start mb-2">
              <p className="text-xs font-medium text-gray-600 dark:text-gray-400">Total Patients</p>
              <Users className="h-5 w-5 text-purple-500" />
            </div>
            <span className="text-3xl font-bold text-purple-600 dark:text-purple-400">
              {kpi.totalPatients}
            </span>
          </div>

          {/* New Patients */}
          <div className="bg-teal-50 dark:bg-teal-900/20 border-2 border-teal-200 dark:border-teal-800 rounded-lg p-4 transition-all hover:scale-[1.02]">
            <div className="flex justify-between items-start mb-2">
              <p className="text-xs font-medium text-gray-600 dark:text-gray-400">New Patients</p>
              <UserPlus className="h-5 w-5 text-teal-500" />
            </div>
            <span className="text-3xl font-bold text-teal-600 dark:text-teal-400">
              {kpi.newPatients}
            </span>
          </div>
        </div>


        {/* Row 2: Main Chart */}
        <TimeSeriesChart
          title="Appointment Volume"
          description="Daily appointment trends over the selected period"
          data={appointmentTrendData}
          type="area"
          period="day"
          onExport={() => toast({ title: "Exporting", description: "Your export is being prepared" })}
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
            onExport={() => toast({ title: "Exporting", description: "Your export is being prepared" })}
            isLoading={isLoading}
          />
        </div>

        {/* Row 4: Coming Soon */}
        <Card className="border-2 border-dashed border-gray-200 dark:border-gray-700">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <span className="text-gray-500 dark:text-gray-400">More Analytics Coming Soon</span>
              <Badge variant="outline" className="text-amber-600 border-amber-200 bg-amber-50">
                In Development
              </Badge>
            </CardTitle>
            <CardDescription>
              Journey analytics, communication metrics, and voice call analytics will be available once the respective features are implemented.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-500">
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
    </div >
  );
}
