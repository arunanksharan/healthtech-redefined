"use client";

import * as React from "react";
import {
  AlertCircle,
  Calendar,
  ChevronRight,
  Clock,
  CheckCircle2,
  FlaskConical,
  Eye,
  Syringe,
  Stethoscope,
  FileText,
  Bell,
  Plus,
  XCircle,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { CareGap, CareGapStatus, CareGapAction } from "@/lib/store/patient-profile-store";
import { formatDistanceToNow, format, isPast, isFuture, differenceInDays } from "date-fns";

// ============================================================================
// Types
// ============================================================================

interface CareGapsSectionProps {
  careGaps: CareGap[];
  isLoading?: boolean;
  onAction?: (gapId: string, action: CareGapAction) => void;
  onViewAll?: () => void;
  className?: string;
}

// ============================================================================
// Helper Functions
// ============================================================================

const getCategoryIcon = (category: CareGap["category"]) => {
  switch (category) {
    case "chronic":
      return FlaskConical;
    case "preventive":
      return Syringe;
    case "screening":
      return Eye;
    case "wellness":
      return Stethoscope;
    default:
      return FileText;
  }
};

const getStatusConfig = (status: CareGapStatus) => {
  switch (status) {
    case "overdue":
      return {
        label: "Overdue",
        bgColor: "bg-destructive/10",
        textColor: "text-destructive",
        borderColor: "border-destructive/20",
        dotColor: "bg-destructive",
        icon: AlertCircle,
      };
    case "due-soon":
      return {
        label: "Due Soon",
        bgColor: "bg-warning/10",
        textColor: "text-warning",
        borderColor: "border-warning/20",
        dotColor: "bg-warning",
        icon: Clock,
      };
    case "up-to-date":
      return {
        label: "Up to Date",
        bgColor: "bg-success/10",
        textColor: "text-success",
        borderColor: "border-success/20",
        dotColor: "bg-success",
        icon: CheckCircle2,
      };
    case "not-applicable":
      return {
        label: "N/A",
        bgColor: "bg-muted/50",
        textColor: "text-muted-foreground",
        borderColor: "border-muted",
        dotColor: "bg-muted-foreground",
        icon: XCircle,
      };
    default:
      return {
        label: "Unknown",
        bgColor: "bg-muted/50",
        textColor: "text-muted-foreground",
        borderColor: "border-muted",
        dotColor: "bg-muted-foreground",
        icon: FileText,
      };
  }
};

const formatDueDate = (gap: CareGap): string => {
  if (!gap.dueDate) return "";

  const dueDate = new Date(gap.dueDate);

  if (gap.status === "overdue" && gap.overdueDays) {
    return `Overdue: ${gap.overdueDays} days`;
  }

  if (isPast(dueDate)) {
    return `Overdue: ${formatDistanceToNow(dueDate)}`;
  }

  if (isFuture(dueDate)) {
    const daysUntil = differenceInDays(dueDate, new Date());
    if (daysUntil <= 7) {
      return `Due: ${formatDistanceToNow(dueDate, { addSuffix: false })}`;
    }
    return `Due: ${format(dueDate, "MMM d")}`;
  }

  return `Due: ${format(dueDate, "MMM d, yyyy")}`;
};

// ============================================================================
// Care Gap Card Component
// ============================================================================

interface CareGapCardProps {
  gap: CareGap;
  onAction?: (gapId: string, action: CareGapAction) => void;
}

function CareGapCard({ gap, onAction }: CareGapCardProps) {
  const statusConfig = getStatusConfig(gap.status);
  const CategoryIcon = getCategoryIcon(gap.category);
  const StatusIcon = statusConfig.icon;

  return (
    <div
      className={cn(
        "p-4 rounded-lg border transition-colors",
        statusConfig.bgColor,
        statusConfig.borderColor
      )}
    >
      {/* Main content row */}
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className={cn("p-2 rounded-lg bg-background/80 shrink-0", statusConfig.textColor)}>
          <CategoryIcon className="h-4 w-4" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <h4 className="font-medium text-foreground truncate">{gap.title}</h4>
              {gap.description && (
                <p className="text-sm text-muted-foreground mt-0.5 line-clamp-1">
                  {gap.description}
                </p>
              )}
            </div>
            {gap.status !== "up-to-date" && (
              <Badge
                variant="outline"
                className={cn(
                  "text-xs shrink-0 whitespace-nowrap",
                  statusConfig.textColor,
                  statusConfig.borderColor
                )}
              >
                <StatusIcon className="h-3 w-3 mr-1" />
                {formatDueDate(gap)}
              </Badge>
            )}
          </div>

          {gap.lastCompletedDate && (
            <p className="text-xs text-muted-foreground mt-1">
              Last: {format(new Date(gap.lastCompletedDate), "MMM d, yyyy")}
              {gap.status === "up-to-date" && " ✓"}
            </p>
          )}
        </div>
      </div>

      {/* Actions - separate row for better spacing */}
      {gap.actions.length > 0 && gap.status !== "up-to-date" && (
        <div className="flex items-center gap-2 mt-3 ml-11">
          {gap.actions.slice(0, 2).map((action) => (
            <Button
              key={action.id}
              variant={action.type.includes("order") || action.type.includes("referral") ? "default" : "outline"}
              size="sm"
              className="text-xs h-7 px-3"
              onClick={() => onAction?.(gap.id, action)}
            >
              {action.label}
            </Button>
          ))}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Care Gaps Section Component
// ============================================================================

export function CareGapsSection({
  careGaps,
  isLoading = false,
  onAction,
  onViewAll,
  className,
}: CareGapsSectionProps) {
  // Group care gaps by status
  const overdueGaps = careGaps.filter((g) => g.status === "overdue");
  const dueSoonGaps = careGaps.filter((g) => g.status === "due-soon");
  const upToDateGaps = careGaps.filter((g) => g.status === "up-to-date");

  // Loading state
  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-primary" />
            Care Gaps & Preventive Care
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-20 bg-muted/50 rounded-lg animate-pulse"
              />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (careGaps.length === 0) {
    return (
      <Card className={className}>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-primary" />
            Care Gaps & Preventive Care
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <CheckCircle2 className="h-8 w-8 text-success mb-2" />
            <p className="text-sm text-muted-foreground">
              All preventive care items are up to date
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-primary" />
            Care Gaps & Preventive Care
          </CardTitle>
          {onViewAll && (
            <Button
              variant="ghost"
              size="sm"
              className="text-xs h-7"
              onClick={onViewAll}
            >
              View All
              <ChevronRight className="h-3 w-3 ml-1" />
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Overdue Section */}
        {overdueGaps.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-destructive" />
              <h3 className="text-sm font-medium text-destructive">
                Overdue ({overdueGaps.length})
              </h3>
            </div>
            <div className="space-y-2">
              {overdueGaps.map((gap) => (
                <CareGapCard key={gap.id} gap={gap} onAction={onAction} />
              ))}
            </div>
          </div>
        )}

        {/* Due Soon Section */}
        {dueSoonGaps.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-warning" />
              <h3 className="text-sm font-medium text-warning">
                Due Soon ({dueSoonGaps.length})
              </h3>
            </div>
            <div className="space-y-2">
              {dueSoonGaps.map((gap) => (
                <CareGapCard key={gap.id} gap={gap} onAction={onAction} />
              ))}
            </div>
          </div>
        )}

        {/* Up to Date Section */}
        {upToDateGaps.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-success" />
              <h3 className="text-sm font-medium text-success">
                Up to Date ({upToDateGaps.length})
              </h3>
            </div>
            <ul className="space-y-1 pl-4">
              {upToDateGaps.map((gap) => (
                <li
                  key={gap.id}
                  className="text-sm text-muted-foreground flex items-center gap-2"
                >
                  <CheckCircle2 className="h-3 w-3 text-success" />
                  <span>{gap.title}</span>
                  {gap.lastCompletedDate && (
                    <span className="text-xs">
                      ({format(new Date(gap.lastCompletedDate), "MMM yyyy")})
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Compact Care Gaps Widget (for sidebar/summary)
// ============================================================================

interface CompactCareGapsProps {
  careGaps: CareGap[];
  onExpand?: () => void;
  className?: string;
}

export function CompactCareGaps({
  careGaps,
  onExpand,
  className,
}: CompactCareGapsProps) {
  const overdueCount = careGaps.filter((g) => g.status === "overdue").length;
  const dueSoonCount = careGaps.filter((g) => g.status === "due-soon").length;

  if (careGaps.length === 0) {
    return (
      <div className={cn("p-4 bg-success/5 rounded-lg border border-success/10", className)}>
        <div className="flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-success" />
          <span className="text-sm font-medium">All care items up to date</span>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("p-4 bg-muted/50 rounded-lg", className)}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium">Care Gaps</span>
        </div>
        {onExpand && (
          <Button
            variant="ghost"
            size="sm"
            className="h-6 text-xs"
            onClick={onExpand}
          >
            View
          </Button>
        )}
      </div>

      <div className="flex items-center gap-4 mt-3">
        {overdueCount > 0 && (
          <div className="flex items-center gap-1.5">
            <div className="h-2 w-2 rounded-full bg-destructive" />
            <span className="text-sm text-destructive font-medium">
              {overdueCount} overdue
            </span>
          </div>
        )}
        {dueSoonCount > 0 && (
          <div className="flex items-center gap-1.5">
            <div className="h-2 w-2 rounded-full bg-warning" />
            <span className="text-sm text-warning font-medium">
              {dueSoonCount} due soon
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Care Gaps Skeleton
// ============================================================================

export function CareGapsSkeleton({ className }: { className?: string }) {
  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-primary" />
          Care Gaps & Preventive Care
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="h-4 bg-muted rounded animate-pulse w-24" />
          <div className="h-20 bg-muted/50 rounded-lg animate-pulse" />
          <div className="h-20 bg-muted/50 rounded-lg animate-pulse" />
        </div>
        <div className="space-y-2">
          <div className="h-4 bg-muted rounded animate-pulse w-20" />
          <div className="h-16 bg-muted/50 rounded-lg animate-pulse" />
        </div>
      </CardContent>
    </Card>
  );
}

export default CareGapsSection;
