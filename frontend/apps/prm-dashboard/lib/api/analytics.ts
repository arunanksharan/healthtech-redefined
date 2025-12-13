import { apiClient, apiCall } from './client';
import { AIInsight, ProactiveAlert, SentimentData } from '@/lib/store/analytics-store';
import { subDays, format } from 'date-fns';
import { patientsAPI } from './patients';
import { journeysAPI } from './journeys';
import { communicationsAPI } from './communications';

export interface AnalyticsDashboardData {
  appointmentTrend: Array<{ date: string; value: number; label: string }>;
  revenueData: Array<{ category: string; value: number; color: string }>;
  appointmentStatus: Array<{ name: string; value: number; color: string }>;
  insights: AIInsight[];
  alerts: ProactiveAlert[];
  sentiment: SentimentData;
  kpi: {
    totalAppointments: number;
    revenue: number;
    patientSatisfaction: number;
    noShowRate: number;
    riskAlerts: number;
  };
}

export const analyticsAPI = {
  /**
   * Get comprehensive dashboard metrics
   */
  async getDashboardData(timePeriod: string = 'last_30_days') {
    try {
      // Fetch real stats in parallel
      const [
        [patientStats],
        [journeyStats],
        [commStats]
      ] = await Promise.all([
        patientsAPI.getStats(),
        journeysAPI.getInstanceStats(),
        communicationsAPI.getStats()
      ]);

      // Generate mock time series data (Backend doesn't support this yet)
      const appointmentTrendData = [];
      for (let i = 29; i >= 0; i--) {
        const date = subDays(new Date(), i);
        appointmentTrendData.push({
          date: date.toISOString(),
          value: Math.floor(100 + Math.random() * 60),
          label: format(date, "MMM d"),
        });
      }

      // Map Real Data to Dashboard Interface
      const analyticsData: AnalyticsDashboardData = {
        // Mocked Trend (No backend support yet)
        appointmentTrend: appointmentTrendData,

        // Mocked Revenue (No Billing API yet)
        revenueData: [
          { category: "Cardiology", value: 3210000, color: "#6366f1" },
          { category: "Orthopedics", value: 2580000, color: "#22c55e" },
          { category: "General Med", value: 1720000, color: "#f59e0b" },
          { category: "Pediatrics", value: 1610000, color: "#ec4899" },
          { category: "Dermatology", value: 1340000, color: "#8b5cf6" },
        ],

        // Real Journey Status
        appointmentStatus: [
          { name: "Active Journeys", value: journeyStats?.active || 0, color: "#22c55e" },
          { name: "Completed", value: journeyStats?.completed || 0, color: "#6366f1" },
          { name: "Cancelled", value: journeyStats?.cancelled || 0, color: "#ef4444" },
          { name: "Total Instances", value: journeyStats?.total || 0, color: "#f59e0b" },
        ],

        // Mocked Insights
        insights: [
          {
            id: "1",
            title: "Cardiology revenue is 15% above target",
            description: "Cardiology department has exceeded revenue targets for the 3rd consecutive month.",
            category: "revenue",
            sentiment: "positive",
            impact: "high",
            metrics: [
              { label: "Current Revenue", value: "₹32.1L", change: 12.6 },
              { label: "Target", value: "₹28L" },
            ],
            suggestedActions: [
              { id: "1", label: "View revenue breakdown" },
            ],
            createdAt: new Date().toISOString(),
          },
        ],

        // Mocked Alerts
        alerts: [
          {
            id: "1",
            title: "No-Show Prediction Alert",
            description: "8 appointments tomorrow flagged as 'High No-Show Risk'.",
            type: "no_show_risk",
            priority: "high",
            affectedItems: [],
            suggestedAction: "Send WhatsApp confirmation",
            primaryAction: "Send Confirmations Now",
            secondaryAction: "Review List",
            createdAt: new Date().toISOString(),
          }
        ],

        // Mocked Sentiment
        sentiment: {
          overallScore: 76,
          previousScore: 78,
          totalFeedback: 1250,
          departments: [],
        },

        // Real KPIs mixed with Mocks
        kpi: {
          totalAppointments: patientStats?.total_patients || 0, // Using Total Patients as proxy for main KPI
          revenue: 4520000, // Mocked
          patientSatisfaction: 4.6, // Mocked
          noShowRate: 12, // Mocked
          riskAlerts: journeyStats?.active || 0 // Using Active Journeys as a "Risk/Activity" proxy
        }
      };

      return [analyticsData, null] as const;

    } catch (error) {
      console.error("Failed to fetch dashboard analytics", error);
      return [null, error] as any;
    }
  },

  async askAI(query: string) {
    // Simulate AI processing
    await new Promise(resolve => setTimeout(resolve, 1500));

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
  }
};
