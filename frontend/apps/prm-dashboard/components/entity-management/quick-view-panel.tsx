"use client";

import * as React from "react";
import {
  X,
  Phone,
  Mail,
  MapPin,
  Calendar,
  AlertCircle,
  Pill,
  Activity,
  ExternalLink,
  MessageSquare,
  User,
  Stethoscope,
  Building,
  Clock,
  Star,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { StatusBadge } from "./entity-list";
import type { Practitioner, Location } from "@/lib/store/organization-store";
import type { Patient } from "@/lib/store/patient-profile-store";
import { format } from "date-fns";

// ============================================================================
// Types
// ============================================================================

interface QuickViewPanelProps {
  isOpen: boolean;
  onClose: () => void;
  entityType: "patient" | "practitioner" | "location";
  entityId: string;
  entity?: Patient | Practitioner | Location | null;
  onNavigate?: () => void;
  onAction?: (action: string) => void;
  className?: string;
}

// ============================================================================
// Patient Quick View
// ============================================================================

interface PatientQuickViewProps {
  patient: Patient;
  onNavigate?: () => void;
  onAction?: (action: string) => void;
}

function PatientQuickView({ patient, onNavigate, onAction }: PatientQuickViewProps) {
  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-start gap-3">
        <Avatar className="h-14 w-14">
          <AvatarImage src={patient.photo} />
          <AvatarFallback className="text-lg">
            {patient.firstName?.[0]}
            {patient.lastName?.[0]}
          </AvatarFallback>
        </Avatar>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-lg">{patient.name}</h3>
          <p className="text-sm text-muted-foreground">
            {patient.gender}, {patient.age} years
          </p>
          <p className="text-xs text-muted-foreground mt-0.5">
            MRN: <code className="bg-muted px-1 rounded">{patient.mrn}</code>
          </p>
        </div>
      </div>

      <Separator />

      {/* Contact Info */}
      <div className="space-y-2">
        {patient.phone && (
          <div className="flex items-center gap-2 text-sm">
            <Phone className="h-4 w-4 text-muted-foreground" />
            <span>{patient.phone}</span>
          </div>
        )}
        {patient.email && (
          <div className="flex items-center gap-2 text-sm">
            <Mail className="h-4 w-4 text-muted-foreground" />
            <span className="truncate">{patient.email}</span>
          </div>
        )}
        {patient.address && (
          <div className="flex items-center gap-2 text-sm">
            <MapPin className="h-4 w-4 text-muted-foreground" />
            <span>{patient.address.city}, {patient.address.state}</span>
          </div>
        )}
      </div>

      <Separator />

      {/* Alerts placeholder */}
      <div className="space-y-2">
        <h4 className="text-sm font-medium flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-warning" />
          Allergies
        </h4>
        <div className="p-2 bg-warning/10 rounded border border-warning/20">
          <p className="text-sm text-warning">Penicillin (Severe)</p>
        </div>
      </div>

      {/* Medications placeholder */}
      <div className="space-y-2">
        <h4 className="text-sm font-medium flex items-center gap-2">
          <Pill className="h-4 w-4 text-primary" />
          Active Medications
        </h4>
        <ul className="text-sm space-y-1 text-muted-foreground">
          <li>• Metformin 1000mg BID</li>
          <li>• Lisinopril 10mg daily</li>
        </ul>
      </div>

      {/* Conditions placeholder */}
      <div className="space-y-2">
        <h4 className="text-sm font-medium flex items-center gap-2">
          <Activity className="h-4 w-4 text-primary" />
          Conditions
        </h4>
        <div className="flex flex-wrap gap-1">
          <Badge variant="outline">Type 2 Diabetes</Badge>
          <Badge variant="outline">Hypertension</Badge>
        </div>
      </div>

      <Separator />

      {/* Next Appointment */}
      {patient.nextAppointment && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium flex items-center gap-2">
            <Calendar className="h-4 w-4 text-primary" />
            Next Appointment
          </h4>
          <div className="p-2 bg-primary/5 rounded border border-primary/10">
            <p className="text-sm font-medium">
              {format(new Date(patient.nextAppointment.dateTime), "EEEE, MMM d 'at' h:mm a")}
            </p>
            <p className="text-xs text-muted-foreground mt-0.5">
              {patient.nextAppointment.provider} • {patient.nextAppointment.type}
            </p>
          </div>
        </div>
      )}

      <Separator />

      {/* Actions */}
      <div className="grid grid-cols-2 gap-2">
        <Button variant="outline" size="sm" onClick={() => onAction?.("profile")}>
          <User className="h-4 w-4 mr-2" />
          Full Profile
        </Button>
        <Button variant="outline" size="sm" onClick={() => onAction?.("book")}>
          <Calendar className="h-4 w-4 mr-2" />
          Book Appt
        </Button>
        <Button variant="outline" size="sm" onClick={() => onAction?.("message")}>
          <MessageSquare className="h-4 w-4 mr-2" />
          Message
        </Button>
        <Button variant="outline" size="sm" onClick={() => onAction?.("call")}>
          <Phone className="h-4 w-4 mr-2" />
          Call
        </Button>
      </div>
    </div>
  );
}

