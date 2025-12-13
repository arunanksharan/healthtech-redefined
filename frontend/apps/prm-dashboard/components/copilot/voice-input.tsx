"use client";

import * as React from "react";
import { useEffect, useRef, useCallback } from "react";
import { Mic, MicOff, AlertCircle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Button } from "@/components/ui/button";
import { useCopilotStore } from "@/lib/store/copilot-store";

// ============================================================================
// Types
// ============================================================================

interface VoiceInputProps {
  className?: string;
  onTranscriptComplete?: (transcript: string) => void;
}

// ============================================================================
// Voice Input Component
// ============================================================================

export function VoiceInput({ className, onTranscriptComplete }: VoiceInputProps) {
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const finalTranscriptRef = useRef("");

  // Store state
  const {
    voiceState,
    voiceTranscript,
    setVoiceTranscript,
    setVoiceState,
    setInputValue,
    stopVoiceInput,
  } = useCopilotStore();

  // ========================================================================
  // Speech Recognition Setup
  // ========================================================================

  useEffect(() => {
    // Check for browser support
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      console.warn("Speech Recognition not supported in this browser");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onstart = () => {
      setVoiceState("listening");
      finalTranscriptRef.current = "";
    };

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interimTranscript = "";
      let finalTranscript = finalTranscriptRef.current;

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalTranscript += result[0].transcript;
          finalTranscriptRef.current = finalTranscript;
        } else {
          interimTranscript += result[0].transcript;
        }
      }

      setVoiceTranscript(finalTranscript + interimTranscript);
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.error("Speech recognition error:", event.error);
      setVoiceState("error");

      // Auto-recover from certain errors
      if (event.error === "no-speech") {
        setTimeout(() => {
          setVoiceState("inactive");
        }, 2000);
      }
    };

    recognition.onend = () => {
      if (voiceState === "listening") {
        setVoiceState("processing");

        // Transfer final transcript to input
        if (finalTranscriptRef.current.trim()) {
          setInputValue(finalTranscriptRef.current.trim());
          onTranscriptComplete?.(finalTranscriptRef.current.trim());
        }

        setTimeout(() => {
          setVoiceState("inactive");
        }, 500);
      }
    };

    recognitionRef.current = recognition;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [setVoiceTranscript, setVoiceState, setInputValue, onTranscriptComplete, voiceState]);

  // Start/Stop recognition based on voice state
  useEffect(() => {
    const recognition = recognitionRef.current;
    if (!recognition) return;

    if (voiceState === "listening") {
      try {
        recognition.start();
      } catch (error) {
        // Recognition might already be running
        console.log("Recognition already started or error:", error);
      }
    } else if (voiceState === "inactive" || voiceState === "error") {
      try {
        recognition.stop();
      } catch (error) {
        // Recognition might not be running
        console.log("Recognition already stopped or error:", error);
      }
    }
  }, [voiceState]);

  // ========================================================================
  // Render
  // ========================================================================

  return (
    <div className={cn("flex items-center gap-3 w-full", className)}>
      {/* Sound Wave Animation */}
      {voiceState === "listening" && (
        <SoundWaveAnimation />
      )}

      {/* Transcript Display */}
      <div className="flex-1 min-h-[24px]">
        {voiceState === "listening" && (
          <p className={cn(
            "text-base",
            voiceTranscript ? "text-foreground" : "text-muted-foreground"
          )}>
            {voiceTranscript || "Listening..."}
          </p>
        )}

        {voiceState === "processing" && (
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Processing...</span>
          </div>
        )}

        {voiceState === "error" && (
          <div className="flex items-center gap-2 text-destructive">
            <AlertCircle className="h-4 w-4" />
            <span>Could not hear you. Please try again.</span>
          </div>
        )}
      </div>

      {/* Release to Stop Hint */}
      {voiceState === "listening" && (
        <span className="text-xs text-muted-foreground whitespace-nowrap">
          Release to stop
        </span>
      )}
    </div>
  );
}

// ============================================================================
// Sound Wave Animation Component
// ============================================================================

function SoundWaveAnimation() {
  return (
    <div className="flex items-center gap-0.5 h-6">
      {[...Array(5)].map((_, i) => (
        <div
          key={i}
          className={cn(
            "w-1 bg-primary rounded-full",
            "animate-sound-wave"
          )}
          style={{
            animationDelay: `${i * 0.1}s`,
            height: `${Math.random() * 16 + 8}px`,
          }}
        />
      ))}
    </div>
  );
}

// ============================================================================
// Voice Button Component (for standalone use)
// ============================================================================

