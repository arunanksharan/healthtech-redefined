"use client";

import * as React from "react";
import {
  MessageSquare,
  Phone,
  Mail,
  MessageCircle,
  Smartphone,
  Monitor,
  Play,
  Pause,
  FileText,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Clock,
  ArrowUpRight,
  ArrowDownLeft,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { Communication, ChannelType } from "@/lib/store/patient-profile-store";
import { format, isToday, isYesterday, formatDistanceToNow } from "date-fns";

// ============================================================================
// Types
// ============================================================================

interface CommunicationHistoryProps {
  communications: Communication[];
  isLoading?: boolean;
  filter: ChannelType | "all";
  onFilterChange: (filter: ChannelType | "all") => void;
  onPlayRecording?: (commId: string) => void;
  onViewTranscript?: (commId: string) => void;
  onViewConversation?: (commId: string) => void;
  onLoadMore?: () => void;
  hasMore?: boolean;
  className?: string;
}

// ============================================================================
// Helper Functions
// ============================================================================

type ChannelConfig = {
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  bgColor: string;
};

const channelConfigs: Record<ChannelType, ChannelConfig> = {
  zoice: {
    label: "Voice",
    icon: Phone,
    color: "text-blue-600",
    bgColor: "bg-blue-500/10",
  },
  whatsapp: {
    label: "WhatsApp",
    icon: MessageCircle,
    color: "text-green-600",
    bgColor: "bg-green-500/10",
  },
  email: {
    label: "Email",
    icon: Mail,
    color: "text-purple-600",
    bgColor: "bg-purple-500/10",
  },
  sms: {
    label: "SMS",
    icon: Smartphone,
    color: "text-orange-600",
    bgColor: "bg-orange-500/10",
  },
  app: {
    label: "App",
    icon: Monitor,
    color: "text-cyan-600",
    bgColor: "bg-cyan-500/10",
  },
  fhir: {
    label: "System",
    icon: Monitor,
    color: "text-gray-600",
    bgColor: "bg-gray-500/10",
  },
};

const filterTabs: { value: ChannelType | "all"; label: string }[] = [
  { value: "all", label: "All" },
  { value: "zoice", label: "Voice" },
  { value: "whatsapp", label: "WhatsApp" },
  { value: "email", label: "Email" },
  { value: "sms", label: "SMS" },
  { value: "app", label: "App" },
];

const formatTimestamp = (date: Date): string => {
  const d = new Date(date);
  if (isToday(d)) {
    return format(d, "h:mm a");
  }
  if (isYesterday(d)) {
    return `Yesterday ${format(d, "h:mm a")}`;
  }
  return format(d, "MMM d, h:mm a");
};

const formatDuration = (seconds: number): string => {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}m ${secs}s`;
};

const groupByDate = (communications: Communication[]): Map<string, Communication[]> => {
  const groups = new Map<string, Communication[]>();

  communications.forEach((comm) => {
    const date = new Date(comm.timestamp);
    let key: string;

    if (isToday(date)) {
      key = "Today";
    } else if (isYesterday(date)) {
      key = "Yesterday";
    } else {
      key = format(date, "MMMM d, yyyy");
    }

    const existing = groups.get(key) || [];
    groups.set(key, [...existing, comm]);
  });

  return groups;
};

// ============================================================================
// Communication Item Component
// ============================================================================

interface CommunicationItemProps {
  communication: Communication;
  onPlayRecording?: (commId: string) => void;
  onViewTranscript?: (commId: string) => void;
  onViewConversation?: (commId: string) => void;
}

function CommunicationItem({
  communication,
  onPlayRecording,
  onViewTranscript,
  onViewConversation,
}: CommunicationItemProps) {
  const [isExpanded, setIsExpanded] = React.useState(false);
  const [isPlaying, setIsPlaying] = React.useState(false);

  const channelConfig = channelConfigs[communication.channel];
  const ChannelIcon = channelConfig.icon;
  const isInbound = communication.direction === "inbound";

  const handlePlay = () => {
    setIsPlaying(!isPlaying);
    onPlayRecording?.(communication.id);
  };

  return (
    <div className="group relative pl-4 pb-4">
      {/* Timeline line */}
      <div className="absolute left-0 top-0 bottom-0 w-px bg-border" />

      {/* Timeline dot */}
      <div
        className={cn(
          "absolute left-[-4px] top-2 w-2 h-2 rounded-full border-2 border-background",
          channelConfig.bgColor.replace("/10", "")
        )}
        style={{ backgroundColor: channelConfig.color.replace("text-", "").replace("-600", "") }}
      />

      <div className="ml-4 p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors">
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            {/* Channel icon */}
            <div className={cn("p-2 rounded-lg", channelConfig.bgColor)}>
              <ChannelIcon className={cn("h-4 w-4", channelConfig.color)} />
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                {/* Direction indicator */}
                {isInbound ? (
                  <ArrowDownLeft className="h-3 w-3 text-muted-foreground" />
                ) : (
                  <ArrowUpRight className="h-3 w-3 text-muted-foreground" />
                )}

                {/* Channel label */}
                <Badge variant="outline" className="text-xs">
                  {channelConfig.label}
                </Badge>

                {/* Duration for calls */}
                {communication.duration && (
                  <span className="text-xs text-muted-foreground">
                    ({formatDuration(communication.duration)})
                  </span>
                )}

                {/* Sentiment */}
                {communication.sentiment && (
                  <Badge
                    variant="outline"
                    className={cn(
                      "text-xs",
                      communication.sentiment.score > 70
                        ? "text-destructive border-destructive/30"
                        : communication.sentiment.score > 40
                        ? "text-warning border-warning/30"
                        : "text-success border-success/30"
                    )}
                  >
                    {communication.sentiment.emoji} {communication.sentiment.label}
                  </Badge>
                )}

                {/* Status */}
                <span className="text-xs text-muted-foreground capitalize">
                  {communication.status}
                </span>
              </div>

              {/* Subject (for email) */}
              {communication.subject && (
                <p className="text-sm font-medium mt-1">{communication.subject}</p>
              )}

              {/* Preview */}
              <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                {communication.preview}
              </p>

              {/* Expanded content */}
              {isExpanded && communication.content && (
                <div className="mt-3 p-3 bg-muted/50 rounded-lg">
                  <p className="text-sm whitespace-pre-wrap">{communication.content}</p>
                </div>
              )}
            </div>
          </div>

          {/* Timestamp */}
          <div className="flex flex-col items-end gap-1 flex-shrink-0">
            <span className="text-xs text-muted-foreground">
              {formatTimestamp(communication.timestamp)}
            </span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 mt-3 pt-2 border-t">
          {/* Voice actions */}
          {communication.channel === "zoice" && (
            <>
              <Button
                variant="outline"
                size="sm"
                className="h-7 text-xs"
                onClick={handlePlay}
              >
                {isPlaying ? (
                  <>
                    <Pause className="h-3 w-3 mr-1" />
                    Pause
                  </>
                ) : (
                  <>
                    <Play className="h-3 w-3 mr-1" />
                    Play Recording
                  </>
                )}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-7 text-xs"
                onClick={() => onViewTranscript?.(communication.id)}
              >
                <FileText className="h-3 w-3 mr-1" />
                Transcript
              </Button>
            </>
          )}

          {/* WhatsApp actions */}
          {communication.channel === "whatsapp" && (
            <Button
              variant="outline"
              size="sm"
              className="h-7 text-xs"
              onClick={() => onViewConversation?.(communication.id)}
            >
              <MessageCircle className="h-3 w-3 mr-1" />
              View Conversation
            </Button>
          )}

          {/* Email actions */}
          {communication.channel === "email" && (
            <Button
              variant="outline"
              size="sm"
              className="h-7 text-xs"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="h-3 w-3 mr-1" />
                  Less
                </>
              ) : (
                <>
                  <ChevronDown className="h-3 w-3 mr-1" />
                  View Email
                </>
              )}
            </Button>
          )}

          {/* Generic expand for content */}
          {communication.content && communication.channel !== "email" && (
            <Button
              variant="ghost"
              size="sm"
              className="h-7 text-xs ml-auto"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? (
                <ChevronUp className="h-3 w-3" />
              ) : (
                <ChevronDown className="h-3 w-3" />
              )}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Communication History Component
// ============================================================================

export function CommunicationHistory({
  communications,
  isLoading = false,
  filter,
  onFilterChange,
  onPlayRecording,
  onViewTranscript,
  onViewConversation,
  onLoadMore,
  hasMore = false,
  className,
}: CommunicationHistoryProps) {
  // Filter communications
  const filteredCommunications =
    filter === "all"
      ? communications
      : communications.filter((c) => c.channel === filter);

  // Group by date
  const groupedCommunications = groupByDate(filteredCommunications);

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
          <MessageSquare className="h-4 w-4 text-primary" />
          Communication History
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Filter Tabs */}
        <div className="flex items-center gap-1 overflow-x-auto pb-2">
          {filterTabs.map((tab) => (
            <Button
              key={tab.value}
              variant={filter === tab.value ? "secondary" : "ghost"}
              size="sm"
              className={cn(
                "h-8 text-xs flex-shrink-0",
                filter === tab.value && "bg-primary/10 text-primary"
              )}
              onClick={() => onFilterChange(tab.value)}
            >
              {tab.value !== "all" && (
                <span className="mr-1.5">
                  {tab.value === "zoice" && "🎤"}
                  {tab.value === "whatsapp" && "💬"}
                  {tab.value === "email" && "📧"}
                  {tab.value === "sms" && "📱"}
                  {tab.value === "app" && "🖥️"}
                </span>
              )}
              {tab.label}
            </Button>
          ))}
        </div>

        {/* Loading state */}
        {isLoading && (
          <div className="flex flex-col items-center justify-center py-8 gap-3">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">Loading communications...</p>
          </div>
        )}

        {/* Empty state */}
        {!isLoading && filteredCommunications.length === 0 && (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <MessageSquare className="h-8 w-8 text-muted-foreground mb-2" />
            <p className="text-sm text-muted-foreground">
              {filter === "all"
                ? "No communication history"
                : `No ${filterTabs.find((t) => t.value === filter)?.label} messages`}
            </p>
          </div>
        )}

        {/* Communication list */}
        {!isLoading && filteredCommunications.length > 0 && (
          <div className="space-y-4">
            {Array.from(groupedCommunications.entries()).map(([date, comms]) => (
              <div key={date}>
                {/* Date header */}
                <div className="flex items-center gap-2 mb-3">
                  <div className="h-px flex-1 bg-border" />
                  <span className="text-xs font-medium text-muted-foreground px-2">
                    {date}
                  </span>
                  <div className="h-px flex-1 bg-border" />
                </div>

                {/* Communications for this date */}
                <div className="space-y-0">
                  {comms.map((comm) => (
                    <CommunicationItem
                      key={comm.id}
                      communication={comm}
                      onPlayRecording={onPlayRecording}
                      onViewTranscript={onViewTranscript}
                      onViewConversation={onViewConversation}
                    />
                  ))}
                </div>
              </div>
            ))}

            {/* Load more */}
            {hasMore && (
              <div className="text-center pt-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onLoadMore}
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  ) : (
                    <Clock className="h-4 w-4 mr-2" />
                  )}
                  Load Earlier Communications
                </Button>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Compact Communication Summary (for sidebar)
// ============================================================================

interface CompactCommunicationSummaryProps {
  communications: Communication[];
  onExpand?: () => void;
  className?: string;
}

export function CompactCommunicationSummary({
  communications,
  onExpand,
  className,
}: CompactCommunicationSummaryProps) {
  // Count by channel
  const channelCounts = communications.reduce((acc, comm) => {
    acc[comm.channel] = (acc[comm.channel] || 0) + 1;
    return acc;
  }, {} as Record<ChannelType, number>);

  // Get most recent
  const mostRecent = communications[0];

  if (communications.length === 0) {
    return (
      <div className={cn("p-4 bg-muted/50 rounded-lg text-center", className)}>
        <MessageSquare className="h-5 w-5 text-muted-foreground mx-auto mb-2" />
        <p className="text-sm text-muted-foreground">No recent communications</p>
      </div>
    );
  }

  return (
    <div className={cn("p-4 bg-muted/50 rounded-lg", className)}>
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <MessageSquare className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium">Communications</span>
        </div>
        {onExpand && (
          <Button
            variant="ghost"
            size="sm"
            className="h-6 text-xs"
            onClick={onExpand}
          >
            View All
          </Button>
        )}
      </div>

      {/* Channel counts */}
      <div className="flex flex-wrap gap-2 mb-3">
        {Object.entries(channelCounts).map(([channel, count]) => {
          const config = channelConfigs[channel as ChannelType];
          return (
            <Badge
              key={channel}
              variant="outline"
              className={cn("text-xs", config.color, config.bgColor)}
            >
              {config.label}: {count}
            </Badge>
          );
        })}
      </div>

      {/* Most recent */}
      {mostRecent && (
        <div className="text-xs text-muted-foreground">
          <span className="font-medium">Latest:</span>{" "}
          {formatDistanceToNow(new Date(mostRecent.timestamp), { addSuffix: true })} via{" "}
          {channelConfigs[mostRecent.channel].label}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Communication History Skeleton
// ============================================================================

export function CommunicationHistorySkeleton({ className }: { className?: string }) {
  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
          <MessageSquare className="h-4 w-4 text-primary" />
          Communication History
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Filter tabs skeleton */}
        <div className="flex items-center gap-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <div
              key={i}
              className="h-8 w-20 bg-muted rounded animate-pulse"
            />
          ))}
        </div>

        {/* Items skeleton */}
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-24 bg-muted/50 rounded-lg animate-pulse"
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export default CommunicationHistory;