// ============================================================================
// Practitioner Quick View
// ============================================================================

interface PractitionerQuickViewProps {
  practitioner: Practitioner;
  onNavigate?: () => void;
  onAction?: (action: string) => void;
}

function PractitionerQuickView({ practitioner, onNavigate, onAction }: PractitionerQuickViewProps) {
  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-start gap-3">
        <Avatar className="h-14 w-14">
          <AvatarImage src={practitioner.photo} />
          <AvatarFallback className="text-lg bg-primary/10 text-primary">
            {practitioner.firstName?.[0]}
            {practitioner.lastName?.[0]}
          </AvatarFallback>
        </Avatar>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-lg">{practitioner.name}</h3>
          <p className="text-sm text-muted-foreground">
            {practitioner.qualifications.join(", ")}
          </p>
          <div className="flex items-center gap-2 mt-1">
            <StatusBadge status={practitioner.status} />
            {practitioner.rating && (
              <span className="text-sm flex items-center gap-1">
                <Star className="h-3 w-3 fill-warning text-warning" />
                {practitioner.rating}
              </span>
            )}
          </div>
        </div>
      </div>

      <Separator />

      {/* Specialties */}
      <div className="space-y-2">
        <h4 className="text-sm font-medium flex items-center gap-2">
          <Stethoscope className="h-4 w-4 text-primary" />
          Specialties
        </h4>
        <div className="flex flex-wrap gap-1">
          {practitioner.specialties.map((specialty) => (
            <Badge key={specialty} variant="secondary">
              {specialty}
            </Badge>
          ))}
        </div>
      </div>

      {/* Contact Info */}
      <div className="space-y-2">
        {practitioner.contact?.phone && (
          <div className="flex items-center gap-2 text-sm">
            <Phone className="h-4 w-4 text-muted-foreground" />
            <span>{practitioner.contact.phone}</span>
          </div>
        )}
        {practitioner.contact?.email && (
          <div className="flex items-center gap-2 text-sm">
            <Mail className="h-4 w-4 text-muted-foreground" />
            <span className="truncate">{practitioner.contact.email}</span>
          </div>
        )}
      </div>

      <Separator />

      {/* Stats */}
      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="p-2 bg-muted/50 rounded">
          <p className="text-lg font-semibold">{practitioner.totalAppointments || 0}</p>
          <p className="text-xs text-muted-foreground">This Month</p>
        </div>
        <div className="p-2 bg-muted/50 rounded">
          <p className="text-lg font-semibold">{practitioner.noShowRate || 0}%</p>
          <p className="text-xs text-muted-foreground">No-Show</p>
        </div>
        <div className="p-2 bg-muted/50 rounded">
          <p className="text-lg font-semibold">{practitioner.rating || "-"}</p>
          <p className="text-xs text-muted-foreground">Rating</p>
        </div>
      </div>

      {/* Leave Info */}
      {practitioner.status === "on_leave" && practitioner.leaveStart && practitioner.leaveEnd && (
        <>
          <Separator />
          <div className="p-2 bg-warning/10 rounded border border-warning/20">
            <p className="text-sm text-warning font-medium">On Leave</p>
            <p className="text-xs text-warning/80">
              {format(new Date(practitioner.leaveStart), "MMM d")} -{" "}
              {format(new Date(practitioner.leaveEnd), "MMM d, yyyy")}
            </p>
          </div>
        </>
      )}

      <Separator />

      {/* Actions */}
      <div className="grid grid-cols-2 gap-2">
        <Button variant="outline" size="sm" onClick={() => onAction?.("profile")}>
          <User className="h-4 w-4 mr-2" />
          Full Profile
        </Button>
        <Button variant="outline" size="sm" onClick={() => onAction?.("schedule")}>
          <Calendar className="h-4 w-4 mr-2" />
          View Schedule
        </Button>
      </div>
    </div>
  );
}

