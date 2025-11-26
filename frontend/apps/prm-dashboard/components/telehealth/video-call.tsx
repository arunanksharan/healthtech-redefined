"use client";

// Video Call Interface Component
// EPIC-UX-008: Telehealth Experience

import React, { useEffect, useRef, useState, useCallback } from "react";
import { format, differenceInSeconds } from "date-fns";
import {
  Mic,
  MicOff,
  Video,
  VideoOff,
  MonitorUp,
  MonitorOff,
  Phone,
  PhoneOff,
  MessageSquare,
  FileText,
  Pill,
  Beaker,
  Settings,
  MoreVertical,
  Maximize2,
  Minimize2,
  PictureInPicture,
  Users,
  Sparkles,
  Loader2,
  Check,
  X,
  Volume2,
  VolumeX,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  Copy,
  Plus,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  useTelehealthStore,
  type Participant,
  type TranscriptionEntry,
  type AISuggestion,
  type ChatMessage,
} from "@/lib/store/telehealth-store";

// ============================================================================
// Types
// ============================================================================

interface VideoCallProps {
  sessionId: string;
  role: "provider" | "patient";
  onEnd: () => void;
  showPatientChart?: boolean;
  patientChartComponent?: React.ReactNode;
  enableRecording?: boolean;
  enableTranscription?: boolean;
}

// ============================================================================
// Sub-Components
// ============================================================================

// Call Timer
function CallTimer({ startTime }: { startTime: Date }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setElapsed(differenceInSeconds(new Date(), startTime));
    }, 1000);
    return () => clearInterval(interval);
  }, [startTime]);

  const hours = Math.floor(elapsed / 3600);
  const minutes = Math.floor((elapsed % 3600) / 60);
  const seconds = elapsed % 60;

  return (
    <span className="font-mono text-sm">
      {hours > 0 && `${hours}:`}
      {minutes.toString().padStart(2, "0")}:{seconds.toString().padStart(2, "0")}
    </span>
  );
}

// Video Tile
interface VideoTileProps {
  participant: Participant;
  stream?: MediaStream | null;
  isLocal: boolean;
  isLarge?: boolean;
}

function VideoTile({ participant, stream, isLocal, isLarge = false }: VideoTileProps) {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    }
  }, [stream]);

  return (
    <div
      className={cn(
        "relative bg-muted rounded-lg overflow-hidden",
        isLarge ? "w-full h-full" : "w-48 h-36"
      )}
    >
      {participant.videoEnabled && stream ? (
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted={isLocal}
          className="w-full h-full object-cover"
        />
      ) : (
        <div className="w-full h-full flex items-center justify-center bg-muted">
          <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center">
            <span className="text-2xl font-semibold text-primary">
              {participant.name
                .split(" ")
                .map((n) => n[0])
                .join("")
                .toUpperCase()}
            </span>
          </div>
        </div>
      )}

      {/* Participant Info */}
      <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs text-white bg-black/50 px-2 py-1 rounded">
            {participant.name} {isLocal && "(You)"}
          </span>
        </div>
        <div className="flex items-center gap-1">
          {!participant.audioEnabled && (
            <div className="p-1 bg-red-500 rounded">
              <MicOff className="h-3 w-3 text-white" />
            </div>
          )}
          {participant.isSpeaking && participant.audioEnabled && (
            <div className="p-1 bg-green-500 rounded animate-pulse">
              <Volume2 className="h-3 w-3 text-white" />
            </div>
          )}
        </div>
      </div>

      {/* Screen sharing indicator */}
      {participant.isScreenSharing && (
        <div className="absolute top-2 left-2">
          <Badge variant="secondary" className="text-xs">
            <MonitorUp className="h-3 w-3 mr-1" />
            Sharing Screen
          </Badge>
        </div>
      )}
    </div>
  );
}

// Control Button
interface ControlButtonProps {
  icon: React.ReactNode;
  activeIcon?: React.ReactNode;
  label: string;
  isActive?: boolean;
  isDestructive?: boolean;
  onClick: () => void;
  disabled?: boolean;
}

