"use client";

import * as React from "react";
import {
  User,
  Calendar,
  Phone,
  Mail,
  AlertTriangle,
  Shield,
  ChevronDown,
  ChevronRight,
  Copy,
  ExternalLink,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { AllergyBadge, type AllergyData } from "./allergy-badge";

interface PatientBannerProps {
  patient: {
    id: string;
    firstName: string;
    lastName: string;
    dateOfBirth: Date | string;
    gender: "male" | "female" | "other";
    mrn: string;
    phone?: string;
    email?: string;
    photoUrl?: string;
    bloodType?: string;
    isVIP?: boolean;
    allergies?: AllergyData[];
    alerts?: {
      type: "warning" | "danger" | "info";
      message: string;
    }[];
  };
  className?: string;
  showActions?: boolean;
  onViewProfile?: () => void;
  onScheduleAppointment?: () => void;
}

const formatDate = (date: Date | string): string => {
  const d = new Date(date);
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
};

const calculateAge = (dateOfBirth: Date | string): number => {
  const today = new Date();
  const birthDate = new Date(dateOfBirth);
  let age = today.getFullYear() - birthDate.getFullYear();
  const monthDiff = today.getMonth() - birthDate.getMonth();
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
    age--;
  }
  return age;
};

const getInitials = (firstName: string, lastName: string): string => {
  return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase();
};

export function PatientBanner({
  patient,
  className,
  showActions = true,
  onViewProfile,
  onScheduleAppointment,
}: PatientBannerProps) {
  const [isExpanded, setIsExpanded] = React.useState(false);
  const age = calculateAge(patient.dateOfBirth);
  const hasAllergies = patient.allergies && patient.allergies.length > 0;
  const hasAlerts = patient.alerts && patient.alerts.length > 0;
  const hasCriticalAllergies = patient.allergies?.some((a) => a.severity === "severe");

  const copyMRN = () => {
    navigator.clipboard.writeText(patient.mrn);
  };

  return (
    <div
      className={cn(
        "bg-card border rounded-lg",
        hasCriticalAllergies && "border-allergy-severe/50",
        className
      )}
    >
      {/* Main Banner */}
      <div className="flex items-center gap-4 p-4">
        {/* Avatar */}
        <Avatar className="h-16 w-16 border-2 border-border">
          <AvatarImage src={patient.photoUrl} alt={`${patient.firstName} ${patient.lastName}`} />
          <AvatarFallback className="text-lg">
            {getInitials(patient.firstName, patient.lastName)}
          </AvatarFallback>
        </Avatar>

        {/* Patient Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h2 className="text-lg font-semibold text-foreground">
              {patient.firstName} {patient.lastName}
            </h2>
            {patient.isVIP && (
              <Badge variant="outline" className="border-warning text-warning">
                <Shield className="h-3 w-3 mr-1" />
                VIP
              </Badge>
            )}
            {patient.bloodType && (
              <Badge variant="secondary" className="font-mono">
                {patient.bloodType}
              </Badge>
            )}
          </div>

          <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground flex-wrap">
            <span className="flex items-center gap-1">
              <Calendar className="h-3.5 w-3.5" />
              {formatDate(patient.dateOfBirth)} ({age}y)
            </span>
            <span className="capitalize">{patient.gender}</span>
            <span className="flex items-center gap-1 font-mono">
              MRN: {patient.mrn}
              <button onClick={copyMRN} className="hover:text-foreground transition-colors">
                <Copy className="h-3 w-3" />
              </button>
            </span>
          </div>

          {/* Contact Info */}
          <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground flex-wrap">
            {patient.phone && (
              <span className="flex items-center gap-1">
                <Phone className="h-3.5 w-3.5" />
                {patient.phone}
              </span>
            )}
            {patient.email && (
              <span className="flex items-center gap-1">
                <Mail className="h-3.5 w-3.5" />
                {patient.email}
              </span>
            )}
          </div>
        </div>

        {/* Allergies Summary */}
        <div className="flex items-center gap-2">
          {hasAllergies && (
            <div className="flex items-center gap-1">
              <AlertTriangle
                className={cn(
                  "h-5 w-5",
                  hasCriticalAllergies ? "text-allergy-severe" : "text-allergy-moderate"
                )}
              />
              <span
                className={cn(
                  "text-sm font-medium",
                  hasCriticalAllergies ? "text-allergy-severe" : "text-allergy-moderate"
                )}
              >
                {patient.allergies!.length} Allerg{patient.allergies!.length > 1 ? "ies" : "y"}
              </span>
            </div>
          )}

          {/* Expand/Collapse Button */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            className="h-8 w-8 p-0"
          >
            {isExpanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </Button>

          {/* Actions */}
          {showActions && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  Actions
                  <ChevronDown className="h-4 w-4 ml-2" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={onViewProfile}>
                  <ExternalLink className="h-4 w-4 mr-2" />
                  View Full Profile
                </DropdownMenuItem>
                <DropdownMenuItem onClick={onScheduleAppointment}>
                  <Calendar className="h-4 w-4 mr-2" />
                  Schedule Appointment
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem>
                  <Phone className="h-4 w-4 mr-2" />
                  Call Patient
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Mail className="h-4 w-4 mr-2" />
                  Send Message
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      </div>

      {/* Expanded Section */}
      {isExpanded && (
        <div className="border-t border-border px-4 py-3 bg-muted/30">
          {/* Allergies */}
          {hasAllergies && (
            <div className="mb-3">
              <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
                Allergies
              </h4>
              <div className="flex flex-wrap gap-2">
                {patient.allergies!.map((allergy, index) => (
                  <AllergyBadge key={index} allergy={allergy} />
                ))}
              </div>
            </div>
          )}

          {/* Alerts */}
          {hasAlerts && (
            <div>
              <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
                Alerts
              </h4>
              <div className="space-y-1">
                {patient.alerts!.map((alert, index) => (
                  <div
                    key={index}
                    className={cn(
                      "flex items-center gap-2 text-sm p-2 rounded",
                      alert.type === "danger" && "bg-destructive/10 text-destructive",
                      alert.type === "warning" && "bg-warning/10 text-warning",
                      alert.type === "info" && "bg-info/10 text-info"
                    )}
                  >
                    <AlertTriangle className="h-4 w-4" />
                    {alert.message}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default PatientBanner;
