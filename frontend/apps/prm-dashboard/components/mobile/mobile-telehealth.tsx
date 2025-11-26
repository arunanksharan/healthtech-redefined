"use client";

// Mobile Telehealth - Video Call Interface for Mobile
// EPIC-UX-012: Mobile Applications - Journey 12.3

import React, { useState, useEffect, useRef } from "react";
import { format } from "date-fns";
import {
  Mic, MicOff, Video, VideoOff, Phone, PhoneOff, MessageSquare,
  MoreVertical, Maximize2, Minimize2, FlipHorizontal, Settings,
  Volume2, VolumeX, ChevronUp, ChevronDown, Send, X, Loader2,
  AlertCircle, Clock, Shield, Users, Wifi, WifiOff,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from "@/components/ui/dropdown-menu";

// Call states
type CallState = "connecting" | "connected" | "reconnecting" | "ended";

// Chat message
interface ChatMessage {
  id: string;
  senderId: string;
  senderName: string;
  content: string;
  timestamp: string;
}

// Participant
interface Participant {
  id: string;
  name: string;
  role: "patient" | "provider" | "interpreter";
  avatar?: string;
  isMuted: boolean;
  isVideoOn: boolean;
  isHost?: boolean;
}

// Call info
interface CallInfo {
  id: string;
  appointmentId: string;
  startTime: string;
  duration: number;
  isRecording: boolean;
  participants: Participant[];
}

// Control button component
interface ControlButtonProps {
  icon: typeof Mic;
  activeIcon?: typeof MicOff;
  label: string;
  isActive?: boolean;
  isDestructive?: boolean;
  onClick: () => void;
  disabled?: boolean;
}

function ControlButton({
  icon: Icon,
  activeIcon: ActiveIcon,
  label,
  isActive = false,
  isDestructive = false,
  onClick,
  disabled = false,
}: ControlButtonProps) {
  const DisplayIcon = isActive && ActiveIcon ? ActiveIcon : Icon;

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "flex flex-col items-center gap-1 p-3 rounded-xl transition-colors",
        isDestructive
          ? "bg-red-500 text-white active:bg-red-600"
          : isActive
          ? "bg-muted text-muted-foreground"
          : "bg-muted/50 text-foreground active:bg-muted",
        disabled && "opacity-50 cursor-not-allowed"
      )}
    >
      <DisplayIcon className="h-6 w-6" />
      <span className="text-[10px]">{label}</span>
    </button>
  );
}

// Connection status indicator
function ConnectionStatus({ state }: { state: CallState }) {
  const config = {
    connecting: { label: "Connecting...", color: "text-amber-500", icon: Loader2 },
    connected: { label: "Connected", color: "text-green-500", icon: Wifi },
    reconnecting: { label: "Reconnecting...", color: "text-amber-500", icon: WifiOff },
    ended: { label: "Call Ended", color: "text-muted-foreground", icon: PhoneOff },
  };
  const c = config[state];

  return (
    <div className={cn("flex items-center gap-1 text-xs", c.color)}>
      <c.icon className={cn("h-3 w-3", state === "connecting" && "animate-spin")} />
      <span>{c.label}</span>
    </div>
  );
}

// Call timer
function CallTimer({ startTime }: { startTime: string }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const start = new Date(startTime).getTime();
    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - start) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, [startTime]);

  const minutes = Math.floor(elapsed / 60);
  const seconds = elapsed % 60;

  return (
    <div className="flex items-center gap-1 text-xs">
      <Clock className="h-3 w-3" />
      <span>{String(minutes).padStart(2, "0")}:{String(seconds).padStart(2, "0")}</span>
    </div>
  );
}

// Video placeholder
function VideoPlaceholder({ participant, isLarge = false }: { participant: Participant; isLarge?: boolean }) {
  return (
    <div className={cn(
      "relative bg-muted rounded-lg flex items-center justify-center",
      isLarge ? "aspect-video" : "aspect-video"
    )}>
      {participant.isVideoOn ? (
        <div className="w-full h-full bg-gradient-to-br from-slate-800 to-slate-900 rounded-lg flex items-center justify-center">
          {/* Video would render here */}
          <Avatar className={cn(isLarge ? "h-24 w-24" : "h-12 w-12")}>
            <AvatarFallback className={cn(isLarge ? "text-2xl" : "text-sm")}>
              {participant.name.split(" ").map(n => n[0]).join("")}
            </AvatarFallback>
          </Avatar>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-2">
          <Avatar className={cn(isLarge ? "h-24 w-24" : "h-12 w-12")}>
            <AvatarFallback className={cn(isLarge ? "text-2xl" : "text-sm")}>
              {participant.name.split(" ").map(n => n[0]).join("")}
            </AvatarFallback>
          </Avatar>
          <span className={cn("text-muted-foreground", isLarge ? "text-sm" : "text-xs")}>
            Video off
          </span>
        </div>
      )}

      {/* Name tag */}
      <div className="absolute bottom-2 left-2 flex items-center gap-1 bg-black/50 px-2 py-1 rounded">
        <span className="text-white text-xs">{participant.name}</span>
        {participant.isMuted && <MicOff className="h-3 w-3 text-red-400" />}
      </div>
    </div>
  );
}

