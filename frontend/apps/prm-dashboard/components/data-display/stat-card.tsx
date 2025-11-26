"use client";

import * as React from "react";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  ArrowRight,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Card, CardContent } from "@/components/ui/card";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: LucideIcon;
  trend?: {
    value: number;
    direction: "up" | "down" | "neutral";
    label?: string;
  };
  variant?: "default" | "outline" | "gradient";
  color?: "default" | "primary" | "success" | "warning" | "destructive";
  className?: string;
  onClick?: () => void;
}

const colorConfig = {
  default: {
    iconBg: "bg-muted",
    iconColor: "text-muted-foreground",
    gradientFrom: "from-gray-500",
    gradientTo: "to-gray-600",
  },
  primary: {
    iconBg: "bg-primary/10",
    iconColor: "text-primary",
    gradientFrom: "from-primary",
    gradientTo: "to-primary/80",
  },
  success: {
    iconBg: "bg-success/10",
    iconColor: "text-success",
    gradientFrom: "from-success",
    gradientTo: "to-success/80",
  },
  warning: {
    iconBg: "bg-warning/10",
    iconColor: "text-warning",
    gradientFrom: "from-warning",
    gradientTo: "to-warning/80",
  },
  destructive: {
    iconBg: "bg-destructive/10",
    iconColor: "text-destructive",
    gradientFrom: "from-destructive",
    gradientTo: "to-destructive/80",
  },
};

export function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  variant = "default",
  color = "default",
  className,
  onClick,
}: StatCardProps) {
  const colorClass = colorConfig[color];

  const TrendIcon =
    trend?.direction === "up"
      ? TrendingUp
      : trend?.direction === "down"
      ? TrendingDown
      : Minus;

  const trendColor =
    trend?.direction === "up"
      ? "text-success"
      : trend?.direction === "down"
      ? "text-destructive"
      : "text-muted-foreground";

  if (variant === "gradient") {
    return (
      <Card
        className={cn(
          "overflow-hidden",
          onClick && "cursor-pointer hover:shadow-lg transition-shadow",
          className
        )}
        onClick={onClick}
      >
        <div
          className={cn(
            "bg-gradient-to-br text-white p-6",
            colorClass.gradientFrom,
            colorClass.gradientTo
          )}
        >
          <div className="flex items-start justify-between">
            <div>
              <p className="text-white/80 text-sm font-medium">{title}</p>
              <p className="text-3xl font-bold mt-1">{value}</p>
              {subtitle && <p className="text-white/70 text-sm mt-1">{subtitle}</p>}
            </div>
            {Icon && (
              <div className="p-2 bg-white/20 rounded-lg">
                <Icon className="h-6 w-6" />
              </div>
            )}
          </div>

          {trend && (
            <div className="flex items-center gap-1 mt-4 text-sm">
              <TrendIcon className="h-4 w-4" />
              <span className="font-medium">
                {trend.value > 0 ? "+" : ""}
                {trend.value}%
              </span>
              {trend.label && <span className="text-white/70">{trend.label}</span>}
            </div>
          )}

          {onClick && (
            <div className="flex items-center gap-1 mt-4 text-sm text-white/80 hover:text-white transition-colors">
              <span>View details</span>
              <ArrowRight className="h-4 w-4" />
            </div>
          )}
        </div>
      </Card>
    );
  }

  return (
    <Card
      className={cn(
        variant === "outline" && "border-2",
        onClick && "cursor-pointer hover:shadow-md transition-shadow",
        className
      )}
      onClick={onClick}
    >
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <p className="text-2xl font-bold text-foreground">{value}</p>
            {subtitle && (
              <p className="text-sm text-muted-foreground">{subtitle}</p>
            )}
          </div>

          {Icon && (
            <div className={cn("p-2 rounded-lg", colorClass.iconBg)}>
              <Icon className={cn("h-5 w-5", colorClass.iconColor)} />
            </div>
          )}
        </div>

        {trend && (
          <div className="flex items-center gap-2 mt-4">
            <div
              className={cn(
                "flex items-center gap-0.5 text-sm font-medium",
                trendColor
              )}
            >
              <TrendIcon className="h-4 w-4" />
              <span>
                {trend.value > 0 ? "+" : ""}
                {trend.value}%
              </span>
            </div>
            {trend.label && (
              <span className="text-sm text-muted-foreground">{trend.label}</span>
            )}
          </div>
        )}

        {onClick && (
          <div className="flex items-center gap-1 mt-4 text-sm text-primary hover:underline">
            <span>View details</span>
            <ArrowRight className="h-4 w-4" />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Stats Grid component
interface StatsGridProps {
  stats: StatCardProps[];
  columns?: 2 | 3 | 4;
  className?: string;
}

export function StatsGrid({ stats, columns = 4, className }: StatsGridProps) {
  const gridCols = {
    2: "grid-cols-1 sm:grid-cols-2",
    3: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3",
    4: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-4",
  };

  return (
    <div className={cn("grid gap-4", gridCols[columns], className)}>
      {stats.map((stat, index) => (
        <StatCard key={index} {...stat} />
      ))}
    </div>
  );
}

export default StatCard;
