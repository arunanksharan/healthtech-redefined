'use client';

import { useQuery } from '@tanstack/react-query';
import {
  Calendar,
  Users,
  MessageSquare,
  Ticket,
  TrendingUp,
  TrendingDown,
  Activity,
  Clock,
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
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { formatSmartDate } from '@/lib/utils/date';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';

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
      const [data] = await journeysAPI.getAll({ limit: 100 });
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

  const appointments = appointmentsData?.data || [];
  const patients = patientsData?.data || [];
  const journeys = journeysData?.data || [];
  const communications = communicationsData?.data || [];
  const tickets = ticketsData?.data || [];

  // Calculate today's appointments
  const today = new Date();
  const todayStart = new Date(today.setHours(0, 0, 0, 0));
  const todayEnd = new Date(today.setHours(23, 59, 59, 999));
  const todaysAppointments = appointments.filter(apt => {
    const aptDate = new Date(apt.scheduled_at);
    return aptDate >= todayStart && aptDate <= todayEnd;
  });

  // Calculate stats
  const stats = {
    todaysAppointments: todaysAppointments.length,
    activeJourneys: journeys.filter(j => j.status === 'active').length,
    messagesSent: communications.length,
    pendingTickets: tickets.filter(t => t.status === 'open' || t.status === 'in_progress').length,
    totalPatients: patients.length,
    completedAppointments: appointments.filter(a => a.status === 'completed').length,
    confirmedAppointments: appointments.filter(a => a.status === 'confirmed').length,
    cancelledAppointments: appointments.filter(a => a.status === 'cancelled').length,
  };

  // Get upcoming appointments
  const upcomingAppointments = appointments
    .filter(apt => new Date(apt.scheduled_at) >= new Date())
    .sort((a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime())
    .slice(0, 5);

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Welcome back!</h1>
        <p className="text-gray-500 mt-1">Here's what's happening with your patients today.</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Today's Appointments"
          value={stats.todaysAppointments.toString()}
          change="+12%"
          icon={<Calendar className="w-6 h-6" />}
          color="blue"
        />
        <StatCard
          title="Active Journeys"
          value={stats.activeJourneys.toString()}
          change="+8%"
          icon={<Users className="w-6 h-6" />}
          color="purple"
        />
        <StatCard
          title="Messages Sent"
          value={stats.messagesSent.toString()}
          change="+23%"
          icon={<MessageSquare className="w-6 h-6" />}
          color="green"
        />
        <StatCard
          title="Pending Tickets"
          value={stats.pendingTickets.toString()}
          change="-4%"
          icon={<Ticket className="w-6 h-6" />}
          color="orange"
        />
      </div>

      {/* Analytics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Appointment Status Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Appointment Status</CardTitle>
            <CardDescription>Current appointment distribution</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600" />
                  <span className="text-sm text-gray-700">Confirmed</span>
                </div>
                <span className="text-sm font-medium">{stats.confirmedAppointments}</span>
              </div>
              <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-green-500"
                  style={{
                    width: `${(stats.confirmedAppointments / appointments.length) * 100}%`,
                  }}
                />
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-blue-600" />
                  <span className="text-sm text-gray-700">Completed</span>
                </div>
                <span className="text-sm font-medium">{stats.completedAppointments}</span>
              </div>
              <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500"
                  style={{
                    width: `${(stats.completedAppointments / appointments.length) * 100}%`,
                  }}
                />
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-red-600" />
                  <span className="text-sm text-gray-700">Cancelled</span>
                </div>
                <span className="text-sm font-medium">{stats.cancelledAppointments}</span>
              </div>
              <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-red-500"
                  style={{
                    width: `${(stats.cancelledAppointments / appointments.length) * 100}%`,
                  }}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Patient Engagement */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Patient Engagement</CardTitle>
            <CardDescription>Communication & journey metrics</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
              <div>
                <div className="text-2xl font-bold text-blue-600">{stats.totalPatients}</div>
                <div className="text-sm text-gray-600">Total Patients</div>
              </div>
              <Users className="w-8 h-8 text-blue-600" />
            </div>
            <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
              <div>
                <div className="text-2xl font-bold text-green-600">{stats.activeJourneys}</div>
                <div className="text-sm text-gray-600">Active Journeys</div>
              </div>
              <Activity className="w-8 h-8 text-green-600" />
            </div>
            <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
              <div>
                <div className="text-2xl font-bold text-purple-600">{communications.filter(c => c.status === 'delivered').length}</div>
                <div className="text-sm text-gray-600">Delivered Messages</div>
              </div>
              <MessageSquare className="w-8 h-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>

        {/* Ticket Analytics */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Support Tickets</CardTitle>
            <CardDescription>Current ticket status</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 border border-gray-200 rounded-lg">
                <div className="text-xl font-bold text-blue-600">{tickets.filter(t => t.status === 'open').length}</div>
                <div className="text-xs text-gray-600">Open</div>
              </div>
              <div className="p-3 border border-gray-200 rounded-lg">
                <div className="text-xl font-bold text-yellow-600">{tickets.filter(t => t.status === 'in_progress').length}</div>
                <div className="text-xs text-gray-600">In Progress</div>
              </div>
              <div className="p-3 border border-gray-200 rounded-lg">
                <div className="text-xl font-bold text-green-600">{tickets.filter(t => t.status === 'resolved').length}</div>
                <div className="text-xs text-gray-600">Resolved</div>
              </div>
              <div className="p-3 border border-gray-200 rounded-lg">
                <div className="text-xl font-bold text-gray-600">{tickets.filter(t => t.status === 'closed').length}</div>
                <div className="text-xs text-gray-600">Closed</div>
              </div>
            </div>
            <div className="pt-3 border-t border-gray-200">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Urgent Priority</span>
                <Badge variant="destructive">{tickets.filter(t => t.priority === 'urgent').length}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upcoming Appointments */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Upcoming Appointments</CardTitle>
                <CardDescription>Next {upcomingAppointments.length} scheduled appointments</CardDescription>
              </div>
              <Button variant="ghost" size="sm">
                View All
                <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {upcomingAppointments.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Calendar className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No upcoming appointments</p>
              </div>
            ) : (
              <div className="space-y-3">
                {upcomingAppointments.map((apt) => (
                  <div
                    key={apt.id}
                    className="flex items-center gap-4 p-3 rounded-lg hover:bg-gray-50 transition-colors border border-gray-100"
                  >
                    <Avatar>
                      <AvatarFallback>
                        {apt.patient?.name
                          ?.split(' ')
                          .map((n) => n[0])
                          .join('')
                          .toUpperCase() || '?'}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{apt.patient?.name || 'Unknown'}</p>
                      <p className="text-xs text-gray-500">{apt.appointment_type || 'General'}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">
                        {new Date(apt.scheduled_at).toLocaleTimeString('en-US', {
                          hour: 'numeric',
                          minute: '2-digit',
                        })}
                      </p>
                      <p className="text-xs text-gray-500">{formatSmartDate(apt.scheduled_at)}</p>
                    </div>
                    <Badge variant={apt.status === 'confirmed' ? 'success' : 'default'}>
                      {apt.status}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Communications */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Recent Communications</CardTitle>
                <CardDescription>Latest patient messages</CardDescription>
              </div>
              <Button variant="ghost" size="sm">
                View All
                <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {communications.slice(0, 5).map((comm) => (
              <div
                key={comm.id}
                className="flex items-start gap-3 py-3 border-b border-gray-100 last:border-0"
              >
                <div className="w-2 h-2 mt-2 rounded-full bg-blue-600" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-900 truncate">
                    {comm.channel === 'email' && comm.subject ? comm.subject : comm.message?.substring(0, 50) || 'No message'}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant="outline" className="text-xs">
                      {comm.channel}
                    </Badge>
                    <span className="text-xs text-gray-500">{formatSmartDate(comm.sent_at || comm.created_at)}</span>
                  </div>
                </div>
                <Badge variant={comm.status === 'delivered' ? 'success' : comm.status === 'failed' ? 'destructive' : 'default'}>
                  {comm.status}
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* AI Suggestions */}
      <Card className="bg-gradient-to-br from-blue-50 to-purple-50 border-blue-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-blue-600" />
            AI Suggestions
          </CardTitle>
          <CardDescription>Smart recommendations powered by AI</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <SuggestionItem suggestion="Send reminders to 12 patients with appointments tomorrow" />
            <SuggestionItem suggestion="3 patients have missed follow-up appointments - create callbacks" />
            <SuggestionItem suggestion="Update billing for 5 completed appointments from yesterday" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function StatCard({
  title,
  value,
  change,
  icon,
  color,
}: {
  title: string;
  value: string;
  change: string;
  icon: React.ReactNode;
  color: "blue" | "purple" | "green" | "orange";
}) {
  const colorClasses = {
    blue: "bg-blue-50 text-blue-600",
    purple: "bg-purple-50 text-purple-600",
    green: "bg-green-50 text-green-600",
    orange: "bg-orange-50 text-orange-600",
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>{icon}</div>
        <span
          className={`text-sm font-medium ${
            change.startsWith("+") ? "text-green-600" : "text-red-600"
          }`}
        >
          {change}
        </span>
      </div>
      <h3 className="text-2xl font-bold text-gray-900">{value}</h3>
      <p className="text-sm text-gray-600 mt-1">{title}</p>
    </div>
  );
}

function ActivityItem({
  type,
  message,
  time,
}: {
  type: string;
  message: string;
  time: string;
}) {
  return (
    <div className="flex items-start gap-3">
      <div className="w-2 h-2 mt-2 rounded-full bg-blue-600" />
      <div className="flex-1">
        <p className="text-sm text-gray-900">{message}</p>
        <p className="text-xs text-gray-500 mt-1">{time}</p>
      </div>
    </div>
  );
}

function AppointmentItem({
  patientName,
  doctor,
  time,
  speciality,
}: {
  patientName: string;
  doctor: string;
  time: string;
  speciality: string;
}) {
  return (
    <div className="flex items-center gap-4 p-3 rounded-lg hover:bg-gray-50 transition-colors">
      <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-semibold">
        {patientName.split(" ").map((n) => n[0]).join("")}
      </div>
      <div className="flex-1">
        <p className="text-sm font-medium text-gray-900">{patientName}</p>
        <p className="text-xs text-gray-500">
          {doctor} • {speciality}
        </p>
      </div>
      <div className="text-right">
        <p className="text-sm font-medium text-gray-900">{time}</p>
      </div>
    </div>
  );
}

function SuggestionItem({ suggestion }: { suggestion: string }) {
  return (
    <div className="flex items-start gap-3 p-3 bg-white rounded-lg border border-blue-200">
      <div className="flex-1">
        <p className="text-sm text-gray-700">{suggestion}</p>
      </div>
      <button className="text-xs font-medium text-blue-600 hover:text-blue-700 whitespace-nowrap">
        Execute
      </button>
    </div>
  );
}
