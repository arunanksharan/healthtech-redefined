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
import { MagicCard } from "@/components/ui/magic-card";
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
    color: "text-blue-600 dark:text-blue-400",
    bgColor: "bg-blue-50 dark:bg-blue-900/30",
  },
  whatsapp: {
    icon: MessageCircle,
    label: "WhatsApp",
    color: "text-green-600 dark:text-green-400",
    bgColor: "bg-green-50 dark:bg-green-900/30",
  },
  email: {
    icon: Mail,
    label: "Email",
    color: "text-purple-600 dark:text-purple-400",
    bgColor: "bg-purple-50 dark:bg-purple-900/30",
  },
  sms: {
    icon: MessageSquare,
    label: "SMS",
    color: "text-indigo-600 dark:text-indigo-400",
    bgColor: "bg-indigo-50 dark:bg-indigo-900/30",
  },
  app: {
    icon: Smartphone,
    label: "App",
    color: "text-orange-600 dark:text-orange-400",
    bgColor: "bg-orange-50 dark:bg-orange-900/30",
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
    color: "text-green-700 dark:text-green-300",
    bgColor: "bg-green-50 dark:bg-green-900/30 border-green-200 dark:border-green-800",
  },
  negative: {
    color: "text-red-700 dark:text-red-300",
    bgColor: "bg-red-50 dark:bg-red-900/30 border-red-200 dark:border-red-800",
  },
  neutral: {
    color: "text-muted-foreground",
    bgColor: "bg-muted border-border",
  },
  frustrated: {
    color: "text-orange-700 dark:text-orange-300",
    bgColor: "bg-orange-50 dark:bg-orange-900/30 border-orange-200 dark:border-orange-800",
  },
  anxious: {
    color: "text-purple-700 dark:text-purple-300",
    bgColor: "bg-purple-50 dark:bg-purple-900/30 border-purple-200 dark:border-purple-800",
  },
};

