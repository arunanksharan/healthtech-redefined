"use client";

import * as React from "react";
import {
  Building,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  Star,
  MessageSquare,
  Phone,
  ChevronRight,
  RefreshCw,
  Filter,
  Download,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { SentimentData } from "@/lib/store/analytics-store";
import { format } from "date-fns";

// ============================================================================
// Types
// ============================================================================

export type SentimentLevel = "good" | "watch" | "critical";

export interface SentimentDepartment {
  id: string;
  name: string;
  score: number;
  previousScore?: number;
  change?: number;
  totalFeedback: number;
  sources: {
    voice: number;
    whatsapp: number;
    survey: number;
    email: number;
  };
  topThemes: {
    positive: string[];
    negative: string[];
  };
}

export interface FeedbackItem {
  id: string;
  source: "voice" | "whatsapp" | "survey" | "email";
  sentiment: "positive" | "negative" | "neutral";
  score: number;
  text: string;
  themes: string[];
  patientId?: string;
  patientName?: string;
  dateTime: string;
  department: string;
}

// ============================================================================
// Sentiment Cell Component
// ============================================================================

interface SentimentCellProps {
  department: SentimentDepartment;
  onClick?: () => void;
  size?: "sm" | "md" | "lg";
  showTrend?: boolean;
}

function SentimentCell({
  department,
  onClick,
  size = "md",
  showTrend = true,
}: SentimentCellProps) {
  const getSentimentLevel = (score: number): SentimentLevel => {
    if (score >= 75) return "good";
    if (score >= 60) return "watch";
    return "critical";
  };

  const sentimentColors = {
    good: "bg-emerald-500",
    watch: "bg-amber-500",
    critical: "bg-red-500",
  };

  const sentimentBgColors = {
    good: "bg-emerald-500/10 border-emerald-500/30",
    watch: "bg-amber-500/10 border-amber-500/30",
    critical: "bg-red-500/10 border-red-500/30",
  };

  const level = getSentimentLevel(department.score);
  const TrendIcon = department.change && department.change > 0 ? TrendingUp : department.change && department.change < 0 ? TrendingDown : Minus;

  const sizeStyles = {
    sm: "p-2 min-h-[80px]",
    md: "p-4 min-h-[120px]",
    lg: "p-6 min-h-[160px]",
  };

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div
            className={cn(
              "rounded-lg border cursor-pointer transition-all hover:scale-[1.02] hover:shadow-md",
              sentimentBgColors[level],
              sizeStyles[size]
            )}
            onClick={onClick}
          >
            <div className="flex flex-col h-full justify-between">
              <div>
                <p className={cn(
                  "font-medium truncate",
                  size === "sm" ? "text-xs" : size === "md" ? "text-sm" : "text-base"
                )}>
                  {department.name}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <span className={cn(
                    "font-bold",
                    size === "sm" ? "text-lg" : size === "md" ? "text-2xl" : "text-3xl"
                  )}>
                    {department.score}%
                  </span>
                  {level === "good" && <Star className={cn("fill-emerald-500 text-emerald-500", size === "sm" ? "h-3 w-3" : "h-4 w-4")} />}
                  {level === "critical" && <AlertTriangle className={cn("text-red-500", size === "sm" ? "h-3 w-3" : "h-4 w-4")} />}
                </div>
              </div>

              {showTrend && department.change !== undefined && (
                <div className={cn(
                  "flex items-center gap-1",
                  department.change > 0 ? "text-emerald-600" : department.change < 0 ? "text-red-600" : "text-muted-foreground",
                  size === "sm" ? "text-xs" : "text-sm"
                )}>
                  <TrendIcon className={size === "sm" ? "h-3 w-3" : "h-4 w-4"} />
                  <span>{department.change > 0 ? "+" : ""}{department.change}%</span>
                </div>
              )}
            </div>
          </div>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-xs">
          <div className="space-y-2">
            <p className="font-medium">{department.name}</p>
            <p className="text-sm">Score: {department.score}% ({level})</p>
            {department.change !== undefined && (
              <p className={cn(
                "text-sm",
                department.change > 0 ? "text-emerald-500" : department.change < 0 ? "text-red-500" : ""
              )}>
                Change: {department.change > 0 ? "+" : ""}{department.change}% vs last period
              </p>
            )}
            <p className="text-xs text-muted-foreground">
              {department.totalFeedback} feedback items
            </p>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

// ============================================================================
// Main Sentiment Heatmap Component
// ============================================================================

export interface SentimentHeatmapProps {
  data: SentimentData;
  title?: string;
  description?: string;
  period?: string;
  onPeriodChange?: (period: string) => void;
  onDepartmentClick?: (department: SentimentDepartment) => void;
  onExport?: () => void;
  onRefresh?: () => void;
  layout?: "grid" | "floor";
  isLoading?: boolean;
  className?: string;
}

export function SentimentHeatmap({
  data,
  title = "Patient Sentiment Heatmap",
  description,
  period = "7d",
  onPeriodChange,
  onDepartmentClick,
  onExport,
  onRefresh,
  layout = "grid",
  isLoading = false,
  className,
}: SentimentHeatmapProps) {
  const [selectedDepartment, setSelectedDepartment] = React.useState<SentimentDepartment | null>(null);

  const handleDepartmentClick = (department: SentimentDepartment) => {
    setSelectedDepartment(department);
    onDepartmentClick?.(department);
  };

  // Find critical departments
  const criticalDepts = data.departments.filter((d) => d.score < 60);
  const watchDepts = data.departments.filter((d) => d.score >= 60 && d.score < 75);

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-medium">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <Skeleton key={i} className="h-32 rounded-lg" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card className={className}>
        <CardHeader className="flex flex-row items-start justify-between pb-2">
          <div>
            <CardTitle className="text-base font-medium">{title}</CardTitle>
            {description && (
              <CardDescription className="text-sm mt-1">{description}</CardDescription>
            )}
            <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <Phone className="h-3 w-3" /> Voice Calls
              </span>
              <span className="flex items-center gap-1">
                <MessageSquare className="h-3 w-3" /> WhatsApp
              </span>
              <span className="flex items-center gap-1">
                <Star className="h-3 w-3" /> Surveys
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {onPeriodChange && (
              <Select defaultValue={period} onValueChange={onPeriodChange}>
                <SelectTrigger className="w-[120px] h-8">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="24h">Last 24 Hours</SelectItem>
                  <SelectItem value="7d">Last 7 Days</SelectItem>
                  <SelectItem value="30d">Last 30 Days</SelectItem>
                  <SelectItem value="90d">Last 90 Days</SelectItem>
                </SelectContent>
              </Select>
            )}
            {onRefresh && (
              <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onRefresh}>
                <RefreshCw className="h-4 w-4" />
              </Button>
            )}
            {onExport && (
              <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onExport}>
                <Download className="h-4 w-4" />
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {/* Heatmap Grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
            {data.departments.map((department) => (
              <SentimentCell
                key={department.id}
                department={department}
                onClick={() => handleDepartmentClick(department)}
              />
            ))}
          </div>

          {/* Legend */}
          <div className="flex items-center justify-center gap-6 py-3 border-t">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded bg-emerald-500" />
              <span className="text-xs text-muted-foreground">Good (&gt;75%)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded bg-amber-500" />
              <span className="text-xs text-muted-foreground">Watch (60-75%)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded bg-red-500" />
              <span className="text-xs text-muted-foreground">Critical (&lt;60%)</span>
            </div>
          </div>

          {/* Critical Alerts */}
          {criticalDepts.length > 0 && (
            <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="h-4 w-4 text-red-500" />
                <span className="text-sm font-medium text-red-500">
                  Critical: {criticalDepts.length} department{criticalDepts.length > 1 ? "s" : ""} need attention
                </span>
              </div>
              <div className="space-y-2">
                {criticalDepts.slice(0, 2).map((dept) => (
                  <div key={dept.id} className="flex items-center justify-between">
                    <span className="text-sm">{dept.name} ({dept.score}%)</span>
                    <Button
                      variant="link"
                      size="sm"
                      className="h-auto p-0 text-red-500"
                      onClick={() => handleDepartmentClick(dept)}
                    >
                      View Details <ChevronRight className="h-3 w-3 ml-1" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Department Detail Dialog */}
      <SentimentDetailDialog
        department={selectedDepartment}
        isOpen={!!selectedDepartment}
        onClose={() => setSelectedDepartment(null)}
      />
    </>
  );
}

// ============================================================================
// Sentiment Detail Dialog
// ============================================================================

interface SentimentDetailDialogProps {
  department: SentimentDepartment | null;
  isOpen: boolean;
  onClose: () => void;
  onAssign?: () => void;
  onCreateAction?: () => void;
}

function SentimentDetailDialog({
  department,
  isOpen,
  onClose,
  onAssign,
  onCreateAction,
}: SentimentDetailDialogProps) {
  if (!department) return null;

  const getSentimentLevel = (score: number): SentimentLevel => {
    if (score >= 75) return "good";
    if (score >= 60) return "watch";
    return "critical";
  };

  const level = getSentimentLevel(department.score);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Building className="h-5 w-5" />
            {department.name} - Sentiment Analysis
          </DialogTitle>
          <DialogDescription>
            Based on {department.totalFeedback} feedback items from all channels
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Score Overview */}
          <div className={cn(
            "p-4 rounded-lg border",
            level === "good" && "bg-emerald-500/10 border-emerald-500/20",
            level === "watch" && "bg-amber-500/10 border-amber-500/20",
            level === "critical" && "bg-red-500/10 border-red-500/20"
          )}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Overall Score</p>
                <p className="text-4xl font-bold">{department.score}%</p>
              </div>
              <div className="text-right">
                {department.change !== undefined && (
                  <div className={cn(
                    "flex items-center gap-1",
                    department.change > 0 ? "text-emerald-500" : department.change < 0 ? "text-red-500" : "text-muted-foreground"
                  )}>
                    {department.change > 0 ? <TrendingUp className="h-4 w-4" /> : department.change < 0 ? <TrendingDown className="h-4 w-4" /> : <Minus className="h-4 w-4" />}
                    <span className="text-lg font-semibold">{department.change > 0 ? "+" : ""}{department.change}%</span>
                  </div>
                )}
                <p className="text-xs text-muted-foreground">vs last period</p>
              </div>
            </div>
          </div>

          {/* Feedback Sources */}
          <div>
            <p className="text-sm font-medium mb-2">Feedback Sources</p>
            <div className="grid grid-cols-4 gap-2">
              <div className="text-center p-2 bg-muted/50 rounded">
                <Phone className="h-4 w-4 mx-auto mb-1 text-muted-foreground" />
                <p className="text-lg font-semibold">{department.sources.voice}</p>
                <p className="text-xs text-muted-foreground">Calls</p>
              </div>
              <div className="text-center p-2 bg-muted/50 rounded">
                <MessageSquare className="h-4 w-4 mx-auto mb-1 text-muted-foreground" />
                <p className="text-lg font-semibold">{department.sources.whatsapp}</p>
                <p className="text-xs text-muted-foreground">WhatsApp</p>
              </div>
              <div className="text-center p-2 bg-muted/50 rounded">
                <Star className="h-4 w-4 mx-auto mb-1 text-muted-foreground" />
                <p className="text-lg font-semibold">{department.sources.survey}</p>
                <p className="text-xs text-muted-foreground">Surveys</p>
              </div>
              <div className="text-center p-2 bg-muted/50 rounded">
                <MessageSquare className="h-4 w-4 mx-auto mb-1 text-muted-foreground" />
                <p className="text-lg font-semibold">{department.sources.email}</p>
                <p className="text-xs text-muted-foreground">Email</p>
              </div>
            </div>
          </div>

          {/* Top Themes */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-medium mb-2 flex items-center gap-1 text-emerald-500">
                <TrendingUp className="h-4 w-4" />
                Positive Themes
              </p>
              <div className="space-y-1">
                {department.topThemes.positive.map((theme, index) => (
                  <Badge key={index} variant="outline" className="mr-1 mb-1 bg-emerald-500/10 border-emerald-500/30">
                    {theme}
                  </Badge>
                ))}
              </div>
            </div>
            <div>
              <p className="text-sm font-medium mb-2 flex items-center gap-1 text-red-500">
                <TrendingDown className="h-4 w-4" />
                Negative Themes
              </p>
              <div className="space-y-1">
                {department.topThemes.negative.map((theme, index) => (
                  <Badge key={index} variant="outline" className="mr-1 mb-1 bg-red-500/10 border-red-500/30">
                    {theme}
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
          <Button variant="outline" onClick={onAssign}>
            Assign to Manager
          </Button>
          <Button onClick={onCreateAction}>
            Create Action Plan
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ============================================================================
// Compact Sentiment Summary
// ============================================================================

export interface SentimentSummaryProps {
  data: SentimentData;
  onClick?: () => void;
  className?: string;
}

export function SentimentSummary({
  data,
  onClick,
  className,
}: SentimentSummaryProps) {
  const avgScore = Math.round(
    data.departments.reduce((acc, d) => acc + d.score, 0) / data.departments.length
  );
  const criticalCount = data.departments.filter((d) => d.score < 60).length;

  return (
    <div
      className={cn(
        "flex items-center gap-4 p-4 rounded-lg border bg-card cursor-pointer hover:bg-accent/50 transition-colors",
        className
      )}
      onClick={onClick}
    >
      <div className={cn(
        "h-12 w-12 rounded-full flex items-center justify-center font-bold text-lg",
        avgScore >= 75 ? "bg-emerald-500/20 text-emerald-500" :
        avgScore >= 60 ? "bg-amber-500/20 text-amber-500" :
        "bg-red-500/20 text-red-500"
      )}>
        {avgScore}%
      </div>
      <div className="flex-1">
        <p className="font-medium">Patient Sentiment</p>
        <p className="text-sm text-muted-foreground">
          {criticalCount > 0 ? (
            <span className="text-red-500">{criticalCount} critical areas</span>
          ) : (
            "All departments healthy"
          )}
        </p>
      </div>
      <ChevronRight className="h-5 w-5 text-muted-foreground" />
    </div>
  );
}

export default SentimentHeatmap;
