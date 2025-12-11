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
import { ScrollArea } from "@/components/ui/scroll-area";
import type { FeedItem, SuggestedAction } from "@/lib/store/inbox-store";

interface InboxContextPanelProps {
  item: FeedItem;
  onClose: () => void;
  onAction?: (action: SuggestedAction) => void;
  className?: string;
}

// Sentiment configuration for display
const sentimentDisplay = {
  positive: { emoji: "😊", label: "Positive", color: "text-green-600" },
  negative: { emoji: "😞", label: "Negative", color: "text-red-600" },
  neutral: { emoji: "😐", label: "Neutral", color: "text-gray-600" },
  frustrated: { emoji: "😤", label: "Frustrated", color: "text-orange-600" },
  anxious: { emoji: "😰", label: "Anxious", color: "text-purple-600" },
};

const priorityDisplay = {
  high: { label: "High", color: "text-red-700", bg: "bg-red-50" },
  medium: { label: "Medium", color: "text-orange-700", bg: "bg-orange-50" },
  low: { label: "Low", color: "text-blue-700", bg: "bg-blue-50" },
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
    <div className="space-y-3 bg-gray-50 p-3 rounded-lg border border-gray-100">
      <div className="flex items-center gap-3">
        <button
          onClick={() => setIsPlaying(!isPlaying)}
          className="p-2.5 rounded-full bg-blue-600 text-white hover:bg-blue-700 transition-colors shadow-sm"
        >
          {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4 pl-0.5" />}
        </button>

        <div className="flex-1 space-y-1.5">
          <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-600 rounded-full transition-all"
              style={{ width: `${(currentTime / totalDuration) * 100}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-500 font-medium">
            <span>{formatDuration(currentTime)}</span>
            <span>{formatDuration(totalDuration)}</span>
          </div>
        </div>

        <button className="p-2 rounded-md hover:bg-white hover:shadow-sm transition-all">
          <Volume2 className="h-4 w-4 text-gray-500" />
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
    <div className="space-y-4">
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
              "max-w-[85%] p-3.5 rounded-2xl text-sm leading-relaxed shadow-sm",
              line.speaker === "AI"
                ? "bg-gray-100 text-gray-800 rounded-tl-none"
                : "bg-blue-50 text-gray-800 rounded-tr-none border border-blue-100"
            )}
          >
            <span className="text-[10px] uppercase font-bold tracking-wider text-gray-400 block mb-1">
              {line.speaker === "AI" ? "AI Agent" : "Patient"}
            </span>
            {line.text}
          </div>
        </div>
      ))}

      {transcript.length > 3 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full flex items-center justify-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-700 py-2 bg-blue-50/50 rounded-md transition-colors"
        >
          {expanded ? (
            <>
              <ChevronUp className="h-3 w-3" /> Show less
            </>
          ) : (
            <>
              <ChevronDown className="h-3 w-3" /> Show {transcript.length - 3} more lines
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
        "h-full flex flex-col bg-white border-l border-gray-200",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between p-6 border-b border-gray-100 bg-white/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="flex items-center gap-4">
          <Avatar className="h-14 w-14 ring-2 ring-white shadow-sm border border-gray-100">
            <AvatarImage src={item.patient.avatar} />
            <AvatarFallback className="bg-gradient-to-br from-blue-100 to-indigo-100 text-blue-700 text-lg font-semibold">
              {item.patient.name.split(" ").map((n) => n[0]).join("").slice(0, 2)}
            </AvatarFallback>
          </Avatar>
          <div>
            <h3 className="font-bold text-gray-900 text-lg mb-0.5">{item.patient.name}</h3>
            <div className="flex flex-col gap-0.5">
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <Phone className="h-3.5 w-3.5" />
                {item.patient.phone || "+1 (555) 123-4567"}
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <Building className="h-3.5 w-3.5" />
                {item.context}
              </div>
            </div>
          </div>
        </div>
        <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100">
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Content */}
      <ScrollArea className="flex-1 bg-gray-50/30">
        <div className="p-6 space-y-6">
          {/* Analysis Section */}
          <Card className="border-gray-200 shadow-sm overflow-hidden">
            <CardHeader className="pb-3 bg-gray-50/50 border-b border-gray-100">
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-gray-500 flex items-center gap-2">
                <FileText className="h-3.5 w-3.5" />
                Call Analysis
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              <div className="grid grid-cols-2 gap-6">
                {/* Sentiment */}
                <div className="space-y-1.5">
                  <span className="text-xs font-medium text-gray-400">Sentiment</span>
                  <div className={cn("flex items-center gap-2 font-medium", sentiment.color)}>
                    <span className="text-xl">{sentiment.emoji}</span>
                    <span className="text-sm font-semibold">{sentiment.label}</span>
                    <span className="text-xs bg-gray-100 px-1.5 py-0.5 rounded-full text-gray-600">{item.sentiment.score}%</span>
                  </div>
                </div>

                {/* Intent */}
                <div className="space-y-1.5">
                  <span className="text-xs font-medium text-gray-400">Intent</span>
                  <div>
                    <Badge variant="secondary" className="font-semibold bg-gray-100 text-gray-700 hover:bg-gray-200 border-transparent">
                      {item.intent.split("_").join(" ")}
                    </Badge>
                  </div>
                </div>

                {/* Urgency */}
                <div className="space-y-1.5">
                  <span className="text-xs font-medium text-gray-400">Urgency</span>
                  <div>
                    <Badge
                      variant="outline"
                      className={cn("font-semibold border-0", priority.color, priority.bg)}
                    >
                      {priority.label}
                    </Badge>
                  </div>
                </div>

                {/* Duration */}
                {item.metadata?.callDuration && (
                  <div className="space-y-1.5">
                    <span className="text-xs font-medium text-gray-400">Duration</span>
                    <div className="flex items-center gap-1.5 text-gray-700 font-medium text-sm">
                      <Clock className="h-3.5 w-3.5 text-gray-400" />
                      {formatDuration(item.metadata.callDuration as number)}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* AI Summary */}
          <Card className="border-gray-200 shadow-sm">
            <CardHeader className="pb-3 bg-gray-50/50 border-b border-gray-100">
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-gray-500">
                AI Summary
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              <p className="text-sm text-gray-700 leading-relaxed">
                Patient called to reschedule tomorrow's 2PM cardiology follow-up.
                Expressed frustration about traffic conditions. Requested Tuesday
                or Wednesday afternoon instead. Preferred time slot: <span className="font-semibold text-gray-900 bg-yellow-50 px-1 rounded">Tuesday 2PM</span>.
              </p>
            </CardContent>
          </Card>

          {/* Suggested Actions */}
          <Card className="border-gray-200 shadow-sm border-l-4 border-l-blue-500">
            <CardHeader className="pb-3 bg-gray-50/50 border-b border-gray-100">
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-blue-600">
                Suggested Actions
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-2.5">
              {item.suggestedActions.map((action) => (
                <Button
                  key={action.id}
                  variant={action.isPrimary ? "default" : "outline"}
                  className={cn(
                    "w-full justify-start h-auto py-2.5 shadow-sm",
                    action.isPrimary
                      ? "bg-blue-600 hover:bg-blue-700"
                      : "border-gray-200 text-gray-700 hover:bg-gray-50 hover:text-gray-900"
                  )}
                  onClick={() => onAction?.(action)}
                >
                  {action.type === "reschedule" && <Calendar className="h-4 w-4 mr-2.5 opacity-70" />}
                  {action.type === "callback" && <Phone className="h-4 w-4 mr-2.5 opacity-70" />}
                  {action.type === "message" && <MessageCircle className="h-4 w-4 mr-2.5 opacity-70" />}
                  <span className="font-medium">{action.label}</span>
                </Button>
              ))}
            </CardContent>
          </Card>

          {/* Media Section (for calls) */}
          {item.channel === "zoice" && (
            <Card className="border-gray-200 shadow-sm">
              <CardHeader className="pb-3 bg-gray-50/50 border-b border-gray-100">
                <CardTitle className="text-xs font-bold uppercase tracking-wider text-gray-500">
                  Recording
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4">
                <AudioPlayer
                  url={item.metadata?.recordingUrl as string}
                  duration={item.metadata?.callDuration as number}
                />
              </CardContent>
            </Card>
          )}

          {/* Transcript */}
          {item.channel === "zoice" && (
            <Card className="border-gray-200 shadow-sm">
              <CardHeader className="pb-3 bg-gray-50/50 border-b border-gray-100">
                <CardTitle className="text-xs font-bold uppercase tracking-wider text-gray-500">
                  Transcript
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4">
                <TranscriptView transcript={mockTranscript} />
              </CardContent>
            </Card>
          )}

          {/* Attachments */}
          {item.attachments && item.attachments.length > 0 && (
            <Card className="border-gray-200 shadow-sm">
              <CardHeader className="pb-3 bg-gray-50/50 border-b border-gray-100">
                <CardTitle className="text-xs font-bold uppercase tracking-wider text-gray-500">
                  Attachments
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-2">
                {item.attachments.map((attachment) => (
                  <div
                    key={attachment.id}
                    className="flex items-center justify-between p-3 bg-gray-50 border border-gray-100 rounded-lg group hover:border-blue-200 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-white rounded-md border border-gray-200 text-blue-600">
                        <FileText className="h-4 w-4" />
                      </div>
                      <span className="text-sm font-medium text-gray-700">{attachment.name}</span>
                    </div>
                    <Button variant="ghost" size="sm" className="opacity-0 group-hover:opacity-100 transition-opacity">
                      <ExternalLink className="h-4 w-4 text-gray-500" />
                    </Button>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>
      </ScrollArea>

      {/* Footer Actions */}
      <div className="p-4 border-t border-gray-200 bg-white sticky bottom-0 z-10">
        <div className="flex gap-2">
          <Button className="flex-1 bg-green-600 hover:bg-green-700 text-white shadow-sm">
            <Send className="h-4 w-4 mr-2" />
            WhatsApp
          </Button>
          <Button variant="outline" className="border-gray-200 text-gray-700 hover:bg-gray-50">
            <Phone className="h-4 w-4 mr-2" />
            Call
          </Button>
          <Button variant="outline" className="border-gray-200 text-gray-700 hover:bg-gray-50" asChild>
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
