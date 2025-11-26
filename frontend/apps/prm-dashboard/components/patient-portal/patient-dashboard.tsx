"use client";

// Patient Portal Dashboard
// EPIC-UX-011: Patient Self-Service Portal - Journey 11.1

import React, { useEffect } from "react";
import { format, isPast, isToday } from "date-fns";
import {
  Home, Calendar, MessageSquare, Pill, CreditCard, FileText, User, Bell,
  MapPin, Clock, ChevronRight, Upload, Loader2, AlertCircle, LogOut,
  TestTube, Stethoscope,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  usePatientPortalStore,
  type Appointment,
  type Medication,
  type LabReport,
  type Bill,
} from "@/lib/store/patient-portal-store";

// Navigation tabs
interface NavTabsProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  unreadMessages: number;
  balanceDue: number;
}

export function PortalNavTabs({ activeTab, onTabChange, unreadMessages, balanceDue }: NavTabsProps) {
  const tabs = [
    { id: "home", label: "Home", icon: Home },
    { id: "appointments", label: "Appointments", icon: Calendar },
    { id: "messages", label: "Messages", icon: MessageSquare, badge: unreadMessages },
    { id: "medications", label: "Medications", icon: Pill },
    { id: "billing", label: "Billing", icon: CreditCard, badge: balanceDue > 0 ? "Due" : undefined },
  ];

  return (
    <nav className="flex items-center gap-1 bg-muted/30 p-1 rounded-lg">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          className={cn(
            "flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors",
            activeTab === tab.id ? "bg-background shadow text-primary" : "text-muted-foreground hover:text-foreground"
          )}
          onClick={() => onTabChange(tab.id)}
        >
          <tab.icon className="h-4 w-4" />
          {tab.label}
          {tab.badge && (
            <Badge variant="destructive" className="h-5 px-1.5 text-xs">
              {tab.badge}
            </Badge>
          )}
        </button>
      ))}
    </nav>
  );
}

// Upcoming appointment card
interface AppointmentCardProps {
  appointment: Appointment;
  onReschedule: () => void;
  onCancel: () => void;
  onDirections: () => void;
}

