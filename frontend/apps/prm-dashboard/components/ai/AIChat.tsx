'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Mic, Sparkles, Bot, User, Paperclip } from 'lucide-react';
import { initializeAISystem, processUserInput, executeConfirmedPlan } from '@/lib/ai';
import { useToast } from '@/hooks/use-toast';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { cn } from '@/lib/utils/cn';

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

interface AIChatProps {
  userId: string;
  orgId: string;
  sessionId: string;
  permissions?: string[];
  onConfirmationRequired?: (plan: any) => void;
}

export function AIChat({
  userId,
  orgId,
  sessionId,
  permissions = [],
  onConfirmationRequired,
}: AIChatProps) {
  const { toast } = useToast();
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

  useEffect(() => {
    try {
      initializeAISystem(process.env.NEXT_PUBLIC_OPENAI_API_KEY);
      setIsInitialized(true);
    } catch (error) {
      console.error('Failed to initialize AI system:', error);
      toast({ title: 'Error', description: 'Failed to initialize AI assistant', variant: 'destructive' });
    }
  }, [toast]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

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
      const result = await processUserInput(
        input,
        userId,
        orgId,
        sessionId,
        permissions
      );

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

        if (onConfirmationRequired) {
          onConfirmationRequired(result.results[0].data.plan);
        }
      } else if (result.metadata?.requiresClarification) {
        // Handle clarification requests - show the questions
        const clarifications = result.metadata.clarifications as string[] || [];
        const clarificationText = clarifications.length > 0
          ? `${result.message}\n\n${clarifications.map((q, i) => `${i + 1}. ${q}`).join('\n')}`
          : result.message;

        const clarificationMessage: Message = {
          id: `msg_${Date.now()}_clarify`,
          role: 'assistant',
          content: clarificationText,
          timestamp: new Date(),
          metadata: {
            agentsUsed: result.agentsUsed,
          },
        };

        setMessages((prev) => [...prev, clarificationMessage]);
      } else {
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

        if (!result.success) {
          toast({ title: 'Error', description: 'Action failed: ' + result.error?.message, variant: 'destructive' });
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
      toast({ title: 'Error', description: 'Failed to process your request', variant: 'destructive' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900 rounded-lg overflow-hidden border-2 border-gray-100 dark:border-gray-800">
      {/* Header - Flat solid blue */}
      <div className="flex items-center gap-4 px-6 py-5 bg-blue-500 text-white shrink-0">
        <div className="w-12 h-12 bg-white rounded-lg flex items-center justify-center transition-all duration-200 hover:scale-105">
          <Sparkles className="w-6 h-6 text-blue-500" />
        </div>
        <div>
          <h2 className="font-heading text-lg text-white leading-tight">Clinical Assistant</h2>
          <div className="flex items-center gap-2 mt-0.5">
            <span className={cn("w-2 h-2 rounded-full", isInitialized ? "bg-emerald-400" : "bg-gray-300")} />
            <p className="text-xs text-blue-100 font-medium">
              {isInitialized ? 'Online & Ready' : 'Initializing...'}
            </p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 bg-gray-50 dark:bg-gray-800/50">
        <div className="px-6 py-6 space-y-6 min-h-full">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-4 ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'} group`}
            >
              {/* Avatar */}
              <Avatar className={cn(
                "w-9 h-9 mt-1 rounded-lg",
                message.role === 'assistant'
                  ? "bg-blue-100 dark:bg-blue-900/30"
                  : "bg-gray-100 dark:bg-gray-700"
              )}>
                {message.role === 'assistant' ? (
                  <AvatarFallback className="bg-blue-500 text-white rounded-lg"><Bot className="w-5 h-5" /></AvatarFallback>
                ) : (
                  <AvatarFallback className="bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-300 rounded-lg"><User className="w-5 h-5" /></AvatarFallback>
                )}
              </Avatar>

              {/* Message Bubble - Flat, no shadows */}
              <div className="flex flex-col max-w-[80%]">
                <div className={cn(
                  "rounded-lg px-5 py-3.5 text-sm leading-relaxed transition-all duration-200",
                  message.role === 'user'
                    ? 'bg-blue-500 text-white'
                    : 'bg-white dark:bg-gray-800 border-2 border-gray-100 dark:border-gray-700 text-gray-800 dark:text-gray-200'
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
                      <div className="flex gap-2">
                        <button
                          className="flat-btn-primary text-sm py-2 px-4"
                          onClick={async () => {
                            // Mark this message as confirmed (remove the button)
                            setMessages(prev => prev.map(m =>
                              m.id === message.id
                                ? { ...m, metadata: { ...m.metadata, requiresConfirmation: false } }
                                : m
                            ));

                            // Add processing message
                            const processingMsg: Message = {
                              id: `msg_${Date.now()}_processing`,
                              role: 'assistant',
                              content: '⏳ Processing your request...',
                              timestamp: new Date(),
                            };
                            setMessages(prev => [...prev, processingMsg]);

                            try {
                              // Get the plan and agent from the message metadata
                              const plan = message.metadata?.plan;
                              const agentName = message.metadata?.agentsUsed?.[0] || 'AppointmentAgent';

                              if (!plan) {
                                throw new Error('No plan found to execute');
                              }

                              // Execute the confirmed plan
                              const result = await executeConfirmedPlan(
                                plan,
                                agentName,
                                userId,
                                orgId,
                                sessionId,
                                permissions
                              );

                              // Add result message
                              const resultMsg: Message = {
                                id: `msg_${Date.now()}_result`,
                                role: 'assistant',
                                content: result.success
                                  ? `✅ ${result.message}`
                                  : `❌ ${result.message || 'Action failed'}`,
                                timestamp: new Date(),
                              };
                              setMessages(prev => [...prev.filter(m => m.id !== processingMsg.id), resultMsg]);

                              if (result.success) {
                                toast({ title: 'Success', description: 'Your action has been completed!' });
                              } else {
                                toast({ title: 'Error', description: result.message, variant: 'destructive' });
                              }
                            } catch (error: any) {
                              const errorMsg: Message = {
                                id: `msg_${Date.now()}_error`,
                                role: 'assistant',
                                content: `❌ Error: ${error.message}`,
                                timestamp: new Date(),
                              };
                              setMessages(prev => [...prev.filter(m => m.id !== processingMsg.id), errorMsg]);
                              toast({ title: 'Error', description: error.message, variant: 'destructive' });
                            }
                          }}
                        >
                          Confirm Action
                        </button>
                        <button
                          className="text-sm py-2 px-4 border-2 border-gray-200 dark:border-gray-700 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-200"
                          onClick={() => {
                            setMessages(prev => prev.map(m =>
                              m.id === message.id
                                ? { ...m, metadata: { ...m.metadata, requiresConfirmation: false } }
                                : m
                            ));
                            const cancelMsg: Message = {
                              id: `msg_${Date.now()}_cancelled`,
                              role: 'assistant',
                              content: '❌ Action cancelled. Let me know if you need anything else.',
                              timestamp: new Date(),
                            };
                            setMessages(prev => [...prev, cancelMsg]);
                          }}
                        >
                          Cancel
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Thinking Indicator */}
          {isLoading && (
            <div className="flex gap-4">
              <Avatar className="w-9 h-9 mt-1 rounded-lg bg-blue-100 dark:bg-blue-900/30">
                <AvatarFallback className="bg-blue-500 text-white rounded-lg"><Bot className="w-5 h-5" /></AvatarFallback>
              </Avatar>
              <div className="bg-white dark:bg-gray-800 border-2 border-gray-100 dark:border-gray-700 rounded-lg px-6 py-4 flex items-center gap-3">
                <div className="flex gap-1.5">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                </div>
                <span className="text-xs text-gray-500 font-medium">Analyzing...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input Area - Flat */}
      <div className="p-4 bg-white dark:bg-gray-900 border-t-2 border-gray-100 dark:border-gray-800 shrink-0">
        <div className="relative rounded-lg border-2 border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 focus-within:border-blue-500 focus-within:bg-white dark:focus-within:bg-gray-900 transition-all duration-200">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Describe your task or ask a question..."
            className="min-h-[70px] max-h-[180px] w-full resize-none border-0 bg-transparent py-4 pl-5 pr-28 placeholder:text-gray-400 text-gray-900 dark:text-white focus-visible:ring-0 font-medium"
          />

          <div className="absolute bottom-2.5 right-2.5 flex items-center gap-1.5">
            <Button
              variant="ghost"
              size="icon"
              className="h-9 w-9 text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-all duration-200 hover:scale-105"
              onClick={() => toast({ title: 'Coming Soon', description: 'Attachments coming soon!' })}
            >
              <Paperclip className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-9 w-9 text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-all duration-200 hover:scale-105"
              onClick={() => toast({ title: 'Coming Soon', description: 'Voice input coming soon!' })}
            >
              <Mic className="h-4 w-4" />
            </Button>
            <div className="w-0.5 h-5 bg-gray-200 dark:bg-gray-600 mx-1" />
            <Button
              onClick={handleSend}
              disabled={!input.trim() || isLoading || !isInitialized}
              size="icon"
              className="h-9 w-9 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 transition-all duration-200 hover:scale-105"
            >
              <Send className="w-4 h-4 ml-0.5" />
            </Button>
          </div>
        </div>

        <div className="flex items-center justify-between mt-3 px-2">
          <div className="flex gap-2">
            {['Summarize Visits', 'Check Alerts'].map(s => (
              <button
                key={s}
                className="text-[10px] sm:text-xs font-semibold bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 px-3 py-1.5 rounded-lg border-2 border-gray-200 dark:border-gray-700 hover:border-blue-500 hover:text-blue-500 transition-all duration-200 hover:scale-105"
                onClick={() => setInput(s)}
              >
                {s}
              </button>
            ))}
          </div>
          <p className="text-[10px] text-gray-400 hidden sm:block">
            Powering clinical workflows securely
          </p>
        </div>
      </div>
    </div>
  );
}
