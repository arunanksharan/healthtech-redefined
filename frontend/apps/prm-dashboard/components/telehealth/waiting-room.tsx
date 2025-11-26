"use client";

// Virtual Waiting Room Component
// EPIC-UX-008: Telehealth Experience

import React, { useEffect, useState, useRef } from "react";
import { format, differenceInMinutes, differenceInSeconds } from "date-fns";
import {
  Clock,
  User,
  Camera,
  CameraOff,
  Mic,
  MicOff,
  Settings,
  HelpCircle,
  LogOut,
  Check,
  Loader2,
  Info,
  Volume2,
  Heart,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useTelehealthStore } from "@/lib/store/telehealth-store";

// ============================================================================
// Types
// ============================================================================

interface WaitingRoomProps {
  sessionId: string;
  patientName: string;
  providerName: string;
  providerSpecialty?: string;
  appointmentTime: Date;
  onJoinCall: () => void;
  onLeave: () => void;
  position?: number;
  estimatedWait?: number; // seconds
  hospitalName?: string;
  hospitalLogo?: string;
}

// ============================================================================
// Sub-Components
// ============================================================================

function WaitingAnimation() {
  const [dots, setDots] = useState(1);

  useEffect(() => {
    const interval = setInterval(() => {
      setDots((prev) => (prev % 3) + 1);
    }, 500);
    return () => clearInterval(interval);
  }, []);

  return (
    <span className="inline-flex w-6">
      {Array.from({ length: dots }).map((_, i) => (
        <span key={i}>.</span>
      ))}
    </span>
  );
}

function WaitTimer({ startTime }: { startTime: Date }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setElapsed(differenceInSeconds(new Date(), startTime));
    }, 1000);
    return () => clearInterval(interval);
  }, [startTime]);

  const minutes = Math.floor(elapsed / 60);
  const seconds = elapsed % 60;

  return (
    <span className="font-mono">
      {minutes}:{seconds.toString().padStart(2, "0")}
    </span>
  );
}

interface CamerPreviewMiniProps {
  stream: MediaStream | null;
  isOn: boolean;
}

