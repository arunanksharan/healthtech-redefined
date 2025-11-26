"use client";

import * as React from "react";
import {
  Calendar,
  Phone,
  Mail,
  MessageSquare,
  FileText,
  Stethoscope,
  Pill,
  FlaskConical,
  Video,
  CreditCard,
  AlertCircle,
  CheckCircle,
  Clock,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

// Timeline event types
export type TimelineEventType =
  | "appointment"
  | "call"
  | "email"
  | "message"
  | "note"
  | "clinical"
  | "medication"
  | "lab"
  | "telehealth"
  | "billing"
  | "alert"
  | "general";

export interface TimelineEvent {
  id: string;
  type: TimelineEventType;
  title: string;
  description?: string;
  timestamp: Date | string;
  status?: "completed" | "pending" | "cancelled" | "in-progress";
  user?: {
    name: string;
    avatar?: string;
    role?: string;
  };
  metadata?: Record<string, string | number>;
  actions?: {
    label: string;
    onClick: () => void;
  }[];
}

// Event type configuration
const eventTypeConfig: Record<
  TimelineEventType,
  {
    icon: LucideIcon;
    iconBg: string;
    iconColor: string;
    label: string;
  }
> = {
  appointment: {
    icon: Calendar,
    iconBg: "bg-scheduled/10",
    iconColor: "text-scheduled",
    label: "Appointment",
  },
  call: {
    icon: Phone,
    iconBg: "bg-channel-voice/10",
    iconColor: "text-channel-voice",
    label: "Phone Call",
  },
  email: {
    icon: Mail,
    iconBg: "bg-channel-email/10",
    iconColor: "text-channel-email",
    label: "Email",
  },
  message: {
    icon: MessageSquare,
    iconBg: "bg-channel-whatsapp/10",
    iconColor: "text-channel-whatsapp",
    label: "Message",
  },
  note: {
    icon: FileText,
    iconBg: "bg-muted",
    iconColor: "text-muted-foreground",
    label: "Note",
  },
  clinical: {
    icon: Stethoscope,
    iconBg: "bg-primary/10",
    iconColor: "text-primary",
    label: "Clinical",
  },
  medication: {
    icon: Pill,
    iconBg: "bg-purple-100 dark:bg-purple-900/20",
    iconColor: "text-purple-600 dark:text-purple-400",
    label: "Medication",
  },
  lab: {
    icon: FlaskConical,
    iconBg: "bg-cyan-100 dark:bg-cyan-900/20",
    iconColor: "text-cyan-600 dark:text-cyan-400",
    label: "Lab Result",
  },
  telehealth: {
    icon: Video,
    iconBg: "bg-blue-100 dark:bg-blue-900/20",
    iconColor: "text-blue-600 dark:text-blue-400",
    label: "Telehealth",
  },
  billing: {
    icon: CreditCard,
    iconBg: "bg-green-100 dark:bg-green-900/20",
    iconColor: "text-green-600 dark:text-green-400",
    label: "Billing",
  },
  alert: {
    icon: AlertCircle,
    iconBg: "bg-destructive/10",
    iconColor: "text-destructive",
    label: "Alert",
  },
  general: {
    icon: Clock,
    iconBg: "bg-muted",
    iconColor: "text-muted-foreground",
    label: "Event",
  },
};

const statusConfig = {
  completed: {
    icon: CheckCircle,
    label: "Completed",
    className: "text-success",
  },
  pending: {
    icon: Clock,
    label: "Pending",
    className: "text-warning",
  },
  cancelled: {
    icon: AlertCircle,
    label: "Cancelled",
    className: "text-destructive",
  },
  "in-progress": {
    icon: Clock,
    label: "In Progress",
    className: "text-primary",
  },
};

// Format timestamp
const formatTimestamp = (timestamp: Date | string, showDate = true): string => {
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

  if (!showDate) {
    return timeStr;
  }

  if (diffDays === 0) {
    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    return `Today at ${timeStr}`;
  }
  if (diffDays === 1) return `Yesterday at ${timeStr}`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: date.getFullYear() !== now.getFullYear() ? "numeric" : undefined,
  });
};