interface VoiceButtonProps {
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function VoiceButton({ size = "md", className }: VoiceButtonProps) {
  const { voiceState, startVoiceInput, stopVoiceInput } = useCopilotStore();

  const isListening = voiceState === "listening";
  const isProcessing = voiceState === "processing";
  const hasError = voiceState === "error";

  const handleClick = useCallback(() => {
    if (isListening) {
      stopVoiceInput();
    } else {
      startVoiceInput();
    }
  }, [isListening, startVoiceInput, stopVoiceInput]);

  // Handle hold-to-talk
  const handleMouseDown = useCallback(() => {
    startVoiceInput();
  }, [startVoiceInput]);

  const handleMouseUp = useCallback(() => {
    if (isListening) {
      stopVoiceInput();
    }
  }, [isListening, stopVoiceInput]);

  const sizeClasses = {
    sm: "h-8 w-8",
    md: "h-10 w-10",
    lg: "h-12 w-12",
  };

  const iconSizes = {
    sm: "h-4 w-4",
    md: "h-5 w-5",
    lg: "h-6 w-6",
  };

  return (
    <Button
      variant={isListening ? "destructive" : "outline"}
      size="icon"
      className={cn(
        sizeClasses[size],
        "relative rounded-full",
        isListening && "animate-pulse",
        className
      )}
      onClick={handleClick}
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      disabled={isProcessing}
    >
      {/* Pulse Ring Animation */}
      {isListening && (
        <div className="absolute inset-0 rounded-full animate-ping bg-destructive/50" />
      )}

      {/* Icon */}
      {isProcessing ? (
        <Loader2 className={cn(iconSizes[size], "animate-spin")} />
      ) : hasError ? (
        <AlertCircle className={iconSizes[size]} />
      ) : isListening ? (
        <MicOff className={iconSizes[size]} />
      ) : (
        <Mic className={iconSizes[size]} />
      )}
    </Button>
  );
}

// ============================================================================
// Voice Input Modal (Full Screen for Mobile)
// ============================================================================

interface VoiceInputModalProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: (transcript: string) => void;
}

export function VoiceInputModal({ isOpen, onClose, onComplete }: VoiceInputModalProps) {
  const { voiceState, voiceTranscript, startVoiceInput, stopVoiceInput, setVoiceState } = useCopilotStore();

  useEffect(() => {
    if (isOpen) {
      startVoiceInput();
    } else {
      setVoiceState("inactive");
    }
  }, [isOpen, startVoiceInput, setVoiceState]);

  const handleComplete = useCallback(() => {
    stopVoiceInput();
    if (voiceTranscript.trim()) {
      onComplete(voiceTranscript.trim());
    }
    onClose();
  }, [stopVoiceInput, voiceTranscript, onComplete, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-background/95 backdrop-blur-sm">
      {/* Close Button */}
      <Button
        variant="ghost"
        size="icon"
        className="absolute top-4 right-4"
        onClick={onClose}
      >
        <MicOff className="h-6 w-6" />
      </Button>

      {/* Main Content */}
      <div className="flex flex-col items-center gap-8 px-8 text-center">
        {/* Animated Mic Icon */}
        <div className="relative">
          <div className={cn(
            "w-32 h-32 rounded-full flex items-center justify-center",
            voiceState === "listening" ? "bg-destructive" : "bg-primary",
            voiceState === "listening" && "animate-pulse"
          )}>
            {voiceState === "listening" && (
              <>
                <div className="absolute inset-0 rounded-full animate-ping bg-destructive/30" />
                <div className="absolute inset-[-8px] rounded-full animate-pulse bg-destructive/20" />
              </>
            )}
            <Mic className="h-16 w-16 text-white" />
          </div>
        </div>

        {/* Status Text */}
        <div className="space-y-2">
          <h2 className="text-2xl font-semibold">
            {voiceState === "listening" ? "Listening..." : "Tap to start"}
          </h2>
          <p className="text-muted-foreground max-w-sm">
            {voiceState === "listening"
              ? "Speak your command clearly"
              : "Hold the button or tap to start voice input"}
          </p>
        </div>

        {/* Transcript */}
        {voiceTranscript && (
          <div className="max-w-lg p-4 bg-muted rounded-lg">
            <p className="text-lg">{voiceTranscript}</p>
          </div>
        )}

        {/* Sound Wave */}
        {voiceState === "listening" && (
          <div className="flex items-end gap-1 h-16">
            {[...Array(12)].map((_, i) => (
              <div
                key={i}
                className="w-2 bg-primary rounded-full animate-sound-wave"
                style={{
                  animationDelay: `${i * 0.05}s`,
                  height: `${Math.random() * 48 + 16}px`,
                }}
              />
            ))}
          </div>
        )}

        {/* Action Button */}
        {voiceTranscript && (
          <Button size="lg" onClick={handleComplete}>
            Use This Command
          </Button>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Web Speech API types are declared in types/speech-recognition.d.ts

export default VoiceInput;
