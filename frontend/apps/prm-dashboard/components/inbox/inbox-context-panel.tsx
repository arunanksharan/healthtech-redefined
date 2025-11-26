"use client";

import * as React from "react";
import { useState } from "react";
import {
  Phone,
  MessageCircle,
  Mail,
  User,
  Building,
  Clock,
  Play,
  Pause,
  Volume2,
  ChevronDown,
  ChevronUp,
  X,
  Calendar,
  FileText,
  Send,
  ExternalLink,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { FeedItem, SuggestedAction } from "@/lib/store/inbox-store";

interface InboxContextPanelProps {
  item: FeedItem;
  onClose: () => void;
  onAction?: (action: SuggestedAction) => void;
  className?: string;
}

// Sentiment configuration for display
const sentimentDisplay = {
  positive: { emoji: "😊", label: "Positive", color: "text-sentiment-positive" },
  negative: { emoji: "😞", label: "Negative", color: "text-sentiment-negative" },
  neutral: { emoji: "😐", label: "Neutral", color: "text-sentiment-neutral" },
  frustrated: { emoji: "😤", label: "Frustrated", color: "text-sentiment-frustrated" },
  anxious: { emoji: "😰", label: "Anxious", color: "text-sentiment-negative" },
};

const priorityDisplay = {
  high: { label: "High", color: "text-urgent", bg: "bg-urgent/10" },
  medium: { label: "Medium", color: "text-warning", bg: "bg-warning/10" },
  low: { label: "Low", color: "text-muted-foreground", bg: "bg-muted" },
};

// Format duration in mm:ss
const formatDuration = (seconds: number): string => {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
};

// Mock transcript data
const mockTranscript = [
  { speaker: "AI", text: "Thank you for calling Surya Hospitals. How can I help you today?" },
  { speaker: "Patient", text: "Hi, I need to reschedule my appointment for tomorrow." },
  { speaker: "AI", text: "Of course, I can help you with that. Let me look up your appointment." },
  { speaker: "Patient", text: "It's for Dr. Sharma at 2 PM. The traffic is going to be terrible." },
  { speaker: "AI", text: "I understand. Would you prefer Tuesday or Wednesday afternoon instead?" },
  { speaker: "Patient", text: "Tuesday at the same time would work for me." },
  { speaker: "AI", text: "Perfect, I've rescheduled your appointment to Tuesday at 2 PM." },
];

// Audio Player Component
function AudioPlayer({ url, duration }: { url?: string; duration?: number }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const totalDuration = duration || 272; // Default 4:32

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-3">
        <button
          onClick={() => setIsPlaying(!isPlaying)}
          className="p-2 rounded-full bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
        </button>

        <div className="flex-1 h-1 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-primary rounded-full transition-all"
            style={{ width: `${(currentTime / totalDuration) * 100}%` }}
          />
        </div>

        <span className="text-xs text-muted-foreground font-mono">
          {formatDuration(currentTime)} / {formatDuration(totalDuration)}
        </span>

        <button className="p-1.5 rounded-md hover:bg-muted">
          <Volume2 className="h-4 w-4 text-muted-foreground" />
        </button>
      </div>
    </div>
  );
}

// Transcript Component
function TranscriptView({ transcript }: { transcript: typeof mockTranscript }) {
  const [expanded, setExpanded] = useState(false);
  const displayedTranscript = expanded ? transcript : transcript.slice(0, 3);

  return (
    <div className="space-y-3">
      {displayedTranscript.map((line, index) => (
        <div
          key={index}
          className={cn(
            "flex gap-3",
            line.speaker === "AI" ? "justify-start" : "justify-end"
          )}
        >
          <div
            className={cn(
              "max-w-[80%] p-3 rounded-lg text-sm",
              line.speaker === "AI"
                ? "bg-muted text-foreground"
                : "bg-primary/10 text-foreground"
            )}
          >
            <span className="text-xs text-muted-foreground block mb-1">
              {line.speaker === "AI" ? "AI Agent" : "Patient"}
            </span>
            {line.text}
          </div>
        </div>
      ))}

      {transcript.length > 3 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-sm text-primary hover:underline"
        >
          {expanded ? (
            <>
              <ChevronUp className="h-4 w-4" /> Show less
            </>
          ) : (
            <>
              <ChevronDown className="h-4 w-4" /> Show {transcript.length - 3} more
            </>
          )}
        </button>
      )}
    </div>
  );
}

