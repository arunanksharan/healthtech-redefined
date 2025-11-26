"use client";

// Provider Telehealth Dashboard
// EPIC-UX-008: Telehealth Experience

import React, { useEffect, useState, useCallback } from "react";
import { format, isToday, isBefore, isAfter, addMinutes } from "date-fns";
import {
  Video,
  Clock,
  Calendar,
  User,
  Check,
  AlertCircle,
  Loader2,
  Play,
  FileText,
  RefreshCw,
  Settings,
  MoreVertical,
  ChevronRight,
  Plus,
  Phone,
  MessageSquare,
  Users,
  Activity,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  useTelehealthStore,
  type TelehealthSession,
  type WaitingRoomPatient,
} from "@/lib/store/telehealth-store";

// ============================================================================
// Types
// ============================================================================

interface TelehealthDashboardProps {
  onStartSession: (sessionId: string) => void;
  onViewChart: (patientId: string) => void;
  onViewPreVisitNotes: (sessionId: string) => void;
}

// ============================================================================
// Sub-Components
// ============================================================================

// Stats Overview
function StatsOverview({
  waitingCount,
  todayCount,
  nextSession,
}: {
  waitingCount: number;
  todayCount: number;
  nextSession?: Date;
}) {
  return (
    <div className="flex items-center gap-6 text-sm">
      <div className="flex items-center gap-2">
        <div
          className={cn(
            "w-3 h-3 rounded-full",
            waitingCount > 0 ? "bg-green-500 animate-pulse" : "bg-muted"
          )}
        />
        <span>
          <strong>{waitingCount}</strong> Patient{waitingCount !== 1 ? "s" : ""} Waiting
        </span>
      </div>
      <div className="flex items-center gap-2 text-muted-foreground">
        <Calendar className="h-4 w-4" />
        <span>
          <strong>{todayCount}</strong> Sessions Today
        </span>
      </div>
      {nextSession && (
        <div className="flex items-center gap-2 text-muted-foreground">
          <Clock className="h-4 w-4" />
          <span>
            Next: <strong>{format(nextSession, "h:mm a")}</strong>
          </span>
        </div>
      )}
    </div>
  );
}

// Waiting Patient Card
interface WaitingPatientCardProps {
  patient: WaitingRoomPatient;
  onStartSession: () => void;
  onViewChart: () => void;
  onViewPreVisitNotes: () => void;
}

function WaitingPatientCard({
  patient,
  onStartSession,
  onViewChart,
  onViewPreVisitNotes,
}: WaitingPatientCardProps) {
  const waitMinutes = Math.floor(patient.waitingDuration / 60);

  return (
    <Card className="overflow-hidden">
      <CardContent className="p-4">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
            {patient.patient.photo ? (
              <img
                src={patient.patient.photo}
                alt={patient.patient.name}
                className="w-12 h-12 rounded-full object-cover"
              />
            ) : (
              <User className="h-6 w-6 text-primary" />
            )}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h4 className="font-semibold">{patient.patient.name}</h4>
              <Badge
                variant="secondary"
                className={cn(
                  "text-xs",
                  waitMinutes > 10
                    ? "bg-amber-100 text-amber-700"
                    : "bg-muted"
                )}
              >
                <Clock className="h-3 w-3 mr-1" />
                {waitMinutes} min
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground">
              {patient.reason} • {format(new Date(patient.appointmentTime), "h:mm a")}
            </p>

            {/* Device Status */}
            <div className="flex items-center gap-2 mt-2">
              {patient.deviceCheckPassed ? (
                <Badge variant="secondary" className="text-xs bg-green-100 text-green-700">
                  <Check className="h-3 w-3 mr-1" />
                  Ready (Device check passed)
                </Badge>
              ) : (
                <Badge variant="secondary" className="text-xs bg-amber-100 text-amber-700">
                  <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                  Device check in progress...
                </Badge>
              )}
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <Button
              size="sm"
              onClick={onStartSession}
              disabled={!patient.deviceCheckPassed}
              className="gap-2"
            >
              <Play className="h-4 w-4" />
              Start Session
            </Button>
            <div className="flex gap-1">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onViewChart}>
                      <FileText className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>View Chart</TooltipContent>
                </Tooltip>
              </TooltipProvider>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onViewPreVisitNotes}>
                      <MessageSquare className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Pre-visit Notes</TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Upcoming Session Row
interface UpcomingSessionRowProps {
  session: TelehealthSession;
  onViewChart: () => void;
  onMessage: () => void;
}

