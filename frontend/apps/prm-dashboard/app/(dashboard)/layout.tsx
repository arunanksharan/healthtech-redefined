"use client";

import { useState, useCallback, useEffect } from "react";
import { AppShell } from "@/components/layout";
import { AIChat } from "@/components/ai";
import { CommandBar } from "@/components/copilot";
import { useCopilotStore } from "@/lib/store/copilot-store";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [aiPanelOpen, setAiPanelOpen] = useState(true);

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
      <AppShell
        onCommandBarOpen={handleCommandBarOpen}
        contextPanelOpen={aiPanelOpen}
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

      {/* AI Copilot Command Bar (Cmd+K) */}
      <CommandBar />
    </>
  );
}