// Chat panel
interface ChatPanelProps {
  messages: ChatMessage[];
  onSend: (message: string) => void;
  currentUserId: string;
}

function ChatPanel({ messages, onSend, currentUserId }: ChatPanelProps) {
  const [newMessage, setNewMessage] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    if (newMessage.trim()) {
      onSend(newMessage.trim());
      setNewMessage("");
    }
  };

  return (
    <div className="flex flex-col h-full">
      <ScrollArea className="flex-1 p-3" ref={scrollRef}>
        <div className="space-y-3">
          {messages.length === 0 ? (
            <p className="text-center text-sm text-muted-foreground py-8">
              No messages yet
            </p>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={cn(
                  "flex flex-col max-w-[80%]",
                  msg.senderId === currentUserId ? "ml-auto items-end" : "items-start"
                )}
              >
                <div
                  className={cn(
                    "rounded-lg px-3 py-2 text-sm",
                    msg.senderId === currentUserId
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted"
                  )}
                >
                  {msg.senderId !== currentUserId && (
                    <p className="text-xs font-medium mb-1">{msg.senderName}</p>
                  )}
                  <p>{msg.content}</p>
                </div>
                <span className="text-[10px] text-muted-foreground mt-1">
                  {format(new Date(msg.timestamp), "h:mm a")}
                </span>
              </div>
            ))
          )}
        </div>
      </ScrollArea>
      <div className="p-3 border-t">
        <div className="flex gap-2">
          <Input
            placeholder="Type a message..."
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
          />
          <Button size="icon" onClick={handleSend} disabled={!newMessage.trim()}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}

// Pre-call screen
interface PreCallScreenProps {
  appointment: {
    provider: string;
    specialty: string;
    visitType: string;
    scheduledTime: string;
  };
  onJoin: () => void;
  onCancel: () => void;
}