function UpcomingAppointmentCard({ appointment, onReschedule, onCancel, onDirections }: AppointmentCardProps) {
  const appointmentDate = new Date(`${appointment.date}T${appointment.time}`);
  const isUpcoming = !isPast(appointmentDate);

  return (
    <Card className={cn(!isUpcoming && "opacity-60")}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-primary" />
              <span className="font-medium">
                {format(appointmentDate, "MMMM d, yyyy")} • {format(appointmentDate, "h:mm a")}
              </span>
              {isToday(appointmentDate) && <Badge variant="default">Today</Badge>}
            </div>
            <div>
              <p className="font-semibold">{appointment.provider.name}</p>
              <p className="text-sm text-muted-foreground">{appointment.visitType}</p>
            </div>
            <div className="flex items-center gap-1 text-sm text-muted-foreground">
              <MapPin className="h-3 w-3" />
              {appointment.location.name}
            </div>
          </div>
          {appointment.telehealth && (
            <Badge variant="secondary" className="bg-blue-100 text-blue-700">
              <Stethoscope className="h-3 w-3 mr-1" />Telehealth
            </Badge>
          )}
        </div>
        {isUpcoming && (
          <div className="flex gap-2 mt-4">
            <Button variant="outline" size="sm" onClick={onDirections}>
              <MapPin className="h-4 w-4 mr-1" />Directions
            </Button>
            <Button variant="outline" size="sm" onClick={onReschedule}>
              <Calendar className="h-4 w-4 mr-1" />Reschedule
            </Button>
            <Button variant="ghost" size="sm" className="text-destructive" onClick={onCancel}>
              Cancel
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Medications widget
interface MedicationsWidgetProps {
  medications: Medication[];
  onRequestRefill: (medicationId: string) => void;
  onViewAll: () => void;
}

function MedicationsWidget({ medications, onRequestRefill, onViewAll }: MedicationsWidgetProps) {
  const activeMeds = medications.filter((m) => m.status === "active").slice(0, 3);

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <Pill className="h-4 w-4" />MEDICATIONS
          </CardTitle>
          <Badge variant="secondary">{medications.filter((m) => m.status === "active").length} Active</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {activeMeds.map((med) => (
          <div key={med.id} className="space-y-1">
            <p className="text-sm font-medium">{med.name}</p>
            <p className="text-xs text-muted-foreground">{med.instructions}</p>
            {med.refillsRemaining === 0 && (
              <p className="text-xs text-amber-600 flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />No refills remaining
              </p>
            )}
          </div>
        ))}
        <Button variant="outline" size="sm" className="w-full" onClick={onViewAll}>
          Request Refill <ChevronRight className="h-4 w-4 ml-1" />
        </Button>
      </CardContent>
    </Card>
  );
}

// Recent results widget
interface ResultsWidgetProps {
  labs: LabReport[];
  onViewDetails: (labId: string) => void;
}

function RecentResultsWidget({ labs, onViewDetails }: ResultsWidgetProps) {
  const recentLab = labs[0];

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <TestTube className="h-4 w-4" />RECENT RESULTS
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {recentLab && (
          <>
            <div className="flex items-center justify-between">
              <span className="text-sm">{format(new Date(recentLab.date), "MMM d")} - Lab Results</span>
            </div>
            {recentLab.results.slice(0, 2).map((result) => (
              <div key={result.id} className="flex items-center justify-between text-sm">
                <span>{result.testName}</span>
                <div className="flex items-center gap-2">
                  <span className="font-medium">{result.result}{result.unit === "%" ? "%" : ` ${result.unit}`}</span>
                  {result.status === "normal" ? (
                    <div className="h-2 w-2 rounded-full bg-green-500" />
                  ) : (
                    <div className="h-2 w-2 rounded-full bg-amber-500" />
                  )}
                </div>
              </div>
            ))}
            <Button variant="ghost" size="sm" className="w-full" onClick={() => onViewDetails(recentLab.id)}>
              View Details <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          </>
        )}
      </CardContent>
    </Card>
  );
}

// Quick actions
interface QuickActionsProps {
  onBookAppointment: () => void;
  onMessageDoctor: () => void;
  onPayBill: () => void;
  onUploadDocument: () => void;
}

function QuickActions({ onBookAppointment, onMessageDoctor, onPayBill, onUploadDocument }: QuickActionsProps) {
  const actions = [
    { label: "Book Appointment", icon: Calendar, onClick: onBookAppointment },
    { label: "Message Doctor", icon: MessageSquare, onClick: onMessageDoctor },
    { label: "Pay Bill", icon: CreditCard, onClick: onPayBill },
    { label: "Upload Document", icon: Upload, onClick: onUploadDocument },
  ];

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">QUICK ACTIONS</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-4 gap-2">
          {actions.map((action) => (
            <Button
              key={action.label}
              variant="outline"
              className="flex flex-col h-auto py-4 gap-2"
              onClick={action.onClick}
            >
              <action.icon className="h-5 w-5" />
              <span className="text-xs">{action.label}</span>
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// Balance due card
interface BalanceDueCardProps {
  balance: number;
  onPayNow: () => void;
}

function BalanceDueCard({ balance, onPayNow }: BalanceDueCardProps) {
  if (balance <= 0) return null;

  return (
    <Card className="border-amber-200 bg-amber-50/50">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-amber-100 flex items-center justify-center">
              <CreditCard className="h-5 w-5 text-amber-600" />
            </div>
            <div>
              <p className="text-sm text-amber-800">Balance Due</p>
              <p className="text-xl font-bold text-amber-900">₹{balance.toLocaleString()}</p>
            </div>
          </div>
          <Button onClick={onPayNow}>Pay Now</Button>
        </div>
      </CardContent>
    </Card>
  );
}

// Main Patient Dashboard
export function PatientDashboard() {
  const {
    patient,
    healthSummary,
    medications,
    appointments,
    messageThreads,
    bills,
    totalBalance,
    isLoadingProfile,
    fetchProfile,
    fetchHealthSummary,
    fetchMedications,
    fetchAppointments,
    fetchMessageThreads,
    fetchBills,
  } = usePatientPortalStore();

  useEffect(() => {
    fetchProfile();
    fetchHealthSummary();
    fetchMedications();
    fetchAppointments();
    fetchMessageThreads();
    fetchBills();
  }, [fetchProfile, fetchHealthSummary, fetchMedications, fetchAppointments, fetchMessageThreads, fetchBills]);

  const unreadMessages = messageThreads.reduce((sum, t) => sum + t.unreadCount, 0);
  const upcomingAppointments = appointments.filter((a) => a.status !== "cancelled" && !isPast(new Date(`${a.date}T${a.time}`)));

  if (isLoadingProfile || !patient) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Avatar className="h-12 w-12">
            <AvatarFallback className="text-lg bg-primary/10">
              {patient.firstName[0]}{patient.lastName[0]}
            </AvatarFallback>
          </Avatar>
          <div>
            <h1 className="text-2xl font-semibold">Welcome, {patient.firstName}!</h1>
            <p className="text-sm text-muted-foreground">MRN: {patient.mrn}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon">
            <Bell className="h-5 w-5" />
          </Button>
          <Button variant="ghost" size="icon">
            <User className="h-5 w-5" />
          </Button>
          <Button variant="ghost" size="sm">
            <LogOut className="h-4 w-4 mr-2" />Logout
          </Button>
        </div>
      </div>

      {/* Balance Due Alert */}
      <BalanceDueCard balance={totalBalance} onPayNow={() => {}} />

      {/* Upcoming Appointments */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm flex items-center gap-2">
              <Calendar className="h-4 w-4" />UPCOMING APPOINTMENTS
            </CardTitle>
            <Button variant="ghost" size="sm">View All <ChevronRight className="h-4 w-4 ml-1" /></Button>
          </div>
        </CardHeader>
        <CardContent>
          {upcomingAppointments.length === 0 ? (
            <div className="text-center py-6 text-muted-foreground">
              <Calendar className="h-8 w-8 mx-auto mb-2 opacity-30" />
              <p>No upcoming appointments</p>
              <Button variant="link" size="sm">Book an appointment</Button>
            </div>
          ) : (
            <div className="space-y-3">
              {upcomingAppointments.slice(0, 2).map((apt) => (
                <UpcomingAppointmentCard
                  key={apt.id}
                  appointment={apt}
                  onReschedule={() => {}}
                  onCancel={() => {}}
                  onDirections={() => {}}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Widgets Grid */}
      <div className="grid grid-cols-2 gap-6">
        <MedicationsWidget
          medications={medications}
          onRequestRefill={() => {}}
          onViewAll={() => {}}
        />
        {healthSummary && (
          <RecentResultsWidget
            labs={healthSummary.recentLabs}
            onViewDetails={() => {}}
          />
        )}
      </div>

      {/* Quick Actions */}
      <QuickActions
        onBookAppointment={() => {}}
        onMessageDoctor={() => {}}
        onPayBill={() => {}}
        onUploadDocument={() => {}}
      />
    </div>
  );
}

// Dashboard skeleton
export function PatientDashboardSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="flex items-center gap-4">
        <div className="h-12 w-12 rounded-full bg-muted" />
        <div className="space-y-2">
          <div className="h-6 w-48 bg-muted rounded" />
          <div className="h-4 w-32 bg-muted rounded" />
        </div>
      </div>
      <div className="h-24 bg-muted rounded-lg" />
      <div className="h-48 bg-muted rounded-lg" />
      <div className="grid grid-cols-2 gap-6">
        <div className="h-40 bg-muted rounded-lg" />
        <div className="h-40 bg-muted rounded-lg" />
      </div>
    </div>
  );
}

export default PatientDashboard;
