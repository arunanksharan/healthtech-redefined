"use client";

import * as React from "react";
import {
  Pill,
  Calendar,
  RefreshCw,
  AlertTriangle,
  Clock,
  User,
  MoreHorizontal,
  CheckCircle,
  XCircle,
  PauseCircle,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export interface MedicationData {
  id: string;
  name: string;
  dosage: string;
  frequency: string;
  route: string;
  status: "active" | "completed" | "discontinued" | "on-hold";
  prescribedDate: Date | string;
  prescribedBy: string;
  quantity?: number;
  refillsRemaining?: number;
  instructions?: string;
  warnings?: string[];
  isControlled?: boolean;
  isPRN?: boolean;
  lastFilledDate?: Date | string;
  nextRefillDate?: Date | string;
}

interface MedicationCardProps {
  medication: MedicationData;
  variant?: "default" | "compact" | "detailed";
  className?: string;
  onRefill?: () => void;
  onDiscontinue?: () => void;
  onEdit?: () => void;
}

const statusConfig = {
  active: {
    icon: CheckCircle,
    label: "Active",
    bgClass: "bg-success/10",
    textClass: "text-success",
    borderClass: "border-success/20",
  },
  completed: {
    icon: CheckCircle,
    label: "Completed",
    bgClass: "bg-muted",
    textClass: "text-muted-foreground",
    borderClass: "border-border",
  },
  discontinued: {
    icon: XCircle,
    label: "Discontinued",
    bgClass: "bg-destructive/10",
    textClass: "text-destructive",
    borderClass: "border-destructive/20",
  },
  "on-hold": {
    icon: PauseCircle,
    label: "On Hold",
    bgClass: "bg-warning/10",
    textClass: "text-warning",
    borderClass: "border-warning/20",
  },
};

const formatDate = (date: Date | string): string => {
  return new Date(date).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
};

export function MedicationCard({
  medication,
  variant = "default",
  className,
  onRefill,
  onDiscontinue,
  onEdit,
}: MedicationCardProps) {
  const status = statusConfig[medication.status];
  const StatusIcon = status.icon;
  const hasWarnings = medication.warnings && medication.warnings.length > 0;

  if (variant === "compact") {
    return (
      <div
        className={cn(
          "flex items-center justify-between p-3 rounded-lg border",
          status.bgClass,
          status.borderClass,
          className
        )}
      >
        <div className="flex items-center gap-3">
          <div className={cn("p-1.5 rounded-md", status.bgClass)}>
            <Pill className={cn("h-4 w-4", status.textClass)} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-medium text-sm">{medication.name}</span>
              {medication.isControlled && (
                <Badge variant="outline" className="text-xs bg-purple-100 text-purple-700 border-purple-200">
                  Controlled
                </Badge>
              )}
              {medication.isPRN && (
                <Badge variant="outline" className="text-xs">
                  PRN
                </Badge>
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              {medication.dosage} - {medication.frequency}
            </p>
          </div>
        </div>
        <Badge variant="outline" className={cn("text-xs", status.bgClass, status.textClass, status.borderClass)}>
          {status.label}
        </Badge>
      </div>
    );
  }

  return (
    <Card className={cn("border", status.borderClass, className)}>
      <CardContent className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className={cn("p-2 rounded-lg", status.bgClass)}>
              <Pill className={cn("h-5 w-5", status.textClass)} />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h4 className="font-semibold text-foreground">{medication.name}</h4>
                {medication.isControlled && (
                  <Badge variant="outline" className="text-xs bg-purple-100 text-purple-700 border-purple-200">
                    Controlled
                  </Badge>
                )}
                {medication.isPRN && (
                  <Badge variant="outline" className="text-xs">
                    PRN
                  </Badge>
                )}
              </div>
              <Badge
                variant="outline"
                className={cn("mt-1 text-xs", status.bgClass, status.textClass, status.borderClass)}
              >
                <StatusIcon className="h-3 w-3 mr-1" />
                {status.label}
              </Badge>
            </div>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={onEdit}>Edit</DropdownMenuItem>
              <DropdownMenuItem onClick={onRefill}>Request Refill</DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={onDiscontinue} className="text-destructive">
                Discontinue
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Dosage Info */}
        <div className="bg-muted/50 rounded-lg p-3 mb-3">
          <p className="text-sm font-medium text-foreground">{medication.dosage}</p>
          <p className="text-sm text-muted-foreground">
            {medication.frequency} - {medication.route}
          </p>
          {medication.instructions && (
            <p className="text-sm text-muted-foreground mt-1 italic">
              "{medication.instructions}"
            </p>
          )}
        </div>

        {/* Warnings */}
        {hasWarnings && (
          <div className="mb-3 p-2 bg-warning/10 border border-warning/20 rounded-lg">
            <div className="flex items-center gap-2 text-warning text-sm font-medium mb-1">
              <AlertTriangle className="h-4 w-4" />
              Warnings
            </div>
            <ul className="text-xs text-muted-foreground space-y-0.5">
              {medication.warnings!.map((warning, index) => (
                <li key={index}>• {warning}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Details */}
        {variant === "detailed" && (
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Calendar className="h-4 w-4" />
              <span>Prescribed: {formatDate(medication.prescribedDate)}</span>
            </div>
            <div className="flex items-center gap-2 text-muted-foreground">
              <User className="h-4 w-4" />
              <span>By: {medication.prescribedBy}</span>
            </div>
            {medication.quantity && (
              <div className="flex items-center gap-2 text-muted-foreground">
                <Pill className="h-4 w-4" />
                <span>Qty: {medication.quantity}</span>
              </div>
            )}
            {medication.refillsRemaining !== undefined && (
              <div className="flex items-center gap-2 text-muted-foreground">
                <RefreshCw className="h-4 w-4" />
                <span>Refills remaining: {medication.refillsRemaining}</span>
              </div>
            )}
            {medication.nextRefillDate && (
              <div className="flex items-center gap-2 text-muted-foreground">
                <Clock className="h-4 w-4" />
                <span>Next refill: {formatDate(medication.nextRefillDate)}</span>
              </div>
            )}
          </div>
        )}

        {/* Quick info footer for default variant */}
        {variant === "default" && (
          <div className="flex items-center justify-between text-xs text-muted-foreground pt-3 border-t border-border mt-3">
            <span className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              {formatDate(medication.prescribedDate)}
            </span>
            {medication.refillsRemaining !== undefined && (
              <span className="flex items-center gap-1">
                <RefreshCw className="h-3 w-3" />
                {medication.refillsRemaining} refills
              </span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Medication list component
interface MedicationListProps {
  medications: MedicationData[];
  variant?: "default" | "compact" | "detailed";
  className?: string;
  showActiveOnly?: boolean;
  onMedicationClick?: (medication: MedicationData) => void;
}

export function MedicationList({
  medications,
  variant = "compact",
  className,
  showActiveOnly = false,
  onMedicationClick,
}: MedicationListProps) {
  const filteredMedications = showActiveOnly
    ? medications.filter((m) => m.status === "active")
    : medications;

  if (filteredMedications.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No medications found
      </div>
    );
  }

  return (
    <div className={cn("space-y-3", className)}>
      {filteredMedications.map((medication) => (
        <div
          key={medication.id}
          onClick={() => onMedicationClick?.(medication)}
          className={onMedicationClick ? "cursor-pointer" : ""}
        >
          <MedicationCard medication={medication} variant={variant} />
        </div>
      ))}
    </div>
  );
}

export default MedicationCard;
