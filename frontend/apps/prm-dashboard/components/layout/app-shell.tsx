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
  onContextPanelClose,
  onCommandBarOpen,
}: AppShellProps) {
  const { collapsed, setCollapsed, mobileOpen, setMobileOpen } = useSidebarState();

  const handleMenuClick = useCallback(() => {
    setMobileOpen((prev) => !prev);
  }, [setMobileOpen]);

  const handleCloseMobileMenu = useCallback(() => {
    setMobileOpen(false);
  }, [setMobileOpen]);

  return (
    <div className={cn("min-h-screen bg-background", className)}>
      {/* Desktop Sidebar */}
      <div className="hidden lg:block fixed inset-y-0 left-0 z-40">
        <Sidebar onCollapsedChange={setCollapsed} />
      </div>

      {/* Mobile Sidebar Overlay */}
      {mobileOpen && (
        <>
          <div
            className="fixed inset-0 bg-black/50 z-40 lg:hidden"
            onClick={handleCloseMobileMenu}
          />
          <div className="fixed inset-y-0 left-0 z-50 lg:hidden">
            <Sidebar onCollapsedChange={setCollapsed} />
          </div>
        </>
      )}

      {/* Main Content Area */}
      <div
        className={cn(
          "flex flex-col min-h-screen transition-all duration-200",
          "lg:pl-sidebar",
          collapsed && "lg:pl-sidebar-collapsed"
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
            contextPanelOpen && "lg:pr-context-panel" // Account for context panel
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
