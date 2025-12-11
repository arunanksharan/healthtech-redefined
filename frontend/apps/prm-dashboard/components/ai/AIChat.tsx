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
    <Card className="flex flex-col h-full bg-white border-none shadow-none rounded-none md:rounded-xl md:border md:shadow-sm overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-3 px-6 py-4 border-b border-gray-100 bg-white/80 backdrop-blur-md sticky top-0 z-10">
        <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center shadow-sm">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div>
          <h2 className="font-semibold text-gray-900 leading-tight">Clinical Assistant</h2>
          <div className="flex items-center gap-1.5">
            <span className={cn("w-2 h-2 rounded-full", isInitialized ? "bg-green-500 animate-pulse" : "bg-gray-300")} />
            <p className="text-xs text-gray-500 font-medium">
              {isInitialized ? 'Online & Ready' : 'Initializing...'}
            </p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 bg-gray-50/30">
        <div className="px-6 py-6 space-y-6">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-4 ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
            >
              {/* Avatar */}
              <Avatar className="w-8 h-8 mt-1 border border-gray-200">
                {message.role === 'assistant' ? (
                  <>
                    <AvatarImage src="/bot-avatar.png" />
                    <AvatarFallback className="bg-blue-50 text-blue-600"><Bot className="w-4 h-4" /></AvatarFallback>
                  </>
                ) : (
                  <>
                    <AvatarFallback className="bg-gray-100 text-gray-600"><User className="w-4 h-4" /></AvatarFallback>
                  </>
                )}
              </Avatar>

              {/* Message Bubble */}
              <div className={cn(
                "max-w-[85%] rounded-2xl px-5 py-3 shadow-sm text-sm leading-relaxed animate-in fade-in slide-in-from-bottom-2 duration-300",
                message.role === 'user'
                  ? 'bg-blue-600 text-white rounded-tr-none'
                  : 'bg-white border border-gray-100 text-gray-800 rounded-tl-none'
              )}>
                <p className="whitespace-pre-wrap">{message.content}</p>

                {/* Metadata & Actions */}
                {message.metadata && message.role === 'assistant' && (
                  <div className="mt-3 pt-2 border-t border-gray-100/50 text-xs opacity-75 space-y-1">
                    {message.metadata.agentsUsed && (
                      <div className="flex items-center gap-1">
                        <span className="font-medium">Agents:</span> {message.metadata.agentsUsed.join(', ')}
                      </div>
                    )}
                    {message.metadata.requiresConfirmation && (
                      <div className="mt-2">
                        <Button
                          size="sm"
                          className="bg-white text-blue-600 border border-blue-200 hover:bg-blue-50 hover:text-blue-700 shadow-sm transition-all"
                        >
                          Confirm Action
                        </Button>
                      </div>
                    )}
                  </div>
                )}

                {/* Timestamp */}
                <div className={cn(
                  "text-[10px] mt-1 opacity-60 text-right",
                  message.role === 'user' ? "text-blue-100" : "text-gray-400"
                )}>
                  {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          ))}

          {/* Thinking Indicator */}
          {isLoading && (
            <div className="flex gap-4 animate-in fade-in duration-300">
              <Avatar className="w-8 h-8 mt-1 border border-gray-200">
                <AvatarFallback className="bg-blue-50 text-blue-600"><Bot className="w-4 h-4" /></AvatarFallback>
              </Avatar>
              <div className="bg-white border border-gray-100 rounded-2xl rounded-tl-none px-5 py-4 shadow-sm flex items-center gap-2">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                </span>
                <span className="text-xs text-gray-500 font-medium">Processing request...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="p-4 bg-white border-t border-gray-100">
        <div className="relative rounded-xl border border-gray-200 bg-gray-50/50 focus-within:ring-2 focus-within:ring-blue-100 focus-within:border-blue-400 transition-all shadow-sm">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your instruction here..."
            className="min-h-[60px] max-h-[180px] w-full resize-none border-0 bg-transparent py-4 pl-4 pr-24 placeholder:text-gray-400 focus-visible:ring-0 text-gray-800"
          />

          <div className="absolute bottom-2 right-2 flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-gray-400 hover:text-gray-600 hover:bg-gray-200/50"
              onClick={() => toast.info('Attachments coming soon!')}
            >
              <Paperclip className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-gray-400 hover:text-gray-600 hover:bg-gray-200/50"
              onClick={() => toast.info('Voice input coming soon!')}
            >
              <Mic className="h-4 w-4" />
            </Button>
            <Button
              onClick={handleSend}
              disabled={!input.trim() || isLoading || !isInitialized}
              size="icon"
              className="h-8 w-8 bg-blue-600 text-white rounded-lg hover:bg-blue-700 shadow-sm disabled:opacity-50 transition-all ml-1"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
        </div>

        <div className="flex items-center justify-between mt-2.5 px-1">
          <p className="text-[10px] text-gray-400">
            AI can make mistakes. Please verify important clinical details.
          </p>
          {/* Suggestions as pills */}
          <div className="flex gap-2 hidden md:flex">
            {['Check Schedule', 'Find Patient'].map(s => (
              <button
                key={s}
                className="text-[10px] bg-gray-100 text-gray-600 px-2 py-0.5 rounded-md hover:bg-gray-200 transition-colors"
                onClick={() => setInput(s)}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      </div>
    </Card>
  );
}
