"use client";

import * as React from "react";
import {
  Phone,
  MessageCircle,
  Mail,
  MessageSquare,
  Smartphone,
  X,
  RotateCcw,
  Save,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type {
  InboxFilters,
  ChannelType,
  ItemStatus,
  SentimentLabel,
  PriorityLevel,
} from "@/lib/store/inbox-store";

interface FilterPanelProps {
  filters: InboxFilters;
  onFiltersChange: (filters: Partial<InboxFilters>) => void;
  onReset: () => void;
  onClose: () => void;
  onSaveFilter?: (name: string) => void;
  className?: string;
}

// Channel options
const channelOptions: { value: ChannelType; label: string; icon: React.ElementType }[] = [
  { value: "zoice", label: "Zoice Calls", icon: Phone },
  { value: "whatsapp", label: "WhatsApp", icon: MessageCircle },
  { value: "email", label: "Email", icon: Mail },
  { value: "sms", label: "SMS", icon: MessageSquare },
  { value: "app", label: "App", icon: Smartphone },
];

// Status options
const statusOptions: { value: ItemStatus; label: string }[] = [
  { value: "unread", label: "Unread" },
  { value: "read", label: "Read" },
  { value: "pending", label: "Pending" },
  { value: "resolved", label: "Resolved" },
  { value: "escalated", label: "Escalated" },
];

// Sentiment options
const sentimentOptions: { value: SentimentLabel; label: string; emoji: string }[] = [
  { value: "positive", label: "Positive", emoji: "😊" },
  { value: "neutral", label: "Neutral", emoji: "😐" },
  { value: "negative", label: "Negative", emoji: "😞" },
  { value: "frustrated", label: "Frustrated", emoji: "😤" },
  { value: "anxious", label: "Anxious", emoji: "😰" },
];

// Priority options
const priorityOptions: { value: PriorityLevel; label: string }[] = [
  { value: "high", label: "High" },
  { value: "medium", label: "Medium" },
  { value: "low", label: "Low" },
];

// Date range presets
const datePresets = [
  { value: "today", label: "Today" },
  { value: "yesterday", label: "Yesterday" },
  { value: "this_week", label: "This Week" },
  { value: "last_week", label: "Last Week" },
  { value: "this_month", label: "This Month" },
  { value: "custom", label: "Custom Range" },
];

// Department options (would come from API)
const departmentOptions = [
  "Cardiology",
  "Orthopedics",
  "General Medicine",
  "Pediatrics",
  "Neurology",
  "Dermatology",
  "Ophthalmology",
];

export function FilterPanel({
  filters,
  onFiltersChange,
  onReset,
  onClose,
  onSaveFilter,
  className,
}: FilterPanelProps) {
  const [saveFilterName, setSaveFilterName] = React.useState("");

  // Toggle array filter
  const toggleArrayFilter = <T extends string>(
    key: keyof InboxFilters,
    value: T,
    currentArray: T[]
  ) => {
    const newArray = currentArray.includes(value)
      ? currentArray.filter((v) => v !== value)
      : [...currentArray, value];
    onFiltersChange({ [key]: newArray } as Partial<InboxFilters>);
  };

  // Count active filters
  const activeFilterCount =
    filters.channels.length +
    filters.status.length +
    filters.sentiments.length +
    filters.priorities.length +
    filters.departments.length +
    (filters.dateRange.from ? 1 : 0) +
    (filters.unreadOnly ? 1 : 0);

  return (
    <div
      className={cn(
        "bg-card border-l border-border w-80 flex flex-col h-full",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold">Filters</h3>
          {activeFilterCount > 0 && (
            <Badge variant="secondary" className="text-xs">
              {activeFilterCount}
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="sm" onClick={onReset} className="h-8">
            <RotateCcw className="h-4 w-4 mr-1" />
            Reset
          </Button>
          <Button variant="ghost" size="sm" onClick={onClose} className="h-8 w-8 p-0">
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Unread Only Toggle */}
        <div className="flex items-center justify-between">
          <Label htmlFor="unread-only">Unread only</Label>
          <Switch
            id="unread-only"
            checked={filters.unreadOnly}
            onCheckedChange={(checked) => onFiltersChange({ unreadOnly: checked })}
          />
        </div>

        <Separator />

        {/* Channel Filter */}
        <div className="space-y-3">
          <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Channel
          </Label>
          <div className="flex flex-wrap gap-2">
            {channelOptions.map((option) => {
              const Icon = option.icon;
              const isSelected = filters.channels.includes(option.value);
              return (
                <button
                  key={option.value}
                  onClick={() =>
                    toggleArrayFilter("channels", option.value, filters.channels)
                  }
                  className={cn(
                    "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-colors",
                    isSelected
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted hover:bg-muted/80"
                  )}
                >
                  <Icon className="h-3.5 w-3.5" />
                  {option.label}
                </button>
              );
            })}
          </div>
        </div>

        <Separator />

        {/* Department Filter */}
        <div className="space-y-3">
          <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Department
          </Label>
          <div className="flex flex-wrap gap-2">
            {departmentOptions.map((dept) => {
              const isSelected = filters.departments.includes(dept);
              return (
                <button
                  key={dept}
                  onClick={() =>
                    toggleArrayFilter("departments", dept, filters.departments)
                  }
                  className={cn(
                    "px-3 py-1.5 rounded-md text-sm transition-colors",
                    isSelected
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted hover:bg-muted/80"
                  )}
                >
                  {dept}
                </button>
              );
            })}
          </div>
        </div>

        <Separator />

        {/* Date Range Filter */}
        <div className="space-y-3">
          <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Date Range
          </Label>
          <Select defaultValue="this_week">
            <SelectTrigger>
              <SelectValue placeholder="Select date range" />
            </SelectTrigger>
            <SelectContent>
              {datePresets.map((preset) => (
                <SelectItem key={preset.value} value={preset.value}>
                  {preset.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Separator />

        {/* Status Filter */}
        <div className="space-y-3">
          <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Status
          </Label>
          <div className="flex flex-wrap gap-2">
            {statusOptions.map((option) => {
              const isSelected = filters.status.includes(option.value);
              return (
                <button
                  key={option.value}
                  onClick={() =>
                    toggleArrayFilter("status", option.value, filters.status)
                  }
                  className={cn(
                    "px-3 py-1.5 rounded-md text-sm transition-colors",
                    isSelected
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted hover:bg-muted/80"
                  )}
                >
                  {option.label}
                </button>
              );
            })}
          </div>
        </div>

        <Separator />

        {/* Sentiment Filter */}
        <div className="space-y-3">
          <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Sentiment
          </Label>
          <div className="flex flex-wrap gap-2">
            {sentimentOptions.map((option) => {
              const isSelected = filters.sentiments.includes(option.value);
              return (
                <button
                  key={option.value}
                  onClick={() =>
                    toggleArrayFilter("sentiments", option.value, filters.sentiments)
                  }
                  className={cn(
                    "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-colors",
                    isSelected
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted hover:bg-muted/80"
                  )}
                >
                  <span>{option.emoji}</span>
                  {option.label}
                </button>
              );
            })}
          </div>
        </div>

        <Separator />

        {/* Priority Filter */}
        <div className="space-y-3">
          <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Priority
          </Label>
          <div className="flex flex-wrap gap-2">
            {priorityOptions.map((option) => {
              const isSelected = filters.priorities.includes(option.value);
              return (
                <button
                  key={option.value}
                  onClick={() =>
                    toggleArrayFilter("priorities", option.value, filters.priorities)
                  }
                  className={cn(
                    "px-3 py-1.5 rounded-md text-sm transition-colors",
                    isSelected
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted hover:bg-muted/80"
                  )}
                >
                  {option.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Footer - Save Filter */}
      {onSaveFilter && (
        <div className="p-4 border-t border-border">
          <div className="flex gap-2">
            <Input
              placeholder="Filter name..."
              value={saveFilterName}
              onChange={(e) => setSaveFilterName(e.target.value)}
              className="flex-1"
            />
            <Button
              variant="outline"
              onClick={() => {
                if (saveFilterName.trim()) {
                  onSaveFilter(saveFilterName);
                  setSaveFilterName("");
                }
              }}
              disabled={!saveFilterName.trim()}
            >
              <Save className="h-4 w-4 mr-1" />
              Save
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

// Quick filter pills component
interface QuickFilterPillsProps {
  filters: InboxFilters;
  onFiltersChange: (filters: Partial<InboxFilters>) => void;
  className?: string;
}

export function QuickFilterPills({
  filters,
  onFiltersChange,
  className,
}: QuickFilterPillsProps) {
  const presets = [
    { id: "my_queue", label: "My Queue", filters: {} },
    { id: "high_priority", label: "High Priority", filters: { priorities: ["high" as PriorityLevel] } },
    { id: "unread", label: "Unread", filters: { unreadOnly: true } },
    { id: "today", label: "Today", filters: {} },
  ];

  return (
    <div className={cn("flex items-center gap-2 flex-wrap", className)}>
      {presets.map((preset) => (
        <button
          key={preset.id}
          onClick={() => onFiltersChange(preset.filters)}
          className="px-3 py-1.5 rounded-full text-sm bg-muted hover:bg-muted/80 transition-colors"
        >
          {preset.label}
        </button>
      ))}
    </div>
  );
}

export default FilterPanel;
