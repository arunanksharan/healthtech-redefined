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
import { MagicCard } from '@/components/ui/magic-card';
import { NumberTicker } from '@/components/ui/number-ticker';
import { BorderBeam } from '@/components/ui/border-beam';

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

  // Real journey instance stats from backend
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
    activeJourneys: journeyInstanceStats?.active ?? journeys.filter(j => j.status === 'active').length,
    messagesSent: communications.length,
    pendingTickets: tickets.filter(t => t.status === 'open' || t.status === 'in_progress').length,
    totalPatients: patients.length,
    completedAppointments: appointments.filter(a => a.status === 'completed').length,
    confirmedAppointments: appointments.filter(a => a.status === 'confirmed').length,
    cancelledAppointments: appointments.filter(a => a.status === 'cancelled').length,
    // New journey stats from backend
    totalJourneys: journeyInstanceStats?.total ?? journeys.length,
    completedJourneys: journeyInstanceStats?.completed ?? 0,
    cancelledJourneys: journeyInstanceStats?.cancelled ?? 0,
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
        <h1 className="text-3xl font-bold text-foreground">Welcome back!</h1>
        <p className="text-muted-foreground mt-1">Here's what's happening with your patients today.</p>
      </div>

      {/* Stats Cards - Upgraded with MagicCard & NumberTicker */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MagicStatCard
          title="Today's Appointments"
          value={stats.todaysAppointments}
          change="+12%"
          icon={<Calendar className="w-6 h-6" />}
          color="blue"
        />
        <MagicStatCard
          title="Active Journeys"
          value={stats.activeJourneys}
          change="+8%"
          icon={<Users className="w-6 h-6" />}
          color="purple"
        />
        <MagicStatCard
          title="Messages Sent"
          value={stats.messagesSent}
          change="+23%"
          icon={<MessageSquare className="w-6 h-6" />}
          color="green"
        />
        <MagicStatCard
          title="Pending Tickets"
          value={stats.pendingTickets}
          change="-4%"
          icon={<Ticket className="w-6 h-6" />}
          color="orange"
        />
      </div>

      {/* Analytics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Appointment Status Breakdown */}
        <Card className="border-border shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg">Appointment Status</CardTitle>
            <CardDescription>Current appointment distribution</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600" />
                  <span className="text-sm text-muted-foreground">Confirmed</span>
                </div>
                <span className="text-sm font-medium">{stats.confirmedAppointments}</span>
              </div>
              <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-green-500 transition-all duration-500"
                  style={{
                    width: `${appointments.length ? (stats.confirmedAppointments / appointments.length) * 100 : 0}%`,
                  }}
                />
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-blue-600" />
                  <span className="text-sm text-muted-foreground">Completed</span>
                </div>
                <span className="text-sm font-medium">{stats.completedAppointments}</span>
              </div>
              <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 transition-all duration-500"
                  style={{
                    width: `${appointments.length ? (stats.completedAppointments / appointments.length) * 100 : 0}%`,
                  }}
                />
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-red-600" />
                  <span className="text-sm text-muted-foreground">Cancelled</span>
                </div>
                <span className="text-sm font-medium">{stats.cancelledAppointments}</span>
              </div>
              <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-red-500 transition-all duration-500"
                  style={{
                    width: `${appointments.length ? (stats.cancelledAppointments / appointments.length) * 100 : 0}%`,
                  }}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Patient Engagement */}
        <Card className="border-border shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg">Patient Engagement</CardTitle>
            <CardDescription>Communication & journey metrics</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-blue-50 dark:bg-blue-900/10 rounded-lg">
              <div>
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  <NumberTicker value={stats.totalPatients} />
                </div>
                <div className="text-sm text-muted-foreground">Total Patients</div>
              </div>
              <Users className="w-8 h-8 text-blue-600 dark:text-blue-400" />
            </div>
            <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/10 rounded-lg">
              <div>
                <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                  <NumberTicker value={stats.activeJourneys} />
                </div>
                <div className="text-sm text-muted-foreground">Active Journeys</div>
              </div>
              <Activity className="w-8 h-8 text-green-600 dark:text-green-400" />
            </div>
            <div className="flex items-center justify-between p-3 bg-purple-50 dark:bg-purple-900/10 rounded-lg">
              <div>
                <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                  <NumberTicker value={communications.filter(c => c.status === 'delivered').length} />
                </div>
                <div className="text-sm text-muted-foreground">Delivered Messages</div>
              </div>
              <MessageSquare className="w-8 h-8 text-purple-600 dark:text-purple-400" />
            </div>
          </CardContent>
        </Card>

        {/* Ticket Analytics */}
        <Card className="border-border shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg">Support Tickets</CardTitle>
            <CardDescription>Current ticket status</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 border border-border rounded-lg">
                <div className="text-xl font-bold text-blue-600">
                  {tickets.filter(t => t.status === 'open').length}
                </div>
                <div className="text-xs text-muted-foreground">Open</div>
              </div>
              <div className="p-3 border border-border rounded-lg">
                <div className="text-xl font-bold text-yellow-600">
                  {tickets.filter(t => t.status === 'in_progress').length}
                </div>
                <div className="text-xs text-muted-foreground">In Progress</div>
              </div>
              <div className="p-3 border border-border rounded-lg">
                <div className="text-xl font-bold text-green-600">
                  {tickets.filter(t => t.status === 'resolved').length}
                </div>
                <div className="text-xs text-muted-foreground">Resolved</div>
              </div>
              <div className="p-3 border border-border rounded-lg">
                <div className="text-xl font-bold text-muted-foreground">
                  {tickets.filter(t => t.status === 'closed').length}
                </div>
                <div className="text-xs text-muted-foreground">Closed</div>
              </div>
            </div>
            <div className="pt-3 border-t border-border">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Urgent Priority</span>
                <Badge variant="destructive">{tickets.filter(t => t.priority === 'urgent').length}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upcoming Appointments */}
        <Card className="border-border shadow-sm">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Upcoming Appointments</CardTitle>
                <CardDescription>Next {upcomingAppointments.length} scheduled appointments</CardDescription>
              </div>
              <Link href="/dashboard/appointments">
                <Button variant="ghost" size="sm">
                  View All
                  <ArrowRight className="w-4 h-4 ml-1" />
                </Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            {upcomingAppointments.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Calendar className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No upcoming appointments</p>
              </div>
            ) : (
              <div className="space-y-3">
                {upcomingAppointments.map((apt) => (
                  <div
                    key={apt.id}
                    className="flex items-center gap-4 p-3 rounded-lg hover:bg-muted/50 transition-colors border border-border/50"
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
                      <p className="text-sm font-medium text-foreground">{apt.patient?.name || 'Unknown'}</p>
                      <p className="text-xs text-muted-foreground">{apt.appointment_type || 'General'}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-foreground">
                        {new Date(apt.scheduled_at).toLocaleTimeString('en-US', {
                          hour: 'numeric',
                          minute: '2-digit',
                        })}
                      </p>
                      <p className="text-xs text-muted-foreground">{formatSmartDate(apt.scheduled_at)}</p>
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
        <Card className="border-border shadow-sm">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Recent Communications</CardTitle>
                <CardDescription>Latest patient messages</CardDescription>
              </div>
              <Link href="/dashboard/communications">
                <Button variant="ghost" size="sm">
                  View All
                  <ArrowRight className="w-4 h-4 ml-1" />
                </Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            {communications.slice(0, 5).map((comm) => (
              <div
                key={comm.id}
                className="flex items-start gap-3 py-3 border-b border-border/50 last:border-0"
              >
                <div className="w-2 h-2 mt-2 rounded-full bg-blue-600" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-foreground truncate">
                    {comm.channel === 'email' && comm.subject ? comm.subject : comm.message?.substring(0, 50) || 'No message'}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant="outline" className="text-xs">
                      {comm.channel}
                    </Badge>
                    <span className="text-xs text-muted-foreground">{formatSmartDate(comm.sent_at || comm.created_at)}</span>
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

      {/* AI Suggestions - Now with BorderBeam */}
      <div className="relative rounded-xl border border-blue-100 dark:border-blue-900/50 bg-gradient-to-br from-blue-50/50 to-purple-50/50 dark:from-blue-950/20 dark:to-purple-950/20 overflow-hidden">
        <BorderBeam size={300} duration={8} delay={4} className="from-transparent via-blue-500 to-transparent" />
        <Card className="border-0 bg-transparent shadow-none">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-blue-700">
              <Zap className="w-5 h-5 text-blue-600 fill-blue-600" />
              AI Suggestions
            </CardTitle>
            <CardDescription className="text-blue-600/80">Smart recommendations powered by AI</CardDescription>
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
    </div>
  );
}

function MagicStatCard({
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
  color: "blue" | "purple" | "green" | "orange";
}) {
  const colorClasses = {
    blue: "text-blue-600 bg-blue-50 dark:bg-blue-900/20 dark:text-blue-400",
    purple: "text-purple-600 bg-purple-50 dark:bg-purple-900/20 dark:text-purple-400",
    green: "text-green-600 bg-green-50 dark:bg-green-900/20 dark:text-green-400",
    orange: "text-orange-600 bg-orange-50 dark:bg-orange-900/20 dark:text-orange-400",
  };

  const gradientFrom = {
    blue: "hsl(var(--info))",
    purple: "hsl(var(--channel-voice))",
    green: "hsl(var(--success))",
    orange: "hsl(var(--warning))",
  };

  const gradientTo = {
    blue: "hsl(var(--info) / 0.5)",
    purple: "hsl(var(--channel-voice) / 0.5)",
    green: "hsl(var(--success) / 0.5)",
    orange: "hsl(var(--warning) / 0.5)",
  };

  // Using specific colors for the gradient background to make it pop more
  const gradientColor = {
    blue: "hsl(var(--info) / 0.2)",
    purple: "hsl(var(--channel-voice) / 0.2)",
    green: "hsl(var(--success) / 0.2)",
    orange: "hsl(var(--warning) / 0.2)",
  };

  return (
    <MagicCard
      className="flex flex-col p-6 border border-border shadow-md hover:shadow-lg transition-all"
      gradientColor={gradientColor[color]}
      gradientOpacity={0.8}
      gradientFrom={gradientFrom[color]}
      gradientTo={gradientTo[color]}
    >
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-lg ${colorClasses[color]} bg-opacity-20`}>
          {icon}
        </div>
        <div className="flex items-center gap-1">
          {change.startsWith("+") ? <TrendingUp className="w-4 h-4 text-green-600" /> : <TrendingUp className="w-4 h-4 text-red-600 rotate-180" />}
          <span
            className={`text-sm font-medium ${change.startsWith("+") ? "text-green-600" : "text-red-600"}`}
          >
            {change}
          </span>
        </div>
      </div>
      <div className="text-3xl font-bold text-foreground">
        <NumberTicker value={value} />
      </div>
      <p className="text-sm text-muted-foreground mt-1">{title}</p>
    </MagicCard>
  );
}

function SuggestionItem({ suggestion }: { suggestion: string }) {
  return (
    <div className="flex items-start gap-3 p-3 bg-background/80 rounded-lg border border-border/50 hover:bg-accent/50 hover:shadow-sm transition-all">
      <div className="flex-1">
        <p className="text-sm text-foreground">{suggestion}</p>
      </div>
      <button className="text-xs font-medium text-blue-600 hover:text-blue-700 whitespace-nowrap px-3 py-1 bg-blue-50 dark:bg-blue-900/20 dark:text-blue-400 rounded-full hover:bg-blue-100 dark:hover:bg-blue-900/40 transition-colors">
        Execute
      </button>
    </div>
  );
}
