"use client";

import * as React from "react";
import {
  Sparkles,
  RefreshCw,
  Copy,
  Check,
  AlertCircle,
  Clock,
  MessageSquare,
  Lightbulb,
  Loader2,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import type { AISummary } from "@/lib/store/patient-profile-store";

// ============================================================================
// Types
// ============================================================================

interface AISummaryCardProps {
  summary: AISummary | null;
  isLoading?: boolean;
  onRegenerate?: () => void;
  className?: string;
}

// ============================================================================
// AI Summary Card Component
// ============================================================================

export function AISummaryCard({
  summary,
  isLoading = false,
  onRegenerate,
  className,
}: AISummaryCardProps) {
  const [copied, setCopied] = React.useState(false);
  const [isExpanded, setIsExpanded] = React.useState(true);

  const handleCopy = async () => {
    if (!summary) return;

    const textToCopy = `
Patient Summary:
${summary.content}

Recent Activity:
${summary.recentActivity.map((a) => `• ${a}`).join("\n")}

Key Concerns:
${summary.keyConcerns.map((c) => `• ${c}`).join("\n")}

Suggested Discussion Points:
${summary.suggestedDiscussionPoints.map((p, i) => `${i + 1}. ${p}`).join("\n")}
    `.trim();

    try {
      await navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error("Failed to copy:", error);
    }
  };

  const formatTimeAgo = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  // Loading state
  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" />
            AI Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 gap-3">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">Generating summary...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // No summary state
  if (!summary) {
    return (
      <Card className={className}>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" />
            AI Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 gap-3 text-center">
            <Sparkles className="h-8 w-8 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">
              No AI summary available yet.
            </p>
            <Button variant="outline" size="sm" onClick={onRegenerate}>
              <Sparkles className="h-4 w-4 mr-2" />
              Generate Summary
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn("border-primary/20", className)}>
      <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              AI Summary
            </CardTitle>

            <div className="flex items-center gap-2">
              {/* Generated time */}
              <Badge variant="outline" className="text-xs text-muted-foreground">
                {formatTimeAgo(summary.generatedAt)}
              </Badge>

              {/* Regenerate button */}
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={onRegenerate}
                disabled={isLoading}
              >
                <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
              </Button>

              {/* Copy button */}
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={handleCopy}
              >
                {copied ? (
                  <Check className="h-4 w-4 text-success" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>

              {/* Collapse toggle */}
              <CollapsibleTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  {isExpanded ? (
                    <ChevronUp className="h-4 w-4" />
                  ) : (
                    <ChevronDown className="h-4 w-4" />
                  )}
                </Button>
              </CollapsibleTrigger>
            </div>
          </div>
        </CardHeader>

        <CollapsibleContent>
          <CardContent className="space-y-4">
            {/* Main Summary */}
            <div className="p-4 bg-primary/5 rounded-lg border border-primary/10">
              <p className="text-foreground leading-relaxed">{summary.content}</p>
            </div>

            {/* Recent Activity */}
            {summary.recentActivity.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium flex items-center gap-2">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  Recent Activity
                </h4>
                <ul className="space-y-1.5">
                  {summary.recentActivity.map((activity, index) => (
                    <li
                      key={index}
                      className="text-sm text-muted-foreground flex items-start gap-2"
                    >
                      <span className="text-primary mt-1">•</span>
                      <span>{activity}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Key Concerns */}
            {summary.keyConcerns.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-warning" />
                  Key Concerns
                </h4>
                <ul className="space-y-1.5">
                  {summary.keyConcerns.map((concern, index) => (
                    <li
                      key={index}
                      className="text-sm flex items-start gap-2 p-2 rounded bg-warning/5 border border-warning/10"
                    >
                      <span className="text-warning mt-0.5">•</span>
                      <span className="text-foreground">{concern}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Suggested Discussion Points */}
            {summary.suggestedDiscussionPoints.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium flex items-center gap-2">
                  <Lightbulb className="h-4 w-4 text-info" />
                  Suggested Discussion Points
                </h4>
                <ol className="space-y-1.5">
                  {summary.suggestedDiscussionPoints.map((point, index) => (
                    <li
                      key={index}
                      className="text-sm flex items-start gap-2 p-2 rounded bg-info/5 border border-info/10"
                    >
                      <span className="text-info font-medium min-w-[20px]">
                        {index + 1}.
                      </span>
                      <span className="text-foreground">{point}</span>
                    </li>
                  ))}
                </ol>
              </div>
            )}

            {/* AI Disclaimer */}
            <p className="text-xs text-muted-foreground flex items-center gap-1 pt-2 border-t">
              <Sparkles className="h-3 w-3" />
              AI-generated summary. Always verify with patient records.
            </p>
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
}

// ============================================================================
// Compact AI Summary (for use in sidebars)
// ============================================================================

interface CompactAISummaryProps {
  summary: AISummary | null;
  onExpand?: () => void;
  className?: string;
}

export function CompactAISummary({
  summary,
  onExpand,
  className,
}: CompactAISummaryProps) {
  if (!summary) {
    return (
      <div className={cn("p-4 bg-muted/50 rounded-lg text-center", className)}>
        <Sparkles className="h-5 w-5 text-muted-foreground mx-auto mb-2" />
        <p className="text-sm text-muted-foreground">No summary available</p>
      </div>
    );
  }

  return (
    <div className={cn("p-4 bg-primary/5 rounded-lg border border-primary/10", className)}>
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium">AI Summary</span>
        </div>
        {onExpand && (
          <Button variant="ghost" size="sm" className="h-6 text-xs" onClick={onExpand}>
            View Full
          </Button>
        )}
      </div>
      <p className="text-sm text-muted-foreground line-clamp-3">{summary.content}</p>

      {summary.keyConcerns.length > 0 && (
        <div className="mt-3 flex items-center gap-2">
          <AlertCircle className="h-3 w-3 text-warning flex-shrink-0" />
          <span className="text-xs text-warning line-clamp-1">
            {summary.keyConcerns.length} concern{summary.keyConcerns.length !== 1 ? "s" : ""} identified
          </span>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// AI Summary Loading Skeleton
// ============================================================================

export function AISummarySkeleton({ className }: { className?: string }) {
  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          AI Summary
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="p-4 bg-muted/50 rounded-lg space-y-2">
          <div className="h-4 bg-muted rounded animate-pulse w-full" />
          <div className="h-4 bg-muted rounded animate-pulse w-5/6" />
          <div className="h-4 bg-muted rounded animate-pulse w-4/6" />
        </div>
        <div className="space-y-2">
          <div className="h-4 bg-muted rounded animate-pulse w-24" />
          <div className="h-3 bg-muted rounded animate-pulse w-full" />
          <div className="h-3 bg-muted rounded animate-pulse w-5/6" />
        </div>
      </CardContent>
    </Card>
  );
}

export default AISummaryCard;
