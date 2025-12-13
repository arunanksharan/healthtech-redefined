"use client";

import * as React from "react";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Activity,
  Heart,
  Thermometer,
  Droplets,
  Scale,
  Pill,
  Info,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type {
  HealthScore,
  HealthScoreComponent,
  VitalSign,
  VitalStatus,
  TrendDirection,
} from "@/lib/store/patient-profile-store";

// ============================================================================
// Types
// ============================================================================

interface HealthScoreWidgetProps {
  healthScore?: HealthScore;
  // Allow individual props as alternative to healthScore object
  score?: number;
  trend?: TrendDirection;
  label?: "Excellent" | "Good" | "Fair" | "Poor" | "Critical";
  components?: HealthScoreComponent[];
  lastUpdated?: Date;
  className?: string;
}

interface VitalsGridProps {
  vitals: VitalSign[];
  className?: string;
}

interface VitalCardProps {
  vital: VitalSign | HealthScoreComponent;
  showTrend?: boolean;
  size?: "sm" | "md" | "lg";
}

// ============================================================================
// Status Configuration
// ============================================================================

const statusConfig: Record<VitalStatus, { color: string; bgColor: string; label: string }> = {
  normal: {
    color: "text-success",
    bgColor: "bg-success/10",
    label: "Normal",
  },
  warning: {
    color: "text-warning",
    bgColor: "bg-warning/10",
    label: "Watch",
  },
  critical: {
    color: "text-destructive",
    bgColor: "bg-destructive/10",
    label: "Critical",
  },
};

const trendIcons: Record<TrendDirection, React.ElementType> = {
  up: TrendingUp,
  down: TrendingDown,
  stable: Minus,
};

const vitalIcons: Record<string, React.ElementType> = {
  BP: Heart,
  HR: Activity,
  TEMP: Thermometer,
  SpO2: Droplets,
  Weight: Scale,
  A1C: Pill,
};

const healthScoreLabels: Record<HealthScore["label"], { color: string; description: string }> = {
  Excellent: { color: "text-success", description: "All health indicators are optimal" },
  Good: { color: "text-success", description: "Most health indicators are within normal range" },
  Fair: { color: "text-warning", description: "Some health indicators need attention" },
  Poor: { color: "text-destructive", description: "Several health indicators are concerning" },
  Critical: { color: "text-destructive", description: "Immediate medical attention may be needed" },
};

// ============================================================================
// Health Score Widget Component
// ============================================================================