function PreCallScreen({ appointment, onJoin, onCancel }: PreCallScreenProps) {
  const [isVideoReady, setIsVideoReady] = useState(false);
  const [isAudioReady, setIsAudioReady] = useState(false);
  const [cameraOn, setCameraOn] = useState(true);
  const [micOn, setMicOn] = useState(true);

  useEffect(() => {
    // Simulate device check
    const timer = setTimeout(() => {
      setIsVideoReady(true);
      setIsAudioReady(true);
    }, 1500);
    return () => clearTimeout(timer);
  }, []);

  const isReady = isVideoReady && isAudioReady;

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <div className="p-4 border-b">
        <h1 className="text-lg font-semibold">Video Visit</h1>
        <p className="text-sm text-muted-foreground">{appointment.visitType} with {appointment.provider}</p>
      </div>

      {/* Video Preview */}
      <div className="flex-1 p-4 flex flex-col items-center justify-center">
        <div className="w-full max-w-sm aspect-video bg-slate-900 rounded-lg relative overflow-hidden mb-4">
          {cameraOn ? (
            <div className="w-full h-full flex items-center justify-center">
              <Avatar className="h-20 w-20">
                <AvatarFallback className="text-xl">You</AvatarFallback>
              </Avatar>
            </div>
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <VideoOff className="h-12 w-12 text-muted-foreground" />
            </div>
          )}

          {/* Preview controls */}
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-3">
            <button
              onClick={() => setMicOn(!micOn)}
              className={cn(
                "p-3 rounded-full",
                micOn ? "bg-muted" : "bg-red-500 text-white"
              )}
            >
              {micOn ? <Mic className="h-5 w-5" /> : <MicOff className="h-5 w-5" />}
            </button>
            <button
              onClick={() => setCameraOn(!cameraOn)}
              className={cn(
                "p-3 rounded-full",
                cameraOn ? "bg-muted" : "bg-red-500 text-white"
              )}
            >
              {cameraOn ? <Video className="h-5 w-5" /> : <VideoOff className="h-5 w-5" />}
            </button>
          </div>
        </div>

        {/* Device Status */}
        <div className="space-y-2 mb-6">
          <div className="flex items-center gap-2">
            {isAudioReady ? (
              <Badge variant="outline" className="text-green-600 border-green-200">
                <Mic className="h-3 w-3 mr-1" /> Microphone ready
              </Badge>
            ) : (
              <Badge variant="outline" className="text-amber-600 border-amber-200">
                <Loader2 className="h-3 w-3 mr-1 animate-spin" /> Checking mic...
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-2">
            {isVideoReady ? (
              <Badge variant="outline" className="text-green-600 border-green-200">
                <Video className="h-3 w-3 mr-1" /> Camera ready
              </Badge>
            ) : (
              <Badge variant="outline" className="text-amber-600 border-amber-200">
                <Loader2 className="h-3 w-3 mr-1 animate-spin" /> Checking camera...
              </Badge>
            )}
          </div>
        </div>

        {/* Join Button */}
        <div className="w-full max-w-sm space-y-3">
          <Button
            size="lg"
            className="w-full"
            onClick={onJoin}
            disabled={!isReady}
          >
            {isReady ? "Join Video Visit" : "Preparing..."}
          </Button>
          <Button variant="outline" className="w-full" onClick={onCancel}>
            Cancel
          </Button>
        </div>
      </div>

      {/* Tips */}
      <div className="p-4 border-t">
        <p className="text-xs text-muted-foreground text-center">
          <Shield className="h-3 w-3 inline mr-1" />
          Your visit is private and HIPAA-compliant
        </p>
      </div>
    </div>
  );
}

// Post-call summary
interface PostCallScreenProps {
  callInfo: CallInfo;
  onClose: () => void;
}

function PostCallScreen({ callInfo, onClose }: PostCallScreenProps) {
  const duration = Math.floor(callInfo.duration / 60);

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6">
      <div className="h-16 w-16 rounded-full bg-green-100 flex items-center justify-center mb-4">
        <Phone className="h-8 w-8 text-green-600" />
      </div>
      <h1 className="text-xl font-semibold mb-2">Visit Complete</h1>
      <p className="text-muted-foreground text-center mb-6">
        Your video visit lasted {duration} minute{duration !== 1 ? "s" : ""}
      </p>

      <Card className="w-full max-w-sm mb-6">
        <CardContent className="p-4 space-y-3">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Provider</span>
            <span className="font-medium">{callInfo.participants.find(p => p.role === "provider")?.name}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Duration</span>
            <span className="font-medium">{duration} min</span>
          </div>
          {callInfo.isRecording && (
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Recording</span>
              <Badge variant="secondary" className="text-xs">Saved</Badge>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="w-full max-w-sm space-y-3">
        <Button className="w-full" onClick={onClose}>
          Return to Home
        </Button>
        <Button variant="outline" className="w-full">
          View Visit Summary
        </Button>
      </div>
    </div>
  );
}

// Main Mobile Telehealth Component
export function MobileTelehealth({
  appointmentId,
  onEnd,
}: {
  appointmentId: string;
  onEnd: () => void;
}) {
  const [callState, setCallState] = useState<CallState>("connecting");
  const [phase, setPhase] = useState<"pre" | "call" | "post">("pre");
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoOn, setIsVideoOn] = useState(true);
  const [isSpeakerOn, setIsSpeakerOn] = useState(true);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isControlsVisible, setIsControlsVisible] = useState(true);
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  const currentUser: Participant = {
    id: "patient-001",
    name: "John Doe",
    role: "patient",
    isMuted,
    isVideoOn,
  };

  const provider: Participant = {
    id: "doc-001",
    name: "Dr. Rohit Sharma",
    role: "provider",
    isMuted: false,
    isVideoOn: true,
    isHost: true,
  };

  const [callInfo, setCallInfo] = useState<CallInfo>({
    id: `call-${Date.now()}`,
    appointmentId,
    startTime: new Date().toISOString(),
    duration: 0,
    isRecording: true,
    participants: [currentUser, provider],
  });

  // Simulate connection
  useEffect(() => {
    if (phase === "call") {
      const timer = setTimeout(() => {
        setCallState("connected");
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [phase]);

  // Track duration
  useEffect(() => {
    if (callState === "connected") {
      const interval = setInterval(() => {
        setCallInfo((prev) => ({ ...prev, duration: prev.duration + 1 }));
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [callState]);

  // Auto-hide controls
  useEffect(() => {
    if (phase === "call" && isControlsVisible) {
      const timer = setTimeout(() => {
        if (!isChatOpen) setIsControlsVisible(false);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [phase, isControlsVisible, isChatOpen]);

  const handleJoin = () => {
    setPhase("call");
    setCallState("connecting");
  };

  const handleEndCall = () => {
    setCallState("ended");
    setTimeout(() => setPhase("post"), 500);
  };

  const handleSendMessage = (content: string) => {
    const newMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      senderId: currentUser.id,
      senderName: currentUser.name,
      content,
      timestamp: new Date().toISOString(),
    };
    setMessages([...messages, newMsg]);
  };

  // Pre-call screen
  if (phase === "pre") {
    return (
      <PreCallScreen
        appointment={{
          provider: provider.name,
          specialty: "Cardiology",
          visitType: "Follow-up",
          scheduledTime: new Date().toISOString(),
        }}
        onJoin={handleJoin}
        onCancel={onEnd}
      />
    );
  }

  // Post-call screen
  if (phase === "post") {
    return (
      <PostCallScreen
        callInfo={callInfo}
        onClose={onEnd}
      />
    );
  }

  // In-call screen
  return (
    <div
      className="min-h-screen bg-black relative"
      onClick={() => setIsControlsVisible(!isControlsVisible)}
    >
      {/* Recording indicator */}
      {callInfo.isRecording && (
        <div className="absolute top-4 right-4 z-20 flex items-center gap-1 bg-red-500 text-white px-2 py-1 rounded text-xs">
          <div className="h-2 w-2 rounded-full bg-white animate-pulse" />
          REC
        </div>
      )}

      {/* Status bar */}
      <div
        className={cn(
          "absolute top-4 left-4 z-20 transition-opacity",
          isControlsVisible ? "opacity-100" : "opacity-0"
        )}
      >
        <div className="flex items-center gap-3">
          <ConnectionStatus state={callState} />
          {callState === "connected" && <CallTimer startTime={callInfo.startTime} />}
        </div>
      </div>

      {/* Main video (Provider) */}
      <div className="absolute inset-0 flex items-center justify-center">
        <VideoPlaceholder participant={provider} isLarge />
      </div>

      {/* Self video (PIP) */}
      <div className="absolute top-16 right-4 w-24 z-10">
        <VideoPlaceholder participant={{ ...currentUser, isMuted, isVideoOn }} />
      </div>

      {/* Controls */}
      <div
        className={cn(
          "absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/80 to-transparent transition-transform",
          isControlsVisible ? "translate-y-0" : "translate-y-full"
        )}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-center gap-4 mb-4">
          <ControlButton
            icon={Mic}
            activeIcon={MicOff}
            label={isMuted ? "Unmute" : "Mute"}
            isActive={isMuted}
            onClick={() => setIsMuted(!isMuted)}
          />
          <ControlButton
            icon={Video}
            activeIcon={VideoOff}
            label={isVideoOn ? "Stop Video" : "Start Video"}
            isActive={!isVideoOn}
            onClick={() => setIsVideoOn(!isVideoOn)}
          />
          <ControlButton
            icon={MessageSquare}
            label="Chat"
            onClick={() => setIsChatOpen(true)}
          />
          <ControlButton
            icon={Phone}
            label="End"
            isDestructive
            onClick={handleEndCall}
          />
        </div>

        {/* More options */}
        <div className="flex justify-center">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="text-white">
                <MoreVertical className="h-4 w-4 mr-1" /> More
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem onClick={() => setIsSpeakerOn(!isSpeakerOn)}>
                {isSpeakerOn ? <Volume2 className="h-4 w-4 mr-2" /> : <VolumeX className="h-4 w-4 mr-2" />}
                {isSpeakerOn ? "Speaker On" : "Speaker Off"}
              </DropdownMenuItem>
              <DropdownMenuItem>
                <FlipHorizontal className="h-4 w-4 mr-2" /> Flip Camera
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem>
                <Users className="h-4 w-4 mr-2" /> Participants ({callInfo.participants.length})
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Chat drawer */}
      <Dialog open={isChatOpen} onOpenChange={setIsChatOpen}>
        <DialogContent className="h-[70vh] flex flex-col p-0">
          <DialogHeader className="p-4 border-b">
            <DialogTitle>Chat</DialogTitle>
          </DialogHeader>
          <ChatPanel
            messages={messages}
            onSend={handleSendMessage}
            currentUserId={currentUser.id}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}

// Waiting room component
export function TelehealthWaitingRoom({
  appointment,
  onProviderReady,
  onCancel,
}: {
  appointment: {
    id: string;
    provider: string;
    scheduledTime: string;
  };
  onProviderReady: () => void;
  onCancel: () => void;
}) {
  const [waitTime, setWaitTime] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setWaitTime((prev) => prev + 1);
    }, 1000);

    // Simulate provider joining
    const timer = setTimeout(onProviderReady, 5000);

    return () => {
      clearInterval(interval);
      clearTimeout(timer);
    };
  }, [onProviderReady]);

  const minutes = Math.floor(waitTime / 60);
  const seconds = waitTime % 60;

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6">
      <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
        <Loader2 className="h-8 w-8 text-primary animate-spin" />
      </div>
      <h1 className="text-xl font-semibold mb-2">Waiting for Provider</h1>
      <p className="text-muted-foreground text-center mb-2">
        {appointment.provider} will join shortly
      </p>
      <p className="text-sm text-muted-foreground mb-6">
        Wait time: {minutes}:{String(seconds).padStart(2, "0")}
      </p>

      <Button variant="outline" onClick={onCancel}>
        Leave Waiting Room
      </Button>
    </div>
  );
}

export default MobileTelehealth;
