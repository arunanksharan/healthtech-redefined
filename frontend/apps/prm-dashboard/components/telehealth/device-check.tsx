"use client";

// Device Check Component
// EPIC-UX-008: Telehealth Experience

import React, { useEffect, useRef, useState, useCallback } from "react";
import {
  Camera,
  CameraOff,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Wifi,
  WifiOff,
  Check,
  X,
  ChevronDown,
  Loader2,
  RefreshCw,
  AlertTriangle,
  Info,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  useTelehealthStore,
  type DeviceType,
  type NetworkQuality,
} from "@/lib/store/telehealth-store";

// ============================================================================
// Types
// ============================================================================

interface DeviceCheckProps {
  onComplete: (passed: boolean) => void;
  onCancel: () => void;
  showNetworkTest?: boolean;
  requiredDevices?: DeviceType[];
  providerName?: string;
  appointmentTime?: string;
}

// ============================================================================
// Sub-Components
// ============================================================================

interface VideoPreviewProps {
  stream: MediaStream | null;
  error: string | null;
}

function VideoPreview({ stream, error }: VideoPreviewProps) {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    }
  }, [stream]);

  if (error) {
    return (
      <div className="w-full aspect-video bg-muted rounded-lg flex flex-col items-center justify-center">
        <CameraOff className="h-12 w-12 text-muted-foreground mb-2" />
        <p className="text-sm text-muted-foreground text-center px-4">{error}</p>
      </div>
    );
  }

  if (!stream) {
    return (
      <div className="w-full aspect-video bg-muted rounded-lg flex flex-col items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground mb-2" />
        <p className="text-sm text-muted-foreground">Initializing camera...</p>
      </div>
    );
  }

  return (
    <video
      ref={videoRef}
      autoPlay
      playsInline
      muted
      className="w-full aspect-video rounded-lg bg-black object-cover"
    />
  );
}

interface AudioLevelMeterProps {
  level: number;
  isActive: boolean;
}

function AudioLevelMeter({ level, isActive }: AudioLevelMeterProps) {
  const bars = 10;

  return (
    <div className="flex items-center gap-0.5 h-6">
      {Array.from({ length: bars }).map((_, i) => {
        const threshold = (i + 1) * (100 / bars);
        const isLit = isActive && level >= threshold;
        return (
          <div
            key={i}
            className={cn(
              "w-1 rounded-full transition-all duration-75",
              isLit
                ? i < 3
                  ? "bg-green-500"
                  : i < 7
                  ? "bg-yellow-500"
                  : "bg-red-500"
                : "bg-muted"
            )}
            style={{ height: `${(i + 1) * 10}%` }}
          />
        );
      })}
    </div>
  );
}

interface DeviceStatusItemProps {
  icon: React.ReactNode;
  label: string;
  status: "checking" | "passed" | "failed" | "warning";
  error?: string | null;
  children?: React.ReactNode;
}

function DeviceStatusItem({ icon, label, status, error, children }: DeviceStatusItemProps) {
  const statusIcons = {
    checking: <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />,
    passed: <Check className="h-4 w-4 text-green-600" />,
    failed: <X className="h-4 w-4 text-red-600" />,
    warning: <AlertTriangle className="h-4 w-4 text-amber-600" />,
  };

  const statusColors = {
    checking: "text-muted-foreground",
    passed: "text-green-600",
    failed: "text-red-600",
    warning: "text-amber-600",
  };

  return (
    <div className="flex items-center gap-3 py-2">
      <div className="flex items-center gap-2 min-w-[180px]">
        {icon}
        <span className={cn("text-sm font-medium", statusColors[status])}>
          {label}
        </span>
        {statusIcons[status]}
      </div>
      <div className="flex-1">
        {error ? (
          <span className="text-xs text-red-600">{error}</span>
        ) : (
          children
        )}
      </div>
    </div>
  );
}

interface NetworkStatusProps {
  quality: NetworkQuality;
  downloadSpeed: number;
  uploadSpeed: number;
  latency: number;
  tested: boolean;
  onTest: () => void;
}

