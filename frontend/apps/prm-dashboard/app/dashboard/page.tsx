'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import {
  Calendar,
  Users,
  MessageSquare,
  Ticket,
  TrendingUp,
  Activity,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  Zap,
} from 'lucide-react';
import { appointmentsAPI } from '@/lib/api/appointments';
import { patientsAPI } from '@/lib/api/patients';
import { journeysAPI } from '@/lib/api/journeys';
import { communicationsAPI } from '@/lib/api/communications';
import { ticketsAPI } from '@/lib/api/tickets';
import { Badge } from '@/components/ui/badge';
import { formatSmartDate } from '@/lib/utils/date';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';

export default function DashboardPage() {
  // Fetch dashboard data
  const { data: appointmentsData } = useQuery({
    queryKey: ['appointments-dashboard'],
    queryFn: async () => {
      const [data] = await appointmentsAPI.getAll({ limit: 100 });
      return data;
    },
  });

  const { data: patientsData } = useQuery({
    queryKey: ['patients-dashboard'],
    queryFn: async () => {
      const [data] = await patientsAPI.getAll({ limit: 100 });
      return data;
    },
  });

  const { data: journeysData } = useQuery({
    queryKey: ['journeys-dashboard'],
    queryFn: async () => {
      const [data] = await journeysAPI.getInstances({ limit: 100 });
      return data;
    },
  });

  const { data: communicationsData } = useQuery({
    queryKey: ['communications-dashboard'],
    queryFn: async () => {
      const [data] = await communicationsAPI.getAll({ limit: 100 });
      return data;
    },
  });

  const { data: ticketsData } = useQuery({
    queryKey: ['tickets-dashboard'],
    queryFn: async () => {
      const [data] = await ticketsAPI.getAll({ limit: 100 });
      return data;
    },
  });

  const { data: ticketStats } = useQuery({
    queryKey: ['tickets-stats'],
    queryFn: async () => {
      const [data] = await ticketsAPI.getStats();
      return data;
    },
  });

  const { data: appointmentStats } = useQuery({
    queryKey: ['appointment-stats'],
    queryFn: async () => {
      const [data] = await appointmentsAPI.getStats();
      return data;
    },
    refetchInterval: 30000,
  });

  const { data: journeyInstanceStats } = useQuery({
    queryKey: ['journey-instance-stats'],
    queryFn: async () => {
      const [data] = await journeysAPI.getInstanceStats();
      return data;
    },
  });

  const appointments = appointmentsData?.items || [];
  const patients = patientsData?.items || [];
  const journeys = journeysData?.instances || [];
  const communications = communicationsData?.communications || [];
  const tickets = ticketsData?.tickets || [];

  // Stats object using backend data
  const stats = {
    todaysAppointments: appointmentStats?.today ?? 0,
    activeJourneys: journeyInstanceStats?.active ?? 0,
    messagesSent: communicationsData?.total ?? 0,
    pendingTickets: (ticketStats?.open ?? 0) + (ticketStats?.in_progress ?? 0),
    totalPatients: patients.length,
    completedAppointments: appointmentStats?.completed ?? 0,
    confirmedAppointments: appointmentStats?.confirmed ?? 0,
    cancelledAppointments: (appointmentStats?.cancelled ?? 0) + (appointmentStats?.no_show ?? 0),
    totalJourneys: journeyInstanceStats?.total ?? journeysData?.total ?? 0,
    completedJourneys: journeyInstanceStats?.completed ?? 0,
    cancelledJourneys: journeyInstanceStats?.cancelled ?? 0,
  };

  // Get upcoming appointments
  const upcomingAppointments = appointments
    .filter(apt => new Date(apt.scheduled_at) >= new Date())
    .sort((a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime())
    .slice(0, 5);

  return (
    <div className="space-y-8">
      {/* Welcome Header - Flat Design */}
      <div>
        <h1 className="font-heading text-3xl text-gray-900 dark:text-white">Welcome back!</h1>
        <p className="text-gray-500 mt-1">Here's what's happening with your patients today.</p>
      </div>

      {/* Stats Cards - Flat Color Blocks */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <FlatStatCard
          title="Today's Appointments"
          value={stats.todaysAppointments}
          change="+12%"
          icon={<Calendar className="w-6 h-6" />}
          color="blue"
        />
        <FlatStatCard
          title="Active Journeys"
          value={stats.activeJourneys}
          change="+8%"
          icon={<Users className="w-6 h-6" />}
          color="purple"
        />
        <FlatStatCard
          title="Messages Sent"
          value={stats.messagesSent}
          change="+23%"
          icon={<MessageSquare className="w-6 h-6" />}
          color="emerald"
        />
        <FlatStatCard
          title="Pending Tickets"
          value={stats.pendingTickets}
          change="-4%"
          icon={<Ticket className="w-6 h-6" />}
          color="amber"
        />
      </div>

      {/* Analytics Grid - Flat Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Appointment Status Breakdown */}
        <div className="flat-card bg-white dark:bg-gray-800">
          <h3 className="font-heading text-lg text-gray-900 dark:text-white mb-1">Appointment Status</h3>
          <p className="text-sm text-gray-500 mb-6">Current appointment distribution</p>

          <div className="space-y-4">
            <StatusBar
              label="Confirmed"
              value={stats.confirmedAppointments}
              total={appointmentStats?.total || 1}
              color="emerald"
              icon={<CheckCircle2 className="w-4 h-4" />}
            />
            <StatusBar
              label="Completed"
              value={stats.completedAppointments}
              total={appointmentStats?.total || 1}
              color="blue"
              icon={<CheckCircle2 className="w-4 h-4" />}
            />
            <StatusBar
              label="Cancelled"
              value={stats.cancelledAppointments}
              total={appointmentStats?.total || 1}
              color="red"
              icon={<AlertCircle className="w-4 h-4" />}
            />
          </div>
        </div>

        {/* Patient Engagement */}
        <div className="flat-card bg-white dark:bg-gray-800">
          <h3 className="font-heading text-lg text-gray-900 dark:text-white mb-1">Patient Engagement</h3>
          <p className="text-sm text-gray-500 mb-6">Communication & journey metrics</p>

          <div className="space-y-4">
            <EngagementBlock
              label="Total Patients"
              value={stats.totalPatients}
              color="blue"
              icon={<Users className="w-6 h-6" />}
            />
            <EngagementBlock
              label="Active Journeys"
              value={stats.activeJourneys}
              color="emerald"
              icon={<Activity className="w-6 h-6" />}
            />
            <EngagementBlock
              label="Delivered Messages"
              value={communications.filter(c => c.status === 'delivered').length}
              color="purple"
              icon={<MessageSquare className="w-6 h-6" />}
            />
          </div>
        </div>

        {/* Ticket Analytics */}
        <div className="flat-card bg-white dark:bg-gray-800">
          <h3 className="font-heading text-lg text-gray-900 dark:text-white mb-1">Support Tickets</h3>
          <p className="text-sm text-gray-500 mb-6">Current ticket status</p>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <TicketBlock label="Open" value={tickets.filter(t => t.status === 'open').length} color="blue" />
            <TicketBlock label="In Progress" value={tickets.filter(t => t.status === 'in_progress').length} color="amber" />
            <TicketBlock label="Resolved" value={tickets.filter(t => t.status === 'resolved').length} color="emerald" />
            <TicketBlock label="Closed" value={tickets.filter(t => t.status === 'closed').length} color="gray" />
          </div>

          <div className="pt-4 border-t-2 border-gray-100 dark:border-gray-700 flex items-center justify-between">
            <span className="text-sm text-gray-500">Urgent Priority</span>
            <span className="bg-red-500 text-white text-sm font-semibold px-3 py-1 rounded-md">
              {tickets.filter(t => t.priority === 'urgent').length}
            </span>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upcoming Appointments */}
        <div className="flat-card bg-white dark:bg-gray-800">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="font-heading text-lg text-gray-900 dark:text-white">Upcoming Appointments</h3>
              <p className="text-sm text-gray-500">Next {upcomingAppointments.length} scheduled</p>
            </div>
            <Link
              href="/dashboard/appointments"
              className="text-blue-500 font-semibold text-sm uppercase tracking-wider flex items-center gap-1 hover:text-blue-600 transition-colors"
            >
              View All
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          {upcomingAppointments.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              <Calendar className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No upcoming appointments</p>
            </div>
          ) : (
            <div className="space-y-3">
              {upcomingAppointments.map((apt) => (
                <div
                  key={apt.id}
                  className="flex items-center gap-4 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg transition-all duration-200 hover:scale-[1.01] hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer"
                >
                  <Avatar className="w-10 h-10">
                    <AvatarFallback className="bg-blue-100 text-blue-600 font-semibold">
                      {apt.patient?.name
                        ?.split(' ')
                        .map((n) => n[0])
                        .join('')
                        .toUpperCase() || '?'}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">{apt.patient?.name || 'Unknown'}</p>
                    <p className="text-xs text-gray-500">{apt.appointment_type || 'General'}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {new Date(apt.scheduled_at).toLocaleTimeString('en-US', {
                        hour: 'numeric',
                        minute: '2-digit',
                      })}
                    </p>
                    <p className="text-xs text-gray-500">{formatSmartDate(apt.scheduled_at)}</p>
                  </div>
                  <Badge
                    className={`${apt.status === 'confirmed' ? 'bg-emerald-500 text-white' : 'bg-gray-200 text-gray-700 dark:bg-gray-600 dark:text-gray-200'}`}
                  >
                    {apt.status}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Communications */}
        <div className="flat-card bg-white dark:bg-gray-800">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="font-heading text-lg text-gray-900 dark:text-white">Recent Communications</h3>
              <p className="text-sm text-gray-500">Latest patient messages</p>
            </div>
            <Link
              href="/dashboard/communications"
              className="text-blue-500 font-semibold text-sm uppercase tracking-wider flex items-center gap-1 hover:text-blue-600 transition-colors"
            >
              View All
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          <div className="space-y-1">
            {communications.slice(0, 5).map((comm) => (
              <div key={comm.id} className="flex items-start gap-3 p-4 border-b-2 border-gray-100 dark:border-gray-700 last:border-0 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                <div className="w-2 h-2 mt-2 rounded-full bg-blue-500 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-900 dark:text-white truncate">
                    {comm.channel === 'email' && comm.subject ? comm.subject : comm.message?.substring(0, 50) || 'No message'}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded">
                      {comm.channel}
                    </span>
                    <span className="text-xs text-gray-400">{formatSmartDate(comm.sent_at || comm.created_at)}</span>
                  </div>
                </div>
                <Badge
                  className={`flex-shrink-0 ${comm.status === 'delivered' ? 'bg-emerald-500 text-white' :
                      comm.status === 'failed' ? 'bg-red-500 text-white' :
                        'bg-gray-200 text-gray-700 dark:bg-gray-600 dark:text-gray-200'
                    }`}
                >
                  {comm.status}
                </Badge>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* AI Suggestions - Flat Blue Block */}
      <div className="bg-blue-500 rounded-lg p-6">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center">
            <Zap className="w-5 h-5 text-blue-500" />
          </div>
          <div>
            <h3 className="font-heading text-lg text-white">AI Suggestions</h3>
            <p className="text-blue-100 text-sm">Smart recommendations powered by AI</p>
          </div>
        </div>

        <div className="space-y-3 mt-6">
          <SuggestionItem suggestion="Send reminders to 12 patients with appointments tomorrow" />
          <SuggestionItem suggestion="3 patients have missed follow-up appointments - create callbacks" />
          <SuggestionItem suggestion="Update billing for 5 completed appointments from yesterday" />
        </div>
      </div>
    </div>
  );
}

// Flat Stat Card Component
function FlatStatCard({
  title,
  value,
  change,
  icon,
  color,
}: {
  title: string;
  value: number;
  change: string;
  icon: React.ReactNode;
  color: "blue" | "purple" | "emerald" | "amber";
}) {
  const colorClasses = {
    blue: { bg: "bg-blue-50 dark:bg-blue-900/20", icon: "text-blue-500", accent: "text-blue-500" },
    purple: { bg: "bg-purple-50 dark:bg-purple-900/20", icon: "text-purple-500", accent: "text-purple-500" },
    emerald: { bg: "bg-emerald-50 dark:bg-emerald-900/20", icon: "text-emerald-500", accent: "text-emerald-500" },
    amber: { bg: "bg-amber-50 dark:bg-amber-900/20", icon: "text-amber-500", accent: "text-amber-500" },
  };

  const isPositive = change.startsWith("+");

  return (
    <div className={`flat-card ${colorClasses[color].bg} group`}>
      <div className="flex items-center justify-between mb-4">
        <div className={`w-12 h-12 rounded-full bg-white dark:bg-gray-800 flex items-center justify-center transition-transform duration-200 group-hover:scale-110 ${colorClasses[color].icon}`}>
          {icon}
        </div>
        <div className="flex items-center gap-1">
          <TrendingUp className={`w-4 h-4 ${isPositive ? 'text-emerald-500' : 'text-red-500 rotate-180'}`} />
          <span className={`text-sm font-medium ${isPositive ? 'text-emerald-500' : 'text-red-500'}`}>
            {change}
          </span>
        </div>
      </div>
      <div className={`font-heading text-4xl ${colorClasses[color].accent}`}>
        {value}
      </div>
      <p className="text-sm text-gray-500 mt-1">{title}</p>
    </div>
  );
}

// Status Bar Component
function StatusBar({
  label,
  value,
  total,
  color,
  icon,
}: {
  label: string;
  value: number;
  total: number;
  color: "emerald" | "blue" | "red";
  icon: React.ReactNode;
}) {
  const colorClasses = {
    emerald: { icon: "text-emerald-500", bar: "bg-emerald-500" },
    blue: { icon: "text-blue-500", bar: "bg-blue-500" },
    red: { icon: "text-red-500", bar: "bg-red-500" },
  };

  const percentage = total > 0 ? (value / total) * 100 : 0;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className={`flex items-center gap-2 ${colorClasses[color].icon}`}>
          {icon}
          <span className="text-sm text-gray-500">{label}</span>
        </div>
        <span className="text-sm font-semibold text-gray-900 dark:text-white">{value}</span>
      </div>
      <div className="w-full h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full ${colorClasses[color].bar} transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

// Engagement Block Component
function EngagementBlock({
  label,
  value,
  color,
  icon,
}: {
  label: string;
  value: number;
  color: "blue" | "emerald" | "purple";
  icon: React.ReactNode;
}) {
  const colorClasses = {
    blue: { bg: "bg-blue-50 dark:bg-blue-900/20", text: "text-blue-500", icon: "text-blue-500" },
    emerald: { bg: "bg-emerald-50 dark:bg-emerald-900/20", text: "text-emerald-500", icon: "text-emerald-500" },
    purple: { bg: "bg-purple-50 dark:bg-purple-900/20", text: "text-purple-500", icon: "text-purple-500" },
  };

  return (
    <div className={`flex items-center justify-between p-4 ${colorClasses[color].bg} rounded-lg transition-all duration-200 hover:scale-[1.02]`}>
      <div>
        <div className={`font-heading text-2xl ${colorClasses[color].text}`}>{value}</div>
        <div className="text-sm text-gray-500">{label}</div>
      </div>
      <div className={colorClasses[color].icon}>{icon}</div>
    </div>
  );
}

// Ticket Block Component
function TicketBlock({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: "blue" | "amber" | "emerald" | "gray";
}) {
  const colorClasses = {
    blue: "text-blue-500",
    amber: "text-amber-500",
    emerald: "text-emerald-500",
    gray: "text-gray-400",
  };

  return (
    <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg transition-all duration-200 hover:scale-[1.02]">
      <div className={`font-heading text-2xl ${colorClasses[color]}`}>{value}</div>
      <div className="text-xs text-gray-500">{label}</div>
    </div>
  );
}

// Suggestion Item Component
function SuggestionItem({ suggestion }: { suggestion: string }) {
  return (
    <div className="flex items-start gap-3 p-4 bg-white/10 rounded-lg transition-all duration-200 hover:bg-white/20 hover:scale-[1.01]">
      <div className="flex-1">
        <p className="text-sm text-white">{suggestion}</p>
      </div>
      <button className="text-xs font-semibold text-blue-500 bg-white px-4 py-2 rounded-md transition-all duration-200 hover:scale-105 hover:bg-blue-50">
        Execute
      </button>
    </div>
  );
}
