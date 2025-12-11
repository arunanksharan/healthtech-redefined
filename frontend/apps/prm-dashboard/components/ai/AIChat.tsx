'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Mic, Loader2, Sparkles } from 'lucide-react';
import { initializeAISystem, processUserInput } from '@/lib/ai';
import toast from 'react-hot-toast';

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
        "Hi! I'm your AI assistant. I can help you with appointments, patients, and more. What would you like to do?",
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
          toast.success('Action completed successfully');
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
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="flex items-center gap-3 px-6 py-4 border-b">
        <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div>
          <h2 className="font-semibold text-gray-900">AI Assistant</h2>
          <p className="text-sm text-gray-500">
            {isInitialized ? 'Ready to help' : 'Initializing...'}
          </p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-3 ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>

              {/* Metadata */}
              {message.metadata && message.role === 'assistant' && (
                <div className="mt-2 pt-2 border-t border-gray-200 text-xs text-gray-500 space-y-1">
                  {message.metadata.agentsUsed && (
                    <div>
                      Agents: {message.metadata.agentsUsed.join(', ')}
                    </div>
                  )}
                  {message.metadata.executionTime && (
                    <div>
                      Execution: {message.metadata.executionTime}ms
                    </div>
                  )}
                  {message.metadata.requiresConfirmation && (
                    <div className="mt-2">
                      <button className="px-3 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700">
                        Confirm Action
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Timestamp */}
              <p className="text-xs opacity-70 mt-2">
                {message.timestamp.toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-3">
              <div className="flex items-center gap-2 text-gray-600">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-sm">Thinking...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="px-6 py-4 border-t">
        <div className="flex items-end gap-3">
          <div className="flex-1">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything... (e.g., 'Show available slots for tomorrow')"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={1}
              disabled={!isInitialized || isLoading}
            />
          </div>

          <button
            onClick={() => toast('Voice input coming soon!', { icon: 'ℹ️' })}
            className="p-3 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            title="Voice input (coming soon)"
          >
            <Mic className="w-5 h-5" />
          </button>

          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading || !isInitialized}
            className="p-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Send message"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>

        {/* Suggestions */}
        <div className="mt-3 flex flex-wrap gap-2">
          {[
            'Show available slots for tomorrow',
            'Search for patient John Doe',
            'Book an appointment',
          ].map((suggestion) => (
            <button
              key={suggestion}
              onClick={() => setInput(suggestion)}
              className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
              disabled={isLoading}
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
