"use client";

import * as React from "react";
import { use, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Edit,
  MoreHorizontal,
  Calendar,
  MessageSquare,
  Phone,
  Mail,
  User,
  Activity,
  Ticket,
  Send,
  Trash2,
} from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { patientsAPI } from "@/lib/api/patients";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { MagicCard } from "@/components/ui/magic-card";
import { formatDate } from "@/lib/utils/date";
import type { Patient360Response } from "@/lib/api/types";
import toast from "react-hot-toast";

// ============================================================================
// Helper Functions
// ============================================================================

function getInitials(firstName?: string, lastName?: string): string {
  const first = firstName?.[0] || "";
  const last = lastName?.[0] || "";
  return (first + last).toUpperCase() || "?";
}

function calculateAge(dob: string): number {
  const birthDate = new Date(dob);
  const today = new Date();
  let age = today.getFullYear() - birthDate.getFullYear();
  const m = today.getMonth() - birthDate.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
    age--;
  }
  return age;
}

function getStatusColor(status: string): string {
  switch (status?.toLowerCase()) {
    case "scheduled":
    case "active":
    case "open":
      return "bg-blue-50 text-blue-700 border-blue-200";
    case "confirmed":
      return "bg-green-50 text-green-700 border-green-200";
    case "completed":
    case "resolved":
      return "bg-gray-50 text-gray-700 border-gray-200";
    case "cancelled":
    case "closed":
      return "bg-red-50 text-red-700 border-red-200";
    case "in_progress":
      return "bg-amber-50 text-amber-700 border-amber-200";
    default:
      return "bg-gray-50 text-gray-600 border-gray-200";
  }
}

function getPriorityColor(priority: string): string {
  switch (priority?.toLowerCase()) {
    case "urgent":
      return "bg-red-100 text-red-700";
    case "high":
      return "bg-orange-100 text-orange-700";
    case "medium":
      return "bg-yellow-100 text-yellow-700";
    case "low":
      return "bg-green-100 text-green-700";
    default:
      return "bg-gray-100 text-gray-700";
  }
}

// ============================================================================
// Main Page Component
// ============================================================================

