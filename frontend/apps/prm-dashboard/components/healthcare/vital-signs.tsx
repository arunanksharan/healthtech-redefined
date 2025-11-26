"use client";

import * as React from "react";
import {
  Heart,
  Activity,
  Thermometer,
  Wind,
  Droplet,
  Scale,
  Ruler,
  TrendingUp,
  TrendingDown,
  Minus,
  Clock,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

// Vital sign types
export interface VitalSign {
  type: VitalType;
  value: number;
  unit: string;
  timestamp: Date | string;
  status: "normal" | "warning" | "critical";
  trend?: "up" | "down" | "stable";
  previousValue?: number;
}

export type VitalType =
  | "bloodPressure"
  | "heartRate"
  | "temperature"
  | "respiratoryRate"
  | "oxygenSaturation"
  | "weight"
  | "height"
  | "bmi";

// Configuration for vital signs
const vitalConfig: Record<
  VitalType,
  {
    label: string;
    icon: React.ElementType;
    normalRange?: [number, number];
    warningRange?: [number, number];
    unit: string;
  }
> = {
  bloodPressure: {
    label: "Blood Pressure",
    icon: Activity,
    unit: "mmHg",
  },
  heartRate: {
    label: "Heart Rate",
    icon: Heart,
    normalRange: [60, 100],
    warningRange: [50, 110],
    unit: "bpm",
  },
  temperature: {
    label: "Temperature",
    icon: Thermometer,
    normalRange: [97.8, 99.1],
    warningRange: [97, 100.4],
    unit: "°F",
  },
  respiratoryRate: {
    label: "Resp. Rate",
    icon: Wind,
    normalRange: [12, 20],
    warningRange: [10, 25],
    unit: "/min",
  },
  oxygenSaturation: {
    label: "SpO2",
    icon: Droplet,
    normalRange: [95, 100],
    warningRange: [90, 100],
    unit: "%",
  },
  weight: {
    label: "Weight",
    icon: Scale,
    unit: "kg",
  },
  height: {
    label: "Height",
    icon: Ruler,
    unit: "cm",
  },
  bmi: {
    label: "BMI",
    icon: Scale,
    normalRange: [18.5, 24.9],
    warningRange: [17, 29.9],
    unit: "kg/m²",
  },
};

const statusConfig = {
  normal: {
    bgClass: "bg-vital-normal/10",
    textClass: "text-vital-normal",
    borderClass: "border-vital-normal/20",
    label: "Normal",
  },
  warning: {
    bgClass: "bg-vital-warning/10",
    textClass: "text-vital-warning",
    borderClass: "border-vital-warning/20",
    label: "Warning",
  },
  critical: {
    bgClass: "bg-vital-critical/10",
    textClass: "text-vital-critical",
    borderClass: "border-vital-critical/20",
    label: "Critical",
  },
};

// Individual vital sign card
interface VitalSignCardProps {
  vital: VitalSign;
  compact?: boolean;
  className?: string;
}

function formatTimestamp(timestamp: Date | string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

export function VitalSignCard({ vital, compact = false, className }: VitalSignCardProps) {
  const config = vitalConfig[vital.type];
  const status = statusConfig[vital.status];
  const Icon = config.icon;

  const TrendIcon = vital.trend === "up" ? TrendingUp : vital.trend === "down" ? TrendingDown : Minus;

  if (compact) {
    return (
      <div
        className={cn(
          "flex items-center justify-between p-3 rounded-lg border",
          status.bgClass,
          status.borderClass,
          className
        )}
      >
        <div className="flex items-center gap-2">
          <Icon className={cn("h-4 w-4", status.textClass)} />
          <span className="text-sm text-muted-foreground">{config.label}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className={cn("font-semibold", status.textClass)}>
            {vital.value}
            <span className="text-xs ml-0.5">{vital.unit}</span>
          </span>
          {vital.trend && (
            <TrendIcon className={cn("h-3.5 w-3.5", status.textClass)} />
          )}
        </div>
      </div>
    );
  }

  return (
    <Card className={cn("border", status.borderClass, className)}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-2">
          <div className={cn("p-2 rounded-lg", status.bgClass)}>
            <Icon className={cn("h-5 w-5", status.textClass)} />
          </div>
          <Badge
            variant="outline"
            className={cn(
              "text-xs",
              status.bgClass,
              status.textClass,
              status.borderClass
            )}
          >
            {status.label}
          </Badge>
        </div>

        <div className="space-y-1">
          <p className="text-sm text-muted-foreground">{config.label}</p>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-bold text-foreground">
              {vital.value}
            </span>
            <span className="text-sm text-muted-foreground">{vital.unit}</span>
            {vital.trend && (
              <TrendIcon
                className={cn(
                  "h-4 w-4 ml-1",
                  vital.trend === "up"
                    ? "text-vital-warning"
                    : vital.trend === "down"
                    ? "text-vital-normal"
                    : "text-muted-foreground"
                )}
              />
            )}
          </div>
        </div>

        <div className="flex items-center gap-1 mt-2 text-xs text-muted-foreground">
          <Clock className="h-3 w-3" />
          {formatTimestamp(vital.timestamp)}
        </div>
      </CardContent>
    </Card>
  );
}

// Vital signs grid component
interface VitalSignsGridProps {
  vitals: VitalSign[];
  className?: string;
  compact?: boolean;
  columns?: 2 | 3 | 4;
}

export function VitalSignsGrid({
  vitals,
  className,
  compact = false,
  columns = 4,
}: VitalSignsGridProps) {
  const gridCols = {
    2: "grid-cols-2",
    3: "grid-cols-2 md:grid-cols-3",
    4: "grid-cols-2 md:grid-cols-4",
  };

  return (
    <div className={cn("grid gap-4", gridCols[columns], className)}>
      {vitals.map((vital, index) => (
        <VitalSignCard key={index} vital={vital} compact={compact} />
      ))}
    </div>
  );
}

// Vital signs summary card (all vitals in one card)
interface VitalSignsSummaryProps {
  vitals: VitalSign[];
  title?: string;
  className?: string;
  showTimestamp?: boolean;
}

export function VitalSignsSummary({
  vitals,
  title = "Vital Signs",
  className,
  showTimestamp = true,
}: VitalSignsSummaryProps) {
  const latestTimestamp =
    vitals.length > 0
      ? vitals.reduce((latest, v) => {
          const vTime = new Date(v.timestamp).getTime();
          return vTime > latest ? vTime : latest;
        }, 0)
      : null;

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">{title}</CardTitle>
          {showTimestamp && latestTimestamp && (
            <span className="text-xs text-muted-foreground">
              Last: {formatTimestamp(new Date(latestTimestamp))}
            </span>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {vitals.map((vital, index) => {
            const config = vitalConfig[vital.type];
            const status = statusConfig[vital.status];
            const Icon = config.icon;

            return (
              <div
                key={index}
                className={cn(
                  "text-center p-3 rounded-lg border",
                  status.bgClass,
                  status.borderClass
                )}
              >
                <Icon className={cn("h-5 w-5 mx-auto mb-1", status.textClass)} />
                <div className={cn("text-xl font-bold", status.textClass)}>
                  {vital.value}
                </div>
                <div className="text-xs text-muted-foreground">
                  {vital.unit}
                </div>
                <div className="text-xs text-muted-foreground mt-0.5">
                  {config.label}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

export default VitalSignsGrid;
