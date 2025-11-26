"use client";

import * as React from "react";
import { AlertTriangle, AlertCircle, Info } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Badge } from "@/components/ui/badge";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

export interface AllergyData {
  allergen: string;
  severity: "severe" | "moderate" | "mild";
  reaction?: string;
  verifiedDate?: Date | string;
  source?: "patient-reported" | "clinical" | "ehr-import";
}

interface AllergyBadgeProps {
  allergy: AllergyData;
  showDetails?: boolean;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const severityConfig = {
  severe: {
    bgClass: "bg-allergy-severe/10 hover:bg-allergy-severe/20",
    textClass: "text-allergy-severe",
    borderClass: "border-allergy-severe/30",
    icon: AlertTriangle,
    label: "Severe",
  },
  moderate: {
    bgClass: "bg-allergy-moderate/10 hover:bg-allergy-moderate/20",
    textClass: "text-allergy-moderate",
    borderClass: "border-allergy-moderate/30",
    icon: AlertCircle,
    label: "Moderate",
  },
  mild: {
    bgClass: "bg-allergy-mild/10 hover:bg-allergy-mild/20",
    textClass: "text-allergy-mild",
    borderClass: "border-allergy-mild/30",
    icon: Info,
    label: "Mild",
  },
};

const sizeConfig = {
  sm: {
    badge: "text-xs px-2 py-0.5",
    icon: "h-3 w-3",
  },
  md: {
    badge: "text-sm px-2.5 py-1",
    icon: "h-3.5 w-3.5",
  },
  lg: {
    badge: "text-base px-3 py-1.5",
    icon: "h-4 w-4",
  },
};

const formatDate = (date: Date | string): string => {
  return new Date(date).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
};

export function AllergyBadge({
  allergy,
  showDetails = true,
  size = "md",
  className,
}: AllergyBadgeProps) {
  const config = severityConfig[allergy.severity];
  const sizes = sizeConfig[size];
  const Icon = config.icon;

  const badge = (
    <Badge
      variant="outline"
      className={cn(
        "inline-flex items-center gap-1.5 cursor-pointer transition-colors border",
        config.bgClass,
        config.textClass,
        config.borderClass,
        sizes.badge,
        className
      )}
    >
      <Icon className={sizes.icon} />
      <span className="font-medium">{allergy.allergen}</span>
    </Badge>
  );

  if (!showDetails) {
    return badge;
  }

  return (
    <Popover>
      <PopoverTrigger asChild>{badge}</PopoverTrigger>
      <PopoverContent className="w-72" align="start">
        <div className="space-y-3">
          {/* Header */}
          <div className="flex items-start justify-between">
            <div>
              <h4 className="font-semibold text-foreground">{allergy.allergen}</h4>
              <Badge
                variant="outline"
                className={cn(
                  "mt-1 text-xs",
                  config.bgClass,
                  config.textClass,
                  config.borderClass
                )}
              >
                {config.label} Severity
              </Badge>
            </div>
            <Icon className={cn("h-5 w-5", config.textClass)} />
          </div>

          {/* Reaction */}
          {allergy.reaction && (
            <div>
              <h5 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
                Reaction
              </h5>
              <p className="text-sm text-foreground">{allergy.reaction}</p>
            </div>
          )}

          {/* Metadata */}
          <div className="pt-2 border-t border-border text-xs text-muted-foreground space-y-1">
            {allergy.verifiedDate && (
              <p>Verified: {formatDate(allergy.verifiedDate)}</p>
            )}
            {allergy.source && (
              <p>
                Source:{" "}
                {allergy.source === "patient-reported"
                  ? "Patient Reported"
                  : allergy.source === "clinical"
                  ? "Clinical Documentation"
                  : "EHR Import"}
              </p>
            )}
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}

// Allergy list component for displaying multiple allergies
interface AllergyListProps {
  allergies: AllergyData[];
  className?: string;
  maxVisible?: number;
  size?: "sm" | "md" | "lg";
}

export function AllergyList({
  allergies,
  className,
  maxVisible = 3,
  size = "md",
}: AllergyListProps) {
  const [showAll, setShowAll] = React.useState(false);

  if (allergies.length === 0) {
    return (
      <span className="text-sm text-muted-foreground">No known allergies</span>
    );
  }

  // Sort by severity
  const sortedAllergies = [...allergies].sort((a, b) => {
    const severityOrder = { severe: 0, moderate: 1, mild: 2 };
    return severityOrder[a.severity] - severityOrder[b.severity];
  });

  const visibleAllergies = showAll
    ? sortedAllergies
    : sortedAllergies.slice(0, maxVisible);
  const hiddenCount = sortedAllergies.length - maxVisible;

  return (
    <div className={cn("flex flex-wrap items-center gap-2", className)}>
      {visibleAllergies.map((allergy, index) => (
        <AllergyBadge key={index} allergy={allergy} size={size} />
      ))}
      {!showAll && hiddenCount > 0 && (
        <button
          onClick={() => setShowAll(true)}
          className="text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          +{hiddenCount} more
        </button>
      )}
      {showAll && hiddenCount > 0 && (
        <button
          onClick={() => setShowAll(false)}
          className="text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          Show less
        </button>
      )}
    </div>
  );
}

export default AllergyBadge;
