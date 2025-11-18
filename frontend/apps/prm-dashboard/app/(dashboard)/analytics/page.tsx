'use client';

import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  TrendingUp,
  TrendingDown,
  Calendar,
  MessageSquare,
  Phone,
  Users,
  Activity,
  Download,
  RefreshCw,
  Filter,
  ChevronDown,
} from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { analyticsAPI, TimePeriod, DashboardOverview } from '@/lib/api/analytics';
import { format } from 'date-fns';
import toast from 'react-hot-toast';

// ==================== Constants ====================

const COLORS = {
  primary: '#3B82F6',
  success: '#10B981',
  warning: '#F59E0B',
  danger: '#EF4444',
  purple: '#8B5CF6',
  pink: '#EC4899',
  gray: '#6B7280',
};

const CHART_COLORS = [
  COLORS.primary,
  COLORS.success,
  COLORS.warning,
  COLORS.purple,
  COLORS.pink,
  COLORS.danger,
];

const TIME_PERIODS: { value: TimePeriod; label: string }[] = [
  { value: 'today', label: 'Today' },
  { value: 'yesterday', label: 'Yesterday' },
  { value: 'last_7_days', label: 'Last 7 Days' },
  { value: 'last_30_days', label: 'Last 30 Days' },
  { value: 'this_week', label: 'This Week' },
  { value: 'this_month', label: 'This Month' },
  { value: 'last_month', label: 'Last Month' },
  { value: 'this_quarter', label: 'This Quarter' },
  { value: 'this_year', label: 'This Year' },
];

// ==================== Main Component ====================

