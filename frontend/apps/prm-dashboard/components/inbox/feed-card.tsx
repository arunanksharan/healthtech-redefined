"use client";

import * as React from "react";
import {
  Phone,
  MessageCircle,
  Mail,
  MessageSquare,
  Smartphone,
  Bell,
  Clock,
  Image,
  FileText,
  Paperclip,
  ChevronRight,
  MoreHorizontal,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type {
  FeedItem,
  ChannelType,
  SentimentLabel,
  PriorityLevel,
  SuggestedAction,
} from "@/lib/store/inbox-store";

// Channel configuration
const channelConfig: Record<ChannelType, {
  icon: React.ElementType;
  label: string;
  color: string;
  bgColor: string;
}> = {
  zoice: {
    icon: Phone,
    label: "Zoice Call",
    color: "text-channel-voice",
    bgColor: "bg-channel-voice/10",
  },
  whatsapp: {
    icon: MessageCircle,
    label: "WhatsApp",
    color: "text-channel-whatsapp",
    bgColor: "bg-channel-whatsapp/10",
  },
  email: {
    icon: Mail,
    label: "Email",
    color: "text-channel-email",
    bgColor: "bg-channel-email/10",
  },
  sms: {
    icon: MessageSquare,
    label: "SMS",
    color: "text-channel-sms",
    bgColor: "bg-channel-sms/10",
  },
  app: {
    icon: Smartphone,
    label: "App",
    color: "text-channel-app",
    bgColor: "bg-channel-app/10",
  },
  system: {
    icon: Bell,
    label: "System",
    color: "text-muted-foreground",
    bgColor: "bg-muted",
  },
};

// Sentiment configuration
const sentimentConfig: Record<SentimentLabel, {
  color: string;
  bgColor: string;
}> = {
  positive: {
    color: "text-sentiment-positive",
    bgColor: "bg-sentiment-positive/10",
  },
  negative: {
    color: "text-sentiment-negative",
    bgColor: "bg-sentiment-negative/10",
  },
  neutral: {
    color: "text-sentiment-neutral",
    bgColor: "bg-sentiment-neutral/10",
  },
  frustrated: {
    color: "text-sentiment-frustrated",
    bgColor: "bg-sentiment-frustrated/10",
  },
  anxious: {
    color: "text-sentiment-negative",
    bgColor: "bg-sentiment-negative/10",
  },
};

// Priority configuration
const priorityConfig: Record<PriorityLevel, {
  color: string;
  bgColor: string;
  borderColor: string;
}> = {
  high: {
    color: "text-urgent",
    bgColor: "bg-urgent/10",
    borderColor: "border-l-urgent",
  },
  medium: {
    color: "text-warning",
    bgColor: "bg-warning/10",
    borderColor: "border-l-warning",
  },
  low: {
    color: "text-muted-foreground",
    bgColor: "bg-muted",
    borderColor: "border-l-muted",
  },
};

// Format timestamp
const formatTimestamp = (timestamp: Date): string => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  const timeStr = date.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return timeStr;
  if (diffDays === 1) return `Yesterday ${timeStr}`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
};

interface FeedCardProps {
  item: FeedItem;
  isSelected?: boolean;
  isMultiSelectMode?: boolean;
  isChecked?: boolean;
  onClick?: () => void;
  onCheck?: () => void;
  onAction?: (action: SuggestedAction) => void;
  onMarkRead?: () => void;
  onMarkResolved?: () => void;
  className?: string;
}

