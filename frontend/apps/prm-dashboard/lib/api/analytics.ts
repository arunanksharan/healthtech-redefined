import { apiClient, apiCall } from './client';

/**
 * Analytics API Module
 * Provides access to comprehensive PRM analytics and metrics
 */

// ==================== Types ====================

export type TimePeriod =
  | 'today'
  | 'yesterday'
  | 'last_7_days'
  | 'last_30_days'
  | 'this_week'
  | 'last_week'
  | 'this_month'
  | 'last_month'
  | 'this_quarter'
  | 'last_quarter'
  | 'this_year'
  | 'custom';

export type AggregationLevel = 'hourly' | 'daily' | 'weekly' | 'monthly';

export interface TimeSeriesDataPoint {
  date: string;
  value: number;
  label?: string;
}

export interface AppointmentMetrics {
  total_appointments: number;
  scheduled: number;
  confirmed: number;
  completed: number;
  canceled: number;
  no_show: number;
  no_show_rate: number;
  completion_rate: number;
  cancellation_rate: number;
  trend: TimeSeriesDataPoint[];
}

export interface AppointmentBreakdown {
  by_channel?: Record<string, number>;
  by_practitioner?: Record<string, number>;
  by_department?: Record<string, number>;
  by_location?: Record<string, number>;
  by_hour?: TimeSeriesDataPoint[];
  by_day_of_week?: TimeSeriesDataPoint[];
}

export interface JourneyMetrics {
  total_active: number;
  completed: number;
  paused: number;
  canceled: number;
  completion_rate: number;
  avg_completion_time_days: number;
  overdue_steps: number;
  trend: TimeSeriesDataPoint[];
}

export interface JourneyBreakdown {
  by_type?: Record<string, number>;
  by_department?: Record<string, number>;
  by_status?: Record<string, number>;
}

export interface CommunicationMetrics {
  total_messages: number;
  total_conversations: number;
  inbound_messages: number;
  outbound_messages: number;
  avg_response_time_minutes: number;
  open_conversations: number;
  pending_conversations: number;
  trend: TimeSeriesDataPoint[];
}

export interface CommunicationBreakdown {
  by_channel?: Record<string, number>;
  by_sentiment?: Record<string, number>;
  by_status?: Record<string, number>;
}

export interface VoiceCallMetrics {
  total_calls: number;
  completed_calls: number;
  failed_calls: number;
  avg_duration_minutes: number;
  total_duration_minutes: number;
  avg_quality_score: number;
  booking_success_rate: number;
  trend: TimeSeriesDataPoint[];
}

export interface VoiceCallBreakdown {
  by_intent?: Record<string, number>;
  by_outcome?: Record<string, number>;
  by_call_type?: Record<string, number>;
}

export interface DashboardOverview {
  appointments: AppointmentMetrics;
  journeys: JourneyMetrics;
  communication: CommunicationMetrics;
  voice_calls: VoiceCallMetrics;
  time_period: string;
  start_date: string;
  end_date: string;
}

export interface AnalyticsQueryParams {
  tenant_id: string;
  time_period?: TimePeriod;
  start_date?: string;
  end_date?: string;
  aggregation?: AggregationLevel;
  include_breakdown?: boolean;
  practitioner_id?: string;
  department?: string;
  location_id?: string;
  channel_origin?: string;
}

// ==================== API Client ====================

