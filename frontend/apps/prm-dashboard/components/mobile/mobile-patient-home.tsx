"use client";

// Mobile Patient Home - Patient Mobile Dashboard
// EPIC-UX-012: Mobile Applications - Journey 12.2

import React, { useEffect, useState } from "react";
import { format, isToday, isTomorrow, parseISO } from "date-fns";
import {
  Calendar, MessageSquare, Pill, FileText, CreditCard, Video,
  ChevronRight, Bell, Heart, Activity, User, Clock, AlertCircle,
  Phone, Building2, RefreshCw, Loader2, Plus, Search,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { Progress } from "@/components/ui/progress";
import { useMobileStore } from "@/lib/store/mobile-store";
import { usePatientPortalStore } from "@/lib/store/patient-portal-store";

// Quick action button
interface QuickActionProps {
  icon: typeof Calendar;
  label: string;
  onClick: () => void;
  badge?: number;
  variant?: "default" | "highlight";
}

function QuickAction({ icon: Icon, label, onClick, badge, variant = "default" }: QuickActionProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex flex-col items-center gap-2 p-4 rounded-xl transition-colors min-w-[80px]",
        variant === "highlight" ? "bg-primary text-primary-foreground" : "bg-muted/50"
      )}
    >
      <div className="relative">
        <Icon className="h-6 w-6" />
        {badge && badge > 0 && (
          <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-red-500 text-white text-[10px] flex items-center justify-center">
            {badge > 9 ? "9+" : badge}
          </span>
        )}
      </div>
      <span className="text-xs font-medium">{label}</span>
    </button>
  );
}

// Upcoming appointment card (mobile optimized)
interface AppointmentCardMobileProps {
  appointment: {
    id: string;
    date: string;
    time: string;
    provider: string;
    specialty: string;
    type: "in-person" | "telehealth" | "phone";
    location?: string;
  };
  onJoin?: () => void;
  onViewDetails?: () => void;
}

