"use client";

import * as React from "react";
import {
  User,
  Phone,
  Mail,
  MapPin,
  Calendar,
  Shield,
  Stethoscope,
  Edit,
  MoreVertical,
  AlertTriangle,
  AlertCircle,
  Heart,
  X,
  ChevronRight,
  Clock,
  CheckCircle2,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Card, CardContent } from "@/components/ui/card";
import type { Patient, PatientAlert, AlertSeverity, AlertType } from "@/lib/store/patient-profile-store";

// ============================================================================
// Types
// ============================================================================

interface PatientHeaderProps {
  patient: Patient;
  alerts: PatientAlert[];
  onEdit?: () => void;
  onAction?: (action: string) => void;
  onAlertDismiss?: (alertId: string) => void;
  onAlertAcknowledge?: (alertId: string) => void;
  className?: string;
}

// ============================================================================
// Alert Configuration
// ============================================================================

const alertSeverityConfig: Record<AlertSeverity, { icon: React.ElementType; color: string; bgColor: string; borderColor: string }> = {
  critical: {
    icon: AlertCircle,
    color: "text-destructive",
    bgColor: "bg-destructive/5",
    borderColor: "border-destructive/30",
  },
  high: {
    icon: AlertTriangle,
    color: "text-urgent",
    bgColor: "bg-urgent/5",
    borderColor: "border-urgent/30",
  },
  medium: {
    icon: AlertTriangle,
    color: "text-warning",
    bgColor: "bg-warning/5",
    borderColor: "border-warning/30",
  },
  low: {
    icon: AlertCircle,
    color: "text-info",
    bgColor: "bg-info/5",
    borderColor: "border-info/30",
  },
};

const alertTypeIcons: Record<AlertType, React.ElementType> = {
  allergy: AlertTriangle,
  condition: Heart,
  "care-gap": Clock,
  "fall-risk": AlertTriangle,
  medication: AlertCircle,
  flag: AlertTriangle,
};

// ============================================================================
// Helper Functions
// ============================================================================

function formatDate(date: Date): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date);
}

function formatTime(date: Date): string {
  return new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  }).format(date);
}

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function calculateAge(dob: Date): number {
  const today = new Date();
  let age = today.getFullYear() - dob.getFullYear();
  const m = today.getMonth() - dob.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) {
    age--;
  }
  return age;
}

// ============================================================================
// Patient Header Component
// ============================================================================

