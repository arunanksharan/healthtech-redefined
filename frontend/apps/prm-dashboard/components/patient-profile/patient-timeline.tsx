"use client";

import * as React from "react";
import {
  Calendar,
  Clock,
  Phone,
  MessageCircle,
  Mail,
  FileText,
  Activity,
  Pill,
  Stethoscope,
  ChevronDown,
  ChevronUp,
  Play,
  ExternalLink,
  Filter,
  MoreHorizontal,
  Loader2,
  Package,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type {
  TimelineEvent,
  Episode,
  EventType,
  ChannelType,
} from "@/lib/store/patient-profile-store";

// ============================================================================
// Types
// ============================================================================

interface PatientTimelineProps {
  events: TimelineEvent[];
  episodes?: Episode[];
  isLoading?: boolean;
  hasMore?: boolean;
  onLoadMore?: () => void;
  onEventAction?: (eventId: string, actionType: string) => void;
  onEventClick?: (event: TimelineEvent) => void;
  groupBy?: "day" | "episode" | "type";
  viewMode?: "story" | "list";
  className?: string;
}

interface TimelineEventCardProps {
  event: TimelineEvent;
  isFirst?: boolean;
  isLast?: boolean;
  onAction?: (actionType: string) => void;
}

interface EpisodeCardProps {
  episode: Episode;
  isExpanded: boolean;
  onToggle: () => void;
  onEventAction?: (eventId: string, actionType: string) => void;
}

// ============================================================================
// Event Type Configuration
// ============================================================================

const eventTypeConfig: Record<EventType, { icon: React.ElementType; color: string; bgColor: string }> = {
  appointment: {
    icon: Calendar,
    color: "text-primary",
    bgColor: "bg-primary/10",
  },
  encounter: {
    icon: Stethoscope,
    color: "text-purple-600",
    bgColor: "bg-purple-500/10",
  },
  call: {
    icon: Phone,
    color: "text-blue-600",
    bgColor: "bg-blue-500/10",
  },
  message: {
    icon: MessageCircle,
    color: "text-green-600",
    bgColor: "bg-green-500/10",
  },
  lab: {
    icon: Activity,
    color: "text-cyan-600",
    bgColor: "bg-cyan-500/10",
  },
  prescription: {
    icon: Pill,
    color: "text-red-600",
    bgColor: "bg-red-500/10",
  },
  document: {
    icon: FileText,
    color: "text-slate-600",
    bgColor: "bg-slate-500/10",
  },
  referral: {
    icon: ExternalLink,
    color: "text-indigo-600",
    bgColor: "bg-indigo-500/10",
  },
};

const channelConfig: Record<ChannelType, { label: string; icon: React.ElementType }> = {
  fhir: { label: "EHR", icon: FileText },
  zoice: { label: "Zoice", icon: Phone },
  whatsapp: { label: "WhatsApp", icon: MessageCircle },
  email: { label: "Email", icon: Mail },
  sms: { label: "SMS", icon: MessageCircle },
  app: { label: "App", icon: Activity },
};

// ============================================================================
// Helper Functions
// ============================================================================

function formatDate(date: Date): string {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const eventDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const diffDays = Math.floor((today.getTime() - eventDate.getTime()) / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return "TODAY";
  if (diffDays === 1) return "YESTERDAY";

  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).toUpperCase();
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}m ${secs}s`;
}

function groupEventsByDate(events: TimelineEvent[]): Map<string, TimelineEvent[]> {
  const grouped = new Map<string, TimelineEvent[]>();

  events.forEach((event) => {
    const dateKey = formatDate(event.timestamp);
    if (!grouped.has(dateKey)) {
      grouped.set(dateKey, []);
    }
    grouped.get(dateKey)!.push(event);
  });

  return grouped;
}

// ============================================================================
// Patient Timeline Component
// ============================================================================

export function PatientTimeline({
  events,
  episodes,
  isLoading = false,
  hasMore = false,
  onLoadMore,
  onEventAction,
  viewMode = "story",
  className,
}: PatientTimelineProps) {
  const [selectedFilter, setSelectedFilter] = React.useState<string>("all");
  const [expandedEpisodes, setExpandedEpisodes] = React.useState<Set<string>>(new Set());

  const toggleEpisode = (episodeId: string) => {
    setExpandedEpisodes((prev) => {
      const next = new Set(prev);
      if (next.has(episodeId)) {
        next.delete(episodeId);
      } else {
        next.add(episodeId);
      }
      return next;
    });
  };

  // Filter events
  const filteredEvents = React.useMemo(() => {
    if (selectedFilter === "all") return events;
    return events.filter((e) => e.type === selectedFilter || e.channel === selectedFilter);
  }, [events, selectedFilter]);

  // Group events by date
  const groupedEvents = React.useMemo(() => {
    return groupEventsByDate(filteredEvents);
  }, [filteredEvents]);

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Patient Timeline
          </CardTitle>

          <div className="flex items-center gap-2">
            {/* Filter */}
            <Select value={selectedFilter} onValueChange={setSelectedFilter}>
              <SelectTrigger className="w-32 h-8 text-xs">
                <Filter className="h-3 w-3 mr-1" />
                <SelectValue placeholder="Filter" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Events</SelectItem>
                <SelectItem value="encounter">Visits</SelectItem>
                <SelectItem value="call">Calls</SelectItem>
                <SelectItem value="message">Messages</SelectItem>
                <SelectItem value="lab">Labs</SelectItem>
                <SelectItem value="prescription">Prescriptions</SelectItem>
              </SelectContent>
            </Select>

            {/* View Mode */}
            <Select defaultValue={viewMode}>
              <SelectTrigger className="w-28 h-8 text-xs">
                <SelectValue placeholder="View" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="story">Story</SelectItem>
                <SelectItem value="list">List</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Episodes (if available) */}
        {episodes && episodes.length > 0 && (
          <div className="space-y-3 pb-4 border-b">
            <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Episodes
            </h4>
            {episodes.map((episode) => (
              <EpisodeCard
                key={episode.id}
                episode={episode}
                isExpanded={expandedEpisodes.has(episode.id)}
                onToggle={() => toggleEpisode(episode.id)}
                onEventAction={onEventAction}
              />
            ))}
          </div>
        )}

        {/* Timeline Events grouped by date */}
        <div className="relative">
          {/* Vertical line */}
          <div className="absolute left-4 top-0 bottom-0 w-px bg-border" />

          {Array.from(groupedEvents.entries()).map(([dateKey, dateEvents], groupIndex) => (
            <div key={dateKey} className="mb-6 last:mb-0">
              {/* Date header */}
              <div className="flex items-center gap-3 mb-4">
                <div className="w-9 h-9 rounded-full bg-muted flex items-center justify-center z-10">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                </div>
                <h4 className="text-sm font-semibold text-foreground">{dateKey}</h4>
              </div>

              {/* Events for this date */}
              <div className="space-y-3 ml-4 pl-8">
                {dateEvents.map((event, eventIndex) => (
                  <TimelineEventCard
                    key={event.id}
                    event={event}
                    isFirst={eventIndex === 0}
                    isLast={eventIndex === dateEvents.length - 1}
                    onAction={(actionType) => onEventAction?.(event.id, actionType)}
                  />
                ))}
              </div>
            </div>
          ))}

          {/* Empty state */}
          {filteredEvents.length === 0 && !isLoading && (
            <div className="text-center py-12 text-muted-foreground">
              <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No timeline events found</p>
            </div>
          )}

          {/* Loading state */}
          {isLoading && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
            </div>
          )}
        </div>

        {/* Load More */}
        {hasMore && !isLoading && (
          <div className="text-center pt-4 border-t">
            <Button variant="outline" onClick={onLoadMore}>
              Load More History...
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Timeline Event Card Component
// ============================================================================

function TimelineEventCard({
  event,
  isFirst,
  isLast,
  onAction,
}: TimelineEventCardProps) {
  const config = eventTypeConfig[event.type];
  const channelInfo = channelConfig[event.channel];
  const EventIcon = config.icon;
  const ChannelIcon = channelInfo.icon;

  return (
    <div className="relative">
      {/* Event Card */}
      <div className="bg-card border rounded-lg p-4 hover:shadow-sm transition-shadow">
        {/* Header */}
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex items-center gap-2">
            <div className={cn("p-1.5 rounded-md", config.bgColor)}>
              <EventIcon className={cn("h-4 w-4", config.color)} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h5 className="font-medium text-foreground text-sm">{event.title}</h5>
                {event.sentiment && (
                  <span className="text-sm">{event.sentiment.emoji}</span>
                )}
              </div>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <ChannelIcon className="h-3 w-3" />
                <span>{channelInfo.label}</span>
                <span>•</span>
                <span>{formatTime(event.timestamp)}</span>
                {typeof event.metadata?.duration === "number" && (
                  <>
                    <span>•</span>
                    <span>{formatDuration(event.metadata.duration)}</span>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Actions menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onAction?.("view_details")}>
                View Details
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onAction?.("add_note")}>
                Add Note
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onAction?.("share")}>
                Share
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Summary */}
        <p className="text-sm text-muted-foreground mb-3">{event.summary}</p>

        {/* Content (expanded) */}
        {event.content && (
          <div className="text-sm bg-muted/50 rounded p-3 mb-3 whitespace-pre-wrap">
            {event.content}
          </div>
        )}

        {/* Actions */}
        {event.actions && event.actions.length > 0 && (
          <div className="flex items-center gap-2 pt-2 border-t">
            {event.actions.map((action) => (
              <Button
                key={action.id}
                variant={action.isPrimary ? "default" : "outline"}
                size="sm"
                className="h-7 text-xs"
                onClick={() => onAction?.(action.type)}
              >
                {action.type === "play" && <Play className="h-3 w-3 mr-1" />}
                {action.label}
              </Button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Episode Card Component
// ============================================================================

function EpisodeCard({
  episode,
  isExpanded,
  onToggle,
  onEventAction,
}: EpisodeCardProps) {
  return (
    <Collapsible open={isExpanded} onOpenChange={onToggle}>
      <div className="border rounded-lg overflow-hidden">
        <CollapsibleTrigger asChild>
          <button className="w-full flex items-center justify-between p-4 hover:bg-muted/50 transition-colors text-left">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <Package className="h-5 w-5 text-primary" />
              </div>
              <div>
                <h4 className="font-medium text-foreground">{episode.title}</h4>
                <p className="text-xs text-muted-foreground">
                  {formatDate(episode.startDate)}
                  {episode.endDate && ` - ${formatDate(episode.endDate)}`}
                  {" • "}
                  {episode.events.length} events
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {episode.outcome && (
                <Badge variant="outline" className="text-xs">
                  {episode.outcome}
                </Badge>
              )}
              {isExpanded ? (
                <ChevronUp className="h-4 w-4 text-muted-foreground" />
              ) : (
                <ChevronDown className="h-4 w-4 text-muted-foreground" />
              )}
            </div>
          </button>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="px-4 pb-4 pt-2 border-t space-y-3">
            {/* Episode details */}
            <div className="text-sm text-muted-foreground">
              <span className="font-medium">Triggered by:</span> {episode.trigger}
            </div>

            {/* Episode events */}
            <div className="space-y-2 pl-4 border-l-2 border-primary/20">
              {episode.events.map((event) => (
                <div
                  key={event.id}
                  className="flex items-center justify-between py-2 px-3 bg-muted/30 rounded"
                >
                  <div className="flex items-center gap-2">
                    {React.createElement(eventTypeConfig[event.type].icon, {
                      className: cn("h-4 w-4", eventTypeConfig[event.type].color),
                    })}
                    <span className="text-sm">{event.title}</span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {formatTime(event.timestamp)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
}

// ============================================================================
// Timeline Loading Skeleton
// ============================================================================

export function TimelineSkeleton({ className }: { className?: string }) {
  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
          <Clock className="h-4 w-4" />
          Patient Timeline
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-muted animate-pulse" />
              <div className="h-4 w-24 bg-muted rounded animate-pulse" />
            </div>
            <div className="ml-12 border rounded-lg p-4 space-y-2">
              <div className="h-4 w-48 bg-muted rounded animate-pulse" />
              <div className="h-3 w-full bg-muted rounded animate-pulse" />
              <div className="h-3 w-3/4 bg-muted rounded animate-pulse" />
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

export default PatientTimeline;