function AppointmentCardMobile({ appointment, onJoin, onViewDetails }: AppointmentCardMobileProps) {
  const appointmentDate = parseISO(`${appointment.date}T${appointment.time}`);
  const dateLabel = isToday(appointmentDate)
    ? "Today"
    : isTomorrow(appointmentDate)
    ? "Tomorrow"
    : format(appointmentDate, "EEE, MMM d");

  const typeConfig = {
    "in-person": { icon: Building2, label: "In-Person", color: "text-blue-600" },
    telehealth: { icon: Video, label: "Video Visit", color: "text-green-600" },
    phone: { icon: Phone, label: "Phone Call", color: "text-purple-600" },
  };
  const config = typeConfig[appointment.type];

  return (
    <Card className="overflow-hidden">
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <div className={cn("h-10 w-10 rounded-full flex items-center justify-center",
            appointment.type === "telehealth" ? "bg-green-100" : "bg-blue-100"
          )}>
            <config.icon className={cn("h-5 w-5", config.color)} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-sm">{dateLabel}</span>
              <span className="text-sm text-muted-foreground">{format(appointmentDate, "h:mm a")}</span>
            </div>
            <p className="font-medium mt-1 truncate">{appointment.provider}</p>
            <p className="text-sm text-muted-foreground truncate">{appointment.specialty}</p>
            {appointment.location && (
              <p className="text-xs text-muted-foreground mt-1 truncate">{appointment.location}</p>
            )}
          </div>
        </div>
        <div className="flex gap-2 mt-3">
          {appointment.type === "telehealth" && isToday(appointmentDate) && (
            <Button size="sm" className="flex-1" onClick={onJoin}>
              <Video className="h-4 w-4 mr-1" /> Join Visit
            </Button>
          )}
          <Button size="sm" variant="outline" className="flex-1" onClick={onViewDetails}>
            View Details
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// Medication reminder card
interface MedicationReminderCardProps {
  reminder: {
    id: string;
    medicationName: string;
    dosage: string;
    scheduledTime: string;
    taken: boolean;
  };
  onTake: () => void;
  onSnooze: () => void;
}

function MedicationReminderCard({ reminder, onTake, onSnooze }: MedicationReminderCardProps) {
  if (reminder.taken) return null;

  return (
    <Card className="border-amber-200 bg-amber-50/50">
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-full bg-amber-100 flex items-center justify-center">
            <Pill className="h-5 w-5 text-amber-600" />
          </div>
          <div className="flex-1">
            <p className="font-medium">{reminder.medicationName}</p>
            <p className="text-sm text-muted-foreground">{reminder.dosage} • {reminder.scheduledTime}</p>
          </div>
        </div>
        <div className="flex gap-2 mt-3">
          <Button size="sm" className="flex-1" onClick={onTake}>
            Mark as Taken
          </Button>
          <Button size="sm" variant="outline" onClick={onSnooze}>
            Snooze
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// Health summary widget
interface HealthWidgetProps {
  data: Array<{
    type: string;
    value: number | string;
    unit: string;
    timestamp: string;
  }>;
  onViewAll: () => void;
}

function HealthWidget({ data, onViewAll }: HealthWidgetProps) {
  const getIcon = (type: string) => {
    switch (type) {
      case "heart_rate": return Heart;
      case "steps": return Activity;
      default: return Activity;
    }
  };

  const getColor = (type: string) => {
    switch (type) {
      case "heart_rate": return "text-red-500";
      case "steps": return "text-green-500";
      default: return "text-blue-500";
    }
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">Today's Health</CardTitle>
          <Button variant="ghost" size="sm" onClick={onViewAll}>
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="pb-4">
        <div className="grid grid-cols-2 gap-3">
          {data.slice(0, 4).map((item, i) => {
            const Icon = getIcon(item.type);
            return (
              <div key={i} className="p-3 bg-muted/50 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <Icon className={cn("h-4 w-4", getColor(item.type))} />
                  <span className="text-xs text-muted-foreground capitalize">
                    {item.type.replace("_", " ")}
                  </span>
                </div>
                <p className="text-lg font-semibold">
                  {item.value} <span className="text-xs font-normal text-muted-foreground">{item.unit}</span>
                </p>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

// Recent message preview
interface MessagePreviewProps {
  message: {
    id: string;
    from: string;
    preview: string;
    timestamp: string;
    unread: boolean;
  };
  onClick: () => void;
}

function MessagePreview({ message, onClick }: MessagePreviewProps) {
  return (
    <button
      onClick={onClick}
      className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-muted/50 transition-colors text-left"
    >
      <Avatar className="h-10 w-10">
        <AvatarFallback>{message.from.split(" ").map(n => n[0]).join("")}</AvatarFallback>
      </Avatar>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <span className={cn("font-medium text-sm", message.unread && "font-semibold")}>{message.from}</span>
          <span className="text-xs text-muted-foreground">{message.timestamp}</span>
        </div>
        <p className={cn("text-sm truncate", message.unread ? "text-foreground" : "text-muted-foreground")}>
          {message.preview}
        </p>
      </div>
      {message.unread && <div className="h-2 w-2 rounded-full bg-primary" />}
    </button>
  );
}

// Main Mobile Patient Home Component
export function MobilePatientHome() {
  const [isRefreshing, setIsRefreshing] = useState(false);

  const {
    notifications,
    unreadCount,
    medicationReminders,
    activeReminder,
    recentHealthData,
    fetchNotifications,
    fetchMedicationReminders,
    markMedicationTaken,
    snoozeMedicationReminder,
  } = useMobileStore();

  const {
    patientProfile,
    upcomingAppointments,
    fetchPatientProfile,
    fetchAppointments,
  } = usePatientPortalStore();

  useEffect(() => {
    fetchNotifications();
    fetchMedicationReminders();
    fetchPatientProfile();
    fetchAppointments();
  }, [fetchNotifications, fetchMedicationReminders, fetchPatientProfile, fetchAppointments]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await Promise.all([
      fetchNotifications(),
      fetchMedicationReminders(),
      fetchPatientProfile(),
      fetchAppointments(),
    ]);
    setIsRefreshing(false);
  };

  // Mock upcoming appointments for mobile display
  const nextAppointments = [
    {
      id: "apt1",
      date: format(new Date(), "yyyy-MM-dd"),
      time: "14:00",
      provider: "Dr. Priya Sharma",
      specialty: "Primary Care",
      type: "telehealth" as const,
    },
    {
      id: "apt2",
      date: format(new Date(Date.now() + 86400000 * 3), "yyyy-MM-dd"),
      time: "10:30",
      provider: "Dr. Raj Patel",
      specialty: "Cardiology",
      type: "in-person" as const,
      location: "Surya Medical Center, Room 204",
    },
  ];

  // Mock messages
  const recentMessages = [
    { id: "m1", from: "Dr. Sharma's Office", preview: "Your lab results are ready to review", timestamp: "2h ago", unread: true },
    { id: "m2", from: "Pharmacy", preview: "Your prescription is ready for pickup", timestamp: "Yesterday", unread: false },
  ];

  return (
    <div className="min-h-screen bg-background pb-20">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-background border-b">
        <div className="flex items-center justify-between p-4">
          <div>
            <p className="text-sm text-muted-foreground">Good {new Date().getHours() < 12 ? "morning" : new Date().getHours() < 17 ? "afternoon" : "evening"},</p>
            <h1 className="text-xl font-semibold">{patientProfile?.firstName || "Patient"}</h1>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" onClick={handleRefresh} disabled={isRefreshing}>
              <RefreshCw className={cn("h-5 w-5", isRefreshing && "animate-spin")} />
            </Button>
            <Button variant="ghost" size="icon" className="relative">
              <Bell className="h-5 w-5" />
              {unreadCount > 0 && (
                <span className="absolute top-1 right-1 h-4 w-4 rounded-full bg-red-500 text-white text-[10px] flex items-center justify-center">
                  {unreadCount > 9 ? "9+" : unreadCount}
                </span>
              )}
            </Button>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-6">
        {/* Quick Actions */}
        <ScrollArea className="w-full">
          <div className="flex gap-3 pb-2">
            <QuickAction icon={Calendar} label="Book" onClick={() => {}} />
            <QuickAction icon={Video} label="Telehealth" onClick={() => {}} variant="highlight" />
            <QuickAction icon={MessageSquare} label="Messages" onClick={() => {}} badge={1} />
            <QuickAction icon={Pill} label="Medications" onClick={() => {}} />
            <QuickAction icon={FileText} label="Records" onClick={() => {}} />
            <QuickAction icon={CreditCard} label="Pay Bill" onClick={() => {}} />
          </div>
          <ScrollBar orientation="horizontal" />
        </ScrollArea>

        {/* Active Medication Reminder */}
        {activeReminder && (
          <MedicationReminderCard
            reminder={activeReminder}
            onTake={() => markMedicationTaken(activeReminder.id)}
            onSnooze={() => snoozeMedicationReminder(activeReminder.id, 30)}
          />
        )}

        {/* Upcoming Appointments */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Upcoming Appointments</h2>
            <Button variant="ghost" size="sm">
              View All <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          </div>
          {nextAppointments.length === 0 ? (
            <Card>
              <CardContent className="py-6 text-center">
                <Calendar className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
                <p className="text-sm text-muted-foreground">No upcoming appointments</p>
                <Button size="sm" className="mt-3">
                  <Plus className="h-4 w-4 mr-1" /> Book Appointment
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {nextAppointments.map((apt) => (
                <AppointmentCardMobile
                  key={apt.id}
                  appointment={apt}
                  onJoin={() => {}}
                  onViewDetails={() => {}}
                />
              ))}
            </div>
          )}
        </div>

        {/* Health Data */}
        {recentHealthData.length > 0 && (
          <HealthWidget data={recentHealthData} onViewAll={() => {}} />
        )}

        {/* Recent Messages */}
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium">Messages</CardTitle>
              <Button variant="ghost" size="sm">
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {recentMessages.map((msg) => (
              <MessagePreview key={msg.id} message={msg} onClick={() => {}} />
            ))}
          </CardContent>
        </Card>

        {/* Medication Reminders Summary */}
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium">Today's Medications</CardTitle>
              <Button variant="ghost" size="sm">
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {medicationReminders.slice(0, 3).map((med) => (
                <div key={med.id} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={cn(
                      "h-8 w-8 rounded-full flex items-center justify-center",
                      med.taken ? "bg-green-100" : "bg-muted"
                    )}>
                      {med.taken ? (
                        <Activity className="h-4 w-4 text-green-600" />
                      ) : (
                        <Pill className="h-4 w-4 text-muted-foreground" />
                      )}
                    </div>
                    <div>
                      <p className="text-sm font-medium">{med.medicationName}</p>
                      <p className="text-xs text-muted-foreground">{med.scheduledTime}</p>
                    </div>
                  </div>
                  {med.taken ? (
                    <Badge variant="secondary" className="bg-green-100 text-green-700">Taken</Badge>
                  ) : (
                    <Button size="sm" variant="outline" onClick={() => markMedicationTaken(med.id)}>
                      Take
                    </Button>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Bottom Navigation (would be in layout) */}
      <div className="fixed bottom-0 left-0 right-0 bg-background border-t">
        <div className="flex items-center justify-around py-2">
          {[
            { icon: Activity, label: "Home", active: true },
            { icon: Calendar, label: "Appointments", active: false },
            { icon: FileText, label: "Records", active: false },
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

// Compact widget for embedding
export function PatientHomeWidget() {
  const { medicationReminders, activeReminder } = useMobileStore();

  return (
    <div className="space-y-3">
      {activeReminder && (
        <div className="p-3 bg-amber-50 rounded-lg border border-amber-200">
          <div className="flex items-center gap-2">
            <Pill className="h-4 w-4 text-amber-600" />
            <span className="text-sm font-medium">Medication Due</span>
          </div>
          <p className="text-sm mt-1">{activeReminder.medicationName}</p>
        </div>
      )}
      <div className="text-xs text-muted-foreground">
        {medicationReminders.filter(m => m.taken).length} of {medicationReminders.length} medications taken today
      </div>
    </div>
  );
}

export default MobilePatientHome;