// ============================================================================
// Location Quick View
// ============================================================================

interface LocationQuickViewProps {
  location: Location;
  onNavigate?: () => void;
  onAction?: (action: string) => void;
}

function LocationQuickView({ location, onNavigate, onAction }: LocationQuickViewProps) {
  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-start gap-3">
        <div className="h-14 w-14 rounded-lg bg-primary/10 flex items-center justify-center">
          <Building className="h-7 w-7 text-primary" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-lg">{location.name}</h3>
          <StatusBadge status={location.status} />
        </div>
      </div>

      <Separator />

      {/* Address */}
      {location.address && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium flex items-center gap-2">
            <MapPin className="h-4 w-4 text-primary" />
            Address
          </h4>
          <p className="text-sm text-muted-foreground">
            {location.address.line1}
            {location.address.line2 && <>, {location.address.line2}</>}
            <br />
            {location.address.city}, {location.address.state} {location.address.postalCode}
          </p>
        </div>
      )}

      {/* Contact */}
      {location.contact && (
        <div className="space-y-2">
          {location.contact.phone && (
            <div className="flex items-center gap-2 text-sm">
              <Phone className="h-4 w-4 text-muted-foreground" />
              <span>{location.contact.phone}</span>
            </div>
          )}
          {location.contact.email && (
            <div className="flex items-center gap-2 text-sm">
              <Mail className="h-4 w-4 text-muted-foreground" />
              <span className="truncate">{location.contact.email}</span>
            </div>
          )}
        </div>
      )}

      <Separator />

      {/* Operating Hours */}
      <div className="space-y-2">
        <h4 className="text-sm font-medium flex items-center gap-2">
          <Clock className="h-4 w-4 text-primary" />
          Operating Hours
        </h4>
        <div className="space-y-1 text-sm">
          {location.operatingHours.length > 0 ? (
            location.operatingHours.map((hours) => (
              <div key={hours.dayOfWeek} className="flex justify-between">
                <span className="text-muted-foreground">
                  {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][hours.dayOfWeek]}
                </span>
                <span>
                  {hours.allDay
                    ? "24 Hours"
                    : `${hours.openingTime} - ${hours.closingTime}`}
                </span>
              </div>
            ))
          ) : (
            <p className="text-muted-foreground">Hours not set</p>
          )}
        </div>
      </div>

      <Separator />

      {/* Actions */}
      <div className="grid grid-cols-2 gap-2">
        <Button variant="outline" size="sm" onClick={() => onAction?.("details")}>
          <Building className="h-4 w-4 mr-2" />
          View Details
        </Button>
        <Button variant="outline" size="sm" onClick={() => onAction?.("schedule")}>
          <Calendar className="h-4 w-4 mr-2" />
          View Schedule
        </Button>
      </div>
    </div>
  );
}

// ============================================================================
// Main Quick View Panel Component
// ============================================================================

export function QuickViewPanel({
  isOpen,
  onClose,
  entityType,
  entityId,
  entity,
  onNavigate,
  onAction,
  className,
}: QuickViewPanelProps) {
  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/20 z-40"
        onClick={onClose}
      />

      {/* Panel */}
      <div
        className={cn(
          "fixed right-0 top-0 h-full w-full max-w-md bg-background border-l shadow-xl z-50",
          "transform transition-transform duration-300",
          isOpen ? "translate-x-0" : "translate-x-full",
          className
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold capitalize">
            Quick View: {entityType}
          </h2>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto h-[calc(100%-60px)]">
          {!entity ? (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
              <User className="h-12 w-12 mb-2" />
              <p>Loading...</p>
            </div>
          ) : entityType === "patient" ? (
            <PatientQuickView
              patient={entity as Patient}
              onNavigate={onNavigate}
              onAction={onAction}
            />
          ) : entityType === "practitioner" ? (
            <PractitionerQuickView
              practitioner={entity as Practitioner}
              onNavigate={onNavigate}
              onAction={onAction}
            />
          ) : entityType === "location" ? (
            <LocationQuickView
              location={entity as Location}
              onNavigate={onNavigate}
              onAction={onAction}
            />
          ) : null}
        </div>
      </div>
    </>
  );
}

export default QuickViewPanel;
