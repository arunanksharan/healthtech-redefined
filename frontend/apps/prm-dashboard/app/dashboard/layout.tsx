"use client";

import { useState, useCallback, useEffect } from "react";
import { AppShell } from "@/components/layout";
import { AIChat } from "@/components/ai";
import { CommandBar } from "@/components/copilot";
import { useCopilotStore } from "@/lib/store/copilot-store";
import { WebSocketProvider } from "@/components/providers/websocket-provider";


export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [aiPanelOpen, setAiPanelOpen] = useState(false);

  // Load state from local storage on mount
  useEffect(() => {
    const savedState = localStorage.getItem('prm_ai_panel_open');
    if (savedState !== null) {
      setAiPanelOpen(savedState === 'true');
    }
  }, []);

  const handleAiPanelToggle = useCallback((open: boolean) => {
    setAiPanelOpen(open);
    localStorage.setItem('prm_ai_panel_open', String(open));
  }, []);

  // Demo user context - replace with actual auth context
  const userId = "user_123";
  const orgId = "org_456";
  const sessionId = `session_${Date.now()}`;
  const permissions = ["appointments.read", "appointments.write", "patients.read", "patients.write"];

  // Copilot store
  const { isOpen: commandBarOpen, openCommandBar, closeCommandBar, setContext } = useCopilotStore();

  // Set initial context
  useEffect(() => {
    setContext({ currentPage: window.location.pathname });
  }, [setContext]);

  // Global keyboard shortcut for Cmd+K / Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        if (commandBarOpen) {
          closeCommandBar();
        } else {
          openCommandBar();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [commandBarOpen, openCommandBar, closeCommandBar]);

  const handleCommandBarOpen = useCallback(() => {
    openCommandBar();
  }, [openCommandBar]);

  return (
    <>
      <WebSocketProvider>
        <AppShell
          onCommandBarOpen={handleCommandBarOpen}
          contextPanelOpen={aiPanelOpen}
          contextPanelOverlay={true}
          contextPanelWidth="2xl"
          contextPanelTitle="AI Assistant"
          contextPanelSubtitle="Ask me anything"
          onContextPanelClose={() => setAiPanelOpen(false)}
          contextPanelContent={
            <AIChat
              userId={userId}
              orgId={orgId}
              sessionId={sessionId}
              permissions={permissions}
            />
          }
        >
          {children}
        </AppShell>
      </WebSocketProvider>

      {/* Floating AI Trigger Button */}
      {!aiPanelOpen && (
        <button
          onClick={() => handleAiPanelToggle(true)}
          className="fixed bottom-6 right-6 z-50 h-14 w-14 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full shadow-lg hover:shadow-xl hover:scale-105 transition-all flex items-center justify-center group"
          title="Open AI Assistant"
        >
          <div className="absolute inset-0 rounded-full bg-white/20 animate-pulse" />
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="text-white relative z-10"
          >
            <path d="M12 8V4H8" />
            <rect width="16" height="12" x="4" y="8" rx="2" />
            <path d="M2 14h2" />
            <path d="M20 14h2" />
            <path d="M15 13v2" />
            <path d="M9 13v2" />
          </svg>
        </button>
      )}

      {/* AI Copilot Command Bar (Cmd+K) */}
      <CommandBar />
    </>
  );
}
