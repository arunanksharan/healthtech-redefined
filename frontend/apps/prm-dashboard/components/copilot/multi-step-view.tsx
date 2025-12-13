"use client";

import * as React from "react";
import { useState } from "react";
import {
  CheckCircle2,
  Circle,
  Loader2,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  XCircle,
  RotateCcw,
  Play,
  Pause,
  SkipForward,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { useCopilotStore } from "@/lib/store/copilot-store";
import type { MultiStepOperation, OperationStep } from "@/lib/store/copilot-store";

// ============================================================================
// Types
// ============================================================================

interface MultiStepViewProps {
  operation: MultiStepOperation;
  className?: string;
}

interface StepCardProps {
  step: OperationStep;
  stepNumber: number;
  isCurrentStep: boolean;
  isExpanded: boolean;
  onToggleExpand: () => void;
  onRetry?: () => void;
  onSkip?: () => void;
}

// ============================================================================
// Multi-Step View Component
// ============================================================================

export function MultiStepView({ operation, className }: MultiStepViewProps) {
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set([operation.steps[0]?.id]));

  const {
    cancelOperation,
    updateStepStatus,
    advanceStep,
  } = useCopilotStore();

  const toggleStepExpand = (stepId: string) => {
    setExpandedSteps((prev) => {
      const next = new Set(prev);
      if (next.has(stepId)) {
        next.delete(stepId);
      } else {
        next.add(stepId);
      }
      return next;
    });
  };

  const handleRetryStep = (stepId: string) => {
    updateStepStatus(stepId, "in_progress");
    // Actual retry logic would be here
  };

  const handleSkipStep = (stepId: string) => {
    updateStepStatus(stepId, "skipped");
    advanceStep();
  };

  const completedSteps = operation.steps.filter((s) => s.status === "completed").length;
  const hasErrors = operation.steps.some((s) => s.status === "error");
  const isInProgress = operation.steps.some((s) => s.status === "in_progress");
  const allCompleted = completedSteps === operation.totalSteps;

  return (
    <div className={cn("p-4 space-y-4", className)}>
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-lg text-foreground">
            {operation.title}
          </h3>
          <p className="text-sm text-muted-foreground">
            {isInProgress
              ? `Step ${operation.currentStepIndex + 1} of ${operation.totalSteps}`
              : allCompleted
                ? "All steps completed"
                : hasErrors
                  ? "Some steps failed"
                  : "Ready to execute"}
          </p>
        </div>

        {/* Overall Progress Badge */}
        <Badge
          variant="outline"
          className={cn(
            allCompleted && "bg-success/10 text-success border-success/30",
            hasErrors && "bg-destructive/10 text-destructive border-destructive/30",
            isInProgress && "bg-primary/10 text-primary border-primary/30"
          )}
        >
          {operation.overallProgress}% complete
        </Badge>
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <Progress
          value={operation.overallProgress}
          className="h-2"
        />
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>{completedSteps} of {operation.totalSteps} steps</span>
          {isInProgress && <span className="animate-pulse">In progress...</span>}
        </div>
      </div>

      {/* Steps List */}
      <div className="space-y-3">
        {operation.steps.map((step, index) => (
          <StepCard
            key={step.id}
            step={step}
            stepNumber={index + 1}
            isCurrentStep={index === operation.currentStepIndex}
            isExpanded={expandedSteps.has(step.id)}
            onToggleExpand={() => toggleStepExpand(step.id)}
            onRetry={step.canRetry ? () => handleRetryStep(step.id) : undefined}
            onSkip={step.status !== "completed" ? () => handleSkipStep(step.id) : undefined}
          />
        ))}
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between pt-4 border-t">
        <Button variant="outline" onClick={cancelOperation}>
          Cancel All
        </Button>

        <div className="flex items-center gap-2">
          {hasErrors && (
            <Button variant="outline" size="sm">
              <RotateCcw className="h-4 w-4 mr-2" />
              Retry Failed
            </Button>
          )}

          {!allCompleted && !isInProgress && (
            <Button>
              <Play className="h-4 w-4 mr-2" />
              Execute All Steps
            </Button>
          )}

          {isInProgress && (
            <Button variant="outline">
              <Pause className="h-4 w-4 mr-2" />
              Pause
            </Button>
          )}

          {allCompleted && (
            <Button variant="default">
              <CheckCircle2 className="h-4 w-4 mr-2" />
              Done
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Step Card Component
// ============================================================================

function StepCard({
  step,
  stepNumber,
  isCurrentStep,
  isExpanded,
  onToggleExpand,
  onRetry,
  onSkip,
}: StepCardProps) {
  const StatusIcon = getStatusIcon(step.status);
  const statusColor = getStatusColor(step.status);

  return (
    <Collapsible open={isExpanded} onOpenChange={onToggleExpand}>
      <div
        className={cn(
          "border rounded-lg overflow-hidden transition-all",
          isCurrentStep && "ring-2 ring-primary/50",
          step.status === "error" && "border-destructive/50",
          step.status === "completed" && "border-success/30 bg-success/5"
        )}
      >
        {/* Step Header */}
        <CollapsibleTrigger asChild>
          <button
            className={cn(
              "w-full flex items-center justify-between px-4 py-3",
              "hover:bg-muted/50 transition-colors text-left"
            )}
          >
            <div className="flex items-center gap-3">
              {/* Status Icon */}
              <div className={cn(
                "flex items-center justify-center w-8 h-8 rounded-full",
                step.status === "completed" && "bg-success/10",
                step.status === "in_progress" && "bg-primary/10",
                step.status === "error" && "bg-destructive/10",
                step.status === "pending" && "bg-muted",
                step.status === "skipped" && "bg-muted"
              )}>
                {step.status === "in_progress" ? (
                  <Loader2 className={cn("h-5 w-5 animate-spin", statusColor)} />
                ) : (
                  <StatusIcon className={cn("h-5 w-5", statusColor)} />
                )}
              </div>

              {/* Step Info */}
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">
                    Step {stepNumber}
                  </span>
                  {isCurrentStep && step.status === "in_progress" && (
                    <Badge variant="default" className="text-xs animate-pulse">
                      Running
                    </Badge>
                  )}
                </div>
                <h4 className={cn(
                  "font-medium",
                  step.status === "skipped" && "text-muted-foreground line-through"
                )}>
                  {step.title}
                </h4>
              </div>
            </div>

            {/* Expand/Collapse */}
            <div className="flex items-center gap-2">
              {step.progress !== undefined && step.status === "in_progress" && (
                <span className="text-xs text-muted-foreground">
                  {step.progress}%
                </span>
              )}
              {isExpanded ? (
                <ChevronUp className="h-4 w-4 text-muted-foreground" />
              ) : (
                <ChevronDown className="h-4 w-4 text-muted-foreground" />
              )}
            </div>
          </button>
        </CollapsibleTrigger>

        {/* Expanded Content */}
        <CollapsibleContent>
          <div className="px-4 pb-4 pt-2 space-y-3 border-t">
            {/* Description */}
            {step.description && (
              <p className="text-sm text-muted-foreground">
                {step.description}
              </p>
            )}

            {/* Progress Bar for In-Progress Steps */}
            {step.status === "in_progress" && typeof step.progress === "number" && (
              <div className="space-y-1">
                <Progress value={step.progress} className="h-1.5" />
                <p className="text-xs text-muted-foreground text-right">
                  {step.progress}% complete
                </p>
              </div>
            )}

            {/* Preview Data */}
            {step.previewData !== undefined && (
              <div className="p-3 bg-muted/50 rounded-lg">
                <pre className="text-xs text-muted-foreground overflow-x-auto">
                  {String(JSON.stringify(step.previewData, null, 2))}
                </pre>
              </div>
            )}

            {/* Result */}
            {step.result && (
              <div
                className={cn(
                  "flex items-start gap-2 p-3 rounded-lg",
                  step.result.success
                    ? "bg-success/5 text-success"
                    : "bg-destructive/5 text-destructive"
                )}
              >
                {step.result.success ? (
                  <CheckCircle2 className="h-4 w-4 flex-shrink-0 mt-0.5" />
                ) : (
                  <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                )}
                <div className="text-sm">
                  <p>{step.result.message}</p>
                  {step.result.data !== undefined && (
                    <pre className="mt-2 text-xs opacity-70 overflow-x-auto">
                      {String(JSON.stringify(step.result.data, null, 2))}
                    </pre>
                  )}
                </div>
              </div>
            )}

            {/* Step Actions */}
            {(onRetry || onSkip) && step.status !== "completed" && (
              <div className="flex items-center gap-2 pt-2">
                {onRetry && step.status === "error" && (
                  <Button variant="outline" size="sm" onClick={onRetry}>
                    <RotateCcw className="h-3 w-3 mr-1" />
                    Retry
                  </Button>
                )}
                {onSkip && step.status !== "skipped" && (
                  <Button variant="ghost" size="sm" onClick={onSkip}>
                    <SkipForward className="h-3 w-3 mr-1" />
                    Skip
                  </Button>
                )}
              </div>
            )}
          </div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
}

// ============================================================================
// Helper Functions
// ============================================================================

function getStatusIcon(status: OperationStep["status"]) {
  switch (status) {
    case "completed":
      return CheckCircle2;
    case "in_progress":
      return Loader2;
    case "error":
      return XCircle;
    case "skipped":
      return SkipForward;
    default:
      return Circle;
  }
}

function getStatusColor(status: OperationStep["status"]) {
  switch (status) {
    case "completed":
      return "text-success";
    case "in_progress":
      return "text-primary";
    case "error":
      return "text-destructive";
    case "skipped":
      return "text-muted-foreground";
    default:
      return "text-muted-foreground";
  }
}

// ============================================================================
// Compact Multi-Step Progress (for inline use)
// ============================================================================

interface CompactMultiStepProgressProps {
  operation: MultiStepOperation;
  className?: string;
}

export function CompactMultiStepProgress({
  operation,
  className,
}: CompactMultiStepProgressProps) {
  const currentStep = operation.steps[operation.currentStepIndex];

  return (
    <div className={cn("space-y-2", className)}>
      {/* Step Indicators */}
      <div className="flex items-center gap-1">
        {operation.steps.map((step, index) => {
          const StatusIcon = getStatusIcon(step.status);
          const statusColor = getStatusColor(step.status);

          return (
            <div key={step.id} className="flex items-center">
              <div
                className={cn(
                  "w-6 h-6 rounded-full flex items-center justify-center",
                  step.status === "completed" && "bg-success/10",
                  step.status === "in_progress" && "bg-primary/10",
                  step.status === "error" && "bg-destructive/10",
                  step.status === "pending" && "bg-muted"
                )}
              >
                {step.status === "in_progress" ? (
                  <Loader2 className={cn("h-3 w-3 animate-spin", statusColor)} />
                ) : (
                  <StatusIcon className={cn("h-3 w-3", statusColor)} />
                )}
              </div>
              {index < operation.steps.length - 1 && (
                <div
                  className={cn(
                    "w-8 h-0.5",
                    step.status === "completed" ? "bg-success" : "bg-muted"
                  )}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* Current Step Info */}
      {currentStep && (
        <p className="text-xs text-muted-foreground">
          {currentStep.status === "in_progress" ? (
            <span className="flex items-center gap-1">
              <Loader2 className="h-3 w-3 animate-spin" />
              {currentStep.title}
            </span>
          ) : (
            `Next: ${currentStep.title}`
          )}
        </p>
      )}
    </div>
  );
}

export default MultiStepView;