export function InboxContextPanel({
  item,
  onClose,
  onAction,
  className,
}: InboxContextPanelProps) {
  const sentiment = sentimentDisplay[item.sentiment.label];
  const priority = priorityDisplay[item.priority];

  return (
    <div
      className={cn(
        "h-full flex flex-col bg-card border-l border-border overflow-hidden",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between p-4 border-b border-border">
        <div className="flex items-center gap-3">
          <Avatar className="h-12 w-12">
            <AvatarImage src={item.patient.avatar} />
            <AvatarFallback>
              {item.patient.name.split(" ").map((n) => n[0]).join("").slice(0, 2)}
            </AvatarFallback>
          </Avatar>
          <div>
            <h3 className="font-semibold text-foreground">{item.patient.name}</h3>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Phone className="h-3.5 w-3.5" />
              {item.patient.phone || "+1 (555) 123-4567"}
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Building className="h-3.5 w-3.5" />
              {item.context}
            </div>
          </div>
        </div>
        <Button variant="ghost" size="sm" onClick={onClose} className="h-8 w-8 p-0">
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Analysis Section */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Call Analysis
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              {/* Sentiment */}
              <div className="space-y-1">
                <span className="text-xs text-muted-foreground">Sentiment</span>
                <div className={cn("flex items-center gap-2 font-medium", sentiment.color)}>
                  <span className="text-lg">{sentiment.emoji}</span>
                  <span>{sentiment.label}</span>
                  <span className="text-xs">({item.sentiment.score}%)</span>
                </div>
              </div>

              {/* Intent */}
              <div className="space-y-1">
                <span className="text-xs text-muted-foreground">Intent</span>
                <Badge variant="secondary" className="font-medium">
                  {item.intent.split("_").join(" ")}
                </Badge>
              </div>

              {/* Urgency */}
              <div className="space-y-1">
                <span className="text-xs text-muted-foreground">Urgency</span>
                <Badge
                  variant="outline"
                  className={cn(priority.color, priority.bg)}
                >
                  {priority.label}
                </Badge>
              </div>

              {/* Duration */}
              {item.metadata?.callDuration && (
                <div className="space-y-1">
                  <span className="text-xs text-muted-foreground">Duration</span>
                  <div className="flex items-center gap-1 text-foreground">
                    <Clock className="h-3.5 w-3.5" />
                    {formatDuration(item.metadata.callDuration as number)}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* AI Summary */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              AI Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-foreground leading-relaxed">
              Patient called to reschedule tomorrow's 2PM cardiology follow-up.
              Expressed frustration about traffic conditions. Requested Tuesday
              or Wednesday afternoon instead. Preferred time slot: Tuesday 2PM.
            </p>
          </CardContent>
        </Card>

        {/* Suggested Actions */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Suggested Actions
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {item.suggestedActions.map((action) => (
              <Button
                key={action.id}
                variant={action.isPrimary ? "default" : "outline"}
                className="w-full justify-start"
                onClick={() => onAction?.(action)}
              >
                {action.type === "reschedule" && <Calendar className="h-4 w-4 mr-2" />}
                {action.type === "callback" && <Phone className="h-4 w-4 mr-2" />}
                {action.type === "message" && <MessageCircle className="h-4 w-4 mr-2" />}
                {action.label}
              </Button>
            ))}
          </CardContent>
        </Card>

        {/* Media Section (for calls) */}
        {item.channel === "zoice" && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Recording
              </CardTitle>
            </CardHeader>
            <CardContent>
              <AudioPlayer
                url={item.metadata?.recordingUrl as string}
                duration={item.metadata?.callDuration as number}
              />
            </CardContent>
          </Card>
        )}

        {/* Transcript */}
        {item.channel === "zoice" && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Transcript
              </CardTitle>
            </CardHeader>
            <CardContent>
              <TranscriptView transcript={mockTranscript} />
            </CardContent>
          </Card>
        )}

        {/* Attachments */}
        {item.attachments && item.attachments.length > 0 && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Attachments
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {item.attachments.map((attachment) => (
                <div
                  key={attachment.id}
                  className="flex items-center justify-between p-2 bg-muted rounded-lg"
                >
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">{attachment.name}</span>
                  </div>
                  <Button variant="ghost" size="sm">
                    <ExternalLink className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Footer Actions */}
      <div className="p-4 border-t border-border bg-muted/30">
        <div className="flex gap-2">
          <Button className="flex-1">
            <Send className="h-4 w-4 mr-2" />
            Send WhatsApp
          </Button>
          <Button variant="outline">
            <Phone className="h-4 w-4 mr-2" />
            Call
          </Button>
          <Button variant="outline" asChild>
            <a href={`/patients/${item.patient.id}`}>
              <User className="h-4 w-4 mr-2" />
              Profile
            </a>
          </Button>
        </div>
      </div>
    </div>
  );
}

export default InboxContextPanel;