export default function AnalyticsPage() {
  const [timePeriod, setTimePeriod] = useState<TimePeriod>('last_30_days');
  const [isRealtime, setIsRealtime] = useState(false);
  const [realtimeData, setRealtimeData] = useState<DashboardOverview | null>(null);

  // Fetch dashboard overview
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['analytics', 'dashboard', timePeriod],
    queryFn: async () => {
      const tenantId = 'your-tenant-id'; // TODO: Get from auth context
      const [result, error] = await analyticsAPI.getDashboardOverview({
        tenant_id: tenantId,
        time_period: timePeriod,
      });
      if (error) throw new Error(error.message);
      return result;
    },
  });

  // Real-time updates via Server-Sent Events
  useEffect(() => {
    if (!isRealtime) return;

    const tenantId = 'your-tenant-id'; // TODO: Get from auth context
    const eventSource = analyticsAPI.createRealtimeStream(tenantId);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setRealtimeData(data);
      } catch (error) {
        console.error('Failed to parse real-time data:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('EventSource error:', error);
      eventSource.close();
      setIsRealtime(false);
      toast.error('Real-time connection lost');
    };

    return () => {
      eventSource.close();
    };
  }, [isRealtime]);

  const overview = realtimeData || data;

  const handleExport = async (format: 'csv' | 'pdf' | 'excel') => {
    try {
      const tenantId = 'your-tenant-id'; // TODO: Get from auth context
      const [blob, error] = await analyticsAPI.exportData({
        tenant_id: tenantId,
        time_period: timePeriod,
        format,
      });

      if (error) throw new Error(error.message);

      // Download blob
      const url = window.URL.createObjectURL(blob!);
      const a = document.createElement('a');
      a.href = url;
      a.download = `analytics-${timePeriod}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast.success(`Exported as ${format.toUpperCase()}`);
    } catch (error) {
      toast.error('Export failed');
    }
  };

  if (isLoading || !overview) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-500 mt-1">
            Comprehensive metrics and insights across your PRM
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Real-time Toggle */}
          <Button
            variant={isRealtime ? 'default' : 'outline'}
            onClick={() => setIsRealtime(!isRealtime)}
          >
            <Activity className={`w-4 h-4 mr-2 ${isRealtime ? 'animate-pulse' : ''}`} />
            {isRealtime ? 'Live' : 'Enable Live'}
          </Button>

          {/* Refresh */}
          <Button variant="outline" onClick={() => refetch()}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>

          {/* Export Dropdown */}
          <div className="relative group">
            <Button variant="outline">
              <Download className="w-4 h-4 mr-2" />
              Export
              <ChevronDown className="w-4 h-4 ml-2" />
            </Button>
            <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
              <button
                onClick={() => handleExport('csv')}
                className="w-full px-4 py-2 text-left hover:bg-gray-50 rounded-t-lg"
              >
                Export as CSV
              </button>
              <button
                onClick={() => handleExport('excel')}
                className="w-full px-4 py-2 text-left hover:bg-gray-50"
              >
                Export as Excel
              </button>
              <button
                onClick={() => handleExport('pdf')}
                className="w-full px-4 py-2 text-left hover:bg-gray-50 rounded-b-lg"
              >
                Export as PDF
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Time Period Selector */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-2 flex-wrap">
            {TIME_PERIODS.map((period) => (
              <Button
                key={period.value}
                variant={timePeriod === period.value ? 'default' : 'outline'}
                size="sm"
                onClick={() => setTimePeriod(period.value)}
              >
                {period.label}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Appointments"
          value={overview.appointments.total_appointments}
          change={calculateChange(overview.appointments.trend)}
          icon={<Calendar className="w-5 h-5" />}
          color="blue"
        />
        <MetricCard
          title="Active Journeys"
          value={overview.journeys.total_active}
          change={calculateChange(overview.journeys.trend)}
          icon={<Users className="w-5 h-5" />}
          color="green"
        />
        <MetricCard
          title="Total Messages"
          value={overview.communication.total_messages}
          change={calculateChange(overview.communication.trend)}
          icon={<MessageSquare className="w-5 h-5" />}
          color="purple"
        />
        <MetricCard
          title="Voice Calls"
          value={overview.voice_calls.total_calls}
          change={calculateChange(overview.voice_calls.trend)}
          icon={<Phone className="w-5 h-5" />}
          color="pink"
        />
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Appointment Completion Rate</CardDescription>
            <CardTitle className="text-3xl">
              {overview.appointments.completion_rate.toFixed(1)}%
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-green-500"
                style={{ width: `${overview.appointments.completion_rate}%` }}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Avg Response Time</CardDescription>
            <CardTitle className="text-3xl">
              {overview.communication.avg_response_time_minutes.toFixed(0)}m
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600">
              {overview.communication.open_conversations} open conversations
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Call Success Rate</CardDescription>
            <CardTitle className="text-3xl">
              {overview.voice_calls.booking_success_rate.toFixed(1)}%
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600">
              {overview.voice_calls.completed_calls} completed calls
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 1: Appointments & Journeys */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Appointments Trend */}
        <Card>
          <CardHeader>
            <CardTitle>Appointment Trends</CardTitle>
            <CardDescription>Daily appointment volume over time</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={overview.appointments.trend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tickFormatter={(date) => format(new Date(date), 'MMM d')} />
                <YAxis />
                <Tooltip labelFormatter={(date) => format(new Date(date), 'MMM d, yyyy')} />
                <Area type="monotone" dataKey="value" stroke={COLORS.primary} fill={COLORS.primary} fillOpacity={0.3} />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Journey Status Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle>Journey Status</CardTitle>
            <CardDescription>Distribution of journey states</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={[
                    { name: 'Active', value: overview.journeys.total_active },
                    { name: 'Completed', value: overview.journeys.completed },
                    { name: 'Paused', value: overview.journeys.paused },
                    { name: 'Canceled', value: overview.journeys.canceled },
                  ]}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {CHART_COLORS.map((color, index) => (
                    <Cell key={`cell-${index}`} fill={color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 2: Communication & Voice Calls */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Communication Trend */}
        <Card>
          <CardHeader>
            <CardTitle>Communication Volume</CardTitle>
            <CardDescription>Messages sent and received over time</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={overview.communication.trend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tickFormatter={(date) => format(new Date(date), 'MMM d')} />
                <YAxis />
                <Tooltip labelFormatter={(date) => format(new Date(date), 'MMM d, yyyy')} />
                <Legend />
                <Line type="monotone" dataKey="value" stroke={COLORS.purple} name="Messages" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Voice Call Metrics */}
        <Card>
          <CardHeader>
            <CardTitle>Voice Call Performance</CardTitle>
            <CardDescription>Call volume and success metrics</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={overview.voice_calls.trend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tickFormatter={(date) => format(new Date(date), 'MMM d')} />
                <YAxis />
                <Tooltip labelFormatter={(date) => format(new Date(date), 'MMM d, yyyy')} />
                <Legend />
                <Bar dataKey="value" fill={COLORS.success} name="Calls" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Appointment Status Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Appointment Status Distribution</CardTitle>
          <CardDescription>Breakdown of appointments by status</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={[
                { name: 'Scheduled', value: overview.appointments.scheduled, fill: COLORS.primary },
                { name: 'Confirmed', value: overview.appointments.confirmed, fill: COLORS.success },
                { name: 'Completed', value: overview.appointments.completed, fill: COLORS.purple },
                { name: 'Canceled', value: overview.appointments.canceled, fill: COLORS.danger },
                { name: 'No Show', value: overview.appointments.no_show, fill: COLORS.warning },
              ]}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}

// ==================== Helper Components ====================

interface MetricCardProps {
  title: string;
  value: number;
  change: number;
  icon: React.ReactNode;
  color: 'blue' | 'green' | 'purple' | 'pink';
}

function MetricCard({ title, value, change, icon, color }: MetricCardProps) {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    purple: 'bg-purple-100 text-purple-600',
    pink: 'bg-pink-100 text-pink-600',
  };

  const isPositive = change >= 0;

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="text-3xl font-bold text-gray-900 mt-2">{value.toLocaleString()}</p>
            <div className="flex items-center mt-2">
              {isPositive ? (
                <TrendingUp className="w-4 h-4 text-green-600 mr-1" />
              ) : (
                <TrendingDown className="w-4 h-4 text-red-600 mr-1" />
              )}
              <span className={`text-sm font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                {Math.abs(change).toFixed(1)}%
              </span>
              <span className="text-sm text-gray-500 ml-1">vs last period</span>
            </div>
          </div>
          <div className={`p-3 rounded-lg ${colorClasses[color]}`}>{icon}</div>
        </div>
      </CardContent>
    </Card>
  );
}

// ==================== Helper Functions ====================

function calculateChange(trend: Array<{ date: string; value: number }>): number {
  if (trend.length < 2) return 0;

  const recent = trend.slice(-7); // Last 7 days
  const previous = trend.slice(-14, -7); // Previous 7 days

  if (recent.length === 0 || previous.length === 0) return 0;

  const recentAvg = recent.reduce((sum, d) => sum + d.value, 0) / recent.length;
  const previousAvg = previous.reduce((sum, d) => sum + d.value, 0) / previous.length;

  if (previousAvg === 0) return 0;

  return ((recentAvg - previousAvg) / previousAvg) * 100;
}
