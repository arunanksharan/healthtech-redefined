"use client";

import * as React from "react";
import {
  TrendingUp,
  TrendingDown,
  ArrowRight,
  AlertTriangle,
  Star,
  Target,
  ExternalLink,
  Minus,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";

// ============================================================================
// Types
// ============================================================================

export type StatStatus = "success" | "warning" | "danger" | "neutral";
export type TrendDirection = "up" | "down" | "flat";

interface BaseStatCardProps {
  title: string;
  className?: string;
  onClick?: () => void;
}

// ============================================================================
// Simple Stat Card
// ============================================================================

interface SimpleStatCardProps extends BaseStatCardProps {
  value: string | number;
  trend?: {
    value: number;
    direction: TrendDirection;
    label: string;
  };
  status?: StatStatus;
  icon?: React.ReactNode;
  actionLabel?: string;
  onAction?: () => void;
}

export function SimpleStatCard({
  title,
  value,
  trend,
  status = "neutral",
  icon,
  actionLabel = "View",
  onAction,
  onClick,
  className,
}: SimpleStatCardProps) {
  const statusColors = {
    success: "text-emerald-500",
    warning: "text-amber-500",
    danger: "text-red-500",
    neutral: "text-muted-foreground",
  };

  const trendColors = {
    up: "text-emerald-500",
    down: "text-red-500",
    flat: "text-muted-foreground",
  };

  const TrendIcon = trend?.direction === "up" ? TrendingUp : trend?.direction === "down" ? TrendingDown : Minus;

  return (
    <Card
      className={cn(
        "hover:shadow-md transition-all cursor-pointer",
        onClick && "hover:border-primary/50",
        className
      )}
      onClick={onClick}
    >
      <CardContent className="pt-6">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <p className={cn("text-3xl font-bold", statusColors[status])}>{value}</p>
            {trend && (
              <div className={cn("flex items-center gap-1 text-sm", trendColors[trend.direction])}>
                <TrendIcon className="h-4 w-4" />
                <span>{trend.direction === "up" ? "+" : trend.direction === "down" ? "-" : ""}{Math.abs(trend.value)}%</span>
                <span className="text-muted-foreground">{trend.label}</span>
              </div>
            )}
          </div>
          {icon && (
            <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
              {icon}
            </div>
          )}
        </div>
        {onAction && (
          <Button
            variant="ghost"
            size="sm"
            className="mt-4 w-full justify-between group"
            onClick={(e) => {
              e.stopPropagation();
              onAction();
            }}
          >
            {actionLabel}
            <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Progress Stat Card
// ============================================================================

interface ProgressStatCardProps extends BaseStatCardProps {
  current: number;
  target: number;
  unit?: string;
  format?: (value: number) => string;
  subtitle?: string;
  status?: StatStatus;
}

export function ProgressStatCard({
  title,
  current,
  target,
  unit = "",
  format = (v) => v.toLocaleString(),
  subtitle,
  status,
  onClick,
  className,
}: ProgressStatCardProps) {
  const percentage = Math.min(Math.round((current / target) * 100), 100);

  const getProgressStatus = () => {
    if (status) return status;
    if (percentage >= 90) return "success";
    if (percentage >= 70) return "neutral";
    if (percentage >= 50) return "warning";
    return "danger";
  };

  const progressColors = {
    success: "bg-emerald-500",
    warning: "bg-amber-500",
    danger: "bg-red-500",
    neutral: "bg-primary",
  };

  const currentStatus = getProgressStatus();

  return (
    <Card
      className={cn(
        "hover:shadow-md transition-all",
        onClick && "cursor-pointer hover:border-primary/50",
        className
      )}
      onClick={onClick}
    >
      <CardContent className="pt-6">
        <div className="space-y-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">{title}</p>
              <p className="text-2xl font-bold mt-1">
                {unit}{format(current)} <span className="text-lg text-muted-foreground font-normal">/ {unit}{format(target)}</span>
              </p>
            </div>
            <div className={cn(
              "px-2 py-1 rounded text-sm font-medium",
              currentStatus === "success" && "bg-emerald-500/10 text-emerald-500",
              currentStatus === "warning" && "bg-amber-500/10 text-amber-500",
              currentStatus === "danger" && "bg-red-500/10 text-red-500",
              currentStatus === "neutral" && "bg-primary/10 text-primary"
            )}>
              {percentage}%
            </div>
          </div>

          <div className="space-y-2">
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div
                className={cn("h-full transition-all rounded-full", progressColors[currentStatus])}
                style={{ width: `${percentage}%` }}
              />
            </div>
            {subtitle && (
              <p className="text-xs text-muted-foreground">{subtitle}</p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Trend Stat Card (with Sparkline)
// ============================================================================

interface TrendStatCardProps extends BaseStatCardProps {
  value: string | number;
  sparklineData: number[];
  trend?: {
    value: number;
    direction: TrendDirection;
  };
  subtitle?: string;
  status?: StatStatus;
}

export function TrendStatCard({
  title,
  value,
  sparklineData,
  trend,
  subtitle,
  status = "neutral",
  onClick,
  className,
}: TrendStatCardProps) {
  const maxVal = Math.max(...sparklineData);
  const minVal = Math.min(...sparklineData);
  const range = maxVal - minVal || 1;

  // Generate SVG path for sparkline
  const generateSparklinePath = () => {
    const width = 100;
    const height = 30;
    const padding = 2;
    const points = sparklineData.map((val, i) => {
      const x = padding + (i / (sparklineData.length - 1)) * (width - padding * 2);
      const y = height - padding - ((val - minVal) / range) * (height - padding * 2);
      return `${x},${y}`;
    });
    return `M${points.join(" L")}`;
  };

  const sparklineColor = status === "success" ? "#10b981" : status === "warning" ? "#f59e0b" : status === "danger" ? "#ef4444" : "#6366f1";

  return (
    <Card
      className={cn(
        "hover:shadow-md transition-all",
        onClick && "cursor-pointer hover:border-primary/50",
        className
      )}
      onClick={onClick}
    >
      <CardContent className="pt-6">
        <div className="space-y-3">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">{title}</p>
              <div className="flex items-baseline gap-2 mt-1">
                <p className="text-3xl font-bold">{value}</p>
                {trend && (
                  <span className={cn(
                    "text-sm font-medium flex items-center",
                    trend.direction === "up" && "text-emerald-500",
                    trend.direction === "down" && "text-red-500",
                    trend.direction === "flat" && "text-muted-foreground"
                  )}>
                    {trend.direction === "up" ? <TrendingUp className="h-3 w-3 mr-0.5" /> :
                     trend.direction === "down" ? <TrendingDown className="h-3 w-3 mr-0.5" /> : null}
                    {trend.value}%
                  </span>
                )}
              </div>
            </div>
            <Star className="h-5 w-5 text-amber-400 fill-amber-400" />
          </div>

          {/* Sparkline */}
          <div className="h-8">
            <svg viewBox="0 0 100 30" className="w-full h-full" preserveAspectRatio="none">
              <defs>
                <linearGradient id={`sparkline-gradient-${title.replace(/\s/g, '')}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={sparklineColor} stopOpacity="0.2" />
                  <stop offset="100%" stopColor={sparklineColor} stopOpacity="0" />
                </linearGradient>
              </defs>
              {/* Area fill */}
              <path
                d={`${generateSparklinePath()} L100,30 L0,30 Z`}
                fill={`url(#sparkline-gradient-${title.replace(/\s/g, '')})`}
              />
              {/* Line */}
              <path
                d={generateSparklinePath()}
                fill="none"
                stroke={sparklineColor}
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>

          {subtitle && (
            <p className="text-xs text-muted-foreground">{subtitle}</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Comparison Stat Card
// ============================================================================

interface ComparisonStatCardProps extends BaseStatCardProps {
  yourValue: number | string;
  benchmarkValue: number | string;
  yourLabel?: string;
  benchmarkLabel?: string;
  unit?: string;
  status?: StatStatus;
  actionLabel?: string;
  onAction?: () => void;
}

export function ComparisonStatCard({
  title,
  yourValue,
  benchmarkValue,
  yourLabel = "Yours",
  benchmarkLabel = "Benchmark",
  unit = "",
  status,
  actionLabel,
  onAction,
  onClick,
  className,
}: ComparisonStatCardProps) {
  const numericYours = typeof yourValue === "number" ? yourValue : parseFloat(yourValue) || 0;
  const numericBenchmark = typeof benchmarkValue === "number" ? benchmarkValue : parseFloat(benchmarkValue) || 0;

  const computedStatus = status || (numericYours >= numericBenchmark ? "success" : "warning");

  return (
    <Card
      className={cn(
        "hover:shadow-md transition-all",
        onClick && "cursor-pointer hover:border-primary/50",
        className
      )}
      onClick={onClick}
    >
      <CardContent className="pt-6">
        <p className="text-sm font-medium text-muted-foreground mb-4">{title}</p>

        <div className="flex items-center justify-center gap-6">
          <div className="text-center">
            <p className={cn(
              "text-2xl font-bold",
              computedStatus === "success" && "text-emerald-500",
              computedStatus === "warning" && "text-amber-500",
              computedStatus === "danger" && "text-red-500"
            )}>
              {unit}{yourValue}
            </p>
            <p className="text-xs text-muted-foreground mt-1">{yourLabel}</p>
          </div>

          <div className="text-muted-foreground font-medium">vs</div>

          <div className="text-center">
            <p className="text-2xl font-bold text-muted-foreground">
              {unit}{benchmarkValue}
            </p>
            <p className="text-xs text-muted-foreground mt-1">{benchmarkLabel}</p>
          </div>
        </div>

        {computedStatus === "warning" && (
          <div className="flex items-center justify-center gap-1.5 mt-3 text-amber-500">
            <AlertTriangle className="h-4 w-4" />
            <span className="text-sm">Below benchmark</span>
          </div>
        )}

        {onAction && actionLabel && (
          <Button
            variant="outline"
            size="sm"
            className="mt-4 w-full"
            onClick={(e) => {
              e.stopPropagation();
              onAction();
            }}
          >
            {actionLabel}
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Action Stat Card
// ============================================================================

interface ActionStatCardProps extends BaseStatCardProps {
  value: string | number;
  subtitle?: string;
  priority: "high" | "medium" | "low";
  actionLabel: string;
  onAction: () => void;
  icon?: React.ReactNode;
}

export function ActionStatCard({
  title,
  value,
  subtitle,
  priority,
  actionLabel,
  onAction,
  icon,
  onClick,
  className,
}: ActionStatCardProps) {
  const priorityStyles = {
    high: {
      bg: "bg-red-500/10",
      border: "border-red-500/30",
      icon: "text-red-500",
      text: "text-red-500",
      button: "bg-red-500 hover:bg-red-600 text-white",
    },
    medium: {
      bg: "bg-amber-500/10",
      border: "border-amber-500/30",
      icon: "text-amber-500",
      text: "text-amber-500",
      button: "bg-amber-500 hover:bg-amber-600 text-white",
    },
    low: {
      bg: "bg-blue-500/10",
      border: "border-blue-500/30",
      icon: "text-blue-500",
      text: "text-blue-500",
      button: "bg-blue-500 hover:bg-blue-600 text-white",
    },
  };

  const styles = priorityStyles[priority];

  return (
    <Card
      className={cn(
        "hover:shadow-md transition-all",
        styles.bg,
        styles.border,
        onClick && "cursor-pointer",
        className
      )}
      onClick={onClick}
    >
      <CardContent className="pt-6">
        <div className="flex items-start gap-3">
          <div className={cn("h-10 w-10 rounded-lg flex items-center justify-center", styles.bg, styles.icon)}>
            {icon || <AlertTriangle className="h-5 w-5" />}
          </div>
          <div className="flex-1 min-w-0">
            <p className={cn("text-sm font-medium", styles.text)}>{title}</p>
            <p className="text-2xl font-bold mt-1">{value}</p>
            {subtitle && (
              <p className="text-xs text-muted-foreground mt-0.5">{subtitle}</p>
            )}
          </div>
        </div>

        <Button
          className={cn("mt-4 w-full", styles.button)}
          onClick={(e) => {
            e.stopPropagation();
            onAction();
          }}
        >
          {actionLabel}
        </Button>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Skeleton Loaders
// ============================================================================

export function StatCardSkeleton({ className }: { className?: string }) {
  return (
    <Card className={className}>
      <CardContent className="pt-6">
        <div className="space-y-3">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-8 w-16" />
          <Skeleton className="h-3 w-32" />
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Stat Cards Grid
// ============================================================================

interface StatCardsGridProps {
  children: React.ReactNode;
  columns?: 2 | 3 | 4 | 5;
  className?: string;
}

export function StatCardsGrid({ children, columns = 4, className }: StatCardsGridProps) {
  const gridCols = {
    2: "grid-cols-1 md:grid-cols-2",
    3: "grid-cols-1 md:grid-cols-2 lg:grid-cols-3",
    4: "grid-cols-1 md:grid-cols-2 lg:grid-cols-4",
    5: "grid-cols-1 md:grid-cols-2 lg:grid-cols-5",
  };

  return (
    <div className={cn("grid gap-4", gridCols[columns], className)}>
      {children}
    </div>
  );
}

export default SimpleStatCard;