function CameraPreviewMini({ stream, isOn }: CamerPreviewMiniProps) {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    }
  }, [stream]);

  if (!isOn || !stream) {
    return (
      <div className="w-full h-full bg-muted rounded-lg flex items-center justify-center">
        <CameraOff className="h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

  return (
    <video
      ref={videoRef}
      autoPlay
      playsInline
      muted
      className="w-full h-full rounded-lg object-cover"
    />
  );
}

interface WaitingTipsProps {
  tips: string[];
}

function WaitingTips({ tips }: WaitingTipsProps) {
  const [currentTip, setCurrentTip] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTip((prev) => (prev + 1) % tips.length);
    }, 5000);
    return () => clearInterval(interval);
  }, [tips.length]);

  return (
    <div className="space-y-2">
      <h4 className="text-sm font-medium flex items-center gap-2">
        <Heart className="h-4 w-4 text-primary" />
        While you wait
      </h4>
      <p className="text-sm text-muted-foreground animate-fade-in">
        {tips[currentTip]}
      </p>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function WaitingRoom({
  sessionId,
  patientName,
  providerName,
  providerSpecialty,
  appointmentTime,
  onJoinCall,
  onLeave,
  position = 1,
  estimatedWait = 300,
  hospitalName = "Healthcare Clinic",
  hospitalLogo,
}: WaitingRoomProps) {
  const [showLeaveDialog, setShowLeaveDialog] = useState(false);
  const [showSettingsDialog, setShowSettingsDialog] = useState(false);
  const [cameraOn, setCameraOn] = useState(true);
  const [micOn, setMicOn] = useState(true);
  const [waitStartTime] = useState(new Date());
  const [isProviderJoining, setIsProviderJoining] = useState(false);

  const { deviceStatus, patientWaitingStatus } = useTelehealthStore();

  // Simulate provider joining after some time (for demo)
  useEffect(() => {
    const timeout = setTimeout(() => {
      setIsProviderJoining(true);
      setTimeout(onJoinCall, 2000);
    }, 10000); // Provider "joins" after 10 seconds for demo

    return () => clearTimeout(timeout);
  }, [onJoinCall]);

  const waitingTips = [
    "Make sure you're in a quiet, private space",
    "Have your medication list ready if applicable",
    "Write down any questions you want to ask",
    "Ensure good lighting so the doctor can see you clearly",
    "Have your insurance card ready if needed",
    "Close other apps to improve video quality",
  ];

  const estimatedMinutes = Math.ceil(estimatedWait / 60);

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/30 flex flex-col">
      {/* Header */}
      <header className="p-4 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            {hospitalLogo ? (
              <img src={hospitalLogo} alt={hospitalName} className="h-8" />
            ) : (
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <span className="text-primary-foreground font-bold">🏥</span>
              </div>
            )}
            <span className="font-semibold">{hospitalName}</span>
          </div>
          <div className="flex items-center gap-2">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setShowSettingsDialog(true)}
                  >
                    <Settings className="h-5 w-5" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Settings</TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="ghost" size="icon">
                    <HelpCircle className="h-5 w-5" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Need help?</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center p-6">
        <div className="max-w-lg w-full space-y-6 text-center">
          {/* Status Message */}
          <div className="space-y-2">
            {isProviderJoining ? (
              <>
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-100 text-green-800 rounded-full">
                  <Check className="h-5 w-5" />
                  <span className="font-medium">Doctor is joining</span>
                </div>
                <h1 className="text-2xl font-semibold mt-4">
                  Connecting you to {providerName}
                  <WaitingAnimation />
                </h1>
              </>
            ) : (
              <>
                <h1 className="text-2xl font-semibold">
                  You're in the waiting room
                </h1>
                <p className="text-lg text-muted-foreground">
                  {providerName} will be with you shortly
                </p>
              </>
            )}
          </div>

          {/* Waiting Status Card */}
          <Card className="relative overflow-hidden">
            <CardContent className="p-6">
              {/* Progress Animation */}
              <div className="absolute top-0 left-0 right-0 h-1 bg-muted">
                <div className="h-full bg-primary animate-pulse w-1/3" />
              </div>

              <div className="flex items-center justify-center gap-8 my-6">
                <div className="text-center">
                  <div className="text-4xl mb-2">🧘</div>
                  <p className="text-sm text-muted-foreground">Please relax</p>
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-center gap-2 text-sm">
                  <User className="h-4 w-4 text-muted-foreground" />
                  <span>Your position: {position} of {position}</span>
                </div>
                <div className="flex items-center justify-center gap-2 text-sm">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <span>
                    Estimated wait: &lt; {estimatedMinutes} minute{estimatedMinutes !== 1 ? "s" : ""}
                  </span>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t">
                <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                  <Clock className="h-4 w-4" />
                  <span>Waiting: </span>
                  <WaitTimer startTime={waitStartTime} />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Tips */}
          <Card>
            <CardContent className="p-4">
              <WaitingTips tips={waitingTips} />
            </CardContent>
          </Card>

          {/* Camera Preview */}
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm flex items-center gap-2">
                  <Camera className="h-4 w-4" />
                  Your camera is on
                </span>
                <span className="text-xs text-muted-foreground">
                  Only visible to doctor when call starts
                </span>
              </div>
              <div className="relative aspect-video max-w-xs mx-auto bg-muted rounded-lg overflow-hidden">
                <CameraPreviewMini
                  stream={deviceStatus.camera.stream}
                  isOn={cameraOn}
                />
                {/* Controls overlay */}
                <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex items-center gap-2">
                  <Button
                    variant={cameraOn ? "secondary" : "destructive"}
                    size="sm"
                    onClick={() => setCameraOn(!cameraOn)}
                  >
                    {cameraOn ? (
                      <Camera className="h-4 w-4" />
                    ) : (
                      <CameraOff className="h-4 w-4" />
                    )}
                  </Button>
                  <Button
                    variant={micOn ? "secondary" : "destructive"}
                    size="sm"
                    onClick={() => setMicOn(!micOn)}
                  >
                    {micOn ? (
                      <Mic className="h-4 w-4" />
                    ) : (
                      <MicOff className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Leave Button */}
          <Button
            variant="ghost"
            className="text-muted-foreground"
            onClick={() => setShowLeaveDialog(true)}
          >
            <LogOut className="h-4 w-4 mr-2" />
            Leave Waiting Room
          </Button>
        </div>
      </main>

      {/* Leave Confirmation Dialog */}
      <Dialog open={showLeaveDialog} onOpenChange={setShowLeaveDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Leave Waiting Room?</DialogTitle>
            <DialogDescription>
              If you leave, you will need to rejoin the waiting room when you're ready.
              Your appointment will not be cancelled.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowLeaveDialog(false)}>
              Stay
            </Button>
            <Button variant="destructive" onClick={onLeave}>
              Leave
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Settings Dialog */}
      <Dialog open={showSettingsDialog} onOpenChange={setShowSettingsDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Device Settings</DialogTitle>
            <DialogDescription>
              Adjust your camera, microphone, and speaker settings
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="flex items-center justify-between">
              <span className="text-sm">Camera</span>
              <Button
                variant={cameraOn ? "default" : "secondary"}
                size="sm"
                onClick={() => setCameraOn(!cameraOn)}
              >
                {cameraOn ? "On" : "Off"}
              </Button>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Microphone</span>
              <Button
                variant={micOn ? "default" : "secondary"}
                size="sm"
                onClick={() => setMicOn(!micOn)}
              >
                {micOn ? "On" : "Off"}
              </Button>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Test Speakers</span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  // Play test sound
                  const audio = new AudioContext();
                  const osc = audio.createOscillator();
                  const gain = audio.createGain();
                  osc.connect(gain);
                  gain.connect(audio.destination);
                  gain.gain.value = 0.1;
                  osc.frequency.value = 440;
                  osc.start();
                  setTimeout(() => osc.stop(), 300);
                }}
              >
                <Volume2 className="h-4 w-4 mr-1" />
                Test
              </Button>
            </div>
          </div>
          <DialogFooter>
            <Button onClick={() => setShowSettingsDialog(false)}>Done</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ============================================================================
