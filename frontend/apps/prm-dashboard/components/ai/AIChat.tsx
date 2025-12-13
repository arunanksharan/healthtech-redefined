'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Mic, Sparkles, Bot, User, Paperclip } from 'lucide-react';
import { initializeAISystem, processUserInput } from '@/lib/ai';
import toast from 'react-hot-toast';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils/cn';

/**
 * Message type
 */
interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: {
    agentsUsed?: string[];
    executionTime?: number;
    requiresConfirmation?: boolean;
    plan?: any;
  };
}

/**
 * AI Chat Props
 */
interface AIChatProps {
  userId: string;
  orgId: string;
  sessionId: string;
  permissions?: string[];
  onConfirmationRequired?: (plan: any) => void;
}

/**
 * AIChat Component
 * Main chat interface for interacting with the AI system
 */
export function AIChat({
  userId,
  orgId,
  sessionId,
  permissions = [],
  onConfirmationRequired,
}: AIChatProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        "Hi! I'm your Clinical Assistant. I can help you with scheduling, patient records, and workflow automation. How can I assist you today?",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize AI system on mount
  useEffect(() => {
    try {
      initializeAISystem(process.env.NEXT_PUBLIC_OPENAI_API_KEY);
      setIsInitialized(true);
    } catch (error) {
      console.error('Failed to initialize AI system:', error);
      toast.error('Failed to initialize AI assistant');
    }
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  /**
   * Handle sending a message
   */
  const handleSend = async () => {
    if (!input.trim() || isLoading || !isInitialized) return;

    const userMessage: Message = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Process through AI system
      const result = await processUserInput(
        input,
        userId,
        orgId,
        sessionId,
        permissions
      );

      // Check if confirmation is required
      if (result.results?.[0]?.data?.requiresConfirmation) {
        const confirmationMessage: Message = {
          id: `msg_${Date.now()}_confirm`,
          role: 'assistant',
          content: result.message,
          timestamp: new Date(),
          metadata: {
            requiresConfirmation: true,
            plan: result.results[0].data.plan,
            agentsUsed: result.agentsUsed,
          },
        };

        setMessages((prev) => [...prev, confirmationMessage]);

        // Notify parent if handler provided
        if (onConfirmationRequired) {
          onConfirmationRequired(result.results[0].data.plan);
        }
      } else {
        // Regular response
        const assistantMessage: Message = {
          id: `msg_${Date.now()}_assistant`,
          role: 'assistant',
          content: result.message,
          timestamp: new Date(),
          metadata: {
            agentsUsed: result.agentsUsed,
            executionTime: result.metadata?.executionTime,
          },
        };

        setMessages((prev) => [...prev, assistantMessage]);

        // Show success/error toast
        if (result.success) {
          // toast.success('Action completed successfully'); // keeping it quiet for better flow
        } else {
          toast.error('Action failed: ' + result.error?.message);
        }
      }
    } catch (error: any) {
      console.error('Chat error:', error);

      const errorMessage: Message = {
        id: `msg_${Date.now()}_error`,
        role: 'assistant',
        content: `I encountered an error: ${error.message}. Please try again.`,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
      toast.error('Failed to process your request');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle Enter key
   */
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Card className="flex flex-col h-full bg-white dark:bg-zinc-950 border-0 shadow-xl rounded-2xl overflow-hidden ring-1 ring-gray-200 dark:ring-gray-800">
      {/* Header */}
      <div className="flex items-center gap-4 px-6 py-5 bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-900 dark:to-indigo-900 text-white shrink-0 shadow-md relative overflow-hidden">
        {/* Decorative elements */}
        <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full blur-2xl -mr-16 -mt-16 pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-24 h-24 bg-white/5 rounded-full blur-xl -ml-12 -mb-12 pointer-events-none" />

        <div className="relative z-10 w-12 h-12 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center shadow-inner border border-white/20">
          <Sparkles className="w-6 h-6 text-white animate-pulse" />
        </div>
        <div className="relative z-10">
          <h2 className="font-bold text-lg text-white leading-tight tracking-tight">Clinical Assistant</h2>
          <div className="flex items-center gap-2 mt-0.5">
            <span className={cn("w-2 h-2 rounded-full shadow-[0_0_8px_rgba(34,197,94,0.6)]", isInitialized ? "bg-green-400" : "bg-gray-400")} />
            <p className="text-xs text-blue-100 font-medium">
              {isInitialized ? 'Online & Ready' : 'Initializing...'}
            </p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 bg-gray-50/50 dark:bg-zinc-900/50 bg-[radial-gradient(#e5e7eb_1px,transparent_1px)] dark:bg-[radial-gradient(#1f2937_1px,transparent_1px)] [background-size:16px_16px]">
        <div className="px-6 py-6 space-y-6 min-h-full">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-4 ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'} group`}
            >
              {/* Avatar */}
              <Avatar className={cn(
                "w-9 h-9 mt-1 shadow-sm border-2",
                message.role === 'assistant'
                  ? "border-blue-100 dark:border-blue-900"
                  : "border-gray-100 dark:border-gray-800"
              )}>
                {message.role === 'assistant' ? (
                  <>
                    <AvatarImage src="/bot-avatar.png" />
                    <AvatarFallback className="bg-gradient-to-br from-blue-500 to-indigo-600 text-white"><Bot className="w-5 h-5" /></AvatarFallback>
                  </>
                ) : (
                  <>
                    <AvatarFallback className="bg-gradient-to-br from-gray-100 to-gray-200 text-gray-600 dark:from-zinc-800 dark:to-zinc-700 dark:text-gray-300"><User className="w-5 h-5" /></AvatarFallback>
                  </>
                )}
              </Avatar>

              {/* Message Bubble */}
              <div className="flex flex-col max-w-[80%]">
                <div className={cn(
                  "rounded-2xl px-5 py-3.5 shadow-sm text-sm leading-relaxed transition-all duration-300",
                  message.role === 'user'
                    ? 'bg-gradient-to-br from-blue-600 to-indigo-600 text-white rounded-tr-none shadow-blue-500/20'
                    : 'bg-white dark:bg-zinc-900 border border-gray-100 dark:border-gray-800 text-gray-800 dark:text-gray-200 rounded-tl-none shadow-gray-200/50 dark:shadow-none'
                )}>
                  <p className="whitespace-pre-wrap">{message.content}</p>
                </div>

                {/* Metadata & Timestamp */}
                <div className={cn(
                  "flex items-center gap-2 mt-1.5 px-1 opacity-0 group-hover:opacity-100 transition-opacity text-[10px]",
                  message.role === 'user' ? "justify-end text-gray-400" : "justify-start text-gray-400"
                )}>
                  <span>{message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  {message.role === 'assistant' && message.metadata && (
                    <>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        {message.metadata.agentsUsed?.length ? 'Multi-Agent' : 'AI'}
                      </span>
                    </>
                  )}
                </div>

                {/* Actions (Assistant Only) */}
                {message.metadata && message.role === 'assistant' && (
                  <div className="mt-2 text-xs space-y-2">
                    {message.metadata.requiresConfirmation && (
                      <div className="flex animate-in fade-in slide-in-from-top-2">
                        <Button
                          size="sm"
                          className="bg-white dark:bg-zinc-800 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800 hover:bg-blue-50 dark:hover:bg-blue-900/30 shadow-sm transition-all font-medium rounded-lg"
                        >
                          Confirm Action
                        </Button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Thinking Indicator */}
          {isLoading && (
            <div className="flex gap-4 animate-in fade-in duration-300">
              <Avatar className="w-9 h-9 mt-1 border border-blue-100 bg-blue-50">
                <AvatarFallback className="bg-transparent text-blue-600"><Bot className="w-5 h-5" /></AvatarFallback>
              </Avatar>
              <div className="bg-white dark:bg-zinc-900 border border-gray-100 dark:border-gray-800 rounded-2xl rounded-tl-none px-6 py-4 shadow-sm flex items-center gap-3">
                <div className="flex gap-1.5">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                </div>
                <span className="text-xs text-muted-foreground font-medium">Analyzing...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="p-4 bg-white dark:bg-zinc-950 border-t border-gray-100 dark:border-gray-800 shrink-0">
        <div className="relative rounded-2xl border border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-zinc-900/50 focus-within:ring-2 focus-within:ring-blue-500/20 focus-within:border-blue-500 focus-within:bg-white dark:focus-within:bg-zinc-900 transition-all duration-200 shadow-sm">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Describe your task or ask a question..."
            className="min-h-[70px] max-h-[180px] w-full resize-none border-0 bg-transparent py-4 pl-5 pr-28 placeholder:text-muted-foreground text-foreground focus-visible:ring-0 font-medium"
          />

          <div className="absolute bottom-2.5 right-2.5 flex items-center gap-1.5">
            <Button
              variant="ghost"
              size="icon"
              className="h-9 w-9 text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-colors"
              onClick={() => toast.info('Attachments coming soon!')}
            >
              <Paperclip className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-9 w-9 text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-colors"
              onClick={() => toast.info('Voice input coming soon!')}
            >
              <Mic className="h-4 w-4" />
            </Button>
            <div className="w-px h-5 bg-gray-200 dark:bg-gray-700 mx-1" />
            <Button
              onClick={handleSend}
              disabled={!input.trim() || isLoading || !isInitialized}
              size="icon"
              className="h-9 w-9 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:shadow-[0_0_15px_rgba(37,99,235,0.4)] disabled:opacity-50 transition-all duration-300"
            >
              <Send className="w-4 h-4 ml-0.5" />
            </Button>
          </div>
        </div>

        <div className="flex items-center justify-between mt-3 px-2">
          <div className="flex gap-2">
            {/* Quick Actions / Suggestions */}
            {['Summarize Visits', 'Check Alerts'].map(s => (
              <button
                key={s}
                className="text-[10px] sm:text-xs font-medium bg-gray-100 dark:bg-zinc-900 text-gray-600 dark:text-gray-400 px-2.5 py-1 rounded-full border border-gray-200 dark:border-gray-800 hover:border-blue-300 dark:hover:border-blue-700 hover:text-blue-600 dark:hover:text-blue-400 transition-all"
                onClick={() => setInput(s)}
              >
                {s}
              </button>
            ))}
          </div>
          <p className="text-[10px] text-muted-foreground hidden sm:block">
            Powering clinical workflows securely
          </p>
        </div>
      </div>
    </Card>
  );
}
