"use client";

import * as React from "react";
import {
  GripVertical,
  Plus,
  Settings,
  Save,
  RotateCcw,
  Maximize2,
  Minimize2,
  X,
  ChevronDown,
  Check,
  Layout,
  BarChart3,
  LineChart,
  PieChart,
  AlertTriangle,
  Users,
  DollarSign,
  Calendar,
  Clock,
  Activity,
  Target,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { DashboardWidget, DashboardLayout as DashboardLayoutType } from "@/lib/store/analytics-store";

// ============================================================================
// Types
// ============================================================================

export type WidgetSize = "1x1" | "2x1" | "1x2" | "2x2" | "3x1" | "3x2";

export interface DashboardWidgetConfig {
  id: string;
  type: string;
  title: string;
  size: WidgetSize;
  position: { row: number; col: number };
  config?: Record<string, any>;
}

export interface AvailableWidget {
  id: string;
  type: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  defaultSize: WidgetSize;
  category: "metrics" | "charts" | "goals" | "alerts" | "lists";
}

// ============================================================================
// Widget Wrapper Component
// ============================================================================

interface DashboardWidgetWrapperProps {
  widget: DashboardWidgetConfig;
  isEditing?: boolean;
  onRemove?: () => void;
  onResize?: (size: WidgetSize) => void;
  onExpand?: () => void;
  children: React.ReactNode;
  className?: string;
}

export function DashboardWidgetWrapper({
  widget,
  isEditing = false,
  onRemove,
  onResize,
  onExpand,
  children,
  className,
}: DashboardWidgetWrapperProps) {
  const [isExpanded, setIsExpanded] = React.useState(false);

  const sizeClasses: Record<WidgetSize, string> = {
    "1x1": "col-span-1 row-span-1",
    "2x1": "col-span-2 row-span-1",
    "1x2": "col-span-1 row-span-2",
    "2x2": "col-span-2 row-span-2",
    "3x1": "col-span-3 row-span-1",
    "3x2": "col-span-3 row-span-2",
  };

  const handleExpand = () => {
    setIsExpanded(!isExpanded);
    onExpand?.();
  };

  return (
    <div
      className={cn(
        "relative group transition-all",
        sizeClasses[widget.size],
        isEditing && "ring-2 ring-dashed ring-primary/30 rounded-lg",
        className
      )}
    >
      {/* Edit mode overlay */}
      {isEditing && (
        <div className="absolute inset-0 z-10 bg-background/80 rounded-lg flex flex-col items-center justify-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <div className="flex items-center gap-1">
            <GripVertical className="h-5 w-5 text-muted-foreground cursor-move" />
            <span className="text-sm font-medium">{widget.title}</span>
          </div>
          <div className="flex items-center gap-2">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  Resize <ChevronDown className="h-3 w-3 ml-1" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => onResize?.("1x1")}>
                  Small (1x1) {widget.size === "1x1" && <Check className="h-4 w-4 ml-2" />}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onResize?.("2x1")}>
                  Wide (2x1) {widget.size === "2x1" && <Check className="h-4 w-4 ml-2" />}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onResize?.("1x2")}>
                  Tall (1x2) {widget.size === "1x2" && <Check className="h-4 w-4 ml-2" />}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onResize?.("2x2")}>
                  Large (2x2) {widget.size === "2x2" && <Check className="h-4 w-4 ml-2" />}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onResize?.("3x1")}>
                  Extra Wide (3x1) {widget.size === "3x1" && <Check className="h-4 w-4 ml-2" />}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            <Button variant="destructive" size="sm" onClick={onRemove}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Widget content */}
      <div className="h-full">
        {children}
      </div>

      {/* Expand button (only in view mode) */}
      {!isEditing && (
        <Button
          variant="ghost"
          size="icon"
          className="absolute top-2 right-2 h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity z-10"
          onClick={handleExpand}
        >
          {isExpanded ? <Minimize2 className="h-3 w-3" /> : <Maximize2 className="h-3 w-3" />}
        </Button>
      )}
    </div>
  );
}

// ============================================================================
// Bento Grid Layout
// ============================================================================

interface BentoGridLayoutProps {
  widgets: DashboardWidgetConfig[];
  renderWidget: (widget: DashboardWidgetConfig) => React.ReactNode;
  isEditing?: boolean;
  onWidgetRemove?: (widgetId: string) => void;
  onWidgetResize?: (widgetId: string, size: WidgetSize) => void;
  columns?: number;
  gap?: number;
  className?: string;
}