// Priority configuration
const priorityConfig: Record<PriorityLevel, {
  color: string;
  bgColor: string;
  borderColor: string;
}> = {
  high: {
    color: "text-red-600 dark:text-red-400",
    bgColor: "bg-red-50 dark:bg-red-900/20",
    borderColor: "border-l-red-500",
  },
  medium: {
    color: "text-orange-600 dark:text-orange-400",
    bgColor: "bg-orange-50 dark:bg-orange-900/20",
    borderColor: "border-l-orange-500",
  },
  low: {
    color: "text-blue-600 dark:text-blue-400",
    bgColor: "bg-blue-50 dark:bg-blue-900/20",
    borderColor: "border-l-blue-500",
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
    <MagicCard
      onClick={isMultiSelectMode ? onCheck : onClick}
      gradientColor="hsl(var(--info) / 0.15)"
      gradientOpacity={0.6}
      className={cn(
        "cursor-pointer overflow-visible transition-all duration-200 border border-border",
        "bg-card shadow-sm hover:shadow-md",
        "border-l-4",
        priority.borderColor,
        isSelected && "bg-blue-50/50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 ring-1 ring-blue-200 dark:ring-blue-800 shadow-md",
        isChecked && "bg-blue-50/30 dark:bg-blue-900/10",
        className
      )}
    >
      <div className="p-4">
        {/* Multi-select checkbox */}
        {isMultiSelectMode && (
          <div className="absolute left-2 top-1/2 -translate-y-1/2">
            <input
              type="checkbox"
              checked={isChecked}
              onChange={onCheck}
              onClick={(e) => e.stopPropagation()}
              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
          </div>
        )}

        <div className={cn(isMultiSelectMode && "pl-6")}>
          {/* Header */}
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              {/* Channel Icon */}
              <div className={cn("p-1.5 rounded-md", channel.bgColor)}>
                <ChannelIcon className={cn("h-4 w-4", channel.color)} />
              </div>
              <span className="text-sm font-medium text-muted-foreground">
                {channel.label}
              </span>
              <span className="text-xs text-muted-foreground/60">
                • {formatTimestamp(item.timestamp)}
              </span>
            </div>

            <div className="flex items-center gap-2">
              {/* Unread indicator */}
              {isUnread && (
                <span className="w-2.5 h-2.5 rounded-full bg-blue-600 ring-2 ring-blue-100" />
              )}

              {/* Status badge */}
              {item.status === "resolved" && (
                <Badge variant="secondary" className="text-xs bg-muted text-muted-foreground">Resolved</Badge>
              )}
              {item.status === "escalated" && (
                <Badge variant="destructive" className="text-xs">Escalated</Badge>
              )}

              {/* Menu */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                  <Button variant="ghost" size="sm" className="h-8 w-8 p-0 text-muted-foreground hover:text-foreground">
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
                  <DropdownMenuItem className="text-red-600">Archive</DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>

          {/* Patient info */}
          <div className="flex items-center gap-3 mb-3">
            <Avatar className="h-10 w-10 border border-border">
              <AvatarImage src={item.patient.avatar} />
              <AvatarFallback className="text-sm bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-900/30 dark:to-purple-900/30 text-blue-700 dark:text-blue-300 font-medium">
                {item.patient.name.split(" ").map((n) => n[0]).join("").slice(0, 2)}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <h4 className="font-semibold text-foreground truncate">
                {item.patient.name}
              </h4>
              <p className="text-sm text-muted-foreground truncate">
                {item.context}
              </p>
            </div>
          </div>

          {/* Sentiment & Intent */}
          <div className="flex flex-wrap items-center gap-2 mb-3">
            <Badge variant="outline" className={cn("text-xs border", sentiment.bgColor, sentiment.color)}>
              {item.sentiment.emoji} {item.sentiment.label}
            </Badge>
            <Badge variant="secondary" className="text-xs bg-muted text-muted-foreground hover:bg-accent">
              {item.intent.split("_").join(" ")}
            </Badge>
          </div>

          {/* Preview */}
          <p className="text-sm text-muted-foreground line-clamp-2 mb-4 leading-relaxed">
            "{item.preview}"
          </p>

          {/* Attachments */}
          {hasAttachments && (
            <div className="flex items-center gap-2 mb-4">
              {item.attachments!.slice(0, 3).map((attachment) => (
                <div
                  key={attachment.id}
                  className="flex items-center gap-1.5 px-2.5 py-1.5 bg-muted border border-border rounded-md text-xs text-muted-foreground font-medium"
                >
                  {attachment.type === "image" ? (
                    <Image className="h-3.5 w-3.5 text-blue-500" />
                  ) : attachment.type === "document" ? (
                    <FileText className="h-3.5 w-3.5 text-orange-500" />
                  ) : (
                    <Paperclip className="h-3.5 w-3.5 text-muted-foreground" />
                  )}
                  <span className="truncate max-w-[100px]">{attachment.name}</span>
                </div>
              ))}
              {item.attachments!.length > 3 && (
                <span className="text-xs text-muted-foreground font-medium pl-1">
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
                  onClick={(e) => {
                    e.stopPropagation();
                    onAction?.(primaryAction);
                  }}
                  className="h-8 bg-blue-600 hover:bg-blue-700 text-white shadow-sm"
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
                  className="h-8 border-border text-muted-foreground hover:bg-accent"
                >
                  {secondaryAction.label}
                </Button>
              )}
            </div>

            <Button
              variant="ghost"
              size="sm"
              onClick={onClick}
              className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/20 h-8"
            >
              View Details
              <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          </div>
        </div>
      </div>

      {/* New item indicator */}
      {item.isNew && (
        <span className="absolute -top-1 -right-1 px-2 py-0.5 bg-blue-600 text-white text-[10px] font-bold tracking-wider rounded-full shadow-sm ring-2 ring-white">
          NEW
        </span>
      )}
    </MagicCard>
  );
}

// Skeleton loader for feed cards
export function FeedCardSkeleton() {
  return (
    <div className="bg-card border rounded-xl p-4 border-border shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-muted rounded-md animate-pulse" />
          <div className="w-24 h-4 bg-muted rounded animate-pulse" />
        </div>
      </div>
      <div className="flex items-center gap-3 mb-3">
        <div className="w-10 h-10 bg-muted rounded-full animate-pulse" />
        <div className="flex-1">
          <div className="w-32 h-4 bg-muted rounded animate-pulse mb-2" />
          <div className="w-24 h-3 bg-muted rounded animate-pulse" />
        </div>
      </div>
      <div className="flex gap-2 mb-3">
        <div className="w-20 h-6 bg-muted rounded animate-pulse" />
        <div className="w-24 h-6 bg-muted rounded animate-pulse" />
      </div>
      <div className="w-full h-12 bg-muted rounded animate-pulse mb-4" />
      <div className="flex justify-between pt-3 border-t border-border">
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