function ControlButton({
  icon,
  activeIcon,
  label,
  isActive = false,
  isDestructive = false,
  onClick,
  disabled = false,
}: ControlButtonProps) {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant={isDestructive ? "destructive" : isActive ? "secondary" : "outline"}
            size="icon"
            className={cn(
              "h-12 w-12 rounded-full",
              isDestructive && "bg-red-600 hover:bg-red-700"
            )}
            onClick={onClick}
            disabled={disabled}
          >
            {isActive && activeIcon ? activeIcon : icon}
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          <p>{label}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

// Chat Panel
interface ChatPanelProps {
  messages: ChatMessage[];
  onSend: (content: string) => void;
  onClose: () => void;
}

function ChatPanel({ messages, onSend, onClose }: ChatPanelProps) {
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = () => {
    if (input.trim()) {
      onSend(input.trim());
      setInput("");
    }
  };

  return (
    <Card className="w-80 h-full flex flex-col">
      <CardHeader className="py-3 px-4 flex flex-row items-center justify-between">
        <CardTitle className="text-sm flex items-center gap-2">
          <MessageSquare className="h-4 w-4" />
          Chat
        </CardTitle>
        <Button variant="ghost" size="icon" className="h-6 w-6" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </CardHeader>
      <ScrollArea ref={scrollRef} className="flex-1 p-4">
        <div className="space-y-3">
          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "text-sm",
                message.type === "system" && "text-center text-muted-foreground text-xs"
              )}
            >
              {message.type === "text" && (
                <>
                  <span className="font-medium">{message.senderName}: </span>
                  <span>{message.content}</span>
                </>
              )}
              {message.type === "system" && <span>{message.content}</span>}
            </div>
          ))}
        </div>
      </ScrollArea>
      <div className="p-3 border-t">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message..."
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            className="flex-1"
          />
          <Button size="icon" onClick={handleSend}>
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </Card>
  );
}

// AI Transcription Panel
interface TranscriptionPanelProps {
  transcription: TranscriptionEntry[];
  suggestions: AISuggestion[];
  onAcceptSuggestion: (id: string) => void;
  onRejectSuggestion: (id: string) => void;
  onClose: () => void;
}

function TranscriptionPanel({
  transcription,
  suggestions,
  onAcceptSuggestion,
  onRejectSuggestion,
  onClose,
}: TranscriptionPanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [transcription]);

  return (
    <Card className="w-96 h-full flex flex-col">
      <CardHeader className="py-3 px-4 flex flex-row items-center justify-between">
        <CardTitle className="text-sm flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-purple-600" />
          AI Assistant
        </CardTitle>
        <Button variant="ghost" size="icon" className="h-6 w-6" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </CardHeader>

      <div className="flex-1 overflow-hidden flex flex-col">
        {/* Live Transcription */}
        <div className="flex-1 overflow-hidden border-b">
          <div className="px-4 py-2 bg-muted/50 text-xs font-medium text-muted-foreground">
            LIVE TRANSCRIPTION
          </div>
          <ScrollArea ref={scrollRef} className="h-48 p-4">
            <div className="space-y-3">
              {transcription.map((entry) => (
                <div key={entry.id} className="text-sm">
                  <span
                    className={cn(
                      "font-medium",
                      entry.speakerRole === "provider"
                        ? "text-primary"
                        : "text-muted-foreground"
                    )}
                  >
                    {entry.speakerRole === "provider" ? "Doctor" : "Patient"}:
                  </span>{" "}
                  <span className="text-foreground">{entry.content}</span>
                </div>
              ))}
              {transcription.length === 0 && (
                <p className="text-sm text-muted-foreground text-center py-4">
                  Transcription will appear here...
                </p>
              )}
            </div>
          </ScrollArea>
        </div>

        {/* AI Suggestions */}
        <div className="flex-1 overflow-hidden">
          <div className="px-4 py-2 bg-muted/50 text-xs font-medium text-muted-foreground flex items-center gap-2">
            📝 AI SUGGESTED NOTES
          </div>
          <ScrollArea className="h-40 p-4">
            <div className="space-y-3">
              {suggestions.map((suggestion) => (
                <Card
                  key={suggestion.id}
                  className={cn(
                    "border-purple-200 bg-purple-50",
                    suggestion.accepted && "border-green-200 bg-green-50"
                  )}
                >
                  <CardContent className="p-3">
                    <p className="text-sm">{suggestion.content}</p>
                    {!suggestion.accepted && (
                      <div className="flex items-center gap-2 mt-2">
                        <Button
                          size="sm"
                          variant="secondary"
                          className="h-7 text-xs"
                          onClick={() => onAcceptSuggestion(suggestion.id)}
                        >
                          <Plus className="h-3 w-3 mr-1" />
                          Add to Note
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 text-xs"
                          onClick={() => onRejectSuggestion(suggestion.id)}
                        >
                          Ignore
                        </Button>
                      </div>
                    )}
                    {suggestion.accepted && (
                      <Badge variant="secondary" className="mt-2 text-xs bg-green-100 text-green-700">
                        <Check className="h-3 w-3 mr-1" />
                        Added
                      </Badge>
                    )}
                  </CardContent>
                </Card>
              ))}
              {suggestions.length === 0 && (
                <p className="text-sm text-muted-foreground text-center py-4">
                  AI suggestions will appear here based on the conversation...
                </p>
              )}
            </div>
          </ScrollArea>
        </div>
      </div>
    </Card>
  );
}

