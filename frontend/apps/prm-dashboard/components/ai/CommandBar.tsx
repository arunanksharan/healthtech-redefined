'use client';

import { useState, useEffect, useCallback } from 'react';
import { Search, Command, ArrowRight, Clock, Sparkles } from 'lucide-react';
import { processUserInput } from '@/lib/ai';
import toast from 'react-hot-toast';

/**
 * Command Bar Props
 */
interface CommandBarProps {
  userId: string;
  orgId: string;
  sessionId: string;
  permissions?: string[];
  onCommandExecuted?: (result: any) => void;
}

/**
 * Recent command type
 */
interface RecentCommand {
  command: string;
  timestamp: Date;
}

/**
 * CommandBar Component
 * Cmd+K style quick command interface
 */
export function CommandBar({
  userId,
  orgId,
  sessionId,
  permissions = [],
  onCommandExecuted,
}: CommandBarProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [recentCommands, setRecentCommands] = useState<RecentCommand[]>([]);
  const [suggestions] = useState([
    'Show available slots for tomorrow',
    'Search for patient with phone',
    'Book appointment for',
    'Cancel appointment',
    'Get patient 360 view',
    'Show today\'s appointments',
    'Create new patient',
    'Update patient information',
  ]);

  /**
   * Handle keyboard shortcut (Cmd+K or Ctrl+K)
   */
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen((prev) => !prev);
      }

      // ESC to close
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
        setInput('');
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  /**
   * Load recent commands from localStorage
   */
  useEffect(() => {
    const stored = localStorage.getItem('recent_commands');
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        setRecentCommands(
          parsed.map((c: any) => ({
            ...c,
            timestamp: new Date(c.timestamp),
          }))
        );
      } catch (error) {
        console.error('Failed to parse recent commands:', error);
      }
    }
  }, []);

  /**
   * Save recent command
   */
  const saveRecentCommand = useCallback((command: string) => {
    setRecentCommands((prev) => {
      const updated = [
        { command, timestamp: new Date() },
        ...prev.filter((c) => c.command !== command).slice(0, 4),
      ];

      localStorage.setItem('recent_commands', JSON.stringify(updated));
      return updated;
    });
  }, []);

  /**
   * Execute command
   */
  const executeCommand = async (command: string) => {
    if (!command.trim() || isLoading) return;

    setIsLoading(true);

    try {
      const result = await processUserInput(
        command,
        userId,
        orgId,
        sessionId,
        permissions
      );

      // Save to recent
      saveRecentCommand(command);

      // Show result
      if (result.success) {
        toast.success(result.message);
      } else {
        toast.error(result.error?.message || 'Command failed');
      }

      // Notify parent
      if (onCommandExecuted) {
        onCommandExecuted(result);
      }

      // Close command bar
      setIsOpen(false);
      setInput('');
    } catch (error: any) {
      console.error('Command execution error:', error);
      toast.error('Failed to execute command');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle Enter key
   */
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      executeCommand(input);
    }
  };

  /**
   * Filter suggestions based on input
   */
  const filteredSuggestions = suggestions.filter((s) =>
    s.toLowerCase().includes(input.toLowerCase())
  );

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 animate-in fade-in duration-200"
        onClick={() => setIsOpen(false)}
      />

      {/* Command Bar */}
      <div className="fixed top-[20%] left-1/2 -translate-x-1/2 w-full max-w-2xl z-50 animate-in slide-in-from-top-4 duration-200">
        <div className="bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
          {/* Input */}
          <div className="flex items-center gap-3 px-4 py-4 border-b">
            <Search className="w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type a command... (e.g., 'Show available slots for tomorrow')"
              className="flex-1 outline-none text-gray-900 placeholder-gray-400"
              autoFocus
              disabled={isLoading}
            />
            {isLoading && (
              <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
            )}
          </div>

          {/* Suggestions / Recent Commands */}
          <div className="max-h-96 overflow-y-auto">
            {input.trim() === '' ? (
              <>
                {/* Recent Commands */}
                {recentCommands.length > 0 && (
                  <div className="p-3">
                    <div className="flex items-center gap-2 px-3 py-2 text-xs font-medium text-gray-500 uppercase">
                      <Clock className="w-4 h-4" />
                      Recent
                    </div>
                    {recentCommands.map((cmd, index) => (
                      <button
                        key={index}
                        onClick={() => executeCommand(cmd.command)}
                        className="w-full flex items-center justify-between px-3 py-2 text-left hover:bg-gray-50 rounded-lg transition-colors group"
                      >
                        <span className="text-sm text-gray-700">
                          {cmd.command}
                        </span>
                        <ArrowRight className="w-4 h-4 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </button>
                    ))}
                  </div>
                )}

                {/* Quick Suggestions */}
                <div className="p-3 border-t">
                  <div className="flex items-center gap-2 px-3 py-2 text-xs font-medium text-gray-500 uppercase">
                    <Sparkles className="w-4 h-4" />
                    Quick Actions
                  </div>
                  {suggestions.slice(0, 5).map((suggestion, index) => (
                    <button
                      key={index}
                      onClick={() => setInput(suggestion)}
                      className="w-full flex items-center justify-between px-3 py-2 text-left hover:bg-gray-50 rounded-lg transition-colors group"
                    >
                      <span className="text-sm text-gray-700">
                        {suggestion}
                      </span>
                      <ArrowRight className="w-4 h-4 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </button>
                  ))}
                </div>
              </>
            ) : (
              <>
                {/* Filtered Suggestions */}
                {filteredSuggestions.length > 0 ? (
                  <div className="p-3">
                    <div className="px-3 py-2 text-xs font-medium text-gray-500 uppercase">
                      Suggestions
                    </div>
                    {filteredSuggestions.map((suggestion, index) => (
                      <button
                        key={index}
                        onClick={() => executeCommand(suggestion)}
                        className="w-full flex items-center justify-between px-3 py-2 text-left hover:bg-gray-50 rounded-lg transition-colors group"
                      >
                        <span className="text-sm text-gray-700">
                          {suggestion}
                        </span>
                        <ArrowRight className="w-4 h-4 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="p-8 text-center text-gray-500">
                    <p className="text-sm">
                      Press Enter to execute your command
                    </p>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between px-4 py-3 bg-gray-50 border-t text-xs text-gray-500">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <kbd className="px-2 py-1 bg-white border border-gray-300 rounded text-xs font-mono">
                  ↵
                </kbd>
                Execute
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-2 py-1 bg-white border border-gray-300 rounded text-xs font-mono">
                  ESC
                </kbd>
                Close
              </span>
            </div>
            <div className="flex items-center gap-1">
              <Command className="w-3 h-3" />
              <span>AI-powered commands</span>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

/**
 * Hook to open command bar programmatically
 */
export function useCommandBar() {
  const open = useCallback(() => {
    // Dispatch custom event to open command bar
    window.dispatchEvent(new CustomEvent('open-command-bar'));
  }, []);

  return { open };
}
