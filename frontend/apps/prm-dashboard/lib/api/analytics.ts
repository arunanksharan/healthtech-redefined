import { apiClient, apiCall } from './client';
import { subDays, format } from 'date-fns';

// ============================================================================
// Types matching backend DashboardOverviewResponse
// ============================================================================

interface AppointmentMetrics {
  total_appointments: number;
  scheduled: number;
  confirmed: number;
  completed: number;
  canceled: number;
  no_show: number;
  rescheduled: number;
  no_show_rate: number;
  completion_rate: number;
  cancellation_rate: number;
  trend: Array<{ date: string; value: number }>;
}

interface AppointmentBreakdown {
  by_channel: Record<string, number>;
  by_practitioner: Record<string, number>;
  by_department: Record<string, number>;
  by_location: Record<string, number>;
  by_hour_of_day: Record<string, number>;
  by_day_of_week: Record<string, number>;
}

interface PatientMetrics {
  total_patients: number;
  new_patients: number;
  active_patients: number;
  inactive_patients: number;
  high_risk_patients: number;
}

interface BackendDashboardResponse {
  appointments: AppointmentMetrics;
  journeys: any;
  communication: any;
  voice_calls: any;
  patients: PatientMetrics;
  generated_at: string;
  time_period: string;
  start_date: string;
  end_date: string;
}

interface BackendAppointmentAnalyticsResponse {
  summary: AppointmentMetrics;
  breakdown: AppointmentBreakdown | null;
  time_period: string;
  start_date: string;
  end_date: string;
}

// Frontend-friendly format
export interface AnalyticsDashboardData {
  // Trend chart
  appointmentTrend: Array<{ date: string; value: number; label: string }>;

  // Appointment status breakdown (for donut chart)
  appointmentStatus: Array<{ name: string; value: number; color: string }>;

  // Channel breakdown (for bar chart)
  appointmentsByChannel: Array<{ name: string; value: number; color: string }>;

  // KPIs
  kpi: {
    totalAppointments: number;
    noShowRate: number;
    completionRate: number;
    cancellationRate: number;
    riskAlerts: number;
    totalPatients: number;
    newPatients: number;
  };
}

// ============================================================================
// Transform backend response to frontend format
// ============================================================================

function transformDashboardResponse(backend: BackendDashboardResponse): AnalyticsDashboardData {
  const appt = backend.appointments;

  // Transform trend data
  const trendData = appt.trend?.map((t) => ({
    date: t.date,
    value: t.value,
    label: format(new Date(t.date), "MMM d")
  })) || [];

  // If no trend data, generate placeholder
  if (trendData.length === 0) {
    for (let i = 29; i >= 0; i--) {
      const date = subDays(new Date(), i);
      trendData.push({
        date: date.toISOString(),
        value: 0,
        label: format(date, "MMM d"),
      });
    }
  }

  // Appointment status for donut chart
  const appointmentStatus = [
    { name: "Completed", value: appt.completed || 0, color: "#22c55e" },
    { name: "Scheduled", value: appt.scheduled || 0, color: "#3b82f6" },
    { name: "Confirmed", value: appt.confirmed || 0, color: "#6366f1" },
    { name: "Cancelled", value: appt.canceled || 0, color: "#ef4444" },
    { name: "No Show", value: appt.no_show || 0, color: "#f59e0b" },
  ].filter(s => s.value > 0); // Only show statuses with values

  return {
    appointmentTrend: trendData,
    appointmentStatus,
    appointmentsByChannel: [], // Will be populated by separate API call
    kpi: {
      totalAppointments: appt.total_appointments || 0,
      noShowRate: appt.no_show_rate || 0,
      completionRate: appt.completion_rate || 0,
      cancellationRate: appt.cancellation_rate || 0,
      riskAlerts: backend.patients?.high_risk_patients || 0,
      totalPatients: backend.patients?.total_patients || 0,
      newPatients: backend.patients?.new_patients || 0,
    }
  };
}

function transformAppointmentAnalytics(backend: BackendAppointmentAnalyticsResponse): Partial<AnalyticsDashboardData> {
  const channelColors: Record<string, string> = {
    web: "#3b82f6",
    whatsapp: "#22c55e",
    phone: "#f59e0b",
    voice_agent: "#8b5cf6",
    callcenter: "#ec4899",
    unknown: "#94a3b8",
  };

  const channelData = Object.entries(backend.breakdown?.by_channel || {}).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value,
    color: channelColors[name.toLowerCase()] || "#94a3b8"
  }));

  return {
    appointmentsByChannel: channelData,
  };
}

// ============================================================================
// Analytics API Client
// ============================================================================

export const analyticsAPI = {
  /**
   * Get dashboard metrics from backend API
   */
  async getDashboardData(timePeriod: string = 'last_30_days'): Promise<readonly [AnalyticsDashboardData | null, Error | null]> {
    try {
      const tenantId = typeof window !== 'undefined'
        ? localStorage.getItem('org_id') || '00000000-0000-0000-0000-000000000001'
        : '00000000-0000-0000-0000-000000000001';

      // Fetch both dashboard and appointments analytics in parallel
      const [dashboardResult, appointmentsResult] = await Promise.all([
        apiCall<BackendDashboardResponse>(
          apiClient.get(`/api/v1/prm/analytics/dashboard?tenant_id=${tenantId}&time_period=${timePeriod}`)
        ),
        apiCall<BackendAppointmentAnalyticsResponse>(
          apiClient.get(`/api/v1/prm/analytics/appointments?tenant_id=${tenantId}&time_period=${timePeriod}&include_breakdown=true`)
        ),
      ]);

      const [dashboardData, dashboardError] = dashboardResult;
      const [appointmentsData, appointmentsError] = appointmentsResult;

      if (!dashboardError && dashboardData) {
        // Transform dashboard data
        const transformedData = transformDashboardResponse(dashboardData);

        // Add channel breakdown from appointments API
        if (!appointmentsError && appointmentsData) {
          const appointmentsExtras = transformAppointmentAnalytics(appointmentsData);
          transformedData.appointmentsByChannel = appointmentsExtras.appointmentsByChannel || [];
        }

        return [transformedData, null] as const;
      }

      // Fallback to empty data if backend fails
      console.warn("Analytics API failed, using empty data", dashboardError);

      const emptyData: AnalyticsDashboardData = {
        appointmentTrend: [],
        appointmentStatus: [],
        appointmentsByChannel: [],
        kpi: {
          totalAppointments: 0,
          noShowRate: 0,
          completionRate: 0,
          cancellationRate: 0,
          riskAlerts: 0,
          totalPatients: 0,
          newPatients: 0,
        }
      };

      return [emptyData, null] as const;

    } catch (error) {
      console.error("Failed to fetch dashboard analytics", error);
      return [null, error as Error] as const;
    }
  },
};