export function PatientHeader({
  patient,
  alerts,
  onEdit,
  onAction,
  onAlertDismiss,
  onAlertAcknowledge,
  className,
}: PatientHeaderProps) {
  const criticalAlerts = alerts.filter((a) => a.severity === "critical" || a.severity === "high");
  const otherAlerts = alerts.filter((a) => a.severity === "medium" || a.severity === "low");

  return (
    <div className={cn("space-y-4", className)}>
      {/* Main Header Card */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col lg:flex-row gap-6">
            {/* Patient Info Section */}
            <div className="flex items-start gap-4 flex-1">
              {/* Avatar */}
              <Avatar className="h-20 w-20 border-2 border-border">
                <AvatarImage src={patient.photo} alt={patient.name} />
                <AvatarFallback className="text-xl font-semibold">
                  {getInitials(patient.name)}
                </AvatarFallback>
              </Avatar>

              {/* Demographics */}
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h1 className="text-2xl font-bold text-foreground">{patient.name}</h1>
                    <p className="text-muted-foreground">
                      DOB: {formatDate(patient.dob)} ({patient.age} years) • {patient.gender.charAt(0).toUpperCase() + patient.gender.slice(1)}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      MRN: {patient.mrn}
                      {patient.ssn && ` • SSN: ${patient.ssn}`}
                    </p>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" onClick={onEdit}>
                      <Edit className="h-4 w-4 mr-2" />
                      Edit
                    </Button>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => onAction?.("print")}>
                          Print Summary
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => onAction?.("export")}>
                          Export Record
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={() => onAction?.("merge")}>
                          Merge Records
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={() => onAction?.("deactivate")}
                        >
                          Deactivate Patient
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>

                {/* Contact Info */}
                <div className="flex flex-wrap items-center gap-4 mt-3">
                  <div className="flex items-center gap-1.5 text-sm">
                    <Phone className="h-4 w-4 text-muted-foreground" />
                    <span>{patient.phone}</span>
                  </div>
                  {patient.email && (
                    <div className="flex items-center gap-1.5 text-sm">
                      <Mail className="h-4 w-4 text-muted-foreground" />
                      <span>{patient.email}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Quick Info Cards */}
            <div className="grid grid-cols-2 lg:grid-cols-1 gap-3 lg:w-72">
              {/* Primary Provider */}
              {patient.primaryProvider && (
                <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/50">
                  <Stethoscope className="h-4 w-4 text-muted-foreground mt-0.5" />
                  <div className="text-sm">
                    <p className="text-muted-foreground">Primary Provider</p>
                    <p className="font-medium">{patient.primaryProvider.name}</p>
                    {patient.primaryProvider.specialty && (
                      <p className="text-xs text-muted-foreground">
                        {patient.primaryProvider.specialty}
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Insurance */}
              {patient.insurance && (
                <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/50">
                  <Shield className="h-4 w-4 text-muted-foreground mt-0.5" />
                  <div className="text-sm">
                    <p className="text-muted-foreground">Insurance</p>
                    <p className="font-medium">
                      {patient.insurance.provider} {patient.insurance.planName}
                    </p>
                    <Badge
                      variant="outline"
                      className={cn(
                        "text-xs mt-1",
                        patient.insurance.status === "active"
                          ? "text-success border-success/30"
                          : "text-destructive border-destructive/30"
                      )}
                    >
                      {patient.insurance.status.charAt(0).toUpperCase() + patient.insurance.status.slice(1)}
                    </Badge>
                  </div>
                </div>
              )}

              {/* Address */}
              {patient.address && (
                <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/50 col-span-2 lg:col-span-1">
                  <MapPin className="h-4 w-4 text-muted-foreground mt-0.5" />
                  <div className="text-sm">
                    <p className="text-muted-foreground">Address</p>
                    <p className="font-medium">{patient.address.line1}</p>
                    <p className="text-xs text-muted-foreground">
                      {patient.address.city}, {patient.address.state} {patient.address.postalCode}
                    </p>
                  </div>
                </div>
              )}

              {/* Next Appointment */}
              {patient.nextAppointment && (
                <div className="flex items-start gap-3 p-3 rounded-lg bg-primary/5 border border-primary/20 col-span-2 lg:col-span-1">
                  <Calendar className="h-4 w-4 text-primary mt-0.5" />
                  <div className="text-sm flex-1">
                    <p className="text-muted-foreground">Next Appointment</p>
                    <p className="font-medium text-primary">
                      {formatDate(patient.nextAppointment.dateTime)} at{" "}
                      {formatTime(patient.nextAppointment.dateTime)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {patient.nextAppointment.provider} • {patient.nextAppointment.type}
                    </p>
                  </div>
                  <Badge variant="outline" className="text-xs">
                    {patient.nextAppointment.status}
                  </Badge>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Alerts Section */}
      {alerts.length > 0 && (
        <Card className="border-warning/30">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="h-4 w-4 text-warning" />
              <h3 className="font-semibold text-sm">
                Alerts ({alerts.length})
              </h3>
            </div>

            <div className="space-y-2">
              {/* Critical/High Alerts */}
              {criticalAlerts.map((alert) => (
                <AlertBanner
                  key={alert.id}
                  alert={alert}
                  onDismiss={() => onAlertDismiss?.(alert.id)}
                  onAcknowledge={() => onAlertAcknowledge?.(alert.id)}
                />
              ))}

              {/* Other Alerts (collapsible if too many) */}
              {otherAlerts.map((alert) => (
                <AlertBanner
                  key={alert.id}
                  alert={alert}
                  onDismiss={() => onAlertDismiss?.(alert.id)}
                  onAcknowledge={() => onAlertAcknowledge?.(alert.id)}
                  compact
                />
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ============================================================================
// Alert Banner Component
// ============================================================================

interface AlertBannerProps {
  alert: PatientAlert;
  onDismiss?: () => void;
  onAcknowledge?: () => void;
  compact?: boolean;
}

function AlertBanner({ alert, onDismiss, onAcknowledge, compact = false }: AlertBannerProps) {
  const config = alertSeverityConfig[alert.severity];
  const TypeIcon = alertTypeIcons[alert.type] || AlertTriangle;

  if (compact) {
    return (
      <div
        className={cn(
          "flex items-center gap-2 px-3 py-2 rounded-lg border",
          config.bgColor,
          config.borderColor
        )}
      >
        <TypeIcon className={cn("h-4 w-4 flex-shrink-0", config.color)} />
        <span className="text-sm flex-1">{alert.title}</span>
        {alert.acknowledgedAt && (
          <CheckCircle2 className="h-4 w-4 text-success" />
        )}
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6"
          onClick={onDismiss}
        >
          <X className="h-3 w-3" />
        </Button>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex items-start gap-3 p-3 rounded-lg border",
        config.bgColor,
        config.borderColor
      )}
    >
      <TypeIcon className={cn("h-5 w-5 flex-shrink-0 mt-0.5", config.color)} />
      <div className="flex-1 min-w-0">
        <p className={cn("font-medium", config.color)}>{alert.title}</p>
        {alert.description && (
          <p className="text-sm text-muted-foreground mt-0.5">
            {alert.description}
          </p>
        )}
        {alert.source && (
          <p className="text-xs text-muted-foreground mt-1">
            Source: {alert.source}
          </p>
        )}
      </div>
      <div className="flex items-center gap-1">
        {!alert.acknowledgedAt && (
          <Button variant="ghost" size="sm" onClick={onAcknowledge}>
            Acknowledge
          </Button>
        )}
        {alert.acknowledgedAt && (
          <Badge variant="outline" className="text-xs text-success border-success/30">
            Acknowledged
          </Badge>
        )}
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onDismiss}>
          <X className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

// ============================================================================
// Compact Patient Header (for sub-pages)
// ============================================================================

interface CompactPatientHeaderProps {
  patient: Patient;
  alerts?: PatientAlert[];
  onBack?: () => void;
  className?: string;
}

export function CompactPatientHeader({
  patient,
  alerts = [],
  onBack,
  className,
}: CompactPatientHeaderProps) {
  const criticalAlertCount = alerts.filter(
    (a) => a.severity === "critical" || a.severity === "high"
  ).length;

  return (
    <div
      className={cn(
        "flex items-center gap-4 p-4 bg-card border-b border-border",
        className
      )}
    >
      {onBack && (
        <Button variant="ghost" size="sm" onClick={onBack}>
          <ChevronRight className="h-4 w-4 rotate-180 mr-1" />
          Back
        </Button>
      )}

      <Avatar className="h-10 w-10">
        <AvatarImage src={patient.photo} alt={patient.name} />
        <AvatarFallback>{getInitials(patient.name)}</AvatarFallback>
      </Avatar>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <h2 className="font-semibold text-foreground truncate">
            {patient.name}
          </h2>
          {criticalAlertCount > 0 && (
            <Badge variant="destructive" className="text-xs">
              {criticalAlertCount} Alert{criticalAlertCount !== 1 ? "s" : ""}
            </Badge>
          )}
        </div>
        <p className="text-sm text-muted-foreground">
          {patient.age}y {patient.gender.charAt(0).toUpperCase()} • MRN: {patient.mrn}
        </p>
      </div>

      {patient.nextAppointment && (
        <div className="hidden sm:flex items-center gap-2 text-sm">
          <Calendar className="h-4 w-4 text-primary" />
          <span className="text-muted-foreground">Next:</span>
          <span className="font-medium">
            {formatDate(patient.nextAppointment.dateTime)}
          </span>
        </div>
      )}
    </div>
  );
}

export default PatientHeader;