export function BentoGridLayout({
  widgets,
  renderWidget,
  isEditing = false,
  onWidgetRemove,
  onWidgetResize,
  columns = 4,
  gap = 4,
  className,
}: BentoGridLayoutProps) {
  const gridCols = {
    3: "grid-cols-1 md:grid-cols-2 lg:grid-cols-3",
    4: "grid-cols-1 md:grid-cols-2 lg:grid-cols-4",
    5: "grid-cols-1 md:grid-cols-2 lg:grid-cols-5",
    6: "grid-cols-1 md:grid-cols-3 lg:grid-cols-6",
  };

  return (
    <div
      className={cn(
        "grid auto-rows-[minmax(140px,auto)]",
        gridCols[columns as keyof typeof gridCols] || gridCols[4],
        `gap-${gap}`,
        className
      )}
      style={{ gap: `${gap * 4}px` }}
    >
      {widgets.map((widget) => (
        <DashboardWidgetWrapper
          key={widget.id}
          widget={widget}
          isEditing={isEditing}
          onRemove={() => onWidgetRemove?.(widget.id)}
          onResize={(size) => onWidgetResize?.(widget.id, size)}
        >
          {renderWidget(widget)}
        </DashboardWidgetWrapper>
      ))}
    </div>
  );
}

// ============================================================================
// Dashboard Header
// ============================================================================

interface DashboardHeaderProps {
  title: string;
  subtitle?: string;
  greeting?: string;
  date?: string;
  isEditing?: boolean;
  onEditToggle?: () => void;
  onSave?: () => void;
  onReset?: () => void;
  onAddWidget?: () => void;
  onSettings?: () => void;
  className?: string;
}