export function HealthScoreWidget({
  healthScore: healthScoreProp,
  score: scoreProp,
  trend: trendProp,
  label: labelProp,
  components: componentsProp,
  lastUpdated: lastUpdatedProp,
  className,
}: HealthScoreWidgetProps) {
  // Support both passing a healthScore object or individual props
  const score = healthScoreProp?.score ?? scoreProp ?? 0;
  const trend = healthScoreProp?.trend ?? trendProp ?? "stable";
  const label = healthScoreProp?.label ?? labelProp ?? "Fair";
  const components = healthScoreProp?.components ?? componentsProp ?? [];
  const lastUpdated = healthScoreProp?.lastUpdated ?? lastUpdatedProp ?? new Date();

  const TrendIcon = trendIcons[trend];
  const labelConfig = healthScoreLabels[label];

  // Calculate score ring
  const circumference = 2 * Math.PI * 45; // radius = 45
  const strokeDashoffset = circumference - (score / 100) * circumference;

  const getScoreColor = (score: number) => {
    if (score >= 80) return "stroke-success";
    if (score >= 60) return "stroke-warning";
    return "stroke-destructive";
  };

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
          <Activity className="h-4 w-4" />
          Health Score & Metrics
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Score Circle */}
          <div className="flex flex-col items-center justify-center lg:w-40">
            <div className="relative w-32 h-32">
              {/* Background circle */}
              <svg className="w-full h-full transform -rotate-90">
                <circle
                  cx="64"
                  cy="64"
                  r="45"
                  stroke="currentColor"
                  strokeWidth="10"
                  fill="none"
                  className="text-muted"
                />
                {/* Progress circle */}
                <circle
                  cx="64"
                  cy="64"
                  r="45"
                  strokeWidth="10"
                  fill="none"
                  strokeLinecap="round"
                  className={cn(getScoreColor(score), "transition-all duration-500")}
                  style={{
                    strokeDasharray: circumference,
                    strokeDashoffset: strokeDashoffset,
                  }}
                />
              </svg>
              {/* Score text */}
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-3xl font-bold text-foreground">
                  {score}
                </span>
                <span className="text-xs text-muted-foreground">/100</span>
              </div>
            </div>

            {/* Label */}
            <div className="flex items-center gap-2 mt-2">
              <span className={cn("font-semibold", labelConfig.color)}>
                {label}
              </span>
              <TrendIcon
                className={cn(
                  "h-4 w-4",
                  trend === "up" && "text-warning",
                  trend === "down" && "text-success",
                  trend === "stable" && "text-muted-foreground"
                )}
              />
            </div>

            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button className="text-xs text-muted-foreground mt-1 flex items-center gap-1 hover:text-foreground">
                    <Info className="h-3 w-3" />
                    How is this calculated?
                  </button>
                </TooltipTrigger>
                <TooltipContent className="max-w-xs">
                  <p>{labelConfig.description}</p>
                  <p className="mt-1 text-xs opacity-70">
                    Based on vitals, lab results, and care compliance.
                  </p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>

          {/* Vital Components Grid */}
          <div className="flex-1 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
            {components.map((component) => (
              <VitalCard key={component.name} vital={component} showTrend />
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Vitals Grid Component
// ============================================================================

export function VitalsGrid({ vitals, className }: VitalsGridProps) {
  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
          <Activity className="h-4 w-4" />
          Current Vitals
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {vitals.map((vital) => (
            <VitalCard key={vital.code} vital={vital} showTrend size="lg" />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Vital Card Component
// ============================================================================

function VitalCard({ vital, showTrend = false, size = "md" }: VitalCardProps) {
  const config = statusConfig[vital.status];
  const TrendIcon = trendIcons[vital.trend];
  const VitalIcon = vitalIcons[("code" in vital ? vital.code : vital.name)] || Activity;

  const sizeClasses = {
    sm: "p-2",
    md: "p-3",
    lg: "p-4",
  };

  const valueSizeClasses = {
    sm: "text-lg",
    md: "text-xl",
    lg: "text-2xl",
  };

  return (
    <div
      className={cn(
        "rounded-lg border transition-colors",
        config.bgColor,
        sizeClasses[size]
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-1.5">
          <VitalIcon className={cn("h-4 w-4", config.color)} />
          <span className="text-xs text-muted-foreground font-medium">
            {vital.name}
          </span>
        </div>
        {/* Status indicator */}
        <div className={cn("w-2 h-2 rounded-full", config.bgColor.replace("/10", ""))} />
      </div>

      {/* Value */}
      <div className="flex items-baseline gap-1">
        <span className={cn("font-bold", valueSizeClasses[size], config.color)}>
          {vital.value}
        </span>
        {"unit" in vital && vital.unit && (
          <span className="text-xs text-muted-foreground">{vital.unit}</span>
        )}
      </div>

      {/* Trend */}
      {showTrend && (
        <div className="flex items-center gap-1 mt-1">
          <TrendIcon
            className={cn(
              "h-3 w-3",
              vital.trend === "up" && vital.status !== "normal" && "text-warning",
              vital.trend === "down" && vital.status !== "normal" && "text-success",
              vital.trend === "stable" && "text-muted-foreground",
              // When normal status, trends are less concerning
              vital.status === "normal" && "text-muted-foreground"
            )}
          />
          {"trendValue" in vital && vital.trendValue && (
            <span className="text-xs text-muted-foreground">{vital.trendValue}</span>
          )}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Compact Health Score (for use in sidebars/cards)
// ============================================================================

interface CompactHealthScoreProps {
  score: number;
  label: HealthScore["label"];
  trend: TrendDirection;
  className?: string;
}

export function CompactHealthScore({ score, label, trend, className }: CompactHealthScoreProps) {
  const TrendIcon = trendIcons[trend];
  const labelConfig = healthScoreLabels[label];

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-success";
    if (score >= 60) return "text-warning";
    return "text-destructive";
  };

  return (
    <div className={cn("flex items-center gap-3", className)}>
      <div className="relative w-12 h-12">
        <svg className="w-full h-full transform -rotate-90">
          <circle
            cx="24"
            cy="24"
            r="20"
            stroke="currentColor"
            strokeWidth="4"
            fill="none"
            className="text-muted"
          />
          <circle
            cx="24"
            cy="24"
            r="20"
            strokeWidth="4"
            fill="none"
            strokeLinecap="round"
            className={cn(getScoreColor(score), "transition-all")}
            style={{
              strokeDasharray: 2 * Math.PI * 20,
              strokeDashoffset: 2 * Math.PI * 20 - (score / 100) * 2 * Math.PI * 20,
            }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-sm font-bold">{score}</span>
        </div>
      </div>
      <div>
        <div className="flex items-center gap-1">
          <span className={cn("font-medium", labelConfig.color)}>{label}</span>
          <TrendIcon className="h-3 w-3 text-muted-foreground" />
        </div>
        <span className="text-xs text-muted-foreground">Health Score</span>
      </div>
    </div>
  );
}

export default HealthScoreWidget;
