"use client";

import * as React from "react";
import {
  Calendar,
  Clock,
  User,
  Stethoscope,
  MapPin,
  Timer,
  Tag,
  AlertTriangle,
  CheckCircle2,
  Info,
  Sparkles,
  Phone,
  Pill,
  FileText,
  Send,
  Search,
  ChartBar,
  Building,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { EntityTag } from "./entity-tag";
import type { ParsedIntent, IntentType, ParsedEntity } from "@/lib/store/copilot-store";

// ============================================================================
// Types
// ============================================================================

interface GhostCardProps {
  intent: ParsedIntent;
  onExecute: () => void;
  onCancel: () => void;
  className?: string;
}

// ============================================================================
// Intent Display Configuration
// ============================================================================

const intentConfig: Record<IntentType, {
  icon: React.ElementType;
  title: string;
  actionLabel: string;
  color: string;
}> = {
  // Appointment Commands
  book_appointment: {
    icon: Calendar,
    title: "Book Appointment",
    actionLabel: "Book Appointment",
    color: "text-blue-600 dark:text-blue-400",
  },
  reschedule_appointment: {
    icon: Calendar,
    title: "Reschedule Appointment",
    actionLabel: "Reschedule",
    color: "text-orange-600 dark:text-orange-400",
  },
  cancel_appointment: {
    icon: Calendar,
    title: "Cancel Appointment",
    actionLabel: "Cancel Appointment",
    color: "text-destructive dark:text-red-400",
  },
  view_schedule: {
    icon: ChartBar,
    title: "View Schedule",
    actionLabel: "View Schedule",
    color: "text-purple-600 dark:text-purple-400",
  },
  find_slot: {
    icon: Search,
    title: "Find Available Slot",
    actionLabel: "Find Slots",
    color: "text-green-600 dark:text-green-400",
  },
  block_calendar: {
    icon: Calendar,
    title: "Block Calendar",
    actionLabel: "Block Time",
    color: "text-red-600 dark:text-red-400",
  },

  // Patient Commands
  find_patient: {
    icon: Search,
    title: "Find Patient",
    actionLabel: "Search",
    color: "text-blue-600 dark:text-blue-400",
  },
  add_patient: {
    icon: User,
    title: "Add New Patient",
    actionLabel: "Create Patient",
    color: "text-green-600 dark:text-green-400",
  },
  update_patient: {
    icon: User,
    title: "Update Patient",
    actionLabel: "Update",
    color: "text-orange-600 dark:text-orange-400",
  },
  view_patient_history: {
    icon: FileText,
    title: "View Patient History",
    actionLabel: "View History",
    color: "text-purple-600 dark:text-purple-400",
  },
  add_allergy: {
    icon: AlertTriangle,
    title: "Add Allergy",
    actionLabel: "Add Allergy",
    color: "text-red-600 dark:text-red-400",
  },
  record_vitals: {
    icon: FileText,
    title: "Record Vitals",
    actionLabel: "Record",
    color: "text-teal-600 dark:text-teal-400",
  },

  // Clinical Commands
  prescribe_medication: {
    icon: Pill,
    title: "Prescribe Medication",
    actionLabel: "Prescribe",
    color: "text-red-600 dark:text-red-400",
  },
  order_lab: {
    icon: FileText,
    title: "Order Lab Test",
    actionLabel: "Order Lab",
    color: "text-cyan-600 dark:text-cyan-400",
  },
  create_referral: {
    icon: Send,
    title: "Create Referral",
    actionLabel: "Create Referral",
    color: "text-indigo-600 dark:text-indigo-400",
  },
  add_clinical_note: {
    icon: FileText,
    title: "Add Clinical Note",
    actionLabel: "Add Note",
    color: "text-slate-600 dark:text-slate-400",
  },
  start_telehealth: {
    icon: Phone,
    title: "Start Telehealth",
    actionLabel: "Start Session",
    color: "text-green-600 dark:text-green-400",
  },

  // Communication Commands
  send_whatsapp: {
    icon: Send,
    title: "Send WhatsApp Message",
    actionLabel: "Send Message",
    color: "text-green-600 dark:text-green-400",
  },
  send_reminder: {
    icon: Clock,
    title: "Send Reminder",
    actionLabel: "Send Reminder",
    color: "text-blue-600 dark:text-blue-400",
  },
  broadcast_message: {
    icon: Send,
    title: "Broadcast Message",
    actionLabel: "Broadcast",
    color: "text-purple-600 dark:text-purple-400",
  },
  call_patient: {
    icon: Phone,
    title: "Call Patient",
    actionLabel: "Call",
    color: "text-blue-600 dark:text-blue-400",
  },

  // Analytics Commands
  show_appointments: {
    icon: Calendar,
    title: "Show Appointments",
    actionLabel: "Show",
    color: "text-blue-600 dark:text-blue-400",
  },
  show_analytics: {
    icon: ChartBar,
    title: "Show Analytics",
    actionLabel: "Show",
    color: "text-purple-600 dark:text-purple-400",
  },
  generate_report: {
    icon: FileText,
    title: "Generate Report",
    actionLabel: "Generate",
    color: "text-teal-600 dark:text-teal-400",
  },

  // Administrative Commands
  add_slot: {
    icon: Clock,
    title: "Add Time Slot",
    actionLabel: "Create Slots",
    color: "text-green-600 dark:text-green-400",
  },
  set_leave: {
    icon: Calendar,
    title: "Set Leave",
    actionLabel: "Set Leave",
    color: "text-orange-600 dark:text-orange-400",
  },
  add_department: {
    icon: Building,
    title: "Add Department",
    actionLabel: "Create",
    color: "text-blue-600 dark:text-blue-400",
  },
  show_tasks: {
    icon: FileText,
    title: "Show Tasks",
    actionLabel: "Show",
    color: "text-slate-600 dark:text-slate-400",
  },
  export_data: {
    icon: FileText,
    title: "Export Data",
    actionLabel: "Export",
    color: "text-teal-600 dark:text-teal-400",
  },

  // Unknown
  unknown: {
    icon: Sparkles,
    title: "Command",
    actionLabel: "Execute",
    color: "text-muted-foreground",
  },
};

// ============================================================================
// Ghost Card Component
// ============================================================================

export function GhostCard({
  intent,
  onExecute,
  onCancel,
  className,
}: GhostCardProps) {
  const config = intentConfig[intent.intent] || intentConfig.unknown;
  const IntentIcon = config.icon;

  const hasAllRequiredEntities = intent.missingRequired.length === 0;
  const hasLowConfidenceEntities = intent.entities.some(
    (e) => e.confidence < 80 && !e.isVerified
  );
  const allEntitiesVerified = intent.entities.every(
    (e) => e.isVerified || e.confidence >= 90
  );

  // Group entities by type for better display
  const groupedEntities = groupEntitiesByCategory(intent.entities);

  return (
    <div className={cn("p-4 space-y-4", className)}>
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className={cn(
            "p-2 rounded-lg",
            "bg-primary/10"
          )}>
            <IntentIcon className={cn("h-5 w-5", config.color)} />
          </div>
          <div>
            <h3 className="font-semibold text-foreground">{config.title}</h3>
            <p className="text-sm text-muted-foreground">
              I understood this as:
            </p>
          </div>
        </div>

        {/* Confidence Badge */}
        <Badge
          variant={intent.confidence >= 80 ? "default" : "secondary"}
          className={cn(
            intent.confidence >= 80
              ? "bg-success/10 text-success border-success/30"
              : "bg-warning/10 text-warning border-warning/30"
          )}
        >
          {intent.confidence}% confident
        </Badge>
      </div>

      {/* Entity Preview Card */}
      <div className="border border-border rounded-lg overflow-hidden">
        {/* Action Banner */}
        <div className="px-4 py-3 bg-primary/5 border-b border-border">
          <div className="flex items-center gap-2">
            <IntentIcon className={cn("h-4 w-4", config.color)} />
            <span className="font-medium text-sm">ACTION: {config.title}</span>
          </div>
        </div>

        {/* Entities */}
        <div className="p-4 space-y-4">
          {/* Primary Entities (Patient, Practitioner, Location) */}
          {groupedEntities.primary.length > 0 && (
            <div className="space-y-3">
              {groupedEntities.primary.map((entity) => (
                <EntityRow key={entity.id} entity={entity} />
              ))}
            </div>
          )}

          {/* Time/Date Entities */}
          {groupedEntities.temporal.length > 0 && (
            <>
              <Separator />
              <div className="space-y-3">
                {groupedEntities.temporal.map((entity) => (
                  <EntityRow key={entity.id} entity={entity} />
                ))}
              </div>
            </>
          )}

          {/* Other Entities */}
          {groupedEntities.other.length > 0 && (
            <>
              <Separator />
              <div className="space-y-3">
                {groupedEntities.other.map((entity) => (
                  <EntityRow key={entity.id} entity={entity} />
                ))}
              </div>
            </>
          )}

          {/* Missing Required Fields */}
          {intent.missingRequired.length > 0 && (
            <>
              <Separator />
              <div className="space-y-2">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                  Missing Information
                </p>
                {intent.missingRequired.map((field) => (
                  <div
                    key={field}
                    className="flex items-center gap-2 px-3 py-2 bg-warning/5 border border-warning/20 rounded-lg"
                  >
                    <AlertTriangle className="h-4 w-4 text-warning" />
                    <span className="text-sm capitalize">
                      {field.replace(/_/g, " ")} is required
                    </span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Warnings */}
      {hasLowConfidenceEntities && (
        <div className="flex items-start gap-2 px-3 py-2 bg-warning/5 border border-warning/20 rounded-lg">
          <AlertTriangle className="h-4 w-4 text-warning flex-shrink-0 mt-0.5" />
          <p className="text-sm text-warning">
            Some fields have low confidence. Click on them to verify or correct.
          </p>
        </div>
      )}

      {/* Pro Tip */}
      {!hasLowConfidenceEntities && hasAllRequiredEntities && (
        <div className="flex items-start gap-2 px-3 py-2 bg-primary/5 rounded-lg">
          <Info className="h-4 w-4 text-primary flex-shrink-0 mt-0.5" />
          <p className="text-sm text-muted-foreground">
            Pro tip: Say "change time to 3PM" to modify any field
          </p>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between pt-2">
        <Button variant="outline" onClick={onCancel}>
          Cancel
        </Button>

        <Button
          onClick={onExecute}
          disabled={!hasAllRequiredEntities}
          className="gap-2"
        >
          <CheckCircle2 className="h-4 w-4" />
          {config.actionLabel}
        </Button>
      </div>
    </div>
  );
}

// ============================================================================
// Entity Row Component
// ============================================================================

interface EntityRowProps {
  entity: ParsedEntity;
}

function EntityRow({ entity }: EntityRowProps) {
  return (
    <div className="flex items-start gap-3">
      <EntityTag entity={entity} size="md" />

      {/* Additional Info */}
      {entity.metadata && Object.keys(entity.metadata).length > 0 && (
        <div className="text-xs text-muted-foreground">
          {Object.entries(entity.metadata).map(([key, value]) => (
            <div key={key}>
              {String(value)}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Helper Functions
// ============================================================================

function groupEntitiesByCategory(entities: ParsedEntity[]) {
  const primary: ParsedEntity[] = [];
  const temporal: ParsedEntity[] = [];
  const other: ParsedEntity[] = [];

  entities.forEach((entity) => {
    switch (entity.type) {
      case "patient":
      case "practitioner":
      case "location":
      case "department":
        primary.push(entity);
        break;
      case "time":
      case "date":
      case "duration":
      case "recurrence":
        temporal.push(entity);
        break;
      default:
        other.push(entity);
    }
  });

  return { primary, temporal, other };
}

// ============================================================================
// Compact Ghost Card (for inline use)
// ============================================================================

interface CompactGhostCardProps {
  intent: ParsedIntent;
  className?: string;
}

export function CompactGhostCard({ intent, className }: CompactGhostCardProps) {
  const config = intentConfig[intent.intent] || intentConfig.unknown;
  const IntentIcon = config.icon;

  return (
    <div className={cn(
      "flex items-center gap-3 p-3 bg-muted/50 rounded-lg border",
      className
    )}>
      <div className={cn("p-1.5 rounded-md", "bg-primary/10")}>
        <IntentIcon className={cn("h-4 w-4", config.color)} />
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{config.title}</p>
        <p className="text-xs text-muted-foreground truncate">
          {intent.entities.map((e) => e.rawValue).join(" • ")}
        </p>
      </div>

      <Badge variant="outline" className="text-xs">
        {intent.confidence}%
      </Badge>
    </div>
  );
}

export default GhostCard;