export function DashboardHeader({
  title,
  subtitle,
  greeting,
  date,
  isEditing = false,
  onEditToggle,
  onSave,
  onReset,
  onAddWidget,
  onSettings,
  className,
}: DashboardHeaderProps) {
  return (
    <div className={cn("flex items-start justify-between", className)}>
      <div>
        {greeting && <p className="text-muted-foreground">{greeting}</p>}
        <h1 className="text-2xl font-bold">{title}</h1>
        {subtitle && <p className="text-sm text-muted-foreground mt-1">{subtitle}</p>}
        {date && (
          <p className="text-sm text-muted-foreground flex items-center gap-1 mt-1">
            <Calendar className="h-4 w-4" />
            {date}
          </p>
        )}
      </div>
      <div className="flex items-center gap-2">
        {isEditing ? (
          <>
            <Button variant="outline" size="sm" onClick={onReset}>
              <RotateCcw className="h-4 w-4 mr-2" />
              Reset
            </Button>
            <Button variant="outline" size="sm" onClick={onAddWidget}>
              <Plus className="h-4 w-4 mr-2" />
              Add Widget
            </Button>
            <Button size="sm" onClick={onSave}>
              <Save className="h-4 w-4 mr-2" />
              Save Layout
            </Button>
          </>
        ) : (
          <>
            {onSettings && (
              <Button variant="ghost" size="icon" onClick={onSettings}>
                <Settings className="h-4 w-4" />
              </Button>
            )}
            {onEditToggle && (
              <Button variant="outline" size="sm" onClick={onEditToggle}>
                <Layout className="h-4 w-4 mr-2" />
                Customize
              </Button>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Widget Library Dialog
// ============================================================================

const AVAILABLE_WIDGETS: AvailableWidget[] = [
  // Metrics
  { id: "appointments_today", type: "stat_simple", name: "Today's Appointments", description: "Current day's appointment count", icon: <Calendar className="h-5 w-5" />, defaultSize: "1x1", category: "metrics" },
  { id: "revenue_mtd", type: "stat_progress", name: "Revenue (MTD)", description: "Month-to-date revenue vs target", icon: <DollarSign className="h-5 w-5" />, defaultSize: "1x1", category: "metrics" },
  { id: "satisfaction", type: "stat_trend", name: "Patient Satisfaction", description: "Average satisfaction score with trend", icon: <Activity className="h-5 w-5" />, defaultSize: "1x1", category: "metrics" },
  { id: "wait_time", type: "stat_simple", name: "Avg Wait Time", description: "Average patient wait time", icon: <Clock className="h-5 w-5" />, defaultSize: "1x1", category: "metrics" },
  { id: "no_show", type: "stat_comparison", name: "No-Show Rate", description: "No-show rate vs benchmark", icon: <Users className="h-5 w-5" />, defaultSize: "1x1", category: "metrics" },

  // Charts
  { id: "appointment_volume", type: "chart_timeseries", name: "Appointment Volume", description: "Appointment trends over time", icon: <LineChart className="h-5 w-5" />, defaultSize: "3x1", category: "charts" },
  { id: "revenue_by_dept", type: "chart_bar", name: "Revenue by Department", description: "Revenue breakdown by department", icon: <BarChart3 className="h-5 w-5" />, defaultSize: "2x1", category: "charts" },
  { id: "patient_distribution", type: "chart_donut", name: "Patient Distribution", description: "Patient distribution by type", icon: <PieChart className="h-5 w-5" />, defaultSize: "1x1", category: "charts" },

  // Goals
  { id: "monthly_targets", type: "goals", name: "Monthly Targets", description: "Track monthly KPI targets", icon: <Target className="h-5 w-5" />, defaultSize: "2x1", category: "goals" },

  // Alerts
  { id: "proactive_alerts", type: "alerts", name: "Proactive Alerts", description: "AI-powered alerts and recommendations", icon: <AlertTriangle className="h-5 w-5" />, defaultSize: "2x2", category: "alerts" },
  { id: "no_show_risk", type: "alert_action", name: "No-Show Risk Alert", description: "Patients at risk of no-show", icon: <AlertTriangle className="h-5 w-5" />, defaultSize: "1x1", category: "alerts" },

  // Lists
  { id: "top_performers", type: "list", name: "Top Performers", description: "Best performing practitioners", icon: <Users className="h-5 w-5" />, defaultSize: "1x2", category: "lists" },
  { id: "recent_feedback", type: "list", name: "Recent Feedback", description: "Latest patient feedback", icon: <Activity className="h-5 w-5" />, defaultSize: "2x1", category: "lists" },
];

interface WidgetLibraryDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onAddWidget: (widget: AvailableWidget) => void;
  existingWidgetIds: string[];
}

export function WidgetLibraryDialog({
  isOpen,
  onClose,
  onAddWidget,
  existingWidgetIds,
}: WidgetLibraryDialogProps) {
  const [selectedCategory, setSelectedCategory] = React.useState<string>("all");

  const categories = ["all", "metrics", "charts", "goals", "alerts", "lists"];

  const filteredWidgets = selectedCategory === "all"
    ? AVAILABLE_WIDGETS
    : AVAILABLE_WIDGETS.filter((w) => w.category === selectedCategory);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Add Widget</DialogTitle>
          <DialogDescription>
            Choose a widget to add to your dashboard
          </DialogDescription>
        </DialogHeader>

        {/* Category filters */}
        <div className="flex items-center gap-2 overflow-x-auto py-2">
          {categories.map((category) => (
            <Button
              key={category}
              variant={selectedCategory === category ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedCategory(category)}
              className="capitalize"
            >
              {category}
            </Button>
          ))}
        </div>

        {/* Widget grid */}
        <ScrollArea className="h-[400px]">
          <div className="grid grid-cols-2 gap-3 pr-4">
            {filteredWidgets.map((widget) => {
              const isAdded = existingWidgetIds.includes(widget.id);
              return (
                <div
                  key={widget.id}
                  className={cn(
                    "flex items-start gap-3 p-3 rounded-lg border bg-card transition-colors",
                    isAdded ? "opacity-50 cursor-not-allowed" : "hover:bg-accent/50 cursor-pointer"
                  )}
                  onClick={() => !isAdded && onAddWidget(widget)}
                >
                  <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                    {widget.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-sm">{widget.name}</p>
                      {isAdded && (
                        <Badge variant="secondary" className="text-xs">Added</Badge>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground mt-0.5">{widget.description}</p>
                    <Badge variant="outline" className="text-xs mt-1 capitalize">
                      {widget.category}
                    </Badge>
                  </div>
                </div>
              );
            })}
          </div>
        </ScrollArea>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ============================================================================
// Dashboard Presets
// ============================================================================

export const DASHBOARD_PRESETS: Record<string, DashboardWidgetConfig[]> = {
  executive: [
    { id: "1", type: "stat_simple", title: "Today's Appointments", size: "1x1", position: { row: 0, col: 0 } },
    { id: "2", type: "stat_progress", title: "Revenue (MTD)", size: "1x1", position: { row: 0, col: 1 } },
    { id: "3", type: "stat_trend", title: "Patient Satisfaction", size: "1x1", position: { row: 0, col: 2 } },
    { id: "4", type: "stat_comparison", title: "No-Show Rate", size: "1x1", position: { row: 0, col: 3 } },
    { id: "5", type: "chart_timeseries", title: "Appointment Volume", size: "3x1", position: { row: 1, col: 0 } },
    { id: "6", type: "alerts", title: "AI Insights", size: "1x2", position: { row: 1, col: 3 } },
    { id: "7", type: "chart_bar", title: "Revenue by Department", size: "2x1", position: { row: 2, col: 0 } },
    { id: "8", type: "list", title: "Recent Feedback", size: "1x1", position: { row: 2, col: 2 } },
  ],
  operations: [
    { id: "1", type: "stat_simple", title: "Today's Appointments", size: "1x1", position: { row: 0, col: 0 } },
    { id: "2", type: "stat_simple", title: "Avg Wait Time", size: "1x1", position: { row: 0, col: 1 } },
    { id: "3", type: "stat_comparison", title: "No-Show Rate", size: "1x1", position: { row: 0, col: 2 } },
    { id: "4", type: "alert_action", title: "No-Show Risk", size: "1x1", position: { row: 0, col: 3 } },
    { id: "5", type: "alerts", title: "Proactive Alerts", size: "2x2", position: { row: 1, col: 0 } },
    { id: "6", type: "chart_timeseries", title: "Appointment Volume", size: "2x1", position: { row: 1, col: 2 } },
    { id: "7", type: "list", title: "Top Performers", size: "1x2", position: { row: 2, col: 2 } },
    { id: "8", type: "chart_bar", title: "Wait Time by Dept", size: "1x1", position: { row: 2, col: 3 } },
  ],
  clinical: [
    { id: "1", type: "stat_simple", title: "Patients Seen", size: "1x1", position: { row: 0, col: 0 } },
    { id: "2", type: "stat_trend", title: "Quality Score", size: "1x1", position: { row: 0, col: 1 } },
    { id: "3", type: "stat_progress", title: "Care Gap Closure", size: "1x1", position: { row: 0, col: 2 } },
    { id: "4", type: "stat_simple", title: "High Risk Patients", size: "1x1", position: { row: 0, col: 3 } },
    { id: "5", type: "chart_timeseries", title: "Clinical Quality Trends", size: "3x1", position: { row: 1, col: 0 } },
    { id: "6", type: "alerts", title: "AI Insights", size: "1x2", position: { row: 1, col: 3 } },
    { id: "7", type: "list", title: "Care Gaps", size: "2x1", position: { row: 2, col: 0 } },
    { id: "8", type: "chart_donut", title: "Patient Distribution", size: "1x1", position: { row: 2, col: 2 } },
  ],
};

// ============================================================================
// Dashboard Selector
// ============================================================================

interface DashboardSelectorProps {
  currentPreset: string;
  onPresetChange: (preset: string) => void;
  presets?: { id: string; name: string }[];
  className?: string;
}

export function DashboardSelector({
  currentPreset,
  onPresetChange,
  presets = [
    { id: "executive", name: "Executive Dashboard" },
    { id: "operations", name: "Operations Dashboard" },
    { id: "clinical", name: "Clinical Quality Dashboard" },
    { id: "financial", name: "Financial Dashboard" },
    { id: "experience", name: "Patient Experience Dashboard" },
  ],
  className,
}: DashboardSelectorProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" className={className}>
          {presets.find((p) => p.id === currentPreset)?.name || "Select Dashboard"}
          <ChevronDown className="h-4 w-4 ml-2" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start">
        <DropdownMenuLabel>Dashboard Views</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {presets.map((preset) => (
          <DropdownMenuItem
            key={preset.id}
            onClick={() => onPresetChange(preset.id)}
          >
            {preset.name}
            {currentPreset === preset.id && <Check className="h-4 w-4 ml-2" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export default BentoGridLayout;