// Provider Waiting Room View
// ============================================================================

interface ProviderWaitingViewProps {
  waitingPatients: {
    sessionId: string;
    patient: {
      id: string;
      name: string;
      photo?: string;
    };
    appointmentTime: string;
    reason: string;
    waitingDuration: number;
    deviceCheckPassed: boolean;
  }[];
  onStartSession: (sessionId: string) => void;
  onViewChart: (patientId: string) => void;
}

export function ProviderWaitingView({
  waitingPatients,
  onStartSession,
  onViewChart,
}: ProviderWaitingViewProps) {
  return (
    <div className="space-y-3">
      {waitingPatients.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          <Clock className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>No patients waiting</p>
        </div>
      ) : (
        waitingPatients.map((patient) => (
          <Card key={patient.sessionId}>
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                    {patient.patient.photo ? (
                      <img
                        src={patient.patient.photo}
                        alt={patient.patient.name}
                        className="w-10 h-10 rounded-full"
                      />
                    ) : (
                      <User className="h-5 w-5 text-primary" />
                    )}
                  </div>
                  <div>
                    <h4 className="font-medium">{patient.patient.name}</h4>
                    <p className="text-sm text-muted-foreground">
                      {patient.reason} • {format(new Date(patient.appointmentTime), "h:mm a")}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      {patient.deviceCheckPassed ? (
                        <Badge variant="secondary" className="text-xs bg-green-100 text-green-700">
                          <Check className="h-3 w-3 mr-1" />
                          Ready
                        </Badge>
                      ) : (
                        <Badge variant="secondary" className="text-xs bg-amber-100 text-amber-700">
                          <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                          Device check...
                        </Badge>
                      )}
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {Math.floor(patient.waitingDuration / 60)} min
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex flex-col gap-2">
                  <Button
                    size="sm"
                    onClick={() => onStartSession(patient.sessionId)}
                    disabled={!patient.deviceCheckPassed}
                  >
                    ▶️ Start Session
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onViewChart(patient.patient.id)}
                  >
                    📋 View Chart
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))
      )}
    </div>
  );
}

// ============================================================================
// Waiting Room Skeleton
// ============================================================================

export function WaitingRoomSkeleton() {
  return (
    <div className="min-h-screen flex flex-col animate-pulse">
      <div className="p-4 border-b">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-muted rounded-lg" />
            <div className="h-5 w-32 bg-muted rounded" />
          </div>
          <div className="flex gap-2">
            <div className="w-9 h-9 bg-muted rounded" />
            <div className="w-9 h-9 bg-muted rounded" />
          </div>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-6">
        <div className="max-w-lg w-full space-y-6">
          <div className="text-center space-y-2">
            <div className="h-8 w-64 bg-muted rounded mx-auto" />
            <div className="h-5 w-48 bg-muted rounded mx-auto" />
          </div>

          <div className="border rounded-lg p-6 space-y-4">
            <div className="h-24 bg-muted rounded" />
            <div className="space-y-2">
              <div className="h-4 w-32 bg-muted rounded mx-auto" />
              <div className="h-4 w-40 bg-muted rounded mx-auto" />
            </div>
          </div>

          <div className="border rounded-lg p-4">
            <div className="h-4 w-24 bg-muted rounded mb-2" />
            <div className="h-4 w-full bg-muted rounded" />
          </div>

          <div className="border rounded-lg p-4">
            <div className="h-4 w-32 bg-muted rounded mb-3" />
            <div className="aspect-video max-w-xs mx-auto bg-muted rounded-lg" />
          </div>
        </div>
      </div>
    </div>
  );
}

export default WaitingRoom;