function UpcomingSessionRow({ session, onViewChart, onMessage }: UpcomingSessionRowProps) {
  const appointmentTime = new Date(session.appointmentTime);
  const isStartingSoon = isBefore(appointmentTime, addMinutes(new Date(), 15));

  return (
    <div className="flex items-center justify-between py-3 px-4 hover:bg-muted/50 rounded-lg transition-colors">
      <div className="flex items-center gap-4">
        <span className="text-sm font-medium w-16 text-muted-foreground">
          {format(appointmentTime, "h:mm a")}
        </span>
        <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
          <User className="h-4 w-4 text-muted-foreground" />
        </div>
        <div>
          <p className="text-sm font-medium">{session.patient.name}</p>
          <p className="text-xs text-muted-foreground">{session.reason}</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {isStartingSoon && (
          <Badge variant="secondary" className="text-xs bg-blue-100 text-blue-700">
            Starting soon
          </Badge>
        )}
        <Badge
          variant="outline"
          className={cn(
            "text-xs",
            session.status === "scheduled"
              ? "border-blue-300 text-blue-700"
              : "border-muted"
          )}
        >
          {session.status === "scheduled" ? "🔵 Scheduled" : session.status}
        </Badge>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={onViewChart}>
              <FileText className="h-4 w-4 mr-2" />
              View Chart
            </DropdownMenuItem>
            <DropdownMenuItem onClick={onMessage}>
              <MessageSquare className="h-4 w-4 mr-2" />
              Send Message
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-destructive">
              Cancel Appointment
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}

// Quick Stats Card
function QuickStatsCard({
  icon,
  label,
  value,
  trend,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  trend?: { value: number; isPositive: boolean };
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
            {icon}
          </div>
          <div>
            <p className="text-xs text-muted-foreground">{label}</p>
            <p className="text-xl font-semibold">{value}</p>
            {trend && (
              <p
                className={cn(
                  "text-xs",
                  trend.isPositive ? "text-green-600" : "text-red-600"
                )}
              >
                {trend.isPositive ? "↑" : "↓"} {Math.abs(trend.value)}% vs last week
              </p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function TelehealthDashboard({
  onStartSession,
  onViewChart,
  onViewPreVisitNotes,
}: TelehealthDashboardProps) {
  const [activeTab, setActiveTab] = useState("today");

  const {
    todaySessions,
    waitingRoom,
    isLoadingSessions,
    fetchTodaySessions,
    fetchWaitingRoom,
  } = useTelehealthStore();

  // Fetch data on mount
  useEffect(() => {
    fetchTodaySessions();
    fetchWaitingRoom();

    // Refresh waiting room every 30 seconds
    const interval = setInterval(fetchWaitingRoom, 30000);
    return () => clearInterval(interval);
  }, [fetchTodaySessions, fetchWaitingRoom]);

  // Filter sessions
  const waitingPatients = waitingRoom.filter((p) => p.deviceCheckPassed);
  const upcomingSessions = todaySessions.filter(
    (s) => s.status === "scheduled" && isAfter(new Date(s.appointmentTime), new Date())
  );
  const completedSessions = todaySessions.filter((s) => s.status === "completed");

  // Next session time
  const nextSession = upcomingSessions[0]
    ? new Date(upcomingSessions[0].appointmentTime)
    : undefined;

  if (isLoadingSessions) {
    return <TelehealthDashboardSkeleton />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Today's Telehealth</h1>
          <p className="text-sm text-muted-foreground">
            {format(new Date(), "EEEE, MMMM d, yyyy")}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              fetchTodaySessions();
              fetchWaitingRoom();
            }}
          >
            <RefreshCw className="h-4 w-4 mr-1" />
            Refresh
          </Button>
          <Button variant="outline" size="sm">
            <Settings className="h-4 w-4 mr-1" />
            Settings
          </Button>
        </div>
      </div>

      {/* Stats Overview */}
      <StatsOverview
        waitingCount={waitingPatients.length}
        todayCount={todaySessions.length}
        nextSession={nextSession}
      />

      {/* Quick Stats */}
      <div className="grid grid-cols-4 gap-4">
        <QuickStatsCard
          icon={<Video className="h-5 w-5 text-primary" />}
          label="Sessions Today"
          value={todaySessions.length}
        />
        <QuickStatsCard
          icon={<Users className="h-5 w-5 text-green-600" />}
          label="Patients Seen"
          value={completedSessions.length}
        />
        <QuickStatsCard
          icon={<Clock className="h-5 w-5 text-amber-600" />}
          label="Avg Wait Time"
          value="4 min"
        />
        <QuickStatsCard
          icon={<Activity className="h-5 w-5 text-blue-600" />}
          label="Completion Rate"
          value="98%"
          trend={{ value: 2, isPositive: true }}
        />
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Waiting Now Section */}
        <div className="col-span-2 space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                  Waiting Now
                  {waitingPatients.length > 0 && (
                    <Badge variant="secondary" className="ml-2">
                      {waitingPatients.length}
                    </Badge>
                  )}
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              {waitingPatients.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Users className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>No patients waiting</p>
                  <p className="text-xs mt-1">
                    Patients will appear here when they join the waiting room
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {waitingPatients.map((patient) => (
                    <WaitingPatientCard
                      key={patient.sessionId}
                      patient={patient}
                      onStartSession={() => onStartSession(patient.sessionId)}
                      onViewChart={() => onViewChart(patient.patient.id)}
                      onViewPreVisitNotes={() => onViewPreVisitNotes(patient.sessionId)}
                    />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Upcoming Sessions */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Upcoming</CardTitle>
            </CardHeader>
            <CardContent>
              {upcomingSessions.length === 0 ? (
                <div className="text-center py-6 text-muted-foreground">
                  <Calendar className="h-6 w-6 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No more sessions scheduled for today</p>
                </div>
              ) : (
                <div className="space-y-1">
                  {upcomingSessions.map((session) => (
                    <UpcomingSessionRow
                      key={session.id}
                      session={session}
                      onViewChart={() => onViewChart(session.patient.id)}
                      onMessage={() => {}}
                    />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Quick Actions */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button variant="outline" className="w-full justify-start">
                <Plus className="h-4 w-4 mr-2" />
                Schedule Telehealth Visit
              </Button>
              <Button variant="outline" className="w-full justify-start">
                <MessageSquare className="h-4 w-4 mr-2" />
                Send Reminder
              </Button>
              <Button variant="outline" className="w-full justify-start">
                <FileText className="h-4 w-4 mr-2" />
                View Pending Documentation
              </Button>
            </CardContent>
          </Card>

          {/* Today's Completed */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <Check className="h-4 w-4 text-green-600" />
                Completed Today
              </CardTitle>
            </CardHeader>
            <CardContent>
              {completedSessions.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">
                  No completed sessions yet
                </p>
              ) : (
                <ScrollArea className="h-48">
                  <div className="space-y-2">
                    {completedSessions.map((session) => (
                      <div
                        key={session.id}
                        className="flex items-center justify-between py-2 px-2 rounded-lg hover:bg-muted/50"
                      >
                        <div className="flex items-center gap-2">
                          <Check className="h-4 w-4 text-green-600" />
                          <div>
                            <p className="text-sm font-medium">
                              {session.patient.name}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {session.reason}
                            </p>
                          </div>
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {format(new Date(session.appointmentTime), "h:mm a")}
                        </span>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              )}
            </CardContent>
          </Card>

          {/* Tips */}
          <Card className="bg-blue-50 border-blue-200">
            <CardContent className="p-4">
              <h4 className="text-sm font-medium text-blue-800 mb-2">
                💡 Telehealth Tips
              </h4>
              <ul className="text-xs text-blue-700 space-y-1">
                <li>• Test your audio/video before each session</li>
                <li>• Use AI transcription to streamline documentation</li>
                <li>• Review patient chart before starting the call</li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Skeleton
// ============================================================================

export function TelehealthDashboardSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="flex items-center justify-between">
        <div>
          <div className="h-8 w-48 bg-muted rounded mb-2" />
          <div className="h-4 w-40 bg-muted rounded" />
        </div>
        <div className="flex gap-2">
          <div className="h-9 w-24 bg-muted rounded" />
          <div className="h-9 w-24 bg-muted rounded" />
        </div>
      </div>

      <div className="flex items-center gap-6">
        <div className="h-4 w-32 bg-muted rounded" />
        <div className="h-4 w-28 bg-muted rounded" />
        <div className="h-4 w-24 bg-muted rounded" />
      </div>

      <div className="grid grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="border rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-muted rounded-lg" />
              <div>
                <div className="h-3 w-16 bg-muted rounded mb-2" />
                <div className="h-6 w-8 bg-muted rounded" />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-4">
          <div className="border rounded-lg p-6">
            <div className="h-5 w-32 bg-muted rounded mb-4" />
            <div className="space-y-3">
              {Array.from({ length: 2 }).map((_, i) => (
                <div key={i} className="h-24 bg-muted rounded" />
              ))}
            </div>
          </div>
        </div>
        <div className="space-y-4">
          <div className="border rounded-lg p-6">
            <div className="h-5 w-28 bg-muted rounded mb-4" />
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-9 bg-muted rounded" />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default TelehealthDashboard;
