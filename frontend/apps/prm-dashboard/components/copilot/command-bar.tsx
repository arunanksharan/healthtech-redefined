"use client";

import * as React from "react";
import { useEffect, useCallback, useRef } from "react";
import {
  Search,
  Mic,
  MicOff,
  X,
  Command,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Clock,
  ArrowRight,
  Calendar,
  User,
  MessageSquare,
  ChartBar,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  useCopilotStore,
  selectIsCommandBarOpen,
  selectInputValue,
  selectVoiceState,
  selectExecutionState,
  selectParsedIntent,
  selectContext,
  selectRecentCommands,
  selectQuickActions,
  selectMultiStepOperation,
} from "@/lib/store/copilot-store";
import type { QuickAction, RecentCommand, ParsedIntent } from "@/lib/store/copilot-store";
import { EntityTag } from "./entity-tag";
import { VoiceInput } from "./voice-input";
import { GhostCard } from "./ghost-card";
import { MultiStepView } from "./multi-step-view";

// ============================================================================
// Types
// ============================================================================

interface CommandBarProps {
  className?: string;
}

// ============================================================================
// Quick Action Icon Mapping
// ============================================================================

const quickActionIcons: Record<string, React.ElementType> = {
  "📅": Calendar,
  "👤": User,
  "📊": ChartBar,
  "💬": MessageSquare,
  "💊": Sparkles,
  "📝": Sparkles,
  "📤": MessageSquare,
};

// ============================================================================
// Command Bar Component
// ============================================================================

