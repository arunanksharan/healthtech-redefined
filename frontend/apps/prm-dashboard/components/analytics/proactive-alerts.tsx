"use client";

import * as React from "react";
import {
  AlertTriangle,
  Bell,
  Calendar,
  CheckCircle,
  ChevronRight,
  Clock,
  MessageSquare,
  Phone,
  Send,
  Users,
  X,
  Eye,
  EyeOff,
  Filter,
  Settings,
  TrendingDown,
  UserX,
  DollarSign,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { ProactiveAlert } from "@/lib/store/analytics-store";
import { formatDistanceToNow, format } from "date-fns";

// ============================================================================
// Types
// ============================================================================

export type AlertPriority = "high" | "medium" | "low";
export type AlertType = "no_show_risk" | "cancellation" | "waitlist" | "capacity" | "revenue" | "quality";

export interface AlertPatient {
  id: string;
  name: string;
  appointmentTime?: string;
  riskScore?: number;
  reason?: string;
}

export interface ProactiveAlertCardProps {
  alert: ProactiveAlert;
  onPrimaryAction?: () => void;
  onSecondaryAction?: () => void;
  onDismiss?: () => void;
  onReview?: () => void;
  expanded?: boolean;
  className?: string;
}

// ============================================================================
// Alert Card Component
// ============================================================================

export function ProactiveAlertCard({
  alert,
  onPrimaryAction,
  onSecondaryAction,
  onDismiss,
  onReview,
  expanded = false,
  className,
}: ProactiveAlertCardProps) {
  const [showDetails, setShowDetails] = React.useState(expanded);
  const [isActioning, setIsActioning] = React.useState(false);

  const priorityStyles = {
    high: {
      bg: "bg-red-500/10",
      border: "border-red-500/20",
      badge: "bg-red-500 text-white",
      icon: "text-red-500",
    },
    medium: {
      bg: "bg-amber-500/10",
      border: "border-amber-500/20",
      badge: "bg-amber-500 text-white",
      icon: "text-amber-500",
    },
    low: {
      bg: "bg-blue-500/10",
      border: "border-blue-500/20",
      badge: "bg-blue-500 text-white",
      icon: "text-blue-500",
    },
  };

  const typeIcons = {
    no_show_risk: UserX,
    cancellation: X,
    waitlist: Users,
    capacity: TrendingDown,
    revenue: DollarSign,
    quality: AlertTriangle,
  };

  const styles = priorityStyles[alert.priority];
  const TypeIcon = typeIcons[alert.type] || AlertTriangle;

  const handlePrimaryAction = async () => {
    setIsActioning(true);
    try {
      await onPrimaryAction?.();
    } finally {
      setIsActioning(false);
    }
  };

  return (
    <Card className={cn("transition-all", styles.bg, styles.border, className)}>
      <CardContent className="pt-4">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-start gap-3">
            <div className={cn("h-10 w-10 rounded-lg flex items-center justify-center", styles.bg, styles.icon)}>
              <TypeIcon className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <Badge className={cn("text-xs uppercase font-semibold", styles.badge)}>
                  {alert.priority} Priority
                </Badge>
                <span className="text-xs text-muted-foreground">
                  {formatDistanceToNow(new Date(alert.createdAt), { addSuffix: true })}
                </span>
              </div>
              <h3 className="font-semibold mt-1">{alert.title}</h3>
            </div>
          </div>
          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onDismiss}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Description */}
        <p className="text-sm text-muted-foreground mb-4">{alert.description}</p>

        {/* Data Preview */}
        {alert.affectedItems && alert.affectedItems.length > 0 && (
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-muted-foreground">
                {alert.affectedItems.length} {alert.affectedItems.length === 1 ? "item" : "items"} affected
              </span>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 text-xs"
                onClick={() => setShowDetails(!showDetails)}
              >
                {showDetails ? (
                  <>
                    <EyeOff className="h-3 w-3 mr-1" />
                    Hide Details
                  </>
                ) : (
                  <>
                    <Eye className="h-3 w-3 mr-1" />
                    View Details
                  </>
                )}
              </Button>
            </div>

            {showDetails && (
              <div className="border rounded-lg overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow className="hover:bg-transparent">
                      <TableHead className="h-8 text-xs">Name</TableHead>
                      <TableHead className="h-8 text-xs">Time</TableHead>
                      <TableHead className="h-8 text-xs text-right">Risk</TableHead>
                      <TableHead className="h-8 text-xs">Reason</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {alert.affectedItems.slice(0, 5).map((item, index) => (
                      <TableRow key={index} className="hover:bg-muted/50">
                        <TableCell className="py-2 text-sm">{item.name}</TableCell>
                        <TableCell className="py-2 text-sm text-muted-foreground">
                          {item.time || "-"}
                        </TableCell>
                        <TableCell className="py-2 text-sm text-right">
                          {item.riskScore ? (
                            <Badge variant={item.riskScore >= 80 ? "destructive" : item.riskScore >= 60 ? "secondary" : "outline"}>
                              {item.riskScore}%
                            </Badge>
                          ) : "-"}
                        </TableCell>
                        <TableCell className="py-2 text-xs text-muted-foreground">
                          {item.reason || "-"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {alert.affectedItems.length > 5 && (
                  <div className="px-4 py-2 bg-muted/50 border-t">
                    <Button variant="link" size="sm" className="h-auto p-0 text-xs" onClick={onReview}>
                      View all {alert.affectedItems.length} items
                    </Button>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Suggested Action */}
        {alert.suggestedAction && (
          <div className="p-3 bg-primary/5 rounded-lg border border-primary/10 mb-4">
            <div className="flex items-center gap-2 mb-2">
              <Bell className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium">Suggested Action</span>
            </div>
            <p className="text-sm text-muted-foreground">{alert.suggestedAction}</p>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2">
          {alert.primaryAction && (
            <Button
              size="sm"
              className="flex-1"
              onClick={handlePrimaryAction}
              disabled={isActioning}
            >
              {isActioning ? (
                <>
                  <Clock className="h-4 w-4 mr-2 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Send className="h-4 w-4 mr-2" />
                  {alert.primaryAction}
                </>
              )}
            </Button>
          )}
          {alert.secondaryAction && (
            <Button variant="outline" size="sm" onClick={onSecondaryAction}>
              {alert.secondaryAction}
            </Button>
          )}
          <Button variant="ghost" size="sm" onClick={onDismiss}>
            Dismiss
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Proactive Alerts Panel
// ============================================================================

export interface ProactiveAlertsPanelProps {
  alerts: ProactiveAlert[];
  title?: string;
  maxVisible?: number;
  showFilters?: boolean;
  onAlertAction?: (alertId: string, action: "primary" | "secondary" | "dismiss" | "review") => void;
  onSeeAll?: () => void;
  onSettings?: () => void;
  isLoading?: boolean;
  className?: string;
}

export function ProactiveAlertsPanel({
  alerts,
  title = "Proactive Alerts",
  maxVisible = 3,
  showFilters = false,
  onAlertAction,
  onSeeAll,
  onSettings,
  isLoading = false,
  className,
}: ProactiveAlertsPanelProps) {
  const [priorityFilter, setPriorityFilter] = React.useState<AlertPriority | "all">("all");

  const filteredAlerts = priorityFilter === "all"
    ? alerts
    : alerts.filter((a) => a.priority === priorityFilter);

  const visibleAlerts = filteredAlerts.slice(0, maxVisible);
  const hasMore = filteredAlerts.length > maxVisible;

  const priorityCounts = {
    high: alerts.filter((a) => a.priority === "high").length,
    medium: alerts.filter((a) => a.priority === "medium").length,
    low: alerts.filter((a) => a.priority === "low").length,
  };

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-base font-medium flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-500" />
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-32 w-full rounded-lg" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-base font-medium flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-amber-500" />
          {title}
          {alerts.length > 0 && (
            <Badge variant="secondary" className="ml-2">
              {alerts.length} Active
            </Badge>
          )}
        </CardTitle>
        <div className="flex items-center gap-2">
          {onSettings && (
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onSettings}>
              <Settings className="h-4 w-4" />
            </Button>
          )}
          {hasMore && onSeeAll && (
            <Button variant="ghost" size="sm" onClick={onSeeAll}>
              See All
              <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {/* Priority filters */}
        {showFilters && alerts.length > 0 && (
          <div className="flex items-center gap-2 mb-4 overflow-x-auto pb-2">
            <Button
              variant={priorityFilter === "all" ? "default" : "outline"}
              size="sm"
              onClick={() => setPriorityFilter("all")}
            >
              All ({alerts.length})
            </Button>
            {priorityCounts.high > 0 && (
              <Button
                variant={priorityFilter === "high" ? "default" : "outline"}
                size="sm"
                onClick={() => setPriorityFilter("high")}
                className={priorityFilter !== "high" ? "border-red-500/30 text-red-500 hover:bg-red-500/10" : "bg-red-500 hover:bg-red-600"}
              >
                High ({priorityCounts.high})
              </Button>
            )}
            {priorityCounts.medium > 0 && (
              <Button
                variant={priorityFilter === "medium" ? "default" : "outline"}
                size="sm"
                onClick={() => setPriorityFilter("medium")}
                className={priorityFilter !== "medium" ? "border-amber-500/30 text-amber-500 hover:bg-amber-500/10" : "bg-amber-500 hover:bg-amber-600"}
              >
                Medium ({priorityCounts.medium})
              </Button>
            )}
            {priorityCounts.low > 0 && (
              <Button
                variant={priorityFilter === "low" ? "default" : "outline"}
                size="sm"
                onClick={() => setPriorityFilter("low")}
                className={priorityFilter !== "low" ? "border-blue-500/30 text-blue-500 hover:bg-blue-500/10" : "bg-blue-500 hover:bg-blue-600"}
              >
                Low ({priorityCounts.low})
              </Button>
            )}
          </div>
        )}

        {/* Alerts list */}
        {filteredAlerts.length === 0 ? (
          <div className="text-center py-8">
            <CheckCircle className="h-12 w-12 text-emerald-500 mx-auto mb-4" />
            <h3 className="font-medium mb-2">All Clear!</h3>
            <p className="text-sm text-muted-foreground">No active alerts at the moment</p>
          </div>
        ) : (
          <div className="space-y-3">
            {visibleAlerts.map((alert) => (
              <ProactiveAlertCard
                key={alert.id}
                alert={alert}
                onPrimaryAction={() => onAlertAction?.(alert.id, "primary")}
                onSecondaryAction={() => onAlertAction?.(alert.id, "secondary")}
                onDismiss={() => onAlertAction?.(alert.id, "dismiss")}
                onReview={() => onAlertAction?.(alert.id, "review")}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Alert Detail Dialog
// ============================================================================

export interface AlertDetailDialogProps {
  alert: ProactiveAlert | null;
  isOpen: boolean;
  onClose: () => void;
  onAction?: (action: "primary" | "secondary" | "dismiss") => void;
}

export function AlertDetailDialog({
  alert,
  isOpen,
  onClose,
  onAction,
}: AlertDetailDialogProps) {
  if (!alert) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangle className={cn(
              "h-5 w-5",
              alert.priority === "high" && "text-red-500",
              alert.priority === "medium" && "text-amber-500",
              alert.priority === "low" && "text-blue-500"
            )} />
            {alert.title}
          </DialogTitle>
          <DialogDescription>{alert.description}</DialogDescription>
        </DialogHeader>

        {/* Full details table */}
        {alert.affectedItems && alert.affectedItems.length > 0 && (
          <ScrollArea className="h-[300px] border rounded-lg">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Time</TableHead>
                  <TableHead className="text-right">Risk Score</TableHead>
                  <TableHead>Reason</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {alert.affectedItems.map((item, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-medium">{item.name}</TableCell>
                    <TableCell>{item.time || "-"}</TableCell>
                    <TableCell className="text-right">
                      {item.riskScore ? (
                        <Badge variant={item.riskScore >= 80 ? "destructive" : item.riskScore >= 60 ? "secondary" : "outline"}>
                          {item.riskScore}%
                        </Badge>
                      ) : "-"}
                    </TableCell>
                    <TableCell className="text-muted-foreground">{item.reason || "-"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </ScrollArea>
        )}

        <DialogFooter>
          <Button variant="ghost" onClick={() => onAction?.("dismiss")}>
            Dismiss
          </Button>
          {alert.secondaryAction && (
            <Button variant="outline" onClick={() => onAction?.("secondary")}>
              {alert.secondaryAction}
            </Button>
          )}
          {alert.primaryAction && (
            <Button onClick={() => onAction?.("primary")}>
              <Send className="h-4 w-4 mr-2" />
              {alert.primaryAction}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ============================================================================
// Compact Alert Badge
// ============================================================================

export interface AlertBadgeProps {
  count: number;
  highPriorityCount: number;
  onClick?: () => void;
  className?: string;
}

export function AlertBadge({
  count,
  highPriorityCount,
  onClick,
  className,
}: AlertBadgeProps) {
  if (count === 0) return null;

  return (
    <Button
      variant="ghost"
      size="sm"
      className={cn("relative", className)}
      onClick={onClick}
    >
      <Bell className="h-4 w-4" />
      <span className={cn(
        "absolute -top-1 -right-1 h-4 min-w-4 rounded-full text-xs flex items-center justify-center px-1",
        highPriorityCount > 0 ? "bg-red-500 text-white" : "bg-amber-500 text-white"
      )}>
        {count}
      </span>
    </Button>
  );
}

export default ProactiveAlertsPanel;
