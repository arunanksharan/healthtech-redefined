"use client";

import * as React from "react";
import { useState } from "react";
import {
  User,
  Stethoscope,
  MapPin,
  Clock,
  Calendar,
  Zap,
  Pill,
  Building,
  Timer,
  Tag,
  Phone,
  Hash,
  Check,
  AlertTriangle,
  ChevronDown,
  X,
  Search,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { useCopilotStore } from "@/lib/store/copilot-store";
import type { ParsedEntity, EntityType, EntityOption } from "@/lib/store/copilot-store";

// ============================================================================
// Types
// ============================================================================

interface EntityTagProps {
  entity: ParsedEntity;
  isEditable?: boolean;
  size?: "sm" | "md" | "lg";
  className?: string;
}

interface EntityCorrectionPopoverProps {
  entity: ParsedEntity;
  onSelect: (option: EntityOption) => void;
  onClose: () => void;
}

// ============================================================================
// Entity Icon Mapping
// ============================================================================

const entityIcons: Record<EntityType, React.ElementType> = {
  patient: User,
  practitioner: Stethoscope,
  location: MapPin,
  time: Clock,
  date: Calendar,
  action: Zap,
  medication: Pill,
  department: Building,
  duration: Timer,
  visit_type: Tag,
  recurrence: Calendar,
  phone: Phone,
  mrn: Hash,
  unknown: Tag,
};

const entityLabels: Record<EntityType, string> = {
  patient: "Patient",
  practitioner: "Doctor",
  location: "Location",
  time: "Time",
  date: "Date",
  action: "Action",
  medication: "Medication",
  department: "Department",
  duration: "Duration",
  visit_type: "Visit Type",
  recurrence: "Recurrence",
  phone: "Phone",
  mrn: "MRN",
  unknown: "Unknown",
};

const entityColors: Record<EntityType, { bg: string; text: string; border: string }> = {
  patient: { bg: "bg-blue-500/10", text: "text-blue-600", border: "border-blue-500/30" },
  practitioner: { bg: "bg-purple-500/10", text: "text-purple-600", border: "border-purple-500/30" },
  location: { bg: "bg-green-500/10", text: "text-green-600", border: "border-green-500/30" },
  time: { bg: "bg-orange-500/10", text: "text-orange-600", border: "border-orange-500/30" },
  date: { bg: "bg-pink-500/10", text: "text-pink-600", border: "border-pink-500/30" },
  action: { bg: "bg-indigo-500/10", text: "text-indigo-600", border: "border-indigo-500/30" },
  medication: { bg: "bg-red-500/10", text: "text-red-600", border: "border-red-500/30" },
  department: { bg: "bg-teal-500/10", text: "text-teal-600", border: "border-teal-500/30" },
  duration: { bg: "bg-amber-500/10", text: "text-amber-600", border: "border-amber-500/30" },
  visit_type: { bg: "bg-cyan-500/10", text: "text-cyan-600", border: "border-cyan-500/30" },
  recurrence: { bg: "bg-violet-500/10", text: "text-violet-600", border: "border-violet-500/30" },
  phone: { bg: "bg-emerald-500/10", text: "text-emerald-600", border: "border-emerald-500/30" },
  mrn: { bg: "bg-slate-500/10", text: "text-slate-600", border: "border-slate-500/30" },
  unknown: { bg: "bg-gray-500/10", text: "text-gray-600", border: "border-gray-500/30" },
};

// ============================================================================
// Entity Tag Component
// ============================================================================

export function EntityTag({
  entity,
  isEditable = true,
  size = "md",
  className,
}: EntityTagProps) {
  const [isOpen, setIsOpen] = useState(false);

  const {
    verifyEntity,
    selectEntityAlternative,
  } = useCopilotStore();

  const Icon = entityIcons[entity.type];
  const label = entityLabels[entity.type];
  const colors = entityColors[entity.type];

  const isHighConfidence = entity.confidence >= 80 || entity.isVerified;
  const isLowConfidence = entity.confidence < 80 && !entity.isVerified;
  const hasAlternatives = entity.alternatives && entity.alternatives.length > 0;

  const handleVerify = () => {
    verifyEntity(entity.id);
  };

  const handleSelectAlternative = (option: EntityOption) => {
    selectEntityAlternative(entity.id, option.id);
    setIsOpen(false);
  };

  const sizeClasses = {
    sm: "text-xs px-2 py-0.5 gap-1",
    md: "text-sm px-3 py-1.5 gap-1.5",
    lg: "text-base px-4 py-2 gap-2",
  };

  const iconSizes = {
    sm: "h-3 w-3",
    md: "h-3.5 w-3.5",
    lg: "h-4 w-4",
  };

  const TagContent = (
    <div
      className={cn(
        "inline-flex items-center rounded-lg border transition-all",
        sizeClasses[size],
        colors.bg,
        colors.border,
        isEditable && "cursor-pointer hover:shadow-sm",
        isLowConfidence && "border-warning/50 bg-warning/5",
        entity.isVerified && "ring-1 ring-success/30",
        className
      )}
    >
      {/* Icon */}
      <Icon className={cn(iconSizes[size], colors.text)} />

      {/* Label & Value */}
      <div className="flex items-center gap-1">
        <span className="text-muted-foreground">{label}:</span>
        <span className={cn("font-medium", colors.text)}>{entity.rawValue}</span>
      </div>

      {/* Confidence Indicator */}
      {isHighConfidence ? (
        <Check className={cn(iconSizes[size], "text-success")} />
      ) : isLowConfidence ? (
        <AlertTriangle className={cn(iconSizes[size], "text-warning")} />
      ) : null}

      {/* Dropdown Indicator */}
      {isEditable && hasAlternatives && (
        <ChevronDown className={cn(iconSizes[size], "text-muted-foreground")} />
      )}
    </div>
  );

  if (!isEditable || !hasAlternatives) {
    return (
      <div className="inline-flex items-center gap-1">
        {TagContent}
        {isLowConfidence && !entity.isVerified && (
          <Button
            variant="ghost"
            size="sm"
            className="h-6 px-2 text-xs"
            onClick={handleVerify}
          >
            Verify
          </Button>
        )}
      </div>
    );
  }

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        {TagContent}
      </PopoverTrigger>
      <PopoverContent className="w-80 p-0" align="start">
        <EntityCorrectionPopover
          entity={entity}
          onSelect={handleSelectAlternative}
          onClose={() => setIsOpen(false)}
        />
      </PopoverContent>
    </Popover>
  );
}