export function CommandBar({ className }: CommandBarProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Store state
  const isOpen = useCopilotStore(selectIsCommandBarOpen);
  const inputValue = useCopilotStore(selectInputValue);
  const voiceState = useCopilotStore(selectVoiceState);
  const executionState = useCopilotStore(selectExecutionState);
  const parsedIntent = useCopilotStore(selectParsedIntent);
  const context = useCopilotStore(selectContext);
  const recentCommands = useCopilotStore(selectRecentCommands);
  const quickActions = useCopilotStore(selectQuickActions);
  const multiStepOperation = useCopilotStore(selectMultiStepOperation);

  // Store actions
  const {
    closeCommandBar,
    setInputValue,
    clearInput,
    parseInput,
    startVoiceInput,
    stopVoiceInput,
    executeCommand,
    executeQuickAction,
    navigateSuggestions,
    selectSuggestion,
    selectedSuggestionIndex,
  } = useCopilotStore();

  // ========================================================================
  // Effects
  // ========================================================================

  // Focus input when opened
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      // Escape to close
      if (e.key === "Escape") {
        e.preventDefault();
        closeCommandBar();
        return;
      }

      // Navigate suggestions
      if (e.key === "ArrowDown") {
        e.preventDefault();
        navigateSuggestions("down");
        return;
      }

      if (e.key === "ArrowUp") {
        e.preventDefault();
        navigateSuggestions("up");
        return;
      }

      // Select suggestion or execute
      if (e.key === "Enter") {
        if (selectedSuggestionIndex >= 0) {
          e.preventDefault();
          selectSuggestion();
        } else if (executionState === "parsed" && parsedIntent) {
          e.preventDefault();
          executeCommand();
        }
        return;
      }

      // Tab to autocomplete
      if (e.key === "Tab" && selectedSuggestionIndex >= 0) {
        e.preventDefault();
        selectSuggestion();
        return;
      }

      // Cmd+Enter to execute without confirmation
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
        if (inputValue.trim()) {
          e.preventDefault();
          // Quick execute
        }
        return;
      }

      // Hold Space for voice (when input is focused and empty)
      if (e.code === "Space" && !inputValue && document.activeElement === inputRef.current) {
        e.preventDefault();
        startVoiceInput();
        return;
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      // Release space to stop voice
      if (e.code === "Space" && voiceState === "listening") {
        stopVoiceInput();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
    };
  }, [
    isOpen,
    closeCommandBar,
    navigateSuggestions,
    selectSuggestion,
    selectedSuggestionIndex,
    executionState,
    parsedIntent,
    executeCommand,
    inputValue,
    voiceState,
    startVoiceInput,
    stopVoiceInput,
  ]);

  // Debounced parsing
  useEffect(() => {
    if (!inputValue.trim() || voiceState === "listening") return;

    const timer = setTimeout(() => {
      parseInput(inputValue);
    }, 300);

    return () => clearTimeout(timer);
  }, [inputValue, parseInput, voiceState]);

  // Click outside to close
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        // Don't close if executing
        if (executionState !== "executing") {
          closeCommandBar();
        }
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen, closeCommandBar, executionState]);

  // ========================================================================
  // Handlers
  // ========================================================================

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setInputValue(e.target.value);
    },
    [setInputValue]
  );

  const handleQuickAction = useCallback(
    (action: QuickAction) => {
      executeQuickAction(action.id);
    },
    [executeQuickAction]
  );

  const handleRecentCommand = useCallback(
    (command: RecentCommand) => {
      setInputValue(command.input);
    },
    [setInputValue]
  );

  const handleVoiceToggle = useCallback(() => {
    if (voiceState === "listening") {
      stopVoiceInput();
    } else {
      startVoiceInput();
    }
  }, [voiceState, startVoiceInput, stopVoiceInput]);

  // ========================================================================
  // Render
  // ========================================================================

  if (!isOpen) return null;

  const showEmptyState = !inputValue && executionState === "idle";
  const showParsingState = executionState === "parsing";
  const showResultsState = executionState === "parsed" && parsedIntent;
  const showExecutingState = executionState === "executing";
  const showSuccessState = executionState === "success";
  const showErrorState = executionState === "error";
  const showMultiStep = multiStepOperation !== null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]">
      {/* Overlay */}
      <div className="absolute inset-0 bg-background/80 backdrop-blur-sm" />

      {/* Command Bar Container */}
      <div
        ref={containerRef}
        className={cn(
          "relative w-full max-w-2xl mx-4 bg-card border border-border rounded-xl shadow-2xl overflow-hidden",
          "animate-in fade-in-0 zoom-in-95 duration-200",
          className
        )}
      >
        {/* Input Section */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-border">
          {/* Search/Voice Icon */}
          {voiceState === "listening" ? (
            <div className="flex items-center justify-center w-8 h-8">
              <div className="relative">
                <div className="w-3 h-3 bg-destructive rounded-full animate-pulse" />
                <div className="absolute inset-0 w-3 h-3 bg-destructive rounded-full animate-ping opacity-75" />
              </div>
            </div>
          ) : (
            <Search className="w-5 h-5 text-muted-foreground flex-shrink-0" />
          )}

          {/* Input Field */}
          <div className="flex-1 relative">
            {voiceState === "listening" ? (
              <VoiceInput />
            ) : (
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={handleInputChange}
                placeholder={
                  context.currentPatient
                    ? `What would you like to do for ${context.currentPatient.name}?`
                    : "Ask anything or type a command..."
                }
                className={cn(
                  "w-full bg-transparent border-none outline-none text-base text-foreground",
                  "placeholder:text-muted-foreground"
                )}
                autoComplete="off"
                autoCorrect="off"
                autoCapitalize="off"
                spellCheck="false"
              />
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2 flex-shrink-0">
            {/* Voice Button */}
            <Button
              variant="ghost"
              size="sm"
              onClick={handleVoiceToggle}
              className={cn(
                "h-8 w-8 p-0",
                voiceState === "listening" && "text-destructive hover:text-destructive"
              )}
            >
              {voiceState === "listening" ? (
                <MicOff className="h-4 w-4" />
              ) : (
                <Mic className="h-4 w-4" />
              )}
            </Button>

            {/* Keyboard Shortcut Badge */}
            <Badge variant="secondary" className="text-xs font-mono hidden sm:flex">
              <Command className="h-3 w-3 mr-1" />K
            </Badge>

            {/* Close Button */}
            <Button
              variant="ghost"
              size="sm"
              onClick={closeCommandBar}
              className="h-8 w-8 p-0"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Context Banner */}
        {context.currentPatient && (
          <div className="px-4 py-2 bg-primary/5 border-b border-border">
            <div className="flex items-center gap-2 text-sm">
              <User className="h-4 w-4 text-primary" />
              <span className="text-muted-foreground">Context:</span>
              <span className="font-medium text-foreground">
                {context.currentPatient.name}
              </span>
              {context.currentPatient.mrn && (
                <Badge variant="outline" className="text-xs">
                  MRN: {context.currentPatient.mrn}
                </Badge>
              )}
            </div>
          </div>
        )}

        {/* Content Area */}
        <div className="max-h-[60vh] overflow-y-auto">
          {/* Empty State */}
          {showEmptyState && (
            <EmptyState
              quickActions={quickActions}
              recentCommands={recentCommands}
              selectedIndex={selectedSuggestionIndex}
              onQuickAction={handleQuickAction}
              onRecentCommand={handleRecentCommand}
            />
          )}

          {/* Parsing State */}
          {showParsingState && (
            <div className="flex items-center gap-3 px-4 py-8 justify-center">
              <Loader2 className="h-5 w-5 animate-spin text-primary" />
              <span className="text-muted-foreground">Parsing your request...</span>
            </div>
          )}

          {/* Results State - Ghost Card */}
          {showResultsState && !showMultiStep && (
            <GhostCard
              intent={parsedIntent}
              onExecute={executeCommand}
              onCancel={clearInput}
            />
          )}

          {/* Multi-Step Operation View */}
          {showMultiStep && (
            <MultiStepView operation={multiStepOperation} />
          )}

          {/* Executing State */}
          {showExecutingState && !showMultiStep && (
            <div className="flex flex-col items-center gap-4 px-4 py-8">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <span className="text-muted-foreground">Executing command...</span>
            </div>
          )}

          {/* Success State */}
          {showSuccessState && (
            <SuccessState />
          )}

          {/* Error State */}
          {showErrorState && (
            <ErrorState />
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 bg-muted/30 border-t border-border">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-muted rounded text-[10px]">↵</kbd>
                Execute
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-muted rounded text-[10px]">↑↓</kbd>
                Navigate
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-muted rounded text-[10px]">Space</kbd>
                Voice
              </span>
            </div>
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 bg-muted rounded text-[10px]">Esc</kbd>
              Close
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Empty State Component
// ============================================================================

interface EmptyStateProps {
  quickActions: QuickAction[];
  recentCommands: RecentCommand[];
  selectedIndex: number;
  onQuickAction: (action: QuickAction) => void;
  onRecentCommand: (command: RecentCommand) => void;
}

function EmptyState({
  quickActions,
  recentCommands,
  selectedIndex,
  onQuickAction,
  onRecentCommand,
}: EmptyStateProps) {
  return (
    <div className="p-4 space-y-6">
      {/* Quick Actions */}
      <div className="space-y-3">
        <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          Quick Actions
        </h4>
        <div className="flex flex-wrap gap-2">
          {quickActions.map((action, index) => {
            const IconComponent = quickActionIcons[action.icon] || Sparkles;
            const isSelected = selectedIndex === index;

            return (
              <button
                key={action.id}
                onClick={() => onQuickAction(action)}
                className={cn(
                  "flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors",
                  "bg-muted hover:bg-muted/80",
                  isSelected && "ring-2 ring-primary bg-primary/5"
                )}
              >
                <IconComponent className="h-4 w-4 text-muted-foreground" />
                <span>{action.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Recent Commands */}
      {recentCommands.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Recent Commands
          </h4>
          <div className="space-y-1">
            {recentCommands.slice(0, 5).map((command, index) => {
              const isSelected = selectedIndex === quickActions.length + index;

              return (
                <button
                  key={command.id}
                  onClick={() => onRecentCommand(command)}
                  className={cn(
                    "w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors text-left",
                    "hover:bg-muted",
                    isSelected && "ring-2 ring-primary bg-primary/5"
                  )}
                >
                  <Clock className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                  <span className="flex-1 truncate">{command.input}</span>
                  {command.success ? (
                    <CheckCircle2 className="h-4 w-4 text-success flex-shrink-0" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-destructive flex-shrink-0" />
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Tips */}
      <div className="pt-2 border-t border-border">
        <p className="text-xs text-muted-foreground">
          <Sparkles className="h-3 w-3 inline mr-1" />
          Pro tip: Try "Book appointment for John Doe with Dr. Sharma tomorrow 2PM"
        </p>
      </div>
    </div>
  );
}

// ============================================================================
// Success State Component
// ============================================================================

function SuccessState() {
  const { executionResult, closeCommandBar, clearInput } = useCopilotStore();

  if (!executionResult) return null;

  return (
    <div className="flex flex-col items-center gap-4 px-4 py-8">
      <div className="w-16 h-16 rounded-full bg-success/10 flex items-center justify-center">
        <CheckCircle2 className="h-8 w-8 text-success" />
      </div>
      <div className="text-center">
        <h3 className="text-lg font-semibold text-foreground">Success!</h3>
        <p className="text-muted-foreground mt-1">{executionResult.message}</p>
      </div>

      {executionResult.actions && executionResult.actions.length > 0 && (
        <div className="flex items-center gap-2 mt-2">
          {executionResult.actions.map((action) => (
            <Button
              key={action.id}
              variant={action.isPrimary ? "default" : "outline"}
              size="sm"
              onClick={() => {
                if (action.action === "reset") {
                  clearInput();
                } else if (action.action === "view") {
                  closeCommandBar();
                }
              }}
            >
              {action.label}
              {action.action === "view" && <ArrowRight className="h-4 w-4 ml-1" />}
            </Button>
          ))}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Error State Component
// ============================================================================

function ErrorState() {
  const { parseError, executionResult, retryExecution, clearInput } = useCopilotStore();

  const errorMessage = parseError || executionResult?.message || "Something went wrong";

  return (
    <div className="px-4 py-6">
      <div className="flex items-start gap-3 p-4 bg-destructive/5 rounded-lg border border-destructive/20">
        <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <h4 className="font-medium text-foreground">Couldn't complete the action</h4>
          <p className="text-sm text-muted-foreground mt-1">{errorMessage}</p>

          <div className="flex items-center gap-2 mt-4">
            <Button size="sm" variant="outline" onClick={retryExecution}>
              Try Again
            </Button>
            <Button size="sm" variant="ghost" onClick={clearInput}>
              Clear
            </Button>
          </div>
        </div>
      </div>

      {/* Suggestions */}
      <div className="mt-4">
        <p className="text-sm text-muted-foreground mb-2">Did you mean:</p>
        <div className="space-y-1">
          {["Book an appointment", "Find a patient", "View schedule"].map((suggestion) => (
            <button
              key={suggestion}
              className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-left hover:bg-muted"
            >
              <ArrowRight className="h-4 w-4 text-muted-foreground" />
              {suggestion}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export default CommandBar;
