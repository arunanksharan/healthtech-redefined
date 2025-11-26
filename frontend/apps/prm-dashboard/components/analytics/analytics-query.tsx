"use client";

import * as React from "react";
import {
  Mic,
  MicOff,
  Send,
  Loader2,
  Sparkles,
  BarChart3,
  Table,
  FileText,
  List,
  Pin,
  Download,
  Share2,
  RefreshCw,
  ChevronRight,
  Clock,
  X,
  Volume2,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table as TableComponent,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { AnalyticsQuery } from "@/lib/store/analytics-store";
import { format } from "date-fns";

// ============================================================================
// Types
// ============================================================================

export type QueryResponseType = "text" | "chart" | "table" | "document" | "list";

export interface QueryResponse {
  type: QueryResponseType;
  content: any;
  insights?: string[];
  followUpQuestions?: string[];
}

export interface QueryHistoryItem {
  id: string;
  query: string;
  response: QueryResponse;
  timestamp: Date;
  isPinned?: boolean;
}

// ============================================================================
// Query Input Component
// ============================================================================

interface AnalyticsQueryInputProps {
  onSubmit: (query: string) => void;
  isLoading?: boolean;
  placeholder?: string;
  suggestions?: string[];
  className?: string;
}

export function AnalyticsQueryInput({
  onSubmit,
  isLoading = false,
  placeholder = "Ask anything about your analytics...",
  suggestions = [
    "What's our revenue by department this quarter?",
    "Show me no-show trends by department",
    "Why did patient satisfaction drop last week?",
    "Compare this month's performance to last month",
  ],
  className,
}: AnalyticsQueryInputProps) {
  const [query, setQuery] = React.useState("");
  const [isListening, setIsListening] = React.useState(false);
  const [showSuggestions, setShowSuggestions] = React.useState(false);
  const inputRef = React.useRef<HTMLInputElement>(null);

  // Web Speech API for voice input
  const startListening = () => {
    if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;

      recognition.onstart = () => setIsListening(true);
      recognition.onend = () => setIsListening(false);
      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setQuery(transcript);
      };

      recognition.start();
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSubmit(query.trim());
      setQuery("");
      setShowSuggestions(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
    onSubmit(suggestion);
    setShowSuggestions(false);
  };

  return (
    <div className={cn("relative", className)}>
      <form onSubmit={handleSubmit}>
        <div className="relative flex items-center">
          <Sparkles className="absolute left-3 h-5 w-5 text-primary" />
          <Input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => setShowSuggestions(true)}
            placeholder={placeholder}
            className="pl-10 pr-24 h-12 text-base"
            disabled={isLoading}
          />
          <div className="absolute right-2 flex items-center gap-1">
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={startListening}
              disabled={isLoading}
            >
              {isListening ? (
                <MicOff className="h-4 w-4 text-red-500" />
              ) : (
                <Mic className="h-4 w-4" />
              )}
            </Button>
            <Button
              type="submit"
              size="icon"
              className="h-8 w-8"
              disabled={!query.trim() || isLoading}
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </form>

      {/* Suggestions dropdown */}
      {showSuggestions && suggestions.length > 0 && !query && (
        <Card className="absolute top-full left-0 right-0 mt-2 z-50">
          <CardContent className="p-2">
            <p className="text-xs text-muted-foreground px-2 py-1">Try asking:</p>
            {suggestions.map((suggestion, index) => (
              <Button
                key={index}
                variant="ghost"
                className="w-full justify-start text-left h-auto py-2 px-2"
                onClick={() => handleSuggestionClick(suggestion)}
              >
                <Sparkles className="h-3 w-3 mr-2 text-primary flex-shrink-0" />
                <span className="text-sm truncate">{suggestion}</span>
              </Button>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ============================================================================
// Query Response Component
// ============================================================================

interface QueryResponseDisplayProps {
  query: string;
  response: QueryResponse;
  onFollowUp?: (question: string) => void;
  onPin?: () => void;
  onExport?: () => void;
  onShare?: () => void;
  className?: string;
}

export function QueryResponseDisplay({
  query,
  response,
  onFollowUp,
  onPin,
  onExport,
  onShare,
  className,
}: QueryResponseDisplayProps) {
  const renderContent = () => {
    switch (response.type) {
      case "chart":
        return (
          <div className="bg-muted/30 rounded-lg p-4">
            {/* Placeholder for chart - actual chart component would be rendered here */}
            <div className="h-64 flex items-center justify-center border-2 border-dashed rounded">
              <div className="text-center">
                <BarChart3 className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">Chart visualization</p>
              </div>
            </div>
          </div>
        );

      case "table":
        return (
          <div className="border rounded-lg overflow-hidden">
            <TableComponent>
              <TableHeader>
                <TableRow>
                  {response.content.headers?.map((header: string, i: number) => (
                    <TableHead key={i}>{header}</TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {response.content.rows?.map((row: any[], rowIndex: number) => (
                  <TableRow key={rowIndex}>
                    {row.map((cell, cellIndex) => (
                      <TableCell key={cellIndex}>{cell}</TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </TableComponent>
          </div>
        );

      case "list":
        return (
          <ul className="space-y-2">
            {response.content.items?.map((item: string, i: number) => (
              <li key={i} className="flex items-start gap-2">
                <span className="h-5 w-5 rounded-full bg-primary/10 text-primary text-xs flex items-center justify-center flex-shrink-0 mt-0.5">
                  {i + 1}
                </span>
                <span className="text-sm">{item}</span>
              </li>
            ))}
          </ul>
        );

      case "document":
        return (
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <div dangerouslySetInnerHTML={{ __html: response.content.html || response.content.text }} />
          </div>
        );

      default:
        return (
          <p className="text-sm whitespace-pre-wrap">{response.content}</p>
        );
    }
  };

  const typeIcons = {
    text: Sparkles,
    chart: BarChart3,
    table: Table,
    document: FileText,
    list: List,
  };

  const TypeIcon = typeIcons[response.type];

  return (
    <Card className={className}>
      <CardContent className="pt-6">
        {/* User query */}
        <div className="flex items-start gap-3 mb-4">
          <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center text-sm font-medium">
            You
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium">{query}</p>
          </div>
        </div>

        <Separator className="my-4" />

        {/* AI response */}
        <div className="flex items-start gap-3">
          <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
            <Sparkles className="h-4 w-4 text-primary" />
          </div>
          <div className="flex-1 min-w-0">
            {/* Response type badge */}
            <div className="flex items-center gap-2 mb-3">
              <Badge variant="secondary" className="text-xs">
                <TypeIcon className="h-3 w-3 mr-1" />
                {response.type}
              </Badge>
            </div>

            {/* Content */}
            {renderContent()}

            {/* Insights */}
            {response.insights && response.insights.length > 0 && (
              <div className="mt-4 p-3 bg-primary/5 rounded-lg border border-primary/10">
                <p className="text-xs font-medium text-primary mb-2 flex items-center gap-1">
                  <Sparkles className="h-3 w-3" />
                  Key Observations
                </p>
                <ul className="space-y-1">
                  {response.insights.map((insight, i) => (
                    <li key={i} className="text-sm text-muted-foreground">• {insight}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Follow-up questions */}
            {response.followUpQuestions && response.followUpQuestions.length > 0 && (
              <div className="mt-4">
                <p className="text-xs text-muted-foreground mb-2">Follow-up questions:</p>
                <div className="flex flex-wrap gap-2">
                  {response.followUpQuestions.map((question, i) => (
                    <Button
                      key={i}
                      variant="outline"
                      size="sm"
                      className="h-auto py-1.5 px-3 text-xs"
                      onClick={() => onFollowUp?.(question)}
                    >
                      {question}
                    </Button>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center gap-2 mt-4 pt-4 border-t">
              <Button variant="ghost" size="sm" onClick={onExport}>
                <Download className="h-4 w-4 mr-1" />
                Export
              </Button>
              <Button variant="ghost" size="sm" onClick={onShare}>
                <Share2 className="h-4 w-4 mr-1" />
                Share
              </Button>
              <Button variant="ghost" size="sm" onClick={onPin}>
                <Pin className="h-4 w-4 mr-1" />
                Pin to Dashboard
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Analytics Assistant Dialog
// ============================================================================

interface AnalyticsAssistantDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onQuery: (query: string) => Promise<QueryResponse>;
  queryHistory?: QueryHistoryItem[];
  className?: string;
}

export function AnalyticsAssistantDialog({
  isOpen,
  onClose,
  onQuery,
  queryHistory = [],
  className,
}: AnalyticsAssistantDialogProps) {
  const [currentQuery, setCurrentQuery] = React.useState<string | null>(null);
  const [currentResponse, setCurrentResponse] = React.useState<QueryResponse | null>(null);
  const [isLoading, setIsLoading] = React.useState(false);

  const handleQuery = async (query: string) => {
    setCurrentQuery(query);
    setIsLoading(true);
    try {
      const response = await onQuery(query);
      setCurrentResponse(response);
    } catch (error) {
      setCurrentResponse({
        type: "text",
        content: "Sorry, I couldn't process that query. Please try again.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            Analytics Assistant
          </DialogTitle>
          <DialogDescription>
            Ask questions about your analytics in natural language
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Query input */}
          <AnalyticsQueryInput
            onSubmit={handleQuery}
            isLoading={isLoading}
          />

          {/* Response */}
          <ScrollArea className="h-[400px]">
            {isLoading ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground">Analyzing your data...</p>
                </div>
              </div>
            ) : currentQuery && currentResponse ? (
              <QueryResponseDisplay
                query={currentQuery}
                response={currentResponse}
                onFollowUp={handleQuery}
              />
            ) : queryHistory.length > 0 ? (
              <div className="space-y-4">
                <p className="text-sm font-medium text-muted-foreground">Recent queries:</p>
                {queryHistory.slice(0, 5).map((item) => (
                  <div
                    key={item.id}
                    className="flex items-start gap-3 p-3 rounded-lg border bg-card hover:bg-accent/50 cursor-pointer transition-colors"
                    onClick={() => handleQuery(item.query)}
                  >
                    <Clock className="h-4 w-4 text-muted-foreground flex-shrink-0 mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{item.query}</p>
                      <p className="text-xs text-muted-foreground">
                        {format(new Date(item.timestamp), "MMM d, h:mm a")}
                      </p>
                    </div>
                    <ChevronRight className="h-4 w-4 text-muted-foreground" />
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <Sparkles className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="font-medium mb-2">Ask me anything</h3>
                  <p className="text-sm text-muted-foreground">
                    I can help you understand your analytics, trends, and provide insights
                  </p>
                </div>
              </div>
            )}
          </ScrollArea>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ============================================================================
// Compact Query Widget
// ============================================================================

interface CompactQueryWidgetProps {
  onOpen: () => void;
  recentQuery?: string;
  className?: string;
}

export function CompactQueryWidget({
  onOpen,
  recentQuery,
  className,
}: CompactQueryWidgetProps) {
  return (
    <div
      className={cn(
        "flex items-center gap-3 p-3 rounded-lg border bg-card hover:bg-accent/50 cursor-pointer transition-colors",
        className
      )}
      onClick={onOpen}
    >
      <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
        <Sparkles className="h-5 w-5 text-primary" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium">Ask Analytics</p>
        <p className="text-xs text-muted-foreground truncate">
          {recentQuery || "Ask questions in natural language..."}
        </p>
      </div>
      <div className="flex items-center gap-1">
        <Mic className="h-4 w-4 text-muted-foreground" />
        <ChevronRight className="h-4 w-4 text-muted-foreground" />
      </div>
    </div>
  );
}

export default AnalyticsQueryInput;
