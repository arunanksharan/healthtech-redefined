"use client";

import * as React from "react";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from "recharts";
import { cn } from "@/lib/utils/cn";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Download, RefreshCw, Maximize2 } from "lucide-react";
import { format } from "date-fns";

// ============================================================================
// Types
// ============================================================================

export interface TimeSeriesDataPoint {
  date: Date | string;
  value: number;
  label?: string;
}

export interface TimeSeriesChartProps {
  title: string;
  description?: string;
  data: TimeSeriesDataPoint[];
  comparison?: TimeSeriesDataPoint[];
  benchmark?: number;
  benchmarkLabel?: string;
  type?: "line" | "area" | "bar";
  period?: "day" | "week" | "month" | "quarter" | "year";
  showTrend?: boolean;
  color?: string;
  comparisonColor?: string;
  height?: number;
  onPointClick?: (point: TimeSeriesDataPoint) => void;
  onPeriodChange?: (period: string) => void;
  onExport?: () => void;
  onRefresh?: () => void;
  isLoading?: boolean;
  className?: string;
}

// ============================================================================
// Time Series Chart
// ============================================================================

export function TimeSeriesChart({
  title,
  description,
  data,
  comparison,
  benchmark,
  benchmarkLabel = "Target",
  type = "line",
  period = "day",
  showTrend = true,
  color = "#6366f1",
  comparisonColor = "#94a3b8",
  height = 300,
  onPointClick,
  onPeriodChange,
  onExport,
  onRefresh,
  isLoading = false,
  className,
}: TimeSeriesChartProps) {
  const formatXAxis = (value: string | Date) => {
    const date = new Date(value);
    switch (period) {
      case "day":
        return format(date, "MMM d");
      case "week":
        return format(date, "MMM d");
      case "month":
        return format(date, "MMM");
      case "quarter":
        return `Q${Math.ceil((date.getMonth() + 1) / 3)}`;
      case "year":
        return format(date, "yyyy");
      default:
        return format(date, "MMM d");
    }
  };

  const formattedData = data.map((d, i) => ({
    ...d,
    date: typeof d.date === "string" ? d.date : d.date.toISOString(),
    formattedDate: formatXAxis(d.date),
    comparisonValue: comparison?.[i]?.value,
  }));

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-popover border rounded-lg shadow-lg p-3">
          <p className="text-sm font-medium mb-1">
            {format(new Date(label), "PPP")}
          </p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value.toLocaleString()}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const renderChart = () => {
    const commonProps = {
      data: formattedData,
      margin: { top: 10, right: 30, left: 0, bottom: 0 },
    };

    const commonAxisProps = {
      xAxis: (
        <XAxis
          dataKey="date"
          tickFormatter={formatXAxis}
          stroke="#888888"
          fontSize={12}
          tickLine={false}
          axisLine={false}
        />
      ),
      yAxis: (
        <YAxis
          stroke="#888888"
          fontSize={12}
          tickLine={false}
          axisLine={false}
          tickFormatter={(value) => value.toLocaleString()}
        />
      ),
    };

    switch (type) {
      case "area":
        return (
          <AreaChart {...commonProps}>
            <defs>
              <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.3} />
                <stop offset="95%" stopColor={color} stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorComparison" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={comparisonColor} stopOpacity={0.3} />
                <stop offset="95%" stopColor={comparisonColor} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            {commonAxisProps.xAxis}
            {commonAxisProps.yAxis}
            <Tooltip content={<CustomTooltip />} />
            {benchmark && (
              <ReferenceLine
                y={benchmark}
                stroke="#f59e0b"
                strokeDasharray="5 5"
                label={{ value: benchmarkLabel, position: "right", fill: "#f59e0b", fontSize: 12 }}
              />
            )}
            {comparison && (
              <Area
                type="monotone"
                dataKey="comparisonValue"
                name="Previous"
                stroke={comparisonColor}
                fillOpacity={1}
                fill="url(#colorComparison)"
              />
            )}
            <Area
              type="monotone"
              dataKey="value"
              name="Current"
              stroke={color}
              fillOpacity={1}
              fill="url(#colorValue)"
              onClick={(e) => onPointClick?.(e)}
            />
            <Legend />
          </AreaChart>
        );

      case "bar":
        return (
          <RechartsBarChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            {commonAxisProps.xAxis}
            {commonAxisProps.yAxis}
            <Tooltip content={<CustomTooltip />} />
            {benchmark && (
              <ReferenceLine
                y={benchmark}
                stroke="#f59e0b"
                strokeDasharray="5 5"
                label={{ value: benchmarkLabel, position: "right", fill: "#f59e0b", fontSize: 12 }}
              />
            )}
            {comparison && (
              <Bar dataKey="comparisonValue" name="Previous" fill={comparisonColor} radius={[2, 2, 0, 0]} />
            )}
            <Bar dataKey="value" name="Current" fill={color} radius={[4, 4, 0, 0]} onClick={(e) => onPointClick?.(e)} />
            <Legend />
          </RechartsBarChart>
        );

      default:
        return (
          <LineChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            {commonAxisProps.xAxis}
            {commonAxisProps.yAxis}
            <Tooltip content={<CustomTooltip />} />
            {benchmark && (
              <ReferenceLine
                y={benchmark}
                stroke="#f59e0b"
                strokeDasharray="5 5"
                label={{ value: benchmarkLabel, position: "right", fill: "#f59e0b", fontSize: 12 }}
              />
            )}
            {comparison && (
              <Line
                type="monotone"
                dataKey="comparisonValue"
                name="Previous"
                stroke={comparisonColor}
                strokeWidth={2}
                dot={false}
              />
            )}
            <Line
              type="monotone"
              dataKey="value"
              name="Current"
              stroke={color}
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6, onClick: (e: any) => onPointClick?.(e) }}
            />
            <Legend />
          </LineChart>
        );
    }
  };

  if (isLoading) {
    return <ChartSkeleton title={title} height={height} className={className} />;
  }

  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div>
          <CardTitle className="text-base font-medium">{title}</CardTitle>
          {description && (
            <CardDescription className="text-sm">{description}</CardDescription>
          )}
        </div>
        <div className="flex items-center gap-2">
          {onPeriodChange && (
            <Select defaultValue={period} onValueChange={onPeriodChange}>
              <SelectTrigger className="w-[100px] h-8">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="day">Daily</SelectItem>
                <SelectItem value="week">Weekly</SelectItem>
                <SelectItem value="month">Monthly</SelectItem>
                <SelectItem value="quarter">Quarterly</SelectItem>
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
        <div style={{ height }}>
          <ResponsiveContainer width="100%" height="100%">
            {renderChart()}
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Bar Chart Component
// ============================================================================

export interface BarChartDataPoint {
  category: string;
  value: number;
  color?: string;
  comparisonValue?: number;
}

export interface BarChartProps {
  title: string;
  description?: string;
  data: BarChartDataPoint[];
  comparison?: { category: string; value: number }[];
  orientation?: "horizontal" | "vertical";
  showLabels?: boolean;
  sortBy?: "value" | "category" | "none";
  height?: number;
  barColor?: string;
  comparisonColor?: string;
  onBarClick?: (data: BarChartDataPoint) => void;
  onExport?: () => void;
  isLoading?: boolean;
  className?: string;
}

export function BarChart({
  title,
  description,
  data,
  comparison,
  orientation = "vertical",
  showLabels = true,
  sortBy = "none",
  height = 300,
  barColor = "#6366f1",
  comparisonColor = "#94a3b8",
  onBarClick,
  onExport,
  isLoading = false,
  className,
}: BarChartProps) {
  // Sort data if needed
  let sortedData = [...data];
  if (sortBy === "value") {
    sortedData.sort((a, b) => b.value - a.value);
  } else if (sortBy === "category") {
    sortedData.sort((a, b) => a.category.localeCompare(b.category));
  }

  // Merge comparison data
  const chartData = sortedData.map((d) => ({
    ...d,
    comparisonValue: comparison?.find((c) => c.category === d.category)?.value,
  }));

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-popover border rounded-lg shadow-lg p-3">
          <p className="text-sm font-medium mb-1">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value.toLocaleString()}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  if (isLoading) {
    return <ChartSkeleton title={title} height={height} className={className} />;
  }

  const isHorizontal = orientation === "horizontal";

  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div>
          <CardTitle className="text-base font-medium">{title}</CardTitle>
          {description && (
            <CardDescription className="text-sm">{description}</CardDescription>
          )}
        </div>
        {onExport && (
          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onExport}>
            <Download className="h-4 w-4" />
          </Button>
        )}
      </CardHeader>
      <CardContent>
        <div style={{ height }}>
          <ResponsiveContainer width="100%" height="100%">
            <RechartsBarChart
              data={chartData}
              layout={isHorizontal ? "vertical" : "horizontal"}
              margin={{ top: 10, right: 30, left: isHorizontal ? 80 : 0, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              {isHorizontal ? (
                <>
                  <XAxis type="number" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis
                    dataKey="category"
                    type="category"
                    stroke="#888888"
                    fontSize={12}
                    tickLine={false}
                    axisLine={false}
                    width={80}
                  />
                </>
              ) : (
                <>
                  <XAxis dataKey="category" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                </>
              )}
              <Tooltip content={<CustomTooltip />} />
              {comparison && (
                <Bar dataKey="comparisonValue" name="Previous" fill={comparisonColor} radius={2}>
                  {chartData.map((entry, index) => (
                    <Cell key={`comparison-cell-${index}`} fill={comparisonColor} />
                  ))}
                </Bar>
              )}
              <Bar
                dataKey="value"
                name="Current"
                fill={barColor}
                radius={4}
                onClick={(data) => onBarClick?.(data)}
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color || barColor} />
                ))}
              </Bar>
              <Legend />
            </RechartsBarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Heatmap Component
