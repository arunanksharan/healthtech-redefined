"use client";

import * as React from "react";
import { useState, useCallback, useEffect } from "react";
import { cn } from "@/lib/utils/cn";
import { Sidebar } from "./sidebar";
import { TopBar } from "./topbar";
import { MobileNav } from "./mobile-nav";
import { ContextPanel } from "./context-panel";

interface AppShellProps {
  children: React.ReactNode;
  className?: string;
  // Context panel props
  contextPanelOpen?: boolean;
  contextPanelContent?: React.ReactNode;
  contextPanelTitle?: string;
  contextPanelSubtitle?: string;
  contextPanelWidth?: "sm" | "md" | "lg" | "xl" | "2xl" | "3xl";
  contextPanelOverlay?: boolean;
  onContextPanelClose?: () => void;
  // Command bar
  onCommandBarOpen?: () => void;
}

// Custom hook for responsive sidebar
const useSidebarState = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  // Close mobile sidebar when resizing to desktop
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 1024) {
        setMobileOpen(false);
      }
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return {
    collapsed,
    setCollapsed,
    mobileOpen,
    setMobileOpen,
  };
};

export function AppShell({
  children,
  className,
  contextPanelOpen = false,
  contextPanelContent,
  contextPanelTitle,
  contextPanelSubtitle,
  contextPanelWidth = "lg",
  contextPanelOverlay = false,
  onContextPanelClose,
  onCommandBarOpen,
}: AppShellProps) {
  const { collapsed, setCollapsed, mobileOpen, setMobileOpen } = useSidebarState();
  const [isDesktop, setIsDesktop] = useState(false);

  // Track if we're on desktop
  useEffect(() => {
    const checkDesktop = () => setIsDesktop(window.innerWidth >= 1024);
    checkDesktop();
    window.addEventListener("resize", checkDesktop);
    return () => window.removeEventListener("resize", checkDesktop);
  }, []);

  const handleMenuClick = useCallback(() => {
    if (isDesktop) {
      // On desktop, toggle collapsed state
      setCollapsed((prev) => !prev);
    } else {
      // On mobile, toggle overlay sidebar
      setMobileOpen((prev) => !prev);
    }
  }, [isDesktop, setCollapsed, setMobileOpen]);

  const handleCloseMobileMenu = useCallback(() => {
    setMobileOpen(false);
  }, [setMobileOpen]);

  return (
    <div className={cn("min-h-screen bg-background", className)}>
      {/* Desktop Sidebar - Always visible on lg+ */}
      <div className="hidden lg:block fixed inset-y-0 left-0 z-40">
        <Sidebar forceCollapsed={collapsed} onCollapsedChange={setCollapsed} />
      </div>

      {/* Mobile/Tablet Sidebar - Collapsed by default, expanded when mobileOpen */}
      <div className="lg:hidden fixed inset-y-0 left-0 z-40">
        <Sidebar
          onCollapsedChange={setCollapsed}
          forceCollapsed={!mobileOpen}
        />
      </div>

      {/* Mobile Overlay - Only shown when sidebar is expanded */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={handleCloseMobileMenu}
        />
      )}

      {/* Main Content Area */}
      <div
        className={cn(
          "flex flex-col min-h-screen transition-all duration-200",
          // Desktop: adjust for sidebar state
          "lg:pl-sidebar",
          collapsed && "lg:pl-sidebar-collapsed",
          // Mobile: always account for collapsed sidebar width
          "pl-sidebar-collapsed lg:pl-sidebar"
        )}
      >
        {/* Top Bar */}
        <TopBar
          showMenuButton={true}
          onMenuClick={handleMenuClick}
          onSearchClick={onCommandBarOpen}
        />

        {/* Page Content */}
        <main
          className={cn(
            "flex-1 p-4 lg:p-6",
            "pb-20 md:pb-6", // Extra padding for mobile nav
            (contextPanelOpen && !contextPanelOverlay) && "lg:pr-context-panel" // Account for context panel if not overlay
          )}
        >
          {children}
        </main>
      </div>

      {/* Context Panel (Desktop only) */}
      {contextPanelOpen && contextPanelContent && onContextPanelClose && (
        <div className="hidden lg:block">
          <ContextPanel
            title={contextPanelTitle}
            subtitle={contextPanelSubtitle}
            width={contextPanelWidth}
            className={contextPanelOverlay ? "shadow-2xl border-l border-border/50" : ""}
            onClose={onContextPanelClose}
          >
            {contextPanelContent}
          </ContextPanel>
        </div>
      )}

      {/* Mobile Navigation */}
      <MobileNav onMoreClick={handleMenuClick} />
    </div>
  );
}

export default AppShell;