export const analyticsAPI = {
  /**
   * Get appointment analytics with optional breakdowns
   */
  async getAppointmentAnalytics(params: AnalyticsQueryParams) {
    return apiCall<{
      summary: AppointmentMetrics;
      breakdown?: AppointmentBreakdown;
      time_period: string;
      start_date: string;
      end_date: string;
    }>(
      apiClient.get('/api/v1/analytics/appointments', {
        params: {
          tenant_id: params.tenant_id,
          time_period: params.time_period || 'last_30_days',
          start_date: params.start_date,
          end_date: params.end_date,
          aggregation: params.aggregation || 'daily',
          include_breakdown: params.include_breakdown ?? true,
          practitioner_id: params.practitioner_id,
          department: params.department,
          location_id: params.location_id,
          channel_origin: params.channel_origin,
        },
      })
    );
  },

  /**
   * Get journey analytics with breakdowns
   */
  async getJourneyAnalytics(params: AnalyticsQueryParams) {
    return apiCall<{
      summary: JourneyMetrics;
      breakdown?: JourneyBreakdown;
      time_period: string;
      start_date: string;
      end_date: string;
    }>(
      apiClient.get('/api/v1/analytics/journeys', {
        params: {
          tenant_id: params.tenant_id,
          time_period: params.time_period || 'last_30_days',
          start_date: params.start_date,
          end_date: params.end_date,
          aggregation: params.aggregation || 'daily',
          include_breakdown: params.include_breakdown ?? true,
          department: params.department,
        },
      })
    );
  },

  /**
   * Get communication analytics (messages and conversations)
   */
  async getCommunicationAnalytics(params: AnalyticsQueryParams) {
    return apiCall<{
      summary: CommunicationMetrics;
      breakdown?: CommunicationBreakdown;
      time_period: string;
      start_date: string;
      end_date: string;
    }>(
      apiClient.get('/api/v1/analytics/communication', {
        params: {
          tenant_id: params.tenant_id,
          time_period: params.time_period || 'last_30_days',
          start_date: params.start_date,
          end_date: params.end_date,
          aggregation: params.aggregation || 'daily',
          include_breakdown: params.include_breakdown ?? true,
        },
      })
    );
  },

  /**
   * Get voice call analytics
   */
  async getVoiceCallAnalytics(params: AnalyticsQueryParams) {
    return apiCall<{
      summary: VoiceCallMetrics;
      breakdown?: VoiceCallBreakdown;
      time_period: string;
      start_date: string;
      end_date: string;
    }>(
      apiClient.get('/api/v1/analytics/voice-calls', {
        params: {
          tenant_id: params.tenant_id,
          time_period: params.time_period || 'last_30_days',
          start_date: params.start_date,
          end_date: params.end_date,
          aggregation: params.aggregation || 'daily',
          include_breakdown: params.include_breakdown ?? true,
        },
      })
    );
  },

  /**
   * Get complete dashboard overview (all metrics in one call)
   */
  async getDashboardOverview(params: AnalyticsQueryParams) {
    return apiCall<DashboardOverview>(
      apiClient.get('/api/v1/analytics/dashboard', {
        params: {
          tenant_id: params.tenant_id,
          time_period: params.time_period || 'last_30_days',
          start_date: params.start_date,
          end_date: params.end_date,
        },
      })
    );
  },

  /**
   * Create EventSource for real-time metrics streaming
   */
  createRealtimeStream(tenantId: string): EventSource {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const url = `${baseUrl}/api/v1/analytics/realtime?tenant_id=${tenantId}`;
    return new EventSource(url);
  },

  /**
   * Export analytics data
   */
  async exportData(params: AnalyticsQueryParams & { format: 'csv' | 'pdf' | 'excel' }) {
    return apiCall<Blob>(
      apiClient.get('/api/v1/analytics/export', {
        params: {
          tenant_id: params.tenant_id,
          time_period: params.time_period || 'last_30_days',
          start_date: params.start_date,
          end_date: params.end_date,
          format: params.format,
        },
        responseType: 'blob',
      })
    );
  },

  /**
   * Natural language query for AI-powered analytics
   */
  async queryWithAI(tenantId: string, query: string) {
    return apiCall<{
      answer: string;
      data?: any;
      visualizations?: any[];
      sql_query?: string;
    }>(
      apiClient.post('/api/v1/analytics/query', {
        tenant_id: tenantId,
        query,
      })
    );
  },
};
