"use client";

import * as React from "react";
import {
  Search,
  Mic,
  MicOff,
  Send,
  X,
  Sparkles,
  TrendingUp,
  FileText,
  Table,
  List,
  Copy,
  Download,
  Plus,
  ChevronRight,
  Loader2,
  ArrowUp,
  MessageSquare,
  BarChart3,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import type { QueryResponse } from "@/lib/store/patient-profile-store";
import { format } from "date-fns";

// ============================================================================
// Types
// ============================================================================

interface AskPatientDataProps {
  isOpen: boolean;
  onClose: () => void;
  patientId: string;
  patientName: string;
  onQuery: (query: string) => Promise<void>;
  queryHistory: QueryResponse[];
  isLoading: boolean;
  suggestedQuestions?: string[];
  className?: string;
}

// ============================================================================
// Default Suggested Questions
// ============================================================================

const defaultSuggestedQuestions = [
  "Show BP trend over the last 6 months",
  "When was the last A1C test?",
  "List all current medications",
  "Compare weight changes over the past year",
  "Show all lab results from last visit",
  "Summarize recent communications",
  "What care gaps are overdue?",
  "Draft a referral letter based on the last consultation",
];

// ============================================================================
// Voice Input Hook
// ============================================================================

function useVoiceInput() {
  const [isListening, setIsListening] = React.useState(false);
  const [transcript, setTranscript] = React.useState("");
  const recognitionRef = React.useRef<SpeechRecognition | null>(null);

  React.useEffect(() => {
    if (typeof window !== "undefined") {
      const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        recognitionRef.current = new SpeechRecognition();
        recognitionRef.current.continuous = false;
        recognitionRef.current.interimResults = true;

        recognitionRef.current.onresult = (event) => {
          const result = event.results[event.results.length - 1];
          setTranscript(result[0].transcript);
        };

        recognitionRef.current.onend = () => {
          setIsListening(false);
        };

        recognitionRef.current.onerror = () => {
          setIsListening(false);
        };
      }
    }

    return () => {
      recognitionRef.current?.abort();
    };
  }, []);

  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      setTranscript("");
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
  };

  const toggleListening = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  return { isListening, transcript, toggleListening, setTranscript };
}

// ============================================================================
// Response Renderers
// ============================================================================

interface ResponseRendererProps {
  response: QueryResponse;
  onCopy?: () => void;
  onExport?: () => void;
  onAddToNote?: () => void;
}

function TextResponse({ response, onCopy }: ResponseRendererProps) {
  return (
    <div className="space-y-3">
      <div className="p-4 bg-muted/50 rounded-lg">
        <p className="text-sm whitespace-pre-wrap">{response.content as string}</p>
      </div>
      {response.analysis && (
        <div className="p-4 bg-primary/5 rounded-lg border border-primary/10">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="h-4 w-4 text-primary" />
            <span className="text-sm font-medium">Analysis</span>
          </div>
          <p className="text-sm text-muted-foreground">{response.analysis}</p>
        </div>
      )}
    </div>
  );
}

function ChartResponse({ response }: ResponseRendererProps) {
  // In production, this would render actual charts with Recharts
  const data = response.content as { title: string; values: { label: string; value: number }[] };

  return (
    <div className="space-y-3">
      <div className="p-4 bg-muted/50 rounded-lg">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium">{data?.title || "Chart"}</span>
        </div>
        {/* Placeholder chart visualization */}
        <div className="h-48 bg-gradient-to-t from-primary/10 to-transparent rounded-lg flex items-end justify-around p-4">
          {(data?.values || []).map((item, i) => (
            <div key={i} className="flex flex-col items-center gap-1">
              <div
                className="w-8 bg-primary/60 rounded-t"
                style={{ height: `${(item.value / 200) * 100}%` }}
              />
              <span className="text-xs text-muted-foreground">{item.label}</span>
            </div>
          ))}
        </div>
      </div>
      {response.analysis && (
        <div className="p-4 bg-primary/5 rounded-lg border border-primary/10">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="h-4 w-4 text-primary" />
            <span className="text-sm font-medium">Analysis</span>
          </div>
          <p className="text-sm text-muted-foreground">{response.analysis}</p>
        </div>
      )}
    </div>
  );
}

