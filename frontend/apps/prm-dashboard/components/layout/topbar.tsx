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
  Sun,
  Moon,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/components/providers/theme-provider";
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
  const { setTheme, resolvedTheme } = useTheme();
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
        "h-topbar bg-background/80 backdrop-blur-md border-b border-border/50 flex items-center justify-between px-4 lg:px-6 sticky top-0 z-30 supports-[backdrop-filter]:bg-background/60",
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
                  <ChevronRight className="w-4 h-4 text-gray-400 mx-1.5" />
                )}
                {crumb.href ? (
                  <Link
                    href={crumb.href}
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors font-medium"
                  >
                    {crumb.label}
                  </Link>
                ) : (
                  <span className="text-sm font-semibold text-foreground bg-accent/50 px-2 py-0.5 rounded-md">
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
          className="flex items-center gap-3 w-full px-4 py-2 bg-muted/50 hover:bg-muted border border-transparent hover:border-border rounded-xl text-sm text-muted-foreground transition-all group focus:outline-none focus:ring-2 focus:ring-blue-100 focus:bg-background focus:border-blue-200 shadow-sm"
        >
          <Search className="w-4 h-4 text-muted-foreground/80 group-hover:text-foreground transition-colors" />
          <span className="flex-1 text-left">Search or ask AI...</span>
          <kbd className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 bg-background border border-border rounded-md text-[10px] font-bold text-muted-foreground font-mono shadow-sm">
            {isMac ? (
              <>
                <Command className="w-3 h-3" />K
              </>
            ) : (
              "Ctrl K"
            )}
          </kbd>
        </button>
      </div>

      {/* Right Section - Actions */}
      <div className="flex items-center gap-1">
        {/* Mobile Search Button */}
        <button
          onClick={onSearchClick}
          className="md:hidden p-2 rounded-full hover:bg-accent transition-colors text-muted-foreground"
          aria-label="Search"
        >
          <Search className="w-5 h-5" />
        </button>

        {/* Notifications */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              className="relative p-2.5 rounded-full hover:bg-accent transition-colors text-muted-foreground hover:text-foreground"
              aria-label="Notifications"
            >
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="absolute top-2 right-2 w-2.5 h-2.5 bg-red-500 border-2 border-background rounded-full"></span>
              )}
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-80">
            <DropdownMenuLabel className="flex items-center justify-between">
              <span>Notifications</span>
              <Badge variant="secondary" className="bg-blue-50 text-blue-700">{unreadCount} new</Badge>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <div className="max-h-80 overflow-y-auto">
              <DropdownMenuItem className="flex flex-col items-start gap-1 py-3 cursor-pointer">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 bg-blue-500 rounded-full" />
                  <span className="font-medium text-sm">New appointment booked</span>
                </div>
                <span className="text-xs text-muted-foreground ml-4">
                  Patient John Doe scheduled for tomorrow at 10:00 AM
                </span>
                <span className="text-xs text-muted-foreground ml-4">5 min ago</span>
              </DropdownMenuItem>
              <DropdownMenuItem className="flex flex-col items-start gap-1 py-3 cursor-pointer">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 bg-amber-500 rounded-full" />
                  <span className="font-medium text-sm">Lab results available</span>
                </div>
                <span className="text-xs text-muted-foreground ml-4">
                  Complete blood count results for Jane Smith
                </span>
                <span className="text-xs text-muted-foreground ml-4">1 hour ago</span>
              </DropdownMenuItem>
            </div>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-center justify-center text-blue-600 font-medium cursor-pointer">
              View all notifications
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Help */}
        <button
          className="hidden sm:block p-2.5 rounded-full hover:bg-accent transition-colors text-muted-foreground hover:text-foreground"
          aria-label="Help"
        >
          <HelpCircle className="w-5 h-5" />
        </button>

        <div className="h-6 w-px bg-border mx-2 hidden sm:block"></div>

        {/* User Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              className="flex items-center gap-2 pl-1 pr-1.5 py-1 rounded-full hover:bg-accent border border-transparent hover:border-border transition-all group"
              aria-label="User menu"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center text-white text-xs font-bold ring-2 ring-background shadow-sm group-hover:shadow-md transition-shadow">
                RS
              </div>
              <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:rotate-90 transition-transform duration-200" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-60">
            <DropdownMenuLabel>
              <div className="flex flex-col space-y-1">
                <span className="font-medium">Dr. Rohit Sharma</span>
                <span className="text-xs font-normal text-gray-500">
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
              <Link href="/dashboard/settings" className="flex items-center gap-2 cursor-pointer">
                <Settings className="w-4 h-4" />
                <span>Settings</span>
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem
              className="flex items-center gap-2 cursor-pointer"
              onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
            >
              {resolvedTheme === "dark" ? (
                <Sun className="w-4 h-4" />
              ) : (
                <Moon className="w-4 h-4" />
              )}
              <span>Switch to {resolvedTheme === "dark" ? "Light" : "Dark"} Mode</span>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="flex items-center gap-2 text-red-600 focus:text-red-700 focus:bg-red-50 cursor-pointer">
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