// Patient Chart Panel (Compact)
interface PatientChartPanelProps {
  patient: {
    id: string;
    name: string;
    mrn: string;
    dob: string;
  };
  onClose: () => void;
  onPrescribe: () => void;
  onOrderLab: () => void;
  onAddNote: () => void;
}

function PatientChartPanel({
  patient,
  onClose,
  onPrescribe,
  onOrderLab,
  onAddNote,
}: PatientChartPanelProps) {
  // Mock patient data
  const mockData = {
    allergies: ["Penicillin"],
    vitals: { bp: "142/90", hr: "76", weight: "185 lbs" },
    medications: [
      { name: "Metformin", dose: "1000mg BID" },
      { name: "Lisinopril", dose: "10mg daily" },
    ],
    recentLabs: { name: "A1C", value: "7.1%", date: "May 15" },
  };

  return (
    <Card className="w-80 h-full flex flex-col">
      <CardHeader className="py-3 px-4 flex flex-row items-center justify-between border-b">
        <div>
          <CardTitle className="text-sm">{patient.name}</CardTitle>
          <p className="text-xs text-muted-foreground">
            {new Date().getFullYear() - new Date(patient.dob).getFullYear()} y/o •
            MRN: {patient.mrn}
          </p>
        </div>
        <Button variant="ghost" size="icon" className="h-6 w-6" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </CardHeader>

      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {/* Allergies Alert */}
          {mockData.allergies.length > 0 && (
            <div className="flex items-center gap-2 p-2 bg-red-50 border border-red-200 rounded-lg">
              <AlertCircle className="h-4 w-4 text-red-600" />
              <span className="text-sm text-red-800">
                {mockData.allergies.join(", ")} Allergy
              </span>
            </div>
          )}

          {/* Recent Vitals */}
          <div>
            <h4 className="text-xs font-medium text-muted-foreground mb-2">
              RECENT VITALS (Nov 20)
            </h4>
            <p className="text-sm">
              BP: {mockData.vitals.bp} • HR: {mockData.vitals.hr} • Wt: {mockData.vitals.weight}
            </p>
          </div>

          {/* Current Medications */}
          <div>
            <h4 className="text-xs font-medium text-muted-foreground mb-2">
              CURRENT MEDS
            </h4>
            <ul className="space-y-1">
              {mockData.medications.map((med, i) => (
                <li key={i} className="text-sm">
                  • {med.name} {med.dose}
                </li>
              ))}
            </ul>
          </div>

          {/* Recent Labs */}
          <div>
            <h4 className="text-xs font-medium text-muted-foreground mb-2">
              RECENT LABS
            </h4>
            <p className="text-sm">
              {mockData.recentLabs.name}: {mockData.recentLabs.value} ({mockData.recentLabs.date})
            </p>
          </div>
        </div>
      </ScrollArea>

      {/* Quick Actions */}
      <div className="p-3 border-t grid grid-cols-2 gap-2">
        <Button variant="outline" size="sm" onClick={onPrescribe}>
          <Pill className="h-4 w-4 mr-1" />
          Prescribe
        </Button>
        <Button variant="outline" size="sm" onClick={onOrderLab}>
          <Beaker className="h-4 w-4 mr-1" />
          Order Lab
        </Button>
        <Button variant="outline" size="sm" className="col-span-2" onClick={onAddNote}>
          <FileText className="h-4 w-4 mr-1" />
          Add Note
        </Button>
      </div>
    </Card>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function VideoCall({
  sessionId,
  role,
  onEnd,
  showPatientChart = true,
  patientChartComponent,
  enableRecording = true,
  enableTranscription = true,
}: VideoCallProps) {
  const [showEndDialog, setShowEndDialog] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [callStartTime] = useState(new Date());

  const {
    activeSession,
    localParticipant,
    remoteParticipant,
    deviceStatus,
    recording,
    chatMessages,
    transcription,
    aiSuggestions,
    showChat,
    showTranscription,
    showPatientChart: chartVisible,
    isScreenSharing,
    toggleVideo,
    toggleAudio,
    startScreenShare,
    stopScreenShare,
    sendChatMessage,
    toggleChat,
    toggleTranscription,
    togglePatientChart: toggleChart,
    acceptAISuggestion,
    rejectAISuggestion,
    startRecording,
    stopRecording,
    endSession,
  } = useTelehealthStore();

  // Handle end session
  const handleEndSession = useCallback(async () => {
    await endSession();
    onEnd();
  }, [endSession, onEnd]);

  // Toggle fullscreen
  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  }, []);

  if (!activeSession || !localParticipant) {
    return (
      <div className="h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-black">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-2 bg-black/80 text-white">
        <div className="flex items-center gap-4">
          <h1 className="text-sm font-medium">Telehealth Session</h1>
          <div className="flex items-center gap-2">
            <CallTimer startTime={callStartTime} />
            {recording?.status === "recording" && (
              <Badge variant="destructive" className="text-xs animate-pulse">
                🔴 REC
              </Badge>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            className="text-white hover:bg-white/10"
            onClick={toggleFullscreen}
          >
            {isFullscreen ? (
              <Minimize2 className="h-4 w-4" />
            ) : (
              <Maximize2 className="h-4 w-4" />
            )}
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="text-white hover:bg-white/10">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => navigator.clipboard.writeText(sessionId)}>
                <Copy className="h-4 w-4 mr-2" />
                Copy Session ID
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Settings className="h-4 w-4 mr-2" />
                Settings
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              {enableRecording && (
                <DropdownMenuItem
                  onClick={() =>
                    recording?.status === "recording" ? stopRecording() : startRecording()
                  }
                >
                  {recording?.status === "recording" ? "⏹️ Stop Recording" : "⏺️ Start Recording"}
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Video Area */}
        <div className="flex-1 relative">
          {/* Remote Video (Large) */}
          {remoteParticipant && (
            <VideoTile
              participant={remoteParticipant}
              stream={deviceStatus.camera.stream} // In production, this would be remote stream
              isLocal={false}
              isLarge
            />
          )}

          {/* Local Video (Picture-in-Picture) */}
          <div className="absolute bottom-4 right-4">
            <VideoTile
              participant={localParticipant}
              stream={deviceStatus.camera.stream}
              isLocal
            />
          </div>

          {/* Controls */}
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-3 p-3 bg-black/60 backdrop-blur rounded-full">
            <ControlButton
              icon={<Mic className="h-5 w-5" />}
              activeIcon={<MicOff className="h-5 w-5" />}
              label={localParticipant.audioEnabled ? "Mute" : "Unmute"}
              isActive={!localParticipant.audioEnabled}
              onClick={toggleAudio}
            />
            <ControlButton
              icon={<Video className="h-5 w-5" />}
              activeIcon={<VideoOff className="h-5 w-5" />}
              label={localParticipant.videoEnabled ? "Stop Video" : "Start Video"}
              isActive={!localParticipant.videoEnabled}
              onClick={toggleVideo}
            />
            {role === "provider" && (
              <>
                <ControlButton
                  icon={<MonitorUp className="h-5 w-5" />}
                  activeIcon={<MonitorOff className="h-5 w-5" />}
                  label={isScreenSharing ? "Stop Sharing" : "Share Screen"}
                  isActive={isScreenSharing}
                  onClick={() => (isScreenSharing ? stopScreenShare() : startScreenShare())}
                />
                <ControlButton
                  icon={<FileText className="h-5 w-5" />}
                  label="Patient Chart"
                  isActive={chartVisible}
                  onClick={toggleChart}
                />
                <ControlButton
                  icon={<Pill className="h-5 w-5" />}
                  label="Prescribe"
                  onClick={() => {}}
                />
              </>
            )}
            <ControlButton
              icon={<MessageSquare className="h-5 w-5" />}
              label="Chat"
              isActive={showChat}
              onClick={toggleChat}
            />
            {role === "provider" && enableTranscription && (
              <ControlButton
                icon={<Sparkles className="h-5 w-5" />}
                label="AI Assistant"
                isActive={showTranscription}
                onClick={toggleTranscription}
              />
            )}
            <ControlButton
              icon={<PhoneOff className="h-5 w-5" />}
              label="End Call"
              isDestructive
              onClick={() => setShowEndDialog(true)}
            />
          </div>
        </div>

        {/* Side Panels */}
        <div className="flex">
          {/* Chat Panel */}
          {showChat && (
            <ChatPanel
              messages={chatMessages}
              onSend={sendChatMessage}
              onClose={toggleChat}
            />
          )}

          {/* AI Transcription Panel */}
          {showTranscription && role === "provider" && enableTranscription && (
            <TranscriptionPanel
              transcription={transcription}
              suggestions={aiSuggestions}
              onAcceptSuggestion={acceptAISuggestion}
              onRejectSuggestion={rejectAISuggestion}
              onClose={toggleTranscription}
            />
          )}

          {/* Patient Chart Panel */}
          {chartVisible && role === "provider" && showPatientChart && (
            <PatientChartPanel
              patient={activeSession.patient}
              onClose={toggleChart}
              onPrescribe={() => {}}
              onOrderLab={() => {}}
              onAddNote={() => {}}
            />
          )}
        </div>
      </div>

      {/* End Session Dialog */}
      <Dialog open={showEndDialog} onOpenChange={setShowEndDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>End Session</DialogTitle>
            <DialogDescription>
              Are you sure you want to end this telehealth session?
              {role === "provider" && " You'll be redirected to complete documentation."}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEndDialog(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleEndSession}>
              End Session
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ============================================================================
// Patient Video Call (Simplified)
// ============================================================================

export function PatientVideoCall({
  sessionId,
  onEnd,
}: {
  sessionId: string;
  onEnd: () => void;
}) {
  return (
    <VideoCall
      sessionId={sessionId}
      role="patient"
      onEnd={onEnd}
      showPatientChart={false}
      enableTranscription={false}
    />
  );
}

// ============================================================================
// Video Call Skeleton
// ============================================================================

export function VideoCallSkeleton() {
  return (
    <div className="h-screen flex flex-col bg-black animate-pulse">
      <div className="h-12 bg-gray-900" />
      <div className="flex-1 flex">
        <div className="flex-1 bg-gray-800" />
        <div className="w-80 bg-gray-900" />
      </div>
    </div>
  );
}

export default VideoCall;
