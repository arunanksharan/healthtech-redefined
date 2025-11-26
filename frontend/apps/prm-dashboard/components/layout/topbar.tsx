"use client";

import * as React from "react";
import { useState, useCallback, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Search,
  Bell,
  HelpCircle,
  Settings,
  Menu,
  ChevronRight,
  Command,
  User,
  LogOut,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface Breadcrumb {
  label: string;
  href?: string;
}

interface TopBarProps {
  className?: string;
  onMenuClick?: () => void;
  onSearchClick?: () => void;
  showMenuButton?: boolean;
}

// Mock notification count - would come from API
const useNotifications = () => {
  return {
    unreadCount: 4,
  };
};

// Generate breadcrumbs from pathname
const useBreadcrumbs = (): Breadcrumb[] => {
  const pathname = usePathname();

  return React.useMemo(() => {
    if (pathname === "/" || pathname === "/dashboard") {
      return [{ label: "Dashboard" }];
    }

    const segments = pathname.split("/").filter(Boolean);
    const breadcrumbs: Breadcrumb[] = [];

    // Map segment names to display labels
    const labelMap: Record<string, string> = {
      patients: "Patients",
      practitioners: "Practitioners",
      organizations: "Organizations",
      locations: "Locations",
      schedules: "Schedules",
      slots: "Slots",
      appointments: "Appointments",
      encounters: "Encounters",
      observations: "Observations",
      conditions: "Conditions",
      medications: "Medications",
      "diagnostic-reports": "Diagnostic Reports",
      analytics: "Analytics",
      collaboration: "Collaboration",
      telehealth: "Telehealth",
      billing: "Billing",
      settings: "Settings",
      inbox: "Inbox",
      schedule: "Schedule",
    };

    let currentPath = "";
    segments.forEach((segment, index) => {
      currentPath += `/${segment}`;
      const isLast = index === segments.length - 1;

      // Check if this is a dynamic segment (ID)
      const isId = /^[a-f0-9-]{20,}$/i.test(segment) || /^\d+$/.test(segment);

      if (isId) {
        breadcrumbs.push({
          label: "Details",
          href: isLast ? undefined : currentPath,
        });
      } else {
        breadcrumbs.push({
          label: labelMap[segment] || segment.charAt(0).toUpperCase() + segment.slice(1),
          href: isLast ? undefined : currentPath,
        });
      }
    });

    return breadcrumbs;
  }, [pathname]);
};

export function TopBar({
  className,
  onMenuClick,
  onSearchClick,
  showMenuButton = false,
}: TopBarProps) {
  const breadcrumbs = useBreadcrumbs();
  const { unreadCount } = useNotifications();
  const [isMac, setIsMac] = useState(false);

  // Detect OS for keyboard shortcut display
  useEffect(() => {
    setIsMac(navigator.platform.toUpperCase().indexOf("MAC") >= 0);
  }, []);

  // Global keyboard shortcut for search
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        onSearchClick?.();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onSearchClick]);

  return (
    <header
      className={cn(
        "h-topbar bg-card border-b border-border flex items-center justify-between px-4 lg:px-6",
        className
      )}
    >
      {/* Left Section - Menu button and Breadcrumbs */}
      <div className="flex items-center gap-4">
        {/* Mobile Menu Button */}
        {showMenuButton && (
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 rounded-md hover:bg-accent transition-colors"
            aria-label="Open menu"
          >
            <Menu className="w-5 h-5 text-muted-foreground" />
          </button>
        )}

        {/* Breadcrumbs */}
        <nav aria-label="Breadcrumb" className="flex items-center">
          <ol className="flex items-center gap-1.5">
            {breadcrumbs.map((crumb, index) => (
              <li key={index} className="flex items-center">
                {index > 0 && (
                  <ChevronRight className="w-4 h-4 text-muted-foreground mx-1.5" />
                )}
                {crumb.href ? (
                  <Link
                    href={crumb.href}
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {crumb.label}
                  </Link>
                ) : (
                  <span className="text-sm font-medium text-foreground">
                    {crumb.label}
                  </span>
                )}
              </li>
            ))}
          </ol>
        </nav>
      </div>

      {/* Center Section - Global Search */}
      <div className="hidden md:flex flex-1 max-w-md mx-8">
        <button
          onClick={onSearchClick}
          className="flex items-center gap-3 w-full px-3 py-2 bg-muted/50 hover:bg-muted border border-border rounded-lg text-sm text-muted-foreground transition-colors"
        >
          <Search className="w-4 h-4" />
          <span className="flex-1 text-left">Search or ask AI...</span>
          <kbd className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 bg-background border border-border rounded text-xs font-mono">
            {isMac ? (
              <>
                <Command className="w-3 h-3" />K
              </>
            ) : (
              "Ctrl+K"
            )}
          </kbd>
        </button>
      </div>

      {/* Right Section - Actions */}
      <div className="flex items-center gap-2">
        {/* Mobile Search Button */}
        <button
          onClick={onSearchClick}
          className="md:hidden p-2 rounded-md hover:bg-accent transition-colors"
          aria-label="Search"
        >
          <Search className="w-5 h-5 text-muted-foreground" />
        </button>

        {/* Notifications */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              className="relative p-2 rounded-md hover:bg-accent transition-colors"
              aria-label="Notifications"
            >
              <Bell className="w-5 h-5 text-muted-foreground" />
              {unreadCount > 0 && (
                <span className="absolute top-1 right-1 w-4 h-4 bg-destructive text-destructive-foreground text-xs rounded-full flex items-center justify-center font-medium">
                  {unreadCount > 9 ? "9+" : unreadCount}
                </span>
              )}
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-80">
            <DropdownMenuLabel className="flex items-center justify-between">
              <span>Notifications</span>
              <Badge variant="secondary">{unreadCount} new</Badge>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <div className="max-h-80 overflow-y-auto">
              {/* Example notifications */}
              <DropdownMenuItem className="flex flex-col items-start gap-1 py-3 cursor-pointer">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 bg-primary rounded-full" />
                  <span className="font-medium text-sm">New appointment booked</span>
                </div>
                <span className="text-xs text-muted-foreground ml-4">
                  Patient John Doe scheduled for tomorrow at 10:00 AM
                </span>
                <span className="text-xs text-muted-foreground ml-4">5 min ago</span>
              </DropdownMenuItem>
              <DropdownMenuItem className="flex flex-col items-start gap-1 py-3 cursor-pointer">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 bg-warning rounded-full" />
                  <span className="font-medium text-sm">Lab results available</span>
                </div>
                <span className="text-xs text-muted-foreground ml-4">
                  Complete blood count results for Jane Smith
                </span>
                <span className="text-xs text-muted-foreground ml-4">1 hour ago</span>
              </DropdownMenuItem>
            </div>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-center justify-center text-primary cursor-pointer">
              View all notifications
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Help */}
        <button
          className="hidden sm:block p-2 rounded-md hover:bg-accent transition-colors"
          aria-label="Help"
        >
          <HelpCircle className="w-5 h-5 text-muted-foreground" />
        </button>

        {/* Settings */}
        <Link
          href="/settings"
          className="hidden sm:block p-2 rounded-md hover:bg-accent transition-colors"
          aria-label="Settings"
        >
          <Settings className="w-5 h-5 text-muted-foreground" />
        </Link>

        {/* User Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              className="flex items-center gap-2 p-1.5 rounded-md hover:bg-accent transition-colors"
              aria-label="User menu"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center text-primary-foreground text-sm font-semibold">
                RS
              </div>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>
              <div className="flex flex-col">
                <span>Dr. Rohit Sharma</span>
                <span className="text-xs font-normal text-muted-foreground">
                  rohit.sharma@suryahospitals.com
                </span>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link href="/profile" className="flex items-center gap-2 cursor-pointer">
                <User className="w-4 h-4" />
                <span>Profile</span>
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link href="/settings" className="flex items-center gap-2 cursor-pointer">
                <Settings className="w-4 h-4" />
                <span>Settings</span>
              </Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="flex items-center gap-2 text-destructive cursor-pointer">
              <LogOut className="w-4 h-4" />
              <span>Sign out</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}

export default TopBar;