export default function PatientDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("overview");
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [editForm, setEditForm] = useState({
    first_name: "",
    last_name: "",
    phone_primary: "",
    email_primary: "",
  });

  // Fetch patient 360 data from real API
  const { data: patient360, isLoading, error } = useQuery({
    queryKey: ["patient-360", id],
    queryFn: async () => {
      const [data, err] = await patientsAPI.get360View(id);
      if (err) throw new Error(err.message);
      return data;
    },
  });

  // Update patient mutation
  const updateMutation = useMutation({
    mutationFn: (data: typeof editForm) => patientsAPI.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["patient-360", id] });
      queryClient.invalidateQueries({ queryKey: ["patients"] });
      setIsEditOpen(false);
      toast.success("Patient updated successfully");
    },
    onError: (error: any) => {
      toast.error("Failed to update patient: " + error.message);
    },
  });

  // Delete patient mutation
  const deleteMutation = useMutation({
    mutationFn: () => patientsAPI.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["patients"] });
      toast.success("Patient deactivated successfully");
      router.push("/dashboard/patients");
    },
    onError: (error: any) => {
      toast.error("Failed to deactivate patient: " + error.message);
    },
  });

  // Activate patient mutation (for reactivating inactive patients)
  const activateMutation = useMutation({
    mutationFn: () => patientsAPI.activate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["patient-360", id] });
      queryClient.invalidateQueries({ queryKey: ["patients"] });
      queryClient.invalidateQueries({ queryKey: ["patient-stats"] });
      toast.success("Patient reactivated successfully");
    },
    onError: (error: any) => {
      toast.error("Failed to reactivate patient: " + error.message);
    },
  });

  // Open edit modal with current data
  const handleEditClick = () => {
    if (patient360?.patient) {
      setEditForm({
        first_name: patient360.patient.first_name || "",
        last_name: patient360.patient.last_name || "",
        phone_primary: patient360.patient.phone_primary || "",
        email_primary: patient360.patient.email_primary || "",
      });
      setIsEditOpen(true);
    }
  };

  // Handle form submit
  const handleEditSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate(editForm);
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-gray-500">Loading patient profile...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !patient360) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 mb-4">
          {error?.message || "Patient not found"}
        </p>
        <Link href="/dashboard/patients">
          <Button>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Patients
          </Button>
        </Link>
      </div>
    );
  }

  const { patient } = patient360;
  const fullName = patient.legal_name || `${patient.first_name} ${patient.last_name}`;
  const age = calculateAge(patient.date_of_birth);

  return (
    <div className="space-y-6 pb-8">
      {/* Top navigation */}
      <div className="flex items-center justify-between">
        <Link href="/dashboard/patients">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Patients
          </Button>
        </Link>

        <div className="flex items-center gap-2">
          {/* Show Reactivate button for inactive patients */}
          {patient360?.patient?.state === 'inactive' && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => activateMutation.mutate()}
              disabled={activateMutation.isPending}
              className="text-green-600 border-green-200 hover:bg-green-50"
            >
              {activateMutation.isPending ? (
                <>
                  <span className="w-3 h-3 border-2 border-green-600/30 border-t-green-600 rounded-full animate-spin mr-2" />
                  Reactivating...
                </>
              ) : (
                <>
                  <Activity className="h-4 w-4 mr-2" />
                  Reactivate
                </>
              )}
            </Button>
          )}
          <Button variant="outline" size="sm" onClick={handleEditClick}>
            <Edit className="h-4 w-4 mr-2" />
            Edit
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem>Print Summary</DropdownMenuItem>
              <DropdownMenuItem>Export Record</DropdownMenuItem>
              {patient360?.patient?.state !== 'inactive' && (
                <>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    className="text-red-600"
                    onClick={() => setIsDeleteOpen(true)}
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Deactivate Patient
                  </DropdownMenuItem>
                </>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Patient Header */}
      <Card className="border-gray-200">
        <CardContent className="p-6">
          <div className="flex flex-col lg:flex-row gap-6">
            {/* Patient Info */}
            <div className="flex items-start gap-4 flex-1">
              <Avatar className="h-16 w-16 border-2 border-gray-200">
                <AvatarFallback className="text-lg font-semibold bg-blue-50 text-blue-600">
                  {getInitials(patient.first_name, patient.last_name)}
                </AvatarFallback>
              </Avatar>

              <div className="flex-1">
                <h1 className="text-2xl font-bold text-gray-900">{fullName}</h1>
                <p className="text-gray-500">
                  {formatDate(patient.date_of_birth, "MMM d, yyyy")} ({age} years) • {patient.gender}
                </p>
                <p className="text-sm text-gray-500">
                  MRN: {patient.mrn || "N/A"}
                </p>

                {/* Contact Info */}
                <div className="flex flex-wrap items-center gap-4 mt-3">
                  {patient.phone_primary && (
                    <div className="flex items-center gap-1.5 text-sm">
                      <Phone className="h-4 w-4 text-gray-400" />
                      <span>{patient.phone_primary}</span>
                    </div>
                  )}
                  {patient.email_primary && (
                    <div className="flex items-center gap-1.5 text-sm">
                      <Mail className="h-4 w-4 text-gray-400" />
                      <span>{patient.email_primary}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Quick Info */}
            <div className="flex flex-wrap gap-3 lg:flex-col lg:w-60">
              {patient360.next_appointment_date && (
                <div className="flex items-start gap-3 p-3 rounded-lg bg-blue-50/50 border border-blue-100">
                  <Calendar className="h-4 w-4 text-blue-600 mt-0.5" />
                  <div className="text-sm">
                    <p className="text-gray-500">Next Appointment</p>
                    <p className="font-medium text-blue-700">
                      {formatDate(patient360.next_appointment_date, "MMM d, yyyy 'at' h:mm a")}
                    </p>
                  </div>
                </div>
              )}
              {patient360.last_visit_date && (
                <div className="flex items-start gap-3 p-3 rounded-lg bg-gray-50 border border-gray-100">
                  <Calendar className="h-4 w-4 text-gray-500 mt-0.5" />
                  <div className="text-sm">
                    <p className="text-gray-500">Last Visit</p>
                    <p className="font-medium">
                      {formatDate(patient360.last_visit_date, "MMM d, yyyy")}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MagicCard className="bg-white border border-gray-200" gradientColor="#eff6ff">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium text-gray-500">Appointments</CardTitle>
            <Calendar className="w-4 h-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{patient360.total_appointments}</div>
            <p className="text-xs text-blue-600 mt-1">{patient360.upcoming_appointments} upcoming</p>
          </CardContent>
        </MagicCard>

        <MagicCard className="bg-white border border-gray-200" gradientColor="#f0fdf4">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium text-gray-500">Active Journeys</CardTitle>
            <Activity className="w-4 h-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{patient360.active_journeys}</div>
            <p className="text-xs text-gray-500 mt-1">Care pathways</p>
          </CardContent>
        </MagicCard>

        <MagicCard className="bg-white border border-gray-200" gradientColor="#fef3c7">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium text-gray-500">Open Tickets</CardTitle>
            <Ticket className="w-4 h-4 text-amber-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{patient360.open_tickets}</div>
            <p className="text-xs text-gray-500 mt-1">Support requests</p>
          </CardContent>
        </MagicCard>

        <MagicCard className="bg-white border border-gray-200" gradientColor="#fae8ff">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium text-gray-500">Communications</CardTitle>
            <MessageSquare className="w-4 h-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{patient360.recent_communications}</div>
            <p className="text-xs text-gray-500 mt-1">Messages</p>
          </CardContent>
        </MagicCard>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="appointments">Appointments</TabsTrigger>
          <TabsTrigger value="communications">Communications</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6 mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Recent Appointments */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-blue-600" />
                  Recent Appointments
                </CardTitle>
              </CardHeader>
              <CardContent>
                {patient360.appointments.length === 0 ? (
                  <p className="text-sm text-gray-500 text-center py-4">No appointments yet</p>
                ) : (
                  <div className="space-y-3">
                    {patient360.appointments.slice(0, 5).map((apt) => (
                      <div key={apt.id} className="flex items-center justify-between p-3 rounded-lg bg-gray-50 border border-gray-100">
                        <div>
                          <p className="text-sm font-medium">{apt.appointment_type || "Appointment"}</p>
                          <p className="text-xs text-gray-500">
                            {apt.scheduled_at ? formatDate(apt.scheduled_at, "MMM d, yyyy 'at' h:mm a") : "Not scheduled"}
                          </p>
                        </div>
                        <Badge className={getStatusColor(apt.status)}>{apt.status}</Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Open Tickets */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <Ticket className="h-4 w-4 text-amber-600" />
                  Open Tickets
                </CardTitle>
              </CardHeader>
              <CardContent>
                {patient360.tickets.length === 0 ? (
                  <p className="text-sm text-gray-500 text-center py-4">No tickets</p>
                ) : (
                  <div className="space-y-3">
                    {patient360.tickets.slice(0, 5).map((ticket) => (
                      <div key={ticket.id} className="flex items-center justify-between p-3 rounded-lg bg-gray-50 border border-gray-100">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{ticket.title}</p>
                          <Badge className={`${getPriorityColor(ticket.priority)} text-xs mt-1`}>
                            {ticket.priority}
                          </Badge>
                        </div>
                        <Badge className={getStatusColor(ticket.status)}>{ticket.status}</Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Active Journeys */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <Activity className="h-4 w-4 text-green-600" />
                  Active Journeys
                </CardTitle>
              </CardHeader>
              <CardContent>
                {patient360.journeys.length === 0 ? (
                  <p className="text-sm text-gray-500 text-center py-4">No active journeys</p>
                ) : (
                  <div className="space-y-3">
                    {patient360.journeys.slice(0, 5).map((journey) => (
                      <div key={journey.id} className="flex items-center justify-between p-3 rounded-lg bg-gray-50 border border-gray-100">
                        <div>
                          <p className="text-sm font-medium">Journey #{journey.journey_id.slice(0, 8)}</p>
                          <p className="text-xs text-gray-500">
                            Stage: {journey.current_stage_id?.slice(0, 8) || "Initial"}
                          </p>
                        </div>
                        <Badge className={getStatusColor(journey.status)}>{journey.status}</Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Recent Communications */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <MessageSquare className="h-4 w-4 text-purple-600" />
                  Recent Communications
                </CardTitle>
              </CardHeader>
              <CardContent>
                {patient360.communications.length === 0 ? (
                  <p className="text-sm text-gray-500 text-center py-4">No communications yet</p>
                ) : (
                  <div className="space-y-3">
                    {patient360.communications.slice(0, 5).map((comm) => (
                      <div key={comm.id} className="flex items-center justify-between p-3 rounded-lg bg-gray-50 border border-gray-100">
                        <div className="flex items-center gap-3">
                          <div className={`p-2 rounded-lg ${comm.direction === "outbound" ? "bg-blue-100" : "bg-green-100"}`}>
                            <Send className={`h-3 w-3 ${comm.direction === "outbound" ? "text-blue-600" : "text-green-600 rotate-180"}`} />
                          </div>
                          <div>
                            <p className="text-sm font-medium capitalize">{comm.channel}</p>
                            <p className="text-xs text-gray-500">
                              {comm.sent_at ? formatDate(comm.sent_at, "MMM d, h:mm a") : "Pending"}
                            </p>
                          </div>
                        </div>
                        <Badge variant="outline" className="text-xs capitalize">
                          {comm.direction}
                        </Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Appointments Tab */}
        <TabsContent value="appointments" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">All Appointments</CardTitle>
            </CardHeader>
            <CardContent>
              {patient360.appointments.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-8">No appointments found</p>
              ) : (
                <div className="space-y-3">
                  {patient360.appointments.map((apt) => (
                    <div key={apt.id} className="flex items-center justify-between p-4 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors">
                      <div className="flex items-center gap-4">
                        <div className="p-3 rounded-lg bg-blue-50">
                          <Calendar className="h-5 w-5 text-blue-600" />
                        </div>
                        <div>
                          <p className="font-medium">{apt.appointment_type || "Appointment"}</p>
                          <p className="text-sm text-gray-500">
                            {apt.scheduled_at ? formatDate(apt.scheduled_at, "EEEE, MMM d, yyyy 'at' h:mm a") : "Not scheduled"}
                          </p>
                        </div>
                      </div>
                      <Badge className={getStatusColor(apt.status)}>{apt.status}</Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Communications Tab */}
        <TabsContent value="communications" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">All Communications</CardTitle>
            </CardHeader>
            <CardContent>
              {patient360.communications.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-8">No communications found</p>
              ) : (
                <div className="space-y-3">
                  {patient360.communications.map((comm) => (
                    <div key={comm.id} className="flex items-center justify-between p-4 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors">
                      <div className="flex items-center gap-4">
                        <div className={`p-3 rounded-lg ${comm.direction === "outbound" ? "bg-blue-50" : "bg-green-50"}`}>
                          <Send className={`h-5 w-5 ${comm.direction === "outbound" ? "text-blue-600" : "text-green-600 rotate-180"}`} />
                        </div>
                        <div>
                          <p className="font-medium capitalize">{comm.channel} - {comm.message_type || "Message"}</p>
                          <p className="text-sm text-gray-500">
                            {comm.sent_at ? formatDate(comm.sent_at, "EEEE, MMM d, yyyy 'at' h:mm a") : "Pending"}
                          </p>
                        </div>
                      </div>
                      <Badge variant="outline" className="capitalize">{comm.direction}</Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Edit Patient Dialog */}
      <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
        <DialogContent className="sm:max-w-[480px] p-0 overflow-hidden rounded-2xl border-gray-200">
          {/* Header with gradient */}
          <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-5 text-white">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white/20 rounded-xl">
                <Edit className="h-5 w-5" />
              </div>
              <div>
                <DialogTitle className="text-lg font-semibold text-white">Edit Patient</DialogTitle>
                <DialogDescription className="text-blue-100 text-sm mt-0.5">
                  Update patient information
                </DialogDescription>
              </div>
            </div>
          </div>

          <form onSubmit={handleEditSubmit} className="px-6 py-5">
            <div className="space-y-5">
              {/* Name Row */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="first_name" className="text-sm font-medium text-gray-700 flex items-center gap-2">
                    <User className="h-3.5 w-3.5 text-gray-400" />
                    First Name
                  </Label>
                  <Input
                    id="first_name"
                    value={editForm.first_name}
                    onChange={(e) => setEditForm({ ...editForm, first_name: e.target.value })}
                    className="h-11 rounded-xl border-gray-200 focus:border-blue-300 focus:ring-blue-100 bg-gray-50/50"
                    placeholder="John"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="last_name" className="text-sm font-medium text-gray-700 flex items-center gap-2">
                    <User className="h-3.5 w-3.5 text-gray-400" />
                    Last Name
                  </Label>
                  <Input
                    id="last_name"
                    value={editForm.last_name}
                    onChange={(e) => setEditForm({ ...editForm, last_name: e.target.value })}
                    className="h-11 rounded-xl border-gray-200 focus:border-blue-300 focus:ring-blue-100 bg-gray-50/50"
                    placeholder="Doe"
                  />
                </div>
              </div>

              {/* Phone */}
              <div className="space-y-2">
                <Label htmlFor="phone" className="text-sm font-medium text-gray-700 flex items-center gap-2">
                  <Phone className="h-3.5 w-3.5 text-gray-400" />
                  Phone Number
                </Label>
                <Input
                  id="phone"
                  value={editForm.phone_primary}
                  onChange={(e) => setEditForm({ ...editForm, phone_primary: e.target.value })}
                  className="h-11 rounded-xl border-gray-200 focus:border-blue-300 focus:ring-blue-100 bg-gray-50/50"
                  placeholder="+1 (555) 123-4567"
                />
              </div>

              {/* Email */}
              <div className="space-y-2">
                <Label htmlFor="email" className="text-sm font-medium text-gray-700 flex items-center gap-2">
                  <Mail className="h-3.5 w-3.5 text-gray-400" />
                  Email Address
                </Label>
                <Input
                  id="email"
                  type="email"
                  value={editForm.email_primary}
                  onChange={(e) => setEditForm({ ...editForm, email_primary: e.target.value })}
                  className="h-11 rounded-xl border-gray-200 focus:border-blue-300 focus:ring-blue-100 bg-gray-50/50"
                  placeholder="john.doe@email.com"
                />
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end gap-3 mt-6 pt-5 border-t border-gray-100">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsEditOpen(false)}
                className="rounded-full px-5 border-gray-200 hover:bg-gray-50"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={updateMutation.isPending}
                className="rounded-full px-6 bg-blue-600 hover:bg-blue-700 text-white shadow-sm hover:shadow-md transition-all"
              >
                {updateMutation.isPending ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                    Saving...
                  </>
                ) : (
                  "Save Changes"
                )}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Deactivate Patient Alert Dialog */}
      <AlertDialog open={isDeleteOpen} onOpenChange={setIsDeleteOpen}>
        <AlertDialogContent className="sm:max-w-[440px] p-0 overflow-hidden rounded-2xl border-gray-200">
          {/* Warning Header */}
          <div className="bg-gradient-to-r from-red-500 to-rose-500 px-6 py-5 text-white">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white/20 rounded-xl">
                <Trash2 className="h-5 w-5" />
              </div>
              <div>
                <AlertDialogTitle className="text-lg font-semibold text-white">
                  Deactivate Patient
                </AlertDialogTitle>
                <p className="text-red-100 text-sm mt-0.5">This action affects patient visibility</p>
              </div>
            </div>
          </div>

          <div className="px-6 py-5">
            <AlertDialogDescription className="text-gray-600 leading-relaxed">
              You are about to deactivate the record for <span className="font-semibold text-gray-900">{fullName}</span>.
            </AlertDialogDescription>

            <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-xl">
              <div className="flex items-start gap-3">
                <div className="p-1.5 bg-amber-100 rounded-lg">
                  <Activity className="h-4 w-4 text-amber-600" />
                </div>
                <div className="text-sm">
                  <p className="font-medium text-amber-800">What happens next?</p>
                  <ul className="mt-1.5 text-amber-700 space-y-1">
                    <li>• Patient won't appear in active lists</li>
                    <li>• Data is retained for compliance</li>
                    <li>• You can reactivate anytime</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 px-6 py-4 bg-gray-50 border-t border-gray-100">
            <AlertDialogCancel className="rounded-full px-5 border-gray-200 hover:bg-white">
              Keep Active
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteMutation.mutate()}
              className="rounded-full px-6 bg-red-600 hover:bg-red-700 text-white shadow-sm hover:shadow-md transition-all"
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                  Deactivating...
                </>
              ) : (
                "Deactivate Patient"
              )}
            </AlertDialogAction>
          </div>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