// ============================================================================
// Entity Correction Popover Component
// ============================================================================

function EntityCorrectionPopover({
  entity,
  onSelect,
  onClose,
}: EntityCorrectionPopoverProps) {
  const [searchValue, setSearchValue] = useState("");

  const Icon = entityIcons[entity.type];
  const label = entityLabels[entity.type];

  const filteredOptions = entity.alternatives?.filter((option) =>
    option.label.toLowerCase().includes(searchValue.toLowerCase()) ||
    option.sublabel?.toLowerCase().includes(searchValue.toLowerCase())
  ) || [];

  return (
    <div className="flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b">
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-muted-foreground" />
          <span className="font-medium">Select {label}</span>
        </div>
        <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Search */}
      <div className="p-3 border-b">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder={`Search ${label.toLowerCase()}s...`}
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {/* Options */}
      <div className="max-h-60 overflow-y-auto p-2">
        {entity.rawValue && (
          <div className="px-2 py-1.5 text-xs text-muted-foreground mb-1">
            Matching "{entity.rawValue}":
          </div>
        )}

        {filteredOptions.length === 0 ? (
          <div className="px-2 py-4 text-center text-sm text-muted-foreground">
            No matches found
          </div>
        ) : (
          <div className="space-y-1">
            {filteredOptions.map((option, index) => (
              <button
                key={option.id}
                onClick={() => onSelect(option)}
                className={cn(
                  "w-full flex items-start gap-3 px-3 py-2 rounded-lg text-left transition-colors",
                  "hover:bg-muted",
                  index === 0 && "bg-primary/5"
                )}
              >
                {/* Radio Circle */}
                <div className={cn(
                  "mt-0.5 w-4 h-4 rounded-full border-2 flex items-center justify-center flex-shrink-0",
                  index === 0 ? "border-primary" : "border-muted-foreground"
                )}>
                  {index === 0 && (
                    <div className="w-2 h-2 rounded-full bg-primary" />
                  )}
                </div>

                {/* Option Content */}
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-foreground">{option.label}</div>
                  {option.sublabel && (
                    <div className="text-xs text-muted-foreground truncate">
                      {option.sublabel}
                    </div>
                  )}
                </div>

                {/* Best Match Badge */}
                {index === 0 && (
                  <span className="text-xs text-primary">Most likely</span>
                )}
              </button>
            ))}
          </div>
        )}

        {/* Create New Option */}
        {entity.type === "patient" && (
          <button
            className="w-full flex items-center gap-3 px-3 py-2 mt-2 rounded-lg text-left border border-dashed border-muted-foreground/30 hover:border-primary/50 hover:bg-primary/5 transition-colors"
            onClick={() => onSelect({ id: "new", label: "Create new patient", value: "new" })}
          >
            <div className="w-4 h-4 rounded-full border-2 border-dashed border-muted-foreground flex items-center justify-center">
              <span className="text-xs">+</span>
            </div>
            <span className="text-muted-foreground">Create new patient</span>
          </button>
        )}
      </div>

      {/* Footer */}
      <div className="px-3 py-2 border-t bg-muted/30">
        <p className="text-xs text-muted-foreground">
          Click to select or start typing to search
        </p>
      </div>
    </div>
  );
}

// ============================================================================
// Entity Tags List Component
// ============================================================================

interface EntityTagsListProps {
  entities: ParsedEntity[];
  isEditable?: boolean;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function EntityTagsList({
  entities,
  isEditable = true,
  size = "md",
  className,
}: EntityTagsListProps) {
  return (
    <div className={cn("flex flex-wrap gap-2", className)}>
      {entities.map((entity) => (
        <EntityTag
          key={entity.id}
          entity={entity}
          isEditable={isEditable}
          size={size}
        />
      ))}
    </div>
  );
}

export default EntityTag;
