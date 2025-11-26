"use client";

// Mobile Provider Home - Provider Mobile Dashboard
// EPIC-UX-012: Mobile Applications - Journey 12.3

import React, { useEffect, useState } from "react";
import { format, isToday, differenceInMinutes, parseISO } from "date-fns";
import {
  Calendar, Users, AlertTriangle, MessageSquare, ClipboardList, Phone,
  ChevronRight, Bell, RefreshCw, Search, Clock, User, Building2,
  Activity, Stethoscope, FileText, CheckCircle, XCircle, Loader2,
  ArrowRight, TrendingUp, Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { Input } from "@/components/ui/input";
import { useMobileStore, type ProviderAlert, type QuickPatient } from "@/lib/store/mobile-store";

// Alert priority indicator
function AlertPriorityBadge({ priority }: { priority: ProviderAlert["priority"] }) {
  const config = {
    high: { label: "High", className: "bg-red-100 text-red-700 border-red-200" },
    medium: { label: "Medium", className: "bg-amber-100 text-amber-700 border-amber-200" },
    low: { label: "Low", className: "bg-blue-100 text-blue-700 border-blue-200" },
  };
  return (
    <Badge variant="outline" className={cn("text-xs", config[priority].className)}>
      {config[priority].label}
    </Badge>
  );
}

// Alert type icon
function getAlertIcon(type: ProviderAlert["type"]) {
  switch (type) {
    case "critical_lab": return AlertTriangle;
    case "consult_request": return Stethoscope;
    case "rx_refill": return ClipboardList;
    case "patient_message": return MessageSquare;
    case "schedule_change": return Calendar;
    default: return Bell;
  }
}

// Provider alert card (mobile optimized)
interface AlertCardMobileProps {
  alert: ProviderAlert;
  onAcknowledge: () => void;
  onViewDetails: () => void;
}

function AlertCardMobile({ alert, onAcknowledge, onViewDetails }: AlertCardMobileProps) {
  const Icon = getAlertIcon(alert.type);
  const timeAgo = differenceInMinutes(new Date(), parseISO(alert.timestamp));
  const timeLabel = timeAgo < 60 ? `${timeAgo}m ago` : `${Math.floor(timeAgo / 60)}h ago`;

  return (
    <Card className={cn(
      "overflow-hidden",
      alert.priority === "high" && !alert.acknowledged && "border-red-200 bg-red-50/30"
    )}>
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <div className={cn(
            "h-10 w-10 rounded-full flex items-center justify-center",
            alert.priority === "high" ? "bg-red-100" : "bg-muted"
          )}>
            <Icon className={cn(
              "h-5 w-5",
              alert.priority === "high" ? "text-red-600" : "text-muted-foreground"
            )} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2">
              <span className="font-semibold text-sm truncate">{alert.title}</span>
              <AlertPriorityBadge priority={alert.priority} />
            </div>
            {alert.patientName && (
              <p className="text-sm font-medium mt-1">
                {alert.patientName} <span className="text-muted-foreground">({alert.patientMrn})</span>
              </p>
            )}
            <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{alert.message}</p>
            <p className="text-xs text-muted-foreground mt-2">{timeLabel}</p>
          </div>
        </div>
        {!alert.acknowledged && (
          <div className="flex gap-2 mt-3">
            <Button size="sm" className="flex-1" onClick={onViewDetails}>
              View Details
            </Button>
            <Button size="sm" variant="outline" onClick={onAcknowledge}>
              <CheckCircle className="h-4 w-4 mr-1" /> Acknowledge
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Schedule item for today
interface ScheduleItemProps {
  appointment: {
    id: string;
    time: string;
    patientName: string;
    patientMrn: string;
    type: string;
    status: "scheduled" | "checked_in" | "in_progress" | "completed";
  };
  onViewPatient: () => void;
}

function ScheduleItem({ appointment, onViewPatient }: ScheduleItemProps) {
  const statusConfig = {
    scheduled: { label: "Scheduled", className: "bg-muted text-muted-foreground" },
    checked_in: { label: "Checked In", className: "bg-green-100 text-green-700" },
    in_progress: { label: "In Progress", className: "bg-blue-100 text-blue-700" },
    completed: { label: "Complete", className: "bg-muted text-muted-foreground" },
  };

  return (
    <button
      onClick={onViewPatient}
      className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-muted/50 transition-colors text-left"
    >
      <div className="text-center min-w-[50px]">
        <p className="text-sm font-semibold">{appointment.time}</p>
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-medium truncate">{appointment.patientName}</p>
        <p className="text-xs text-muted-foreground">{appointment.type} • MRN: {appointment.patientMrn}</p>
      </div>
      <Badge variant="secondary" className={cn("text-xs shrink-0", statusConfig[appointment.status].className)}>
        {statusConfig[appointment.status].label}
      </Badge>
      <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
    </button>
  );
}

// Recent patient card
interface RecentPatientCardProps {
  patient: QuickPatient;
  onSelect: () => void;
}

function RecentPatientCard({ patient, onSelect }: RecentPatientCardProps) {
  return (
    <button
      onClick={onSelect}
      className="flex flex-col items-center p-3 rounded-lg bg-muted/50 min-w-[100px] hover:bg-muted transition-colors"
    >
      <Avatar className="h-12 w-12 mb-2">
        <AvatarFallback>{patient.name.split(" ").map(n => n[0]).join("")}</AvatarFallback>
      </Avatar>
      <p className="text-xs font-medium text-center truncate w-full">{patient.name}</p>
      <p className="text-[10px] text-muted-foreground">MRN: {patient.mrn}</p>
      {patient.hasActiveAlerts && (
        <AlertTriangle className="h-3 w-3 text-amber-500 mt-1" />
      )}
    </button>
  );
}

// Stats card
interface StatCardProps {
  label: string;
  value: string | number;
  icon: typeof Calendar;
  trend?: "up" | "down" | "neutral";
  color?: string;
}

function StatCard({ label, value, icon: Icon, trend, color = "text-primary" }: StatCardProps) {
  return (
    <div className="p-3 bg-muted/50 rounded-lg">
      <div className="flex items-center justify-between mb-1">
        <Icon className={cn("h-4 w-4", color)} />
        {trend && (
          <TrendingUp className={cn(
            "h-3 w-3",
            trend === "up" ? "text-green-500" : trend === "down" ? "text-red-500 rotate-180" : "text-muted-foreground"
          )} />
        )}
      </div>
      <p className="text-lg font-bold">{value}</p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  );
}

// Main Mobile Provider Home Component
export function MobileProviderHome() {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const {
    providerAlerts,
    unacknowledgedAlerts,
    recentPatients,
    searchResults,
    isSearching,
    fetchProviderAlerts,
    acknowledgeAlert,
    searchPatients,
    addToRecentPatients,
  } = useMobileStore();

  useEffect(() => {
    fetchProviderAlerts();
  }, [fetchProviderAlerts]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await fetchProviderAlerts();
    setIsRefreshing(false);
  };

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    if (query.length >= 2) {
      searchPatients(query);
    }
  };

  // Mock today's schedule
  const todaySchedule = [
    { id: "s1", time: "9:00 AM", patientName: "John Doe", patientMrn: "12345", type: "Follow-up", status: "completed" as const },
    { id: "s2", time: "9:30 AM", patientName: "Mary Johnson", patientMrn: "67890", type: "Annual Physical", status: "in_progress" as const },
    { id: "s3", time: "10:00 AM", patientName: "Bob Wilson", patientMrn: "11111", type: "New Patient", status: "checked_in" as const },
    { id: "s4", time: "10:30 AM", patientName: "Alice Brown", patientMrn: "22222", type: "Follow-up", status: "scheduled" as const },
    { id: "s5", time: "11:00 AM", patientName: "Charlie Davis", patientMrn: "33333", type: "Telehealth", status: "scheduled" as const },
  ];

  const criticalAlerts = providerAlerts.filter(a => a.priority === "high" && !a.acknowledged);

  return (
    <div className="min-h-screen bg-background pb-20">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-background border-b">
        <div className="flex items-center justify-between p-4">
          <div>
            <p className="text-sm text-muted-foreground">{format(new Date(), "EEEE, MMMM d")}</p>
            <h1 className="text-xl font-semibold">Provider Dashboard</h1>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" onClick={handleRefresh} disabled={isRefreshing}>
              <RefreshCw className={cn("h-5 w-5", isRefreshing && "animate-spin")} />
            </Button>
            <Button variant="ghost" size="icon" className="relative">
              <Bell className="h-5 w-5" />
              {unacknowledgedAlerts > 0 && (
                <span className="absolute top-1 right-1 h-4 w-4 rounded-full bg-red-500 text-white text-[10px] flex items-center justify-center">
                  {unacknowledgedAlerts > 9 ? "9+" : unacknowledgedAlerts}
                </span>
              )}
            </Button>
          </div>
        </div>

        {/* Search */}
        <div className="px-4 pb-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search patients (name or MRN)..."
              className="pl-9"
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
            />
            {isSearching && (
              <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin" />
            )}
          </div>
          {searchQuery.length >= 2 && searchResults.length > 0 && (
            <Card className="absolute left-4 right-4 mt-1 z-20">
              <CardContent className="p-2">
                {searchResults.map((patient) => (
                  <button
                    key={patient.id}
                    className="w-full flex items-center gap-3 p-2 rounded hover:bg-muted transition-colors text-left"
                    onClick={() => {
                      addToRecentPatients(patient);
                      setSearchQuery("");
                    }}
                  >
                    <Avatar className="h-8 w-8">
                      <AvatarFallback className="text-xs">
                        {patient.name.split(" ").map(n => n[0]).join("")}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{patient.name}</p>
                      <p className="text-xs text-muted-foreground">
                        MRN: {patient.mrn} • {patient.age}y {patient.gender}
                      </p>
                    </div>
                    {patient.hasActiveAlerts && (
                      <AlertTriangle className="h-4 w-4 text-amber-500" />
                    )}
                  </button>
                ))}
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      <div className="p-4 space-y-6">
        {/* Critical Alerts Banner */}
        {criticalAlerts.length > 0 && (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-red-100 flex items-center justify-center">
                  <AlertTriangle className="h-5 w-5 text-red-600" />
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-red-900">{criticalAlerts.length} Critical Alert{criticalAlerts.length > 1 ? "s" : ""}</p>
                  <p className="text-sm text-red-700">Requires immediate attention</p>
                </div>
                <Button size="sm" variant="destructive">
                  View <ArrowRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Today's Stats */}
        <div className="grid grid-cols-3 gap-3">
          <StatCard
            label="Patients Today"
            value={todaySchedule.length}
            icon={Users}
            color="text-blue-600"
          />
          <StatCard
            label="Seen"
            value={todaySchedule.filter(s => s.status === "completed").length}
            icon={CheckCircle}
            color="text-green-600"
          />
          <StatCard
            label="Pending"
            value={todaySchedule.filter(s => s.status !== "completed").length}
            icon={Clock}
            color="text-amber-600"
          />
        </div>

        {/* Recent Patients */}
        {recentPatients.length > 0 && (
          <div className="space-y-3">
            <h2 className="font-semibold">Recent Patients</h2>
            <ScrollArea className="w-full">
              <div className="flex gap-3 pb-2">
                {recentPatients.map((patient) => (
                  <RecentPatientCard
                    key={patient.id}
                    patient={patient}
                    onSelect={() => {}}
                  />
                ))}
              </div>
              <ScrollBar orientation="horizontal" />
            </ScrollArea>
          </div>
        )}

        {/* Today's Schedule */}
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Today's Schedule
              </CardTitle>
              <Button variant="ghost" size="sm">
                Full Schedule <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y">
              {todaySchedule.map((apt) => (
                <ScheduleItem
                  key={apt.id}
                  appointment={apt}
                  onViewPatient={() => {}}
                />
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Provider Alerts */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Alerts & Notifications</h2>
            <Button variant="ghost" size="sm">
              View All <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          </div>
          {providerAlerts.length === 0 ? (
            <Card>
              <CardContent className="py-6 text-center">
                <CheckCircle className="h-8 w-8 mx-auto text-green-500 mb-2" />
                <p className="text-sm text-muted-foreground">No pending alerts</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {providerAlerts.slice(0, 3).map((alert) => (
                <AlertCardMobile
                  key={alert.id}
                  alert={alert}
                  onAcknowledge={() => acknowledgeAlert(alert.id)}
                  onViewDetails={() => {}}
                />
              ))}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-2 gap-3">
          <Button variant="outline" className="h-auto py-4 flex flex-col gap-2">
            <Stethoscope className="h-5 w-5" />
            <span className="text-sm">Request Consult</span>
          </Button>
          <Button variant="outline" className="h-auto py-4 flex flex-col gap-2">
            <ClipboardList className="h-5 w-5" />
            <span className="text-sm">Start Handoff</span>
          </Button>
          <Button variant="outline" className="h-auto py-4 flex flex-col gap-2">
            <Phone className="h-5 w-5" />
            <span className="text-sm">On-Call Schedule</span>
          </Button>
          <Button variant="outline" className="h-auto py-4 flex flex-col gap-2">
            <MessageSquare className="h-5 w-5" />
            <span className="text-sm">Messages</span>
          </Button>
        </div>
      </div>

      {/* Bottom Navigation */}
      <div className="fixed bottom-0 left-0 right-0 bg-background border-t">
        <div className="flex items-center justify-around py-2">
          {[
            { icon: Activity, label: "Home", active: true },
            { icon: Calendar, label: "Schedule", active: false },
            { icon: Users, label: "Patients", active: false },
            { icon: MessageSquare, label: "Messages", active: false },
            { icon: User, label: "Profile", active: false },
          ].map((item, i) => (
            <button
              key={i}
              className={cn(
                "flex flex-col items-center gap-1 p-2",
                item.active ? "text-primary" : "text-muted-foreground"
              )}
            >
              <item.icon className="h-5 w-5" />
              <span className="text-[10px]">{item.label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

// Compact alerts widget
export function ProviderAlertsWidget() {
  const { providerAlerts, unacknowledgedAlerts } = useMobileStore();
  const critical = providerAlerts.filter(a => a.priority === "high" && !a.acknowledged);

  return (
    <div className="space-y-2">
      {critical.length > 0 && (
        <div className="flex items-center gap-2 p-2 bg-red-50 rounded-lg border border-red-200">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <span className="text-sm font-medium text-red-900">{critical.length} critical alerts</span>
        </div>
      )}
      <p className="text-xs text-muted-foreground">
        {unacknowledgedAlerts} unacknowledged alert{unacknowledgedAlerts !== 1 ? "s" : ""}
      </p>
    </div>
  );
}

export default MobileProviderHome;