// ============================================================================

export interface HeatmapDataPoint {
  x: string;
  y: string;
  value: number;
  label?: string;
}

export interface HeatmapProps {
  title: string;
  description?: string;
  data: HeatmapDataPoint[];
  xLabels: string[];
  yLabels: string[];
  colorScale?: [number, string][];
  showValues?: boolean;
  height?: number;
  onClick?: (cell: HeatmapDataPoint) => void;
  isLoading?: boolean;
  className?: string;
}

export function Heatmap({
  title,
  description,
  data,
  xLabels,
  yLabels,
  colorScale = [
    [0, "#ef4444"],     // red
    [50, "#f59e0b"],    // amber
    [75, "#22c55e"],    // green
    [100, "#10b981"],   // emerald
  ],
  showValues = true,
  height = 300,
  onClick,
  isLoading = false,
  className,
}: HeatmapProps) {
  const getColor = (value: number) => {
    // Find the two color stops that bracket this value
    for (let i = 0; i < colorScale.length - 1; i++) {
      const [threshold1, color1] = colorScale[i];
      const [threshold2, color2] = colorScale[i + 1];
      if (value >= threshold1 && value <= threshold2) {
        // Simple interpolation - just return color2 for now
        return value < (threshold1 + threshold2) / 2 ? color1 : color2;
      }
    }
    // Return last color if above all thresholds
    return colorScale[colorScale.length - 1][1];
  };

  const getValue = (x: string, y: string) => {
    const point = data.find((d) => d.x === x && d.y === y);
    return point?.value ?? null;
  };

  const cellWidth = 100 / xLabels.length;
  const cellHeight = 100 / yLabels.length;

  if (isLoading) {
    return <ChartSkeleton title={title} height={height} className={className} />;
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">{title}</CardTitle>
        {description && (
          <CardDescription className="text-sm">{description}</CardDescription>
        )}
      </CardHeader>
      <CardContent>
        <div style={{ height }} className="relative">
          {/* Y-axis labels */}
          <div className="absolute left-0 top-0 bottom-8 w-20 flex flex-col justify-around">
            {yLabels.map((label) => (
              <div key={label} className="text-xs text-muted-foreground truncate pr-2 text-right">
                {label}
              </div>
            ))}
          </div>

          {/* Heatmap grid */}
          <div className="ml-20 h-[calc(100%-32px)]">
            <div className="grid h-full" style={{ gridTemplateRows: `repeat(${yLabels.length}, 1fr)` }}>
              {yLabels.map((y) => (
                <div
                  key={y}
                  className="grid"
                  style={{ gridTemplateColumns: `repeat(${xLabels.length}, 1fr)` }}
                >
                  {xLabels.map((x) => {
                    const value = getValue(x, y);
                    const point = data.find((d) => d.x === x && d.y === y);
                    return (
                      <div
                        key={`${x}-${y}`}
                        className={cn(
                          "flex items-center justify-center border border-background/50 rounded-sm transition-transform hover:scale-105 cursor-pointer",
                          value === null && "bg-muted"
                        )}
                        style={{ backgroundColor: value !== null ? getColor(value) : undefined }}
                        onClick={() => point && onClick?.(point)}
                        title={point?.label || `${x}: ${value}%`}
                      >
                        {showValues && value !== null && (
                          <span className="text-xs font-medium text-white drop-shadow-sm">
                            {value}%
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>

          {/* X-axis labels */}
          <div className="ml-20 h-8 flex justify-around items-center">
            {xLabels.map((label) => (
              <div key={label} className="text-xs text-muted-foreground truncate text-center" style={{ width: `${cellWidth}%` }}>
                {label}
              </div>
            ))}
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center justify-center gap-4 mt-4">
          <span className="text-xs text-muted-foreground">Low</span>
          <div className="flex gap-1">
            {colorScale.map(([threshold, color], index) => (
              <div
                key={index}
                className="w-6 h-4 rounded-sm"
                style={{ backgroundColor: color }}
                title={`${threshold}%`}
              />
            ))}
          </div>
          <span className="text-xs text-muted-foreground">High</span>
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Donut Chart Component
// ============================================================================

import { PieChart, Pie } from "recharts";

export interface DonutChartDataPoint {
  name: string;
  value: number;
  color?: string;
}

export interface DonutChartProps {
  title: string;
  description?: string;
  data: DonutChartDataPoint[];
  centerLabel?: string;
  centerValue?: string | number;
  height?: number;
  colors?: string[];
  onSegmentClick?: (data: DonutChartDataPoint) => void;
  isLoading?: boolean;
  className?: string;
}

export function DonutChart({
  title,
  description,
  data,
  centerLabel,
  centerValue,
  height = 250,
  colors = ["#6366f1", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"],
  onSegmentClick,
  isLoading = false,
  className,
}: DonutChartProps) {
  const chartData = data.map((d, i) => ({
    ...d,
    fill: d.color || colors[i % colors.length],
  }));

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const item = payload[0].payload;
      return (
        <div className="bg-popover border rounded-lg shadow-lg p-3">
          <p className="text-sm font-medium">{item.name}</p>
          <p className="text-sm text-muted-foreground">
            {item.value.toLocaleString()} ({((item.value / data.reduce((a, b) => a + b.value, 0)) * 100).toFixed(1)}%)
          </p>
        </div>
      );
    }
    return null;
  };

  if (isLoading) {
    return <ChartSkeleton title={title} height={height} className={className} />;
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">{title}</CardTitle>
        {description && (
          <CardDescription className="text-sm">{description}</CardDescription>
        )}
      </CardHeader>
      <CardContent>
        <div style={{ height }} className="relative">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={2}
                dataKey="value"
                onClick={(data) => onSegmentClick?.(data)}
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} cursor="pointer" />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>

          {/* Center label */}
          {(centerLabel || centerValue) && (
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              {centerValue && (
                <span className="text-2xl font-bold">{centerValue}</span>
              )}
              {centerLabel && (
                <span className="text-xs text-muted-foreground">{centerLabel}</span>
              )}
            </div>
          )}
        </div>

        {/* Legend */}
        <div className="flex flex-wrap justify-center gap-4 mt-4">
          {chartData.map((item, index) => (
            <div key={index} className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.fill }} />
              <span className="text-xs text-muted-foreground">{item.name}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Chart Skeleton
// ============================================================================

export function ChartSkeleton({
  title,
  height = 300,
  className,
}: {
  title?: string;
  height?: number;
  className?: string;
}) {
  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        {title ? (
          <CardTitle className="text-base font-medium">{title}</CardTitle>
        ) : (
          <Skeleton className="h-5 w-32" />
        )}
      </CardHeader>
      <CardContent>
        <div style={{ height }} className="flex items-center justify-center">
          <div className="space-y-4 w-full">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-4 w-2/3" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default TimeSeriesChart;