export function FeedCard({
  item,
  isSelected = false,
  isMultiSelectMode = false,
  isChecked = false,
  onClick,
  onCheck,
  onAction,
  onMarkRead,
  onMarkResolved,
  className,
}: FeedCardProps) {
  const channel = channelConfig[item.channel];
  const sentiment = sentimentConfig[item.sentiment.label];
  const priority = priorityConfig[item.priority];
  const ChannelIcon = channel.icon;

  const isUnread = item.status === "unread";
  const hasAttachments = item.attachments && item.attachments.length > 0;
  const primaryAction = item.suggestedActions.find((a) => a.isPrimary) || item.suggestedActions[0];
  const secondaryAction = item.suggestedActions[1];

  return (
    <div
      onClick={isMultiSelectMode ? onCheck : onClick}
      className={cn(
        "relative bg-card border rounded-lg p-4 transition-all cursor-pointer",
        "hover:shadow-md hover:border-primary/30",
        "border-l-4",
        priority.borderColor,
        isUnread && "border-l-primary",
        isSelected && "bg-primary/5 border-primary/50 shadow-md",
        isChecked && "bg-primary/5",
        item.isNew && "animate-fade-in ring-2 ring-primary/50",
        className
      )}
    >
      {/* Multi-select checkbox */}
      {isMultiSelectMode && (
        <div className="absolute left-2 top-1/2 -translate-y-1/2">
          <input
            type="checkbox"
            checked={isChecked}
            onChange={onCheck}
            onClick={(e) => e.stopPropagation()}
            className="h-4 w-4 rounded border-input"
          />
        </div>
      )}

      <div className={cn(isMultiSelectMode && "pl-6")}>
        {/* Header */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            {/* Channel Icon */}
            <div className={cn("p-1.5 rounded-md", channel.bgColor)}>
              <ChannelIcon className={cn("h-4 w-4", channel.color)} />
            </div>
            <span className="text-sm font-medium text-muted-foreground">
              {channel.label}
            </span>
            <span className="text-xs text-muted-foreground">
              {formatTimestamp(item.timestamp)}
            </span>
          </div>

          <div className="flex items-center gap-2">
            {/* Priority indicator */}
            {item.priority !== "low" && (
              <span className={cn("w-2 h-2 rounded-full", priority.bgColor.replace("/10", ""))} />
            )}

            {/* Unread indicator */}
            {isUnread && (
              <span className="w-2 h-2 rounded-full bg-primary" />
            )}

            {/* Status badge */}
            {item.status === "resolved" && (
              <Badge variant="secondary" className="text-xs">Resolved</Badge>
            )}
            {item.status === "escalated" && (
              <Badge variant="destructive" className="text-xs">Escalated</Badge>
            )}

            {/* Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {isUnread ? (
                  <DropdownMenuItem onClick={onMarkRead}>Mark as read</DropdownMenuItem>
                ) : (
                  <DropdownMenuItem>Mark as unread</DropdownMenuItem>
                )}
                <DropdownMenuItem onClick={onMarkResolved}>Mark as resolved</DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem>Assign to...</DropdownMenuItem>
                <DropdownMenuItem>Escalate</DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem className="text-destructive">Archive</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Patient info */}
        <div className="flex items-center gap-3 mb-2">
          <Avatar className="h-10 w-10">
            <AvatarImage src={item.patient.avatar} />
            <AvatarFallback className="text-sm">
              {item.patient.name.split(" ").map((n) => n[0]).join("").slice(0, 2)}
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <h4 className="font-medium text-foreground truncate">
              {item.patient.name}
            </h4>
            <p className="text-sm text-muted-foreground truncate">
              {item.context}
            </p>
          </div>
        </div>

        {/* Sentiment & Intent */}
        <div className="flex items-center gap-2 mb-2">
          <Badge variant="outline" className={cn("text-xs", sentiment.bgColor, sentiment.color)}>
            {item.sentiment.emoji} {item.sentiment.label}
          </Badge>
          <Badge variant="secondary" className="text-xs">
            {item.intent.split("_").join(" ")}
          </Badge>
        </div>

        {/* Preview */}
        <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
          "{item.preview}"
        </p>

        {/* Attachments */}
        {hasAttachments && (
          <div className="flex items-center gap-2 mb-3">
            {item.attachments!.slice(0, 3).map((attachment) => (
              <div
                key={attachment.id}
                className="flex items-center gap-1.5 px-2 py-1 bg-muted rounded text-xs text-muted-foreground"
              >
                {attachment.type === "image" ? (
                  <Image className="h-3 w-3" />
                ) : attachment.type === "document" ? (
                  <FileText className="h-3 w-3" />
                ) : (
                  <Paperclip className="h-3 w-3" />
                )}
                <span className="truncate max-w-20">{attachment.name}</span>
              </div>
            ))}
            {item.attachments!.length > 3 && (
              <span className="text-xs text-muted-foreground">
                +{item.attachments!.length - 3} more
              </span>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between pt-3 border-t border-border">
          <div className="flex items-center gap-2">
            {primaryAction && (
              <Button
                size="sm"
                variant="default"
                onClick={(e) => {
                  e.stopPropagation();
                  onAction?.(primaryAction);
                }}
                className="h-8"
              >
                {primaryAction.label}
              </Button>
            )}
            {secondaryAction && (
              <Button
                size="sm"
                variant="outline"
                onClick={(e) => {
                  e.stopPropagation();
                  onAction?.(secondaryAction);
                }}
                className="h-8"
              >
                {secondaryAction.label}
              </Button>
            )}
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={onClick}
            className="text-primary h-8"
          >
            View Details
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      </div>

      {/* New item indicator */}
      {item.isNew && (
        <span className="absolute -top-2 -right-2 px-2 py-0.5 bg-primary text-primary-foreground text-xs font-medium rounded-full">
          NEW
        </span>
      )}
    </div>
  );
}

// Skeleton loader for feed cards
export function FeedCardSkeleton() {
  return (
    <div className="bg-card border rounded-lg p-4 border-l-4 border-l-muted">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-muted rounded-md animate-pulse" />
          <div className="w-20 h-4 bg-muted rounded animate-pulse" />
          <div className="w-16 h-3 bg-muted rounded animate-pulse" />
        </div>
      </div>
      <div className="flex items-center gap-3 mb-2">
        <div className="w-10 h-10 bg-muted rounded-full animate-pulse" />
        <div className="flex-1">
          <div className="w-32 h-4 bg-muted rounded animate-pulse mb-1" />
          <div className="w-24 h-3 bg-muted rounded animate-pulse" />
        </div>
      </div>
      <div className="flex gap-2 mb-2">
        <div className="w-20 h-5 bg-muted rounded animate-pulse" />
        <div className="w-24 h-5 bg-muted rounded animate-pulse" />
      </div>
      <div className="w-full h-10 bg-muted rounded animate-pulse mb-3" />
      <div className="flex justify-between pt-3 border-t">
        <div className="flex gap-2">
          <div className="w-24 h-8 bg-muted rounded animate-pulse" />
          <div className="w-20 h-8 bg-muted rounded animate-pulse" />
        </div>
        <div className="w-24 h-8 bg-muted rounded animate-pulse" />
      </div>
    </div>
  );
}

export default FeedCard;
