import { apiClient, apiCall } from './client';
import { AIInsight, ProactiveAlert, SentimentData } from '@/lib/store/analytics-store';
import { subDays, format } from 'date-fns';

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
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 800));

    // Generate mock time series data
    const appointmentTrendData = [];
    for (let i = 29; i >= 0; i--) {
      const date = subDays(new Date(), i);
      appointmentTrendData.push({
        date: date.toISOString(),
        value: Math.floor(100 + Math.random() * 60),
        label: format(date, "MMM d"),
      });
    }

    // Mock Response
    const mockData: AnalyticsDashboardData = {
      appointmentTrend: appointmentTrendData,
      revenueData: [
        { category: "Cardiology", value: 3210000, color: "#6366f1" },
        { category: "Orthopedics", value: 2580000, color: "#22c55e" },
        { category: "General Med", value: 1720000, color: "#f59e0b" },
        { category: "Pediatrics", value: 1610000, color: "#ec4899" },
        { category: "Dermatology", value: 1340000, color: "#8b5cf6" },
      ],
      appointmentStatus: [
        { name: "Completed", value: 65, color: "#22c55e" },
        { name: "Scheduled", value: 20, color: "#6366f1" },
        { name: "Canceled", value: 10, color: "#ef4444" },
        { name: "No-Show", value: 5, color: "#f59e0b" },
      ],
      insights: [
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
      ],
      alerts: [
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
      ],
      sentiment: {
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
      },
      kpi: {
        totalAppointments: 142,
        revenue: 4520000,
        patientSatisfaction: 4.6,
        noShowRate: 12,
        riskAlerts: 8
      }
    };

    return [mockData, null] as const;
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