// Individual timeline item
interface TimelineItemProps {
  event: TimelineEvent;
  isFirst?: boolean;
  isLast?: boolean;
  variant?: "default" | "compact";
}

function TimelineItem({ event, isFirst, isLast, variant = "default" }: TimelineItemProps) {
  const config = eventTypeConfig[event.type];
  const Icon = config.icon;
  const statusConf = event.status ? statusConfig[event.status] : null;
  const StatusIcon = statusConf?.icon;

  if (variant === "compact") {
    return (
      <div className="flex items-start gap-3 py-2">
        <div className={cn("p-1.5 rounded-lg shrink-0", config.iconBg)}>
          <Icon className={cn("h-4 w-4", config.iconColor)} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <p className="text-sm font-medium truncate">{event.title}</p>
            <span className="text-xs text-muted-foreground shrink-0">
              {formatTimestamp(event.timestamp)}
            </span>
          </div>
          {event.description && (
            <p className="text-xs text-muted-foreground truncate">{event.description}</p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-4">
      {/* Timeline line and icon */}
      <div className="flex flex-col items-center">
        <div className={cn("p-2 rounded-lg z-10", config.iconBg)}>
          <Icon className={cn("h-5 w-5", config.iconColor)} />
        </div>
        {!isLast && (
          <div className="w-px flex-1 bg-border my-2" />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 pb-6">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h4 className="font-medium text-foreground">{event.title}</h4>
              {event.status && StatusIcon && (
                <Badge variant="outline" className={cn("text-xs", statusConf?.className)}>
                  <StatusIcon className="h-3 w-3 mr-1" />
                  {statusConf?.label}
                </Badge>
              )}
            </div>
            {event.description && (
              <p className="text-sm text-muted-foreground">{event.description}</p>
            )}
          </div>
          <span className="text-xs text-muted-foreground whitespace-nowrap">
            {formatTimestamp(event.timestamp)}
          </span>
        </div>

        {/* User info */}
        {event.user && (
          <div className="flex items-center gap-2 mt-3">
            <Avatar className="h-6 w-6">
              <AvatarImage src={event.user.avatar} />
              <AvatarFallback className="text-xs">
                {event.user.name
                  .split(" ")
                  .map((n) => n[0])
                  .join("")}
              </AvatarFallback>
            </Avatar>
            <span className="text-sm text-muted-foreground">{event.user.name}</span>
            {event.user.role && (
              <Badge variant="secondary" className="text-xs">
                {event.user.role}
              </Badge>
            )}
          </div>
        )}

        {/* Metadata */}
        {event.metadata && Object.keys(event.metadata).length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3">
            {Object.entries(event.metadata).map(([key, value]) => (
              <span
                key={key}
                className="text-xs px-2 py-1 bg-muted rounded"
              >
                {key}: {value}
              </span>
            ))}
          </div>
        )}

        {/* Actions */}
        {event.actions && event.actions.length > 0 && (
          <div className="flex gap-2 mt-3">
            {event.actions.map((action, index) => (
              <button
                key={index}
                onClick={action.onClick}
                className="text-sm text-primary hover:underline"
              >
                {action.label}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// Main Timeline component
interface TimelineProps {
  events: TimelineEvent[];
  variant?: "default" | "compact";
  maxItems?: number;
  className?: string;
  onViewAll?: () => void;
}

export function Timeline({
  events,
  variant = "default",
  maxItems,
  className,
  onViewAll,
}: TimelineProps) {
  const displayedEvents = maxItems ? events.slice(0, maxItems) : events;
  const hasMore = maxItems && events.length > maxItems;

  if (events.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No events to display
      </div>
    );
  }

  return (
    <div className={className}>
      {displayedEvents.map((event, index) => (
        <TimelineItem
          key={event.id}
          event={event}
          isFirst={index === 0}
          isLast={index === displayedEvents.length - 1}
          variant={variant}
        />
      ))}

      {hasMore && onViewAll && (
        <button
          onClick={onViewAll}
          className="text-sm text-primary hover:underline mt-4"
        >
          View all {events.length} events
        </button>
      )}
    </div>
  );
}

export default Timeline;
