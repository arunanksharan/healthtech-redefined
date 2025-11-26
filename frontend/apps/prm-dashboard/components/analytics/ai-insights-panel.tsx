"use client";

import * as React from "react";
import {
  Lightbulb,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Target,
  ChevronRight,
  Sparkles,
  RefreshCw,
  Pin,
  PinOff,
  ExternalLink,
  ThumbsUp,
  ThumbsDown,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { AIInsight } from "@/lib/store/analytics-store";
import { formatDistanceToNow } from "date-fns";

// ============================================================================
// Types
// ============================================================================

export type InsightCategory = "revenue" | "operations" | "clinical" | "experience" | "prediction";
export type InsightSentiment = "positive" | "negative" | "neutral" | "warning";
export type InsightImpact = "high" | "medium" | "low";

export interface AIInsightCardProps {
  insight: AIInsight;
  onAction?: (action: string) => void;
  onPin?: () => void;
  onDismiss?: () => void;
  onFeedback?: (helpful: boolean) => void;
  compact?: boolean;
  className?: string;
}

// ============================================================================
// Insight Card Component
// ============================================================================

export function AIInsightCard({
  insight,
  onAction,
  onPin,
  onDismiss,
  onFeedback,
  compact = false,
  className,
}: AIInsightCardProps) {
  const [isPinned, setIsPinned] = React.useState(false);
  const [feedbackGiven, setFeedbackGiven] = React.useState<boolean | null>(null);

  const categoryIcons = {
    revenue: TrendingUp,
    operations: Target,
    clinical: Lightbulb,
    experience: Sparkles,
    prediction: Clock,
  };

  const categoryColors = {
    revenue: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
    operations: "bg-blue-500/10 text-blue-500 border-blue-500/20",
    clinical: "bg-purple-500/10 text-purple-500 border-purple-500/20",
    experience: "bg-pink-500/10 text-pink-500 border-pink-500/20",
    prediction: "bg-amber-500/10 text-amber-500 border-amber-500/20",
  };

  const sentimentStyles = {
    positive: { icon: TrendingUp, color: "text-emerald-500" },
    negative: { icon: TrendingDown, color: "text-red-500" },
    neutral: { icon: Lightbulb, color: "text-primary" },
    warning: { icon: AlertTriangle, color: "text-amber-500" },
  };

  const impactStyles = {
    high: "bg-red-500/10 text-red-500 border-red-500/20",
    medium: "bg-amber-500/10 text-amber-500 border-amber-500/20",
    low: "bg-blue-500/10 text-blue-500 border-blue-500/20",
  };

  const CategoryIcon = categoryIcons[insight.category];
  const SentimentIcon = sentimentStyles[insight.sentiment].icon;

  const handlePin = () => {
    setIsPinned(!isPinned);
    onPin?.();
  };

  const handleFeedback = (helpful: boolean) => {
    setFeedbackGiven(helpful);
    onFeedback?.(helpful);
  };

  if (compact) {
    return (
      <div className={cn("flex items-start gap-3 p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors", className)}>
        <div className={cn("h-8 w-8 rounded-lg flex items-center justify-center flex-shrink-0", categoryColors[insight.category])}>
          <CategoryIcon className="h-4 w-4" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium line-clamp-2">{insight.title}</p>
          <div className="flex items-center gap-2 mt-1">
            <Badge variant="outline" className="text-xs h-5">
              {insight.category}
            </Badge>
            <span className="text-xs text-muted-foreground">
              {formatDistanceToNow(new Date(insight.createdAt), { addSuffix: true })}
            </span>
          </div>
        </div>
        <ChevronRight className="h-4 w-4 text-muted-foreground flex-shrink-0" />
      </div>
    );
  }

  return (
    <Card className={cn("transition-all hover:shadow-md", isPinned && "ring-2 ring-primary/20", className)}>
      <CardContent className="pt-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-start gap-3">
            <div className={cn("h-10 w-10 rounded-lg flex items-center justify-center", categoryColors[insight.category])}>
              <CategoryIcon className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-semibold">{insight.title}</h3>
                <SentimentIcon className={cn("h-4 w-4", sentimentStyles[insight.sentiment].color)} />
              </div>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant="outline" className={cn("text-xs", impactStyles[insight.impact])}>
                  {insight.impact} impact
                </Badge>
                <span className="text-xs text-muted-foreground">
                  {formatDistanceToNow(new Date(insight.createdAt), { addSuffix: true })}
                </span>
              </div>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={handlePin}
          >
            {isPinned ? <PinOff className="h-4 w-4" /> : <Pin className="h-4 w-4" />}
          </Button>
        </div>

        {/* Description */}
        <p className="text-sm text-muted-foreground mb-4">{insight.description}</p>

        {/* Key Metrics */}
        {insight.metrics && insight.metrics.length > 0 && (
          <div className="grid grid-cols-2 gap-2 mb-4">
            {insight.metrics.map((metric, index) => (
              <div key={index} className="flex items-center justify-between p-2 bg-muted/50 rounded">
                <span className="text-xs text-muted-foreground">{metric.label}</span>
                <span className="text-sm font-medium flex items-center gap-1">
                  {metric.value}
                  {metric.change && (
                    <span className={cn(
                      "text-xs",
                      metric.change > 0 ? "text-emerald-500" : "text-red-500"
                    )}>
                      {metric.change > 0 ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                      {Math.abs(metric.change)}%
                    </span>
                  )}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Suggested Actions */}
        {insight.suggestedActions && insight.suggestedActions.length > 0 && (
          <div className="space-y-2 mb-4">
            <p className="text-xs font-medium text-muted-foreground flex items-center gap-1">
              <Lightbulb className="h-3 w-3" />
              Suggested Actions
            </p>
            <div className="space-y-1">
              {insight.suggestedActions.map((action, index) => (
                <Button
                  key={index}
                  variant="outline"
                  size="sm"
                  className="w-full justify-between text-left h-auto py-2"
                  onClick={() => onAction?.(action.id)}
                >
                  <span className="text-sm">{action.label}</span>
                  <ExternalLink className="h-3 w-3 flex-shrink-0" />
                </Button>
              ))}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between pt-3 border-t">
          <div className="flex items-center gap-1">
            <span className="text-xs text-muted-foreground mr-2">Helpful?</span>
            <Button
              variant={feedbackGiven === true ? "default" : "ghost"}
              size="icon"
              className="h-7 w-7"
              onClick={() => handleFeedback(true)}
              disabled={feedbackGiven !== null}
            >
              <ThumbsUp className="h-3 w-3" />
            </Button>
            <Button
              variant={feedbackGiven === false ? "default" : "ghost"}
              size="icon"
              className="h-7 w-7"
              onClick={() => handleFeedback(false)}
              disabled={feedbackGiven !== null}
            >
              <ThumbsDown className="h-3 w-3" />
            </Button>
          </div>
          <Button variant="ghost" size="sm" onClick={onDismiss}>
            Dismiss
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// AI Insights Panel Component
// ============================================================================

export interface AIInsightsPanelProps {
  insights: AIInsight[];
  title?: string;
  maxVisible?: number;
  showSeeAll?: boolean;
  onSeeAll?: () => void;
  onInsightAction?: (insightId: string, action: string) => void;
  onRefresh?: () => void;
  isLoading?: boolean;
  className?: string;
}

export function AIInsightsPanel({
  insights,
  title = "AI Insights",
  maxVisible = 3,
  showSeeAll = true,
  onSeeAll,
  onInsightAction,
  onRefresh,
  isLoading = false,
  className,
}: AIInsightsPanelProps) {
  const visibleInsights = insights.slice(0, maxVisible);
  const hasMore = insights.length > maxVisible;

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-base font-medium flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" />
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-1/2" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-base font-medium flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          {title}
        </CardTitle>
        <div className="flex items-center gap-2">
          {onRefresh && (
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onRefresh}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          )}
          {showSeeAll && hasMore && (
            <Button variant="ghost" size="sm" onClick={onSeeAll}>
              See All ({insights.length})
              <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {insights.length === 0 ? (
          <div className="text-center py-8">
            <Sparkles className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">No insights available</p>
          </div>
        ) : (
          <div className="space-y-3">
            {visibleInsights.map((insight) => (
              <AIInsightCard
                key={insight.id}
                insight={insight}
                compact
                onAction={(action) => onInsightAction?.(insight.id, action)}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Expanded AI Insights View
// ============================================================================

export interface AIInsightsExpandedProps {
  insights: AIInsight[];
  selectedCategory?: InsightCategory | "all";
  onCategoryChange?: (category: InsightCategory | "all") => void;
  onInsightAction?: (insightId: string, action: string) => void;
  onRefresh?: () => void;
  isLoading?: boolean;
  className?: string;
}

export function AIInsightsExpanded({
  insights,
  selectedCategory = "all",
  onCategoryChange,
  onInsightAction,
  onRefresh,
  isLoading = false,
  className,
}: AIInsightsExpandedProps) {
  const categories: (InsightCategory | "all")[] = ["all", "revenue", "operations", "clinical", "experience", "prediction"];

  const filteredInsights = selectedCategory === "all"
    ? insights
    : insights.filter((i) => i.category === selectedCategory);

  return (
    <div className={cn("space-y-4", className)}>
      {/* Category filters */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2">
        {categories.map((category) => (
          <Button
            key={category}
            variant={selectedCategory === category ? "default" : "outline"}
            size="sm"
            onClick={() => onCategoryChange?.(category)}
            className="capitalize"
          >
            {category}
          </Button>
        ))}
        {onRefresh && (
          <Button variant="ghost" size="icon" className="h-8 w-8 ml-auto" onClick={onRefresh}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* Insights grid */}
      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="p-6">
              <div className="space-y-3">
                <Skeleton className="h-5 w-3/4" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-2/3" />
              </div>
            </Card>
          ))}
        </div>
      ) : filteredInsights.length === 0 ? (
        <div className="text-center py-12">
          <Sparkles className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">No insights in this category</h3>
          <p className="text-sm text-muted-foreground">Check back later for new insights</p>
        </div>
      ) : (
        <ScrollArea className="h-[600px]">
          <div className="grid gap-4 md:grid-cols-2 pr-4">
            {filteredInsights.map((insight) => (
              <AIInsightCard
                key={insight.id}
                insight={insight}
                onAction={(action) => onInsightAction?.(insight.id, action)}
              />
            ))}
          </div>
        </ScrollArea>
      )}
    </div>
  );
}

export default AIInsightsPanel;