function DocumentResponse({ response, onCopy, onExport }: ResponseRendererProps) {
  const doc = response.content as { title: string; body: string };

  return (
    <div className="space-y-3">
      <div className="p-4 bg-card rounded-lg border">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-primary" />
            <span className="text-sm font-medium">{doc?.title || "Document"}</span>
          </div>
          <div className="flex items-center gap-1">
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onCopy}>
              <Copy className="h-3 w-3" />
            </Button>
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onExport}>
              <Download className="h-3 w-3" />
            </Button>
          </div>
        </div>
        <div className="p-4 bg-muted/50 rounded-lg text-sm whitespace-pre-wrap font-mono">
          {String(doc?.body || response.content || "")}
        </div>
      </div>
    </div>
  );
}

function TableResponse({ response }: ResponseRendererProps) {
  const tableData = response.content as { headers: string[]; rows: string[][] };

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto rounded-lg border">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr>
              {(tableData?.headers || []).map((header, i) => (
                <th key={i} className="px-4 py-2 text-left font-medium">
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {(tableData?.rows || []).map((row, i) => (
              <tr key={i} className="border-t">
                {row.map((cell, j) => (
                  <td key={j} className="px-4 py-2">
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {response.analysis && (
        <div className="p-4 bg-primary/5 rounded-lg border border-primary/10">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="h-4 w-4 text-primary" />
            <span className="text-sm font-medium">Analysis</span>
          </div>
          <p className="text-sm text-muted-foreground">{response.analysis}</p>
        </div>
      )}
    </div>
  );
}

function ListResponse({ response }: ResponseRendererProps) {
  const items = response.content as string[];

  return (
    <div className="space-y-3">
      <ul className="space-y-2">
        {(items || []).map((item, i) => (
          <li
            key={i}
            className="flex items-start gap-2 p-2 rounded bg-muted/50"
          >
            <span className="text-primary font-medium">{i + 1}.</span>
            <span className="text-sm">{item}</span>
          </li>
        ))}
      </ul>
      {response.analysis && (
        <div className="p-4 bg-primary/5 rounded-lg border border-primary/10">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="h-4 w-4 text-primary" />
            <span className="text-sm font-medium">Analysis</span>
          </div>
          <p className="text-sm text-muted-foreground">{response.analysis}</p>
        </div>
      )}
    </div>
  );
}

function ResponseRenderer(props: ResponseRendererProps) {
  switch (props.response.type) {
    case "chart":
      return <ChartResponse {...props} />;
    case "document":
      return <DocumentResponse {...props} />;
    case "table":
      return <TableResponse {...props} />;
    case "list":
      return <ListResponse {...props} />;
    case "text":
    default:
      return <TextResponse {...props} />;
  }
}

// ============================================================================
// Ask Patient Data Component
// ============================================================================

export function AskPatientData({
  isOpen,
  onClose,
  patientId,
  patientName,
  onQuery,
  queryHistory,
  isLoading,
  suggestedQuestions = defaultSuggestedQuestions,
  className,
}: AskPatientDataProps) {
  const [input, setInput] = React.useState("");
  const inputRef = React.useRef<HTMLInputElement>(null);
  const { isListening, transcript, toggleListening, setTranscript } = useVoiceInput();
  const scrollRef = React.useRef<HTMLDivElement>(null);

  // Update input with voice transcript
  React.useEffect(() => {
    if (transcript) {
      setInput(transcript);
    }
  }, [transcript]);

  // Focus input when dialog opens
  React.useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  // Scroll to bottom when new response arrives
  React.useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [queryHistory]);

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || isLoading) return;

    const query = input.trim();
    setInput("");
    setTranscript("");
    await onQuery(query);
  };

  const handleSuggestedClick = (question: string) => {
    setInput(question);
    inputRef.current?.focus();
  };

  const handleCopy = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
    } catch (error) {
      console.error("Failed to copy:", error);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className={cn("max-w-2xl max-h-[80vh] flex flex-col p-0", className)}>
        <DialogHeader className="px-6 pt-6 pb-4 border-b">
          <DialogTitle className="flex items-center gap-2">
            <Search className="h-5 w-5 text-primary" />
            Ask Patient Data
          </DialogTitle>
          <p className="text-sm text-muted-foreground">
            Ask anything about <span className="font-medium">{patientName}</span>'s health data
          </p>
        </DialogHeader>

        {/* Content area */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-4">
          {/* Empty state with suggestions */}
          {queryHistory.length === 0 && !isLoading && (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground text-center">
                Try asking questions like:
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {suggestedQuestions.slice(0, 6).map((question, i) => (
                  <Button
                    key={i}
                    variant="outline"
                    size="sm"
                    className="h-auto py-2 px-3 text-left justify-start text-xs"
                    onClick={() => handleSuggestedClick(question)}
                  >
                    <span className="line-clamp-1">{question}</span>
                    <ChevronRight className="h-3 w-3 ml-auto flex-shrink-0" />
                  </Button>
                ))}
              </div>
            </div>
          )}

          {/* Query history */}
          {queryHistory.map((response) => (
            <div key={response.id} className="space-y-3">
              {/* User query */}
              <div className="flex justify-end">
                <div className="bg-primary text-primary-foreground rounded-lg px-4 py-2 max-w-[80%]">
                  <p className="text-sm">{response.query}</p>
                </div>
              </div>

              {/* AI response */}
              <div className="flex justify-start">
                <div className="max-w-[90%] space-y-2">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-primary" />
                    <span className="text-xs text-muted-foreground">
                      {format(new Date(response.timestamp), "h:mm a")}
                    </span>
                  </div>
                  <ResponseRenderer
                    response={response}
                    onCopy={() => handleCopy(JSON.stringify(response.content))}
                  />

                  {/* Response actions */}
                  {response.actions && response.actions.length > 0 && (
                    <div className="flex items-center gap-2 pt-2">
                      {response.actions.map((action) => (
                        <Button
                          key={action.id}
                          variant="outline"
                          size="sm"
                          className="h-7 text-xs"
                        >
                          {action.label}
                        </Button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}

          {/* Loading state */}
          {isLoading && (
            <div className="flex justify-start">
              <div className="flex items-center gap-2 px-4 py-3 bg-muted/50 rounded-lg">
                <Loader2 className="h-4 w-4 animate-spin text-primary" />
                <span className="text-sm text-muted-foreground">Analyzing data...</span>
              </div>
            </div>
          )}
        </div>

        {/* Input area */}
        <div className="border-t p-4">
          <form onSubmit={handleSubmit} className="flex items-center gap-2">
            <div className="flex-1 relative">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={`Ask anything about ${patientName}'s health data...`}
                className="w-full px-4 py-3 pr-20 rounded-lg border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                disabled={isLoading}
              />
              <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                {/* Voice input */}
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className={cn(
                    "h-8 w-8",
                    isListening && "text-destructive bg-destructive/10"
                  )}
                  onClick={toggleListening}
                  disabled={isLoading}
                >
                  {isListening ? (
                    <MicOff className="h-4 w-4" />
                  ) : (
                    <Mic className="h-4 w-4" />
                  )}
                </Button>

                {/* Submit */}
                <Button
                  type="submit"
                  size="icon"
                  className="h-8 w-8"
                  disabled={!input.trim() || isLoading}
                >
                  {isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <ArrowUp className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
          </form>

          {/* Voice indicator */}
          {isListening && (
            <div className="flex items-center gap-2 mt-2 px-2">
              <div className="h-2 w-2 rounded-full bg-destructive animate-pulse" />
              <span className="text-xs text-muted-foreground">Listening...</span>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ============================================================================
// Ask Patient Data Button (trigger)
// ============================================================================

interface AskPatientDataButtonProps {
  onClick: () => void;
  className?: string;
}

export function AskPatientDataButton({ onClick, className }: AskPatientDataButtonProps) {
  return (
    <Button
      variant="outline"
      className={cn("gap-2", className)}
      onClick={onClick}
    >
      <Search className="h-4 w-4" />
      Ask Patient Data
    </Button>
  );
}

// ============================================================================
// Compact Query Widget (for inline use)
// ============================================================================

interface CompactQueryWidgetProps {
  onQuery: (query: string) => Promise<void>;
  isLoading: boolean;
  patientName: string;
  className?: string;
}

export function CompactQueryWidget({
  onQuery,
  isLoading,
  patientName,
  className,
}: CompactQueryWidgetProps) {
  const [input, setInput] = React.useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    await onQuery(input.trim());
    setInput("");
  };

  return (
    <Card className={className}>
      <CardContent className="p-4">
        <form onSubmit={handleSubmit} className="flex items-center gap-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={`Ask about ${patientName}'s data...`}
              className="w-full pl-10 pr-4 py-2 rounded-lg border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
              disabled={isLoading}
            />
          </div>
          <Button type="submit" size="sm" disabled={!input.trim() || isLoading}>
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

export default AskPatientData;