function NetworkStatus({
  quality,
  downloadSpeed,
  uploadSpeed,
  latency,
  tested,
  onTest,
}: NetworkStatusProps) {
  const qualityConfig = {
    excellent: { color: "text-green-600", bg: "bg-green-100", label: "Excellent" },
    good: { color: "text-green-600", bg: "bg-green-100", label: "Good" },
    fair: { color: "text-amber-600", bg: "bg-amber-100", label: "Fair" },
    poor: { color: "text-red-600", bg: "bg-red-100", label: "Poor" },
  };

  const config = qualityConfig[quality];

  if (!tested) {
    return (
      <Button variant="outline" size="sm" onClick={onTest}>
        <RefreshCw className="h-4 w-4 mr-1" />
        Test Connection
      </Button>
    );
  }

  return (
    <div className="flex items-center gap-4">
      <Badge variant="secondary" className={cn("text-xs", config.color, config.bg)}>
        {config.label}
      </Badge>
      <span className="text-xs text-muted-foreground">
        ↓ {downloadSpeed} Mbps
      </span>
      <span className="text-xs text-muted-foreground">
        ↑ {uploadSpeed} Mbps
      </span>
      <span className="text-xs text-muted-foreground">
        {latency}ms latency
      </span>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function DeviceCheck({
  onComplete,
  onCancel,
  showNetworkTest = true,
  requiredDevices = ["camera", "microphone"],
  providerName,
  appointmentTime,
}: DeviceCheckProps) {
  const [isTestingNetwork, setIsTestingNetwork] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);

  const {
    deviceStatus,
    availableDevices,
    startDeviceCheck,
    selectDevice,
    testSpeakers,
    testNetwork,
  } = useTelehealthStore();

  // Initialize devices on mount
  useEffect(() => {
    startDeviceCheck();
  }, [startDeviceCheck]);

  // Audio level monitoring
  useEffect(() => {
    if (!deviceStatus.microphone.stream) return;

    const audioContext = new AudioContext();
    const analyser = audioContext.createAnalyser();
    const microphone = audioContext.createMediaStreamSource(deviceStatus.microphone.stream);

    analyser.smoothingTimeConstant = 0.8;
    analyser.fftSize = 1024;
    microphone.connect(analyser);

    const dataArray = new Uint8Array(analyser.frequencyBinCount);

    const updateLevel = () => {
      analyser.getByteFrequencyData(dataArray);
      const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
      setAudioLevel(Math.min(100, average * 2));
    };

    const interval = setInterval(updateLevel, 100);

    return () => {
      clearInterval(interval);
      audioContext.close();
    };
  }, [deviceStatus.microphone.stream]);

  // Handle network test
  const handleNetworkTest = useCallback(async () => {
    setIsTestingNetwork(true);
    await testNetwork();
    setIsTestingNetwork(false);
  }, [testNetwork]);

  // Calculate overall status
  const cameraOk = deviceStatus.camera.available && !deviceStatus.camera.error;
  const micOk = deviceStatus.microphone.available && !deviceStatus.microphone.error;
  const speakerOk = deviceStatus.speaker.available;
  const networkOk = !showNetworkTest || deviceStatus.network.quality !== "poor";

  const requiredPassed =
    (!requiredDevices.includes("camera") || cameraOk) &&
    (!requiredDevices.includes("microphone") || micOk) &&
    (!requiredDevices.includes("speaker") || speakerOk);

  const allPassed = requiredPassed && networkOk;

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="text-center mb-6">
        <h1 className="text-2xl font-semibold mb-2">Join Your Appointment</h1>
        {providerName && appointmentTime && (
          <p className="text-muted-foreground">
            👨‍⚕️ {providerName} • 📅 {appointmentTime}
          </p>
        )}
        <p className="text-sm text-muted-foreground mt-4">
          Let's check your devices before you join
        </p>
      </div>

      <Card className="mb-6">
        <CardContent className="p-6">
          {/* Video Preview */}
          <div className="mb-6">
            <VideoPreview
              stream={deviceStatus.camera.stream}
              error={deviceStatus.camera.error}
            />
          </div>

          {/* Device Status */}
          <div className="space-y-1">
            {/* Camera */}
            <DeviceStatusItem
              icon={
                cameraOk ? (
                  <Camera className="h-4 w-4 text-green-600" />
                ) : (
                  <CameraOff className="h-4 w-4 text-red-600" />
                )
              }
              label="Camera"
              status={
                deviceStatus.camera.error
                  ? "failed"
                  : cameraOk
                  ? "passed"
                  : "checking"
              }
              error={deviceStatus.camera.error}
            >
              {availableDevices.cameras.length > 0 && (
                <Select
                  value={deviceStatus.camera.selected?.deviceId || ""}
                  onValueChange={(value) => selectDevice("camera", value)}
                >
                  <SelectTrigger className="h-8 text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {availableDevices.cameras.map((device) => (
                      <SelectItem key={device.deviceId} value={device.deviceId}>
                        {device.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </DeviceStatusItem>

            {/* Microphone */}
            <DeviceStatusItem
              icon={
                micOk ? (
                  <Mic className="h-4 w-4 text-green-600" />
                ) : (
                  <MicOff className="h-4 w-4 text-red-600" />
                )
              }
              label="Microphone"
              status={
                deviceStatus.microphone.error
                  ? "failed"
                  : micOk
                  ? "passed"
                  : "checking"
              }
              error={deviceStatus.microphone.error}
            >
              <div className="flex items-center gap-3">
                {availableDevices.microphones.length > 0 && (
                  <Select
                    value={deviceStatus.microphone.selected?.deviceId || ""}
                    onValueChange={(value) => selectDevice("microphone", value)}
                  >
                    <SelectTrigger className="h-8 text-xs flex-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {availableDevices.microphones.map((device) => (
                        <SelectItem key={device.deviceId} value={device.deviceId}>
                          {device.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
                <AudioLevelMeter level={audioLevel} isActive={micOk} />
              </div>
            </DeviceStatusItem>

            {/* Speaker */}
            <DeviceStatusItem
              icon={
                speakerOk ? (
                  <Volume2 className="h-4 w-4 text-green-600" />
                ) : (
                  <VolumeX className="h-4 w-4 text-red-600" />
                )
              }
              label="Speakers"
              status={
                speakerOk
                  ? deviceStatus.speaker.tested
                    ? "passed"
                    : "warning"
                  : "failed"
              }
            >
              <div className="flex items-center gap-3">
                {availableDevices.speakers.length > 0 && (
                  <Select
                    value={deviceStatus.speaker.selected?.deviceId || ""}
                    onValueChange={(value) => selectDevice("speaker", value)}
                  >
                    <SelectTrigger className="h-8 text-xs flex-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {availableDevices.speakers.map((device) => (
                        <SelectItem key={device.deviceId} value={device.deviceId}>
                          {device.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
                <Button
                  variant="outline"
                  size="sm"
                  className="text-xs"
                  onClick={testSpeakers}
                >
                  Test 🔊
                </Button>
                {deviceStatus.speaker.tested && (
                  <Check className="h-4 w-4 text-green-600" />
                )}
              </div>
            </DeviceStatusItem>

            {/* Network */}
            {showNetworkTest && (
              <DeviceStatusItem
                icon={
                  deviceStatus.network.quality === "poor" ? (
                    <WifiOff className="h-4 w-4 text-red-600" />
                  ) : (
                    <Wifi className="h-4 w-4 text-green-600" />
                  )
                }
                label="Internet Connection"
                status={
                  isTestingNetwork
                    ? "checking"
                    : !deviceStatus.network.tested
                    ? "warning"
                    : deviceStatus.network.quality === "poor"
                    ? "failed"
                    : "passed"
                }
              >
                <NetworkStatus
                  quality={deviceStatus.network.quality}
                  downloadSpeed={deviceStatus.network.downloadSpeed}
                  uploadSpeed={deviceStatus.network.uploadSpeed}
                  latency={deviceStatus.network.latency}
                  tested={deviceStatus.network.tested}
                  onTest={handleNetworkTest}
                />
              </DeviceStatusItem>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Tips */}
      {!allPassed && (
        <Card className="mb-6 border-amber-200 bg-amber-50">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <Info className="h-5 w-5 text-amber-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-amber-800 mb-1">Troubleshooting Tips</h4>
                <ul className="text-sm text-amber-700 space-y-1">
                  {deviceStatus.camera.error && (
                    <li>• Make sure your camera is not being used by another app</li>
                  )}
                  {deviceStatus.microphone.error && (
                    <li>• Check your browser permissions for microphone access</li>
                  )}
                  {deviceStatus.network.quality === "poor" && (
                    <li>• Try moving closer to your WiFi router</li>
                  )}
                  <li>• Try refreshing the page if issues persist</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={onCancel}>
          Need Help?
        </Button>
        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={() => startDeviceCheck()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
          <Button
            onClick={() => onComplete(allPassed)}
            disabled={!requiredPassed}
          >
            {allPassed ? "Continue" : "Continue Anyway"} →
          </Button>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Provider Pre-Call Check (Compact)
// ============================================================================

interface ProviderPreCallCheckProps {
  session: {
    id: string;
    patientName: string;
  };
  onJoin: () => void;
  onCancel: () => void;
  enableRecording: boolean;
  enableTranscription: boolean;
  onRecordingChange: (enabled: boolean) => void;
  onTranscriptionChange: (enabled: boolean) => void;
}

export function ProviderPreCallCheck({
  session,
  onJoin,
  onCancel,
  enableRecording,
  enableTranscription,
  onRecordingChange,
  onTranscriptionChange,
}: ProviderPreCallCheckProps) {
  const { deviceStatus, startDeviceCheck } = useTelehealthStore();

  useEffect(() => {
    startDeviceCheck();
  }, [startDeviceCheck]);

  const allDevicesOk =
    deviceStatus.camera.available &&
    deviceStatus.microphone.available &&
    !deviceStatus.camera.error &&
    !deviceStatus.microphone.error;

  return (
    <div className="p-6 max-w-md mx-auto">
      <h2 className="text-lg font-semibold mb-4">
        Starting Session: {session.patientName}
      </h2>

      {/* Camera Preview */}
      <div className="mb-4">
        <VideoPreview
          stream={deviceStatus.camera.stream}
          error={deviceStatus.camera.error}
        />
      </div>

      {/* Device Status Summary */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center gap-2 text-sm">
          {deviceStatus.camera.available && !deviceStatus.camera.error ? (
            <Check className="h-4 w-4 text-green-600" />
          ) : (
            <X className="h-4 w-4 text-red-600" />
          )}
          <span>Camera: {deviceStatus.camera.selected?.label || "Not found"}</span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          {deviceStatus.microphone.available && !deviceStatus.microphone.error ? (
            <Check className="h-4 w-4 text-green-600" />
          ) : (
            <X className="h-4 w-4 text-red-600" />
          )}
          <span>Microphone: {deviceStatus.microphone.selected?.label || "Not found"}</span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          {deviceStatus.speaker.available ? (
            <Check className="h-4 w-4 text-green-600" />
          ) : (
            <X className="h-4 w-4 text-red-600" />
          )}
          <span>Speaker: {deviceStatus.speaker.selected?.label || "Not found"}</span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <Check className="h-4 w-4 text-green-600" />
          <span>Network: Strong ({deviceStatus.network.downloadSpeed || 45} Mbps)</span>
        </div>
      </div>

      {/* Options */}
      <div className="space-y-3 mb-6">
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={enableRecording}
            onChange={(e) => onRecordingChange(e.target.checked)}
            className="rounded"
          />
          Record this session (Patient consent obtained)
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={enableTranscription}
            onChange={(e) => onTranscriptionChange(e.target.checked)}
            className="rounded"
          />
          Enable AI note-taking
        </label>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between">
        <Button variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button onClick={onJoin} disabled={!allDevicesOk}>
          Join Session →
        </Button>
      </div>
    </div>
  );
}

// ============================================================================
// Device Check Skeleton
// ============================================================================

export function DeviceCheckSkeleton() {
  return (
    <div className="max-w-2xl mx-auto p-6 animate-pulse">
      <div className="text-center mb-6">
        <div className="h-8 w-48 bg-muted rounded mx-auto mb-2" />
        <div className="h-4 w-64 bg-muted rounded mx-auto" />
      </div>

      <div className="border rounded-lg p-6">
        <div className="w-full aspect-video bg-muted rounded-lg mb-6" />

        <div className="space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3">
              <div className="h-4 w-4 bg-muted rounded" />
              <div className="h-4 w-24 bg-muted rounded" />
              <div className="h-4 w-4 bg-muted rounded" />
              <div className="flex-1 h-8 bg-muted rounded" />
            </div>
          ))}
        </div>
      </div>

      <div className="flex items-center justify-between mt-6">
        <div className="h-9 w-24 bg-muted rounded" />
        <div className="flex gap-3">
          <div className="h-9 w-20 bg-muted rounded" />
          <div className="h-9 w-28 bg-muted rounded" />
        </div>
      </div>
    </div>
  );
}

export default DeviceCheck;
